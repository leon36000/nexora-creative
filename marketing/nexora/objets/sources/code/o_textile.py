"""Textile : t-shirt, chandail a capuchon, casquette, tuque, sac fourre-tout, pochette pour portable."""
from fab import *
from mock import *


def silhouette_tee(cx, y0, dos=False, ech=1.0):
    """Silhouette de reference d'un t-shirt taille M (schema, non imprime)."""
    s = ech
    dip = 28 if dos else 70
    p = lambda dx, dy: (cx + dx * s, y0 + dy * s)
    pts_r = [p(95, 0), p(238, 32), p(352, 168), p(305, 205), p(262, 176), p(262, 720)]
    pts_l = [(2 * cx - x, y) for x, y in pts_r]
    d = f"M{pts_l[0][0]:.1f} {pts_l[0][1]:.1f}"
    d += f" C{cx - 60 * s:.1f} {y0 + dip * s:.1f} {cx + 60 * s:.1f} {y0 + dip * s:.1f} {pts_r[0][0]:.1f} {pts_r[0][1]:.1f}"
    for x, y in pts_r[1:]:
        d += f" L{x:.1f} {y:.1f}"
    for x, y in reversed(pts_l[1:]):
        d += f" L{x:.1f} {y:.1f}"
    return d + " Z"


# ============================================================ 01 T-SHIRT
TEE = dict(
    num=1, slug="tshirt", nom_fr="T-shirt noir, braise au dos", nom_en="Black T-shirt, ember mosaic on the back",
    desc_fr="Coton épais, noir profond. Dans le dos, le N se reconstitue en pixels de braise qui montent et se dissolvent ; au cœur, le symbole, tout petit. Un vêtement qu'on met et qu'on photographie.",
    desc_en="Heavy cotton in deep black. On the back, the N reassembles itself in ember pixels that rise and dissolve; over the heart, the symbol, very small. A shirt you wear, and photograph.",
    materiau_fr="Coton peigné épais (environ 220 g/m²), noir teint masse, coupe unisexe, étiquette imprimée sans marque tierce.",
    materiau_en="Heavy combed cotton (about 220 gsm), solution-dyed black, unisex cut, printed neck label with no third-party branding.",
    technique_fr="Dos : impression numérique directe (DTG) ou transfert sérigraphique numérique. Cœur : sérigraphie 2 couleurs ou broderie.",
    technique_en="Back: direct-to-garment (DTG) or digital screen-print transfer. Heart: 2-colour screen print or embroidery.",
    zones=["Dos : zone d'impression 300 × 350 mm, centrée, haut à 80 mm sous la couture d'encolure (taille de référence M).",
           "Cœur : symbole de 40 mm, côté gauche, centre à 105 mm de l'axe, haut à 125 mm sous la couture d'épaule.",
           "Le gabarit à l'échelle 1:1 montre une silhouette de référence (schéma non imprimé)."],
    moq_fr="Environ 50 pièces par couleur de vêtement (indicatif, à confirmer).",
    moq_en="About 50 pieces per garment colour (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange", "b0", "b1", "b2", "b4", "b5"],
    notes_fr=["Dos : 6 teintes de braise ; en DTG prévoir une sous-couche blanche sélective sous toutes les teintes sur coton noir.",
              "Les pixels isolés mesurent environ 7 mm : tolérance de repérage inutile en DTG, à vérifier en sérigraphie (déconseillée à 6 écrans).",
              "Cœur : symbole officiel « sombre » (os + orange signal) sans modification ; zone de protection de 0,2 × la hauteur.",
              "Étiquette d'encolure : symbole seul, imprimé en os. Aucune date, aucun chiffre, aucune mention de provenance non vérifiée.",
              "Fournir un bon à tirer (BAT) photographié sur vêtement avant la série."],
    notes_en=["Back: 6 ember tones; for DTG add a selective white underbase under every tone on black cotton.",
              "Isolated pixels are about 7 mm: registration tolerance is a non-issue in DTG, check carefully with screen printing (6 screens not recommended).",
              "Heart: official dark-background symbol (bone + signal orange), unmodified; clear space of 0.2 × its height.",
              "Neck label: symbol only, printed in bone. No date, number, or unverified origin claim.",
              "Supply a photographed pre-production sample (BAT) before the run."])


