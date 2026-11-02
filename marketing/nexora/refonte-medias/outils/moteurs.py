"""Site redesign ("Signal"): direct calls to the Nexora Creative server (/api/generate), with the prompt written by hand
(no LLM rewriting) so the prompt we keep in the manifest is exactly the one the engine received.

  Qwen-Image-2.1 (GB10) : image(prompt, out, w, h, seed=None, negatif=...)
  MiniMax H3 (RTX 5090) : video(prompt, out, fmt="16:9"|"9:16", moteur="max"|"rapide", secondes=5)
  MiniMax-Music3 (GB10) : musique(description, out, secondes, paroles="[Instrumental]")

Every render is logged (engine, duration, take) in the work folder's journal-gpu.jsonl: the GPU total comes from there.
"""
import json, shutil, time, urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:37161"
TRAVAIL = Path.home() / "nexora-creative-data/site-medias-travail"
JOURNAL = TRAVAIL / "journal-gpu.jsonl"

NEG_IMAGE = ("text, letters, words, numbers, logo, watermark, signature, brand name, label, caption, robot, android, "
             "glowing brain, purple gradient, cartoon, illustration, lowres, blurry, deformed, extra fingers, distorted hands")

H3_MAX = {"videoModel": "h3-max", "steps": 24}  # "cinema" recipe: full model, 24 steps (recherche/10-qualite-h3.md)
MOTEUR_H3 = "http://127.0.0.1:37288"  # ComfyUI of the RTX 5090 (SSH tunnel), read only: list of models


def checkpoint_max():
    """Full H3 FL2VA checkpoint of the "cinema" recipe, looked up on each render in the list the engine publishes
    (GET /object_info/UNETLoader): nothing hard-coded, so a version removed on pc1 is handled automatically.
    Order: the studio's recipe variable (NEXORA_H3_MAX_CHECKPOINT) if present, otherwise the official non-distilled FL2VA."""
    import os
    with urllib.request.urlopen(MOTEUR_H3 + "/object_info/UNETLoader", timeout=30) as r:
        noms = json.loads(r.read())["UNETLoader"]["input"]["required"]["unet_name"][0]
    voulu = os.environ.get("NEXORA_H3_MAX_CHECKPOINT")
    if voulu and voulu in noms:
        return voulu
    cand = [n for n in noms if "fl2va" in n.lower() and not any(x in n.lower() for x in ("fast", "turbo", "8step", "ref2va"))]
    if not cand:
        raise RuntimeError("aucun point de contrôle H3 FL2VA complet sur le moteur")
    return sorted(cand, key=lambda n: ("official" not in n and "minimax_h3_fl2va" not in n, n))[0]
H3_RAPIDE = {"videoModel": "h3-fast", "steps": 8}
TAILLES_H3 = {"16:9": (1344, 768), "9:16": (768, 1344)}


def _appel(chemin, corps=None, delai=120):
    req = urllib.request.Request(BASE + chemin, data=None if corps is None else json.dumps(corps).encode(),
                                 headers={"content-type": "application/json"}, method="GET" if corps is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=delai) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{chemin} : HTTP {e.code} {e.read().decode()[:400]}")


def _attendre(tid, delai_max=3600):
    t0 = time.time()
    while True:
        p = _appel(f"/api/studio/prise/{tid}")
        if p["statut"] == "done" and p.get("creation"):
            return p["creation"]
        if p["statut"] in ("failed", "stopped"):
            raise RuntimeError(f"prise {tid} échouée : {p.get('erreur')}")
        if time.time() - t0 > delai_max:
            raise TimeoutError(f"prise {tid} trop longue")
        time.sleep(3)


def _copier(c, sortie):
    sortie = Path(sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    src = Path(c["fichier"]) if c.get("fichier") else None
    if src and src.exists():
        shutil.copyfile(src, sortie)
    else:
        with urllib.request.urlopen(BASE + f"/api/media/{c['id']}?download=1", timeout=300) as r, open(sortie, "wb") as f:
            shutil.copyfileobj(r, f)
    return sortie


def _lancer(corps, sortie, moteur, delai_max=3600):
    t0 = time.time()
    r = _appel("/api/generate", corps)
    tid = r.get("takeId") or r["takeIds"][0]
    c = _attendre(tid, delai_max)
    t1 = time.time()
    _copier(c, sortie)
    TRAVAIL.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL, "a") as f:
        f.write(json.dumps({"fichier": str(sortie), "moteur": moteur, "prise": tid, "debut": t0, "fin": t1,
                            "secondes": round(t1 - t0, 1)}) + "\n")
    return sortie, tid, t1 - t0


def image(prompt, sortie, w=2560, h=1440, seed=None, negatif=NEG_IMAGE, brouillon=False):
    corps = {"kind": "still", "model": "qwen21", "quality": "draft" if brouillon else "quality", "prompt": prompt,
             "negative": negatif, "width": w, "height": h, "count": 1, "app": "nexora-image", "shotName": Path(sortie).stem}
    if seed is not None:
        corps["seed"] = seed
    return _lancer(corps, sortie, "gb10-qwen21", 1800)


I2VA = "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"


def televerser(chemin):
    """Uploads a local image as an engine input; returns the asset:<id> token (first image of an I2VA shot)."""
    import base64
    data = base64.b64encode(Path(chemin).read_bytes()).decode()
    mime = "image/png" if str(chemin).endswith(".png") else "image/jpeg"
    return _appel("/api/upload", {"name": Path(chemin).stem, "dataUrl": f"data:{mime};base64,{data}"})["name"]


def video(prompt, sortie, fmt="16:9", moteur="max", secondes=5, son=True, seed=None, depart=None):
    """depart: local image (exact H3 size of the format) used as the first frame (I2VA)."""
    w, h = TAILLES_H3[fmt]
    if depart:
        prompt = I2VA + prompt
    n = max(0, -(-(round(secondes * 24) - 124) // 17))
    recette = dict(H3_MAX, checkpoint=checkpoint_max()) if moteur == "max" else H3_RAPIDE
    corps = {"kind": "video", **recette, "prompt": prompt, "width": w, "height": h,
             "lengthFrames": min(362, 124 + 17 * n), "withAudio": son, "shotName": Path(sortie).stem}
    if depart:
        corps["startImage"] = televerser(depart)
    if seed is not None:
        corps["seed"] = seed
    return _lancer(corps, sortie, f"rtx5090-h3-{moteur}", 5400)


def musique(description, sortie, secondes=40, paroles="[Instrumental]", seed=None):
    corps = {"kind": "musique", "videoModel": "music3", "description": description, "paroles": paroles,
             "dureeS": secondes, "app": "nexora-musique", "shotName": Path(sortie).stem, "prompt": description}
    if seed is not None:
        corps["seed"] = seed
    return _lancer(corps, sortie, "music3", 1800)


def h3(description, son, musique_nd="N/A"):
    """Builds a T2VA H3 prompt (official guide: three fields in order)."""
    return f"integrated_multimodal_description: {description}\n\noverall_soundscape: {son}\n\nnon_diegetic_music: {musique_nd}"
