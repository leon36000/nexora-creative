"""Carton de marque Nexora AI : des braises (petits carrés lumineux) montent dans le noir, treize d'entre elles se rassemblent
en « N » (deux montants et une diagonale de trois carrés orange), le symbole se range à gauche et le logotype se révèle,
puis la signature. L'image finale est le logo officiel rastérisé (sources/logo/), pixel pour pixel : rien n'est redessiné.

Usage : python3 carton_nexora.py sortie.mp4 [--format 16:9|9:16|1:1] [--version marque|sting] [--lang fr|en] [--duree 8]
  marque : braises → N → logotype → signature (≈ 8 s) ; sting : braises → N → logotype (≈ 4,6 s, sans signature).
Polices : Geist, Inter, JetBrains Mono (SIL OFL), lues dans le dépôt du site (lecture seule). Aucun texte n'est dessiné par une IA.
"""
import argparse, math, random, subprocess
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
LOGO = ICI.parent / "sources" / "logo"
POLICES = Path.home() / "Desktop/NexoraSite/web/src/fonts"
FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")
IPS = 24
ENCRE, OS, BRUME, SIGNAL, ACCENT = (10, 10, 14), (245, 244, 239), (168, 168, 182), (255, 90, 31), (255, 122, 69)
BRAISE = [(255, 211, 122), (255, 177, 26), (255, 138, 31), (255, 90, 31), (224, 52, 28), (176, 26, 60)]
TAILLES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
TEXTES = {
    "fr": ("L’IA qui travaille pour votre entreprise.", "Sous votre contrôle.", "IA SOUVERAINE AU QUÉBEC"),
    "en": ("AI that works for your business.", "Under your control.", "SOVEREIGN AI, MADE IN QUÉBEC"),
}
SS = 2  # sur-échantillonnage


def police(nom, taille, graisse=b"Medium"):
    f = ImageFont.truetype(str(POLICES / nom), taille)
    f.set_variation_by_name(graisse)
    return f


