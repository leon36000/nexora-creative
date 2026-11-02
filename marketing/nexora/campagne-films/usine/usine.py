"""Usine à films de la campagne : un brief JSON → films finis (16:9 et 9:16, fr et en, versions long/30/15), revue, web, manifeste.

  python3 usine.py <brief.json> [etape ...]
  étapes (dans l'ordre, toutes par défaut) :
    valider     contrôle du brief : sources présentes, coupes sur la grille musicale, temps de lecture, textes traduits,
                mots interdits, « En préparation » affiché. Chaque violation donne l'endroit, la valeur attendue et la
                correction proposée ; l'usine s'arrête s'il en reste.
    plaques     commande du brief (« commandes.plaques » : images clés Qwen puis vidéos H3, recettes h3-max / h3-fast) ;
                rien à faire pour un film fait de captures.
    captures    commande du brief (« commandes.captures », Playwright sur l'application réelle).
    montage     écrit <travail>/montage.json (segments résolus, textes, bruitages, musique posée sur ses repères).
    animatique  version longue 16:9 fr en demi-définition (images fixes à la place des plaques) : la porte avant le rendu.
    rendu       tous les formats × langues × versions dans <travail>/brouillons.
    revue       planche (une image par segment), mesures (LUFS, crête, délai de la preuve, densité de texte) → revue.json.
    livrer      finaux dans promo/montage, encodages web H.264 ≤ 25 Mo + affiche dans site-medias, manifest-campagne.json.
La revue ne note pas : elle mesure. La note sévère est écrite à la main dans le brief (« revue »), après visionnage de la
planche et des chiffres ; ne jamais se fier à un juge LLM seul (biais d'ordre) : chiffres d'abord, grille ensuite.
Effets des étapes : valider/revue = lecture ; montage/animatique/rendu = écriture dans <travail> (idempotent, cache) ;
plaques/captures = écriture + GPU ou application réelle ; livrer = écriture hors de <travail> (remplace les fichiers du film).
"""
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import typo  # noqa: E402

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FFPROBE = str(Path(FFMPEG).with_name("ffprobe"))
INTERDITS = ["nvidia", "dgx", "geforce", "rtx", "openai", "chatgpt", "révolutionn", "revolutionar", "game-changer", "magique", "magic"]
ETAPES = ["valider", "plaques", "captures", "montage", "animatique", "rendu", "master", "revue", "livrer"]


def X(p):
    return Path(str(p)).expanduser()


def charger(brief_f):
    b = json.loads(Path(brief_f).read_text())
    b["_dir"] = Path(brief_f).resolve().parent
    b["_travail"] = X(b["travail"])
    marque_f = (b["_dir"] / b.get("marque", "../../marque.json")).resolve()
    b["_marque"] = json.loads(marque_f.read_text())
    for nom, seg in b["segments"].items():  # « base » : hérite d'un autre segment puis remplace ses champs
        if seg.get("base"):
            b["segments"][nom] = {**json.loads(json.dumps(b["segments"][seg["base"]])), **{k: v for k, v in seg.items() if k != "base"}}
    return b


def captures(b, etiquette):
    """« etiquette » : « repos » (tous les fichiers *-repos.jpg) ou « fr1:exec » (fichiers fr1-*-exec.jpg : une prise nommée par la capture)."""
    if ":" in etiquette:
        prise, et = etiquette.split(":", 1)
        return sorted(str(f) for f in X(b["captures"]).glob(f"{prise}-*-{et}.jpg"))
    return sorted(str(f) for f in X(b["captures"]).glob(f"*-{etiquette}.jpg"))


def resoudre_images(b, spec):
    """[[t0, t1, etiquette, i0, i1], ...] → [[t, fichier], ...] (captures de l'étiquette réparties de t0 à t1)."""
    out = []
    for t0, t1, et, *plage in spec:
        fs = captures(b, et)
        if plage:
            fs = fs[plage[0]: plage[1] if len(plage) > 1 else None]
        n = max(1, len(fs) - 1)
        out += [[round(t0 + (t1 - t0) * k / n, 3), f] for k, f in enumerate(fs)]
    return sorted(out, key=lambda x: x[0])


