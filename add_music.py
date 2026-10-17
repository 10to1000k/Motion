"""Generate an original, quiet ambient score and mix beneath the existing narrator."""
from pathlib import Path
import numpy as np
import wave, subprocess
import imageio_ffmpeg

root=Path(__file__).parent
sr=44100
seconds=60
t=np.arange(sr*seconds)/sr
rng=np.random.default_rng(28)
left=np.zeros(len(t)); right=np.zeros(len(t))
# Slow consonant drone with softened harmonics; original procedural composition.
for freq,gain,phase in [(73.416,.11,0),(110,.055,.8),(146.832,.035,1.4),(220,.022,2.1)]:
    swell=.65+.35*np.sin(2*np.pi*.035*t+phase)
    left+=gain*swell*np.sin(2*np.pi*freq*t+0.15*np.sin(t*.2))
    right+=gain*swell*np.sin(2*np.pi*(freq+.08)*t+phase*.2)
# Sparse bell-like notes leave ample space for Persian narration.
notes=[293.665,330,440,391.995,293.665,220,261.626,293.665,440,330,293.665,220]
for i,freq in enumerate(notes):
    start=2+i*4.7
    u=t-start; mask=(u>=0)&(u<7)
    x=u[mask]
    env=(1-np.exp(-x*7))*np.exp(-x/1.5)
    tone=.055*env*(np.sin(2*np.pi*freq*x)+.2*np.sin(2*np.pi*freq*2*x))
    pan=.3+.4*(i%3)/2
    left[mask]+=tone*(1-pan);right[mask]+=tone*pan
# Quiet transition sound design: filtered air swells and a soft low impact.
for cut in [7,19,28,35,43,50,56]:
    first=max(0,int((cut-.6)*sr)); last=min(len(t),int((cut+.9)*sr))
    x=t[first:last]-cut
    air=rng.normal(0,1,len(x))
    air=np.convolve(air,np.ones(55)/55,mode='same')
    envelope=np.exp(-(x/.32)**2)
    whoosh=.055*air*envelope
    hit=.035*np.sin(2*np.pi*55*np.maximum(x,0))*np.exp(-np.maximum(x,0)*9)*(x>=0)
    left[first:last]+=whoosh+hit
    right[first:last]+=whoosh[::-1]+hit
fade=np.minimum(1,t/3)*np.minimum(1,(seconds-t)/4)
audio=np.stack([left*fade,right*fade],axis=1)
(root/'media').mkdir(exist_ok=True)
with wave.open(str(root/'media/ambient-score.wav'),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
    w.writeframes((np.clip(audio,-1,1)*32767).astype('<i2').tobytes())
ff=imageio_ffmpeg.get_ffmpeg_exe()
source=root/'deliverables/zurvan-instagram.mp4'
target=root/'deliverables/zurvan-instagram-scored.mp4'
subprocess.run([ff,'-y','-i',str(source),'-i',str(root/'media/ambient-score.wav'),'-filter_complex','[1:a]volume=0.32[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]','-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-t','60','-movflags','+faststart',str(target)],check=True)
target.replace(source)
