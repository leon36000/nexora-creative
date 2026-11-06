"""Rendu d'un film du concours OPSYS-AI : EditPlan v1 (contrat du harnais `app/server/nexora/montage/editplan.ts`) + annexe.

  python3 monter.py <equipe> <long|court|vertical> [--brouillon] [--sortie fichier.mp4] [--jobs 14]

Image : plans H3 (prise retenue, `choix.json`), image source décodée à sa définition native puis zoom/recadrage et remise à
l'échelle Lanczos en 1920×1080 (ou 1080×1920 : un plan 16:9 est recadré au centre ou à `annexe.recadrage_v[plan]`), vitesse et
rampes avec mélange d'images, transitions cut / fondu / dip / glisse, étalonnage « pellicule » des promos V3/V4
(`marketing/creative/video-v3/couches.py`), puis textes de l'EditPlan, incrustations de l'annexe (typographie cinétique
`usine/typo.py` + `chaine/incrustations.py`). Son : musique (entrée, gain, fondus), voix, ducking (rampes de 0,25 s), son natif
des plans (`son_plans`), bruitages synthétiques (`video-v3/sfx_v3.py`), normalisation loudnorm deux passes (cible et crête du plan).
Le rendu se fait par tranches d'images en parallèle ; les tranches et le mix restent sous
`montage/tranches-<équipe>-<version>-<mode>-<horodatage>/` avec l'export du film.
"""
import argparse
import json
import math
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
DEPOT = RACINE.parents[3]
sys.path.insert(0, str(ICI))
sys.path.insert(0, str(DEPOT / "marketing/creative/video-v3"))
sys.path.insert(0, str(DEPOT / "marketing/nexora/campagne-films/usine"))
import couches  # noqa: E402
import sfx_v3  # noqa: E402
from incrustations import Incrustations  # noqa: E402
from typo import Typo, ease_out  # noqa: E402
import tourner as T  # noqa: E402

FF = T.FF
FP = T.FP
FPS = 24
SR = 48000
REGLAGES = {"exposition": 1.0, "teinte_ombres": [-0.006, 0.0, 0.012], "teinte_hautes": [0.025, 0.008, -0.02], "saturation": 1.0,
            "contraste": 1.06, "noir": 0.008, "seuil_halo": 0.86, "halo": 0.22, "seuil_reflet": 0.985, "reflet": 0.25,
            "vignette": 0.25, "grain": 0.03}
MARQUE = json.loads((RACINE / "marque-opsys.json").read_text())
TYPO_TYPES = {"titre", "impact", "pile", "surtitre", "etiquette"}


# ------------------------------------------------------------------------------------------------------------ préparation
def charger(equipe, version):
    D = T.dossier(equipe)
    plan = D["montage"][version]
    annexe = (D.get("annexe") or {}).get(version) or {}
    return D, plan, annexe


def valider_ts(plan):
    """Validation officielle (validerEditPlan) par tsx si disponible ; renvoie le rapport ou None."""
    tsx = Path("/home/pc6/Desktop/Nexora Creative/app/node_modules/.bin/tsx")
    if not tsx.exists():
        return None
    f = T.TRAVAIL / "tmp" / f"editplan-{abs(hash(json.dumps(plan, sort_keys=True)))}.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(plan))
    r = subprocess.run([str(tsx), str(ICI / "valider-editplan.ts"), str(f)], capture_output=True, text=True,
                       cwd="/home/pc6/Desktop/Nexora Creative/app")
    f.unlink(missing_ok=True)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "erreurs": [{"regle": "tsx", "message": (r.stderr or r.stdout)[-400:]}]}


class ValidationEditPlanRefusee(ValueError):
    """Le rapport du validateur officiel ne permet pas le rendu."""


def verifier_rapport_validation(rapport):
    """Refuse un rapport invalide; rend explicite l'absence du validateur tsx."""
    if rapport is None:
        print("AVERTISSEMENT : EditPlan non validé (tsx absent); rendu poursuivi sans validation officielle.", file=sys.stderr)
        return None
    if not isinstance(rapport, dict) or rapport.get("ok") is not True:
        erreurs = rapport.get("erreurs") if isinstance(rapport, dict) else None
        details = []
        if isinstance(erreurs, list):
            for erreur in erreurs:
                if isinstance(erreur, dict):
                    details.append(f"{erreur.get('regle', '?')} : {erreur.get('message', '')}".strip())
                else:
                    details.append(str(erreur))
        elif erreurs:
            details.append(str(erreurs))
        raison = " ; ".join(details) or "rapport absent ou mal formé (ok doit être strictement true)"
        raise ValidationEditPlanRefusee(f"EditPlan refusé par le validateur officiel : {raison}. Rendu refusé.")
    return rapport


