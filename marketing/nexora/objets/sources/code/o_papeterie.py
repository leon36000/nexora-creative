"""Papeterie : carnet, stylo gravé, planche d'autocollants."""
from fab import *
from mock import *


# ============================================================ 12 AUTOCOLLANTS
def contour_symbole(taille, bord, ppm=24):
    """Contour de decoupe qui suit le symbole (decalage arrondi de `bord` mm). Retourne (d, (w, h)) en mm, origine = coin du carre
    englobant le symbole + bord."""
    s = taille / 52.0
    rects = [(0, 0, 10.4, 52), (41.6, 0, 10.4, 52), (10.4, 10.4, 10.4, 10.4), (20.8, 20.8, 10.4, 10.4), (31.2, 31.2, 10.4, 10.4)]
    W = int((taille + 2 * bord) * ppm) + 4
    m = np.zeros((W, W), np.uint8)
    for (x, y, w, h) in rects:
        x0, y0 = int((x * s + bord) * ppm) + 2, int((y * s + bord) * ppm) + 2
        m[y0:y0 + int(h * s * ppm), x0:x0 + int(w * s * ppm)] = 255
    k = int(bord * ppm)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 0.08 * ppm / 4, True)[:, 0, :].astype(float)
    pts = (c - 2) / ppm
    d = "M" + " L".join(f"{x:.3f} {y:.3f}" for x, y in pts) + " Z"
    return d, ((W - 4) / ppm, (W - 4) / ppm)


TEXTES = {
    "fr": dict(controle="Sous votre contrôle", campagne="Rêvez grand. Gardez le contrôle."),
    "en": dict(controle="Under your control", campagne="Dream big. Stay in control."),
}
FEUILLE_W, FEUILLE_H, SAIGNEE = 148, 210, 1.6


def autocollants(lang="fr"):
    """Liste des 8 autocollants : dict(id, nom, x, y, w, h, rx, art (svg, coords absolues planche), coupe (path d absolu))."""
    T = TEXTES[lang]
    S = []

    def carre(id_, nom, x, y, w, h, fond, art, rx=3.0):
        b = SAIGNEE
        fondsvg = f'<rect x="{x - b}" y="{y - b}" width="{w + 2 * b}" height="{h + 2 * b}" fill="{fond}"/>'
        coupe = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/>'
        clip = f'<clipPath id="c{id_}"><rect x="{x - b}" y="{y - b}" width="{w + 2 * b}" height="{h + 2 * b}" rx="{rx + b}"/></clipPath>'
        S.append(dict(id=id_, nom=nom, x=x, y=y, w=w, h=h, rx=rx, art=fondsvg + art, coupe=coupe, clip=clip))

    # A : symbole sur noir
    a = 63; ss = 30
    carre("A", "Symbole sur fond noir", 8, 8, a, a, NOIR, symbole(8 + (a - ss) / 2, 8 + (a - ss) / 2, ss, "sombre"))
    # B : N en mosaique braise
    carre("B", "N en pixels de braise", 77, 8, a, a, NOIR, svg_n_mosaique(77 + 3, 8 + 3, a - 6, seed=1))
    # C : carre orange
    carre("C", "Carré orange", 8, 77, 30, 30, ORANGE, "", rx=2.0)
    # D : mosaique 5x5 (pastille de tuile)
    carre("D", "Tuile mosaïque", 41, 77, 30, 30, NOIR, svg_mosaic(41 + 3, 77 + 3, 24, 5, 5, seed=4, toward="center", fade=0.0, gap=0.08), rx=2.0)
    # E : symbole, decoupe contour (liseré blanc)
    ts, bord = 30, 2.2
    dE, (cw, ch) = contour_symbole(ts, bord)
    ex, ey = 77 + (a - cw) / 2, 77 - 1.5
    cE = f'<g transform="translate({ex:.3f} {ey:.3f})"><path d="{dE}" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="{2 * SAIGNEE}" stroke-linejoin="round"/></g>'
    sE = symbole(ex + bord, ey + bord, ts, "clair")
    S.append(dict(id="E", nom="Symbole, découpe contour", x=ex, y=ey, w=cw, h=ch, rx=0,
                  art=cE + sE, coupe=f'<path transform="translate({ex:.3f} {ey:.3f})" d="{dE}"/>', clip=""))
    # F : Sous votre controle
    W = 132
    tF, wt = texte(T["controle"], 0, 0, 8.2, OS)
    xt = 8 + 10
    carre("F", "« Sous votre contrôle » (bande noire)", 8, 113, W, 22, NOIR,
          f'<g transform="translate({xt} {113 + 22 / 2 + 8.2 * 0.36})">{tF}</g>'
          f'<rect x="{8 + W - 10 - 5}" y="{113 + 22 / 2 - 2.5}" width="5" height="5" fill="{ORANGE}"/>', rx=2.0)
    # G : campagne sur orange, texte noir
    tG, wg = texte(T["campagne"], 0, 0, 7.0, NOIR)
    carre("G", "Ligne de campagne (bande orange)", 8, 141, W, 22, ORANGE,
          f'<g transform="translate({8 + (W - wg) / 2} {141 + 22 / 2 + 7.0 * 0.36})">{tG}</g>', rx=2.0)
    # H : logo complet
    lw = 70
    lg, lh = logo_complet(0, 0, lw, "sombre")
    carre("H", "Logo complet (bande noire)", 8, 169, W, 22, NOIR, f'<g transform="translate({8 + (W - lw) / 2} {169 + (22 - lh) / 2})">{lg}</g>', rx=2.0)
    return S


