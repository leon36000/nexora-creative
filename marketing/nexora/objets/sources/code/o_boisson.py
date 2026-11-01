"""Boissons : tasse en ceramique, gourde en acier, bouteille isotherme."""
from fab import *
from mock import *


def _bouteille_gabarit(d, h, haut_bouchon, zone_w, zone_h, zone_y, art, etiquette_art, ep_bouchon_couleur="#2A2A33"):
    g = Gabarit(d * 3.2 + 60, h + 40)
    # elevation de la bouteille (schema) + vue developpee de la zone
    x0 = 40
    g.add("SILHOUETTE", f'<rect x="{x0}" y="{haut_bouchon}" width="{d}" height="{h - haut_bouchon}" rx="6" fill="#EDEDF0" stroke="#9A9AA6" stroke-width=".6"/>'
                        f'<rect x="{x0 + 6}" y="0" width="{d - 12}" height="{haut_bouchon}" rx="4" fill="#D5D5DB" stroke="#9A9AA6" stroke-width=".6"/>')
    g.rect("ZONE-IMPRESSION", x0 + d / 2 - zone_w / 2, zone_y, zone_w, zone_h, C_IMPR, "4 2", sw=.6)
    g.add("ART", art(x0 + d / 2, zone_y + zone_h / 2))
    g.cote_h(x0 + d / 2 - zone_w / 2, x0 + d / 2 + zone_w / 2, zone_y - 4, f"{zone_w:g} mm", 5)
    g.cote_v(x0 - 8, zone_y, zone_y + zone_h, f"{zone_h:g} mm", 5)
    g.cote_h(x0, x0 + d, h + 12, f"Ø {d:g} mm", 5)
    g.cote_v(x0 + d + 10, 0, h, f"{h:g} mm", 5)
    g.ligne("REPERES", x0 + d / 2, -10, x0 + d / 2, h + 20, C_REP, .25, "6 3")
    # vue developpee (a plat) de la surface, pour le fournisseur
    circ = math.pi * d
    ox = x0 + d + 40
    g.rect("COUPE", ox, haut_bouchon, circ, h - haut_bouchon, C_COUPE, sw=.5)
    cx = ox + circ / 2
    g.rect("ZONE-IMPRESSION", cx - zone_w / 2, zone_y, zone_w, zone_h, C_IMPR, "4 2", sw=.6)
    g.add("ART", art(cx, zone_y + zone_h / 2))
    g.cote_h(ox, ox + circ, h + 12, f"développé {circ:.0f} mm", 5)
    g.note(ox, haut_bouchon - 6, "VUE DÉVELOPPÉE (surface à plat)", 4)
    g.note(x0, -6, "ÉLÉVATION (schéma)", 4)
    return g


# ============================================================ 05 TASSE
TASSE = dict(
    num=5, slug="tasse", nom_fr="Tasse en céramique noire mate", nom_en="Matte black ceramic mug",
    desc_fr="Grès noir mat, doux sous le pouce. Le symbole en os et orange, posé comme une signature, face à la main qui la tient.",
    desc_en="Matte black stoneware, soft under the thumb. The symbol in bone and orange, set like a signature, facing the hand that holds it.",
    materiau_fr="Grès ou porcelaine émaillée noir mat, capacité d'environ 350 ml, passe au lave-vaisselle, intérieur noir mat.",
    materiau_en="Matte black glazed stoneware or porcelain, about 350 ml, dishwasher-safe, matte black interior.",
    technique_fr="Décalcomanie céramique cuite à basse température (2 couleurs : os + orange), ou impression UV durcie ; à valider au lave-vaisselle.",
    technique_en="Ceramic decal fired at low temperature (2 colours: bone + orange), or cured UV print; validate dishwasher durability.",
    zones=["Marque : symbole de 38 mm, centré à 90° de l'anse (face visible pour un droitier), centre à 50 mm du bord supérieur.",
           "Zone d'impression : 60 × 60 mm. Zone de sécurité : 4 mm autour du symbole.",
           "Mug : Ø 82 mm, hauteur 105 mm ; développé 258 mm."],
    moq_fr="Environ 100 pièces (indicatif, à confirmer).", moq_en="About 100 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os", "orange"],
    notes_fr=["Le symbole est le fichier officiel « sombre » (os + orange signal), non modifié ; aucune ombre, aucun contour.",
              "Sur céramique, l'os est un blanc cassé : demander un essai de cuisson pour que l'os reste chaud et ne vire pas au blanc pur.",
              "Aucun texte, aucun chiffre, aucune date. Dessous de la tasse : symbole seul en relief ou estampille, facultatif.",
              "Demander un échantillon physique avant la série (comparer l'orange au nuancier)."],
    notes_en=["The symbol is the official dark-background file (bone + signal orange), unmodified; no shadow, no outline.",
              "On ceramic, bone is an off-white: request a firing test so the bone stays warm and does not turn pure white.",
              "No text, number or date. Underside: symbol alone, embossed or stamped, optional.",
              "Request a physical sample before the run (compare the orange against the swatch)."])


