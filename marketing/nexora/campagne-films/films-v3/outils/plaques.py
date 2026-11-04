"""Plaques cinéma des films V5 : peu de plans, plus lumineux, regardés un à un.

  python3 plaques.py <film> [<film> ...] [--formats 16:9,9:16]
  python3 plaques.py rejeter <film> <plaque> <format>     (rejet visuel : nouvelle graine, image clé puis vidéo)
Chaîne : image clé Qwen-Image 2.1 (GB10) à la taille exacte de H3 → MiniMax H3 sur la RTX 5090 de pc1 (h3-max 10Eros-Max
pour les plans héros, h3-fast sinon ; première image exacte), par l'API du studio (VM 202, tunnel 127.0.0.1:13161, file normale :
aucun travail en cours n'est interrompu). Plaques reprises d'un film précédent (« existant ») : copiées de pc1 pour le 16:9 ;
le 9:16 est tourné à neuf (cadrage vertical natif). Contrôles : image trop sombre (luminance médiane), figée, noire.
Journal : work/films-v3/<film>/plaques/plaques.json.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

import commun as C

sys.path.insert(0, str(C.RACINE.parent.parent / "refonte-medias/outils"))
os.environ.setdefault("NEXORA_H3_MAX_CHECKPOINT", "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors")
import moteurs  # noqa: E402

moteurs.BASE = os.environ.get("NEXORA_STUDIO", "http://127.0.0.1:13161")
moteurs.TRAVAIL = C.TRAVAIL
moteurs.JOURNAL = C.TRAVAIL / "journal-gpu.jsonl"
moteurs.H3_MAX = {"videoModel": "h3-max", "steps": 8, "refMode": True}
PC1_V2 = "/run/media/pc1/Infrastructure/NexoraStudioWork/films-v2/travail"
LUMIERE = ("Bright, luminous, well exposed image with a clear key light and lifted blacks, natural colors, photorealistic cinematic "
           "film still, natural skin and hands, no text, no letters, no numbers, no logos, no screens with readable content, no watermark.")
SUFFIXE_H3 = "Photorealistic cinematic, bright natural exposure, no text, no logos."
TAILLES = {"16:9": (1344, 768), "9:16": (768, 1344)}


def graine(film, pid, fmt, k):
    return int(hashlib.sha1(f"v5-{film}-{pid}-{fmt}-{k}".encode()).hexdigest()[:6], 16)


def luminance(im):
    a = np.asarray(im.convert("L"), np.float32)
    return float(np.median(a)), float(np.percentile(a, 95))


def images_video(f, n=4):
    d = C.duree(f)
    out = []
    for i in range(n):
        b = subprocess.run([C.FF, "-v", "error", "-ss", f"{d * (i + 0.5) / n:.2f}", "-i", str(f), "-frames:v", "1", "-f", "rawvideo",
                            "-pix_fmt", "gray", "-s", "160x90", "-"], capture_output=True).stdout
        if len(b) == 160 * 90:
            out.append(np.frombuffer(b, np.uint8).astype(np.float32))
    return out


def controle_video(f):
    ims = images_video(f)
    if len(ims) < 3:
        return "illisible"
    if np.median(ims[len(ims) // 2]) < 38:
        return "trop sombre"
    if max(np.abs(ims[i] - ims[0]).mean() for i in range(1, len(ims))) < 1.2:
        return "figée"
    return None


def une_plaque(film, pid, p, fmt, dos, j, k=0):
    cle_id = f"{pid}-{fmt.replace(':', 'x')}"
    rec = j.setdefault(cle_id, {})
    if p.get("existant") and fmt == "16:9":
        f = dos / f"{cle_id}.mp4"
        if not f.exists():
            subprocess.run(["scp", "-q", f"pc1:{PC1_V2}/{p['existant']}", str(f)], check=True)
        rec.update({"video": f.name, "recette": "reprise " + p["existant"]})
        return rec
    w, h = TAILLES[fmt]
    cadrage = " Vertical portrait composition, subject centered, generous headroom." if fmt == "9:16" else ""
    fc = dos / f"{cle_id}-cle-{k}.png"
    if not fc.exists() and os.environ.get("PLAQUES_SANS_CLE"):
        # GB10 occupée par un autre travail : H3 tourne directement depuis le texte (T2VA) sur la 5090 de pc1
        moteur = "max" if p.get("recette") == "max" else "rapide"
        fv = dos / f"{cle_id}-{moteur}-t2v-{k}.mp4"
        if not fv.exists():
            prompt = moteurs.h3(f"{p['image']}{cadrage} {p['mouvement']} {LUMIERE} {SUFFIXE_H3}", p.get("son") or "Quiet ambience")
            _, tid, s = moteurs.video(prompt, fv, fmt, moteur, p.get("secondes", 5), True, seed=graine(film, pid, fmt, k))
            rec["h3_s"] = round(s, 1)
        rec.update({"video": fv.name, "recette": ("h3-max" if moteur == "max" else "h3-fast") + " texte→vidéo",
                    "graine": graine(film, pid, fmt, k), "controle": controle_video(fv)})
        return rec
    if not fc.exists():
        _, _, s = moteurs.image(f"{p['image']}{cadrage} {LUMIERE}", fc, w, h, seed=graine(film, pid, fmt, k))
        rec["qwen_s"] = round(s, 1)
    im = Image.open(fc)
    med, p95 = luminance(im)
    if med < 70:  # plaque trop sombre : on relève avant H3 (gamma doux, noirs levés), la première image reste exacte
        a = np.asarray(im.convert("RGB"), np.float32) / 255
        a = 0.04 + 0.96 * a ** (0.78 if med < 55 else 0.86)
        Image.fromarray((a * 255).clip(0, 255).astype(np.uint8)).save(fc)
        rec["releve"] = round(med, 1)
    if os.environ.get("PLAQUES_CLES_SEULES"):  # second fil : images clés d'avance (la GB10 est partagée), vidéos par le fil principal
        return rec
    moteur = "max" if p.get("recette") == "max" else "rapide"
    fv = dos / f"{cle_id}-{moteur}-{k}.mp4"
    if not fv.exists():
        prompt = moteurs.h3(f"{p['image']} {p['mouvement']} {SUFFIXE_H3}", p.get("son") or "Quiet ambience")
        _, tid, s = moteurs.video(prompt, fv, fmt, moteur, p.get("secondes", 5), True, seed=graine(film, pid, fmt, k), depart=fc)
        rec["h3_s"] = round(s, 1)
    rec.update({"cle": fc.name, "video": fv.name, "recette": "h3-max" if moteur == "max" else "h3-fast", "graine": graine(film, pid, fmt, k),
                "controle": controle_video(fv), "luminance_cle": round(med, 1)})
    return rec


def travailler(films, formats):
    for film in films:
        f = C.charger_film(film)
        dos = C.dossier(film) / "plaques"
        dos.mkdir(exist_ok=True)
        jf = dos / "plaques.json"
        j = json.loads(jf.read_text()) if jf.exists() else {}
        # héros d'abord (16:9 puis 9:16), puis le reste
        ordre = sorted(f["plaques"].items(), key=lambda kv: kv[1].get("recette") != "max")
        if os.environ.get("PLAQUES_CLES_SEULES"):
            ordre = ordre[::-1]
        for fmt in formats:
            for pid, p in ordre:
                t0 = time.time()
                try:
                    r = une_plaque(film, pid, p, fmt, dos, j)
                    print(film, pid, fmt, r.get("recette"), r.get("controle"), round(time.time() - t0), "s", flush=True)
                except Exception as e:  # noqa: BLE001
                    print(film, pid, fmt, "ÉCHEC", str(e)[:300], flush=True)
                if not os.environ.get("PLAQUES_CLES_SEULES"):
                    jf.write_text(json.dumps(j, ensure_ascii=False, indent=1))


def rejeter(film, pid, fmt):
    f = C.charger_film(film)
    dos = C.dossier(film) / "plaques"
    jf = dos / "plaques.json"
    j = json.loads(jf.read_text())
    cle_id = f"{pid}-{fmt.replace(':', 'x')}"
    k = 1 + max([int(x.stem.split("-")[-1]) for x in dos.glob(f"{cle_id}-cle-*.png")] + [0])
    r = une_plaque(film, pid, f["plaques"][pid], fmt, dos, j, k)
    r["rejets"] = r.get("rejets", 0) + 1
    jf.write_text(json.dumps(j, ensure_ascii=False, indent=1))
    print(film, pid, fmt, r)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "rejeter":
        rejeter(*a[1:4])
    else:
        fm = ["16:9", "9:16"]
        if "--formats" in a:
            fm = a[a.index("--formats") + 1].split(",")
            a = [x for x in a if x not in ("--formats", ",".join(fm))]
        travailler(a, fm)
