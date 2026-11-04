/**
 * Les trois paliers du monteur de Nexora Creative : Éco, Équilibré, Expert. Chaque palier = un modèle, un fournisseur,
 * un prix de liste et les manies du modèle (raisonnement, mode JSON, jetons maximum, reprises), réunis dans UNE table
 * d'adaptateurs : rien de propre à un modèle ne vit ailleurs. Les trois modèles sont puissants ; les paliers servent
 * au coût et à l'escalade (le moins cher d'abord), pas à séparer des faibles d'un fort.
 *
 * Clés (jamais journalisées, lues dans l'environnement du serveur) :
 *   NEXORA_LLM_CLE_DEEPINFRA   palier Éco         (DeepInfra)
 *   NEXORA_LLM_CLE_OPENROUTER  paliers Équilibré et Expert (OpenRouter)
 */
import { type ClientLlm, type MessageLlm, type DefinitionOutil, type RoleLlm, ErreurLlm, type AppelOutil, versApi } from './llm.js';

export const PALIERS = ['eco', 'equilibre', 'expert'] as const;
export type Palier = (typeof PALIERS)[number];
export const LIBELLES_PALIER: Record<Palier, string> = { eco: 'Éco', equilibre: 'Équilibré', expert: 'Expert' };
export const estPalier = (v: unknown): v is Palier => typeof v === 'string' && (PALIERS as readonly string[]).includes(v);

/** Usage brut renvoyé par le fournisseur pour UN appel. */
export interface UsageBrut { entree: number; sortie: number; raisonnement: number; coutFournisseurUsd: number | null }

export interface AdapterModele {
  palier: Palier;
  modele: string;
  fournisseur: 'deepinfra' | 'openrouter';
  url: string;
  envCle: string;
  /** Prix de liste du fournisseur, USD par million de jetons (le raisonnement se facture comme la sortie). */
  prixEntreeUsdM: number;
  prixSortieUsdM: number;
  /** Point de terminaison réellement utilisé (étiquette de la mesure). */
  endpoint: string;
  /** Champs à ajouter au corps de la requête (raisonnement, routage, comptage d'usage). */
  corps: (o: { json: boolean }) => Record<string, unknown>;
  /** Plancher de jetons de sortie : le raisonnement mange le plafond avant la réponse. */
  maxSortieMin: number;
  /** Repli explicite (Expert seulement) : même modèle, point de terminaison standard au double du prix. */
  repli?: { endpoint: string; prixEntreeUsdM: number; prixSortieUsdM: number; corps: () => Record<string, unknown> };
}

const OR = 'https://openrouter.ai/api/v1';
export const ADAPTATEURS: Record<Palier, AdapterModele> = {
  // DeepSeek V4.1 Flash 1017 (DeepInfra) : 0,20 $ entrée / 0,60 $ sortie par M. Raisonne par défaut : `reasoning_effort: none`.
  eco: {
    palier: 'eco', modele: 'deepseek-ai/DeepSeek-V4.1-Flash-1017', fournisseur: 'deepinfra', url: 'https://api.deepinfra.com/v1/openai', envCle: 'NEXORA_LLM_CLE_DEEPINFRA',
    prixEntreeUsdM: 0.2, prixSortieUsdM: 0.6, endpoint: 'deepinfra', maxSortieMin: 2000,
    corps: () => ({ reasoning_effort: 'none' }),
  },
  // Muse Spark 1.3 Contributor (OpenRouter) : 0,10 $ / 0,20 $ par M. Raisonnement obligatoire : on le met au minimum.
  equilibre: {
    palier: 'equilibre', modele: 'meta/muse-spark-1.3-contributor', fournisseur: 'openrouter', url: OR, envCle: 'NEXORA_LLM_CLE_OPENROUTER',
    prixEntreeUsdM: 0.1, prixSortieUsdM: 0.2, endpoint: 'openrouter', maxSortieMin: 6000,
    corps: () => ({ reasoning: { effort: 'minimal' }, usage: { include: true } }),
  },
  // Gemini 4 Argon « Flex » (OpenRouter, point de terminaison google-ai-studio/flex) : 1 $ / 5 $ par M, file d'attente
  // possible. Repli explicite et plafonné sur le point standard (google-vertex/global) à 2 $ / 10 $.
  expert: {
    palier: 'expert', modele: 'google/gemini-4-argon', fournisseur: 'openrouter', url: OR, envCle: 'NEXORA_LLM_CLE_OPENROUTER',
    prixEntreeUsdM: 1, prixSortieUsdM: 5, endpoint: 'google-ai-studio/flex', maxSortieMin: 4000,
    corps: () => ({ reasoning: { effort: 'low' }, usage: { include: true }, provider: { order: ['google-ai-studio/flex'], allow_fallbacks: false } }),
    repli: { endpoint: 'google-vertex/global', prixEntreeUsdM: 2, prixSortieUsdM: 10, corps: () => ({ reasoning: { effort: 'low' }, usage: { include: true }, provider: { order: ['google-vertex/global'], allow_fallbacks: false } }) },
  },
};

