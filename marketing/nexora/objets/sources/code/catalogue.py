"""Catalogue PDF (fr-CA et en-CA) + planche-contact apercu.png.  python catalogue.py [--apercu] [--pdf]"""
import sys, html, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import registre
from fab import *
import cv2

W, H = 1920, 1080


def heros():
    out = {}
    for o, *_ in registre():
        nom = f"{o['num']:02d}-{o['slug']}"
        d = FINAL / nom
        fs = sorted(d.glob(f"{nom}-maquette*.jpg"), key=lambda p: (p.stem != f"{nom}-maquette", p.name))
        if fs: out[o["num"]] = fs[0]
    return out


def mini(p, taille, nom):
    dest = SRC / "code" / "_tmp" / f"{nom}.jpg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = cv2.imread(str(p)); im = cv2.resize(im, (taille, taille), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(dest), im, [cv2.IMWRITE_JPEG_QUALITY, 90]); return dest


CSS = """
*{box-sizing:border-box;margin:0}
body{width:1920px;background:#0A0A0E;color:#F5F4EF;font-family:Inter,sans-serif;-webkit-print-color-adjust:exact}
.page{width:1920px;height:1080px;position:relative;overflow:hidden;background:#0A0A0E;page-break-after:always}
.img{position:absolute;left:0;top:0;width:1080px;height:1080px}
.col{position:absolute;left:1160px;top:92px;width:680px;bottom:92px}
.lib{font-family:'JetBrains Mono',monospace;font-size:17px;letter-spacing:.06em;text-transform:uppercase;color:#FF7A45}
.gris{color:#A8A8B6}
h1{font-family:Geist,sans-serif;font-weight:500;font-size:60px;line-height:1.02;letter-spacing:-.03em;margin:20px 0 26px;text-wrap:balance}
.desc{font-size:23px;line-height:1.5;color:#F5F4EF;margin-bottom:34px}
.spec{border-top:1px solid rgba(245,244,239,.16);padding:16px 0 14px}
.spec p{font-size:19px;line-height:1.45;color:#A8A8B6;margin-top:6px}
.bas{position:absolute;left:1160px;right:80px;bottom:44px;display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:14px;letter-spacing:.06em;text-transform:uppercase;color:#A8A8B6}
.bande{position:absolute;left:1080px;right:0;bottom:0;height:10px;display:flex;gap:5px}.bande b{flex:1}
.sq{display:inline-block;width:14px;height:14px;background:#FF5A1F;margin-right:12px;vertical-align:-1px}
"""
TXT = {
 "fr": dict(objet="Objet", mat="Matériau", imp="Impression et fabrication", moq="Quantité minimale indicative", pied="Nexora AI · Objets promotionnels",
            titre_c="Objets promotionnels", sous_c="Rêvez grand. Gardez le contrôle.", note_c="Maquettes et fichiers de fabrication",
            fin="L'IA qui travaille pour votre entreprise. Sous votre contrôle.", ligne_q="IA souveraine au Québec"),
 "en": dict(objet="Object", mat="Material", imp="Print and production", moq="Indicative minimum quantity", pied="Nexora AI · Promotional objects",
            titre_c="Promotional objects", sous_c="Dream big. Stay in control.", note_c="Mock-ups and production files",
            fin="AI that works for your business. Under your control.", ligne_q="Sovereign AI, made in Québec"),
}


def page_objet(o, img, lang):
    t = TXT[lang]; s = "" if lang == "fr" else "_en"
    bande = "".join(f'<b style="background:{c}"></b>' for c in BRAISE[1:5])
    return f"""<section class=page><img class=img src="file://{img}">
<div class=col><div class=lib><span class=sq></span>{t['objet']} {o['num']:02d}</div>
<h1>{html.escape(o['nom_fr'] if lang=='fr' else o['nom_en'])}</h1>
<p class=desc>{html.escape(o['desc_fr'] if lang=='fr' else o['desc_en'])}</p>
<div class=spec><div class=lib>{t['mat']}</div><p>{html.escape(o['materiau_fr'] if lang=='fr' else o['materiau_en'])}</p></div>
<div class=spec><div class=lib>{t['imp']}</div><p>{html.escape(o['technique_fr'] if lang=='fr' else o['technique_en'])}</p></div>
<div class=spec><div class=lib>{t['moq']}</div><p>{html.escape(o['moq_fr'] if lang=='fr' else o['moq_en'])}</p></div></div>
<div class=bas><span>{t['pied']}</span><span>{o['num']:02d}</span></div><div class=bande>{bande}</div></section>"""


