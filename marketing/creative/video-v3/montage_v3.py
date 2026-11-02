"""Liste de montage de la promo V3 (génère montage-v3.json pour monter_v3.py). Le montage suit la musique.

Bande originale : MiniMax-Music3 graine 31 (audio/v3-musique-31.flac), posée à +1,25 s (film = source + 1,25).
Coups de la source relevés par analyse (outils d'attaques) : motif 5,26 · 7,54 · 11,05 · 12,59 · 14,62 · DROP 16,75 ·
18,09 · 19,97 · 23,07 · 24,36 · 25,38 · 30,09 · 32,05 · 35,16 · 36,70 · 37,92 · 38,94 · 40,55-41,84 (pulsations 0,43 s) ·
CLIMAX 43,55 puis un coup toutes les ≈ 0,43 s jusqu'à 50,41 · fin du morceau 53.
Courbe d'énergie (0-10) : ouverture 1 → montée 3-5 → drop 8 → action 7-8 → respiration 5 → climax 10 → silence 0 → coup final 9.
Usage : python3 montage_v3.py > montage-v3.json
"""
import json

O = 1.25  # décalage musique → film
MUS = "~/nexora-creative-data/promo/v3/audio/v3-musique-31.flac"
P = "~/nexora-creative-data/promo/v3/plans/"


def f(src):
    """Instant film d'un coup de la musique source."""
    return round(src + O, 3)


# ------------------------------------------------------------------------------------------------ plans (plaques + couches)
FLOTTE_LOIN = {"type": "flotte", "n": 1400, "zone": [0, 0.15, 1, 0.85], "mur": True, "profondeur": [2, 9], "taille": [1.5, 4],
               "derive": [-14, 0], "moteurs": "bleu", "lueur": 0.8}
TIRS_O = {"type": "traceurs", "par_s": 40, "source": [0, 0.45, 0.35, 0.9], "cible": [0.55, 0.1, 1, 0.55], "couleur": "orange", "rafale": 6,
          "cadence": 0.07, "impacts": 0.3, "vitesse": 1.5, "longueur": 0.06, "epaisseur": 2.4}
TIRS_B = {"type": "traceurs", "par_s": 8, "source": [0.65, 0.05, 1, 0.45], "cible": [0, 0.4, 0.5, 0.95], "couleur": "bleu", "longueur": 0.09,
          "vitesse": 1.0, "epaisseur": 3.4, "rafale": 3, "cadence": 0.12}
LOIN_BOUM = {"type": "explosions", "par_s": 2.5, "zone": [0.05, 0.12, 0.95, 0.75], "taille": [8, 28], "duree": 1.1}


VERTICAUX = {"p01-orbite-nuit", "p02-mur-flotte", "p03-vague-ennemie", "p04-bordee", "p07-pilote", "p08-vaisseau-mere", "p09-rupture", "p10-aube"}


def plan(nom, **kw):
    """Plaque 16:9 ; en 9:16, la plaque rendue nativement en vertical (768×1344) quand elle existe, sinon recadrage."""
    return {"plaque": P + nom + ".mp4", **({"plaque_v": P + nom + "-v.mp4"} if nom in VERTICAUX else {}), **kw}


