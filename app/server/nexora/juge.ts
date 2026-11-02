/**
 * Juge visuel (feuille de route R8) : deux prises d'un même plan, un modèle vision (rôle LLM « juge », réglable depuis
 * l'administration) choisit la meilleure et le dit en une phrase. Le contrôle qualité déterministe (controle.ts) passe
 * d'abord : une prise noire, figée ou muette n'est jamais retenue, quoi que dise le juge. Si le juge ne répond pas, le
 * code garde la première prise valide : un juge en panne ne bloque jamais un film.
 * Le juge voit une planche par prise (trois images : début, milieu, fin), assez pour l'identité, les artefacts, le
 * texte parasite et le mouvement, pour quelques centimes de jetons.
 */
import { execFile } from 'node:child_process';
import { readFile, rm } from 'node:fs/promises';
import { avecCompetences } from './competences.js';
import { type ClientLlm, lireJson, reglagesLlmCourants } from './llm.js';

export interface VerdictJuge { gagnant: 'A' | 'B'; raison: string; notes: { A: number; B: number } }
export interface ChoixCandidat { take: number; source: 'juge' | 'controle' | 'repli'; raison: string }

const note = (v: unknown) => Math.max(0, Math.min(10, Math.round(Number(v) || 0)));

export function lireVerdict(texte: string): VerdictJuge | null {
  try {
    const o = lireJson<Record<string, any>>(texte);
    const g = String(o.gagnant ?? '').trim().toUpperCase();
    if (g !== 'A' && g !== 'B') return null;
    return { gagnant: g, raison: String(o.raison ?? '').trim().slice(0, 200), notes: { A: note(o.notes?.A), B: note(o.notes?.B) } };
  } catch {
    return null;
  }
}

/** Décision : contrôle qualité d'abord, puis le juge, puis la première prise. */
export function choisirCandidat(c: { take: number; controleOk: boolean }[], v: VerdictJuge | null): ChoixCandidat {
  const valides = c.filter((x) => x.controleOk);
  if (valides.length === 1 && c.length > 1) return { take: valides[0].take, source: 'controle', raison: `Seule la prise ${valides[0].take} passe le contrôle qualité.` };
  if (valides.length >= 2 && v) return { take: (v.gagnant === 'A' ? c[0] : c[1]).take, source: 'juge', raison: v.raison || 'Choisie par le juge visuel.' };
  return { take: (valides[0] ?? c[0]).take, source: 'repli', raison: 'Juge indisponible : première prise valide gardée.' };
}

/** Le juge n'est proposé que si un modèle (vision) est réglé pour son rôle : le modèle par défaut est textuel. */
export function jugeDisponible(env: NodeJS.ProcessEnv = process.env): boolean {
  return !!(reglagesLlmCourants().roles.juge?.trim() || env.NEXORA_LLM_MODELE_JUGE?.trim());
}

export async function jugerCandidats(llm: ClientLlm | null, description: string, planches: [string, string] | string[]): Promise<VerdictJuge | null> {
  if (!llm) return null;
  // Deux essais : un modèle vision qui raisonne rend parfois une réponse vide ou tronquée.
  for (let essai = 0; essai < 2; essai++) {
    const v = await unAppel(llm, description, planches);
    if (v) return v;
  }
  return null;
}

async function unAppel(llm: ClientLlm, description: string, planches: string[]): Promise<VerdictJuge | null> {
  try {
    const brut = await llm.completer('juge', [
      { role: 'system', content: avecCompetences('juge', 'You are the visual judge of Nexora Creative.') },
      { role: 'user', content: [
        { type: 'text', text: `Shot description: ${description.slice(0, 1500)}\nCandidate A:` },
        { type: 'image_url', image_url: { url: planches[0] } },
        { type: 'text', text: 'Candidate B:' },
        { type: 'image_url', image_url: { url: planches[1] } },
      ] },
    ], { json: true, temperature: 0, maxTokens: 2000 });
    return lireVerdict(brut);
  } catch {
    return null;
  }
}

/** Arguments ffmpeg : trois images réparties sur la durée, réduites et posées côte à côte (JPEG). */
export function argsPlanche(fichier: string, sortie: string, dureeS: number): string[] {
  const d = Math.max(0.5, Math.round(dureeS * 100) / 100);
  return ['-y', '-v', 'error', '-i', fichier, '-vf', `fps=3/${d},scale=384:-2,tile=3x1`, '-frames:v', '1', '-q:v', '5', sortie];
}

/** Planche d'une prise en data URL (pour le message multimodal). */
export async function plancheDataUrl(ffmpeg: string, fichier: string, dureeS: number, sortie: string): Promise<string> {
  await new Promise<void>((ok, ko) => execFile(ffmpeg, argsPlanche(fichier, sortie, dureeS), (e, _o, err) => (e ? ko(new Error(String(err).slice(-200))) : ok())));
  try {
    return `data:image/jpeg;base64,${(await readFile(sortie)).toString('base64')}`;
  } finally {
    await rm(sortie, { force: true });
  }
}
