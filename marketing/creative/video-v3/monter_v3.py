"""Montage de la promo V3 à partir de montage-v3.json : plans composités (couches.py), moments produit et titres
(interface.py), carton de fin, bande-son (musique MiniMax-Music3 + son natif H3 + sound design sfx_v3.py), normalisation
à −14 LUFS, puis encodage. Les plans de bataille sont mis en cache par format (ils ne dépendent pas de la langue).

Usage : python3 monter_v3.py montage-v3.json --format 16x9|9x16 --langue fr|en [--version long|30|15] [--sortie f.mp4]
        [--plans id,id] (ne recalcule que ces plans) [--jobs 10]
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import couches  # noqa: E402
import interface  # noqa: E402
import sfx_v3  # noqa: E402

FFMPEG = couches.FFMPEG
IPS = 24
SR = 48000
CACHE = Path.home() / "nexora-creative-data/promo/v3/rendu"


def ff(args, **kw):
    r = subprocess.run([FFMPEG, "-v", "error", "-y", *args], capture_output=True, **kw)
    if r.returncode:
        raise SystemExit(f"ffmpeg : {r.stderr[-1500:]}")
    return r


def taille(fmt):
    return (1920, 1080) if fmt == "16x9" else (1080, 1920)


class Encodeur:
    """Écrit des images rgb24 dans un fichier vidéo intermédiaire (x264 presque sans perte)."""

    def __init__(self, chemin, W, H):
        self.p = subprocess.Popen([FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(IPS),
                                   "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "10", "-pix_fmt", "yuv444p", str(chemin)],
                                  stdin=subprocess.PIPE)

    def __call__(self, b):
        self.p.stdin.write(b)

    def fermer(self):
        self.p.stdin.close()
        if self.p.wait():
            raise SystemExit("encodage intermédiaire échoué")


def lire_video(chemin, W, H):
    brut = ff(["-i", str(chemin), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]).stdout
    return list(np.frombuffer(brut, np.uint8).reshape(-1, H, W, 3))


def cle(spec, fmt, n, reglages):
    h = hashlib.sha1(json.dumps([spec, fmt, n, reglages], sort_keys=True).encode())
    for k in ("plaque", "image"):
        if spec.get(k):
            h.update(str(Path(spec[k]).expanduser().stat().st_mtime).encode())
    h.update((ICI / "couches.py").read_bytes())
    return h.hexdigest()[:12]


def rendre_un(args):
    spec, fmt, n, reglages, chemin = args
    W, H = taille(fmt)
    enc = Encodeur(chemin, W, H)
    couches.rendre_plan(spec, W, H, n, enc, reglages, vertical=(fmt == "9x16"), lettre=reglages.get("cache_239", True))
    enc.fermer()
    return chemin


# ------------------------------------------------------------------------------------------------ audio
def lire_audio(chemin, debut=0.0, duree=None):
    a = ["-ss", f"{debut:.4f}"] if debut else []
    a += ["-i", str(chemin)]
    if duree:
        a += ["-t", f"{duree:.4f}"]
    brut = ff([*a, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]).stdout
    return np.frombuffer(brut, np.float32).reshape(-1, 2).copy()


def poser(piste, son, t, db=0.0, fondu_in=0.0, fondu_out=0.0):
    i0 = int(round(t * SR))
    if i0 < 0:
        son = son[-i0:]
        i0 = 0
    son = son[: max(0, len(piste) - i0)].copy()
    if not len(son):
        return
    if fondu_in:
        k = min(len(son), int(fondu_in * SR))
        son[:k] *= np.linspace(0, 1, k)[:, None]
    if fondu_out:
        k = min(len(son), int(fondu_out * SR))
        son[-k:] *= np.linspace(1, 0, k)[:, None]
    piste[i0:i0 + len(son)] += son * 10 ** (db / 20)


def ecrire_wav(x, chemin):
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------------------------------------ montage
def construire(m, fmt, langue, version, sortie, seulement=None, jobs=10):
    W, H = taille(fmt)
    reglages = m.get("pellicule", {})
    # une version courte (« 30 », « 15 ») a sa propre séquence, sa musique et ses sons ; elle partage les plans
    V = m["versions"][version] if version != "long" else {"sequence": m["sequence"], "musique": m["musique"], "sons": m["sons"],
                                                           "silences": m.get("silences", {}).get("long", [])}
    seq = V["sequence"]
    plans = m["plans"]
    # 1. découpage en images exactes sur la grille (aucune dérive cumulée)
    segs, faites, debut_seg = [], 0, 0.0
    for s in seq:
        n = max(1, round(s["fin"] * IPS) - faites)
        segs.append({**s, "n": n, "t0": faites / IPS})
        faites += n
    duree = faites / IPS
    print(f"{fmt} {langue} {version} : {len(segs)} segments, {duree:.2f} s", flush=True)

    # 2. plans de bataille (cache par format), en parallèle
    (CACHE / fmt).mkdir(parents=True, exist_ok=True)
    travaux, fichiers = [], {}
    for k, s in enumerate(segs):
        if "plan" not in s:
            continue
        spec = {**plans[s["plan"]], **s.get("modif", {}), "nom": s["plan"] + s.get("suffixe", "")}
        if fmt == "9x16" and spec.get("plaque_v") and Path(spec["plaque_v"]).expanduser().exists():
            # plaque verticale native : le cadrage 16:9 ne s'applique pas, le suivi reste
            spec["plaque"] = spec.pop("plaque_v")
            spec.pop("cadre", None)
        spec.pop("plaque_v", None)
        for q in ("plaque", "image"):
            if spec.get(q):
                spec[q] = str(Path(spec[q]).expanduser())
        c = CACHE / fmt / f"{spec['nom']}-{cle(spec, fmt, s['n'], reglages)}.mp4"
        fichiers[k] = (c, spec)
        if not c.exists() or (seulement and s["plan"] in seulement and False):
            travaux.append((spec, fmt, s["n"], reglages, str(c)))
    if travaux:
        print(f"  {len(travaux)} plans à calculer", flush=True)
        with ProcessPoolExecutor(jobs) as ex:
            for c in ex.map(rendre_un, travaux):
                print("  ✓", Path(c).name, flush=True)

    # 3. segments finaux (interface, titres, carton) et concaténation
    ui = interface.Interface(W, H, langue)
    T = interface.MARQUE["langues"][langue]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        morceaux = []
        for k, s in enumerate(segs):
            f = d / f"s{k:03d}.mp4"
            if k in fichiers:
                f = fichiers[k][0]
            else:
                imgs = segment_special(s, ui, T, W, H, fichiers, segs, d)
                enc = Encodeur(f, W, H)
                for im in imgs[: s["n"]]:
                    enc(np.ascontiguousarray(im).tobytes())
                for _ in range(s["n"] - len(imgs)):
                    enc(np.ascontiguousarray(imgs[-1]).tobytes())
                enc.fermer()
            morceaux.append(f)
        liste = d / "liste.txt"
        liste.write_text("".join(f"file '{x}'\n" for x in morceaux))
        image = d / "image.mp4"
        ff(["-f", "concat", "-safe", "0", "-i", str(liste), "-c", "copy", str(image)])

        # 4. bande-son
        piste = np.zeros((int(duree * SR) + SR, 2), np.float32)
        mus = V["musique"]
        for bloc in mus["blocs"]:
            son = lire_audio(Path(bloc["fichier"]).expanduser(), bloc["de"], bloc["a"] - bloc["de"])
            poser(piste, son, bloc["t"], bloc.get("db", 0) + mus.get("db", 0), bloc.get("fondu_in", 0.01), bloc.get("fondu_out", 0.02))
        h3 = np.zeros_like(piste)
        for k, s in enumerate(segs):
            if k in fichiers:
                spec = fichiers[k][1]
                if spec.get("plaque") and s.get("son_h3", spec.get("son_h3", -6)) is not None:
                    son = son_plan(spec, s)
                    poser(h3, son, s["t0"], s.get("son_h3", spec.get("son_h3", -6)), 0.004, 0.03)
        piste += h3 * 10 ** (m.get("h3_db", 0) / 20)
        rng = np.random.default_rng(7)
        for e in V["sons"] + [x for s in segs for x in s.get("sons", [])]:
            t = e["t"]
            son = sfx_v3.generer(e["type"], e.get("duree", 1.0), np.random.default_rng(e.get("graine", int(rng.integers(1 << 30)))))
            ancre = e.get("ancre", 0.0) * e.get("duree", 1.0)  # « montee » / « inverse » : la fin tombe sur t
            poser(piste, son.astype(np.float32), t - ancre, e.get("db", -6))
        piste = piste[: int(duree * SR)]
        for a, b in V.get("silences", []):
            piste[int(a * SR):int(b * SR)] *= 0.0
        brut = d / "brut.wav"
        ecrire_wav(piste / max(1.0, np.abs(piste).max()) * 0.9, brut)
        # mesure puis normalisation linéaire à −14 LUFS, crête vraie −1 dBTP
        mes = subprocess.run([FFMPEG, "-hide_banner", "-i", str(brut), "-af", "loudnorm=I=-14:TP=-1:LRA=14:print_format=json", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        j = json.loads(mes[mes.rindex("{"):mes.rindex("}") + 1])
        # gain vers −14 LUFS puis limiteur à crête −1,2 dBFS (le limiteur ne retire que les crêtes, la sonie reste à la cible)
        af = f"volume={-14.0 - float(j['input_i']):.2f}dB,alimiter=limit=0.8:attack=0.5:release=60:level=false,aresample=48000"
        ff(["-i", str(image), "-i", str(brut), "-af", af, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "320k", "-shortest", str(sortie)])
    print("→", sortie, flush=True)


def son_plan(spec, s):
    """Son natif H3 du plan, aux mêmes instants source que l'image (vitesse, rampes)."""
    n = s["n"]
    src = lire_audio(spec["plaque"])
    pos = couches.temps_source(spec, n, 10 ** 6) / IPS  # instants source par image
    t_out = np.arange(int(n / IPS * SR)) / SR
    t_src = np.interp(t_out, np.arange(n) / IPS, pos)
    idx = np.clip((t_src * SR).astype(np.int64), 0, len(src) - 1)
    return src[idx]


