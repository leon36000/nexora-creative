import { describe, expect, it } from 'vitest';
import Fastify from 'fastify';
import { Document, NodeIO } from '@gltf-transform/core';
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { unzipSync } from 'fflate';
import { NEXORA_PRODUCT_NAMES } from '../../shared/productNames.js';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { Mesh, Material } from 'three';
import { analyser, cartesPbr, cibleTriangles, cleArete, compatibiliteObj, decimerGlb, exporter, lireGlb, maillageDuDocument, nomCacheExport, nomCacheRapport, repondreObjIncompatible, versObj, versStl, vers3mf, zipAligne, type Maillage } from './relief.js';

/** Sphère UV (étanche une fois les sommets soudés), avec une texture 1×1 PNG. */
async function glbSphere(divisions = 24, ouvert = false): Promise<Uint8Array> {
  const doc = new Document();
  const buf = doc.createBuffer();
  const pos: number[] = [], uv: number[] = [], idx: number[] = [];
  for (let i = 0; i <= divisions; i++) for (let j = 0; j <= divisions; j++) {
    const th = (i / divisions) * Math.PI, ph = (j / divisions) * 2 * Math.PI;
    pos.push(Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph)); uv.push(j / divisions, i / divisions);
  }
  for (let i = 0; i < divisions; i++) for (let j = 0; j < divisions; j++) {
    const a = i * (divisions + 1) + j, b = a + divisions + 1;
    if (ouvert && i === 3 && j === 3) continue;
    idx.push(a, b, a + 1, a + 1, b, b + 1);
  }
  const png = Uint8Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64'));
  const tex = doc.createTexture('c').setImage(png).setMimeType('image/png');
  const mat = doc.createMaterial('m').setBaseColorTexture(tex);
  const prim = doc.createPrimitive().setMaterial(mat)
    .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(Float32Array.from(pos)).setBuffer(buf))
    .setAttribute('TEXCOORD_0', doc.createAccessor().setType('VEC2').setArray(Float32Array.from(uv)).setBuffer(buf))
    .setIndices(doc.createAccessor().setType('SCALAR').setArray(Uint32Array.from(idx)).setBuffer(buf));
  const node = doc.createNode('n').setMesh(doc.createMesh('mesh').addPrimitive(prim));
  doc.createScene().addChild(node);
  return new NodeIO().writeBinary(doc);
}

/** GLB minimal pour tester la lecture de géométries non conformes sans bricoler l'en-tête binaire. */
async function glbMaillage(positions: Float32Array, indices: Uint32Array): Promise<Uint8Array> {
  const doc = new Document();
  const buf = doc.createBuffer();
  const prim = doc.createPrimitive()
    .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(positions).setBuffer(buf))
    .setIndices(doc.createAccessor().setType('SCALAR').setArray(indices).setBuffer(buf));
  doc.createScene().addChild(doc.createNode().setMesh(doc.createMesh().addPrimitive(prim)));
  return new NodeIO().writeBinary(doc);
}

async function glbNormales(options: { normale?: number[]; echelle?: [number, number, number]; indices?: boolean; uv?: boolean; taille?: number } = {}): Promise<Uint8Array> {
  const doc = new Document(), buf = doc.createBuffer();
  const p = doc.createPrimitive().setAttribute('POSITION', doc.createAccessor().setType('VEC3')
    .setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf));
  if (options.normale) p.setAttribute('NORMAL', doc.createAccessor().setType('VEC3')
    .setArray(Float32Array.from(Array(options.taille ?? 3).fill(options.normale).flat())).setBuffer(buf));
  if (options.uv) p.setAttribute('TEXCOORD_0', doc.createAccessor().setType('VEC2')
    .setArray(new Float32Array([0, 0, 1, 0, 0, 1])).setBuffer(buf));
  if (options.indices) p.setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array([0, 1, 2])).setBuffer(buf));
  doc.createScene().addChild(doc.createNode().setScale(options.echelle ?? [1, 1, 1]).setMesh(doc.createMesh().addPrimitive(p)));
  return new NodeIO().writeBinary(doc);
}

