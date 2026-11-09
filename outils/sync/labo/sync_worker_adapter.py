"""Adaptateur local de tâches R&D Sync pour un worker déjà durable.

Le worker appelant doit d'abord résoudre/autoriser des IDs de prises côté serveur.
Ce module n'est ni une route HTTP, ni un daemon, ni une source d'identités client.
Il copie les médias autorisés dans un dossier privé, puis réutilise les capsules
existantes MuseTalk/LatentSync. Un dispatch ambigu n'est jamais rejoué ici.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Callable, Mapping
import uuid

from outils.sync.labo import media_sync

ENGINE_IDS = frozenset({'musetalk', 'latentsync'})
TASK_STATE = 'worker-task.json'
PLAN_NAME = 'plan-execution.json'
MAX_TASK_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z')


class ErreurTache(ValueError):
    pass


class DispatchAmbigu(RuntimeError):
    """Le dispatch a commencé, mais son résultat n'est pas confirmé."""


@dataclass(frozen=True)
class PriseResolue:
    """Référence interne produite après résolution et contrôle d'accès serveur."""
    take_id: int
    path: Path
    sha256: str
    bytes: int


@dataclass(frozen=True)
class MediasResolus:
    video: PriseResolue
    audio: PriseResolue


@dataclass(frozen=True)
class Moteur:
    """Bindings provenant du worker/configuration serveur, jamais de la requête."""
    configuration: Mapping[str, object]
    planifier: Callable[[dict, Path], str]
    executer: Callable[[Path, str], dict]


def lier_capsules(configurations: Mapping[str, Mapping[str, object]]) -> dict[str, Moteur]:
    """Lie les moteurs explicitement activés à une config serveur locale."""
    if not configurations or not set(configurations).issubset(ENGINE_IDS):
        raise ErreurTache('configuration moteur R&D invalide')
    modules = {}
    if 'latentsync' in configurations:
        from outils.sync.labo import latentsync_execution
        modules['latentsync'] = latentsync_execution
    if 'musetalk' in configurations:
        from outils.sync.labo import musetalk_execution
        modules['musetalk'] = musetalk_execution
    return {name: Moteur(dict(configurations[name]), modules[name].planifier,
                         modules[name].executer) for name in sorted(configurations)}


