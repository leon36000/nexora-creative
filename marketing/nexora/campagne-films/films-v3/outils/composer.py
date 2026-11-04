"""Compositeur des films V5 : film.json → image (16:9 ou 9:16), rendue image par image à la taille finale.

  python3 composer.py <film> <16x9|9x16> [--de T --a T]  (extrait pour revue)  [--brouillon]  (1 image sur 2, rapide)
Ce que fait le code :
  - grille musicale MESURÉE (musique.py) : chaque coupe est aimantée sur le temps le plus proche (±0,3 s), plan ≥ 1,2 s ;
  - plaques H3 : variante native 9:16 quand elle existe, sinon recadrage ; étalonnage « lumineux » (noirs levés, gamma réglé sur
    la luminance médiane du plan), lente poussée, grain léger commun ;
  - vraies captures (PNG 3840×2160, flux CDP) en carte sans appareil : coins arrondis, ombre douce, poussée lente du cadrage
    (de → a), entrée par montée 0,35 s ; suites de captures en fondu ; le film réellement produit par le studio en carte ;
  - dessins de code : tableau M1–M10 (OPSYS-AI), lumière du flux et recomposition de l'envoi (WorkStudio), imprimés sur table ;
  - typographie `usine/typo.py` (Geist, interlettrage serré, révélation mot à mot, mot d'accent orange #FF6600) ;
  - carton final depuis marque.json (nom interchangeable) ; étiquette « Vision » permanente quand le film en a une.
Sortie : work/films-v3/<film>/rendu/<film>-<format>-image.mp4 (x264 CRF 15, sans son) + plans.json (temps recalés).
"""
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import commun as C

sys.path.insert(0, str(C.RACINE.parent / "usine"))
import typo  # noqa: E402

IPS = 24
MARQUE = json.loads((C.RACINE / "marque.json").read_text())
COUL = {k: tuple(v) for k, v in MARQUE["couleurs"].items()}
SIG, OS_, BRUME, ENCRE = COUL["signal"], COUL["os"], COUL["brume"], COUL["encre"]
DEPTS = {"M1": "Réception", "M2": "CRM", "M3": "Estimation", "M4": "Terrain", "M5": "Finance", "M6": "Matériel", "M7": "Marketing",
         "M8": "Analytique", "M9": "Stratégie", "M10": "Mémoire"}


def eio(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def eout(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


# ------------------------------------------------------------------------------------------------------------ grille
def recaler(film, mus):
    """Début de chaque plan aimanté sur le temps musical le plus proche (±0,3 s), durée ≥ 1,2 s ; fin du film conservée."""
    temps, ph = mus["temps_s"], mus["phase_s"]
    plans = film["plans"]
    debuts = [p["t"] for p in plans]
    neufs = [0.0]
    for t in debuts[1:]:
        k = round((t - ph) / temps)
        b = ph + k * temps
        neufs.append(round(b if abs(b - t) <= 0.3 else t, 3))
    for i in range(1, len(neufs)):
        neufs[i] = max(neufs[i], neufs[i - 1] + 1.2)
    fin = film["duree"]
    durees = [round(b - a, 3) for a, b in zip(neufs, neufs[1:] + [fin])]
    ecart = float(np.mean([abs(a - b) for a, b in zip(neufs, debuts)]))
    return neufs, durees, ecart


# ------------------------------------------------------------------------------------------------------------ fonds
@lru_cache(maxsize=8)
def fond(W, H, ton="encre"):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H * 0.45) / H) ** 2)
    if ton == "papier":
        base, bord = np.array([232, 228, 222], np.float32), np.array([200, 195, 188], np.float32)
    else:
        base, bord = np.array([26, 26, 30], np.float32), np.array([8, 8, 10], np.float32)
    k = np.clip(r / 0.75, 0, 1)[..., None] ** 1.4
    a = base * (1 - k) + bord * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


@lru_cache(maxsize=32)
def masque_carte(cw, ch, rayon, ombre):
    m = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=rayon, fill=255)
    pad = int(ombre * 3)
    o = Image.new("L", (cw + 2 * pad, ch + 2 * pad), 0)
    ImageDraw.Draw(o).rounded_rectangle([pad, pad + ombre * 0.5, pad + cw, pad + ch + ombre * 0.5], radius=rayon, fill=150)
    return m, o.filter(ImageFilter.GaussianBlur(ombre)), pad


