/**
 * Liste de montage compacte : ce que le modèle écrit à la place d'un EditPlan complet. Des SECONDES (jamais d'images),
 * une ligne par plan, aucune arithmétique de fps, de fondus audio ni de recouvrement : le code compile la liste en
 * EditPlan v1 (coupes aimantées sur les temps forts, images entières, textes calés sur le temps de lecture, audio par
 * défaut, durée finale exacte). Trois fois moins de jetons qu'un EditPlan, et les erreurs d'arithmétique des petits
 * modèles disparaissent (recherche/14 §12 : le code fait le plancher, le modèle apporte le choix et le texte).
 * Le validateur parle au modèle en secondes, avec la valeur attendue et la réparation.
 */
import { z } from 'zod';
import { type EditPlan, type Violation, framesDe, validerEditPlan } from './editplan.js';
import { BANDES, type Brief, energieA } from './types.js';

export const ListeMontageSchema = z.object({
  plans: z.array(z.object({
    src: z.string().min(1).max(40),
    in: z.number().min(0).max(600).default(0).describe('seconde de la source où le plan commence'),
    dur: z.number().min(0.3).max(30).describe('durée à l’écran, en secondes'),
    tr: z.enum(['cut', 'fondu', 'dip']).default('cut'),
    texte: z.string().max(120).optional().describe('texte posé sur ce plan (≤ 2 lignes, « \\n » entre les lignes)'),
  })).min(2).max(60),
  gain_db: z.number().min(-24).max(0).optional().describe('niveau de la musique, −8 par défaut'),
});
export type ListeMontage = z.infer<typeof ListeMontageSchema>;

const CPS = 15; // caractères par seconde de lecture visés (le validateur de plan accepte 17)
export const DELAI_TEXTE_S = 0.25;
export const TOLERANCE_AIMANT_S = 0.35;

const V = (regle: string, chemin: string, message: string, indice: string): Violation => ({ regle, chemin, message, indice });
const f1 = (x: number) => (Math.round(x * 100) / 100).toString();

/** Plus grand nombre de caractères lisible dans un plan de `dur` secondes. */
export const CPS_MAX = 16.5; // le contrôle de lisibilité du plan en accepte 17
export const maxCaracteres = (dur: number) => Math.max(0, Math.floor(CPS_MAX * (dur - DELAI_TEXTE_S - 0.1)));

