import { describe, expect, it } from 'vitest';
import { requiertPhotographie, styleNonPhotographiqueDemande } from './liveAction.js';

describe('choix du médium du réalisateur', () => {
  it('réserve la recette photo par défaut aux pubs et aux films produit', () => {
    expect(requiertPhotographie('pub', 'A coffee shop video')).toBe(true);
    expect(requiertPhotographie('produit', 'A glass perfume bottle with a falling drop')).toBe(true);
    expect(requiertPhotographie('film', 'A detective finds a letter in the rain')).toBe(false);
    expect(requiertPhotographie('vfx', 'A dragon lands on a tower')).toBe(false);
  });

  it.each([
    ['une pub en dessin animé 2D', true],
    ['a 3D animated product film', true],
    ['a stop-motion claymation ad', true],
    ['un film d’animation', true],
    ['an anime short', true],
    ['an illustration of a spaceship', true],
    ['a stylized video-game style promo', true],
    ['une pub avec un style de jeu vidéo', true],
    ['animer une photo de cette femme', false],
    ['animation d’un vrai acteur dans la rue', false],
    ['animate this photo of a real actor', false],
    ['animation of a real actor walking', false],
  ])('reconnaît les styles visuels sans confondre la motion avec le médium : %s', (texte, anime) => {
    expect(styleNonPhotographiqueDemande(texte)).toBe(anime);
  });

  it.each([
    ['pas de dessin animé, une vraie prise de vues', true],
    ['not a cartoon; use live-action footage', true],
    ['no 2D animation, film the real actor', true],
    ['pas photoréaliste, fais un film en animation 3D', false],
    ['not photorealistic; use a 3D animated look', false],
    ['je ne veux pas de style anime, filme cette scène en vrai', true],
    ['I don’t want a cartoon style; shoot it live-action', true],
  ])('respecte la négation et le choix de médium : %s', (texte, photo) => {
    expect(requiertPhotographie('pub', texte)).toBe(photo);
  });

  it('prend en compte un style explicitement choisi dans les consignes de l’interface', () => {
    expect(requiertPhotographie('pub', 'coffee shop ad', ['Visual style: 2D cel animation'])).toBe(false);
    expect(requiertPhotographie('pub', 'coffee shop ad', ['Camera movement: slow tracking shot'])).toBe(true);
  });
});
