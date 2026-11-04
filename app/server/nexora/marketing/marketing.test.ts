import { existsSync, mkdtempSync, readdirSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { join } from 'node:path';
import { deflateSync } from 'node:zlib';
import { PDFDocument } from 'pdf-lib';
import { describe, expect, it } from 'vitest';
import { devisMarketing } from './devis.js';
import { allegationsRefusees, nettoyerProposition, pistesParDefaut, proposer, validerPisteLogo } from './assistant.js';
import { KIT_EXEMPLE, TEXTE_EXEMPLE } from './exemple.js';
import { assainirSvg, contactsActifs, contraste, controlerLogo, couleursDePng, couleursDeSvg, estVide, KitMarqueSchema, paletteDepuisCouleurs, resumeMarque, texteSur, variantePalette, verifierContrastes } from './kit.js';
import { construireSpec, GABARITS, gabaritsPour, variablesPour } from './modeles.js';
import { fermerNavigateur, rendre } from './rendu.js';
import { boites, controler, dpiEffectif, FORMATS, lireSpec, MARGE_TRAITS, po, resoudre, SpecConceptionSchema } from './spec.js';
import { StoreKit } from './store.js';
import type { ClientLlm } from '../llm.js';

const kit = KIT_EXEMPLE;

describe('kit de marque', () => {
  it('rejette un kit sans nom ou avec une couleur mal formée, accepte le minimum', () => {
    expect(KitMarqueSchema.safeParse({ nom: '' }).success).toBe(false);
    expect(KitMarqueSchema.safeParse({ nom: 'A', couleurs: { primaire: 'rouge', secondaire: '#FFFFFF', accent: '#000000', encre: '#000000', papier: '#FFFFFF' } }).success).toBe(false);
    const k = KitMarqueSchema.parse({ nom: 'Atelier Nord' });
    expect(k.couleurs.primaire).toMatch(/^#[0-9A-F]{6}$/);
    expect(k.contact.courriel).toBe('');
  });
  it('contraste WCAG : noir/blanc = 21, le texte choisi sur un fond est le mieux contrasté', () => {
    expect(contraste('#000000', '#FFFFFF')).toBeCloseTo(21, 0);
    expect(texteSur('#1F4E5F', kit)).toBe(kit.couleurs.papier);
    expect(texteSur('#E07A2F', kit)).toBe(kit.couleurs.encre);
    const v = verifierContrastes(kit);
    expect(v.find((x) => x.texte === kit.couleurs.papier && x.fond === kit.couleurs.accent)!.aa).toBe(false); // papier sur orange : 2,9:1
    expect(v.find((x) => x.texte === kit.couleurs.encre && x.fond === kit.couleurs.papier)!.aa).toBe(true);
  });
  it('les coordonnées vides ou « à compléter » disparaissent sans trou', () => {
    expect(estVide('«à compléter : téléphone»')).toBe(true);
    const a = contactsActifs({ telephone: '', courriel: 'a@b.ca', web: '«à compléter»', adresse: '1 rue X' });
    expect(a.map((x) => x.cle)).toEqual(['courriel', 'adresse']);
    expect(contactsActifs({ courriel: 'a@b.ca' }, 'en')[0].libelle).toBe('Email');
  });
  it('assainit un logo SVG : scripts, gestionnaires et URL externes retirés ; viewBox exigé ou déduit', () => {
    const sale = '<svg width="100" height="50" onload="x()"><script>alert(1)</script><image href="http://x/y.png"/><path d="M0 0h10" fill="url(http://evil/x)" onclick="y()"/><foreignObject><p>x</p></foreignObject></svg>';
    const s = assainirSvg(sale);
    expect(s).not.toMatch(/script|onload|onclick|http:|foreignObject|<image/i);
    expect(s).toMatch(/viewBox="0 0 100 50"/);
    expect(() => assainirSvg('<div>pas un svg</div>')).toThrow();
    expect(() => assainirSvg('<svg><path d="M0 0"/></svg>')).toThrow(/viewBox/);
  });
  it('contrôle du logo : un PNG de 200 px est trop petit pour 25 mm à 300 dpi, un SVG passe', () => {
    expect(controlerLogo({ largeurPx: 200, hauteurPx: 100 }).ok).toBe(false);
    expect(controlerLogo({ largeurPx: 1200, hauteurPx: 400 }).ok).toBe(true);
    expect(controlerLogo({ svg: '<svg viewBox="0 0 1 1"/>' }).zoneProtectionPct).toBe(25);
    expect(controlerLogo({}).ok).toBe(false);
  });
  it('extrait les couleurs dominantes d’un SVG et d’un PNG, puis propose une palette', () => {
    expect(couleursDeSvg('<svg><path fill="#E07A2F"/><path fill="#1f4e5f"/><path fill="#1F4E5F"/><rect fill="#fff"/></svg>')).toEqual(['#1F4E5F', '#E07A2F']);
    // PNG RVB 8 bits 20×10 : moitié rouge vif, moitié bleu
    const w = 20, h = 10, raw = Buffer.alloc((w * 3 + 1) * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) raw.set(x < 12 ? [200, 30, 30] : [20, 60, 200], y * (w * 3 + 1) + 1 + x * 3);
    const crc = () => Buffer.alloc(4);
    const chunk = (t: string, d: Buffer) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); return Buffer.concat([l, Buffer.from(t), d, crc()]); };
    const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
    const png = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
    const dom = couleursDePng(png);
    expect(dom[0]).toBe('#C81E1E');
    expect(dom).toContain('#143CC8');
    const p = paletteDepuisCouleurs(dom);
    expect(p.primaire).toBe('#C81E1E');
    expect(p.secondaire).not.toBe(p.primaire);
  });
  it('variante de palette : inverse et sombre', () => {
    expect(variantePalette(kit, 'inverse').couleurs.primaire).toBe(kit.couleurs.accent);
    expect(variantePalette(kit, 'sombre').couleurs.papier).toBe(kit.couleurs.encre);
    expect(variantePalette(kit, 'defaut')).toBe(kit);
  });
  it('résumé pour le Producteur : nom, ton, interdits, couleurs, coordonnées remplies seulement', () => {
    const r = resumeMarque({ ...kit, contact: { ...kit.contact, adresse: '' } });
    expect(r).toContain('Source-Vive');
    expect(r).toContain('chaleureux');
    expect(r).toContain('meilleur');
    expect(r).toContain('#1F4E5F');
    expect(r).not.toContain('120, rue');
  });
  it('stockage par organisation, isolé', () => {
    const s = new StoreKit(mkdtempSync(join(tmpdir(), 'kit-')));
    expect(s.lire('orgA')).toBeNull();
    s.ecrire('orgA', kit);
    expect(s.lire('orgA')!.nom).toBe('Source-Vive');
    expect(s.lire('orgB')).toBeNull();
    expect(s.lire('../../etc')).toBeNull();
  });
});

