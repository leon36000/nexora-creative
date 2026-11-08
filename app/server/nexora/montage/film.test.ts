import { describe, expect, it } from 'vitest';
import type { ClientLlm } from '../llm.js';
import { compilerListe, listeVersPlan, planVersListe, validerListe, aimanter, reparerListe } from './liste.js';
import { BRIEFS_FILMS } from '../bench/briefsFilms.js';
import { MemoireFilm, briefDeMontage, clipsDuTournage, escalader, exclusionPour, validerTournage, type Tournage } from './film.js';
import { ErreurPlafondLlm } from '../usage.js';
import { mesurer } from './metriques.js';

const B = BRIEFS_FILMS.find((b) => b.id === 'creative')!;
const plansTournage = (n: number): Tournage => ({
  titre: 't', style: 's',
  plans: Array.from({ length: n }, (_, i) => ({ resume: `plan ${i}`, prompt: `Wide cinematic shot number ${i} of a glowing studio desk at night with slow camera motion and warm amber light across the wooden surface`, camera: 'push-in', duree: 5 as const })),
});
const bm = () => briefDeMontage(B, clipsDuTournage(plansTournage(9)));
const bonneListe = () => {
  const b = bm();
  const plans = [] as any[];
  let t = 0, i = 0;
  while (t < b.duree_cible_s - 4.4) { const d = 2.2; plans.push({ src: `s${(i % 9) + 1}`, in: (i % 3) * 0.5, dur: d, ...(i === 0 ? { texte: 'Une phrase' } : {}) }); t += d; i++; }
  plans.push({ src: 'carton', in: 0, dur: Math.round((b.duree_cible_s - t) * 100) / 100, tr: 'fondu', texte: B.marque });
  return { plans, gain_db: -8 };
};

describe('liste de montage', () => {
  it('une bonne liste compile en EditPlan valide, durée exacte, coupes sur la grille', () => {
    const r = listeVersPlan(bonneListe(), bm());
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    const m = mesurer(r.plan, bm());
    expect(m.porte).toBe(true);
    expect(m.metriques.battues.score).toBeGreaterThan(0.85);
    expect(r.plan.textes.some((t) => t.texte === B.marque)).toBe(true);
  });
  it('signale source inconnue, dépassement de source, texte imposé absent, durée, avec valeur attendue et réparation', () => {
    const l = bonneListe();
    l.plans[1].src = 'zzz';
    l.plans[2].in = 5;
    l.plans[2].dur = 3;
    l.plans[l.plans.length - 1].texte = 'AUTRE';
    const v = validerListe(l, bm());
    const regles = v.erreurs.map((e) => e.regle);
    expect(regles).toEqual(expect.arrayContaining(['source_connue', 'dans_la_source', 'texte_impose']));
    expect(v.erreurs.find((e) => e.regle === 'dans_la_source')!.indice).toMatch(/in ≤ 2\.1|dur ≤ 0\.1/);
    expect(v.erreurs.find((e) => e.regle === 'texte_impose')!.indice).toContain(B.marque);
  });
  it('un texte peut déborder sur les plans suivants jusqu’au prochain texte', () => {
    const l = bonneListe();
    l.plans[0].texte = 'Une phrase de trente et un car.'; // 31 caractères sur un plan de 2,2 s : trop long seul
    expect(validerListe(l, bm()).erreurs.some((e) => e.regle === 'texte_trop_long')).toBe(false);
    l.plans[1].texte = 'Autre';
    expect(validerListe(l, bm()).erreurs.some((e) => e.regle === 'texte_trop_long')).toBe(true);
  });
  it('refuse deux fois la même source de suite et un schéma illisible', () => {
    const l = bonneListe();
    l.plans[1].src = l.plans[0].src;
    expect(validerListe(l, bm()).erreurs.map((e) => e.regle)).toContain('meme_source');
    expect(validerListe({ plans: 'x' }, bm()).erreurs[0].regle).toBe('schema');
  });
  it('aimante sans créer de plan de moins de 0,5 s', () => {
    const o = aimanter([0, 1.0, 1.2, 4], [0.9, 1.1, 2, 3.9]);
    for (let i = 1; i < o.length; i++) expect(o[i] - o[i - 1]).toBeGreaterThanOrEqual(0.5 - 1e-9);
    expect(o[0]).toBe(0);
    expect(o[o.length - 1]).toBe(4);
  });
  it('aller-retour EditPlan → liste → EditPlan garde les plans', () => {
    const r = listeVersPlan(bonneListe(), bm());
    if (!r.ok) throw new Error('invalide');
    const liste = planVersListe(r.plan);
    expect(liste.plans).toHaveLength(r.plan.video.length);
    expect(compilerListe(liste, bm()).video).toHaveLength(r.plan.video.length);
  });
});

