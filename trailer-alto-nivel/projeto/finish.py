import os, subprocess, build
W = os.path.join(build.OUT, 'work_master', 'video.mov')
x264_4k = ['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level', '5.1', '-pix_fmt', 'yuv420p',
           '-b:v', '45M', '-maxrate', '60M', '-bufsize', '90M', '-x264-params', 'keyint=60:min-keyint=30']
build.mux(W, os.path.join(build.OUT, 'ALTO_NIVEL_trailer_4K.mp4'), x264_4k)
print('4K ok', flush=True)
x264_hd = ['-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high', '-level', '4.2', '-pix_fmt', 'yuv420p',
           '-crf', '17', '-maxrate', '20M', '-bufsize', '30M', '-x264-params', 'keyint=60:min-keyint=30']
build.mux(W, os.path.join(build.OUT, 'ALTO_NIVEL_trailer_1080p.mp4'), x264_hd, size='1920:1080')
print('1080p ok', flush=True)
# versão web (< 100 MB) em 2 passes, 7,2 Mb/s
web = os.path.join(build.OUT, 'ALTO_NIVEL_trailer_1080p_web.mp4')
common = ['-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-profile:v', 'high',
          '-pix_fmt', 'yuv420p', '-b:v', '7200k', '-maxrate', '11M', '-bufsize', '14M',
          '-x264-params', 'keyint=60:min-keyint=30', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709']
plog = os.path.join(build.OUT, 'x264pass')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', W] + common + ['-pass', '1', '-passlogfile', plog, '-an', '-f', 'mp4', '/dev/null'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', W, '-i', build.AUD] + common + ['-pass', '2', '-passlogfile', plog,
               '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-map', '0:v:0', '-map', '1:a:0', '-t', '90', '-movflags', '+faststart', web], check=True)
print('web ok', flush=True)
