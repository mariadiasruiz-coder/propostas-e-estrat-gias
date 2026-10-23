"""Trilha original 'ALTO NÍVEL' — Hybrid Cinematic Trailer Score em Ré menor -> Ré maior.
Composta nota a nota sobre a timeline do trailer (timeline.EV), de modo que cada revelação
visual caia num acento musical. Gera stems separados para a mixagem."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import EV, DUR, IMPACT
from dsp import SR, secs, place, pan, butter, expdecay, softclip, reverb, noise, stereo, fade, RNG
from instruments import Part, N
import sfx

TOTAL = DUR + 2.0
NS = secs(TOTAL)

# ---------------------------------------------------------------------------
# Harmonia (tempo T, acorde). Voicings por registro.
CH = {
    'Dm': dict(root='D', bass=['D2'], low=['D3', 'A3'], mid=['D4', 'F4', 'A4'], hi=['D5', 'F5', 'A5']),
    'Bb': dict(root='Bb', bass=['Bb1'], low=['Bb2', 'F3'], mid=['D4', 'F4', 'Bb4'], hi=['D5', 'F5', 'Bb5']),
    'F':  dict(root='F', bass=['F2'], low=['F2', 'C3'], mid=['C4', 'F4', 'A4'], hi=['C5', 'F5', 'A5']),
    'C':  dict(root='C', bass=['C2'], low=['C3', 'G3'], mid=['C4', 'E4', 'G4'], hi=['C5', 'E5', 'G5']),
    'Gm': dict(root='G', bass=['G1'], low=['G2', 'D3'], mid=['D4', 'G4', 'Bb4'], hi=['D5', 'G5', 'Bb5']),
    'A':  dict(root='A', bass=['A1'], low=['A2', 'E3'], mid=['C#4', 'E4', 'A4'], hi=['C#5', 'E5', 'A5']),
    'Asus': dict(root='A', bass=['A1'], low=['A2', 'E3'], mid=['D4', 'E4', 'A4'], hi=['D5', 'E5', 'A5']),
    'D':  dict(root='D', bass=['D2'], low=['D3', 'A3'], mid=['D4', 'F#4', 'A4'], hi=['D5', 'F#5', 'A5']),
}
ROOT_HZ = lambda name, octave: 440 * 2 ** ((N(CH[name]['root'] + str(octave)) - 69) / 12)

PROG = [  # (t0, t1, acorde)
    (0.00, 5.10, 'Dm'),
    (5.29, 8.00, 'Dm'), (8.00, 9.69, 'Bb'), (9.69, 11.07, 'Gm'),
    (11.07, 12.59, 'Dm'), (12.59, 13.59, 'Bb'), (13.59, 14.59, 'F'), (14.59, 15.97, 'C'),
    (15.97, 17.97, 'Dm'), (17.97, 19.14, 'Bb'),
    (19.14, 21.14, 'Dm'), (21.14, 23.14, 'Bb'), (23.14, 25.14, 'F'), (25.14, 26.20, 'C'),
    (26.20, 28.27, 'Dm'),
    (28.27, 31.00, 'F'), (31.00, 34.00, 'C'), (34.00, 37.00, 'Dm'), (37.00, 40.88, 'Bb'),
    (40.88, 43.67, 'F'), (43.67, 45.50, 'C'), (45.50, 47.70, 'Dm'),
    (47.70, 49.60, 'Dm'), (49.60, 51.40, 'Bb'), (51.40, 52.60, 'F'),
    (52.60, 55.10, 'F'), (55.10, 57.60, 'C'), (57.60, 60.09, 'Dm'),
    (60.09, 62.00, 'Bb'), (62.00, 64.00, 'C'), (64.00, 65.96, 'Dm'),
    (65.96, 68.00, 'Dm'), (68.00, 70.00, 'Bb'), (70.00, 72.00, 'F'), (72.00, 74.00, 'C'),
    (74.00, 76.00, 'Dm'), (76.00, 78.00, 'Bb'), (78.00, 79.00, 'Gm'),
    (79.00, 79.50, 'Dm'), (79.50, 80.00, 'Bb'), (80.00, 80.50, 'F'), (80.50, 81.00, 'C'),
    (81.00, 82.00, 'Bb'), (82.00, 83.00, 'C'), (83.00, 83.50, 'Asus'), (83.50, 84.00, 'A'),
    (IMPACT, DUR, 'D'),
]


def chord_at(t):
    for a, b, c in PROG:
        if a <= t < b:
            return c
    return None


# ===========================================================================
def orchestra():
    st = {}
    # ---------------- PIANO (Splendid Grand) --------------------------------
    pno = Part('piano', 0)
    pno.cc(0, 64, 127)
    for t, n, v in [(0.62, 'A4', 74), (0.62, 'D2', 52), (1.55, 'F4', 58), (2.42, 'D4', 56),
                    (EV['decisao'], 'E4', 70), (EV['decisao'], 'A2', 40)]:
        pno.note(t, 3.0, n, v)
    pno.cc(5.05, 64, 0); pno.cc(5.35, 64, 127)
    # cena 02: notas esparsas, o "tema da decisão" volta transformado
    for t, n, v in [(5.62, ['D3', 'A3'], 46), (6.70, 'F4', 50), (7.62, 'E4', 46), (EV['seguidores'], 'D4', 52),
                    (9.69, ['G2', 'D3'], 44), (10.30, 'Bb4', 48), (EV['caminho'], 'A4', 56),
                    (EV['estrategia'], ['D5', 'D4'], 62)]:
        pno.note(t, 2.5, n, v)
    for a, b in [(8.0, 8.02), (9.69, 9.71), (11.07, 11.09), (12.59, 12.61)]:
        pno.cc(a, 64, 0); pno.cc(b + 0.03, 64, 127)
    # cenas 04-08: arpejos íntimos sob os depoimentos (80 BPM)
    step = 0.375
    for a, b, c in PROG:
        if not (28.27 <= a < 60.09):
            continue
        pno.cc(a - 0.02, 64, 0); pno.cc(a + 0.03, 64, 127)
        ch = CH[c]
        pat = [ch['low'][0], ch['low'][1], ch['mid'][0], ch['mid'][1], ch['mid'][2], ch['mid'][1]]
        k = 0
        for t in np.arange(a, b - 0.05, step):
            vel = 34 + (8 if k % 6 == 0 else 0) + RNG.integers(-3, 4)
            if 47.7 <= t < 52.6:
                vel += 6           # Bianca: mais presente
            if 52.6 <= t < 60.09 and k % 2:
                k += 1             # Fernanda: mais espaço
                continue
            pno.note(t + RNG.uniform(-0.008, 0.008), 1.2, pat[k % len(pat)], vel)
            k += 1
        pno.note(a, 2.5, ch['bass'][0].replace('1', '2'), 42)
    # melodia da Bianca (emoção) e chegada no "rumo"
    for t, n, v, d in [(47.85, 'A5', 50, 1.6), (49.05, 'G5', 46, 0.6), (49.6, 'F5', 52, 1.8),
                       (50.85, 'E5', 46, 0.6), (51.4, 'F5', 54, 0.6), (EV['rumo'] - 0.05, 'A5', 58, 2.0)]:
        pno.note(t, d, n, v)
    # Rútilla: oitavas em crescendo
    for i, t in enumerate(np.arange(60.09, 65.9, 0.5)):
        c = CH[chord_at(t)]
        pno.note(t, 0.45, c['mid'][0], 40 + i * 2)
    # cena 09: oitavas graves de impacto nas trocas de acorde
    for a, b, c in PROG:
        if 65.96 <= a < 84.0:
            r = CH[c]['root']
            pno.note(a, min(1.8, b - a), [N(r + '1') if N(r + '1') >= 21 else N(r + '2'), N(r + '2')], 92)
    # final: acorde grave + brilho na assinatura
    pno.cc(84.2, 64, 0); pno.cc(84.3, 64, 127)
    pno.note(IMPACT, 3.6, ['D1', 'D2', 'A2', 'D3', 'F#3', 'A3'], 104)
    for i, n in enumerate(['D6', 'F#6', 'A6', 'D7']):
        pno.note(EV['signature'] + i * 0.09, 2.5, n, 54 - i * 4)
    st['piano'] = pno.render(TOTAL, 0.7)

    # ---------------- CORDAS (VSCO-2 CE, expressivas via CC2) --------------
    sl = Part('strings_slow', 49, 17)
    dyn = [(0.0, 18), (3.8, 78), (4.85, 70), (5.05, 0), (5.25, 0), (5.45, 40), (8.0, 52), (11.0, 60),
           (12.6, 78), (15.6, 104), (15.97, 70), (18.9, 86), (19.2, 74), (25.9, 108), (26.05, 60),
           (26.2, 120), (27.4, 80), (28.2, 48), (40.0, 48), (47.7, 58), (52.6, 44), (60.0, 46), (62.0, 64),
           (65.9, 96), (66.1, 70), (71.8, 92), (76.4, 104), (78.9, 112), (83.95, 127), (84.05, 0),
           (IMPACT - 0.01, 0), (IMPACT, 127), (88.0, 110), (89.9, 30)]
    sl.ramp(dyn, nums=(2,))
    for a, b, c in PROG:
        voic = CH[c]['low'] + CH[c]['mid']
        if a >= 65.96 or a >= IMPACT:
            voic = voic + CH[c]['hi'][:2]
        if c == 'D':
            voic = ['D2', 'A2', 'D3', 'F#3', 'A3', 'D4', 'F#4', 'A4', 'D5', 'F#5', 'A5', 'E5']
        sl.note(a, b - a + 0.08, voic, 96)
    st['strings'] = sl.render(TOTAL, 0.55)

    # ostinato (spiccato) — autoridade e ascensão
    fs = Part('strings_fast', 48, 17)
    fs.ramp([(15.9, 0), (16.0, 52), (18.5, 60), (19.14, 70), (25.9, 96), (26.0, 0), (65.9, 0), (66.0, 62),
             (72.0, 80), (78.0, 98), (84.0, 120), (84.05, 0)], nums=(2,))
    def ostinato(t0, t1, sixteenth=0.125, accent=0.5):
        k = 0
        for t in np.arange(t0, t1 - 0.01, sixteenth):
            c = CH[chord_at(t + 0.001)]
            r3, r4 = N(c['root'] + '3'), N(c['root'] + '4')
            seq = [r3, r3, r3 + 7, r3, r4, r3, r3 + 7, r3]
            if r3 + 7 > 71:
                seq = [r3 - 12 if x > 71 else x for x in seq]
            on_beat = abs(((t - t0) / accent) - round((t - t0) / accent)) < 1e-3
            fs.note(t, sixteenth * 0.8, seq[k % 8], 112 if on_beat else 84)
            k += 1
    ostinato(15.97, 18.55)
    ostinato(19.14, 25.95)
    ostinato(66.0, 84.0)
    st['ostinato'] = fs.render(TOTAL, 0.5)

    # tremolo agudo — tensão final
    tr = Part('tremolo', 44, 17)
    tr.ramp([(80.9, 0), (81.0, 40), (84.0, 127), (84.03, 0)], nums=(2,))
    for a, b, c in PROG:
        if 81.0 <= a < 84.0:
            tr.note(a, b - a + 0.03, CH[c]['hi'], 100)
    st['tremolo'] = tr.render(TOTAL, 0.4)

    # ---------------- GRAVES: violoncelos + contrabaixos -------------------
    lo = Part('cellos', 42)
    lo.ramp([(0, 30), (4.0, 96), (5.0, 0), (5.3, 50), (15.9, 100), (26.2, 120), (28.0, 60), (60, 60),
             (65.9, 100), (84.0, 127), (84.03, 0), (IMPACT, 127), (89.9, 40)])
    cb = Part('basses', 43)
    cb.ramp([(0, 50), (4.0, 100), (5.0, 0), (5.3, 60), (26.2, 127), (28, 70), (65.9, 110), (84.0, 127),
             (84.03, 0), (IMPACT, 127), (89.9, 40)])
    for a, b, c in PROG:
        r = CH[c]['root']
        lo.note(a, b - a + 0.05, [r + '2', r + '3'] if a >= 65.96 else [r + '2'], 92)
        cb.note(a, b - a + 0.05, CH[c]['bass'][0] if N(CH[c]['bass'][0]) >= 28 else r + '2', 96)
    # Bianca: linha de cello cantabile
    for t, n, d in [(47.9, 'A3', 1.6), (49.6, 'Bb3', 1.7), (51.4, 'A3', 1.2)]:
        lo.note(t, d, n, 70)
    st['cellos'] = lo.render(TOTAL, 0.55)
    st['basses'] = cb.render(TOTAL, 0.55)

    # ---------------- METAIS ------------------------------------------------
    br = Part('brass', 61)
    br.ramp([(26.15, 127), (27.6, 40), (28.0, 0), (76.3, 70), (78.0, 90), (79.0, 100), (82.0, 96),
             (84.0, 127), (84.02, 0), (IMPACT - 0.01, 0), (IMPACT, 127), (87.5, 100), (89.9, 20)])
    br.note(EV['n150'], 1.9, ['D3', 'A3', 'D4', 'F4'], 118)
    br.note(EV['estrategia'], 0.6, ['D3', 'A3', 'D4'], 70)
    br.note(EV['marcas'], 0.7, ['D3', 'A3', 'D4'], 86)
    br.note(76.47, 1.5, ['Bb2', 'F3', 'Bb3', 'D4'], 104)
    for t in [79.0, 79.5, 80.0, 80.5, 81.0]:
        c = CH[chord_at(t + 0.01)]
        br.note(t, 0.32, [c['root'] + '3'] + c['mid'][:2], 112)
    br.note(81.5, 0.5, ['Bb2', 'F3', 'D4'], 100)
    br.note(82.0, 1.0, ['C3', 'G3', 'E4'], 108)
    br.note(83.0, 1.0, ['A2', 'E3', 'A3', 'D4'], 116)
    br.note(83.5, 0.5, ['A2', 'E3', 'A3', 'C#4'], 122)
    br.note(IMPACT, 3.7, ['D2', 'A2', 'D3', 'F#3', 'A3', 'D4', 'F#4'], 124)
    st['brass'] = br.render(TOTAL, 0.5)

    hn = Part('horns', 60)
    hn.ramp([(70.0, 50), (78.0, 100), (84.0, 127), (84.02, 0), (IMPACT, 110), (89.9, 20)])
    for a, b, c in PROG:
        if 70.0 <= a < 84.0:
            hn.note(a, b - a + 0.05, CH[c]['mid'][:2], 90)
    hn.note(IMPACT + 0.05, 3.6, ['A3', 'D4', 'F#4', 'A4'], 104)
    st['horns'] = hn.render(TOTAL, 0.45)

    # ---------------- CORO ---------------------------------------------------
    co = Part('choir', 52, 17)
    co.ramp([(80.9, 0), (81.0, 40), (84.0, 120), (84.03, 0), (IMPACT - 0.01, 0), (IMPACT, 118), (88.2, 96),
             (89.9, 15)], nums=(2,))
    for a, b, c in PROG:
        if 81.0 <= a < 84.0:
            co.note(a, b - a + 0.05, CH[c]['mid'], 100)
    co.note(IMPACT, 3.75, ['D4', 'F#4', 'A4', 'D5', 'E5'], 110)
    st['choir'] = co.render(TOTAL, 0.4)

    # ---------------- PERCUSSÃO ORQUESTRAL ---------------------------------
    tp = Part('timpani', 47)
    def roll(t0, t1, n, v0, v1, step0=0.09, step1=0.045):
        t = t0
        while t < t1:
            x = (t - t0) / (t1 - t0)
            tp.note(t, 0.2, n, int(v0 + (v1 - v0) * x))
            t += step0 + (step1 - step0) * x
    roll(15.2, 15.95, 'A2', 40, 96)
    tp.note(EV['cut3'], 1.2, 'D2', 110)
    tp.note(EV['marcas'], 1.2, 'D2', 118)
    roll(25.0, 25.98, 'A2', 50, 110)
    tp.note(EV['n150'], 1.5, ['D2', 'A2'], 127)
    for a, b, c in PROG:
        if 65.96 <= a < 84.0:
            tp.note(a, 0.8, CH[c]['root'] + ('2' if CH[c]['root'] in ('D', 'C', 'Bb', 'A') else '2'), 100)
    roll(82.5, 83.98, 'A2', 60, 127, 0.07, 0.035)
    tp.note(IMPACT, 2.5, ['D2', 'A2'], 127)
    st['timpani'] = tp.render(TOTAL, 0.6)

    tk = Part('taiko', 116)
    pat = [0, 0.75, 1.0, 1.5]          # padrão por compasso de 2 s (120 BPM, 4/4)
    for bar in np.arange(66.0, 78.0, 2.0):
        for k, o in enumerate(pat):
            v = 118 if k == 0 else 84
            if bar < 70 and k in (1, 3):
                continue
            tk.note(bar + o, 0.5, 'C3' if k == 0 else 'G3', v)
    for t in np.arange(78.0, 84.0, 0.25):
        tk.note(t, 0.3, 'C3' if (t * 4) % 2 == 0 else 'G3', 96 if (t * 2) % 1 == 0 else 74)
    for t in [EV['estrategia'], EV['marcas'], EV['n150'], 76.47, IMPACT]:
        tk.note(t, 1.0, ['C3', 'C2'], 127)
    st['taiko'] = tk.render(TOTAL, 0.55)

    kit = Part('orch_kit', 48, drum=True)
    for t, v in [(EV['n150'], 120), (76.47, 100), (IMPACT, 127)]:
        kit.note(t, 3, [49, 57], v)               # pratos de choque
        kit.note(t, 2, 35, 127)                   # bumbo de concerto
    for t in [EV['marcas'], EV['cut3']]:
        kit.note(t, 2, 35, 110)
    st['kit'] = kit.render(TOTAL, 0.5)

    # ---------------- CAMPANAS / BRILHO --------------------------------------
    bl = Part('bells', 14)
    bl.note(EV['signature'], 3, ['D5'], 70)
    bl.note(EV['open_reveal'], 3, ['D5'], 38)
    st['bells'] = bl.render(TOTAL, 0.45)
    ce = Part('celesta', 8)
    for i, n in enumerate(['A5', 'D6', 'F6', 'A6']):
        ce.note(EV['caminho'] + 0.1 + i * 0.12, 1.5, n, 50)
    for i, n in enumerate(['D6', 'F#6', 'A6', 'D7', 'F#7']):
        ce.note(EV['signature'] + 0.05 + i * 0.07, 1.8, n, 58)
    for i, n in enumerate(['F5', 'A5', 'D6']):
        ce.note(EV['rumo'] - 0.25 + i * 0.1, 1.6, n, 44)
    st['celesta'] = ce.render(TOTAL, 0.45)

    # reverse cymbal (patch GM 119) para a chegada final
    rc = Part('revcym', 119)
    rc.note(IMPACT - 1.9, 1.95, 'C4', 110)
    rc.note(EV['n150'] - 1.4, 1.45, 'C4', 70)
    st['revcym'] = rc.render(TOTAL, 0.4)
    return st


# ===========================================================================
def synths():
    out = {k: np.zeros((NS, 2)) for k in ('pulse', 'sub', 'pad')}
    t_all = np.arange(NS) / SR

    # ---------------- PULSO ELETRÔNICO (8ths/16ths) --------------------------
    def pluck(f, dur, cutoff=900, level=0.3, p=0.0):
        n = secs(dur)
        t = np.arange(n) / SR
        saw = sum(np.sin(2 * np.pi * f * k * t * (1 + d)) / k for k in range(1, 18) for d in (-0.003, 0.003)) / 2
        y = butter(saw, 'lowpass', cutoff * (1 + 3 * np.exp(-t[0] / 0.03)), 2)
        y *= expdecay(n, dur * 0.35) * np.minimum(1, t / 0.002)
        return pan(softclip(y * level * 1.8, 1.4), p)

    def pulse_run(t0, t1, step, lvl0, lvl1, cut0, cut1, octave=2):
        k = 0
        for t in np.arange(t0, t1 - 1e-3, step):
            c = chord_at(t + 1e-3)
            if c is None:
                continue
            x = (t - t0) / max(t1 - t0, 1e-3)
            f = ROOT_HZ(c, octave) * (2 if k % 4 == 2 else 1)
            place(out['pulse'], pluck(f, step * 1.6, cut0 + (cut1 - cut0) * x, lvl0 + (lvl1 - lvl0) * x,
                                      0.25 if k % 2 else -0.25), t)
            k += 1
    pulse_run(EV['caminho'], 12.45, 0.25, 0.20, 0.30, 500, 900)
    pulse_run(EV['estrategia'], 15.55, 0.25, 0.28, 0.42, 700, 1600)
    pulse_run(15.97, 18.55, 0.25, 0.30, 0.34, 900, 1200)
    pulse_run(19.14, 25.14, 0.25, 0.32, 0.40, 900, 1700)
    pulse_run(25.14, 25.95, 0.125, 0.40, 0.48, 1700, 2600)
    pulse_run(62.0, 65.95, 0.25, 0.10, 0.30, 500, 1100)
    pulse_run(66.0, 78.0, 0.25, 0.30, 0.42, 900, 1800)
    pulse_run(78.0, 84.0, 0.125, 0.40, 0.52, 1600, 3200)

    # ---------------- SUB (raiz do acorde, oitava 1) --------------------------
    sub = np.zeros(NS)
    lvl = np.interp(t_all, [0, 0.6, 4.8, 5.05, 5.3, 11.0, 12.6, 15.97, 26.2, 28.3, 60.0, 62, 66, 83.9, 84.0, 84.1,
                            IMPACT, IMPACT + 0.01, 89.0, 90.0],
                    [0, .35, .4, 0, .15, .2, .35, .4, .5, .12, .1, .2, .4, .6, .6, 0, 0, .7, .4, 0])
    ph = 0.0
    freq = np.array([ROOT_HZ(chord_at(t) or 'Dm', 1) if chord_at(t) else 36.7 for t in t_all[::480]])
    freq = np.repeat(freq, 480)[:NS]
    freq = np.where(freq > 62, freq / 2, freq)
    # portamento curto
    k = int(0.03 * SR)
    freq = np.convolve(freq, np.ones(k) / k, mode='same')
    phs = 2 * np.pi * np.cumsum(freq) / SR
    sub = np.sin(phs) * lvl
    out['sub'] = stereo(softclip(sub, 1.2))

    # ---------------- PAD (supersaw filtrado, estéreo largo) ------------------
    pad = np.zeros((NS, 2))
    for a, b, c in PROG:
        if not (a < 28.27 or a >= 60.09):
            continue
        n = secs(b - a + 1.2)
        t = np.arange(n) / SR
        e = np.minimum(1, t / 0.6) * np.minimum(1, np.maximum(0, (b - a + 1.2) - t) / 1.2)
        notes = CH[c]['low'] + CH[c]['mid']
        if c == 'D':
            notes = ['D3', 'A3', 'D4', 'F#4', 'A4', 'E5']
        y = np.zeros((n, 2))
        for m in notes:
            f0 = 440 * 2 ** ((N(m) - 69) / 12)
            for d, p in [(-0.006, -0.9), (-0.002, -0.3), (0.002, 0.3), (0.006, 0.9)]:
                ph0 = RNG.uniform(0, 1)
                saw = 2 * ((f0 * (1 + d) * t + ph0) % 1) - 1
                y += pan(saw, p) * 0.05
        y = butter(y, 'lowpass', 1400 if a < 60 else 2200, 2)
        place(pad, y * e[:, None], a)
    out['pad'] = pad
    return out


# ===========================================================================
def sound_design():
    """Efeitos sincronizados com a imagem (ver EV / timeline)."""
    fx = np.zeros((NS, 2))
    E = EV

    def at(t, s, g=1.0, end=False):
        place(fx, s, t - (len(s) / SR if end else 0), g)

    # CENA 01 — linha de luz, revelação, "UMA DECISÃO", suspensão
    at(E['open_line'], sfx.light_streak(1.0, 0.35))
    at(E['open_reveal'], sfx.impact(0.55, 3.5, low=1.0, mid=0.35, top=0.15, wet=0.5, f0=52))
    at(E['open_reveal'] - 0.05, sfx.air(1.6, 0.18, 0.4, -0.4, 3500))
    at(E['uma'], sfx.pulse_hit(0.32, 60, -0.2))
    at(E['decisao'], sfx.pulse_hit(0.42, 55, 0.2))
    at(E['decisao'] + 0.02, sfx.metallic(0.16, 880, 2.0, 0.0, scrape=0.0, wet=0.5))
    at(E['q_end'] - 0.15, sfx.light_streak(0.8, 0.22))
    at(E['sc2'] + 0.05, sfx.rev_whoosh(1.3, 7000, 500, color='pink'), 0.42, end=True)

    # CENA 02 — constelação de perfis, SEGUIDORES riscado, caminho, ESTRATÉGIA, celular
    for k in range(16):
        t = 5.55 + k * 0.155 + RNG.uniform(-0.04, 0.04)
        at(t, sfx.tick(0.12 + 0.01 * k, RNG.uniform(1800, 3400), RNG.uniform(-0.8, 0.8)))
    at(E['seguidores'] - 0.32, sfx.whoosh(0.6, 400, 3200, -0.3, 0.3, peak=0.55, bw=1.1, wet=0.15), 0.32)
    at(E['strike'], sfx.metallic(0.34, 1350, 2.0, 0.6, scrape=0.9, wet=0.35))
    at(E['conteudo_end'] + 0.05, sfx.air(1.8, 0.24, 0.7, -0.7, 2500))
    at(E['caminho'] - 0.45, sfx.whoosh(1.4, 250, 5200, -0.9, 0.9, peak=0.45, bw=1.6, wet=0.3, body=0.25), 0.3)
    at(E['estrategia'] - 0.6, sfx.rev_whoosh(0.9, 5000, 600), 0.25, end=False)
    at(E['estrategia'], sfx.impact(0.62, 3.5, low=0.9, mid=0.55, top=0.3, f0=60))
    at(13.15, sfx.whoosh(0.7, 500, 2600, 0.9, 0.1, peak=0.6, bw=1.0, wet=0.2, body=0.15), 0.3)
    for k, t in enumerate([13.75, 14.05, 14.35, 14.65]):
        at(t, sfx.tick(0.2, 2600 + 250 * k, -0.4 + 0.25 * k))
    at(15.97, sfx.riser(1.9, 0.38), end=True)
    at(15.97 - 0.42, sfx.whoosh(0.6, 900, 7000, 0, 0, peak=0.7, bw=1.4, wet=0.2), 0.36)
    at(15.97, sfx.impact(0.5, 3.0, low=0.8, mid=0.6, top=0.4, f0=66))

    # CENA 03 — autoridade
    at(E['tres_anos'] - 0.05, sfx.whoosh(0.55, 700, 3500, -0.9, -0.4, peak=0.6, bw=0.9, wet=0.15), 0.22)
    at(E['tres_anos'] + 0.28, sfx.tick(0.16, 2100, -0.6))
    for t, s in sfx.count_ticks(E['n450'], E['marcas'] - 0.04, 11, 1300, 3000, 0.22):
        at(t, s)
    at(E['marcas'], sfx.impact(0.8, 3.5, low=1.0, mid=0.55, top=0.3, f0=58))
    at(E['marcas'] + 0.02, sfx.metallic(0.18, 700, 2.0, -0.5, scrape=0.0))
    at(E['contratos'] - 0.18, sfx.whoosh(0.75, 350, 4200, 0.95, 0.3, peak=0.62, bw=1.2, wet=0.2, body=0.2), 0.32)
    at(E['contratos'] + 0.30, sfx.metallic(0.24, 980, 1.8, 0.4, scrape=0.25))
    at(E['seis_meses'], sfx.tick(0.14, 2300, 0.3))
    at(E['n150'], sfx.riser(1.6, 0.5), end=True)
    at(E['n150'] - 0.55, sfx.rev_whoosh(0.55, 6000, 700), 0.4)
    for t, s in sfx.count_ticks(E['n150'] - 0.47, E['n150'] - 0.03, 9, 1600, 3600, 0.22):
        at(t, s)
    at(E["n150"], sfx.impact(0.85, 4.0, low=1.1, mid=0.8, top=0.45, wet=0.55, f0=55))
    at(E["n150"], sfx.sub_boom(3.0, 54, 34, 1.3), 0.6)
    at(E['n150'] + 0.05, sfx.shimmer((74, 81, 86, 89, 93), 3.0, 0.16, 0.25))
    at(E['lais'] - 0.35, sfx.air(1.4, 0.22, -0.6, 0.6, 3000))

    # CENA 04 — Laís: cards discretos (sob a voz)
    at(E['lais_15'] + 0.1, sfx.whoosh(0.45, 900, 3000, 0.9, 0.5, peak=0.6, bw=0.9, wet=0.12), 0.12)
    at(E['parcerias'] - 0.05, sfx.whoosh(0.5, 600, 2800, 0.9, 0.4, peak=0.6, bw=1.0, wet=0.12), 0.14)
    at(E['parcerias'] + 0.25, sfx.pulse_hit(0.2, 80, 0.4))
    at(E['internacional'] + 0.1, sfx.shimmer((86, 90, 93), 1.6, 0.08, 0.2))
    at(E['us50'] + 0.15, sfx.pulse_hit(0.2, 76, 0.4))
    at(E['us50'] + 0.17, sfx.tick(0.12, 2700, 0.5))
    at(E['r450'] - 0.05, sfx.whoosh(0.5, 700, 3200, 0.9, 0.4, peak=0.6, bw=1.0, wet=0.12), 0.14)
    at(E['r450'] + 0.25, sfx.pulse_hit(0.22, 74, 0.4))

    # CENA 05 — Sara: print em perspectiva + notificação + destaque
    at(E['sara'] - 0.1, sfx.whoosh(0.9, 300, 2600, 0.6, -0.2, peak=0.55, bw=1.3, wet=0.25, body=0.2), 0.3)
    at(E['sara'] + 0.45, sfx.bell((88, 95), 0.11, 0.2, 0.1))
    at(E['proposta'] + 0.1, sfx.air(1.2, 0.12, -0.3, 0.3, 4000))
    at(E['magalu'] + 0.15, sfx.metallic(0.2, 760, 2.2, 0.0, scrape=0.0, wet=0.5))
    at(E['analisar'] - 0.2, sfx.whoosh(0.6, 500, 2200, -0.2, 0.2, peak=0.5, bw=0.9, wet=0.15), 0.12)

    # CENA 06 — Bianca: emoção, brilho na frase
    at(E['bianca'] - 0.3, sfx.air(1.4, 0.2, 0.6, -0.6, 2600))
    at(E['bianca'] + 0.3, sfx.bell((93,), 0.0, 0.16, -0.2, 2.6, 1.2, 2.0))
    at(E['rumo_phrase'], sfx.air(1.4, 0.1, -0.4, 0.4, 6000))
    at(E['rumo'] - 0.2, sfx.shimmer((81, 86, 89, 93, 98), 2.8, 0.17, 0.3))

    # CENA 07 — Fernanda: respiro e sinceridade
    at(E['fernanda'] - 0.35, sfx.whoosh(0.8, 200, 1500, -0.5, 0.5, peak=0.45, bw=1.6, wet=0.35, body=0.3), 0.26)
    rp = Part('rp', 0)
    rp.note(0.5, 2.5, ['F3', 'C4', 'A4'], 70)
    rev_pno = rp.render(4.0, 0.6)
    at(E['vocesestao'] + 0.45, sfx.reverse_swell(rev_pno[:secs(2.6)], 'hall', 1.2, keep=1.6), 0.5, end=True)

    # CENA 08 — Rútilla: entrada em profundidade + início do crescendo
    at(E['rutilla'] - 0.05, sfx.impact(0.32, 2.5, low=0.6, mid=0.4, top=0.35, f0=70, wet=0.4))
    at(E['rutilla'] - 0.4, sfx.whoosh(0.55, 700, 4200, 0, 0, peak=0.75, bw=1.2, wet=0.2), 0.22)
    at(E['rutilla'] + 0.35, sfx.bell((86, 93), 0.09, 0.16, 0.2))
    at(E['visao'] + 0.1, sfx.tick(0.14, 2400, -0.2))
    at(E['resultados'] + 0.1, sfx.shimmer((86, 89, 93), 1.8, 0.1, 0.25))
    at(65.96, sfx.riser(3.6, 0.32), end=True)

    # CENA 09 — ascensão
    at(65.96, sfx.impact(0.45, 3.0, low=0.9, mid=0.5, top=0.25, f0=60))
    for t, p in [(E['pronta'], -0.6), (E['saber'], 0.6), (E['ideal'], -0.4)]:
        at(t - 0.1, sfx.air(1.2, 0.16, p, -p, 3500))
    for k, t in enumerate([73.0, 73.5, 74.0]):
        at(t, sfx.pulse_hit(0.42 + 0.06 * k, 62 - 3 * k, (-0.4, 0, 0.4)[k]))
    at(73.0 - 0.6, sfx.rev_whoosh(0.6, 5000, 700), 0.25)
    at(76.47 - 0.5, sfx.whoosh(0.7, 400, 5000, 0.8, -0.2, peak=0.72, bw=1.3, wet=0.25, body=0.25), 0.35)
    at(76.47, sfx.impact(0.65, 3.0, low=0.9, mid=0.6, top=0.35, f0=58))
    at(78.5, sfx.sub_drop(1.6, 120, 34, 0.75))
    at(78.5 - 0.5, sfx.rev_whoosh(0.5, 6000, 900), 0.3)
    montage_fx = [
        lambda: sfx.impact(0.5, 1.8, low=0.8, mid=0.5, top=0.4, f0=64, wet=0.3),
        lambda: sfx.whoosh(0.45, 800, 6000, -0.9, 0.9, peak=0.5, bw=1.2, wet=0.15),
        lambda: sfx.metallic(0.3, 1100, 1.4, 0.3, scrape=0.5),
        lambda: sfx.whoosh(0.45, 6000, 700, 0.9, -0.9, peak=0.4, bw=1.2, wet=0.15),
        lambda: sfx.impact(0.55, 2.0, low=1.0, mid=0.5, top=0.3, f0=56, wet=0.35),
    ]
    for k, t in enumerate([79.0, 79.5, 80.0, 80.5, 81.0]):
        at(t - (0.18 if k in (1, 3) else 0), montage_fx[k](), 0.6 if k in (1, 3) else 1.0)
    at(84.0, sfx.riser(2.9, 0.45), end=True)

    # SILÊNCIO -> BEM-VINDA -> IMPACTO FINAL
    at(E['blackout'] - 0.02, sfx.heartbeat(0.22))
    at(IMPACT, sfx.rev_whoosh(1.4, 8000, 600), 0.35, end=True)
    at(IMPACT, sfx.impact(0.8, 4.5, low=1.1, mid=0.9, top=0.5, wet=0.6, f0=54))
    at(IMPACT, sfx.sub_boom(3.6, 52, 33, 1.6), 0.5)
    at(IMPACT, sfx.metallic(0.3, 520, 3.5, 0.0, scrape=0.6, room='huge', wet=0.6))
    at(IMPACT + 0.02, sfx.light_streak(1.6, 0.3))
    at(EV['signature'], sfx.shimmer((86, 90, 93, 98, 102), 3.2, 0.2, 0.35))
    return fx


if __name__ == '__main__':
    import soundfile as sf, time
    os.makedirs('stems', exist_ok=True)
    t = time.time()
    st = orchestra()
    print('orquestra', time.time() - t)
    for k, v in st.items():
        sf.write(f'stems/orch_{k}.wav', v.astype(np.float32), SR, subtype='FLOAT')
    sy = synths()
    for k, v in sy.items():
        sf.write(f'stems/syn_{k}.wav', v.astype(np.float32), SR, subtype='FLOAT')
    print('synths', time.time() - t)
    fx = sound_design()
    sf.write('stems/sfx.wav', fx.astype(np.float32), SR, subtype='FLOAT')
    print('sfx', time.time() - t)
