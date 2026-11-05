"""Référence minimale du service STT de la VM 204 ; pas une copie de sa production."""
import subprocess
import threading
import time

import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from faster_whisper import WhisperModel

from encoder_endpoint import installer as installer_encoder
from transcrire_endpoint import installer

app = FastAPI()
LOCK = threading.Lock()
CACHE = {}
LAST = [time.time()]  # comme en production : LAST[0]


def charge(nom, construire):
    """À appeler sous LOCK ; LAST[0] = dernière utilisation."""
    if nom not in CACHE:
        CACHE[nom] = construire()
    LAST[0] = time.time()
    return CACHE[nom]


installer(app, charge, LOCK, LAST)
installer_encoder(app, LOCK)


@app.post("/stt")
def stt(file: UploadFile = File(...), language: str = Form("fr")):
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0", "-vn", "-ac", "1",
         "-ar", "16000", "-f", "f32le", "pipe:1"],
        input=file.file.read(), capture_output=True, check=True,
    ).stdout
    with LOCK:
        try:
            whisper = charge("stt", lambda: WhisperModel(
                "deepdml/faster-whisper-large-v3-turbo-ct2",
                device="cuda", compute_type="float16",
            ))
            segments, info = whisper.transcribe(
                np.frombuffer(pcm, dtype=np.float32), language=language,
            )
            return {"language": info.language, "segments": [
                {"text": s.text, "start": float(s.start), "end": float(s.end)}
                for s in segments
            ]}
        finally:
            LAST[0] = time.time()
