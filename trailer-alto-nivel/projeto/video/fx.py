"""Biblioteca de composição (float32 RGB/RGBA em [0,1]). Todas as medidas de design são
em unidades 4K (3840x2160) e multiplicadas por SC, permitindo prévias em baixa resolução."""
import os, math
from functools import lru_cache
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

cv2.setNumThreads(1)
FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'fonts')

W = H = SC = None


def setup(width):
    global W, H, SC
    W = int(width)
    H = int(round(W * 9 / 16))
    SC = W / 3840.0


def px(v):
    return v * SC


# ---------------------------------------------------------------------------
# Paleta
def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)

BLACK = hexc('0A0908')
GRAPHITE = hexc('2B2926')
CHAMP = hexc('E3C99A')
CHAMP_L = hexc('F2E3C4')
GOLD = hexc('C9A464')
OFFW = hexc('F4EFE6')
BEIGE = hexc('CDB89A')


# ---------------------------------------------------------------------------
# Easing
def clamp01(x):
    return max(0.0, min(1.0, x))


def lin(t, a, b):
    return clamp01((t - a) / (b - a)) if b != a else float(t >= a)


def ease_out(x, p=3):
    x = clamp01(x)
    return 1 - (1 - x) ** p


def ease_in(x, p=3):
    x = clamp01(x)
    return x ** p


