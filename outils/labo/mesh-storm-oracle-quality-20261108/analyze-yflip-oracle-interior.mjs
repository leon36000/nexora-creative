import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runRoot } from './config.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const DIR = join(runRoot, 'rendered-stages-verified');
const OUT = join(runRoot, 'storm-analysis-final');
const W = 640, H = 480, N = W * H, THRESHOLD = 3;
const hash = (b) => createHash('sha256').update(b).digest('hex');
const configs = [
  { oracle: 'oracle-n32-v2', variant: 'target-normal-yflip', label: 'yflip-vs-n32' },
  { oracle: 'oracle-n64', variant: 'target-normal-yflip', label: 'yflip-vs-n64' },
];
function load(name) {
  const raw = readFileSync(join(DIR, `${name}.rgba`));
  if (raw.length !== W * H * 4) throw new Error(`Bad RGBA size: ${name}`);
  const background = [raw[0], raw[1], raw[2]], mask = new Uint8Array(N);
  let count = 0;
  for (let p = 0; p < N; p++) {
    const o = p * 4;
    if (Math.max(Math.abs(raw[o] - background[0]), Math.abs(raw[o+1] - background[1]), Math.abs(raw[o+2] - background[2])) > THRESHOLD) { mask[p] = 1; count++; }
  }
  return { name, raw, background, mask, maskCount: count };
}
const percentile = (xs, q) => { const sorted = [...xs].sort((a,b) => a-b); return sorted[Math.max(0, Math.ceil(q * sorted.length) - 1)] ?? null; };
function compare(oracleName, variantName, label) {
  const a = load(oracleName), b = load(variantName), unionMask = new Uint8Array(N), intersection = new Uint8Array(N);
  let unionCount = 0, intersectionCount = 0, changedUnion = 0, fullChanged = 0, maxUnion = 0;
  const unionDeltaMax = [], intersectionDeltaMax = [], intersectionChannel = [[],[],[]], sumUnion = [0,0,0], sumFull = [0,0,0];
  const maxLocations = [];
  for (let p = 0; p < N; p++) {
    const inUnion = a.mask[p] || b.mask[p], inInter = a.mask[p] && b.mask[p];
    if (inUnion) { unionMask[p] = 1; unionCount++; }
    if (inInter) { intersection[p] = 1; intersectionCount++; }
    const o = p * 4, delta = [0,1,2].map((c) => Math.abs(a.raw[o+c] - b.raw[o+c]));
    const pixelDelta = Math.max(...delta);
    let changed = false;
    for (let c = 0; c < 3; c++) { sumFull[c] += delta[c]; if (inUnion) sumUnion[c] += delta[c]; if (delta[c]) changed = true; }
    if (changed) { fullChanged++; if (inUnion) changedUnion++; }
    if (inUnion) { unionDeltaMax.push(pixelDelta); maxUnion = Math.max(maxUnion, pixelDelta); }
    if (inInter) { intersectionDeltaMax.push(pixelDelta); delta.forEach((x,c) => intersectionChannel[c].push(x)); }
  }
  const interior = new Uint8Array(N);
  for (let y = 2; y < H - 2; y++) for (let x = 2; x < W - 2; x++) {
    const p = y * W + x;
    if (!intersection[p]) continue;
    let keep = true;
    for (let dy = -2; dy <= 2 && keep; dy++) for (let dx = -2; dx <= 2; dx++) if (!intersection[(y+dy)*W+x+dx]) { keep = false; break; }
    if (keep) interior[p] = 1;
  }
  const inside = [], border = [], insideChannels = [[],[],[]], borderCoords = [];
  for (let p = 0; p < N; p++) if (intersection[p]) {
    const o=p*4, d=[0,1,2].map((c)=>Math.abs(a.raw[o+c]-b.raw[o+c])), v=Math.max(...d);
    if (interior[p]) { inside.push(v); d.forEach((x,c)=>insideChannels[c].push(x)); }
    else { border.push(v); if (v === maxUnion) borderCoords.push({x:p%W,y_from_bottom:Math.floor(p/W),delta_rgb:d}); }
    if (v === maxUnion) maxLocations.push({x:p%W,y_from_bottom:Math.floor(p/W),delta_rgb:d,inside:!!interior[p]});
  }
  const top = [0.5,0.9,0.95,0.99,0.999];
  const pixelSum = (xs) => xs.reduce((s,x)=>s+x,0);
  return {
    label, oracle: oracleName, variant: variantName,
    images: { oracle_rgba_sha256: hash(a.raw), variant_rgba_sha256: hash(b.raw), dimensions: [W,H], byte_format: 'RGBA8, raw OpenGL readback' },
    foreground: { threshold: `any RGB channel differs by >${THRESHOLD} byte levels from that render's own pixel (0,0) background`, oracle_pixels:a.maskCount, variant_pixels:b.maskCount, union_pixels:unionCount, intersection_pixels:intersectionCount, iou:unionCount ? intersectionCount/unionCount : 1, union_rgb_mae_levels: sumUnion.reduce((s,x)=>s+x,0)/(unionCount*3), union_max_rgb_delta:maxUnion, union_changed_pixels:changedUnion, full_image_rgb_mae_levels:sumFull.reduce((s,x)=>s+x,0)/(N*3), full_image_changed_pixels:fullChanged },
    intersection_interior: { erosion:'5x5 square kernel, 2 pixels on all sides from intersection foreground mask', pixels:inside.length, rgb_mae_levels:inside.length ? insideChannels.flat().reduce((s,x)=>s+x,0)/(inside.length*3) : null, max_delta_per_pixel:inside.length ? Math.max(...inside) : null, max_rgb_delta_channel_percentiles_nearest_rank:Object.fromEntries(top.map((q)=>[q,percentile(inside,q)])), per_channel_percentiles_nearest_rank:insideChannels.map((xs)=>Object.fromEntries(top.map((q)=>[q,percentile(xs,q)]))) },
    excluded_two_pixel_border: { pixels:border.length, max_delta_per_pixel:border.length ? Math.max(...border) : null, p95_max_delta:percentile(border,0.95), p99_max_delta:percentile(border,0.99), max_delta_locations:borderCoords.slice(0,50) },
    max_delta_locations_all_mask:maxLocations.slice(0,50),
    pixel_coordinates:'x/y_from_bottom (origin bottom-left), matching raw glReadPixels buffers.',
  };
}
const report = {
  definition: { renderer:'OpenUSD 26.03 Hydra Storm / llvmpipe', fresh_process_per_stage:true, threads:2, network:'bwrap --unshare-net', compare_rgb_only:true, no_sRGB_or_linear_claim:true, source_images_own_background:true },
  convergence_status:'n64 still fails the predeclared global max-delta criterion; these Y-flip comparisons are diagnostic against n32/n64, not a converged oracle.',
  comparisons: configs.map((c)=>compare(c.oracle,c.variant,c.label)),
};
const path=join(OUT,'yflip-oracle-interior-report.json');
writeFileSync(path,`${JSON.stringify(report,null,2)}\n`,{flag:'wx'});
console.log(JSON.stringify({path,sha256:hash(readFileSync(path)),comparisons:report.comparisons.map((x)=>({label:x.label,unionMae:x.foreground.union_rgb_mae_levels,unionMax:x.foreground.union_max_rgb_delta,inside:x.intersection_interior.pixels,insideMax:x.intersection_interior.max_delta_per_pixel,insideP95:x.intersection_interior.max_rgb_delta_channel_percentiles_nearest_rank['0.95'],border:x.excluded_two_pixel_border.pixels,borderMax:x.excluded_two_pixel_border.max_delta_per_pixel}))}));
