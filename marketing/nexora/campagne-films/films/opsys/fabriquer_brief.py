"""Écrit brief.json du film OPSYS-AI (python3 fabriquer_brief.py [cles|h3]).

« cles » : les plans pointent vers les images clés Qwen (animatique) ; « h3 » (défaut) : vers les plans H3 choisis (CHOIX).
Grille : piste opsys-musique-71 mesurée à 88,63 BPM (temps 0,6770 s ; grille = demi-temps 0,3385 s ; mesure = 8 grilles).
Le coup de la source à 6,188 s tombe à l'apparition de l'avatar ; celui de 53,5 s tombe à sa deuxième apparition.
"""
import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
W = "~/nexora-creative-data/promo/v6/opsys/"
PL, AV = W + "plaques/", W + "avatar/"
BPM = 88.63
G = 60 / BPM / 2
g = lambda n: round(n * G, 4)  # noqa: E731
MES = 8
PHASE = sys.argv[1] if len(sys.argv) > 1 else "h3"
# plan H3 retenu par plan (après visionnage) ; absent = rapide
CHOIX = {"l4-hockey": "max2", "m3-maison": "max", "l1-course": "max"}
VOILE = {"v": 0.80, "h": 0.50}
VOILE_V = {"v": 0.82, "h": 0.44}


def plan(i, d, zoom=0.07):
    f = PL + (f"{i}-cle.png" if PHASE == "cles" else f"{i}-{CHOIX.get(i, 'rapide')}.mp4")
    cad = [[0, 0.5, 0.5, 1.0], [d, 0.5, 0.5, round(1 - zoom, 3)]]
    return {"type": "plan", "d": d, "plaque": f, "cle": PL + f"{i}-cle.png", "debut": 0.2, "cadre": cad,
            "cadre_v": [[0, 0.5, 0.5, 1.0], [d, 0.5, 0.5, 0.95]], "voile": VOILE, "voile_v": VOILE_V,
            "textes": [], "sfx": [{"t": 0.0, "type": "fouet", "duree": 0.3, "db": -26}]}


def avatar(cle, d, duck=-11.0):
    return {"type": "plan", "d": d, "plaque": AV + f"avatar-{cle}-{{l}}-16x9.mp4", "plaque_v": AV + f"avatar-{cle}-{{l}}-9x16.mp4",
            "debut": 0.0, "cadre": [[0, 0.5, 0.5, 1.0], [d, 0.52, 0.48, 0.94]], "cadre_vv": [[0, 0.5, 0.5, 1.0], [d, 0.5, 0.47, 0.94]],
            "cadre_v": [[0, 0.5, 0.5, 1.0]], "son_h3": 3.0, "duck": duck, "en_preparation": True,
            "textes": [{"t": 0.0, "d": d, "cle": "vision", "style": "prepa", "zone": "bas", "y": 0.90, "y_v": 0.93}],
            "sfx": [{"t": 0.0, "type": "impact", "duree": 1.6, "db": -18}]}


seg = {}
seg["q1"] = {"type": "noir", "d": g(10), "textes": [{"t": 0.25, "d": g(10) - 0.25, "cle": "q1", "style": "citation", "zone": "centre",
                                                     "align": "centre", "guillemets": False, "frappe": 1.1, "taille": 1.9}],
             "sfx": [{"t": 0.25 + 0.09 * k, "type": "clic", "duree": 0.05, "db": -30} for k in range(12)]
             + [{"t": 1.6, "type": "montee", "duree": g(10) - 1.6, "db": -24}]}
seg["a"] = avatar("a", g(26))
seg["a15"] = avatar("a15", g(15))
seg["dix"] = {"type": "noir", "d": g(MES), "textes": [{"t": 0.05, "d": g(MES) - 0.05, "cle": "dix", "style": "impact", "zone": "centre",
                                                       "align": "centre", "taille": 0.9}],
              "sfx": [{"t": 0.0, "type": "impact", "duree": 1.4, "db": -19}]}
VIE = {"l1-course": "v1", "l2-dejeuner": "v2", "l3-terrasse": "v3", "l4-hockey": "v4"}
DEP = {"m1-appel": "d1", "m3-maison": "d3", "m4-camion": "d4", "m6-entrepot": "d6", "m5-bureau": "d5", "m7-photo": "d7",
       "m2-porte": "d2", "m9-matin": "d9"}
