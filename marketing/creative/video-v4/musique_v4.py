"""Bande originale de la promo V4 (MiniMax-Music3 sur la GB10, par l'API du studio). Usage : python3 musique_v4.py [graine ...]

Structure voulue (120 BPM, une mesure = 2 s) calée sur le film : saisie presque silencieuse, plan qui s'anime, montée,
coupure, DROP sur le film fini, montage des genres qui accélère, arrêt net, coup final et halo pour le carton.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nexora/refonte-medias/outils"))
from moteurs import musique  # noqa: E402

SORTIE = Path.home() / "nexora-creative-data/promo/v4/audio"
DESCRIPTION = (
    "Global Metadata: Premium cinematic electronic with orchestral elements for a luxury product launch film, 120 BPM, D minor "
    "resolving to F major, elegant, precise, exciting, modern high-end commercial production, wide stereo, deep clean sub-bass, very "
    "hard punchy transient hits, huge dynamic range, loud polished master.\n\n"
    "Vocal Details: Instrumental, no lyrics, no vocals.\n\n"
    "Arrangement: [Intro] near silence for 8 seconds: a soft ticking clock-like hi-hat, a single felt piano note now and then, a low "
    "warm drone. [Verse] a glassy plucked synth arpeggio and soft pulsing bass join, curious and focused, building gently for 8 seconds. "
    "[Build] tight drums enter, staccato strings, a rising snare roll and a big reverse swell and riser; at 26 seconds everything "
    "stops for one beat of silence. [Drop] at 28 seconds a colossal deep impact, then a majestic slow powerful groove: huge sub-bass "
    "hits on every bar, lush strings and a noble brass theme, shimmering bells. [Climax] at 40 seconds the energy doubles: driving "
    "percussion, fast strings, a hard hit on every beat, risers, faster and bigger. [Break] at 52 seconds an abrupt hard stop, total "
    "silence for one second. [Outro] one enormous low boom with a long bright shimmering tail and a final resolved F major chord "
    "fading out.")
PAROLES = "[Intro]\n\n[Verse]\n\n[Build]\n\n[Drop]\n\n[Climax]\n\n[Break]\n\n[Outro]"

if __name__ == "__main__":
    for g in [int(x) for x in sys.argv[1:]] or [41, 42]:
        f = SORTIE / f"v4-musique-{g}.flac"
        if not f.exists():
            _, tid, s = musique(DESCRIPTION, f, 64, PAROLES, seed=g)
            print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
