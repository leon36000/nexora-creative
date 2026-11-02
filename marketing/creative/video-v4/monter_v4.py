"""Rendu de la promo V4 « Une phrase. Un film. » à partir de montage-v4.json (écrit par montage_v4.py).

Chaque segment est rendu à part (en parallèle, avec cache), puis concaténé ; le son (musique Music3, sons des plans H3,
bruitages synthétisés de sfx_v3) est mixé en numpy puis normalisé à −14 LUFS. Tous les textes viennent de marque.json.

Usage : python3 monter_v4.py montage-v4.json {16x9|9x16} {fr|en} sortie.mp4 [--version long|30|15] [--animatique]
  --animatique : plans remplacés par leur image clé (pas de vidéo H3 nécessaire), rendu demi-définition rapide.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "video-v3"))
import couches  # noqa: E402  (Pellicule : étalonnage, halo, vignette, grain)
import sfx_v3  # noqa: E402

FFMPEG = couches.FFMPEG
IPS = 24
SR = 48000
CACHE = Path.home() / "nexora-creative-data/promo/v4/rendu"
MARQUE = json.loads((ICI / "marque.json").read_text())
COUL = {k: tuple(v) for k, v in MARQUE["couleurs"].items()}
POLICES = Path(MARQUE["polices"]["dossier"]).expanduser()


def ff(args, **kw):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *args], capture_output=True, **kw)
    if r.returncode:
        raise SystemExit(f"ffmpeg : {r.stderr[-1500:]}")
    return r


def chemin(p):
    return Path(p).expanduser()


@lru_cache(maxsize=64)
def police(nom, taille, graisse="Regular"):
    f = ImageFont.truetype(str(POLICES / MARQUE["polices"][nom]), int(taille))
    try:
        f.set_variation_by_name(graisse)
    except Exception:
        pass
    return f


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def interp(cles, t):
    """cles : [[t, a, b, c...], ...] interpolées avec lissage ; renvoie les valeurs à t."""
    if t <= cles[0][0]:
        return cles[0][1:]
    for k0, k1 in zip(cles, cles[1:]):
        if t <= k1[0]:
            u = ease((t - k0[0]) / max(1e-6, k1[0] - k0[0]))
            return [a + (b - a) * u for a, b in zip(k0[1:], k1[1:])]
    return cles[-1][1:]


def recadrer(im: Image.Image, cx, cy, w, W, H):
    """Fenêtre de largeur w (fraction de la source), centrée en (cx, cy), au rapport W/H, gardée dans l'image."""
    sw, sh = im.size
    pw = w * sw
    ph = pw * H / W
    if ph > sh:
        ph, pw = sh, sh * W / H
    x0 = min(max(cx * sw - pw / 2, 0), sw - pw)
    y0 = min(max(cy * sh - ph / 2, 0), sh - ph)
    return im.transform((W, H), Image.EXTENT, (x0, y0, x0 + pw, y0 + ph), Image.BICUBIC)


# ------------------------------------------------------------------------------------------------------------- sources
@lru_cache(maxsize=8)
def plaque(fichier):
    f = chemin(fichier)
    if f.suffix.lower() in (".png", ".jpg"):
        return [np.asarray(Image.open(f).convert("RGB"))]
    w, h, _ = couches.sonder(str(f))
    brut = ff(["-i", str(f), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]).stdout
    return list(np.frombuffer(brut, np.uint8).reshape(-1, h, w, 3))


@lru_cache(maxsize=256)
def capture(fichier):
    return Image.open(chemin(fichier)).convert("RGB")


def temps_source(seg, t):
    """Instant source (s) d'un plan : début + intégrale de la vitesse (constante ou rampe [[t, v], ...])."""
    v = seg.get("vitesse", 1.0)
    if isinstance(v, (int, float)):
        return seg.get("debut", 0.0) + t * v
    pas = 1 / IPS / 4
    s, x = seg.get("debut", 0.0), 0.0
    while x < t:
        s += interp(v, x)[0] * pas
        x += pas
    return s