def ligne_de_temps(video):
    debuts, t = [], 0
    for i, c in enumerate(video):
        tr = c.get("transition_in") or {"type": "cut", "duree_f": 0}
        rec = tr.get("duree_f", 0) if i > 0 and tr.get("type", "cut") != "cut" else 0
        d = t - rec
        debuts.append(d)
        t = d + c["duree_f"]
    return debuts, t


def resoudre(equipe, plan, version):
    """src → fichier vidéo (ou None = image d'encre), voix → wav, musique → wav."""
    vert = plan.get("format") == "9:16"
    vid = {}
    for sid, s in plan["sources"].items():
        if s.get("kind") != "video":
            continue
        f = T.plan_retenu(equipe, sid)
        if f is None and vert and sid.endswith("v"):  # 9:16 natif non tourné : le plan 16:9 du même nom, recadré
            # Le suffixe « v » encode la paire, p.ex. p02v → p02. Ne pas
            # deviner de paire pour des IDs indépendants comme v01.
            f = T.plan_retenu(equipe, sid[:-1])
        vid[sid] = str(f) if f else None
    voix = {}
    for v in plan.get("audio", {}).get("voix", []):
        try:
            voix[v["src"]] = str(T.prise_voix(equipe, v["src"]))
        except FileNotFoundError:
            voix[v["src"]] = None
    c = T.choix(equipe)
    n = c.get("musique") or 1
    if isinstance(n, dict):  # choix par version : {"long": 1, "court": 3}
        n = n.get(version) or n.get("long") or 1
    # une source musique nommée comme une entrée de musique.prompts ({id, prompt}) désigne cette génération-là
    D = T.dossier(equipe)
    src = (plan.get("audio", {}).get("musique") or {}).get("src")
    for i, pr in enumerate(D.get("musique", {}).get("prompts") or [], 1):
        if isinstance(pr, dict) and pr.get("id") == src:
            n = i
    if isinstance(n, str):  # piste conformée au montage (partition.py) ou candidat nommé
        m = T.TRAVAIL / equipe / "musique" / n
        return vid, voix, (str(m) if m.exists() else None)
    m = T.TRAVAIL / equipe / "musique" / f"lyria-{n}.wav"
    return vid, voix, (str(m) if m.exists() else None)


class PlansVideoManquants(ValueError):
    """Le montage référence des plans vidéo qui ne sont pas encore disponibles."""


def verifier_sources_video(equipe, version, sources):
    """Refuse un rendu quand un plan manque au lieu de remplir ses images d'encre."""
    manquants = sorted(
        sid for sid, fichier in sources.items()
        if sid not in ("noir", "carton")
        and (not fichier or not Path(fichier).is_file())
    )
    if manquants:
        liste = ", ".join(manquants)
        raise PlansVideoManquants(
            f"Plans vidéo manquants pour {equipe}/{version} : {liste}. "
            "Générez les plans manquants ou corrigez l'EditPlan avant le rendu."
        )
    return manquants


def verifier_fichier_libre(cible, type_artefact):
    """Refuse de remplacer un artefact déjà présent, y compris un lien symbolique cassé."""
    cible = Path(cible)
    if cible.exists() or cible.is_symlink():
        raise FileExistsError(f"Refus d'écraser {type_artefact} existant : {cible}")
    return cible


def verifier_sortie_libre(sortie):
    """Refuse de remplacer un export déjà présent."""
    return verifier_fichier_libre(sortie, "l'export")


def chemin_libre(cible):
    """Retourne le premier nom libre en gardant intact tout artefact déjà présent."""
    cible = Path(cible)
    if not cible.exists() and not cible.is_symlink():
        return cible
    for n in range(2, 100_000):
        candidat = cible.with_name(f"{cible.stem}-{n}{cible.suffix}")
        if not candidat.exists() and not candidat.is_symlink():
            return candidat
    raise FileExistsError(f"Aucun nom libre trouvé près de : {cible}")


