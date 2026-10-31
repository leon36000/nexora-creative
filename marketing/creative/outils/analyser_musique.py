"""Structure d'une musique : durée, énergie (dB RMS) par fenêtre, montées brusques (chutes, impacts), silences.
Sert à choisir la bande originale et à caler les coupes du montage sur ses temps forts.
Usage : python3 analyser_musique.py fichier.flac [fenêtre_s]"""
import subprocess
import sys
from pathlib import Path

import numpy as np

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
f, fen = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
pcm = subprocess.run([FFMPEG, "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(pcm, dtype=np.float32)
n = int(16000 * fen)
blocs = x[: len(x) // n * n].reshape(-1, n)
db = 20 * np.log10(np.sqrt((blocs**2).mean(axis=1)) + 1e-9)
print(f"{Path(f).name} : {len(x) / 16000:.1f} s, crête {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dB")
print("courbe (dB, 1 caractère = %.1f s) :" % fen)
echelle = " ▁▂▃▄▅▆▇█"
print("".join(echelle[int(np.clip((d + 50) / 50 * 8, 0, 8))] for d in db))
saut = np.diff(db)
for i in np.argsort(saut)[::-1][:8]:
    print(f"  montée +{saut[i]:.1f} dB à {(i + 1) * fen:.1f} s")
for i, d in enumerate(db):
    if d < -45:
        print(f"  silence à {i * fen:.1f} s ({d:.0f} dB)")
