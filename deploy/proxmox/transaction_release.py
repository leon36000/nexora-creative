#!/usr/bin/env python3
"""Transaction de fichiers de code ; l'appelant arrête Creative et tient flock."""
import hashlib
import fcntl
import json
import os
import re
import sqlite3
from pathlib import Path, PurePosixPath
import shutil
import stat
import tarfile
import tempfile
from contextlib import contextmanager


def verifier_ancetres(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('ancêtre symbolique interdit')


def verifier_build(release):
    marker = Path(release) / 'BUILD_OK'
    verifier_ancetres(marker)
    if not marker.is_file() or not re.fullmatch('[0-9a-f]{64}\\n', marker.read_text(encoding='ascii')):
        raise ValueError('build non vérifié')


def verifier_travaux(data):
    """Vérifie les états persistés, sans afficher le contenu des travaux."""
    data = Path(data)
    verifier_ancetres(data)
    db = data / 'openfield.db'
    if not db.is_file() or db.is_symlink():
        raise ValueError('base de travaux introuvable')
    uri = db.resolve().as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as conn:
        actifs = conn.execute("SELECT count(*) FROM takes WHERE status NOT IN ('done','failed','stopped') OR status IS NULL OR NOT json_valid(settings) OR json_extract(settings,'$.nexoraSoumission')='indeterminee'").fetchone()[0]
        inconnus = conn.execute("SELECT count(*) FROM projets_longs WHERE NOT json_valid(data) OR coalesce(json_type(data,'$.sequences'),'') <> 'array'").fetchone()[0]
        if inconnus:
            raise ValueError('état des projets indéterminé')
        inconnus += conn.execute("SELECT count(*) FROM projets_longs p, json_each(p.data,'$.sequences') s WHERE coalesce(json_type(s.value,'$.scenes'),'') <> 'array'").fetchone()[0]
        if inconnus:
            raise ValueError('état des scènes indéterminé')
        inconnus += conn.execute("SELECT count(*) FROM projets_longs p, json_each(p.data,'$.sequences') s, json_each(s.value,'$.scenes') c WHERE coalesce(json_type(c.value,'$.plans'),'') <> 'array'").fetchone()[0]
        if inconnus:
            raise ValueError('état des plans indéterminé')
        inconnus += conn.execute("SELECT count(*) FROM projets_longs p, json_each(p.data,'$.sequences') s, json_each(s.value,'$.scenes') c, json_each(c.value,'$.plans') x WHERE coalesce(json_extract(x.value,'$.etat'),'') NOT IN ('a_tourner','en_cours','tourne','echec')").fetchone()[0]
        plans = conn.execute("SELECT count(*) FROM projets_longs p, json_each(p.data,'$.sequences') s, json_each(s.value,'$.scenes') c, json_each(c.value,'$.plans') x WHERE json_extract(x.value,'$.etat')='en_cours'").fetchone()[0]
    registry = data / 'detourage/registre.json'
    verifier_ancetres(registry)
    if registry.exists():
        with registry.open(encoding='utf-8') as f:
            travaux = json.load(f)
        if not isinstance(travaux, list) or any(not isinstance(t, dict) or t.get('etat') not in ('depose', 'termine', 'erreur', 'annule', 'interrompu') for t in travaux):
            raise ValueError('travaux de détourage actifs ou état inconnu')
    if actifs or inconnus or plans:
        raise ValueError('travaux actifs ou état indéterminé')


def sauvegarder_base(data, backup):
    """Copie SQLite cohérente sans afficher ses données et sans toucher à la source."""
    data, backup = Path(data), Path(backup)
    verifier_ancetres(data)
    verifier_ancetres(backup)
    source = data / 'openfield.db'
    if not source.is_file() or source.is_symlink():
        raise ValueError('base de travaux introuvable')
    cible = backup / 'openfield-avant.db'
    fd = os.open(cible, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    with sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True) as src:
        with sqlite3.connect(cible) as dst:
            src.backup(dst)
            if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('sauvegarde SQLite invalide')
    with cible.open('rb') as f:
        os.fsync(f.fileno())
    with (backup / 'openfield-avant.sha256').open('x', encoding='ascii') as f:
        f.write(digest(cible) + '\n')
        f.flush()
        os.fsync(f.fileno())
    sync_dir(backup)


@contextmanager
def verrou(path):
    verifier_ancetres(Path(path).parent)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('verrou ordinaire requis')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def chemin(root, rel):
    p = PurePosixPath(rel)
    app_ok = (len(p.parts) > 1 and p.parts[0] == 'app'
              and (p.parts[1] in ('server', 'src', 'shared', 'public', 'mcp', 'workflows', 'scripts', 'dist')
                   or len(p.parts) == 2 and p.parts[1] in ('index.html', 'package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts')))
    studio_ok = len(p.parts) > 2 and p.parts[:2] == ('mode-studio', 'dist')
    if (p.is_absolute() or not p.parts or '..' in p.parts or p.parts[0] not in ('app', 'mode-studio')
            or any(x in ('.git', 'node_modules', 'secrets') or x.startswith('.env') or x == '.npmrc' for x in p.parts)
            or not (app_ok or studio_ok)):
        raise ValueError('chemin interdit')
    verifier_ancetres(root)
    path = Path(root)
    for index, part in enumerate(p.parts):
        path = path / part
        if path.is_symlink():
            raise ValueError('chemin symbolique interdit')
        if index < len(p.parts) - 1 and path.exists() and not path.is_dir():
            raise ValueError('parent non répertoire')
    return path


def digest(path):
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(mode):
        raise ValueError('fichier ordinaire requis')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


SANS_CONTROLE = object()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def copier(source, target, attendu_source, attendu_cible=SANS_CONTROLE):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.nexora-livraison-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as out, os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as src:
            source_stat = os.fstat(src.fileno())
            shutil.copyfileobj(src, out)
            out.flush()
            os.fsync(out.fileno())
        if digest(Path(name)) != attendu_source:
            raise ValueError('source modifiée pendant la copie')
        if attendu_cible is not SANS_CONTROLE and digest(target) != attendu_cible:
            raise ValueError('cible modifiée pendant la copie')
        os.chmod(name, stat.S_IMODE(source_stat.st_mode))
        if os.geteuid() == 0:
            os.chown(name, source_stat.st_uid, source_stat.st_gid)
        os.replace(name, target)
        sync_dir(target.parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)  # uniquement le temporaire exclusif de cette copie


def planifier(release, cible, chemins):
    """Calcule les empreintes avant/après pour revue, sans modifier la cible."""
    release, cible = Path(release), Path(cible)
    verifier_build(release)
    if not chemins or len(set(chemins)) != len(chemins):
        raise ValueError('liste de chemins vide ou dupliquée')
    if any(a != b and PurePosixPath(a) in PurePosixPath(b).parents for a in chemins for b in chemins):
        raise ValueError('chemins imbriqués')
    actions = []
    for rel in chemins:
        src, dst = chemin(release, rel), chemin(cible, rel)
        apres = digest(src)
        if apres is None:
            raise ValueError('source absente')
        actions.append({'chemin': rel, 'avant': digest(dst), 'apres': apres})
    return actions


def preparer(release, cible, backup, actions):
    """Vérifie le manifeste revu puis sauvegarde les versions présentes."""
    release, cible, backup = Path(release), Path(cible), Path(backup)
    verifier_build(release)
    verifier_ancetres(backup.parent)
    if (backup.resolve().is_relative_to(release.resolve())
            or any(backup.resolve().is_relative_to((cible / part).resolve()) for part in ('app', 'mode-studio'))
            or any(release.resolve().is_relative_to((cible / part).resolve()) for part in ('app', 'mode-studio'))):
        raise ValueError('release ou sauvegarde dans un arbre actif')
    if cible.stat().st_dev != backup.parent.stat().st_dev:
        raise ValueError('sauvegarde sur un autre système de fichiers')
    if not actions or len({a['chemin'] for a in actions}) != len(actions):
        raise ValueError('manifeste vide ou dupliqué')
    for action in actions:
        rel = action['chemin']
        if not re.fullmatch('[0-9a-f]{64}', str(action['apres'])) or (action['avant'] is not None and not re.fullmatch('[0-9a-f]{64}', str(action['avant']))):
            raise ValueError('empreinte de manifeste invalide')
        if digest(chemin(release, rel)) != action['apres'] or digest(chemin(cible, rel)) != action['avant']:
            raise ValueError('conflit avec le manifeste revu')
    backup.mkdir(mode=0o700)  # nom unique, jamais remplacé
    sync_dir(backup.parent)
    for action in actions:
        rel = action['chemin']
        if action['avant'] is not None:
            dst, saved = chemin(cible, rel), chemin(backup / 'avant', rel)
            copier(dst, saved, action['avant'], None)
            if digest(dst) != action['avant'] or digest(saved) != action['avant']:
                raise ValueError('conflit pendant la sauvegarde')
    with (backup / 'manifest.json').open('x', encoding='utf-8') as f:
        json.dump({'cible': str(cible.resolve()), 'release': str(release.resolve()), 'actions': actions}, f)
        f.flush()
        os.fsync(f.fileno())
    sync_dir(backup)
    return actions


def appliquer(release, cible, actions):
    """Écrit uniquement les chemins dont la préimage est encore attendue."""
    verifier_build(release)
    for action in actions:
        src, dst = chemin(release, action['chemin']), chemin(cible, action['chemin'])
        if digest(src) != action['apres'] or digest(dst) != action['avant']:
            raise ValueError('conflit avant écriture')
        copier(src, dst, action['apres'], action['avant'])
        if digest(dst) != action['apres']:
            raise ValueError('écriture non vérifiée')


def verifier_rollback(cible, backup):
    """Vérifie toutes les préconditions sans rien restaurer."""
    cible, backup = Path(cible), Path(backup)
    verifier_ancetres(cible)
    verifier_ancetres(backup)
    with (backup / 'manifest.json').open(encoding='utf-8') as f:
        state = json.load(f)
    if str(cible.resolve()) != state['cible']:
        raise ValueError('cible différente de la sauvegarde')
    for action in state['actions']:
        dst = chemin(cible, action['chemin'])
        if digest(dst) not in (action['avant'], action['apres']):
            raise ValueError('conflit : version modifiée depuis la livraison')
        if action['avant'] is not None and digest(chemin(backup / 'avant', action['chemin'])) != action['avant']:
            raise ValueError('sauvegarde corrompue')
        if (action['avant'] is None and digest(dst) == action['apres']
                and os.path.lexists(chemin(backup / 'nouveaux', action['chemin']))):
            raise ValueError('destination de conservation occupée')
    return state


def rollback(cible, backup):
    """N'écrase aucune divergence ; les nouvelles versions restent dans la release."""
    cible, backup = Path(cible), Path(backup)
    state = verifier_rollback(cible, backup)
    for action in reversed(state['actions']):
        dst = chemin(cible, action['chemin'])
        if digest(dst) != action['apres'] or action['avant'] == action['apres']:
            continue
        if action['avant'] is None:
            retired = chemin(backup / 'nouveaux', action['chemin'])
            retired.parent.mkdir(parents=True, exist_ok=True)
            if os.path.lexists(retired):
                raise ValueError('destination de conservation occupée')
            os.rename(dst, retired)
            sync_dir(dst.parent)
            sync_dir(retired.parent)
        else:
            copier(chemin(backup / 'avant', action['chemin']), dst, action['avant'], action['apres'])


def ajouter_dependances_tar(archive, root):
    """Conserve les liens symboliques et matérialise les liens physiques en fichiers."""
    root = Path(root)
    prefix = PurePosixPath('release/app/node_modules')
    if archive.dereference:
        raise ValueError('suivi global des liens interdit')

    def filtrer(info):
        if info.islnk():
            relatif = PurePosixPath(info.name).relative_to(prefix)
            source = root.joinpath(*relatif.parts)
            if source.is_symlink() or not source.is_file():
                raise ValueError('source de lien physique invalide')
            info.type = tarfile.REGTYPE
            info.linkname = ''
            info.size = source.stat().st_size
        return info

    archive.add(root, arcname=str(prefix), filter=filtrer)


def empreinte_dependances(root):
    """Empreinte du seul arbre de dépendances construit pour cette release."""
    root = Path(root)
    h = hashlib.sha256()
    for parent, dirs, files in os.walk(root, followlinks=False):
        dirs.sort()
        for name in sorted(dirs + files):
            if name.startswith('.env') or name == '.npmrc':
                raise ValueError('configuration interdite dans les dépendances')
            item = Path(parent) / name
            rel = item.relative_to(root).as_posix()
            if item.is_symlink():
                if not item.resolve().is_relative_to(root.resolve()):
                    raise ValueError('lien de dépendance hors release')
                value = 'lien:' + os.readlink(item)
            elif item.is_dir():
                value = 'dossier'
            else:
                value = 'fichier:' + str(digest(item))
            h.update((rel + '\0' + value + '\n').encode())
    return h.hexdigest()


def planifier_dependances(release, cible):
    """Empreintes des dépendances avant/après pour revue."""
    release, cible = Path(release), Path(cible)
    verifier_build(release)
    for path in (release, cible, cible / 'app'):
        verifier_ancetres(path)
    if not release.resolve().is_relative_to((cible / 'releases').resolve()) or release.resolve() == (cible / 'releases').resolve():
        raise ValueError('release hors répertoire dédié')
    nouveau = release / 'app/node_modules'
    ancien = cible / 'app/node_modules'
    if nouveau.is_symlink() or not nouveau.is_dir() or not ancien.is_dir():
        raise ValueError('dépendances absentes')
    recu = release / 'DEPENDANCES_SHA256'
    verifier_ancetres(recu)
    if not recu.is_file() or recu.read_text(encoding='ascii').strip() != empreinte_dependances(nouveau):
        raise ValueError('dépendances modifiées depuis le build')
    lien = os.readlink(ancien) if ancien.is_symlink() else None
    if lien:
        old_root = ancien.resolve()
        if not Path(lien).is_absolute() or not old_root.is_relative_to((cible / 'releases').resolve()) or old_root.name != 'node_modules' or old_root.parent.name != 'app':
            raise ValueError('lien de dépendances hors release')
        verifier_build(old_root.parent.parent)
    st = ancien.lstat()
    return {'ancien_dev': st.st_dev, 'ancien_ino': st.st_ino, 'ancien_mtime': st.st_mtime_ns,
            'ancien_lien': lien,
            'ancien_sha256': empreinte_dependances(ancien),
            'nouveau': str(nouveau.resolve()), 'sha256': empreinte_dependances(nouveau)}


def preparer_dependances(release, cible, backup, state):
    """Vérifie les empreintes revues avant le déplacement du répertoire actif."""
    backup = Path(backup)
    verifier_ancetres(backup)
    if planifier_dependances(release, cible) != state:
        raise ValueError('conflit avec le manifeste des dépendances')
    if state['ancien_dev'] != backup.stat().st_dev:
        raise ValueError('sauvegarde sur un autre système de fichiers')
    with (backup / 'dependances.json').open('x', encoding='utf-8') as f:
        json.dump(state, f)
        f.flush()
        os.fsync(f.fileno())
    sync_dir(backup)
    return state


def appliquer_dependances(cible, backup, state):
    for path in (cible, Path(cible) / 'app', backup):
        verifier_ancetres(path)
    verifier_build(Path(state['nouveau']).parent.parent)
    ancien = Path(cible) / 'app/node_modules'
    st = ancien.stat(follow_symlinks=False)
    if ((not stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode)) or (st.st_dev, st.st_ino, st.st_mtime_ns) !=
            (state['ancien_dev'], state['ancien_ino'], state['ancien_mtime'])
            or (os.readlink(ancien) if ancien.is_symlink() else None) != state['ancien_lien']
            or empreinte_dependances(ancien) != state['ancien_sha256']
            or empreinte_dependances(state['nouveau']) != state['sha256']):
        raise ValueError('conflit avant remplacement des dépendances')
    if os.path.lexists(Path(backup) / 'node_modules-avant'):
        raise ValueError('sauvegarde de dépendances déjà présente')
    os.rename(ancien, Path(backup) / 'node_modules-avant')
    sync_dir(ancien.parent)
    sync_dir(backup)
    os.symlink(state['nouveau'], ancien)
    sync_dir(ancien.parent)


