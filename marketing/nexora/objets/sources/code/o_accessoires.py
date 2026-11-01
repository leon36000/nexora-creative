"""Accessoires : epinglettes en email dur (3 modeles), cle USB, porte-badge et cordon, tapis de bureau."""
from fab import *
from mock import *
from o_papeterie import fond_sombre

# ============================================================ 13 EPINGLETTES
NICKEL = "#1B1B21"          # nickel noir (metal)
MUR, BORD = 0.6, 0.9       # cloisons entre emaux, bord exterieur (mm)


def pins_def():
    """Trois modeles de 26 mm : regions d'email (x, y, w, h, couleur) en mm, origine en haut a gauche d'un carre de 26 mm."""
    s = 26 / 52.0
    ox = oy = 0
    N = [(0, 0, 10.4, 52, OS), (41.6, 0, 10.4, 52, OS), (10.4, 10.4, 10.4, 10.4, ORANGE), (20.8, 20.8, 10.4, 10.4, ORANGE), (31.2, 31.2, 10.4, 10.4, ORANGE)]
    pN = [(x * s, y * s, w * s, h * s, c) for x, y, w, h, c in N]
    # carre orange 20 mm
    pC = [(0, 0, 20, 20, ORANGE)]
    # mosaique 5 x 5 de 4,8 mm
    cells = mosaic_cells(5, 5, 4, "center", 0.0, 6)
    pM = []
    for c, r, t in cells:
        pM.append((c * 4.8, r * 4.8, 4.8, 4.8, BRAISE[t]))
    return [("N", "Le N pixel", pN), ("C", "Le carré orange", pC), ("M", "La tuile braise", pM)]


EPINGLETTES = dict(
    num=13, slug="epinglettes", nom_fr="Épinglettes en émail dur (trois modèles)", nom_en="Hard enamel pins (three designs)",
    desc_fr="Trois pièces qui se collectionnent : le N pixel, le carré orange, la tuile de mosaïque braise. Métal noir, émail poli, un poids qui rassure dans la main.",
    desc_en="Three collectible pieces: the pixel N, the orange square, the ember mosaic tile. Black metal, polished enamel, a reassuring weight in the hand.",
    materiau_fr="Laiton ou zinc estampé, placage nickel noir, émail dur poli (surface au niveau du métal), tige avec fermoir papillon en métal noir ; carte de présentation noire.",
    materiau_en="Die-struck brass or zinc, black nickel plating, polished hard enamel (flush with the metal), post with black metal butterfly clutch; black backing card.",
    technique_fr="Estampage, remplissage d'émail dur par couleur, cuisson et polissage, placage nickel noir ; pas de sérigraphie ni d'époxy.",
    technique_en="Die striking, hard enamel fill per colour, firing and polishing, black nickel plating; no printing or epoxy dome.",
    zones=["Hors tout, bord de métal compris : N pixel 27,4 mm (émail 26 mm) ; carré orange 21,4 mm (émail 20 mm) ; tuile braise 25,4 mm (5 × 5 cases de 4,8 mm).",
           "Cloisons de métal : 0,6 mm ; contour de métal : 0,9 mm ; épaisseur totale : environ 1,5 mm.",
           "Le N reproduit à l'identique la géométrie du symbole officiel (deux montants, trois carrés)."],
    moq_fr="Environ 100 pièces par modèle (indicatif, à confirmer).", moq_en="About 100 pieces per design (indicative, to be confirmed).",
    couleurs=["os", "orange", "b0", "b1", "b2", "b3", "b4", "b5"],
    notes_fr=["Le calque COUPE est le tracé d'estampage (contour extérieur) ; les cloisons séparent chaque couleur.",
              "Demander un cuivre/zinc « black nickel » (RAL approchant le noir 9005) et non un noir peint.",
              "Émail dur : prévoir un essai pour l'os (blanc cassé, jamais blanc pur) et pour l'écart entre #FF8A1F et #FF5A1F.",
              "Mettre un chiffre ou une date au dos est interdit tant que rien n'est validé : dos lisse avec symbole seul, en relief."],
    notes_en=["The COUPE layer is the strike outline (outer contour); the walls separate every colour.",
              "Ask for black nickel plating, not paint.",
              "Hard enamel: request a test for bone (off-white, never pure white) and for the gap between #FF8A1F and #FF5A1F.",
              "No number or date on the back: smooth back with the symbol alone, in relief."])


