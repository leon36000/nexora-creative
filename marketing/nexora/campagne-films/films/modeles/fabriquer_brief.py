"""Écrit brief.json du film « Modèles et API » : parcours réel de la page /modeles (ui/sections.json, voir capturer.mjs et decouper.py).
Usage : python3 fabriquer_brief.py   (après capturer.mjs et decouper.py)"""
import json
import os
from pathlib import Path

G = 60 / 128 * 0.5            # grille : une croche à 128 BPM (mesuré sur mod-musique-72.flac)
g = lambda n: round(n * G, 4)  # noqa: E731
TRAVAIL = Path("~/nexora-creative-data/promo/v5/modeles").expanduser()
SEC = json.loads((TRAVAIL / "ui/sections.json").read_text())["fr"]
CARTE = [0.29, 0.08, 0.975, 0.92]     # carte 16:9 (rapport 1,45) ; le texte reste dans la marge de gauche
CARTE_V = [0.04, 0.28, 0.96, 0.88]    # carte 9:16 haute (rapport 0,86) sous la bande de texte ; cadrages étroits propres au vertical (cadre_v)


def mise_a_l_echelle(label, d, sub=None):
    """f = durée du segment / durée de l'étiquette (ou de la sous-plage d'images [i0, i1] à 30 images/s)."""
    dur = SEC[label]["d"] if not sub else (sub[1] - sub[0]) / 30
    return d / dur


def cam(f, ks):  # [[t de l'étiquette, cx, cy, largeur]] → temps du segment
    return [[round(t * f, 3), cx, cy, w] for t, cx, cy, w in ks]


def curseur(label, f):
    c = SEC[label]["curseur"]
    if not c:
        return {}
    t0 = round(c[0][0] * f, 3)
    liste = [[max(0.0, t0 - 0.01), 1.4, 1.4], *[[round(t * f, 3), x, y] for t, x, y in c]]  # hors cadre jusqu'au premier geste
    return {"curseur": liste, "clics": [round(t * f, 3) for t in SEC[label]["clics"]]}


def clics_sfx(label, f, db=-14):
    return [{"t": round(t * f, 3), "type": "clic", "duree": 0.15, "db": db} for t in SEC[label]["clics"]]


def frappes(t0, t1, f, pas=0.13):
    n = int((t1 - t0) / pas)
    return [{"t": round((t0 + k * pas) * f, 3), "type": "frappe", "duree": 0.08, "db": -24} for k in range(n)]


R = lambda lab, key: SEC[lab]["reperes"][key]  # noqa: E731


def ecran(label, d, ks, ks_v=None, textes=(), sfx=(), carte=CARTE, extra=None, sub=None):
    f = mise_a_l_echelle(label, d, sub)
    imgs = [[0, d, "{l}:" + label, *(sub or [])]]
    s = {"type": "ecran", "d": d, "carte": carte, "carte_v": CARTE_V, "images": imgs, "cadre": cam(f, ks), "cadre_v": cam(f, ks_v or ks),
         "textes": [{"t": t, "d": round(min(dd, d - t), 3), "cle": cle, "style": st} for t, dd, cle, st in
                    [(a, d - a if b is None else b, c, e) for a, b, c, e in textes]],
         "sfx": list(sfx)}
    if not sub:
        s.update(curseur(label, f))
    if extra:
        s.update(extra)
    return s, f


seg = {}
# --- s1 : la page d'accueil, la réponse en continu s'écrit (preuve), clic « Parcourir le catalogue » ---
hf, tc = SEC["hero"]["reperes"]["hero_fin"], SEC["hero"]["clics"][0]
KS_HERO = [[0, .71, .52, .48], [1.6, .72, .655, .40], [hf, .72, .655, .40], [tc - 0.5, .38, .62, .68], [5.3, .5, .55, .70]]
KV_HERO = [[0, .71, .55, .40], [1.6, .72, .58, .38], [hf, .72, .58, .38], [tc - 0.5, .30, .62, .46], [5.3, .33, .6, .47]]


def hero(d, textes):
    s, f = ecran("hero", d, KS_HERO, KV_HERO, textes=textes, extra={"preuve": True})
    s["sfx"] = [{"t": round(tc * f - 0.0, 3), "type": "clic", "duree": 0.2, "db": -14}] + \
               [{"t": round(x * f, 3), "type": "frappe", "duree": 0.08, "db": -26} for x in (1.2, 1.35, 1.5, 1.65, 1.8, 1.95)]
    return s


