import { describe, expect, it } from 'vitest';
import { Document, NodeIO } from '@gltf-transform/core';
import { unzipSync } from 'fflate';
import { analyser, cartesPbr, cibleTriangles, cleArete, decimerGlb, exporter, lireGlb, versStl, versUsdz, vers3mf, zipAligne, type Maillage } from './relief.js';

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

describe('Nexora Mesh : contrôle du maillage', () => {
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
  it('STL binaire : taille = 84 + 50 par triangle, plus grande dimension à 100 mm', async () => {
    const m = await lireGlb(await glbSphere(8));
    const stl = versStl(m);
    expect(stl.length).toBe(84 + 50 * (m.indices.length / 3));
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
    expect((xml.match(/<triangle /g) ?? []).length).toBe(m.indices.length / 3);
  });
  it('OBJ : un zip avec .obj, .mtl et la texture', async () => {
    const z = unzipSync(await exporter(await glbSphere(8), 'obj', { nom: 'balle' }));
    expect(Object.keys(z).sort()).toEqual(['balle.mtl', 'balle.obj', 'balle.png']);
    expect(new TextDecoder().decode(z['balle.mtl'])).toContain('map_Kd balle.png');
  });
  it('USDZ : zip non compressé, chaque fichier aligné sur 64 octets, USDA lisible', async () => {
    const octets = versUsdz(await lireGlb(await glbSphere(8)), { nom: 'balle' });
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
    expect(Object.keys(z)).toContain('couleur.png');
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
});
