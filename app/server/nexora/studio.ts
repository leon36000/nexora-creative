/**
 * Mode Studio : le montage expert de Nexora Creative (éditeur FreeCut dans mode-studio/, servi sous /mode-studio/).
 *   créations   les prises terminées de l'organisation, importables d'un clic dans la timeline ;
 *   assistant   une demande en français + un résumé de la timeline → le LLM répond par des commandes Nexora en secondes
 *               (que le navigateur traduit en opérations FreeCut, une seule annulation par demande) et par des actions
 *               d'IA exécutées par du code déterministe (silences, sous-titres, rythme, génération) ;
 *   analyses    silences (ffmpeg silencedetect), temps forts d'une musique (enveloppe d'attaques + autocorrélation),
 *               transcription au mot (faster-whisper, server/nexora/transcrire.py).
 * Tout ce qui est validé ici est borné : le LLM ne peut proposer que des commandes et des actions connues.
 */
import type { ClientLlm } from './llm.js';
import { lireJson } from './llm.js';
import { avecCompetences } from './competences.js';

// ---------------------------------------------------------------------------------------------------------------------
// Créations

export type GenreCreation = 'video' | 'image' | 'musique';

export interface Creation {
  id: number;
  genre: GenreCreation;
  nom: string;
  url: string;
  date: string;
  dureeS?: number;
}

interface PriseLue {
  id: number;
  kind: string;
  status: string;
  shot_name: string;
  output_path: string | null;
  settings: string;
  created_at: string;
}

function genreDe(p: PriseLue): GenreCreation | null {
  const chemin = (p.output_path ?? '').toLowerCase();
  if (p.kind === 'musique' || /\.(mp3|wav|flac|m4a|ogg)$/.test(chemin)) return 'musique';
  if (p.kind === 'still' || /\.(png|jpe?g|webp)$/.test(chemin)) return 'image';
  if (p.kind === 'video' || /\.(mp4|mov|webm|mkv)$/.test(chemin)) return 'video';
  return null;
}

/** Les prises terminées, importables dans le Mode Studio (les films en cours et les échecs sont exclus). */
export function creationsPourStudio(prises: PriseLue[]): Creation[] {
  const sortie: Creation[] = [];
  for (const p of prises) {
    if (p.status !== 'done' || !p.output_path) continue;
    const genre = genreDe(p);
    if (!genre) continue;
    let s: Record<string, unknown> = {};
    try { s = JSON.parse(p.settings); } catch { /* réglages illisibles : on garde la prise */ }
    const nom = String(s.intention ?? s.userPrompt ?? p.shot_name ?? `Prise ${p.id}`).trim().slice(0, 120) || `Prise ${p.id}`;
    const dureeS = genre === 'musique' ? Number(s.dureeS) || undefined
      : genre === 'video' && Number(s.lengthFrames) ? Math.round((Number(s.lengthFrames) / 24) * 10) / 10 : undefined;
    sortie.push({ id: p.id, genre, nom, url: `/api/studio/media/${p.id}`, date: p.created_at, ...(dureeS ? { dureeS } : {}) });
  }
  return sortie;
}

// ---------------------------------------------------------------------------------------------------------------------
// Assistant

/** Commandes de montage que le LLM peut demander ; le navigateur les traduit en opérations FreeCut. */
export const COMMANDES = ['texte', 'deplacer', 'supprimer', 'couper', 'raccourcirDebut', 'raccourcirFin', 'volume', 'transition', 'ajouterClip', 'modifier'] as const;
export type NomCommande = (typeof COMMANDES)[number];
export type Commande = Record<string, unknown> & { commande: NomCommande };

/** Actions d'IA exécutées par du code (analyses côté serveur, puis commandes calculées côté navigateur). */
export const ACTIONS = ['silences', 'sous_titres', 'rythme', 'generer_video', 'generer_image', 'generer_musique'] as const;
export type NomAction = (typeof ACTIONS)[number];
export type Action = Record<string, unknown> & { type: NomAction };

export interface ReponseAssistant {
  reponse: string;
  commandes: Commande[];
  actions: Action[];
}

export const MAX_COMMANDES = 200;

