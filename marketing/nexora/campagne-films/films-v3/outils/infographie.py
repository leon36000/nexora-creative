"""Infographie d'un film V5 (1080×1350 et 1080×1080) : une image du film, la ligne à retenir, quatre étapes, la mention vraie.

  python3 infographie.py <film>     → work/films-v3/<film>/rendu/infographie-<film>-{1080x1350,1080x1080}.png
"""
import io
import json
import subprocess
import sys

from PIL import Image, ImageDraw

import commun as C
from composer import MARQUE, SIG, OS_, BRUME, ENCRE, poser_carte, typo

CONTENU = {
    "creative": {"t": 30.0, "ligne": "Écrivez-le. *On le filme.*",
                 "etapes": ["Une phrase", "Le plan, et le prix d'abord", "Deux prises, le juge garde la meilleure", "Monté sur la musique"],
                 "mention": "Images du film réellement tourné par le studio, session du 3 novembre 2026."},
    "workstudio": {"t": 17.0, "ligne": "Rien ne part *sans vous.*",
                   "etapes": ["Lire le courrier", "Trier", "Préparer la réponse", "Attendre votre accord"],
                   "image": ["ui/ws-approuver.jpg", (0, 0, 1186, 560)], "mention": "Capture réelle du workflow « Tri du courrier entrant », exécution du 2 novembre 2026."},
    "opsys": {"t": 38.5, "ligne": "Votre entreprise. *Au complet.*",
              "etapes": ["Dix départements, M1 à M10", "Des agents dans chacun", "Tout en brouillon", "Vous décidez"],
              "mention": "Vision · en développement. Tableau dessiné d'après les départements réels du dépôt."},
}


def infographie(nom):
    film = C.charger_film(nom)
    c = CONTENU[nom]
    dos = C.dossier(nom) / "rendu"
    b = subprocess.run([C.FF, "-v", "error", "-ss", str(c["t"]), "-i", str(dos / f"V5-{nom}-16x9-fr-master.mp4"), "-frames:v", "1",
                        "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    cadre = Image.open(io.BytesIO(b)).convert("RGB")
    if c.get("image"):  # capture réelle directe plutôt qu'une image du film (carte trop petite dans le cadre)
        cadre = Image.open(C.dossier(nom) / c["image"][0]).convert("RGB").crop(c["image"][1])
    ty = typo.Typo(MARQUE)
    for W, H in ((1080, 1350), (1080, 1080)):
        im = Image.new("RGB", (W, H), ENCRE)
        d = ImageDraw.Draw(im)
        fm = ty.police("mono", 22, "Medium")
        m = " ".join(MARQUE["marque"]) + "   ·   " + film["produit"].upper()
        d.text((64, 56), m, font=fm, fill=BRUME)
        spec = {"d": 99, "style": "titre", "zone": "haut", "taille": 0.62}
        zone = Image.new("RGB", (W, int(H * 0.34)), ENCRE)
        zone = ty.poser(zone.resize((W, W)), spec, c["ligne"], 5.0).crop((0, 0, W, int(H * 0.34)))
        im.paste(zone, (0, 40))
        hw = W - 128 if H > W else 760
        hh = int(hw * cadre.height / cadre.width)
        y_img = int(H * (0.22 if H > W else 0.24))
        poser_carte(im, cadre.resize((hw, hh), Image.LANCZOS), W / 2, y_img + hh / 2)
        fe = ty.police("titre", 30, "Regular")
        fn = ty.police("mono", 22, "Medium")
        y = y_img + hh + (40 if H == W else 56)
        for i, e in enumerate(c["etapes"]):
            col = 64
            row = y + i * (52 if H == W else 62)
            d.text((col, row + 4), f"0{i + 1}", font=fn, fill=SIG)
            d.text((col + 52, row), e, font=fe, fill=OS_)
        fs = ty.police("mono", 18, "Medium")
        d.text((64, H - 70), c["mention"], font=fs, fill=(130, 130, 138))
        d.rectangle([64, H - 92, 64 + 64, H - 88], fill=SIG)
        out = dos / f"infographie-{nom}-{W}x{H}.png"
        im.save(out)
        print(out)


if __name__ == "__main__":
    infographie(sys.argv[1])
