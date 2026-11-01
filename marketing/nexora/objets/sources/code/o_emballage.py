"""Emballage et presentation : trousse de bienvenue, sac de papier, ruban adhesif, boite « edition lancement », fond de kiosque."""
from fab import *
from mock import *
from o_papeterie import symbole_frappe, fond_sombre
from o_accessoires import barres_braise, fond_cuir

# ============================================================ 16 TROUSSE DE BIENVENUE
def carte_remerciement(lang="fr", x=0, y=0):
    """Carte de bienvenue 148 x 105 mm : symbole, ligne de campagne, bande braise. Verso = autre langue."""
    ligne1, ligne2 = ("Rêvez grand.", "Gardez le contrôle.") if lang == "fr" else ("Dream big.", "Stay in control.")
    t1, w1 = texte(ligne1, x + 14, y + 66, 11.5, OS)
    t2, w2 = texte(ligne2, x + 14, y + 80, 11.5, OS)
    return (f'<rect x="{x - 3}" y="{y - 3}" width="154" height="111" fill="{NOIR}"/>' + symbole(x + 14, y + 14, 16, "sombre") + t1 + t2 +
            barres_braise(x, y + 105 - 10.6, 148))


TROUSSE = dict(
    num=16, slug="trousse-bienvenue", nom_fr="Trousse de bienvenue", nom_en="Welcome kit",
    desc_fr="Une boîte noire à fermeture aimantée ; on soulève le couvercle, un papier de soie noir, une carte au revers bilingue, la planche d'autocollants. Le premier geste du client est un déballage.",
    desc_en="A black magnetic-closure box; lift the lid, black tissue paper, a bilingual card, the sticker sheet. The customer's first gesture is an unboxing.",
    materiau_fr="Boîte rigide à rabat 280 × 220 × 70 mm, carton gris de 2 mm gainé de papier noir mat, aimants dissimulés, intérieur noir ; papier de soie noir 18 g/m² ; carte 148 × 105 mm, papier 350 g/m².",
    materiau_en="Rigid flap box 280 × 220 × 70 mm, 2 mm grey board wrapped in matte black paper, hidden magnets, black interior; black 18 gsm tissue; 148 × 105 mm card, 350 gsm paper.",
    technique_fr="Boîte : dorure à chaud os (logo complet blanc, monochrome) à l'intérieur du rabat, face qu'on découvre à l'ouverture ; extérieur noir uni. Carte : offset CMJN + noir riche, pelliculage soft-touch, verso en anglais ; planche d'autocollants : voir l'objet 12.",
    technique_en="Box: bone hot-foil (monochrome white full logo) inside the flap, the face you discover on opening; plain black outside. Card: offset CMYK + rich black, soft-touch lamination, English on the back; sticker sheet: see object 12.",
    zones=["Intérieur du rabat : logo complet de 70 mm de large, centré ; extérieur sans marquage.", "Carte : symbole 16 mm, ligne de campagne en Geist 11,5 mm, bande braise de 10,6 mm en pied ; fonds perdus de 3 mm.",
           "Contenu : papier de soie, carte, planche d'autocollants (148 × 210 mm, à plat)."],
    moq_fr="Environ 100 trousses (indicatif, à confirmer).", moq_en="About 100 kits (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange", "b1", "b2", "b4"],
    notes_fr=["Le message de remerciement manuscrit ou imprimé est volontairement vide : le mot « Merci » n'est pas dans la liste des mots autorisés sur les objets ; à valider avec le fondateur avant impression.",
              "Papier de soie noir sans impression (le symbole n'est pas un motif répété).", "Fermeture aimantée : vérifier la force des aimants pour que le couvercle ne se rouvre pas au transport."],
    notes_en=["The thank-you message is deliberately empty: the word “Thank you” is not on the approved short-words list for objects; validate with the founder before printing.",
              "Plain black tissue (the symbol is not a repeating pattern).", "Magnetic closure: check magnet strength so the lid does not reopen in transit."])


