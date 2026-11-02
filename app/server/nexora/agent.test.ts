import { describe, expect, it, vi } from 'vitest';
import {
  type DepsAgent, devisProduction, depassement, lirePlanProduction, nouvelleSession, planVersStoryboard, tourProducteur, validerProposition, variante,
} from './agent.js';
import type { ClientLlm, ReponseOutils } from './llm.js';

const planBrut = {
  titre: 'Boulangerie du Coin', format: '9:16', qualite: 'rapide', son: true,
  bible: { style: 'chaud, matinal', personnages: [{ nom: 'Léa', description: 'boulangère, tablier beige' }], lieux: [] },
  plans: [
    { resume: 'Le four s’ouvre', description: 'Close-up of a bread oven opening, steam.', camera: 'push in', duree: 5 },
    { resume: 'Léa sourit', description: 'Léa hands a warm baguette over the counter.', camera: 'static', duree: 5, replique: 'Tout chaud, comme chaque matin !' },
  ],
  musique: { envie: 'acoustique, joyeuse' },
  cartons: [{ texte: 'Boulangerie du Coin', position: 'fin' }],
};

/** Faux LLM qui rejoue une suite de réponses (un appel d'outil ou un texte par tour). */
function fauxLlm(tours: ReponseOutils[]): ClientLlm & { appels: number; vus: any[][] } {
  const f = {
    appels: 0, vus: [] as any[][],
    completer: async () => '{}',
    completerAvecOutils: async (_r: unknown, messages: any[]) => {
      f.vus.push(messages);
      return tours[Math.min(f.appels++, tours.length - 1)];
    },
  };
  return f;
}
const outil = (nom: string, args: Record<string, unknown>, id = 'c1'): ReponseOutils => ({ texte: '', appels: [{ id, nom, arguments: args }], jetons: 100 });
const texte = (t: string): ReponseOutils => ({ texte: t, appels: [], jetons: 50 });

const devisFixe = (credits: number, secondes = 60) => () => ({ credits, creditsEstimes: credits, secondesGpu: secondes, minutes: 1, rendus: 2, plans: 2, musique: true, candidats: 1 as const });
function deps(llm: ClientLlm, extra: Partial<DepsAgent> = {}): DepsAgent {
  return {
    llm, devis: devisFixe(80), plafond: { credits: 500, secondes: 1800 },
    outils: { etat_studio: async () => ({ moteur: 'MiniMax H3', musique: 'MiniMax-Music3' }) },
    ...extra,
  };
}

describe('personnages @ dans le Producteur', () => {
  const persos = { liste: () => 'Personnages disponibles : @Mara (femme rousse, manteau vert).', cite: (t: string) => /@Mara/.test(t) };
  it('donne la liste au modèle et passe en qualité cinéma un plan qui cite un personnage', async () => {
    const brut = { ...planBrut, qualite: 'rapide', plans: [{ ...planBrut.plans[0] }, { resume: '@Mara sourit', description: '@Mara sourit à la caméra.', camera: 'static', duree: 5 }] };
    const llm = fauxLlm([outil('proposer_production', brut), texte('Plan prêt.')]);
    const s = await tourProducteur(nouvelleSession(), 'Un film avec Mara', deps(llm, { personnages: persos }));
    expect(JSON.stringify(llm.vus[0][0])).toContain('@Mara');
    expect(s.proposition).toMatchObject({ genre: 'production', plan: { qualite: 'max' } });
  });
  it('sans personnage cité, la qualité demandée ne change pas', async () => {
    const llm = fauxLlm([outil('proposer_production', planBrut), texte('Plan prêt.')]);
    const s = await tourProducteur(nouvelleSession(), 'Une pub', deps(llm, { personnages: persos }));
    expect(s.proposition).toMatchObject({ plan: { qualite: 'rapide' } });
  });
});