def verifier_rollback_dependances(cible, backup):
    ancien, backup = Path(cible) / 'app/node_modules', Path(backup)
    for path in (cible, Path(cible) / 'app', backup):
        verifier_ancetres(path)
    with (backup / 'dependances.json').open(encoding='utf-8') as f:
        state = json.load(f)
    saved = backup / 'node_modules-avant'
    if not os.path.lexists(saved) and ancien.is_dir():
        st = ancien.lstat()
        if ((st.st_dev, st.st_ino) == (state['ancien_dev'], state['ancien_ino'])
                and (os.readlink(ancien) if ancien.is_symlink() else None) == state['ancien_lien']
                and empreinte_dependances(ancien) == state['ancien_sha256']):
            return False  # rien à annuler, ou retour arrière déjà terminé
    if not saved.is_dir() or (os.readlink(saved) if saved.is_symlink() else None) != state['ancien_lien']:
        raise ValueError('sauvegarde de dépendances absente')
    st = saved.lstat()
    if ((st.st_dev, st.st_ino) != (state['ancien_dev'], state['ancien_ino'])
            or empreinte_dependances(saved) != state['ancien_sha256']):
        raise ValueError('sauvegarde de dépendances modifiée')
    if ancien.is_symlink():
        if os.readlink(ancien) != state['nouveau'] or empreinte_dependances(state['nouveau']) != state['sha256']:
            raise ValueError('conflit sur les dépendances déployées')
        if os.path.lexists(backup / 'node_modules-nouveau-lien'):
            raise ValueError('destination de conservation occupée')
    elif ancien.exists():
        raise ValueError('dépendances actives modifiées')
    return True


def rollback_dependances(cible, backup):
    ancien, backup = Path(cible) / 'app/node_modules', Path(backup)
    if not verifier_rollback_dependances(cible, backup):
        return
    saved = backup / 'node_modules-avant'
    if ancien.is_symlink():
        os.rename(ancien, backup / 'node_modules-nouveau-lien')
        sync_dir(ancien.parent)
        sync_dir(backup)
    os.rename(saved, ancien)
    sync_dir(ancien.parent)
    sync_dir(backup)
