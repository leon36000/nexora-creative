"""Vidéo vitrine de l'accueil (héros), v3 : montage de plaques photographiques H3 déjà tournées (surveillance,
réception, centre de données), étalonnées ensemble, liées par fouets, éclairs et fondus, avec couches « IA » posées
en code (crochets de détection suivis, transcription, cartes de notification). Muette, en boucle sans couture.

  python3 boucle_v3.py 16x9|9x16 [--apercu]      → ~/nexora-creative-data/site-medias/hero-v3/maitre-<fmt>.mp4
                                                    + planche-<fmt>.jpg + mesures de luminance

Rythme (30 i/s, ~18 s) : VOIT (entrepôt, stationnement) → ÉCOUTE (accueil de nuit, onde + transcription)
→ AGIT (alerte, carte et envois) → infrastructure (allée de serveurs) → retour à l'entrepôt.
Plaques : site-medias-travail/plans/ (voir plaques.txt). Aucun texte n'est généré par le modèle vidéo."""
import sys, json, math, subprocess
from pathlib import Path
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "outils"))
import hud  # suivi par gabarit et images clés du film Surveillance

FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
PL = Path.home() / "nexora-creative-data/site-medias-travail/plans"
SORTIE = Path.home() / "nexora-creative-data/site-medias/hero-v3"
POL = Path.home() / "Desktop/NexoraSite/web/src/fonts"
IPS, SW, SH = 30, 1344, 768
hx = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
ABYSSE, ION, FLARE, TEXTE, TEXTE2, SURF = hx("#05070B"), hx("#3EC8FF"), hx("#FF6A2B"), hx("#EEF3FA"), hx("#8C97AA"), hx("#0B0F16")
c8 = lambda c, a=255: tuple(int(v * 255) for v in c) + (a,)

_pol = {}
def police(nom, t, g):
    k = (nom, t, g)
    if k not in _pol:
        f = ImageFont.truetype(str(POL / f"{nom}-latin-wght-normal.woff2"), t)
        f.set_variation_by_name(g)
        _pol[k] = f
    return _pol[k]
MONO = lambda t, g=b"Medium": police("jetbrains-mono", t, g)
GEIST = lambda t, g=b"SemiBold": police("geist", t, g)
INTER = lambda t, g=b"Regular": police("inter", t, g)

ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else u * u * (3 - 2 * u)
sortie_douce = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else 1 - (1 - u) ** 3

# ------------------------------------------------------------------------------------------------ plaques et plans
# cam : zoom (début, fin) relatif au cadrage plein, point source (début, fin) placé à l'ancre (ax, ay) de la sortie.
BEATS = [
  dict(nom="entrepot", f="surv/entrepot-16x9-v1.mp4", d=3.8, src=0.55, v=(1.0, 0.8), gain=0.8, gamma=1.18, sat=0.5,
       teinte=(0.84, 0.97, 1.14), calme=0.3,
       cam={"16x9": dict(z=(1.18, 1.36), p=((700, 560), (680, 610)), a=(0.62, 0.66)),
            "9x16": dict(z=(1.05, 1.18), p=((660, 560), (650, 600)), a=(0.52, 0.66))}),
  dict(nom="stationnement", f="surv/stationnement-16x9-v1.mp4", d=3.6, src=0.9, v=(1.0, 0.75), gain=1.0, gamma=0.88, sat=0.6,
       teinte=(0.9, 1.0, 1.1),
       cam={"16x9": dict(z=(1.22, 1.42), p=((880, 360), (880, 380)), a=(0.62, 0.56)),
            "9x16": dict(z=(1.0, 1.12), p=((860, 360), (850, 380)), a=(0.5, 0.52))}),
  dict(nom="accueil", f="recep/telephone-16x9-v1.mp4", d=2.1, src=1.2, v=(1.1, 1.0), gain=1.55, gamma=0.78, sat=0.9,
       teinte=(0.92, 1.0, 1.08),
       cam={"16x9": dict(z=(1.12, 1.3), p=((820, 420), (760, 440)), a=(0.6, 0.6)),
            "9x16": dict(z=(1.0, 1.1), p=((760, 420), (730, 440)), a=(0.5, 0.6))}),
  dict(nom="onde", f="recep/onde-16x9-v1.mp4", d=3.6, src=0.6, v=(1.2, 0.9), gain=1.35, gamma=0.85, sat=1.0,
       teinte=(0.95, 1.0, 1.02), calme=0.55,
       cam={"16x9": dict(z=(1.05, 1.16), p=((700, 384), (660, 384)), a=(0.52, 0.42)),
            "9x16": dict(z=(1.0, 1.08), p=((700, 384), (650, 384)), a=(0.5, 0.42))}),
  dict(nom="alerte", f="surv/alerte-16x9-v3.mp4", d=3.8, src=0.8, v=(1.0, 0.85), gain=1.7, gamma=0.75, sat=0.85,
       teinte=(0.95, 1.0, 1.05), orange=True,
       cam={"16x9": dict(z=(1.12, 1.3), p=((650, 560), (660, 580)), a=(0.48, 0.7)),
            "9x16": dict(z=(1.0, 1.1), p=((640, 590), (660, 600)), a=(0.5, 0.75))}),
  dict(nom="allee", f="hero/allee-16x9-v1.mp4", d=3.0, src=2.2, v=(1.0, 1.1), gain=1.5, gamma=0.78, sat=1.0,
       teinte=(0.95, 1.0, 1.02),
       cam={"16x9": dict(z=(1.04, 1.2), p=((672, 330), (672, 330)), a=(0.5, 0.45)),
            "9x16": dict(z=(1.0, 1.1), p=((672, 330), (672, 330)), a=(0.5, 0.45))}),
]
# transition après chaque plan (la dernière ramène au premier) : (type, images)
TRANS = [("fouet", 8), ("eclair", 8), ("fondu", 10), ("fouet", 8), ("eclair", 8), ("eclair", 10)]

