#!/usr/bin/env python3
"""Agrège les notes JSON : tableau compact + statistiques + extraits pour la synthèse.
Usage : agreger.py <dossier-notes> <listes.txt...>"""
import glob, json, statistics as st, sys

d = sys.argv[1]
marques = {}
for liste in sys.argv[2:]:
    for l in open(liste):
        p = l.rstrip("\n").split("\t")
        if len(p) >= 2:
            marques[p[0]] = p[1]
marques.setdefault("9Pbg-_ptBcE", "Higgsfield")
marques.setdefault("5fuQnUuu1BM", "Higgsfield")
lignes, regles, accroches, voix, fins, musiques = [], [], [], [], [], []
for f in sorted(glob.glob(d + "/*.json")):
    try:
        j = json.load(open(f))
    except Exception:
        continue
    if "meta" not in j:
        continue
    m, me, a = j["meta"], j["mesures"], j.get("analyse", {})
    if "brut" in a or m["id"] not in marques:
        continue
    mu = a.get("musique", {}) or {}
    vo = a.get("voix", {}) or {}
    lignes.append({
        "id": m["id"], "marque": marques.get(m["id"], "?"), "titre": (m.get("title") or "")[:60],
        "date": m.get("upload_date"), "vues": m.get("view_count"), "duree": me["duree_s"],
        "plans": me["plans"], "s_plan": me["duree_moyenne_plan_s"], "plans_est": a.get("nb_plans_estime"),
        "lufs": me.get("lufs"), "lra": me.get("lra"), "bpm": mu.get("tempo_bpm_estime"), "energie": mu.get("energie_1_10"),
        "voix": vo.get("presence"), "note": a.get("note_spectaculaire_10"), "rythme": (a.get("rythme_percu") or "")[:12],
    })
    regles += [f"[{m['id']}] {r}" for r in a.get("regles_a_retenir", []) or []]
    accroches.append(f"[{m['id']} {marques.get(m['id'],'?')} note={a.get('note_spectaculaire_10')}] {a.get('accroche_0_2s','')}")
    voix.append(f"[{m['id']}] {vo.get('presence')} | {vo.get('style')} | « {vo.get('exemple_phrase')} »")
    fins.append(f"[{m['id']}] {a.get('fin','')}")
    musiques.append(f"[{m['id']}] {mu.get('genre')} | {mu.get('tempo_bpm_estime')} BPM | énergie {mu.get('energie_1_10')} | {mu.get('evolution')} | synchro : {mu.get('synchro_coupes')}")

lignes.sort(key=lambda x: (-(x["note"] or 0), x["marque"]))
print("| # | Marque | Vidéo (id) | Date | Vues | Durée s | Plans | s/plan | BPM | Énergie | Voix | LUFS | Note |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, l in enumerate(lignes, 1):
    print(f"| {i} | {l['marque']} | [{l['titre'].replace('|','/')}](https://youtu.be/{l['id']}) | {l['date']} | {l['vues']} | {l['duree']:.0f} | {l['plans']} ({l['plans_est']}) | {l['s_plan']} | {l['bpm']} | {l['energie']} | {l['voix']} | {l['lufs']} | {l['note']} |")


def med(k, sel=lignes):
    v = [x[k] for x in sel if isinstance(x[k], (int, float)) and x[k]]
    return (round(st.median(v), 2), len(v)) if v else (None, 0)


print("\nSTATS n=", len(lignes))
for k in ("duree", "s_plan", "bpm", "energie", "lufs", "lra", "note"):
    print(k, "médiane", med(k))
top = [x for x in lignes if (x["note"] or 0) >= 8]
print("TOP (note>=8) n=", len(top), {k: med(k, top) for k in ("s_plan", "bpm", "energie", "duree")})
bas = [x for x in lignes if (x["note"] or 0) <= 6]
print("BAS (note<=6) n=", len(bas), {k: med(k, bas) for k in ("s_plan", "bpm", "energie", "duree")})
from collections import Counter
print("voix", Counter(x["voix"] for x in lignes))
for nom, lst in (("REGLES", regles), ("ACCROCHES", accroches), ("VOIX", voix), ("FINS", fins), ("MUSIQUES", musiques)):
    with open(f"{d}/_{nom}.txt", "w") as f:
        f.write("\n".join(lst))
