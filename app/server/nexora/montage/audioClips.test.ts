import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type EditPlan, type PlanVideo } from './editplan.js';
import { audioDesClips, filtresTempo } from './audioClips.js';

const { segmentsVitesseMock } = vi.hoisted(() => ({ segmentsVitesseMock: vi.fn() }));
vi.mock('./retiming.js', () => ({ segmentsVitesse: segmentsVitesseMock }));

const clip = (src: string, duree_f: number, overrides: Partial<PlanVideo> = {}): PlanVideo => ({
  id: `plan-${src}`,
  src,
  entree_f: 0,
  duree_f,
  vitesse: 1,
  transition_in: { type: 'cut', duree_f: 0 },
  ...overrides,
});

const planPour = (
  fps: 24 | 25 | 30,
  video: EditPlan['video'],
  sources: EditPlan['sources'],
  fondu_coupe_ms = 30,
): EditPlan => ({
  version: 1,
  fps,
  format: '16:9',
  sources,
  video,
  audio: {
    voix: [],
    ducking: { actif: false, profondeur_db: 0 },
    cible_lufs: -14,
    crete_db: -1,
    fondu_coupe_ms,
  },
  textes: [],
  generations: [],
});

const sourceVideo = (a_audio?: boolean): EditPlan['sources'][string] => ({
  kind: 'video',
  duree_f: 500,
  ...(a_audio === undefined ? {} : { a_audio }),
});

