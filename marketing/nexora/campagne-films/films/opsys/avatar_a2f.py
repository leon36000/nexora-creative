"""Avatar d'OPSYS-AI animé par NVIDIA Audio2Face-3D (modèle ouvert v2.3.1-Claire, licence NVIDIA Open Model License).

Chaîne réelle : voix (wav) -> réseau Audio2Face-3D (ONNX, onnxruntime) -> 140 coefficients de peau + mâchoire + yeux par image
-> géométrie du visage (61 520 sommets) -> rendu « Signal » (nuage de points éclairé, encre et bleu ion) en numpy.
Le rendu est le nôtre ; l'animation du visage (lèvres, mâchoire, joues, sourcils, clignements) vient du modèle NVIDIA.

Usage : python avatar_a2f.py animer <voix.wav> <sortie.npz>      (coefficients par image, 24 i/s)
        python avatar_a2f.py rendre <anim.npz> <dossier_images> [--l 1080 --h 1080 --cam ...]
Données du modèle : ~/nexora-creative-data/promo/v6/opsys/a2f (téléchargées depuis huggingface.co/nvidia, non versionnées).
"""
import argparse
import json
from pathlib import Path

import numpy as np

A2F = Path.home() / "nexora-creative-data/promo/v6/opsys/a2f"
IPS = 24
SR = 16000
FEN, OFS = 8320, 4160


def charger_wav(p):
    import soundfile as sf
    x, sr = sf.read(str(p), dtype="float32", always_2d=True)
    x = x.mean(1)
    if sr != SR:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(sr, SR)
        x = resample_poly(x, SR // g, sr // g).astype(np.float32)
    return x


def emotion(joie=0.15, etonnement=0.0):
    e = np.load(A2F / "implicit_emo_db.npz")
    noms = [n.decode() for n in e["emo_spec_names"]]
    cfg = json.loads((A2F / "model_config.json").read_text())["config"]
    i = noms.index(cfg["source_shot"])
    imp = e["emo_db"][e["emo_spec_start"][i] + cfg["source_frame"]]
    exp = np.zeros(10, np.float32)
    exp[6] = joie          # joy
    exp[0] = etonnement    # amazement
    return np.concatenate([imp, exp]).astype(np.float32)[None, None]


def animer(wav, sortie, joie=0.15):
    import onnxruntime as ort
    s = ort.InferenceSession(str(A2F / "network.onnx"), providers=["CPUExecutionProvider"])
    x = charger_wav(wav)
    n = int(np.ceil(len(x) / SR * IPS))
    pad = np.concatenate([np.zeros(OFS, np.float32), x, np.zeros(FEN, np.float32)])
    em = emotion(joie)
    fen = np.stack([pad[int(round(k / IPS * SR)):int(round(k / IPS * SR)) + FEN] for k in range(n)])[:, None, :]
    res = []
    for b in range(0, n, 32):
        lot = fen[b:b + 32].astype(np.float32)
        res.append(s.run(None, {"input": lot, "emotion": np.repeat(em, len(lot), 0)})[0][:, 0])
    r = np.concatenate(res)
    # lissage temporel léger (équivalent du lissage bas du visage du SDK)
    k = np.array([0.25, 0.5, 0.25], np.float32)
    rl = r.copy()
    rl[1:-1] = k[0] * r[:-2] + k[1] * r[1:-1] + k[2] * r[2:]
    np.savez_compressed(sortie, skin=rl[:, :140], tongue=rl[:, 140:150], jaw=rl[:, 150:165], eyes=rl[:, 165:169],
                        ips=IPS, duree=len(x) / SR)
    print(f"{n} images, {len(x) / SR:.2f} s -> {sortie}")


class Visage:
    def __init__(self):
        d = np.load(A2F / "model_data.npz")
        self.moy = d["shapes_mean_skin"]
        self.M = d["shapes_matrix_skin"].reshape(140, -1)
        self.cligne = d["eye_close_pose_delta"]
        b = np.load(A2F / "bs_skin.npz")
        self.neutre = b["neutral"]
        c = self.neutre.mean(0)
        self.centre = c
        from scipy.spatial import cKDTree
        t = cKDTree(self.neutre)
        _, idx = t.query(self.neutre, k=12)
        P = self.neutre[idx] - self.neutre[idx].mean(1, keepdims=True)
        _, _, vt = np.linalg.svd(P, full_matrices=False)
        n = vt[:, 2, :]
        axe = self.neutre - np.array([c[0], 0, c[2] - 5.0], np.float32)
        axe[:, 1] = (self.neutre[:, 1] - c[1]) * 0.35
        n *= np.sign((axe * n).sum(1, keepdims=True) + 1e-9)
        self.normales = n.astype(np.float32)
        dd, _ = t.query(self.neutre, k=6)
        self.espacement = dd[:, 5].astype(np.float32)
        # orbites : centre des déplacements du clignement
        bl, br = b["eyeBlinkLeft"], b["eyeBlinkRight"]
        self.yeux = []
        for dlt in (bl, br):
            w = np.linalg.norm(dlt, axis=1)
            sel = w > w.max() * 0.3
            self.yeux.append((self.neutre[sel] * w[sel, None]).sum(0) / w[sel].sum())
        self.rayon_oeil = 0.43 * np.linalg.norm(self.yeux[0] - self.yeux[1]) / 2.2

    def geometrie(self, coef):
        return (self.moy.reshape(-1) + coef @ self.M).reshape(-1, 3)


ION = np.array([0.36, 0.70, 1.0], np.float32)     # bleu ion
CHAUD = np.array([1.0, 0.36, 0.12], np.float32)   # point chaud (signal)


def rot(yaw, pitch, roll=0.0):
    cy, sy, cp, sp, cr, sr = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch), np.cos(roll), np.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], np.float32)
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]], np.float32)
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]], np.float32)
    return Ry @ Rx @ Rz


