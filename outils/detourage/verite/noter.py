"""
Note des mattes contre une vérité terrain (métriques standard du matting d'image et de vidéo).

  python -I noter.py <dossier_verite> <dossier_prediction> [--bande 10]   -> JSON sur la sortie standard

Séquences PNG associées par index numérique ; gris, gris-alpha et RGBA 8 ou 16 bits. Deux zones : « image » (tout)
et « bande » (pixels où 0,002 < vérité < 0,998, dilatés de --bande px : le bord incertain, là où les méthodes diffèrent).
  sad    somme |p - g| / 1000                       mse   moyenne (p - g)² × 1000
  grad   somme (|∇p| - |∇g|)² / 1000, dérivées de gaussienne σ = 1,4 (Rhemann et al. 2009)
  dtssd  temporel : √ moyenne (Δp - Δg)² × 100, où Δ est l'écart entre deux images voisines (Erofeev et al. 2015)
"""
from __future__ import annotations

import argparse
import json
import hashlib
import importlib.util
import os
from pathlib import Path
import re

import cv2
import numpy as np

_source = Path(__file__).resolve().parents[1] / 'comparateur_alpha.py'
_spec = importlib.util.spec_from_file_location('nexora_comparateur_alpha_png', _source)
if _spec is None or _spec.loader is None:
    raise RuntimeError('Validateur PNG indisponible')
_png = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_png)


def lire(chemin: str) -> tuple[np.ndarray, dict]:
    data = _png._read_bounded(Path(chemin), _png.MAX_PNG_BYTES)
    largeur, hauteur, profondeur, couleur = _png._png_info(data)
    im = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise ValueError(f'PNG illisible : {chemin}')
    if im.dtype != (np.uint16 if profondeur == 16 else np.uint8) or im.shape[:2] != (hauteur, largeur):
        raise ValueError(f'PNG : type ou dimensions décodés invalides : {chemin}')
    if couleur == 0 and im.ndim == 2:
        alpha = im
    elif couleur in (4, 6) and im.ndim == 3 and im.shape[2] == 4:
        alpha = im[..., 3]
    else:
        raise ValueError(f'PNG : alpha décodé ambigu : {chemin}')
    meta = {'fichier': str(chemin), 'sha256': hashlib.sha256(data).hexdigest(),
            'largeur': largeur, 'hauteur': hauteur, 'profondeur': profondeur, 'type_png': couleur}
    return alpha.astype(np.float64) / ((1 << profondeur) - 1), meta


def sequence(d: str) -> dict[int, str]:
    frames = {}
    for nom in os.listdir(d):
        if not nom.lower().endswith('.png'):
            if re.fullmatch(r'(?:alpha_)?[0-9]+\.(?:jpg|jpeg|tiff|tif|webp|bmp|gif|exr)', nom, flags=re.IGNORECASE | re.ASCII):
                raise ValueError(f'image indexée non PNG : {nom}')
            continue
        match = re.fullmatch(r'(?:alpha_)?([0-9]+)\.png', nom, flags=re.IGNORECASE | re.ASCII)
        if not match:
            raise ValueError(f'nom PNG sans index reconnu : {nom}')
        index = int(match.group(1))
        if index in frames:
            raise ValueError(f'index PNG en doublon : {index}')
        frames[index] = os.path.join(d, nom)
    indices = sorted(frames)
    if not indices:
        raise ValueError('séquence vide')
    if any(b != a + 1 for a, b in zip(indices, indices[1:])):
        raise ValueError('indices de séquence non consécutifs')
    return frames


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
    if type(px) is not int or px < 0:
        raise ValueError('bande : entier positif ou nul requis')
    fg, fp = sequence(verite), sequence(prediction)
    if set(fg) != set(fp):
        raise ValueError('indices des séquences différents')
    indices = sorted(fg)
    n = len(indices)
    acc = {z: {'sad': 0.0, 'mse': 0.0, 'grad': 0.0, 'dtssd': 0.0} for z in ('image', 'bande')}
    nb_dt = 0
    prec = None
    dimensions = None
    provenance = {'verite': [], 'prediction': []}
    pixels_bande = []
    for i in indices:
        g, mg = lire(fg[i]); p, mp = lire(fp[i])
        if g.shape != p.shape or (dimensions is not None and g.shape != dimensions):
            raise ValueError('dimensions des images différentes ou inconstantes')
        dimensions = g.shape
        provenance['verite'].append({'index': i, **mg})
        provenance['prediction'].append({'index': i, **mp})
        zones = {'image': np.ones_like(g, bool), 'bande': bande(g, px)}
        pixels_bande.append(int(np.count_nonzero(zones['bande'])))
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
    frames_bande = sum(pixels > 0 for pixels in pixels_bande)
    transitions_bande = sum(pixels > 0 for pixels in pixels_bande[1:])
    if frames_bande != n:
        for k in ('sad', 'mse', 'grad'):
            res['bande'][k] = None
    if transitions_bande != nb_dt:
        res['bande']['dtssd'] = None
    return {'schema': 'nexora-matte-noter-v2', 'profil_metrologique': 'nexora-verite-v1',
            'limites': ['gradient local non directement comparable aux tableaux publiés',
                        'appariement par indices, cadence temporelle non attestée',
                        'indices appariés ne prouvent pas le nombre de frames du film original',
                        'dtSSD moyenné sur les n-1 transitions et non sur n frames'],
            'images': n, 'avertissement': None, 'bande_px': px, 'pixels_bande': pixels_bande,
            'frames_bande_evaluees': frames_bande, 'transitions_bande_evaluees': transitions_bande,
            'versions': {'opencv': cv2.__version__, 'numpy': np.__version__}, 'provenance': provenance, **res}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('verite'); parser.add_argument('prediction')
    parser.add_argument('--bande', type=int, default=10)
    args = parser.parse_args(argv)
    try:
        result = noter(args.verite, args.prediction, args.bande)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Comparaison refusée : {exc}\n')


if __name__ == '__main__':
    main()