def gabarit_tee():
    g = Gabarit(1500, 840)
    for i, dos in enumerate((False, True)):
        cx = 360 + i * 770
        g.add("SILHOUETTE", f'<path d="{silhouette_tee(cx, 40, dos)}" fill="#16161C" stroke="#9A9AA6" stroke-width="0.6"/>')
        g.note(cx, 790, "DOS" if dos else "FACE", 8, ancrage="middle")
    # dos : zone 300 x 350, mosaique N 300 x 300
    cx = 360 + 770
    g.rect("ZONE-IMPRESSION", cx - 150, 40 + 80, 300, 350, C_IMPR, "4 2", sw=.6)
    g.add("ART", svg_n_mosaique(cx - 150, 40 + 80, 300, seed=1))
    g.cote_h(cx - 150, cx + 150, 40 + 80 - 10, "300 mm", 6)
    g.cote_v(cx - 175, 40 + 80, 40 + 80 + 350, "350 mm", 6)
    g.cote_v(cx + 200, 40, 40 + 80, "80 mm", 5)
    # coeur : symbole 40 mm
    cxf = 360
    sx = cxf + 105 - 20
    g.rect("ZONE-IMPRESSION", sx - 6, 40 + 125 - 6, 52, 52, C_IMPR, "3 1.5", sw=.5)
    g.add("ART", symbole(sx, 40 + 125, 40, "sombre"))
    g.rect("SECURITE", sx - 8, 40 + 125 - 8, 56, 56, C_SEC, "1.5 1.5", sw=.4)
    g.cote_h(sx, sx + 40, 40 + 125 - 14, "40 mm", 5)
    g.cote_v(cxf + 150, 40, 40 + 125, "125 mm", 5)
    g.ligne("REPERES", cxf, 20, cxf, 780, C_REP, .25, "6 3")
    g.ligne("REPERES", cx, 20, cx, 780, C_REP, .25, "6 3")
    g.note(0, -8, "ZONE-IMPRESSION = cyan · SÉCURITÉ = vert · ART = couleurs de marque · silhouette = référence taille M, non imprimée", 4)
    return g


def maquette_tee(dest):
    base = charger_photo("tee_dos")
    return base  # complété après lecture de la photo


def maquette_tee():
    base = charger_photo("tee_dos")
    art = raster_art(svg_doc(300, 300, svg_n_mosaique(0, 0, 300, seed=1)), 4, "tee_art")
    x0, y0, s = 845, 531, 731
    w = poser_perspective(art, [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)])
    out = encre(base, w, texture=1.0)
    return finition(out)


def maquette_tee_face():
    base = charger_photo("tee_face")
    k = 1.5625
    art = raster_art(svg_doc(40, 40, symbole(0, 0, 40, "sombre")), 20.0, "tee_coeur")
    cx, cy, s = 935, 482, 64
    w = poser_perspective(art, [((cx - s / 2) * k, (cy - s / 2) * k), ((cx + s / 2) * k, (cy - s / 2) * k), ((cx + s / 2) * k, (cy + s / 2) * k), ((cx - s / 2) * k, (cy + s / 2) * k)])
    out = encre(base, w, texture=1.0, tissage=1.0, densite=.96)
    return finition(out, .009, .2)