/** Coût de liste d'un usage (USD). */
export function coutListeUsd(u: Pick<UsageBrut, 'entree' | 'sortie'>, a: Pick<AdapterModele, 'prixEntreeUsdM' | 'prixSortieUsdM'>): number {
  return (u.entree * a.prixEntreeUsdM + u.sortie * a.prixSortieUsdM) / 1e6;
}

/** Lit le bloc `usage` d'une réponse (formats DeepInfra et OpenRouter). `sortie` inclut déjà le raisonnement. */
export function lireUsage(usage: any): UsageBrut {
  const cout = typeof usage?.cost === 'number' ? usage.cost : typeof usage?.estimated_cost === 'number' ? usage.estimated_cost : null;
  return {
    entree: Number(usage?.prompt_tokens ?? 0) || 0,
    sortie: Number(usage?.completion_tokens ?? 0) || 0,
    raisonnement: Number(usage?.completion_tokens_details?.reasoning_tokens ?? 0) || 0,
    coutFournisseurUsd: cout,
  };
}

/** Un appel mesuré : ce qui part au grand livre. */
export interface AppelMesure {
  role: RoleLlm; palier: Palier | 'direct'; modele: string; endpoint: string; usage: UsageBrut; coutUsd: number;
  /** « fournisseur » : coût rapporté par le fournisseur ; « tarif » : calculé au prix de liste. */
  source: 'fournisseur' | 'tarif'; ms: number; repli: boolean;
}

/** Surveillant d'un run : reçoit chaque appel et peut refuser le suivant (plafond dur). */
export interface Surveillant { avant(role: RoleLlm, palier: Palier): void; apres(a: AppelMesure): void }

export interface OptionsClientPalier {
  surveillant?: Surveillant;
  /** Autorise le repli payant (point de terminaison standard) quand Flex est saturé. Défaut : non. */
  autoriserRepli?: boolean;
  tentatives?: number;
  f?: typeof fetch;
  /** Attente entre deux tentatives, remplaçable par les tests. */
  attendre?: (ms: number) => Promise<void>;
  env?: NodeJS.ProcessEnv;
}

const dormir = (ms: number) => new Promise<void>((ok) => setTimeout(ok, ms));
const transitoire = (statut: number) => statut === 429 || statut === 408 || statut >= 500;

