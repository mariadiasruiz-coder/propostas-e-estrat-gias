# ALTO NÍVEL — por Duda Dias
### Trailer cinematográfico · 90 s · 16:9 · pt-BR

> *A transformação que começa com uma decisão.*

Este diretório tem a produção completa do trailer: o projeto que gera o vídeo, a trilha original, o sound design, as legendas, a timeline editável e as licenças. O vídeo final é **gerado inteiro por código**, a partir do vídeo montado no CapCut, e pode ser regenerado com um comando.

---

## 1. Entregáveis

| Arquivo | O que é |
|---|---|
| `ALTO_NIVEL_trailer_4K.mp4` *(513 MB, enviado à parte: grande demais para o Git)* | **Master** 3840×2160, 30 fps, 2700 quadros, H.264 High 5.1, Rec.709 SDR, 45,6 Mb/s, AAC 320 kb/s 48 kHz estéreo, **90,000 s** |
| `ALTO_NIVEL_trailer_1080p.mp4` *(218 MB, enviado à parte)* | 1920×1080 em alta qualidade (CRF 17, ~19 Mb/s), para apresentações e webinars |
| `entrega/ALTO_NIVEL_trailer_1080p_web.mp4` | 1920×1080, 7,5 Mb/s, 84 MB, *faststart*: para página de vendas, checkout e upload em plataformas |

**Controle de qualidade medido nos três arquivos finais** (`projeto/qc.py`): 90,000 s · 2700 quadros · 30 fps · Rec.709 · −14,0 LUFS integrado · pico verdadeiro −1,2 dBTP · LRA 2,5 LU.
| `entrega/ALTO_NIVEL_legendas_ptBR.srt` | Legendas sincronizadas (camada separada, para players que aceitam SRT) |
| `entrega/ALTO_NIVEL_cortes_voz.edl` | EDL CMX3600 com os 5 cortes de voz/imagem sobre o `original.mov`, para reabrir a montagem no DaVinci/Premiere/FCP |
| `entrega/timeline.json` | Mapa completo: cenas, cortes, 70+ eventos de sincronia imagem↔som e legendas |
| `entrega/stems/` | Stems de áudio em FLAC 24 bits: voz, trilha, efeitos e o master |
| `projeto/` | Código-fonte de toda a produção (imagem, trilha, mixagem, build) |
| `licencas/` | Licenças das fontes, da soundfont e dos modelos usados |

---

## 2. Estrutura narrativa (tempos reais do trailer)

A montagem seguiu o **áudio real**: nenhuma fala foi acelerada, cortada no meio da palavra ou recombinada. Para chegar a exatamente 90 s, foram inseridas só **pausas dramáticas** (sem fala): abertura, suspensão após a pergunta, respiro após os US$ 150 mil, silêncio antes de "Bem-vinda" e a revelação final.