def gabarit_autocollants(lang="fr"):
    g = Gabarit(FEUILLE_W, FEUILLE_H)
    st = autocollants(lang)
    defs = "".join(s["clip"] for s in st)
    g.add("SILHOUETTE", f'<rect width="{FEUILLE_W}" height="{FEUILLE_H}" rx="4" fill="#FFFFFF" stroke="#BBBBC4" stroke-width=".3"/>')
    for s in st:
        if s["clip"]:
            g.add("ART", f'<defs>{s["clip"]}</defs><g clip-path="url(#c{s["id"]})">{s["art"]}</g>')
        else:
            g.add("ART", s["art"])
        g.add("COUPE", f'<g fill="none" stroke="{C_COUPE}" stroke-width=".3">{s["coupe"]}</g>')
    g.rect("COUPE", 0, 0, FEUILLE_W, FEUILLE_H, C_COUPE, "3 1.5", rx=4, sw=.3)
    g.rect("SECURITE", 3, 3, FEUILLE_W - 6, FEUILLE_H - 6, C_SEC, "1.5 1.5", rx=2, sw=.25)
    g.note(0, -7, "COUPE (magenta) = ligne « CutContour » à la traversée du vinyle, sans le support ; art déborde de 1,6 mm (fonds perdus) · cadre pointillé = coupe de la planche", 3)
    g.note(0, FEUILLE_H + 13, "Planche A5 (148 × 210 mm) ; autocollants prédécoupés « kiss-cut » sur support siliconé", 3)
    return g


