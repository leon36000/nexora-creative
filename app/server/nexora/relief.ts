/**
 * Relief (mode 3D de Nexora Creative) : tout ce qui travaille sur le maillage d'un GLB, côté serveur et sans GPU.
 * Lecture du GLB, contrôle (étanchéité, arêtes non-variété, composantes, nombre de triangles), décimation à un nombre de
 * triangles voulu (meshoptimizer), exports OBJ (+ MTL + texture), STL binaire, 3MF et USDZ. Tout est pur et testé sans moteur.
 * Nom du produit : src/produit3d.ts. Rapport : recherche/18 ; mesures : recherche/21.
 */
import { crc32 } from 'node:zlib';
import { Document, NodeIO, type Primitive, type Transform } from '@gltf-transform/core';
import { simplify, weld } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import { zipSync, strToU8 } from 'fflate';

export type FormatRelief = 'glb' | 'obj' | 'stl' | '3mf' | 'usdz';
export const FORMATS_RELIEF: readonly FormatRelief[] = ['glb', 'obj', 'stl', '3mf', 'usdz'];
export const TYPE_MIME_RELIEF: Record<FormatRelief | 'zip', string> = {
  glb: 'model/gltf-binary', obj: 'application/zip', stl: 'model/stl', '3mf': 'model/3mf', usdz: 'model/vnd.usdz+zip', zip: 'application/zip',
};
/** Extension du fichier livré (l'OBJ part en zip : le .obj, son .mtl et la texture ensemble). */
export const EXTENSION_RELIEF: Record<FormatRelief, string> = { glb: 'glb', obj: 'zip', stl: 'stl', '3mf': '3mf', usdz: 'usdz' };

export const FACES_MIN = 500;
export const FACES_MAX = 2_000_000;
/** Hauteur par défaut des fichiers d'impression (STL, 3MF), en millimètres. */
export const TAILLE_MM_DEFAUT = 100;

export interface Maillage {
  positions: Float32Array;
  /** Coordonnées de texture (2 par sommet) ; null si le modèle n'en a pas. */
  uvs: Float32Array | null;
  indices: Uint32Array;
  /** Image de la couleur de base (PNG ou JPEG) et son type. */
  couleur: { octets: Uint8Array; mime: string } | null;
}

export interface RapportMaillage {
  sommets: number;
  triangles: number;
  /** Triangles de surface nulle ou à sommet répété. */
  degeneres: number;
  /** Arêtes n'appartenant qu'à un seul triangle (trous). */
  aretesOuvertes: number;
  /** Arêtes partagées par plus de deux triangles. */
  aretesNonVariete: number;
  composantes: number;
  etanche: boolean;
  /** Boîte englobante (largeur, hauteur, profondeur) dans l'unité du modèle. */
  taille: [number, number, number];
  /** Volume (unité³) si une composante fermée a un volume calculable ; null si ouvert ou ambigu. */
  volume: number | null;
  avertissements: string[];
}

// ---------- lecture ----------

const io = new NodeIO();

/** Aplatit toutes les primitives triangulaires d'un GLB (transformations de nœuds appliquées) en un seul maillage. */
export async function lireGlb(glb: Uint8Array): Promise<Maillage> {
  const doc = await io.readBinary(glb);
  return maillageDuDocument(doc);
}

