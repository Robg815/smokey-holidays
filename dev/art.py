"""SVG art that stays vector: the S2 brand mark, the admin tablet wallpaper and the Halloween city map card.
Scenes, emblems and reward pictures are rendered by dev/paint.py and dev/paint_icons.py.   python dev/art.py"""
import random, math, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
R = str(ROOT / 'web' / 'img')
def out(h,n,s):
    os.makedirs(f'{R}/{h}',exist_ok=True); open(f'{R}/{h}/{n}.svg','w').write(s)
def svg(b,d='',vb='0 0 1200 520',pa='xMidYMid slice'): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" preserveAspectRatio="{pa}"><defs>{d}</defs>{b}</svg>'
def lg(i,st,v=True): return f'<linearGradient id="{i}" x1="0" y1="0" x2="{0 if v else 1}" y2="{1 if v else 0}">'+''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o,c in st)+'</linearGradient>'
def rg(i,st,cx=.5,cy=.5,r=.5): return f'<radialGradient id="{i}" cx="{cx}" cy="{cy}" r="{r}">'+''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o,c in st)+'</radialGradient>'
def stars(n,ym,seed,col='#fff'):
    r=random.Random(seed); return ''.join(f'<circle cx="{r.uniform(0,1200):.0f}" cy="{r.uniform(0,ym):.0f}" r="{r.uniform(.6,1.9):.1f}" fill="{col}" opacity="{r.uniform(.35,1):.2f}"/>' for _ in range(n))
SOFT='<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>'
def brand():
    d=lg('bg',[(0,'#7b5cff'),(1,'#ff5fa2')],False)+lg('hl',[(0,'rgba(255,255,255,.55)'),(1,'rgba(255,255,255,0)')])
    b=('<rect x="4" y="4" width="92" height="92" rx="26" fill="url(#bg)"/><rect x="4" y="4" width="92" height="46" rx="26" fill="url(#hl)" opacity=".5"/>'
       '<path d="M30 64c4 6 11 9 19 9 10 0 17-5 17-13 0-18-34-10-34-27 0-7 7-12 16-12 7 0 12 3 15 7" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/>'
       '<circle cx="72" cy="28" r="7" fill="#fff"/>')
    return svg(b,d,'0 0 100 100','xMidYMid meet')
def citymap():
    d=lg('bg',[(0,'#1c0d2e'),(1,'#0e0618')])+rg('pg',[(0,'rgba(255,138,31,.75)'),(1,'rgba(255,138,31,0)')])
    r=random.Random(21)
    b='<rect width="400" height="220" rx="18" fill="url(#bg)"/>'
    b+='<path d="M-10 160C60 140 90 190 160 170S260 120 330 140 410 120 410 120V230H-10Z" fill="#160a28"/>'
    b+='<path d="M0 205C70 190 120 214 190 196S300 180 400 196" stroke="#2a5a8a" stroke-width="10" fill="none" opacity=".55"/>'
    for i in range(0,400,40): b+=f'<path d="M{i} 0V220" stroke="#ffffff" stroke-opacity=".04"/>'
    for j in range(0,220,40): b+=f'<path d="M0 {j}H400" stroke="#ffffff" stroke-opacity=".04"/>'
    b+='<g stroke="#3a2456" stroke-width="7" fill="none" stroke-linecap="round"><path d="M20 60L130 90 220 70 380 110"/><path d="M110 10L130 90 120 200"/><path d="M260 10L220 70 250 190"/><path d="M30 150L120 140 250 150 370 175"/></g>'
    b+='<g stroke="#ff8a1f" stroke-width="2.5" stroke-dasharray="6 7" fill="none" opacity=".8"><path d="M60 70Q120 120 180 85T300 120 350 160"/></g>'
    for x,y in ((60,70),(180,85),(300,120),(350,160),(120,165),(245,40)):
        b+=f'<circle cx="{x}" cy="{y}" r="22" fill="url(#pg)"/><path d="M{x} {y+12}c-10-11-14-17-14-23a14 14 0 0128 0c0 6-4 12-14 23z" fill="#ff8a1f" stroke="#7a3300" stroke-width="1.5"/><circle cx="{x}" cy="{y-11}" r="5" fill="#2a0f3e"/>'
    return svg(b,d,'0 0 400 220','xMidYMid slice')
def wallpaper():
    d=lg('s',[(0,'#0a0f1f'),(1,'#141a33')])+rg('a',[(0,'rgba(123,92,255,.6)'),(1,'rgba(123,92,255,0)')])+rg('b',[(0,'rgba(255,95,162,.45)'),(1,'rgba(255,95,162,0)')])+rg('c',[(0,'rgba(95,243,255,.35)'),(1,'rgba(95,243,255,0)')])+SOFT
    b='<rect width="1200" height="800" fill="url(#s)"/><circle cx="220" cy="140" r="420" fill="url(#a)"/><circle cx="1040" cy="200" r="380" fill="url(#b)"/><circle cx="700" cy="760" r="460" fill="url(#c)"/>'
    b+=''.join(f'<path d="M-50 {y}C250 {y-140} 500 {y+120} 800 {y-30}S1150 {y-90} 1260 {y}" fill="none" stroke="#ffffff" stroke-opacity="{.035+.01*(i%3):.3f}" stroke-width="{1.5+i%3}"/>' for i,y in enumerate(range(260,800,34)))
    return svg(b,d,'0 0 1200 800')

out('halloween','map',citymap()); out('admin','wallpaper',wallpaper())
open(f'{R}/brand.svg','w').write(brand())
