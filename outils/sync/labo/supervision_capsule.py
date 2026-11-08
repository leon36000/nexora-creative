"""Supervise une capsule déjà construite ; signaux vers notre Popen seulement.

Les PID et espaces de noms sont ceux de l'hôte. Le child-pid de bubblewrap
désigne son reaper, pas le Python exécutant le modèle. Aucun changement global
de récolte des processus, aucune lecture de cmdline ou d'environnement.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def identite(pid: int):
    p = Path('/proc')/str(pid)
    texte = (p/'stat').read_text()
    champs = texte[texte.rindex(')')+2:].split()
    uid = next(l for l in (p/'status').read_text().splitlines() if l.startswith('Uid:'))
    return {'pid':pid, 'start':int(champs[19]), 'uid':int(uid.split()[1]),
            'ppid':int(champs[1]), 'etat':champs[0], 'ns':os.readlink(p/'ns/pid')}


def _meme(a, b):
    return all(a[k] == b[k] for k in ('pid','start','uid','ns'))


def _namespace(ns):
    result = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            if os.readlink(path/'ns/pid') == ns:
                result.append(identite(int(path.name)))
        except FileNotFoundError:
            continue  # Processus déjà terminé pendant l'énumération.
        except PermissionError:
            # Un autre programme peut être non traçable, même sous notre UID.
            # Les identités de NOTRE capsule sont relues séparément ci-dessous :
            # une erreur sur l'une d'elles empêche de confirmer son arrêt.
            continue
    return result


def _ecrire(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


class _Interruption(Exception):
    pass


def _interrompre(sig, frame):
    raise _Interruption(sig)


def _arreter(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def superviser(argv: list[str], run: Path, lock_fd: int, status_fd_lire: int,
               status_fd_ecrire: int, delai: float, controle=None):
    """Prend possession des deux FDs de statut, jamais du FD de verrou.

    L'appelant garde son verrou ouvert. bubblewrap le conserve via --sync-fd.
    Un arrêt est confirmé seulement après disparition (ou zombie) des identités
    observées et absence de processus vivant dans le namespace isolé.
    """
    if isinstance(delai, bool) or not isinstance(delai, (int,float)) or not math.isfinite(delai) or delai <= 0:
        raise ValueError('délai positif fini requis')
    if not isinstance(argv, list) or not argv or any(not isinstance(a,str) or '\0' in a for a in argv):
        raise ValueError('argv invalide')
    if len({lock_fd,status_fd_lire,status_fd_ecrire}) != 3 or any(
        isinstance(f,bool) or not isinstance(f,int) or f < 3 for f in (lock_fd,status_fd_lire,status_fd_ecrire)):
        raise ValueError('descripteurs distincts >= 3 requis')
    for option, attendu in (('--sync-fd',lock_fd),('--json-status-fd',status_fd_ecrire)):
        i = argv.index(option)
        if i >= argv.index('--') or argv[i+1] != str(attendu):
            raise ValueError('descripteur différent de la commande')
    debut = time.monotonic()
    bilan = {'statut':'echec', 'phase':'avant_demarrage', 'identite_namespace':None,
             'arret_confirmé':False, 'processus_observés':[]}
    proc = None
    connus = {}
    precedents = {}
    try:
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            precedents[sig] = signal.signal(sig, _interrompre)
        fd = os.open(run/'execution.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as log:
            proc = subprocess.Popen(argv, env={}, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, pass_fds=(lock_fd,status_fd_ecrire), close_fds=True)
        os.close(status_fd_ecrire)
        status_fd_ecrire = None
        os.set_blocking(status_fd_lire,False)
        tampon = b''
        total_lu = 0
        while True:
            try:
                morceau = os.read(status_fd_lire,4096)
            except BlockingIOError:
                morceau = b''
            tampon += morceau
            total_lu += len(morceau)
            if total_lu > 65536:
                raise ValueError('statut bubblewrap excessif')
            while b'\n' in tampon:
                ligne,tampon = tampon.split(b'\n',1)
                obj = json.loads(ligne)
                if 'child-pid' in obj and bilan['identite_namespace'] is None:
                    pid = obj['child-pid']
                    if isinstance(pid,bool) or not isinstance(pid,int) or pid < 1:
                        raise ValueError('child-pid invalide')
                    idn = identite(pid)
                    if (idn['uid'] != os.getuid() or idn['ppid'] != proc.pid
                            or idn['ns'] == os.readlink('/proc/self/ns/pid')):
                        raise ValueError('identité du reaper non vérifiée')
                    bilan['identite_namespace'] = idn
                    bilan['wrapper_pid'] = proc.pid
            idn = bilan['identite_namespace']
            if proc.poll() is not None:
                bilan['phase'] = 'termine' if proc.returncode == 0 else 'capsule_echouee'
                break
            if idn is not None:
                for item in _namespace(idn['ns']):
                    if item['uid'] != os.getuid():
                        raise ValueError('UID inattendu dans notre namespace')
                    connus[(item['pid'],item['start'])] = item
                if proc.poll() is None:
                    try:
                        actuelle = identite(idn['pid'])
                    except FileNotFoundError:
                        # Le reaper peut finir entre poll() et la lecture de /proc.
                        # Attendre uniquement notre wrapper avant le contrôle final.
                        proc.wait(timeout=.5)
                        bilan['phase'] = 'termine' if proc.returncode == 0 else 'capsule_echouee'
                        break
                    if not _meme(idn,actuelle):
                        raise ValueError('identité du reaper changée')
                    if controle is not None:
                        controle(idn, [p['pid'] for p in _namespace(idn['ns'])])
            if time.monotonic()-debut >= delai:
                bilan['phase'] = 'delai_depasse'
                break
            time.sleep(.2)
    except Exception as exc:
        bilan.update(phase='interrompu' if isinstance(exc,_Interruption) else 'erreur_supervision',
                     erreur=type(exc).__name__+': '+str(exc))
    finally:
        try:
            if proc is not None:
                _arreter(proc)
                bilan['code_sortie'] = proc.returncode
            idn = bilan['identite_namespace']
            if idn is not None and proc is not None and proc.poll() is not None:
                fin = time.monotonic()+2
                while True:
                    vivants = [p for p in _namespace(idn['ns']) if p['etat'] not in ('Z','X')]
                    inconnus = []
                    for ancien in connus.values():
                        try:
                            p = identite(ancien['pid'])
                            if _meme(ancien,p) and p['etat'] not in ('Z','X'):
                                inconnus.append(p)
                        except FileNotFoundError:
                            pass
                    if not vivants and not inconnus:
                        bilan['arret_confirmé'] = True
                        break
                    if time.monotonic() >= fin:
                        break
                    time.sleep(.05)
                if bilan['phase'] == 'termine' and bilan['arret_confirmé']:
                    bilan['statut'] = 'succès'
        except Exception as exc:
            bilan['erreur_arret'] = type(exc).__name__+': '+str(exc)
        finally:
            for sig,ancien in precedents.items():
                signal.signal(sig,ancien)
            for fd in (status_fd_lire,status_fd_ecrire):
                if fd is not None:
                    os.close(fd)
            bilan['duree'] = time.monotonic()-debut
            bilan['processus_observés'] = list(connus.values())
            _ecrire(run/'resultat-execution.json',bilan)
    return bilan
