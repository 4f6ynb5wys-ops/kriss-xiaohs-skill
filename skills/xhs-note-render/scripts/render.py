# -*- coding: utf-8 -*-
"""
小红书图文渲染器 —— 由 spec.json 驱动，一套设计系统渲染封面与全部内页。
用法：  python render.py spec.json
设计系统写死在代码里，不接受逐篇覆写 —— 这是它不会漂移的原因。

主题：
  A 宣纸留白 / B 深墨立牌 / C 暖纸 —— 纯排版
  D 水墨（默认）—— 程序化笔触：贝塞尔骨架 + 压力曲线 + 各向异性飞白
"""
import json, os, sys, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
try:
    import numpy as np
    HAS_NP = True
except ImportError:
    HAS_NP = False

W, H, M = 1080, 1440, 96
SONG = "/System/Library/Fonts/Supplemental/Songti.ttc"
_PF = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"
PF = _PF if os.path.exists(_PF) else "/System/Library/Fonts/Hiragino Sans GB.ttc"
_I = (3, 7) if PF == _PF else (0, 2)

song_black = lambda s: ImageFont.truetype(SONG, s, index=0)
song_light = lambda s: ImageFont.truetype(SONG, s, index=3)
pf_reg     = lambda s: ImageFont.truetype(PF, s, index=_I[0])
pf_med     = lambda s: ImageFont.truetype(PF, s, index=_I[1])

THEMES = {
    "A": dict(bg=(242,238,229), ink=(28,32,30),   sub=(74,78,74),    dim=(138,134,124),
              rule=(206,199,186), accent=(150,42,34), vig=14, brush=False),
    "B": dict(bg=(26,34,31),    ink=(240,235,224), sub=(176,184,176), dim=(126,138,130),
              rule=(58,70,64),   accent=(188,155,94), vig=22, brush=False),
    "C": dict(bg=(238,233,222), ink=(26,30,28),   sub=(78,82,78),    dim=(140,136,126),
              rule=(210,203,190), accent=(150,42,34), vig=12, brush=False),
    "D": dict(bg=(243,239,229), ink=(24,26,25),   sub=(86,88,84),    dim=(146,142,131),
              rule=(208,201,188), accent=(150,42,34), vig=10, brush=True),
}

# ── 字距：大字收紧，小字放开 ──────────────────────────────────
def ls_w(d,t,f,ls): return sum(d.textlength(c,font=f) for c in t)+ls*max(len(t)-1,0)
def ls_t(d,xy,t,f,fill,ls=0):
    x,y=xy
    for c in t: d.text((x,y),c,font=f,fill=fill); x+=d.textlength(c,font=f)+ls
    return x
def wrap(d,text,f,maxw):
    lines,cur=[],""
    for ch in text:
        if ch=="\n": lines.append(cur); cur=""; continue
        if d.textlength(cur+ch,font=f)>maxw and cur: lines.append(cur); cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return lines
def chunk(text, n):
    return [text[i:i+n] for i in range(0, len(text), n)]

# ══ 水墨引擎 ══════════════════════════════════════════════════
def _toL(a): return Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
def _fromL(im): return np.array(im, np.float32)/255
def _blur(a,r): return _fromL(_toL(a).filter(ImageFilter.GaussianBlur(r)))

def _noise(h,w,sx,sy,seed):
    """各向异性噪声：sx≪sy 产生纵向丝缕 —— 飞白的关键，圆噪点做不出来"""
    rng = np.random.default_rng(seed)
    small = rng.random((max(int(h/sy),2), max(int(w/sx),2))).astype(np.float32)
    return _fromL(Image.fromarray((small*255).astype(np.uint8)).resize((w,h), Image.BICUBIC))

def _bezier(p0,p1,p2,p3,n=420):
    t=np.linspace(0,1,n)[:,None]
    return ((1-t)**3*np.array(p0)+3*(1-t)**2*t*np.array(p1)
            +3*(1-t)*t**2*np.array(p2)+t**3*np.array(p3))

def brush(path, w0, w1, seed, dry=0.50, taper=2.6):
    buf=Image.new("L",(W,H),0); d=ImageDraw.Draw(buf); n=len(path)
    for i,(x,y) in enumerate(path):
        t=i/(n-1)
        press=(1-t)**0.35*(1-t**taper*0.92)          # 起笔重 → 行笔稳 → 收笔提
        r=(w0*(1-t)+w1*t)*max(press,0.04)
        d.ellipse([x-r,y-r*0.92,x+r,y+r*0.92], fill=255)
    m=_blur(_fromL(buf),6)
    streak=_noise(H,W,3.5,46,seed)                   # 飞白：顺笔锋方向拉丝
    bite=np.clip((np.linspace(0,1,H)[:,None]-0.22)/0.78,0,1)*dry
    m=np.clip(m-(streak<bite)*streak*1.35,0,1)
    edge=np.clip(1-np.abs(m-0.5)/0.5,0,1)
    m=np.clip(m-edge*_noise(H,W,2.2,14,seed+7)*0.30,0,1)
    return _blur(m,1.6)

