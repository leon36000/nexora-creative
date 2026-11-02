import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { BRIEFS } from '../bench/briefs.js';
import { analyserMedia, analyserSignal, ffmpegParDefaut, lireDuree, lireLoudness, lireScdet, lireSilences, vueTexte } from './analyse.js';
import { montageAuto } from './auto.js';
import { critiquer, lireNotesJuge } from './critique.js';
import { type EditPlan, EditPlanSchema, dureeTotaleS, lignedeTemps, validerEditPlan } from './editplan.js';
import { chargerMemoire, exemplairesInvalides, indicesFonction, recupererSavoir } from './memoire.js';
import { mesurer, metriqueAudio, metriqueDoublons, metriqueTexte, spearman } from './metriques.js';
import { planifierMontage, vueBrief } from './planifier.js';
import { reviser } from './revise.js';
import type { ClientLlm } from '../llm.js';

const plan = (): EditPlan => ({
  version: 1, fps: 24, format: '16:9', genre: 'pub',
  sources: { a: { kind: 'video', duree_f: 240, mots: [[50, 70]] }, b: { kind: 'video', duree_f: 240 }, mus: { kind: 'audio', duree_f: 960 } },
  video: [
    { id: 'p1', src: 'a', entree_f: 0, duree_f: 48, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } },
    { id: 'p2', src: 'b', entree_f: 24, duree_f: 72, vitesse: 1, transition_in: { type: 'fondu', duree_f: 10 } },
  ],
  audio: { musique: { src: 'mus', entree_f: 0, duree_f: 110, gain_db: -8, fondu_in_f: 7, fondu_out_f: 36 }, voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
  textes: [{ texte: 'Une phrase courte.', debut_f: 12, duree_f: 36, style: 'titre', position: 'bas', taille_pct: 6 }],
  generations: [],
});
const regles = (p: unknown, ctx = {}) => validerEditPlan(p, ctx).erreurs.map((e) => e.regle);

describe('EditPlan v1 : validateur', () => {
  it('accepte un plan valide et calcule la durée avec le recouvrement des fondus', () => {
    const r = validerEditPlan(plan());
    expect(r.ok).toBe(true);
    expect(lignedeTemps(r.plan!).total).toBe(48 + 72 - 10);
    expect(dureeTotaleS(r.plan!)).toBeCloseTo(110 / 24);
  });
  it('refuse les durées non entières et les champs hors bornes', () => {
    const p: any = plan(); p.video[0].duree_f = 47.5;
    expect(validerEditPlan(p).ok).toBe(false);
    const q: any = plan(); q.video[0].vitesse = 9;
    expect(regles(q)).toContain('schema');
  });
  it('refuse une source inconnue, hors inventaire, ou lue au-delà de sa fin', () => {
    const p = plan(); p.video[0].src = 'zz';
    expect(regles(p)).toContain('source_connue');
    const q = plan(); q.video[1].entree_f = 200;
    expect(regles(q)).toContain('dans_la_source');
    expect(regles(plan(), { inventaire: { a: { duree_s: 10 } } })).toContain('source_autorisee');
  });
  it('refuse une coupe dans un mot, avec un indice de déplacement', () => {
    const p = plan(); p.video[0].entree_f = 60;
    const r = validerEditPlan(p);
    expect(r.erreurs.find((e) => e.regle === 'pas_de_coupe_dans_un_mot')?.indice).toContain('71');
    const ok = plan(); ok.video[0].entree_f = 72;
    expect(validerEditPlan(ok).ok).toBe(true);
  });
  it('borne les transitions, le fondu audio de 30 ms, la durée cible et les textes', () => {
    const p = plan(); p.video[1].transition_in = { type: 'fondu', duree_f: 30 };
    expect(regles(p)).toContain('transition_duree');
    const q = plan(); q.audio.fondu_coupe_ms = 10;
    expect(regles(q)).toContain('fondu_audio_30ms');
    expect(regles(plan(), { duree_cible_s: 10 })).toContain('duree_cible');
    const t = plan(); t.textes[0].texte = 'a\nb\nc';
    expect(regles(t)).toContain('texte_lignes');
    const u = plan(); u.textes[0].debut_f = 100;
    expect(regles(u)).toContain('texte_dans_la_sequence');
  });
  it('exige un ducking quand une voix passe sur la musique', () => {
    const p = plan(); p.sources.v = { kind: 'audio', duree_f: 100 }; p.audio.voix = [{ src: 'v', debut_f: 0, entree_f: 0, duree_f: 100, gain_db: 0 }];
    expect(regles(p)).toContain('ducking');
    p.audio.ducking = { actif: true, profondeur_db: 10 };
    expect(validerEditPlan(p).ok).toBe(true);
  });
  it('le schéma applique des valeurs par défaut sûres', () => {
    const p: any = plan(); delete p.audio; delete p.textes;
    const lu = EditPlanSchema.parse(p);
    expect(lu.audio.fondu_coupe_ms).toBe(30);
    expect(lu.audio.cible_lufs).toBe(-14);
  });
});

