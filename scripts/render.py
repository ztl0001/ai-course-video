# -*- coding: utf-8 -*-
"""按 scenes.json 渲染画面

用法：
  py -3.12 render.py --scenes ./video-out/scenes.json --out ./video-out/slides

场景 kind：hook / title / text / code / image / end
"""
import json, argparse
from pathlib import Path
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common import (W,H,PAPER,GRID,INK,GRAY,LGRAY,PURPLE,LINE,DARK,
                    fb,fr,fm,base_canvas,header,footer,wrap,draw_mixed,tokenize,pages_of)

def text_card(out,label,title,points,idx,total):
    img=base_canvas(); d=header(img,label,title)
    y=296
    for p in points:
        d.ellipse([140,y+16,156,y+32],fill=PURPLE)
        for ln in wrap(d,p,fr(30),W-340):
            d.text((186,y),ln,font=fr(30),fill=INK); y+=48
        y+=18
    footer(d,idx,total); img.save(out,quality=95)

def code_page(out,label,title,rows,idx,total):
    img=base_canvas(); d=header(img,label,title)
    tx,ty,tw,th=110,265,W-220,660
    d.rounded_rectangle([tx,ty,tx+tw,ty+th],radius=18,fill=DARK)
    for i,c in enumerate([(255,96,92),(255,190,70),(80,200,120)]):
        d.ellipse([tx+24+i*26,ty+18,tx+38+i*26,ty+32],fill=c)
    d.text((tx+130,ty+14),"python · 原文代码",font=fr(18),fill=(130,134,146))
    probe=ImageDraw.Draw(Image.new("RGB",(10,10)))
    size=21
    def line_w(line):
        w=0
        for seg,_ in tokenize(line):
            f=fm(size) if all(ord(c)<128 for c in seg) else fr(size)
            w+=probe.textlength(seg,font=f)
        return w
    mw=max((line_w(l) for _,l in rows), default=0)
    if mw>1390: size=max(14,int(size*1390/mw))
    lh=max(20,int(size*1.48)); y0=ty+54
    for i,(no,line) in enumerate(rows):
        cy=y0+i*lh
        d.text((tx+18,cy+4),f"{no:3d}",font=fm(13),fill=(86,90,100))
        cx=tx+64
        for seg,col in tokenize(line):
            cx=draw_mixed(d,cx,cy,seg,col,size)
    footer(d,idx,total); img.save(out,quality=95)

def image_page(out,label,title,sub,src,maxw,maxh,idx,total):
    img=base_canvas(); d=header(img,label,title,sub)
    im0=Image.open(src).convert("RGB")
    r=min(maxw/im0.width,maxh/im0.height)
    w,h=int(im0.width*r),int(im0.height*r)
    im=im0.resize((w,h),Image.LANCZOS)
    x=(W-w)//2; y=300+(maxh-h)//2
    d.rounded_rectangle([x-12,y-12,x+w+12,y+h+12],radius=14,
                        fill=(255,255,255),outline=LINE,width=2)
    img.paste(im,(x,y)); footer(d,idx,total); img.save(out,quality=95)

def hook_page(out,idx,total,line1="你的 Agent",line2="记得住你吗？",sub="",label="HELLO · 8.2"):
    img=Image.new("RGB",(W,H),(24,26,32)); d=ImageDraw.Draw(img)
    for x in range(0,W,80): d.line([(x,0),(x,H)],fill=(38,41,50),width=1)
    d.ellipse([110,250,140,280],fill=PURPLE)
    d.text((170,246),label,font=fb(30),fill=(170,140,220))
    d.text((108,340),line1,font=fb(112),fill=(248,248,250))
    d.text((108,480),line2,font=fb(112),fill=(248,248,250))
    if sub: d.text((112,660),sub,font=fr(34),fill=(168,170,182))
    footer(d,idx,total,dark=True); img.save(out,quality=95)

def title_page(out,idx,total,items=()):
    img=base_canvas(); d=header(img,"CHAPTER","目录","")
    for i,(num,name) in enumerate(items):
        yy=330+i*112
        d.text((130,yy+10),num,font=fb(30),fill=PURPLE)
        d.text((270,yy),name,font=fr(36),fill=INK)
    footer(d,idx,total); img.save(out,quality=95)

def end_page(out,idx,total):
    img=Image.new("RGB",(W,H),(24,26,32)); d=ImageDraw.Draw(img)
    d.text((110,220),"完",font=fb(76),fill=(248,248,250))
    d.text((110,360),"下一节见",font=fr(36),fill=(180,182,194))
    footer(d,idx,total,dark=True); img.save(out,quality=95)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenes", required=True)
    ap.add_argument("--out", default="./video-out/slides")
    a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    S=json.loads(Path(a.scenes).read_text(encoding="utf-8"))
    total=len(S)

    for s in S:
        i=s["idx"]; k=s["kind"]; fn=f"{i:02d}_{k}.png"
        if k=="hook":
            hook_page(out/fn,i+1,total,line1=s.get("line1","你的 Agent"),
                      line2=s.get("line2","记得住你吗？"),sub=s.get("sub",""),
                      label=s.get("label","HELLO · 8.2"))
        elif k=="title":
            title_page(out/fn,i+1,total,items=s.get("items",()))
        elif k=="end":
            end_page(out/fn,i+1,total)
        elif k=="text":
            points=s.get("points")
            if not points:
                # 未填提炼要点时，把原文段落拆成短句兜底，避免溢出
                import re as _re
                points=[]
                for para in s.get("paras",[]):
                    for sent in _re.split(r"(?<=[。；])", para):
                        sent=sent.strip()
                        if sent and len(points)<6:
                            points.append(sent[:42])
                print(f"  ! scene {i}: 未填 points，已用原文短句兜底（建议手写提炼卡）")
            text_card(out/fn,s.get("label",""),s.get("title","要点"),points or ["（待填要点）"],i+1,total)
        elif k=="code":
            code_page(out/fn,s.get("label",""),s.get("title","代码"),
                      s["rows"],i+1,total)
        elif k=="image":
            image_page(out/fn,s.get("label",""),s.get("title",""),
                       s.get("sub",""),s["src"],s.get("maxw",900),s.get("maxh",530),
                       i+1,total)
        s["img"]=fn
        print("render",fn)

    Path(a.scenes).write_text(json.dumps(S,ensure_ascii=False,indent=1),encoding="utf-8")
    print("done. 下一步跑 build.py")

if __name__=="__main__":
    main()
