"""Mesures comparables des quatre films (pour COMPARAISON.md) : durée, plans montés, secondes par plan, part de narration,
dialogues, sonie, crête, coût en jetons (journal de la passerelle des sous-agents), temps GPU (journaux des rendus).

  python3 comparer.py [equipe …]   → JSON sur la sortie standard et <travail>/comparaison.json
"""
import json
import statistics
import subprocess
import sys
from pathlib import Path

import tourner as T

USAGE = Path.home() / ".local/share/nexora-sous-agents/usage.jsonl"
ALIAS = {"deepseek": ("eco-deepseek",), "muse": ("eco-muse",), "gemini": ("eco-gemini", "eco-gemini-eleve")}


def sonie(f):
    r = subprocess.run([T.FF, "-hide_banner", "-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    i = [l for l in r.splitlines() if l.strip().startswith("I:")]
    p = [l for l in r.splitlines() if l.strip().startswith("Peak:")]
    return (float(i[-1].split()[1]) if i else None), (float(p[-1].split()[1]) if p else None)


def jetons(eq):
    if eq not in ALIAS or not USAGE.exists():
        return None
    tot = {"req": 0, "in": 0, "out": 0, "usd": 0.0}
    for l in USAGE.read_text().splitlines():
        try:
            r = json.loads(l)
        except ValueError:
            continue
        run = r.get("run") or ""
        if r.get("alias") in ALIAS[eq] and run.startswith("ou-"):
            tot["req"] += 1
            tot["in"] += r.get("in") or 0
            tot["out"] += r.get("out") or 0
            tot["usd"] += r.get("cost") or 0
    tot["usd"] = round(tot["usd"], 4)
    return tot


def gpu(eq):
    out = {"5090_s": 0.0, "gb10_s": 0.0, "rendus_h3": 0, "images": 0, "erreurs": 0}
    for sous in ("plans", "fiches", "cles"):
        j = T.TRAVAIL / eq / sous / "rendus.jsonl"
        if not j.exists():
            continue
        for l in j.read_text().splitlines():
            r = json.loads(l)
            if r.get("erreur"):
                out["erreurs"] += 1
                continue
            s = r.get("secondesMoteur") or 0
            if r.get("type", "h3") == "h3":
                out["5090_s"] += s
                out["rendus_h3"] += 1
            else:
                out["gb10_s"] += s
                out["images"] += 1
    out["5090_min"] = round(out.pop("5090_s") / 60, 1)
    out["gb10_min"] = round(out.pop("gb10_s") / 60, 1)
    return out


def film(eq, version):
    D = T.dossier(eq)
    P = D["montage"].get(version)
    f = T.TRAVAIL / eq / "montage" / f"{eq}-{version}.mp4"
    if not P or not f.exists():
        return None
    durees = [c["duree_f"] / 24 for c in P["video"]]
    roles = {v["id"]: v.get("role", "") for v in D.get("voix", [])}
    narr = sum(v["duree_f"] for v in P.get("audio", {}).get("voix", []) if "narr" in roles.get(v["src"], "").lower()) / 24
    dial = [v for v in P.get("audio", {}).get("voix", []) if "narr" not in roles.get(v["src"], "").lower()]
    lufs, crete = sonie(f)
    tot = T.duree(f)
    return {"fichier": str(f), "duree_s": round(tot, 1), "plans_montes": len(durees), "s_par_plan_mediane": round(statistics.median(durees), 2),
            "s_par_plan_moyenne": round(sum(durees) / len(durees), 2), "plan_le_plus_long_s": round(max(durees), 1),
            "narration_s": round(narr, 1), "narration_pct": round(100 * narr / tot, 1), "repliques_dialogue": len(dial),
            "lufs": lufs, "crete_dbfs": crete}


def main(eqs):
    res = {}
    for eq in eqs:
        res[eq] = {"long": film(eq, "long"), "court": film(eq, "court"), "vertical": film(eq, "vertical"), "gpu": gpu(eq), "jetons": jetons(eq),
                   "budget": T.etat(eq)}
    (T.TRAVAIL / "comparaison.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:] or ["opus", "deepseek", "muse", "gemini"])
