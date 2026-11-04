import { describe, expect, it } from 'vitest';
import { ParamsSchema, secondesEstimees, versParamsMoteur } from './schema.js';

const base = { invites: [{ image: 0, points: [[0.4, 0.5, 1], [0.1, 0.1, 0]] }] };

describe('réglages du détourage', () => {
  it('valeurs par défaut et traduction vers le serveur', () => {
    const p = ParamsSchema.parse(base);
    expect(p.palier).toBe('rapide');
    expect(p.largeurMax).toBe(1920);
    const m = versParamsMoteur(p) as any;
    expect(m.etapes).toEqual(['suivi', 'matting', 'sorties']);
    expect(m.invites[0].points).toHaveLength(2);
    expect(m.source).toBe('source.mp4');
    expect(versParamsMoteur(ParamsSchema.parse({ ...base, mode: 'suivi' })).etapes).toEqual(['suivi']);
  });
  it('refuse un clic hors image, une étiquette inconnue et un travail sans clic', () => {
    expect(ParamsSchema.safeParse({ invites: [{ image: 0, points: [[1.2, 0.5, 1]] }] }).success).toBe(false);
    expect(ParamsSchema.safeParse({ invites: [{ image: 0, points: [[0.2, 0.5, 2]] }] }).success).toBe(false);
    expect(ParamsSchema.safeParse({ invites: [] }).success).toBe(false);
    expect(ParamsSchema.safeParse({ invites: [{ image: 0, points: [] }] }).success).toBe(false);
    expect(ParamsSchema.safeParse({ invites: [{ image: 0, points: [], boite: [0.1, 0.1, 0.9, 0.9] }] }).success).toBe(true);
  });
  it('borne les dimensions, la durée et les segments', () => {
    expect(ParamsSchema.safeParse({ ...base, largeurMax: 8000 }).success).toBe(false);
    expect(ParamsSchema.safeParse({ ...base, segment: { taille: 10, recouvrement: 10 } }).success).toBe(false);
    expect(ParamsSchema.safeParse({ ...base, segment: { taille: 10, recouvrement: 1 } }).success).toBe(false);
  });
  it('fond : couleur hexadécimale, nom de fichier sans chemin', () => {
    expect(ParamsSchema.safeParse({ ...base, composite: { type: 'couleur', valeur: '#12ab9f' } }).success).toBe(true);
    expect(ParamsSchema.safeParse({ ...base, composite: { type: 'couleur', valeur: 'rouge' } }).success).toBe(false);
    expect(ParamsSchema.safeParse({ ...base, composite: { type: 'image', fichier: '../../etc/passwd' } }).success).toBe(false);
    expect(ParamsSchema.safeParse({ ...base, composite: { type: 'video', fichier: 'fond-1.mp4' } }).success).toBe(true);
  });
  it('le palier pro n’a pas d’aperçu de suivi', () => {
    expect(ParamsSchema.safeParse({ ...base, palier: 'pro', mode: 'suivi' }).success).toBe(false);
  });
  it('devis : croît avec la durée et la résolution, l’aperçu coûte moins', () => {
    const p = ParamsSchema.parse(base);
    const court = secondesEstimees({ ...p, dureeS: 2, largeurMax: 1280 });
    const long = secondesEstimees({ ...p, dureeS: 8, largeurMax: 1280 });
    const hd = secondesEstimees({ ...p, dureeS: 8, largeurMax: 1920 });
    expect(long).toBeGreaterThan(court);
    expect(hd).toBeGreaterThan(long);
    expect(secondesEstimees({ ...p, dureeS: 8, largeurMax: 1280, mode: 'suivi' })).toBeLessThan(long);
  });
});