export function maillageDuDocument(doc: Document): Maillage {
  const pos: number[] = [];
  const uv: number[] = [];
  const idx: number[] = [];
  let aUv = true;
  let couleur: Maillage['couleur'] = null;
  const racine = doc.getRoot();
  const noeuds = racine.listNodes().filter((n) => n.getMesh());
  for (const n of noeuds) {
    const m = n.getWorldMatrix();
    for (const p of n.getMesh()!.listPrimitives() as Primitive[]) {
      if (p.getMode() !== 4) continue; // triangles seulement
      const P = p.getAttribute('POSITION');
      if (!P) continue;
      const base = pos.length / 3;
      const t = [0, 0, 0];
      for (let i = 0; i < P.getCount(); i++) {
        P.getElement(i, t);
        pos.push(m[0] * t[0] + m[4] * t[1] + m[8] * t[2] + m[12], m[1] * t[0] + m[5] * t[1] + m[9] * t[2] + m[13], m[2] * t[0] + m[6] * t[1] + m[10] * t[2] + m[14]);
      }
      const U = p.getAttribute('TEXCOORD_0');
      if (U) {
        const u = [0, 0];
        for (let i = 0; i < U.getCount(); i++) { U.getElement(i, u); uv.push(u[0], u[1]); }
      } else { aUv = false; for (let i = 0; i < P.getCount(); i++) uv.push(0, 0); }
      const I = p.getIndices();
      if (I) { for (let i = 0; i < I.getCount(); i++) idx.push(base + I.getScalar(i)); }
      else { for (let i = 0; i < P.getCount(); i++) idx.push(base + i); }
      const tex = p.getMaterial()?.getBaseColorTexture();
      if (!couleur && tex?.getImage()) couleur = { octets: tex.getImage()!, mime: tex.getMimeType() || 'image/png' };
    }
  }
  return { positions: Float32Array.from(pos), uvs: aUv ? Float32Array.from(uv) : null, indices: Uint32Array.from(idx), couleur };
}

// ---------- contrôle ----------

/** Clé d'un sommet par position (les coutures d'UV dupliquent les sommets sans ouvrir la surface). */
function sommetsSoudes(m: Maillage): Uint32Array {
  const carte = new Map<string, number>();
  const sortie = new Uint32Array(m.positions.length / 3);
  const q = 1e5;
  for (let i = 0; i < sortie.length; i++) {
    const k = `${Math.round(m.positions[3 * i] * q)},${Math.round(m.positions[3 * i + 1] * q)},${Math.round(m.positions[3 * i + 2] * q)}`;
    let v = carte.get(k);
    if (v === undefined) { v = carte.size; carte.set(k, v); }
    sortie[i] = v;
  }
  return sortie;
}

/** Identifie une arête non orientée : a et b sont des indices Uint32 dans [0, nombreSommets). */
export function cleArete(a: number, b: number, nombreSommets: number): number | bigint {
  const bas = Math.min(a, b), haut = Math.max(a, b);
  // Tant que nombreSommets² reste dans les entiers exacts, une clé numérique est rapide.
  // Au-delà, deux indices Uint32 restent représentables sans perte dans une clé BigInt.
  if (nombreSommets <= 94_906_265) return bas * nombreSommets + haut;
  return (BigInt(bas) << 32n) | BigInt(haut);
}