# ------------------------------------------------------------------------------------------------------------- valider
def valider(b):
    v = []  # (endroit, problème, attendu, correction)
    beat = 60 / b["musique"]["bpm"]
    grille = beat * b["musique"].get("subdivision", 1)
    langues = b["langues"]
    for nom, seg in b["segments"].items():
        if seg.get("images"):
            for t0, t1, et, *_ in seg["images"]:
                for l in langues:  # « {l} » dans l'étiquette = langue du rendu (captures d'interface dans chaque langue)
                    if not captures(b, et.replace("{l}", l)):
                        v.append((f"segments.{nom}.images", f"aucune capture « {et.replace('{l}', l)} »", f"des fichiers dans {b['captures']}",
                                  "lancer l'étape captures ou corriger l'étiquette"))
        for k in ("plaque", "cle"):
            if seg.get(k) and not all(X(seg[k].replace("{l}", l)).exists() for l in langues):
                v.append((f"segments.{nom}.{k}", "fichier absent", seg[k], "lancer l'étape plaques"))
        if seg.get("en_preparation") and not any(x.get("style") == "prepa" for x in seg.get("textes", [])):
            v.append((f"segments.{nom}", "fonction non livrée montrée sans étiquette", "un texte de style « prepa »",
                      'ajouter {"t": 0, "d": <durée>, "cle": "prepa", "style": "prepa"}'))
    for nv, ver in b["versions"].items():
        t = 0.0
        for item in ver["ordre"]:
            nom, d = (item, None) if isinstance(item, str) else (item["id"], item.get("d"))
            seg = b["segments"].get(nom)
            if seg is None:
                v.append((f"versions.{nv}", f"segment inconnu « {nom} »", "un id de « segments »", "corriger l'ordre"))
                continue
            d = d or seg["d"]
            r = (t + d) / grille
            if abs(r - round(r)) > 0.02:
                v.append((f"versions.{nv}.{nom} (coupe à {t + d:.3f} s)", "coupe hors de la grille musicale",
                          f"multiple de {grille:.4f} s", f"durée {round(r) * grille - t:.4f} s"))
            for x in seg.get("textes", []):
                dx = min(x["d"], d - x["t"]) if x.get("d") else d - x["t"]
                for l in langues:
                    txt = b["textes"].get(l, {}).get(x["cle"], b["_marque"].get("langues", {}).get(l, {}).get(x["cle"]))
                    if txt is None and not x.get("langues"):
                        v.append((f"textes.{l}.{x['cle']}", "texte manquant", "une traduction", "l'écrire dans textes"))
                        continue
                    if txt is None or (x.get("langues") and l not in x["langues"]):
                        continue
                    if x.get("style") in ("titre", "pile", "impact") and dx < typo.lecture_min(txt) - 0.05:
                        v.append((f"versions.{nv}.{nom}.{x['cle']} ({l})", f"temps de lecture {dx:.2f} s",
                                  f"≥ {typo.lecture_min(txt):.2f} s ({typo.mots(txt)} mots)", "allonger le segment ou raccourcir la ligne"))
                    if x.get("style") in ("titre", "impact") and typo.mots(txt) > 7:
                        v.append((f"textes.{l}.{x['cle']}", f"{typo.mots(txt)} mots", "≤ 7 mots", "couper la ligne"))
            t += d
        cible = ver.get("cible")
        if cible and t > cible + 0.5:
            v.append((f"versions.{nv}", f"durée {t:.2f} s", f"≤ {cible} s", "raccourcir des segments"))
    for l, d in b["textes"].items():
        for k, txt in d.items():
            for m in INTERDITS:
                if m in txt.lower():
                    v.append((f"textes.{l}.{k}", f"mot interdit « {m} »", "aucun nom de fournisseur ni superlatif creux", "réécrire"))
    for x in v:
        print(f"✗ {x[0]} : {x[1]} ; attendu {x[2]} ; correction : {x[3]}")
    print(f"valider : {len(v)} violation(s)")
    return not v