PLANS = {
    "p01-orbite-nuit": plan("p01-orbite-nuit", cadre=[[0, 0.5, 0.55, 1.0], [6, 0.5, 0.55, 1.06]], secousse={"base": 0, "derive": 2},
                            effets=[{**FLOTTE_LOIN, "n": 900, "zone": [0, 0.45, 1, 1.0], "taille": [1, 3], "lueur": 0.6, "derive": [-6, 0]}],
                            son_h3=-22, etalonnage={"exposition": 0.95}),
    "p02-mur-flotte": plan("p02-mur-flotte", suivi=True, cadre=[[0, 0.5, 0.5, 1.02], [5, 0.48, 0.5, 1.1]], secousse={"base": 1.5},
                           effets=[{**FLOTTE_LOIN, "zone": [0.3, 0.05, 1, 0.6], "derive": [-10, 2]}], son_h3=-8),
    "p03-vague-ennemie": plan("p03-vague-ennemie", suivi=True, cadre=[[0, 0.5, 0.5, 1.0], [5, 0.5, 0.5, 1.15]], secousse={"base": 5},
                              effets=[{"type": "flotte", "n": 2600, "zone": [0, 0, 1, 1], "profondeur": [1, 7], "taille": [1.5, 5], "derive": [0, 0],
                                       "agitation": 30, "moteurs": "rouge", "lueur": 0.6, "cap": 2.6, "dispersion_cap": 0.4}], son_h3=-6),
    "p04-bordee": plan("p04-bordee", suivi=True, secousse={"base": 6, "coups": [{"t": 0.0, "force": 40}, {"t": 0.9, "force": 25}, {"t": 1.7, "force": 25}]},
                       effets=[{**TIRS_O, "par_s": 70, "source": [0.1, 0.35, 0.8, 0.7], "cible": [0.6, 0.0, 1.2, 0.3]}, LOIN_BOUM,
                               {"type": "flash", "t": 0.0, "force": 1.2, "couleur": "ambre", "duree": 0.3}], impact=True, son_h3=-2),
    "p05-hangar": plan("p05-hangar", secousse={"base": 7}, cadre=[[0, 0.5, 0.5, 1.05]], son_h3=-6),
    "p06-cockpit": plan("p06-cockpit", secousse={"base": 9}, suivi=True,
                        effets=[{**TIRS_O, "source": [0.2, 0.9, 0.8, 1.1], "cible": [0.3, 0.2, 0.7, 0.45], "par_s": 30}, LOIN_BOUM], son_h3=-4),
    "p07-pilote": plan("p07-pilote", secousse={"base": 6, "coups": [{"t": 0.6, "force": 18}]},
                       effets=[{"type": "flash", "t": 0.6, "force": 0.6, "couleur": "orange", "duree": 0.5}], son_h3=-6),
    "p08-vaisseau-mere": plan("p08-vaisseau-mere", suivi=True, secousse={"base": 7, "coups": [{"t": 0.0, "force": 35}]},
                              effets=[{**FLOTTE_LOIN, "n": 600, "moteurs": "bleu", "derive": [-40, 0]}, {**TIRS_B, "par_s": 30}, LOIN_BOUM,
                                      {"type": "flash", "t": 0.0, "force": 1.4, "couleur": "blanc", "duree": 0.25}], son_h3=-2),
    "p09-rupture": plan("p09-rupture", secousse={"base": 6, "coups": [{"t": 0.2, "force": 30}]}, suivi=True,
                        effets=[{"type": "debris", "t": 0.1, "origine": [0.5, 0.45], "n": 140, "vitesse": 650, "vers_camera": 0.9, "braises": 0.6}],
                        son_h3=-3),
    "p10-aube": plan("p10-aube", cadre=[[0, 0.5, 0.5, 1.0], [5, 0.5, 0.5, 1.05]], secousse={"base": 0, "derive": 3}, son_h3=-12),
    "t01-passage": plan("t01-passage", secousse={"base": 10}, fouet={"sortie": 4, "sens": 1},
                        effets=[TIRS_O, TIRS_B, LOIN_BOUM, {**FLOTTE_LOIN, "n": 700, "derive": [-80, 0]}], son_h3=-3),
    "t02-poursuite": plan("t02-poursuite", secousse={"base": 9}, suivi=True, effets=[TIRS_B, LOIN_BOUM], son_h3=-3),
    "t03-torpilles": plan("t03-torpilles", secousse={"base": 4}, effets=[{**FLOTTE_LOIN, "n": 500}], son_h3=-4),
    "t04-explosion": plan("t04-explosion", cadre=[[0, 0.5, 0.5, 1.45]], cadre_v=[[0, 0.5, 0.5, 1.0]], secousse={"base": 5, "coups": [{"t": 0.0, "force": 45, "tenue": 0.4}]},
                          effets=[{"type": "flash", "t": 0.0, "force": 1.6, "couleur": "orange", "duree": 0.35},
                                  {"type": "debris", "t": 0.05, "origine": [0.5, 0.5], "n": 160, "vitesse": 900, "vers_camera": 1.4, "braises": 0.7}],
                          impact=True, son_h3=-2),
    "t05-onde-choc": plan("t05-onde-choc", secousse={"base": 3, "coups": [{"t": 0.3, "force": 25, "tenue": 0.6}]},
                          effets=[{**FLOTTE_LOIN, "n": 1800, "derive": [-5, 0]}], son_h3=-3),
    "t06-tourelle": plan("t06-tourelle", cadre=[[0, 0.5, 0.6, 1.15]], cadre_v=[[0, 0.62, 0.6, 1.0]], secousse={"base": 3, "coups": [{"t": 0.1, "force": 14}, {"t": 0.55, "force": 14}]},
                         effets=[{**TIRS_O, "source": [0.4, 0.4, 0.6, 0.6], "cible": [0.9, 0, 1.2, 0.2], "par_s": 50}], son_h3=-3),
    "t07-essaim": plan("t07-essaim", suivi=True, secousse={"base": 6},
                       effets=[{**TIRS_O, "par_s": 90, "source": [0, 0.6, 1, 1], "cible": [0, 0, 1, 0.45]}, TIRS_B, {**LOIN_BOUM, "par_s": 5},
                               {"type": "flotte", "n": 1500, "zone": [0, 0, 1, 0.5], "profondeur": [1, 6], "taille": [1.5, 4], "derive": [30, 40],
                                "agitation": 20, "moteurs": "rouge", "cap": 0.9, "dispersion_cap": 0.3}], son_h3=-4),
}