def rot(m,deg): return _fromL(_toL(m).rotate(deg,resample=Image.BICUBIC,center=(W/2,H/2),fillcolor=0))
def sft(m,dx,dy):
    o=Image.new("L",(W,H),0); o.paste(_toL(m),(int(dx),int(dy))); return _fromL(o)

def paper(T):
    base=np.ones((H,W,3),np.float32)*np.array(T["bg"],np.float32)/255
    base*=(0.978+0.042*_noise(H,W,1.4,1.4,5))[...,None]
    base*=(0.986+0.026*_noise(H,W,300,300,9))[...,None]
    return base

def ink_on(base,m,color):
    c=np.array(color,np.float32)/255; a=m[...,None]
    tint=c[None,None,:]*(0.62+0.38*a)+np.array([0.34,0.29,0.24])[None,None,:]*(1-a)*0.42
    return base*(1-a)+tint*a

# ── 质感 ──────────────────────────────────────────────────────
def grain(im, amount=5, step=2):
    px=im.load()
    for y in range(0,H,step):
        for x in range(0,W,step):
            n=random.randint(-amount,amount); r,g,b=px[x,y]
            px[x,y]=(max(0,min(255,r+n)),max(0,min(255,g+n)),max(0,min(255,b+n)))

def vignette(im,s):
    mask=Image.new("L",(W,H),0); md=ImageDraw.Draw(mask)
    md.ellipse([-W*0.35,-H*0.22,W*1.35,H*1.22],fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(190))
    return Image.composite(im, Image.blend(im, Image.new("RGB",(W,H),(0,0,0)), s/100), mask)

def seal(d,x,y,s,two,color):
    d.rounded_rectangle([x,y,x+s,y+s],radius=6,fill=color)
    f=pf_med(int(s*0.30))
    for i,t in enumerate(two):
        ls_t(d,(x+(s-ls_w(d,t,f,2))/2, y+s*0.17+i*s*0.34), t, f, (247,243,236), 2)

def canvas(T, ink_mask=None):
    if T["brush"] and HAS_NP:
        base = paper(T)
        if ink_mask is not None: base = ink_on(base, ink_mask, T["ink"])
        im = Image.fromarray((np.clip(base,0,1)*255).astype(np.uint8))
    else:
        im = Image.new("RGB",(W,H),T["bg"])
    return im, ImageDraw.Draw(im)

def finish(im,T,path):
    grain(im,5); im=vignette(im,T["vig"]); im.save(path); return im

def footer(d,T,text,brand,x=M):
    if not T["brush"]: d.line([(M,1252),(W-M,1252)],fill=T["rule"],width=2)
    if text: ls_t(d,(x,1300 if T["brush"] else 1288),text,pf_reg(27 if T["brush"] else 28),T["dim"],4)

