/**
 * Le réalisateur de Nexora Creative (« le LLM qui booste le tout ») : la phrase écrite à l'arrache par le client
 * (fautes, québécois, flou) devient en UN appel une fiche de réalisation : ce que le LLM a compris, les choix faits
 * par défaut (aucune question au client), les personnages, puis chaque plan en langage de réalisateur (cadrage et
 * objectif, action découpée dans le temps, caméra, lumière, matières, son). Le CODE compile ensuite la fiche dans le
 * dialecte de chaque générateur (MiniMax H3 T2VA/I2VA, image Qwen) : la forme est garantie par construction, les
 * répliques sont posées mot pour mot par le code, les personnages gardent la même description d'un plan à l'autre.
 *
 * Appuis : routage par scénario puis règles propres au scénario (SCMAPR, arXiv 2604.05489 ; TIDE, 2610.15098 : une
 * « compétence » de réécriture en un seul appel), fidélité à l'intention d'abord (VPO, 2503.20491), expansion créative
 * plutôt que simple mise en forme sur H3 (2610.29407 : +0,63 point sur H3 post-entraîné), mémoire d'entités pour la
 * cohérence entre plans (VideoMemory, 2601.03655 ; CoAgent, 2512.22536). Mesures : recherche/25.
 */
import { type ClientLlm, lireJson, type MessageLlm } from './llm.js';
import { instructionH3, type ModeH3, validerPromptH3 } from './promptH3.js';
import { convertirEnPromptRef, type SujetRef } from './personnages.js';
import {
  NEGATIF_LIVE_ACTION, REGLES_ACTION, REGLES_LIVE_ACTION, STYLE_LIVE_ACTION, STYLE_NEUTRE,
  requiertPhotographie, verifierRecetteLiveAction, verifierVaisseauxOriginaux,
} from './liveAction.js';

export type Famille = 'pub' | 'produit' | 'film' | 'vfx' | 'cours' | 'social' | 'clip' | 'autre';
export const FAMILLES: readonly Famille[] = ['pub', 'produit', 'film', 'vfx', 'cours', 'social', 'clip', 'autre'];

export interface PersonnageFiche {
  /** Identifiant utilisé dans les plans : P1, P2… */
  id: string;
  /** Groupe nominal anglais court et stable (« the little girl in the yellow raincoat »). */
  court: string;
  /** Apparence complète (anglais), posée une seule fois à la première apparition. */
  apparence: string;
  /** Voix (anglais) s'il parle : âge, timbre, débit, accent. */
  voix?: string;
}

export interface PlanFiche {
  /** Début du plan en secondes (0 pour le premier). */
  debut: number;
  /** Étiquette courte du cadrage (anglais), pour le storyboard montré au client. */
  cadrage: string;
  /**
   * Le plan en prose de réalisateur (anglais, un paragraphe) : cadrage et objectif, action découpée dans le temps,
   * mouvement de caméra, lumière, matières, sons synchronisés ; [P1] pour un personnage, [R1] pour la réplique 1.
   */
  texte: string;
}

export interface FicheRealisation {
  /** Ce que le LLM a compris, dans la langue du client, pour le client (une ou deux phrases). */
  compris: string;
  famille: Famille;
  /** Choix faits sans demander (langue du client, courts). */
  hypotheses: string[];
  /** Photographie : caméra, objectif nommé, pellicule ou capteur. */
  style: string;
  personnages: PersonnageFiche[];
  plans: PlanFiche[];
  ambiance: string;
  musique: string;
  /** Textes à l'écran DEMANDÉS par le client, recopiés tels quels (sinon vide). */
  texteEcran: string[];
  /** Trois autres directions possibles, dans la langue du client, une ligne chacune. */
  variantes: string[];
  /** Qui dit chaque réplique du client : { R1: 'P2' }. */
  locuteurs?: Record<string, string>;
}

export interface EntreeRealisateur {
  intention: string;
  mode: ModeH3;
  references?: { sujets: SujetRef[]; composition?: number };
  /** Langue des explications au client ; sinon détectée par le LLM depuis la demande. */
  langueClient?: 'fr' | 'en';
  dureeS: number;
  dialogues?: { texte: string; langue: string; locuteur?: string }[];
  consignes?: string[];
  /** Moteur visé : le dialecte change un peu (FastH3 rapide en 832×480 contre H3 cinéma en 1344×768). */
  moteur?: 'h3-fast' | 'h3-max';
  format?: '16:9' | '9:16' | '1:1';
}

