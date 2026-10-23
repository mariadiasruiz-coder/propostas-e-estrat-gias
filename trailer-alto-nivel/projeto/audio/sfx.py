"""Biblioteca de sound design gerada proceduralmente (100% original, sem samples de terceiros).
Cada função devolve um array estéreo float. O ponto de sincronia ("hit") de cada som
é indicado no docstring, para que a timeline posicione o som exatamente no quadro visual."""
import numpy as np
from dsp import (SR, secs, pan, expdecay, noise, butter, sweep_filter, reverb, fade,
                 softclip, stereo, peq, RNG)


def _t(n):
    return np.arange(n) / SR


def whoosh(dur=0.9, f0=300, f1=3000, p0=0.8, p1=-0.8, peak=0.55, bw=1.3, color='pink',
           body=0.0, room='plate', wet=0.18, seed=None):
    """Whoosh com filtro em varredura e pan em movimento. Pico em peak*dur."""
    n = secs(dur)
    t = np.linspace(0, 1, n)
    x = noise(n, color)
    fc = lambda tt: f0 * (f1 / f0) ** np.clip(tt / dur, 0, 1) ** 0.9
    y = sweep_filter(x, fc, bw)
    e = np.where(t < peak, (t / peak) ** 2.2, ((1 - t) / (1 - peak)) ** 1.6)
    y = y * e
    if body:
        # corpo grave ("doppler") que segue o envelope
        ph = 2 * np.pi * np.cumsum(np.interp(t, [0, peak, 1], [70, 110, 60])) / SR
        y += body * np.sin(ph) * e ** 1.5
    pv = p0 + (p1 - p0) * (np.clip((t - peak * 0.4) / 0.6, 0, 1))
    out = pan(y / (np.abs(y).max() + 1e-9), pv)
    return reverb(out, room, wet) if wet else out


def rev_whoosh(dur=1.2, f0=6000, f1=400, **kw):
    """Whoosh reverso (sucção) — termina no pico: o 'hit' está no FIM do arquivo."""
    w = whoosh(dur, f0, f1, peak=0.5, wet=0.0, **kw)
    w = reverb(w, 'hall', 0.6)
    return w[::-1].copy()


def reverse_swell(snd, room='hall', wet=1.0, keep=None):
    """Inverte (som + reverb) — cauda reversa que culmina no ataque original (fim do arquivo)."""
    y = reverb(snd, room, wet, dry=0.3)
    y = y[::-1].copy()
    if keep:
        y = y[-secs(keep):]
    return fade(y, 0.05, 0.002)