seg["s1"] = hero(g(22), [(0.0, None, "prepa", "prepa"), (0.2, None, "t_cle", "titre")])
# --- s2 : 36 modèles, un clic sur la pastille Code, 25 modèles ---
KS_CAT = [[0, .5, .5, .80], [R("cat", "c_go") - 0.5, .5, .5, .80], [R("cat", "c_go") + 0.3, .36, .63, .52], [4.4, .36, .63, .52]]
KV_CAT = [[0, .33, .62, .47], [4.4, .33, .66, .47]]
s, f = ecran("cat", g(18), KS_CAT, KV_CAT, textes=[(0.0, None, "reel", "sur"), (0.1, None, "t_filtre", "titre")])
s["sfx"] = [{"t": round(R("cat", "c_go") * f, 3), "type": "clic", "duree": 0.15, "db": -14},
            {"t": round(R("cat", "c_res") * f, 3), "type": "fouet", "duree": 0.3, "db": -26}]
seg["s2"] = (s, f)
# --- s3 : on tape « qwen », 5 modèles, tri par prix d'entrée ---
tf = R("rech", "tape_fin")
KS_RECH = [[0, .40, .72, .66], [tf + 0.4, .40, .72, .66], [4.5, .62, .72, .62], [5.6, .62, .72, .62], [6.7, .38, .80, .55]]
KV_RECH = [[0, .33, .66, .47], [tf + 0.4, .33, .66, .47], [4.0, .70, .66, .47], [5.6, .70, .66, .47], [6.7, .33, .82, .47]]
s, f = ecran("rech", g(26), KS_RECH, KV_RECH, textes=[(0.0, None, "reel", "sur"), (0.1, None, "t_cherche", "titre")])
s["sfx"] = frappes(R("rech", "tape"), tf, f) + clics_sfx("rech", f)
seg["s3"] = (s, f)
# --- s4 : la fiche du premier modèle, prix d'entrée et de sortie en dollars canadiens ---
KS_FICHE = [[0, .5, .52, .80], [0.9, .58, .74, .42], [2.9, .58, .74, .40]]
KV_FICHE = [[0, .33, .52, .47], [0.7, .33, .52, .47], [1.3, .56, .64, .47], [2.9, .56, .66, .46]]
s, f = ecran("fiche", g(14), KS_FICHE, KV_FICHE, textes=[(0.0, None, "reel", "sur"), (0.1, None, "t_prix", "titre")])
s["entree"] = True
s["sfx"] = [{"t": 0.0, "type": "impact", "duree": 1.8, "db": -23}]
seg["s4"] = (s, f)
# --- s5 : défilement vers les benchmarks publiés, avec leur source ---
KS_BENCH = [[0, .495, .50, .78], [1.3, .495, .50, .78], [2.7, .36, .50, .48]]
KV_BENCH = [[0, .335, .5, .47], [2.7, .335, .5, .47]]
s, f = ecran("bench", g(12), KS_BENCH, KV_BENCH, textes=[(0.0, None, "reel", "sur"), (0.1, None, "t_bench", "titre")])
s["sfx"] = [{"t": 0.0, "type": "fouet", "duree": 0.35, "db": -24}]
seg["s5"] = (s, f)
# --- s6 : l'exemple d'appel de la fiche (étiqueté Aperçu), clic « Copier » ---
cp = SEC["api"]["clics"][0]
KS_API = [[0, .40, .40, .64], [cp - 1.2, .40, .40, .64], [cp - 0.2, .41, .52, .60], [5.4, .41, .52, .60]]
KV_API = [[0, .335, .42, .47], [cp - 1.6, .335, .42, .47], [cp - 0.4, .50, .48, .47], [5.4, .50, .48, .47]]
d6 = g(22)
s, f = ecran("api", d6, KS_API, KV_API, textes=[(0.0, None, "prepa", "prepa"), (0.1, 1.75, "t_api", "titre"),
                                         (1.9, None, "t_api2", "titre")])
s["sfx"] = [{"t": 0.0, "type": "fouet", "duree": 0.35, "db": -24}] + clics_sfx("api", f, -12)
seg["s6"] = (s, f)
# --- s7 : retour sur l'exemple de l'accueil : une ligne à changer (« vous changez de modèle en changeant une ligne », dit la page) ---
SUB = [70, 124]
s, f = ecran("hero", g(16), [[0, .72, .655, .40], [1.8, .72, .655, .40]], [[0, .72, .58, .40], [1.8, .72, .60, .38]], textes=[(0.0, None, "prepa", "prepa"), (0.1, None, "t_ligne", "titre")], sub=SUB)
s["sfx"] = [{"t": 0.0, "type": "fouet", "duree": 0.35, "db": -24}, {"t": 0.9, "type": "montee", "duree": g(16) - 0.9, "db": -27}]
seg["s7"] = (s, f)
seg = {k: (v[0] if isinstance(v, tuple) else v) for k, v in seg.items()}
seg["silence"] = {"type": "noir", "d": g(2)}
seg["fin"] = {"type": "fin", "d": g(20), "t_marque": g(4), "sfx": [{"t": g(4), "type": "impact", "duree": 1.6, "db": -20}]}


