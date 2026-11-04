/**
 * Banc du réécrivain (recherche/25) : chaque système réécrit les 32 demandes du banc ; on garde le prompt, la fiche, les
 * jetons, le coût et la durée. Les clés sont lues dans ~/Desktop/Deepinfra.env par le code, jamais affichées.
 *
 *   npx tsx server/nexora/bench/reecriture.ts --etiquette 2026-11-04 --systemes actuel-glm,real-eco [--demandes id1,id2] [--plafond-usd 2]
 *
 * Systèmes : actuel-<palier|glm> (réécrivain classique, guide complet + réparations) ; real-<palier|glm> (réalisateur).
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { clientLlmDepuisEnv, type ClientLlm } from '../llm.js';
import { clientPalier, type Palier } from '../niveaux.js';
import { reecrireH3Classique } from '../reecritureH3.js';
import { realiser } from '../realisateur.js';
import { DEMANDES } from './demandesReecriture.js';
import { Releve } from '../usage.js';

const arg = (n: string, d?: string) => { const i = process.argv.indexOf(`--${n}`); return i > 0 ? process.argv[i + 1] : d; };

/** Clés des fournisseurs, lues sans jamais les écrire ailleurs que dans l'environnement des clients. */
export function clesFournisseurs(): NodeJS.ProcessEnv {
  const f = join(homedir(), 'Desktop/Deepinfra.env');
  if (!existsSync(f)) throw new Error('~/Desktop/Deepinfra.env introuvable');
  const t = readFileSync(f, 'utf8');
  const di = t.match(/^\s*deepinfra\s*[:=]\s*(\S+)/im)?.[1];
  const or = t.match(/^\s*openrouter\s*[:=]\s*(\S+)/im)?.[1];
  if (!di || !or) throw new Error('clé absente de Deepinfra.env');
  return { ...process.env, NEXORA_LLM_CLE_DEEPINFRA: di, NEXORA_LLM_CLE_OPENROUTER: or };
}

/** fetch qui additionne l'usage (coût rapporté par OpenRouter, sinon tarif) ; `effort` null = comportement de production. */
export function compteur(tarif: { entree: number; sortie: number }, effort: string | null) {
  const etat = { usd: 0, entree: 0, sortie: 0, raisonnement: 0, appels: 0 };
  const f: typeof fetch = async (url, init) => {
    const corps = init?.body ? JSON.parse(String(init.body)) : {};
    const r = await fetch(url, { ...init, body: JSON.stringify({ ...corps, usage: { include: true }, ...(effort ? { reasoning: { effort } } : {}) }) });
    etat.appels++;
    try {
      const j = (await r.clone().json()) as any;
      const pe = j.usage?.prompt_tokens ?? 0, ps = j.usage?.completion_tokens ?? 0;
      etat.entree += pe; etat.sortie += ps; etat.raisonnement += j.usage?.completion_tokens_details?.reasoning_tokens ?? 0;
      etat.usd += typeof j.usage?.cost === 'number' ? j.usage.cost : (pe * tarif.entree + ps * tarif.sortie) / 1e6;
    } catch { /* rien à compter */ }
    return r;
  };
  return { f, etat };
}

interface Mesure { usd: number; entree: number; sortie: number; raisonnement: number; appels: number }