def ease_io(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_io5(x):
    x = clamp01(x)
    return x * x * x * (x * (6 * x - 15) + 10)


def back_out(x, s=1.4):
    x = clamp01(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def mix(a, b, x):
    return a + (b - a) * x


def keys(t, pts, ease=ease_io):
    """Interpolação por keyframes [(t, valor), ...] com easing entre pares."""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts[:-1], pts[1:]):
        if t0 <= t <= t1:
            x = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            if isinstance(v0, (tuple, list, np.ndarray)):
                return tuple(mix(np.asarray(v0, float), np.asarray(v1, float), x))
            return mix(v0, v1, x)
    return pts[-1][1]


# ---------------------------------------------------------------------------
# Composição
def canvas(color=BLACK):
    c = np.empty((H, W, 3), np.float32)
    c[:] = color
    return c


def over(dst, src, x=0, y=0, opacity=1.0):
    """Alpha-over de src RGBA (h,w,4) em dst na posição inteira (x,y) (canto sup. esq.)."""
    if opacity <= 0.001:
        return dst
    h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    a = s[..., 3:4] * opacity
    d = dst[y0:y1, x0:x1]
    d *= (1 - a)
    d += s[..., :3] * a
    return dst


def add(dst, src, x=0, y=0, amount=1.0):
    """Soma aditiva (luz). src RGB ou RGBA (usa rgb*alpha)."""
    if amount <= 0.001:
        return dst
    h, w = src.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    if s.shape[2] == 4:
        s = s[..., :3] * s[..., 3:4]
    dst[y0:y1, x0:x1] += s * amount
    return dst


def screen(dst, light):
    """Screen blend em tela cheia."""
    return 1 - (1 - dst) * (1 - np.clip(light, 0, 1))


def blur(img, sigma):
    if sigma < 0.3:
        return img
    if sigma > 4:
        f = max(1, int(sigma / 3))
        h, w = img.shape[:2]
        small = cv2.resize(img, (max(1, w // f), max(1, h // f)), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), sigma / f)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(img, (0, 0), sigma)


def premul(rgba):
    out = rgba.copy()
    out[..., :3] *= out[..., 3:4]
    return out


def unpremul(p):
    a = p[..., 3:4]
    out = p.copy()
    out[..., :3] = np.where(a > 1e-4, p[..., :3] / np.maximum(a, 1e-4), 0)
    return out


def blur_rgba(rgba, sigma):
    return unpremul(blur(premul(rgba), sigma))


def glow_of(rgba, sigma, color=None, strength=1.0):
    """Imagem RGB de brilho (para somar) a partir de um RGBA."""
    p = premul(rgba)
    g = blur(p, sigma)
    rgb = g[..., :3] if color is None else g[..., 3:4] * np.asarray(color, np.float32)
    return rgb * strength


def warp_affine(img, M, size=None, border=cv2.BORDER_CONSTANT, interp=cv2.INTER_LINEAR):
    size = size or (W, H)
    return cv2.warpAffine(img, M, size, flags=interp, borderMode=border)


def camera_matrix(scale, cx, cy, ox=None, oy=None, rot=0.0):
    """Mapeia (cx,cy) da imagem-fonte para (ox,oy) do quadro com zoom 'scale'."""
    ox = W / 2 if ox is None else ox
    oy = H / 2 if oy is None else oy
    a = math.radians(rot)
    c, s = math.cos(a) * scale, math.sin(a) * scale
    return np.array([[c, -s, ox - c * cx + s * cy], [s, c, oy - s * cx - c * cy]], np.float32)


# --------------------------------------------------------------------------- 3D
def project_card(w, h, rx=0, ry=0, rz=0, tx=0, ty=0, tz=0, f=None, cx=None, cy=None):
    """Projeta os cantos de um retângulo w x h (centrado na origem) após rotação (graus)
    e translação 3D. Retorna 4 pontos (TL, TR, BR, BL) em pixels do quadro."""
    f = f or 2.2 * W
    cx = W / 2 if cx is None else cx
    cy = H / 2 if cy is None else cy
    pts = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]], np.float64)
    ax, ay, az = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    p = pts @ (Rz @ Ry @ Rx).T + np.array([tx, ty, tz])
    z = f + p[:, 2]
    return np.stack([cx + p[:, 0] * f / z, cy + p[:, 1] * f / z], 1).astype(np.float32)


def place_quad(dst, src_rgba, quad, opacity=1.0, interp=cv2.INTER_LINEAR, shadow=0.0, shadow_blur=60,
               shadow_off=(0, 40)):
    """Desenha src RGBA projetado no quadrilátero 'quad' (TL,TR,BR,BL), com sombra opcional."""
    h, w = src_rgba.shape[:2]
    srcq = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    x0, y0 = np.floor(quad.min(0)).astype(int) - 2
    x1, y1 = np.ceil(quad.max(0)).astype(int) + 2
    pad = int(shadow_blur * 3 * SC) + int(abs(shadow_off[1]) * SC) if shadow > 0 else 0
    bx0, by0 = max(x0 - pad, 0), max(y0 - pad, 0)
    bx1, by1 = min(x1 + pad, W), min(y1 + pad, H)
    if bx1 <= bx0 or by1 <= by0:
        return dst
    M = cv2.getPerspectiveTransform(srcq, (quad - [bx0, by0]).astype(np.float32))
    warped = cv2.warpPerspective(src_rgba, M, (bx1 - bx0, by1 - by0), flags=interp,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    if shadow > 0:
        a = warped[..., 3]
        sh = blur(a, shadow_blur * SC)
        dx, dy = int(shadow_off[0] * SC), int(shadow_off[1] * SC)
        sh = _shift(sh, dx, dy) * shadow * opacity
        dst[by0:by1, bx0:bx1] *= (1 - sh[..., None])
    over(dst, warped, bx0, by0, opacity)
    return dst


def _shift(a, dx, dy):
    """Desloca sem 'dar a volta' na borda (diferente de np.roll)."""
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def rounded_mask(w, h, r, feather=1.0):
    m = np.zeros((h, w), np.uint8)
    r = int(r)
    ss = 4
    big = np.zeros((h * ss, w * ss), np.uint8)
    cv2.rectangle(big, (r * ss, 0), ((w - r) * ss, h * ss), 255, -1)
    cv2.rectangle(big, (0, r * ss), (w * ss, (h - r) * ss), 255, -1)
    for cx, cy in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]:
        cv2.circle(big, (cx * ss, cy * ss), r * ss, 255, -1)
    m = cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return m


def rounded_stroke(w, h, r, thick, progress=1.0):
    """Contorno arredondado (alpha), desenhado progressivamente (0..1) a partir do topo-esq."""
    ss = 3
    big = np.zeros((h * ss, w * ss), np.uint8)
    r = int(r)
    t = max(1, int(thick * ss))
    pts = []
    # caminho ao longo do retângulo arredondado
    def arc(cx, cy, a0, a1):
        return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
                for a in np.linspace(a0, a1, 12)]
    pts += arc(r, r, 180, 270)
    pts += [(w - r, 0)]
    pts += arc(w - r, r, 270, 360)
    pts += [(w, h - r)]
    pts += arc(w - r, h - r, 0, 90)
    pts += [(r, h)]
    pts += arc(r, h - r, 90, 180)
    pts += [(0, r)]
    pts = np.array(pts)
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    L = seg.sum() * clamp01(progress)
    acc = 0
    out = [pts[0]]
    for i, s in enumerate(seg):
        if acc + s <= L:
            out.append(pts[i + 1])
            acc += s
        else:
            k = (L - acc) / s
            out.append(pts[i] + (pts[i + 1] - pts[i]) * k)
            break
    out = (np.array(out) * ss).astype(np.int32)
    inset = t // 2 + 1
    out = np.clip(out, inset, [w * ss - inset, h * ss - inset])
    if len(out) > 1:
        cv2.polylines(big, [out], False, 255, t, cv2.LINE_AA)
    return cv2.resize(big, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


# ---------------------------------------------------------------------------
# Tipografia
FONT_FILES = {
    'serif': ('cormorantgaramond__CormorantGaramond[wght].ttf', 'Weight'),
    'serif_i': ('cormorantgaramond__CormorantGaramond-Italic[wght].ttf', 'Weight'),
    'didone': ('bodonimoda__BodoniModa[opsz,wght].ttf', None),
    'sans': ('montserrat__Montserrat[wght].ttf', 'Weight'),
    'ui': ('inter__Inter[opsz,wght].ttf', None),
}


@lru_cache(maxsize=256)
def font(kind, size, weight=500):
    fn, _ = FONT_FILES[kind]
    f = ImageFont.truetype(os.path.join(FONTS, fn), max(4, int(round(size))))
    axes = f.get_variation_axes()
    vals = []
    for ax in axes:
        nm = ax['name'].decode() if isinstance(ax['name'], bytes) else ax['name']
        if nm.lower().startswith('weight'):
            vals.append(weight)
        elif nm.lower().startswith('optical'):
            vals.append(min(ax['maximum'], max(ax['minimum'], 12 if kind == 'didone' else 32)))
        else:
            vals.append(ax['default'])
    f.set_variation_by_axes(vals)
    return f


@lru_cache(maxsize=64)
def text_rgba(text, kind, size, weight=500, tracking=0.0, color=(1, 1, 1)):
    """Renderiza texto (uma linha) com tracking (em em). Retorna (rgba, baseline_y, advance)."""
    f = font(kind, size, weight)
    asc, desc = f.getmetrics()
    tr = tracking * size
    widths = [f.getlength(ch) for ch in text]
    total = sum(widths) + tr * max(0, len(text) - 1)
    pad = int(size * 0.35)
    wimg = int(math.ceil(total)) + 2 * pad
    himg = asc + desc + 2 * pad
    img = Image.new('L', (max(1, wimg), max(1, himg)), 0)
    d = ImageDraw.Draw(img)
    if tr == 0:
        d.text((pad, pad), text, font=f, fill=255)
    else:
        x = pad
        for ch, wd in zip(text, widths):
            d.text((x, pad), ch, font=f, fill=255)
            x += wd + tr
    a = np.asarray(img, np.float32) / 255
    rgba = np.zeros((himg, wimg, 4), np.float32)
    rgba[..., :3] = np.asarray(color, np.float32)
    rgba[..., 3] = a
    return rgba, pad + asc, total, pad


def text(text, kind, size, weight=500, tracking=0.0, color=OFFW):
    """Atalho: retorna (rgba, info) com size já em pixels do quadro (aplica SC)."""
    s = max(4, int(round(size * SC)))
    rgba, base, adv, pad = text_rgba(text, kind, s, weight, round(tracking, 3), tuple(np.round(color, 3)))
    return rgba, dict(base=base, adv=adv, pad=pad, size=s)


def gradient_fill(rgba, top, bottom, mid=None):
    """Aplica gradiente vertical (metálico) à cor do texto."""
    h = rgba.shape[0]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top, bottom = np.asarray(top, np.float32), np.asarray(bottom, np.float32)
    if mid is None:
        col = top * (1 - y) + bottom * y
    else:
        mid = np.asarray(mid, np.float32)
        col = np.where(y < 0.5, top * (1 - 2 * y) + mid * 2 * y, mid * (2 - 2 * y) + bottom * (2 * y - 1))
    out = rgba.copy()
    out[..., :3] = col
    return out


def place_text(dst, rgba, info, x, y, anchor='lb', opacity=1.0, glow=0.0, glow_sigma=24, glow_color=None,
               blur_px=0.0, scale=1.0):
    """Posiciona texto. anchor: l/c/r + b(aseline)/m(eio)/t(opo)."""
    img = rgba
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR if scale > 1 else cv2.INTER_AREA)
    k = scale
    pad, base, adv = info['pad'] * k, info['base'] * k, info['adv'] * k
    if anchor[0] == 'l':
        ox = x - pad
    elif anchor[0] == 'c':
        ox = x - pad - adv / 2
    else:
        ox = x - pad - adv
    if anchor[1] == 'b':
        oy = y - base
    elif anchor[1] == 'm':
        oy = y - (base - info['size'] * k * 0.36)
    else:
        oy = y - (base - info['size'] * k * 0.72)
    if blur_px > 0.3:
        img = blur_rgba(img, blur_px)
    if glow > 0:
        add(dst, glow_of(img, glow_sigma * SC, glow_color, glow), ox, oy, opacity)
    over(dst, img, ox, oy, opacity)
    return ox, oy, img.shape[1], img.shape[0]


