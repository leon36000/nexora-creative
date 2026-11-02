"""Écrit brief.json du film « Modèles et API » (captures réelles de /modeles + terminal en code ; voir capturer.mjs et terminal.py)."""
import json
from pathlib import Path

G = 60 / 128 * 0.5            # grille : une croche à 128 BPM (mesuré sur mod-musique-72.flac)
g = lambda n: round(n * G, 4)  # noqa: E731
CARTE_H = [0.33, 0.27, 0.962, 0.73]
CARTE_HV = [0.06, 0.40, 0.94, 0.68]
CARTE_P = [0.33, 0.30, 0.962, 0.70]
CARTE_PV = [0.06, 0.42, 0.94, 0.62]
CARTE_C = [0.33, 0.30, 0.962, 0.70]
CARTE_CV = [0.06, 0.40, 0.94, 0.62]
PAGE = "0000-page"


def frappes(t0, t1, pas=0.17):
    n = int((t1 - t0) / pas)
    return [{"t": round(t0 + k * pas, 3), "type": "frappe", "duree": 0.08, "db": -24} for k in range(n)]


def cam(d, ks):  # [[t_rel (0..1), cx, cy, w]] → temps absolus
    return [[round(t * d, 3), cx, cy, w] for t, cx, cy, w in ks]


seg = {}
T1, T2 = g(20), g(16)
seg["s1"] = {"type": "ecran", "d": T1, "images": [[0, T1, "t1"]], "images_v": [[0, T1, "t1v"]], "cadre": cam(T1, [[0, .5, .43, .93], [1, .5, .43, .87]]),
             "cadre_v": [[0, 0.5, 0.5, 1.0]], "carte_v": [0.04, 0.30, 0.96, 0.72],
             "textes": [{"t": 0.0, "d": T1, "cle": "prepa", "style": "prepa"},
                        {"t": 0.2, "d": T1 - 0.3, "cle": "t_cle", "style": "titre"}],
             "sfx": frappes(0.25, 1.85) + [{"t": 1.98, "type": "clic", "duree": 0.15, "db": -14},
                                           {"t": 2.5, "type": "clic", "duree": 0.12, "db": -22}], "preuve": True}
seg["s2"] = {"type": "ecran", "d": T2, "images": [[0, T2, "t2"]], "images_v": [[0, T2, "t2v"]], "cadre": cam(T2, [[0, .5, .43, .93], [1, .5, .43, .87]]),
             "cadre_v": [[0, 0.5, 0.5, 1.0]], "carte_v": [0.04, 0.30, 0.96, 0.72],
             "textes": [{"t": 0.0, "d": T2, "cle": "prepa", "style": "prepa"},
                        {"t": 0.1, "d": T2 - 0.2, "cle": "t_ligne", "style": "titre"}],
             "sfx": frappes(1.0, 1.8, 0.14) + [{"t": 0.5, "type": "clic", "duree": 0.12, "db": -20},
                                               {"t": 2.28, "type": "clic", "duree": 0.15, "db": -14},
                                               {"t": 1.3, "type": "montee", "duree": T2 - 1.3, "db": -27}]}
seg["s3"] = {"type": "ecran", "d": g(16), "carte": CARTE_H, "carte_v": CARTE_HV, "entree": True,
             "images": [[0, g(16), "page"]],
             "cadre": cam(g(16), [[0, .295, .121, .45], [1, .295, .121, .42]]),
             "cadre_v": cam(g(16), [[0, .295, .106, .40], [1, .295, .106, .38]]),
             "textes": [{"t": 0.0, "d": g(16), "cle": "reel", "style": "sur"},
                        {"t": 0.1, "d": g(16) - 0.2, "cle": "t_fiche", "style": "titre"}],
             "sfx": [{"t": 0.0, "type": "impact", "duree": 1.8, "db": -23}]}
seg["s4"] = {"type": "ecran", "d": g(18), "carte": CARTE_P, "carte_v": CARTE_PV, "images": [[0, g(18), "page"]],
             "cadre": cam(g(18), [[0, .50, .345, .26], [0.25, .50, .345, .26], [0.5, .777, .345, .26], [1, .777, .345, .26]]),
             "cadre_v": cam(g(18), [[0, .50, .345, .26], [0.25, .50, .345, .26], [0.5, .777, .345, .26], [1, .777, .345, .26]]),
             "textes": [{"t": 0.0, "d": g(18), "cle": "reel", "style": "sur"},
                        {"t": 0.1, "d": g(18) - 0.2, "cle": "t_prix", "style": "titre"}],
             "sfx": [{"t": 0.0, "type": "fouet", "duree": 0.35, "db": -24}, {"t": g(9), "type": "fouet", "duree": 0.3, "db": -26}]}
