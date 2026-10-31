/**
 * Témoin de session de Nexora Creative : charge JSON en base64url + HMAC-SHA256, avec échéance. Il ne porte que des
 * identifiants (organisation, utilisateur, territoire) ; la clé de passerelle de l'organisation reste côté serveur.
 */
import { createHmac, timingSafeEqual } from 'node:crypto';

export interface ChargeSession {
  /** Organisation Nexora. */
  o: string;
  /** Utilisateur (sub OIDC). */
  u: string;
  /** Territoire de l'organisation (ISO 3166-1 alpha-2) ou null. */
  t: string | null;
  /** Échéance, en millisecondes depuis l'époque. */
  e: number;
}

function signature(corps: string, secret: string): string {
  if (secret.length < 32) throw new Error('NEXORA_SESSION_SECRET doit compter au moins 32 caractères');
  return createHmac('sha256', secret).update(corps).digest('base64url');
}

export function signerSession(c: ChargeSession, secret: string): string {
  const corps = Buffer.from(JSON.stringify(c)).toString('base64url');
  return `${corps}.${signature(corps, secret)}`;
}

export function lireSession(valeur: string, secret: string, maintenant = Date.now()): ChargeSession | null {
  const morceaux = valeur.split('.');
  if (morceaux.length !== 2 || !morceaux[0] || !morceaux[1]) return null;
  const attendue = Buffer.from(signature(morceaux[0], secret));
  const recue = Buffer.from(morceaux[1]);
  if (attendue.length !== recue.length || !timingSafeEqual(attendue, recue)) return null;
  try {
    const c = JSON.parse(Buffer.from(morceaux[0], 'base64url').toString('utf8')) as ChargeSession;
    if (typeof c.o !== 'string' || typeof c.u !== 'string' || typeof c.e !== 'number' || c.e < maintenant) return null;
    return { o: c.o, u: c.u, t: typeof c.t === 'string' ? c.t : null, e: c.e };
  } catch {
    return null;
  }
}
