"""Film V6 « Trois mots. » : génère la liste de montage montage-v6.json (rendue par monter_v6.py).
Grille : Lyria 3 Pro n° 3, 124,81 BPM mesurés, phase 0,317 s. Le premier drop du morceau (temps 16, 8,009 s) tombe à 2,40 s
du film ; la reprise finale (temps 87, 42,14 s) tombe sur le temps 71 du film. Toutes les coupes sont sur les temps.
Recette : recherche/23 (plan fort avant 1 s, plans de 0,5 à 2,5 s, boucle phrase → plan toutes les 5 à 8 s, trous
musicaux pour le son natif, voix ≤ 25 % de la durée, 2 répliques dans l'image, mur de résultats, fin courte + scène bonus).
  python3 montage_v6.py > montage-v6.json      (V6_SANS_NARRATION=1 : seulement les répliques dans l'image)
"""
import json
import os
from pathlib import Path

D = Path.home() / "nexora-creative-data/promo/v6-creative"
R, C = D / "rushes", D / "captures"
BPM, PHASE_M = 124.81, 0.317
B = 60 / BPM
T0 = 2.40                      # temps 0 du film (= premier drop)
ENTREE = PHASE_M + 16 * B - T0  # point d'entrée dans le morceau


# prises retenues (contrôle plan par plan sur planches) ; None = pas encore tournée
P = {"s01_drop": 791, "s01_fpv": 809, "s01_alt": 790, "s01_v": 822, "s02_fpv": 797, "s02_b": 794, "s02_c": 793,
     "s03_a": 795, "s03_b": 796, "s03_v": 828, "s09": 812, "s07_fpv": 820, "s07_truck": 810, "s07_v": 826,
     "s08": 819, "s08_v": 811, "chat": 823, "chat_v": 825}
VOIX_FR = os.environ.get("V6_VOIX_FR", "h3-fr")
VOIX_EN = os.environ.get("V6_VOIX_EN", "h3-en")


def t(b):
    return round(T0 + b * B, 4)


def rush(n):
    return str(R / f"{n}.mp4")


def dial(nom):
    return str(R / "dialogues" / f"{nom}.mp4")


def vert(n):
    p = R / f"{n}.mp4" if n else None
    return str(p) if p and p.exists() else None


SEG = []
SFX = []


def plan(b0, b1, fichier, entree, **kw):
    s = {"type": "plan", "debut": t(b0), "duree": round(t(b1) - t(b0), 4), "fichier": fichier, "entree": entree}
    if kw.get("vertical"):
        v = kw.pop("vertical")
        if v:
            s["fichier_vertical"] = v
    s.update(kw)
    SEG.append(s)


def debut_abs(a, b, **kw):
    """Segment placé en secondes absolues (prologue avant le premier temps)."""
    s = {"debut": round(a, 4), "duree": round(b - a, 4), **kw}
    SEG.append(s)


ZONE_CHAMP = [100, 296, 532, 474]
ZONE_BOOST = [100, 490, 532, 765]


def saisie(b0, b1, plan_id, etapes=("vide", "saisie", "saisie-fin")):
    SEG.append({"type": "saisie", "debut": t(b0), "duree": round(t(b1) - t(b0), 4), "dossier": str(C / "boost" / plan_id),
                "etapes": list(etapes), "viewport": [1600, 900], "zone": ZONE_CHAMP, "zone_texte": [104, 300, 470, 345], "zoom_texte": 1.25, "zoom_texte_v": 2.0, "clavier_db": -16})


def boost(b0, b1, plan_id, termes, **kw):
    SEG.append({"type": "boost", "debut": t(b0), "duree": round(t(b1) - t(b0), 4), "dossier": str(C / "boost" / plan_id),
                "viewport": [1600, 900], "zone": ZONE_BOOST, "termes_cles": termes, **kw})


def titre(b0, b1, texte_id, style="claque", sur=None):
    s = {"type": "titre", "debut": t(b0), "duree": round(t(b1) - t(b0), 4), "texte_id": texte_id, "style": style}
    if sur:
        s["sur_video"] = sur
    SEG.append(s)


def chapitre(b0, b1, texte_id, media, **kw):
    SEG.append({"type": "chapitre", "debut": t(b0), "duree": round(t(b1) - t(b0), 4), "texte_id": texte_id, "media": media, **kw})