describe('réparations du code', () => {
  it('borne la lecture, retire un texte qui ne tient pas, sépare deux plans de même source, et la liste devient valide', () => {
    const l = bonneListe();
    l.plans[2].in = 5;
    l.plans[3].src = l.plans[2].src;
    l.plans[4].texte = 'Un texte beaucoup trop long pour le temps disponible ici';
    expect(validerListe(l, bm()).ok).toBe(false);
    const r = reparerListe(l, bm())!;
    expect(r.faits.length).toBeGreaterThanOrEqual(2);
    const v = listeVersPlan(r.liste, bm());
    expect(v.ok ? [] : v.erreurs.map((e) => `${e.regle} ${e.message}`)).toEqual([]);
  });
  it('ne touche pas aux textes imposés et ne renvoie rien si rien à réparer', () => {
    expect(reparerListe(bonneListe(), bm())).toBeNull();
  });
});

describe('tournage', () => {
  it('valide une liste correcte', () => {
    expect(validerTournage(plansTournage(9), B).ok).toBe(true);
  });
  it('refuse trop peu de plans, texte/logo/marque dans le prompt et prompt français, avec la valeur attendue', () => {
    const t: any = plansTournage(5);
    t.plans[0].prompt = 'A logo of Netflix appears over a wide cinematic city street at night with slow camera motion and warm amber light across wet asphalt';
    t.plans[1].prompt = 'Un gros plan sur une main qui écrit une phrase dans le bureau avec une lumière chaude et un mouvement lent de la caméra vers le haut';
    const r = validerTournage(t, B);
    expect(r.ok).toBe(false);
    if (r.ok) return;
    const regles = r.erreurs.map((e) => e.regle);
    expect(regles).toEqual(expect.arrayContaining(['nombre_de_plans', 'interdit_dans_le_prompt', 'prompt_en_anglais']));
    expect(r.erreurs.find((e) => e.regle === 'nombre_de_plans')!.indice).toMatch(/au moins 7/);
  });
  it('accepte « no text » mais refuse « text »', () => {
    const t: any = plansTournage(9);
    t.plans[0].prompt += ' with no text anywhere';
    expect(validerTournage(t, B).ok).toBe(true);
    t.plans[0].prompt += ' and a big text on the wall';
    expect(validerTournage(t, B).ok).toBe(false);
  });
});

describe('mémoire', () => {
  it('exclut les graines du film d’origine et les exemplaires appris sur le même brief', () => {
    const ex = exclusionPour(BRIEFS_FILMS.find((b) => b.id === 'surveillance')!);
    expect(ex('seg-claude-surveillance-long')).toBe(true);
    expect(ex('seg-claude-opsys-30')).toBe(false);
    expect(ex('seg-appris-surveillance-eco')).toBe(true);
    expect(ex('seg-appris-creative-eco')).toBe(false);
  });
  it('apprend un plan réussi une seule fois et garde le meilleur ; ignore sous le seuil', () => {
    const m = new MemoireFilm();
    const r = listeVersPlan(bonneListe(), bm());
    if (!r.ok) throw new Error('invalide');
    const n0 = m.segments.length;
    expect(m.apprendre(B, 'eco', r.plan, null, 0.7)).toBe(false);
    expect(m.apprendre(B, 'eco', r.plan, null, 0.9)).toBe(true);
    expect(m.apprendre(B, 'eco', r.plan, null, 0.88)).toBe(false);
    expect(m.apprendre(B, 'eco', r.plan, null, 0.95)).toBe(true);
    expect(m.segments.length).toBe(n0 + 1);
    // L'exemplaire appris sur CE brief n'est jamais rendu pour lui-même.
    expect(m.montage(bm(), exclusionPour(B)).segment?.id).not.toBe('seg-appris-creative-eco');
  });
  it('les graines du professeur sont des EditPlan valides', async () => {
    const { exemplairesInvalides } = await import('./memoire.js');
    expect(exemplairesInvalides()).toEqual([]);
  });
});

