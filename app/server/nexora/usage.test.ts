import { describe, expect, it } from 'vitest';
import type { Facturation } from './credits.js';
import { ADAPTATEURS, clientPalier, coutListeUsd, lireUsage } from './niveaux.js';
import { creditsExacts, creditsFactures, devisLlm, ErreurPlafondLlm, executerSousReservation, GrandLivreUsage, Releve, tarifClientDepuisEnv } from './usage.js';

const T = { marge: 1.1, usdVersCad: 1.4025, creditsParCad: 100 };
const reponse = (usage: unknown, contenu = '{"ok":true}', statut = 200) =>
  new Response(JSON.stringify({ choices: [{ message: { content: contenu }, finish_reason: 'stop' }], usage }), { status: statut });

describe('prix client', () => {
  it('1 USD coûte 154,275 crédits (marge 1,10 × 1,4025 × 100)', () => {
    expect(creditsExacts(1, T)).toBeCloseTo(154.275, 6);
  });
  it('arrondit au crédit supérieur, minimum 1 dès qu’un jeton est consommé, 0 sinon', () => {
    expect(creditsFactures(0.004, T)).toBe(1);
    expect(creditsFactures(0.01, T)).toBe(2);
    expect(creditsFactures(0, T)).toBe(0);
  });
  it('lit les constantes de l’environnement', () => {
    expect(tarifClientDepuisEnv({ NEXORA_LLM_MARGE: '1.25' } as any).marge).toBe(1.25);
    expect(tarifClientDepuisEnv({} as any).usdVersCad).toBe(1.4025);
  });
});

describe('mesure des appels', () => {
  it('lit les usages DeepInfra (estimated_cost) et OpenRouter (cost)', () => {
    expect(lireUsage({ prompt_tokens: 10, completion_tokens: 5, estimated_cost: 0.1 }).coutFournisseurUsd).toBe(0.1);
    const u = lireUsage({ prompt_tokens: 10, completion_tokens: 50, cost: 0.2, completion_tokens_details: { reasoning_tokens: 40 } });
    expect([u.entree, u.sortie, u.raisonnement, u.coutFournisseurUsd]).toEqual([10, 50, 40, 0.2]);
  });
  it('prix de liste des trois paliers (Argon en Flex : 1 $ / 5 $)', () => {
    expect(coutListeUsd({ entree: 1e6, sortie: 1e6 }, ADAPTATEURS.expert)).toBe(6);
    expect(coutListeUsd({ entree: 1e6, sortie: 1e6 }, ADAPTATEURS.equilibre)).toBeCloseTo(0.3);
    expect(coutListeUsd({ entree: 1e6, sortie: 1e6 }, ADAPTATEURS.eco)).toBeCloseTo(0.8);
  });
  it('enregistre chaque appel au grand livre avec palier, modèle, jetons et crédits', async () => {
    const livre = new GrandLivreUsage();
    const r = new Releve({ run: 'r1', tache: 'montage', projet: 'p', utilisateur: 'u', organisation: 'o' }, 1, livre, T);
    const c = clientPalier('expert', { surveillant: r, env: { NEXORA_LLM_CLE_OPENROUTER: 'k' } as any, f: (async () => reponse({ prompt_tokens: 1000, completion_tokens: 500, cost: 0.0035 })) as any });
    await c.completer('monteur', [{ role: 'user', content: 'x' }], { json: true });
    const l = livre.lignes({ run: 'r1' });
    expect(l).toHaveLength(1);
    expect(l[0]).toMatchObject({ palier: 'expert', modele: 'google/gemini-4-argon', endpoint: 'google-ai-studio/flex', entree: 1000, sortie: 500, coutUsd: 0.0035, source: 'fournisseur', projet: 'p', role: 'monteur' });
    expect(l[0].credits).toBeCloseTo(0.0035 * 154.275, 6);
  });
  it('sans coût rapporté, calcule au prix de liste', async () => {
    const livre = new GrandLivreUsage();
    const r = new Releve({ run: 'r', tache: 't' }, 1, livre, T);
    const c = clientPalier('eco', { surveillant: r, env: { NEXORA_LLM_CLE_DEEPINFRA: 'k' } as any, f: (async () => reponse({ prompt_tokens: 1e6, completion_tokens: 1e6 })) as any });
    await c.completer('monteur', [{ role: 'user', content: 'x' }]);
    expect(livre.lignes()[0]).toMatchObject({ coutUsd: 0.8, source: 'tarif' });
  });
  it('envoie le routage Flex et coupe le raisonnement de Flash', async () => {
    const corps: any[] = [];
    const f = (async (_u: string, init: any) => { corps.push(JSON.parse(init.body)); return reponse({ prompt_tokens: 1, completion_tokens: 1 }); }) as any;
    await clientPalier('expert', { env: { NEXORA_LLM_CLE_OPENROUTER: 'k' } as any, f }).completer('monteur', [{ role: 'user', content: 'x' }]);
    await clientPalier('eco', { env: { NEXORA_LLM_CLE_DEEPINFRA: 'k' } as any, f }).completer('monteur', [{ role: 'user', content: 'x' }]);
    expect(corps[0].provider).toEqual({ order: ['google-ai-studio/flex'], allow_fallbacks: false });
    expect(corps[1].reasoning_effort).toBe('none');
    expect(corps[1].model).toBe('deepseek-ai/DeepSeek-V4.1-Flash-1017');
  });
  it('refuse sans clé', async () => {
    await expect(clientPalier('eco', { env: {} as any }).completer('monteur', [{ role: 'user', content: 'x' }])).rejects.toThrow(/NEXORA_LLM_CLE_DEEPINFRA/);
  });
});

