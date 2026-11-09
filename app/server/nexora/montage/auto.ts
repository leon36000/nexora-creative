/**
 * `montage_auto` : base déterministe du harnais (recherche/14 §3). Clips + musique (temps forts) + courbe d'énergie →
 * EditPlan valide, sans LLM. Rythme : durée de plan = bande du genre, plus courte quand l'énergie monte ; coupes aimantées
 * sur les temps forts ; aucun plan réutilisé (curseur par source) ; textes imposés posés lisiblement ; musique à −8 dB
 * avec fondu final ; cible −14 LUFS. C'est le plancher de qualité ET le repli de tout échec du LLM.
 */
import { type EditPlan, type PlanVideo, framesDe, validerEditPlan } from './editplan.js';
import { BANDES, COUPE_MIN_S, type Brief, energieA } from './types.js';

const arr = (x: number) => Math.round(x * 1000) / 1000;

/** Coupes (s) de 0 à `total`, aimantées sur la grille de temps forts quand elle existe. */
export function grilleDeCoupes(b: Brief, total: number): number[] {
  const [mini, maxi] = BANDES[b.genre];
  const battues = (b.musique?.battues_s ?? []).filter((t) => t > 0 && t < total);
  const coupes = [0];
  let t = 0;
  while (total - t > maxi + 0.001) {
    const e = energieA(b.musique?.energie ?? [], t);
    const voulu = maxi - (maxi - mini) * e;
    let cible = t + voulu;
    if (battues.length) {
      const dansBande = battues.filter((x) => x >= t + Math.max(mini, COUPE_MIN_S) - 1e-6 && x <= t + maxi + 1e-6);
      if (dansBande.length) cible = dansBande.reduce((m, x) => (Math.abs(x - cible) < Math.abs(m - cible) ? x : m));
    }
    t = Math.min(cible, total - COUPE_MIN_S);
    coupes.push(t);
  }
  coupes.push(total);
  return coupes;
}

interface Curseur { id: string; duree_s: number; pos_s: number; coupes_s: number[]; mots: [number, number][] }

/** Sort d'un intervalle de parole ou d'une coupe interne : premier point libre ≥ t. */
function pointLibre(c: Curseur, t: number): number {
  let p = t;
  for (let boucle = 0; boucle < 20; boucle++) {
    const m = c.mots.find(([a, b]) => p > a - 0.05 && p < b + 0.05);
    if (!m) return p;
    p = m[1] + 0.05;
  }
  return p;
}

