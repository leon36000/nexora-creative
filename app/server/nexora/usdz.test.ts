import { describe, expect, it } from 'vitest';
import { Document, NodeIO } from '@gltf-transform/core';
import { unzipSync } from 'fflate';
import { exporter } from './relief.js';

// Deux motifs déterministes distincts, minuscules et intégrés au GLB de test.
const TEXTURE_ROUGE = Uint8Array.from(Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAG0lEQVR42mP4ICL3X+SOxn8GOY1n/z9cEvkPAEu8CTkQW3q5AAAAAElFTkSuQmCC',
  'base64',
));
const TEXTURE_BLEUE = Uint8Array.from(Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAMAAAACCAYAAACddGYaAAAAJUlEQVR42gEaAOX/AArS5v/SFNz/8G4K/wBu5h7/FBQU//r69f/DRw9+03j5QAAAAABJRU5ErkJggg==',
  'base64',
));

type CarteNonPriseEnCharge = 'normales' | 'occlusion' | 'emission';
type OptionsFixture = {
  carte?: CarteNonPriseEnCharge;
  metallicRoughness?: boolean;
  alphaMask?: boolean;
  filtrageExplicite?: boolean;
  filtrageLineaire?: boolean;
};

async function glbDeuxMatieres(options: OptionsFixture = {}): Promise<Uint8Array> {
  const doc = new Document();
  const buffer = doc.createBuffer();
  const texRouge = doc.createTexture('texture-rouge').setImage(TEXTURE_ROUGE).setMimeType('image/png');
  const texBleue = doc.createTexture('texture-bleue').setImage(TEXTURE_BLEUE).setMimeType('image/png');
  const rouge = doc.createMaterial('rouge')
    .setBaseColorFactor([1, 0, 0, 0.2])
    .setMetallicFactor(0.15)
    .setRoughnessFactor(0.33)
    .setAlphaMode('BLEND')
    .setBaseColorTexture(texRouge);
  const bleu = doc.createMaterial('bleu')
    .setBaseColorFactor([0, 0, 1, 1])
    .setMetallicFactor(0.85)
    .setRoughnessFactor(0.61)
    .setBaseColorTexture(texBleue);
  bleu.getBaseColorTextureInfo()!.setTexCoord(1);
  if (options.alphaMask) rouge.setAlphaMode('MASK').setAlphaCutoff(0.42);
  if (options.filtrageExplicite) rouge.getBaseColorTextureInfo()!.setMagFilter(9728);
  if (options.filtrageLineaire) rouge.getBaseColorTextureInfo()!.setMagFilter(9729);
  if (options.metallicRoughness) {
    const metalRough = doc.createTexture('texture-metallic-roughness').setImage(TEXTURE_BLEUE).setMimeType('image/png');
    bleu.setMetallicRoughnessTexture(metalRough);
    bleu.getMetallicRoughnessTextureInfo()!.setTexCoord(0);
  }
  if (options.carte === 'normales') rouge.setNormalTexture(doc.createTexture('normales').setImage(TEXTURE_ROUGE).setMimeType('image/png'));
  if (options.carte === 'occlusion') rouge.setOcclusionTexture(doc.createTexture('occlusion').setImage(TEXTURE_ROUGE).setMimeType('image/png'));
  if (options.carte === 'emission') rouge.setEmissiveTexture(doc.createTexture('emission').setImage(TEXTURE_ROUGE).setMimeType('image/png'));

  const maillage = doc.createMesh('deux-matieres');
  const positions = [
    [0, 0, 0, 1, 0, 0, 0, 1, 0],
    [2, 0, 0, 3, 0, 0, 2, 1, 0],
  ];
  const uv = [
    [0.125, 0.25, 0.875, 0.3125, 0.25, 0.9375],
    [0.1875, 0.125, 0.8125, 0.375, 0.3125, 0.875],
  ];
  for (let i = 0; i < 2; i++) {
    const primitive = doc.createPrimitive().setMaterial(i === 0 ? rouge : bleu)
      .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(Float32Array.from(positions[i])).setBuffer(buffer))
      .setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array([0, 1, 2])).setBuffer(buffer));
    if (i === 1 && options.metallicRoughness) {
      primitive.setAttribute('TEXCOORD_0', doc.createAccessor().setType('VEC2')
        .setArray(Float32Array.from([0.0625, 0.1875, 0.9375, 0.28125, 0.34375, 0.78125])).setBuffer(buffer));
    }
    primitive.setAttribute(i === 0 ? 'TEXCOORD_0' : 'TEXCOORD_1',
      doc.createAccessor().setType('VEC2').setArray(Float32Array.from(uv[i])).setBuffer(buffer));
    maillage.addPrimitive(primitive);
  }
  doc.createScene().addChild(doc.createNode().setMesh(maillage));
  return new NodeIO().writeBinary(doc);
}

