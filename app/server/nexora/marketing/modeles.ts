/**
 * Gabarits v1 (vague 2, #15) : 3 compositions par pièce (carte d'affaires, dépliant/affiche, accroche-porte), pilotées par
 * le kit de marque (couleurs, polices, logo, coordonnées), jamais codées pour une marque. Le LLM choisit un gabarit et
 * remplit les variables ; la géométrie, les marges et les contrastes restent au code. Langage visuel : celui du moteur
 * d'imprimés Nexora (aplats nets, filets fins, un accent, beaucoup d'air).
 */
import { contactsActifs, estVide, texteSur, type KitMarque } from './kit.js';
import { FORMATS, po, type Calque, type Face, type FormatPiece, type SpecConception } from './spec.js';

export interface Variables { accroche: string; sousTitre: string; point1: string; point2: string; point3: string; appel: string; offre: string; nom: string; titre: string; entreprise: string; telephone: string; courriel: string; web: string; adresse: string; url: string }
export type OptionsGabarit = { image?: { src: string; pxLargeur?: number; pxHauteur?: number } };
export interface Gabarit { id: string; nom: string; description: string; formats: string[]; construire: (kit: KitMarque, v: Variables, f: FormatPiece, o?: OptionsGabarit) => Face[] }

/** Variables d'un kit (coordonnées et nom) complétées par le texte de l'utilisateur ou de l'IA. */
export function variablesPour(kit: KitMarque, texte: Partial<Variables> = {}): Variables {
  const c = kit.contact, web = c.web.trim();
  const defauts: Variables = {
    accroche: '', sousTitre: '', point1: '', point2: '', point3: '', appel: '', offre: '',
    nom: c.nom, titre: c.titre, entreprise: c.entreprise || kit.nom, telephone: c.telephone, courriel: c.courriel, web: c.web, adresse: c.adresse,
    url: estVide(web) ? '' : /^https?:\/\//i.test(web) ? web : `https://${web}`,
  };
  const out = { ...defauts };
  for (const [k, v] of Object.entries(texte)) if (typeof v === 'string') (out as Record<string, string>)[k] = v.trim();
  for (const k of Object.keys(out) as (keyof Variables)[]) if (estVide(out[k])) out[k] = '';
  return out;
}

type OptT = { police?: 'titre' | 'texte'; poids?: 400 | 600 | 700; taille: number; couleur: string; align?: 'left' | 'center' | 'right'; interligne?: number; casse?: 'aucune' | 'majuscules'; crenage?: number; valign?: 'top' | 'middle' | 'bottom'; ajuster?: boolean };
class Outils {
  n = 0;
  constructor(public kit: KitMarque, public sx = 1, public sy = 1) {}
  id = (p: string) => `${p}${++this.n}`;
  txt(texte: string, x: number, y: number, l: number, h: number, o: OptT, id?: string): Calque {
    return { type: 'texte', id: id ?? this.id('texte'), x: x * this.sx, y: y * this.sy, l: l * this.sx, h: h * this.sy, texte, police: this.kit.polices[o.police ?? 'texte'], poids: o.poids ?? 400, taille: o.taille * this.sx, couleur: o.couleur, align: o.align ?? 'left', interligne: o.interligne ?? 1.2, crenage: o.crenage ?? 0, casse: o.casse ?? 'aucune', ajuster: o.ajuster ?? true, valign: o.valign ?? 'top' };
  }
  forme(x: number, y: number, l: number, h: number, remplissage: string, extra: Partial<Extract<Calque, { type: 'forme' }>> = {}): Calque {
    return { type: 'forme', id: this.id('forme'), x: x * this.sx, y: y * this.sy, l: l * this.sx, h: h * this.sy, forme: 'rect', remplissage, epaisseur: 0.25, rayon: 0, opacite: 1, decoupe: false, ...extra };
  }
  logo(x: number, y: number, l: number, h: number, variante: 'original' | 'clair' | 'sombre'): Calque { return { type: 'logo', id: this.id('logo'), x: x * this.sx, y: y * this.sy, l: l * this.sx, h: h * this.sy, variante }; }
  qr(x: number, y: number, t: number, url: string, fond?: string, encre?: string): Calque { return { type: 'qr', id: this.id('qr'), x: x * this.sx, y: y * this.sy, l: t * this.sx, h: t * this.sx, url, ...(fond ? { fond } : {}), ...(encre ? { encre } : {}) }; }
}
const face = (nom: string, fond: string, calques: Calque[], zonesInterdites: Face['zonesInterdites'] = []): Face => ({ nom, genre: 'art', fond: { couleur: fond }, calques, zonesInterdites });
const lignes = (...l: string[]) => l.join('\n');
const contactBloc = (v: Variables) => lignes('{{telephone}}', '{{courriel}}', '{{web}}', '{{adresse}}');