def _maintenant() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _json_bytes(data: object) -> bytes:
    return (json.dumps(data, sort_keys=True, ensure_ascii=False,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def _paires(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ErreurTache('clé JSON dupliquée')
        result[key] = value
    return result


def _lire_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ErreurTache('état de tâche absent ou non régulier')
    st = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ErreurTache('état de tâche non privé')
    try:
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_paires,
                           parse_constant=lambda _: (_ for _ in ()).throw(ErreurTache('valeur JSON non finie')))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ErreurTache('état de tâche illisible') from exc
    if not isinstance(value, dict):
        raise ErreurTache('état de tâche invalide')
    return value


def _ecrire_atomique(run: Path, name: str, data: dict) -> None:
    target = run / name
    if target.is_symlink():
        raise ErreurTache('cible d’état liée refusée')
    temp = run / f'.{name}.{uuid.uuid4().hex}.tmp'
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        payload = _json_bytes(data)
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError('écriture de tâche interrompue')
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temp, target)
    dir_fd = os.open(run, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _trusted_dir(path: Path, label: str, mode: int = 0o700) -> None:
    if not path.is_absolute() or path.is_symlink() or not path.is_dir():
        raise ErreurTache(f'{label} absent ou lié')
    st = path.stat(follow_symlinks=False)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ErreurTache(f'{label} doit être privé à 0700')


def _sans_lien(path: Path) -> None:
    """Vérifie chaque composant d'un chemin configuré/résolu sans suivre de lien."""
    cursor = Path(path.anchor)
    for part in path.parts[1:]:
        cursor = cursor / part
        try:
            if cursor.is_symlink():
                raise ErreurTache('composant de chemin symbolique refusé')
        except OSError as exc:
            raise ErreurTache('composant de chemin inaccessible') from exc


def _ouvrir_prise(prise: PriseResolue, racines: tuple[Path, ...]) -> int:
    if isinstance(prise.take_id, bool) or not isinstance(prise.take_id, int) or prise.take_id <= 0:
        raise ErreurTache('ID de prise résolue invalide')
    if (not isinstance(prise.sha256, str) or len(prise.sha256) != 64 or
            any(ch not in '0123456789abcdef' for ch in prise.sha256)):
        raise ErreurTache('SHA de prise résolue invalide')
    if isinstance(prise.bytes, bool) or not isinstance(prise.bytes, int) or not 0 < prise.bytes <= media_sync.MAX_MEDIA_BYTES:
        raise ErreurTache('taille de prise résolue invalide')
    path = Path(prise.path)
    if not path.is_absolute() or '..' in path.parts:
        raise ErreurTache('chemin résolu non absolu ou traversant')
    for root in racines:
        root = Path(root)
        if not root.is_absolute():
            raise ErreurTache('racine média non absolue')
        _sans_lien(root)
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if not relative.parts:
            continue
        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        current_fd = root_fd
        try:
            for part in relative.parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                  dir_fd=current_fd)
                if current_fd != root_fd:
                    os.close(current_fd)
                current_fd = next_fd
            fd = os.open(relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=current_fd)
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_size != prise.bytes:
                os.close(fd)
                raise ErreurTache('fichier source différent de la prise résolue')
            return fd
        finally:
            if current_fd != root_fd:
                os.close(current_fd)
            os.close(root_fd)
    raise ErreurTache('fichier résolu hors racines médias autorisées')


def _copier_prise(prise: PriseResolue, racines: tuple[Path, ...], destination: Path) -> None:
    source_fd = _ouvrir_prise(prise, racines)
    target_fd = None
    try:
        target_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        h = hashlib.sha256()
        total = 0
        source_st = os.fstat(source_fd)
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > media_sync.MAX_MEDIA_BYTES:
                raise ErreurTache('prise trop volumineuse')
            h.update(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(target_fd, view)
                if written <= 0:
                    raise OSError('écriture de prise interrompue')
                view = view[written:]
        if (total != prise.bytes or h.hexdigest() != prise.sha256 or
                os.fstat(source_fd).st_ino != source_st.st_ino or
                os.fstat(source_fd).st_size != source_st.st_size):
            raise ErreurTache('prise modifiée pendant sa copie')
        os.fsync(target_fd)
    finally:
        try:
            os.close(source_fd)
        finally:
            if target_fd is not None:
                os.close(target_fd)


def _run_dir(task_root: Path, task_id: str) -> Path:
    if not isinstance(task_id, str) or MAX_TASK_ID.fullmatch(task_id) is None:
        raise ErreurTache('ID de tâche invalide')
    root = Path(task_root)
    _trusted_dir(root, 'racine des tâches')
    run = root / f'sync-{task_id}'
    os.mkdir(run, 0o700)
    return run


def _statut_resultat(run: Path, plan_sha: str, result: object) -> tuple[str, str | None]:
    if not isinstance(result, dict):
        raise ErreurTache('résultat moteur invalide')
    status = result.get('statut')
    mapped = {
        'av_valide_non_juge': 'av_validated_unjudged',
        'av_refuse': 'av_rejected',
        'echec_ou_non_verifie': 'completed_unverified',
    }.get(status)
    if mapped is None:
        raise ErreurTache('état moteur non reconnu')
    receipt = _lire_json(run / 'validation-av.json')
    if receipt.get('plan_sha256') != plan_sha or receipt.get('statut') != status:
        raise ErreurTache('reçu audiovisuel différent du plan ou du résultat')
    if status in {'av_valide_non_juge', 'av_refuse'}:
        av_result = receipt.get('av')
        if not isinstance(av_result, dict) or av_result.get('valide') is not (status == 'av_valide_non_juge'):
            raise ErreurTache('reçu audiovisuel incohérent')
        output = run / 'sortie.mp4'
        if output.is_symlink() or not output.is_file() or output.stat(follow_symlinks=False).st_size <= 0:
            raise ErreurTache('sortie audiovisuelle absente ou liée')
        output_sha = result.get('sortie_sha256')
        if (not isinstance(output_sha, str) or len(output_sha) != 64 or
                any(ch not in '0123456789abcdef' for ch in output_sha) or _sha(output) != output_sha):
            raise ErreurTache('empreinte de sortie moteur incohérente')
        if receipt.get('sortie_sha256') != output_sha:
            raise ErreurTache('reçu et sortie moteur différents')
        return mapped, output_sha
    av_result = receipt.get('av')
    if av_result is not None and not isinstance(av_result, dict):
        raise ErreurTache('reçu audiovisuel invalide')
    return mapped, None


def preparer_tache(task_root: Path, racines_medias: tuple[Path, ...],
                   medias: MediasResolus, task_id: str, engine_id: str,
                   moteurs: Mapping[str, Moteur]) -> dict:
    """Prépare une tâche durable depuis des IDs déjà résolus par le serveur.

    Les chemins viennent uniquement de `medias`, sortie interne du résolveur.
    L'API appelante ne devrait jamais accepter un chemin de média du navigateur.
    """
    if engine_id not in ENGINE_IDS or engine_id not in moteurs:
        raise ErreurTache('moteur R&D non disponible')
    if not isinstance(medias, MediasResolus) or medias.video.take_id == medias.audio.take_id:
        raise ErreurTache('prises vidéo/audio serveur distinctes requises')
    roots = tuple(Path(p) for p in racines_medias)
    if not roots:
        raise ErreurTache('aucune racine média autorisée')
    run = _run_dir(Path(task_root), task_id)
    binding = moteurs[engine_id]
    state = {'schema': 'nexora.sync.worker-task.v1', 'task_id': task_id,
             'engine_id': engine_id, 'status': 'preparing', 'created_at': _maintenant(),
             'source_ids': {'video': medias.video.take_id, 'audio': medias.audio.take_id}}
    _ecrire_atomique(run, TASK_STATE, state)
    try:
        _copier_prise(medias.video, roots, run / media_sync.VIDEO_NAME)
        _copier_prise(medias.audio, roots, run / media_sync.AUDIO_NAME)
        provenance_sha = media_sync.ecrire_provenance_serveur(
            run, medias.video.take_id, medias.audio.take_id)
        configuration = dict(binding.configuration)
        configuration['provenance_sha256'] = provenance_sha
        plan_sha = binding.planifier(configuration, run)
        if (not isinstance(plan_sha, str) or len(plan_sha) != 64 or
                any(ch not in '0123456789abcdef' for ch in plan_sha)):
            raise ErreurTache('planificateur sans empreinte de plan valide')
        plan_path = run / PLAN_NAME
        if plan_path.is_symlink() or not plan_path.is_file() or _sha(plan_path) != plan_sha:
            raise ErreurTache('plan absent ou différent après préparation')
        state.update(status='prepared', prepared_at=_maintenant(),
                     plan_sha256=plan_sha,
                     media_sha256={'video': medias.video.sha256, 'audio': medias.audio.sha256})
        _ecrire_atomique(run, TASK_STATE, state)
        return {'task_id': task_id, 'engine_id': engine_id, 'status': 'prepared',
                'run_dir': str(run), 'plan_sha256': plan_sha}
    except BaseException as exc:
        state.update(status='preparation_failed', failed_at=_maintenant(),
                     error_class=type(exc).__name__)
        _ecrire_atomique(run, TASK_STATE, state)
        raise


def preparer_depuis_ids(task_root: Path, racines_medias: tuple[Path, ...],
                        video_take_id: int, audio_take_id: int, task_id: str,
                        engine_id: str, moteurs: Mapping[str, Moteur],
                        resoudre_autorisees: Callable[[int, int], MediasResolus]) -> dict:
    """Entrée destinée au worker: résolution/ACL côté serveur, jamais un chemin client.

    `resoudre_autorisees` doit être lié au principal authentifié et à la transaction
    du job appelant; elle retourne les chemins, empreintes et tailles du registre.
    """
    for value in (video_take_id, audio_take_id):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ErreurTache('ID de prise serveur invalide')
    if video_take_id == audio_take_id:
        raise ErreurTache('prises vidéo/audio distinctes requises')
    if engine_id not in ENGINE_IDS or engine_id not in moteurs:
        raise ErreurTache('capacité R&D indisponible')
    if not isinstance(task_id, str) or MAX_TASK_ID.fullmatch(task_id) is None:
        raise ErreurTache('ID de tâche invalide')
    medias = resoudre_autorisees(video_take_id, audio_take_id)
    if (not isinstance(medias, MediasResolus) or
            medias.video.take_id != video_take_id or medias.audio.take_id != audio_take_id):
        raise ErreurTache('le résolveur serveur a retourné d’autres prises')
    return preparer_tache(task_root, racines_medias, medias, task_id, engine_id, moteurs)


def executer_une_fois(task_root: Path, task_id: str,
                       moteurs: Mapping[str, Moteur]) -> dict:
    """Effectue un seul dispatch; `dispatch_unknown` n'est jamais relancé.

    À appeler uniquement par un worker durable qui a déjà validé l'accès aux IDs.
    Toute exception après la transition persistée demeure ambiguë jusqu'à inspection.
    """
    if not isinstance(task_id, str) or MAX_TASK_ID.fullmatch(task_id) is None:
        raise ErreurTache('ID de tâche invalide')
    root = Path(task_root)
    _trusted_dir(root, 'racine des tâches')
    run = root / f'sync-{task_id}'
    _trusted_dir(run, 'dossier de tâche')
    lock_path = run / '.dispatch.lock'
    if lock_path.is_symlink():
        raise ErreurTache('verrou de tâche symbolique refusé')
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ErreurTache('verrou de tâche non privé')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ErreurTache('dispatch déjà actif') from exc
        state = _lire_json(run / TASK_STATE)
        if state.get('schema') != 'nexora.sync.worker-task.v1' or state.get('task_id') != task_id:
            raise ErreurTache('état de tâche incohérent')
        if state.get('status') != 'prepared':
            raise DispatchAmbigu('tâche non préparée ou dispatch déjà commencé; aucun rejeu automatique')
        engine_id = state.get('engine_id')
        binding = moteurs.get(engine_id)
        if binding is None or engine_id not in ENGINE_IDS:
            raise ErreurTache('binding de moteur absent')
        plan_sha = state.get('plan_sha256')
        plan_path = run / PLAN_NAME
        if (not isinstance(plan_sha, str) or len(plan_sha) != 64 or
                any(ch not in '0123456789abcdef' for ch in plan_sha) or
                plan_path.is_symlink() or not plan_path.is_file() or _sha(plan_path) != plan_sha):
            raise ErreurTache('plan absent ou empreinte différente')
        state.update(status='dispatch_unknown', dispatch_started_at=_maintenant())
        _ecrire_atomique(run, TASK_STATE, state)
        try:
            result = binding.executer(run, plan_sha)
        except BaseException as exc:
            state.update(last_error_class=type(exc).__name__, updated_at=_maintenant())
            _ecrire_atomique(run, TASK_STATE, state)
            raise DispatchAmbigu('dispatch commencé; résultat à réconcilier, aucun rejeu') from exc
        try:
            safe_status, output_sha = _statut_resultat(run, plan_sha, result)
        except ErreurTache as exc:
            state.update(last_error_class='InvalidEngineResult', updated_at=_maintenant())
            _ecrire_atomique(run, TASK_STATE, state)
            raise DispatchAmbigu('résultat moteur non confirmé; aucun rejeu') from exc
        state.update(status=safe_status, finished_at=_maintenant())
        if output_sha:
            state['output_sha256'] = output_sha
        _ecrire_atomique(run, TASK_STATE, state)
        return {'task_id': task_id, 'engine_id': engine_id, 'status': safe_status}
    finally:
        os.close(fd)
