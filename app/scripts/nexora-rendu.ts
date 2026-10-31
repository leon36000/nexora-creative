/**
 * Rendu H3 direct sur un moteur donné (GB10 local ou RTX 5090 de pc1 par tunnel), pour les bancs de qualité et la
 * vidéo promotionnelle. Construit le graphe avec server/graphs/h3.ts (le même que le studio), envoie l'image de départ
 * au moteur si besoin, attend la fin et rapatrie le fichier.
 * Usage : npx tsx scripts/nexora-rendu.ts spec.json   (spec : voir Spec ci-dessous ; un tableau = plusieurs rendus à la suite)
 * Sortie : une ligne JSON par rendu (moteur, réglages, secondes, fichier local).
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { buildH3Graph } from '../server/graphs/h3.js';

interface Spec {
  comfy: string; // http://127.0.0.1:37188 (GB10) ou http://127.0.0.1:37288 (5090 de pc1)
  nom: string;
  prompt: string;
  largeur?: number;
  hauteur?: number;
  images?: number;
  graine?: number;
  etapes?: number;
  checkpoint?: string;
  imageDepart?: string; // chemin local
  imageFin?: string;
  son?: boolean;
  /** Nœud de référence (point de contrôle ref2va) ; images de référence locales facultatives. */
  ref?: boolean;
  refs?: string[];
  sortie: string; // dossier local
}

async function envoyerImage(comfy: string, chemin: string): Promise<string> {
  const form = new FormData();
  form.append('image', new Blob([readFileSync(chemin)]), basename(chemin));
  form.append('overwrite', 'true');
  const r = await fetch(`${comfy}/upload/image`, { method: 'POST', body: form });
  const j = (await r.json()) as { name?: string };
  if (!j.name) throw new Error(`envoi de ${chemin} refusé : HTTP ${r.status}`);
  return j.name;
}

async function rendre(s: Spec): Promise<Record<string, unknown>> {
  const graph = buildH3Graph({
    prompt: s.prompt,
    width: s.largeur ?? 1344,
    height: s.hauteur ?? 768,
    lengthFrames: s.images ?? 124,
    seed: s.graine ?? 42,
    steps: s.etapes ?? 24,
    checkpoint: s.checkpoint,
    startImage: s.imageDepart ? await envoyerImage(s.comfy, s.imageDepart) : undefined,
    endImage: s.imageFin ? await envoyerImage(s.comfy, s.imageFin) : undefined,
    withAudio: s.son ?? true,
    refMode: s.ref,
    refImages: s.refs ? await Promise.all(s.refs.map((r) => envoyerImage(s.comfy, r))) : undefined,
  });
  (graph.save as { inputs: Record<string, unknown> }).inputs.filename_prefix = `nexora-promo/${s.nom}`;
  const t0 = performance.now();
  const r = await fetch(`${s.comfy}/prompt`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ prompt: graph }),
  });
  const sent = (await r.json()) as { prompt_id?: string };
  if (!sent.prompt_id) throw new Error(`refus du moteur : ${JSON.stringify(sent).slice(0, 2000)}`);
  for (;;) {
    await new Promise((ok) => setTimeout(ok, 3000));
    const hist = (await (await fetch(`${s.comfy}/history/${sent.prompt_id}`)).json()) as Record<string, any>;
    const entry = hist[sent.prompt_id];
    if (!entry) continue;
    if (entry.status?.status_str === 'error') throw new Error(`échec : ${JSON.stringify(entry.status.messages).slice(-2000)}`);
    if (!entry.status?.completed) continue;
    const msgs: [string, { timestamp?: number }][] = entry.status.messages ?? [];
    const at = (k: string) => msgs.find((m) => m[0] === k)?.[1]?.timestamp;
    const f = Object.values(entry.outputs as Record<string, any>).flatMap((o: any) => [...(o.video ?? []), ...(o.images ?? [])])[0];
    const q = new URLSearchParams({ filename: f.filename, subfolder: f.subfolder ?? '', type: f.type ?? 'output' });
    const data = Buffer.from(await (await fetch(`${s.comfy}/view?${q}`)).arrayBuffer());
    mkdirSync(s.sortie, { recursive: true });
    const local = join(s.sortie, `${s.nom}.mp4`);
    writeFileSync(local, data);
    return {
      nom: s.nom, comfy: s.comfy, checkpoint: s.checkpoint, etapes: s.etapes ?? 24,
      taille: `${s.largeur ?? 1344}x${s.hauteur ?? 768}`, images: s.images ?? 124, graine: s.graine ?? 42,
      secondesMoteur: at('execution_start') && at('execution_success') ? ((at('execution_success')! - at('execution_start')!) / 1000) : null,
      secondesTotal: Math.round((performance.now() - t0) / 100) / 10,
      fichier: local,
    };
  }
}

const brut = JSON.parse(readFileSync(resolve(process.argv[2]), 'utf8'));
const specs: Spec[] = Array.isArray(brut) ? brut : [brut];
for (const s of specs) {
  try {
    console.log(JSON.stringify(await rendre({ ...s, sortie: resolve(dirname(process.argv[2]), s.sortie) })));
  } catch (e) {
    console.log(JSON.stringify({ nom: s.nom, erreur: (e as Error).message }));
  }
}
