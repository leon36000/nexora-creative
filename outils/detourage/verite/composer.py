"""
Compose un rendu RGBA (scene_blender.py) sur un vrai fond vidéo (bandes noires du format 2,39 retirées) : la source à détourer et sa vérité terrain exacte.

  python -I composer.py <dossier_rgba> <fond.mp4> <debut_s> <dossier_sortie>

Écrit <sortie>/source.mp4 (H.264 crf 10, 24 i/s, 1280×720), <sortie>/verite/alpha_%04d.png (alpha 16 bits du rendu)
et <sortie>/invites.json : la sélection donnée à toutes les méthodes (boîte englobante et un point au centre du sujet
sur l'image 0, comme un utilisateur qui trace un cadre). Composition I = F·α + B·(1 − α) en sRGB, alpha droit.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import cv2
import numpy as np


def main():
    rgba, fond, debut, sortie = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    ff = os.environ.get('FFMPEG_BIN', 'ffmpeg')
    images = sorted(f for f in os.listdir(rgba) if f.endswith('.png'))
    os.makedirs(os.path.join(sortie, 'verite'), exist_ok=True)
    tmp = os.path.join(sortie, 'composite')
    os.makedirs(tmp, exist_ok=True)
    fonds = os.path.join(sortie, 'fond')
    os.makedirs(fonds, exist_ok=True)
    subprocess.run([ff, '-v', 'error', '-y', '-ss', str(debut), '-i', fond, '-frames:v', str(len(images)), '-vf',
                    'crop=iw:ih*0.75,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,fps=24', os.path.join(fonds, '%04d.png')], check=True)
    invites = None
    for i, f in enumerate(images):
        im = cv2.imread(os.path.join(rgba, f), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
        a = im[..., 3:4]
        fg = im[..., [2, 1, 0]]  # BGR -> RGB
        bg = cv2.cvtColor(cv2.imread(os.path.join(fonds, f'{i + 1:04d}.png')), cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0
        c = fg * a + bg * (1 - a)
        cv2.imwrite(os.path.join(tmp, f'{i:04d}.png'), cv2.cvtColor(np.rint(np.clip(c, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        cv2.imwrite(os.path.join(sortie, 'verite', f'alpha_{i:04d}.png'), np.rint(a[..., 0] * 65535).astype(np.uint16))
        if i == 0:
            m = a[..., 0] > 0.02
            ys, xs = np.nonzero(m)
            h, w = m.shape
            x0, x1, y0, y1 = xs.min() / w, xs.max() / w, ys.min() / h, ys.max() / h
            poids = a[..., 0]
            cx, cy = float((poids * np.arange(w)).sum() / poids.sum() / w), float((poids.T * np.arange(h)).sum() / poids.sum() / h)
            invites = [{'image': 0, 'boite': [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)], 'points': [[round(cx, 4), round(cy, 4), 1]]}]
    subprocess.run([ff, '-v', 'error', '-y', '-framerate', '24', '-i', os.path.join(tmp, '%04d.png'), '-c:v', 'libx264', '-crf', '10',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(sortie, 'source.mp4')], check=True)
    json.dump(invites, open(os.path.join(sortie, 'invites.json'), 'w'))
    for d in (tmp, fonds):
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)
    print(json.dumps({'images': len(images), 'invites': invites}))


if __name__ == '__main__':
    main()