describe('reprises et repli Flex', () => {
  const env = { NEXORA_LLM_CLE_OPENROUTER: 'k' } as any;
  it('reprend sur 429 avec attente puis réussit', async () => {
    let n = 0; const attentes: number[] = [];
    const f = (async () => (++n < 3 ? new Response('{}', { status: 429 }) : reponse({ prompt_tokens: 1, completion_tokens: 1 }))) as any;
    await clientPalier('expert', { env, f, attendre: async (ms) => { attentes.push(ms); } }).completer('monteur', [{ role: 'user', content: 'x' }]);
    expect(n).toBe(3);
    expect(attentes).toEqual([1500, 3000]);
  });
  it('sans autorisation, ne bascule jamais sur le point standard payant', async () => {
    const f = (async () => new Response('{}', { status: 429 })) as any;
    await expect(clientPalier('expert', { env, f, attendre: async () => {} }).completer('monteur', [{ role: 'user', content: 'x' }])).rejects.toThrow(/HTTP 429/);
  });
  it('avec autorisation, bascule une fois et enregistre le point réellement utilisé au double du prix', async () => {
    const livre = new GrandLivreUsage();
    const r = new Releve({ run: 'r', tache: 't' }, 1, livre, T);
    const f = (async (_u: string, init: any) => (JSON.parse(init.body).provider.order[0] === 'google-ai-studio/flex' ? new Response('{}', { status: 429 }) : reponse({ prompt_tokens: 1e6, completion_tokens: 0 }))) as any;
    await clientPalier('expert', { env, f, surveillant: r, autoriserRepli: true, attendre: async () => {} }).completer('monteur', [{ role: 'user', content: 'x' }]);
    expect(livre.lignes()[0]).toMatchObject({ endpoint: 'google-vertex/global', repli: true, coutUsd: 2, source: 'tarif' });
  });
  it('ne reprend pas sur une erreur définitive (400)', async () => {
    let n = 0;
    const f = (async () => { n++; return new Response('{}', { status: 400 }); }) as any;
    await expect(clientPalier('expert', { env, f, attendre: async () => {} }).completer('monteur', [{ role: 'user', content: 'x' }])).rejects.toThrow(/HTTP 400/);
    expect(n).toBe(1);
  });
});

describe('plafond dur', () => {
  it('refuse l’appel suivant une fois le plafond atteint', async () => {
    const r = new Releve({ run: 'r', tache: 't' }, 0.01, undefined, T);
    const c = clientPalier('expert', { surveillant: r, env: { NEXORA_LLM_CLE_OPENROUTER: 'k' } as any, f: (async () => reponse({ prompt_tokens: 1, completion_tokens: 1, cost: 0.02 })) as any });
    await c.completer('monteur', [{ role: 'user', content: 'x' }]);
    await expect(c.completer('monteur', [{ role: 'user', content: 'x' }])).rejects.toBeInstanceOf(ErreurPlafondLlm);
  });
});