# ============================================================ 02 CHANDAIL A CAPUCHON
HOODIE = dict(
    num=2, slug="chandail-capuchon", nom_fr="Chandail à capuchon noir, N pixel brodé", nom_en="Black hoodie, embroidered pixel N",
    desc_fr="Molleton lourd, noir profond. Un N pixel géant brodé sur la poitrine, en fil os et orange ; un seul carré orange brodé sur la manche, comme un pixel allumé dans la nuit.",
    desc_en="Heavyweight fleece in deep black. A giant pixel N embroidered across the chest in bone and orange thread; a single orange square on the sleeve, like a pixel lit in the dark.",
    materiau_fr="Molleton gratté 380 à 420 g/m² environ, coton et polyester, noir teint masse, capuchon doublé, poche kangourou, cordons noirs mats sans marque.",
    materiau_en="Brushed fleece, about 380 to 420 gsm, cotton/polyester blend, solution-dyed black, lined hood, kangaroo pocket, matte black drawcords without branding.",
    technique_fr="Broderie machine satin et remplissage sur support de découpe (stabilisateur), fil polyester brillant : os (chaud) et orange vif.",
    technique_en="Machine embroidery, satin and fill stitches on cut-away stabiliser, glossy polyester thread: bone (warm) and bright orange.",
    zones=["Poitrine : symbole de 170 mm de large (170 × 170 mm), centré, haut à 230 mm sous la couture d'encolure (sous l'extrémité des cordons), au-dessus de la poche kangourou.",
           "Manche gauche (côté droit de l'image de face) : carré orange de 40 × 40 mm, au centre de la manche, à 270 mm sous la couture d'épaule, aligné sur l'axe de la manche.",
           "La zone de protection du symbole est de 0,2 × sa hauteur : poche kangourou à 70 mm au moins sous la broderie."],
    moq_fr="Environ 50 pièces (indicatif, à confirmer) ; frais de numérisation (digitizing) uniques.",
    moq_en="About 50 pieces (indicative, to be confirmed); one-off digitising fee.",
    couleurs=["noir", "os", "orange"],
    notes_fr=["Fichier de broderie : demander au brodeur de numériser depuis le SVG (carrés pleins de 34 mm de côté, sans lissage) ; les angles restent droits.",
              "Fil os : un blanc chaud (pas blanc optique) ; fil orange : valider sur échantillon, le rouge-orangé vire en broderie.",
              "Sens des points : montants verticaux, carrés orange en diagonale à 45° ; densité satin moyenne pour éviter le froncement du molleton.",
              "Fournir une épreuve brodée (stitch-out) avant la série."],
    notes_en=["Embroidery file: ask the embroiderer to digitise from the SVG (solid squares of 34 mm, no smoothing); corners stay square.",
              "Bone thread: a warm white (not optical white); orange thread: validate on sample, red-oranges shift in embroidery.",
              "Stitch direction: vertical posts, orange squares at 45°; medium satin density to avoid fleece puckering.",
              "Supply a stitch-out sample before the run."])


def silhouette_hoodie(cx, y0):
    """Silhouette de reference (schema) : corps, manches pendantes le long du corps, capuchon."""
    P = lambda x, y: f"{cx + x:.1f} {y0 + y:.1f}"
    droite = [(95, 0), (240, 30), (330, 120), (395, 330), (408, 690), (300, 712), (278, 330), (262, 200)]
    corps_d = [(262, 730)]
    pts = [(-95, 0)] + [(95, 0)]
    d = f"M{P(-95, 0)} C{P(-60, 40)} {P(60, 40)} {P(95, 0)}"
    for (x, y) in droite[1:]:
        d += f" L{P(x, y)}"
    d += f" L{P(262, 730)} L{P(-262, 730)}"
    for (x, y) in reversed(droite[1:]):
        d += f" L{P(-x, y)}"
    d += " Z"
    capuche = f"M{P(-135, 6)} C{P(-150, -90)} {P(150, -90)} {P(135, 6)} C{P(110, 60)} {P(-110, 60)} {P(-135, 6)} Z"
    return d, capuche


