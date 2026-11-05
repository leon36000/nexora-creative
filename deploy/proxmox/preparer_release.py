#!/usr/bin/env python3
"""Prépare une release isolée ; ne modifie jamais l'application active."""
import hashlib
import json
import os
import posixpath
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile

from transaction_release import empreinte_dependances
from transaction_release import chemin, verifier_ancetres


def interdit(path):
    p = PurePosixPath(path)
    return (p.is_absolute() or not p.parts or p.parts[0] not in ('app', 'mode-studio')
            or any(x in ('', '.', '..', '.git', 'node_modules', 'secrets')
                   or x.startswith('.env') or x == '.npmrc' for x in p.parts)
            or p.parts[:2] == ('app', 'data'))


def code_app(path):
    p = PurePosixPath(path)
    return (len(p.parts) > 1 and p.parts[0] == 'app'
            and (p.parts[1] in ('server', 'src', 'shared', 'public', 'mcp', 'workflows', 'scripts')
                 or len(p.parts) == 2 and p.parts[1] in ('index.html', 'package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts')))


def build_seulement(path):
    p = PurePosixPath(path)
    return (len(p.parts) > 1 and p.parts[0] == 'app'
            and (p.parts[1] in ('docs', 'deploy') or len(p.parts) == 2 and
                 (p.parts[1] in ('.dockerignore', '.gitignore', 'LICENSE', 'vitest.director.ci.config.mjs', 'vite-build.test.ts')
                  or p.parts[1].endswith('.md'))))


def archive(repo, revision, sortie):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('SHA Git complet requis')
    env = {'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_TERMINAL_PROMPT': '0'}
    ref = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', revision + '^{commit}'], env=env, text=True).strip()
    if ref != revision:
        raise ValueError('SHA différent du commit demandé')
    tree = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-rz', revision, '--', 'app', 'mode-studio'], env=env)
    paths = []
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        meta, raw = entry.split(b'\t', 1)
        name = raw.decode('utf-8', 'strict')
        if interdit(name):
            continue
        if not meta.startswith((b'100644 blob ', b'100755 blob ')):
            raise ValueError('fichier Git non ordinaire refusé')
        paths.append(name)
    if not paths:
        raise ValueError('archive vide')
    with open(sortie, 'xb') as out:
        subprocess.run(['git', '-C', str(repo), 'archive', '--format=tar', revision, '--', *paths],
                       env=env, stdout=out, check=True)
    with open(sortie, 'rb') as result:
        return hashlib.file_digest(result, 'sha256').hexdigest()


