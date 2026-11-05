#!/usr/bin/env python3
"""Prépare une release isolée ; ne modifie jamais l'application active."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile

from transaction_release import empreinte_dependances


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
                 (p.parts[1] in ('.dockerignore', '.gitignore', 'LICENSE', 'vitest.director.ci.config.mjs')
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
    if not re.fullmatch('[0-9a-f]{64}', sha):
        raise ValueError('SHA-256 complet requis')
    fichiers, source_sha = [], {}
    with open(archive_path, 'rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest() != sha:
            raise ValueError('archive altérée')
        f.seek(0)
        dossier = Path(dossier)
        dossier.mkdir(mode=0o700)  # exclusif : une release existante n'est jamais remplacée
        with tarfile.open(fileobj=f, mode='r:') as tar:
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
                    if code_app(item.name):
                        fichiers.append(item.name)
                        with target.open('rb') as contenu:
                            source_sha[item.name] = hashlib.file_digest(contenu, 'sha256').hexdigest()
    home = dossier / 'home-build'
    home.mkdir(mode=0o700)
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(home.resolve()),
           'NPM_CONFIG_USERCONFIG': '/dev/null', 'NPM_CONFIG_GLOBALCONFIG': '/dev/null'}
    for component in ('app', 'mode-studio'):
        for cmd in (['npm', 'ci', '--no-audit', '--no-fund'], ['npm', 'run', 'build']):
            runner(cmd, cwd=dossier / component, env=env, check=True)
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
    for nom, attendu in source_sha.items():
        with (dossier / nom).open('rb') as contenu:
            if hashlib.file_digest(contenu, 'sha256').hexdigest() != attendu:
                raise ValueError('source Git modifiée pendant le build')
    with open(dossier / 'SOURCE_FILES.json', 'x', encoding='utf-8') as manifest:
        json.dump(sorted(fichiers), manifest)
    with open(dossier / 'SOURCE_HASHES.json', 'x', encoding='utf-8') as manifest:
        json.dump(source_sha, manifest, sort_keys=True)
    with open(dossier / 'DEPENDANCES_SHA256', 'x', encoding='ascii') as f:
        f.write(empreinte_dependances(dossier / 'app/node_modules') + '\n')
    with open(dossier / 'BUILD_OK', 'x', encoding='utf-8') as marker:
        marker.write(sha + '\n')


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == 'archive':
        print(archive(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])))
    elif len(sys.argv) == 5 and sys.argv[1] == 'construire':
        construire(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    else:
        raise SystemExit('usage : preparer_release.py archive DEPOT SHA_GIT ARCHIVE | construire ARCHIVE SHA256 DOSSIER_NEUF')
