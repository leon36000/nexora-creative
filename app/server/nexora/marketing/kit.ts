/**
 * Kit de marque (vague 2, #13) : nom, logo, couleurs, polices libres, ton, coordonnées. Un seul kit par organisation,
 * saisi une fois, qui alimente chaque sortie (imprimés, vidéos du Producteur, images). Module pur : aucune E/S.
 */
import { inflateSync } from 'node:zlib';
import { z } from 'zod';

export const hex = z.string().regex(/^#[0-9a-fA-F]{6}$/, 'couleur au format #RRGGBB').transform((s) => s.toUpperCase());

/** Polices à licence libre (OFL) que le moteur d'impression sait intégrer au PDF (fichiers @fontsource, poids 400/600/700). */
export const POLICES = [
  { id: 'geist', nom: 'Geist', famille: 'Geist', paquet: 'geist-sans', genre: 'sans' },
  { id: 'inter', nom: 'Inter', famille: 'Inter', paquet: 'inter', genre: 'sans' },
  { id: 'archivo', nom: 'Archivo', famille: 'Archivo', paquet: 'archivo', genre: 'sans' },
  { id: 'fraunces', nom: 'Fraunces', famille: 'Fraunces', paquet: 'fraunces', genre: 'serif' },
  { id: 'playfair', nom: 'Playfair Display', famille: 'Playfair Display', paquet: 'playfair-display', genre: 'serif' },
  { id: 'jetbrains', nom: 'JetBrains Mono', famille: 'JetBrains Mono', paquet: 'jetbrains-mono', genre: 'mono' },
] as const;
export type IdPolice = (typeof POLICES)[number]['id'];
export const IDS_POLICES = POLICES.map((p) => p.id) as [IdPolice, ...IdPolice[]];
export const policeParId = (id: string) => POLICES.find((p) => p.id === id) ?? POLICES[0];

const texteCourt = (n: number) => z.string().trim().max(n).default('');

export const ContactSchema = z.object({
  entreprise: texteCourt(80), nom: texteCourt(80), titre: texteCourt(80), adresse: texteCourt(160),
  telephone: texteCourt(40), courriel: texteCourt(120), web: texteCourt(120),
});
export type Contact = z.infer<typeof ContactSchema>;

export const KitMarqueSchema = z.object({
  nom: z.string().trim().min(1, 'Le nom de la marque est obligatoire').max(80),
  logo: z.object({
    /** SVG assaini (préféré) ou image PNG en data URL. */
    svg: z.string().max(400_000).optional(),
    png: z.string().max(3_000_000).regex(/^data:image\/png;base64,/).optional(),
    largeurPx: z.number().int().positive().optional(),
    hauteurPx: z.number().int().positive().optional(),
  }).default({}),
  couleurs: z.object({ primaire: hex, secondaire: hex, accent: hex, encre: hex, papier: hex }).default({ primaire: '#1F4E5F', secondaire: '#E8EEF0', accent: '#E07A2F', encre: '#14181B', papier: '#FBFAF7' }),
  polices: z.object({ titre: z.enum(IDS_POLICES), texte: z.enum(IDS_POLICES) }).default({ titre: 'fraunces', texte: 'inter' }),
  ton: z.object({ adjectifs: z.array(z.string().trim().max(30)).max(3).default([]), interdits: z.array(z.string().trim().max(40)).max(20).default([]) }).default({ adjectifs: [], interdits: [] }),
  contact: ContactSchema.default({ entreprise: '', nom: '', titre: '', adresse: '', telephone: '', courriel: '', web: '' }),
  langue: z.enum(['fr', 'en']).default('fr'),
});
export type KitMarque = z.infer<typeof KitMarqueSchema>;

/** Valeurs de remplissage qui valent « vide » (comme les marqueurs de `coordonnees.json`). */
export const estVide = (v: string | undefined | null) => !v || /^\s*$/.test(v) || /^[«<\[]\s*à compl[ée]ter/i.test(v.trim()) || /^(todo|n\/a|-+)$/i.test(v.trim());

/** Coordonnées réellement remplies, dans l'ordre d'affichage : les champs vides disparaissent sans laisser de trou. */
export function contactsActifs(c: Partial<Contact>, langue: 'fr' | 'en' = 'fr'): { cle: keyof Contact; libelle: string; valeur: string }[] {
  const lib = langue === 'en' ? { telephone: 'Tel.', courriel: 'Email', web: 'Web', adresse: 'Address' } : { telephone: 'Tél.', courriel: 'Courriel', web: 'Web', adresse: 'Adresse' };
  return (['telephone', 'courriel', 'web', 'adresse'] as const).filter((k) => !estVide(c[k])).map((k) => ({ cle: k, libelle: lib[k], valeur: String(c[k]).trim() }));
}

// ---- couleurs et contraste (WCAG 2.x) ----
export function rgb(h: string): [number, number, number] {
  const v = h.replace('#', '');
  return [0, 2, 4].map((i) => parseInt(v.slice(i, i + 2), 16)) as [number, number, number];
}
export function luminance(h: string): number {
  const [r, g, b] = rgb(h).map((c) => { const s = c / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
export function contraste(a: string, b: string): number {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
/** Couleur de texte lisible sur un fond : l'encre ou le papier du kit, la mieux contrastée. */
export const texteSur = (fond: string, kit: Pick<KitMarque, 'couleurs'>) =>
  contraste(kit.couleurs.encre, fond) >= contraste(kit.couleurs.papier, fond) ? kit.couleurs.encre : kit.couleurs.papier;

export interface VerdictContraste { texte: string; fond: string; ratio: number; aa: boolean; aaGrandTexte: boolean }
export function verifierContrastes(k: Pick<KitMarque, 'couleurs'>): VerdictContraste[] {
  const c = k.couleurs;
  const paires: [string, string][] = [[c.encre, c.papier], [c.papier, c.primaire], [c.encre, c.secondaire], [c.papier, c.accent], [c.encre, c.accent], [c.primaire, c.papier]];
  return paires.map(([texte, fond]) => { const ratio = Math.round(contraste(texte, fond) * 100) / 100; return { texte, fond, ratio, aa: ratio >= 4.5, aaGrandTexte: ratio >= 3 }; });
}

// ---- logo ----
const BALISES_SVG = new Set(['svg', 'g', 'path', 'circle', 'rect', 'ellipse', 'polygon', 'polyline', 'line', 'defs', 'lineargradient', 'radialgradient', 'stop', 'clippath', 'mask', 'text', 'tspan', 'title']);
/** Assainit un SVG avant de l'intégrer à une page : balises permises seulement, aucun script, aucun gestionnaire, aucune URL externe. */
export function assainirSvg(svg: string): string {
  if (!/<svg[\s>]/i.test(svg)) throw new Error('Le logo SVG est illisible (balise <svg> absente).');
  let s = svg.replace(/<\?xml[^>]*>/g, '').replace(/<!DOCTYPE[^>]*>/gi, '').replace(/<!--[\s\S]*?-->/g, '');
  s = s.replace(/<\s*(script|foreignObject|style|image|use|iframe|animate\w*|set)\b[\s\S]*?(<\/\s*\1\s*>|\/>)/gi, '');
  s = s.replace(/<\/?\s*([a-zA-Z][\w:-]*)([^>]*)>/g, (m, nom: string) => (BALISES_SVG.has(nom.toLowerCase()) ? m : ''));
  s = s.replace(/\s(on\w+|xlink:href|href)\s*=\s*("[^"]*"|'[^']*')/gi, (m, a: string, v: string) => (/^href|xlink:href$/i.test(a) && /^["']#/.test(v) ? m : ''));
  s = s.replace(/url\(\s*["']?(?!#)[^)]*\)/gi, 'none').replace(/javascript:/gi, '');
  if (!/viewBox\s*=/.test(s)) {
    const l = /<svg[^>]*\swidth\s*=\s*["']?([\d.]+)/i.exec(s)?.[1], h = /<svg[^>]*\sheight\s*=\s*["']?([\d.]+)/i.exec(s)?.[1];
    if (!l || !h) throw new Error('Le logo SVG n’a ni viewBox ni largeur/hauteur : impossible de le dimensionner.');
    s = s.replace(/<svg/i, `<svg viewBox="0 0 ${l} ${h}"`);
  }
  return s.trim();
}

export interface ControleLogo { ok: boolean; avertissements: string[]; zoneProtectionPct: number; tailleMinMm: number }
/** Contrôles du logo : taille minimale (raster : 300 dpi à 25 mm de large), zone de protection (la hauteur du « x » ≈ 25 % de la hauteur). */
export function controlerLogo(l: { svg?: string; largeurPx?: number; hauteurPx?: number }): ControleLogo {
  const av: string[] = [];
  let ok = true;
  if (!l.svg && !l.largeurPx) { return { ok: false, avertissements: ['Aucun logo fourni.'], zoneProtectionPct: 25, tailleMinMm: 20 }; }
  if (!l.svg && l.largeurPx) {
    const minPx = Math.round((25 / 25.4) * 300);
    if (l.largeurPx < minPx) { ok = false; av.push(`Logo trop petit (${l.largeurPx} px de large) : au moins ${minPx} px pour 25 mm à 300 dpi. Fournis un SVG de préférence.`); }
    if (l.hauteurPx && l.largeurPx / l.hauteurPx > 6) av.push('Logo très allongé : prévoir une version compacte (icône) pour les petits formats.');
  }
  if (l.svg && (l.svg.match(/<path/gi)?.length ?? 0) > 400) av.push('Logo SVG très détaillé : à petite taille, il risque de s’empâter.');
  av.push('Laisser une zone de protection d’au moins 25 % de la hauteur du logo, sans texte ni image.');
  return { ok, avertissements: av, zoneProtectionPct: 25, tailleMinMm: 20 };
}

// ---- couleurs dominantes ("extraire de mon logo") ----
const versHex = (r: number, g: number, b: number) => '#' + [r, g, b].map((x) => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, '0')).join('').toUpperCase();
const norm3 = (s: string) => (s.length === 4 ? '#' + [...s.slice(1)].map((c) => c + c).join('') : s).toUpperCase();

/** Couleurs d'un SVG par fréquence d'usage (fill/stroke/stop-color), sans blanc ni noir pur ni transparent. */
export function couleursDeSvg(svg: string): string[] {
  const n = new Map<string, number>();
  for (const m of svg.matchAll(/(?:fill|stroke|stop-color)\s*[:=]\s*["']?\s*(#[0-9a-fA-F]{3,6})\b/g)) {
    if (m[1].length !== 4 && m[1].length !== 7) continue;
    const h = norm3(m[1]);
    n.set(h, (n.get(h) ?? 0) + 1);
  }
  return [...n.entries()].sort((a, b) => b[1] - a[1]).map(([h]) => h).filter((h) => !['#FFFFFF', '#000000'].includes(h));
}

/** Décode un PNG 8 bits non entrelacé (gris, RVB, RVBA, palette) → pixels RGBA. Lève une erreur pour tout autre PNG. */
export function decoderPng(buf: Buffer): { w: number; h: number; rgba: Uint8Array } {
  if (buf.length < 33 || buf.readUInt32BE(0) !== 0x89504e47) throw new Error('Ce n’est pas un PNG.');
  let o = 8, w = 0, h = 0, depth = 0, type = 0, inter = 0;
  const idat: Buffer[] = [];
  let plte: Buffer | null = null, trns: Buffer | null = null;
  while (o + 8 <= buf.length) {
    const len = buf.readUInt32BE(o), t = buf.toString('latin1', o + 4, o + 8), d = buf.subarray(o + 8, o + 8 + len);
    if (t === 'IHDR') { w = d.readUInt32BE(0); h = d.readUInt32BE(4); depth = d[8]; type = d[9]; inter = d[12]; }
    else if (t === 'IDAT') idat.push(d);
    else if (t === 'PLTE') plte = d;
    else if (t === 'tRNS') trns = d;
    else if (t === 'IEND') break;
    o += 12 + len;
  }
  if (depth !== 8 || inter !== 0) throw new Error('PNG non pris en charge pour l’extraction (8 bits, non entrelacé).');
  const canaux = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 }[type as 0 | 2 | 3 | 4 | 6];
  if (!canaux) throw new Error('Type de PNG inconnu.');
  const raw = inflateSync(Buffer.concat(idat)), stride = w * canaux, out = Buffer.alloc(h * stride);
  for (let y = 0; y < h; y++) {
    const f = raw[y * (stride + 1)], src = y * (stride + 1) + 1;
    for (let x = 0; x < stride; x++) {
      const a = x >= canaux ? out[y * stride + x - canaux] : 0, b = y > 0 ? out[(y - 1) * stride + x] : 0, c = x >= canaux && y > 0 ? out[(y - 1) * stride + x - canaux] : 0;
      let v = raw[src + x];
      if (f === 1) v += a; else if (f === 2) v += b; else if (f === 3) v += (a + b) >> 1;
      else if (f === 4) { const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      out[y * stride + x] = v & 255;
    }
  }
  const rgba = new Uint8Array(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    const p = i * canaux;
    let r: number, g: number, b: number, a = 255;
    if (type === 6) [r, g, b, a] = [out[p], out[p + 1], out[p + 2], out[p + 3]];
    else if (type === 2) [r, g, b] = [out[p], out[p + 1], out[p + 2]];
    else if (type === 0) r = g = b = out[p];
    else if (type === 4) { r = g = b = out[p]; a = out[p + 1]; }
    else { const k = out[p]; r = plte?.[k * 3] ?? 0; g = plte?.[k * 3 + 1] ?? 0; b = plte?.[k * 3 + 2] ?? 0; a = trns?.[k] ?? 255; }
    rgba.set([r, g, b, a], i * 4);
  }
  return { w, h, rgba };
}

/** Couleurs dominantes d'un PNG : quantification à 4 bits par canal, pixels opaques, ni quasi-blancs ni quasi-noirs. */
export function couleursDePng(buf: Buffer, n = 4): string[] {
  const { rgba } = decoderPng(buf);
  const seaux = new Map<number, { c: number; r: number; g: number; b: number }>();
  const pas = Math.max(1, Math.floor(rgba.length / 4 / 60_000));
  for (let i = 0; i < rgba.length; i += 4 * pas) {
    const [r, g, b, a] = [rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]];
    if (a < 200 || (r > 240 && g > 240 && b > 240) || (r < 18 && g < 18 && b < 18)) continue;
    const k = (r >> 4) * 256 + (g >> 4) * 16 + (b >> 4), s = seaux.get(k) ?? { c: 0, r: 0, g: 0, b: 0 };
    s.c++; s.r += r; s.g += g; s.b += b; seaux.set(k, s);
  }
  const triees = [...seaux.values()].sort((a, b) => b.c - a.c).map((s) => versHex(s.r / s.c, s.g / s.c, s.b / s.c));
  const out: string[] = [];
  for (const h of triees) if (out.every((o) => distance(o, h) > 60)) out.push(h);
  return out.slice(0, n);
}
const distance = (a: string, b: string) => { const [x, y] = [rgb(a), rgb(b)]; return Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]); };

/** Palette proposée à partir des couleurs du logo : primaire (la plus sombre assez saturée), secondaire (teinte pâle), accent. */
export function paletteDepuisCouleurs(dom: string[], base: KitMarque['couleurs'] = KitMarqueSchema.shape.couleurs.parse(undefined)): KitMarque['couleurs'] {
  if (!dom.length) return base;
  const [primaire, deuxieme] = dom;
  const pale = (h: string) => { const [r, g, b] = rgb(h); return versHex(r + (255 - r) * 0.88, g + (255 - g) * 0.88, b + (255 - b) * 0.88); };
  const accent = deuxieme && distance(primaire, deuxieme) > 90 ? deuxieme : base.accent;
  const encre = contraste('#14181B', primaire) < 1.5 ? '#000000' : '#14181B';
  return { primaire, secondaire: pale(primaire), accent, encre, papier: base.papier };
}

/** Résumé du kit pour les modèles de langage (Producteur, assistant de conception) : marque, ton, couleurs, interdits. */
export function resumeMarque(k: KitMarque): string {
  const c = contactsActifs(k.contact, k.langue).map((x) => `${x.libelle} ${x.valeur}`).join(', ');
  return [
    `Marque : ${k.nom}${k.contact.entreprise && k.contact.entreprise !== k.nom ? ` (${k.contact.entreprise})` : ''}.`,
    k.ton.adjectifs.length ? `Ton : ${k.ton.adjectifs.join(', ')}.` : '',
    k.ton.interdits.length ? `Mots à éviter : ${k.ton.interdits.join(', ')}.` : '',
    `Couleurs : primaire ${k.couleurs.primaire}, secondaire ${k.couleurs.secondaire}, accent ${k.couleurs.accent}, encre ${k.couleurs.encre}, papier ${k.couleurs.papier}. Polices : ${policeParId(k.polices.titre).nom} (titres), ${policeParId(k.polices.texte).nom} (texte).`,
    c ? `Coordonnées : ${c}.` : '',
    `Langue : ${k.langue === 'en' ? 'anglais' : 'français canadien'}. Les images, vidéos et imprimés doivent rester dans ces couleurs et ce ton.`,
  ].filter(Boolean).join(' ');
}

/** Variantes de palette en un clic : « inverse » échange primaire et accent, « sombre » échange encre et papier. */
export function variantePalette(k: KitMarque, mode: 'defaut' | 'inverse' | 'sombre'): KitMarque {
  const c = k.couleurs;
  if (mode === 'inverse') return { ...k, couleurs: { ...c, primaire: c.accent, accent: c.primaire, secondaire: paletteDepuisCouleurs([c.accent], c).secondaire } };
  if (mode === 'sombre') return { ...k, couleurs: { ...c, encre: c.papier, papier: c.encre } };
  return k;
}