def gabarit_trousse():
    g = Gabarit(280 + 170 + 30, 220 + 30)
    g.add("SILHOUETTE", f'<rect width="280" height="220" rx="2" fill="{NOIR}" stroke="#9A9AA6" stroke-width=".5"/>')
    lg, lh = logo_complet(105, 110 - 6.5, 70, "blanc")
    g.add("FEUILLE-ORANGE", "")      # (calque inutilise ici : la dorure est en os)
    g.add("ART", lg)
    g.rect("ZONE-IMPRESSION", 95, 110 - 14, 90, 28, C_IMPR, "3 1.5", sw=.4)
    g.cote_h(105, 175, 110 - 20, "70 mm", 4)
    g.cote_v(290, 0, 220, "220 mm", 5)
    g.cote_h(0, 280, 232, "280 mm", 5)
    g.note(0, -4, "INTÉRIEUR DU RABAT (1:1) · dorure os, logo complet blanc", 4)
    cx = 310
    g.add("ART", f'<g clip-path="url(#cc)"><defs><clipPath id="cc"><rect x="{cx}" y="0" width="148" height="105" rx="2"/></clipPath></defs>{carte_remerciement("fr", cx, 0)}</g>')
    g.rect("COUPE", cx, 0, 148, 105, C_COUPE, rx=2, sw=.3)
    g.add("ART", f'<g clip-path="url(#cd)"><defs><clipPath id="cd"><rect x="{cx}" y="125" width="148" height="105" rx="2"/></clipPath></defs>{carte_remerciement("en", cx, 125)}</g>')
    g.rect("COUPE", cx, 125, 148, 105, C_COUPE, rx=2, sw=.3)
    g.note(cx, -4, "CARTE RECTO (fr-CA)", 4); g.note(cx, 121, "CARTE VERSO (en-CA)", 4)
    return g


def maquette_trousse():
    from o_papeterie import planche_png
    base = charger_photo("trousse")
    k = 1.5625
    # intérieur du rabat : logo complet en feuille os
    lg, lh = logo_complet(105, 110 - 6.5, 70, "blanc")
    art_l = raster_art(svg_doc(280, 220, lg.replace("#ffffff", "#ffffff")), 6.0, "trousse_rabat")
    quad_l = [(690 * k, 172 * k), (1242 * k, 392 * k), (1150 * k, 822 * k), (548 * k, 598 * k)]
    wl = poser_perspective(art_l, quad_l)
    out = feuille_chaud(base, wl, teinte="#D9D6CC", relief=.6)
    # contenu : planche d'autocollants et carte, posees sur le papier de soie (plan du rebord reduit et descendu)
    A, B, C, D = [np.array(p, np.float32) for p in ((545, 600), (1145, 838), (870, 1160), (225, 878))]
    ctr = (A + B + C + D) / 4
    shrink = lambda p: ctr + (p - ctr) * 0.90 + np.array([0, 40], np.float32)
    P = np.array([shrink(A), shrink(B), shrink(C), shrink(D)], np.float32) * k
    H = cv2.getPerspectiveTransform(np.array([[0, 0], [280, 0], [280, 220], [0, 220]], np.float32), P)
    def sur_boite(x, y, w, h, rot=0):
        th = np.deg2rad(rot); c = np.array([x + w / 2, y + h / 2])
        pts = []
        for (px, py) in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            q = c + np.array([px * np.cos(th) - py * np.sin(th), px * np.sin(th) + py * np.cos(th)])
            v = H @ np.array([q[0], q[1], 1.0]); pts.append((v[0] / v[2], v[1] / v[2]))
        return pts
    lum = np.clip(carte_lumiere(base, sigma_large=200, force_fin=0), .7, 1.2)
    art_s, _ = planche_png("fr", 8)
    ws = poser_perspective(art_s, sur_boite(14, 6, 148, 210, -4))
    out = ombre_contact(out, ws[..., 3], 5, 9, 9, .75)
    out = composite(out, np.clip(ws[..., :3] * .55 * lum[..., None], 0, 1), ws[..., 3])
    carte = raster_art(svg_doc(148, 105, f'<defs><clipPath id="k"><rect width="148" height="105" rx="2"/></clipPath></defs><g clip-path="url(#k)">{carte_remerciement("fr", 0, 0)}</g>'), 8.0, "trousse_carte")
    wc = poser_perspective(carte, sur_boite(128, 96, 148, 105, 6))
    out = ombre_contact(out, wc[..., 3], 5, 9, 9, .8)
    out = composite(out, np.clip(wc[..., :3] * .8 * lum[..., None] + .02, 0, 1), wc[..., 3])
    return finition(out, .010, .22)


