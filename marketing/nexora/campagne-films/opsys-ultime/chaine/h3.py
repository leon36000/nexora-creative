"""Client ComfyUI du film ultime OPSYS-AI : MiniMax H3 (RTX 5090 de pc1, tunnel 127.0.0.1:37288) et Qwen-Image-2.1 (GB10,
127.0.0.1:37188). Reprend le graphe de `marketing/creative/video-v3/moteur.py` et ajoute ce qu'il faut au film :
  - références (jusqu'à 9 images : fiches de personnages, lieux) sur le point de contrôle ref2va (`h3-max`) ;
  - ancrages `MiniMaxH3AddGuide` : image(s) à un indice d'image (première image exacte, dernière image d'un plan précédent
    pour enchaîner), et **piste audio ancrée** (la voix choisie) : H3 génère les lèvres sur cette voix (synchronisation native) ;
  - `h3-fast` (FastH3, famille fl2va) depuis une première image exacte ;
  - un journal GPU par équipe (`<sortie>/rendus.jsonl` et `~/.../opsys-ultime/journal-gpu.jsonl`).
File partagée : on soumet normalement, on attend son tour, jamais plus de `--max-file` travaux à nous en attente.

Spec H3 : {"type":"h3","equipe","nom","recette":"h3-max"|"h3-fast","prompt","largeur","hauteur","images" (17k+5),
           "graine","refs":[png...],"premiere":png|null,"guides":[{"image":png,"indice":0}],"audio":wav|null,
           "audio_indice":0,"sortie"}
Spec image : {"type":"image","equipe","nom","prompt","negatif","largeur","hauteur","graine","sortie"}
Usage : python3 h3.py specs.json [nom ...] [--max-file 6]
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

H3_COMFY = os.environ.get("H3_COMFY", "http://127.0.0.1:37288")
IMG_COMFY = os.environ.get("IMG_COMFY", "http://127.0.0.1:37188")
CLIP_H3 = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
RECETTES = {
    # mesuré le 02/11 (HANDOFF video-v3) : 112 s moteur pour 1344x768x124 ; avec références ≈ 129 s (JOURNAL)
    "h3-max": {"checkpoint": "10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors", "etapes": 8,
               "decalage": [12, 3], "echantillonneur": "euler", "ref": True},
    # FastH3 nvfp4 8 étapes, famille fl2va (première image exacte), 104 s moteur
    "h3-fast": {"checkpoint": "fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors", "etapes": 8,
                "decalage": None, "echantillonneur": "res_multistep", "ref": False},
}
JOURNAL_GLOBAL = Path(os.environ.get("OPSYS_JOURNAL", "~/nexora-creative-data/work/opsys-ultime/journal-gpu.jsonl")).expanduser()


def http(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def envoyer(comfy, chemin):
    """Téléverse une image ou un son dans le dossier input de ComfyUI ; nom unique par contenu pour éviter les collisions."""
    p = Path(chemin).expanduser()
    import hashlib
    h = hashlib.sha1(p.read_bytes()).hexdigest()[:10]
    nom = f"opsys-{h}{p.suffix.lower()}"
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".wav": "audio/wav", ".mp3": "audio/mpeg", ".flac": "audio/flac"}.get(p.suffix.lower(), "application/octet-stream")
    lim = uuid.uuid4().hex
    corps = (f"--{lim}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{nom}\"\r\nContent-Type: {mime}\r\n\r\n").encode() \
        + p.read_bytes() + f"\r\n--{lim}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{lim}--\r\n".encode()
    r = json.loads(http(f"{comfy}/upload/image", corps, {"Content-Type": f"multipart/form-data; boundary={lim}"}))
    return r["name"]


def graphe_h3(s, comfy):
    rec = RECETTES[s.get("recette", "h3-max")]
    turbo = rec["decalage"]
    src = "shift" if turbo else "u"
    pref = f"opsys-ultime/{s.get('equipe', 'commun')}/{s['nom']}"
    g = {
        "u": {"class_type": "UNETLoader", "inputs": {"unet_name": rec["checkpoint"], "weight_dtype": "default"}},
        "c": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP_H3, "type": "minimax", "device": "default"}},
        "vv": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "va": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "sampler": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": rec["echantillonneur"]}},
        "sched": {"class_type": "BasicScheduler", "inputs": {"model": [src, 0], "scheduler": "simple", "steps": rec["etapes"], "denoise": 1.0}},
        "noise": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(s.get("graine", 42))}},
        "sca": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler", 0],
                                                                  "sigmas": ["sched", 0], "latent_image": ["gen", 1]}},
        "dv": {"class_type": "VAEDecode", "inputs": {"samples": ["sca", 0], "vae": ["vv", 0]}},
        "da": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["sca", 0], "vae": ["va", 0]}},
        "vid": {"class_type": "CreateVideo", "inputs": {"images": ["dv", 0], "audio": ["da", 0], "fps": 24}},
        "save": {"class_type": "SaveVideo", "inputs": {"video": ["vid", 0], "filename_prefix": pref, "format": "auto", "codec": "auto"}},
    }
    if turbo:
        g["shift"] = {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["u", 0], "shift_video": turbo[0], "shift_audio": turbo[1]}}
    gen = {"clip": ["c", 0], "vae": ["vv", 0], "prompt": s["prompt"], "width": int(s.get("largeur", 1344)),
           "height": int(s.get("hauteur", 768)), "length": int(s.get("images", 124))}
    if rec["ref"]:
        gen["audio_vae"] = ["va", 0]
        gen["ref_image_size"] = s.get("taille_ref", "match")
        for i, r in enumerate(s.get("refs", [])[:9]):
            g[f"ref{i}"] = {"class_type": "LoadImage", "inputs": {"image": envoyer(comfy, r)}}
            gen[f"ref_images.ref_image_{i}"] = [f"ref{i}", 0]
        for i, r in enumerate(s.get("refs_audio", [])[:3]):
            g[f"ra{i}"] = {"class_type": "LoadAudio", "inputs": {"audio": envoyer(comfy, r)}}
            gen[f"ref_audios.ref_audio_{i}"] = [f"ra{i}", 0]
        g["gen"] = {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": gen}
    else:
        if s.get("premiere"):
            g["ls"] = {"class_type": "LoadImage", "inputs": {"image": envoyer(comfy, s["premiere"])}}
            g["ss"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["ls", 0], "upscale_method": "lanczos",
                                                                          "megapixels": gen["width"] * gen["height"] / 1e6, "resolution_steps": 32}}
            gen["first_frame"] = ["ss", 0]
        g["gen"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": gen}
    # ancrages (image(s) à un indice, piste audio) chaînés sur le conditionnement positif
    pos = ["gen", 0]
    guides = list(s.get("guides", []))
    if rec["ref"] and s.get("premiere"):
        guides.insert(0, {"image": s["premiere"], "indice": 0})
    for i, gd in enumerate(guides):
        g[f"gi{i}"] = {"class_type": "LoadImage", "inputs": {"image": envoyer(comfy, gd["image"])}}
        g[f"gs{i}"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": [f"gi{i}", 0], "upscale_method": "lanczos",
                                                                          "megapixels": gen["width"] * gen["height"] / 1e6, "resolution_steps": 32}}
        g[f"g{i}"] = {"class_type": "MiniMaxH3AddGuide", "inputs": {"positive": pos, "latent": ["gen", 1], "frame_idx": int(gd.get("indice", 0)),
                                                                    "vae": ["vv", 0], "image": [f"gs{i}", 0]}}
        pos = [f"g{i}", 0]
    if s.get("audio"):
        g["la"] = {"class_type": "LoadAudio", "inputs": {"audio": envoyer(comfy, s["audio"])}}
        g["ga"] = {"class_type": "MiniMaxH3AddGuide", "inputs": {"positive": pos, "latent": ["gen", 1], "frame_idx": int(s.get("audio_indice", 0)),
                                                                 "audio_vae": ["va", 0], "audio": ["la", 0]}}
        pos = ["ga", 0]
    g["guider"] = {"class_type": "BasicGuider", "inputs": {"model": [src, 0], "conditioning": pos}}
    return g


def graphe_image(s):
    return {
        "u": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_int8_convrot.safetensors", "weight_dtype": "default"}},
        "cache": {"class_type": "QwenImage21Cache", "inputs": {"model": ["u", 0], "device": "auto", "dtype": "default"}},
        "c": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_8b_int8_convrot.safetensors", "type": "qwen_image", "device": "default"}},
        "v": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
        "enc": {"class_type": "TextEncodeQwenImage21", "inputs": {"clip": ["c", 0], "prompt": s["prompt"], "negative_prompt": s.get("negatif", ""), "resolution": 1024}},
        "lat": {"class_type": "EmptyLatentImage", "inputs": {"width": int(s.get("largeur", 1664)), "height": int(s.get("hauteur", 928)), "batch_size": 1}},
        "k": {"class_type": "KSampler", "inputs": {"model": ["cache", 0], "positive": ["enc", 0], "negative": ["enc", 1], "latent_image": ["lat", 0],
                                                   "seed": int(s.get("graine", 1)), "steps": int(s.get("etapes", 25)), "cfg": 1, "sampler_name": "euler",
                                                   "scheduler": "simple", "denoise": 1.0}},
        "d": {"class_type": "VAEDecode", "inputs": {"samples": ["k", 0], "vae": ["v", 0]}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["d", 0], "filename_prefix": f"opsys-ultime/{s.get('equipe', 'commun')}/{s['nom']}"}},
    }


def nos_travaux_en_attente(comfy):
    try:
        q = json.loads(http(f"{comfy}/queue"))
    except Exception:
        return 0
    n = 0
    for it in q.get("queue_pending", []) + q.get("queue_running", []):
        try:
            if "opsys-ultime/" in json.dumps(it[2].get("save", {}).get("inputs", {})):
                n += 1
        except Exception:
            pass
    return n


def soumettre(s, max_file=6):
    video = s.get("type", "h3") == "h3"
    comfy = s.get("comfy", H3_COMFY if video else IMG_COMFY)
    while nos_travaux_en_attente(comfy) >= max_file:
        time.sleep(10)
    g = graphe_h3(s, comfy) if video else graphe_image(s)
    pid = json.loads(http(f"{comfy}/prompt", json.dumps({"prompt": g, "client_id": "opsys-ultime"}).encode(),
                          {"Content-Type": "application/json"}))["prompt_id"]
    return comfy, pid, time.time()


def attendre(s, comfy, pid, t0):
    while True:
        time.sleep(4)
        try:
            h = json.loads(http(f"{comfy}/history/{pid}")).get(pid)
        except Exception:
            continue
        if not h:
            continue
        st = h.get("status", {})
        if st.get("status_str") == "error":
            raise RuntimeError(json.dumps(st.get("messages"))[-1500:])
        if not st.get("completed"):
            continue
        ts = {m[0]: m[1].get("timestamp") for m in st.get("messages", [])}
        f = [x for o in h["outputs"].values() for x in o.get("video", []) + o.get("images", []) + o.get("gifs", [])][0]
        q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
        data = http(f"{comfy}/view?{q}", timeout=600)
        sortie = Path(s["sortie"]).expanduser()
        sortie.mkdir(parents=True, exist_ok=True)
        extension = Path(f["filename"]).suffix
        index = 1
        while True:
            nom = f"{s['nom']}{extension}" if index == 1 else f"{s['nom']}-{index}{extension}"
            local = sortie / nom
            try:
                with local.open("xb") as fichier:
                    fichier.write(data)
                break
            except FileExistsError:
                index += 1
        moteur = None
        if ts.get("execution_start") and ts.get("execution_success"):
            moteur = round((ts["execution_success"] - ts["execution_start"]) / 1000, 1)
        return {"equipe": s.get("equipe"), "nom": s["nom"], "type": s.get("type", "h3"), "recette": s.get("recette"),
                "images": s.get("images"), "largeur": s.get("largeur"), "hauteur": s.get("hauteur"), "graine": s.get("graine"),
                "refs": len(s.get("refs", [])), "audio": bool(s.get("audio")), "secondesMoteur": moteur,
                "secondesTotal": round(time.time() - t0, 1), "fichier": str(local), "fin": time.strftime("%Y-%m-%dT%H:%M:%S")}


def journaliser(s, res):
    for j in (Path(s["sortie"]).expanduser() / "rendus.jsonl", JOURNAL_GLOBAL):
        j.parent.mkdir(parents=True, exist_ok=True)
        with j.open("a") as fh:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")


def rendre_tous(specs, max_file=6, parallele=True):
    """Soumet jusqu'à `max_file` travaux d'avance (la file ComfyUI les exécute dans l'ordre), récupère au fil de l'eau."""
    import concurrent.futures as cf
    resultats = []

    def un(s):
        try:
            comfy, pid, t0 = soumettre(s, max_file)
            res = attendre(s, comfy, pid, t0)
        except Exception as e:
            res = {"equipe": s.get("equipe"), "nom": s["nom"], "erreur": str(e)[:1500]}
        journaliser(s, res)
        print(json.dumps(res, ensure_ascii=False), flush=True)
        return res

    if not parallele:
        return [un(s) for s in specs]
    with cf.ThreadPoolExecutor(max_workers=max_file) as ex:
        futs = []
        for s in specs:
            futs.append(ex.submit(un, s))
            time.sleep(1.5)  # garder l'ordre de soumission
        for f in futs:
            resultats.append(f.result())
    return resultats


if __name__ == "__main__":
    args = sys.argv[1:]
    mf = 6
    if "--max-file" in args:
        i = args.index("--max-file")
        mf = int(args[i + 1])
        del args[i:i + 2]
    specs = json.loads(Path(args[0]).read_text())
    noms = set(args[1:])
    specs = [s for s in specs if not noms or s["nom"] in noms]
    rendre_tous(specs, mf)
