"""Planche des plans verticaux : une ligne par plan, v1 et v2 côte à côte (images à 1 s et 3,5 s)."""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
dossier, sortie, noms = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
w, h = 180, 320
feuille = Image.new("RGB", (w * 4 * 1, (h + 18) * len(noms)), (10, 10, 14)); d = ImageDraw.Draw(feuille)
tmp = tempfile.mkdtemp()
for r, nom in enumerate(noms):
    for v in (1, 2):
        for k, t in enumerate((1.0, 3.5)):
            c = (v - 1) * 2 + k
            f = dossier / f"{nom}-v{v}.mp4"
            if not f.exists(): continue
            subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", str(f), "-frames:v", "1", "-vf", f"scale={w}:{h}", f"{tmp}/x.png"])
            try: feuille.paste(Image.open(f"{tmp}/x.png"), (c * w, r * (h + 18) + 18))
            except Exception: pass
    d.text((4, r * (h + 18) + 3), nom + "  (v1 | v2)", fill=(255, 122, 69))
feuille.save(sortie)