def wipe_mask(h, w, progress, direction='up', soft=0.15):
    """Máscara de revelação (0..1). direction: up (de baixo p/ cima), right, center."""
    if direction in ('up', 'down'):
        v = np.linspace(1, 0, h, dtype=np.float32) if direction == 'up' else np.linspace(0, 1, h, dtype=np.float32)
        m = np.clip((progress * (1 + soft) - v) / soft, 0, 1)[:, None]
        return np.repeat(m, w, 1)
    if direction == 'right':
        v = np.linspace(0, 1, w, dtype=np.float32)
        m = np.clip((progress * (1 + soft) - v) / soft, 0, 1)[None, :]
        return np.repeat(m, h, 0)
    if direction == 'center':
        v = np.abs(np.linspace(-1, 1, w, dtype=np.float32))
        m = np.clip((progress * (1 + soft) - v) / soft, 0, 1)[None, :]
        return np.repeat(m, h, 0)
    raise ValueError(direction)


def masked(rgba, mask):
    out = rgba.copy()
    out[..., 3] *= mask
    return out


# ---------------------------------------------------------------------------
# Luz e atmosfera
@lru_cache(maxsize=8)
def vignette_map(strength=0.55, roundness=1.0):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (x / W - 0.5) * 2, (y / H - 0.5) * 2 * roundness
    r = np.sqrt(nx ** 2 * 0.85 + ny ** 2)
    v = 1 - strength * np.clip((r - 0.45) / 1.0, 0, 1) ** 1.6
    return v[..., None].astype(np.float32)