# ------------------------------------------------------------------------------------------------ séquence (fin = instant de coupe, s)
S, SONS = [], []


def seg(fin, sec, **kw):
    S.append({"fin": round(fin, 3), "section": sec, **kw})


def son(t, kind, duree=1.0, db=-6, **kw):
    SONS.append({"t": round(t, 3), "type": kind, "duree": duree, "db": db, **kw})


# I. Ouverture (énergie 1) : une image, presque le silence, puis la promesse tapée dans le studio
seg(3.2, "ouverture", plan="p01-orbite-nuit", modif={"debut": 0.4, "fondu_noir_entree": 14})
son(0.0, "drone", 6.8, -19)
seg(f(5.26), "ouverture", type="saisie", part_frappe=0.62, clic=0.84)
for k in range(40):  # frappe des touches pendant la saisie (3,25 → 5,25 s)
    son(3.25 + k * 0.049 + 0.01 * ((k * 7) % 3), "frappe", 0.05, -22, graine=k)
son(f(5.26) - 0.66, "clic", 0.08, -12)
son(f(5.26), "impact", 2.5, -4)
son(f(5.26), "chute", 2.0, -10)
# II. Montée (énergie 3 → 5) : la menace, la flotte qui s'allume, les pilotes (plans de 1,5 à 2,8 s)
seg(f(7.54), "montee", plan="p03-vague-ennemie", modif={"debut": 2.4})
seg(f(10.38), "montee", plan="p02-mur-flotte", modif={"debut": 1.1})
son(f(7.54), "boom", 2.5, -10)
son(f(10.38) - 0.45, "fouet", 0.6, -14)
seg(f(12.59), "montee", plan="p05-hangar", modif={"debut": 1.0})
son(f(10.38), "souffle", 1.6, -14)
seg(f(14.62), "montee", plan="p07-pilote", modif={"debut": 0.25})
seg(f(14.62) + 0.92, "montee", plan="p06-cockpit", modif={"debut": 3.15})
son(f(14.62) + 0.92, "explosion", 1.0, -14)
seg(f(16.75), "montee", type="titre", texte="carton_1")
son(f(16.75), "montee", 3.2, -12, ancre=1.0)
son(f(16.75), "inverse", 1.1, -12, ancre=1.0)
# III. DROP (énergie 8) : la bordée, puis l'action sur les temps forts (plans de 1 à 2 s)
seg(f(18.09), "action", plan="p04-bordee", modif={"debut": 0.0, "vitesse": [[0, 0.5], [0.45, 0.5], [0.8, 1.15]]})
son(f(16.75), "impact", 3.0, 0)
son(f(16.75), "canons", 1.3, -9)
seg(f(19.97), "action", plan="t01-passage", modif={"debut": 1.0})
son(f(19.97) - 0.3, "fouet", 0.55, -11)
seg(f(21.4), "action", plan="t06-tourelle", modif={"debut": 2.85, "fouet": {"entree": 4, "sens": 1}})
son(f(21.4) - 0.9, "canons", 0.9, -10)
seg(f(23.07), "action", plan="t07-essaim", modif={"debut": 0.8})
son(f(23.07), "impact", 2.0, -6)
seg(f(24.36), "action", plan="p06-cockpit", modif={"debut": 2.2}, suffixe="-b")
seg(f(25.38), "action", plan="t04-explosion", modif={"debut": 0.9})
son(f(24.36), "explosion", 1.8, -6)
# moment produit : la carte « Rendu en cours » devient le plan des torpilles
seg(f(27.3), "action", type="rendu", source="t03-torpilles")
son(f(25.38) + 0.1, "clic", 0.08, -14)
seg(f(30.09), "action", plan="t03-torpilles", modif={"debut": 0.9})
son(f(27.3) - 0.35, "fouet", 0.6, -13)
son(f(30.09), "impact", 2.0, -6)
seg(f(32.05), "action", plan="p03-vague-ennemie", modif={"debut": 3.0, "miroir": True}, suffixe="-b")
seg(f(33.6), "action", plan="p02-mur-flotte", modif={"debut": 3.1, "vitesse": 1.25}, suffixe="-b")
seg(f(35.16), "action", plan="t01-passage", modif={"debut": 3.2, "miroir": True}, suffixe="-b")
son(f(35.16) - 0.3, "fouet", 0.55, -11)
seg(f(36.70), "action", plan="p04-bordee", modif={"debut": 2.3, "miroir": True}, suffixe="-b")
son(f(36.70), "impact", 2.2, -4)
seg(f(37.92), "action", plan="p05-hangar", modif={"debut": 1.9}, suffixe="-b")
seg(f(38.94), "action", plan="t07-essaim", modif={"debut": 3.0, "miroir": True}, suffixe="-b")
for t in (f(19.97), f(21.4), f(24.36), f(25.38), f(32.05), f(33.6), f(35.16), f(37.92), f(38.94)):
    son(t, "impact", 1.0, -10, graine=int(t * 10))
