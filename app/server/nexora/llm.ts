/**
 * Client LLM de Nexora Creative : une API compatible OpenAI (en production la passerelle Nexora `/v1`, qui débite les
 * crédits et applique le Privacy Router ; en développement un LiteLLM). Le modèle se choisit par rôle, jamais en dur.
 *
 * NEXORA_LLM_BASE_URL   ex. https://nexora.example/v1 ou http://127.0.0.1:4400/v1
 * NEXORA_LLM_CLE        clé de l'organisation (jamais journalisée)
 * NEXORA_LLM_MODELE     modèle par défaut ; NEXORA_LLM_MODELE_<ROLE> le remplace pour un rôle (ex. NEXORA_LLM_MODELE_JUGE)
 */

/**
 * Rôles : chacun peut recevoir son propre modèle (local ou cloud) depuis l'administration du site.
 *  redaction   : prompts H3 et image (le plus exigeant)      realisation : découpage d'un film (Director)
 *  boost       : « Booster ma phrase »                        musique     : description de la bande originale
 *  moderation  : garde-fou avant rendu (licence H3, V.5)      publication : titres et textes pour les réseaux
 *  idees       : « Inspire-moi »                              juge        : contrôle visuel (réservé)
 * `prompt`, `intention` et `assistant` restent acceptés (anciens appels).
 */
export type RoleLlm = 'intention' | 'realisation' | 'prompt' | 'juge' | 'assistant' | 'redaction' | 'boost' | 'musique' | 'moderation' | 'publication' | 'idees';
export const ROLES_LLM: readonly RoleLlm[] = ['redaction', 'realisation', 'boost', 'musique', 'moderation', 'publication', 'idees', 'juge'];

/** Réglages venus de l'administration du site (modèle par défaut et par rôle) ; ils passent avant l'environnement du poste. */
let reglages: { defaut?: string; roles: Partial<Record<RoleLlm, string>> } = { roles: {} };
export function appliquerReglagesLlm(r: { defaut?: string | null; roles?: Partial<Record<RoleLlm, string>> } | null): void {
  reglages = { defaut: r?.defaut?.trim() || undefined, roles: { ...(r?.roles ?? {}) } };
}
export const reglagesLlmCourants = () => ({ defaut: reglages.defaut ?? null, roles: { ...reglages.roles } });

export interface MessageLlm {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ClientLlm {
  /** Renvoie le texte de la réponse ; `json` demande un objet JSON. */
  completer(role: RoleLlm, messages: MessageLlm[], options?: { json?: boolean; temperature?: number }): Promise<string>;
}

export class ErreurLlm extends Error {}

export function modelePour(role: RoleLlm, env: NodeJS.ProcessEnv = process.env): string | null {
  // Ordre : réglage du site pour ce rôle, variable d'environnement du rôle, réglage du site par défaut, variable par défaut.
  return reglages.roles[role]?.trim() || env[`NEXORA_LLM_MODELE_${role.toUpperCase()}`]?.trim() || reglages.defaut || env.NEXORA_LLM_MODELE?.trim() || null;
}

export function clientLlmDepuisEnv(env: NodeJS.ProcessEnv = process.env, f: typeof fetch = fetch): ClientLlm | null {
  const base = env.NEXORA_LLM_BASE_URL?.trim().replace(/\/+$/, '');
  const cle = env.NEXORA_LLM_CLE?.trim();
  if (!base || !cle || !modelePour('prompt', env)) return null;
  return {
    async completer(role, messages, options = {}) {
      const model = modelePour(role, env);
      if (!model) throw new ErreurLlm(`aucun modèle configuré pour le rôle ${role}`);
      const r = await f(`${base}/chat/completions`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: `Bearer ${cle}` },
        body: JSON.stringify({
          model,
          messages,
          temperature: options.temperature ?? 0.4,
          ...(options.json ? { response_format: { type: 'json_object' } } : {}),
        }),
        signal: AbortSignal.timeout(180_000),
      });
      if (!r.ok) throw new ErreurLlm(`passerelle LLM : HTTP ${r.status}`);
      const corps = (await r.json()) as { choices?: { message?: { content?: string } }[] };
      const texte = corps.choices?.[0]?.message?.content;
      if (typeof texte !== 'string' || !texte.trim()) throw new ErreurLlm('réponse LLM vide');
      return texte;
    },
  };
}

/** Extrait le premier objet JSON d'une réponse (certains modèles l'entourent de ```json …```). */
export function lireJson<T>(texte: string): T {
  const debut = texte.indexOf('{');
  const fin = texte.lastIndexOf('}');
  if (debut < 0 || fin <= debut) throw new ErreurLlm('pas d’objet JSON dans la réponse');
  return JSON.parse(texte.slice(debut, fin + 1)) as T;
}

/**
 * Client LLM de la requête en cours : avec une session Nexora, la passerelle et la clé de l'organisation (ses crédits,
 * sa politique de confidentialité) ; sinon la configuration du poste (développement).
 */
export function clientLlmCourant(
  compte: { organisationId: string } | null,
  acces: (org: string) => { url: string; model: string; key: string } | undefined,
  env: NodeJS.ProcessEnv = process.env,
): ClientLlm | null {
  const a = compte ? acces(compte.organisationId) : undefined;
  if (!a) return compte ? null : clientLlmDepuisEnv(env);
  return clientLlmDepuisEnv({ ...env, NEXORA_LLM_BASE_URL: a.url, NEXORA_LLM_CLE: a.key, NEXORA_LLM_MODELE: a.model });
}

