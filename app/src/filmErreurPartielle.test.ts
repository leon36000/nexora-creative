import { afterEach, expect, it, vi } from 'vitest';
import { api, EchecFilmPartiel } from './api';
import { filmPartielAConsulter, ouvrirCiblePartielle } from './filmPartielActions';

afterEach(() => vi.unstubAllGlobals());

it('transmet les identifiants partiels en cas d’échec du tournage', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ error: 'moteur indisponible', filmId: 1, prises: [{ plan: 0, takeId: 101 }] }), { status: 400 })));
  const storyboard = { titre: 'test', bible: { style: '', personnages: [], lieux: [] }, plans: [], dureeTotale: 0 };
  try {
    await api.nexoraFilmTourner({ storyboard, format: '16:9', son: false, intention: 'test' });
    throw new Error('une erreur était attendue');
  } catch (e) {
    expect(e).toBeInstanceOf(EchecFilmPartiel);
    expect(e).toMatchObject({ message: 'moteur indisponible', filmId: 1, prises: [{ plan: 0, takeId: 101 }] });
  }
});

it('ouvre le film en conflit seulement après actualisation, sans autre action', async () => {
  const rafraichir = vi.fn(async () => {}), ouvrir = vi.fn();
  const id = filmPartielAConsulter({ filmId: 5, conflit: { filmId: 7 } });
  expect(await ouvrirCiblePartielle(id, rafraichir, (cible) => cible === 7, ouvrir)).toBe(true);
  expect(rafraichir).toHaveBeenCalledOnce();
  expect(ouvrir).toHaveBeenCalledExactlyOnceWith(7);
  expect(await ouvrirCiblePartielle(9, rafraichir, () => false, ouvrir)).toBe(false);
  expect(ouvrir).toHaveBeenCalledOnce();
});

it('rejette les identifiants erronés avant de proposer une action de récupération', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ error: 'panne', filmId: -1, prises: [{ plan: 0, takeId: 101 }] }), { status: 400 })));
  const storyboard = { titre: 'test', bible: { style: '', personnages: [], lieux: [] }, plans: [], dureeTotale: 0 };
  const promesse = api.nexoraFilmTourner({ storyboard, format: '16:9', son: false, intention: 'test' });
  await expect(promesse).rejects.not.toBeInstanceOf(EchecFilmPartiel);
  const rafraichir = vi.fn(async () => {}), ouvrir = vi.fn();
  expect(await ouvrirCiblePartielle(-1, rafraichir, () => true, ouvrir)).toBe(false);
  expect(rafraichir).not.toHaveBeenCalled();
  expect(ouvrir).not.toHaveBeenCalled();
});

it('ne propose pas un conflit dont les identifiants sont invalides', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ error: 'panne', filmId: 5, prises: [], conflit: { filmId: -7, plan: 0, takeId: 102 } }), { status: 400 })));
  const storyboard = { titre: 'test', bible: { style: '', personnages: [], lieux: [] }, plans: [], dureeTotale: 0 };
  await expect(api.nexoraFilmTourner({ storyboard, format: '16:9', son: false, intention: 'test' })).rejects.not.toBeInstanceOf(EchecFilmPartiel);
});