// ---------- cartes d'affaires 88,9 × 50,8 mm ----------
const carteAplat: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit), c = kit.couleurs, W = f.largeur, H = f.hauteur, fp = 3.175, surP = texteSur(c.primaire, kit);
  return [
    face('recto', c.primaire, [
      o.forme(-fp, H - 9, W + 2 * fp, 9 + fp, c.accent),
      o.logo(7, 7, 38, 15, 'clair'),
      o.txt('{{accroche}}', 7, 24, W - 14, 12, { police: 'titre', taille: 9, couleur: surP, interligne: 1.25, valign: 'top' }, 'accroche'),
    ]),
    face('verso', c.papier, [
      o.forme(W - 6, -fp, 6 + fp, H + 2 * fp, c.primaire),
      o.txt('{{nom}}', 7, 7, W - 22, 8, { police: 'titre', poids: 700, taille: 13, couleur: c.encre }, 'nom'),
      o.txt('{{titre}}', 7, 15.5, W - 22, 5, { poids: 600, taille: 7, couleur: c.primaire, casse: 'majuscules', crenage: 0.08 }, 'titre'),
      o.forme(7, 22.5, 12, 0.5, c.accent),
      o.txt(contactBloc(v), 7, 26, W - 22, H - 26 - 6, { taille: 7.5, couleur: c.encre, interligne: 1.45, valign: 'bottom' }, 'coordonnees'),
    ]),
  ];
};
const carteFilet: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit), c = kit.couleurs, W = f.largeur, H = f.hauteur;
  return [
    face('recto', c.papier, [
      o.txt('{{entreprise}}', 7, 8, W - 14, 18, { police: 'titre', poids: 700, taille: 17, couleur: c.encre, interligne: 1.05, valign: 'bottom' }, 'entreprise'),
      o.forme(7, 29, W - 14, 0.35, c.accent),
      o.txt('{{accroche}}', 7, 32, W - 14, 10, { taille: 8, couleur: c.primaire, interligne: 1.3 }, 'accroche'),
    ]),
    face('verso', c.encre, [
      o.logo(W - 7 - 24, 7, 24, 9, 'clair'),
      o.txt('{{nom}}', 7, 7, 50, 7, { police: 'titre', poids: 700, taille: 12, couleur: c.papier }, 'nom'),
      o.txt('{{titre}}', 7, 14.5, 50, 5, { taille: 7, couleur: c.accent, poids: 600, casse: 'majuscules', crenage: 0.08 }, 'titre'),
      o.txt(contactBloc(v), 7, 24, W - 14, H - 24 - 6, { taille: 7.5, couleur: c.papier, interligne: 1.45, valign: 'bottom' }, 'coordonnees'),
    ]),
  ];
};
const carteBloc: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit), c = kit.couleurs, W = f.largeur, H = f.hauteur, fp = 3.175, bloc = W * 0.38, surP = texteSur(c.primaire, kit);
  const droite = bloc + 6;
  return [
    face('recto', c.papier, [
      o.forme(-fp, -fp, bloc + fp, H + 2 * fp, c.primaire),
      o.logo(6, H / 2 - 9, bloc - 12, 18, 'clair'),
      o.txt('{{entreprise}}', droite, 8, W - droite - 7, 16, { police: 'titre', poids: 700, taille: 12, couleur: c.encre, interligne: 1.1, valign: 'bottom' }, 'entreprise'),
      o.forme(droite, 26, 10, 0.5, c.accent),
      o.txt('{{accroche}}', droite, 29, W - droite - 7, 14, { taille: 7.5, couleur: c.encre, interligne: 1.3 }, 'accroche'),
    ]),
    face('verso', c.secondaire, [
      ...(v.url ? [o.qr(7, 7, 22, v.url, c.papier, c.encre)] : []),
      o.txt('{{nom}}', v.url ? 34 : 7, 7, W - 41, 7, { police: 'titre', poids: 700, taille: 11.5, couleur: c.encre }, 'nom'),
      o.txt('{{titre}}', v.url ? 34 : 7, 14.2, W - 41, 5, { taille: 6.8, poids: 600, couleur: texteSur(c.secondaire, kit) === c.encre ? c.primaire : c.encre, casse: 'majuscules', crenage: 0.08 }, 'titre'),
      o.txt(contactBloc(v), 7, 28.5, W - 14, H - 28.5 - 6, { taille: 7.5, couleur: c.encre, interligne: 1.45, valign: 'bottom' }, 'coordonnees'),
      ...(surP ? [] : []),
    ]),
  ];
};

