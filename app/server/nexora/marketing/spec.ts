/**
 * SpecConception v1 (vague 2, #15) : une pièce imprimée décrite en JSON typé. Le LLM choisit un gabarit et des valeurs ;
 * le code garantit le fond perdu, la zone de sécurité, le contraste et la conformité. Dimensions en millimètres, origine
 * en haut à gauche de la zone de coupe (fini). Module pur : le rendu (Playwright) est dans rendu.ts.
 */
import { z } from 'zod';
import { contraste, hex, IDS_POLICES } from './kit.js';

export const MM_PAR_PO = 25.4;
export const po = (n: number) => Math.round(n * MM_PAR_PO * 1000) / 1000;

export interface FormatPiece { id: string; nom: string; largeur: number; hauteur: number; fondPerdu: number; securite: number; faces: number; type: 'carte' | 'flyer' | 'accroche-porte' | 'affiche' | 'brochure' | 'logo' }
/** Formats v1. Fond perdu 0,125 po (3,175 mm), sécurité 0,125 po, sauf affiche (0,25 po) et formats métriques (3 mm). */
export const FORMATS: Record<string, FormatPiece> = {
  'carte-affaires': { id: 'carte-affaires', nom: 'Carte d’affaires 3,5 × 2 po', largeur: po(3.5), hauteur: po(2), fondPerdu: po(0.125), securite: po(0.125), faces: 2, type: 'carte' },
  'flyer-lettre': { id: 'flyer-lettre', nom: 'Dépliant Lettre 8,5 × 11 po', largeur: po(8.5), hauteur: po(11), fondPerdu: po(0.125), securite: po(0.25), faces: 1, type: 'flyer' },
  'flyer-a5': { id: 'flyer-a5', nom: 'Dépliant A5 148 × 210 mm', largeur: 148, hauteur: 210, fondPerdu: 3, securite: 6, faces: 1, type: 'flyer' },
  'accroche-porte': { id: 'accroche-porte', nom: 'Accroche-porte 3,5 × 8,5 po', largeur: po(3.5), hauteur: po(8.5), fondPerdu: po(0.125), securite: po(0.125), faces: 2, type: 'accroche-porte' },
  'affiche-18x24': { id: 'affiche-18x24', nom: 'Affiche 18 × 24 po', largeur: po(18), hauteur: po(24), fondPerdu: po(0.25), securite: po(0.5), faces: 1, type: 'affiche' },
  'brochure-dl': { id: 'brochure-dl', nom: 'Brochure DL 99 × 210 mm', largeur: 99, hauteur: 210, fondPerdu: 3, securite: 5, faces: 1, type: 'brochure' },
  'planche-logo': { id: 'planche-logo', nom: 'Planche de logo Lettre', largeur: po(8.5), hauteur: po(11), fondPerdu: 0, securite: po(0.5), faces: 1, type: 'logo' },
};
export const IDS_FORMATS = Object.keys(FORMATS) as [string, ...string[]];

/** Marge de légende au-delà du fond perdu pour les traits de coupe (mm). */
export const MARGE_TRAITS = 9;

export interface Boites { page: { l: number; h: number }; coupe: { x: number; y: number; l: number; h: number }; fondPerdu: { x: number; y: number; l: number; h: number }; securite: { x: number; y: number; l: number; h: number } }
/** Géométrie d'une page de PDF : avec traits, la page est agrandie d'une marge de légende ; sans, elle s'arrête au fond perdu. */
export function boites(f: { largeur: number; hauteur: number }, fondPerdu: number, securite: number, traits: boolean): Boites {
  const s = fondPerdu + (traits ? MARGE_TRAITS : 0);
  const r = (n: number) => Math.round(n * 1000) / 1000;
  return {
    page: { l: r(f.largeur + 2 * s), h: r(f.hauteur + 2 * s) },
    coupe: { x: r(s), y: r(s), l: f.largeur, h: f.hauteur },
    fondPerdu: { x: r(s - fondPerdu), y: r(s - fondPerdu), l: r(f.largeur + 2 * fondPerdu), h: r(f.hauteur + 2 * fondPerdu) },
    securite: { x: r(s + securite), y: r(s + securite), l: r(f.largeur - 2 * securite), h: r(f.hauteur - 2 * securite) },
  };
}
export const mmVersPt = (mm: number) => (mm / MM_PAR_PO) * 72;
export const dpiEffectif = (pxLargeur: number, largeurMm: number) => Math.round(pxLargeur / (largeurMm / MM_PAR_PO));