for i, k in VIE.items():
    s = plan(i, g(MES))
    s["voile"], s["voile_v"] = {"v": 0.55, "h": 1.0}, {"v": 0.6, "h": 1.0}
    s["textes"] = [{"t": 0.0, "d": g(MES), "cle": k + "h", "style": "sur", "zone": "centre", "align": "centre", "taille": 1.7,
                    "y": 0.38, "y_v": 0.40},
                   {"t": 0.1, "d": g(MES) - 0.1, "cle": k, "style": "impact", "zone": "centre", "align": "centre", "taille": 1.0}]
    seg[i] = s
for i, k in DEP.items():
    s = plan(i, g(MES))
    s["textes"] = [{"t": 0.0, "d": g(MES), "cle": k + "m", "style": "sur", "zone": "bas", "y": 0.585, "y_v": 0.585, "taille": 1.5},
                   {"t": 0.12, "d": g(MES) - 0.12, "cle": k, "style": "titre", "zone": "bas", "taille": 1.25}]
    s["sfx"].append({"t": 0.0, "type": "clic", "duree": 0.12, "db": -20})
    seg[i] = s
seg["q2"] = {"type": "noir", "d": g(MES), "textes": [{"t": 0.2, "d": g(MES) - 0.2, "cle": "q2", "style": "citation", "zone": "centre",
                                                      "align": "centre", "guillemets": False, "frappe": 1.2, "taille": 1.9}],
             "sfx": [{"t": 0.2 + 0.09 * k, "type": "clic", "duree": 0.05, "db": -30} for k in range(13)]}
seg["b"] = avatar("b", g(20))
seg["ok"] = {"type": "noir", "d": g(4), "textes": [{"t": 0.05, "d": g(4) - 0.05, "cle": "ok", "style": "impact", "zone": "centre",
                                                    "align": "centre"}],
             "sfx": [{"t": 0.0, "type": "clic", "duree": 0.15, "db": -12}, {"t": 0.02, "type": "impact", "duree": 1.2, "db": -18}]}
m10 = avatar("a", g(MES))
m10.update({"debut": 3.0, "cadre": [[0, 0.62, 0.50, 0.42], [g(MES), 0.62, 0.50, 0.34]], "cadre_vv": [[0, 0.44, 0.36, 0.5],
            [g(MES), 0.44, 0.36, 0.42]], "son_h3": None, "duck": None, "en_preparation": False, "voile": VOILE, "voile_v": VOILE_V,
            "textes": [{"t": 0.0, "d": g(MES), "cle": "d10m", "style": "sur", "zone": "bas", "y": 0.585, "y_v": 0.585, "taille": 1.5},
                       {"t": 0.12, "d": g(MES) - 0.12, "cle": "d10", "style": "titre", "zone": "bas", "taille": 1.25}],
            "sfx": [{"t": 0.0, "type": "fouet", "duree": 0.3, "db": -26}]})
seg["m10"] = m10
seg["liste"] = {"type": "noir", "d": g(12), "textes": [{"t": round(0.27 * k, 2), "d": g(12) - round(0.27 * k, 2), "cle": f"n{k + 1}",
                                                        "style": "sur", "zone": "centre", "align": "centre", "taille": 1.9,
                                                        "y": round(0.12 + 0.076 * k, 3), "y_v": round(0.25 + 0.052 * k, 3)} for k in range(10)],
                "sfx": [{"t": round(0.27 * k, 2), "type": "clic", "duree": 0.08, "db": -22} for k in range(10)]
                + [{"t": 0.0, "type": "montee", "duree": g(12), "db": -22}]}
seg["grande"] = {"type": "noir", "d": g(10), "textes": [{"t": 0.05, "d": g(10) - 0.05, "cle": "grande", "style": "titre",
                                                         "zone": "centre", "align": "centre"}],
                 "sfx": [{"t": 0.0, "type": "impact", "duree": 1.6, "db": -18}]}
seg["silence"] = {"type": "noir", "d": g(1)}
seg["fin"] = {"type": "fin", "d": g(16), "t_marque": g(4), "sfx": [{"t": g(4), "type": "impact", "duree": 1.8, "db": -17}]}

MONTAGE = ["l1-course", "m1-appel", "m3-maison", "l2-dejeuner", "m4-camion", "m6-entrepot", "m5-bureau", "l3-terrasse",
           "m7-photo", "m2-porte", "m9-matin", "l4-hockey"]