function ajouterExtensionTexture(glb: Uint8Array): Uint8Array {
  const view = new DataView(glb.buffer, glb.byteOffset, glb.byteLength);
  const jsonLength = view.getUint32(12, true);
  const json = JSON.parse(new TextDecoder().decode(glb.subarray(20, 20 + jsonLength)));
  json.materials[0].pbrMetallicRoughness.baseColorTexture.extensions = {
    KHR_texture_transform: { offset: [0.2, 0.3], scale: [0.5, 0.75] },
  };
  json.extensionsUsed = ['KHR_texture_transform'];
  const source = new TextEncoder().encode(JSON.stringify(json));
  const paddedLength = Math.ceil(source.length / 4) * 4;
  const output = new Uint8Array(20 + paddedLength + glb.length - 20 - jsonLength);
  output.set(glb.subarray(0, 20));
  const header = new DataView(output.buffer);
  header.setUint32(8, output.length, true);
  header.setUint32(12, paddedLength, true);
  output.fill(0x20, 20, 20 + paddedLength);
  output.set(source, 20);
  output.set(glb.subarray(20 + jsonLength), 20 + paddedLength);
  return output;
}

async function exporterUsdz(glb: Uint8Array) {
  const bytes = await exporter(glb, 'usdz', { nom: 'fixture' });
  return { bytes, fichiers: unzipSync(bytes), usda: new TextDecoder().decode(unzipSync(bytes)['fixture.usda']) };
}

async function glbNormalesNulles(positions: number[]): Promise<Uint8Array> {
  const doc = new Document();
  const buffer = doc.createBuffer();
  const primitive = doc.createPrimitive()
    .setAttribute('POSITION', doc.createAccessor().setType('VEC3').setArray(Float32Array.from(positions)).setBuffer(buffer))
    .setAttribute('NORMAL', doc.createAccessor().setType('VEC3').setArray(new Float32Array([0, 0, 0, 0, 0, 0, 0, 0, 0])).setBuffer(buffer))
    .setIndices(doc.createAccessor().setType('SCALAR').setArray(new Uint16Array([0, 1, 2])).setBuffer(buffer));
  doc.createScene().addChild(doc.createNode().setMesh(doc.createMesh().addPrimitive(primitive)));
  return new NodeIO().writeBinary(doc);
}

