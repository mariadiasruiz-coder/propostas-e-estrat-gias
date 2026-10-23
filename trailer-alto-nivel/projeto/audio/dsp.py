"""Blocos de DSP para trilha e sound design (numpy/scipy, 48 kHz, estéreo float32)."""
import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(7)


def secs(n):
    return int(round(n * SR))


def stereo(x):
    return np.stack([x, x], 1) if x.ndim == 1 else x


def pan(x, p):
    """p em [-1, 1] (constante de potência). p pode ser array (pan dinâmico)."""
    x = x if x.ndim == 1 else x.mean(1)
    th = (np.asarray(p) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)], 1)


def place(buf, snd, t, gain=1.0):
    """Mixa snd (estéreo) no buffer a partir de t segundos (aceita t negativo)."""
    snd = stereo(snd) * gain
    i = secs(t)
    j0 = max(0, -i)
    i0 = max(0, i)
    n = min(len(buf) - i0, len(snd) - j0)
    if n > 0:
        buf[i0:i0 + n] += snd[j0:j0 + n]


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, sus_len=None):
    a, d, r = secs(a), secs(d), secs(r)
    sus = n - a - d - r if sus_len is None else secs(sus_len)
    sus = max(sus, 0)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False),
                        np.linspace(1, s, d, endpoint=False),
                        np.full(sus, s), np.linspace(s, 0, r)])
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def expdecay(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def fade(x, fi=0.005, fo=0.005):
    x = x.copy()
    a, b = secs(fi), secs(fo)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def butter(x, kind, f, order=2):
    sos = signal.butter(order, f, btype=kind, fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=0)


def peq(x, f0, gain_db, q=1.0):
    """Filtro peaking (RBJ)."""
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / (2 * q)
    b = [1 + al * A, -2 * np.cos(w0), 1 - al * A]
    a = [1 + al / A, -2 * np.cos(w0), 1 - al / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)


def shelf(x, f0, gain_db, high=True):
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / 2 * np.sqrt(2)
    c = np.cos(w0)
    if high:
        b = [A * ((A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al), -2 * A * ((A - 1) + (A + 1) * c),
             A * ((A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al)]
        a = [(A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al, 2 * ((A - 1) - (A + 1) * c),
             (A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al]
    else:
        b = [A * ((A + 1) - (A - 1) * c + 2 * np.sqrt(A) * al), 2 * A * ((A - 1) - (A + 1) * c),
             A * ((A + 1) - (A - 1) * c - 2 * np.sqrt(A) * al)]
        a = [(A + 1) + (A - 1) * c + 2 * np.sqrt(A) * al, -2 * ((A - 1) + (A + 1) * c),
             (A + 1) + (A - 1) * c - 2 * np.sqrt(A) * al]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)


def noise(n, color='white'):
    w = RNG.standard_normal(n)
    if color == 'white':
        return w
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    W = np.fft.rfft(w)
    if color == 'pink':
        W /= np.sqrt(f)
    elif color == 'brown':
        W /= f
    x = np.fft.irfft(W, n)
    return x / (np.abs(x).max() + 1e-9)


def sweep_filter(x, fc, bw_oct=1.0, nfft=2048, hop=256):
    """Passa-faixa variável no tempo via STFT. fc: função t->Hz ou array por quadro."""
    f, t, Z = signal.stft(x, SR, nperseg=nfft, noverlap=nfft - hop)
    fcs = fc(t) if callable(fc) else np.interp(t, np.linspace(0, t[-1], len(fc)), fc)
    lf = np.log2(np.maximum(f, 1))[:, None]
    bw = bw_oct(t) if callable(bw_oct) else bw_oct
    g = np.exp(-0.5 * ((lf - np.log2(fcs)[None, :]) / (np.asarray(bw) / 2)) ** 2)
    _, y = signal.istft(Z * g, SR, nperseg=nfft, noverlap=nfft - hop)
    return y[:len(x)] if len(y) >= len(x) else np.pad(y, (0, len(x) - len(y)))


def softclip(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive)


# ---------------------------------------------------------------------------
# Reverb por convolução com respostas ao impulso sintéticas (salas estéreo)
def make_ir(length=3.2, rt60_low=3.4, rt60_high=1.4, predelay=0.022, early=True, seed=1, width=1.0):
    rng = np.random.default_rng(seed)
    n = secs(length)
    bands = [(20, 250, rt60_low), (250, 1000, rt60_low * 0.9), (1000, 4000, (rt60_low + rt60_high) / 2),
             (4000, 12000, rt60_high), (12000, 20000, rt60_high * 0.6)]
    out = np.zeros((n, 2))
    t = np.arange(n) / SR
    for ch in range(2):
        acc = np.zeros(n)
        for lo, hi, rt in bands:
            nz = rng.standard_normal(n)
            nz = butter(nz, 'bandpass', [lo, min(hi, SR / 2 - 100)], 2)
            acc += nz * np.exp(-6.9 * t / rt)
        out[:, ch] = acc
    mid = out.mean(1, keepdims=True)
    out = mid + (out - mid) * width
    # ataque suave da cauda
    out *= np.minimum(1, t / 0.06)[:, None] ** 1.5
    if early:
        for k in range(14):
            d = rng.uniform(0.004, 0.075)
            g = rng.uniform(0.25, 0.7) * (1 - d / 0.08)
            i = secs(d)
            out[i, 0] += g * rng.choice([-1, 1])
            out[i + rng.integers(0, 40), 1] += g * rng.choice([-1, 1])
    pd = secs(predelay)
    out = np.concatenate([np.zeros((pd, 2)), out])
    return out / np.sqrt((out ** 2).sum() / 2)


_IR_CACHE = {}


def reverb(x, kind='hall', wet=0.3, dry=1.0):
    if kind not in _IR_CACHE:
        if kind == 'hall':
            _IR_CACHE[kind] = make_ir(4.0, 3.6, 1.6, 0.03, seed=11)
        elif kind == 'huge':
            _IR_CACHE[kind] = make_ir(7.0, 6.5, 2.8, 0.045, seed=12, width=1.2)
        elif kind == 'room':
            _IR_CACHE[kind] = make_ir(1.4, 0.9, 0.45, 0.008, seed=13)
        elif kind == 'plate':
            _IR_CACHE[kind] = make_ir(2.6, 2.2, 1.6, 0.012, early=False, seed=14)
    ir = _IR_CACHE[kind]
    x = stereo(x)
    y = np.zeros((len(x) + len(ir) - 1, 2))
    for ch in range(2):
        y[:, ch] = signal.fftconvolve(x[:, ch], ir[:, ch])
    y *= wet
    y[:len(x)] += x * dry
    return y


def lufs_short(x):
    import pyloudnorm as pyln
    return pyln.Meter(SR).integrated_loudness(stereo(x))
