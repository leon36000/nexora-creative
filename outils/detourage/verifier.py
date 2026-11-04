"""
Vérification indépendante des sorties d'un détourage (relecture par OpenCV, OpenEXR et ffprobe, pas par nos écrivains).
Usage : python -I verifier.py <dossier_tache> [--raccords 52,116,...]
  - PNG alpha : profondeur 16 bits réelle (valeurs distinctes > 256), plage ;
  - EXR : canaux, type de pixel (HALF), compression, prémultiplication (R ≤ A, R = lin(PNG)·A), accord avec l'alpha PNG ;
  - ProRes 4444 / WebM : format de pixel et présence du canal alpha ;
  - raccords : écart temporel de l'alpha (flux optique) aux images de recouvrement comparé au reste.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser('~/nexora-creative-data/models/detourage/pylibs'))
import cv2  # noqa: E402
import numpy as np  # noqa: E402

import noyau as N  # noqa: E402
from traitement import ffprobe_bin  # noqa: E402


def verifier(tache: str, raccords: list[int] | None = None) -> dict:
    s = os.path.join(tache, 'sorties')
    n = len(os.listdir(os.path.join(s, 'alpha')))
    rapport: dict = {'images': n}
    mid = n // 2
    a16 = cv2.imread(os.path.join(s, 'alpha', f'alpha_{mid:06d}.png'), cv2.IMREAD_UNCHANGED)
    rapport['png_alpha'] = {'dtype': str(a16.dtype), 'valeurs_distinctes': int(len(np.unique(a16))), 'min': int(a16.min()), 'max': int(a16.max()),
                            'vraiment_16_bits': bool(len(np.unique(a16)) > 256)}
    rgba = cv2.imread(os.path.join(s, 'rgba16', f'rgba_{mid:06d}.png'), cv2.IMREAD_UNCHANGED)
    rapport['png_rgba'] = {'dtype': str(rgba.dtype), 'canaux': int(rgba.shape[2])}
    try:
        import OpenEXR
        f = OpenEXR.File(os.path.join(s, 'exr', f'rgba_{mid:06d}.exr'))
        ch = f.channels()['RGBA'].pixels.astype(np.float32)
        hdr = f.header()
        a_png = a16.astype(np.float32) / 65535
        lin = N.srgb_vers_lineaire(rgba[..., 2::-1].astype(np.float32) / 65535) * a_png[..., None]  # BGR -> RGB
        rapport['exr'] = {'pixels': 'float16' if f.channels()['RGBA'].pixels.dtype == np.float16 else str(f.channels()['RGBA'].pixels.dtype),
                          'compression': str(hdr.get('compression')), 'canaux': list(f.channels().keys()),
                          'nexora_alpha': str(hdr.get('nexora/alpha')),
                          'R_inferieur_ou_egal_A': bool((ch[..., :3].max(axis=2) <= ch[..., 3] + 2e-3).all()),
                          'ecart_max_alpha_png_vs_exr': round(float(np.abs(ch[..., 3] - a_png).max()), 5),
                          'ecart_moyen_couleur_premultipliee': round(float(np.abs(ch[..., :3] - lin).mean()), 6)}
    except ImportError:
        rapport['exr'] = 'OpenEXR absent : relecture indépendante non faite'
    for nom in ('detourage-prores4444.mov', 'detourage-alpha.webm'):
        c = os.path.join(s, nom)
        if os.path.exists(c):
            r = subprocess.run([ffprobe_bin(), '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,pix_fmt:stream_tags', '-of', 'json', c],
                               capture_output=True, text=True)
            st = (json.loads(r.stdout or '{}').get('streams') or [{}])[0]
            rapport[nom] = {**st, 'alpha': ('a' in str(st.get('pix_fmt', '')).replace('yuv', '')) or str(st.get('tags', {}).get('alpha_mode', '')) == '1'}
    if raccords:
        gris = {}
        def lire(i):
            if i not in gris:
                a = cv2.imread(os.path.join(s, 'alpha', f'alpha_{i:06d}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
                rgb = cv2.cvtColor(cv2.imread(os.path.join(tache, 'travail', 'trames', f'{i:06d}.png')), cv2.COLOR_BGR2RGB)
                gris[i] = (a, rgb)
            return gris[i]
        ecarts = {}
        for i in range(1, n):
            e = N.ecart_temporel(lire(i)[0], lire(i)[1], lire(i - 1)[0], lire(i - 1)[1])
            if e is not None:
                ecarts[i] = e
            gris.pop(i - 2, None)
        sur = [ecarts[i] for i in raccords if i in ecarts]
        hors = [v for i, v in ecarts.items() if i not in set(raccords)]
        rapport['raccords'] = {'images_de_raccord': raccords, 'ecart_moyen_aux_raccords': round(float(np.mean(sur)), 5) if sur else None,
                               'ecart_moyen_ailleurs': round(float(np.mean(hors)), 5) if hors else None,
                               'ecart_max_aux_raccords': round(float(np.max(sur)), 5) if sur else None,
                               'ecart_max_ailleurs': round(float(np.max(hors)), 5) if hors else None}
    return rapport


if __name__ == '__main__':
    rac = []
    if '--raccords' in sys.argv:
        rac = [int(x) for x in sys.argv[sys.argv.index('--raccords') + 1].split(',') if x]
    print(json.dumps(verifier(sys.argv[1], rac), ensure_ascii=False, indent=1))