PLAQUES, SUIVI_ENTREPOT, CLES_STAT = {}, None, None
VOITURES = [(697, 303, 812, 436), (950, 315, 1108, 446), (436, 155, 500, 200), (502, 151, 562, 198), (0, 312, 148, 418)]


def charger():
    global SUIVI_ENTREPOT, CLES_STAT
    for b in BEATS:
        PLAQUES[b["nom"]] = hud.lire(PL / b["f"])[0]
    SUIVI_ENTREPOT = hud.suivre(PLAQUES["entrepot"], [550, 632, 608, 748])
    cles = "0:793,262,838,362;1.5:803,282,842,382;2.6:809,300,860,407;3.8:800,300,854,407;5.2:806,300,860,407"
    cles = [tuple([float(a.split(":")[0])] + [float(v) for v in a.split(":")[1].split(",")]) for a in cles.split(";")]
    CLES_STAT = hud.interpoler(cles, len(PLAQUES["stationnement"]))


def calendrier():
    n = [round(b["d"] * IPS) for b in BEATS]
    s = [0]
    for k in range(len(BEATS) - 1):
        s.append(s[-1] + n[k] - TRANS[k][1])
    N = s[-1] + n[-1] - TRANS[-1][1]
    return n, s, N


# ------------------------------------------------------------------------------------------------ caméra et image
def camera(b, fmt, tau, W, H):
    c = b["cam"][fmt]
    u = sortie_douce(max(0.0, min(1.0, (tau + 0.35) / (b["d"] + 0.35))))
    z = c["z"][0] + (c["z"][1] - c["z"][0]) * u
    px = c["p"][0][0] + (c["p"][1][0] - c["p"][0][0]) * u
    py = c["p"][0][1] + (c["p"][1][1] - c["p"][0][1]) * u
    s = max(W / SW, H / SH) * z
    x0 = min(max(px - c["a"][0] * W / s, 0), SW - W / s)
    y0 = min(max(py - c["a"][1] * H / s, 0), SH - H / s)
    return s, x0, y0


def temps_source(b, tau):
    """Rampe de vitesse : v passe de v0 à v1 (ralenti au verrouillage)."""
    v0, v1 = b["v"]
    d = b["d"]
    u = max(-0.5, min(tau, d))
    return b["src"] + v0 * u + (v1 - v0) * (u * u) / (2 * d) if u > 0 else b["src"] + v0 * u