def ease(t):  # cubique entrée-sortie
    t = max(0.0, min(1.0, t))
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def mix(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def cellules():
    """Les 13 cellules du symbole en unités de 10,4 sur 52 : (colonne, rangée, couleur) ; montants pleins et diagonale orange."""
    c = [(0, r, OS) for r in range(5)] + [(4, r, OS) for r in range(5)] + [(1, 1, SIGNAL), (2, 2, SIGNAL), (3, 3, SIGNAL)]
    return c


def rendre(format, version, lang, duree, sortie, facteur=1.0):
    W, H = TAILLES[format]
    n = round(duree * IPS)
    rnd = random.Random(7)
    cel = cellules()
    # Taille du symbole : grand au centre pendant le rassemblement, puis rangé dans le logotype.
    S_big = round(H * (0.40 if format == "16:9" else 0.26 if format == "9:16" else 0.36))
    lock = Image.open(LOGO / "logo-sombre-2400.png").convert("RGBA")
    LW = round(W * (0.46 if format == "16:9" else 0.80 if format == "9:16" else 0.70))
    LH = round(LW * lock.height / lock.width)
    lock = lock.resize((LW, LH), Image.LANCZOS)
    lx, ly = (W - LW) // 2, round(H * (0.40 if version == "marque" else 0.5)) - LH // 2
    S_small = LH  # le symbole du logotype a la hauteur du logotype
    sx_final = lx  # le symbole commence au bord gauche du logotype
    sy_final = ly
    # Cibles des cellules (grand symbole centré), puis petit symbole.
    gx0, gy0 = (W - S_big) // 2, round(H * (0.42 if version == "marque" else 0.5)) - S_big // 2
    u_big = S_big / 5
    # Braises : positions de départ (bas du cadre, dispersées), vitesse de montée, taille, teinte.
    braises = []
    for i in range(150):
        braises.append({
            "x": rnd.uniform(0.05, 0.95) * W, "y": rnd.uniform(0.55, 1.15) * H, "v": rnd.uniform(0.04, 0.16) * H,
            "s": rnd.choice([6, 8, 10, 12, 16, 22, 30]) * W / 1920, "c": rnd.choice(BRAISE[:5]), "t0": rnd.uniform(0.7, 2.2),
            "ph": rnd.uniform(0, 6.28), "k": rnd.random(),
        })
    # Chaque cellule du N est portée par une braise choisie (les plus proches de la cible, tirées au hasard) .
    for i, (c, r, col) in enumerate(cel):
        b = braises[i]
        b["cible"] = (gx0 + c * u_big, gy0 + r * u_big, col)
        b["s"] = max(b["s"], 16 * W / 1920)  # les cellules du N sont des braises bien visibles
        b["t0"] = min(b["t0"], 1.2)
        b["c"] = BRAISE[1 + (i % 3)]
    f_l1 = police("geist-latin-wght-normal.woff2", round(H * (0.052 if format == "16:9" else 0.034 if format == "9:16" else 0.046)), b"Medium")
    f_l2 = f_l1
    f_et = police("jetbrains-mono-latin-wght-normal.woff2", round(H * (0.019 if format == "16:9" else 0.0125 if format == "9:16" else 0.017)), b"Medium")
    l1, l2, et = TEXTES[lang]
    T_ASSEMBLE, T_FIN_ASSEMBLE, T_RANGE, T_FIN_RANGE = 2.1, 3.5, 4.2, 5.4
    out = subprocess.Popen(
        [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(IPS), "-i", "-",
         "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "slow", "-crf", "14",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(sortie)], stdin=subprocess.PIPE)
    for i in range(n):
        treel = i / IPS
        t = treel / facteur  # facteur < 1 : animation accélérée (versions courtes)
        couche = Image.new("RGB", (W * SS, H * SS), ENCRE)
        d = ImageDraw.Draw(couche)
        # --- Braises et rassemblement du N
        a_ass = ease((t - T_ASSEMBLE) / (T_FIN_ASSEMBLE - T_ASSEMBLE))
        phase_ln = t >= T_RANGE
        for b in braises:
            ap = (t - b["t0"]) / 0.5
            if ap <= 0 and "cible" not in b:
                continue
            ap = max(0.0, min(1.0, ap))
            y = b["y"] - b["v"] * max(0.0, t - b["t0"]) * 3.0
            x = b["x"] + math.sin(t * 1.3 + b["ph"]) * 18 * W / 1920
            s = b["s"]
            if "cible" in b:
                tx, ty, col = b["cible"]
                # Les cellules du N montent aussi, puis convergent vers leur place en grandissant et prennent leur couleur.
                px, py, ps = x, y, s
                x = px + (tx - px) * a_ass
                y = py + (ty - py) * a_ass
                s = ps + (u_big - ps) * a_ass
                couleur = mix(b["c"], col, a_ass)
                alpha = 1.0
                if t < b["t0"]:
                    alpha = 0.0
                if phase_ln:
                    continue  # le petit symbole est dessiné plus bas
            else:
                alpha = ap * max(0.0, 1 - a_ass * 2.2)
                couleur = b["c"]
            if alpha <= 0:
                continue
            col = mix(ENCRE, couleur, alpha)
            d.rectangle([x * SS, y * SS, (x + s - max(1, s * 0.08)) * SS, (y + s - max(1, s * 0.08)) * SS], fill=col)
        # Lueur douce sous les braises (screen d'une copie floue réduite)
        if t < T_RANGE:
            petit = couche.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
            lueur = petit.resize((W * SS, H * SS), Image.BILINEAR)
            couche = ImageChops.add(couche, lueur.point(lambda v: int(v * 0.55)))
        # --- Rangement du symbole et logotype
        if phase_ln:
            k = ease((t - T_RANGE) / (T_FIN_RANGE - T_RANGE))
            S = S_big + (S_small - S_big) * k
            x0 = gx0 + (sx_final - gx0) * k
            y0 = gy0 + (sy_final - gy0) * k
            d = ImageDraw.Draw(couche)
            u = S / 5
            for c, r, col in cel:
                d.rectangle([(x0 + c * u) * SS, (y0 + r * u) * SS, (x0 + (c + 1) * u) * SS - 1, (y0 + (r + 1) * u) * SS - 1], fill=col)
        out_img = couche.resize((W, H), Image.LANCZOS)
        if phase_ln:
            # Logotype : révélé de gauche à droite à partir du bord du symbole ; l'image finale est le logo officiel.
            k = ease((t - T_RANGE) / (T_FIN_RANGE - T_RANGE))
            if t >= T_FIN_RANGE:
                out_img.paste(lock, (lx, ly), lock)
            else:
                # Le logotype se découvre à mesure que le symbole se range : tout ce qui est à droite du bord du symbole
                # (plus une marge) apparaît en fondu ; le symbole en mouvement n'est jamais recouvert.
                S = S_big + (S_small - S_big) * k
                bord = round(gx0 + (sx_final - gx0) * k + S + LH * 0.25 - lx)
                alpha_k = ease((k - 0.25) / 0.75)
                if alpha_k > 0 and bord < LW:
                    reveal = lock.copy()
                    sym_w = round(LH)
                    import numpy as np
                    x = np.arange(LW, dtype=np.float32)
                    rampe = np.clip((x - max(bord, sym_w)) / (LH * 0.5), 0, 1) * alpha_k  # bord adouci : aucune lettre coupée net
                    masque = Image.fromarray((np.tile(rampe, (LH, 1)) * 255).astype("uint8"), "L")
                    reveal.putalpha(ImageChops.multiply(reveal.getchannel("A"), masque))
                    out_img.paste(reveal, (lx, ly), reveal)
        d2 = ImageDraw.Draw(out_img)
        if version == "marque" and t >= 5.2:
            cx = W // 2
            y1 = ly + LH + round(H * (0.075 if format == "16:9" else 0.06))
            for texte, f, y, t0, col in ((l1, f_l1, y1, 5.4, OS), (l2, f_l2, y1 + round(f_l1.size * 1.35), 6.2, ACCENT)):
                a = ease((t - t0) / 0.7)
                if a > 0:
                    d2.text((cx, y + (1 - a) * 18), texte, font=f, fill=mix(ENCRE, col, a), anchor="mm")
            a = ease((t - 7.1) / 0.7)
            if a > 0:
                d2.text((cx, y1 + round(f_l1.size * 3.0), ), et, font=f_et, fill=mix(ENCRE, BRUME, a), anchor="mm")
        if treel > duree - 0.7:
            out_img = Image.blend(out_img, Image.new("RGB", (W, H), ENCRE), min(1.0, (treel - (duree - 0.7)) / 0.7))
        out.stdin.write(out_img.tobytes())
    out.stdin.close()
    if out.wait():
        raise SystemExit("ffmpeg a échoué")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("sortie")
    a.add_argument("--format", default="16:9", choices=list(TAILLES))
    a.add_argument("--version", default="marque", choices=["marque", "sting"])
    a.add_argument("--lang", default="fr", choices=["fr", "en"])
    a.add_argument("--duree", type=float)
    a.add_argument("--facteur", type=float, default=1.0, help="< 1 accélère l'animation (spots courts)")
    o = a.parse_args()
    rendre(o.format, o.version, o.lang, o.duree or (8.4 if o.version == "marque" else 5.4), o.sortie, o.facteur)