export function analyser(m: Maillage): RapportMaillage {
  const soude = sommetsSoudes(m);
  const nTri = m.indices.length / 3;
  const aretes = new Map<number | bigint, number>();
  // union-find sur les sommets soudés
  const nbSoudes = soude.reduce((x, y) => (y > x ? y : x), 0) + 1;
  const cle = (a: number, b: number) => cleArete(a, b, nbSoudes);
  const p = new Int32Array(nbSoudes).map((_, i) => i);
  const racine = (x: number): number => { while (p[x] !== x) { p[x] = p[p[x]]; x = p[x]; } return x; };
  let degeneres = 0;
  const utilises = new Uint8Array(nbSoudes);
  let volume6 = 0;
  for (let t = 0; t < nTri; t++) {
    const a = soude[m.indices[3 * t]], b = soude[m.indices[3 * t + 1]], c = soude[m.indices[3 * t + 2]];
    const ia = m.indices[3 * t] * 3, ib = m.indices[3 * t + 1] * 3, ic = m.indices[3 * t + 2] * 3;
    const ux = m.positions[ib] - m.positions[ia], uy = m.positions[ib + 1] - m.positions[ia + 1], uz = m.positions[ib + 2] - m.positions[ia + 2];
    const vx = m.positions[ic] - m.positions[ia], vy = m.positions[ic + 1] - m.positions[ia + 1], vz = m.positions[ic + 2] - m.positions[ia + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    if (a === b || b === c || a === c || nx * nx + ny * ny + nz * nz < 1e-18) { degeneres++; continue; }
    for (const [x, y] of [[a, b], [b, c], [c, a]] as const) { const k = cle(x, y); aretes.set(k, (aretes.get(k) ?? 0) + 1); }
    utilises[a] = utilises[b] = utilises[c] = 1;
    p[racine(a)] = racine(b); p[racine(b)] = racine(c);
    volume6 += m.positions[ia] * (m.positions[ib + 1] * m.positions[ic + 2] - m.positions[ib + 2] * m.positions[ic + 1])
      - m.positions[ia + 1] * (m.positions[ib] * m.positions[ic + 2] - m.positions[ib + 2] * m.positions[ic])
      + m.positions[ia + 2] * (m.positions[ib] * m.positions[ic + 1] - m.positions[ib + 1] * m.positions[ic]);
  }
  let ouvertes = 0, nonVariete = 0;
  for (const n of aretes.values()) { if (n === 1) ouvertes++; else if (n > 2) nonVariete++; }
  const racines = new Set<number>();
  for (let i = 0; i < nbSoudes; i++) if (utilises[i]) racines.add(racine(i));
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < m.positions.length; i += 3) for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], m.positions[i + k]); max[k] = Math.max(max[k], m.positions[i + k]); }
  const etanche = nTri > 0 && ouvertes === 0 && nonVariete === 0 && degeneres === 0;
  const avertissements: string[] = [];
  if (nTri === 0) avertissements.push('Maillage vide.');
  if (ouvertes > 0) avertissements.push(`${ouvertes} arêtes ouvertes : le modèle n’est pas étanche (impression 3D : à réparer).`);
  if (nonVariete > 0) avertissements.push(`${nonVariete} arêtes partagées par plus de deux faces (non-variété).`);
  if (degeneres > 0) avertissements.push(`${degeneres} triangles dégénérés.`);
  if (etanche && racines.size > 1) avertissements.push('Volume non calculé : plusieurs composantes fermées peuvent représenter des solides distincts ou des cavités imbriquées.');
  if (racines.size > 1) avertissements.push(`${racines.size} morceaux séparés (fragments flottants possibles).`);
  return {
    sommets: m.positions.length / 3, triangles: nTri, degeneres, aretesOuvertes: ouvertes, aretesNonVariete: nonVariete,
    composantes: racines.size, etanche,
    taille: nTri ? [max[0] - min[0], max[1] - min[1], max[2] - min[2]] : [0, 0, 0],
    volume: etanche && racines.size === 1 ? Math.abs(volume6) / 6 : null, avertissements,
  };
}

// ---------- décimation ----------

let simplifierPret: Promise<void> | null = null;

/** Nombre de triangles voulu borné ; null = ne pas décimer. */
export function cibleTriangles(valeur: unknown, actuels: number): number | null {
  const n = Math.floor(Number(valeur));
  if (!Number.isFinite(n) || n <= 0) return null;
  const cible = Math.max(FACES_MIN, Math.min(FACES_MAX, n));
  return cible >= actuels ? null : cible;
}

/** Réduit le GLB à environ `cible` triangles en gardant les UV, la texture et les bords (meshoptimizer). */
export async function decimerGlb(glb: Uint8Array, cible: number): Promise<Uint8Array> {
  simplifierPret ??= MeshoptSimplifier.ready;
  await simplifierPret;
  const doc = await io.readBinary(glb);
  const avant = maillageDuDocument(doc).indices.length / 3;
  const transformations: Transform[] = [
    weld(),
    simplify({ simplifier: MeshoptSimplifier, ratio: Math.max(0.001, Math.min(1, cible / Math.max(1, avant))), error: 0.05, lockBorder: false }),
  ];
  await doc.transform(...transformations);
  return io.writeBinary(doc);
}

// ---------- exports ----------

const f = (x: number) => (Math.abs(x) < 1e-9 ? '0' : String(+x.toFixed(6)));

export interface OptionsExport { nom?: string; tailleMm?: number }
const nomSur = (n?: string) => (n ?? 'relief').replace(/[^A-Za-z0-9_-]+/g, '_').slice(0, 40) || 'relief';
const extensionImage = (mime: string) => (mime.includes('jpeg') ? 'jpg' : 'png');

