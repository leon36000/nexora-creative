/**
 * Nexora Mesh (mode 3D de Nexora Creative ; ex-Relief, ex-Object) : tout ce qui travaille sur le maillage d'un GLB, côté serveur et sans GPU.
 * Lecture du GLB, contrôle (étanchéité, arêtes non-variété, composantes, nombre de triangles), décimation à un nombre de
 * triangles voulu (meshoptimizer), exports OBJ (+ MTL + texture), STL binaire, 3MF et USDZ. Tout est pur et testé sans moteur.
 * Nom du produit : shared/productNames.ts. Rapport : recherche/18 ; mesures : recherche/21.
 */
import { NEXORA_PRODUCT_NAMES } from '../../shared/productNames.js';
import { crc32 } from 'node:zlib';
import type { FastifyReply } from 'fastify';
import { Document, NodeIO, type Primitive, type Texture, type Transform } from '@gltf-transform/core';
import { simplify, weld } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import { zipSync, strToU8 } from 'fflate';
import { Matrix3, Matrix4, Vector3 } from 'three';
import { exporterUsdz, verifierGlbUsdz } from './usdz.js';

export const CODE_OBJ_INCOMPATIBLE = 'OBJ_UNSUPPORTED' as const;

export class ObjIncompatible extends Error {
  readonly code = CODE_OBJ_INCOMPATIBLE;
}

/** Réponse stable pour les clients qui téléchargent directement sans passer par l'interface. */
export function repondreObjIncompatible(reply: FastifyReply) {
  return reply.code(400).send({ code: CODE_OBJ_INCOMPATIBLE, error: 'Export OBJ incompatible avec les textures, les coordonnées UV ou les normales de ce modèle. Utilisez le GLB.' });
}

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
  positions: Float32Array | Float64Array;
  /** Coordonnées de texture (2 par sommet) ; null si le modèle n'en a pas. */
  uvs: Float32Array | null;
  indices: Uint32Array;
  /** Image de la couleur de base (PNG ou JPEG) et son type. */
  couleur: { octets: Uint8Array; mime: string } | null;
  /** Données OBJ par primitive ; absentes pour les maillages construits directement. */
  partiesObj?: PartieObj[];
  uvsObj?: Float32Array;
  normalesObj?: Float32Array;
  indicesObj?: Uint32Array;
  normalesCoinsObj?: Map<number, [number, number, number]>;
}

