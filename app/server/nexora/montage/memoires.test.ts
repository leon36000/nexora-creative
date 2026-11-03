import { describe, expect, it } from 'vitest';
import type { ClientLlm } from '../llm.js';
import { BRIEFS_FILMS } from '../bench/briefsFilms.js';
import { type BriefFilm, briefDeMontage, clipsDuTournage, monterListe, runFilm, structureVersListe, validerTournage, type Tournage } from './film.js';
import { listeVersPlan, validerListe } from './liste.js';
import { BanqueStrategies, MemoireProfesseur, chargerTrajectoires, composer, extraireStrategies, jugerTrace, listeDuProfesseur, sousTache, type Strategie } from './memoires.js';
import { mesurer } from './metriques.js';

const MARQUE = BRIEFS_FILMS[0].marque;
const versFilm = (t: ReturnType<typeof chargerTrajectoires>[number]): BriefFilm => ({ ...t.brief, marque: MARQUE });
const llmQui = (reponses: string[]): ClientLlm & { vus: string[][] } => {
  const vus: string[][] = [];
  let i = 0;
  return { vus, completer: async (_r, m) => { vus.push(m.map((x) => String((x as any).content))); return reponses[Math.min(i++, reponses.length - 1)]; } };
};

describe('mémoire du professeur (AMD)', () => {
  const trajs = chargerTrajectoires();
  it('quatre trajectoires d\'apprentissage, aucune sur un brief du banc de test (scellé)', () => {
    expect(trajs.length).toBeGreaterThanOrEqual(4);
    const test = new Set(BRIEFS_FILMS.map((b) => b.id));
    for (const t of trajs) { expect(t.partition).toBe('apprentissage'); expect(test.has(t.brief.id)).toBe(false); }
  });
  it('chaque trajectoire est une RÉUSSITE : tournage valide, liste valide, note en code ≥ 0,9', () => {
    for (const t of trajs) {
      const b = versFilm(t);
      expect(validerTournage(t.tournage, b).ok, t.id).toBe(true);
      const bm = briefDeMontage(b, clipsDuTournage(t.tournage));
      const v = validerListe(listeDuProfesseur(t, MARQUE), bm);
      expect(v.erreurs, t.id).toEqual([]);
      const r = listeVersPlan(listeDuProfesseur(t, MARQUE), bm);
      expect(r.ok).toBe(true);
      if (r.ok) expect(mesurer(r.plan, bm).composite, t.id).toBeGreaterThanOrEqual(0.9);
    }
  });
  it('sous-tâches anonymisées : jetons <SRC_x>, aucune source réelle, durée de source annotée', () => {
    const s = sousTache(trajs[0], 'apogee')!;
    expect(s).toMatch(/<SRC_A>/);
    expect(s).not.toMatch(/"src":"s\d+"/);
    expect(s).toMatch(/source de 5,1 s/);
  });
  it('proactif : workflow + une sous-tâche par phase, du même genre, marque instanciée ; réactif : indice seulement sur erreur', () => {
    const m = new MemoireProfesseur();
    const b = BRIEFS_FILMS.find((x) => x.id === 'opsys')!;
    const bloc = m.avant('montage', b);
    expect(bloc).toMatch(/Bande-annonce/);
    for (const ph of ['Accroche', 'Montée', 'Respiration', 'Apogée', 'Résolution', 'Carton']) expect(bloc).toContain(ph);
    expect(bloc).toContain(MARQUE);
    expect(bloc).not.toContain('<MARQUE>');
    expect(m.avant('tournage', b)).toBe('');
    expect(m.surErreur('montage', [])).toEqual([]);
    const ind = m.surErreur('montage', [{ regle: 'texte_trop_long', chemin: 'plans.2.texte', message: 'x' }]);
    expect(ind.join(' ')).toMatch(/16/);
    expect(m.tournage(b)?.genre).toEqual(['bande-annonce']);
  });
  it('l\'indice du professeur est joint au refus du validateur', async () => {
    const b = BRIEFS_FILMS.find((x) => x.id === 'creative')!;
    const t = chargerTrajectoires().find((x) => x.brief.genre === 'pub')!;
    const bm = briefDeMontage(b, clipsDuTournage(t.tournage));
    const mauvaise = JSON.stringify({ plans: [{ src: 's1', in: 0, dur: 2, texte: 'Un texte beaucoup trop long pour deux secondes de plan' }, { src: 'carton', dur: 28, texte: b.marque }] });
    const llm = llmQui([mauvaise, mauvaise]);
    await monterListe(llm, bm, { module: new MemoireProfesseur(), brief: b, reparations: 1 });
    expect(llm.vus[1].at(-1)).toMatch(/Rappels du professeur/);
  });
});

