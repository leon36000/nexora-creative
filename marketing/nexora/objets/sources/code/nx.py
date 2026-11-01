"""Bibliotheque commune de la famille OBJETS : couleurs de marque, logos officiels (lus sans modification),
mosaique (portage fidele de web/src/components/brand/mosaic.tsx), texte en contours (Geist 500), rendu Chromium.

Toutes les oeuvres sont des fragments SVG en MILLIMETRES : meme source pour le fichier de fabrication (echelle reelle)
et pour la maquette (rasterisee puis posee en perspective)."""
import io, json, re, subprocess, tempfile, os, math
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]            # .../objets
SRC = RACINE / "sources"
GENEREES = SRC / "generees"
FINAL = RACINE / "final"
LOGOS = Path("/home/pc6/Desktop/NexoraSite/docs/marque/logos")
FONTS = Path("/home/pc6/Desktop/NexoraSite/web/src/fonts")
BUN = "/home/pc6/.local/bin/bun"

# ---------------------------------------------------------------- couleurs (charte)
NOIR, SURFACE, PAPIER, CREME, OS, GRIS = "#0A0A0E", "#121218", "#FBFBF8", "#F3F2EC", "#F5F4EF", "#A8A8B6"
ORANGE, ORANGE_TXT, ORANGE_CLAIR, NUIT = "#FF5A1F", "#FF7A45", "#B53A0A", "#11112A"
ORANGE_LOGO_CLAIR = "#F04A10"        # orange du logo officiel sur fond clair
BRAISE = ["#FFD37A", "#FFB11A", "#FF8A1F", "#FF5A1F", "#E0341C", "#B01A3C"]

# Valeurs Pantone APPROCHEES (a valider sur nuancier physique) + equivalents indicatifs
COULEURS = {
    "noir":   dict(nom="Noir profond",   hex=NOIR,    pantone="Black 6 C (approx.)",              cmjn="C75 M68 Y67 K90"),
    "surface": dict(nom="Surface",       hex=SURFACE, pantone="Black 7 C (approx.)",              cmjn="C70 M62 Y60 K80"),
    "os":     dict(nom="Os (texte clair)", hex=OS,    pantone="Warm Gray 1 C eclairci (approx.)", cmjn="C2 M2 Y5 K0"),
    "creme":  dict(nom="Creme / ecru",   hex=CREME,   pantone="9224 C ou Warm Gray 1 C (approx.)", cmjn="C3 M3 Y8 K0"),
    "orange": dict(nom="Orange signal",  hex=ORANGE,  pantone="1655 C (alt. Orange 021 C) (approx.)", cmjn="C0 M75 Y100 K0"),
    "orange_clair": dict(nom="Orange signal sur fond clair", hex=ORANGE_LOGO_CLAIR, pantone="172 C (approx.)", cmjn="C0 M80 Y100 K0"),
    "b0": dict(nom="Braise 1", hex=BRAISE[0], pantone="1215 C (approx.)", cmjn="C0 M20 Y60 K0"),
    "b1": dict(nom="Braise 2", hex=BRAISE[1], pantone="1235 C (approx.)", cmjn="C0 M32 Y100 K0"),
    "b2": dict(nom="Braise 3", hex=BRAISE[2], pantone="151 C (approx.)", cmjn="C0 M58 Y100 K0"),
    "b3": dict(nom="Braise 4 (= orange signal)", hex=BRAISE[3], pantone="1655 C (approx.)", cmjn="C0 M75 Y100 K0"),
    "b4": dict(nom="Braise 5", hex=BRAISE[4], pantone="485 C (approx.)", cmjn="C5 M90 Y100 K0"),
    "b5": dict(nom="Braise 6", hex=BRAISE[5], pantone="201 C (approx.)", cmjn="C15 M100 Y65 K20"),
    "or_feuille": dict(nom="Dorure / feuille orange", hex=ORANGE, pantone="Feuille orange vif (a choisir sur echantillon)", cmjn="n/a (feuille)"),
}


def rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- logos officiels (lecture seule)
def _lire_svg(nom):
    t = (LOGOS / nom).read_text()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', t).group(1).split()]
    paths = re.findall(r'<path fill="([^"]+)" d="([^"]+)"', t)
    return vb, paths


def logo_officiel(fichier, x, y, largeur):
    """Fragment SVG (mm) du logo officiel tel quel (aucune modification des trace), pose en (x,y) a la largeur donnee.
    Retourne (fragment, hauteur)."""
    vb, paths = _lire_svg(fichier)
    s = largeur / vb[2]
    g = "".join(f'<path fill="{f}" d="{d}"/>' for f, d in paths)
    return (f'<g transform="translate({x - vb[0] * s:.4f} {y - vb[1] * s:.4f}) scale({s:.6f})">{g}</g>', vb[3] * s)


# variantes de symbole : (encre, accent)
SYMBOLES = {"sombre": ("nexora-ai-symbole-sombre.svg"), "clair": "nexora-ai-symbole.svg",
            "blanc": "nexora-ai-symbole-blanc.svg", "noir": "nexora-ai-symbole-noir.svg"}
LOGOS_COMPLETS = {"sombre": "nexora-ai-logo-sombre.svg", "clair": "nexora-ai-logo.svg",
                  "blanc": "nexora-ai-logo-blanc.svg", "noir": "nexora-ai-logo-noir.svg"}


def symbole(x, y, taille, variante="sombre"):
    """Symbole officiel (carre) : taille = cote en mm."""
    return logo_officiel(SYMBOLES[variante], x, y, taille)[0]


def logo_complet(x, y, largeur, variante="sombre"):
    return logo_officiel(LOGOS_COMPLETS[variante], x, y, largeur)


def zone_protection(taille):
    return taille * 10 / 52 * (52 / 52)   # 10 unites sur 64 -> 0,2 x la hauteur du symbole (charte)


# ---------------------------------------------------------------- mosaique (port de mosaic.tsx)
M32 = 0xFFFFFFFF


def _imul(a, b):
    return (a * b) & M32


def _hash(col, row, seed):
    h = _imul(col + 1, 73856093) ^ _imul(row + 1, 19349663) ^ _imul(seed + 1, 83492791)
    h = _imul(h ^ (h >> 15), 2246822507)
    h = _imul(h ^ (h >> 13), 3266489909)
    return ((h ^ (h >> 16)) & M32) / 4294967296


def _progress(col, row, cols, rows, toward):
    x = col / (cols - 1) if cols > 1 else .5
    y = row / (rows - 1) if rows > 1 else .5
    if toward == "right": return x
    if toward == "left": return 1 - x
    if toward == "bottom": return y
    if toward == "top": return 1 - y
    return max(0, 1 - math.hypot((x - .5) * 2, (y - .5) * 2) / 1.2)


def mosaic_cells(cols, rows, seed=1, toward="right", fade=0.9, tiers=6):
    out = []
    for row in range(rows):
        for col in range(cols):
            noise = _hash(col, row, seed)
            t = _progress(col, row, cols, rows, toward)
            v = 0.82 * t * fade + (1 - fade) * 0.5 + (noise - 0.5) * 0.7
            if fade > 0:
                keep = 0.03 + 0.92 * ((t ** 1.7) * fade + (1 - fade))
                if _hash(col, row, seed + 101) > keep or v <= 0.2:
                    continue
            tier = max(0, min(tiers - 1, math.floor(v * tiers)))
            out.append((col, row, tier))
    return out


