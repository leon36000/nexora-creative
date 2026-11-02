/**
 * Banc de montage (recherche/14 §5 et §9) : 3 bras × 12 briefs × répétitions, score en code (aucun rendu, aucun GPU).
 *   npx tsx server/nexora/bench/lancer.ts [--reps 3] [--partitions apprentissage,validation,test] [--briefs id,id]
 *        [--bras code,a0,a1] [--modele z-ai/glm-5.3] [--plafond-usd 3] [--etiquette nom] [--a-blanc]
 * Bras : code = montage_auto seul ; a0 = GLM tel quel (format EditPlan + brief, un seul appel, rien d'autre) ;
 *        a1 = GLM + recette et exemplaire top-1 + validateur avec 1 réparation (indices de fonction) + 1 tour critique.
 * La clé OpenRouter est lue au lancement dans ~/Desktop/Deepinfra.env (comme scripts/dev-nexora.sh lit son .env) ;
 * elle n'est ni affichée ni écrite. Dépense plafonnée (défaut 3 USD) : le banc s'arrête et sauvegarde si elle est atteinte.
 * Toutes les réponses brutes sont conservées (leçon du 03/10 : sorties tronquées, cause non prouvable).
 */
import { mkdirSync, readFileSync, writeFileSync, appendFileSync, existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { clientLlmDepuisEnv, type ClientLlm } from '../llm.js';
import { montageAuto } from '../montage/auto.js';
import { mesurer } from '../montage/metriques.js';
import { planifierMontage } from '../montage/planifier.js';
import { BRIEFS } from './briefs.js';
import { compareApparie, icMoyenne, moyenne } from './stats.js';

type Bras = 'code' | 'a0' | 'a1';
const NOMS: Record<Bras, string> = { code: 'montage_auto (code seul)', a0: 'GLM tel quel', a1: 'GLM + exemplaire + validateur + 1 critique' };

function arg(nom: string, def?: string): string | undefined {
  const i = process.argv.indexOf(`--${nom}`);
  return i >= 0 ? (process.argv[i + 1]?.startsWith('--') || i + 1 >= process.argv.length ? 'oui' : process.argv[i + 1]) : def;
}

export class ErreurPlafond extends Error {}

/** Lit la clé OpenRouter du Bureau sans jamais la renvoyer ailleurs que dans l'environnement du client. */
function cleOpenRouter(): string {
  const f = join(homedir(), 'Desktop/Deepinfra.env');
  if (!existsSync(f)) throw new Error('~/Desktop/Deepinfra.env introuvable');
  const m = readFileSync(f, 'utf8').match(/^\s*openrouter\s*[:=]\s*(\S+)/im);
  if (!m) throw new Error('clé OpenRouter absente de Deepinfra.env');
  return m[1];
}

/**
 * fetch qui compte les jetons et les dollars de chaque réponse et refuse d'appeler au-delà du plafond. */
export function fetchCompteur(plafondUsd: number, tarif = { entree: 0.6, sortie: 2.2 }, effortRaisonnement: 'low' | 'medium' | 'high' | null = 'low') {
  const etat = { usd: 0, entree: 0, sortie: 0, appels: 0, coutReel: 0 };
  const f: typeof fetch = async (url, init) => {
    if (etat.usd >= plafondUsd) throw new ErreurPlafond(`plafond de ${plafondUsd} USD atteint (${etat.usd.toFixed(3)})`);
    const corps = init?.body ? JSON.parse(String(init.body)) : {};
    const r = await fetch(url, { ...init, body: JSON.stringify({ ...corps, usage: { include: true }, ...(effortRaisonnement ? { reasoning: { effort: effortRaisonnement } } : {}) }) });
    etat.appels++;
    try {
      const j = (await r.clone().json()) as { usage?: { prompt_tokens?: number; completion_tokens?: number; cost?: number } };
      const pe = j.usage?.prompt_tokens ?? 0, ps = j.usage?.completion_tokens ?? 0;
      etat.entree += pe; etat.sortie += ps;
      if (typeof j.usage?.cost === 'number') { etat.usd += j.usage.cost; etat.coutReel += j.usage.cost; } else etat.usd += (pe * tarif.entree + ps * tarif.sortie) / 1e6;
    } catch { /* réponse non JSON : rien à compter */ }
    return r;
  };
  return { f, etat };
}

interface Essai { brief: string; partition: string; genre: string; bras: Bras; rep: number; brut: number; avecRepli: number; porteBrut: boolean; premierCoup: boolean; source: string; appels: number; jetons: number; usd: number; notes: string[]; ecartsRestants: number; secondes: number }

async function main() {
  const reps = Number(arg('reps', '3'));
  const partitions = (arg('partitions', 'apprentissage,validation,test') as string).split(',');
  const ids = arg('briefs')?.split(',');
  const bras = (arg('bras', 'code,a0,a1') as string).split(',') as Bras[];
  const modele = arg('modele', 'z-ai/glm-5.3') as string;
  const plafond = Number(arg('plafond-usd', '3'));
  const etiquette = arg('etiquette', new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-')) as string;
  const briefs = BRIEFS.filter((b) => partitions.includes(b.partition) && (!ids || ids.includes(b.id)));
  const dossier = join(import.meta.dirname, 'resultats', etiquette);
  mkdirSync(dossier, { recursive: true });

  const compteur = fetchCompteur(plafond);
  const llm: ClientLlm | null = bras.some((b) => b !== 'code') && !arg('a-blanc')
    ? clientLlmDepuisEnv({ NEXORA_LLM_BASE_URL: 'https://openrouter.ai/api/v1', NEXORA_LLM_CLE: cleOpenRouter(), NEXORA_LLM_MODELE: modele }, compteur.f)
    : null;
  const essais: Essai[] = [];
  const registre = join(dossier, 'registre.jsonl');
  const brutes: string[] = [];
  let arret = '';
  console.error(`banc ${etiquette} : ${briefs.length} briefs × ${reps} rép. × bras ${bras.join('+')} ; modèle ${modele} ; plafond ${plafond} USD`);

  boucle: for (const b of briefs) {
    for (let rep = 1; rep <= reps; rep++) {
      for (const br of bras) {
        if (br === 'code' && rep > 1) continue; // déterministe : une seule répétition
        const t0 = Date.now(), avant = { ...compteur.etat };
        try {
          let plan, source = 'code', premier = true, appels = 0, notes: string[] = [], bruts: string[] = [];
          if (br === 'code') plan = montageAuto(b);
          else {
            const r = await planifierMontage(llm, b, br === 'a0' ? { memoire: false, reparations: 0, tours: 0, maxAppels: 1, temperature: 0.3 } : { memoire: true, reparations: 1, tours: 1, maxAppels: 4, temperature: 0.3 });
            plan = r.plan; source = r.source; premier = r.valideDuPremierCoup; appels = r.appels; notes = r.notes; bruts = r.brutes;
          }
          const m = mesurer(plan, b);
          const e: Essai = {
            brief: b.id, partition: b.partition, genre: b.genre, bras: br, rep,
            // brut : si le modèle n'a pas livré de plan valide, 0 ; avecRepli : ce que la personne reçoit (montage_auto en secours).
            brut: source === 'repli' ? 0 : m.composite, avecRepli: m.composite, porteBrut: source !== 'repli', premierCoup: br === 'code' ? true : premier,
            source, appels, jetons: compteur.etat.entree + compteur.etat.sortie - avant.entree - avant.sortie, usd: compteur.etat.usd - avant.usd, notes, ecartsRestants: m.ecarts.length, secondes: (Date.now() - t0) / 1000,
          };
          essais.push(e);
          appendFileSync(registre, JSON.stringify({ ...e, metriques: Object.fromEntries(Object.entries(m.metriques).map(([k, v]) => [k, v.score])), credits: m.credits, versions: (plan.metadonnees?.savoir ?? []) }) + '\n');
          if (bruts.length) brutes.push(JSON.stringify({ brief: b.id, bras: br, rep, reponses: bruts }));
          console.error(`${b.id.padEnd(16)} ${br} r${rep}  brut ${e.brut.toFixed(3)}  repli ${e.avecRepli.toFixed(3)}  ${source}${premier ? '' : ' (réparé)'}  ${compteur.etat.usd.toFixed(3)} USD`);
        } catch (err) {
          if (err instanceof ErreurPlafond) { arret = err.message; break boucle; }
          throw err;
        }
      }
    }
  }
  if (brutes.length) writeFileSync(join(dossier, 'brutes.jsonl.gz'), gzipSync(brutes.join('\n') + '\n'));

  // --- Agrégation ---
  const par = (br: Bras, champ: 'brut' | 'avecRepli', filtre: (e: Essai) => boolean = () => true) => {
    const o: Record<string, number[]> = {};
    for (const e of essais.filter((x) => x.bras === br && filtre(x))) (o[e.brief] ??= []).push(e[champ]);
    return o;
  };
  const f2 = (x: number) => x.toFixed(3);
  const lignes: string[] = [];
  const ecrire = (s = '') => { lignes.push(s); console.log(s); };
  ecrire(`# Banc de montage ${etiquette}`);
  ecrire(`Modèle ${modele} ; ${briefs.length} briefs × ${reps} répétitions ; ${compteur.etat.appels} appels ; ${compteur.etat.entree + compteur.etat.sortie} jetons ; ${compteur.etat.usd.toFixed(3)} USD (plafond ${plafond})${arret ? ` ; ARRÊT : ${arret}` : ''}`);
  ecrire();
  ecrire('| Bras | score brut [IC95] | score avec repli [IC95] | EDL valide 1er coup | repli | USD/essai | jetons/essai |');
  ecrire('|---|---|---|---|---|---|---|');
  for (const br of bras) {
    const l = essais.filter((e) => e.bras === br);
    if (!l.length) continue;
    const [m, lo, hi] = icMoyenne(par(br, 'brut')), [m2, lo2, hi2] = icMoyenne(par(br, 'avecRepli'));
    ecrire(`| ${NOMS[br]} | ${f2(m)} [${f2(lo)} ; ${f2(hi)}] | ${f2(m2)} [${f2(lo2)} ; ${f2(hi2)}] | ${(100 * l.filter((e) => e.premierCoup).length / l.length).toFixed(0)} % | ${(100 * l.filter((e) => e.source === 'repli').length / l.length).toFixed(0)} % | ${f2(moyenne(l.map((e) => e.usd)))} | ${Math.round(moyenne(l.map((e) => e.jetons)))} |`);
  }
  ecrire();
  ecrire('Comparaisons appariées par brief (différence de score, IC95 bootstrap sur les briefs ; « brut » = invalide compte 0) :');
  ecrire('| B − A | brut : Δ [IC95] | avec repli : Δ [IC95] | briefs |');
  ecrire('|---|---|---|---|');
  for (const [a, b] of [['code', 'a0'], ['code', 'a1'], ['a0', 'a1']] as [Bras, Bras][]) {
    if (!bras.includes(a) || !bras.includes(b)) continue;
    const x = compareApparie(par(a, 'brut'), par(b, 'brut')), y = compareApparie(par(a, 'avecRepli'), par(b, 'avecRepli'));
    ecrire(`| ${b} − ${a} | ${x.delta >= 0 ? '+' : ''}${f2(x.delta)} [${f2(x.ic95[0])} ; ${f2(x.ic95[1])}] | ${y.delta >= 0 ? '+' : ''}${f2(y.delta)} [${f2(y.ic95[0])} ; ${f2(y.ic95[1])}] | ${x.n} |`);
  }
  ecrire();
  ecrire('Par partition (score avec repli moyen) :');
  ecrire(`| Partition | ${bras.map((b) => b).join(' | ')} |`);
  ecrire(`|---|${bras.map(() => '---').join('|')}|`);
  for (const p of ['apprentissage', 'validation', 'test']) {
    const cells = bras.map((br) => { const v = Object.values(par(br, 'avecRepli', (e) => e.partition === p)).map(moyenne); return v.length ? f2(moyenne(v)) : '—'; });
    if (cells.some((c) => c !== '—')) ecrire(`| ${p} | ${cells.join(' | ')} |`);
  }
  writeFileSync(join(dossier, 'rapport.md'), lignes.join('\n') + '\n');
  writeFileSync(join(dossier, 'essais.json'), JSON.stringify({ etiquette, modele, reps, plafond, usd: compteur.etat.usd, arret, essais }, null, 1));
  console.error(`résultats : ${dossier}`);
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => { console.error(e instanceof Error ? e.message : String(e)); process.exit(1); });