const nb = z.number().finite();
const base = { id: z.string().min(1).max(40), x: nb, y: nb, l: nb.positive(), h: nb.positive() };

export const CalqueSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('texte'), ...base,
    /** Texte avec variables {{nom}} ; une variable vide fait disparaître le calque (aucun trou, aucune ligne fantôme). */
    texte: z.string().max(1200),
    police: z.enum(IDS_POLICES), poids: z.union([z.literal(400), z.literal(600), z.literal(700)]).default(400),
    taille: nb.min(4).max(400), couleur: hex, align: z.enum(['left', 'center', 'right']).default('left'),
    interligne: nb.min(0.8).max(2.4).default(1.2), crenage: nb.min(-0.1).max(0.5).default(0), casse: z.enum(['aucune', 'majuscules']).default('aucune'),
    /** Réduit la taille jusqu'à ce que le texte tienne dans la boîte (jamais sous 60 %). */
    ajuster: z.boolean().default(true), valign: z.enum(['top', 'middle', 'bottom']).default('top'),
  }),
  z.object({ type: z.literal('image'), ...base, src: z.string().max(12_000_000), ajustement: z.enum(['cover', 'contain']).default('cover'), pxLargeur: z.number().int().positive().optional(), pxHauteur: z.number().int().positive().optional(), opacite: nb.min(0).max(1).default(1) }),
  z.object({ type: z.literal('forme'), ...base, forme: z.enum(['rect', 'cercle']).default('rect'), remplissage: hex.optional(), contour: hex.optional(), epaisseur: nb.min(0).max(5).default(0.25), rayon: nb.min(0).default(0), opacite: nb.min(0).max(1).default(1), decoupe: z.boolean().default(false) }),
  z.object({ type: z.literal('logo'), ...base, variante: z.enum(['original', 'clair', 'sombre']).default('original') }),
  z.object({ type: z.literal('qr'), ...base, url: z.string().max(300), fond: hex.optional(), encre: hex.optional() }),
]);
export type Calque = z.infer<typeof CalqueSchema>;
export type CalqueTexte = Extract<Calque, { type: 'texte' }>;

export const FaceSchema = z.object({
  nom: z.string().max(30),
  /** `decoupe` : face technique (gabarit de découpe en couleur d'accompagnement), exclue des aperçus. */
  genre: z.enum(['art', 'decoupe']).default('art'),
  fond: z.object({ couleur: hex, degrade: z.object({ vers: hex, angle: nb.default(180) }).optional() }),
  calques: z.array(CalqueSchema).max(60),
  /** Zones où aucun texte ne doit tomber (trou de poignée) : [x, y, l, h] en mm. */
  zonesInterdites: z.array(z.tuple([nb, nb, nb.positive(), nb.positive()])).max(8).default([]),
});
export type Face = z.infer<typeof FaceSchema>;

export const SpecConceptionSchema = z.object({
  version: z.literal(1),
  format: z.enum(IDS_FORMATS),
  fondPerdu: nb.min(0).max(12),
  securite: nb.min(0).max(30),
  gabarit: z.string().max(60),
  variables: z.record(z.string().max(40), z.string().max(400)).default({}),
  faces: z.array(FaceSchema).min(1).max(3),
});
export type SpecConception = z.infer<typeof SpecConceptionSchema>;

/** Lit et valide une spec reçue du réseau ; les erreurs sont lisibles. */
export function lireSpec(b: unknown): SpecConception {
  const r = SpecConceptionSchema.safeParse(b);
  if (!r.success) throw new Error('Spec de conception invalide : ' + r.error.issues.slice(0, 3).map((i) => `${i.path.join('.')} ${i.message}`).join(' ; '));
  return r.data;
}

