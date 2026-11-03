"""Étape « plaques » du comparatif v2 : génère les plaques PROPRES à chaque film (les prompts du modèle auteur), sa musique,
et fait les contrôles techniques (image noire ou vide, image figée, doublon) avec UNE régénération par plaque en échec.

  python3 plaques.py <film> [<film> ...]       ex. creative-eco opsys-opus ; « tous » = les 12 films
  python3 plaques.py rejeter <film> <id> ...   rejet visuel (fait à la main sur la planche) : régénère l'image clé puis la vidéo,
                                               une seule fois par plaque (graine suivante)
Files : Qwen-Image et Music3 sur la GB10, H3 sur la RTX 5090 de pc1 (par le serveur du studio, file normale). Deux fils :
les images clés et la musique d'un côté, les vidéos H3 de l'autre (une vidéo part dès que son image clé est validée).
Recettes : h3-max (10Eros-Max turbo) sur les plans « heros » du modèle (≤ 3), h3-fast (première image exacte) sinon.
Journal par film : <film>/plaques.json (secondes GPU par machine, régénérations, contrôles).
"""
import hashlib
import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[1] / "refonte-medias/outils"))
import moteurs  # noqa: E402

os.environ.setdefault("NEXORA_H3_MAX_CHECKPOINT", "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors")
moteurs.H3_MAX = {"videoModel": "h3-max", "steps": 8, "refMode": True}
TRAVAIL = Path.home() / "nexora-creative-data/work/films-v2"
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
SUFFIXE_IMAGE = "Photorealistic cinematic film still, natural skin and hands, no text, no letters, no numbers, no logos, no watermark."
SUFFIXE_H3 = "Photorealistic cinematic, no text, no logos."
FILMS = [f"{b}-{p}" for p in ("eco", "equilibre", "expert", "opus") for b in ("creative", "opsys", "workstudio")]
VERROU = threading.Lock()


def charger_journal(dos):
    f = dos / "plaques.json"
    return json.loads(f.read_text()) if f.exists() else {"plaques": {}, "gpu_s": {"gb10-qwen": 0, "gb10-music3": 0, "pc1-h3-fast": 0, "pc1-h3-max": 0}}


def sauver(dos, j):
    with VERROU:
        (dos / "plaques.json").write_text(json.dumps(j, ensure_ascii=False, indent=1))


def graine(film, pid, k):
    return int(hashlib.sha1(f"{pid}-{k}".encode()).hexdigest()[:6], 16)  # même graine pour un même id de plan, quel que soit le modèle


def ahash(im):
    a = np.asarray(im.convert("L").resize((16, 9)), np.float32)
    return (a > a.mean()).flatten()


def controle_image(f, autres):
    im = Image.open(f).convert("RGB")
    a = np.asarray(im, np.float32)
    if a.mean() < 10 or a.std() < 6:
        return "image noire ou vide"
    h = ahash(im)
    for g, h2 in autres:
        if (h != h2).sum() < 8:
            return f"doublon de {g}"
    return None


