# YOU FOUND US. — THE FIRST SIGNAL · Campaign Film 001

Filme de 12,00 s para o primeiro Reels de @youfoundus.dl.

## Entregáveis (`entrega/`)
| Arquivo | Uso |
|---|---|
| `YOUFOUNDUS_THE-FIRST-SIGNAL_001_CTA_1080x1920.mp4` | Versão principal — publicar **somente com a landing page no ar** (tem "LINK NA BIO"). |
| `YOUFOUNDUS_THE-FIRST-SIGNAL_001_SEM-CTA_1080x1920.mp4` | Versão sem CTA — fecha em YF. / YOU FOUND US. / @youfoundus.dl. |
| `CAPA_REELS_E-QUEM-CRIA-POR-VOCE.png` | Quadro-chave para capa (texto dentro do recorte 3:4 da grade). |
| `QUADRO-FINAL_IDENTIDADE.png` | Último quadro, estável, usável como imagem de identidade. |

Especificação: 1080×1920 nativo (sem upscale), 9:16, 30 fps constantes, H.264 High, AAC 320 kbps 48 kHz estéreo, ~−13 LUFS / −1 dBTP.

## Como foi produzido (100% original, sem banco de imagens/música)
- **CGI**: a escultura *Signal Object* é modelada por campos de distância (SDF) e renderizada por raymarching em WebGL2 — obsidiana acetinada (Fresnel físico), filete prateado no bisel, interior de metal líquido com pontes que se rompem na abertura, iluminação de estúdio por área-lights, microtextura, profundidade de campo e bloom.
- **Tipografia**: vetorial (Cormorant Garamond 300–400, Manrope 300–400 — licença OFL), animada por máscaras, refração no vidro, oclusão real pela escultura e dissolução em partículas que se reorganizam no monograma.
- **Som**: trilha e sound design sintetizados do zero em Python (subgraves, síntese modal metálica, pads analógicos em Ré menor, assinatura sonora D5–A5–F5, reverb convolucional).

## Re-renderizar
```bash
cd source
node render.js ../frames cta 0-359          # frames principais
node render.js ../framesB nocta 270-359     # final sem CTA
python3 audio.py score.wav
./build.sh ../frames ../framesB score.wav ../entrega
```
Requer Node + Playwright (Chromium), Python 3 com numpy/scipy, ffmpeg.

## Pendência de marca
O monograma **"YF."** foi composto em Cormorant Garamond Light seguindo a descrição do briefing (fino, delicado, proporcional). A foto de perfil de referência **não foi enviada** nesta sessão — se o logo oficial for diferente, basta enviar o arquivo (SVG/PNG) que ele substitui o glifo nas cenas 04–05 e o filme é re-renderizado.