/** Un client mesuré par système ; renvoie aussi une fonction qui lit l'usage cumulé. */
function clientDe(systeme: string, env: NodeJS.ProcessEnv): { llm: ClientLlm; lire: () => Mesure } {
  const cible = systeme.split('-')[1];
  if (cible === 'glm') {
    // Production actuelle (VM 202) : OpenRouter z-ai/glm-5.3, sans réglage du raisonnement.
    const c = compteur({ entree: 0.6, sortie: 2.2 }, null);
    const llm = clientLlmDepuisEnv({ NEXORA_LLM_BASE_URL: 'https://openrouter.ai/api/v1', NEXORA_LLM_CLE: env.NEXORA_LLM_CLE_OPENROUTER, NEXORA_LLM_MODELE: 'z-ai/glm-5.3' }, c.f)!;
    return { llm, lire: () => ({ ...c.etat }) };
  }
  const rel = new Releve({ run: systeme, tache: 'banc-reecriture' }, 50);
  const llm = clientPalier(cible as Palier, { surveillant: rel, env, autoriserRepli: true });
  return { llm, lire: () => { const t = rel.totaux; return { usd: t.coutUsd, entree: t.entree, sortie: t.sortie, raisonnement: t.raisonnement, appels: t.appels }; } };
}

async function main() {
  const etiquette = arg('etiquette', new Date().toISOString().slice(0, 10))!;
  const systemes = arg('systemes', 'actuel-glm,actuel-eco,real-eco,real-equilibre,real-expert')!.split(',');
  const ids = arg('demandes')?.split(',');
  const plafond = Number(arg('plafond-usd', '3'));
  const parallele = Number(arg('parallele', '6'));
  const demandes = DEMANDES.filter((d) => !ids || ids.includes(d.id));
  const dossier = join(import.meta.dirname, 'resultats', `reecriture-${etiquette}`);
  mkdirSync(dossier, { recursive: true });
  const sortie = join(dossier, 'candidats.jsonl');
  const faits = new Set(existsSync(sortie) ? readFileSync(sortie, 'utf8').split('\n').filter(Boolean).map((l) => { const x = JSON.parse(l); return `${x.systeme}|${x.demande}`; }) : []);
  const env = clesFournisseurs();
  let depense = 0;

  for (const systeme of systemes) {
    const file = demandes.filter((d) => !faits.has(`${systeme}|${d.id}`));
    let i = 0;
    const travailleur = async () => {
      while (i < file.length) {
        const d = file[i++];
        if (depense >= plafond) return;
        const { llm, lire } = clientDe(systeme, env);
        const entree = {
          intention: d.intention, mode: 't2va' as const, dureeS: ({ 5: 124, 10: 243, 15: 362 } as const)[d.duree] / 24,
          ...(d.replique ? { dialogues: [{ texte: d.replique, langue: 'French' }] } : {}), moteur: 'h3-fast' as const, format: d.format,
        };
        const t0 = Date.now();
        let ligne: Record<string, unknown>;
        try {
          if (systeme.startsWith('actuel')) {
            const r = await reecrireH3Classique(entree, llm);
            ligne = { prompt: r.prompt, source: r.source, tentatives: r.tentatives, erreurs: r.erreurs };
          } else {
            const r = await realiser(entree, llm);
            ligne = { prompt: r.prompt, source: "llm", tentatives: r.tentatives, erreurs: r.erreurs, historique: r.historique, fiche: r.fiche };
          }
        } catch (e) {
          ligne = { prompt: '', source: 'echec', erreurs: [(e as Error).message.slice(0, 300)] };
        }
        const m = lire();
        depense += m.usd;
        const l = { systeme, demande: d.id, famille: d.famille, ...ligne, ...m, ms: Date.now() - t0 };
        appendFileSync(sortie, JSON.stringify(l) + '\n');
        console.error(`${systeme.padEnd(15)} ${d.id.padEnd(22)} ${String(ligne.source).padEnd(6)} t${ligne.tentatives ?? '-'} ${m.entree}/${m.sortie} jetons ${m.usd.toFixed(5)} $ ${((Date.now() - t0) / 1000).toFixed(1)} s  (total ${depense.toFixed(3)} $)`);
      }
    };
    await Promise.all(Array.from({ length: parallele }, travailleur));
  }
  console.error(`fini : ${depense.toFixed(4)} USD → ${sortie}`);
}

if (process.argv[1]?.endsWith('/reecriture.ts')) main().catch((e) => { console.error(e instanceof Error ? e.message : e); process.exit(1); });
