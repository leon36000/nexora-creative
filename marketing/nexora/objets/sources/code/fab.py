"""Fichiers de fabrication : gabarit SVG/PDF vectoriel A L'ECHELLE REELLE (mm), calques nommes pour le fournisseur,
et fiche de specifications (couleurs Pantone approchees + RVB/CMJN indicatifs, technique, notes)."""
import html, subprocess
from nx import *

C_IMPR, C_COUPE, C_SEC, C_REP = "#00AEEF", "#EC008C", "#00A651", "#7C7C88"
MARGE = 22


class Gabarit:
    """Planche a l'echelle 1:1. Coordonnees en mm depuis le coin haut-gauche de la zone utile ; marge ajoutee autour."""
    def __init__(self, w, h, marge=MARGE):
        self.w, self.h, self.m = w, h, marge
        self.l = {k: [] for k in ("FOND", "ART", "FEUILLE-ORANGE", "GAUFRAGE-SEC", "SILHOUETTE", "COUPE", "ZONE-IMPRESSION", "SECURITE", "REPERES", "NOTES")}

    def _t(self, x, y):
        return x + self.m, y + self.m

    def add(self, calque, frag, dx=0, dy=0):
        self.l[calque].append(f'<g transform="translate({self.m + dx:.3f} {self.m + dy:.3f})">{frag}</g>')

    def rect(self, calque, x, y, w, h, couleur, dash="", rx=0, sw=0.35, fill="none"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(calque, f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{rx}" fill="{fill}" stroke="{couleur}" stroke-width="{sw}"{d}/>')

    def path(self, calque, d, couleur, dash="", sw=0.35, fill="none"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(calque, f'<path d="{d}" fill="{fill}" stroke="{couleur}" stroke-width="{sw}"{da}/>')

    def ligne(self, calque, x1, y1, x2, y2, couleur=C_REP, sw=0.25, dash=""):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(calque, f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{couleur}" stroke-width="{sw}"{da}/>')

    def note(self, x, y, txt, taille=3.2, couleur=C_REP, ancrage="start", calque="NOTES"):
        frag, w = texte(txt, 0, 0, taille, couleur, suivi=0.0, ancrage=ancrage)
        self.add(calque, f'<g transform="translate({x:.3f} {y:.3f})">{frag}</g>')
        return w

    def cote_h(self, x1, x2, y, txt, taille=3.2):
        self.ligne("NOTES", x1, y, x2, y, C_REP, .25)
        for x in (x1, x2):
            self.ligne("NOTES", x, y - 1.6, x, y + 1.6, C_REP, .25)
        self.note((x1 + x2) / 2, y - 1.8, txt, taille, ancrage="middle")

    def cote_v(self, x, y1, y2, txt, taille=3.2):
        self.ligne("NOTES", x, y1, x, y2, C_REP, .25)
        for y in (y1, y2):
            self.ligne("NOTES", x - 1.6, y, x + 1.6, y, C_REP, .25)
        frag, w = texte(txt, 0, 0, taille, C_REP, suivi=0.0, ancrage="middle")
        self.add("NOTES", f'<g transform="translate({x - 2.2:.3f} {(y1 + y2) / 2:.3f}) rotate(-90)">{frag}</g>')

    def reperes(self, longueur=6):
        """Traits de coupe aux quatre angles de la zone utile + croix de centrage."""
        w, h = self.w, self.h
        for (x, y, sx, sy) in ((0, 0, -1, -1), (w, 0, 1, -1), (w, h, 1, 1), (0, h, -1, 1)):
            self.ligne("REPERES", x + sx * 2, y, x + sx * (2 + longueur), y, "#000", .25)
            self.ligne("REPERES", x, y + sy * 2, x, y + sy * (2 + longueur), "#000", .25)
        self.ligne("REPERES", w / 2 - 4, h + 8, w / 2 + 4, h + 8, "#000", .25)
        self.ligne("REPERES", w / 2, h + 4, w / 2, h + 12, "#000", .25)

    def svg(self, titre="", fond="#FFFFFF"):
        W, H = self.w + 2 * self.m, self.h + 2 * self.m
        ns = ('xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
              f'width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.3f} {H:.3f}"')
        g = ""
        ordre = ("FOND", "SILHOUETTE", "ART", "GAUFRAGE-SEC", "FEUILLE-ORANGE", "ZONE-IMPRESSION", "SECURITE", "COUPE", "REPERES", "NOTES")
        for k in ordre:
            if not self.l[k] and k != "FOND":
                continue
            if k == "FOND":
                g += f'<g id="FOND-GABARIT" inkscape:groupmode="layer" inkscape:label="FOND-GABARIT (non imprime)"><rect width="{W}" height="{H}" fill="{fond}"/></g>'
                continue
            g += f'<g id="{k}" inkscape:groupmode="layer" inkscape:label="{k}">{"".join(self.l[k])}</g>'
        return f'<svg {ns}><title>{html.escape(titre)}</title>{g}</svg>'


def cmjn_indicatif(hexa):
    r, g, b = [v / 255 for v in rgb(hexa)]
    k = 1 - max(r, g, b)
    if k >= 1: return "C0 M0 Y0 K100"
    c, m, y = [(1 - v - k) / (1 - k) for v in (r, g, b)]
    f = lambda v: int(round(v * 100 / 5) * 5)
    return f"C{f(c)} M{f(m)} Y{f(y)} K{f(k)}"


def table_couleurs(cles):
    lignes = ""
    for c in cles:
        d = COULEURS[c]
        r, g, b = rgb(d["hex"])
        cm = d["cmjn"] if d["cmjn"] != "n/a (feuille)" else d["cmjn"]
        lignes += (f'<tr><td><i style="background:{d["hex"]}"></i></td><td>{html.escape(d["nom"])}</td><td class="m">{d["hex"]}</td>'
                   f'<td class="m">{r} {g} {b}</td><td class="m">{cm}</td><td>{html.escape(d["pantone"])}</td></tr>')
    return lignes


CSS_FICHE = """
@page{size:215.9mm 279.4mm;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,sans-serif;color:#0A0A0E;background:#FBFBF8;-webkit-print-color-adjust:exact}
.p{width:215.9mm;height:279.4mm;padding:11mm 13mm 12mm;position:relative;overflow:hidden}
.bandeau{display:flex;gap:1.6mm;position:absolute;left:0;right:0;bottom:0;height:3mm}
.bandeau b{flex:1}
h1{font-family:Geist,sans-serif;font-weight:500;font-size:9.5mm;line-height:1;letter-spacing:-.03em;margin:2mm 0 1mm}
.lib{font-family:'JetBrains Mono',monospace;font-size:2.7mm;letter-spacing:.06em;text-transform:uppercase;color:#54545F}
.sec{font-family:'JetBrains Mono',monospace;font-size:2.5mm;letter-spacing:.06em;text-transform:uppercase;color:#B53A0A;margin:3.4mm 0 1.2mm;border-top:.25mm solid #0A0A0E22;padding-top:1.4mm}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:8mm}
p,li{font-size:2.85mm;line-height:1.42;margin:0 0 .8mm}
ul{padding-left:4mm;margin:0}
table{width:100%;border-collapse:collapse;font-size:2.7mm}
td,th{padding:.7mm 1.2mm;border-bottom:.2mm solid #0A0A0E22;text-align:left;vertical-align:middle}
th{font-family:'JetBrains Mono',monospace;font-size:2.3mm;letter-spacing:.06em;text-transform:uppercase;color:#54545F;font-weight:500}
td.m{font-family:'JetBrains Mono',monospace;font-size:2.4mm}
td i{display:block;width:3.8mm;height:3.8mm;border-radius:.8mm;border:.2mm solid #0A0A0E33}
.vue{background:#fff;border:.25mm solid #0A0A0E22;border-radius:1.5mm;display:flex;align-items:center;justify-content:center;height:60mm;padding:2mm}
.vue svg{max-width:100%;max-height:100%}
.pied{position:absolute;left:13mm;right:13mm;bottom:5.5mm;font-size:2.1mm;color:#54545F;line-height:1.45}
.sq{display:inline-block;width:3mm;height:3mm;background:#FF5A1F;margin-right:2mm;vertical-align:-.3mm}
"""


def fiche_html(o, svg_gabarit):
    """Fiche de specifications Letter, bilingue (fr-CA d'abord, EN-CA en regard)."""
    bandeau = "".join(f'<b style="background:{c}"></b>' for c in BRAISE[1:5])
    long = len(o["couleurs"]) > 6
    extra = ".vue{height:40mm}td,th{padding:.35mm 1.2mm}td i{width:3mm;height:3mm}.sec{margin:2.4mm 0 .8mm}" if long else ""
    notes_fr = "".join(f"<li>{html.escape(n)}</li>" for n in o["notes_fr"])
    notes_en = "".join(f"<li>{html.escape(n)}</li>" for n in o["notes_en"])
    zones = "".join(f"<li>{html.escape(z)}</li>" for z in o["zones"])
    return f"""<!doctype html><meta charset=utf-8><style>{police_css()}{CSS_FICHE}{extra}</style>
<div class=p>
<div class=lib><span class=sq></span>Nexora AI · fiche de fabrication · production sheet</div>
<h1>{html.escape(o['nom_fr'])}</h1>
<div class=lib>{html.escape(o['nom_en'])} · réf. NX-OBJ-{o['num']:02d}</div>
<div class=sec>Gabarit à l'échelle réelle : voir page 1 (SVG/PDF vectoriel) · Layout at real scale: page 1</div>
<div class=vue>{svg_gabarit}</div>
<div class=cols>
 <div><div class=sec>Technique · Technique</div><p><b>{html.escape(o['technique_fr'])}</b><br>{html.escape(o['technique_en'])}</p>
 <div class=sec>Matériau · Material</div><p>{html.escape(o['materiau_fr'])}<br><span style="color:#54545F">{html.escape(o['materiau_en'])}</span></p></div>
 <div><div class=sec>Zones et dimensions · Zones and sizes</div><ul>{zones}</ul>
 <div class=sec>Quantité minimale indicative · Indicative MOQ</div><p>{html.escape(o['moq_fr'])}<br><span style="color:#54545F">{html.escape(o['moq_en'])}</span></p></div>
</div>
<div class=sec>Couleurs · Colours (Pantone approchés, RVB et CMJN indicatifs)</div>
<table><tr><th></th><th>Nom</th><th>Hex</th><th>RVB</th><th>CMJN indicatif</th><th>Pantone approché</th></tr>{table_couleurs(o['couleurs'])}</table>
<div class=cols>
 <div><div class=sec>Notes de fabrication</div><ul>{notes_fr}</ul></div>
 <div><div class=sec>Production notes</div><ul>{notes_en}</ul></div>
</div>
<div class=pied>Valeurs Pantone et CMJN approchées, à valider sur échantillon physique ou épreuve avant production ; le logo se pose toujours à partir des fichiers officiels, jamais redessiné. Pantone and CMYK values are approximations: validate on a physical proof before production. Quantités minimales indicatives, à confirmer auprès du fournisseur.</div>
<div class=bandeau>{bandeau}</div></div>"""


def ecrire_fabrication(o, g, dossier, suffixe=""):
    """Ecrit <dossier>/<slug>-fabrication.svg + .pdf (page 1 gabarit echelle 1:1, page 2 fiche)."""
    dossier = Path(dossier); dossier.mkdir(parents=True, exist_ok=True)
    nom = f"{o['num']:02d}-{o['slug']}{suffixe}"
    svg = g.svg(titre=f"Nexora AI - {o['nom_fr']} - gabarit 1:1")
    (dossier / f"{nom}-fabrication.svg").write_text(svg)
    W, H = g.w + 2 * g.m, g.h + 2 * g.m
    tmp = SRC / "code" / "_tmp"; tmp.mkdir(parents=True, exist_ok=True)
    p1 = tmp / f"{nom}-p1.html"
    p1.write_text(f'<!doctype html><meta charset=utf-8><style>@page{{size:{W:.2f}mm {H:.2f}mm;margin:0}}html,body{{margin:0}}svg{{display:block}}</style>{svg}')
    pdf1 = tmp / f"{nom}-p1.pdf"
    from nx import _jobs
    _jobs([dict(type="pdf", src=str(p1), out=str(pdf1), wmm=round(W, 2), hmm=round(H, 2))])
    # fiche : gabarit reduit
    petit = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', 'width="100%" height="100%"', svg, count=1)
    p2 = tmp / f"{nom}-p2.html"
    p2.write_text(fiche_html(o, petit))
    pdf2 = tmp / f"{nom}-p2.pdf"
    _jobs([dict(type="pdf", src=str(p2), out=str(pdf2), wmm=215.9, hmm=279.4)])
    sortie = dossier / f"{nom}-fabrication.pdf"
    subprocess.run(["pdfunite", str(pdf1), str(pdf2), str(sortie)], check=True)
    return sortie
