/**
 * Écrit les prompts H3 d'une liste d'intentions avec le réécrivain de Nexora Creative (LLM cloud + validateur du guide
 * officiel), exactement comme le parcours « Créer ». Sert à préparer un tournage hors interface (vidéo promotionnelle).
 * Usage (clé lue comme dans dev-nexora.sh) : npx tsx scripts/nexora-prompts.ts entree.json sortie.json
 * Entrée : [{ nom, intention, consignes?: string[], dureeS? }] ; sortie : la même liste avec prompt, source, tentatives.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { clientLlmDepuisEnv } from '../server/nexora/llm.js';
import { reecrireH3 } from '../server/nexora/reecritureH3.js';

const [entree, sortie] = process.argv.slice(2);
const plans = JSON.parse(readFileSync(entree, 'utf8')) as { nom: string; intention: string; consignes?: string[]; dureeS?: number }[];
const llm = clientLlmDepuisEnv();
if (!llm) throw new Error('LLM non configuré (NEXORA_LLM_BASE_URL, NEXORA_LLM_CLE)');
const resultats = await Promise.all(plans.map(async (p) => {
  const t0 = performance.now();
  const r = await reecrireH3({ intention: p.intention, mode: 't2va', dureeS: p.dureeS ?? 124 / 24, consignes: p.consignes }, llm);
  console.error(`${p.nom} : ${r.source}, ${r.tentatives} essai(s), ${((performance.now() - t0) / 1000).toFixed(1)} s${r.erreurs.length ? ' — ' + r.erreurs.join(' ; ') : ''}`);
  return { ...p, prompt: r.prompt, source: r.source, tentatives: r.tentatives };
}));
writeFileSync(sortie, JSON.stringify(resultats, null, 2));