def sub_boom(dur=2.4, f0=58, f1=27, tau=0.9, drive=1.6):
    """Boom grave/sub. Hit no início."""
    n = secs(dur)
    t = _t(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * expdecay(n, tau)
    y = softclip(y, drive)
    y *= np.minimum(1, t / 0.004)
    return stereo(y)


def impact(level=1.0, dur=3.5, low=1.0, mid=0.7, top=0.35, room='huge', wet=0.45, f0=62, seed=0):
    """Impacto cinematográfico em camadas (sub + corpo + transiente + cauda). Hit no início."""
    n = secs(dur)
    t = _t(n)
    sub = sub_boom(dur, f0, 34, 1.0)[:, 0] * low
    body = butter(noise(n, 'brown'), 'lowpass', 420, 4) * expdecay(n, 0.16)
    body = body / (np.abs(body).max() + 1e-9) * mid
    tr = butter(noise(n), 'bandpass', [1200, 9000], 2) * expdecay(n, 0.018)
    tr = tr / (np.abs(tr).max() + 1e-9) * top
    # "metal" grave inarmônico (sensação de trailer)
    met = sum(np.sin(2 * np.pi * f * t + RNG.uniform(0, 6)) * expdecay(n, d)
              for f, d in [(113, 0.9), (171, 0.7), (247, 0.55), (389, 0.4), (517, 0.3)]) * 0.12 * mid
    y = sub + body + tr + met
    y = stereo(y) * level
    out = reverb(y, room, wet)
    return out[:n + secs(2.5)]


def taiko(level=1.0, f0=95, dur=1.6, room='hall', wet=0.35, p=0.0):
    """Tambor grave de trailer sintetizado. Hit no início."""
    n = secs(dur)
    t = _t(n)
    f = 48 + (f0 - 48) * np.exp(-t / 0.05)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(n, 0.32)
    skin = butter(noise(n), 'bandpass', [150, 1800], 2) * expdecay(n, 0.035)
    y = softclip(tone * 1.1 + skin * 0.35, 1.3) * level
    return reverb(pan(y, p), room, wet)


def tick(level=0.5, f=2400, p=0.0, dur=0.05):
    """Clique digital suave (UI). Hit no início."""
    n = secs(dur)
    t = _t(n)
    y = np.sin(2 * np.pi * f * t) * expdecay(n, 0.006) + butter(noise(n), 'highpass', 3000, 2) * expdecay(n, 0.002) * 0.4
    return reverb(pan(y * level, p), 'room', 0.12)


def pulse_hit(level=0.6, f=72, p=0.0):
    """Pulso grave curto (sincronizado com animações numéricas/palavras). Hit no início."""
    n = secs(0.5)
    t = _t(n)
    fr = f * (1 + 0.6 * np.exp(-t / 0.02))
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * expdecay(n, 0.09)
    y += tick(0.25, 1800, p)[:n, 0] * 0.6
    return reverb(pan(softclip(y, 1.2) * level, p), 'room', 0.2)


def metallic(level=0.5, base=620, dur=2.2, p=0.0, scrape=0.4, room='plate', wet=0.4):
    """Acento metálico premium (inarmônico) + leve raspagem. Hit no início."""
    n = secs(dur)
    t = _t(n)
    ratios = [1.0, 2.756, 5.404, 8.933, 13.34]
    y = sum(np.sin(2 * np.pi * base * r * t + RNG.uniform(0, 6)) * expdecay(n, 0.9 / (1 + i * 0.6)) / (1 + i)
            for i, r in enumerate(ratios))
    y *= np.minimum(1, t / 0.002)
    if scrape:
        s = sweep_filter(noise(n), lambda tt: 9000 - 5000 * np.clip(tt / 0.25, 0, 1), 0.8)
        y += s * expdecay(n, 0.08) * scrape * 3
    y = butter(y, 'highpass', 300, 2)
    return reverb(pan(y / (np.abs(y).max() + 1e-9) * level, p), room, wet)


def bell(notes=(88, 95), gap=0.11, level=0.35, p=0.0, dur=2.2, index=1.6, ratio=3.5):
    """Notificação elegante (sino FM, duas notas). Hit no início."""
    n = secs(dur + gap * len(notes))
    out = np.zeros(n)
    for k, m in enumerate(notes):
        f = 440 * 2 ** ((m - 69) / 12)
        nn = secs(dur)
        t = _t(nn)
        mod = index * expdecay(nn, 0.25) * np.sin(2 * np.pi * f * ratio * t)
        y = np.sin(2 * np.pi * f * t + mod) * expdecay(nn, 0.55) * np.minimum(1, t / 0.003)
        i = secs(gap * k)
        out[i:i + nn] += y * (0.8 if k else 1.0)
    return reverb(pan(out * level, p), 'plate', 0.35)


def shimmer(chord=(74, 78, 81, 86, 90, 93), dur=3.0, level=0.25, attack=0.4, seed=3):
    """Brilho tonal (cluster agudo com tremolo). Pico em ~attack."""
    rng = np.random.default_rng(seed)
    n = secs(dur)
    t = _t(n)
    y = np.zeros((n, 2))
    for m in chord:
        f = 440 * 2 ** ((m - 69) / 12) * (1 + rng.uniform(-0.002, 0.002))
        e = np.minimum(1, t / attack) ** 2 * np.exp(-np.maximum(0, t - attack) / (dur * 0.35))
        trem = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(4, 7) * t + rng.uniform(0, 6))
        s = np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * e * trem
        y += pan(s, rng.uniform(-0.8, 0.8))
    return reverb(y / len(chord) * level * 3, 'huge', 0.7)


