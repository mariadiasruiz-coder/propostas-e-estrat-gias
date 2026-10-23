"""Cenas 01–03: a pergunta, o outro caminho (motion graphics), autoridade."""
import math
from functools import lru_cache
import numpy as np
import cv2
import fx
from fx import (px, ease_out, ease_in, ease_io, ease_io5, back_out, lin, keys, mix, CHAMP, CHAMP_L, GOLD, OFFW,
                BEIGE, BLACK, GRAPHITE)
import sources
from common import duda_layers, comp, glass_card, flash, name_tag
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timeline import EV

OFF1 = 0.52   # S = T - OFF1 (cena 01)
OFF3 = 0.82   # cena 03
DUST = fx.Particles(260, seed=3, depth=(0.7, 7.0), size=(1.5, 5.0))


# =========================================================================== CENA 01
def scene01(T):
    img = fx.canvas(BLACK)
    # 0.15–0.60: a linha de luz nasce no centro
    line_y = fx.H * 0.5
    if T < 0.6:
        g = ease_out(lin(T, EV['open_line'], 0.58), 2)
        half = fx.W * 0.5 * g
        fx.light_line(img, line_y, fx.W / 2 - half, fx.W / 2 + half, 0.9 * g + 0.1, thick=1.6)
        return img, dict(vig=0.3)
    S = T - OFF1
    zoom = keys(T, [(0.6, 1.06), (5.1, 1.15)], ease=lambda x: x)
    dxs = keys(T, [(0.6, 0), (2.6, 0), (3.3, 300), (5.1, 330)])
    bg, fg, m, eye = duda_layers(S, zoom=zoom, dx=dxs, eye_y=0.38, bg_dim=0.52, bg_blur=5, halo=0.09)
    frame = bg.copy()
    # "UMA DECISÃO" — tipografia flutuante atrás da Duda (composição em profundidade)
    uma_t, dec_t = EV['uma'], EV['decisao']
    exit_a = 1 - ease_in(lin(T, 4.70, 5.05))
    if T >= uma_t - 0.05 and exit_a > 0:
        xL = 190
        yb = 1220
        a1 = ease_out(lin(T, uma_t, uma_t + 0.5)) * exit_a
        tr1 = mix(0.9, 0.55, ease_out(lin(T, uma_t, uma_t + 1.4)))
        u, ui = fx.text('UMA', 'sans', 58, 500, tr1, CHAMP)
        fx.place_text(frame, u, ui, px(xL + 6), px(yb - 250), 'lb', a1)
        prog = ease_out(lin(T, dec_t, dec_t + 0.55), 3)
        if prog > 0:
            tr = mix(0.30, 0.10, ease_out(lin(T, dec_t, dec_t + 1.6)))
            d, di = fx.text('DECISÃO', 'serif', 215, 560, tr, OFFW)
            d = fx.gradient_fill(d, CHAMP_L, GOLD, CHAMP)
            msk = fx.wipe_mask(d.shape[0], d.shape[1], prog, 'up', 0.25)
            dd = fx.masked(d, msk)
            bl = (1 - ease_out(lin(T, dec_t, dec_t + 0.45))) * 8
            sc = mix(1.06, 1.0, ease_out(lin(T, dec_t, dec_t + 1.4)))
            fx.place_text(frame, dd, di, px(xL), px(yb), 'lb', exit_a, glow=0.35, glow_sigma=30,
                          glow_color=CHAMP, blur_px=bl * fx.SC, scale=sc)
            # fio de luz sob a palavra
            Lw = px(1020) * ease_out(lin(T, dec_t + 0.15, dec_t + 1.0))
            if Lw > 1:
                fx.light_line(frame, px(yb + 60), px(xL), px(xL) + Lw, 0.6 * exit_a, thick=1.2, glow=0.5, flare=0.3)
    frame = comp(frame, fg, m)
    # revelação: a linha se abre como uma fenda (0.60–1.40)
    op = ease_io5(lin(T, 0.60, 1.45))
    if op < 1:
        yy = np.abs(np.arange(fx.H, dtype=np.float32) - line_y)[:, None, None]
        half = op * fx.H * 0.62
        msk = np.clip((half - yy) / px(90) + 0.5, 0, 1)
        frame = frame * msk
        fx.light_line(frame, line_y - half, 0, fx.W, (1 - op) * 0.9, thick=1.4, glow=0.6)
        fx.light_line(frame, line_y + half, 0, fx.W, (1 - op) * 0.9, thick=1.4, glow=0.6)
    # exposição respirando a partir do escuro
    frame *= mix(0.55, 1.0, ease_out(lin(T, 0.6, 2.2)))
    frame = flash(frame, 0.10 * (1 - ease_out(lin(T, 0.6, 1.0))))
    # transição: rastro de luz atravessa e fecha em preto (4.92–5.29)
    if T > EV['q_end'] - 0.1:
        k = lin(T, EV['q_end'] - 0.1, 5.29)
        frame *= 1 - ease_in(k, 2)
        x = mix(-0.3, 1.3, ease_io(k)) * fx.W
        fx.light_line(frame, line_y, x - px(1600), x + px(400), 0.9 * math.sin(math.pi * k), thick=1.8)
    return frame, dict(vig=0.55)


