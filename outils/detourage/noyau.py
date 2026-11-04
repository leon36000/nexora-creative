"""
Noyau du détourage vidéo de Nexora Creative : toute la mathématique des masques, sans GPU et sans modèle.

- plan de segments avec recouvrement et poids de raccord (vidéos longues) ;
- trimap depuis une bande autour du bord du masque ;
- fusion « masque dur dedans / matting dans la bande » ;
- estimation de l'avant-plan sans franges (Blur-Fusion, Forte et Pitié 2021, réécriture ici d'après l'article) ;
- stabilisation temporelle de l'alpha guidée par le flux optique (DIS d'OpenCV) avec garde de cohérence de couleur ;
- composition sur un fond ; mesure du scintillement.

Aucun code d'un projet tiers n'est repris : tout est écrit pour Nexora, testé dans tests/test_noyau.py.
"""
from __future__ import annotations

import numpy as np

try:  # OpenCV n'est requis que pour le flux optique et les morphologies rapides
    import cv2
except Exception:  # pragma: no cover - testé par l'absence dans l'environnement minimal
    cv2 = None


# ---------------------------------------------------------------- segments

def plan_segments(n: int, taille: int, recouvrement: int) -> list[dict]:
    """Découpe n images en segments de `taille` images qui se recouvrent de `recouvrement` images.

    Chaque segment : {'debut', 'fin' (exclu)}. Le dernier segment est prolongé pour ne jamais être plus court que
    le recouvrement (un segment trop court ne porte aucune image « propre »).
    """
    if n <= 0:
        return []
    taille = max(2, int(taille))
    recouvrement = max(0, min(int(recouvrement), taille - 1))
    if n <= taille:
        return [{'debut': 0, 'fin': n}]
    pas = taille - recouvrement
    segs: list[dict] = []
    debut = 0
    while True:
        fin = min(n, debut + taille)
        segs.append({'debut': debut, 'fin': fin})
        if fin >= n:
            break
        debut += pas
    if len(segs) > 1 and (segs[-1]['fin'] - segs[-1]['debut']) <= recouvrement:
        # le dernier segment n'aurait que des images de recouvrement : on le fusionne avec le précédent
        segs[-2]['fin'] = n
        segs.pop()
    return segs


def plan_plans(n: int, coupures: list[int], taille: int, recouvrement: int) -> list[dict]:
    """Segments par plan : une coupure (première image du nouveau plan) interdit tout recouvrement.

    Chaque segment porte `debut`, `fin` (exclu) et `plan` (numéro du plan). Dans un plan, mêmes règles que `plan_segments`.
    """
    bornes = [0] + sorted({c for c in coupures if 0 < c < n}) + [n]
    segs: list[dict] = []
    for k in range(len(bornes) - 1):
        for s in plan_segments(bornes[k + 1] - bornes[k], taille, recouvrement):
            segs.append({'debut': bornes[k] + s['debut'], 'fin': bornes[k] + s['fin'], 'plan': k})
    return segs


def poids_segment(f: int, i: int, segs: list[dict], recouvrement: int) -> float:
    """Poids de l'image f dans le segment i : rampe linéaire dans les recouvrements, 1 ailleurs.

    Dans un recouvrement entre deux segments voisins, les deux poids somment à 1 (vérifié par les tests).
    """
    s = segs[i]
    if not (s['debut'] <= f < s['fin']):
        return 0.0
    w = 1.0
    if i > 0:
        r = segs[i - 1]['fin'] - s['debut']  # recouvrement réel avec le précédent
        if r > 0 and f < s['debut'] + r:
            w = min(w, (f - s['debut'] + 1) / (r + 1))
    if i < len(segs) - 1:
        r = s['fin'] - segs[i + 1]['debut']
        if r > 0 and f >= segs[i + 1]['debut']:
            w = min(w, (s['fin'] - f) / (r + 1))
    return w


def raccorder(masques_par_segment: list[tuple[int, np.ndarray]], segs: list[dict], n: int, recouvrement: int) -> np.ndarray:
    """Assemble les masques doux (float32 H×W) de chaque segment en une séquence unique de n images.

    `masques_par_segment[i] = (debut_i, tableau T×H×W)`. Dans les recouvrements, moyenne pondérée par les rampes.
    """
    h, w = masques_par_segment[0][1].shape[1:]
    somme = np.zeros((n, h, w), np.float32)
    poids = np.zeros(n, np.float32)
    for i, (debut, arr) in enumerate(masques_par_segment):
        for k in range(arr.shape[0]):
            f = debut + k
            p = poids_segment(f, i, segs, recouvrement)
            if p > 0:
                somme[f] += arr[k] * p
                poids[f] += p
    poids[poids == 0] = 1.0
    return somme / poids[:, None, None]


