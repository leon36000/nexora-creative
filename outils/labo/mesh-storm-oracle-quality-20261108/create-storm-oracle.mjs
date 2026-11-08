import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

import { nodeRequire, assetRoot, runRoot } from './config.mjs';

const require = nodeRequire;
const { NodeIO } = nodeRequire('@gltf-transform/core');
const sharp = require('sharp');
sharp.concurrency(2);
const HERE = dirname(fileURLToPath(import.meta.url));
const ASSETS = join(runRoot, 'payload-03');
const SOURCE = join(assetRoot, 'quality-overlap-patch-source.glb');
const TARGET = join(assetRoot, 'atlas-run-01', 'quality-overlap-patch-rebaked-atlas.glb');
if (existsSync(ASSETS)) throw new Error(`No-clobber: ${ASSETS} already exists.`);
mkdirSync(ASSETS, { recursive: false });
const hash = (b) => createHash('sha256').update(b).digest('hex');
const clamp = (x, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
const add = (a, b) => a.map((x, i) => x + b[i]);
const scale = (a, s) => a.map((x) => x * s);
const dot = (a, b) => a.reduce((sum, x, i) => sum + x * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (v) => {
  const m = Math.hypot(...v);
  if (!(m > 1e-20) || !Number.isFinite(m)) throw new Error('Zero/non-finite vector while building oracle.');
  return v.map((x) => x / m);
};
const fmt = (x) => {
  if (!Number.isFinite(x)) throw new Error('Non-finite USDA number.');
  return String(+x.toPrecision(9));
};
const CRC_TABLE = Array.from({ length: 256 }, (_, i) => {
  let c = i;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
const crc32Local = (bytes) => {
  let crc = 0xffffffff;
  for (const b of bytes) crc = CRC_TABLE[(crc ^ b) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
};
const tuple = (v) => `(${v.map(fmt).join(', ')})`;
const readElement = (accessor, i) => {
  const out = Array(accessor.getElementSize()).fill(0);
  accessor.getElement(i, out);
  return out;
};
const identityTRS = (node) => {
  const t = node.getTranslation(), r = node.getRotation(), s = node.getScale();
  return t.every((x) => Math.abs(x) < 1e-12) && r.every((x, i) => Math.abs(x - [0, 0, 0, 1][i]) < 1e-12) && s.every((x) => Math.abs(x - 1) < 1e-12);
};

async function readGlb(path) {
  const bytes = readFileSync(path);
  const doc = await new NodeIO().readBinary(bytes);
  const root = doc.getRoot();
  const meshes = root.listMeshes();
  const nodes = root.listNodes().filter((n) => n.getMesh());
  if (meshes.length !== 1 || nodes.length !== 1 || !identityTRS(nodes[0])) throw new Error(`Expected one mesh node with identity TRS: ${path}`);
  const primitive = meshes[0].listPrimitives()[0];
  const attrs = Object.fromEntries(['POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0'].map((s) => [s, primitive.getAttribute(s)]));
  if (Object.values(attrs).some((x) => !x)) throw new Error(`Missing required GLB attribute in ${path}`);
  const indexAccessor = primitive.getIndices();
  const indices = indexAccessor ? Array.from({ length: indexAccessor.getCount() }, (_, i) => indexAccessor.getScalar(i)) : Array.from({ length: attrs.POSITION.getCount() }, (_, i) => i);
  if (!indices.length || indices.length % 3) throw new Error(`Invalid triangles in ${path}`);
  const mat = primitive.getMaterial();
  if (!mat) throw new Error(`Missing material in ${path}`);
  const slots = {};
  for (const [key, method] of Object.entries({ base: 'getBaseColorTexture', mrao: 'getMetallicRoughnessTexture', normal: 'getNormalTexture' })) {
    const tex = mat[method]();
    if (!tex?.getImage()) throw new Error(`Missing ${key} map in ${path}`);
    slots[key] = { bytes: Buffer.from(tex.getImage()), mime: tex.getMimeType() };
  }
  const ao = mat.getOcclusionTexture();
  if (!ao?.getImage() || hash(ao.getImage()) !== hash(slots.mrao.bytes)) throw new Error(`Expected shared MR/AO map in ${path}`);
  const info = (method) => {
    const i = mat[method]();
    return { texCoord: i.getTexCoord(), mag: i.getMagFilter(), min: i.getMinFilter(), wrapS: i.getWrapS(), wrapT: i.getWrapT() };
  };
  const samplers = {
    base: info('getBaseColorTextureInfo'), mrao: info('getMetallicRoughnessTextureInfo'),
    normal: info('getNormalTextureInfo'), ao: info('getOcclusionTextureInfo'),
  };
  for (const [slot, s] of Object.entries(samplers)) {
    if (s.texCoord !== 0 || s.mag !== 9729 || s.min !== 9729 || s.wrapS !== 33071 || s.wrapT !== 33071) {
      throw new Error(`${slot} sampler/UV differs from the frozen preflight: ${JSON.stringify(s)}`);
    }
  }
  return { path, bytes, sha256: hash(bytes), doc, primitive, attrs, indices, material: mat, slots, samplers };
}

const [src, dst] = await Promise.all([readGlb(SOURCE), readGlb(TARGET)]);
if (src.indices.length !== dst.indices.length || src.indices.length !== 63) throw new Error('Source/target triangle corner counts differ.');
const sourceNode = src.doc.getRoot().listNodes().find((n) => n.getMesh());
const targetNode = dst.doc.getRoot().listNodes().find((n) => n.getMesh());
const identityMatrix = (node) => node.getMatrix().every((x, i) => Math.abs(x - [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1][i]) < 1e-12);
if (!identityMatrix(sourceNode) || !identityMatrix(targetNode)) throw new Error('Scene matrices must be identity for this frozen patch.');
const sourceFaces = [];
const positions = [], sourceNormals = [], sourceTangents = [], sourceUvs = [], targetUvs = [];
const bbox = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
for (let f = 0; f < src.indices.length / 3; f++) {
  const face = { sourceFaceId: src.primitive.getExtras().source_face_ids[f], corners: [] };
  for (let c = 0; c < 3; c++) {
    const si = src.indices[3 * f + c], ti = dst.indices[3 * f + c];
    const p = readElement(src.attrs.POSITION, si), rawN = readElement(src.attrs.NORMAL, si), n = unit(rawN);
    const tangent4 = readElement(src.attrs.TANGENT, si), uv = readElement(src.attrs.TEXCOORD_0, si), uvT = readElement(dst.attrs.TEXCOORD_0, ti);
    const pT = readElement(dst.attrs.POSITION, ti), rawNT = readElement(dst.attrs.NORMAL, ti);
    if (p.some((x, i) => !Object.is(x, pT[i])) || rawN.some((x, i) => !Object.is(x, rawNT[i]))) throw new Error(`Source/target point or geometric normal mismatch at face ${f}, corner ${c}.`);
    for (let k = 0; k < 3; k++) { bbox.min[k] = Math.min(bbox.min[k], p[k]); bbox.max[k] = Math.max(bbox.max[k], p[k]); }
    positions.push(p); sourceNormals.push(n); sourceTangents.push(unit(tangent4.slice(0, 3))); sourceUvs.push(uv); targetUvs.push(uvT);
    face.corners.push({ position: p, normal: n, tangent: unit(tangent4.slice(0, 3)), w: tangent4[3], uv, targetUv: uvT });
  }
  const ws = face.corners.map((c) => c.w);
  if (new Set(ws).size !== 1 || ![1, -1].includes(ws[0])) throw new Error(`Mixed/invalid glTF TANGENT.w in source face ${face.sourceFaceId}.`);
  face.w = ws[0];
  face.corners.forEach((c) => { c.bitangent = unit(cross(c.normal, c.tangent)).map((x) => x * face.w); });
  sourceFaces.push(face);
}
for (let i = 0; i < 3 * 21; i++) {
  const uv = targetUvs[i], uvS = sourceUvs[i];
  if (uvS.some((x) => x < 0 || x > 1) || uv.some((x) => x < 0 || x > 1)) throw new Error('Unexpected UV outside [0,1].');
}
const sameBounds = (() => {
  const b = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
  for (const p of dst.attrs.POSITION.getArray().reduce((a, x, i) => { (a[Math.floor(i / 3)] ??= [0, 0, 0])[i % 3] = x; return a; }, [])) for (let k = 0; k < 3; k++) { b.min[k] = Math.min(b.min[k], p[k]); b.max[k] = Math.max(b.max[k], p[k]); }
  return b;
})();
if (bbox.min.some((x, i) => Math.abs(x - sameBounds.min[i]) > 1e-7) || bbox.max.some((x, i) => Math.abs(x - sameBounds.max[i]) > 1e-7)) throw new Error('Source/target bounding boxes differ.');

async function decodeMap(bytes) {
  const out = await sharp(bytes).raw().toBuffer({ resolveWithObject: true });
  if (out.info.channels < 3) throw new Error('Unexpected map channels.');
  return { data: out.data, width: out.info.width, height: out.info.height, channels: out.info.channels };
}
const normalMap = await decodeMap(src.slots.normal.bytes);
const sample = (map, u, v) => {
  const x = clamp(u * map.width - 0.5, 0, map.width - 1), y = clamp(v * map.height - 0.5, 0, map.height - 1);
  const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(x0 + 1, map.width - 1), y1 = Math.min(y0 + 1, map.height - 1), fx = x - x0, fy = y - y0;
  const at = (ix, iy, c) => map.data[(iy * map.width + ix) * map.channels + c] / 255;
  return [0, 1, 2].map((c) => (1 - fy) * ((1 - fx) * at(x0, y0, c) + fx * at(x1, y0, c)) + fy * ((1 - fx) * at(x0, y1, c) + fx * at(x1, y1, c)));
};
const normalScale = src.material.getNormalScale();
if (!(normalScale > 0) || !Number.isFinite(normalScale)) throw new Error(`Invalid source normalScale ${normalScale}.`);

function interp(corners, beta, key, width) {
  return Array.from({ length: width }, (_, k) => corners.reduce((s, c, i) => s + beta[i] * c[key][k], 0));
}
function sampleWorldNormal(face, beta) {
  // Three r186 USE_TANGENT: interpolate per-vertex normalized N/T/B columns, normalize each in fragment,
  // decode the raw glTF map, scale XY, multiply by the TBN, then normalize the world vector.
  const N = unit(interp(face.corners, beta, 'normal', 3));
  const T = unit(interp(face.corners, beta, 'tangent', 3));
  const B = unit(interp(face.corners, beta, 'bitangent', 3));
  const uv = interp(face.corners, beta, 'uv', 2);
  const tex = sample(normalMap, uv[0], uv[1]);
  const mapN = [2 * tex[0] - 1, (2 * tex[1] - 1), 2 * tex[2] - 1];
  mapN[0] *= normalScale; mapN[1] *= normalScale;
  return unit(add(add(scale(T, mapN[0]), scale(B, mapN[1])), scale(N, mapN[2])));
}

function surfaceArrays(level, mapped) {
  const P = [], N = [], UV = [], indices = [];
  const n = level;
  for (const face of sourceFaces) {
    const local = new Map();
    const indexAt = (i, j) => {
      const key = `${i},${j}`;
      if (local.has(key)) return local.get(key);
      const beta = [1 - (i + j) / n, i / n, j / n];
      const pos = interp(face.corners, beta, 'position', 3);
      const uv = interp(face.corners, beta, 'uv', 2);
      let normal;
      if (mapped) normal = sampleWorldNormal(face, beta);
      else normal = unit(interp(face.corners, beta, 'normal', 3));
      const idx = P.length;
      P.push(pos); N.push(normal); UV.push(uv); local.set(key, idx);
      return idx;
    };
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n - i; j++) {
        indices.push(indexAt(i, j), indexAt(i + 1, j), indexAt(i, j + 1));
        if (i + j < n - 1) indices.push(indexAt(i + 1, j), indexAt(i + 1, j + 1), indexAt(i, j + 1));
      }
    }
  }
  return { positions: P, normals: N, uvs: UV, indices };
}

function meshArrays(glb, uvOverride = null, normalOverride = null) {
  const primitive = glb.primitive;
  const P = Array.from({ length: glb.attrs.POSITION.getCount() }, (_, i) => readElement(glb.attrs.POSITION, i));
  const N = Array.from({ length: glb.attrs.NORMAL.getCount() }, (_, i) => unit(readElement(glb.attrs.NORMAL, i)));
  const U = Array.from({ length: glb.attrs.TEXCOORD_0.getCount() }, (_, i) => readElement(glb.attrs.TEXCOORD_0, i));
  return { positions: P, normals: normalOverride ?? N, uvs: uvOverride ?? U, indices: glb.indices };
}

function textureDecl(slot, filename, mapPath, sourceColorSpace, scale4, bias4, outputs) {
  const path = '/Patch/Materials/m0';
  return `def Shader "coord_${slot}" {\n uniform token info:id = "UsdPrimvarReader_float2"\n string inputs:varname = "st"\n float2 outputs:result\n}\ndef Shader "texture_${slot}" {\n uniform token info:id = "UsdUVTexture"\n asset inputs:file = @${filename}@\n float2 inputs:st.connect = <${path}/coord_${slot}.outputs:result>\n token inputs:sourceColorSpace = "${sourceColorSpace}"\n token inputs:wrapS = "clamp"\n token inputs:wrapT = "clamp"\n float4 inputs:scale = ${tuple(scale4)}\n float4 inputs:bias = ${tuple(bias4)}\n ${outputs.map((o) => `${o.type} outputs:${o.name}`).join('\n ')}\n}`;
}

function stageText({ name, arrays, baseFactor, metallic, roughness, occlusionStrength, alpha, baseFile, mraoFile, normalFile = null, normalMode = 'mapped', includeNormalTexture = false, flatNormal = false }) {
  const nfaces = arrays.indices.length / 3;
  if (!nfaces || !Number.isInteger(nfaces)) throw new Error(`Stage ${name} has no triangles.`);
  const meshPath = '/Patch/mesh';
  const matPath = '/Patch/Materials/m0';
  const pointsText = arrays.positions.map(tuple).join(', ');
  const normalsText = arrays.normals.map(tuple).join(', ');
  const stText = arrays.uvs.map(([u, v]) => tuple([u, 1 - v])).join(', '); // GLB v=0 maps to first PNG row; USD st is vertically flipped.
  const indexText = arrays.indices.join(', ');
  const wrapValues = (count) => Array.from({ length: count }, () => 3).join(', ');
  const baseTex = textureDecl('base', baseFile, baseFile, 'sRGB', [...baseFactor.slice(0, 3), 1], [0, 0, 0, 0], [{ type: 'float3', name: 'rgb' }, { type: 'float', name: 'a' }]);
  const mrTex = textureDecl('mrao', mraoFile, mraoFile, 'raw', [1, roughness, metallic, 1], [0, 0, 0, 0], [{ type: 'float', name: 'r' }, { type: 'float', name: 'g' }, { type: 'float', name: 'b' }]);
  const aoTex = textureDecl('ao', mraoFile, mraoFile, 'raw', [occlusionStrength, 1, 1, 1], [1 - occlusionStrength, 0, 0, 0], [{ type: 'float', name: 'r' }]);
  const normalTex = includeNormalTexture ? textureDecl('normal', normalFile, normalFile, 'raw', [2, 2, 2, 1], [-1, -1, -1, 0], [{ type: 'float3', name: 'rgb' }]) : '';
  const baseScale = baseFactor.slice(0, 3);
  const surfaceNormal = includeNormalTexture ? `normal3f inputs:normal.connect = <${matPath}/texture_normal.outputs:rgb>` : '';
  const stage = `#usda 1.0\n(\n defaultPrim = "Patch"\n metersPerUnit = 1\n upAxis = "Y"\n)\ndef Xform "Patch" (kind = "component") {\n def Mesh "mesh" (prepend apiSchemas = ["MaterialBindingAPI"]) {\n  int[] faceVertexCounts = [${wrapValues(nfaces)}]\n  int[] faceVertexIndices = [${indexText}]\n  point3f[] points = [${pointsText}]\n  normal3f[] normals = [${normalsText}] (interpolation = "vertex")\n  texCoord2f[] primvars:st = [${stText}] (interpolation = "vertex")\n  uniform token subdivisionScheme = "none"\n  uniform bool doubleSided = true\n  rel material:binding = <${matPath}>\n }\n def Scope "Materials" {\n  def Material "m0" {\n   token outputs:surface.connect = <${matPath}/surface.outputs:surface>\n   def Shader "surface" {\n    uniform token info:id = "UsdPreviewSurface"\n    color3f inputs:diffuseColor.connect = <${matPath}/texture_base.outputs:rgb>\n    float inputs:opacity = ${fmt(alpha)}\n    float inputs:metallic.connect = <${matPath}/texture_mrao.outputs:b>\n    float inputs:roughness.connect = <${matPath}/texture_mrao.outputs:g>\n    float inputs:occlusion.connect = <${matPath}/texture_ao.outputs:r>\n    ${surfaceNormal}\n    token outputs:surface\n   }\n   ${baseTex}\n   ${mrTex}\n   ${aoTex}\n   ${normalTex}\n  }\n }\n}\n`;
  return stage;
}

function writeNew(path, data) { writeFileSync(path, data, { flag: 'wx' }); }
function zipAligneLocal(files) {
  const pieces = [], central = [];
  let pos = 0;
  const u16 = (v) => [v & 255, (v >> 8) & 255];
  const u32 = (v) => [v & 255, (v >>> 8) & 255, (v >>> 16) & 255, (v >>> 24) & 255];
  for (const { nom, octets } of files) {
    const name = new TextEncoder().encode(nom), header = 30 + name.length;
    const padding = (64 - ((pos + header + 4) % 64)) % 64, extra = padding + 4;
    const crc = crc32Local(octets);
    const local = Uint8Array.from([0x50, 0x4b, 3, 4, ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0x21), ...u32(crc), ...u32(octets.length), ...u32(octets.length), ...u16(name.length), ...u16(extra), ...name, 0x55, 0x53, ...u16(padding), ...new Array(padding).fill(0)]);
    central.push(Uint8Array.from([0x50, 0x4b, 1, 2, ...u16(20), ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0x21), ...u32(crc), ...u32(octets.length), ...u32(octets.length), ...u16(name.length), ...u16(0), ...u16(0), ...u16(0), ...u16(0), ...u32(0), ...u32(pos), ...name]));
    pieces.push(local, octets); pos += local.length + octets.length;
  }
  const centralSize = central.reduce((s, c) => s + c.length, 0);
  const end = Uint8Array.from([0x50, 0x4b, 5, 6, 0, 0, 0, 0, ...u16(files.length), ...u16(files.length), ...u32(centralSize), ...u32(pos), 0, 0]);
  const result = new Uint8Array(pos + centralSize + end.length);
  let offset = 0;
  for (const item of [...pieces, ...central, end]) { result.set(item, offset); offset += item.length; }
  return result;
}
function packageFiles(stageName, files) {
  // Packages are experimental lab stages, not output of the product USDZ exporter.
  const bytes = zipAligneLocal([{ nom: stageName, octets: Buffer.from(readFileSync(join(ASSETS, stageName))) }, ...files.map((f) => ({ nom: f, octets: Buffer.from(readFileSync(join(ASSETS, f))) }))]);
  const out = join(ASSETS, `${stageName.replace(/\.usda$/, '')}.usdz`);
  writeNew(out, bytes);
  return { path: out, bytes: bytes.length, sha256: hash(bytes) };
}

for (const [glb, prefix] of [[src, 'source'], [dst, 'target']]) {
  for (const [slot, value] of Object.entries(glb.slots)) writeNew(join(ASSETS, `${prefix}-${slot}.png`), value.bytes);
}
const flatRaw = Buffer.alloc(4 * 4 * 3);
for (let i = 0; i < 16; i++) { flatRaw[i * 3] = 128; flatRaw[i * 3 + 1] = 128; flatRaw[i * 3 + 2] = 255; }
const flatPng = await sharp(flatRaw, { raw: { width: 4, height: 4, channels: 3 } }).png().toBuffer();
writeNew(join(ASSETS, 'flat-normal.png'), flatPng);

const targetArrays = meshArrays(dst);
const sourceArrays = meshArrays(src);
writeNew(join(ASSETS, 'source-flat-material.usda'), stageText({ name: 'source-flat-material', arrays: sourceArrays, baseFactor: src.material.getBaseColorFactor(), metallic: src.material.getMetallicFactor(), roughness: src.material.getRoughnessFactor(), occlusionStrength: src.material.getOcclusionStrength(), alpha: 1, baseFile: 'source-base.png', mraoFile: 'source-mrao.png' }));
writeNew(join(ASSETS, 'target-flat-material.usda'), stageText({ name: 'target-flat-material', arrays: targetArrays, baseFactor: dst.material.getBaseColorFactor(), metallic: dst.material.getMetallicFactor(), roughness: dst.material.getRoughnessFactor(), occlusionStrength: dst.material.getOcclusionStrength(), alpha: 1, baseFile: 'target-base.png', mraoFile: 'target-mrao.png' }));
writeNew(join(ASSETS, 'target-normal.usda'), stageText({ name: 'target-normal', arrays: targetArrays, baseFactor: dst.material.getBaseColorFactor(), metallic: dst.material.getMetallicFactor(), roughness: dst.material.getRoughnessFactor(), occlusionStrength: dst.material.getOcclusionStrength(), alpha: 1, baseFile: 'target-base.png', mraoFile: 'target-mrao.png', normalFile: 'target-normal.png', includeNormalTexture: true }));
writeNew(join(ASSETS, 'target-flat-normal.usda'), stageText({ name: 'target-flat-normal', arrays: targetArrays, baseFactor: dst.material.getBaseColorFactor(), metallic: dst.material.getMetallicFactor(), roughness: dst.material.getRoughnessFactor(), occlusionStrength: dst.material.getOcclusionStrength(), alpha: 1, baseFile: 'target-base.png', mraoFile: 'target-mrao.png', normalFile: 'flat-normal.png', includeNormalTexture: true, flatNormal: true }));
writeNew(join(ASSETS, 'source-direct-normal.usda'), stageText({ name: 'source-direct-normal', arrays: sourceArrays, baseFactor: src.material.getBaseColorFactor(), metallic: src.material.getMetallicFactor(), roughness: src.material.getRoughnessFactor(), occlusionStrength: src.material.getOcclusionStrength(), alpha: 1, baseFile: 'source-base.png', mraoFile: 'source-mrao.png', normalFile: 'source-normal.png', includeNormalTexture: true }));

const oracleCounts = {};
for (const n of [4, 8, 16]) {
  const arrays = surfaceArrays(n, true);
  if (arrays.indices.length / 3 !== 21 * n * n) throw new Error(`Oracle n=${n} triangle count mismatch.`);
  const expectedPoints = 21 * (n + 1) * (n + 2) / 2;
  if (arrays.positions.length !== expectedPoints) throw new Error(`Oracle n=${n} vertex count mismatch.`);
  const stageName = `oracle-n${n}.usda`;
  writeNew(join(ASSETS, stageName), stageText({ name: `oracle-n${n}`, arrays, baseFactor: src.material.getBaseColorFactor(), metallic: src.material.getMetallicFactor(), roughness: src.material.getRoughnessFactor(), occlusionStrength: src.material.getOcclusionStrength(), alpha: 1, baseFile: 'source-base.png', mraoFile: 'source-mrao.png' }));
  oracleCounts[n] = { triangles: arrays.indices.length / 3, vertices: arrays.positions.length, stage: stageName };
  if (n === 16) {
    const flat = surfaceArrays(n, false);
    writeNew(join(ASSETS, 'oracle-n16-flat.usda'), stageText({ name: 'oracle-n16-flat', arrays: flat, baseFactor: src.material.getBaseColorFactor(), metallic: src.material.getMetallicFactor(), roughness: src.material.getRoughnessFactor(), occlusionStrength: src.material.getOcclusionStrength(), alpha: 1, baseFile: 'source-base.png', mraoFile: 'source-mrao.png' }));
  }
}

const packaged = [
  await packageFiles('target-normal.usda', ['target-base.png', 'target-mrao.png', 'target-normal.png']),
  await packageFiles('oracle-n16.usda', ['source-base.png', 'source-mrao.png']),
  await packageFiles('source-direct-normal.usda', ['source-base.png', 'source-mrao.png', 'source-normal.png']),
];

const assets = [];
for (const name of ['source-base.png', 'source-mrao.png', 'source-normal.png', 'target-base.png', 'target-mrao.png', 'target-normal.png', 'flat-normal.png', 'source-flat-material.usda', 'target-flat-material.usda', 'target-normal.usda', 'target-flat-normal.usda', 'source-direct-normal.usda', 'oracle-n4.usda', 'oracle-n8.usda', 'oracle-n16.usda', 'oracle-n16-flat.usda', 'target-normal.usdz', 'oracle-n16.usdz', 'source-direct-normal.usdz']) {
  const bytes = readFileSync(join(ASSETS, name));
  assets.push({ path: name, bytes: bytes.length, sha256: hash(bytes) });
}
const report = {
  method: 'Laboratoire uniquement: USDA/Hydra Storm stages créés depuis les deux GLB figés, aucun code produit modifié.',
  source: { path: src.path, bytes: src.bytes.length, sha256: src.sha256 },
  target: { path: dst.path, bytes: dst.bytes.length, sha256: dst.sha256 },
  transform: { source_trs: sourceNode.getMatrix(), target_trs: targetNode.getMatrix(), identity_verified: true, determinant: 1, positions_copied_without_coordinate_transform: true, normals_inverse_transpose: 'identité, inchangées', tangent_w_adjustment: 'determinant +1, aucun signe inversé', stage_up_axis: 'Y', camera_up_axis: 'Z (comme le lecteur Three fixe)', bbox_source_equals_target: bbox },
  source_material: { baseColorFactor: src.material.getBaseColorFactor(), metallicFactor: src.material.getMetallicFactor(), roughnessFactor: src.material.getRoughnessFactor(), normalScale: normalScale, occlusionStrength: src.material.getOcclusionStrength(), alphaMode: src.material.getAlphaMode(), samplers: src.samplers },
  target_material: { baseColorFactor: dst.material.getBaseColorFactor(), metallicFactor: dst.material.getMetallicFactor(), normalScale: dst.material.getNormalScale(), occlusionStrength: dst.material.getOcclusionStrength(), alphaMode: dst.material.getAlphaMode(), samplers: dst.samplers },
  gltf_tbn: 'Three r186 USE_TANGENT: per-corner normalized N/T, B=normalize(cross(N,T)*w); interpolate and normalize N/T/B per fragment; decode normal texture raw, scale XY, multiply by TBN, normalize. Oracle samples the source map at barycentric points and stores this world normal as USD vertex/geometric normals. Source stage direct-normal is a separate diagnostic: Storm constructs its own tangent frame from USD st/position derivatives.',
  oracle: oracleCounts,
  stages: ['source-flat-material.usda', 'source-direct-normal.usda', 'oracle-n4.usda', 'oracle-n8.usda', 'oracle-n16.usda', 'oracle-n16-flat.usda', 'target-flat-material.usda', 'target-normal.usda', 'target-flat-normal.usda'],
  lab_usdz_packages: packaged,
  textures: { source_baseColor: hash(src.slots.base.bytes), source_mraoAo: hash(src.slots.mrao.bytes), source_normal: hash(src.slots.normal.bytes), target_baseColor: hash(dst.slots.base.bytes), target_mraoAo: hash(dst.slots.mrao.bytes), target_normal: hash(dst.slots.normal.bytes), flat_normal: hash(flatPng), usd_uv: 'primvar st = (u, 1-v), matching the prior GLB→USD export mapping; LINEAR/CLAMP; baseColor sRGB; normal/MR/AO raw' },
  asset_manifest: assets,
  limitations: ['TANGENT.w is constant per source triangle in this 21-face patch; the 3,290 mixed-w source faces are not covered.', 'Normal-map sampling is linear/clamp, UV0, in-range only; no UDIM/wrap variation or mipmaps.', 'The target and source stages are experimental lab USDA, not product-exporter output; production `USDZ_UNSUPPORTED` for normal/AO remains intact.', 'The oracle vertex normals converge only as tessellation increases; convergence does not prove every USD renderer or Quick Look matches Three.', 'Source/target material-only controls still include USD texture filtering/shading; they isolate map/material contribution under the chosen fixed Storm scene, not all lighting implementations.'],
};
writeNew(join(ASSETS, 'generation-report.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ payload: ASSETS, counts: oracleCounts, bbox: bbox, outputs: assets.length + 1 }));
