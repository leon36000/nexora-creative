import { mkdtempSync } from 'node:fs';
import { createServer, type Server } from 'node:http';
import type { AddressInfo } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import Fastify from 'fastify';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { avecCompte } from '../compte.js';
import { enregistrerDetourage, moteurPour } from './routes.js';

describe('choix du moteur', () => {
  const m = (id: string, recettes: string[], detourageUrl?: string) => ({ id, nom: id, recettes, detourageUrl });
  it('le rapide va au moteur qui déclare un serveur de détourage, le pro seulement à celui qui le déclare nommément', () => {
    const liste = [m('a', ['*']), m('b', ['detourage-rapide'], 'http://b'), m('c', ['*'], 'http://c')];
    expect(moteurPour(liste, 'rapide')?.id).toBe('b');
    expect(moteurPour([m('c', ['*'], 'http://c')], 'rapide')?.id).toBe('c');
    expect(moteurPour([m('c', ['*'], 'http://c')], 'pro')).toBeUndefined();
    expect(moteurPour([m('c', ['detourage-pro'], 'http://c')], 'pro')?.id).toBe('c');
    expect(moteurPour([m('a', ['*'])], 'rapide')).toBeUndefined();
  });
});

describe('routes /api/nexora/detourage (moteur simulé)', () => {
  let faux: Server;
  const recu: string[] = [];
  const octetsRecus: number[] = [];
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
      const morceaux: Buffer[] = [];
      req.on('data', (d) => morceaux.push(d));
      req.on('end', () => {
        octetsRecus.push(Buffer.concat(morceaux).length);
        res.setHeader('content-type', 'application/json');
        if (req.method === 'PUT') res.end(JSON.stringify({ ok: true, info: { largeur: 1280, hauteur: 720, fps: 25, duree: 4, audio: false } }));
        else if (req.url?.endsWith('/lancer')) { res.statusCode = 202; res.end('{"ok":true}'); }
        else if (req.method === 'GET' && /\/travaux\/[0-9a-f]+$/.test(req.url ?? '')) res.end(JSON.stringify({ etat: 'termine', etape: 'termine', progression: 1, message: 'terminé', mesures: { temps_total_s: 9 }, sorties: { fichiers: { 'matte.mp4': 10 }, sequences: { alpha: 4 } } }));
        else if (req.url?.includes('/sorties/matte.mp4')) { res.setHeader('content-type', 'video/mp4'); res.end('VIDEO'); }
        else res.end('{"ok":true}');
      });
    });
    await new Promise<void>((r) => faux.listen(0, '127.0.0.1', r));
    const port = (faux.address() as AddressInfo).port;
    enregistrerDetourage(app, {
      dossierDonnees: mkdtempSync(join(tmpdir(), 'detourage-routes-')),
      moteurs: () => [{ id: 'principal', nom: 'GPU', recettes: ['*'], detourageUrl: `http://127.0.0.1:${port}` }],
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

  it('identifiant mal formé : 404 sans rien demander au moteur', async () => {
    const avant = recu.length;
    const r = await inj(A, { method: 'GET', url: '/api/nexora/detourage/travaux/..%2F..' });
    expect(r.statusCode).toBe(404);
    expect(recu.length).toBe(avant);
  });
});
