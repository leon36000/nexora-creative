"""Auto-revue d'un film V4 : planche (une image par segment, au milieu, + vignette 480 px de large pour la lisibilité),
volume intégré et crête, coupes. Usage : python3 revue_v4.py montage-v4.json film.mp4 planche.jpg [--petit]"""
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")


def image(film, t, largeur):
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", film, "-frames:v", "1", "-vf", f"scale={largeur}:-2",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    return Image.open(BytesIO(r.stdout)).convert("RGB")


if __name__ == "__main__":
    m, film, sortie = sys.argv[1:4]
    L = 480 if "--petit" in sys.argv else 640
    v = json.loads(Path(m).read_text())["versions"]["long"]
    t, pts = 0.0, []
    for s in v["segments"]:
        pts.append((t + s["d"] * (0.7 if s["type"] in ("fin", "ab") else 0.5), s["nom"]))
        t += s["d"]
    ims = [(image(film, x, L), f"{n} {x:.1f}s") for x, n in pts]
    col = 4
    h = ims[0][0].height + 16
    page = Image.new("RGB", (col * L, h * (-(-len(ims) // col))), (30, 30, 30))
    d = ImageDraw.Draw(page)
    for i, (im, n) in enumerate(ims):
        page.paste(im, ((i % col) * L, (i // col) * h + 16))
        d.text(((i % col) * L + 4, (i // col) * h + 2), n, fill=(255, 190, 120))
    page.save(sortie, quality=82)
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", film, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    res = r.stderr[r.stderr.rfind("Summary"):]
    print(" ".join(x.strip() for x in res.splitlines() if x.strip().startswith(("I:", "Peak:", "LRA:"))))