export const SYSTEME_ASSISTANT = `Tu es l'assistant de montage du Mode Studio de Nexora Creative, un éditeur vidéo multipiste.
On te donne la demande de la personne (en français) et l'état de sa timeline en JSON : images par seconde, pistes, éléments
(id, type, piste, debutS, dureeS, nom, texte), médias importés (mediaId, nom, type, dureeS), tête de lecture et sélection.
Tous les temps sont en SECONDES sur la timeline.

Réponds UNIQUEMENT par un objet JSON :
{"reponse": "une ou deux phrases en français qui disent ce que tu fais", "commandes": [...], "actions": [...]}

Commandes possibles (champ "commande") :
- texte {texte, debutS, dureeS, taille?, couleur? "#rrggbb", gras? booléen, position? "haut"|"milieu"|"bas", piste?}
- deplacer {id, debutS, piste?}
- supprimer {ids: [...]}
- couper {id, aS}  (coupe l'élément à l'instant aS de la timeline)
- raccourcirDebut {id, s}  et  raccourcirFin {id, s}  (enlève s secondes au début ou à la fin)
- volume {id, db}  (de -60 à 12 ; 0 = volume d'origine)
- transition {gaucheId, droiteId, style? "fade"|"dissolve"|"wipe"|"slide"|"iris"|"glitch"|"lightLeakBurn", dureeS?}
- ajouterClip {mediaId, debutS, piste?, dureeS?}
- modifier {id, champs: {...}}  (pour un texte : text, color, fontSize, fontWeight, textAlign ; pour un clip : volume, label)

Actions d'IA possibles (champ "type"), quand la demande les appelle :
- silences {ids?: [...]}  coupe les silences des clips (tous les clips audio/vidéo si ids est absent)
- sous_titres {ids?: [...]}  transcrit les clips et pose les sous-titres sur une piste dédiée
- rythme {musiqueId?: "id d'un élément audio"}  recale les coupes des clips vidéo sur les temps de la musique
- generer_video {intention, duree?: 5|10, format?: "16:9"|"9:16"|"1:1"}  crée un plan avec MiniMax H3, posé à la tête de lecture
- generer_image {intention, format?}  crée une image avec Qwen-Image, posée à la tête de lecture
- generer_musique {envie, dureeS?}  compose une musique avec MiniMax-Music3, posée sous la timeline

Règles : n'utilise que des id présents dans l'état ; ne fais que ce qui est demandé ; si la demande est floue, ne
renvoie aucune commande et pose une question dans "reponse". Plusieurs commandes s'appliquent dans l'ordre donné.`;

const nombre = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? v : undefined);

/** Valide la réponse du LLM : commandes et actions connues seulement, temps finis, texte borné. */
export function lireReponseAssistant(o: unknown): ReponseAssistant {
  const b = (o ?? {}) as Record<string, unknown>;
  const reponse = typeof b.reponse === 'string' && b.reponse.trim() ? b.reponse.trim().slice(0, 1200) : 'C’est fait.';
  const commandes = (Array.isArray(b.commandes) ? b.commandes : [])
    .filter((c): c is Commande => !!c && typeof c === 'object' && (COMMANDES as readonly string[]).includes((c as any).commande))
    .filter((c) => ['debutS', 'dureeS', 'aS', 's', 'db'].every((k) => c[k] === undefined || nombre(c[k]) !== undefined))
    .slice(0, MAX_COMMANDES);
  const actions = (Array.isArray(b.actions) ? b.actions : [])
    .filter((a): a is Action => !!a && typeof a === 'object' && (ACTIONS as readonly string[]).includes((a as any).type))
    .slice(0, 6);
  return { reponse, commandes, actions };
}

export interface DemandeAssistant {
  demande: string;
  etat: unknown;
  historique: { role: 'user' | 'assistant'; content: string }[];
}

export function lireDemandeAssistant(b: unknown): DemandeAssistant {
  const o = (b ?? {}) as Record<string, unknown>;
  const demande = typeof o.demande === 'string' ? o.demande.trim() : '';
  if (!demande) throw new Error('Dis ce que tu veux faire sur ton montage.');
  if (demande.length > 2000) throw new Error('Demande trop longue (2 000 caractères au plus).');
  const etat = JSON.stringify(o.etat ?? {});
  if (etat.length > 120_000) throw new Error('Timeline trop grande pour l’assistant.');
  const historique = (Array.isArray(o.historique) ? o.historique : [])
    .filter((m: any) => (m?.role === 'user' || m?.role === 'assistant') && typeof m?.content === 'string')
    .slice(-8)
    .map((m: any) => ({ role: m.role, content: String(m.content).slice(0, 1200) }));
  return { demande, etat: o.etat ?? {}, historique };
}

