#!/usr/bin/env python3
"""Vidéo vitrine du héros de l'accueil (« Signal », reprise du 02/11/2026).

Aucune pellicule ni modèle génératif : tout est calculé en code (numpy + Pillow, encodage ffmpeg), pour un rendu
« motion design » net plutôt qu'un aspect de banque d'images IA.

Ce que montre la boucle (12 s, muette, sans texte) :
  - VOIR    : un glissement lent dans l'allée d'un entrepôt relevée en nuage de points façon lidar (anneaux de balayage,
              front de scan qui parcourt l'allée deux fois par boucle) ; deux chariots chargés roulent devant nous et des
              crochets de détection se verrouillent sur eux.
  - ÉCOUTER : en bas à droite, une onde vocale en barres fines se dessine, puis s'aplatit en lignes de transcription.
  - AGIR    : un seul point chaud (#FF6A2B) : le second chariot passe en alerte (crochets orange, ondes au sol), puis revient.
Les 45 % de gauche (16:9) ou le haut (9:16) restent sombres et calmes pour le titre posé par le site.

Boucle sans couture : tout dépend de t/T de façon périodique ; la caméra avance d'exactement une travée (P) et le
contenu des rayonnages (seul élément non périodique) est fondu sur ses voisins pendant les 2 dernières secondes.
Finitions : objectif décentré (verticales droites), halo à deux rayons, brume au point de fuite, vignettage, grain fin
et tramage avant quantification (pas de bandes).

Usage :
  python3 boucle_signal.py planche {16x9|9x16}     # planche contact de 12 images + une image pleine taille
  python3 boucle_signal.py rendu   {16x9|9x16}     # rendu complet -> maître intermédiaire -> MP4/WebM/affiches
"""
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

