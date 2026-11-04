"""Matériel de la ronde de révision d'une équipe : planches de ses plans, rapport de ses voix et de ses musiques, budget.

  python3 revue.py <equipe> [--sortie dossier]   → <sortie>/planche-plans-<n>.jpg (16 plans par planche), REVUE.md
Les défauts relevés à l'œil par le producteur sont lus dans <travail>/<equipe>/defauts.json : {"p05-r1": "texte dans l'image", …}.
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import tourner as T

POLICE = Path.home() / "Desktop/NexoraSite/web/src/fonts/jetbrains-mono-latin-wght-normal.woff2"


def vignettes(f, n=3, largeur=420):
    d = T.duree(f)
    out = []
    for k in range(n):
        t = d * (0.12 + 0.76 * k / max(1, n - 1))
        raw = subprocess.run([T.FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(f), "-frames:v", "1", "-vf", f"scale={largeur}:-2",
                              "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        from io import BytesIO
        out.append(Image.open(BytesIO(raw)).convert("RGB"))
    return out, d


def planches(eq, sortie, journal):
    d = T.TRAVAIL / eq / "plans"
    fichiers = sorted(d.glob("*.mp4"), key=lambda f: (f.stem.split("-r")[0], int(f.stem.rsplit("-r", 1)[1])))
    font = ImageFont.truetype(str(POLICE), 18)
    pages, page = [], []
    for f in fichiers:
        page.append(f)
        if len(page) == 12:
            pages.append(page)
            page = []
    if page:
        pages.append(page)
    noms = []
    for i, page in enumerate(pages, 1):
        lignes = []
        for f in page:
            ims, du = vignettes(f)
            w = sum(im.width for im in ims) + 8 * (len(ims) - 1)
            h = max(im.height for im in ims)
            L = Image.new("RGB", (w + 300, h + 8), (14, 14, 18))
            x = 300
            for im in ims:
                L.paste(im, (x, 4))
                x += im.width + 8
            dr = ImageDraw.Draw(L)
            j = journal.get(f.stem, {})
            dr.text((12, 10), f.stem, font=ImageFont.truetype(str(POLICE), 26), fill=(246, 244, 238))
            dr.text((12, 50), f"{du:.1f} s", font=font, fill=(160, 160, 172))
            if j.get("secondesMoteur"):
                dr.text((12, 76), f"GPU {j['secondesMoteur']:.0f} s", font=font, fill=(160, 160, 172))
            lignes.append(L)
        W = max(l.width for l in lignes)
        H = sum(l.height for l in lignes)
        P = Image.new("RGB", (W, H), (8, 8, 10))
        y = 0
        for l in lignes:
            P.paste(l, (0, y))
            y += l.height
        n = sortie / f"planche-plans-{i}.jpg"
        P.save(n, quality=84)
        noms.append(n)
    return noms


def main():
    a = argparse.ArgumentParser()
    a.add_argument("equipe")
    a.add_argument("--sortie")
    o = a.parse_args()
    eq = o.equipe
    sortie = Path(o.sortie) if o.sortie else T.dossier_travail(eq, "revue")
    sortie.mkdir(parents=True, exist_ok=True)
    journal = {}
    jf = T.TRAVAIL / eq / "plans" / "rendus.jsonl"
    if jf.exists():
        for l in jf.read_text().splitlines():
            r = json.loads(l)
            journal[r["nom"]] = r
    defauts = {}
    df = T.TRAVAIL / eq / "defauts.json"
    if df.exists():
        defauts = json.loads(df.read_text())
    noms = planches(eq, sortie, journal)
    D = T.dossier(eq)
    u = T.etat(eq)
    gpu = sum((r.get("secondesMoteur") or 0) for r in journal.values())
    t = [f"# Ronde de révision : équipe {eq}", "",
         f"Budget consommé : {u['16:9']} unités 16:9 sur 40, {u['9:16']} unités 9:16 sur 6 ; reprises disponibles : 8 unités. "
         f"Temps GPU (5090) : {gpu / 60:.1f} min.", "",
         "## Plans tournés (planches : " + ", ".join(n.name for n in noms) + ")", "",
         "Trois images par plan (12 %, 50 %, 88 % de la durée). Défauts relevés à l'œil par le producteur :", "",
         "| prise | durée | GPU | défauts relevés |", "|---|---|---|---|"]
    for nom, r in sorted(journal.items()):
        t.append(f"| {nom} | {r.get('images', 0) / 24:.1f} s | {r.get('secondesMoteur') or '–'} s | {defauts.get(nom, r.get('erreur', '') or 'aucun relevé')} |")
    t += ["", "## Voix", "", "Oreille de machine (Gemini 4 Argon, sur 10 : accent québécois, énergie, naturel, clarté) ; EMR = erreur de mots Whisper.", "",
          "| réplique | prise | durée | c/s | relief | EMR | oreille | transcription | avis |", "|---|---|---|---|---|---|---|---|---|"]
    for j in sorted((T.TRAVAIL / eq / "voix").glob("*.json")):
        m = json.loads(j.read_text())
        o2 = (m.get("oreille") or {})
        mo = o2.get("moyennes") or {}
        av = " / ".join(p.get("commentaire", "") for p in o2.get("passes", [])[:1])
        t.append(f"| {m['id']} | {m['prise']} | {m['utile_s']} s | {m.get('cps')} | {m.get('relief_demitons')} | {m.get('emr')} | "
                 f"{mo.get('accent_quebecois', '–')}/{mo.get('energie', '–')}/{mo.get('naturel', '–')}/{mo.get('clarte', '–')} | {m.get('transcription', '')} | {av} |")
    t += ["", "## Musiques (grille mesurée)", ""]
    for j in sorted((T.TRAVAIL / eq / "musique").glob("lyria-*.json")):
        g = json.loads(j.read_text())
        t.append(f"- `{j.stem}` : {g['duree_s']} s, **{g['bpm']} BPM mesurés** (temps {g['temps_s']} s, phase {g['phase_s']} s), "
                 f"sauts d'énergie à {', '.join(str(x) for x in g['sauts_energie_s'][:8])} s")
    m = T.TRAVAIL / eq / "montage"
    t += ["", "## Premier montage", ""] + [f"- `{f.name}`" for f in sorted(m.glob("*.mp4"))] if m.exists() else []
    t += ["", "## Ce que tu peux décider (une seule ronde)", "",
          "Écris `equipes/<equipe>/REVISION.json` : `{\"reprises\": [{\"plan\": \"p05\", \"prompt\": \"…\" (facultatif), \"graine\": 1234 (facultatif)}],",
          "\"voix\": {\"l01\": 2} (prise retenue), \"voix_reprises\": [{\"id\": \"l03\", \"texte\": \"…\", \"direction\": \"…\", \"vitesse\": 1.1, \"voix\": \"…\"}],",
          "\"musique\": 1, \"plans\": {\"p05\": \"p05-r2.mp4\"} (prise retenue après reprise : laisser au producteur)}` ;",
          "reprises ≤ 8 unités en tout. Puis corrige ton `dossier.json` (EditPlan révisés : durées réelles, calage sur la musique mesurée).", ""]
    (sortie / "REVUE.md").write_text("\n".join(t))
    print(sortie / "REVUE.md", [str(n) for n in noms])


if __name__ == "__main__":
    main()
