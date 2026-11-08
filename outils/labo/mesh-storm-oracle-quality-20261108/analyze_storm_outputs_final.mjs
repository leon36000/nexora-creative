import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { nodeRequire, assetRoot, runRoot } from './config.mjs';

const require = nodeRequire;
const sharp = require('sharp');
sharp.concurrency(2);
const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = join(runRoot, 'rendered-stages-verified');
const FIGURES = join(runRoot, 'storm-analysis-final');
if (existsSync(FIGURES)) throw new Error('No-clobber: analysis directory already exists: ' + FIGURES);
mkdirSync(FIGURES, { recursive: false });
const W = 640, H = 480, N = W * H, THRESHOLD = 3;
const hash = (b) => createHash('sha256').update(b).digest('hex');
const names = ['oracle-n4', 'oracle-n8', 'oracle-n16', 'oracle-n32-v2', 'oracle-n64', 'oracle-n16-flat', 'source-direct-normal', 'source-flat-material', 'target-flat-material', 'target-flat-normal', 'target-normal', 'target-normal-yflip', 'target-normal-vsame', 'target-normal-yflip-vsame'];
const images = new Map();
for (const name of names) {
  const raw = readFileSync(join(DIR, `${name}.rgba`));
  if (raw.length !== N * 4) throw new Error(`Wrong raw RGBA size for ${name}: ${raw.length}`);
  const stageReport = JSON.parse(readFileSync(join(DIR, `${name}.json`), 'utf8'));
  if (stageReport.renderer.toLowerCase().indexOf('llvmpipe') === -1 || stageReport.hydra_plugin !== 'HdStormRendererPlugin') throw new Error(`Renderer guard/report mismatch for ${name}`);
  const rgbMin = [255, 255, 255], rgbMax = [0, 0, 0], alphaRange = [255, 0];
  const background = [raw[0], raw[1], raw[2]];
  const mask = new Uint8Array(N);
  let maskCount = 0;
  for (let p = 0; p < N; p++) {
    const o = p * 4;
    for (let c = 0; c < 3; c++) {
      const v = raw[o + c]; rgbMin[c] = Math.min(rgbMin[c], v); rgbMax[c] = Math.max(rgbMax[c], v);
    }
    alphaRange[0] = Math.min(alphaRange[0], raw[o + 3]); alphaRange[1] = Math.max(alphaRange[1], raw[o + 3]);
    if (Math.max(Math.abs(raw[o] - background[0]), Math.abs(raw[o + 1] - background[1]), Math.abs(raw[o + 2] - background[2])) > THRESHOLD) { mask[p] = 1; maskCount++; }
  }
  const pngPath = join(FIGURES, `${name}.png`);
  const png = await sharp(raw, { raw: { width: W, height: H, channels: 4 } }).flip().png().toBuffer();
  writeFileSync(pngPath, png, { flag: 'wx' });
  images.set(name, {
    name, raw, mask, bg: background, maskCount,
    stats: { renderer: stageReport.renderer, triangles: stageReport.mesh.triangles, points: stageReport.mesh.points, bboxMin: stageReport.mesh.bbox_min, bboxMax: stageReport.mesh.bbox_max, normalMapConnected: stageReport.mesh.preview_surface_normal_links.length > 0, bboxNormalLengthMin: stageReport.mesh.normal_length_min, bboxNormalLengthMax: stageReport.mesh.normal_length_max, backgroundRGB: background, foregroundPixels: maskCount, rgbRangeMin: rgbMin, rgbRangeMax: rgbMax, alphaRange, rawSha256: stageReport.raw_rgba.sha256, pngSha256: hash(png), pngBytes: png.length },
  });
}

