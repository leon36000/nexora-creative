/**
 * Métriques de montage SUR L'EDITPLAN, en code, sans GPU ni rendu (recherche/14 §5). Chacune rend un score 0-1 et une
 * liste d'écarts typés avec un indice de correction ; le composite = porte × moyenne pondérée. Gratuit, déterministe.
 */
import { type EditPlan, type Violation, FONDU_AUDIO_MS_MIN, lignedeTemps, validerEditPlan } from './editplan.js';
import { BANDES, COUPE_MIN_S, type Brief, FENETRE_ENERGIE_S, energieA } from './types.js';
import { devisCredits, tarifDepuisEnv } from '../credits.js';

export interface Ecart { metrique: string; clip?: string; gravite: 'bloquant' | 'majeur' | 'mineur'; message: string; indice: string }
export interface Metrique { score: number; detail: Record<string, number | string>; ecarts: Ecart[] }
export interface RapportMetriques {
  porte: boolean;
  porteErreurs: Violation[];
  metriques: Record<'rythme' | 'battues' | 'doublons' | 'texte' | 'audio', Metrique>;
  /** 0-1 sans le juge : porte × moyenne pondérée. */
  composite: number;
  credits: number;
  ecarts: Ecart[];
}

export const POIDS = { rythme: 0.3, battues: 0.2, doublons: 0.15, texte: 0.15, audio: 0.2 } as const;
const clamp = (x: number) => Math.max(0, Math.min(1, x));

/** Corrélation de Spearman (rangs moyens pour les ex æquo). */
export function spearman(a: number[], b: number[]): number {
  const n = Math.min(a.length, b.length);
  if (n < 3) return 0;
  const rangs = (v: number[]) => {
    const idx = v.slice(0, n).map((x, i) => [x, i] as const).sort((p, q) => p[0] - q[0]);
    const r = new Array<number>(n);
    for (let i = 0; i < n;) { let j = i; while (j + 1 < n && idx[j + 1][0] === idx[i][0]) j++; for (let k = i; k <= j; k++) r[idx[k][1]] = (i + j) / 2; i = j + 1; }
    return r;
  };
  const x = rangs(a), y = rangs(b);
  const mx = x.reduce((s, v) => s + v, 0) / n, my = y.reduce((s, v) => s + v, 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; }
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : 0;
}

function coupesS(plan: EditPlan): number[] {
  const { debuts } = lignedeTemps(plan);
  return debuts.slice(1).map((d) => d / plan.fps);
}

export function metriqueRythme(plan: EditPlan, b: Brief): Metrique {
  const { total } = lignedeTemps(plan);
  const [mini, maxi] = BANDES[b.genre];
  const durees = plan.video.map((c) => c.duree_f / plan.fps);
  const ecarts: Ecart[] = [];
  const dansBande = durees.filter((d) => d >= mini - 0.05 && d <= maxi + 0.05).length / durees.length;
  durees.forEach((d, i) => {
    if (d < COUPE_MIN_S - 1e-6) ecarts.push({ metrique: 'rythme', clip: plan.video[i].id, gravite: 'majeur', message: `plan de ${d.toFixed(2)} s : aucune coupe sous ${COUPE_MIN_S} s`, indice: `allonge ${plan.video[i].id} à au moins ${Math.ceil(COUPE_MIN_S * plan.fps)} images ou fusionne-le avec un voisin` });
    else if (d > maxi + 0.5) ecarts.push({ metrique: 'rythme', clip: plan.video[i].id, gravite: 'mineur', message: `plan de ${d.toFixed(1)} s : au-dessus de la bande du genre (${mini}-${maxi} s)`, indice: `coupe ${plan.video[i].id} en deux plans ou raccourcis-le` });
  });
  // Densité de coupes par fenêtre de 2 s contre l'énergie moyenne de la fenêtre.
  const energie = b.musique?.energie ?? [];
  const T = total / plan.fps;
  const dens: number[] = [], en: number[] = [];
  const cs = coupesS(plan);
  for (let t = 0; t + 2 <= T + 1e-6; t += 2) {
    dens.push(cs.filter((c) => c >= t && c < t + 2).length);
    let s = 0; for (let k = 0; k < 4; k++) s += energieA(energie, t + k * FENETRE_ENERGIE_S); en.push(s / 4);
  }
  const rho = energie.length ? spearman(dens, en) : 0;
  const suit = energie.length ? clamp((rho + 1) / 2) : 0.5;
  if (energie.length && rho < 0.2) ecarts.push({ metrique: 'rythme', gravite: 'majeur', message: `les coupes ne suivent pas l’énergie (corrélation ${rho.toFixed(2)})`, indice: 'plans plus courts là où l’énergie monte (> 0,66), plus longs dans les creux' });
  // Variété : un montage à durée constante est plat.
  const moy = durees.reduce((s, v) => s + v, 0) / durees.length;
  const cv = Math.sqrt(durees.reduce((s, v) => s + (v - moy) ** 2, 0) / durees.length) / moy;
  const variete = clamp(cv / 0.35);
  const score = energie.length ? 0.45 * suit + 0.4 * dansBande + 0.15 * variete : 0.7 * dansBande + 0.3 * variete;
  return { score: clamp(score), detail: { spearman: Math.round(rho * 100) / 100, dans_la_bande: Math.round(dansBande * 100) / 100, variete: Math.round(variete * 100) / 100, plans: durees.length }, ecarts };
}