export interface ResultatRealisateur {
  prompt: string;
  fiche: FicheRealisation;
  tentatives: number;
  erreurs: string[];
  /** Écarts de chaque tentative refusée (diagnostic du banc). */
  historique: string[][];
}

// ---------------------------------------------------------------------------------------------------------------------
// Consignes : la compétence du réalisateur, compacte (≈ 1 700 jetons) ; le guide officiel complet n'est plus envoyé,
// sa forme est appliquée par le code.

const REGLES_FAMILLE: Record<Famille, string> = {
  pub: 'AD: open on a hook in the first second; the offer or product is the hero; show the human benefit (taste, relief, joy) on an expressive face or character consistent with the requested medium; add a beauty beat; end on a calm, clean hero frame (no text, no logo: the code adds them later); always a music bed.',
  produit: 'PRODUCT: the object never deforms, melts or changes design; exact materials (brushed gold, frosted glass, knit mesh), macro details, studio lighting with gradient backdrop and crisp specular highlights, slow controlled camera (arc, push in, turntable); one hero transformation at most; end on a centered hero frame; always a music bed; contrast that makes the object read (a white object on a darker gradient).',
  film: 'FILM: classic coverage (establishing, then medium, then close-up on the emotion); motivated practical light consistent across shots; characters keep the exact same look in every shot; the dramatic beat lands in the last shot; dialogue paced with pauses and reactions; music unless the scene asks for silence.',
  vfx: 'VFX: make scale legible (tiny humans, buildings, birds, clouds for reference); give effects a clear cause and consequence (fireballs expand then roll into black smoke, debris arcs and falls, shockwaves spread, glass shards travel); let the effect affect its surroundings; camera reacts (shake on impact, slight lag); one hero element per shot, the rest as background action; preserve the requested visual medium.',
  cours: 'LESSON: clarity first; one idea per shot; for mechanisms and concepts use a clear cutaway or practical demonstration in the requested visual medium, with readable color-coded parts (no labels or text unless the user asked); slow camera moves that reveal the mechanism step by step; calm, friendly tone; simple diegetic sounds.',
  social: 'SOCIAL: vertical-first composition, subject centered and close; hook in the first second; punchy pace and a clear payoff; phone or handheld look when it suits (authentic), otherwise bold colorful light; humor lands on a reaction.',
  clip: 'MUSIC VIDEO: performance to camera, rhythmic camera moves synced to beats, strong stylized light (neon, haze, backlight), atmosphere particles (smoke, steam, snow); diegetic sound is the performance itself.',
  autre: 'GENERAL: choose the clearest visual medium for the idea and the client’s stated style; one clear subject and action.',
};