// ---- variables et disparition des champs vides ----
const reVar = /\{\{\s*([\w-]+)\s*\}\}/g;
/**
 * Remplace les {{variables}}. Un calque de texte dont une variable est vide (ou dont le texte résolu est vide) est retiré.
 * Les lignes d'un texte multiligne dont la variable est vide sont retirées une à une.
 */
export function resoudre(spec: SpecConception, extra: Record<string, string> = {}): SpecConception {
  const vars = { ...spec.variables, ...extra };
  const plein = (v?: string) => !!v && !/^\s*$/.test(v) && !/^[«<\[]\s*à compl/i.test(v);
  const faces = spec.faces.map((f) => ({
    ...f,
    calques: f.calques.flatMap((c): Calque[] => {
      if (c.type === 'qr') return plein(c.url.replace(reVar, (_, k) => vars[k] ?? '')) ? [{ ...c, url: c.url.replace(reVar, (_, k) => vars[k] ?? '') }] : [];
      if (c.type !== 'texte') return [c];
      const lignes = c.texte.split('\n').filter((l) => {
        const noms = [...l.matchAll(reVar)].map((m) => m[1]);
        return noms.every((n) => plein(vars[n])) && (noms.length > 0 || l.trim() !== '');
      }).map((l) => l.replace(reVar, (_, k) => vars[k].trim()));
      return lignes.length ? [{ ...c, texte: lignes.join('\n') }] : [];
    }),
  }));
  return { ...spec, faces };
}

// ---- contrôle préliminaire ----
export interface Mesure { face: number; id: string; x: number; y: number; l: number; h: number; taillePt?: number; debordeBoite?: boolean }
export type Gravite = 'erreur' | 'avertissement' | 'info';
export interface Constat { gravite: Gravite; code: 'resolution' | 'zone-securite' | 'fond-perdu' | 'contraste' | 'texte-petit' | 'zone-interdite' | 'debordement' | 'cmjn' | 'police'; face: number; calque?: string; message: string }
export interface Controle { ok: boolean; erreurs: number; avertissements: number; constats: Constat[] }

const dans = (m: { x: number; y: number; l: number; h: number }, z: { x: number; y: number; l: number; h: number }, tol = 0.05) =>
  m.x >= z.x - tol && m.y >= z.y - tol && m.x + m.l <= z.x + z.l + tol && m.y + m.h <= z.y + z.h + tol;
const inter = (a: { x: number; y: number; l: number; h: number }, b: { x: number; y: number; l: number; h: number }) =>
  a.x < b.x + b.l && a.x + a.l > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

/** Fond sous un point : la dernière forme pleine qui le contient, sinon le fond de la face. */
export function fondSousPoint(face: Face, px: number, py: number): string {
  for (const c of [...face.calques].reverse()) {
    if (c.type === 'forme' && c.remplissage && !c.decoupe && c.opacite >= 0.9 && px >= c.x && px <= c.x + c.l && py >= c.y && py <= c.y + c.h) return c.remplissage;
  }
  return face.fond.couleur;
}

/**
 * Contrôle préliminaire (pur) : résolution des images, texte hors zone de sécurité ou dans une zone interdite, fond perdu
 * manquant, contraste (AA), texte trop petit. `mesures` vient du rendu réel (boîtes du texte mesurées dans Chromium).
 */
export function controler(spec: SpecConception, mesures: Mesure[] = [], o: { cmjn?: boolean; cmjnDisponible?: boolean } = {}): Controle {
  const f = FORMATS[spec.format];
  const constats: Constat[] = [];
  const add = (c: Constat) => constats.push(c);
  const sec = { x: spec.securite, y: spec.securite, l: f.largeur - 2 * spec.securite, h: f.hauteur - 2 * spec.securite };
  spec.faces.forEach((face, i) => {
    if (face.genre === 'decoupe') return;
    for (const c of face.calques) {
      if (c.type === 'image') {
        const dpi = c.pxLargeur ? dpiEffectif(c.pxLargeur, c.l) : null;
        if (dpi !== null && dpi < 150) add({ gravite: 'erreur', code: 'resolution', face: i, calque: c.id, message: `Image « ${c.id} » à ${dpi} dpi : trop floue pour l’impression (150 minimum, 300 visé).` });
        else if (dpi !== null && dpi < 300) add({ gravite: 'avertissement', code: 'resolution', face: i, calque: c.id, message: `Image « ${c.id} » à ${dpi} dpi : sous 300 dpi (acceptable pour une grande affiche vue de loin).` });
      }
      if ((c.type === 'forme' || c.type === 'image') && !(c.type === 'forme' && (c.decoupe || !c.remplissage))) {
        const b = spec.fondPerdu;
        const touche = (v: number, bord: number) => Math.abs(v - bord) < 0.5;
        const manque = (touche(c.x, 0) && c.x > -b + 0.01) || (touche(c.y, 0) && c.y > -b + 0.01) || (touche(c.x + c.l, f.largeur) && c.x + c.l < f.largeur + b - 0.01) || (touche(c.y + c.h, f.hauteur) && c.y + c.h < f.hauteur + b - 0.01);
        if (manque && b > 0) add({ gravite: 'erreur', code: 'fond-perdu', face: i, calque: c.id, message: `« ${c.id} » touche le bord de la coupe sans déborder dans le fond perdu (${b} mm) : un liseré blanc peut apparaître à la coupe.` });
      }
      if (c.type === 'texte') {
        if (c.taille < 6) add({ gravite: 'avertissement', code: 'texte-petit', face: i, calque: c.id, message: `Texte « ${c.id} » à ${c.taille} pt : illisible en dessous de 6 pt.` });
        const fond = fondSousPoint(face, c.x + c.l / 2, c.y + c.h / 2), r = contraste(c.couleur, fond);
        const grand = c.taille >= 18 || (c.taille >= 14 && c.poids >= 600);
        if (r < (grand ? 3 : 4.5)) add({ gravite: r < 3 ? 'erreur' : 'avertissement', code: 'contraste', face: i, calque: c.id, message: `Contraste ${r.toFixed(1)}:1 pour « ${c.id} » (${grand ? 3 : 4.5}:1 requis, norme AA).` });
      }
    }
    for (const m of mesures.filter((m) => m.face === i)) {
      if (!dans(m, sec)) add({ gravite: 'erreur', code: 'zone-securite', face: i, calque: m.id, message: `Texte « ${m.id} » hors de la zone de sécurité (${spec.securite} mm du bord) : risque de coupe.` });
      for (const z of face.zonesInterdites) if (inter(m, { x: z[0], y: z[1], l: z[2], h: z[3] })) add({ gravite: 'erreur', code: 'zone-interdite', face: i, calque: m.id, message: `Texte « ${m.id} » sur la découpe de la poignée.` });
      if (m.debordeBoite) add({ gravite: 'avertissement', code: 'debordement', face: i, calque: m.id, message: `Le texte « ${m.id} » a dû être réduit à ${m.taillePt?.toFixed(1)} pt pour tenir : raccourcir le texte.` });
    }
  });
  if (o.cmjn && !o.cmjnDisponible) add({ gravite: 'info', code: 'cmjn', face: 0, message: 'Conversion CMJN indisponible sur ce serveur (Ghostscript absent) : PDF en RVB. Demander une épreuve à l’imprimeur.' });
  else if (o.cmjn) add({ gravite: 'info', code: 'cmjn', face: 0, message: 'PDF converti en CMJN par Ghostscript (profil par défaut, sans PDF/X certifié) : les couleurs vives (orange, vert) peuvent ternir ; épreuve conseillée.' });
  else add({ gravite: 'info', code: 'cmjn', face: 0, message: 'PDF en RVB : l’imprimeur le convertira ; demander une épreuve pour les couleurs vives.' });
  const erreurs = constats.filter((c) => c.gravite === 'erreur').length, avertissements = constats.filter((c) => c.gravite === 'avertissement').length;
  return { ok: erreurs === 0, erreurs, avertissements, constats };
}

/** Polices utilisées par une spec (pour ne charger que celles-là dans le PDF). */
export const policesUtilisees = (s: SpecConception) => [...new Set(s.faces.flatMap((f) => f.calques.flatMap((c) => (c.type === 'texte' ? [c.police] : []))))];
