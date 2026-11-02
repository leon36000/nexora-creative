"""Liste de montage de la promo V4 « Une phrase. Un film. » (écrit montage-v4.json pour monter_v4.py).

Récit (58 s) : une phrase est tapée dans le VRAI Producteur → il répond avec le plan, la musique, les cartons et le devis →
on valide → il tourne (captures réelles du suivi) → deux prises, on garde la meilleure → le montage s'assemble → DROP :
le film produit par cette phrase, plein cadre → « et tout ce que tu imagines » : six genres, chacun avec sa phrase →
arrêt net → « Une phrase. Un film. » et carton neutre (marque.json).
Captures : ~/nexora-creative-data/promo/v4/ui/fr (capturer.mjs, 3200×1800). Coordonnées des cadres : fractions de l'image.
Usage : python3 montage_v4.py > montage-v4.json
"""
import json
from pathlib import Path

V4 = Path.home() / "nexora-creative-data/promo/v4"
UI = V4 / "ui/fr"
CLES = "~/nexora-creative-data/promo/v4/cles/"
PLANS = "~/nexora-creative-data/promo/v4/plans/"
HERO = "~/nexora-creative-data/promo/v4/hero/"  # plan4-v (version verticale du studio) écarté : flacon flou, on recadre plan4-c


def ui(prefixe):
    return sorted(str(f) for f in UI.glob(f"*-{prefixe}.jpg"))


def etaler(fichiers, debut, fin):
    """Feuilletage : les captures réparties régulièrement entre debut et fin (s, relatif au segment)."""
    n = max(1, len(fichiers) - 1)
    return [[round(debut + (fin - debut) * k / n, 3), f] for k, f in enumerate(fichiers)]


# ---------------------------------------------------------------------------------------------- choix (mis à jour à la revue)
# Musique Music3 graine 42 : 100 BPM (un temps = 0,6 s, une mesure = 2,4 s), intro calme, creux à 16,5 s, DROP à 17,0 s
# (source), puis plein régime jusqu'à 64 s. Posée à +7,55 s : son DROP tombe sur DROP. Coupes du film sur la grille des temps.
MUS = "~/nexora-creative-data/promo/v4/audio/v4-musique-42.flac"
DROP = 24.55     # le film du parfum apparaît (= 17,0 s de la musique)
STOP = DROP + 28.8   # arrêt net après 12 mesures (un temps de silence)
MUSIQUE = [
    {"fichier": MUS, "source": 0.0, "pose": DROP - 17.0, "d": STOP - (DROP - 17.0), "fondu_entree": 1.5, "fondu_fin": 0.03},
    {"fichier": MUS, "source": 0.0, "pose": STOP + 0.6, "d": 5.5, "db": -3, "fondu_entree": 0.2, "fondu_fin": 2.0},  # reprise douce sous le carton
]
GENRES = [  # (nom, image clé, plaque, début source, vitesse)
    ("g1-ville", "g1-ville-12", "g1-ville-p1", 0.3, 1.0),
    ("g2-chevaux", "g2-chevaux-11", "g2-chevaux-p1", 0.3, 1.0),
    ("g3-chocolat", "g3-chocolat-12", "g3-chocolat-p2", 2.0, 1.0),
    ("g4-robe", "g4-robe-12", "g4-robe-p1", 2.2, 1.0),
    ("g5-vague", "g5-vague-12", "g5-vague-p1", 0.5, 1.0),
    ("g6-papier", "g6-papier-12", "g6-papier-p1", 1.0, 1.0),
]
HEROS = [  # plans du film tourné par le Producteur (prise gardée), début source, vitesse
    ("h1", "h1-goutte-21", "plan1-a", 0.4, 1.0),
    ("h2", "h2-chute-21", "plan2-a", 0.9, 1.0),
    ("h3", "h3-impact-21", "plan3-b", 1.0, [[0, 1.0], [0.6, 0.5], [3.6, 0.5]]),  # prise B (Refaire ce plan), gardée
    ("h4", "h4-flacon-21", "plan4-c", 1.3, 1.0),  # plan refait avec la description retouchée (flacon taillé)
]
AB = {"plan": "plan3", "cle": "h3-impact-21", "garde": "b"}  # plan3-a : prise du premier tournage ; plan3-b : « Refaire ce plan »
TOURNAGE = [str(UI / f"{n:04d}-tournage.jpg") for n in (73, 79, 85, 91, 97, 98)]  # suivi réel : 0 → 4 plans tournés → PRÊT