| Tempo | Cena | Imagem | Som |
|---|---|---|---|
| 00:00–00:05 | **01 · A pergunta** | Linha de luz nasce no escuro e se abre como uma fenda, revelando a Duda. "UMA DECISÃO" surge **atrás** dela, recortada por matte. | Grave cinematográfico, piano espaçado (Lá–Fá–Ré–Mi), drone de violoncelos. Suspensão e whoosh reverso. |
| 00:05–00:16 | **02 · Existe outro caminho** *(era tela preta)* | Campo 3D de conteúdos reais; constelação de "seguidores"; **NÃO É SOBRE SEGUIDORES** riscado a ouro; caminho dourado em perspectiva; **É SOBRE ESTRATÉGIA**; celular 3D com a Duda gravando + fluxo CONTEÚDO → MARCAS → CONTRATOS; mergulho na tela. | Cliques digitais, acento metálico no risco, primeiro **pulso eletrônico** em "outro caminho", impacto em "estratégia", riser até o corte. |
| 00:16–00:28 | **03 · Autoridade** | 3 ANOS DE PROFISSÃO → contagem **450+ MARCAS** → card de vidro **CONTRATOS EM DÓLAR** com globo → **US$ 150 MIL+** · *Faturamento da operação · últimos 6 meses*, com a Duda desfocada ao fundo. | Ostinato de cordas, contagem com ticks, impacto no "marcas", whoosh + metal no card, stop + riser e o **maior impacto até então** no 150. |
| 00:28–00:41 | **04 · Laís** | Vídeo vertical em painel 3D na proporção original, sobre fundo dele mesmo desfocado; linha de marcos: 15 DIAS · 2 PARCERIAS · INTERNACIONAL US$ 50/SEMANA · R$ 450. | Trilha recua (piano em arpejo, cordas suaves); efeitos discretos sob a voz. |
| 00:41–00:48 | **05 · Sara** | Print entra em perspectiva; foco seletivo no balão "Eu recebi uma proposta de parceria com a magazine Luiza"; citação fiel; etiqueta **PROPOSTA RECEBIDA**. | Whoosh suave, tom de notificação, acento tonal no destaque. |
| 00:48–00:53 | **06 · Bianca** | Print sobe da base; marca-texto champanhe em "já me vejo tendo um rumo"; citação revelada por máscara com brilho. | Melodia de piano e violoncelo cantabile; brilho tonal no "rumo". |
| 00:53–01:00 | **07 · Fernanda** | Painel à direita, *push-in* gradual; manchete **EU COMECEI EXATAMENTE ONDE VOCÊS ESTÃO.** construída palavra a palavra; "— num webinar da Duda." | Percussão ausente, voz em primeiro plano; textura de piano reverso. |
| 01:00–01:06 | **08 · Rútilla** | Print sobe inclinado em profundidade; destaque em "Leo e Duda tem muita visão de mercado e resultados incríveis"; luz e partículas subindo. | Entrada com impacto curto, notificação, início do crescendo (riser, pulsos voltando). |
| 01:06–01:24 | **09 · A decisão** | Duda em *push-in*; dúvidas que se dissolvem ("pronta?", "saber tudo?"); **NINGUÉM COMEÇA PRONTA.**; **O PRÓXIMO PASSO É SEU.**; montagem nos pulsos (Laís, Sara, Fernanda, Bianca); a **linha do nível sobe** atrás dela. | 120 BPM: ostinato, taikos, tímpanos, metais, coro, trêmolos. Sub drop em "muda tudo". Pico em 01:24 e **corte seco**. |
| 01:24–01:26 | **10 · Bem-vinda** | Silêncio e preto; close íntimo: "Bem-vinda ao Alto Nível." | Quase silêncio (batida grave abafada), a voz sozinha, whoosh reverso. |
| 01:26–01:30 | **Assinatura** | Clarão → **ALTO NÍVEL** com reflexo metálico e fio de luz → ***por Duda Dias***. Fade no quadro 2700. | Tutti orquestral em **Ré maior** (a transformação Ré menor → Ré maior), boom, pratos, sinos, cauda longa terminando aos 90,0 s. |

**Assinatura oficial:** somente "ALTO NÍVEL / por Duda Dias". O nome "Leo" só aparece onde ele existe no depoimento original da Rútilla.

---

## 3. Fidelidade das provas (o que aparece na tela e de onde vem)

| Na tela | Fonte literal |
|---|---|
| 450+ MARCAS · em 3 anos de profissão | Duda: "Em três anos de profissão, eu já trabalhei com mais de 450 marcas." |
| CONTRATOS EM DÓLAR | Duda: "além dos meus contratos em dólar" |
| US$ 150 MIL+ · Faturamento da operação · últimos 6 meses | Duda: "nos últimos seis meses, a nossa operação já faturou mais de 150 mil dólares" (rotulado como **operação**, não como renda pessoal nem lucro) |
| 15 DIAS · 2 PARCERIAS · US$ 50/SEMANA · R$ 450 | Laís, no vídeo original (trechos contínuos, sem recombinar palavras) |
| "Eu recebi uma proposta de parceria com a Magazine Luiza." · PROPOSTA RECEBIDA | Print da Sara (proposta **recebida**; sem logotipo nem sugestão de endosso da marca) |
| "Já me vejo tendo um rumo." | Print da Bianca |
| EU COMECEI EXATAMENTE ONDE VOCÊS ESTÃO. — num webinar da Duda. | Fernanda, no vídeo original |
| "Leo e Duda tem muita visão de mercado e resultados incríveis" | Print da Rútilla (texto original intacto) |

