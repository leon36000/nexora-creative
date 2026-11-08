"""Construction pure de l'argv bubblewrap pour une capsule Nexora Sync.

Ce module ne lance aucun processus : pas de lancement, pas de signal, pas de
suppression, pas de lecture de ``os.environ``. Il vérifie les métadonnées des
chemins (stat/lstat) et produit la liste d'arguments remise au superviseur,
qui devra :

* fournir les FDs de verrou et de statut et les hériter (``--sync-fd`` et
  ``--json-status-fd`` désignent des descripteurs du superviseur, transmis à
  bwrap à la création du processus) ;
* vérifier lui-même les SHA du code et des modèles ainsi que les prévols
  GPU/AV : ce constructeur ne remplace aucun de ces contrôles ;
* mesurer séparément l'arrêt effectif des descendants (la fin seule du
  processus direct n'est pas une preuve).

Le dossier ``run`` doit être privé, distinct de ``runtime`` et hors de sa
hiérarchie : il est monté en lecture-écriture alors que ``runtime`` reste
lecture seule. Les caches attendus (``cache/hf``, ``cache/torch``,
``cache/xdg``, ``cache/mpl``, ``tmp``) sont créés par le préparateur, pas ici.

Les remontées ``..`` et les liens de répertoires sont refusés. ``Path`` peut
déjà normaliser ``.`` et des séparateurs répétés : ce module ne prétend pas
retrouver leur chaîne d'origine. Le Python d'un venv conserve son chemin.
"""
from __future__ import annotations

import os
import re
import stat
from pathlib import Path

__all__ = ['ErreurCapsule', 'construire', 'UUID_GPU']

# UUID canonique NVIDIA : 16 octets en hexadécimal, groupes 8-4-4-4-12.
UUID_GPU = re.compile(r'GPU-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z')

_SOUS_CHEMINS = {'HF_HOME': 'cache/hf', 'TORCH_HOME': 'cache/torch',
                 'XDG_CACHE_HOME': 'cache/xdg', 'MPLCONFIGDIR': 'cache/mpl',
                 'TMPDIR': 'tmp'}


class ErreurCapsule(ValueError):
    """Contrat de capsule violé ; aucun argv n'est produit."""


def _texte_valeur(value, quoi: str) -> str:
    if not isinstance(value, str):
        raise ErreurCapsule(f'{quoi} : chaîne attendue')
    if '\x00' in value:
        raise ErreurCapsule(f'{quoi} : NUL interdit')
    return value


def _absolu(value, quoi: str) -> Path:
    if not isinstance(value, Path):
        raise ErreurCapsule(f'{quoi} : pathlib.Path attendu')
    # Pas de resolve() : on refuse les chemins non canoniques au lieu de les
    # réécrire, et on conserve la forme d'origine (notamment un Python de venv).
    texte = str(value)
    if (not value.is_absolute() or '\x00' in texte or not texte or texte == '/'
            or '/' in texte[1:] and (texte.endswith('/') or '//' in texte)):
        raise ErreurCapsule(f'{quoi} : chemin absolu canonique (sans "//" ni "/" final) attendu')
    for element in texte.split('/')[1:]:
        if element in ('.', '..'):
            raise ErreurCapsule(f'{quoi} : élément "." ou ".." interdit')
    return value


def _sans_echappement(path: Path, quoi: str) -> None:
    """Interdit tout lien (y compris dossier) et toute remontée par parent."""
    courant = path
    while True:
        if os.path.islink(courant):
            raise ErreurCapsule(f'{quoi} : lien interdit ({courant})')
        if courant.parent == courant:
            return
        courant = courant.parent


def _exe(value, quoi: str, suivre_lien: bool) -> str:
    path = _absolu(value, quoi)
    try:
        meta = os.stat(path, follow_symlinks=suivre_lien)
    except OSError as exc:
        raise ErreurCapsule(f'{quoi} : inaccessible ({exc.strerror})') from None
    if not stat.S_ISREG(meta.st_mode):
        raise ErreurCapsule(f'{quoi} : fichier régulier attendu')
    if meta.st_uid not in (0, os.getuid()):
        raise ErreurCapsule(f'{quoi} : exécutable attendu du système ou de l’UID courant')
    if meta.st_mode & 0o022:
        raise ErreurCapsule(f'{quoi} : modifiable par groupe/autres (propriétaire attendu seul)')
    if suivre_lien and not os.access(path, os.X_OK):
        raise ErreurCapsule(f'{quoi} : non exécutable')
    return str(path)


def _dossier(value, quoi: str, mode_max: int) -> Path:
    path = _absolu(value, quoi)
    _sans_echappement(path, quoi)
    try:
        meta = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise ErreurCapsule(f'{quoi} : inaccessible ({exc.strerror})') from None
    if not stat.S_ISDIR(meta.st_mode):
        raise ErreurCapsule(f'{quoi} : répertoire attendu')
    if meta.st_uid != os.getuid():
        raise ErreurCapsule(f'{quoi} : propriétaire différent de l’UID courant')
    if stat.S_IMODE(meta.st_mode) & ~mode_max:
        raise ErreurCapsule(f'{quoi} : permissions trop larges ({oct(stat.S_IMODE(meta.st_mode))})')
    return path


