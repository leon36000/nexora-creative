"""Film V6 : essai MiniMax-Music3 (GB10, par l'API du studio de la branche) contre Lyria 3 Pro, même structure que le film.
  python3 musique_music3_v6.py [graine ...]   → ~/nexora-creative-data/promo/v6-creative/musique/music3-<graine>.flac
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nexora/refonte-medias/outils"))
import moteurs  # noqa: E402

moteurs.BASE = os.environ.get("V6_API", "http://127.0.0.1:37171")
SORTIE = Path.home() / "nexora-creative-data/promo/v6-creative/musique"
DESCRIPTION = (
    "Global Metadata: Upbeat, fun, high-energy hybrid trailer music for a blockbuster teaser, electro-orchestral big beat, 124 BPM, "
    "E minor resolving to G major, triumphant, catchy, never sad, never dark, punchy modern production, deep sub-bass, very hard drum "
    "transients, loud polished master.\n\n"
    "Vocal Details: Instrumental, no lyrics; only short wordless choir shouts \"Hey!\" on some downbeats.\n\n"
    "Arrangement: [Intro] 2 seconds: a ticking hi-hat and a fast rising whoosh. [Drop] at 2.4 seconds a huge hybrid impact, then "
    "pounding big-beat drums from the first bar, distorted synth bass and short heroic brass stabs. [Verse] driving, fast string "
    "ostinato, taiko hits every bar, rising energy until 22 seconds. [Groove] 22 to 29 seconds a bouncy funky groove, punchy claps. "
    "[Break] at 30 seconds an abrupt stop: near silence for four seconds with only a low drone. [Final Drop] at 36.5 seconds the "
    "biggest moment: full drums, choir shouts, brass melody in a bright major key, euphoric and triumphant. [Outro] at 50 seconds one "
    "final hit and a ringing tail that ends cleanly.")
PAROLES = "[Intro]\n\n[Drop]\n\n[Verse]\n\n[Groove]\n\n[Break]\n\n[Final Drop]\n\n[Outro]"

if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    for g in [int(x) for x in sys.argv[1:]] or [61, 62]:
        f = SORTIE / f"music3-{g}.flac"
        if not f.exists():
            _, tid, s = moteurs.musique(DESCRIPTION, f, 56, PAROLES, seed=g)
            print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
