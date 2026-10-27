import numpy as np, subprocess
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile
SR = 48000; DUR = 24.0; N = int(SR * DUR)
rng = np.random.default_rng(3)
def T(n): return np.arange(n) / SR
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
L = np.zeros(N); R = np.zeros(N)       # music bus
SL = np.zeros(N); SRr = np.zeros(N)    # sfx bus
def add(bus, x, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR); x = x[:max(0, N - i)]
    l, r = bus
    l[i:i + len(x)] += x * gain * np.sqrt((1 - pan) / 2) * 1.414
    r[i:i + len(x)] += x * gain * np.sqrt((1 + pan) / 2) * 1.414
MUS = (L, R); SFX = (SL, SRr)
def env(n, a, d, curve=4):
    t = T(n); e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-curve * np.maximum(0, t - a) / max(d, 1e-4)); return e
def saw(f, n, ph=0): t = T(n); return 2 * ((t * f + ph) % 1) - 1
def sine(f, n): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(f, (n,))) / SR)
def noise(n): return rng.standard_normal(n)

# ---------------- MUSIC (120 BPM, beat = .5s) ----------------
chords = {  # bar start (s): midi notes
}
prog = [(0, [45, 52, 57, 58]),  # tension: A + Bb rub
        (2.7, [41, 53, 57, 60, 64]), (4.7, [36, 52, 55, 60, 64]), (6.7, [43, 55, 59, 62, 67]), (8.7, [45, 57, 60, 64, 69]),
        (10.7, [41, 53, 57, 60, 65]), (12.7, [36, 52, 55, 60, 67]), (14.7, [43, 55, 59, 62, 69]), (16.7, [45, 57, 60, 64, 71]),
        (18.0, [41, 53, 57, 60, 64, 69]), (19.5, [36, 52, 55, 60, 64, 67]), (21.1, [41, 57, 60, 64, 67]), (22.3, [36, 48, 55, 60, 64, 67, 72])]
for k, (t0, notes) in enumerate(prog):
    t1 = prog[k + 1][0] if k + 1 < len(prog) else DUR
    n = int((t1 - t0 + .6) * SR); tt = T(n)
    e = np.minimum(1, tt / .25) * np.clip((t1 - t0 + .6 - tt) / .6, 0, 1)
    pad = np.zeros(n)
    for m in notes[1:]:
        for det in (-.08, 0, .07): pad += saw(mtof(m + det), n, rng.random()) * .05
    bright = 1400 if t0 < 18 else 3200
    if t0 < 2.7: bright = 700
    pad = lp(pad, bright) * e
    pan = .0
    add(MUS, pad, t0, .55 if t0 >= 2.7 else .45, -.25); add(MUS, pad[::-1][::-1], t0 + .012, .55 if t0 >= 2.7 else .45, .25)
    # bass: 8th pulses with sidechain shape
    root = notes[0]
    if t0 >= 2.7:
        for b in np.arange(t0, t1 - 1e-6, .25):
            if 8.95 < b < 9.2 or 17.85 < b < 18.0: continue
            bn = int(.24 * SR); x = (sine(mtof(root), bn) * .7 + lp(saw(mtof(root), bn), 400) * .5) * env(bn, .01, .2, 3)
            add(MUS, x, b, .5)
# tension drone 0–2.7: pulse
n = int(2.75 * SR); tt = T(n)
dr = (sine(mtof(33), n) * .6 + sine(mtof(45) * 1.003, n) * .25 + sine(mtof(46), n) * .12) * (0.6 + .4 * (np.sin(2 * np.pi * 4 * tt) > 0)) * np.minimum(1, tt / .05) * np.clip((2.75 - tt) / .3, 0, 1)
add(MUS, lp(dr, 500), 0, .6)
# kick + hats
def kick():
    n = int(.4 * SR); tt = T(n); f = 45 + 90 * np.exp(-tt * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) + lp(noise(n), 3000) * np.exp(-tt * 120) * .2
