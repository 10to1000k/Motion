from PIL import Image, ImageDraw, ImageFont
import numpy as np, math, random, subprocess, wave
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display
import imageio_ffmpeg

ROOT=Path(__file__).parent
W=H=1080; FPS=24; DURATION=60
ff=imageio_ffmpeg.get_ffmpeg_exe()
font=lambda size: ImageFont.truetype(str(ROOT/'assets/Vazirmatn-Regular.ttf'),size)
def rtl(s): return get_display(arabic_reshaper.reshape(s))
def text(draw,s,y,size,color=(237,216,167,255)):
    draw.text((540,y),rtl(s),font=font(size),fill=color,anchor='mt')
base=Image.open(ROOT/'media/zurvan.png').convert('RGB').resize((1080,1080),Image.Resampling.LANCZOS)
# Soft darkening at the base keeps Persian titles readable.
grad=np.zeros((1080,1080,4),dtype=np.uint8)
for y in range(1080): grad[y,:,3]=int(max(0,(y-560)/520)*224)
shade=Image.fromarray(grad)
chapters=[(0,7,'پیش از جهان، زمان بود','بی‌آغاز • بی‌پایان'),(7,15,'زَروان','زمانِ بی‌کران'),(15,24,'فراتر از روز و شب','روایتی از ایران باستان'),(24,33,'روشنایی و تاریکی','اهورامزدا و اهریمن، در روایت زَروانی'),(33,41,'یک روایت، نه تمام تاریخ','زَروانی‌گری؛ یکی از سنت‌های دینی ایران'),(41,49,'همه‌چیز می‌گذرد','ستارگان، روزها، آدمیان'),(49,56,'زمان در ماست؟','یا ما در زمان زندگی می‌کنیم؟'),(56,60,'زَروان','پدرِ اسطوره‌ایِ زمانِ بی‌کران')]
cards=[]
for start,end,title,sub in chapters:
    card=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(card)
    d.line((450,806,630,806),fill=(201,162,88,220),width=2)
    text(d,title,836,76 if title=='زَروان' else 47)
    text(d,sub,934,27,(216,207,189,255))
    cards.append((start,end,card))
random.seed(42)
stars=[(random.uniform(50,1030),random.uniform(65,790),random.uniform(.5,2),random.random()*6.28,random.uniform(5,17)) for _ in range(85)]
Path('deliverables').mkdir(exist_ok=True)
cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1080x1080','-r',str(FPS),'-i','-','-i','media/narration.wav','-filter_complex','[1:a]adelay=700|700,apad,afade=t=out:st=59:d=1[a]','-map','0:v','-map','[a]','-t','60','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','deliverables/zurvan-instagram.mp4']
p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=open('render.log','w'))
for n in range(FPS*DURATION):
    t=n/FPS
    # A continuous camera push, not a static slide.
    scale=1.0+.09*t/60
    side=int(1080/scale); x=(1080-side)//2; y=int((1080-side)*.36)
    frame=base.crop((x,y,x+side,y+side)).resize((W,H),Image.Resampling.BICUBIC).convert('RGBA')
    frame.alpha_composite(shade)
    fx=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(fx)
    # Fine orbiting time marks frame the symbolic portrait.
    cx,cy=540,485
    for k in range(96):
        a=2*math.pi*k/96+t*.025
        r=445; leng=12 if k%8==0 else 4
        d.line((cx+math.cos(a)*r,cy+math.sin(a)*r,cx+math.cos(a)*(r+leng),cy+math.sin(a)*(r+leng)),fill=(212,175,100,105 if k%8==0 else 45),width=2 if k%8==0 else 1)
    for sx,sy,r,ph,speed in stars:
        yy=60+(sy-60-t*speed*.15)%740
        alpha=int(55+130*(.5+.5*math.sin(t*.7+ph)))
        d.ellipse((sx-r,yy-r,sx+r,yy+r),fill=(255,222,159,alpha))
    d.rectangle((38,38,1042,1042),outline=(200,165,99,65),width=1)
    text(d,'ایرانِ اسطوره‌ای',61,20,(222,202,161,190))
    frame.alpha_composite(fx)
    for start,end,card in cards:
        if start<=t<end:
            opacity=min(1,(t-start)/.6,(end-t)/.6)
            temp=card.copy();temp.putalpha(card.getchannel('A').point(lambda a:int(a*max(0,opacity))))
            frame.alpha_composite(temp)
            break
    fade=min(1,t/1.3,(60-t)/1.1)
    if fade<1: frame=Image.blend(Image.new('RGBA',(W,H),(5,9,18,255)),frame,max(0,fade))
    if n==8*FPS: frame.convert('RGB').save('deliverables/cover.jpg',quality=95)
    p.stdin.write(frame.convert('RGB').tobytes())
    if n%240==0: print(f'{t:.0f}/60 seconds',flush=True)
p.stdin.close()
if p.wait()!=0: raise RuntimeError('Encoding failed; see render.log')
print('DONE',flush=True)