def sphere(n=2600):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi) * 0 + np.sin(th) * np.sin(phi), np.cos(phi)], 1).astype(np.float32)


def rendre_image(v, P, yeux_rot, W, H, yaw=0.0, pitch=0.0, roll=0.0, dist=46.0, focale=1.9, dx=0.0, dy=0.0,
                 ss=2, lueur=0.6, intensite=1.0):
    """P : sommets (N,3). Renvoie une image float RGB (H,W,3) dans [0,1+]."""
    R = rot(yaw, pitch, roll)
    c = v.centre + np.array([0, 1.5, 0], np.float32)
    pts = [(P - c) @ R.T]
    nrm = [v.normales @ R.T]
    typ = [np.zeros(len(P), np.int8)]
    esp = [v.espacement]
    sp = sphere()
    for k, o in enumerate(v.yeux):
        ry = rot(float(yeux_rot[2 * k + 1]) * 0.6, float(yeux_rot[2 * k]) * 0.6)
        s = (sp @ ry.T)
        pts.append(((o - c) + s * v.rayon_oeil - np.array([0, 0, v.rayon_oeil * 0.95], np.float32)) @ R.T)
        nrm.append(s @ R.T)
        iris = np.where(s[:, 2] > 0.90, 2, 1).astype(np.int8)
        iris[s[:, 2] > 0.965] = 4
        iris[(s[:, 2] > 0.93) & (s[:, 0] < -0.10) & (s[:, 1] > 0.10) & (s[:, 1] < 0.22)] = 3
        typ.append(iris)
        esp.append(np.full(len(sp), v.rayon_oeil * 0.09, np.float32))
    X = np.concatenate(pts); N = np.concatenate(nrm); T = np.concatenate(typ); E = np.concatenate(esp)
    Ws, Hs = W * ss, H * ss
    z = dist - X[:, 2]
    f = focale * Hs / 2
    px = (X[:, 0] / z * f + Ws / 2 + dx * Ws).astype(np.int32)
    py = (-X[:, 1] / z * f + Hs / 2 + dy * Hs).astype(np.int32)
    vue = -np.stack([X[:, 0], X[:, 1], X[:, 2] - dist], 1)
    vue /= np.linalg.norm(vue, axis=1, keepdims=True)
    ndv = (N * vue).sum(1)
    ok = (X[:, 1] > -13.0) & (ndv > -0.05) & (px > 2) & (px < Ws - 3) & (py > 2) & (py < Hs - 3)
    cle = np.array([-0.55, 0.45, 0.70], np.float32); cle /= np.linalg.norm(cle)
    bord = np.array([0.85, 0.15, -0.35], np.float32); bord /= np.linalg.norm(bord)
    lam = np.clip(N @ cle, 0, 1)
    rim = np.clip(N @ bord, 0, 1) ** 1.5 + np.clip(1 - np.abs(ndv), 0, 1) ** 3 * 0.9
    col = (0.10 + 0.85 * lam)[:, None] * np.array([0.78, 0.84, 0.92], np.float32) * 0.62 + rim[:, None] * ION * 1.15
    col[T == 1] = (0.25 + 0.6 * lam[T == 1])[:, None] * np.array([0.85, 0.88, 0.95], np.float32)
    col[T == 2] = ION * (0.6 + 0.5 * lam[T == 2])[:, None]
    col[T == 3] = CHAUD * 1.2
    from scipy.ndimage import grey_closing, gaussian_filter
    px, py, zz, T, Y = px[ok], py[ok], z[ok], T[ok], X[ok][:, 1]
    rpx = np.clip(np.round(E[ok] * f / zz * 0.72), 1, 16).astype(np.int32)
    zb = np.full((Hs, Ws), np.inf, np.float32)
    tb = np.zeros((Hs, Ws), np.int8)
    yb = np.zeros((Hs, Ws), np.float32)
    o = np.argsort(-zz)
    for rad in np.unique(rpx):
        sel = rpx == rad
        so = sel[o]
        oo = o[so]
        for a in range(-rad, rad + 1):
            for b in range(-rad, rad + 1):
                if a * a + b * b > rad * rad + 1:
                    continue
                yy = np.clip(py[sel] + a, 0, Hs - 1); xx = np.clip(px[sel] + b, 0, Ws - 1)
                np.minimum.at(zb, (yy, xx), zz[sel])
    # type (peau / oeil / iris) et hauteur : pris au plus proche (comparaison au tampon de profondeur)
    for rad in np.unique(rpx):
        sel = np.where(rpx == rad)[0]
        for a in range(-rad, rad + 1):
            for b in range(-rad, rad + 1):
                if a * a + b * b > rad * rad + 1:
                    continue
                yy = np.clip(py[sel] + a, 0, Hs - 1); xx = np.clip(px[sel] + b, 0, Ws - 1)
                gagne = zz[sel] <= zb[yy, xx] + 1e-4
                tb[yy[gagne], xx[gagne]] = T[sel][gagne]
                yb[yy[gagne], xx[gagne]] = Y[sel][gagne]
    pts_img = np.zeros((Hs, Ws), np.float32)
    pts_img[py, px] = 1.0
    masque = np.isfinite(zb)
    zf = np.where(masque, zb, 0)
    zf = grey_closing(zf, size=(3, 3))
    masque = zf > 0
    zs = gaussian_filter(np.where(masque, zf, zf[masque].max() if masque.any() else 0), sigma=1.2 * ss)
    gy, gx = np.gradient(zs)
    k = f / dist  # pixels par unité de profondeur
    nx, ny, nz = gx * k, -gy * k, -np.ones_like(gx)
    nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    Nn = np.stack([nx / nn, ny / nn, -nz / nn], -1)  # vers la caméra : +z
    cle = np.array([-0.55, 0.45, 0.70], np.float32); cle /= np.linalg.norm(cle)
    bord = np.array([0.9, 0.25, -0.2], np.float32); bord /= np.linalg.norm(bord)
    lam = np.clip(Nn @ cle, 0, 1)
    fres = np.clip(1 - Nn[..., 2], 0, 1) ** 2.2
    rim = np.clip(Nn @ bord, 0, 1) ** 2 + fres * 0.8
    base = np.array([0.80, 0.85, 0.93], np.float32)
    trame = 0.55 + 0.45 * gaussian_filter(pts_img, 0.6 * ss) / max(1e-6, gaussian_filter(pts_img, 0.6 * ss).max())
    spec = np.clip(Nn @ ((cle + np.array([0, 0, 1], np.float32)) / np.linalg.norm(cle + np.array([0, 0, 1], np.float32))), 0, 1) ** 24
    img = ((0.025 + 0.55 * lam ** 1.3)[..., None] * base * trame[..., None] + rim[..., None] * ION * 1.25
           + spec[..., None] * np.array([0.55, 0.75, 1.0], np.float32) * 0.35)
    img[tb == 1] *= 0.55
    img[tb == 2] = (ION * (0.30 + 0.45 * lam[tb == 2])[:, None])
    img[tb == 4] = 0.02
    img[tb == 3] = CHAUD * 1.3
    # fondu du cou et des épaules
    fondu = np.clip((yb + 11.5) / 4.0, 0, 1) ** 1.8
    img *= (masque * fondu)[..., None]
    if ss > 1:
        img = img.reshape(H, ss, W, ss, 3).mean((1, 3))
    if lueur > 0:
        from scipy.ndimage import gaussian_filter
        g = gaussian_filter(img, sigma=(H / 90, H / 90, 0))
        img = img + lueur * g
    return img * intensite


