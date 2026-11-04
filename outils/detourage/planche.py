"""
Planche de contrôle d'un détourage : pour quelques images, la source, le matte, le composite sur un fond de couleur
et un zoom ×4 sur la zone de bord la plus détaillée (cheveux, fourrure). Sert aux captures et aux comparaisons.
Usage : python -I planche.py <dossier_tache> <sortie.jpg> [images ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser('~/nexora-creative-data/models/detourage/pylibs'))
import cv2  # noqa: E402
import numpy as np  # noqa: E402


def planche(tache: str, sortie: str, images: list[int], fond=(26, 163, 111), larg=480):
    t = os.path.join(tache, 'travail', 'trames')
    s = os.path.join(tache, 'sorties')
    lignes = []
    for f in images:
        src = cv2.imread(os.path.join(t, f'{f:06d}.png'))
        a16 = cv2.imread(os.path.join(s, 'alpha', f'alpha_{f:06d}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
        rgba = cv2.imread(os.path.join(s, 'rgba16', f'rgba_{f:06d}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
        fg = rgba[..., :3]  # BGR
        bg = np.zeros_like(fg)
        bg[...] = np.array(fond[::-1], np.float32) / 255.0
        comp = (fg * a16[..., None] + bg * (1 - a16[..., None]))
        comp8 = (comp * 255).astype(np.uint8)
        # zone de bord la plus riche en demi-transparences
        bord = ((a16 > 0.05) & (a16 < 0.95)).astype(np.float32)
        dens = cv2.boxFilter(bord, -1, (96, 96))
        y, x = np.unravel_index(int(dens.argmax()), dens.shape)
        h, w = a16.shape
        y0, x0 = int(np.clip(y - 48, 0, h - 96)), int(np.clip(x - 48, 0, w - 96))
        z = lambda im: cv2.resize(im[y0:y0 + 96, x0:x0 + 96], (larg * 2 // 3, larg * 2 // 3), interpolation=cv2.INTER_NEAREST)
        redim = lambda im: cv2.resize(im, (larg, int(larg * h / w)), interpolation=cv2.INTER_AREA)
        cols = [redim(src), redim((np.repeat(a16[..., None], 3, 2) * 255).astype(np.uint8)), redim(comp8)]
        hh = cols[0].shape[0]
        zoom = np.vstack([z(src), z(comp8)])
        zoom = cv2.resize(zoom, (int(zoom.shape[1] * hh / zoom.shape[0]), hh))
        lignes.append(np.hstack(cols + [zoom]))
    wmax = max(l.shape[1] for l in lignes)
    lignes = [np.pad(l, ((0, 0), (0, wmax - l.shape[1]), (0, 0))) for l in lignes]
    cv2.imwrite(sortie, np.vstack(lignes), [cv2.IMWRITE_JPEG_QUALITY, 90])


if __name__ == '__main__':
    planche(sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]] or [0])