/** Contrôle de la liste, en secondes, avec la valeur attendue et la réparation pour chaque violation. */
export function validerListe(brut: unknown, b: Brief): { ok: boolean; erreurs: Violation[]; liste?: ListeMontage } {
  const lu = ListeMontageSchema.safeParse(brut);
  if (!lu.success) {
    return { ok: false, erreurs: lu.error.issues.slice(0, 8).map((i) => V('schema', i.path.join('.') || '(racine)', i.message, 'Forme attendue : {"plans":[{"src":"s1","in":0,"dur":2.4,"tr":"cut","texte":"…"}],"gain_db":-8}')) };
  }
  const l = lu.data;
  const e: Violation[] = [];
  const dureeSrc = new Map(b.clips.map((c) => [c.id, c.duree_s] as const));
  const [mini, maxi] = BANDES[b.genre];
  let somme = 0;
  l.plans.forEach((p, i) => {
    const ch = `plans.${i}`;
    somme += p.dur;
    const d = dureeSrc.get(p.src);
    if (d === undefined) { e.push(V('source_connue', `${ch}.src`, `source inconnue « ${p.src} »`, `Sources permises : ${[...dureeSrc.keys()].join(', ')}.`)); return; }
    if (p.in + p.dur > d + 1e-6) e.push(V('dans_la_source', ch, `${p.src} dure ${f1(d)} s : le plan lit de ${f1(p.in)} à ${f1(p.in + p.dur)} s`, `Mets in ≤ ${f1(Math.max(0, d - p.dur))} ou dur ≤ ${f1(d - p.in)}.`));
    if (i > 0 && l.plans[i - 1].src === p.src) e.push(V('meme_source', `${ch}.src`, `${p.src} deux fois de suite`, 'Intercale une autre source, ou change de passage sans répéter les mêmes images.'));
    if (p.src !== 'carton' && (p.dur < mini - 0.3 || p.dur > maxi + 0.5)) e.push(V('bande_de_duree', `${ch}.dur`, `plan de ${f1(p.dur)} s ; bande du genre ${mini}-${maxi} s`, `Garde dur entre ${mini} et ${maxi}.`));
    if (p.texte) {
      const lignes = p.texte.split('\n');
      // Le texte peut déborder sur les plans suivants jusqu'au prochain texte : la place est la durée jusqu'à lui.
      let place = p.dur, k = i + 1;
      while (k < l.plans.length && !l.plans[k].texte) place += l.plans[k++].dur;
      const max = maxCaracteres(place);
      if (lignes.length > 2 || lignes.some((x) => [...x].length > 42)) e.push(V('texte_lignes', `${ch}.texte`, 'plus de 2 lignes ou ligne de plus de 42 caractères', 'Raccourcis : 2 lignes de 42 caractères au plus.'));
      else if ([...p.texte.replace(/\n/g, ' ')].length > max) e.push(V('texte_trop_long', `${ch}.texte`, `${[...p.texte].length} caractères pour ${f1(place)} s disponibles jusqu'au texte suivant : ${max} au plus`, `Raccourcis le texte à ${max} caractères, ou allonge ce plan à ${f1(p.dur + Math.ceil(([...p.texte].length / CPS_MAX + 0.35 - place) * 10) / 10)} s, ou retire le texte du plan suivant.`));
    }
  });
  // Le code remet les durées à l'échelle (±25 % tolérés) : seul un écart grossier est une erreur du modèle.
  if (Math.abs(somme - b.duree_cible_s) > b.duree_cible_s * 0.25) {
    e.push(V('duree_cible', 'plans', `somme des dur = ${f1(somme)} s au lieu de ${b.duree_cible_s} s`, `Ajuste les durées pour que la somme vaille ${b.duree_cible_s} s (écart de ${f1(b.duree_cible_s - somme)} s à répartir).`));
  }
  for (const t of b.textes_imposes) {
    if (!l.plans.some((p) => (p.texte ?? '').replace(/\s+/g, ' ').trim() === t.replace(/\s+/g, ' ').trim())) {
      e.push(V('texte_impose', 'plans', `texte imposé absent ou modifié : « ${t} »`, `Pose exactement « ${t} » dans le champ texte d'un plan.`));
    }
  }
  if (b.musique) {
    // L'accroche : un plan d'ouverture court, le texte d'ouverture avant 3 s.
    if (l.plans[0].dur > 2.6) e.push(V('accroche', 'plans.0.dur', `premier plan de ${f1(l.plans[0].dur)} s`, 'Ouvre par un plan de 2,6 s au plus : l\'accroche se joue dans les 3 premières secondes.'));
  }
  return { ok: e.length === 0, erreurs: e, liste: l };
}

/** Aimante les frontières sur les temps forts (±TOLERANCE) sans créer de plan de moins de 0,5 s. */
export function aimanter(bornes: number[], battues: number[], minPlan = 0.5): number[] {
  const out = [bornes[0]];
  for (let k = 1; k < bornes.length - 1; k++) {
    let c = bornes[k];
    let meilleur = Infinity;
    for (const t of battues) { const d = Math.abs(t - bornes[k]); if (d < meilleur) { meilleur = d; if (d <= TOLERANCE_AIMANT_S) c = t; } }
    if (c - out[out.length - 1] < minPlan) c = out[out.length - 1] + minPlan;
    if (bornes[bornes.length - 1] - c < minPlan) c = bornes[k];
    out.push(c);
  }
  out.push(bornes[bornes.length - 1]);
  return out;
}

