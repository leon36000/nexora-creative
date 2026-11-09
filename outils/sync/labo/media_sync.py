"""Provenance d’entrées Sync : banc Eleven4 séparé des prises validées par le serveur.

Ce module ne choisit pas de voix ni de fournisseur. Le chemin `server-media`
est créé seulement par l’adaptateur appelé après résolution serveur des deux prises.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat

SCHEMA_SERVER_MEDIA = 'nexora.sync.server-media.v1'
ELEVEN4 = 'elevenlabs/eleven-v4'
HEX = re.compile(r'[0-9a-f]{64}\Z')
MAX_MEDIA_BYTES = 4 * 1024 ** 3
VIDEO_NAME = 'video-entree.mp4'
AUDIO_NAME = 'audio-entree.wav'
AUDIO_ORIGINAL = 'audio-original.mp3'


class ErreurEntree(ValueError):
    pass


def empreinte(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloc)
    return h.hexdigest()


def _paires(paires):
    out = {}
    for cle, valeur in paires:
        if cle in out:
            raise ErreurEntree('clé JSON dupliquée')
        out[cle] = valeur
    return out


def _rejeter_nombre_non_fini(_value: str) -> None:
    raise ErreurEntree('nombre non fini')


def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf8'), object_pairs_hook=_paires,
                          parse_constant=_rejeter_nombre_non_fini)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ErreurEntree('provenance JSON invalide') from exc


def _sha(sha: object) -> bool:
    return isinstance(sha, str) and HEX.fullmatch(sha) is not None


def _fichier_exact(run: Path, name: str, sha: str, nbytes: int | None = None) -> None:
    path = run / name
    if path.is_symlink() or not path.is_file():
        raise ErreurEntree('média de tâche absent ou non régulier')
    st = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(st.st_mode) or st.st_size <= 0 or st.st_size > MAX_MEDIA_BYTES:
        raise ErreurEntree('taille de média invalide')
    if nbytes is not None and (isinstance(nbytes, bool) or not isinstance(nbytes, int) or st.st_size != nbytes):
        raise ErreurEntree('taille de média différente')
    if not _sha(sha) or empreinte(path) != sha:
        raise ErreurEntree('empreinte différente')


def _verifier_provenance_eleven4(run: Path, p: dict) -> tuple[str, dict[str, str]]:
    files = p.get('fichiers')
    required = (AUDIO_ORIGINAL, AUDIO_NAME, VIDEO_NAME)
    if not isinstance(files, dict) or any(not _sha(files.get(n)) for n in required):
        raise ErreurEntree('provenance Eleven4 incomplète')
    for name in required:
        _fichier_exact(run, name, files[name])
    return 'eleven4-bench', {n: files[n] for n in required}


def _verifier_provenance_serveur(run: Path, p: dict) -> tuple[str, dict[str, str]]:
    if p.get('schema') != SCHEMA_SERVER_MEDIA:
        raise ErreurEntree('schéma de provenance non pris en charge')
    if set(p) != {'schema', 'source_ids', 'fichiers'} or 'modele_demande' in p or 'voix' in p:
        raise ErreurEntree('champs de provenance serveur inattendus')
    ids = p.get('source_ids')
    if not isinstance(ids, dict) or set(ids) != {'video', 'audio'} or any(
        isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in ids.values()
    ):
        raise ErreurEntree('identifiants de prises serveur invalides')
    files = p.get('fichiers')
    if not isinstance(files, dict) or set(files) != {VIDEO_NAME, AUDIO_NAME}:
        raise ErreurEntree('médias serveur incomplets')
    hashes = {}
    for name in (VIDEO_NAME, AUDIO_NAME):
        item = files[name]
        if not isinstance(item, dict) or set(item) != {'sha256', 'bytes'} or not _sha(item['sha256']):
            raise ErreurEntree('référence média serveur invalide')
        if isinstance(item['bytes'], bool) or not isinstance(item['bytes'], int) or item['bytes'] <= 0:
            raise ErreurEntree('taille média serveur invalide')
        _fichier_exact(run, name, item['sha256'], item['bytes'])
        hashes[name] = item['sha256']
    if os.path.lexists(run / AUDIO_ORIGINAL):
        raise ErreurEntree('audio-original réservé au banc Eleven4')
    return 'server-media', hashes


def verifier_provenance(run: Path, sha_attendu: str) -> tuple[str, dict[str, str]]:
    """Vérifie une provenance existante sans confondre banc vocal et média générique."""
    path = run / 'provenance-entrees.json'
    if path.is_symlink() or not path.is_file() or not _sha(sha_attendu) or empreinte(path) != sha_attendu:
        raise ErreurEntree('provenance absente ou empreinte différente')
    p = _json(path)
    if not isinstance(p, dict):
        raise ErreurEntree('provenance invalide')
    if p.get('modele_demande') == ELEVEN4:
        return _verifier_provenance_eleven4(run, p)
    return _verifier_provenance_serveur(run, p)


def ecrire_provenance_serveur(run: Path, video_take_id: int, audio_take_id: int) -> str:
    """Écrit une provenance pour des médias déjà copiés par le worker depuis des prises résolues par le serveur."""
    for value in (video_take_id, audio_take_id):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ErreurEntree('identifiant de prise invalide')
    if os.path.lexists(run / AUDIO_ORIGINAL):
        raise ErreurEntree('audio-original réservé au banc Eleven4')
    files = {}
    for name in (VIDEO_NAME, AUDIO_NAME):
        path = run / name
        st = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode) or path.is_symlink() or st.st_size <= 0 or st.st_size > MAX_MEDIA_BYTES:
            raise ErreurEntree('copie média serveur invalide')
        files[name] = {'sha256': empreinte(path), 'bytes': st.st_size}
    obj = {'schema': SCHEMA_SERVER_MEDIA,
           'source_ids': {'video': video_take_id, 'audio': audio_take_id},
           'fichiers': files}
    data = (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    fd = os.open(run / 'provenance-entrees.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as out:
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    dir_fd = os.open(run, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return hashlib.sha256(data).hexdigest()
