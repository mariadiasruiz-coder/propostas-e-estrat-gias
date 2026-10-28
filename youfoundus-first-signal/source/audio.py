# THE FIRST SIGNAL — original score & sound design (synthesised from scratch, 48 kHz stereo)
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 12.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(2026)
dry = np.zeros((N, 2))
send = np.zeros((N, 2))     # reverb send


def env_ad(n, a, d, curve=1.0):
    x = np.arange(n) / SR
    e = np.where(x < a, (x / max(a, 1e-6)) ** curve, np.exp(-(x - a) / d))
    return e


def place(buf, start, sig, pan=0.0, gain=1.0):
    i = int(start * SR)
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], 1) * np.sqrt(2)
    n = min(len(sig), N - i)
    if n > 0:
        buf[i:i + n] += sig[:n] * gain


def lp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), 'low')
    return signal.lfilter(b, a, x, axis=0)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), 'high')
    return signal.lfilter(b, a, x, axis=0)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    return signal.lfilter(b, a, x, axis=0)


def sub_boom(dur, f0, f1, decay, drive=1.6):
    n = int(dur * SR); x = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-x / 0.06)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env_ad(n, 0.003, decay)
    # gentle saturation adds harmonics so the hit translates on phone speakers
    return np.tanh(s * drive) / np.tanh(drive)


def metal(dur, f0, decay, ratios=(1, 2.32, 3.91, 5.27, 6.83, 8.95), seed=0, bright=1.0):
    n = int(dur * SR); x = np.arange(n) / SR
    r = np.random.default_rng(seed)
    s = np.zeros(n)
    for k, q in enumerate(ratios):
        f = f0 * q * (1 + r.uniform(-0.004, 0.004))
        if f > 19000: continue
        a = (0.75 ** k) * (bright if k > 1 else 1)
        s += a * np.sin(2 * np.pi * f * x + r.uniform(0, 6.28)) * np.exp(-x / (decay / (1 + 0.45 * k)))
    s *= np.minimum(1, x / 0.0007)
    return s / (np.abs(s).max() + 1e-9)


def click(dur=0.03, f=5200, seed=1):
    n = int(dur * SR)
    nz = np.random.default_rng(seed).standard_normal(n)
    return bp(nz, f * 0.6, min(f * 1.6, 20000), 2) * np.exp(-np.arange(n) / SR / 0.004)


def noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n)


def fm_bell(dur, f, idx=2.2, ratio=3.5, decay=0.9):
    n = int(dur * SR); x = np.arange(n) / SR
    mod = idx * np.exp(-x / 0.25) * np.sin(2 * np.pi * f * ratio * x)
    s = np.sin(2 * np.pi * f * x + mod) * env_ad(n, 0.002, decay)
    return s


def pad_voice(freqs, dur, cutoff_curve, seed, detune=0.0035):
    n = int(dur * SR); x = np.arange(n) / SR
    r = np.random.default_rng(seed)
    s = np.zeros(n)
    for f in freqs:
        for d in (-detune, 0, detune):
            ph = r.uniform(0, 1)
            saw = 2 * ((f * (1 + d) * x + ph) % 1) - 1
            s += saw / 3
    # slowly moving one-pole low-pass (analog warmth)
    out = np.zeros(n); y = 0.0
    c = cutoff_curve(x)
    g = 1 - np.exp(-2 * np.pi * c / SR)
    for i in range(n):
        y += g[i] * (s[i] - y); out[i] = y
    out2 = np.zeros(n); y = 0.0
    for i in range(n):
        y += g[i] * (out[i] - y); out2[i] = y
    return out2 / len(freqs)


D1, A1, D2, F2, A2, C3, E3, D3, F3, A3, D4, E4, F4, A4, D5, A5, F5, E5 = (
    36.71, 55.0, 73.42, 87.31, 110.0, 130.81, 164.81, 146.83, 174.61, 220.0, 293.66, 329.63, 349.23, 440.0, 587.33, 880.0, 698.46, 659.25)