/** Dimension la plus grande ramenée à `tailleMm` millimètres, posé à plat sur Z=0 et centré (impression). */
function pourImpression(m: Maillage, tailleMm: number): Float32Array {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < m.positions.length; i += 3) for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], m.positions[i + k]); max[k] = Math.max(max[k], m.positions[i + k]); }
  const grand = Math.max(max[0] - min[0], max[1] - min[1], max[2] - min[2]) || 1;
  const echelle = tailleMm / grand;
  const sortie = new Float32Array(m.positions.length);
  // Z vers le haut pour les trancheurs : Y (haut glTF) devient Z, Z devient -Y.
  for (let i = 0; i < m.positions.length; i += 3) {
    const x = (m.positions[i] - (min[0] + max[0]) / 2) * echelle, y = (m.positions[i + 1] - min[1]) * echelle, z = (m.positions[i + 2] - (min[2] + max[2]) / 2) * echelle;
    sortie[i] = x; sortie[i + 1] = -z; sortie[i + 2] = y;
  }
  return sortie;
}

/** Zip sans compression dont chaque fichier démarre sur un multiple de 64 octets (obligatoire pour USDZ). */
export function zipAligne(fichiers: { nom: string; octets: Uint8Array }[]): Uint8Array {
  const morceaux: Uint8Array[] = [];
  const centrale: Uint8Array[] = [];
  let pos = 0;
  const u16 = (v: number) => [v & 255, (v >> 8) & 255];
  const u32 = (v: number) => [v & 255, (v >>> 8) & 255, (v >>> 16) & 255, (v >>> 24) & 255];
  for (const { nom, octets } of fichiers) {
    const n = strToU8(nom);
    const entete = 30 + n.length;
    const bourrage = (64 - ((pos + entete + 4) % 64)) % 64; // 4 octets d'en-tête du champ supplémentaire
    const extra = bourrage + 4;
    const c = crc32(octets) >>> 0;
    const local = Uint8Array.from([0x50, 0x4b, 3, 4, ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0x21), ...u32(c), ...u32(octets.length), ...u32(octets.length), ...u16(n.length), ...u16(extra), ...n, 0x55, 0x53, ...u16(bourrage), ...new Array(bourrage).fill(0)]);
    centrale.push(Uint8Array.from([0x50, 0x4b, 1, 2, ...u16(20), ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0x21), ...u32(c), ...u32(octets.length), ...u32(octets.length), ...u16(n.length), ...u16(0), ...u16(0), ...u16(0), ...u16(0), ...u32(0), ...u32(pos), ...n]));
    morceaux.push(local, octets);
    pos += local.length + octets.length;
  }
  const taille = centrale.reduce((s, c) => s + c.length, 0);
  const fin = Uint8Array.from([0x50, 0x4b, 5, 6, 0, 0, 0, 0, ...u16(fichiers.length), ...u16(fichiers.length), ...u32(taille), ...u32(pos), 0, 0]);
  const tout = new Uint8Array(pos + taille + fin.length);
  let o = 0;
  for (const c of [...morceaux, ...centrale, fin]) { tout.set(c, o); o += c.length; }
  return tout;
}

export function versObj(m: Maillage, opt: OptionsExport = {}): Uint8Array {
  const nom = nomSur(opt.nom);
  const lignes: string[] = [`# Relief : ${nom}`, `mtllib ${nom}.mtl`, `o ${nom}`];
  const n = m.positions.length / 3;
  for (let i = 0; i < n; i++) lignes.push(`v ${f(m.positions[3 * i])} ${f(m.positions[3 * i + 1])} ${f(m.positions[3 * i + 2])}`);
  if (m.uvs) for (let i = 0; i < n; i++) lignes.push(`vt ${f(m.uvs[2 * i])} ${f(1 - m.uvs[2 * i + 1])}`);
  lignes.push('usemtl matiere');
  for (let t = 0; t < m.indices.length; t += 3) {
    const [a, b, c] = [m.indices[t] + 1, m.indices[t + 1] + 1, m.indices[t + 2] + 1];
    lignes.push(m.uvs ? `f ${a}/${a} ${b}/${b} ${c}/${c}` : `f ${a} ${b} ${c}`);
  }
  const fichiers: Record<string, Uint8Array> = {};
  const ext = m.couleur ? extensionImage(m.couleur.mime) : '';
  fichiers[`${nom}.obj`] = strToU8(lignes.join('\n') + '\n');
  fichiers[`${nom}.mtl`] = strToU8(`newmtl matiere\nKa 1 1 1\nKd 1 1 1\nKs 0 0 0\nd 1\nillum 1\n${m.couleur ? `map_Kd ${nom}.${ext}\n` : ''}`);
  if (m.couleur) fichiers[`${nom}.${ext}`] = m.couleur.octets;
  return zipSync(fichiers, { level: 0 });
}

