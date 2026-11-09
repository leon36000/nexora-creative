"""Essai MuseTalk isolé sur les mêmes entrées que LatentSync ; R&D seulement."""
from __future__ import annotations

import fcntl
import os
from pathlib import Path
import stat
import time

from outils.sync import valider_duree_av as av
from outils.sync.labo import capsule_sync, highsync_preflight, lanceur_musetalk
from outils.sync.labo import latentsync_execution as commun
from outils.sync.labo.musetalk_patch import PATCHED_SHA256

TASK_YAML = 'task.yaml'
SORTIE_MP4 = 'sortie.mp4'
AUDIO_ENTREE_WAV = 'audio-entree.wav'
VIDEO_ENTREE_MP4 = 'video-entree.mp4'
MOTEUR = 'MuseTalk1.5'
PLAN_EXECUTION_JSON = 'plan-execution.json'


def _verrou_exclusif(fd: int):
    m = os.fstat(fd)
    if not stat.S_ISREG(m.st_mode) or m.st_uid != os.getuid() or m.st_mode & 0o077:
        raise ValueError('verrou non privé')
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _arguments(c, run: Path):
    models = Path(c['models'])
    return ['--inference_config', str(run/TASK_YAML),
            '--result_dir', str(run/'results'),
            '--output_vid_name', str(run/SORTIE_MP4),
            '--unet_model_path', str(models/'musetalkV15/unet.pth'),
            '--unet_config', str(models/'musetalkV15/musetalk.json'),
            '--whisper_dir', str(models/'whisper'),
            '--vae_type', 'sd-vae', '--version', 'v15', '--gpu_id', '0',
            '--fps', '25', '--batch_size', '2', '--extra_margin', '10',
            '--parsing_mode', 'jaw', '--left_cheek_width', '90',
            '--right_cheek_width', '90', '--saved_coord', '--use_float16']


def _commande(c, run: Path, lock_fd: int, status_fd: int):
    runtime = Path(c['runtime'])
    argv = capsule_sync.construire(runtime, run, Path(c['python']),
        runtime/'scripts/inference_preserve.py', _arguments(c, run),
        Path(c['ffmpeg']), c['gpu_uuid'], lock_fd, status_fd, Path(c['bwrap']))
    # Variables spécifiques du runner préservant, après le clearenv du socle.
    i = argv.index('--')
    argv[i:i] = ['--setenv', 'NEXORA_FFMPEG_BIN', c['ffmpeg'],
                 '--setenv', 'NEXORA_FEATURE_AUDIO_PATH', str(run/AUDIO_ENTREE_WAV)]
    return argv


def _verifier_runtime(c):
    runtime = Path(c['runtime'])
    manifest_path = Path(c['runtime_manifest'])
    highsync_preflight._verifier_fichier(manifest_path, c['runtime_manifest_sha256'])
    manifest = commun._lire(manifest_path)
    models = Path(c['models'])
    if manifest['runtime'] != str(runtime) or manifest['links'] != {'models': str(models)}:
        raise ValueError('racine runtime ou lien models différent')
    capsule_sync._sans_echappement(models, 'poids')
    if not models.is_dir() or not (runtime/'models').is_symlink():
        raise ValueError('répertoire des poids ou lien models absent')
    if (runtime/'models').resolve(strict=True) != models:
        raise ValueError('cible models différente')
    paths = list(runtime.rglob('*'))
    if {p.relative_to(runtime).as_posix() for p in paths if p.is_symlink()} != {'models'}:
        raise ValueError('lien runtime inattendu')
    files = manifest['runtime_sha256']
    if not isinstance(files, dict) or not files or {
        p.relative_to(runtime).as_posix() for p in paths if p.is_file()
    } != set(files):
        raise ValueError('contenu runtime différent')
    for name, sha in files.items():
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or not rel.parts:
            raise ValueError('chemin runtime invalide')
        highsync_preflight._verifier_fichier(runtime/rel, sha)
    for name, sha in lanceur_musetalk.EXPECTED_SOURCE.items():
        highsync_preflight._verifier_fichier(runtime/name, sha)
    highsync_preflight._verifier_fichier(runtime/'musetalk/utils/audio_processor.py', PATCHED_SHA256)
    expected = lanceur_musetalk.make_preserving_runner(runtime/'scripts/inference.py')
    if (runtime/'scripts/inference_preserve.py').read_bytes() != expected:
        raise ValueError('runner préservant différent')
    # Les onze poids/configurations sont ceux du banc existant, sans copie.
    for name, sha in lanceur_musetalk.EXPECTED_MODELS.items():
        path = models/Path(name).relative_to('models')
        capsule_sync._sans_echappement(path, 'poids')
        highsync_preflight._verifier_fichier(path, sha)


