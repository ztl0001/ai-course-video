# -*- coding: utf-8 -*-
"""逐句 TTS → 分段 → 拼接 → 字幕 → 响度 → BGM

用法：
  py -3.12 build.py --scenes ./video-out/scenes.json \
      --voice zh-CN-YunyangNeural --rate +8% --gap 0.7 \
      --bgm bgm.mp3 --name 课程-01.mp4
"""
import asyncio, subprocess, time, re, sys, json, argparse
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
from pathlib import Path
import edge_tts

sys.path.insert(0, str(Path(__file__).parent))

def sh(cmd, cwd=None):
    r=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="ignore",cwd=cwd)
    if r.returncode!=0:
        raise RuntimeError(f"CMD FAILED: {' '.join(map(str,cmd))}\n{r.stderr[-1000:]}")
    return r.stdout

def dur(p):
    return float(sh(["ffprobe","-v","error","-show_entries","format=duration",
                     "-of","csv=p=0",str(p)]).strip())

def mean_vol(p):
    r=subprocess.run(["ffmpeg","-hide_banner","-i",str(p),"-af","volumedetect","-f","null","-"],
                     capture_output=True,text=True,encoding="utf-8",errors="ignore")
    m=re.search(r"mean_volume:\s*(-?[\d.]+)",r.stderr)
    return float(m.group(1)) if m else -20.0

async def _tts(text,voice,rate,out):
    await edge_tts.Communicate(text,voice,rate=rate).save(str(out))

def sentences(t):
    parts=[x.strip() for x in re.split(r"(?<=[。！？])",t) if x.strip()]
    return parts or [t]

def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h}:{m:02d}:{s:05.2f}"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenes",required=True)
    ap.add_argument("--out",default="./video-out")
    ap.add_argument("--voice",default="zh-CN-YunyangNeural")
    ap.add_argument("--rate",default="+8%")
    ap.add_argument("--gap",type=float,default=0.7)
    ap.add_argument("--bgm",default=None)
    ap.add_argument("--name",default="final.mp4")
    a=ap.parse_args()

    HERE=Path(a.out); SL=HERE/"slides"
    VO=HERE/"vo"; SEG=HERE/"seg"
    for p in (VO,SEG): p.mkdir(exist_ok=True)
    S=json.loads(Path(a.scenes).read_text(encoding="utf-8"))

    # 断言：每幕必须有口播
    empty=[s["idx"] for s in S if not s.get("voice","").strip()]
    if empty:
        raise SystemExit(f"以下场景缺少口播，先补再合成：{empty}")

    # 1) 逐句 TTS
    index={}
    for s in S:
        idx=s["idx"]; sents=sentences(s["voice"]); parts=[]
        for k,sent in enumerate(sents):
            p=VO/f"{idx:02d}_{k}.mp3"; parts.append(p)
            if p.exists() and p.stat().st_size>800: continue
            for _ in range(4):
                try:
                    asyncio.run(_tts(sent,a.voice,a.rate,p)); break
                except Exception as e:
                    print("retry",idx,k,e); time.sleep(2)
            else: raise SystemExit(f"tts fail {idx}-{k}")
        dst=VO/f"{idx:02d}.mp3"
        if not (dst.exists() and dst.stat().st_size>1500):
            lst=VO/f"{idx:02d}.txt"
            lst.write_text("".join(f"file '{p.name}'\n" for p in parts),encoding="utf-8")
            sh(["ffmpeg","-y","-f","concat","-safe","0","-i",lst.name,"-c","copy",dst.name],cwd=VO)
        index[str(idx)]=[(p.name,dur(p),sent) for p,sent in zip(parts,sents)]
        print("tts",idx,round(dur(dst),2),len(sents))

    # 2) 分段
    for s in S:
        vo=VO/f"{s['idx']:02d}.mp3"; T=dur(vo); d=T+a.gap
        sh(["ffmpeg","-y","-loop","1","-framerate","30","-i",str(SL/s["img"]),"-i",str(vo),
            "-t",f"{d:.3f}","-map","0:v","-map","1:a","-af","apad",
            "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",
            "-r","30","-c:a","aac","-b:a","160k","-ar","48000","-ac","2",
            str(SEG/f"{s['idx']:02d}.mp4")])

    # 3) concat
    lst=HERE/"list.txt"
    lst.write_text("".join(f"file 'seg/{s['idx']:02d}.mp4'\n" for s in S),encoding="utf-8")
    sh(["ffmpeg","-y","-f","concat","-safe","0","-i","list.txt","-c","copy","withvoice.mp4"],cwd=HERE)

    # 4) ASS
    head="""[Script Info]
ScriptType: v4.00+
PlayResX: 1600
PlayResY: 1000
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Microsoft YaHei,38,&H00282626,&H000000FF,&H00FFFFFF,&H28FFFFFF,0,0,0,0,100,100,0,0,3,20,0,2,80,80,74,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[head]; t0=0.0
    for s in S:
        t=t0
        for name,d,sent in index[str(s["idx"])]:
            lines.append(f"Dialogue: 1,{ts(t)},{ts(t+d)},Sub,,0,0,0,,{sent}\n")
            t+=d
        t0+=sum(x[1] for x in index[str(s["idx"])])+a.gap
    (HERE/"subs.ass").write_text("".join(lines),encoding="utf-8")

    # 5) 烧字幕
    sh(["ffmpeg","-y","-i","withvoice.mp4","-vf","ass=subs.ass",
        "-c:v","libx264","-preset","medium","-crf","19","-g","60","-keyint_min","30",
        "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart","voice.mp4"],cwd=HERE)

    # 6) 响度
    sh(["ffmpeg","-y","-i","voice.mp4","-af","loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","voice_n.mp4"],cwd=HERE)

    # 7) BGM
    if a.bgm and Path(a.bgm).exists():
        v=mean_vol(HERE/"voice_n.mp4"); b=mean_vol(a.bgm)
        coef=10**((abs(b)-(abs(v)+9))/20)
        total=dur(HERE/"voice_n.mp4"); fade=max(0.0,total-3)
        fc=(f"[1:a]volume={coef:.4f},afade=t=in:st=0:d=2,afade=t=out:st={fade:.2f}:d=3[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[mix];"
            f"[mix]alimiter=limit=0.89:level=0[a]")
        sh(["ffmpeg","-y","-i","voice_n.mp4","-stream_loop","-1","-i",a.bgm,
            "-filter_complex",fc,"-map","0:v","-map","[a]",
            "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",
            "-movflags","+faststart",a.name],cwd=HERE)
    else:
        sh(["ffmpeg","-y","-i","voice_n.mp4","-c","copy",a.name],cwd=HERE)

    print(f"DONE -> {HERE/a.name}  {dur(HERE/a.name):.1f}s")

if __name__=="__main__":
    main()
