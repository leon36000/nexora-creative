"""Versions courtes (30 s, 15 s, 6 s) du film de marque Nexora AI, en fr/en et en 16:9, 9:16, 1:1, sur des musiques dédiées
(MiniMax-Music3 : D-30s, E-15s, F-6s). Même logique que montage-hero.py : chaque plan est pleinement visible à l'instant T.
Usage : python3 montage-court.py 30|15|6 fr|en 16x9|9x16|1x1 [--rapide]
"""
import importlib.util, json, subprocess, sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
VIDEO = ICI.parent
_s = importlib.util.spec_from_file_location("hero", ICI / "montage-hero.py")
hero = importlib.util.module_from_spec(_s); _s.loader.exec_module(hero)
plan, FORMATS = hero.plan, hero.FORMATS

# spot : (musique, durée, carton (version, durée, facteur), segments (T, plan, début, vitesse, fondu, zoom), textes, sfx)
SPOTS = {
    30: ("D-30s.flac", 30.0, ("sting", 5.4, 0.8), 24.6, [
        (0.0, "s01-pixel", 0.0, 1.0, 0, 0.03), (4.7, "s05-atelier", 0.0, 0.9, 0.5, 0.03), (10.5, "s04-ville", 1.5, 1.0, 0.3, 0.03),
        (12.2, "s02-aurore", 0.0, 1.0, 0.1, 0.04), (15.9, "s03-pont", 0.3, 1.0, 0.1, 0.05), (18.5, "s13-lanternes", 0.0, 1.0, 0.3, 0.02),
        (21.8, "s08-paume", 0.0, 1.0, 0.1, 0.0)],
        {"fr": [("Rêvez grand.", 12.5, 3.2, 0.10, "grand."), ("Gardez le contrôle.", 21.9, 2.5, 0.085, "contrôle.")],
         "en": [("Dream big.", 12.5, 3.2, 0.10, "big."), ("Stay in control.", 21.9, 2.5, 0.085, "control.")]},
        [("boom", 12.2, 1.6, -9), ("whoosh", 15.7, 0.9, -15), ("boom", 21.8, 1.6, -8), ("riser", 22.4, 2.2, -14)]),
    15: ("E-15s.flac", 15.0, ("marque", 6.0, 0.55), 9.0, [
        (0.0, "s01-pixel", 0.0, 1.0, 0, 0.03), (2.6, "s05-atelier", 1.8, 1.0, 0.3, 0.03), (6.0, "s02-aurore", 0.5, 1.0, 0.3, 0.04)],
        {"fr": [("Rêvez grand.", 6.3, 2.4, 0.10, "grand.")], "en": [("Dream big.", 6.3, 2.4, 0.10, "big.")]},
        [("whoosh", 5.8, 0.9, -15), ("boom", 9.0, 1.6, -8)]),
    6: ("F-6s.flac", 6.0, ("sting", 3.8, 0.5), 2.2, [(0.0, "s01-pixel", 0.5, 1.0, 0, 0.03)], {"fr": [], "en": []},
        [("riser", 0.8, 3.2, -14), ("boom", 4.0, 1.6, -7)]),
}


def spec(spot, lang, fmt, sortie):
    musique, total, (ver, dcarton, fact), T_carton, segs_def, textes_def, sfx = SPOTS[spot]
    carton = ICI / f"carton-court-{spot}-{lang}-{fmt}.mp4"
    L = [*segs_def, (T_carton, ("carton", carton), 0, 1, 0.3, 0)]
    segs = []
    for k, (T, src, debut, vit, d, z) in enumerate(L):
        fin = L[k + 1][0] if k + 1 < len(L) else total
        s = {"duree": round((fin - T) + (d if k else 0), 3), "fondu": d}
        if isinstance(src, tuple):
            s["carton"] = str(src[1])
        else:
            s.update({"plan": plan(src, fmt), "debut": debut, "vitesse": vit, "zoom": z})
        segs.append(s)
    vertical, carre = fmt == "9x16", fmt == "1x1"
    echelle = 0.55 if vertical else (0.8 if carre else 1.0)
    textes = [{"texte": t if not (vertical and " " in t and len(t) > 12) else t.replace(" ", "\n", 1), "debut": d0, "duree": dur,
               "taille": round(tl * echelle, 4), "position": "bas", "accent": acc} for (t, d0, dur, tl, acc) in textes_def[lang]]
    return {"sortie": sortie, "format": FORMATS[fmt], "ambiance_db": -17,
            "musique": {"fichier": str(ICI / "musique" / musique), "debut": 0, "db": 0, "fondu_fin": 0.6},
            "segments": segs, "textes": textes,
            "sfx": [{"type": t, "t": at, "duree": du, "db": db} for (t, at, du, db) in sfx], "noir_debut": 0.0}


if __name__ == "__main__":
    spot, lang, fmt = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    rapide = "--rapide" in sys.argv
    ver, dcarton, fact = SPOTS[spot][2]
    carton = ICI / f"carton-court-{spot}-{lang}-{fmt}.mp4"
    if not carton.exists():
        subprocess.run([sys.executable, str(VIDEO / "outils" / "carton_nexora.py"), str(carton), "--format", FORMATS[fmt], "--version", ver,
                        "--lang", lang, "--duree", str(dcarton + 1.0), "--facteur", str(fact)], check=True)
    sortie = VIDEO / "final" / f"spot-{spot}s-{fmt}-{lang}{'-apercu' if rapide else ''}.mp4"
    montage = ICI / f"montage-court-{spot}-{lang}-{fmt}.json"
    montage.write_text(json.dumps(spec(spot, lang, fmt, str(sortie)), indent=1, ensure_ascii=False))
    subprocess.run([sys.executable, str(VIDEO / "outils" / "film.py"), str(montage), *(["--rapide"] if rapide else [])], check=True)
