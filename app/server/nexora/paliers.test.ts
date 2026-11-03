import { describe, expect, it } from 'vitest';
import { palierDuRole, palierSuivant, paliersDisponibles } from './paliers.js';

const cles = { NEXORA_LLM_CLE_DEEPINFRA: 'a', NEXORA_LLM_CLE_OPENROUTER: 'b' } as any;
describe('choix du palier', () => {
  it('défauts : tournage et montage en Éco, Producteur en Expert', () => {
    expect(palierDuRole('tournage', { env: cles, reglages: {} })).toBe('eco');
    expect(palierDuRole('montage', { env: cles, reglages: {} })).toBe('eco');
    expect(palierDuRole('producteur', { env: cles, reglages: {} })).toBe('expert');
  });
  it('ordre : projet > réglage du site > variable du rôle > variable globale', () => {
    expect(palierDuRole('montage', { projet: 'equilibre', env: { ...cles, NEXORA_PALIER: 'expert' }, reglages: { montage: 'palier:expert' } })).toBe('equilibre');
    expect(palierDuRole('montage', { env: { ...cles, NEXORA_PALIER: 'equilibre' }, reglages: { montage: 'palier:expert' } })).toBe('expert');
    expect(palierDuRole('montage', { env: { ...cles, NEXORA_PALIER_MONTAGE: 'expert', NEXORA_PALIER: 'equilibre' }, reglages: {} })).toBe('expert');
    expect(palierDuRole('montage', { env: { ...cles, NEXORA_PALIER: 'equilibre' }, reglages: {} })).toBe('equilibre');
  });
  it('un palier sans clé laisse la place au premier disponible ; aucune clé : null', () => {
    expect(palierDuRole('producteur', { env: { NEXORA_LLM_CLE_DEEPINFRA: 'a' } as any, reglages: {} })).toBe('eco');
    expect(palierDuRole('producteur', { env: {} as any, reglages: {} })).toBeNull();
  });
  it('escalade : suivant disponible, jamais au-delà d’Expert', () => {
    expect(palierSuivant('eco', cles)).toBe('equilibre');
    expect(palierSuivant('equilibre', cles)).toBe('expert');
    expect(palierSuivant('expert', cles)).toBeNull();
    expect(palierSuivant('eco', { NEXORA_LLM_CLE_DEEPINFRA: 'a' } as any)).toBeNull();
    expect(paliersDisponibles(cles)).toEqual({ eco: true, equilibre: true, expert: true });
  });
});
