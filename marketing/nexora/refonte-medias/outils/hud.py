"""Detection overlay set in code on a fixed-camera shot (surveillance film): the moving subject is found by background
subtraction (median of the frames), framed by "Signal" detection brackets (ion), labelled in JetBrains Mono, then
switched to alert (red) from --alerte seconds. A scan line sweeps the image when the overlay appears; a discreet HUD
in the corner (camera, live). Labels in fr or en: the text is set in code, never by the model.

  python3 hud.py in.mp4 out.mp4 --lang fr [--debut 0.6] [--alerte 2.5] [--camera "CAM 04"] [--seuil 28]
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ICI = Path(__file__).resolve().parent
MARQUE = json.loads((ICI.parent / "marque.json").read_text())
POL = Path(MARQUE["polices"]["dossier"]).expanduser()
FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
FFPROBE = str(Path(FFMPEG).with_name("ffprobe"))
H = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
ION, ALERTE, TEXTE = H(MARQUE["couleurs"]["ion"]), H(MARQUE["couleurs"]["alerte"]), H(MARQUE["couleurs"]["texte"])
LIB = {
    "fr": {"sujet": "PERSONNE", "alerte": "COMPORTEMENT SUSPECT", "direct": "EN DIRECT", "analyse": "ANALYSE IA"},
    "en": {"sujet": "PERSON", "alerte": "SUSPICIOUS BEHAVIOUR", "direct": "LIVE", "analyse": "AI ANALYSIS"},
}


def lire(f):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-of", "json", str(f)], capture_output=True, text=True)
    s = json.loads(r.stdout)["streams"][0]
    W, Hh = s["width"], s["height"]
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(f), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, Hh, W, 3), W, Hh


def boites(frames, seuil, bloc=16):
    """Bounding box of the moving subject per frame (None if nothing moves), smoothed."""
    n, Hh, W, _ = frames.shape
    pet = frames[:, ::4, ::4].astype(np.int16)
    fond = np.median(pet[:: max(1, n // 40)], axis=0)
    sortie, prec = [], None
    b4 = bloc // 4
    for k in range(n):
        d = np.abs(pet[k] - fond).sum(axis=2) > seuil
        h4, w4 = d.shape[0] // b4 * b4, d.shape[1] // b4 * b4
        bl = d[:h4, :w4].reshape(h4 // b4, b4, w4 // b4, b4).mean(axis=(1, 3)) > 0.25
        # keep the blocks that have neighbours (removes noise)
        voisin = np.zeros_like(bl, dtype=int)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    voisin += np.roll(np.roll(bl, dy, 0), dx, 1)
        bl = bl & (voisin >= 2)
        ys, xs = np.nonzero(bl)
        if len(ys) < 3:
            sortie.append(prec); continue
        # largest group: blocks close to the median
        my, mx = np.median(ys), np.median(xs)
        garde = (np.abs(ys - my) < 14) & (np.abs(xs - mx) < 10)
        ys, xs = ys[garde], xs[garde]
        if not len(ys):
            sortie.append(prec); continue
        b = np.array([xs.min() * bloc, ys.min() * bloc, (xs.max() + 1) * bloc, (ys.max() + 1) * bloc], float)
        prec = b if prec is None else prec * 0.7 + b * 0.3
        sortie.append(prec.copy())
    return sortie


def suivre(frames, cible, rayon=20):
    """Tracks the box `cible` (x0,y0,x1,y1 at frame 0) by template matching (SSD on luminance), template refreshed slowly."""
    from numpy.lib.stride_tricks import sliding_window_view
    g = frames.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    x0, y0, x1, y1 = map(int, cible)
    w, h = x1 - x0, y1 - y0
    modele = g[0, y0:y1, x0:x1].copy()
    sortie, x, y = [], x0, y0
    H_, W_ = g.shape[1:]
    for k in range(len(g)):
        if k:
            ya, yb = max(0, y - rayon), min(H_ - h, y + rayon)
            xa, xb = max(0, x - rayon), min(W_ - w, x + rayon)
            zone = g[k, ya:yb + h, xa:xb + w]
            fen = sliding_window_view(zone, (h, w))[::2, ::2]
            ssd = ((fen - modele) ** 2).mean(axis=(2, 3))
            iy, ix = np.unravel_index(np.argmin(ssd), ssd.shape)
            y, x = ya + iy * 2, xa + ix * 2
            modele = modele * 0.75 + g[k, y:y + h, x:x + w] * 0.25
        sortie.append(np.array([x, y, x + w, y + h], float))
    # temporal smoothing
    lis = [sortie[0]]
    for b in sortie[1:]:
        lis.append(lis[-1] * 0.35 + b * 0.65)
    return lis


def interpoler(cles, n):
    """Art-directed boxes: keyframes [(t, x0, y0, x1, y1)] set by eye on the frames, eased linear interpolation."""
    cles = sorted(cles)
    out = []
    for k in range(n):
        t = k / 24
        a = max([c for c in cles if c[0] <= t], default=cles[0])
        b = min([c for c in cles if c[0] >= t], default=cles[-1])
        u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
        u = u * u * (3 - 2 * u)
        out.append(np.array([a[i] + (b[i] - a[i]) * u for i in range(1, 5)], float))
    return out


def rendre(src, sortie, lang="fr", debut=0.6, alerte=2.5, camera="CAM 04", seuil=28, cible=None, cles=None, recadre=None):
    frames, W, Hh = lire(src)
    if recadre is not None:
        # vertical version cut from the horizontal shot (CCTV footage: the lower definition stays credible)
        w = round(Hh * 9 / 16) // 2 * 2
        x0 = int(max(0, min(W - w, recadre)))
        frames = np.ascontiguousarray(frames[:, :, x0:x0 + w])
        W = w
        if cible:
            cible = [cible[0] - x0, cible[1], cible[2] - x0, cible[3]]
        if cles:
            cles = [(c[0], c[1] - x0, c[2], c[3] - x0, c[4]) for c in cles]
    bx = interpoler(cles, len(frames)) if cles else (suivre(frames, cible) if cible else boites(frames, seuil))
    m = min(W, Hh)
    f_lab = ImageFont.truetype(str(POL / MARQUE["polices"]["mono"]), max(11, round(m * 0.022)))
    f_lab.set_variation_by_name(b"Medium")
    L = LIB[lang]
    son = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(src)],
                         capture_output=True, text=True).stdout.strip()
    cmd = [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{Hh}", "-r", "24", "-i", "-"]
    if son:
        cmd += ["-i", str(src), "-map", "0:v", "-map", "1:a", "-c:a", "copy"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", str(sortie)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    e = max(2, round(m * 0.004))
    for k, fr in enumerate(frames):
        t = k / 24
        im = Image.fromarray(fr).convert("RGBA")
        cal = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(cal)
        # corner HUD
        a_h = min(1, max(0, (t - 0.1) / 0.4))
        if a_h > 0:
            pad = round(m * 0.045)
            pt = round(m * 0.011)
            clign = (int(t * 2) % 2 == 0)
            d.ellipse([pad, pad + pt * 0.4, pad + 2 * pt, pad + 2.4 * pt], fill=ALERTE + (int(230 * a_h * clign),))
            d.text((pad + 3 * pt, pad), f"{camera} · {L['direct']}", font=f_lab, fill=TEXTE + (int(220 * a_h),))
            tw = f_lab.getlength(L["analyse"])
            d.text((W - pad - tw, pad), L["analyse"], font=f_lab, fill=ION + (int(230 * a_h),))
        # scan line when the analysis starts
        bal = (t - debut) / 0.8
        if 0 <= bal <= 1:
            y = round(bal * Hh)
            for dy, a in ((0, 230), (1, 120), (-1, 120), (2, 50), (-2, 50)):
                d.line([(0, y + dy), (W, y + dy)], fill=ION + (a,))
            d.rectangle([0, 0, W, y], fill=ION + (14,))
        # detection box
        b = bx[k]
        if b is not None and t >= debut + 0.3:
            x0, y0, x1, y1 = b
            mx, my = (x1 - x0) * 0.15 + m * 0.008, (y1 - y0) * 0.06 + m * 0.008
            x0, y0, x1, y1 = x0 - mx, y0 - my, x1 + mx, y1 + my
            al = t >= alerte
            col = ALERTE if al else ION
            ap = min(1, (t - debut - 0.3) / 0.25)
            c = round(min(x1 - x0, y1 - y0) * 0.22)
            A = int(255 * ap)
            for (px, py, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                d.line([(px, py), (px + sx * c, py)], fill=col + (A,), width=e)
                d.line([(px, py), (px, py + sy * c)], fill=col + (A,), width=e)
            if al:
                pul = 0.5 + 0.5 * np.cos((t - alerte) * 2 * np.pi * 1.6)
                d.rectangle([x0, y0, x1, y1], outline=col + (int(90 * pul),), width=1)
                d.rectangle([x0, y0, x1, y1], fill=col + (int(22 * pul),))
            lab = L["alerte"] if al else L["sujet"]
            tw = f_lab.getlength(lab)
            hh = f_lab.size * 1.5
            ly = y0 - hh - e * 2 if y0 - hh - e * 2 > 0 else y1 + e * 2
            d.rectangle([x0, ly, x0 + tw + f_lab.size, ly + hh], fill=(5, 7, 11, int(190 * ap)))
            d.text((x0 + f_lab.size * 0.5, ly + hh * 0.18), lab, font=f_lab, fill=col + (A,))
        im.alpha_composite(cal)
        p.stdin.write(np.asarray(im.convert("RGB")).tobytes())
    p.stdin.close()
    if p.wait():
        raise SystemExit("ffmpeg a échoué")
    return sortie


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("src"); a.add_argument("sortie"); a.add_argument("--lang", default="fr")
    a.add_argument("--debut", type=float, default=0.6); a.add_argument("--alerte", type=float, default=2.5)
    a.add_argument("--camera", default="CAM 04"); a.add_argument("--seuil", type=int, default=28)
    a.add_argument("--recadre", type=float, help="x of the left edge of a 9:16 crop (vertical version)")
    a.add_argument("--cles", help="keyframes 't:x0,y0,x1,y1;t:...' (boxes set by eye), takes precedence over --cible")
    a.add_argument("--cible", help="x0,y0,x1,y1 of the subject at frame 0 (template tracking) instead of background subtraction")
    o = a.parse_args()
    cible = [float(v) for v in o.cible.split(",")] if o.cible else None
    cles = [tuple(float(v) for v in c.replace(":", ",").split(",")) for c in o.cles.split(";")] if o.cles else None
    print(rendre(o.src, o.sortie, o.lang, o.debut, o.alerte, o.camera, o.seuil, cible, cles, o.recadre))