def etalonner(b, x):
    x = np.clip(x * b["gain"], 0, None) ** b["gamma"]
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * b["sat"]
    x = x * np.array(b["teinte"], np.float32)
    x = np.clip(x, 0, 1)
    x = x * 0.65 + (x * x * (3 - 2 * x)) * 0.35  # S doux
    return ABYSSE + x * (1 - ABYSSE)


def image_plaque(b, tau, fmt, W, H):
    fr = PLAQUES[b["nom"]]
    t = temps_source(b, tau) * 24
    i0 = int(np.clip(math.floor(t), 0, len(fr) - 1)); i1 = min(i0 + 1, len(fr) - 1); a = float(np.clip(t - i0, 0, 1))
    src = fr[i0] if a < 0.02 else (fr[i0] * (1 - a) + fr[i1] * a).astype(np.uint8)
    s, x0, y0 = camera(b, fmt, tau, W, H)
    im = Image.fromarray(src).transform((W, H), Image.AFFINE, (1 / s, 0, x0, 0, 1 / s, y0), Image.BICUBIC)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    x = np.asarray(im, np.float32) / 255
    if b.get("orange"):  # la lueur rouge du téléphone devient le point chaud de la marque
        r, g, bl = x[..., 0], x[..., 1], x[..., 2]
        m = np.clip((r - np.maximum(g, bl) - 0.08) * 4, 0, 1)[..., None]
        chaud = r[..., None] * np.array([1.0, 0.45, 0.18], np.float32) * 1.15
        x = x * (1 - m) + chaud * m
    return etalonner(b, x), (s, x0, y0, t / 24)


# ------------------------------------------------------------------------------------------------ couches IA
def crochets(d, box, col, a, ep=3, coin=None):
    x0, y0, x1, y1 = box
    L = coin or max(10, min(x1 - x0, y1 - y0) * 0.28)
    c = c8(col, int(255 * a))
    for (px, py, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(px, py + sy * L), (px, py), (px + sx * L, py)], fill=c, width=ep, joint="curve")
    d.rectangle(box, fill=c8(col, int(18 * a)))


def etiquette(d, x, y, txt, col, a, taille=21, fond_sombre=False):
    f = MONO(taille, b"Bold")
    w = d.textlength(txt, font=f)
    h = taille + 12
    if fond_sombre:
        d.rectangle([x, y - h, x + w + 18, y], fill=c8(SURF, int(215 * a)))
        d.rectangle([x, y - h, x + 3, y], fill=c8(col, int(255 * a)))
        d.text((x + 11, y - h + 5), txt, font=f, fill=c8(TEXTE, int(255 * a)))
    else:
        d.rectangle([x, y - h, x + w + 16, y], fill=c8(col, int(235 * a)))
        d.text((x + 8, y - h + 5), txt, font=f, fill=c8(ABYSSE, int(255 * a)))
    return w + 16


def verrou(d, box, tau, t0, col, txt, conf=None):
    """Crochets qui se referment sur la cible (verrouillage), puis étiquette tapée."""
    if tau < t0:
        return
    u = sortie_douce((tau - t0) / 0.35)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    k = 1 + 0.9 * (1 - u)
    w, h = (box[2] - box[0]) / 2 * k, (box[3] - box[1]) / 2 * k
    crochets(d, (cx - w, cy - h, cx + w, cy + h), col, min(1, u * 1.6))
    if tau > t0 + 0.2:
        n = int((tau - t0 - 0.2) * 40)
        if conf is not None:
            c = conf - 0.25 * max(0, 1 - (tau - t0 - 0.2) / 0.6)
            txt = f"{txt} · {c:.2f}".replace(".", ",")
        etiquette(d, box[0], box[1] - 8, txt[:n], col, 1)


def vers_sortie(box, cam):
    s, x0, y0, _ = cam
    return tuple(((box[i] - (x0 if i % 2 == 0 else y0)) * s) for i in range(4))


def hud_coin(d, W, tau, cam_nom):
    f = MONO(22, b"Bold")
    txt = f"{cam_nom} · EN DIRECT"
    w = d.textlength(txt, font=f)
    x, y = W - w - 64, 52
    if (tau * 2) % 1 < 0.6:
        d.ellipse([x - 26, y + 6, x - 12, y + 20], fill=c8(ION))
    d.text((x, y), txt, font=f, fill=c8(TEXTE, 235))
    d.text((x, y + 32), "ANALYSE IA · LOCALE", font=MONO(20), fill=c8(ION, 230))


