"""Endpoint de transcription Studio ; partage le cache, le verrou et LAST avec /stt.

Sécurité : jeton exigé à chaque requête (fichier, jamais en dur), WAV uniquement,
taille et durée plafonnées, aucun chemin de fichier accepté (audio par le corps de la requête).
"""
import hmac
import os
import subprocess
import time

import numpy as np
from fastapi import File, Form, Header, HTTPException, UploadFile

FICHIER_JETON = os.environ.get("NEXORA_TRANSCRIRE_JETON_FICHIER", "/srv/nexora-gpu/transcrire.token")
TAILLE_MAX = int(os.environ.get("NEXORA_TRANSCRIRE_TAILLE_MAX", str(150 * 2**20)))  # ~1 h de WAV 16 kHz mono
DUREE_MAX_S = int(os.environ.get("NEXORA_TRANSCRIRE_DUREE_MAX_S", "3600"))
LANGUES = {"fr", "en", "es", "it", "pt", "de"}


def _jeton_attendu():
    try:
        with open(FICHIER_JETON, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def verifier_jeton(authorization):
    attendu = _jeton_attendu()
    if not attendu:  # pas de jeton configuré : le point reste fermé
        raise HTTPException(503, "transcription non configurée")
    recu = (authorization or "")[7:] if (authorization or "").startswith("Bearer ") else ""
    if not hmac.compare_digest(recu.encode(), attendu.encode()):
        raise HTTPException(401, "jeton invalide")


def decoder(donnees):
    """WAV -> PCM f32 16 kHz mono, plafonné à DUREE_MAX_S (413 au-delà)."""
    try:
        pcm = subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "wav", "-i", "pipe:0", "-vn", "-ac", "1",
             "-ar", "16000", "-t", str(DUREE_MAX_S + 1), "-f", "f32le", "pipe:1"],
            input=donnees, capture_output=True, check=True, timeout=300,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise HTTPException(422, "audio illisible")
    audio = np.frombuffer(pcm, dtype=np.float32)
    if len(audio) > DUREE_MAX_S * 16000:
        raise HTTPException(413, "audio trop long")
    return audio


def installer(app, charge, LOCK, LAST):
    @app.post("/transcrire")
    def transcrire(file: UploadFile = File(...), language: str = Form("fr"),
                   authorization: str = Header(None)):
        verifier_jeton(authorization)
        if language not in LANGUES:
            raise HTTPException(422, "langue non prise en charge")
        donnees = file.file.read(TAILLE_MAX + 1)
        if len(donnees) > TAILLE_MAX:
            raise HTTPException(413, "fichier trop volumineux")
        audio = decoder(donnees)
        from faster_whisper import WhisperModel
        with LOCK:
            LAST[0] = time.time()
            try:
                whisper = charge("stt", lambda: WhisperModel(
                    "deepdml/faster-whisper-large-v3-turbo-ct2",
                    device="cuda", compute_type="float16",
                ))
                segments, info = whisper.transcribe(
                    audio, language=language, vad_filter=True, word_timestamps=True,
                )
                phrases = []
                for s in segments:
                    mots = [
                        {"mot": m.word.strip(), "debutS": round(float(m.start), 3),
                         "finS": round(float(m.end), 3)}
                        for m in (s.words or [])
                    ]
                    phrases.append({
                        "texte": s.text.strip(), "debutS": round(float(s.start), 3),
                        "finS": round(float(s.end), 3), "mots": mots,
                    })
                return {"langue": info.language, "phrases": phrases}
            finally:
                LAST[0] = time.time()
