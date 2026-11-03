/**
 * Banc « mémoire AMD × ReasoningBank × harnais » (recherche/20). Partition SCELLÉE :
 *  - apprentissage : les 4 briefs des trajectoires du professeur (memoire/professeur/*.json) ; l'élève y collecte aussi sa
 *    banque ReasoningBank (D) ; jamais un brief de test ;
 *  - test : les 8 briefs de la campagne (bench/briefsFilms.ts), joués une fois par condition × répétition, rien n'en est appris.
 * Conditions : A sans mémoire · B mémoire existante · C AMD professeur (workflow + sous-tâches + fonction) · D ReasoningBank
 * (stratégies de l'élève, réussites et échecs, juge = l'élève) · E = C + D · F meilleur-de-4 (juge en code) sur B ·
 * G harnais décomposé (structure puis textes) sur B · H = C + G.
 *   npx tsx server/nexora/bench/memoires.ts --phase rb|test|juge|rapport [--paliers eco,equilibre] [--conditions A,B,…] [--reps 3] [--plafond-usd 6]
 * Clés lues au lancement dans ~/Desktop/Deepinfra.env (jamais affichées). Reprise : les essais déjà au registre sont sautés.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { clientPalier, type Palier } from '../niveaux.js';
import { type BriefFilm, MemoireFilm, type OptionsRun, runFilm, type RunFilm } from '../montage/film.js';
import { BanqueStrategies, MemoireProfesseur, chargerTrajectoires, composer, extraireStrategies, jugerTrace } from '../montage/memoires.js';
import { creditsExacts, GrandLivreUsage, Releve } from '../usage.js';
import { lireJson } from '../llm.js';
import { BRIEFS_FILMS } from './briefsFilms.js';
import { chargerCles } from './campagne.js';
import { compareApparie, icMoyenne, moyenne } from './stats.js';

const arg = (n: string, d: string) => { const i = process.argv.indexOf(`--${n}`); return i >= 0 ? process.argv[i + 1] : d; };
const DOSSIER = join(import.meta.dirname, 'resultats/memoire-amd-rb');
mkdirSync(DOSSIER, { recursive: true });
const REGISTRE = join(DOSSIER, 'registre.jsonl');
const JUGE = join(DOSSIER, 'juge.jsonl');
const livre = new GrandLivreUsage(join(DOSSIER, 'usage.jsonl'));
const PLAFOND = Number(arg('plafond-usd', '6'));
const MARQUE = BRIEFS_FILMS[0].marque;
const APPRENTISSAGE: BriefFilm[] = chargerTrajectoires().map((t) => ({ ...t.brief, marque: MARQUE }));
const banque = (p: Palier) => join(DOSSIER, `strategies-${p}.json`);

export interface EssaiMem {
  cle: string; palier: Palier; condition: string; brief: string; rep: number; score: number; source: string; reparePar: string | null;
  tournageValide: boolean; tournagePremierCoup: boolean; montagePremierCoup: boolean; appels: number; entree: number; sortie: number; usd: number; credits: number; ms: number;
  metriques: Record<string, number>; erreurs: string[]; journal: string[]; tournage: unknown; liste: unknown;
}

function options(c: string, p: Palier): OptionsRun {
  const prof = new MemoireProfesseur();
  const rb = () => BanqueStrategies.lire(banque(p));
  switch (c) {
    case 'A': return {};
    case 'B': return { memoire: new MemoireFilm() };
    case 'C': return { module: prof };
    case 'D': return { module: rb() };
    case 'E': return { module: composer(prof, rb()) };
    case 'F': return { memoire: new MemoireFilm(), candidats: 4 };
    case 'G': return { memoire: new MemoireFilm(), decompose: true };
    case 'H': return { module: prof, decompose: true };
    default: throw new Error(`condition inconnue ${c}`);
  }
}

async function pool<T>(taches: (() => Promise<T>)[], n: number): Promise<void> {
  let i = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (i < taches.length) { const t = taches[i++]; await t(); } }));
}

async function essai(p: Palier, c: string, b: BriefFilm, rep: number, faits: Map<string, EssaiMem>, fichier = REGISTRE): Promise<{ e: EssaiMem; r: RunFilm | null } | null> {
  const cle = `${p}|${c}|${b.id}|${rep}`;
  if (faits.has(cle)) return null;
  if (livre.total().coutUsd >= PLAFOND) { console.error(`plafond ${PLAFOND} USD atteint, ${cle} sauté`); return null; }
  const rel = new Releve({ run: cle, tache: 'film', projet: b.id }, c === 'F' ? 1.5 : 0.6, livre);
  const llm = clientPalier(p, { surveillant: rel, autoriserRepli: false });
  const t0 = Date.now();
  let r: RunFilm | null = null, err = '';
  try { r = await runFilm(llm, p, b, { ...options(c, p), reparations: 2 }); } catch (x) { err = x instanceof Error ? x.message : String(x); }
  const tot = rel.totaux;
  const e: EssaiMem = {
    cle, palier: p, condition: c, brief: b.id, rep, score: r?.score ?? 0, source: r?.montage.source ?? 'echec', reparePar: r?.montage.reparePar ?? null,
    tournageValide: r?.tournageValide ?? false, tournagePremierCoup: r?.tournagePremierCoup ?? false, montagePremierCoup: r?.montage.premierCoup ?? false,
    appels: r?.appels ?? 0, entree: tot.entree, sortie: tot.sortie, usd: tot.coutUsd, credits: creditsExacts(tot.coutUsd), ms: Date.now() - t0,
    metriques: r?.metriques ?? {}, erreurs: [...(r?.montage.erreurs ?? []).map((x) => x.regle), ...(err ? [err] : [])], journal: r?.montage.journal ?? [], tournage: r?.tournage ?? null, liste: r?.montage.liste ?? null,
  };
  faits.set(cle, e);
  appendFileSync(fichier, JSON.stringify(e) + '\n');
  console.error(`${p.padEnd(9)} ${c} ${b.id.padEnd(16)} r${rep} ${e.score.toFixed(3)} ${e.source}${e.reparePar ? '(code)' : ''}${e.montagePremierCoup ? ' 1er' : ''} ${e.usd.toFixed(4)} $ ${(e.ms / 1000).toFixed(0)} s | ${livre.total().coutUsd.toFixed(3)} $`);
  return { e, r };
}

const lire = (f: string) => new Map<string, EssaiMem>(existsSync(f) ? readFileSync(f, 'utf8').split('\n').filter(Boolean).map((l) => { const e = JSON.parse(l); return [e.cle, e]; }) : []);

/** Phase D : l'élève joue les briefs d'apprentissage sans mémoire, se juge, distille ses stratégies (succès ET échecs). */
async function phaseRb(paliers: Palier[]) {
  const f = join(DOSSIER, 'apprentissage.jsonl');
  const faits = lire(f);
  const cal: Record<string, { accord: number; n: number }> = {};
  await Promise.all(paliers.map(async (p) => {
    const bq = BanqueStrategies.lire(banque(p));
    for (const rep of [1, 2]) for (const b of APPRENTISSAGE) {
      const x = await essai(p, 'A', b, rep, faits, f);
      if (!x?.r) continue;
      const rel = new Releve({ run: `rb|${x.e.cle}`, tache: 'juge', projet: b.id }, 0.2, livre);
      const llm = clientPalier(p, { surveillant: rel, autoriserRepli: false });
      const trace = { brief: b, palier: p, tournage: x.r.tournage, liste: x.r.montage.liste, journal: x.r.montage.journal ?? [], premierCoup: x.r.montage.premierCoup, source: x.r.montage.source, scoreCode: x.r.score };
      try {
        const v = await jugerTrace(llm, trace);
        const s = await extraireStrategies(llm, trace, v);
        const vrai = x.r.montage.source === 'llm' && !x.r.montage.reparePar && x.r.score >= 0.85;
        cal[p] ??= { accord: 0, n: 0 }; cal[p].n++; if (v.succes === vrai) cal[p].accord++;
        console.error(`  juge ${p} ${b.id} : ${v.succes ? 'succès' : 'échec'} (code : ${vrai ? 'succès' : 'échec'}) → +${bq.ajouter(s)} stratégies`);
      } catch (e) { console.error(`  extraction ${p} ${b.id} en échec : ${e instanceof Error ? e.message : e}`); }
      bq.ecrire(banque(p));
    }
  }));
  writeFileSync(join(DOSSIER, 'etalonnage-juge-rb.json'), JSON.stringify(cal, null, 1));
}