export function metriqueBattues(plan: EditPlan, b: Brief): Metrique {
  const battues = b.musique?.battues_s ?? [];
  if (!battues.length || !plan.audio.musique) return { score: 0.5, detail: { sans_grille: 1 }, ecarts: [] };
  const tol = Math.max(0.06, 1 / plan.fps);
  const cs = coupesS(plan);
  const ecarts: Ecart[] = [];
  let ok = 0;
  cs.forEach((c, i) => {
    const plusProche = battues.reduce((m, x) => (Math.abs(x - c) < Math.abs(m - c) ? x : m), battues[0]);
    if (Math.abs(plusProche - c) <= tol + 1e-6) ok++;
    else ecarts.push({ metrique: 'battues', clip: plan.video[i + 1].id, gravite: 'mineur', message: `coupe à ${c.toFixed(2)} s à ${Math.round(Math.abs(plusProche - c) * 1000)} ms du temps fort le plus proche`, indice: `décale le début de ${plan.video[i + 1].id} à l’image ${Math.round(plusProche * plan.fps)}` });
  });
  const part = cs.length ? ok / cs.length : 0;
  return { score: clamp(part / 0.7), detail: { part_sur_battue: Math.round(part * 100) / 100, tolerance_ms: Math.round(tol * 1000) }, ecarts: ecarts.slice(0, 8) };
}

export function metriqueDoublons(plan: EditPlan): Metrique {
  const ecarts: Ecart[] = [];
  const intervalles = plan.video.map((c) => ({ id: c.id, src: c.src, a: c.entree_f, b: c.entree_f + Math.round(c.duree_f * (c.rampe ? (c.rampe.de + c.rampe.a) / 2 : c.vitesse)) }));
  let doubles = 0;
  for (let i = 0; i < intervalles.length; i++) for (let j = i + 1; j < intervalles.length; j++) {
    const x = intervalles[i], y = intervalles[j];
    if (x.src !== y.src) continue;
    const inter = Math.min(x.b, y.b) - Math.max(x.a, y.a);
    if (inter > 0.5 * Math.min(x.b - x.a, y.b - y.a)) { doubles++; ecarts.push({ metrique: 'doublons', clip: y.id, gravite: 'majeur', message: `${y.id} montre les mêmes images de ${y.src} que ${x.id}`, indice: `change l’entrée de ${y.id} (autre partie de ${y.src}) ou utilise une autre source` }); }
  }
  // Même source deux plans de suite : monotone.
  let suite = 0;
  for (let i = 1; i < plan.video.length; i++) if (plan.video[i].src === plan.video[i - 1].src) suite++;
  const score = clamp(1 - doubles / plan.video.length * 2 - suite / plan.video.length);
  return { score, detail: { doublons: doubles, memes_sources_consecutives: suite }, ecarts: ecarts.slice(0, 8) };
}

export function metriqueTexte(plan: EditPlan, b?: Brief): Metrique {
  const ecarts: Ecart[] = [];
  let bons = 0;
  plan.textes.forEach((t, i) => {
    const sec = t.duree_f / plan.fps;
    const cps = [...t.texte.replace(/\n/g, ' ')].length / sec;
    const pb: string[] = [];
    if (cps > 17) pb.push(`${cps.toFixed(0)} caractères/s (max 17)`);
    if (sec < 1) pb.push(`${sec.toFixed(1)} s à l’écran (min 1 s)`);
    if (t.taille_pct < 4) pb.push(`hauteur ${t.taille_pct} % (min 4 %)`);
    const chevauche = plan.textes.some((u, j) => j !== i && u.debut_f < t.debut_f + t.duree_f && t.debut_f < u.debut_f + u.duree_f);
    if (chevauche) pb.push('chevauche un autre texte');
    if (pb.length) ecarts.push({ metrique: 'texte', gravite: 'majeur', message: `texte « ${t.texte.slice(0, 24)} » : ${pb.join(', ')}`, indice: `duree_f ≥ ${Math.ceil(Math.max(1, [...t.texte].length / 15) * plan.fps)} et pas de chevauchement` }); else bons++;
  });
  let couverture = 1;
  if (b?.textes_imposes.length) {
    const presents = b.textes_imposes.filter((x) => plan.textes.some((t) => t.texte.replace(/\s+/g, ' ').trim() === x.replace(/\s+/g, ' ').trim())).length;
    couverture = presents / b.textes_imposes.length;
    if (couverture < 1) ecarts.push({ metrique: 'texte', gravite: 'bloquant', message: `${b.textes_imposes.length - presents} texte(s) imposé(s) absent(s) ou modifié(s)`, indice: `pose mot pour mot : ${b.textes_imposes.map((x) => `« ${x} »`).join(' ; ')}` });
  }
  const lisible = plan.textes.length ? bons / plan.textes.length : (b?.textes_imposes.length ? 0 : 1);
  return { score: clamp(lisible * couverture), detail: { lisibles: bons, textes: plan.textes.length, couverture: Math.round(couverture * 100) / 100 }, ecarts };
}

