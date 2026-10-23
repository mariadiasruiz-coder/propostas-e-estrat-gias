"""Mixagem e masterização: reverb por stem, automação de seções, ducking pela voz,
limiter de pico verdadeiro e normalização a -14 LUFS / -1 dBTP."""
import sys, os, subprocess, json
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal
from scipy.ndimage import minimum_filter1d, maximum_filter1d
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import DUR, IMPACT, EV, SCENES
from dsp import SR, secs, reverb, butter, peq, shelf

NS = secs(DUR)
db = lambda x: 10 ** (x / 20)


def load(name):
    a, sr = sf.read(f'stems/{name}.wav', dtype='float64')
    assert sr == SR
    a = a[:NS] if len(a) >= NS else np.pad(a, ((0, NS - len(a)), (0, 0)))
    return a


def curve(points, kind='db'):
    t = np.arange(NS) / SR
    ts, vs = zip(*points)
    v = np.interp(t, ts, vs)
    return db(v) if kind == 'db' else v


def follower(x, att=0.04, rel=0.35, win=0.03):
    """Envelope (dB) da voz com ataque/relaxamento, com look-ahead de 60 ms."""
    m = x.mean(1) if x.ndim == 2 else x
    w = secs(win)
    rms = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, mode='same') + 1e-12)
    e = 20 * np.log10(rms)
    e = np.roll(e, -secs(0.06))
    # suavização assimétrica em blocos de 1 ms
    hop = 48
    eb = e[::hop]
    out = np.empty_like(eb)
    a_c = np.exp(-hop / (att * SR))
    r_c = np.exp(-hop / (rel * SR))
    y = -90.0
    for i, v in enumerate(eb):
        c = a_c if v > y else r_c
        y = c * y + (1 - c) * v
        out[i] = y
    return np.repeat(out, hop)[:len(m)]


def limiter(x, ceiling_db=-1.3, look=0.004, rel=0.12):
    up = signal.resample_poly(x, 4, 1, axis=0)
    pk = np.abs(up).max(1).reshape(-1, 4).max(1)[:len(x)]
    pk = np.pad(pk, (0, len(x) - len(pk)), constant_values=pk[-1])
    c = db(ceiling_db)
    g = np.minimum(1.0, c / np.maximum(pk, 1e-9))
    L = secs(look)
    g = minimum_filter1d(g, 2 * L + 1)
    hop = 16
    gb = g[::hop]
    out = np.empty_like(gb)
    rc = np.exp(-hop / (rel * SR))
    y = 1.0
    for i, v in enumerate(gb):
        y = v if v < y else rc * y + (1 - rc) * v
        out[i] = y
    gs = np.repeat(out, hop)[:len(x)]
    k = signal.windows.hann(2 * L + 1)
    gs = np.convolve(np.pad(gs, L, mode='edge'), k / k.sum(), mode='valid')
    gs = np.minimum(gs, g)
    return x * gs[:, None]


