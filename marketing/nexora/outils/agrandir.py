"""Agrandissement ×4 (Real-ESRGAN x4plus, sur le GPU de pc6) pour l'impression, puis redimensionnement exact.

  python3 agrandir.py entree.png sortie.png [--largeur 4800] [--hauteur 7200]

Sans --largeur/--hauteur : ×4. Avec : l'image ×4 est ramenée (Lanczos) à la taille demandée. Lance le modèle dans le
venv de ComfyUI (torch + CUDA) avec spandrel installé à part (engine/upscale-libs). Tuiles de 512 px pour borner la mémoire.
"""
import argparse, os, subprocess, sys
from pathlib import Path

RACINE = Path.home() / "nexora-creative-data"
if os.environ.get("NEXORA_AGRANDIR_INTERNE") != "1":
    env = {**os.environ, "NEXORA_AGRANDIR_INTERNE": "1", "PYTHONPATH": str(RACINE / "engine/upscale-libs")}
    sys.exit(subprocess.run([str(RACINE / "engine/venv/bin/python"), __file__, *sys.argv[1:]], env=env).returncode)

import numpy as np, torch, spandrel
from PIL import Image

a = argparse.ArgumentParser()
a.add_argument("entree"); a.add_argument("sortie")
a.add_argument("--largeur", type=int); a.add_argument("--hauteur", type=int)
o = a.parse_args()
m = spandrel.ModelLoader().load_from_file(str(RACINE / "models/upscale_models/RealESRGAN_x4plus.pth")).cuda().eval()
img = Image.open(o.entree).convert("RGB")
x = torch.from_numpy(np.asarray(img)).permute(2, 0, 1).float().div(255)[None].cuda()
_, _, h, w = x.shape
T, P, S = 512, 24, 4
sortie = torch.zeros(1, 3, h * S, w * S)
with torch.no_grad():
    for y in range(0, h, T):
        for xx in range(0, w, T):
            y0, x0 = max(0, y - P), max(0, xx - P)
            y1, x1 = min(h, y + T + P), min(w, xx + T + P)
            t = m(x[:, :, y0:y1, x0:x1]).clamp(0, 1).cpu()
            oy, ox = (y - y0) * S, (xx - x0) * S
            hh, ww = min(T, h - y) * S, min(T, w - xx) * S
            sortie[:, :, y * S:y * S + hh, xx * S:xx * S + ww] = t[:, :, oy:oy + hh, ox:ox + ww]
res = Image.fromarray((sortie[0].permute(1, 2, 0).numpy() * 255).round().astype("uint8"))
if o.largeur or o.hauteur:
    lw = o.largeur or round(res.width * o.hauteur / res.height)
    lh = o.hauteur or round(res.height * o.largeur / res.width)
    res = res.resize((lw, lh), Image.LANCZOS)
Path(o.sortie).parent.mkdir(parents=True, exist_ok=True)
res.save(o.sortie)
print(o.sortie, res.size)