# ------------------------------------------------------------------------------------------------------------- montage
def montage(b):
    out = {"produit": b["produit"], "textes": b["textes"], "cache": str(b["_travail"] / "rendu"), "versions": {}}
    mu = b["musique"]
    for nv, ver in b["versions"].items():
        segs, textes, sfx, t, debuts = [], [], [], 0.0, {}
        for item in ver["ordre"]:
            nom, d = (item, None) if isinstance(item, str) else (item["id"], item.get("d"))
            seg = json.loads(json.dumps(b["segments"][nom]))
            d = d or seg["d"]
            seg.update({k: v for k, v in item.items() if k not in ("id", "d")} if isinstance(item, dict) else {})
            seg.update({"nom": f"{nom}-{nv}" if d != b["segments"][nom]["d"] else nom, "d": round(d, 4)})
            if seg.get("type") == "ecran":
                seg["type"] = "ui"
            for k in ("images", "images_v"):
                if seg.get(k):
                    if any("{l}" in x[2] for x in seg[k]):  # une liste d'images par langue (interface capturée dans chaque langue)
                        seg[k + "_l"] = {l: resoudre_images(b, [[a, z, e.replace("{l}", l), *r] for a, z, e, *r in seg[k]]) for l in b["langues"]}
                        seg[k] = seg[k + "_l"][b["langues"][0]]
                    else:
                        seg[k] = resoudre_images(b, seg[k])
            for k in ("textes", "sfx"):
                for x in seg.pop(k, []):
                    if x["t"] >= d:
                        continue
                    y = {**x, "t": round(t + x["t"], 4)}
                    if k == "textes":
                        y["d"] = round(min(x.get("d", d - x["t"]), d - x["t"]), 4)
                        textes.append(y)
                    else:
                        sfx.append(y)
            debuts[nom] = t
            segs.append(seg)
            t += d
        m = ver.get("musique", {})
        rep = debuts[m["repere_segment"]] + m.get("repere_decalage", 0.0)
        pose = rep - mu["repere_source"]
        fin = debuts.get(m.get("arret_segment"), t)
        musique = [{"fichier": mu["fichier"], "source": max(0.0, -pose), "pose": max(0.0, pose), "d": fin - max(0.0, pose),
                    "fondu_entree": m.get("fondu_entree", 0.3), "fondu_fin": 0.03}]
        if m.get("queue"):
            q = m["queue"]
            musique.append({"fichier": mu["fichier"], "source": q["source"], "pose": debuts[q["segment"]], "d": t - debuts[q["segment"]],
                            "db": q.get("db", -4), "fondu_entree": 0.15, "fondu_fin": 1.5})
        silence = [debuts[m["silence"]], debuts[m["silence"]] + b["segments"][m["silence"]]["d"]] if m.get("silence") else None
        out["versions"][nv] = {"segments": segs, "textes": textes, "sfx": sfx, "musique": musique, "silence": silence,
                               "_duree": round(t, 3), "_debuts": debuts}
    f = b["_travail"] / "montage.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("montage :", f, {k: v["_duree"] for k, v in out["versions"].items()})
    return out


def lire_montage(b):
    return json.loads((b["_travail"] / "montage.json").read_text())


def rendre(b, versions, animatique=False):
    import monter
    m = lire_montage(b)
    sortie = b["_travail"] / ("animatique" if animatique else "brouillons")
    sortie.mkdir(parents=True, exist_ok=True)
    fichiers = []
    for fmt in (["16x9"] if animatique else b["formats"]):
        for l in (["fr"] if animatique else b["langues"]):
            for nv in versions:
                f = sortie / f"{b['film']}-{fmt}-{l}-{nv}.mp4"
                monter.construire(m, b["_marque"], b["produit"], b["textes"], m["cache"], fmt, l, str(f), nv, animatique)
                fichiers.append(f)
    return fichiers


# -------------------------------------------------------------------------------------------------------------- master
def masteriser(b, cible=-14.0, crete=-2.5):
    """Loudnorm à deux passes sur chaque brouillon (image copiée, son seul recodé) : −14 LUFS intégrés, crête vraie ≤ −1 dBTP après le recodage AAC (limiteur suréchantillonné ×4 à −2,4 dBFS).
    Le mixage du moteur V4 tombe entre −14,5 et −16 LUFS selon la durée du film (les 15 s sont trop courts pour la mesure) :
    cette passe ramène toutes les versions à la même cible."""
    for f in sorted((b["_travail"] / "brouillons").glob("*.mp4")):
        r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(f), "-af", f"loudnorm=I={cible}:TP={crete}:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True)
        m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
        af = (f"loudnorm=I={cible + 0.15}:TP={crete}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
              f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
              "aresample=192000,alimiter=limit=0.76:level=false:attack=1:release=60,aresample=48000")
        tmp = f.with_suffix(".master.mp4")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(f), "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "256k", str(tmp)], check=True)
        tmp.replace(f)
        print("master", f.name, f"{m['input_i']} LUFS → {cible}")


