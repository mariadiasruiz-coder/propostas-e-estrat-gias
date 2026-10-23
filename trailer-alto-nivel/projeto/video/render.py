"""Renderizador do trailer: despacha cada quadro (T) para a cena correspondente, aplica
legendas e acabamento, e encoda em paralelo.

Uso:
  python3 render.py stills 1280 0.7 3.6 8.4 ...      # quadros de prévia (PNG)
  python3 render.py video 3840 out.mov [f0 f1]      # sequência (ProRes 422 HQ intermediário)
"""
import sys, os, subprocess, time
import numpy as np
import cv2
import fx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import FPS, NFRAMES, IMPACT, SCENES


def frame(T, idx=0):
    import scenes_a, scenes_b, common
    if T < 5.29:
        img, o = scenes_a.scene01(T)
    elif T < 15.97:
        img, o = scenes_a.scene02(T)
    elif T < 28.27:
        img, o = scenes_a.scene03(T)
    elif T < 40.88:
        img, o = scenes_b.scene04(T)
    elif T < 47.70:
        img, o = scenes_b.scene05(T)
    elif T < 52.60:
        img, o = scenes_b.scene06(T)
    elif T < 60.09:
        img, o = scenes_b.scene07(T)
    elif T < 65.96:
        img, o = scenes_b.scene08(T)
    elif T < 84.13:
        img, o = scenes_b.scene09(T)
    elif T < 84.48:
        img, o = fx.canvas(fx.BLACK), dict(vig=0.3)
    elif T < IMPACT:
        img, o = scenes_b.scene10(T)
    else:
        img, o = scenes_b.title(T)
    img = common.subtitles(img, T, hide=T >= IMPACT - 0.02, band_amt=o.get('band', 0.35))
    img = common.post(img, T, idx, vig=o.get('vig', 0.5), grain_amt=o.get('grain', 0.012))
    return img


def to8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def stills(width, times, outdir):
    fx.setup(width)
    os.makedirs(outdir, exist_ok=True)
    for T in times:
        t0 = time.time()
        img = frame(T, int(T * FPS))
        cv2.imwrite(os.path.join(outdir, f'T{T:06.2f}.png'), to8(img)[:, :, ::-1])
        print(f'T={T:.2f}  {time.time() - t0:.2f}s', flush=True)


def video(width, out, f0=0, f1=NFRAMES, codec='prores'):
    fx.setup(width)
    if codec == 'prores':
        enc = ['-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', '-vendor', 'apl0']
    else:
        enc = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{fx.W}x{fx.H}',
           '-r', str(FPS), '-i', '-'] + enc + ['-color_primaries', 'bt709', '-color_trc', 'bt709',
                                                 '-colorspace', 'bt709', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(f0, f1):
        T = i / FPS
        img = frame(T, i)
        p.stdin.write(to8(img).tobytes())
        if (i - f0) % 30 == 0:
            el = time.time() - t0
            print(f'[{f0}-{f1}] quadro {i}  {el / max(1, i - f0 + 1):.2f}s/quadro', flush=True)
    p.stdin.close()
    p.wait()


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        stills(int(sys.argv[2]), [float(x) for x in sys.argv[3:]], os.environ.get('OUT', 'previews'))
    elif mode == 'video':
        f0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
        f1 = int(sys.argv[5]) if len(sys.argv) > 5 else NFRAMES
        video(int(sys.argv[2]), sys.argv[3], f0, f1, os.environ.get('CODEC', 'prores'))