async function compare(aName, bName, label) {
  const a = images.get(aName), b = images.get(bName);
  let sumFull = 0, sumUnion = 0, sumIntersection = 0, union = 0, intersection = 0, changedAll = 0, changedUnion = 0, maxUnion = 0;
  for (let p = 0; p < N; p++) {
    const o = p * 4;
    const inUnion = a.mask[p] || b.mask[p];
    const inIntersection = a.mask[p] && b.mask[p];
    if (inUnion) union++;
    if (inIntersection) intersection++;
    let changed = false;
    for (let c = 0; c < 3; c++) {
      const delta = Math.abs(a.raw[o + c] - b.raw[o + c]);
      sumFull += delta;
      if (delta) changed = true;
      if (inUnion) { sumUnion += delta; maxUnion = Math.max(maxUnion, delta); }
      if (inIntersection) sumIntersection += delta;
    }
    if (changed) changedAll++;
    if (changed && inUnion) changedUnion++;
  }
  const diffRaw = Buffer.alloc(N * 4);
  for (let p = 0; p < N; p++) {
    const o = p * 4;
    for (let c = 0; c < 3; c++) diffRaw[o + c] = Math.min(255, Math.abs(a.raw[o + c] - b.raw[o + c]) * 8);
    diffRaw[o + 3] = 255;
  }
  const diffPng = await sharp(diffRaw, { raw: { width: W, height: H, channels: 4 } }).flip().png().toBuffer();
  const diffPath = join(FIGURES, `difference-x8-${label}.png`);
  writeFileSync(diffPath, diffPng, { flag: 'wx' });
  return {
    label, a: aName, b: bName, readback: 'RGBA8; compare RGB only; OpenGL bottom-row-first buffers; uncalibrated output values, not labeled linear or sRGB.',
    full_rgb_mae_byte_levels: sumFull / (N * 3),
    union_mask: { threshold_byte_delta_from_each_image_background: THRESHOLD, a_pixels: a.maskCount, b_pixels: b.maskCount, union_pixels: union, intersection_pixels: intersection, iou: union ? intersection / union : 1, rgb_mae_byte_levels: union ? sumUnion / (union * 3) : 0, rgb_max_byte_delta: maxUnion, changed_pixels: changedUnion },
    full_changed_pixels_rgb: changedAll,
    intersection_mask_rgb_mae_byte_levels: intersection ? sumIntersection / (intersection * 3) : 0,
    difference_png: { path: diffPath, bytes: diffPng.length, sha256: hash(diffPng), scale: 'absolute RGB byte delta × 8, clipped to 255' },
  };
}

const pairs = [];
for (const [a, b, label] of [
  ['oracle-n4', 'oracle-n8', 'oracle-n4-vs-n8'],
  ['oracle-n8', 'oracle-n16', 'oracle-n8-vs-n16'],
  ['oracle-n16', 'oracle-n32-v2', 'oracle-n16-vs-n32'],
  ['oracle-n32-v2', 'oracle-n64', 'oracle-n32-vs-n64'],
  ['target-normal', 'target-flat-normal', 'target-normal-vs-flat-control'],
  ['source-direct-normal', 'source-flat-material', 'source-direct-normal-vs-flat'],
  ['source-flat-material', 'target-flat-material', 'source-vs-target-material-only'],
  ['oracle-n64', 'target-normal', 'oracle-n64-vs-target-normal-usdz'],
  ['source-direct-normal', 'oracle-n64', 'storm-direct-vs-gltf-frame-oracle-n64'],
  ['source-flat-material', 'oracle-n16-flat', 'source-flat-vs-oracle-geometric-flat'],
  ['oracle-n64', 'target-normal-yflip', 'oracle-n64-vs-yflip'],
  ['oracle-n64', 'target-normal-vsame', 'oracle-n64-vs-vsame'],
  ['oracle-n64', 'target-normal-yflip-vsame', 'oracle-n64-vs-yflip-vsame'],
  ['target-normal', 'target-normal-yflip', 'standard-vs-yflip'],
  ['target-normal', 'target-normal-vsame', 'standard-vs-vsame'],
  ['target-normal', 'target-normal-yflip-vsame', 'standard-vs-yflip-vsame'],
]) pairs.push(await compare(a, b, label));

const convergence = pairs.filter((p) => p.label.startsWith('oracle-n') && p.label.includes('-vs-n')).map((p) => ({ level_pair: p.label, mae: p.union_mask.rgb_mae_byte_levels, max: p.union_mask.rgb_max_byte_delta, changed: p.union_mask.changed_pixels, pass_proposed_threshold: p.union_mask.rgb_mae_byte_levels <= 0.25 && p.union_mask.rgb_max_byte_delta <= 2 }));

