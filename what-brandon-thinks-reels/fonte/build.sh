#!/usr/bin/env bash
# Junta os segmentos renderizados + mixagem num MP4 pronto para o Reels.
set -e
printf "file '%s'\n" seg_0.mkv seg_1.mkv seg_2.mkv seg_3.mkv > segs.txt
ffmpeg -y -f concat -safe 0 -i segs.txt -i mix.wav \
  -map 0:v -map 1:a -c:v libx264 -profile:v high -preset slow -crf 14 -maxrate 18M -bufsize 36M \
  -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -r 30 \
  -c:a aac -b:a 320k -ar 48000 -ac 2 -t 24 -movflags +faststart WBT_reels_1080x1920_24s.mp4
