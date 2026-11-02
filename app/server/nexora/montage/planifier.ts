/**
 * `plan_edit` / `revise` côté LLM : le modèle propose un EditPlan (ou des rustines), le code dispose.
 * Garde-fous câblés ici, jamais dans le prompt : le plan est validé (Zod + invariants) ; au plus `reparations`
 * réparations avec le message du validateur et l'indice de fonction (AMD, niveau fonction) ; au plus `tours` tours
 * critique → rustines, et une rustine n'est gardée que si le score en code monte ; nombre d'appels plafonné ;
 * à toute exception, plan invalide ou plafond atteint : repli sur `montageAuto` (le plancher ne dépend pas du modèle).
 */
import { avecCompetences } from '../competences.js';
import { type ClientLlm, lireJson } from '../llm.js';
import { montageAuto } from './auto.js';
import { critiquer, composite } from './critique.js';
import { type EditPlan, type RapportValidation, framesDe, messageErreurs, validerEditPlan } from './editplan.js';
import { blocSavoir, indicesFonction, recupererSavoir } from './memoire.js';
import { mesurer } from './metriques.js';
import { reviser } from './revise.js';
import type { Brief } from './types.js';

export interface OptionsPlan {
  /** Recette + exemplaire top-1 injectés (niveaux workflow et sous-tâche). */
  memoire?: boolean;
  /** Réparations après refus du validateur (avec indices de fonction). 0 = aucune. */
  reparations?: number;
  /** Tours critique → rustines (le code garde la rustine seulement si le score monte). */
  tours?: number;
  /** Exemplaires interdits (anti-fuite du banc : l'exemplaire du brief courant). */
  exclure?: string[];
  maxAppels?: number;
  temperature?: number;
  maxTokens?: number;
}

export interface ResultatPlan {
  plan: EditPlan;
  source: 'llm' | 'repli';
  /** Raisons du repli ou notes de parcours (diagnostic, jamais montré au modèle). */
  notes: string[];
  appels: number;
  valideDuPremierCoup: boolean;
  /** Plan brut du modèle avant réparation (pour le registre du banc). */
  brutes: string[];
  versionsSavoir: string[];
}

/** Vue texte du brief et de l'inventaire pour le modèle : identifiants, durées en images, grille de la musique. */
export function vueBrief(b: Brief): string {
  const f = (s: number) => framesDe(s, b.fps);
  const l: string[] = [
    `BRIEF : ${b.enonce}`,
    `genre ${b.genre}, format ${b.format}, fps ${b.fps}, durée cible ${b.duree_cible_s} s = ${f(b.duree_cible_s)} images (durée totale du plan entre ${Math.round(f(b.duree_cible_s) * 0.96)} et ${Math.round(f(b.duree_cible_s) * 1.04)} images).`,
  ];
  if (b.textes_imposes.length) l.push(`TEXTES IMPOSÉS (mot pour mot, un texte chacun) : ${b.textes_imposes.map((t) => JSON.stringify(t)).join(' ; ')}`);
  l.push('INVENTAIRE (sources vidéo, durée en images) :');
  for (const c of b.clips) l.push(`- ${c.id}: ${f(c.duree_s)} images${c.description ? ` — ${c.description}` : ''}${c.coupes_s?.length ? ` ; coupes internes aux images ${c.coupes_s.map(f).join(',')}` : ''}${c.mots?.length ? ` ; paroles (images) ${c.mots.map(([x, y]) => `${f(x)}-${f(y)}`).join(' ')}` : ''}`);
  if (b.musique) {
    const m = b.musique;
    l.push(`MUSIQUE ${m.id} (source audio, ${f(m.duree_s)} images, ${m.bpm} BPM). Temps forts en images : ${m.battues_s.filter((t) => t < b.duree_cible_s + 0.5).map(f).join(',')}`);
    l.push(`Énergie 0-9 par demi-seconde : ${m.energie.slice(0, Math.ceil(b.duree_cible_s * 2)).map((v) => Math.round(v * 9)).join('')}`);
  }
  if (b.voix) l.push(`VOIX OFF ${b.voix.id} (source audio, ${f(b.voix.duree_s)} images)${b.voix.mots?.length ? ` ; mots (images) ${b.voix.mots.map(([x, y]) => `${f(x)}-${f(y)}`).join(' ')}` : ''} : à poser avec ducking.`);
  l.push('Réponds par UN SEUL objet JSON EditPlan v1.');
  return l.join('\n');
}

const SYSTEME = 'Tu es le monteur de Nexora Creative. Tu réponds uniquement par du JSON.';