# =========================================================================== CENA 02
@lru_cache(maxsize=1)
def _tiles():
    """Miniaturas 9:16 de conteúdo real (Duda e mentoradas), dessaturadas, em 3 níveis de foco."""
    rng = np.random.default_rng(4)
    thumbs = []
    srcs = [('duda', s) for s in (2.0, 17.0, 21.0, 67.0, 70.0, 75.5, 80.0)] + \
           [('lais', s) for s in (29.0, 33.0, 37.0)] + [('fern', s) for s in (53.0, 56.0, 58.0)]
    tw, th = int(px(300)), int(px(533))
    for kind, S in srcs:
        if kind == 'duda':
            img, k = sources.duda(S)
            fxp, fyp, _ = sources.face(S)
            cw = int(img.shape[0] * 9 / 16)
            x0 = int(min(max(fxp * k - cw / 2, 0), img.shape[1] - cw))
            crop = img[:, x0:x0 + cw]
        else:
            crop, _ = sources.clip(kind, S)
        t = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_AREA)
        lum = t.mean(2, keepdims=True)
        t = (t * 0.45 + lum * 0.55) * 0.75
        a = fx.rounded_mask(tw, th, px(22))
        rgba = np.dstack([t, a]).astype(np.float32)
        thumbs.append([rgba, fx.blur_rgba(rgba, px(6)), fx.blur_rgba(rgba, px(16))])
    n = 46
    P = np.stack([rng.uniform(-2.2, 2.2, n), rng.uniform(-1.2, 1.2, n), rng.uniform(1.6, 9.0, n)], 1)
    return thumbs, P, rng.integers(0, len(thumbs), n), rng.uniform(0, 6.28, n)


@lru_cache(maxsize=1)
def _dots():
    rng = np.random.default_rng(8)
    n = 520
    P = np.stack([rng.uniform(-2.4, 2.4, n), rng.uniform(-1.3, 1.3, n), rng.uniform(1.4, 9.0, n)], 1)
    birth = 5.45 + np.sort(rng.uniform(0, 1, n)) ** 0.6 * 2.6
    return P, birth, rng.uniform(0.4, 1.0, n), rng.normal(0, 1, (n, 3))


def _proj(P, cam):
    cx, cy, cz, f = cam
    z = P[:, 2] - cz
    sx = fx.W / 2 + (P[:, 0] - cx) / np.maximum(z, 1e-3) * f
    sy = fx.H / 2 + (P[:, 1] - cy) / np.maximum(z, 1e-3) * f
    return sx, sy, z


def _path_pts():
    u = np.linspace(0, 1, 400)
    x = -1.9 + 2.3 * u + 0.35 * np.sin(u * math.pi * 1.2)
    y = 0.95 - 1.0 * u ** 0.8
    z = 1.25 + 8.5 * u ** 1.35
    return np.stack([x, y, z], 1), u