def page_couverture(lang):
    t = TXT[lang]
    mos = svg_mosaic(0, 0, 1000, 40, 40, seed=5, toward="right", fade=.9)
    sym = symbole(0, 0, 100, "sombre")
    return f"""<section class=page>
<svg style="position:absolute;right:0;top:40px;width:1000px;height:1000px" viewBox="0 0 1000 1000" shape-rendering="crispEdges">{mos}</svg>
<div style="position:absolute;left:100px;top:100px;width:140px"><svg viewBox="0 0 100 100" width="110">{sym}</svg></div>
<div style="position:absolute;left:100px;bottom:130px;width:900px"><div class=lib>{t['note_c']}</div>
<div style="font-family:Geist;font-weight:500;font-size:120px;line-height:1;letter-spacing:-.03em;margin:26px 0">{t['titre_c']}</div>
<div style="font-family:Geist;font-weight:500;font-size:40px;letter-spacing:-.02em;color:#FF7A45">{t['sous_c']}</div></div></section>"""


def page_fin(lang):
    t = TXT[lang]
    return f"""<section class=page><div style="position:absolute;left:100px;top:100px"><svg viewBox="0 0 100 100" width="110">{symbole(0,0,100,'sombre')}</svg></div>
<div style="position:absolute;left:100px;bottom:140px;width:1300px"><div style="font-family:Geist;font-weight:500;font-size:84px;line-height:1.04;letter-spacing:-.03em">{t['fin']}</div>
<div class=lib style="margin-top:40px">{t['ligne_q']}</div></div></section>"""


def pdf(lang):
    hs = heros(); pages = [page_couverture(lang)]
    for o, *_ in registre():
        if o["num"] in hs:
            pages.append(page_objet(o, mini(hs[o["num"]], 1080, f"cat_{o['num']:02d}"), lang))
    pages.append(page_fin(lang))
    doc = f"<!doctype html><meta charset=utf-8><style>{police_css()}{CSS}@page{{size:1920px 1080px;margin:0}}</style>" + "".join(pages)
    f = SRC / "code" / "_tmp" / f"catalogue_{lang}.html"; f.write_text(doc)
    sortie = FINAL / ("catalogue.pdf" if lang == "fr" else "catalogue-en.pdf")
    from nx import _jobs
    _jobs([dict(type="pdf", src=str(f), out=str(sortie), wmm=508.0, hmm=285.75)])
    return sortie


def apercu():
    hs = heros(); items = [(o, hs[o["num"]]) for o, *_ in registre() if o["num"] in hs]
    cols = 6; cell = 600; gap = 12; hdr = 140
    rows = (len(items) + cols - 1) // cols
    Wp, Hp = cols * cell + (cols + 1) * gap, hdr + rows * (cell + 44) + (rows + 1) * gap
    cells = ""
    for o, p in items:
        m = mini(p, cell, f"ap_{o['num']:02d}")
        cells += f'<figure><img src="file://{m}"><figcaption><span>{o["num"]:02d}</span>{html.escape(o["nom_fr"].split(",")[0].split(" (")[0])}</figcaption></figure>'
    doc = f"""<!doctype html><meta charset=utf-8><style>{police_css()}
*{{box-sizing:border-box;margin:0}}body{{width:{Wp}px;background:#0A0A0E;color:#F5F4EF;font-family:Inter}}
header{{height:{hdr}px;padding:44px {gap + 20}px 0;display:flex;align-items:baseline;justify-content:space-between}}
h1{{font:500 54px Geist;letter-spacing:-.03em}}.l{{font:16px 'JetBrains Mono';letter-spacing:.06em;text-transform:uppercase;color:#FF7A45}}
.g{{display:grid;grid-template-columns:repeat({cols},{cell}px);gap:{gap}px;padding:{gap}px}}
figure img{{display:block;width:{cell}px;height:{cell}px}}figcaption{{height:44px;display:flex;gap:14px;align-items:center;font:15px 'JetBrains Mono';letter-spacing:.04em;text-transform:uppercase;color:#A8A8B6}}figcaption span{{color:#FF7A45}}</style>
<header><h1>Objets promotionnels : planche-contact</h1><div class=l>Nexora AI · Rêvez grand. Gardez le contrôle.</div></header><div class=g>{cells}</div>"""
    f = SRC / "code" / "_tmp" / "apercu.html"; f.write_text(doc)
    from nx import _jobs
    _jobs([dict(type="png", src=str(f), out=str(RACINE / "apercu.png"), width=Wp, height=Hp)])
    return RACINE / "apercu.png"


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or "--pdf" in a:
        print(pdf("fr")); print(pdf("en"))
    if not a or "--apercu" in a:
        print(apercu())