describe('formats, fond perdu et marges', () => {
  it('conversions : 3,5 × 2 po = 88,9 × 50,8 mm, fond perdu 0,125 po = 3,175 mm', () => {
    expect(FORMATS['carte-affaires'].largeur).toBe(88.9);
    expect(FORMATS['carte-affaires'].hauteur).toBe(50.8);
    expect(FORMATS['carte-affaires'].fondPerdu).toBe(3.175);
    expect(po(8.5)).toBe(215.9);
  });
  it('géométrie de la page : avec traits, marge de légende ajoutée ; sans traits, la page s’arrête au fond perdu', () => {
    const f = FORMATS['carte-affaires'];
    const a = boites(f, f.fondPerdu, f.securite, true), b = boites(f, f.fondPerdu, f.securite, false);
    expect(b.page.l).toBeCloseTo(88.9 + 2 * 3.175, 1);
    expect(a.page.l).toBeCloseTo(88.9 + 2 * (3.175 + MARGE_TRAITS), 1);
    expect(a.coupe.x).toBeCloseTo(3.175 + MARGE_TRAITS, 1);
    expect(a.fondPerdu.x).toBeCloseTo(MARGE_TRAITS, 1);
    expect(a.securite.l).toBeCloseTo(88.9 - 2 * 3.175, 1);
    expect(b.coupe.x).toBeCloseTo(b.fondPerdu.x + 3.175, 1);
  });
  it('résolution effective : 1050 px sur 3,5 po = 300 dpi', () => { expect(dpiEffectif(1050, 88.9)).toBe(300); });
});