describe('plan de production', () => {
  it('borne et normalise ce que propose le LLM', () => {
    const p = lirePlanProduction({ ...planBrut, format: 'carre?', candidats: 5, plans: [...planBrut.plans, { description: '' }] });
    expect(p.format).toBe('16:9');
    expect(p.candidats).toBe(2);
    expect(p.plans).toHaveLength(2);
    expect(p.plans[1].replique).toBe('Tout chaud, comme chaque matin !');
    expect(p.cartons).toEqual([{ texte: 'Boulangerie du Coin', position: 'fin' }]);
    expect(p.musique).toEqual({ envie: 'acoustique, joyeuse' });
  });
  it('refuse un plan sans plan tourné ou trop long', () => {
    expect(() => lirePlanProduction({ titre: 'x', plans: [] })).toThrow(/au moins un plan/);
    expect(() => lirePlanProduction({ titre: 'x', plans: Array.from({ length: 13 }, () => ({ description: 'a', duree: 10 })) })).toThrow(/12 plans au plus/);
  });
  it('devient un storyboard du Director (la réplique suit le plan)', () => {
    const sb = planVersStoryboard(lirePlanProduction(planBrut));
    expect(sb.plans[1].replique).toBe('Tout chaud, comme chaque matin !');
    expect(sb.dureeTotale).toBe(10);
  });
});

describe('devis', () => {
  const p = lirePlanProduction(planBrut);
  it('additionne les plans ; deux candidats doublent seulement les plans indépendants', () => {
    const un = devisProduction(p, { moteur: 'h3-fast', creditsActifs: true, tarif: { creditsParSecondeGpu: 0.5 } });
    expect(un.rendus).toBe(2);
    expect(un.credits).toBe(30);
    expect(un.musique).toBe(true);
    const deux = devisProduction({ ...p, candidats: 2, plans: [p.plans[0], { ...p.plans[1], suite: true }] }, { moteur: 'h3-fast', creditsActifs: true, tarif: { creditsParSecondeGpu: 0.5 } });
    expect(deux.rendus).toBe(3);
    expect(deux.credits).toBe(45);
  });
  it('sans crédits (poste local) : pas de montant, mais le temps GPU', () => {
    const d = devisProduction(p, { moteur: 'h3-fast', creditsActifs: false, tarif: { creditsParSecondeGpu: 0.5 } });
    expect(d.credits).toBeNull();
    expect(d.secondesGpu).toBe(60);
  });
  it('signale un dépassement du plafond', () => {
    expect(depassement({ credits: 900, creditsEstimes: 900, secondesGpu: 10 } as any, { credits: 500, secondes: 1800 })).toMatch(/900/);
    expect(depassement({ credits: null, secondesGpu: 4000 } as any, { credits: 500, secondes: 1800 })).toMatch(/min/);
    expect(depassement({ credits: 10, creditsEstimes: 10, secondesGpu: 10 } as any, { credits: 500, secondes: 1800 })).toBeNull();
  });
});

describe('boucle du Producteur', () => {
  it('objectif → plan → devis, et rien n’est lancé sans validation', async () => {
    const llm = fauxLlm([outil('etat_studio', {}, 'a'), outil('proposer_production', planBrut, 'b'), texte('Voici le plan : 2 plans verticaux, 80 crédits.')]);
    const s = await tourProducteur(nouvelleSession(), 'Une pub de 10 s pour ma boulangerie, verticale', deps(llm));
    expect(llm.appels).toBe(3);
    expect(s.proposition?.genre).toBe('production');
    expect(s.proposition?.devis.credits).toBe(80);
    const derniere = s.fil.at(-1)!;
    expect(derniere).toMatchObject({ de: 'producteur', texte: 'Voici le plan : 2 plans verticaux, 80 crédits.', proposition: s.proposition!.id });
    expect(s.productions).toHaveLength(0);
    // Le résultat de l'outil renvoyé au modèle contient le devis.
    expect(JSON.stringify(llm.vus[2])).toContain('80');
    // Les consignes système portent les compétences versionnées.
    expect(String(llm.vus[0][0].content)).toContain('[compétence producteur v1]');
  });
  it('un devis au-dessus du plafond est refusé à l’outil, sans proposition', async () => {
    const llm = fauxLlm([outil('proposer_production', planBrut), texte('Trop cher, je raccourcis.')]);
    const s = await tourProducteur(nouvelleSession(), 'pub', deps(llm, { devis: devisFixe(900) }));
    expect(s.proposition).toBeNull();
    expect(JSON.stringify(llm.vus[1])).toMatch(/plafond/);
  });
  it('s’arrête au nombre d’étapes maximal', async () => {
    const llm = fauxLlm([outil('etat_studio', {})]);
    const s = await tourProducteur(nouvelleSession(), 'boucle', deps(llm, { maxEtapes: 4 }));
    expect(llm.appels).toBe(4);
    expect(s.fil.at(-1)!.de).toBe('producteur');
  });
  it('un outil inconnu ou illisible renvoie une erreur au modèle, sans planter', async () => {
    const llm = fauxLlm([{ texte: '', appels: [{ id: 'x', nom: 'lancer_tout', arguments: {} }, { id: 'y', nom: 'proposer_production', arguments: {}, illisible: true }], jetons: 10 }, texte('ok')]);
    const s = await tourProducteur(nouvelleSession(), 'x', deps(llm));
    const retour = JSON.stringify(llm.vus[1]);
    expect(retour).toContain('outil inconnu');
    expect(retour).toContain('arguments illisibles');
    expect(s.fil.at(-1)!.texte).toBe('ok');
  });
  it('une réponse vide est relancée une fois, dans la limite des étapes', async () => {
    const llm = fauxLlm([texte(''), outil('proposer_production', planBrut), texte('Plan prêt.')]);
    const s = await tourProducteur(nouvelleSession(), 'pub', deps(llm));
    expect(llm.appels).toBe(3);
    expect(s.proposition).not.toBeNull();
    expect(JSON.stringify(llm.vus[1])).toContain('Continue');
  });
  it('s’arrête quand le budget de jetons de la session est épuisé', async () => {
    const llm = fauxLlm([outil('etat_studio', {})]);
    const s = nouvelleSession();
    s.jetons = 10_000_000;
    const r = await tourProducteur(s, 'encore', deps(llm));
    expect(llm.appels).toBe(0);
    expect(r.fil.at(-1)!.texte).toMatch(/limite/);
  });
});

