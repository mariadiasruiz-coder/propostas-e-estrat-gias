"""ALTO NÍVEL — por Duda Dias
Timeline-mestre (fonte da verdade para imagem, legendas, trilha e sound design).

T = tempo no trailer final (0–90 s, 30 fps)
S = tempo no vídeo original montado no CapCut (0–85,57 s)
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(ROOT)            # scratchpad (assets extraídos)
FPS = 30
DUR = 90.0
NFRAMES = int(DUR * FPS)                # 2700

# ---------------------------------------------------------------------------
# Trechos de voz/imagem com sincronia labial: (S_in, S_out, T_in)
# Entre eles há pausas dramáticas inseridas (sem acelerar nenhuma fala).
VOICE = [
    (0.08, 4.42, 0.60),     # Duda: pergunta de abertura
    (4.42, 15.10, 5.29),    # Duda (narração sobre tela preta) -> motion graphics
    (15.15, 26.95, 15.97),  # Duda: autoridade / números
    (27.30, 83.10, 28.33),  # Laís, Sara, Bianca, Fernanda, Rútilla, Duda (fechamento)
    (83.10, 84.70, 84.48),  # "Bem-vinda ao Alto Nível."
]
IMPACT = 86.25              # revelação ALTO NÍVEL / por Duda Dias


def s2t(s):
    for a, b, t0 in VOICE:
        if a - 1e-6 <= s <= b + 1e-6:
            return t0 + (s - a)
    raise ValueError(s)


def offset_for(t):
    """Offset S = T - off para imagem sincronizada no trecho que contém T."""
    for a, b, t0 in VOICE:
        if t0 <= t < t0 + (b - a):
            return t0 - a
    return None


# ---------------------------------------------------------------------------
# Palavras (Whisper large-v3, revisadas) já em T
def load_words():
    d = json.load(open(os.path.join(WORK, 'src', 'transcript.json')))
    ws = [w for s in d for w in s['words']][:-3]      # descarta alucinação final
    out = []
    for w in ws:
        s0, s1 = w['s'], w['e']
        try:
            out.append((w['w'].strip(), s2t(s0), s2t(s1)))
        except ValueError:
            # palavra na borda de um corte: aproxima pelo trecho mais próximo
            for a, b, t0 in VOICE:
                if a - 0.4 <= s0 <= b + 0.4:
                    out.append((w['w'].strip(), t0 + max(0, s0 - a), t0 + min(b - a, s1 - a)))
                    break
    return out

WORDS = load_words()

# Legendas: (palavra_ini, palavra_fim, texto). Texto revisado por escuta
# (Whisper: "Está"→"Estou há", "pública"→"publi", "Sarah"→"Sara", "No"→"Num").
CUES_SRC = [
    (0, 7, "E se a vida que você quiser construir"),
    (8, 14, "estiver do outro lado de uma decisão"),
    (15, 19, "que você ainda não tomou?"),
    (20, 26, "Muita gente ainda acredita que precisa"),
    (27, 33, "de milhares de seguidores pra viver de conteúdo."),
    (34, 42, "Mas a verdade é que existe um outro caminho."),
    (43, 48, "Um caminho mais estratégico, mais real"),
    (49, 55, "e muito mais próximo do que parece."),
    (56, 60, "Em três anos de profissão,"),
    (61, 68, "eu já trabalhei com mais de 450 marcas."),
    (69, 75, "Hoje, além dos meus contratos em dólar,"),
    (76, 79, "nos últimos seis meses,"),
    (80, 89, "a nossa operação já faturou\nmais de 150 mil dólares."),
    (90, 96, "Estou há 15 dias sendo mentorada por eles."),
    (97, 101, "Eu já fechei duas parcerias,"),
    (102, 104, "sendo uma internacional,"),
    (105, 109, "ganhando 50 dólares por semana,"),
    (110, 118, "e uma publi que eu fechei\nprospectando a empresa,"),
    (119, 121, "ganhando 450 reais."),
    (122, 132, "A Sara recebeu uma proposta de parceria\ncom a Magazine Luiza"),
    (133, 142, "e procurou direção para analisar\na oportunidade de forma certa."),
    (143, 149, "A Bianca ainda estava na primeira aula"),
    (150, 158, "e já sentia que finalmente\ntinha encontrado um rumo."),
    (159, 170, "E eu posso dizer que eu comecei\nexatamente onde vocês estão, tá?"),
    (171, 174, "Num webinar da Duda."),
    (175, 184, "Com a orientação certa deles\ne com o seu esforço,"),
    (185, 188, "gente, as coisas acontecem."),
    (189, 195, "E quando a visão certa encontra execução,"),
    (196, 203, "os resultados começam a deixar\nde parecer distantes."),
    (204, 211, "Talvez você ainda ache\nque precisa estar pronta,"),
    (212, 215, "que precisa saber tudo,"),
    (216, 221, "que precisa esperar o momento ideal."),
    (222, 230, "Mas a verdade é que\nnenhuma delas começou assim."),
    (231, 237, "Elas só decidiram dar o próximo passo."),
    (238, 243, "E é isso que muda tudo."),
    (244, 249, "Elas começaram exatamente aonde você tá."),
    (250, 255, "E decidiram viver o alto nível."),
    (256, 260, "Bem-vinda ao Alto Nível."),
]

# Correções de início de fala medidas no envelope (Whisper adianta algumas)
_START_FIX = {90: 28.55, 256: 84.64, 0: 0.72}


def build_cues():
    cues = []
    for k, (i0, i1, txt) in enumerate(CUES_SRC):
        t0 = _START_FIX.get(i0, WORDS[i0][1]) - 0.06
        t1 = WORDS[i1][2] + 0.30
        for a, b, tv in VOICE:                          # não atravessa pausas/cortes
            if tv <= WORDS[i1][2] <= tv + (b - a) + 0.05:
                t1 = min(t1, tv + (b - a) + 0.02)
        cues.append([t0, t1, txt])
    for k in range(len(cues) - 1):                      # sem sobreposição
        cues[k][1] = min(cues[k][1], cues[k + 1][0] - 0.04)
    return cues

CUES = build_cues()


def w(i, end=False):
    return WORDS[i][2 if end else 1]


# ---------------------------------------------------------------------------
# Cenas (T)
SCENES = {
    'S01_pergunta':     (0.00, 5.29),
    'S02_caminho':      (5.29, 15.97),
    'S03_autoridade':   (15.97, 28.27),
    'S04_lais':         (28.27, 40.88),
    'S05_sara':         (40.88, 47.70),
    'S06_bianca':       (47.70, 52.60),
    'S07_fernanda':     (52.60, 60.09),
    'S08_rutilla':      (60.09, 65.96),
    'S09_decisao':      (65.96, 84.13),
    'S09b_silencio':    (84.13, 84.48),
    'S10_bemvinda':     (84.48, IMPACT),
    'S10_titulo':       (IMPACT, DUR),
}

# Eventos de sincronia (imagem <-> som)
EV = dict(
    open_line=0.15, open_reveal=0.60,
    uma=w(13), decisao=w(14), q_end=w(19, True), sc2=5.29,
    seguidores=w(29), strike=w(29, True) + 0.35, conteudo_end=w(33, True),
    caminho=w(41), estrategia=w(46), real=w(48), proximo=w(52), cut3=15.97,
    tres_anos=w(57), n450=w(67), marcas=w(68), contratos=w(73), dolar=w(75),
    seis_meses=w(78), operacao=w(82), n150=w(87), mil=w(88), dolares_end=w(89, True),
    lais=28.27, lais_15=28.60, parcerias=w(100), internacional=w(104), us50=w(106),
    semana_end=w(109, True), publi=w(111), r450=w(120), reais_end=w(121, True),
    sara=40.88, proposta=w(126), magalu=w(131), analisar=w(137),
    bianca=47.70, rumo_phrase=w(151), encontrado=w(156), rumo=w(158),
    fernanda=52.60, comecei=w(165), vocesestao=w(168), webinar=w(172), esforco=w(184),
    rutilla=60.09, visao=w(192), resultados=w(197), distantes_end=w(203, True),
    final=65.96, pronta=w(211), saber=w(214), ideal=w(220), nenhuma=w(227),
    proximo_passo=w(236), muda_tudo=w(242), elas_comecaram=w(244), voce_ta=w(248),
    decidiram=w(251), alto_nivel1=w(254), blackout=84.13,
    bemvinda=84.64, nivel_end=w(260, True), impact=IMPACT, signature=IMPACT + 0.85,
)

# Grade rítmica da ascensão (cena 09): 120 BPM ancorado em 66,0 s
BEAT = 0.5
MONTAGE_CUTS = [79.0, 79.5, 80.0, 80.5, 81.0]

if __name__ == '__main__':
    for k, v in sorted(EV.items(), key=lambda kv: kv[1]):
        print(f'{v:7.2f}  {k}')
    print()
    for c in CUES:
        print(f'{c[0]:6.2f}-{c[1]:6.2f}  {c[2]!r}')