export async function demanderAssistant(d: DemandeAssistant, llm: ClientLlm | null): Promise<ReponseAssistant> {
  if (!llm) return { reponse: 'L’assistant n’est pas disponible : aucun modèle de langage n’est configuré.', commandes: [], actions: [] };
  const texte = await llm.completer('assistant', [
    { role: 'system', content: avecCompetences('assistant', SYSTEME_ASSISTANT) },
    ...d.historique,
    { role: 'user', content: `État de la timeline :\n${JSON.stringify(d.etat)}\n\nDemande : ${d.demande}` },
  ], { json: true, temperature: 0.2, maxTokens: 4000 });
  return lireReponseAssistant(lireJson(texte));
}

// ---------------------------------------------------------------------------------------------------------------------
// Silences

export interface Plage { debutS: number; finS: number }

/** Lit la sortie stderr de `ffmpeg -af silencedetect` : les plages de silence, en secondes de la source. */
export function lireSilences(stderr: string, dureeS?: number): Plage[] {
  const plages: Plage[] = [];
  let debut: number | null = null;
  for (const ligne of stderr.split('\n')) {
    const d = /silence_start:\s*(-?[\d.]+)/.exec(ligne);
    if (d) { debut = Math.max(0, Number(d[1])); continue; }
    const f = /silence_end:\s*([\d.]+)/.exec(ligne);
    if (f && debut !== null) { plages.push({ debutS: debut, finS: Number(f[1]) }); debut = null; }
  }
  if (debut !== null && dureeS && dureeS > debut) plages.push({ debutS: debut, finS: dureeS });
  return plages;
}

export function argsSilences(fichier: string, seuilDb = -35, minS = 0.45): string[] {
  return ['-hide_banner', '-nostats', '-i', fichier, '-vn', '-af', `silencedetect=noise=${seuilDb}dB:d=${minS}`, '-f', 'null', '-'];
}

/** Garde une marge de parole autour de chaque coupe pour ne pas mordre les mots. */
export function silencesAvecMarge(plages: Plage[], margeS = 0.12): Plage[] {
  return plages
    .map((p) => ({ debutS: Math.round((p.debutS + margeS) * 1000) / 1000, finS: Math.round((p.finS - margeS) * 1000) / 1000 }))
    .filter((p) => p.finS - p.debutS >= 0.2);
}

// ---------------------------------------------------------------------------------------------------------------------
// Temps forts d'une musique

export const TAUX_RYTHME = 11025;
const FENETRE = 1024;
const SAUT = 256;

export function argsPcm(fichier: string, taux = TAUX_RYTHME): string[] {
  return ['-v', 'error', '-i', fichier, '-vn', '-ac', '1', '-ar', String(taux), '-f', 'f32le', '-'];
}

/**
 * Tempo et temps d'une musique : enveloppe d'attaques (hausse de l'énergie logarithmique par trame), tempo par
 * autocorrélation entre 70 et 180 BPM, phase qui maximise l'énergie des attaques sur la grille, chaque temps recalé sur
 * le pic d'attaque voisin.
 */