def construire(archive_path, sha, dossier, runner=subprocess.run):
    if runner is subprocess.run and (os.environ.get('NEXORA_RELEASE_SANDBOX') != 'ci-chroot'
                                      or os.getuid() != 65534 or os.geteuid() != 65534
                                      or os.getgid() != 65534 or os.getegid() != 65534
                                      or set(os.getgroups()) - {65534} or Path('/proc').exists()
                                      or Path('/etc/nexora').exists()):
        raise ValueError('construction autorisée seulement dans le chroot CI isolé')
    if Path(archive_path).name.startswith('.env') or Path(archive_path).name == '.npmrc':
        raise ValueError('archive à nom interdit')
    if not re.fullmatch('[0-9a-f]{64}', sha):
        raise ValueError('SHA-256 complet requis')
    fichiers, source_sha, toutes_sources = [], {}, {}
    with open(archive_path, 'rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != sha:
            raise ValueError('archive altérée')
        f.seek(0)
        dossier = Path(dossier)
        dossier.mkdir(mode=0o700)  # exclusif : une release existante n'est jamais remplacée
        with tarfile.open(fileobj=f, mode='r:*') as tar:
            for item in tar:
                if interdit(item.name) or not (item.isdir() or item.isfile()):
                    raise ValueError('entrée d’archive interdite')
                target = dossier.joinpath(*PurePosixPath(item.name).parts)
                if item.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    if item.name.startswith('app/') and not (code_app(item.name) or build_seulement(item.name)):
                        raise ValueError('fichier app non classé')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = tar.extractfile(item)
                    if source is None:
                        raise ValueError('fichier d’archive illisible')
                    with source, open(target, 'xb') as out:
                        while chunk := source.read(1024 * 1024):
                            out.write(chunk)
                    target.chmod(item.mode & 0o755)
                    with target.open('rb') as contenu:
                        toutes_sources[item.name] = hashlib.file_digest(contenu, 'sha256').hexdigest()
                    if code_app(item.name):
                        fichiers.append(item.name)
                        source_sha[item.name] = toutes_sources[item.name]
    home = dossier / 'home-build'
    home.mkdir(mode=0o700)
    config_user = home / 'npm-user-config'
    config_global = home / 'npm-global-config'
    config_user.touch(mode=0o600, exist_ok=False)
    config_global.touch(mode=0o600, exist_ok=False)
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(home.resolve()),
           'CC': '/usr/bin/gcc', 'CXX': '/usr/bin/g++',
           'NPM_CONFIG_USERCONFIG': str(config_user.resolve()),
           'NPM_CONFIG_GLOBALCONFIG': str(config_global.resolve())}
    for component in ('app', 'mode-studio'):
        for cmd in (['npm', 'ci', '--no-audit', '--no-fund'], ['npm', 'run', 'build']):
            npm_env = env
            if component == 'mode-studio' and cmd[1] == 'ci':
                npm_env = {**env, 'ONNXRUNTIME_NODE_INSTALL_CUDA': 'skip'}
            runner(cmd, cwd=dossier / component, env=npm_env, check=True)
        if not (dossier / component / 'dist/index.html').is_file() or not (dossier / component / 'node_modules').is_dir():
            raise ValueError(f'build incomplet : {component}')
        dist = dossier / component / 'dist'
        for parent, dirs, names in os.walk(dist, followlinks=False):
            for name in sorted(dirs + names):
                item = Path(parent) / name
                if item.is_symlink() or interdit(item.relative_to(dossier).as_posix()):
                    raise ValueError('artefact de build interdit')
                if item.is_file():
                    fichiers.append(item.relative_to(dossier).as_posix())
                elif not item.is_dir():
                    raise ValueError('artefact de build non ordinaire')
    for nom, attendu in toutes_sources.items():
        with (dossier / nom).open('rb') as contenu:
            if hashlib.file_digest(contenu, 'sha256').hexdigest() != attendu:
                raise ValueError('source Git modifiée pendant le build')
    with open(dossier / 'SOURCE_FILES.json', 'x', encoding='utf-8') as manifest:
        json.dump(sorted(fichiers), manifest)
    with open(dossier / 'SOURCE_HASHES.json', 'x', encoding='utf-8') as manifest:
        json.dump(source_sha, manifest, sort_keys=True)
    empreintes = {}
    for nom in fichiers:
        with (dossier / nom).open('rb') as contenu:
            empreintes[nom] = hashlib.file_digest(contenu, 'sha256').hexdigest()
    with open(dossier / 'FICHIERS_SHA256.json', 'x', encoding='utf-8') as manifest:
        json.dump(empreintes, manifest, sort_keys=True)
    with open(dossier / 'DEPENDANCES_SHA256', 'x', encoding='ascii') as f:
        f.write(empreinte_dependances(dossier / 'app/node_modules') + '\n')
    with open(dossier / 'BUILD_OK', 'x', encoding='utf-8') as marker:
        marker.write(sha + '\n')


