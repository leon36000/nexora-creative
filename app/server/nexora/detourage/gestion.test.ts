import { mkdtempSync, mkdirSync, readFileSync, rmdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { Facturation } from '../credits.js';
import type { ClientDetourage, EtatMoteur } from './client.js';
import { Detourage, ErreurDetourage, type OptionsDetourage } from './gestion.js';

function faux() {
  const etats = new Map<string, EtatMoteur>();
  const journal: string[] = [];
  const client: ClientDetourage = {
    async sante() { return { ok: true }; },
    async segmenter() { return { masqueB64: '', score: 1, aire: 0.1, secondes: 0.1, largeur: 2, hauteur: 2 }; },
    async texte() { return { objets: [], secondes: 0.1, largeur: 2, hauteur: 2 }; },
    async deposer(id, nom) { journal.push(`deposer ${id} ${nom}`); return { largeur: 1280, hauteur: 720, fps: 24, duree: 5, audio: false }; },
    async lancer(id) { journal.push(`lancer ${id}`); etats.set(id, { etat: 'en_attente', progression: 0 }); },
    async etat(id) { return etats.get(id) ?? null; },
    async annuler(id) { journal.push(`annuler ${id}`); etats.set(id, { etat: 'annule', message: 'annulé' }); },
    async supprimer(id) { journal.push(`supprimer ${id}`); etats.delete(id); },
    async sortie() { throw new Error('non utilisé'); },
  };
  return { etats, journal, client };
}
function factu() {
  const appels: string[] = [];
  let reservations = 0;
  const f: Facturation = {
    async reserver({ credits }) { appels.push(`reserver ${credits}`); return { ok: true, reservationId: `r${++reservations}`, credits }; },
    async valider(id, c) { appels.push(`valider ${id} ${c}`); },
    async liberer(id) { appels.push(`liberer ${id}`); },
  };
  return { appels, f };
}
function monter(opts: { moteur?: boolean; registre?: string } = {}) {
  const m = faux();
  const fa = factu();
  let t = 1_000_000;
  const registre = opts.registre ?? join(mkdtempSync(join(tmpdir(), 'detourage-')), 'registre.json');
  const options: OptionsDetourage = {
    registre,
    moteur: (palier) => (palier === 'rapide' && opts.moteur !== false ? { id: 'gb10', client: m.client } : null),
    clientDe: (id) => (id === 'gb10' ? m.client : null),
    facturation: () => fa.f,
    maintenant: () => t,
    ttl: { termineMs: 1000, deposeMs: 5000 },
  };
  const nouveau = () => new Detourage(options);
  const d = nouveau();
  return { ...m, fa, d, nouveau, registre, avancer: (ms: number) => { t += ms; } };
}
const A = 'org-a';
const B = 'org-b';
const params = { invites: [{ image: 0, points: [[0.5, 0.5, 1]] }] };
function deferred() {
  let resolve!: () => void;
  const promise = new Promise<void>((r) => { resolve = r; });
  return { promise, resolve };
}

describe('cycle de vie d’un travail de détourage', () => {
  it('dépôt, lancement, progression, fin et crédits validés une seule fois', async () => {
    const { d, etats, fa } = monter();
    const t = d.creer(A, 'u1', 'Plan 12');
    expect(t.etat).toBe('depose');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, t.id, params, { secondes: 40, credits: 20 });
    expect(d.obtenir(A, t.id).etat).toBe('en_attente');
    etats.set(t.id, { etat: 'en_cours', etape: 'suivi', progression: 0.3, message: 'suivi' });
    expect((await d.actualiser(A, t.id)).progression).toBe(0.3);
    etats.set(t.id, { etat: 'termine', progression: 1, mesures: { temps_total_s: 12 }, sorties: { sequences: { alpha: 5 } } });
    const fin = await d.actualiser(A, t.id);
    expect(fin.etat).toBe('termine');
    expect(fin.mesures).toEqual({ temps_total_s: 12 });
    await d.actualiser(A, t.id);
    expect(fa.appels).toEqual(['reserver 20', 'valider r1 20']);
  });

  it('lancer sans vidéo déposée est refusé', async () => {
    const { d } = monter();
    const t = d.creer(A, 'u1', 'x');
    await expect(d.lancer(A, t.id, params)).rejects.toThrow(/Dépose d’abord/);
  });

  it('une organisation ne voit, ne lance, n’annule ni ne supprime le travail d’une autre', async () => {
    const { d, journal } = monter();
    const t = d.creer(A, 'u1', 'secret');
    expect(d.lister(B)).toEqual([]);
    for (const act of [() => d.obtenir(B, t.id), () => d.actualiser(B, t.id), () => d.annuler(B, t.id), () => d.supprimer(B, t.id), () => d.deposer(B, t.id, 'source.mp4', Buffer.from('x'))]) {
      await expect(Promise.resolve().then(() => act() as Promise<unknown>)).rejects.toMatchObject({ code: 404 });
    }
    expect(journal).toEqual([]);
    expect(d.lister(A)).toHaveLength(1);
  });

  it('annulation : le moteur est prévenu, les crédits sont libérés', async () => {
    const { d, fa, journal } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    const r = await d.annuler(A, t.id);
    expect(r.etat).toBe('annule');
    expect(journal).toContain(`annuler ${t.id}`);
    expect(fa.appels).toEqual(['reserver 5', 'liberer r1']);
  });

  it('reprise : après une interruption ou une erreur, relance les mêmes réglages et rend l’ancien devis', async () => {
    const { d, etats, journal, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    await expect(d.reprendre(A, t.id)).rejects.toThrow(/pas interrompu/);
    etats.set(t.id, { etat: 'interrompu', message: 'serveur redémarré' });
    await d.actualiser(A, t.id);
    const r = await d.reprendre(A, t.id);
    expect(r.etat).toBe('en_attente');
    expect(journal.filter((x) => x === `lancer ${t.id}`)).toHaveLength(2);
    expect(fa.appels).toEqual(['reserver 5', 'liberer r1', 'reserver 5']);
    expect(r.params).toEqual(params);
  });

  it('échec du moteur : état erreur et crédits libérés', async () => {
    const { d, etats, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, t.id, params, { secondes: 10, credits: 7 });
    etats.set(t.id, { etat: 'erreur', message: 'RuntimeError: CUDA' });
    const r = await d.actualiser(A, t.id);
    expect(r.etat).toBe('erreur');
    expect(r.message).toContain('CUDA');
    expect(fa.appels).toEqual(['reserver 7', 'liberer r1']);
  });

  it('suppression : annule si besoin, nettoie le dossier GPU, libère les crédits réservés', async () => {
    const { d, journal, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, t.id, params, { secondes: 10, credits: 3 });
    await d.supprimer(A, t.id);
    expect(journal).toContain(`supprimer ${t.id}`);
    expect(d.lister(A)).toEqual([]);
    expect(fa.appels).toContain('liberer r1');
  });

  it('nettoyage : les travaux terminés et les dépôts abandonnés trop anciens disparaissent, pas les récents ni ceux en cours', async () => {
    const { d, etats, avancer, journal } = monter();
    const fini = d.creer(A, 'u', 'fini');
    await d.deposer(A, fini.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, fini.id, params);
    etats.set(fini.id, { etat: 'termine', progression: 1 });
    await d.actualiser(A, fini.id);
    const encours = d.creer(A, 'u', 'encours');
    await d.deposer(A, encours.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, encours.id, params);
    const depose = d.creer(A, 'u', 'depose');
    avancer(900);
    expect(await d.nettoyer()).toEqual([]);
    avancer(200); // termine : 1100 ms > 1000
    expect(await d.nettoyer()).toEqual([fini.id]);
    avancer(5000);
    expect(await d.nettoyer()).toEqual([depose.id]);
    expect(d.lister(A).map((t) => t.id)).toEqual([encours.id]);
    expect(journal).toContain(`supprimer ${fini.id}`);
  });

  it('le registre survit à un redémarrage du serveur', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'detourage-reg-'));
    const registre = join(dir, 'registre.json');
    const a = monter({ registre });
    const t = a.d.creer(A, 'u', 'persistant');
    await a.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    const b = monter({ registre });
    expect(b.d.obtenir(A, t.id).nom).toBe('persistant');
    expect(b.d.obtenir(A, t.id).fichiers['source.mp4']).toBe(1);
  });

  it('sans moteur pour le palier demandé, le message dit pourquoi', () => {
    const { d } = monter();
    expect(() => d.creer(A, 'u', 'x', 'pro')).toThrow(ErreurDetourage);
    expect(() => d.creer(A, 'u', 'x', 'pro')).toThrow(/pro.*pas encore disponible/);
    const sans = monter({ moteur: false });
    expect(() => sans.d.creer(A, 'u', 'x')).toThrow(/Aucun moteur/);
  });

  it('moteur injoignable : le travail garde son état et le dit', async () => {
    const { d, client } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await d.lancer(A, t.id, params);
    client.etat = async () => { throw new Error('ECONNREFUSED'); };
    const r = await d.actualiser(A, t.id);
    expect(r.etat).toBe('en_attente');
    expect(r.message).toMatch(/injoignable/);
  });

  it('un seul lancer gagne la réservation et le moteur; le règlement terminal reste unique', async () => {
    const { d, client, etats, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    const reserveEntree = deferred();
    const reserveSuite = deferred();
    let reservations = 0, moteurs = 0, validations = 0;
    fa.f.reserver = async ({ credits }) => {
      const n = ++reservations;
      reserveEntree.resolve();
      await reserveSuite.promise;
      return { ok: true, reservationId: `r${n}`, credits };
    };
    fa.f.valider = async () => { validations++; };
    fa.f.liberer = async () => {};
    client.lancer = async (id) => { moteurs++; etats.set(id, { etat: 'en_attente', progression: 0 }); };

    const premier = d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    await reserveEntree.promise;
    const second = d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    const reservationsAvantSuite = reservations;
    reserveSuite.resolve();
    const resultats = await Promise.allSettled([premier, second]);

    expect(reservationsAvantSuite).toBe(1);
    expect(resultats[0].status).toBe('fulfilled');
    expect(resultats[1].status).toBe('rejected');
    if (resultats[1].status === 'rejected') expect(resultats[1].reason).toMatchObject({ code: 409 });
    expect(moteurs).toBe(1);
    etats.set(t.id, { etat: 'termine', progression: 1 });
    await d.actualiser(A, t.id);
    await d.actualiser(A, t.id);
    expect(validations).toBe(1);
  });

  it('deux identifiants distincts peuvent lancer leur moteur en parallèle', async () => {
    const { d, client, etats } = monter();
    const a = d.creer(A, 'u', 'a');
    const b = d.creer(A, 'u', 'b');
    const attente = deferred();
    const demarrages: string[] = [];
    await d.deposer(A, a.id, 'source.mp4', Buffer.from('a'), 1);
    await d.deposer(A, b.id, 'source.mp4', Buffer.from('b'), 1);
    client.lancer = async (id) => { demarrages.push(id); await attente.promise; etats.set(id, { etat: 'en_attente' }); };

    const pa = d.lancer(A, a.id, params);
    const pb = d.lancer(A, b.id, params);
    const demarragesAvantSuite = [...demarrages];
    attente.resolve();
    const resultats = await Promise.allSettled([pa, pb]);

    expect(demarragesAvantSuite).toEqual([a.id, b.id]);
    expect(resultats.map((r) => r.status)).toEqual(['fulfilled', 'fulfilled']);
  });

  it('libère le verrou après un refus de réservation', async () => {
    const { d, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    let appels = 0;
    fa.f.reserver = async ({ credits }) => ++appels === 1
      ? { ok: false, message: 'quota' }
      : { ok: true, reservationId: 'r-retry', credits };

    await expect(d.lancer(A, t.id, params, { secondes: 10, credits: 5 })).rejects.toMatchObject({ code: 402 });
    const reprise = await d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    expect(appels).toBe(2);
    expect(reprise.etat).toBe('en_attente');
  });

  it('libère le verrou après une exception de réservation', async () => {
    const { d, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    let appels = 0;
    fa.f.reserver = async ({ credits }) => {
      if (++appels === 1) throw new Error('facturation indisponible');
      return { ok: true, reservationId: 'r-retry', credits };
    };

    await expect(d.lancer(A, t.id, params, { secondes: 10, credits: 5 })).rejects.toThrow('facturation indisponible');
    const reprise = await d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    expect(appels).toBe(2);
    expect(reprise.etat).toBe('en_attente');
  });

  it('libère crédits et verrou après une erreur moteur, puis accepte un nouvel essai', async () => {
    const { d, client, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    let moteurs = 0;
    client.lancer = async () => { if (++moteurs === 1) throw new Error('moteur indisponible'); };

    await expect(d.lancer(A, t.id, params, { secondes: 10, credits: 5 })).rejects.toThrow('moteur indisponible');
    expect(t.credits?.etat).toBe('liberee');
    const reprise = await d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    expect(moteurs).toBe(2);
    expect(reprise.etat).toBe('en_attente');
    expect(reprise.credits?.etat).toBe('reservee');
    expect(fa.appels.filter((x) => x.startsWith('liberer '))).toHaveLength(1);
  });

  it('pendant une réservation, les polls et mutations ne touchent pas le travail; l’autre organisation reste en 404', async () => {
    const { d, client, journal, etats, fa } = monter();
    const t = d.creer(A, 'u', 'x');
    await d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    const reserveEntree = deferred(), reserveSuite = deferred();
    const moteurEntree = deferred(), moteurSuite = deferred();
    let reservations = 0, etatAppels = 0, validations = 0, liberations = 0;
    fa.f.reserver = async ({ credits }) => {
      reservations++;
      reserveEntree.resolve();
      await reserveSuite.promise;
      return { ok: true, reservationId: 'r-garde', credits };
    };
    fa.f.valider = async () => { validations++; };
    fa.f.liberer = async () => { liberations++; };
    client.etat = async (id) => { etatAppels++; return etats.get(id) ?? null; };
    client.lancer = async (id) => { moteurEntree.resolve(); await moteurSuite.promise; etats.set(id, { etat: 'en_attente' }); };

    const lancer = d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    await reserveEntree.promise;
    const avantReservation = { etat: t.etat, credits: t.credits, travaux: d.lister(A).length };
    const pollReservation = await d.actualiser(A, t.id);
    const mutationsReservation = await Promise.allSettled([
      d.annuler(A, t.id),
      d.supprimer(A, t.id),
      d.deposer(A, t.id, 'fond-a.png', Buffer.from('f'), 1),
      d.lancer(B, t.id, params, { secondes: 10, credits: 5 }),
    ]);
    const journalReservation = journal.slice(1);
    const etatAppelsReservation = etatAppels;
    reserveSuite.resolve();
    await moteurEntree.promise;
    const creditsPendantMoteur = t.credits && { ...t.credits };
    const etatPendantMoteur = t.etat;
    const pollMoteur = await Promise.allSettled([d.actualiser(A, t.id)]);
    const mutationsMoteur = await Promise.allSettled([d.annuler(A, t.id), d.supprimer(A, t.id)]);
    moteurSuite.resolve();
    const lancement = await Promise.allSettled([lancer]);

    expect(avantReservation).toEqual({ etat: 'depose', credits: undefined, travaux: 1 });
    expect(pollReservation).toBe(t);
    expect(mutationsReservation.slice(0, 3).map((r) => r.status)).toEqual(['rejected', 'rejected', 'rejected']);
    for (const r of mutationsReservation.slice(0, 3)) if (r.status === 'rejected') expect(r.reason).toMatchObject({ code: 409 });
    expect(mutationsReservation[3].status).toBe('rejected');
    if (mutationsReservation[3].status === 'rejected') expect(mutationsReservation[3].reason).toMatchObject({ code: 404 });
    expect(journalReservation).toEqual([]);
    expect(etatAppelsReservation).toBe(0);
    expect(pollMoteur[0].status).toBe('fulfilled');
    if (pollMoteur[0].status === 'fulfilled') expect(pollMoteur[0].value).toBe(t);
    expect(etatPendantMoteur).toBe('depose');
    expect(creditsPendantMoteur).toEqual({ reservationId: 'r-garde', credits: 5, etat: 'reservee' });
    expect(mutationsMoteur.map((r) => r.status)).toEqual(['rejected', 'rejected']);
    for (const r of mutationsMoteur) if (r.status === 'rejected') expect(r.reason).toMatchObject({ code: 409 });
    expect(lancement[0].status).toBe('fulfilled');
    expect(reservations).toBe(1);
    expect(etatAppels).toBe(0);
    expect(validations).toBe(0);
    expect(liberations).toBe(0);
    expect(d.lister(A)).toHaveLength(1);
    expect(d.lister(A)[0]?.credits?.etat).toBe('reservee');
  });

  it('après échec moteur et remboursement refusé, garde l’intention libérer au registre et à la reprise après redémarrage', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    let demarrages = 0;
    h.client.lancer = async (id) => {
      h.journal.push(`lancer ${id}`);
      demarrages++;
      h.etats.set(id, { etat: 'termine', progression: 1 });
      if (demarrages === 1) throw new Error('moteur refuse le lancement');
    };
    const libererBase = h.fa.f.liberer;
    let echecsLibere = 2;
    h.fa.f.liberer = async (id) => {
      if (echecsLibere-- > 0) { h.fa.appels.push(`liberer ${id}`); throw new Error('facturation indisponible'); }
      await libererBase(id);
    };

    await expect(h.d.lancer(A, t.id, params, { secondes: 10, credits: 5 })).rejects.toThrow('moteur refuse le lancement');
    const dansMemoire = h.d.obtenir(A, t.id);
    const dansRegistre = (JSON.parse(readFileSync(h.registre, 'utf8')) as typeof dansMemoire[]).find((x) => x.id === t.id)!;
    expect(dansMemoire).toMatchObject({ etat: 'erreur', credits: { reservationId: 'r1', etat: 'reservee', reglement: 'liberer' } });
    expect(dansRegistre).toMatchObject({ etat: 'erreur', credits: { reservationId: 'r1', etat: 'reservee', reglement: 'liberer' } });

    const redemarre = h.nouveau();
    const apresNouvelEchec = await redemarre.actualiser(A, t.id);
    expect(apresNouvelEchec).toMatchObject({ etat: 'erreur', credits: { reservationId: 'r1', etat: 'reservee', reglement: 'liberer' } });
    expect(h.fa.appels).toEqual(['reserver 5', 'liberer r1', 'liberer r1']);
    expect(h.journal.filter((x) => x.startsWith('lancer '))).toHaveLength(1);
    expect(h.fa.appels.some((x) => x.startsWith('valider '))).toBe(false);

    const recupere = await h.nouveau().actualiser(A, t.id);
    expect(recupere).toMatchObject({ etat: 'erreur', credits: { reservationId: 'r1', etat: 'liberee', reglement: 'liberer' } });
    expect(h.fa.appels).toEqual(['reserver 5', 'liberer r1', 'liberer r1', 'liberer r1']);
    expect(h.journal.filter((x) => x.startsWith('lancer '))).toHaveLength(1);
  });

  it('un remboursement refusé empêche une nouvelle réservation ou une suppression distante', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await h.d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    h.etats.set(t.id, { etat: 'erreur', message: 'moteur en erreur' });
    const libererBase = h.fa.f.liberer;
    let echecsLibere = 3;
    h.fa.f.liberer = async (id) => {
      if (echecsLibere-- > 0) { h.fa.appels.push(`liberer ${id}`); throw new Error('facturation indisponible'); }
      await libererBase(id);
    };
    await h.d.actualiser(A, t.id);
    await expect(h.d.reprendre(A, t.id)).rejects.toMatchObject({ code: 503 });
    expect(h.fa.appels).toEqual(['reserver 5', 'liberer r1', 'liberer r1']);
    expect(h.journal.filter((x) => x.startsWith('lancer '))).toHaveLength(1);

    const avantDelete = (JSON.parse(readFileSync(h.registre, 'utf8')) as typeof t[]).find((x) => x.id === t.id)!;
    await expect(h.d.supprimer(A, t.id)).rejects.toMatchObject({ code: 503 });
    expect(h.d.lister(A)).toHaveLength(1);
    expect((JSON.parse(readFileSync(h.registre, 'utf8')) as typeof t[]).find((x) => x.id === t.id)).toEqual(avantDelete);
    expect(h.journal.filter((x) => x.startsWith('supprimer '))).toEqual([]);

    await h.d.supprimer(A, t.id);
    expect(h.fa.appels).toEqual(['reserver 5', 'liberer r1', 'liberer r1', 'liberer r1', 'liberer r1']);
    expect(h.journal.filter((x) => x.startsWith('supprimer '))).toEqual([`supprimer ${t.id}`]);
    expect(h.d.lister(A)).toEqual([]);
  });

  it('une tâche interrompue dont le moteur a terminé ne reçoit pas une nouvelle réservation', async () => {
    const reprise = monter();
    const fini = reprise.d.creer(A, 'u', 'fini');
    await reprise.d.deposer(A, fini.id, 'source.mp4', Buffer.from('x'), 1);
    await reprise.d.lancer(A, fini.id, params, { secondes: 10, credits: 5 });
    fini.etat = 'interrompu'; // état local après redémarrage; le moteur a fini entre-temps.
    reprise.etats.set(fini.id, { etat: 'termine', progression: 1 });
    await expect(reprise.d.reprendre(A, fini.id)).rejects.toMatchObject({ code: 409 });
    expect(reprise.d.obtenir(A, fini.id).etat).toBe('termine');
    expect(reprise.fa.appels).toEqual(['reserver 5', 'valider r1 5']);
    expect(reprise.journal.filter((x) => x.startsWith('lancer '))).toHaveLength(1);
  });

  it('une tâche interrompue encore active est arrêtée avant suppression', async () => {
    const suppression = monter();
    const actif = suppression.d.creer(A, 'u', 'actif');
    await suppression.d.deposer(A, actif.id, 'source.mp4', Buffer.from('x'), 1);
    await suppression.d.lancer(A, actif.id, params, { secondes: 10, credits: 5 });
    actif.etat = 'interrompu'; // le registre est périmé; le moteur est encore actif.
    suppression.etats.set(actif.id, { etat: 'en_cours', progression: 0.5 });
    await suppression.d.supprimer(A, actif.id);
    expect(suppression.journal.indexOf(`annuler ${actif.id}`)).toBeGreaterThanOrEqual(0);
    expect(suppression.journal.indexOf(`annuler ${actif.id}`)).toBeLessThan(suppression.journal.indexOf(`supprimer ${actif.id}`));
    expect(suppression.fa.appels).toEqual(['reserver 5', 'liberer r1']);
  });

  it('un moteur absent bloque la suppression et conserve le registre', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await h.d.lancer(A, t.id, params);
    h.etats.set(t.id, { etat: 'erreur' });
    await h.d.actualiser(A, t.id);
    const sansMoteur = new Detourage({ registre: h.registre, moteur: () => null, clientDe: () => null });

    await expect(sansMoteur.supprimer(A, t.id)).rejects.toMatchObject({ code: 503 });
    expect(sansMoteur.lister(A).map((x) => x.id)).toEqual([t.id]);
    expect((JSON.parse(readFileSync(h.registre, 'utf8')) as typeof t[]).map((x) => x.id)).toEqual([t.id]);
    expect(h.journal.filter((x) => x.startsWith('supprimer '))).toEqual([]);
  });

  it('une lecture moteur inconnue bloque la suppression et conserve le registre', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await h.d.lancer(A, t.id, params);
    h.client.etat = async () => { throw new Error('lecture moteur indisponible'); };

    await expect(h.d.supprimer(A, t.id)).rejects.toMatchObject({ code: 503 });
    expect(h.d.lister(A).map((x) => x.id)).toEqual([t.id]);
    expect((JSON.parse(readFileSync(h.registre, 'utf8')) as typeof t[]).map((x) => x.id)).toEqual([t.id]);
    expect(h.journal.filter((x) => x.startsWith('supprimer '))).toEqual([]);
  });

  it('une annulation non confirmée bloque la suppression et conserve le registre', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await h.d.lancer(A, t.id, params);
    h.etats.set(t.id, { etat: 'en_cours', progression: 0.8 });
    h.client.annuler = async (id) => { h.journal.push(`annuler ${id}`); /* le faux moteur reste en_cours */ };

    await expect(h.d.supprimer(A, t.id)).rejects.toMatchObject({ code: 409 });
    expect(h.d.obtenir(A, t.id).etat).toBe('en_cours');
    expect(h.d.lister(A).map((x) => x.id)).toEqual([t.id]);
    expect((JSON.parse(readFileSync(h.registre, 'utf8')) as typeof t[]).map((x) => x.id)).toEqual([t.id]);
    expect(h.journal).toContain(`annuler ${t.id}`);
    expect(h.journal.filter((x) => x.startsWith('supprimer '))).toEqual([]);
  });

  it('un DELETE refusé laisse le travail dans le registre', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await h.d.lancer(A, t.id, params);
    h.etats.set(t.id, { etat: 'erreur' });
    await h.d.actualiser(A, t.id);
    h.client.supprimer = async (id) => { h.journal.push(`supprimer ${id}`); throw new Error('DELETE refusé'); };

    await expect(h.d.supprimer(A, t.id)).rejects.toThrow('DELETE refusé');
    expect(h.d.lister(A).map((x) => x.id)).toEqual([t.id]);
    expect((JSON.parse(readFileSync(h.registre, 'utf8')) as typeof t[]).map((x) => x.id)).toEqual([t.id]);
    expect(h.journal).toContain(`supprimer ${t.id}`);
  });

  it('après échec d’écriture suivant une réservation, ne valide pas le crédit d’un lancement jamais appelé', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    await h.d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    h.etats.set(t.id, { etat: 'termine', progression: 1 });
    await h.d.actualiser(A, t.id);
    expect(h.fa.appels).toEqual(['reserver 5', 'valider r1 5']);

    const callsBefore = h.journal.filter((x) => x.startsWith('lancer ')).length;
    const reserverBase = h.fa.f.reserver;
    let ecritureBloquee = false;
    h.fa.f.reserver = async (devis) => {
      const r = await reserverBase(devis);
      if (r.ok && r.reservationId === 'r2') {
        mkdirSync(`${h.registre}.tmp`); // l’échec arrive après la création réelle de r2, juste avant sauver.
        ecritureBloquee = true;
      }
      return r;
    };
    try {
      await expect(h.d.lancer(A, t.id, params, { secondes: 10, credits: 5 })).rejects.toBeTruthy();
    } finally {
      if (ecritureBloquee) rmdirSync(`${h.registre}.tmp`);
    }
    expect(h.fa.appels).toEqual(['reserver 5', 'valider r1 5', 'reserver 5']);
    expect(h.d.obtenir(A, t.id).credits).toMatchObject({ reservationId: 'r2', etat: 'reservee', reglement: 'liberer' });
    expect(h.journal.filter((x) => x.startsWith('lancer '))).toHaveLength(callsBefore);
    await h.d.actualiser(A, t.id);
    expect(h.fa.appels).toEqual(['reserver 5', 'valider r1 5', 'reserver 5', 'liberer r2']);
    expect(h.fa.appels.filter((x) => x.startsWith('valider '))).toEqual(['valider r1 5']);
    expect(h.d.obtenir(A, t.id).credits).toMatchObject({ reservationId: 'r2', etat: 'liberee', reglement: 'liberer' });
  });

  it('si sauver échoue après le rejet moteur, rejoue libérer r2 sans relire le moteur', async () => {
    const h = monter();
    const t = h.d.creer(A, 'u', 'x');
    await h.d.deposer(A, t.id, 'source.mp4', Buffer.from('x'), 1);
    let appelsMoteur = 0;
    const lancerBase = h.client.lancer;
    h.client.lancer = async (id, p) => {
      appelsMoteur++;
      if (appelsMoteur === 1) return lancerBase(id, p);
      mkdirSync(`${h.registre}.tmp`); // la réservation r2 est sauvée; le sauver du catch moteur échouera.
      throw new Error('moteur refuse le second lancement');
    };
    const etatBase = h.client.etat;
    let lecturesMoteur = 0;
    h.client.etat = async (id) => { lecturesMoteur++; return etatBase(id); };

    await h.d.lancer(A, t.id, params, { secondes: 10, credits: 5 });
    h.etats.set(t.id, { etat: 'termine', progression: 1 });
    await h.d.actualiser(A, t.id);
    expect(h.fa.appels).toEqual(['reserver 5', 'valider r1 5']);
    const lecturesAvantNouvellePrise = lecturesMoteur;
    try {
      await expect(h.d.lancer(A, t.id, params, { secondes: 10, credits: 5 })).rejects.toBeTruthy();
    } finally {
      rmdirSync(`${h.registre}.tmp`);
    }
    expect(h.fa.appels).toEqual(['reserver 5', 'valider r1 5', 'reserver 5']);
    expect(h.d.obtenir(A, t.id).credits).toMatchObject({ reservationId: 'r2', etat: 'reservee', reglement: 'liberer' });
    expect(lecturesMoteur).toBe(lecturesAvantNouvellePrise + 1); // la seule lecture est le prévol avant r2.

    await h.d.actualiser(A, t.id);
    expect(h.fa.appels).toEqual(['reserver 5', 'valider r1 5', 'reserver 5', 'liberer r2']);
    expect(lecturesMoteur).toBe(lecturesAvantNouvellePrise + 1);
    expect(h.d.obtenir(A, t.id).credits).toMatchObject({ reservationId: 'r2', etat: 'liberee', reglement: 'liberer' });
  });
});
