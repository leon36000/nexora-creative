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


def planche_montage(eq, sortie):
    """Une image toutes les 2 s du premier montage long, avec le temps : pour réviser sans regarder la vidéo."""
    f = T.TRAVAIL / eq / "montage" / f"{eq}-long.mp4"
    if not f.exists():
        f = T.TRAVAIL / eq / "montage" / f"{eq}-long-brouillon.mp4"
    if not f.exists():
        return []
    d = T.duree(f)
    font = ImageFont.truetype(str(POLICE), 20)
    ims = []
    t = 1.0
    while t < d:
        raw = subprocess.run([T.FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(f), "-frames:v", "1", "-vf", "scale=384:-2",
                              "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        from io import BytesIO
        im = Image.open(BytesIO(raw)).convert("RGB")
        ImageDraw.Draw(im).text((8, 6), f"{t:5.1f} s", font=font, fill=(255, 90, 31))
        ims.append(im)
        t += 2.0
    noms = []
    for k in range(0, len(ims), 30):
        lot = ims[k:k + 30]
        w, h = lot[0].size
        P = Image.new("RGB", (w * 5 + 16, h * ((len(lot) + 4) // 5) + 4 * ((len(lot) + 4) // 5)), (8, 8, 10))
        for i, im in enumerate(lot):
            P.paste(im, ((i % 5) * (w + 4), (i // 5) * (h + 4)))
        n = sortie / f"planche-montage-{k // 30 + 1}.jpg"
        P.save(n, quality=82)
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
    noms_m = planche_montage(eq, sortie)
    descr = {}
    dfd = T.TRAVAIL / eq / "descriptions.json"
    if dfd.exists():
        descr = json.loads(dfd.read_text())
    D = T.dossier(eq)
    u = T.etat(eq)
    gpu = sum((r.get("secondesMoteur") or 0) for r in journal.values())
    t = [f"# Ronde de révision : équipe {eq}", "",
         f"Budget consommé : {u['16:9']} unités 16:9 sur 40, {u['9:16']} unités 9:16 sur 6 ; reprises disponibles : 8 unités. "
         f"Temps GPU (5090) : {gpu / 60:.1f} min.", "",
         "## Plans tournés (planches : " + ", ".join(n.name for n in noms) + ")", "",
         "Trois images par plan (12 %, 50 %, 88 % de la durée). Défauts relevés à l'œil par le producteur :", "",
         "Colonne « réel » : juge de machine « réel contre synthèse » (Gemini 4 Argon, 3 images, deux passes) : 10 = indiscernable d'une "
         "vraie prise de vues, 0 = image de synthèse évidente ; « jeu » = look jeu vidéo (10 = très). Description : celle du producteur si "
         "elle existe, sinon celle du juge (marquée « juge : »).", "",
         "| prise | durée | GPU | réel | jeu | ce qu'on voit | défauts relevés |", "|---|---|---|---|---|---|---|"]
    jr = {}
    jrf = T.TRAVAIL / eq / "juge-reel.json"
    if jrf.exists():
        jr = json.loads(jrf.read_text())
    for nom, r in sorted(journal.items()):
        j = jr.get(nom, {})
        mo = j.get("moyennes", {})
        p0 = next((p for p in j.get("passes", []) if "resume" in p), {})
        d_ = descr.get(nom) or (("juge : " + p0.get("resume", "")) if p0 else "")
        dj = ", ".join(p0.get("defauts", [])[:4]) if p0 else ""
        t.append(f"| {nom} | {(r.get('images') or 0) / 24:.1f} s | {r.get('secondesMoteur') or '–'} s | {mo.get('reel', '–')} | {mo.get('look_jeu_video', '–')} | "
                 f"{d_} | {defauts.get(nom, '') or dj or (r.get('erreur', '') or 'aucun relevé')} |")
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
    if noms_m:
        t += ["", "## Premier montage (planches : " + ", ".join(n.name for n in noms_m) + ", une image toutes les 2 s)", ""]
        jm = T.TRAVAIL / "journal-montage.jsonl"
        if jm.exists():
            for l in jm.read_text().splitlines():
                r = json.loads(l)
                if r.get("equipe") == eq:
                    t.append(f"- {Path(r['film']).name} : {r['duree_s']} s, {r['plans']} plans montés, plans manquants : {r.get('manquants') or 'aucun'}")
        for jf in sorted((T.TRAVAIL / eq / "montage").glob("*.juge.json")):
            if "essai-musique" in jf.name:
                continue
            jj = json.loads(jf.read_text())
            t += ["", f"### Juge audio-vidéo sur `{jf.name[:-10]}` (Gemini 4 Argon, film mixé, deux passes)", "",
                  "Notes : " + ", ".join(f"{k} {v}" for k, v in jj.get("moyennes", {}).items())]
            for p in jj.get("passes", [])[:1]:
                t += ["Forces : " + " ; ".join(p.get("forces", [])), "Faiblesses : " + " ; ".join(p.get("faiblesses", [])),
                      "Moments plats : " + " ; ".join(p.get("moments_plats", []))]
        rp = T.TRAVAIL / eq / "montage" / "rapport.md"
        if rp.exists():
            t += ["", rp.read_text()]
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
