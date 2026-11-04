"""Planches de comparaison de vidéos (recherche/25) : six images par vidéo, une rangée par vidéo, ordre des rangées
tiré au hasard (graine fixe) et noté dans cle.json pour que le juge ne sache pas laquelle est laquelle.

    python3 planches.py <dossier-des-mp4> <sortie> <paire1-A,paire1-B> [<paire2-A,paire2-B> ...] [--ffmpeg chemin]

Chaque paire donne deux noms de fichiers (sans .mp4). Sortie : <sortie>/<paire>.jpg, <sortie>/cle.json.
"""
import json
import os
import random
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw


def duree(ffprobe, f):
    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True)
    return float(r.stdout.strip())


def images(ffmpeg, f, n=6, larg=320):
    d = duree(os.path.join(os.path.dirname(ffmpeg), os.path.basename(ffmpeg).replace("ffmpeg", "ffprobe")), f)
    out = []
    with tempfile.TemporaryDirectory() as t:
        for k in range(n):
            p = os.path.join(t, f"{k}.jpg")
            subprocess.run([ffmpeg, "-v", "error", "-ss", f"{d * (k + 0.5) / n:.3f}", "-i", f, "-frames:v", "1", "-vf", f"scale={larg}:-2", p], check=True)
            out.append(Image.open(p).convert("RGB"))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ffmpeg = sys.argv[sys.argv.index("--ffmpeg") + 1] if "--ffmpeg" in sys.argv else "ffmpeg"
    if "--ffmpeg" in sys.argv:
        args.remove(ffmpeg)
    dossier, sortie, paires = args[0], args[1], args[2:]
    os.makedirs(sortie, exist_ok=True)
    rnd = random.Random(2511)
    cle = {}
    for paire in paires:
        a, b = paire.split(",")
        haut, bas = (a, b) if rnd.random() < 0.5 else (b, a)
        vues = {x: images(ffmpeg, os.path.join(dossier, f"{x}.mp4")) for x in (a, b)}
        nom = os.path.commonprefix([a, b]).rstrip("-_") or a
        # Deux planches : l'ordre tiré au hasard puis l'ordre inverse (biais de position du juge).
        for suffixe, (x, y) in (("", (haut, bas)), ("-inv", (bas, haut))):
            w, h = vues[x][0].size
            marge = 28
            c = Image.new("RGB", (w * 6, (h + marge) * 2), (16, 16, 18))
            d = ImageDraw.Draw(c)
            for r, (lettre, cle_v) in enumerate(zip("XY", (x, y))):
                d.text((8, r * (h + marge) + 6), f"Video {lettre}  (6 frames, start to end)", fill=(230, 230, 230))
                for k, im in enumerate(vues[cle_v]):
                    c.paste(im.resize((w, h)), (k * w, r * (h + marge) + marge))
            c.save(os.path.join(sortie, f"{nom}{suffixe}.jpg"), quality=86)
            cle[f"{nom}{suffixe}"] = {"X": x, "Y": y}
    with open(os.path.join(sortie, "cle.json"), "w", encoding="utf-8") as f:
        json.dump(cle, f, indent=1)


if __name__ == "__main__":
    main()
