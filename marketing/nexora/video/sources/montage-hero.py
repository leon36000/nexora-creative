"""Montage du film de marque « Rêvez grand. Gardez le contrôle. » (60 s) sur la musique C-piano, en fr/en et en 16:9, 9:16, 1:1.

Chaque plan est donné par l'instant T où il est pleinement visible (calé sur la musique) ; le fondu enchaîné qui l'amène
se termine à T. La durée de chaque segment est calculée pour que tout tombe sur la grille.
Usage : python3 montage-hero.py fr|en 16x9|9x16|1x1 [--rapide]      (écrit le montage JSON, rend le carton si besoin, monte)
"""
import json, subprocess, sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
VIDEO = ICI.parent
TOTAL = 60.0
FORMATS = {"16x9": "16:9", "9x16": "9:16", "1x1": "1:1"}

# Variante retenue pour chaque plan (après contrôle à l'œil) ; « plans/… » = rendu h3-max.
CHOIX = {
    "s01-pixel": "plans/s01-pixel-v1.mp4", "s05-atelier": "v2", "s02-aurore": "v2", "s03-pont": "v2", "s04-ville": "v2",
    "s10-pluie": "v2", "s09-crete": "v1", "s08-paume": "v2", "s12-glace": "v2", "s06-phare": "v1", "s13-lanternes": "v2",
    "s14-explosion": "v2",
}


# Variante verticale retenue (rendue nativement en 9:16).
CHOIX_V = {"s01-pixel": "v1", "s05-atelier": "v2", "s02-aurore": "v2", "s03-pont": "v2", "s04-ville": "v2", "s10-pluie": "v2",
           "s09-crete": "v1", "s08-paume": "v2", "s12-glace": "v2", "s06-phare": "v2", "s13-lanternes": "v2", "s14-explosion": "v2"}


def plan(nom, fmt):
    if fmt == "9x16":
        f = ICI / "plans-vertical" / f"{nom}-{CHOIX_V[nom]}.mp4"
        if f.exists():
            return str(f)
    choix = CHOIX[nom]
    if choix.startswith("plans/"):
        return str(ICI / choix)
    return str(ICI / "plans-rapide" / f"{nom}-{choix}.mp4")


# (T, plan ou carton, début dans le plan, vitesse, fondu, zoom)
def edl(fmt, lang):
    carton = ICI / f"carton-marque-{lang}-{fmt}.mp4"
    return [
        (0.0, ("carton", ICI / "noir.mp4"), 0, 1, 0, 0),
        (2.0, "s01-pixel", 0.0, 1.0, 0.9, 0.04),
        (7.0, "s05-atelier", 0.0, 0.84, 0.6, 0.03),
        (13.4, "s02-aurore", 0.0, 0.74, 0.5, 0.04),
        (19.9, "s03-pont", 0.3, 1.0, 0.35, 0.05),
        (23.67, "s04-ville", 1.5, 1.0, 0.1, 0.03),
        (24.71, "s10-pluie", 0.4, 1.0, 0.1, 0.03),
        (25.38, "s09-crete", 0.6, 1.0, 0.1, 0.0),
        (27.3, "s08-paume", 0.0, 0.9, 1.0, 0.0),
        (32.5, "s12-glace", 0.0, 1.0, 0.8, 0.0),
        (37.7, "s06-phare", 1.2, 1.0, 0.9, 0.0),
        (41.5, "s13-lanternes", 0.0, 1.0, 0.1, 0.02),
        (46.7, "s14-explosion", 0.0, 1.0, 0.6, 0.0),
        (49.3, ("carton", carton), 0, 1, 0.3, 0),
    ]


