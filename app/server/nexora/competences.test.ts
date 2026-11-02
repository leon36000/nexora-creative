import { describe, expect, it } from 'vitest';
import { competencesPour, lireCompetence, listeCompetences } from './competences.js';

describe('compétences (procédures versionnées des rôles LLM)', () => {
  it('lit l’en-tête : nom, version, rôles, description', () => {
    const c = lireCompetence('---\nname: essai\nversion: 3\nroles: [juge, producteur]\ndescription: Une ligne.\n---\nCorps du texte.\n', 'essai.md');
    expect(c).toEqual({ nom: 'essai', version: 3, roles: ['juge', 'producteur'], description: 'Une ligne.', texte: 'Corps du texte.' });
  });
  it('refuse un fichier sans en-tête ou sans rôle', () => {
    expect(() => lireCompetence('pas d’en-tête', 'x.md')).toThrow();
    expect(() => lireCompetence('---\nname: x\nversion: 1\nroles: []\n---\ntexte', 'x.md')).toThrow();
  });
  it('les fichiers du dépôt sont valides, versionnés et sous le plafond de 8 000 jetons par rôle', () => {
    const toutes = listeCompetences();
    expect(toutes.map((c) => c.nom).sort()).toEqual(['juge', 'montage', 'montage-outils', 'montage-plan', 'producteur', 'publication', 'realisation']);
    for (const role of ['producteur', 'realisation', 'assistant', 'publication', 'juge'] as const) {
      const t = competencesPour(role);
      expect(t.length).toBeGreaterThan(100);
      expect(t.length / 4).toBeLessThan(8000);
    }
  });
  it('un rôle reçoit seulement ses compétences, avec leur version', () => {
    const p = competencesPour('producteur');
    expect(p).toContain('[compétence producteur v1]');
    expect(p).toContain('[compétence realisation v1]');
    expect(p).not.toContain('[compétence juge');
    expect(competencesPour('idees')).toBe('');
  });
});
