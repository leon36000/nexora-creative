"""
Banc du serveur de détourage : mêmes clips, mêmes clics, même chemin HTTP que le banc GB10 du 03/11 (recherche/22 §5).

  python -I banc.py <url | unix:/chemin/prise> <dossier_clips> <sortie.json> [--matting vitmatte-small] [--seul nom]

Le jeton est lu dans le fichier NEXORA_DETOURAGE_JETON_FICHIER (jamais affiché). Chaque clip est déposé, lancé en
1280 px de large, suivi jusqu'à la fin ; on garde les mesures du serveur (temps par étape, VRAM et RAM pic,
scintillement, contrôle des fichiers) et un échantillonnage de la VRAM vue par nvidia-smi (tout le GPU). Les dossiers
de travail restent sur le serveur (planches) : les supprimer ensuite par DELETE /travaux/<id>.
"""
from __future__ import annotations

import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

# Les cinq séquences de mesure de la GB10 (scratchpad bench.sh du 03/11, recopiées telles quelles).
CLIPS = [
    ('fourrure-lapin-prairie', 'lapin-prairie', [{'image': 0, 'points': [[0.47, 0.55, 1], [0.48, 0.22, 1], [0.51, 0.05, 1], [0.1, 0.9, 0], [0.9, 0.2, 0]]}],
     {'composite': {'type': 'couleur', 'valeur': '#2b3a67'}}),
    ('mouvement-rapide-gros-plan', 'lapin-pres', [{'image': 0, 'points': [[0.62, 0.68, 1], [0.6, 0.15, 1], [0.75, 0.28, 1], [0.45, 0.92, 1], [0.1, 0.3, 0]]}],
     {'composite': {'type': 'flou'}}),
    ('personnages-trio', 'trio', [{'image': 0, 'points': [[0.34, 0.42, 1], [0.33, 0.1, 1], [0.5, 0.35, 0], [0.69, 0.62, 0]]}],
     {'composite': {'type': 'couleur', 'valeur': '#1aa36f'}}),
    ('raccords-segments-12-4', 'lapin-marche', [{'image': 0, 'points': [[0.44, 0.62, 1], [0.46, 0.3, 1], [0.1, 0.1, 0]]}],
     {'segment': {'taille': 12, 'recouvrement': 4}}),
    ('long-continu-224-images-segments-64-12', 'lapin-long', [{'image': 0, 'points': [[0.44, 0.62, 1], [0.46, 0.3, 1], [0.1, 0.1, 0]]}],
     {'segment': {'taille': 64, 'recouvrement': 12}, 'composite': {'type': 'couleur', 'valeur': '#222244'}}),
]


def entete() -> dict:
    f = os.environ.get('NEXORA_DETOURAGE_JETON_FICHIER')
    return {'Authorization': 'Bearer ' + open(f).read().strip()} if f else {}


class ConnexionUnix(http.client.HTTPConnection):
    def __init__(self, prise: str):
        super().__init__('localhost', timeout=600)
        self.prise = prise

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(600)
        self.sock.connect(self.prise)


def appel(base: str, methode: str, chemin: str, corps=None, brut: bytes | None = None, ct='application/json'):
    d = brut if brut is not None else (json.dumps(corps).encode() if corps is not None else None)
    if base.startswith('unix:'):  # prise Unix d'administration (unix:/chemin/vers/prise)
        c = ConnexionUnix(base[5:])
        c.request(methode, chemin, body=d, headers={'content-type': ct, **entete()})
        x = c.getresponse()
        b = x.read()
        c.close()
        return json.loads(b or b'{}') if x.status < 400 else {'HTTP': x.status, 'corps': b.decode()[:300]}
    r = urllib.request.Request(base + chemin, data=d, method=methode, headers={'content-type': ct, **entete()})
    try:
        with urllib.request.urlopen(r, timeout=600) as x:
            return json.loads(x.read() or b'{}')
    except urllib.error.HTTPError as e:
        return {'HTTP': e.code, 'corps': e.read().decode()[:300]}


class VramSmi(threading.Thread):
    """Pic de mémoire GPU utilisée (tout le GPU, Mo) vu par nvidia-smi, échantillonné toutes les 0,5 s."""

    def __init__(self):
        super().__init__(daemon=True)
        self.pic, self.fin = 0, threading.Event()

    def run(self):
        while not self.fin.is_set():
            try:
                o = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits', '-i', os.environ.get('BANC_GPU', '0')],
                                   capture_output=True, text=True, timeout=5).stdout
                self.pic = max(self.pic, int(o.strip().splitlines()[0]))
            except Exception:  # noqa: BLE001
                pass
            self.fin.wait(0.5)


def main():
    base, clips, sortie = sys.argv[1].rstrip('/'), sys.argv[2], sys.argv[3]
    opts = sys.argv[4:]
    matting = opts[opts.index('--matting') + 1] if '--matting' in opts else None
    seul = opts[opts.index('--seul') + 1] if '--seul' in opts else None
    resultats = {}
    for nom, fichier, invites, extra in CLIPS:
        if seul and seul not in nom:
            continue
        id_ = f'banc-{fichier}-{int(time.time())}'
        r = appel(base, 'PUT', f'/travaux/{id_}/fichiers/source.mp4', brut=open(os.path.join(clips, fichier + '.mp4'), 'rb').read(), ct='application/octet-stream')
        if not r.get('ok'):
            print(nom, 'dépôt refusé', r, flush=True)
            continue
        params = {'invites': invites, 'largeur_max': 1280, **extra}
        if matting:
            params['matting'] = matting
        smi = VramSmi()
        smi.start()
        t0 = time.time()
        r = appel(base, 'POST', f'/travaux/{id_}/lancer', {'params': params})
        while True:
            time.sleep(1)
            e = appel(base, 'GET', f'/travaux/{id_}')
            if e.get('etat') in ('termine', 'erreur', 'annule', 'interrompu'):
                break
        smi.fin.set()
        m = e.get('mesures', {})
        m['mur_s'] = round(time.time() - t0, 1)
        m['vram_smi_pic_mo'] = smi.pic
        m['etat'] = e.get('etat')
        m['message'] = e.get('message')
        m['id'] = id_
        resultats[nom] = m
        t = m.get('temps_etapes_s', {})
        print(f"{nom:42s} {e.get('etat'):8s} images {m.get('images')} total {m.get('temps_total_s')} s  suivi {t.get('suivi')}  matting {t.get('matting')}"
              f"  sorties {t.get('stabilisation_et_images')}  enc {t.get('encodage')}  VRAM {m.get('gpu', {}).get('vram_pic_go')} Go (smi {smi.pic} Mo)"
              f"  RAM {m.get('ram_pic_go')} Go  scint {m.get('scintillement')}", flush=True)
    json.dump(resultats, open(sortie, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
