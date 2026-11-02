import subprocess, sys, numpy as np, json
def pcm(p):
    r=subprocess.run(['ffmpeg','-v','error','-i',p,'-af','pan=mono|c0=0.5*c0+0.5*c1','-f','f32le','-acodec','pcm_f32le','-'],capture_output=True)
    return np.frombuffer(r.stdout,dtype=np.float32)
def lvl(x,sr,a,b):
    S=np.abs(np.fft.rfft(x*np.hanning(len(x))))**2; f=np.fft.rfftfreq(len(x),1/sr)
    return 10*np.log10(S[(f>=a)&(f<b)].sum()/len(x)**2+1e-20)
res={}
for p in sys.argv[1:]:
    x=pcm(p); res[p]={k:round(lvl(x,48000,a,b),2) for k,(a,b) in {'lt250':(20,250),'mid':(250,4000),'pres2_4k':(2000,4000),'sib5_9k':(5000,9000)}.items()}
for c in ['female_hi','male_hi','sibilant_numbers_hi']:
    b=res[f'base_{c}.wav']
    for k in ['base','candA','candB','candC','candD','candE']:
        r=res[f'{k}_{c}.wav']; print(f"{k+'_'+c:30}", ' '.join(f"{n}={v:7.2f}({v-b[n]:+5.2f})" for n,v in r.items()))
json.dump(res,open('bandlevels.json','w'),indent=1)
