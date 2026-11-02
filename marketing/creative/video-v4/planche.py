"""Planche contact : images (ou vidéos : 3 images réparties) en grille, légendées. Usage : python3 planche.py sortie.jpg fichiers..."""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
L = 480


def vignettes(f):
    f = Path(f).expanduser()
    if f.suffix.lower() in (".mp4", ".mov", ".webm"):
        out = []
        for k, t in enumerate((0.3, 2.5, 4.8)):
            r = subprocess.run([FFMPEG, "-v", "error", "-ss", str(t), "-i", str(f), "-frames:v", "1", "-vf", f"scale={L}:-2",
                                "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
            if r.stdout:
                from io import BytesIO
                out.append((Image.open(BytesIO(r.stdout)).convert("RGB"), f"{f.stem} @{t}s"))
        return out
    im = Image.open(f).convert("RGB")
    im.thumbnail((L, L * 2))
    return [(im, f.stem)]


if __name__ == "__main__":
    tout = [v for f in sys.argv[2:] for v in vignettes(f)]
    col = 3
    h = max(im.height for im, _ in tout) + 18
    page = Image.new("RGB", (col * L, h * (-(-len(tout) // col))), (20, 20, 20))
    d = ImageDraw.Draw(page)
    for i, (im, nom) in enumerate(tout):
        x, y = (i % col) * L, (i // col) * h
        page.paste(im, (x, y + 18))
        d.text((x + 4, y + 3), nom, fill=(255, 200, 120))
    page.save(sys.argv[1], quality=85)
