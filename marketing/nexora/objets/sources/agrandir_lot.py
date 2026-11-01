"""Agrandissement x4 (Real-ESRGAN) des photos vierges, puis ramene a 2400 px : generees/<nom>.png -> generees/<nom>_x.png.
Charge le modele une seule fois ; surveille le dossier jusqu'a ce que tous les noms demandes soient traites (ou 25 min sans rien de neuf).
  python3 agrandir_lot.py nom1 nom2 ..."""
import os, sys, subprocess, time
from pathlib import Path
RACINE = Path.home() / "nexora-creative-data"
if os.environ.get("NEXORA_AGRANDIR_INTERNE") != "1":
    env = {**os.environ, "NEXORA_AGRANDIR_INTERNE": "1", "PYTHONPATH": str(RACINE / "engine/upscale-libs")}
    sys.exit(subprocess.run([str(RACINE / "engine/venv/bin/python"), __file__, *sys.argv[1:]], env=env).returncode)
import numpy as np, torch, spandrel
from PIL import Image
D = Path(__file__).resolve().parent / "generees"
m = spandrel.ModelLoader().load_from_file(str(RACINE / "models/upscale_models/RealESRGAN_x4plus.pth")).cuda().eval()

def agrandir(entree, sortie):
    img = Image.open(entree).convert("RGB")
    x = torch.from_numpy(np.asarray(img)).permute(2, 0, 1).float().div(255)[None].cuda()
    _, _, h, w = x.shape
    T, P, S = 512, 24, 4
    out = torch.zeros(1, 3, h * S, w * S)
    with torch.no_grad():
        for y in range(0, h, T):
            for xx in range(0, w, T):
                y0, x0 = max(0, y - P), max(0, xx - P); y1, x1 = min(h, y + T + P), min(w, xx + T + P)
                t = m(x[:, :, y0:y1, x0:x1]).clamp(0, 1).cpu()
                oy, ox = (y - y0) * S, (xx - x0) * S
                hh, ww = min(T, h - y) * S, min(T, w - xx) * S
                out[:, :, y * S:y * S + hh, xx * S:xx * S + ww] = t[:, :, oy:oy + hh, ox:ox + ww]
    res = Image.fromarray((out[0].permute(1, 2, 0).numpy() * 255).round().astype("uint8")).resize((2400, 2400), Image.LANCZOS)
    res.save(sortie)

noms = set(sys.argv[1:]); fait = set(); derniere = time.time()
while fait != noms and time.time() - derniere < 1500:
    for n in sorted(noms - fait):
        f, s = D / f"{n}.png", D / f"{n}_x.png"
        if s.exists(): fait.add(n); continue
        if f.exists() and time.time() - f.stat().st_mtime > 5:
            agrandir(f, s); fait.add(n); derniere = time.time(); print(n, "agrandi", flush=True)
    time.sleep(10)
