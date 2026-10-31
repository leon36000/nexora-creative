"""Tempo et grille de temps d'une musique (enveloppe d'attaques + autocorrélation), et les attaques les plus fortes.
Usage : python3 tempo.py fichier.flac"""
import subprocess
import sys
from pathlib import Path

import numpy as np

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
SR, HOP = 16000, 160  # 10 ms
x = np.frombuffer(subprocess.run([FFMPEG, "-v", "error", "-i", sys.argv[1], "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True).stdout, dtype=np.float32)
n = len(x) // HOP
e = np.log1p(100 * np.sqrt((x[: n * HOP].reshape(n, HOP) ** 2).mean(axis=1)))
att = np.maximum(0, np.diff(e, prepend=e[0]))  # attaques
att -= att.mean()
ac = np.correlate(att, att, "full")[n - 1:]
lo, hi = int(60 / 180 * 100), int(60 / 70 * 100)  # 70 à 180 BPM
lag = lo + int(np.argmax(ac[lo:hi]))
bpm = 6000 / lag
phases = [att[p::lag].sum() for p in range(lag)]
phase = int(np.argmax(phases)) / 100
print(f"tempo ≈ {bpm:.1f} BPM (temps = {lag / 100:.2f} s), premier temps à {phase:.2f} s")
top = np.argsort(att)[::-1]
vus = []
for i in top:
    if all(abs(i - j) > 40 for j in vus):
        vus.append(i)
    if len(vus) >= 16:
        break
print("attaques fortes :", ", ".join(f"{i / 100:.2f}" for i in sorted(vus)))