K = kick()
for b in np.arange(2.75, 23.0, .5):
    if 8.95 < b < 9.2 or 17.6 < b < 18.0: continue
    add(MUS, K, b, .55 if b < 18 else .65)
hat = hp(noise(int(.05 * SR)), 7000) * env(int(.05 * SR), .001, .03)
for b in np.arange(3.0, 23.0, .5):
    if 17.6 < b < 18.0: continue
    add(MUS, hat, b, .12, .3)
for b in np.arange(18.125, 23.0, .25): add(MUS, hat, b, .06, -.3)
clap = bp(noise(int(.2 * SR)), 800, 4000) * env(int(.2 * SR), .002, .12)
for b in np.arange(3.25, 23.0, 1.0):
    if 17.5 < b < 18.0: continue
    add(MUS, clap, b, .14)
# arpeggio plucks 16ths from 5.6
def pluck(m, bright):
    n = int(.3 * SR); return lp(saw(mtof(m), n) + saw(mtof(m) * 1.005, n), bright) * env(n, .003, .18, 5) * .18
for k, (t0, notes) in enumerate(prog):
    if t0 < 5.0: continue
    t1 = prog[k + 1][0] if k + 1 < len(prog) else 22.4
    pat = [notes[1] + 12, notes[2] + 12, notes[3] + 12, notes[2] + 12, notes[-1] + 12, notes[3] + 12]
    st = max(t0, 5.6); i = 0
    for b in np.arange(st, t1 - 1e-6, .125):
        if 8.95 < b < 9.2 or 17.7 < b < 18.0: continue
        add(MUS, pluck(pat[i % len(pat)], 2600 if b < 18 else 4200), b, .7, .4 if i % 2 else -.4); i += 1

# ---------------- SFX ----------------
def boom(dur=1.6, f0=55):
    n = int(dur * SR); tt = T(n); f = f0 + 60 * np.exp(-tt * 20)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3) + lp(noise(n), 900) * np.exp(-tt * 14) * .5
def whoosh(dur, f0=300, f1=3000, rev=False):
    n = int(dur * SR); tt = T(n); x = noise(n); out = np.zeros(n); seg = 512
    for s in range(0, n, seg):
        q = s / n; fc = f0 * (f1 / f0) ** q
        out[s:s + seg] = bp(x[max(0, s - 2048):s + seg], fc * .6, min(fc * 1.6, 20000))[-len(out[s:s + seg]):]
    e = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    if rev: e = (tt / dur) ** 3
    return out * e
def blip(f, dur=.08, g=1):
    n = int(dur * SR); return sine(f, n) * env(n, .002, dur * .5, 5) * g
def click():
    n = int(.03 * SR); return hp(noise(n), 2500) * env(n, .0005, .008, 6) + np.pad(blip(2400, .02) * .5, (0, n - int(.02 * SR)))
def chime(ms, step=.06, dur=1.2):
    n = int((dur + step * len(ms)) * SR); out = np.zeros(n)
    for i, m in enumerate(ms):
        k = int(i * step * SR); nn = n - k; tt = T(nn)
        out[k:] += (np.sin(2 * np.pi * mtof(m) * tt) + .3 * np.sin(2 * np.pi * mtof(m) * 2.01 * tt)) * np.exp(-tt * 4) * np.minimum(1, tt / .003)
    return out * .3
def riser(dur, f0=200, f1=2000):
    n = int(dur * SR); tt = T(n); f = f0 * (f1 / f0) ** (tt / dur)
    return (whoosh(dur, 400, 8000, rev=True) * .6 + np.sin(2 * np.pi * np.cumsum(f) / SR) * (tt / dur) ** 2 * .3)
def pop(f=900):
    n = int(.12 * SR); tt = T(n); fr = f * (1 + 1.5 * np.exp(-tt * 60))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * 30) * .5
