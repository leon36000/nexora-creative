import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { createServer, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import Fastify from 'fastify';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { avecCompte } from '../compte.js';
import { enregistrerDetourage, moteurPour, serviceRapide } from './routes.js';

describe('choix du moteur', () => {
  const m = (id: string, recettes: string[], detourageUrl?: string) => ({ id, nom: id, recettes, detourageUrl });
  it('le rapide va au moteur qui déclare un serveur de détourage, le pro seulement à celui qui le déclare nommément', () => {
    const liste = [m('a', ['*']), m('b', ['detourage-rapide'], 'http://b'), m('c', ['*'], 'http://c')];
    expect(moteurPour(liste, 'rapide')?.id).toBe('b');
    expect(moteurPour([m('c', ['*'], 'http://c')], 'rapide')?.id).toBe('c');
    expect(moteurPour([m('c', ['*'], 'http://c')], 'pro')).toBeUndefined();
    expect(moteurPour([m('c', ['detourage-pro'], 'http://c')], 'pro')?.id).toBe('c');
    expect(moteurPour([m('a', ['*'])], 'rapide')).toBeUndefined();
    expect(moteurPour([m('a', ['h3-max'], 'http://a')], 'rapide')).toBeUndefined();
    const natif = { id: 'detourage-natif', nom: 'Natif', detourageUrl: 'http://localhost:1234' };
    expect(serviceRapide([m('a', ['h3-max'], 'http://a')], natif)).toBe(natif);
    expect(serviceRapide([m('a', ['h3-max'], 'http://a')])).toBeUndefined();
    expect(serviceRapide([m('b', ['detourage-rapide'], 'http://b')])?.id).toBe('b');
    expect(serviceRapide([m('detourage-natif', ['h3-max'], 'http://dedie')], natif)).toBeUndefined();
    for (const recette of ['detourage-rapide', 'detourage-pro', '*']) {
      expect(serviceRapide([m('detourage-natif', [recette], 'http://dedie')], natif)).toBeUndefined();
      expect(serviceRapide([m('detourage-natif', [recette], 'http://dedie')])).toBeUndefined();
    }
  });
});

describe('disponibilité du détourage pro', () => {
  it('reste indisponible même si un moteur pro est déclaré, avant tout dépôt', async () => {
    const app = Fastify();
    const { arreter } = enregistrerDetourage(app, {
      dossierDonnees: mkdtempSync(join(tmpdir(), 'detourage-pro-')),
      moteurs: () => [{ id: 'pro', nom: 'Pro', recettes: ['detourage-pro'], detourageUrl: 'http://127.0.0.1:1' }],
      facturation: () => null, nexora: false,
    });
    try {
      const capacites = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(capacites.statusCode).toBe(200);
      expect(capacites.json().pro.disponible).toBe(false);
      const creation = await app.inject({ method: 'POST', url: '/api/nexora/detourage/travaux', payload: { palier: 'pro' } });
      expect(creation.statusCode).toBe(503);
      expect(creation.json().error).not.toMatch(/poids.*install/i);
      const travaux = await app.inject({ method: 'GET', url: '/api/nexora/detourage/travaux' });
      expect(travaux.json()).toEqual([]);
    } finally {
      arreter();
      await app.close();
    }
  });

  it('refuse un ancien travail pro même si la requête demande le palier rapide', async () => {
    const dossierDonnees = mkdtempSync(join(tmpdir(), 'detourage-pro-ancien-'));
    const id = 'a'.repeat(24);
    const mixte = 'c'.repeat(24);
    mkdirSync(join(dossierDonnees, 'detourage'), { recursive: true });
    const repris = 'b'.repeat(24);
    const ancien = {
      id, organisation: 'local', utilisateur: 'local', nom: 'ancien', moteurId: 'pro',
      creeLe: Date.now(), majLe: Date.now(), etat: 'depose', etape: 'dépôt', progression: 0,
      message: '', fichiers: { 'source.mp4': 1 }, source: { duree: 1, fps: 24 },
    };
    writeFileSync(join(dossierDonnees, 'detourage', 'registre.json'), JSON.stringify([
      ancien, { ...ancien, id: repris, etat: 'interrompu', params: { source: 'source.mp4' } },
      { ...ancien, id: mixte, moteurId: 'mixte', etat: 'interrompu', params: { source: 'source.mp4', palier: 'pro' } },
    ]));
    const app = Fastify();
    const { arreter } = enregistrerDetourage(app, {
      dossierDonnees,
      moteurs: () => [
        { id: 'pro', nom: 'Pro', recettes: ['detourage-pro'], detourageUrl: 'http://127.0.0.1:1' },
        { id: 'mixte', nom: 'Mixte', recettes: ['*', 'detourage-pro'], detourageUrl: 'http://127.0.0.1:1' },
      ],
      facturation: () => null, nexora: false,
    });
    try {
      const lancement = await app.inject({ method: 'POST', url: `/api/nexora/detourage/travaux/${id}/lancer`,
        payload: { palier: 'rapide', invites: [{ image: 0, points: [[0.5, 0.5, 1]] }] } });
      expect(lancement.statusCode).toBe(503);
      const travail = await app.inject({ method: 'GET', url: `/api/nexora/detourage/travaux/${id}` });
      expect(travail.json().etat).toBe('depose');
      const reprise = await app.inject({ method: 'POST', url: `/api/nexora/detourage/travaux/${repris}/reprendre` });
      expect(reprise.statusCode).toBe(503);
      const interrompu = await app.inject({ method: 'GET', url: `/api/nexora/detourage/travaux/${repris}` });
      expect(interrompu.json().etat).toBe('interrompu');
      const reprisePro = await app.inject({ method: 'POST', url: `/api/nexora/detourage/travaux/${mixte}/reprendre` });
      expect(reprisePro.statusCode).toBe(503);
    } finally {
      arreter();
      await app.close();
    }
  });
});

describe('santé du détourage rapide', () => {
  it('bloque une collision même avec recettes rapides et conserve les travaux en suivi ou en reprise', async () => {
    let appels = 0;
    const faux = createServer((_req, res) => { appels++; res.end('{"ok":true}'); });
    await new Promise<void>((r) => faux.listen(0, '127.0.0.1', r));
    const port = (faux.address() as AddressInfo).port;
    const dossierDonnees = mkdtempSync(join(tmpdir(), 'detourage-collision-'));
    const suivi = 'd'.repeat(24), reprise = 'f'.repeat(24);
    const ancien = {
      id: suivi, organisation: 'local', utilisateur: 'local', nom: 'ancien', moteurId: 'detourage-natif',
      creeLe: Date.now(), majLe: Date.now(), etat: 'en_cours', etape: 'calcul', progression: 40,
      message: '', fichiers: { 'source.mp4': 1 }, source: { duree: 1, fps: 24 },
      params: { source: 'source.mp4' }, credits: { reservationId: 'reserve-factice', credits: 3, etat: 'reservee' },
    };
    mkdirSync(join(dossierDonnees, 'detourage'), { recursive: true });
    writeFileSync(join(dossierDonnees, 'detourage', 'registre.json'), JSON.stringify([ancien, { ...ancien, id: reprise, etat: 'interrompu' }]));
    const app = Fastify();
    let natifActif = true;
    const { arreter, detourage } = enregistrerDetourage(app, {
      dossierDonnees,
      moteurs: () => [{ id: 'detourage-natif', nom: 'Autre', recettes: ['detourage-rapide', 'detourage-pro', '*'], detourageUrl: `http://127.0.0.1:${port}` }],
      serviceNatif: () => natifActif ? { id: 'detourage-natif', nom: 'Natif', detourageUrl: `http://127.0.0.1:${port}` } : undefined,
      facturation: () => null, nexora: false,
    });
    try {
      const capacites = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(capacites.json().rapide).toMatchObject({ disponible: false, moteur: null });
      expect(capacites.json().pro).toMatchObject({ disponible: false, moteur: null });
      expect((await app.inject({ method: 'POST', url: '/api/nexora/detourage/travaux', payload: {} })).statusCode).toBe(503);
      const suiviResult = await app.inject({ method: 'GET', url: `/api/nexora/detourage/travaux/${suivi}` });
      expect(suiviResult.json()).toMatchObject({ etat: 'en_cours', progression: 40, moteur: 'detourage-natif' });
      expect(detourage.obtenir('local', suivi).credits?.etat).toBe('reservee');
      expect((await app.inject({ method: 'POST', url: `/api/nexora/detourage/travaux/${reprise}/reprendre` })).statusCode).toBe(503);
      expect(detourage.obtenir('local', reprise).etat).toBe('interrompu');
      expect(detourage.obtenir('local', reprise).credits?.etat).toBe('reservee');
      natifActif = false;
      expect((await app.inject({ method: 'GET', url: `/api/nexora/detourage/travaux/${suivi}` })).json().etat).toBe('en_cours');
      expect((await app.inject({ method: 'POST', url: `/api/nexora/detourage/travaux/${reprise}/reprendre` })).statusCode).toBe(503);
      expect(detourage.obtenir('local', suivi).credits?.etat).toBe('reservee');
      expect(appels).toBe(0);
    } finally { arreter(); await app.close(); await new Promise<void>((r) => faux.close(() => r())); }
  });

  it('ne réaffecte pas un ancien travail principal au service natif', async () => {
    const dossierDonnees = mkdtempSync(join(tmpdir(), 'detourage-historique-'));
    const id = 'e'.repeat(24);
    mkdirSync(join(dossierDonnees, 'detourage'), { recursive: true });
    writeFileSync(join(dossierDonnees, 'detourage', 'registre.json'), JSON.stringify([{
      id, organisation: 'local', utilisateur: 'local', nom: 'ancien', moteurId: 'principal',
      creeLe: Date.now(), majLe: Date.now(), etat: 'depose', etape: 'dépôt', progression: 0,
      message: '', fichiers: { 'source.mp4': 1 }, source: { duree: 1, fps: 24 },
    }]));
    const app = Fastify();
    const { arreter } = enregistrerDetourage(app, {
      dossierDonnees,
      moteurs: () => [{ id: 'principal', nom: 'GB10', recettes: ['qwen21'] }],
      serviceNatif: () => ({ id: 'detourage-natif', nom: 'Natif', detourageUrl: 'http://127.0.0.1:1' }),
      facturation: () => null, nexora: false,
    });
    try {
      const lancement = await app.inject({ method: 'POST', url: `/api/nexora/detourage/travaux/${id}/lancer`,
        payload: { invites: [{ image: 0, points: [[0.5, 0.5, 1]] }] } });
      expect(lancement.statusCode).toBe(503);
      const travail = await app.inject({ method: 'GET', url: `/api/nexora/detourage/travaux/${id}` });
      expect(travail.json()).toMatchObject({ etat: 'depose', moteur: 'principal' });
    } finally { arreter(); await app.close(); }
  });

  it('utilise le service natif même si les recettes Comfy excluent le détourage', async () => {
    const recus: string[] = [];
    const faux = createServer((req, res) => {
      recus.push(`${req.method} ${req.url} ${req.headers.authorization}`);
      res.setHeader('content-type', 'application/json');
      res.end('{"ok":true,"modeles":{"sam":["SAM 3.1"]}}');
    });
    await new Promise<void>((r) => faux.listen(0, '127.0.0.1', r));
    const port = (faux.address() as AddressInfo).port;
    const app = Fastify();
    const { arreter } = enregistrerDetourage(app, {
      dossierDonnees: mkdtempSync(join(tmpdir(), 'detourage-natif-')),
      moteurs: () => [{ id: 'principal', nom: 'GB10', recettes: ['qwen21', 'music3'] }],
      serviceNatif: () => ({ id: 'detourage-natif', nom: 'Détourage natif', detourageUrl: `http://127.0.0.1:${port}`, detourageJeton: 'jeton-factice' }),
      facturation: () => null, nexora: false,
    });
    try {
      const result = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(result.json().rapide).toMatchObject({ disponible: true, moteur: { id: 'detourage-natif' } });
      expect(result.json().pro.disponible).toBe(false);
      expect(recus).toEqual(['GET /sante Bearer jeton-factice']);
    } finally {
      arreter(); await app.close(); await new Promise<void>((r) => faux.close(() => r()));
    }
  });

  it('distingue un moteur déclaré mais refusant la santé d’un moteur qui répond', async () => {
    let statut = 401;
    let corps: Record<string, unknown> = {};
    const faux = createServer((_req, res) => {
      res.statusCode = statut;
      res.setHeader('content-type', 'application/json');
      res.end(JSON.stringify(corps));
    });
    await new Promise<void>((r) => faux.listen(0, '127.0.0.1', r));
    const port = (faux.address() as AddressInfo).port;
    const app = Fastify();
    const { arreter } = enregistrerDetourage(app, {
      dossierDonnees: mkdtempSync(join(tmpdir(), 'detourage-sante-')),
      moteurs: () => [{ id: 'rapide', nom: 'Rapide', recettes: ['detourage-rapide'], detourageUrl: `http://127.0.0.1:${port}` }],
      facturation: () => null, nexora: false,
    });
    try {
      const refus = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(refus.json().rapide).toMatchObject({ disponible: false, moteur: { id: 'rapide' } });
      statut = 200;
      const incomplet = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(incomplet.json().rapide).toMatchObject({ disponible: false, moteur: { id: 'rapide' } });
      corps = { ok: false };
      const malade = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(malade.json().rapide).toMatchObject({ disponible: false, moteur: { id: 'rapide' } });
      corps = { ok: true };
      const ok = await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' });
      expect(ok.json().rapide).toMatchObject({ disponible: true, moteur: { id: 'rapide' } });
    } finally {
      arreter();
      await app.close();
      await new Promise<void>((r) => faux.close(() => r()));
    }
  });
});

describe('routes /api/nexora/detourage (moteur simulé)', () => {
  let faux: Server;
  const recu: string[] = [];
  const octetsRecus: number[] = [];
  const sansJeton: string[] = [];
  const JETON = 'jeton-de-test-0123456789abcdefghijklmnop';
  const app = Fastify();
  // comme monterAuthentification : la requête s'exécute dans le contexte du compte
  app.addHook('onRequest', (req, _r, done) => avecCompte({ organisationId: String(req.headers['x-org']), utilisateurId: 'u', territoire: 'CA' }, done));
  type Opts = { method: 'GET' | 'POST' | 'PUT' | 'DELETE'; url: string; headers?: Record<string, string>; payload?: string | Buffer | object };
  const inj = (c: { organisationId: string }, o: Opts) => app.inject({ ...o, headers: { ...(o.headers ?? {}), 'x-org': c.organisationId } });
  const A = { organisationId: 'org-a', utilisateurId: 'ua', territoire: 'CA' };
  const B = { organisationId: 'org-b', utilisateurId: 'ub', territoire: 'CA' };
  beforeAll(async () => {
    faux = createServer((req, res) => {
      recu.push(`${req.method} ${req.url}`);
      if (req.headers.authorization !== `Bearer ${JETON}`) { // comme serveur.py : 401 sans le jeton partagé
        sansJeton.push(`${req.method} ${req.url}`);
        res.statusCode = 401; res.end('{"erreur":"jeton manquant ou invalide"}'); return;
      }
      const morceaux: Buffer[] = [];
      req.on('data', (d) => morceaux.push(d));
      req.on('end', () => {
        octetsRecus.push(Buffer.concat(morceaux).length);
        res.setHeader('content-type', 'application/json');
        if (req.method === 'PUT') res.end(JSON.stringify({ ok: true, info: { largeur: 1280, hauteur: 720, fps: 25, duree: 4, audio: false } }));
        else if (req.url?.endsWith('/lancer')) { res.statusCode = 202; res.end('{"ok":true}'); }
        else if (req.url === '/texte') res.end(JSON.stringify({ objets: [{ masque_b64: 'MASQUE', score: 0.9, boite: [0.1, 0.1, 0.5, 0.9], aire: 0.25 }], secondes: 0.5, largeur: 1280, hauteur: 720 }));
        else if (req.method === 'GET' && /\/travaux\/[0-9a-f]+$/.test(req.url ?? '')) res.end(JSON.stringify({ etat: 'termine', etape: 'termine', progression: 1, message: 'terminé', mesures: { temps_total_s: 9 }, sorties: { fichiers: { 'matte.mp4': 10 }, sequences: { alpha: 4 } } }));
        else if (req.url?.includes('/sorties/matte.mp4')) { res.setHeader('content-type', 'video/mp4'); res.end('VIDEO'); }
        else res.end('{"ok":true}');
      });
    });
    await new Promise<void>((r) => faux.listen(0, '127.0.0.1', r));
    const port = (faux.address() as AddressInfo).port;
    enregistrerDetourage(app, {
      dossierDonnees: mkdtempSync(join(tmpdir(), 'detourage-routes-')),
      moteurs: () => [{ id: 'principal', nom: 'GPU', recettes: ['qwen21', 'music3'] }],
      serviceNatif: () => ({ id: 'detourage-natif', nom: 'Détourage natif', detourageUrl: `http://127.0.0.1:${port}`, detourageJeton: JETON }),
      facturation: () => null, nexora: false,
    });
    await app.ready();
  });
  afterAll(async () => { await app.close(); faux.close(); });

  const creer = async (c = A) => (await inj(c, { method: 'POST', url: '/api/nexora/detourage/travaux', payload: { nom: 'plan' } })).json() as { id: string };

  it('dépôt en flux, lancement validé, suivi, sortie relayée', async () => {
    const t = await creer();
    const put = await inj(A, { method: 'PUT', url: `/api/nexora/detourage/travaux/${t.id}/source`, headers: { 'content-type': 'application/octet-stream' }, payload: Buffer.alloc(5000, 1) });
    expect(put.statusCode).toBe(200);
    expect(put.json().source).toMatchObject({ largeur: 1280, fps: 25 });
    expect(octetsRecus).toContain(5000);
    const mauvais = await inj(A, { method: 'POST', url: `/api/nexora/detourage/travaux/${t.id}/lancer`, payload: { invites: [{ image: 0, points: [[2, 0.5, 1]] }] } });
    expect(mauvais.statusCode).toBe(400);
    const horsPlage = await inj(A, { method: 'POST', url: `/api/nexora/detourage/travaux/${t.id}/lancer`, payload: { invites: [{ image: 9999, points: [[0.5, 0.5, 1]] }] } });
    expect(horsPlage.statusCode).toBe(400);
    expect(horsPlage.json().error).toMatch(/après la dernière image/);
    const pro = await inj(A, { method: 'POST', url: `/api/nexora/detourage/travaux/${t.id}/lancer`, payload: { palier: 'pro', invites: [{ image: 0, points: [[0.5, 0.5, 1]] }] } });
    expect(pro.statusCode).toBe(503);
    const ok = await inj(A, { method: 'POST', url: `/api/nexora/detourage/travaux/${t.id}/lancer`, payload: { invites: [{ image: 0, points: [[0.5, 0.5, 1], [0.1, 0.1, 0]] }] } });
    expect(ok.statusCode).toBe(200);
    expect(ok.json().devis.secondes).toBeGreaterThan(0);
    const etat = await inj(A, { method: 'GET', url: `/api/nexora/detourage/travaux/${t.id}` });
    expect(etat.json()).toMatchObject({ etat: 'termine', progression: 1 });
    const video = await inj(A, { method: 'GET', url: `/api/nexora/detourage/travaux/${t.id}/sorties/matte.mp4` });
    expect(video.statusCode).toBe(200);
    expect(video.body).toBe('VIDEO');
    const evade = await inj(A, { method: 'GET', url: `/api/nexora/detourage/travaux/${t.id}/sorties/..%2F..%2Fetc%2Fpasswd` });
    expect(evade.statusCode).toBe(404);
    expect(sansJeton).toEqual([]); // chaque requête vers la machine GPU porte le jeton
    expect(JSON.stringify(etat.json())).not.toContain(JETON); // et il n'est jamais renvoyé au navigateur
  });

  it('une autre organisation ne voit rien et ne peut rien faire', async () => {
    const t = await creer(A);
    for (const [methode, url] of [['GET', ''], ['POST', '/annuler'], ['DELETE', ''], ['GET', '/sorties/matte.mp4']] as const) {
      const r = await inj(B, { method: methode, url: `/api/nexora/detourage/travaux/${t.id}${url}` });
      expect(r.statusCode, `${methode} ${url}`).toBe(404);
    }
    const liste = await inj(B, { method: 'GET', url: '/api/nexora/detourage/travaux' });
    expect(liste.json()).toEqual([]);
    const put = await inj(B, { method: 'PUT', url: `/api/nexora/detourage/travaux/${t.id}/source`, headers: { 'content-type': 'application/octet-stream' }, payload: Buffer.alloc(10) });
    expect(put.statusCode).toBe(404);
  });

  it('sélection par mot : les objets reviennent, un mot vide est refusé sans appeler le moteur', async () => {
    const imageB64 = 'A'.repeat(200);
    const ok = await inj(A, { method: 'POST', url: '/api/nexora/detourage/texte', payload: { imageB64, texte: ' person ' } });
    expect(ok.statusCode).toBe(200);
    expect(ok.json()).toMatchObject({ objets: [{ masqueB64: 'MASQUE', score: 0.9, boite: [0.1, 0.1, 0.5, 0.9], aire: 0.25 }], secondes: 0.5, largeur: 1280, hauteur: 720 });
    const avant = recu.length;
    for (const payload of [{ imageB64, texte: '   ' }, { imageB64, texte: 'person', seuil: 2 }]) {
      const r = await inj(A, { method: 'POST', url: '/api/nexora/detourage/texte', payload });
      expect(r.statusCode).toBe(400);
    }
    expect(recu.length).toBe(avant); // rien n'a été demandé au moteur
    expect(sansJeton).toEqual([]); // le jeton accompagne la requête au moteur
  });

  it('identifiant mal formé : 404 sans rien demander au moteur', async () => {
    const avant = recu.length;
    const r = await inj(A, { method: 'GET', url: '/api/nexora/detourage/travaux/..%2F..' });
    expect(r.statusCode).toBe(404);
    expect(recu.length).toBe(avant);
  });
});


describe('registre de détourage illisible', () => {
  it('répond 503 sur la liste et la création sans écraser le fichier ni appeler moteur ou crédits', async () => {
    const dossierDonnees = mkdtempSync(join(tmpdir(), 'matte-registre-http-'));
    const dossier = join(dossierDonnees, 'detourage');
    mkdirSync(dossier);
    const chemin = join(dossier, 'registre.json');
    const original = '[{"id":"contenu-a-ne-pas-exposer"';
    writeFileSync(chemin, original);
    let appels = 0;
    const app = Fastify();
    const { arreter, detourage } = enregistrerDetourage(app, {
      dossierDonnees, moteurs: () => { appels++; return []; },
      facturation: () => { appels++; return null; }, nexora: false,
    });
    try {
      for (const requete of [
        { method: 'GET' as const, url: '/api/nexora/detourage/travaux' },
        { method: 'POST' as const, url: '/api/nexora/detourage/travaux', payload: {} },
        { method: 'GET' as const, url: `/api/nexora/detourage/travaux/${'a'.repeat(24)}` },
      ]) {
        const reponse = await app.inject(requete);
        expect(reponse.statusCode).toBe(503);
        expect(reponse.json()).toEqual({ error: 'Le registre du détourage est indisponible. Réessaie plus tard.' });
        expect(reponse.body).not.toContain(chemin);
        expect(reponse.body).not.toContain('contenu-a-ne-pas-exposer');
      }
      expect(await detourage.nettoyer()).toEqual([]);
      expect(appels).toBe(0);
      expect(readFileSync(chemin, 'utf8')).toBe(original);
      // Le reste du serveur et la déclaration des capacités restent accessibles.
      expect((await app.inject({ method: 'GET', url: '/api/nexora/detourage/capacites' })).statusCode).toBe(200);
    } finally { arreter(); await app.close(); }
  });
});
