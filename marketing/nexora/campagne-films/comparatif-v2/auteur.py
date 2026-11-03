"""Étape « auteur » du comparatif v2 : un modèle écrit le film ENTIER (concept, narration, plans avec ses propres prompts,
textes, musique, carton) depuis le brief ; le code valide, demande au plus UNE réparation par classe de violation, puis répare
mécaniquement ce qui reste. Même prompt système et même brief pour tous les modèles ; aucun ne voit la sortie des autres.

  python3 auteur.py <brief: creative|opsys|workstudio> <palier: eco|equilibre|expert> [--force]
  python3 auteur.py valider <film.json> <brief>      (validation seule : sert aussi au film écrit par Opus)
Sortie : ~/nexora-creative-data/work/films-v2/<brief>-<palier>/film.json et auteur.json (jetons, coût, latence, réparations).
Clés lues dans ~/Desktop/Deepinfra.env (« Deepinfra: <clé> » / « Openrouter: <clé> »), jamais affichées.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
TRAVAIL = Path.home() / "nexora-creative-data/work/films-v2"
MARGE, USD_CAD = 1.10, 1.4025

OR = "https://openrouter.ai/api/v1"
PALIERS = {
    "eco": {"modele": "deepseek-ai/DeepSeek-V4.1-Flash-1017", "url": "https://api.deepinfra.com/v1/openai", "cle": "Deepinfra",
            "prix": (0.20, 0.60), "efforts": [None], "corps": lambda e: {}},
    "equilibre": {"modele": "meta/muse-spark-1.3-contributor", "url": OR, "cle": "Openrouter", "prix": (0.10, 0.20),
                  "efforts": ["max", "xhigh", "high"], "corps": lambda e: {"reasoning": {"effort": e}, "usage": {"include": True}}},
    "expert": {"modele": "google/gemini-4-argon", "url": OR, "cle": "Openrouter", "prix": (1.0, 5.0), "efforts": ["high"],
               "corps": lambda e: {"reasoning": {"effort": e}, "usage": {"include": True},
                                   "provider": {"order": ["google-ai-studio/flex"], "allow_fallbacks": False}}},
}
INSERTS = {"workstudio": ["ui-approuver", "ui-tri"]}
INTERDITS_COPIE = ["meilleur", "révolution", "magique", "n°1", "numéro un", "%", "fois plus", "nvidia", "openai", "google", "apple",
                   "chatgpt", "game-changer", "ce n'est pas", "ce n’est pas"]
INTERDITS_PROMPT = ["nvidia", "apple", "iphone", "ipad", "macbook", "samsung", "google", "microsoft", "tesla", "marvel", "disney", "pixar",
                    "star wars", "starbucks", "ford", "chevrolet", "dodge", "ram ", "toyota", "home depot", "rona", "tim hortons",
                    "sign reading", "text reading", "words ", "logo of", "brand logo", "lettering", "caption", "subtitle", "headline"]
STYLES = {"titre", "impact", "sur", "prepa"}


def cles():
    d = {}
    for l in (Path.home() / "Desktop/Deepinfra.env").read_text().splitlines():
        if ":" in l:
            k, v = l.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def mots(t):
    return len([m for m in re.sub(r"[*|]", " ", t).split() if re.search(r"\w", m)])


# ---------------------------------------------------------------------------------------------------------------- valider
def valider(f, brief):
    """Liste de (classe, message avec valeur attendue et correction)."""
    v = []
    plans = f.get("plans") or []
    fin = f.get("fin") or {}
    if f.get("mode") not in ("narration", "texte"):
        v.append(("mode", "« mode » doit valoir narration ou texte"))
    attendu = "texte" if brief == "workstudio" else "narration"
    if f.get("mode") != attendu:
        v.append(("mode", f"le brief impose mode « {attendu} »"))
    if not 12 <= len(plans) <= 22:
        v.append(("plans", f"{len(plans)} plans ; attendu 12 à 22 (hors carton)"))
    ids = set()
    for p in plans:
        pid = p.get("id", "?")
        if pid in ids:
            v.append(("plans", f"id {pid} en double"))
        ids.add(pid)
        d = p.get("duree")
        if not isinstance(d, (int, float)) or not 1.0 <= d <= 5.0:
            v.append(("durees", f"{pid} : durée {d} ; attendu 1,0 à 5,0 s"))
        t = p.get("type")
        if t == "plan":
            for k, lo, hi in (("image", 25, 110), ("mouvement", 8, 60)):
                n = len(str(p.get(k, "")).split())
                if not lo <= n <= hi:
                    v.append(("prompts", f"{pid}.{k} : {n} mots ; attendu {lo} à {hi}"))
            txt = (str(p.get("image", "")) + " " + str(p.get("mouvement", ""))).lower()
            for m in INTERDITS_PROMPT:
                if m in txt:
                    v.append(("prompts", f"{pid} : « {m.strip()} » interdit dans un prompt (marque, ou texte demandé dans l'image) ; réécrire sans"))
        elif t == "ui":
            if p.get("ui") not in INSERTS.get(brief, []):
                v.append(("plans", f"{pid} : insert « {p.get('ui')} » inconnu ; disponibles : {INSERTS.get(brief, []) or 'aucun'}"))
            elif not 1.0 <= (d or 0) <= 2.2:
                v.append(("durees", f"{pid} : un insert d'interface dure 1 à 2 s"))
        elif t == "tableau":
            tb = p.get("tableau") or []
            if brief != "opsys":
                v.append(("plans", f"{pid} : le type tableau est réservé au brief OPSYS-AI"))
            elif not 2 <= len(tb) <= 6 or any(not re.fullmatch(r"M(10|[1-9])", str(x.get("m", ""))) or not 1 <= mots(str(x.get("action", ""))) <= 5 for x in tb):
                v.append(("plans", f"{pid} : tableau = 2 à 6 tuiles {{m: M1..M10, action: 1 à 5 mots}}"))
        else:
            v.append(("plans", f"{pid} : type « {t} » inconnu (plan, ui, tableau)"))
    if brief == "workstudio":
        n_ui = sum(1 for p in plans if p.get("type") == "ui")
        if not 1 <= n_ui <= 2:
            v.append(("plans", f"{n_ui} insert(s) d'interface ; le brief en veut 1 ou 2"))
    n_heros = sum(1 for p in plans if p.get("heros"))
    if n_heros > 3:
        v.append(("plans", f"{n_heros} plans héros ; 3 au maximum"))
    fd = fin.get("duree")
    if not isinstance(fd, (int, float)) or not 3 <= fd <= 5:
        v.append(("durees", f"carton : durée {fd} ; attendu 3 à 5 s"))
        fd = 4
    tp = sum(p.get("duree", 0) or 0 for p in plans if isinstance(p.get("duree"), (int, float)))
    tot = tp + fd
    if not 40 <= tot <= 50:
        v.append(("durees", f"durée totale {tot:.1f} s ; attendu 40 à 50 s (ajuster les durées des plans)"))
    if not fin.get("slogan") or mots(fin.get("slogan", "")) > 7:
        v.append(("textes", "fin.slogan : une ligne de 1 à 7 mots"))
    # textes
    tx = sorted(f.get("textes") or [], key=lambda x: x.get("debut", 0))
    for i, x in enumerate(tx):
        s, d, t = x.get("style"), x.get("duree", 0), str(x.get("texte", ""))
        if s not in STYLES:
            v.append(("textes", f"texte « {t[:30]} » : style « {s} » inconnu ({', '.join(sorted(STYLES))})"))
        lim = {"titre": 7, "impact": 5, "sur": 4, "prepa": 5}.get(s, 7)
        if mots(t) > lim:
            v.append(("textes", f"« {t} » : {mots(t)} mots ; ≤ {lim} pour le style {s}"))
        if t.count("*") > 2:
            v.append(("textes", f"« {t} » : un seul mot d'accent *mot*"))
        mini = 0.3 * mots(t) + 0.5
        if s != "prepa" and d < mini - 0.05:
            v.append(("lecture", f"« {t} » dure {d} s ; temps de lecture ≥ {mini:.1f} s"))
        if x.get("debut", 0) + d > tp + 0.05:
            v.append(("lecture", f"« {t} » déborde sur le carton (fin {x.get('debut', 0) + d:.1f} s > {tp:.1f} s)"))
        if i and s != "prepa" and tx[i - 1].get("style") != "prepa" and x.get("debut", 0) < tx[i - 1].get("debut", 0) + tx[i - 1].get("duree", 0) - 0.05:
            v.append(("lecture", f"« {t} » chevauche « {tx[i - 1].get('texte')} »"))
    nar = sorted(f.get("narration") or [], key=lambda x: x.get("debut", 0))
    if attendu == "narration":
        if len(nar) < 4:
            v.append(("narration", f"{len(nar)} phrases de narration ; attendu au moins 4"))
        n_ass = sum(1 for x in nar if x.get("role") == "assistant")
        if n_ass > (1 if brief == "opsys" else 0):
            v.append(("narration", f"{n_ass} répliques d'assistant ; autorisé : {1 if brief == 'opsys' else 0}"))
        for i, x in enumerate(nar):
            dmin = mots(x.get("texte", "")) / 2.9
            fin_x = x.get("debut", 0) + dmin
            if i + 1 < len(nar) and fin_x > nar[i + 1].get("debut", 0) + 0.05:
                v.append(("narration", f"{x.get('id')} : ≈ {dmin:.1f} s de parole à 2,9 mots/s, chevauche {nar[i + 1].get('id')} (début {nar[i + 1].get('debut')} s)"))
            if fin_x > tot - 0.3:
                v.append(("narration", f"{x.get('id')} finit après le film ({fin_x:.1f} s > {tot:.1f} s)"))
        if nar and nar[0].get("debut", 9) > 3.0 and not any(x.get("debut", 9) < 3.0 for x in tx):
            v.append(("accroche", "rien n'est dit ni écrit avant 3 s : l'accroche doit arriver avant 3 s"))
    elif nar:
        v.append(("narration", "le brief interdit la narration : « narration » doit être vide"))
    if attendu == "texte" and not any(x.get("debut", 9) < 3.0 for x in tx):
        v.append(("accroche", "aucun texte avant 3 s : l'accroche doit arriver avant 3 s"))
    if not any(x.get("debut", 9) < 5.0 for x in tx + nar):
        v.append(("accroche", "rien ne nomme ni ne montre le produit en mots avant 5 s"))
    if brief == "opsys" and not any(x.get("style") == "prepa" and "vision" in str(x.get("texte", "")).lower() for x in tx):
        v.append(("textes", "OPSYS-AI est un film de vision : un texte style prepa « Vision · en développement » est obligatoire"))
    copie = " ".join([str(x.get("texte", "")) for x in tx + nar] + [str(fin.get(k, "")) for k in ("slogan", "sous_titre", "mentions")]).lower()
    for m in INTERDITS_COPIE:
        if m in copie:
            v.append(("interdits", f"« {m} » interdit dans la copie (affirmation invérifiable, marque tierce ou tic d'écriture)"))
    if re.search(r"\b\d{2,}\s*(%|\$|heures|h économisées|clients)", copie):
        v.append(("interdits", "chiffre non prouvable dans la copie"))
    mu = f.get("musique") or {}
    if not mu.get("description") or not mu.get("sections"):
        v.append(("musique", "musique : description et sections obligatoires"))
    for k in ("concept", "accroche", "produit_evident"):
        if not f.get(k):
            v.append(("concept", f"« {k} » manquant"))
    return v


# ------------------------------------------------------------------------------------------------------ réparations code
def reparer_code(f, brief):
    """Réparations mécaniques après la réparation par le modèle : bornes de durée, durée totale, temps de lecture,
    chevauchements, narration recalée. Chaque réparation est journalisée."""
    j = []
    plans = f["plans"]
    for p in plans:
        d0 = p.get("duree", 2.5)
        p["duree"] = round(min(5.0, max(1.0, float(d0 or 2.5))), 2)
        if p["duree"] != d0:
            j.append(f"{p.get('id')} durée {d0} → {p['duree']}")
    fin = f.setdefault("fin", {})
    fin["duree"] = min(5.0, max(3.0, float(fin.get("duree") or 4)))
    tp = sum(p["duree"] for p in plans)
    tot = tp + fin["duree"]
    if not 40 <= tot <= 50:
        cible = min(50, max(40, tot)) - fin["duree"]
        k = cible / tp
        for p in plans:
            p["duree"] = round(min(5.0, max(1.0, p["duree"] * k)), 2)
        j.append(f"durées ×{k:.2f} (total {tot:.1f} → {sum(p['duree'] for p in plans) + fin['duree']:.1f} s)")
        tp = sum(p["duree"] for p in plans)
    tx = sorted([x for x in f.get("textes") or [] if x.get("style") in STYLES], key=lambda x: x.get("debut", 0))
    garde = []
    for x in tx:
        mini = 0.3 * mots(x["texte"]) + 0.5
        if x.get("style") != "prepa" and x.get("duree", 0) < mini:
            j.append(f"« {x['texte'][:25]} » {x.get('duree')} → {mini:.1f} s")
            x["duree"] = round(mini, 2)
        x["debut"] = min(x.get("debut", 0), max(0, tp - x["duree"]))
        prec = next((g for g in reversed(garde) if g.get("style") != "prepa"), None)
        if x.get("style") != "prepa" and prec and x["debut"] < prec["debut"] + prec["duree"]:
            x["debut"] = round(prec["debut"] + prec["duree"] + 0.1, 2)
            if x["debut"] + x["duree"] > tp:
                j.append(f"« {x['texte'][:25]} » retiré (ne tient plus)")
                continue
        garde.append(x)
    f["textes"] = garde
    return j


# --------------------------------------------------------------------------------------------------------------- appel
def appeler(palier, messages, effort):
    a = PALIERS[palier]
    corps = {"model": a["modele"], "messages": messages, "response_format": {"type": "json_object"}, "max_tokens": 32000,
             "temperature": 0.8, **a["corps"](effort)}
    cle = cles()[a["cle"]]
    for essai in range(4):
        t0 = time.time()
        req = urllib.request.Request(a["url"] + "/chat/completions", data=json.dumps(corps).encode(),
                                     headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                rep = json.loads(r.read())
            return rep, time.time() - t0
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code == 400:
                raise ValueError(f"HTTP 400 {msg}")
            if e.code in (408, 429) or e.code >= 500:
                time.sleep(1.5 * 2 ** essai)
                continue
            raise RuntimeError(f"HTTP {e.code} {msg}")
        except (TimeoutError, urllib.error.URLError):
            time.sleep(1.5 * 2 ** essai)
    raise RuntimeError("appel échoué après 4 tentatives")


def cout(palier, u):
    pe, ps = PALIERS[palier]["prix"]
    c = u.get("cost", u.get("estimated_cost"))
    return float(c) if isinstance(c, (int, float)) else (u.get("prompt_tokens", 0) * pe + u.get("completion_tokens", 0) * ps) / 1e6


def extraire(texte):
    texte = texte.strip()
    if texte.startswith("```"):
        texte = re.sub(r"^```\w*\n|\n```$", "", texte)
    i, k = texte.find("{"), texte.rfind("}")
    return json.loads(texte[i:k + 1])


def ecrire(brief, palier, force=False):
    dos = TRAVAIL / f"{brief}-{palier}"
    if (dos / "film.json").exists() and not force:
        print("déjà écrit :", dos / "film.json")
        return
    dos.mkdir(parents=True, exist_ok=True)
    systeme = (ICI / "prompt-auteur.md").read_text()
    texte_brief = (ICI.parent / "briefs-v2" / f"{brief}.md").read_text()
    msgs = [{"role": "system", "content": systeme}, {"role": "user", "content": texte_brief}]
    journal = {"brief": brief, "palier": palier, "modele": PALIERS[palier]["modele"], "appels": [], "reparations_modele": [],
               "reparations_code": [], "effort_essais": []}
    effort, rep, sec = None, None, 0
    for e in PALIERS[palier]["efforts"]:
        try:
            rep, sec = appeler(palier, msgs, e)
            effort = e
            break
        except ValueError as err:
            journal["effort_essais"].append({"effort": e, "refus": str(err)[:200]})
    if rep is None:
        raise SystemExit("aucun effort accepté")
    journal["effort"] = effort or "défaut du fournisseur"

    def noter(rep, sec, etape):
        u = rep.get("usage", {})
        journal["appels"].append({"etape": etape, "entree": u.get("prompt_tokens", 0), "sortie": u.get("completion_tokens", 0),
                                  "raisonnement": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                                  "usd": round(cout(palier, u), 6), "cout_rapporte": "cost" in u or "estimated_cost" in u,
                                  "latence_s": round(sec, 1), "fournisseur": rep.get("provider")})
    noter(rep, sec, "auteur")
    contenu = rep["choices"][0]["message"]["content"]
    try:
        film = extraire(contenu)
    except Exception:
        film = {}
    deja = set()
    for tour in range(3):
        viol = valider(film, brief) if film else [("json", "réponse non JSON")]
        nouvelles = [x for x in viol if x[0] not in deja]
        journal.setdefault("violations", []).append([f"{c} : {m}" for c, m in viol])
        if not nouvelles:
            break
        deja |= {c for c, _ in nouvelles}
        msgs += [{"role": "assistant", "content": contenu},
                 {"role": "user", "content": "Le contrôle automatique a trouvé ces violations. Corrige-les et renvoie le film complet "
                  "(même JSON, rien d'autre) sans rien changer d'autre :\n- " + "\n- ".join(m for _, m in nouvelles)}]
        journal["reparations_modele"].append([m for _, m in nouvelles])
        rep, sec = appeler(palier, msgs, effort)
        noter(rep, sec, f"reparation{tour + 1}")
        contenu = rep["choices"][0]["message"]["content"]
        try:
            film = extraire(contenu)
        except Exception:
            pass
    journal["reparations_code"] = reparer_code(film, brief)
    journal["violations_finales"] = [f"{c} : {m}" for c, m in valider(film, brief)]
    usd = sum(a["usd"] for a in journal["appels"])
    journal.update({"usd": round(usd, 6), "credits_client": round(usd * MARGE * USD_CAD * 100, 3),
                    "jetons_entree": sum(a["entree"] for a in journal["appels"]), "jetons_sortie": sum(a["sortie"] for a in journal["appels"]),
                    "latence_s": round(sum(a["latence_s"] for a in journal["appels"]), 1)})
    (dos / "film.json").write_text(json.dumps(film, ensure_ascii=False, indent=1))
    (dos / "auteur.json").write_text(json.dumps(journal, ensure_ascii=False, indent=1))
    print(json.dumps({k: journal[k] for k in ("brief", "palier", "effort", "usd", "credits_client", "jetons_entree", "jetons_sortie",
                                              "latence_s", "violations_finales")}, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "valider":
        f = json.loads(Path(sys.argv[2]).read_text())
        for c, m in valider(f, sys.argv[3]):
            print(f"✗ {c} : {m}")
    else:
        ecrire(sys.argv[1], sys.argv[2], "--force" in sys.argv)
