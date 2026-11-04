"""
Note des mattes contre une vérité terrain (métriques standard du matting d'image et de vidéo).

  python -I noter.py <dossier_verite> <dossier_prediction> [--bande 10]   -> JSON sur la sortie standard

Séquences PNG associées par ordre trié ; 8 ou 16 bits ; un PNG RGBA donne son canal alpha. Deux zones : « image » (tout)
et « bande » (pixels où 0,002 < vérité < 0,998, dilatés de --bande px : le bord incertain, là où les méthodes diffèrent).
  sad    somme |p - g| / 1000                       mse   moyenne (p - g)² × 1000
  grad   somme (|∇p| - |∇g|)² / 1000, dérivées de gaussienne σ = 1,4 (Rhemann et al. 2009)
  dtssd  temporel : √ moyenne (Δp - Δg)² × 100, où Δ est l'écart entre deux images voisines (Erofeev et al. 2015)
"""
from __future__ import annotations

import json
import os
import sys

import cv2
import numpy as np


def lire(chemin: str) -> np.ndarray:
    im = cv2.imread(chemin, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise RuntimeError(f'illisible : {chemin}')
    if im.ndim == 3:
        im = im[..., 3] if im.shape[2] == 4 else im[..., 0]
    return im.astype(np.float64) / (65535.0 if im.dtype == np.uint16 else 255.0)


def sequence(d: str) -> list[str]:
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith('.png')]


def gradient(a: np.ndarray, sigma: float = 1.4) -> np.ndarray:
    r = int(np.ceil(3 * sigma))
    x = np.arange(-r, r + 1, dtype=np.float64)
    g = np.exp(-x ** 2 / (2 * sigma ** 2))
    g /= g.sum()
    dg = -x / sigma ** 2 * g
    dg /= np.abs(dg).sum() / 2
    gx = cv2.sepFilter2D(a, cv2.CV_64F, dg, g)
    gy = cv2.sepFilter2D(a, cv2.CV_64F, g, dg)
    return np.sqrt(gx ** 2 + gy ** 2)


def bande(g: np.ndarray, px: int) -> np.ndarray:
    m = ((g > 0.002) & (g < 0.998)).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
    return cv2.dilate(m, k) > 0


def noter(verite: str, prediction: str, px: int = 10) -> dict:
    fg, fp = sequence(verite), sequence(prediction)
    n = min(len(fg), len(fp))
    if n == 0:
        raise RuntimeError('séquence vide')
    acc = {z: {'sad': 0.0, 'mse': 0.0, 'grad': 0.0, 'dtssd': 0.0} for z in ('image', 'bande')}
    nb_dt = 0
    prec = None
    for i in range(n):
        g, p = lire(fg[i]), lire(fp[i])
        if p.shape != g.shape:
            p = cv2.resize(p, (g.shape[1], g.shape[0]), interpolation=cv2.INTER_LINEAR)
        zones = {'image': np.ones_like(g, bool), 'bande': bande(g, px)}
        e = p - g
        dgr = (gradient(p) - gradient(g)) ** 2
        for z, m in zones.items():
            acc[z]['sad'] += np.abs(e[m]).sum() / 1000
            acc[z]['mse'] += (e[m] ** 2).mean() * 1000 if m.any() else 0
            acc[z]['grad'] += dgr[m].sum() / 1000
        if prec is not None:
            d = (p - prec[0]) - (g - prec[1])
            for z, m in zones.items():
                acc[z]['dtssd'] += np.sqrt((d[m] ** 2).mean()) * 100 if m.any() else 0
            nb_dt += 1
        prec = (p, g)
    res = {}
    for z, v in acc.items():
        res[z] = {k: round(x / (nb_dt if k == 'dtssd' else n), 4) if (nb_dt or k != 'dtssd') else None for k, x in v.items()}
    return {'images': n, 'avertissement': None if len(fg) == len(fp) else f'{len(fg)} images de vérité, {len(fp)} prédites', **res}


if __name__ == '__main__':
    a = sys.argv[1:]
    px = int(a[a.index('--bande') + 1]) if '--bande' in a else 10
    print(json.dumps(noter(a[0], a[1], px), ensure_ascii=False))
