"""Exporta artefatos editáveis da timeline:
  - legendas .srt (pt-BR) sincronizadas com o trailer final
  - EDL CMX3600 com os cortes de voz/imagem sobre o vídeo original (para reabrir a montagem no
    DaVinci Resolve / Premiere / Final Cut)
  - timeline.json com cenas, eventos de sincronia e cortes
"""
import json, os, sys
from timeline import CUES, VOICE, SCENES, EV, FPS, DUR, IMPACT

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def tc(t):
    f = int(round(t * FPS))
    s, fr = divmod(f, FPS)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f'{h:02d}:{m:02d}:{s:02d}:{fr:02d}'


with open(os.path.join(OUT, 'ALTO_NIVEL_legendas_ptBR.srt'), 'w', encoding='utf-8') as f:
    for i, (t0, t1, txt) in enumerate(CUES, 1):
        f.write(f'{i}\n{srt_time(t0)} --> {srt_time(t1)}\n{txt}\n\n')

with open(os.path.join(OUT, 'ALTO_NIVEL_cortes_voz.edl'), 'w') as f:
    f.write('TITLE: ALTO NIVEL - por Duda Dias - cortes de voz (90s)\nFCM: NON-DROP FRAME\n\n')
    for i, (s0, s1, t0) in enumerate(VOICE, 1):
        t1 = t0 + (s1 - s0)
        f.write(f'{i:03d}  ORIGINAL AA/V  C        {tc(s0)} {tc(s1)} {tc(t0)} {tc(t1)}\n')
        f.write('* FROM CLIP NAME: original.mov\n\n')

json.dump({
    'titulo': 'ALTO NÍVEL — por Duda Dias', 'duracao_s': DUR, 'fps': FPS, 'impacto_titulo_s': IMPACT,
    'cortes_voz': [{'origem_in': a, 'origem_out': b, 'trailer_in': t, 'trailer_out': round(t + b - a, 3)}
                   for a, b, t in VOICE],
    'cenas': {k: {'in': v[0], 'out': v[1]} for k, v in SCENES.items()},
    'eventos_sincronia': {k: round(v, 3) for k, v in sorted(EV.items(), key=lambda kv: kv[1])},
    'legendas': [{'in': round(a, 3), 'out': round(b, 3), 'texto': t} for a, b, t in CUES],
}, open(os.path.join(OUT, 'timeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', OUT)