# ---------- PROLOGUE (avant le drop) : le plan le plus fort d'abord ----------
debut_abs(0.0, 0.72, type="plan", fichier=rush(791), entree=3.55, vitesse=1.0, etalonnage="nuit_feu", son_db=-2,
          cadrage=[[0, 0.62, 0.5, 1.25], [0.72, 0.6, 0.5, 1.12]], cadrage_v=[[0, 0.62, 0.5, 1.0], [0.72, 0.6, 0.5, 1.0]],
          secousses=[[0.05, 26, 0.45]])
debut_abs(0.72, 1.68, type="saisie", dossier=str(C / "boost/s01"), etapes=["saisie", "saisie-fin"], viewport=[1600, 900],
          zone=ZONE_CHAMP, zone_texte=[104, 300, 470, 345], zoom_texte=1.25, zoom_texte_v=2.0, clavier_db=-14)
debut_abs(1.68, T0, type="boost", dossier=str(C / "boost/s01"), viewport=[1600, 900], zone=ZONE_BOOST,
          termes_cles=["dragon", "château", "feu", "flammes", "rugissant", "travelling circulaire", "nuit"])
SFX += [{"t": 0.0, "type": "sub", "db": -4}, {"t": 0.0, "type": "impact", "db": -6}]

# ---------- ACTE 1 : le dragon ----------
plan(0, 3, rush(P["s01_drop"]), 2.9, vitesse=[[0, 1.0], [0.6, 0.45], [1.44, 0.6]], etalonnage="nuit_feu", son_db=-6,
     cadrage=[[0, 0.55, 0.5, 1.0], [1.44, 0.58, 0.48, 1.12]], cadrage_v=[[0, 0.62, 0.5, 1.0], [1.44, 0.66, 0.5, 1.0]],
     secousses=[[0.55, 18, 0.5]], vertical=vert(P["s01_v"]))
plan(3, 5, rush(P["s01_fpv"]), 2.0, vitesse=1.15, etalonnage="nuit_feu", son_db=-8,
     cadrage=[[0, 0.5, 0.5, 1.0], [0.96, 0.5, 0.5, 1.08]])
plan(5, 7, rush(P["s01_alt"]), 2.4, vitesse=1.2, etalonnage="nuit_feu", son_db=-8, cadrage=[[0, 0.5, 0.45, 1.05], [0.96, 0.52, 0.47, 1.15]])
titre(7, 8, "plus_gros", sur="precedent")
SFX.append({"t": t(7), "type": "impact", "db": -6})

# ---------- ACTE 2 : bataille spatiale ----------
saisie(8, 9.5, "s02", ("saisie", "saisie-fin"))
boost(9.5, 10.5, "s02", ["bataille spatiale", "vaisseaux", "laser", "explosions", "croiseurs", "planète"])
plan(10.5, 14, rush(P["s02_fpv"]), 1.6, vitesse=1.25, etalonnage="espace", son_db=-6,
     cadrage=[[0, 0.5, 0.5, 1.0], [1.68, 0.5, 0.52, 1.1]], secousses=[[1.0, 12, 0.6]])
plan(14, 15.5, rush(P["s02_b"]), 2.9, vitesse=1.3, etalonnage="espace", son_db=-8, cadrage=[[0, 0.5, 0.5, 1.0], [1.2, 0.48, 0.5, 1.1]])
plan(15.5, 20, dial("d1-pilote-fr-coupe"), 0.0, etalonnage="espace", son_db=-24, fichier_en=dial("d1-pilote-en-coupe"),
     cadrage=[[0, 0.42, 0.45, 1.0], [1.44, 0.42, 0.45, 1.08]], secousses=[[0.2, 14, 1.2]])
plan(20, 21, rush(P["s02_c"]), 3.6, vitesse=1.2, etalonnage="espace", son_db=-8, flash=[[0.5, "signal", 0.08]])
titre(21, 22, "plus_fou", sur="precedent")
SFX.append({"t": t(21), "type": "impact", "db": -6})