# ============================================================ 17 SAC DE PAPIER
def art_sac(x=0, y=0, lang="fr", fond=True):
    t, w = texte("IA souveraine au Québec" if lang == "fr" else "Sovereign AI, made in Québec", 0, 0, 7.2, OS)
    return ((f'<rect x="{x}" y="{y}" width="320" height="410" fill="{NOIR}"/>' if fond else "") + symbole(x + 160 - 45, y + 150, 90, "sombre") +
            f'<g transform="translate({x + 160 - w / 2} {y + 290})">{t}</g>')


SAC = dict(
    num=17, slug="sac-papier", nom_fr="Sac de papier boutique", nom_en="Boutique paper bag",
    desc_fr="Papier noir mat, poignées de corde noire. Le symbole, grand, et une seule ligne dessous : « IA souveraine au Québec ». Un sac qu'on garde pour la sortie suivante.",
    desc_en="Matte black paper, black rope handles. The symbol, large, and one line below: “Sovereign AI, made in Québec”. A bag you keep for the next outing.",
    materiau_fr="Papier couché noir mat 157 g/m² contrecollé, 320 × 410 × 120 mm, poignées de corde torsadée noire de 7 mm, fond renforcé.",
    materiau_en="Laminated matte black 157 gsm coated paper, 320 × 410 × 120 mm, 7 mm twisted black rope handles, reinforced bottom.",
    technique_fr="Sérigraphie ou flexographie 2 couleurs (os + orange du logo sombre) sur papier noir ; en option, dorure à chaud pour la diagonale.",
    technique_en="2-colour screen or flexographic print (bone + dark-logo orange) on black paper; optional hot-foil for the diagonal.",
    zones=["Face avant : symbole de 90 mm, centre à 195 mm du bas ; ligne « IA souveraine au Québec » en Geist 7,2 mm, à 40 mm sous le symbole.", "Soufflets latéraux et dos : noir uni.",
           "Version anglaise : « Sovereign AI, made in Québec » (fichier -en)."],
    moq_fr="Environ 250 sacs (indicatif, à confirmer).", moq_en="About 250 bags (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange"],
    notes_fr=["Os sur noir : contraste 17,9:1 ; le texte reste lisible à 3 mètres.", "Sur papier noir, l'encre claire demande souvent deux passes : valider l'opacité de l'os."],
    notes_en=["Bone on black: 17.9:1 contrast; the text stays legible at 3 metres.", "On black paper, light ink often needs two passes: validate the opacity of the bone."])


def gabarit_sac(lang="fr"):
    g = Gabarit(320, 410)
    g.add("SILHOUETTE", f'<rect width="320" height="410" fill="{NOIR}" stroke="#9A9AA6" stroke-width=".5"/>')
    g.add("ART", art_sac(0, 0, lang))
    g.rect("ZONE-IMPRESSION", 40, 100, 240, 220, C_IMPR, "4 2", sw=.5)
    g.rect("SECURITE", 160 - 45 - 18, 150 - 18, 126, 126, C_SEC, "2 2", sw=.4)
    g.cote_h(160 - 45, 160 + 45, 140, "90 mm", 5)
    g.cote_h(0, 320, 422, "320 mm", 5)
    g.cote_v(-8, 0, 410, "410 mm", 5)
    return g


def maquette_sac():
    base = charger_photo("sac_papier")
    k = 1.5625
    art = raster_art(svg_doc(320, 410, art_sac(0, 0, "fr", fond=False)), 3.2, "sac_art")
    quad = [(392 * k, 402 * k), (1200 * k, 420 * k), (1222 * k, 1355 * k), (402 * k, 1380 * k)]
    w = poser_perspective(art, quad)
    lum = comprime(carte_lumiere(base, sigma_large=220, force_fin=.6), .6, .65, 1.0)
    out = encre(base, w, lum=lum, densite=.97, souplesse=.8, tissage=.9)
    return finition(out, .010, .2)


