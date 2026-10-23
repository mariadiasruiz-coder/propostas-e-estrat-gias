import numpy as np, soundfile as sf, sys
SR=48000
def st_lufs(x, t, win=1.0):
    # aproximação de loudness de curto prazo (K-weighting simplificado: HPF + shelf)
    from scipy import signal
    seg=x[int(t*SR):int((t+win)*SR)]
    if len(seg)==0: return -99
    b,a=signal.butter(2,100,'highpass',fs=SR); seg=signal.lfilter(b,a,seg,axis=0)
    p=(seg**2).mean(0).sum()
    return 10*np.log10(p+1e-12)-0.691
names=sys.argv[1:] or ['out/stem_voz.wav','out/stem_musica.wav','out/stem_sfx.wav','out/master_48k_24bit.wav']
data=[sf.read(n)[0] for n in names]
print('  T   '+'  '.join(f'{n.split("/")[-1][:10]:>10}' for n in names))
for t in np.arange(0,90,1.0):
    print(f'{t:4.0f} '+'  '.join(f'{st_lufs(d,t):10.1f}' for d in data))
