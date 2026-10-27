# What Brandon Thinks — Reels "Sua conversa. Sua curiosidade. Sua privacidade."

Vídeo vertical de 24 s para Instagram Reels e TikTok, produzido a partir do master prompt da campanha.

| Arquivo | O que é |
|---|---|
| `WBT_reels_1080x1920_24s.mp4` | **Arquivo para postar.** 1080×1920, 9:16, 30 fps, H.264 High, ~16 Mbps, áudio AAC estéreo 48 kHz, −14 LUFS |
| `fonte/` | Código que gera o vídeo quadro a quadro (pode ser editado e renderizado de novo) |

## Roteiro como foi produzido

| Tempo | Cena | Texto na tela | Narração |
|---|---|---|---|
| 0:00–2:7 | A grande dúvida | UMA **IA** LENDO SEU CHAT? → MAS… É SEGURO? | "Uma IA lendo seu chat? É seguro?" |
| 2:7–5:6 | Você escolhe | VOCÊ ESCOLHE O QUE ENVIAR. | "Você escolhe a conversa que quer analisar." |
| 5:6–9:0 | Criptografia | CRIPTOGRAFADO. / NO ENVIO + NO ARMAZENAMENTO | "Os dados são criptografados no envio e armazenamento." |
| 9:0–11:8 | Participantes | NINGUÉM DO CHAT É AVISADO. | "Ninguém da conversa é avisado." |
| 11:8–14:9 | Sem treino de IA | SEUS CHATS NÃO TREINAM IA. | "Seus chats não são usados para treinar IA." |
| 14:9–18:0 | Controle | VOCÊ CONTROLA SEUS DADOS. / EXCLUA QUANDO QUISER + aviso dos 7 dias | "E você pode apagá-los quando quiser." |
| 18:0–21:1 | O veredito | PADRÕES DA CONVERSA / QUEM PUXA ASSUNTO? / O VEREDITO DO BRANDON → E O BRANDON? TEM UMA OPINIÃO. | "Brandon transforma a conversa em um relatório surpreendente." |
| 21:1–24:0 | CTA | Logo + AGORA É SUA VEZ. / TESTE A PRÉVIA GRÁTIS / whatbrandonthinks.com / SIGA @WHATBRANDONTHINKSBRASIL | "Teste sua prévia grátis no site oficial!" |

Todos os textos importantes ficam entre 14% do topo e 35% da base da tela, a área segura do Reels. O último quadro fica parado, sem fade para preto.

## Como foi feito (e o que isso significa)

- **Mascote 2.5D:** as duas imagens de referência foram recortadas (`fonte/cut.py`) e animadas como camadas, com entrada, inclinação, aceno, reflexo nas lentes e luz de recorte. A aparência é 100% a da referência, mas **não há animação facial nem gestos de mão**: o personagem não foi remodelado em 3D.
- **Motion design:** canvas 2D renderizado em 1080×1920 nativo com tipografia cinética (Sora ExtraBold e Space Grotesk), mockups conceituais, partículas, escudo, túnel e transições (íris pela lente, match-cut, whip-pan, light leak).
- **Narração:** voz neural pt-BR (Microsoft Edge TTS, "Antonio").
- **Trilha e efeitos:** compostos por código, 120 BPM, sem samples de terceiros: drone de tensão, pad, baixo, arpejos, impactos, lock-click, assinatura sonora de 3 notas. A música abaixa automaticamente quando a voz entra.

## Para chegar a uma versão 3D "de estúdio"

Hoje nenhuma ferramenta gera 24 s contínuos com personagem consistente, texto em português sem erro e sincronia de áudio. O fluxo que funciona melhor:

1. **Gerar cada cena separadamente** (4–8 s) em Veo, Kling ou Runway, usando a imagem do Brandon como referência de personagem ou como primeiro quadro, e **sem pedir texto dentro do vídeo** (IA de vídeo ainda erra letras).
2. **Montar no CapCut, After Effects ou Premiere** e colocar por cima os textos, o logo e o CTA, aproveitando a tipografia e os tempos deste vídeo.
3. **Reaproveitar a mixagem deste vídeo** (narração, trilha e efeitos já sincronizados) como guia de tempo.

Este vídeo também serve como animatic e referência de tempo para esse caminho.

## Gerar de novo

```bash
cd fonte
pip install edge-tts numpy scipy        # narração (tts.py) e áudio (audio.py)
# render: node + playwright, 4 processos em paralelo
for k in 0 1 2 3; do node render.js full $k $((k*180)) $(((k+1)*180)) & done; wait
```
Depois, junte os segmentos `seg_*.mkv` com a mixagem `mix.wav` (veja `build.sh`).