async function phaseTest(paliers: Palier[], conditions: string[], reps: number) {
  const faits = lire(REGISTRE);
  await Promise.all(paliers.map(async (p) => {
    const conds = p === 'expert' ? conditions.filter((c) => ['A', 'B', 'C'].includes(c)) : conditions;
    const taches = [] as (() => Promise<unknown>)[];
    for (let rep = 1; rep <= reps; rep++) for (const b of BRIEFS_FILMS) for (const c of conds) taches.push(() => essai(p, c, b, rep, faits));
    await pool(taches, p === 'expert' ? 3 : 5);
  }));
}

/** Rendu texte d'un film pour le juge : plans tournés + liste de montage (temps, source, texte). */
function film(e: EssaiMem): string {
  const t = e.tournage as { plans: { resume: string }[] } | null;
  const l = e.liste as { plans: { src: string; dur: number; texte?: string }[] } | null;
  if (!l) return '(aucun montage du modèle : repli automatique)';
  let s = 0;
  return l.plans.map((p) => { const k = Number(p.src.slice(1)) - 1; const x = `${s.toFixed(1)}-${(s += p.dur).toFixed(1)} s · ${p.src === 'carton' ? 'carton' : (t?.plans[k]?.resume ?? p.src)}${p.texte ? ` · TEXTE « ${p.texte} »` : ''}`; return x; }).join('\n');
}