def balayage(d, W, H, tau, t0, x_min):
    u = (tau - t0) / 0.7
    if 0 <= u <= 1:
        y = H * (0.08 + 0.84 * sortie_douce(u))
        d.line([(x_min, y), (W, y)], fill=c8(ION, int(200 * (1 - u))), width=2)
        d.rectangle([x_min, y - 40, W, y], fill=c8(ION, int(22 * (1 - u))))


def couches(b, tau, cam, W, H, fmt):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    nom, ts = b["nom"], cam[3]
    vert = fmt == "9x16"
    if nom == "entrepot":
        k = float(np.clip(ts * 24, 0, len(SUIVI_ENTREPOT) - 1))
        k0 = int(k); k1 = min(k0 + 1, len(SUIVI_ENTREPOT) - 1)
        bx = SUIVI_ENTREPOT[k0] * (1 - (k - k0)) + SUIVI_ENTREPOT[k1] * (k - k0)
        bx = bx + np.array([-10, -12, 10, 6])
        # traînée de la trajectoire
        for j in range(1, 22, 3):
            kj = max(0, k0 - j * 2)
            p = vers_sortie(SUIVI_ENTREPOT[kj] + np.array([0, 0, 0, 0]), cam)
            px, py = (p[0] + p[2]) / 2, p[3]
            r = 4 - j * 0.12
            if tau > 0.5:
                d.ellipse([px - r, py - r, px + r, py + r], fill=c8(ION, int(200 * (1 - j / 24))))
        verrou(d, vers_sortie(bx, cam), tau, 0.35, ION, "PERSONNE · ID 07", 0.97)
        for i, (zb, t0, lab) in enumerate([((1060, 572, 1212, 700), 1.0, "PALETTE · QUAI 4")]):
            verrou(d, vers_sortie(zb, cam), tau, t0, TEXTE2, lab)
        hud_coin(d, W, tau, "CAM 12")
        balayage(d, W, H, tau, 0.1, 0 if vert else W * 0.42)
    elif nom == "stationnement":
        for i, v in enumerate(VOITURES):
            bo = vers_sortie(v, cam)
            if bo[0] > (40 if vert else W * 0.4) and bo[2] < W - 20:
                verrou(d, bo, tau, 0.25 + i * 0.16, ION, "VÉHICULE", 0.94)
        k = int(np.clip(ts * 24, 0, len(CLES_STAT) - 1))
        p = CLES_STAT[k] + np.array([-14, -10, 14, 8])
        alerte = tau > 2.5
        col = FLARE if alerte else ION
        verrou(d, vers_sortie(p, cam), tau, 0.9, col, "COMPORTEMENT SUSPECT" if alerte else "PERSONNE", None if alerte else 0.96)
        hud_coin(d, W, tau, "CAM 03")
        balayage(d, W, H, tau, 0.05, 0 if vert else W * 0.42)
    elif nom == "accueil":
        f = MONO(22, b"Bold")
        x, y = (W * 0.58, H * 0.16) if not vert else (W * 0.08, H * 0.2)
        if tau > 0.4:
            if (tau * 2) % 1 < 0.6:
                d.ellipse([x, y + 6, x + 14, y + 20], fill=c8(ION))
            d.text((x + 26, y), "APPEL ENTRANT · 23:47", font=f, fill=c8(TEXTE, 235))
            d.text((x + 26, y + 34), "RÉCEPTION IA · RÉPOND", font=MONO(20), fill=c8(ION, 230))
    elif nom == "onde":
        x = W * 0.55 if not vert else W * 0.08
        y = H * 0.665 if not vert else H * 0.69
        lignes = ["« Bonjour, j’aimerais un rendez-vous", "jeudi matin, si possible. »"]
        if tau > 0.1:
            fo = min(1, tau / 0.3)
            d.rounded_rectangle([x - 28, y - 24, x + (W * 0.43 if not vert else W * 0.84), y + 270], 16,
                                fill=c8(ABYSSE, int(150 * fo)))
            d.text((x, y), "TRANSCRIPTION EN DIRECT · FR", font=MONO(21, b"Bold"), fill=c8(ION, 240))
            # barre d'onde vivante à droite de l'en-tête
            for j in range(18):
                a = abs(math.sin(tau * 9 + j * 0.7)) * (0.4 + 0.6 * abs(math.sin(j * 1.3 + tau * 3)))
                hb = 4 + 20 * a
                bx = x + 430 + j * 9
                d.rectangle([bx, y + 12 - hb / 2, bx + 4, y + 12 + hb / 2], fill=c8(ION, 220))
        n = int(max(0, tau - 0.3) * 30)
        f = GEIST(40 if not vert else 44, b"Medium")
        for i, l in enumerate(lignes):
            m = max(0, min(len(l), n - sum(len(z) for z in lignes[:i])))
            if m:
                d.text((x, y + 44 + i * 54), l[:m], font=f, fill=c8(TEXTE, 250))
        for i, (t0, txt) in enumerate([(2.35, "INTENTION → RENDEZ-VOUS"), (2.7, "CRÉNEAU → JEUDI 9 H 30")]):
            if tau > t0:
                a = sortie_douce((tau - t0) / 0.25)
                xx = x + (0 if vert or i == 0 else 0) + 30 * (1 - a)
                yy = y + 44 + 2 * 54 + 22 + 50 * i + 34
                etiquette(d, xx, yy, txt, ION, a, 21, fond_sombre=True)
    elif nom == "alerte":
        cw = W * 0.36 if not vert else W * 0.86
        x1 = W * 0.6 if not vert else W * 0.07
        y1 = H * 0.2 if not vert else H * 0.19
        u = sortie_douce((tau - 0.25) / 0.4)
        if u > 0:
            xx = x1 + (W - x1 + 40) * (1 - u)
            ch = 178
            d.rounded_rectangle([xx, y1, xx + cw, y1 + ch], 14, fill=c8(SURF, 232), outline=c8(hx("#2A3446"), 255), width=2)
            d.rounded_rectangle([xx, y1, xx + 6, y1 + ch], 3, fill=c8(FLARE))
            pul = 0.5 + 0.5 * math.sin(tau * 8)
            r = 9 + 5 * pul
            d.ellipse([xx + 34 - r, y1 + 38 - r, xx + 34 + r, y1 + 38 + r], fill=c8(FLARE, int(70 + 60 * pul)))
            d.ellipse([xx + 27, y1 + 31, xx + 41, y1 + 45], fill=c8(FLARE))
            d.text((xx + 58, y1 + 26), "ALERTE · CAM 03 · 02:14", font=MONO(21, b"Bold"), fill=c8(TEXTE2))
            d.text((xx + 30, y1 + 66), "Comportement suspect", font=GEIST(36), fill=c8(TEXTE))
            d.text((xx + 30, y1 + 118), "Stationnement nord · véhicule 2", font=INTER(25), fill=c8(TEXTE2))
        for i, (t0, txt, h) in enumerate([(1.05, "Texto envoyé au responsable", "02:14:03"),
                                           (1.35, "Courriel avec l’extrait vidéo", "02:14:04"),
                                           (1.65, "Tableau de bord mis à jour", "02:14:04")]):
            v = sortie_douce((tau - t0) / 0.35)
            if v <= 0:
                continue
            yy = y1 + 196 + i * 74
            xx = x1 + 60 * (1 - v)
            a = int(255 * min(1, v * 1.5))
            d.rounded_rectangle([xx, yy, xx + cw, yy + 62], 12, fill=c8(SURF, int(a * 0.88)), outline=c8(hx("#1C2433"), a), width=2)
            d.ellipse([xx + 20, yy + 17, xx + 48, yy + 45], outline=c8(ION, a), width=3)
            d.line([(xx + 27, yy + 31), (xx + 33, yy + 37), (xx + 42, yy + 25)], fill=c8(ION, a), width=3)
            d.text((xx + 64, yy + 15), txt, font=INTER(25, b"Medium"), fill=c8(TEXTE, a))
            hw = d.textlength(h, font=MONO(20))
            if not vert or cw > 700:
                d.text((xx + cw - hw - 20, yy + 19), h, font=MONO(20), fill=c8(TEXTE2, a))
    elif nom == "allee":
        x = W - 430 if not vert else W * 0.08
        y = 52 if not vert else H * 0.16
        if tau > 0.2:
            d.text((x, y), "INFRASTRUCTURE LOCALE", font=MONO(22, b"Bold"), fill=c8(TEXTE, 235))
            for j in range(4):
                on = tau > 0.45 + j * 0.18
                d.rectangle([x + j * 30, y + 40, x + j * 30 + 20, y + 52], fill=c8(ION if on else TEXTE2, 240 if on else 90))
            d.text((x + 132, y + 34), "4/4 NŒUDS · EN LIGNE", font=MONO(20), fill=c8(ION, 230))
        balayage(d, W, H, tau, 0.25, 0 if vert else W * 0.42)
    return np.asarray(im, np.float32) / 255