# ============================================================ 18 RUBAN ADHESIF
def art_ruban(x=0, y=0, longueur=600, lang="fr", fond=True):
    out = (f'<rect x="{x}" y="{y}" width="{longueur}" height="48" fill="{NOIR}"/>' if fond else "") + barres_braise(x, y + 5, longueur, ep=1.0, jeu=.6)
    for k in range(longueur // 300):
        ox = x + k * 300 + 18
        lg, lh = logo_complet(ox, y + 24 - 3.4, 42, "sombre")
        t, w = texte("Sous votre contrôle" if lang == "fr" else "Under your control", ox + 56, y + 24 + 2.4, 6.2, OS)
        out += lg + t
    return out


RUBAN = dict(
    num=18, slug="ruban-adhesif", nom_fr="Ruban adhésif d'emballage", nom_en="Packaging tape",
    desc_fr="Du noir qui se déroule : le logo, « Sous votre contrôle » et la bande de braise en lisière. Chaque colis qui part porte la marque sans crier.",
    desc_en="Black that unrolls: the logo, “Under your control” and the ember band along the edge. Every parcel that leaves carries the brand without shouting.",
    materiau_fr="Polypropylène noir mat de 50 microns, adhésif acrylique, largeur 48 mm, rouleau de longueur standard (à confirmer).",
    materiau_en="Matte black polypropylene, 50 micron, acrylic adhesive, 48 mm wide, standard length roll (to be confirmed).",
    technique_fr="Impression flexographique 2 couleurs (os + orange), motif répété tous les 300 mm ; barres en 4 teintes en lisière.",
    technique_en="2-colour flexographic print (bone + orange), pattern repeated every 300 mm; 4-tone bars along the edge.",
    zones=["Largeur 48 mm ; répétition 300 mm (deux répétitions présentées au gabarit, 600 mm).", "Logo complet : 42 mm de large (minimum 18 mm) ; « Sous votre contrôle » en Geist 6,2 mm à 14 mm du logo.",
           "Bande braise : quatre barres de 1,0 mm (jeu 0,6 mm) à 5 mm du bord."],
    moq_fr="Environ 36 rouleaux (indicatif, à confirmer).", moq_en="About 36 rolls (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange", "b1", "b2", "b4"],
    notes_fr=["Le logo se répète comme logo (jamais le symbole seul comme motif) ; espacement fixé à 300 mm pour qu'un colis de taille courante en porte au moins un.", "Demander un test d'adhérence à basse température."],
    notes_en=["The logo repeats as a logo (never the bare symbol as a pattern); 300 mm spacing so an average parcel carries at least one.", "Request a low-temperature adhesion test."])


def gabarit_ruban(lang="fr"):
    g = Gabarit(600, 48)
    g.add("ART", art_ruban(0, 0, 600, lang))
    g.rect("COUPE", 0, 0, 600, 48, C_COUPE, sw=.4)
    g.ligne("REPERES", 300, -6, 300, 54, C_REP, .25, "4 2")
    g.cote_h(0, 300, -8, "répétition 300 mm", 5)
    g.cote_v(-8, 0, 48, "48 mm", 4)
    return g


