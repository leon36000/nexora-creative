/**
 * Compose une musique avec MiniMax Music 3 (server/graphs/music3.ts) sur un moteur donné et rapatrie le fichier.
 * Usage : npx tsx scripts/nexora-musique.ts spec.json  — spec : { comfy, nom, description, paroles, dureeS, graine, sortie, devant? }
 * « devant » place la composition en tête de la file du moteur (elle dure moins d'une minute).
 * (un tableau = plusieurs compositions à la suite). Sortie : une ligne JSON par musique.
 */
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { buildMusic3Graph } from '../server/graphs/music3.js';

interface Spec { comfy: string; nom: string; description: string; paroles: string; dureeS: number; graine: number; sortie: string; devant?: boolean }

async function composer(s: Spec) {
  const graph = buildMusic3Graph({ description: s.description, paroles: s.paroles, dureeS: s.dureeS, seed: s.graine });
  (graph.save as { inputs: Record<string, unknown> }).inputs.filename_prefix = `nexora-promo/${s.nom}`;
  const t0 = performance.now();
  const r = await fetch(`${s.comfy}/prompt`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ prompt: graph, ...(s.devant ? { front: true } : {}) }) });
  const sent = (await r.json()) as { prompt_id?: string };
  if (!sent.prompt_id) throw new Error(`refus du moteur : ${JSON.stringify(sent).slice(0, 2000)}`);
  for (;;) {
    await new Promise((ok) => setTimeout(ok, 3000));
    const entry = ((await (await fetch(`${s.comfy}/history/${sent.prompt_id}`)).json()) as Record<string, any>)[sent.prompt_id];
    if (!entry) continue;
    if (entry.status?.status_str === 'error') throw new Error(`échec : ${JSON.stringify(entry.status.messages).slice(-2000)}`);
    if (!entry.status?.completed) continue;
    const f = Object.values(entry.outputs as Record<string, any>).flatMap((o: any) => o.audio ?? [])[0];
    const q = new URLSearchParams({ filename: f.filename, subfolder: f.subfolder ?? '', type: f.type ?? 'output' });
    const data = Buffer.from(await (await fetch(`${s.comfy}/view?${q}`)).arrayBuffer());
    mkdirSync(s.sortie, { recursive: true });
    const local = join(s.sortie, `${s.nom}.${f.filename.split('.').pop()}`);
    writeFileSync(local, data);
    return { nom: s.nom, secondesTotal: Math.round((performance.now() - t0) / 100) / 10, fichier: local };
  }
}

const brut = JSON.parse(readFileSync(resolve(process.argv[2]), 'utf8'));
for (const s of (Array.isArray(brut) ? brut : [brut]) as Spec[]) {
  try { console.log(JSON.stringify(await composer({ ...s, sortie: resolve(dirname(process.argv[2]), s.sortie) }))); }
  catch (e) { console.log(JSON.stringify({ nom: s.nom, erreur: (e as Error).message })); }
}
