"""Regenerates the SVG scene backdrops and emblems in web/img/<holiday>/. Deterministic (seeded). Run: python dev/art.py"""
import random, math, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
R = str(ROOT / 'web' / 'img')
def out(h,n,s):
    os.makedirs(f'{R}/{h}',exist_ok=True); open(f'{R}/{h}/{n}.svg','w').write(s)
def svg(b,d='',vb='0 0 1200 520',pa='xMidYMid slice'): return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" preserveAspectRatio="{pa}"><defs>{d}</defs>{b}</svg>'
def lg(i,st,v=True): return f'<linearGradient id="{i}" x1="0" y1="0" x2="{0 if v else 1}" y2="{1 if v else 0}">'+''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o,c in st)+'</linearGradient>'
def rg(i,st,cx=.5,cy=.5,r=.5): return f'<radialGradient id="{i}" cx="{cx}" cy="{cy}" r="{r}">'+''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o,c in st)+'</radialGradient>'
def sky(i): return f'<rect width="1200" height="520" fill="url(#{i})"/>'
def stars(n,ym,seed,col='#fff'):
    r=random.Random(seed); return ''.join(f'<circle cx="{r.uniform(0,1200):.0f}" cy="{r.uniform(0,ym):.0f}" r="{r.uniform(.6,1.9):.1f}" fill="{col}" opacity="{r.uniform(.35,1):.2f}"/>' for _ in range(n))
def hills(y,amp,fill,seed,n=5):
    r=random.Random(seed); p=[y+r.uniform(-amp,amp) for _ in range(n+1)]; d=f'M0 520L0 {p[0]:.0f}'
    for i in range(n): d+=f'Q{(i+.5)*1200/n:.0f} {(p[i]+p[i+1])/2-r.uniform(amp*.3,amp):.0f} {(i+1)*1200/n:.0f} {p[i+1]:.0f}'
    return f'<path d="{d}L1200 520Z" fill="{fill}"/>'
HEART='M0 8C-14-4-12-16-4-16 0-16 0-10 0-10S0-16 4-16C12-16 14-4 0 8Z'
def heart(x,y,s,f,rot=0,op=1): return f'<path d="{HEART}" transform="translate({x:.0f} {y:.0f}) rotate({rot}) scale({s})" fill="{f}" opacity="{op}"/>'
def star4(x,y,s,f='#fff',op=1): return f'<path d="M0-10Q1-1 10 0Q1 1 0 10Q-1 1-10 0Q-1-1 0-10Z" transform="translate({x:.0f} {y:.0f}) scale({s})" fill="{f}" opacity="{op}"/>'
def bokeh(seed,n,col,ym=440):
    r=random.Random(seed); return ''.join(f'<circle cx="{r.uniform(0,1200):.0f}" cy="{r.uniform(10,ym):.0f}" r="{r.uniform(18,64):.0f}" fill="url(#{col})" opacity="{r.uniform(.2,.6):.2f}"/>' for _ in range(n))
def branch(x,y,a,l,d,r,o,sw):
    x2=x+math.cos(a)*l; y2=y-math.sin(a)*l; o.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke-width="{sw:.1f}"/>')
    if d:
        for da in (-r.uniform(.3,.65),r.uniform(.3,.65)): branch(x2,y2,a+da,l*r.uniform(.66,.8),d-1,r,o,sw*.72)
def tree(x,y,s,seed,col):
    o=[]; branch(x,y,math.pi/2,80*s,6,random.Random(seed),o,8*s); return f'<g stroke="{col}" stroke-linecap="round">{"".join(o)}</g>'
def skyline(seed,base,hmin,hmax,fill,lit='#ffd87a',p=.35,x0=0,x1=1200):
    r=random.Random(seed); b=''; x=x0
    while x<x1:
        w=r.randint(40,90); h=r.randint(hmin,hmax); b+=f'<rect x="{x}" y="{base-h}" width="{w}" height="{h+60}" fill="{fill}"/>'
        for wy in range(base-h+12,base-8,22):
            for wx in range(x+8,x+w-10,16):
                if r.random()<p: b+=f'<rect x="{wx}" y="{wy}" width="6" height="9" fill="{lit}" opacity="{r.uniform(.5,1):.2f}"/>'
        x+=w+r.randint(0,6)
    return b
def bunting(cols,y0=12,sag=38):
    f=lambda x:y0+sag*math.sin(math.pi*((x%600)/600)); b='<path d="M'+' L'.join(f'{x} {f(x):.0f}' for x in range(0,1201,20))+'" fill="none" stroke="#dfe6ff" stroke-width="2"/>'
    for i,x in enumerate(range(20,1200,60)): b+=f'<path d="M{x-18} {f(x-18):.0f}L{x+18} {f(x+18):.0f}L{x} {f(x)+40:.0f}Z" fill="{cols[i%len(cols)]}" stroke="#0004"/>'
    return b
BAT=lambda x,y,s:f'<path d="M0 0c-6-12-18-16-36-8 6 0 10 4 12 10 4-2 8 0 10 6 4-4 10-4 14 0 2-6 6-8 10-6 2-6 6-10 12-10C-4-16 6-12 0 0z" transform="translate({x} {y}) scale({s})" fill="#0b0413"/>'

# ---------------- scene backdrops (1200x520, drawn to be cropped to fit) ----------------
def fogband(y,h,op,seed,col='#c8a8ff'):
    r=random.Random(seed); return ''.join(f'<ellipse cx="{r.uniform(-50,1250):.0f}" cy="{y+r.uniform(-h/3,h/3):.0f}" rx="{r.uniform(160,340):.0f}" ry="{h*r.uniform(.35,.6):.0f}" fill="{col}" opacity="{op*r.uniform(.5,1):.2f}" filter="url(#blur)"/>' for _ in range(9))
