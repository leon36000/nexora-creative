"""Transcription au mot pour le Mode Studio de Nexora Creative (faster-whisper, sur le processeur).

Usage : python -I transcrire.py <audio.f32> [modele]
L'audio est déjà décodé par ffmpeg en PCM float32 mono 16 kHz (le décodeur PyAV de faster-whisper n'est pas utilisé).
Écrit sur la sortie standard : {"langue": "fr", "phrases": [{"texte", "debutS", "finS", "mots": [{"mot", "debutS", "finS"}]}]}
"""
import json
import os
import sys

import numpy as np
from faster_whisper import WhisperModel


def main() -> None:
    audio = np.fromfile(sys.argv[1], dtype=np.float32)
    modele = sys.argv[2] if len(sys.argv) > 2 else "medium"
    whisper = WhisperModel(modele, device="cpu", compute_type="int8", cpu_threads=min(16, os.cpu_count() or 4))
    segments, info = whisper.transcribe(audio, vad_filter=True, word_timestamps=True)
    phrases = []
    for s in segments:
        mots = [{"mot": m.word.strip(), "debutS": round(float(m.start), 3), "finS": round(float(m.end), 3)} for m in (s.words or [])]
        phrases.append({"texte": s.text.strip(), "debutS": round(float(s.start), 3), "finS": round(float(s.end), 3), "mots": mots})
    json.dump({"langue": info.language, "phrases": phrases}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
