"""Écrit brief.json du film « Surveillance IA v2 » (les segments se ressemblent : on les génère plutôt que de les recopier)."""
import json
from pathlib import Path

P = "~/nexora-creative-data/site-medias-travail/plans/surv/"
G = 60 / 86.5 * 0.5            # grille : une croche à 86,5 BPM (mesuré sur surv-v2.flac)
g = lambda n: round(n * G, 4)  # noqa: E731
VOILE = {"v": 0.78, "h": 0.52}
VOILE_V = {"v": 0.80, "h": 0.46}


def plan(fichier, d, hud=False, debut=0.3, zoom=0.06):
    z = 0.0 if hud else zoom
    pl = P + fichier + ("-16x9-v1-hud-{l}-16x9.mp4" if hud else "-16x9-v1.mp4")
    pv = P + fichier + ("-16x9-v1-hud-{l}-9x16.mp4" if hud else "-9x16-v1.mp4")
    cad = [[0, 0.5, 0.5, 1.0], [d, 0.5, 0.5, round(1 - z, 3)]]
    return {"type": "plan", "d": d, "plaque": pl, "plaque_v": pv, "debut": debut, "cadre": cad, "cadre_vv": cad,
            "cadre_v": [[0, 0.5, 0.5, 1.0]], "voile": VOILE, "voile_v": VOILE_V, "textes": [], "sfx": []}


def fouet(db=-24):
    return {"t": 0.0, "type": "fouet", "duree": 0.35, "db": db}


seg = {}
a = plan("stationnement", g(12), hud=True, debut=0.12)
a["preuve"] = True
a["textes"] = [{"t": 0.15, "d": 1.9, "cle": "a1", "style": "titre", "zone": "bas", "taille": 1.3},
               {"t": g(6), "d": g(12) - g(6) - 0.05, "cle": "a2", "style": "impact", "zone": "bas", "taille": 1.2},
               {"t": 0.0, "d": g(12), "cle": "maq", "style": "sur", "zone": "bas", "y": 0.945, "y_v": 0.88}]
a["sfx"] = [{"t": 0.0, "type": "montee", "duree": g(6), "db": -20}, {"t": g(6), "type": "impact", "duree": 1.8, "db": -17}]
seg["hook"] = a

b = plan("murs", g(10))
b["textes"] = [{"t": 0.1, "d": g(10) - 0.2, "cle": "b1", "style": "titre", "zone": "bas", "taille": 1.3}]
b["sfx"] = [fouet()]
seg["murs"] = b

c = plan("stockage", g(12))
c["textes"] = [{"t": 0.1, "d": g(12) - 0.2, "cle": "c1", "style": "titre", "zone": "bas", "taille": 1.3}]
c["sfx"] = [fouet()]
seg["stockage"] = c

d = plan("entrepot", g(12), hud=True, debut=0.0)
d["voile_v"] = {"v": 0.80, "h": 0.40, "haut": True}
d["textes"] = [{"t": 0.1, "d": g(12) - 0.2, "cle": "d1", "style": "titre", "zone": "bas", "zone_v": "haut", "taille": 1.3},
               {"t": 0.0, "d": g(12), "cle": "maq", "style": "sur", "zone": "bas", "y": 0.945, "y_v": 0.88}]
d["sfx"] = [fouet(), {"t": 0.55, "type": "clic", "duree": 0.15, "db": -16}]
seg["entrepot"] = d

e = plan("alerte", g(12))
e["plaque"] = P + "alerte-16x9-v3.mp4"  # 16:9 : v3 (téléphone sans insigne) ; 9:16 : v1
e["textes"] = [{"t": 0.1, "d": g(12) - 0.2, "cle": "e_sur", "style": "sur", "zone": "bas", "y": 0.57, "y_v": 0.60},
               {"t": 0.25, "d": g(12) - 0.35, "cle": "e_pile", "style": "pile", "zone": "bas", "taille": 1.25}]
e["sfx"] = [fouet()] + [{"t": round(0.25 + 0.14 * k, 2), "type": "clic", "duree": 0.12, "db": -15} for k in range(4)]
seg["alerte"] = e

f = plan("intervention", g(10))
f["textes"] = [{"t": 0.1, "d": g(10) - 0.2, "cle": "f1", "style": "titre", "zone": "bas", "taille": 1.3}]
f["sfx"] = [fouet()]
seg["intervention"] = f

h = plan("rapport", g(12))
h["textes"] = [{"t": 0.1, "d": g(12) - 0.2, "cle": "g1", "style": "titre", "zone": "bas", "taille": 1.3}]
h["sfx"] = [fouet()]
seg["rapport"] = h

seg["silence"] = {"type": "noir", "d": g(1)}
seg["fin"] = {"type": "fin", "d": g(15), "t_marque": g(4), "sfx": [{"t": g(4), "type": "impact", "duree": 1.6, "db": -19}]}

