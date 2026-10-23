"""Elementos compartilhados: plano da Duda com separação de profundidade, cards de vidro,
etiquetas de nome, legendas e pós-processamento."""
import math
import numpy as np
import cv2
import fx
from fx import px, ease_out, ease_in, ease_io, lin, keys, CHAMP, CHAMP_L, GOLD, OFFW, BEIGE, BLACK
import sources
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import CUES


# ---------------------------------------------------------------------------
def duda_layers(S, zoom=1.0, follow=1.0, dx=0.0, dy=0.0, eye_y=0.40, bg_dim=0.5, bg_blur=6.0, bg_desat=0.3,
                halo=0.08, rot=0.0):
    """Quadro real da Duda (sincronia labial preservada) com câmera virtual.
    Retorna (bg, fg, matte) já no espaço do quadro. zoom=1 enquadra a imagem inteira."""
    img, k = sources.duda(S)
    m = sources.duda_matte(S)
    fxp, fyp, fw = sources.face(S)
    sw, sh = img.shape[1], img.shape[0]
    fit = fx.W / sw
    s = fit * zoom
    # ponto da fonte que vai para o ponto (ox, oy) do quadro
    cx = 0.5 * sw + (fxp * k - 0.5 * sw) * follow
    cy_eye = fyp * k
    oy_target = fx.H * eye_y
    # centro da câmera de modo que os olhos fiquem na altura eye_y (quando follow=1)
    cy = cy_eye + (0.5 * fx.H - oy_target) / s * follow + (0.5 * sh) * (1 - follow)
    hv, vv = fx.W / 2 / s, fx.H / 2 / s
    cx = min(max(cx, hv), sw - hv) if hv * 2 <= sw else sw / 2
    cy = min(max(cy, vv), sh - vv) if vv * 2 <= sh else sh / 2
    M = fx.camera_matrix(s, cx, cy, fx.W / 2 + px(dx), fx.H / 2 + px(dy), rot)
    fg = fx.warp_affine(img, M, border=cv2.BORDER_REPLICATE)
    mt = fx.warp_affine(m, M, border=cv2.BORDER_REPLICATE)
    bg = fg
    if bg_blur > 0:
        bg = fx.blur(fg, bg_blur * fx.SC * 2)
    lum = bg.mean(2, keepdims=True)
    bg = (bg * (1 - bg_desat) + lum * bg_desat) * bg_dim
    if halo > 0:
        # luz seletiva: halo quente atrás da cabeça (separação de planos)
        hx = (fxp * k - cx) * s + fx.W / 2 + px(dx)
        hy = (fyp * k - cy) * s + fx.H / 2 + px(dy)
        bg = bg + fx.radial(hx, hy - px(120) * zoom, px(1100) * zoom, px(900) * zoom, CHAMP, 1.2) * halo
    # leve realce do primeiro plano (contraste local suave)
    fg = np.clip(fg * 1.02, 0, 1)
    eye = ((fxp * k - cx) * s + fx.W / 2 + px(dx), (fyp * k - cy) * s + fx.H / 2 + px(dy), fw * k * s)
    return bg, fg, mt, eye


def comp(bg, fg, m):
    out = fg - bg
    out *= m[..., None]
    out += bg
    return out


# ---------------------------------------------------------------------------
def glass_card(img, x, y, w, h, opacity=1.0, radius=36, border=0.45, tint_a=0.58, shadow=0.5):
    """Card de vidro fosco premium (coordenadas 4K -> quadro)."""
    if opacity <= 0.01:
        return img
    X, Y, Wd, Hd = px(x), px(y), int(px(w)), int(px(h))
    if shadow > 0:
        m_ = int(px(200))
        x0, y0 = max(int(X) - m_, 0), max(int(Y) - m_, 0)
        x1, y1 = min(int(X + Wd) + m_, fx.W), min(int(Y + Hd) + m_ + int(px(30)), fx.H)
        if x1 > x0 and y1 > y0:
            sh = np.zeros((y1 - y0, x1 - x0), np.float32)
            cv2.rectangle(sh, (int(X + px(10)) - x0, int(Y + px(30)) - y0),
                          (int(X + Wd - px(10)) - x0, int(Y + Hd + px(30)) - y0), 1, -1)
            sh = fx.blur(sh, px(50)) * shadow * opacity
            img[y0:y1, x0:x1] *= (1 - sh[..., None])
    fx.frosted(img, X, Y, Wd, Hd, sigma=36, tint=(0.05, 0.045, 0.04), tint_a=tint_a, radius=radius,
               opacity=opacity)
    st = fx.rounded_stroke(Wd, Hd, px(radius), max(1.2, px(2.2)))
    rgba = np.zeros((Hd, Wd, 4), np.float32)
    # borda com brilho superior (luz vinda de cima)
    grad = np.linspace(1.0, 0.35, Hd, dtype=np.float32)[:, None]
    rgba[..., :3] = CHAMP_L
    rgba[..., 3] = st * grad * border
    fx.over(img, rgba, X, Y, opacity)
    return img