def reserver_chemin_libre(cible):
    """Réserve atomiquement un artefact de travail avant qu'un writer permissif l'ouvre."""
    while True:
        candidat = chemin_libre(cible)
        try:
            with candidat.open("xb"):
                pass
            return candidat
        except FileExistsError:
            # Un autre processus a pris ce nom entre la recherche et la réservation.
            continue


def creer_dossier_tranches(out_dir, equipe, version, brouillon):
    """Réserve un dossier propre et étiqueté pour garder les vidéos intermédiaires."""
    horodatage = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    mode = "brouillon" if brouillon else "final"
    label = f"tranches-{equipe}-{version}-{mode}-{horodatage}-{time.time_ns()}"
    dossier = Path(out_dir) / label
    dossier.mkdir(parents=True, exist_ok=False)
    return dossier


def sonder(f):
    r = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                        "stream=width,height,nb_read_packets", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    w, h, n = r.split(",")[:3]
    return int(w), int(h), int(n)


# ---------------------------------------------------------------------------------------------------------------- image
_CACHE = {}


def images_source(f, a, b):
    """Images [a, b] (indices de la source) à la définition native, en uint8 ; cache par processus."""
    cle = (f, a, b)
    if cle in _CACHE:
        return _CACHE[cle]
    if len(_CACHE) > 6:
        _CACHE.clear()
    w, h, n = sonder(f)
    a = max(0, min(a, n - 1))
    b = max(a, min(b, n - 1))
    raw = subprocess.run([FF, "-v", "error", "-i", f, "-vf", f"select='between(n\\,{a}\\,{b})'", "-vsync", "0",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    _CACHE[cle] = (a, fr, n)
    return _CACHE[cle]


def indice_source(c, k):
    """Indice (réel) de l'image source pour la k-ième image du plan (vitesse constante ou rampe linéaire)."""
    e = c.get("entree_f", 0)
    if c.get("rampe"):
        v0, v1, d = c["rampe"]["de"], c["rampe"]["a"], max(1, c["duree_f"])
        return e + v0 * k + (v1 - v0) * k * k / (2 * d)
    return e + c.get("vitesse", 1.0) * k


def image_plan(c, k, fichier, W, H, cx_v):
    if fichier is None:
        return Image.new("RGB", (W, H), tuple(MARQUE["couleurs"]["encre"]))
    s = indice_source(c, k)
    conso = indice_source(c, c["duree_f"]) + 2
    a0, fr, n = images_source(fichier, int(c.get("entree_f", 0)), int(math.ceil(conso)))
    i0 = int(math.floor(s)) - a0
    t = s - math.floor(s)
    i0 = max(0, min(len(fr) - 1, i0))
    i1 = min(len(fr) - 1, i0 + 1)
    x = fr[i0] if t < 0.02 or i1 == i0 else (fr[i0] * (1 - t) + fr[i1] * t).astype(np.uint8)
    im = Image.fromarray(x)
    sw, sh = im.size
    z = 1.0
    if c.get("zoom"):
        u = k / max(1, c["duree_f"] - 1)
        z = c["zoom"]["de"] + (c["zoom"]["a"] - c["zoom"]["de"]) * (u * u * (3 - 2 * u))
    # recadrage au ratio de sortie, centré (ou cx_v en vertical), puis zoom
    r_out = W / H
    if sw / sh > r_out:
        cw, ch = sh * r_out, sh
    else:
        cw, ch = sw, sw / r_out
    cw, ch = cw / z, ch / z
    cx = (cx_v if cx_v is not None else 0.5) * sw
    cy = 0.5 * sh
    x0 = min(max(0, cx - cw / 2), sw - cw)
    y0 = min(max(0, cy - ch / 2), sh - ch)
    im = im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    return im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2))


class Contexte:
    def __init__(self, equipe, version, brouillon):
        self.D, self.plan, self.annexe = charger(equipe, version)
        self.equipe, self.version = equipe, version
        vert = self.plan.get("format") == "9:16"
        self.W, self.H = (1080, 1920) if vert else (1920, 1080)
        if brouillon:
            self.W, self.H = self.W // 2, self.H // 2
        self.vert = vert
        self.vid, self.voix, self.musique = resoudre(equipe, self.plan, version)
        self.debuts, self.total = ligne_de_temps(self.plan["video"])


