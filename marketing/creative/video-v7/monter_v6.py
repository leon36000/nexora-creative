#!/usr/bin/env python3
"""Moteur V6 CPU : JSON → Pillow → tube ffmpeg → segments H.264 → master.

Voir README-montage.md pour le contrat JSON et les conventions de temps.
Architecture et outils repris de V4 ; pellicule et synthèses reprises de V3.
Aucune image intermédiaire sur disque, aucune dépendance à l'état de V4.
"""
import argparse
import bisect
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import uuid
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

import effets_v6
import sfx_v6

ICI = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("V6_CACHE", str(ICI / ".cache"))).expanduser().resolve()
STATIQUE = Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static"
FFMPEG = os.environ.get("V6_FFMPEG") or str(STATIQUE / "ffmpeg")
FFPROBE = os.environ.get("V6_FFPROBE") or str(STATIQUE / "ffprobe")
IPS, SR = 24, 48000
TYPES = {"plan", "saisie", "boost", "titre", "chapitre", "avant_apres", "mosaique", "noir", "carton"}
PATH_KEYS = {"fichier", "fichier_vertical", "dossier", "logo", "boost_json"}
LOCAL_KEYS = {f"{k}_{langue}" for k in ("fichier", "fichier_vertical", "dossier") for langue in ("fr", "en")}
STYLES = {"claque", "balayage", "empile", "legende", "grand", "phrase"}
PRESETS = {
    "neutre": {"exposition": 1., "saturation": 1., "contraste": 1.02, "teinte_ombres": [0, 0, 0], "teinte_hautes": [0, 0, 0]},
    "nuit_feu": {"exposition": 1.06, "saturation": 1.08, "contraste": 1.08, "teinte_ombres": [-.012, .002, .025], "teinte_hautes": [.045, .012, -.025]},
    "espace": {"exposition": 1., "saturation": .92, "contraste": 1.12, "teinte_ombres": [-.014, .006, .032], "teinte_hautes": [.005, .008, .025]},
    "orage": {"exposition": .98, "saturation": .80, "contraste": 1.16, "teinte_ombres": [-.012, .008, .025], "teinte_hautes": [.008, .012, .025]},
    "aube": {"exposition": 1.05, "saturation": .96, "contraste": 1.04, "teinte_ombres": [.008, .002, .016], "teinte_hautes": [.04, .018, -.018]},
}


def ff(args, **kw):
    r = subprocess.run([FFMPEG, "-hide_banner", "-v", "error", "-nostdin", "-y", *map(str, args)], capture_output=True, **kw)
    if r.returncode:
        raise RuntimeError(f"ffmpeg : {r.stderr.decode(errors='replace')[-2500:]}")
    return r


@lru_cache(maxsize=128)
def sonder(fichier):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(fichier)], capture_output=True, text=True)
    if r.returncode:
        raise ValueError(f"Média illisible : {fichier}\n{r.stderr[-1000:]}")
    return json.loads(r.stdout)


def duree_media(fichier):
    return float(sonder(str(fichier))["format"]["duration"])


def chemin(p, base=ICI):
    p = Path(os.path.expandvars(str(p))).expanduser()
    return (base / p).resolve() if not p.is_absolute() else p.resolve()


def ecriture(p):
    p = chemin(p, Path.cwd())
    if not (p.is_relative_to(ICI) or p.is_relative_to(CACHE)):
        raise ValueError(f"Écriture limitée au dossier V6 et à V6_CACHE : {p}")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def sortie_exclusive(sortie):
    rapport = sortie.with_suffix('.rendu.json')
    collisions = [str(p) for p in (sortie, rapport) if p.exists()]
    if collisions:
        raise FileExistsError('Sortie déjà présente; choisir un nouveau nom : '+', '.join(collisions))


def copier_exclusif(source, destination):
    """Publie en création exclusive; une interruption laisse l'essai partiel au même nom."""
    source, destination = Path(source), Path(destination)
    with source.open('rb') as src, destination.open('xb') as dst:
        shutil.copyfileobj(src, dst)
        dst.flush()
        os.fsync(dst.fileno())
    return destination


def ecrire_exclusif(destination, contenu):
    with Path(destination).open('x', encoding='utf-8') as dst:
        dst.write(contenu)
        dst.flush()
        os.fsync(dst.fileno())


def resoudre(obj, base, langue=None):
    if isinstance(obj, list):
        return [resoudre(v, base, langue) for v in obj]
    if not isinstance(obj, dict):
        return obj
    out = {k: str(chemin(v, base)) if k in PATH_KEYS | LOCAL_KEYS and isinstance(v, str)
           else resoudre(v, base, langue) for k, v in obj.items()}
    if langue:
        for k in ("fichier", "dossier", "fichier_vertical"):
            local = out.get(f"{k}_{langue}")
            if local:
                if Path(local).exists():
                    out[k] = local
                else:
                    # Une variante verticale traduite manquante revient au fichier
                    # horizontal de la langue, plutôt qu'à une autre langue.
                    repli = out.get("fichier") if k == "fichier_vertical" else out.get(k)
                    print(f"Avertissement : source {langue} absente : {local} ; repli sur {repli or local}", file=sys.stderr)
                    out[k] = repli or local
        out = {k: v for k, v in out.items() if k not in LOCAL_KEYS}
    return out


def ease(x):
    x = min(1., max(0., x))
    return x*x*(3-2*x)


def interp(cles, t):
    """Interpolation lissée de cadrages ; les vitesses ont leur intégrale propre."""
    if t <= cles[0][0]:
        return cles[0][1:]
    for a, b in zip(cles, cles[1:]):
        if t <= b[0]:
            u = ease((t-a[0])/(b[0]-a[0]))
            return [x+(y-x)*u for x, y in zip(a[1:], b[1:])]
    return cles[-1][1:]


def integrale_vitesse(v, t):
    """Intégrale analytique de la rampe linéaire, prolongée constante aux bouts.

    t peut être un scalaire, des instants d'image ou tous les échantillons audio.
    Aucune somme arrondie au nombre d'images : son et image partagent cette horloge.
    """
    x = np.maximum(np.asarray(t, dtype=np.float64), 0.)
    if isinstance(v, (int, float)):
        return x*float(v)
    ts, vs = np.asarray(v, dtype=np.float64).T
    if ts[0] > 0:
        ts, vs = np.r_[0., ts], np.r_[vs[0], vs]
    aires = np.r_[0., np.cumsum(np.diff(ts)*(vs[:-1]+vs[1:])*.5)]
    k = np.clip(np.searchsorted(ts, x, side="right")-1, 0, len(ts)-1)
    pentes = np.r_[np.diff(vs)/np.diff(ts), 0.]
    dt = x-ts[k]
    return aires[k]+vs[k]*dt+.5*pentes[k]*dt*dt


def temps_source(seg, t):
    return seg.get("entree", 0.)+(-1 if seg.get("inverse") else 1)*integrale_vitesse(seg.get("vitesse", 1.), t)


def boite(im, cx, cy, zoom, W, H):
    sw, sh = im.size
    pw = min(sw, sh*W/H)/max(1., zoom)
    ph = pw*H/W
    x = min(max(cx*sw-pw/2, 0), sw-pw)
    y = min(max(cy*sh-ph/2, 0), sh-ph)
    return (x, y, x+pw, y+ph)


def recadrer(im, cx, cy, zoom, W, H):
    return im.resize((W, H), Image.Resampling.LANCZOS, box=boite(im, cx, cy, zoom, W, H))


@lru_cache(maxsize=12)
def capture(fichier):
    with Image.open(fichier) as im:
        return im.convert("RGB")


class Lecteur:
    """Décode au plus deux blocs d'une seconde par source, jamais un rush entier.

    Le même lecteur convient aux rampes, au retour arrière et aux couches synchrones.
    Les blocs RGB passent dans stdout ; aucun fichier d'images n'est créé.
    """
    def __init__(self):
        self.blocs = OrderedDict()

    def image(self, fichier, t):
        f = str(fichier)
        if Path(f).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            return capture(f).copy()
        p = sonder(f)
        v = next(s for s in p["streams"] if s["codec_type"] == "video")
        w, h = int(v["width"]), int(v["height"])
        n = max(1, int(round(float(v.get("duration", p["format"]["duration"]))*IPS)))
        idx = min(n-1, max(0, int(math.floor(float(t)*IPS+1e-7))))
        block = idx//IPS
        key = (f, block)
        if key not in self.blocs:
            raw = ff(["-threads", "1", "-ss", block, "-i", f, "-an", "-vf", f"fps={IPS}", "-frames:v", IPS,
                      "-threads", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]).stdout
            a = np.frombuffer(raw, np.uint8)
            if not len(a) or len(a) % (w*h*3):
                raise ValueError(f"Bloc vidéo vide ou incomplet : {f} à {block}s")
            self.blocs[key] = a.reshape(-1, h, w, 3)
            # Deux secondes par source ; neuf petits rushes restent bornés en RAM.
            anciens = [k for k in self.blocs if k[0] == f]
            for k in anciens[:-2]:
                del self.blocs[k]
        self.blocs.move_to_end(key)
        frames = self.blocs[key]
        return Image.fromarray(frames[min(idx % IPS, len(frames)-1)]).copy()


@lru_cache(maxsize=96)
def police(fichier, taille, graisse=900):
    f = ImageFont.truetype(fichier, max(8, int(taille)))
    try:
        axes = f.get_variation_axes()
        f.set_variation_by_axes([max(a["minimum"], min(a["maximum"], graisse)) if a["name"] == b"Weight" else a["default"] for a in axes])
    except (OSError, AttributeError):
        pass
    return f


