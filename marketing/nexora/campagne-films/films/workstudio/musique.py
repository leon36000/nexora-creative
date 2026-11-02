"""Bande originale du film WorkStudio (MiniMax-Music3 par l'API du studio, file d'attente normale). Usage : python3 musique.py [graine ...]

Grille : 120 BPM (un temps = 0,5 s, une mesure = 2 s). Le film montre le résultat tôt : la pulsation démarre tout de suite,
un coup net à 12 s (l'accord donné), groove jusqu'à 48 s, arrêt d'un temps à 50 s, coup final et queue pour le carton.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "refonte-medias/outils"))
from moteurs import musique  # noqa: E402

SORTIE = Path.home() / "nexora-creative-data/promo/v5/workstudio/audio"
DESCRIPTION = (
    "Global Metadata: Modern minimal electronic for a software product film, 120 BPM, A minor to C major, confident, precise, warm, "
    "focused, clean high-end commercial production, tight punchy drums, round sub-bass, crisp plucks, wide stereo, loud polished master.\n\n"
    "Vocal Details: Instrumental, no lyrics, no vocals.\n\n"
    "Arrangement: [Intro] starts immediately with a tight muted pluck pattern and a ticking hi-hat on every beat, a soft kick from bar 2. "
    "[Build] at 6 seconds a filtered bass line and a short riser. [Hit] at 12 seconds one clean hard hit with a bright chord, then "
    "[Groove] a steady confident four-on-the-floor groove with plucked arpeggios, clap on beats 2 and 4, small fills every 8 bars, "
    "energy rising slowly until 48 seconds. [Break] at 50 seconds an abrupt stop, one beat of silence. [Outro] one deep clean hit and "
    "a resolved C major chord with a long soft tail fading out.")
PAROLES = "[Intro]\n\n[Build]\n\n[Hit]\n\n[Groove]\n\n[Break]\n\n[Outro]"

if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    for g in [int(x) for x in sys.argv[1:]] or [51, 52]:
        f = SORTIE / f"ws-musique-{g}.flac"
        if not f.exists():
            _, tid, s = musique(DESCRIPTION, f, 62, PAROLES, seed=g)
            print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
