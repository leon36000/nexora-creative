/**
 * Connexion unique au portail Nexora AI (OpenID Connect, code + PKCE), sur le patron de WorkStudio
 * (docs/INTEGRATION-NEXORA.md). Sans configuration OIDC, le serveur reste en « poste local » : un seul compte, aucun
 * filtre, territoire tiré de NEXORA_TERRITOIRE. Avec configuration, toute requête sans session valide est refusée
 * (API, direct) ou renvoyée vers la connexion (pages), et chaque requête s'exécute dans le compte de sa session.
 */
import type { FastifyInstance, FastifyReply, FastifyRequest } from 'fastify';
import * as oidc from 'openid-client';
import { avecCompte } from './compte.js';
import { lireSession, signerSession } from './session.js';

export interface ConfigAuth {
  issuer: string;
  clientId: string;
  clientSecret: string;
  /** Adresse publique de Nexora Creative (retour : `${publicUrl}/auth/retour`). */
  publicUrl: string;
  secretSession: string;
  /** Adresse du site Nexora (route d'accès `/api/oauth/creative-access`). */
  siteUrl: string;
  /** Autorise http:// (développement local seulement). */
  http?: boolean;
  dureeSessionMs?: number;
}

/** Ce que le site remet pour l'organisation : la passerelle /v1, son modèle par défaut, sa clé, son territoire. */
export interface AccesOrganisation { url: string; model: string; key: string; territory: string | null }

/** Accès des organisations connectées, en mémoire seulement (jamais dans le témoin ni dans le navigateur). */
const acces = new Map<string, AccesOrganisation>();
export const accesOrganisation = (organisationId: string) => acces.get(organisationId);

export function configAuthDepuisEnv(env: NodeJS.ProcessEnv = process.env): ConfigAuth | null {
  const issuer = env.NEXORA_OIDC_ISSUER?.trim();
  const clientId = env.NEXORA_OIDC_CLIENT_ID?.trim();
  const clientSecret = env.NEXORA_OIDC_CLIENT_SECRET?.trim();
  const publicUrl = env.NEXORA_PUBLIC_URL?.trim().replace(/\/+$/, '');
  const secretSession = env.NEXORA_SESSION_SECRET?.trim();
  const siteUrl = env.NEXORA_SITE_URL?.trim().replace(/\/+$/, '');
  if (!issuer && !clientId) return null;
  const manque = Object.entries({ NEXORA_OIDC_ISSUER: issuer, NEXORA_OIDC_CLIENT_ID: clientId, NEXORA_OIDC_CLIENT_SECRET: clientSecret, NEXORA_PUBLIC_URL: publicUrl, NEXORA_SESSION_SECRET: secretSession, NEXORA_SITE_URL: siteUrl })
    .filter(([, v]) => !v).map(([k]) => k);
  // Configuration partielle : on refuse de démarrer plutôt que d'ouvrir le studio sans authentification.
  if (manque.length) throw new Error(`Connexion Nexora incomplète, variables manquantes : ${manque.join(', ')}`);
  return { issuer: issuer!, clientId: clientId!, clientSecret: clientSecret!, publicUrl: publicUrl!, secretSession: secretSession!, siteUrl: siteUrl!, http: env.NEXORA_OIDC_HTTP === '1' };
}

const TEMOIN = 'nx_session';
const TEMOIN_OIDC = 'nx_oidc';

function lireTemoin(req: FastifyRequest, nom: string): string | null {
  const brut = req.headers.cookie ?? '';
  for (const morceau of brut.split(/;\s*/)) {
    const i = morceau.indexOf('=');
    if (i > 0 && morceau.slice(0, i) === nom) return decodeURIComponent(morceau.slice(i + 1));
  }
  return null;
}

function poserTemoin(reply: FastifyReply, nom: string, valeur: string, maxAgeS: number, securise: boolean) {
  const attrs = [`${nom}=${encodeURIComponent(valeur)}`, 'Path=/', 'HttpOnly', 'SameSite=Lax', `Max-Age=${maxAgeS}`];
  if (securise) attrs.push('Secure');
  const deja = reply.getHeader('set-cookie');
  const liste = Array.isArray(deja) ? deja.map(String) : deja ? [String(deja)] : [];
  reply.header('set-cookie', [...liste.filter((c) => !c.startsWith(`${nom}=`)), attrs.join('; ')]);
}

const PUBLIC = /^\/auth\//;