# --------------------------------------------------------------------------------------------------------------- revue
def image(film, t, largeur):
    from PIL import Image
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", str(film), "-frames:v", "1", "-vf", f"scale={largeur}:-2",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def revue(b):
    from PIL import Image, ImageDraw
    m = lire_montage(b)
    res = {}
    for f in sorted((b["_travail"] / "brouillons").glob("*.mp4")):
        nv = f.stem.rsplit("-", 1)[1]
        ver = m["versions"][nv]
        r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(f), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        s = r.stderr[r.stderr.rfind("Summary"):]
        mes = {k: float(x.split(":")[1].split()[0]) for x in s.splitlines() for k in ("I", "Peak", "LRA") if x.strip().startswith(k + ":")}
        preuve = next((ver["_debuts"][n] for n in ver["_debuts"] if b["segments"][n].get("preuve")), None)
        texte_s = sum(x["d"] for x in ver["textes"])
        res[f.name] = {"duree": ver["_duree"], "lufs": mes.get("I"), "crete_dbtp": mes.get("Peak"), "lra": mes.get("LRA"),
                       "preuve_a_s": preuve, "texte_ecran_pct": round(100 * texte_s / ver["_duree"]), "plans": len(ver["segments"]),
                       "plan_moyen_s": round(ver["_duree"] / len(ver["segments"]), 2)}
        if f.stem.endswith(("16x9-fr-long", "9x16-fr-long", "16x9-en-long")):
            L = 480 if "9x16" in f.stem else 640
            pts, t = [], 0.0
            for sg in ver["segments"]:
                pts.append((t + sg["d"] * 0.6, sg["nom"]))
                t += sg["d"]
            ims = [(image(f, x, L), f"{n} {x:.1f}s") for x, n in pts]
            col = 6 if "9x16" in f.stem else 4
            h = ims[0][0].height + 16
            page = Image.new("RGB", (col * L, h * (-(-len(ims) // col))), (30, 30, 30))
            d = ImageDraw.Draw(page)
            for i, (im, n) in enumerate(ims):
                page.paste(im, ((i % col) * L, (i // col) * h + 16))
                d.text(((i % col) * L + 4, (i // col) * h + 2), n, fill=(255, 190, 120))
            page.save(b["_travail"] / f"planche-{f.stem}.jpg", quality=82)
    (b["_travail"] / "revue.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, x in res.items():
        print(k, x)


# -------------------------------------------------------------------------------------------------------------- livrer
def duree(f):
    return round(float(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                      capture_output=True, text=True).stdout), 2)


def livrer(b):
    M = X("~/nexora-creative-data/promo/montage")
    S = X("~/nexora-creative-data/site-medias")
    M.mkdir(parents=True, exist_ok=True)
    n = b["film"]
    fichiers = []
    for fmt in b["formats"]:
        for l in b["langues"]:
            for nv in b["versions"]:
                src = b["_travail"] / "brouillons" / f"{n}-{fmt}-{l}-{nv}.mp4"
                fin = M / f"Nexora-{b['nom_fichier']}-{fmt}-{l}{'' if nv == 'long' else '-' + nv}.mp4"
                subprocess.run(["cp", str(src), str(fin)], check=True)
                web = S / f"film-{n}-{fmt}-{l}{'' if nv == 'long' else '-' + nv}.mp4"
                subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(fin), "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate",
                                "2900k", "-bufsize", "5800k", "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                                "-movflags", "+faststart", str(web)], check=True)
                fichiers.append({"file": web.name, "role": f"film-{nv}", "format": fmt.replace("x", ":"), "language": l,
                                 "dimensions": "1920x1080" if fmt == "16x9" else "1080x1920", "duration": duree(web),
                                 "size_bytes": web.stat().st_size, "source_file": str(fin)})
    aff = b.get("affiche", {})
    poster = S / f"film-{n}-poster.jpg"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", str(aff.get("t", 5.0)), "-i", str(M / f"Nexora-{b['nom_fichier']}-16x9-{aff.get('langue', 'fr')}.mp4"),
                    "-frames:v", "1", "-q:v", "2", str(poster)], check=True)
    fichiers.append({"file": poster.name, "role": "affiche", "format": "16:9", "dimensions": "1920x1080", "size_bytes": poster.stat().st_size})
    mf = S / "manifest-campagne.json"
    man = json.loads(mf.read_text()) if mf.exists() else {"projet": "Campagne de films Nexora", "films": {}}
    man["films"][n] = {"titre": b["titre"], "date": b.get("date"), "note": b.get("note_manifeste", ""), "fichiers": fichiers}
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n")
    print("\n".join(f"{x['file']} {x.get('size_bytes', 0) / 1e6:.1f} Mo" for x in fichiers))


def commande(b, cle):
    c = b.get("commandes", {}).get(cle)
    if not c:
        print(f"{cle} : rien à faire")
        return
    subprocess.run(c, shell=True, check=True, cwd=b["_dir"])


if __name__ == "__main__":
    b = charger(sys.argv[1])
    etapes = sys.argv[2:] or ETAPES
    for e in etapes:
        if e == "valider" and not valider(b):
            sys.exit(1)
        elif e in ("plaques", "captures"):
            commande(b, e)
        elif e == "montage":
            montage(b)
        elif e == "animatique":
            print(rendre(b, ["long"], animatique=True))
        elif e == "rendu":
            print(rendre(b, list(b["versions"])))
        elif e == "master":
            masteriser(b)
        elif e == "revue":
            revue(b)
        elif e == "livrer":
            livrer(b)