seg["s5"] = {"type": "ecran", "d": g(22), "carte": CARTE_C, "carte_v": CARTE_CV, "images": [[0, g(22), "page"]],
             "cadre": cam(g(22), [[0, .33, .43, .50], [0.4, .33, .43, .50], [0.55, .74, .455, .34], [1, .74, .455, .34]]),
             "cadre_v": cam(g(22), [[0, .33, .43, .50], [0.4, .33, .43, .50], [0.55, .74, .455, .34], [1, .74, .455, .34]]),
             "textes": [{"t": 0.0, "d": g(22), "cle": "reel", "style": "sur"},
                        {"t": 0.1, "d": g(10) + 0.1, "cle": "t_filtres", "style": "titre"},
                        {"t": g(11) + 0.1, "d": g(11) - 0.2, "cle": "t_statut", "style": "titre"}],
             "sfx": [{"t": 0.0, "type": "fouet", "duree": 0.35, "db": -24}, {"t": g(11), "type": "fouet", "duree": 0.3, "db": -26}]}
seg["silence"] = {"type": "noir", "d": g(2)}
seg["fin"] = {"type": "fin", "d": g(20), "t_marque": g(4), "sfx": [{"t": g(4), "type": "impact", "duree": 1.6, "db": -20}]}
# versions courtes : mêmes images, comprimées (les images d'un segment sont réparties sur sa durée)
seg["s1c"] = {**json.loads(json.dumps(seg["s1"])), "d": g(12), "images": [[0, g(12), "t1"]], "images_v": [[0, g(12), "t1v"]],
              "sfx": frappes(0.15, 1.2, 0.12) + [{"t": 1.25, "type": "clic", "duree": 0.15, "db": -14}]}
seg["s1c"]["textes"] = [{"t": 0.0, "d": g(12), "cle": "prepa", "style": "prepa"}, {"t": 0.15, "d": g(12) - 0.2, "cle": "t_cle", "style": "titre"}]
seg["s2c"] = {**json.loads(json.dumps(seg["s2"])), "d": g(12), "images": [[0, g(12), "t2"]], "images_v": [[0, g(12), "t2v"]],
              "sfx": frappes(0.6, 1.3, 0.12) + [{"t": 1.9, "type": "clic", "duree": 0.15, "db": -14}]}
seg["s2c"]["textes"] = [{"t": 0.0, "d": g(12), "cle": "prepa", "style": "prepa"}, {"t": 0.1, "d": g(12) - 0.2, "cle": "t_ligne", "style": "titre"}]
seg["s3c"] = {**json.loads(json.dumps(seg["s3"])), "d": g(12), "images": [[0, g(12), "page"]]}
seg["s3c"]["textes"] = [{"t": 0.0, "d": g(12), "cle": "reel", "style": "sur"}, {"t": 0.1, "d": g(12) - 0.2, "cle": "t_fiche", "style": "titre"}]
seg["s4c"] = {**json.loads(json.dumps(seg["s4"])), "d": g(14), "images": [[0, g(14), "page"]],
              "cadre": cam(g(14), [[0, .50, .345, .26], [0.25, .50, .345, .26], [0.5, .777, .345, .26], [1, .777, .345, .26]]),
              "cadre_v": cam(g(14), [[0, .50, .345, .26], [0.25, .50, .345, .26], [0.5, .777, .345, .26], [1, .777, .345, .26]])}
seg["s4c"]["textes"] = [{"t": 0.0, "d": g(14), "cle": "reel", "style": "sur"}, {"t": 0.1, "d": g(14) - 0.2, "cle": "t_prix", "style": "titre"}]
seg["s4c"]["sfx"] = [{"t": 0.0, "type": "fouet", "duree": 0.35, "db": -24}, {"t": g(7), "type": "fouet", "duree": 0.3, "db": -26}]

