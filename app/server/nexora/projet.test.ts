import { describe, expect, it } from 'vitest';
import { aplatir, estimerProjet, intentionDuPlanProjet, ordreAssemblage, prochainLot, type ProjetLong, scenarioVersArbre } from './projet.js';

const SCENARIO = `SÉQUENCE 1 : Le retour

INT. CAFÉ DU PORT - NUIT
Mara entre dans le café désert, la pluie ruisselle sur son manteau vert.

Elle s'assoit au comptoir et pose une vieille clé sur le zinc.

EXT. QUAI - AUBE
Le brouillard se lève sur les bateaux. Mara marche seule le long de l'eau.

SÉQUENCE 2 : La clé

INT. ATELIER - JOUR
Un serrurier examine la clé sous une loupe.`;

const projet = (sequences = scenarioVersArbre(SCENARIO)): ProjetLong => ({
  id: 'x', titre: 'Le retour', format: '16:9', qualite: 'max', scenario: SCENARIO, cree: '2026-11-02',
  bible: { style: 'cinéma naturaliste, grain fin', notes: '', personnages: [{ nom: 'Mara', description: 'femme de trente ans, cheveux roux courts, manteau vert' }], lieux: [{ nom: 'Café du port', description: 'petit bar de marins, zinc, néon rouge' }] },
  sequences,
});

describe('projet long : scénario → arbre', () => {
  it('découpe séquences, scènes et plans', () => {
    const s = scenarioVersArbre(SCENARIO);
    expect(s.map((x) => x.titre)).toEqual(['Le retour', 'La clé']);
    expect(s[0].scenes.map((x) => x.lieu)).toEqual(['CAFÉ DU PORT - NUIT', 'QUAI - AUBE']);
    expect(aplatir(projet(s)).map((x) => x.plan.id)).toEqual(['p1', 'p2', 'p3', 'p4']);
  });
  it('la bible est injectée : style, lieu et personnage cité', () => {
    const p = projet();
    const i = intentionDuPlanProjet(p, aplatir(p)[0]);
    expect(i).toContain('Style : cinéma naturaliste');
    expect(i).toContain('Lieu (Café du port)');
    expect(i).toContain('Personnage Mara : femme de trente ans');
    expect(intentionDuPlanProjet(p, aplatir(p)[3])).not.toContain('Personnage Mara');
    // « Elle s'assoit… » ne nomme personne : Mara reste dans le plan par continuité de scène.
    expect(aplatir(p)[1].plan.description).not.toContain('Mara');
    expect(intentionDuPlanProjet(p, aplatir(p)[1])).toContain('Personnage Mara');
  });
});

describe('projet long : échelle, coût, lots, assemblage', () => {
  const tarif = { creditsParSecondeGpu: 0.5 };
  it('un film de 90 minutes est simplement 1 080 plans de 5 s, estimé et découpé en lots sans limite codée', () => {
    const plans = Array.from({ length: 1080 }, (_, i) => ({ id: `p${i}`, resume: `plan ${i}`, description: `plan ${i}`, duree: 5 as const, camera: '', etat: 'a_tourner' as const }));
    const scenes = Array.from({ length: 108 }, (_, i) => ({ id: `c${i}`, titre: `Scène ${i}`, plans: plans.slice(i * 10, i * 10 + 10) }));
    const p = projet(Array.from({ length: 9 }, (_, i) => ({ id: `s${i}`, titre: `Séquence ${i + 1}`, scenes: scenes.slice(i * 12, i * 12 + 12) })));
    const t0 = Date.now();
    const e = estimerProjet(p, tarif);
    expect(Date.now() - t0).toBeLessThan(500);
    expect(e).toMatchObject({ plans: 1080, scenes: 108, sequences: 9, dureeS: 5400, restants: 1080, tournes: 0 });
    expect(e.credits).toBe(1080 * 65);
    expect(e.heuresGpu).toBeGreaterThan(30);
    expect(prochainLot(p, 8)).toHaveLength(8);
    expect(prochainLot(p, 8)[0].plan.id).toBe('p0');
  });
  it('le coût ne compte que les plans restants ; l’assemblage suit l’ordre du film', () => {
    const p = projet();
    const plans = aplatir(p);
    plans[0].plan.etat = 'tourne'; plans[0].plan.take = 11;
    plans[2].plan.etat = 'tourne'; plans[2].plan.take = 13;
    expect(estimerProjet(p, tarif)).toMatchObject({ restants: 2, tournes: 2 });
    plans[1].plan.etat = 'en_cours';
    expect(estimerProjet(p, tarif)).toMatchObject({ restants: 1, enCours: 1, credits: 65 });
    plans[1].plan.etat = 'a_tourner';
    expect(ordreAssemblage(p).map((x) => x.take)).toEqual([11, 13]);
    expect(prochainLot(p, 5).map((x) => x.plan.id)).toEqual(['p2', 'p4']);
  });
});
