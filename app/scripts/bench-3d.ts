/**
 * Banc 3D sur un ComfyUI local : joue le graphe Qwen-Image (référence) ou TRELLIS.2 et mesure
 * le temps par nœud (via le WebSocket de ComfyUI), la mémoire GPU/unifiée et la taille du GLB.
 *
 *   tsx scripts/bench-3d.ts still "<prompt>" <sortie.png> [seed]
 *   tsx scripts/bench-3d.ts object <image.png> <draft|quality> <dossier-sortie> [seed]
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { buildStillsGraph } from '../server/graphs/stills.js';
import { buildTrellisGraph } from '../server/graphs/trellis.js';

const URL_ = process.env.COMFY_URL ?? 'http://127.0.0.1:37188';

async function uploadImage(path: string): Promise<string> {
  const name = `bench3d_${Date.now()}.png`;
  const fd = new FormData();
  fd.append('image', new Blob([readFileSync(path)], { type: 'image/png' }), name);
  const r = await fetch(`${URL_}/upload/image`, { method: 'POST', body: fd });
  if (!r.ok) throw new Error(`upload: ${r.status}`);
  return ((await r.json()) as { name: string }).name;
}

function memMo(): number {
  try { return Number(execSync("free -m | awk '/Mem/{print $3}'").toString().trim()); } catch { return 0; }
}
function gpuMo(): number {
  try { return Number(execSync('nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null').toString().trim().split('\n')[0]) || 0; } catch { return 0; }
}

async function run(graph: Record<string, unknown>) {
  const clientId = `bench-${Date.now()}`;
  const ws = new WebSocket(`${URL_.replace('http', 'ws')}/ws?clientId=${clientId}`);
  await new Promise((res, rej) => { ws.onopen = () => res(null); ws.onerror = rej; });
  const classOf = (id: string) => (graph[id] as { class_type: string } | undefined)?.class_type ?? id;
  const stages: { node: string; cls: string; s: number }[] = [];
  let cur: string | null = null; let t0 = 0; let peakRam = memMo(); let peakGpu = gpuMo();
  const ram0 = peakRam;
  const sampler = setInterval(() => { peakRam = Math.max(peakRam, memMo()); peakGpu = Math.max(peakGpu, gpuMo()); }, 1500);
  const done = new Promise<string>((resolve, reject) => {
    ws.onmessage = (ev) => {
      if (typeof ev.data !== 'string') return;
      const m = JSON.parse(ev.data) as { type: string; data: any };
      if (m.type === 'executing') {
        const now = Date.now();
        if (cur) stages.push({ node: cur, cls: classOf(cur), s: (now - t0) / 1000 });
        cur = m.data.node; t0 = now;
        if (m.data.node === null && m.data.prompt_id) resolve(m.data.prompt_id);
      }
      if (m.type === 'execution_error') reject(new Error(JSON.stringify(m.data).slice(0, 800)));
    };
  });
  const start = Date.now();
  const r = await fetch(`${URL_}/prompt`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ prompt: graph, client_id: clientId }) });
  if (!r.ok) throw new Error(`prompt: ${r.status} ${(await r.text()).slice(0, 1500)}`);
  const pid = await done;
  clearInterval(sampler); ws.close();
  const total = (Date.now() - start) / 1000;
  const h = ((await (await fetch(`${URL_}/history/${pid}`)).json()) as any)[pid];
  return { pid, total, stages, h, ramDeltaMo: peakRam - ram0, peakGpuMo: peakGpu, peakRamMo: peakRam };
}

async function main() {
  const [mode, ...a] = process.argv.slice(2);
  if (mode === 'still') {
    const [prompt, out, seed = '7'] = a;
    const g = buildStillsGraph({ model: 'qwen21', quality: 'quality', prompt, width: 1024, height: 1024, seed: Number(seed) });
    const r = await run(g);
    const img = r.h.outputs.save.images[0];
    const f = await fetch(`${URL_}/view?filename=${img.filename}&subfolder=${img.subfolder}&type=${img.type}`);
    writeFileSync(out, Buffer.from(await f.arrayBuffer()));
    console.log(JSON.stringify({ total: r.total, ramDeltaMo: r.ramDeltaMo, peakGpuMo: r.peakGpuMo }));
    return;
  }
  const [image, quality, dir, seed = '1'] = a;
  mkdirSync(dir, { recursive: true });
  const name = await uploadImage(image);
  const g = buildTrellisGraph({ image: name, seed: Number(seed), quality: quality as 'draft' | 'quality', removeBackground: true, turntableFrames: 0, filenamePrefix: `bench3d/${quality}` });
  const r = await run(g);
  const glb = Object.values(r.h.outputs as Record<string, any>).flatMap((o) => o['3d'] ?? [])[0];
  const f = await fetch(`${URL_}/view?filename=${glb.filename}&subfolder=${glb.subfolder ?? ''}&type=${glb.type ?? 'output'}`);
  const buf = Buffer.from(await f.arrayBuffer());
  writeFileSync(`${dir}/${quality}.glb`, buf);
  const byCls: Record<string, number> = {};
  for (const s of r.stages) byCls[s.cls] = (byCls[s.cls] ?? 0) + s.s;
  const top = Object.entries(byCls).sort((x, y) => y[1] - x[1]).slice(0, 10).map(([k, v]) => `${k}=${v.toFixed(1)}s`);
  const res = { quality, totalS: +r.total.toFixed(1), glbMo: +(buf.length / 1e6).toFixed(2), ramPicMo: r.peakRamMo, ramDeltaMo: r.ramDeltaMo, gpuPicMo: r.peakGpuMo, top };
  writeFileSync(`${dir}/${quality}.json`, JSON.stringify({ ...res, stages: r.stages }, null, 1));
  console.log(JSON.stringify(res));
}
main().catch((e) => { console.error(e); process.exit(1); });