_CTX = {}


def contexte(args):
    cle = tuple(args)
    if cle not in _CTX:
        ctx = Contexte(*args)
        reg = dict(REGLAGES)
        e = ctx.annexe.get("etalonnage") or {}
        reg["contraste"] *= float(e.get("contraste", 1.0))
        reg["saturation"] *= float(e.get("saturation", 1.0))
        reg["grain"] *= float(e.get("grain", 1.0))
        ch = float(e.get("chaleur", 0.0))
        reg["teinte_hautes"] = [reg["teinte_hautes"][0] + 0.02 * ch, reg["teinte_hautes"][1], reg["teinte_hautes"][2] - 0.02 * ch]
        ctx.pel = couches.Pellicule(ctx.W, ctx.H, f"opsys-{ctx.equipe}", reg)
        ctx.typo = Typo({**MARQUE})
        env = {}
        for lid, f in ctx.voix.items():
            if f:
                a = lire_audio(f, mono=True)
                n = int(len(a) / SR * FPS) + 1
                e2 = np.array([np.sqrt(np.mean(a[int(i * SR / FPS):int((i + 1) * SR / FPS)] ** 2)) if int(i * SR / FPS) < len(a) else 0 for i in range(n)])
                env[lid] = (e2 / (e2.max() + 1e-6)).astype(np.float32)
        ctx.inc = Incrustations(MARQUE, ctx.W, ctx.H, env)
        _CTX.clear()
        _CTX[cle] = ctx
    return _CTX[cle]


@lru_cache(maxsize=512)
def mesurer_typo_cadre(typo, texte, type_, W, H, echelle, mx, y):
    """Plus grande police qui entre dans le cadre ; résultat réutilisé entre images."""
    maxi = min(max(W, H), max(6, int(min(W, H) * 0.024 * echelle)))
    bas_taille, haut_taille, meilleur = 6, maxi, None
    while bas_taille <= haut_taille:
        taille = (bas_taille + haut_taille) // 2
        f = typo.police("mono", taille, "Medium")
        lw = typo.larg(f, texte, 0.12)
        pad = f.size * 0.6
        largeur = lw + (2 * pad if type_ == "etiquette" else f.size * 1.3)
        haut = y - pad * 0.6 if type_ == "etiquette" else y
        bas = y + f.size + pad * 0.7 if type_ == "etiquette" else y + f.size
        if largeur <= W - 2 * mx and haut >= H * 0.04 and bas <= H * 0.96:
            meilleur = f, lw, pad, largeur
            bas_taille = taille + 1
        else:
            haut_taille = taille - 1
    if meilleur is None:
        raise ValueError("Texte d'incrustation trop long pour le cadre sûr")
    return meilleur


def poser_typo(ctx, im, spec, u):
    t = spec["type"]
    d = spec["duree_f"] / FPS
    W, H = im.size
    v = H > W
    if t in ("titre", "impact", "pile"):
        txt = spec.get("texte") or "|".join(spec.get("lignes", []))
        zone = spec.get("zone") or {"impact": "centre", "pile": "colonne"}.get(t, "bas")
        if v and zone == "colonne":
            zone = "haut"
        return ctx.typo.poser(im, {"d": d, "zone": zone, "style": t, "taille": spec.get("echelle", 1.0)}, txt, u)
    # surtitre / étiquette : tracés ici pour gérer les quatre coins
    calque = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(calque)
    txt = spec["texte"].upper()
    mx = (0.08 if v else 0.06) * W
    pos = spec.get("position", "haut-gauche" if t == "surtitre" else "bas-droite")
    y = (0.105 * H if v else 0.075 * H) if pos.startswith("haut") else ((0.86 if v else 0.885) * H if pos.startswith("bas") else 0.5 * H)
    f, lw, pad, largeur = mesurer_typo_cadre(ctx.typo, txt, t, W, H, spec.get("echelle", 1.0), mx, y)
    x = mx if "gauche" in pos else (W - mx - largeur if "droite" in pos else (W - largeur) / 2)
    p = ease_out(u / 0.3)
    sortie = min(1.0, max(0.0, (d - u) / 0.22))
    a = int(255 * p * sortie)
    sig, brume = tuple(MARQUE["couleurs"]["signal"]), tuple(MARQUE["couleurs"]["brume"])
    if t == "etiquette":
        dd.rounded_rectangle([x, y - pad * 0.6, x + lw + 2 * pad, y + f.size + pad * 0.7], radius=f.size * 0.3,
                             fill=(8, 8, 10, int(a * 0.55)), outline=(*sig, a), width=max(2, int(f.size * 0.09)))
        ctx.typo.tracer(dd, (x + pad, y), txt, f, (*sig, a), 0.12)
    else:
        r = f.size * 0.28
        dd.ellipse([x, y + f.size * 0.5 - r, x + 2 * r, y + f.size * 0.5 + r], fill=(*sig, a))
        ombre = calque.copy()
        ctx.typo.tracer(dd, (x + 2 * r + f.size * 0.7, y), txt, f, (*MARQUE["couleurs"]["os"], a), 0.12)
    return Image.alpha_composite(im.convert("RGBA"), calque).convert("RGB")