export function metriqueAudio(plan: EditPlan, b?: Brief): Metrique {
  const a = plan.audio, ecarts: Ecart[] = [];
  const controles: [string, boolean, string, string][] = [];
  const attendu = !!b?.musique;
  controles.push(['musique', attendu ? !!a.musique : true, 'une musique est fournie mais absente du plan', 'ajoute audio.musique avec la piste fournie']);
  if (a.musique) {
    controles.push(['gain', a.voix.length ? a.musique.gain_db <= -3 && a.musique.gain_db >= -24 : a.musique.gain_db >= -24 && a.musique.gain_db <= 6, `gain musique ${a.musique.gain_db} dB hors de la plage (−24 à −3 sous une voix)`, 'gain_db entre −12 et −6']);
    controles.push(['fondu_fin', a.musique.fondu_out_f >= Math.floor(plan.fps * 0.5), 'pas de fondu de sortie de la musique (≥ 0,5 s)', `fondu_out_f = ${Math.round(plan.fps * 1.5)}`]);
  }
  controles.push(['cible', Math.abs(a.cible_lufs - -14) <= 1, `cible ${a.cible_lufs} LUFS : −14 ± 1 pour la diffusion en ligne`, 'cible_lufs = −14']);
  controles.push(['crete', a.crete_db <= -1, `crête ${a.crete_db} dB : −1 dBTP au plus`, 'crete_db = −1']);
  controles.push(['fondu_30ms', a.fondu_coupe_ms >= FONDU_AUDIO_MS_MIN, 'fondu audio < 30 ms aux coupes', 'fondu_coupe_ms = 30']);
  if (a.voix.length) controles.push(['ducking', a.ducking.actif && a.ducking.profondeur_db >= 8, 'musique sous la voix : ducking d’au moins 8 dB', 'ducking = {"actif": true, "profondeur_db": 10}']);
  let ok = 0;
  for (const [nom, bon, msg, indice] of controles) if (bon) ok++; else ecarts.push({ metrique: 'audio', gravite: nom === 'musique' ? 'majeur' : 'mineur', message: msg, indice });
  return { score: ok / controles.length, detail: { controles: controles.length, reussis: ok }, ecarts };
}

/** Coût en crédits des plans à tourner demandés par le plan (le montage lui-même ne dépense rien). */
export function coutCredits(plan: EditPlan, env: NodeJS.ProcessEnv = process.env): number {
  const tarif = tarifDepuisEnv(env);
  return plan.generations.reduce((n, g) => n + (g.moteur === 'h3' ? devisCredits({ videoModel: 'h3', lengthFrames: g.duree_s === 10 ? 244 : 124 }, tarif) : g.moteur === 'qwen' ? 3 : 8), 0);
}

export function mesurer(plan: unknown, b: Brief): RapportMetriques {
  const inventaire: Record<string, { duree_s: number }> = {};
  for (const c of b.clips) inventaire[c.id] = { duree_s: c.duree_s };
  if (b.musique) inventaire[b.musique.id] = { duree_s: b.musique.duree_s };
  if (b.voix) inventaire[b.voix.id] = { duree_s: b.voix.duree_s };
  const v = validerEditPlan(plan, { inventaire, duree_cible_s: b.duree_cible_s });
  const vide = (): Metrique => ({ score: 0, detail: {}, ecarts: [] });
  if (!v.ok || !v.plan) {
    return { porte: false, porteErreurs: v.erreurs, metriques: { rythme: vide(), battues: vide(), doublons: vide(), texte: vide(), audio: vide() }, composite: 0, credits: 0, ecarts: v.erreurs.map((e) => ({ metrique: 'validite', gravite: 'bloquant' as const, message: `${e.chemin} : ${e.message}`, indice: e.indice ?? e.regle })) };
  }
  const p = v.plan;
  const metriques = { rythme: metriqueRythme(p, b), battues: metriqueBattues(p, b), doublons: metriqueDoublons(p), texte: metriqueTexte(p, b), audio: metriqueAudio(p, b) };
  const composite = (Object.keys(POIDS) as (keyof typeof POIDS)[]).reduce((s, k) => s + POIDS[k] * metriques[k].score, 0);
  const ecarts = Object.values(metriques).flatMap((m) => m.ecarts).sort((x, y) => ordre(x.gravite) - ordre(y.gravite));
  return { porte: true, porteErreurs: [], metriques, composite: Math.round(composite * 10000) / 10000, credits: coutCredits(p), ecarts };
}
const ordre = (g: Ecart['gravite']) => (g === 'bloquant' ? 0 : g === 'majeur' ? 1 : 2);