def _fiche_autocollants():
    return dict(
        num=12, slug="autocollants", nom_fr="Planche de huit autocollants", nom_en="Sheet of eight stickers",
        desc_fr="Huit autocollants prédécoupés : le symbole, le N en pixels de braise, le carré orange, une tuile de mosaïque, « Sous votre contrôle », la ligne de campagne et le logo. Faits pour un portable, une gourde, un casque.",
        desc_en="Eight kiss-cut stickers: the symbol, the N in ember pixels, the orange square, a mosaic tile, “Under your control”, the campaign line and the logo. Made for a laptop, a bottle, a helmet.",
        materiau_fr="Vinyle blanc mat ou brillant avec adhésif repositionnable, laminé anti-UV ; support siliconé ; planche A5.",
        materiau_en="White matte or gloss vinyl with repositionable adhesive, UV-laminated; siliconised liner; A5 sheet.",
        technique_fr="Impression numérique CMJN + blanc de fond si vinyle transparent, laminage, découpe contour (kiss-cut) à partir du tracé « CutContour » du calque COUPE.",
        technique_en="Digital CMYK print (+ white underprint on clear vinyl), lamination, kiss-cut along the “CutContour” path in the COUPE layer.",
        zones=["Planche : 148 × 210 mm ; fonds perdus de 1,6 mm autour de chaque autocollant ; marge de sécurité de 3 mm au bord de la planche.",
               "Autocollant E : liseré blanc de 2,2 mm qui suit le contour du symbole (jamais moins de 2 mm).",
               "Versions fr-CA et en-CA (fichiers distincts : -fr, -en)."],
        moq_fr="Environ 100 planches (indicatif, à confirmer).", moq_en="About 100 sheets (indicative, to be confirmed).",
        couleurs=["noir", "os", "orange", "orange_clair", "b0", "b1", "b2", "b4", "b5"],
        notes_fr=["Le noir de fond est le noir profond de la charte (C75 M68 Y67 K90 indicatif) : demander un noir riche, pas du CMJN 0/0/0/100.",
                  "Le texte et le logo sont en contours : aucune police à embarquer. Contraste texte/fond : os sur noir 17,9:1 ; noir sur orange 6,3:1.",
                  "Mosaïque et N en braise : générées avec une graine fixe, reproductibles ; ne pas redimensionner une tuile en dessous de 18 mm.",
                  "Aucune date, aucun chiffre, aucune URL tant que coordonnees.json est incomplet."],
        notes_en=["Background black is the brand deep black (indicative C75 M68 Y67 K90): ask for a rich black, not 0/0/0/100.",
                  "Text and logo are outlined: no font to embed. Contrast: bone on black 17.9:1; black on orange 6.3:1.",
                  "Mosaic and ember N are generated with a fixed seed and are reproducible; do not scale a tile below 18 mm.",
                  "No date, number or URL while coordonnees.json is incomplete."])


AUTOCOLLANTS = _fiche_autocollants()


def planche_png(lang="fr", ppm=12):
    g = gabarit_autocollants(lang)
    st = autocollants(lang)
    corps = f'<rect width="{FEUILLE_W}" height="{FEUILLE_H}" rx="4" fill="#F4F4F1"/>'
    for s in st:
        corps += f'<defs><clipPath id="k{s["id"]}">{s["coupe"]}</clipPath></defs><g clip-path="url(#k{s["id"]})">{s["art"]}</g>'
        corps += f'<g fill="none" stroke="#C9C9C4" stroke-width=".18">{s["coupe"]}</g>'
    return raster_art(svg_doc(FEUILLE_W, FEUILLE_H, corps), ppm, f"planche_{lang}"), st


def fond_sombre(taille=T, graine=2):
    """Fond d'atelier : ardoise sombre, lumiere rasante douce en haut a gauche."""
    yy, xx = np.mgrid[0:taille, 0:taille].astype(np.float32) / taille
    d = np.hypot(xx - .3, yy - .25)
    v = 0.115 - 0.085 * np.clip(d * 1.15, 0, 1)
    rng = np.random.default_rng(graine)
    n = cv2.GaussianBlur(rng.normal(0, 1, (taille, taille)).astype(np.float32), (0, 0), 1.2) * .006
    im = np.stack([v * 1.05, v * .98, v * .96], -1) + n[..., None]
    return np.clip(im, 0, 1).astype(np.float32)


def maquette_planche(lang="fr"):
    art, st = planche_png(lang, 12)
    base = fond_sombre()
    # feuille tournee de -5 degres, hauteur ~ 1900 px
    ech = 1880 / FEUILLE_H
    cx, cy = 1200, 1210
    th = np.deg2rad(-5.0)
    def pt(x, y):
        x, y = (x - FEUILLE_W / 2) * ech, (y - FEUILLE_H / 2) * ech
        return (cx + x * np.cos(th) - y * np.sin(th), cy + x * np.sin(th) + y * np.cos(th))
    quad = [pt(0, 0), pt(FEUILLE_W, 0), pt(FEUILLE_W, FEUILLE_H), pt(0, FEUILLE_H)]
    w = poser_perspective(art, quad)
    masque = w[..., 3]
    out = ombre_contact(base, masque, 28, 46, 46, .75)
    out = ombre_contact(out, masque, 4, 7, 6, .55)
    col = w[..., :3]
    # relief de lumiere : degrade doux + reflet vinyle brillant en diagonale
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    lum = 1.0 - .20 * np.clip((xx * .5 + yy * .8) / T - .55, 0, 1) - .05 * np.clip(.5 - (xx * .6 - yy * .2) / T, 0, 1)
    bande = np.exp(-(((xx * .8 - yy * .6) - 520) / 220.0) ** 2) * .075
    col = np.clip(col * lum[..., None] + bande[..., None], 0, 1)
    out = composite(out, col, masque)
    return finition(out, .008, .22)