# ---------- ACTE 3 : duel aux lames d'énergie ----------
saisie(22, 23.5, "s03", ("saisie", "saisie-fin"))
boost(23.5, 24.5, "s03", ["sabres laser", "orange incandescent", "orage", "étincelles", "orbite", "ralenti"])
plan(24.5, 26.5, rush(P["s03_a"]), 1.9, vitesse=1.1, etalonnage="orage", son_db=-6, vertical=vert(P["s03_v"]), cadrage=[[0, 0.5, 0.45, 1.0], [1.2, 0.5, 0.45, 1.06]])
plan(26.5, 28, rush(P["s03_b"]), 2.4, vitesse=1.0, etalonnage="orage", son_db=-6)
plan(28, 31.5, dial("d2-duel-fr-coupe"), 0.0, etalonnage="orage", son_db=-24, fichier_en=dial("d2-duel-en-coupe"))
plan(31.5, 32.5, rush(P["s03_a"]), 3.6, vitesse=[[0, 0.35], [0.48, 0.35]], etalonnage="orage", son_db=0, flash=[[0.0, "os", 0.08]],
     cadrage=[[0, 0.5, 0.42, 1.25], [0.48, 0.5, 0.42, 1.32]])
titre(32.5, 33.5, "plus_grand", sur="precedent")
SFX.append({"t": t(32.5), "type": "impact", "db": -5})

# ---------- ACTE 4 : explosion au ralenti ----------
saisie(33.5, 35, "s09", ("saisie", "saisie-fin"))
boost(35, 36, "s09", ["explose", "ultra-ralenti", "flammes", "éclats de verre", "orbite", "crépuscule"])
plan(36, 41, rush(P["s09"]), 0.4, vitesse=[[0, 0.8], [0.8, 0.4], [2.4, 0.5]],
     etalonnage="aube", son_db=-4, secousses=[[0.05, 20, 0.6]])

# ---------- LA PALETTE (chapitres façon Kling) ----------
DET = C / "detourage/sorties"
SEG.append({"type": "avant_apres", "debut": t(41), "duree": round(t(45) - t(41), 4), "couches": [
    {"fichier": str(C / "detourage-src/duel-795.mp4"), "entree": 0.2, "texte_id": "brut"},
    {"fichier": str(DET / "apercu-echecs.mp4"), "entree": 0.2, "texte_id": "masque"},
    {"fichier": str(DET / "composite.mp4"), "entree": 0.2, "texte_id": "final"}],
    "textes": [{"t": 0.0, "duree": 1.9, "texte_id": "ch_detourage", "style": "balayage", "position": "haut"}]})
# image clé IA → vidéo : l'ingrédient reste visible (recherche 23, R5)
SEG.append({"type": "avant_apres", "debut": t(45), "duree": round(t(48) - t(45), 4), "couches": [
    {"fichier": str(R / "798.png"), "texte_id": "ch_image"},
    {"fichier": rush(P["s07_truck"]), "entree": 2.2, "texte_id": "ch_video"}]})
RELIEF = C / "relief"
if list(RELIEF.glob("*tour-textured*.jpg")):
    chapitre(48, 51, "ch_relief", {"dossier": str(RELIEF), "etapes": ["tour-wire", "tour-clay", "tour-textured"]})
else:  # repli : vraie capture de Relief d'une session précédente (captures-v3)
    chapitre(48, 51, "ch_relief", str(Path(__file__).resolve().parent.parent / "captures-v3/3d-texte-resultat.jpg"))
chapitre(51, 53, "ch_voix", {"fichier": dial("d1-pilote-fr-coupe"), "entree": 0.3, "fichier_en": dial("d1-pilote-en-coupe")})
chapitre(53, 54, "ch_studio", str(sorted((C / "studio2").glob("*editeur*.jpg"))[-1]))
chapitre(54, 55, "ch_marketing", str(C / "marketing/0033-propositions.jpg"))
mur = [rush(n) for n in (791, 797, 795, 812, 796, 810, 819, 809, 794) if (R / f"{n}.mp4").exists()]
SEG.append({"type": "mosaique", "debut": t(55), "duree": round(t(57) - t(55), 4), "rushes": [{"fichier": f, "entree": 1.5} for f in mur[:9]],
            "temps": [i * 0.107 for i in range(9)],
            "textes": [{"t": 0.45, "duree": 0.5, "texte_id": "ch_tout", "style": "grand", "position": "centre"}]})

# ---------- LE SILENCE : « et si t'écris… tout ? » ----------
SEG.append({"type": "saisie", "debut": t(57), "duree": round(t(62) - t(57), 4), "dossier": str(C / "boost/tout"),
            "dossier_en": str(C / "boost/tout-en"), "etapes": ["saisie", "saisie-fin"], "viewport": [1600, 900],
            "zone": ZONE_CHAMP, "zone_texte": [104, 300, 470, 345], "clavier_db": -10})