def variante(base, d, **kw):
    """Même plan, durée différente : images, caméra, curseur et bruitages recalés (échelle d / durée d'origine)."""
    b = json.loads(json.dumps(seg[base]))
    r = d / b["d"]
    b["d"] = d
    b["images"] = [[0, d, *x[2:]] for x in b["images"]]
    for k in ("cadre", "cadre_v", "curseur"):
        if b.get(k):
            b[k] = [[round(x[0] * r, 3), *x[1:]] for x in b[k]]
    if b.get("clics"):
        b["clics"] = [round(x * r, 3) for x in b["clics"]]
    b["sfx"] = [{**x, "t": round(x["t"] * r, 3)} for x in b["sfx"] if x["t"] * r < d]
    for x in b["textes"]:
        x["d"] = round(min(x["d"] * r if x["t"] else d, d - x["t"] * r), 3)
        x["t"] = round(x["t"] * r, 3)
    b["textes"] = [x for x in b["textes"] if x["d"] > 0.2]
    b.update(kw)
    return b


def retexte(b, garder):
    """Ne garde que les textes demandés, étalés sur tout le segment (versions courtes : une seule ligne par plan)."""
    b["textes"] = [x for x in b["textes"] if x["cle"] in garder or x["style"] in ("prepa", "sur")]
    for x in b["textes"]:
        if x["cle"] in garder:
            x["t"], x["d"] = 0.1, round(b["d"] - 0.2, 3)
        else:
            x["t"], x["d"] = 0.0, b["d"]
    return b


seg["s1c"] = variante("s1", g(16))
seg["s2c"] = variante("s2", g(14))
seg["s3c"] = variante("s3", g(20))
seg["s4c"] = variante("s4", g(12))
seg["s5c"] = variante("s5", g(10))
seg["s6c"] = retexte(variante("s6", g(18)), {"t_api2"})
seg["s7c"] = variante("s7", g(14))
seg["s1k"] = variante("s1", g(10))
seg["s2k"] = variante("s2", g(12))
seg["s4k"] = variante("s4", g(12))
seg["s6k"] = retexte(variante("s6", g(14)), {"t_api2"})
seg["fin15"] = {"type": "fin", "d": g(14), "t_marque": g(3), "sfx": [{"t": g(3), "type": "impact", "duree": 1.6, "db": -20}]}

HIT, FINAL = 14.99, 36.47


def mus(rep, fin_id="fin", tm=g(4)):
    return {"repere_segment": rep, "arret_segment": "silence", "silence": "silence",
            "queue": {"segment": fin_id, "source": round(FINAL - tm, 3), "db": -5}}


V = {"long": {"cible": 45, "ordre": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "silence", "fin"], "musique": mus("s4")},
     "30": {"cible": 30, "ordre": ["s1c", "s2c", "s3c", "s4c", "s5c", "s6c", "s7c", "silence", "fin"], "musique": mus("s4c")},
     "15": {"cible": 15, "ordre": ["s1k", "s2k", "s4k", "s6k", "silence", {"id": "fin15"}], "musique": mus("s4k", "fin15", g(3))}}
V["15"]["ordre"] = ["s1k", "s2k", "s4k", "s6k", "silence", "fin15"]

TEXTES = {
    "fr": {"prepa": "Aperçu",
           "t_cle": "Une clé.|Tous les *modèles.*",
           "t_filtre": "36 modèles.|Un clic, *25.*",
           "t_cherche": "Cherchez,|triez par *prix.*",
           "t_prix": "Le prix, en|*dollars canadiens.*",
           "t_bench": "Mesures publiées,|*source* citée.",
           "t_api": "Exemple *prêt à copier.*",
           "t_api2": "L'API n'est pas *encore ouverte.*",
           "t_ligne": "Changer de modèle :|*une ligne.*",
           "slogan": "Une clé.|Tous les *modèles.*",
           "sous_titre": "Catalogue en aperçu.",
           "mentions": "Aperçu : le catalogue est en aperçu et l'appel par API n'est pas encore ouvert · captures de la page Modèles et API"},
    "en": {"prepa": "Preview",
           "t_cle": "One key.|Every *model.*",
           "t_filtre": "36 models.|One click, *25.*",
           "t_cherche": "Search,|sort by *price.*",
           "t_prix": "Price in|*Canadian dollars.*",
           "t_bench": "Published benchmarks,|*sources* cited.",
           "t_api": "Ready to *copy.*",
           "t_api2": "The API is *not open yet.*",
           "t_ligne": "Switch models:|change *one line.*",
           "slogan": "One key.|Every *model.*",
           "sous_titre": "Catalogue in preview.",
           "mentions": "Preview: the catalogue is in preview and API calls are not open yet · screen captures of the Models and API page"},
}