describe('OBJ : normales et orientation', () => {
  for (const reflet of [false, true]) it(`combine rotation enfant et échelle parent, reflet=${reflet}`, async () => {
    const doc = new Document(), buf = doc.createBuffer();
    const n = 1 / Math.sqrt(3);
    const p = doc.createPrimitive()
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, -1, 0, 1, 0, -1])).setBuffer(buf))
      .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array([n, n, n, n, n, n, n, n, n])).setBuffer(buf))
      .setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array([0, 1, 2])).setBuffer(buf));
    const child = doc.createNode().setTranslation([1, 2, 3]).setRotation([0, 0, Math.SQRT1_2, Math.SQRT1_2]).setMesh(doc.createMesh().addPrimitive(p));
    doc.createScene().addChild(doc.createNode().setTranslation([4, 5, 6]).setScale([reflet ? -2 : 2, 3, 4]).addChild(child));
    const obj = new TextDecoder().decode(unzipSync(await exporter(await new NodeIO().writeBinary(doc), 'obj'))['relief.obj']);
    const normale = obj.split('\n').find((ligne) => ligne.startsWith('vn '))!.split(' ').slice(1).map(Number);
    const attendu = [reflet ? 6 : -6, 4, 3].map((x) => x / Math.sqrt(61));
    normale.forEach((x, i) => expect(x).toBeCloseTo(attendu[i], 5));
    const sommets = obj.split('\n').filter((ligne) => ligne.startsWith('v ')).map((ligne) => ligne.split(' ').slice(1).map(Number));
    const face = obj.split('\n').find((ligne) => ligne.startsWith('f '))!.split(' ').slice(1).map((s) => Number(s.split('/')[0]) - 1);
    const [a, b, c] = face.map((i) => sommets[i]);
    const u = b.map((x, i) => x - a[i]), v = c.map((x, i) => x - a[i]);
    expect(u.reduce((s, x, i) => s + x * normale[i], 0)).toBeCloseTo(0, 5);
    expect(v.reduce((s, x, i) => s + x * normale[i], 0)).toBeCloseTo(0, 5);
    const cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    expect(cross.reduce((s, x, i) => s + x * normale[i], 0)).toBeGreaterThan(0);
  });
  it('conserve les normales uniquement sur les primitives qui en possèdent', async () => {
    const doc = new Document(), buf = doc.createBuffer(), mesh = doc.createMesh();
    for (const avec of [false, true]) {
      const p = doc.createPrimitive().setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf));
      if (avec) p.setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1])).setBuffer(buf));
      mesh.addPrimitive(p);
    }
    doc.createScene().addChild(doc.createNode().setMesh(mesh));
    const obj = new TextDecoder().decode(unzipSync(await exporter(await new NodeIO().writeBinary(doc), 'obj'))['relief.obj']);
    expect(obj.match(/^vn /gm)).toHaveLength(3);
    expect(obj).toContain('usemtl matiere_0\ns off\nf 1 2 3');
    expect(obj).toContain('f 4//1 5//2 6//3');
  });
  it('OBJLoader conserve le lissage par matériau pour normale, absence, normale', async () => {
    const doc = new Document(), buf = doc.createBuffer(), mesh = doc.createMesh();
    for (const avec of [true, false, true]) {
      const p = doc.createPrimitive().setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf));
      if (avec) p.setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1])).setBuffer(buf));
      mesh.addPrimitive(p);
    }
    doc.createScene().addChild(doc.createNode().setMesh(mesh));
    const obj = new TextDecoder().decode(unzipSync(await exporter(await new NodeIO().writeBinary(doc), 'obj'))['relief.obj']);
    const materials: Material[] = [];
    new OBJLoader().parse(obj).traverse((child) => {
      if (child instanceof Mesh) materials.push(...(Array.isArray(child.material) ? child.material : [child.material]));
    });
    expect(materials.map((m) => (m as Material & { flatShading: boolean }).flatShading)).toEqual([false, true, false]);
  });
  it('refuse un accessoire de normales dont le type est incorrect', () => {
    const doc = new Document(), buf = doc.createBuffer();
    const p = doc.createPrimitive()
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf))
      .setAttribute('NORMAL', doc.createAccessor().setType('VEC2').setArray(new Float32Array(6)).setBuffer(buf));
    doc.createScene().addChild(doc.createNode().setMesh(doc.createMesh().addPrimitive(p)));
    expect(() => versObj(maillageDuDocument(doc))).toThrow(/Normales OBJ/);
  });
  for (const uv of [false, true]) for (const normale of [false, true]) {
    it(`écrit les faces uv=${uv}, normales=${normale}`, async () => {
      const glb = await glbNormales({ uv, normale: normale ? [0, 0, 1] : undefined });
      const obj = new TextDecoder().decode(unzipSync(await exporter(glb, 'obj'))['relief.obj']);
      expect(obj.match(/^vn /gm)?.length ?? 0).toBe(normale ? 3 : 0);
      expect(obj).toContain(normale ? (uv ? 'f 1/1/1 2/2/2 3/3/3' : 'f 1//1 2//2 3//3') : (uv ? 'f 1/1 2/2 3/3' : 'f 1 2 3'));
      if (!normale) expect(obj).toContain('s off');
    });
  }
  it('transforme les normales en inverse transposée pour une échelle non uniforme', async () => {
    const obj = new TextDecoder().decode(unzipSync(await exporter(await glbNormales({ normale: [1, 1, 0], echelle: [2, 1, 1] }), 'obj'))['relief.obj']);
    const [, x, y, z] = obj.match(/^vn ([^ ]+) ([^ ]+) ([^\n]+)/m)!;
    expect(Number(x)).toBeCloseTo(1 / Math.sqrt(5), 5); expect(Number(y)).toBeCloseTo(2 / Math.sqrt(5), 5); expect(Number(z)).toBe(0);
  });
  for (const indices of [false, true]) it(`inverse le winding réfléchi, indexé=${indices}`, async () => {
    const obj = new TextDecoder().decode(unzipSync(await exporter(await glbNormales({ normale: [0, 0, 1], echelle: [-1, 1, 1], indices }), 'obj'))['relief.obj']);
    expect(obj).toContain('f 1//1 3//3 2//2');
  });
  it('complète les coins nuls avec les normales de faces opposées, sans modifier les autres', async () => {
    const doc = new Document(), buf = doc.createBuffer();
    const p = doc.createPrimitive()
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf))
      .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 0, 0, 1, 0, 0, 1])).setBuffer(buf))
      .setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array([0, 1, 2, 0, 2, 1])).setBuffer(buf));
    doc.createScene().addChild(doc.createNode().setMesh(doc.createMesh().addPrimitive(p)));
    const obj = new TextDecoder().decode(unzipSync(await exporter(await new NodeIO().writeBinary(doc), 'obj'))['relief.obj']);
    expect(obj).toContain('# 2 normales de coin calculées');
    expect(obj).toContain('vn 0 0 1\nvn 0 0 -1');
    expect(obj).toContain('f 1//3 2//1 3//2');
    expect(obj).toContain('f 1//4 3//2 2//1');
  });
  it('refuse une normale nulle incidente à une face dégénérée sans la supprimer', async () => {
    const doc = new Document(), buf = doc.createBuffer();
    const p = doc.createPrimitive()
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 2, 0, 0])).setBuffer(buf))
      .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 0, 0, 1, 0, 0, 1])).setBuffer(buf));
    doc.createScene().addChild(doc.createNode().setMesh(doc.createMesh().addPrimitive(p)));
    const glb = await new NodeIO().writeBinary(doc);
    expect(compatibiliteObj(glb, await lireGlb(glb)).compatible).toBe(false);
    await expect(exporter(glb, 'obj')).rejects.toMatchObject({ code: 'OBJ_UNSUPPORTED' });
  });
  for (const options of [{ normale: [NaN, 0, 1] }, { normale: [0, 0, 1], taille: 2 }, { normale: [0, 0, 1], echelle: [0, 1, 1] as [number, number, number] }]) {
    it('refuse les normales ou la matrice invalides', async () => {
      const glb = await glbNormales(options);
      expect(compatibiliteObj(glb, await lireGlb(glb)).compatible).toBe(false);
      await expect(exporter(glb, 'obj')).rejects.toMatchObject({ code: 'OBJ_UNSUPPORTED' });
    });
  }
});

