"""Trois idees originales : jeu de cartes Pixel, puzzle N en braise, lampe veilleuse carree."""
from fab import *
from mock import *
from o_papeterie import fond_sombre

# =============================================================== A. JEU DE CARTES « PIXEL »
CW, CH, CR, CB = 63, 88, 3.5, 3.0      # carte poker : 63 x 88 mm, coins arrondis 3,5 mm, fonds perdus 3 mm
SEEDS = [11, 23, 35, 47, 59, 71, 83, 95]


def carte_face(i, x=0, y=0):
    """Face d'une carte : tuile 5 x 5 de braise (graine i), ou carte « N » (la grille du symbole) si i == 'N'."""
    c = 8.4
    fx, fy = x + (CW - 5 * c) / 2, y + (CH - 5 * c) / 2
    g = f'<rect x="{x - CB}" y="{y - CB}" width="{CW + 2 * CB}" height="{CH + 2 * CB}" fill="{NOIR}"/>'
    if i == "N":
        for col in range(5):
            for row in range(5):
                if col in (0, 4):
                    t = [0, 1, 2, 3, 4][min(4, row)] if col == 0 else [1, 2, 3, 4, 5][min(4, row)]
                    fill = BRAISE[t]
                elif (col, row) in ((1, 1), (2, 2), (3, 3)):
                    fill = ORANGE
                else:
                    continue
                g += f'<rect x="{fx + col * c + .3:.3f}" y="{fy + row * c + .3:.3f}" width="{c - .6:.3f}" height="{c - .6:.3f}" fill="{fill}"/>'
    else:
        for col, row, t in mosaic_cells(5, 5, i, "center", 0.0, 6):
            g += f'<rect x="{fx + col * c + .3:.3f}" y="{fy + row * c + .3:.3f}" width="{c - .6:.3f}" height="{c - .6:.3f}" fill="{BRAISE[t]}"/>'
    g += f'<rect x="{x + 3}" y="{y + 3}" width="{CW - 6}" height="{CH - 6}" rx="1.6" fill="none" stroke="{OS}" stroke-opacity=".35" stroke-width=".25"/>'
    return g


def carte_dos(x=0, y=0):
    g = f'<rect x="{x - CB}" y="{y - CB}" width="{CW + 2 * CB}" height="{CH + 2 * CB}" fill="{NOIR}"/>'
    g += f'<rect x="{x + 3}" y="{y + 3}" width="{CW - 6}" height="{CH - 6}" rx="1.6" fill="none" stroke="{OS}" stroke-opacity=".35" stroke-width=".25"/>'
    g += symbole(x + (CW - 22) / 2, y + (CH - 22) / 2, 22, "sombre")
    return g


CARTES = dict(
    num=21, slug="jeu-cartes-pixel", nom_fr="Jeu de cartes « Pixel » (idée originale)", nom_en="“Pixel” card game (original idea)",
    desc_fr="Un jeu de paires où chaque carte est une tuile de braise unique ; une seule carte reproduit la grille exacte du symbole. Le dos porte le symbole. Sans chiffre ni lettre : on joue avec les yeux.",
    desc_en="A pairs game where every card is a unique ember tile; only one card reproduces the exact grid of the symbol. The back carries the symbol. No numbers or letters: you play with your eyes.",
    materiau_fr="Carton noir de qualité jeu de cartes (environ 310 g/m²) laminé, pelliculage mat soft-touch, coins arrondis, étui rigide noir à fermeture magnétique.",
    materiau_en="Black playing-card stock (about 310 gsm), matte soft-touch lamination, rounded corners, rigid black magnetic-closure tuck box.",
    technique_fr="Impression offset CMJN + noir riche, vernis sélectif mat/brillant sur les cases, découpe aux coins arrondis, étui avec dorure orange (symbole) en option.",
    technique_en="Offset CMYK + rich black, selective matte/gloss varnish on the cells, rounded-corner die cut, box with optional orange foil symbol.",
    zones=["Carte : 63 × 88 mm (format poker), fonds perdus de 3 mm, coins arrondis de 3,5 mm, filet intérieur à 3 mm.",
           "Face : tuile de 5 × 5 cases de 8,4 mm centrée ; dos : symbole de 22 mm centré.",
           "Planche d'épreuve livrée : huit faces + le dos + la carte « N »."],
    moq_fr="Environ 100 jeux (indicatif, à confirmer).", moq_en="About 100 decks (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange", "b0", "b1", "b2", "b4", "b5"],
    notes_fr=["Chaque face est générée avec une graine fixe (voir sources/code/o_idees.py) : on peut en produire autant que nécessaire.",
              "La carte « N » respecte la géométrie du symbole sur une grille 5 × 5 ; aucune carte ne porte le logo en couleur sur la mosaïque.",
              "Aucun chiffre, aucune lettre : la règle du jeu (trouver les paires) s'explique sur la boîte avec le seul mot « Pixel » ou en images, à valider."],
    notes_en=["Each face is generated with a fixed seed (see sources/code/o_idees.py): produce as many as needed.",
              "The “N” card follows the symbol geometry on a 5 × 5 grid; no card places the colour logo on the mosaic.",
              "No numbers or letters: the rule (find the pairs) can be explained on the box with the single word “Pixel” or with pictures, to be validated."])