# ---------------------------------------------------------------- 00:00 first interruption
place(dry, 0.0, sub_boom(1.6, 95, 41, 0.55, 2.0), gain=0.85)
m = metal(1.4, 412, 0.55, seed=3); place(dry, 0.0, m, -0.15, 0.20); place(send, 0.0, m, 0, 0.30)
place(dry, 0.0, click(0.04, 3800, 4), 0.1, 0.35)
# beam crossing: thin rising tone panned left -> right with the light
n = int(0.55 * SR); x = np.arange(n) / SR
beam = np.sin(2 * np.pi * (2400 * x + 1800 * x * x)) * np.sin(np.pi * x / 0.55) ** 2 * 0.05
pan = np.linspace(-0.8, 0.8, n)
place(dry, 0.02, np.stack([beam * np.cos((pan + 1) * np.pi / 4), beam * np.sin((pan + 1) * np.pi / 4)], 1) * 1.4)

# ---------------------------------------------------------------- drone bed 0 -> 3.8 (D minor, analog)
bed = pad_voice([D2, A2, D3], 3.8, lambda x: 260 + 900 * np.clip(x / 3.5, 0, 1) ** 1.5, 11)
bed *= np.minimum(1, t[:len(bed)] / 0.25) * 0.55
bed[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))      # hard musical cut at 3.80
wob = 0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t[:len(bed)])
place(dry, 0.0, np.stack([bed * (0.8 + 0.2 * wob), bed * (1.0 - 0.2 * wob)], 1), gain=0.9)
# discrete electronic pulse (quarter = 0.38 s), rising
for k, tt in enumerate(np.arange(0.76, 3.70, 0.38)):
    p = sub_boom(0.25, 70, 46, 0.07, 1.2) * 0.22 * (0.4 + 0.6 * k / 7)
    place(dry, tt, p)
    tick = click(0.02, 7000 + 300 * (k % 2), 20 + k) * 0.10 * (0.5 + 0.5 * k / 7)
    place(dry, tt + 0.19, tick, 0.5 if k % 2 else -0.5)

# 00:00.3–01.2 optical texture under the first phrase (filtered granular shimmer)
n = int(1.1 * SR); x = np.arange(n) / SR
gr = bp(noise(n, 30), 5500, 9000, 2) * (np.sin(np.pi * x / 1.1) ** 2)
gr *= 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 37 * x)) * 0.3
place(dry, 0.30, np.stack([gr, np.roll(gr, 240)], 1) * 0.05)
place(send, 0.30, gr * 0.05)

# 01:50 phrase completes — soft analog accent
a = metal(0.9, 293.66, 0.35, ratios=(1, 2, 3.01, 4.2), seed=7, bright=0.5)
place(dry, 1.50, a, 0.2, 0.10); place(send, 1.50, a, 0, 0.12)
place(dry, 1.50, sub_boom(0.6, 70, 44, 0.18), gain=0.35)

# 02:00 air transition (breath of air, band-limited, no generic whoosh)
n = int(1.0 * SR); x = np.arange(n) / SR
air = noise(n, 41)
fc = 900 + 4200 * np.sin(np.pi * x / 1.0) ** 2
air_f = np.zeros(n)
for i0 in range(0, n, 480):
    seg = air[i0:i0 + 480]
    c = fc[i0]
    air_f[i0:i0 + 480] = seg
air_f = bp(air, 1200, 7000, 1) * np.sin(np.pi * x / 1.0) ** 3
place(dry, 1.95, np.stack([air_f * np.linspace(1, 0.4, n), air_f * np.linspace(0.4, 1, n)], 1) * 0.045)

# 02:70–03:30 crossing the optical glass: glassy partials
g = metal(1.2, 1730, 0.5, ratios=(1, 1.503, 2.41, 3.17), seed=9, bright=0.6)
place(dry, 2.78, g, -0.3, 0.06); place(send, 2.78, g, 0, 0.12)
n = int(0.5 * SR); x = np.arange(n) / SR
swp = bp(noise(n, 50), 2500, 11000, 1) * np.sin(np.pi * x / 0.5) ** 2
place(dry, 2.80, np.stack([swp * 0.3, swp], 1) * 0.05)

