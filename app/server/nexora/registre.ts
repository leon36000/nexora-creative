/**
 * Registre universel de capacités, version 1 (sous-ensemble du contrat « nexora.capability/1 » du rapport
 * recherche/05 §5). Chaque moteur se décrit par un manifeste : tâches, durées, son, licence et territoires, ensembles
 * de modèles requis, qualité relative. Ajouter un moteur = ajouter un manifeste (et sa recette de graphe) ; l'interface
 * et le Director lisent le registre au lieu de connaître les moteurs.
 *
 * Le planificateur applique d'abord les filtres durs (tâche, durée, licence et territoire, modèles installés), puis
 * classe ce qui reste. La licence ne se discute pas : un moteur exclu l'est avec sa raison, lisible par l'interface.
 */
import { z } from 'zod';
import { verdictLicence } from './licences.js';

export const Tache = z.enum(['t2v', 'i2v', 'flf2v', 'r2v', 'v2v', 'extend']);
export type Tache = z.infer<typeof Tache>;

export const Manifeste = z.object({
  contrat: z.literal('nexora.capability/1'),
  id: z.string().regex(/^[a-z0-9][a-z0-9._-]*\/[a-z0-9][a-z0-9._-]*$/),
  nom: z.object({ fr: z.string().min(1), en: z.string().optional() }),
  famille: z.literal('video'),
  /** Valeur de `videoModel` attendue par la recette de graphe (server/index.ts). */
  recette: z.enum(['h3-fast', 'h3-max']),
  taches: z.array(Tache).min(1),
  sortie: z.object({ audio: z.boolean(), fps: z.number().int().positive(), dureeS: z.object({ min: z.number(), max: z.number() }) }),
  /** Ensembles de server/models.ts à avoir sur le moteur. */
  ensembles: z.array(z.string()).min(1),
  licence: z.object({
    nom: z.string().min(1),
    url: z.string().url(),
    commercial: z.boolean(),
    /** Ensemble de server/nexora/licences.ts qui porte la règle de territoire. */
    regle: z.string().min(1),
    affichage: z.string().optional(),
  }),
  /** Qualité relative (0 à 100) pour le classement ; mesurée sur notre jeu d'or quand il existe. */
  qualite: z.number().min(0).max(100),
  materiel: z.object({ requiertSm: z.array(z.string()).optional(), memoireGo: z.number().positive() }),
}).strict();
export type Manifeste = z.infer<typeof Manifeste>;

export const MANIFESTES: Manifeste[] = [
  {
    contrat: 'nexora.capability/1',
    id: 'minimax/fasth3-v2-nvfp4',
    nom: { fr: 'MiniMax H3 (FastH3 V2)', en: 'MiniMax H3 (FastH3 V2)' },
    famille: 'video',
    recette: 'h3-fast',
    taches: ['t2v', 'i2v'],
    sortie: { audio: true, fps: 24, dureeS: { min: 5, max: 15.1 } },
    ensembles: ['h3-fast'],
    licence: {
      nom: 'MiniMax H3 Community License Agreement',
      url: 'https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE',
      commercial: true,
      regle: 'h3-fast',
      affichage: 'MiniMax H3',
    },
    // Arène Artificial Analysis texte-vers-vidéo avec audio : 3e, seul modèle ouvert du haut du classement (rapport 03).
    qualite: 90,
    materiel: { requiertSm: ['sm_120', 'sm_121'], memoireGo: 36 },
  },
  {
    contrat: 'nexora.capability/1',
    id: 'minimax/h3-cinema',
    nom: { fr: 'MiniMax H3 (cinéma, pleines étapes)', en: 'MiniMax H3 (cinema, full steps)' },
    famille: 'video',
    recette: 'h3-max',
    taches: ['t2v', 'i2v'],
    sortie: { audio: true, fps: 24, dureeS: { min: 5, max: 15.1 } },
    ensembles: ['h3-max'],
    licence: {
      nom: 'MiniMax H3 Community License Agreement',
      url: 'https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE',
      commercial: true,
      regle: 'h3-max',
      affichage: 'MiniMax H3',
    },
    // Modèle non distillé, 1344×768, ≥ 24 étapes : la meilleure image du parc (banc du 31/10, recherche/10).
    qualite: 97,
    materiel: { requiertSm: ['sm_120'], memoireGo: 32 },
  },
];

export interface Besoin { tache: Tache; dureeS: number; son: boolean }
export interface Contexte {
  territoire: string | null;
  ensemblesPrets?: Set<string>;
  /** Recettes que le parc de moteurs GPU sait rendre (server/engine.ts) ; absent = pas de filtre. */
  recettes?: Set<string>;
}

export function planifierMoteurs(b: Besoin, ctx: Contexte, manifestes: Manifeste[] = MANIFESTES) {
  const retenus: (Manifeste & { score: number })[] = [];
  const exclus: { id: string; raison: string }[] = [];
  for (const m of manifestes) {
    const raison = !m.taches.includes(b.tache)
      ? `tâche ${b.tache} non prise en charge`
      : b.dureeS < m.sortie.dureeS.min || b.dureeS > m.sortie.dureeS.max
        ? `durée ${b.dureeS} s hors de ${m.sortie.dureeS.min} à ${m.sortie.dureeS.max} s`
        : !m.licence.commercial
          ? 'licence non commerciale'
          : verdictLicence(m.licence.regle, ctx.territoire).statut !== 'permis'
            ? `licence ${m.licence.nom} : territoire du compte exclu ou inconnu`
            : ctx.ensemblesPrets && !m.ensembles.every((e) => ctx.ensemblesPrets!.has(e))
              ? 'modèles pas encore installés sur le moteur'
              : ctx.recettes && !ctx.recettes.has('*') && !ctx.recettes.has(m.recette)
                ? 'aucun moteur GPU du parc ne porte cette recette'
                : null;
    if (raison) exclus.push({ id: m.id, raison });
    // Classement : qualité, puis bonus si le son demandé est natif.
    else retenus.push({ ...m, score: m.qualite + (b.son && m.sortie.audio ? 10 : 0) });
  }
  retenus.sort((a, z2) => z2.score - a.score);
  return { retenus, exclus };
}
