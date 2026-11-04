"""Planche contact d'un rendu : une image par seconde (ou par pas donné), 480 px de large, horodatée.

  python3 planche.py <video> <sortie.jpg> [pas_s=1] [colonnes=8]
"""
import subprocess
import sys

from PIL import Image, ImageDraw

import commun as C


def planche(video, sortie, pas=1.0, cols=8, larg=480):
    d = C.duree(video)
    ims = []
    t = 0.2
    while t < d:
        b = subprocess.run([C.FF, "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf", f"scale={larg}:-2",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        if b:
            import io
            ims.append((t, Image.open(io.BytesIO(b)).convert("RGB")))
        t += pas
    w, h = ims[0][1].size
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (cols * w, rows * (h + 16)), (24, 24, 24))
    dr = ImageDraw.Draw(sh)
    for i, (t, im) in enumerate(ims):
        x, y = (i % cols) * w, (i // cols) * (h + 16)
        sh.paste(im, (x, y + 16))
        dr.text((x + 3, y + 2), f"{t:.1f}s", fill=(255, 190, 0))
    sh.save(sortie, quality=82)
    return sortie


if __name__ == "__main__":
    a = sys.argv[1:]
    planche(a[0], a[1], float(a[2]) if len(a) > 2 else 1.0, int(a[3]) if len(a) > 3 else 8)