def gabarit_hoodie():
    g = Gabarit(900, 860)
    cx = 450
    d, cap = silhouette_hoodie(cx, 90)
    g.add("SILHOUETTE", f'<path d="{cap}" fill="#1D1D24" stroke="#9A9AA6" stroke-width=".6"/><path d="{d}" fill="#16161C" stroke="#9A9AA6" stroke-width=".6"/>')
    # poitrine : 240 mm
    g.rect("ZONE-IMPRESSION", cx - 92, 90 + 230 - 7, 184, 184, C_IMPR, "4 2", sw=.6)
    g.add("ART", symbole(cx - 85, 90 + 230, 170, "sombre"))
    g.rect("SECURITE", cx - 102, 90 + 230 - 17, 204, 204, C_SEC, "2 2", sw=.4)
    g.cote_h(cx - 85, cx + 85, 90 + 230 - 24, "170 mm", 6)
    g.cote_v(cx - 115, 90 + 230, 90 + 400, "170 mm", 6)
    g.cote_v(cx + 130, 90, 90 + 230, "230 mm", 5)
    # manche : carre orange 40 mm, manche a droite de l'image
    mx, my = cx + 340, 90 + 270
    g.rect("ZONE-IMPRESSION", mx - 25, my - 25, 50, 50, C_IMPR, "3 1.5", sw=.5)
    g.add("ART", f'<rect x="{mx - 20}" y="{my - 20}" width="40" height="40" fill="{ORANGE}"/>')
    g.cote_h(mx - 20, mx + 20, my - 32, "40 mm", 5)
    g.ligne("REPERES", cx, 20, cx, 840, C_REP, .25, "6 3")
    g.note(0, -2, "SILHOUETTE = référence taille M (schéma), non imprimée · calque ART = broderie", 4)
    return g


def _quad_rot(c, demi, deg):
    th = np.deg2rad(deg); R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    return [tuple(np.array(c) + R @ np.array(p)) for p in ((-demi, -demi), (demi, -demi), (demi, demi), (-demi, demi))]


def maquette_hoodie():
    base = charger_photo("hoodie")
    k = 1.5625
    art = raster_art(svg_doc(170, 170, symbole(0, 0, 170, "sombre")), 8.0, "hoodie_art")
    w = poser_perspective(art, [(672 * k, 712 * k), (869 * k, 712 * k), (869 * k, 909 * k), (672 * k, 909 * k)])
    out = broderie(base, w, pitch=5.2, angle_deg=90, relief=1.0)
    art2 = raster_art(svg_doc(40, 40, f'<rect width="40" height="40" fill="{ORANGE}"/>'), 14.0, "hoodie_carre")
    w2 = poser_perspective(art2, _quad_rot((1186 * k, 735 * k), 23.2 * k, -13))
    out = broderie(out, w2, pitch=4.4, angle_deg=45, relief=1.0)
    return finition(out, .010, .2)


# ============================================================ 03 CASQUETTE
CASQUETTE = dict(
    num=3, slug="casquette", nom_fr="Casquette brodée", nom_en="Embroidered cap",
    desc_fr="Six panneaux, noir mat, visière courbe. Le symbole brodé au centre, en fil os et orange : rien d'autre. Elle s'ajuste, se déforme un peu, se porte.",
    desc_en="Six panels, matte black, curved brim. The symbol embroidered at the centre in bone and orange thread: nothing else. It adjusts, softens with wear, gets worn.",
    materiau_fr="Sergé de coton brossé noir, six panneaux non structurés ou semi-structurés, œillets noirs, sangle réglable à boucle métallique noire mate.",
    materiau_en="Black brushed cotton twill, six panels (unstructured or semi-structured), black eyelets, adjustable strap with matte black metal buckle.",
    technique_fr="Broderie machine à plat sur le panneau avant avant assemblage, fil polyester brillant os et orange.",
    technique_en="Flat machine embroidery on the front panel before assembly, glossy polyester thread in bone and orange.",
    zones=["Panneau avant : zone de broderie 90 × 55 mm, centrée, bas de la broderie à 18 mm au-dessus de la couture de la visière.",
           "Symbole : 44 mm de hauteur (zone de protection de 8,8 mm).",
           "Sangle arrière : sans marquage (option : carré orange brodé de 12 mm)."],
    moq_fr="Environ 50 pièces (indicatif, à confirmer).", moq_en="About 50 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange"],
    notes_fr=["Sur casquette, ne pas descendre sous 3 mm de largeur de montant : à 44 mm, chaque montant fait 8,8 mm (satin).",
              "Prévoir un support de broderie rigide pour garder les angles droits sur le panneau bombé.",
              "Aucun texte sur la casquette : le symbole parle seul."],
    notes_en=["On a cap, never go below 3 mm stroke width: at 44 mm each post is 8.8 mm (satin).",
              "Use a firm backing so the corners stay square on the domed panel.",
              "No text on the cap: the symbol speaks on its own."])