describe('Nexora Mesh : export USDZ multi-matériaux', () => {
  it('conserve deux matériaux, deux textures et les affectations des primitives', async () => {
    const glb = await glbDeuxMatieres();
    const sortie = await exporterUsdz(glb);
    const usda = sortie.usda;
    const materiaux = [...usda.matchAll(/def Material\s+"([^"]+)"/g)].map((m) => m[1]);
    const maillages = [...usda.matchAll(/def Mesh\s+"([^"]+)"/g)].map((m) => m[1]);
    const liaisons = [...usda.matchAll(/rel material:binding\s*=\s*<([^>]+)>/g)].map((m) => m[1]);
    const textures = Object.keys(sortie.fichiers).filter((nom) => /\.(png|jpe?g)$/i.test(nom));

    expect(materiaux).toHaveLength(2);
    expect(maillages).toHaveLength(2);
    expect(liaisons).toHaveLength(2);
    expect(new Set(liaisons).size).toBe(2);
    expect(textures).toHaveLength(2);
    expect(Array.from(sortie.fichiers[textures[0]])).toEqual(Array.from(TEXTURE_ROUGE));
    expect(Array.from(sortie.fichiers[textures[1]])).toEqual(Array.from(TEXTURE_BLEUE));
  });

  it('sélectionne UV0/UV1 selon la texture et inverse V pour USD', async () => {
    const { usda } = await exporterUsdz(await glbDeuxMatieres());
    expect(usda).toContain('string inputs:varname = "st_base"');
    expect(usda).not.toContain('token inputs:varname');
    expect(usda).toContain('texCoord2f[] primvars:st_base = [(0.125, 0.75), (0.875, 0.6875), (0.25, 0.0625)]');
    expect(usda).toContain('texCoord2f[] primvars:st_base = [(0.1875, 0.875), (0.8125, 0.625), (0.3125, 0.125)]');
  });

  it('conserve facteurs RGBA et facteurs PBR scalaires distincts', async () => {
    const { usda } = await exporterUsdz(await glbDeuxMatieres());
    expect(usda).toContain('float4 inputs:scale = (1, 0, 0, 0.2)');
    expect(usda).toContain('float4 inputs:scale = (0, 0, 1, 1)');
    expect(usda).toContain('float inputs:opacity.connect = </Mesh_fixture/Materiaux/m0/texture_base.outputs:a>');
    expect(usda).toContain('float inputs:opacity = 1');
    expect(usda).toContain('float inputs:metallic = 0.15');
    expect(usda).toContain('float inputs:roughness = 0.33');
    expect(usda).toContain('float inputs:metallic = 0.85');
    expect(usda).toContain('float inputs:roughness = 0.61');
  });

  it('refuse une extension glTF de transformation de texture', async () => {
    const glb = ajouterExtensionTexture(await glbDeuxMatieres());
    await expect(exporter(glb, 'usdz')).rejects.toMatchObject({ code: 'USDZ_UNSUPPORTED' });
  });

  it.each(['normales', 'occlusion', 'emission'] as const)('refuse une carte %s non prise en charge', async (carte) => {
    await expect(exporter(await glbDeuxMatieres({ carte }), 'usdz')).rejects.toMatchObject({ code: 'USDZ_UNSUPPORTED' });
  });

  it('refuse un mode de filtrage explicite qui n’est pas représenté dans USDZ', async () => {
    await expect(exporter(await glbDeuxMatieres({ filtrageExplicite: true }), 'usdz'))
      .rejects.toMatchObject({ code: 'USDZ_UNSUPPORTED' });
  });

  it('accepte le filtrage explicite LINEAR', async () => {
    const { usda } = await exporterUsdz(await glbDeuxMatieres({ filtrageLineaire: true }));
    expect(usda).toContain('def Material "m0"');
    expect(usda).toContain('asset inputs:file = @texture_0_base.png@');
  });

  it('conserve la carte metallic-roughness : G=roughness, B=metallic, UV choisis séparément', async () => {
    const { usda } = await exporterUsdz(await glbDeuxMatieres({ metallicRoughness: true }));
    expect(usda).toContain('float inputs:metallic.connect = </Mesh_fixture/Materiaux/m1/texture_mr.outputs:b>');
    expect(usda).toContain('float inputs:roughness.connect = </Mesh_fixture/Materiaux/m1/texture_mr.outputs:g>');
    expect(usda).toContain('float4 inputs:scale = (1, 0.61, 0.85, 1)');
    expect(usda).toContain('texCoord2f[] primvars:st_base = [(0.1875, 0.875), (0.8125, 0.625), (0.3125, 0.125)]');
    expect(usda).toContain('texCoord2f[] primvars:st_mr = [(0.0625, 0.8125), (0.9375, 0.71875), (0.34375, 0.21875)]');
  });

  it('conserve le masque alpha et son seuil', async () => {
    const { usda } = await exporterUsdz(await glbDeuxMatieres({ alphaMask: true }));
    expect(usda).toContain('float inputs:opacity.connect = </Mesh_fixture/Materiaux/m0/texture_base.outputs:a>');
    expect(usda).toContain('float inputs:opacityThreshold = 0.42');
    expect(usda).toContain('float4 inputs:scale = (1, 0, 0, 0.2)');
  });

  it('complète les normales nulles avec la normale de face et refuse une face dégénérée', async () => {
    const triangle = await exporter(await glbNormalesNulles([0, 0, 0, 1, 0, 0, 0, 1, 0]), 'usdz', { nom: 'triangle' });
    const usda = new TextDecoder().decode(unzipSync(triangle)['triangle.usda']);
    expect(usda).toContain('normal3f[] normals = [(0, 0, 1), (0, 0, 1), (0, 0, 1)] (interpolation = "faceVarying")');
    await expect(exporter(await glbNormalesNulles([0, 0, 0, 1, 0, 0, 2, 0, 0]), 'usdz'))
      .rejects.toMatchObject({ code: 'USDZ_UNSUPPORTED' });
  });

  it('produit un ZIP USDZ non compressé avec chaque payload aligné sur 64 octets', async () => {
    const { bytes, fichiers } = await exporterUsdz(await glbDeuxMatieres());
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const entrees: { nom: string; methode: number; offsetDonnees: number }[] = [];
    let offset = 0;
    while (offset + 30 <= bytes.length && view.getUint32(offset, true) === 0x04034b50) {
      const longueurNom = view.getUint16(offset + 26, true);
      const longueurExtra = view.getUint16(offset + 28, true);
      const longueurCompressee = view.getUint32(offset + 18, true);
      const debutDonnees = offset + 30 + longueurNom + longueurExtra;
      entrees.push({
        nom: new TextDecoder().decode(bytes.subarray(offset + 30, offset + 30 + longueurNom)),
        methode: view.getUint16(offset + 8, true),
        offsetDonnees: debutDonnees,
      });
      offset = debutDonnees + longueurCompressee;
    }
    expect(entrees).toHaveLength(3); // USDA + deux images
    expect(new Set(entrees.map((e) => e.nom))).toEqual(new Set(Object.keys(fichiers)));
    for (const entree of entrees) {
      expect(entree.methode).toBe(0);
      expect(entree.offsetDonnees % 64).toBe(0);
    }
  });
});