# ------------------------------------------------------------------------------------------------ assemblage
_R = {}
def rampe(fmt, W, H):
    """0 côté titre (gauche en 16:9, haut en 9:16), 1 côté action."""
    if fmt not in _R:
        if fmt == "16x9":
            r = np.clip((np.arange(W, dtype=np.float32) / W - 0.2) / 0.38, 0, 1)[None, :, None]
        else:
            r = np.clip((np.arange(H, dtype=np.float32) / H - 0.05) / 0.3, 0, 1)[:, None, None]
        _R[fmt] = r * r * (3 - 2 * r)
    return _R[fmt]


def rendre_plan(k, tau, fmt, W, H):
    b = BEATS[k]
    x, cam = image_plaque(b, tau, fmt, W, H)
    if b.get("calme"):
        x = ABYSSE + (x - ABYSSE) * (1 - b["calme"] * (1 - rampe(fmt, W, H)))
    c = couches(b, tau, cam, W, H, fmt)
    a = c[..., 3:4]
    return x * (1 - a) + c[..., :3] * a


def trainee(x, force):
    """Flou de bougé horizontal (fouet)."""
    H, W = x.shape[:2]
    im = Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8))
    w = max(16, int(W / (4 + 20 * force)))
    p = im.resize((w, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2.5)).resize((W, H), Image.BICUBIC)
    return np.asarray(p, np.float32) / 255