describe('montage_auto : base déterministe', () => {
  it('produit un plan valide pour les 12 briefs, à la durée cible, sans doublon ni plan < 0,5 s', () => {
    for (const b of BRIEFS) {
      const p = montageAuto(b);
      const m = mesurer(p, b);
      expect(m.porte, b.id).toBe(true);
      expect(Math.abs(dureeTotaleS(p) - b.duree_cible_s) / b.duree_cible_s, b.id).toBeLessThanOrEqual(0.05);
      expect(m.metriques.doublons.detail.doublons, b.id).toBe(0);
      expect(Math.min(...p.video.map((c) => c.duree_f / p.fps)), b.id).toBeGreaterThanOrEqual(0.5 - 1e-9);
      expect(m.metriques.texte.detail.couverture, b.id).toBe(1);
    }
  });
  it('est déterministe et pose les coupes sur les temps forts', () => {
    const b = BRIEFS[0];
    expect(JSON.stringify(montageAuto(b))).toBe(JSON.stringify(montageAuto(b)));
    expect(mesurer(montageAuto(b), b).metriques.battues.detail.part_sur_battue).toBeGreaterThan(0.7);
  });
  it('plans plus courts dans le climax que dans l’ouverture (bande-annonce)', () => {
    const b = BRIEFS.find((x) => x.id === 'bande-annonce-a')!;
    const p = montageAuto(b);
    const moy = (s: string) => { const l = p.video.filter((c) => c.section === s); return l.reduce((n, c) => n + c.duree_f, 0) / l.length; };
    expect(moy('climax')).toBeLessThan(moy('ouverture'));
  });
  it('ne coupe pas dans la parole d’une source', () => {
    const b = { ...BRIEFS[0], clips: BRIEFS[0].clips.map((c, i) => (i % 2 ? c : { ...c, mots: [[0.5, 2.5], [3, 4.2]] as [number, number][] })) };
    expect(validerEditPlan(montageAuto(b), { duree_cible_s: b.duree_cible_s }).ok).toBe(true);
  });
});

