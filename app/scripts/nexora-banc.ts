/**
 * Banc d'essai Nexora : envoie un graphe H3 construit par server/graphs/h3.ts à un ComfyUI, attend la fin et mesure.
 * Usage : COMFY_URL=http://127.0.0.1:37188 npx tsx scripts/nexora-banc.ts [largeur] [hauteur] [images] [graine]
 * Sortie : une ligne JSON par rendu (temps total, fichier produit), à recopier dans recherche/08-mesures-gb10.md.
 */
import { buildH3Graph } from '../server/graphs/h3.js';

const COMFY = process.env.COMFY_URL ?? 'http://127.0.0.1:37188';
const [w = '832', h = '480', frames = '124', seed = '42'] = process.argv.slice(2);

const prompt = `integrated_multimodal_description: [Shot 1] Cinematic wide shot at golden hour. A red vintage sports car is parked on a wet coastal road; the camera slowly orbits the car from its front left to its side while the low sun flares across the lens. Waves crash against black rocks in the background, sea spray catches the light, reflections ripple on the asphalt. Shallow depth of field, anamorphic look, rich warm color grade.
overall_soundscape: steady ocean waves, light wind, distant seagulls, a faint engine tick as the metal cools.
non_diegetic_music: none.`;

async function rendu(): Promise<Record<string, unknown>> {
  const graph = buildH3Graph({
    prompt,
    width: Number(w),
    height: Number(h),
    lengthFrames: Number(frames),
    seed: Number(seed),
    steps: 8,
    checkpoint: 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors',
    withAudio: true,
  });
  (graph.save as { inputs: Record<string, unknown> }).inputs.filename_prefix = 'nexora/banc_h3';
  const t0 = performance.now();
  const r = await fetch(`${COMFY}/prompt`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ prompt: graph }),
  });
  const sent = (await r.json()) as { prompt_id?: string; error?: unknown; node_errors?: unknown };
  if (!sent.prompt_id) throw new Error(`refus du moteur : ${JSON.stringify(sent).slice(0, 2000)}`);
  for (;;) {
    await new Promise((ok) => setTimeout(ok, 2000));
    const hist = (await (await fetch(`${COMFY}/history/${sent.prompt_id}`)).json()) as Record<string, any>;
    const entry = hist[sent.prompt_id];
    if (!entry) continue;
    const status = entry.status?.status_str;
    if (status === 'error') throw new Error(`échec : ${JSON.stringify(entry.status.messages).slice(0, 3000)}`);
    if (entry.status?.completed) {
      const files = Object.values(entry.outputs as Record<string, any>).flatMap((o: any) => [
        ...(o.images ?? []),
        ...(o.video ?? []),
        ...(o.gifs ?? []),
      ]);
      return { secondes: Math.round((performance.now() - t0) / 100) / 10, largeur: w, hauteur: h, images: frames, graine: seed, fichiers: files };
    }
  }
}

console.log(JSON.stringify(await rendu()));