def images_video(f, n=3):
    d = float(subprocess.run([str(Path(FF).with_name("ffprobe")), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                             capture_output=True, text=True).stdout or 0)
    out = []
    for t in np.linspace(0.2, max(0.3, d - 0.3), n):
        b = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(f), "-frames:v", "1", "-vf", "scale=320:-2", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if b:
            out.append(np.frombuffer(b, np.uint8).astype(np.float32))
    return d, out


def controle_video(f):
    d, ims = images_video(f)
    if d < 4.5 or len(ims) < 3:
        return f"vidéo trop courte ({d:.1f} s)"
    if min(x.mean() for x in ims) < 8:
        return "image noire dans la vidéo"
    if np.abs(ims[0] - ims[-1]).mean() < 1.5:
        return "plan figé"
    return None


def description_musique(mu, duree):
    secs = " ".join(f"[{s.get('nom', 'Section')}] at {float(s.get('debut', 0)):.0f} seconds: {s.get('description', '')}" for s in mu.get("sections", []))
    coups = ", ".join(f"{float(c):.1f}" for c in mu.get("coups", []))
    return (f"Global Metadata: {mu.get('genre', '')}, {mu.get('tempo_bpm', 110)} BPM, {mu.get('description', '')} Loud polished master.\n\n"
            "Vocal Details: Instrumental, no lyrics, no vocals, no choir.\n\n"
            f"Arrangement: {secs}" + (f" Strong hits at {coups} seconds." if coups else "") + f" Clean ending at {duree:.0f} seconds.")


def travailler(films, rejets=None):
    q_h3 = queue.Queue()
    fin_cles = threading.Event()

    def fil_h3():
        while True:
            try:
                x = q_h3.get(timeout=5)
            except queue.Empty:
                if fin_cles.is_set():
                    return
                continue
            dos, j, p, k = x
            pid = p["id"]
            rec = j["plaques"][pid]
            moteur = "max" if p.get("heros") else "rapide"
            for essai in range(2):  # une régénération si le contrôle échoue ; une reprise si le moteur échoue (limite de puissance)
                f = dos / "plaques" / f"{pid}-{moteur}-{k}{'b' if essai else ''}.mp4"
                prompt = moteurs.h3(f"{p['image']} {p['mouvement']} {SUFFIXE_H3}", p.get("son") or "Quiet ambience")
                try:
                    _, tid, s = moteurs.video(prompt, f, "16:9", moteur, 5, True, seed=graine(dos.name, pid, k) + essai,
                                              depart=dos / "plaques" / rec["cle"])
                except Exception as e:  # noqa: BLE001
                    rec.setdefault("erreurs", []).append(str(e)[:200])
                    continue
                j["gpu_s"]["pc1-h3-max" if moteur == "max" else "pc1-h3-fast"] += round(s, 1)
                err = controle_video(f)
                rec.update({"video": f.name, "recette": "h3-max" if moteur == "max" else "h3-fast", "video_s": round(s, 1), "controle_video": err})
                if not err:
                    break
                rec["regen_video"] = rec.get("regen_video", 0) + 1
            sauver(dos, j)
            print(f"h3 {dos.name} {pid} {rec.get('recette')} {rec.get('video_s')} s {rec.get('controle_video') or 'ok'}", flush=True)

    th = threading.Thread(target=fil_h3)
    th.start()
    try:
        for nom in films:
            dos = TRAVAIL / nom
            film = json.loads((dos / "film.json").read_text())
            (dos / "plaques").mkdir(exist_ok=True)
            j = charger_journal(dos)
            empreintes = []
            for p in film["plans"]:
                if p.get("type") != "plan":
                    continue
                pid = p["id"]
                rec = j["plaques"].setdefault(pid, {})
                k = rec.get("tour", 0)
                if rejets is not None:
                    if pid not in rejets.get(nom, []):
                        if rec.get("cle"):
                            empreintes.append((pid, ahash(Image.open(dos / "plaques" / rec["cle"]))))
                        continue
                    if rec.get("rejet_visuel"):
                        print("déjà régénérée une fois :", nom, pid)
                        continue
                    rec["rejet_visuel"] = True
                    k = rec["tour"] = k + 1
                    rec.pop("video", None)
                if rec.get("cle") and rec.get("video"):
                    empreintes.append((pid, ahash(Image.open(dos / "plaques" / rec["cle"]))))
                    continue
                if not rec.get("cle") or rejets is not None:
                    for essai in range(2):
                        f = dos / "plaques" / f"{pid}-cle-{k}{'b' if essai else ''}.png"
                        _, tid, s = moteurs.image(f"{p['image']} {SUFFIXE_IMAGE}", f, 1344, 768, seed=graine(nom, pid, k) + 1000 * essai)
                        j["gpu_s"]["gb10-qwen"] += round(s, 1)
                        err = controle_image(f, empreintes)
                        rec.update({"cle": f.name, "cle_s": round(s, 1), "controle_image": err})
                        if not err:
                            break
                        rec["regen_cle"] = rec.get("regen_cle", 0) + 1
                    sauver(dos, j)
                    print(f"cle {nom} {pid} {rec['cle_s']} s {rec.get('controle_image') or 'ok'}", flush=True)
                empreintes.append((pid, ahash(Image.open(dos / "plaques" / rec["cle"]))))
                q_h3.put((dos, j, p, k))
            fm = dos / "musique.flac"
            if not fm.exists() and rejets is None:
                tot = sum(p["duree"] for p in film["plans"]) + film["fin"]["duree"]
                paroles = "\n\n".join(f"[{s.get('nom', 'Section')}]" for s in film["musique"].get("sections", [])) or "[Instrumental]"
                _, tid, s = moteurs.musique(description_musique(film["musique"], tot + 2), fm, round(tot + 4), paroles, seed=71)
                j["gpu_s"]["gb10-music3"] += round(s, 1)
                j["musique"] = {"description": description_musique(film["musique"], tot + 2), "secondes": round(s, 1)}
                sauver(dos, j)
                print(f"musique {nom} {s:.0f} s", flush=True)
    finally:
        fin_cles.set()
        th.join()


def planche(nom, largeur=400):
    """Planche des plaques d'un film (image à 40 % de chaque vidéo, sinon l'image clé), id en surimpression : pour la revue à l'œil."""
    from PIL import ImageDraw
    dos = TRAVAIL / nom
    j = charger_journal(dos)
    ims = []
    for pid, r in sorted(j["plaques"].items()):
        f = dos / "plaques" / r.get("video", "")
        if r.get("video") and f.exists():
            b = subprocess.run([FF, "-v", "error", "-ss", "2.5", "-i", str(f), "-frames:v", "1", "-vf", f"scale={largeur}:-2", "-f", "image2pipe",
                                "-vcodec", "png", "-"], capture_output=True).stdout
            from io import BytesIO
            im = Image.open(BytesIO(b)).convert("RGB")
        else:
            im = Image.open(dos / "plaques" / r["cle"]).convert("RGB").resize((largeur, int(largeur * 768 / 1344)))
        ImageDraw.Draw(im).text((6, 4), pid + (" MAX" if r.get("recette") == "h3-max" else ""), fill=(255, 200, 0))
        ims.append(im)
    col = 5
    h = ims[0].height
    page = Image.new("RGB", (col * largeur, h * (-(-len(ims) // col))))
    for i, im in enumerate(ims):
        page.paste(im, ((i % col) * largeur, (i // col) * h))
    f = dos / f"planche-plaques-{nom}.jpg"
    page.save(f, quality=80)
    print(f)


if __name__ == "__main__":
    if sys.argv[1] == "planche":
        for n in sys.argv[2:]:
            planche(n)
        sys.exit()
    if sys.argv[1] == "rejeter":
        travailler([sys.argv[2]], {sys.argv[2]: sys.argv[3:]})
    else:
        travailler(FILMS if sys.argv[1] == "tous" else sys.argv[1:])