def mansion(x,y,s):
    w='#ffb347'
    sil=(f'<g transform="translate({x} {y}) scale({s})" fill="#0e0618">'
        '<path d="M-150 0V-120H-110V-160L-80-200-50-160V-120H50V-150L90-230 130-150V-120H160V0Z"/>'
        '<path d="M-20-120V-170L10-215 40-170V-120Z"/><path d="M8-212l2-30 2 30z"/><path d="M88-228l2-22 2 22z"/>'
        '<path d="M-150-120L-130-140H160L170-120Z"/></g>')
    win=''.join(f'<rect x="{x+wx*s:.0f}" y="{y+wy*s:.0f}" width="{14*s:.0f}" height="{20*s:.0f}" rx="{3*s:.0f}" fill="{w}" opacity="{o}" filter="url(#glow)"/>'
        for wx,wy,o in ((-125,-100,.95),(-95,-100,.4),(-65,-150,.9),(-30,-60,.85),(5,-160,1),(40,-60,.35),(80,-180,.95),(110,-100,.9),(135,-60,.6),(-125,-50,.7)))
    return sil+win
def pumpkin(x,y,s):
    return (f'<g transform="translate({x} {y}) scale({s})"><ellipse cx="0" cy="0" rx="46" ry="34" fill="#ff8a1f" filter="url(#pglow)" opacity=".55"/>'
        '<path d="M0-30c-26 0-38 12-38 28s14 26 38 26 38-10 38-26-12-28-38-28z" fill="url(#pk)" stroke="#8a3a00" stroke-width="2"/>'
        '<path d="M0-30c-11 4-13 50 0 54M0-30c11 4 13 50 0 54M-22-26c-9 8-9 40 0 48M22-26c9 8 9 40 0 48" fill="none" stroke="#8a3a00" stroke-opacity=".55" stroke-width="1.6"/>'
        '<path d="M-2-29q0-12 9-16" stroke="#3a7d2a" stroke-width="5" fill="none" stroke-linecap="round"/>'
        '<path d="M-20-8l8-8 6 9zM20-8l-8-8-6 9zM-20 8q20 14 40 0l-5-2-5 5-5-5-5 5-5-5-5 5-5-5z" fill="#ffe08a"/></g>')
def fence(y):
    b=f'<path d="M0 {y}H1200M0 {y+26}H1200" stroke="#120820" stroke-width="5"/>'
    for x in range(10,1200,22): b+=f'<path d="M{x} {y+44}V{y-14}l5-10 5 10V{y+44}z" fill="#120820"/>'
    return b
def halloween():
    d=(lg('s',[(0,'#0b0418'),(.45,'#2a0f45'),(.78,'#6b2463'),(1,'#c4573e')])+rg('m',[(0,'#fffbe8'),(.6,'#ffe2a0'),(1,'#f0a94a')],.42,.38,.62)
       +rg('g',[(0,'rgba(255,190,110,.55)'),(.5,'rgba(255,140,80,.18)'),(1,'rgba(255,140,80,0)')])+lg('pk',[(0,'#ffb04a'),(1,'#d4560a')])
       +lg('hz',[(0,'rgba(255,120,60,0)'),(1,'rgba(255,120,60,.35)')])
       +'<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="22"/></filter>'
       +'<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
       +'<filter id="pglow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="14"/></filter>')
    b=sky('s')+stars(120,320,2)+'<rect y="250" width="1200" height="200" fill="url(#hz)"/>'
    b+='<circle cx="930" cy="130" r="230" fill="url(#g)"/><circle cx="930" cy="130" r="78" fill="url(#m)"/>'
    b+=''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#c98a3a" opacity=".22"/>' for x,y,r in ((905,105,13),(955,150,10),(920,160,6),(965,105,8),(940,125,4)))
    b+='<g fill="#2a1240" opacity=".75"><ellipse cx="880" cy="150" rx="120" ry="9"/><ellipse cx="990" cy="168" rx="90" ry="7"/><ellipse cx="820" cy="96" rx="70" ry="5"/></g>'
    b+=skyline(5,400,40,150,'#1a0a2c',lit='#ff9f4a',p=.18,x0=0,x1=560)
    b+=hills(360,40,'#160828',3)+mansion(930,330,1.05)+hills(420,20,'#0f0619',8)
    b+=fogband(400,90,.18,4)+tree(70,470,1.5,7,'#07020d')+tree(1150,480,1.25,11,'#07020d')+tree(470,430,.6,4,'#0f0619')
    for i,x in enumerate(range(160,1080,110)):
        y=462+(i*17)%20; b+=f'<path d="M{x} {y}v-28a12 12 0 0124 0v28z" fill="#1f1230" stroke="#4a2a66" stroke-width="2"/>'
    b+=fence(440)+fogband(470,70,.22,9,'#b48cff')
    b+=BAT(905,95,1.1)+BAT(1010,60,.7)+BAT(860,170,.55)+BAT(320,80,.8)+BAT(560,130,.5)+BAT(180,150,.4)
    b+=pumpkin(60,488,.9)+pumpkin(1140,492,.75)
    return svg(b+'<rect y="496" width="1200" height="24" fill="#05020a"/>',d)
def valentines():
    r=random.Random(3); d=lg('s',[(0,'#3a0a22'),(1,'#7a1a44')])+lg('c',[(0,'#4a0d2a'),(.5,'#8c2058'),(1,'#4a0d2a')],False)+rg('bk',[(0,'rgba(255,170,210,.55)'),(1,'rgba(255,170,210,0)')])
    g=lambda x:38+50*abs(math.sin(x/1200*math.pi*3)); b=sky('s')+bokeh(3,22,'bk')+heart(600,250,9,'#ff6fb5',0,.07)
    b+='<path d="M'+' L'.join(f'{x} {g(x):.0f}' for x in range(0,1201,20))+'" fill="none" stroke="#e6c27a" stroke-width="3"/>'
    for x in range(60,1200,80): b+=f'<path d="M{x} {g(x):.0f}v14" stroke="#e6c27a"/>'+heart(x,g(x)+26,1.3,r.choice(['#ff4d7a','#ff8fb8','#e0243f']),r.uniform(-15,15))
    b+='<path d="M0 0H200Q150 200 210 520H0Z" fill="url(#c)"/><path d="M1200 0H1000Q1050 200 990 520H1200Z" fill="url(#c)"/>'
    b+='<path d="M60 0Q40 260 70 520M120 0Q100 260 130 520M1140 0Q1160 260 1130 520M1080 0Q1100 260 1070 520" stroke="#2a0616" stroke-opacity=".5" stroke-width="6" fill="none"/>'
    b+='<rect y="470" width="1200" height="50" fill="#2a0616"/>'+''.join(heart(r.uniform(230,970),r.uniform(480,510),r.uniform(.5,.9),'#ff4d7a',r.uniform(-60,60),.55) for _ in range(26))
    return svg(b,d)
