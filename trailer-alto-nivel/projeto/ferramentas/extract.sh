#!/usr/bin/env bash
# Extrai do vídeo montado no CapCut as fontes usadas pelo projeto (rodar a partir de trailer-alto-nivel/):
#   src/original.mov  -> src/voice16k.wav, src/voice48k.wav
#                     -> ext/duda (quadros 4K tratados), ext/lais e ext/fern (recortes verticais)
# Os prints são limpos por mediana temporal em prints.py.
set -euo pipefail
mkdir -p ext/duda ext/lais ext/fern ext/prints ext/matte
ffmpeg -v error -y -i src/original.mov -vn -ac 1 -ar 16000 src/voice16k.wav
ffmpeg -v error -y -i src/original.mov -vn -ar 48000 -c:a pcm_s24le src/voice48k.wav

# Tratamento de cor Rec.709: cianos/azuis do sofá para grafite, pele preservada, altas luzes champanhe
GD="huesaturation=colors=c+b:saturation=-0.45:strength=1.5,huesaturation=colors=g:saturation=-0.3,eq=contrast=1.05:saturation=0.95:gamma=0.98,colorbalance=rs=-0.012:bs=0.018:rm=0.008:bm=-0.008:rh=0.022:gh=0.012:bh=-0.026,curves=master='0/0 0.06/0.045 0.5/0.5 0.86/0.87 1/0.965'"
GT="eq=contrast=1.04:saturation=0.96,colorbalance=rh=0.015:gh=0.008:bh=-0.018,curves=master='0/0 0.06/0.05 0.5/0.5 1/0.97'"

ex() { # nome quadro_ini quadro_fim recorte tratamento   (quadros a 30 fps)
  local ss dur
  ss=$(python3 -c "print($2/30)"); dur=$(python3 -c "print(($3-$2+1)/30)")
  ffmpeg -v error -y -ss "$ss" -i src/original.mov -t "$dur" -vf "fps=30,${4}${5}" -start_number "$2" -q:v 2 "ext/$1/%05d.jpg"
}
ex duda 0 141 "" "$GD" &
ex duda 453 822 "" "$GD" &
ex duda 1947 2566 "" "$GD" &
ex lais 816 1197 "crop=1066:1906:1387:128," "$GT" &
ex fern 1545 1773 "crop=1076:1906:1382:128," "$GT" &
wait
echo "ok"