describe('filtresTempo', () => {
  it('décompose les vitesses usuelles sans changer leur produit', () => {
    for (const [vitesse, attendu] of [
      [0.25, 'atempo=0.5,atempo=0.5'],
      [0.5, 'atempo=0.5'],
      [1, ''],
      [2, 'atempo=2'],
      [4, 'atempo=2,atempo=2'],
    ] as const) {
      expect(filtresTempo(vitesse)).toBe(attendu);
      const facteurs = attendu ? attendu.split(',').map((f) => Number(f.slice('atempo='.length))) : [];
      expect(facteurs.reduce((produit, facteur) => produit * facteur, 1)).toBe(vitesse);
    }
  });

  it('refuse zéro, valeurs négatives et nombres non finis', () => {
    for (const vitesse of [0, -0.25, Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
      expect(() => filtresTempo(vitesse)).toThrow(RangeError);
    }
  });

  it('garde chaque facteur dans la plage WSOLA attendue', () => {
    for (const vitesse of [0.125, 0.25, 0.5, 1, 2, 4, 8]) {
      const chaine = filtresTempo(vitesse);
      const facteurs = chaine ? chaine.split(',').map((f) => Number(f.slice('atempo='.length))) : [];
      expect(facteurs.every((f) => f >= 0.5 && f <= 2)).toBe(true);
      expect(facteurs.reduce((produit, facteur) => produit * facteur, 1)).toBeCloseTo(vitesse, 12);
    }
  });
});

describe('audioDesClips', () => {
  beforeEach(() => {
    segmentsVitesseMock.mockReset();
    segmentsVitesseMock.mockImplementation((p: PlanVideo) => [{
      entree_f: p.entree_f,
      duree_f: p.duree_f,
      source_f: Math.round(p.duree_f * p.vitesse),
      vitesse: p.vitesse,
    }]);
  });

  it('ajoute une piste uniquement si la source mesure a_audio=true', () => {
    const plan = planPour(24, [clip('avec-son', 12)], { 'avec-son': sourceVideo(true) });
    const result = audioDesClips(plan, new Map([['avec-son', 2]]));

    expect(result.pistes).toEqual(['sonclip0']);
    expect(result.filtres.join('\n')).toContain('[2:a]');
  });

  it('laisse silencieuses les sources false et les anciens plans sans mesure', () => {
    for (const [id, src] of [['mesuré-silencieux', sourceVideo(false)], ['ancien-plan', sourceVideo()]] as const) {
      const plan = planPour(24, [clip(id, 12)], { [id]: src });
      expect(audioDesClips(plan, new Map()).pistes).toEqual([]);
      expect(audioDesClips(plan, new Map()).filtres).toEqual([]);
    }
  });

  it('exige une valeur booléenne strictement vraie, pas une valeur seulement truthy', () => {
    const src = { kind: 'video' as const, duree_f: 500, a_audio: 1 as unknown as boolean };
    const plan = planPour(24, [clip('flag-malformé', 12)], { 'flag-malformé': src });

    expect(audioDesClips(plan, new Map()).pistes).toEqual([]);
  });

  it('refuse une source sonore mesurée absente de la map sans bloquer un clip silencieux', () => {
    const audible = planPour(24, [clip('audible', 12)], { audible: sourceVideo(true) });
    expect(() => audioDesClips(audible, new Map())).toThrow('Source audio du clip introuvable.');

    const silencieux = planPour(24, [clip('silencieux', 12)], { silencieux: sourceVideo(false) });
    expect(audioDesClips(silencieux, new Map())).toEqual({ filtres: [], pistes: [] });
  });

  it('convertit les bornes et durées en échantillons exacts à 24, 25 et 30 fps', () => {
    for (const [fps, echantillonsParImage] of [[24, 2000], [25, 1920], [30, 1600]] as const) {
      const plan = planPour(fps, [clip('clip', 12, { entree_f: 7 })], { clip: sourceVideo(true) });
      const result = audioDesClips(plan, new Map([['clip', 0]]));
      const filtre = result.filtres.join('\n');

      expect(filtre).toContain(`atrim=start_sample=${7 * echantillonsParImage}:end_sample=${19 * echantillonsParImage}`);
      expect(filtre).toContain(`apad=whole_len=${12 * echantillonsParImage}`);
      expect(filtre).toContain(`atrim=end_sample=${12 * echantillonsParImage}`);
    }
  });

  it('aligne le décalage de piste et le remplissage sur la ligne de temps chevauchée', () => {
    const plan = planPour(24, [
      clip('premier', 12),
      clip('second', 12, { transition_in: { type: 'fondu', duree_f: 4 } }),
    ], { premier: sourceVideo(false), second: sourceVideo(true) });
    const result = audioDesClips(plan, new Map([['second', 3]]));
    const filtre = result.filtres.join('\n');

    expect(result.pistes).toEqual(['sonclip1']);
    expect(filtre).toContain('adelay=16000S:all=1');
    expect(filtre).toContain('apad=whole_len=40000');
    expect(filtre).toContain('atrim=end_sample=40000');
  });

  it('fait correspondre les fondus audio aux transitions entrante et sortante', () => {
    const plan = planPour(24, [
      clip('a', 12),
      clip('b', 12, { transition_in: { type: 'dip', duree_f: 4 } }),
    ], { a: sourceVideo(true), b: sourceVideo(true) });
    const result = audioDesClips(plan, new Map([['a', 0], ['b', 1]]));

    expect(result.filtres[1]).toContain('afade=t=in:ss=0:ns=1440');
    expect(result.filtres[1]).toContain('afade=t=out:ss=16000:ns=8000');
    expect(result.filtres[3]).toContain('afade=t=in:ss=0:ns=8000');
    expect(result.filtres[3]).toContain('afade=t=out:ss=22560:ns=1440');
  });

  it('rend chaque morceau de rampe à sa vitesse et concatène les échantillons produits', () => {
    segmentsVitesseMock.mockReturnValue([
      { entree_f: 4, duree_f: 4, source_f: 2, vitesse: 0.5 },
      { entree_f: 6, duree_f: 6, source_f: 12, vitesse: 2 },
    ]);
    const plan = planPour(24, [clip('rampe', 10, { entree_f: 4, rampe: { de: 0.5, a: 2 } })], { rampe: sourceVideo(true) });
    const filtre = audioDesClips(plan, new Map([['rampe', 0]])).filtres.join('\n');

    expect(filtre).toContain('sonclip0s0');
    expect(filtre).toContain('atrim=start_sample=8000:end_sample=12000');
    expect(filtre).toContain('atempo=0.5');
    expect(filtre).toContain('sonclip0s1');
    expect(filtre).toContain('atrim=start_sample=12000:end_sample=36000');
    expect(filtre).toContain('atempo=2');
    expect(filtre).toContain('concat=n=2:v=0:a=1');
    expect(filtre).toContain('apad=whole_len=20000');
  });

  it('garde l’ordre des pistes audibles et saute les clips sans son mesuré', () => {
    const plan = planPour(25, [clip('muet', 10), clip('voix-et-clip', 12), clip('musique-clip', 8)], {
      muet: sourceVideo(false),
      'voix-et-clip': sourceVideo(true),
      'musique-clip': sourceVideo(true),
    });
    const result = audioDesClips(plan, new Map([['voix-et-clip', 4], ['musique-clip', 6]]));

    expect(result.pistes).toEqual(['sonclip1', 'sonclip2']);
    expect(result.filtres.join('\n')).toContain('adelay=19200S:all=1');
    expect(result.filtres.join('\n')).toContain('adelay=42240S:all=1');
  });

  it('ignore les images et les fichiers audio même marqués sonores', () => {
    for (const kind of ['image', 'audio'] as const) {
      const plan = planPour(24, [clip('s', 12)], { s: { kind, a_audio: true } });
      expect(audioDesClips(plan, new Map())).toEqual({ filtres: [], pistes: [] });
    }
  });

  it('ignore une source héritée du prototype', () => {
    const plan = planPour(24, [clip('s', 12)], Object.create({ s: sourceVideo(true) }));
    expect(audioDesClips(plan, new Map())).toEqual({ filtres: [], pistes: [] });
  });

  it('ne modifie ni le plan ni les index d’entrée', () => {
    const plan = planPour(30, [clip('stable', 12, { entree_f: 3 })], { stable: sourceVideo(true) });
    const index = new Map([['stable', 9]]);
    const planAvant = JSON.stringify(plan);
    const indexAvant = [...index.entries()];

    audioDesClips(plan, index);

    expect(JSON.stringify(plan)).toBe(planAvant);
    expect([...index.entries()]).toEqual(indexAvant);
  });
});
