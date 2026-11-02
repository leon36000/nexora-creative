/**
 * Graines de la mémoire de montage (recherche/14 §4) : convertit les vraies listes de montage de la maison en
 * exemplaires EditPlan v1 (identifiants anonymisés c1…cn, textes en jetons) sous server/nexora/memoire/segments/.
 *   npx tsx scripts/graines-montage.ts
 * Sources : marketing/creative/video-v3/montage-v3.json (bande-annonce « bataille spatiale », 60 s) et
 * marketing/nexora/refonte-medias/montages/film-surveillance-fr-{16x9,9x16}.json (publicité, 36 s).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { type EditPlan, validerEditPlan } from '../server/nexora/montage/editplan.js';

const racine = join(import.meta.dirname, '../..');
const sortie = join(import.meta.dirname, '../server/nexora/memoire/segments');
const lire = (p: string) => JSON.parse(readFileSync(join(racine, p), 'utf8'));
const FPS = 24;
const f = (s: number) => Math.round(s * FPS);

function ecrire(id: string, meta: Record<string, unknown>, plan: EditPlan) {
  const v = validerEditPlan(plan);
  if (!v.ok) throw new Error(`${id} invalide : ${JSON.stringify(v.erreurs)}`);
  writeFileSync(join(sortie, `${id}.json`), JSON.stringify({ id, version: 1, ...meta, extrait_edl: v.plan }) + '\n');
  console.log(id, v.plan!.video.length, 'plans');
}

// 1) Bande-annonce V3 : plans seuls, ligne de temps continue, sections conservées.
{
  const d = lire('marketing/creative/video-v3/montage-v3.json');
  const sources: EditPlan['sources'] = {};
  const nom = new Map<string, string>();
  const curseur = new Map<string, number>();
  const video: EditPlan['video'] = [];
  let prec = 0;
  for (const s of d.sequence as any[]) {
    const dur = s.fin - prec; prec = s.fin;
    if (!s.plan) continue;
    const cle = s.plan as string;
    if (!nom.has(cle)) nom.set(cle, `c${nom.size + 1}`);
    const src = nom.get(cle)!;
    const duree_f = Math.max(f(0.3), f(dur));
    const entree_f = curseur.get(src) ?? 0;
    curseur.set(src, entree_f + duree_f + 2);
    video.push({ id: `p${video.length + 1}`, src, entree_f, duree_f, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 }, section: s.section, ...(duree_f >= f(1.8) ? { zoom: { de: 1, a: 1.06 } } : {}) });
  }
  for (const [src, fin] of curseur) sources[src] = { kind: 'video', duree_f: fin + f(1) };
  const total = video.reduce((n, p) => n + p.duree_f, 0);
  sources.mus = { kind: 'audio', duree_f: total + f(4) };
  ecrire('seg-bande-annonce-bataille', {
    genre: ['bande-annonce'], format: ['16:9'], etiquette: 'bande_annonce_complete', origine: 'marketing/creative/video-v3/montage-v3.json (film V3, plans seuls)',
    description: 'Bande-annonce de 50 s sur musique d’abord : ouverture lente (1 plan de 3 s), montée à 2-3 s par plan, action à 1,5 s, climax en rafale de 0,4 à 0,9 s, plan final calme. Les coupes tombent sur les coups de la musique ; une source peut resservir plus tard sur une autre partie.',
    mots_cles: ['bande-annonce', 'trailer', 'action', 'film', 'musique', 'rythme', 'climax', 'espace', 'bataille', 'jeu'],
  }, {
    version: 1, fps: FPS, format: '16:9', genre: 'bande-annonce', sources, video,
    audio: { musique: { src: 'mus', entree_f: 0, duree_f: total, gain_db: 0, fondu_in_f: f(0.5), fondu_out_f: f(1.5) }, voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
    textes: [{ texte: '<TEXTE_ACCROCHE>', debut_f: f(18), duree_f: f(2), style: 'titre', position: 'centre', taille_pct: 8 }, { texte: '<TEXTE_TITRE_FINAL>', debut_f: Math.max(0, total - f(4)), duree_f: f(3), style: 'carton', position: 'centre', taille_pct: 9 }],
    generations: [],
  });
}

// 2) Publicité de surveillance : un plan par argument, texte à gauche au bas, carton final.
for (const [fmt, fichier, genre] of [['16:9', 'film-surveillance-fr-16x9.json', 'pub'], ['9:16', 'film-surveillance-fr-9x16.json', 'social']] as const) {
  const d = lire(`marketing/nexora/refonte-medias/montages/${fichier}`);
  const sources: EditPlan['sources'] = {};
  const video: EditPlan['video'] = [];
  (d.segments as any[]).forEach((s, i) => {
    const src = `c${i + 1}`;
    const duree_f = f(s.duree);
    const entree_f = s.carton ? 0 : f(s.debut ?? 0);
    sources[src] = { kind: 'video', duree_f: entree_f + duree_f + f(1) };
    video.push({ id: `p${i + 1}`, src, entree_f, duree_f, vitesse: s.vitesse ?? 1, transition_in: s.fondu && i > 0 ? { type: 'fondu', duree_f: f(s.fondu) } : { type: 'cut', duree_f: 0 }, ...(s.zoom ? { zoom: { de: 1, a: 1 + s.zoom * 2 } } : {}), section: s.carton ? 'carton' : 'argument' });
  });
  const fond = video.reduce((n, p) => n + p.duree_f, 0) - video.reduce((n, p, i) => n + (i > 0 && p.transition_in.type !== 'cut' ? p.transition_in.duree_f : 0), 0);
  sources.mus = { kind: 'audio', duree_f: fond + f(4) };
  // Le dernier fondu raccourcit la séquence : on la garde telle quelle, les textes restent dans ses bornes.
  const textes = (d.textes as any[]).map((t) => ({ texte: String(t.texte).replace(/\n/g, ' ').replace(/[^\s]+/g, (m) => m).replace(/.*/s, '<TEXTE_ARGUMENT>'), debut_f: f(t.debut), duree_f: Math.max(f(1.2), f(t.duree)), style: 'titre' as const, position: fmt === '9:16' ? 'centre' as const : 'bas' as const, taille_pct: fmt === '9:16' ? 4.5 : 6.4 })).filter((t) => t.debut_f + t.duree_f <= fond);
  ecrire(`seg-${genre}-surveillance-${fmt.replace(':', 'x')}`, {
    genre: [genre, ...(fmt === '9:16' ? ['social'] : [])].filter((g, i, a) => a.indexOf(g) === i), format: [fmt], etiquette: 'pub_arguments_et_carton', origine: `marketing/nexora/refonte-medias/montages/${fichier}`,
    description: 'Publicité de 36 s : un plan de 4 à 5 s par argument (zoom lent de 6 %), un texte court par plan en ouverture de plan, fondu enchaîné de 0,4 s avant le carton final de 5,5 s, musique sans voix à pleine échelle puis normalisée à −14 LUFS.',
    mots_cles: ['pub', 'publicité', 'produit', 'service', 'surveillance', 'arguments', 'entreprise', 'carton', 'appel', 'action', 'vertical', 'horizontal'],
  }, {
    version: 1, fps: FPS, format: fmt, genre, sources, video,
    audio: { musique: { src: 'mus', entree_f: 0, duree_f: fond, gain_db: 0, fondu_in_f: f(0.3), fondu_out_f: f(1.4) }, voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
    textes, generations: [],
  });
}