describe('métriques sur l’EditPlan', () => {
  it('Spearman : monotone = 1, inverse = −1, constant = 0', () => {
    expect(spearman([1, 2, 3, 4], [10, 20, 30, 40])).toBeCloseTo(1);
    expect(spearman([1, 2, 3, 4], [4, 3, 2, 1])).toBeCloseTo(-1);
    expect(spearman([1, 1, 1], [1, 2, 3])).toBe(0);
  });
  it('détecte les doublons de plans', () => {
    const p = plan(); p.video[1] = { ...p.video[1], src: 'a', entree_f: 10, transition_in: { type: 'cut', duree_f: 0 } };
    p.video[0].entree_f = 72; p.video[0].duree_f = 48;
    p.video.push({ id: 'p3', src: 'a', entree_f: 80, duree_f: 24, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } });
    expect(metriqueDoublons(p).detail.doublons).toBeGreaterThanOrEqual(1);
  });
  it('lisibilité du texte : trop de caractères par seconde et texte imposé modifié', () => {
    const p = plan(); p.textes[0] = { ...p.textes[0], texte: 'Un texte vraiment beaucoup trop long pour rester si peu', duree_f: 24 };
    const m = metriqueTexte(p, { ...BRIEFS[0], textes_imposes: ['Autre texte'] });
    expect(m.ecarts.some((e) => e.message.includes('caractères/s'))).toBe(true);
    expect(m.ecarts.some((e) => e.gravite === 'bloquant')).toBe(true);
    expect(m.score).toBe(0);
  });
  it('audio : cible, crête et ducking', () => {
    const p = plan(); p.audio.cible_lufs = -20; p.audio.crete_db = 0;
    const m = metriqueAudio(p, BRIEFS[0]);
    expect(m.score).toBeLessThan(1);
    expect(m.ecarts.map((e) => e.indice).join()).toContain('cible_lufs = −14');
  });
  it('un plan invalide échoue à la porte avec un composite nul, et le coût en crédits compte les plans à tourner', () => {
    const b = BRIEFS[0];
    expect(mesurer({ version: 1 }, b)).toMatchObject({ porte: false, composite: 0 });
    const p = montageAuto(b); p.generations = [{ description: 'plan manquant', duree_s: 5, moteur: 'h3' }];
    expect(mesurer(p, b).credits).toBeGreaterThan(0);
    expect(mesurer(montageAuto(b), b).credits).toBe(0);
  });
});

describe('revise et critique', () => {
  const b = BRIEFS[0];
  it('applique des rustines par identifiant et revalide', () => {
    const p = montageAuto(b);
    const [a, c] = p.video;
    const r = reviser(p, [{ op: 'regler_plan', id: a.id, duree_f: a.duree_f + 2 }, { op: 'regler_plan', id: c.id, duree_f: c.duree_f - 2 }], { duree_cible_s: b.duree_cible_s });
    expect(r.ok).toBe(true);
    if (r.ok) expect(r.plan.video[0].duree_f).toBe(a.duree_f + 2);
  });
  it('refuse une rustine qui invalide le plan, laisse l’original intact', () => {
    const p = montageAuto(b); const copie = JSON.stringify(p);
    const r = reviser(p, [{ op: 'regler_plan', id: 'p1', entree_f: 99999 }]);
    expect(r.ok).toBe(false);
    expect(JSON.stringify(p)).toBe(copie);
    expect(reviser(p, [{ op: 'inconnue' }]).ok).toBe(false);
    expect(reviser(p, [{ op: 'supprimer', id: 'zz' }]).ok).toBe(false);
  });
  it('critique : résumé avec écarts typés ; le juge est optionnel et pondéré 30 %', async () => {
    const p = montageAuto(b); p.audio.cible_lufs = -20;
    const c = await critiquer(p, b);
    expect(c.juge).toBeNull();
    expect(c.resume).toContain('cible_lufs');
    const llm: ClientLlm = { completer: async () => '{"accroche":8,"coherence":8,"lisibilite":8,"finition":8,"remarque":"ok"}' };
    const avec = await critiquer(montageAuto(b), b, { llm, planche: 'data:image/jpeg;base64,AAAA' });
    expect(avec.juge?.moyenne).toBe(8);
    expect(avec.composite).toBeCloseTo(0.7 * avec.metriques.composite + 0.3 * 0.8, 3);
    expect(lireNotesJuge('pas du json')).toBeNull();
  });
});