def textes_plan(ctx):
    """Textes de l'EditPlan → incrustations typographiques équivalentes."""
    out = []
    for t in ctx.plan.get("textes", []):
        style = {"titre": "titre", "sous-titre": "surtitre", "carton": "impact", "bas": "titre"}.get(t.get("style", "titre"), "titre")
        zone = {"haut": "haut", "centre": "centre", "bas": "bas"}.get(t.get("position", "bas"), "bas")
        out.append({"type": style, "texte": t["texte"].replace("\n", "|"), "debut_f": t["debut_f"], "duree_f": t["duree_f"], "zone": zone,
                    "position": "haut-gauche" if zone == "haut" else "bas-gauche", "echelle": t.get("taille_pct", 6) / 6})
    return out


def verifier_typo_cadre(ctx, incs, W, H):
    """Refuse avant l'encodeur les mentions qui ne rentrent pas dans le cadre sûr."""
    fond = Image.new('RGB', (W, H))
    for spec in incs:
        if spec.get('type') in ('surtitre', 'etiquette'):
            poser_typo(ctx, fond, spec, 0.5)


def rendre_tranche(args):
    equipe, version, brouillon, a, b, sortie = args
    sortie = verifier_fichier_libre(sortie, "la tranche")
    ctx = contexte((equipe, version, brouillon))
    W, H = ctx.W, ctx.H
    video = ctx.plan["video"]
    rec_v = ctx.annexe.get("recadrage_v") or {}
    incs = sorted(textes_plan(ctx) + list(ctx.annexe.get("incrustations", [])), key=lambda s: 1 if s["type"] in ("flash", "glitch") else 0)
    verifier_typo_cadre(ctx, incs, W, H)
    enc = subprocess.Popen([FF, "-v", "error", "-n", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "ultrafast" if brouillon else "medium", "-crf", "24" if brouillon else "13",
                            "-pix_fmt", "yuv420p", str(sortie)], stdin=subprocess.PIPE)
    for g in range(a, b):
        # plan(s) actif(s) à l'image g
        actifs = [i for i, c in enumerate(video) if ctx.debuts[i] <= g < ctx.debuts[i] + c["duree_f"]]
        if not actifs:
            im = Image.new("RGB", (W, H), (0, 0, 0))
        else:
            i = actifs[-1]
            c = video[i]
            k = g - ctx.debuts[i]
            cxv = (rec_v.get(c["src"]) if c["src"] in rec_v else rec_v.get(c["src"][:-1])) if ctx.vert else None
            im = image_plan(c, k, ctx.vid.get(c["src"]), W, H, cxv)
            tr = c.get("transition_in") or {}
            if len(actifs) > 1 and tr.get("type", "cut") != "cut" and k < tr.get("duree_f", 0):
                j = actifs[0]
                cp = video[j]
                prev = image_plan(cp, g - ctx.debuts[j], ctx.vid.get(cp["src"]), W, H, None)
                u = (k + 1) / (tr["duree_f"] + 1)
                if tr["type"] == "fondu":
                    im = Image.blend(prev, im, u)
                elif tr["type"] == "dip":
                    noir = Image.new("RGB", (W, H), (0, 0, 0))
                    im = Image.blend(prev, noir, min(1, u * 2)) if u < 0.5 else Image.blend(noir, im, (u - 0.5) * 2)
                elif tr["type"] == "glisse":
                    dx = int(W * (1 - ease_out(u)))
                    base = prev.copy()
                    base.paste(im.crop((0, 0, W - dx, H)), (dx, 0))
                    im = base
            if ctx.vid.get(c["src"]) is not None:
                x = np.asarray(im, np.float32) / 255
                x = ctx.pel.finir(ctx.pel.etalonner(x), g, False)
                im = Image.fromarray((x * 255 + 0.5).astype(np.uint8))
        for s in incs:
            d0 = s["debut_f"]
            if d0 <= g < d0 + s["duree_f"]:
                u = (g - d0) / FPS
                try:
                    im = poser_typo(ctx, im, s, u) if s["type"] in TYPO_TYPES else ctx.inc.poser(im, s, u)
                except Exception as e:  # une incrustation mal formée ne bloque pas le film : elle est signalée
                    print(f"incrustation {s.get('type')} à {d0} : {e}", file=sys.stderr)
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    if enc.wait():
        raise SystemExit("encodage échoué")
    return str(sortie)