def riser(dur=3.0, level=0.6, f0=300, f1=7000, tone=True, end_cut=True):
    """Riser de trailer: o 'hit' (fim) está no último sample."""
    n = secs(dur)
    tt = np.linspace(0, 1, n)
    x = sweep_filter(noise(n, 'pink'), lambda t: f0 * (f1 / f0) ** np.clip(t / dur, 0, 1), 1.2)
    x /= np.abs(x).max() + 1e-9
    y = x * tt ** 2.5
    if tone:
        for k, base in enumerate([110, 165, 220]):
            f = base * 2 ** (tt * 2.0)
            y += np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.05 * tt ** 3
            y += np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * 0.12 * tt ** 3
    out = pan(y * level, 0)
    out[:, 0] *= 1 + 0.15 * np.sin(2 * np.pi * 0.7 * tt * dur)
    out[:, 1] *= 1 - 0.15 * np.sin(2 * np.pi * 0.7 * tt * dur)
    out = reverb(out, 'plate', 0.25)[:n]
    return fade(out, 0.2, 0.004 if end_cut else 0.2)


def sub_drop(dur=1.8, f0=110, f1=34, level=0.9):
    """Sub drop — hit no início."""
    n = secs(dur)
    t = _t(n)
    f = f1 + (f0 - f1) * (1 - np.clip(t / (dur * 0.8), 0, 1)) ** 2
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - t / dur) ** 1.3
    y *= np.minimum(1, t / 0.01)
    return stereo(softclip(y, 1.3) * level)


def air(dur=2.0, level=0.25, p0=-0.6, p1=0.6, f=5000):
    """Varredura de ar (transições atmosféricas). Pico no meio."""
    n = secs(dur)
    tt = np.linspace(0, 1, n)
    x = butter(noise(n, 'pink'), 'highpass', f, 2)
    x = sweep_filter(x, lambda t: f * 0.6 * 2 ** (1.5 * np.sin(np.pi * np.clip(t / dur, 0, 1))), 1.6)
    e = np.sin(np.pi * tt) ** 2
    return reverb(pan(x / (np.abs(x).max() + 1e-9) * e * level, p0 + (p1 - p0) * tt), 'hall', 0.3)[:n + secs(1)]


def count_ticks(t0, t1, n=12, f0=1400, f1=3200, level=0.35):
    """Lista de (tempo, som) — cliques acelerando para contagens numéricas."""
    out = []
    for k in range(n):
        x = (k / (n - 1))
        tt = t0 + (t1 - t0) * (1 - (1 - x) ** 1.8)
        out.append((tt, tick(level * (0.6 + 0.4 * x), f0 + (f1 - f0) * x, RNG.uniform(-0.3, 0.3))))
    return out


def light_streak(dur=1.2, level=0.3):
    """Som para traço de luz horizontal: brilho + ar fino. Pico em ~40%."""
    a = air(dur, level, -0.9, 0.9, 7000)
    s = shimmer((86, 93, 98), dur, level * 0.5, attack=dur * 0.4, seed=9)
    n = min(len(a), len(s))
    return a[:n] + s[:n]


def heartbeat(level=0.5):
    """Batida dupla grave e abafada (tensão). Hit no início."""
    a = pulse_hit(level, 52)
    b = pulse_hit(level * 0.7, 48)
    out = np.zeros((len(a) + secs(0.28), 2))
    out[:len(a)] += a
    out[secs(0.28):secs(0.28) + len(b)] += b
    return butter(out, 'lowpass', 900, 2)
