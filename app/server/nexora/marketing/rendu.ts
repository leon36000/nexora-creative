/**
 * Rendu des pièces (vague 2, #15/#17) : SpecConception → HTML en millimètres → Chromium (Playwright) → PDF avec fond perdu
 * et traits de coupe (TrimBox/BleedBox posées par pdf-lib) + PNG à 300 dpi, mesure réelle des boîtes de texte pour le
 * contrôle préliminaire, conversion CMJN optionnelle par Ghostscript. Polices intégrées (OFL, fichiers @fontsource).
 */
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { PDFDocument } from 'pdf-lib';
import qrcode from 'qrcode-generator';
import { chromium, type Browser } from 'playwright-core';
import { type KitMarque, policeParId, assainirSvg } from './kit.js';
import { FORMATS, boites, controler, mmVersPt, policesUtilisees, resoudre, type Calque, type Controle, type Face, type Mesure, type SpecConception } from './spec.js';

const require_ = createRequire(import.meta.url);
const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

const cssPolices = new Map<string, Promise<string>>();
/** @font-face en base64 pour une police du kit (poids 400, 600, 700) : le PDF n'a besoin d'aucune police installée. */
export function cssPolice(id: string): Promise<string> {
  let p = cssPolices.get(id);
  if (!p) {
    const f = policeParId(id);
    p = Promise.all([400, 600, 700].map(async (w) => {
      const chemin = require_.resolve(`@fontsource/${f.paquet}/files/${f.paquet}-latin-${w}-normal.woff`);
      return `@font-face{font-family:"${f.famille}";font-weight:${w};font-style:normal;src:url(data:font/woff;base64,${(await readFile(chemin)).toString('base64')}) format("woff")}`;
    })).then((l) => l.join('\n'));
    cssPolices.set(id, p);
  }
  return p;
}
const famille = (id: string) => {
  const f = policeParId(id);
  return `'${f.famille}',${f.genre === 'serif' ? 'serif' : f.genre === 'mono' ? 'monospace' : 'sans-serif'}`;
};

function svgQr(url: string, encre: string, fond: string): string {
  const q = qrcode(0, 'M');
  q.addData(url); q.make();
  const n = q.getModuleCount(), m = 3;
  let d = '';
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${c + m} ${r + m}h1v1h-1z`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${n + 2 * m} ${n + 2 * m}" shape-rendering="crispEdges" style="width:100%;height:100%;display:block"><rect width="100%" height="100%" fill="${fond}"/><path d="${d}" fill="${encre}"/></svg>`;
}

function htmlLogo(c: Extract<Calque, { type: 'logo' }>, kit: KitMarque): string {
  const filtre = c.variante === 'clair' ? 'filter:brightness(0) invert(1);' : c.variante === 'sombre' ? 'filter:brightness(0);' : '';
  const boite = `left:${c.x}mm;top:${c.y}mm;width:${c.l}mm;height:${c.h}mm;`;
  if (kit.logo.svg) {
    const svg = assainirSvg(kit.logo.svg).replace(/<svg([^>]*)>/i, (_, a: string) => `<svg${a.replace(/\s(width|height|preserveAspectRatio)\s*=\s*("[^"]*"|'[^']*')/gi, '')} preserveAspectRatio="xMinYMid meet" style="width:100%;height:100%;display:block">`);
    return `<div class="c" data-id="${esc(c.id)}" style="${boite}${filtre}">${svg}</div>`;
  }
  if (kit.logo.png) return `<img class="c" data-id="${esc(c.id)}" src="${kit.logo.png}" style="${boite}object-fit:contain;object-position:left center;${filtre}">`;
  const col = c.variante === 'clair' ? kit.couleurs.papier : c.variante === 'sombre' ? kit.couleurs.encre : kit.couleurs.primaire;
  return `<div class="c" data-id="${esc(c.id)}" style="${boite}display:flex;align-items:center;font-family:${famille(kit.polices.titre)};font-weight:700;font-size:${(c.h * 0.62 * 72 / 25.4).toFixed(1)}pt;color:${col};letter-spacing:-.02em;white-space:nowrap">${esc(kit.nom)}</div>`;
}

