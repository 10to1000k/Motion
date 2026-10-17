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
art=ROOT/'assets/art'
images={name:Image.open(art/(name+'.jpg')).convert('RGB').resize((1080,1080),Image.Resampling.LANCZOS) for name in ['origin','zurvan','duality','world']}
# Narrative cuts have independent camera directions, animated foregrounds and dissolves.
scenes=[(0,7,'origin'),(7,19,'zurvan'),(19,28,'duality'),(28,35,'origin'),(35,43,'zurvan'),(43,50,'world'),(50,56,'origin'),(56,60,'zurvan')]
def shot(index,t):
    start,end,name=scenes[index]; u=max(0,min(1,(t-start)/(end-start)))
    smooth=u*u*(3-2*u)
    scale=1.03+.09*(smooth if index%2==0 else 1-smooth)
    side=int(1080/scale)
    x=int((1080-side)*(.25+.5*smooth)); y=int((1080-side)*(.35 if name=='zurvan' else .6))
    return images[name].crop((x,y,x+side,y+side)).resize((W,H),Image.Resampling.BICUBIC).convert('RGBA')

# Soft darkening at the base keeps Persian titles readable.
grad=np.zeros((1080,1080,4),dtype=np.uint8)
for y in range(1080): grad[y,:,3]=int(max(0,(y-560)/520)*224)
shade=Image.fromarray(grad)
chapters=[(0,7,'پیش از جهان، زمان بود','بی‌آغاز • بی‌پایان'),(7,19,'زَروان','زمانِ بی‌کران'),(19,28,'روشنایی و تاریکی','دو نیرو، در روایت زَروانی'),(28,35,'یک روایت، نه تمام تاریخ','زَروانی‌گری؛ یکی از سنت‌های دینی ایران'),(35,43,'چهره‌ای برای بی‌کرانگی','تصویری نمادین و خیالی'),(43,50,'همه‌چیز می‌گذرد','ستارگان، روزها، آدمیان'),(50,56,'زمان در ماست؟','یا ما در زمان زندگی می‌کنیم؟'),(56,60,'زَروان','پدرِ اسطوره‌ایِ زمانِ بی‌کران')]
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
cmd=[ff,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1080x1080','-r',str(FPS),'-i','-','-i','assets/audio/narration.flac','-filter_complex','[1:a]adelay=700|700,apad,afade=t=out:st=59:d=1[a]','-map','0:v','-map','[a]','-t','60','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','deliverables/zurvan-instagram.mp4']
p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=open('render.log','w'))
for n in range(FPS*DURATION):
    t=n/FPS
    index=next(i for i,(start,end,name) in enumerate(scenes) if start<=t<end)
    frame=shot(index,t)
    start,end,name=scenes[index]
    if index>0 and t-start<.85:
        mix=(t-start)/.85; mix=mix*mix*(3-2*mix)
        frame=Image.blend(shot(index-1,t),frame,mix)
    frame.alpha_composite(shade)
    fx=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(fx)
    # Fine orbiting time marks frame the symbolic portrait.
    cx,cy=540,485
    for k in range(96):
        a=2*math.pi*k/96+t*.025
        r=445; leng=12 if k%8==0 else 4
        d.line((cx+math.cos(a)*r,cy+math.sin(a)*r,cx+math.cos(a)*(r+leng),cy+math.sin(a)*(r+leng)),fill=(212,175,100,105 if k%8==0 else 45),width=2 if k%8==0 else 1)
    if name=='origin':
        # Expanding orbit wavefronts suggest the birth and infinity of time.
        for j in range(7):
            radius=35+((t*24+j*76)%530)
            alpha=int(100*(1-radius/600))
            d.ellipse((540-radius,450-radius,540+radius,450+radius),outline=(219,180,104,alpha),width=2)
        for j in range(3):
            a=t*.18+j*2.094
            px=540+math.cos(a)*310;py=450+math.sin(a)*150
            d.ellipse((px-3,py-3,px+3,py+3),fill=(255,227,161,210))
    elif name=='duality':
        # Opposing currents: distinct warm and cool moving particle streams.
        for j in range(100):
            u=(j/100+t*.06)%1
            yy=150+u*570
            sway=90*math.sin(u*5+t*.35)
            for xx,col in [(340+sway,(255,211,132,150)),(740-sway,(160,170,248,125))]:
                r=1+(j%3)*.6
                d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=col)
    elif name=='world':
        # Falling golden grains over the ruins, independent of camera movement.
        for j in range(120):
            xx=80+(j*71)%920
            yy=180+((j*83+t*(18+j%17))%590)
            d.line((xx,yy,xx-3,yy+5),fill=(232,191,119,55+j%65),width=1)
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
    if n==9*FPS: frame.convert('RGB').save('deliverables/cover.jpg',quality=95)
    if n in [4*FPS,12*FPS,23*FPS,46*FPS]: frame.convert('RGB').save(f'deliverables/scene-{int(t):02d}.jpg',quality=91)
    p.stdin.write(frame.convert('RGB').tobytes())
    if n%240==0: print(f'{t:.0f}/60 seconds',flush=True)
p.stdin.close()
if p.wait()!=0: raise RuntimeError('Encoding failed; see render.log')
print('DONE',flush=True)
