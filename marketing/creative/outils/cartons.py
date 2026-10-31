"""Cartons de la bande-annonce Nexora Creative, dessinés image par image (PIL) puis encodés par ffmpeg.

- « saisie » : le champ de Nexora Creative où une phrase en français se tape toute seule, puis le bouton « Tourner »
  s'allume ; c'est la promesse du produit montrée avant chaque scène.
- « logo » : la mosaïque « braise » de Nexora qui se calcule en logo, le slogan et les mentions obligatoires.

Usage : python3 cartons.py saisie "<phrase>" sortie.mp4 [durée_s]
        python3 cartons.py logo sortie.mp4 [durée_s]
Polices : Geist et Inter (SIL OFL 1.1), lues dans le dépôt du site (lecture seule).
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

L, H, IPS = 1920, 1080, 24
FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
POLICES = Path.home() / "Desktop/NexoraSite/web/src/fonts"
ENCRE, SURFACE, FILET = (10, 10, 14), (18, 18, 24), (43, 43, 56)
OS, BRUME, SIGNAL = (245, 244, 239), (168, 168, 182), (255, 90, 31)
BRAISE = [(255, 211, 122), (255, 177, 26), (255, 138, 31), (255, 90, 31), (224, 52, 28), (176, 26, 60)]


def police(nom: str, taille: int, graisse: bytes = b"Regular") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(POLICES / nom), taille)
    f.set_variation_by_name(graisse)
    return f


def hache(c: int, r: int, s: int) -> float:
    h = ((c + 1) * 73856093 ^ (r + 1) * 19349663 ^ (s + 1) * 83492791) & 0xFFFFFFFF
    h = ((h ^ (h >> 15)) * 2246822507) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 3266489909) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967296


def mosaique(d: ImageDraw.ImageDraw, x0, y0, l, h, taille, seuil, graine, avance):
    cols, rows = math.ceil(l / taille), math.ceil(h / taille)
    for c in range(cols):
        for r in range(rows):
            a = avance(c / max(1, cols - 1), r / max(1, rows - 1))
            k = hache(c, r, graine)
            if k > a - seuil:
                continue
            teinte = BRAISE[min(5, int(a * 6 * (0.6 + 0.4 * k)))]
            d.rectangle([x0 + c * taille, y0 + r * taille, x0 + (c + 1) * taille - 2, y0 + (r + 1) * taille - 2], fill=teinte)


def lignes(texte: str, f: ImageFont.FreeTypeFont, largeur: int) -> list[str]:
    mots, out, cur = texte.split(), [], ""
    for m in mots:
        essai = f"{cur} {m}".strip()
        if f.getlength(essai) <= largeur:
            cur = essai
        else:
            out.append(cur)
            cur = m
    if cur:
        out.append(cur)
    return out


def encoder(images, sortie: str):
    p = subprocess.Popen(
        [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L}x{H}", "-r", str(IPS), "-i", "-",
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", sortie],
        stdin=subprocess.PIPE,
    )
    for im in images:
        p.stdin.write(im.tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit("ffmpeg a échoué")


def saisie(phrase: str, sortie: str, duree: float = 2.0):
    n = round(duree * IPS)
    f_txt = police("geist-latin-wght-normal.woff2", 62, b"Medium")
    f_eti = police("inter-latin-wght-normal.woff2", 22, b"Medium")
    f_bt = police("inter-latin-wght-normal.woff2", 28, b"SemiBold")
    lx, ly, ll, lh = 240, 360, 1440, 360  # champ de saisie
    frappe = int(n * 0.72)  # la phrase est tapée sur 72 % du carton, puis « Tourner » s'allume
    images = []
    for i in range(n):
        im = Image.new("RGB", (L, H), ENCRE)
        d = ImageDraw.Draw(im)
        mosaique(d, 1920 - 420, 0, 420, 240, 30, 0.0, 11, lambda x, y: max(0.0, x * 1.4 - 0.4 - y * 0.6))
        d.rounded_rectangle([lx, ly, lx + ll, ly + lh], radius=10, fill=SURFACE, outline=FILET, width=2)
        d.text((lx + 48, ly + 40), "NEXORA CREATIVE  ·  DÉCRIS TA SCÈNE", font=f_eti, fill=SIGNAL)
        k = min(len(phrase), round(len(phrase) * min(1.0, i / max(1, frappe))))
        texte = phrase[:k]
        y = ly + 100
        lgn = lignes(texte, f_txt, ll - 96) or [""]
        for j, ligne in enumerate(lgn[-3:]):
            d.text((lx + 48, y + j * 80), ligne, font=f_txt, fill=OS)
        if (i // 6) % 2 == 0 or k < len(phrase):
            dernier = lgn[-3:][-1]
            cx = lx + 48 + f_txt.getlength(dernier) + 6
            cy = y + (len(lgn[-3:]) - 1) * 80
            d.rectangle([cx, cy + 10, cx + 6, cy + 72], fill=SIGNAL)
        allume = i >= frappe
        bx0, by0 = lx + ll - 268, ly + lh - 96
        d.rounded_rectangle([bx0, by0, bx0 + 220, by0 + 60], radius=8, fill=SIGNAL if allume else FILET)
        d.text((bx0 + 110, by0 + 30), "Tourner", font=f_bt, fill=ENCRE if allume else BRUME, anchor="mm")
        images.append(im)
    encoder(images, sortie)


def logo(sortie: str, duree: float = 5.0):
    n = round(duree * IPS)
    f_nom = police("geist-latin-wght-normal.woff2", 150, b"SemiBold")
    f_slo = police("geist-latin-wght-normal.woff2", 58, b"Medium")
    f_pet = police("inter-latin-wght-normal.woff2", 26, b"Regular")
    images = []
    for i in range(n):
        t = i / max(1, n - 1)
        im = Image.new("RGB", (L, H), ENCRE)
        d = ImageDraw.Draw(im)
        # La mosaïque se calcule (0 → 35 % du carton), puis se dissout (35 → 55 %) et laisse le nom sur fond net ;
        # il reste la petite mosaïque d'angle du site.
        if t < 0.35:
            seuil = 1.2 - t / 0.35 * 1.2
        else:
            seuil = (t - 0.35) / 0.2 * 1.3
        if seuil < 1.25:
            mosaique(d, 0, 0, L, H, 40, seuil, 5, lambda x, y: 1 - abs(x - 0.5) * 0.9 - abs(y - 0.5) * 0.5)
        if t > 0.5:
            mosaique(d, L - 480, 0, 480, 280, 34, max(0.0, 0.6 - (t - 0.5) * 3), 11, lambda x, y: max(0.0, x * 1.4 - 0.4 - y * 0.6))
        if t > 0.5:
            a = min(1.0, (t - 0.5) / 0.12)
            col = tuple(int(ENCRE[k] + (OS[k] - ENCRE[k]) * a) for k in range(3))
            sig = tuple(int(ENCRE[k] + (SIGNAL[k] - ENCRE[k]) * a) for k in range(3))
            larg = f_nom.getlength("NEXORA CREATIVE")
            x = (L - larg) / 2
            d.text((x, 380), "NEXORA", font=f_nom, fill=col)
            d.text((x + f_nom.getlength("NEXORA "), 380), "CREATIVE", font=f_nom, fill=sig)
            d.text((L / 2, 610), "Écris-le. Nexora le filme.", font=f_slo, fill=col, anchor="mm")
        if t > 0.62:
            a = min(1.0, (t - 0.62) / 0.12)
            pet = tuple(int(ENCRE[k] + (BRUME[k] - ENCRE[k]) * a) for k in range(3))
            d.text((L / 2, 760), "Bientôt dans ton espace Nexora", font=f_pet, fill=pet, anchor="mm")
            d.text((L / 2, 1010), "Images et sons 100 % générés par IA avec Nexora Creative  ·  MiniMax H3  ·  MiniMax-Music3",
                   font=f_pet, fill=pet, anchor="mm")
        images.append(im)
    encoder(images, sortie)


def logo_impact(sortie: str, duree: float = 6.0):
    """Logo calé sur un impact de musique : la mosaïque pleine éclate à la première image (flash blanc), se dissout en
    1,6 s et laisse le nom, le slogan et les mentions ; fondu au noir sur la dernière seconde."""
    n = round(duree * IPS)
    f_nom = police("geist-latin-wght-normal.woff2", 150, b"SemiBold")
    f_slo = police("geist-latin-wght-normal.woff2", 58, b"Medium")
    f_pet = police("inter-latin-wght-normal.woff2", 26, b"Regular")
    images = []
    for i in range(n):
        s_ = i / IPS
        im = Image.new("RGB", (L, H), ENCRE)
        d = ImageDraw.Draw(im)
        seuil = -0.35 + min(1.0, max(0.0, (s_ - 0.1) / 0.95)) * 1.6  # dense à l'impact, vide à 1,05 s
        if seuil < 1.2:
            mosaique(d, 0, 0, L, H, 40, seuil, 5, lambda x, y: 1 - abs(x - 0.5) * 0.9 - abs(y - 0.5) * 0.5)
        a = min(1.0, max(0.0, (s_ - 1.05) / 0.4))
        mix = lambda c: tuple(int(ENCRE[k] + (c[k] - ENCRE[k]) * a) for k in range(3))
        if a > 0:
            larg = f_nom.getlength("NEXORA CREATIVE")
            x = (L - larg) / 2
            d.text((x, 380), "NEXORA", font=f_nom, fill=mix(OS))
            d.text((x + f_nom.getlength("NEXORA "), 380), "CREATIVE", font=f_nom, fill=mix(SIGNAL))
            d.text((L / 2, 610), "Écris-le. Nexora le filme.", font=f_slo, fill=mix(OS), anchor="mm")
        b = min(1.0, max(0.0, (s_ - 2.0) / 0.5))
        if b > 0:
            pet = tuple(int(ENCRE[k] + (BRUME[k] - ENCRE[k]) * b) for k in range(3))
            d.text((L / 2, 760), "Bientôt dans ton espace Nexora", font=f_pet, fill=pet, anchor="mm")
            d.text((L / 2, 1010), "Images et sons 100 % générés par IA avec Nexora Creative  ·  MiniMax H3  ·  MiniMax-Music3",
                   font=f_pet, fill=pet, anchor="mm")
        if s_ < 0.12:  # flash de l'impact
            k = 1 - s_ / 0.12
            im = Image.blend(im, Image.new("RGB", (L, H), (255, 255, 255)), 0.85 * k)
        if s_ > duree - 1.0:  # fondu au noir final
            im = Image.blend(im, Image.new("RGB", (L, H), ENCRE), min(1.0, (s_ - (duree - 1.0)) / 1.0))
        images.append(im)
    encoder(images, sortie)


def texte(phrase: str, sortie: str, duree: float = 2.0):
    """Phrase plein écran qui apparaît mot à mot, en Geist, sur le noir encre."""
    n = round(duree * IPS)
    f = police("geist-latin-wght-normal.woff2", 96, b"SemiBold")
    mots = phrase.split()
    images = []
    for i in range(n):
        t = i / max(1, n - 1)
        im = Image.new("RGB", (L, H), ENCRE)
        d = ImageDraw.Draw(im)
        k = min(len(mots), 1 + int(t / 0.55 * len(mots)))
        lgn = lignes(" ".join(mots), f, 1500)
        y0 = H / 2 - len(lgn) * 60
        vus = 0
        for j, ligne in enumerate(lgn):
            x = (L - f.getlength(ligne)) / 2
            for m in ligne.split():
                vus += 1
                if vus <= k:
                    d.text((x, y0 + j * 120), m, font=f, fill=SIGNAL if m.rstrip(".,") == mots[-1].rstrip(".,") else OS)
                x += f.getlength(m + " ")
        images.append(im)
    encoder(images, sortie)


if __name__ == "__main__":
    if sys.argv[1] == "saisie":
        saisie(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 2.0)
    elif sys.argv[1] == "texte":
        texte(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 2.0)
    elif sys.argv[1] == "logo_impact":
        logo_impact(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 6.0)
    elif sys.argv[1] == "logo":
        logo(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 5.0)
