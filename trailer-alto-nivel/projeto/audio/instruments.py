"""Renderização de partes orquestrais via FluidSynth + MuseScore_General (MIT; cordas VSCO-2 CE CC0,
piano 'Splendid Grand' domínio público). Cada parte vira um MIDI e é renderizada a 48 kHz, sem reverb
interno (a reverb é aplicada depois, por convolução, para coerência espacial)."""
import os, subprocess, tempfile
import numpy as np
import mido
import soundfile as sf
from dsp import SR

SF = '/usr/share/sounds/sf3/MuseScore_General_Full.sf3'
TPB = 960                     # ticks por segundo (tempo fixo de 60 BPM)
NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def N(s):
    """'D4' -> 62 ; aceita # e b ('F#3', 'Bb2')."""
    if isinstance(s, int):
        return s
    p = NAMES[s[0]]
    k = 1
    while k < len(s) and s[k] in '#b':
        p += 1 if s[k] == '#' else -1
        k += 1
    return 12 * (int(s[k:]) + 1) + p


class Part:
    def __init__(self, name, program, bank=0, drum=False):
        self.name, self.program, self.bank, self.drum = name, program, bank, drum
        self.notes = []          # (t, dur, pitch, vel)
        self.ccs = []            # (t, cc, val)

    def note(self, t, dur, pitch, vel=80):
        if isinstance(pitch, (list, tuple)):
            for p in pitch:
                self.note(t, dur, p, vel)
            return
        self.notes.append((float(t), float(dur), N(pitch), int(np.clip(vel, 1, 127))))

    def cc(self, t, num, val):
        self.ccs.append((float(t), num, int(np.clip(val, 0, 127))))

    def ramp(self, pts, nums=(11,), step=0.02):
        """Automação linear de CC: pts=[(t, v), ...]."""
        pts = sorted(pts)
        for (t0, v0), (t1, v1) in zip(pts[:-1], pts[1:]):
            for t in np.arange(t0, t1, step):
                v = v0 + (v1 - v0) * (t - t0) / max(t1 - t0, 1e-6)
                for n in nums:
                    self.cc(t, n, v)
        for n in nums:
            self.cc(pts[-1][0], n, pts[-1][1])

    def render(self, total=92.0, gain=0.5):
        ch = 9 if self.drum else 0
        evs = []
        for t, d, p, v in self.notes:
            evs.append((t, 1, mido.Message('note_on', channel=ch, note=p, velocity=v)))
            evs.append((t + d, 0, mido.Message('note_off', channel=ch, note=p, velocity=0)))
        for t, n, v in self.ccs:
            evs.append((t, 0.5, mido.Message('control_change', channel=ch, control=n, value=v)))
        evs.sort(key=lambda e: (e[0], e[1]))
        mid = mido.MidiFile(ticks_per_beat=TPB)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage('set_tempo', tempo=1_000_000))
        if not self.drum:
            tr.append(mido.Message('control_change', channel=ch, control=0, value=self.bank))
        tr.append(mido.Message('program_change', channel=ch, program=self.program))
        # volume nominal; dinâmica fica a cargo de CC11/velocity
        tr.append(mido.Message('control_change', channel=ch, control=7, value=110))
        if not any(n == 11 for _, n, _ in self.ccs):
            tr.append(mido.Message('control_change', channel=ch, control=11, value=127))
        last = 0
        for t, _, m in evs:
            tk = int(round(max(t, 0) * TPB))
            m.time = max(0, tk - last)
            last = max(last, tk)
            tr.append(m)
        tr.append(mido.MetaMessage('end_of_track', time=int(TPB * 3)))
        with tempfile.TemporaryDirectory() as d:
            mp, wp = os.path.join(d, 'p.mid'), os.path.join(d, 'p.wav')
            mid.save(mp)
            subprocess.run(['fluidsynth', '-ni', '-q', '-F', wp, '-r', str(SR), '-O', 'float', '-T', 'wav',
                            '-g', str(gain), '-R', '0', '-C', '0', '-o', 'synth.polyphony=1024', SF, mp],
                           check=True, capture_output=True)
            a, sr = sf.read(wp, dtype='float32')
        assert sr == SR
        n = int(total * SR)
        a = a[:n] if len(a) >= n else np.pad(a, ((0, n - len(a)), (0, 0)))
        return a.astype(np.float64)