brief = {
    "_gabarit": "Généré par fabriquer_brief.py ; éditer le script, pas ce fichier.",
    "film": "modeles", "titre": "Modèles et API : une clé, tous les modèles du catalogue", "nom_fichier": "Modeles-et-API-film",
    "produit": "MODÈLES ET API", "date": "2026-11-02", "marque": "../../marque.json",
    "travail": "~/nexora-creative-data/promo/v5/modeles", "captures": "~/nexora-creative-data/promo/v5/modeles/ui",
    "concept": "Un seul parcours réel de la page Modèles et API du site, filmé tel quel : la page d'accueil et sa réponse en continu, "
               "le catalogue de 36 modèles, la pastille Code (25), la recherche, le tri par prix, la fiche d'un modèle (prix en dollars "
               "canadiens, mesures publiées avec leur source), l'exemple d'appel prêt à copier, étiqueté Aperçu : l'API n'est pas ouverte.",
    "public": "développeurs et responsables techniques de PME qui veulent un point d'accès unique à plusieurs modèles",
    "formats": ["16x9", "9x16"], "langues": ["fr", "en"], "affiche": {"t": 17.3, "langue": "fr"},
    "note_manifeste": "Aperçu : l'API n'est pas ouverte et le catalogue est en aperçu. Captures réelles du parcours de la page /modeles "
                      "(français) et /en/modeles (anglais) du site en ligne : filtres, recherche, tri, fiche et exemple d'appel de la page "
                      "elle-même ; clé, adresse et réponse sont figurées par la page. Aucun chiffre ajouté : 36, 25 et les prix sont ceux de la page.",
    "commandes": {"plaques": "", "captures": "node capturer.mjs ~/nexora-creative-data/promo/v5/modeles/brut && python3 decouper.py ~/nexora-creative-data/promo/v5/modeles"},
    "musique": {"fichier": "~/nexora-creative-data/promo/v5/modeles/audio/mod-musique-72.flac",
                "brief": "musique.py (graine 72), mesurée : 128,0 BPM (temps 0,46875 s), intro calme 0-14 s, coup fort à 14,99 s (mesure 16), "
                         "groove jusqu'à 29 s, respiration puis coup final à 36,47 s et queue jusqu'à 44 s.",
                "bpm": 128.0, "subdivision": 0.5, "repere_source": HIT},
    "segments": seg, "versions": V, "textes": TEXTES,
}
brief["revue"] = {
    "date": "2026-11-02", "livre": True,
    "grille_severe": {"concept": 7.5, "preuve_rapide": 8, "textes": 7.5, "rythme": 7, "son": 6.5, "finition": 7, "authenticite": 9},
    "note": 7.5,
    "mesures": "long 35,6 s, 30 s = 29,5 s, 15 s = 15,0 s ; preuve (page réelle, réponse en continu) à 0 s ; filtre Code 36 → 25 à ≈ 7 s, fiche "
               "ouverte à 15,5 s (long) / 10,3 s (30 s) ; −14,8 LUFS (long, 30 s) et −15,0 (15 s), crête vraie ≤ −2,0 dBTP après AAC ; "
               "musique mesurée à 127,7 BPM (grille 128) ; plan moyen 4,0 s (long)",
    "faiblesses": [
        "note limite (7,5) : le parcours est réel mais sans « effet » ; la page est claire et petite, les textes de la page sont peu lisibles hors des zooms (surtout en 9:16)",
        "le beat « une ligne » (s7) réutilise le plan de l'accueil : la page ne montre pas de vrai changement de modèle (l'API n'est pas ouverte), rien n'est simulé",
        "son jugé aux chiffres, personne n'a écouté ; loudnorm ajouté à l'usine (limiteur seul : crête +2 dB après AAC)",
        "l'adresse de développement ts.net apparaît dans le code de l'exemple d'appel quand le cadrage le montre (cadrages évités dans les zooms, pas partout) ; en-tête du site masqué (marque)",
        "capture 1× (1600×900) : zooms ≈ 1,3 à 1,6× un peu mous ; le curseur est dessiné aux positions réelles mais le survol n'est pas visible"],
}
Path(__file__).with_name("brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1))
print("brief.json écrit :", {k: round(v["d"], 3) for k, v in seg.items()})
