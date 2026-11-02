/**
 * `critique` : les métriques en code d'abord (gratuites), puis le juge visuel (rôle « juge ») sur une planche contact
 * quand des images existent. Le juge ne pèse que 30 % et ne casse jamais la porte (recherche/14 §5, note 05).
 * Rend des écarts typés avec un indice : c'est la matière première de `revise`.
 */
import { avecCompetences } from '../competences.js';
import { type ClientLlm, lireJson } from '../llm.js';
import { type Ecart, type RapportMetriques, mesurer } from './metriques.js';
import type { Brief } from './types.js';

export interface NotesJuge { accroche: number; coherence: number; lisibilite: number; finition: number; remarque: string; moyenne: number }
export interface Critique {
  metriques: RapportMetriques;
  juge: NotesJuge | null;
  /** 0-1 : porte × (0,7 × métriques + 0,3 × juge/10) ; sans juge, les métriques seules. */
  composite: number;
  ecarts: Ecart[];
  /** Vue texte compacte pour le modèle. */
  resume: string;
}

const n10 = (v: unknown) => Math.max(0, Math.min(10, Number(v) || 0));

export function lireNotesJuge(texte: string): NotesJuge | null {
  try {
    const o = lireJson<Record<string, unknown>>(texte);
    const t = { accroche: n10(o.accroche), coherence: n10(o.coherence), lisibilite: n10(o.lisibilite), finition: n10(o.finition) };
    return { ...t, remarque: String(o.remarque ?? '').slice(0, 240), moyenne: (t.accroche + t.coherence + t.lisibilite + t.finition) / 4 };
  } catch {
    return null;
  }
}

export function composite(m: RapportMetriques, juge: NotesJuge | null): number {
  if (!m.porte) return 0;
  return Math.round((juge ? 0.7 * m.composite + 0.3 * (juge.moyenne / 10) : m.composite) * 10000) / 10000;
}

export function resumeCritique(c: Pick<Critique, 'metriques' | 'juge' | 'composite' | 'ecarts'>): string {
  const m = c.metriques;
  if (!m.porte) return `PORTE ÉCHOUÉE (plan invalide) :\n${m.ecarts.slice(0, 8).map((e) => `- ${e.message} → ${e.indice}`).join('\n')}`;
  const s = (Object.entries(m.metriques) as [string, { score: number }][]).map(([k, v]) => `${k} ${v.score.toFixed(2)}`).join(', ');
  return [`score ${c.composite.toFixed(2)} (${s}${c.juge ? `, juge ${c.juge.moyenne.toFixed(1)}/10` : ''}); crédits ${m.credits}`,
    ...c.ecarts.slice(0, 8).map((e) => `- [${e.gravite}] ${e.clip ? `${e.clip}: ` : ''}${e.message} → ${e.indice}`),
    ...(c.juge?.remarque ? [`juge: ${c.juge.remarque}`] : [])].join('\n');
}

export async function critiquer(plan: unknown, brief: Brief, o: { llm?: ClientLlm | null; planche?: string } = {}): Promise<Critique> {
  const metriques = mesurer(plan, brief);
  let juge: NotesJuge | null = null;
  if (metriques.porte && o.llm && o.planche) {
    for (let essai = 0; essai < 2 && !juge; essai++) {
      try {
        const brut = await o.llm.completer('juge', [
          { role: 'system', content: avecCompetences('juge', 'You are the editing judge of Nexora Creative. Rate the contact sheet of a video edit 0-10 on: accroche (hook), coherence, lisibilite (text legibility), finition (polish). Reply with JSON {"accroche":n,"coherence":n,"lisibilite":n,"finition":n,"remarque":"one sentence in French"}.') },
          { role: 'user', content: [{ type: 'text', text: `Brief: ${brief.enonce}\nMeasured: ${resumeCritique({ metriques, juge: null, composite: metriques.composite, ecarts: metriques.ecarts })}` }, { type: 'image_url', image_url: { url: o.planche } }] },
        ], { json: true, temperature: 0, maxTokens: 1500 });
        juge = lireNotesJuge(brut);
      } catch { /* un juge en panne ne bloque jamais le montage */ }
    }
  }
  const base = { metriques, juge, composite: composite(metriques, juge), ecarts: metriques.ecarts };
  return { ...base, resume: resumeCritique(base) };
}