function htmlCalque(c: Calque, i: number, kit: KitMarque): string {
  const boite = `left:${c.x}mm;top:${c.y}mm;width:${c.l}mm;height:${c.h}mm;`;
  switch (c.type) {
    case 'texte': {
      const just = { top: 'flex-start', middle: 'center', bottom: 'flex-end' }[c.valign];
      return `<div class="c t" data-id="${esc(c.id)}" data-face="${i}" data-auto="${c.ajuster ? 1 : 0}" style="${boite}display:flex;flex-direction:column;justify-content:${just};font-family:${famille(c.police)};font-weight:${c.poids};font-size:${c.taille}pt;color:${c.couleur};text-align:${c.align};line-height:${c.interligne};letter-spacing:${c.crenage}em;${c.casse === 'majuscules' ? 'text-transform:uppercase;' : ''}"><div class="in">${esc(c.texte).replace(/\n/g, '<br>')}</div></div>`;
    }
    case 'image': return `<img class="c" data-id="${esc(c.id)}" src="${c.src}" style="${boite}object-fit:${c.ajustement};opacity:${c.opacite}">`;
    case 'forme': {
      const contour = c.contour ? `border:${c.epaisseur}mm solid ${c.contour};box-sizing:border-box;` : '';
      return `<div class="c" data-id="${esc(c.id)}" style="${boite}${c.remplissage ? `background:${c.remplissage};` : ''}${contour}border-radius:${c.forme === 'cercle' ? '50%' : `${c.rayon}mm`};opacity:${c.opacite}"></div>`;
    }
    case 'logo': return htmlLogo(c, kit);
    case 'qr': return `<div class="c" data-id="${esc(c.id)}" style="${boite}">${svgQr(c.url, c.encre ?? kit.couleurs.encre, c.fond ?? kit.couleurs.papier)}</div>`;
  }
}

function htmlTraits(coupe: { x: number; y: number; l: number; h: number }, fp: number, nom: string): string {
  const e = 1.5, long = 5, ep = 0.18;
  const ligne = (x: number, y: number, l: number, h: number) => `<i class="m" style="left:${x}mm;top:${y}mm;width:${l}mm;height:${h}mm"></i>`;
  const out: string[] = [];
  for (const x of [coupe.x, coupe.x + coupe.l]) for (const [y0, sens] of [[coupe.y - fp - e, -1], [coupe.y + coupe.h + fp + e, 1]] as const) out.push(ligne(x - ep / 2, sens < 0 ? y0 - long : y0, ep, long));
  for (const y of [coupe.y, coupe.y + coupe.h]) for (const [x0, sens] of [[coupe.x - fp - e, -1], [coupe.x + coupe.l + fp + e, 1]] as const) out.push(ligne(sens < 0 ? x0 - long : x0, y - ep / 2, long, ep));
  out.push(`<div class="leg" style="left:${coupe.x}mm;top:${coupe.y + coupe.h + fp + 3}mm;width:${coupe.l}mm">${esc(nom)}</div>`);
  return out.join('');
}

export function htmlPiece(spec: SpecConception, kit: KitMarque, o: { traits: boolean; fontCss: string }): string {
  const f = FORMATS[spec.format];
  const b = boites(f, spec.fondPerdu, spec.securite, o.traits);
  const pages = spec.faces.map((face: Face, i) => {
    const fond = face.genre === 'decoupe' ? '#FFFFFF' : face.fond.degrade ? `linear-gradient(${face.fond.degrade.angle}deg,${face.fond.couleur},${face.fond.degrade.vers})` : face.fond.couleur;
    return `<section class="page" style="width:${b.page.l}mm;height:${b.page.h}mm">
<div class="fp" style="left:${b.fondPerdu.x}mm;top:${b.fondPerdu.y}mm;width:${b.fondPerdu.l}mm;height:${b.fondPerdu.h}mm;background:${fond}">
<div class="trim" data-face="${i}" style="left:${spec.fondPerdu}mm;top:${spec.fondPerdu}mm;width:${f.largeur}mm;height:${f.hauteur}mm">${face.calques.map((c) => htmlCalque(c, i, kit)).join('\n')}</div></div>
${o.traits ? htmlTraits(b.coupe, spec.fondPerdu, `${spec.gabarit} — ${face.nom} — ${f.nom} — fond perdu ${spec.fondPerdu} mm`) : ''}</section>`;
  });
  return `<!doctype html><html><head><meta charset="utf-8"><style>
${o.fontCss}
@page{size:${b.page.l}mm ${b.page.h}mm;margin:0}
*{box-sizing:border-box;margin:0;padding:0}html,body{margin:0;background:#fff}
.page{position:relative;overflow:hidden;break-after:page;page-break-after:always}.page:last-child{break-after:auto;page-break-after:auto}
.fp{position:absolute;overflow:hidden}.trim{position:absolute}.c{position:absolute}
.t .in{width:100%;overflow-wrap:break-word;font-kerning:normal;font-variant-ligatures:common-ligatures}
.m{position:absolute;background:#000;display:block}
.leg{position:absolute;font:5pt "Inter",sans-serif;color:#555;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
</style></head><body>${pages.join('\n')}</body></html>`;
}

