"""Génère les plans H3 d'un fichier JSON (h3-max, un à la fois pour ne pas saturer la RTX 5090), sans refaire ceux qui existent.
Usage : python3 lancer-plans.py plans.json dossier_sortie [--variantes N] [--format 16:9|9:16] [--rapide]"""
import json, sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
from generer import video
a = argparse.ArgumentParser(); a.add_argument("json"); a.add_argument("sortie")
a.add_argument("--variantes", type=int, default=1); a.add_argument("--format"); a.add_argument("--rapide", action="store_true")
o = a.parse_args()
d = json.loads(Path(o.json).read_text()); fmt = o.format or d.get("format", "16:9")
for nom, prompt in d["plans"].items():
    for v in range(o.variantes):
        f = Path(o.sortie) / f"{nom}{'' if o.variantes == 1 else '-v%d' % (v + 1)}.mp4"
        if f.exists():
            continue
        try:
            video(prompt, f, 5, fmt, True, not o.rapide); print("ok", f.name, flush=True)
        except Exception as e:
            print("ECHEC", f.name, e, flush=True)