def lockclick():
    a = click() * 1.5; n = int(.9 * SR); tt = T(n)
    ring_ = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, d in [(1870, 7), (2930, 9), (4410, 12)]) * .12
    th = boom(.3, 70) * .6
    out = np.zeros(n); out[:len(a)] += a; out += ring_; out[:len(th)] += th; out[int(.045 * SR):int(.045 * SR) + len(a)] += a * .8
    return out
def crush(dur):
    n = int(dur * SR); x = noise(n); x = np.repeat(x[::40], 40)[:n]; tt = T(n)
    f = 1200 * np.exp(-tt * 12) + 80
    return (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .3 + x * .3) * np.exp(-tt * 10)
def sparkle(dur, k=40, lo=3000, hi=7000):
    n = int(dur * SR); out = np.zeros(n)
    for i in range(k):
        s = int(rng.random() * (n - 3000)); b = blip(lo + rng.random() * (hi - lo), .04, .3); out[s:s + len(b)] += b
    return out
# timeline
add(SFX, boom(1.8, 50), 0.0, .9)
add(SFX, boom(1.0, 70), .17, .55)
for i, t in enumerate([.35, .65, .95]): add(SFX, blip(1700 + i * 300, .1), t, .25, [-.7, .6, -.2][i])
add(SFX, whoosh(.36, 300, 6000, rev=True), 1.5, .5)
add(SFX, boom(.8, 65), 1.86, .4); add(SFX, boom(.8, 60), 2.15, .45)
add(SFX, whoosh(.5, 200, 4000, rev=True), 2.2, .7)
add(SFX, whoosh(.5, 3000, 300), 2.7, .4)
add(SFX, click(), 3.65, .9, -.4)
add(SFX, whoosh(.8, 500, 5000), 3.82, .45, 0)
add(SFX, boom(.4, 90) * .5, 4.6, .55); add(SFX, chime([88, 95], .03, .6), 4.6, .5)
add(SFX, chime([76, 79, 84], .07, 1.0), 5.3, .45)
add(SFX, riser(.45, 300, 3000), 5.15, .5); add(SFX, sparkle(.6), 5.6, .35)
# granular ascending synth 5.6–7.5
for i in range(60):
    tt0 = 5.65 + i * .03; add(SFX, blip(400 * 2 ** (i / 24) + rng.random() * 50, .05, .25), tt0, .5, rng.uniform(-.8, .8))
