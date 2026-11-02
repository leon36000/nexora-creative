import { describe, expect, it } from 'vitest';
import { argsCarton, couperLignes, fichierAss, lireCartons, texteAss } from './cartons.js';

describe('cartons de texte posés en code', () => {
  it('coupe en lignes sur les espaces, trois lignes au plus', () => {
    expect(couperLignes('Le pain chaud dès six heures du matin', 16)).toEqual(['Le pain chaud', 'dès six heures', 'du matin']);
    expect(couperLignes('a b c d e f g h i j k l m n o p q r s t', 3)).toHaveLength(3);
  });
  it('neutralise les commandes ASS du texte', () => {
    expect(texteAss('{\\b1}Prix\\N')).toBe('Prix＼N');
  });
  it('le fichier ASS est à la taille du film et porte le texte', () => {
    const a = fichierAss('Ouvert 7 jours', { w: 480, h: 832, dureeS: 2.5 });
    expect(a).toContain('PlayResX: 480');
    expect(a).toContain('Ouvert 7 jours');
    expect(a).toContain('0:00:02.50');
  });
  it('ajoute une piste muette quand le film a du son', () => {
    expect(argsCarton('/t/c.ass', '/t/c.mp4', { w: 832, h: 480, dureeS: 2, son: true }).join(' ')).toContain('anullsrc');
    expect(argsCarton('/t/c.ass', '/t/c.mp4', { w: 832, h: 480, dureeS: 2, son: false }).join(' ')).not.toContain('anullsrc');
  });
  it('lit 3 cartons au plus, sans texte vide', () => {
    expect(lireCartons([{ texte: ' A ', position: 'debut' }, { texte: '' }, { texte: 'B' }, { texte: 'C' }, { texte: 'D' }])).toEqual([
      { texte: 'A', position: 'debut' }, { texte: 'B', position: 'fin' }, { texte: 'C', position: 'fin' },
    ]);
  });
});
