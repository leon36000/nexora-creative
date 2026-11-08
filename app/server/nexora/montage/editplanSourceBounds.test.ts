import { randomUUID } from 'node:crypto';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { type ContexteValidation, type EditPlan, framesDe, validerEditPlan } from './editplan.js';
import { rendreEditPlan } from './rendu.js';

const basePlan = (): EditPlan => ({
  version: 1,
  fps: 24,
  format: '16:9',
  sources: { video: { kind: 'video', duree_f: 240 } },
  video: [{ id: 'p1', src: 'video', entree_f: 0, duree_f: 240, vitesse: 1, transition_in: { type: 'cut', duree_f: 0 } }],
  audio: { voix: [], ducking: { actif: false, profondeur_db: 0 }, cible_lufs: -14, crete_db: -1, fondu_coupe_ms: 30 },
  textes: [],
  generations: [],
} as EditPlan);

const ctx = (inventaire: Record<string, { duree_s: unknown }>): ContexteValidation => ({ inventaire: inventaire as ContexteValidation['inventaire'] });
const valider = (plan: unknown, contexte?: ContexteValidation) => validerEditPlan(plan, contexte);
const expectValid = (plan: unknown, contexte?: ContexteValidation) => {
  const rapport = valider(plan, contexte);
  expect(rapport.ok).toBe(true);
  expect(rapport.erreurs).toEqual([]);
};
const expectSourceRefused = (plan: unknown, contexte: ContexteValidation | undefined, path: string) => {
  const rapport = valider(plan, contexte);
  expect(rapport.ok).toBe(false);
  expect(rapport.erreurs).toEqual(expect.arrayContaining([
    expect.objectContaining({ regle: 'dans_la_source', chemin: path }),
  ]));
};

function addMusic(
  plan: EditPlan,
  sourceDureeF?: number,
  music: Partial<NonNullable<EditPlan['audio']['musique']>> = {},
) {
  plan.sources.music = { kind: 'audio', ...(sourceDureeF === undefined ? {} : { duree_f: sourceDureeF }) };
  plan.audio.musique = { src: 'music', entree_f: 0, gain_db: -8, fondu_in_f: 0, fondu_out_f: 0, ...music };
  return plan;
}

function addVoice(plan: EditPlan, sourceDureeF?: number, entreeF = 0, dureeF = 48) {
  plan.sources.voice = { kind: 'audio', ...(sourceDureeF === undefined ? {} : { duree_f: sourceDureeF }) };
  plan.audio.voix = [{ src: 'voice', debut_f: 0, entree_f: entreeF, duree_f: dureeF, gain_db: 0 }];
  return plan;
}

