"""Contrôle CPU des entrées HighSync ; ne lance aucune inférence."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import os
import wave
from pathlib import Path

from outils.sync import valider_duree_av as av


def _verifier_fichier(path: Path, sha: str) -> None:
    if path.is_symlink() or not path.is_file() or not path.is_absolute():
        raise ValueError('fichier absolu régulier requis')
    if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
        raise ValueError('SHA-256 invalide')
    h = hashlib.sha256()
    with path.open('rb') as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloc)
    if h.hexdigest() != sha:
        raise ValueError('empreinte différente')


def preflight(video: Path, audio: Path, video_sha: str, audio_sha: str,
              ffmpeg: Path, ffprobe: Path, delai: int = 120) -> dict:
    """Vérifie les octets, la durée PCM, et le vrai calendrier CFR 25 fps."""
    _verifier_fichier(video, video_sha)
    _verifier_fichier(audio, audio_sha)
    for binaire in (ffmpeg, ffprobe):
        if not binaire.is_absolute() or not binaire.is_file() or not os.access(binaire, os.X_OK):
            raise ValueError('binaire absolu requis')
    try:
        with wave.open(str(audio), 'rb') as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, 'NONE'):
                raise ValueError('audio requis : WAV PCM mono 16 bits 16 kHz')
    except (wave.Error, EOFError) as exc:
        raise ValueError('audio WAV PCM invalide') from exc
    flux_video = av.informations(ffprobe, video, delai)
    v = av.mesure_video(ffprobe, video, flux_video, delai)
    a = av.mesure_audio(ffmpeg, audio, av.informations(ffprobe, audio, delai), delai)
    if Fraction(v['cadence_moyenne']) != 25 or abs(v['duree_derniere_image_secondes'] - 0.04) > 0.001 or any(
        abs(intervalle - 0.04) > 0.001 for intervalle in v['intervalles_images_secondes']
    ):
        raise ValueError('vidéo non CFR 25 fps')
    if a['frequence_hz'] != 16000:
        raise ValueError('audio source non échantillonné à 16 kHz')
    if v['images_decodees'] * 16000 < a['echantillons'] * 25:
        raise ValueError('vidéo plus courte que le PCM : nombre d’images insuffisant')
    if v['duree_secondes'] < a['duree_secondes']:
        raise ValueError('vidéo plus courte que le PCM décodé')
    return {'video_sha256': video_sha, 'audio_sha256': audio_sha,
            'video': v, 'audio_pcm': a, 'statut': 'preflight_cpu_valide'}
