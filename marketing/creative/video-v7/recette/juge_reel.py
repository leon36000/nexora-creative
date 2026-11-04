"""Juge visuel « prise de vues réelles contre images de synthèse / jeu vidéo » (Gemini 4 Argon par OpenRouter, vision).
Deux usages :
  python3 juge_reel.py paire <A> <B>          compare deux médias, dans les deux ordres (A puis B, B puis A) ; image ou vidéo
  python3 juge_reel.py note <media> [seuil]   note absolue de réalisme 0-10 ; code de sortie 1 si < seuil (relance auto)
Une vidéo est jugée sur 3 images (début, milieu, fin) assemblées. La clé est lue dans ~/Desktop/Deepinfra.env.
"""
import base64
import io
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image

FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
MODELE = "google/gemini-4-argon"
CRITERES = ("photographique", "eclairage_reel", "matieres", "camera_reelle", "aspect_jeu")
NOTE = ("Tu es superviseur des effets visuels d'un long métrage. Cette image (ou ces 3 images d'un même plan) doit passer pour "
        "une PRISE DE VUES RÉELLES (live action) tournée par une vraie caméra, même si le sujet est fantastique. Juge sans pitié "
        "les signes d'images de synthèse ou de jeu vidéo : surfaces lisses ou plastiques, éclairage trop propre ou « lueur » partout, "
        "absence de grain et d'imperfections d'objectif, composition symétrique de jaquette de jeu, échelle incohérente, look Unreal, "
        "sursaturation, aspect maquette. Réponds en JSON : {\"photographique\": 0-10, \"eclairage_reel\": 0-10, \"matieres\": 0-10, "
        "\"camera_reelle\": 0-10, \"aspect_jeu\": 0-10 (10 = on dirait un jeu), \"reel\": 0-10 (note globale de crédibilité live "
        "action), \"defauts\": [\"…\"]}")
PAIRE = ("Tu es superviseur des effets visuels d'un long métrage. Deux médias : le PREMIER puis le SECOND. Lequel passe le mieux "
         "pour une prise de vues réelles (live action) tournée par une vraie caméra, et lequel fait le plus images de synthèse / jeu "
         "vidéo ? Ignore le sujet et le cadrage, juge seulement le réalisme photographique. Réponds en JSON : {\"plus_reel\": "
         "\"premier\"|\"second\", \"ecart\": 0-10, \"reel_premier\": 0-10, \"reel_second\": 0-10, \"raison\": \"une phrase\"}")


def cle():
    for l in open(Path.home() / "Desktop/Deepinfra.env"):
        if ":" in l and l.split(":", 1)[0].strip().lower() == "openrouter":
            return l.split(":", 1)[1].strip()


def image_de(media, largeur=1024):
    p = Path(media)
    if p.suffix.lower() in (".mp4", ".mov", ".webm"):
        dur = float(subprocess.run([FF.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                   capture_output=True, text=True).stdout or 5)
        ims = []
        for t in (0.15 * dur, 0.5 * dur, 0.85 * dur):
            raw = subprocess.run([FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                                 capture_output=True).stdout
            ims.append(Image.open(io.BytesIO(raw)).convert("RGB"))
        w = largeur // 3 * 3
        h = int(ims[0].height * (w / 3) / ims[0].width)
        out = Image.new("RGB", (w, h))
        for i, im in enumerate(ims):
            out.paste(im.resize((w // 3, h)), (i * w // 3, 0))
    else:
        out = Image.open(p).convert("RGB")
        out.thumbnail((largeur, largeur))
    b = io.BytesIO()
    out.save(b, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def demander(contenu, temperature=0.0):
    corps = {"model": MODELE, "temperature": temperature, "response_format": {"type": "json_object"},
             "messages": [{"role": "user", "content": contenu}]}
    r = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(corps).encode(),
                               headers={"Authorization": "Bearer " + cle(), "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=240) as x:
        j = json.loads(x.read())
    t = j["choices"][0]["message"]["content"]
    return json.loads(t[t.find("{"): t.rfind("}") + 1])


def note(media):
    return demander([{"type": "image_url", "image_url": {"url": image_de(media)}}, {"type": "text", "text": NOTE}])


def paire(a, b):
    ia, ib = image_de(a), image_de(b)
    r1 = demander([{"type": "text", "text": "PREMIER :"}, {"type": "image_url", "image_url": {"url": ia}},
                   {"type": "text", "text": "SECOND :"}, {"type": "image_url", "image_url": {"url": ib}}, {"type": "text", "text": PAIRE}])
    r2 = demander([{"type": "text", "text": "PREMIER :"}, {"type": "image_url", "image_url": {"url": ib}},
                   {"type": "text", "text": "SECOND :"}, {"type": "image_url", "image_url": {"url": ia}}, {"type": "text", "text": PAIRE}])
    gagne_a = (r1["plus_reel"] == "premier") + (r2["plus_reel"] == "second")
    return {"a": str(a), "b": str(b), "victoires_a": gagne_a, "victoires_b": 2 - gagne_a,
            "reel_a": (r1["reel_premier"] + r2["reel_second"]) / 2, "reel_b": (r1["reel_second"] + r2["reel_premier"]) / 2,
            "coherent": gagne_a in (0, 2), "raisons": [r1.get("raison"), r2.get("raison")]}


if __name__ == "__main__":
    if sys.argv[1] == "paire":
        print(json.dumps(paire(sys.argv[2], sys.argv[3]), ensure_ascii=False))
    else:
        n = note(sys.argv[2])
        print(json.dumps(n, ensure_ascii=False))
        sys.exit(1 if len(sys.argv) > 3 and n.get("reel", 0) < float(sys.argv[3]) else 0)