seg(f(41.0), "action", type="galerie", sources=["p04-bordee", "t03-torpilles", "p02-mur-flotte", "t04-explosion", "p03-vague-ennemie", "t01-passage"])
son(f(38.94), "fouet", 0.5, -14)
# IV. Respiration (énergie 5 → 9) : carton 2 sur les pulsations, montée vers le climax
seg(f(43.55), "montee2", type="titre", texte="carton_2")
son(f(43.55), "montee", 3.0, -9, ancre=1.0)
son(f(43.55), "inverse", 1.2, -10, ancre=1.0)
# V. CLIMAX (énergie 10) : un coup toutes les ≈ 0,43 s, impacts et flashs
CLIMAX = [
    (44.41, "t03-torpilles", {"debut": 2.2}),
    (44.83, "p08-vaisseau-mere", {"debut": 0.6}),
    (45.27, "t04-explosion", {"debut": 1.2, "miroir": True}),
    (45.69, "p07-pilote", {"debut": 1.45}),
    (46.54, "p09-rupture", {"debut": 0.8}),
    (46.98, "t01-passage", {"debut": 2.0}),
    (47.40, "p04-bordee", {"debut": 1.2}),
    (47.84, "p03-vague-ennemie", {"debut": 4.2}),
    (48.69, "p08-vaisseau-mere", {"debut": 2.2, "vitesse": [[0, 0.6], [0.4, 1.3]]}),
    (49.55, "p09-rupture", {"debut": 2.6}),
    (50.41, "p06-cockpit", {"debut": 3.6}),
]
debut_climax = f(43.55)
for k, (fin, nom, modif) in enumerate(CLIMAX):
    seg(f(fin), "climax", plan=nom, modif={**modif, "impact": k % 2 == 0}, suffixe=f"-c{k}")
    if k:  # un coup sourd sur chaque coupe du climax, en plus des coups de la musique
        son(debut_climax, "impact", 1.2, -8 if k % 2 else -6, graine=100 + k)
    debut_climax = f(fin)
