#!/usr/bin/env python3
"""Maintenance Creative : manifeste revu, service unique et rollback contrôlé."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

import transaction_release as T


def service(action):
    subprocess.run(['systemctl', action, 'nexora-creative'], check=True,
                   env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin'})


def attendre_sante(url, predicate):
    limite = time.monotonic() + 30
    while time.monotonic() < limite:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if predicate(json.load(r)):
                    return True
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(.5)
    return False


def sante():
    return attendre_sante('http://127.0.0.1:3161/api/nexora/detourage/capacites',
                          lambda obj: obj.get('rapide', {}).get('disponible') is True)


def sante_creative():
    return attendre_sante('http://127.0.0.1:3161/api/nexora/etat', lambda obj: isinstance(obj, dict))


def base_ouverte(data, groupe, racine_cgroup=Path('/sys/fs/cgroup'), racine_proc=Path('/proc')):
    if not groupe.startswith('/system.slice/') or '..' in groupe:
        raise ValueError('groupe du service illisible')
    procs = racine_cgroup / groupe.lstrip('/') / 'cgroup.procs'
    expected = str((Path(data) / 'openfield.db').resolve())
    for pid in procs.read_text().split():
        if not pid.isdigit():
            raise ValueError('identité du processus invalide')
        dossier = racine_proc / pid / 'fd'
        try:
            for fd in dossier.iterdir():
                try:
                    if os.readlink(fd) == expected:
                        return
                except FileNotFoundError:
                    continue
        except FileNotFoundError:
            continue
    raise ValueError('base ouverte par Creative non confirmée')


def verifier_base_active(data):
    groupe = subprocess.check_output(['systemctl', 'show', 'nexora-creative', '--property=ControlGroup', '--value'],
                                      env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin'}, text=True).strip()
    base_ouverte(data, groupe)


def planifier(release, cible, sortie):
    release, cible = Path(release), Path(cible)
    T.verifier_build(release)
    T.verifier_ancetres(release / 'SOURCE_FILES.json')
    with (release / 'SOURCE_FILES.json').open(encoding='utf-8') as f:
        chemins = json.load(f)
    T.verifier_ancetres(release / 'SOURCE_HASHES.json')
    with (release / 'SOURCE_HASHES.json').open(encoding='utf-8') as f:
        source_sha = json.load(f)
    if (not isinstance(source_sha, dict) or set(source_sha) != {nom for nom in chemins if nom.startswith('app/') and not nom.startswith('app/dist/')}
            or any(T.digest(T.chemin(release, nom)) != sha for nom, sha in source_sha.items())):
        raise ValueError('sources modifiées depuis le build')
    actions = T.planifier(release, cible, chemins)
    plan = {'release': str(release.resolve()), 'cible': str(cible.resolve()),
            'archive_sha256': (release / 'BUILD_OK').read_text().strip(),
            'dependances': T.planifier_dependances(release, cible), 'actions': actions}
    with open(sortie, 'x', encoding='utf-8') as f:
        json.dump(plan, f, indent=2)


def activer(release, cible, data, backup, actions, dependances, stopper=None, demarrer=None, verifier=None, identite=None):
    """L'appelant a revu le manifeste ; l'identité de la base est vérifiée."""
    release, cible, data, backup = map(Path, (release, cible, data, backup))
    stopper = stopper or (lambda: service('stop'))
    demarrer = demarrer or (lambda: service('start'))
    verifier = verifier or sante
    identite = identite or verifier_base_active
    with T.verrou(cible / '.nexora-livraison.lock'):
        identite(data)
        T.verifier_travaux(data)
        actions = T.preparer(release, cible, backup, actions)
        dep = T.preparer_dependances(release, cible, backup, dependances)
        stopper()
        modifie = False
        demarre = False
        try:
            T.verifier_travaux(data)  # contrôle de nouveau après l'arrêt
            T.sauvegarder_base(data, backup)
            modifie = True  # une interruption peut survenir pendant la première copie
            T.appliquer(release, cible, actions)
            T.appliquer_dependances(cible, backup, dep)
            demarre = True  # même une erreur de commande peut suivre un démarrage effectif
            demarrer()
            if not verifier():
                raise ValueError('santé Matte indisponible après livraison')
        except BaseException:
            if demarre:
                stopper()
                T.verifier_travaux(data)
            if modifie:
                T.verifier_rollback(cible, backup)
                T.verifier_rollback_dependances(cible, backup)
                T.rollback_dependances(cible, backup)
                T.rollback(cible, backup)
            demarrer()
            raise


def retour(cible, data, backup, stopper=None, demarrer=None, identite=None, verifier=None):
    """Retour explicite, seulement si toutes les écritures sont reconnues."""
    cible, data, backup = map(Path, (cible, data, backup))
    stopper = stopper or (lambda: service('stop'))
    demarrer = demarrer or (lambda: service('start'))
    identite = identite or verifier_base_active
    verifier = verifier or sante_creative
    with T.verrou(cible / '.nexora-livraison.lock'):
        identite(data)
        T.verifier_travaux(data)
        T.verifier_rollback(cible, backup)
        T.verifier_rollback_dependances(cible, backup)
        stopper()
        modifie = False
        try:
            T.verifier_travaux(data)
            T.verifier_rollback(cible, backup)
            T.verifier_rollback_dependances(cible, backup)
            modifie = True
            T.rollback_dependances(cible, backup)
            T.rollback(cible, backup)
        except BaseException:
            if not modifie:
                demarrer()
            raise
        demarrer()
        if not verifier():
            raise ValueError('Creative indisponible après retour')


def main(argv):
    if len(argv) == 4 and argv[0] == 'plan':
        planifier(*argv[1:])
        return
    if len(argv) == 4 and argv[0] == 'retour':
        retour(*argv[1:])
        return
    if len(argv) != 6 or argv[0] != 'activer':
        raise SystemExit('usage : livrer_release.py plan RELEASE CIBLE MANIFESTE | activer RELEASE CIBLE DATA BACKUP MANIFESTE | retour CIBLE DATA BACKUP')
    with open(argv[5], encoding='utf-8') as f:
        plan = json.load(f)
    release, cible = Path(argv[1]), Path(argv[2])
    T.verifier_build(release)
    if (plan['release'] != str(release.resolve()) or plan['cible'] != str(cible.resolve())
            or plan['archive_sha256'] != (release / 'BUILD_OK').read_text().strip()):
        raise ValueError('manifeste d’une autre release ou cible')
    T.verifier_ancetres(release / 'SOURCE_FILES.json')
    with (release / 'SOURCE_FILES.json').open(encoding='utf-8') as f:
        chemins = json.load(f)
    if sorted(a['chemin'] for a in plan['actions']) != sorted(chemins):
        raise ValueError('liste de fichiers différente de la release')
    activer(*argv[1:5], plan['actions'], plan['dependances'])


if __name__ == '__main__':
    main(sys.argv[1:])