export function detecterTemps(pcm: Float32Array, taux = TAUX_RYTHME): { bpm: number; temps: number[] } {
  const n = Math.floor((pcm.length - FENETRE) / SAUT);
  if (n < 32) return { bpm: 0, temps: [] };
  const energie = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let e = 0;
    for (let j = 0; j < FENETRE; j++) { const v = pcm[i * SAUT + j]; e += v * v; }
    energie[i] = Math.log1p(1000 * e / FENETRE);
  }
  const attaque = new Float64Array(n);
  for (let i = 1; i < n; i++) attaque[i] = Math.max(0, energie[i] - energie[i - 1]);
  const trameS = SAUT / taux;
  const lagMin = Math.round(60 / 180 / trameS);
  const lagMax = Math.round(60 / 70 / trameS);
  let meilleurLag = 0, meilleur = -1;
  for (let lag = lagMin; lag <= lagMax; lag++) {
    let s = 0;
    for (let i = lag; i < n; i++) s += attaque[i] * attaque[i - lag];
    // Légère préférence pour les tempos autour de 120 BPM (évite de doubler ou de diviser par deux le tempo).
    const bpm = 60 / (lag * trameS);
    s *= Math.exp(-0.5 * Math.log2(bpm / 120) ** 2);
    if (s > meilleur) { meilleur = s; meilleurLag = lag; }
  }
  if (!meilleurLag) return { bpm: 0, temps: [] };
  let phase = 0, meilleurePhase = -1;
  for (let p = 0; p < meilleurLag; p++) {
    let s = 0;
    for (let i = p; i < n; i += meilleurLag) s += attaque[i];
    if (s > meilleurePhase) { meilleurePhase = s; phase = p; }
  }
  // Suivi : chaque temps est cherché une période après le pic précédent, ce qui absorbe l'erreur d'une trame sur la
  // période (sinon la grille dérive). Une attaque est vue à la trame dont la fenêtre se termine sur elle.
  const pics: number[] = [];
  const rayon = Math.max(1, Math.round(meilleurLag / 6));
  for (let attendu = phase; attendu < n;) {
    let pic = attendu;
    for (let k = Math.max(0, attendu - rayon); k <= Math.min(n - 1, attendu + rayon); k++) if (attaque[k] > attaque[pic]) pic = k;
    if (pics.length && pic <= pics[pics.length - 1]) pic = attendu;
    pics.push(pic);
    attendu = pic + meilleurLag;
  }
  const temps = pics.map((pic) => Math.round((pic * trameS + FENETRE / taux) * 1000) / 1000);
  const periodeS = temps.length > 1 ? (temps[temps.length - 1] - temps[0]) / (temps.length - 1) : meilleurLag * trameS;
  return { bpm: Math.round((60 / periodeS) * 10) / 10, temps };
}

// ---------------------------------------------------------------------------------------------------------------------
// Transcription

export interface MotTranscrit { mot: string; debutS: number; finS: number }
export interface PhraseTranscrite { texte: string; debutS: number; finS: number; mots: MotTranscrit[] }
export interface Transcription { langue: string; phrases: PhraseTranscrite[] }
export interface LigneSousTitre { texte: string; debutS: number; finS: number }

/** Lit le JSON écrit par transcrire.py ; jette les entrées mal formées. */
export function lireTranscription(texte: string): Transcription {
  const o = JSON.parse(texte) as { langue?: unknown; phrases?: unknown };
  const phrases = (Array.isArray(o.phrases) ? o.phrases : [])
    .map((p: any) => ({
      texte: String(p?.texte ?? '').trim(),
      debutS: Number(p?.debutS),
      finS: Number(p?.finS),
      mots: (Array.isArray(p?.mots) ? p.mots : [])
        .map((m: any) => ({ mot: String(m?.mot ?? '').trim(), debutS: Number(m?.debutS), finS: Number(m?.finS) }))
        .filter((m: MotTranscrit) => m.mot && Number.isFinite(m.debutS) && Number.isFinite(m.finS)),
    }))
    .filter((p: PhraseTranscrite) => p.texte && Number.isFinite(p.debutS) && Number.isFinite(p.finS) && p.finS > p.debutS);
  return { langue: typeof o.langue === 'string' ? o.langue : '', phrases };
}

/**
 * Sous-titres lisibles : une phrase longue est découpée en lignes de 42 caractères au plus, chaque ligne gardant les
 * temps de ses mots (sans mots, la phrase reste entière).
 */
export function decouperSousTitres(t: Transcription, maxCar = 42): LigneSousTitre[] {
  const lignes: LigneSousTitre[] = [];
  for (const p of t.phrases) {
    if (!p.mots.length || p.texte.length <= maxCar) { lignes.push({ texte: p.texte, debutS: p.debutS, finS: p.finS }); continue; }
    let courant: MotTranscrit[] = [];
    const vider = () => {
      if (!courant.length) return;
      lignes.push({ texte: courant.map((m) => m.mot).join(' ').replace(/\s+([,.!?;:»])/g, '$1'), debutS: courant[0].debutS, finS: courant[courant.length - 1].finS });
      courant = [];
    };
    for (const m of p.mots) {
      const longueur = courant.map((x) => x.mot).join(' ').length + m.mot.length + 1;
      if (courant.length && longueur > maxCar) vider();
      courant.push(m);
    }
    vider();
  }
  return lignes;
}