def image_plan(seg, t, W, H, vertical, animatique):
    if vertical and seg.get("plaque_v") and chemin(seg["plaque_v"]).exists() and not animatique:
        seg = dict(seg, plaque=seg["plaque_v"], cadre_v=seg.get("cadre_vv"))  # plaque tournée nativement en 9:16
    if animatique and seg.get("cle"):
        frames = plaque(seg["cle"])
    else:
        frames = plaque(seg["plaque"])
    i = min(len(frames) - 1, max(0, int(round(temps_source(seg, t) * IPS))))
    im = Image.fromarray(frames[i])
    cadre = seg.get("cadre_v" if vertical else "cadre") or [[0, seg.get("cx_v", 0.5) if vertical else 0.5, 0.5, 1.0]]
    cx, cy, w = interp(cadre, t)
    if animatique and seg.get("cle"):  # mouvement simulé sur l'image fixe
        w *= 1 - 0.06 * t / max(seg["d"], 1)
    return recadrer(im, cx, cy, w, W, H)


def image_ui(seg, t, W, H, vertical):
    imgs = seg["images"]  # [[t, fichier], ...]
    f = imgs[0][1]
    for ti, fi in imgs:
        if t >= ti:
            f = fi
    cadre = seg.get("cadre_v" if vertical else "cadre")
    cx, cy, w = interp(cadre, t)
    im = recadrer(capture(f), cx, cy, w, W, H)
    if seg.get("clic") is not None and 0 <= t - seg["clic"] < 0.25:  # pression du bouton : léger flash orange
        a = 1 - (t - seg["clic"]) / 0.25
        im = Image.blend(im, Image.new("RGB", im.size, COUL["signal"]), 0.12 * a)
    return im


