import { describe, expect, it, vi } from 'vitest';
import { creerCopieMatte } from './matteCopy';

describe('Matte copy value formatting', () => {
  it('formats scalar values consistently in French and English', () => {
    const fr = creerCopieMatte('fr');
    const en = creerCopieMatte('en');
    expect(fr.t('mask.summary', { pourcent: '12.5', detailCalcul: '' })).toBe('Masque : 12.5 % de l’image.');
    expect(en.t('mask.summary', { pourcent: 12.5, detailCalcul: '' })).toBe('Mask: 12.5% of the frame.');
    expect(fr.t('format.sizeKB', { v: true })).toBe('true Ko');
    expect(en.t('format.sizeKB', { v: 12n })).toBe('12 KB');
  });

  it('uses the placeholder for nullish and non-scalar values without coercing them', () => {
    const fr = creerCopieMatte('fr');
    const en = creerCopieMatte('en');
    const objectToString = vi.fn(() => 'objet visible');
    const objectValue = { toString: objectToString };
    expect(fr.t('format.sizeKB', { v: null })).toBe('— Ko');
    expect(en.t('format.sizeKB', { v: undefined })).toBe('— KB');
    expect(fr.t('format.sizeKB', { v: objectValue })).toBe('— Ko');
    expect(en.t('format.sizeKB', { v: () => 'fonction visible' })).toBe('— KB');
    expect(en.t('format.sizeKB', { v: Symbol('valeur') })).toBe('— KB');
    expect(objectToString).not.toHaveBeenCalled();
  });

  it('leaves a placeholder when a value exists only on the prototype', () => {
    const values = Object.create({ v: 7 }) as Record<string, unknown>;
    expect(creerCopieMatte('en').t('format.sizeKB', values)).toBe('{v} KB');
  });

  it('preserves exact size thresholds, units, and rounding', () => {
    const fr = creerCopieMatte('fr');
    const en = creerCopieMatte('en');
    expect(fr.fmtTaille(1_000_000_001)).toBe('1.00 Go');
    expect(en.fmtTaille(1_000_000_000)).toBe('1000.0 MB');
    expect(fr.fmtTaille(1_000_001)).toBe('1.0 Mo');
    expect(en.fmtTaille(1_000_000)).toBe('1000 KB');
    expect(en.fmtTaille(-100)).toBe('0 KB');
  });
});
