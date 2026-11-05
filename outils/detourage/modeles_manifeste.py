"""
Manifeste des poids du détourage (hors de l'image) : dépôt Hugging Face, révision exacte, fichiers, tailles, sha256.

  python -I modeles_manifeste.py decrire <dossier_poids> > modeles.json      relève ce qui est installé (cache HF_HOME/hub)
  python -I modeles_manifeste.py verifier <dossier_poids> modeles.json        recalcule les sha256, code 1 si écart
  python -I modeles_manifeste.py telecharger <dossier_poids> modeles.json     retélécharge chaque dépôt à sa révision, puis vérifie

Poids libres (Apache-2.0), sans compte ni jeton. Le dossier est celui monté en /modeles dans le pod (HF_HOME=<dossier>/hf).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

LICENCES = {'facebook/sam2.1-hiera-large': 'apache-2.0', 'facebook/sam2.1-hiera-small': 'apache-2.0',
            'hustvl/vitmatte-small-composition-1k': 'apache-2.0', 'hustvl/vitmatte-base-composition-1k': 'apache-2.0'}


def sha256(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def hub(dossier: str) -> str:
    return os.path.join(dossier, 'hf', 'hub')


def decrire(dossier: str) -> dict:
    depots = []
    for d in sorted(os.listdir(hub(dossier))):
        if not d.startswith('models--'):
            continue
        depot = d[len('models--'):].replace('--', '/')
        snaps = os.path.join(hub(dossier), d, 'snapshots')
        for rev in sorted(os.listdir(snaps)):
            fichiers = []
            for racine, _, fs in os.walk(os.path.join(snaps, rev)):
                for f in sorted(fs):
                    c = os.path.join(racine, f)
                    fichiers.append({'chemin': os.path.relpath(c, os.path.join(snaps, rev)), 'octets': os.path.getsize(c), 'sha256': sha256(c)})
            depots.append({'depot': depot, 'revision': rev, 'licence': LICENCES.get(depot), 'source': f'https://huggingface.co/{depot}',
                           'fichiers': fichiers})
    return {'format': 1, 'usage': 'outils/detourage (palier rapide)', 'hf_home': 'hf', 'depots': depots,
            'octets_total': sum(f['octets'] for d in depots for f in d['fichiers'])}


def verifier(dossier: str, manifeste: dict) -> list[str]:
    ecarts = []
    for d in manifeste['depots']:
        base = os.path.join(hub(dossier), 'models--' + d['depot'].replace('/', '--'), 'snapshots', d['revision'])
        for f in d['fichiers']:
            c = os.path.join(base, f['chemin'])
            if not os.path.exists(c):
                ecarts.append(f"absent : {d['depot']}/{f['chemin']}")
            elif sha256(c) != f['sha256']:
                ecarts.append(f"sha256 différent : {d['depot']}/{f['chemin']}")
    return ecarts


def telecharger(dossier: str, manifeste: dict) -> None:
    os.environ['HF_HOME'] = os.path.join(dossier, 'hf')
    os.environ.pop('HF_HUB_OFFLINE', None)
    from huggingface_hub import snapshot_download
    for d in manifeste['depots']:
        snapshot_download(d['depot'], revision=d['revision'], allow_patterns=[f['chemin'] for f in d['fichiers']])


def main():
    action, dossier = sys.argv[1], sys.argv[2]
    if action == 'decrire':
        print(json.dumps(decrire(dossier), ensure_ascii=False, indent=1))
        return
    manifeste = json.load(open(sys.argv[3]))
    if action == 'telecharger':
        telecharger(dossier, manifeste)
    ecarts = verifier(dossier, manifeste)
    print('\n'.join(ecarts) if ecarts else f"conforme : {len(manifeste['depots'])} dépôts, {manifeste['octets_total'] / 1e9:.2f} Go")
    sys.exit(1 if ecarts else 0)


if __name__ == '__main__':
    main()
