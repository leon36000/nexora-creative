"""Planche-contact de plans vidéo : 3 images par plan (0,8 s, 2,5 s, 4,3 s), étiquetées. Usage : python3 planche.py sortie.png plan1.mp4 plan2.mp4 …"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
out, fichiers = sys.argv[1], sys.argv[2:]
T = [0.8, 2.5, 4.3]; w, h = 480, 270
feuille = Image.new("RGB", (w * 3, (h + 22) * len(fichiers)), (10, 10, 14))
d = ImageDraw.Draw(feuille)
tmp = tempfile.mkdtemp()
for r, f in enumerate(fichiers):
    d.text((6, r * (h + 22) + 5), Path(f).name, fill=(255, 122, 69))
    for c, t in enumerate(T):
        p = f"{tmp}/x.png"
        subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", f, "-frames:v", "1", "-vf", f"scale={w}:{h}", p], check=False)
        try:
            feuille.paste(Image.open(p), (c * w, r * (h + 22) + 22))
        except Exception:
            pass
feuille.save(out)