def easter():
    r=random.Random(8); d=lg('s',[(0,'#8fd3ff'),(1,'#eaf8ff')])+rg('sun',[(0,'#fff8c0'),(1,'rgba(255,240,150,0)')])
    b=sky('s')+'<circle cx="1010" cy="90" r="140" fill="url(#sun)"/><circle cx="1010" cy="90" r="46" fill="#fff3a8"/>'+hills(340,34,'#9be27f',2)+hills(390,26,'#7fd66a',6)
    b+=''.join(f'<path d="M{x} 440V392l7-9 7 9v48z" fill="#fff" stroke="#d9dee8" stroke-width="1.5"/>' for x in range(0,1200,38))+'<rect y="402" width="1200" height="6" fill="#fff" stroke="#d9dee8"/><rect y="422" width="1200" height="6" fill="#fff" stroke="#d9dee8"/>'+hills(455,18,'#5cc24a',4)
    for _ in range(46):
        x=r.uniform(0,1200); y=r.uniform(470,505); b+=f'<path d="M{x:.0f} {y:.0f}v18" stroke="#2f8f3a" stroke-width="2"/><circle cx="{x:.0f}" cy="{y:.0f}" r="{r.uniform(4,7):.0f}" fill="{r.choice(["#ff7aa8","#ffd23f","#c79bff","#ffffff","#ff9a5a"])}"/><circle cx="{x:.0f}" cy="{y:.0f}" r="1.8" fill="#fff7a0"/>'
    return svg(b,d)
def clover(x,y,s,f='#2fbf5a'): return f'<g transform="translate({x:.0f} {y:.0f}) scale({s})" fill="{f}" opacity=".9"><circle cx="-6" cy="-6" r="6"/><circle cx="6" cy="-6" r="6"/><circle cx="-6" cy="6" r="6"/><circle cx="6" cy="6" r="6"/></g>'
def stpat():
    r=random.Random(4); d=lg('s',[(0,'#0a2c48'),(.6,'#1d6a6a'),(1,'#2a8a5a')])+rg('gd',[(0,'rgba(255,220,100,.7)'),(1,'rgba(255,220,100,0)')])
    b=sky('s')+stars(50,200,4,'#e6fff0')
    for i,c in enumerate(['#ff5a5a','#ffb347','#f5e642','#4dff8a','#5ab0ff','#b06cff']): rr=420-i*20; b+=f'<path d="M{600-rr} 440A{rr} {rr} 0 0 1 {600+rr} 440" fill="none" stroke="{c}" stroke-width="20" opacity=".8"/>'
    b+=hills(455,18,'#0f5a34',6)+'<circle cx="1030" cy="425" r="70" fill="url(#gd)"/><path d="M990 440q0 52 40 52t40-52z" fill="#15130f"/><ellipse cx="1030" cy="440" rx="40" ry="9" fill="#2a2620"/>'
    b+=''.join(f'<circle cx="{1010+i*10+r.uniform(-3,3):.0f}" cy="{432-(i%3)*6}" r="9" fill="#f5c542" stroke="#b8860b" stroke-width="2"/>' for i in range(5))
    b+=''.join(clover(r.uniform(20,1180),r.uniform(480,512),r.uniform(.8,1.5)) for _ in range(34))
    return svg(b,d)
def independence():
    d=lg('s',[(0,'#04081c'),(.7,'#0f1f5a'),(1,'#2a2f7a')]); b=sky('s')+stars(90,320,6)
    for cx,cy,c in ((250,150,'#ff6b6b'),(620,100,'#8fb0ff'),(940,180,'#ffffff')): b+=''.join(f'<line x1="{cx}" y1="{cy}" x2="{cx+math.cos(a*math.pi/12)*70:.0f}" y2="{cy+math.sin(a*math.pi/12)*70:.0f}" stroke="{c}" stroke-width="2" stroke-linecap="round" opacity=".35"/>' for a in range(24))
    return svg(b+skyline(12,470,90,230,'#060b26')+'<rect y="480" width="1200" height="40" fill="#03061a"/>'+bunting(['#d7263d','#f4f6ff','#3b57c8']),d)
def newyear():
    r=random.Random(21); d=lg('s',[(0,'#070b26'),(1,'#1d1a5e')])+rg('bk',[(0,'rgba(255,215,120,.5)'),(1,'rgba(255,215,120,0)')])
    b=sky('s')+bokeh(21,16,'bk',500)
    for _ in range(90):
        x,y,w,h=r.uniform(0,1200),r.uniform(0,520),r.uniform(5,10),r.uniform(10,20); b+=f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{r.choice(["#f5c542","#ffd86b","#e8ecff","#b8c4ff","#ff9ac1"])}" opacity="{r.uniform(.5,.95):.2f}" transform="rotate({r.uniform(0,180):.0f} {x+w/2:.0f} {y+h/2:.0f})"/>'
    for i in range(6): y=r.uniform(40,300); b+=f'<path d="M0 {y:.0f}C300 {y+r.uniform(-90,90):.0f} 700 {y+r.uniform(-90,90):.0f} 1200 {y+r.uniform(-60,60):.0f}" fill="none" stroke="{"#f5c542" if i%2 else "#dfe6ff"}" stroke-width="3" opacity=".55"/>'
    return svg(b+''.join(star4(r.uniform(0,1200),r.uniform(0,480),r.uniform(.8,2),'#fff8d0',r.uniform(.5,1)) for _ in range(16)),d)