describe('mémoire AMD', () => {
  it('les exemplaires semés sont des EditPlan valides et les recettes couvrent les 4 genres', () => {
    expect(exemplairesInvalides()).toEqual([]);
    const m = chargerMemoire();
    expect(m.recettes.flatMap((r) => r.genres).sort()).toEqual(['bande-annonce', 'explicatif', 'pub', 'social']);
    for (const r of m.recettes) expect(r.texte.split(/\s+/).length).toBeLessThanOrEqual(600);
  });
  it('récupère UN exemplaire adapté au genre et au format, et respecte l’exclusion', () => {
    const b = BRIEFS.find((x) => x.id === 'bande-annonce-c')!;
    expect(recupererSavoir(b).segment?.id).toBe('seg-bande-annonce-bataille');
    expect(recupererSavoir(b, { exclure: ['seg-bande-annonce-bataille'] }).segment?.id).not.toBe('seg-bande-annonce-bataille');
    expect(recupererSavoir(BRIEFS.find((x) => x.id === 'social-a')!).segment?.id).toBe('seg-social-surveillance-9x16');
    expect(recupererSavoir(BRIEFS.find((x) => x.id === 'explicatif-b')!).segment?.id).toBe('seg-explicatif-voix-musique');
  });
  it('indice de fonction seulement pour les règles violées', () => {
    expect(indicesFonction('plan_edit', [{ regle: 'dans_la_source', chemin: 'x', message: 'm' }]).join('\n')).toContain('entree_f + duree_f');
    expect(indicesFonction('plan_edit', [])).toEqual([]);
  });
});

describe('planification LLM (client simulé)', () => {
  const b = BRIEFS.find((x) => x.id === 'pub-b')!;
  const llm = (reponses: string[]): ClientLlm & { vus: string[] } => { const vus: string[] = []; let i = 0; return { vus, completer: async (_r, m) => { vus.push(JSON.stringify(m)); return reponses[Math.min(i++, reponses.length - 1)]; } }; };
  it('vue du brief : identifiants, durées en images, temps forts', () => {
    const v = vueBrief(b);
    expect(v).toContain('m1:'); expect(v).toContain('images'); expect(v).toContain('Temps forts');
  });
  it('plan valide du premier coup gardé tel quel', async () => {
    const bon = montageAuto(b);
    const r = await planifierMontage(llm([JSON.stringify(bon)]), b, { memoire: true });
    expect(r.source).toBe('llm'); expect(r.valideDuPremierCoup).toBe(true); expect(r.appels).toBe(1);
    expect(r.versionsSavoir.length).toBe(2);
  });
  it('plan invalide : une réparation avec indice, puis repli sur montage_auto', async () => {
    const mauvais = JSON.stringify({ version: 1, fps: 24 });
    const c = llm([mauvais, mauvais]);
    const r = await planifierMontage(c, b, { reparations: 1 });
    expect(r.source).toBe('repli'); expect(r.appels).toBe(2);
    expect(c.vus[1]).toContain('Le validateur refuse');
    expect(mesurer(r.plan, b).porte).toBe(true);
  });
  it('sans LLM ou sur exception : repli, jamais d’erreur', async () => {
    expect((await planifierMontage(null, b)).source).toBe('repli');
    const casse: ClientLlm = { completer: async () => { throw new Error('HTTP 500'); } };
    expect((await planifierMontage(casse, b)).source).toBe('repli');
  });
  it('un tour de rustines n’est gardé que si le score en code monte', async () => {
    const base = montageAuto(b); base.audio.cible_lufs = -20;
    const r = await planifierMontage(llm([JSON.stringify(base), JSON.stringify({ rustines: [{ op: 'regler_audio', cible_lufs: -14 }] })]), b, { tours: 1 });
    expect(r.plan.audio.cible_lufs).toBe(-14);
    const pire = await planifierMontage(llm([JSON.stringify(montageAuto(b)), JSON.stringify({ rustines: [{ op: 'regler_audio', cible_lufs: -22 }] })]), b, { tours: 1 });
    expect(pire.plan.audio.cible_lufs).toBe(-14);
  });
  it('plafond d’appels respecté', async () => {
    const r = await planifierMontage(llm(['{}']), b, { reparations: 9, maxAppels: 2 });
    expect(r.appels).toBeLessThanOrEqual(2); expect(r.source).toBe('repli');
  });
});

