"""Moments produit de la promo V3 : l'interface du studio dessinée en code (PIL), textes lus dans marque.json.

  saisie  : caméra qui avance vers le champ « Décris ta scène », la phrase se tape vite, le bouton s'allume et se
            presse (la coupe suivante tombe sur l'impact de la musique) ;
  rendu   : la carte « Rendu en cours » se remplit, le plan apparaît dedans et la carte grandit jusqu'au plein cadre ;
  galerie : la grille « Tes créations » se remplit de plans de la bataille qui jouent.
Les plans montrés dans l'interface sont les vrais plans du film (images RGB passées par monter_v3.py).
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
MARQUE = json.loads((ICI / "marque.json").read_text())
C = {k: tuple(v) for k, v in MARQUE["couleurs"].items()}
SURFACE, FILET, CARTE = (19, 19, 25), (43, 43, 56), (24, 24, 31)
POLICES = Path(MARQUE["polices"]["dossier"]).expanduser()


def police(nom, taille, graisse=b"Regular"):
    f = ImageFont.truetype(str(POLICES / nom), int(taille))
    try:
        f.set_variation_by_name(graisse)
    except Exception:
        pass
    return f


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


class Interface:
    def __init__(self, W, H, langue):
        self.W, self.H = W, H
        self.v = H > W
        self.T = MARQUE["langues"][langue]
        u = (W / 1920) if not self.v else (W / 1080) * 1.0
        self.u = u
        self.f_marque = police(MARQUE["polices"]["titre"], 30 * u, b"SemiBold")
        self.f_prompt = police(MARQUE["polices"]["titre"], (44 if not self.v else 52) * u, b"Medium")
        self.f_eti = police("jetbrains-mono-latin-wght-normal.woff2", 20 * u, b"Medium")
        self.f_bt = police(MARQUE["polices"]["texte"], 30 * u, b"SemiBold")
        self.f_titre = police(MARQUE["polices"]["texte"], 34 * u, b"SemiBold")

    # ---------------------------------------------------------------- fond commun : barre du haut + panneau
    def fond(self):
        W, H, u = self.W, self.H, self.u
        im = Image.new("RGB", (W, H), C["encre"])
        d = ImageDraw.Draw(im)
        d.line([(0, 72 * u), (W, 72 * u)], fill=(28, 28, 36), width=max(1, int(u)))
        x = 40 * u
        d.rounded_rectangle([x, 22 * u, x + 28 * u, 50 * u], radius=6 * u, fill=C["signal"])
        d.text((x + 42 * u, 36 * u), MARQUE["marque"].title() + " ", font=self.f_marque, fill=C["os"], anchor="lm")
        lx = x + 42 * u + self.f_marque.getlength(MARQUE["marque"].title() + " ")
        d.text((lx, 36 * u), MARQUE["produit"].title(), font=self.f_marque, fill=C["signal"], anchor="lm")
        return im, d

    def champ(self):
        W, H, u = self.W, self.H, self.u
        if self.v:
            return (60 * u, 520 * u, W - 60 * u, 1060 * u)
        return (330 * u, 300 * u, 1590 * u, 700 * u)

    # ---------------------------------------------------------------- 1. saisie du prompt et clic sur « Tourner »
    def saisie(self, n, ips=24, part_frappe=0.62, clic=0.80):
        W, H, u = self.W, self.H, self.u
        phrase = self.T["prompt"]
        out = []
        for i in range(n):
            s = i / max(1, n - 1)
            im, d = self.fond()
            x0, y0, x1, y1 = self.champ()
            d.rounded_rectangle([x0, y0, x1, y1], radius=14 * u, fill=SURFACE, outline=FILET, width=max(1, int(2 * u)))
            d.text((x0 + 40 * u, y0 + 44 * u), self.T["etiquette"].replace("1344×768", "768×1344") if self.v else self.T["etiquette"], font=self.f_eti, fill=C["signal"], anchor="lm")
            k = round(len(phrase) * min(1.0, s / part_frappe))
            texte = phrase[:k]
            lignes, cur = [], ""
            for m in texte.split(" "):
                essai = (cur + " " + m).strip()
                if self.f_prompt.getlength(essai) <= (x1 - x0) - 80 * u:
                    cur = essai
                else:
                    lignes.append(cur)
                    cur = m
            lignes.append(cur)
            if not texte:
                d.text((x0 + 40 * u, y0 + 100 * u), self.T["invite"], font=self.f_prompt, fill=(90, 90, 104))
            lh = self.f_prompt.size * 1.3
            for j, l in enumerate(lignes):
                d.text((x0 + 40 * u, y0 + 100 * u + j * lh), l, font=self.f_prompt, fill=C["os"])
            if k < len(phrase) or (i // 6) % 2 == 0:
                cx = x0 + 40 * u + self.f_prompt.getlength(lignes[-1]) + 6 * u
                cy = y0 + 100 * u + (len(lignes) - 1) * lh
                d.rectangle([cx, cy + 6 * u, cx + 5 * u, cy + self.f_prompt.size * 1.1], fill=C["signal"])
            # bouton : s'allume à la fin de la frappe, s'enfonce au clic, halo qui part
            allume = s >= part_frappe
            presse = clic <= s < clic + 0.08
            bw, bh = 250 * u, 74 * u
            bx1, by1 = x1 - 36 * u, y1 - 32 * u
            r = 0.94 if presse else 1.0
            bx0, by0 = bx1 - bw * r, by1 - bh * r
            if s >= clic:
                a = ease((s - clic) / 0.2)
                halo = Image.new("L", (W, H))
                ImageDraw.Draw(halo).rounded_rectangle([bx0 - 30 * u * a, by0 - 30 * u * a, bx1 + 30 * u * a, by1 + 30 * u * a], radius=24 * u, fill=int(180 * (1 - a)))
                halo = halo.filter(ImageFilter.GaussianBlur(14 * u))
                im = Image.composite(Image.new("RGB", (W, H), C["signal"]), im, halo)
                d = ImageDraw.Draw(im)
            d.rounded_rectangle([bx0, by0, bx1, by1], radius=12 * u, fill=C["signal"] if allume else FILET)
            coul = C["encre"] if allume else C["brume"]
            tx = (bx0 + bx1) / 2 + 16 * u
            d.text((tx, (by0 + by1) / 2), self.T["bouton"], font=self.f_bt, fill=coul, anchor="mm")
            px = tx - self.f_bt.getlength(self.T["bouton"]) / 2 - 30 * u
            py = (by0 + by1) / 2
            d.polygon([(px, py - 11 * u), (px, py + 11 * u), (px + 18 * u, py)], fill=coul)
            # caméra : poussée lente vers le champ, puis coup de zoom au clic
            z = 1.0 + 0.10 * s + (0.06 * ease((s - clic) / 0.2) if s > clic else 0)
            cxz, cyz = (x0 + x1) / 2, (y0 + y1) / 2 + 40 * u
            bw2, bh2 = W / z, H / z
            bx = min(max(0, cxz - bw2 / 2), W - bw2)
            by = min(max(0, cyz - bh2 / 2), H - bh2)
            im = im.resize((W, H), Image.BICUBIC, box=(bx, by, bx + bw2, by + bh2))
            out.append(np.asarray(im))
        return out

    # ---------------------------------------------------------------- 2. carte de rendu qui devient le plan plein cadre
    def rendu(self, n, plan: list, ips=24):
        W, H, u = self.W, self.H, self.u
        out = []
        for i in range(n):
            s = i / max(1, n - 1)
            im, d = self.fond()
            d.text((c0x := ((W - 1180 * u) / 2 if not self.v else 60 * u), 140 * u), self.T["creations"], font=self.f_titre, fill=C["os"], anchor="lm")
            if self.v:
                c0 = (60 * u, 190 * u, W - 60 * u, 190 * u + (W - 120 * u) * 9 / 16)
            else:
                cw = 1180 * u
                c0 = ((W - cw) / 2, 190 * u, (W + cw) / 2, 190 * u + cw * 9 / 16)
            # grandissement vers le plein cadre sur le dernier tiers
            g = ease((s - 0.55) / 0.45)
            cx0 = c0[0] * (1 - g)
            cy0 = c0[1] * (1 - g)
            cx1 = c0[2] + (W - c0[2]) * g
            cy1 = c0[3] + (H - c0[3]) * g
            fr = plan[min(len(plan) - 1, i)]
            pr = min(1.0, s / 0.35)
            box = [int(cx0), int(cy0), int(cx1), int(cy1)]
            d.rounded_rectangle(box, radius=int(14 * u * (1 - g)), fill=CARTE, outline=FILET, width=max(1, int(2 * u)))
            if pr < 1:
                # barre de progression et lueur orange de la carte
                d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), self.T["rendu"], font=self.f_bt, fill=C["signal"], anchor="mm")
                d.rectangle([box[0] + 30 * u, box[3] - 40 * u, box[0] + 30 * u + (box[2] - box[0] - 60 * u) * pr, box[3] - 32 * u], fill=C["signal"])
            else:
                a = ease((s - 0.35) / 0.12)
                vign = Image.fromarray(fr).resize((box[2] - box[0], box[3] - box[1]), Image.BICUBIC)
                if a < 1:
                    vign = Image.blend(Image.new("RGB", vign.size, CARTE), vign, a)
                masque = Image.new("L", vign.size, 0)
                ImageDraw.Draw(masque).rounded_rectangle([0, 0, vign.size[0] - 1, vign.size[1] - 1], radius=int(14 * u * (1 - g)), fill=255)
                im.paste(vign, (box[0], box[1]), masque)
                if g < 0.6:
                    d = ImageDraw.Draw(im)
                    d.rounded_rectangle([box[0] + 16 * u, box[1] + 16 * u, box[0] + 110 * u, box[1] + 50 * u], radius=8 * u, fill=(0, 0, 0))
                    d.text((box[0] + 63 * u, box[1] + 33 * u), "vidéo" if "Rendu" in self.T["rendu"] else "video", font=self.f_eti, fill=C["os"], anchor="mm")
            out.append(np.asarray(im))
        return out

    # ---------------------------------------------------------------- 3. galerie qui se remplit de plans
    def galerie(self, n, plans: list[list], ips=24):
        W, H, u = self.W, self.H, self.u
        cols, rows = (2, 4) if self.v else (3, 2)
        out = []
        for i in range(n):
            s = i / max(1, n - 1)
            im, d = self.fond()
            d.text((90 * u, 120 * u), self.T["creations"], font=self.f_titre, fill=C["os"], anchor="lm")
            gx0, gy0 = (60 * u, 180 * u) if self.v else (90 * u, 170 * u)
            gw = W - 2 * gx0
            tw = (gw - (cols - 1) * 24 * u) / cols
            th = tw * 9 / 16
            # légère poussée de caméra
            for k in range(cols * rows):
                c, r = k % cols, k // cols
                x0 = gx0 + c * (tw + 24 * u)
                y0 = gy0 + r * (th + 24 * u)
                box = [int(x0), int(y0), int(x0 + tw), int(y0 + th)]
                apparition = ease((s - k * 0.07) / 0.15)
                d.rounded_rectangle(box, radius=int(12 * u), fill=CARTE, outline=FILET, width=max(1, int(2 * u)))
                if apparition > 0:
                    p = plans[k % len(plans)]
                    fr = p[min(len(p) - 1, i)]
                    vign = Image.fromarray(fr).resize((box[2] - box[0], box[3] - box[1]), Image.BICUBIC)
                    vign = Image.blend(Image.new("RGB", vign.size, CARTE), vign, apparition)
                    m = Image.new("L", vign.size, 0)
                    ImageDraw.Draw(m).rounded_rectangle([0, 0, vign.size[0] - 1, vign.size[1] - 1], radius=int(12 * u), fill=255)
                    im.paste(vign, (box[0], box[1]), m)
            z = 1.0 + 0.05 * s
            bw2, bh2 = W / z, H / z
            im = im.resize((W, H), Image.BICUBIC, box=((W - bw2) / 2, (H - bh2) / 2, (W + bw2) / 2, (H + bh2) / 2))
            out.append(np.asarray(im))
        return out


# ------------------------------------------------------------------------------------------------ titres et carton de fin
def titre(W, H, n, texte, fond=None, ips=24, accent_dernier=True):
    """Titre de bande-annonce : grandes capitales espacées qui se resserrent lentement, sur noir ou sur des images."""
    v = H > W
    u = W / (1080 if v else 1920)
    f = police(MARQUE["polices"]["titre"], (96 if v else 84) * u, b"SemiBold")
    out = []
    mots = texte.upper()
    for i in range(n):
        s = i / max(1, n - 1)
        im = Image.fromarray(fond[min(len(fond) - 1, i)]) if fond is not None else Image.new("RGB", (W, H), (0, 0, 0))
        if fond is not None:
            im = Image.blend(im, Image.new("RGB", (W, H)), 0.45)
        couche = Image.new("L", (W, H))
        d = ImageDraw.Draw(couche)
        esp = (0.28 - 0.1 * s) * f.size
        # retour à la ligne en vertical
        lignes = [mots]
        if v and f.getlength(mots) + esp * len(mots) > W * 0.86:
            ms = mots.split()
            moitie = len(ms) // 2 + len(ms) % 2
            lignes = [" ".join(ms[:moitie]), " ".join(ms[moitie:])]
        a = min(1.0, s / 0.18) * min(1.0, (1 - s) / 0.12)
        for j, l in enumerate(lignes):
            larg = sum(f.getlength(c) for c in l) + esp * (len(l) - 1)
            x = (W - larg) / 2
            y = H / 2 + (j - (len(lignes) - 1) / 2) * f.size * 1.25
            for c in l:
                d.text((x, y), c, font=f, fill=int(255 * a), anchor="lm")
                x += f.getlength(c) + esp
        im = Image.composite(Image.new("RGB", (W, H), C["os"]), im, couche)
        out.append(np.asarray(im))
    return out