def gabarit_casquette():
    g = Gabarit(260, 150)
    cx = 130
    g.add("SILHOUETTE", f'<path d="M{cx - 100} 30 Q{cx} -5 {cx + 100} 30 L{cx + 108} 100 L{cx - 108} 100 Z" fill="#16161C" stroke="#9A9AA6" stroke-width=".6"/>'
                        f'<path d="M{cx - 125} 100 Q{cx} 135 {cx + 125} 100 L{cx + 108} 100 L{cx - 108} 100 Z" fill="#1D1D24" stroke="#9A9AA6" stroke-width=".6"/>')
    g.rect("ZONE-IMPRESSION", cx - 45, 100 - 18 - 55, 90, 55, C_IMPR, "4 2", sw=.6)
    g.add("ART", symbole(cx - 22, 100 - 18 - 50, 44, "sombre"))
    g.rect("SECURITE", cx - 31, 100 - 18 - 59, 62, 62, C_SEC, "1.5 1.5", sw=.4)
    g.cote_h(cx - 22, cx + 22, 100 - 18 - 64, "44 mm", 4)
    g.cote_v(cx + 55, 100 - 18 - 55, 100 - 18, "55 mm", 4)
    g.ligne("REPERES", cx, 0, cx, 140, C_REP, .25, "6 3")
    g.note(0, -4, "PANNEAU AVANT (schéma) · broderie à plat avant assemblage", 4)
    return g


def maquette_casquette():
    base = charger_photo("casquette")
    k = 1.5625
    art = raster_art(svg_doc(44, 44, symbole(0, 0, 44, "sombre")), 14.0, "casquette_art")
    cx, cy, s = 770, 705, 262
    w = poser_perspective(art, [((cx - s / 2) * k, (cy - s / 2) * k), ((cx + s / 2) * k, (cy - s / 2) * k), ((cx + s / 2) * k, (cy + s / 2) * k), ((cx - s / 2) * k, (cy + s / 2) * k)])
    out = broderie(base, w, pitch=4.2, angle_deg=90, relief=1.0, ombre=.55)
    return finition(out, .010, .2)


# ============================================================ 04 TUQUE
TUQUE = dict(
    num=4, slug="tuque", nom_fr="Tuque noire, patch symbole", nom_en="Black beanie (tuque), symbol patch",
    desc_fr="Une tuque comme on les porte ici : bonnet côtelé noir à rebord large. Un patch tissé écru porte le symbole, cousu au centre du rebord.",
    desc_en="A tuque as worn here: ribbed black knit with a wide cuff. A woven ecru patch carries the symbol, sewn at the centre of the cuff.",
    materiau_fr="Maille côtelée acrylique et laine, noir, rebord double ; patch tissé 52 × 52 mm, fond écru, fil noir et orange, bord surjeté.",
    materiau_en="Ribbed acrylic and wool knit, black, double cuff; 52 × 52 mm woven patch, ecru ground, black and orange thread, merrowed edge.",
    technique_fr="Patch tissé haute densité (symbole version claire : encre #121218 et orange du logo clair), cousu à la machine, rebord couvert.",
    technique_en="High-density woven patch (light-background symbol: #121218 ink and the light-version orange), machine stitched through the cuff.",
    zones=["Patch : 52 × 52 mm, coins à 3 mm, centré sur le rebord (à 12 mm du bord inférieur).",
           "Symbole : 32 mm dans le patch (zone de protection de 6,4 mm respectée).",
           "Rebord : 90 mm de haut environ."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "creme", "orange_clair", "surface"],
    notes_fr=["Le patch est écru pour respecter la règle : le symbole en couleur ne se pose que sur un fond clair.",
              "Demander un tissage 2 couleurs avec arêtes nettes ; le patch ne doit pas se froncer sur la maille.",
              "Aucune étiquette de marque tierce : étiquette tissée intérieure avec le symbole seul."],
    notes_en=["The patch is ecru to follow the rule: the colour symbol only sits on a light ground.",
              "Ask for a 2-colour weave with crisp edges; the patch must not pucker on the knit.",
              "No third-party label: inside woven label with the symbol alone."])