def _verifier(c, run: Path):
    _commande(c, run, 3, 4)  # Validation pure, aucun processus lancé.
    _verifier_runtime(c)
    for name in ('python', 'ffmpeg', 'ffprobe', 'bwrap', 'nvidia_smi'):
        path = Path(c[name])
        capsule_sync._exe(path, name, suivre_lien=True)
        highsync_preflight._verifier_fichier(path.resolve(), c['executables_sha256'][name])
    if Path(c['ffmpeg']).parent != Path(c['ffprobe']).parent:
        raise ValueError('paire FFmpeg/FFprobe requise')
    provenance = run/'provenance-entrees.json'
    highsync_preflight._verifier_fichier(provenance, c['provenance_sha256'])
    p = commun._lire(provenance)
    if p['modele_demande'] != 'elevenlabs/eleven-v4':
        raise ValueError('provenance Eleven4 requise')
    for name in ('audio-original.mp3', AUDIO_ENTREE_WAV, VIDEO_ENTREE_MP4):
        highsync_preflight._verifier_fichier(run/name, p['fichiers'][name])
    return highsync_preflight.preflight(run/VIDEO_ENTREE_MP4, run/AUDIO_ENTREE_WAV,
        p['fichiers'][VIDEO_ENTREE_MP4], p['fichiers'][AUDIO_ENTREE_WAV],
        Path(c['ffmpeg']), Path(c['ffprobe']))


def _task(run: Path):
    return {'task_0': {'video_path': str(run/VIDEO_ENTREE_MP4),
                       'audio_path': str(run/AUDIO_ENTREE_WAV)}}


def planifier(c, run: Path):
    entree = _verifier(c, run)
    prevol = commun._prevol(c)
    commun._ecrire(run/TASK_YAML, _task(run))  # JSON est un sous-ensemble de YAML.
    plan = {'statut': 'planifie_sans_inference', 'moteur': MOTEUR,
            'configuration': c, 'entrees_av': entree, 'prevol': prevol,
            'task_sha256': commun.empreinte(run/TASK_YAML),
            'voix_validee_humain': False, 'produit_livre': False}
    commun._ecrire(run/PLAN_EXECUTION_JSON, plan)
    return commun.empreinte(run/PLAN_EXECUTION_JSON)


def _cache_sfd(c, run: Path):
    path = run/'cache/torch/hub/checkpoints/s3fd-619a316812.pth'
    target = Path(c['models'])/'syncnet/auxiliary/s3fd-619a316812.pth'
    capsule_sync._sans_echappement(path.parent, 'cache SFD')
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if os.path.lexists(path):
        if not path.is_symlink() or path.resolve(strict=True) != target:
            raise ValueError('cache SFD différent')
    else:
        path.symlink_to(target)


def executer(run: Path, plan_sha256: str):
    from outils.sync.labo.supervision_capsule import superviser
    plan_path = run/PLAN_EXECUTION_JSON
    highsync_preflight._verifier_fichier(plan_path, plan_sha256)
    plan = commun._lire(plan_path)
    if plan['statut'] != 'planifie_sans_inference' or plan['moteur'] != MOTEUR:
        raise ValueError('plan MuseTalk non exécutable')
    c = plan['configuration']
    _verifier(c, run)
    highsync_preflight._verifier_fichier(run/TASK_YAML, plan['task_sha256'])
    if commun._lire(run/TASK_YAML) != _task(run):
        raise ValueError('tâche différente')
    if any(os.path.lexists(run/p) for p in (SORTIE_MP4, 'results',
                   'execution.log', 'resultat-execution.json', 'validation-av.json')):
        raise ValueError('essai déjà exécuté ; créer un autre dossier')
    lock = Path(c['gpu_lock'])
    capsule_sync._sans_echappement(lock, 'verrou')
    capsule_sync._dossier(lock.parent, 'dossier du verrou', 0o700)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        _verrou_exclusif(fd)
        for rel in ('cache/hf', 'cache/torch', 'cache/xdg', 'cache/mpl', 'tmp'):
            (run/rel).mkdir(parents=True, mode=0o700, exist_ok=True)
        _cache_sfd(c, run)
        prevol = commun._prevol(c)
        commun._ecrire(run/'prevol-lancement.json', prevol)
        initial = prevol['gpu']
        samples = []
        dernier = [-float('inf')]

        def controle(_identite, pids):
            if time.monotonic()-dernier[0] < 1:
                return
            dernier[0] = time.monotonic()
            info = commun.gpu(c)
            samples.append(info)
            if any(p['pid'] not in pids for p in info['processus']):
                raise RuntimeError('autre processus GPU apparu : arrêter notre essai')
            if sum(p['mib'] for p in info['processus']) > initial['total_mib']*.70:
                raise RuntimeError('mémoire de notre essai au-dessus du seuil')

        read_fd, write_fd = os.pipe()
        bilan = superviser(_commande(c, run, fd, write_fd), run,
            fd, read_fd, write_fd, 1200, controle)
        commun._ecrire(run/'surveillance-gpu.json', samples)
    finally:
        os.close(fd)
    resultat = {'plan_sha256': plan_sha256, 'moteur': MOTEUR,
                'supervision': bilan, 'qualite_humaine': 'non évaluée',
                'statut': 'echec_ou_non_verifie'}
    if bilan['statut'] == 'succès' and bilan['arret_confirmé'] is True:
        resultat['av'] = av.valider(run/AUDIO_ENTREE_WAV, run/SORTIE_MP4,
            Path(c['ffmpeg']), Path(c['ffprobe']), .08, cadence_cible='25')
        resultat['sortie_sha256'] = commun.empreinte(run/SORTIE_MP4)
        resultat['statut'] = 'av_valide_non_juge' if resultat['av']['valide'] else 'av_refuse'
    commun._ecrire(run/'validation-av.json', resultat)
    return resultat