# (texte large, texte vertical/carré, début, durée, taille, accent, position)
TEXTES = {
    "fr": [
        ("Tout commence par une lumière.", "Tout commence\npar une lumière.", 0.7, 3.3, 0.06, None, "centre"),
        ("Rêvez grand.", "Rêvez grand.", 20.2, 3.3, 0.10, "grand.", "bas"),
        ("Gardez le contrôle.", "Gardez\nle contrôle.", 27.5, 4.0, 0.085, "contrôle.", "bas"),
        ("Chez vous. Ou au Québec.", "Chez vous.\nOu au Québec.", 37.9, 3.1, 0.065, None, "bas"),
        ("Un seul compte.\nTous vos outils.", "Un seul compte.\nTous vos outils.", 41.9, 3.7, 0.075, "Tous vos outils.", "bas"),
    ],
    "en": [
        ("It all starts with a light.", "It all starts\nwith a light.", 0.7, 3.3, 0.06, None, "centre"),
        ("Dream big.", "Dream big.", 20.2, 3.3, 0.10, "big.", "bas"),
        ("Stay in control.", "Stay\nin control.", 27.5, 4.0, 0.085, "control.", "bas"),
        ("On your premises, or in Quebec.", "On your premises,\nor in Quebec.", 37.9, 3.1, 0.065, None, "bas"),
        ("One account.\nAll your tools.", "One account.\nAll your tools.", 41.9, 3.7, 0.075, "All your tools.", "bas"),
    ],
}


def spec(fmt, lang, sortie):
    segs = []
    L = edl(fmt, lang)
    for k, (T, src, debut, vit, d, z) in enumerate(L):
        fin = L[k + 1][0] if k + 1 < len(L) else TOTAL
        duree = (fin - T) + (d if k else 0)  # le segment commence d secondes avant T (fondu) et finit à l'instant T du suivant
        s = {"duree": round(duree, 3), "fondu": d}
        if isinstance(src, tuple):
            s["carton"] = str(src[1])
        else:
            s.update({"plan": plan(src, fmt), "debut": debut, "vitesse": vit, "zoom": z})
        segs.append(s)
    vertical, carre = fmt == "9x16", fmt == "1x1"
    echelle = 0.55 if vertical else (0.8 if carre else 1.0)
    textes = []
    for large, haut, deb, dur, taille, accent, pos in TEXTES[lang]:
        t = {"texte": haut if (vertical or carre) else large, "debut": deb, "duree": dur, "taille": round(taille * echelle, 4), "position": pos}
        if accent:
            t["accent"] = accent
        textes.append(t)
    return {
        "sortie": sortie, "format": FORMATS[fmt], "ambiance_db": -17,
        "musique": {"fichier": str(ICI / "musique" / "C-piano.flac"), "debut": 0, "db": 0, "fondu_fin": 0.5},
        "segments": segs, "textes": textes,
        "sfx": [
            {"type": "whoosh", "t": 12.5, "duree": 1.2, "db": -14},
            {"type": "boom", "t": 19.9, "duree": 1.6, "db": -9},
            {"type": "whoosh", "t": 23.2, "duree": 0.9, "db": -15},
            {"type": "whoosh", "t": 26.8, "duree": 1.0, "db": -16},
            {"type": "boom", "t": 41.5, "duree": 1.8, "db": -8},
            {"type": "riser", "t": 44.2, "duree": 5.1, "db": -13},
            {"type": "boom", "t": 49.3, "duree": 2.4, "db": -5},
        ],
        "noir_debut": 0.0, "noir_fin": 0.5,
    }


if __name__ == "__main__":
    lang, fmt = sys.argv[1], sys.argv[2]
    rapide = "--rapide" in sys.argv
    carton = ICI / f"carton-marque-{lang}-{fmt}.mp4"
    if not carton.exists():
        subprocess.run([sys.executable, str(VIDEO / "outils" / "carton_nexora.py"), str(carton), "--format", FORMATS[fmt],
                        "--version", "marque", "--lang", lang, "--duree", "10.7"], check=True)
    sortie = VIDEO / "final" / f"film-marque-{fmt}-{lang}{'-apercu' if rapide else ''}.mp4"
    montage = ICI / f"montage-hero-{lang}-{fmt}.json"
    montage.write_text(json.dumps(spec(fmt, lang, str(sortie)), indent=1, ensure_ascii=False))
    subprocess.run([sys.executable, str(VIDEO / "outils" / "film.py"), str(montage), *(["--rapide"] if rapide else [])], check=True)