export function monterAuthentification(app: FastifyInstance, cfg: ConfigAuth, f: typeof fetch = fetch) {
  const securise = cfg.publicUrl.startsWith('https://');
  const duree = cfg.dureeSessionMs ?? 12 * 3600 * 1000;
  let decouverte: Promise<oidc.Configuration> | null = null;
  const configuration = () =>
    (decouverte ??= oidc.discovery(new URL(cfg.issuer), cfg.clientId, cfg.clientSecret, undefined, {
      ...(cfg.http ? { execute: [oidc.allowInsecureRequests] } : {}),
      [oidc.customFetch]: f,
    }).catch((e) => { decouverte = null; throw e; }));

  // Chaque requête s'exécute dans le compte de sa session (crochet à rappel : le reste de la requête hérite du contexte).
  app.addHook('onRequest', (req, reply, done) => {
    const chemin = req.url.split('?')[0];
    if (PUBLIC.test(chemin)) return done();
    const brut = lireTemoin(req, TEMOIN);
    const s = brut ? lireSession(brut, cfg.secretSession) : null;
    if (!s) {
      if (chemin.startsWith('/api/') || chemin === '/live') {
        void reply.code(401).send({ error: 'Connecte-toi à ton compte Nexora pour utiliser Nexora Creative.' });
      } else {
        void reply.redirect(`/auth/connexion?retour=${encodeURIComponent(req.url)}`);
      }
      return;
    }
    avecCompte({ organisationId: s.o, utilisateurId: s.u, territoire: s.t }, done);
  });

  app.get('/auth/connexion', async (req, reply) => {
    const c = await configuration();
    const verifier = oidc.randomPKCECodeVerifier();
    const state = oidc.randomState();
    const retour = String((req.query as any)?.retour ?? '/');
    poserTemoin(reply, TEMOIN_OIDC, signerSession({ o: state, u: verifier, t: retour.startsWith('/') ? retour : '/', e: Date.now() + 10 * 60_000 }, cfg.secretSession), 600, securise);
    const url = oidc.buildAuthorizationUrl(c, {
      redirect_uri: `${cfg.publicUrl}/auth/retour`,
      scope: 'openid profile email creative:model',
      code_challenge: await oidc.calculatePKCECodeChallenge(verifier),
      code_challenge_method: 'S256',
      state,
    });
    return reply.redirect(url.href);
  });

  app.get('/auth/retour', async (req, reply) => {
    const brut = lireTemoin(req, TEMOIN_OIDC);
    const attente = brut ? lireSession(brut, cfg.secretSession) : null;
    if (!attente) return reply.code(400).send({ error: 'Connexion expirée : recommence depuis ton compte Nexora.' });
    const c = await configuration();
    const ici = new URL(req.url, cfg.publicUrl);
    let jetons;
    try {
      jetons = await oidc.authorizationCodeGrant(c, ici, { pkceCodeVerifier: attente.u, expectedState: attente.o });
    } catch {
      return reply.code(400).send({ error: 'La connexion Nexora a échoué. Réessaie depuis ton compte.' });
    }
    const sub = jetons.claims()?.sub;
    if (!sub) return reply.code(400).send({ error: 'Identité Nexora incomplète.' });
    const info = await oidc.fetchUserInfo(c, jetons.access_token, sub);
    const organisationId = typeof info.organization_id === 'string' ? info.organization_id : null;
    if (!organisationId) return reply.code(403).send({ error: 'Ton compte Nexora n’a pas d’organisation.' });
    const r = await f(`${cfg.siteUrl}/api/oauth/creative-access`, { headers: { authorization: `Bearer ${jetons.access_token}` } });
    if (!r.ok) {
      const corps = (await r.json().catch(() => ({}))) as { error?: string; message?: string };
      return reply.code(r.status === 403 ? 403 : 502).send({ error: corps.message ?? corps.error ?? 'Accès Nexora Creative refusé par le site.' });
    }
    const a = (await r.json()) as AccesOrganisation;
    acces.set(organisationId, { url: a.url, model: a.model, key: a.key, territory: typeof a.territory === 'string' ? a.territory : null });
    poserTemoin(reply, TEMOIN, signerSession({ o: organisationId, u: sub, t: acces.get(organisationId)!.territory, e: Date.now() + duree }, cfg.secretSession), Math.floor(duree / 1000), securise);
    poserTemoin(reply, TEMOIN_OIDC, '', 0, securise);
    return reply.redirect(attente.t ?? '/');
  });

  app.post('/auth/deconnexion', async (_req, reply) => {
    poserTemoin(reply, TEMOIN, '', 0, securise);
    return { ok: true };
  });
}
