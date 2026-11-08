import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

import { nodeRequire, assetRoot, runRoot } from './config.mjs';

const require = nodeRequire;
const { NodeIO } = nodeRequire('@gltf-transform/core');
const sharp = require('sharp');
sharp.concurrency(2);
const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = join(runRoot, 'payload-03');
const SOURCE = join(assetRoot, 'quality-overlap-patch-source.glb');
const OUTPUT = join(DIR, 'oracle-n32-v2.usda');
const REPORT = join(DIR, 'oracle-n32-generation-report-v2.json');
const hash = (b) => createHash('sha256').update(b).digest('hex');
const clamp = (x, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
const add = (a, b) => a.map((x, i) => x + b[i]);
const scale = (a, s) => a.map((x) => x * s);
const dot = (a, b) => a.reduce((sum, x, i) => sum + x * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (v) => { const m = Math.hypot(...v); if (!(m > 1e-20) || !Number.isFinite(m)) throw new Error('Zero/non-finite vector.'); return v.map((x) => x / m); };
const fmt = (x) => { if (!Number.isFinite(x)) throw new Error('Non-finite USDA value.'); return String(+x.toPrecision(9)); };
const tuple = (v) => `(${v.map(fmt).join(', ')})`;
const readElement = (a, i) => { const out = Array(a.getElementSize()).fill(0); a.getElement(i, out); return out; };
function interp(corners, beta, key, size) { return Array.from({ length: size }, (_, k) => corners.reduce((s, c, i) => s + beta[i] * c[key][k], 0)); }

const sourceBytes = readFileSync(SOURCE), doc = await new NodeIO().readBinary(sourceBytes), root = doc.getRoot();
const primitive = root.listMeshes()[0].listPrimitives()[0], material = primitive.getMaterial();
const attrs = Object.fromEntries(['POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0'].map((s) => [s, primitive.getAttribute(s)]));
const indices = primitive.getIndices();
const node = root.listNodes().find((n) => n.getMesh());
if (!node || node.getMatrix().some((x, i) => Math.abs(x - [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1][i]) > 1e-12)) throw new Error('Expected identity scene transform.');
const normalBytes = Buffer.from(material.getNormalTexture().getImage());
const normalSHA = hash(normalBytes);
if (normalSHA !== hash(readFileSync(join(DIR, 'source-normal.png')))) throw new Error('Extracted normal map differs from source GLB.');
const decoded = await sharp(normalBytes).raw().toBuffer({ resolveWithObject: true });
if (decoded.info.channels < 3) throw new Error('Normal map is not RGB.');
const map = { data: decoded.data, width: decoded.info.width, height: decoded.info.height, channels: decoded.info.channels };
const sample = (u, v) => {
  const x = clamp(u * map.width - 0.5, 0, map.width - 1), y = clamp(v * map.height - 0.5, 0, map.height - 1);
  const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(x0 + 1, map.width - 1), y1 = Math.min(y0 + 1, map.height - 1), fx = x - x0, fy = y - y0;
  const at = (ix, iy, c) => map.data[(iy * map.width + ix) * map.channels + c] / 255;
  return [0,1,2].map((c) => (1 - fy) * ((1 - fx) * at(x0,y0,c) + fx * at(x1,y0,c)) + fy * ((1 - fx) * at(x0,y1,c) + fx * at(x1,y1,c)));
};
const normalScale = material.getNormalScale();
const sourceIds = primitive.getExtras().source_face_ids;
if (!Array.isArray(sourceIds) || sourceIds.length !== 21) throw new Error('Unexpected source face ids.');
const faces = [];
for (let f = 0; f < 21; f++) {
  const corners = [0,1,2].map((c) => {
    const i = indices.getScalar(f * 3 + c), n = unit(readElement(attrs.NORMAL, i)), tangent4 = readElement(attrs.TANGENT, i);
    return { position: readElement(attrs.POSITION, i), normal: n, tangent: unit(tangent4.slice(0,3)), w: tangent4[3], uv: readElement(attrs.TEXCOORD_0, i) };
  });
  const ws = corners.map((c) => c.w);
  if (new Set(ws).size !== 1 || Math.abs(ws[0]) !== 1) throw new Error(`Mixed/invalid w at source face ${sourceIds[f]}.`);
  corners.forEach((c) => { c.bitangent = unit(cross(c.normal, c.tangent)).map((x) => x * ws[0]); });
  faces.push({ sourceFaceId: sourceIds[f], w: ws[0], corners });
}
function worldNormal(face, beta) {
  // Match Three r186 USE_TANGENT columns interpolated from original GLB vertices.
  const N = unit(interp(face.corners, beta, 'normal', 3));
  const T = unit(interp(face.corners, beta, 'tangent', 3));
  const B = unit(interp(face.corners, beta, 'bitangent', 3));
  const uv = interp(face.corners, beta, 'uv', 2), tex = sample(uv[0], uv[1]);
  const m = [2 * tex[0] - 1, 2 * tex[1] - 1, 2 * tex[2] - 1];
  m[0] *= normalScale; m[1] *= normalScale;
  return unit(add(add(scale(T, m[0]), scale(B, m[1])), scale(N, m[2])));
}
const n = 32, positions = [], normals = [], uvs = [], indicesOut = [];
for (const face of faces) {
  const local = new Map();
  const get = (i, j) => {
    const key = `${i},${j}`;
    if (local.has(key)) return local.get(key);
    const beta = [1 - (i + j) / n, i / n, j / n];
    const idx = positions.length;
    positions.push(interp(face.corners, beta, 'position', 3));
    uvs.push(interp(face.corners, beta, 'uv', 2));
    normals.push(worldNormal(face, beta));
    local.set(key, idx);
    return idx;
  };
  for (let i = 0; i < n; i++) for (let j = 0; j < n - i; j++) {
    indicesOut.push(get(i,j), get(i+1,j), get(i,j+1));
    if (i + j < n - 1) indicesOut.push(get(i+1,j), get(i+1,j+1), get(i,j+1));
  }
}
const expectedTriangles = 21 * n * n, expectedVertices = 21 * (n + 1) * (n + 2) / 2;
if (indicesOut.length / 3 !== expectedTriangles || positions.length !== expectedVertices) throw new Error('n32 counts mismatch.');
const pointsText = positions.map(tuple).join(', '), normalsText = normals.map(tuple).join(', '), stText = uvs.map(([u,v]) => tuple([u,1-v])).join(', '), indexText = indicesOut.join(', ');
const facesText = Array.from({ length: expectedTriangles }, () => 3).join(', ');
const template = readFileSync(join(DIR, 'source-flat-material.usda'), 'utf8');
function replaceOnce(text, regex, replacement, name) {
  const matches = text.match(regex);
  if (!matches || matches.length !== 1) throw new Error(`Expected exactly one ${name} declaration in source-flat template.`);
  return text.replace(regex, replacement);
}
let stage = template;
stage = replaceOnce(stage, /int\[\] faceVertexCounts = \[[^\]]*\]/, `int[] faceVertexCounts = [${facesText}]`, 'faceVertexCounts');
stage = replaceOnce(stage, /int\[\] faceVertexIndices = \[[^\]]*\]/, `int[] faceVertexIndices = [${indexText}]`, 'faceVertexIndices');
stage = replaceOnce(stage, /point3f\[\] points = \[[^\]]*\]/, `point3f[] points = [${pointsText}]`, 'points');
stage = replaceOnce(stage, /normal3f\[\] normals = \[[^\]]*\]/, `normal3f[] normals = [${normalsText}]`, 'normals');
stage = replaceOnce(stage, /texCoord2f\[\] primvars:st = \[[^\]]*\]/, `texCoord2f[] primvars:st = [${stText}]`, 'st');
writeFileSync(OUTPUT, stage, { flag: 'wx' });
const report = {
  source_glb: { path: SOURCE, sha256: hash(sourceBytes), bytes: sourceBytes.length },
  source_normal_map: { sha256: normalSHA, bytes: normalBytes.length, dimensions: [map.width, map.height], normalScale, raw: true, sampling: 'bilinear, clamp, glTF/Three v=0 maps to first PNG row (flipY=false)' },
  scene_transform: { source_node_identity: true, determinant: 1, positions_unchanged: true, normals_as_world_vectors_in_USD_Y_up: true, normal_inverse_transpose: 'identity', tangent_w_adjustment: 'none; determinant +1; w retained', camera_up: 'Z as in fixed Three reader' },
  source_TBN: 'Three r186 USE_TANGENT: normalize per-corner N/T, B=normalize(cross(N,T)*w); independently interpolate/normalize N,T,B at barycentric evaluation; raw normal sample, normalScale on XY, TBN multiply and normalize.',
  subdivisions_per_source_face_edge: n,
  source_faces: faces.length,
  triangles: indicesOut.length / 3,
  vertices: positions.length,
  per_face_w: Object.fromEntries(faces.map((face) => [face.sourceFaceId, face.w])),
  bounds: { min: [0,1,2].map((k) => Math.min(...positions.map((p) => p[k]))), max: [0,1,2].map((k) => Math.max(...positions.map((p) => p[k]))) },
  output: { path: OUTPUT, bytes: Buffer.byteLength(stage), sha256: hash(Buffer.from(stage)) },
  materials: { source_baseColor: 'source-base.png, sRGB', source_MR_AO: 'source-mrao.png, raw', metallicFactor: material.getMetallicFactor(), roughnessFactor: material.getRoughnessFactor(), occlusionStrength: material.getOcclusionStrength(), alphaMode: material.getAlphaMode() },
  limitations: ['w is constant per triangle in this selected patch; mixed-w faces are excluded.', 'USD direct stage, not product exporter output; no normal map on oracle stage because sampled source normals are baked into geometric vertex normals.', 'Stage is an approximation at this tessellation level; compare n16↔n32 before using it as a reference.']
};
writeFileSync(REPORT, `${JSON.stringify(report, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify({ stage: OUTPUT, triangles: report.triangles, vertices: report.vertices, sha256: report.output.sha256, bounds: report.bounds }));