function consignes(e: EntreeRealisateur): string {
  const fast = e.moteur !== 'h3-max';
  return [
    'You are the director of Nexora Creative. Clients type a few careless words (typos, Quebec French slang or English, vague ideas). You turn them into a shooting plan',
    'for MiniMax H3, an audio+video model, so the video looks like a top-tier production. Never ask the client anything: choose strong defaults and list them.',
    '',
    'STEP 1 UNDERSTAND. Fix spelling; decode Quebec French (char = car, pis = and, ptit/ptite = small, chu = I am, dépanneur = convenience store, tuque = knit hat,',
    'cabane à sucre = maple sugar shack, tire = maple taffy on snow, cantine/casse-croûte = snack bar). Classify the request into one family:',
    'pub (ad for a business), produit (product shot), film (story), vfx (spectacle/special effects), cours (lesson), social (social media), clip (music video), autre.',
    'Keep EVERY subject, place, action and constraint the client named, exactly (a spaceship stays a spaceship; Montreal stays Montreal). Real landmarks are fine.',
    'Protected characters, franchises and brands become generic equivalents that keep the look: lightsaber -> plasma-blade sword / energy blade;',
    'Jedi -> hooded knight in a brown robe; Sith -> masked warrior with a red energy blade; "like Starbucks" -> premium coffee-shop style, no logo. Never name real people.',
    '',
    'STEP 2 DIRECT. Every field except compris, hypotheses and variantes is in ENGLISH (the video model reads English), even when the client writes French.',
    'Each shot is ONE flowing paragraph of shooting prose (texte), 45 to 90 words, like a director briefing the crew, never a list of keywords. It covers, in this order:',
    'the framing, the action told along time (start, peak, result), ONE camera move, light and color, key materials or particles, and sounds synced to the action.',
    '- When the requested medium is photography, use the real camera, lens and light details in the conditional photo recipe below. For animation or illustration, describe the intended visual language instead of adding real camera hardware.',
    '- Shot 1 texte starts with its framing, e.g. "a low-angle wide shot on a 24mm lens frames ...". Shots 2+ texte starts with the noun phrase that follows "the camera cuts to", e.g. "a tight close-up of her hands, 85mm, as ...".',
    '- Characters: write [P1], [P2] at their first mention in each shot, then he/she/they; never "[P1]\'s" (write "the hand of [P1]"). The code writes their description.',
    '- A client line is spoken where you put its tag [R1] as its own sentence right after the speaker acts: the code writes "the teacher (S1) says: <d>...</d>" there, word for word.',
    '- Camera vocabulary: push in / pull out, pan, truck, tilt, pedestal, arc shot, tracking shot, static shot, zoom, POV, shake slightly/strongly, roll, with "small/large amplitude" and',
    '  "slow/fast speed" only when meaningful. Never redundant ("slowly at slow speed") and never contradictory (a static shot does not move; a macro lens does not frame two full bodies).',
    '- Timing: a shot under 4 s holds ONE action; spoken lines need about 1 second per 2.5 words inside their shot. Keep physics, season and story logic coherent (no fireflies in snow;',
    '  a cook serves before anyone eats). Lens and look fit the format (no anamorphic look in 9:16 or macro product shots) and the family (a children lesson is not a blockbuster).',
    '- Translate objects exactly (canette = can, not canister). Never add an accent, a brand, a logo or text that the client did not ask for.',
    `Shots: 5 s -> 1 shot (2 only for ads/social hooks); 10 s -> 2 or 3 shots; 15 s -> 3 or 4 shots. Each shot lasts at least 2.5 s; first shot starts at 0; the last shot starts at least 2.5 s before the end (e.g. 10 s: 0, 3.5, 7; 15 s: 0, 4, 8, 11.5).`,
    'A cut must bring new information (new angle, subject or moment); a simple reframing is a camera move, not a cut.',
    '',
    REGLES_ACTION,
    '',
    REGLES_LIVE_ACTION,
    '',
    'FAMILY RULES (apply the one you chose while preserving the client’s requested medium):',
    ...FAMILLES.filter((f) => f !== 'autre').map((f) => `- ${REGLES_FAMILLE[f]}`),
    '',
    'H3 DIALECT:',
    '- style: preserve an explicitly requested visual medium or style. If none is named, choose one that fits the brief; only promotional ads and product films default to the conditional photographic recipe above.',
    '- NEVER put written words, signs, labels, subtitles, logos or numbers on screen unless the client quoted them; if quoted, copy them in texteEcran and show them once, in English double quotes, in the action.',
    '- H3 handles poorly: small legible text, close-ups of many faces in a crowd, intricate finger work, more than two speaking characters, too many subjects in one shot. Avoid them.',
    fast
      ? '- Engine: fast 832x480 draft engine. Favor bold, readable compositions (medium and close shots, strong silhouettes, high contrast), few simultaneous elements.'
      : '- Engine: cinema 1344x768 engine. Make the main subject easy to read within the chosen composition.',
    '- ambiance: 1 to 3 English sentences summarizing ambient and action sounds for the whole video (no dialogue). musique: 1 or 2 sentences about instruments, tempo and dynamics; "N/A" only if the client wants no music or the scene needs silence.',
    '- personnages: only characters who appear. court = stable short noun phrase (e.g. "the old detective in a grey trench coat"); apparence = age, face, hair, clothing, colors; voix only if they speak, in English (e.g. "a calm, clear mid-pitched female voice"), no accent unless the client asked.',
    e.mode === 'i2va' || e.mode === 'fl2va' ? '- The video starts from the client\'s photo: shot 1 must start from the picture (same subject, framing, clothes, colors) and develop the action from it.' : '',
    '',
    e.mode === 'fl2va' || e.mode === 'l2va' ? '- The last shot must end exactly at the supplied last image: describe a continuous physical transition, do not invent a cut after it.' : '',
    e.mode === 'ref2va' ? '- References: keep the supplied subject names literally in shot text where they appear (do not replace their names with [P1]); preserve their identity, do not invent other reference assets. Composition references anchor framing, not identity.' : '',
    'STEP 3 EXPLAIN. compris, hypotheses and variantes use the CLIENT LANGUAGE (French for Quebec French, English for English), following langue_client if supplied. compris: one or two sentences; hypotheses: short defaults; variantes: three distinct directions that preserve the requested medium. All technical fields remain English.',
    '',
    'Before answering, check silently each shot for contradictions (lens vs framing, camera, timing, physics, season, story order) and fix them.',
    'Answer with ONE JSON object and nothing else:',
    '{"compris":"","famille":"pub|produit|film|vfx|cours|social|clip|autre","hypotheses":[""],"style":"","personnages":[{"id":"P1","court":"","apparence":"","voix":""}],',
    '"plans":[{"debut":0,"cadrage":"short label","texte":"one paragraph"}],"locuteurs":{"R1":"P1"},"ambiance":"","musique":"","texteEcran":[],"variantes":["","",""]}',
    'locuteurs maps each client line tag to the character who says it (empty object when there is no client line).',
  ].filter((l) => l !== '').join('\n');
}