def gabarit_tasse():
    d, h = 82, 105
    circ = math.pi * d
    g = Gabarit(circ + 80, h + 50)
    ox = 40
    g.add("SILHOUETTE", f'<rect x="{ox}" y="25" width="{circ:.2f}" height="{h}" fill="{NOIR}"/>')
    g.rect("COUPE", ox, 25, circ, h, C_COUPE, sw=.5)
    cx = ox + circ / 4              # 90 degres de l'anse (anse a x = ox et ox+circ)
    g.rect("ZONE-IMPRESSION", cx - 30, 25 + 50 - 30, 60, 60, C_IMPR, "4 2", sw=.6)
    g.rect("SECURITE", cx - 23, 25 + 50 - 23, 46, 46, C_SEC, "1.5 1.5", sw=.4)
    g.add("ART", symbole(cx - 19, 25 + 50 - 19, 38, "sombre"))
    g.ligne("REPERES", ox, 10, ox, 25 + h + 12, C_REP, .25, "6 3")
    g.ligne("REPERES", ox + circ, 10, ox + circ, 25 + h + 12, C_REP, .25, "6 3")
    g.note(ox, 6, "AXE DE L'ANSE (0°)", 4)
    g.note(ox + circ, 6, "AXE DE L'ANSE (360°)", 4, ancrage="end")
    g.ligne("REPERES", cx, 12, cx, 25 + h + 12, C_REP, .25, "6 3")
    g.note(cx, 8, "CENTRE DE LA MARQUE (90°)", 4, ancrage="middle")
    g.cote_h(ox, ox + circ, 25 + h + 12, f"développé {circ:.0f} mm (Ø {d} mm)", 5)
    g.cote_v(ox - 10, 25, 25 + h, f"{h} mm", 5)
    g.cote_h(cx - 19, cx + 19, 25 + 50 - 38, "38 mm", 4)
    g.cote_v(cx + 40, 25, 25 + 50, "50 mm", 4)
    return g


def maquette_tasse():
    base = charger_photo("tasse")
    art = raster_art(svg_doc(38, 38, symbole(0, 0, 38, "sombre")), 30, "tasse_art")
    w = poser_cylindre(art, 38, 38, 1195, 1360, 406, 41, phi0=0.0)
    return finition(vernis_uv(base, w))



# ============================================================ 06 GOURDE EN ACIER
GOURDE = dict(
    num=6, slug="gourde-acier", nom_fr="Gourde en acier inoxydable", nom_en="Stainless steel water bottle",
    desc_fr="Acier brossé, bouchon noir mat. Le symbole gravé au laser, sans encre : la marque ne s'écaille pas, elle s'use avec l'objet.",
    desc_en="Brushed steel, matte black cap. The symbol laser-engraved, no ink: the mark does not chip, it ages with the object.",
    materiau_fr="Acier inoxydable 304 brossé, simple paroi, bouchon à vis noir mat avec anse, contenance d'environ 750 ml ; sans BPA.",
    materiau_en="Brushed 304 stainless steel, single wall, matte black screw cap with loop, about 750 ml; BPA-free.",
    technique_fr="Gravure laser à fibre (marquage noir par oxydation), une couleur ; symbole monochrome officiel (version noire).",
    technique_en="Fibre-laser engraving (black oxidation marking), single colour; official monochrome symbol (black version).",
    zones=["Zone de gravure : 56 × 110 mm, centrée, haut à 90 mm sous le bouchon.", "Symbole : 44 mm de côté (version monochrome noire, remplissage plein, sans contour).",
           "Corps : Ø 73 mm, hauteur totale 265 mm ; développé 229 mm."],
    moq_fr="Environ 50 pièces (indicatif, à confirmer).", moq_en="About 50 pieces (indicative, to be confirmed).",
    couleurs=["noir", "os"],
    notes_fr=["La gravure est monochrome : le fichier est le symbole noir officiel ; l'orange n'existe pas en gravure sur inox (option : impression UV orange sur le carré central).",
              "Prévoir un test de profondeur : marquage noir et net, sans rugosité qui retient la saleté.",
              "Aucun texte, aucun volume imprimé en couleur ; la capacité peut être poinçonnée sous le fond si le fournisseur l'exige."],
    notes_en=["Engraving is monochrome: the file is the official black symbol; orange does not exist in engraving on steel (option: orange UV print on the central square).",
              "Request a depth test: crisp black marking, with no roughness that traps dirt.",
              "No text, no volume printed in colour; capacity may be stamped under the base if the supplier requires it."])


