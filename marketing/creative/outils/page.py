"""Assemble la page marketing de Nexora Creative à partir du gabarit index.html.

- remplit {{PROMPT_P01}} avec le prompt réellement écrit par le réécrivain pour le plan 1 ;
- remplit {{PLANCHE}} avec les images choisies dans les rushes et la phrase française qui les a produites ;
- extrait les images (JPEG 1280 px) dans marketing/creative/site/img et copie la bande-annonce en site/promo.mp4 ;
- écrit site/index.html (pour le site Nexora) et apercu.html (images en data URI, vidéo à part) pour l'aperçu.

Usage : python3 page.py choix.json
choix.json : { "promo": "...mp4", "prompts": "...prompts.json", "intentions": "...intentions.json",
               "images": { "p01": ["rush.mp4", 2.4], "p01b": [...], ... }, "planche": ["p01", "p03", ...] }
"""
import base64
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
FFMPEG = str(Path.home() / "nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg")


def image(rush: str, t: float, sortie: Path):
    subprocess.run([FFMPEG, "-v", "error", "-y", "-ss", str(t), "-i", rush, "-frames:v", "1", "-vf", "scale=1280:-2:flags=lanczos",
                    "-q:v", "3", str(sortie)], check=True)


def colorer(prompt: str) -> str:
    """Le prompt du moteur, échappé, avec ses trois champs mis en évidence."""
    p = html.escape(prompt)
    for champ in ("integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
        p = p.replace(champ, f'<span class="champ">{champ}</span>')
    return p


def main(choix: dict):
    site = ICI / "site"
    (site / "img").mkdir(parents=True, exist_ok=True)
    for nom, (rush, t) in choix["images"].items():
        image(rush, t, site / "img" / f"{nom}.jpg")
    prompts = {x["nom"][:3]: x for x in json.loads(Path(choix["prompts"]).read_text())}
    intentions = {x["nom"][:3]: x for x in json.loads(Path(choix["intentions"]).read_text())}
    cases = []
    for k in choix["planche"]:
        phrase = choix.get("phrases", {}).get(k) or intentions[k[:3]]["intention"]
        cases.append(
            f'        <figure class="plan"><img src="img/{k}.jpg" alt="{html.escape(phrase)}" loading="lazy">'
            f'<figcaption class="legende"><span class="etiquette">Plan {k[1:3]} · 5 s avec son</span>'
            f"<p>« {html.escape(phrase)} »</p></figcaption></figure>"
        )
    gabarit = (ICI / "index.html").read_text()
    page = gabarit.replace("{{PROMPT_P01}}", colorer(prompts["p01"]["prompt"])).replace("{{PLANCHE}}", "\n".join(cases))
    (site / "index.html").write_text(page)
    shutil.copy(choix["promo"], site / "promo.mp4")
    # Aperçu autonome : images embarquées, vidéo servie à part (magasin de l'artefact).
    apercu = page
    for f in (site / "img").glob("*.jpg"):
        apercu = apercu.replace(f'"img/{f.name}"', '"data:image/jpeg;base64,' + base64.b64encode(f.read_bytes()).decode() + '"')
    apercu = apercu.replace('href="/fr/apps/creative"', 'href="#acces"')
    if choix.get("video_url"):
        apercu = apercu.replace('src="promo.mp4"', f'src="{choix["video_url"]}"')
    (ICI / "apercu.html").write_text(apercu)
    print(site / "index.html", ICI / "apercu.html", f"{len(apercu) / 1e6:.1f} Mo")


if __name__ == "__main__":
    main(json.loads(Path(sys.argv[1]).read_text()))