def gabarit_epinglettes():
    g = Gabarit(110, 56)
    x = 4
    for k, nom, regs in pins_def():
        W = max(x2 + w for x2, y, w, h, c in regs); H = max(y + h for x2, y, w, h, c in regs)
        oy = (40 - H) / 2 + 4
        for (rx, ry, w, h, c) in regs:
            g.add("ART", f'<rect x="{x + rx + MUR / 2:.3f}" y="{oy + ry + MUR / 2:.3f}" width="{w - MUR:.3f}" height="{h - MUR:.3f}" fill="{c}"/>')
        g.add("SILHOUETTE", f'<rect x="{x - BORD}" y="{oy - BORD}" width="{W + 2 * BORD}" height="{H + 2 * BORD}" fill="{NICKEL}"/>')
        g.rect("COUPE", x - BORD, oy - BORD, W + 2 * BORD, H + 2 * BORD, C_COUPE, sw=.25)
        g.cote_h(x - BORD, x + W + BORD, oy + H + BORD + 5, f"{W + 2 * BORD:.1f} mm", 3)
        g.note(x - BORD, 2, nom, 3.6)
        x += W + 2 * BORD + 14
    return g


def _ombre_pin(base, m, dx=10, dy=16):
    out = ombre_contact(base, m, dx, dy, 14, .75)
    return ombre_contact(out, m, 2, 4, 3, .6)


def rendre_pin(regs, ppm, rot_deg=0):
    """Rend une epinglette : retourne (couleur BGR float, masque, hauteur) sur une toile locale ; relief eclaire (haut-gauche)."""
    W = max(x + w for x, y, w, h, c in regs); H = max(y + h for x, y, w, h, c in regs)
    pad = 2.0
    pw, ph = int((W + 2 * BORD + 2 * pad) * ppm), int((H + 2 * BORD + 2 * pad) * ppm)
    ox, oy = pad + BORD, pad + BORD
    P = lambda v: int(round(v * ppm))
    outer = np.zeros((ph, pw), np.uint8)
    em = []
    for (x, y, w, h, c) in regs:
        cv2.rectangle(outer, (P(ox + x - BORD * .0), P(oy + y)), (P(ox + x + w) - 1, P(oy + y + h) - 1), 255, -1)
    k = P(BORD)
    outer = cv2.dilate(outer, cv2.getStructuringElement(cv2.MORPH_RECT, (2 * k + 1, 2 * k + 1)))
    hm = np.zeros((ph, pw), np.float32)
    hm[outer > 0] = 1.0
    colmap = np.zeros((ph, pw, 3), np.float32)
    emmask = np.zeros((ph, pw), np.float32)
    for (x, y, w, h, c) in regs:
        x0, y0 = P(ox + x + MUR / 2), P(oy + y + MUR / 2)
        x1, y1 = P(ox + x + w - MUR / 2), P(oy + y + h - MUR / 2)
        cv2.rectangle(emmask, (x0, y0), (x1 - 1, y1 - 1), 1.0, -1)
        cv2.rectangle(colmap, (x0, y0), (x1 - 1, y1 - 1), tuple(float(v) for v in bgr(c)), -1)
    hm = np.where(emmask > 0, .62, hm)
    mask = (outer > 0).astype(np.float32)
    hs = cv2.GaussianBlur(hm, (0, 0), ppm * .07)
    gx = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=3) / 8
    gx *= ppm * .6; gy *= ppm * .6
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Ld = np.array([-.45, -.6, .66], np.float32); Ld /= np.linalg.norm(Ld)
    diff = np.clip((n * Ld).sum(-1), 0, 1)
    Hh = Ld + np.array([0, 0, 1], np.float32); Hh /= np.linalg.norm(Hh)
    spec = np.clip((n * Hh).sum(-1), 0, 1) ** 28
    # emaux : leger bombe poli + reflet de fenetre doux
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    fen = np.exp(-(((xx * .8 + yy * .6) - pw * .55) / (pw * .22)) ** 2) * .16
    em3 = emmask[..., None]
    base_metal = np.array([bgr(NICKEL)] * 1, np.float32)[0] * (0.5 + 1.2 * diff[..., None]) + spec[..., None] * np.array([1.1, 1.1, 1.15], np.float32)
    base_em = colmap * (0.82 + .3 * diff[..., None]) + (fen[..., None] + spec[..., None] * .35) * em3
    col = np.where(em3 > 0, base_em, base_metal)
    col = np.clip(col, 0, 1)
    return col, mask, hm


