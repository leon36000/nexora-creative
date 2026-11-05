import { describe, expect, it } from 'vitest';
import { consignesAmeliorationCreation, erreurAmeliorationCreation, erreurImageCreation, ideesRepliCreation, lireLangueClient, messageErreurRendu } from './creationLanguage.js';

describe('langue du parcours Créer', () => {
  it('accepte seulement les langues explicites fr/en et garde les autres absentes', () => {
    expect(lireLangueClient('fr')).toBe('fr');
    expect(lireLangueClient('en')).toBe('en');
    expect(lireLangueClient(undefined)).toBeUndefined();
    expect(lireLangueClient('es')).toBeUndefined();
  });

  it('garde les exemples français par défaut et propose leur équivalent anglais sur demande', () => {
    expect(ideesRepliCreation('video', undefined)[0]).toContain('Un dragon');
    expect(ideesRepliCreation('video', 'en')[0]).toContain('An obsidian dragon');
  });

  it('adapte les consignes et les erreurs du bouton d’amélioration à la langue choisie', () => {
    expect(consignesAmeliorationCreation(undefined, 'video')).toContain('en français');
    expect(consignesAmeliorationCreation('en', 'video')).toContain('in English');
    expect(consignesAmeliorationCreation('en', 'video')).toContain('one clear action');
    expect(erreurAmeliorationCreation(undefined, 'echec')).toBe('L’assistant n’a pas pu améliorer ta phrase. Réessaie.');
    expect(erreurAmeliorationCreation('en', 'echec')).toBe('The writing assistant could not improve your prompt. Please try again.');
  });

  it('localise les erreurs de validation de l’étape de création des plans clés', () => {
    expect(erreurImageCreation(undefined, 'descriptionVide')).toBe('Décris l’image que tu veux.');
    expect(erreurImageCreation('en', 'descriptionVide')).toBe('Describe the image you want.');
    expect(erreurImageCreation('en', 'descriptionLongue')).toContain('4,000 characters');
  });

  it('garde le message API historique quand aucune langue n’est fournie', () => {
    expect(messageErreurRendu(undefined, 'Montage FR.', 'Cut EN.', 'A cut is made from its shots. Use /api/director/scene (Recreate in the app does).'))
      .toBe('A cut is made from its shots. Use /api/director/scene (Recreate in the app does).');
    expect(messageErreurRendu('en', 'Montage FR.', 'Cut EN.', 'Legacy EN.')).toBe('Cut EN.');
    expect(messageErreurRendu('fr', 'Montage FR.', 'Cut EN.', 'Legacy EN.')).toBe('Montage FR.');
  });
});