def gabarit_cartes():
    g = Gabarit(4 * (CW + 8) + 10, 2 * (CH + 8) + 10)
    k = 0
    for r in range(2):
        for c in range(4):
            x, y = 5 + c * (CW + 8), 5 + r * (CH + 8)
            idx = SEEDS[k]; k += 1
            g.add("ART", f'<defs><clipPath id="cp{k}"><rect x="{x - CB}" y="{y - CB}" width="{CW + 2 * CB}" height="{CH + 2 * CB}"/></clipPath></defs><g clip-path="url(#cp{k})">{carte_face(idx, x, y)}</g>')
            g.rect("COUPE", x, y, CW, CH, C_COUPE, rx=CR, sw=.3)
            g.rect("SECURITE", x + 3, y + 3, CW - 6, CH - 6, C_SEC, "1.2 1.2", rx=1.6, sw=.25)
    return g


def _carte_raster(contenu, ppm, nom):
    svg = svg_doc(CW, CH, f'<defs><clipPath id="k"><rect width="{CW}" height="{CH}" rx="{CR}"/></clipPath></defs><g clip-path="url(#k)">{contenu}</g>')
    return raster_art(svg, ppm, nom)


def maquette_cartes():
    base = fond_sombre(graine=4)
    ppm = 8.8
    faces = [_carte_raster(carte_face(s), ppm, f"carte_{s}") for s in (11, 23, "N", 59)]
    dos = _carte_raster(carte_dos(), ppm, "carte_dos")
    h, w = faces[0].shape[:2]
    out = base
    place = [(520, 900, -15), (930, 850, -7), (1350, 835, 2), (1770, 880, 11)]
    for img, (cx, cy, a) in zip(faces, place):
        out = _poser_carte_c(out, img, cx, cy, a, h, w)
    # pioche : trois cartes de dos empilees, la derniere au dessus
    for k, (cx, cy, a) in enumerate([(1165, 1736, 6), (1171, 1727, 6), (1178, 1717, 6)]):
        out = _poser_carte_c(out, dos, cx, cy, a, h, w, ombre=.8 if k else 1.1)
    return finition(out, .008, .25)


def _poser_carte_c(out, img, cx, cy, angle, h, w, ombre=1.0):
    th = np.deg2rad(angle)
    def pt(x, y):
        lx, ly = x - w / 2, y - h / 2
        return (cx + lx * np.cos(th) - ly * np.sin(th), cy + lx * np.sin(th) + ly * np.cos(th))
    quad = [pt(0, 0), pt(w, 0), pt(w, h), pt(0, h)]
    wp = poser_perspective(img, quad)
    A = wp[..., 3]
    out = ombre_contact(out, A, int(14 * ombre), int(22 * ombre), 22, .7)
    out = ombre_contact(out, A, 2, 3, 3, .5)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    lum = 1 - .12 * np.clip((xx * .4 + yy * .6) / T - .5, 0, 1)
    brillance = np.exp(-(((xx * .7 - yy * .7) - 300) / 260.0) ** 2) * .03
    col = np.clip(wp[..., :3] * lum[..., None] + brillance[..., None], 0, 1)
    ed = A - cv2.GaussianBlur(A, (0, 0), 1.6)
    col = np.clip(col + np.clip(ed, 0, 1)[..., None] * .35, 0, 1)
    return composite(out, col, cv2.GaussianBlur(A, (0, 0), .6))