def poser_carte(base, im, cx, cy, entree=1.0, liseré=True):
    """Carte arrondie avec ombre douce posée au centre (cx, cy) ; entrée : montée + opacité."""
    W, H = base.size
    cw, ch = im.size
    rayon = max(10, int(0.011 * min(W, H) * 1.6))
    m, o, pad = masque_carte(cw, ch, rayon, int(0.022 * min(W, H)))
    a = eout(entree)
    dy = int((1 - a) * 0.03 * H)
    x, y = int(cx - cw / 2), int(cy - ch / 2) + dy
    noir = Image.new("RGB", o.size, (0, 0, 0))
    base.paste(noir, (x - pad, y - pad), o.point(lambda q: int(q * a)))
    if liseré:
        ImageDraw.Draw(base).rounded_rectangle([x - 1, y - 1, x + cw, y + ch], radius=rayon + 1, outline=(58, 58, 64))
    base.paste(im, (x, y), m.point(lambda q: int(q * a)))
    return (x, y, cw, ch)


def boite(src_w, src_h, c, aspect):
    """[cx, cy, w] (fractions de la source) + aspect → boîte de recadrage en pixels de la source."""
    cx, cy, w = c
    bw = w * src_w
    bh = bw / aspect
    if bh > src_h:
        bh = src_h
        bw = bh * aspect
    x0 = min(max(cx * src_w - bw / 2, 0), src_w - bw)
    y0 = min(max(cy * src_h - bh / 2, 0), src_h - bh)
    return (x0, y0, x0 + bw, y0 + bh)


def taille_carte(W, H, aspect, v):
    mw, mh = (0.88 * W, 0.60 * H) if v else (0.80 * W, 0.76 * H)
    cw = mw
    ch = cw / aspect
    if ch > mh:
        ch = mh
        cw = ch * aspect
    return int(cw), int(ch)


