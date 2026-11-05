// @vitest-environment jsdom
import { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { expect, it } from 'vitest';
import { LangueSelection } from './LangueSelection';
import type { LangueClient } from '../shared/creationLanguage';

it('sélectionne réellement la langue du film et interdit le changement durant un lancement', async () => {
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
  function Harness() {
    const [langue, choisir] = useState<LangueClient>('fr');
    return <><LangueSelection mode="film" langue={langue} libelle="Langue" occupe={false} filmPartiel={false} choisir={choisir} /><output>{langue}</output></>;
  }
  const conteneur = document.createElement('div');
  const root = createRoot(conteneur);
  await act(async () => { root.render(<Harness />); });
  const boutons = [...conteneur.querySelectorAll('button')];
  await act(async () => { boutons[1].click(); });
  expect(conteneur.querySelector('output')?.textContent).toBe('en');
  expect(boutons[1].getAttribute('aria-pressed')).toBe('true');
  expect(conteneur.querySelector('[role=group]')?.getAttribute('aria-label')).toBe('Film and dialogue language');
  await act(async () => { root.render(<LangueSelection mode="film" langue="en" libelle="Langue" occupe filmPartiel={false} choisir={() => { throw new Error('clic interdit'); }} />); });
  expect([...conteneur.querySelectorAll('button')].every((b) => b.disabled)).toBe(true);
  await act(async () => { root.unmount(); });
});