describe('SpecConception', () => {
  it('valide les 9 gabarits sur leurs formats, avec des couleurs et polices du kit', () => {
    for (const g of GABARITS) for (const f of g.formats) {
      const spec = construireSpec(g.id, f, kit, { ...TEXTE_EXEMPLE.flyer });
      expect(SpecConceptionSchema.safeParse(spec).success, `${g.id} ${f}`).toBe(true);
      expect(spec.faces.length).toBeGreaterThanOrEqual(1);
    }
    expect(GABARITS.filter((g) => g.formats.includes('carte-affaires'))).toHaveLength(3);
    expect(gabaritsPour('flyer-lettre')).toHaveLength(3);
    expect(gabaritsPour('accroche-porte')).toHaveLength(3);
  });
  it('rejette une spec invalide avec un message lisible', () => {
    expect(() => lireSpec({ version: 2 })).toThrow(/invalide/);
    const s = construireSpec('carte-aplat', 'carte-affaires', kit);
    expect(() => lireSpec({ ...s, format: 'inconnu' })).toThrow();
    expect(() => lireSpec({ ...s, faces: [{ ...s.faces[0], calques: [{ type: 'texte', id: 'x', x: 0, y: 0, l: 1, h: 1, texte: 'a', police: 'comic-sans', taille: 10, couleur: '#000000' }] }] })).toThrow();
  });
  it('un gabarit ne s’applique qu’à ses formats ; un kit autre donne d’autres couleurs (pas codé en dur)', () => {
    expect(() => construireSpec('carte-aplat', 'flyer-lettre', kit)).toThrow(/ne s’applique pas/);
    const autre = KitMarqueSchema.parse({ nom: 'Autre', couleurs: { primaire: '#6B1F7A', secondaire: '#F1E6F4', accent: '#2FA37A', encre: '#101010', papier: '#FFFFFF' } });
    const a = JSON.stringify(construireSpec('carte-aplat', 'carte-affaires', kit)), b = JSON.stringify(construireSpec('carte-aplat', 'carte-affaires', autre));
    expect(a).toContain('#1F4E5F'); expect(b).not.toContain('#1F4E5F'); expect(b).toContain('#6B1F7A');
  });
  it('les champs vides disparaissent : ligne de coordonnées, calque de texte, QR sans adresse', () => {
    const sansWeb = { ...kit, contact: { ...kit.contact, web: '', adresse: '' } };
    const spec = resoudre(construireSpec('carte-bloc', 'carte-affaires', sansWeb));
    const verso = spec.faces[1].calques;
    expect(verso.some((c) => c.type === 'qr')).toBe(false);
    const coord = verso.find((c) => c.type === 'texte' && c.id === 'coordonnees') as any;
    expect(coord.texte.split('\n')).toEqual(['819 555-0142', 'camille@source-vive.example']);
    const sansAccroche = resoudre(construireSpec('carte-aplat', 'carte-affaires', kit));
    expect(sansAccroche.faces[0].calques.some((c) => c.type === 'texte' && c.id === 'accroche')).toBe(false);
    const avec = resoudre(construireSpec('carte-aplat', 'carte-affaires', kit, TEXTE_EXEMPLE.carte));
    expect(avec.faces[0].calques.some((c) => c.type === 'texte' && c.id === 'accroche')).toBe(true);
    expect(variablesPour(kit, { accroche: '«à compléter»' }).accroche).toBe('');
    expect(variablesPour(kit).url).toBe('https://source-vive.example');
  });
  it('contrôle : image à 120 dpi = erreur, 250 dpi = avertissement, texte hors zone de sécurité, contraste, bord sans débordement', () => {
    const base = construireSpec('carte-aplat', 'carte-affaires', kit, TEXTE_EXEMPLE.carte);
    const calque = (c: any) => ({ ...base, faces: [{ ...base.faces[0], calques: [...base.faces[0].calques, c] }, base.faces[1]] });
    const img = (px: number) => ({ type: 'image', id: 'photo', x: 10, y: 10, l: 40, h: 20, src: 'data:image/png;base64,AA', ajustement: 'cover', pxLargeur: px, opacite: 1 });
    expect(controler(calque(img(Math.round(40 / 25.4 * 120)))).constats.find((c) => c.code === 'resolution')!.gravite).toBe('erreur');
    expect(controler(calque(img(Math.round(40 / 25.4 * 250)))).constats.find((c) => c.code === 'resolution')!.gravite).toBe('avertissement');
    expect(controler(calque(img(Math.round(40 / 25.4 * 320)))).constats.some((c) => c.code === 'resolution')).toBe(false);
    const hors = controler(base, [{ face: 0, id: 'accroche', x: 1, y: 10, l: 30, h: 5 }]);
    expect(hors.ok).toBe(false);
    expect(hors.constats.some((c) => c.code === 'zone-securite')).toBe(true);
    expect(controler(base, [{ face: 0, id: 'accroche', x: 7, y: 10, l: 30, h: 5 }]).ok).toBe(true);
    const faible = calque({ type: 'texte', id: 'gris', x: 5, y: 5, l: 30, h: 5, texte: 'x', police: 'inter', poids: 400, taille: 8, couleur: '#2A6B7F', align: 'left', interligne: 1.2, crenage: 0, casse: 'aucune', ajuster: true, valign: 'top' });
    expect(controler(faible).constats.some((c) => c.code === 'contraste')).toBe(true);
    const bord = calque({ type: 'forme', id: 'bande', x: 0, y: 40, l: 88.9, h: 10.8, forme: 'rect', remplissage: '#E07A2F', epaisseur: 0, rayon: 0, opacite: 1, decoupe: false });
    expect(controler(bord).constats.some((c) => c.code === 'fond-perdu')).toBe(true);
    expect(controler(base).constats.some((c) => c.code === 'fond-perdu')).toBe(false); // les gabarits débordent
  });
  it('tous les gabarits passent le contrôle de contraste et de fond perdu avec le kit d’exemple', () => {
    for (const g of GABARITS) for (const f of g.formats) {
      const c = controler(resoudre(construireSpec(g.id, f, kit, { ...TEXTE_EXEMPLE.flyer })));
      expect(c.constats.filter((x) => x.gravite === 'erreur'), `${g.id} ${f}`).toEqual([]);
    }
  });
});