# ---------------------------------------------------------------- bord et matting

def largeur_bande(h: int, w: int, fraction: float = 0.012, minimum: int = 6) -> int:
    return max(minimum, int(round(min(h, w) * fraction)))


def _noyau(r: int) -> np.ndarray:
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def trimap(masque: np.ndarray, bande_int: int, bande_ext: int) -> np.ndarray:
    """Trimap uint8 (0 fond sûr, 128 inconnu, 255 avant-plan sûr) autour du bord d'un masque binaire/doux H×W.

    Le sujet sûr est le masque érodé de `bande_int`, le fond sûr est le complément du masque dilaté de `bande_ext`.
    """
    m = (masque >= 0.5).astype(np.uint8)
    sur_fg = cv2.erode(m, _noyau(bande_int)) if bande_int > 0 else m
    pas_fond = cv2.dilate(m, _noyau(bande_ext)) if bande_ext > 0 else m
    t = np.zeros(m.shape, np.uint8)
    t[pas_fond > 0] = 128
    t[sur_fg > 0] = 255
    return t


def fusionner(masque: np.ndarray, matting: np.ndarray, tri: np.ndarray) -> np.ndarray:
    """Alpha final float32 : 1 dans l'avant-plan sûr, 0 dans le fond sûr, valeur du matting dans la bande inconnue."""
    a = matting.astype(np.float32).copy()
    a[tri == 255] = 1.0
    a[tri == 0] = 0.0
    return np.clip(a, 0.0, 1.0)


def boite(masque: np.ndarray, marge: int = 0, seuil: float = 0.02) -> tuple[int, int, int, int] | None:
    """Boîte englobante (x0, y0, x1, y1) du masque (exclu), élargie de `marge`, ou None si vide."""
    ys, xs = np.nonzero(masque > seuil)
    if len(xs) == 0:
        return None
    h, w = masque.shape
    return (max(0, int(xs.min()) - marge), max(0, int(ys.min()) - marge),
            min(w, int(xs.max()) + 1 + marge), min(h, int(ys.max()) + 1 + marge))


# ---------------------------------------------------------------- avant-plan sans franges

def _flou(x: np.ndarray, r: int) -> np.ndarray:
    return cv2.blur(x, (r, r)).reshape(x.shape)  # cv2 retire l'axe des canaux quand il vaut 1


def _blur_fusion(image, F, B, alpha, r):
    a_flou = _flou(alpha, r)
    fa = _flou(F * alpha, r) / (a_flou + 1e-5)
    b1 = _flou(B * (1 - alpha), r) / ((1 - a_flou) + 1e-5)
    F2 = fa + alpha * (image - alpha * fa - (1 - alpha) * b1)
    return np.clip(F2, 0, 1), b1


def avant_plan(rgb: np.ndarray, alpha: np.ndarray, r_large: int = 45, r_fin: int = 6) -> np.ndarray:
    """Couleur d'avant-plan float32 H×W×3 (0..1, non prémultipliée) estimée sous la bande semi-transparente.

    Évite le liseré de fond qui reste dans les pixels de bord quand on compose avec un autre fond.
    """
    img = rgb.astype(np.float32) / (255.0 if rgb.dtype == np.uint8 else 1.0)
    a = alpha.astype(np.float32)[..., None]
    F, b = _blur_fusion(img, img, img, a, r_large)
    F, _ = _blur_fusion(img, F, b, a, r_fin)
    return F


# ---------------------------------------------------------------- flux optique et stabilisation

_dis = None


def _flux(g0: np.ndarray, g1: np.ndarray) -> np.ndarray:
    """Flux optique dense g0 -> g1 (gris uint8). DIS, préréglage moyen."""
    global _dis
    if _dis is None:
        _dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    return _dis.calc(g0, g1, None)


