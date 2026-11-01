"""Recadre les plans générés pour les bannières IAB (JPG légers, ×2 pour les écrans denses).
  python3 images_bannieres.py   -> publicite/sources/bannieres-img/<plan>-<L>x<H>.jpg"""
import sys, json
from pathlib import Path
from PIL import Image, ImageFilter
RAC = Path(__file__).resolve().parents[2] / "social" / "sources" / "generees"
SORTIE = Path(__file__).resolve().parent / "bannieres-img"
SORTIE.mkdir(exist_ok=True)
tailles = [(300,250),(336,280),(728,90),(970,250),(160,600),(300,600),(320,50),(320,100),(468,60)]
def recadrer(src, w, h, fx, fy, q):
    im = Image.open(src).convert("RGB")
    W, H = w * 2, h * 2
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = min(max(round(fx * im.width - W / 2), 0), im.width - W)
    y = min(max(round(fy * im.height - H / 2), 0), im.height - H)
    return im.crop((x, y, x + W, y + H))
for w, h in tailles:
    tall = h > w * 1.5
    src = RAC / ("aurore-vertical.png" if tall and (RAC / "aurore-vertical.png").exists() else "aurore-foret.png")
    fx, fy = (0.5, 0.45) if src.name == "aurore-vertical.png" else (0.55, 0.38)
    im = recadrer(src, w, h, fx, fy, 60)
    q = 68 if w * h > 60000 else 72
    im.save(SORTIE / f"aurore-{w}x{h}.jpg", quality=q, optimize=True, progressive=True)
print("ok")