Nenhum print foi alterado: foram limpos (mediana temporal dos quadros estáticos para tirar ruído de compressão) e só ganharam enquadramento, perspectiva e foco seletivo.

**Revisão da transcrição** (Whisper large-v3, conferida trecho a trecho): "Está 15 dias" → **"Estou há 15 dias"**; "uma pública" → **"uma publi"**; "Sarah" → **"Sara"** (como no print); "No webinar" → **"Num webinar"**. A primeira frase da Duda é **"…que você quiser construir…"** (é o que está no áudio; o roteiro dizia "quer").

**Dados pessoais:** os prints mostram sobrenomes ("Sara Teodoro", "Bianca Figueiredo"), como na montagem original. Se preferir ocultá-los, é um ajuste de uma linha no projeto (desfoque na região do cabeçalho).

---

## 4. Trilha original e sound design

**Composição:** *Hybrid Cinematic Trailer Score* composta nota a nota sobre a timeline (`projeto/audio/score.py`). Ré menor, com resolução final em Ré maior.

- **Progressões:** Dm–Bb–Gm (mistério) → Dm–Bb–F–C (descoberta/autoridade, 120 BPM) → F–C–Dm–Bb (depoimentos, piano a 80 BPM) → Dm–Bb–F–C–Gm, montagem a cada meio tempo, Asus4–A (dominante) → **silêncio** → **D maior** (tutti).
- **Orquestra:** piano Splendid Grand, cordas expressivas VSCO-2 (lentas, ostinato spiccato, trêmolo), violoncelos, contrabaixos, metais, trompas, coro, tímpanos, taikos, pratos de concerto, sinos tubulares, celesta, prato reverso.
- **Camada híbrida (sintetizada):** pulsos eletrônicos com filtro abrindo, sub-bass seguindo as fundamentais, pad *supersaw* largo.
- **Sound design (100% gerado):** impactos em camadas, sub booms, sub drop, whooshes com filtro em varredura e pan em movimento, whooshes reversos, risers, cliques digitais, contagem com ticks acelerando, acentos metálicos, notificações FM, *air sweeps*, *shimmers*, piano reverso, traços de luz sonoros e batida grave. Cada som é posicionado pelo mesmo evento (`timeline.EV`) que dispara a animação correspondente, então imagem e som usam o mesmo relógio, sem nenhuma sincronia manual.

**Mixagem e master** (`projeto/audio/mix.py`, `voice.py`):
- Vozes: declip, HPF 75 Hz, redução leve de ruído, EQ (−2 dB em 280 Hz, +1,8 dB em 3,2 kHz, brilho em 9,5 kHz), de-esser e compressão 3:1. Nivelamento por locutora em −18 LUFS (o original variava de −7 a −17 LUFS entre trechos).
- Trilha: metas de loudness por seção (arco emocional) mais **ducking automático** guiado pela voz (6–7 dB) e recorte de médios onde a voz vive.
- Master: limpeza infrassônica, limiter *look-ahead* de pico verdadeiro com 4× oversampling.
- **Medido no master (FFmpeg EBU R128): −14,0 LUFS integrado · pico verdadeiro −1,3 dBTP · 48 kHz estéreo.**

---

## 5. Imagem

