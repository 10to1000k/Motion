"""Zurvan: a 60-second square film built mostly from time-varying geometry.
No stock footage is used. Artwork is confined to two portrait inserts and ruins.
Run from the repository root; then run add_music.py once.
"""
from pathlib import Path
import math, subprocess, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper
from bidi.algorithm import get_display
import imageio_ffmpeg

ROOT=Path(__file__).parent
W=H=1080; FPS=24
GOLD=(223,179,103); WHITE=(246,231,202); BLUE=(127,169,224)
FONTS={n:ImageFont.truetype(str(ROOT/'assets/Vazirmatn-Regular.ttf'),n) for n in [19,23,27,33,44,54,76,112]}
def rtl(s): return get_display(arabic_reshaper.reshape(s))
def label(d,s,x,y,size=44,color=WHITE,anchor='mt'):
    d.text((x,y),rtl(s),font=FONTS[size],fill=color,anchor=anchor)
def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def rgba(color,a): return (*color,max(0,min(255,int(a))))
rng=np.random.default_rng(123)
yy,xx=np.mgrid[:1080,:1080]
r=np.sqrt(((xx-540)/800)**2+((yy-430)/850)**2)
noise=rng.normal(0,.85,(1080,1080))
bg=np.stack([7+7*np.exp(-r*r*3)+noise,12+9*np.exp(-r*r*3)+noise,23+13*np.exp(-r*r*3)+noise],axis=-1)
BACKGROUND=Image.fromarray(np.uint8(np.clip(bg,0,255))).convert('RGBA')
ART={n:Image.open(ROOT/'assets/art'/f'{n}.jpg').convert('RGB') for n in ['zurvan','world']}
stars=rng.random((420,5)); particles=rng.random((650,5)); dust=rng.random((280,4))
# The narrative alternates scale and form rather than repeating a single layout.
SHOTS=[(0,3,'seed','پیش از جهان، زمان بود','بی‌آغاز • بی‌پایان'),
(3,7,'vortex','زمانِ بی‌کران',''),
(7,13,'portrait','زَروان','روایتی از ایران باستان'),
(13,19,'hourglass','فراتر از روز و شب','نه پادشاه؛ سرچشمه‌ای اسطوره‌ای'),
(19,24,'duality','روشنایی و تاریکی','دو نیرو، در روایت زَروانی'),
(24,28,'duality','از یک سرچشمه','اهورامزدا و اهریمن'),
(28,35,'branches','یک روایت، نه تمام تاریخ','زَروانی‌گری؛ نه باور همهٔ زرتشتیان'),
(35,40,'portrait','چهره‌ای برای بی‌کرانگی','تصویری نمادین و خیالی'),
(40,45,'sphere','ستارگان می‌چرخند','روز به شب می‌رسد'),
(45,50,'ruins','و آدمی می‌گذرد',''),
(50,56,'hourglass','زمان در ماست؟','یا ما در زمان زندگی می‌کنیم؟'),
(56,60,'ending','زَروان','پدرِ اسطوره‌ایِ زمانِ بی‌کران')]

def starfield(d,t,zoom=1):
    for u,v,z,phase,size in stars:
        # Radial travel in depth, not a flat texture translated across the frame.
        depth=.25+((z+t*.018)%1)*1.8
        x=540+(u-.5)*1500/depth*zoom; y=455+(v-.5)*1250/depth*zoom
        if 45<x<1035 and 45<y<1010:
            a=45+100*(.5+.5*math.sin(t*.8+phase*7))
            rad=.6+size/depth
            d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=rgba(WHITE,a))

def orbit(d,t,cx=540,cy=435,scale=1):
    for j in range(4):
        points=[]
        ang=j*.62+t*.1
        for k in range(181):
            a=2*math.pi*k/180
            x=math.cos(a)*(285+j*25)*scale
            y=math.sin(a)*(100+j*21)*scale
            points.append((cx+x*math.cos(ang)-y*math.sin(ang),cy+x*math.sin(ang)+y*math.cos(ang)))
        d.line(points,fill=rgba(GOLD,65+j*18),width=1)
        a=t*(.45+j*.13)+j
        x=math.cos(a)*(285+j*25)*scale;y=math.sin(a)*(100+j*21)*scale
        px=cx+x*math.cos(ang)-y*math.sin(ang);py=cy+x*math.sin(ang)+y*math.cos(ang)
        d.ellipse((px-4,py-4,px+4,py+4),fill=rgba(WHITE,230))