# ------------------------------------------------------------------------------------------------------------ plaques
class Plaque:
    def __init__(self, f, debut, d, W, H, zoom, centre):
        self.W, self.H, self.zoom, self.centre, self.d = W, H, zoom, centre, d
        info = subprocess.run([C.FF, "-hide_banner", "-i", str(f)], capture_output=True, text=True).stderr
        import re
        m = re.search(r", (\d{3,5})x(\d{3,5})", info)
        self.sw, self.sh = int(m[1]), int(m[2])
        dsrc = C.duree(f)
        self.vitesse = min(1.0, max(0.5, (dsrc - debut - 0.05) / max(d, 0.1)))
        n = int(d * IPS) + 3
        self.p = subprocess.Popen([C.FF, "-v", "error", "-ss", f"{debut:.3f}", "-i", str(f), "-vf",
                                   (f"setpts=PTS/{self.vitesse:.4f},framerate={IPS}" if self.vitesse < 0.98 else f"fps={IPS}"), "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE)
        self.derniere = None
        self.g = None
        self.i = 0

    def lire(self):
        b = self.p.stdout.read(self.sw * self.sh * 3)
        if len(b) == self.sw * self.sh * 3:
            self.derniere = np.frombuffer(b, np.uint8).reshape(self.sh, self.sw, 3)
        return self.derniere

    def image(self, u):
        a = self.lire()
        if self.g is None:  # étalonnage réglé une fois par plan sur sa première image : médiane visée ≈ 0,40
            med = float(np.median(a.mean(2))) / 255
            self.g = float(np.clip(math.log(0.40) / math.log(max(0.05, min(0.95, med))), 0.72, 1.0))
            self.lut = (255 * (0.028 + 0.972 * (np.arange(256) / 255) ** self.g)).clip(0, 255).astype(np.uint8)
        a = self.lut[a]
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * eio(u / self.d)
        asp = self.W / self.H
        bw = min(self.sw, self.sh * asp) / z
        bh = bw / asp
        cx, cy = self.centre
        x0 = min(max(cx * self.sw - bw / 2, 0), self.sw - bw)
        y0 = min(max(cy * self.sh - bh / 2, 0), self.sh - bh)
        return Image.fromarray(a).resize((self.W, self.H), Image.BICUBIC, box=(x0, y0, x0 + bw, y0 + bh))


# ------------------------------------------------------------------------------------------------------------ rendus
class Rendu:
    def __init__(self, film, fmt):
        self.film, self.fmt = film, fmt
        self.v = fmt == "9x16"
        self.W, self.H = (1080, 1920) if self.v else (1920, 1080)
        self.dos = C.TRAVAIL / film["id"]
        self.ty = typo.Typo(MARQUE)
        pj = self.dos / "plaques/plaques.json"
        self.pj = json.loads(pj.read_text()) if pj.exists() else {}
        self.cache = {}

    def img(self, chemin):
        if chemin not in self.cache:
            p = Path(chemin)
            self.cache[chemin] = Image.open(p if p.is_absolute() else self.dos / p).convert("RGB")
        return self.cache[chemin]

    def cadre(self, p, u, d):
        k = "_v" if self.v and p.get("de_v") else ""
        de, a = p["de" + k], p.get("a" + k, p["de" + k])
        e = eio(u / d)
        return [de[i] + (a[i] - de[i]) * e for i in range(3)], p.get("aspect" + k, p["aspect"])

    def ui(self, src, p, u, d, entree=True):
        c, asp = self.cadre(p, u, d)
        bx = boite(src.width, src.height, c, asp)
        cw, ch = taille_carte(self.W, self.H, asp, self.v)
        im = src.resize((cw, ch), Image.LANCZOS, box=bx)
        base = fond(self.W, self.H).copy()
        cy = self.H * (0.47 if self.v else 0.5)
        geo = poser_carte(base, im, self.W / 2, cy, (u / 0.35) if entree else 1.0)
        return base, geo, bx, (cw, ch)

    # ---------------------------------------------------------------------------------------------- types de plans
    def ouvrir(self, p, d):
        t = p["type"]
        if t == "plaque":
            pl = self.film["plaques"][p["src"]]
            r9 = self.pj.get(f"{p['src']}-9x16", {})
            r16 = self.pj.get(f"{p['src']}-16x9", {})
            if self.v and r9.get("video"):
                f, centre = self.dos / "plaques" / r9["video"], [0.5, 0.5]
            else:
                f = self.dos / "plaques" / r16["video"]
                centre = p.get("centre_v", [0.5, 0.5]) if self.v else p.get("centre", [0.5, 0.5])
            pq = Plaque(f, p.get("debut", 0.0), d, self.W, self.H, p.get("zoom", [1.0, 1.04]), centre)
            return lambda u: pq.image(u)
        if t in ("ui", "chaine"):
            src = self.img(p["image"])
            if t == "ui":
                def f(u):
                    base, geo, bx, cs = self.ui(src, p, u, d)
                    if p.get("appui"):
                        self.appui(base, geo, bx, src, p["appui"], u, d)
                    return base
                return f
            return lambda u: self.chaine(src, p, u, d)
        if t == "flux":
            lignes = [json.loads(x) for x in (self.dos / "cap/flux.jsonl").read_text().splitlines()]
            seq = [(x["t"], self.dos / "cap/flux" / f"{x['seq']}-{x['f']:05d}.jpg") for x in lignes if x["seq"] == p["seq"]]
            ts = np.array([s[0] for s in seq])

            def f(u):
                k = int(np.searchsorted(ts, p["t0"] + u * p["vitesse"], side="right") - 1)
                return self.ui(self.img(str(seq[max(0, k)][1])), p, u, d)[0]
            return f
        if t == "suite":
            ims = [self.img(x) for x in p["images"]]
            pas = d / len(ims)

            def f(u):
                k = min(len(ims) - 1, int(u / pas))
                base = self.ui(ims[k], p, u, d)[0]
                if k + 1 < len(ims) and u > (k + 1) * pas - 0.18:
                    b2 = self.ui(ims[k + 1], p, u, d, entree=False)[0]
                    base = Image.blend(base, b2, eio((u - ((k + 1) * pas - 0.18)) / 0.18))
                return base
            return f
        if t == "video":
            return self.video(p, d)
        if t == "imprime":
            return self.imprime(p, d)
        if t == "tableau":
            return lambda u: self.tableau(p, u, d)
        if t == "envoye":
            return lambda u: self.envoye(u, d)
        if t == "ligne":
            return lambda u: self.ligne(p, u, d)
        if t == "carton":
            return lambda u: self.carton(p, u, d)
        raise ValueError(t)

    def appui(self, base, geo, bx, cs, ap, u, d):
        """Appui sur le bouton de la capture (rond qui s'élargit) à 60 % du plan : geste, rien d'autre n'est redessiné."""
        x, y, cw, ch = geo
        src = cs  # image source de la capture
        k = (u - 0.6 * d) / 0.5
        if not (0 <= k <= 1):
            return
        dr = ImageDraw.Draw(base, "RGBA")
        sw = bx[2] - bx[0]
        # coordonnées de l'appui (fractions de la source → pixels écran)
        X = x + (ap[0] * src.width - bx[0]) / sw * cw
        Y = y + (ap[1] * src.height - bx[1]) / (bx[3] - bx[1]) * ch
        r = (0.02 + 0.05 * eout(k)) * self.W
        dr.ellipse([X - r, Y - r, X + r, Y + r], outline=(*SIG, int(255 * (1 - k))), width=max(3, int(0.004 * self.W)))

    def video(self, p, d):
        f = self.dos / p["fichier"]
        segs = p["segments"]
        tot = sum(b - a for a, b in segs)
        vit = tot / d
        frames = []
        for a, b in segs:
            raw = subprocess.run([C.FF, "-v", "error", "-ss", str(a), "-t", str(b - a), "-i", str(f), "-vf", f"fps={IPS}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            info = subprocess.run([C.FF, "-hide_banner", "-i", str(f)], capture_output=True, text=True).stderr
            import re
            m = re.search(r", (\d{3,5})x(\d{3,5})", info)
            w, h = int(m[1]), int(m[2])
            n = len(raw) // (w * h * 3)
            frames += [np.frombuffer(raw[i * w * h * 3:(i + 1) * w * h * 3], np.uint8).reshape(h, w, 3) for i in range(n)]
        asp = w / h

        def rendre(u):
            k = min(len(frames) - 1, int(u * vit * IPS))
            im = Image.fromarray(frames[k])
            z = 1.0 + 0.03 * eio(u / d)
            if self.v:  # 9:16 : recadrage carré au centre du film produit (plus grand que la bande 16:9)
                cw = ch = int(0.88 * self.W)
                bw = bh = h / z
            else:
                cw, ch = int(0.86 * self.W), int(0.86 * self.W / asp)
                bw, bh = w / z, h / z
            im = im.resize((cw, ch), Image.LANCZOS, box=((w - bw) / 2, (h - bh) / 2, (w + bw) / 2, (h + bh) / 2))
            im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
            base = fond(self.W, self.H).copy()
            poser_carte(base, im, self.W / 2, self.H * (0.47 if self.v else 0.5), u / 0.4)
            return base
        return rendre

    def imprime(self, p, d):
        src = Image.open(C.RACINE.parents[1] / "imprimes/final" / p["source"]) if p.get("source") else self.img(p["image"])
        src = src.convert("RGB")

        def rendre(u):
            base = fond(self.W, self.H, "papier").copy()
            mh = (0.66 if self.v else 0.84) * self.H
            mw = (0.80 if self.v else 0.62) * self.W
            s = min(mh / src.height, mw / src.width) * (1.0 + 0.04 * eio(u / d))
            im = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
            rgba = im.convert("RGBA").rotate(p.get("rot", 0), resample=Image.BICUBIC, expand=True)
            al = rgba.getchannel("A")
            ombre = Image.new("L", (rgba.width + 120, rgba.height + 120), 0)
            ombre.paste(al.point(lambda q: int(q * 0.45)), (60, 78))
            ombre = ombre.filter(ImageFilter.GaussianBlur(26))
            x, y = int(self.W / 2 - rgba.width / 2), int(self.H * 0.5 - rgba.height / 2)
            base.paste((60, 50, 40), (x - 60, y - 60, x - 60 + ombre.width, y - 60 + ombre.height), ombre)
            base.paste(rgba, (x, y), al)
            return base
        return rendre

    # ---------------------------------------------------------------------------------------------- tableau M1–M10
    def tableau(self, p, u, d):
        W, H, v = self.W, self.H, self.v
        base = fond(W, H).copy()
        cols, rows = (2, 5) if v else (5, 2)
        gx = 0.018 * W
        tw = (0.86 * W - (cols - 1) * gx) / cols
        th = tw * (0.60 if v else 0.72)
        gy = gx
        x0 = (W - (cols * tw + (cols - 1) * gx)) / 2
        y0 = (H - (rows * th + (rows - 1) * gy)) / 2 + (0.02 * H if v else 0.03 * H)
        fm = self.ty.police("mono", th * 0.11, "Medium")
        fn = self.ty.police("titre", th * 0.17, "SemiBold")
        fa = self.ty.police("titre", th * 0.125, "Regular")
        deja = set(p.get("deja", []))
        allume = p.get("allume", [])
        pas = max(0.8, (d - 1.2) / max(1, len(allume)))
        etat = {}
        for k, (m, act) in enumerate(allume):
            etat[m] = (min(1.0, max(0.0, (u - 0.5 - k * pas) / 0.35)), act, max(0.0, u - 0.7 - k * pas))
        cal = Image.new("RGB", (W, H), (0, 0, 0))
        dh = ImageDraw.Draw(cal)
        dd = ImageDraw.Draw(base)
        pos = {}
        for i in range(10):
            m = f"M{i + 1}"
            c, r = (i % cols, i // cols)
            x, y = x0 + c * (tw + gx), y0 + r * (th + gy)
            pos[m] = (x, y)
            a, act, ut = etat.get(m, (1.0 if m in deja else 0.0, None, 99))
            vif = m in etat
            bord = tuple(int(44 + (cc - 44) * a) for cc in (SIG if vif else (120, 120, 130))) if a else (40, 40, 46)
            dd.rounded_rectangle([x, y, x + tw, y + th], radius=th * 0.08, fill=(18, 18, 22), outline=bord, width=3 if a else 2)
            if vif and a:
                dh.rounded_rectangle([x - 4, y - 4, x + tw + 4, y + th + 4], radius=th * 0.09, outline=tuple(int(cc * a * 0.8) for cc in SIG), width=10)
            dd.text((x + th * 0.1, y + th * 0.1), m, font=fm, fill=SIG if (vif and a) else BRUME)
            dd.text((x + th * 0.1, y + th * 0.27), DEPTS[m], font=fn, fill=OS_ if a else (98, 98, 108))
            if vif and act and a:
                n = int(len(act) * min(1.0, ut / 0.5))
                dd.text((x + th * 0.1, y + th * 0.62), act[:n], font=fa, fill=(*OS_,))
                rr = th * 0.035
                dd.ellipse([x + tw - th * 0.16, y + th * 0.13, x + tw - th * 0.16 + 2 * rr, y + th * 0.13 + 2 * rr], fill=SIG)
            elif m in deja:
                rr = th * 0.03
                dd.ellipse([x + tw - th * 0.16, y + th * 0.13, x + tw - th * 0.16 + 2 * rr, y + th * 0.13 + 2 * rr], fill=(150, 150, 160))
        # ligne de lumière entre deux départements allumés successivement
        for k in range(len(allume) - 1):
            q = (u - 0.85 - k * pas) / (pas * 0.6)
            if 0 < q:
                (ax, ay), (bx, by) = pos[allume[k][0]], pos[allume[k + 1][0]]
                p0, p1 = (ax + tw / 2, ay + th / 2), (bx + tw / 2, by + th / 2)
                q = min(1.0, q)
                dh.line([p0, (p0[0] + (p1[0] - p0[0]) * q, p0[1] + (p1[1] - p0[1]) * q)], fill=tuple(int(c * 0.7) for c in SIG), width=5)
        cal = cal.filter(ImageFilter.GaussianBlur(12))
        im = Image.fromarray(np.clip(np.asarray(base, np.int16) + np.asarray(cal, np.int16), 0, 255).astype(np.uint8))
        s = 1.0 + 0.03 * eio(u / d)
        cw, ch = W / s, H / s
        return im.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))

    # ---------------------------------------------------------------------------------------------- WorkStudio
    def chaine(self, src, p, u, d):
        """Vraie capture du workflow ; la lumière (dessinée) entre, traverse « Brouillon » (agent) et s'arrête sur « Validation »."""
        base, (x, y, cw, ch), bx, _ = self.ui(src, p, u, d)
        sx = lambda fx: x + (fx * src.width - bx[0]) / (bx[2] - bx[0]) * cw
        sy = lambda fy: y + (fy * src.height - bx[1]) / (bx[3] - bx[1]) * ch
        cal = Image.new("RGB", (self.W, self.H), (0, 0, 0))
        dc = ImageDraw.Draw(cal)
        q = eio((u - 0.4) / (0.62 * d))
        fx = 0.0 + 0.46 * q
        yy = sy(0.499)
        if 0.087 < fx or q >= 1:
            a1 = min(1.0, max(0.0, (fx - 0.087) / 0.05)) * (1 - min(1.0, max(0.0, (fx - 0.40) / 0.06)))
            if a1 > 0:
                dc.rounded_rectangle([sx(0.083), sy(0.395), sx(0.351), sy(0.595)], radius=int(0.012 * cw), outline=tuple(int(c * a1) for c in SIG), width=6)
        if q >= 1:
            pul = 0.55 + 0.45 * math.sin((u - 0.4 - 0.62 * d) * 3.4)
            dc.rounded_rectangle([sx(0.456), sy(0.395), sx(0.724), sy(0.595)], radius=int(0.012 * cw), outline=tuple(int(c * pul) for c in SIG), width=7)
        else:
            for k in range(14):
                t = fx - k * 0.009
                if t > 0:
                    r = 0.011 * self.W * (1 - k / 16)
                    X = sx(t)
                    dc.ellipse([X - r, yy - r, X + r, yy + r], fill=tuple(int(c * (1 - k / 14)) for c in SIG))
        # peinture (pas d'addition) : la lumière reste orange même sur l'interface blanche
        a = np.asarray(cal.convert("L"), np.float32) / 255
        h = np.asarray(cal.convert("L").filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
        al = np.clip(np.maximum(a, h * 1.4), 0, 1)[..., None]
        out = np.asarray(base, np.float32) * (1 - al) + np.array(SIG, np.float32) * al
        return Image.fromarray(out.clip(0, 255).astype(np.uint8))

    def envoye(self, u, d):
        """Recomposition dessinée (étiquetée) de la fin de l'exécution réelle : accord humain → envoi vers la boîte de test."""
        W, H, v = self.W, self.H, self.v
        base = fond(W, H).copy()
        dd = ImageDraw.Draw(base)
        cal = Image.new("RGB", (W, H), (0, 0, 0))
        dc = ImageDraw.Draw(cal)
        etapes = [("Brouillon", "Agent"), ("Validation", "Humain"), ("Envoi", "Courriel")]
        s = min(W, H)
        bw, bh = (0.76 * W, 0.12 * H) if v else (0.255 * W, 0.20 * H)
        fn = self.ty.police("titre", s * 0.050, "SemiBold")
        fm = self.ty.police("mono", s * 0.024, "Medium")
        pts = []
        for i, (nom, qui) in enumerate(etapes):
            if v:
                x, y = (W - bw) / 2, H * 0.27 + i * (bh + 0.05 * H)
            else:
                x, y = W * 0.0675 + i * (bw + 0.05 * W), H * 0.36
            pts.append((x, y))
            fait = u > 0.3 + i * 0.55 * (d - 1.8) / 2
            dd.rounded_rectangle([x, y, x + bw, y + bh], radius=bh * 0.14, fill=(242, 241, 238) if fait else (30, 30, 34),
                                 outline=(80, 80, 88), width=2)
            dd.text((x + bh * 0.22, y + bh * 0.2), nom, font=fn, fill=(20, 20, 24) if fait else OS_)
            dd.text((x + bh * 0.22, y + bh * 0.62), qui.upper(), font=fm, fill=(110, 110, 118) if fait else BRUME)
            if fait:
                r = bh * 0.14
                cx, cy = x + bw - bh * 0.32, y + bh * 0.5
                dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SIG)
                dd.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)], fill=(255, 255, 255), width=max(3, int(r * 0.22)))
        q = eio((u - 0.2) / (d - 1.6))
        if v:
            p0, p1 = (W / 2, pts[0][1] + bh), (W / 2, pts[-1][1])
        else:
            p0, p1 = (pts[0][0] + bw, H * 0.36 + bh / 2), (pts[-1][0], H * 0.36 + bh / 2)
        dc.line([p0, (p0[0] + (p1[0] - p0[0]) * q, p0[1] + (p1[1] - p0[1]) * q)], fill=SIG, width=6)
        fin = eout((u - (d - 1.5)) / 0.5)
        if fin > 0:
            ft = self.ty.police("titre", s * 0.05, "SemiBold")
            txt = "Réponse envoyée."
            tw = ft.getlength(txt)
            yy = H * (0.70 if v else 0.70)
            dd.text(((W - tw) / 2, yy), txt, font=ft, fill=tuple(int(c * fin) for c in OS_))
        fe = self.ty.police("mono", s * 0.017, "Medium")
        et = "RECOMPOSITION D'APRÈS UNE EXÉCUTION RÉELLE · ENVOI VERS UNE BOÎTE DE TEST"
        if v:
            et = "RECOMPOSITION · EXÉCUTION RÉELLE"
        dd.text(((W - fe.getlength(et)) / 2, H * (0.88 if v else 0.86)), et, font=fe, fill=(120, 120, 128))
        halo = cal.filter(ImageFilter.GaussianBlur(10))
        out = np.clip(np.asarray(base, np.int16) + np.asarray(halo, np.int16) + np.asarray(cal, np.int16), 0, 255)
        return Image.fromarray(out.astype(np.uint8))

    # ---------------------------------------------------------------------------------------------- ligne et carton
    def ligne(self, p, u, d):
        im = Image.new("RGB", (self.W, self.H), ENCRE)
        spec = {"d": d, "style": "titre", "zone": "centre", "align": "centre", "taille": 1.1 if self.v else 1.25}
        return self.ty.poser(im, spec, p["texte"], u * 0.55)

    def carton(self, p, u, d):
        W, H = self.W, self.H
        im = Image.new("RGB", (W, H), ENCRE)
        dd = ImageDraw.Draw(im)
        s = min(W, H)
        a = eout(u / 0.6)
        fp = self.ty.police("titre", s * (0.15 if self.v else 0.13), "SemiBold")
        fm = self.ty.police("mono", s * 0.026, "Medium")
        fs = self.ty.police("titre", s * 0.040, "Regular")
        produit = self.film["produit"]
        marque = MARQUE["marque"]
        y = H * (0.42 if self.v else 0.38)
        tm = " ".join(marque)
        dd.text(((W - fm.getlength(tm)) / 2, y - s * 0.07), tm, font=fm, fill=tuple(int(c * a) for c in BRUME))
        tw = fp.getlength(produit)
        dd.text(((W - tw) / 2, y), produit, font=fp, fill=tuple(int(c * a) for c in OS_))
        bar_w = s * 0.06 * eout((u - 0.3) / 0.5)
        yb = y + fp.size * 1.25
        dd.rectangle([W / 2 - bar_w / 2, yb, W / 2 + bar_w / 2, yb + max(3, s * 0.005)], fill=SIG)
        a2 = eout((u - 0.6) / 0.6)
        if p.get("sous") and a2 > 0:
            st = p["sous"]
            dd.text(((W - fs.getlength(st)) / 2, yb + s * 0.045), st, font=fs, fill=tuple(int(c * a2) for c in BRUME))
        if MARQUE.get("url"):
            dd.text(((W - fm.getlength(MARQUE["url"])) / 2, H * 0.80), MARQUE["url"], font=fm, fill=BRUME)
        if self.film.get("etiquette") and a2 > 0:
            spec = {"d": d + 1, "style": "prepa", "zone": "centre", "align": "centre", "y": 0.72 if not self.v else 0.68}
            im = self.ty.poser(im, spec, self.film["etiquette"], u)
        return im

    # ---------------------------------------------------------------------------------------------- passe complète
    def rendre(self, de=0.0, a=None, pas=1):
        film = self.film
        mus = json.loads((self.dos / "musique/musique.json").read_text())
        choix = next(x for x in mus["propositions"] if x["fichier"] == mus["choix"])
        debuts, durees, ecart = recaler(film, choix)
        a = film["duree"] if a is None else a
        out = self.dos / "rendu"
        out.mkdir(exist_ok=True)
        suffixe = "" if (de == 0 and a == film["duree"] and pas == 1) else f"-extrait-{de:g}-{a:g}"
        sortie = out / f"{film['id']}-{self.fmt}-image{suffixe}.mp4"
        enc = subprocess.Popen([C.FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.W}x{self.H}", "-r", str(IPS / pas),
                                "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", str(sortie)], stdin=subprocess.PIPE)
        textes = sorted(film.get("textes", []), key=lambda x: x["t"])
        rng = np.random.default_rng(7)
        grain = [(rng.normal(0, 1, (self.H // 2, self.W // 2)) * 3.2).astype(np.int16) for _ in range(6)]
        n_tot = 0
        for i, p in enumerate(film["plans"]):
            t0, d = debuts[i], durees[i]
            if t0 + d <= de or t0 >= a:
                continue
            try:
                f = self.ouvrir(p, d)
            except (KeyError, FileNotFoundError) as e:  # plaque pas encore tournée : gris neutre (extraits de revue seulement)
                print("manque", p["id"], e, flush=True)
                gris = Image.new("RGB", (self.W, self.H), (60, 60, 64))
                f = lambda u, g=gris: g
            n = int(round(d * IPS))
            for j in range(n):
                u = j / IPS
                im = f(u)  # toujours appelé : les plaques lisent leurs images dans l'ordre
                t = t0 + u
                if t < de or t >= a or j % pas:
                    continue
                if p.get("entree") == "noir" and u < 0.7:
                    im = Image.blend(Image.new("RGB", im.size, (0, 0, 0)), im, eio(u / 0.7))
                if i == len(film["plans"]) - 1 and u > d - 0.6:
                    im = Image.blend(im, Image.new("RGB", im.size, (0, 0, 0)), eio((u - (d - 0.6)) / 0.6))
                for x in textes:
                    if x["t"] <= t < x["t"] + x["d"]:
                        spec = {"d": x["d"], "style": x["style"], "zone": x.get("zone", "haut" if x["style"] == "sur" else "centre")}
                        if x["style"] == "sur":
                            spec["y"] = (0.115 if film.get("etiquette") else 0.075) if not self.v else None
                            spec["y_v"] = 0.12 if not film.get("etiquette") else 0.105
                        if x["style"] == "impact":
                            vo = 0.62 * eio((t - x["t"]) / 0.3) * (1 - eio((t - x["t"] - x["d"] + 0.3) / 0.3))
                            im = Image.blend(im, Image.new("RGB", im.size, ENCRE), vo)
                            spec["taille"] = 0.8
                        im = self.ty.poser(im, spec, x["texte"], t - x["t"])
                if film.get("etiquette") and p["type"] not in ("carton",) and t >= film["plans"][2]["t"]:
                    spec = {"d": 99, "style": "prepa", "zone": "haut", "y": 0.05, "y_v": 0.07}
                    im = self.ty.poser(im, spec, film["etiquette"], 1.0)
                if p["type"] in ("plaque", "video"):
                    a8 = np.asarray(im, np.int16)
                    g = grain[(j // 2) % 6].repeat(2, 0).repeat(2, 1)[:self.H, :self.W, None]
                    im = Image.fromarray(np.clip(a8 + g, 0, 255).astype(np.uint8))
                enc.stdin.write(im.tobytes())
                n_tot += 1
            print(f"{film['id']} {self.fmt} {p['id']} {p['type']} {t0:.2f}+{d:.2f}", flush=True)
        enc.stdin.close()
        enc.wait()
        (out / f"plans-{self.fmt}.json").write_text(json.dumps({"debuts": debuts, "durees": durees, "ecart_moyen_s": round(ecart, 3),
                                                                 "bpm": choix["bpm"], "temps_s": choix["temps_s"], "phase_s": choix["phase_s"]}, indent=1))
        return sortie


if __name__ == "__main__":
    a = sys.argv[1:]
    film = C.charger_film(a[0])
    r = Rendu(film, a[1])
    de = float(a[a.index("--de") + 1]) if "--de" in a else 0.0
    fin = float(a[a.index("--a") + 1]) if "--a" in a else None
    print(r.rendre(de, fin, 2 if "--brouillon" in a else 1))