/** Deux primitives glTF avec couleurs différentes et une texture : aucune ressource externe. */
async function glbDeuxMatieres(options: { sansUv?: boolean; uvNaN?: boolean; jpeg?: boolean; blend?: boolean; deuxTextures?: boolean; grille?: boolean; texturePartagee?: boolean; memeNom?: boolean } = {}): Promise<Uint8Array> {
  const doc = new Document();
  const buf = doc.createBuffer();
  const png = Uint8Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64'));
  const jpeg = Uint8Array.from(Buffer.from('/9j/4AAQSkZJRgABAgAAAQABAAD//gAPTGF2YzYxLjMuMTAwAP/bAEMACAQEBAQEBQUFBQUFBgYGBgYGBgYGBgYGBgcHBwgICAcHBwYGBwcICAgICQkJCAgICAkJCgoKDAwLCw4ODhERFP/EAEwAAQEAAAAAAAAAAAAAAAAAAAAHAQEBAAAAAAAAAAAAAAAAAAAFBxABAAAAAAAAAAAAAAAAAAAAABEBAAAAAAAAAAAAAAAAAAAAAP/AABEIABAAEAMBIgACEQADEQD/2gAMAwEAAhEDEQA/AI4Av4t//9k=', 'base64'));
  const tex = doc.createTexture('texture').setImage(options.jpeg ? jpeg : png).setMimeType(options.jpeg ? 'image/jpeg' : 'image/png');
  const mats = [doc.createMaterial('rouge').setBaseColorFactor([1, 0, 0, .2]),
    doc.createMaterial('bleu').setBaseColorFactor([0, 0, 1, 1]).setBaseColorTexture(tex)];
  if (options.memeNom) mats[1].setName('rouge');
  if (options.texturePartagee) mats[0].setBaseColorTexture(tex);
  if (options.deuxTextures) mats[0].setBaseColorTexture(doc.createTexture('premiere').setImage(png).setMimeType('image/png'));
  if (options.blend) mats[1].setAlphaMode('BLEND').setBaseColorFactor([0, 0, 1, .5]);
  mats[1].getBaseColorTextureInfo()!.setTexCoord(1);
  const mesh = doc.createMesh();
  for (let i = 0; i < 2; i++) {
    const positions: number[] = [], uvs: number[] = [], indices: number[] = [];
    if (options.grille) {
      const n = 30;
      for (let y = 0; y <= n; y++) for (let x = 0; x <= n; x++) {
        positions.push(i * 2 + x / n, y / n, 0); uvs.push(x / n, y / n);
      }
      for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
        const a = y * (n + 1) + x, b = a + n + 1;
        indices.push(a, a + 1, b, a + 1, b + 1, b);
      }
    } else {
      positions.push(i * 2, 0, 0, i * 2 + 1, 0, 0, i * 2, 1, 0);
      uvs.push(0, 0, 1, 0, 0, options.uvNaN ? Number.NaN : 1);
      indices.push(0, 1, 2);
    }
    const p = doc.createPrimitive().setMaterial(mats[i])
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(Float32Array.from(positions)).setBuffer(buf))
      .setIndices(doc.createAccessor().setType('SCALAR').setArray(Uint16Array.from(indices)).setBuffer(buf));
    if (i === 0 && options.deuxTextures) p.setAttribute('TEXCOORD_0', doc.createAccessor().setType('VEC2').setArray(Float32Array.from(uvs)).setBuffer(buf));
    if (i === 1 && !options.sansUv) p.setAttribute('TEXCOORD_1', doc.createAccessor().setType('VEC2').setArray(Float32Array.from(uvs)).setBuffer(buf));
    mesh.addPrimitive(p);
  }
  doc.createScene().addChild(doc.createNode().setMesh(mesh));
  return new NodeIO().writeBinary(doc);
}