def svg_mosaic(x, y, w, cols, rows, seed=1, toward="right", fade=0.9, gap=0.07, palette=BRAISE, keep=None, cell_h=None):
    """Mosaique SVG (mm) : une couche (chemin) par teinte. Cellules carrees de cote w/cols."""
    c = w / cols
    ins = gap * c / 2
    side = c * (1 - gap)
    layers = {}
    for col, row, tier in mosaic_cells(cols, rows, seed, toward, fade, len(palette)):
        if keep and not keep(col, row):
            continue
        layers.setdefault(tier, []).append(f"M{x + col * c + ins:.3f} {y + row * c + ins:.3f}h{side:.3f}v{side:.3f}h{-side:.3f}z")
    return "".join(f'<path fill="{palette[t]}" d="{"".join(d)}"/>' for t, d in sorted(layers.items()))


def svg_n_mosaique(x, y, taille, seed=7, k=6, marge=7, gap=0.08):
    """Le « N » reconstitue en pixels de braise : carres qui se rassemblent en N (motif approuve), dont le haut se dissout
    en braises qui montent. Derive graphique du symbole (le logo officiel n'est jamais altere : voir LISEZMOI).
    taille = cote du champ total (N + marge de dispersion) en mm."""
    G = 5 * k                       # N : 5 x 5 macro-cellules, k sous-pixels chacune
    cols = G + 2 * marge
    c = taille / cols
    ins = gap * c / 2
    side = c * (1 - gap)
    layers, diag = {}, []

    def dans_n(cc, rr):
        mx, my = cc // k, rr // k
        if mx in (0, 4): return "m"
        if (mx, my) in ((1, 1), (2, 2), (3, 3)): return "d"
        return None

    def ajoute(col, row, teinte):
        layers.setdefault(teinte, []).append(f"M{x + col * c + ins:.3f} {y + row * c + ins:.3f}h{side:.3f}v{side:.3f}h{-side:.3f}z")

    for rr in range(G):
        for cc in range(G):
            t = dans_n(cc, rr)
            if not t: continue
            n1 = _hash(cc, rr, seed)
            n2 = _hash(cc, rr, seed + 5)
            hauteur = rr / (G - 1)            # 0 haut -> 1 bas
            # dissolution : le haut du N se detache en braises
            if t == "d":
                teinte = 3 if n1 < .72 else (2 if n1 < .86 else 4)   # la diagonale reste l'orange signal
            else:
                v = 0.06 + 0.84 * hauteur + (n1 - .5) * 0.5
                teinte = max(0, min(5, int(v * 6)))
            p_detache = (max(0.0, 0.36 - hauteur) / 0.36) ** 1.15 * .92
            if n2 < p_detache and t == "m":
                dx = int(round((_hash(cc, rr, seed + 11) - .5) * 2.2))
                dy = -int(2 + _hash(cc, rr, seed + 17) ** 1.4 * (15 * (0.36 - hauteur) / 0.36 + 1))
                col, row = cc + marge + dx, rr + marge + dy
                if 0 <= col < cols and 0 <= row < cols:
                    ajoute(col, row, max(0, teinte - 1))
                continue
            ajoute(cc + marge, rr + marge, teinte)
    # braises isolees supplementaires au-dessus
    for i in range(26):
        col = int(_hash(i, 1, seed + 31) * cols)
        row = int(_hash(i, 2, seed + 37) * (marge + k * 1.2))
        if _hash(i, 3, seed + 41) < .55 and (marge - 1 <= col < marge + G + 1 or _hash(i, 4, seed) < .25):
            ajoute(col, row, int(_hash(i, 5, seed + 43) * 3))
    return "".join(f'<path fill="{BRAISE[t]}" d="{"".join(d)}"/>' for t, d in sorted(layers.items()))


