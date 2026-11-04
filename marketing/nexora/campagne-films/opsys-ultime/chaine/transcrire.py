"""Transcription Whisper medium (faster-whisper, CPU du GB10) : python transcrire.py f1 f2 ... → JSON {fichier: {texte, mots:[[début,fin,mot]]}}.
À lancer avec le venv ~/nexora-creative-data/engine/transcription-venv (option -I)."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=16)
out = {}
for f in sys.argv[1:]:
    pcm = subprocess.run([FF, "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    seg, _ = m.transcribe(np.frombuffer(pcm, np.float32), language="fr", beam_size=5, word_timestamps=True,
                          initial_prompt="OPSYS, monsieur Morin, monsieur Thibault, soumission, revêtement, cédule.")
    seg = list(seg)
    out[f] = {"texte": " ".join(s.text.strip() for s in seg),
              "mots": [[round(w.start, 2), round(w.end, 2), w.word.strip()] for s in seg for w in (s.words or [])]}
print(json.dumps(out, ensure_ascii=False))
