import { describe, expect, it } from 'vitest';
import { CREATION_VIDEO_COPY, creationVideoCopy, erreurVisibleCreationVideo, nomCameraCreation } from './creationVideoCopy';

describe('libellés du parcours vidéo Director', () => {
  it('fournit les mêmes champs visibles en français et en anglais', () => {
    expect(Object.keys(CREATION_VIDEO_COPY.en).sort()).toEqual(Object.keys(CREATION_VIDEO_COPY.fr).sort());
    expect(creationVideoCopy('fr').language).toBe('Langue du réalisateur');
    expect(creationVideoCopy('en').language).toBe('Director language');
  });

  it('localise la saisie, le résumé et les contrôles principaux dans les deux langues', () => {
    expect(creationVideoCopy('fr')).toMatchObject({ placeholder: 'Décris ta scène : sujet, action, décor et ambiance…', understood: 'Ce que le réalisateur a compris', format: 'Format' });
    expect(creationVideoCopy('en')).toMatchObject({ placeholder: 'Describe your scene: subject, action, setting, and mood…', understood: 'What the director understood', format: 'Format' });
    expect(creationVideoCopy('en').cameraNames['push-in']).toBe('Push in');
    expect(nomCameraCreation('en', 'push-in', 'unknown')).toBe('Push in');
    expect(nomCameraCreation('en', 'custom', 'Custom movement')).toBe('Custom movement');
    expect(creationVideoCopy('en').ideaExamples[0]).toContain('An obsidian dragon');
    expect(creationVideoCopy('en')).toMatchObject({
      modelVideo: 'Video', modelMusic: 'Music', replyLanguage: 'Spoken language',
      toastMusicMixReady: 'Your video with music is ready.',
      toast3dKeyframe: expect.stringContaining('3D view'),
    });
  });

  it('remplace les erreurs réseau opaques par un message de parcours localisé', () => {
    expect(erreurVisibleCreationVideo(new TypeError('Failed to fetch'), 'Échec.', 'Connexion impossible.')).toBe('Connexion impossible.');
    expect(erreurVisibleCreationVideo(new Error('The video engine is offline.'), 'Échec.', 'Connection failed.')).toBe('The video engine is offline.');
    expect(erreurVisibleCreationVideo(undefined, 'Échec.', 'Connexion impossible.')).toBe('Échec.');
  });
});
