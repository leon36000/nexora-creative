import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { nodeRequire, assetRoot, runRoot } from './config.mjs';

const { NodeIO } = nodeRequire('@gltf-transform/core');
const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = join(runRoot, 'payload-03');
const TARGET = join(assetRoot, 'atlas-run-01', 'quality-overlap-patch-rebaked-atlas.glb');
const baseStagePath = join(DIR, 'target-normal.usda');
const baseStage = readFileSync(baseStagePath, 'utf8');
const hash = (b) => createHash('sha256').update(b).digest('hex');
const fmt = (x) => String(+Number(x).toPrecision(9));
const tuple = (v) => `(${v.map(fmt).join(', ')})`;
function writeNew(path, data) { writeFileSync(path, data, { flag: 'wx' }); }
const yScale = 'float4 inputs:scale = (2, 2, 2, 1)\n float4 inputs:bias = (-1, -1, -1, 0)';
const yFlip = 'float4 inputs:scale = (2, -2, 2, 1)\n float4 inputs:bias = (-1, 1, -1, 0)';
if (baseStage.split(yScale).length !== 2) throw new Error('Expected one canonical normal scale/bias pair.');

const doc = await new NodeIO().read(TARGET);
const p = doc.getRoot().listMeshes()[0].listPrimitives()[0];
const uv = p.getAttribute('TEXCOORD_0');
if (!uv || uv.getCount() !== 63) throw new Error('Expected 63 target atlas UVs.');
const uvValues = Array.from({ length: uv.getCount() }, (_, i) => { const v=[0,0]; uv.getElement(i,v); return v; });
const normalStLine = `  texCoord2f[] primvars:st_normal = [${uvValues.map(([u,v]) => tuple([u,v])).join(', ')}] (interpolation = "vertex")\n`;
const baseStPattern = /  texCoord2f\[\] primvars:st = \[[^\]]*\] \(interpolation = "vertex"\)\n/;
if (!baseStPattern.test(baseStage) || baseStage.match(baseStPattern)?.length !== 1) throw new Error('Expected one shared target primvar:st declaration.');
const normalCoordPattern = /def Shader "coord_normal" \{[^}]*\}/;
const normalCoord = baseStage.match(normalCoordPattern)?.[0];
if (!normalCoord || !normalCoord.includes('string inputs:varname = "st"')) throw new Error('Expected normal coordinate reader using st.');
const normalCoordSeparated = normalCoord.replace('string inputs:varname = "st"', 'string inputs:varname = "st_normal"');
const separateNormalUv = (stage) => stage
  .replace(baseStPattern, (m) => `${m}${normalStLine}`)
  .replace(normalCoordPattern, normalCoordSeparated);

const variants = [
  { name: 'target-normal-yflip.usda', text: baseStage.replace(yScale, yFlip), change: 'invert decoded tangent-space Y by negating green scale and changing green bias; keep raw PNG and st mapping.' },
  { name: 'target-normal-vsame.usda', text: separateNormalUv(baseStage), change: 'only normal texture uses st_normal=(u,v), while base/MR/AO retain st=(u,1-v); keep raw channels and scale/bias.' },
  { name: 'target-normal-yflip-vsame.usda', text: separateNormalUv(baseStage.replace(yScale, yFlip)), change: 'invert decoded tangent-space Y and use st_normal=(u,v); base/MR/AO retain st=(u,1-v).' },
];
const files = [];
for (const item of variants) {
  const path = join(DIR, item.name), data = Buffer.from(item.text);
  writeNew(path, data);
  files.push({ path, bytes: data.length, sha256: hash(data), change: item.change });
}
const normalNode = baseStage.match(/def Shader "texture_normal" \{[^}]*\}/)?.[0];
if (!normalNode || !normalNode.includes('sourceColorSpace = "raw"') || !normalNode.includes('asset inputs:file = @target-normal.png@') || !normalNode.includes(yScale)) throw new Error('Target normal node raw/texture/scale/bias preflight failed.');
const report = {
  baseline: { path: baseStagePath, sha256: hash(Buffer.from(baseStage)), usd_normal_primvar: 'st=(u,1-v)', texture_space: 'raw', scale: [2,2,2,1], bias: [-1,-1,-1,0], normal_map_stage_file: 'target-normal.png' },
  target_glb: { path: TARGET, sha256: hash(readFileSync(TARGET)) },
  target_uv_count: uvValues.length,
  shader_variants: files,
  shader_frame_note: 'UsdPreviewSurface normal path in OpenUSD 26.03 computes TBN from dFdx/dFdy(P, st), including signDet/flipSign; variants isolate green sign and normal-only V without altering color/MR/AO coordinates.',
  limitations: ['These are lab USDA stages only; no product source change.', 'Compare against highest tessellation oracle n64, which failed the predeclared maximum-pixel convergence threshold (max delta 12, despite MAE 0.03104). Thus variant results are diagnostic relative to n64, not a converged equivalence claim.', 'The alternative sign/UV results cannot establish Apple/Quick Look conventions.'],
};
const reportPath = join(DIR, 'normal-variants-report.json');
writeNew(reportPath, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ variants: files, report: reportPath, reportSha256: hash(readFileSync(reportPath)) }));
