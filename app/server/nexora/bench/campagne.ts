/**
 * Campagne « trois paliers », stade A (aucun GPU) : pour chaque palier × brief × condition de mémoire (éteinte / allumée)
 * × tour (1 et 2), le modèle écrit la liste de plans, les prompts et la liste de montage ; le code compile, valide et note.
 * Entre les tours, les plans réussis nourrissent la mémoire (jamais le brief dont ils viennent : anti-fuite).
 *   npx tsx server/nexora/bench/campagne.ts [--etiquette a1] [--plafond-usd 8] [--paliers eco,equilibre,expert] [--briefs id,id] [--tours 2]
 * Les clés sont lues au lancement dans ~/Desktop/Deepinfra.env (jamais affichées ni écrites). Reprise : les essais déjà
 * dans registre.jsonl sont sautés. Dépense plafonnée au total et par palier.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { clientPalier, PALIERS, type Palier } from '../niveaux.js';
import { type BriefFilm, MemoireFilm, briefDeMontage, clipsDuTournage, escalader, runFilm, type RunFilm } from '../montage/film.js';
import { planifierMontage } from '../montage/planifier.js';
import { mesurer } from '../montage/metriques.js';
import { ErreurPlafondLlm, GrandLivreUsage, Releve } from '../usage.js';
import { BRIEFS_FILMS } from './briefsFilms.js';

function arg(nom: string, def: string): string {
  const i = process.argv.indexOf(`--${nom}`);
  return i >= 0 ? process.argv[i + 1] : def;
}

export function chargerCles(): void {
  const t = readFileSync(join(homedir(), 'Desktop/Deepinfra.env'), 'utf8');
  const lire = (n: string) => t.match(new RegExp(`^\\s*${n}\\s*[:=]\\s*(\\S+)`, 'im'))?.[1];
  process.env.NEXORA_LLM_CLE_DEEPINFRA ||= lire('deepinfra');
  process.env.NEXORA_LLM_CLE_OPENROUTER ||= lire('openrouter');
}

export interface Essai {
  cle: string; palier: Palier; brief: string; memoire: 'off' | 'on' | 'v0'; tour: number; score: number; porte: boolean; source: string; tournageValide: boolean; tournagePremierCoup: boolean;
  montagePremierCoup: boolean; appels: number; entree: number; sortie: number; raisonnement: number; usd: number; credits: number; ms: number; metriques: Record<string, number>; ecarts: number;
  nbPlans: number; erreurs: string[]; notes: string[]; tournage: unknown; liste: unknown; plan: unknown; apprise?: boolean;
}

async function main() {
  chargerCles();
  const etiquette = arg('etiquette', 'a1');
  const plafondTotal = Number(arg('plafond-usd', '8'));
  const paliers = arg('paliers', PALIERS.join(',')).split(',') as Palier[];
  const ids = arg('briefs', '').split(',').filter(Boolean);
  const tours = Number(arg('tours', '2'));
  const briefs = BRIEFS_FILMS.filter((b) => !ids.length || ids.includes(b.id));
  const plafondPalier: Record<Palier, number> = { eco: 1.5, equilibre: 1.5, expert: Number(arg('plafond-expert', '5')) };
  const dossier = join(homedir(), 'nexora-creative-data/work/tests-agents', etiquette);
  mkdirSync(dossier, { recursive: true });
  const registre = join(dossier, 'registre.jsonl');
  const livre = new GrandLivreUsage(join(dossier, 'usage.jsonl'));
  const faits = new Map<string, Essai>();
  if (existsSync(registre)) for (const l of readFileSync(registre, 'utf8').split('\n').filter(Boolean)) { const e = JSON.parse(l) as Essai; faits.set(e.cle, e); }
  const depense = () => livre.total().coutUsd;
  const depensePalier = (p: Palier) => livre.total({ palier: p }).coutUsd;
  const graine = new MemoireFilm();
  let memoireTour2: MemoireFilm = graine.copie();

  const essai = async (p: Palier, b: BriefFilm, mem: 'off' | 'on', tour: number, memoire: MemoireFilm) => {
    const cle = `${etiquette}|${p}|${b.id}|${mem}|${tour}`;
    if (faits.has(cle)) return;
    if (depense() >= plafondTotal || depensePalier(p) >= plafondPalier[p]) { console.error(`plafond atteint, ${cle} sauté`); return; }
    const releve = new Releve({ run: cle, tache: 'film', projet: b.id }, 0.6, livre);
    const llm = clientPalier(p, { surveillant: releve, autoriserRepli: false });
    const t0 = Date.now();
    let r: RunFilm | null = null; let err = '';
    try { r = await runFilm(llm, p, b, { memoire: mem === 'on' ? memoire : undefined, reparations: 2 }); } catch (e) { err = e instanceof Error ? e.message : String(e); if (e instanceof ErreurPlafondLlm) err = `plafond du run : ${err}`; }
    const tot = releve.totaux;
    const e: Essai = {
      cle, palier: p, brief: b.id, memoire: mem, tour, score: r?.score ?? 0, porte: r?.porte ?? false, source: r?.montage.source ?? 'echec', tournageValide: r?.tournageValide ?? false,
      tournagePremierCoup: r?.tournagePremierCoup ?? false, montagePremierCoup: r?.montage.premierCoup ?? false, appels: r?.appels ?? 0, entree: tot.entree, sortie: tot.sortie, raisonnement: tot.raisonnement,
      usd: tot.coutUsd, credits: tot.credits, ms: Date.now() - t0, metriques: r?.metriques ?? {}, ecarts: r?.ecarts ?? 0, nbPlans: r?.plan.video.length ?? 0,
      erreurs: [...(r?.montage.erreurs ?? []).map((x) => x.regle), ...(err ? [err] : [])], notes: r?.montage.notes ?? [], tournage: r?.tournage ?? null, liste: r?.montage.liste ?? null, plan: r?.plan ?? null,
    };
    faits.set(cle, e);
    appendFileSync(registre, JSON.stringify(e) + '\n');
    console.error(`${p.padEnd(9)} ${b.id.padEnd(13)} ${mem.padEnd(3)} t${tour}  score ${e.score.toFixed(3)}  ${e.source}${e.montagePremierCoup ? '' : ' (réparé)'}  ${e.usd.toFixed(4)} USD  ${(e.ms / 1000).toFixed(0)} s  total ${depense().toFixed(3)} USD`);
    // Bras v0 (ancien harnais : EditPlan brut, aucune mémoire, aucun validateur interactif) sur la MÊME matière, une fois.
    if (p === 'eco' && mem === 'off' && tour === 1 && r?.tournage) {
      const cleV0 = `${etiquette}|${p}|${b.id}|v0|1`;
      if (!faits.has(cleV0) && depensePalier(p) < plafondPalier[p]) {
        const rel0 = new Releve({ run: cleV0, tache: 'film', projet: b.id }, 0.3, livre);
        const bm = briefDeMontage(b, clipsDuTournage(r.tournage));
        const t1 = Date.now();
        const v0 = await planifierMontage(clientPalier(p, { surveillant: rel0 }), bm, { memoire: false, reparations: 0, tours: 0, maxAppels: 1, temperature: 0.3, maxTokens: 12000 });
        const m0 = mesurer(v0.plan, bm);
        const t0u = rel0.totaux;
        const e0: Essai = { ...e, cle: cleV0, memoire: 'v0', score: v0.source === 'llm' ? m0.composite : 0, porte: m0.porte, source: v0.source, montagePremierCoup: v0.valideDuPremierCoup, appels: v0.appels, entree: t0u.entree, sortie: t0u.sortie, raisonnement: t0u.raisonnement, usd: t0u.coutUsd, credits: t0u.credits, ms: Date.now() - t1, metriques: Object.fromEntries(Object.entries(m0.metriques).map(([k, v]) => [k, v.score])), ecarts: m0.ecarts.length, nbPlans: v0.plan.video.length, erreurs: v0.notes, notes: v0.notes, liste: null, plan: v0.plan };
        faits.set(cleV0, e0); appendFileSync(registre, JSON.stringify(e0) + '\n');
        console.error(`${p.padEnd(9)} ${b.id.padEnd(13)} v0  t1  score ${e0.score.toFixed(3)}  ${e0.source}  ${e0.usd.toFixed(4)} USD`);
      }
    }
  };

  for (let tour = 1; tour <= tours; tour++) {
    // Un travailleur par palier (les paliers tournent en parallèle ; au sein d'un palier, séquentiel).
    await Promise.all(paliers.map(async (p) => {
      for (const b of briefs) for (const mem of ['off', 'on'] as const) await essai(p, b, mem, tour, tour === 1 ? graine : memoireTour2);
    }));
    // Croissance de la mémoire : les meilleurs plans valides du tour entrent (tous paliers), jamais ceux du brief courant.
    if (tour < tours) {
      memoireTour2 = graine.copie();
      let n = 0;
      for (const e of faits.values()) {
        if (e.tour !== tour || e.memoire === 'v0' || e.source !== 'llm' || !e.plan) continue;
        const b = BRIEFS_FILMS.find((x) => x.id === e.brief)!;
        if (memoireTour2.apprendre(b, e.palier, e.plan as any, e.tournage as any, e.score)) n++;
      }
      console.error(`mémoire : +${n} exemplaires appris au tour ${tour} (${memoireTour2.segments.length} segments, ${memoireTour2.tournages.length} tournages)`);
      writeFileSync(join(dossier, `memoire-tour${tour}.json`), JSON.stringify({ segments: memoireTour2.segments.map((s) => s.id), tournages: memoireTour2.tournages.map((t) => t.id) }, null, 1));
    }
  }
  console.error(`terminé : ${faits.size} essais, ${depense().toFixed(3)} USD`);
  void escalader;
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => { console.error(e instanceof Error ? e.message : String(e)); process.exit(1); });
