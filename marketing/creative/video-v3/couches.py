"""Compositeur de la promo V3 : un plan = une plaque MiniMax H3 + des couches calculées en code, image par image.

L'échelle vient de la composition : des milliers de vaisseaux minuscules en parallaxe, des centaines de traçants et de
tirs plasma, des explosions lointaines, des débris, des éclairs d'impact, puis le traitement « pellicule » commun à tous
les plans (étalonnage froid/chaud, halo, reflets anamorphiques, tremblement caméra, grain, vignette, cache 2,39).
Tout est déterministe (graine = nom du plan) et reproductible ; seul numpy, Pillow et ffmpeg sont utilisés.

API : rendre_plan(spec, largeur, hauteur, images, sortie_rgb) écrit les images brutes (rgb24) dans un fichier ou un tube.
Le format de spec est documenté dans montage-v3.json (champ « _schema »).
"""
import hashlib
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FFPROBE = str(Path(FFMPEG).with_name("ffprobe"))
IPS = 24

# Teintes (linéaires approximatives, peuvent dépasser 1 : la courbe d'épaule les ramène au blanc)
TEINTES = {
    "orange": (1.6, 0.75, 0.25), "blanc": (1.6, 1.5, 1.35), "bleu": (0.45, 0.85, 1.7), "rouge": (1.5, 0.35, 0.15),
    "vert": (0.5, 1.5, 0.6), "ambre": (1.5, 1.0, 0.45), "cyan": (0.4, 1.3, 1.6),
}


def graine(nom: str) -> int:
    return int(hashlib.sha1(nom.encode()).hexdigest()[:8], 16)


# --------------------------------------------------------------------------------------------- lecture des plaques
def sonder(fichier: str) -> tuple[int, int, int]:
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=width,height,nb_read_packets", "-of", "csv=p=0", fichier], capture_output=True, text=True)
    w, h, n = r.stdout.strip().split(",")[:3]
    return int(w), int(h), int(n)


