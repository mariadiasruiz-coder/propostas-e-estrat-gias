"""Acesso às fontes reais (quadros 4K tratados, matte, prints) com cache."""
import os, json
from functools import lru_cache
import numpy as np
import cv2
import fx

EXT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'ext')
FACE = {int(k): v for k, v in json.load(open(os.path.join(EXT, 'face.json'))).items()}
SRC_W, SRC_H = 3840, 2160


def _idx(S):
    return int(round(S * 30))


@lru_cache(maxsize=6)
def _load(folder, n, scale):
    p = os.path.join(EXT, folder, f'{n:05d}.jpg')
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(p)
    if scale != 1.0:
        im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return (im[:, :, ::-1].astype(np.float32) / 255)


def _nearest(folder, n):
    p = os.path.join(EXT, folder, f'{n:05d}.jpg')
    if os.path.exists(p):
        return n
    for d in range(1, 40):
        for c in (n - d, n + d):
            if os.path.exists(os.path.join(EXT, folder, f'{c:05d}.jpg')):
                return c
    raise FileNotFoundError((folder, n))


def src_scale():
    """Fator para carregar fontes já reduzidas em prévias (economia de memória/tempo)."""
    return min(1.0, max(fx.SC * 1.6, 0.25))


def duda(S):
    n = _nearest('duda', _idx(S))
    k = src_scale()
    img = _load('duda', n, round(k, 3))
    return img, k


@lru_cache(maxsize=12)
def _matte(n, k):
    m = cv2.imread(os.path.join(EXT, 'matte', f'{n:05d}.png'), 0)
    m = cv2.resize(m, (int(SRC_W * k), int(SRC_H * k)), interpolation=cv2.INTER_LINEAR)
    return m.astype(np.float32) / 255


def duda_matte(S):
    n = _nearest('duda', _idx(S))
    k = round(src_scale(), 3)
    return _matte(n, k)


def face(S):
    n = _nearest('duda', _idx(S))
    return FACE.get(n, [1960, 820, 860])


def clip(name, S):
    """Depoimentos em vídeo: 'lais' ou 'fern' (recorte vertical já isolado)."""
    n = _nearest(name, _idx(S))
    k = round(src_scale(), 3)
    return _load(name, n, k), k


@lru_cache(maxsize=4)
def print_img(name):
    im = cv2.imread(os.path.join(EXT, 'prints', f'{name}.png'), cv2.IMREAD_COLOR)
    return im[:, :, ::-1].astype(np.float32) / 255


def print_rgba(name, radius=34):
    im = print_img(name)
    h, w = im.shape[:2]
    a = fx.rounded_mask(w, h, radius)
    return np.dstack([im, a]).astype(np.float32)


# Regiões de interesse nos prints (coordenadas do print, px) — medidas no arquivo original
PRINT_ROI = {
    'sara': {'bubble1': (110, 400, 1520, 505), 'bubble2': (110, 1068, 1530, 455), 'header': (136, 33, 1306, 345)},
    'bianca': {'rumo': (330, 790, 860, 92), 'bubble1': (275, 550, 1297, 775), 'bubble2': (276, 1369, 1306, 500)},
    'rutilla': {'leo': (140, 712, 1345, 395), 'bubble': (83, 35, 1468, 1387)},
}
