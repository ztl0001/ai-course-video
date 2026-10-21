# -*- coding: utf-8 -*-
"""共用：画布、字体、混排、语法高亮"""
from pathlib import Path
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1600, 1000
PAPER=(250,248,246); GRID=(240,237,233); INK=(36,38,44); GRAY=(112,114,124)
LGRAY=(168,170,180); PURPLE=(124,92,180); LINE=(226,222,216); DARK=(30,33,40)
C_KEY=(198,120,221); C_STR=(152,195,121); C_FUN=(229,192,123)
C_CMT=(106,112,124); C_NUM=(209,154,102); C_TXT=(171,178,191)

FBD="C:/Windows/Fonts/msyhbd.ttc"; FRG="C:/Windows/Fonts/msyh.ttc"
FMN="C:/Windows/Fonts/consola.ttf"; FEM="C:/Windows/Fonts/seguiemj.ttf"

def fb(s): return ImageFont.truetype(FBD,s)
def fr(s): return ImageFont.truetype(FRG,s)
def fm(s): return ImageFont.truetype(FMN,s)
def fe(s): return ImageFont.truetype(FEM,s)

def base_canvas(dark=False):
    if dark:
        return Image.new("RGB",(W,H),(24,26,32))
    img=Image.new("RGB",(W,H),PAPER); d=ImageDraw.Draw(img)
    for x in range(0,W,40): d.line([(x,0),(x,H)],fill=GRID,width=1)
    for y in range(0,H,40): d.line([(0,y),(W,y)],fill=GRID,width=1)
    atmo=Image.new("RGBA",(W,H),(0,0,0,0)); ad=ImageDraw.Draw(atmo)
    for cx,cy,r,col in [(int(W*.97),int(H*.02),int(W*.55),(194,212,238,135)),
                        (int(W*.02),int(H*.99),int(W*.50),(224,210,238,125))]:
        for i in range(16,0,-1):
            rad=int(r*i/16); a=int(col[3]*(1-i/16)**1.3)
            ad.ellipse([cx-rad,cy-rad,cx+rad,cy+rad],fill=col[:3]+(a,))
    atmo=atmo.filter(ImageFilter.GaussianBlur(70))
    return Image.alpha_composite(img.convert("RGBA"),atmo).convert("RGB")

def header(img,label,title,sub=None,dark=False):
    d=ImageDraw.Draw(img)
    ink=(245,245,248) if dark else INK
    d.text((110,70),label,font=fb(23),fill=PURPLE if not dark else (170,140,220))
    d.text((110,105),title,font=fb(46),fill=ink)
    if sub: d.text((110,172),sub,font=fr(24),fill=GRAY if not dark else (150,152,162))
    d.line([(110,232),(W-110,232)],fill=(60,63,72) if dark else LINE,width=2)
    return d

def footer(d,idx,total,dark=False):
    d.text((W-150,H-58),f"{idx:02d} / {total:02d}",font=fr(22),
           fill=(110,112,122) if dark else LGRAY)

def wrap(d,text,f,maxw):
    lines,cur=[],""
    for ch in text:
        if ch=="\n": lines.append(cur); cur=""; continue
        if d.textlength(cur+ch,font=f)<=maxw: cur+=ch
        else: lines.append(cur); cur=ch
    if cur: lines.append(cur)
    return lines

def is_emoji(ch):
    o=ord(ch)
    return (0x1F000<=o<=0x1FAFF) or (0x2600<=o<=0x27BF) or (0x2B00<=o<=0x2BFF)

def draw_mixed(d,x,y,text,color,size):
    """ASCII→Consolas，中文→雅黑，emoji→Segoe UI Emoji"""
    fa,fc,fe_=fm(size),fr(size),fe(size)
    cx=x; buf=""; kind=None
    def flush(b,k):
        nonlocal cx
        if not b: return
        f = fe_ if k=="e" else (fc if k=="c" else fa)
        d.text((cx,y),b,font=f,fill=color); cx+=d.textlength(b,font=f)
    for ch in text:
        k = "e" if is_emoji(ch) else ("c" if ord(ch)>127 else "a")
        if kind is None or k==kind: buf+=ch; kind=k
        else: flush(buf,kind); buf,kind=ch,k
    flush(buf,kind)
    return cx

KEYWORDS={"def","class","return","if","elif","else","for","while","in","not","and","or",
 "is","None","True","False","import","from","as","try","except","finally","with","lambda",
 "yield","pass","continue","break","self","async","await","raise","global","nonlocal",
 "assert","del"}
TOK=re.compile(r"(#[^\n]*)|('(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\")|(\b\d+\.?\d*\b)|"
               r"([A-Za-z_]\w*)|(\s+)|(.)")

def tokenize(line):
    out=[]
    for m in TOK.finditer(line):
        if m.group(1): out.append((m.group(1),C_CMT))
        elif m.group(2): out.append((m.group(2),C_STR))
        elif m.group(3): out.append((m.group(3),C_NUM))
        elif m.group(4):
            w=m.group(4); nxt=line[m.end():m.end()+1]
            out.append((w, C_KEY if w in KEYWORDS else (C_FUN if nxt=="(" else C_TXT)))
        elif m.group(5): out.append((m.group(5),C_TXT))
        else: out.append((m.group(6),C_TXT))
    return out

def pages_of(rows, max_lines=18):
    """先算页数再均分，避免最后一页只剩一两行"""
    if not rows: return [[]]
    npg=max(1,(len(rows)+max_lines-1)//max_lines)
    per=(len(rows)+npg-1)//npg
    return [rows[i:i+per] for i in range(0,len(rows),per)]
