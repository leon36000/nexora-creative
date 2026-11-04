"""Contrôle d'un dossier créatif du concours OPSYS-AI (le même pour les quatre équipes).
Usage : python3 valider.py chemin/vers/dossier.json [palette.json]
Affiche chaque erreur (bloquante) et avertissement avec l'endroit et la correction attendue ; code de sortie 1 s'il y a des erreurs.
Reprend les règles de l'EditPlan v1 (app/server/nexora/montage/editplan.ts) et le budget du BRIEF (§5)."""
import json
import re
import sys
from pathlib import Path

GRILLE = [124 + 17 * k for k in range(8)]
RECETTES = {"h3-max", "h3-fast"}
INC = {"titre": ["texte"], "impact": ["texte"], "pile": ["lignes"], "surtitre": ["texte"], "etiquette": ["texte"], "statut": ["texte"],
       "document": ["titre", "lignes"], "compteur": ["de", "a"], "courbe": ["points"], "cedule": ["semaines", "blocs"],
       "pointage": ["heure", "nom"], "appel": ["nom"], "trajet": ["points"], "flash": [], "glitch": [], "carton": []}
SFX = {"fouet", "impact", "montee", "inverse", "chute", "clic", "frappe", "souffle", "boom", "drone", "explosion", "tir", "canons"}
INTERDITS = ["nvidia", "tableau de bord", "dashboard", "iphone", "apple", "samsung", "bell", "vidéotron", "hydro-québec", "tron"]