def segments():
    s, textes, sfx = [], [], []
    t = 0.0

    def ajouter(seg):
        nonlocal t
        s.append(seg)
        t0 = t
        t += seg["d"]
        return t0

    # 1. la phrase est tapée (zoom sur le champ du Producteur)
    vide, saisie, fin = ui("vide"), ui("saisie"), ui("saisie-fin")
    t1 = ajouter({"type": "ui", "nom": "saisie", "d": 6.0, "fondu_entree": 0.5,
                  "images": etaler(vide, 0, 0.7) + etaler(saisie, 0.8, 5.4) + [[5.6, fin[0]]],
                  "cadre": [[0, 0.20, 0.875, 0.25], [6.0, 0.20, 0.87, 0.29]], "cadre_v": [[0, 0.198, 0.62, 0.27], [6.0, 0.198, 0.66, 0.245]]})
    for k in range(len(saisie)):
        sfx.append({"type": "frappe", "t": t1 + 0.8 + 4.6 * k / len(saisie), "duree": 0.08, "db": -16})
    textes.append({"t": t1 + 1.0, "d": 5.0, "cle": "phrase_hero", "style": "phrase", "frappe": 4.3, "langues": ["en"], "pos_v": 0.18})
    # 2. envoi : le Producteur réfléchit (vrai délai ≈ 13 s, ramené à 2 s)
    t2 = ajouter({"type": "ui", "nom": "envoi", "d": 2.35, "clic": 0.0,
                  "images": [[0, fin[0]]] + etaler(ui("reflexion"), 0.15, 2.2),
                  "cadre": [[0, 0.20, 0.87, 0.29], [2.0, 0.20, 0.55, 0.33]], "cadre_v": [[0, 0.198, 0.66, 0.245], [2.35, 0.198, 0.6, 0.27]]})
    sfx.append({"type": "clic", "t": t2, "duree": 0.2, "db": -10})
    # 3. sa réponse, puis le plan (cartes), puis le devis et « Valider et lancer »
    plan = ui("plan")
    t3 = ajouter({"type": "ui", "nom": "reponse", "d": 3.0, "images": [[0, plan[0]]],
                  "cadre": [[0, 0.19, 0.55, 0.33], [3.0, 0.19, 0.68, 0.33]], "cadre_v": [[0, 0.186, 0.6, 0.245], [3.0, 0.186, 0.66, 0.245]]})
    textes.append({"t": t3 + 0.4, "d": 2.5, "cle": "plan", "pos": "haut"})
    t4 = ajouter({"type": "ui", "nom": "cartes", "d": 3.0, "images": [[0, plan[-1]], [2.2, ui("format")[0]]],
                  "cadre": [[0, 0.50, 0.50, 0.45], [3.0, 0.76, 0.55, 0.45]], "cadre_v": [[0, 0.58, 0.53, 0.19], [1.0, 0.58, 0.53, 0.19], [1.6, 0.723, 0.53, 0.19], [2.2, 0.723, 0.53, 0.19], [2.8, 0.866, 0.55, 0.19]]})
    sfx.append({"type": "fouet", "t": t4 - 0.15, "duree": 0.5, "db": -18})
    t5 = ajouter({"type": "ui", "nom": "devis", "d": 2.4, "clic": 2.0,
                  "images": [[0, ui("format")[0]], [0.5, ui("cinema")[0]], [1.4, ui("valider-survol")[0]]],
                  "cadre": [[0, 0.62, 0.84, 0.46], [2.4, 0.75, 0.9, 0.34]], "cadre_v": [[0, 0.55, 0.85, 0.22], [2.4, 0.79, 0.9, 0.2]]})
    textes.append({"t": t5 + 0.2, "d": 2.1, "cle": "devis", "pos": "haut"})
    sfx.append({"type": "clic", "t": t5 + 2.0, "duree": 0.2, "db": -8})
    # 4. le tournage (captures réelles du suivi)
    images = etaler(TOURNAGE, 0, 1.5) if TOURNAGE else [[0, ui("valider-survol")[0]]]
    t6 = ajouter({"type": "ui", "nom": "tournage", "d": 1.8, "images": images,
                  "cadre": [[0, 0.72, 0.53, 0.48], [1.8, 0.745, 0.54, 0.44]], "cadre_v": [[0, 0.81, 0.5, 0.26], [1.8, 0.81, 0.52, 0.25]]})
    textes.append({"t": t6 + 0.2, "d": 1.6, "cle": "tournage", "pos": "haut"})
    # 5. deux prises, on garde la meilleure
    t7 = ajouter({"type": "ab", "nom": "ab", "d": 3.0, "t_choix": 1.8, "debut": 1.0, "garde": AB["garde"],
                  "a": HERO + AB["plan"] + "-a.mp4", "b": HERO + AB["plan"] + "-b.mp4", "cle_a": CLES + AB["cle"] + ".png",
                  "cle_b": CLES + AB["cle"] + ".png"})
    textes.append({"t": t7 + 0.2, "d": 1.5, "cle": "prises", "pos": "haut"})
    sfx.append({"type": "fouet", "t": t7 + 1.8, "duree": 0.5, "db": -16})
    # 6. le montage s'assemble sur la musique
    t8 = ajouter({"type": "chrono", "nom": "chrono", "d": round(DROP - t - 0.6, 3), "temps": [0.0, 0.6, 1.2, 1.8],
                  "plans": [{"plaque": HERO + p + ".mp4", "cle": CLES + c + ".png", "debut": 1.5} for _, c, p, _, _ in HEROS]})
    textes.append({"t": t8 + 0.1, "d": DROP - 0.7 - t8, "cle": "montage", "pos": "haut"})
    for k in range(4):
        sfx.append({"type": "clic", "t": t8 + 0.6 * k, "duree": 0.15, "db": -14})
    sfx.append({"type": "montee", "t": t8, "duree": DROP - t8, "db": -14})
    ajouter({"type": "noir", "nom": "souffle", "d": 0.6})
    # 7. DROP : le film tourné par cette phrase
    sfx.append({"type": "impact", "t": DROP, "duree": 2.5, "db": -6})
    for k, (h, cle, p, debut, vit) in enumerate(HEROS):
        dh = [2.4, 2.4, 3.6, 3.6][k]
        th = ajouter({"type": "plan", "nom": h, "d": dh, "plaque": HERO + p + ".mp4",
                      "cle": CLES + cle + ".png", "plaque_v": HERO + p.split("-")[0] + "-v.mp4" if not p.startswith("plan4") else None, "debut": debut, "vitesse": vit, "son_h3": -16,
                      "cadre": [[0, 0.5, 0.5, 1.0], [dh, 0.5, 0.5, 0.92]], "cadre_v": [[0, 0.5, 0.5, 1.0], [dh, 0.5, 0.5, 0.95]]})
        if k == 0:
            textes.append({"t": th + 0.3, "d": 2.2, "cle": "phrase_hero", "style": "phrase", "frappe": 0.8})
    textes.append({"t": t - 1.8, "d": 1.8, "cle": "carton_film", "style": "grand"})
    # 8. et tout ce que tu imagines : six genres, chacun sa phrase
    ti = ajouter({"type": "noir", "nom": "imagine", "d": 2.4})
    textes.append({"t": ti + 0.05, "d": 2.3, "cle": "imagine", "style": "grand"})
    sfx.append({"type": "fouet", "t": ti + 2.2, "duree": 0.5, "db": -12})
    dg = (STOP - t) / len(GENRES)
    for nom, cle, p, debut, vit in GENRES:
        tg = ajouter({"type": "plan", "nom": nom, "d": round(dg, 3), "plaque": PLANS + p + ".mp4", "cle": CLES + cle + ".png", "plaque_v": PLANS + nom + "-v.mp4",
                      "cadre_vv": [[0, 0.5, 0.5, 1.0], [dg, 0.5, 0.5, 0.93]],
                      "debut": debut, "vitesse": vit, "son_h3": -18, "cadre": [[0, 0.5, 0.5, 1.0], [dg, 0.5, 0.5, 0.93]]})
        textes.append({"t": tg + 0.1, "d": dg - 0.15, "cle": "phrase_" + nom, "style": "phrase", "frappe": 0.45})
    # 9. arrêt net, puis la promesse et le carton
    ajouter({"type": "noir", "nom": "silence", "d": 0.6})
    tf = ajouter({"type": "fin", "nom": "fin", "d": 5.5})
    sfx.append({"type": "boom", "t": tf, "duree": 4.0, "db": -4})
    return s, textes, sfx, t


