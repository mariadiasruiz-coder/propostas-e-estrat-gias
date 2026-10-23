"""Tratamento e edição das vozes reais (sem alterar falas, sem acelerar):
pré-nivelamento por trecho -> declip, HPF, redução leve de ruído, EQ, de-esser, compressão ->
nivelamento fino (-18 LUFS por locutora) -> montagem na timeline do trailer com micro-fades."""
import sys, os, subprocess, tempfile
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import VOICE, DUR, WORK
from dsp import SR, secs

REGIONS = [  # (S0, S1, quem)
    (0.0, 4.60, 'duda_cam'), (4.60, 15.15, 'duda_vo'), (15.15, 27.283, 'duda_cam'),
    (27.283, 39.85, 'lais'), (39.85, 51.567, 'duda_vo'), (51.567, 59.06, 'fernanda'),
    (59.06, 64.933, 'duda_vo'), (64.933, 85.57, 'duda_cam'),
]
TARGET = -18.0
CHAIN = ('adeclip,highpass=f=75:p=2,afftdn=nr=7:nf=-44:tn=1,'
         'equalizer=f=280:t=q:w=1.0:g=-2.0,equalizer=f=3200:t=q:w=0.9:g=1.8,'
         'highshelf=f=9500:g=1.5,deesser=i=0.35:m=0.5:f=0.5,'
         'acompressor=threshold=0.08:ratio=3:attack=6:release=140:knee=4:makeup=1.6')


def region_gain(x, target):
    m = pyln.Meter(SR)
    y = x.copy()
    for s0, s1, _ in REGIONS:
        a, b = secs(s0), min(secs(s1), len(x))
        L = m.integrated_loudness(y[a:b])
        g = 10 ** ((target - L) / 20)
        # transição de 10 ms entre regiões para evitar degraus
        y[a:b] *= g
    return y


def process():
    a, sr = sf.read(os.path.join(WORK, 'src', 'voice48k.wav'))
    assert sr == SR
    mono = a.mean(1)
    pre = region_gain(mono, -20.0)
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, 'i.wav'), os.path.join(d, 'o.wav')
        sf.write(i, pre.astype(np.float32), SR, subtype='FLOAT')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', i, '-af', CHAIN, '-c:a', 'pcm_f32le', o], check=True)
        y, _ = sf.read(o)
    y = y[:len(mono)] if y.ndim == 1 else y[:len(mono), 0]
    y = region_gain(y, TARGET)
    return y


def edit(y):
    out = np.zeros(secs(DUR + 2))
    for s0, s1, t0 in VOICE:
        seg = y[secs(s0):secs(s1)].copy()
        f = secs(0.008)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        i = secs(t0)
        out[i:i + len(seg)] += seg
    return out


if __name__ == '__main__':
    y = process()
    v = edit(y)
    os.makedirs('stems', exist_ok=True)
    sf.write('stems/voice.wav', np.stack([v, v], 1).astype(np.float32), SR, subtype='FLOAT')
    m = pyln.Meter(SR)
    for s0, s1, who in REGIONS:
        print(who, s0, round(m.integrated_loudness(y[secs(s0):secs(s1)]), 1), 'peak', round(np.abs(y[secs(s0):secs(s1)]).max(), 3))