def maquette_epinglettes():
    base = fond_cuir()
    defs = pins_def()
    ppm = 26.0
    pos = [(700, 880, -6), (1650, 800, 5), (1290, 1700, -3)]
    out = base
    for (k, nom, regs), (cx, cy, rot) in zip(defs, pos):
        col, mask, hm = rendre_pin(regs, ppm)
        h, w = mask.shape
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0)
        # canvas complet
        L = np.zeros((T, T, 3), np.float32); A = np.zeros((T, T), np.float32)
        M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
        L = cv2.warpAffine(col, M, (T, T), flags=cv2.INTER_CUBIC)
        A = cv2.warpAffine(mask, M, (T, T), flags=cv2.INTER_LINEAR)
        A = cv2.GaussianBlur(A, (0, 0), .7)
        out = _ombre_pin(out, A)
        out = composite(out, L, A)
        # reflets de bord arrondi
    out = finition(out, .009, .25)
    return out


def fond_cuir(taille=T, graine=5):
    """Fond de presentation : feutre / cuir noir grene, eclaire de haut a gauche."""
    yy, xx = np.mgrid[0:taille, 0:taille].astype(np.float32) / taille
    d = np.hypot(xx - .35, yy - .3)
    v = 0.105 - 0.075 * np.clip(d * 1.2, 0, 1)
    rng = np.random.default_rng(graine)
    g = cv2.GaussianBlur(rng.normal(0, 1, (taille, taille)).astype(np.float32), (0, 0), 1.6) * .010
    g2 = cv2.GaussianBlur(rng.normal(0, 1, (taille, taille)).astype(np.float32), (0, 0), 6) * .010
    im = np.stack([v * .98, v * .98, v * 1.03], -1) + (g + g2)[..., None]
    return np.clip(im, 0, 1).astype(np.float32)



