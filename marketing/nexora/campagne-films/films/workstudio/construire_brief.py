"""Écrit brief.json du film WorkStudio (v2 : cycle réel complet) à partir des captures de ui2 et de leur journal.

Pourquoi un script : les positions du curseur sont celles des VRAIS clics (journal.jsonl de la capture), et trois versions
(long, 30, 15) partagent les mêmes segments avec des durées et des textes différents. Relancer après chaque nouvelle capture :
    python3 construire_brief.py && python3 ../../usine/usine.py brief.json valider montage animatique
Grille musicale : un temps = 0,71875 s (83,478 BPM mesurés), subdivision 1/2 → U = 0,359375 s ; toutes les durées sont des
multiples de U (le validateur le vérifie).
"""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
U = 0.359375
CAP = Path.home() / "nexora-creative-data/promo/v5/workstudio/ui2"
b = json.loads((ICI / "brief.json").read_text())


def pos():
    """Positions réelles des clics, par cycle (fr1, fr2, en1, en2) : {cycle: {nom: (x, y)}} (fractions de la fenêtre au moment du clic)."""
    out, cur = {}, None
    for ligne in (CAP / "journal.jsonl").read_text().splitlines():
        e = json.loads(ligne)
        if e.get("etape") == "executer":
            cur = e["c"]
            out[cur] = {}
        elif "pos" in e and cur:
            out[cur][e["pos"]] = (e["x"], e["y"])
    return out


P = pos()
p1 = P["fr1"]  # fr et en ont la même mise en page ; on prend le premier cycle de chaque cas
p2 = P["fr2"]


def u(n):
    return round(n * U, 6)


def C(*cles):  # un texte {l} : cycle numéro 1 ou 2 → étiquette « {l}1:exec »
    return cles


def im(t0, t1, cyc, et, *plage):
    return [t0, t1, f"{{l}}{cyc}:{et}", *plage]


# ----------------------------------------------------------------------------------------------------------------- segments
# Cadres : [t, cx, cy, largeur] en fractions de la capture. Éditeur (fenêtre 2240×1260) : blocs Tri .264, Brouillon .379, Validation .497,
# Approbation .615, Envoi .732, ligne y = .405.
def exec_(cyc, d, textes, preuve=False):
    run = (0.9735, 0.023)  # le bouton « Exécuter » (position réelle du clic)
    D = u(d)
    cad = lambda w: [[0, 0.5, 0.5, 1.0], [0.38, 0.5, 0.5, 1.0], [1.0, 0.285, 0.42, w], [1.9, 0.34, 0.42, w], [2.6, 0.40, 0.42, w], [3.7, 0.47, 0.42, w], [D, 0.50, 0.42, w]]  # noqa: E731
    s = {"type": "ecran", "d": D, "entree": True,
         "images": [im(0, 0.38, cyc, "repos", 0, 1), im(0.45, 4.6, cyc, "exec"), im(4.65, D, cyc, "pause", 0, 5)],
         "cadre": cad(0.32), "cadre_v": cad(0.27), "curseur": [[0, *run]], "clics": [0.35], "textes": textes,
         "sfx": [{"t": 0.35, "type": "clic", "duree": 0.2, "db": -10}]}
    if preuve:
        s["preuve"] = True
    return s