son(f(43.55), "impact", 3.0, -1)
son(f(44.41), "explosion", 1.5, -10)
son(f(46.54), "explosion", 1.5, -9)
son(f(48.69), "boom", 2.5, -6)
seg(f(51.25), "climax", plan="t05-onde-choc", modif={"debut": 0.5, "vitesse": 0.8}, suffixe="-fin")
son(f(50.41), "souffle", 1.4, -8)
# VI. Silence (énergie 0) : la lumière revient ; puis le coup final (énergie 9) et le carton
seg(f(51.25) + 1.5, "silence", plan="p10-aube", modif={"debut": 1.2})
FIN = f(51.25) + 1.5
son(FIN, "impact", 4.0, 0)
son(FIN, "boom", 4.0, -4)
seg(FIN + 6.5, "fin", type="fin")

MUSIQUE = {"db": 0, "blocs": [{"fichier": MUS, "de": 1.95, "a": 51.25, "t": f(1.95), "fondu_in": 0.5, "fondu_out": 0.04}]}

# ------------------------------------------------------------------------------------------------ versions courtes (30 s, 15 s)
def version_courte(plan_coupes, blocs, sons, silence, fin):
    seq = []
    for c in plan_coupes:
        fin_c, quoi = c[0], c[1]
        d = {"fin": round(fin_c, 3), "section": c[3] if len(c) > 3 else "action"}
        if quoi in PLANS:
            d.update(plan=quoi, modif=c[2], suffixe=c[2].pop("_suffixe", ""))
        else:
            d.update(type=quoi, **c[2])
        seq.append(d)
    seq.append({"fin": fin, "section": "fin", "type": "fin"})
    return {"sequence": seq, "musique": {"db": 0, "blocs": [{"fichier": MUS, **b} for b in blocs]}, "sons": sons, "silences": [silence]}


def climax_vers(o, suffixe):
    """Les coupes du climax (mêmes plans que le film long) décalées : t = source + o."""
    out = []
    for k, (fin, nom, modif) in enumerate(CLIMAX):
        out.append((fin + o, nom, {**modif, "impact": k % 2 == 0, "_suffixe": f"-c{k}"}, "climax"))
    out.append((51.25 + o, "t05-onde-choc", {"debut": 0.5, "vitesse": 0.8, "_suffixe": "-fin"}, "climax"))
    return out


def coups_climax(o):
    sons, prec = [], 43.55 + o
    for k, (fin, _n, _m) in enumerate(CLIMAX):
        if k:
            sons.append({"t": round(prec, 3), "type": "impact", "duree": 1.2, "db": -8 if k % 2 else -6, "graine": 100 + k})
        prec = fin + o
    return sons + [{"t": round(43.55 + o, 3), "type": "impact", "duree": 3.0, "db": -1}, {"t": round(48.69 + o, 3), "type": "boom", "duree": 2.5, "db": -6}]