export function montageAuto(b: Brief): EditPlan {
  const { fps } = b;
  const musique = b.musique;
  const sonPremierPlan = !!b.voix || b.clips.some(c => c.a_audio === true);
  const total = Math.max(2, Math.min(b.duree_cible_s, musique ? Math.max(2, musique.duree_s) : b.duree_cible_s));
  const totalF = framesDe(total, fps);
  const coupesS = grilleDeCoupes(b, totalF / fps);
  // Frontières en images, strictement croissantes.
  const f: number[] = [0];
  for (const s of coupesS.slice(1, -1)) { const x = framesDe(s, fps); if (x > f[f.length - 1] + 1 && x < totalF - 1) f.push(x); }
  f.push(totalF);

  const curseurs: Curseur[] = b.clips.map((c) => ({ id: c.id, duree_s: c.duree_s, pos_s: 0, coupes_s: c.coupes_s ?? [], mots: c.mots ?? [] }));
  const video: PlanVideo[] = [];
  const dernierPar = new Map<string, number>();
  for (let i = 0; i < f.length - 1; i++) {
    let duree_f = f[i + 1] - f[i];
    // Dernier plan d'une pub ou d'un explicatif : fondu vers la fin ; le recouvrement est ajouté d'emblée à sa durée.
    const fonduDernier = i === f.length - 2 && (b.genre === 'pub' || b.genre === 'explicatif') && duree_f >= 8 && i > 0 && Math.floor((video[video.length - 1]?.duree_f ?? 0) / 2) >= 1;
    const tf = fonduDernier ? Math.min(Math.floor(duree_f / 2), Math.floor(fps * 0.5), Math.floor((video[video.length - 1]?.duree_f ?? 0) / 2)) : 0;
    duree_f += tf;
    const dureeS = duree_f / fps;
    // Clip : celui qui a le plus de matière restante, hors celui du plan précédent (sauf unique).
    const prec = video[video.length - 1]?.src;
    const dansMot = (c: Curseur, fr: number) => c.mots.some(([x, y]) => fr / fps > x - 0.05 && fr / fps < y + 0.05);
    const traverse = (c: Curseur, e: number, n: number) => c.coupes_s.some((cs) => cs > e / fps + 1e-6 && cs < (e + n) / fps - 1e-6);
    const place = (c: Curseur, vit: number) => {
      const besoin = Math.round(duree_f * vit);
      const depart = Math.ceil(pointLibre(c, c.pos_s) * fps);
      const dureeSrc = framesDe(c.duree_s, fps);
      // Premier point d'entrée ≥ départ dont l'entrée et la sortie sont hors des paroles et qui ne traverse aucune coupe de plan.
      const entree = trouver(c, depart, besoin);
      return { entree, besoin, dispo: dureeSrc - entree };
    };
    function trouver(c: Curseur, depart: number, besoin: number): number {
      const dureeSrc = framesDe(c.duree_s, fps);
      for (let k = 0; k <= fps * 4 && depart + k + besoin <= dureeSrc; k++) {
        if (!dansMot(c, depart + k) && !dansMot(c, depart + k + besoin) && !traverse(c, depart + k, besoin)) return depart + k;
      }
      return depart;
    }
    const candidats = curseurs
      .filter((c) => c.id !== prec || curseurs.length === 1)
      .map((c) => ({ c, ...place(c, 1) }))
      .filter((x) => !dansMot(x.c, x.entree + x.besoin))
      .sort((x, y) => y.dispo - x.dispo || (dernierPar.get(x.c.id) ?? -1) - (dernierPar.get(y.c.id) ?? -1));
    let choix = candidats.find((x) => x.dispo >= x.besoin);
    let vitesse = 1;
    if (!choix) {
      // Ralenti borné pour tenir la durée avec la matière qui reste ; sinon on repart du début d'une source (réemploi tardif).
      const rest = candidats[0];
      if (rest && rest.dispo >= rest.besoin * 0.5 && rest.dispo > fps * 0.4) { choix = rest; vitesse = Math.max(0.5, Math.round((rest.dispo / duree_f) * 100) / 100); }
      else {
        const rec = curseurs.filter((c) => c.id !== prec || curseurs.length === 1).sort((x, y) => y.duree_s - x.duree_s)[0] ?? curseurs[0];
        rec.pos_s = 0;
        const p = place(rec, 1);
        choix = { c: rec, ...p };
        if (choix.dispo < choix.besoin) vitesse = Math.max(0.25, Math.round((choix.dispo / duree_f) * 100) / 100);
      }
    }
    const c = choix.c;
    const conso = Math.round(duree_f * vitesse);
    const entree_f = vitesse === 1 ? choix.entree : trouver(c, choix.entree, conso);
    c.pos_s = arr((entree_f + conso) / fps + 0.05);
    dernierPar.set(c.id, i);
    const premier = i === 0, dernier = i === f.length - 2;
    const section = premier ? 'ouverture' : dernier ? 'fin' : energieA(musique?.energie ?? [], f[i] / fps) > 0.66 ? 'climax' : 'developpement';
    const fondu = fonduDernier;
    video.push({
      id: `p${i + 1}`, src: c.id, entree_f, duree_f, vitesse,
      transition_in: fondu ? { type: 'fondu', duree_f: tf } : { type: 'cut', duree_f: 0 },
      ...(dureeS >= 1.8 ? { zoom: i % 2 === 0 ? { de: 1, a: 1.06 } : { de: 1.06, a: 1 } } : {}),
      section,
      pourquoi: musique ? 'coupe aimantée sur un temps fort, durée suivant l’énergie' : 'durée de la bande du genre',
    });
  }
  const sources: EditPlan['sources'] = {};
  for (const c of b.clips) sources[c.id] = { kind: 'video', duree_f: framesDe(c.duree_s, fps), ...(c.a_audio === undefined ? {} : { a_audio: c.a_audio }), ...(c.mots?.length ? { mots: c.mots.map(([x, y]) => [framesDe(x, fps), framesDe(y, fps)] as [number, number]) } : {}) };
  if (musique) sources[musique.id] = { kind: 'audio', duree_f: framesDe(musique.duree_s, fps) };
  if (b.voix) sources[b.voix.id] = { kind: 'audio', duree_f: framesDe(b.voix.duree_s, fps) };

  // Textes imposés : accroche en tête, appel à l'action en fin, le reste réparti ; lisibles (≥ 1 s, ≤ 17 caractères/s).
  const textes: EditPlan['textes'] = [];
  const n = b.textes_imposes.length;
  b.textes_imposes.forEach((texte, k) => {
    const dur = Math.min(totalF, Math.max(fps, Math.ceil(([...texte].length / 15) * fps)));
    const debut = k === n - 1 && n > 1 ? totalF - dur - Math.floor(fps * 0.3) : n === 1 ? Math.floor(fps * 0.5) : Math.min(totalF - dur, Math.floor(((totalF - dur) * k) / Math.max(1, n - 1)));
    textes.push({ texte, debut_f: Math.max(0, debut), duree_f: dur, style: k === 0 ? 'titre' : k === n - 1 ? 'carton' : 'sous-titre', position: b.format === '9:16' ? 'centre' : 'bas', taille_pct: b.format === '9:16' ? 5.5 : 6 });
  });
  // Pas de chevauchement entre textes.
  textes.sort((x, y) => x.debut_f - y.debut_f);
  for (let i = 1; i < textes.length; i++) {
    const fin = textes[i - 1].debut_f + textes[i - 1].duree_f;
    if (textes[i].debut_f < fin) textes[i].debut_f = Math.min(fin, Math.max(0, totalF - textes[i].duree_f));
  }

  const plan: EditPlan = {
    version: 1, fps, format: b.format, genre: b.genre, titre: b.enonce.slice(0, 80),
    sources, video,
    audio: {
      ...(musique ? { musique: { src: musique.id, entree_f: 0, duree_f: totalF, gain_db: sonPremierPlan ? -14 : -8, fondu_in_f: Math.floor(fps * 0.3), fondu_out_f: Math.min(totalF - 1, Math.floor(fps * 1.5)) } } : {}),
      voix: b.voix ? [{ src: b.voix.id, debut_f: Math.floor(fps * 0.5), entree_f: 0, duree_f: Math.min(framesDe(b.voix.duree_s, fps), totalF - Math.floor(fps * 0.5) - 1), gain_db: 0 }] : [],
      ducking: sonPremierPlan && musique ? { actif: true, profondeur_db: 10 } : { actif: false, profondeur_db: 0 },
      cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30,
    },
    textes, generations: [],
    metadonnees: { modele: 'montage_auto', savoir: ['montage_auto@1'] },
  };
  const r = validerEditPlan(plan, { duree_cible_s: b.duree_cible_s });
  if (!r.ok) throw new Error(`montage_auto a produit un plan invalide (bug) :\n${r.erreurs.map((e) => `${e.regle} ${e.chemin} ${e.message}`).join('\n')}`);
  return r.plan!;
}
