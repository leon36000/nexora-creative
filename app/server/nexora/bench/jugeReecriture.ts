/**
 * Juge à l'aveugle du banc du réécrivain (recherche/25) : Gemini 4 Argon, raisonnement élevé (OpenRouter). Pour chaque
 * demande, les prompts des systèmes sont mélangés, nommés A, B, C… et notés ensemble, deux fois avec deux ordres
 * différents (biais de position). Le juge voit la demande du client et la liste de ce qu'elle exige ; jamais le nom
 * des systèmes.
 *
 *   npx tsx server/nexora/bench/jugeReecriture.ts --etiquette 2026-11-04 [--systemes a,b,c] [--passes 2] [--plafond-usd 4]
 */
import { appendFileSync, existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { lireJson } from '../llm.js';
import { DEMANDES } from './demandesReecriture.js';
import { clesFournisseurs, compteur } from './reecriture.js';

const arg = (n: string, d?: string) => { const i = process.argv.indexOf(`--${n}`); return i > 0 ? process.argv[i + 1] : d; };

/** Mélange déterministe (graine) : les deux passes ont des ordres différents mais reproductibles. */
function melange<T>(x: T[], graine: number): T[] {
  const a = [...x];
  let s = graine >>> 0;
  for (let i = a.length - 1; i > 0; i--) {
    s = (s * 1664525 + 1013904223) >>> 0;
    const j = s % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export const CONSIGNES_JUGE = [
  'You are a strict senior film director and VFX supervisor judging prompts written for MiniMax H3, a text-to-audio+video diffusion model.',
  'A client typed a short, careless request. Several assistants rewrote it into an H3 prompt. Judge which prompt will produce the best final video for this client.',
  'Score each prompt from 1 to 10 on:',
  '- fidelite: keeps everything the client asked (see the checklist), contradicts nothing, adds no unrequested on-screen text, brands or protected characters, client dialogue verbatim.',
  '- realisation: director and cinematographer craft: framing and lens, timed action, motivated lighting, materials, camera grammar, sound design, music fit.',
  '- filmabilite: H3 can actually render it convincingly in the duration: not overloaded, one clear action per shot, physically coherent, consistent characters, sensible shot timing.',
  '- impact: how strong the resulting video will be for the client\'s purpose (an ad that sells, a film that moves, a spectacular effect, a clear lesson).',
  '- global: overall expected quality of the final video. 10 = indistinguishable from a top studio; 5 = usable but generic; 1 = wrong or broken.',
  'Be harsh and use the whole scale: earlier evaluations were 1 to 3 points too generous. Longer is not better by itself; penalize padding, redundancy and contradictions.',
  'Answer with JSON only: {"notes":{"A":{"fidelite":0,"realisation":0,"filmabilite":0,"impact":0,"global":0,"defauts":"short"}, ...},"classement":["best label", "..."]}',
].join('\n');

async function main() {
  const etiquette = arg('etiquette', new Date().toISOString().slice(0, 10))!;
  const dossier = join(import.meta.dirname, 'resultats', `reecriture-${etiquette}`);
  const cands = readFileSync(join(dossier, 'candidats.jsonl'), 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l));
  const systemes = arg('systemes')?.split(',') ?? [...new Set(cands.map((c) => c.systeme as string))];
  const passes = Number(arg('passes', '2'));
  const plafond = Number(arg('plafond-usd', '4'));
  const effort = arg('effort', 'high')!;
  const sortie = join(dossier, `juge-${arg('nom', 'argon')}.jsonl`);
  const faits = new Set(existsSync(sortie) ? readFileSync(sortie, 'utf8').split('\n').filter(Boolean).map((l) => { const x = JSON.parse(l); return `${x.demande}|${x.passe}`; }) : []);
  const env = clesFournisseurs();
  const c = compteur({ entree: 2, sortie: 10 }, effort);

  const taches: { d: (typeof DEMANDES)[number]; passe: number }[] = [];
  for (const d of DEMANDES) for (let p = 1; p <= passes; p++) if (!faits.has(`${d.id}|${p}`)) taches.push({ d, passe: p });
  let i = 0;
  const travailleur = async () => {
    while (i < taches.length) {
      const { d, passe } = taches[i++];
      if (c.etat.usd >= plafond) return;
      const ici = systemes.map((s) => cands.find((x) => x.systeme === s && x.demande === d.id)).filter((x) => x && x.prompt);
      const ordre = melange(ici, passe * 7919 + d.id.length * 31 + d.id.charCodeAt(0));
      const lettres = ordre.map((_, k) => String.fromCharCode(65 + k));
      const user = [
        `CLIENT REQUEST (as typed): ${d.intention}`,
        `Duration: ${d.duree} s · format ${d.format}${d.replique ? ` · line the client wants spoken, verbatim: «${d.replique}»` : ''}`,
        `Checklist of what the client needs: ${d.doit.join('; ')}`,
        '',
        ...ordre.map((x, k) => `=== PROMPT ${lettres[k]} ===\n${x.prompt}\n`),
      ].join('\n');
      const t0 = Date.now();
      try {
        const r = await c.f('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST', headers: { 'content-type': 'application/json', authorization: `Bearer ${env.NEXORA_LLM_CLE_OPENROUTER}` },
          body: JSON.stringify({ model: 'google/gemini-4-argon', messages: [{ role: 'system', content: CONSIGNES_JUGE }, { role: 'user', content: user }], temperature: 0, max_tokens: 16000, response_format: { type: 'json_object' } }),
          signal: AbortSignal.timeout(300_000),
        });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = (await r.json()) as any;
        const v = lireJson<{ notes: Record<string, Record<string, unknown>>; classement: string[] }>(j.choices[0].message.content);
        const notes = Object.fromEntries(ordre.map((x, k) => [x.systeme, v.notes?.[lettres[k]] ?? null]));
        const rang = Object.fromEntries(ordre.map((x, k) => [x.systeme, (v.classement ?? []).indexOf(lettres[k]) + 1 || null]));
        appendFileSync(sortie, JSON.stringify({ demande: d.id, famille: d.famille, passe, ordre: ordre.map((x) => x.systeme), notes, rang, ms: Date.now() - t0 }) + '\n');
        console.error(`${d.id.padEnd(22)} p${passe} ${ordre.map((x, k) => `${x.systeme}=${(v.notes?.[lettres[k]] as any)?.global ?? '?'}`).join(' ')}  (${c.etat.usd.toFixed(3)} $)`);
      } catch (e) {
        console.error(`${d.id} p${passe} : échec ${(e as Error).message}`);
      }
    }
  };
  await Promise.all(Array.from({ length: Number(arg('parallele', '6')) }, travailleur));
  console.error(`juge fini : ${c.etat.usd.toFixed(3)} USD, ${c.etat.entree} / ${c.etat.sortie} jetons → ${sortie}`);
}

main().catch((e) => { console.error(e instanceof Error ? e.message : e); process.exit(1); });