interface PartieObj {
  debut: number; fin: number; base: number; sommets: number; aUv: boolean; aNormale: boolean;
  facteur: readonly number[]; alphaMode: string;
  texture: { octets: Uint8Array; mime: string } | null;
  erreur: string | null;
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
  /** Volume (unité³) si une composante fermée et orientée de façon cohérente a un volume calculable ; null sinon. */
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
  const uvObj: number[] = [];
  const normalesObj: number[] = [];
  const indicesObj: number[] = [];
  const normalesCoinsObj = new Map<number, [number, number, number]>();
  const partiesObj: PartieObj[] = [];
  let aUv = true;
  let couleur: Maillage['couleur'] = null;
  const racine = doc.getRoot();
  const noeuds = racine.listNodes().filter((n) => n.getMesh());
  for (const n of noeuds) {
    const m = n.getWorldMatrix();
    const matrice = new Matrix4().fromArray(m);
    const determinant = matrice.determinant();
    const matriceNormale = new Matrix3().getNormalMatrix(matrice);
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
      const mat = p.getMaterial();
      const tex = mat?.getBaseColorTexture();
      const info = mat?.getBaseColorTextureInfo();
      const uvPourObj = p.getAttribute(`TEXCOORD_${tex ? info?.getTexCoord() ?? 0 : 0}`);
      const uvValides = !!uvPourObj && uvPourObj.getCount() === P.getCount();
      const coord = [0, 0];
      let uvFinies = true;
      for (let i = 0; i < P.getCount(); i++) {
        if (uvValides) uvPourObj!.getElement(i, coord);
        if (uvValides && (!Number.isFinite(coord[0]) || !Number.isFinite(coord[1]))) uvFinies = false;
        uvObj.push(uvValides ? coord[0] : 0, uvValides ? coord[1] : 0);
      }
      const debut = idx.length;
      const I = p.getIndices();
      if (I) { for (let i = 0; i < I.getCount(); i++) idx.push(base + I.getScalar(i)); }
      else { for (let i = 0; i < P.getCount(); i++) idx.push(base + i); }
      for (let i = debut; i < idx.length; i += 3) {
        // Un reflet inverse l'orientation géométrique : la rétablir pour tous les exports.
        if (determinant < 0 && i + 2 < idx.length) [idx[i + 1], idx[i + 2]] = [idx[i + 2], idx[i + 1]];
        indicesObj.push(idx[i], idx[i + 1], idx[i + 2]);
      }
      const image = tex?.getImage();
      const mime = tex?.getMimeType() || '';
      let erreur: string | null = null;
      const N = p.getAttribute('NORMAL');
      const aNormale = !!N && N.getType() === 'VEC3' && N.getArray() instanceof Float32Array && N.getCount() === P.getCount();
      if (N && (!aNormale || !Number.isFinite(determinant) || determinant === 0)) erreur = 'Normales OBJ ou transformation invalides.';
      const normale = [0, 0, 0];
      const v = new Vector3();
      let normalesNulles = false;
      for (let i = 0; i < P.getCount(); i++) {
        if (!aNormale || erreur) { normalesObj.push(0, 0, 0); continue; }
        N!.getElement(i, normale);
        if (normale.every((x) => x === 0)) { normalesObj.push(0, 0, 0); normalesNulles = true; continue; }
        v.set(normale[0], normale[1], normale[2]).applyMatrix3(matriceNormale);
        if (![v.x, v.y, v.z, v.lengthSq()].every(Number.isFinite) || v.lengthSq() === 0) erreur = 'Normale OBJ non finie ou nulle.';
        v.normalize();
        normalesObj.push(v.x, v.y, v.z);
      }
      if (normalesNulles && !erreur) {
        const a = new Vector3(), b = new Vector3(), c = new Vector3(), face = new Vector3();
        for (let t = debut; t < idx.length; t += 3) {
          const coins = indicesObj.slice(t, t + 3);
          const manque = coins.map((s) => normalesObj[3 * s] === 0 && normalesObj[3 * s + 1] === 0 && normalesObj[3 * s + 2] === 0);
          if (!manque.some(Boolean)) continue;
          a.fromArray(pos, 3 * coins[0]); b.fromArray(pos, 3 * coins[1]); c.fromArray(pos, 3 * coins[2]);
          face.subVectors(b, a).cross(c.sub(a));
          if (![face.x, face.y, face.z, face.lengthSq()].every(Number.isFinite) || face.lengthSq() === 0) {
            erreur = 'Normale nulle sur une face OBJ dégénérée.'; break;
          }
          face.normalize();
          for (let coin = 0; coin < 3; coin++) if (manque[coin]) normalesCoinsObj.set(t + coin, [face.x, face.y, face.z]);
        }
      }
      if (!erreur && !uvFinies) erreur = 'Coordonnées UV OBJ non finies.';
      else if (tex && (!image || !uvValides)) erreur = 'Texture de base sans image ou coordonnées UV utilisables.';
      else if (tex && mime !== 'image/png' && mime !== 'image/jpeg') erreur = 'Texture OBJ : seuls PNG et JPEG sont pris en charge.';
      else if (info && info.listExtensions().length) erreur = 'Transformation de texture OBJ non prise en charge.';
      partiesObj.push({ debut, fin: idx.length, base, sommets: P.getCount(), aUv: uvValides, aNormale, facteur: mat?.getBaseColorFactor() ?? [1, 1, 1, 1],
        alphaMode: mat?.getAlphaMode() ?? 'OPAQUE', texture: image ? { octets: image, mime } : null, erreur });
      if (!couleur && image) couleur = { octets: image, mime: mime || 'image/png' };
    }
  }
  return { positions: Float64Array.from(pos), uvs: aUv ? Float32Array.from(uv) : null, indices: Uint32Array.from(idx), couleur, partiesObj, uvsObj: Float32Array.from(uvObj), normalesObj: Float32Array.from(normalesObj), indicesObj: Uint32Array.from(indicesObj), normalesCoinsObj };
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