/** Client LLM d'un palier : adaptateur du modèle, reprises avec attente, mesure de chaque appel. */
export function clientPalier(palier: Palier, o: OptionsClientPalier = {}): ClientLlm {
  const a = ADAPTATEURS[palier];
  const env = o.env ?? process.env;
  const f = o.f ?? fetch;
  const attendre = o.attendre ?? dormir;
  const tentatives = o.tentatives ?? 3;

  const appeler = async (role: RoleLlm, corps: Record<string, unknown>) => {
    const cle = env[a.envCle]?.trim();
    if (!cle) throw new ErreurLlm(`clé ${a.envCle} absente : palier ${LIBELLES_PALIER[palier]} indisponible`);
    o.surveillant?.avant(role, palier);
    let repli = false;
    for (let essai = 0; ; essai++) {
      const extra = repli && a.repli ? a.repli.corps() : a.corps({ json: !!corps.response_format });
      const t0 = Date.now();
      let r: Response | null = null;
      try {
        r = await f(`${a.url}/chat/completions`, {
          method: 'POST', headers: { 'content-type': 'application/json', authorization: `Bearer ${cle}` },
          body: JSON.stringify({ model: a.modele, ...corps, ...extra }), signal: AbortSignal.timeout(240_000),
        });
      } catch { /* réseau : traité comme transitoire */ }
      if (r?.ok) {
        const j = (await r.json()) as { choices?: { message?: any; finish_reason?: string }[]; usage?: unknown };
        const u = lireUsage(j.usage);
        const prix = repli && a.repli ? a.repli : a;
        const liste = coutListeUsd(u, prix);
        o.surveillant?.apres({
          role, palier, modele: a.modele, endpoint: repli && a.repli ? a.repli.endpoint : a.endpoint, usage: u,
          coutUsd: u.coutFournisseurUsd ?? liste, source: u.coutFournisseurUsd !== null ? 'fournisseur' : 'tarif', ms: Date.now() - t0, repli,
        });
        return j;
      }
      const statut = r?.status ?? 0;
      if (r && !transitoire(statut)) throw new ErreurLlm(`${LIBELLES_PALIER[palier]} (${a.endpoint}) : HTTP ${statut}`);
      if (essai + 1 >= tentatives) {
        // Flex saturé : repli explicite sur le point de terminaison standard, une seule fois, si autorisé.
        if (a.repli && o.autoriserRepli && !repli) { repli = true; essai = -1; continue; }
        throw new ErreurLlm(`${LIBELLES_PALIER[palier]} (${a.endpoint}) : ${statut ? `HTTP ${statut}` : 'réseau'} après ${tentatives} tentatives`);
      }
      await attendre(Math.min(20_000, 1500 * 2 ** essai));
    }
  };

  return {
    async completer(role, messages: MessageLlm[], options = {}) {
      const j = await appeler(role, {
        messages: versApi(messages), temperature: options.temperature ?? 0.4,
        max_tokens: Math.max(options.maxTokens ?? 8000, a.maxSortieMin),
        ...(options.json ? { response_format: { type: 'json_object' } } : {}),
      });
      const c = j.choices?.[0];
      const texte = c?.message?.content;
      if (typeof texte !== 'string' || !texte.trim()) throw new ErreurLlm(c?.finish_reason === 'length' ? 'réponse tronquée (jetons de sortie épuisés)' : 'réponse LLM vide');
      return texte;
    },
    async completerAvecOutils(role, messages, outils: DefinitionOutil[], options = {}) {
      const j = await appeler(role, {
        messages: versApi(messages), temperature: options.temperature ?? 0.3, max_tokens: Math.max(options.maxTokens ?? 2000, a.maxSortieMin),
        ...(outils.length ? { tools: outils.map((x) => ({ type: 'function', function: { name: x.nom, description: x.description, parameters: x.parametres } })), tool_choice: 'auto' } : {}),
      });
      const m = j.choices?.[0]?.message;
      const appels: AppelOutil[] = (m?.tool_calls ?? []).map((t: any, i: number) => {
        const id = t.id || `appel_${i}`;
        const nom = String(t.function?.name ?? '');
        try {
          const x = JSON.parse(t.function?.arguments || '{}');
          return { id, nom, arguments: x && typeof x === 'object' && !Array.isArray(x) ? x : {} };
        } catch { return { id, nom, arguments: {}, illisible: true as const }; }
      });
      const u = lireUsage((j as any).usage);
      return { texte: typeof m?.content === 'string' ? m.content : '', appels, jetons: u.entree + u.sortie };
    },
  };
}

/** Palier disponible sur ce serveur : sa clé est présente. */
export const palierDisponible = (p: Palier, env: NodeJS.ProcessEnv = process.env) => !!env[ADAPTATEURS[p].envCle]?.trim();