function demande(e: EntreeRealisateur): string {
  return JSON.stringify({
    client: e.intention,
    duree_secondes: Number(e.dureeS.toFixed(2)),
    format: e.format ?? '16:9',
    mode: e.mode,
    depart_photo: e.mode === 'i2va' || e.mode === 'fl2va',
    arrivee_photo: e.mode === 'fl2va' || e.mode === 'l2va',
    references: e.references,
    langue_client: e.langueClient,
    repliques_client: (e.dialogues ?? []).map((d, i) => ({ tag: `R${i + 1}`, texte: d.texte, langue: d.langue })),
    consignes_interface: e.consignes ?? [],
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// Lecture et validation de la fiche

const chaine = (v: unknown, max = 900) => (typeof v === 'string' ? v.replace(/\s+/g, ' ').trim().slice(0, max) : '');
const liste = (v: unknown, n: number, max = 300) => (Array.isArray(v) ? v.map((x) => chaine(x, max)).filter(Boolean).slice(0, n) : []);

export function lireFiche(brut: unknown, demande?: Pick<EntreeRealisateur, 'intention' | 'consignes'>): FicheRealisation {
  const o = (brut ?? {}) as Record<string, unknown>;
  const famille = FAMILLES.includes(o.famille as Famille) ? (o.famille as Famille) : 'autre';
  const personnages = (Array.isArray(o.personnages) ? o.personnages : []).slice(0, 4).map((p: any, i: number) => ({
    id: /^P\d$/.test(String(p?.id)) ? String(p.id) : `P${i + 1}`,
    court: chaine(p?.court, 120),
    apparence: chaine(p?.apparence, 400),
    ...(chaine(p?.voix, 200) ? { voix: chaine(p?.voix, 200) } : {}),
  })).filter((p) => p.court);
  const plans = (Array.isArray(o.plans) ? o.plans : []).slice(0, 6).map((p: any) => ({
    debut: Number(p?.debut) || 0,
    cadrage: chaine(p?.cadrage, 160),
    // Ancien format par champs (v1) : recollé en un paragraphe.
    texte: chaine(p?.texte, 1400) || ['cadrage', 'action', 'camera', 'lumiere', 'details', 'son'].map((k) => chaine(p?.[k], 600)).filter(Boolean).join('. '),
  }));
  return {
    compris: chaine(o.compris, 400), famille, hypotheses: liste(o.hypotheses, 6, 160),
    style: chaine(o.style, 600) || (requiertPhotographie(famille, demande?.intention ?? '', demande?.consignes) ? STYLE_LIVE_ACTION : STYLE_NEUTRE),
    ...(o.locuteurs && typeof o.locuteurs === 'object' ? { locuteurs: Object.fromEntries(Object.entries(o.locuteurs as Record<string, unknown>).filter(([k, v]) => /^R\d$/.test(k) && /^P\d$/.test(String(v))).map(([k, v]) => [k, String(v)])) } : {}),
    personnages, plans, ambiance: chaine(o.ambiance, 600), musique: chaine(o.musique, 400) || 'N/A', texteEcran: liste(o.texteEcran, 3, 120), variantes: liste(o.variantes, 3, 200),
  };
}

export const MARQUES = /\b(lightsabers?|jedi|sith|star ?wars|darth|starbucks|marvel|avengers|nike|adidas|coca-?cola|pepsi|disney|pixar|pok[eé]mon|harry potter|batman|superman|spider-?man|iron ?man|transformers?|godzilla|tim hortons?|mcdonald'?s|iphone|samsung|stetson|rolex|ferrari|lego)\b/i;

/** Écarts de la fiche (en anglais : ils repartent au LLM pour réparation). */
export function verifierFiche(f: FicheRealisation, e: EntreeRealisateur): string[] {
  const err: string[] = [];
  if (!f.plans.length) err.push('plans is empty: write at least one shot');
  const max = e.dureeS <= 6 ? 2 : e.dureeS <= 11 ? 3 : 4;
  if (f.plans.length > max) err.push(`too many shots (${f.plans.length}) for ${e.dureeS.toFixed(1)} s: at most ${max}`);
  f.plans.forEach((p, i) => {
    if (!p.texte) err.push(`shot ${i + 1}: texte is empty`);
    const mots = p.texte.split(/\s+/).length;
    if (mots > 90) err.push(`shot ${i + 1} has ${mots} words: keep each shot under 90 words, cut redundant adjectives`);
    if (i === 0 && p.debut !== 0) err.push('shot 1 must start at 0');
    if (i > 0) {
      const avant = f.plans[i - 1].debut;
      if (!(p.debut > avant)) err.push(`shot ${i + 1}: start ${p.debut} must be after shot ${i} start ${avant}`);
      if (p.debut - avant < 2.4) err.push(`shot ${i}: lasts ${(p.debut - avant).toFixed(1)} s, shots must last at least 2.5 s`);
      if (p.debut > e.dureeS - 2.4) err.push(`shot ${i + 1}: starts at ${p.debut} s, too close to the end (${e.dureeS.toFixed(2)} s)`);
    }
  });
  const tous = JSON.stringify(f);
  if (e.mode === 'ref2va') {
    for (const s of e.references?.sujets ?? []) {
      if (!f.plans.some((p) => p.texte.toLowerCase().includes(s.nom.toLowerCase()))) err.push(`reference subject ${s.nom}: keep its literal name in the shots where it appears`);
    }
  }
  const ids = new Set(f.personnages.map((p) => p.id));
  for (const m of tous.matchAll(/\[(P\d)\]/g)) if (!ids.has(m[1])) { err.push(`[${m[1]}] is used but not defined in personnages`); break; }
  (e.dialogues ?? []).forEach((_, i) => {
    const n = f.plans.filter((p) => p.texte.includes(`[R${i + 1}]`)).length;
    if (n !== 1) err.push(`put the tag [R${i + 1}] exactly once, in the texte of the shot where the client line ${i + 1} is spoken (found ${n})`);
  });
  // Le client peut nommer une marque (« comme Starbucks mais pas Starbucks ») : le prompt, lui, n'en porte jamais.
  const anglais = versH3(f, e).replace(/<d>[\s\S]*?<\/d>/g, ' ');
  const photo = requiertPhotographie(f.famille, e.intention, e.consignes);
  err.push(...verifierRecetteLiveAction(anglais, e.intention, f.famille, e.consignes));
  err.push(...verifierVaisseauxOriginaux(anglais, e.intention));
  f.plans.forEach((p, i) => {
    if (!/\b(close[- ]?up|medium|tight|fills?|half the frame|foreground|large in (?:the )?frame)\b/i.test(p.texte)) err.push(`shot ${i + 1}: keep the hero large and readable in frame`);
    if (photo) {
      if (!/\b\d{2,3}\s?mm\b/i.test(p.texte)) err.push(`shot ${i + 1}: name its focal length`);
      if (!/\b(Cooke|Zeiss|Leica|Angenieux|Angénieux|Panavision|Canon|Nikkor|Sigma|Atlas)\b/i.test(p.texte)) err.push(`shot ${i + 1}: name its lens family`);
      if (!/\b(sun(?:light)?|daylight|overcast|windows?|lamps?|lanterns?|fire|sodium|softbox|soft box|LED|studio light|key light|backlight|neon|candles?|torches?|light from|lit by)\b/i.test(p.texte)) err.push(`shot ${i + 1}: name a motivated practical light source`);
      if (!/\b(metal|steel|alumin(?:i)?um|copper|gold|silver|glass|wood(?:en)?|leather|skin|fabric|cotton|silk|wool|flannel|fur|scales?|stone|brick|concrete|mud|wet|water|rain|snow|ice|steam|smoke|dust|rust|scratched|worn|paper|cardboard|ceramic|porcelain|cheese|syrup|taffy|sauce|knit|mesh|foam|sand|rubber|flesh|bark)\b/i.test(p.texte)) err.push(`shot ${i + 1}: describe tangible material or surface texture`);
    }
    const sujetsVisibles = p.texte.replace(/\[(P\d)\]/g, (_, id) => { const x = f.personnages.find((s) => s.id === id); return x ? `${x.court} ${x.apparence}` : ''; });
    if (f.famille === 'vfx' && !/\b(people|human|crew|windows?|buildings?|doors?|person|soldiers?|crowd|cars?|trees?|figure|cockpit|dock|brick|castle|tower|knight|warrior|man|woman|boy|girl|child|human-sized|hands?|faces?)\b/i.test(sujetsVisibles)) err.push(`shot ${i + 1}: include a concrete scale cue`);
    if (!/\b(then|as|while|before|after|initially|finally|start|end|first|until|during|at \d)\b/i.test(p.texte)) err.push(`shot ${i + 1}: describe action changing over time, keep movement precise`);
  });
  const motsFr = anglais.match(/\b(le|la|les|des|du|de|une|et|au|aux|avec|sur|dans|puis|est|sous|vers|lumière|caméra|plan|gros|lent)\b/gi) ?? [];
  if (motsFr.length >= 5) err.push('shot fields, style, personnages, ambiance and musique must be written in English, not French');
  const marque = tous.replace(/"compris":"[^"]*"|"hypotheses":\[[^\]]*\]|"variantes":\[[^\]]*\]/g, '').match(MARQUES);
  if (marque) err.push(`"${marque[0]}" is a brand or protected name: use a generic equivalent (e.g. energy blade, hooded knight, premium coffee shop)`);
  const cite = /["«“]/.test(e.intention);
  for (const t of f.texteEcran) if (!cite || !e.intention.toLowerCase().includes(t.toLowerCase())) err.push(`texteEcran "${t}" was not quoted by the client: remove it`);
  const description = f.plans.map((p) => p.texte).join(' ').replace(/\[R\d\]/g, '');
  for (const m of description.matchAll(/"([^"]{1,120})"/g)) {
    if (!f.texteEcran.some((t) => t.toLowerCase() === m[1].toLowerCase())) err.push(`on-screen text "${m[1]}" was not requested: remove it`);
  }
  return err;
}

// ---------------------------------------------------------------------------------------------------------------------
// Dialectes compilés par le code

const horodatage = (s: number) => {
  const ms = Math.round(s * 1000);
  return `${String(Math.floor(ms / 60000)).padStart(2, '0')}:${String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')}.${String(ms % 1000).padStart(3, '0')}`;
};
const phrase = (s: string) => { const t = s.trim(); return t ? (/([.!?]|<\/d>)$/.test(t) ? t : `${t}.`) : ''; };
const majuscule = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

const groupe = (p: PersonnageFiche) => p.court.replace(/^(a|an)\s+/i, 'the ');

/** [P1] → groupe nominal stable ; [R1] → « the teacher (S1) says in a … voice: <d>…</d> », mot pour mot. */
function remplir(texte: string, f: FicheRealisation, e: EntreeRealisateur, locuteurs: Map<string, string>): string {
  let t = texte.replace(/\[R(\d)\]/g, (_, n) => {
    const d = e.dialogues?.[Number(n) - 1];
    if (!d) return '';
    // Locuteur : celui que la fiche désigne, sinon le personnage cité juste avant la réplique, sinon le premier qui a une voix.
    const avant = texte.slice(0, texte.indexOf(`[R${n}]`));
    const id = f.locuteurs?.[`R${n}`] ?? [...avant.matchAll(/\[(P\d)\]/g)].pop()?.[1] ?? f.personnages.find((p) => p.voix)?.id ?? f.personnages[0]?.id;
    const p = f.personnages.find((x) => x.id === id);
    const s = locuteurs.get(id ?? '') ?? `S${locuteurs.size + 1}`;
    if (id) locuteurs.set(id, s);
    const voix = p?.voix ? ` in ${/^(a|an)\s/i.test(p.voix) ? p.voix : `a ${p.voix}`}` : '';
    return ` ${p ? majuscule(groupe(p)) : 'The speaker'} (${s}) says${voix}: <d>[${d.langue}] ${d.texte.trim()}</d> `;
  });
  t = t.replace(/\[(P\d)\]/g, (_, id) => { const p = f.personnages.find((x) => x.id === id); return p ? groupe(p) : 'the character'; });
  t = t.replace(/<\/d>\s*\./g, '</d>').replace(/\s+([.,;:])/g, '$1').replace(/\s{2,}/g, ' ').replace(/\.\s*\./g, '.').trim();
  // Majuscule en début de phrase (un [P1] en tête donne « the … »), sans toucher au texte des répliques.
  return t.split(/(<d>[\s\S]*?<\/d>)/).map((x, i) => (i % 2 ? x : x.replace(/(^|[.!?]\s+)([a-z])/g, (_, a, b) => a + b.toUpperCase()))).join('')
    .replace(/(<\/d>\s+)([a-z])/g, (_, a, b) => a + b.toUpperCase());
}

/** Première mention d'un personnage dans le film : groupe court puis apparence complète en apposition. */
function presenter(texte: string, f: FicheRealisation, vus: Set<string>): string {
  return texte.replace(/\[(P\d)\]('s)?/g, (m, id, poss) => {
    const x = f.personnages.find((y) => y.id === id);
    if (!x || vus.has(id) || !x.apparence || poss) return m;
    vus.add(id);
    return `[${id}] (${x.apparence.replace(/[.\s]+$/, '')})`;
  });
}

const minusculeInitiale = (s: string) => s.charAt(0).toLowerCase() + s.slice(1).replace(/[.\s]+$/, '');

/** Compile la fiche en prompt MiniMax H3 (T2VA ou I2VA), toujours dans la forme du guide officiel. */
export function versH3(f: FicheRealisation, e: EntreeRealisateur): string {
  const vus = new Set<string>();
  const locuteurs = new Map<string, string>();
  const plans = f.plans.map((p, i) => {
    const texte = minusculeInitiale(phrase(remplir(presenter(p.texte, f, vus), f, e, locuteurs)));
    const fin = /<\/d>$/.test(texte) ? '' : '.';
    const debutStyle = f.style.trim() ? `${f.style.replace(/[.\s]+$/, '')}, ` : '';
    const corps = i === 0 ? `${debutStyle}${texte}${fin}` : `At ${horodatage(p.debut)}, the camera cuts to ${texte.replace(/^the camera cuts to\s+/i, '')}${fin}`;
    return `[Shot ${i + 1}] ${corps.replace(/\.\.$/, '.')}`;
  });
  // Les consignes de l'interface sont interprétées/traduites par le LLM, jamais recollées brutes en aval.
  const exclusions = requiertPhotographie(f.famille, e.intention, e.consignes) ? ` ${NEGATIF_LIVE_ACTION}` : '';
  const corps = `integrated_multimodal_description: ${plans.join(' ')}${exclusions}

overall_soundscape: ${phrase(f.ambiance) || 'Natural ambient sound matching the scene.'}

non_diegetic_music: ${/^n\/?a\.?$/i.test(f.musique.trim()) ? 'N/A' : phrase(f.musique)}`;
  if (e.mode === 'ref2va') return convertirEnPromptRef(corps, e.references?.sujets ?? [], { composition: e.references?.composition, style: f.style });
  const instruction = instructionH3({ mode: e.mode, dureeS: e.dureeS, dernierPlan: f.plans.length });
  return instruction ? `${instruction}\n\n${corps}` : corps;
}

/** Même fiche, dialecte image (Qwen-Image) : un plan figé, pour le plan clé « image d'abord ». */
export function versImage(f: FicheRealisation, plan = 0, intention = ''): string {
  const p = f.plans[plan] ?? f.plans[0];
  if (!p) return f.compris;
  const texte = p.texte.replace(/\[R\d\]/g, '').replace(/\[(P\d)\]('s)?/g, (_, id, poss) => {
    const x = f.personnages.find((y) => y.id === id);
    return x ? `${groupe(x)}${x.apparence ? ` (${x.apparence.replace(/[.\s]+$/, '')})` : ''}${poss ?? ''}` : 'the character';
  });
  const style = f.style.trim() ? `${f.style.replace(/[.\s]+$/, '')}, ` : '';
  const negative = requiertPhotographie(f.famille, [intention, f.style].filter(Boolean).join('\n')) ? ` ${NEGATIF_LIVE_ACTION}` : '';
  return [`${style}a single still frame:`, phrase(texte), 'Frozen moment, no motion blur from camera moves. No text, no logo, no watermark.', negative].join(' ');
}

// ---------------------------------------------------------------------------------------------------------------------

/** Client qui passe au suivant quand un appel échoue (palier saturé, clé absente) : le client n'attend jamais un seul fournisseur. */
export function clientAvecSecours(clients: ClientLlm[]): ClientLlm {
  const essayer = async <T>(f: (c: ClientLlm) => Promise<T>): Promise<T> => {
    let derniere: unknown;
    for (const c of clients) {
      try { return await f(c); } catch (e) { derniere = e; }
    }
    throw derniere instanceof Error ? derniere : new Error('aucun client LLM');
  };
  return {
    completer: (role, messages, options) => essayer((c) => c.completer(role, messages, options)),
    ...(clients.every((c) => c.completerAvecOutils) ? { completerAvecOutils: (role, messages, outils, options) => essayer((c) => c.completerAvecOutils!(role, messages, outils, options)) } : {}),
  };
}

/**
 * Un appel (deux réparations au plus). Le LLM propose la fiche, le code vérifie la fiche, compile le dialecte, puis
 * repasse le validateur officiel. Lève une erreur si rien d'utilisable : l'appelant retombe sur le réécrivain classique.
 */
export async function realiser(e: EntreeRealisateur, llm: ClientLlm, maxTentatives = 3): Promise<ResultatRealisateur> {
  const messages: MessageLlm[] = [
    { role: 'system', content: consignes(e) },
    { role: 'user', content: demande(e) },
  ];
  const ctx = { mode: e.mode, references: e.references, dureeS: e.dureeS, dialogues: e.dialogues?.map((d) => d.texte) };
  let erreurs: string[] = [];
  const historique: string[][] = [];
  for (let tentatives = 1; tentatives <= maxTentatives; tentatives++) {
    let brut = '';
    try {
      brut = await llm.completer('redaction', messages, { json: true, temperature: 0.6, maxTokens: 3000 });
      const fiche = lireFiche(lireJson(brut), e);
      erreurs = verifierFiche(fiche, e);
      const prompt = versH3(fiche, e);
      if (!erreurs.length) erreurs = validerPromptH3(prompt, ctx);
      if (!erreurs.length) return { prompt, fiche, tentatives, erreurs, historique };
    } catch (err) {
      erreurs = [`unusable answer: ${(err as Error).message}`];
    }
    historique.push(erreurs);
    messages.push({ role: 'assistant', content: brut || '(invalid)' });
    messages.push({ role: 'user', content: `Fix exactly these problems and answer again with the full JSON object:\n- ${erreurs.join('\n- ')}` });
  }
  // Une fiche encore invalide repart au chemin de secours ; aucune règle de photographie n'est ignorée.
  throw new Error(`réalisateur : ${erreurs.join(' ; ')}`);
}