def main(f, palette=None):
    E, A = [], []
    err = lambda ou, m: E.append(f"ERREUR  {ou} : {m}")  # noqa: E731
    av = lambda ou, m: A.append(f"avert.  {ou} : {m}")  # noqa: E731
    try:
        D = json.loads(Path(f).read_text())
    except Exception as e:
        print(f"ERREUR  dossier.json illisible : {e}")
        return 1
    pal = set()
    if palette and Path(palette).exists():
        pal = set(json.loads(Path(palette).read_text())["voix"])
    for k in ("equipe", "titre", "personnages", "voix", "plans", "musique", "montage", "annexe"):
        if k not in D:
            err(k, "champ manquant")
    refs_ok = {p["id"] for p in D.get("personnages", []) + D.get("lieux", []) + D.get("objets", [])}
    persos = {p["id"] for p in D.get("personnages", [])}
    cles = {k["id"] for k in D.get("cles", [])}
    voix = {v["id"]: v for v in D.get("voix", [])}
    nfiches = len(D.get("personnages", [])) + len(D.get("lieux", [])) + len(D.get("objets", []))
    if nfiches > 8:
        err("personnages+lieux+objets", f"{nfiches} fiches : 8 au plus (BRIEF §5)")
    if len(cles) > 24:
        err("cles", f"{len(cles)} images clés : 24 au plus")
    for p in D.get("personnages", []) + D.get("lieux", []) + D.get("objets", []):
        if not p.get("fiche") or len(p["fiche"]) < 40:
            err(f"fiche {p.get('id')}", "description de fiche absente ou trop courte (apparence, tenue, âge…)")
    # voix
    if len(voix) > 30:
        err("voix", f"{len(voix)} répliques : 30 au plus")
    for v in D.get("voix", []):
        ou = f"voix {v.get('id')}"
        if pal and v.get("voix") not in pal:
            err(ou, f"voix « {v.get('voix')} » absente de la palette ({', '.join(sorted(pal))})")
        if not v.get("texte"):
            err(ou, "texte vide")
        if int(v.get("prises", 1)) > 3:
            err(ou, "3 prises au plus")
        if not 0.8 <= float(v.get("vitesse", 1.0)) <= 1.3:
            err(ou, "vitesse entre 0,8 et 1,3")
        for w in INTERDITS:
            if re.search(rf"\b{w}\b", v.get("texte", "").lower()):
                av(ou, f"mot à éviter : « {w.strip()} »")
    # plans et budget
    u169, u916, parl = 0, 0, 0
    ids = set()
    for p in D.get("plans", []):
        ou = f"plan {p.get('id')}"
        if p.get("id") in ids:
            err(ou, "identifiant en double")
        ids.add(p.get("id"))
        if p.get("recette") not in RECETTES:
            err(ou, f"recette « {p.get('recette')} » : h3-max ou h3-fast")
        im = int(p.get("images", 124))
        if im not in GRILLE:
            err(ou, f"images = {im} : valeurs permises {GRILLE} (24 i/s, grille 17k+5)")
        n = 1 if im <= 124 else 2
        if p.get("format", "16:9") == "9:16":
            u916 += n
        else:
            u169 += n
        for r in p.get("refs", []):
            if r not in refs_ok:
                err(ou, f"référence inconnue « {r} » (déclarer dans personnages/lieux/objets)")
        nimg = sum(2 if r in persos else 1 for r in p.get("refs", []))
        if nimg > 9:
            err(ou, f"{nimg} images de référence (un personnage = 2 images) : 9 au plus")
        if p.get("refs") and p.get("recette") == "h3-fast":
            err(ou, "les références n'existent qu'en h3-max")
        pr = p.get("prompt", "")
        for r in p.get("refs", []):
            if f"@{r}" not in pr:
                av(ou, f"la référence {r} n'est pas nommée dans le prompt (@{r})")
        for sec in ("summary:", "detailed_description:", "[Shot 1]", "overall_soundscape:"):
            if sec not in pr:
                err(ou, f"section « {sec} » absente du prompt H3 (grammaire BRIEF §4.1)")
        if "no text" not in pr.lower():
            av(ou, "ajouter « No text, no logos » dans le prompt (H3 écrit spontanément)")
        if p.get("premiere"):
            pm = p["premiere"]
            if pm.startswith("fin:"):
                if pm[4:] not in {q.get("id") for q in D.get("plans", [])}:
                    err(ou, f"premiere {pm} : plan inconnu")
            elif pm not in cles:
                err(ou, f"premiere {pm} : image clé inconnue")
        if p.get("parole"):
            parl += 1 if p.get("format", "16:9") == "16:9" else 0
            if p["parole"] not in voix:
                err(ou, f"parole {p['parole']} : réplique inconnue")
            if p.get("recette") != "h3-max":
                err(ou, "un plan parlant est en h3-max")
            else:
                t = voix.get(p["parole"], {}).get("texte", "")
                if len(t) / 14 > 9.8:
                    err(ou, f"réplique {p['parole']} trop longue pour un plan (≈ {len(t) / 14:.1f} s > 10 s) : la couper en deux plans")
        for w in INTERDITS:
            if re.search(rf"\b{w}\b", pr.lower()) and not re.search(rf"no {w}\b", pr.lower()):
                av(ou, f"mot à éviter dans le prompt : « {w.strip()} »")
    if u169 > 40:
        err("plans", f"{u169} unités 16:9 : 40 au plus (un plan de 125 à 243 images = 2 unités)")
    if u916 > 6:
        err("plans", f"{u916} unités 9:16 : 6 au plus")
    if parl > 12:
        err("plans", f"{parl} plans parlants : 12 au plus")
    # musique
    mu = D.get("musique", {})
    prompts = mu.get("prompts") or ([mu["prompt"]] if mu.get("prompt") else [])
    if not prompts:
        err("musique", "prompt Lyria absent")
    if len(prompts) > 3:
        err("musique", "3 générations au plus")
    # montage
    for ver, (dmin, dmax) in (("long", (90, 180)), ("court", (10, 15)), ("vertical", (10, 15))):
        P = (D.get("montage") or {}).get(ver)
        if not P:
            if ver != "vertical":
                err(f"montage.{ver}", "EditPlan absent")
            continue
        ann = (D.get("annexe") or {}).get(ver) or {}
        verifier_plan(P, ann, ver, dmin, dmax, ids, voix, err, av)
    print(f"{D.get('equipe')} · « {D.get('titre')} » : {len(D.get('plans', []))} plans, {u169} unités 16:9 / 40, {u916} unités 9:16 / 6, "
          f"{parl} plans parlants / 12, {len(voix)} répliques, {nfiches} fiches, {len(cles)} images clés")
    for l in E + A:
        print(l)
    print("OK" if not E else f"{len(E)} erreur(s)")
    return 1 if E else 0