# 30 s : saisie → DROP (16,75) → action jusqu'à 25,38 → raccord sur 36,70 → galerie, carton 2 → climax → silence → carton
o1, o2 = 2.2 - 16.75, 10.83 - 36.70
SAISIE30 = [{"t": round(0.25 + k * 0.035, 3), "type": "frappe", "duree": 0.05, "db": -22, "graine": k} for k in range(36)]
V30 = version_courte(
    [(2.2, "saisie", {"part_frappe": 0.62, "clic": 0.86}, "ouverture"),
     (18.09 + o1, "p04-bordee", {"debut": 0.0, "vitesse": [[0, 0.5], [0.45, 0.5], [0.8, 1.15]]}),
     (19.97 + o1, "t01-passage", {"debut": 1.0}),
     (21.4 + o1, "p03-vague-ennemie", {"debut": 3.0, "_suffixe": "-b"}),
     (23.07 + o1, "p02-mur-flotte", {"debut": 1.6, "_suffixe": "-30"}),
     (24.36 + o1, "p06-cockpit", {"debut": 2.2, "_suffixe": "-b"}),
     (25.38 + o1, "t04-explosion", {"debut": 0.9}),
     (37.92 + o2, "t03-torpilles", {"debut": 0.9, "_suffixe": "-30"}),
     (38.94 + o2, "p07-pilote", {"debut": 0.25, "_suffixe": "-30"}),
     (41.0 + o2, "galerie", {"sources": ["p04-bordee", "t03-torpilles", "p02-mur-flotte", "t04-explosion", "p03-vague-ennemie", "t01-passage"]}),
     (43.55 + o2, "titre", {"texte": "carton_2"}, "montee2")] + climax_vers(o2, "-c")
    + [(51.25 + o2 + 1.0, "p10-aube", {"debut": 1.2, "_suffixe": "-30"}, "silence")],
    [{"de": 16.75, "a": 25.38, "t": 2.2, "fondu_in": 0.005, "fondu_out": 0.02}, {"de": 36.70, "a": 51.25, "t": 10.83, "fondu_in": 0.005, "fondu_out": 0.04}],
    SAISIE30 + [{"t": 0.0, "type": "drone", "duree": 2.4, "db": -19}, {"t": 1.88, "type": "clic", "duree": 0.08, "db": -12},
                {"t": 2.2, "type": "impact", "duree": 3.0, "db": 0}, {"t": 2.2, "type": "canons", "duree": 1.3, "db": -9},
                {"t": 10.83, "type": "impact", "duree": 2.0, "db": -4}, {"t": 43.55 + o2, "type": "montee", "duree": 3.0, "db": -9, "ancre": 1.0},
                {"t": 51.25 + o2 + 1.0, "type": "impact", "duree": 4.0, "db": 0}, {"t": 51.25 + o2 + 1.0, "type": "boom", "duree": 4.0, "db": -4}]
    + [{"t": round(t, 3), "type": "impact", "duree": 1.0, "db": -10} for t in (19.97 + o1, 21.4 + o1, 24.36 + o1, 37.92 + o2, 38.94 + o2)]
    + coups_climax(o2),
    [round(51.25 + o2 + 0.02, 3), round(51.25 + o2 + 0.98, 3)], round(51.25 + o2 + 1.0 + 3.6, 3))

# 15 s : saisie → DROP → raccord direct sur le climax → silence → carton
p1, p2 = 1.6 - 16.75, (18.09 - 16.75 + 1.6) - 43.55
SAISIE15 = [{"t": round(0.15 + k * 0.027, 3), "type": "frappe", "duree": 0.05, "db": -22, "graine": k} for k in range(30)]
V15 = version_courte(
    [(1.6, "saisie", {"part_frappe": 0.55, "clic": 0.82}, "ouverture"),
     (18.09 + p1, "p04-bordee", {"debut": 0.0, "vitesse": [[0, 0.6], [0.5, 1.2]]})] + climax_vers(p2, "-c")
    + [(51.25 + p2 + 0.7, "p10-aube", {"debut": 1.2, "_suffixe": "-15"}, "silence")],
    [{"de": 16.75, "a": 18.09, "t": 1.6, "fondu_in": 0.005, "fondu_out": 0.01}, {"de": 43.55, "a": 51.25, "t": 18.09 + p1, "fondu_in": 0.005, "fondu_out": 0.04}],
    SAISIE15 + [{"t": 1.32, "type": "clic", "duree": 0.08, "db": -12}, {"t": 1.6, "type": "impact", "duree": 2.5, "db": 0},
                {"t": 51.25 + p2 + 0.7, "type": "impact", "duree": 4.0, "db": 0}, {"t": 51.25 + p2 + 0.7, "type": "boom", "duree": 4.0, "db": -4}]
    + coups_climax(p2),
    [round(51.25 + p2 + 0.02, 3), round(51.25 + p2 + 0.68, 3)], 15.0)

print(json.dumps({
    "_schema": "plans : spec couches.py (plaque, debut, vitesse, cadre[[t,cx,cy,zoom]], cadre_v, secousse{base,derive,coups}, effets[], "
               "fouet, impact, miroir, son_h3 dB) ; sequence : segments {fin, section, plan|type, modif, suffixe, …} ; sons : sfx_v3 datés",
    "pellicule": {"cache_239": True},
    "musique": MUSIQUE, "h3_db": 0, "plans": PLANS, "sequence": S, "sons": SONS,
    "silences": {"long": [[f(51.25) + 0.02, FIN - 0.02]]},
    "versions": {"30": V30, "15": V15},
}, ensure_ascii=False, indent=1))
