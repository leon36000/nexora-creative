/**
 * Écrit des prompts H3 avec le réalisateur pour une liste de demandes (banc des effets visuels, recherche/25 §6).
 *   npx tsx server/nexora/bench/ecrirePrompts.ts demandes.json sortie.json [palier=expert]
 * demandes.json : [{ nom, intention, mode: 't2va'|'i2va', duree: 5|10|15, format }]
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { clientPalier, type Palier } from '../niveaux.js';
import { realiser } from '../realisateur.js';
import { Releve } from '../usage.js';
import { clesFournisseurs } from './reecriture.js';

const [entree, sortie, palier = 'expert'] = process.argv.slice(2);
const env = clesFournisseurs();
const liste = JSON.parse(readFileSync(entree, 'utf8')) as { nom: string; intention: string; mode: 't2va' | 'i2va'; duree: 5 | 10 | 15; format?: '16:9' | '9:16' | '1:1' }[];
const rel = new Releve({ run: 'prompts', tache: 'banc-vfx' }, 2);
const llm = clientPalier(palier as Palier, { surveillant: rel, env, autoriserRepli: true });
const res = await Promise.all(liste.map(async (d) => {
  const r = await realiser({ intention: d.intention, mode: d.mode, dureeS: ({ 5: 124, 10: 243, 15: 362 } as const)[d.duree] / 24, moteur: 'h3-fast', format: d.format ?? '16:9' }, llm);
  return { nom: d.nom, prompt: r.prompt, compris: r.fiche.compris };
}));
writeFileSync(sortie, JSON.stringify(res, null, 1));
console.error(`${res.length} prompts, ${rel.coutUsd.toFixed(4)} USD`);
