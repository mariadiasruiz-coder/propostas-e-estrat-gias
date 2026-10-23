"""Controle de qualidade do arquivo final: formato, duração exata, quadros, cor, loudness e pico verdadeiro."""
import json, subprocess, sys

f = sys.argv[1]
p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-count_frames', '-of', 'json', f],
                              capture_output=True, text=True).stdout)
v = next(s for s in p['streams'] if s['codec_type'] == 'video')
a = next(s for s in p['streams'] if s['codec_type'] == 'audio')
print(f"arquivo   {f}")
print(f"vídeo     {v['codec_name']} {v.get('profile')} {v['width']}x{v['height']} {v['r_frame_rate']} fps  "
      f"quadros={v.get('nb_read_frames')}  pix={v['pix_fmt']}  cor={v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')}")
print(f"áudio     {a['codec_name']} {a['sample_rate']} Hz {a['channels']} canais  {int(a.get('bit_rate', 0)) // 1000} kb/s")
print(f"duração   {float(p['format']['duration']):.3f} s   bitrate total {int(p['format']['bit_rate']) // 1000} kb/s   "
      f"tamanho {int(p['format']['size']) / 1e6:.1f} MB")
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f, '-map', '0:a', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
s = r[r.rfind('Summary'):]
for key in ('I:', 'LRA:', 'Peak:'):
    line = next((l.strip() for l in s.splitlines() if l.strip().startswith(key)), '')
    print('loudness ', line)
bd = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f, '-map', '0:v', '-vf', 'blackdetect=d=0.25:pix_th=0.04',
                     '-f', 'null', '-'], capture_output=True, text=True).stderr
print('trechos pretos (intencionais esperados: ~0,0–0,15 s e 84,13–84,48 s):')
for l in bd.splitlines():
    if 'black_start' in l:
        print('  ', l[l.find('black_start'):])