q = lambda src, db=-2: {"segment": "fin", "source": src, "db": db}  # noqa: E731
mus = lambda rep: {"repere_segment": rep, "repere_decalage": 0.0, "arret_segment": "silence", "silence": "silence"}  # noqa: E731
V = {
    "long": {"cible": 90, "ordre": ["q1", "a", "dix", *MONTAGE, "q2", "b", "ok", "m10", "liste", "grande", "silence", "fin"],
             "musique": {**mus("a"), "queue": q(69.0)}},
    "30": {"cible": 30, "ordre": ["q1", "a15", "dix", "m1-appel", "m3-maison", "m5-bureau", "l4-hockey", "silence",
                                  {"id": "fin", "d": g(14), "t_marque": g(3)}],
           "musique": {**mus("a15"), "queue": q(69.0)}},
    "15": {"cible": 15, "ordre": ["a15", "m3-maison", "l4-hockey", "silence", {"id": "fin", "d": g(12), "t_marque": g(3)}],
           "musique": {**mus("a15"), "queue": q(69.0)}},
}
NOMS = {"fr": ["M1 Réception", "M2 CRM", "M3 Estimation", "M4 Terrain", "M5 Finance", "M6 Matériel", "M7 Marketing",
               "M8 Analytique", "M9 Stratégie", "M10 Mémoire"],
        "en": ["M1 Front office", "M2 CRM", "M3 Estimating", "M4 Field ops", "M5 Finance", "M6 Materials", "M7 Marketing",
               "M8 Analytics", "M9 Strategy", "M10 Memory"]}
T = {
    "fr": {"q1": "« Opsys, on en est où ? »", "vision": "Vision · en développement",
           "dix": "Dix départements.|*Une seule équipe.*",
           "v1h": "06 h 12", "v1": "Vous *courez.*", "v2h": "07 h 40", "v2": "Vous *déjeunez.*",
           "v3h": "17 h 45", "v3": "Vous *respirez.*", "v4h": "19 h 30", "v4": "Vous êtes *là.*",
           "d1m": "M1 · Réception", "d1": "Chaque demande,|*qualifiée.*",
           "d3m": "M3 · Estimation", "d3": "La soumission,|*prête* au réveil.",
           "d4m": "M4 · Terrain", "d4": "L'équipe,|au *bon* chantier.",
           "d6m": "M6 · Matériel", "d6": "Le matériel,|*réservé.*",
           "d5m": "M5 · Finance", "d5": "Chantier fini.|Facture *prête.*",
           "d7m": "M7 · Marketing", "d7": "Votre chantier devient|une *publication.*",
           "d2m": "M2 · CRM", "d2": "Aucun client|*oublié.*",
           "d9m": "M9 · Stratégie", "d9": "Votre briefing,|à *7 h.*",
           "q2": "« Le deuxième camion, on peut ? »", "ok": "*Approuvé.*",
           "d10m": "M10 · Mémoire", "d10": "Chaque décision,|*retenue.*",
           "grande": "Une grande entreprise.|À *votre* taille.",
           "slogan": "Ils travaillent.|Vous *vivez.*", "sous_titre": "Dix départements IA pour votre PME.",
           "mentions": "Film de vision : avatar et envois en développement · plans générés par IA · visage animé par Audio2Face-3D · voix synthétique"},
    "en": {"q1": "“Opsys, where are we?”", "vision": "Vision · in development",
           "dix": "Ten departments.|*One team.*",
           "v1h": "6:12 a.m.", "v1": "You *run.*", "v2h": "7:40 a.m.", "v2": "You have *breakfast.*",
           "v3h": "5:45 p.m.", "v3": "You *breathe.*", "v4h": "7:30 p.m.", "v4": "You're *there.*",
           "d1m": "M1 · Front office", "d1": "Every request,|*qualified.*",
           "d3m": "M3 · Estimating", "d3": "The quote,|*ready* by morning.",
           "d4m": "M4 · Field ops", "d4": "The crew,|at the *right* job.",
           "d6m": "M6 · Materials", "d6": "Materials,|*reserved.*",
           "d5m": "M5 · Finance", "d5": "Job done.|Invoice *ready.*",
           "d7m": "M7 · Marketing", "d7": "Your finished job|becomes a *post.*",
           "d2m": "M2 · CRM", "d2": "No client|*forgotten.*",
           "d9m": "M9 · Strategy", "d9": "Your briefing,|at *7 a.m.*",
           "q2": "“Can we afford a second truck?”", "ok": "*Approved.*",
           "d10m": "M10 · Memory", "d10": "Every decision,|*remembered.*",
           "grande": "Big-company muscle.|At *your* size.",
           "slogan": "They work.|You *live.*", "sous_titre": "Ten AI departments for your business.",
           "mentions": "Vision film: avatar and outbound sending in development · AI-generated footage · face animated by Audio2Face-3D · synthetic voice"},
}
for l in T:
    for k, n in enumerate(NOMS[l]):
        T[l][f"n{k + 1}"] = n

