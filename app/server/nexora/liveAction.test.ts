import { describe, expect, it } from 'vitest';
import { estSpatial, horsParoles, motsRenduInterdits, nettoyerRepli, requiertPhotographie, STYLE_LIVE_ACTION, styleNonPhotographiqueDemande, verifierRecetteLiveAction, verifierVaisseauxOriginaux } from './liveAction.js';

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
    ['an anime scene for a coffee ad', true],
    ['an anime battle in a coffee ad', true],
    ['une pub en anime de combat', true],
    ['une pub en style anime', true],
    ['an illustration of a spaceship', true],
    ['a stylized video-game style promo', true],
    ['une pub avec un style de jeu vidéo', true],
    ['animer une photo de cette femme', false],
    ['anime cette photo pour une pub', false],
    ['animation d’un vrai acteur dans la rue', false],
    ['animate this photo of a real actor', false],
    ['animation of a real actor walking', false],
  ])('reconnaît les styles visuels sans confondre la motion avec le médium : %s', (texte, anime) => {
    expect(styleNonPhotographiqueDemande(texte)).toBe(anime);
  });

  it('applique bien le style anime de combat FR aux publicités', () => {
    expect(requiertPhotographie('pub', 'une pub en anime de combat')).toBe(false);
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

  it('ne confond pas le verbe français « anime » avec un style visuel', () => {
    expect(requiertPhotographie('pub', 'anime cette photo pour une pub')).toBe(true);
    expect(requiertPhotographie('pub', 'une pub en style anime')).toBe(false);
  });

  it('ignore les slogans cités lors du choix de médium', () => {
    expect(requiertPhotographie('pub', 'A photorealistic coffee ad with the sign "anime scene".')).toBe(true);
    expect(requiertPhotographie('pub', 'A photorealistic coffee ad with the sign “not photorealistic”.')).toBe(true);
  });

  it('ne traite pas le slogan terrestre « Moon » comme une scène spatiale', () => {
    const intention = 'A photorealistic coffee shop ad with the sign "Moon".';
    expect(estSpatial(intention)).toBe(false);
    expect(verifierRecetteLiveAction(STYLE_LIVE_ACTION, intention, 'pub')).toEqual([]);
  });

  it('ne demande pas un vaisseau quand la scène spatiale ne contient qu’un astronaute', () => {
    expect(verifierVaisseauxOriginaux('An astronaut walks on the Moon.', 'An astronaut walks on the Moon.')).toEqual([]);
    expect(verifierVaisseauxOriginaux('An astronaut walks alone on the Moon.', 'An astronaut walks alone on the Moon without a spacecraft.')).toEqual([]);
    expect(verifierVaisseauxOriginaux('An astronaut walks alone on the Moon.', 'An astronaut walks alone beneath a sign reading "SPACECRAFT".')).toEqual([]);
    expect(verifierVaisseauxOriginaux('Un astronaute marche seul sur la Lune.', 'Un astronaute marche seul sur la Lune sans vaisseau.')).toEqual([]);
    expect(verifierVaisseauxOriginaux('An original spacecraft passes the Moon.', 'A spacecraft passes the Moon.')).toEqual([]);
    expect(verifierVaisseauxOriginaux('A crater under moonlight.', 'A spacecraft passes the Moon.')).toContain('space: preserve the requested spacecraft and use an original purpose-built design');
    expect(verifierVaisseauxOriginaux('A crater under moonlight.', 'Space fighters cross the Moon.')).toContain('space: preserve the requested spacecraft and use an original purpose-built design');
    expect(verifierVaisseauxOriginaux('An astronaut walks without an original spacecraft on the Moon.', 'A spacecraft passes the Moon.')).toContain('space: preserve the requested spacecraft and use an original purpose-built design');
    expect(verifierVaisseauxOriginaux('A spacecraft passes the Moon.', 'A spacecraft passes the Moon.')).toContain('space: use original purpose-built spacecraft designs');
    expect(verifierVaisseauxOriginaux('A battleship passes the Moon.', 'A spacecraft passes the Moon.')).toContain('space: replace real military aircraft and naval vessels with original spacecraft');
    expect(verifierVaisseauxOriginaux('An original spacecraft passes the Moon, without a battleship.', 'A spacecraft passes the Moon.')).toEqual([]);
  });

  it('exclut les citations droites, françaises et courbes des contrôles de rendu', () => {
    const citations = '"cinematic" «cinematic» “cinematic”';
    expect(horsParoles(citations).trim()).toBe('');
    expect(motsRenduInterdits(citations)).toEqual([]);
    expect(motsRenduInterdits(`${citations} cinematic`)).toEqual(['cinematic']);
  });

  it.each(['"cinematic  Ferrari"', '«cinematic  Ferrari»', '“cinematic  Ferrari”'])('préserve exactement la citation %s pendant le repli', (citation) => {
    const nettoye = nettoyerRepli(`cinematic Ferrari outside; ${citation}`);
    expect(nettoye).toContain(citation);
    expect(nettoye).toContain('unbranded sports car');
    expect(horsParoles(nettoye)).not.toMatch(/cinematic|Ferrari/i);
  });
});