# ============================================================ 08 CARNET
def symbole_frappe(x, y, taille):
    """Frappe signature : (poteaux_svg, diagonale_svg) du symbole, geometrie du fichier officiel. Les poteaux sont gaufres a sec, la diagonale en feuille orange."""
    s = taille / 52.0
    poteaux = (f'<rect x="{x}" y="{y}" width="{10.4 * s:.3f}" height="{taille}"/><rect x="{x + 41.6 * s:.3f}" y="{y}" width="{10.4 * s:.3f}" height="{taille}"/>')
    diag = "".join(f'<rect x="{x + k * 10.4 * s:.3f}" y="{y + k * 10.4 * s:.3f}" width="{10.4 * s:.3f}" height="{10.4 * s:.3f}"/>' for k in (1, 2, 3))
    return poteaux, diag


CARNET = dict(
    num=8, slug="carnet", nom_fr="Carnet à couverture rigide noire", nom_en="Black hardcover notebook",
    desc_fr="Couverture rigide noire, grain fin. Le symbole en frappe signature : montants gaufrés à sec, diagonale en dorure orange. À l'intérieur, une grille de points sur papier crème, pour écrire comme pour dessiner.",
    desc_en="Black hardcover with a fine grain. The symbol in signature stamping: posts blind-embossed, diagonal in orange hot foil. Inside, a dot grid on cream paper, for writing or sketching.",
    materiau_fr="Couverture rigide en carton gainé de papier simili noir mat, format A5 (148 × 210 mm), papier crème de 100 g/m², cahiers cousus, élastique et signet noirs, poche arrière.",
    materiau_en="Hard board covered in matte black paper, A5 (148 × 210 mm), cream 100 gsm paper, sewn signatures, black elastic and ribbon, back pocket.",
    technique_fr="Couverture : gaufrage à sec (montants) + dorure à chaud feuille orange (diagonale), même matrice. Pages : impression offset 1 couleur, grille de points gris.",
    technique_en="Cover: blind embossing (posts) + orange hot-foil stamping (diagonal), single die. Pages: 1-colour offset, grey dot grid.",
    zones=["Couverture : symbole de 28 mm de haut, bord gauche à 18 mm, bas à 18 mm ; zone de protection de 5,6 mm.",
           "Pages : grille de points tous les 5 mm, points de Ø 0,35 mm, marge de 12 mm ; teinte gris #A8A8B6 à 60 %.",
           "Matrice unique de 28 × 28 mm : relief de 0,4 mm pour les montants, feuille seulement sur la diagonale."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "or_feuille", "creme", "gris"] if False else ["noir", "or_feuille", "creme"],
    notes_fr=["Les calques GAUFRAGE-SEC (montants) et FEUILLE-ORANGE (diagonale) donnent la matrice : un seul outil, deux effets ; la géométrie reste celle du symbole officiel.",
              "Variante à valider avec le fondateur : montants aussi en feuille (os nacré) pour un symbole complet en deux feuilles.",
              "Feuille orange vif mate-brillante ; demander un échantillon de feuille (pas un orange rouge ni un cuivre).",
              "Aucun texte ni numéro de page ; les pages sont seulement à points."],
    notes_en=["The GAUFRAGE-SEC (posts) and FEUILLE-ORANGE (diagonal) layers make up the die: one tool, two effects; geometry remains the official symbol.",
              "Variant to validate with the founder: posts also in foil (pearl bone) for a full two-foil symbol.",
              "Bright orange foil, semi-gloss; request a foil sample (not red-orange or copper).",
              "No text or page numbers; the pages are dots only."])


