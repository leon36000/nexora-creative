"""Worker Sync R&D local : HTTP/1.1 sur socket Unix, SQLite durable, aucun retry.

Le client est le serveur Sync de confiance. Il transmet des identifiants de prises
et des assertions de métadonnées; les chemins reçus ne sont jamais ouverts ni
persistés. Les seuls chemins utilisables proviennent du registre serveur local.
Le service garde l’acceptation et le dispatch séparés : SQLite confirme le job
avant que la boucle du worker puisse planifier ou lancer une capsule.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import sqlite3
import stat
import struct
import subprocess
import sys
import threading
import time
from typing import Callable, Mapping
import uuid

from outils.sync.labo import media_sync, sync_worker_adapter as adapter

PROTOCOL = 'nexora.sync.worker.v1'
REQUEST_SCHEMA = 'nexora.sync.worker-request.v1'
RESULT_SCHEMA = 'nexora.sync.worker-result.v1'
MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 64 * 1024
MAX_HEADER_BYTES = 8 * 1024
MAX_HEADERS = 40
MAX_JOB_ID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z', re.I)
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
MAX_SAFE_INTEGER = (1 << 53) - 1
ACTIVE_STATES = ('queued', 'planning', 'prepared', 'dispatch_unknown')


class RpcError(ValueError):
    """Erreur de protocole sans données sensibles dans son texte."""

_CHILD_ENV = {'PATH': '/usr/bin:/bin', 'PYTHONNOUSERSITE': '1',
              'PYTHONDONTWRITEBYTECODE': '1'}
_CHILD_MODULE = 'outils.sync.labo.sync_worker_rpc'


def _known_source_root() -> Path:
    source = Path(__file__).resolve(strict=True)
    root = source.parents[3]
    expected = root / 'outils' / 'sync' / 'labo' / 'sync_worker_rpc.py'
    if source != expected or not (root / 'outils' / 'sync' / 'labo' / '__init__.py').is_file():
        raise RpcError('source du worker non reconnu')
    return root


def _run_child_process(argv: list[str]) -> int:
    """Exécute un argv interne, sans shell ni environnement hérité."""
    if (not isinstance(argv, list) or not argv or not Path(sys.executable).is_absolute() or
            argv[0] != sys.executable or any(not isinstance(arg, str) or '\0' in arg for arg in argv)):
        raise RpcError('commande enfant invalide')
    completed = subprocess.run(
        argv, cwd=_known_source_root(), env=dict(_CHILD_ENV),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, check=False,
    )
    return completed.returncode



@dataclass(frozen=True)
class TakeRecord:
    organisation_id: str
    take_id: int
    kind: str
    path: Path
    sha256: str
    bytes: int
    duration_seconds: float
    fps: float | None = None
    sample_rate: int | None = None

    def as_resolved(self) -> adapter.PriseResolue:
        return adapter.PriseResolue(self.take_id, self.path, self.sha256, self.bytes)


class AllowlistResolver:
    """Index privé fourni par le registre serveur, jamais par le message RPC."""

    def __init__(self, records: tuple[TakeRecord, ...] | list[TakeRecord]):
        self._records: dict[tuple[str, int], TakeRecord] = {}
        for record in records:
            if (not isinstance(record, TakeRecord) or not record.organisation_id or
                    isinstance(record.take_id, bool) or not isinstance(record.take_id, int) or
                    record.take_id <= 0 or record.kind not in {'video', 'audio'} or
                    (record.organisation_id, record.take_id) in self._records):
                raise RpcError('registre de prises invalide')
            self._records[(record.organisation_id, record.take_id)] = record

    def resolve(self, organisation_id: str, take_id: int, kind: str) -> TakeRecord:
        record = self._records.get((organisation_id, take_id))
        if record is None or record.kind != kind:
            raise RpcError('prise non autorisée')
        return record

    def medias(self, organisation_id: str, video_id: int, audio_id: int) -> adapter.MediasResolus:
        if video_id == audio_id:
            raise RpcError('prises vidéo/audio distinctes requises')
        return adapter.MediasResolus(
            self.resolve(organisation_id, video_id, 'video').as_resolved(),
            self.resolve(organisation_id, audio_id, 'audio').as_resolved(),
        )

    def verifier_assertions(self, request: dict) -> None:
        org = request['organisationId']
        video = self.resolve(org, request['video']['takeId'], 'video')
        audio = self.resolve(org, request['audio']['takeId'], 'audio')
        for claim, record, side in ((request['video'], video, 'video'),
                                    (request['audio'], audio, 'audio')):
            if claim['sha256'] != record.sha256 or claim['bytes'] != record.bytes:
                raise RpcError('empreinte ou taille de prise différente')
            if claim['durationSeconds'] != record.duration_seconds:
                raise RpcError('durée de prise différente')
            expected_extra = {'fps': record.fps} if side == 'video' else {'sampleRate': record.sample_rate}
            for key, expected in expected_extra.items():
                if expected is None or claim.get(key) != expected:
                    raise RpcError('métadonnées de prise différentes')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RpcError('clé JSON dupliquée')
        result[key] = value
    return result


def _json_load(data: bytes):
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=lambda _v: (_ for _ in ()).throw(RpcError('valeur JSON non finie')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RpcError('JSON invalide') from exc


def _json_dump(value: object) -> bytes:
    try:
        data = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise RpcError('réponse JSON invalide') from exc
    if len(data) > MAX_RESPONSE_BYTES:
        raise RpcError('réponse trop grande')
    return data


def _finite_positive(value: object) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float)) and
            math.isfinite(value) and value > 0)


def _safe_positive_integer(value: object) -> bool:
    return (not isinstance(value, bool) and isinstance(value, int) and
            0 < value <= MAX_SAFE_INTEGER)


def _exact_keys(value: object, required: set[str], optional: set[str] = frozenset()) -> bool:
    return isinstance(value, dict) and required.issubset(value) and set(value).issubset(required | optional)


def _parse_request(body: object) -> dict:
    top = {'schema', 'jobId', 'engine', 'organisationId', 'createdBy', 'video', 'audio', 'manifest'}
    if not _exact_keys(body, top) or set(body) != top:
        raise RpcError('requête Sync invalide')
    if (body['schema'] != REQUEST_SCHEMA or not isinstance(body['jobId'], str) or
            MAX_JOB_ID.fullmatch(body['jobId']) is None or
            not isinstance(body['engine'], str) or body['engine'] not in adapter.ENGINE_IDS or
            not isinstance(body['organisationId'], str) or not 1 <= len(body['organisationId']) <= 128 or
            not isinstance(body['createdBy'], str) or not 1 <= len(body['createdBy']) <= 128):
        raise RpcError('requête Sync invalide')
    for side, required, optional in (
        ('video', {'takeId', 'path', 'sha256', 'bytes', 'durationSeconds', 'fps'}, set()),
        ('audio', {'takeId', 'path', 'sha256', 'bytes', 'durationSeconds', 'sampleRate'}, set()),
    ):
        claim = body[side]
        if not _exact_keys(claim, required) or set(claim) != required:
            raise RpcError('métadonnées de prise invalides')
        if (not _safe_positive_integer(claim['takeId']) or
                not isinstance(claim['path'], str) or len(claim['path']) > 4096 or '\0' in claim['path'] or
                not isinstance(claim['sha256'], str) or SHA256.fullmatch(claim['sha256']) is None or
                not _safe_positive_integer(claim['bytes']) or claim['bytes'] > media_sync.MAX_MEDIA_BYTES or
                not _finite_positive(claim['durationSeconds'])):
            raise RpcError('métadonnées de prise invalides')
    if not _finite_positive(body['video']['fps']) or not _safe_positive_integer(body['audio']['sampleRate']):
        raise RpcError('métadonnées de prise invalides')
    manifest = body['manifest']
    keys = {'schema', 'id', 'engine', 'videoTakeId', 'audioTakeId', 'inputs',
            'state', 'researchOnly', 'productAvailable', 'humanReview', 'quality'}
    if (not _exact_keys(manifest, keys) or set(manifest) != keys or
            manifest['schema'] != 'nexora.sync.job.v1' or manifest['id'] != body['jobId'] or
            manifest['engine'] != body['engine'] or
            manifest['videoTakeId'] != body['video']['takeId'] or
            manifest['audioTakeId'] != body['audio']['takeId'] or
            manifest['inputs'] != {'videoSha256': body['video']['sha256'], 'audioSha256': body['audio']['sha256']} or
            manifest['state'] != 'dispatching' or manifest['researchOnly'] is not True or
            manifest['productAvailable'] is not False or manifest['humanReview'] != 'pending' or
            manifest['quality'] != 'not_evaluated'):
        raise RpcError('manifeste Sync invalide')
    # Les chemins servent uniquement d’assertions côté appelant; les supprimer avant
    # empreinte/persistance permet un stockage commun PC6/PC1 sans chemin client.
    safe = json.loads(json.dumps(body, ensure_ascii=False, allow_nan=False))
    safe['video'].pop('path')
    safe['audio'].pop('path')
    return safe


def _trusted_dir(path: Path, label: str) -> None:
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise RpcError(f'{label} absent ou lié')
    st = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise RpcError(f'{label} doit être privé à 0700')


def _private_file(path: Path, label: str, allow_missing: bool = False) -> None:
    try:
        st = path.lstat()
    except FileNotFoundError:
        if allow_missing:
            return
        raise RpcError(f'{label} absent')
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or
            st.st_mode & 0o077 or st.st_nlink != 1):
        raise RpcError(f'{label} doit être un fichier privé régulier')


class SyncWorkerRpc:
    """Serveur HTTP Unix à file durable; `process_one()` est explicitement séparé."""

    def __init__(self, state_root: Path, socket_path: Path, media_roots: tuple[Path, ...],
                 resolver: AllowlistResolver, engines: Mapping[str, adapter.Moteur],
                 engine_limits: Mapping[str, dict], worker_id: str = 'nexora-sync-rnd',
                 max_concurrent: int = 1, expected_uid: int | None = None,
                 principal_allowed: Callable[[int, str, str], bool] | None = None):
        self.state_root = Path(state_root)
        self.socket_path = Path(socket_path)
        self.task_root = self.state_root / 'tasks'
        self.db_path = self.state_root / 'worker.sqlite3'
        self.media_roots = tuple(Path(p) for p in media_roots)
        self.resolver = resolver
        self.engines = dict(engines)
        self.engine_limits = {k: dict(v) for k, v in engine_limits.items()}
        self.worker_id = worker_id
        self.max_concurrent = max_concurrent
        self.expected_uid = os.getuid() if expected_uid is None else expected_uid
        self.principal_allowed = principal_allowed or (
            lambda uid, org, user: uid == self.expected_uid and bool(org) and bool(user))
        self._db_lock = threading.RLock()
        self._process_lock = threading.Lock()
        self._active = False
        self._processor_thread = None
        self._listener: socket.socket | None = None
        self._validate_configuration()
        _trusted_dir(self.state_root, 'racine du worker')
        if (not self.socket_path.is_absolute() or self.socket_path.parent.is_symlink() or
                len(os.fsencode(self.socket_path)) > 107):
            raise RpcError('chemin de socket Sync invalide')
        _trusted_dir(self.socket_path.parent, 'répertoire de socket')
        if self.socket_path.exists() or self.socket_path.is_symlink():
            raise RpcError('socket existante refusée; utiliser une nouvelle racine privée')
        if not self.task_root.exists():
            os.mkdir(self.task_root, 0o700)
        _trusted_dir(self.task_root, 'racine des tâches')
        self._open_database()

    def _validate_configuration(self):
        if (not self.worker_id or len(self.worker_id) > 64 or
                re.fullmatch(r'[A-Za-z0-9._-]+', self.worker_id) is None or
                self.max_concurrent != 1 or not self.engines or
                not set(self.engines).issubset(adapter.ENGINE_IDS) or
                set(self.engine_limits) != set(self.engines) or not self.media_roots):
            raise RpcError('configuration du worker invalide')
        for name, limits in self.engine_limits.items():
            if (not _finite_positive(limits.get('maxDurationSeconds')) or
                    not _safe_positive_integer(limits.get('maxInputBytes')) or
                    limits['maxInputBytes'] > media_sync.MAX_MEDIA_BYTES):
                raise RpcError('limites moteur invalides')
        for root in self.media_roots:
            if not Path(root).is_absolute():
                raise RpcError('racine média non absolue')

    def _open_database(self):
        _private_file(self.db_path, 'base SQLite', allow_missing=True)
        old_mask = os.umask(0o077)
        try:
            if not self.db_path.exists():
                fd = os.open(self.db_path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.close(fd)
            _private_file(self.db_path, 'base SQLite')
            self._db = sqlite3.connect(self.db_path, timeout=5, isolation_level=None,
                                       check_same_thread=False)
            self._db.execute('PRAGMA journal_mode=WAL')
            self._db.execute('PRAGMA synchronous=FULL')
            self._db.execute('PRAGMA busy_timeout=5000')
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS jobs ("
                "job_id TEXT PRIMARY KEY, request_sha256 TEXT NOT NULL, request_json TEXT NOT NULL, "
                "organisation_id TEXT NOT NULL, created_by TEXT NOT NULL, engine TEXT NOT NULL, "
                "video_take_id INTEGER NOT NULL, audio_take_id INTEGER NOT NULL, "
                "video_sha256 TEXT NOT NULL, audio_sha256 TEXT NOT NULL, "
                "state TEXT NOT NULL CHECK(state IN ('queued','planning','prepared','dispatch_unknown','completed','failed')), "
                "created_at REAL NOT NULL, updated_at REAL NOT NULL, error_code TEXT, "
                "plan_sha256 TEXT, result_json TEXT, output_bytes INTEGER, run_name TEXT, "
                "acknowledged INTEGER NOT NULL DEFAULT 0 CHECK(acknowledged IN (0,1)))"
            )
            self._db.execute('CREATE INDEX IF NOT EXISTS jobs_state_created ON jobs(state,created_at)')
            for suffix in ('', '-wal', '-shm'):
                candidate = Path(str(self.db_path) + suffix)
                if candidate.exists():
                    os.chmod(candidate, 0o600, follow_symlinks=False)
                    _private_file(candidate, 'fichier SQLite')
            dir_fd = os.open(self.state_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        finally:
            os.umask(old_mask)

    def _transaction(self, fn):
        with self._db_lock:
            self._db.execute('BEGIN IMMEDIATE')
            try:
                result = fn()
                self._db.execute('COMMIT')
            except BaseException:
                self._db.execute('ROLLBACK')
                raise
            self._verify_db_files()
            return result

    def _verify_db_files(self):
        for suffix in ('', '-wal', '-shm'):
            candidate = Path(str(self.db_path) + suffix)
            if candidate.exists():
                os.chmod(candidate, 0o600, follow_symlinks=False)
                _private_file(candidate, 'fichier SQLite')

    def _lookup(self, job_id: str):
        with self._db_lock:
            row = self._db.execute('SELECT * FROM jobs WHERE job_id=?', (job_id,)).fetchone()
        return row

    def capabilities(self) -> dict:
        ready = (self._active and self._processor_thread is not None and
                 self._processor_thread.is_alive() and bool(self.engines))
        engine_caps = {}
        for name in sorted(adapter.ENGINE_IDS):
            limits = self.engine_limits.get(name)
            if limits is not None and name in self.engines:
                engine_caps[name] = {
                    'ready': ready,
                    'maxDurationSeconds': limits['maxDurationSeconds'],
                    'maxInputBytes': limits['maxInputBytes'],
                }
        return {'protocol': PROTOCOL, 'workerId': self.worker_id,
                'ready': ready, 'maxConcurrent': self.max_concurrent, 'engines': engine_caps}

    def _request_matches_registry(self, request: dict) -> None:
        self.resolver.verifier_assertions(request)

    def enqueue(self, raw_request: object, peer_uid: int) -> tuple[int, dict]:
        try:
            request = _parse_request(raw_request)
        except RpcError:
            return 400, {'accepted': False, 'errorCode': 'input_rejected'}
        job_id = request['jobId']
        if not self.principal_allowed(peer_uid, request['organisationId'], request['createdBy']):
            return 200, {'accepted': False, 'jobId': job_id, 'errorCode': 'input_rejected'}
        engine = request['engine']
        limits = self.engine_limits.get(engine)
        if (not self.capabilities()['ready'] or engine not in self.engines or limits is None):
            return 200, {'accepted': False, 'jobId': job_id, 'errorCode': 'engine_unavailable'}
        if any(request[side]['bytes'] > limits['maxInputBytes'] or
               request[side]['durationSeconds'] > limits['maxDurationSeconds']
               for side in ('video', 'audio')):
            return 200, {'accepted': False, 'jobId': job_id, 'errorCode': 'input_rejected'}
        try:
            self._request_matches_registry(request)
        except RpcError:
            return 200, {'accepted': False, 'jobId': job_id, 'errorCode': 'input_rejected'}
        encoded = json.dumps(request, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False)
        request_sha = hashlib.sha256(encoded.encode('utf-8')).hexdigest()

        def insert():
            row = self._db.execute('SELECT request_sha256 FROM jobs WHERE job_id=?', (job_id,)).fetchone()
            if row:
                if row[0] != request_sha:
                    return 'conflict'
                return 'existing'
            n = self._db.execute(
                "SELECT COUNT(*) FROM jobs WHERE state IN ('queued','planning','prepared','dispatch_unknown')"
            ).fetchone()[0]
            if n >= self.max_concurrent:
                return 'full'
            now = time.time()
            self._db.execute(
                'INSERT INTO jobs(job_id,request_sha256,request_json,organisation_id,created_by,engine,'
                'video_take_id,audio_take_id,video_sha256,audio_sha256,state,created_at,updated_at,run_name,acknowledged) '
                "VALUES(?,?,?,?,?,?,?,?,?,?,'queued',?,?,?,0)",
                (job_id, request_sha, encoded, request['organisationId'], request['createdBy'], engine,
                 request['video']['takeId'], request['audio']['takeId'], request['video']['sha256'],
                 request['audio']['sha256'], now, now, f'sync-{job_id}'))
            return 'created'

        status = self._transaction(insert)
        if status == 'conflict':
            return 409, {'accepted': False, 'jobId': job_id, 'errorCode': 'idempotency_conflict'}
        if status == 'full':
            return 200, {'accepted': False, 'jobId': job_id, 'errorCode': 'worker_busy'}
        # Commit with synchronous=FULL and WAL is complete before this ACK is constructed.
        return 202, {'accepted': True, 'jobId': job_id}

    def inspect(self, job_id: str) -> tuple[int, dict]:
        if MAX_JOB_ID.fullmatch(job_id) is None:
            return 200, {'state': 'not_found'}
        row = self._lookup(job_id)
        if row is None:
            return 200, {'state': 'not_found'}
        if row[18] != 1:
            return 503, {'state': 'unknown', 'errorCode': 'acceptance_unconfirmed'}
        state = row[10]
        if state in {'queued', 'planning', 'prepared'}:
            return 200, {'state': 'queued'}
        if state == 'dispatch_unknown':
            if row[13] is not None:
                return 200, {'state': 'dispatch_unknown', 'errorCode': 'engine_failed'}
            return 200, {'state': 'running', 'progress': 0}
        if state == 'failed':
            return 200, {'state': 'failed', 'errorCode': row[13] or 'engine_failed'}
        result = json.loads(row[15]) if row[15] else None
        if not isinstance(result, dict):
            return 200, {'state': 'failed', 'errorCode': 'engine_failed'}
        return 200, {'state': 'completed', 'result': result}

    def _resolve_job_medias(self, request: dict) -> adapter.MediasResolus:
        self._request_matches_registry(request)
        return self.resolver.medias(request['organisationId'],
                                    request['video']['takeId'], request['audio']['takeId'])

    def process_one(self) -> str | None:
        """Traite au plus un job; aucun état dispatch_unknown n’est sélectionné."""
        if not self._process_lock.acquire(blocking=False):
            return None
        try:
            def claim():
                row = self._db.execute(
                    "SELECT job_id,state,request_json,engine,organisation_id FROM jobs "
                    "WHERE state IN ('queued','prepared') AND acknowledged=1 "
                    "ORDER BY CASE state WHEN 'prepared' THEN 0 ELSE 1 END,created_at,job_id LIMIT 1"
                ).fetchone()
                if row is None:
                    return None
                job_id, state, request_json, engine, org = row
                if state == 'queued':
                    self._db.execute("UPDATE jobs SET state='planning',updated_at=? WHERE job_id=? AND state='queued'",
                                     (time.time(), job_id))
                return job_id, state, request_json, engine, org
            item = self._transaction(claim)
            if item is None:
                return None
            job_id, state, request_json, engine, org = item
            request = json.loads(request_json)
            if state == 'queued':
                try:
                    self._request_matches_registry(request)
                    resolver = lambda video_id, audio_id: self.resolver.medias(org, video_id, audio_id)
                    prepared = adapter.preparer_depuis_ids(
                        self.task_root, self.media_roots, request['video']['takeId'],
                        request['audio']['takeId'], job_id, engine, self.engines, resolver)
                except BaseException as exc:
                    self._set_failed(job_id, 'input_rejected' if isinstance(exc, (RpcError, adapter.ErreurTache)) else 'engine_failed')
                    return job_id
                plan_sha = prepared.get('plan_sha256')
                if prepared.get('status') != 'prepared' or not isinstance(plan_sha, str) or SHA256.fullmatch(plan_sha) is None:
                    self._set_failed(job_id, 'engine_failed')
                    return job_id
                self._transaction(lambda: self._db.execute(
                    "UPDATE jobs SET state='prepared',plan_sha256=?,updated_at=? WHERE job_id=? AND state='planning'",
                    (plan_sha, time.time(), job_id)))
            return self._dispatch_prepared(job_id)
        finally:
            self._process_lock.release()

    def _set_failed(self, job_id: str, code: str) -> None:
        allowed = {'input_rejected', 'engine_failed', 'worker_timeout'}
        if code not in allowed:
            code = 'engine_failed'
        self._transaction(lambda: self._db.execute(
            "UPDATE jobs SET state='failed',error_code=?,updated_at=? WHERE job_id=? AND state IN ('planning','prepared')",
            (code, time.time(), job_id)))

    def _dispatch_prepared(self, job_id: str) -> str:
        def begin():
            row = self._db.execute('SELECT state,plan_sha256,engine FROM jobs WHERE job_id=?', (job_id,)).fetchone()
            if row is None or row[0] != 'prepared':
                return None
            self._db.execute("UPDATE jobs SET state='dispatch_unknown',updated_at=? WHERE job_id=? AND state='prepared'",
                             (time.time(), job_id))
            return row[1], row[2]
        claimed = self._transaction(begin)
        if claimed is None:
            return job_id
        plan_sha, engine_id = claimed
        # L’état ambigu est committé avant de démarrer un Python dédié. Le thread
        # HTTP/consommateur n'appelle jamais la capsule ni signal.signal directement.
        try:
            argv = [sys.executable, '-m', _CHILD_MODULE, '--execute-task',
                    '--task-root', str(self.task_root), '--task-id', job_id,
                    '--engine', engine_id, '--plan-sha256', plan_sha]
            return_code = _run_child_process(argv)
            if return_code != 0:
                raise RuntimeError('processus enfant non confirmé')
            run = self.task_root / f'sync-{job_id}'
            child_state = adapter._lire_json(run / adapter.TASK_STATE)
            if (child_state.get('task_id') != job_id or child_state.get('engine_id') != engine_id or
                    child_state.get('plan_sha256') != plan_sha):
                raise RpcError('reçu enfant différent du plan')
            outcome = {'status': child_state.get('status')}
        except BaseException as exc:
            self._transaction(lambda: self._db.execute(
                "UPDATE jobs SET error_code=?,updated_at=? WHERE job_id=? AND state='dispatch_unknown'",
                ('worker_timeout' if 'Timeout' in type(exc).__name__ else 'engine_failed', time.time(), job_id)))
            return job_id
        try:
            run = self.task_root / f'sync-{job_id}'
            state_data = adapter._lire_json(run / adapter.TASK_STATE)
            status = outcome.get('status')
            status_to_av = {'av_validated_unjudged': 'pass', 'av_rejected': 'refused'}
            av_status = status_to_av.get(status)
            output = run / 'sortie.mp4'
            output_sha = state_data.get('output_sha256')
            if (state_data.get('status') != status or state_data.get('plan_sha256') != plan_sha or
                    av_status is None or output.is_symlink() or not output.is_file() or
                    output.stat(follow_symlinks=False).st_size <= 0 or
                    not isinstance(output_sha, str) or SHA256.fullmatch(output_sha) is None or
                    adapter._sha(output) != output_sha):
                raise RpcError('résultat audiovisuel non confirmé')
            output_bytes = output.stat(follow_symlinks=False).st_size
            row = self._lookup(job_id)
            request = json.loads(row[2])
            result = {
                'schema': RESULT_SCHEMA, 'jobId': job_id, 'engine': row[5],
                'inputs': {'videoSha256': row[8], 'audioSha256': row[9]},
                'outputSha256': output_sha, 'outputBytes': output_bytes,
                'avStatus': av_status, 'researchOnly': True, 'productAvailable': False,
            }
            if request['engine'] != result['engine']:
                raise RpcError('résultat moteur différent')
            encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
            self._transaction(lambda: self._db.execute(
                "UPDATE jobs SET state='completed',result_json=?,output_bytes=?,error_code=NULL,updated_at=? "
                "WHERE job_id=? AND state='dispatch_unknown'",
                (encoded, output_bytes, time.time(), job_id)))
        except BaseException as exc:
            # L’inférence a commencé; même un reçu invalide n’autorise pas le rejeu.
            self._transaction(lambda: self._db.execute(
                "UPDATE jobs SET error_code=?,updated_at=? WHERE job_id=? AND state='dispatch_unknown'",
                ('engine_failed', time.time(), job_id)))
        return job_id

    def _read_http(self, conn: socket.socket) -> tuple[str, str, bytes]:
        conn.settimeout(5.0)
        data = bytearray()
        marker = -1
        while marker < 0:
            chunk = conn.recv(2048)
            if not chunk:
                raise RpcError('en-têtes HTTP incomplets')
            data.extend(chunk)
            if len(data) > MAX_HEADER_BYTES + MAX_REQUEST_BYTES:
                raise RpcError('requête trop grande')
            marker = data.find(b'\r\n\r\n')
            if marker < 0 and len(data) > MAX_HEADER_BYTES:
                raise RpcError('en-têtes trop grands')
        header_raw = bytes(data[:marker])
        body = bytes(data[marker + 4:])
        try:
            lines = header_raw.decode('ascii').split('\r\n')
        except UnicodeDecodeError as exc:
            raise RpcError('en-têtes invalides') from exc
        if not lines or len(lines) - 1 > MAX_HEADERS:
            raise RpcError('en-têtes invalides')
        parts = lines[0].split(' ')
        if len(parts) != 3 or parts[2] != 'HTTP/1.1' or not parts[0] or not parts[1].startswith('/'):
            raise RpcError('ligne HTTP invalide')
        headers = {}
        for line in lines[1:]:
            if ':' not in line:
                raise RpcError('en-tête HTTP invalide')
            key, value = line.split(':', 1)
            key = key.strip().lower()
            if not key or key in headers or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in key):
                raise RpcError('en-tête HTTP dupliqué ou invalide')
            headers[key] = value.strip()
        if 'transfer-encoding' in headers or 'expect' in headers:
            raise RpcError('encodage HTTP non pris en charge')
        if 'content-length' in headers:
            value = headers['content-length']
            if not value.isdigit() or len(value) > 10:
                raise RpcError('longueur HTTP invalide')
            length = int(value)
        else:
            length = 0
        method, path = parts[:2]
        if method == 'POST' and length == 0:
            raise RpcError('corps requis')
        if method != 'POST' and length != 0:
            raise RpcError('corps HTTP inattendu')
        if length > MAX_REQUEST_BYTES:
            raise RpcError('requête trop grande')
        while len(body) < length:
            chunk = conn.recv(min(4096, length - len(body)))
            if not chunk:
                raise RpcError('corps HTTP incomplet')
            body += chunk
        if len(body) != length:
            raise RpcError('octets après le corps HTTP')
        return method, path, body

    @staticmethod
    def _send_http(conn: socket.socket, status: int, payload: dict) -> None:
        body = _json_dump(payload)
        reason = {200: 'OK', 202: 'Accepted', 400: 'Bad Request', 404: 'Not Found',
                  409: 'Conflict', 413: 'Payload Too Large', 503: 'Service Unavailable'}.get(status, 'Error')
        head = (f'HTTP/1.1 {status} {reason}\r\nContent-Type: application/json; charset=utf-8\r\n'
                f'Content-Length: {len(body)}\r\nConnection: close\r\n\r\n').encode('ascii')
        conn.sendall(head + body)

    def _peer_uid(self, conn: socket.socket) -> int:
        if not hasattr(socket, 'SO_PEERCRED'):
            raise RpcError('identité Unix non vérifiable')
        raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
        _pid, uid, _gid = struct.unpack('3i', raw)
        if uid != self.expected_uid:
            raise RpcError('pair Unix non autorisé')
        return uid

    def handle_connection(self, conn: socket.socket) -> None:
        try:
            peer_uid = self._peer_uid(conn)
            method, path, body = self._read_http(conn)
            if method == 'GET' and path == '/capabilities':
                status, payload = 200, self.capabilities()
            elif method == 'POST' and path == '/jobs':
                try:
                    decoded = _json_load(body)
                    status, payload = self.enqueue(decoded, peer_uid)
                except RpcError:
                    status, payload = 400, {'accepted': False, 'errorCode': 'input_rejected'}
            elif method == 'GET' and path.startswith('/jobs/') and '?' not in path and path.count('/') == 2:
                status, payload = self.inspect(path.rsplit('/', 1)[1])
            else:
                status, payload = 404, {'errorCode': 'not_found'}
            try:
                self._send_http(conn, status, payload)
            except OSError:
                return
            if status == 202 and payload.get('accepted') is True:
                job_id = payload.get('jobId')
                if isinstance(job_id, str):
                    self._acknowledge(job_id)
        except (OSError, RpcError, TimeoutError):
            try:
                self._send_http(conn, 400, {'errorCode': 'invalid_request'})
            except OSError:
                pass

    def _acknowledge(self, job_id: str) -> None:
        # L’ACK HTTP a été transmis avant cette écriture; seul un ACK remis à
        # l’appelant rend le job planifiable. Un socket rompu laisse l’état en attente.
        self._transaction(lambda: self._db.execute(
            "UPDATE jobs SET acknowledged=1,updated_at=? WHERE job_id=? AND state='queued'",
            (time.time(), job_id)))

    def _bind(self) -> socket.socket:
        _trusted_dir(self.state_root, 'racine du worker')
        _trusted_dir(self.socket_path.parent, 'répertoire de socket')
        if self.socket_path.exists() or self.socket_path.is_symlink():
            raise RpcError('socket existante refusée; utiliser une nouvelle racine privée')
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(self.socket_path))
            os.chmod(self.socket_path, 0o600, follow_symlinks=False)
            st = self.socket_path.lstat()
            if not stat.S_ISSOCK(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
                raise RpcError('socket créée non privée')
            listener.listen(8)
            listener.settimeout(0.5)
            self._listener = listener
            return listener
        except BaseException:
            listener.close()
            raise

    def serve_forever(self, stop_event: threading.Event | None = None) -> None:
        """Lance explicitement le service et son unique consommateur de file."""
        stop = stop_event or threading.Event()
        listener = self._bind()
        worker = threading.Thread(target=self._worker_loop, args=(stop,),
                                  name='nexora-sync-rnd-worker', daemon=False)
        self._processor_thread = worker
        worker.start()
        self._active = True
        try:
            while not stop.is_set():
                try:
                    conn, _ = listener.accept()
                except socket.timeout:
                    continue
                with conn:
                    self.handle_connection(conn)
        finally:
            self._active = False
            stop.set()
            listener.close()
            worker.join()
            self._listener = None
            self._processor_thread = None

    def _worker_loop(self, stop: threading.Event) -> None:
        while not stop.is_set():
            if self.process_one() is None:
                stop.wait(0.2)

    def close(self) -> None:
        if self._listener is not None:
            raise RpcError('arrêter la boucle de service avant de fermer SQLite')
        with self._db_lock:
            self._verify_db_files()
            self._db.close()


def _no_secret_keys(value, path='config') -> None:
    forbidden = {'token', 'secret', 'password', 'authorization', 'cookie', 'api_key', 'apikey', 'credential'}
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r'[^a-z0-9]', '', str(key).lower())
            if normalized in {re.sub(r'[^a-z0-9]', '', v) for v in forbidden}:
                raise RpcError('configuration locale ne doit contenir aucun identifiant d’accès')
            _no_secret_keys(child, f'{path}.{key}')
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _no_secret_keys(child, f'{path}[{index}]')


def _from_config(path: Path) -> SyncWorkerRpc:
    path = Path(path)
    _private_file(path, 'configuration locale')
    config = _json_load(path.read_bytes())
    _no_secret_keys(config)
    expected = {'schema', 'workerId', 'stateRoot', 'socketPath', 'mediaRoots',
                'maxConcurrent', 'engineLimits', 'engineConfig', 'takes'}
    if not _exact_keys(config, expected) or set(config) != expected or config['schema'] != 'nexora.sync.local-worker-config.v1':
        raise RpcError('configuration locale invalide')
    engines = adapter.lier_capsules(config['engineConfig'])
    limits = config['engineLimits']
    if not isinstance(config['takes'], list):
        raise RpcError('registre de prises local invalide')
    records = []
    for raw in config['takes']:
        keys = {'organisationId', 'takeId', 'kind', 'path', 'sha256', 'bytes', 'durationSeconds'}
        if not _exact_keys(raw, keys, {'fps', 'sampleRate'}):
            raise RpcError('entrée de registre invalide')
        records.append(TakeRecord(raw['organisationId'], raw['takeId'], raw['kind'], Path(raw['path']),
                                  raw['sha256'], raw['bytes'], raw['durationSeconds'],
                                  raw.get('fps'), raw.get('sampleRate')))
    return SyncWorkerRpc(Path(config['stateRoot']), Path(config['socketPath']),
                         tuple(Path(x) for x in config['mediaRoots']), AllowlistResolver(records),
                         engines, limits, config['workerId'], config['maxConcurrent'])


def _executer_tache_enfant(task_root: Path, job_id: str, engine_id: str,
                            expected_plan_sha: str) -> None:
    """Valide un plan privé puis l'exécute dans le thread principal de ce processus."""
    if (MAX_JOB_ID.fullmatch(job_id) is None or engine_id not in adapter.ENGINE_IDS or
            SHA256.fullmatch(expected_plan_sha) is None):
        raise RpcError('commande d’exécution enfant invalide')
    root = Path(task_root)
    _trusted_dir(root, 'racine des tâches')
    run = root / f'sync-{job_id}'
    _trusted_dir(run, 'dossier de tâche')
    state = adapter._lire_json(run / adapter.TASK_STATE)
    if (state.get('schema') != 'nexora.sync.worker-task.v1' or state.get('task_id') != job_id or
            state.get('engine_id') != engine_id or state.get('status') != 'prepared' or
            state.get('plan_sha256') != expected_plan_sha):
        raise RpcError('état préparé différent de la réservation')
    plan_path = run / adapter.PLAN_NAME
    plan = adapter._lire_json(plan_path)
    if adapter._sha(plan_path) != expected_plan_sha:
        raise RpcError('plan enfant différent de la réservation')
    if plan.get('statut') != 'planifie_sans_inference' or not isinstance(plan.get('configuration'), dict):
        raise RpcError('plan enfant invalide')
    if engine_id == 'musetalk' and plan.get('moteur') != 'MuseTalk1.5':
        raise RpcError('plan MuseTalk différent')
    bindings = adapter.lier_capsules({engine_id: plan['configuration']})
    adapter.executer_une_fois(root, job_id, bindings)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description='Worker Sync R&D local sur socket Unix')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--config', type=Path,
                      help='configuration locale privée nexora.sync.local-worker-config.v1')
    mode.add_argument('--execute-task', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--task-root', type=Path)
    parser.add_argument('--task-id')
    parser.add_argument('--engine', choices=sorted(adapter.ENGINE_IDS))
    parser.add_argument('--plan-sha256')
    args = parser.parse_args()
    if args.execute_task:
        if args.config is not None or any(v is None for v in
                (args.task_root, args.task_id, args.engine, args.plan_sha256)):
            parser.error('commande enfant incomplète')
        try:
            _executer_tache_enfant(args.task_root, args.task_id, args.engine, args.plan_sha256)
        except BaseException:
            return 1
        return 0
    if any(v is not None for v in (args.task_root, args.task_id, args.engine, args.plan_sha256)):
        parser.error('options enfant interdites avec --config')
    service = _from_config(args.config)
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        return 130
    finally:
        service.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