def couper(d, txt, f, largeur):
    lignes = []
    for paragraphe in txt.split("\n"):
        cur = ""
        for mot in paragraphe.split():
            essai = (cur+" "+mot).strip()
            if cur and d.textlength(essai, font=f) > largeur:
                lignes.append(cur)
                cur = mot
            else:
                cur = essai
        lignes.append(cur)
    return lignes


class CapturesAbsentes(ValueError):
    pass


@lru_cache(maxsize=64)
def sequence(dossier, etapes, duree):
    folder = Path(dossier)
    journal = folder / "journal.jsonl"
    rows = []
    if journal.exists():
        for line in journal.read_text().splitlines():
            r = json.loads(line)
            if "image" in r and r.get("etiquette") in etapes:
                # Le journal peut provenir d'une autre machine : priorité au basename local.
                f = folder / Path(r["image"]).name
                rows.append((float(r["t"]), str(f), r["etiquette"]))
    else:
        for f in sorted(folder.glob("*")):
            if f.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                etape = f.stem.split("-", 1)[-1]
                if etape in etapes:
                    rows.append((float(len(rows)), str(f), etape))
    if not rows:
        raise CapturesAbsentes(f"Aucune capture pour {etapes} dans {dossier}")
    rows.sort()
    deltas = np.diff([r[0] for r in rows])
    pas = float(np.median(deltas[deltas > 0])) if np.any(deltas > 0) else 1.
    span = rows[-1][0]-rows[0][0]+pas
    return tuple(((t-rows[0][0])/span*duree, f, etape) for t, f, etape in rows)


def fichier_capture(seg, t):
    rows = sequence(seg["dossier"], tuple(seg.get("etapes", ["vide", "saisie", "saisie-fin", "survol"])), seg["duree"])
    k = max(0, bisect.bisect_right([r[0] for r in rows], t)-1)
    return rows[k][1]


def capture_a(seg, t):
    return capture(fichier_capture(seg, t)).copy()


def cle_mot(txt):
    return "".join(c for c in unicodedata.normalize("NFKD", txt.casefold()) if c.isalnum())


def mots_boost(texte, termes, duree):
    """Budget visuel borné ; les expressions clés restent entières et prioritaires."""
    cles = list(dict.fromkeys(t.strip() for t in termes if t.strip()))
    exclus = {cle_mot(m) for t in cles for m in t.split()}
    exclus.update("avec dans pour plus sans sous dont leur leurs cette comme tandis chaque puis from with that this into over under while then their".split())
    secondaires = []
    vus = set(exclus)
    for mot in texte.split():
        normal = cle_mot(mot)
        if len(normal) >= 4 and normal not in vus:
            secondaires.append(mot)
            vus.add(normal)
    budget = max(6, min(24, round(duree*12)))
    if len(secondaires) > budget:
        secondaires = [secondaires[i] for i in np.linspace(0, len(secondaires)-1, budget, dtype=int)]
    return [(t, True) for t in cles]+[(m, False) for m in secondaires]


# Petit lexique volontairement local : aucune dépendance réseau/correcteur.
# Les accents comptent ici (chateau ≠ château), contrairement à la déduplication.
LEXIQUE_BOOST = frozenset("""
un une le la les des du de d l et en au aux sur sous dans avec sans pour par
ce cette ces son sa ses mon ma mes ton ta tes qui que à a est sont très plus
dragon dragons château châteaux feu flammes nuit caméra travelling circulaire
attaque croiseur spatial vaisseau vaisseaux sabre sabres laser bataille orage
monstre marin petit chat voiture explose explosion flotte montagne montagnes
image vidéo film lumière rouge orange bleu vert noir blanc sombre forêt mer
robot espace planète soleil lune femme homme enfant marche court vole tourne
ralenti rapide lent gros plan cinématique épique réaliste photo portrait
a an the and of on in at to from with without is are this that my your
dragon dragons castle fire flames night camera tracking circular attack
spaceship space ship ships battle storm sea monster little cat car explodes
explosion fleet mountain mountains image video film light red blue green
black white dark forest ocean robot planet sun moon woman man child walking
running flying slow fast cinematic realistic photo close up portrait
""".split())


def fautes_boost(mots, explicites=None):
    normal = lambda m: unicodedata.normalize("NFC", m.casefold()).strip(".,;:!?«»\"'()")
    if explicites is not None:
        return {normal(m) for m in explicites}
    return {normal(m) for m in mots.split() if normal(m) not in LEXIQUE_BOOST}


def horloge_boost(seg, t):
    """Phases en images, y compris pour un début non aligné sur 24 i/s."""
    debut = round(seg.get("debut", 0)*IPS)
    n = round((seg.get("debut", 0)+seg["duree"])*IPS)-debut
    i = max(0, min(n-1, round((seg.get("debut", 0)+t)*IPS)-debut))
    return i, n, max(1, math.floor(n*.25)), max(2, math.floor(n*.80))