# ---------------------------------------------------------------- texte en contours (Geist 500)
class Police:
    def __init__(self, chemin):
        from fontTools.ttLib import TTFont
        import uharfbuzz as hb
        tt = TTFont(str(chemin)); tt.flavor = None
        b = io.BytesIO(); tt.save(b); data = b.getvalue()
        self.tt = TTFont(io.BytesIO(data)); self.upem = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet(); self.ordre = self.tt.getGlyphOrder()
        self.hb = hb; self.font = hb.Font(hb.Face(hb.Blob(data)))

    def trace(self, texte, taille, x=0.0, y=0.0, suivi=0.0, ancrage="start"):
        """Retourne (d, largeur) : chemin SVG des lettres, ligne de base en y, taille = corps en mm."""
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        buf = self.hb.Buffer(); buf.add_str(texte); buf.guess_segment_properties()
        self.hb.shape(self.font, buf, {"kern": True, "liga": True})
        s = taille / self.upem
        pos = 0.0; d = []
        glyphes = []
        for info, p in zip(buf.glyph_infos, buf.glyph_positions):
            glyphes.append((info.codepoint, pos + p.x_offset * s, p.y_offset * s)); pos += p.x_advance * s + suivi * taille
        largeur = pos - suivi * taille
        dx = 0 if ancrage == "start" else (-largeur / 2 if ancrage == "middle" else -largeur)
        for gid, gx, gy in glyphes:
            pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.3f}".rstrip("0").rstrip("."))
            tp = TransformPen(pen, (s, 0, 0, -s, x + dx + gx, y - gy))
            self.gs[self.ordre[gid]].draw(tp)
            d.append(pen.getCommands())
        return "".join(d), largeur


_geist = None


def geist():
    global _geist
    if _geist is None:
        _geist = Police(FONTS / "og" / "geist-latin-500-normal.woff")
    return _geist


def texte(txt, x, y, taille, couleur, suivi=-0.03, ancrage="start"):
    """Texte Geist 500 en contours. Retourne (fragment, largeur)."""
    d, w = geist().trace(txt, taille, x, y, suivi, ancrage)
    return f'<path fill="{couleur}" d="{d}"/>', w


# ---------------------------------------------------------------- SVG / rendu
def svg_doc(w, h, corps, fond=None, extra_defs=""):
    bg = f'<rect width="{w}" height="{h}" fill="{fond}"/>' if fond else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            f'{extra_defs}{bg}{corps}</svg>')


def _jobs(jobs):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(jobs, f); nom = f.name
    try:
        r = subprocess.run([BUN, str(SRC / "code" / "rend.mjs"), nom], capture_output=True, text=True, timeout=600)
        if r.returncode:
            raise RuntimeError(r.stderr[-2000:])
    finally:
        os.unlink(nom)


def rend_svg_png(svg, sortie, largeur_px, transparent=True, tmp=None):
    """Rastérise un SVG en mm (w x h donnes dans l'en-tete) a largeur_px."""
    m = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm"', svg)
    w, h = float(m.group(1)), float(m.group(2))
    hp = round(largeur_px * h / w)
    svg2 = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{largeur_px}" height="{hp}"', svg, count=1)
    tmp = Path(tmp or (SRC / "code" / "_tmp"))
    tmp.mkdir(parents=True, exist_ok=True)
    f = tmp / (Path(sortie).stem + "_svg.html")
    f.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:transparent}}svg{{display:block}}</style>{svg2}')
    _jobs([dict(type="png", src=str(f), out=str(sortie), width=largeur_px, height=hp, transparent=transparent)])
    return Path(sortie)


def rend_html(html, sortie, type_, w_px=1000, h_px=1000, wmm=None, hmm=None, scale=1, transparent=False, tmp=None):
    tmp = Path(tmp or (SRC / "code" / "_tmp")); tmp.mkdir(parents=True, exist_ok=True)
    f = tmp / (Path(sortie).stem + ".html"); f.write_text(html)
    _jobs([dict(type=type_, src=str(f), out=str(sortie), width=w_px, height=h_px, wmm=wmm, hmm=hmm, scale=scale, transparent=transparent)])
    return Path(sortie)


def police_css():
    return "".join(f"@font-face{{font-family:'{n}';src:url('file://{FONTS}/{f}') format('woff2');font-weight:100 900}}" for n, f in
                   (("Geist", "geist-latin-wght-normal.woff2"), ("Inter", "inter-latin-wght-normal.woff2"),
                    ("JetBrains Mono", "jetbrains-mono-latin-wght-normal.woff2")))