def gabarit_carnet():
    g = Gabarit(148 * 2 + 40, 210 + 20)
    # couverture avant (a droite) : couleur
    fx = 148 + 40
    g.add("SILHOUETTE", f'<rect x="{fx}" y="10" width="148" height="210" rx="4" fill="#16161C" stroke="#9A9AA6" stroke-width=".6"/>')
    sx, sy = fx + 18, 10 + 210 - 18 - 28
    p, d = symbole_frappe(sx, sy, 28)
    g.add("GAUFRAGE-SEC", f'<g fill="#3A3A44" stroke="{OS}" stroke-width=".25" stroke-dasharray="1 .8">{p}</g>')
    g.add("FEUILLE-ORANGE", f'<g fill="{ORANGE}">{d}</g>')
    g.rect("ZONE-IMPRESSION", sx - 5.6, sy - 5.6, 39.2, 39.2, C_IMPR, "3 1.5", sw=.4)
    g.cote_h(sx, sx + 28, sy - 9, "28 mm", 4)
    g.cote_v(fx + 8, sy, sy + 28, "28 mm", 4)
    g.note(fx, 4, "COUVERTURE AVANT (échelle 1:1)", 4)
    # page : grille de points
    g.add("SILHOUETTE", '<rect x="0" y="10" width="148" height="210" fill="#F3F2EC" stroke="#9A9AA6" stroke-width=".4"/>')
    pts = "".join(f'<circle cx="{x}" cy="{y}" r="0.175"/>' for x in range(12, 137, 5) for y in range(22, 209, 5))
    g.add("ART", f'<g fill="#A8A8B6">{pts}</g>')
    g.rect("SECURITE", 12, 22, 125, 185 - .0, C_SEC, "1.5 1.5", sw=.3)
    g.note(0, 4, "PAGE INTÉRIEURE : GRILLE DE POINTS 5 mm (1 couleur)", 4)
    g.cote_h(12, 137, 18, "125 mm", 4)
    return g


def frappe_signature(base, quad, taille_mm, ppm=16.0, nom="frappe"):
    """Applique la frappe signature (montants gaufres a sec + diagonale en feuille orange) dans le quad donne."""
    po, di = symbole_frappe(0, 0, taille_mm)
    a_po = raster_art(svg_doc(taille_mm, taille_mm, f'<g fill="#FFFFFF">{po}</g>'), ppm, nom + "_po")
    a_di = raster_art(svg_doc(taille_mm, taille_mm, f'<g fill="{ORANGE}">{di}</g>'), ppm, nom + "_di")
    w_po = poser_perspective(a_po, quad); w_di = poser_perspective(a_di, quad)
    out = gaufrage_sec(base, w_po, force=1.0)
    return feuille_chaud(out, w_di, relief=1.0)


def maquette_carnet():
    base = charger_photo("carnet")
    k = 1.5625
    x0, y0, s = 545, 1128, 138
    quad = [(x0 * k, y0 * k), ((x0 + s) * k, y0 * k), ((x0 + s) * k, (y0 + s) * k), (x0 * k, (y0 + s) * k)]
    out = frappe_signature(base, quad, 28.0, nom="carnet_fr")
    return {"": finition(out, .010, .2), "pages": maquette_carnet_pages()}


def maquette_carnet_pages():
    """Vue ouverte : grille de points 5 mm sur les deux pages (format de la photo : 128 x 210 mm par page)."""
    base = charger_photo("carnet_ouvert")
    k = 1.5625
    pts = "".join(f'<circle cx="{x}" cy="{y}" r="0.2"/>' for x in range(9, 128, 5) for y in range(12, 205, 5))
    art = raster_art(svg_doc(128, 210, f'<g fill="#686874">{pts}</g>'), 12.0, "carnet_points")
    out = base
    for (x0, x1) in ((217, 744), (794, 1320)):
        quad = [(x0 * k, 313 * k), (x1 * k, 313 * k), (x1 * k, 1184 * k), (x0 * k, 1184 * k)]
        w = poser_perspective(art, quad)
        lum = np.clip(lum_clair(out, sigma=30), .55, 1.0)
        out = encre(out, w, lum=lum, densite=.9, souplesse=.9)
    return finition(out, .009, .18)


