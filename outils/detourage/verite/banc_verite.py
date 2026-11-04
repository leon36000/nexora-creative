"""
Banc de qualité à vérité terrain : chaque variante de matting sur les clips composés (composer.py), notée par noter.py.

  python -I banc_verite.py <url | unix:/prise> <dossier_travaux_du_serveur> <dossier_des_clips> <sortie.json> [variante ...]

Une variante est « nom=json » (ex. 'vitmatte-base={"matting":"vitmatte-base"}') ; sans variante, la liste VARIANTES.
Le même identifiant de travail sert pour toutes les variantes d'un clip : le suivi SAM est calculé une fois (clés de
contenu), seules les étapes qui dépendent du réglage changé sont refaites. Le serveur doit tourner sur cette machine.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from banc import appel  # noqa: E402
from noter import noter  # noqa: E402

VARIANTES = {
    'sam-seul': {'matting': 'aucun'},
    'vitmatte-small': {'matting': 'vitmatte-small'},
    'vitmatte-base': {'matting': 'vitmatte-base'},
    'vitmatte-base-bande3': {'matting': 'vitmatte-base', 'bande': 0.03},
    'vitmatte-small-sans-lissage': {'matting': 'vitmatte-small', 'lissage': 0.0},
}
SORTIES = {'png16': True, 'rgba16': False, 'exr': False, 'prores': False, 'webm': False, 'matte': False, 'apercu': False}


def main():
    base, travaux, clips, sortie = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3], sys.argv[4]
    variantes = dict(VARIANTES)
    if len(sys.argv) > 5:
        variantes = {a.split('=', 1)[0]: json.loads(a.split('=', 1)[1]) for a in sys.argv[5:]}
    res = json.load(open(sortie)) if os.path.exists(sortie) else {}
    for clip in sorted(d for d in os.listdir(clips) if d.startswith('clip-')):
        dc = os.path.join(clips, clip)
        id_ = f'verite-{clip[5:]}'
        if not os.path.exists(os.path.join(travaux, id_, 'source.mp4')):
            r = appel(base, 'PUT', f'/travaux/{id_}/fichiers/source.mp4', brut=open(os.path.join(dc, 'source.mp4'), 'rb').read(), ct='application/octet-stream')
            assert r.get('ok'), r
        invites = json.load(open(os.path.join(dc, 'invites.json')))
        for nom, v in variantes.items():
            params = {'invites': invites, 'largeur_max': 1280, 'sorties': SORTIES, 'composite': None, **v}
            t0 = time.time()
            appel(base, 'POST', f'/travaux/{id_}/lancer', {'params': params})
            while True:
                time.sleep(1)
                e = appel(base, 'GET', f'/travaux/{id_}')
                if e.get('etat') in ('termine', 'erreur', 'annule', 'interrompu'):
                    break
            if e.get('etat') != 'termine':
                print(clip, nom, 'ÉCHEC', e.get('message'), flush=True)
                continue
            n = noter(os.path.join(dc, 'verite'), os.path.join(travaux, id_, 'sorties', 'alpha'))
            m = e.get('mesures', {})
            n.update(secondes=round(time.time() - t0, 1), temps_etapes_s=m.get('temps_etapes_s'), vram_pic_go=m.get('gpu', {}).get('vram_pic_go'),
                     scintillement=m.get('scintillement'))
            res.setdefault(clip[5:], {})[nom] = n
            b = n['bande']
            print(f"{clip[5:]:9s} {nom:30s} bande: SAD {b['sad']:8.3f}  MSE {b['mse']:7.3f}  Grad {b['grad']:8.3f}  dtSSD {b['dtssd']:6.3f}"
                  f"   image: SAD {n['image']['sad']:8.3f}   matting {(m.get('temps_etapes_s') or {}).get('matting')} s", flush=True)
            json.dump(res, open(sortie, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
