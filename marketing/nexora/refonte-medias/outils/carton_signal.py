"""Neutral "Signal" end card (site redesign): 1 px precision grid, a scan line of ion light that unfolds then sweeps down
and reveals the temporary name (Geist) next to the "signal" mark (detection brackets around a point of light), then
the signature (Inter) and an optional mono label. Name, signature and colours come from ../marque.json: change the
brand there and re-render (a few seconds). Never the pixel N, never AI-drawn text.

Usage : python3 carton_signal.py out.mp4 [--format 16:9|9:16] [--lang fr|en] [--etiquette "SURVEILLANCE IA"] [--duree 5.5]
"""
import argparse, json, math, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
MARQUE = json.loads((ICI.parent / "marque.json").read_text())
POL = Path(MARQUE["polices"]["dossier"]).expanduser()
FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
IPS = 24
TAILLES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}


def hexa(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


C = {k: hexa(v) for k, v in MARQUE["couleurs"].items()}


def police(cle, taille, graisse):
    f = ImageFont.truetype(str(POL / MARQUE["polices"][cle]), taille)
    f.set_variation_by_name(graisse)
    return f


def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3


def couche_texte(texte, f, couleur, espace=0.0):
    """RGBA layer trimmed to the text (manual letter spacing when espace > 0)."""
    l = sum(f.getlength(c) + espace for c in texte) if espace else f.getlength(texte)
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (int(l + 4), asc + desc + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if espace:
        x = 0
        for c in texte:
            d.text((x, 0), c, font=f, fill=couleur + (255,)); x += f.getlength(c) + espace
    else:
        d.text((0, 0), texte, font=f, fill=couleur + (255,))
    return im


def rendre(sortie, fmt="16:9", lang="fr", etiquette=None, duree=5.5):
    W, H = TAILLES[fmt]
    m = min(W, H)
    n = round(duree * IPS)
    # --- static layers
    f_nom = police("titre", round(m * 0.105), b"SemiBold")
    f_sig = police("texte", round(m * 0.03), b"Regular")
    f_eti = police("mono", round(m * 0.017), b"Medium")
    nom = couche_texte(MARQUE["nom"], f_nom, C["texte"])
    asc, _ = f_nom.getmetrics()
    cap = round(f_nom.size * 0.72)  # cap height of Geist ≈ 0.72 em
    marque_c = round(cap * 1.05)
    ecart = round(cap * 0.42)
    larg = marque_c + ecart + nom.width
    x0 = (W - larg) // 2
    y_nom = round(H * 0.5 - asc * 0.62)  # letter top ≈ y_nom + (asc - cap)
    haut_lettres = y_nom + (asc - cap)
    bas_lettres = haut_lettres + cap
    ligne_y0, ligne_y1 = haut_lettres - round(cap * 0.35), bas_lettres + round(cap * 0.45)
    sig_lignes = MARQUE["signature"][lang].split("\n")
    sigs = [couche_texte(s, f_sig, C["texte_2"]) for s in sig_lignes]
    eti = couche_texte(etiquette.upper(), f_eti, C["ion"], espace=f_eti.size * 0.14) if etiquette else None
    # grid with radial falloff
    u = round(m / 17)
    grille = Image.new("L", (W, H), 0)
    dg = ImageDraw.Draw(grille)
    cx, cy = W // 2, H // 2
    for x in range(cx % u, W, u):
        dg.line([(x, 0), (x, H)], fill=255)
    for y in range(cy % u, H, u):
        dg.line([(0, y), (W, y)], fill=255)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.55)) ** 2)
    chute = np.clip(1 - r, 0, 1) ** 1.6
    grille = np.asarray(grille, np.float32) / 255 * chute
    fond = np.zeros((H, W, 3), np.float32) + np.array(C["abysse"], np.float32)
    # faint ion halo in the centre
    halo = np.exp(-(((xx - cx) / (W * 0.35)) ** 2 + ((yy - cy) / (H * 0.18)) ** 2))[..., None]
    filet = np.array(C["filet"], np.float32) * 1.6

    def compose_rgba(base, im, x, y, alpha=1.0, masque_bas=None):
        """Composites an RGBA image (alpha × opacity); masque_bas: rows below this y are hidden (reveal by the line)."""
        if alpha <= 0:
            return
        a = np.asarray(im, np.float32)
        h, w = a.shape[:2]
        x, y = int(x), int(y)
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(W, x + w), min(H, y + h)
        if x2 <= x1 or y2 <= y1:
            return
        sub = a[y1 - y:y2 - y, x1 - x:x2 - x]
        al = sub[..., 3:4] / 255 * alpha
        if masque_bas is not None:
            rows = np.arange(y1, y2)[:, None, None]
            al = al * np.clip((masque_bas - rows) / 6.0, 0, 1)
        base[y1:y2, x1:x2] = base[y1:y2, x1:x2] * (1 - al) + sub[..., :3] * al

    proc = subprocess.Popen([FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(IPS),
                             "-i", "-", "-f", "lavfi", "-t", f"{duree:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
                             "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac",
                             "-shortest", "-movflags", "+faststart", str(sortie)], stdin=subprocess.PIPE)
    ion = np.array(C["ion"], np.float32)
    for i in range(n):
        t = i / IPS
        img = fond.copy()
        g = ease(t / 0.9) * (0.75 - 0.35 * ease((t - 2.0) / 1.5))
        img += (filet - img) * (grille * g)[..., None]
        img += ion * 0.05 * ease(t / 2.0) * halo
        # scan line: unfolds (0.25-1.05 s), sweeps down (1.05-2.0 s), then fades out
        dep = ease((t - 0.25) / 0.8)
        balayage = ease((t - 1.05) / 0.95)
        ly = ligne_y0 + (ligne_y1 - ligne_y0) * balayage
        la = 1.0 - ease((t - 2.0) / 0.7)
        if dep > 0 and la > 0:
            demi = W * 0.5 * dep
            xs = np.arange(W)
            prof = np.clip((demi - np.abs(xs - cx)) / (W * 0.08), 0, 1)  # soft ends
            for dy, k in ((0, 1.0), (1, 0.55), (-1, 0.55), (2, 0.18), (-2, 0.18)):
                yl = int(ly) + dy
                if 0 <= yl < H:
                    img[yl] += (np.array([255, 255, 255], np.float32) * 0.35 + ion * 0.65 - img[yl]) * (prof * k * la)[:, None]
            # glow
            band = np.exp(-((np.arange(H) - ly) / (m * 0.012)) ** 2)[:, None, None]
            img += ion * 0.35 * la * band * prof[None, :, None]
        # name revealed above the line, then fully kept
        revele = ly if t < 2.0 else H
        if t >= 1.05:
            compose_rgba(img, nom, x0 + marque_c + ecart, y_nom, 1.0, masque_bas=revele + cap * 0.08)
        # signal mark: brackets + point (appears with the line)
        if t >= 1.05:
            mk = Image.new("RGBA", (marque_c + 8, marque_c + 8), (0, 0, 0, 0))
            d = ImageDraw.Draw(mk)
            e = max(2, round(m * 0.0022)); b = round(marque_c * 0.3); s = marque_c
            col = C["texte"] + (255,)
            for (px, py, sx, sy) in ((0, 0, 1, 1), (s, 0, -1, 1), (0, s, 1, -1), (s, s, -1, -1)):
                d.line([(px, py), (px + sx * b, py)], fill=col, width=e)
                d.line([(px, py), (px, py + sy * b)], fill=col, width=e)
            pul = 1 + 0.5 * math.exp(-((t - 2.0) / 0.25) ** 2)
            rr = marque_c * 0.13 * pul
            d.ellipse([s / 2 - rr, s / 2 - rr, s / 2 + rr, s / 2 + rr], fill=C["ion"] + (255,))
            lueur = mk.filter(ImageFilter.GaussianBlur(marque_c * 0.08))
            compose_rgba(img, lueur, x0, haut_lettres - (marque_c - cap) // 2, 0.6, masque_bas=revele + cap * 0.08)
            compose_rgba(img, mk, x0, haut_lettres - (marque_c - cap) // 2, 1.0, masque_bas=revele + cap * 0.08)
        # signature
        a_sig = ease((t - 2.15) / 0.8)
        if a_sig > 0:
            y = bas_lettres + round(cap * 0.85) + round(m * 0.01 * (1 - a_sig))
            for s in sigs:
                compose_rgba(img, s, (W - s.width) // 2, y, a_sig)
                y += round(f_sig.size * 1.35)
        if eti is not None:
            a_e = ease((t - 2.5) / 0.7)
            if a_e > 0:
                compose_rgba(img, eti, (W - eti.width) // 2, haut_lettres - round(cap * 1.25) - eti.height, a_e)
        proc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    if proc.wait():
        raise SystemExit("ffmpeg a échoué")
    return sortie


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("sortie"); a.add_argument("--format", default="16:9"); a.add_argument("--lang", default="fr")
    a.add_argument("--etiquette"); a.add_argument("--duree", type=float, default=5.5)
    o = a.parse_args()
    print(rendre(o.sortie, o.format, o.lang, o.etiquette, o.duree))