def importer(archive_path, sha, revision, dossier):
    """Importe un artefact CI vérifié ; le marqueur n'est écrit qu'après contrôle."""
    if not re.fullmatch('[0-9a-f]{64}', sha) or not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('empreinte ou SHA Git invalide')
    if Path(archive_path).name.startswith('.env') or Path(archive_path).name == '.npmrc':
        raise ValueError('archive à nom interdit')
    verifier_ancetres(archive_path)
    dossier = Path(dossier)
    verifier_ancetres(dossier.parent)
    with open(archive_path, 'rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != sha:
            raise ValueError('artefact altéré')
        f.seek(0)
        dossier.mkdir(mode=0o700)
        seen, liens, fichiers_extraits, marqueur = set(), set(), set(), None
        with tarfile.open(fileobj=f, mode='r:*') as tar:
            for item in tar:
                p = PurePosixPath(item.name)
                if p.is_absolute() or not p.parts or p.parts[0] != 'release' or '..' in p.parts:
                    raise ValueError('chemin artefact interdit')
                rel = PurePosixPath(*p.parts[1:])
                if not rel.parts:
                    continue
                name = rel.as_posix()
                if name in seen:
                    raise ValueError('entrée artefact dupliquée')
                if any(name.startswith(lien + '/') for lien in liens):
                    raise ValueError('extraction à travers un lien interdite')
                seen.add(name)
                meta = name in ('BUILD_OK', 'SOURCE_FILES.json', 'SOURCE_HASHES.json', 'FICHIERS_SHA256.json', 'DEPENDANCES_SHA256', 'CI_COMMIT_SHA')
                if meta and (not item.isfile() or item.size > 16 * 1024 * 1024):
                    raise ValueError('métadonnée d’artefact invalide')
                dependance = name == 'app/node_modules' or name.startswith('app/node_modules/')
                dep_interdite = dependance and any(x.startswith('.env') or x in ('.npmrc', '.git', 'secrets') for x in rel.parts)
                studio_interdit = rel.parts[0] == 'mode-studio' and len(rel.parts) > 1 and rel.parts[1] != 'dist'
                if dep_interdite or studio_interdit or not meta and not dependance and interdit(name):
                    raise ValueError('contenu artefact interdit')
                if item.issym():
                    cible = posixpath.normpath(posixpath.join(posixpath.dirname(name), item.linkname))
                    if posixpath.isabs(item.linkname) or not name.startswith('app/node_modules/') or not cible.startswith('app/node_modules/'):
                        raise ValueError('lien artefact interdit')
                    liens.add(name)
                elif not (item.isdir() or item.isfile()):
                    raise ValueError('entrée artefact non ordinaire')
                if item.isfile() and not meta and not dependance:
                    fichiers_extraits.add(name)
                if name == 'BUILD_OK':
                    source = tar.extractfile(item)
                    if source is None:
                        raise ValueError('marqueur absent')
                    with source:
                        marqueur = source.read(128).decode('ascii')
                    continue
                item.name = name
                verifier_ancetres(dossier / name)
                tar.extract(item, path=dossier, filter='data')
        if not marqueur or not re.fullmatch('[0-9a-f]{64}\\n', marqueur):
            raise ValueError('marqueur de build invalide')
        if (dossier / 'CI_COMMIT_SHA').read_text(encoding='ascii').strip() != revision:
            raise ValueError('SHA Git de l’artefact incorrect')
        deps = (dossier / 'DEPENDANCES_SHA256').read_text(encoding='ascii').strip()
        if deps != empreinte_dependances(dossier / 'app/node_modules'):
            raise ValueError('dépendances de l’artefact altérées')
        with (dossier / 'SOURCE_FILES.json').open(encoding='utf-8') as f:
            fichiers = json.load(f)
        with (dossier / 'FICHIERS_SHA256.json').open(encoding='utf-8') as f:
            empreintes = json.load(f)
        if not isinstance(fichiers, list) or not isinstance(empreintes, dict) or set(fichiers) != set(empreintes) or set(fichiers) != fichiers_extraits:
            raise ValueError('manifestes de fichiers incohérents')
        if not {'app/dist/index.html', 'mode-studio/dist/index.html'} <= set(fichiers):
            raise ValueError('artefact incomplet')
        for nom, attendu in empreintes.items():
            target = chemin(dossier, nom)
            verifier_ancetres(target)
            with target.open('rb') as contenu:
                if hashlib.file_digest(contenu, 'sha256').hexdigest() != attendu:
                    raise ValueError('fichier de l’artefact altéré')
        with (dossier / 'SOURCE_HASHES.json').open(encoding='utf-8') as f:
            sources = json.load(f)
        if (not isinstance(sources, dict) or set(sources) != {nom for nom in fichiers if nom.startswith('app/') and not nom.startswith('app/dist/')}
                or any(empreintes.get(nom) != sha for nom, sha in sources.items())):
            raise ValueError('sources Git incohérentes')
        with (dossier / 'BUILD_OK').open('x', encoding='ascii') as marker:
            marker.write(marqueur)


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == 'archive':
        print(archive(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])))
    elif len(sys.argv) == 5 and sys.argv[1] == 'construire':
        construire(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    elif len(sys.argv) == 6 and sys.argv[1] == 'importer':
        importer(Path(sys.argv[2]), sys.argv[3], sys.argv[4], Path(sys.argv[5]))
    else:
        raise SystemExit('usage : preparer_release.py archive DEPOT SHA_GIT ARCHIVE | construire ARCHIVE SHA256 DOSSIER_NEUF | importer ARTEFACT SHA256 SHA_GIT DOSSIER_NEUF')
