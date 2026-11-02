"""Client ComfyUI de la promo V3 : rendus MiniMax H3 (RTX 5090 de pc1, tunnel 37288) et images Qwen-Image-2.1 (GB10, 37188).

Les graphes reprennent ceux du studio (app/server/graphs/h3.ts, stills.ts) avec en plus le réglage du décalage sigma et de
l'échantillonneur, nécessaire pour les points de contrôle turbo (FastH3, 10Eros-Max). Une file partagée : on soumet
normalement et on attend, sans jamais passer devant les travaux des autres.

Usage : python3 moteur.py specs.json [nom ...]   (un tableau de specs ; seuls les noms donnés si présents)
Spec H3   : {"type": "h3", "nom", "prompt", "checkpoint", "etapes", "decalage": [12, 3] | null, "echantillonneur",
             "ref": bool, "image": "chemin.png" | null, "largeur", "hauteur", "images", "graine", "sortie"}
Spec image: {"type": "image", "nom", "prompt", "negatif", "largeur", "hauteur", "graine", "sortie"}
Sortie : une ligne JSON par rendu (secondes moteur, fichier) ajoutée au journal <sortie>/rendus.jsonl.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

H3_COMFY = "http://127.0.0.1:37288"
IMG_COMFY = "http://127.0.0.1:37188"
CLIP_H3 = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"


def http(url: str, data: bytes | None = None, headers: dict | None = None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def envoyer_image(comfy: str, chemin: str) -> str:
    limite = uuid.uuid4().hex
    corps = (f"--{limite}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{Path(chemin).name}\"\r\n"
             f"Content-Type: image/png\r\n\r\n").encode() + Path(chemin).read_bytes() + \
        f"\r\n--{limite}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{limite}--\r\n".encode()
    r = json.loads(http(f"{comfy}/upload/image", corps, {"Content-Type": f"multipart/form-data; boundary={limite}"}))
    return r["name"]


def graphe_h3(s: dict, image: str | None) -> dict:
    turbo = s.get("decalage")
    src = "shift" if turbo else "u"
    g = {
        "u": {"class_type": "UNETLoader", "inputs": {"unet_name": s["checkpoint"], "weight_dtype": "default"}},
        "c": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP_H3, "type": "minimax", "device": "default"}},
        "vv": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "va": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "sampler": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": s.get("echantillonneur", "res_multistep")}},
        "sched": {"class_type": "BasicScheduler", "inputs": {"model": [src, 0], "scheduler": "simple", "steps": s["etapes"], "denoise": 1.0}},
        "noise": {"class_type": "RandomNoise", "inputs": {"noise_seed": s.get("graine", 42)}},
        "guider": {"class_type": "BasicGuider", "inputs": {"model": [src, 0], "conditioning": ["gen", 0]}},
        "sca": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["noise", 0], "guider": ["guider", 0], "sampler": ["sampler", 0],
                                                                  "sigmas": ["sched", 0], "latent_image": ["gen", 1]}},
        "dv": {"class_type": "VAEDecode", "inputs": {"samples": ["sca", 0], "vae": ["vv", 0]}},
        "da": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["sca", 0], "vae": ["va", 0]}},
        "vid": {"class_type": "CreateVideo", "inputs": {"images": ["dv", 0], "audio": ["da", 0], "fps": 24}},
        "save": {"class_type": "SaveVideo", "inputs": {"video": ["vid", 0], "filename_prefix": f"nexora-promo-v3/{s['nom']}", "format": "auto", "codec": "auto"}},
    }
    if turbo:
        g["shift"] = {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["u", 0], "shift_video": turbo[0], "shift_audio": turbo[1]}}
    gen = {"clip": ["c", 0], "vae": ["vv", 0], "prompt": s["prompt"], "width": s.get("largeur", 1344), "height": s.get("hauteur", 768),
           "length": s.get("images", 124)}
    if s.get("ref"):
        gen["audio_vae"] = ["va", 0]
        gen["ref_image_size"] = "match"
        if image:
            g["ref0"] = {"class_type": "LoadImage", "inputs": {"image": image}}
            gen["ref_images.ref_image_0"] = ["ref0", 0]
        g["gen"] = {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": gen}
    else:
        if image:
            g["ls"] = {"class_type": "LoadImage", "inputs": {"image": image}}
            g["ss"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["ls", 0], "upscale_method": "lanczos",
                                                                          "megapixels": gen["width"] * gen["height"] / 1e6, "resolution_steps": 32}}
            gen["first_frame"] = ["ss", 0]
        g["gen"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": gen}
    return g


def graphe_image(s: dict) -> dict:
    return {
        "u": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_int8_convrot.safetensors", "weight_dtype": "default"}},
        "cache": {"class_type": "QwenImage21Cache", "inputs": {"model": ["u", 0], "device": "auto", "dtype": "default"}},
        "c": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_8b_int8_convrot.safetensors", "type": "qwen_image", "device": "default"}},
        "v": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
        "enc": {"class_type": "TextEncodeQwenImage21", "inputs": {"clip": ["c", 0], "prompt": s["prompt"], "negative_prompt": s.get("negatif", ""), "resolution": 1024}},
        "lat": {"class_type": "EmptyLatentImage", "inputs": {"width": s.get("largeur", 1664), "height": s.get("hauteur", 928), "batch_size": 1}},
        "k": {"class_type": "KSampler", "inputs": {"model": ["cache", 0], "positive": ["enc", 0], "negative": ["enc", 1], "latent_image": ["lat", 0],
                                                   "seed": s.get("graine", 1), "steps": s.get("etapes", 25), "cfg": 1, "sampler_name": "euler",
                                                   "scheduler": "simple", "denoise": 1.0}},
        "d": {"class_type": "VAEDecode", "inputs": {"samples": ["k", 0], "vae": ["v", 0]}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["d", 0], "filename_prefix": f"nexora-promo-v3/{s['nom']}"}},
    }


def rendre(s: dict) -> dict:
    video = s.get("type", "h3") == "h3"
    comfy = s.get("comfy", H3_COMFY if video else IMG_COMFY)
    if video:
        image = envoyer_image(comfy, str(Path(s["image"]).expanduser())) if s.get("image") else None
        g = graphe_h3(s, image)
    else:
        g = graphe_image(s)
    t0 = time.time()
    pid = json.loads(http(f"{comfy}/prompt", json.dumps({"prompt": g}).encode(), {"Content-Type": "application/json"}))["prompt_id"]
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
        local = sortie / f"{s['nom']}{Path(f['filename']).suffix}"
        local.write_bytes(data)
        moteur = None
        if ts.get("execution_start") and ts.get("execution_success"):
            moteur = round((ts["execution_success"] - ts["execution_start"]) / 1000, 1)
        return {"nom": s["nom"], "checkpoint": s.get("checkpoint"), "etapes": s.get("etapes"), "graine": s.get("graine"),
                "secondesMoteur": moteur, "secondesTotal": round(time.time() - t0, 1), "fichier": str(local)}


if __name__ == "__main__":
    specs = json.loads(Path(sys.argv[1]).read_text())
    noms = set(sys.argv[2:])
    for s in specs:
        if noms and s["nom"] not in noms:
            continue
        try:
            res = rendre(s)
        except Exception as e:  # un échec n'arrête pas la série
            res = {"nom": s["nom"], "erreur": str(e)[:1500]}
        print(json.dumps(res, ensure_ascii=False), flush=True)
        journal = Path(s["sortie"]).expanduser() / "rendus.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        with journal.open("a") as fh:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