def lire_plaque(fichier: str) -> np.ndarray:
    w, h, _n = sonder(fichier)
    brut = subprocess.run([FFMPEG, "-v", "error", "-i", fichier, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(brut, dtype=np.uint8).reshape(-1, h, w, 3)


def image_fixe(fichier: str) -> np.ndarray:
    return np.asarray(Image.open(fichier).convert("RGB"))[None]


# --------------------------------------------------------------------------------------------- outils
def bruit_lisse(rng: np.random.Generator, n: int, douceur: float) -> np.ndarray:
    """Bruit 1-D lissé (tremblement caméra) : marche aléatoire filtrée, centrée, amplitude ~1."""
    x = rng.normal(size=n + 64)
    k = max(1, int(douceur))
    noyau = np.hanning(2 * k + 1)
    noyau /= noyau.sum()
    y = np.convolve(x, noyau, mode="same")[32:32 + n]
    return y / (np.abs(y).max() + 1e-6)


def tuile_bruit(rng: np.random.Generator, taille=256, octaves=5) -> np.ndarray:
    """Bruit fractal (somme d'octaves de bruit de valeur) en tuile, 0..1."""
    total = np.zeros((taille, taille), np.float32)
    amp, somme = 1.0, 0.0
    for o in range(octaves):
        c = 4 * 2 ** o
        g = rng.random((c, c)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((taille, taille), Image.BICUBIC)
        total += amp * np.asarray(im, np.float32) / 255
        somme += amp
        amp *= 0.55
    total /= somme
    return (total - total.min()) / (total.max() - total.min() + 1e-6)


def flou(a: np.ndarray, rayon: float, reduction: int = 4) -> np.ndarray:
    """Flou gaussien rapide d'une couche float (H, W, 3) : réduction, flou PIL par canal, agrandissement."""
    h, w = a.shape[:2]
    pw, ph = max(2, w // reduction), max(2, h // reduction)
    canaux = []
    for c in range(a.shape[2]):
        m = float(a[..., c].max())
        if m <= 1e-5:
            canaux.append(np.zeros((h, w), np.float32))
            continue
        im = Image.fromarray(np.clip(a[..., c] / m * 255, 0, 255).astype(np.uint8)).resize((pw, ph), Image.BILINEAR)
        im = im.filter(ImageFilter.GaussianBlur(rayon / reduction)).resize((w, h), Image.BILINEAR)
        canaux.append(np.asarray(im, np.float32) / 255 * m)
    return np.stack(canaux, -1)


def trainee_horizontale(a: np.ndarray, facteur_x: int = 48, facteur_y: int = 3) -> np.ndarray:
    """Étirement horizontal (reflet anamorphique) : on écrase fortement en X puis on réagrandit."""
    h, w = a.shape[:2]
    out = np.zeros_like(a)
    for c in range(a.shape[2]):
        m = float(a[..., c].max())
        if m <= 1e-5:
            continue
        im = Image.fromarray(np.clip(a[..., c] / m * 255, 0, 255).astype(np.uint8))
        im = im.resize((max(2, w // facteur_x), max(2, h // facteur_y)), Image.BOX).resize((w, h), Image.BILINEAR)
        out[..., c] = np.asarray(im, np.float32) / 255 * m
    return out


# --------------------------------------------------------------------------------------------- couches d'effets
class Couches:
    """Toutes les couches d'un plan. Les coordonnées des specs sont normalisées (0..1) dans l'image utile."""

    def __init__(self, spec: dict, W: int, H: int, n: int):
        self.s, self.W, self.H, self.n = spec, W, H, n
        self.rng = np.random.default_rng(graine(spec["nom"]))
        self.effets = spec.get("effets", [])
        self.echelle = min(W, H) / 1080  # tailles de specs données pour une image de 1080 de petit côté
        self.prepare()

    # -- préparation déterministe de tous les objets
    def prepare(self):
        rng, W, H, n = self.rng, self.W, self.H, self.n
        self.flottes, self.traceurs, self.explosions, self.debris, self.rayons, self.flashs = [], [], [], [], [], []
        for e in self.effets:
            t = e["type"]
            if t == "flotte":
                k = int(e.get("n", 800))
                x0, y0, x1, y1 = e.get("zone", [0, 0, 1, 1])
                prof = rng.uniform(*e.get("profondeur", [1, 6]), k)
                # densité en bandes (formations) : une partie des vaisseaux s'aligne sur des « murs »
                xs = rng.uniform(x0, x1, k)
                ys = rng.uniform(y0, y1, k)
                if e.get("mur"):
                    bandes = rng.uniform(y0, y1, max(2, k // 120))
                    idx = rng.integers(0, len(bandes), k)
                    pente = e.get("pente", 0.0)
                    ys = np.where(rng.random(k) < 0.75, bandes[idx] + (xs - 0.5) * pente + rng.normal(0, 0.006, k), ys)
                cap = e.get("cap", 0.0)  # orientation des vaisseaux (radians, 0 = vers la droite)
                self.flottes.append({
                    "x": xs * W, "y": ys * H, "z": prof, "cap": cap + rng.normal(0, e.get("dispersion_cap", 0.08), k),
                    "taille": rng.uniform(*e.get("taille", [2, 7]), k) * self.echelle / prof ** 0.5,
                    "derive": np.array(e.get("derive", [-30, 0]), np.float32) * self.echelle,
                    "teinte": TEINTES[e.get("moteurs", "bleu")], "sombre": e.get("silhouette", True),
                    "lueur": e.get("lueur", 1.0), "clignote": rng.random(k), "propre": rng.normal(0, 1, (k, 2)) * e.get("agitation", 4) * self.echelle,
                    "feu": rng.random(k) < e.get("part_tir", 0.0),
                })
            elif t == "traceurs":
                duree = n / IPS
                k = int(e.get("par_s", 30) * duree)
                src, dst = e.get("source", [0, 0.4, 0.2, 0.6]), e.get("cible", [0.8, 0.3, 1, 0.7])
                t0 = rng.uniform(-1.0, duree, k)
                # tirs en rafales : un émetteur tire plusieurs coups de suite
                rafale = int(e.get("rafale", 1))
                if rafale > 1:
                    base = rng.uniform(-1.0, duree, max(1, k // rafale))
                    t0 = (base[:, None] + np.arange(rafale)[None] * e.get("cadence", 0.07)).ravel()[:k]
                    k = len(t0)
                    sx = np.repeat(rng.uniform(src[0], src[2], len(base)), rafale)[:k]
                    sy = np.repeat(rng.uniform(src[1], src[3], len(base)), rafale)[:k]
                    dx = np.repeat(rng.uniform(dst[0], dst[2], len(base)), rafale)[:k] + rng.normal(0, 0.01, k)
                    dy = np.repeat(rng.uniform(dst[1], dst[3], len(base)), rafale)[:k] + rng.normal(0, 0.01, k)
                else:
                    sx, sy = rng.uniform(src[0], src[2], k), rng.uniform(src[1], src[3], k)
                    dx, dy = rng.uniform(dst[0], dst[2], k), rng.uniform(dst[1], dst[3], k)
                self.traceurs.append({
                    "t0": t0, "sx": sx * W, "sy": sy * H, "dx": dx * W, "dy": dy * H,
                    "vitesse": rng.uniform(0.8, 1.2, k) * e.get("vitesse", 1.6),  # traversées par seconde (1 = trajet en 1 s)
                    "longueur": e.get("longueur", 0.12), "epaisseur": e.get("epaisseur", 2.0) * self.echelle,
                    "teinte": TEINTES[e.get("couleur", "orange")], "force": e.get("force", 1.0),
                    "impacts": e.get("impacts", 0.0), "pi": rng.random(k),
                })
            elif t == "explosions":
                liste = list(e.get("liste", []))
                if "par_s" in e:
                    duree = n / IPS
                    k = int(e["par_s"] * duree + 0.5)
                    z = e.get("zone", [0.1, 0.1, 0.9, 0.9])
                    for _ in range(k):
                        liste.append({"t": float(rng.uniform(-0.3, duree)), "x": float(rng.uniform(z[0], z[2])), "y": float(rng.uniform(z[1], z[3])),
                                      "taille": float(rng.uniform(*e.get("taille", [10, 40])))})
                for x in liste:
                    x = dict(x)
                    x.setdefault("duree", e.get("duree", 1.4))
                    x.setdefault("couleur", e.get("couleur", "orange"))
                    x["graine"] = int(rng.integers(0, 1 << 30))
                    x["eclaire"] = x.get("eclaire", e.get("eclaire", 0.0))
                    self.explosions.append(x)
            elif t == "debris":
                k = int(e.get("n", 120))
                ox, oy = e.get("origine", [0.5, 0.5])
                ang = rng.uniform(0, 2 * math.pi, k)
                v = rng.uniform(0.2, 1.0, k) ** 0.6 * e.get("vitesse", 500) * self.echelle
                self.debris.append({
                    "t0": e.get("t", 0.0), "x": ox * W, "y": oy * H, "vx": np.cos(ang) * v, "vy": np.sin(ang) * v + e.get("gravite", 0) * 0,
                    "taille": rng.uniform(*e.get("taille", [2, 9]), k) * self.echelle, "braise": rng.random(k) < e.get("braises", 0.5),
                    "rot": rng.uniform(0, math.pi, k), "vr": rng.normal(0, 4, k), "vers_camera": e.get("vers_camera", 0.0),
                    "duree": e.get("duree", 3.0),
                })
            elif t == "rayon":
                self.rayons.append(e)
            elif t == "flash":
                self.flashs.append(e)
        self.bruits = [tuile_bruit(np.random.default_rng(graine(self.s["nom"]) + i), 192) for i in range(4)]

    # -- dessin d'une image : renvoie (lumière additive, assombrissement 0..1) aux dimensions du canevas
    def dessiner(self, i: int, ox: float, oy: float) -> tuple[np.ndarray, np.ndarray]:
        W, H = self.W, self.H
        t = i / IPS
        lum = Image.new("RGB", (W, H))
        lumc = Image.new("RGB", (W, H))  # cœurs nets (non floutés)
        omb = Image.new("L", (W, H))
        dl, dc, do = ImageDraw.Draw(lum), ImageDraw.Draw(lumc), ImageDraw.Draw(omb)

        def couleur(teinte, k):
            return tuple(int(min(255, max(0, c / 1.7 * 255 * k))) for c in teinte)

        # flottes : silhouettes sombres + lueurs de réacteurs, parallaxe selon la profondeur
        for f in self.flottes:
            px = f["x"] + (f["derive"][0] * t + ox) / f["z"] + f["propre"][:, 0] * math.sin(t * 0.7)
            py = f["y"] + (f["derive"][1] * t + oy) / f["z"] + f["propre"][:, 1] * math.cos(t * 0.6)
            px = np.mod(px + W * 0.1, W * 1.2) - W * 0.1
            for j in np.argsort(-f["z"]):
                x, y, s, a = px[j], py[j], f["taille"][j], f["cap"][j]
                if not (-20 < x < W + 20 and -20 < y < H + 20):
                    continue
                ca, sa = math.cos(a), math.sin(a)
                if f["sombre"] and s > 1.6:
                    long, larg = s * 2.4, s * 0.55
                    pts = [(x + ca * long, y + sa * long), (x - sa * larg - ca * long * 0.6, y + ca * larg - sa * long * 0.6),
                           (x + sa * larg - ca * long * 0.6, y - ca * larg - sa * long * 0.6)]
                    do.polygon(pts, fill=int(200 / f["z"][j] ** 0.3))
                    # liseré éclairé par le soleil / la planète
                    dc.line([pts[0], pts[1]], fill=(26, 30, 38), width=1)
                k = f["lueur"] * (0.55 + 0.45 * math.sin(t * 9 + f["clignote"][j] * 40)) / f["z"][j] ** 0.4
                ex, ey = x - ca * s * 1.6, y - sa * s * 1.6
                r = max(0.6, s * 0.35)
                dl.ellipse([ex - r * 2.2, ey - r * 2.2, ex + r * 2.2, ey + r * 2.2], fill=couleur(f["teinte"], k * 0.55))
                dc.ellipse([ex - r * 0.6, ey - r * 0.6, ex + r * 0.6, ey + r * 0.6], fill=couleur(TEINTES["blanc"], k))
                if f["feu"][j] and (int(t * 12 + j) % 7 == 0):
                    lx, ly = x + ca * s * 30, y + sa * s * 30
                    dc.line([(x + ca * s * 3, y + sa * s * 3), (lx, ly)], fill=couleur(f["teinte"], 1.0), width=1)

        # les flottes vivent sur leurs propres couches : elles passent DERRIÈRE les coques claires de la plaque
        flum = np.asarray(lum, np.float32) / 255 * 1.7
        flumc = np.asarray(lumc, np.float32) / 255 * 1.7
        fomb = np.asarray(omb, np.float32) / 255
        if self.flottes:
            flum = flum * 0.6 + flou(flum, 8 * self.echelle, 4) * 0.75
            lum, lumc, omb = Image.new("RGB", (W, H)), Image.new("RGB", (W, H)), Image.new("L", (W, H))
            dl, dc, do = ImageDraw.Draw(lum), ImageDraw.Draw(lumc), ImageDraw.Draw(omb)
        self.derniere_flotte = (flum + flumc, fomb)
        # traceurs : segments lumineux (flou de bougé = longueur), rafales, petits impacts au bout
        for tr in self.traceurs:
            age = (t - tr["t0"]) * tr["vitesse"]
            vis = (age > 0) & (age < 1 + tr["longueur"])
            for j in np.nonzero(vis)[0]:
                a1 = min(1.0, age[j])
                a0 = max(0.0, age[j] - tr["longueur"])
                x1 = tr["sx"][j] + (tr["dx"][j] - tr["sx"][j]) * a1 + ox * 0.3
                y1 = tr["sy"][j] + (tr["dy"][j] - tr["sy"][j]) * a1 + oy * 0.3
                x0 = tr["sx"][j] + (tr["dx"][j] - tr["sx"][j]) * a0 + ox * 0.3
                y0 = tr["sy"][j] + (tr["dy"][j] - tr["sy"][j]) * a0 + oy * 0.3
                e = tr["epaisseur"]
                dl.line([(x0, y0), (x1, y1)], fill=couleur(tr["teinte"], 0.9 * tr["force"]), width=max(1, int(e * 2.5)))
                dc.line([(x0, y0), (x1, y1)], fill=couleur(TEINTES["blanc"], 0.85 * tr["force"]), width=max(1, int(e)))
                if age[j] >= 1 and tr["pi"][j] < tr["impacts"]:
                    r = e * 6 * (1.4 - (age[j] - 1) / tr["longueur"])
                    dl.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=couleur(TEINTES["orange"], 1.0))

        # rayons (bordées de vaisseaux capitaux) : faisceau épais qui s'allume, pulse et s'éteint
        for r in self.rayons:
            t0, t1 = r["t"]
            if not (t0 <= t <= t1 + 0.15):
                continue
            k = min(1.0, (t - t0) / 0.06) * (1.0 if t <= t1 else max(0.0, 1 - (t - t1) / 0.15))
            k *= 0.85 + 0.15 * math.sin(t * 60)
            (xa, ya), (xb, yb) = r["de"], r["a"]
            pa, pb = (xa * W + ox * 0.3, ya * H + oy * 0.3), (xb * W + ox * 0.3, yb * H + oy * 0.3)
            ep = r.get("epaisseur", 6) * self.echelle
            te = TEINTES[r.get("couleur", "bleu")]
            dl.line([pa, pb], fill=couleur(te, k * 0.6), width=int(ep * 2.5))
            dc.line([pa, pb], fill=couleur(TEINTES["blanc"], k), width=max(1, int(ep)))
            re = ep * 5 * k
            dl.ellipse([pb[0] - re, pb[1] - re, pb[0] + re, pb[1] + re], fill=couleur(TEINTES["blanc"], k))

        lum_np = np.asarray(lum, np.float32) / 255 * 1.7
        lumc_np = np.asarray(lumc, np.float32) / 255 * 1.7
        omb_np = np.asarray(omb, np.float32) / 255

        # explosions : boule de feu bruitée qui s'étend et refroidit, puis fumée qui assombrit
        for x in self.explosions:
            age = (t - x["t"]) / x["duree"]
            if not (0 <= age <= 1):
                continue
            self.boule(lum_np, omb_np, x, age, ox, oy)

        # débris : morceaux sombres en rotation (flou de bougé) et braises incandescentes
        for d in self.debris:
            age = t - d["t0"]
            if age < 0 or age > d["duree"]:
                continue
            croissance = 1 + d["vers_camera"] * age ** 2
            xs = d["x"] + d["vx"] * age * croissance + ox * 0.5
            ys = d["y"] + d["vy"] * age * croissance + oy * 0.5
            im = Image.new("L", (W, H))
            dd = ImageDraw.Draw(im)
            imb = Image.new("RGB", (W, H))
            db = ImageDraw.Draw(imb)
            for j in range(len(xs)):
                s = d["taille"][j] * croissance
                if d["braise"][j]:
                    k = max(0.0, 1 - age / d["duree"]) * (0.6 + 0.4 * math.sin(age * 20 + j))
                    # traînée de bougé
                    db.line([(xs[j] - d["vx"][j] * croissance / IPS, ys[j] - d["vy"][j] * croissance / IPS), (xs[j], ys[j])],
                            fill=(int(255 * k), int(150 * k), int(50 * k)), width=max(1, int(s * 0.35)))
                else:
                    a = d["rot"][j] + d["vr"][j] * age
                    pts = [(xs[j] + math.cos(a + q * 2.1) * s * (0.6 + 0.4 * ((j + q) % 3) / 2), ys[j] + math.sin(a + q * 2.1) * s * 0.8) for q in range(3)]
                    dd.polygon(pts, fill=230)
            omb_np = np.maximum(omb_np, np.asarray(im, np.float32) / 255 * 0.95)
            lumc_np += np.asarray(imb, np.float32) / 255 * 1.6

        # halo de toutes les sources (flou large) + cœurs nets
        halo = flou(lum_np, 8 * self.echelle, 4) * 0.75 + flou(lum_np, 34 * self.echelle, 8) * 0.3
        return lum_np * 0.6 + halo + lumc_np, omb_np

    def boule(self, lum, omb, x, age, ox, oy):
        W, H = self.W, self.H
        R = x["taille"] * self.echelle * (0.35 + 0.65 * (1 - (1 - age) ** 3)) * 1.0
        cx, cy = x["x"] * W + ox * 0.4, x["y"] * H + oy * 0.4
        m = int(R * 1.6) + 2
        x0, y0, x1, y1 = int(cx - m), int(cy - m), int(cx + m), int(cy + m)
        if x1 < 0 or y1 < 0 or x0 >= W or y0 >= H or m < 2:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(R, 1)
        tex = self.bruits[x["graine"] % 4]
        ts = tex.shape[0]
        u = ((xx - cx) / max(R, 1) * 40 + x["graine"] % 97 + age * 25).astype(np.int32) % ts
        v = ((yy - cy) / max(R, 1) * 40 + x["graine"] % 89 - age * 18).astype(np.int32) % ts
        nz = tex[v, u]
        dens = np.clip(1.15 - d - (nz - 0.5) * 0.9, 0, 1) ** 1.5
        chaleur = np.clip((1 - age * 1.25) * (1.2 - d * 0.8) + (nz - 0.5) * 0.5, 0, 1)
        te = np.array(TEINTES.get(x["couleur"], TEINTES["orange"]), np.float32)
        col = (te[None, None] * chaleur[..., None] ** 1.2 + np.array([1.4, 1.3, 1.1], np.float32) * chaleur[..., None] ** 4 * 1.5) * dens[..., None]
        # éclair initial
        if age < 0.12:
            col += np.exp(-d * 2.5)[..., None] * (1 - age / 0.12) * 3.0
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x1), min(H, y1)
        cut = (slice(sy0 - y0, sy1 - y0), slice(sx0 - x0, sx1 - x0))
        lum[sy0:sy1, sx0:sx1] += col[cut] * (1.0 - 0.3 * age)
        fumee = np.clip(dens * np.clip(age * 1.8 - 0.2, 0, 1) * 0.7, 0, 1)
        omb[sy0:sy1, sx0:sx1] = np.maximum(omb[sy0:sy1, sx0:sx1], fumee[cut])

    def eclairage(self, t: float) -> np.ndarray:
        """Lumière globale ajoutée à l'image : éclairs d'explosion proches et flashs d'impact (couleur, 0..)."""
        k = np.zeros(3, np.float32)
        for x in self.explosions:
            if x["eclaire"] > 0:
                age = (t - x["t"]) / x["duree"]
                if 0 <= age <= 1:
                    k += np.array(TEINTES[x["couleur"]], np.float32) * x["eclaire"] * math.exp(-age * 7)
        for f in self.flashs:
            dt = t - f["t"]
            if 0 <= dt <= f.get("duree", 0.25):
                k += np.array(TEINTES[f.get("couleur", "blanc")], np.float32) * f.get("force", 1.0) * (1 - dt / f.get("duree", 0.25)) ** 2
        return k


# --------------------------------------------------------------------------------------------- traitement pellicule
class Pellicule:
    def __init__(self, W, H, nom, reglages):
        self.W, self.H, self.r = W, H, reglages
        rng = np.random.default_rng(graine(nom) + 7)
        self.grains = [np.asarray(Image.fromarray((np.clip(rng.normal(0.5, 0.18, (H // 2, W // 2)), 0, 1) * 255).astype(np.uint8))
                                  .resize((W, H), Image.BILINEAR), np.float32) / 255 - 0.5 for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vignette = (1 - reglages.get("vignette", 0.32) * np.clip(d - 0.35, 0, None) ** 1.6)[..., None]
        self.rng = rng

    def etalonner(self, x: np.ndarray) -> np.ndarray:
        r = self.r
        x = x * r.get("exposition", 1.0)
        # séparation froid/chaud : ombres bleu acier, hautes lumières orangées
        l = (x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11)[..., None]
        ombre = np.clip(1 - l * 2.2, 0, 1)
        haute = np.clip((l - 0.45) * 1.8, 0, 1)
        x = x + ombre * np.array(r.get("teinte_ombres", [-0.012, 0.004, 0.03]), np.float32) \
              + haute * np.array(r.get("teinte_hautes", [0.05, 0.01, -0.04]), np.float32)
        sat = r.get("saturation", 0.92)
        l = (x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11)[..., None]
        x = l + (x - l) * sat
        # contraste en S doux autour de 0,4 et noirs denses
        c = r.get("contraste", 1.12)
        x = 0.4 + (x - 0.4) * c
        x = np.clip(x - r.get("noir", 0.012), 0, None)
        return x

    def finir(self, x: np.ndarray, i: int, lettre: bool) -> np.ndarray:
        r = self.r
        # halo (bloom) et reflets anamorphiques sur les hautes lumières
        lum = (x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11)[..., None]
        hautes = np.clip(lum - r.get("seuil_halo", 0.88), 0, None) * x / (lum + 1e-4)
        if hautes.max() > 1e-3:
            x = x + flou(hautes, 22, 8) * r.get("halo", 0.3)
            tr = trainee_horizontale(np.clip(lum - r.get("seuil_reflet", 0.97), 0, None), 40, 4)
            x = x + tr * np.array([0.35, 0.6, 1.25], np.float32) * r.get("reflet", 0.7)
        # épaule douce : les sources très fortes roulent vers le blanc au lieu d'écrêter
        s = 0.82
        x = np.where(x < s, x, s + (1 - s) * (1 - np.exp(-(x - s) / (1 - s))))
        x = x * self.vignette
        g = self.grains[(i * 5 + int(self.rng.integers(0, 6))) % 6]
        lum = (x[..., 0] * 0.3 + x[..., 1] * 0.59 + x[..., 2] * 0.11)[..., None]
        x = x + g[..., None] * r.get("grain", 0.05) * (0.4 + 0.6 * (1 - np.abs(lum - 0.4)))
        x = np.clip(x, 0, 1)
        if lettre:  # cache 2,39:1 dans le 16:9
            b = int(round((self.H - self.W / 2.39) / 2))
            x[:b] = 0
            x[self.H - b:] = 0
        return x


# --------------------------------------------------------------------------------------------- suivi du mouvement de la plaque
def suivre(frames: np.ndarray) -> np.ndarray:
    """Translation globale cumulée de la plaque (pixels source) par corrélation de phase, pour que les couches collent
    au mouvement de caméra du plan."""
    n = len(frames)
    g = [np.asarray(Image.fromarray(f).convert("L").resize((320, 180)), np.float32) for f in frames]
    fen = np.outer(np.hanning(180), np.hanning(320)).astype(np.float32)
    pos = np.zeros((n, 2), np.float32)
    sx, sy = frames.shape[2] / 320, frames.shape[1] / 180
    for k in range(1, n):
        A, B = np.fft.fft2(g[k - 1] * fen), np.fft.fft2(g[k] * fen)
        R = A * np.conj(B)
        R /= np.abs(R) + 1e-6
        c = np.fft.ifft2(R).real
        py, px = np.unravel_index(np.argmax(c), c.shape)
        if py > 90:
            py -= 180
        if px > 160:
            px -= 320
        pos[k] = pos[k - 1] - np.array([px * sx, py * sy])
    return pos


# --------------------------------------------------------------------------------------------- rendu d'un plan
def temps_source(spec: dict, n: int, n_src: int) -> np.ndarray:
    """Instant source (en images) de chaque image de sortie : début, vitesse constante ou rampe [[t_sortie, vitesse], …]."""
    debut = spec.get("debut", 0.0) * IPS
    v = spec.get("vitesse", 1.0)
    if isinstance(v, list):
        ts, vs = zip(*v)
        vit = np.interp(np.arange(n) / IPS, ts, vs)
    else:
        vit = np.full(n, float(v))
    pos = debut + np.concatenate([[0], np.cumsum(vit[:-1])])
    if spec.get("inverse"):
        pos = debut - np.concatenate([[0], np.cumsum(vit[:-1])])
    return np.clip(pos, 0, n_src - 1.001)


def cadrage(spec: dict, t: float, vertical: bool) -> tuple[float, float, float]:
    """(centre x, centre y, zoom) normalisés : clés « cadre » [[t, cx, cy, zoom], …] (cadre_v en vertical)."""
    cles = spec.get("cadre_v" if vertical else "cadre") or spec.get("cadre") or [[0, 0.5, 0.5, 1.0]]
    cles = sorted(cles)
    ts = [c[0] for c in cles]
    return tuple(float(np.interp(t, ts, [c[q] for c in cles])) for q in (1, 2, 3))


def rendre_plan(spec: dict, W: int, H: int, n: int, ecrire, reglages: dict, vertical: bool = False, lettre: bool = True):
    """Calcule les n images du plan et les passe une à une à ecrire(bytes rgb24)."""
    src = image_fixe(spec["image"]) if spec.get("image") else lire_plaque(spec["plaque"])
    if spec.get("miroir"):
        src = src[:, :, ::-1]
    n_src, sh, sw = src.shape[:3]
    pos = temps_source(spec, n, n_src)
    marge = int(0.045 * max(W, H))
    CW, CH = W + 2 * marge, H + 2 * marge
    rng = np.random.default_rng(graine(spec["nom"]) + 3)
    # tremblement caméra : fond permanent + coups aux impacts, décroissance rapide
    sec = spec.get("secousse", {})
    base = sec.get("base", 0.0) * min(W, H) / 1080
    bx, by = bruit_lisse(rng, n, 3), bruit_lisse(rng, n, 3)
    lent_x, lent_y = bruit_lisse(rng, n, 14), bruit_lisse(rng, n, 14)
    amp = np.full(n, base)
    for c in sec.get("coups", []):
        k0 = int(c["t"] * IPS)
        for k in range(k0, n):
            amp[k] += c.get("force", 20) * min(W, H) / 1080 * math.exp(-(k - k0) / (c.get("tenue", 0.25) * IPS))
    dxs = bx * amp + lent_x * sec.get("derive", 6) * min(W, H) / 1080
    dys = by * amp + lent_y * sec.get("derive", 6) * min(W, H) / 1080
    suivi = suivre(src) if spec.get("suivi") and n_src > 1 else np.zeros((n_src, 2), np.float32)
    couches = Couches(spec, CW, CH, n)
    pell = Pellicule(W, H, spec["nom"], {**reglages, **spec.get("etalonnage", {})})
    fouet = spec.get("fouet")  # {"entree": images, "sortie": images, "sens": ±1}
    precedent = None
    for i in range(n):
        t = i / IPS
        p = pos[i]
        a = int(p)
        b = min(n_src - 1, a + 1)
        w = p - a
        fr = src[a].astype(np.float32) if w < 0.02 or a == b else src[a].astype(np.float32) * (1 - w) + src[b].astype(np.float32) * w
        cx, cy, z = cadrage(spec, t, vertical)
        # fenêtre source au rapport du canevas, zoomée ; la marge du canevas absorbe le tremblement
        ratio = CW / CH
        fh = sh / z if sw / sh > ratio else sw / ratio / z
        fw = fh * ratio
        fw, fh = min(fw, sw), min(fh, sh)
        x0 = np.clip(cx * sw - fw / 2, 0, sw - fw)
        y0 = np.clip(cy * sh - fh / 2, 0, sh - fh)
        im = Image.fromarray(fr.astype(np.uint8)).resize((CW, CH), Image.LANCZOS, box=(x0, y0, x0 + fw, y0 + fh))
        im = im.filter(ImageFilter.UnsharpMask(2, 60, 2))
        x = np.asarray(im, np.float32) / 255
        x = pell.etalonner(x)
        # couches de code, recalées sur le mouvement de la plaque
        sx = CW / fw
        ox, oy = (suivi[a] if len(suivi) > a else (0, 0))
        ox, oy = ox * sx, oy * sx
        lum, omb = couches.dessiner(i, ox, oy)
        if couches.flottes:
            fl, fo = couches.derniere_flotte
            pl = np.asarray(Image.fromarray(np.clip(x.mean(-1) * 255, 0, 255).astype(np.uint8)).resize((CW // 8, CH // 8), Image.BILINEAR)
                            .filter(ImageFilter.GaussianBlur(1.5)).resize((CW, CH), Image.BILINEAR), np.float32) / 255
            libre = np.clip(1 - (pl - spec.get("seuil_occultation", 0.42)) / 0.2, 0, 1)
            x = x * (1 - fo[..., None] * 0.85 * libre[..., None]) + fl * libre[..., None]
        x = x * (1 - omb[..., None] * 0.92) + lum
        x = x + couches.eclairage(t)[None, None] * (0.25 + x)
        # fouet (whip pan) : décalage et flou horizontal violents en tête ou en queue de plan
        if fouet:
            kf = 0.0
            if i < fouet.get("entree", 0):
                kf = 1 - i / fouet["entree"]
            elif i >= n - fouet.get("sortie", 0):
                kf = -(i - (n - fouet["sortie"]) + 1) / fouet["sortie"]
            if kf:
                d = int(kf * CW * 0.35 * fouet.get("sens", 1))
                x = np.roll(x, d, axis=1)
                x = trainee_horizontale(x, int(8 + 60 * abs(kf)), 1) * 0.85 + x * 0.15
        # tremblement : recadrage décalé dans la marge
        ox_, oy_ = int(np.clip(marge + dxs[i], 0, 2 * marge)), int(np.clip(marge + dys[i], 0, 2 * marge))
        x = x[oy_:oy_ + H, ox_:ox_ + W]
        # flou de bougé pendant les grosses secousses : mélange avec l'image précédente
        if precedent is not None and amp[i] - base > 10 * min(W, H) / 1080:
            x = x * 0.62 + precedent * 0.38
        precedent = x
        x = pell.finir(x, i, lettre and not vertical)
        # image d'impact : surexposée et désaturée une image
        if spec.get("impact") and i < spec.get("impact_images", 1):
            l = x.mean(-1, keepdims=True)
            x = np.clip(l * 2.2 + 0.25, 0, 1) * np.array([1, 0.97, 0.92], np.float32)
        if spec.get("fondu_noir_sortie") and i >= n - spec["fondu_noir_sortie"]:
            x = x * (n - i) / (spec["fondu_noir_sortie"] + 1)
        if spec.get("fondu_noir_entree") and i < spec["fondu_noir_entree"]:
            x = x * (i + 1) / (spec["fondu_noir_entree"] + 1)
        ecrire((x * 255 + 0.5).astype(np.uint8).tobytes())