describe('Bornes de durée de source mesurée', () => {
  it('refuse une vidéo au-delà de la mesure même si la durée déclarée est plus longue', () => {
    const p = basePlan();
    p.sources.video.duree_f = 480;
    expectSourceRefused(p, ctx({ video: { duree_s: 2 } }), 'video.0');
  });

  it('borne la musique à l’inventaire quand sa durée est omise et garde le défaut jusqu’à la fin', () => {
    const p = addMusic(basePlan());
    expectSourceRefused(p, ctx({ video: { duree_s: 10 }, music: { duree_s: 2 } }), 'audio.musique');
  });

  it('refuse une musique déclarée plus longue que la mesure', () => {
    const pMusic = addMusic(basePlan(), 480, { duree_f: 100 });
    expectSourceRefused(pMusic, ctx({ video: { duree_s: 10 }, music: { duree_s: 2 } }), 'audio.musique');
  });

  it('refuse une voix déclarée plus longue que la mesure', () => {
    const pVoice = addVoice(basePlan(), 480, 0, 100);
    expectSourceRefused(pVoice, ctx({ video: { duree_s: 10 }, voice: { duree_s: 2 } }), 'audio.voix.0');
  });

  it('accepte une fin exactement à la mesure pour vidéo, musique et voix', () => {
    const pVideo = basePlan();
    pVideo.sources.video.duree_f = 480;
    pVideo.video[0].duree_f = 48;
    expectValid(pVideo, ctx({ video: { duree_s: 2 } }));

    const pMusic = addMusic(basePlan(), undefined, { duree_f: 48 });
    expectValid(pMusic, ctx({ video: { duree_s: 10 }, music: { duree_s: 2 } }));

    const pVoice = addVoice(basePlan(), undefined, 0, 48);
    expectValid(pVoice, ctx({ video: { duree_s: 10 }, voice: { duree_s: 2 } }));
  });

  it('conserve une durée déclarée plus courte que la mesure', () => {
    const pVideo = basePlan();
    pVideo.sources.video.duree_f = 24;
    pVideo.video[0].duree_f = 25;
    expectSourceRefused(pVideo, ctx({ video: { duree_s: 4 } }), 'video.0');

    const pMusic = addMusic(basePlan(), 24, { entree_f: 5, duree_f: 20 });
    expectSourceRefused(pMusic, ctx({ video: { duree_s: 10 }, music: { duree_s: 4 } }), 'audio.musique');

    const pVoice = addVoice(basePlan(), 24, 0, 25);
    expectSourceRefused(pVoice, ctx({ video: { duree_s: 10 }, voice: { duree_s: 4 } }), 'audio.voix.0');
  });

  it('garde les bornes déclarées en l’absence de mesure, et n’en invente aucune sans durée connue', () => {
    const pVideo = basePlan();
    pVideo.sources.video.duree_f = 60;
    pVideo.video[0].duree_f = 60;
    expectValid(pVideo);
    pVideo.video[0].duree_f = 61;
    expectSourceRefused(pVideo, undefined, 'video.0');

    const pMusic = addMusic(basePlan(), 60, { duree_f: 61 });
    expectSourceRefused(pMusic, undefined, 'audio.musique');

    const pVoice = addVoice(basePlan(), 60, 0, 61);
    expectSourceRefused(pVoice, undefined, 'audio.voix.0');
    const pUnknownVideo = basePlan();
    delete pUnknownVideo.sources.video.duree_f;
    expectValid(pUnknownVideo);
    expectValid(addVoice(basePlan(), undefined, 0, 100));
    expectValid(addMusic(basePlan()));
  });

  it.each([0, -1, Number.NaN, Number.POSITIVE_INFINITY, '2'])('ignore une mesure malformée (%s) sans la convertir en zéro', (mesuree) => {
    const p = basePlan();
    p.sources.video.duree_f = 60;
    p.video[0].duree_f = 50;
    expectValid(p, ctx({ video: { duree_s: mesuree } }));
  });

  it('retombe sur la durée déclarée si une mesure positive déborde à la conversion en images', () => {
    expect(Number.isFinite(Number.MAX_VALUE)).toBe(true);
    expect(framesDe(Number.MAX_VALUE, 24)).toBe(Infinity);
    const p = basePlan();
    p.sources.video.duree_f = 60;
    p.video[0].duree_f = 50;
    expectValid(p, ctx({ video: { duree_s: Number.MAX_VALUE } }));
  });

  it('respecte l’arrondi de framesDe pour une mesure positive', () => {
    const p = basePlan();
    delete p.sources.video.duree_f;
    p.video[0].duree_f = 48;
    expectValid(p, ctx({ video: { duree_s: 2.02 } }));
    p.video[0].duree_f = 49;
    expectSourceRefused(p, ctx({ video: { duree_s: 2.02 } }), 'video.0');
  });

  it('garde une mesure positive arrondie à zéro comme borne mesurée', () => {
    const p = basePlan();
    delete p.sources.video.duree_f;
    p.video[0].duree_f = 1;
    expectSourceRefused(p, ctx({ video: { duree_s: 0.001 } }), 'video.0');
  });

  it('refuse un plan hors source avant de résoudre les chemins ou de créer la sortie', async () => {
    const p = basePlan();
    p.sources.video.duree_f = 480;
    const dossier = join(process.env.SYNC_TEST_ROOT ?? tmpdir(), `nexora-source-bounds-${process.pid}-${randomUUID()}`);
    expect(existsSync(dossier)).toBe(false);
    let resolutions = 0;
    const result = await rendreEditPlan(
      p,
      () => { resolutions += 1; throw new Error('le chemin ne doit pas être résolu'); },
      join(dossier, 'sortie.mp4'),
      { ctx: ctx({ video: { duree_s: 2 } }), ffmpeg: '/ne-doit-pas-être-appelé' },
    );
    expect(result.ok).toBe(false);
    expect(resolutions).toBe(0);
    expect(existsSync(dossier)).toBe(false);
    if (!result.ok) expect(result.erreurs.join('\n')).toContain('[dans_la_source] video.0');
  });

  it('préserve une musique courte avec entrée non nulle et le défaut jusqu’à la fin quand la piste le permet', () => {
    const pShort = addMusic(basePlan(), 120, { entree_f: 10, duree_f: 40 });
    expectValid(pShort, ctx({ video: { duree_s: 10 }, music: { duree_s: 5 } }));

    const pDefault = addMusic(basePlan(), 240);
    expectValid(pDefault, ctx({ video: { duree_s: 10 }, music: { duree_s: 10 } }));
  });
});
