import { createHash, randomBytes } from 'node:crypto';
import Fastify, { type FastifyInstance } from 'fastify';
import { exportJWK, generateKeyPair, SignJWT } from 'jose';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { accesOrganisation, monterAuthentification } from './auth.js';
import { compteCourant } from './compte.js';

/**
 * Faux site Nexora : fournisseur OIDC minimal (découverte, authorize, token avec PKCE S256, userinfo, jwks) et route
 * /api/oauth/creative-access, conformes au contrat de docs/INTEGRATION-NEXORA.md.
 */
let site: FastifyInstance;
let creative: FastifyInstance;
let issuer = '';
const codes = new Map<string, { challenge: string; nonce?: string }>();

beforeAll(async () => {
  const { publicKey, privateKey } = await generateKeyPair('RS256');
  const jwk = { ...(await exportJWK(publicKey)), kid: 'k1', alg: 'RS256', use: 'sig' };
  site = Fastify();
  site.get('/api/auth/.well-known/openid-configuration', async () => ({
    issuer,
    authorization_endpoint: `${issuer}/oauth2/authorize`,
    token_endpoint: `${issuer}/oauth2/token`,
    userinfo_endpoint: `${issuer}/oauth2/userinfo`,
    jwks_uri: `${issuer}/jwks`,
    response_types_supported: ['code'],
    subject_types_supported: ['public'],
    id_token_signing_alg_values_supported: ['RS256'],
    code_challenge_methods_supported: ['S256'],
    token_endpoint_auth_methods_supported: ['client_secret_post', 'client_secret_basic'],
  }));
  site.get('/api/auth/jwks', async () => ({ keys: [jwk] }));
  site.get('/api/auth/oauth2/authorize', async (req, reply) => {
    const q = req.query as Record<string, string>;
    const code = randomBytes(8).toString('hex');
    codes.set(code, { challenge: q.code_challenge });
    return reply.redirect(`${q.redirect_uri}?code=${code}&state=${q.state}&iss=${encodeURIComponent(issuer)}`);
  });
  site.post('/api/auth/oauth2/token', async (req, reply) => {
    const b = req.body as Record<string, string>;
    const c = codes.get(b.code);
    const attendu = c && createHash('sha256').update(b.code_verifier).digest('base64url');
    if (!c || attendu !== c.challenge) return reply.code(400).send({ error: 'invalid_grant' });
    codes.delete(b.code);
    const id_token = await new SignJWT({ sub: 'user-42' })
      .setProtectedHeader({ alg: 'RS256', kid: 'k1' }).setIssuer(issuer).setAudience('nexora-creative')
      .setIssuedAt().setExpirationTime('10m').sign(privateKey);
    return { access_token: 'jeton-acces', token_type: 'Bearer', expires_in: 600, id_token };
  });
  site.get('/api/auth/oauth2/userinfo', async (req, reply) =>
    req.headers.authorization === 'Bearer jeton-acces' ? { sub: 'user-42', email: 'a@b.ca', organization_id: 'org-42' } : reply.code(401).send());
  site.get('/api/oauth/creative-access', async (req, reply) =>
    req.headers.authorization === 'Bearer jeton-acces'
      ? { url: 'https://site.test/v1', model: 'nexora/modele', key: 'nxk_cle_secrete', territory: 'CA' }
      : reply.code(401).send());
  site.addContentTypeParser('application/x-www-form-urlencoded', { parseAs: 'string' }, (_r, body, done) =>
    done(null, Object.fromEntries(new URLSearchParams(String(body)))));
  await site.listen({ port: 0, host: '127.0.0.1' });
  const port = (site.server.address() as { port: number }).port;
  issuer = `http://127.0.0.1:${port}/api/auth`;

  creative = Fastify();
  monterAuthentification(creative, {
    issuer, clientId: 'nexora-creative', clientSecret: 'secret-du-client-de-test-0123456789',
    publicUrl: 'http://creative.test', secretSession: 'secret-de-session-de-test-0123456789-abcdef',
    siteUrl: `http://127.0.0.1:${port}`, http: true,
  });
  creative.get('/api/qui', async () => compteCourant());
  creative.get('/', async () => 'accueil');
});

afterAll(async () => {
  await creative?.close();
  await site?.close();
});

const temoins = (h: string | string[] | undefined) =>
  (Array.isArray(h) ? h : h ? [h] : []).map((c) => c.split(';')[0]).filter((c) => !c.endsWith('='));

describe('connexion unique Nexora (OIDC + PKCE)', () => {
  it('refuse l’API et renvoie les pages vers la connexion sans session', async () => {
    expect((await creative.inject('/api/qui')).statusCode).toBe(401);
    const page = await creative.inject('/');
    expect(page.statusCode).toBe(302);
    expect(page.headers.location).toMatch(/^\/auth\/connexion/);
  });

  it('connecte de bout en bout et pose le compte de l’organisation sur chaque requête', async () => {
    const debut = await creative.inject('/auth/connexion?retour=/');
    expect(debut.statusCode).toBe(302);
    const versSite = new URL(String(debut.headers.location));
    expect(versSite.searchParams.get('scope')).toBe('openid profile email creative:model');
    expect(versSite.searchParams.get('code_challenge_method')).toBe('S256');
    const oidcTemoin = temoins(debut.headers['set-cookie']).join('; ');

    const autorisation = await fetch(versSite, { redirect: 'manual' });
    const retour = new URL(String(autorisation.headers.get('location')));
    const fin = await creative.inject({ url: `${retour.pathname}${retour.search}`, headers: { cookie: oidcTemoin } });
    expect(fin.statusCode).toBe(302);
    const session = temoins(fin.headers['set-cookie']).find((c) => c.startsWith('nx_session='));
    expect(session).toBeTruthy();
    expect(String(fin.headers['set-cookie'])).toMatch(/HttpOnly/);

    const qui = await creative.inject({ url: '/api/qui', headers: { cookie: session! } });
    expect(qui.statusCode).toBe(200);
    expect(qui.json()).toEqual({ organisationId: 'org-42', utilisateurId: 'user-42', territoire: 'CA' });
    expect(accesOrganisation('org-42')?.key).toBe('nxk_cle_secrete');
    expect(session).not.toMatch(/nxk_/);
  });

  it('refuse un retour sans le témoin de connexion (état ou vérificateur absents)', async () => {
    expect((await creative.inject('/auth/retour?code=x&state=y')).statusCode).toBe(400);
  });
});