# ---------------------------------------------------------------- 03:80 silence (true digital silence until 04:00)
# 04:20 sub tension rising into 05:20
n = int(1.0 * SR); x = np.arange(n) / SR
f = 32 + 22 * (x / 1.0) ** 2
ten = np.sin(2 * np.pi * np.cumsum(f) / SR) * (x / 1.0) ** 1.6
ten = np.tanh(ten * 1.8) / np.tanh(1.8)
ten[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))   # 50 ms vacuum before the hit
place(dry, 4.15, ten, gain=0.30)
ris = bp(noise(n, 60), 300, 3000, 1) * (x / 1.0) ** 3
ris[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
place(dry, 4.15, np.stack([ris, np.roll(ris, 300)], 1) * 0.035)
# 04:25 the fissure: hairline crack of light — glass ring + micro ticks
c = metal(1.0, 2637, 0.45, ratios=(1, 1.41, 2.13, 2.97), seed=12, bright=0.7)
place(dry, 4.25, c, 0.0, 0.07); place(send, 4.25, c, 0, 0.15)
for k in range(9):
    place(dry, 4.27 + k * 0.05 + 0.01 * np.sin(k * 3), click(0.015, 9000, 70 + k) * 0.05 * (1 - k / 10), (k % 3 - 1) * 0.3)
# 04:72 the question appears — breath
n = int(0.5 * SR); x = np.arange(n) / SR
br = bp(noise(n, 80), 600, 2400, 1) * np.sin(np.pi * x / 0.5) ** 2
place(dry, 4.68, br, 0, 0.03)
# liquid metal stretching 04:75–05:15
n = int(0.45 * SR); x = np.arange(n) / SR
liq = np.sin(2 * np.pi * (180 * x - 60 * x * x)) * np.sin(np.pi * x / 0.45) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * x))
place(dry, 4.72, lp(liq, 900), 0, 0.10)

# ---------------------------------------------------------------- 05:20 MAIN IMPACT
place(dry, 5.20, sub_boom(2.0, 120, 38, 0.95, 2.4), gain=1.0)
m1 = metal(2.6, 146.83, 1.4, seed=21); m2 = metal(2.2, 587.33, 0.8, seed=22, bright=0.8)
place(dry, 5.20, m1, -0.2, 0.30); place(dry, 5.20, m2, 0.25, 0.15)
place(send, 5.20, m1, 0, 0.45); place(send, 5.20, m2, 0, 0.27)
place(dry, 5.20, click(0.05, 2500, 23), 0, 0.45)
place(dry, 5.20, lp(noise(int(0.4 * SR), 24) * np.exp(-np.arange(int(0.4 * SR)) / SR / 0.06), 1800), 0, 0.12)
# low chord blooming under the question (Dm9 voicing)
ch = pad_voice([D2, A2, F3, E4], 3.2, lambda x: 180 + 1100 * np.exp(-x / 0.6) + 200, 31)
ch *= np.minimum(1, np.arange(len(ch)) / SR / 0.04) * np.exp(-np.arange(len(ch)) / SR / 1.6)
place(dry, 5.20, np.stack([ch, np.roll(ch, 360)], 1) * 0.55); place(send, 5.20, ch * 0.35)

# 06:80 reverberant dissolve — airy shimmer following the light sweep
n = int(0.7 * SR); x = np.arange(n) / SR
sh = bp(noise(n, 90), 6000, 14000, 2) * np.sin(np.pi * x / 0.7) ** 2
pan = np.linspace(-0.9, 0.9, n)
place(dry, 6.80, np.stack([sh * np.cos((pan + 1) * np.pi / 4), sh * np.sin((pan + 1) * np.pi / 4)], 1) * 0.05)
place(send, 6.80, sh * 0.06)

# 07:20–07:95 tiny metallic pieces reorganising
r = np.random.default_rng(99)
for k in range(46):
    tt = 7.2 + 0.75 * (k / 46) ** 0.8 + r.uniform(-0.01, 0.01)
    f0 = r.uniform(2500, 7000)
    pc = metal(0.12, f0, 0.025, ratios=(1, 2.76, 5.4), seed=200 + k)
    place(dry, tt, pc, r.uniform(-0.8, 0.8), 0.022 * r.uniform(0.5, 1.0))
    place(send, tt, pc, 0, 0.012)
place(dry, 7.95, metal(0.5, 1174.7, 0.16, seed=300), 0, 0.06)

# 08:30 SONIC SIGNATURE — D5 · A5 · F5 (rising fifth, falling third) over a soft sub
for k, (tt, f) in enumerate([(8.30, D5), (8.42, A5), (8.60, F5)]):
    b = fm_bell(1.6, f, idx=1.6, ratio=3.5, decay=0.55 if k < 2 else 0.9)
    place(dry, tt, b, [-0.25, 0.25, 0.0][k], 0.11)
    place(send, tt, b, 0, 0.16)