def vortex(d,t,scale=1):
    for radius,phase,vel,size,tint in particles:
        r=25+radius**.6*365*scale
        a=phase*math.tau+t*(.13+vel*.25)+radius*6
        # Long curved streaks have an actual head and trailing path.
        pts=[]
        for k in range(5):
            b=a-k*.012*(1+vel*2)
            pts.append((540+math.cos(b)*r,430+math.sin(b)*r*.76))
        col=WHITE if tint>.8 else GOLD
        d.line(pts,fill=rgba(col,65+size*160),width=1+int(size*1.7))
    for j in range(3):
        r=14+j*7+3*math.sin(t*1.5)
        d.ellipse((540-r,430-r,540+r,430+r),outline=rgba(GOLD,160-j*40),width=2)

def hourglass(d,t):
    cx=540; top=170; bottom=710; half=220
    # The glass silhouette stays rigid; sand really moves inside it.
    for sign in [-1,1]:
        pts=[]
        for k in range(101):
            u=k/100; y=top+(bottom-top)*u
            width=14+half*abs(2*u-1)**.76
            pts.append((cx+sign*width,y))
        d.line(pts,fill=rgba(GOLD,205),width=3)
    for y in [top-13,bottom+13]:
        d.rounded_rectangle((cx-half-20,y-5,cx+half+20,y+5),radius=4,fill=rgba(GOLD,220))
        d.line((cx-half-35,y+14,cx+half+35,y+14),fill=rgba(GOLD,70),width=1)
    for u,v,speed,size,tint in particles:
        phase=(v+t*(.15+speed*.12))%1
        if phase<.43:
            q=phase/.43; y=top+35+q*225; width=(1-q)*170+6
            x=cx+(u-.5)*2*width
        elif phase<.72:
            q=(phase-.43)/.29;y=430+q*230;x=cx+(u-.5)*9+math.sin(q*9+t)*2
        else:
            q=(phase-.72)/.28;y=660+q*38;x=cx+(u-.5)*(100+q*220)
        rr=.8+size*1.4
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=rgba(WHITE if tint>.85 else GOLD,130+size*120))
    # A growing breathing dune; outlines emphasize volume.
    for j in range(8):
        pts=[]
        for k in range(81):
            x=390+k*300/80; y=698-48*max(0,1-abs(x-540)/150)+j*1.7+2*math.sin(t*.7)
            pts.append((x,y))
        d.line(pts,fill=rgba(GOLD,35+j*12),width=1)

def duality(d,t,local):
    # Opposing animated ribbons assembled from hundreds of independent particles.
    for side,color in [(-1,GOLD),(1,BLUE)]:
        for j in range(7):
            pts=[]
            for k in range(145):
                u=k/144
                angle=u*math.tau*1.25+t*.4*side+j*.045
                radius=40+u*325
                x=540+side*math.cos(angle)*radius
                y=440+math.sin(angle)*radius*.84
                pts.append((x,y))
            d.line(pts,fill=rgba(color,30+j*18),width=2)
        for u,v,vel,size,tint in particles[::2]:
            q=(v+t*(.04+vel*.025))%1
            angle=q*math.tau*1.25+t*.4*side
            rad=40+q*325+(u-.5)*40
            x=540+side*math.cos(angle)*rad;y=440+math.sin(angle)*rad*.84
            r=.8+size*2
            d.ellipse((x-r,y-r,x+r,y+r),fill=rgba(color,90+size*155))
    d.ellipse((530,430,550,450),fill=rgba(WHITE,230))