/** Juge par paires en ordre inversé (Gemini Argon Flex, indépendant des élèves bon marché) : X contre B, même brief, même répétition. */
async function phaseJuge(paliers: Palier[], conditions: string[]) {
  const faits = lire(REGISTRE);
  const deja = new Set(existsSync(JUGE) ? readFileSync(JUGE, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l).cle) : []);
  const taches = [] as (() => Promise<unknown>)[];
  for (const p of paliers) for (const c of conditions.filter((x) => x !== 'B')) for (const b of BRIEFS_FILMS) for (const rep of [1, 2]) {
    const x = faits.get(`${p}|${c}|${b.id}|${rep}`), ref = faits.get(`${p}|B|${b.id}|${rep}`);
    const cle = `${p}|${c}|${b.id}|${rep}`;
    if (!x || !ref || deja.has(cle)) continue;
    taches.push(async () => {
      if (livre.total().coutUsd >= PLAFOND) return;
      const rel = new Releve({ run: `juge|${cle}`, tache: 'juge', projet: b.id }, 0.2, livre);
      const llm = clientPalier('expert', { surveillant: rel, autoriserRepli: false });
      const un = async (a: EssaiMem, z: EssaiMem) => {
        const txt = await llm.completer('juge', [
          { role: 'system', content: 'Tu es directeur de création. Tu compares deux montages du même brief. Réponds uniquement par du JSON {"gagnant":"1"|"2"|"egal","raison":"…"}.' },
          { role: 'user', content: `BRIEF : ${b.enonce}\n\nMONTAGE 1 :\n${film(a)}\n\nMONTAGE 2 :\n${film(z)}\n\nLequel est le meilleur film publicitaire (accroche, progression, apogée, force et justesse des textes en français du Québec, aucune promesse invérifiable, carton final) ? « egal » si tu ne peux pas trancher.` },
        ], { json: true, temperature: 0, maxTokens: 800 });
        return String(lireJson<{ gagnant?: unknown }>(txt).gagnant ?? 'egal');
      };
      try {
        const [g1, g2] = await Promise.all([un(x, ref), un(ref, x)]);
        const pts = g1 === '1' && g2 === '2' ? 1 : g1 === '2' && g2 === '1' ? 0 : 0.5;
        appendFileSync(JUGE, JSON.stringify({ cle, palier: p, condition: c, brief: b.id, rep, g1, g2, points: pts }) + '\n');
      } catch (e) { console.error(`juge ${cle} : ${e instanceof Error ? e.message : e}`); }
    });
  }
  await pool(taches, 6);
}

