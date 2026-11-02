"""Bande originale du film « Modèles et API » (MiniMax-Music3 par l'API du studio, file d'attente normale).
Usage : python3 musique.py [graine ...]   (à mesurer ensuite : temps, phrases, coup fort ; le BPM demandé n'est pas le BPM rendu)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "refonte-medias/outils"))
from moteurs import musique  # noqa: E402

SORTIE = Path.home() / "nexora-creative-data/promo/v5/modeles/audio"
DESCRIPTION = (
    "Global Metadata: Clean technical electronic for a developer product film, 124 BPM, D minor, precise, calm confidence, crisp, "
    "minimal, high-end commercial production, tight clicky percussion like keystrokes, round sub-bass, glassy plucked arpeggios, wide "
    "stereo, polished master.\n\nVocal Details: Instrumental, no lyrics, no vocals.\n\n"
    "Arrangement: [Intro] starts immediately with a muted ticking pluck pattern and soft rim clicks, kick from bar 2. [Build] at 7 "
    "seconds a filtered bass and a short riser. [Hit] at 8 seconds one clean hard hit with a bright chord, then [Groove] a steady "
    "confident groove with plucked arpeggios, clap on beats 2 and 4, energy rising slowly until 26 seconds. [Break] at 27 seconds an "
    "abrupt stop. [Outro] one deep clean hit and a resolved chord with a long soft tail.")
PAROLES = "[Intro]\n\n[Build]\n\n[Hit]\n\n[Groove]\n\n[Break]\n\n[Outro]"

if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    for g in [int(x) for x in sys.argv[1:]] or [71, 72]:
        f = SORTIE / f"mod-musique-{g}.flac"
        if not f.exists():
            _, tid, s = musique(DESCRIPTION, f, 44, PAROLES, seed=g)
            print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
