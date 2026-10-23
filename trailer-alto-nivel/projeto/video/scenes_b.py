"""Cenas 04–10: depoimentos (Laís, Sara, Bianca, Fernanda, Rútilla), ascensão, assinatura."""
import math
from functools import lru_cache
import numpy as np
import cv2
import fx
from fx import (px, ease_out, ease_in, ease_io, ease_io5, back_out, lin, keys, mix, CHAMP, CHAMP_L, GOLD, OFFW,
                BEIGE, BLACK, GRAPHITE)
import sources
from sources import PRINT_ROI
from common import duda_layers, comp, glass_card, flash, name_tag
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import EV, IMPACT, MONTAGE_CUTS

OFF4 = 1.03   # S = T - OFF4 (Laís ... fechamento)
OFF10 = 1.38
DUST = fx.Particles(200, seed=11, depth=(0.8, 6.0), size=(1.5, 5.5))
RISE = fx.Particles(260, seed=12, depth=(0.8, 6.0), size=(1.5, 5.0), drift=(0.0, -90.0))


# --------------------------------------------------------------------------- helpers
def clip_bg(frame_img, dim=0.32, desat=0.35, sigma=60, warm=0.06):
    """Fundo cinematográfico a partir do próprio vídeo vertical (cobre 16:9 sem distorcer)."""
    h, w = frame_img.shape[:2]
    s = max(fx.W / w, fx.H / h) * 1.08
    small = cv2.resize(frame_img, (max(1, int(w * s / 8)), max(1, int(h * s / 8))), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma * fx.SC / 8 * 2)
    big = cv2.resize(small, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC)
    y0 = (big.shape[0] - fx.H) // 2
    x0 = (big.shape[1] - fx.W) // 2
    bg = big[y0:y0 + fx.H, x0:x0 + fx.W]
    lum = bg.mean(2, keepdims=True)
    bg = (bg * (1 - desat) + lum * desat) * dim
    return bg + CHAMP * warm * dim