def gabarit_gourde():
    return _bouteille_gabarit(73, 265, 45, 56, 110, 90, lambda cx, cy: symbole(cx - 22, cy - 22, 44, "noir"), None)


# ============================================================ 20 BOUTEILLE ISOTHERME
ISOTHERME = dict(
    num=20, slug="bouteille-isotherme", nom_fr="Bouteille isotherme écrue", nom_en="Ecru insulated bottle",
    desc_fr="Double paroi, laque écrue mate, bouchon noir. Le symbole noir et orange, imprimé net : une bouteille pour les longues journées, qui se pose bien sur une table de réunion.",
    desc_en="Double wall, matte ecru powder coat, black cap. The symbol in black and orange, crisply printed: a bottle for long days that sits well on a meeting table.",
    materiau_fr="Acier inoxydable double paroi sous vide, laque poudre écrue mate (#F3F2EC approchée), bouchon à vis noir mat, contenance d'environ 500 ml.",
    materiau_en="Vacuum double-wall stainless steel, matte ecru powder coat (about #F3F2EC), matte black screw cap, about 500 ml.",
    technique_fr="Impression UV 2 couleurs (noir profond + orange du logo clair) sur surface cylindrique, ou tampographie 2 passes.",
    technique_en="2-colour UV print (deep black + light-logo orange) on cylindrical surface, or 2-pass pad printing.",
    zones=["Zone d'impression : 60 × 100 mm, centrée, haut à 95 mm sous le bouchon.", "Symbole : 48 mm (version claire : montants #121218, diagonale #F04A10).",
           "Corps : Ø 68 mm, hauteur totale 270 mm ; développé 214 mm."],
    moq_fr="Environ 50 pièces (indicatif, à confirmer).", moq_en="About 50 pieces (indicative, to be confirmed).",
    couleurs=["creme", "surface", "orange_clair", "noir"],
    notes_fr=["Sur laque écrue, c'est la version claire du symbole qui s'applique (jamais la version sombre).", "Contrôle de l'adhérence de l'encre UV au lave-main (pas lave-vaisselle) ; mentionner « lavage à la main » sur le carton d'emballage seulement."],
    notes_en=["On an ecru coat the light-background symbol version applies (never the dark version).", "Check UV ink adhesion under hand washing (not dishwasher); mention “hand wash” on the packaging only."])


def gabarit_isotherme():
    return _bouteille_gabarit(68, 270, 55, 60, 100, 95, lambda cx, cy: symbole(cx - 24, cy - 24, 48, "clair"), None)


def maquette_gourde():
    base = charger_photo("gourde")
    k = 1.5625
    art = raster_art(svg_doc(44, 44, symbole(0, 0, 44, "noir")), 14.0, "gourde_art")
    w = poser_cylindre(art, 44, 44, 765 * k, 850 * k, 185 * k, 36.5)
    return finition(gravure_inox(base, w), .009, .2)


def maquette_isotherme():
    base = charger_photo("isotherme")
    k = 1.5625
    art = raster_art(svg_doc(48, 48, symbole(0, 0, 48, "clair")), 14.0, "isotherme_art")
    w = poser_cylindre(art, 48, 48, 775 * k, 820 * k, 175 * k, 34.0)
    lum = comprime(lum_clair(base, sigma=40), k=.55, lo=.72, hi=1.0)
    return finition(vernis_uv(base, w, lum=lum, plafond=1.0, brillance=.25), .009, .2)


OBJETS = [(TASSE, gabarit_tasse, maquette_tasse), (GOURDE, gabarit_gourde, maquette_gourde), (ISOTHERME, gabarit_isotherme, maquette_isotherme)]