# ---------------------------------------------------------------- voix, plans de l'avatar
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
REPLIQUES = {
    "a": {"fr": "Bonjour Marc. Cette nuit, j'ai qualifié douze demandes et préparé trois soumissions. Elles n'attendent que ta signature.",
          "en": "Morning, Marc. Overnight, I qualified twelve requests and drafted three quotes. They just need your signature."},
    "a15": {"fr": "Trois soumissions sont prêtes. Il ne manque que ta signature.",
            "en": "Three quotes are ready. They just need your signature."},
    "b": {"fr": "Oui, si tu attends mars. Le dossier est prêt pour ton comptable. Tu approuves ?",
          "en": "Yes, if you wait until March. The file is ready for your accountant. Approve?"},
}
VOIX = {"fr": ("f", "ff_siwis", 1.0), "en": ("a", "af_heart", 1.0)}
AVANT = 0.6  # silence avant la voix (apparition du visage)


def dire(cle, l, sortie):
    """Voix synthétique Kokoro-82M (Apache-2.0), 24 kHz, précédée de AVANT s de silence et suivie de 0,5 s."""
    import soundfile as sf
    from kokoro import KPipeline
    lang, voix, vit = VOIX[l]
    p = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
    a = np.concatenate([np.asarray(x[2]) for x in p(REPLIQUES[cle][l], voice=voix, speed=vit)]).astype(np.float32)
    a = a / max(1e-6, np.abs(a).max()) * 0.9
    a = np.concatenate([np.zeros(int(AVANT * 24000), np.float32), a, np.zeros(12000, np.float32)])
    sf.write(sortie, a, 24000)
    return len(a) / 24000


