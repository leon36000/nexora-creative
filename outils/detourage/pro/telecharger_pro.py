"""
Télécharge les poids du palier pro (et SAM 3.1) depuis les dépôts OFFICIELS, à la révision épinglée, et vérifie
chaque fichier contre le sha256 publié par Hugging Face (métadonnées LFS, visibles avec le jeton).

  python -I telecharger_pro.py <modeles-pro.json> <dossier_poids> <profil> [profil ...]   (profils : rtx5080, 32go, sam3.1)

Jeton : fichier désigné par HF_TOKEN_PATH (mode 600, ou Secret monté) ; jamais affiché ni écrit ailleurs.
Écrit <dossier_poids>/pro/<depot>/<chemin> et <dossier_poids>/pro/verifie.json (sha256 relevés). Reprend un
téléchargement interrompu ; un fichier déjà présent et conforme n'est pas retéléchargé.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time


def sha256(c: str) -> str:
    h = hashlib.sha256()
    with open(c, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 24), b''):
            h.update(b)
    return h.hexdigest()


def main():
    manifeste, dossier, profils = json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3:]
    if not os.environ.get('HF_TOKEN_PATH') or not os.path.exists(os.environ['HF_TOKEN_PATH']):
        sys.exit('HF_TOKEN_PATH absent : le jeton de lecture est nécessaire pour ces dépôts protégés')
    os.environ.pop('HF_HUB_OFFLINE', None)
    os.environ.setdefault('HF_HUB_ENABLE_HF_TRANSFER', '0')
    from huggingface_hub import HfApi, hf_hub_download
    api = HfApi()
    cles = list(dict.fromkeys(k for p in profils for k in manifeste['profils'][p]))
    racine = os.path.join(dossier, 'pro')
    os.makedirs(racine, exist_ok=True)
    fverif = os.path.join(racine, 'verifie.json')
    verifie = json.load(open(fverif)) if os.path.exists(fverif) else {}
    libre = os.statvfs(racine)
    besoin = sum(manifeste['fichiers'][k]['octets'] for k in cles if k not in verifie)
    print(f'{len(cles)} fichiers, {besoin / 1e9:.1f} Go à télécharger, {libre.f_bavail * libre.f_frsize / 1e9:.1f} Go libres', flush=True)
    for k in cles:
        f = manifeste['fichiers'][k]
        local = os.path.join(racine, f['depot'], f['chemin'])
        info = api.get_paths_info(f['depot'], [f['chemin']], revision=f['revision'], expand=True)[0]
        attendu = info.lfs.sha256 if info.lfs else None
        if k in verifie and os.path.exists(local) and verifie[k]['sha256'] == attendu:
            print(f'{k}: déjà conforme', flush=True)
            continue
        t = time.time()
        hf_hub_download(f['depot'], f['chemin'], revision=f['revision'], local_dir=os.path.join(racine, f['depot']))
        for a in f.get('accompagnement', []):
            hf_hub_download(f['depot'], a, revision=f['revision'], local_dir=os.path.join(racine, f['depot']))
        reel = sha256(local)
        if attendu and reel != attendu:
            os.remove(local)
            sys.exit(f'{k}: sha256 différent de celui publié, fichier supprimé')
        verifie[k] = {'depot': f['depot'], 'revision': f['revision'], 'chemin': f['chemin'], 'octets': os.path.getsize(local), 'sha256': reel,
                      'publie': attendu, 'secondes': round(time.time() - t)}
        json.dump(verifie, open(fverif, 'w'), indent=1)
        print(f"{k}: {os.path.getsize(local) / 1e9:.2f} Go, sha256 conforme, {verifie[k]['secondes']} s", flush=True)
    print('terminé', flush=True)


if __name__ == '__main__':
    main()