const erodedDetail = (() => {
  const a = images.get('oracle-n32-v2'), b = images.get('oracle-n64');
  const mask = new Uint8Array(N);
  for (let p = 0; p < N; p++) mask[p] = a.mask[p] && b.mask[p] ? 1 : 0;
  const interior = new Uint8Array(N);
  for (let y = 2; y < H - 2; y++) for (let x = 2; x < W - 2; x++) {
    const p = y * W + x;
    if (!mask[p]) continue;
    let keep = true;
    for (let dy = -2; dy <= 2 && keep; dy++) for (let dx = -2; dx <= 2; dx++) if (!mask[(y + dy) * W + x + dx]) { keep = false; break; }
    if (keep) interior[p] = 1;
  }
  const vals = { all: [], inner: [], border: [], channelInner: [[], [], []] };
  let allCount = 0, innerCount = 0, max = -1, maxPixels = [];
  for (let p = 0; p < N; p++) {
    if (!mask[p]) continue;
    allCount++;
    const o = p * 4, d = [0,1,2].map((c) => Math.abs(a.raw[o + c] - b.raw[o + c])), v = Math.max(...d);
    vals.all.push(v);
    if (interior[p]) {
      innerCount++; vals.inner.push(v); d.forEach((x, c) => vals.channelInner[c].push(x));
    } else vals.border.push(v);
    if (v > max) { max = v; maxPixels = [{ x: p % W, y_from_bottom: Math.floor(p / W), delta_rgb: d, inner: !!interior[p] }]; }
    else if (v === max) maxPixels.push({ x: p % W, y_from_bottom: Math.floor(p / W), delta_rgb: d, inner: !!interior[p] });
  }
  const percentile = (xs, q) => { const s = [...xs].sort((x,y) => x-y); return s[Math.max(0, Math.ceil(q*s.length)-1)] ?? null; };
  const mae = (xs) => xs.length ? xs.reduce((s,x) => s+x, 0) / xs.length : null;
  const totalInside = vals.channelInner.flat();
  return {
    pair: 'oracle-n32-v2 vs oracle-n64',
    foreground_definition: `intersection of each RGBA8 render's RGB difference >${THRESHOLD} from its own pixel (0,0) background`,
    mask_intersection_pixels: allCount,
    eroded_interior: { rule: 'binary intersection mask eroded with a 5x5 square kernel (2 px each side)', pixels: innerCount, fraction: innerCount / allCount, rgb_mae_levels: mae(totalInside), max_rgb_delta_per_pixel: Math.max(...vals.inner), max_channel_percentiles_nearest_rank: Object.fromEntries([0.5,0.9,0.95,0.99,0.999].map((q) => [q, percentile(vals.inner,q)])), per_channel_percentiles_nearest_rank: vals.channelInner.map((xs) => Object.fromEntries([0.5,0.9,0.95,0.99,0.999].map((q) => [q, percentile(xs,q)]))) },
    excluded_two_pixel_border_band: { pixels: vals.border.length, rgb_mae_max_channel_levels: mae(vals.border), max_rgb_delta_per_pixel: Math.max(...vals.border), p95_max_channel_delta: percentile(vals.border,0.95), p99_max_channel_delta: percentile(vals.border,0.99) },
    whole_mask: { max_rgb_delta_per_pixel: max, max_pixels: maxPixels, max_pixel_count: maxPixels.length },
    pixel_coordinate_note: 'x/y_from_bottom refer to OpenGL glReadPixels buffer coordinates (origin bottom-left).',
  };
})();
const summary = {
  method: 'Same OpenUSD 26.03 Hydra Storm / llvmpipe CPU renderer per stage in a fresh isolated process. No Three↔Storm pixel comparison.',
  conditions: { viewport: [W, H], camera_shared: true, lighting_shared: true, background_shared: true, cpu_threads: 2, network: 'bwrap --unshare-net', llvmpipe_gate: 'renderer must contain llvmpipe', mask_rule: `RGB differs from that image's pixel (0,0) background by >${THRESHOLD} byte levels in any channel`, pbr_maps: 'source oracle/direct/source-flat use source baseColor+MR/AO; target stages use target baseColor+MR/AO; baseColor sRGB; MR/AO/normal raw; each stage uses its own UVs with USD st=(u,1-v).',
  },
  renders: Object.fromEntries([...images].map(([k, v]) => [k, v.stats])),
  comparisons: pairs,
  oracle_convergence: { proposed_threshold: { union_mask_rgb_mae_byte_levels: 0.25, max_byte_delta: 2 }, levels: convergence, converged_by_n64: convergence.find((x) => x.level_pair === 'oracle-n32-vs-n64')?.pass_proposed_threshold ?? false, maximum_level_tested: 64, refinement_stopped_at_n64: true, n32_n64_detail: erodedDetail },
  interpretation_limits: ['The strict predeclared convergence threshold fails at n32↔n64 because the single boundary max delta is 12; after 2 px erosion the interior max is 1, but this does not override the global criterion.', 'Storm response/sensitivity is tested only under this fixed render setup.', 'Oracle samples the source normal map and TBN field at tessellated barycentric vertices; convergence is necessary but not sufficient to reproduce all fragment interpolation.', 'Material-only source/target pair holds geometry and geometric normals fixed but includes Storm texture filtering, atlas resampling and the two maps; it is not an independent lighting model comparison.', 'The target USDZ is a lab package assembled from USDA and the rebaked target texture octets; it is not produced by the product exporter, which still refuses normal/AO maps.', 'Y/V variants are diagnostics against the highest level n64, not a converged comparison; no interpretation can be generalized to Apple/Quick Look or other USD/glTF readers.'],
};
const out = join(runRoot, 'storm-render-metrics-final.json');
writeFileSync(out, `${JSON.stringify(summary, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify({ out, convergence, comparisons: pairs.map((p) => ({ label: p.label, mae: p.union_mask.rgb_mae_byte_levels, max: p.union_mask.rgb_max_byte_delta, changed: p.union_mask.changed_pixels, iou: p.union_mask.iou })), sha256: hash(readFileSync(out)) }));