/** Compile la liste VALIDE en EditPlan v1 (images entières, durée totale exacte). */
export function compilerListe(l: ListeMontage, b: Brief): EditPlan {
  const { fps } = b;
  const total = b.duree_cible_s;
  const n = l.plans.length;
  // Frontières cumulées, remises à l'échelle pour valoir exactement la durée cible, puis aimantées sur la grille.
  const somme = l.plans.reduce((s, p) => s + p.dur, 0);
  let t = 0;
  const brutes = [0, ...l.plans.map((p) => (t += (p.dur * total) / somme))];
  brutes[n] = total;
  const bornes = (b.musique ? aimanter(brutes, b.musique.battues_s) : brutes).map((x) => framesDe(x, fps));
  const dureeSrcF = new Map(b.clips.map((c) => [c.id, framesDe(c.duree_s, fps)] as const));
  const video: EditPlan['video'] = l.plans.map((p, i) => {
    const t_f = i > 0 && p.tr !== 'cut' ? Math.max(1, Math.min(Math.floor(fps * 0.4), Math.floor((bornes[i + 1] - bornes[i]) / 2), Math.floor((bornes[i] - bornes[i - 1]) / 2))) : 0;
    const duree_f = bornes[i + 1] - bornes[i] + t_f;
    const src = dureeSrcF.get(p.src) ?? duree_f;
    const entree_f = Math.max(0, Math.min(framesDe(p.in, fps), src - duree_f));
    const dureeS = duree_f / fps;
    const en = energieA(b.musique?.energie ?? [], bornes[i] / fps);
    return {
      id: `p${i + 1}`, src: p.src, entree_f, duree_f, vitesse: 1,
      transition_in: t_f ? { type: p.tr, duree_f: t_f } : { type: 'cut', duree_f: 0 },
      ...(dureeS >= 1.8 ? { zoom: i % 2 === 0 ? { de: 1, a: 1.06 } : { de: 1.06, a: 1 } } : {}),
      section: i === 0 ? 'ouverture' : i === n - 1 ? 'fin' : en > 0.66 ? 'climax' : 'developpement',
    };
  });
  const sources: EditPlan['sources'] = {};
  for (const c of b.clips) if (l.plans.some((p) => p.src === c.id)) sources[c.id] = { kind: 'video', duree_f: framesDe(c.duree_s, fps) };
  if (b.musique) sources[b.musique.id] = { kind: 'audio', duree_f: framesDe(b.musique.duree_s, fps) };
  const totalF = bornes[n];
  const textes: EditPlan['textes'] = [];
  l.plans.forEach((p, i) => {
    if (!p.texte) return;
    const debut = bornes[i] + Math.round(DELAI_TEXTE_S * fps);
    let k = i + 1;
    while (k < n && !l.plans[k].texte) k++;
    const fin = (k < n ? bornes[k] : bornes[n]) - 2;
    const voulu = Math.max(fps, Math.ceil((([...p.texte.replace(/\n/g, ' ')].length) / CPS) * fps));
    const duree_f = Math.max(1, Math.min(fin - debut, Math.max(voulu, Math.round(fps * 2))));
    textes.push({ texte: p.texte, debut_f: debut, duree_f, style: i === n - 1 ? 'carton' : i === 0 ? 'titre' : 'sous-titre', position: b.format === '9:16' ? 'centre' : i === n - 1 ? 'centre' : 'bas', taille_pct: i === n - 1 ? 9 : b.format === '9:16' ? 5 : 6 });
  });
  return {
    version: 1, fps, format: b.format, genre: b.genre, titre: b.enonce.slice(0, 80), sources, video,
    audio: {
      ...(b.musique ? { musique: { src: b.musique.id, entree_f: 0, duree_f: totalF, gain_db: l.gain_db ?? -8, fondu_in_f: Math.floor(fps * 0.3), fondu_out_f: Math.min(totalF - 1, Math.floor(fps * 1.5)) } } : {}),
      voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30,
    },
    textes, generations: [], metadonnees: { modele: 'liste', savoir: [] },
  };
}

/** Liste → EditPlan validé (le validateur d'EditPlan reste le dernier garde-fou). */
export function listeVersPlan(brut: unknown, b: Brief): { ok: true; plan: EditPlan; liste: ListeMontage } | { ok: false; erreurs: Violation[] } {
  const v = validerListe(brut, b);
  if (!v.ok || !v.liste) return { ok: false, erreurs: v.erreurs };
  const plan = compilerListe(v.liste, b);
  const inv = Object.fromEntries([...b.clips.map((c) => [c.id, { duree_s: c.duree_s }] as const), ...(b.musique ? [[b.musique.id, { duree_s: b.musique.duree_s }] as const] : [])]);
  const r = validerEditPlan(plan, { inventaire: inv, duree_cible_s: b.duree_cible_s });
  if (!r.ok || !r.plan) return { ok: false, erreurs: r.erreurs };
  return { ok: true, plan: r.plan, liste: v.liste };
}

/** Liste équivalente d'un EditPlan (graines de mémoire : exemplaires montrés au modèle dans SON format). */
export function planVersListe(p: EditPlan): ListeMontage {
  const textesPar = (debut: number, fin: number) => p.textes.find((t) => t.debut_f >= debut - 1 && t.debut_f < fin)?.texte;
  let curseur = 0;
  return {
    plans: p.video.map((c, i) => {
      const rec = i > 0 ? (c.transition_in.type !== 'cut' ? c.transition_in.duree_f : 0) : 0;
      const debut = curseur - rec;
      curseur = debut + c.duree_f;
      const texte = textesPar(debut, curseur);
      return { src: c.src, in: Math.round((c.entree_f / p.fps) * 100) / 100, dur: Math.round(((curseur - debut - rec) / p.fps) * 100) / 100, tr: c.transition_in.type === 'cut' ? 'cut' : c.transition_in.type === 'dip' ? 'dip' : 'fondu', ...(texte ? { texte } : {}) };
    }),
    ...(p.audio.musique ? { gain_db: p.audio.musique.gain_db } : {}),
  };
}
