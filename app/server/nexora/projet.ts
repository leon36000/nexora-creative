/**
 * Projet long (ambition « long métrage ») : scénario → séquences → scènes → plans, bible de continuité injectée dans
 * chaque plan, estimation de coût du projet entier, lots de rendu, ordre d'assemblage. Aucune limite de longueur codée :
 * un film de 90 minutes est simplement 1 080 plans de 5 s (ou 540 de 10 s) ; seuls les lots bornent le travail en cours.
 * Module pur (aucun accès disque ni moteur) : le serveur le pilote, les tests le prouvent à l'échelle.
 */
import { devisCredits, secondesGpuEstimees } from './credits.js';

export type DureePlan = 5 | 10;

export interface PlanProjet {
  id: string;
  resume: string;
  description: string;
  duree: DureePlan;
  camera: string;
  replique?: string;
  /** Prise retenue pour le plan (id de création). */
  take?: number;
  /** Prises tournées pour ce plan (retenue ou non). */
  prises?: number[];
  etat: 'a_tourner' | 'en_cours' | 'tourne' | 'echec';
}
export interface SceneProjet { id: string; titre: string; lieu?: string; plans: PlanProjet[] }
export interface SequenceProjet { id: string; titre: string; scenes: SceneProjet[] }

export interface BibleProjet {
  /** Style visuel et sonore, injecté dans tous les plans. */
  style: string;
  personnages: { nom: string; description: string }[];
  lieux: { nom: string; description: string }[];
  notes: string;
}

export interface ProjetLong {
  id: string;
  titre: string;
  format: '16:9' | '9:16' | '1:1';
  qualite: 'rapide' | 'max';
  scenario: string;
  bible: BibleProjet;
  sequences: SequenceProjet[];
  cree: string;
}

export interface PlanAPlat { sequence: number; scene: number; index: number; seq: SequenceProjet; sc: SceneProjet; plan: PlanProjet }

/** Les plans dans l'ordre du film (séquence, scène, plan). */
export function aplatir(p: ProjetLong): PlanAPlat[] {
  const out: PlanAPlat[] = [];
  p.sequences.forEach((seq, i) => seq.scenes.forEach((sc, j) => sc.plans.forEach((plan, k) => out.push({ sequence: i, scene: j, index: k, seq, sc, plan }))));
  return out;
}

const norm = (s: string) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

/**
 * Intention complète d'un plan : style, lieu de la scène, personnages cités (par @nom ou par leur nom), puis l'action et
 * la caméra. C'est la continuité : chaque plan reçoit les mêmes descriptions, où qu'il soit dans le film.
 */
export function intentionDuPlanProjet(p: ProjetLong, ref: PlanAPlat): string {
  const texte = `${ref.plan.resume} ${ref.plan.description}`;
  // Continuité de scène : un personnage nommé dans un plan reste dans les suivants de la même scène, même quand le texte
  // dit seulement « elle » ou « il » (sinon le plan suivant tournerait avec un autre visage).
  const scene = norm(ref.sc.plans.slice(0, ref.index + 1).map((x) => `${x.resume} ${x.description}`).join(' '));
  const persos = p.bible.personnages.filter((x) => scene.includes(norm(x.nom.replace(/^@/, ''))));
  const lieu = p.bible.lieux.find((l) => norm(`${ref.sc.lieu ?? ''} ${ref.sc.titre} ${texte}`).includes(norm(l.nom)));
  return [
    p.bible.style ? `Style : ${p.bible.style}.` : '',
    p.bible.notes ? `Notes : ${p.bible.notes}.` : '',
    lieu ? `Lieu (${lieu.nom}) : ${lieu.description}.` : ref.sc.lieu ? `Lieu : ${ref.sc.lieu}.` : '',
    ...persos.map((x) => `Personnage ${x.nom} : ${x.description}.`),
    `Plan : ${ref.plan.description || ref.plan.resume}`,
    ref.plan.camera ? `Caméra : ${ref.plan.camera}.` : '',
  ].filter(Boolean).join('\n');
}

export interface EstimationProjet {
  plans: number;
  scenes: number;
  sequences: number;
  dureeS: number;
  credits: number;
  secondesGpu: number;
  /** Heures de calcul vidéo estimées (une file, un moteur). */
  heuresGpu: number;
  restants: number;
  tournes: number;
  /** Plans partis au tournage : leur coût est déjà engagé, il ne compte plus dans le reste à payer. */
  enCours: number;
}

const TAILLES = { rapide: { '16:9': [832, 480], '9:16': [480, 832], '1:1': [640, 640] }, max: { '16:9': [1344, 768], '9:16': [768, 1344], '1:1': [1024, 1024] } } as const;