def decaler(x, dx):
    dx = int(dx)
    if dx == 0:
        return x
    y = np.roll(x, dx, axis=1)
    return y


def transition(typ, u, A, B, W):
    if typ == "fondu":
        a = ease(u)
        return A * (1 - a) + B * a
    if typ == "eclair":
        a = ease((u - 0.3) / 0.4)
        f = math.exp(-((u - 0.5) / 0.2) ** 2)
        x = A * (1 - a) + B * a
        return x * (1 + 0.9 * f) + np.array([0.55, 0.78, 1.0], np.float32) * 0.22 * f
    # fouet : les deux plans filent vers la gauche, flou de bougé au milieu
    f = math.sin(math.pi * u)
    A2 = trainee(decaler(A, -u * W * 0.45), f)
    B2 = trainee(decaler(B, (1 - u) * W * 0.45), f)
    a = ease((u - 0.35) / 0.3)
    return A2 * (1 - a) + B2 * a


GR = {}
def finir(x, i, W, H, fmt):
    # bloom
    hi = np.clip(x - 0.62, 0, None)
    pe = Image.fromarray((np.clip(hi * 2.4, 0, 1) * 255).astype(np.uint8)).resize((W // 8, H // 8), Image.BILINEAR)
    pe = pe.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
    x = x + np.asarray(pe, np.float32) / 255 * 0.42 * np.array([0.85, 0.95, 1.0], np.float32)
    # calme de la zone du titre + vignette
    if fmt not in GR:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        if fmt == "16x9":
            calme = 0.5 + 0.5 * np.clip((xx / W - 0.1) / 0.45, 0, 1) ** 1.3
        else:
            calme = 0.7 + 0.3 * np.clip((yy / H - 0.04) / 0.3, 0, 1)
        r = np.sqrt(((xx / W - 0.5) * 1.6) ** 2 + ((yy / H - 0.5) * 1.6) ** 2)
        vig = 1 - 0.32 * np.clip(r - 0.45, 0, 1) ** 1.4
        rng = np.random.default_rng(7)
        grains = [rng.normal(0, 1, (H, W)).astype(np.float32) for _ in range(6)]
        GR[fmt] = ((calme * vig)[..., None], grains)
    m, grains = GR[fmt]
    x = ABYSSE + (x - ABYSSE) * m
    lum = x.mean(axis=2, keepdims=True)
    x = x + grains[i % 6][..., None] * (0.012 + 0.03 * lum * (1 - lum))
    # roulement doux des hautes lumières
    x = np.where(x > 0.85, 0.85 + (1 - np.exp(-(x - 0.85) * 4)) * 0.15 / 1.0, x)
    return (np.clip(x, 0, 1) * 255 + np.random.default_rng(i).random(x.shape, np.float32) - 0.5).clip(0, 255).astype(np.uint8)


CTX = {}
def image(i):
    fmt, W, H = CTX["fmt"], CTX["W"], CTX["H"]
    n, s, N = calendrier()
    K = len(BEATS)
    actifs = []
    for k in range(K):
        if s[k] <= i < s[k] + n[k]:
            actifs.append((k, (i - s[k]) / IPS))
    if i >= N - TRANS[-1][1]:
        actifs.append((0, (i - N) / IPS))
    if len(actifs) == 1:
        k, tau = actifs[0]
        x = rendre_plan(k, tau, fmt, W, H)
    else:
        (ka, ta), (kb, tb) = actifs[0], actifs[1]
        T = TRANS[ka][1]
        debut = s[kb] if kb > 0 else N - T  # la transition commence à l'entrée du plan suivant
        u = (i - debut + 0.5) / T
        x = transition(TRANS[ka][0], u, rendre_plan(ka, ta, fmt, W, H), rendre_plan(kb, tb, fmt, W, H), W)
    out = finir(x, i, W, H, fmt)
    g = out.astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mes = (float(g[:, : int(W * 0.45)].mean()), float(g[:, W // 2:].mean()), float(g.mean()))
    return out.tobytes(), mes


def main():
    fmt = sys.argv[1]
    apercu = "--apercu" in sys.argv
    W, H = (1920, 1080) if fmt == "16x9" else (1080, 1920)
    CTX.update(fmt=fmt, W=W, H=H)
    charger()
    n, s, N = calendrier()
    SORTIE.mkdir(parents=True, exist_ok=True)
    idx = list(range(0, N, 15)) if apercu else list(range(N))
    maitre = SORTIE / f"maitre-{fmt}.mp4"
    enc = None if apercu else subprocess.Popen(
        [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(IPS), "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(maitre)],
        stdin=subprocess.PIPE)
    vignettes, mesures = [], []
    with Pool(12) as pool:
        for j, (buf, mes) in enumerate(pool.imap(image, idx, chunksize=2)):
            i = idx[j]
            mesures.append(mes)
            if enc:
                enc.stdin.write(buf)
            if apercu or i % 30 == 0:
                vignettes.append(Image.frombytes("RGB", (W, H), buf).resize((W // 4, H // 4), Image.LANCZOS))
    if enc:
        enc.stdin.close(); enc.wait()
    cols = 6 if fmt == "16x9" else 9
    rows = math.ceil(len(vignettes) / cols)
    pw, ph = vignettes[0].size
    pl = Image.new("RGB", (cols * pw, rows * ph), (20, 20, 20))
    for j, v in enumerate(vignettes):
        pl.paste(v, ((j % cols) * pw, (j // cols) * ph))
    pl.save(SORTIE / f"planche-{fmt}{'-apercu' if apercu else ''}.jpg", quality=85)
    m = np.array(mesures)
    r = {"images": N, "duree_s": N / IPS, "lum_gauche45": round(float(m[:, 0].mean()), 1),
         "lum_droite50": round(float(m[:, 1].mean()), 1), "lum_moy": round(float(m[:, 2].mean()), 1),
         "lum_droite_min": round(float(m[:, 1].min()), 1)}
    (SORTIE / f"mesures-{fmt}.json").write_text(json.dumps(r, indent=1))
    print(r)


if __name__ == "__main__":
    main()