def accord(cyc, d, p, textes, reprise=False, rep=0.0):
    """Page de validation (fenêtre 1300×900) : brouillon, liste, « vrai », survol de Reprendre. Vertical : captures en fenêtre étroite (p*)."""
    t_ch, t_cs, t_sv = u(d) * 0.30, u(d) * 0.50, u(d) * 0.72
    fin = u(d) - rep
    s = {"type": "ecran", "d": u(d), "entree": True,
         "images": [im(0, t_ch - 0.05, cyc, "val"), im(t_ch, t_ch + 0.4, cyc, "choix", 1, 4), im(t_cs, t_cs + 0.5, cyc, "choisi", 0, 4), im(t_sv, fin, cyc, "survol-reprendre")],
         "images_v": [im(0, t_ch - 0.05, cyc, "pval", 0, 2), im(t_ch, t_cs - 0.05, cyc, "pchoix", 1, 4), im(t_cs, t_sv - 0.05, cyc, "pchoisi", 0, 4), im(t_sv, fin, cyc, "psurvol")],
         "cadre": [[0, 0.62, 0.45, 0.68], [t_ch, 0.62, 0.52, 0.66], [t_sv, 0.62, 0.62, 0.66], [u(d), 0.62, 0.62, 0.66]],
         "cadre_v": [[0, 0.5, 0.5, 1.0], [u(d), 0.5, 0.5, 1.0]],
         "textes": textes,
         "sfx": [{"t": t_ch, "type": "clic", "duree": 0.15, "db": -14}, {"t": t_cs, "type": "clic", "duree": 0.15, "db": -14},
                 {"t": max(0.2, u(d) - 1.3), "type": "montee", "duree": 1.2, "db": -20}]}
    (lx, ly), (ox, oy), (rx, ry) = p["liste"], p["option"], p["reprendre"]
    (plx, ply), (pox, poy), (prx, pry) = p["pliste"], p["poption"], p["preprendre"]
    s["curseur_v"] = [[0, plx + 0.10, ply - 0.25], [t_ch - 0.2, plx, ply], [t_ch, plx, ply], [t_cs - 0.15, pox, poy], [t_cs, pox, poy], [t_sv + 0.2, prx, pry], [u(d), prx, pry]]
    s["curseur"] = [[0, lx + 0.12, ly - 0.30], [t_ch - 0.2, lx, ly], [t_ch, lx, ly], [t_cs - 0.15, ox, oy], [t_cs, ox, oy], [t_sv + 0.2, rx, min(ry, 0.99)], [u(d), rx, min(ry, 0.99)]]
    s["clics"] = [t_ch, t_cs]
    if reprise:
        s["images"].append(im(fin, u(d), cyc, "reprise", 0, 3)); s["clics"].append(fin)
    return s


def envoi_a(cyc, d, p):
    """La reprise, sur la page de validation : le clic d'accord (au début du segment, sur le coup de la musique)."""
    rx, ry = p["reprendre"]
    return {"type": "ecran", "d": u(d), "images": [im(0, u(d), cyc, "reprise")],
            "cadre": [[0, 0.30, 0.20, 0.56], [u(d), 0.30, 0.20, 0.56]],
            "cadre_v": [[0, 0.27, 0.22, 0.50], [u(d), 0.27, 0.22, 0.50]],
            "curseur": [[0, rx, min(ry, 0.99)]], "clics": [0.04],
            "textes": [{"t": 0.0, "d": u(d), "cle": "sur_reprise", "style": "sur"}],
            "sfx": [{"t": 0.0, "type": "clic", "duree": 0.2, "db": -8}]}


def envoi_b(cyc, d, p, textes):
    """Les journaux : l'exécution est « Réussi », puis la trace étape par étape."""
    lx, ly = p["ligne"]; tx, ty = p["trace"]
    dj = u(d) * 0.45
    return {"type": "ecran", "d": u(d),
            "images": [im(0, dj, cyc, "jrnd", 0, 3), im(dj, u(d), cyc, "trace")],
            "cadre": [[0, 0.80, 0.22, 0.44], [dj - 0.05, 0.80, 0.22, 0.44], [dj + 0.25, 0.885, 0.22, 0.27], [u(d), 0.885, 0.22, 0.27]],
            "cadre_v": [[0, 0.84, 0.26, 0.40], [dj - 0.05, 0.84, 0.26, 0.40], [dj + 0.25, 0.885, 0.24, 0.26], [u(d), 0.885, 0.24, 0.26]],
            "curseur": [[0, lx, ly], [dj - 0.3, tx, ty], [dj, tx, ty], [u(d), tx, ty]], "clics": [dj],
            "textes": textes, "sfx": [{"t": dj, "type": "clic", "duree": 0.15, "db": -14}]}


def mail(cyc, d, textes):
    """La boîte de test (Mailpit) : le courriel est arrivé, puis son contenu. Vertical : message en fenêtre étroite."""
    dm = u(d) * 0.38
    return {"type": "ecran", "d": u(d), "entree": True,
            "images": [im(0, dm, cyc, "mp", 0, 3), im(dm, u(d), cyc, "mpm")],
            "images_v": [im(0, dm, cyc, "mp", 0, 3), im(dm, u(d), cyc, "vmpm")],
            "cadre": [[0, 0.33, 0.10, 0.55], [dm - 0.05, 0.33, 0.10, 0.55], [dm + 0.25, 0.60, 0.24, 0.76], [u(d), 0.60, 0.24, 0.76]],
            "cadre_v": [[0, 0.30, 0.10, 0.46], [dm - 0.05, 0.30, 0.10, 0.46], [dm - 0.04, 0.5, 0.47, 1.0], [u(d), 0.5, 0.47, 1.0]],
            "textes": textes, "sfx": [{"t": 0.0, "type": "fouet", "duree": 0.4, "db": -20}]}