describe('Nexora Mesh : contrôle du maillage', () => {
  it('analyse et exporte uniquement la scène GLB par défaut, y compris ses descendants', async () => {
    const doc = new Document(), buf = doc.createBuffer();
    const position = doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf);
    const mesh = doc.createMesh().addPrimitive(doc.createPrimitive().setAttribute('POSITION', position));
    doc.createScene('inactive').addChild(doc.createNode().setMesh(mesh));
    const active = doc.createScene('active').addChild(doc.createNode().setTranslation([10, 0, 0]).addChild(doc.createNode().setMesh(mesh)));
    doc.createNode('orphan').setMesh(mesh);
    doc.getRoot().setDefaultScene(active);
    const glb = await new NodeIO().writeBinary(doc);
    const m = await lireGlb(glb);
    expect(m.indices).toHaveLength(3);
    expect(Array.from(m.positions)).toEqual([10, 0, 0, 11, 0, 0, 10, 1, 0]);
    const stl = await exporter(glb, 'stl');
    expect(new DataView(stl.buffer, stl.byteOffset, stl.byteLength).getUint32(80, true)).toBe(1);
    const model = new TextDecoder().decode(unzipSync(await exporter(glb, '3mf'))['3D/3dmodel.model']);
    expect(model.match(/<triangle /g)).toHaveLength(1);
    const obj = new TextDecoder().decode(unzipSync(await exporter(glb, 'obj'))['relief.obj']);
    expect(obj.match(/^f /gm)).toHaveLength(1);
  });
  it('utilise la première scène si aucune scène par défaut n’est indiquée', async () => {
    const doc = new Document(), buf = doc.createBuffer();
    const position = doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf);
    const mesh = doc.createMesh().addPrimitive(doc.createPrimitive().setAttribute('POSITION', position));
    doc.createScene('première').addChild(doc.createNode().setTranslation([2, 0, 0]).setMesh(mesh));
    doc.createScene('seconde').addChild(doc.createNode().setTranslation([50, 0, 0]).setMesh(mesh));
    const m = await lireGlb(await new NodeIO().writeBinary(doc));
    expect(m.indices).toHaveLength(3);
    expect(Array.from(m.positions)).toEqual([2, 0, 0, 3, 0, 0, 2, 1, 0]);
  });
  it('ne considère pas un nœud orphelin comme une scène', () => {
    const doc = new Document(), buf = doc.createBuffer();
    const position = doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 1, 0, 0, 0, 1, 0])).setBuffer(buf);
    doc.createNode().setMesh(doc.createMesh().addPrimitive(doc.createPrimitive().setAttribute('POSITION', position)));
    expect(maillageDuDocument(doc).indices).toHaveLength(0);
  });
  it('refuse un accessoire d’indices qui pointe hors des sommets après lecture GLB', async () => {
    const glb = await glbMaillage(Float32Array.from([0, 0, 0, 1, 0, 0, 0, 1, 0]), Uint32Array.from([0, 1, 99]));
    const maillage = await lireGlb(glb);
    expect(maillage.indices).toEqual(Uint32Array.from([0, 1, 99]));
    expect(() => analyser(maillage)).toThrow(/indice 99 hors plage/);
  });

  it('refuse des coordonnées non finies après lecture GLB', async () => {
    const glb = await glbMaillage(Float32Array.from([0, 0, 0, 1, 0, 0, 0, Number.NaN, 0]), Uint32Array.from([0, 1, 2]));
    const maillage = await lireGlb(glb);
    expect(maillage.positions.some((x) => !Number.isFinite(x))).toBe(true);
    expect(() => analyser(maillage)).toThrow(/coordonnée de position non finie/);
  });

  it('refuse les tableaux de positions et d’indices dont les dimensions ne forment pas des triangles', () => {
    expect(() => analyser({ positions: Float32Array.from([0, 0, 0, 1]), uvs: null, indices: Uint32Array.from([0, 0, 0]), couleur: null }))
      .toThrow(/positions.*multiple de 3/);
    expect(() => analyser({ positions: Float32Array.from([0, 0, 0]), uvs: null, indices: Uint32Array.from([0, 0, 0, 0]), couleur: null }))
      .toThrow(/indices.*multiple de 3/);
  });

  it('conserve le rapport explicite d’un maillage vide', () => {
    const r = analyser({ positions: new Float32Array(), uvs: null, indices: new Uint32Array(), couleur: null });
    expect(r.triangles).toBe(0);
    expect(r.taille).toEqual([0, 0, 0]);
    expect(r.avertissements).toContain('Maillage vide.');
  });

  it('distingue les arêtes des grands maillages et ignore leur orientation', () => {
    const a = 2 ** 21, b = a + 3, n = a + 10;
    expect(cleArete(a, b, n)).not.toBe(cleArete(a, b + 1, n));
    expect(cleArete(a, b, n)).toBe(cleArete(b, a, n));
    for (const limite of [94_906_265, 94_906_266, 2 ** 32]) {
      expect(cleArete(limite - 3, limite - 2, limite)).not.toBe(cleArete(limite - 3, limite - 1, limite));
      expect(cleArete(limite - 3, limite - 1, limite)).toBe(cleArete(limite - 1, limite - 3, limite));
    }
    const grand = 100_000_000;
    expect(cleArete(grand - 3, grand - 2, grand)).not.toBe(cleArete(grand - 3, grand - 1, grand));
    for (let taille = 2; taille <= 15; taille++) {
      const cles = new Set<number | bigint>();
      for (let x = 0; x < taille; x++) for (let y = x + 1; y < taille; y++) {
        const cle = cleArete(x, y, taille);
        expect(cle).toBe(cleArete(y, x, taille));
        expect(cles.has(cle)).toBe(false);
        cles.add(cle);
      }
      expect(cles.size).toBe(taille * (taille - 1) / 2);
    }
  });
  it('une sphère UV : un seul morceau, 2 de haut, triangles écrasés des pôles comptés', async () => {
    const m = await lireGlb(await glbSphere());
    const r = analyser(m);
    expect(r.triangles).toBe(24 * 24 * 2); // les pôles gardent des triangles écrasés par la grille UV
    expect(r.degeneres).toBeGreaterThan(0);
    expect(r.composantes).toBe(1);
    expect(r.taille[1]).toBeCloseTo(2, 3);
  });
  it('un trou est compté en arêtes ouvertes et le modèle n’est pas étanche', async () => {
    const r = analyser(await lireGlb(await glbSphere(24, true)));
    expect(r.aretesOuvertes).toBeGreaterThanOrEqual(4);
    expect(r.etanche).toBe(false);
    expect(r.avertissements.join(' ')).toMatch(/arêtes ouvertes/);
  });
  it('un tétraèdre propre est étanche, de volume exact', () => {
    const m: Maillage = { positions: Float32Array.from([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]), uvs: null, indices: Uint32Array.from([0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3]), couleur: null };
    const r = analyser(m);
    expect(r.etanche).toBe(true);
    expect(r.volume).toBeCloseTo(1 / 6, 6);
    expect(r.composantes).toBe(1);
  });
  it('refuse le volume d’un tétraèdre fermé dont une face est inversée', () => {
    const positions = Float32Array.from([2, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3]);
    const faces = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3];
    const propre = analyser({ positions, uvs: null, indices: Uint32Array.from(faces), couleur: null });
    expect(propre.volume).toBeCloseTo(1 / 6, 6);
    const indices = [...faces];
    [indices[1], indices[2]] = [indices[2], indices[1]];
    const r = analyser({ positions, uvs: null, indices: Uint32Array.from(indices), couleur: null });
    expect(r.etanche).toBe(true);
    expect(r.aretesOuvertes).toBe(0);
    expect(r.aretesNonVariete).toBe(0);
    expect(r.volume).toBeNull();
    expect(r.avertissements).toContain('Volume non calculé : orientation incohérente des faces.');
  });
  it('ne donne pas un volume physique ambigu pour plusieurs coquilles fermées', () => {
    const tetra = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]];
    const faces = [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3];
    const positions = Float32Array.from([...tetra.flat(), ...tetra.map(([x, y, z]) => [x + 3, y, z]).flat()]);
    const indices = [...faces];
    for (let i = 0; i < faces.length; i += 3) {
      const [a, b, c] = faces.slice(i, i + 3);
      indices.push(4 + a, 4 + c, 4 + b); // second tetrahedron orienté à l'inverse
    }
    const r = analyser({ positions, uvs: null, indices: Uint32Array.from(indices), couleur: null });
    expect(r.etanche).toBe(true);
    expect(r.composantes).toBe(2);
    expect(r.volume).toBeNull();
    expect(r.avertissements).toContain('Volume non calculé : plusieurs composantes fermées peuvent représenter des solides distincts ou des cavités imbriquées.');
  });
});