# ============================================================ 10 CLE USB ET ETUI
USB = dict(
    num=10, slug="cle-usb", nom_fr="Clé USB et son étui", nom_en="USB drive and case",
    desc_fr="Une clé en métal gris anthracite brossé, symbole gravé ; dans un étui rigide noir qui s'ouvre comme un écrin (frappe signature sur le couvercle, voir le gabarit).",
    desc_en="A brushed anthracite metal drive with the symbol engraved; in a rigid black case that opens like a jewel box (signature stamp on the lid, see the template).",
    materiau_fr="Clé : aluminium anodisé gris anthracite brossé, USB-C, capuchon pivotant, capacité à confirmer avec le fournisseur ; étui : carton rigide noir mat, mousse noire, aimant.",
    materiau_en="Drive: brushed anthracite anodised aluminium, USB-C, swivel cover, capacity to be confirmed with the supplier; case: rigid black matte board, black foam, magnet.",
    technique_fr="Clé : gravure laser du symbole (monochrome, version blanche, marquage clair mat par ablation de l'anodisation (comme le stylo)). Étui : frappe signature (montants gaufrés à sec + diagonale en feuille orange).",
    technique_en="Drive: laser-engraved symbol (monochrome, white version, light matte marking by ablating the anodising (like the pen)). Case: signature stamp (posts blind-embossed + diagonal in orange foil).",
    zones=["Clé : 58 × 19 mm ; symbole gravé de 11 mm, centré à 12 mm du bord du pivot.", "Étui : 100 × 52 × 22 mm ; symbole de 16 mm centré sur le couvercle (zone de protection de 3,2 mm).",
           "Aucune capacité ni vitesse imprimée sur l'objet."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os", "or_feuille", "orange"],
    notes_fr=["La clé est livrée vide ou préchargée selon le besoin (à décider : aucun contenu n'est préchargé par défaut).", "Le fichier de matrice de l'étui est le même que celui du carnet, à l'échelle."],
    notes_en=["The drive ships empty or preloaded as needed (to decide: nothing is preloaded by default).", "The case die file is the same as the notebook's, scaled."])


def gabarit_usb():
    g = Gabarit(220, 80)
    g.add("SILHOUETTE", '<rect x="4" y="12" width="58" height="19" rx="2.5" fill="#C9CBD0" stroke="#9A9AA6" stroke-width=".4"/><rect x="62" y="16" width="12" height="11" fill="#555" stroke="#9A9AA6" stroke-width=".3"/>')
    g.add("ART", symbole(4 + 12, 12 + 4, 11, "blanc"))
    g.rect("ZONE-IMPRESSION", 4 + 10, 12 + 2, 15, 15, C_IMPR, "2 1", sw=.3)
    g.cote_h(16, 27, 8, "11 mm", 3)
    g.note(4, 4, "CLÉ (1:1)", 3.4)
    ex, ey = 90, 4
    g.add("SILHOUETTE", f'<rect x="{ex}" y="{ey}" width="100" height="52" rx="4" fill="#16161C" stroke="#9A9AA6" stroke-width=".5"/>')
    p, d = symbole_frappe_local(ex + 42, ey + 18, 16)
    g.add("GAUFRAGE-SEC", f'<g fill="#3A3A44" stroke="{OS}" stroke-width=".2" stroke-dasharray=".8 .6">{p}</g>')
    g.add("FEUILLE-ORANGE", f'<g fill="{ORANGE}">{d}</g>')
    g.rect("ZONE-IMPRESSION", ex + 42 - 3.2, ey + 18 - 3.2, 22.4, 22.4, C_IMPR, "2 1", sw=.3)
    g.cote_h(ex + 42, ex + 58, ey + 12, "16 mm", 3)
    g.note(ex, ey - 1, "COUVERCLE DE L'ÉTUI (1:1)", 3.4)
    return g


def symbole_frappe_local(x, y, taille):
    s = taille / 52.0
    p = f'<rect x="{x}" y="{y}" width="{10.4 * s:.3f}" height="{taille}"/><rect x="{x + 41.6 * s:.3f}" y="{y}" width="{10.4 * s:.3f}" height="{taille}"/>'
    d = "".join(f'<rect x="{x + k * 10.4 * s:.3f}" y="{y + k * 10.4 * s:.3f}" width="{10.4 * s:.3f}" height="{10.4 * s:.3f}"/>' for k in (1, 2, 3))
    return p, d


def maquette_usb():
    base = charger_photo("usb2")
    k = 1.5625
    c = np.array([795.0, 735.0]); ux = np.array([.9, .44]); uy = np.array([-.646, .763])
    h = 52.0
    quad = [tuple((c + a * ux * h + b * uy * h) * k) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    art = raster_art(svg_doc(11, 11, symbole(0, 0, 11, "blanc")), 40.0, "usb_art")
    w = poser_perspective(art, quad)
    lum = np.clip(carte_lumiere(base, sigma_large=120, force_fin=.3), .8, 1.2)
    out = gravure(base, w, clair=.88, profondeur=.8)
    return finition(out, .009, .2)


# ============================================================ 11 PORTE-BADGE ET CORDON
def barres_braise(x, y, longueur, ep=1.3, jeu=.7, horizontal=True):
    cols = BRAISE[1:5]
    out = ""
    for i, c in enumerate(cols):
        o = i * (ep + jeu)
        out += (f'<rect x="{x}" y="{y + o:.3f}" width="{longueur}" height="{ep}" fill="{c}"/>' if horizontal else
                f'<rect x="{x + o:.3f}" y="{y}" width="{ep}" height="{longueur}" fill="{c}"/>')
    return out


BADGE = dict(
    num=11, slug="porte-badge", nom_fr="Porte-badge et cordon", nom_en="Badge holder and lanyard",
    desc_fr="Un cordon tissé noir, sans un mot, et un porte-badge rigide noir mat dont l'insert porte le logo et la bande de braise ; la place du nom reste vide, à remplir à l'inscription.",
    desc_en="A black woven lanyard, without a word, and a rigid matte black badge holder whose insert carries the logo and the ember band; the name area is left empty, to be filled at registration.",
    materiau_fr="Cordon : polyester tissé jacquard noir, largeur 15 mm, longueur 900 mm, mousqueton métal noir mat, sécurité de rupture ; porte-badge : PETG transparent, 86 × 54 mm utiles.",
    materiau_en="Lanyard: black jacquard-woven polyester, 15 mm wide, 900 mm long, matte black metal clasp, breakaway safety; holder: clear PETG, 86 × 54 mm usable.",
    technique_fr="Cordon : tissage ton sur ton (fils noirs, grain fin), mousqueton nickelé ou noir ; insert : impression offset CMJN + noir riche, pelliculage mat.",
    technique_en="Lanyard: tone-on-tone weave (black threads, fine grain), nickel or black clasp; insert: offset CMYK + rich black, matte lamination.",
    zones=["Cordon : noir uni de 15 mm × 900 mm, sans marquage (la marque vit sur l'insert) ; option à valider : bande braise de quatre barres de 1,3 mm.",
           "Insert : 54 × 86 mm vertical, logo complet de 34 mm de large (minimum 18 mm) en haut à gauche, bande braise en pied ; zone du nom vide.",
           "Aucun nom ni titre imprimé : à ajouter par l'organisateur."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange", "b1", "b2", "b4"],
    notes_fr=["Les quatre barres de la bande braise de l'insert utilisent les teintes #FFB11A, #FF8A1F, #FF5A1F et #E0341C (calque ART de l'insert).", "Le cordon reste noir uni par retenue : si une option imprimée est retenue, la bande braise (4 barres, 1,3 mm) se tisse au centre ; le symbole ne se répète jamais le long du cordon (il n'est pas un motif)."],
    notes_en=["The four bars use #FFB11A, #FF8A1F, #FF5A1F and #E0341C.", "In weaving, allow at least 0.8 mm per visible thread: do not shrink the bars.",
              "The symbol does not repeat along the lanyard (it is not a pattern): one occurrence only, at the centre of the front."])


def gabarit_badge():
    g = Gabarit(960, 110)
    g.add("SILHOUETTE", '<rect x="0" y="0" width="900" height="15" fill="#16161C" stroke="#9A9AA6" stroke-width=".3"/>')
    g.cote_h(0, 900, -6, "900 mm", 5)
    g.cote_v(-8, 0, 15, "15 mm", 3)
    g.note(0, 24, "CORDON (1:1, déroulé) · noir uni, tissage ton sur ton, sans marquage", 4)
    # insert
    ix, iy = 10, 34
    g.add("SILHOUETTE", f'<rect x="{ix}" y="{iy}" width="54" height="86" rx="3" fill="{NOIR}" stroke="#9A9AA6" stroke-width=".4"/>')
    lg, lh = logo_complet(ix + 6, iy + 6, 34, "sombre")
    g.add("ART", lg + barres_braise(ix, iy + 86 - 14, 54))
    g.rect("COUPE", ix, iy, 54, 86, C_COUPE, rx=3, sw=.3)
    g.rect("SECURITE", ix + 3, iy + 3, 48, 80, C_SEC, "1.5 1.5", rx=2, sw=.25)
    g.note(ix + 62, iy + 10, "INSERT 54 × 86 mm (1:1)", 4)
    g.note(ix + 62, iy + 17, "zone vide : nom à ajouter", 3.4)
    return g


def art_insert(x=0, y=0):
    lg, lh = logo_complet(x + 6, y + 6, 34, "sombre")
    return f'<rect x="{x}" y="{y}" width="54" height="86" fill="{NOIR}"/>' + lg + barres_braise(x, y + 86 - 14, 54)


def maquette_badge():
    base = charger_photo("badge")
    k = 1.5625
    art = raster_art(svg_doc(54, 86, art_insert(0, 0)), 14.0, "badge_art")
    quad = [(680 * k, 897 * k), (893 * k, 946 * k), (791 * k, 1299 * k), (564 * k, 1245 * k)]
    w = poser_perspective(art, quad)
    lum = np.clip(comprime(carte_lumiere(base, sigma_large=160, force_fin=.1), .6, .8, 1.05), .8, 1.05)
    out = vernis_uv(base, w, lum=lum, plafond=1.0, brillance=.15)
    # reflet doux du film PETG
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    A = w[..., 3]
    refl = np.exp(-(((xx * .6 + yy * .8) - 1900) / 120.0) ** 2) * .07 * A
    out = np.clip(out + refl[..., None], 0, 1)
    return finition(out, .009, .2)


# ============================================================ 14 TAPIS DE BUREAU
def art_tapis(x=0, y=0):
    cell = 10
    sx, sy = x + 26, y + 540 - 26 - 22
    keep = lambda c, r: not (x + c * cell + cell > sx - 12 and x + c * cell < sx + 22 + 12 and y + r * cell + cell > sy - 12 and y + r * cell < sy + 22 + 12)
    return (f'<rect x="{x}" y="{y}" width="600" height="540" fill="{NOIR}"/>' + svg_mosaic(x, y, 600, 60, 54, seed=3, toward="right", fade=0.88, keep=keep) +
            symbole(sx, sy, 22, "blanc"))


TAPIS = dict(
    num=14, slug="tapis-bureau", nom_fr="Tapis de bureau grand format (sous-main)", nom_en="Large desk mat (blotter)",
    desc_fr="Un sous-main de 640 × 580 mm : la mosaïque de braise monte du côté droit et se dissout vers le clavier. En bas à gauche, dans le noir, le symbole.",
    desc_en="A 640 × 580 mm desk blotter: the ember mosaic rises on the right and dissolves toward the keyboard. Bottom left, in the black, the symbol.",
    materiau_fr="Dessus similicuir PU noir mat à grain fin, sous-couche en feutre de 3 mm antidérapante, couture périphérique noire, bords arrondis ; 640 × 580 mm hors tout.",
    materiau_en="Matte black fine-grain PU leatherette top, 3 mm non-slip felt backing, black perimeter stitching, rounded corners; 640 × 580 mm overall.",
    technique_fr="Impression numérique UV à plat directement sur le similicuir (CMJN + noir riche), puis découpe et couture ; contrôler que le noir profond reste profond.",
    technique_en="Flatbed UV print directly on the leatherette (CMYK + rich black), then cutting and stitching; check that deep black stays deep.",
    zones=["Surface imprimée : 600 × 540 mm (20 mm de marge de couture de chaque côté) ; fonds perdus de 5 mm.", "Mosaïque : 60 × 54 cases de 10 mm, pleine à droite, dissoute vers la gauche.",
           "Symbole (version blanche) : 22 mm, à 26 mm du bord gauche et du bas de la surface imprimée ; aucune case à moins de 12 mm (zone de protection)."],
    moq_fr="Environ 50 pièces (indicatif, à confirmer).", moq_en="About 50 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os", "b0", "b1", "b2", "b3", "b4", "b5"],
    notes_fr=["Le symbole blanc est utilisé parce que le logo en couleur ne se pose jamais près de la mosaïque.", "Variante « grand tapis de souris » 900 × 400 mm : même art étiré à 90 × 40 cases, par sublimation sur microfibre (essai de teinte requis).",
              "Couture : fil noir, sans marque."],
    notes_en=["The white symbol is used because the colour logo never sits next to the mosaic.", "“Long mouse mat” variant 900 × 400 mm: same art stretched to 90 × 40 cells, dye-sublimation on microfibre (colour test required).", "Stitching: black thread, no mark."])


def gabarit_tapis():
    g = Gabarit(640, 580)
    g.add("SILHOUETTE", f'<rect width="640" height="580" rx="14" fill="{NOIR}" stroke="#9A9AA6" stroke-width=".6"/>')
    g.add("ART", f'<defs><clipPath id="tp"><rect width="600" height="540" rx="4"/></clipPath></defs><g transform="translate(20 20)"><g clip-path="url(#tp)">{art_tapis(0, 0)}</g></g>')
    g.rect("COUPE", 0, 0, 640, 580, C_COUPE, rx=14, sw=.5)
    g.rect("SECURITE", 28, 28, 584, 524, C_SEC, "3 3", rx=4, sw=.4)
    g.rect("ZONE-IMPRESSION", 20, 20, 600, 540, C_IMPR, "4 2", rx=4, sw=.5)
    g.cote_h(0, 640, -6, "640 mm", 6)
    g.cote_v(-8, 0, 580, "580 mm", 6)
    g.cote_h(46, 68, 580 - 46 - 22 - 16, "22 mm", 4)
    return g


def maquette_tapis():
    base = charger_photo("tapis")
    k = 1.5625
    art = raster_art(svg_doc(600, 540, art_tapis(0, 0)), 2.4, "tapis_art")
    quad = [(216 * k, 266 * k), (1334 * k, 266 * k), (1386 * k, 1250 * k), (150 * k, 1250 * k)]
    w = poser_perspective(art, quad)
    lum = comprime(carte_lumiere(base, sigma_large=200, force_fin=.5), .55, .75, 1.15)
    out = encre(base, w, lum=lum, densite=.985, souplesse=.8, tissage=.8)
    return finition(out, .009, .2)


OBJETS = [(EPINGLETTES, gabarit_epinglettes, maquette_epinglettes), (USB, gabarit_usb, maquette_usb), (BADGE, gabarit_badge, maquette_badge), (TAPIS, gabarit_tapis, maquette_tapis)]
