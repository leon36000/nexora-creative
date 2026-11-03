"""Bande originale du film OPSYS-AI (MiniMax-Music3 par l'API du studio, file d'attente normale). Usage : python3 musique.py [graine ...]

Structure voulue (à MESURER ensuite : Music3 ne respecte pas le BPM demandé) : impulsion grave tout de suite (la question),
coup net vers 4 s (l'avatar apparaît), section basse sous la voix, montée, grosse pulsation pour les dix départements,
cassure calme sous la deuxième réponse de l'avatar, reprise finale et coup du carton.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "refonte-medias/outils"))
from moteurs import musique  # noqa: E402

SORTIE = Path.home() / "nexora-creative-data/promo/v6/opsys/audio"
DESCRIPTION = (
    "Global Metadata: Cinematic electronic trailer score for a premium technology brand film, 100 BPM, D minor resolving to F major, "
    "driving, precise, nocturnal, hopeful, huge clean modern production, deep sub-bass, tight punchy kick, metallic ticks, "
    "pulsing arpeggiated synths, wide stereo, loud polished master, strong hits on downbeats.\n\n"
    "Vocal Details: Instrumental, no lyrics, no vocals, no choir.\n\n"
    "Arrangement: [Intro] starts immediately with a low heartbeat pulse and a ticking clock-like hi-hat. [Hit] at 4 seconds one huge "
    "clean hit with a shimmering chord. [Calm] from 4 to 14 seconds a soft low pulse and airy pad, quiet, leaving room for a voice. "
    "[Build] 14 to 18 seconds a rising riser and snare roll. [Drive] from 18 to 56 seconds a powerful driving pulse, four-on-the-floor "
    "kick, offbeat bass, arpeggios, a hard accent hit every 2 bars, energy rising. [Break] at 56 seconds a sudden drop to a quiet "
    "warm pad and soft pulse for 12 seconds. [Climax] from 68 to 84 seconds the full beat returns bigger with a soaring lead. "
    "[Outro] at 84 seconds one final deep hit and a resolved F major chord with a long tail.")
PAROLES = "[Intro]\n\n[Hit]\n\n[Calm]\n\n[Build]\n\n[Drive]\n\n[Break]\n\n[Climax]\n\n[Outro]"

if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    for g in [int(x) for x in sys.argv[1:]] or [71, 72]:
        f = SORTIE / f"opsys-musique-{g}.flac"
        if not f.exists():
            _, tid, s = musique(DESCRIPTION, f, 94, PAROLES, seed=g)
            print(f"ok {f.name} prise {tid} {s:.0f}s", flush=True)
