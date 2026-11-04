#!/usr/bin/env python3
"""Une vignette par seconde, horodatée, sans extraction d'images sur disque."""
import argparse
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from PIL import Image, ImageDraw

from monter_v6 import ICI, chemin, ecriture, ff, police, sonder


def planche(video, jpg, colonnes=4):
    video = chemin(video, Path.cwd())
    meta = sonder(str(video))
    v = next(s for s in meta["streams"] if s["codec_type"] == "video")
    duree = float(meta["format"]["duration"])
    n = max(1, math.ceil(duree-1e-4))
    tw = 320 if v["width"] >= v["height"] else 180
    th = round(tw*v["height"]/v["width"])
    colonnes = min(colonnes, n)
    bande, marge = 30, 8
    # Police déclarée dans la marque, comme le moteur. Les horodatages sont des données.
    import json
    b = json.loads((ICI/"marque-v6.json").read_text())
    feuille = Image.new("RGB", (colonnes*(tw+marge)+marge, math.ceil(n/colonnes)*(th+bande+marge)+marge), tuple(b["couleurs"]["encre"]))
    font = police(str(chemin(b["polices"]["mono"])), 15, 500)
    for sec in range(n):
        raw = ff(["-threads", "1", "-ss", sec, "-i", video, "-frames:v", "1", "-vf", f"scale={tw}:{th}:flags=lanczos", "-threads", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]).stdout
        if len(raw) != tw*th*3:
            raise ValueError(f"Image manquante à {sec}s")
        im = Image.frombytes("RGB", (tw, th), raw)
        x, y = marge+(sec % colonnes)*(tw+marge), marge+(sec//colonnes)*(th+bande+marge)
        feuille.paste(im, (x, y))
        ImageDraw.Draw(feuille).text((x+6, y+th+6), f"{sec//60:02d}:{sec%60:02d}", font=font, fill=tuple(b["couleurs"]["os"]))
    jpg = ecriture(jpg)
    feuille.save(jpg, quality=90)
    print(jpg)
    return jpg


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mp4")
    p.add_argument("jpg")
    p.add_argument("--colonnes", type=int, default=4)
    a = p.parse_args()
    if a.colonnes < 1:
        p.error("--colonnes doit être positif")
    planche(a.mp4, a.jpg, a.colonnes)