# ══ 封面 ══════════════════════════════════════════════════════
def cover(spec,T,out):
    c=spec["cover"]; cred=spec["brand"]["credential"]; sl=spec["brand"]["seal"]

    if T["brush"] and HAS_NP:
        # 水墨版：左侧竖笔 + 竖排标题（斜笔与横排标题在 3:4 里必抢位，已弃用）
        m = brush(_bezier((196,-60),(214,420),(188,900),(206,1500)), 84, 62, seed=23)
        im,d = canvas(T,m)
        x0=356; limit=W-M-146-180-24
        ls_t(d,(x0,150),cred,pf_reg(27),T["dim"],5)
        ft=song_black(142); cx=W-M-146
        for i,ch in enumerate(c["title"][0]): d.text((cx,296+i*160),ch,font=ft,fill=T["ink"])
        if len(c["title"])>1:
            cx2=cx-180
            for i,ch in enumerate(c["title"][1]): d.text((cx2,378+i*160),ch,font=ft,fill=(96,98,94))
        sub=c.get("sub")
        subs = sub if isinstance(sub,list) else chunk(sub or "", 6)
        fs=song_light(40)
        for j,l in enumerate(subs):
            assert ls_w(d,l,fs,1)+x0 < limit, f"副标题第 {j+1} 行过长，会撞上竖排标题：{l}"
            ls_t(d,(x0,706+j*62),l,fs,T["sub"],1)
        footer(d,T,c.get("footer"),sl,x0)
        seal(d,x0,1168,88,sl,T["accent"])
        return finish(im,T,f"{out}/01_封面.png")

    im,d=canvas(T)
    ls_t(d,(M,150),cred,pf_reg(27),T["dim"],5)
    d.line([(M,205),(M+300,205)],fill=T["rule"],width=2)
    lines=c["title"]; size=172 if max(len(l) for l in lines)<=4 else 138
    ft=song_black(size); y=330
    for i,line in enumerate(lines):
        col = T["ink"] if (i==0 or T is THEMES["A"]) else T["accent"]
        endx=ls_t(d,(M,y),line,ft,col,-6)
        if i==len(lines)-1 and c.get("accent"): d.text((endx+14,y),c["accent"],font=ft,fill=T["accent"])
        y+=int(size*1.15)
    sub=c.get("sub")
    if sub:
        s=" ".join(sub) if isinstance(sub,list) else sub
        for j,l in enumerate(wrap(d,s,song_light(44),W-2*M)):
            ls_t(d,(M,y+42+j*60),l,song_light(44),T["sub"],1)
    footer(d,T,c.get("footer"),sl)
    seal(d,W-M-96,1256,96,sl,T["accent"])
    return finish(im,T,f"{out}/01_封面.png")

# ══ 内页 ══════════════════════════════════════════════════════
def page(spec,T,out,idx,p):
    if T["brush"] and HAS_NP:
        # 内页用同一支笔，但只留一道细墨作页边 —— 同一语言，减重
        m = brush(_bezier((150,-40),(158,400),(146,860),(154,1480)), 17, 11, seed=40+idx, dry=0.58)
        m = sft(m, -66, 0)
        im,d = canvas(T,m)
    else:
        im,d = canvas(T)
        d.line([(M,190),(W-M,190)],fill=T["rule"],width=2)

    x = M + (40 if (T["brush"] and HAS_NP) else 0)
    ls_t(d,(x,138),f"{idx:02d}",pf_med(30),T["dim"],2)
    ft=song_black(76); y=250
    for l in wrap(d,p["title"],ft,W-x-M): ls_t(d,(x,y),l,ft,T["ink"],-3); y+=96
    y+=40
    fb=song_light(42)
    for raw in p.get("body",[]):
        if not raw: y+=34; continue
        for l in wrap(d,raw,fb,W-x-M): ls_t(d,(x,y),l,fb,T["sub"],1); y+=64
        y+=16
    if p.get("note"):
        by=max(1130, int(y)+44)                      # 自动避让正文，不再压字
        assert by+96 < 1290, f"第 {idx} 页正文过长，提示条放不下 —— 回去删正文，不要改版式"
        d.rectangle([x,by,x+5,by+96],fill=T["accent"])
        for j,l in enumerate(wrap(d,p["note"],pf_med(34),W-x-M-40)[:2]):
            ls_t(d,(x+30,by+8+j*46),l,pf_med(34),T["ink"],1)
    seal(d, W-M-84, 1300, 84, spec["brand"]["seal"], T["accent"])
    return finish(im,T,f"{out}/{idx:02d}_{p['title'][:8]}.png")

def contact(imgs,out):
    n=len(imgs); cols=min(n,4); rows=(n+cols-1)//cols; tw,th=270,360
    s=Image.new("RGB",(cols*(tw+20)+20, rows*(th+50)+20),(255,255,255))
    for i,im in enumerate(imgs):
        r,c=divmod(i,cols); s.paste(im.resize((tw,th),Image.LANCZOS),(20+c*(tw+20),20+r*(th+50)))
    s.save(f"{out}/_缩略图对照.png")

def main(sp):
    spec=json.load(open(sp,encoding="utf-8")); random.seed(spec.get("seed",7))
    name=spec.get("theme","D")
    if name=="D" and not HAS_NP:
        print("⚠️  numpy 缺失，水墨主题回退到 A（纯排版）。装 numpy 可恢复。"); name="A"
    T=THEMES[name]; out=spec["out"]; os.makedirs(out,exist_ok=True)
    imgs=[cover(spec,T,out)]
    for i,p in enumerate(spec.get("pages",[]),start=2): imgs.append(page(spec,T,out,i,p))
    contact(imgs,out)
    print(f"渲染完成 {len(imgs)} 张（主题 {name}） -> {out}")

if __name__=="__main__": main(sys.argv[1])
