"""Planches-contact apercu.png : social/ et publicite/ (grille de toutes les pièces, par sous-dossier).
  python3 apercu_familles.py [social|publicite ...]"""
import sys, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RAC = Path(__file__).resolve().parents[2]
CELL, PAD, COLS, W = 176, 10, 13, 2400

def font(n):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p): return ImageFont.truetype(p, n)
    try: return ImageFont.load_default(size=n)
    except TypeError: return ImageFont.load_default()

def sections(final: Path, exclure=()):
    out = {}
    for r, _, fs in os.walk(final):
        for f in sorted(fs):
            if f.lower().endswith((".png", ".jpg")) and not any(x in f for x in exclure):
                rel = Path(r).relative_to(final)
                top = rel.parts[0] if rel.parts else "."
                out.setdefault(top, []).append(Path(r) / f)
    return {k: sorted(v) for k, v in sorted(out.items())}

def planche(final: Path, sortie: Path, titre: str, exclure=()):
    secs = sections(final, exclure)
    big, small = font(26), font(14)
    # hauteur
    ht = 70
    for k, v in secs.items():
        ht += 44 + ((len(v) + COLS - 1) // COLS) * (CELL + PAD) + 18
    img = Image.new("RGB", (W, ht), (10, 10, 14))
    d = ImageDraw.Draw(img)
    d.text((PAD * 2, 20), titre, fill=(245, 244, 239), font=big)
    y = 70
    for k, v in secs.items():
        d.text((PAD * 2, y), f"{k}  ({len(v)})", fill=(255, 122, 69), font=small)
        d.line([(PAD * 2, y + 22), (W - PAD * 2, y + 22)], fill=(50, 50, 60))
        y += 36
        for i, p in enumerate(v):
            try:
                im = Image.open(p)
                if im.mode in ("RGBA", "LA"):
                    bg = Image.new("RGB", im.size, (30, 30, 38)); bg.paste(im, mask=im.split()[-1]); im = bg
                im = im.convert("RGB"); im.thumbnail((CELL, CELL), Image.LANCZOS)
            except Exception:
                continue
            cx = PAD * 2 + (i % COLS) * (CELL + PAD) + (CELL - im.width) // 2
            cy = y + (i // COLS) * (CELL + PAD) + (CELL - im.height) // 2
            img.paste(im, (cx, cy))
        y += ((len(v) + COLS - 1) // COLS) * (CELL + PAD) + 18
    img = img.crop((0, 0, W, y))
    img.save(sortie, optimize=True)
    return sortie

if __name__ == "__main__":
    cibles = sys.argv[1:] or ["social", "publicite"]
    if "social" in cibles:
        print(planche(RAC / "social" / "final", RAC / "social" / "apercu.png", "Nexora AI : lancement, famille SOCIAL (toutes les pièces)", ("reels-cadre",)))
    if "publicite" in cibles:
        print(planche(RAC / "publicite" / "final", RAC / "publicite" / "apercu.png", "Nexora AI : lancement, famille PUBLICITÉ (toutes les pièces)"))