def _phone_rgba(T):
    """Smartphone premium com o conteúdo real da Duda na tela (interface de gravação)."""
    pw, ph = int(px(860)), int(px(1760))
    r = px(120)
    body = np.zeros((ph, pw, 4), np.float32)
    m = fx.rounded_mask(pw, ph, r)
    g = np.linspace(0.20, 0.07, ph, dtype=np.float32)[:, None, None]
    body[..., :3] = g * np.array([1.0, 0.96, 0.9], np.float32)
    body[..., 3] = m
    st = fx.rounded_stroke(pw, ph, r, max(1.5, px(7)))
    body[..., :3] += st[..., None] * CHAMP * 0.8
    # tela
    inset = int(px(34))
    sw_, sh_ = pw - 2 * inset, ph - 2 * inset
    S = 66.0 + (T - 13.0)
    img, k = sources.duda(S)
    fxp, fyp, _ = sources.face(S)
    ch = img.shape[0]
    cw = int(ch * sw_ / sh_)
    x0 = int(min(max(fxp * k - cw / 2, 0), img.shape[1] - cw))
    scr = cv2.resize(img[:, x0:x0 + cw], (sw_, sh_), interpolation=cv2.INTER_AREA)
    # interface discreta de gravação (sem métricas inventadas)
    if int(T * 2) % 2 == 0:
        cv2.circle(scr, (int(px(70)), int(px(90))), max(2, int(px(16))), (0.86, 0.18, 0.15), -1, cv2.LINE_AA)
    rec, ri = fx.text('REC', 'ui', 34, 600, 0.12, OFFW)
    tc, ti = fx.text('00:%02d' % (int(T * 1.0) % 60), 'ui', 34, 500, 0.06, OFFW)
    fx.place_text(scr, rec, ri, px(100), px(104), 'lb', 0.9)
    fx.place_text(scr, tc, ti, sw_ - px(50), px(104), 'rb', 0.8)
    grid = np.zeros(scr.shape[:2], np.float32)
    for gx in (1 / 3, 2 / 3):
        cv2.line(grid, (int(sw_ * gx), 0), (int(sw_ * gx), sh_), 1.0, 1, cv2.LINE_AA)
    for gy in (1 / 3, 2 / 3):
        cv2.line(grid, (0, int(sh_ * gy)), (sw_, int(sh_ * gy)), 1.0, 1, cv2.LINE_AA)
    scr = scr * (1 - grid[..., None] * 0.22) + grid[..., None] * 0.22
    sm = fx.rounded_mask(sw_, sh_, r - inset)
    # reflexo de vidro
    yy, xx = np.mgrid[0:sh_, 0:sw_].astype(np.float32)
    refl = np.clip(1 - np.abs((xx / sw_ + yy / sh_ * 0.6) - 0.55) * 6, 0, 1) * 0.07
    scr = scr + refl[..., None]
    body[inset:inset + sh_, inset:inset + sw_, :3] = body[inset:inset + sh_, inset:inset + sw_, :3] * (1 - sm[..., None]) + scr * sm[..., None]
    return body


