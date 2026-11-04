"""Finition des films V5 : image + mix → master (pc1) et version web H.264 ≤ 25 Mo (pc6), planche 480 px, revue chiffrée.

  python3 finir.py <film> <16x9|9x16>
Revue (revue-<format>.json) : durée, plans et plan moyen, écart moyen des coupes à la grille, temps d'écran du produit
(captures réelles, film produit, tableau et recompositions comptés à part), mots de narration et débit, lignes à l'écran,
LUFS / crête vraie / écart voix-musique, poids du fichier web.
"""
import json
import subprocess
import sys
from pathlib import Path

import commun as C
import planche

LIVRE = Path.home() / "nexora-creative-data/promo/montage"
REEL = {"ui", "flux", "suite", "video", "chaine"}
DESSIN = {"tableau", "envoye"}


def finir(nom, fmt):
    film = C.charger_film(nom)
    dos = C.dossier(nom)
    r = dos / "rendu"
    image = r / f"{nom}-{fmt}-image.mp4"
    mix = dos / "audio/mix.wav"
    master = r / f"V5-{nom}-{fmt}-fr-master.mp4"
    C.ff("-i", image, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest",
         "-movflags", "+faststart", master)
    d = C.duree(master)
    debit = int((24.0 * 8 * 1024 * 1024 / d - 192_000) * 0.97)  # ≤ 25 Mo avec marge
    web = LIVRE / f"V5-{nom}-{fmt}-fr.mp4"
    base = ["-i", master, "-c:v", "libx264", "-preset", "slow", "-b:v", str(debit), "-maxrate", str(int(debit * 1.6)),
            "-bufsize", str(debit * 2), "-pix_fmt", "yuv420p", "-profile:v", "high"]
    C.ff(*base, "-pass", "1", "-passlogfile", r / f"x264-{fmt}", "-an", "-f", "mp4", "/dev/null")
    C.ff(*base, "-pass", "2", "-passlogfile", r / f"x264-{fmt}", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", web)
    pl = json.loads((r / f"plans-{fmt}.json").read_text())
    aj = json.loads((dos / "audio/audio.json").read_text())
    durees = pl["durees"]
    types = [p["type"] for p in film["plans"]]
    reel = sum(dd for dd, t in zip(durees, types) if t in REEL)
    dessin = sum(dd for dd, t in zip(durees, types) if t in DESSIN)
    imprime = sum(dd for dd, t in zip(durees, types) if t == "imprime")
    premier = next(t for t, ty in zip(pl["debuts"], types) if ty in REEL | DESSIN)
    mots = sum(len(x["texte"].split()) for x in film["narration"])
    parole = sum(x["duree"] for x in aj["voix"]["phrases"])
    rv = {"film": nom, "format": fmt, "duree_s": round(d, 2), "plans": len(durees), "plan_moyen_s": round(sum(durees) / len(durees), 2),
          "bpm": pl["bpm"], "ecart_coupes_grille_s": pl["ecart_moyen_s"],
          "produit_premier_s": round(premier, 2), "produit_reel_s": round(reel, 2), "produit_dessine_s": round(dessin, 2),
          "imprimes_s": round(imprime, 2), "part_produit": round((reel + dessin + imprime) / d, 3),
          "narration": {"phrases": len(film["narration"]), "mots": mots, "parole_s": round(parole, 2), "mots_s": round(mots / parole, 2),
                        "moteur": aj["voix"]["moteur"], "statut": aj["statut"]},
          "lignes_ecran": [x["texte"] for x in film.get("textes", []) if x["style"] != "sur"] + [p["texte"] for p in film["plans"] if p["type"] == "ligne"],
          "audio": aj["mesure"], "web_mo": round(web.stat().st_size / 1024 / 1024, 2), "web": str(web), "master": str(master)}
    (r / f"revue-{fmt}.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1))
    planche.planche(master, r / f"planche-{nom}-{fmt}.jpg", 1.0, 8 if fmt == "16x9" else 12, 480 if fmt == "16x9" else 270)
    print(json.dumps(rv, ensure_ascii=False))
    return rv


if __name__ == "__main__":
    finir(sys.argv[1], sys.argv[2])