def name_tag(img, name, role, x, y, t, t0, align='l', size=1.0):
    """Identificação discreta: Nome (serifa itálica) + PAPEL (sans espaçada) com fio dourado."""
    a = ease_out(lin(t, t0, t0 + 0.6))
    if a <= 0:
        return img
    off = (1 - a) * 40
    size = size * 1.3
    n, ni = fx.text(name, 'serif_i', 92 * size, 500, 0.0, OFFW)
    r, ri = fx.text(role, 'sans', 28 * size, 500, 0.32, CHAMP)
    if align == 'l':
        fx.place_text(img, n, ni, px(x + off), px(y), 'lb', a)
        L = px(70 * size) * ease_out(lin(t, t0 + 0.15, t0 + 0.8))
        cv2.line(img, (int(px(x)), int(px(y + 34 * size))), (int(px(x) + L), int(px(y + 34 * size))),
                 fx.col(CHAMP, a), max(1, int(px(3))), cv2.LINE_AA)
        fx.place_text(img, r, ri, px(x + 90 * size + off * 0.5), px(y + 46 * size), 'lb', a * 0.95)
    else:
        fx.place_text(img, n, ni, px(x - off), px(y), 'rb', a)
        fx.place_text(img, r, ri, px(x - off * 0.5), px(y + 46 * size), 'rb', a * 0.95)
    return img


def flash(img, amount, color=(1.0, 0.95, 0.86)):
    if amount <= 0.002:
        return img
    return img + np.asarray(color, np.float32) * amount


# ---------------------------------------------------------------------------
KEYWORDS = {'decisão', 'estratégico,', 'alto', 'nível', 'nível.', 'Alto', 'Nível.', 'dólar,', 'dólares.', 'dólares',
            'rumo.', 'Magazine', 'Luiza', 'webinar'}


def subtitles(img, T, hide=False, band_amt=0.35):
    if hide:
        return img
    cue = None
    for c in CUES:
        if c[0] - 0.001 <= T <= c[1]:
            cue = c
            break
    if cue is None:
        return img
    t0, t1, txt = cue
    a = min(ease_out(lin(T, t0, t0 + 0.14)), 1 - ease_in(lin(T, t1 - 0.12, t1)))
    if a <= 0.01:
        return img
    rise = (1 - ease_out(lin(T, t0, t0 + 0.25))) * 10
    lines = txt.split('\n')
    size = 88
    lh = size * 1.30
    base_y = 2160 * 0.925 - (len(lines) - 1) * lh + rise
    ytop = int(max(0, px(base_y - size * 1.6)))
    shadow_layer = np.zeros((fx.H - ytop, fx.W), np.float32)
    items = []
    for li, line in enumerate(lines):
        words = line.split(' ')
        rendered = []
        total = 0
        space = fx.font('ui', max(4, int(round(size * fx.SC))), 500).getlength(' ')
        for wd in words:
            hl = any(ch.isdigit() for ch in wd) or wd in KEYWORDS
            col = CHAMP_L if hl else OFFW
            r, ri = fx.text(wd, 'ui', size, 560 if hl else 500, 0.0, col)
            rendered.append((r, ri))
            total += ri['adv']
        total += space * (len(words) - 1)
        x = fx.W / 2 - total / 2
        y = px(base_y + li * lh)
        for r, ri in rendered:
            items.append((r, ri, x, y))
            ox = x - ri['pad']
            oy = y - ri['base'] - ytop
            h, w = r.shape[:2]
            x0, y0 = int(max(ox, 0)), int(max(oy, 0))
            x1, y1 = int(min(ox + w, fx.W)), int(min(oy + h, fx.H - ytop))
            if x1 > x0 and y1 > y0:
                shadow_layer[y0:y1, x0:x1] = np.maximum(shadow_layer[y0:y1, x0:x1],
                                                         r[y0 - int(oy):y1 - int(oy), x0 - int(ox):x1 - int(ox), 3])
            x += ri['adv'] + space
    # faixa escura sutil na base (legibilidade sobre fundos claros)
    y0b = int(px(base_y - 160))
    band = np.clip((np.arange(fx.H, dtype=np.float32) - y0b) / max(1, fx.H - y0b), 0, 1) ** 1.4
    img *= (1 - band_amt * a * band)[:, None, None]
    sh = fx.blur(shadow_layer, px(9))
    sh2 = fx.blur(shadow_layer, px(28))
    img[ytop:] *= (1 - np.clip(sh * 0.85 + sh2 * 0.35, 0, 0.9) * a)[..., None]
    for r, ri, x, y in items:
        fx.place_text(img, r, ri, x, y, 'lb', a)
    return img


def post(img, T, frame_idx, vig=0.5, grain_amt=0.02):
    img = fx.vignette(img, vig)
    img = fx.grain(img, frame_idx, grain_amt)
    # rolloff suave de altas luzes (evita clipping duro)
    hi = img > 0.92
    if hi.any():
        o = img[hi] - 0.92
        img[hi] = 0.92 + o / (1 + o * 6)
    return np.clip(img, 0, 1, out=img)
