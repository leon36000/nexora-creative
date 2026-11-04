"""Détecte les coupes internes d'un rush (H3 ajoute parfois « [Shot 2] » dans son propre prompt) : écart moyen entre images.
  python3 coupes.py <video> [seuil=28]   → temps (s) des coupes
"""
import subprocess, sys
import numpy as np
from pathlib import Path
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")

def coupes(f, seuil=28.0):
    raw = subprocess.run([FF, "-v", "error", "-i", str(f), "-vf", "scale=96:54", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, 54, 96).astype(np.float32)
    d = np.abs(np.diff(a, axis=0)).mean((1, 2))
    med = np.median(d) + 1e-3
    return [round((i + 1) / 24, 2) for i, v in enumerate(d) if v > seuil and v > 4 * med]

if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(Path(f).name, coupes(f))
