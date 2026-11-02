"""Rendu d'un film de la campagne : réutilise le moteur de la promo V4 (`marketing/creative/video-v4/monter_v4.py` : segments
en parallèle avec cache, étalonnage et grain de `video-v3/couches.py`, bruitages `video-v3/sfx_v3.py`, mixage −14 LUFS) et
remplace trois pièces :
  - les textes : `typo.py` (typographie cinétique) au lieu des pastilles de la V4 ;
  - les segments « ui » : présentés en « écran » (capture recadrée dans une carte arrondie sur fond d'encre, texte dans la
    marge sombre), avec curseur et clic dessinés aux positions réelles des clics ; « plein »: true garde le plein cadre V4 ;
  - le carton final : marque.json (nom, produit, logo, adresse) + lignes du film, en typographie cinétique.
Appelé par usine.py ; utilisable seul : python3 monter.py <montage.json> <marque.json> <fmt> <langue> <sortie.mp4> [--version v]
"""
import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parents[2] / "creative/video-v4"))
sys.path.insert(0, str(ICI))
import monter_v4 as M  # noqa: E402
from typo import Typo, ease_io, ease_out  # noqa: E402

VERSION_RENDU = "v5.3"  # changer pour invalider le cache des segments
TY = None
_UI_V4 = M.image_ui


def configurer(marque, produit, textes, cache):
    """Branche la marque, les textes du film et le cache sur le moteur V4 (avant le ProcessPool : fork hérite)."""
    global TY
    langues = {l: {**marque.get("langues", {}).get(l, {}), **t} for l, t in textes.items()}
    M.MARQUE = {**marque, "produit": produit, "langues": langues, "_rendu": VERSION_RENDU}
    M.COUL = {k: tuple(v) for k, v in marque["couleurs"].items()}
    M.POLICES = Path(marque["polices"]["dossier"]).expanduser()
    M.CACHE = Path(cache).expanduser()
    M.poser_textes = poser_textes
    M.image_ui = image_ecran
    M.image_fin = image_fin
    TY = Typo(marque)
    if not getattr(M.mixer, "_v5", False):
        M.mixer = limiter_crete(M.mixer)


def limiter_crete(mixer_v4):
    """Après le mixage V4 (−14 LUFS) : limiteur suréchantillonné ×4, crête vraie ≤ −1,5 dBTP même après l'AAC."""
    def mixer(m, segs, duree, sortie_wav):
        mixer_v4(m, segs, duree, sortie_wav)
        tmp = sortie_wav.with_suffix(".lim.wav")
        M.ff(["-i", str(sortie_wav), "-af", "aresample=192000,alimiter=limit=0.8:level=false:attack=1:release=60,aresample=48000",
              str(tmp)])
        tmp.replace(sortie_wav)
    mixer._v5 = True
    return mixer


def poser_textes(im, textes, t_glob, L, vertical):
    for x in textes:
        u = t_glob - x["t"]
        if 0 <= u < x["d"]:
            im = TY.poser(im, x, L.get(x["cle"], x["cle"]), u)
    return im


# ------------------------------------------------------------------------------------------------------------ écran
CARTE = {"16x9": (0.33, 0.075, 0.962, 0.925), "9x16": (0.06, 0.255, 0.94, 0.875)}


@lru_cache(maxsize=16)
def ombre_carte(W, H, box, rayon):
    x0, y0, x1, y1 = box
    fond = Image.new("RGB", (W, H), M.COUL["encre"])
    o = Image.new("L", (W, H), 0)
    ImageDraw.Draw(o).rounded_rectangle([x0, y0 + rayon * 0.6, x1, y1 + rayon * 0.6], radius=rayon, fill=150)
    o = o.filter(ImageFilter.GaussianBlur(rayon * 1.6))
    fond.paste((0, 0, 0), (0, 0), o)
    return fond


@lru_cache(maxsize=16)
def masque_carte(w, h, rayon):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=rayon, fill=255)
    return m


def fenetre(src_w, src_h, cx, cy, w, W, H):
    """Même calcul que monter_v4.recadrer : renvoie (x0, y0, pw, ph) dans la source."""
    pw = w * src_w
    ph = pw * H / W
    if ph > src_h:
        ph, pw = src_h, src_h * W / H
    x0 = min(max(cx * src_w - pw / 2, 0), src_w - pw)
    y0 = min(max(cy * src_h - ph / 2, 0), src_h - ph)
    return x0, y0, pw, ph


def curseur(d, x, y, s, presse):
    k = s / 1080 * (0.92 if presse else 1.0)
    pts = [(0, 0), (0, 25), (6, 19.5), (10.5, 29), (15, 27), (10.5, 18), (18, 18)]
    poly = [(x + px * k * 1.25, y + py * k * 1.25) for px, py in pts]
    d.polygon(poly, fill=(20, 20, 24), outline=(250, 250, 250), width=max(2, int(2.2 * k)))