// ---------- dépliants Lettre / A5 / affiche (coordonnées en espace Lettre, mises à l'échelle) ----------
const LW = 215.9, LH = 279.4;
const flyerBandeau: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit, f.largeur / LW, f.hauteur / LH), c = kit.couleurs, fp = 3.175 / o.sx, surP = texteSur(c.primaire, kit), surA = texteSur(c.accent, kit);
  const pts = [v.point1, v.point2, v.point3].filter(Boolean).length;
  return [face('recto', c.papier, [
    o.forme(-fp, -fp, LW + 2 * fp, 126 + fp, c.primaire),
    o.logo(16, 14, 52, 17, 'clair'),
    o.txt('{{accroche}}', 16, 38, LW - 32, 82, { police: 'titre', poids: 700, taille: 46, couleur: surP, interligne: 1.02, valign: 'bottom', crenage: -0.01 }, 'accroche'),
    o.txt('{{sousTitre}}', 16, 136, LW - 32, 28, { taille: 16, couleur: c.encre, interligne: 1.3 }, 'sous-titre'),
    ...(pts ? [o.forme(16, 169, 1.6, pts * 10.2 + 1, c.accent), o.txt(lignes('{{point1}}', '{{point2}}', '{{point3}}'), 24, 168, LW - 40, 14 * pts + 4, { taille: 14, couleur: c.encre, interligne: 2.05, poids: 600 }, 'points')] : []),
    o.forme(-fp, LH - 44, LW + 2 * fp, 44 + fp, c.accent),
    o.txt('{{appel}}', 16, LH - 38, 100, 24, { police: 'titre', poids: 700, taille: 22, couleur: surA, interligne: 1.1, valign: 'middle' }, 'appel'),
    o.txt(contactBloc(v), 122, LH - 40, LW - 122 - 16, 28, { taille: 10.5, couleur: surA, interligne: 1.35, align: 'right', valign: 'middle' }, 'coordonnees'),
  ])];
};
const flyerSombre: Gabarit['construire'] = (kit, v, f, opt) => {
  const o = new Outils(kit, f.largeur / LW, f.hauteur / LH), c = kit.couleurs, surA = texteSur(c.accent, kit);
  const pts = [v.point1, v.point2, v.point3].filter(Boolean).length;
  return [face('recto', c.encre, [
    ...(opt?.image ? [{ type: 'image' as const, id: 'image', x: -3.175 * 2, y: LH * 0.52 * o.sy, l: f.largeur + 3.175 * 4, h: LH * 0.48 * o.sy + 3.175 * 2, src: opt.image.src, ajustement: 'cover' as const, pxLargeur: opt.image.pxLargeur, pxHauteur: opt.image.pxHauteur, opacite: 0.55 }] : []),
    o.logo(16, 16, 50, 16, 'clair'),
    o.txt('{{accroche}}', 16, 48, 140, 96, { police: 'titre', poids: 700, taille: 50, couleur: c.papier, interligne: 1.0, crenage: -0.015 }, 'accroche'),
    o.txt('{{sousTitre}}', 16, 152, 118, 36, { taille: 15, couleur: c.papier, interligne: 1.3 }, 'sous-titre'),
    ...(v.offre ? [{ ...o.forme(140, 138, 56, 56, c.accent, { forme: 'cercle' }) }, o.txt('{{offre}}', 146, 144, 44, 44, { police: 'titre', poids: 700, taille: 15, couleur: surA, align: 'center', valign: 'middle', interligne: 1.1 }, 'offre')] : []),
    ...(pts ? [o.txt(lignes('{{point1}}', '{{point2}}', '{{point3}}'), 16, 196, LW - 32, 14 * pts + 4, { taille: 13, couleur: c.papier, interligne: 1.9, poids: 600 }, 'points')] : []),
    o.forme(16, LH - 38, LW - 32, 0.4, c.accent),
    o.txt('{{appel}}', 16, LH - 33, 100, 20, { police: 'titre', poids: 700, taille: 17, couleur: c.accent, valign: 'middle' }, 'appel'),
    o.txt(contactBloc(v), 116, LH - 34, LW - 116 - 16, 24, { taille: 10, couleur: c.papier, interligne: 1.35, align: 'right', valign: 'middle' }, 'coordonnees'),
  ])];
};
const flyerEditorial: Gabarit['construire'] = (kit, v, f, opt) => {
  const o = new Outils(kit, f.largeur / LW, f.hauteur / LH), c = kit.couleurs, fp = 3.175 / o.sx;
  const pts = [v.point1, v.point2, v.point3].filter(Boolean);
  const bloc = opt?.image
    ? { type: 'image' as const, id: 'image', x: -fp * o.sx, y: 136 * o.sy, l: f.largeur + 2 * fp * o.sx, h: 84 * o.sy, src: opt.image.src, ajustement: 'cover' as const, pxLargeur: opt.image.pxLargeur, pxHauteur: opt.image.pxHauteur, opacite: 1 }
    : o.forme(-fp, 136, LW + 2 * fp, 84, c.secondaire);
  return [face('recto', c.papier, [
    o.txt('{{entreprise}}', 16, 16, 120, 8, { poids: 700, taille: 10, couleur: c.primaire, casse: 'majuscules', crenage: 0.18 }, 'entreprise'),
    o.forme(16, 27, 30, 0.8, c.accent),
    o.txt('{{accroche}}', 16, 38, LW - 32, 70, { police: 'titre', poids: 700, taille: 40, couleur: c.encre, interligne: 1.06 }, 'accroche'),
    o.txt('{{sousTitre}}', 16, 100, 150, 30, { taille: 14, couleur: c.encre, interligne: 1.4 }, 'sous-titre'),
    bloc,
    ...(opt?.image ? [] : [o.forme(130, 150, 56, 56, c.primaire, { forme: 'cercle' }), o.forme(108, 180, 36, 36, c.accent, { forme: 'cercle', opacite: 0.9 })]),
    ...pts.map((p, i) => o.txt(`0${i + 1}`, 16 + i * 62, 226, 14, 8, { police: 'titre', poids: 700, taille: 12, couleur: c.primaire }, `num${i + 1}`)),
    ...pts.map((_, i) => o.txt(`{{point${i + 1}}}`, 16 + i * 62, 235, 54, 22, { taille: 10.5, couleur: c.encre, interligne: 1.3 }, `point${i + 1}`)),
    o.forme(16, LH - 32, LW - 32, 0.3, c.encre, { opacite: 0.35 }),
    o.txt(lignes('{{telephone}}', '{{courriel}}', '{{web}}'), 16, LH - 28, 120, 16, { taille: 9.5, couleur: c.encre, interligne: 1.35 }, 'coordonnees'),
    ...(v.url ? [o.qr(LW - 16 - 17, LH - 29, 17, v.url)] : []),
  ])];
};