def branches(d,t,local):
    # A visual metaphor for a plurality of traditions, not a historical chart.
    trunk=(540,615)
    nodes=[(235,300),(405,250),(675,250),(845,300)]
    growth=smooth(local/2)
    d.line((540,715,540,615),fill=rgba(GOLD,180),width=3)
    for j,(x,y) in enumerate(nodes):
        end=(540+(x-540)*growth,615+(y-615)*growth)
        pts=[]
        for k in range(61):
            u=k/60; pts.append((540+(end[0]-540)*u,615+(end[1]-615)*(u*u*(3-2*u))))
        col=GOLD if j==1 else BLUE
        d.line(pts,fill=rgba(col,160 if j==1 else 65),width=3 if j==1 else 1)
        rad=8+2*math.sin(t*1.5+j)
        d.ellipse((end[0]-rad,end[1]-rad,end[0]+rad,end[1]+rad),outline=rgba(col,200),width=2)
        for n in range(6):
            q=(n/6+t*.13)%1
            px=540+(end[0]-540)*q;py=615+(end[1]-615)*smooth(q)
            d.ellipse((px-2,py-2,px+2,py+2),fill=rgba(col,200))
    label(d,'روایت‌های اندیشهٔ ایرانی',540,166,27,GOLD)

def sphere(d,t):
    # A rotating celestial globe projected from actual 3D coordinates.
    rot=t*.18
    def project(x,y,z):
        xx=x*math.cos(rot)+z*math.sin(rot);zz=-x*math.sin(rot)+z*math.cos(rot)
        yy=y*.93-zz*.25; depth=1+zz*.0003
        return (540+xx/depth,440+yy/depth),zz
    for latitude in range(-60,90,15):
        lat=math.radians(latitude); pts=[]
        for k in range(181):
            a=k*math.tau/180
            pt,z=project(290*math.cos(lat)*math.cos(a),290*math.sin(lat),290*math.cos(lat)*math.sin(a))
            pts.append(pt)
        d.line(pts,fill=rgba(GOLD,75),width=1)
    for j in range(12):
        pts=[]
        for k in range(181):
            a=k*math.tau/180;lon=j*math.pi/12
            pt,z=project(290*math.cos(a)*math.cos(lon),290*math.sin(a),290*math.cos(a)*math.sin(lon));pts.append(pt)
        d.line(pts,fill=rgba(BLUE,65),width=1)
    orbit(d,t,scale=1.12)
    for u,v,z,size,ph in stars[::3]:
        a=u*math.tau; lat=(v-.5)*math.pi
        p,depth=project(292*math.cos(lat)*math.cos(a),292*math.sin(lat),292*math.cos(lat)*math.sin(a))
        if depth<0:
            r=1+size*1.5;d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=rgba(WHITE,210))

# Cached gradient: keep the entire lower text-safe area dark.
g=np.zeros((1080,1080,4),dtype=np.uint8)
for y in range(1080):g[y,:,3]=int(max(0,min(1,(y-610)/390))*230)
SHADE=Image.fromarray(g)