def nye():
    r=random.Random(31); d=lg('s',[(0,'#050a1e'),(1,'#183066')])+rg('bk',[(0,'rgba(255,220,150,.5)'),(1,'rgba(255,220,150,0)')])
    b=sky('s')+stars(60,240,3)+bokeh(31,14,'bk',420)+skyline(3,470,60,200,'#070d2a',x0=0,x1=520)+skyline(9,470,60,200,'#070d2a',x0=680,x1=1200)
    b+='<g stroke="#8a97c8" stroke-width="3" fill="none"><path d="M590 80V480M610 80V480"/>'+''.join(f'<path d="M590 {y}L610 {y+24}M610 {y}L590 {y+24}"/>' for y in range(100,470,48))+'</g><rect x="574" y="70" width="52" height="14" rx="3" fill="#a9b6e6"/><path d="M600 70V38" stroke="#a9b6e6" stroke-width="3"/><circle cx="600" cy="34" r="5" fill="#ffd86b"/>'
    return svg(b+'<rect y="480" width="1200" height="40" fill="#03061a"/>',d)
def thanks():
    r=random.Random(41); d=lg('s',[(0,'#3a1c0a'),(1,'#1a0d05')])+rg('gl',[(0,'rgba(255,190,90,.35)'),(1,'rgba(255,190,90,0)')],.5,.1,.7)
    b=sky('s')+''.join(f'<rect x="{x}" width="3" height="520" fill="#000" opacity=".25"/>' for x in range(0,1200,100))+sky('gl')
    for x in (70,1130):
        b+=f'<rect x="{x-9}" y="220" width="18" height="300" fill="#2a1408"/>'+''.join(f'<circle cx="{x+r.uniform(-70,70):.0f}" cy="{r.uniform(90,260):.0f}" r="{r.uniform(26,58):.0f}" fill="{r.choice(["#e8762c","#c4452a","#f0b23c","#a4531f"])}" opacity=".55"/>' for _ in range(12))
    g=lambda x:20+34*abs(math.sin(x/400*math.pi)); b+='<path d="M'+' L'.join(f'{x} {g(x):.0f}' for x in range(0,1201,20))+'" fill="none" stroke="#5a3a18" stroke-width="3"/>'
    for x in range(10,1200,26): b+=f'<ellipse cx="{x}" cy="{g(x)+10:.0f}" rx="7" ry="13" fill="{r.choice(["#e8762c","#c4452a","#f0b23c","#a4531f","#7a8a2a"])}" transform="rotate({r.uniform(-40,40):.0f} {x} {g(x):.0f})"/>'
    return svg(b,d)
def tribute(vet):
    r=random.Random(52 if vet else 51); top,mid,low=('#1a2a5a','#6a5a8a','#f0a050') if vet else ('#0a1030','#2a2a5a','#c46a3a')
    d=lg('s',[(0,top),(.6,mid),(1,low)])+rg('sun',[(0,'rgba(255,200,120,.75)'),(1,'rgba(255,200,120,0)')])
    b=sky('s')+('' if vet else stars(40,220,7))+'<circle cx="600" cy="460" r="260" fill="url(#sun)"/>'+hills(430,26,'#2a2a4a' if vet else '#1a1a3a',3)+hills(470,16,'#0c0c22',5)
    fy=120 if vet else 175; b+=f'<rect x="298" y="{fy-14}" width="5" height="{490-fy}" fill="#cfd6e6"/><circle cx="300" cy="{fy-16}" r="6" fill="#e6c27a"/>'
    for i in range(7): b+=f'<rect x="303" y="{fy+i*12}" width="190" height="12" fill="{"#d7263d" if i%2==0 else "#f4f6ff"}" transform="skewY(3)"/>'
    b+=f'<rect x="303" y="{fy}" width="84" height="48" fill="#3b57c8" transform="skewY(3)"/>'+''.join(f'<circle cx="{312+c*16}" cy="{fy+9+rr*13}" r="2" fill="#fff" transform="skewY(3)"/>' for c in range(5) for rr in range(3))
    if vet: b+=''.join(f'<path d="M{x} {y}q10-10 20 0q10-10 20 0" fill="none" stroke="#1a1a3a" stroke-width="3" stroke-linecap="round"/>' for x,y in ((760,120),(830,90),(900,140),(980,100),(700,70)))
    else:
        for _ in range(70):
            x=r.uniform(0,1200); y=r.uniform(485,512); b+=f'<path d="M{x:.0f} {y:.0f}q{r.uniform(-6,6):.0f} 12 0 24" stroke="#1f5a2a" stroke-width="2" fill="none"/><circle cx="{x:.0f}" cy="{y:.0f}" r="{r.uniform(5,9):.0f}" fill="#d7263d"/><circle cx="{x:.0f}" cy="{y:.0f}" r="2" fill="#1a1a1a"/>'
    return svg(b+'<rect y="505" width="1200" height="15" fill="#070714"/>',d)

# ---------------- emblems (100x100 round badges) ----------------
def badge(inner,c1,c2):
    return svg(f'<circle cx="50" cy="50" r="47" fill="url(#b)" stroke="#fff" stroke-opacity=".7" stroke-width="2.5"/><circle cx="50" cy="50" r="42" fill="none" stroke="#fff" stroke-opacity=".22"/>{inner}',rg('b',[(0,c1),(1,c2)],.35,.3,.9),'0 0 100 100','xMidYMid meet')