brief = {
    "_gabarit": "Généré par fabriquer_brief.py ; éditer le script, pas ce fichier.",
    "film": "opsys", "titre": "OPSYS-AI : Ils travaillent. Vous vivez.", "nom_fichier": "OPSYS-AI", "produit": "OPSYS-AI",
    "date": "2026-11-02", "marque": "../../marque.json", "travail": W + "film", "captures": W + "captures",
    "concept": "Film de vision : la journée d'un entrepreneur pendant que ses dix départements OPSYS travaillent ; au centre, "
               "l'avatar (visage animé par Audio2Face-3D à partir de sa voix) répond et demande l'accord. Voir CONCEPT.md et FAITS.md.",
    "public": "propriétaires de PME de services (rénovation au Québec d'abord) qui font tout eux-mêmes",
    "formats": ["16x9", "9x16"], "langues": ["fr", "en"], "affiche": {"t": 6.0, "langue": "fr"},
    "note_manifeste": "Film de vision. Plans de vie et de chantier générés par IA (Qwen-Image puis H3). Avatar : visage animé par "
                      "NVIDIA Audio2Face-3D v2.3.1 (modèle ouvert, exécuté localement en ONNX), rendu « Signal » maison, voix "
                      "synthétique Kokoro-82M ; répliques écrites pour le film. La conversation vocale avec un avatar n'existe pas "
                      "encore dans OPSYS-AI (vision) ; aucun composant NVIDIA ACE autre qu'Audio2Face-3D n'est utilisé.",
    "commandes": {"plaques": "", "captures": ""},
    "musique": {"fichier": W + "audio/opsys-musique-71.flac",
                "brief": "MiniMax-Music3 graine 71 (demandé 100 BPM, 94 s ; rendu 76,9 s), mesuré 88,63 BPM (demi-temps 0,3385 s, "
                         "phase 0,095 s) ; coups à 6,19 s, 33,0 s, 36,25 s, 53,5 s ; cassure 34-37 s.",
                "bpm": BPM, "subdivision": 0.5, "repere_source": 6.1885},
    "segments": seg, "versions": V, "textes": T,
    "revue": {"date": "2026-11-02",
              "grille_severe": {"concept": 8, "reve_emotion": 7.5, "avatar": 6.5, "rythme": 7.5, "spectacle": 6.5, "textes": 8,
                                "son": 6.5, "finition": 7.5, "authenticite": 6},
              "note": 7.1,
              "mesures": "long 74,1 s, 30 s = 27,1 s, 15 s = 14,9 s ; avatar à 3,4 s (long), 0 s (15) ; coupes sur la grille de 88,63 BPM "
                         "(demi-temps 0,3385 s) ; montage des départements : 12 plans de 2,71 s (une mesure) ; plan moyen 3,2 s ; avatar a "
                         "8,8 s, b 6,8 s ; -14,5/-14,6 LUFS (long), -14,3 (30), -15,2 (15) ; crête vraie ≤ -2,0 dBTP ; musique baissée de "
                         "11 dB sous la voix (vérifié à l'enveloppe : voix ≈ -15 dB, musique seule ≈ -33 dB avant réglage à -11).",
              "faiblesses": [
                  "aucune capture réelle d'OPSYS : aucune instance ne tourne ici ; c'est un film de vision (authenticité 6)",
                  "avatar : visage générique « Claire » du modèle NVIDIA, sans cheveux ni peau, rendu en points ; synchronisation labiale "
                  "réelle (Audio2Face-3D) mais personne ne l'a regardée avec le son ; tête animée par code, pas par le modèle",
                  "voix Kokoro française (accent de France), pas québécoise ; anglaise correcte ; aucune écoute humaine",
                  "musique Music3 graine 71 : structure demandée non respectée (76,9 s au lieu de 94, 88,6 BPM au lieu de 100) ; "
                  "bruitages synthétiques ; 15 s à -15,2 LUFS",
                  "image très sombre et toute bleue : peu de contraste de lumière entre les séquences ; pas de grand mouvement de caméra",
                  "plans 9:16 recadrés dans le 16:9 (432 px de large avant agrandissement) : mous",
                  "titres des départements tous sur le même gabarit (surtitre + deux lignes en bas à gauche)"]},
}
(ICI / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1))
print("brief.json écrit :", PHASE)