describe('Nexora Mesh : précision monde', () => {
  it('calcule le volume avec un ancrage utilisé, même si un sommet isolé est très éloigné', () => {
    const positions = Float64Array.from([1e18,0,0, 1e9,-1e9,1e9, 1e9+1,-1e9,1e9, 1e9,-1e9+1,1e9, 1e9,-1e9,1e9+1]);
    const indices = Uint32Array.from([1,3,2, 1,2,4, 1,4,3, 2,3,4]);
    const rapport = analyser({ positions, indices, uvs: null, couleur: null });
    expect(rapport.etanche).toBe(true);
    expect(rapport.volume).toBeCloseTo(1 / 6, 12);
  });
  it('préserve un tétraèdre local après une translation de nœud de 1e9', async () => {
    const doc = new Document(), buffer = doc.createBuffer();
    const points = doc.createAccessor().setType('VEC3').setArray(Float32Array.from([0,0,0, 1,0,0, 0,1,0, 0,0,1])).setBuffer(buffer);
    const indices = doc.createAccessor().setType('SCALAR').setArray(Uint16Array.from([0,2,1, 0,1,3, 0,3,2, 1,2,3])).setBuffer(buffer);
    const primitive = doc.createPrimitive().setAttribute('POSITION', points).setIndices(indices);
    const node = doc.createNode().setMesh(doc.createMesh().addPrimitive(primitive)).setTranslation([1e9, -1e9, 1e9]);
    doc.createScene().addChild(node);
    const glb = await new NodeIO().writeBinary(doc);
    const m = await lireGlb(glb), rapport = analyser(m);
    expect(m.positions).toBeInstanceOf(Float64Array);
    expect(rapport.taille).toEqual([1,1,1]);
    expect(rapport.degeneres).toBe(0);
    expect(rapport.etanche).toBe(true);
    expect(rapport.volume).toBeCloseTo(1 / 6, 12);
    const stl = versStl(m), bytes = new DataView(stl.buffer, stl.byteOffset, stl.byteLength);
    expect(bytes.getUint32(80, true)).toBe(4);
    const coordonnees: number[][] = [[], [], []];
    for (let t = 0; t < 4; t++) for (let k = 0; k < 9; k++) coordonnees[k % 3].push(bytes.getFloat32(84 + 50 * t + 12 + 4 * k, true));
    expect(coordonnees.map((axe) => Math.max(...axe) - Math.min(...axe))).toEqual([100, 100, 100]);
  });
});