describe('escalade', () => {
  const llmQui = (reponses: (() => string)[], plafondApres?: number): ClientLlm => {
    let i = 0;
    return { async completer() { if (plafondApres !== undefined && i >= plafondApres) throw new ErreurPlafondLlm('plafond'); return reponses[Math.min(i++, reponses.length - 1)](); } };
  };
  const tournageOk = () => JSON.stringify(plansTournage(9));
  const mauvais = () => '{"plans":[{"src":"inconnu","dur":1}]}';
  const bon = () => JSON.stringify(bonneListe());
  const clients = (p: Record<string, ClientLlm>) => p as any;

  it('passe au palier suivant quand le moins cher échoue, et s’arrête dès qu’un palier réussit', async () => {
    const r = await escalader(clients({
      eco: llmQui([tournageOk, mauvais]), equilibre: llmQui([tournageOk, bon]), expert: llmQui([tournageOk, bon]),
    }), 'eco', B, { reparations: 0, seuil: 0.5 });
    expect(r.runs.map((x) => x.palier)).toEqual(['eco', 'equilibre']);
    expect(r.palierFinal).toBe('equilibre');
    expect(r.final.score).toBeGreaterThan(0.5);
    expect(r.escalades).toBe(1);
  });
  it('ne monte pas si le premier palier réussit', async () => {
    const r = await escalader(clients({ eco: llmQui([tournageOk, bon]), equilibre: llmQui([bon]), expert: llmQui([bon]) }), 'eco', B, { reparations: 0, seuil: 0.5 });
    expect(r.runs).toHaveLength(1);
  });
  it('le plafond de dépense arrête l’escalade et rend le meilleur essai', async () => {
    const r = await escalader(clients({ eco: llmQui([tournageOk, mauvais]), equilibre: llmQui([tournageOk], 0), expert: llmQui([bon]) }), 'eco', B, { reparations: 0 });
    expect(r.runs.map((x) => x.palier)).toEqual(['eco']);
    expect(r.final.montage.source).toBe('repli');
  });
  it('propage le plafond au premier appel sans essayer un palier supérieur', async () => {
    const appels: Record<string, number> = { eco: 0, equilibre: 0, expert: 0 };
    const plafond = new ErreurPlafondLlm('plafond');
    const client = (p: keyof typeof appels): ClientLlm => ({ async completer() { appels[p]++; throw plafond; } });
    await expect(escalader(clients({ eco: client('eco'), equilibre: client('equilibre'), expert: client('expert') }), 'eco', B, { reparations: 0 }))
      .rejects.toBe(plafond);
    expect(appels).toEqual({ eco: 1, equilibre: 0, expert: 0 });
  });
  it('refuse un ordre vide avant tout appel', async () => {
    const appels: Record<string, number> = { eco: 0, equilibre: 0, expert: 0 };
    const client = (p: keyof typeof appels): ClientLlm => ({ async completer() { appels[p]++; return tournageOk(); } });
    const cs = clients({ eco: client('eco'), equilibre: client('equilibre'), expert: client('expert') });
    await expect(escalader(cs, 'eco', B, { ordre: [], reparations: 0 })).rejects.toBeInstanceOf(RangeError);
    expect(appels).toEqual({ eco: 0, equilibre: 0, expert: 0 });
  });
  it('refuse un ordre sans le palier de départ avant tout appel', async () => {
    const appels: Record<string, number> = { eco: 0, equilibre: 0, expert: 0 };
    const client = (p: keyof typeof appels): ClientLlm => ({ async completer() { appels[p]++; return tournageOk(); } });
    const cs = clients({ eco: client('eco'), equilibre: client('equilibre'), expert: client('expert') });
    await expect(escalader(cs, 'eco', B, { ordre: ['equilibre'], reparations: 0 })).rejects.toBeInstanceOf(RangeError);
    expect(appels).toEqual({ eco: 0, equilibre: 0, expert: 0 });
  });
  it('répare avec les violations et réussit au second appel', async () => {
    let n = 0;
    const llm: ClientLlm = { async completer(_r, m) { n++; if (n === 1) return tournageOk(); if (n === 2) return mauvais(); expect(m[m.length - 1].content).toMatch(/schema/); return bon(); } };
    const r = await escalader(clients({ eco: llm, equilibre: llm, expert: llm }), 'eco', B, { reparations: 1, seuil: 0.5 });
    expect(r.final.montage.source).toBe('llm');
    expect(r.final.montage.premierCoup).toBe(false);
    expect(r.runs).toHaveLength(1);
  });
});