def courte(version):
    """Coupes 30 s et 15 s : même récit resserré (saisie, plan, devis pour 30 s), DROP plus tôt, genres à 2 temps."""
    s, textes, sfx = [], [], []
    t = 0.0

    def ajouter(seg):
        nonlocal t
        s.append(seg)
        t0 = t
        t += seg["d"]
        return t0

    trente = version == "30"
    vide, saisie, fin = ui("vide"), ui("saisie"), ui("saisie-fin")
    ds = 4.2 if trente else 2.4
    t1 = ajouter({"type": "ui", "nom": f"saisie-{version}", "d": ds, "fondu_entree": 0.3,
                  "images": etaler(vide, 0, 0.2) + etaler(saisie, 0.3, ds - 0.4) + [[ds - 0.25, fin[0]]],
                  "cadre": [[0, 0.20, 0.875, 0.25], [ds, 0.20, 0.87, 0.29]], "cadre_v": [[0, 0.198, 0.62, 0.27], [ds, 0.198, 0.66, 0.245]]})
    for k in range(0, len(saisie), 2):
        sfx.append({"type": "frappe", "t": t1 + 0.3 + (ds - 0.7) * k / len(saisie), "duree": 0.08, "db": -16})
    textes.append({"t": t1 + 0.3, "d": ds - 0.3, "cle": "phrase_hero", "style": "phrase", "frappe": ds - 0.8, "langues": ["en"], "pos_v": 0.18})
    if trente:
        t2 = ajouter({"type": "ui", "nom": "envoi-30", "d": 1.2, "clic": 0.0, "images": [[0, fin[0]]] + etaler(ui("reflexion"), 0.1, 1.1),
                      "cadre": [[0, 0.20, 0.87, 0.29], [1.2, 0.20, 0.55, 0.33]], "cadre_v": [[0, 0.198, 0.66, 0.245], [1.2, 0.198, 0.6, 0.27]]})
        sfx.append({"type": "clic", "t": t2, "duree": 0.2, "db": -10})
        plan = ui("plan")
        t4 = ajouter({"type": "ui", "nom": "cartes-30", "d": 2.4, "images": [[0, plan[-1]]],
                      "cadre": [[0, 0.50, 0.50, 0.45], [2.4, 0.74, 0.55, 0.45]], "cadre_v": [[0, 0.58, 0.53, 0.19], [1.2, 0.58, 0.53, 0.19], [2.0, 0.723, 0.53, 0.19]]})
        textes.append({"t": t4 + 0.2, "d": 2.1, "cle": "plan", "pos": "haut"})
        t5 = ajouter({"type": "ui", "nom": "devis-30", "d": 1.8, "clic": 1.5,
                      "images": [[0, ui("cinema")[0]], [0.9, ui("valider-survol")[0]]],
                      "cadre": [[0, 0.62, 0.84, 0.46], [1.8, 0.75, 0.9, 0.34]], "cadre_v": [[0, 0.55, 0.85, 0.22], [1.8, 0.79, 0.9, 0.2]]})
        textes.append({"t": t5 + 0.1, "d": 1.6, "cle": "devis", "pos": "haut"})
        sfx.append({"type": "clic", "t": t5 + 1.5, "duree": 0.2, "db": -8})
    td = ajouter({"type": "noir", "nom": "souffle", "d": 0.6})
    sfx.append({"type": "montee", "t": max(0.0, td - 2.0), "duree": 2.0, "db": -16})
    drop = t
    sfx.append({"type": "impact", "t": drop, "duree": 2.5, "db": -6})
    heros = [HEROS[0], HEROS[2]]
    for k, (h, cle, p, debut, vit) in enumerate(heros):
        dh = 2.4 if (k == 0 or not trente) else 3.6
        th = ajouter({"type": "plan", "nom": f"{h}-{version}", "d": dh, "plaque": HERO + p + ".mp4",
                      "cle": CLES + cle + ".png", "plaque_v": HERO + p.split("-")[0] + "-v.mp4" if not p.startswith("plan4") else None, "debut": debut, "vitesse": vit, "son_h3": -16,
                      "cadre": [[0, 0.5, 0.5, 1.0], [dh, 0.5, 0.5, 0.92]], "cadre_v": [[0, 0.5, 0.5, 1.0], [dh, 0.5, 0.5, 0.95]]})
        if k == 0 and trente:
            textes.append({"t": th + 0.2, "d": 2.1, "cle": "phrase_hero", "style": "phrase", "frappe": 0.7})
    genres = GENRES if trente else [GENRES[i] for i in (0, 2, 3, 5)]
    for nom, cle, p, debut, vit in genres:
        tg = ajouter({"type": "plan", "nom": nom + "-c", "d": 1.2, "plaque": PLANS + p + ".mp4", "cle": CLES + cle + ".png", "plaque_v": PLANS + nom + "-v.mp4",
                      "debut": debut, "vitesse": vit, "son_h3": -18, "cadre": [[0, 0.5, 0.5, 1.0], [1.2, 0.5, 0.5, 0.95]]})
        textes.append({"t": tg + 0.05, "d": 1.1, "cle": "phrase_" + nom, "style": "phrase", "frappe": 0.3})
    stop = t
    ajouter({"type": "noir", "nom": "silence", "d": 0.6})
    tf = ajouter({"type": "fin", "nom": f"fin-{version}", "d": 4.2 if trente else 2.4})
    sfx.append({"type": "boom", "t": tf, "duree": 3.5, "db": -4})
    pose = drop - 17.0
    musique = [{"fichier": MUS, "source": max(0.0, -pose), "pose": max(0.0, pose), "d": stop - max(0.0, pose), "fondu_entree": 0.8, "fondu_fin": 0.03},
               {"fichier": MUS, "source": 0.0, "pose": stop + 0.6, "d": t - stop - 0.6, "db": -3, "fondu_entree": 0.2, "fondu_fin": 1.2}]
    return {"segments": s, "textes": textes, "sfx": sfx, "musique": musique, "silence": [stop, stop + 0.6]}


if __name__ == "__main__":
    s, textes, sfx, total = segments()
    print(json.dumps({"_duree": round(total, 2), "versions": {"long": {"segments": s, "textes": textes, "sfx": sfx, "musique": MUSIQUE,
                                                                       "silence": [STOP, STOP + 0.6]},
                                                         "30": courte("30"), "15": courte("15")}},
                     ensure_ascii=False, indent=1))
