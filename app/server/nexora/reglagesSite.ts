/**
 * Réglages de Nexora Creative venus de l'administration du site (module Directus « Nexora Creative ») : modèle LLM par
 * rôle et moteurs de génération (locaux ou cloud). Lus toutes les minutes avec le jeton du SERVICE (distinct du jeton
 * d'administration) ; tant que rien n'est configuré, ou si le site ne répond pas, l'environnement du poste reste en place.
 * Contrat : GET {site}/api/creative/config → { configured: false } | { configured: true, llm, engines[] }.
 */
import { appliquerReglagesLlm, type RoleLlm } from './llm.js';
import { appliquerMoteurs, type MoteurGpu, retablirMoteursEnv } from '../engine.js';

export interface ReglagesSite {
  configured: true;
  updatedAt: string;
  llm: { default: string | null; roles: Partial<Record<RoleLlm, string>> };
  engines: { id: string; label: string; kind: 'local' | 'cloud'; baseUrl: string; comfyUrl: string; recipes: string[]; apiKey?: string; keyError?: string }[];
}

export async function lireReglagesSite(siteUrl: string, jeton: string, f: typeof fetch = fetch): Promise<ReglagesSite | { configured: false } | null> {
  try {
    const r = await f(`${siteUrl.replace(/\/+$/, '')}/api/creative/config`, { headers: { authorization: `Bearer ${jeton}` }, signal: AbortSignal.timeout(10_000) });
    if (!r.ok) return null;
    const c = (await r.json()) as { configured?: boolean };
    return c.configured === true ? (c as ReglagesSite) : { configured: false };
  } catch {
    return null;
  }
}

/** Convertit et applique. Un moteur cloud dont la clé est illisible est ignoré (et signalé) plutôt que servi sans clé. */
export function appliquerReglagesSite(r: ReglagesSite | { configured: false }, journal: (m: string) => void = () => {}): { moteurs: number; ignores: string[] } {
  if (!r.configured) {
    appliquerReglagesLlm(null);
    retablirMoteursEnv();
    return { moteurs: 0, ignores: [] };
  }
  appliquerReglagesLlm({ defaut: r.llm.default, roles: r.llm.roles });
  const ignores: string[] = [];
  const liste: MoteurGpu[] = [];
  for (const e of r.engines) {
    if (e.kind === 'cloud' && !e.apiKey) {
      ignores.push(e.id);
      journal(`moteur cloud « ${e.id} » ignoré : clé indisponible (${e.keyError ?? 'absente'})`);
      continue;
    }
    liste.push({ id: e.id, nom: e.label, comfyUrl: e.comfyUrl.replace(/\/+$/, ''), baseUrl: e.baseUrl.replace(/\/+$/, ''), recettes: e.recipes, ...(e.apiKey ? { cle: e.apiKey } : {}) });
  }
  appliquerMoteurs(liste);
  return { moteurs: liste.length, ignores };
}

export function demarrerLectureReglages(opts: { siteUrl: string; jeton: string; periodeMs?: number; journal: (m: string) => void }): () => void {
  let derniere = '';
  const tour = async () => {
    const r = await lireReglagesSite(opts.siteUrl, opts.jeton);
    if (!r) return; // site injoignable : on garde les derniers réglages appliqués
    const signature = JSON.stringify(r);
    if (signature === derniere) return;
    derniere = signature;
    const res = appliquerReglagesSite(r, opts.journal);
    opts.journal(r.configured ? `réglages du site appliqués : ${res.moteurs} moteur(s)${res.ignores.length ? `, ${res.ignores.length} ignoré(s)` : ''}` : 'site : rien de configuré, environnement du poste conservé');
  };
  void tour();
  const t = setInterval(() => void tour(), opts.periodeMs ?? 60_000);
  return () => clearInterval(t);
}
