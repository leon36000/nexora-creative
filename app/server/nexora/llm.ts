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
 *  idees       : « Inspire-moi »                              juge        : juge visuel (deux candidats, modèle vision)
 *  producteur  : agent Producteur (boucle d'outils bornée, server/nexora/agent.ts)
 *  monteur     : planification de montage (EditPlan v1, server/nexora/montage/)
 * `prompt`, `intention` et `assistant` restent acceptés (anciens appels).
 */
export type RoleLlm = 'intention' | 'realisation' | 'prompt' | 'juge' | 'assistant' | 'redaction' | 'boost' | 'musique' | 'moderation' | 'publication' | 'idees' | 'producteur' | 'monteur';
export const ROLES_LLM: readonly RoleLlm[] = ['redaction', 'realisation', 'boost', 'musique', 'moderation', 'publication', 'idees', 'juge', 'producteur', 'monteur'];

/** Réglages venus de l'administration du site (modèle par défaut et par rôle) ; ils passent avant l'environnement du poste. */
let reglages: { defaut?: string; roles: Partial<Record<RoleLlm, string>> } = { roles: {} };
export function appliquerReglagesLlm(r: { defaut?: string | null; roles?: Partial<Record<RoleLlm, string>> } | null): void {
  reglages = { defaut: r?.defaut?.trim() || undefined, roles: { ...(r?.roles ?? {}) } };
}
export const reglagesLlmCourants = () => ({ defaut: reglages.defaut ?? null, roles: { ...reglages.roles } });

/** Contenu multimodal (format OpenAI) : texte et images en data URL, pour le juge visuel. */
export type PartieContenu = { type: 'text'; text: string } | { type: 'image_url'; image_url: { url: string } };

export interface AppelOutil {
  id: string;
  nom: string;
  arguments: Record<string, unknown>;
  /** Arguments non JSON renvoyés par le modèle : l'outil répond par une erreur lisible au lieu de planter. */
  illisible?: true;
}

export type MessageLlm =
  | { role: 'system' | 'user'; content: string | PartieContenu[] }
  | { role: 'assistant'; content: string; appels?: AppelOutil[] }
  | { role: 'tool'; content: string; appelId: string };

/** Description d'un outil pour le modèle (paramètres en JSON Schema). */
export interface DefinitionOutil { nom: string; description: string; parametres: Record<string, unknown> }

export interface ReponseOutils { texte: string; appels: AppelOutil[]; jetons: number }

export interface ClientLlm {
  /** Renvoie le texte de la réponse ; `json` demande un objet JSON. */
  completer(role: RoleLlm, messages: MessageLlm[], options?: { json?: boolean; temperature?: number; maxTokens?: number }): Promise<string>;
  /** Un tour d'appel de fonctions (« tools ») : texte éventuel et appels d'outils demandés par le modèle. */
  completerAvecOutils?(role: RoleLlm, messages: MessageLlm[], outils: DefinitionOutil[], options?: { temperature?: number; maxTokens?: number }): Promise<ReponseOutils>;
}

/** Messages au format de l'API (tool_calls, tool_call_id). */
function versApi(messages: MessageLlm[]) {
  return messages.map((m) => {
    if (m.role === 'tool') return { role: 'tool', tool_call_id: m.appelId, content: m.content };
    if (m.role === 'assistant' && m.appels?.length) {
      return { role: 'assistant', content: m.content || null, tool_calls: m.appels.map((a) => ({ id: a.id, type: 'function', function: { name: a.nom, arguments: JSON.stringify(a.arguments) } })) };
    }
    return { role: m.role, content: m.content };
  });
}

export class ErreurLlm extends Error {}

/**
 * Modèle par défaut d'un rôle qui exige une capacité que le modèle général n'a pas. Le juge regarde des images : le modèle
 * par défaut (textuel) ne convient pas, `qwen/qwen3.8-27b` (vision) a été éprouvé sur de vraies prises.
 */
export const MODELES_PAR_DEFAUT_ROLE: Partial<Record<RoleLlm, string>> = { juge: 'qwen/qwen3.8-27b' };

export function modelePour(role: RoleLlm, env: NodeJS.ProcessEnv = process.env): string | null {
  // Ordre : réglage du site pour ce rôle, variable d'environnement du rôle, modèle par défaut du rôle, réglage du site
  // par défaut, variable par défaut.
  return reglages.roles[role]?.trim() || env[`NEXORA_LLM_MODELE_${role.toUpperCase()}`]?.trim() || MODELES_PAR_DEFAUT_ROLE[role] || reglages.defaut || env.NEXORA_LLM_MODELE?.trim() || null;
}

export function clientLlmDepuisEnv(env: NodeJS.ProcessEnv = process.env, f: typeof fetch = fetch): ClientLlm | null {
  const base = env.NEXORA_LLM_BASE_URL?.trim().replace(/\/+$/, '');
  const cle = env.NEXORA_LLM_CLE?.trim();
  if (!base || !cle || !modelePour('prompt', env)) return null;
  const appeler = async (role: RoleLlm, corps: Record<string, unknown>) => {
    const model = modelePour(role, env);
    if (!model) throw new ErreurLlm(`aucun modèle configuré pour le rôle ${role}`);
    const r = await f(`${base}/chat/completions`, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: `Bearer ${cle}` },
      body: JSON.stringify({ model, ...corps }),
      signal: AbortSignal.timeout(180_000),
    });
    if (!r.ok) throw new ErreurLlm(`passerelle LLM : HTTP ${r.status}`);
    return (await r.json()) as {
      choices?: { message?: { content?: string | null; tool_calls?: { id?: string; function?: { name?: string; arguments?: string } }[] } }[];
      usage?: { prompt_tokens?: number; completion_tokens?: number };
    };
  };
  return {
    async completer(role, messages, options = {}) {
      const corps = await appeler(role, {
        messages: versApi(messages),
        temperature: options.temperature ?? 0.4,
        // Sans plafond, la passerelle réserve le maximum du modèle sur les crédits à chaque appel.
        max_tokens: options.maxTokens ?? 8000,
        ...(options.json ? { response_format: { type: 'json_object' } } : {}),
      });
      const texte = corps.choices?.[0]?.message?.content;
      if (typeof texte !== 'string' || !texte.trim()) throw new ErreurLlm('réponse LLM vide');
      return texte;
    },
    async completerAvecOutils(role, messages, outils, options = {}) {
      const corps = await appeler(role, {
        messages: versApi(messages),
        temperature: options.temperature ?? 0.3,
        max_tokens: options.maxTokens ?? 2000,
        ...(outils.length ? { tools: outils.map((o) => ({ type: 'function', function: { name: o.nom, description: o.description, parameters: o.parametres } })), tool_choice: 'auto' } : {}),
      });
      const m = corps.choices?.[0]?.message;
      const appels: AppelOutil[] = (m?.tool_calls ?? []).map((t, i) => {
        const id = t.id || `appel_${i}`;
        const nom = String(t.function?.name ?? '');
        try {
          const a = JSON.parse(t.function?.arguments || '{}');
          return { id, nom, arguments: a && typeof a === 'object' && !Array.isArray(a) ? a : {} };
        } catch {
          return { id, nom, arguments: {}, illisible: true as const };
        }
      });
      return { texte: typeof m?.content === 'string' ? m.content : '', appels, jetons: (corps.usage?.prompt_tokens ?? 0) + (corps.usage?.completion_tokens ?? 0) };
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

