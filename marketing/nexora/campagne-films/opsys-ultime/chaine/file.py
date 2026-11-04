"""File de tournage H3 commune aux quatre équipes : les plans sont entrelacés (un plan de chaque équipe à tour de rôle) pour
que personne n'attende plus qu'un autre ; jamais plus de `--max-file` de nos rendus en attente dans ComfyUI (la 5090 est
partagée avec un autre film : sa file passe entre les nôtres).

  python3 file.py plans    [--equipes opus,deepseek,muse,gemini] [--format 16:9|9:16] [--max-file 4] [--seulement p01,p02]
  python3 file.py reprises [--equipes …]      lit equipes/<e>/REVISION.json → {"reprises": [{"plan", "prompt"?, "graine"?, "refs"?}]}
Chaque spec est construite au moment de la soumission (la prise de voix et la dernière image d'un plan précédent doivent exister).
"""
import argparse
import json
import threading
import time
from pathlib import Path

import h3
import tourner as T

VERROU = threading.Lock()


def a_faire(eq, fmt, seulement=None):
    D = T.dossier(eq)
    out = []
    for p in D["plans"]:
        if p.get("format", "16:9") != fmt:
            continue
        if seulement and p["id"] not in seulement:
            continue
        if list((T.TRAVAIL / eq / "plans").glob(f"{p['id']}-r*.mp4")):
            continue
        out.append((eq, p, 1))
    return out


def reprises(eq):
    f = T.RACINE / "equipes" / eq / "REVISION.json"
    if not f.exists():
        return []
    R = json.loads(f.read_text())
    D = T.dossier(eq)
    out = []
    for r in R.get("reprises", []):
        p = dict(next(q for q in D["plans"] if q["id"] == r["plan"]))
        for k in ("prompt", "graine", "refs", "images", "premiere", "recette"):
            if r.get(k) is not None:
                p[k] = r[k]
        n = len(list((T.TRAVAIL / eq / "plans").glob(f"{p['id']}-r*.mp4"))) + 1
        if (T.TRAVAIL / eq / "plans" / f"{p['id']}-r{n}.mp4").exists():
            continue
        out.append((eq, p, n))
    return out


def trouver_dans_comfy(s):
    """Identifiant ComfyUI d'un travail déjà soumis pour ce plan (file d'attente, en cours, ou historique récent), sinon None."""
    pref = f"opsys-ultime/{s['equipe']}/{s['nom']}"
    try:
        q = json.loads(h3.http(f"{h3.H3_COMFY}/queue"))
        for it in q.get("queue_running", []) + q.get("queue_pending", []):
            if json.dumps(it[2].get("save", {}).get("inputs", {})).find(f'"{pref}"') >= 0:
                return it[1]
        hist = json.loads(h3.http(f"{h3.H3_COMFY}/history?max_items=200", timeout=120))
        for pid, h in hist.items():
            if json.dumps(h.get("prompt", [None, None, {}])[2].get("save", {}).get("inputs", {})).find(f'"{pref}"') >= 0 \
                    and h.get("status", {}).get("completed"):
                return pid
    except Exception:
        return None
    return None


def entrelacer(listes):
    out = []
    while any(listes):
        for l in listes:
            if l:
                out.append(l.pop(0))
    return out


def travailler(tache, max_file):
    eq, p, prise = tache
    D = T.dossier(eq)
    # dépendance « fin:pXX » : attendre que le plan source existe
    pm = p.get("premiere") or ""
    if pm.startswith("fin:"):
        while T.plan_retenu(eq, pm[4:]) is None:
            time.sleep(15)
    # prérequis : fiches des références, image clé, prise de voix ancrée (attente, jamais d'échec silencieux)
    t_att = time.time()
    while True:
        manque = []
        for r in (p.get("refs") or []) if p.get("recette", "h3-max") == "h3-max" else []:
            try:
                T.images_ref(eq, r)
            except FileNotFoundError:
                manque.append(f"fiche {r}")
        if pm and not pm.startswith("fin:") and not (T.TRAVAIL / eq / "cles" / f"{pm}.png").exists():
            manque.append(f"clé {pm}")
        if p.get("parole"):
            try:
                T.prise_voix(eq, p["parole"])
            except FileNotFoundError:
                manque.append(f"voix {p['parole']}")
        if not manque:
            break
        if time.time() - t_att > 4 * 3600:
            res = {"equipe": eq, "nom": f"{p['id']}-r{prise}", "erreur": "prérequis absents : " + ", ".join(manque)}
            print(json.dumps(res, ensure_ascii=False), flush=True)
            return res
        time.sleep(30)
    try:
        s = T.spec_plan(eq, D, p, prise)
    except Exception as e:
        res = {"equipe": eq, "nom": f"{p['id']}-r{prise}", "erreur": f"spec : {e}"}
        print(json.dumps(res, ensure_ascii=False), flush=True)
        return res
    # reprise après redémarrage : ce plan est peut-être déjà dans la file ComfyUI ou déjà rendu (historique)
    deja = trouver_dans_comfy(s)
    if deja:
        comfy, pid, t0 = h3.H3_COMFY, deja, time.time()
    else:
      with VERROU:  # une soumission à la fois, dans l'ordre entrelacé
        comfy, pid, t0 = h3.soumettre(s, max_file)
    try:
        res = h3.attendre(s, comfy, pid, t0)
    except Exception as e:
        res = {"equipe": eq, "nom": s["nom"], "erreur": str(e)[:1500]}
    res["unites"] = s["_unites"]
    res["format"] = s["_format"]
    h3.journaliser(s, res)
    print(json.dumps({k: res.get(k) for k in ("equipe", "nom", "secondesMoteur", "erreur", "fin")}, ensure_ascii=False), flush=True)
    return res


def main():
    a = argparse.ArgumentParser()
    a.add_argument("cmd")
    a.add_argument("--equipes", default="opus,deepseek,muse,gemini")
    a.add_argument("--format", default="16:9")
    a.add_argument("--max-file", type=int, default=4)
    a.add_argument("--seulement", default="")
    o = a.parse_args()
    eqs = [e for e in o.equipes.split(",") if (T.RACINE / "equipes" / e / "dossier.json").exists()]
    seul = set(filter(None, o.seulement.split(",")))
    if o.cmd == "plans":
        taches = entrelacer([a_faire(e, o.format, seul) for e in eqs])
    else:
        taches = entrelacer([reprises(e) for e in eqs])
    print(f"{len(taches)} rendus à faire : " + ", ".join(f"{e}={sum(1 for t in taches if t[0] == e)}" for e in eqs), flush=True)
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(max_workers=o.max_file) as ex:
        futs = []
        for t in taches:
            futs.append(ex.submit(travailler, t, o.max_file))
            time.sleep(0.5)
        for f in futs:
            f.result()


if __name__ == "__main__":
    main()