def maquette_ruban():
    base = charger_photo("ruban")
    k = 1.5625
    ppm = 14.0
    art = raster_art(svg_doc(300, 48, art_ruban(0, 0, 300, "fr", fond=False)), ppm, "ruban_art")
    # surface exterieure du rouleau : P(phi, t) = (cx + a cos(phi) + dx t, cy + b sin(phi)) ; s = R phi (mm le long du ruban), t de 0 a 1 en travers
    cx, cy, a, b, dx = 732 * k, 790 * k, 218 * k, 360 * k, 205 * k
    R_mm, s0 = 50.0, -71.0
    x0, x1, y0, y1 = int(760 * k), int(1190 * k), int(420 * k), int(1135 * k)
    xs, ys = np.meshgrid(np.arange(x0, x1, dtype=np.float32), np.arange(y0, y1, dtype=np.float32))
    sn = np.clip((ys - cy) / b, -.999, .999)
    phi = np.arcsin(sn)
    cph = np.cos(phi)
    t = (xs - cx - a * cph) / dx
    s_mm = R_mm * phi - s0
    mapx = (s_mm / 300.0 * art.shape[1]).astype(np.float32)
    mapy = ((1 - t) * art.shape[0]).astype(np.float32)
    pm = art.copy(); pm[..., :3] *= pm[..., 3:4]
    roi = cv2.remap(pm, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    valid = ((t >= 0) & (t <= 1) & (np.abs(phi) < np.deg2rad(82)) & (s_mm >= 0) & (s_mm <= 300)).astype(np.float32)
    roi *= valid[..., None]
    w = np.zeros((T, T, 4), np.float32)
    a_ = roi[..., 3:4]
    w[y0:y1, x0:x1, :3] = np.where(a_ > 1e-4, roi[..., :3] / np.maximum(a_, 1e-4), 0)
    w[y0:y1, x0:x1, 3] = roi[..., 3]
    lum = np.clip(comprime(carte_lumiere(base, sigma_large=160, force_fin=.4), .8, .6, 1.2), .6, 1.15)
    out = encre(base, w, lum=lum * .95, densite=.96, souplesse=.9, tissage=.4)
    return finition(out, .010, .2)


# ============================================================ 19 COFFRET EDITION LANCEMENT
COFFRET = dict(
    num=19, slug="coffret-lancement", nom_fr="Boîte de présentation « édition lancement »", nom_en="“Launch edition” presentation box",
    desc_fr="Un coffret noir mat, couvercle plat, une seule frappe : le symbole, montants gaufrés à sec, diagonale en dorure orange. Rien d'autre. Ce qu'on offre aux premiers.",
    desc_en="A matte black box, flat lid, a single stamp: the symbol, posts blind-embossed, diagonal in orange foil. Nothing else. What you give to the first.",
    materiau_fr="Coffret rigide à deux pièces 260 × 260 × 90 mm, carton gris de 2,5 mm gainé de papier noir mat texturé, intérieur noir, ruban de tirage noir.",
    materiau_en="Two-piece rigid box 260 × 260 × 90 mm, 2.5 mm grey board wrapped in matte textured black paper, black interior, black pull ribbon.",
    technique_fr="Frappe signature : gaufrage à sec des montants + dorure à chaud orange de la diagonale (une matrice, une frappe).",
    technique_en="Signature stamp: blind embossing of the posts + orange hot foil on the diagonal (one die, one strike).",
    zones=["Couvercle : symbole de 70 mm de haut centré (zone de protection de 14 mm) ; aucun texte.", "Dimensions du couvercle : 262 × 262 mm ; hauteur de bord : 40 mm.",
           "« Édition lancement » n'est pas imprimé : ni mention, ni numéro, ni date."],
    moq_fr="Environ 100 coffrets (indicatif, à confirmer).", moq_en="About 100 boxes (indicative, to be confirmed).",
    couleurs=["noir", "or_feuille", "orange"],
    notes_fr=["Même principe que le carnet : calques GAUFRAGE-SEC et FEUILLE-ORANGE du gabarit pour la matrice.", "Pas de mention « limitée » ni de numérotation : aucune quantité ne peut être prouvée tant que la série n'est pas arrêtée."],
    notes_en=["Same principle as the notebook: GAUFRAGE-SEC and FEUILLE-ORANGE layers of the template make the die.", "No “limited” wording or numbering: no quantity can be proven until the run is fixed."])


def gabarit_coffret():
    g = Gabarit(262, 262)
    g.add("SILHOUETTE", f'<rect width="262" height="262" rx="3" fill="{NOIR}" stroke="#9A9AA6" stroke-width=".5"/>')
    sx, sy = 131 - 35, 131 - 35
    p, d = symbole_frappe(sx, sy, 70)
    g.add("GAUFRAGE-SEC", f'<g fill="#3A3A44" stroke="{OS}" stroke-width=".35" stroke-dasharray="1.5 1">{p}</g>')
    g.add("FEUILLE-ORANGE", f'<g fill="{ORANGE}">{d}</g>')
    g.rect("ZONE-IMPRESSION", sx - 14, sy - 14, 98, 98, C_IMPR, "4 2", sw=.5)
    g.cote_h(sx, sx + 70, sy - 20, "70 mm", 5)
    g.cote_v(sx - 22, sy, sy + 70, "70 mm", 5)
    g.cote_h(0, 262, 274, "262 mm", 5)
    g.ligne("REPERES", 131, -8, 131, 270, C_REP, .25, "6 3")
    return g


def maquette_coffret():
    from o_papeterie import frappe_signature
    base = charger_photo("coffret")
    k = 1.5625
    quad = np.array([(685, 285), (1397, 483), (968, 985), (157, 668)], np.float32) * k       # dessus du couvercle : fond, droite, avant, gauche
    H = cv2.getPerspectiveTransform(np.array([[0, 0], [262, 0], [262, 262], [0, 262]], np.float32), quad)
    def pt(x, y):
        v = H @ np.array([x, y, 1.0]); return (v[0] / v[2], v[1] / v[2])
    sq = [pt(96, 96), pt(166, 96), pt(166, 166), pt(96, 166)]
    out = frappe_signature(base, sq, 70.0, ppm=14.0, nom="coffret")
    return finition(out, .010, .2)


# ============================================================ 21 FOND DE KIOSQUE
def art_fond(x=0, y=0, lang="fr"):
    """Fond de kiosque 3000 x 3000 mm : noir, mosaique de braise a droite, ligne de campagne a gauche, logo complet."""
    g = f'<rect x="{x}" y="{y}" width="3000" height="3000" fill="{NOIR}"/>'
    g += svg_mosaic(x + 1700, y, 1300, 26, 60, seed=17, toward="right", fade=0.9)
    l1, l2 = ("Rêvez grand.", "Gardez le contrôle.") if lang == "fr" else ("Dream big.", "Stay in control.")
    t1, w1 = texte(l1, x + 200, y + 1480, 170, OS)
    t2, w2 = texte(l2, x + 200, y + 1690, 170, OS)
    lg, lh = logo_complet(x + 200, y + 300, 640, "sombre")
    return g + t1 + t2 + lg


def art_comptoir(x=0, y=0, lang="fr"):
    t, w = texte("IA souveraine au Québec" if lang == "fr" else "Sovereign AI, made in Québec", 0, 0, 62, OS)
    return (f'<rect x="{x}" y="{y}" width="1800" height="950" fill="{NOIR}"/>' + symbole(x + 900 - 130, y + 190, 260, "sombre") +
            f'<g transform="translate({x + 900 - w / 2} {y + 640})">{t}</g>' + barres_braise(x, y + 950 - 60, 1800, ep=12, jeu=6))


KIOSQUE = dict(
    num=24, slug="fond-kiosque", nom_fr="Fond de kiosque et face de comptoir (salon)", nom_en="Trade-show backdrop and counter front",
    desc_fr="Trois mètres carrés de noir et de braise : la mosaïque monte à droite, la ligne de campagne à gauche, le logo en haut. Le comptoir répète le symbole et la ligne Québec. On reconnaît le kiosque depuis l'allée.",
    desc_en="Three metres of black and ember: the mosaic rises on the right, the campaign line on the left, the logo above. The counter repeats the symbol and the Québec line. You recognise the booth from the aisle.",
    materiau_fr="Fond : toile tendue en polyester (tissu sans reflet) 3 000 × 3 000 mm sur cadre aluminium à gorge de silicone ; comptoir : panneau en PVC expansé ou tissu tendu 1 800 × 950 mm.",
    materiau_en="Backdrop: tensioned polyester fabric (non-reflective) 3,000 × 3,000 mm on an aluminium silicone-edge frame; counter: foamed PVC panel or tensioned fabric 1,800 × 950 mm.",
    technique_fr="Impression par sublimation grand format (CMJN + noir riche) pour le tissu ; impression UV à plat pour le panneau.",
    technique_en="Large-format dye-sublimation (CMYK + rich black) for fabric; flatbed UV print for the panel.",
    zones=["Fond : 3 000 × 3 000 mm ; logo complet de 640 mm de large en haut à gauche ; ligne de campagne en Geist (corps 170 mm) sur deux lignes, à mi-hauteur (hors de la zone cachée par le comptoir) ; mosaïque : cases de 50 mm, à droite de l'axe 1 700 mm (jamais sous le texte).",
           "Comptoir : 1 800 × 950 mm ; symbole de 260 mm centré, ligne « IA souveraine au Québec » en corps 62 mm, bande braise de 4 barres en pied.",
           "Fonds perdus de 30 mm et ourlet de silicone de 15 mm à ajouter selon le système de cadre."],
    moq_fr="1 jeu complet (indicatif, à confirmer) ; réutilisable d'un salon à l'autre.", moq_en="1 full set (indicative, to be confirmed); reusable from show to show.",
    couleurs=["noir", "os", "orange", "b0", "b1", "b2", "b3", "b4", "b5"],
    notes_fr=["Lisibilité à 3 mètres : la ligne de campagne fait 170 mm de corps (os sur noir, 17,9:1).", "Aucune zone importante à moins de 150 mm du bord (ourlet et cadre).", "Le logo en couleur reste hors de la mosaïque : il est dans la moitié gauche, sur noir uni."],
    notes_en=["Legible at 3 metres: the campaign line is 170 mm tall (bone on black, 17.9:1).", "Nothing important within 150 mm of the edge (hem and frame).", "The colour logo stays off the mosaic: it sits in the left half on plain black."])


def gabarit_kiosque(lang="fr"):
    g = Gabarit(3000, 3000 + 1200)
    g.add("ART", art_fond(0, 0, lang))
    g.rect("SECURITE", 150, 150, 2700, 2700, C_SEC, "20 15", sw=2)
    g.rect("COUPE", 0, 0, 3000, 3000, C_COUPE, sw=3)
    g.rect("ZONE-IMPRESSION", 0, 1900, 3000, 1100, C_IMPR, "30 15", sw=2)
    g.note(20, 1890, "ZONE PARTIELLEMENT CACHÉE PAR LE COMPTOIR (rien d'essentiel au-dessous de ce trait)", 36)
    g.cote_h(0, 3000, -12, "3 000 mm", 60)
    g.cote_v(-14, 0, 3000, "3 000 mm", 60)
    g.add("ART", art_comptoir(600, 3200, lang))
    g.rect("COUPE", 600, 3200, 1800, 950, C_COUPE, sw=3)
    g.cote_h(600, 2400, 3188, "1 800 mm", 50)
    g.cote_v(580, 3200, 4150, "950 mm", 50)
    return g


def maquette_kiosque():
    base = charger_photo("kiosque")
    k = 1.5625
    out = base
    art1 = raster_art(svg_doc(3000, 3000, art_fond(0, 0, "fr")), .45, "kiosque_fond")
    w1 = poser_perspective(art1, [(246 * k, 159 * k), (1327 * k, 159 * k), (1327 * k, 1240 * k), (246 * k, 1240 * k)])
    L = cv2.GaussianBlur(luma(base), (0, 0), 60)
    lum = np.clip(L / np.percentile(L[(w1[..., 3] > .5)], 90), .5, 1.0)
    out = encre(out, w1, lum=lum, densite=.99, souplesse=1.0, tissage=.3)
    art2 = raster_art(svg_doc(1800, 950, art_comptoir(0, 0, "fr")), .7, "kiosque_comptoir")
    w2 = poser_perspective(art2, [(303 * k, 915 * k), (1262 * k, 915 * k), (1262 * k, 1420 * k), (303 * k, 1420 * k)])
    lum2 = np.clip(carte_lumiere(base, sigma_large=160, force_fin=.2), .7, 1.2)
    out = encre(out, w2, lum=lum2, densite=.99, souplesse=.8)
    return finition(out, .009, .22)


OBJETS = [(TROUSSE, gabarit_trousse, maquette_trousse), (SAC, gabarit_sac, maquette_sac, lambda: gabarit_sac("en")), (RUBAN, gabarit_ruban, maquette_ruban, lambda: gabarit_ruban("en")),
          (COFFRET, gabarit_coffret, maquette_coffret), (KIOSQUE, gabarit_kiosque, maquette_kiosque, lambda: gabarit_kiosque("en"))]
