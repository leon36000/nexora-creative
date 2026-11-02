"""Review contact sheets: python3 planche.py out.jpg file1 [file2 ...] [--images N] [--largeur 1800]
Image -> one tile; video -> a row of N frames spread across the duration (labelled with the name and the time)."""
import argparse, subprocess, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FFPROBE = str(Path(FFMPEG).with_name("ffprobe"))


def duree(f):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(f)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def image_a(f, t):
    r = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", str(f), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True)
    from io import BytesIO
    return Image.open(BytesIO(r.stdout)).convert("RGB")


def planche(sortie, fichiers, n=5, largeur=1800):
    rangs = []
    for f in fichiers:
        f = Path(f)
        if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            ims, eti = [Image.open(f).convert("RGB")], [f.name]
        else:
            d = duree(f)
            ts = [d * (k + 0.5) / n for k in range(n)]
            ims, eti = [image_a(f, t) for t in ts], [f"{f.stem} {t:.1f}s" for t in ts]
        rangs.append((ims, eti))
    cols = max(len(r[0]) for r in rangs)
    tw = largeur // cols
    lignes = []
    for ims, eti in rangs:
        th = max(round(tw * im.height / im.width) for im in ims)
        L = Image.new("RGB", (largeur, th + 2), (20, 20, 20))
        d = ImageDraw.Draw(L)
        for k, (im, e) in enumerate(zip(ims, eti)):
            im = im.resize((tw - 2, round((tw - 2) * im.height / im.width)))
            L.paste(im, (k * tw, 0))
            d.text((k * tw + 6, 4), e, fill=(255, 255, 0))
        lignes.append(L)
    H = sum(l.height for l in lignes)
    P = Image.new("RGB", (largeur, H), (0, 0, 0))
    y = 0
    for l in lignes:
        P.paste(l, (0, y)); y += l.height
    P.save(sortie, quality=85)
    return sortie


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("sortie"); a.add_argument("fichiers", nargs="+")
    a.add_argument("--images", type=int, default=5); a.add_argument("--largeur", type=int, default=1800)
    o = a.parse_args()
    print(planche(o.sortie, o.fichiers, o.images, o.largeur))
