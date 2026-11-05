// @vitest-environment jsdom
import { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { expect, it, vi } from 'vitest';
import { EchecFilmPartiel } from './api';
import { FilmPartielAlerte } from './FilmPartielAlerte';
import FilmPlans from './FilmPlans';

vi.mock('./store', () => {
  const takes = [5, 7].map((id) => ({ id, status: 'failed', settings: JSON.stringify({ film: true, storyboard: { titre: `Film ${id}`, plans: [] } }) }));
  return { useStore: (select: (s: unknown) => unknown) => select({ takes }), settingsOf: (t: { settings: string }) => JSON.parse(t.settings), toast: vi.fn() };
});

it('le bouton React ouvre réellement les plans du film en conflit, sans relance', async () => {
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
  const rafraichir = vi.fn(async () => {}), ouvrirPrise = vi.fn(), nouveauFilm = vi.fn();
  const erreur = new EchecFilmPartiel('panne', 5, [{ plan: 0, takeId: 101 }], true, { filmId: 7, plan: 0, takeId: 102 });
  function Harness() {
    const [film, setFilm] = useState<number | null>(null);
    return <><FilmPartielAlerte erreur={erreur} langue="fr" rafraichir={rafraichir} existe={(id) => id === 7} ouvrirFilm={setFilm} ouvrirPrise={ouvrirPrise} indisponible={() => {}} nouveauFilm={nouveauFilm} />
      {film !== null && <FilmPlans filmId={film} onClose={() => setFilm(null)} />}</>;
  }
  const conteneur = document.createElement('div');
  document.body.append(conteneur);
  const root = createRoot(conteneur);
  await act(async () => { root.render(<Harness />); });
  const bouton = [...conteneur.querySelectorAll('button')].find((b) => b.textContent === 'Voir les plans');
  expect(bouton).toBeDefined();
  await act(async () => { bouton!.click(); });
  expect(rafraichir).toHaveBeenCalledOnce();
  expect(conteneur.querySelector('[role="dialog"]')?.getAttribute('aria-label')).toBe('Plans du film Film 7');
  expect(ouvrirPrise).not.toHaveBeenCalled();
  expect(nouveauFilm).not.toHaveBeenCalled();
  await act(async () => { root.unmount(); });
});
