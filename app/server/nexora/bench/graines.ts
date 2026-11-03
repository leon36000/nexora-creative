/**
 * Graines de mémoire écrites par le professeur (Claude) : les listes de montage des films de la campagne (V4/V5 :
 * WorkStudio, Surveillance, OPSYS-AI, Modèles et API) converties en segments EditPlan typés. Un plan = un segment du
 * film (durée réelle `d`), le texte principal du segment est posé comme texte de plan, temps forts de la musique mesurés.
 *   npx tsx server/nexora/bench/graines.ts
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { compilerListe, type ListeMontage } from '../montage/liste.js';
import { validerEditPlan } from '../montage/editplan.js';
import type { Brief } from '../montage/types.js';

const RACINE = join(import.meta.dirname, '../../../../marketing/nexora/campagne-films/films');
const SORTIE = join(import.meta.dirname, '../memoire/segments');
const nettoyer = (t: string) => t.replace(/\*/g, '').replace(/\|/g, '\n');

const FILMS: { film: string; version: 'long' | '30'; genre: 'pub' | 'bande-annonce'; mots: string[]; description: string }[] = [
  { film: 'surveillance', version: 'long', genre: 'pub', mots: ['surveillance', 'video', 'camera', 'alerte', 'temps', 'reel', 'rapport'], description: 'Pub de 36 s : accroche « personne ne regardait », milliers d\'heures, détection, alerte, rapport, silence puis carton ; coupes sur les temps forts à 86 BPM.' },
  { film: 'workstudio', version: '30', genre: 'bande-annonce', mots: ['agents', 'equipe', 'travail', 'courriel', 'accord', 'automatique', 'workstudio'], description: 'Bande-annonce de 30 s : l\'agent trie et rédige, attend l\'accord humain, résultat en blocs, silence puis carton ; 83 BPM.' },
  { film: 'opsys', version: '30', genre: 'bande-annonce', mots: ['agent', 'departements', 'humains', 'approuvent', 'equipe', 'opsys', 'journee'], description: 'Bande-annonce de 30 s : une phrase en noir, la journée d\'un dirigeant en plans courts, la liste des départements, grande finale ; 88 BPM.' },
  { film: 'modeles', version: 'long', genre: 'pub', mots: ['modeles', 'api', 'cle', 'prix', 'catalogue', 'filtre'], description: 'Pub de 45 s : une clé, tous les modèles, filtre, prix en dollars canadiens, silence puis carton ; 128 BPM.' },
];

for (const F of FILMS) {
  const b = JSON.parse(readFileSync(join(RACINE, F.film, 'brief.json'), 'utf8'));
  const v = b.versions[F.version];
  const seg = (id: string) => b.segments[id] ?? b.segments[`${id}_${F.version}`];
  const plans: ListeMontage['plans'] = [];
  const clips: Brief['clips'] = [];
  (v.ordre as (string | { id: string; d?: number })[]).forEach((o, i) => {
    const id = typeof o === 'string' ? o : o.id;
    const s = seg(id);
    if (!s) return;
    const d = Math.round((typeof o === 'object' && o.d ? o.d : s.d) * 100) / 100;
    if (d < 0.5) return;
    const choix = (s.textes ?? []).find((t: any) => ['titre', 'impact'].includes(t.style) && b.textes.fr[t.cle]) ?? (s.textes ?? []).find((t: any) => t.style === 'citation' && b.textes.fr[t.cle]);
    const cid = `c${i + 1}`;
    clips.push({ id: cid, duree_s: d + 1, description: id });
    plans.push({ src: cid, in: 0, dur: d, tr: id === 'fin' ? 'fondu' : 'cut', ...(choix ? { texte: nettoyer(b.textes.fr[choix.cle]) } : {}) });
  });
  const total = Math.round(plans.reduce((s, p) => s + p.dur, 0) * 100) / 100;
  const bpm = b.musique.bpm as number, rep = b.musique.repere_source as number;
  const battues: number[] = [];
  for (let t = (rep % (60 / bpm)); t < total + 8; t += 60 / bpm) battues.push(Math.round(t * 1000) / 1000);
  const brief: Brief = {
    id: F.film, partition: 'apprentissage', genre: F.genre, format: '16:9', duree_cible_s: total, fps: 24, enonce: F.description, textes_imposes: [],
    clips, musique: { id: 'mus', duree_s: total + 8, bpm, battues_s: battues, energie: Array.from({ length: Math.ceil((total + 8) * 2) }, (_, i) => Math.min(1, 0.35 + (0.6 * i) / (total * 2))) },
  };
  const plan = compilerListe({ plans, gain_db: -8 }, brief);
  plan.metadonnees = { modele: 'claude-professeur', savoir: [] };
  const rap = validerEditPlan(plan);
  if (!rap.ok) { console.error(F.film, rap.erreurs.map((e) => `${e.regle} ${e.chemin} ${e.message}`)); process.exit(1); }
  const id = `seg-claude-${F.film}-${F.version}`;
  writeFileSync(join(SORTIE, `${id}.json`), JSON.stringify({
    id, version: 1, genre: [F.genre], format: ['16:9'], etiquette: 'professeur_claude', origine: `marketing/nexora/campagne-films/films/${F.film}/brief.json (versions.${F.version})`,
    description: F.description, mots_cles: [...F.mots, F.genre], extrait_edl: rap.plan,
  }) + '\n');
  console.log(id, `${plans.length} plans, ${total} s, ${plan.textes.length} textes`);
}