// ---------- accroche-portes 88,9 × 215,9 mm ----------
const D_TROU = 38.1, CX = 44.45, CY = 20;
const trou: Face['zonesInterdites'] = [[CX - D_TROU / 2 - 2, CY - D_TROU / 2 - 2, D_TROU + 4, D_TROU + 4], [CX, CY - 3, 50, 6]];
const faceDecoupe = (kit: KitMarque, f: FormatPiece): Face => {
  const o = new Outils(kit), W = f.largeur, H = f.hauteur, mag = '#E6007E';
  return { nom: 'découpe', genre: 'decoupe', fond: { couleur: '#FFFFFF' }, zonesInterdites: [], calques: [
    o.forme(0, 0, W, H, '#FFFFFF', { remplissage: undefined, contour: mag, epaisseur: 0.25 }),
    { type: 'forme', id: 'trou', x: CX - D_TROU / 2, y: CY - D_TROU / 2, l: D_TROU, h: D_TROU, forme: 'cercle', contour: mag, epaisseur: 0.25, rayon: 0, opacite: 1, decoupe: true },
    { type: 'forme', id: 'fente', x: CX, y: CY - 1.5, l: W - CX, h: 3, forme: 'rect', contour: mag, epaisseur: 0.25, rayon: 0, opacite: 1, decoupe: true },
    o.txt('Gabarit de découpe : trou Ø 38,1 mm (1,5 po) et fente, en couleur d’accompagnement « DIECUT » (magenta 100 %), sans impression. Ne pas imprimer cette page en couleur.', 6, 60, W - 12, 40, { taille: 7, couleur: '#14181B', interligne: 1.4 }, 'note'),
  ] };
};
const accrocheBande: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit), c = kit.couleurs, W = f.largeur, H = f.hauteur, fp = 3.175, surP = texteSur(c.primaire, kit), surA = texteSur(c.accent, kit);
  const pts = [v.point1, v.point2, v.point3].filter(Boolean).length;
  return [
    face('recto', c.primaire, [
      o.txt('{{accroche}}', 8, 52, W - 16, 78, { police: 'titre', poids: 700, taille: 27, couleur: surP, interligne: 1.05, valign: 'top' }, 'accroche'),
      o.forme(-fp, 138, W + 2 * fp, 36, c.accent),
      o.txt('{{appel}}', 8, 140, W - 16, 32, { police: 'titre', poids: 700, taille: 14, couleur: surA, valign: 'middle', interligne: 1.15 }, 'appel'),
      o.logo(8, H - 24, 44, 14, 'clair'),
    ], trou),
    face('verso', c.papier, [
      o.txt('{{sousTitre}}', 8, 52, W - 16, 38, { police: 'titre', poids: 700, taille: 15, couleur: c.encre, interligne: 1.2 }, 'sous-titre'),
      ...(pts ? [o.forme(8, 96, 1.2, 6 + pts * 14, c.accent), o.txt(lignes('{{point1}}', '{{point2}}', '{{point3}}'), 13, 95, W - 21, 14 * pts + 4, { taille: 10, couleur: c.encre, interligne: 1.8, poids: 600 }, 'points')] : []),
      ...(v.url ? [o.qr(W - 8 - 22, H - 12 - 22 - 24, 22, v.url)] : []),
      o.forme(-fp, H - 36, W + 2 * fp, 36 + fp, c.primaire),
      o.txt(contactBloc(v), 8, H - 33, W - 16, 28, { taille: 8.5, couleur: surP, interligne: 1.4, valign: 'middle' }, 'coordonnees'),
    ], trou), faceDecoupe(kit, f),
  ];
};
const accrocheSobre: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit), c = kit.couleurs, W = f.largeur, H = f.hauteur, fp = 3.175;
  return [
    face('recto', c.papier, [
      o.forme(-fp, -fp, W + 2 * fp, 46 + fp, c.encre),
      o.txt('{{accroche}}', 8, 56, W - 16, 70, { police: 'titre', poids: 700, taille: 23, couleur: c.encre, interligne: 1.08 }, 'accroche'),
      o.forme(8, 132, 14, 0.8, c.accent),
      o.txt('{{sousTitre}}', 8, 138, W - 16, 40, { taille: 10.5, couleur: c.encre, interligne: 1.4 }, 'sous-titre'),
      o.logo(8, H - 22, 40, 12, 'original'),
    ], trou),
    face('verso', c.encre, [
      o.txt('{{appel}}', 8, 52, W - 16, 40, { police: 'titre', poids: 700, taille: 20, couleur: c.accent, interligne: 1.1 }, 'appel'),
      o.txt(lignes('{{point1}}', '{{point2}}', '{{point3}}'), 8, 98, W - 16, 56, { taille: 10, couleur: c.papier, interligne: 1.8 }, 'points'),
      o.txt(contactBloc(v), 8, H - 46, W - 16, 38, { taille: 8.5, couleur: c.papier, interligne: 1.45, valign: 'bottom' }, 'coordonnees'),
    ], trou), faceDecoupe(kit, f),
  ];
};
const accrocheArche: Gabarit['construire'] = (kit, v, f) => {
  const o = new Outils(kit), c = kit.couleurs, W = f.largeur, H = f.hauteur, surA = texteSur(c.accent, kit);
  return [
    face('recto', c.accent, [
      { ...o.forme(-20, 150, 130, 130, c.primaire, { forme: 'cercle' }) },
      o.txt('{{accroche}}', 8, 52, W - 16, 78, { police: 'titre', poids: 700, taille: 28, couleur: surA, interligne: 1.04 }, 'accroche'),
      o.txt('{{sousTitre}}', 8, 132, W - 16, 22, { taille: 9.5, couleur: surA, interligne: 1.35 }, 'sous-titre'),
      o.logo(10, H - 40, 44, 14, 'clair'),
    ], trou),
    face('verso', c.encre, [
      o.txt('{{appel}}', 8, 52, W - 16, 40, { police: 'titre', poids: 700, taille: 19, couleur: c.papier, interligne: 1.12 }, 'appel'),
      o.forme(8, 96, 14, 0.8, c.accent),
      o.txt(lignes('{{point1}}', '{{point2}}', '{{point3}}'), 8, 102, W - 16, 56, { taille: 10, couleur: c.papier, interligne: 1.8 }, 'points'),
      ...(v.url ? [o.qr(8, H - 80, 24, v.url)] : []),
      o.txt(contactBloc(v), 8, H - 50, W - 16, 40, { taille: 8.5, couleur: c.papier, interligne: 1.45, valign: 'bottom' }, 'coordonnees'),
    ], trou), faceDecoupe(kit, f),
  ];
};