def cles_boost(seg):
    """Chaque claque dispose de 2–3 images ; le surplus reste dans les rayons."""
    _, _, a, b = horloge_boost(seg, 0)
    termes = list(dict.fromkeys(t.strip() for t in seg.get("termes_cles", []) if t.strip()))
    count = min(len(termes), (b-a)//2)
    # L'ordre JSON est l'ordre de priorité éditoriale.
    return [(terme, a+2*k, a+2*k+2+int(k == count-1 and b-a > 2*count))
            for k, terme in enumerate(termes[:count])]


def flou_directionnel(im, dx, dy, force=1.):
    if abs(dx)+abs(dy) < .7:
        return im
    out = im
    for k in range(1, 4):
        shifted = ImageChops.offset(im, int(dx*k/3*force), int(dy*k/3*force))
        out = Image.blend(out, shifted, 1/(k+1))
    return out


def flou_radial(im, force):
    out = im
    for k in range(1, 4):
        z = recadrer(im, .5, .5, 1+force*k/3, *im.size)
        out = Image.blend(out, z, 1/(k+1))
    return out


class Rendu:
    def __init__(self, m, marque, fmt, langue, brouillon=False, taille=None):
        self.m, self.b, self.langue = m, marque, langue
        self.vertical = fmt == "9x16"
        self.W, self.H = taille or ((1080, 1920) if self.vertical else (1920, 1080))
        if brouillon:
            self.W, self.H = self.W//2, self.H//2
        self.s = min(self.W, self.H)
        self.c = {k: tuple(v) for k, v in marque["couleurs"].items()}
        self.L = marque.get("textes", marque.get("langues", {}))[langue]
        self.lecteur = Lecteur()
        self.pellicules = {}
        self.sprites = {}
        self.animations = {}
        self.beat = 60/m.get("bpm", 124.8)

    def texte(self, id_):
        if id_ not in self.L:
            raise ValueError(f"Texte de marque absent ({self.langue}) : {id_}")
        return self.L[id_]

    def font(self, taille, mono=False, graisse=None):
        p = self.b["polices"]
        return police(p["mono" if mono else "titre"], int(taille), graisse or (500 if mono else p.get("graisse_titre", 900)))

    def noir(self):
        return Image.new("RGB", (self.W, self.H), self.c["encre"])

    def manquant(self, fichier, W=None, H=None):
        W, H = W or self.W, H or self.H
        im = Image.new("RGB", (W, H), (0, 0, 0))
        sprite, _ = self.texte_calque(Path(fichier).name, min(W, H)*.075, W*.88, H*.65, mono=True)
        im.paste(sprite, ((W-sprite.width)//2, (H-sprite.height)//2), sprite)
        return im

    def texte_calque(self, texte, taille, largeur, hauteur, couleur="os", mono=False, empile=False):
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        while True:
            f = self.font(taille, mono)
            lignes = texte.split() if empile else couper(d, texte, f, largeur)
            large = max([d.textlength(l, font=f) for l in lignes] or [0])
            haut = len(lignes)*f.size*1.16
            if (large <= largeur and haut <= hauteur) or taille <= 9:
                break
            taille *= .94
        im = Image.new("RGBA", (max(1, int(large)+int(f.size*.12)+4), max(1, int(haut)+4)))
        d = ImageDraw.Draw(im)
        for k, ligne in enumerate(lignes):
            d.text((im.width/2, k*f.size*1.16), ligne, font=f, anchor="mt", fill=(*self.c[couleur], 255))
        return im, f.size

    def place(self, im, calque, position="centre", alpha=1.):
        if isinstance(position, (list, tuple)):
            cx, cy = position
        else:
            cx, cy = .5, {"haut": .19 if self.vertical else .14, "bas": .73 if self.vertical else .84, "centre": .46 if self.vertical else .5}.get(position, .5)
        x, y = int(cx*self.W-calque.width/2), int(cy*self.H-calque.height/2)
        if self.vertical:
            y = max(math.ceil(.12*self.H), min(y, math.floor(.80*self.H)-calque.height))
        calque = calque.copy()
        if alpha < 1:
            calque.putalpha(calque.getchannel("A").point(lambda a: int(a*max(0, alpha))))
        im.paste(calque, (x, y), calque)
        return im

    def etiquette(self, im, id_, x, y, couleur="os"):
        txt = self.texte(id_)
        sprite, _ = self.texte_calque(txt, self.s*.027, self.W*.72, self.H*.10, couleur, mono=True)
        pad = max(5, int(self.s*.012))
        d = ImageDraw.Draw(im)
        d.rectangle((x-pad, y-pad, x+sprite.width+pad, y+sprite.height+pad), fill=self.c["encre"])
        im.paste(sprite, (int(x), int(y)), sprite)

    def pellicule(self, im, seg, t):
        nom = seg.get("etalonnage", "neutre")
        key = (nom, im.size)
        if key not in self.pellicules:
            r = {"noir": .003, "halo": .12, "reflet": .05, "vignette": .14, "grain": .014, **PRESETS[nom]}
            self.pellicules[key] = effets_v6.Pellicule(*im.size, nom, r)
        pel = self.pellicules[key]
        # V3 utilise un RNG pour choisir le grain ; réamorçage par image pour que --de
        # retrouve exactement le grain d'un rendu complet et que les couches restent stables.
        pel.rng = np.random.default_rng(int(t*IPS)+7)
        a = pel.finir(pel.etalonner(np.asarray(im, np.float32)/255), int(t*IPS), False)
        return Image.fromarray((a*255+.5).astype(np.uint8))

    def source(self, spec, t, W=None, H=None, decouper_zone=False):
        if isinstance(spec, str):
            spec = {"fichier": spec}
        W, H = W or self.W, H or self.H
        absent = spec.get("_absents", {})
        k = "dossier" if "dossier" in spec else ("fichier_vertical" if self.vertical and "fichier_vertical" in spec else "fichier")
        if k in absent:
            return self.manquant(absent[k], W, H)
        if spec.get("type") == "damier":
            yy, xx = np.indices((H, W))
            a = ((xx//max(4, int(self.s*.035))+yy//max(4, int(self.s*.035))) % 2)[..., None]
            return Image.fromarray(np.where(a, self.c["brume"], self.c["encre"]).astype(np.uint8))
        if "dossier" in spec:
            f = fichier_capture(spec, t)
            if f in spec.get("_captures_absentes", []):
                return self.manquant(f, W, H)
            im = capture(f).copy()
        else:
            f = spec.get("fichier_vertical", spec["fichier"]) if self.vertical else spec["fichier"]
            im = self.lecteur.image(f, temps_source(spec, t))
        if "zone" in spec:
            # Une zone désigne le média à montrer, pas seulement son centre.
            # Couper d'abord évite de réintroduire le reste de l'UI dans le panneau.
            cx, cy, zoom, rect = self.zone(im, spec, W, H)
            if decouper_zone:
                im = im.crop(tuple(round(v) for v in rect))
                cx, cy, zoom = .5, .5, 1
        else:
            cles = spec.get("cadrage_v" if self.vertical else "cadrage") or spec.get("cadrage") or [[0, .5, .5, 1]]
            cx, cy, zoom = interp(cles, t)
        im = recadrer(im, cx, cy, zoom, W, H)
        if spec.get("saturation") is not None:
            im = ImageEnhance.Color(im).enhance(spec["saturation"])
        return im

    def zone(self, im, seg, W=None, H=None):
        W, H = W or self.W, H or self.H
        vw, vh = seg.get("viewport", [1600, 900])
        x0, y0, x1, y1 = seg.get("zone", [124, 370, 660, 592])
        x0, y0 = max(0, min(vw-1, x0)), max(0, min(vh-1, y0))
        x1, y1 = max(x0+1, min(vw, x1)), max(y0+1, min(vh, y1))
        sw, sh = im.size
        rect = (x0/vw*sw, y0/vh*sh, x1/vw*sw, y1/vh*sh)
        zoom = max(1, min(sw, sh*W/H)/((x1-x0)/vw*sw*1.08))
        return (x0+x1)/2/vw, (y0+y1)/2/vh, zoom, rect

    def saisie(self, seg, t):
        if "dossier" in seg.get("_absents", {}):
            return self.manquant(seg["dossier"])
        f = fichier_capture(seg, t)
        if f in seg.get("_captures_absentes", []):
            return self.manquant(f)
        im = capture(f).copy()
        cx, cy, z, rect = self.cadre_saisie(im, seg, t)
        mask = Image.new("L", im.size)
        ImageDraw.Draw(mask).rectangle(rect, fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(max(2, im.width*.005)))
        im = Image.composite(im, im.filter(ImageFilter.GaussianBlur(im.width*.002)), mask)
        return recadrer(im, cx, cy, z, self.W, self.H)

    def cadre_saisie(self, im, seg, t):
        x0, y0, x1, y1 = seg.get("zone", [124, 370, 660, 592])
        spec = dict(seg, zone=seg.get("zone_texte", [x0, y0, x1, min(y1, y0+49)]))
        cx, cy, _, rect = self.zone(im, spec)
        largeur = rect[2]-rect[0]
        cible = .90 if self.vertical else .70
        part = cible*(seg.get("zoom_texte_v", seg.get("zoom_texte", 1)) if self.vertical else seg.get("zoom_texte", 1))
        # Une saisie courte n'utilise qu'une fraction du champ. Mesurer la
        # dernière capture garde la caméra stable pendant les frappes et porte
        # la ligne terminée à au moins 38 % du cadre (marge pour la compression).
        key = ("cadre-saisie", json.dumps(seg, sort_keys=True), im.size)
        if key not in self.animations:
            fin = capture(fichier_capture(seg, seg["duree"]-1e-6))
            if fin.size != im.size:
                fin = fin.resize(im.size, Image.Resampling.LANCZOS)
            a = np.asarray(fin)
            x0, y0, x1, y1 = map(round, rect)
            # Écarter le contour du champ sans supprimer les soulignements.
            pad = max(1, round(im.width/1600*9))
            roi = a[y0+pad:y1-pad, x0+pad:x1-pad, :3].astype(np.int16)
            if roi.size:
                blanc = (roi.min(2) > 135) & (roi.max(2)-roi.min(2) < 60)
                xs = np.where(blanc)[1]
                largeur_texte = (xs.max()-xs.min()+1) if len(xs) else largeur
            else:
                largeur_texte = largeur
            self.animations[key] = min(largeur, largeur_texte*cible/.38)
        cadre = self.animations[key]
        cx = (rect[0]+cadre/2)/im.width
        largeur = cadre
        # Déjà serré à la première image ; poussée discrète seulement ensuite.
        part *= 1+.035*ease(t/seg["duree"])
        z = max(1, min(im.width, im.height*self.W/self.H)*part/largeur)
        # Le texte commence au bord gauche du champ : la fenêtre part de là (petite marge), sinon un fort
        # grossissement coupe le début des mots tapés.
        pw = min(im.width, im.height*self.W/self.H)/z
        cx = min(cx, (rect[0] - pw*.06 + pw/2)/im.width)
        return cx, cy, z, rect

    def plan(self, seg, t):
        f = seg.get("fichier_vertical", seg["fichier"]) if self.vertical else seg["fichier"]
        if f in seg.get("_absents", {}).values():
            return self.manquant(f)
        src = self.lecteur.image(f, temps_source(seg, t))
        cles = seg.get("cadrage_v" if self.vertical else "cadrage") or seg.get("cadrage") or [[0, .5, .5, 1]]
        cx, cy, z = interp(cles, t)
        dx, dy, px, py = 0., 0., 0., 0.
        marge = 0
        for start, amp, duree in seg.get("secousses", []):
            marge = max(marge, amp*self.s/1080)
            for q, tt in enumerate([t, t-1/IPS]):
                age = tt-start
                if 0 <= age < duree:
                    a = amp*self.s/1080*math.exp(-5*age/duree)*(1-age/duree)
                    xx, yy = a*math.cos(age*111), a*.65*math.sin(age*147+.7)
                    if q == 0:
                        dx, dy = dx+xx, dy+yy
                    else:
                        px, py = px+xx, py+yy
        # Surcadre pour ne pas dévoiler les bords pendant une secousse.
        z *= 1+2*marge/self.s
        box = boite(src, cx, cy, z, self.W, self.H)
        cx -= dx/self.W*(box[2]-box[0])/src.width
        cy -= dy/self.H*(box[3]-box[1])/src.height
        im = recadrer(src, cx, cy, z, self.W, self.H).filter(ImageFilter.UnsharpMask(radius=.8, percent=38, threshold=3))
        im = self.pellicule(im, seg, t)
        im = flou_directionnel(im, (dx-px)*.45, (dy-py)*.45)
        for start, couleur, duree in seg.get("flash", []):
            age = t-start
            if 0 <= age < duree:
                c = self.c[couleur] if isinstance(couleur, str) else tuple(couleur)
                im = Image.blend(im, Image.new("RGB", im.size, c), .85*(1-age/duree)**2)
        return im

    def sprite_boost(self, texte, taille, largeur, hauteur, couleur="os", mono=True):
        key = (texte, round(taille), round(largeur), round(hauteur), couleur, mono)
        if key not in self.sprites:
            self.sprites[key] = self.texte_calque(texte, taille, largeur, hauteur, couleur, mono)[0]
        return self.sprites[key]

    def cle_boost(self, terme):
        key = ("cle", terme)
        if key not in self.sprites:
            # Conserver la hauteur des lettres en portrait, même pour une clé
            # longue : une expression passe sur deux lignes, puis se condense
            # horizontalement si nécessaire.
            sprite, _ = self.texte_calque(terme, self.H*.20, self.W*5,
                                        self.H*.48, "signal", empile=self.vertical)
            if sprite.width > self.W*.78:
                sprite = sprite.resize((round(self.W*.78), sprite.height), Image.Resampling.LANCZOS)
            self.sprites[key] = sprite
        return self.sprites[key]

    @staticmethod
    def projeter(layer, sprite, x, y, z=1, alpha=1, angle=0):
        if alpha <= 0 or z <= 0:
            return
        w, h = max(1, round(sprite.width*z)), max(1, round(sprite.height*z))
        # Éviter le redimensionnement d'éclats déjà hors écran.
        if x+w < 0 or y+h < 0 or x-w > layer.width or y-h > layer.height:
            return
        sprite = sprite.resize((w, h), Image.Resampling.BICUBIC)
        if angle:
            sprite = sprite.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        if alpha < 1:
            sprite.putalpha(sprite.getchannel("A").point(lambda a: round(a*alpha)))
        layer.alpha_composite(sprite, (round(x-sprite.width/2), round(y-sprite.height/2)))

    def lettres_boost(self, seg):
        texte = seg.get("_mots_saisis", "")
        fautes = seg.get("_fautes", set())
        key = (texte, tuple(sorted(fautes)))
        if key in self.animations:
            return self.animations[key]
        taille = self.H*.13
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        while True:
            f = self.font(taille, True)
            lignes = couper(d, texte, f, self.W*.84)
            if len(lignes)*f.size*1.3 <= self.H*.57 or taille <= 9:
                break
            taille *= .94
        lettres, traits = [], []
        top = self.H*.49-len(lignes)*f.size*1.3/2
        for row, ligne in enumerate(lignes):
            x = (self.W-d.textlength(ligne, font=f))/2
            y = top+row*f.size*1.3
            for mot in ligne.split():
                debut = x
                for char in mot:
                    w = d.textlength(char, font=f)
                    sprite = self.sprite_boost(char, f.size, w+f.size*.3, f.size*1.2)
                    lettres.append((sprite, x+w/2, y+sprite.height/2))
                    x += w
                normal = unicodedata.normalize("NFC", mot.casefold()).strip(".,;:!?«»\"'()")
                if normal in fautes:
                    traits.append((debut, x, y+f.size*.90, f.size))
                x += d.textlength(" ", font=f)
        self.animations[key] = (lettres, traits)
        return lettres, traits

    def boost(self, seg, t):
        if seg.get("_absents") or seg.get("_captures_absentes"):
            fichiers = [*seg.get("_absents", {}).values(), *seg.get("_captures_absentes", [])]
            return self.manquant(fichiers[0])
        i, n, a, b = horloge_boost(seg, t)
        if i >= n-2:
            return Image.new("RGB", (self.W, self.H), (255, 255, 255))
        fond = self.noir()
        layer = Image.new("RGBA", fond.size)
        if i < a:
            # Deux images de tension puis rupture de chaque glyphe ; pas de faux
            # correcteur sur le prompt boosté, seulement sur la saisie du client.
            lettres, traits = self.lettres_boost(seg)
            explosion = max(0., (i/max(1, a-1)-.40)/.60)
            for k, (sprite, x, y) in enumerate(lettres):
                rng = np.random.default_rng(710+k)
                theta = rng.uniform(0, math.tau)
                vx, vy = math.cos(theta)*self.W*rng.uniform(.22, .65), math.sin(theta)*self.H*rng.uniform(.20, .65)
                spin = rng.uniform(-170, 170)
                shake = self.s*.004*(1-explosion)
                for trail in (2, 1, 0):
                    age = max(0., explosion-trail*.12)
                    xx = x+vx*age+shake*math.sin(i*7+k)
                    yy = y+vy*age+shake*math.cos(i*9+k)
                    self.projeter(layer, sprite, xx, yy, 1+age*.65,
                                  (1-age*.8)*(1 if trail == 0 else .16), spin*age)
            if not explosion:
                d = ImageDraw.Draw(layer)
                for x0, x1, yy, fs in traits:
                    points = [(x, yy+math.sin((x-x0)/max(1, fs*.055))*fs*.024)
                              for x in np.arange(x0, x1, max(1, self.s/540))]
                    if len(points) > 1:
                        d.line(points, fill=(255, 52, 65, 255), width=max(2, round(self.s*.003)))
            fond = Image.alpha_composite(fond.convert("RGBA"), layer).convert("RGB")
            if i == a-1:
                fond = Image.blend(fond, Image.new("RGB", fond.size, "white"), .78)
            return fond

        # Matière issue du texte réel : rubans gris défilants et mots en profondeur.
        u = (i-a)/max(1, b-a)
        mots = mots_boost(seg["_texte_boost"], seg.get("termes_cles", []), seg["duree"])
        for k in range(5 if self.vertical else 4):
            extrait = " ".join(seg["_texte_boost"].split()[k*14:k*14+38])
            if not extrait:
                continue
            ruban = self.sprite_boost(extrait, self.H*.019, self.W*2, self.H*.10, "brume")
            x = self.W*(.5+(.6-u*.8)*(1 if k % 2 else -1))
            y = self.H*(.19+k*.15)+math.sin(u*3+k)*self.H*.025
            self.projeter(layer, ruban, x, y, alpha=.28)
        for k, (mot, important) in enumerate(mots):
            rng = np.random.default_rng(900+k)
            theta = math.tau*(k*.61803398875 % 1)
            # Profondeur cyclique : chaque mot repart du point de fuite, puis
            # accélère vers le spectateur au lieu de s'arrêter dans une cellule.
            p = (u*1.35+k/max(1, len(mots))) % 1
            dx = math.cos(theta)*self.W*.78
            dy = math.sin(theta)*self.H*.73
            sprite = self.sprite_boost(mot, self.H*.047, self.W*.58, self.H*.19, "brume")
            opacity = min(1., p*5)*(1-.70*p)*(.65 if important else .45)
            for trail in (3, 2, 1, 0):
                pp = max(0, p-trail*.035)
                rr = pp*pp*1.1
                self.projeter(layer, sprite, self.W/2+dx*rr, self.H*.49+dy*rr,
                              .12+pp*2.4, opacity*(1 if trail == 0 else .13))
        # Les clés claquent seules au centre, très grandes, sur 2–3 images.
        cles = cles_boost(seg)
        for k, (terme, debut, fin) in enumerate(cles):
            if debut <= i < fin or (i >= b and k == len(cles)-1):
                sprite = self.cle_boost(terme)
                zoom = 1+.15*(1-ease((i-debut)/max(1, fin-debut-1)))
                self.projeter(layer, sprite, self.W*.5, self.H*.49, zoom)
        suction = ease((i-b+1)/max(1, n-2-b)) if i >= b else 0
        if suction:
            layer = recadrer(layer, .5, .49, 1+2*suction, self.W, self.H)
        fond = Image.alpha_composite(fond.convert("RGBA"), layer).convert("RGB")
        return flou_radial(fond, .32*suction) if suction else fond

    def cinetique(self, im, texte, style, t, duree, position="centre", grand=True):
        W, H = self.W, self.H
        if style == "empile":
            mots = [m for m in texte.split() if m not in {"·", "•"}]
            sprite, fs = self.texte_calque(" ".join(mots), self.s*.23, W*.84, H*.60, empile=True)
            count = min(len(mots), int(t/self.beat)+1)
            mask = Image.new("L", sprite.size)
            ImageDraw.Draw(mask).rectangle((0, 0, sprite.width, int(count*fs*1.16)), fill=255)
            sprite.putalpha(ImageChops.multiply(sprite.getchannel("A"), mask))
        else:
            hauteur = H*(.60 if grand else .20)
            if self.vertical and style == "claque":
                hauteur /= 1.35  # réserver aussi les marges pendant le dépassement initial
            sprite, _ = self.texte_calque(texte, self.s*(.29 if grand else .064), W*.84, hauteur)
        if style == "claque":
            z = 1+.35*(1-ease(t/(4/IPS)))
            sprite = sprite.resize((int(sprite.width*z), int(sprite.height*z)), Image.Resampling.BICUBIC)
            if t < 4/IPS:
                sprite = flou_directionnel(sprite, (z-1)*22*self.s/1080, (z-1)*5*self.s/1080)
            if position == "centre":
                a = math.exp(-t*27)*.009
                position = [.5+a*math.sin(t*173), (.46 if self.vertical else .5)+a*math.cos(t*137)]
        elif style == "balayage":
            mask = Image.new("L", sprite.size)
            ImageDraw.Draw(mask).rectangle((0, 0, int(sprite.width*ease(t/.27)), sprite.height), fill=255)
            sprite.putalpha(ImageChops.multiply(sprite.getchannel("A"), mask))
        alpha = 1. if grand else min(1., t/.08, (duree-t)/.10)
        if not grand:
            pad = int(self.s*.016)
            bg = Image.new("RGBA", (sprite.width+pad*2, sprite.height+pad*2), (*self.c["encre"], 220))
            bg.alpha_composite(sprite, (pad, pad))
            sprite = bg
        return self.place(im, sprite, position, alpha)

    def titre(self, seg, t):
        fond = self.noir()
        if seg.get("sur_video"):
            ref = seg["sur_video"]
            if isinstance(ref, str):
                idx = seg["_index"]+(-1 if ref in {"precedent", "précédent"} else 1)
                other = self.m["segments"][idx]
                start = max(0, other["duree"]-seg["duree"]) if idx < seg["_index"] else 0
                fond = self.image(other, start+t, overlays=False, profondeur=1)
            else:
                fond = self.source(ref, t)
            fond = Image.blend(fond, self.noir(), .20)
        return self.cinetique(fond, self.texte(seg["texte_id"]), seg.get("style", "claque"), t, seg["duree"])

    def chapitre(self, seg, t):
        media = seg["media"]
        cw = int(self.W*(.92 if self.vertical else .86))
        ch = int(self.H*(.40 if self.vertical else .61))
        panel = self.source(media, t, cw, ch, decouper_zone=True)
        panel = recadrer(panel, .5, .5, 1+.06*t/seg["duree"], cw, ch)
        fond = self.source(media, t, decouper_zone=True).filter(ImageFilter.GaussianBlur(self.s*.022))
        fond = Image.blend(self.noir(), fond, .28)
        u = ease(t/(3/IPS))
        panel = panel.resize((round(cw*(.92+.08*u)), round(ch*(.92+.08*u))), Image.Resampling.LANCZOS)
        y = int(self.H*.56-panel.height/2+(1-u)*self.H*.055)
        x = (self.W-panel.width)//2
        fond.paste(panel, (x, y))
        d = ImageDraw.Draw(fond)
        for side in (-1, 1):
            xx = self.W/2+side*(cw/2+self.W*.016+(1-u)*self.W*.10)
            for k in (0, 1):
                xxk = xx+side*k*self.s*.012
                h = self.s*.024
                d.line([(xxk-side*h*.5, self.H*.56-h), (xxk+side*h*.5, self.H*.56), (xxk-side*h*.5, self.H*.56+h)], fill=self.c["signal"], width=max(2, int(self.s*.005)))
        titre = self.titre_chapitre(self.texte(seg["texte_id"]))
        fond.paste(titre, ((self.W-titre.width)//2, round(self.H*(.11 if self.vertical else .065))), titre)
        if seg.get("en_preparation"):
            self.etiquette(fond, self.b["carton"]["preparation_id"], x, min(self.H*.77, y+panel.height+self.s*.025))
        return fond

    def titre_chapitre(self, texte):
        # Geist 900, un mot signal ; retour à la ligne autorisé en portrait.
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        taille = self.H*.14  # hauteur visible des capitales ≈ 10 % du cadre
        while True:
            f = self.font(taille, graisse=900)
            lignes = couper(d, texte, f, self.W*.90)
            hauteur = len(lignes)*f.size*1.12
            if (hauteur <= self.H*(.235 if self.vertical else .18)
                    and max(d.textlength(l, font=f) for l in lignes) <= self.W*.90) or taille <= 9:
                break
            taille *= .95
        sprite = Image.new("RGBA", (round(self.W*.92), math.ceil(hauteur)))
        d = ImageDraw.Draw(sprite)
        mots = texte.split()
        compteur = 0
        for row, ligne in enumerate(lignes):
            x = (sprite.width-d.textlength(ligne, font=f))/2
            for mot in ligne.split():
                c = "signal" if len(mots) == 2 and compteur == 1 else "os"
                d.text((x, row*f.size*1.12), mot, font=f, anchor="lt", fill=self.c[c])
                x += d.textlength(mot+" ", font=f)
                compteur += 1
        return sprite

    def avant_apres(self, seg, t):
        layers = seg["couches"]
        u = min(len(layers)-1-1e-7, max(0., t/max(1/IPS, seg["duree"]-1/IPS)*(len(layers)-1)))
        k = int(u)
        im = self.source(layers[k], t)
        following = self.source(layers[k+1], t)
        v = ease(u-k)
        mask = Image.new("L", im.size)
        d = ImageDraw.Draw(mask)
        edge = int((self.H if self.vertical else self.W)*v)
        if self.vertical:
            d.rectangle((0, 0, self.W, edge), fill=255)
        else:
            d.rectangle((0, 0, edge, self.H), fill=255)
        im = Image.composite(following, im, mask)
        d = ImageDraw.Draw(im)
        d.line([(0, edge), (self.W, edge)] if self.vertical else [(edge, 0), (edge, self.H)], fill=self.c["signal"], width=max(2, int(self.s*.004)))
        for j, layer in enumerate(layers):
            id_ = layer.get("texte_id") if isinstance(layer, dict) else None
            id_ = id_ or (["brut", "final"] if len(layers) == 2 else ["brut", "masque", "final"])[j]
            self.etiquette(im, id_, self.W*(.06+j*.30), self.H*(.13 if self.vertical else .07), "signal" if j == k+1 else "os")
        return im

    def mosaique(self, seg, t):
        im = self.noir()
        sources = seg["rushes"]
        n = len(sources)
        gap = max(2, int(self.s*.009))
        cols = 1 if self.vertical else math.ceil(math.sqrt(n*16/9))
        rows = math.ceil(n/cols)
        top, bottom = (int(self.H*.12), int(self.H*.80)) if self.vertical else (gap, self.H-gap)
        cw, ch = (self.W-(cols+1)*gap)//cols, (bottom-top-(rows-1)*gap)//rows
        for k, src in enumerate(sources):
            start = seg.get("temps", [j*self.beat for j in range(n)])[k]
            if t < start:
                continue
            age = t-start
            tile = self.source(src, age, cw, ch)
            tile = Image.blend(Image.new("RGB", tile.size, self.c["encre"]), tile, ease(age/.12))
            x = gap+(k % cols)*(cw+gap)
            y = top+(k//cols)*(ch+gap)+int((1-ease(age/.18))*ch*.15)
            im.paste(tile, (x, y))
        return im

    def carton(self, seg, t):
        im = self.noir()
        alpha = ease(t/.22)
        if "logo" in self.b.get("_absents", {}):
            return self.manquant(self.b["logo"])
        if self.b.get("logo"):
            with Image.open(self.b["logo"]) as logo:
                logo = logo.convert("RGBA")
            logo.thumbnail((int(self.W*.72), int(self.H*.19)), Image.Resampling.LANCZOS)
            self.place(im, logo, [.5, .30], alpha)
        else:
            name, _ = self.texte_calque(self.b["nom"], self.s*.16, self.W*.86, self.H*.17)
            product, _ = self.texte_calque(self.b["produit"], self.s*.13, self.W*.86, self.H*.14, "signal")
            self.place(im, name, [.5, .27], alpha)
            self.place(im, product, [.5, .37], alpha)
        carton = self.b["carton"]
        slogan, _ = self.texte_calque(self.texte(carton["slogan_id"]), self.s*.085, self.W*.86, self.H*.18)
        self.place(im, slogan, [.5, .53], ease((t-.10)/.25))
        if self.b.get("url"):
            url, _ = self.texte_calque(self.b["url"], self.s*.030, self.W*.80, self.H*.06, "signal", True)
            self.place(im, url, [.5, .67], alpha)
        mentions, _ = self.texte_calque(self.texte(carton["mentions_id"]), self.s*.018, self.W*.82, self.H*.07, "brume", True)
        return self.place(im, mentions, [.5, .77 if self.vertical else .86], alpha)

    def poser_textes(self, im, textes, t):
        for x in textes:
            if self.langue not in x.get("langues", [self.langue]):
                continue
            age = t-x["t"]
            if 0 <= age < x["duree"]:
                im = self.cinetique(im, self.texte(x["texte_id"]), x.get("style", "legende"), age, x["duree"], x.get("position", "bas"), x.get("style") in {"grand", "claque", "balayage", "empile"})
        return im

    def image(self, seg, t, overlays=True, profondeur=0):
        typ = seg["type"]
        if profondeur and typ == "titre":
            raise ValueError("sur_video doit désigner un média, pas un autre titre")
        if typ == "noir":
            im = self.noir()
            if seg.get("texte_id"):
                im = self.cinetique(im, self.texte(seg["texte_id"]), seg.get("style", "balayage"), t, seg["duree"])
        else:
            im = getattr(self, typ)(seg, t)
        if overlays:
            im = self.poser_textes(im, seg.get("textes", []), t)
            im = self.poser_textes(im, self.m.get("textes", []), seg["debut"]+t)
        return im.convert("RGB")


def rendre_segment(task):
    m, marque, fmt, langue, brouillon, seg, i0, i1, sortie = task
    rendu = Rendu(m, marque, fmt, langue, brouillon)
    sortie = Path(sortie)
    tmp = sortie.with_suffix(f".{os.getpid()}.part.mp4")
    log = tmp.with_suffix(".log")
    try:
        with log.open("wb") as err:
            enc = subprocess.Popen([FFMPEG, "-hide_banner", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{rendu.W}x{rendu.H}",
                                    "-r", str(IPS), "-i", "pipe:0", "-an", "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "16", "-profile:v", "high",
                                    "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(tmp)], stdin=subprocess.PIPE, stderr=err)
            try:
                for i in range(i0, i1):
                    # Les limites sont quantifiées globalement, puis le temps local reste
                    # relatif au début JSON : aucune dérive cumulée entre les coupes.
                    t = max(0., i/IPS-seg["debut"])
                    enc.stdin.write(rendu.image(seg, t).tobytes())
                enc.stdin.close()
                if enc.wait():
                    raise RuntimeError(log.read_text()[-2500:])
            except BaseException:
                enc.terminate()
                enc.wait()
                raise
        tmp.replace(sortie)
    finally:
        tmp.unlink(missing_ok=True)
        log.unlink(missing_ok=True)
    return str(sortie)


def lire_audio(f, debut=0., duree=None):
    args = ["-ss", max(0., debut), "-i", f, "-vn"]
    if duree is not None:
        args += ["-t", max(.0001, duree)]
    raw = ff(args+["-threads", "1", "-f", "f32le", "-ac", "2", "-ar", SR, "pipe:1"]).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, 2).copy()


def poser(piste, son, t, db=0.):
    i = int(round(t*SR))
    source = max(0, -i)
    cible = max(0, i)
    n = min(len(son)-source, len(piste)-cible)
    if n > 0:
        piste[cible:cible+n] += son[source:source+n]*10**(db/20)


def fondre(son, duree=.01):
    n = min(len(son)//2, int(duree*SR))
    if n:
        son[:n] *= np.linspace(0, 1, n)[:, None]
        son[-n:] *= np.linspace(1, 0, n)[:, None]
    return son


def musique(m, n):
    piste = np.zeros((n, 2), np.float32)
    mu = m.get("musique")
    if not mu or "fichier" in mu.get("_absents", {}):
        return piste
    coupes = {0.: mu.get("entree", 0.)}
    coupes.update({float(t): float(s) for t, s in mu.get("coupes", [])})
    points = sorted(coupes.items())
    for k, (start, source) in enumerate(points):
        end = points[k+1][0] if k+1 < len(points) else n/SR
        a, b = max(0, start-(.015 if k else 0)), min(n/SR, end+(.015 if k+1 < len(points) else 0))
        if b <= a:
            continue
        # Fondu centré sur la coupe, sans déplacer la phase de la musique suivante.
        entree = source+a-start
        silence = max(0., -entree)
        son = lire_audio(mu["fichier"], max(0., entree), b-a-silence)
        if silence:
            son = np.concatenate([np.zeros((int(round(silence*SR)), 2), np.float32), son])
        tt = a+np.arange(len(son))/SR
        gain = np.ones(len(son))
        if k:
            gain *= np.clip((tt-start+.015)/.030, 0, 1)
        if k+1 < len(points):
            gain *= np.clip((end+.015-tt)/.030, 0, 1)
        poser(piste, son*gain[:, None], a, mu.get("gain_db", mu.get("gain", 0.)))
    # Temps film, après les coupes de source. Les 15 ms se trouvent à
    # l'extérieur du trou : toute la plage demandée reste strictement muette.
    gain = np.ones(n, np.float32)
    for debut, fin in mu.get("trous", []):
        a, b = max(0, math.floor((debut-.015)*SR)), min(n, math.ceil((fin+.015)*SR)+1)
        if b > a:
            tt = np.arange(a, b)/SR
            enveloppe = np.clip(np.maximum((debut-tt)/.015, (tt-fin)/.015), 0, 1)
            gain[a:b] = np.minimum(gain[a:b], enveloppe)
    return piste*gain[:, None]


def evenements_auto(m):
    events = []
    for seg in m["segments"]:
        if seg.get("sfx_auto", True) is False:
            continue
        t = seg["debut"]
        if seg["type"] == "saisie":
            if "dossier" in seg.get("_absents", {}):
                continue
            rows = sequence(seg["dossier"], tuple(seg.get("etapes", ["vide", "saisie", "saisie-fin", "survol"])), seg["duree"])
            vus = set()
            for ti, _, etape in rows:
                image = math.ceil((t+ti)*IPS-1e-8)
                if etape == "saisie" and image not in vus:
                    events.append({"t": image/IPS, "type": "clavier", "db": seg.get("clavier_db", -20), "duree": .065})
                    vus.add(image)
        elif seg["type"] == "boost":
            events += [{"t": t, "type": "souffle", "db": -11, "duree": seg["duree"]}, {"t": t, "type": "riser", "db": -14, "duree": seg["duree"]}]
        elif seg["type"] == "titre" and seg.get("style", "claque") == "claque":
            events.append({"t": t, "type": "impact", "db": -9, "duree": min(.8, seg["duree"])})
    return events


def ducking(n, intervalles, db=7.):
    g = np.ones(n, np.float32)
    for debut, fin in intervalles:
        a, b = max(0, int((debut-.060)*SR)), min(n, int((fin+.250)*SR))
        if b <= a:
            continue
        t = np.arange(a, b)/SR
        depth = np.minimum(np.clip((t-debut+.060)/.060, 0, 1), np.clip((fin+.250-t)/.250, 0, 1))
        g[a:b] = np.minimum(g[a:b], 10**(-db*depth/20))
    return g


def mixer(m, langue, fmt, frames, de=0, fin=None):
    n = int(round(frames/IPS*SR))
    piste = np.zeros((n, 2), np.float32)
    voix = m.get("voix", [])
    if isinstance(voix, dict):
        voix = voix.get(langue, [])
    intervalles = []
    for v in voix:
        if langue not in v.get("langues", [langue]):
            continue
        if "fichier" in v.get("_absents", {}):
            continue
        dossier = m.get("dossiers_voix", {}).get(langue)
        f = v.get("fichier") or str(Path(dossier)/f"{v['id']}.wav")
        son = lire_audio(f)
        poser(piste, fondre(son.copy(), .005), v["t"], v.get("db", 0.))
        intervalles.append((v["t"], v["t"]+len(son)/SR))
    piste += musique(m, n)*ducking(n, intervalles, (m.get("musique") or {}).get("ducking_db", 7.))[:, None]
    for seg in m["segments"]:
        if seg["type"] != "plan" or seg.get("son_db") is None:
            continue
        f = seg.get("fichier_vertical", seg["fichier"]) if fmt == "9x16" else seg["fichier"]
        if f in seg.get("_absents", {}).values():
            continue
        if not any(s["codec_type"] == "audio" for s in sonder(f)["streams"]):
            print(f"Son natif absent : {f}", file=sys.stderr)
            continue
        # Même temps local que pour la vidéo, y compris les coupes arrondies à 24 i/s.
        a, b = round(seg["debut"]*IPS), round((seg["debut"]+seg["duree"])*IPS)
        tt = np.arange(int((b-a)/IPS*SR))/SR+a/IPS-seg["debut"]
        positions = temps_source(seg, np.maximum(0, tt))
        lo, hi = max(0., float(positions.min())-.002), float(positions.max())+.002
        raw = lire_audio(f, lo, hi-lo)
        if not len(raw):
            continue
        x = (positions-lo)*SR
        son = np.stack([np.interp(x, np.arange(len(raw)), raw[:, c], left=0, right=0) for c in (0, 1)], 1).astype(np.float32)
        poser(piste, fondre(son, .010), a/IPS, seg["son_db"])
    for k, x in enumerate([*evenements_auto(m), *m.get("sfx", [])]):
        if langue not in x.get("langues", [langue]):
            continue
        rng = np.random.default_rng(4000+k)
        duree = x.get("duree", {"clavier": .065, "whoosh": .20, "impact": .8, "riser": 1., "sub": 1.}.get(x["type"], 1.))
        son = sfx_v6.generer(x["type"], duree, rng)
        poser(piste, fondre(son, .003), x["t"], x.get("db", 0.))
    return piste[int(de/IPS*SR):int((fin if fin is not None else frames)/IPS*SR)]


def analyser_audio(fichier, master="web"):
    i, tp = (-14, -1.5) if master == "web" else (-10, -1)
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", "-i", str(fichier), "-vn", "-af", f"loudnorm=I={i}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors="replace")[-2500:])
    s = r.stderr.decode()
    return json.loads(s[s.rfind("{"):s.rfind("}")+1])


def masteriser(son, sortie, master, marge=.3):
    i, plafond = (-14, -1.5) if master == "web" else (-10, -1)
    # Marge de 0,3 dB pour les crêtes interéchantillons après codage AAC.
    tp = plafond-marge
    base = ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "pipe:0"]
    raw = son.astype("<f4").tobytes()
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostdin", *base, "-af", f"loudnorm=I={i}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"], input=raw, capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors="replace")[-2000:])
    s = r.stderr.decode()
    j = json.loads(s[s.rfind("{"):s.rfind("}")+1])
    if not math.isfinite(float(j["input_i"])):
        filtre = "anull"
    else:
        filtre = (f"loudnorm=I={i}:TP={tp}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
                  f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    ff(base+["-af", filtre, "-ar", SR, "-c:a", "pcm_f32le", sortie], input=raw)
    # Sur les montages courts, loudnorm peut rester sous sa consigne quand ses
    # transitoires rencontrent le plafond. Calibrer le WAV réellement produit,
    # avec un limiteur suréchantillonné pour réduire le facteur de crête.
    # La latence du limiteur est compensée : les attaques restent sur les coupes.
    if math.isfinite(float(j["input_i"])):
        for _ in range(12):
            mesure = analyser_audio(sortie, master)
            delta = i-float(mesure["input_i"])
            if abs(delta) <= .10:
                break
            temporaire = Path(sortie).with_name("master-calibration.wav")
            filtre = (f"aresample=192000,volume={delta}dB,"
                      f"alimiter=limit={10**(tp/20)}:attack=5:release=80:level=false:latency=true,aresample={SR}")
            ff(["-i", sortie, "-af", filtre, "-t", len(son)/SR, "-c:a", "pcm_f32le", temporaire])
            temporaire.replace(sortie)
        mesure = analyser_audio(sortie, master)
        if abs(i-float(mesure["input_i"])) > .15:
            raise RuntimeError(f"Master hors cible après calibration : {mesure['input_i']} LUFS (cible {i})")
    return j


def valider_cles(cles, largeur, nom, minimum=None):
    if not isinstance(cles, list) or not cles:
        raise ValueError(f"{nom} : liste de clés vide")
    last = -math.inf
    for c in cles:
        if len(c) != largeur or not all(isinstance(x, (float, int)) and math.isfinite(x) for x in c) or c[0] < 0 or c[0] <= last:
            raise ValueError(f"{nom} : clés croissantes [t, …] requises")
        if minimum is not None and c[-1] < minimum:
            raise ValueError(f"{nom} : dernière valeur ≥ {minimum} requise")
        if largeur == 4 and not (0 <= c[1] <= 1 and 0 <= c[2] <= 1):
            raise ValueError(f"{nom} : centre normalisé attendu")
        last = c[0]


def charger(fichier, langue, tolerant=False):
    fichier = chemin(fichier, Path.cwd())
    brut = json.loads(fichier.read_text())
    if isinstance(brut.get("voix"), dict):
        brut["voix"] = brut["voix"].get(langue, [])
    m = resoudre(brut, fichier.parent, langue)
    marque_path = chemin(m.get("marque", "marque-v6.json"), fichier.parent)
    marque = resoudre(json.loads(marque_path.read_text()), marque_path.parent)
    for key in ("titre", "mono"):
        marque["polices"][key] = str(chemin(marque["polices"][key], marque_path.parent))
        police(marque["polices"][key], 16)
    m["dossiers_voix"] = {k: str(chemin(v, fichier.parent)) for k, v in m.get("dossiers_voix", {}).items()}
    if langue not in marque.get("textes", marque.get("langues", {})):
        raise ValueError(f"Langue de marque absente : {langue}")
    if not m.get("segments") or m.get("bpm", 124.8) <= 0:
        raise ValueError("Liste de segments et BPM positif requis")
    def source_obj(v):
        return {"fichier": str(chemin(v, fichier.parent))} if isinstance(v, str) else v
    for s in m["segments"]:
        for key in ("couches", "rushes"):
            if key in s:
                s[key] = [source_obj(v) for v in s[key]]
        if "media" in s:
            s["media"] = source_obj(s["media"])
    deps = set(marque["polices"][k] for k in ("titre", "mono"))
    absents = set()
    def absent(obj, key, p):
        if not tolerant or key == "boost_json":
            raise ValueError(f"Source absente : {p}")
        if str(p) not in absents:
            print(f"Avertissement : média absent, animatique : {p}", file=sys.stderr)
        absents.add(str(p))
        obj.setdefault("_absents", {})[key] = str(p)

    def fichiers(obj):
        if isinstance(obj, list):
            for v in obj:
                fichiers(v)
        elif isinstance(obj, dict):
            if langue not in obj.get("langues", [langue]):
                return
            for k, v in list(obj.items()):
                if k.startswith("_"):
                    continue
                if k in PATH_KEYS and isinstance(v, str):
                    p = Path(v)
                    if not p.exists():
                        absent(obj, k, p)
                        continue
                    if p.is_dir():
                        deps.update(str(f) for f in p.iterdir() if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".json", ".jsonl"})
                    else:
                        deps.add(str(p))
                else:
                    fichiers(v)
    fichiers(m)
    fichiers(marque)

    def verifier_captures(obj, etapes, duree):
        if "dossier" in obj.get("_absents", {}):
            return
        try:
            rows = sequence(obj["dossier"], tuple(etapes), duree)
        except CapturesAbsentes:
            # Seul le dossier sans captures est assimilé à un média absent.
            absent(obj, "dossier", obj["dossier"])
            return
        for _, f, _ in rows:
            if not Path(f).is_file():
                if not tolerant:
                    raise ValueError(f"Source absente : {f}")
                if f not in absents:
                    print(f"Avertissement : capture absente, animatique : {f}", file=sys.stderr)
                absents.add(f)
                obj.setdefault("_captures_absentes", []).append(f)

    def verifier_sources(obj, duree):
        if isinstance(obj, list):
            for v in obj:
                verifier_sources(v, duree)
        elif isinstance(obj, dict):
            if "dossier" in obj and not (obj.get("type") == "boost" and "fichier" in obj):
                obj.setdefault("duree", duree)
                etapes = ["boost"] if obj.get("type") == "boost" else obj.get("etapes", ["vide", "saisie", "saisie-fin", "survol"])
                verifier_captures(obj, etapes, obj["duree"])
            for k, v in list(obj.items()):
                if not k.startswith("_"):
                    verifier_sources(v, duree)

    segs, end = [], 0
    for s in sorted(m["segments"], key=lambda s: s["debut"]):
        s = dict(s)
        if s["type"] not in TYPES or not all(math.isfinite(s[k]) for k in ("debut", "duree")) or s["debut"] < 0 or s["duree"] <= 0:
            raise ValueError(f"Segment invalide : {s}")
        a, b = round(s["debut"]*IPS), round((s["debut"]+s["duree"])*IPS)
        if b <= a or a < end:
            raise ValueError("Segments superposés ou durée inférieure à une image ; utiliser sur_video pour un titre")
        if a > end:
            segs.append({"type": "noir", "debut": end/IPS, "duree": (a-end)/IPS})
        if s.get("style", "claque") not in STYLES:
            raise ValueError(f"Style inconnu : {s['style']}")
        if s.get("etalonnage", "neutre") not in PRESETS:
            raise ValueError(f"Étalonnage inconnu : {s['etalonnage']}")
        verifier_sources(s, s["duree"])
        if s["type"] == "saisie":
            zoom_texte = s.get("zoom_texte", 1)
            if not isinstance(zoom_texte, (int, float)) or not math.isfinite(zoom_texte) or zoom_texte <= 0:
                raise ValueError("saisie.zoom_texte : nombre positif fini requis")
            for nom in ("zone", "zone_texte"):
                if nom in s and (not isinstance(s[nom], list) or len(s[nom]) != 4
                        or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in s[nom])
                        or not s[nom][0] < s[nom][2] or not s[nom][1] < s[nom][3]):
                    raise ValueError(f"saisie.{nom} : [x0,y0,x1,y1] CSS non vide requis")
        for cadre in ("cadrage", "cadrage_v"):
            if cadre in s:
                valider_cles(s[cadre], 4, cadre, 1.)
        v = s.get("vitesse", 1.)
        if isinstance(v, list):
            valider_cles(v, 2, "vitesse", .001)
        elif not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
            raise ValueError("Vitesse strictement positive ; utiliser inverse pour le retour arrière")
        if s["type"] == "plan":
            for f in {s["fichier"], s.get("fichier_vertical", s["fichier"])}:
                if f in s.get("_absents", {}).values():
                    continue
                d = duree_media(f)
                if s.get("inverse") and "entree" not in s:
                    s["entree"] = d-1/IPS
                pos = temps_source(s, np.array([0., max(0., (b-1)/IPS-s["debut"])]))
                if pos.min() < -1e-6 or pos.max() >= d:
                    raise ValueError(f"Plan hors rush ({f}) : source {pos.tolist()}, durée {d}")
        elif s["type"] == "boost":
            data = {}
            boost_fichier = s.get("boost_json") or (str(Path(s["dossier"])/"boost.json") if "dossier" in s else None)
            if boost_fichier and Path(boost_fichier).is_file():
                data = json.loads(Path(boost_fichier).read_text())
                s["boost_json"] = boost_fichier
            if s.get("texte"):
                texte = s["texte"].get(langue) if isinstance(s["texte"], dict) else s["texte"]
            elif s.get("_absents") or s.get("_captures_absentes"):
                texte = ""  # Le média sera remplacé par son noir étiqueté.
            else:
                texte = data.get("boost")
            if (not isinstance(texte, str) or not texte.strip()) and not s.get("_absents") and not s.get("_captures_absentes"):
                raise ValueError("Texte boost réel absent")
            s["_texte_boost"] = texte
            mots = s.get("mots", data.get("mots", ""))
            if isinstance(mots, list) and all(isinstance(m, str) for m in mots):
                mots = " ".join(mots)
            fautes = s.get("fautes", data.get("fautes"))
            if not isinstance(mots, str) or (fautes is not None and
                    (not isinstance(fautes, list) or not all(isinstance(m, str) for m in fautes))):
                raise ValueError("boost : mots chaîne/liste et fautes liste de mots requis")
            s["_mots_saisis"] = mots
            s["_fautes"] = sorted(fautes_boost(mots, fautes))
        elif s["type"] == "chapitre":
            s["media"].setdefault("duree", s["duree"])
        elif s["type"] == "avant_apres" and len(s["couches"]) not in {2, 3}:
            raise ValueError("avant_apres : deux ou trois couches requises")
        elif s["type"] == "mosaique" and not 3 <= len(s["rushes"]) <= 9:
            raise ValueError("mosaique : trois à neuf rushes requis")
        segs.append(s)
        end = b
    total = round(m.get("duree", end/IPS)*IPS)
    if total < end:
        raise ValueError("Durée totale plus courte que les segments")
    if total > end:
        segs.append({"type": "noir", "debut": end/IPS, "duree": (total-end)/IPS})
    for k, s in enumerate(segs):
        s["_index"] = k
        ref = s.get("sur_video")
        if isinstance(ref, str):
            if ref not in {"precedent", "précédent", "suivant"}:
                raise ValueError("sur_video : precedent, suivant, ou source objet")
            idx = k+(-1 if ref in {"precedent", "précédent"} else 1)
            if not 0 <= idx < len(segs) or segs[idx]["type"] != "plan":
                raise ValueError("sur_video adjacent : un segment plan doit exister à cet endroit")
    m["segments"] = segs
    # Contrôle des identifiants avant de lancer un rendu coûteux.
    L = marque.get("textes", marque.get("langues", {}))[langue]
    def verifier_textes(obj):
        if isinstance(obj, list):
            for v in obj:
                verifier_textes(v)
        elif isinstance(obj, dict):
            if "langues" in obj and langue not in obj["langues"]:
                return
            for k, v in obj.items():
                if (k == "texte_id" or k.endswith("_id")) and k != "id" and isinstance(v, str) and v not in L:
                    raise ValueError(f"Texte de marque absent ({langue}) : {v}")
                verifier_textes(v)
    verifier_textes(m)
    verifier_textes(marque.get("carton", {}))
    for s in segs:
        if s["type"] == "avant_apres":
            for id_ in (["brut", "final"] if len(s["couches"]) == 2 else ["brut", "masque", "final"]):
                if id_ not in L:
                    raise ValueError(f"Texte de marque absent : {id_}")
    for mu_t, mu_s in (m.get("musique") or {}).get("coupes", []):
        if mu_t < 0 or mu_s < 0 or not math.isfinite(mu_t+mu_s):
            raise ValueError("Coupes musique : instants positifs finis requis")
    mu = m.get("musique") or {}
    for trou in mu.get("trous", []):
        if (not isinstance(trou, (list, tuple)) or len(trou) != 2
                or not all(isinstance(t, (int, float)) and math.isfinite(t) for t in trou)
                or not 0 <= trou[0] < trou[1]):
            raise ValueError("Trous musique : [début, fin] finis, 0 ≤ début < fin requis")
    db = mu.get("ducking_db", 7.)
    if not isinstance(db, (int, float)) or not math.isfinite(db) or db < 0:
        raise ValueError("musique.ducking_db : atténuation positive ou nulle finie requise")
    for v in (m.get("voix", {}).get(langue, []) if isinstance(m.get("voix"), dict) else m.get("voix", [])):
        if langue not in v.get("langues", [langue]):
            continue
        dossier = m.get("dossiers_voix", {}).get(langue)
        if not v.get("fichier") and not dossier:
            raise ValueError(f"Dossier de voix absent pour {langue}")
        f = Path(v.get("fichier") or str(Path(dossier)/f"{v['id']}.wav"))
        v["fichier"] = str(f)
        if not f.is_file():
            absent(v, "fichier", f)
            continue
        deps.add(str(f))
    fichiers(m)  # médias normalisés et données boost inclus dans l'empreinte
    m["_medias_absents"] = sorted(absents)
    stats = [(f, Path(f).stat().st_size, Path(f).stat().st_mtime_ns) for f in sorted(deps)]
    return m, marque, total, stats


def construire(args):
    start = time.perf_counter()
    m, marque, total, deps = charger(args.montage, args.langue, args.tolerant)
    de = max(0, round(args.de*IPS))
    fin = min(total, round(args.a*IPS)) if args.a is not None else total
    if fin <= de:
        raise ValueError("Plage --de/--a vide")
    if args.jobs < 1:
        raise ValueError("--jobs doit être positif")
    sortie = ecriture(args.sortie)
    sortie_exclusive(sortie)
    CACHE.mkdir(parents=True, exist_ok=True)
    segments_dir = CACHE / "segments"
    segments_dir.mkdir(exist_ok=True)
    code = hashlib.sha256(b"".join((ICI/f).read_bytes() for f in ("monter_v6.py", "effets_v6.py", "sfx_v6.py"))).hexdigest()
    commun = [m, marque, args.format, args.langue, args.brouillon, deps, code]
    tasks = []
    for s in m["segments"]:
        i0, i1 = max(de, round(s["debut"]*IPS)), min(fin, round((s["debut"]+s["duree"])*IPS))
        if i1 <= i0:
            continue
        cle = hashlib.sha256(json.dumps([commun, s, i0, i1], sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]
        cache = segments_dir / f"{cle}.mp4"
        tasks.append((m, marque, args.format, args.langue, args.brouillon, s, i0, i1, str(cache)))
    faire = [task for task in tasks if not Path(task[-1]).exists()]
    print(f"{args.format} {args.langue} : {(fin-de)/IPS:.3f}s, {len(faire)}/{len(tasks)} segments à rendre, {args.jobs} processus CPU", flush=True)
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(rendre_segment, task): task for task in faire}
        for future in as_completed(futures):
            f = future.result()
            task = futures[future]
            print(f"  {task[5]['type']} terminé ({Path(f).stat().st_size/1e6:.1f} Mo)", flush=True)
    work = CACHE / 'essais' / f'{sortie.stem}-{uuid.uuid4().hex}'
    work.mkdir(parents=True, exist_ok=False)
    liste = work / 'segments.txt'
    essais_path = work / 'calibrations.jsonl'
    plafond = -1.5 if args.master == "web" else -1.
    cible = -14 if args.master == "web" else -10
    marge = .3
    essais_calibration = []
    loud = None
    try:
        liste.write_text("".join("file '"+task[-1].replace("'", "'\\''")+"'\n" for task in tasks))
        son = mixer(m, args.langue, args.format, total, de, fin)
        for numero in range(1, 5):
            # Chaque passe garde son WAV et son film pour comparer les calibrations
            # et préserver les tentatives même si une passe suivante échoue.
            wav = work / f'master-{numero:02d}.wav'
            mux = work / f'film-{numero:02d}.mp4'
            essai = {'calibration': numero, 'master_wav': str(wav), 'film_aac': str(mux),
                     'marge_db': round(marge, 3), 'etat': 'en_cours'}
            essais_calibration.append(essai)
            with essais_path.open('a', encoding='utf-8') as journal:
                journal.write(json.dumps(essai, ensure_ascii=False)+'\n')
                journal.flush()
                os.fsync(journal.fileno())
            masteriser(son, wav, args.master, marge)
            ff(["-f", "concat", "-safe", "0", "-i", liste, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                "-ar", SR, "-t", (fin-de)/IPS, "-movflags", "+faststart", "-metadata", f"language={args.langue}", mux])
            loud = analyser_audio(mux, args.master)
            essai.update(etat='termine', loudness_aac=loud, plafond_dbTP=plafond, cible_lufs=cible)
            with essais_path.open('a', encoding='utf-8') as journal:
                journal.write(json.dumps(essai, ensure_ascii=False)+'\n')
                journal.flush()
                os.fsync(journal.fileno())
            if float(loud["input_tp"]) <= plafond:
                break
            marge += float(loud["input_tp"])-plafond+.2
        else:
            raise RuntimeError(f"Crête AAC hors plafond après calibration : {loud['input_tp']} dBTP")
        if math.isfinite(float(loud["input_i"])) and abs(float(loud["input_i"])-cible) > .25:
            raise RuntimeError(f"Loudness AAC hors cible : {loud['input_i']} LUFS (cible {cible})")
        copier_exclusif(mux, sortie)
    except BaseException as exc:
        for essai in essais_calibration:
            if essai['etat'] == 'en_cours':
                essai.update(etat='echec', erreur=f'{type(exc).__name__}: {exc}')
        rapport_travail = work / 'rapport-echec.json'
        rapport_echec = {'etat': 'echec', 'erreur': f'{type(exc).__name__}: {exc}', 'essais_dir': str(work),
                         'journal_calibrations': str(essais_path), 'film': str(sortie),
                         'rapport_echec': str(rapport_travail), 'essais_calibration': essais_calibration}
        with essais_path.open('a', encoding='utf-8') as journal:
            journal.write(json.dumps(rapport_echec, ensure_ascii=False)+'\n')
            journal.flush()
            os.fsync(journal.fileno())
        ecrire_exclusif(rapport_travail, json.dumps(rapport_echec, ensure_ascii=False, indent=2)+'\n')
        rapport_path = sortie.with_suffix('.rendu.json')
        try:
            ecrire_exclusif(rapport_path, json.dumps(rapport_echec, ensure_ascii=False, indent=2)+'\n')
        except FileExistsError:
            # Une sortie concurrente ne doit jamais être remplacée. Le journal
            # de l'essai contient le statut et les chemins de conservation.
            pass
        if isinstance(exc, KeyboardInterrupt):
            print(f"Essais de calibration conservés dans {work}; rapport : {rapport_travail}", file=sys.stderr, flush=True)
            raise
        raise RuntimeError(f"{exc}; essais de calibration conservés dans {work}; rapport d'échec : {rapport_travail}") from exc
    elapsed = time.perf_counter()-start
    rapport = {"film": str(sortie), "format": args.format, "langue": args.langue, "brouillon": args.brouillon, "master": args.master,
               "de": de/IPS, "a": fin/IPS, "duree": (fin-de)/IPS, "images": fin-de, "segments_rendus": len(faire), "segments_cache": len(tasks)-len(faire),
               "temps_rendu_s": round(elapsed, 3), "secondes_par_seconde_film": round(elapsed/((fin-de)/IPS), 3), "loudness_aac": loud, "marge_master_db": round(marge, 3),
               "commande": [sys.executable, *sys.argv], "cache_segments": [t[-1] for t in tasks],
               "essais_dir": str(work), "journal_calibrations": str(essais_path),
               "essais_calibration": essais_calibration,
               "tolerant": args.tolerant, "medias_absents": m["_medias_absents"]}
    ecrire_exclusif(sortie.with_suffix('.rendu.json'), json.dumps(rapport, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({k: v for k, v in rapport.items() if k not in {"cache_segments", "commande"}}, ensure_ascii=False), flush=True)
    return rapport


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("montage")
    p.add_argument("--format", choices=["16x9", "9x16"], required=True)
    p.add_argument("--langue", choices=["fr", "en"], required=True)
    p.add_argument("--sortie", required=True)
    p.add_argument("--master", choices=["web", "reseaux"], default="web")
    p.add_argument("--de", type=float, default=0.)
    p.add_argument("--a", type=float)
    p.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    p.add_argument("--brouillon", action="store_true")
    p.add_argument("--tolerant", action="store_true", help="Remplacer les médias absents par des noirs étiquetés (audio : silence)")
    return p


if __name__ == "__main__":
    try:
        construire(parser().parse_args())
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        print(f"Erreur V6 : {exc}", file=sys.stderr)
        sys.exit(1)