def gabarit_tuque():
    g = Gabarit(260, 230)
    cx = 130
    g.add("SILHOUETTE", f'<path d="M{cx - 95} 120 C{cx - 105} 20 {cx + 105} 20 {cx + 95} 120 Z" fill="#16161C" stroke="#9A9AA6" stroke-width=".6"/>'
                        f'<rect x="{cx - 98}" y="120" width="196" height="90" rx="6" fill="#1D1D24" stroke="#9A9AA6" stroke-width=".6"/>')
    px, py = cx - 26, 120 + 90 - 12 - 52
    g.add("ART", f'<rect x="{px}" y="{py}" width="52" height="52" rx="3" fill="{CREME}"/>' + symbole(px + 10, py + 10, 32, "clair"))
    g.rect("COUPE", px, py, 52, 52, C_COUPE, rx=3, sw=.4)
    g.rect("SECURITE", px + 3.6, py + 3.6, 44.8, 44.8, C_SEC, "1.5 1.5", sw=.3)
    g.cote_h(px, px + 52, py - 6, "52 mm", 4)
    g.cote_v(px - 8, py, py + 52, "52 mm", 4)
    g.cote_v(cx + 108, 120, 210, "90 mm", 4)
    g.ligne("REPERES", cx, 0, cx, 225, C_REP, .25, "6 3")
    g.note(0, -4, "CALQUE COUPE = contour du patch (surjet) · silhouette de la tuque en schéma", 4)
    return g


def art_patch():
    return (f'<rect width="52" height="52" rx="3" fill="{CREME}"/>'
            f'<rect x="1.9" y="1.9" width="48.2" height="48.2" rx="1.6" fill="none" stroke="#DAD8CC" stroke-width=".5"/>' + symbole(10, 10, 32, "clair"))


def maquette_tuque():
    base = charger_photo("tuque")
    k = 1.5625
    art = raster_art(svg_doc(52, 52, art_patch()), 12.0, "tuque_art")
    w = poser_cylindre(art, 52, 52, 760 * k, 990 * k, 462 * k, 462 / 4.6)
    lum = .97 * np.clip(carte_lumiere(base, sigma_large=140, force_fin=.2, force_large=.6), .7, 1.15)
    out = broderie(base, w, pitch=2.7, angle_deg=0, relief=.45, ombre=.6, lum=lum, seglen=2.7 * 4)
    return finition(out, .010, .2)