export async function planifierMontage(llm: ClientLlm | null, b: Brief, o: OptionsPlan = {}): Promise<ResultatPlan> {
  const notes: string[] = [];
  const brutes: string[] = [];
  const savoir = o.memoire ? recupererSavoir(b, { exclure: o.exclure }) : { recette: null, segment: null, versions: [] as string[] };
  const ctx = { inventaire: Object.fromEntries([...b.clips.map((c) => [c.id, { duree_s: c.duree_s }] as const), ...(b.musique ? [[b.musique.id, { duree_s: b.musique.duree_s }] as const] : []), ...(b.voix ? [[b.voix.id, { duree_s: b.voix.duree_s }] as const] : [])]), duree_cible_s: b.duree_cible_s };
  const repli = (raison: string, appels: number, premier = false): ResultatPlan => ({ plan: montageAuto(b), source: 'repli', notes: [...notes, raison], appels, valideDuPremierCoup: premier, brutes, versionsSavoir: savoir.versions });
  if (!llm) return repli('aucun LLM branché', 0);

  const messages: { role: 'system' | 'user' | 'assistant'; content: string }[] = [
    { role: 'system', content: avecCompetences('monteur', SYSTEME) },
    { role: 'user', content: `${savoir.recette || savoir.segment ? `${blocSavoir(savoir)}\n\n` : ''}${vueBrief(b)}` },
  ];
  let appels = 0;
  const max = o.maxAppels ?? 6;
  const appeler = async (): Promise<string | null> => {
    if (appels >= max) { notes.push('plafond d’appels atteint'); return null; }
    appels++;
    try {
      const t = await llm.completer('monteur', messages, { json: true, temperature: o.temperature ?? 0.3, maxTokens: o.maxTokens ?? 12000 });
      brutes.push(t);
      messages.push({ role: 'assistant', content: t });
      return t;
    } catch (e) {
      notes.push(`appel LLM en échec : ${e instanceof Error ? e.message : String(e)}`);
      return null;
    }
  };
  const lire = (t: string): RapportValidation => {
    try { return validerEditPlan(lireJson<unknown>(t), ctx); } catch (e) { return { ok: false, erreurs: [{ regle: 'schema', chemin: '(racine)', message: `JSON illisible : ${e instanceof Error ? e.message : String(e)}` }], avertissements: [] }; }
  };

  let texte = await appeler();
  if (texte === null) return repli('pas de réponse', appels);
  let rapport = lire(texte);
  const premier = rapport.ok;
  for (let r = 0; !rapport.ok && r < (o.reparations ?? 0); r++) {
    const indices = indicesFonction('plan_edit', rapport.erreurs);
    messages.push({ role: 'user', content: `Le validateur refuse ton EditPlan :\n${messageErreurs(rapport)}\n${indices.length ? `\nIndices :\n${indices.join('\n')}\n` : ''}\nRenvoie l'EditPlan COMPLET corrigé, en JSON seul.` });
    texte = await appeler();
    if (texte === null) break;
    rapport = lire(texte);
  }
  if (!rapport.ok || !rapport.plan) return repli(`plan invalide après ${appels} appel(s) : ${rapport.erreurs.slice(0, 3).map((e) => e.regle).join(', ')}`, appels, premier);
  let plan = rapport.plan;
  plan.metadonnees = { ...plan.metadonnees, modele: 'llm', savoir: savoir.versions };

  // Tours critique → rustines : le code garde une rustine seulement si le score en code monte.
  for (let tour = 0; tour < (o.tours ?? 0); tour++) {
    const c = await critiquer(plan, b);
    if (!c.metriques.porte || c.composite >= 0.97 || !c.ecarts.length) break;
    messages.push({ role: 'user', content: `Critique mesurée de ton plan :\n${c.resume}\n\nCorrige avec au plus 8 rustines, JSON seul : {"rustines":[{"op":"regler_plan","id":"p3","duree_f":30}, ...]}. Opérations : regler_plan{id,entree_f,duree_f,vitesse,transition_in,zoom,src}, echanger{a,b}, supprimer{id}, inserer_apres{apres,plan}, regler_texte{index,texte,debut_f,duree_f,taille_pct,position}, ajouter_texte{texte}, supprimer_texte{index}, regler_audio{musique,ducking,cible_lufs,crete_db,fondu_coupe_ms}. Si tu raccourcis un plan, rallonge un autre du même nombre d'images.` });
    const t = await appeler();
    if (t === null) break;
    let rustines: unknown;
    try { rustines = lireJson<{ rustines?: unknown }>(t).rustines; } catch { notes.push('rustines illisibles'); break; }
    const rev = reviser(plan, rustines, ctx);
    if (!rev.ok) { notes.push(`rustines refusées : ${rev.message.slice(0, 160)}`); continue; }
    const apres = composite(mesurer(rev.plan, b), null);
    if (apres > c.composite) { plan = rev.plan; notes.push(`tour ${tour + 1} : ${c.composite.toFixed(3)} → ${apres.toFixed(3)}`); } else notes.push(`tour ${tour + 1} : rustines sans gain (${apres.toFixed(3)} ≤ ${c.composite.toFixed(3)}), gardées de côté`);
  }
  return { plan, source: 'llm', notes, appels, valideDuPremierCoup: premier, brutes, versionsSavoir: savoir.versions };
}
