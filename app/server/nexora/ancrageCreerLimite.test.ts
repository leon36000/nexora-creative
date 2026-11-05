import { describe, expect, it } from 'vitest';
import { ancrageMaxIndisponible, CHECKPOINT_FASTH3, messageAncrageMax } from './creer.js';

describe('garde limitée aux nouvelles créations et devis', () => {
  const ref = { NEXORA_H3_MAX_CHECKPOINT: 'cinema_ref2va.safetensors' };
  it('détecte le modèle ref2va ou FastH3 annoncé comme max avec une ancre', () => {
    expect(ancrageMaxIndisponible('h3-max', true, ref)).toBe(true);
    expect(ancrageMaxIndisponible('h3-max', true, { NEXORA_H3_MAX_CHECKPOINT: CHECKPOINT_FASTH3 })).toBe(true);
    expect(ancrageMaxIndisponible('h3-max', true, {})).toBe(true);
    expect(ancrageMaxIndisponible('h3-max', true, { NEXORA_H3_MAX_CHECKPOINT: 'unknown.safetensors' })).toBe(true);
    expect(ancrageMaxIndisponible('h3-max', true, { NEXORA_H3_MAX_CHECKPOINT: 'custom_fl2va.safetensors' })).toBe(true);
  });
  it('préserve rapide, max sans image et max avec checkpoint FL2VA distinct', () => {
    expect(ancrageMaxIndisponible('h3-fast', true, ref)).toBe(false);
    expect(ancrageMaxIndisponible('h3-max', false, ref)).toBe(false);
    expect(ancrageMaxIndisponible('h3-max', true, { NEXORA_H3_MAX_CHECKPOINT: 'minimax_h3_fl2va_pruned_fp8_scaled.safetensors' })).toBe(false);
  });
  it('explique le refus dans les deux langues', () => {
    expect(messageAncrageMax('fr')).toMatch(/qualité maximale.*image ancrée/);
    expect(messageAncrageMax('en')).toMatch(/Maximum quality.*anchored image/);
  });
});