def image_ecran(seg, t, W, H, vertical):
    if seg.get("plein"):
        return _UI_V4(seg, t, W, H, vertical)
    imgs = seg["images"]
    f = imgs[0][1]
    for ti, fi in imgs:
        if t >= ti:
            f = fi
    src = M.capture(f)
    fmt = "9x16" if vertical else "16x9"
    bx = seg.get("carte_v" if vertical else "carte") or CARTE[fmt]
    k = ease_out(t / 0.45) if seg.get("entree") else 1.0
    sc = 0.965 + 0.035 * k
    x0, y0, x1, y1 = bx[0] * W, bx[1] * H, bx[2] * W, bx[3] * H
    cxw, cyw = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = int((x1 - x0) * sc), int((y1 - y0) * sc)
    box = (int(cxw - w / 2), int(cyw - h / 2), int(cxw - w / 2) + w, int(cyw - h / 2) + h)
    rayon = int(min(W, H) * 0.018)
    fond = ombre_carte(W, H, box, rayon).copy()
    cadre = seg.get("cadre_v" if vertical else "cadre")
    cx, cy, cw = M.interp(cadre, t)
    fx, fy, pw, ph = fenetre(src.width, src.height, cx, cy, cw, w, h)
    carte = src.transform((w, h), Image.EXTENT, (fx, fy, fx + pw, fy + ph), Image.BICUBIC)
    d = ImageDraw.Draw(carte)
    if seg.get("curseur"):  # [[t, x, y], ...] en fractions de la source (positions réelles des clics de la capture)
        cxs, cys = M.interp(seg["curseur"], t)
        px, py = (cxs * src.width - fx) / pw * w, (cys * src.height - fy) / ph * h
        presse = False
        for tc in seg.get("clics", []):
            if 0 <= t - tc < 0.5:
                r = (t - tc) / 0.5
                rr = (8 + 46 * ease_out(r)) * min(W, H) / 1080
                d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=(*M.COUL["signal"], int(255 * (1 - r))), width=4)
                presse = presse or (t - tc) < 0.12
        curseur(d, px, py, min(W, H), presse)
    if seg.get("clic") is not None and 0 <= t - seg["clic"] < 0.25:
        carte = Image.blend(carte, Image.new("RGB", carte.size, M.COUL["signal"]), 0.10 * (1 - (t - seg["clic"]) / 0.25))
    fond.paste(carte, box[:2], masque_carte(w, h, rayon))
    ImageDraw.Draw(fond).rounded_rectangle(box, radius=rayon, outline=(255, 255, 255, 30), width=1)
    return fond


# ------------------------------------------------------------------------------------------------------------ carton
def image_fin(seg, t, W, H, L):
    """Carton : slogan (titre, mots révélés), nom du produit, sous-titre, mentions ; tout vient de marque.json + du brief."""
    im = Image.new("RGB", (W, H), M.COUL["encre"])
    v = H > W
    im = TY.poser(im, {"style": "titre", "d": seg["d"] + 1, "zone": "centre", "align": "centre", "taille": 0.82 if v else 0.95},
                  L.get("slogan", ""), t)
    a = ease_io((t - seg.get("t_marque", 1.1)) / 0.45)
    if a <= 0:
        return im
    d = ImageDraw.Draw(im)
    s = min(W, H)
    fm = TY.police("titre", s * 0.05, "Bold")
    marque, produit = M.MARQUE["marque"], M.MARQUE["produit"]
    lw = d.textlength(marque + "  " + produit, font=fm)
    y = H * (0.74 if v else 0.75)
    x = (W - lw) / 2
    if M.MARQUE.get("logo"):
        lg = Image.open(Path(M.MARQUE["logo"]).expanduser()).convert("RGBA")
        lg.thumbnail((int(fm.size * 1.3), int(fm.size * 1.3)))
        im.paste(lg, (int(x - lg.width - fm.size * 0.4), int(y)), lg)
    mix = lambda c: tuple(int(M.COUL["encre"][i] + (c[i] - M.COUL["encre"][i]) * a) for i in range(3))  # noqa: E731
    d.text((x, y), marque + "  ", font=fm, fill=mix(M.COUL["os"]))
    d.text((x + d.textlength(marque + "  ", font=fm), y), produit, font=fm, fill=mix(M.COUL["signal"]))
    fs = TY.police("titre", s * 0.024, "Regular")
    sous = L.get("sous_titre", "") + (f"   ·   {M.MARQUE['url']}" if M.MARQUE.get("url") else "")
    d.text(((W - d.textlength(sous, font=fs)) / 2, y + fm.size * 1.55), sous, font=fs, fill=mix(M.COUL["brume"]))
    fp = TY.police("titre", s * 0.015, "Regular")
    men = L.get("mentions", "")
    d.text(((W - d.textlength(men, font=fp)) / 2, H - fp.size * (6 if v else 3)), men, font=fp,
           fill=tuple(int(c * 0.6) for c in mix(M.COUL["brume"])))
    return im


def construire(montage, marque, produit, textes, cache, fmt, langue, sortie, version="long", animatique=False, jobs=10):
    configurer(marque, produit, textes, cache)
    M.construire(montage, fmt, langue, sortie, version, animatique, jobs)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    for x in ("montage", "marque", "fmt", "langue", "sortie"):
        a.add_argument(x)
    a.add_argument("--version", default="long"), a.add_argument("--animatique", action="store_true")
    o = a.parse_args()
    m = json.loads(Path(o.montage).read_text())
    construire(m, json.loads(Path(o.marque).read_text()), m["produit"], m["textes"], m["cache"], o.fmt, o.langue, o.sortie,
               o.version, o.animatique)
