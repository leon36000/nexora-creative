/**
 * Nexora AI Director, v1 : une idée devient un film de plusieurs plans.
 *   planifier  le LLM cloud écrit un storyboard (plans, caméra, durées) et une bible de continuité (style, personnages,
 *              lieux) ; le code borne et normalise tout ; repli en découpage simple si le LLM échoue.
 *   tourner    chaque plan est réécrit pour H3 (réécrivain validé) puis rendu ; la bible est répétée dans chaque plan
 *              pour garder le même héros, le même lieu, la même lumière.
 *   assembler  quand tous les plans sont rendus, ffmpeg les met bout à bout (H.264 + AAC).
 * L'état vit dans la prise « film » (settings), comme les coupes de scène d'OpenField : un redémarrage reprend.
 */
import { type ClientLlm, lireJson } from './llm.js';

export interface PlanFilm {
  resume: string;
  description: string;
  duree: 5 | 10;
  camera: string;
  /** Le plan prolonge directement le précédent : il part de sa dernière image (H3 en image vers vidéo). */
  suite?: boolean;
  /** Prise de rendu de ce plan, une fois en file. */
  take?: number;
}

export interface Storyboard {
  titre: string;
  bible: { style: string; personnages: { nom: string; description: string }[]; lieux: { nom: string; description: string }[] };
  plans: PlanFilm[];
  dureeTotale: number;
}

export const MAX_PLANS = 12;

const txt = (v: unknown, max = 1200) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const entites = (v: unknown) =>
  (Array.isArray(v) ? v : [])
    .map((e) => ({ nom: txt((e as any)?.nom, 80), description: txt((e as any)?.description, 600) }))
    .filter((e) => e.nom || e.description)
    .slice(0, 8);

export function lireStoryboard(o: unknown, dureeCible: number): Storyboard {
  const b = (o ?? {}) as Record<string, any>;
  const plans: PlanFilm[] = (Array.isArray(b.plans) ? b.plans : [])
    .map((p: any) => ({
      resume: txt(p?.resume, 160),
      description: txt(p?.description),
      duree: (Number(p?.duree) >= 8 ? 10 : 5) as 5 | 10,
      camera: txt(p?.camera, 300),
      suite: p?.suite === true,
    }))
    .filter((p: PlanFilm) => p.description || p.resume)
    .slice(0, MAX_PLANS);
  if (!plans.length) throw new Error('storyboard sans plan');
  plans[0].suite = false;
  for (const p of plans) {
    if (!p.description) p.description = p.resume;
    if (!p.resume) p.resume = p.description.slice(0, 80);
  }
  void dureeCible;
  return {
    titre: txt(b.titre, 120) || 'Sans titre',
    bible: { style: txt(b.bible?.style, 600), personnages: entites(b.bible?.personnages), lieux: entites(b.bible?.lieux) },
    plans,
    dureeTotale: plans.reduce((n, p) => n + p.duree, 0),
  };
}

/** Ce que le réécrivain H3 reçoit pour un plan : la bible complète, puis le plan lui-même. */
export function intentionDuPlan(s: Storyboard, i: number): string {
  const p = s.plans[i];
  const parties = [
    s.bible.style && `Visual style for the whole film: ${s.bible.style}.`,
    ...s.bible.personnages.map((c) => `Character "${c.nom}": ${c.description}.`),
    ...s.bible.lieux.map((l) => `Location "${l.nom}": ${l.description}.`),
    `This is shot ${i + 1} of ${s.plans.length} of the film "${s.titre}". Keep characters, places and light exactly consistent with the descriptions above.`,
    `Shot content: ${p.description}`,
    p.camera && `Camera: ${p.camera}.`,
  ];
  return parties.filter(Boolean).join('\n');
}