def sur(cle, t0, d):
    return {"t": t0, "d": d, "cle": cle, "style": "sur"}


def ti(cle, t0, d, **k):
    return {"t": t0, "d": d, "cle": cle, "style": "titre", **k}


S = {}
S["exec1"] = exec_("1", 16, [sur("sur_courriel", 0, 5.7), {"t": 0.3, "d": 2.1, "cle": "c_courriel1", "style": "citation", "frappe": 1.0},
                              ti("t_trie", 2.6, 3.1)], preuve=True)
S["accord1"] = accord("1", 10, p1, [ti("t_attend", 0.1, 3.4)])
S["envoi1a"] = envoi_a("1", 4, p1)
S["envoi1b"] = envoi_b("1", 10, p1, [sur("sur_journal", 0, 3.5), ti("t_envoi", 0.2, 2.9)])
S["mail1"] = mail("1", 12, [sur("sur_test", 0, 4.3), ti("t_arrive", 0.3, 3.2)])
S["exec2"] = exec_("2", 12, [sur("sur_courriel", 0, 4.2), {"t": 0.2, "d": 1.5, "cle": "c_courriel2", "style": "citation", "frappe": 0.9},
                              ti("t_autre", 1.8, 2.45)])
S["accord2"] = accord("2", 8, p2, [ti("t_sans_vous", 0.2, 2.5)], reprise=True, rep=0.6)
S["mail2"] = mail("2", 10, [sur("sur_test2", 0, 3.5), ti("t_deux", 0.3, 3.2)])
S["impact"] = {"type": "noir", "d": u(6), "textes": [{"t": 0.0, "d": u(6), "cle": "t_bloc", "style": "impact", "zone": "centre"}],
               "sfx": [{"t": 0.0, "type": "impact", "duree": 2.0, "db": -16}]}
S["etapes"] = {"type": "ecran", "d": u(8), "entree": True, "images": [im(0, 1.4, "x", "etapes", 0, 7), im(1.45, u(8), "x", "etapes-bas")],
               "cadre": [[0, 0.44, 0.3, 0.36], [1.4, 0.44, 0.4, 0.36], [1.45, 0.44, 0.3, 0.36], [u(8), 0.44, 0.45, 0.35]],
               "cadre_v": [[0, 0.44, 0.33, 0.34], [1.4, 0.44, 0.45, 0.34], [1.45, 0.44, 0.33, 0.34], [u(8), 0.44, 0.5, 0.33]],
               "textes": [sur("sur_etapes", 0, 2.85), ti("t_etapes", 0.3, 2.5)], "sfx": [{"t": 1.4, "type": "fouet", "duree": 0.4, "db": -24}]}
S["blocs"] = {"type": "ecran", "d": u(14), "entree": True,
              "images": [im(0, 0.9, "x", "blocs-repos", 0, 2), im(1.0, 1.7, "x", "blocs-Agent"), im(1.75, 2.9, "x", "blocs-Agent-vue"),
                         im(3.0, 3.7, "x", "blocs-Fonction"), im(3.75, u(14), "x", "blocs-Fonction-vue")],
              "cadre": [[0, 0.40, 0.42, 0.60], [3.0, 0.42, 0.50, 0.64], [u(14), 0.42, 0.52, 0.66]], "cadre_v": [[0, 0.32, 0.42, 0.50], [3.0, 0.36, 0.5, 0.56], [u(14), 0.38, 0.52, 0.60]],
              "textes": [ti("t_changer", 0.3, 2.6), ti("t_ajout", 3.0, 2.1)],
              "sfx": [{"t": 1.0, "type": "clic", "duree": 0.15, "db": -14}, {"t": 3.0, "type": "clic", "duree": 0.15, "db": -14}]}
S["silence"] = {"type": "noir", "d": u(2)}
S["fin"] = {"type": "fin", "d": u(18), "t_marque": 4.25}


def variante(base, nom, d, **chg):
    S[nom] = {**json.loads(json.dumps(S[base])), "d": u(d), **chg}