def em():
    E={}
    E['christmas']=badge('<path d="M50 18l14 22H55l12 18H55l14 20H31l14-20H33l12-18H36z" fill="#2f8145" stroke="#164a26" stroke-width="2" stroke-linejoin="round"/><rect x="46" y="78" width="8" height="8" fill="#6a3a1a"/><path d="M50 8l3 7 8 1-6 5 2 8-7-4-7 4 2-8-6-5 8-1z" fill="#f5c542"/><circle cx="44" cy="52" r="3.4" fill="#e0243f"/><circle cx="58" cy="66" r="3.4" fill="#f5c542"/><circle cx="46" cy="70" r="3.4" fill="#5ab0ff"/>','#9c1f2b','#4a0d18')
    E['halloween']=badge('<path d="M50 30c-24 0-34 14-34 28s12 24 34 24 34-10 34-24-10-28-34-28z" fill="#ff8a1f" stroke="#a84a00" stroke-width="2.5"/><path d="M50 30c-10 4-12 46 0 52M50 30c10 4 12 46 0 52" fill="none" stroke="#a84a00" stroke-opacity=".55" stroke-width="2"/><path d="M48 30q0-10 8-14" stroke="#3a7d2a" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M28 52l10-7 8 10zM72 52l-10-7-8 10z" fill="#ffe27a"/><path d="M30 68q20 14 40 0l-6-3-5 5-5-5-5 5-5-5z" fill="#ffe27a"/>','#5a2a7a','#1a0b2e')
    E['valentines']=badge('<path d="M50 80C16 58 16 24 38 24c8 0 12 7 12 7s4-7 12-7c22 0 22 34-12 56z" fill="#e0243f" stroke="#8a0f26" stroke-width="2.5"/><path d="M32 36q4-6 10-4" stroke="#fff" stroke-opacity=".6" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M20 76L82 22" stroke="#e6c27a" stroke-width="3" stroke-linecap="round"/><path d="M82 22l-4 12M82 22l-12 4" stroke="#e6c27a" stroke-width="3" stroke-linecap="round"/>','#e0508a','#5a1236')
    E['easter']=badge('<ellipse cx="50" cy="54" rx="26" ry="34" fill="#ffb6d9" stroke="#c9508a" stroke-width="2.5"/><path d="M25 46l9-7 8 7 8-7 8 7 8-7 9 7M25 62l9-7 8 7 8-7 8 7 8-7 9 7" fill="none" stroke="#fff" stroke-width="4" stroke-linejoin="round"/><circle cx="50" cy="76" r="3.5" fill="#9ed8ff"/><circle cx="38" cy="30" r="3" fill="#ffe27a"/><circle cx="62" cy="30" r="3" fill="#b9f0a0"/><ellipse cx="40" cy="36" rx="5" ry="9" fill="#fff" opacity=".4" transform="rotate(20 40 36)"/>','#c79bff','#4a3a8a')
    E['stpatricks']=badge('<g fill="#2fbf5a" stroke="#0f6a30" stroke-width="2.5">'+''.join(f'<path d="M50 50C36 40 36 22 46 22c3 0 4 4 4 4s1-4 4-4c10 0 10 18-4 28z" transform="rotate({a} 50 50)"/>' for a in (0,120,240))+'</g><path d="M50 50Q54 68 62 80" stroke="#0f6a30" stroke-width="4" fill="none" stroke-linecap="round"/><circle cx="50" cy="50" r="4" fill="#0f6a30"/>','#1f9a5a','#063a1e')
    E['independence']=badge('<path d="M50 14l9 22 24 2-18 16 6 24-21-13-21 13 6-24-18-16 24-2z" fill="#f4f6ff" stroke="#3b57c8" stroke-width="2.5" stroke-linejoin="round"/><path d="M50 8v-2M14 30l-3-2M86 30l3-2M50 92v2" stroke="#ff6b6b" stroke-width="3" stroke-linecap="round"/><circle cx="50" cy="50" r="7" fill="#d7263d"/>','#3b57c8','#0a1240')
    E['thanksgiving']=badge(''.join(f'<ellipse cx="50" cy="42" rx="7" ry="26" fill="{c}" stroke="#0004" transform="rotate({a} 50 62)"/>' for a,c in zip((-60,-40,-20,0,20,40,60),('#c4452a','#e8762c','#f0b23c','#7a8a2a','#f0b23c','#e8762c','#c4452a')))+'<circle cx="50" cy="64" r="20" fill="#8a4a1e" stroke="#4a2408" stroke-width="2.5"/><circle cx="50" cy="52" r="10" fill="#a45a24" stroke="#4a2408" stroke-width="2"/><circle cx="46" cy="50" r="1.8" fill="#111"/><circle cx="54" cy="50" r="1.8" fill="#111"/><path d="M48 55l2 4 2-4z" fill="#f5c542"/><path d="M50 58v6" stroke="#d7263d" stroke-width="3" stroke-linecap="round"/>','#e8762c','#4a1e08')
    E['new_years_eve']=badge('<circle cx="50" cy="52" r="30" fill="#f4f6ff" stroke="#3b4a8a" stroke-width="3"/>'+''.join(f'<path d="M50 26v4" stroke="#3b4a8a" stroke-width="2.5" transform="rotate({a} 50 52)"/>' for a in range(0,360,30))+'<path d="M50 52V32M50 52l-2 0" stroke="#111" stroke-width="3.5" stroke-linecap="round"/><path d="M50 52L50 36" stroke="#d7263d" stroke-width="2" stroke-linecap="round"/><circle cx="50" cy="52" r="3" fill="#111"/><path d="M22 20l3 6 6 3-6 3-3 6-3-6-6-3 6-3zM80 16l2 4 4 2-4 2-2 4-2-4-4-2 4-2z" fill="#ffd86b"/>','#3b4a8a','#0a1030')
    E['new_years']=badge('<path d="M28 30h20l-2 16q-2 8-8 8t-8-8z" fill="#ffe9a8" stroke="#b8860b" stroke-width="2.5" transform="rotate(-14 38 54)"/><path d="M52 30h20l-2 16q-2 8-8 8t-8-8z" fill="#ffe9a8" stroke="#b8860b" stroke-width="2.5" transform="rotate(14 62 54)"/><path d="M34 56v22M66 56v22M26 80h16M58 80h16" stroke="#b8860b" stroke-width="3" stroke-linecap="round" transform="rotate(0)"/><circle cx="50" cy="24" r="3" fill="#fff"/><circle cx="42" cy="16" r="2" fill="#ffd86b"/><circle cx="60" cy="18" r="2.5" fill="#ffd86b"/>','#8a6a1a','#1a1440')
    E['memorial']=badge(''.join(f'<circle cx="{50+math.cos(a)*15:.0f}" cy="{46+math.sin(a)*15:.0f}" r="14" fill="#d7263d" stroke="#8a0f26" stroke-width="2"/>' for a in [i*2*math.pi/5-math.pi/2 for i in range(5)])+'<circle cx="50" cy="46" r="7" fill="#1a1a1a"/><path d="M50 62Q46 78 54 90" stroke="#2f8f3a" stroke-width="4" fill="none" stroke-linecap="round"/>','#3b57c8','#0a1240')
    return E
