"""Prépare les images de la galerie de partage (JPEG ≤ 1600 px) et les affiches des vidéos."""
import subprocess
from pathlib import Path
from PIL import Image
RACINE = Path(__file__).resolve().parents[1]
OUT = RACINE / "partage" / "img"; OUT.mkdir(parents=True, exist_ok=True)
FF = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")

def jpg(src, nom, large=1600, q=84):
    im = Image.open(RACINE / src).convert("RGB")
    if im.width > large:
        im = im.resize((large, round(im.height * large / im.width)), Image.LANCZOS)
    im.save(OUT / f"{nom}.jpg", quality=q, optimize=True)

IMAGES = {
  "apercu-identite": "identite/apercu.png", "apercu-imprimes": "imprimes/apercu.png", "apercu-social": "social/apercu.png",
  "apercu-publicite": "publicite/apercu.png", "apercu-objets": "objets/apercu.png", "apercu-video": "video/teasers/apercu.png",
  "carte-recto": "imprimes/final/cartes/personne-1/carte-personne-1-recto.png",
  "carte-verso-fr": "imprimes/final/cartes/personne-1/carte-personne-1-verso-fr.png",
  "carte-verso-braise": "imprimes/final/cartes/personne-1/carte-personne-1-verso-braise-fr.png",
  "affiche-heros": "imprimes/final/affiches/heros/affiche-heros-fr-18x24po.png",
  "affiche-quebec": "imprimes/final/affiches/quebec/affiche-quebec-fr-18x24po.png",
  "affiche-famille": "imprimes/final/affiches/famille/affiche-famille-fr-18x24po.png",
  "affiche-typo": "imprimes/final/affiches/typo/affiche-typo-fr-18x24po.png",
  "fb-aurore": "social/final/facebook/couverture-aurore.fr.png", "fb-nuit": "social/final/facebook/couverture-nuit.fr.png",
  "fb-mosaique": "social/final/facebook/couverture-mosaique.fr.png",
  "ig-1": "social/final/instagram/carrousel/carrousel-1-sur-7.fr.png", "ig-2": "social/final/instagram/carrousel/carrousel-2-sur-7.fr.png",
  "ig-3": "social/final/instagram/carrousel/carrousel-3-sur-7.fr.png",
  "site-1440": "publicite/final/atterrissage/apercu-1440.fr.png", "site-390": "publicite/final/atterrissage/apercu-390.fr.png",
  "obj-tshirt": "objets/final/01-tshirt/01-tshirt-maquette.jpg", "obj-hoodie": "objets/final/02-chandail-capuchon/02-chandail-capuchon-maquette.jpg",
  "obj-tasse": "objets/final/05-tasse/05-tasse-maquette.jpg", "obj-tote": "objets/final/07-sac-fourre-tout/07-sac-fourre-tout-maquette.jpg",
  "obj-carnet": "objets/final/08-carnet/08-carnet-maquette.jpg", "obj-trousse": "objets/final/16-trousse-bienvenue/16-trousse-bienvenue-maquette.jpg",
  "obj-coffret": "objets/final/19-coffret-lancement/19-coffret-lancement-maquette.jpg", "obj-lampe": "objets/final/23-lampe-veilleuse/23-lampe-veilleuse-maquette.jpg",
  "obj-kiosque": "objets/final/24-fond-kiosque/24-fond-kiosque-maquette.jpg",
}
for nom, src in IMAGES.items():
    try: jpg(src, nom, 1800 if nom.startswith("apercu") else 1600)
    except Exception as e: print("ABSENT", nom, e)
# guide de marque : couverture et deux pages
guide = RACINE / "identite/final/guide/kit-de-marque-nexora-ai-fr-CA.pdf"
for p, nom in ((1, "guide-1"), (6, "guide-6"), (9, "guide-9")):
    subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "80", "-jpeg", "-singlefile", str(guide), str(OUT / nom)], check=False)
# affiches des vidéos
V = RACINE / "partage" / "video"
for f in sorted(V.glob("*.mp4")):
    subprocess.run([FF, "-v", "error", "-y", "-ss", "4.5" if "spot-6" not in f.name else "1.5", "-i", str(f), "-frames:v", "1", "-q:v", "4", str(OUT / f"{f.stem}.jpg")], check=False)
print(len(list(OUT.glob("*.jpg"))), "images")
