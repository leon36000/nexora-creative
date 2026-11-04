/**
 * Juge visuel à l'aveugle des paires de vidéos (recherche/25) : Gemini 4 Argon voit la planche (six images de chaque
 * vidéo, rangées X et Y) et la demande du client ; chaque paire est jugée deux fois, rangées inversées.
 * Le son n'est pas jugé (images seules) : il est écouté à part.
 *
 *   npx tsx server/nexora/bench/jugeVideos.ts <dossier-planches> <demandes.json> [--plafond-usd 2]
 * demandes.json : { "<nom de planche sans -inv>": { "intention": "...", "duree": 5, "doit": ["..."] } }
 */
import { appendFileSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { lireJson } from '../llm.js';
import { clesFournisseurs, compteur } from './reecriture.js';

const [dossier, fichierDemandes] = process.argv.slice(2);
const plafond = Number(process.argv[process.argv.indexOf('--plafond-usd') + 1] || 2);
const cle = JSON.parse(readFileSync(join(dossier, 'cle.json'), 'utf8')) as Record<string, { X: string; Y: string }>;
const demandes = JSON.parse(readFileSync(fichierDemandes, 'utf8')) as Record<string, { intention: string; duree: number; doit?: string[] }>;
const env = clesFournisseurs();
const c = compteur({ entree: 2, sortie: 10 }, 'high');

const CONSIGNE = [
  'You are a strict senior film director and VFX supervisor. You see six frames, from start to end, of two short AI-generated videos (rows X and Y) made for the same client request.',
  'Judge the final videos, not the idea. Score each from 1 to 10 on: fidelite (does it show what the client asked, checklist), image (photographic quality, artifacts, deformed bodies or objects, garbled text),',
  'mouvement (does something meaningful happen across the frames, coherent motion, no frozen or melting subject), impact (would the client be proud to post or show it), global.',
  'Be harsh: 10 = indistinguishable from a top studio, 5 = usable but generic or flawed, 1 = broken. Earlier evaluations were 1 to 3 points too generous.',
  'Answer JSON only: {"X":{"fidelite":0,"image":0,"mouvement":0,"impact":0,"global":0,"defauts":"short"},"Y":{...},"gagnant":"X|Y|egal"}',
].join('\n');

const sortie = join(dossier, 'juge-videos.jsonl');
for (const [planche, xy] of Object.entries(cle)) {
  if (c.etat.usd >= plafond) break;
  const nom = planche.replace(/-inv$/, '');
  const d = demandes[nom];
  if (!d) { console.error(`${nom} : demande inconnue`); continue; }
  const image = `data:image/jpeg;base64,${readFileSync(join(dossier, `${planche}.jpg`)).toString('base64')}`;
  try {
    const r = await c.f('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST', headers: { 'content-type': 'application/json', authorization: `Bearer ${env.NEXORA_LLM_CLE_OPENROUTER}` },
      body: JSON.stringify({
        model: 'google/gemini-4-argon', temperature: 0, max_tokens: 12000, response_format: { type: 'json_object' },
        messages: [{ role: 'system', content: CONSIGNE }, { role: 'user', content: [
          { type: 'text', text: `CLIENT REQUEST (as typed): ${d.intention}\nDuration: ${d.duree} s${d.doit?.length ? `\nChecklist: ${d.doit.join('; ')}` : ''}` },
          { type: 'image_url', image_url: { url: image } },
        ] }],
      }),
      signal: AbortSignal.timeout(300_000),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = (await r.json()) as any;
    const v = lireJson<Record<string, any>>(j.choices[0].message.content);
    const parSysteme = { [xy.X]: v.X, [xy.Y]: v.Y };
    const gagnant = v.gagnant === 'X' ? xy.X : v.gagnant === 'Y' ? xy.Y : 'egal';
    appendFileSync(sortie, JSON.stringify({ planche, nom, notes: parSysteme, gagnant }) + '\n');
    console.error(`${planche.padEnd(28)} ${xy.X}=${v.X?.global} ${xy.Y}=${v.Y?.global} → ${gagnant}  (${c.etat.usd.toFixed(3)} $)`);
  } catch (e) {
    console.error(`${planche} : échec ${(e as Error).message}`);
  }
}
console.error(`fini : ${c.etat.usd.toFixed(3)} USD`);