describe('validation et variantes', () => {
  it('valider exécute une seule fois la proposition validée', async () => {
    const llm = fauxLlm([outil('proposer_production', planBrut), texte('Plan prêt.')]);
    const s = await tourProducteur(nouvelleSession(), 'pub', deps(llm));
    const executer = vi.fn(async () => ({ filmId: 42 }));
    const id = s.proposition!.id;
    await expect(validerProposition(s, 'autre', { executer, plafond: { credits: 500, secondes: 1800 } })).rejects.toThrow();
    const apres = await validerProposition(s, id, { executer, plafond: { credits: 500, secondes: 1800 } });
    expect(executer).toHaveBeenCalledTimes(1);
    expect(apres.proposition).toBeNull();
    expect(apres.productions[0]).toMatchObject({ filmId: 42 });
    await expect(validerProposition(apres, id, { executer, plafond: { credits: 500, secondes: 1800 } })).rejects.toThrow();
    expect(executer).toHaveBeenCalledTimes(1);
  });
  it('une variante de format reprend le même plan dans un nouveau devis', async () => {
    const s = nouvelleSession();
    s.productions.push({ filmId: 7, plan: lirePlanProduction(planBrut), lanceLe: 'x' });
    const v = variante(s, 7, 'format-16:9', devisFixe(70));
    expect(v.proposition).toMatchObject({ genre: 'production' });
    expect((v.proposition as any).plan.format).toBe('16:9');
    expect((v.proposition as any).plan.plans).toHaveLength(2);
    const court = variante(s, 7, 'courte', devisFixe(0));
    expect(court.proposition).toMatchObject({ genre: 'remontage', film: 7 });
    expect(() => variante(s, 99, 'courte', devisFixe(0))).toThrow();
  });
});

describe('ajustement d’une proposition avant validation', () => {
  it('change candidats, qualité ou format et refait le devis, avec un nouvel identifiant', async () => {
    const { ajusterProposition } = await import('./agent.js');
    const s = nouvelleSession();
    s.proposition = { id: 'p1', genre: 'production', plan: lirePlanProduction(planBrut), devis: devisFixe(10)() };
    const a = ajusterProposition(s, 'p1', { candidats: 2, qualite: 'max', format: '1:1' }, (p) => ({ ...devisFixe(p.candidats === 2 ? 200 : 10)(), candidats: p.candidats }));
    expect(a.proposition).toMatchObject({ genre: 'production', devis: { credits: 200 } });
    expect((a.proposition as any).plan).toMatchObject({ candidats: 2, qualite: 'max', format: '1:1' });
    expect(a.proposition!.id).not.toBe('p1');
    expect(() => ajusterProposition(s, 'autre', {}, devisFixe(1))).toThrow();
  });
});