add(SFX, lockclick(), 7.5, 1.0)
for i in range(4): add(SFX, blip(1300 + i * 200, .06), 7.8 + i * .12, .35, .5)
add(SFX, chime([81, 88], .05, .8), 8.4, .3, .5)
add(SFX, riser(.4, 300, 4000), 8.6, .55)
add(SFX, boom(.6, 80), 9.0, .45)
for i, t in enumerate([9.9, 10.0, 10.1]): add(SFX, pop(900 + i * 120), t, .6, [-.5, -.3, -.1][i])
add(SFX, boom(.6, 60), 9.85, .4); add(SFX, chime([84, 79], .1, .8), 9.95, .25)
add(SFX, whoosh(.42, 300, 7000), 11.6, .7, -.3)
for i in range(6): add(SFX, blip(900 + i * 150, .05), 12.4 + i * .1, .2, .3)
add(SFX, whoosh(.25, 6000, 800), 12.82, .3)
add(SFX, crush(.35), 13.0, .45, .4); add(SFX, boom(.7, 45), 13.0, .55)
add(SFX, chime([72, 76, 79, 84], .04, 1.0), 13.4, .4)
add(SFX, whoosh(.42, 400, 6000), 14.7, .7, .3)
add(SFX, click(), 15.85, .9, .3); add(SFX, sparkle(.6, 50, 2500, 6000) + 0, 16.05, .45, .4)
add(SFX, whoosh(.6, 4000, 9000) * .5, 16.05, .3, .5)
add(SFX, chime([79, 83, 86, 91], .06, 1.1), 16.75, .35)
add(SFX, riser(.4, 200, 3000), 17.6, .6)
add(SFX, boom(2.0, 48), 18.0, .8); add(SFX, chime([72, 79, 84, 88], .03, 1.6), 18.0, .35)
for i, t in enumerate([18.2, 18.68, 19.16]): add(SFX, whoosh(.35, 600, 5000), t - .1, .35, [.6, -.6, .6][i]); add(SFX, boom(.35, 90), t + .15, .3)
n = int(.35 * SR); tt = T(n); boing = np.sin(2 * np.pi * np.cumsum(300 + 500 * (tt / .35) ** .5 + 30 * np.sin(2 * np.pi * 14 * tt)) / SR) * env(n, .01, .3, 3) * .35
add(SFX, boing, 20.35, .7)
add(SFX, sparkle(.4, 20, 5000, 9000), 20.45, .4)
add(SFX, riser(.35, 400, 5000), 20.75, .55)
add(SFX, boom(1.5, 50), 21.1, .7)
# brand signature: three memorable notes + tail
sig = np.zeros(int(2.9 * SR))
for i, (m, t) in enumerate([(76, 0), (83, .16), (88, .32)]):
    k = int(t * SR); nn = len(sig) - k; tt = T(nn)
    tone = (np.sin(2 * np.pi * mtof(m) * tt) + .45 * np.sin(2 * np.pi * mtof(m) * 2 * tt) + .2 * np.sin(2 * np.pi * mtof(m) * 3.01 * tt)) * np.exp(-tt * (2.5 if i == 2 else 5)) * np.minimum(1, tt / .004)
    sig[k:] += tone * .32
add(SFX, sig, 21.12, .7)
add(SFX, whoosh(.3, 800, 6000), 21.9, .35)
for i in range(21): add(SFX, click() * .5, 22.3 + i * .5 / 21, .35, rng.uniform(-.3, .3))
add(SFX, chime([88, 91, 96], .05, 1.0), 23.1, .2)

# ---------------- reverb ----------------
def reverb(x, dur=2.2, seed=0):
    n = int(dur * SR); tt = T(n); ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-tt * 3.2); ir = lp(ir, 6000); ir /= np.sqrt((ir ** 2).sum())
    return fftconvolve(x, ir)[:len(x)]
for bus, wet in ((MUS, .35), (SFX, .22)):
    l, r = bus; wl, wr = reverb(l, seed=1), reverb(r, seed=2)
    l += wl * wet; r += wr * wet

# ---------------- voice + ducking ----------------
VO = np.zeros(N)
place = [('l1a', .05), ('l1b', 2.18), ('l2', 2.8), ('l3', 5.75), ('l4', 9.15), ('l5', 11.85), ('l6', 15.05), ('l7', 18.1), ('l8', 21.42)]
for name, t0 in place:
    sr, x = wavfile.read(f'vo/{name}.wav'); x = x.astype(float) / 32768
    x = hp(x, 90); x /= np.max(np.abs(x)) + 1e-9
    i = int(t0 * SR); VO[i:i + len(x)] += x[:N - i] * .8
    print(name, t0, round(t0 + len(x) / SR, 2))
vo_env = np.convolve(np.abs(VO), np.ones(2400) / 2400, 'same')
duck = 1 - .6 * np.clip(vo_env / .08, 0, 1)
duck = np.convolve(duck, np.ones(4800) / 4800, 'same')
mus_g, sfx_g = .55, .55
outL = L * mus_g * duck + SL * sfx_g * (0.55 + .45 * duck) + VO
outR = R * mus_g * duck + SRr * sfx_g * (0.55 + .45 * duck) + VO
out = np.stack([outL, outR], 1); out /= np.max(np.abs(out)) / .89
wavfile.write('mix_raw.wav', SR, (out * 32767).astype(np.int16))