function decoupageSimple(intention: string, dureeCible: number): Storyboard {
  const n = Math.max(1, Math.min(MAX_PLANS, Math.round(dureeCible / 5)));
  const cameras = ['wide establishing shot, slow push in', 'medium shot, arc shot at slow speed', 'close-up, static shot', 'low-angle tracking shot'];
  return lireStoryboard(
    {
      titre: intention.slice(0, 60),
      bible: { style: 'Live-action, cinematic', personnages: [], lieux: [] },
      plans: Array.from({ length: n }, (_, i) => ({ resume: `Plan ${i + 1}`, description: intention, duree: 5, camera: cameras[i % cameras.length] })),
    },
    dureeCible,
  );
}

const CONSIGNES = `You are the director of Nexora Creative, an AI film studio whose camera is the MiniMax H3 audio-video model.
Turn the user's idea (often short, in French) into a storyboard for a film of about the requested duration.
Each shot is rendered separately by H3 as a 5 or 10 second clip, so:
- write every shot description so it can be filmed on its own, in English, concrete and visual (subjects, action, light, materials, sound sources);
- put everything that must stay identical across shots in the "bible" (style, characters with precise looks and clothes, places), and reuse the same names;
- vary framing and camera (wide, medium, close-up, low angle, arc shot, tracking shot, push in, static) to tell the story like a real editor;
- prefer 5 s shots; use 10 s only for a continuous action that needs it; the sum of durations should be close to the requested duration;
- set "suite": true on a shot that continues the previous one with no jump in time or place (the same action goes on, e.g. a transformation that keeps unfolding): it will start from the last frame of the previous shot, which keeps subjects identical; use it for at most half of the shots and never on the first;
- the "resume" of each shot is a short French phrase for the user interface.
Answer only with JSON: {"titre": "...", "bible": {"style": "...", "personnages": [{"nom": "...", "description": "..."}], "lieux": [{"nom": "...", "description": "..."}]}, "plans": [{"resume": "...", "description": "...", "duree": 5, "camera": "...", "suite": false}]}`;

export async function planifierFilm(
  d: { intention: string; dureeCible: number },
  llm: ClientLlm | null,
): Promise<{ storyboard: Storyboard; source: 'llm' | 'repli' }> {
  if (llm) {
    for (let essai = 0; essai < 2; essai++) {
      try {
        const brut = await llm.completer(
          'realisation',
          [
            { role: 'system', content: CONSIGNES },
            { role: 'user', content: JSON.stringify({ idee: d.intention, duree_cible_secondes: d.dureeCible }) },
          ],
          { json: true, temperature: 0.8 },
        );
        return { storyboard: lireStoryboard(lireJson(brut), d.dureeCible), source: 'llm' };
      } catch {
        /* nouvel essai, puis repli */
      }
    }
  }
  return { storyboard: decoupageSimple(d.intention, d.dureeCible), source: 'repli' };
}

export interface OptionsAssemblage {
  transition: 'coupe' | 'fondu';
  /** Durée de chaque plan (s), nécessaire au fondu pour placer les transitions. */
  durees: number[];
  /** Durée du fondu enchaîné (s). */
  fondu: number;
}

/**
 * Arguments ffmpeg qui mettent les plans bout à bout (même taille, ré-encodés en H.264 + AAC), en coupe franche ou
 * en fondu enchaîné (xfade pour l'image, acrossfade pour le son).
 */