def panel(img, src, cx, cy, height, T, t_in, ry0=-9, ry1=-3, rx=0.0, opacity=1.0, border=0.55, radius=40,
          extra_scale=1.0):
    """Vídeo vertical como painel flutuante em 3D, proporção original preservada."""
    h, w = src.shape[:2]
    Hh = px(height) * extra_scale
    Ww = Hh * w / h
    a = ease_out(lin(T, t_in, t_in + 0.7)) * opacity
    if a <= 0:
        return img
    sc = Hh / h
    tex = cv2.resize(src, (int(Ww), int(Hh)), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
    m = fx.rounded_mask(tex.shape[1], tex.shape[0], px(radius))
    st = fx.rounded_stroke(tex.shape[1], tex.shape[0], px(radius), max(1.2, px(3)))
    tex = tex * (1 - st[..., None] * border) + CHAMP_L * st[..., None] * border
    rgba = np.dstack([tex, m]).astype(np.float32)
    ry = mix(ry0, ry1, ease_out(lin(T, t_in, t_in + 6)))
    rise = (1 - ease_out(lin(T, t_in, t_in + 0.8))) * px(120)
    q = fx.project_card(rgba.shape[1], rgba.shape[0], rx=rx, ry=ry, tx=px(cx) - fx.W / 2,
                        ty=px(cy) - fx.H / 2 + rise, tz=(1 - a) * px(500))
    fx.place_quad(img, rgba, q, opacity=a, shadow=0.7, shadow_blur=70, shadow_off=(30, 50))
    return img


def result_card(img, T, t0, x, y, big, small, kicker=None, w=1480, h=310, big_font='didone', big_size=170,
                active=1.0):
    a = ease_out(lin(T, t0, t0 + 0.5), 3)
    if a <= 0:
        return img
    slide = (1 - a) * 700
    glass_card(img, x + slide, y, w, h, a * mix(0.75, 1.0, active), radius=34, border=0.4 + 0.25 * active)
    X = x + slide + 70
    if kicker:
        k, ki = fx.text(kicker, 'sans', 32, 500, 0.4, CHAMP)
        fx.place_text(img, k, ki, px(X), px(y + 78), 'lb', a * 0.95)
    b, bi = fx.text(big, big_font, big_size, 600, 0.02, OFFW)
    b = fx.gradient_fill(b, OFFW, CHAMP_L)
    yb = y + (h * 0.66 if kicker else h * 0.60) + (24 if kicker else 0)
    fx.place_text(img, b, bi, px(X), px(yb), 'lb', a * mix(0.7, 1.0, active),
                  glow=0.25 * active * (1 - lin(T, t0 + 0.4, t0 + 1.2)), glow_color=CHAMP)
    if small:
        s, si = fx.text(small, 'sans', 36, 500, 0.32, BEIGE)
        fx.place_text(img, s, si, px(X + 8) + bi['adv'] + px(30), px(yb - 8), 'lb', a * 0.95)
    return img


def print_scene(T, name, t_in, cam_keys, ry_keys, base_h, cx, cy, roi_hl=None, hl_t=None, dim_rest=0.0, rx=0.0,
                entry='right', hl_style='outline', bg_rgb=None):
    """Print real flutuando em 3D sobre fundo atmosférico, com câmera e destaque de trecho."""
    img = fx.canvas(BLACK) if bg_rgb is None else bg_rgb.copy()
    pr = sources.print_rgba(name)
    h, w = pr.shape[:2]
    zoom = keys(T, cam_keys)
    sc_ = px(base_h) / h * zoom
    ry = keys(T, ry_keys)
    ent = ease_out(lin(T, t_in, t_in + 0.8), 3)
    if entry == 'right':
        tx = (1 - ent) * fx.W * 0.6
        ty = 0
        rx_e = rx
    else:   # de baixo, inclinado
        tx = 0
        ty = (1 - ent) * fx.H * 0.7
        rx_e = rx + (1 - ent) * 35
    # textura: reduz/expande uma vez para a escala final
    tw, th = max(2, int(w * sc_)), max(2, int(h * sc_))
    tex = cv2.resize(pr, (tw, th), interpolation=cv2.INTER_AREA if sc_ < 1 else cv2.INTER_CUBIC)
    # destaque do trecho
    if roi_hl is not None and hl_t is not None:
        if isinstance(roi_hl, list):          # [(t, roi), ...] -> interpola a janela de foco
            roi_hl = keys(T, roi_hl)
        x, y, rw, rh = roi_hl
        p = ease_io(lin(T, hl_t, hl_t + 0.7))
        if p > 0:
            X, Y, RW, RH = [int(v * sc_) for v in (x, y, rw, rh)]
            if dim_rest > 0:
                # foco seletivo: fora do trecho citado, desfoca e escurece (profundidade de campo)
                msk = np.zeros((th, tw), np.float32)
                pad_ = int(px(16) * zoom)
                cv2.rectangle(msk, (X - pad_, Y - pad_), (X + RW + pad_, Y + RH + pad_), 1.0, -1)
                msk = fx.blur(msk, px(14) * zoom)[..., None]
                tex = tex.copy()
                soft = fx.blur(tex[..., :3], px(7) * zoom)
                k_ = p * (1 - msk)
                tex[..., :3] = (tex[..., :3] * (1 - k_) + soft * k_) * (1 - dim_rest * k_)
            if hl_style == 'outline':
                pad = int(px(18) * zoom)
                st = fx.rounded_stroke(RW + 2 * pad, RH + 2 * pad, px(40) * zoom, max(1.5, px(5) * zoom), p)
                lay = np.zeros((th, tw, 4), np.float32)
                y0, x0 = max(Y - pad, 0), max(X - pad, 0)
                y1, x1 = min(Y - pad + st.shape[0], th), min(X - pad + st.shape[1], tw)
                lay[y0:y1, x0:x1, :3] = CHAMP_L
                lay[y0:y1, x0:x1, 3] = st[y0 - (Y - pad):y1 - (Y - pad), x0 - (X - pad):x1 - (X - pad)]
                g = fx.blur(lay[..., 3], px(14) * zoom)
                tex = tex.copy()
                tex[..., :3] = tex[..., :3] * (1 - lay[..., 3:4]) + lay[..., :3] * lay[..., 3:4] + g[..., None] * CHAMP * 0.6
            else:   # marca-texto champanhe varrendo da esquerda para a direita
                tex = tex.copy()
                xe = X + int(RW * p)
                reg = tex[Y:Y + RH, X:xe, :3]
                tex[Y:Y + RH, X:xe, :3] = reg * np.array([1.0, 0.83, 0.52], np.float32)
                uy = min(th - 2, Y + RH + int(px(4) * zoom))
                tex[uy:uy + max(1, int(px(5) * zoom)), X:xe, :3] = np.asarray(GOLD)
    q = fx.project_card(tw, th, rx=rx_e, ry=ry, tx=px(cx) - fx.W / 2 + tx, ty=px(cy) - fx.H / 2 + ty, tz=0)
    fx.place_quad(img, tex, q, opacity=ent, shadow=0.75, shadow_blur=90, shadow_off=(40, 70))
    return img, sc_


def quote(img, lines, x, y, T, t0, size=84, step=0.22, color=OFFW, italic=True, align='l', lh=1.18, a_mul=1.0):
    kind = 'serif_i' if italic else 'serif'
    for i, ln in enumerate(lines):
        p = ease_out(lin(T, t0 + i * step, t0 + i * step + 0.6), 3)
        if p <= 0:
            continue
        r, ri = fx.text(ln, kind, size, 500, 0.0, color)
        r = fx.masked(r, fx.wipe_mask(r.shape[0], r.shape[1], p, 'up', 0.35))
        fx.place_text(img, r, ri, px(x), px(y + i * size * lh) + (1 - p) * px(24), 'lb' if align == 'l' else 'rb',
                      a_mul)
    return img


# =========================================================================== CENA 04 — LAÍS
def scene04(T):
    S = T - OFF4
    src, _ = sources.clip('lais', S)
    img = clip_bg(src, dim=0.30)
    img += fx.light_leak(T, 21, 0.06)
    DUST.render(img, T, amount=0.5)
    push = mix(1.0, 1.045, lin(T, 28.27, 40.88))
    panel(img, src, 1180, 1060, 1760 * push, T, 28.20, ry0=10, ry1=4)
    name_tag(img, 'Laís', 'MENTORADA', 2140, 300, T, 28.5)
    # linha de progresso com marcos
    x_line = 2000
    ys = [570, 930, 1290, 1650]
    times = [EV['lais_15'], EV['parcerias'], EV['internacional'], EV['r450']]
    grow = ease_io(lin(T, 28.5, 40.0))
    y_end = ys[0] + (ys[-1] - ys[0]) * grow
    a_line = ease_out(lin(T, 28.4, 28.9))
    cv2.line(img, (int(px(x_line)), int(px(ys[0]))), (int(px(x_line)), int(px(y_end))),
             fx.col(CHAMP, 0.55 * a_line), max(1, int(px(2.5))), cv2.LINE_AA)
    for i, (yy, tt) in enumerate(zip(ys, times)):
        on = ease_out(lin(T, tt, tt + 0.3))
        if on > 0:
            spr = fx._sprite(int(px(16)))
            fx.add(img, spr[..., None] * CHAMP_L, px(x_line) - spr.shape[1] / 2, px(yy) - spr.shape[0] / 2, on * 1.2)
    last = max([i for i, tt in enumerate(times) if T >= tt] or [0])
    act = lambda i: 1.0 if i == last else 0.0
    result_card(img, T, times[0], 2120, ys[0] - 140, '15 DIAS', 'DE MENTORIA', active=act(0))
    result_card(img, T, times[1], 2120, ys[1] - 140, '2', 'PARCERIAS FECHADAS', active=act(1))
    # internacional: chip -> valor
    ti, tv = EV['internacional'], EV['us50']
    a = ease_out(lin(T, ti, ti + 0.5), 3)
    if a > 0:
        slide = (1 - a) * 700
        y = ys[2] - 140
        glass_card(img, 2120 + slide, y, 1480, 310, a * mix(0.75, 1, act(2)), radius=34, border=0.4 + 0.25 * act(2))
        k, ki = fx.text('INTERNACIONAL', 'sans', 32, 500, 0.4, CHAMP)
        fx.place_text(img, k, ki, px(2190 + slide), px(y + 78), 'lb', a)
        pv = ease_out(lin(T, tv, tv + 0.45))
        if pv > 0:
            b, bi = fx.text('US$ 50', 'didone', 170, 600, 0.02, OFFW)
            b = fx.gradient_fill(b, OFFW, CHAMP_L)
            fx.place_text(img, b, bi, px(2190 + slide), px(y + 240) + (1 - pv) * px(30), 'lb', a * pv,
                          glow=0.3 * (1 - lin(T, tv + 0.3, tv + 1.2)), glow_color=CHAMP)
            s, si = fx.text('/ SEMANA', 'sans', 36, 500, 0.32, BEIGE)
            fx.place_text(img, s, si, px(2198 + slide) + bi['adv'] + px(30), px(y + 232), 'lb', a * pv)
        else:
            gl = fx.text('· · ·', 'sans', 60, 500, 0.2, CHAMP)
            fx.place_text(img, gl[0], gl[1], px(2190 + slide), px(y + 200), 'lb', a * 0.6)
    result_card(img, T, times[3], 2120, ys[3] - 140, 'R$ 450', 'PUBLI · VIA PROSPECÇÃO', active=act(3))
    # transição de saída (para o print da Sara)
    if T > 40.5:
        k = lin(T, 40.5, 40.88)
        img = img * (1 - ease_in(k)) + fx.light_leak(T, 4, 0.4 * math.sin(math.pi * k))
    if T < 28.6:
        img = img * ease_out(lin(T, 28.20, 28.6)) + fx.light_leak(T, 3, 0.45 * (1 - lin(T, 28.2, 28.6)))
    return img, dict(vig=0.6, band=0.45)


# =========================================================================== CENA 05 — SARA
def _atmo(T, seed, warm=0.05, beam=0.08):
    img = fx.canvas(BLACK)
    img += fx.radial(fx.W * 0.4, fx.H * 0.5, fx.W * 0.8, fx.H * 0.8, GRAPHITE, 1.0) * 0.7
    img += fx.beams(T, origin=(0.85, -0.2), n=5, intensity=beam, seed=seed)
    img += fx.light_leak(T, seed, warm)
    return img


def scene05(T):
    bg = _atmo(T, 31, 0.05, 0.09)
    DUST.render(bg, T, amount=0.55)
    t_in = 40.80
    cam = [(40.8, 0.92), (41.6, 0.95), (EV['proposta'] - 0.1, 0.97), (43.4, 1.34), (45.0, 1.36), (46.6, 1.40),
           (47.7, 1.46)]
    ry = [(40.8, 34), (41.7, 9), (47.7, 5)]
    # o print se desloca para manter o trecho destacado em cena
    k1 = ease_io(lin(T, EV['proposta'] - 0.1, 43.4))
    k2 = ease_io(lin(T, EV['analisar'] - 0.6, EV['analisar'] + 0.9))
    cy = 1080 + 260 * k1 - 560 * k2
    cx = 1300 + 120 * k1
    roi = [(EV['analisar'] - 0.6, PRINT_ROI['sara']['bubble1']), (EV['analisar'] + 0.5, PRINT_ROI['sara']['bubble2'])]
    img, _ = print_scene(T, 'sara', t_in, cam, ry, 1380, cx, cy, roi, EV['proposta'], dim_rest=0.68, bg_rgb=bg)
    # citação fiel ao print (lado direito)
    ex = 1 - ease_in(lin(T, 47.3, 47.7))
    qa = ex
    if T > EV['magalu'] - 0.3:
        glass_card(img, 2420, 430, 1260, 1180, ease_out(lin(T, EV['magalu'] - 0.3, EV['magalu'] + 0.3)) * ex * 0.85,
                   radius=36, tint_a=0.62)
        quote(img, ['“Eu recebi uma', 'proposta de', 'parceria com a', 'Magazine Luiza.”'], 2530, 690, T,
              EV['magalu'] - 0.2, size=132, step=0.16, a_mul=qa)
        name_tag(img, 'Sara', 'MENTORADA', 2535, 1380, T, EV['magalu'] + 0.5, size=1.0)
        tg, tgi = fx.text('PROPOSTA RECEBIDA', 'sans', 34, 500, 0.4, BEIGE)
        fx.place_text(img, tg, tgi, px(2535), px(1520), 'lb', ease_out(lin(T, EV['magalu'] + 0.8, EV['magalu'] + 1.3)) * ex * 0.85)
    if T > 47.35:
        img = img * (1 - ease_in(lin(T, 47.35, 47.70)))
    return img, dict(vig=0.6, band=0.7)


# =========================================================================== CENA 06 — BIANCA
def scene06(T):
    img = fx.canvas(BLACK)
    img += fx.radial(fx.W * 0.6, fx.H * 0.45, fx.W * 0.75, fx.H * 0.75, BEIGE, 1.0) * 0.16
    img += fx.light_leak(T, 41, 0.10)
    img += fx.beams(T, origin=(0.2, -0.25), n=6, intensity=0.12, seed=7)
    DUST.render(img, T, amount=0.7)
    t_in = 47.62
    cam = [(47.6, 0.96), (EV['rumo_phrase'] - 0.2, 1.02), (51.2, 1.30), (52.6, 1.36)]
    ry = [(47.6, -12), (52.6, -6)]
    k = ease_io(lin(T, EV['rumo_phrase'] - 0.2, 51.2))
    cx = 2380 - 220 * k
    cy = 1100 + 330 * k
    img, _ = print_scene(T, 'bianca', t_in, cam, ry, 1500, cx, cy, PRINT_ROI['bianca']['rumo'], EV['rumo_phrase'],
                         dim_rest=0.5, entry='bottom', rx=4, hl_style='marker', bg_rgb=img)
    a = 1 - ease_in(lin(T, 52.3, 52.6))
    quote(img, ['“Já me vejo', 'tendo um rumo.”'], 250, 900, T, EV['encontrado'] - 0.15, size=150, step=0.32,
          a_mul=a)
    if T > EV['rumo'] - 0.2:
        # brilho discreto na revelação
        gl = 0.35 * math.sin(math.pi * lin(T, EV['rumo'] - 0.2, EV['rumo'] + 0.6))
        fx.light_line(img, px(1265), px(250), px(250) + px(1150) * ease_out(lin(T, EV['rumo'] - 0.2, EV['rumo'] + 0.4)),
                      0.7 * a, thick=1.3, glow=0.6, flare=0.4)
        img += fx.radial(px(900), px(1060), px(900), px(300), CHAMP, 1.5) * gl * a
    name_tag(img, 'Bianca', 'MENTORADA', 260, 1500, T, EV['bianca'] + 0.5, size=0.85)
    if T < 47.95:
        img = img * ease_out(lin(T, 47.62, 47.95))
    if T > 52.35:
        img = img * (1 - ease_in(lin(T, 52.35, 52.60))) + fx.light_leak(T, 6, 0.35 * lin(T, 52.35, 52.6))
    return img, dict(vig=0.55, band=0.7)


# =========================================================================== CENA 07 — FERNANDA
def scene07(T):
    S = T - OFF4
    src, _ = sources.clip('fern', S)
    img = clip_bg(src, dim=0.28, warm=0.1)
    img += fx.light_leak(T, 51, 0.05)
    DUST.render(img, T, amount=0.45)
    push = mix(1.0, 1.10, ease_io(lin(T, 52.6, 60.09)))
    panel(img, src, 2700, 1060 - 40 * (push - 1) * 10, 1780 * push, T, 52.55, ry0=-14, ry1=-6, radius=40)
    name_tag(img, 'Fernanda', 'MENTORADA', 3380, 2010, T, 53.2, align='r')
    # manchete construída palavra a palavra, no ritmo da fala
    words = [('EU COMECEI', EV['comecei'] - 0.25), ('EXATAMENTE', EV['comecei'] + 0.27),
             ('ONDE VOCÊS', EV['vocesestao'] - 0.32), ('ESTÃO.', EV['vocesestao'] + 0.25)]
    fade = 1 - 0.55 * ease_io(lin(T, 57.5, 58.5))
    for i, (wd, tt) in enumerate(words):
        p = ease_out(lin(T, tt, tt + 0.45), 3)
        if p <= 0:
            continue
        r, ri = fx.text(wd, 'serif', 170, 560, mix(0.2, 0.08, ease_out(lin(T, tt, tt + 1.2))), OFFW)
        if i == 3:
            r = fx.gradient_fill(r, CHAMP_L, GOLD, CHAMP)
        r = fx.masked(r, fx.wipe_mask(r.shape[0], r.shape[1], p, 'up', 0.35))
        fx.place_text(img, r, ri, px(250), px(760 + i * 210) + (1 - p) * px(30), 'lb', fade,
                      glow=0.25 if i == 3 else 0, glow_color=CHAMP)
    wa = ease_out(lin(T, EV['webinar'] - 0.1, EV['webinar'] + 0.5)) * fade
    if wa > 0:
        L = px(120) * wa
        cv2.line(img, (int(px(255)), int(px(1590))), (int(px(255) + L), int(px(1590))), fx.col(CHAMP, wa), max(1, int(px(3))), cv2.LINE_AA)
        r, ri = fx.text('num webinar da Duda.', 'serif_i', 92, 500, 0.0, CHAMP_L)
        fx.place_text(img, r, ri, px(410), px(1615), 'lb', wa)
    if T < 52.85:
        img = img * ease_out(lin(T, 52.55, 52.85)) + fx.light_leak(T, 6, 0.3 * (1 - lin(T, 52.55, 52.85)))
    return img, dict(vig=0.6)


# =========================================================================== CENA 08 — RÚTILLA
def scene08(T):
    img = fx.canvas(BLACK)
    up = lin(T, 60, 66)
    img += fx.radial(fx.W * 0.5, fx.H * 1.05, fx.W * 0.9, fx.H * 0.7, CHAMP, 1.0) * mix(0.10, 0.32, up)
    img += fx.beams(T, origin=(0.5, 1.25), n=8, intensity=mix(0.08, 0.24, up), seed=9, spread=0.9, length=2.2)
    RISE.render(img, T, amount=mix(0.6, 1.4, up), speed=mix(1.5, 3.0, up))
    t_in = 60.05
    cam = [(60.0, 0.94), (EV['visao'] - 0.1, 0.98), (61.8, 1.26), (65.9, 1.42)]
    k = ease_io(lin(T, EV['visao'] - 0.1, 61.8))
    cy = 1080 + 120 * k
    cx = 1920 + keys(T, [(60.0, 0), (61.8, 0), (65.9, -160)])
    ry = [(60.0, -10), (61.8, -4), (65.9, 7)]
    img, _ = print_scene(T, 'rutilla', t_in, cam, ry, 1330, cx, cy, PRINT_ROI['rutilla']['leo'],
                         EV['visao'] - 0.05, dim_rest=0.45, entry='bottom', rx=6, bg_rgb=img)
    name_tag(img, 'Rútilla', 'MENTORADA', 3480, 1960, T, 60.8, align='r', size=0.85)
    # saída: o print passa pela câmera em direção à luz
    if T > 65.6:
        k = lin(T, 65.6, 65.96)
        img = flash(img * (1 - 0.3 * k), 0.6 * ease_in(k, 2))
    if T < 60.35:
        img = img * ease_out(lin(T, 60.0, 60.35))
    return img, dict(vig=0.55, band=0.7)


# =========================================================================== CENA 09 — A DECISÃO
@lru_cache(maxsize=1)
def _montage_specs():
    return [
        ('lais', 30.6), ('print', 'sara'), ('fern', 53.6), ('print', 'bianca'),
    ]


def _montage(T, i, t0):
    k = lin(T, t0, t0 + 0.5)
    kind, arg = _montage_specs()[i]
    if kind in ('lais', 'fern'):
        src, _ = sources.clip(kind, arg + (T - t0))
        img = clip_bg(src, dim=0.35, warm=0.08)
        panel(img, src, 1920, 1080, 1900 * mix(1.0, 1.08, k), T, t0 - 1.0, ry0=0, ry1=0)
    else:
        img = _atmo(T, 70 + i, 0.08, 0.1)
        roi = PRINT_ROI['sara']['bubble1'] if arg == 'sara' else PRINT_ROI['bianca']['rumo']
        cx, cy = (1700, 1300) if arg == 'sara' else (2050, 1500)
        img, _ = print_scene(T, arg, t0 - 2.0, [(t0, 1.45), (t0 + 0.5, 1.6)], [(t0, 8 if arg == 'sara' else -8)] * 2,
                             1380 if arg == 'sara' else 1500, cx, cy, roi, t0 - 2.0, dim_rest=0.4,
                             hl_style='outline' if arg == 'sara' else 'marker', bg_rgb=img)
    # micro-transições distintas
    if i == 0:
        img = flash(img, 0.5 * (1 - ease_out(lin(T, t0, t0 + 0.12))))
    elif i == 1:
        sh = int((1 - ease_out(lin(T, t0, t0 + 0.15))) * px(160))
        if sh > 0:
            img = cv2.blur(img, (sh * 2 + 1, 1))
    elif i == 2:
        img = img + fx.light_leak(T, 9, 0.5 * (1 - lin(T, t0, t0 + 0.25)))
    else:
        z = 1 + 0.15 * (1 - ease_out(lin(T, t0, t0 + 0.18)))
        if z > 1.001:
            M = fx.camera_matrix(z, fx.W / 2, fx.H / 2)
            img = fx.warp_affine(img, M, border=cv2.BORDER_REFLECT)
    return img


def scene09(T):
    S = T - OFF4
    # montagem sincronizada com os pulsos (79,0 · 79,5 · 80,0 · 80,5)
    for i, t0 in enumerate(MONTAGE_CUTS[:4]):
        if t0 <= T < MONTAGE_CUTS[i + 1]:
            return _montage(T, i, t0), dict(vig=0.55)
    zoom = keys(T, [(65.96, 1.10), (71.8, 1.24), (72.2, 1.14), (77.5, 1.22), (78.35, 1.24), (78.9, 1.46),
                    (79.0, 1.46), (81.0, 1.20), (84.13, 1.32)], ease=lambda x: ease_io(x))
    dx = keys(T, [(65.96, 0), (72.0, 0), (72.5, 380), (75.2, 380), (75.9, 0), (84, 0)])
    dark = ease_io(lin(T, 72.4, 73.0)) * (1 - ease_io(lin(T, 75.0, 75.6)))
    bg, fg, m, eye = duda_layers(S, zoom=zoom, dx=dx, eye_y=0.40, bg_dim=mix(0.5, 0.28, dark), bg_blur=6,
                                 halo=0.08 + 0.06 * lin(T, 81, 84))
    frame = bg.copy()
    # linha do "nível" subindo atrás dela (81–84)
    if T > 81.6:
        k = ease_io(lin(T, 81.6, 84.0))
        y = mix(fx.H * 1.02, fx.H * 0.36, k)
        fx.light_line(frame, y, 0, fx.W, 0.9 * k + 0.1, thick=2.0, glow=1.1, flare=1.0)
        frame += fx.radial(fx.W / 2, y, fx.W * 0.7, px(300), CHAMP, 1.0) * 0.12 * k
        RISE.render(frame, T, amount=k, speed=2.0)
    # NINGUÉM COMEÇA PRONTA (atrás dela, à esquerda)
    ex = 1 - ease_in(lin(T, 75.0, 75.4))
    for i, (wd, tt) in enumerate([('NINGUÉM', 73.0), ('COMEÇA', 73.5), ('PRONTA.', 74.0)]):
        p = ease_out(lin(T, tt - 0.12, tt + 0.3), 3)
        if p <= 0 or ex <= 0:
            continue
        r, ri = fx.text(wd, 'serif', 235, 600, mix(0.3, 0.1, ease_out(lin(T, tt, tt + 1.2))), OFFW)
        if i == 2:
            r = fx.gradient_fill(r, CHAMP_L, GOLD, CHAMP)
        fx.place_text(frame, r, ri, px(210), px(800 + i * 285), 'lb', p * ex, blur_px=(1 - p) * px(14),
                      scale=mix(1.12, 1.0, p), glow=0.3 if i == 2 else 0, glow_color=CHAMP)
    frame = comp(frame, fg, m)
    # dúvidas que se dissolvem (pronta? saber tudo? o momento ideal?)
    for wd, tt, x, y in [('pronta?', EV['pronta'], 300, 640), ('saber tudo?', EV['saber'], 2880, 560),
                         ('o momento ideal?', EV['ideal'], 2700, 1500)]:
        k = lin(T, tt - 0.05, tt + 1.7)
        if 0 < k < 1:
            a = math.sin(math.pi * k) ** 0.8 * 0.75
            r, ri = fx.text(wd, 'serif_i', 110, 450, 0.02, BEIGE)
            fx.place_text(frame, r, ri, px(x + 80 * k), px(y - 60 * k), 'lb', a, blur_px=px(6) * k)
    # O PRÓXIMO PASSO É SEU. — momento central (Duda desfocada ao fundo)
    tp = EV['proximo_passo']
    foc = ease_io(lin(T, tp - 0.55, tp - 0.1)) * (1 - ease_io(lin(T, 77.55, 78.0)))
    if foc > 0.01:
        frame = fx.blur(frame, px(18) * foc) * (1 - 0.55 * foc)
        lines = [('O PRÓXIMO PASSO', -0.45, 190, OFFW), ('É SEU.', 0.0, 300, None)]
        for i, (wd, dt, sz, colr) in enumerate(lines):
            p = ease_out(lin(T, tp + dt, tp + dt + 0.4), 3)
            if p <= 0:
                continue
            r, ri = fx.text(wd, 'serif', sz, 600 if i else 560, mix(0.35, 0.16, ease_out(lin(T, tp + dt, tp + dt + 1.3))), OFFW)
            if i == 1:
                r = fx.gradient_fill(r, CHAMP_L, GOLD, CHAMP)
            r = fx.masked(r, fx.wipe_mask(r.shape[0], r.shape[1], p, 'center', 0.25))
            fx.place_text(frame, r, ri, fx.W / 2, px(900 + i * 380), 'cb', foc,
                          glow=(0.55 if i else 0.15) * (1 + 0.8 * (1 - ease_out(lin(T, tp, tp + 0.8)))),
                          glow_sigma=45, glow_color=CHAMP, scale=mix(1.06, 1.0, p))
        if T >= tp:
            fx.light_line(frame, px(990), fx.W / 2 - px(900) * ease_out(lin(T, tp, tp + 0.6)),
                          fx.W / 2 + px(900) * ease_out(lin(T, tp, tp + 0.6)), 0.8 * foc, thick=1.3, glow=0.7, flare=0.6)
    # impacto em "muda tudo"
    frame = flash(frame, 0.25 * (1 - ease_out(lin(T, 78.5, 78.8))) * (T >= 78.5))
    frame = flash(frame, 0.12 * (1 - ease_out(lin(T, tp, tp + 0.3))) * (T >= tp))
    if T >= 81.0 and T < 81.15:
        frame = flash(frame, 0.4 * (1 - lin(T, 81.0, 81.15)))
    if T < 66.25:
        frame = flash(frame * ease_out(lin(T, 65.96, 66.2)), 0.5 * (1 - lin(T, 65.96, 66.25)))
    return frame, dict(vig=0.6)


# =========================================================================== CENA 10
def scene10(T):
    S = T - OFF10
    zoom = mix(1.62, 1.72, lin(T, 84.48, IMPACT))
    bg, fg, m, eye = duda_layers(S, zoom=zoom, eye_y=0.42, bg_dim=0.28, bg_blur=8, halo=0.06)
    frame = comp(bg, fg, m)
    frame *= ease_out(lin(T, 84.48, 84.68))
    # antecipação: a linha de luz nasce no último instante
    if T > 85.95:
        k = ease_in(lin(T, 85.95, IMPACT), 2)
        fx.light_line(frame, fx.H * 0.5, fx.W / 2 - fx.W * 0.5 * k, fx.W / 2 + fx.W * 0.5 * k, k, thick=1.6)
        frame = frame * (1 - 0.5 * k)
    return frame, dict(vig=0.65)


# =========================================================================== TÍTULO FINAL
def title(T):
    t = T - IMPACT
    img = fx.canvas(BLACK)
    img += fx.radial(fx.W / 2, -fx.H * 0.1, fx.W * 0.6, fx.H * 0.9, CHAMP, 1.0) * 0.10
    img += fx.beams(T, origin=(0.5, -0.35), n=9, intensity=0.13, seed=13, spread=0.8, length=2.0)
    DUST.render(img, T, amount=0.8)
    push = mix(1.0, 1.035, ease_io(lin(T, IMPACT, 90.0)))
    fade_out = 1 - ease_in(lin(T, 89.25, 89.98))
    cy = fx.H * 0.50
    # ALTO NÍVEL
    open_ = ease_out(lin(t, 0.0, 0.7), 3)
    tr = mix(0.62, 0.34, ease_out(lin(t, 0.0, 3.5), 2))
    r, ri = fx.text('ALTO NÍVEL', 'serif', 330 * push, 520, tr, OFFW)
    r = fx.gradient_fill(r, hexc_l(), GOLD, CHAMP_L)
    sweep = lin(t, 0.35, 1.5)
    if 0 < sweep < 1:
        xx = np.linspace(0, 1, r.shape[1], dtype=np.float32)[None, :]
        yy = np.linspace(0, 1, r.shape[0], dtype=np.float32)[:, None]
        band = np.exp(-(((xx + yy * 0.3) - mix(-0.25, 1.35, sweep)) / 0.05) ** 2)
        r = r.copy()
        r[..., :3] = r[..., :3] + band[..., None] * 0.55
    r = fx.masked(r, fx.wipe_mask(r.shape[0], r.shape[1], open_, 'center', 0.25))
    fx.place_text(img, r, ri, fx.W / 2, cy + px(70), 'cb', fade_out, glow=0.35 + 0.8 * (1 - ease_out(lin(t, 0, 1.2))),
                  glow_sigma=45, glow_color=CHAMP, blur_px=(1 - open_) * px(6))
    # fio do nível
    Lw = px(1650) * push * ease_out(lin(t, 0.05, 1.0), 3)
    fx.light_line(img, cy + px(165), fx.W / 2 - Lw / 2, fx.W / 2 + Lw / 2, 0.85 * fade_out, thick=1.3, glow=0.7,
                  flare=0.6)
    # por Duda Dias
    sig = ease_out(lin(T, EV['signature'], EV['signature'] + 0.8), 3)
    if sig > 0:
        s, si = fx.text('por Duda Dias', 'serif_i', 120 * push, 500, mix(0.25, 0.06, sig), OFFW)
        s = fx.masked(s, fx.wipe_mask(s.shape[0], s.shape[1], sig, 'right', 0.3))
        fx.place_text(img, s, si, fx.W / 2, cy + px(350), 'cb', fade_out * 0.95, glow=0.2, glow_color=CHAMP)
    # impacto: clarão + rastro
    img = flash(img, 0.65 * (1 - ease_out(lin(t, 0.0, 0.4))))
    if t < 0.5:
        fx.light_line(img, cy + px(150), 0, fx.W, 1.2 * (1 - lin(t, 0, 0.5)), thick=2.5, glow=1.3, flare=1.5)
    img *= max(fade_out, 0.0) * 0.85 + 0.15 * fade_out
    return img, dict(vig=0.6)


def hexc_l():
    return fx.hexc('FBF1DC')
