"""Film V6 : bande originale par Lyria 3 Pro (OpenRouter), trois briefs entraînants, tempo et grille MESURÉS.
  python3 musique_v6.py [n…]    → ~/nexora-creative-data/promo/v6-creative/musique/lyria-<n>.{mp3,wav} + musique.json
Le montage se cale ensuite sur la grille mesurée (pas sur le tempo demandé).
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nexora/campagne-films/films-v3/outils"))
import commun as C  # noqa: E402
from musique import grille, lyria  # noqa: E402

D = Path.home() / "nexora-creative-data/promo/v6-creative/musique"
STRUCTURE = ("Structure, 58 seconds total, at exactly 124 BPM in 4/4: "
             "0-2 s a tense intro, ticking hi-hat and a rising whoosh; "
             "2.4 s FIRST DROP: a huge hybrid impact then pounding big-beat drums, distorted synth bass and short heroic brass stabs; "
             "10-24 s keep driving, add fast string ostinato and taiko hits every bar, rising energy; "
             "24-34 s a bouncy, funky groove section, lighter and playful, punchy claps; "
             "34-35 s one bar of near silence (a single held breath); "
             "35 s FINAL DROP, the biggest moment: full drums, choir shouts, brass melody in a bright major key, euphoric and triumphant; "
             "50-58 s a final hit and a ringing tail that ends cleanly. ")
BRIEFS = {
    1: ("Instrumental only, no vocals except wordless choir shouts. Upbeat, fun, energetic hybrid trailer music for a blockbuster "
        "teaser: electro-orchestral big beat, never sad, never dark, never melancholic, confident and exciting. ") + STRUCTURE,
    2: ("Instrumental only. A high-energy French-touch electro and orchestra crossover for a viral ad: driving four-on-the-floor kick, "
        "funky distorted bass, filtered disco strings, brass hits, euphoric and catchy, never sad. ") + STRUCTURE,
    3: ("Instrumental only, no lyrics. Epic but joyful action-adventure anthem for a superhero-style trailer: huge drums, heroic brass "
        "fanfare, soaring strings, modern trap hi-hats and 808 sub bass, triumphant and catchy, never gloomy. ") + STRUCTURE,
}

if __name__ == "__main__":
    D.mkdir(parents=True, exist_ok=True)
    nums = [int(x) for x in sys.argv[1:]] or list(BRIEFS)
    res = json.loads((D / "musique.json").read_text()) if (D / "musique.json").exists() else {}
    for k in nums:
        t0 = time.time()
        b, cout = lyria(BRIEFS[k])
        (D / f"lyria-{k}.mp3").write_bytes(b)
        C.ff("-i", D / f"lyria-{k}.mp3", "-ar", C.SR, "-ac", 2, D / f"lyria-{k}.wav")
        g = grille(D / f"lyria-{k}.wav")
        g.update({"brief": BRIEFS[k], "cout": cout, "secondes": round(time.time() - t0, 1)})
        res[str(k)] = g
        print(k, g["bpm"], g["duree_s"], cout, g["secondes"], flush=True)
    (D / "musique.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
