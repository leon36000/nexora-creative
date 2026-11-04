"""Endpoint de transcription Studio ; partage le cache, le verrou et LAST avec /stt."""
import subprocess
import time

import numpy as np
from fastapi import File, Form, UploadFile
from faster_whisper import WhisperModel


def installer(app, charge, LOCK, LAST):
    @app.post("/transcrire")
    def transcrire(file: UploadFile = File(...), language: str = Form("fr")):
        pcm = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", "pipe:0", "-vn", "-ac", "1",
             "-ar", "16000", "-f", "f32le", "pipe:1"],
            input=file.file.read(), capture_output=True, check=True,
        ).stdout
        audio = np.frombuffer(pcm, dtype=np.float32)
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
