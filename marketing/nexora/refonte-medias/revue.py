"""Review sheet of the delivered media: reads site-medias/manifest.json, writes light thumbnails (JPG) into revue/,
a page revue/index.html (role, format, duration, weight, prompt) and a contact sheet planche-medias.jpg.
Usage: python3 revue.py"""
import html, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI / "outils"))
import exporter
from planche import duree, image_a

LIVRE = exporter.LIVRE
REV = ICI / "revue"
REV.mkdir(exist_ok=True)
m = json.loads(exporter.MANIFESTE.read_text())
POL = Path.home() / "Desktop/NexoraSite/web/src/fonts"
f_eti = ImageFont.truetype(str(POL / "jetbrains-mono-latin-wght-normal.woff2"), 15)


def vignette(im, w=480):
    return im.convert("RGB").resize((w, round(w * im.height / im.width)), Image.LANCZOS)


cartes, tuiles = [], []
for nom, e in m["medias"].items():
    if e["type"] == "image":
        im = Image.open(LIVRE / e["fichiers"]["16x9"][2])
        v = vignette(im)
        v.save(REV / f"{nom}.jpg", quality=78)
        extra = "".join(f'<img src="{nom}-{r}.jpg" class="v" alt="">' for r in e["fichiers"] if r != "16x9")
        for r in e["fichiers"]:
            if r != "16x9":
                vignette(Image.open(LIVRE / e["fichiers"][r][2]), 160).save(REV / f"{nom}-{r}.jpg", quality=78)
        poids = sum(e["octets"].values()) / 1e6
        meta = f"image · {', '.join(e['dimensions'].values())} · {poids:.1f} Mo (toutes déclinaisons)"
        tuiles.append((nom, v))
    else:
        src = LIVRE / e["fichiers"]["web_h264"]
        d = duree(src)
        ims = [image_a(src, d * (k + 0.5) / 4) for k in range(4)]
        w = 240 if ims[0].width > ims[0].height else 110
        bande = Image.new("RGB", (w * 4 + 6, round(w * ims[0].height / ims[0].width)))
        for k, im in enumerate(ims):
            bande.paste(vignette(im, w), (k * (w + 2), 0))
        bande.save(REV / f"{nom}.jpg", quality=78)
        extra = ""
        meta = (f"vidéo · {e['dimensions']} · {e['duree_s']:.1f} s · {e['langue']} · H.264 "
                f"{e['octets'][e['fichiers']['web_h264']] / 1e6:.1f} Mo / WebM {e['octets'][e['fichiers']['web_webm']] / 1e6:.1f} Mo")
        tuiles.append((nom, vignette(ims[1])))
    prompt = e.get("prompt") or json.dumps(e.get("plans_h3", ""), ensure_ascii=False)[:600]
    cartes.append(f'<article><img src="{nom}.jpg" alt="">{extra}<h2>{html.escape(nom)}</h2><p class="m">{html.escape(meta)}</p>'
                  f'<p>{html.escape(e["role"])}</p><details><summary>prompt</summary><p class="p">{html.escape(str(prompt))}</p></details></article>')

page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Médias de la refonte</title><style>
:root{{--abysse:#05070B;--surface:#0B0F16;--filet:#1C2433;--texte:#EEF3FA;--t2:#8C97AA;--ion:#3EC8FF}}
body{{margin:0;background:var(--abysse);color:var(--texte);font:15px/1.5 Inter,system-ui,sans-serif;padding:32px 16px}}
h1{{font:600 32px/1.1 Geist,system-ui;letter-spacing:-.03em;margin:0 0 4px}} .s{{color:var(--t2);margin:0 0 24px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,500px),1fr));gap:16px}}
article{{background:var(--surface);border:1px solid var(--filet);border-radius:6px;padding:10px}}
article img{{max-width:100%;display:block}} article img.v{{display:inline-block;height:90px;margin:6px 6px 0 0}}
h2{{font:500 14px/1.3 "JetBrains Mono",monospace;color:var(--ion);margin:10px 0 2px;text-transform:uppercase;letter-spacing:.04em}}
.m{{color:var(--t2);font-size:13px;margin:0}} .p{{color:var(--t2);font-size:12px}} summary{{cursor:pointer;color:var(--t2)}}
</style></head><body><h1>Médias de la refonte « Signal »</h1>
<p class="s">{len(m['medias'])} médias · manifeste : ~/nexora-creative-data/site-medias/manifest.json · généré le {m['genere_le']}</p>
<main>{''.join(cartes)}</main></body></html>"""
(REV / "index.html").write_text(page)

# contact sheet
col, tw = 4, 420
th = round(tw * 9 / 16)
lig = -(-len(tuiles) // col)
P = Image.new("RGB", (col * (tw + 8) + 8, lig * (th + 30) + 8), (5, 7, 11))
d = ImageDraw.Draw(P)
for k, (nom, v) in enumerate(tuiles):
    x, y = 8 + (k % col) * (tw + 8), 8 + (k // col) * (th + 30)
    v = v.copy()
    v.thumbnail((tw, th))
    P.paste(v, (x + (tw - v.width) // 2, y))
    d.text((x, y + th + 6), nom, font=f_eti, fill=(62, 200, 255))
P.save(ICI / "planche-medias.jpg", quality=82)
print(REV / "index.html", ICI / "planche-medias.jpg", len(tuiles))