# 30 s et 15 s : mêmes plans, resserrés ; textes recoupés à la durée
variante("exec1", "exec1_30", 12, textes=[sur("sur_courriel", 0, 4.2), {"t": 0.2, "d": 1.7, "cle": "c_courriel1", "style": "citation", "frappe": 0.9}, ti("t_trie", 2.0, 2.3)])
variante("accord1", "accord1_30", 8)
variante("envoi1b", "envoi1b_30", 6, textes=[sur("sur_journal", 0, 2.1), ti("t_envoi", 0.1, 2.0)])
variante("mail1", "mail1_30", 8, textes=[sur("sur_test", 0, 2.85), ti("t_arrive", 0.2, 2.5)])
variante("exec2", "exec2_30", 8, textes=[sur("sur_courriel", 0, 2.85), ti("t_autre", 0.4, 2.45)])
variante("accord2", "accord2_30", 6, textes=[ti("t_sans_vous", 0.05, 2.1)])
variante("mail2", "mail2_30", 8, textes=[sur("sur_test2", 0, 2.85), ti("t_deux", 0.2, 2.5)])
variante("blocs", "blocs_30", 10, textes=[ti("t_ajout", 0.3, 3.3)])
variante("fin", "fin_30", 11, t_marque=2.9)
variante("exec1", "exec1_15", 8, textes=[sur("sur_courriel", 0, 2.85), ti("t_trie", 0.9, 1.95)])
variante("accord1", "accord1_15", 6, textes=[ti("t_attend", 0.1, 2.0)])
variante("envoi1a", "envoi1a_15", 3)
variante("mail1", "mail1_15", 8, textes=[sur("sur_test", 0, 2.85), ti("t_arrive", 0.2, 2.5)])
variante("blocs", "blocs_15", 5, textes=[ti("t_ajout", 0.05, 1.7)], images=[im(0, 0.3, "x", "blocs-repos", 0, 1), im(0.35, 1.0, "x", "blocs-Agent"), im(1.05, 1.79, "x", "blocs-Fonction-vue")])
variante("silence", "silence_15", 1)
variante("fin", "fin_15", 12, t_marque=2.5)

ordre_long = ["exec1", "accord1", "envoi1a", "envoi1b", "mail1", "exec2", "accord2", "mail2", "impact", "etapes", "blocs", "silence", "fin"]
ordre_30 = ["exec1_30", "accord1_30", "envoi1a", "envoi1b_30", "mail1_30", "exec2_30", "accord2_30", "mail2_30", "blocs_30", "silence", "fin_30"]
ordre_15 = ["exec1_15", "accord1_15", "envoi1a_15", "mail1_15", "blocs_15", "silence_15", "fin_15"]
queue = lambda seg, src: {"segment": seg, "source": src, "db": -3}  # noqa: E731
b["segments"] = S
b["versions"] = {
    "long": {"cible": 60, "ordre": ordre_long, "musique": {"repere_segment": "envoi1a", "arret_segment": "silence", "silence": "silence", "queue": queue("fin", 7.25)}},
    "30": {"cible": 30, "ordre": ordre_30, "musique": {"repere_segment": "envoi1a", "arret_segment": "silence", "silence": "silence", "queue": queue("fin_30", 8.5)}},
    "15": {"cible": 15, "ordre": ordre_15, "musique": {"repere_segment": "envoi1a_15", "arret_segment": "silence_15", "silence": "silence_15", "queue": queue("fin_15", 9.0)}},
}
b["captures"] = str(CAP).replace(str(Path.home()), "~")
b["travail"] = "~/nexora-creative-data/promo/v5/workstudio"
b["commandes"]["captures"] = ('node capturer.mjs ~/nexora-creative-data/promo/v5/workstudio/ui2 "$TEMOINS" '
                              '2533f479-26dd-478e-9260-1d237c6abf67,c27a6dcb-de1e-4fa9-8c0c-67b264d0bebe')
b["titre"] = "WorkStudio : un courriel, un brouillon, votre accord, l'envoi"
b["concept"] = ("Deux vrais courriels de clients arrivent dans une boulangerie fictive. Le workflow « Tri du courrier entrant » trie, "
                "rédige, s'arrête sur la validation humaine ; au clic d'accord le courriel part vers une boîte de test (Mailpit) et "
                "l'exécution se lit dans les journaux. Puis l'étendue : la vue Étapes et des blocs ajoutés à la main.")