def vignette(img, strength=0.55):
    return img * vignette_map(round(strength, 2))


@lru_cache(maxsize=4)
def _grain_bank(n=6):
    rng = np.random.default_rng(5)
    out = []
    for _ in range(n):
        g = rng.standard_normal((H, W)).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), max(0.55, 0.9 * SC * 2))
        g /= g.std() + 1e-6
        out.append(g)
    return out


def grain(img, frame_idx, amount=0.022):
    g = _grain_bank()[frame_idx % 6]
    lum = img.mean(2, keepdims=True)
    w = (0.35 + 0.65 * np.clip(1 - np.abs(lum - 0.45) * 1.6, 0, 1))
    return img + g[..., None] * amount * w


def radial(cx, cy, rx, ry, color, power=2.0):
    """Mancha de luz radial (RGB) em tela cheia, coordenadas de quadro (calculada em 1/8 e ampliada)."""
    k = 8
    sw, sh = max(2, W // k), max(2, H // k)
    y, x = np.ogrid[0:sh, 0:sw]
    d = ((x * k - cx) / rx) ** 2 + ((y * k - cy) / ry) ** 2
    m = np.exp(-d * power).astype(np.float32)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    return m[..., None] * np.asarray(color, np.float32)


@lru_cache(maxsize=32)
def _streak_profile(h_sigma, length_sigma):
    pass


def light_line(img, y, x0, x1, intensity=1.0, thick=2.0, color=CHAMP_L, glow=1.0, flare=1.0):
    """Linha de luz horizontal com brilho e flare anamórfico (motivo visual do 'nível')."""
    if intensity <= 0.002 or x1 <= x0:
        return img
    ys = int(max(0, y - px(300)))
    ye = int(min(H, y + px(300)))
    if ye <= ys:
        return img
    yy = np.arange(ys, ye, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    span = np.clip(np.minimum(xx - x0, x1 - xx) / px(60), 0, 1)
    core = np.exp(-((yy - y) / max(px(thick), 0.6)) ** 2) * span
    g1 = np.exp(-((yy - y) / px(14)) ** 2) * span * 0.55 * glow
    cxm = (x0 + x1) / 2
    flare_x = np.exp(-((xx - cxm) / max(1.0, (x1 - x0) * 0.6)) ** 2)
    g2 = np.exp(-((yy - y) / px(70)) ** 2) * flare_x * 0.22 * flare
    val = (core * 1.2 + g1 + g2)[..., None] * np.asarray(color, np.float32) * intensity
    img[ys:ye] += val
    return img


class Particles:
    """Poeira/partículas atmosféricas 3D com profundidade de campo simulada."""

    def __init__(self, n=220, seed=1, depth=(0.6, 6.0), size=(2.0, 7.0), color=CHAMP_L, drift=(0.0, -12.0)):
        rng = np.random.default_rng(seed)
        self.p = np.stack([rng.uniform(-1.4, 1.4, n), rng.uniform(-1.0, 1.0, n), rng.uniform(*depth, n)], 1)
        self.size = rng.uniform(*size, n)
        self.phase = rng.uniform(0, 6.28, n)
        self.bright = rng.uniform(0.25, 1.0, n)
        self.color = np.asarray(color, np.float32)
        self.drift = drift

    def render(self, img, t, cam_z=0.0, cam_x=0.0, cam_y=0.0, focus=2.0, amount=1.0, speed=1.0):
        if amount <= 0.01:
            return img
        P = self.p.copy()
        P[:, 0] += np.sin(t * 0.21 * speed + self.phase) * 0.03 + self.drift[0] * 0.001 * t
        P[:, 1] += np.cos(t * 0.17 * speed + self.phase) * 0.03 + self.drift[1] * 0.001 * t * speed
        P[:, 1] = (P[:, 1] + 1.2) % 2.4 - 1.2
        z = P[:, 2] - cam_z
        ok = z > 0.15
        sx = W / 2 + (P[:, 0] - cam_x) / z * W * 0.5
        sy = H / 2 + (P[:, 1] - cam_y) / z * W * 0.5
        for i in np.where(ok)[0]:
            if not (-50 < sx[i] < W + 50 and -50 < sy[i] < H + 50):
                continue
            coc = abs(1 / z[i] - 1 / focus) * 26 + 1
            r = self.size[i] * SC * coc / max(z[i], 0.3) * 1.2
            r = max(r, 0.8)
            a = self.bright[i] * amount * min(1.0, 3.0 / coc) * (0.6 + 0.4 * math.sin(t * 1.3 + self.phase[i]))
            spr = _sprite(int(min(r, 120)))
            s = spr.shape[0]
            add(img, spr[..., None] * self.color, sx[i] - s / 2, sy[i] - s / 2, a * 0.5)
        return img


@lru_cache(maxsize=256)
def _sprite(r):
    r = max(1, r)
    s = 2 * r * 2 + 1
    y, x = np.mgrid[0:s, 0:s].astype(np.float32) - s // 2
    d = np.sqrt(x * x + y * y) / r
    return np.clip(np.exp(-d ** 2 * 1.6) * 1.2 - 0.02, 0, 1).astype(np.float32)


def beams(t, origin=(0.18, -0.15), n=5, color=CHAMP, intensity=0.12, spread=0.55, seed=2, length=1.6):
    """Feixes volumétricos suaves (RGB tela cheia, renderizados em baixa resolução)."""
    rng = np.random.default_rng(seed)
    sw, sh = W // 8, H // 8
    out = np.zeros((sh, sw), np.float32)
    ox, oy = origin[0] * sw, origin[1] * sh
    for k in range(n):
        ang = math.radians(35 + rng.uniform(-1, 1) * spread * 40 + math.sin(t * 0.15 + k) * 2.5)
        wdt = rng.uniform(0.04, 0.12)
        L = length * sw
        a1 = ang - wdt / 2
        a2 = ang + wdt / 2
        poly = np.array([[ox, oy], [ox + L * math.cos(a1), oy + L * math.sin(a1)],
                         [ox + L * math.cos(a2), oy + L * math.sin(a2)]], np.int32)
        layer = np.zeros_like(out)
        cv2.fillPoly(layer, [poly], rng.uniform(0.4, 1.0) * (0.75 + 0.25 * math.sin(t * 0.4 + k * 1.7)))
        out += layer
    out = cv2.GaussianBlur(out, (0, 0), 6)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    fall = np.exp(-np.sqrt((xx - ox) ** 2 + (yy - oy) ** 2) / (sw * 0.7))
    out *= fall
    big = cv2.resize(out, (W, H), interpolation=cv2.INTER_CUBIC)
    return big[..., None] * np.asarray(color, np.float32) * intensity


def light_leak(t, seed=0, intensity=0.25, colors=(CHAMP, hexc('D98E4A'), hexc('F6E7C8'))):
    """Vazamento de luz orgânico (RGB) — blobs grandes em movimento, baixa resolução."""
    rng = np.random.default_rng(seed)
    sw, sh = W // 10, H // 10
    out = np.zeros((sh, sw, 3), np.float32)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    for k in range(4):
        c = colors[k % len(colors)]
        cx = (rng.uniform(-0.2, 1.2) + 0.25 * math.sin(t * rng.uniform(0.3, 0.8) + k)) * sw
        cy = (rng.uniform(-0.1, 1.1) + 0.2 * math.cos(t * rng.uniform(0.3, 0.7) + k)) * sh
        r = rng.uniform(0.25, 0.6) * sw
        out += np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r))[..., None] * c * rng.uniform(0.5, 1.0)
    big = cv2.resize(out, (W, H), interpolation=cv2.INTER_CUBIC)
    return big * intensity


def frosted(dst, x, y, w, h, sigma=40, tint=(0.06, 0.055, 0.05), tint_a=0.55, radius=40, opacity=1.0):
    """Painel de vidro fosco: desfoca o que está atrás, aplica tom escuro e borda arredondada."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0 or opacity <= 0.01:
        return dst
    region = dst[y0:y1, x0:x1]
    b = blur(region, sigma * SC)
    m = rounded_mask(w, h, radius * SC)[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * opacity
    col = b * (1 - tint_a) + np.asarray(tint, np.float32) * tint_a
    dst[y0:y1, x0:x1] = region * (1 - m) + col * m
    return dst


def col(c, a=1.0):
    """Cor numpy -> tupla de floats (para funções de desenho do OpenCV)."""
    return tuple(float(v) * float(a) for v in c)