place(dry, 8.30, sub_boom(1.2, 70, D1 * 1.0, 0.45, 1.3), gain=0.40)

# 08:3–09:2 calm bed; 09:2 energy reduces
bed2 = pad_voice([D2, A2, F3], 3.6, lambda x: 700 - 450 * np.clip((x - 0.9) / 1.2, 0, 1), 41)
bed2 *= np.minimum(1, np.arange(len(bed2)) / SR / 0.6) * np.exp(-np.arange(len(bed2)) / SR / 2.2)
place(dry, 7.80, np.stack([bed2, np.roll(bed2, 500)], 1) * 0.30)

# 09:75 ACESSO ANTECIPADO — soft air; 10:00 the signal returns (beam tone, mirrored)
n = int(0.6 * SR); x = np.arange(n) / SR
place(dry, 9.72, bp(noise(n, 120), 900, 3500, 1) * np.sin(np.pi * x / 0.6) ** 2, 0, 0.025)
n = int(0.55 * SR); x = np.arange(n) / SR
beam2 = np.sin(2 * np.pi * (2400 * x + 1200 * x * x)) * np.sin(np.pi * x / 0.55) ** 2 * 0.035
pan = np.linspace(-0.8, 0.8, n)
place(dry, 10.0, np.stack([beam2 * np.cos((pan + 1) * np.pi / 4), beam2 * np.sin((pan + 1) * np.pi / 4)], 1) * 1.4)
# 10:50 soft metallic click on the CTA
cl = metal(0.25, 3520, 0.04, ratios=(1, 2.1, 3.3), seed=140) * 0.5; cl[:1440] += click(0.03, 6000, 141)
place(dry, 10.50, cl, 0.05, 0.10); place(send, 10.50, cl, 0, 0.05)

# 10:85 final chord — low, sophisticated, short tail resolving exactly at 12.00
fin = pad_voice([D1 * 2, A2, D3, F3, C3 * 2, E4], 1.15, lambda x: 900 * np.exp(-x / 0.5) + 260, 51)
L = len(fin); xe = np.arange(L) / SR
fin *= np.minimum(1, xe / 0.03) * np.exp(-xe / 0.75)
place(dry, 10.85, np.stack([fin, np.roll(fin, 420)], 1) * 0.75)
place(send, 10.85, fin * 0.30)
place(dry, 10.85, sub_boom(1.15, 60, D1, 0.6, 1.4), gain=0.45)
pi = fm_bell(1.15, D4, idx=0.9, ratio=2.0, decay=0.6)
place(dry, 10.85, pi, -0.1, 0.07); place(send, 10.85, pi, 0, 0.1)

# ---------------------------------------------------------------- space: synthetic stereo hall (1.4 s), dark
ir_n = int(1.4 * SR); xi = np.arange(ir_n) / SR
irL = noise(ir_n, 500) * np.exp(-xi / 0.38); irR = noise(ir_n, 501) * np.exp(-xi / 0.38)
irL = lp(hp(irL, 250), 6500); irR = lp(hp(irR, 250), 6500)
pre = int(0.018 * SR)
irL = np.concatenate([np.zeros(pre), irL]); irR = np.concatenate([np.zeros(pre), irR])
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
wet = np.stack([signal.fftconvolve(send[:, 0], irL)[:N], signal.fftconvolve(send[:, 1], irR)[:N]], 1)
mix = dry + wet * 0.9

# keep the 03.80 -> 04.15 window silent (only the faintest room tail)
s0, s1 = int(3.80 * SR), int(4.15 * SR)
fade = np.ones(N); fade[s0:s1] = 0.0
fade[s0 - int(0.010 * SR):s0] = np.linspace(1, 0, int(0.010 * SR))
mix *= fade[:, None]

# master: DC/rumble filter, gentle bus glue, true-peak safety, smooth end
mix = hp(mix, 24, 2)
mix = np.tanh(mix * 1.15) / 1.15
end = int(0.25 * SR)
mix[-end:] *= (np.cos(np.linspace(0, np.pi / 2, end)) ** 2)[:, None]
mix /= np.abs(mix).max() / 0.89
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else 'score.wav', SR, (mix * 32767).astype(np.int16))
print('ok', mix.shape, np.abs(mix).max())