def _fd(value, quoi: str, distincts: list[tuple[int, str]], optionnel: bool = False):
    if optionnel and value is None:
        return None
    # bool est une sous-classe de int : doit être refusé explicitement.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ErreurCapsule(f'{quoi} : entier attendu')
    if value < 3:
        raise ErreurCapsule(f'{quoi} : FD >= 3 attendu (0/1/2 réservés)')
    if any(value == f for f, _ in distincts):
        raise ErreurCapsule(f'{quoi} : FD réutilisé')
    distincts.append((value, quoi))
    return value


def _uuid_gpu(value) -> str:
    if not isinstance(value, str):
        raise ErreurCapsule('gpu_uuid : chaîne attendue')
    if not UUID_GPU.match(value):
        raise ErreurCapsule('gpu_uuid : forme GPU-<hexadécimal canonique> attendue')
    return value


def _script(value: Path, runtime: Path) -> str:
    script = _absolu(value, 'script')
    _sans_echappement(script, 'script')
    try:
        relatif = script.relative_to(runtime)
    except ValueError:
        raise ErreurCapsule('script : doit être situé dans runtime') from None
    if not relatif.parts:
        raise ErreurCapsule('script : doit être strictement sous runtime')
    try:
        meta = os.stat(script, follow_symlinks=False)
    except OSError as exc:
        raise ErreurCapsule(f'script : inaccessible ({exc.strerror})') from None
    if not stat.S_ISREG(meta.st_mode):
        raise ErreurCapsule('script : fichier régulier attendu')
    if meta.st_uid != os.getuid():
        raise ErreurCapsule('script : propriétaire différent de l’UID courant')
    if os.path.isdir(script) or script.suffix != '.py':
        raise ErreurCapsule('script : extension .py attendue')
    return str(script)


def _arguments(values) -> list[str]:
    if not isinstance(values, list):
        raise ErreurCapsule('arguments : liste attendue')
    out = []
    for i, arg in enumerate(values):
        out.append(_texte_valeur(arg, f'arguments[{i}]'))
    return out


def construire(runtime: Path, run: Path, python: Path, script: Path,
               arguments: list[str], ffmpeg: Path, gpu_uuid: str,
               lock_fd: int, status_fd: int | None = None,
               bwrap: Path = Path('/usr/bin/bwrap')) -> list[str]:
    """Valide les contrats et renvoie l'argv bubblewrap (jamais exécuté)."""
    runtime_p = _dossier(runtime, 'runtime', 0o755)
    run_p = _dossier(run, 'run', 0o700)
    if run_p == runtime_p:
        raise ErreurCapsule('run : doit être distinct de runtime')
    if runtime_p in run_p.parents or run_p in runtime_p.parents:
        raise ErreurCapsule('run : ne doit pas être parent ni enfant de runtime')
    # Un cache apparemment dans l'essai ne doit pas résoudre vers un cache du compte hôte.
    for path in (run_p / 'cache', *(run_p / s for s in _SOUS_CHEMINS.values())):
        _sans_echappement(path, 'cache')
        if os.path.lexists(path) and not path.is_dir():
            raise ErreurCapsule('cache : répertoire attendu')

    python_s = _exe(python, 'python', suivre_lien=True)
    ffmpeg_s = _exe(ffmpeg, 'ffmpeg', suivre_lien=True)
    bwrap_s = _exe(bwrap, 'bwrap', suivre_lien=True)
    script_s = _script(script, runtime_p)
    uuid = _uuid_gpu(gpu_uuid)
    args = _arguments(arguments)

    fds: list[tuple[int, str]] = []
    _fd(lock_fd, 'lock_fd', fds)
    _fd(status_fd, 'status_fd', fds, optionnel=True)

    runtime_txt, run_txt = str(runtime_p), str(run_p)
    argv = [bwrap_s,
            '--unshare-net', '--unshare-pid', '--die-with-parent', '--new-session',
            '--ro-bind', '/', '/',
            '--dev-bind', '/dev', '/dev',
            '--proc', '/proc',
            '--bind', run_txt, run_txt,
            '--chdir', runtime_txt,
            '--sync-fd', str(lock_fd)]
    if status_fd is not None:
        argv += ['--json-status-fd', str(status_fd)]
    argv += ['--clearenv']
    env = [
        ('PATH', os.path.dirname(ffmpeg_s) + ':/usr/bin:/bin'),
        ('PYTHONPATH', runtime_txt),
        ('CUDA_VISIBLE_DEVICES', uuid),
        ('HF_HUB_OFFLINE', '1'),
        ('TRANSFORMERS_OFFLINE', '1'),
        ('HF_HOME', run_txt + '/' + _SOUS_CHEMINS['HF_HOME']),
        ('TORCH_HOME', run_txt + '/' + _SOUS_CHEMINS['TORCH_HOME']),
        ('XDG_CACHE_HOME', run_txt + '/' + _SOUS_CHEMINS['XDG_CACHE_HOME']),
        ('TMPDIR', run_txt + '/' + _SOUS_CHEMINS['TMPDIR']),
        ('MPLCONFIGDIR', run_txt + '/' + _SOUS_CHEMINS['MPLCONFIGDIR']),
        ('PYTHONDONTWRITEBYTECODE', '1'),
        ('NO_ALBUMENTATIONS_UPDATE', '1'),
        ('TOKENIZERS_PARALLELISM', 'false'),
        ('TORCH_FORCE_WEIGHTS_ONLY_LOAD', '1'),
        ('IMAGEIO_FFMPEG_EXE', ffmpeg_s),
    ]
    for nom, valeur in env:
        argv += ['--setenv', nom, valeur]
    argv.append('--')
    argv += [python_s, script_s] + args
    return argv