_V = None


def _image(args):
    k, P, yeux, cam, W, H, n, energie, fichier = args
    global _V
    if _V is None:
        _V = Visage()
    t = k / IPS
    # mouvement de tête procédural (A2F 2.3 ne donne pas la tête) : lent balancement + hochement suivant l'énergie de la voix
    u = min(1.0, t / max(1e-3, n / IPS))
    yaw = cam["yaw"] - cam.get("orbite", 0.0) * (0.5 - (3 * u * u - 2 * u ** 3)) + 0.04 * np.sin(t * 0.7) + 0.015 * np.sin(t * 1.9)
    pitch = cam["pitch"] + 0.025 * np.sin(t * 0.9 + 1) - 0.035 * energie
    roll = 0.015 * np.sin(t * 0.6 + 2)
    dist = cam["dist"] - cam.get("poussee", 0.0) * min(1.0, t / max(1e-3, n / IPS))
    im = rendre_image(_V, P, yeux, W, H, yaw=yaw, pitch=pitch, roll=roll, dist=dist, dx=cam["dx"], dy=cam["dy"], ss=2)
    # apparition : balayage de bas en haut pendant AVANT s, ligne de lumière au front du balayage
    a = min(1.0, t / AVANT)
    if a < 1.0:
        yy = np.linspace(1, 0, H)[:, None]
        front = a * 1.25
        m = np.clip((front - yy) / 0.08, 0, 1)
        ligne = np.exp(-((yy - front) / 0.012) ** 2) * (im.sum(-1, keepdims=False) > 0.02)
        im = im * m[..., None] + ligne[..., None] * ION * 1.6
    # halo d'ambiance derrière la tête
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W * (0.5 + cam["dx"]), H * (0.44 + cam["dy"])
    r = np.sqrt(((xx - cx) / (0.55 * H)) ** 2 + ((yy - cy) / (0.55 * H)) ** 2)
    halo = np.exp(-r ** 2 * 1.6)[..., None] * np.array([0.02, 0.05, 0.10], np.float32)
    im = im + halo
    from PIL import Image
    Image.fromarray((np.clip(im, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)).save(fichier)
    return k


CAMS = {
    "16x9": {"W": 1920, "H": 1080, "yaw": -0.22, "pitch": 0.05, "dist": 37.0, "dx": 0.17, "dy": 0.07, "poussee": 4.0, "orbite": 0.22},
    "9x16": {"W": 1080, "H": 1920, "yaw": -0.12, "pitch": 0.05, "dist": 46.0, "dx": 0.0, "dy": -0.04, "poussee": 5.0, "orbite": 0.16},
}


def plan(cle, l, fmt, dossier, procs=10):
    """Voix -> Audio2Face-3D -> images -> mp4 (voix incluse : le monteur la lit comme son natif du plan, « son_h3 »)."""
    from multiprocessing import Pool
    import subprocess
    import tempfile
    dossier = Path(dossier); dossier.mkdir(parents=True, exist_ok=True)
    wav = dossier / f"voix-{cle}-{l}.wav"
    if not wav.exists():
        dire(cle, l, wav)
    anim = dossier / f"anim-{cle}-{l}.npz"
    if not anim.exists():
        animer(wav, anim, joie=0.4)
    d = np.load(anim)
    v = Visage()
    n = len(d["skin"])
    import soundfile as sf
    x, sr = sf.read(str(wav), dtype="float32")
    env = np.array([np.sqrt(np.mean(x[int(k / IPS * sr):int((k + 1) / IPS * sr)] ** 2) + 1e-9) for k in range(n)])
    env = np.convolve(env / max(1e-6, env.max()), np.ones(5) / 5, "same")
    cam = CAMS[fmt]
    sortie = dossier / f"avatar-{cle}-{l}-{fmt}.mp4"
    with tempfile.TemporaryDirectory(dir=dossier) as tmp:
        taches = []
        for k in range(n):
            P = v.moy + (v.geometrie(d["skin"][k]) - v.moy) * 1.15   # force du bas du visage (SDK : lower_face_strength 1,25)
            taches.append((k, P, d["eyes"][k], cam, cam["W"], cam["H"], n, float(env[k]), f"{tmp}/{k:05d}.png"))
        with Pool(procs) as pool:
            for _ in pool.imap_unordered(_image, taches, chunksize=4):
                pass
        subprocess.run([FF, "-v", "error", "-y", "-framerate", str(IPS), "-i", f"{tmp}/%05d.png", "-i", str(wav),
                        "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        str(sortie)], check=True)
    print(sortie, f"{n / IPS:.2f} s")
    return sortie


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--joie", type=float, default=0.15)
    a = ap.parse_args()
    if a.cmd == "animer":
        animer(a.a, a.b, a.joie)
    elif a.cmd == "plan":          # python avatar_a2f.py plan a:fr 16x9
        cle, l = a.a.split(":")
        plan(cle, l, a.b, Path.home() / "nexora-creative-data/promo/v6/opsys/avatar")
