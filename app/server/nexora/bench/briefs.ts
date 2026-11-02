/**
 * 12 briefs synthétiques du banc de montage (recherche/14 §9) : 4 genres × 3 combinaisons format/durée, inventaire de
 * clips et musique PRÉ-ANALYSÉS générés de façon déterministe (graine fixe) : aucun GPU, aucun média réel.
 * Partition : 6 apprentissage, 3 validation, 3 test scellé. Rien n'est ajusté d'après le test.
 */
import type { Format, Genre } from '../montage/editplan.js';
import type { Brief, ClipInfo, MusiqueInfo, VoixInfo } from '../montage/types.js';

function prng(graine: number) {
  let a = graine >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const arr = (x: number, n = 3) => Math.round(x * 10 ** n) / 10 ** n;

const THEMES: Record<string, { sujet: string; plans: string[]; textes: string[] }> = {
  cafe: { sujet: 'le café de quartier « Chez Odette »', plans: ['grain de café en gros plan', 'barista qui verse un latte', 'vitrine au petit matin', 'tasse fumante sur le comptoir', 'client qui sourit', 'pâtisseries sous cloche', 'moulin à café', 'terrasse ensoleillée', 'mains qui servent', 'enseigne lumineuse', 'vue du comptoir', 'sac de grains'], textes: ['Le vrai café du quartier.', 'Torréfié chaque matin.', 'Chez Odette, 12 rue des Lilas'] },
  velo: { sujet: 'un vélo électrique pliable', plans: ['vélo qui roule en ville', 'pliage en 10 secondes', 'batterie qu’on retire', 'cycliste sur un pont', 'détail du moteur', 'vélo dans un train', 'rangement sous un bureau', 'descente d’une colline', 'freins en gros plan', 'écran de bord', 'portrait du cycliste', 'coucher de soleil'], textes: ['Plie. Roule. Repars.', '80 km d’autonomie.', 'Essayez-le cette semaine'] },
  jeu: { sujet: 'le jeu de stratégie « Frontière »', plans: ['armée qui traverse une plaine', 'forteresse sous la pluie', 'explosion de catapulte', 'carte stratégique', 'cavalerie au galop', 'roi sur son trône', 'navire en pleine tempête', 'archers en rang', 'ville en flammes', 'dragon dans les nuages', 'duel au sommet', 'étendard qui flotte'], textes: ['Chaque frontière a un prix.', 'Précommandez maintenant'] },
  appli: { sujet: 'une appli de budget pour les familles', plans: ['téléphone dans la main', 'famille à la cuisine', 'graphique qui monte', 'facture qu’on scanne', 'enfants qui comptent la tirelire', 'notification de dépense', 'écran d’accueil', 'couple qui planifie', 'courses au marché', 'carte de paiement', 'objectif d’épargne atteint', 'bureau à la maison'], textes: ['Votre budget, enfin clair.', 'Zéro tableau. Zéro stress.', 'Essai gratuit 30 jours'] },
};

/** Courbe d'énergie typique par genre (0-1 par 0,5 s) : ouverture, montée, climax, retombée. */
function courbe(genre: Genre, n: number, r: () => number): number[] {
  const profil: Record<Genre, [number, number][]> = {
    pub: [[0, 0.35], [0.2, 0.55], [0.6, 0.85], [0.85, 0.7], [1, 0.3]],
    'bande-annonce': [[0, 0.15], [0.25, 0.4], [0.55, 0.7], [0.8, 1], [0.92, 1], [1, 0.2]],
    explicatif: [[0, 0.4], [0.5, 0.5], [1, 0.4]],
    social: [[0, 0.8], [0.5, 0.9], [1, 0.75]],
  };
  const p = profil[genre];
  return Array.from({ length: n }, (_, i) => {
    const x = i / Math.max(1, n - 1);
    let k = 0; while (k < p.length - 2 && x > p[k + 1][0]) k++;
    const u = (x - p[k][0]) / (p[k + 1][0] - p[k][0] || 1);
    return arr(Math.max(0, Math.min(1, p[k][1] + (p[k + 1][1] - p[k][1]) * u + (r() - 0.5) * 0.18)), 3);
  });
}

function fabriquer(id: string, partition: Brief['partition'], genre: Genre, format: Format, duree: number, theme: keyof typeof THEMES, graine: number, o: { voix?: boolean; fps?: 24 | 25 | 30 } = {}): Brief {
  const r = prng(graine);
  const t = THEMES[theme];
  const n = 8 + Math.floor(r() * 5);
  const clips: ClipInfo[] = Array.from({ length: n }, (_, i) => {
    const d = arr(genre === 'bande-annonce' ? 4 + r() * 8 : 3.5 + r() * 8.5, 2);
    const coupes = r() < 0.3 ? [arr(d * (0.35 + r() * 0.3), 2)] : [];
    return { id: `m${i + 1}`, duree_s: d, description: t.plans[i % t.plans.length], ...(coupes.length ? { coupes_s: coupes } : {}) };
  });
  const bpm = Math.round(genre === 'explicatif' ? 92 + r() * 18 : genre === 'social' ? 112 + r() * 24 : 100 + r() * 36);
  const periode = 60 / bpm, phase = arr(0.1 + r() * 0.3, 2);
  const dureeMus = duree + 6;
  const battues: number[] = [];
  for (let x = phase; x < dureeMus; x += periode) battues.push(arr(x));
  const musique: MusiqueInfo = { id: 'musique', duree_s: dureeMus, bpm, battues_s: battues, energie: courbe(genre, Math.ceil(dureeMus * 2), r) };
  let voix: VoixInfo | undefined;
  if (o.voix) {
    const mots: [number, number][] = [];
    for (let x = 0.5; x < duree - 1.5;) { const a = x, b = arr(a + 0.2 + r() * 0.35, 2); mots.push([arr(a, 2), b]); x = b + (r() < 0.15 ? 0.5 + r() * 0.6 : 0.04 + r() * 0.12); }
    voix = { id: 'voix', duree_s: arr(mots[mots.length - 1][1] + 0.5, 1), mots };
  }
  const imposes = (genre === 'social' ? t.textes.slice(0, 2) : genre === 'explicatif' ? t.textes.slice(0, 3) : t.textes.slice(0, Math.min(3, t.textes.length)));
  return {
    id, partition, genre, format, duree_cible_s: duree, fps: o.fps ?? 24,
    enonce: `${{ pub: 'Publicité', 'bande-annonce': 'Bande-annonce', explicatif: 'Vidéo explicative', social: 'Vidéo courte pour les réseaux' }[genre]} de ${duree} s pour ${t.sujet}, format ${format}.${genre === 'explicatif' ? ' Une voix off présente les idées.' : ''}`,
    textes_imposes: imposes, clips, musique, ...(voix ? { voix } : {}),
  };
}

export const BRIEFS: Brief[] = [
  fabriquer('pub-a', 'apprentissage', 'pub', '16:9', 30, 'cafe', 101),
  fabriquer('bande-annonce-a', 'apprentissage', 'bande-annonce', '16:9', 45, 'jeu', 102),
  fabriquer('bande-annonce-b', 'apprentissage', 'bande-annonce', '9:16', 30, 'velo', 103),
  fabriquer('explicatif-a', 'apprentissage', 'explicatif', '16:9', 45, 'appli', 104, { voix: true }),
  fabriquer('social-a', 'apprentissage', 'social', '9:16', 15, 'cafe', 105, { fps: 30 }),
  fabriquer('social-b', 'apprentissage', 'social', '9:16', 20, 'jeu', 106, { fps: 30 }),
  fabriquer('pub-b', 'validation', 'pub', '9:16', 20, 'velo', 201),
  fabriquer('bande-annonce-c', 'validation', 'bande-annonce', '16:9', 30, 'jeu', 202),
  fabriquer('explicatif-b', 'validation', 'explicatif', '1:1', 30, 'velo', 203, { voix: true }),
  fabriquer('pub-c', 'test', 'pub', '1:1', 15, 'appli', 301),
  fabriquer('explicatif-c', 'test', 'explicatif', '16:9', 60, 'cafe', 302, { voix: true }),
  fabriquer('social-c', 'test', 'social', '9:16', 30, 'velo', 303, { fps: 30 }),
];