def _poser_carte(out, img, pivot, angle, h, w, ombre=1.0):
    """Pose une carte dont le milieu du bord bas est a `pivot`, tournee de `angle` degres autour de lui."""
    th = np.deg2rad(angle)
    # coin local -> position : le pivot est le milieu bas de la carte, remonte de 0.12 h pour eventail serre
    def pt(x, y):
        lx, ly = x - w / 2, y - h
        return (pivot[0] + lx * np.cos(th) - ly * np.sin(th), pivot[1] + lx * np.sin(th) + ly * np.cos(th))
    quad = [pt(0, 0), pt(w, 0), pt(w, h), pt(0, h)]
    wp = poser_perspective(img, quad)
    A = wp[..., 3]
    out = ombre_contact(out, A, int(18 * ombre), int(28 * ombre), 26, .7)
    out = ombre_contact(out, A, 2, 3, 3, .5)
    yy, xx = np.mgrid[0:T, 0:T].astype(np.float32)
    lum = 1 - .14 * np.clip((xx * .4 + yy * .6) / T - .5, 0, 1)
    brillance = np.exp(-(((xx * .7 - yy * .7) - 300) / 260.0) ** 2) * .035
    col = np.clip(wp[..., :3] * lum[..., None] + brillance[..., None], 0, 1)
    # filet de tranche clair en haut a gauche
    ed = A - cv2.GaussianBlur(A, (0, 0), 1.6)
    col = np.clip(col + np.clip(ed, 0, 1)[..., None] * .35, 0, 1)
    return composite(out, col, cv2.GaussianBlur(A, (0, 0), .6))


# =============================================================== B. PUZZLE N
PN, PS = 6, 200.0              # 6 x 6 pieces sur 200 x 200 mm
PCS = PS / PN
_rng = np.random.default_rng(42)
SENS_H = _rng.integers(0, 2, (PN, PN - 1)) * 2 - 1   # pour chaque arete verticale (entre colonnes j et j+1)
SENS_V = _rng.integers(0, 2, (PN - 1, PN)) * 2 - 1   # pour chaque arete horizontale (entre rangees i et i+1)


def _bouton(sens, n=18):
    """Arete de 0 a 1 en x, bouton vers +y (sens=+1) ou -y. Retourne des points (x, y) unitaires."""
    pts = [(0, 0), (0.40, 0.0), (0.44, 0.03), (0.46, 0.085)]
    for phi in np.linspace(245, -65, n):
        pts.append((0.5 + .095 * np.cos(np.deg2rad(phi)), .165 + .095 * np.sin(np.deg2rad(phi))))
    pts += [(0.54, 0.085), (0.56, 0.03), (0.60, 0.0), (1, 0)]
    return [(x, y * sens) for x, y in pts]


def contour_piece(i, j):
    """Contour (liste de points en mm, coordonnees absolues) de la piece en rangee i, colonne j."""
    x0, y0 = j * PCS, i * PCS
    P = []

    def arete(p0, p1, normale, sens):
        # p0 -> p1 : arete droite ou avec bouton ; le bouton sort vers `normale` * sens
        if sens == 0:
            return [p0]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = np.hypot(dx, dy); ux, uy = dx / L, dy / L
        out = []
        for (bx, by) in _bouton(sens):
            out.append((p0[0] + ux * bx * L + normale[0] * by * L, p0[1] + uy * bx * L + normale[1] * by * L))
        return out[:-1]

    # haut : arete entre (i-1,j) et (i,j) : SENS_V[i-1][j] ; bouton de la piece du dessus pointe vers le bas
    s_haut = 0 if i == 0 else -SENS_V[i - 1, j]          # vu depuis la piece (i,j) vers le haut
    s_bas = 0 if i == PN - 1 else SENS_V[i, j]
    s_gauche = 0 if j == 0 else -SENS_H[i, j - 1]
    s_droite = 0 if j == PN - 1 else SENS_H[i, j]
    # haut : gauche->droite, normale vers le haut (0,-1)
    P += arete((x0, y0), (x0 + PCS, y0), (0, -1), s_haut)
    # droite : haut->bas, normale vers la droite (1,0)
    P += arete((x0 + PCS, y0), (x0 + PCS, y0 + PCS), (1, 0), s_droite)
    # bas : droite->gauche, normale vers le bas (0,1)
    P += arete((x0 + PCS, y0 + PCS), (x0, y0 + PCS), (0, 1), s_bas)
    # gauche : bas->haut, normale vers la gauche (-1,0)
    P += arete((x0, y0 + PCS), (x0, y0), (-1, 0), s_gauche)
    return P