# ============================================================ 09 STYLO
STYLO = dict(
    num=9, slug="stylo", nom_fr="Stylo à bille gravé", nom_en="Engraved ballpoint pen",
    desc_fr="Métal anodisé graphite mat, mine noire. Le logo gravé au laser le long du fût, en clair sur le métal sombre : un objet qu'on prête et qui revient rarement.",
    desc_en="Matte graphite anodised metal, black ink. The logo laser-engraved along the barrel, light on the dark metal: an object you lend and rarely get back.",
    materiau_fr="Aluminium anodisé graphite mat (ou noir mat), mécanisme à poussoir, clip droit, mine noire à bille de 1,0 mm (recharge standard) ; longueur 140 mm, Ø 10 mm.",
    materiau_en="Matte graphite (or matte black) anodised aluminium, click mechanism, straight clip, 1.0 mm black ballpoint refill (standard); length 140 mm, Ø 10 mm.",
    technique_fr="Gravure laser (ablation de l'anodisation, marque argentée mate), une couleur ; logo complet monochrome (version blanche, tracé inchangé).",
    technique_en="Laser engraving (anodising ablation, matte silver mark), single colour; monochrome full logo (white version, outline unchanged).",
    zones=["Zone de gravure : 50 × 7 mm sur le fût, côté opposé au clip, centrée à 80 mm de la pointe.", "Logo complet : 34 mm de large (minimum 18 mm), hauteur d'environ 6,2 mm.",
           "Une seule face gravée."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os"],
    notes_fr=["Le logo complet est le fichier monochrome officiel : « AI » ne prend pas l'orange en gravure.", "Prévoir un contrôle de lisibilité à 1:1 : le hauteur du « N » pixel (6 mm) doit garder ses angles droits."],
    notes_en=["The full logo is the official monochrome file: “AI” does not take orange in engraving.", "Check legibility at 1:1: the 6 mm pixel “N” must keep its square corners."])


def gabarit_stylo():
    g = Gabarit(150, 26)
    g.add("SILHOUETTE", '<rect x="2" y="8" width="136" height="10" rx="5" fill="#16161C" stroke="#9A9AA6" stroke-width=".4"/><rect x="110" y="3" width="30" height="3" rx="1.5" fill="#2A2A33" stroke="#9A9AA6" stroke-width=".3"/>')
    lg, h = logo_complet(35, 13 - 3.1, 34, "blanc")
    g.add("ART", lg)
    g.rect("ZONE-IMPRESSION", 30, 9, 50, 8, C_IMPR, "3 1.5", sw=.3)
    g.cote_h(35, 69, 4, "34 mm", 3)
    g.note(0, -4, "FÛT (vue de côté, 1:1) · gravure laser, une couleur", 3.4)
    return g


def maquette_stylo():
    base = charger_photo("stylo")
    k = 1.5625
    dy = 140
    base = np.concatenate([base[dy:], np.repeat(base[-1:], dy, 0)], 0)     # recadrage : le stylo remonte au centre
    lg, lh = logo_complet(0, 0, 34, "blanc")
    art = raster_art(svg_doc(34, lh, lg), 20.0, "stylo_art")
    art_t = cv2.transpose(art)
    wt = poser_cylindre(art_t, lh, 34, 850 * k - dy, 560 * k, 50 * k, 5.35)
    w = cv2.transpose(wt)
    out = gravure(base, w, clair=.80, profondeur=.8)
    M = cv2.getRotationMatrix2D((1200, 1190), 17, 1.1)          # composition en diagonale
    out = cv2.warpAffine(out, M, (T, T), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return finition(out, .009, .22)


OBJETS = [(AUTOCOLLANTS, gabarit_autocollants, lambda: {"planche": maquette_planche("fr")}, lambda: gabarit_autocollants("en")), (CARNET, gabarit_carnet, maquette_carnet), (STYLO, gabarit_stylo, maquette_stylo)]
