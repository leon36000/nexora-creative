"""Pellicule et flous repris de video-v3/couches.py ; copie locale autonome V6."""
import hashlib
import numpy as np
from PIL import Image, ImageFilter

def graine(nom):
    return int(hashlib.sha1(nom.encode()).hexdigest()[:8], 16)

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