def pts_path(pts):
    return "M" + " L".join(f"{x:.3f} {y:.3f}" for x, y in pts) + " Z"


def art_puzzle(x=0, y=0, taille=PS):
    """Image du puzzle : le N reconstitue en braise sur noir, plein cadre 200 x 200 mm."""
    return f'<rect x="{x - 3}" y="{y - 3}" width="{taille + 6}" height="{taille + 6}" fill="{NOIR}"/>' + svg_n_mosaique(x, y, taille, seed=1)


PUZZLE = dict(
    num=22, slug="puzzle-n", nom_fr="Puzzle « N en braise » (idée originale)", nom_en="“Ember N” jigsaw puzzle (original idea)",
    desc_fr="Trente-six pièces : une image de pixels de braise qui se rassemblent en N. On le monte sur un bureau, on le laisse à moitié fini devant un visiteur. Boîte noire, une seule image.",
    desc_en="Thirty-six pieces: an image of ember pixels that gather into an N. Build it on a desk, leave it half-done in front of a visitor. Black box, one picture.",
    materiau_fr="Carton gris rigide de 2 mm contrecollé sur papier noir mat, découpe à l'emporte-pièce en 6 × 6 pièces, boîte noire à couvercle.",
    materiau_en="2 mm rigid grey board laminated with matte black paper, die-cut into 6 × 6 pieces, black lidded box.",
    technique_fr="Impression offset CMJN + noir riche (image du N en braise), pelliculage mat, découpe à l'emporte-pièce selon le calque COUPE.",
    technique_en="Offset CMYK + rich black (ember N image), matte lamination, die-cut following the COUPE layer.",
    zones=["Image : 200 × 200 mm ; pièces : 6 × 6, chacune d'environ 33,3 mm de côté (sans les tenons).",
           "Fonds perdus : 3 mm. Les tenons ont une tête d'environ 6 mm.",
           "La disposition des tenons est fixée par une graine : le tracé de découpe est reproductible."],
    moq_fr="Environ 100 puzzles (indicatif, à confirmer).", moq_en="About 100 puzzles (indicative, to be confirmed).",
    couleurs=["noir", "orange", "b0", "b1", "b2", "b4", "b5"],
    notes_fr=["L'image est dérivée du symbole (carrés qui se rassemblent en N) ; le logo officiel reste intact sur la boîte (symbole seul, version sombre).",
              "Prévoir un essai de découpe : les tenons doivent entrer sans forcer sur du carton de 2 mm.",
              "Sans chiffre, sans date, sans texte sur la boîte autre que le symbole."],
    notes_en=["The picture is derived from the symbol (squares gathering into an N); the official logo stays intact on the box (symbol only, dark version).",
              "Request a die-cut trial: the knobs must fit without force on 2 mm board.",
              "No number, date or text on the box other than the symbol."])


def gabarit_puzzle():
    g = Gabarit(PS + 20, PS + 20)
    g.add("ART", f'<defs><clipPath id="pz"><rect x="{10 - 3}" y="{10 - 3}" width="{PS + 6}" height="{PS + 6}"/></clipPath></defs><g clip-path="url(#pz)">{art_puzzle(10, 10)}</g>')
    for i in range(PN):
        for j in range(PN):
            pts = [(x + 10, y + 10) for x, y in contour_piece(i, j)]
            g.path("COUPE", pts_path(pts), C_COUPE, sw=.25)
    g.rect("SECURITE", 10, 10, PS, PS, C_SEC, "1.5 1.5", sw=.25)
    g.cote_h(10, 10 + PS, 6, "200 mm", 4)
    return g