describe('banque de stratégies (ReasoningBank)', () => {
  const strat = (titre: string, genre: string, verdict: 'succes' | 'echec' = 'succes'): Strategie => ({ id: titre, titre, description: 'd', contenu: 'c', etape: 'montage', source: { brief: 'app-x', genre, mots: ['usine'], palier: 'eco', verdict } });
  it('ajout dédoublonné par titre, plafonné, top-1 du même genre', () => {
    const b = new BanqueStrategies([], { plafond: 3 });
    expect(b.ajouter([strat('A', 'pub'), strat('a', 'pub'), strat('B', 'bande-annonce')])).toBe(2);
    b.ajouter([strat('C', 'pub'), strat('D', 'pub')]);
    expect(b.items.length).toBe(3);
    const r = b.recuperer({ genre: 'bande-annonce', enonce: 'usine', mots: [] }, 'montage');
    expect(r.length).toBe(1);
    expect(r[0].titre).toBe('B');
    expect(b.systeme('montage', BRIEFS_FILMS[0])).toMatch(/expériences passées/);
    expect(b.systeme('tournage', BRIEFS_FILMS[0])).toBe('');
  });
  it('juge sans vérité terrain puis extraction : ≤ 3 stratégies, provenance et verdict notés', async () => {
    const llm = llmQui(['{"succes":false,"raison":"textes trop longs"}', JSON.stringify({ strategies: [1, 2, 3, 4].map((k) => ({ titre: `T${k}`, description: 'd', contenu: 'c', etape: 'montage' })) })]);
    const trace = { brief: BRIEFS_FILMS[0], palier: 'eco', tournage: null, liste: null, journal: ['texte_trop_long'], premierCoup: false, source: 'repli' as const, scoreCode: 0 };
    const v = await jugerTrace(llm, trace);
    expect(v.succes).toBe(false);
    const s = await extraireStrategies(llm, trace, v);
    expect(s.length).toBe(3);
    expect(s[0].source.verdict).toBe('echec');
    expect(llm.vus[1].join(' ')).toMatch(/ÉCHEC/);
  });
  it('composition C + D : les deux blocs et les indices réunis', () => {
    const d = new BanqueStrategies([strat('Respire avant l\'apogée', 'bande-annonce')]);
    const e = composer(new MemoireProfesseur(), d)!;
    const b = BRIEFS_FILMS.find((x) => x.id === 'opsys')!;
    expect(e.avant!('montage', b)).toMatch(/professeur/);
    expect(e.systeme!('montage', b)).toMatch(/Respire/);
  });
});

describe('harnais : meilleur-de-n et décomposé', () => {
  const b = BRIEFS_FILMS.find((x) => x.id === 'creative')!;
  const t: Tournage = chargerTrajectoires().find((x) => x.brief.genre === 'pub')!.tournage;
  const bm = briefDeMontage(b, clipsDuTournage(t));
  it('structure → liste : le code choisit des passages dans la source et pose le carton imposé', () => {
    const l = structureVersListe({ plans: [{ src: 's1', dur: 2 }, { src: 's2', dur: 3 }, { src: 's1', dur: 2.5 }, { src: 's1', dur: 4 }] }, bm);
    expect(l.plans[2].in).toBe(2);
    expect(l.plans[3].in + l.plans[3].dur).toBeLessThanOrEqual(5.1);
    expect(l.plans.at(-1)).toMatchObject({ src: 'carton', texte: b.marque });
  });
  it('décomposé : structure puis textes, plan valide du modèle', async () => {
    const st = { plans: [1.8, 2.4, 2.4, 2.2, 2.4, 3.0, 1.4, 1.4, 1.4, 2.6, 2.2, 2.0].map((dur, i) => ({ src: `s${(i % 9) + 1}`, dur })).concat([{ src: 'carton', dur: 4 }] as any) };
    const llm = llmQui([JSON.stringify(st), JSON.stringify({ textes: [{ i: 0, texte: 'Une phrase.' }, { i: 2, texte: 'Une pub.' }] })]);
    const r = await monterListe(llm, bm, { decompose: true, brief: b });
    expect(r.source).toBe('llm');
    expect(r.premierCoup).toBe(true);
    expect(r.appels).toBe(2);
    expect(r.plan.textes.some((x) => x.texte === 'Une phrase.')).toBe(true);
    expect(llm.vus[1].at(-1)).toMatch(/caractères au plus/);
  });
  it('meilleur-de-n : n chaînes, la liste valide l\'emporte sur l\'invalide', async () => {
    const bonne = listeDuProfesseur(chargerTrajectoires().find((x) => x.brief.genre === 'pub' && x.brief.duree_cible_s === 30)!, b.marque);
    let k = 0;
    const llm: ClientLlm = { completer: async () => (k++ % 2 ? JSON.stringify(bonne) : '{"plans":[]}') };
    const r = await monterListe(llm, bm, { candidats: 4, reparations: 0 });
    expect(r.source).toBe('llm');
    expect(r.notes.join(' ')).toMatch(/meilleur de 4/);
  });
  it('runFilm transmet le module au tournage (exemplaire du professeur) et au montage', async () => {
    const llm = llmQui([JSON.stringify(t), '{"plans":[]}']);
    await runFilm(llm, 'eco', b, { module: new MemoireProfesseur(), reparations: 0 });
    expect(llm.vus[0].at(-1)).toMatch(/exemplaire d'un autre film/);
    expect(llm.vus[1].at(-1)).toMatch(/savoir-faire du professeur/);
  });
});

describe('politique par palier (défaut mesuré, recherche/20)', () => {
  it('Éco et Équilibré : professeur + décomposé ; Expert : mémoire existante ; NEXORA_HARNAIS_FILM=v3 rend l\'ancien', async () => {
    const { optionsPalier, MemoireFilm } = await import('./film.js');
    for (const p of ['eco', 'equilibre'] as const) { const o = optionsPalier(p, {}); expect(o.decompose).toBe(true); expect(o.module).toBeInstanceOf(MemoireProfesseur); }
    expect(optionsPalier('expert', {}).memoire).toBeInstanceOf(MemoireFilm);
    expect(optionsPalier('eco', { NEXORA_HARNAIS_FILM: 'v3' }).decompose).toBeUndefined();
  });
});
