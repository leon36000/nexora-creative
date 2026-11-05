/**
 * Garde-fou avant rendu. La licence MiniMax H3 (V.5, AUP) impose des mesures raisonnables, testées et revues
 * périodiquement contre les usages interdits : mineurs, atteinte à une personne réelle, désinformation électorale,
 * contenu haineux ou violent extrême, malware, usage militaire. Deux couches :
 *  1. des règles déterministes (toujours actives, même sans LLM) pour les cas les plus graves ;
 *  2. un classificateur LLM (rôle « moderation ») pour le reste ; s'il est indisponible, seules les règles s'appliquent
 *     et le fait est journalisé (échec ouvert contrôlé : on ne bloque pas toute la création pour une panne du LLM).
 * Le texte refusé n'est jamais renvoyé tel quel dans les journaux.
 */
import { type ClientLlm, lireJson } from './llm.js';
import type { LangueClient } from '../../shared/creationLanguage.js';

export interface VerdictModeration { ok: boolean; categorie?: string; raison?: string; source: 'regles' | 'llm' | 'regles_seules' }

const REGLES: { categorie: string; motif: RegExp; raison: string; raisonEn: string }[] = [
  { categorie: 'mineurs', motif: /\b(enfant|mineur|mineure|gamin|gamine|fillette|garçonnet|petite? fille|petit garçon|adolescent(?:e)?|child|kid|minor|underage|teen(?:ager)?)\b[^.]{0,80}\b(nu|nue|nus|nues|sexe|sexuel|sexuelle|érotique|porn|nude|naked|sexual|erotic)\b/i, raison: 'Contenu sexuel impliquant des mineurs : interdit.', raisonEn: 'Sexual content involving minors is not allowed.' },
  { categorie: 'mineurs', motif: /\b(nu|nue|nus|nues|sexuel|sexuelle|érotique|nude|naked|sexual|erotic)\b[^.]{0,80}\b(enfant|mineur|mineure|gamin|gamine|fillette|petite? fille|petit garçon|adolescent(?:e)?|child|kid|minor|underage|teen(?:ager)?)\b/i, raison: 'Contenu sexuel impliquant des mineurs : interdit.', raisonEn: 'Sexual content involving minors is not allowed.' },
  { categorie: 'deepfake', motif: /\b(deepfake|hypertrucage|hypertrucage|fausse? vidéo de|fake video of)\b/i, raison: 'Les imitations trompeuses de personnes réelles sont interdites.', raisonEn: 'Deceptive impersonations of real people are not allowed.' },
  { categorie: 'malware', motif: /\b(ransomware|malware|virus informatique)\b[^.]{0,60}\b(code|écris|écrire|crée|générer?|write|create)\b/i, raison: 'Création de logiciel malveillant : interdit.', raisonEn: 'Creating malware is not allowed.' },
  { categorie: 'terrorisme', motif: /\b(propagande|recrutement|recruitment|propaganda)\b[^.]{0,60}\b(terroriste|djihad|isis|daech|terrorist)\b/i, raison: 'Propagande terroriste : interdite.', raisonEn: 'Terrorist propaganda is not allowed.' },
];

export function modererParRegles(texte: string, langue: LangueClient = 'fr'): VerdictModeration {
  for (const r of REGLES) if (r.motif.test(texte)) return { ok: false, categorie: r.categorie, raison: langue === 'en' ? r.raisonEn : r.raison, source: 'regles' };
  return { ok: true, source: 'regles' };
}

function systeme(langue: LangueClient): string {
  const langueReponse = langue === 'en' ? 'English' : 'French';
  return [
  'You are the safety reviewer of a video and image studio built on MiniMax H3. Decide if the user request may be rendered.',
  'Refuse only requests that clearly fall in one of these categories: sexual content involving minors; realistic impersonation or a deceptive',
  'depiction of a real, named person (public figure or private individual); election or political disinformation meant to mislead; hateful or',
  'extremely graphic violent content meant to harass or incite; terrorism or violent extremism; malware; military use; instructions for serious harm.',
  'Fiction is allowed: fantasy fights, dragons, martial arts, space battles, stylized action, horror without real persons are fine.',
  `Answer with JSON {"verdict":"ok"|"refuse","categorie":"...","raison":"one short sentence in ${langueReponse} for the user"} and nothing else.`,
  ].join(' ');
}

export async function moderer(texte: string, llm: ClientLlm | null, journal: (m: string) => void = () => {}, langue: LangueClient = 'fr'): Promise<VerdictModeration> {
  const regles = modererParRegles(texte, langue);
  if (!regles.ok) return regles;
  if (!llm) return { ok: true, source: 'regles_seules' };
  try {
    const brut = await llm.completer('moderation', [{ role: 'system', content: systeme(langue) }, { role: 'user', content: texte.slice(0, 4000) }], { json: true, temperature: 0 });
    const r = lireJson<{ verdict?: string; categorie?: string; raison?: string }>(brut);
    if (r.verdict === 'refuse') return { ok: false, categorie: String(r.categorie ?? 'autre').slice(0, 40), raison: String(r.raison ?? (langue === 'en' ? 'This request cannot be completed.' : 'Cette demande ne peut pas être traitée.')).slice(0, 240), source: 'llm' };
    if (r.verdict === 'ok') return { ok: true, source: 'llm' };
    throw new Error('verdict inconnu');
  } catch (e) {
    journal(`modération LLM indisponible (${e instanceof Error ? e.message : 'erreur'}) : règles seules`);
    return { ok: true, source: 'regles_seules' };
  }
}