describe('Nexora Mesh : décimation', () => {
  it('cibleTriangles borne et ignore ce qui ne réduit pas', () => {
    expect(cibleTriangles(undefined, 1000)).toBeNull();
    expect(cibleTriangles(10, 100000)).toBe(500);
    expect(cibleTriangles(5000, 4000)).toBeNull();
    expect(cibleTriangles(5000, 100000)).toBe(5000);
  });
  it('réduit nettement le nombre de triangles en gardant UV et texture', async () => {
    const glb = await glbSphere(64);
    const avant = analyser(await lireGlb(glb)).triangles;
    const m = await lireGlb(await decimerGlb(glb, 800));
    expect(m.indices.length / 3).toBeLessThan(avant / 2);
    expect(m.uvs).not.toBeNull();
    expect(m.couleur).not.toBeNull();
  });
});

describe('Nexora Mesh : exports', () => {
  for (const indices of [false, true]) for (const reflet of [false, true]) {
    it(`préserve l'orientation pour STL, 3MF et USDZ, reflet=${reflet}, indexé=${indices}`, async () => {
      const glb = await glbNormales({ echelle: [reflet ? -1 : 1, 1, 1], indices });
      const ordre = reflet ? [0, 2, 1] : [0, 1, 2];
      const m = await lireGlb(glb);
      expect(Array.from(m.indices)).toEqual(ordre);
      const stl = await exporter(glb, 'stl');
      const vue = new DataView(stl.buffer, stl.byteOffset, stl.byteLength);
      // La normale +Z glTF devient -Y dans le repère d'impression.
      expect(vue.getFloat32(88, true)).toBeCloseTo(-1);
      const xml = new TextDecoder().decode(unzipSync(await exporter(glb, '3mf'))['3D/3dmodel.model']);
      expect(xml).toContain(`<triangle v1="${ordre[0]}" v2="${ordre[1]}" v3="${ordre[2]}"/>`);
      const usda = new TextDecoder().decode(unzipSync(await exporter(glb, 'usdz'))['relief.usda']);
      expect(usda).toContain(`int[] faceVertexIndices = [${ordre.join(', ')}]`);
    });
  }
  it('STL binaire : taille = 84 + 50 par triangle, plus grande dimension à 100 mm', async () => {
    const m = await lireGlb(await glbSphere(8));
    const stl = versStl(m);
    expect(stl.length).toBe(84 + 50 * (m.indices.length / 3));
    expect(new TextDecoder().decode(stl.subarray(0, 80)).replace(/\0+$/, '')).toBe(NEXORA_PRODUCT_NAMES.mesh);
    expect(new DataView(stl.buffer).getUint32(80, true)).toBe(m.indices.length / 3);
    let max = -Infinity, min = Infinity;
    const dv = new DataView(stl.buffer);
    for (let t = 0; t < m.indices.length / 3; t++) for (let k = 0; k < 3; k++) { const z = dv.getFloat32(84 + 50 * t + 12 + 12 * k + 8, true); max = Math.max(max, z); min = Math.min(min, z); }
    expect(min).toBeCloseTo(0, 3);
    expect(max).toBeCloseTo(100, 2);
  });
  it('3MF : un zip avec le modèle en millimètres', async () => {
    const m = await lireGlb(await glbSphere(8));
    const z = unzipSync(vers3mf(m));
    expect(Object.keys(z).sort()).toEqual(['3D/3dmodel.model', '[Content_Types].xml', '_rels/.rels']);
    const xml = new TextDecoder().decode(z['3D/3dmodel.model']);
    expect(xml).toContain('unit="millimeter"');
    expect(xml).toContain(`<metadata name="Application">${NEXORA_PRODUCT_NAMES.mesh}</metadata>`);
    expect((xml.match(/<triangle /g) ?? []).length).toBe(m.indices.length / 3);
  });
  it('OBJ : un zip avec .obj, .mtl et la texture', async () => {
    const z = unzipSync(await exporter(await glbSphere(8), 'obj', { nom: 'balle' }));
    expect(Object.keys(z).sort()).toEqual(['balle.mtl', 'balle.obj', 'balle.png']);
    expect(new TextDecoder().decode(z['balle.obj'])).toContain(`# ${NEXORA_PRODUCT_NAMES.mesh} : balle`);
    expect(new TextDecoder().decode(z['balle.mtl'])).toContain('map_Kd balle.png');
  });
  it('OBJ conserve séparément les matières de deux primitives GLB', async () => {
    const zip = unzipSync(await exporter(await glbDeuxMatieres(), 'obj', { nom: 'deux' }));
    const obj = new TextDecoder().decode(zip['deux.obj']);
    const mtl = new TextDecoder().decode(zip['deux.mtl']);
    expect(obj).toMatch(/usemtl matiere_0[\s\S]*f 1 2 3[\s\S]*usemtl matiere_1[\s\S]*f 4\/4 5\/5 6\/6/);
    expect(mtl).toMatch(/newmtl matiere_0[\s\S]*Kd 1 0 0/);
    expect(mtl).toMatch(/newmtl matiere_1[\s\S]*Kd 0 0 1[\s\S]*map_Kd deux_1\.png/);
    expect(Array.from(zip['deux_1.png'])).toEqual(Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64')));
    expect(mtl).toMatch(/newmtl matiere_0[\s\S]*?d 1\n/); // alpha ignoré en mode OPAQUE
    expect(obj).toContain('vt 0 1\nvt 1 1\nvt 0 0'); // même convention V que l'ancien export

  });
  it('OBJ préserve JPEG et alpha BLEND et refuse une texture sans UV utilisables', async () => {
    const glb = await glbDeuxMatieres({ jpeg: true, blend: true });
    const document = await new NodeIO().readBinary(glb);
    const image = document.getRoot().listMaterials()[1].getBaseColorTexture()!.getImage()!;
    const zip = unzipSync(await exporter(glb, 'obj', { nom: 'jpeg' }));
    const mtl = new TextDecoder().decode(zip['jpeg.mtl']);
    expect(mtl).toMatch(/newmtl matiere_1[\s\S]*d 0\.5[\s\S]*map_Kd jpeg_1\.jpg/);
    expect(Array.from(zip['jpeg_1.jpg'])).toEqual(Array.from(image));
    const sansUv = await glbDeuxMatieres({ sansUv: true });
    expect(compatibiliteObj(sansUv, await lireGlb(sansUv))).toEqual({ compatible: false, code: 'OBJ_UNSUPPORTED' });
    expect(compatibiliteObj(glb, await lireGlb(glb))).toEqual({ compatible: true, code: null });
    await expect(exporter(sansUv, 'obj')).rejects.toThrow(/coordonnées UV utilisables/);
    await expect(exporter(await glbDeuxMatieres({ uvNaN: true }), 'obj')).rejects.toThrow(/UV OBJ non finies/);
  });
  it('OBJ conserve deux images distinctes sans chemins fournis par le nom', async () => {
    const glb = await glbDeuxMatieres({ deuxTextures: true, jpeg: true });
    const document = await new NodeIO().readBinary(glb);
    const images = document.getRoot().listMaterials().map((mat) => mat.getBaseColorTexture()!.getImage()!);
    const zip = unzipSync(await exporter(glb, 'obj', { nom: '../../deux' }));
    const files = Object.keys(zip);
    expect(files).toHaveLength(4);
    expect(files.every((name) => !name.includes('/') && !name.includes('..'))).toBe(true);
    const png = files.find((name) => name.endsWith('_0.png'))!;
    const jpg = files.find((name) => name.endsWith('_1.jpg'))!;
    expect(Array.from(zip[png])).toEqual(Array.from(images[0]));
    expect(Array.from(zip[jpg])).toEqual(Array.from(images[1]));
    const mtl = new TextDecoder().decode(zip[files.find((name) => name.endsWith('.mtl'))!]);
    expect(mtl).toContain(`map_Kd ${png}`);
    expect(mtl).toContain(`map_Kd ${jpg}`);
  });
  it('décime réellement deux primitives puis exporte leurs matières et UV valides', async () => {
    const glb = await glbDeuxMatieres({ deuxTextures: true, jpeg: true, grille: true });
    const avant = analyser(await lireGlb(glb)).triangles;
    expect(avant).toBe(3600);
    const original = await new NodeIO().readBinary(glb);
    const images = original.getRoot().listMaterials().map((mat) => mat.getBaseColorTexture()!.getImage()!);
    const zip = unzipSync(await exporter(glb, 'obj', { nom: 'reduit', cible: 500 }));
    const obj = new TextDecoder().decode(zip['reduit.obj']);
    const mtl = new TextDecoder().decode(zip['reduit.mtl']);
    const lignes = obj.split('\n');
    const nbVertices = lignes.filter((l) => l.startsWith('v ')).length;
    const nbUV = lignes.filter((l) => l.startsWith('vt ')).length;
    const faces = lignes.filter((l) => l.startsWith('f '));
    expect(faces.length).toBeLessThan(avant);
    expect(faces.length).toBeGreaterThan(0);
    expect(obj).toMatch(/usemtl matiere_0[\s\S]*f [\s\S]*usemtl matiere_1[\s\S]*f /);
    expect(mtl).toContain('map_Kd reduit_0.png');
    expect(mtl).toContain('map_Kd reduit_1.jpg');
    expect(Array.from(zip['reduit_0.png'])).toEqual(Array.from(images[0]));
    expect(Array.from(zip['reduit_1.jpg'])).toEqual(Array.from(images[1]));
    for (const face of faces) for (const vertex of face.slice(2).split(' ')) {
      const [v, uv] = vertex.split('/').map(Number);
      expect(v).toBeGreaterThan(0); expect(v).toBeLessThanOrEqual(nbVertices);
      expect(uv).toBeGreaterThan(0); expect(uv).toBeLessThanOrEqual(nbUV);
    }
  });
  it('OBJ refuse une transformation de texture explicite même si décimation demandée', async () => {
    const original = await glbDeuxMatieres();
    const view = new DataView(original.buffer, original.byteOffset, original.byteLength);
    const jsonLength = view.getUint32(12, true);
    const description = JSON.parse(new TextDecoder().decode(original.subarray(20, 20 + jsonLength)));
    description.materials[1].pbrMetallicRoughness.baseColorTexture.extensions = { KHR_texture_transform: { offset: [.2, .3] } };
    description.extensionsUsed = ['KHR_texture_transform'];
    const data = new TextEncoder().encode(JSON.stringify(description));
    const size = Math.ceil(data.length / 4) * 4;
    const tail = original.subarray(20 + jsonLength);
    const output = new Uint8Array(20 + size + tail.length);
    const header = new DataView(output.buffer);
    output.set(original.subarray(0, 20));
    header.setUint32(8, output.length, true);
    header.setUint32(12, size, true);
    output.fill(0x20, 20, 20 + size);
    output.set(data, 20);
    output.set(tail, 20 + size);
    expect(compatibiliteObj(output, await lireGlb(original))).toEqual({ compatible: false, code: 'OBJ_UNSUPPORTED' });
    await expect(exporter(output, 'obj', { cible: 500 })).rejects.toThrow(/Transformation de texture OBJ/);
  });
  it('le refus HTTP OBJ expose un code stable et le statut 400', async () => {
    const app = Fastify();
    app.get('/obj', (_request, reply) => repondreObjIncompatible(reply));
    const response = await app.inject({ method: 'GET', url: '/obj' });
    expect(response.statusCode).toBe(400);
    expect(response.json().code).toBe('OBJ_UNSUPPORTED');
    expect(response.json().error).toContain('GLB');
    await app.close();
  });
  it('le nouveau cache OBJ ignore un ancien fichier tout en le conservant', () => {
    const base = process.env.DIRECTOR_CI_CACHE;
    if (!base) throw new Error('DIRECTOR_CI_CACHE requis pour conserver la fixture');
    const dir = mkdtempSync(join(base, 'obj-cache-fixture-'));
    const ancien = join(dir, 'export-obj-normales-v4-plein-100.zip');
    const nouveau = join(dir, nomCacheExport('obj', null, 100));
    writeFileSync(ancien, 'ancien', { flag: 'wx' });
    expect(existsSync(nouveau)).toBe(false);
    writeFileSync(nouveau, 'nouveau', { flag: 'wx' });
    expect(readFileSync(ancien, 'utf8')).toBe('ancien');
    expect(readFileSync(nouveau, 'utf8')).toBe('nouveau');
    expect(nomCacheRapport(null)).toBe('rapport-monde64-v2-plein.json');
    expect(nomCacheRapport(500)).toBe('rapport-monde64-v2-500.json');
    expect(nomCacheExport('obj', null, 100)).toBe('export-obj-normales-v5-plein-100.zip');
    expect(nomCacheExport('stl', null, 100)).toBe('export-stl-orientation-v4-plein-100.stl');
    expect(nomCacheExport('3mf', null, 100)).toBe('export-3mf-orientation-v4-plein-100.3mf');
    expect(nomCacheExport('usdz', null, 100)).toBe('export-usdz-matieres-v3-plein-100.usdz');
    expect(nomCacheExport('glb', null, 100)).toBe('export-glb-plein-100.glb');
    expect(nomCacheExport('glb', 500, 100)).toBe('export-glb-scene-v1-500-100.glb');
    expect(nomCacheExport('usdz', 500, 100)).toBe('export-usdz-matieres-v3-scene-v1-500-100.usdz');
  });
  it('USDZ : zip non compressé, chaque fichier aligné sur 64 octets, USDA lisible', async () => {
    const octets = await exporter(await glbSphere(8), 'usdz', { nom: 'balle' });
    const dv = new DataView(octets.buffer, octets.byteOffset);
    let o = 0, n = 0;
    while (dv.getUint32(o, true) === 0x04034b50) {
      const lnom = dv.getUint16(o + 26, true), lextra = dv.getUint16(o + 28, true), taille = dv.getUint32(o + 18, true);
      expect((o + 30 + lnom + lextra) % 64).toBe(0);
      expect(dv.getUint16(o + 8, true)).toBe(0); // non compressé
      o += 30 + lnom + lextra + taille; n++;
    }
    expect(n).toBe(2);
    const z = unzipSync(octets);
    expect(new TextDecoder().decode(z['balle.usda'])).toMatch(/^#usda 1\.0/);
    expect(Object.keys(z)).toContain('texture_0_base.png');
  });
  it('zipAligne : le contenu se relit à l’identique', () => {
    const z = unzipSync(zipAligne([{ nom: 'a.txt', octets: new TextEncoder().encode('bonjour') }, { nom: 'b.bin', octets: Uint8Array.from([1, 2, 3]) }]));
    expect(new TextDecoder().decode(z['a.txt'])).toBe('bonjour');
    expect(Array.from(z['b.bin'])).toEqual([1, 2, 3]);
  });
  it('cartes PBR : la couleur est listée avec son type', async () => {
    const c = await cartesPbr(await glbSphere(8));
    expect(c.map((x) => x.nom)).toEqual(['couleur']);
    expect(c[0].mime).toBe('image/png');
  });
  it('liste deux cartes de couleur distinctes même si les matériaux ont le même nom', async () => {
    const cartes = await cartesPbr(await glbDeuxMatieres({ deuxTextures: true, jpeg: true, memeNom: true }));
    expect(cartes.map((c) => c.nom)).toEqual(['couleur', 'couleur-2']);
    expect(cartes.map((c) => c.mime)).toEqual(['image/png', 'image/jpeg']);
    expect(cartes.map((c) => c.materiaux)).toEqual([[{ index: 1, nom: 'rouge' }], [{ index: 2, nom: 'rouge' }]]);
    expect(cartes[0].octets).not.toEqual(cartes[1].octets);
  });
  it('associe une même texture partagée aux deux matériaux sans la dupliquer', async () => {
    const cartes = await cartesPbr(await glbDeuxMatieres({ texturePartagee: true }));
    expect(cartes.map((c) => c.nom)).toEqual(['couleur']);
    expect(cartes[0].materiaux).toEqual([{ index: 1, nom: 'rouge' }, { index: 2, nom: 'bleu' }]);
  });
});
