/**
 * Fait juger des planches de vues (JPEG, quatre côtés d'un modèle 3D) par le juge de Relief, pour le banc comparatif.
 *
 *   NEXORA_LLM_BASE_URL=… NEXORA_LLM_CLE=… [NEXORA_LLM_MODELE_JUGE3D=…] tsx scripts/relief-juge.ts <sujets.txt> <sortie.jsonl> <planche.jpg>…
 *
 * sujets.txt : une ligne « nom|description » par sujet ; le nom du fichier de planche doit contenir « NN-nom » (ex. …-01-chaise.jpg).
 * Sort une ligne JSON par planche (note, défauts, raison, jetons) ; la clé n'est jamais écrite.
 */
import { appendFileSync, readFileSync } from 'node:fs';
import { basename } from 'node:path';
import { clientLlmDepuisEnv } from '../server/nexora/llm.js';
import { jugerVuesObjet } from '../server/nexora/objet3d.js';
import { coutJuge3dUsd } from '../server/nexora/usage.js';

const [sujetsFichier, sortie, ...planches] = process.argv.slice(2);
if (!sujetsFichier || !sortie || !planches.length) { console.error('usage: relief-juge.ts <sujets.txt> <sortie.jsonl> <planche.jpg>…'); process.exit(2); }
const sujets = Object.fromEntries(readFileSync(sujetsFichier, 'utf8').split('\n').filter(Boolean).map((l) => { const [n, ...d] = l.split('|'); return [n.trim(), d.join('|').trim()]; }));
const llm = clientLlmDepuisEnv();
if (!llm) { console.error('Pas de LLM : NEXORA_LLM_BASE_URL et NEXORA_LLM_CLE sont requis.'); process.exit(2); }
for (const f of planches) {
  const nom = Object.keys(sujets).find((n) => basename(f).includes(`-${n}`)) ?? '';
  const t0 = Date.now();
  const v = await jugerVuesObjet(llm, sujets[nom] ?? basename(f), `data:image/jpeg;base64,${readFileSync(f).toString('base64')}`);
  const ligne = { fichier: basename(f), sujet: nom, note: v?.note ?? null, defauts: v?.defauts ?? [], raison: v?.raison ?? '', modele: v?.usage?.modele ?? null, entree: v?.usage?.entree ?? 0, sortie: v?.usage?.sortie ?? 0, usd: v?.usage ? +coutJuge3dUsd(v.usage).toFixed(6) : 0, ms: Date.now() - t0 };
  appendFileSync(sortie, JSON.stringify(ligne) + '\n');
  console.log(`${ligne.fichier}: ${ligne.note ?? '—'}/10 ${ligne.raison.slice(0, 100)}`);
}