def frame_at(t):
    idx=next(i for i,(a,b,*_) in enumerate(SHOTS) if a<=t<b)
    a,b,kind,title,sub=SHOTS[idx];local=t-a
    frame=BACKGROUND.copy()
    if kind in ('portrait','ruins'):
        name='zurvan' if kind=='portrait' else 'world';u=local/(b-a)
        side=int(1080/(1.02+.09*smooth(u)));x=int((1080-side)*(.25+.5*u));y=int((1080-side)*.35)
        art=ART[name].resize((1080,1080)).crop((x,y,x+side,y+side)).resize((1080,1080),Image.Resampling.BICUBIC).convert('RGBA')
        frame=Image.blend(frame,art,.92)
    fine=Image.new('RGBA',(1080,1080));d=ImageDraw.Draw(fine)
    starfield(d,t,1.0 if kind not in ('portrait','ruins') else .65)
    if kind=='seed':
        progress=smooth(local/3)
        for j in range(12):
            radius=10+j*19+progress*95
            d.ellipse((540-radius,430-radius,540+radius,430+radius),outline=rgba(GOLD,(1-j/14)*100),width=1)
        for j in range(8):
            r=4+j*3;d.ellipse((540-r,430-r,540+r,430+r),fill=rgba(WHITE,25))
        orbit(d,t,scale=.45+progress*.2)
    elif kind=='vortex':vortex(d,t)
    elif kind=='hourglass':hourglass(d,t);orbit(d,t,scale=1.16)
    elif kind=='duality':duality(d,t,local)
    elif kind=='branches':branches(d,t,local)
    elif kind=='sphere':sphere(d,t)
    elif kind=='ending':vortex(d,t,scale=.86);orbit(d,t,scale=.9)
    elif kind=='portrait':
        # Animated luminous ring passing in front of the portrait.
        for j in range(3):
            pts=[]
            for k in range(161):
                ang=k*math.tau/160
                pts.append((540+math.cos(ang)*(360+j*5),475+math.sin(ang)*(360+j*5)))
            d.line(pts,fill=rgba(GOLD,65-j*20),width=1)
        for n in range(12):
            ang=t*.22+n*math.tau/12;px=540+math.cos(ang)*360;py=475+math.sin(ang)*360
            d.ellipse((px-2,py-2,px+2,py+2),fill=rgba(GOLD,190))
    elif kind=='ruins':
        for u,v,speed,size in dust:
            x=(u*1200+t*(15+speed*15))%1200-60;y=150+(v*650+t*(16+speed*30))%660
            d.line((x,y,x-7,y-4),fill=rgba(GOLD,50+size*90),width=1)
    # Emissive elements receive a bloom pass, then their sharp core.
    glow=fine.resize((360,360)).filter(ImageFilter.GaussianBlur(5)).resize((1080,1080))
    frame.alpha_composite(glow);frame.alpha_composite(fine)
    frame.alpha_composite(SHADE)
    ui=Image.new('RGBA',(1080,1080));d=ImageDraw.Draw(ui)
    d.line((65,90,235,90),fill=rgba(GOLD,140),width=1)
    label(d,'روایتِ زمان',1015,65,23,rgba(GOLD,210),'rt')
    # Draw-on ornaments lead the eye into the title.
    enter=smooth(local/.65);leave=smooth((b-t)/.35)
    span=90*enter
    d.line((540-span,800,540+span,800),fill=rgba(GOLD,200),width=2)
    offset=22*(1-enter)
    if kind=='ending':
        label(d,title,540,816+offset,112,WHITE)
        label(d,sub,540,958+offset,27,GOLD)
    else:
        size=76 if title=='زَروان' else 44
        label(d,title,540,836+offset,size,WHITE)
        if sub:label(d,sub,540,936+offset,27,GOLD)
    # A restrained timeline makes the one-minute structure tangible.
    d.line((65,1020,1015,1020),fill=rgba(GOLD,35),width=1)
    d.line((65,1020,65+950*t/60,1020),fill=rgba(GOLD,165),width=2)
    ui.putalpha(ui.getchannel('A').point(lambda x:int(x*enter*leave)))
    frame.alpha_composite(ui)
    # Short dip-through-ink separates the visual acts; every shot has its own motion.
    transition=min(1,local/.22,(b-t)/.18)
    fade=min(transition,smooth(t/.8),smooth((60-t)/1.0))
    if fade<1:frame=Image.blend(BACKGROUND,frame,max(0,fade))
    return frame.convert('RGB')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',type=float);args=parser.parse_args()
    output=ROOT/'deliverables';output.mkdir(exist_ok=True)
    if args.preview is not None:
        frame_at(args.preview).save(output/'preview.jpg',quality=94);return
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1080x1080','-r','24','-i','-','-i','assets/audio/narration.flac','-filter_complex','[1:a]adelay=700|700,apad,afade=t=out:st=59:d=1[a]','-map','0:v','-map','[a]','-t','60','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(output/'zurvan-instagram.mp4')]
    with open(ROOT/'render.log','w') as log:
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
        try:
            for n in range(1440):
                t=n/24;frame=frame_at(t)
                if n==9*24:frame.save(output/'cover.jpg',quality=95)
                if n in [4*24,12*24,23*24,46*24]:frame.save(output/f'scene-{int(t):02d}.jpg',quality=92)
                p.stdin.write(frame.tobytes())
                if n%240==0:print(f'{int(t)}/60',flush=True)
        finally:p.stdin.close()
        if p.wait():raise RuntimeError('See render.log')
    print('DONE',flush=True)
if __name__=='__main__':main()