/** Refuse les géométries qui rendraient les mesures de topologie ou de boîte englobante trompeuses. */
function validerGeometrie(m: Maillage): void {
  if (m.positions.length % 3 !== 0) throw new Error('Maillage invalide : la longueur des positions doit être un multiple de 3.');
  if (m.indices.length % 3 !== 0) throw new Error('Maillage invalide : la longueur des indices doit être un multiple de 3.');
  for (let i = 0; i < m.positions.length; i++) {
    if (!Number.isFinite(m.positions[i])) throw new Error(`Maillage invalide : coordonnée de position non finie à l’offset ${i}.`);
  }
  const sommets = m.positions.length / 3;
  for (let i = 0; i < m.indices.length; i++) {
    if (m.indices[i] >= sommets) throw new Error(`Maillage invalide : indice ${m.indices[i]} hors plage (${sommets} sommets).`);
  }
}

export function analyser(m: Maillage): RapportMaillage {
  validerGeometrie(m);
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
  let ancrage: [number, number, number] | null = null;
  for (let t = 0; t < nTri; t++) {
    const a = soude[m.indices[3 * t]], b = soude[m.indices[3 * t + 1]], c = soude[m.indices[3 * t + 2]];
    const ia = m.indices[3 * t] * 3, ib = m.indices[3 * t + 1] * 3, ic = m.indices[3 * t + 2] * 3;
    const ux = m.positions[ib] - m.positions[ia], uy = m.positions[ib + 1] - m.positions[ia + 1], uz = m.positions[ib + 2] - m.positions[ia + 2];
    const vx = m.positions[ic] - m.positions[ia], vy = m.positions[ic + 1] - m.positions[ia + 1], vz = m.positions[ic + 2] - m.positions[ia + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    if (a === b || b === c || a === c || nx * nx + ny * ny + nz * nz < 1e-18) { degeneres++; continue; }
    for (const [x, y] of [[a, b], [b, c], [c, a]] as const) {
      const k = cle(x, y), sens = x < y ? 1 : -1, precedent = aretes.get(k);
      if (precedent === undefined) aretes.set(k, sens);
      else if (Math.abs(precedent) === 1) aretes.set(k, precedent === -sens ? 2 : -2);
      else if (Math.abs(precedent) === 2) aretes.set(k, 3);
    }
    utilises[a] = utilises[b] = utilises[c] = 1;
    p[racine(a)] = racine(b); p[racine(b)] = racine(c);
    ancrage ??= [m.positions[ia], m.positions[ia + 1], m.positions[ia + 2]];
    const ax = m.positions[ia] - ancrage[0], ay = m.positions[ia + 1] - ancrage[1], az = m.positions[ia + 2] - ancrage[2];
    const bx = m.positions[ib] - ancrage[0], by = m.positions[ib + 1] - ancrage[1], bz = m.positions[ib + 2] - ancrage[2];
    const cx = m.positions[ic] - ancrage[0], cy = m.positions[ic + 1] - ancrage[1], cz = m.positions[ic + 2] - ancrage[2];
    volume6 += ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx);
  }
  let ouvertes = 0, nonVariete = 0, orientationIncoherente = false;
  for (const etat of aretes.values()) {
    if (Math.abs(etat) === 1) ouvertes++;
    else if (Math.abs(etat) === 3) nonVariete++;
    else if (etat === -2) orientationIncoherente = true;
  }
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
  if (etanche && orientationIncoherente) avertissements.push('Volume non calculé : orientation incohérente des faces.');
  if (etanche && racines.size > 1) avertissements.push('Volume non calculé : plusieurs composantes fermées peuvent représenter des solides distincts ou des cavités imbriquées.');
  if (racines.size > 1) avertissements.push(`${racines.size} morceaux séparés (fragments flottants possibles).`);
  return {
    sommets: m.positions.length / 3, triangles: nTri, degeneres, aretesOuvertes: ouvertes, aretesNonVariete: nonVariete,
    composantes: racines.size, etanche,
    taille: nTri ? [max[0] - min[0], max[1] - min[1], max[2] - min[2]] : [0, 0, 0],
    volume: etanche && racines.size === 1 && !orientationIncoherente ? Math.abs(volume6) / 6 : null, avertissements,
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
  if (m.partiesObj) return versObjAvecMatieres(m, nom);
  const lignes: string[] = [`# ${NEXORA_PRODUCT_NAMES.mesh} : ${nom}`, `mtllib ${nom}.mtl`, `o ${nom}`];
  const n = m.positions.length / 3;
  for (let i = 0; i < n; i++) lignes.push(`v ${f(m.positions[3 * i])} ${f(m.positions[3 * i + 1])} ${f(m.positions[3 * i + 2])}`);
  if (m.uvs) for (let i = 0; i < n; i++) lignes.push(`vt ${f(m.uvs[2 * i])} ${f(1 - m.uvs[2 * i + 1])}`);
  lignes.push('usemtl matiere', 's off');
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

/** OBJ/MTL : une affectation de matériau par primitive, sans prétention d'export PBR complet. */
function versObjAvecMatieres(m: Maillage, nom: string): Uint8Array {
  const parties = m.partiesObj!;
  const lignes = [`# ${NEXORA_PRODUCT_NAMES.mesh} : ${nom}`, `mtllib ${nom}.mtl`, `o ${nom}`];
  const n = m.positions.length / 3;
  for (let i = 0; i < n; i++) lignes.push(`v ${f(m.positions[3 * i])} ${f(m.positions[3 * i + 1])} ${f(m.positions[3 * i + 2])}`);
  if (parties.some((p) => p.aUv)) {
    const uv = m.uvsObj!;
    for (let i = 0; i < n; i++) lignes.push(`vt ${f(uv[2 * i])} ${f(1 - uv[2 * i + 1])}`);
  }
  const indexNormales = new Map<number, number>();
  const indexNormalesCoins = new Map<number, number>();
  const normales = m.normalesObj!;
  for (const partie of parties) if (partie.aNormale && !partie.erreur) {
    for (let i = partie.base; i < partie.base + partie.sommets; i++) {
      if (normales[3 * i] === 0 && normales[3 * i + 1] === 0 && normales[3 * i + 2] === 0) continue;
      indexNormales.set(i + 1, indexNormales.size + 1);
      lignes.push(`vn ${f(normales[3 * i])} ${f(normales[3 * i + 1])} ${f(normales[3 * i + 2])}`);
    }
  }
  for (const [coin, normale] of m.normalesCoinsObj ?? []) {
    indexNormalesCoins.set(coin, indexNormales.size + indexNormalesCoins.size + 1);
    lignes.push(`vn ${normale.map(f).join(' ')}`);
  }
  if (indexNormalesCoins.size) lignes.push(`# ${indexNormalesCoins.size} normales de coin calculées depuis les faces pour remplacer des normales nulles`);
  const fichiers: Record<string, Uint8Array> = {};
  const definitions: string[] = [];
  for (let i = 0; i < parties.length; i++) {
    const partie = parties[i];
    if (partie.erreur) throw new ObjIncompatible(partie.erreur);
    const mat = parties.length === 1 ? 'matiere' : `matiere_${i}`;
    lignes.push(`usemtl ${mat}`);
    lignes.push(partie.aNormale ? 's 1' : 's off');
    for (let t = partie.debut; t < partie.fin; t += 3) {
      const idx = m.indicesObj!;
      const sommets = [idx[t] + 1, idx[t + 1] + 1, idx[t + 2] + 1];
      const face = sommets.map((s, coin) => {
        const normale = indexNormales.get(s) ?? indexNormalesCoins.get(t + coin);
        return partie.aNormale ? (partie.aUv ? `${s}/${s}/${normale}` : `${s}//${normale}`) : (partie.aUv ? `${s}/${s}` : `${s}`);
      });
      lignes.push(`f ${face.join(' ')}`);
    }
    let map = '';
    if (partie.texture) {
      const fichier = `${nom}${parties.length === 1 ? '' : `_${i}`}.${extensionImage(partie.texture.mime)}`;
      fichiers[fichier] = partie.texture.octets;
      map = `map_Kd ${fichier}\n`;
    }
    const alpha = partie.alphaMode === 'BLEND' ? partie.facteur[3] : 1;
    definitions.push(`newmtl ${mat}\nKa 1 1 1\nKd ${partie.facteur.slice(0, 3).map(f).join(' ')}\nKs 0 0 0\nd ${f(alpha)}\nillum 1\n${map}`);
  }
  fichiers[`${nom}.obj`] = strToU8(lignes.join('\n') + '\n');
  fichiers[`${nom}.mtl`] = strToU8(definitions.join(''));
  return zipSync(fichiers, { level: 0 });
}

/** Les anciennes versions restent en place ; les exports corrigés utilisent un nouveau cache. */
export function nomCacheExport(format: FormatRelief, cible: number | null, taille: number): string {
  const version = format === 'obj' ? '-normales-v4' : format === 'glb' ? '' : format === 'usdz' ? '-matieres-v3' : '-orientation-v3';
  return `export-${format}${version}-${cible ?? 'plein'}-${taille}.${EXTENSION_RELIEF[format]}`;
}

/** Sépare les rapports calculés après conservation de la précision des coordonnées monde. */
export function nomCacheRapport(cible: number | null): string {
  return `rapport-monde64-v1-${cible ?? 'plein'}.json`;
}

/** STL binaire, en millimètres, Z vers le haut, posé sur le plateau. */
export function versStl(m: Maillage, opt: OptionsExport = {}): Uint8Array {
  const p = pourImpression(m, opt.tailleMm ?? TAILLE_MM_DEFAUT);
  const nTri = m.indices.length / 3;
  const tampon = new ArrayBuffer(84 + 50 * nTri);
  const vue = new DataView(tampon);
  new Uint8Array(tampon).set(strToU8(NEXORA_PRODUCT_NAMES.mesh), 0);
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
  const modele = `<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="fr-FR" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Title">${nomSur(opt.nom)}</metadata><metadata name="Application">${NEXORA_PRODUCT_NAMES.mesh}</metadata><resources><object id="1" type="model"><mesh><vertices>${sommets.join('')}</vertices><triangles>${triangles.join('')}</triangles></mesh></object></resources><build><item objectid="1"/></build></model>`;
  return zipSync({
    '[Content_Types].xml': strToU8('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'),
    '_rels/.rels': strToU8('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'),
    '3D/3dmodel.model': strToU8(modele),
  }, { level: 6 });
}

/** Le fichier du format voulu, depuis un GLB (décimé d'abord si `cible` est donné). */
/** L'export OBJ ne sait pas appliquer KHR_texture_transform ; le refuser avant toute décimation. */
function refuserTransformationTextureObj(glb: Uint8Array): void {
  if (glb.byteLength < 20) throw new Error('GLB invalide.');
  const vue = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  const longueur = vue.getUint32(12, true);
  if (vue.getUint32(0, true) !== 0x46546c67 || vue.getUint32(16, true) !== 0x4e4f534a || longueur > glb.byteLength - 20) {
    throw new Error('GLB invalide.');
  }
  const json = JSON.parse(new TextDecoder().decode(glb.subarray(20, 20 + longueur))) as {
    materials?: { pbrMetallicRoughness?: { baseColorTexture?: { extensions?: Record<string, unknown> } } }[];
  };
  if (json.materials?.some((m) => m.pbrMetallicRoughness?.baseColorTexture?.extensions?.KHR_texture_transform != null)) {
    throw new ObjIncompatible('Transformation de texture OBJ non prise en charge.');
  }
}

/** Compatibilité avant téléchargement ; aucun export ni génération GPU n'est lancé. */
export function compatibiliteObj(glb: Uint8Array, m: Maillage): { compatible: boolean; code: typeof CODE_OBJ_INCOMPATIBLE | null } {
  try {
    refuserTransformationTextureObj(glb);
    const erreur = m.partiesObj?.find((partie) => partie.erreur)?.erreur;
    if (erreur) throw new ObjIncompatible(erreur);
    return { compatible: true, code: null };
  } catch (error) {
    if (error instanceof ObjIncompatible) return { compatible: false, code: CODE_OBJ_INCOMPATIBLE };
    throw error;
  }
}

export async function exporter(glb: Uint8Array, format: FormatRelief, opt: OptionsExport & { cible?: number | null } = {}): Promise<Uint8Array> {
  if (format === 'obj') refuserTransformationTextureObj(glb);
  if (format === 'usdz') verifierGlbUsdz(glb);
  const source = opt.cible ? await decimerGlb(glb, opt.cible) : glb;
  if (format === 'glb') return source;
  if (format === 'usdz') return exporterUsdz(source, opt.nom);
  const m = await lireGlb(source);
  if (format === 'obj') return versObj(m, opt);
  if (format === 'stl') return versStl(m, opt);
  return vers3mf(m, opt);
}

/** Cartes PBR d'un GLB (couleur, métal/rugosité, normales, occlusion, émission) : octets des images présentes. */
export async function cartesPbr(glb: Uint8Array): Promise<{ nom: string; mime: string; octets: Uint8Array; largeur: number | null; materiaux: { index: number; nom: string }[] }[]> {
  const doc = await io.readBinary(glb);
  const sortie: { nom: string; mime: string; octets: Uint8Array; largeur: number | null; materiaux: { index: number; nom: string }[] }[] = [];
  const vues = new Map<string, Map<Texture, (typeof sortie)[number]>>();
  for (const [index, mat] of doc.getRoot().listMaterials().entries()) {
    const liste: [string, ReturnType<typeof mat.getBaseColorTexture>][] = [
      ['couleur', mat.getBaseColorTexture()], ['metal-rugosite', mat.getMetallicRoughnessTexture()], ['normales', mat.getNormalTexture()],
      ['occlusion', mat.getOcclusionTexture()], ['emission', mat.getEmissiveTexture()],
    ];
    for (const [nom, tex] of liste) {
      const img = tex?.getImage();
      if (!tex || !img) continue;
      const dejaVues = vues.get(nom) ?? new Map<Texture, (typeof sortie)[number]>();
      const deja = dejaVues.get(tex);
      const materiau = { index: index + 1, nom: mat.getName() };
      if (deja) { deja.materiaux.push(materiau); continue; }
      const taille = tex.getSize();
      const carte = { nom: dejaVues.size === 0 ? nom : `${nom}-${dejaVues.size + 1}`, mime: tex.getMimeType() || 'image/png', octets: img, largeur: taille ? taille[0] : null, materiaux: [materiau] };
      dejaVues.set(tex, carte);
      vues.set(nom, dejaVues);
      sortie.push(carte);
    }
  }
  return sortie;
}
