"""Outils communs des films V5 (films-v3) : chemins, ffmpeg, clés (lues à l'exécution, jamais affichées), lecture audio.

Dossier de travail léger sur pc6 : ~/nexora-creative-data/work/films-v3/<film>/ ; masters et intermédiaires lourds sur pc1 :
/run/media/pc1/Infrastructure/NexoraStudioWork/films-v3/ (copie par `livrer.py`).
"""
import json
import os
import re
import subprocess
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
TRAVAIL = Path.home() / "nexora-creative-data/work/films-v3"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
SR = 48000


def cle(nom):
    """Clé d'API depuis ~/Desktop/Deepinfra.env (« nom: valeur ») ; jamais imprimée."""
    for ligne in open(Path.home() / "Desktop/Deepinfra.env"):
        if ":" in ligne:
            k, v = ligne.split(":", 1)
            if k.strip().lower() == nom:
                return v.strip()
    raise KeyError(nom)


def ff(*a):
    r = subprocess.run([FF, "-v", "error", "-y", *map(str, a)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])


def duree(f):
    r = subprocess.run([FF, "-hide_banner", "-i", str(f)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])


def lire(f, sr=SR, canaux=2):
    """Audio → tableau float32 (n, canaux)."""
    b = subprocess.run([FF, "-v", "error", "-i", str(f), "-f", "f32le", "-ac", str(canaux), "-ar", str(sr), "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, canaux).copy()


def ecrire(f, x, sr=SR):
    p = subprocess.Popen([FF, "-v", "error", "-y", "-f", "f32le", "-ac", str(x.shape[1]), "-ar", str(sr), "-i", "-",
                          "-c:a", "pcm_s24le", str(f)], stdin=subprocess.PIPE)
    p.stdin.write(np.ascontiguousarray(x, np.float32).tobytes())
    p.stdin.close()
    p.wait()


def charger_film(nom):
    return json.loads((RACINE / nom / "film.json").read_text())


def dossier(nom):
    d = TRAVAIL / nom
    d.mkdir(parents=True, exist_ok=True)
    return d