describe('devis et assistant', () => {
  it('devis : le rendu est gratuit, les propositions coûtent des crédits croissants avec le palier', () => {
    expect(devisMarketing('rendu', 'eco').credits).toBe(0);
    const eco = devisMarketing('propositions', 'eco'), expert = devisMarketing('propositions', 'expert');
    expect(eco.credits).toBeGreaterThanOrEqual(1);
    expect(expert.credits).toBeGreaterThanOrEqual(eco.credits);
    expect(eco.creditsReserves).toBeGreaterThanOrEqual(eco.credits);
    expect(devisMarketing('logos', 'eco').llm!.sortie).toBeGreaterThan(devisMarketing('variantes', 'eco').llm!.sortie);
  });
  it('allégations : superlatifs, garanties, chiffres et mots interdits du kit sont refusés', () => {
    expect(allegationsRefusees('Le meilleur plombier de la région', kit)).toContain('meilleur');
    expect(allegationsRefusees('Satisfaction garantie, 100 % fiable')).toHaveLength(2);
    expect(allegationsRefusees('Soumission gratuite', kit).length).toBeGreaterThan(0);
    expect(allegationsRefusees('Une plomberie qui coule de source.', kit)).toEqual([]);
    expect(allegationsRefusees('Best price, guaranteed')).toHaveLength(2);
  });
  it('nettoyage : longueur bornée et retrait signalé', () => {
    const r = nettoyerProposition({ gabarit: 'carte-aplat', accroche: 'Chaque goutte à sa place.', sousTitre: '', point1: 'x'.repeat(80), point2: 'Garantie à vie', point3: '', appel: '', offre: '', pourquoi: '' }, kit, 'flyer-lettre');
    expect(r.variables).toEqual({ accroche: 'Chaque goutte à sa place.' });
    expect(r.retires).toHaveLength(2);
    expect(nettoyerProposition({ gabarit: 'c', accroche: 'a'.repeat(50), sousTitre: '', point1: '', point2: '', point3: '', appel: '', offre: '', pourquoi: '' }, kit, 'carte-affaires').variables.accroche).toBeUndefined();
  });
  const faux = (reponses: string[]): ClientLlm => { let i = 0; return { completer: async () => reponses[Math.min(i++, reponses.length - 1)] }; };
  const bonne = JSON.stringify({ propositions: [
    { gabarit: 'carte-aplat', accroche: 'Chaque goutte à sa place.', pourquoi: 'bénéfice' },
    { gabarit: 'carte-filet', accroche: 'Votre eau, notre soin.', pourquoi: 'invitation' },
    { gabarit: 'carte-bloc', accroche: 'Un geste précis, un chantier propre.', pourquoi: 'preuve' },
  ] });
  it('propositions : trois specs valides, textes du modèle, 0 escalade quand Éco réussit', async () => {
    const r = await proposer({ phrase: 'carte d’affaires pour une plombière à Sherbrooke, ton chaleureux', format: 'carte-affaires' }, kit, [{ palier: 'eco', client: faux([bonne]) }, { palier: 'equilibre', client: faux([bonne]) }]);
    expect(r.sansIA).toBe(false); expect(r.palier).toBe('eco'); expect(r.escalades).toBe(0);
    expect(r.propositions).toHaveLength(3);
    expect(new Set(r.propositions.map((p) => p.gabarit)).size).toBe(3);
    for (const p of r.propositions) expect(SpecConceptionSchema.safeParse(p.spec).success).toBe(true);
  });
  it('escalade : Éco répond du texte invalide ou des allégations → le palier suivant est utilisé', async () => {
    const mauvaise = JSON.stringify({ propositions: [{ gabarit: 'carte-aplat', accroche: 'Le meilleur plombier' }, { gabarit: 'carte-filet', accroche: 'Satisfaction garantie' }] });
    const r = await proposer({ phrase: 'x', format: 'carte-affaires' }, kit, [{ palier: 'eco', client: faux([mauvaise]) }, { palier: 'equilibre', client: faux([bonne]) }]);
    expect(r.palier).toBe('equilibre'); expect(r.escalades).toBe(1);
    const nul = await proposer({ phrase: 'x', format: 'carte-affaires' }, kit, [{ palier: 'eco', client: faux(['pas du json']) }]);
    expect(nul.sansIA).toBe(true); expect(nul.propositions).toHaveLength(3);
  });
  it('sans modèle : trois compositions avec textes de substitution', async () => {
    const r = await proposer({ phrase: 'x', format: 'accroche-porte' }, kit, []);
    expect(r.sansIA).toBe(true);
    expect(r.propositions.map((p) => p.gabarit)).toEqual(['accroche-bande', 'accroche-sobre', 'accroche-arche']);
  });
  it('pistes de logo : le code en fournit quatre valides ; celles du modèle sont rejetées hors palette ou avec script', () => {
    const d = pistesParDefaut(kit);
    expect(d).toHaveLength(4);
    for (const p of d) expect(validerPisteLogo(p, kit)).not.toBeNull();
    expect(validerPisteLogo({ nom: 'x', svg: '<svg viewBox="0 0 240 80"><rect fill="#FF00FF" width="10" height="10"/></svg>' }, kit)).toBeNull();
    const s = validerPisteLogo({ nom: 'x', svg: `<svg viewBox="0 0 240 80"><script>x</script><rect fill="${kit.couleurs.primaire}" width="10" height="10"/></svg>` }, kit)!;
    expect(s.svg).not.toContain('script');
  });
});

