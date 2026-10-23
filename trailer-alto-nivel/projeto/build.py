"""Build completo: renderiza a imagem em N processos paralelos, concatena e une com a trilha masterizada.

  python3 build.py preview   -> 960x540, x264 (revisão rápida)
  python3 build.py master    -> 3840x2160 ProRes intermediário -> H.264 High (MP4) + versão 1080p
"""
import os, sys, subprocess, time
from timeline import NFRAMES, FPS

ROOT = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(ROOT, 'video')
AUD = os.path.join(ROOT, 'audio', 'out', 'master_48k_24bit.wav')
OUT = os.path.join(os.path.dirname(ROOT), 'out')


def render_parallel(width, workdir, nproc=4, codec='x264'):
    os.makedirs(workdir, exist_ok=True)
    bounds = [round(i * NFRAMES / nproc) for i in range(nproc + 1)]
    procs = []
    ext = 'mov' if codec == 'prores' else 'mp4'
    parts = []
    for k in range(nproc):
        out = os.path.join(workdir, f'part{k}.{ext}')
        parts.append(out)
        env = dict(os.environ, CODEC=codec, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        log = open(os.path.join(workdir, f'part{k}.log'), 'w')
        procs.append(subprocess.Popen([sys.executable, 'render.py', 'video', str(width), out, str(bounds[k]),
                                       str(bounds[k + 1])], cwd=VID, env=env, stdout=log, stderr=subprocess.STDOUT))
    t0 = time.time()
    for p in procs:
        p.wait()
        if p.returncode != 0:
            raise SystemExit('falha no render (ver logs em %s)' % workdir)
    print(f'render {width}px: {time.time() - t0:.0f}s')
    lst = os.path.join(workdir, 'parts.txt')
    with open(lst, 'w') as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    joined = os.path.join(workdir, f'video.{ext}')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', joined],
                   check=True)
    return joined


def mux(video, out, vcodec_args, size=None):
    vf = []
    if size:
        vf = ['-vf', f'scale={size}:flags=lanczos']
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', AUD] + vf + vcodec_args + [
        '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
        '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-ac', '2',
        '-map', '0:v:0', '-map', '1:a:0', '-t', '90', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    if mode == 'preview':
        v = render_parallel(960, os.path.join(OUT, 'work_preview'))
        mux(v, os.path.join(OUT, 'preview_540p.mp4'), ['-c:v', 'libx264', '-crf', '20', '-preset', 'fast',
                                                       '-pix_fmt', 'yuv420p'])
    elif mode == 'master':
        v = render_parallel(3840, os.path.join(OUT, 'work_master'), codec='prores')
        x264_4k = ['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level', '5.1', '-pix_fmt', 'yuv420p',
                   '-b:v', '45M', '-maxrate', '60M', '-bufsize', '90M', '-x264-params', 'keyint=60:min-keyint=30']
        mux(v, os.path.join(OUT, 'ALTO_NIVEL_trailer_4K.mp4'), x264_4k)
        x264_hd = ['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level', '4.2', '-pix_fmt', 'yuv420p',
                   '-crf', '17', '-maxrate', '20M', '-bufsize', '30M', '-x264-params', 'keyint=60:min-keyint=30']
        mux(v, os.path.join(OUT, 'ALTO_NIVEL_trailer_1080p.mp4'), x264_hd, size='1920:1080')