def maquette_puzzle():
    ppm = 6.3
    n = int(PS * ppm)
    art = raster_art(svg_doc(PS, PS, art_puzzle(0, 0)), ppm, "puzzle_art")
    art = cv2.resize(art, (n, n), interpolation=cv2.INTER_AREA)
    from o_accessoires import fond_cuir
    base = fond_cuir(graine=8)
    ox, oy = (T - n) / 2 + 20, (T - n) / 2 + 60
    # deplacements : pieces sorties de leur place (i, j) -> (dx mm, dy mm, rot deg)
    depl = {(0, 2): (-8, -46, -9), (0, 3): (30, -62, 14), (3, 5): (58, 20, 6), (5, 1): (-34, 52, -12), (2, 0): (-60, -6, 8)}
    ordre = [(i, j) for i in range(PN) for j in range(PN)]
    ordre.sort(key=lambda p: (p in depl, p))
    out = base
    for (i, j) in ordre:
        pts = np.array(contour_piece(i, j), np.float32) * ppm
        x0, y0 = pts.min(0) - 6; x1, y1 = pts.max(0) + 6
        bw, bh = int(x1 - x0), int(y1 - y0)
        m = np.zeros((bh, bw), np.uint8)
        cv2.fillPoly(m, [((pts - [x0, y0]) * 8).astype(np.int32)], 255, lineType=cv2.LINE_AA, shift=3)
        m = m.astype(np.float32) / 255
        # texture d'image de la piece
        ys0, xs0 = int(y0), int(x0)
        tex = np.zeros((bh, bw, 4), np.float32)
        a = art[max(0, ys0):ys0 + bh, max(0, xs0):xs0 + bw]
        tex[(0 if ys0 >= 0 else -ys0):(0 if ys0 >= 0 else -ys0) + a.shape[0], (0 if xs0 >= 0 else -xs0):(0 if xs0 >= 0 else -xs0) + a.shape[1]] = a
        colb = np.where(tex[..., 3:4] > .05, tex[..., :3], bgr(NOIR))
        # relief de bord : distance au contour
        dist = cv2.distanceTransform((m > .5).astype(np.uint8), cv2.DIST_L2, 3)
        bord = np.clip(1 - dist / 5.0, 0, 1)
        gx = cv2.Sobel(cv2.GaussianBlur(m, (0, 0), 1.8), cv2.CV_32F, 1, 0, ksize=3) / 8
        gy = cv2.Sobel(cv2.GaussianBlur(m, (0, 0), 1.8), cv2.CV_32F, 0, 1, ksize=3) / 8
        biseau = np.clip(-(gx * .7 + gy * .7) * 6, -1, 1)
        colp = np.clip(colb * (1 + .5 * biseau[..., None] * bord[..., None]) + np.clip(biseau, 0, 1)[..., None] * bord[..., None] * .30, 0, 1)
        dx, dy, rot = depl.get((i, j), (0, 0, 0))
        cx, cy = ox + (x0 + x1) / 2 + dx * ppm, oy + (y0 + y1) / 2 + dy * ppm
        M = cv2.getRotationMatrix2D((bw / 2, bh / 2), rot, 1.0)
        M[0, 2] += cx - bw / 2; M[1, 2] += cy - bh / 2
        L = cv2.warpAffine(colp, M, (T, T), flags=cv2.INTER_CUBIC)
        A = cv2.warpAffine(m, M, (T, T), flags=cv2.INTER_LINEAR)
        lev = 1.0 if (i, j) in depl else .45
        out = ombre_contact(out, A, int(10 * lev), int(16 * lev), 10 + 12 * lev, .6 * lev + .3)
        out = composite(out, L, A)
    return finition(out, .009, .22)


def fond_cuir_bois(taille=T, graine=8):
    """Plan de travail : bois sombre (noyer) a fil horizontal, lumiere douce."""
    rng = np.random.default_rng(graine)
    yy, xx = np.mgrid[0:taille, 0:taille].astype(np.float32) / taille
    fil = cv2.GaussianBlur(rng.normal(0, 1, (taille, taille)).astype(np.float32), (0, 0), sigmaX=220, sigmaY=5)
    fil = fil / (fil.std() + 1e-6)
    d = np.hypot(xx - .35, yy - .3)
    v = .095 - .055 * np.clip(d * 1.2, 0, 1) + .006 * fil
    im = np.stack([v * .62, v * .84, v * 1.0], -1)
    return np.clip(im, 0, 1).astype(np.float32)



