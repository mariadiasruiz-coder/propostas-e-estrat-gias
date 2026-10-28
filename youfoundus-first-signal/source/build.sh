#!/usr/bin/env bash
# Encode frames + score into Instagram-ready masters.
# usage: build.sh <framesDir> <framesBDir> <score.wav> <outDir>
set -euo pipefail
F=$1; FB=$2; A=$3; O=$4; mkdir -p "$O"
enc() { ffmpeg -loglevel error -y -framerate 30 -i "$1/%04d.png" -i "$A" \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 14 -profile:v high -level 4.2 -pix_fmt yuv420p \
  -x264-params "aq-mode=3:deblock=-1,-1" -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv \
  -r 30 -t 12 -c:a aac -b:a 320k -ar 48000 -ac 2 -movflags +faststart "$2"; }
enc "$F" "$O/YOUFOUNDUS_THE-FIRST-SIGNAL_001_CTA_1080x1920.mp4"
# variant without CTA: frames 0-269 from main render, 270-359 from no-CTA render
T=$(mktemp -d); for f in "$F"/*.png; do n=$(basename "$f" .png); [ "$((10#$n))" -lt 270 ] && ln -s "$(realpath "$f")" "$T/$n.png"; done
for f in "$FB"/*.png; do ln -s "$(realpath "$f")" "$T/$(basename "$f")"; done
enc "$T" "$O/YOUFOUNDUS_THE-FIRST-SIGNAL_001_SEM-CTA_1080x1920.mp4"; rm -rf "$T"
# Reels cover (the question) + final identity frame
cp "$F/0192.png" "$O/CAPA_REELS_E-QUEM-CRIA-POR-VOCE.png"
cp "$F/0359.png" "$O/QUADRO-FINAL_IDENTIDADE.png"
