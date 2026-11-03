"""Typographie cinétique de la campagne (Pillow + raqm, rendu à la résolution finale, image par image : net à toute taille).

Styles (champ « style » d'un texte du brief) :
  titre     grande capitale d'affiche (Geist SemiBold, interlettrage serré −2 %), mots révélés un à un sous un cache
            (montée de 0,9 ligne, décalage 0,07 s par mot) ; *mot* = couleur d'accent.
  impact    phrase courte au centre : arrivée en échelle 1,10 → 1 et flou 14 → 0 px en 0,35 s.
  pile      plusieurs lignes (séparées par « | ») révélées ligne à ligne (décalage 0,14 s), alignées à gauche.
  sur       surtitre mono en capitales, interlettré +12 %, puce d'accent ; sert d'étiquette (« CAPTURE RÉELLE »).
  prepa     étiquette « En préparation » obligatoire sur tout ce qui n'est pas en service : contour d'accent, mono.
  citation  texte de l'interface ou du client, mono, révélé à la frappe, guillemets.
Zones (champ « zone ») : colonne (gauche, 16:9), haut, bas, centre ; « auto » = colonne en 16:9 et haut en 9:16.
Marges sûres : 6 % des côtés en 16:9 ; 8 % des côtés, 11 % en haut et 15 % en bas en 9:16 (interfaces des réseaux).
Temps de lecture exigé (vérifié par usine.py) : 0,3 s par mot + 0,5 s.
"""
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class Typo:
    def __init__(self, marque):
        self.m = marque
        self.c = {k: tuple(v) for k, v in marque["couleurs"].items()}
        self.dossier = Path(marque["polices"]["dossier"]).expanduser()

    @lru_cache(maxsize=128)
    def police(self, nom, taille, graisse):
        f = ImageFont.truetype(str(self.dossier / self.m["polices"][nom]), max(6, int(taille)), layout_engine=ImageFont.Layout.RAQM)
        try:
            f.set_variation_by_name(graisse)
        except Exception:
            pass
        return f

    # ------------------------------------------------------------------------------------------------ mesure et tracé
    @staticmethod
    def jetons(txt):
        """« Il *rédige*. » → [("Il", False), ("rédige.", True)] ; l'astérisque peut couvrir plusieurs mots."""
        out, acc = [], False
        for brut in txt.split():
            debut, fin = brut.startswith("*"), brut.endswith("*") or brut.rstrip(".,;:!?»").endswith("*")
            mot = brut.replace("*", "")
            if debut:
                acc = True
            out.append((mot, acc))
            if fin:
                acc = False
        return out

    def larg(self, f, mot, track):
        return f.getlength(mot) + track * f.size * max(0, len(mot) - 1)

    def tracer(self, d, xy, mot, f, coul, track):
        """Mot avec interlettrage : lettres posées une à une, crénage conservé (longueur des paires)."""
        if abs(track) < 1e-4:
            d.text(xy, mot, font=f, fill=coul)
            return
        x, y = xy
        for i, ch in enumerate(mot):
            d.text((x, y), ch, font=f, fill=coul)
            nxt = mot[i + 1] if i + 1 < len(mot) else ""
            x += (f.getlength(ch + nxt) - f.getlength(nxt) if nxt else f.getlength(ch)) + track * f.size

    def lignes(self, jetons, f, largeur, track):
        esp = f.getlength(" ") * 0.92
        lignes, cur, w = [], [], 0.0
        for mot, acc in jetons:
            lw = self.larg(f, mot, track)
            if cur and w + esp + lw > largeur:
                lignes.append(cur)
                cur, w = [], 0.0
            cur.append((mot, acc, lw))
            w += (esp if len(cur) > 1 else 0) + lw
        return lignes + ([cur] if cur else []), esp

    # ------------------------------------------------------------------------------------------------------- zones
    def zone(self, nom, W, H):
        v = H > W
        mx = 0.08 * W if v else 0.06 * W
        if nom == "auto":
            nom = "haut" if v else "colonne"
        if nom == "colonne":
            return (mx, 0.14 * H, 0.295 * W, 0.86 * H), "gauche", "centre"
        if nom == "haut":
            return (mx, 0.105 * H if v else 0.09 * H, W - mx, 0.235 * H if v else 0.40 * H), "gauche", "haut"
        if nom == "bas":
            return (mx, 0.60 * H, W - mx, 0.85 * H if v else 0.90 * H), "gauche", "bas"
        return (mx, 0.2 * H, W - mx, 0.8 * H), "centre", "centre"

    # --------------------------------------------------------------------------------------------------- un texte
    def poser(self, im, spec, txt, u):
        """Pose un texte (spec du brief, texte traduit) à l'instant u (s depuis son début) ; renvoie l'image."""
        W, H = im.size
        v = H > W
        d_tot = spec["d"]
        zn = spec["zone_v"] if v and spec.get("zone_v") else spec.get("zone", "auto")  # « zone_v » : zone propre au 9:16
        style = spec.get("style", "titre")
        sortie = ease_io((u - (d_tot - 0.22)) / 0.22)  # 0 → 1 pendant les 0,22 dernières secondes
        alpha_g = 1 - sortie
        if alpha_g <= 0:
            return im
        (x0, y0, x1, y1), align, vert = self.zone(zn, W, H)
        if spec.get("align"):
            align = spec["align"]
        s = min(W, H)
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(calque)
        os_, sig, brume = self.c["os"], self.c["signal"], self.c["brume"]
        echelle = spec.get("taille", 1.0)

        if style in ("titre", "pile", "impact"):
            base = {"titre": 0.095, "pile": 0.072, "impact": 0.11}[style] * (1.0 if v else 0.86) * echelle
            if not v and zn in ("auto", "colonne"):
                base *= 0.74
            track = -0.02
            blocs = txt.split("|")  # « | » = retour à la ligne voulu
            for _ in range(6):  # ajustement : la ligne tient dans la zone (largeur et hauteur), sinon le corps diminue
                f = self.police("titre", s * base, "SemiBold")
                lignes_tot = []
                for b in blocs:
                    ls, esp = self.lignes(self.jetons(b.strip()), f, x1 - x0, track)
                    lignes_tot += ls
                pas = f.size * 1.08
                hh = len(lignes_tot) * pas
                trop_large = any(w > x1 - x0 for l in lignes_tot for _m, _a, w in l)
                if hh <= (y1 - y0) and not trop_large:
                    break
                base *= 0.9
            yb = {"haut": y0, "bas": y1 - hh, "centre": (y0 + y1 - hh) / 2}[vert]
            if style == "impact":
                k = ease_out(u / 0.35)
                sc = 1.10 - 0.10 * k
                f = self.police("titre", s * base * sc, "SemiBold")
                esp *= sc
                pas = f.size * 1.08
                hh = len(lignes_tot) * pas
                yb = (y0 + y1 - hh) / 2 if vert == "centre" else yb
            n_mot = 0
            for li, ligne in enumerate(lignes_tot):
                lw = sum(w for _, _, w in ligne) + esp * (len(ligne) - 1)
                if style == "impact":
                    lw = sum(self.larg(f, m, track) for m, _, _ in ligne) + esp * (len(ligne) - 1)
                x = x0 if align == "gauche" else (x0 + x1 - lw) / 2
                y = yb + li * pas
                # cache de ligne : les mots montent depuis sous la ligne de base, rognés au cadre de la ligne
                boite = Image.new("RGBA", (int(lw + f.size), int(pas + f.size * 0.4)), (0, 0, 0, 0))
                bd = ImageDraw.Draw(boite)
                xx = 0.0
                for mot, acc, w in ligne:
                    if style == "impact":
                        w = self.larg(f, mot, track)
                        p = 1.0
                    elif style == "pile":
                        p = ease_out((u - 0.14 * li) / 0.45)
                    else:
                        p = ease_out((u - 0.07 * n_mot) / 0.42)
                    n_mot += 1
                    if p > 0:
                        dy = (1 - p) * pas * 0.9
                        a = int(255 * min(1.0, p * 1.6))
                        self.tracer(bd, (xx, dy), mot, f, (*(sig if acc else os_), a), track)
                    xx += w + esp
                if style == "impact":
                    k = ease_out(u / 0.35)
                    r = 14 * (1 - k) * s / 1080
                    if r > 0.3:
                        boite = boite.filter(ImageFilter.GaussianBlur(r))
                    boite.putalpha(boite.getchannel("A").point(lambda q: int(q * min(1.0, k * 1.4))))
                calque.alpha_composite(boite, (int(x), int(y - sortie * f.size * 0.15)))
        elif style in ("sur", "prepa"):
            f = self.police("mono", s * 0.024 * echelle, "Medium")
            t2 = txt.upper()
            track = 0.12
            lw = self.larg(f, t2, track)
            p = ease_out(u / 0.3)
            x = x0 if align == "gauche" else (x0 + x1 - lw) / 2
            y = y0 - f.size * 2.2 if zn != "centre" else (y0 + y1) / 2
            if spec.get("y_v") is not None and v:  # position verticale propre au format 9:16 (fraction de la hauteur)
                y = spec["y_v"] * H
            elif spec.get("y") is not None:
                y = spec["y"] * H
            a = int(255 * p)
            if style == "prepa":
                pad = f.size * 0.6
                dd.rounded_rectangle([x, y - pad * 0.6, x + lw + 2 * pad, y + f.size + pad * 0.7], radius=f.size * 0.3,
                                     outline=(*sig, a), width=max(2, int(f.size * 0.09)))
                self.tracer(dd, (x + pad, y), t2, f, (*sig, a), track)
            else:
                r = f.size * 0.28
                dd.ellipse([x, y + f.size * 0.5 - r, x + 2 * r, y + f.size * 0.5 + r], fill=(*sig, a))
                self.tracer(dd, (x + 2 * r + f.size * 0.7, y), t2, f, (*brume, a), track)
        elif style == "citation":
            f = self.police("mono", s * (0.046 if v else 0.042) * echelle, "Medium")
            n = int(len(txt) * min(1.0, u / max(0.2, spec.get("frappe", 0.04 * len(txt)))))
            ls, esp = self.lignes([(m, False) for m in ((("« " if spec.get("guillemets", True) else "") + txt[:n] + ((" »" if spec.get("guillemets", True) else "") if n == len(txt) else "▍")).split())], f, x1 - x0, 0)
            pas = f.size * 1.4
            hh = len(ls) * pas
            yb = {"haut": y0, "bas": y1 - hh, "centre": (y0 + y1 - hh) / 2}[vert]
            for li, ligne in enumerate(ls):
                lt = " ".join(m for m, _, _ in ligne)
                xl = x0 if align == "gauche" else (x0 + x1 - f.getlength(lt)) / 2
                dd.text((xl, yb + li * pas), lt, font=f, fill=(*os_, 255))
        if alpha_g < 1:
            calque.putalpha(calque.getchannel("A").point(lambda q: int(q * alpha_g)))
        return Image.alpha_composite(im.convert("RGBA"), calque).convert("RGB")


def mots(txt):
    return len(txt.replace("*", "").replace("|", " ").split())


def lecture_min(txt):
    """Temps de lecture minimal (s) : 0,3 s par mot + 0,5 s."""
    return 0.3 * mots(txt) + 0.5