// Scripts exécutés dans la page (écrits en texte : le serveur n'a pas la bibliothèque DOM).
const SCRIPT_MESURE = `(() => {
  const MM = 25.4 / 96, out = [];
  document.querySelectorAll('.t').forEach((el) => {
    const inner = el.querySelector('.in'), taille0 = parseFloat(getComputedStyle(el).fontSize);
    let taille = taille0;
    if (el.dataset.auto === '1') while (taille > taille0 * 0.6 && (inner.scrollHeight > el.clientHeight + 0.5 || el.scrollWidth > el.clientWidth + 0.5)) { taille *= 0.96; el.style.fontSize = taille + 'px'; }
    const trim = el.closest('.trim').getBoundingClientRect(), r = document.createRange();
    r.selectNodeContents(inner);
    const b = r.getBoundingClientRect();
    out.push({ face: Number(el.dataset.face), id: el.dataset.id, x: (b.left - trim.left) * MM, y: (b.top - trim.top) * MM, l: b.width * MM, h: b.height * MM, taillePt: taille * 0.75, debordeBoite: taille < taille0 - 0.01 });
  });
  return out;
})()`;
/** Mêmes tailles de texte que la première passe, pour que les variantes de PDF soient identiques. */
const scriptRestaurer = (m: Mesure[]) => `(() => { for (const x of ${JSON.stringify(m)}) { const el = document.querySelector('.t[data-id="' + x.id + '"][data-face="' + x.face + '"]'); if (el && x.debordeBoite) el.style.fontSize = (x.taillePt / 0.75) + 'px'; } })()`;

// ---- Chromium ----
let navigateur: Promise<Browser> | null = null;
function browser(): Promise<Browser> {
  if (!navigateur) {
    navigateur = chromium.launch({
      executablePath: process.env.NEXORA_CHROMIUM?.trim() || undefined,
      args: process.env.NEXORA_CHROMIUM_SANS_BAC ? ['--no-sandbox'] : [],
    });
    navigateur.then((b) => b.on('disconnected', () => { navigateur = null; })).catch(() => { navigateur = null; });
  }
  return navigateur;
}
export async function fermerNavigateur() { const b = navigateur; navigateur = null; if (b) await (await b).close().catch(() => {}); }

// Un rendu à la fois : Chromium consomme ~300 Mo et la VM n'a que 4 Go.
let file: Promise<unknown> = Promise.resolve();
const enFile = <T>(t: () => Promise<T>): Promise<T> => { const p = file.then(t, t); file = p.catch(() => {}); return p; };

const lancer = (cmd: string, args: string[]) => new Promise<{ code: number; err: string }>((ok) => {
  const p = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] });
  let err = '';
  p.stderr.on('data', (d) => { err += d; });
  p.on('error', (e) => ok({ code: -1, err: String(e) }));
  p.on('close', (code) => ok({ code: code ?? -1, err }));
});
let gsDispo: Promise<boolean> | null = null;
export const ghostscriptDisponible = () => (gsDispo ??= lancer('gs', ['--version']).then((r) => r.code === 0));