T, FPS = 12.0, 30
NF = int(T * FPS)
P = 2.8                      # longueur d'une travée (m) : la caméra avance de P en T
FONDU = 2.0                  # fondu du contenu des rayonnages en fin de boucle (s)
ION = np.array([62, 200, 255], np.float32) / 255
ORANGE = np.array([255, 106, 43], np.float32) / 255
FOND = np.array([5, 7, 11], np.float32) / 255
TEINTE = 0.80 * ION + 0.20   # couleur des points : ion avec un cœur légèrement blanc
FFMPEG = os.path.expanduser("~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
OUT = os.path.expanduser("~/nexora-creative-data/site-medias/hero-v2")

FORMATS = {
    # cx, cy : point principal (objectif décentré) ; f : focale en fraction de W ; calme : zone laissée au titre ;
    # onde : (x début, x fin, y) de l'onde vocale, en fractions de l'image.
    "16x9": dict(W=1920, H=1080, cx=0.665, cy=0.47, f=0.90, calme=("x", 0.34, 0.56), onde=(0.62, 0.90, 0.86)),
    "9x16": dict(W=1080, H=1920, cx=0.56, cy=0.58, f=1.65, calme=("y", 0.28, 0.46), onde=(0.16, 0.84, 0.86)),
}
GAIN = 1.7


def lisse(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def sortie(x):  # ease-out cubique
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


# ----------------------------------------------------------------------------------------------------------------------
# Géométrie (monde : x à droite, y en haut, z vers l'avant ; mètres)
# ----------------------------------------------------------------------------------------------------------------------
ANNEAU = 0.045  # pas vertical des anneaux du lidar


def grille_y(y0, y1):
    return np.arange(math.ceil(y0 / ANNEAU) * ANNEAU, y1, ANNEAU)


def face_x(r, x, z0, z1, y0, y1, dz=0.03, garde=0.85, poids=1.0):
    """Face verticale parallèle à l'allée (devant de colis) : points sur les anneaux, arêtes renforcées."""
    ys, zs = grille_y(y0, y1), np.arange(z0, z1, dz)
    Z, Y = np.meshgrid(zs, ys)
    Z = Z.ravel() + r.uniform(-dz / 2, dz / 2, Z.size)
    Y = Y.ravel()
    m = r.random(Z.size) < garde
    Z, Y = Z[m], Y[m]
    bord = (np.minimum(Z - z0, z1 - Z) < 0.035) | (np.minimum(Y - y0, y1 - Y) < 0.05)
    return np.c_[np.full(Z.size, x) + r.normal(0, 0.006, Z.size), Y, Z], np.where(bord, 2.0, 1.0) * poids


def face_z(r, z, x0, x1, y0, y1, dx=0.022, garde=0.9, poids=1.0):
    ys, xs = grille_y(y0, y1), np.arange(x0, x1, dx)
    X, Y = np.meshgrid(xs, ys)
    X = X.ravel() + r.uniform(-dx / 2, dx / 2, X.size)
    Y = Y.ravel()
    m = r.random(X.size) < garde
    X, Y = X[m], Y[m]
    bord = (np.minimum(X - x0, x1 - X) < 0.03) | (np.minimum(Y - y0, y1 - Y) < 0.05)
    return np.c_[X, Y, np.full(X.size, z)], np.where(bord, 2.0, 1.0) * poids


def face_y(r, y, x0, x1, z0, z1, d=0.03, garde=0.8, poids=1.0):
    xs, zs = np.arange(x0, x1, d), np.arange(z0, z1, d)
    X, Z = np.meshgrid(xs, zs)
    X, Z = X.ravel() + r.uniform(-d / 2, d / 2, X.size), Z.ravel() + r.uniform(-d / 2, d / 2, X.size)
    m = r.random(X.size) < garde
    X, Z = X[m], Z[m]
    bord = (np.minimum(X - x0, x1 - X) < 0.03) | (np.minimum(Z - z0, z1 - Z) < 0.03)
    return np.c_[X, np.full(X.size, y), Z], np.where(bord, 1.8, 0.8) * poids


def ligne(a, b, pas, poids):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = max(2, int(np.linalg.norm(b - a) / pas))
    u = np.linspace(0, 1, n)[:, None]
    return a + (b - a) * u, np.full(n, poids)


def assemble(parts):
    return np.concatenate([p for p, _ in parts]).astype(np.float32), np.concatenate([w for _, w in parts]).astype(np.float32)


def travee_structure():
    """Une travée (z dans [0, P)) : montants, lisses, sol, plafonniers. Identique d'une travée à l'autre."""
    parts = []
    for cote in (-1, 1):
        xf, xb = cote * 1.7, cote * 2.75
        for xp in (xf, xb):
            for dx in (0.0, cote * 0.08):
                for dz in (0.0, 0.08):
                    parts.append(ligne((xp + dx, 0, dz), (xp + dx, 6.3, dz), ANNEAU, 1.1 if xp == xf else 0.5))
        for yb in (0.15, 1.75, 3.35, 4.95):
            for dy in (0.0, 0.12):
                parts.append(ligne((xf, yb + dy, 0), (xf, yb + dy, P), 0.05, 0.4))
    # sol : grille fine pointillée au mètre, marquage d'allée en tirets, poussière
    for xg in (-0.6, 0.6):
        parts.append(ligne((xg, 0, 0), (xg, 0, P), 0.07, 0.3))
    for zg in np.arange(0, P, 0.7):
        parts.append(ligne((-1.65, 0, zg), (1.65, 0, zg), 0.07, 0.3))
    for xl in (-1.3, 1.3):
        p, w = ligne((xl, 0, 0), (xl, 0, P), 0.018, 0.75)
        m = (p[:, 2] % 1.4) < 0.85
        parts.append((p[m], w[m]))
    r = np.random.default_rng(11)
    n = 1600
    parts.append((np.c_[r.uniform(-1.7, 1.7, n), np.zeros(n), r.uniform(0, P, n)], np.full(n, 0.16)))
    # plafonnier linéaire au-dessus de l'allée
    parts.append(ligne((0, 7.2, 0.5), (0, 7.2, 1.9), 0.012, 1.6))
    return assemble(parts)


def travee_contenu(k):
    """Colis et palettes d'une travée k (varie d'une travée à l'autre)."""
    r = np.random.default_rng(1000 + k)
    parts = []
    for cote in (-1, 1):
        x = cote * 1.62
        for niveau in (0.27, 1.87, 3.47, 5.07):
            z = 0.08
            hmax = 1.1 if niveau > 5 else 1.4
            while True:
                larg = r.uniform(0.55, 1.25)
                if z + larg > P - 0.08:
                    break
                if r.random() < 0.8:
                    h = r.uniform(0.5, hmax)
                    p, w = face_x(r, x + cote * r.uniform(0, 0.12), z, z + larg, niveau, niveau + h, garde=0.78, poids=0.75)
                    if h > 0.8 and r.random() < 0.6:  # colis empilés : une couture horizontale
                        yc = niveau + h * r.uniform(0.4, 0.6)
                        m = np.abs(p[:, 1] - yc) > 0.03
                        p, w = p[m], w[m]
                    parts.append((p, w))
                z += larg + r.uniform(0.04, 0.16)
    p, w = assemble(parts)
    p[:, 2] += k * P
    return p, w


def chariot(cote_visible, graine):
    """Chariot bas chargé de colis, centré en (0, 0, 0), vu de l'arrière : faces arrière, dessus, flanc visible."""
    r = np.random.default_rng(graine)
    boites = [(-0.45, 0.45, 0.10, 0.30, -0.60, 0.60),
              (-0.42, 0.00, 0.30, 1.00, -0.55, 0.05),
              (0.03, 0.42, 0.30, 0.78, -0.55, 0.55),
              (-0.42, 0.00, 0.30, 0.72, 0.08, 0.55),
              (-0.30, 0.22, 1.00, 1.30, -0.50, -0.05)]
    parts = []
    for x0, x1, y0, y1, z0, z1 in boites:
        parts.append(face_z(r, z0, x0, x1, y0, y1, poids=1.0))
        parts.append(face_y(r, y1, x0, x1, z0, z1, poids=0.9))
        xs = x0 if cote_visible < 0 else x1
        parts.append(face_x(r, xs, z0, z1, y0, y1, dz=0.025, garde=0.85, poids=0.8))
    for wx in (-0.36, 0.36):  # roues
        for wz in (-0.48, 0.48):
            a = np.linspace(0, 2 * np.pi, 40)
            parts.append((np.c_[np.full(40, wx), 0.06 + 0.06 * np.sin(a), wz + 0.06 * np.cos(a)], np.full(40, 1.2)))
    return assemble(parts)


BOITE_CHARIOT = np.array([[x, y, z] for x in (-0.5, 0.5) for y in (0.0, 1.36) for z in (-0.64, 0.64)], np.float32)

STRUCT_1, STRUCT_W1 = travee_structure()
TRAVEES = range(-2, 21)
STRUCT = np.concatenate([STRUCT_1 + np.array([0, 0, k * P], np.float32) for k in TRAVEES])
STRUCT_W = np.tile(STRUCT_W1, len(TRAVEES))
_c = [travee_contenu(k) for k in TRAVEES]
CONT = np.concatenate([p for p, _ in _c])
CONT_W = np.concatenate([w for _, w in _c])
CHAR_A = chariot(-1, 5)
CHAR_B = chariot(+1, 6)
_r = np.random.default_rng(3)
PHASE_S = _r.uniform(0, 2 * np.pi, STRUCT.shape[0]).astype(np.float32)
PHASE_C = _r.uniform(0, 2 * np.pi, CONT.shape[0]).astype(np.float32)


# ----------------------------------------------------------------------------------------------------------------------
# Caméra, projection, dépôt des points
# ----------------------------------------------------------------------------------------------------------------------
def camera(t):
    ph = 2 * np.pi * t / T
    return dict(x=-0.35 + 0.08 * math.sin(ph), y=1.6 + 0.05 * math.sin(ph + 1.3), z=P * t / T,
                lacet=0.012 * math.sin(ph + 0.7))


def chariots(t):
    ph = 2 * np.pi * t / T
    cz = P * t / T
    return [dict(nom="A", x=0.8 + 0.04 * math.sin(ph * 2), z=cz + 10.0 + 1.1 * math.sin(ph), pts=CHAR_A),
            dict(nom="B", x=-0.8 + 0.05 * math.sin(ph + 1), z=cz + 17.5 + 1.8 * math.sin(ph + 2.2), pts=CHAR_B)]


def projette(F, cam, p):
    X, Y, Z = p[:, 0] - cam["x"], p[:, 1] - cam["y"], p[:, 2] - cam["z"]
    c, s = math.cos(cam["lacet"]), math.sin(cam["lacet"])
    X, Z = X * c - Z * s, X * s + Z * c
    Zs = np.maximum(Z, 1e-3)
    f = F["f"] * F["W"]
    return F["cx"] * F["W"] + f * X / Zs, F["cy"] * F["H"] - f * Y / Zs, Z


def depose(buf, W, H, sx, sy, w):
    """Dépôt bilinéaire (anticrénelé) d'intensités dans un tampon plat W*H."""
    x0, y0 = np.floor(sx), np.floor(sy)
    ok = (x0 >= 0) & (x0 < W - 1) & (y0 >= 0) & (y0 < H - 1) & (w > 1e-5)
    x0, y0, fx, fy, w = x0[ok].astype(np.int64), y0[ok].astype(np.int64), (sx - x0)[ok], (sy - y0)[ok], w[ok]
    i = y0 * W + x0
    idx = np.concatenate([i, i + 1, i + W, i + W + 1])
    ww = np.concatenate([w * (1 - fx) * (1 - fy), w * fx * (1 - fy), w * (1 - fx) * fy, w * fx * fy])
    buf += np.bincount(idx, ww, minlength=W * H)


def nuage(F, buf, cam, t, p, w, phase=None):
    sx, sy, Z = projette(F, cam, p)
    wd = np.exp(-Z / 15.0) * lisse((Z - 0.7) / 1.5)
    # front de scan : parcourt l'allée deux fois par boucle, laisse une rémanence derrière lui
    d = 1.5 + 44.0 * ((2 * t / T) % 1.0)
    av = d - Z
    scan = 1.6 * np.exp(-(av / 0.45) ** 2) + np.where(av > 0, 0.45 * np.exp(-av / 4.0), 0.0)
    v = w * wd * (0.55 + scan)
    if phase is not None:
        v *= 0.85 + 0.15 * np.sin(4 * np.pi * t / T + phase)
    depose(buf, F["W"], F["H"], sx, sy, v)


# ----------------------------------------------------------------------------------------------------------------------
# Interface (crochets, onde, transcription, alerte) : calque RVB séparé
# ----------------------------------------------------------------------------------------------------------------------
def rect(hud, x0, x1, y0, y1, rgb, a):
    """Rectangle aligné aux axes, bords fractionnaires anticrénelés."""
    H, W, _ = hud.shape
    if a <= 0 or x1 <= x0 or y1 <= y0:
        return
    c0, c1 = max(int(math.floor(x0)), 0), min(int(math.ceil(x1)), W)
    r0, r1 = max(int(math.floor(y0)), 0), min(int(math.ceil(y1)), H)
    if c1 <= c0 or r1 <= r0:
        return
    cols = np.arange(c0, c1)
    rows = np.arange(r0, r1)
    cx = np.clip(np.minimum(x1, cols + 1) - np.maximum(x0, cols), 0, 1)
    cy = np.clip(np.minimum(y1, rows + 1) - np.maximum(y0, rows), 0, 1)
    hud[r0:r1, c0:c1] += (a * np.outer(cy, cx))[..., None] * rgb


def points_hud(hud, sx, sy, v, rgb):
    H, W, _ = hud.shape
    buf = np.zeros(W * H)
    depose(buf, W, H, sx, sy, v)
    hud += buf.reshape(H, W)[..., None] * rgb


def crochets(hud, S, box, prog, a, rgb, tag_a, tag_rgb):
    x0, y0, x1, y1 = box
    e = (1 - prog) * 30 * S
    x0, y0, x1, y1 = x0 - e, y0 - e, x1 + e, y1 + e
    L = float(np.clip(0.22 * min(x1 - x0, y1 - y0), 9 * S, 24 * S))
    th = 1.6 * S
    for (cx, sxn) in ((x0, 1), (x1, -1)):
        for (cy, syn) in ((y0, 1), (y1, -1)):
            hx0, hx1 = (cx, cx + sxn * L) if sxn > 0 else (cx + sxn * L, cx)
            rect(hud, hx0, hx1, cy - th / 2, cy + th / 2, rgb, a)
            vy0, vy1 = (cy, cy + syn * L) if syn > 0 else (cy + syn * L, cy)
            rect(hud, cx - th / 2, cx + th / 2, vy0, vy1, rgb, a)
    if tag_a > 0:  # étiquette abstraite : un filet puis deux barres (aucun glyphe)
        lx = x1 + 6 * S
        rect(hud, lx, lx + 26 * S, y0 - 0.5 * S, y0 + 0.5 * S, tag_rgb, 0.55 * tag_a)
        bx = lx + 32 * S
        rect(hud, bx, bx + 34 * S * sortie(tag_a), y0 - 1.3 * S, y0 + 1.3 * S, tag_rgb, 0.9 * tag_a)
        rect(hud, bx, bx + 20 * S * sortie(tag_a), y0 + 6 * S, y0 + 8.2 * S, tag_rgb, 0.5 * tag_a)


def fenetre(t, t0, t1, montee=0.5, descente=0.6):
    return sortie((t - t0) / montee) * (1 - lisse((t - (t1 - descente)) / descente))


MOTS_1 = [(0.0, 0.07), (0.10, 0.24), (0.27, 0.33), (0.37, 0.55), (0.59, 0.66), (0.70, 0.86), (0.89, 1.0)]
MOTS_2 = [(0.0, 0.17), (0.21, 0.29), (0.33, 0.52), (0.56, 0.63)]
MOTS_3 = [(0.0, 0.11), (0.15, 0.36)]
_ra = np.random.default_rng(21)
AMP_MOTS = _ra.uniform(0.45, 1.0, len(MOTS_1))


def enveloppe(u):
    e = np.zeros_like(u)
    for (a, b), amp in zip(MOTS_1, AMP_MOTS):
        m = (u >= a) & (u <= b)
        e[m] = amp * np.sin(np.pi * (u[m] - a) / (b - a)) ** 0.5
    return e


def lignes_mots(hud, mots, xa, xb, y, prog, S, a):
    """Une ligne de transcription : barres de mots, tapées de gauche à droite selon prog."""
    for (u0, u1) in mots:
        v = np.clip((prog * 1.15 - u0) / max(u1 - u0, 1e-3), 0, 1)
        if v > 0:
            rect(hud, xa + u0 * (xb - xa), xa + (u0 + v * (u1 - u0)) * (xb - xa), y - 1.3 * S, y + 1.3 * S, ION, a)


def onde(hud, F, t, S):
    W, H = F["W"], F["H"]
    xa, xb, yb = F["onde"][0] * W, F["onde"][1] * W, F["onde"][2] * H
    glob = 1 - lisse((t - 10.2) / 0.8)
    if t < 3.1 or glob <= 0:
        return
    # témoin d'écoute
    vie = fenetre(t, 3.2, 6.6, 0.3, 0.5)
    rect(hud, xa - 16 * S, xa - 11 * S, yb - 2.5 * S, yb + 2.5 * S, ION, (0.6 + 0.4 * math.sin(t * 9)) * vie * glob)
    pas = 4.0 * S
    n = int((xb - xa) / pas)
    u = (np.arange(n) + 0.5) / n
    rev = sortie((t - 3.5) / 2.0)
    ecr = lisse((t - 6.0) / 0.8)               # l'onde s'aplatit en texte
    mont = sortie((t - 6.9) / 0.5)             # la première ligne remonte
    y1 = yb - 18 * S * mont
    env = enveloppe(u)
    h = env * (0.3 + 0.7 * np.abs(np.sin(2 * np.pi * (u * 7.3 + t * 2.1)) * np.sin(2 * np.pi * (u * 3.1 - t * 1.3) + 1)))
    h = h * 24 * S * (1 - ecr)
    for i in range(n):
        if u[i] > rev:
            rect(hud, xa + i * pas, xa + i * pas + 1.4 * S, y1 - 0.6 * S, y1 + 0.6 * S, ION, 0.18 * glob)
            continue
        hh = max(h[i], 1.3 * S)
        a = (0.85 if env[i] > 0 else 0.3) * (1 - ecr) * glob
        rect(hud, xa + i * pas, xa + i * pas + 1.6 * S, y1 - hh, y1 + hh, ION, a)
    if 0 < rev < 1:  # tête de lecture
        xh = xa + rev * (xb - xa)
        rect(hud, xh - 1 * S, xh + 1 * S, y1 - 14 * S, y1 + 14 * S, ION, 0.8 * glob)
    if ecr > 0:
        lignes_mots(hud, MOTS_1, xa, xb, y1, 1.0, S, 0.85 * ecr * glob)
    lignes_mots(hud, MOTS_2, xa, xb, yb, sortie((t - 7.3) / 0.9), S, 0.55 * glob)
    lignes_mots(hud, MOTS_3, xa, xb, yb + 18 * S, sortie((t - 8.2) / 0.5), S, 0.35 * glob)


def anneau_sol(F, hud, cam, cx, cz, rayon, a, rgb):
    ang = np.linspace(0, 2 * np.pi, 360, endpoint=False)
    p = np.c_[cx + rayon * np.cos(ang), np.full(ang.size, 0.02), cz + rayon * np.sin(ang)].astype(np.float32)
    sx, sy, Z = projette(F, cam, p)
    points_hud(hud, sx, sy, np.where(Z > 0.8, a, 0.0) * 1.2, rgb)


# ----------------------------------------------------------------------------------------------------------------------
# Image
# ----------------------------------------------------------------------------------------------------------------------
_PRE = {}


def precalc(F):
    k = id(F)
    if k not in _PRE:
        W, H = F["W"], F["H"]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ax, a0, a1 = F["calme"]
        c = xx / W if ax == "x" else yy / H
        calme = 0.03 + 0.97 * lisse((c - a0) / (a1 - a0))
        dx, dy = (xx - F["cx"] * W) / W, (yy - F["cy"] * H) / W
        brume = 0.05 * np.exp(-(dx ** 2 + dy ** 2) / 0.02) + 0.025 * np.exp(-(dx ** 2 + (dy * 1.6) ** 2) / 0.12)
        rx, ry = (xx / W - 0.5) * 2, (yy / H - 0.5) * 2
        vign = 1 - 0.38 * lisse((rx ** 2 + ry ** 2 - 0.25) / 1.6)
        _PRE[k] = (calme.astype(np.float32), (brume * calme).astype(np.float32), vign[..., None].astype(np.float32))
    return _PRE[k]


def flou_boite(a, r):
    for ax in (0, 1):
        n = a.shape[ax]
        pad = [(0, 0)] * a.ndim
        pad[ax] = (r + 1, r)
        c = np.cumsum(np.pad(a, pad, mode="edge"), axis=ax)
        a = (np.take(c, range(2 * r + 1, 2 * r + 1 + n), axis=ax) - np.take(c, range(0, n), axis=ax)) / (2 * r + 1)
    return a


def halo(L, W, H):
    d = L.reshape(H // 4, 4, W // 4, 4, 3).mean(axis=(1, 3))
    b1, b2 = d, d
    for _ in range(3):
        b1 = flou_boite(b1, 2)
        b2 = flou_boite(b2, 9)
    b = 0.55 * b1 + 0.5 * b2
    up = [np.asarray(Image.fromarray(b[..., c].astype(np.float32), "F").resize((W, H), Image.BILINEAR)) for c in range(3)]
    return np.stack(up, -1)


def image(F, i, grain=True):
    t = (i % NF) / FPS
    W, H = F["W"], F["H"]
    S = min(W, H) / 1080
    cam = camera(t)
    calme, brume, vign = precalc(F)
    buf = np.zeros(W * H)
    nuage(F, buf, cam, t, STRUCT, STRUCT_W, PHASE_S)
    a = lisse((t - (T - FONDU)) / FONDU)
    if a < 1:
        nuage(F, buf, cam, t, CONT, CONT_W * (1 - a), PHASE_C)
    if a > 0:
        nuage(F, buf, cam, t, CONT + np.array([0, 0, P], np.float32), CONT_W * a, PHASE_C)
    hud = np.zeros((H, W, 3), np.float32)
    boites = {}
    for c in chariots(t):
        p = c["pts"][0] + np.array([c["x"], 0, c["z"]], np.float32)
        nuage(F, buf, cam, t, p, c["pts"][1] * 1.25)
        sx, sy, _ = projette(F, cam, BOITE_CHARIOT + np.array([c["x"], 0, c["z"]], np.float32))
        boites[c["nom"]] = (sx.min(), sy.min(), sx.max(), sy.max(), c)
    # détections : A verrouillé de 1,4 à 11,0 s ; B de 3,2 à 10,2 s, en alerte de 6,2 à 8,2 s
    for nom, t0, t1 in (("A", 1.4, 11.0), ("B", 3.2, 10.2)):
        x0, y0, x1, y1, c = boites[nom]
        a_det = fenetre(t, t0, t1, 0.5, 0.6)
        if a_det <= 0:
            continue
        al = fenetre(t, 6.2, 8.2, 0.25, 0.35) if nom == "B" else 0.0
        rgb = (1 - al) * ION + al * ORANGE
        crochets(hud, S, (x0, y0, x1, y1), sortie((t - t0) / 0.5), a_det, rgb,
                 sortie((t - t0 - 0.35) / 0.5) * a_det, rgb)
        if al > 0:
            for k, ta in enumerate((6.25, 6.85, 7.45)):
                u = (t - ta) / 1.2
                if 0 < u < 1:
                    anneau_sol(F, hud, cam, c["x"], c["z"], 0.55 + 1.6 * sortie(u), 0.9 * (1 - u) ** 2, ORANGE)
            puls = 0.65 + 0.35 * math.sin((t - 6.2) * 2 * np.pi * 1.6)
            rect(hud, x0 - 30 * S, x0 - 25 * S, y0 - 2.5 * S, y0 + 2.5 * S, ORANGE, 1.6 * al * puls)
    onde(hud, F, t, S)

    L = (buf.reshape(H, W) * calme * 0.9 * GAIN)[..., None] * TEINTE + brume[..., None] * ION + hud
    X = L + 0.85 * halo(L, W, H)
    out = 1 - np.exp(-X)
    out = FOND + out * (1 - FOND)
    out = out * vign
    if grain:
        r = np.random.default_rng(10_000 + i)
        out = out + r.normal(0, 0.009, (H, W, 1)).astype(np.float32) * (0.5 + out)
    out = out * 255 + np.random.default_rng(20_000 + i).uniform(-0.5, 0.5, out.shape).astype(np.float32)
    return np.clip(np.rint(out), 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------------------------------------------------
def _travail(args):
    fmt, i = args
    return image(FORMATS[fmt], i).tobytes()


def planche(fmt):
    F = FORMATS[fmt]
    idx = [int(k * NF / 12) for k in range(12)]
    with Pool(12) as pool:
        ims = pool.map(_travail, [(fmt, i) for i in idx])
    W, H = F["W"], F["H"]
    tw = 480 if fmt == "16x9" else 270
    th = int(tw * H / W)
    cols = 4 if fmt == "16x9" else 6
    rows = 12 // cols
    sheet = Image.new("RGB", (cols * tw, rows * th))
    for k, b in enumerate(ims):
        im = Image.frombytes("RGB", (W, H), b)
        if k == 6 if fmt == "16x9" else k == 6:
            im.save(os.path.join(OUT, f"plein-{fmt}.jpg"), quality=92)
        sheet.paste(im.resize((tw, th), Image.LANCZOS), ((k % cols) * tw, (k // cols) * th))
    sheet.save(os.path.join(OUT, f"planche-{fmt}.jpg"), quality=88)
    print("planche ->", os.path.join(OUT, f"planche-{fmt}.jpg"))


def rendu(fmt):
    F = FORMATS[fmt]
    W, H = F["W"], F["H"]
    maitre = os.path.join(OUT, f"maitre-{fmt}.mp4")
    ff = subprocess.Popen([FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "8",
                           "-pix_fmt", "yuv420p", maitre], stdin=subprocess.PIPE)
    with Pool(18) as pool:
        for k, b in enumerate(pool.imap(_travail, [(fmt, i) for i in range(NF)], chunksize=2)):
            ff.stdin.write(b)
            if k % 60 == 0:
                print(f"  {fmt} image {k}/{NF}", flush=True)
    ff.stdin.close()
    ff.wait()
    # affiche : image sans grain à 5,6 s (deux détections verrouillées, onde en cours)
    aff = Image.fromarray(image(F, int(5.6 * FPS), grain=False))
    base = os.path.join(OUT, f"hero-boucle-{fmt}")
    aff.save(base + "-poster.jpg", quality=90, optimize=True, progressive=True)
    print("maître ->", maitre)


if __name__ == "__main__":
    action, fmt = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    {"planche": planche, "rendu": rendu}[action](fmt)
