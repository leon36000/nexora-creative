import { describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { avecGardeNouveauRendu, nouveauRenduAncreMaxInvalide, raisonRefusNouveauRendu, GENRES_NON_H3 } from './gardeNouveauRendu.js';
import { buildH3Graph, H3_MODELS } from '../graphs/h3.js';

const fast = 'fastvideo_fasth3_8step_v2_pruned_nvfp4.safetensors';
const cin = '10Eros_Max_h3_8stepTURBO_beta7_SingularityV2_ref2va_int8HQ.safetensors';
const base = { kind: 'video', videoModel: 'h3-max', startImage: 'photo' };

describe('protection externe des nouveaux rendus', () => {
  it.each([undefined, fast, cin, 'unknown.safetensors', 'custom_fl2va.safetensors', ''])('refuse avant le helper le checkpoint %s', (checkpoint) => {
    const generate = vi.fn(() => 'enqueued');
    const refuse = vi.fn(() => 'refused');
    expect(avecGardeNouveauRendu({ ...base, checkpoint }, generate, refuse)).toBe('refused');
    expect(generate).not.toHaveBeenCalled();
    expect(refuse).toHaveBeenCalledOnce();
  });
  it('maintient la liste non-H3 alignée avec les comparaisons explicites de graphFor', () => {
    const source = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
    const debut = source.indexOf('async function graphFor(');
    const fin = source.indexOf(' * Director post passes', debut);
    expect(debut).toBeGreaterThanOrEqual(0);
    expect(fin).toBeGreaterThan(debut);
    const repartiteur = source.slice(debut, fin);
    const genres = [...repartiteur.matchAll(/\bb\.kind\s*===\s*(['"])([^'"]+)\1/g)].map((m) => m[2]);
    expect([...new Set(genres)].sort()).toEqual([...GENRES_NON_H3].sort());
  });
  it('refuse les kinds inconnus avant le helper, y compris en variante', () => {
    const generate = vi.fn();
    const refuse = vi.fn();
    avecGardeNouveauRendu({ ...base, kind: 'other', checkpoint: fast }, generate, refuse);
    expect(generate).not.toHaveBeenCalled();
    expect(refuse).toHaveBeenCalledWith('INVALID_KIND');
    expect(raisonRefusNouveauRendu({ ...base, variants: [{ kind: 'other' }] })).toBe('INVALID_KIND');
    expect(raisonRefusNouveauRendu({ ...base, kind: 'other', checkpoint: H3_MODELS.fl2va })).toBe('INVALID_KIND');
  });
  it.each(['still','effect','reshoot','reshoot-preview','mirror','edit','extend','transition','speak','sound','musique','object','stage','stage-look','upscale','cutout','restyle','swap','seam','hdr'])('ne bloque pas la branche non-H3 %s', (kind) => {
    expect(raisonRefusNouveauRendu({ ...base, kind, checkpoint: fast })).toBeNull();
  });
  it('accepte un FL2VA sélectionné explicitement par le graphe', () => {
    expect(nouveauRenduAncreMaxInvalide({ ...base, checkpoint: H3_MODELS.fl2va })).toBe(false);
    const graph = buildH3Graph({ prompt: '', width: 1344, height: 768, lengthFrames: 124, seed: 0, steps: 8, startImage: 'photo', checkpoint: H3_MODELS.fl2va });
    expect(graph.u).toMatchObject({ inputs: { unet_name: H3_MODELS.fl2va } });
  });
  it('couvre dernière image et variantes tout en préservant les autres modèles', () => {
    expect(nouveauRenduAncreMaxInvalide({ kind: 'video', videoModel: 'h3-max', endImage: 'fin', checkpoint: fast })).toBe(true);
    expect(nouveauRenduAncreMaxInvalide({ kind: 'video', videoModel: 'h3-max', variants: [{ startImage: 'photo', checkpoint: fast }] })).toBe(true);
    expect(nouveauRenduAncreMaxInvalide({ ...base, videoModel: 'h3-fast', checkpoint: fast })).toBe(false);
    expect(nouveauRenduAncreMaxInvalide({ ...base, kind: 'still', checkpoint: fast })).toBe(false);
    expect(nouveauRenduAncreMaxInvalide({ videoModel: 'h3-max', checkpoint: fast })).toBe(false);
  });
});
