/**
 * De l'intention à la vidéo, en ligne de commande : intention en français → réécrivain H3 (LLM cloud) → rendu H3.
 * Usage : NEXORA_LLM_BASE_URL=… NEXORA_LLM_CLE=… NEXORA_LLM_MODELE=… COMFY_URL=… \
 *         npx tsx scripts/nexora-intention.ts "Fais une scène où …" [largeur] [hauteur] [images] [graine]
 */
import { buildH3Graph, H3_DISTILLED_CHECKPOINTS } from '../server/graphs/h3.js';
import { clientLlmDepuisEnv } from '../server/nexora/llm.js';
import { reecrireH3 } from '../server/nexora/reecritureH3.js';

const COMFY = process.env.COMFY_URL ?? 'http://127.0.0.1:37188';
const [intention, w = '832', h = '480', frames = '124', seed = '7'] = process.argv.slice(2);
if (!intention) throw new Error('intention manquante');
const CKPT = 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors';
if (!H3_DISTILLED_CHECKPOINTS[CKPT]) throw new Error('point de contrôle inconnu');

const t0 = performance.now();
const r = await reecrireH3({ intention, mode: 't2va', dureeS: Number(frames) / 24 }, clientLlmDepuisEnv());
const tLlm = (performance.now() - t0) / 1000;
console.error(`--- prompt (${r.source}, ${r.tentatives} tentative(s), ${tLlm.toFixed(1)} s) ---\n${r.prompt}\n---`);

const graph = buildH3Graph({ prompt: r.prompt, width: Number(w), height: Number(h), lengthFrames: Number(frames), seed: Number(seed), steps: 8, checkpoint: CKPT, withAudio: true });
(graph.save as { inputs: Record<string, unknown> }).inputs.filename_prefix = 'nexora/intention';
const t1 = performance.now();
const sent = (await (await fetch(`${COMFY}/prompt`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ prompt: graph }) })).json()) as { prompt_id?: string };
if (!sent.prompt_id) throw new Error(`refus du moteur : ${JSON.stringify(sent).slice(0, 1500)}`);
for (;;) {
  await new Promise((ok) => setTimeout(ok, 2000));
  const e = ((await (await fetch(`${COMFY}/history/${sent.prompt_id}`)).json()) as Record<string, any>)[sent.prompt_id];
  if (e?.status?.status_str === 'error') throw new Error(JSON.stringify(e.status.messages).slice(0, 2000));
  if (e?.status?.completed) {
    const files = Object.values(e.outputs as Record<string, any>).flatMap((o: any) => o.images ?? o.video ?? []);
    console.log(JSON.stringify({ source: r.source, tentatives: r.tentatives, llm_s: Number(tLlm.toFixed(1)), rendu_s: Number(((performance.now() - t1) / 1000).toFixed(1)), fichiers: files.map((f: any) => `${f.subfolder}/${f.filename}`) }));
    break;
  }
}