for n,s in (('halloween',halloween()),('valentines',valentines()),('easter',easter()),('stpatricks',stpat()),('independence',independence()),('new_years',newyear()),('new_years_eve',nye()),('thanksgiving',thanks()),('memorial',tribute(False))): out(n,'scene',s)
for n,s in em().items(): out(n,'emblem',s)
# ---------------- Halloween contest trophy: golden cup topped with a pumpkin ----------------
def trophy():
    d=lg('cup',[(0,'#fff1b0'),(.45,'#f5c542'),(1,'#a8740c')],False)+lg('pk',[(0,'#ffb04a'),(1,'#d9600a')])
    b=('<path d="M30 52H18c-8 0-12 6-12 14s6 16 18 18" fill="none" stroke="#c9961a" stroke-width="6" stroke-linecap="round"/>'
       '<path d="M90 52h12c8 0 12 6 12 14s-6 16-18 18" fill="none" stroke="#c9961a" stroke-width="6" stroke-linecap="round"/>'
       '<path d="M26 48h68c0 36-14 56-34 58-20-2-34-22-34-58z" fill="url(#cup)" stroke="#8a5a00" stroke-width="2.5"/>'
       '<path d="M36 56c0 22 6 36 14 42" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="4" stroke-linecap="round"/>'
       '<path d="M52 106h16l4 18H48z" fill="url(#cup)" stroke="#8a5a00" stroke-width="2"/>'
       '<rect x="34" y="124" width="52" height="12" rx="3" fill="#5a2a7a" stroke="#2a0f3e" stroke-width="2"/>'
       '<rect x="28" y="136" width="64" height="12" rx="3" fill="#3a1650" stroke="#1a0b2e" stroke-width="2"/>'
       '<path d="M60 20c-18 0-26 9-26 18s9 14 26 14 26-5 26-14-8-18-26-18z" fill="url(#pk)" stroke="#a84a00" stroke-width="2"/>'
       '<path d="M60 20c-7 3-8 29 0 32M60 20c7 3 8 29 0 32" fill="none" stroke="#a84a00" stroke-opacity=".5" stroke-width="1.6"/>'
       '<path d="M58 21q0-9 7-12" stroke="#3a7d2a" stroke-width="4" fill="none" stroke-linecap="round"/>'
       '<path d="M46 34l6-5 4 7zM74 34l-6-5-4 7z" fill="#2a0f3e"/><path d="M47 42q13 8 26 0l-4-2-4 3-5-3-5 3-4-3z" fill="#2a0f3e"/>')
    return svg(b,d,'0 0 120 152','xMidYMid meet')
out('halloween','trophy',trophy())
print(sorted(os.listdir(R)))

# ---------------- UI art: brand mark, hero scenes, map card, reward illustrations, admin wallpaper ----------------
GLOW='<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
SOFT='<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter>'
def brand():
    d=lg('bg',[(0,'#7b5cff'),(1,'#ff5fa2')],False)+lg('hl',[(0,'rgba(255,255,255,.55)'),(1,'rgba(255,255,255,0)')])
    b=('<rect x="4" y="4" width="92" height="92" rx="26" fill="url(#bg)"/><rect x="4" y="4" width="92" height="46" rx="26" fill="url(#hl)" opacity=".5"/>'
       '<path d="M30 64c4 6 11 9 19 9 10 0 17-5 17-13 0-18-34-10-34-27 0-7 7-12 16-12 7 0 12 3 15 7" fill="none" stroke="#fff" stroke-width="8" stroke-linecap="round"/>'
       '<circle cx="72" cy="28" r="7" fill="#fff"/>')
    return svg(b,d,'0 0 100 100','xMidYMid meet')