def build():
    V = load('voice')
    # voz: limiter de pico suave (crista natural preservada)
    V = limiter(V, -5.5, 0.002, 0.06)

    # ---------------- MÚSICA ------------------------------------------------
    stems = {  # nome: (ganho dB, sala, wet)
        'orch_piano': (2.0, 'hall', 0.32), 'orch_strings': (1.0, 'hall', 0.30),
        'orch_ostinato': (-3.5, 'hall', 0.22), 'orch_tremolo': (-4.0, 'hall', 0.30),
        'orch_cellos': (-1.0, 'hall', 0.25), 'orch_basses': (-1.5, 'hall', 0.2),
        'orch_brass': (-1.5, 'hall', 0.30), 'orch_horns': (-3.0, 'hall', 0.32),
        'orch_choir': (-2.0, 'huge', 0.40), 'orch_timpani': (0.0, 'hall', 0.28),
        'orch_taiko': (-1.0, 'hall', 0.30), 'orch_kit': (-2.5, 'hall', 0.35),
        'orch_bells': (-4.0, 'huge', 0.45), 'orch_celesta': (-5.0, 'huge', 0.45),
        'orch_revcym': (-6.0, 'hall', 0.2),
        'syn_pulse': (-6.0, 'plate', 0.14), 'syn_sub': (-12.0, None, 0), 'syn_pad': (-13.0, 'hall', 0.35),
    }
    M = np.zeros((NS, 2))
    for k, (g, room, wet) in stems.items():
        x = load(k)
        if room:
            x = reverb(x, room, wet)[:NS]
        M += x * db(g)
    # limpeza infrassônica + recorte de médias onde a voz vive
    M = butter(M, 'highpass', 30, 4)
    M = shelf(M, 48, -3.0, high=False)
    M = peq(M, 2600, -2.5, 0.8)
    M = peq(M, 320, -1.0, 1.0)

    # automação por seção: metas de loudness (LUFS) da trilha ANTES do ducking.
    # O arco intencional (mistério -> descoberta -> prova -> ascensão -> clímax) está nas metas;
    # a dinâmica interna (stops, crescendos, impactos) vem da própria partitura.
    meter = pyln.Meter(SR)
    SECT = [  # (t0, t1, meta LUFS)
        (0.0, 4.95, -19.5), (5.29, 11.07, -19.5), (11.07, 15.97, -17.5), (15.97, 26.0, -17.5),
        (26.0, 28.27, -14.0), (28.27, 40.88, -20.5), (40.88, 47.70, -20), (47.70, 52.60, -19),
        (52.60, 60.09, -22), (60.09, 65.96, -18.5), (65.96, 76.4, -17.0), (76.4, 84.05, -14.5),
        (IMPACT, 90.0, -13.5)]
    pts = [(0, -60)]
    for a, b, tgt in SECT:
        L = meter.integrated_loudness(M[secs(a):secs(b)])
        g = float(np.clip(tgt - L, -30, 30))
        pts += [(a + 0.001, g), (b - 0.001, g)]
    pts = sorted(pts)
    # pausas dramáticas: suspensão após a pergunta e silêncio antes de "Bem-vinda"
    fixed = [(4.95, None), (5.29, None)]
    gpts = []
    for t, g in pts:
        gpts.append((t, g))
    gpts += [(4.96, -18), (5.28, -18), (84.06, -60), (IMPACT - 0.002, -60)]
    gpts.sort()
    # rampas suaves entre seções (0,25 s)
    tt = np.arange(NS) / SR
    gc = np.interp(tt, [p[0] for p in gpts], [p[1] for p in gpts])
    k = secs(0.25)
    gc_s = np.convolve(np.pad(gc, k, mode='edge'), np.ones(2 * k + 1) / (2 * k + 1), mode='valid')
    # não suavizar o corte seco para o silêncio (84,05) nem o ataque do impacto final
    hard = (tt >= 84.0) & (tt < IMPACT + 0.05)
    gc_s[hard] = gc[hard]
    M *= db(gc_s)[:, None]

    # ducking automático pela voz (profundidade varia por seção)
    env = follower(V)
    act = np.clip((env + 42) / 18, 0, 1)                # 0 = silêncio, 1 = fala plena
    depth = curve([(0, 6), (28.2, 6), (28.4, 7), (60.0, 7), (60.1, 6), (66, 5), (84, 5), (90, 5)], 'lin')
    duck = db(-depth * act)
    M *= duck[:, None]

    # ---------------- SFX ---------------------------------------------------
    F = load('sfx')
    F = butter(F, 'highpass', 32, 4)
    F = peq(F, 110, 2.0, 0.9)            # mais corpo audível em alto-falantes pequenos
    F *= db(-3.0 * act)[:, None]
    F *= curve([(0, 0), (84.08, 0), (84.12, -6), (IMPACT - 0.6, -6), (IMPACT - 0.4, 0), (90, 0)])[:, None]

    mix = butter(V + M + F * db(-5.0), 'highpass', 28, 4)
    return mix, V, M, F * db(-5.0)


def master(mix, target=-14.0):
    meter = pyln.Meter(SR)
    # fade final dentro dos 90 s
    t = np.arange(NS) / SR
    mix = mix * np.clip((90.0 - t) / 0.55, 0, 1)[:, None]
    g = 0.0
    for it in range(6):
        y = limiter(mix * db(g), -1.3)
        L = meter.integrated_loudness(y)
        if abs(L - target) < 0.05:
            break
        g += target - L
    gr = 20 * np.log10(np.maximum(np.abs(y).max(1), 1e-9) / np.maximum(np.abs(mix * db(g)).max(1), 1e-9))
    act = np.abs(mix * db(g)).max(1) > 0.05
    print('limiter: GR max %.1f dB, p99 %.2f dB, amostras com GR>1dB: %.2f%%' % (
        -gr[act].min(), -np.percentile(gr[act], 1), 100 * (gr[act] < -1).mean()))
    return y, L, g


if __name__ == '__main__':
    mix, V, M, F = build()
    y, L, g = master(mix)
    os.makedirs('out', exist_ok=True)
    sf.write('out/master_48k_24bit.wav', y.astype(np.float32), SR, subtype='PCM_24')
    for name, s in [('voz', V), ('musica', M), ('sfx', F)]:
        sf.write(f'out/stem_{name}.wav', (s * db(g)).astype(np.float32), SR, subtype='PCM_24')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', 'out/master_48k_24bit.wav', '-af',
                        'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    summ = r[r.rfind('Summary'):]
    print('gain', round(g, 2), 'LUFS(py)', round(L, 2))
    print(summ)