/** STL binaire, en millimètres, Z vers le haut, posé sur le plateau. */
export function versStl(m: Maillage, opt: OptionsExport = {}): Uint8Array {
  const p = pourImpression(m, opt.tailleMm ?? TAILLE_MM_DEFAUT);
  const nTri = m.indices.length / 3;
  const tampon = new ArrayBuffer(84 + 50 * nTri);
  const vue = new DataView(tampon);
  new Uint8Array(tampon).set(strToU8('Nexora Relief'), 0);
  vue.setUint32(80, nTri, true);
  let o = 84;
  for (let t = 0; t < nTri; t++) {
    const a = m.indices[3 * t] * 3, b = m.indices[3 * t + 1] * 3, c = m.indices[3 * t + 2] * 3;
    const ux = p[b] - p[a], uy = p[b + 1] - p[a + 1], uz = p[b + 2] - p[a + 2], vx = p[c] - p[a], vy = p[c + 1] - p[a + 1], vz = p[c + 2] - p[a + 2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const l = Math.hypot(nx, ny, nz) || 1; nx /= l; ny /= l; nz /= l;
    for (const v of [nx, ny, nz, p[a], p[a + 1], p[a + 2], p[b], p[b + 1], p[b + 2], p[c], p[c + 1], p[c + 2]]) { vue.setFloat32(o, v, true); o += 4; }
    vue.setUint16(o, 0, true); o += 2;
  }
  return new Uint8Array(tampon);
}

/** 3MF (géométrie seule, millimètres, Z vers le haut) : le format que lisent les trancheurs récents. */
export function vers3mf(m: Maillage, opt: OptionsExport = {}): Uint8Array {
  const p = pourImpression(m, opt.tailleMm ?? TAILLE_MM_DEFAUT);
  const sommets: string[] = [];
  for (let i = 0; i < p.length; i += 3) sommets.push(`<vertex x="${f(p[i])}" y="${f(p[i + 1])}" z="${f(p[i + 2])}"/>`);
  const triangles: string[] = [];
  for (let t = 0; t < m.indices.length; t += 3) triangles.push(`<triangle v1="${m.indices[t]}" v2="${m.indices[t + 1]}" v3="${m.indices[t + 2]}"/>`);
  const modele = `<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="fr-FR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Title">${nomSur(opt.nom)}</metadata><metadata name="Application">Nexora Relief</metadata><resources><object id="1" type="model"><mesh><vertices>${sommets.join('')}</vertices><triangles>${triangles.join('')}</triangles></mesh></object></resources><build><item objectid="1"/></build></model>`;
  return zipSync({
    '[Content_Types].xml': strToU8('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'),
    '_rels/.rels': strToU8('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'),
    '3D/3dmodel.model': strToU8(modele),
  }, { level: 6 });
}

/** USDZ (Apple : Quick Look, Vision Pro) : un USDA et la texture, zip non compressé aligné sur 64 octets. */
export function versUsdz(m: Maillage, opt: OptionsExport = {}): Uint8Array {
  const nom = nomSur(opt.nom);
  const n = m.positions.length / 3;
  const pts: string[] = [];
  for (let i = 0; i < n; i++) pts.push(`(${f(m.positions[3 * i])}, ${f(m.positions[3 * i + 1])}, ${f(m.positions[3 * i + 2])})`);
  const nbFaces = m.indices.length / 3;
  const ext = m.couleur ? extensionImage(m.couleur.mime) : 'png';
  const st = m.uvs ? Array.from({ length: n }, (_, i) => `(${f(m.uvs![2 * i])}, ${f(m.uvs![2 * i + 1])})`) : [];
  const usda = `#usda 1.0
(
    defaultPrim = "${nom}"
    metersPerUnit = 1
    upAxis = "Y"
)

def Xform "${nom}" (kind = "component")
{
    def Mesh "maillage"
    {
        int[] faceVertexCounts = [${Array(nbFaces).fill(3).join(', ')}]
        int[] faceVertexIndices = [${Array.from(m.indices).join(', ')}]
        point3f[] points = [${pts.join(', ')}]
        uniform token subdivisionScheme = "none"
        ${m.uvs ? `texCoord2f[] primvars:st = [${st.join(', ')}] (interpolation = "vertex")` : ''}
        rel material:binding = </${nom}/Materiaux/matiere>
    }
    def Scope "Materiaux"
    {
        def Material "matiere"
        {
            token outputs:surface.connect = </${nom}/Materiaux/matiere/surface.outputs:surface>
            def Shader "surface"
            {
                uniform token info:id = "UsdPreviewSurface"
                ${m.couleur ? `color3f inputs:diffuseColor.connect = </${nom}/Materiaux/matiere/texture.outputs:rgb>` : 'color3f inputs:diffuseColor = (0.8, 0.8, 0.8)'}
                float inputs:roughness = 0.7
                float inputs:metallic = 0
                token outputs:surface
            }
            ${m.couleur ? `def Shader "texture"
            {
                uniform token info:id = "UsdUVTexture"
                asset inputs:file = @couleur.${ext}@
                float2 inputs:st.connect = </${nom}/Materiaux/matiere/coord.outputs:result>
                token inputs:sourceColorSpace = "sRGB"
                float3 outputs:rgb
            }
            def Shader "coord"
            {
                uniform token info:id = "UsdPrimvarReader_float2"
                token inputs:varname = "st"
                float2 outputs:result
            }` : ''}
        }
    }
}
`;
  const fichiers: { nom: string; octets: Uint8Array }[] = [{ nom: `${nom}.usda`, octets: strToU8(usda) }];
  if (m.couleur) fichiers.push({ nom: `couleur.${ext}`, octets: m.couleur.octets });
  return zipAligne(fichiers);
}

/** Le fichier du format voulu, depuis un GLB (décimé d'abord si `cible` est donné). */
export async function exporter(glb: Uint8Array, format: FormatRelief, opt: OptionsExport & { cible?: number | null } = {}): Promise<Uint8Array> {
  const source = opt.cible ? await decimerGlb(glb, opt.cible) : glb;
  if (format === 'glb') return source;
  const m = await lireGlb(source);
  if (format === 'obj') return versObj(m, opt);
  if (format === 'stl') return versStl(m, opt);
  if (format === '3mf') return vers3mf(m, opt);
  return versUsdz(m, opt);
}

/** Cartes PBR d'un GLB (couleur, métal/rugosité, normales, occlusion, émission) : octets des images présentes. */
export async function cartesPbr(glb: Uint8Array): Promise<{ nom: string; mime: string; octets: Uint8Array; largeur: number | null }[]> {
  const doc = await io.readBinary(glb);
  const sortie: { nom: string; mime: string; octets: Uint8Array; largeur: number | null }[] = [];
  const vues = new Set<string>();
  for (const mat of doc.getRoot().listMaterials()) {
    const liste: [string, ReturnType<typeof mat.getBaseColorTexture>][] = [
      ['couleur', mat.getBaseColorTexture()], ['metal-rugosite', mat.getMetallicRoughnessTexture()], ['normales', mat.getNormalTexture()],
      ['occlusion', mat.getOcclusionTexture()], ['emission', mat.getEmissiveTexture()],
    ];
    for (const [nom, tex] of liste) {
      const img = tex?.getImage();
      if (!tex || !img || vues.has(nom)) continue;
      vues.add(nom);
      const taille = tex.getSize();
      sortie.push({ nom, mime: tex.getMimeType() || 'image/png', octets: img, largeur: taille ? taille[0] : null });
    }
  }
  return sortie;
}