const chromium = [process.env.NEXORA_CHROMIUM, ...(existsSync(join(homedir(), '.cache/ms-playwright')) ? readdirSync(join(homedir(), '.cache/ms-playwright')).filter((d) => d.startsWith('chromium')) : [])].filter(Boolean).length > 0;
describe.skipIf(!chromium)('rendu réel (Chromium)', () => {
  it('une carte : PDF 2 pages avec fond perdu, TrimBox et BleedBox posées, PNG à 300 dpi', async () => {
    const spec = construireSpec('carte-aplat', 'carte-affaires', kit, TEXTE_EXEMPLE.carte);
    const r = await rendre(spec, kit);
    await fermerNavigateur();
    const impr = await PDFDocument.load(r.pdfs.find((p) => p.variante === 'impression')!.pdf);
    const sans = await PDFDocument.load(r.pdfs.find((p) => p.variante === 'sans-traits')!.pdf);
    expect(impr.getPageCount()).toBe(1 + 1);
    const mm = (pt: number) => (pt / 72) * 25.4;
    const p = sans.getPage(0);
    expect(mm(p.getWidth())).toBeCloseTo(88.9 + 2 * 3.175, 1);
    expect(mm(impr.getPage(0).getWidth())).toBeCloseTo(88.9 + 2 * (3.175 + MARGE_TRAITS), 1);
    const trim = impr.getPage(0).getTrimBox();
    expect(mm(trim.width)).toBeCloseTo(88.9, 1);
    expect(mm(trim.height)).toBeCloseTo(50.8, 1);
    const bleed = impr.getPage(0).getBleedBox();
    expect(mm(bleed.width)).toBeCloseTo(88.9 + 2 * 3.175, 1);
    expect(r.pngs).toHaveLength(2);
    const largeurPng = r.pngs[0].png.readUInt32BE(16);
    expect(largeurPng).toBeGreaterThanOrEqual(1050); // 3,5 po × 300 dpi (arrondi vers l’extérieur par Chromium : +3 px au plus)
    expect(largeurPng).toBeLessThanOrEqual(1056);
    expect(r.controle.erreurs).toBe(0);
    expect(r.mesures.length).toBeGreaterThan(0);
  }, 60_000);
});