describe('devis, réservation, règlement', () => {
  const faux = () => {
    const j: string[] = [];
    const fac: Facturation = {
      reserver: async (r) => { j.push(`reserve ${r.credits}`); return { ok: true, reservationId: 'res1', credits: r.credits }; },
      valider: async (_id, c) => { j.push(`settle ${c}`); },
      liberer: async () => { j.push('release'); },
    };
    return { fac, j };
  };
  it('devis : tables sans historique, moyenne de l’historique à partir de 3 runs', () => {
    const livre = new GrandLivreUsage();
    expect(devisLlm('montage', 'expert', { livre, tarif: T }).source).toBe('tables');
    for (const run of ['a', 'b', 'c']) livre.enregistrer({ run, tache: 'montage', ts: '', role: 'monteur', palier: 'expert', modele: 'm', endpoint: 'e', repli: false, entree: 10_000, sortie: 1000, raisonnement: 0, coutUsd: 0, source: 'tarif', credits: 0, ms: 1 });
    const d = devisLlm('montage', 'expert', { livre, tarif: T });
    expect(d).toMatchObject({ source: 'historique', entree: 10_000, sortie: 1000 });
    expect(d.usd).toBeCloseTo(0.015, 6);
    expect(d.plafondUsd).toBeCloseTo(0.03, 6);
  });
  it('réserve le plafond, règle le réel, libère le reste', async () => {
    const { fac, j } = faux();
    const devis = devisLlm('montage', 'expert', { tarif: T });
    const { bilan } = await executerSousReservation({ fac, devis, ctx: { run: 'x', tache: 'montage' }, tarif: T }, async (rel) => {
      rel.apres({ role: 'monteur', palier: 'expert', modele: 'm', endpoint: 'e', usage: { entree: 1, sortie: 1, raisonnement: 0, coutFournisseurUsd: 0.01 }, coutUsd: 0.01, source: 'fournisseur', ms: 1, repli: false });
    });
    expect(j).toEqual([`reserve ${devis.creditsReserves}`, 'settle 2']);
    expect(bilan.factures).toBe(2);
    expect(bilan.liberes).toBe(devis.creditsReserves - 2);
  });
  it('libère tout si rien n’a été consommé, et règle les jetons déjà dus si le travail échoue', async () => {
    const a = faux();
    const devis = devisLlm('montage', 'eco', { tarif: T });
    await executerSousReservation({ fac: a.fac, devis, ctx: { run: 'x', tache: 'montage' }, tarif: T }, async () => 1);
    expect(a.j[1]).toBe('release');
    const b = faux();
    await expect(executerSousReservation({ fac: b.fac, devis, ctx: { run: 'y', tache: 'montage' }, tarif: T }, async (rel) => {
      rel.apres({ role: 'monteur', palier: 'eco', modele: 'm', endpoint: 'e', usage: { entree: 1, sortie: 1, raisonnement: 0, coutFournisseurUsd: 0.01 }, coutUsd: 0.01, source: 'fournisseur', ms: 1, repli: false });
      throw new Error('boum');
    })).rejects.toThrow('boum');
    expect(b.j[1]).toBe(`settle ${Math.min(2, devis.creditsReserves)}`);
  });
  it('ne facture jamais plus que la réservation', async () => {
    const { fac, j } = faux();
    const devis = { ...devisLlm('montage', 'eco', { tarif: T }), creditsReserves: 3 };
    await executerSousReservation({ fac, devis, ctx: { run: 'x', tache: 'montage' }, tarif: T }, async (rel) => {
      rel.apres({ role: 'monteur', palier: 'eco', modele: 'm', endpoint: 'e', usage: { entree: 1, sortie: 1, raisonnement: 0, coutFournisseurUsd: 1 }, coutUsd: 1, source: 'fournisseur', ms: 1, repli: false });
    });
    expect(j[1]).toBe('settle 3');
  });
  it('réservation refusée : le travail ne démarre pas ; sans facturation, rien n’est débité mais tout est enregistré', async () => {
    const fac: Facturation = { reserver: async () => ({ ok: false, message: 'solde insuffisant' }), valider: async () => {}, liberer: async () => {} };
    let lance = false;
    await expect(executerSousReservation({ fac, devis: devisLlm('film', 'eco', { tarif: T }), ctx: { run: 'x', tache: 'film' } }, async () => { lance = true; })).rejects.toThrow('solde insuffisant');
    expect(lance).toBe(false);
    const livre = new GrandLivreUsage();
    const { bilan } = await executerSousReservation({ fac: null, devis: devisLlm('film', 'eco', { tarif: T }), ctx: { run: 'z', tache: 'film' }, livre, tarif: T }, async (rel) => {
      rel.apres({ role: 'monteur', palier: 'eco', modele: 'm', endpoint: 'e', usage: { entree: 5, sortie: 5, raisonnement: 0, coutFournisseurUsd: 0.01 }, coutUsd: 0.01, source: 'fournisseur', ms: 1, repli: false });
    });
    expect(bilan.factures).toBe(0);
    expect(livre.total({ run: 'z' }).credits).toBeGreaterThan(0);
  });
});

describe('juge de Nexora Mesh : coût et devis', () => {
  it('le coût suit les jetons et les prix réglables', async () => {
    const { coutJuge3dUsd, devisJuge3d } = await import('./usage.js');
    expect(coutJuge3dUsd({ entree: 1_000_000, sortie: 0 }, {})).toBeCloseTo(0.4, 6);
    expect(coutJuge3dUsd({ entree: 0, sortie: 1_000_000 }, { NEXORA_PRIX_JUGE3D_SORTIE_USD_M: '2' })).toBeCloseTo(2, 6);
    const d = devisJuge3d(undefined, {});
    expect(d.tache).toBe('juge3d');
    expect(d.creditsReserves).toBeGreaterThanOrEqual(d.credits);
    expect(d.credits).toBeGreaterThanOrEqual(1);
  });
});
