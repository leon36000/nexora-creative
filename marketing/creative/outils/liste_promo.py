"""Liste de montage de la bande-annonce (monter.py), calée sur la bande originale b89 de MiniMax-Music3.
Instants (s) mesurés sur la musique : démarrage 0,47 ; braam 7,99 ; DROP 11,24 ; pulsation de 1 s de 17,12 à 20,03 ;
relance 23,54 ; grappe 26,85-31,75 ; 33,69 ; 35,65 ; 37,60 ; 41,51 (relance) ; 44,44 ; 45,42 ; 46,24 ; 48,38 ;
silence vers 52,6 ; IMPACT final 54,21.
Usage : python3 liste_promo.py rushes_dir cartons_dir musique.flac sortie.mp4 > liste.json"""
import json
import os
import sys
from pathlib import Path

R, C, MUSIQUE, SORTIE = (Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4])


def rush(nom: str) -> str:
    """5090 si le plan y existe ; ce choix est révisé à l'œil plan par plan (PREFERE)."""
    pref = PREFERE.get(nom[:3])
    for moteur in ([pref] if pref else []) + ["5090", "gb10"]:
        f = R / f"{nom}-{moteur}.mp4"
        if f.exists():
            return str(f)
    # Aperçu seulement : les premiers robots ressemblaient à des personnages de franchises connues, ils ne sont jamais
    # dans la version publiée (PREVIEW non défini = échec).
    if os.environ.get("PREVIEW") and nom.endswith("b"):
        return rush(nom[:-1])
    raise SystemExit(f"rush manquant : {nom}")


# Moteur retenu par plan après examen des planches (voir docs/JOURNAL.md).
PREFERE = {"p01": "5090", "p02": "gb10", "p03": "5090", "p04": "gb10", "p05": "gb10", "p06": "gb10", "p07": "gb10",
           "p08": "5090", "p09": "5090", "p10": "5090", "p11": "5090", "p12": "5090"}
seg = []
def carton(nom, fin): seg.append({"carton": str(C / nom), "fin": fin})
def plan(nom, debut, fin, **kw): seg.append({"plan": rush(nom), "debut": debut, "fin": fin, **kw})

carton("k1-dragon.mp4", 4.40)
plan("p01-dragon-nuages", 0.0, 11.24, vitesse=0.76)          # montée lente, rugissement sur le DROP
plan("p02-dragon-forteresse", 2.4, 13.23, flash=True)          # flash blanc sur le DROP
carton("k2-karate.mp4", 15.10)
plan("p03-karate-toit", 0.3, 17.12, ajuste=True)
plan("p04-karate-impact", 0.2, 18.09)                          # pulsation d'une seconde
plan("p03-karate-toit", 2.3, 19.08, ajuste=True)
plan("p04-karate-impact", 2.0, 20.03)
plan("p10-dragon-flotte", 0.5, 23.54, ajuste=True)
carton("k3-flotte.mp4", 25.78)
plan("p05-flotte-hyperespace", 0.0, 28.81, ajuste=True)
plan("p06-vaisseau-amiral", 0.8, 31.42)
plan("p07-duel-energie", 0.5, 33.69, ajuste=True)
plan("p07-duel-energie", 3.4, 35.65, ajuste=True)
plan("p08-lames-croisees", 0.5, 37.60)
plan("p09-voiture-robotb", 1.0, 41.51)
plan("p11-robot-atterritb", 1.5, 44.44, flash=True)
plan("p01-dragon-nuages", 4.3, 45.42)
plan("p02-dragon-forteresse", 3.6, 46.24)
plan("p12-finale-heros", 0.4, 52.55, vitesse=0.82, ajuste=True)
carton("k4-phrase.mp4", 54.21)
carton("k5-logo.mp4", 60.0)
print(json.dumps({"sortie": SORTIE, "musique": MUSIQUE, "bpm": 122.4, "sfx_db": -9, "musique_db": 0, "silences": [[52.75, 54.15]], "segments": seg}, indent=1))