/** Conversion CMJN (Ghostscript, profil par défaut). Renvoie le PDF d'origine si Ghostscript est absent ou échoue. */
export async function versCmjn(pdf: Buffer): Promise<{ pdf: Buffer; fait: boolean }> {
  if (!(await ghostscriptDisponible())) return { pdf, fait: false };
  const dir = await mkdtemp(join(tmpdir(), 'nexora-cmjn-'));
  try {
    await writeFile(join(dir, 'in.pdf'), pdf);
    const r = await lancer('gs', ['-q', '-dNOPAUSE', '-dBATCH', '-dSAFER', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4', '-dPDFSETTINGS=/prepress', '-sColorConversionStrategy=CMYK', '-sProcessColorModel=DeviceCMYK', `-sOutputFile=${join(dir, 'out.pdf')}`, join(dir, 'in.pdf')]);
    if (r.code !== 0) return { pdf, fait: false };
    return { pdf: await readFile(join(dir, 'out.pdf')), fait: true };
  } finally { await rm(dir, { recursive: true, force: true }); }
}

/** Pose TrimBox et BleedBox (Chromium ne sait pas les écrire) pour que l'imprimeur retrouve la coupe. */
export async function poserBoites(pdf: Buffer, spec: SpecConception, traits: boolean): Promise<Buffer> {
  const f = FORMATS[spec.format], b = boites(f, spec.fondPerdu, spec.securite, traits);
  const doc = await PDFDocument.load(pdf);
  const H = mmVersPt(b.page.h);
  for (const p of doc.getPages()) {
    const r = (z: { x: number; y: number; l: number; h: number }) => [mmVersPt(z.x), H - mmVersPt(z.y + z.h), mmVersPt(z.l), mmVersPt(z.h)] as const;
    p.setTrimBox(...r(b.coupe)); p.setBleedBox(...r(b.fondPerdu));
  }
  doc.setTitle(`${spec.gabarit} — ${f.nom}`); doc.setProducer('Nexora Creative'); doc.setCreator('Nexora Creative — mode Marketing');
  return Buffer.from(await doc.save());
}

export interface OptionsRendu { cmjn?: boolean; dpiPng?: number; variantes?: ('impression' | 'sans-traits')[]; extra?: Record<string, string> }
export interface ResultatRendu {
  pdfs: { variante: 'impression' | 'sans-traits'; pdf: Buffer; cmjn: boolean }[];
  pngs: { face: string; png: Buffer }[];
  mesures: Mesure[]; controle: Controle; ms: number;
}

/** Rend une spec : PDF (avec et sans traits), PNG des faces d'art à 300 dpi (réduit pour les grands formats), contrôle. */
export function rendre(specBrute: SpecConception, kit: KitMarque, o: OptionsRendu = {}): Promise<ResultatRendu> {
  return enFile(async () => {
    const t0 = Date.now();
    const spec = resoudre(specBrute, o.extra);
    const f = FORMATS[spec.format];
    const fontCss = (await Promise.all([...new Set([...policesUtilisees(spec), kit.polices.titre, 'inter'])].map(cssPolice))).join('\n');
    const dpi = o.dpiPng ?? Math.max(72, Math.min(300, Math.floor(3300 / (Math.max(f.largeur, f.hauteur) / 25.4))));
    const ctx = await (await browser()).newContext({ deviceScaleFactor: dpi / 96, viewport: { width: 1400, height: 1000 } });
    try {
      const page = await ctx.newPage();
      const variantes = o.variantes ?? ['impression', 'sans-traits'];
      const pdfs: ResultatRendu['pdfs'] = [];
      let mesures: Mesure[] = [];
      const pngs: ResultatRendu['pngs'] = [];
      for (const [k, v] of variantes.entries()) {
        const traits = v === 'impression';
        await page.setContent(htmlPiece(spec, kit, { traits, fontCss }), { waitUntil: 'load' });
        await page.evaluate('document.fonts.ready.then(() => true)');
        if (k === 0) {
          mesures = (await page.evaluate(SCRIPT_MESURE)) as Mesure[];
          for (const [i, face] of spec.faces.entries()) {
            if (face.genre === 'decoupe') continue;
            pngs.push({ face: face.nom, png: await page.locator(`.trim[data-face="${i}"]`).screenshot({ type: 'png' }) });
          }
        } else {
          // Même mise à l'échelle des textes que la première passe, pour que les variantes soient identiques.
          await page.evaluate(scriptRestaurer(mesures));
        }
        const b = boites(f, spec.fondPerdu, spec.securite, traits);
        let pdf: Buffer = Buffer.from(await page.pdf({ width: `${b.page.l}mm`, height: `${b.page.h}mm`, printBackground: true, preferCSSPageSize: true }));
        const c = o.cmjn ? await versCmjn(pdf) : { pdf, fait: false };
        pdfs.push({ variante: v, pdf: await poserBoites(c.pdf, spec, traits), cmjn: c.fait });
      }
      const controle = controler(spec, mesures, { cmjn: o.cmjn, cmjnDisponible: pdfs[0]?.cmjn });
      return { pdfs, pngs, mesures, controle, ms: Date.now() - t0 };
    } finally { await ctx.close(); }
  });
}
