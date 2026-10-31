/**
 * Réécrivain de prompts MiniMax H3 : transforme l'intention d'un débutant (en français, quelques mots) en prompt
 * structuré conforme au guide officiel. C'est l'équivalent maison du H3-Context-IR que MiniMax garde pour son API.
 * Le LLM propose, le validateur déterministe (promptH3.ts) décide ; deux réparations au plus, puis un repli minimal
 * toujours conforme, pour qu'un incident LLM ne bloque jamais un rendu.
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { type ClientLlm, lireJson, type MessageLlm } from './llm.js';
import { instructionH3, type ModeH3, validerPromptH3 } from './promptH3.js';

export interface EntreeReecriture {
  /** Ce que la personne a écrit, tel quel. */
  intention: string;
  mode: ModeH3;
  dureeS: number;
  /** Répliques à faire dire, recopiées mot pour mot. */
  dialogues?: { texte: string; langue: string; locuteur?: string }[];
  /** Consignes de cinéma choisies dans l'interface (caméra, lumière, style), en anglais du guide. */
  consignes?: string[];
}

export interface ResultatReecriture {
  prompt: string;
  source: 'llm' | 'repli';
  tentatives: number;
  /** Erreurs restantes de la dernière tentative LLM (vide si le prompt LLM est retenu). */
  erreurs: string[];
}

const ICI = dirname(fileURLToPath(import.meta.url));
let guide: string | null = null;
function guideOfficiel(): string {
  guide ??= readFileSync(join(ICI, 'guides', 'VIDEO_PROMPT_WRITING_GUIDE_base_en.md'), 'utf8');
  return guide;
}

function consignesSysteme(): string {
  return [
    'You are the prompt writer of Nexora Creative, a video studio built on the MiniMax H3 audio-video model.',
    'Rewrite the user intent into ONE final H3 prompt that follows the official guide below exactly.',
    'Rules: write the prompt in English, except dialogue inside <d>…</d> which stays verbatim in its own language;',
    'make it vivid, concrete and filmable (subjects, materials, light, composition, action along the timeline, camera motion with',
    'the guide vocabulary, diegetic sounds); keep it consistent with the requested duration; never add text on screen unless asked;',
    'respect the safety rules: no real person impersonation, no minors in harmful contexts, no misleading political content.',
    'Write only what is seen and heard: no meta remarks, notes or parentheses about the prompt itself (e.g. never "(S1 is not applicable)");',
    'keep every subject the user named exactly as named (a spaceship stays a spaceship, never an airship), and never add brands, franchises or trademarked characters.',
    'Answer with a JSON object {"prompt": "<the final prompt>"} and nothing else.',
    '',
    '=== OFFICIAL GUIDE ===',
    guideOfficiel(),
  ].join('\n');
}

function demande(e: EntreeReecriture): string {
  return JSON.stringify(
    {
      intention_utilisateur: e.intention,
      tache: e.mode.toUpperCase(),
      duree_secondes: Number(e.dureeS.toFixed(2)),
      ligne_instruction_obligatoire: instructionH3({ mode: e.mode, dureeS: e.dureeS, dernierPlan: 1 }) || null,
      repliques_mot_pour_mot: e.dialogues ?? [],
      consignes_cinema: e.consignes ?? [],
    },
    null,
    2,
  );
}

/** Prompt minimal, toujours conforme, utilisé quand le LLM est absent ou n'arrive pas à produire un prompt valide. */
export function promptDeRepli(e: EntreeReecriture): string {
  const repliques = (e.dialogues ?? [])
    .map((d, i) => ` A character (S${i + 1}) says: <d>[${d.langue}] ${d.texte.trim()}</d>`)
    .join('');
  const consignes = e.consignes?.length ? ` ${e.consignes.join(' ')}` : '';
  const corps = `integrated_multimodal_description: [Shot 1] Cinematic. ${e.intention.trim()}${consignes}${repliques}

overall_soundscape: Natural ambient sound matching the scene.

non_diegetic_music: N/A`;
  const instruction = instructionH3({ mode: e.mode, dureeS: e.dureeS, dernierPlan: 1 });
  return instruction ? `${instruction}\n\n${corps}` : corps;
}

/**
 * Textes affichés à l'image (entre guillemets dans la description, hors répliques <d>) que la personne n'a pas demandés.
 * H3 écrit ce qu'on lui cite : une enseigne inventée par le LLM apparaît dans la vidéo. Un texte est « demandé » s'il
 * figure dans l'intention et que celle-ci contient des guillemets.
 */
export function texteEcranNonDemande(prompt: string, intention: string): string[] {
  const debut = prompt.indexOf('integrated_multimodal_description:');
  const fin = prompt.indexOf('overall_soundscape:');
  const description = (debut >= 0 ? prompt.slice(debut, fin > debut ? fin : undefined) : prompt).replace(/<d>[\s\S]*?<\/d>/g, '');
  const cite = /["«“]/.test(intention);
  const normal = (x: string) => x.toLowerCase().replace(/[.,!?…]+$/, '').trim();
  return [...description.matchAll(/"([^"\n]{1,120})"/g)]
    .map((m) => m[1].trim())
    .filter((t) => !(cite && normal(intention).includes(normal(t))));
}

/** Notes adressées au modèle au lieu de décrire la scène ; H3 les lirait comme du contenu. */
export function remarquesParasites(prompt: string): string[] {
  return [...prompt.matchAll(/\((?:[^()]*\b(?:not applicable|does not speak|no dialogue|note:|N\/A)\b[^()]*)\)/gi)]
    .map((m) => `remove the meta remark ${m[0]}: describe only what is seen and heard`);
}

export async function reecrireH3(e: EntreeReecriture, llm: ClientLlm | null, maxTentatives = 3): Promise<ResultatReecriture> {
  const ctx = { mode: e.mode, dureeS: e.dureeS, dialogues: e.dialogues?.map((d) => d.texte) };
  let erreurs: string[] = ['aucun LLM configuré'];
  let tentatives = 0;
  if (llm) {
    const messages: MessageLlm[] = [
      { role: 'system', content: consignesSysteme() },
      { role: 'user', content: demande(e) },
    ];
    while (tentatives < maxTentatives) {
      tentatives++;
      let prompt = '';
      try {
        const brut = await llm.completer('redaction', messages, { json: true, temperature: 0.7 });
        prompt = String(lireJson<{ prompt?: unknown }>(brut).prompt ?? '').trim();
        erreurs = [
          ...validerPromptH3(prompt, ctx),
          ...remarquesParasites(prompt),
          ...texteEcranNonDemande(prompt, e.intention).map((t) => `on-screen text "${t}" was not requested by the user: remove it`),
        ];
        messages.push({ role: 'assistant', content: brut });
      } catch (err) {
        erreurs = [`réponse inutilisable : ${(err as Error).message}`];
        messages.push({ role: 'assistant', content: '(invalid)' });
      }
      if (!erreurs.length) return { prompt, source: 'llm', tentatives, erreurs: [] };
      messages.push({
        role: 'user',
        content: `The prompt does not follow the guide. Fix exactly these problems and answer again with {"prompt": "..."}:\n- ${erreurs.join('\n- ')}`,
      });
    }
  }
  const prompt = promptDeRepli(e);
  return { prompt, source: 'repli', tentatives, erreurs: validerPromptH3(prompt, ctx) };
}
