"""Planche-contact : python3 planche.py sortie.png colonnes largeur_vignette fichier|dossier ... [--titre "..."] [--filtre sous-chaine]
Chaque vignette est étiquetée du nom de fichier. Les dossiers sont parcourus (png/jpg), triés par chemin."""
import sys, os
from PIL import Image, ImageDraw, ImageFont

def lister(args, filtre=None):
    out = []
    for a in args:
        if os.path.isdir(a):
            for r, _, fs in os.walk(a):
                for f in fs:
                    if f.lower().endswith((".png", ".jpg", ".jpeg")) and (not filtre or filtre in os.path.join(r, f)):
                        out.append(os.path.join(r, f))
        elif os.path.exists(a):
            out.append(a)
    return sorted(out)

def planche(sortie, cols, cw, fichiers, titre=None, fond=(14, 14, 18)):
    try:
        police = ImageFont.load_default(size=13)
        grand = ImageFont.load_default(size=22)
    except TypeError:
        police = grand = ImageFont.load_default()
    pad, hl = 14, 22
    vigs = []
    for f in fichiers:
        im = Image.open(f).convert("RGB")
        ch = max(1, round(cw * im.height / im.width))
        vigs.append((os.path.basename(f), im.resize((cw, ch), Image.LANCZOS)))
    # rangées à hauteur propre
    rangs = [vigs[i:i + cols] for i in range(0, len(vigs), cols)]
    ht = (36 if titre else 0) + sum(max(v[1].height for v in r) + hl + pad for r in rangs) + pad
    W = cols * (cw + pad) + pad
    img = Image.new("RGB", (W, ht), fond)
    d = ImageDraw.Draw(img)
    y = pad
    if titre:
        d.text((pad, y - 6), titre, fill=(245, 244, 239), font=grand)
        y += 36
    for r in rangs:
        mh = max(v[1].height for v in r)
        for i, (nom, im) in enumerate(r):
            x = pad + i * (cw + pad)
            img.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + cw, y + im.height], outline=(60, 60, 70))
            d.text((x, y + mh + 4), nom[:60], fill=(168, 168, 182), font=police)
        y += mh + hl + pad
    img.save(sortie)
    return sortie

if __name__ == "__main__":
    a = sys.argv[1:]
    sortie, cols, cw = a[0], int(a[1]), int(a[2])
    titre = filtre = None
    rest = []
    i = 3
    while i < len(a):
        if a[i] == "--titre": titre = a[i + 1]; i += 2
        elif a[i] == "--filtre": filtre = a[i + 1]; i += 2
        else: rest.append(a[i]); i += 1
    planche(sortie, cols, cw, lister(rest, filtre), titre)
    print(sortie)