def _warp(img: np.ndarray, flux: np.ndarray) -> np.ndarray:
    """Ramène `img` (image t+d) sur la grille de l'image t, flux t -> t+d."""
    h, w = flux.shape[:2]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(img, gx + flux[..., 0], gy + flux[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def _gris(rgb_u8: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2GRAY)


def lisser_trame(a: np.ndarray, rgb: np.ndarray, voisines: list[tuple[np.ndarray, np.ndarray]], force: float = 1.0,
                 sigma_couleur: float = 14.0, rayon_bord: int = 8) -> np.ndarray:
    """Stabilise l'alpha d'UNE image sur sa bande de bord (le cœur et le fond ne bougent pas).

    Chaque voisine (alpha, rgb uint8) est ramenée sur l'image courante par le flux optique ; elle ne compte que là où
    la couleur recalée colle à l'image courante (écart ≲ sigma_couleur niveaux sur 255) : les mouvements rapides et les
    occlusions sont ainsi protégés. Moyenne pondérée : (a + Σ w·a_voisine) / (1 + Σ w).
    """
    if not voisines or force <= 0:
        return a.copy()
    bord = ((a > 0.003) & (a < 0.997)).astype(np.uint8)
    if not bord.any():
        return a.copy()
    zone = cv2.dilate(bord, _noyau(rayon_bord)).astype(bool)
    g = _gris(rgb)
    num, den = a.copy(), np.ones_like(a)
    for a_u, rgb_u in voisines:
        fl = _flux(g, _gris(rgb_u))
        a_w = _warp(a_u, fl)
        c_w = _warp(rgb_u.astype(np.float32), fl)
        ecart = np.abs(c_w - rgb.astype(np.float32)).mean(axis=2)
        w = np.exp(-(ecart / sigma_couleur) ** 2) * force
        num += w * a_w
        den += w
    res = a.copy()
    res[zone] = (num / den)[zone]
    return np.clip(res, 0, 1)


def lisser_temporel(alphas: list[np.ndarray], rgbs: list[np.ndarray], force: float = 1.0, sigma_couleur: float = 14.0,
                    rayon_bord: int = 8) -> list[np.ndarray]:
    """`lisser_trame` sur toute une séquence (voisines t-1 et t+1). `alphas` float32 0..1 ; `rgbs` uint8 H×W×3."""
    n = len(alphas)
    if n < 3 or force <= 0:
        return [a.copy() for a in alphas]
    return [lisser_trame(alphas[t], rgbs[t], [(alphas[u], rgbs[u]) for u in (t - 1, t + 1) if 0 <= u < n], force,
                         sigma_couleur, rayon_bord) for t in range(n)]


def ecart_temporel(a: np.ndarray, rgb: np.ndarray, a_prec: np.ndarray, rgb_prec: np.ndarray) -> float | None:
    """Écart moyen |a − recalage(a_prec)| sur la bande de bord (None si aucun bord). Brique de `scintillement`."""
    bord = (a > 0.003) & (a < 0.997)
    if not bord.any():
        return None
    zone = cv2.dilate(bord.astype(np.uint8), _noyau(4)).astype(bool)
    fl = _flux(_gris(rgb), _gris(rgb_prec))
    return float(np.abs(a - _warp(a_prec, fl))[zone].mean())


def scintillement(alphas: list[np.ndarray], rgbs: list[np.ndarray]) -> float:
    """Scintillement des bords : moyenne des `ecart_temporel` (0..1). Plus bas = plus stable ; le recalage par flux
    retire le mouvement réel, ce qui reste est du bruit temporel."""
    v = [ecart_temporel(alphas[t], rgbs[t], alphas[t - 1], rgbs[t - 1]) for t in range(1, len(alphas))]
    v = [x for x in v if x is not None]
    return sum(v) / len(v) if v else 0.0


# ---------------------------------------------------------------- composition

def composer(fg: np.ndarray, alpha: np.ndarray, fond: np.ndarray) -> np.ndarray:
    """over : fg×α + fond×(1−α), tout en float32 0..1 (fg non prémultiplié)."""
    a = alpha[..., None] if alpha.ndim == 2 else alpha
    return fg * a + fond * (1.0 - a)


def srgb_vers_lineaire(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def echecs(h: int, w: int, case: int = 16) -> np.ndarray:
    """Damier gris (float32 H×W×3) pour l'aperçu de la transparence."""
    yy, xx = np.indices((h, w))
    v = np.where(((xx // case) + (yy // case)) % 2 == 0, 0.43, 0.60).astype(np.float32)
    return np.repeat(v[..., None], 3, axis=2)