export function estimerProjet(p: ProjetLong, tarif: { creditsParSecondeGpu: number }): EstimationProjet {
  const plans = aplatir(p);
  const [width, height] = TAILLES[p.qualite][p.format];
  const videoModel = p.qualite === 'max' ? 'h3-max' : 'h3-fast';
  const cache = new Map<number, { credits: number; secondes: number }>();
  const coutDe = (d: DureePlan) => {
    let c = cache.get(d);
    if (!c) {
      const corps = { videoModel, width, height, lengthFrames: d === 10 ? 243 : 124 };
      c = { credits: devisCredits(corps, tarif), secondes: secondesGpuEstimees(corps) };
      cache.set(d, c);
    }
    return c;
  };
  let credits = 0, secondes = 0, dureeS = 0, restants = 0, tournes = 0, enCours = 0;
  for (const { plan } of plans) {
    dureeS += plan.duree;
    if (plan.etat === 'tourne') { tournes++; continue; }
    if (plan.etat === 'en_cours') { enCours++; continue; }
    restants++;
    const c = coutDe(plan.duree);
    credits += c.credits; secondes += c.secondes;
  }
  return {
    plans: plans.length, scenes: p.sequences.reduce((n, s) => n + s.scenes.length, 0), sequences: p.sequences.length,
    dureeS, credits, secondesGpu: secondes, heuresGpu: Math.round((secondes / 3600) * 10) / 10, restants, tournes, enCours,
  };
}

/** Prochain lot à tourner : les `taille` premiers plans « à tourner », dans l'ordre du film. */
export function prochainLot(p: ProjetLong, taille: number): PlanAPlat[] {
  return aplatir(p).filter((x) => x.plan.etat === 'a_tourner').slice(0, Math.max(1, Math.floor(taille)));
}

/** Plans tournés dans l'ordre du film : la liste d'assemblage pour la timeline du Mode Studio. */
export function ordreAssemblage(p: ProjetLong): { plan: string; take: number; sequence: string; scene: string }[] {
  return aplatir(p).filter((x) => x.plan.etat === 'tourne' && typeof x.plan.take === 'number').map((x) => ({ plan: x.plan.id, take: x.plan.take!, sequence: x.seq.titre, scene: x.sc.titre }));
}

// ---------------------------------------------------------------------------------------------------------------------
// Scénario → arbre (code seul : le LLM peut ensuite affiner plan par plan)

const SLUG = /^(?:\d+[.)]?\s*)?(INT\.?\/EXT\.?|EXT\.?\/INT\.?|INT\.?|EXT\.?|INTÉRIEUR|EXTÉRIEUR)\s+[-–.]?\s*(.+)$/i;
const SEQ = /^(?:S[ÉE]QUENCE|ACTE|ACT|PARTIE|CHAPITRE)\s+[\w.]+\s*[:\-–—]?\s*(.*)$/i;

/** Découpe un scénario texte : « SÉQUENCE n » ouvre une séquence, une ligne de scène (INT./EXT.) une scène, chaque paragraphe un plan. */
export function scenarioVersArbre(texte: string, dureeParDefaut: DureePlan = 5): SequenceProjet[] {
  const sequences: SequenceProjet[] = [];
  let seq: SequenceProjet | null = null;
  let scene: SceneProjet | null = null;
  const nouvelleSeq = (titre: string) => { seq = { id: `s${sequences.length + 1}`, titre: titre || `Séquence ${sequences.length + 1}`, scenes: [] }; sequences.push(seq); scene = null; };
  const nouvelleScene = (titre: string, lieu?: string) => {
    if (!seq) nouvelleSeq('');
    scene = { id: `${seq!.id}c${seq!.scenes.length + 1}`, titre, ...(lieu ? { lieu } : {}), plans: [] };
    seq!.scenes.push(scene);
  };
  let compteur = 0;
  for (const bloc of texte.replace(/\r/g, '').split(/\n\s*\n/)) {
    const ligne = bloc.trim();
    if (!ligne) continue;
    const premiere = ligne.split('\n')[0].trim();
    const s = SEQ.exec(premiere);
    if (s) { nouvelleSeq(s[1].trim() || premiere); const reste = ligne.split('\n').slice(1).join('\n').trim(); if (!reste) continue; }
    const corps = s ? ligne.split('\n').slice(1).join('\n').trim() : ligne;
    const l = SLUG.exec(corps.split('\n')[0].trim());
    if (l) {
      nouvelleScene(corps.split('\n')[0].trim(), l[2].trim());
      const reste = corps.split('\n').slice(1).join(' ').trim();
      if (!reste) continue;
      ajouterPlan(reste);
    } else ajouterPlan(corps.replace(/\n/g, ' '));
  }
  function ajouterPlan(description: string) {
    if (!scene) nouvelleScene('Scène 1');
    compteur++;
    scene!.plans.push({ id: `p${compteur}`, resume: description.slice(0, 90), description: description.slice(0, 1200), duree: dureeParDefaut, camera: '', etat: 'a_tourner' });
  }
  return sequences;
}
