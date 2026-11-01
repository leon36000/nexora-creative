"""Composition des maquettes : le logo / la mosaique sont poses EN CODE sur une photo de produit vierge.
Perspective (homographie), cylindre, eclairage (carte de luminance de la photo), grain, relief selon la technique
(sérigraphie, broderie, feuille a chaud, gravure laser, vernis UV)."""
import sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nx import *

T = 2400


# ------------------------------------------------------------------ entrees / sorties
def charger_photo(nom, taille=T):
    p = GENEREES / f"{nom}_x.png"
    if not p.exists():
        p = GENEREES / f"{nom}.png"
    im = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if im.shape[0] != taille:
        im = cv2.resize(im, (taille, taille), interpolation=cv2.INTER_LANCZOS4)
    return im.astype(np.float32) / 255.0


def sauver(im, chemin, q=None):
    chemin = Path(chemin); chemin.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(chemin), np.clip(im * 255 + .5, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95] if chemin.suffix == '.jpg' else [])


def grille(photo, sortie, pas=100):
    im = (np.clip(photo, 0, 1) * 255).astype(np.uint8).copy()
    H, W = im.shape[:2]
    for v in range(0, W, pas):
        cv2.line(im, (v, 0), (v, H), (0, 255, 255) if v % 500 == 0 else (0, 160, 160), 1)
        cv2.putText(im, str(v), (v + 3, 24), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
    for v in range(0, H, pas):
        cv2.line(im, (0, v), (W, v), (255, 0, 255) if v % 500 == 0 else (160, 0, 160), 1)
        cv2.putText(im, str(v), (4, v - 4), cv2.FONT_HERSHEY_SIMPLEX, .7, (255, 0, 255), 2)
    cv2.imwrite(str(sortie), cv2.resize(im, (1600, 1600), interpolation=cv2.INTER_AREA) if W > 1600 else im)


def raster_art(svg, ppm, tmp_nom):
    """Rasterise une oeuvre SVG (mm) a ppm pixels/mm : RGBA float32 non prémultiplié."""
    m = re.search(r'width="([\d.]+)mm"', svg)
    w = float(m.group(1))
    sortie = SRC / "code" / "_tmp" / f"{tmp_nom}.png"
    rend_svg_png(svg, sortie, max(16, int(round(w * ppm))), transparent=True)
    im = cv2.imread(str(sortie), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255.0
    if im.shape[2] == 3:
        im = np.dstack([im, np.ones(im.shape[:2], np.float32)])
    return im  # BGRA


# ------------------------------------------------------------------ geometrie
def _pm(bgra):
    out = bgra.copy(); out[..., :3] *= out[..., 3:4]; return out


def _unpm(pm):
    a = pm[..., 3:4]; out = pm.copy(); out[..., :3] = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0); return out


def poser_perspective(art, quad, taille=T, ss=2):
    """art : BGRA ; quad : [(x,y)] TL,TR,BR,BL en pixels image. Retourne BGRA pleine taille (couleur non prémultipliée)."""
    h, w = art.shape[:2]
    quad = np.array(quad, np.float32)
    x0, y0 = np.floor(quad.min(0)).astype(int) - 4
    x1, y1 = np.ceil(quad.max(0)).astype(int) + 4
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(taille, x1), min(taille, y1)
    src = np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32)
    dst = ((quad - [x0, y0]) * ss).astype(np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    pm = _pm(art)
    roi = cv2.warpPerspective(pm, M, ((x1 - x0) * ss, (y1 - y0) * ss), flags=cv2.INTER_AREA if False else cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    roi = cv2.resize(roi, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    out = np.zeros((taille, taille, 4), np.float32)
    out[y0:y1, x0:x1] = _unpm(roi)
    return out


def poser_cylindre(art, w_mm, h_mm, cx, yc, rayon_px, rayon_mm, phi0=0.0, taille=T, ss=2, courbure=0.0, echelle_y=None):
    """Pose sur un cylindre vertical (axe en x=cx). art couvre w_mm x h_mm, centre sur l'angle phi0 (rad) et a la hauteur yc.
    courbure : deformation en 'sourire' de l'ellipse (px de fleche au bord, + vers le bas)."""
    ah, aw = art.shape[:2]
    k = rayon_px / rayon_mm * (echelle_y or 1.0)   # px / mm verticalement
    half = int(rayon_px) + 2
    x0, x1 = max(0, int(cx) - half), min(taille, int(cx) + half)
    yh = int(h_mm * k / 2) + 40
    y0, y1 = max(0, int(yc) - yh), min(taille, int(yc) + yh)
    xs = (np.arange(x0 * ss, x1 * ss) + .5) / ss
    ys = (np.arange(y0 * ss, y1 * ss) + .5) / ss
    X, Y = np.meshgrid(xs, ys)
    s = np.clip((X - cx) / rayon_px, -0.9999, 0.9999)
    phi = np.arcsin(s)
    xm = w_mm / 2 + (phi - phi0) * rayon_mm
    yy = Y - (courbure * (s ** 2) if courbure else 0) - yc
    ym = h_mm / 2 + yy / k
    mapx = (xm / w_mm * aw).astype(np.float32)
    mapy = (ym / h_mm * ah).astype(np.float32)
    pm = _pm(art)
    roi = cv2.remap(pm, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    roi = cv2.resize(roi, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    out = np.zeros((taille, taille, 4), np.float32)
    out[y0:y1, x0:x1] = _unpm(roi)
    return out


# ------------------------------------------------------------------ lumiere
def luma(im):
    return im[..., 0] * .114 + im[..., 1] * .587 + im[..., 2] * .299


def carte_lumiere(base, sigma_fin=6, sigma_large=90, lissage_pre=1.2, force_fin=1.0, force_large=1.0):
    """Facteur multiplicatif (H,W) qui transporte plis/tissage (fin) et degrades de lumiere (large) de la photo."""
    L = luma(base)
    L = cv2.GaussianBlur(L, (0, 0), lissage_pre)
    large = cv2.GaussianBlur(L, (0, 0), sigma_large) + 1e-3
    moyen = cv2.GaussianBlur(L, (0, 0), sigma_fin) + 1e-3
    fin = np.clip(moyen / (cv2.GaussianBlur(L, (0, 0), sigma_fin * 5) + 1e-3), .55, 1.6)
    ref = np.median(large[large > 0.01]) if (large > .01).any() else 1
    gl = np.clip(large / ref, .55, 1.7)
    return (fin ** force_fin) * (gl ** force_large)


def grain(im, sigma=0.012, graine=3):
    rng = np.random.default_rng(graine)
    n = rng.normal(0, sigma, im.shape[:2]).astype(np.float32)
    n = cv2.GaussianBlur(n, (0, 0), .6) * 1.6
    return im + n[..., None]


def composite(base, couleur, alpha):
    a = np.clip(alpha, 0, 1)[..., None]
    return base * (1 - a) + couleur * a


# ------------------------------------------------------------------ techniques
def _bgr(h):
    r, g, b = rgb(h); return np.array([b, g, r], np.float32) / 255.0


def lum_clair(base, masque_zone=None, plafond=1.0, sigma=120):
    """Support clair : l'encre ne peut etre plus claire que le tissu au meme endroit (blanc de reference = 95e percentile)."""
    L = cv2.GaussianBlur(luma(base), (0, 0), sigma)
    ref = np.percentile(L[L > .15], 95)
    return np.clip(L / ref, .55, plafond)


def encre(base, art_bgra, lum=None, mat=0.0, souplesse=.8, texture=1.0, densite=0.97, tissage=0.0):
    """Serigraphie / transfert : l'encre prend la lumiere et le tissage du support (tissage : relief fin du tissu a travers l'encre)."""
    lum = carte_lumiere(base, force_fin=texture) if lum is None else lum
    a = cv2.GaussianBlur(art_bgra[..., 3], (0, 0), souplesse) * densite
    col = art_bgra[..., :3] * lum[..., None]
    if tissage:
        L = luma(base); hp = (L - cv2.GaussianBlur(L, (0, 0), 2.2)) / (cv2.GaussianBlur(L, (0, 0), 2.2) + .02)
        col = col * (1 + tissage * np.clip(hp, -.4, .4))[..., None]
    out = composite(base, col, a)
    return out


bgr = _bgr


def broderie(base, art_bgra, pitch=5.0, angle_deg=35, relief=1.0, ombre=.5, taille=T, lum=None, seglen=None):
    """Broderie (remplissage tatami) : rangs de fils arrondis, points decales avec petites encoches d'aiguille,
    relief eclaire en haut a gauche, ombre portee sur le tissu."""
    A = art_bgra[..., 3]
    H, W = A.shape
    seglen = seglen or pitch * 5.5
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    th = np.deg2rad(angle_deg)
    u = (xx * np.cos(th) + yy * np.sin(th)).astype(np.float32)
    v = (-xx * np.sin(th) + yy * np.cos(th)).astype(np.float32)
    rang = np.floor(v / pitch).astype(np.int64)
    rng = np.random.default_rng(11)
    nr = int(rang.max() - rang.min() + 3)
    off = rng.random(nr).astype(np.float32)[rang - rang.min()]
    bril = (0.9 + 0.2 * rng.random(nr)).astype(np.float32)[rang - rang.min()]
    frac = (v / pitch - rang).astype(np.float32)
    prof = 1 - (2 * frac - 1) ** 2                       # section arrondie du fil
    dprof = -2 * (2 * frac - 1) * 2                      # pente transversale
    vh = np.array([-np.sin(th), np.cos(th)], np.float32)
    lum_dir = float(vh @ np.array([-.55, -.8], np.float32))
    su = (u / seglen + off).astype(np.float32)
    fu = su - np.floor(su)
    dist_notch = np.minimum(fu, 1 - fu) * seglen
    notch = np.exp(-(dist_notch / 0.9) ** 2) * (0.12 + 0.14 * prof)
    seg_id = np.floor(su).astype(np.int64)
    seg_b = (0.93 + 0.14 * np.sin(seg_id * 12.9898 + rang * 78.233) ).astype(np.float32)
    Am = cv2.GaussianBlur(A, (0, 0), 2.2)
    bord = np.clip(Am * 1.6, 0, 1)
    shade = 1.0 + 0.42 * relief * dprof * lum_dir * 0.5
    sheen = 0.72 + 0.55 * prof ** 1.3
    couleur_f = (shade * sheen * bril * seg_b * (1 - notch) * (0.72 + 0.28 * bord)).astype(np.float32)
    lum = carte_lumiere(base, force_fin=.4) if lum is None else lum
    col = art_bgra[..., :3] * (couleur_f * lum)[..., None]
    spec = (np.clip(prof - .82, 0, 1) * 1.6 * bril)[..., None] * np.array([.5, .55, .6], np.float32) * .5
    col = np.clip(col + spec * (A[..., None] > .5), 0, 1)
    sh = cv2.GaussianBlur(np.roll(np.roll(A, 4, 0), 3, 1), (0, 0), 3.5)
    out = base * (1 - ombre * sh)[..., None]
    a = cv2.GaussianBlur(A, (0, 0), .6)
    col = cv2.GaussianBlur(col, (0, 0), .45)
    return composite(out, col, a)


def feuille_chaud(base, art_bgra, teinte="#FF5A1F", lum=None, relief=1.0):
    """Dorure / feuille a chaud (orange) : surface metallique a reflets anisotropes, bord en creux (gaufrage)."""
    A = art_bgra[..., 3]
    H, W = A.shape
    Am = cv2.GaussianBlur(A, (0, 0), 1.4)
    # relief : creux sous la feuille
    gx = cv2.Sobel(Am, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(Am, cv2.CV_32F, 0, 1, ksize=3) / 8
    bord = np.clip(-(gx * .7 + gy * .7) * 5 * relief, -1, 1)          # eclairage haut-gauche
    # reflet anisotrope : bandes diffuses en diagonale selon la position
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    env = .5 + .5 * np.sin((xx * .6 + yy * .35) / 55.0 + 1.2) * .6 + .25 * np.sin((xx - yy) / 130.0)
    env = cv2.GaussianBlur(env, (0, 0), 6)
    micro = cv2.GaussianBlur(np.random.default_rng(5).normal(0, 1, (H, W)).astype(np.float32), (0, 0), .7) * .05
    t = _bgr(teinte)
    k = (0.9 + 0.5 * env + micro + .25 * bord)[..., None]
    col = np.clip(t * k + np.clip(k - 1.05, 0, 1) * .55 * np.array([.55, .8, 1.0], np.float32), 0, 1)
    # ombre/ressaut au bord
    sh = cv2.GaussianBlur(np.roll(np.roll(A, 2, 0), 2, 1), (0, 0), 2.0)
    out = base * (1 - .35 * sh)[..., None]
    return composite(out, col, cv2.GaussianBlur(A, (0, 0), .6))


def gaufrage_sec(base, art_bgra, force=1.0, poli=.05):
    """Gaufrage a sec (relief sans feuille) : le motif est repousse dans la couverture ; arete eclairee en haut a gauche,
    ombre de l'autre cote, interieur legerement poli."""
    A = cv2.GaussianBlur(art_bgra[..., 3], (0, 0), 1.6)
    gx = cv2.Sobel(A, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(A, cv2.CV_32F, 0, 1, ksize=3) / 8
    b = -(gx * .7 + gy * .7) * 7 * force            # + = arete eclairee
    L = luma(base)
    eclat = np.clip(b, 0, 1) * (.20 + .8 * L)
    ombre = np.clip(-b, 0, 1)
    out = base * (1 - .55 * ombre)[..., None] + (eclat * .55)[..., None]
    inter = cv2.GaussianBlur(art_bgra[..., 3], (0, 0), .8)
    out = out + (inter * poli * (.3 + L))[..., None]
    return out


def gravure_inox(base, art_bgra, k=.16, teinte_chaude=.03):
    """Gravure laser sur inox brosse : oxydation noire mate, la lumiere et le brossage du support restent visibles."""
    A = cv2.GaussianBlur(art_bgra[..., 3], (0, 0), .7)
    H, W = A.shape
    micro = cv2.GaussianBlur(np.random.default_rng(13).normal(0, 1, (H, W)).astype(np.float32), (0, 0), sigmaX=6, sigmaY=.6) * .02
    L = luma(base)
    mark = (base * k + (.012 + .06 * L + micro)[..., None])
    mark[..., 2] += teinte_chaude * L
    gx = cv2.Sobel(A, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(A, cv2.CV_32F, 0, 1, ksize=3) / 8
    mark = mark + (np.clip(-(gx * .7 + gy * .7) * 3, 0, 1) * .12)[..., None]
    return composite(base, np.clip(mark, 0, 1), A * .97)


def gravure(base, art_bgra, clair=.62, sombre=0, profondeur=1.0, grain_micro=.06, couleur=None):
    """Gravure laser : le revetement est ablate ; marque claire mate (anodise noir) ou sombre (inox)."""
    A = cv2.GaussianBlur(art_bgra[..., 3], (0, 0), .8)
    H, W = A.shape
    gx = cv2.Sobel(A, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(A, cv2.CV_32F, 0, 1, ksize=3) / 8
    micro = cv2.GaussianBlur(np.random.default_rng(9).normal(0, 1, (H, W)).astype(np.float32), (0, 0), .6)
    bord = -(gx * .7 + gy * .7) * 2.5 * profondeur
    L = luma(base)
    if couleur is None:
        v = clair * (0.85 + 0.35 * np.clip(L / (np.percentile(L[A > .5], 50) + 1e-3), 0, 2) * .3) + grain_micro * micro + .18 * bord
        col = np.repeat(v[..., None], 3, 2) * np.array([1.0, .99, .97], np.float32)
    else:
        col = _bgr(couleur)[None, None, :] * (1 + grain_micro * micro + .2 * bord)[..., None]
    return composite(base, np.clip(col, 0, 1), A)


def comprime(lum, k=.35, lo=.82, hi=1.08):
    """Le logo ne doit jamais ressembler a un degrade : on ne garde qu'une fraction de la lumiere ambiante."""
    return np.clip(1 + k * (lum - 1), lo, hi)


def vernis_uv(base, art_bgra, lum=None, brillance=.5, k=.35, plafond=.93):
    """Impression UV : encre lisse, leger reflet speculaire doux, minuscule relief."""
    A = art_bgra[..., 3]
    lum = comprime(carte_lumiere(base, force_fin=.3, sigma_large=140), k) if lum is None else lum
    Am = cv2.GaussianBlur(A, (0, 0), 1.2)
    gx = cv2.Sobel(Am, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(Am, cv2.CV_32F, 0, 1, ksize=3) / 8
    spec = np.clip(-(gx * .6 + gy * .8) * 5, 0, 1) * brillance * .55
    col = np.minimum(art_bgra[..., :3] * lum[..., None] + spec[..., None], plafond)
    return composite(base, col, cv2.GaussianBlur(A, (0, 0), .6))


def ombre_contact(im, masque, dx=0, dy=14, flou=26, force=.5):
    """Ombre portee d'un objet decoupe (maquettes d'objets poses)."""
    m = np.roll(np.roll(masque, dy, 0), dx, 1)
    s = cv2.GaussianBlur(m, (0, 0), flou)
    return im * (1 - force * s)[..., None]


def lueur_chaude(im, centre, rayon, intensite=.25, couleur="#FF5A1F"):
    H, W = im.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot(xx - centre[0], yy - centre[1]) / rayon
    g = np.exp(-(d ** 2) * 1.6)[..., None]
    return np.clip(im + g * _bgr(couleur) * intensite, 0, 1)


def finition(im, grain_sigma=.011, vignette=.18, graine=3):
    H, W = im.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    im = im * (1 - vignette * np.clip(d - .35, 0, 1.2) ** 1.6)[..., None]
    return np.clip(grain(im, grain_sigma, graine), 0, 1)
