"""Infographie fixe prête pour les réseaux (1080×1350 et 1080×1080), tirée du film lui-même : son image clé héros en fond
(générée, sans texte), sa copie (accroche, trois temps forts pris dans ses textes, slogan) posée par le code (Geist, jetons de
marque.json). Aucun chiffre ajouté : seule la copie du modèle, déjà validée (pas de statistique, pas de superlatif).

  python3 infographie.py <film> [<film> ...]
Sortie : ~/nexora-creative-data/promo/montage/Test2-<brief>-<palier>-infographie-{4x5,1x1}.jpg
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "usine"))
import typo  # noqa: E402

TRAVAIL = Path.home() / "nexora-creative-data/work/films-v2"
PRODUITS = {"creative": "Creative", "opsys": "OPSYS-AI", "workstudio": "WorkStudio"}


def propre(t):
    return re.sub(r"\s+", " ", t.replace("|", " ").replace("*", "")).strip()


def habiller(d, txt, f, largeur):
    lignes, cour = [], ""
    for m in txt.split():
        if d.textlength((cour + " " + m).strip(), font=f) > largeur:
            lignes.append(cour)
            cour = m
        else:
            cour = (cour + " " + m).strip()
    return lignes + [cour]


def faire(nom):
    brief, palier = nom.split("-", 1)
    dos = TRAVAIL / nom
    film = json.loads((dos / "film.json").read_text())
    pj = json.loads((dos / "plaques.json").read_text())
    marque = json.loads((ICI.parent / "marque.json").read_text())
    C = {k: tuple(v) for k, v in marque["couleurs"].items()}
    ty = typo.Typo(marque)
    plans = [p for p in film["plans"] if p["type"] == "plan" and p["id"] in pj["plaques"]]
    heros = next((p for p in plans if p.get("heros")), plans[len(plans) // 2])
    fond0 = Image.open(dos / "plaques" / pj["plaques"][heros["id"]]["cle"]).convert("RGB")
    tx = [x for x in film.get("textes", []) if x["style"] in ("titre", "impact")]
    temps = [propre(x["texte"]) for x in tx][:3]
    accroche = propre(film["fin"]["slogan"])
    for fmt, (W, H) in {"4x5": (1080, 1350), "1x1": (1080, 1080)}.items():
        k = max(W / fond0.width, H * 0.62 / fond0.height)
        im = fond0.resize((int(fond0.width * k), int(fond0.height * k)), Image.LANCZOS)
        x0 = (im.width - W) // 2
        haut = im.crop((x0, 0, x0 + W, int(H * 0.62)))
        page = Image.new("RGB", (W, H), C["encre"])
        page.paste(haut, (0, 0))
        y = np.linspace(0, 1, int(H * 0.62))[:, None, None]
        a = np.maximum(np.clip((y - 0.45) / 0.55, 0, 1) ** 1.6, 0.75 * np.clip(1 - y / 0.16, 0, 1))  # bas fondu dans l'encre, haut assombri sous le surtitre
        zone = np.asarray(page.crop((0, 0, W, int(H * 0.62))), np.float32)
        zone = zone * (1 - a) + np.array(C["encre"], np.float32) * a
        page.paste(Image.fromarray(zone.astype(np.uint8)), (0, 0))
        d = ImageDraw.Draw(page)
        mx = int(W * 0.074)
        f_sur = ty.police("mono", W * 0.022, "Medium")
        d.ellipse([mx, mx + 6, mx + 14, mx + 20], fill=C["signal"])
        sur = (marque["marque"] + "  ·  " + PRODUITS[brief]).upper()
        d.text((mx + 26, mx), sur, font=f_sur, fill=C["os"])
        f_t = ty.police("titre", W * (0.082 if fmt == "4x5" else 0.07), "SemiBold")
        lignes = habiller(d, accroche, f_t, W - 2 * mx)
        yy = int(H * (0.50 if fmt == "4x5" else 0.42))
        for l in lignes:
            d.text((mx, yy), l, font=f_t, fill=C["os"])
            yy += int(f_t.size * 1.08)
        yy += int(H * 0.025)
        f_n = ty.police("mono", W * 0.026, "Medium")
        f_b = ty.police("titre", W * 0.036, "Regular")
        for i, t in enumerate(temps):
            d.text((mx, yy + 4), f"0{i + 1}", font=f_n, fill=C["signal"])
            for l in habiller(d, t, f_b, W - 2 * mx - 70)[:2]:
                d.text((mx + 70, yy), l, font=f_b, fill=C["os"])
                yy += int(f_b.size * 1.2)
            yy += int(H * 0.012)
            d.line([(mx + 70, yy - 6), (W - mx, yy - 6)], fill=(40, 40, 48), width=1)
        f_p = ty.police("titre", W * 0.024, "Regular")
        bas = propre(film["fin"].get("sous_titre", ""))
        lb = habiller(d, bas, f_p, W - 2 * mx)[:2]
        for i, l in enumerate(lb):
            d.text((mx, H - mx - f_p.size * 1.3 * (len(lb) - i)), l, font=f_p, fill=C["brume"])
        if brief == "opsys":
            f_e = ty.police("titre", W * 0.022, "Medium")
            e = "Vision · en développement"
            lw = d.textlength(e, font=f_e)
            d.rounded_rectangle([W - mx - lw - 28, mx - 8, W - mx, mx + f_e.size + 10], radius=10, outline=C["signal"], width=2)
            d.text((W - mx - lw - 14, mx), e, font=f_e, fill=C["signal"])
        out = Path.home() / f"nexora-creative-data/promo/montage/Test2-{brief}-{palier}-infographie-{fmt}.jpg"
        page.filter(ImageFilter.UnsharpMask(1, 40, 2)).save(out, quality=92)
        print(out)


if __name__ == "__main__":
    for n in sys.argv[1:]:
        faire(n)