TOUS = " ".join(json.loads((C / "boost" / p / "boost.json").read_text())["boost"] for p in ("s01", "s02", "s03", "s09", "s07", "s08"))
SEG.append({"type": "boost", "debut": t(62), "duree": round(t(64) - t(62), 4), "dossier": str(C / "boost/s07"), "texte": TOUS,
            "viewport": [1600, 900], "zone": ZONE_BOOST, "termes_cles": ["dragon", "vaisseaux", "sabres laser", "explose", "flotte", "croiseur"]})
titre(64, 66, "tout", sur="suivant")
plan(66, 71, rush(P["s07_truck"]), 0.3, vertical=vert(P["s07_v"]), vitesse=1.0, etalonnage="espace", son_db=-6,
     cadrage=[[0, 0.5, 0.5, 1.0], [2.4, 0.5, 0.5, 1.12]])

# ---------- CLIMAX (reprise finale, temps 71) ----------
CLIMAX = [  # (rush, entree, temps, étalonnage)
    (P["s07_fpv"] if (R / f"{P['s07_fpv']}.mp4").exists() else P["s07_truck"], 1.0, 3, "espace"),
    (797, 3.2, 2, "espace"),
    (796, 3.6, 1, "orage"),
    (791, 4.1, 1, "nuit_feu"),
    (P["s09"], 1.8, 2, "aube"),
    (P["s01_fpv"], 3.6, 2, "nuit_feu"),
    (794, 3.8, 1, "espace"),
    (795, 4.2, 1, "orage"),
]
b = 71
for n, e, d, et in CLIMAX:
    plan(b, b + d, rush(n), e, vitesse=1.15, etalonnage=et, son_db=-8, flash=[[0.0, "os", 0.04]])
    SFX.append({"t": t(b), "type": "impact", "db": -9})
    b += d
FIN = P["s08"]
plan(b, b + 8, rush(FIN), 0.4, vitesse=0.9, etalonnage="aube", son_db=-10, vertical=vert(P["s08_v"]),
     cadrage=[[0, 0.5, 0.5, 1.0], [3.85, 0.5, 0.5, 1.06]])
b += 8
SEG.append({"type": "carton", "debut": t(b), "duree": round(t(b + 6) - t(b), 4)})
SFX.append({"t": t(b), "type": "boom", "db": -6})
b += 6

# ---------- SCÈNE BONUS : la faute de frappe qui donne un chat ----------
saisie(b, b + 2.5, "s10", ("saisie", "saisie-fin"))
boost(b + 2.5, b + 4, "s10", ["petit chat", "crache un jet de flammes", "comme un dragon", "ronronnement"])
CHAT = P["chat"] if P["chat"] and (R / f"{P['chat']}.mp4").exists() else None
if CHAT:
    plan(b + 4, b + 9, rush(CHAT), 0.6, vitesse=1.0, etalonnage="aube", son_db=-2, vertical=vert(P["chat_v"]),
         textes=[{"t": 0.5, "duree": 1.6, "texte_id": "bonus", "style": "legende", "position": "bas"}])
    b += 9
else:
    b += 4

# voix : une phrase par fichier ; le chuchoté v13 est la prise entière (« Chut ! Et si t'écris… tout ! »), « tout » tombe sur TOUT.
VOIX = [("v01", 0.72), ("v03", 2.08), ("v04", t(7) + 0.05), ("v06", t(21) + 0.05), ("v09", t(41) + 0.1), ("v10", t(48) + 0.1),
        ("v11", t(51) + 0.05), ("v12", t(55) + 0.5), ("v13", t(56) + 0.05), ("v14", t(84) + 0.3), ("v15", t(84) + 2.95), ("d1", t(15.5)), ("d2", t(28))]
print(json.dumps({
    "marque": "marque-v6.json", "bpm": BPM, "phase": T0,
    "musique": {"fichier": str(D / "musique/lyria-3.wav"), "entree": round(ENTREE, 4), "gain_db": -4, "ducking_db": 7,
                "trous": [[t(31.5), t(32.5)]]},
    "dossiers_voix": {"fr": str(D / "voix/narration" / VOIX_FR), "en": str(D / "voix/narration" / VOIX_EN)},
    "voix": [{"id": i, "t": round(x, 3), "db": 5 if i in ("v10", "v14", "v15") else 2} for i, x in VOIX
              if not os.environ.get("V6_SANS_NARRATION") or i.startswith("d")],
    "sfx": SFX,
    "duree": round(t(b), 4),
    "segments": SEG,
}, ensure_ascii=False, indent=1))