def segment_special(s, ui, T, W, H, fichiers, segs, d):
    kind = s["type"]
    def images_de(plan_id, nmax=200):
        for k, (c, spec) in fichiers.items():
            if segs[k]["plan"] == plan_id:
                return lire_video(c, W, H)[:nmax]
        raise SystemExit(f"plan {plan_id} absent du montage")
    if kind == "saisie":
        return ui.saisie(s["n"], part_frappe=s.get("part_frappe", 0.62), clic=s.get("clic", 0.8))
    if kind == "rendu":
        return ui.rendu(s["n"], images_de(s["source"]))
    if kind == "galerie":
        return ui.galerie(s["n"], [images_de(p) for p in s["sources"]])
    if kind == "titre":
        fond = images_de(s["fond"]) if s.get("fond") else None
        return interface.titre(W, H, s["n"], T[s["texte"]], fond)
    if kind == "noir":
        return [np.zeros((H, W, 3), np.uint8)]
    if kind == "fin":
        return carton_fin(W, H, s["n"], T)
    raise SystemExit(f"segment inconnu : {kind}")


def carton_fin(W, H, n, T):
    """Carton de fin actuel (mosaïque qui éclate à l'impact, puis nom, slogan, mentions), paramétré par marque.json."""
    from PIL import Image, ImageDraw
    M = interface.MARQUE
    col = {k: tuple(v) for k, v in M["couleurs"].items()}
    braise = [(255, 211, 122), (255, 177, 26), (255, 138, 31), (255, 90, 31), (224, 52, 28), (176, 26, 60)]
    v = H > W
    u = W / (1080 if v else 1920)
    f_nom = interface.police(M["polices"]["titre"], (150 if v else 150) * u, b"SemiBold")
    f_slo = interface.police(M["polices"]["titre"], (54 if v else 56) * u, b"Medium")
    f_pet = interface.police(M["polices"]["texte"], (30 if v else 24) * u, b"Regular")

    def hache(c, r, s_):
        h = ((c + 1) * 73856093 ^ (r + 1) * 19349663 ^ (s_ + 1) * 83492791) & 0xFFFFFFFF
        h = ((h ^ (h >> 15)) * 2246822507) & 0xFFFFFFFF
        h = ((h ^ (h >> 13)) * 3266489909) & 0xFFFFFFFF
        return ((h ^ (h >> 16)) & 0xFFFFFFFF) / 4294967296

    out = []
    taille_c = int(40 * u)
    cols, rows = math.ceil(W / taille_c), math.ceil(H / taille_c)
    for i in range(n):
        s_ = i / IPS
        im = Image.new("RGB", (W, H), col["encre"])
        d = ImageDraw.Draw(im)
        seuil = -0.35 + min(1.0, max(0.0, (s_ - 0.1) / 0.95)) * 1.6
        if seuil < 1.2 and M.get("carton_fin") == "mosaique":
            for c in range(cols):
                for r in range(rows):
                    a = 1 - abs(c / max(1, cols - 1) - 0.5) * 0.9 - abs(r / max(1, rows - 1) - 0.5) * 0.5
                    k = hache(c, r, 5)
                    if k > a - seuil:
                        continue
                    d.rectangle([c * taille_c, r * taille_c, (c + 1) * taille_c - 2, (r + 1) * taille_c - 2], fill=braise[min(5, int(a * 6 * (0.6 + 0.4 * k)))])
        a = min(1.0, max(0.0, (s_ - 1.05) / 0.4))
        mix = lambda c: tuple(int(col["encre"][q] + (c[q] - col["encre"][q]) * a) for q in range(3))
        if a > 0:
            n1, n2 = M["marque"], M["produit"]
            larg = f_nom.getlength(n1 + " " + n2)
            if larg > W * 0.9 or v:
                d.text((W / 2, H * 0.40), n1, font=f_nom, fill=mix(col["os"]), anchor="mm")
                d.text((W / 2, H * 0.40 + f_nom.size * 1.05), n2, font=f_nom, fill=mix(col["signal"]), anchor="mm")
                ys = H * 0.40 + f_nom.size * 2.3
            else:
                x = (W - larg) / 2
                d.text((x, H * 0.44), n1, font=f_nom, fill=mix(col["os"]), anchor="ls")
                d.text((x + f_nom.getlength(n1 + " "), H * 0.44), n2, font=f_nom, fill=mix(col["signal"]), anchor="ls")
                ys = H * 0.56
            d.text((W / 2, ys), T["slogan"], font=f_slo, fill=mix(col["os"]), anchor="mm")
        b = min(1.0, max(0.0, (s_ - 2.0) / 0.5))
        if b > 0:
            pet = tuple(int(col["encre"][q] + (col["brume"][q] - col["encre"][q]) * b) for q in range(3))
            d.text((W / 2, ys + 90 * u), T["sous_titre"], font=f_pet, fill=pet, anchor="mm")
            ment = T["mentions"]
            if v and f_pet.getlength(ment) > W * 0.92:
                p = ment.split(" · ", 1)
                d.text((W / 2, H - 120 * u), p[0], font=f_pet, fill=pet, anchor="mm")
                d.text((W / 2, H - 84 * u), p[1], font=f_pet, fill=pet, anchor="mm")
            else:
                d.text((W / 2, H - 70 * u), ment, font=f_pet, fill=pet, anchor="mm")
        if s_ < 0.12:
            k = 1 - s_ / 0.12
            im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.85 * k)
        fin = n / IPS
        if s_ > fin - 0.8:
            im = Image.blend(im, Image.new("RGB", (W, H), col["encre"]), min(1.0, (s_ - (fin - 0.8)) / 0.8))
        out.append(np.asarray(im))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("montage")
    ap.add_argument("--format", default="16x9")
    ap.add_argument("--langue", default="fr")
    ap.add_argument("--version", default="long")
    ap.add_argument("--sortie")
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    m = json.loads(Path(a.montage).read_text())
    sortie = a.sortie or str(Path.home() / f"nexora-creative-data/promo/v3/brouillons/v3-{a.format}-{a.langue}-{a.version}.mp4")
    construire(m, a.format, a.langue, a.version, sortie, jobs=a.jobs)