# =============================================================== C. LAMPE VEILLEUSE CARREE
LAMPE = dict(
    num=23, slug="lampe-veilleuse", nom_fr="Lampe veilleuse « carré orange » (idée originale)", nom_en="“Orange square” night light (original idea)",
    desc_fr="Un cube de verre opale qui s'allume en orange signal : le pixel qui s'allume dans le noir, devenu objet. Elle veille sur un bureau, une chambre, un comptoir. Aucune marque visible, seulement la couleur.",
    desc_en="An opal cube that glows signal orange: the pixel lighting up in the dark, turned into an object. It watches over a desk, a bedroom, a counter. No visible mark, only the colour.",
    materiau_fr="Cube de 120 mm en PMMA opale teinté orange (diffuseur), socle noir mat de 120 × 120 × 18 mm en aluminium, LED chaude à intensité réglable, alimentation USB-C.",
    materiau_en="120 mm cube in orange-tinted opal PMMA (diffuser), 120 × 120 × 18 mm matte black aluminium base, warm LED with adjustable brightness, USB-C power.",
    technique_fr="Cube : PMMA teinté dans la masse (orange signal #FF5A1F à valider éclairé et éteint) ; socle : anodisation noire mate, symbole gravé au laser sous le socle.",
    technique_en="Cube: through-dyed PMMA (signal orange #FF5A1F, validate lit and unlit); base: matte black anodising, symbol laser-engraved under the base.",
    zones=["Cube : 120 × 120 × 120 mm ; épaisseur de paroi 4 mm.", "Socle : 120 × 120 × 18 mm ; bouton tactile discret sur l'arête arrière.", "Symbole gravé sous le socle (monochrome, 20 mm) ; aucune inscription visible."],
    moq_fr="Environ 50 pièces (indicatif, à confirmer).", moq_en="About 50 pieces (indicative, to be confirmed).",
    couleurs=["orange", "noir", "os"],
    notes_fr=["Prototype à valider : l'orange allumé tire vers le jaune avec une LED trop froide ; viser une LED chaude (chromaticité à fixer par essai).", "Aucune performance (autonomie, lumens) n'est annoncée sur l'objet ni dans la boîte tant qu'elle n'est pas mesurée."],
    notes_en=["Prototype to validate: lit orange drifts toward yellow with a cool LED; aim for a warm LED (chromaticity to fix by test).", "No performance claim (battery life, lumens) is stated on the object or the box until measured."])


def gabarit_lampe():
    g = Gabarit(300, 160)
    g.add("SILHOUETTE", f'<rect x="10" y="10" width="120" height="120" fill="#F0E6DF" stroke="#9A9AA6" stroke-width=".5"/><rect x="10" y="130" width="120" height="18" fill="{NOIR}"/>')
    g.add("ART", f'<rect x="14" y="14" width="112" height="112" fill="{ORANGE}"/>')
    g.cote_h(10, 130, 6, "120 mm", 5)
    g.cote_v(140, 10, 130, "120 mm", 5)
    g.cote_v(150, 130, 148, "18 mm", 4)
    g.note(10, 156, "FACE (1:1) · PMMA orange, socle noir", 4)
    g.add("SILHOUETTE", f'<rect x="170" y="10" width="120" height="120" fill="{NOIR}" stroke="#9A9AA6" stroke-width=".5"/>')
    g.add("ART", symbole(170 + 50, 10 + 50, 20, "blanc"))
    g.note(170, 156, "DESSOUS DU SOCLE (1:1) · gravure laser", 4)
    return g


def maquette_lampe():
    """Le cube de la photo est ambre : on le recolore en orange signal (teinte, saturation), la lueur suit."""
    base = charger_photo("lampe")
    hsv = cv2.cvtColor(base, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    chaud = np.clip(v * 4, 0, 1)
    h2 = np.where(chaud > 0, h - 11.0 * chaud, h)           # ambre (~33 deg) -> orange signal (~14 deg)
    s2 = np.clip(s * (1 + .22 * chaud) + .03 * chaud, 0, 1)
    hsv2 = np.stack([np.mod(h2, 360), s2, np.clip(v * 1.02, 0, 1)], -1).astype(np.float32)
    out = cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR)
    return finition(out, .008, .22)


OBJETS = [(CARTES, gabarit_cartes, maquette_cartes), (PUZZLE, gabarit_puzzle, maquette_puzzle), (LAMPE, gabarit_lampe, maquette_lampe)]