b["affiche"] = {"t": 15.2, "langue": "fr"}
T = b["textes"]
T["fr"].update({
    "sur_courriel": "Courriel reçu", "c_courriel1": "Possible de le livrer plutôt à 11 h ?", "c_courriel2": "Une soumission pour 40 croissants ?",
    "t_trie": "Il trie.|Il *rédige.*", "t_pause": "Il s'arrête avant *d'envoyer.*", "t_attend": "Il attend *votre accord.*",
    "sur_reprise": "Vous approuvez", "sur_journal": "Journal d'exécution", "t_envoi": "Votre accord.|Puis *l'envoi.*",
    "sur_test": "Réponse envoyée", "sur_test2": "Boîte de test", "t_arrive": "Envoi vers une|*boîte de test.*", "t_autre": "Un autre courriel.|Une *autre réponse.*",
    "t_deux": "Deux courriels.|Deux *réponses.*", "t_bloc": "Chaque étape est un *bloc.*", "t_changer": "Changez une étape sans *tout refaire.*",
    "t_ajout": "Ajoutez un *agent.*",
    "mentions": "Captures d'écran réelles de Nexora WorkStudio · exemple fictif · envoi vers une boîte de test"})
T["en"].update({
    "sur_courriel": "Incoming email", "c_courriel1": "Could you deliver it at 11 instead?", "c_courriel2": "A quote for 40 croissants?",
    "t_trie": "It sorts.|It *drafts.*", "t_pause": "It stops before *sending.*", "t_attend": "It waits *for you.*",
    "sur_reprise": "You approve", "sur_journal": "Run log", "t_envoi": "Your approval.|Then *it sends.*",
    "sur_test": "Reply sent", "sur_test2": "Test inbox", "t_arrive": "Sent to a|*test inbox.*", "t_autre": "Another email.|Another *reply.*",
    "t_deux": "Two emails.|Two *replies.*", "t_bloc": "Every step is a *block.*", "t_changer": "Change one step. *Keep the rest.*",
    "t_ajout": "Add an *agent.*",
    "mentions": "Real Nexora WorkStudio screen captures · fictional example · sent to a test inbox"})

b["note_manifeste"] = ("Captures réelles de WorkStudio (VM 203), deux exécutions complètes de « Tri du courrier entrant » avec deux courriels différents : "
                       "tri et brouillon par le modèle du relais LiteLLM, pause de validation humaine, accord sur la page de reprise, envoi SMTP vers "
                       "une boîte de test (Mailpit, rien ne sort du réseau), journal d'exécution et trace. Interface capturée en français et en anglais. "
                       "Contenu d'exemple fictif ; le ralenti est un étirement des images réellement capturées (l'exécution dure environ 3 s).")
b["revue"] = {"date": "2026-11-02", "version": "v2 : cycle réel complet",
              "grille_severe": {"concept": 8.5, "preuve_rapide": 8.5, "textes": 8, "rythme": 7.5, "son": 7, "finition": 7.5, "authenticite": 9.5}, "note": 8.1,
              "mesures": "long 46,7 s (60 demandés) ; 1re image réelle à 0,4 s ; clic d'accord à 9,3 s ; courriel reçu à 14,4 s ; −14,2 LUFS (15 s : −14,4 à −14,8) ; crête −1,6 à −2,0 dBTP ; plan moyen 3,6 s",
              "faiblesses": ["46,7 s au lieu de 60 s : rien de réel de plus à montrer sans remplissage (une 3e exécution, le refus « faux », ajouterait 8 s)",
                             "interface blanche et fine : plans d'éditeur peu lisibles en 9:16, beaucoup de vide autour des blocs",
                             "la séquence d'ajout de blocs (Agent, Fonction) est le plan le plus faible : blocs minuscules sur canevas vide",
                             "l'exécution réelle dure environ 3 s : ralenti par étirement d'images (10 images), l'allumage reste saccadé",
                             "musique jugée aux chiffres (BPM 83,5 mesuré, coup à 11,5 s) et jamais à l'oreille ; bruitages synthétiques",
                             "Mailpit reste en anglais dans la version française ; le premier plan (0,4 s) est un plan large illisible"]}
(ICI / "brief.json").write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n")
print("brief.json écrit :", len(S), "segments")
