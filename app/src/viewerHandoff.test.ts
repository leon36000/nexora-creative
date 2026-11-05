import { describe, expect, it } from 'vitest';
import { isCurrentVideoHandoff, readVideoStillHandoff, videoFromStillHref } from './viewerHandoff';

describe('handoff d’une image du Viewer vers la vidéo H3', () => {
  it.each([
    ['français', 'Un café glacé couvert de gouttes, lumière dorée.'],
    ['anglais', 'An iced coffee covered in droplets, golden light.'],
  ])('préserve la prise et le prompt en %s', (_langue, intention) => {
    const href = videoFromStillHref(42, intention);
    if (!href) throw new Error('Identifiant de prise attendu valide');
    const url = new URL(href, 'http://nexora.local');
    expect(url.pathname).toBe('/');
    expect(url.searchParams.get('mode')).toBe('video');
    expect(url.searchParams.get('cle')).toBe('42');
    expect(url.searchParams.get('intention')).toBe(intention);
    expect(url.searchParams.get('handoff')).toBeTruthy();
    expect(readVideoStillHandoff(url.searchParams.get('mode')!, url.searchParams)).toMatchObject({ takeId: 42, intention });
  });

  it('conserve le parcours H3 avec photo si la prise n’a pas de prompt', () => {
    const href = videoFromStillHref(42);
    if (!href) throw new Error('Identifiant de prise attendu valide');
    const url = new URL(href, 'http://nexora.local');
    expect(url.searchParams.get('mode')).toBe('video');
    expect(url.searchParams.get('cle')).toBe('42');
    expect(url.searchParams.has('intention')).toBe(false);
    expect(readVideoStillHandoff(url.searchParams.get('mode')!, url.searchParams)).toMatchObject({ takeId: 42 });
  });

  it('ignore les identifiants de prise invalides', () => {
    expect(videoFromStillHref(0)).toBeNull();
    expect(videoFromStillHref(42.5)).toBeNull();
    expect(videoFromStillHref(Number.MAX_SAFE_INTEGER + 1)).toBeNull();
    expect(readVideoStillHandoff('video', new URLSearchParams('cle=0'))).toBeNull();
    expect(readVideoStillHandoff('video', new URLSearchParams('cle=42.5'))).toBeNull();
    expect(readVideoStillHandoff('video', new URLSearchParams('cle=9007199254740992'))).toBeNull();
    expect(readVideoStillHandoff('image', new URLSearchParams('cle=42&intention=old'))).toBeNull();
  });

  it('attribue une clé distincte à chaque sélection du même plan', () => {
    const first = new URL(videoFromStillHref(42)!, 'http://nexora.local').searchParams.get('handoff');
    const second = new URL(videoFromStillHref(42)!, 'http://nexora.local').searchParams.get('handoff');
    expect(first).toBeTruthy();
    expect(second).toBeTruthy();
    expect(second).not.toBe(first);
  });

  it('invalide une réponse après changement de mode, de locale ou de génération', () => {
    const routeInitiale = '/?mode=video&locale=fr';
    expect(isCurrentVideoHandoff(4, 4, routeInitiale, routeInitiale)).toBe(true);
    expect(isCurrentVideoHandoff(4, 5, routeInitiale, routeInitiale)).toBe(false);
    expect(isCurrentVideoHandoff(4, 4, routeInitiale, '/?mode=video&locale=en')).toBe(false);
    expect(isCurrentVideoHandoff(4, 4, routeInitiale, '/?mode=image&locale=fr')).toBe(false);
  });
});
