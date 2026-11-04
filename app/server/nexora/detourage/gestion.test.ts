import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import type { Facturation } from '../credits.js';
import type { ClientDetourage, EtatMoteur } from './client.js';
import { Detourage, ErreurDetourage } from './gestion.js';

function faux() {
  const etats = new Map<string, EtatMoteur>();
  const journal: string[] = [];
  const client: ClientDetourage = {
    async sante() { return { ok: true }; },
    async segmenter() { return { masqueB64: '', score: 1, aire: 0.1, secondes: 0.1, largeur: 2, hauteur: 2 }; },
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
  const f: Facturation = {
    async reserver({ credits }) { appels.push(`reserver ${credits}`); return { ok: true, reservationId: `r${appels.length}`, credits }; },
    async valider(id, c) { appels.push(`valider ${id} ${c}`); },
    async liberer(id) { appels.push(`liberer ${id}`); },
  };
  return { appels, f };
}
function monter(opts: { moteur?: boolean; registre?: string } = {}) {
  const m = faux();
  const fa = factu();
  let t = 1_000_000;
  const d = new Detourage({
    registre: opts.registre ?? join(mkdtempSync(join(tmpdir(), 'detourage-')), 'registre.json'),
    moteur: (palier) => (palier === 'rapide' && opts.moteur !== false ? { id: 'gb10', client: m.client } : null),
    clientDe: (id) => (id === 'gb10' ? m.client : null),
    facturation: () => fa.f,
    maintenant: () => t,
    ttl: { termineMs: 1000, deposeMs: 5000 },
  });
  return { ...m, fa, d, avancer: (ms: number) => { t += ms; } };
}
const A = 'org-a';
const B = 'org-b';
const params = { invites: [{ image: 0, points: [[0.5, 0.5, 1]] }] };

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
    expect(() => d.creer(A, 'u', 'x', 'pro')).toThrow(/pas encore de moteur/);
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
});
