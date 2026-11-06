"""Prépare un essai HighSync privé et traçable ; aucun modèle n'est exécuté."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
import uuid

from outils.sync.labo import highsync_patch, highsync_preflight, highsync_s3fd


def _copier(source: Path, cible: Path, attendu: str) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError('entrée non régulière ou lien symbolique')
    h = hashlib.sha256()
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ValueError('entrée non régulière')
    with os.fdopen(fd, 'rb') as src, cible.open('xb') as dst:
        os.fchmod(dst.fileno(), 0o600)
        for bloc in iter(lambda: src.read(1024 * 1024), b''):
            h.update(bloc)
            dst.write(bloc)
    if h.hexdigest() != attendu:
        raise ValueError('entrée modifiée pendant la copie')


def preparer(root: Path, video: Path, audio: Path, video_sha: str, audio_sha: str,
             ffmpeg: Path, ffprobe: Path, source: Path) -> Path:
    """Crée un dossier neuf, fige les fichiers et revalide leurs données décodées."""
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or root.resolve() != root:
        raise ValueError('racine de travail invalide')
    # Les contrôles se font avant toute création ; la copie est ensuite hachée à nouveau.
    highsync_preflight.preflight(video, audio, video_sha, audio_sha, ffmpeg, ffprobe)
    if source.is_symlink() or not source.is_file():
        raise ValueError('source auteur invalide')
    runner = highsync_patch.adapter(source.read_bytes())
    image_source = source.parent / 'image_processor.py.txt'
    if image_source.is_symlink() or not image_source.is_file():
        raise ValueError('source image_processor absente')
    image_runner = highsync_patch.adapter_image_processor(image_source.read_bytes())
    whisper_source = source.parent / 'whisper_init.py.txt'
    if whisper_source.is_symlink() or not whisper_source.is_file():
        raise ValueError('source Whisper absente')
    whisper_runner = highsync_patch.adapter_whisper(whisper_source.read_bytes())
    detecteur = Path(highsync_s3fd.__file__).read_bytes()
    run = root / ('highsync-' + uuid.uuid4().hex)
    run.mkdir(mode=0o700)
    video_copy, audio_copy = run / 'video-entree.mp4', run / 'audio-entree.wav'
    _copier(video, video_copy, video_sha)
    _copier(audio, audio_copy, audio_sha)
    preuves = highsync_preflight.preflight(video_copy, audio_copy, video_sha, audio_sha, ffmpeg, ffprobe)
    with (run / 'inference_adaptee.py').open('xb') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(runner)
    for nom, contenu in (('highsync_image_processor.py', image_runner), ('highsync_s3fd.py', detecteur), ('whisper_init_adapte.py', whisper_runner)):
        with (run / nom).open('xb') as f:
            os.fchmod(f.fileno(), 0o600)
            f.write(contenu)
    manifeste = {'detector_backend': 's3fd',
                 'detector_source_sha256': highsync_s3fd.SOURCE_SHA,
                 'detector_weights_sha256': highsync_s3fd.WEIGHT_SHA,
                 'image_processor_source_sha256': highsync_patch.IMAGE_PROCESSOR_SHA256,
                 'whisper_source_sha256': highsync_patch.WHISPER_SOURCE_SHA256,
                 'whisper_adapte_sha256': hashlib.sha256(whisper_runner).hexdigest(),
                 'image_processor_sha256': hashlib.sha256(image_runner).hexdigest(),
                 's3fd_adapter_sha256': hashlib.sha256(detecteur).hexdigest(),
                 'source_commit': highsync_patch.SOURCE_COMMIT,
                 'source_sha256': highsync_patch.SOURCE_SHA256,
                 'runner_sha256': hashlib.sha256(runner).hexdigest(),
                 'entrees': preuves,
                 'statut': 'prepare_sans_inference'}
    with (run / 'manifest.json').open('x', encoding='utf-8') as f:
        os.fchmod(f.fileno(), 0o600)
        json.dump(manifeste, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')
    return run



def preparer_audio_source(root: Path, video: Path, original: Path, video_sha: str, original_sha: str,
                     ffmpeg: Path, ffprobe: Path, source: Path) -> Path:
    """Fige la source audio déclarée, la convertit en PCM puis prépare le moteur."""
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or root.resolve() != root:
        raise ValueError('racine de travail invalide')
    highsync_preflight._verifier_fichier(video, video_sha)
    highsync_preflight._verifier_fichier(original, original_sha)
    if not ffmpeg.is_absolute() or not ffmpeg.is_file() or not os.access(ffmpeg, os.X_OK):
        raise ValueError('FFmpeg absolu exécutable requis')
    run = root / ('highsync-audio-' + uuid.uuid4().hex)
    run.mkdir(mode=0o700)
    copie = run / 'audio-original.mp3'
    pcm = run / 'audio-16k-mono.wav'
    _copier(original, copie, original_sha)
    commande = [str(ffmpeg), '-v', 'error', '-xerror', '-nostdin', '-n',
                '-protocol_whitelist', 'file,pipe', '-i', str(copie), '-map', '0:a:0',
                '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(pcm)]
    highsync_preflight.av.executer(commande, 120, True)
    h = hashlib.sha256()
    with pcm.open('rb') as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloc)
    pcm_sha = h.hexdigest()
    enfant = preparer(run, video, pcm, video_sha, pcm_sha, ffmpeg, ffprobe, source)
    manifeste = {'statut': 'prepare_sans_inference', 'audio_original_sha256': original_sha,
                 'audio_pcm_sha256': pcm_sha, 'ffmpeg_sha256': hashlib.sha256(ffmpeg.read_bytes()).hexdigest(),
                 'commande_conversion': commande, 'essai': enfant.name}
    with (run / 'provenance-audio.json').open('x', encoding='utf-8') as f:
        os.fchmod(f.fileno(), 0o600)
        json.dump(manifeste, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write('\n')
    return run


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root', type=Path, required=True)
    p.add_argument('--video', type=Path, required=True)
    p.add_argument('--video-sha256', required=True)
    groupe = p.add_mutually_exclusive_group(required=True)
    groupe.add_argument('--audio-pcm', type=Path)
    groupe.add_argument('--audio-original', type=Path)
    p.add_argument('--audio-sha256', required=True)
    p.add_argument('--ffmpeg', type=Path, required=True)
    p.add_argument('--ffprobe', type=Path, required=True)
    p.add_argument('--source-auteur', type=Path, required=True)
    args = p.parse_args()
    try:
        fonction = preparer_audio_source if args.audio_original else preparer
        entree_audio = args.audio_original or args.audio_pcm
        run = fonction(args.run_root, args.video, entree_audio, args.video_sha256,
                       args.audio_sha256, args.ffmpeg, args.ffprobe, args.source_auteur)
    except (ValueError, OSError, highsync_preflight.av.ValidationErreur) as exc:
        print(json.dumps({'statut': 'refuse', 'erreur': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({'statut': 'prepare_sans_inference', 'run': str(run)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