# musique : coup fort à 14,99 s de la source, tombant au début de la page réelle ; coup final à 36,47 s sous le nom du carton
HIT, FINAL = 14.99, 36.47
q = lambda tm: {"segment": "fin", "source": round(FINAL - tm, 3), "db": -5}  # noqa: E731
V = {
    "long": {"cible": 30, "ordre": ["s1", "s2", "s3", "s4", "s5", "silence", "fin"],
             "musique": {"repere_segment": "s3", "arret_segment": "silence", "silence": "silence", "queue": q(g(4))}},
    "15": {"cible": 15, "ordre": ["s1c", "s2c", "s3c", "s4c", {"id": "silence"}, {"id": "fin", "d": g(14), "t_marque": g(3)}],
           "musique": {"repere_segment": "s3c", "arret_segment": "silence", "silence": "silence", "queue": q(g(3))}},
}
T = {
    "fr": {"prepa": "Aperçu", "t_cle": "Une clé.|Plusieurs *modèles.*", "t_ligne": "Changez de modèle.|Changez *une ligne.*",
           "t_fiche": "Une fiche|par *modèle.*", "t_prix": "Prix en *dollars canadiens.*|Hébergement *affiché.*",
           "t_filtres": "Filtrez par *capacité, licence, prix.*", "t_statut": "Le catalogue est en *préparation.*",
           "slogan": "Une clé.|Plusieurs *modèles.*", "sous_titre": "Modèles et API par Nexora.",
           "mentions": "Aperçu : l'API n'est pas encore ouverte · captures de la page Modèles et API · clé, adresse et modèles fictifs"},
    "en": {"prepa": "Preview", "t_cle": "One key.|Many *models.*", "t_ligne": "Swap the model.|Change *one line.*",
           "t_fiche": "A spec sheet|per *model.*", "t_prix": "Prices in *Canadian dollars.*|Hosting *shown.*",
           "t_filtres": "Filter by *capability, license, price.*", "t_statut": "The catalogue is *in preparation.*",
           "slogan": "One key.|Many *models.*", "sous_titre": "Models and API by Nexora.",
           "mentions": "Preview: the API is not open yet · screen captures of the Models and API page (French) · fictional key, address and models"},
}
B = {
    "_gabarit": "Généré par fabriquer_brief.py ; éditer le script, pas ce fichier.",
    "film": "modeles", "titre": "Modèles et API : une clé, plusieurs modèles", "nom_fichier": "Modeles-et-API-film", "produit": "MODÈLES ET API",
    "date": "2026-11-02", "marque": "../../marque.json", "travail": "~/nexora-creative-data/promo/v5/modeles",
    "captures": "~/nexora-creative-data/promo/v5/modeles/ui",
    "concept": "Un appel d'API tapé, la réponse en continu (terminal en code, étiqueté Aperçu : l'API n'est pas ouverte), puis une seule "
               "ligne qui change pour changer de modèle ; ensuite la vraie page /modeles du site : une fiche par modèle, prix en dollars "
               "canadiens et hébergement affichés, filtres, et l'état réel du catalogue (en préparation).",
    "public": "développeurs et responsables techniques de PME qui veulent un point d'accès unique à plusieurs modèles",
    "formats": ["16x9", "9x16"], "langues": ["fr", "en"], "affiche": {"t": 9.4, "langue": "fr"},
    "note_manifeste": "Aperçu : l'API n'est pas ouverte et le catalogue est en préparation. Captures réelles de la page /modeles du site "
                      "en ligne (français) ; terminal rendu en code d'après l'exemple d'appel de la page (clé masquée, adresse et "
                      "identifiants de modèles fictifs, réponse figurée). Aucun prix ni mesure.",
    "commandes": {"plaques": "", "captures": "node capturer.mjs ~/nexora-creative-data/promo/v5/modeles/ui && python3 terminal.py ~/nexora-creative-data/promo/v5/modeles/ui"},
    "musique": {"fichier": "~/nexora-creative-data/promo/v5/modeles/audio/mod-musique-72.flac",
                "brief": "musique.py (graine 72), mesurée : 128,0 BPM (temps 0,46875 s), intro calme 0-14 s, coup fort à 14,99 s (mesure 16), "
                         "groove jusqu'à 29 s, respiration puis coup final à 36,47 s et queue jusqu'à 44 s.",
                "bpm": 128.0, "subdivision": 0.5, "repere_source": HIT},
    "segments": seg, "versions": V, "textes": T,
    "revue": {"date": "2026-11-02",
              "grille_severe": {"concept": 7, "preuve_rapide": 6.5, "textes": 7.5, "rythme": 6.5, "son": 6, "finition": 7, "authenticite": 9},
              "note": 7.1, "livre": False,
              "mesures": "long 26,7 s (PLAN : 30 s), 15 s = 15,5 s ; réponse en continu à 2,5 s (illustrative, étiquetée Aperçu) ; coup de musique au début de la page réelle (8,4 s) ; -14,7 LUFS ; plan moyen 3,8 s",
              "faiblesses": ["sous le seuil de livraison (7,5) : non publié dans site-medias ni dans le manifeste",
                             "le catalogue du site est vide (aucun modèle publié) : pas de fiche, de filtre en action ni de prix à filmer ; le film montre des cartes de texte sur fond sombre, d'aspect semblable",
                             "la preuve du début est un terminal en code (appel et réponse figurés), pas un appel réel : l'API n'est pas ouverte",
                             "captures du site en français dans la version anglaise (mentionné au carton) ; en-tête du site non montré (nom de marque et adresse ts.net)",
                             "musique et bruitages jugés aux chiffres, personne n'a écouté ; version 9:16 : grand vide sous les cartes",
                             "pour passer 7,5 : attendre un modèle publié et filmer sa fiche réelle, les filtres et un appel réel"]},
}
Path(__file__).with_name("brief.json").write_text(json.dumps(B, ensure_ascii=False, indent=1))
print("brief.json écrit")