const FLYERS = ['flyer-lettre', 'flyer-a5', 'affiche-18x24'];
export const GABARITS: Gabarit[] = [
  { id: 'carte-aplat', nom: 'Aplat', description: 'Recto couleur de marque avec logo et accroche ; verso clair avec bande latérale.', formats: ['carte-affaires'], construire: carteAplat },
  { id: 'carte-filet', nom: 'Filet', description: 'Recto typographique sobre, verso sombre avec coordonnées et logo.', formats: ['carte-affaires'], construire: carteFilet },
  { id: 'carte-bloc', nom: 'Bloc', description: 'Bloc de couleur avec logo, verso avec code QR vers le site.', formats: ['carte-affaires'], construire: carteBloc },
  { id: 'flyer-bandeau', nom: 'Bandeau', description: 'Grand bandeau de marque, accroche forte, trois points, appel à l’action en pied.', formats: FLYERS, construire: flyerBandeau },
  { id: 'flyer-sombre', nom: 'Plein sombre', description: 'Fond sombre, titre géant, pastille d’offre, image optionnelle.', formats: FLYERS, construire: flyerSombre },
  { id: 'flyer-editorial', nom: 'Éditorial', description: 'Mise en page de magazine : titre serif, trois points numérotés, code QR.', formats: FLYERS, construire: flyerEditorial },
  { id: 'accroche-bande', nom: 'Bande', description: 'Recto couleur de marque et bande d’appel ; verso avec points et code QR.', formats: ['accroche-porte'], construire: accrocheBande },
  { id: 'accroche-sobre', nom: 'Sobre', description: 'Haut sombre, titre lisible, verso sombre ; logo en couleur.', formats: ['accroche-porte'], construire: accrocheSobre },
  { id: 'accroche-arche', nom: 'Arche', description: 'Recto couleur d’accent avec grand disque de marque ; verso sombre.', formats: ['accroche-porte'], construire: accrocheArche },
];
export const gabaritParId = (id: string) => GABARITS.find((g) => g.id === id);
export const gabaritsPour = (format: string) => GABARITS.filter((g) => g.formats.includes(format));

/** Construit une spec complète à partir d'un gabarit, du kit et des variables. */
export function construireSpec(gabaritId: string, formatId: string, kit: KitMarque, texte: Partial<Variables> = {}, opt?: OptionsGabarit): SpecConception {
  const g = gabaritParId(gabaritId), f = FORMATS[formatId];
  if (!g) throw new Error(`Gabarit inconnu : ${gabaritId}`);
  if (!f || !g.formats.includes(formatId)) throw new Error(`Le gabarit ${gabaritId} ne s’applique pas au format ${formatId}.`);
  const v = variablesPour(kit, texte);
  return { version: 1, format: formatId, fondPerdu: f.fondPerdu, securite: f.securite, gabarit: g.id, variables: Object.fromEntries(Object.entries(v).filter(([, x]) => x !== '')), faces: g.construire(kit, v, f, opt) };
}
export { po, contactsActifs };