# ============================================================ 07 SAC FOURRE-TOUT
TOTE = dict(
    num=7, slug="sac-fourre-tout", nom_fr="Sac fourre-tout en toile écrue, grande mosaïque", nom_en="Ecru canvas tote bag, large mosaic",
    desc_fr="Toile de coton épaisse, couleur d'avoine. Une grande mosaïque de braise monte du fond du sac et se dissout en pixels ; au sommet, tout petit, le symbole. Le sac qu'on porte à l'épaule en ville.",
    desc_en="Heavy oat-coloured cotton canvas. A large ember mosaic rises from the bottom of the bag and dissolves into pixels; at the top, very small, the symbol. The bag you carry over the shoulder in the city.",
    materiau_fr="Toile de coton écrue d'environ 280 g/m², 380 × 420 mm, anses plates de 700 mm cousues en carré renforcé, fond sans soufflet.",
    materiau_en="Ecru cotton canvas of about 280 gsm, 380 × 420 mm, 700 mm flat handles with reinforced box-stitching, flat bottom without gusset.",
    technique_fr="Sérigraphie à l'eau 6 couleurs (une par teinte de braise) ou impression numérique directe ; symbole en une couleur (noir profond et orange en 2 passes).",
    technique_en="Water-based screen print, 6 colours (one per ember tone) or direct digital print; symbol in 2 passes (deep black and orange).",
    zones=["Mosaïque : 300 × 300 mm, bas du motif à 30 mm du bas du sac, centrée.",
           "Symbole (version claire) : 24 mm, centre à 52 mm du haut, dans la zone claire ; aucune case de mosaïque à moins de 5 mm.",
           "Anses : 700 mm de longueur, 25 mm de largeur, fixées à 100 mm de chaque côté."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["creme", "noir", "orange_clair", "b0", "b1", "b2", "b3", "b4", "b5"],
    notes_fr=["Sur toile écrue, l'orange du symbole est #F04A10 (version logo clair) et le noir #121218 ; la mosaïque garde la rampe braise sans changement.",
              "Pour la sérigraphie, les cases ont 8,3 mm : tracer à plat, sans demi-teinte, un écran par teinte ; prévoir un trapping de 0,1 mm entre cases (déjà un jeu de 7 %).",
              "Le sac ne porte ni texte ni date. Étiquette cousue intérieure : symbole seul."],
    notes_en=["On ecru canvas, the symbol orange is #F04A10 (light logo version) and the black #121218; the mosaic keeps the ember ramp unchanged.",
              "For screen printing, cells are 8.3 mm: flat artwork, no halftones, one screen per tone; the 7% gap between cells is already built in.",
              "The bag carries no text or date. Inside sewn label: symbol only."])


def art_tote(x=0, y=0):
    sx, sy = 190 - 12, 52 - 12
    mos = svg_mosaic(x + 40, y + 90, 300, 36, 36, seed=9, toward="bottom", fade=0.8)
    return mos + symbole(x + 190 - 12, y + 52 - 12, 24, "clair")


def gabarit_tote():
    g = Gabarit(760, 520)
    cx = 380
    g.add("SILHOUETTE", f'<rect x="{cx - 190}" y="80" width="380" height="420" fill="#ECE9DD" stroke="#9A9AA6" stroke-width=".6"/>'
                        f'<path d="M{cx - 120} 80 L{cx - 120} 0 L{cx - 95} 0 L{cx - 95} 80 M{cx + 95} 80 L{cx + 95} 0 L{cx + 120} 0 L{cx + 120} 80" fill="none" stroke="#9A9AA6" stroke-width=".6"/>')
    g.rect("ZONE-IMPRESSION", cx - 150, 80 + 90 - 10, 300, 320, C_IMPR, "4 2", sw=.6)
    g.add("ART", art_tote(cx - 190, 80))
    g.rect("SECURITE", cx - 12 - 5, 80 + 52 - 12 - 5, 34, 34, C_SEC, "1.5 1.5", sw=.3)
    g.cote_h(cx - 150, cx + 150, 80 + 90 - 18, "300 mm", 6)
    g.cote_v(cx + 205, 80, 80 + 500 - 80, "420 mm", 6)
    g.cote_h(cx - 190, cx + 190, 80 + 430, "380 mm", 6)
    g.ligne("REPERES", cx, 0, cx, 515, C_REP, .25, "6 3")
    return g


def maquette_tote():
    base = charger_photo("tote")
    art = raster_art(svg_doc(380, 420, art_tote(0, 0)), 5.0, "tote_art")
    w = poser_perspective(art, [(687, 944), (1766, 944), (1766, 2168), (687, 2168)])
    lum = lum_clair(base) * carte_lumiere(base, sigma_large=1000, sigma_fin=4, force_fin=1.0, force_large=0)
    out = encre(base, w, lum=np.clip(lum, .5, 1.0), tissage=1.3, densite=.93, souplesse=.9)
    return finition(out, .008, .16)


# ============================================================ 15 POCHETTE POUR PORTABLE
POCHETTE = dict(
    num=15, slug="pochette-portable", nom_fr="Pochette pour portable", nom_en="Laptop sleeve",
    desc_fr="Néoprène noir mat, fermeture à glissière, un seul patch : le symbole, en relief, dans le coin du bas. Le portable y est chez lui.",
    desc_en="Matte black neoprene, zip closure, a single patch: the symbol, in relief, in the lower corner. The laptop feels at home.",
    materiau_fr="Néoprène noir de 5 mm, doublure feutre gris anthracite, glissière métal noir mat ; format 13 à 16 po, forme carrée arrondie : 350 × 340 mm extérieur.",
    materiau_en="5 mm black neoprene, charcoal felt lining, matte black metal zip; 13 to 16 in format, rounded-square shape: 350 × 340 mm outside.",
    technique_fr="Patch de silicone moulé à 2 couleurs (os + orange) thermocollé et cousu, ou impression thermique en relief.",
    technique_en="Moulded 2-colour silicone patch (bone + orange) heat-bonded and stitched, or embossed heat-transfer.",
    zones=["Patch : symbole de 34 mm, centre à 38 mm du bord droit et à 38 mm du bas (zone de protection de 6,8 mm).",
           "Dimensions extérieures : 350 × 340 mm, coins arrondis de 28 mm."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange"],
    notes_fr=["Le patch est le fichier officiel « sombre » ; hauteur du relief 0,8 mm, arêtes nettes (pas d'arrondi du moule : les carrés restent carrés).",
              "Glissière et tirette noires mates, sans marque."],
    notes_en=["The patch is the official dark-background file; 0.8 mm relief, crisp edges (no mould rounding: squares stay square).",
              "Matte black zip and pull, unbranded."])


def gabarit_pochette():
    g = Gabarit(350, 340)
    g.add("SILHOUETTE", f'<rect width="350" height="340" rx="28" fill="#16161C" stroke="#9A9AA6" stroke-width=".6"/><line x1="12" y1="14" x2="338" y2="14" stroke="#3A3A44" stroke-width="2"/>')
    cx, cy = 350 - 38, 340 - 38
    g.rect("ZONE-IMPRESSION", cx - 24, cy - 24, 48, 48, C_IMPR, "3 1.5", sw=.5)
    g.add("ART", symbole(cx - 17, cy - 17, 34, "sombre"))
    g.rect("SECURITE", cx - 23.8, cy - 23.8, 47.6, 47.6, C_SEC, "1.5 1.5", sw=.3)
    g.cote_h(cx - 17, cx + 17, cy - 30, "34 mm", 4)
    g.cote_v(350 + 8, cy, 340, "38 mm", 4)
    g.cote_h(350 - 38, 350, 340 + 8, "38 mm", 4)
    g.note(0, -4, "VUE DE FACE · glissière en haut", 4)
    return g


def maquette_pochette():
    base = charger_photo("pochette")
    k = 1.5625
    art = raster_art(svg_doc(34, 34, symbole(0, 0, 34, "sombre")), 24.0, "pochette_art")
    cx, cy, s = 1171, 1176, 102
    quad = [((cx - s / 2) * k, (cy - s / 2) * k), ((cx + s / 2) * k, (cy - s / 2) * k), ((cx + s / 2) * k, (cy + s / 2) * k), ((cx - s / 2) * k, (cy + s / 2) * k)]
    w = poser_perspective(art, quad)
    out = ombre_contact(base, w[..., 3], 4, 7, 5, .65)             # patch en relief : ombre portee sur le neoprene
    lum = comprime(carte_lumiere(base, sigma_large=200), .5, .8, 1.1)
    out = vernis_uv(out, w, lum=lum, brillance=.7, plafond=.96)
    return finition(out, .010, .2)


OBJETS = [(TEE, gabarit_tee, lambda: {"": maquette_tee(), "face": maquette_tee_face()}), (HOODIE, gabarit_hoodie, maquette_hoodie), (CASQUETTE, gabarit_casquette, maquette_casquette),
          (TUQUE, gabarit_tuque, maquette_tuque), (TOTE, gabarit_tote, maquette_tote), (POCHETTE, gabarit_pochette, maquette_pochette)]
