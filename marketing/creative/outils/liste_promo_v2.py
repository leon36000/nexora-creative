"""Liste de montage v2 de la bande-annonce Nexora Creative (monter.py), calée sur la bande originale b89 de MiniMax-Music3.

Deux versions, même structure :
  public : uniquement des plans H3 texte → vidéo (aucun plan clé Qwen-Image-2.1, dont la licence est non commerciale) ;
  demo   : remplace deux plans par leurs versions « plan clé Qwen → H3 » (démonstration privée aux investisseurs).
Instants de la musique (s) : démarrage 0,47 ; braam 7,99 ; DROP 11,24 ; pulsation de 1 s de 17,12 à 20,03 ; relance 23,54 ;
grappe 26,85-31,75 ; 33,69 ; 35,65 ; 37,60 ; 41,51 (relance) ; 44,44 ; 45,42 ; 46,24 ; 48,38 ; silence 52,75-54,15 ; IMPACT 54,21.
Usage : python3 liste_promo_v2.py public|demo rushes_dir cartons_dir musique.flac sortie.mp4 correspondance.json > liste.json
correspondance.json : { "<nom de plan>": "/chemin/fichier.mp4", ... } pour les plans de la v2.
"""
import json
import sys
from pathlib import Path

VERSION, R, C, MUSIQUE, SORTIE, CORR = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5], json.loads(Path(sys.argv[6]).read_text())
DEMO = VERSION == "demo"

V1 = {"p01": "5090", "p02": "gb10", "p03": "5090", "p04": "gb10", "p05": "gb10", "p06": "gb10", "p07": "gb10", "p08": "5090",
      "p09": "5090", "p10": "5090", "p11": "5090", "p12": "5090"}


def rush(nom: str) -> str:
    """Un plan de la v2 (CORR) ou un rush de la v1 (dossier des rushes)."""
    if nom in CORR:
        return CORR[nom]
    for moteur in [V1.get(nom[:3], "5090"), "5090", "gb10"]:
        f = R / f"{nom}-{moteur}.mp4"
        if f.exists():
            return str(f)
    raise SystemExit(f"plan manquant : {nom}")


seg, ajouts = [], []
def carton(nom, fin): seg.append({"carton": str(C / nom), "fin": fin})
def plan(nom, debut, fin, **kw): seg.append({"plan": rush(nom), "debut": debut, "fin": fin, **kw})
def whoosh(coupe, d=0.9, db=10): ajouts.append({"type": "whoosh", "t": round(coupe - 0.62 * d, 3), "duree": d, "db": db})
def boom(t, d=2.4, db=9): ajouts.append({"type": "boom", "t": t, "duree": d, "db": db})
def riser(fin, d=3.0, db=-7): ajouts.append({"type": "riser", "t": round(fin - d, 3), "duree": d, "db": db})

# --- Acte I : le calme, la montée (0 → 11,24)
carton("k1-dragon.mp4", 4.40)
plan("p01-dragon-nuages", 0.0, 11.24, vitesse=0.76)
riser(11.24)
# --- Acte II : le DROP, la Terre et la flotte (11,24 → 23,54)
# Le saut en hyperespace (traînées d'étoiles) mène au flash blanc exactement sur la révélation de la Terre (13,23).
plan("terre-saut", 0.35, 13.23, flash=True, recadre=0.62, cy=0.1); boom(11.24, 2.0, 7)
plan("terre-flotte-demo" if DEMO else "terre-flotte", 0.3, 17.12, zoom=0.05); boom(13.23, 2.6, 10); whoosh(13.23)
plan("sabres-mer-demo" if DEMO else "sabres-mer", 1.1, 18.09, zoom=0.05); whoosh(17.12, 0.6, 9)
plan("p04-karate-impact", 0.2, 19.08); whoosh(18.09, 0.6, 9)
plan("sabres-mer-demo" if DEMO else "sabres-mer", 4.0, 20.03); whoosh(19.08, 0.6, 9)
plan("terre-croiseur", 0.4, 23.54, zoom=0.05); whoosh(20.03)
# --- Acte III : les duels (23,54 → 41,51)
carton("k6-sabre.mp4", 25.78); boom(23.54, 1.6, 5); whoosh(23.54, 1.0)
plan("sabres-hangar", 1.8, 28.81); whoosh(25.78)
plan("sabres-ruines", 1.9, 31.42, zoom=0.05); whoosh(28.81, 0.7, 9)
plan("p07-duel-energie", 0.5, 33.69, zoom=0.05); whoosh(31.42, 0.6, 9)
plan("p03-karate-toit", 1.2, 35.65); whoosh(33.69, 0.6, 9)
plan("sabres-hangar", 0.3, 37.60); whoosh(35.65, 0.6, 9)
plan("p08-lames-croisees", 0.5, 39.24); whoosh(37.60, 0.6, 9)
plan("p09-voiture-robotb", 1.0, 41.51); whoosh(39.24, 0.6, 9)
riser(41.51, 2.4, -8)
# --- Acte IV : le climax (41,51 → 52,55)
plan("p11-robot-atterritb", 1.5, 44.44, flash=True); boom(41.51, 2.4, 10)
plan("terre-croiseur", 2.6, 45.42); whoosh(44.44, 0.6, 9)
plan("p02-dragon-forteresse", 3.6, 46.24); whoosh(45.42, 0.5, 9)
plan("terre-flotte-demo" if DEMO else "terre-flotte", 2.4, 48.38, zoom=0.05); whoosh(46.24, 0.5, 9)
plan("p12-finale-heros", 0.4, 52.55, vitesse=0.82, ajuste=True); whoosh(48.38, 0.8, 8)
# --- Silence (52,75 → 54,15), puis l'IMPACT et le logo
carton("k4-phrase.mp4", 54.21)
boom(54.21, 3.8, 12)
carton("k5-logo.mp4", 60.0)
print(json.dumps({"sortie": SORTIE, "musique": MUSIQUE, "bpm": 122.4, "sfx_db": -9, "musique_db": 0, "silences": [[52.75, 54.15]],
                  "ajouts_son": ajouts, "segments": seg}, indent=1))