export function argsAssemblage(fichiers: string[], sortie: string, son: boolean, o?: OptionsAssemblage): string[] {
  const entrees = fichiers.flatMap((f) => ['-i', f]);
  let filtre: string;
  if (o?.transition === 'fondu' && fichiers.length > 1) {
    const d = o.fondu;
    const norm = fichiers.map((_, i) => `[${i}:v:0]fps=24,settb=AVTB,format=yuv420p[n${i}]`);
    const video: string[] = [];
    let cumul = 0;
    let precedent = 'n0';
    for (let i = 1; i < fichiers.length; i++) {
      cumul += o.durees[i - 1];
      const offset = Math.round((cumul - i * d) * 1000) / 1000;
      const sortieV = i === fichiers.length - 1 ? 'v' : `x${i}`;
      video.push(`[${precedent}][n${i}]xfade=transition=fade:duration=${d}:offset=${offset}[${sortieV}]`);
      precedent = sortieV;
    }
    const audio: string[] = [];
    if (son) {
      let pa = '0:a:0';
      for (let i = 1; i < fichiers.length; i++) {
        const sortieA = i === fichiers.length - 1 ? 'a' : `y${i}`;
        audio.push(`[${pa}][${i}:a:0]acrossfade=d=${d}[${sortieA}]`);
        pa = sortieA;
      }
    }
    filtre = [...norm, ...video, ...audio].join(';');
  } else {
    const flux = fichiers.map((_, i) => `[${i}:v:0]${son ? `[${i}:a:0]` : ''}`).join('');
    filtre = `${flux}concat=n=${fichiers.length}:v=1:a=${son ? 1 : 0}[v]${son ? '[a]' : ''}`;
  }
  return [
    '-y', ...entrees,
    '-filter_complex', filtre,
    '-map', '[v]', ...(son ? ['-map', '[a]', '-c:a', 'aac', '-b:a', '192k'] : []),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    sortie,
  ];
}

/** Export professionnel : ProRes 422 HQ 10 bits + PCM, lisible par Premiere, DaVinci Resolve et Final Cut. */
export function argsExport(entree: string, sortie: string, format: 'prores'): string[] {
  void format;
  return ['-y', '-i', entree, '-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le', '-vendor', 'apl0', '-c:a', 'pcm_s16le', sortie];
}

/** Nouvelle version d'un film avec un autre ordre de plans (ou des plans retirés), sans aucun nouveau rendu. */
export function storyboardPourMontage(sb: Storyboard, ordre: number[]): Storyboard {
  if (!ordre.length) throw new Error('un film garde au moins un plan');
  if (new Set(ordre).size !== ordre.length) throw new Error('un plan apparaît deux fois');
  const plans = ordre.map((i) => {
    if (!Number.isInteger(i) || i < 0 || i >= sb.plans.length) throw new Error(`le film n'a pas de plan ${i + 1}`);
    // Les plans sont déjà tournés : l'enchaînement par image ne sert plus qu'au tournage.
    return { ...sb.plans[i], suite: false };
  });
  return { ...sb, plans, dureeTotale: plans.reduce((n, p) => n + p.duree, 0) };
}

/**
 * Nouvelle version d'un film où seul le plan `i` est refait (avec une description ou une caméra retouchées), ainsi
 * que les plans enchaînés qui partaient de son image. Les autres plans gardent leur prise : ils ne sont pas retournés.
 * Ne s'applique qu'au storyboard lu côté serveur (jamais à des numéros de prise venus du navigateur).
 */
export function storyboardPourRefaire(sb: Storyboard, i: number, modif: { description?: string; camera?: string }): Storyboard {
  if (!Number.isInteger(i) || i < 0 || i >= sb.plans.length) throw new Error(`le film n'a pas de plan ${i + 1}`);
  let refaire = false;
  const plans = sb.plans.map((p, k) => {
    if (k === i) refaire = true;
    else if (!p.suite) refaire = false;
    const garde = !(refaire && k >= i);
    const base = { ...p } as PlanFilm & Record<string, unknown>;
    delete base.attente;
    // Un plan gardé garde aussi son contrôle qualité (pas de nouvelle reprise sur une prise déjà acceptée).
    if (!garde) { delete base.take; delete base.corps; delete base.reservation; delete base.controle; delete base.reprises; delete base.controleRefuse; }
    if (k === i) {
      if (modif.description?.trim()) base.description = modif.description.trim().slice(0, 1200);
      if (modif.camera?.trim()) base.camera = modif.camera.trim().slice(0, 300);
    }
    return base as PlanFilm;
  });
  return { ...sb, plans };
}