# ------------------------------------------------------------------------------------------------------------------ son
def lire_audio(f, debut=0.0, duree=None, mono=False):
    a = ["-ss", str(max(0.0, debut)), "-i", str(f)] + (["-t", str(duree)] if duree else [])
    brut = subprocess.run([FF, "-v", "error", *a, "-f", "f32le", "-ac", "1" if mono else "2", "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(brut, np.float32)
    return x.copy() if mono else x.reshape(-1, 2).copy()


def poser(piste, son, t, db=0.0, fondu=0.0):
    i = int(round(t * SR))
    if i < 0:
        son = son[-i:]
        i = 0
    if i >= len(piste) or len(son) == 0:
        return
    s = son[: len(piste) - i] * (10 ** (db / 20))
    if fondu:
        k = min(len(s), int(fondu * SR))
        s[-k:] *= np.linspace(1, 0, k)[:, None]
        k2 = min(len(s), int(0.01 * SR))
        s[:k2] *= np.linspace(0, 1, k2)[:, None]
    piste[i: i + len(s)] += s


def mixer(ctx, sortie_wav):
    sortie_wav = verifier_fichier_libre(sortie_wav, "le mix audio")
    P = ctx.plan
    A = P.get("audio", {})
    dur = ctx.total / FPS
    piste = np.zeros((int(dur * SR) + SR, 2), np.float32)
    # voix
    intervalles = []
    for v in A.get("voix", []):
        f = ctx.voix.get(v["src"])
        if not f:
            continue
        a = lire_audio(f, mono=True)
        e = v.get("entree_f", 0) / FPS
        a = a[int(e * SR):]
        t = v["debut_f"] / FPS
        poser(piste, np.stack([a, a], 1), t, v.get("gain_db", 0) + 0.0, 0.03)
        intervalles.append((t, t + len(a) / SR))
    # musique avec ducking
    m = A.get("musique")
    if m and ctx.musique:
        e = 0.0 if "conforme-" in Path(ctx.musique).name else m.get("entree_f", 0) / FPS  # une piste conformée part de 0
        d = (m.get("duree_f") or (ctx.total - 0)) / FPS
        mu = lire_audio(ctx.musique, e, d)
        n = len(mu)
        fi, fo = int(m.get("fondu_in_f", 0) / FPS * SR), int(m.get("fondu_out_f", 0) / FPS * SR)
        if fi:
            mu[:fi] *= np.linspace(0, 1, fi)[:, None]
        if fo:
            mu[-fo:] *= np.linspace(1, 0, min(fo, n))[:, None]
        duck = A.get("ducking") or {}
        if duck.get("actif") and intervalles:
            tt = np.arange(n) / SR
            g = np.zeros(n, np.float32)
            prof = -abs(duck.get("profondeur_db", 9))
            for a0, b0 in intervalles:
                r = np.clip(np.minimum(tt - (a0 - 0.25), (b0 + 0.25) - tt) / 0.25, 0, 1)
                g = np.minimum(g, r * prof)
            mu *= (10 ** (g / 20))[:, None]
        poser(piste, mu, 0.0, m.get("gain_db", -8))
    # son natif des plans (vitesse 1 seulement)
    son_db = {s["plan"]: s["db"] for s in (ctx.annexe.get("son_plans") or [])}
    for i, c in enumerate(P["video"]):
        f = ctx.vid.get(c["src"])
        if c["src"] in son_db and f and not c.get("rampe") and abs(c.get("vitesse", 1.0) - 1) < 1e-3:
            a = lire_audio(f, c.get("entree_f", 0) / FPS, c["duree_f"] / FPS)
            poser(piste, a, ctx.debuts[i] / FPS, son_db[c["src"]], 0.06)
    rng = np.random.default_rng(4)
    for x in ctx.annexe.get("sfx", []):
        try:
            poser(piste, sfx_v3.generer(x["type"], float(x.get("duree_s", 1.0)), rng), x["debut_f"] / FPS, x.get("db", 0.0))
        except Exception as e:
            print("bruitage", x, e, file=sys.stderr)
    piste = piste[: int(dur * SR)]
    piste /= max(1.0, float(np.abs(piste).max()) / 0.98)
    brut = reserver_chemin_libre(sortie_wav.with_suffix(".brut.wav"))
    sfx_v3.ecrire(piste, str(brut))
    cible = A.get("cible_lufs", -14)
    tp = A.get("crete_db", -1.5) - 0.5
    r = subprocess.run([FF, "-hide_banner", "-i", str(brut), "-af", f"loudnorm=I={cible}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True)
    e = r.stderr.decode()
    j = json.loads(e[e.rfind("{"): e.rfind("}") + 1])
    subprocess.run([FF, "-v", "error", "-n", "-i", str(brut), "-af",
                    f"loudnorm=I={cible}:TP={tp}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
                    f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,alimiter=limit=0.72:level=false:asc=1",
                    "-ar", str(SR), str(sortie_wav)], check=True)


# ----------------------------------------------------------------------------------------------------------------- tout
def construire(equipe, version, brouillon=False, sortie=None, jobs=14):
    t0 = time.time()
    ctx = Contexte(equipe, version, brouillon)
    manquants = verifier_sources_video(equipe, version, ctx.vid)
    nom_sortie = f"{equipe}-{version}{'-brouillon' if brouillon else ''}.mp4"
    chemin_defaut = T.TRAVAIL / equipe / "montage" / nom_sortie
    sortie = verifier_sortie_libre(sortie if sortie is not None else chemin_defaut)
    rapport = verifier_rapport_validation(valider_ts(ctx.plan))
    out_dir = T.dossier_travail(equipe, "montage")
    tranches = creer_dossier_tranches(out_dir, equipe, version, brouillon)
    pas = 36
    taches = [(equipe, version, brouillon, a, min(ctx.total, a + pas), tranches / f"t{a:06d}.mp4") for a in range(0, ctx.total, pas)]
    with ProcessPoolExecutor(jobs) as ex:
        list(ex.map(rendre_tranche, taches))
    (tranches / "liste.txt").write_text("".join(f"file '{x[-1]}'\n" for x in taches))
    wav = tranches / "mix.wav"
    mixer(ctx, wav)
    subprocess.run([FF, "-v", "error", "-n", "-f", "concat", "-safe", "0", "-i", str(tranches / "liste.txt"), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "fast" if brouillon else "slow", "-crf", "23" if brouillon else "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", str(sortie)], check=True)
    res = {"film": str(sortie), "equipe": equipe, "version": version, "duree_s": round(ctx.total / FPS, 2), "plans": len(ctx.plan["video"]),
           "tranches": str(tranches), "manquants": manquants, "validation": rapport, "secondes": round(time.time() - t0, 1)}
    print(json.dumps(res, ensure_ascii=False))
    with (T.TRAVAIL / "journal-montage.jsonl").open("a") as fh:
        fh.write(json.dumps(res, ensure_ascii=False) + "\n")
    return res


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("equipe")
    a.add_argument("version")
    a.add_argument("--brouillon", action="store_true")
    a.add_argument("--sortie")
    a.add_argument("--jobs", type=int, default=14)
    o = a.parse_args()
    try:
        construire(o.equipe, o.version, o.brouillon, o.sortie, o.jobs)
    except (PlansVideoManquants, FileExistsError, ValidationEditPlanRefusee) as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        raise SystemExit(2)