def scene02(T):
    t = T
    img = fx.canvas(BLACK)
    img += fx.radial(fx.W * 0.55, fx.H * 0.45, fx.W * 0.7, fx.H * 0.7, GRAPHITE, 1.0) * 0.55
    img += fx.beams(t, origin=(0.15, -0.2), n=6, intensity=0.10, seed=5)
    # câmera virtual: avanço contínuo; acelera no final (mergulho no celular)
    cz = keys(t, [(5.29, 0.0), (9.7, 1.9), (11.7, 3.0), (14.9, 3.6)], ease=lambda x: x)
    cx = 0.12 * math.sin(t * 0.25)
    cy = 0.04 * math.cos(t * 0.21)
    f = fx.W * 0.5
    fade_in = ease_out(lin(t, 5.29, 6.1))
    # --- campo de conteúdos (fase 1)
    thumbs, P, which, ph = _tiles()
    tiles_a = fade_in * (1 - ease_io(lin(t, 9.4, 11.2))) * (1 - 0.45 * ease_io(lin(t, EV['seguidores'] - 0.4, EV['seguidores'] + 0.2)))
    if tiles_a > 0:
        Q = P.copy()
        Q[:, 1] += 0.05 * np.sin(t * 0.5 + ph)
        sx, sy, z = _proj(Q, (cx, cy, cz, f))
        for i in np.argsort(-z):
            if z[i] < 0.35:
                continue
            s = 1.0 / z[i] * 1.9
            focus = abs(1 / z[i] - 1 / 4.0)
            lvl = 0 if focus < 0.08 else (1 if focus < 0.2 else 2)
            th = thumbs[which[i]][lvl]
            w_, h_ = int(th.shape[1] * s), int(th.shape[0] * s)
            if w_ < 3 or w_ > fx.W * 1.5:
                continue
            tt = cv2.resize(th, (w_, h_), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
            fog = np.clip(1.25 - z[i] / 9.0, 0, 1)
            fx.over(img, tt, sx[i] - w_ / 2, sy[i] - h_ / 2, tiles_a * fog * 0.9)
    # --- constelação de "seguidores"
    DP, birth, br, jit = _dots()
    dots_a = 1 - ease_io(lin(t, EV['strike'] + 0.1, 10.6))
    if dots_a > 0 and t > 5.4:
        Q = DP.copy()
        scatter = ease_in(lin(t, EV['strike'], 10.6), 2)
        Q += jit * scatter * 1.2
        sx, sy, z = _proj(Q, (cx, cy, cz, f))
        alive = np.clip((t - birth) / 0.25, 0, 1)
        for i in np.where(alive > 0)[0]:
            if z[i] < 0.3 or not (0 <= sx[i] < fx.W and 0 <= sy[i] < fx.H):
                continue
            rr = max(1, int(px(10) / z[i] * 2.2))
            spr = fx._sprite(min(rr, 40))
            fx.add(img, spr[..., None] * CHAMP_L, sx[i] - spr.shape[1] / 2, sy[i] - spr.shape[0] / 2,
                   br[i] * alive[i] * dots_a * 0.55)
    DUST.render(img, t, cam_z=cz * 0.3, amount=fade_in * 0.8)
    # --- tipografia: NÃO É SOBRE / SEGUIDORES (riscado)
    s_t = EV['seguidores']
    ex = 1 - ease_in(lin(t, 9.55, 9.95))
    if t > s_t - 0.3 and ex > 0:
        scrim = fx.radial(fx.W / 2, px(1020), px(1700), px(420), (1, 1, 1), 1.6)[..., :1]
        img *= 1 - 0.75 * scrim * ease_out(lin(t, s_t - 0.3, s_t + 0.2)) * ex
        a0 = ease_out(lin(t, s_t - 0.25, s_t + 0.2)) * ex
        n1, n1i = fx.text('NÃO É SOBRE', 'sans', 56, 500, mix(0.8, 0.5, ease_out(lin(t, s_t - 0.25, s_t + 1))), CHAMP)
        fx.place_text(img, n1, n1i, fx.W / 2, px(860), 'cb', a0)
        pr = ease_out(lin(t, s_t, s_t + 0.45))
        sg, sgi = fx.text('SEGUIDORES', 'serif', 230, 520, mix(0.22, 0.10, ease_out(lin(t, s_t, s_t + 1.4))), OFFW)
        dim = 1 - 0.55 * ease_out(lin(t, EV['strike'], EV['strike'] + 0.5))
        sgm = fx.masked(sg, fx.wipe_mask(sg.shape[0], sg.shape[1], pr, 'up', 0.3))
        x0, y0, w0, h0 = fx.place_text(img, sgm, sgi, fx.W / 2, px(1120), 'cb', ex * dim,
                                       blur_px=(1 - pr) * px(10) + (1 - dim) * px(5))
        # risco dourado com brilho
        sp = ease_io(lin(t, EV['strike'], EV['strike'] + 0.35))
        if sp > 0:
            xl = fx.W / 2 - sgi['adv'] / 2 - px(30)
            xr = xl + (sgi['adv'] + px(60)) * sp
            fx.light_line(img, px(1050), xl, xr, 0.95 * ex, thick=2.2, color=CHAMP_L, glow=0.8, flare=0.5)
    # --- o outro caminho: linha dourada em perspectiva
    pts, u = _path_pts()
    path_a = ease_out(lin(t, 9.8, 10.2)) * (1 - 0.7 * ease_io(lin(t, 12.4, 13.4))) * (1 - ease_in(lin(t, 14.9, 15.6)))
    head = ease_io(lin(t, 9.9, 11.75))
    if path_a > 0 and head > 0:
        sx, sy, z = _proj(pts, (cx, cy, cz, f))
        keep = (u <= head) & (z > 0.2)
        if keep.sum() > 2:
            layer = np.zeros((fx.H, fx.W), np.float32)
            xy = np.stack([sx[keep], sy[keep]], 1)
            zz = z[keep]
            for k in range(len(xy) - 1):
                th = max(1, int(px(12) / zz[k] * 1.8))
                cv2.line(layer, tuple(np.int32(xy[k])), tuple(np.int32(xy[k + 1])), 1.0, th, cv2.LINE_AA)
            glow = fx.blur(layer, px(18))
            glow2 = fx.blur(layer, px(60))
            img += (layer[..., None] * CHAMP_L * 1.0 + glow[..., None] * CHAMP * 2.2 + glow2[..., None] * CHAMP * 2.0) * path_a
            hx, hy = xy[-1]
            spr = fx._sprite(int(px(26)))
            fx.add(img, spr[..., None] * CHAMP_L, hx - spr.shape[1] / 2, hy - spr.shape[0] / 2, 1.6 * path_a * (1 - lin(t, 11.75, 12.4)))
    # --- É SOBRE ESTRATÉGIA (impacto) -> vira cabeçalho
    e_t = EV['estrategia']
    if t > e_t - 0.05:
        a = ease_out(lin(t, e_t, e_t + 0.3)) * (1 - ease_in(lin(t, 14.95, 15.4)))
        mv = ease_io(lin(t, 13.2, 13.9))
        scale = mix(1.0, 0.42, mv)
        X = mix(fx.W / 2, px(250), mv)
        Y = mix(px(1150), px(470), mv)
        anchor = 'cb' if mv < 0.5 else 'lb'
        if mv >= 0.5:
            X = mix(fx.W / 2 - px(1560) * 0.42, px(250), (mv - 0.5) * 2)
        open_ = ease_out(lin(t, e_t, e_t + 0.55), 4)
        es, esi = fx.text('ESTRATÉGIA', 'serif', 250, 560, mix(0.25, 0.12, ease_out(lin(t, e_t, e_t + 1.5))), OFFW)
        es = fx.gradient_fill(es, CHAMP_L, GOLD, CHAMP)
        es = fx.masked(es, fx.wipe_mask(es.shape[0], es.shape[1], open_, 'center', 0.2))
        so, soi = fx.text('É SOBRE', 'sans', 56, 500, 0.5, CHAMP)
        if anchor == 'cb':
            fx.place_text(img, so, soi, X, Y - px(270) * scale, 'cb', a * open_, scale=scale)
            fx.place_text(img, es, esi, X, Y, 'cb', a, glow=0.5 * (1 - mv), glow_sigma=40, glow_color=CHAMP, scale=scale)
        else:
            fx.place_text(img, so, soi, X, Y - px(270) * scale, 'lb', a, scale=max(scale, 0.6))
            fx.place_text(img, es, esi, X, Y, 'lb', a, scale=scale)
        if t < e_t + 0.6:
            fx.light_line(img, Y - px(90) * scale, fx.W / 2 - fx.W * 0.5 * open_, fx.W / 2 + fx.W * 0.5 * open_,
                          0.8 * (1 - lin(t, e_t + 0.2, e_t + 0.6)), thick=1.5)
    # --- celular + fluxo CONTEÚDO -> MARCAS -> CONTRATOS
    if t > 13.0:
        ent = ease_out(lin(t, 13.15, 13.95), 3)
        dive = ease_in(lin(t, 14.85, 15.97), 2.4)
        ry = mix(-38, -14, ent) * (1 - dive)
        tx = mix(fx.W * 0.75, fx.W * 0.16, ent) * (1 - dive)
        tz = mix(900 * fx.SC * 4, 0, ent) - dive * fx.W * 0.84
        ty = px(30) * (1 - dive)
        ph_rgba = _phone_rgba(t)
        q = fx.project_card(ph_rgba.shape[1], ph_rgba.shape[0], rx=2 * (1 - dive), ry=ry, rz=-2 * (1 - dive),
                            tx=tx, ty=ty, tz=tz)
        fx.place_quad(img, ph_rgba, q, opacity=ent, shadow=0.6 * (1 - dive), shadow_blur=80, shadow_off=(-40, 60))
        # chips
        labels = ['CONTEÚDO', 'MARCAS', 'CONTRATOS']
        chip_a = 1 - ease_in(lin(t, 14.85, 15.3))
        for k, (lab, tk) in enumerate(zip(labels, [13.75, 14.05, 14.35])):
            a = ease_out(lin(t, tk, tk + 0.35)) * chip_a
            if a <= 0:
                continue
            y = 820 + k * 260
            xoff = (1 - a) * -60
            glass_card(img, 250 + xoff, y, 760, 170, a, radius=85, tint_a=0.5)
            lb, lbi = fx.text(lab, 'sans', 56, 500, 0.30, OFFW)
            fx.place_text(img, lb, lbi, px(370 + xoff), px(y + 104), 'lb', a)
            nb, nbi = fx.text('0%d' % (k + 1), 'didone', 46, 600, 0.0, CHAMP)
            fx.place_text(img, nb, nbi, px(930 + xoff), px(y + 104), 'rb', a * 0.9)
        # fio conectando as etapas
        cp = ease_io(lin(t, 14.3, 14.7)) * chip_a
        if cp > 0:
            y0, y1 = px(990), px(990 + 520 * cp)
            cv2.line(img, (int(px(300)), int(y0)), (int(px(300)), int(y1)), fx.col(CHAMP, 0.9), max(1, int(px(3))), cv2.LINE_AA)
        img = fx.flash(img, 0) if False else img
        if dive > 0:
            img = flash(img, 0.35 * ease_in(lin(t, 15.75, 15.97), 2))
    img *= fade_in
    return img, dict(vig=0.5)


# =========================================================================== CENA 03
def _count(t, t0, t1, target):
    x = ease_out(lin(t, t0, t1), 3)
    return int(round(target * x))


def _globe(img, cx, cy, r, t, a):
    R = px(r)
    m_ = int(R + px(60))
    ox, oy = int(px(cx)) - m_, int(px(cy)) - m_
    layer = np.zeros((2 * m_, 2 * m_), np.float32)
    cx, cy = (m_ + 0.0) / fx.SC, (m_ + 0.0) / fx.SC
    for k in range(7):
        ang = t * 0.6 + k * math.pi / 7
        rx = abs(math.cos(ang)) * R
        cv2.ellipse(layer, (int(px(cx)), int(px(cy))), (max(1, int(rx)), int(R)), 0, 0, 360, 1.0, max(1, int(px(2))), cv2.LINE_AA)
    for lat in (-0.6, -0.3, 0, 0.3, 0.6):
        yy = px(cy) + lat * R
        rr = math.sqrt(max(0, 1 - lat * lat)) * R
        cv2.ellipse(layer, (int(px(cx)), int(yy)), (int(rr), max(1, int(rr * 0.12))), 0, 0, 360, 1.0, max(1, int(px(2))), cv2.LINE_AA)
    cv2.circle(layer, (int(px(cx)), int(px(cy))), int(R), 1.0, max(1, int(px(3))), cv2.LINE_AA)
    rgb = (layer[..., None] * CHAMP * 0.55 + fx.blur(layer, px(10))[..., None] * CHAMP * 0.5)
    fx.add(img, rgb, ox, oy, a)


def plus(img, x, ycenter, size, a, color=CHAMP_L):
    """Sinal de + geométrico, fino e elegante (x = borda esquerda, em px de quadro)."""
    if a <= 0:
        return
    L = px(size)
    t = max(1.5, px(size * 0.085))
    lay = np.zeros((fx.H, fx.W), np.float32)
    cx = x + L / 2
    cv2.line(lay, (int(x), int(ycenter)), (int(x + L), int(ycenter)), 1.0, int(round(t)), cv2.LINE_AA)
    cv2.line(lay, (int(cx), int(ycenter - L / 2)), (int(cx), int(ycenter + L / 2)), 1.0, int(round(t)), cv2.LINE_AA)
    g = fx.blur(lay, px(18))
    img[:] = img * (1 - lay[..., None] * a) + lay[..., None] * np.asarray(color) * a + g[..., None] * CHAMP * 0.6 * a


def scene03(T):
    S = T - OFF3
    # chegada do mergulho: zoom assenta; depois push lento; foco dramático nos 150 mil
    zoom = keys(T, [(15.97, 1.42), (16.7, 1.16), (24.6, 1.20), (26.2, 1.30), (28.27, 1.36)],
                ease=lambda x: ease_out(x, 2))
    dx = keys(T, [(15.97, 0), (18.4, 0), (19.0, 260), (20.8, 260), (21.3, -260), (24.3, -260), (25.0, 0)])
    big = ease_out(lin(T, EV['n150'] - 0.5, EV['n150'] + 0.1))
    bg, fg, m, eye = duda_layers(S, zoom=zoom, dx=dx, eye_y=0.40, bg_dim=mix(0.5, 0.3, big), bg_blur=6, halo=0.08)
    frame = bg.copy()
    # 450+ MARCAS (lado esquerdo, atrás do ombro)
    n_t, mk_t = EV['n450'], EV['marcas']
    ex = 1 - ease_in(lin(T, 20.55, 21.0))
    if T > n_t - 0.05 and ex > 0:
        v = _count(T, n_t, mk_t, 450)
        land = lin(T, mk_t, mk_t + 0.6)
        sc = mix(1.18, 1.0, ease_out(lin(T, n_t, mk_t), 2)) * (1 + 0.03 * math.sin(math.pi * land) * (land < 1))
        num, numi = fx.text(f'{v}', 'didone', 420, 600, 0.0, OFFW)
        num = fx.gradient_fill(num, CHAMP_L, GOLD, CHAMP_L)
        mb = (1 - ease_out(lin(T, n_t, mk_t))) * px(8)
        nx, ny, nw, nh = fx.place_text(frame, num, numi, px(260 - (1 - ex) * 120), px(1180), 'lb', ex * ease_out(lin(T, n_t, n_t + 0.2)),
                      glow=0.25 + 0.6 * (1 - ease_out(land)), glow_sigma=40, glow_color=CHAMP, blur_px=mb, scale=sc)
        plus(frame, nx + (numi['pad'] + numi['adv']) * sc + px(20), px(1180) - px(150) * sc, 120 * sc,
             ex * ease_out(lin(T, n_t, n_t + 0.2)))
        la = ease_out(lin(T, mk_t, mk_t + 0.5)) * ex
        lb, lbi = fx.text('MARCAS', 'serif', 150, 560, mix(0.6, 0.28, ease_out(lin(T, mk_t, mk_t + 1.5))), OFFW)
        lb = fx.masked(lb, fx.wipe_mask(lb.shape[0], lb.shape[1], la, 'up', 0.3))
        fx.place_text(frame, lb, lbi, px(270), px(1400), 'lb', ex)
        sb, sbi = fx.text('EM 3 ANOS DE PROFISSÃO', 'sans', 40, 500, 0.4, CHAMP)
        fx.place_text(frame, sb, sbi, px(280), px(1500), 'lb', ease_out(lin(T, mk_t + 0.3, mk_t + 0.9)) * ex)
    frame = comp(frame, fg, m)
    # 3 ANOS DE PROFISSÃO — rótulo discreto
    t3 = EV['tres_anos']
    a3 = ease_out(lin(T, t3, t3 + 0.5)) * (1 - ease_in(lin(T, 18.1, 18.5)))
    if a3 > 0:
        L = px(140) * ease_out(lin(T, t3, t3 + 0.6))
        cv2.line(frame, (int(px(250)), int(px(520))), (int(px(250) + L), int(px(520))), fx.col(CHAMP, a3), max(1, int(px(3))), cv2.LINE_AA)
        tl, tli = fx.text('3 ANOS DE PROFISSÃO', 'sans', 64, 500, 0.38, OFFW)
        fx.place_text(frame, tl, tli, px(250 + 175 - (1 - a3) * 40), px(542), 'lb', a3, glow=0.2, glow_color=CHAMP)
    # CONTRATOS EM DÓLAR — card de vidro entra pela direita
    c_t = EV['contratos']
    ca = ease_out(lin(T, c_t - 0.18, c_t + 0.4), 3) * (1 - ease_in(lin(T, 24.2, 24.7)))
    if ca > 0:
        slide = (1 - ease_out(lin(T, c_t - 0.18, c_t + 0.42), 3)) * 900 + ease_in(lin(T, 24.2, 24.7)) * 900
        X = 2330 + slide
        glass_card(frame, X, 560, 1260, 900, ca, radius=40)
        _globe(frame, X + 300, 1010, 190, T, ca * 0.9)
        us, usi = fx.text('US$', 'didone', 120, 600, 0.0, CHAMP_L)
        fx.place_text(frame, us, usi, px(X + 300), px(1052), 'cb', ca, glow=0.3, glow_color=CHAMP)
        t1, t1i = fx.text('CONTRATOS', 'serif', 118, 600, 0.12, OFFW)
        t2, t2i = fx.text('EM DÓLAR', 'serif', 118, 600, 0.12, OFFW)
        t2 = fx.gradient_fill(t2, CHAMP_L, GOLD)
        fx.place_text(frame, t1, t1i, px(X + 560), px(980), 'lb', ca)
        fx.place_text(frame, t2, t2i, px(X + 560), px(1110), 'lb', ca)
        sb, sbi = fx.text('PARCERIAS INTERNACIONAIS', 'sans', 34, 500, 0.38, CHAMP)
        fx.place_text(frame, sb, sbi, px(X + 566), px(1215), 'lb', ca * ease_out(lin(T, c_t + 0.3, c_t + 0.8)))
    # US$ 150 MIL+ — o grande número
    b_t = EV['n150']
    st = b_t - 0.47
    if T > st:
        frame = fx.blur(frame, px(16) * big) * (1 - 0.5 * big) if big > 0.02 else frame
        v = _count(T, st, b_t, 150)
        land = lin(T, b_t, b_t + 0.7)
        sc = mix(1.25, 1.0, ease_out(lin(T, st, b_t), 2)) * mix(1.0, 1.05, lin(T, b_t, 28.27))
        a = ease_out(lin(T, st, st + 0.15)) * (1 - ease_in(lin(T, 28.0, 28.3)))
        num, numi = fx.text(f'US$ {v} MIL', 'didone', 330, 600, 0.02, OFFW)
        num = fx.gradient_fill(num, CHAMP_L, GOLD, CHAMP_L)
        # brilho metálico atravessando o número após o impacto
        sweep = lin(T, b_t + 0.25, b_t + 1.1)
        if 0 < sweep < 1:
            xx = np.linspace(0, 1, num.shape[1], dtype=np.float32)[None, :]
            yy = np.linspace(0, 1, num.shape[0], dtype=np.float32)[:, None]
            band = np.exp(-(((xx + yy * 0.25) - mix(-0.2, 1.3, sweep)) / 0.06) ** 2)
            num = num.copy()
            num[..., :3] = np.clip(num[..., :3] + band[..., None] * 0.5, 0, 1.2)
        fx.light_line(frame, px(1000), 0, fx.W, 0.75 * (1 - ease_out(land)) * a, thick=2.0, glow=1.0, flare=1.2)
        nx, ny, nw, nh = fx.place_text(frame, num, numi, fx.W / 2 - px(60) * sc, px(1180), 'cb', a,
                                       glow=0.3 + 0.9 * (1 - ease_out(land)), glow_sigma=50, glow_color=CHAMP,
                                       blur_px=(1 - ease_out(lin(T, st, b_t))) * px(10), scale=sc)
        plus(frame, nx + (numi['pad'] + numi['adv']) * sc + px(30), px(1180) - px(120) * sc, 100 * sc, a)
        la = ease_out(lin(T, b_t + 0.25, b_t + 0.9)) * a
        sb, sbi = fx.text('FATURAMENTO DA OPERAÇÃO · ÚLTIMOS 6 MESES', 'sans', 46, 500, 0.36, CHAMP_L)
        sb = fx.masked(sb, fx.wipe_mask(sb.shape[0], sb.shape[1], la, 'center', 0.2))
        fx.place_text(frame, sb, sbi, fx.W / 2, px(1340), 'cb', a)
        frame = flash(frame, 0.22 * (1 - ease_out(lin(T, b_t, b_t + 0.45))) * (T >= b_t))
    # entrada (mergulho) e saída (vazamento de luz para a Laís)
    if T < 16.3:
        frame = flash(frame, 0.45 * (1 - ease_out(lin(T, 15.97, 16.3))))
    if T > 27.85:
        k = lin(T, 27.85, 28.27)
        frame = frame * (1 - 0.5 * k) + fx.light_leak(T, 3, 0.55 * math.sin(math.pi * k))
    return frame, dict(vig=0.55)