def verifier_plan(P, ann, ver, dmin, dmax, ids, voix, err, av):
    ou = f"montage.{ver}"
    if P.get("version") != 1 or P.get("fps") != 24:
        err(ou, "version 1 et fps 24 exigés")
    if P.get("format") not in ("16:9", "9:16"):
        err(ou, "format 16:9 ou 9:16")
    src = P.get("sources", {})
    total, vus = 0, set()
    for i, c in enumerate(P.get("video", [])):
        o = f"{ou}.video[{i}]"
        for k in ("id", "src", "duree_f"):
            if k not in c:
                err(o, f"champ {k} manquant")
        for k in ("entree_f", "duree_f"):
            if k in c and not isinstance(c[k], int):
                err(o, f"{k} doit être un entier d'images")
        if c.get("id") in vus:
            err(o, "id de plan monté en double")
        vus.add(c.get("id"))
        s = c.get("src")
        if s not in src:
            err(o, f"source {s} non déclarée dans sources")
        elif src[s].get("kind") == "video" and s not in ids:
            err(o, f"source vidéo {s} : aucun plan tourné de ce nom")
        tr = c.get("transition_in") or {"type": "cut", "duree_f": 0}
        if tr.get("type") not in ("cut", "fondu", "dip", "glisse"):
            err(o, "transition cut, fondu, dip ou glisse")
        rec = tr.get("duree_f", 0) if i and tr.get("type") != "cut" else 0
        conso = c.get("duree_f", 0) * (((c.get("rampe") or {}).get("de", 1) + (c.get("rampe") or {}).get("a", 1)) / 2 if c.get("rampe") else c.get("vitesse", 1))
        if src.get(s, {}).get("kind") == "video" and c.get("entree_f", 0) + conso > 243:
            av(o, f"lit jusqu'à l'image {c.get('entree_f', 0) + conso:.0f} : vérifier la longueur du plan tourné (124 = 5,2 s)")
        if not 0.25 <= c.get("vitesse", 1) <= 4:
            err(o, "vitesse entre 0,25 et 4")
        total += c.get("duree_f", 0) - rec
    d = total / 24
    if not dmin <= d <= dmax:
        err(ou, f"durée {d:.1f} s hors de [{dmin}, {dmax}] s")
    A = P.get("audio") or {}
    m = A.get("musique")
    if not m:
        av(ou, "pas de musique")
    if A.get("voix") and m and (not (A.get("ducking") or {}).get("actif") or (A.get("ducking") or {}).get("profondeur_db", 0) < 6):
        err(ou, "voix sur musique : ducking actif ≥ 6 dB exigé")
    for j, v in enumerate(A.get("voix", [])):
        if v.get("src") not in voix:
            err(f"{ou}.audio.voix[{j}]", f"réplique {v.get('src')} inconnue")
        if v.get("debut_f", 0) + v.get("duree_f", 0) > total + 1:
            err(f"{ou}.audio.voix[{j}]", "la voix dépasse la fin du film")
    for j, t in enumerate(P.get("textes", [])):
        l = t.get("texte", "").split("\n")
        if len(l) > 2 or any(len(x) > 42 for x in l):
            err(f"{ou}.textes[{j}]", "deux lignes de 42 caractères au plus")
    for j, s in enumerate(ann.get("incrustations", [])):
        o = f"annexe.{ver}.incrustations[{j}]"
        t = s.get("type")
        if t not in INC:
            err(o, f"type « {t} » inconnu ({', '.join(INC)})")
            continue
        for k in ["debut_f", "duree_f"] + INC[t]:
            if k not in s:
                err(o, f"champ {k} manquant pour {t}")
        if s.get("debut_f", 0) + s.get("duree_f", 0) > total + 1:
            err(o, "dépasse la fin du film")
        if t == "titre" and len(re.sub(r"[*|]", " ", s.get("texte", "")).split()) > 7:
            av(o, "titre de plus de 7 mots")
        if t in ("titre", "impact") and s.get("duree_f", 99) / 24 < 0.3 * len(s.get("texte", "").split()) + 0.5:
            av(o, "temps de lecture court (0,3 s par mot + 0,5 s)")
    for j, x in enumerate(ann.get("sfx", [])):
        if x.get("type") not in SFX:
            err(f"annexe.{ver}.sfx[{j}]", f"bruitage « {x.get('type')} » inconnu ({', '.join(sorted(SFX))})")
    if not any(s.get("type") == "carton" for s in ann.get("incrustations", [])):
        err(f"annexe.{ver}", "aucun carton final (incrustation « carton » : nom et logo remplaçables)")


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