- **Fonte:** o `.mov` do CapCut (3840×2160, 60 fps, ~2,2 Mb/s). Os quadros da Duda têm detalhe 4K real; os depoimentos verticais são ampliações (~1066×1906 dentro do quadro) e foram exibidos **perto da escala nativa**, sem upscale artificial e sem esticar.
- **Separação de profundidade:** matte de pessoa (RobustVideoMatting) em todos os quadros da Duda. Ele escurece e desfoca o fundo (luz seletiva) e permite a **tipografia atrás dela**.
- **Cor:** Rec.709, preto profundo, altas luzes champanhe, cianos do sofá dessaturados para grafite, pele preservada, *roll-off* suave de altas luzes, grão fino e vinheta discretos.
- **Tipografia** (todas OFL): Cormorant Garamond (títulos), Bodoni Moda (números), Montserrat (rótulos), Inter (legendas).
- **Hierarquia visual:** legendas (Inter, base da tela, sombra suave) ≠ títulos (serifa champanhe, cinéticos) ≠ cards (vidro fosco, Bodoni, provas).
- **Paleta:** preto `#0A0908` · grafite `#2B2926` · champanhe `#E3C99A` / `#F2E3C4` · dourado discreto `#C9A464` · off-white `#F4EFE6` · bege `#CDB89A`.

---

## 6. Como regenerar

Requisitos: Python 3.11+, FFmpeg com libx264, FluidSynth e o pacote `musescore-general-soundfont` (Debian/Ubuntu), além de `numpy scipy opencv-python-headless pillow soundfile pyloudnorm mido onnxruntime faster-whisper`.

```bash
# 0) dentro de trailer-alto-nivel/: copie o vídeo do CapCut para src/original.mov e baixe o modelo
#    rvm_mobilenetv3_fp32.onnx (RobustVideoMatting v1.0.0) para models/
# 1) preparar fontes (uma vez): quadros tratados, áudio, matte, prints limpos, posição do rosto
bash projeto/ferramentas/extract.sh
python3 projeto/ferramentas/transcribe.py src/voice16k.wav src/transcript.json   # já incluso em src/
python3 projeto/ferramentas/matte.py && python3 projeto/ferramentas/prints.py && python3 projeto/ferramentas/facetrack.py
# 2) trilha, efeitos, vozes e master
cd projeto/audio && python3 score.py && python3 voice.py && python3 mix.py && cd ..
# 3) imagem + encode final (4 processos em paralelo)
python3 build.py preview     # 960×540 para revisão rápida
python3 build.py master      # 4K ProRes intermediário -> MP4 4K e 1080p
python3 export_timeline.py ../entrega
```

Todos os tempos ficam num único arquivo, `projeto/timeline.py`. Mudar um evento ali move juntos a animação, o efeito sonoro e a legenda.

---

## 7. Limitações (relato honesto)

- **Não havia geração de vídeo por IA disponível.** As telas pretas viraram motion graphics 3D construídos com material real da própria Duda e das mentoradas, em vez de cenas sintéticas.
- **Não houve audição humana durante a produção.** A trilha e a mixagem foram validadas por medições objetivas (loudness por seção, espectro, envelopes rítmicos, pico verdadeiro, mapas de atividade por instrumento), não de ouvido. Antes de publicar, vale uma audição atenta em fone e em celular. Ajustes de nível por seção ficam em `projeto/audio/mix.py` (`SECT`).
- A orquestra usa uma soundfont livre (MuseScore General: cordas VSCO-2, piano Splendid Grand). O resultado é sólido, mas não tem o realismo de bibliotecas comerciais como Spitfire ou Kontakt. Com uma biblioteca premium, as mesmas partes MIDI (geradas pelo `score.py`) podem ser re-renderizadas sem mexer na composição.
- Não havia imagens de bastidores reais nem "imagens aspiracionais" extras no material. A montagem da cena 09 usa só os depoimentos e prints reais.
- Os *push-ins* na Duda são zooms digitais sobre o 4K original (1,06× a 1,7×, este no close de "Bem-vinda"). Nesses planos a nitidez em 4K é um pouco menor que a do quadro original. Não foi aplicado nenhum upscale ou nitidez artificial, para não criar detalhes que não existem.
- O vídeo do CapCut chegou com bitrate baixo (~2,2 Mb/s para 4K/60). Se existir o arquivo bruto do celular (sem a recompressão do CapCut), basta trocar `src/original.mov` e regenerar para ganhar nitidez em todo o filme.