q = lambda src, db=-3: {"segment": "fin", "source": src, "db": db}  # noqa: E731
mus = lambda: {"repere_segment": "hook", "repere_decalage": g(6), "arret_segment": "silence", "silence": "silence"}  # noqa: E731
V = {
    "long": {"cible": 36, "ordre": ["hook", "murs", "stockage", "entrepot", "alerte", "intervention", "rapport", "silence", "fin"],
             "musique": {**mus(), "queue": q(3.0)}},
    "30": {"cible": 30, "ordre": ["hook", "murs", "entrepot", "alerte", "intervention", "rapport", "silence", "fin"],
           "musique": {**mus(), "queue": q(3.0)}},
    "15": {"cible": 15, "ordre": ["hook", {"id": "alerte", "d": g(10)}, {"id": "rapport", "d": g(10)}, {"id": "silence"},
                                  {"id": "fin", "d": g(10), "t_marque": g(3)}],
           "musique": {**mus(), "queue": q(3.0)}},
}
T = {
    "fr": {
        "a1": "Personne ne regardait.", "a2": "Nos IA, *si.*", "maq": "Maquette illustrative",
        "b1": "Des milliers d'heures|de *vidéo.*", "c1": "Trop pour des *yeux humains.*",
        "d1": "Chaque caméra,|*en temps réel.*", "e_sur": "Alerte immédiate", "e_pile": "Texto|Courriel|Tableau de bord|*Application*",
        "f1": "Selon *vos consignes.*", "g1": "Un rapport|*par événement.*",
        "slogan": "Nos IA regardent.|Vous *décidez.*", "sous_titre": "Surveillance IA par Nexora.",
        "mentions": "Plans générés par IA · détections, alertes et rapports : maquette illustrative"},
    "en": {
        "a1": "Nobody was watching.", "a2": "Our AI *was.*", "maq": "Illustrative mock-up",
        "b1": "Thousands of hours|of *video.*", "c1": "Too much for *human eyes.*",
        "d1": "Every camera,|*in real time.*", "e_sur": "Immediate alert", "e_pile": "Text|Email|Dashboard|*App*",
        "f1": "Following *your rules.*", "g1": "A report|*for every event.*",
        "slogan": "Our AI watches.|You *decide.*", "sous_titre": "AI surveillance by Nexora.",
        "mentions": "AI-generated footage · detections, alerts and reports: illustrative mock-up"},
}
B = {
    "_gabarit": "Généré par fabriquer_brief.py (python3 fabriquer_brief.py) ; éditer le script, pas ce fichier.",
    "film": "surveillance-v2", "titre": "Surveillance IA : personne ne regardait, nos IA si", "nom_fichier": "Surveillance-IA-v2",
    "produit": "SURVEILLANCE IA", "date": "2026-11-02", "marque": "../../marque.json",
    "travail": "~/nexora-creative-data/promo/v5/surveillance", "captures": "~/nexora-creative-data/promo/v5/surveillance/ui",
    "concept": "Personne ne regarde des milliers d'heures de vidéo ; nos IA, si, en temps réel. Ouverture sur la preuve (la détection "
               "passe au rouge à 2,1 s, sur le coup de la musique), puis le problème en deux plans, la détection d'entrepôt, "
               "l'alerte (texto, courriel, tableau de bord, application), la consigne, le rapport.",
    "public": "responsables de sites (entrepôts, stationnements, commerces) qui enregistrent des heures de vidéo que personne ne revoit",
    "formats": ["16x9", "9x16"], "langues": ["fr", "en"], "affiche": {"t": 2.6, "langue": "fr"},
    "note_manifeste": "Plans vidéo générés par IA (H3) ; boîtes de détection et libellés posés en code : maquette illustrative, "
                      "aucune statistique. Remplace film-surveillance-* de la refonte « Signal ».",
    "commandes": {"plaques": "", "captures": ""},
    "musique": {"fichier": "~/nexora-creative-data/site-medias-travail/musique/surv-v2.flac",
                "brief": "Piste surv-v2 de la refonte, mesurée : 86,5 BPM (temps 0,6936 s) sur 12,3 à 40 s, coup fort à 12,5 s de la "
                         "source (18 temps), respiration de 9 à 12 s avant le coup. Posée pour que le coup tombe quand la boîte passe au rouge.",
                "bpm": 86.5, "subdivision": 0.5, "repere_source": 12.5},
    "segments": seg, "versions": V, "textes": T,
    "revue": {"date": "2026-11-02",
              "grille_severe": {"concept": 8, "preuve_rapide": 8.5, "textes": 7.5, "rythme": 7.5, "son": 6.5, "finition": 7.5, "authenticite": 8},
              "note": 7.6,
              "mesures": "long 33,3 s (PLAN : 40 s, recoupé sans remplissage), 30 s = 29,1 s, 15 s = 14,9 s ; boîte de détection à 0,1 s, passage au rouge et coup de musique à 2,08 s ; -14,0 LUFS ; crête vraie -1,7 dBTP ; plan moyen 3,7 s ; coupes sur la grille de 86,5 BPM ; respiration de la piste (22,35-22,9 s de la source) calée juste après une coupe",
              "faiblesses": ["musique et bruitages jugés aux chiffres, personne n'a écouté ; bruitages synthétiques",
                             "huit titres du même gabarit (blanc + mot orange en bas à gauche) : peu de variété typographique",
                             "plans 9:16 des deux caméras de surveillance recadrés dans le 16:9 (432x768) : mous ; titre de l'entrepôt en haut sur le bandeau CAM 12 atténué",
                             "plans murs, stockage et rapport : peu de mouvement (zoom lent de 6 %)",
                             "les boîtes de détection sont posées en code (maquette illustrative) ; aucune capture du produit réel",
                             "carton sans logo, mentions en petits caractères illisibles sur téléphone"]},
}
Path(__file__).with_name("brief.json").write_text(json.dumps(B, ensure_ascii=False, indent=1))
print("brief.json écrit")
