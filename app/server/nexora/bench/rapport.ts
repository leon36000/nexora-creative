/**
 * Rapport de la campagne (stade A) : tableaux par palier, effet de la mémoire, évolution par tour, ancien harnais (v0).
 *   npx tsx server/nexora/bench/rapport.ts a1
 */
import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { PALIERS } from '../niveaux.js';
import type { Essai } from './campagne.js';
import { compareApparie, icMoyenne, moyenne } from './stats.js';

const etiquette = process.argv[2] ?? 'a1';
const essais: Essai[] = readFileSync(join(homedir(), 'nexora-creative-data/work/tests-agents', etiquette, 'registre.jsonl'), 'utf8').split('\n').filter(Boolean).map((l) => JSON.parse(l));
const f = (x: number, n = 3) => x.toFixed(n);
const par = (l: Essai[], champ: (e: Essai) => number) => { const o: Record<string, number[]> = {}; for (const e of l) (o[e.brief] ??= []).push(champ(e)); return o; };
const ic = (l: Essai[], champ: (e: Essai) => number) => { const [m, lo, hi] = icMoyenne(par(l, champ)); return `${f(m)} [${f(lo)} ; ${f(hi)}]`; };
const pct = (l: Essai[], p: (e: Essai) => boolean) => `${Math.round((100 * l.filter(p).length) / Math.max(1, l.length))} %`;
const sel = (o: Partial<Pick<Essai, 'palier' | 'memoire' | 'tour'>>) => essais.filter((e) => (!o.palier || e.palier === o.palier) && (!o.memoire || e.memoire === o.memoire) && (!o.tour || e.tour === o.tour));
const delta = (a: Essai[], b: Essai[]) => { const d = compareApparie(par(a, (e) => e.score), par(b, (e) => e.score)); return `${d.delta >= 0 ? '+' : ''}${f(d.delta)} [${f(d.ic95[0])} ; ${f(d.ic95[1])}] (n=${d.n})`; };

const L = (s = '') => console.log(s);
const total = essais.reduce((s, e) => s + e.usd, 0);
L(`# Campagne ${etiquette} : ${essais.length} essais, ${f(total, 3)} USD fournisseur`);
L('\n## 1. Par palier (tous tours, hors v0) : score avec les IC95 bootstrap sur les briefs\n');
L('| Palier | essais | score brut [IC95] | tournage valide 1er coup | montage valide 1er coup | repli | USD / film | crédits / film | jetons (lus/écrits) | latence |');
L('|---|---|---|---|---|---|---|---|---|---|');
for (const p of PALIERS) {
  const l = sel({ palier: p }).filter((e) => e.memoire !== 'v0');
  if (!l.length) continue;
  L(`| ${p} | ${l.length} | ${ic(l, (e) => e.score)} | ${pct(l, (e) => e.tournagePremierCoup)} | ${pct(l, (e) => e.montagePremierCoup && e.source === 'llm')} | ${pct(l, (e) => e.source !== 'llm')} | ${f(moyenne(l.map((e) => e.usd)), 4)} | ${f(moyenne(l.map((e) => e.credits)), 2)} | ${Math.round(moyenne(l.map((e) => e.entree)))} / ${Math.round(moyenne(l.map((e) => e.sortie)))} | ${Math.round(moyenne(l.map((e) => e.ms)) / 1000)} s |`);
}
L('\n## 2. Effet de la mémoire (allumée − éteinte, apparié par brief, tours 1 à 3)\n');
L('| Palier | éteinte | allumée | Δ [IC95] |\n|---|---|---|---|');
for (const p of PALIERS) { const a = sel({ palier: p, memoire: 'off' }), b = sel({ palier: p, memoire: 'on' }); if (a.length && b.length) L(`| ${p} | ${ic(a, (e) => e.score)} | ${ic(b, (e) => e.score)} | ${delta(a, b)} |`); }
L('\n## 3. Évolution par tour (la mémoire grossit entre les tours)\n');
L('| Palier | Mémoire | tour 1 | tour 2 | tour 3 | Δ tour 3 − tour 1 [IC95] | USD/film t1 → t3 |\n|---|---|---|---|---|---|---|');
for (const p of PALIERS) for (const m of ['off', 'on'] as const) {
  const t = [1, 2, 3].map((k) => sel({ palier: p, memoire: m, tour: k }));
  if (!t[0].length || !t[2].length) continue;
  L(`| ${p} | ${m === 'on' ? 'allumée' : 'éteinte'} | ${t.map((x) => (x.length ? f(moyenne(Object.values(par(x, (e) => e.score)).map(moyenne))) : '—')).join(' | ')} | ${delta(t[0], t[2])} | ${f(moyenne(t[0].map((e) => e.usd)), 4)} → ${f(moyenne(t[2].map((e) => e.usd)), 4)} |`);
}
L('\n## 4. Ancien harnais (EditPlan brut, un appel, sans mémoire) contre la liste compacte (palier Éco, tour 1, mémoire éteinte, même matière)\n');
const v0 = sel({ palier: 'eco', memoire: 'v0' }), nv = sel({ palier: 'eco', memoire: 'off', tour: 1 });
if (v0.length) L(`| Harnais | valide 1er coup | repli | score brut | USD/film |\n|---|---|---|---|---|\n| v0 (EditPlan brut) | ${pct(v0, (e) => e.montagePremierCoup && e.source === 'llm')} | ${pct(v0, (e) => e.source !== 'llm')} | ${ic(v0, (e) => e.score)} | ${f(moyenne(v0.map((e) => e.usd)), 4)} |\n| liste compacte + validateur + 2 réparations | ${pct(nv, (e) => e.montagePremierCoup && e.source === 'llm')} | ${pct(nv, (e) => e.source !== 'llm')} | ${ic(nv, (e) => e.score)} | ${f(moyenne(nv.map((e) => e.usd)), 4)} |\n\nΔ liste − v0 : ${delta(v0, nv)}`);
L('\n## 5. Par brief (score moyen, tours et mémoires confondus)\n');
const briefs = [...new Set(essais.map((e) => e.brief))];
L(`| Brief | ${PALIERS.join(' | ')} |\n|---|${PALIERS.map(() => '---').join('|')}|`);
for (const b of briefs) L(`| ${b} | ${PALIERS.map((p) => { const l = essais.filter((e) => e.brief === b && e.palier === p && e.memoire !== 'v0'); return l.length ? f(moyenne(l.map((e) => e.score)), 2) : '—'; }).join(' | ')} |`);
L('\n## 6. Métriques du composite (moyennes, hors v0)\n');
L(`| Palier | rythme | battues | doublons | texte | audio |\n|---|---|---|---|---|---|`);
for (const p of PALIERS) { const l = sel({ palier: p }).filter((e) => e.memoire !== 'v0' && e.source === 'llm'); if (l.length) L(`| ${p} | ${['rythme', 'battues', 'doublons', 'texte', 'audio'].map((k) => f(moyenne(l.map((e) => e.metriques[k] ?? 0)), 2)).join(' | ')} |`); }
const rep = essais.filter((e) => e.memoire !== 'v0' && e.source !== 'llm');
const causes: Record<string, number> = {};
for (const e of rep) for (const c of new Set(e.erreurs)) causes[c] = (causes[c] ?? 0) + 1;
L(`\nCauses des replis (${rep.length}) : ${Object.entries(causes).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ×${v}`).join(', ') || '—'}`);