describe('analyze_media : analyseurs et calcul de temps forts', () => {
  it('lit durée, scdet, silences et sonie dans la sortie ffmpeg', () => {
    expect(lireDuree('  Duration: 00:01:02.50, start')).toBeCloseTo(62.5);
    expect(lireScdet('[scdet @ 0x1] lavfi.scd.score: 20.1, lavfi.scd.time: 4.5\n[scdet @ 0x1] lavfi.scd.score: 33.0, lavfi.scd.time: 9.04')).toEqual([4.5, 9.04]);
    expect(lireSilences('silence_start: 1.5\n[x] silence_end: 2.7 | silence_duration: 1.2\nsilence_start: 8')).toEqual([[1.5, 2.7]]);
    expect(lireLoudness('Summary:\n  Integrated loudness:\n    I:         -14.3 LUFS\n  True peak:\n    Peak:       -1.2 dBFS')).toEqual({ integre_lufs: -14.3, crete_db: -1.2 });
  });
  it('retrouve le tempo et la grille d’un signal à 120 BPM', () => {
    const sr = 11025, dur = 20, x = new Float32Array(sr * dur);
    for (let t = 0.3; t < dur; t += 0.5) { const i = Math.round(t * sr); for (let k = 0; k < 400 && i + k < x.length; k++) x[i + k] = Math.sin(k * 0.4) * Math.exp(-k / 90) * 0.9; }
    const a = analyserSignal(x, sr);
    expect(a.bpm).toBeGreaterThan(115); expect(a.bpm).toBeLessThan(125);
    const proches = a.battues_s.filter((b) => { const d = (b - 0.3) % 0.5; return Math.min(d, 0.5 - d) < 0.04; }).length;
    expect(proches / a.battues_s.length).toBeGreaterThan(0.8);
    expect(a.energie.length).toBeGreaterThanOrEqual(40);
  });
  const ff = ffmpegParDefaut();
  const dispo = (() => { try { execFileSync(ff, ['-version'], { stdio: 'ignore' }); return true; } catch { return false; } })();
  it.skipIf(!dispo)('analyse un vrai fichier synthétique avec cache (ffmpeg)', async () => {
    const d = mkdtempSync(join(tmpdir(), 'nx-analyse-'));
    try {
      const f = join(d, 'essai.mp4');
      execFileSync(ff, ['-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=160x90:r=24:d=2,format=yuv420p', '-f', 'lavfi', '-i', 'color=c=blue:s=160x90:r=24:d=2,format=yuv420p', '-f', 'lavfi', '-i', 'sine=f=440:d=4', '-filter_complex', '[0][1]concat=n=2:v=1:a=0[v]', '-map', '[v]', '-map', '2:a', '-shortest', f]);
      const a = await analyserMedia(f, { ffmpeg: ff, cache: join(d, 'cache') });
      expect(a.duree_s).toBeGreaterThan(3.5); expect(a.a_video).toBe(true); expect(a.a_audio).toBe(true);
      expect(a.coupes_s.some((t) => Math.abs(t - 2) < 0.2)).toBe(true);
      expect(a.loudness?.integre_lufs).toBeLessThan(0);
      expect(existsSync(join(d, 'cache', `${a.empreinte}.json`))).toBe(true);
      expect((await analyserMedia(f, { ffmpeg: ff, cache: join(d, 'cache') })).empreinte).toBe(a.empreinte);
      expect(vueTexte('m1', a)).toContain('m1:');
    } finally { rmSync(d, { recursive: true, force: true }); }
  }, 60_000);
});
