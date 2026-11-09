"""Tournage d'un dossier créatif (`equipes/<equipe>/dossier.json`) avec la chaîne commune. Idempotent : ce qui existe est sauté.

  python3 tourner.py <equipe> fiches            fiches Qwen-Image (personnages : 2 références découpées ; lieux/objets : 1)
  python3 tourner.py <equipe> cles              images clés Qwen-Image
  python3 tourner.py <equipe> voix [ids]        répliques (toutes les prises demandées), mesures et oreille de machine
  python3 tourner.py <equipe> musique [n]       génération(s) Lyria 3 Pro
  python3 tourner.py <equipe> specs [ids]       écrit les specs H3 (plans) sans rien lancer : contrôle
  python3 tourner.py <equipe> etat              budget consommé
  python3 file.py …                             tournage H3 entrelacé des quatre équipes (voir file.py)

Conventions de prompt (BRIEF §4.1) : dans un prompt de plan, `@id` désigne une référence de `refs` ; la chaîne écrit les balises
`<Picture n>` dans l'ordre et ajoute les lignes `subject_definitions`. Un plan `parole` reçoit `<Audio 1>` (la prise choisie).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent  # opsys-ultime/
TRAVAIL = Path.home() / "nexora-creative-data/work/opsys-ultime"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FP = FF[:-6] + "ffprobe"
sys.path.insert(0, str(ICI))
import h3  # noqa: E402

GRILLE_IMAGES = [124 + 17 * k for k in range(8)]  # 124 … 243
TAILLES = {"16:9": (1344, 768), "9:16": (768, 1344)}
TAILLES_IMG = {"16:9": (1664, 928), "9:16": (928, 1664)}

FICHE_PERSO = ("Character reference sheet, photorealistic high-end photograph, plain flat mid-grey studio background, soft even studio "
               "lighting. Left half of the image: the same person standing, full body, front view, arms relaxed. Right half of the image: "
               "close-up portrait of the same person's face and shoulders, front view, calm expression. {d} Plain clothing with no logo. "
               "No text, no letters, no numbers, no watermark anywhere.")
FICHE_LIEU = ("{d} Photorealistic cinematic wide establishing photograph, large-format camera, natural light, rich detail. "
              "No text, no letters, no logos, no watermark anywhere.")


def dossier(equipe):
    return json.loads((RACINE / "equipes" / equipe / "dossier.json").read_text())


def dossier_travail(equipe, *sous):
    d = TRAVAIL.joinpath(equipe, *sous)
    d.mkdir(parents=True, exist_ok=True)
    return d


def choix(equipe):
    f = dossier_travail(equipe) / "choix.json"
    return json.loads(f.read_text()) if f.exists() else {"plans": {}, "voix": {}, "musique": None}


def ecrire_choix(equipe, c):
    (dossier_travail(equipe) / "choix.json").write_text(json.dumps(c, ensure_ascii=False, indent=1))


# ------------------------------------------------------------------------------------------------------------ fiches
def fiches(equipe):
    D = dossier(equipe)
    out = dossier_travail(equipe, "fiches")
    specs = []
    for p in D.get("personnages", []):
        if not (out / f"{p['id']}-a.png").exists():
            specs.append({"type": "image", "equipe": equipe, "nom": f"fiche-{p['id']}", "prompt": FICHE_PERSO.format(d=p["fiche"]),
                          "largeur": 1792, "hauteur": 1024, "graine": p.get("graine", 11), "sortie": str(out), "_perso": p["id"]})
    for p in D.get("lieux", []) + D.get("objets", []):
        if not (out / f"{p['id']}.png").exists():
            specs.append({"type": "image", "equipe": equipe, "nom": f"fiche-{p['id']}", "prompt": FICHE_LIEU.format(d=p["fiche"]),
                          "largeur": 1664, "hauteur": 928, "graine": p.get("graine", 12), "sortie": str(out), "_lieu": p["id"]})
    for r in h3.rendre_tous(specs, max_file=3):
        if r.get("erreur"):
            continue
        s = next(x for x in specs if x["nom"] == r["nom"])
        f = Path(r["fichier"])
        if s.get("_perso"):
            from PIL import Image
            im = Image.open(f).convert("RGB")
            W, H = im.size
            im.crop((0, 0, W // 2, H)).save(out / f"{s['_perso']}-a.png")
            im.crop((W // 2, 0, W, H)).save(out / f"{s['_perso']}-b.png")
            f.rename(out / f"{s['_perso']}-fiche.png")
        else:
            f.rename(out / f"{s['_lieu']}.png")


def images_ref(equipe, rid):
    d = TRAVAIL / equipe / "fiches"
    if (d / f"{rid}-a.png").exists():
        return [str(d / f"{rid}-a.png"), str(d / f"{rid}-b.png")]
    if (d / f"{rid}.png").exists():
        return [str(d / f"{rid}.png")]
    raise FileNotFoundError(f"fiche absente : {rid}")


def nom_ref(D, rid):
    for p in D.get("personnages", []):
        if p["id"] == rid:
            return f"{p.get('nom', rid)} ({p.get('role', 'character')})", True
    for p in D.get("lieux", []) + D.get("objets", []):
        if p["id"] == rid:
            return p.get("nom", rid), False
    return rid, False


# -------------------------------------------------------------------------------------------------------------- clés
def cles(equipe):
    D = dossier(equipe)
    out = dossier_travail(equipe, "cles")
    specs = []
    for k in D.get("cles", []):
        if not (out / f"{k['id']}.png").exists():
            w, h = TAILLES_IMG[k.get("format", "16:9")]
            pr = k["prompt"] if "no text" in k["prompt"].lower() else k["prompt"] + " No text, no letters, no logos anywhere."
            specs.append({"type": "image", "equipe": equipe, "nom": k["id"], "prompt": pr, "largeur": w, "hauteur": h,
                          "graine": k.get("graine", 21), "sortie": str(out)})
    h3.rendre_tous(specs, max_file=3)


# -------------------------------------------------------------------------------------------------------------- voix
def lire_palette(palette):
    if not palette:
        raise ValueError('Palette explicite requise (--palette ou OPSYS_PALETTE).')
    chemin_palette = Path(palette)
    if chemin_palette.suffix.lower() != '.json' or chemin_palette.is_symlink() or not chemin_palette.is_file():
        raise ValueError('Palette JSON explicite et régulière requise.')
    return json.loads(chemin_palette.read_text())['voix']


def voix(equipe, ids=None, *, palette):
    """Génère seulement des rôles Eleven v4 depuis une palette fournie explicitement."""
    import voix as V
    D = dossier(equipe)
    pal = lire_palette(palette)
    for l in D.get("voix", []):
        if ids and l["id"] not in ids:
            continue
        p = pal.get(l["voix"])
        if not p:
            raise ValueError(f"Voix absente de la palette : {l['voix']}")
        vitesse = l.get("vitesse", p.get("vitesse", 1.0))
        direction = l.get("direction") or p.get("direction", "")
        for k in range(1, int(l.get("prises", 1)) + 1):
            m = V.ligne(equipe, l["id"], p["moteur"], l["texte"], direction, vitesse, k,
                        langue=l.get("langue"), racine=TRAVAIL, ffmpeg=FF)
            print(l["id"], k, m["statut_humain"], flush=True)


def prise_voix(equipe, lid, *, palette=None, autoriser_factice=False):
    """Lit seulement les nouveaux reçus Eleven v4 liés par SHA ; aucune note inventée."""
    import voix as V
    V._identifiant(equipe, 'Équipe'); V._identifiant(lid, 'Réplique')
    lignes = [ligne for ligne in dossier(equipe)['voix'] if ligne.get('id') == lid]
    if len(lignes) != 1 or lignes[0].get('langue') not in ('fr', 'en'):
        raise ValueError(f'Langue explicite et unique requise pour {lid}.')
    langue = lignes[0]['langue']
    ligne = lignes[0]
    import os
    pal = lire_palette(palette or os.environ.get('OPSYS_PALETTE'))
    p = pal.get(ligne['voix'])
    if not p:
        raise ValueError(f"Voix absente de la palette : {ligne['voix']}")
    c = choix(equipe)["voix"].get(lid)
    d = TRAVAIL / equipe / "voix" / "eleven4"
    candidats = []
    for j in sorted(d.glob(f"*/*/{lid}-p*.json")):
        if j.is_symlink() or j.parent.is_symlink() or j.parent.parent.is_symlink():
            continue
        m = json.loads(j.read_text())
        if m.get('id') != lid or m.get('equipe') != equipe or m.get('langue') != langue or (c is not None and m.get('prise') != c):
            continue
        try:
            spec = V.contrat(equipe, lid, p['moteur'], ligne['texte'], ligne.get('direction') or p.get('direction', ''),
                             ligne.get('vitesse', p.get('vitesse', 1.0)), m['prise'], langue)
            attendu = V.signature(spec, m.get('origine') == 'factice')
        except (KeyError, TypeError, ValueError):
            continue
        if m.get('contrat') == spec and m.get('signature') == attendu and V.verifier_recu(m, j, autoriser_factice):
            candidats.append(Path(m['fichier']))
    if len(candidats) != 1:
        raise ValueError(f"Prise Eleven v4 absente ou ambiguë pour {lid} ; sélection explicite requise.")
    return candidats[0]


def duree(f):
    return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout.strip())


# ----------------------------------------------------------------------------------------------------------- musique
def musique(equipe, n=None):
    import musique as MU
    D = dossier(equipe)
    m = D["musique"]
    prompts = m.get("prompts") or [m["prompt"]]
    a_faire = [int(n)] if n else list(range(1, len(prompts) + 1))
    for i in a_faire:
        if (TRAVAIL / equipe / "musique" / f"lyria-{i}.json").exists():
            continue
        pr = prompts[min(i, len(prompts)) - 1]
        g = MU.composer(equipe, i, pr, m.get("modele", "google/lyria-3-pro-preview"))
        print("musique", i, g["bpm"], g["duree_s"], g["sauts_energie_s"][:6], flush=True)


# ------------------------------------------------------------------------------------------------------------- plans
def derniere_image(video, sortie):
    sortie = Path(sortie)
    cible = sortie
    index = 2
    while cible.exists() or cible.is_symlink():
        cible = sortie.with_name(f"{sortie.stem}-{index}{sortie.suffix}")
        index += 1
    subprocess.run([FF, "-v", "error", "-n", "-sseof", "-0.08", "-i", str(video), "-frames:v", "1", "-update", "1", str(cible)], check=True)
    return cible


def spec_plan(equipe, D, p, prise=1, format_=None):
    fmt = format_ or p.get("format", "16:9")
    w, h = TAILLES[fmt]
    images = int(p.get("images", 124))
    refs = p.get("refs", []) if p.get("recette", "h3-max") == "h3-max" else []
    imgs, defs, k = [], [], 1
    prompt = p["prompt"]
    for rid in refs:
        fs = images_ref(equipe, rid)
        nom, perso = nom_ref(D, rid)
        tags = [f"<Picture {k + i}>" for i in range(len(fs))]
        k += len(fs)
        imgs += fs
        etiquette = " and ".join(tags)
        prompt = re.sub(rf"@{re.escape(rid)}\b", etiquette, prompt)
        if perso and len(fs) == 2:
            defs.append(f"{tags[0]} and {tags[1]} show {nom}: full body and face close-up of the same person (identity, face, hair and clothing must match).")
        else:
            defs.append(f"{etiquette} shows {nom} (keep its look).")
    if len(imgs) > 9:
        raise ValueError(f"{p['id']} : {len(imgs)} images de référence (9 au plus ; un personnage = 2 images)")
    audio = None
    if p.get("parole"):
        audio = prise_voix(equipe, p["parole"])
        besoin = int((duree(audio) + 0.35) * 24)
        images = max(images, next((g for g in GRILLE_IMAGES if g >= besoin), 999))
        if images > 243:
            raise ValueError(f"{p['id']} : réplique de {duree(audio):.1f} s, trop longue pour un plan (≤ 10 s)")
        defs.append("<Audio 1> is the voice that speaks in [Shot 1]; lips and jaw move exactly with it.")
    if images not in GRILLE_IMAGES:
        images = next((g for g in GRILLE_IMAGES if g >= images), 243)
    if defs and "subject_definitions:" not in prompt:
        prompt = "subject_definitions:\n" + "\n".join(defs) + "\n\n" + prompt
    elif defs:
        prompt = prompt.replace("subject_definitions:", "subject_definitions:\n" + "\n".join(defs), 1)
    premiere = None
    pr = p.get("premiere")
    if pr:
        if pr.startswith("fin:"):
            src = plan_retenu(equipe, pr[4:])
            if src is None:
                raise FileNotFoundError(f"{p['id']} : le plan {pr[4:]} doit être tourné avant (enchaînement)")
            premiere = str(derniere_image(src, TRAVAIL / equipe / "cles" / f"fin-{pr[4:]}.png"))
        else:
            premiere = str(TRAVAIL / equipe / "cles" / f"{pr}.png")
    suffixe = "" if fmt == p.get("format", "16:9") else "-v"
    return {"type": "h3", "equipe": equipe, "nom": f"{p['id']}{suffixe}-r{prise}", "recette": p.get("recette", "h3-max"),
            "prompt": prompt, "largeur": w, "hauteur": h, "images": images, "graine": int(p.get("graine", 1000)) + 97 * (prise - 1),
            "refs": imgs, "premiere": premiere, "audio": str(audio) if audio else None, "sortie": str(dossier_travail(equipe, "plans")),
            "_unites": 1 if images <= 124 else 2, "_plan": p["id"], "_format": fmt}


def plan_retenu(equipe, pid, fmt="16:9"):
    c = choix(equipe)["plans"].get(pid if fmt == "16:9" else pid + "-v")
    d = TRAVAIL / equipe / "plans"
    if c:
        return d / c
    suf = "" if fmt == "16:9" else "-v"
    prises = sorted(d.glob(f"{pid}{suf}-r*.mp4"), key=lambda f: int(f.stem.rsplit("-r", 1)[1]))
    return prises[-1] if prises else None


def etat(equipe):
    j = TRAVAIL / equipe / "plans" / "rendus.jsonl"
    u = {"16:9": 0, "9:16": 0, "reprises": 0}
    if j.exists():
        for l in j.read_text().splitlines():
            r = json.loads(l)
            if r.get("erreur"):
                continue
            n = 1 if (r.get("images") or 124) <= 124 else 2
            if "-v-r" in r["nom"]:
                u["9:16"] += n
            elif not r["nom"].endswith("-r1"):
                u["reprises"] += n
            else:
                u["16:9"] += n
    return u


if __name__ == "__main__":
    eq, cmd, *reste = sys.argv[1:]
    if cmd == "fiches":
        fiches(eq)
    elif cmd == "cles":
        cles(eq)
    elif cmd == "voix":
        if len(reste) < 2 or reste[0] != '--palette':
            raise SystemExit('Usage : tourner.py EQUIPE voix --palette CHEMIN [IDS...]')
        voix(eq, set(reste[2:]) or None, palette=reste[1])
    elif cmd == "musique":
        musique(eq, reste[0] if reste else None)
    elif cmd == "specs":
        D = dossier(eq)
        for p in D["plans"]:
            if reste and p["id"] not in reste:
                continue
            try:
                s = spec_plan(eq, D, p)
                print(p["id"], s["recette"], s["images"], "images", len(s["refs"]), "réf.", "audio" if s["audio"] else "")
            except Exception as e:
                print(p["id"], "ERREUR", e)
    elif cmd == "etat":
        print(json.dumps(etat(eq)))