// 3) Explicatif : AUCUNE liste réelle de la maison (écrit à la main d'après la recette) ; marqué comme tel.
{
  const durees = [4.5, 5.5, 4.0, 6.0, 5.0, 5.0]; // 30 s ; un plan par idée, fondu enchaîné entre les idées
  const sources: EditPlan['sources'] = { voix: { kind: 'audio', duree_f: f(31) }, mus: { kind: 'audio', duree_f: f(34) } };
  const video: EditPlan['video'] = durees.map((d, i) => {
    sources[`c${i + 1}`] = { kind: 'video', duree_f: f(d + 3) };
    return { id: `p${i + 1}`, src: `c${i + 1}`, entree_f: f(0.5), duree_f: f(d), vitesse: 1, transition_in: i === 0 ? { type: 'cut' as const, duree_f: 0 } : { type: 'fondu' as const, duree_f: f(0.4) }, zoom: { de: 1, a: 1.05 }, section: i === 0 ? 'accroche' : i === durees.length - 1 ? 'appel' : 'idee' };
  });
  const total = video.reduce((n, p, i) => n + p.duree_f - (i > 0 ? f(0.4) : 0), 0);
  video[video.length - 1].duree_f += total < f(30) ? f(30) - total : 0;
  const fin = video.reduce((n, p, i) => n + p.duree_f - (i > 0 ? f(0.4) : 0), 0);
  ecrire('seg-explicatif-voix-musique', {
    genre: ['explicatif'], format: ['16:9', '1:1'], etiquette: 'explicatif_voix_et_fond', origine: 'écrit à la main d’après memoire/recettes/explicatif.md (aucune liste réelle disponible)',
    description: 'Explicatif de 30 s : une idée par plan de 4 à 6 s, fondus enchaînés de 0,4 s, voix off sur toute la durée avec musique à −14 dB et ducking de 10 dB, texte clé de 2 s au début de chaque idée, appel à l’action en dernier plan.',
    mots_cles: ['explicatif', 'explication', 'tutoriel', 'présentation', 'service', 'voix', 'voix off', 'étapes', 'idées', 'comment'],
  }, {
    version: 1, fps: FPS, format: '16:9', genre: 'explicatif', sources, video,
    audio: { musique: { src: 'mus', entree_f: 0, duree_f: fin, gain_db: -14, fondu_in_f: f(0.5), fondu_out_f: f(1.5) }, voix: [{ src: 'voix', debut_f: f(0.5), entree_f: 0, duree_f: fin - f(1.5), gain_db: 0 }], ducking: { actif: true, profondeur_db: 10 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
    textes: [{ texte: '<TEXTE_ACCROCHE>', debut_f: f(0.5), duree_f: f(3), style: 'titre', position: 'bas', taille_pct: 6 }, { texte: '<TEXTE_IDEE_CLE>', debut_f: f(10), duree_f: f(2.5), style: 'sous-titre', position: 'bas', taille_pct: 5 }, { texte: '<TEXTE_APPEL_ACTION>', debut_f: fin - f(4), duree_f: f(3), style: 'carton', position: 'centre', taille_pct: 8 }],
    generations: [],
  });
}
