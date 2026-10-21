# -*- coding: utf-8 -*-
"""从 Markdown 提取代码块与文字段，生成 scenes.json 骨架（voice 待填）

用法：
  py -3.12 extract.py --md doc.md --out ./video-out

会输出 scenes.json：
  [{"kind":"code","page":1,"of":3,"rows":[[1,"..."],...],"voice":""}, ...]

之后人工/模型填 voice，并要求：
  每个代码块的 len(voices) == of
"""
import re, json, argparse, sys
from pathlib import Path
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

def clean(t):
    t=re.sub(r"<div[^>]*>.*?</div>","",t,flags=re.S)
    t=re.sub(r"<[^>]+>","",t)
    t=re.sub(r"!\[[^\]]*\]\([^)]*\)","",t)
    t=re.sub(r"^#{1,6}\s*.*$","",t,flags=re.M)
    return "\n".join(x.strip() for x in t.replace("`","").split("\n") if x.strip()).strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", default="./video-out")
    ap.add_argument("--start", default=None, help="起始小节标题，如 '8.2'")
    ap.add_argument("--end", default=None, help="结束小节标题，如 '8.3'")
    ap.add_argument("--title", default="", help="视频总标题")
    a=ap.parse_args()

    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    lines=Path(a.md).read_text(encoding="utf-8").split("\n")

    # 截取小节
    if a.start:
        idx=[i for i,l in enumerate(lines) if l.strip().startswith("#") and a.start in l]
        if idx: lines=lines[idx[0]:]
    if a.end:
        idx=[i for i,l in enumerate(lines) if l.strip().startswith("#") and a.end in l]
        if idx: lines=lines[:idx[0]]

    # 解析
    blocks=[]; buf=[]; inb=False; text_acc=[]
    for ln in lines:
        if re.match(r"^\s*```", ln):
            if inb:
                blocks.append(("code", list(buf))); buf=[]; inb=False
            else:
                if text_acc: blocks.append(("text","\n".join(text_acc))); text_acc=[]
                inb=True
            continue
        if inb: buf.append(ln)
        else: text_acc.append(ln)
    if inb: blocks.append(("code", list(buf)))
    if text_acc: blocks.append(("text","\n".join(text_acc)))

    scenes=[]; small=[]
    for kind,payload in blocks:
        if kind=="text":
            t=clean(payload)
            if not t: continue
            paras=[x.strip() for x in re.split(r"\n\s*\n", t) if len(x.strip())>=6]
            if sum(len(x) for x in paras) < 60:
                small.extend(paras); continue
            if small: paras=small+paras; small=[]
            scenes.append(dict(kind="text", paras=paras, voice=""))
        else:
            sub=" ".join(small); small=[]
            rows=[[i+1,l] for i,l in enumerate(payload)]
            for pi,page in enumerate(pages_split(rows)):
                scenes.append(dict(kind="code", page=pi+1, of=len(pages_split(rows)),
                                   rows=page, sub=sub, voice=""))
    if small:
        scenes.append(dict(kind="text", paras=small, voice=""))

    # 前后加钩子/标题/结尾
    scenes=[dict(kind="hook",voice="")]+scenes+[dict(kind="end",voice="")]
    for i,s in enumerate(scenes): s["idx"]=i; s["total"]=len(scenes)

    (out/"scenes.json").write_text(json.dumps(scenes,ensure_ascii=False,indent=1),encoding="utf-8")
    print(f"scenes={len(scenes)}  code_pages={sum(1 for s in scenes if s['kind']=='code')}")
    print("下一步：填写每幕 voice，确保代码块每页都有口播，再跑 render.py")

def pages_split(rows, max_lines=18):
    if not rows: return [[]]
    npg=max(1,(len(rows)+max_lines-1)//max_lines)
    per=(len(rows)+npg-1)//npg
    return [rows[i:i+per] for i in range(0,len(rows),per)]

if __name__=="__main__":
    main()