function phaseRapport() {
  const faits = [...lire(REGISTRE).values()];
  const juge = existsSync(JUGE) ? readFileSync(JUGE, 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l)) : [];
  const par = (p: string, c: string) => faits.filter((e) => e.palier === p && e.condition === c);
  const parBrief = (l: EssaiMem[]) => { const o: Record<string, number[]> = {}; for (const e of l) (o[e.brief] ??= []).push(e.score); return o; };
  const lignes = ['| Palier | Cond. | n | note [IC95] | Δ vs B [IC95] | tournage 1er coup | montage 1er coup | réparé code | repli | appels | USD / film | crédits / film | USD / film valide | latence méd. | juge vs B (pts) |', '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|'];
  const pct = (x: number) => `${Math.round(x * 100)} %`;
  const resume: Record<string, unknown> = {};
  for (const p of ['eco', 'equilibre', 'expert']) for (const c of ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']) {
    const l = par(p, c);
    if (!l.length) continue;
    const [m, lo, hi] = icMoyenne(parBrief(l));
    const ref = par(p, 'B');
    const d = c !== 'B' && ref.length ? compareApparie(parBrief(ref), parBrief(l)) : null;
    const valides = l.filter((e) => e.source === 'llm').length;
    const usd = l.reduce((s, e) => s + e.usd, 0);
    const ms = l.map((e) => e.ms).sort((a, b) => a - b)[Math.floor(l.length / 2)];
    const j = juge.filter((x) => x.palier === p && x.condition === c);
    const r = { n: l.length, note: m, ic: [lo, hi], delta: d, tPremier: moyenne(l.map((e) => (e.tournagePremierCoup ? 1 : 0))), mPremier: moyenne(l.map((e) => (e.montagePremierCoup ? 1 : 0))), code: moyenne(l.map((e) => (e.reparePar ? 1 : 0))), repli: moyenne(l.map((e) => (e.source !== 'llm' ? 1 : 0))), appels: moyenne(l.map((e) => e.appels)), usd: usd / l.length, credits: creditsExacts(usd / l.length), usdValide: valides ? usd / valides : null, ms, juge: j.length ? moyenne(j.map((x) => x.points)) : null, jn: j.length };
    resume[`${p}|${c}`] = r;
    lignes.push(`| ${p} | ${c} | ${r.n} | ${m.toFixed(3)} [${lo.toFixed(3)} ; ${hi.toFixed(3)}] | ${d ? `${d.delta >= 0 ? '+' : ''}${d.delta.toFixed(3)} [${d.ic95[0].toFixed(3)} ; ${d.ic95[1].toFixed(3)}]` : '—'} | ${pct(r.tPremier)} | ${pct(r.mPremier)} | ${pct(r.code)} | ${pct(r.repli)} | ${r.appels.toFixed(1)} | ${r.usd.toFixed(5)} | ${r.credits.toFixed(3)} | ${r.usdValide?.toFixed(5) ?? '—'} | ${(ms / 1000).toFixed(0)} s | ${r.juge !== null ? `${r.juge.toFixed(2)} (n = ${r.jn})` : '—'} |`);
  }
  const tot = livre.total();
  const md = `# Banc mémoire AMD × ReasoningBank × harnais\n\nDépense totale (registre) : ${tot.coutUsd.toFixed(3)} USD, ${tot.appels} appels.\n\n${lignes.join('\n')}\n`;
  writeFileSync(join(DOSSIER, 'rapport.md'), md);
  writeFileSync(join(DOSSIER, 'resume.json'), JSON.stringify(resume, null, 1));
  console.log(md);
}

async function main() {
  chargerCles();
  const phase = arg('phase', 'test');
  const paliers = arg('paliers', 'eco,equilibre').split(',') as Palier[];
  const conditions = arg('conditions', 'A,B,C,D,E,F,G,H').split(',');
  if (phase === 'rb') await phaseRb(paliers);
  else if (phase === 'test') await phaseTest(paliers, conditions, Number(arg('reps', '3')));
  else if (phase === 'juge') await phaseJuge(paliers, conditions);
  phaseRapport();
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch((e) => { console.error(e instanceof Error ? e.message : String(e)); process.exit(1); });