def image_ab(seg, t, W, H, vertical, animatique, L):
    """Deux prises côte à côte (ou l'une sur l'autre en vertical) ; au choix, la gardée s'agrandit en plein cadre."""
    fond = Image.new("RGB", (W, H), COUL["encre"])
    u = ease((t - seg["t_choix"]) / 0.7) if t > seg["t_choix"] else 0.0
    marge = int(0.035 * min(W, H))
    if vertical:
        cw, ch = W - 2 * marge, int((W - 2 * marge) * 9 / 16)
        pos = [(marge, H // 2 - ch - marge // 2), (marge, H // 2 + marge // 2)]
    else:
        cw = (W - 3 * marge) // 2
        ch = int(cw * 9 / 16)
        pos = [(marge, (H - ch) // 2), (2 * marge + cw, (H - ch) // 2)]
    d = ImageDraw.Draw(fond)
    garde = 1 if seg["garde"] == "b" else 0
    for k, cle in enumerate(("a", "b")):
        sous = dict(seg, plaque=seg[cle], cle=seg.get("cle_" + cle), cadre=None, cadre_v=None)
        im = image_plan(sous, t, cw, ch, False, animatique)
        x, y = pos[k]
        if k == garde:
            x, y = int(x + (0 - x) * u), int(y + ((H - H) // 2 - y) * u)
            ww, hh = int(cw + (W - cw) * u), int(ch + (H - ch) * u)
            if u > 0:
                sous["cadre"] = None
                im = image_plan(sous, t, ww, hh, vertical, animatique) if vertical else im.resize((ww, hh), Image.BICUBIC)
        else:
            im = Image.blend(Image.new("RGB", im.size, COUL["encre"]), im, 1 - u)
            ww, hh = cw, ch
        fond.paste(im, (x, y))
        if u < 0.5:
            f = police("mono", 0.022 * max(W, H) * (0.8 if vertical else 1), "Medium")
            lab = L["prise_a" if k == 0 else "prise_b"]
            choisi = k == garde and t > seg["t_choix"] - 0.6
            d.text((pos[k][0] + 14, pos[k][1] - f.size - 12), lab + (f"  ·  {L['gardee']}" if choisi else ""), font=f,
                   fill=COUL["signal"] if choisi else COUL["brume"])
            if choisi:
                d.rectangle([pos[k][0] - 3, pos[k][1] - 3, pos[k][0] + cw + 2, pos[k][1] + ch + 2], outline=COUL["signal"], width=4)
    return fond


def image_chrono(seg, t, W, H, vertical, animatique, onde):
    """Le montage s'assemble : les plans tombent sur une piste au rythme de la musique, tête de lecture, forme d'onde."""
    fond = Image.new("RGB", (W, H), COUL["encre"])
    d = ImageDraw.Draw(fond)
    n = len(seg["plans"])
    marge = int(0.06 * W)
    piste_w = W - 2 * marge
    pw = piste_w // n
    ph = int(pw * 9 / 16)
    y = int(H * (0.42 if not vertical else 0.45))
    # forme d'onde de la musique sous la piste
    if onde is not None:
        oy = y + ph + int(0.05 * H)
        for k in range(0, piste_w, 4):
            a = onde[int(k / piste_w * (len(onde) - 1))]
            hh = max(2, int(a * 0.07 * H))
            d.rectangle([marge + k, oy - hh, marge + k + 2, oy + hh], fill=(70, 70, 80))
    for k, p in enumerate(seg["plans"]):
        tk = seg["temps"][k]
        if t < tk:
            d.rectangle([marge + k * pw + 3, y, marge + (k + 1) * pw - 3, y + ph], outline=(50, 50, 58), width=2)
            continue
        u = ease((t - tk) / 0.18)
        sous = {"plaque": p["plaque"], "cle": p.get("cle"), "debut": p.get("debut", 1.0), "d": seg["d"]}
        im = image_plan(sous, 0.0, pw - 6, ph, False, animatique)
        yy = int(y - (1 - u) * 0.25 * H)
        fond.paste(im, (marge + k * pw + 3, yy))
    x = marge + int(piste_w * min(1, t / seg["d"]))
    d.rectangle([x - 1, y - int(0.04 * H), x + 1, y + ph + int(0.12 * H)], fill=COUL["signal"])
    return fond


def image_fin(seg, t, W, H, L):
    fond = Image.new("RGB", (W, H), COUL["encre"])
    d = ImageDraw.Draw(fond)
    v = H > W
    s = min(W, H)
    f1 = police("titre", s * (0.12 if v else 0.11), "SemiBold")
    l1, l2 = L["slogan_1"], L["slogan_2"]
    a1 = ease(t / 0.35)
    a2 = ease((t - 0.55) / 0.35)
    cy = H * (0.40 if v else 0.42)
    if v:
        for k, (txt, a, col) in enumerate(((l1, a1, COUL["os"]), (l2, a2, COUL["signal"]))):
            bw = d.textlength(txt, font=f1)
            d.text(((W - bw) / 2, cy - f1.size * 1.1 + k * f1.size * 1.25), txt, font=f1,
                   fill=tuple(int(c * a) for c in col))
    else:
        w1 = d.textlength(l1 + " ", font=f1)
        w2 = d.textlength(l2, font=f1)
        x = (W - w1 - w2) / 2
        d.text((x, cy - f1.size / 2), l1, font=f1, fill=tuple(int(c * a1) for c in COUL["os"]))
        d.text((x + w1, cy - f1.size / 2), l2, font=f1, fill=tuple(int(c * a2) for c in COUL["signal"]))
    a3 = ease((t - 1.5) / 0.5)
    if a3 > 0:
        fm = police("titre", s * 0.062, "Bold")
        nom = MARQUE["marque"] + "  " + MARQUE["produit"]
        y = H * (0.70 if v else 0.68)
        x = (W - d.textlength(nom, font=fm)) / 2
        if MARQUE.get("logo"):
            lg = Image.open(chemin(MARQUE["logo"])).convert("RGBA")
            lg.thumbnail((int(fm.size * 1.3), int(fm.size * 1.3)))
            fond.paste(lg, (int(x - lg.width - fm.size * 0.4), int(y)), lg)
        d.text((x, y), MARQUE["marque"] + "  ", font=fm, fill=tuple(int(c * a3) for c in COUL["os"]))
        d.text((x + d.textlength(MARQUE["marque"] + "  ", font=fm), y), MARQUE["produit"], font=fm,
               fill=tuple(int(c * a3) for c in COUL["signal"]))
        fs = police("titre", s * 0.026, "Regular")
        sous = L["sous_titre"] + (f"   ·   {MARQUE['url']}" if MARQUE.get("url") else "")
        d.text(((W - d.textlength(sous, font=fs)) / 2, y + fm.size * 1.6), sous, font=fs, fill=tuple(int(c * a3) for c in COUL["brume"]))
        fp = police("titre", s * 0.016, "Regular")
        d.text(((W - d.textlength(L["mentions"], font=fp)) / 2, H - fp.size * 3), L["mentions"], font=fp,
               fill=tuple(int(c * a3 * 0.6) for c in COUL["brume"]))
    return fond


# --------------------------------------------------------------------------------------------------------- textes posés
def poser_textes(im: Image.Image, textes, t_glob, L, vertical):
    W, H = im.size
    s = min(W, H)
    for x in textes:
        u = t_glob - x["t"]
        if not (0 <= u < x["d"]):
            continue
        a = min(1.0, u / 0.18, (x["d"] - u) / 0.22)
        txt = L.get(x["cle"], x["cle"])
        style = x.get("style", "legende")
        calque = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(calque)
        if style == "grand":
            f = police("titre", s * (0.085 if vertical else 0.075), "SemiBold")
            lignes = couper(d, txt, f, W * 0.86)
            y0 = H / 2 - len(lignes) * f.size * 0.62
            ombre = Image.new("RGBA", im.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ombre)
            for k, l in enumerate(lignes):  # ombre portée large : lisible sur une image claire
                od.text(((W - d.textlength(l, font=f)) / 2, y0 + k * f.size * 1.2), l, font=f, fill=(0, 0, 0, int(235 * a)),
                        stroke_width=int(f.size * 0.12), stroke_fill=(0, 0, 0, int(235 * a)))
            calque = Image.alpha_composite(calque, ombre.filter(ImageFilter.GaussianBlur(f.size * 0.35)))
            d = ImageDraw.Draw(calque)
            for k, l in enumerate(lignes):
                d.text(((W - d.textlength(l, font=f)) / 2, y0 + k * f.size * 1.2), l, font=f, fill=(*COUL["os"], int(255 * a)))
        elif style == "phrase":  # la phrase tapée, en mono, lettre à lettre
            f = police("mono", s * (0.042 if vertical else 0.036), "Medium")
            n = int(len(txt) * min(1.0, u / x.get("frappe", 0.6)))
            lignes = couper(d, "› " + txt[:n], f, W * 0.8)
            hh = len(lignes) * f.size * 1.35
            y0 = H * x["pos_v"] if vertical and x.get("pos_v") else H * (0.80 if vertical else 0.82) - hh
            x0 = W * 0.06
            ww = max(d.textlength(l, font=f) for l in lignes)
            d.rounded_rectangle([x0 - f.size * 0.6, y0 - f.size * 0.5, x0 + ww + f.size * 0.6, y0 + hh + f.size * 0.2],
                                radius=f.size * 0.4, fill=(0, 0, 0, int(150 * a)))
            for k, l in enumerate(lignes):
                d.text((x0, y0 + k * f.size * 1.35), l, font=f, fill=(*COUL["os"], int(255 * a)))
        else:  # légende : barre orange + texte, en bas à gauche (en haut pour « haut »)
            f = police("titre", s * (0.05 if vertical else 0.044), "Medium")
            lignes = couper(d, txt, f, W * 0.8)
            hh = len(lignes) * f.size * 1.2
            y0 = (H * 0.09) if x.get("pos") == "haut" else H * (0.86 if vertical else 0.88) - hh
            x0 = W * 0.06 + f.size * 0.5
            dy = (1 - a) * f.size * 0.4
            # pastille sombre : la légende reste lisible sur l'interface comme sur une image claire
            ww = max(d.textlength(l, font=f) for l in lignes)
            d.rounded_rectangle([W * 0.06 - f.size * 0.55, y0 + dy - f.size * 0.35, x0 + ww + f.size * 0.6, y0 + dy + hh + f.size * 0.3],
                                radius=f.size * 0.35, fill=(6, 6, 8, int(228 * a)))
            ombre = Image.new("RGBA", im.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ombre)
            for k, l in enumerate(lignes):
                od.text((x0, y0 + dy + k * f.size * 1.2), l, font=f, fill=(0, 0, 0, int(200 * a)))
            calque = Image.alpha_composite(calque, ombre.filter(ImageFilter.GaussianBlur(f.size * 0.25)))
            d = ImageDraw.Draw(calque)
            d.rectangle([W * 0.06, y0 + dy + f.size * 0.12, W * 0.06 + f.size * 0.14, y0 + dy + hh - f.size * 0.1],
                        fill=(*COUL["signal"], int(255 * a)))
            for k, l in enumerate(lignes):
                d.text((x0, y0 + dy + k * f.size * 1.2), l, font=f, fill=(*COUL["os"], int(255 * a)))
        im = Image.alpha_composite(im.convert("RGBA"), calque).convert("RGB")
    return im


def couper(d, txt, f, largeur):
    mots, lignes, cur = txt.split(" "), [], ""
    for m in mots:
        essai = (cur + " " + m).strip()
        if d.textlength(essai, font=f) > largeur and cur:
            lignes.append(cur)
            cur = m
        else:
            cur = essai
    return lignes + [cur]


# ----------------------------------------------------------------------------------------------------------- un segment
REGLAGES_PLAN = {"exposition": 1.0, "teinte_ombres": [-0.006, 0.0, 0.012], "teinte_hautes": [0.025, 0.008, -0.02], "saturation": 1.0,
                 "contraste": 1.06, "noir": 0.008, "seuil_halo": 0.86, "halo": 0.22, "seuil_reflet": 0.985, "reflet": 0.25,
                 "vignette": 0.25, "grain": 0.03}
REGLAGES_UI = {"vignette": 0.18, "grain": 0.014}


def rendre_segment(args):
    seg, fmt, langue, t0, textes, animatique, onde, sortie = args
    W, H = (1920, 1080) if fmt == "16x9" else (1080, 1920)
    if animatique:
        W, H = W // 2, H // 2
    vertical = fmt == "9x16"
    L = MARQUE["langues"][langue]
    n = max(1, int(round(seg["d"] * IPS)))
    typ = seg["type"]
    pel = couches.Pellicule(W, H, seg.get("nom", typ), {**REGLAGES_PLAN, **seg.get("etalonnage", {})} if typ in ("plan", "ab")
                            else REGLAGES_UI)
    enc = subprocess.Popen([FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(IPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "fast" if animatique else "medium", "-crf", "12",
                            "-pix_fmt", "yuv420p", str(sortie)], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / IPS
        if typ == "noir":
            im = Image.new("RGB", (W, H), (0, 0, 0))
        elif typ == "ui":
            im = image_ui(seg, t, W, H, vertical)
        elif typ == "plan":
            im = image_plan(seg, t, W, H, vertical, animatique)
        elif typ == "ab":
            im = image_ab(seg, t, W, H, vertical, animatique, L)
        elif typ == "chrono":
            im = image_chrono(seg, t, W, H, vertical, animatique, onde)
        elif typ == "fin":
            im = image_fin(seg, t, W, H, L)
        else:
            raise SystemExit(f"segment inconnu {typ}")
        if seg.get("fondu_entree") and t < seg["fondu_entree"]:
            im = Image.blend(Image.new("RGB", im.size, (0, 0, 0)), im, ease(t / seg["fondu_entree"]))
        if seg.get("flash") is not None and 0 <= t - seg["flash"] < 0.12:
            im = Image.blend(im, Image.new("RGB", im.size, (255, 246, 230)), 0.55 * (1 - (t - seg["flash"]) / 0.12))
        x = np.asarray(im, np.float32) / 255
        if typ in ("plan", "ab"):
            x = pel.finir(pel.etalonner(x), i, False)
        elif typ != "fin" and typ != "noir":
            x = np.clip(x * pel.vignette + pel.grains[i % 6][..., None] * pel.r["grain"], 0, 1)
        im = Image.fromarray((x * 255 + 0.5).astype(np.uint8))
        im = poser_textes(im, textes, t0 + t, L, vertical)
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    if enc.wait():
        raise SystemExit("encodage du segment échoué")
    return str(sortie)


# ------------------------------------------------------------------------------------------------------------------ son
def lire_audio(f, debut=0.0, duree=None):
    a = ["-ss", str(max(0.0, debut)), "-i", str(chemin(f))] + (["-t", str(duree)] if duree else [])
    brut = ff(a + ["-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]).stdout
    return np.frombuffer(brut, np.float32).reshape(-1, 2).copy()


def poser(piste, son, t, db=0.0, fin=0.0):
    i = int(t * SR)
    if i >= len(piste) or len(son) == 0:
        return
    s = son[: len(piste) - i] * (10 ** (db / 20))
    if fin:
        k = min(len(s), int(fin * SR))
        s[-k:] *= np.linspace(1, 0, k)[:, None]
    piste[i: i + len(s)] += s


def mixer(m, segs, duree, sortie_wav):
    piste = np.zeros((int(duree * SR) + SR, 2), np.float32)
    for mu in m["musique"]:  # morceaux de la bande originale (montage de la musique : intro, drop, fin)
        son = lire_audio(mu["fichier"], mu.get("source", 0.0), mu.get("d", duree - mu.get("pose", 0.0)))
        k = min(len(son), int(mu.get("fondu_entree", 0.0) * SR))
        if k:
            son[:k] *= np.linspace(0, 1, k)[:, None]
        poser(piste, son, mu.get("pose", 0.0), mu.get("db", 0.0), mu.get("fondu_fin", 0.05))
    for s in segs:  # sons natifs des plans H3 (vitesse 1 seulement)
        if s["type"] == "plan" and s.get("son_h3") is not None and not isinstance(s.get("vitesse", 1.0), list) and s.get("vitesse", 1.0) == 1.0 \
                and chemin(s["plaque"]).exists():
            a = lire_audio(s["plaque"], s.get("debut", 0.0), s["d"])
            k = min(len(a), int(0.04 * SR))
            a[:k] *= np.linspace(0, 1, k)[:, None]
            poser(piste, a, s["t"], s["son_h3"], 0.08)
    rng = np.random.default_rng(4)
    for x in m.get("sfx", []):
        poser(piste, sfx_v3.generer(x["type"], x.get("duree", 1.0), rng), x["t"], x.get("db", 0.0))
    if m.get("silence"):
        a, b = m["silence"]
        piste[int(a * SR): int(b * SR)] *= 0.0
    piste = piste[: int(duree * SR)]
    brut = sortie_wav.with_suffix(".brut.wav")
    piste /= max(1.0, float(np.abs(piste).max()) / 0.98)  # pas d'écrêtage avant la normalisation
    sfx_v3.ecrire(piste, str(brut))
    # deux passes loudnorm : −14 LUFS intégrés, crête vraie −1,5 dBTP
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(brut), "-af", "loudnorm=I=-13.4:TP=-2:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True)
    e = r.stderr.decode()
    j = json.loads(e[e.rfind("{"): e.rfind("}") + 1])
    ff(["-i", str(brut), "-af", f"loudnorm=I=-13.4:TP=-2:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
        f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,alimiter=limit=0.75:level=false",
        "-ar", str(SR), str(sortie_wav)])
    brut.unlink()


def onde_musique(m, duree):
    try:
        a = np.zeros((int(duree * SR), 2), np.float32)
        for mu in m["musique"]:
            poser(a, lire_audio(mu["fichier"], mu.get("source", 0.0), mu.get("d", duree)), mu.get("pose", 0.0))
        e = np.abs(a).mean(1)
        n = 400
        e = np.array([c.mean() for c in np.array_split(e, n)])
        return (e / (e.max() + 1e-6)).tolist()
    except Exception:
        return None


# ---------------------------------------------------------------------------------------------------------------- tout
def construire(m, fmt, langue, sortie, version="long", animatique=False, jobs=12):
    v = m["versions"][version]
    segs, t = [], 0.0
    for s in v["segments"]:
        segs.append({**s, "t": t})
        t += s["d"]
    duree = t
    textes = v.get("textes", [])
    onde = onde_musique(v, duree)
    CACHE.mkdir(parents=True, exist_ok=True)
    taches = []
    for s in segs:
        tx = [x for x in textes if x["t"] < s["t"] + s["d"] and x["t"] + x["d"] > s["t"] and langue in x.get("langues", [langue])]
        cle = hashlib.sha1(json.dumps([s, tx, fmt, langue, animatique, MARQUE, 3], sort_keys=True).encode()).hexdigest()[:16]
        f = CACHE / f"{'a' if animatique else 's'}-{cle}.mp4"
        taches.append((s, fmt, langue, s["t"], tx, animatique, onde if s["type"] == "chrono" else None, f))
    a_faire = [x for x in taches if not x[-1].exists()]
    with ProcessPoolExecutor(jobs) as ex:
        list(ex.map(rendre_segment, a_faire))
    liste = CACHE / f"liste-{fmt}-{langue}-{version}.txt"
    liste.write_text("".join(f"file '{x[-1]}'\n" for x in taches))
    wav = Path(sortie).with_suffix(".wav")
    mixer(v, segs, duree, wav)
    ff(["-f", "concat", "-safe", "0", "-i", str(liste), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
        "-preset", "slow", "-crf", "15" if not animatique else "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k",
        "-movflags", "+faststart", "-shortest", str(sortie)])
    wav.unlink()
    print(json.dumps({"film": str(sortie), "duree": round(duree, 2), "segments": len(segs), "rendus": len(a_faire)}))


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("montage"), a.add_argument("fmt"), a.add_argument("langue"), a.add_argument("sortie")
    a.add_argument("--version", default="long"), a.add_argument("--animatique", action="store_true")
    o = a.parse_args()
    construire(json.loads(Path(o.montage).read_text()), o.fmt, o.langue, o.sortie, o.version, o.animatique)