def christmas():
    d=(lg('s',[(0,'#06102a'),(.6,'#173a6a'),(1,'#3b6aa0')])+rg('gl',[(0,'rgba(255,214,140,.7)'),(1,'rgba(255,214,140,0)')])+SOFT
       +'<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    r=random.Random(12)
    b=sky('s')+stars(70,260,5)+'<path d="M0 120Q300 60 600 140T1200 90" stroke="#7affc4" stroke-opacity=".18" stroke-width="40" fill="none" filter="url(#soft)"/>'
    b+=hills(360,30,'#d8e6f5',4)+skyline(14,420,40,120,'#12244a',lit='#ffd27a',p=.3,x0=0,x1=1200)
    b+='<g filter="url(#glow)">'+''.join(f'<circle cx="{x}" cy="{300+18*math.sin(x/70):.0f}" r="3.5" fill="{["#ff5a6e","#ffd36b","#6dffb0","#8fd8ff"][i%4]}"/>' for i,x in enumerate(range(10,1200,34)))+'</g>'
    b+=f'<path d="M0 {300+18*math.sin(0):.0f}'+''.join(f'L{x} {300+18*math.sin(x/70):.0f}' for x in range(10,1201,10))+'" stroke="#0a1530" stroke-width="1.5" fill="none" opacity=".6"/>'
    b+=hills(450,18,'#eef5ff',9)
    for x,sc in ((150,1.3),(260,.9),(1000,1.4),(1110,1.0),(640,.7)):
        b+=f'<g transform="translate({x} 470) scale({sc})"><circle cx="0" cy="-60" r="60" fill="url(#gl)"/><path d="M0-120L-40-50H-20L-50 0H50L20-50H40Z" fill="#1d5a3a" stroke="#0e3a24" stroke-width="2"/><path d="M0-132l4 9 10 1-7 7 2 10-9-5-9 5 2-10-7-7 10-1z" fill="#ffd36b"/>'
        b+=''.join(f'<circle cx="{r.uniform(-30,30):.0f}" cy="{r.uniform(-90,-10):.0f}" r="3.5" fill="{r.choice(["#ff5a6e","#ffd36b","#8fd8ff"])}" filter="url(#glow)"/>' for _ in range(7))+'</g>'
    b+=''.join(f'<circle cx="{r.uniform(0,1200):.0f}" cy="{r.uniform(0,500):.0f}" r="{r.uniform(1,3.2):.1f}" fill="#fff" opacity="{r.uniform(.4,.95):.2f}"/>' for _ in range(160))
    return svg(b,d)
def hero_default():
    d=lg('s',[(0,'#0b1022'),(1,'#1b2347')])+rg('a',[(0,'rgba(123,92,255,.55)'),(1,'rgba(123,92,255,0)')])+rg('c',[(0,'rgba(95,243,255,.4)'),(1,'rgba(95,243,255,0)')])
    b=sky('s')+'<circle cx="300" cy="80" r="360" fill="url(#a)"/><circle cx="980" cy="420" r="380" fill="url(#c)"/>'+stars(70,520,9)
    b+=''.join(f'<path d="M0 {y}Q300 {y-60} 600 {y}T1200 {y}" fill="none" stroke="#ffffff" stroke-opacity=".05" stroke-width="2"/>' for y in range(200,520,26))
    return svg(b,d)
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
def reward(kind):
    d=rg('halo',[(0,'rgba(255,255,255,.28)'),(1,'rgba(255,255,255,0)')])+lg('pk',[(0,'#ffb04a'),(1,'#d4560a')])+lg('gold',[(0,'#fff1b0'),(.5,'#f5c542'),(1,'#a8740c')])+GLOW
    b='<circle cx="80" cy="80" r="78" fill="url(#halo)"/>'
    if kind=='candy':
        b+=('<path d="M42 64h76l-8 70H50z" fill="#7b3fb0" stroke="#3a1458" stroke-width="3"/><path d="M42 64l10-12h56l10 12" fill="#9a5ad0" stroke="#3a1458" stroke-width="3"/>'
            '<path d="M60 100q20 16 40 0" stroke="#ffd36b" stroke-width="5" fill="none" stroke-linecap="round"/><circle cx="66" cy="88" r="5" fill="#ffd36b"/><circle cx="94" cy="88" r="5" fill="#ffd36b"/>'
            '<g transform="rotate(-25 56 46)"><rect x="40" y="38" width="32" height="16" rx="8" fill="#ff5a8a"/><path d="M40 46l-10-8v16zM72 46l10-8v16z" fill="#ff9ab8"/></g>'
            '<g transform="rotate(20 106 42)"><rect x="92" y="34" width="28" height="14" rx="7" fill="#5ad0ff"/><path d="M92 41l-9-7v14zM120 41l9-7v14z" fill="#a8e6ff"/></g>')
    elif kind=='scare':
        b+=('<path d="M80 22c-30 0-48 22-48 52 0 36 22 64 48 64s48-28 48-64c0-30-18-52-48-52z" fill="#f2f5fa" stroke="#9aa6c0" stroke-width="3"/>'
            '<path d="M52 66q10-14 24-4-6 18-24 4zM108 66q-10-14-24-4 6 18 24 4z" fill="#14081f"/><ellipse cx="80" cy="108" rx="13" ry="20" fill="#14081f"/>'
            '<path d="M24 40l-12-8M136 40l12-8M20 80H6M140 80h14" stroke="#ff8a1f" stroke-width="5" stroke-linecap="round" filter="url(#glow)"/>')
    elif kind=='ghost':
        b+=('<path d="M38 140V72c0-28 18-46 42-46s42 18 42 46v68l-12-10-10 10-10-10-10 10-10-10-10 10-10-10z" fill="#eafcff" stroke="#9fd8ff" stroke-width="3" filter="url(#glow)"/>'
            '<ellipse cx="66" cy="74" rx="7" ry="9" fill="#1a0b2e"/><ellipse cx="94" cy="74" rx="7" ry="9" fill="#1a0b2e"/><ellipse cx="80" cy="98" rx="8" ry="11" fill="#1a0b2e"/>'
            '<path d="M126 40l4 8 8 2-8 3-4 8-3-8-8-3 8-2z" fill="#ffd36b"/><path d="M30 104l3 6 6 2-6 2-3 6-2-6-6-2 6-2z" fill="#b06cff"/>')
    elif kind=='empty':
        b+=('<path d="M30 76L80 34l50 42" fill="#241335" stroke="#6a4a8a" stroke-width="4" stroke-linejoin="round"/><rect x="40" y="74" width="80" height="62" fill="#1c0f2a" stroke="#6a4a8a" stroke-width="4"/>'
            '<rect x="70" y="98" width="20" height="38" fill="#0b0412"/><rect x="50" y="86" width="14" height="14" fill="#0b0412"/><rect x="96" y="86" width="14" height="14" fill="#0b0412"/>'
            '<path d="M112 28c8 0 12 4 12 10s-6 8-6 14M118 60v2" stroke="#9aa6c0" stroke-width="4" fill="none" stroke-linecap="round"/>')
    elif kind=='gift':
        b+=('<rect x="34" y="66" width="92" height="70" rx="6" fill="#ff5a6e" stroke="#8a1a2a" stroke-width="3"/><rect x="28" y="52" width="104" height="22" rx="5" fill="#ff7a8a" stroke="#8a1a2a" stroke-width="3"/>'
            '<rect x="72" y="52" width="16" height="84" fill="#ffd36b"/><path d="M80 52c-10-4-30-14-26-24s20 0 26 22c6-22 22-32 26-22s-16 20-26 24z" fill="#ffd36b" stroke="#a8740c" stroke-width="2.5"/>')
    elif kind=='coins':
        b+=''.join(f'<ellipse cx="{x}" cy="{y}" rx="30" ry="10" fill="url(#gold)" stroke="#8a5a00" stroke-width="2"/><rect x="{x-30}" y="{y-8}" width="60" height="8" fill="#c9961a"/><ellipse cx="{x}" cy="{y-8}" rx="30" ry="10" fill="url(#gold)" stroke="#8a5a00" stroke-width="2"/>' for x,y in ((60,128),(60,112),(60,96),(104,128),(104,112)))
        b+='<circle cx="104" cy="64" r="26" fill="url(#gold)" stroke="#8a5a00" stroke-width="3"/><text x="104" y="73" text-anchor="middle" font-family="Georgia,serif" font-size="26" font-weight="700" fill="#8a5a00">$</text>'
    elif kind=='star':
        b+=''.join(f'<path d="M80 80L{80+math.cos(a)*62:.0f} {80+math.sin(a)*62:.0f}" stroke="{c}" stroke-width="4" stroke-linecap="round" filter="url(#glow)"/>' for a,c in zip([i*math.pi/6 for i in range(12)],['#ff6b6b','#ffd36b','#5b8cff','#ffffff']*3))
        b+='<path d="M80 50l9 20 22 2-17 14 5 22-19-12-19 12 5-22-17-14 22-2z" fill="url(#gold)" stroke="#8a5a00" stroke-width="2.5"/>'
    return svg(b,d,'0 0 160 160','xMidYMid meet')
def wallpaper():
    d=lg('s',[(0,'#0a0f1f'),(1,'#141a33')])+rg('a',[(0,'rgba(123,92,255,.6)'),(1,'rgba(123,92,255,0)')])+rg('b',[(0,'rgba(255,95,162,.45)'),(1,'rgba(255,95,162,0)')])+rg('c',[(0,'rgba(95,243,255,.35)'),(1,'rgba(95,243,255,0)')])+SOFT
    b='<rect width="1200" height="800" fill="url(#s)"/><circle cx="220" cy="140" r="420" fill="url(#a)"/><circle cx="1040" cy="200" r="380" fill="url(#b)"/><circle cx="700" cy="760" r="460" fill="url(#c)"/>'
    b+=''.join(f'<path d="M-50 {y}C250 {y-140} 500 {y+120} 800 {y-30}S1150 {y-90} 1260 {y}" fill="none" stroke="#ffffff" stroke-opacity="{.035+.01*(i%3):.3f}" stroke-width="{1.5+i%3}"/>' for i,y in enumerate(range(260,800,34)))
    return svg(b,d,'0 0 1200 800')
out('christmas','scene',christmas()); out('default','hero',hero_default()); out('halloween','map',citymap()); out('admin','wallpaper',wallpaper())
os.makedirs(f'{R}/rewards',exist_ok=True)
for k in ('candy','scare','ghost','empty','gift','coins','star'): out('rewards',k,reward(k))
open(f'{R}/brand.svg','w').write(brand())

# ---------------- Labor Day ----------------
def crane(x,y,s,c):
    return (f'<g transform="translate({x} {y}) scale({s})" stroke="{c}" stroke-width="5" fill="none">'
        '<path d="M0 0V-300M14 0V-300M0-300H14"/>'+''.join(f'<path d="M0 {-k}L14 {-k-20}"/>' for k in range(0,300,20))+
        '<path d="M-80-300H260M-80-300L7-340 260-300M7-340V-300"/><path d="M200-300V-200" stroke-width="2"/><rect x="190" y="-200" width="20" height="16" fill="'+c+'"/><rect x="-80" y="-310" width="40" height="24" fill="'+c+'"/></g>')
def labor():
    d=lg('s',[(0,'#0e1a3a'),(.5,'#3a3a6a'),(.82,'#f08a4a'),(1,'#ffd27a')])+rg('sun',[(0,'#fff0c0'),(1,'#ff9a4a')])
    b=sky('s')+stars(30,140,6)+'<circle cx="760" cy="350" r="110" fill="url(#sun)" opacity=".95"/>'
    b+=skyline(23,400,60,190,'#1a1a34',lit='#ffcf6a',p=.2)+crane(240,400,1,'#14142a')+crane(980,400,.8,'#14142a')
    b+='<g fill="#14142a"><rect x="520" y="160" width="160" height="240" fill="none" stroke="#14142a" stroke-width="6"/>'+''.join(f'<rect x="520" y="{y}" width="160" height="6"/>' for y in range(160,400,40))+''.join(f'<rect x="{x}" y="160" width="6" height="240"/>' for x in range(520,681,40))+'</g>'
    b+='<path d="M0 400H1200" stroke="#14142a" stroke-width="10"/>'+''.join(f'<path d="M{x} 400L{x+40} 360L{x+80} 400" stroke="#14142a" stroke-width="5" fill="none"/>' for x in range(0,1200,80))
    b+='<rect y="404" width="1200" height="116" fill="#2a2a3a"/>'+''.join(f'<rect x="{x}" y="452" width="60" height="6" fill="#ffc247" opacity=".6"/>' for x in range(20,1200,120))
    return svg(b,d)
def em_labor():
    return badge('<path d="M20 64c0-22 13-36 30-36s30 14 30 36z" fill="#ffc247" stroke="#a8740c" stroke-width="3"/><rect x="14" y="62" width="72" height="10" rx="5" fill="#ffd36b" stroke="#a8740c" stroke-width="3"/><path d="M50 28v34M40 32c-2 10-2 20 0 30M60 32c2 10 2 20 0 30" stroke="#a8740c" stroke-width="2.5" fill="none"/>','#3a6ab8','#0e1a3a')
out('labor','scene',labor()); out('labor','emblem',em_labor())
