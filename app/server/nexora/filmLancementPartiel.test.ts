import { beforeEach, expect, it, vi } from 'vitest';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import ts from 'typescript';

const memoire = vi.hoisted(() => ({ lignes: new Map<number, any>(), echecPatch: new Set<number>(), reecritures: [] as any[], outputDir: '/non-utilise' }));
vi.mock('../config.js', () => ({ config: { get outputDir() { return memoire.outputDir; }, ffmpegBin: 'ffmpeg-fictif' } }));
vi.mock('node:child_process', () => ({ execFile: (_bin: unknown, _args: unknown, cb: (e: null, out: string, err: string) => void) => cb(null, '', '') }));
vi.mock('../jobs.js', () => ({ takes: {
  create: ({ settings }: any) => { memoire.lignes.set(1, { id: 1, status: 'queued', settings: JSON.stringify(settings) }); return 1; },
  get: (id: number) => memoire.lignes.get(id),
  organisationDe: () => 'local',
  setSettings: (id: number, settings: unknown) => { memoire.lignes.get(id).settings = JSON.stringify(settings); },
  patchSettings: (id: number, patch: Record<string, unknown>) => { if (memoire.echecPatch.has(id)) throw new Error('écriture impossible'); const t = memoire.lignes.get(id); t.settings = JSON.stringify({ ...JSON.parse(t.settings), ...patch }); },
  fail: (id: number, error: string) => { Object.assign(memoire.lignes.get(id), { status: 'failed', error }); },
} }));
vi.mock('./reecritureH3.js', () => ({ reecrireH3: async (entree: any) => { memoire.reecritures.push(entree); return { prompt: 'plan', source: 'repli' }; } }));
vi.mock('./personnagesCast.js', () => ({ resoudrePersonnages: vi.fn() }));
vi.mock('./encodageGpu.js', () => ({ encoderSurGpu: vi.fn() }));
import { avancerFilm, initFilms, marquerReservationFilmLiberee, tournerFilm } from './filmMoteur.js';
import { lireStoryboard } from './film.js';
import { EchecTournage, resultatEchecTournage, soumissionIndeterminee } from './filmEchec.js';

beforeEach(() => { memoire.lignes.clear(); memoire.echecPatch.clear(); memoire.reecritures.length = 0; memoire.outputDir = '/non-utilise'; });

it('rattache au bon plan les prises déjà lancées malgré un échec partiel de queue', async () => {
  const erreur = Object.assign(new Error('moteur indisponible'), { takeIds: [202] });
  const queueTakes = vi.fn()
    .mockImplementationOnce(async (corps, _n, credits) => { memoire.lignes.set(101, { id: 101, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) }); return [101]; })
    .mockImplementationOnce(async (corps, _n, credits) => { memoire.lignes.set(202, { id: 202, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0], nexoraSoumission: 'indeterminee' }) }); throw erreur; });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'Film test', plans: [
    { resume: 'un', description: 'un', duree: 5 },
    { resume: 'deux', description: 'deux', duree: 5 },
  ] }, 10);
  const reservations = ['r1', 'r2'].map((reservationId) => ({ reservationId, credits: 1, etat: 'reservee' as const }));
  await expect(tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations }, null)).rejects.toThrow('moteur indisponible');
  expect(JSON.parse(memoire.lignes.get(101).settings).nexoraCredits.reservationId).toBe('r1');
  expect(JSON.parse(memoire.lignes.get(202).settings).nexoraCredits.reservationId).toBe('r2');
  const plans = JSON.parse(memoire.lignes.get(1).settings).storyboard.plans;
  expect(plans[0].take).toBe(101);
  expect(plans[1].take).toBe(202);
});

it('route film/tourner : ne libère que les réservations sans prise et rend les identifiants partiels', async () => {
  const texte = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  const source = ts.createSourceFile('index.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  let route: ts.ArrowFunction | undefined;
  function cherche(n: ts.Node) {
    if (ts.isCallExpression(n) && n.arguments.length >= 2 && ts.isStringLiteral(n.arguments[0])
        && n.arguments[0].text === '/api/nexora/film/tourner' && ts.isArrowFunction(n.arguments[1])) route = n.arguments[1];
    ts.forEachChild(n, cherche);
  }
  cherche(source);
  if (!route) throw new Error('route film/tourner introuvable');
  const js = ts.transpileModule(`const handler = ${route.getText(source)};`, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  const liberees: string[] = [];
  let no = 0;
  const fac = { reserver: async () => ({ ok: true, reservationId: `r${++no}`, credits: 1 }), liberer: async (id: string) => { liberees.push(id); } };
  const erreur = Object.assign(new Error('moteur indisponible'), { takeIds: [202] });
  const queueTakes = vi.fn()
    .mockImplementationOnce(async (corps, _n, credits) => { memoire.lignes.set(101, { id: 101, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) }); return [101]; })
    .mockImplementationOnce(async (corps, _n, credits) => { memoire.lignes.set(202, { id: 202, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0], nexoraSoumission: 'indeterminee' }) }); throw erreur; });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const deps: Record<string, unknown> = {
    lireStoryboard, lireDemandeCreer: () => ({ format: '16:9', son: false, qualite: 'rapide' }), moteurDuCompte: () => 'h3-fast',
    erreurAncrageMaxFilm: () => null, blockingReasonFor: async () => null, eng: { isLocal: () => false, recetteSurPrincipal: () => false },
    bundlesFor: () => [], lireCartons: () => [], facturationCourante: () => fac, corpsRendu: () => ({}),
    randomUUID: () => 'test', devisCredits: () => 1, tarifDepuisEnv: () => ({}), tournerFilm, llmRedaction: () => null, resultatEchecTournage, marquerReservationFilmLiberee,
  };
  const handler = new Function(...Object.keys(deps), `${js}; return handler;`)(...Object.values(deps));
  const reply = { code: vi.fn().mockReturnThis(), send: vi.fn((v) => v) };
  const resultat = await handler({ body: { storyboard: { langue: 'en', titre: 'test', plans: [
    { resume: 'un', description: 'un', replique: 'Hello!' }, { resume: 'deux', description: 'deux' }, { resume: 'trois', description: 'trois' },
  ] } } }, reply);
  expect(resultat.error).toBe('moteur indisponible');
  expect(memoire.reecritures[0].dialogues).toEqual([{ texte: 'Hello!', langue: 'English' }]);
  expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.langue).toBe('en');
  expect(liberees).toEqual(['r3']);
  expect(resultat.filmId).toBe(1);
  expect(resultat.prises).toEqual(expect.arrayContaining([expect.objectContaining({ plan: 0, takeId: 101 }), expect.objectContaining({ plan: 1, takeId: 202 })]));
});

it('une file à deux candidats ne conserve que la réservation de la prise partielle unique', async () => {
  const reservation = (reservationId: string) => ({ reservationId, credits: 1, etat: 'reservee' as const });
  const queueTakes = vi.fn(async (corps, _n, credits) => {
    memoire.lignes.set(202, { id: 202, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) });
    throw Object.assign(new Error('second candidat refusé'), { takeIds: [202, 202, -1, 999] });
  });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'Film test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  const r1 = reservation('r1'), r2 = reservation('r2');
  let erreur: unknown;
  try { await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations: [r1], reservationsCandidats: [r2], candidats: 2 }, null); }
  catch (e) { erreur = e; }
  expect(erreur).toBeInstanceOf(EchecTournage);
  const liberees: string[] = [];
  const resultat = await resultatEchecTournage(erreur, [r1, r2, r2], { liberer: async (id) => { liberees.push(id); } });
  expect(resultat.error).toBe('second candidat refusé');
  expect(resultat.prises).toEqual([{ plan: 0, takeId: 202 }]);
  expect(liberees).toEqual(['r2']);
  expect(JSON.parse(memoire.lignes.get(202).settings).nexoraCredits.reservationId).toBe('r1');
});

it('sans prise lancée libère tout une seule fois et conserve l’erreur primaire si libération échoue', async () => {
  const r1 = { reservationId: 'r1', credits: 1, etat: 'reservee' as const };
  const r2 = { ...r1, reservationId: 'r2' };
  const appels: string[] = [];
  const resultat = await resultatEchecTournage(new Error('erreur initiale'), [r1, r1, r2], {
    liberer: async (id) => { appels.push(id); if (id === 'r1') throw new Error('site indisponible'); },
  });
  expect(appels).toEqual(['r1', 'r2']);
  expect(resultat).toEqual({ error: 'erreur initiale', reservationsEnAttente: ['r1'] });
});

it('sans aucune prise créée, le tournage libère toutes ses réservations', async () => {
  const queueTakes = vi.fn(async () => { throw Object.assign(new Error('validation avant soumission'), { takeIds: [] }); });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }, { resume: 'deux', description: 'deux' }] }, 10);
  const reservations = ['r1', 'r2'].map((reservationId) => ({ reservationId, credits: 1, etat: 'reservee' as const }));
  let erreur: unknown;
  try { await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations }, null); } catch (e) { erreur = e; }
  const liberees: string[] = [];
  const resultat = await resultatEchecTournage(erreur, reservations, { liberer: async (id) => { liberees.push(id); } });
  expect(resultat.error).toBe('validation avant soumission');
  expect(resultat.prises).toEqual([]);
  expect(liberees).toEqual(['r1', 'r2']);
});

it('protège les deux prises dont les crédits étaient enregistrés avant une panne', async () => {
  const r1 = { reservationId: 'r1', credits: 1, etat: 'reservee' as const };
  const r2 = { ...r1, reservationId: 'r2' };
  const queueTakes = vi.fn(async (corps, _n, credits) => {
    for (const [i, id] of [101, 102].entries()) memoire.lignes.set(id, { id, settings: JSON.stringify({ ...corps, nexoraCredits: credits[i] }) });
    throw Object.assign(new Error('erreur moteur initiale'), { takeIds: [101, 102] });
  });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  let erreur: unknown;
  try { await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations: [r1], reservationsCandidats: [r2], candidats: 2 }, null); } catch (e) { erreur = e; }
  const liberer = vi.fn(async () => {});
  const resultat = await resultatEchecTournage(erreur, [r1, r2], { liberer });
  expect(resultat.error).toBe('erreur moteur initiale');
  expect(resultat.prises).toEqual([{ plan: 0, takeId: 101 }, { plan: 0, takeId: 102 }]);
  expect(resultat.attachementsEnAttente).toBeUndefined();
  expect(liberer).not.toHaveBeenCalled();
  expect(JSON.parse(memoire.lignes.get(102).settings).nexoraCredits.reservationId).toBe('r2');
  expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.plans[0].candidats).toEqual([101, 102]);
});

it('enregistre la libération d’une suite non lancée dans le storyboard du film échoué', async () => {
  const reservation = { reservationId: 'suite', credits: 1, etat: 'reservee' as const };
  memoire.lignes.set(1, { id: 1, settings: JSON.stringify({ storyboard: { plans: [{}, { suite: true, reservation }] } }) });
  const erreur = new EchecTournage(new Error('panne'), 1, [], [], []);
  await resultatEchecTournage(erreur, [reservation], { liberer: async () => {} }, marquerReservationFilmLiberee);
  expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.plans[1].reservation.etat).toBe('liberee');
});

it('une file qui retourne moins de prises que prévu échoue et protège les prises existantes', async () => {
  const queueTakes = vi.fn(async (corps, _n, credits) => { memoire.lignes.set(101, { id: 101, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) }); return [101]; });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  const r1 = { reservationId: 'r1', credits: 1, etat: 'reservee' as const };
  const r2 = { ...r1, reservationId: 'r2' };
  let erreur: unknown;
  try { await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations: [r1], reservationsCandidats: [r2], candidats: 2 }, null); } catch (e) { erreur = e; }
  const liberees: string[] = [];
  const resultat = await resultatEchecTournage(erreur, [r1, r2], { liberer: async (id) => { liberees.push(id); } });
  expect(resultat.error).toBe('Prises ou réservations de tournage non confirmées');
  expect(resultat.prises).toEqual([{ plan: 0, takeId: 101 }]);
  expect(liberees).toEqual(['r2']);
});

it('un film avec suite libère et marque la suite si un plan ultérieur ne démarre pas', async () => {
  const queueTakes = vi.fn()
    .mockImplementationOnce(async (corps, _n, credits) => { memoire.lignes.set(101, { id: 101, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) }); return [101]; })
    .mockRejectedValueOnce(Object.assign(new Error('panne après suite'), { takeIds: [] }));
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }, { resume: 'suite', description: 'suite', suite: true }, { resume: 'trois', description: 'trois' }] }, 15);
  const reservations = ['r1', 'r2', 'r3'].map((reservationId) => ({ reservationId, credits: 1, etat: 'reservee' as const }));
  let erreur: unknown;
  try { await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations }, null); } catch (e) { erreur = e; }
  const liberees: string[] = [];
  const resultat = await resultatEchecTournage(erreur, reservations, { liberer: async (id) => { liberees.push(id); } }, marquerReservationFilmLiberee);
  expect(resultat.error).toBe('panne après suite');
  expect(liberees).toEqual(['r2', 'r3']);
  expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.plans[1].reservation.etat).toBe('liberee');
});

it('ne relance pas automatiquement une prise en échec dont la soumission est indéterminée', async () => {
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  sb.plans[0].take = 101;
  memoire.lignes.set(1, { id: 1, status: 'queued', settings: JSON.stringify({ storyboard: sb }) });
  memoire.lignes.set(101, { id: 101, status: 'failed', settings: JSON.stringify({ nexoraSoumission: 'indeterminee', nexoraCredits: { reservationId: 'r1', credits: 1, etat: 'reservee' } }) });
  const queueTakes = vi.fn();
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  await avancerFilm(1);
  expect(queueTakes).not.toHaveBeenCalled();
  expect(JSON.parse(memoire.lignes.get(101).settings).nexoraCredits.etat).toBe('reservee');
});

it('une relance ambiguë conserve le crédit sur la nouvelle prise sans nouveau retry automatique', async () => {
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  sb.plans[0].take = 101;
  Object.assign(sb.plans[0], { corps: { nexoraFilm: 1, nexoraPlan: 0 }, clePlan: 'cle' });
  memoire.lignes.set(1, { id: 1, status: 'queued', project_id: null, settings: JSON.stringify({ storyboard: sb, format: '16:9', son: false, moteur: 'h3-fast', prompt: 'test' }) });
  const credit = { reservationId: 'r1', credits: 1, etat: 'reservee' };
  memoire.lignes.set(101, { id: 101, status: 'failed', error: 'panne', settings: JSON.stringify({ nexoraFilm: 1, nexoraPlan: 0, nexoraCredits: credit }) });
  const queueTakes = vi.fn(async (corps, _n, credits, _cle, ancien) => {
    expect(ancien).toBe(101);
    expect(JSON.parse(memoire.lignes.get(101).settings).nexoraCredits.etat).toBe('reservee');
    memoire.lignes.get(101).settings = JSON.stringify({ ...JSON.parse(memoire.lignes.get(101).settings), nexoraCredits: { ...credit, etat: 'transferee' } });
    memoire.lignes.set(102, { id: 102, status: 'queued', settings: JSON.stringify({ ...corps, nexoraCredits: credits[0], nexoraSoumission: 'indeterminee' }) });
    throw Object.assign(new Error('réponse moteur perdue'), { takeIds: [102] });
  });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  await avancerFilm(1);
  expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.plans[0].take).toBe(102);
  expect(JSON.parse(memoire.lignes.get(102).settings).nexoraCredits).toEqual(credit);
  await avancerFilm(1);
  expect(queueTakes).toHaveBeenCalledOnce();
});

it('une suite ambiguë conserve sa réservation sur la prise créée avant soumission', async () => {
  memoire.outputDir = mkdtempSync(join(tmpdir(), 'director-suite-'));
  const dossier = join(memoire.outputDir, 'films', 'images');
  mkdirSync(dossier, { recursive: true });
  writeFileSync(join(dossier, 'film_1_plan1_depart.png'), 'image synthétique');
  const precedent = join(memoire.outputDir, 'source-factice');
  writeFileSync(precedent, 'source synthétique');
  const sb = lireStoryboard({ langue: 'en', titre: 'test', plans: [{ resume: 'un', description: 'un' }, { resume: 'suite', description: 'suite', replique: 'Hello!', suite: true }] }, 10);
  sb.plans[0].take = 101;
  Object.assign(sb.plans[0], { controle: { ok: true, defauts: [] } });
  const reservation = { reservationId: 'suite', credits: 1, etat: 'reservee' };
  Object.assign(sb.plans[1], { reservation });
  memoire.lignes.set(1, { id: 1, status: 'queued', project_id: null, settings: JSON.stringify({ storyboard: sb, format: '16:9', son: false, moteur: 'h3-fast', prompt: 'test' }) });
  memoire.lignes.set(101, { id: 101, status: 'done', output_path: precedent, settings: '{}' });
  const queueTakes = vi.fn(async (corps, _n, credits, cle) => {
    expect(credits[0]).toEqual(reservation);
    expect(cle).toMatch(/^[0-9a-f]{64}$/);
    memoire.lignes.set(102, { id: 102, status: 'queued', settings: JSON.stringify({ ...corps, nexoraCredits: credits[0], nexoraSoumission: 'indeterminee' }) });
    throw Object.assign(new Error('réponse moteur perdue'), { takeIds: [102] });
  });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => 'image', llmPour: () => null });
  await avancerFilm(1);
  expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.plans[1].take).toBe(102);
  expect(JSON.parse(memoire.lignes.get(102).settings).nexoraCredits).toEqual(reservation);
  await avancerFilm(1);
  expect(queueTakes).toHaveBeenCalledOnce();
  expect(memoire.reecritures.at(-1).dialogues).toEqual([{ texte: 'Hello!', langue: 'English' }]);
});

it('une prise existante garde ses crédits ; le nouveau plan reçoit seulement sa nouvelle réservation', async () => {
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'ancien', description: 'ancien' }, { resume: 'nouveau', description: 'nouveau' }] }, 10);
  sb.plans[0].take = 88;
  memoire.lignes.set(88, { id: 88, settings: JSON.stringify({ nexoraCredits: { reservationId: 'ancienne', etat: 'validee' } }) });
  const nouvelle = { reservationId: 'nouvelle', credits: 1, etat: 'reservee' as const };
  const queueTakes = vi.fn(async (corps, _n, credits) => { memoire.lignes.set(101, { id: 101, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) }); return [101]; });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations: [undefined, nouvelle] }, null);
  expect(JSON.parse(memoire.lignes.get(88).settings).nexoraCredits.reservationId).toBe('ancienne');
  expect(JSON.parse(memoire.lignes.get(101).settings).nexoraCredits.reservationId).toBe('nouvelle');
});

it('ignore les identifiants de prise qui appartiennent à un autre film ou qui n’existent pas', async () => {
  const queueTakes = vi.fn(async () => {
    memoire.lignes.set(202, { id: 202, settings: JSON.stringify({ nexoraFilm: 99, nexoraPlan: 0 }) });
    throw Object.assign(new Error('panne sans prise valide'), { takeIds: [202, 999] });
  });
  initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
  const sb = lireStoryboard({ titre: 'test', plans: [{ resume: 'un', description: 'un' }] }, 5);
  const r1 = { reservationId: 'r1', credits: 1, etat: 'reservee' as const };
  let erreur: unknown;
  try { await tournerFilm(sb, { format: '16:9', son: false, intention: 'test', moteur: 'h3-fast', reservations: [r1] }, null); } catch (e) { erreur = e; }
  const liberees: string[] = [];
  const resultat = await resultatEchecTournage(erreur, [r1], { liberer: async (id) => { liberees.push(id); } });
  expect(resultat.prises).toEqual([]);
  expect(liberees).toEqual(['r1']);
  expect(JSON.parse(memoire.lignes.get(202).settings)).not.toHaveProperty('nexoraCredits');
});

/** Exécute les fonctions de file réellement présentes dans index.ts, avec moteur et base simulés. */
function fileReelle(deps: Record<string, unknown>) {
  const prises = deps.takes as { create: (row: unknown) => number; createProtegee?: (row: unknown, cle: string) => number };
  prises.createProtegee ??= (row) => prises.create(row);
  const texte = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  const source = ts.createSourceFile('index.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const noms = new Set(['stripServerKeys', 'submitTake', 'queueTakes', 'queueAfter']);
  const morceaux: string[] = [];
  for (const n of source.statements) {
    if (ts.isFunctionDeclaration(n) && n.name && noms.has(n.name.text)) morceaux.push(n.getText(source));
    if (ts.isVariableStatement(n) && n.declarationList.declarations.some((d) => ts.isIdentifier(d.name) && d.name.text === 'SERVER_KEYS')) morceaux.push(n.getText(source));
  }
  if (morceaux.length !== 5) throw new Error('fonctions de file introuvables');
  const js = ts.transpileModule(morceaux.join('\n'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  return new Function(...Object.keys(deps), `${js}; return { queueTakes, queueAfter };`)(...Object.values(deps));
}

it('persiste les crédits et l’état indéterminé avant submit, même si setPrompt échoue après acceptation', async () => {
  let stocke: any;
  const fail = vi.fn();
  const submit = vi.fn(async () => {
    expect(stocke.settings.nexoraCredits.reservationId).toBe('r1');
    expect(stocke.settings.nexoraSoumission).toBe('indeterminee');
    return 'job-accepte';
  });
  const takes = {
    create: (row: any) => { stocke = { id: 101, ...row, settings: row.settings }; return 101; },
    get: () => ({ ...stocke, settings: JSON.stringify(stocke.settings) }),
    setPrompt: () => { throw new Error('écriture prompt impossible'); }, patchSettings: vi.fn(), fail,
  };
  const deps = { takes, resolveCast: async (body: unknown) => ({ body }), graphFor: async () => ({ graph: {}, settings: {}, kind: 'video' }),
    eng: { moteursPour: () => [], submit }, recetteDe: () => 'h3-fast', broadcast: () => {}, recordWorkflow: () => {} };
  const { queueTakes } = fileReelle(deps);
  const credit = { reservationId: 'r1', credits: 1, etat: 'reservee' };
  await expect(queueTakes({ nexoraFilm: 1, nexoraPlan: 0 }, 1, [credit], 'cle')).rejects.toMatchObject({ message: 'écriture prompt impossible', takeIds: [101] });
  expect(submit).toHaveBeenCalledOnce();
  expect(fail).not.toHaveBeenCalled();
  expect(stocke.settings).toMatchObject({ nexoraCredits: credit, nexoraSoumission: 'indeterminee' });
});

it('refuse tout crédit injecté par le corps externe et ne soumet rien si la création échoue', async () => {
  let settings: any;
  let refuserCreation = false;
  const submit = vi.fn(async () => 'job');
  const takes = {
    create: (row: any) => { if (refuserCreation) throw new Error('base indisponible'); settings = row.settings; return 101; },
    get: () => ({ settings: JSON.stringify(settings), status: 'queued' }), setPrompt: () => {}, patchSettings: () => {}, fail: () => {},
  };
  const deps = { takes, resolveCast: async (body: unknown) => ({ body }), graphFor: async () => ({ graph: {}, settings: {}, kind: 'video' }),
    eng: { moteursPour: () => [], submit }, recetteDe: () => 'h3-fast', broadcast: () => {}, recordWorkflow: async () => {} };
  const { queueTakes } = fileReelle(deps);
  await queueTakes({ nexoraCredits: { reservationId: 'injection' }, nexoraSoumission: 'indeterminee', nexoraClePlan: 'injection' }, 1);
  expect(settings).not.toHaveProperty('nexoraCredits');
  expect(settings).not.toHaveProperty('nexoraSoumission');
  expect(settings).not.toHaveProperty('nexoraClePlan');
  submit.mockClear(); refuserCreation = true;
  await expect(queueTakes({}, 1, [{ reservationId: 'r1', credits: 1, etat: 'reservee' }], 'cle')).rejects.toMatchObject({ message: 'base indisponible', takeIds: [] });
  expect(submit).not.toHaveBeenCalled();
});

it('queueAfter conserve les crédits à la création, à la construction tardive et à la soumission', async () => {
  let settings: any;
  const submit = vi.fn(async () => {
    expect(settings).toMatchObject({ nexoraCredits: { reservationId: 'r1' }, nexoraSoumission: 'indeterminee' });
    return 'job';
  });
  const takes = {
    create: (row: any) => { settings = row.settings; return 101; },
    get: () => ({ settings: JSON.stringify(settings), status: 'queued' }),
    setSettings: (_id: number, s: any) => { settings = s; }, setPrompt: () => { settings.nexoraSoumission = 'confirmee'; },
    patchSettings: (_id: number, patch: any) => { settings = { ...settings, ...patch }; }, fail: vi.fn(),
  };
  const deps = { takes, graphFor: async () => ({ graph: {}, settings: {}, kind: 'video' }),
    eng: { moteursPour: () => [], submit }, recetteDe: () => 'h3-fast', broadcast: () => {}, recordWorkflow: async () => {} };
  const { queueAfter } = fileReelle(deps);
  const credit = { reservationId: 'r1', credits: 1, etat: 'reservee' };
  const id = queueAfter({ nexoraFilm: 1, nexoraPlan: 0 }, 1, Promise.resolve({ takeId: 5, token: 'image' }), null,
    (body: any, still: any) => ({ ...body, startImage: still.token }), true, credit, 'cle');
  expect(id).toBe(101);
  expect(settings).toMatchObject({ nexoraCredits: credit, nexoraSoumission: 'attente' });
  await new Promise((resolve) => setImmediate(resolve));
  expect(submit).toHaveBeenCalledOnce();
  expect(settings).toMatchObject({ nexoraCredits: credit, nexoraSoumission: 'confirmee' });
});

it('une panne de création du second candidat conserve l’ID et le crédit du premier', async () => {
  const lignes = new Map<number, any>();
  let creations = 0;
  const submit = vi.fn(async () => 'job');
  const takes = {
    create: (row: any) => { if (++creations === 2) throw new Error('base indisponible'); lignes.set(101, row.settings); return 101; },
    get: (id: number) => ({ settings: JSON.stringify(lignes.get(id)), status: 'queued' }), setPrompt: (id: number) => { lignes.get(id).nexoraSoumission = 'confirmee'; },
    patchSettings: (id: number, patch: any) => { lignes.set(id, { ...lignes.get(id), ...patch }); }, fail: vi.fn(),
  };
  const deps = { takes, resolveCast: async (body: unknown) => ({ body }), graphFor: async () => ({ graph: {}, settings: {}, kind: 'video' }),
    eng: { moteursPour: () => [], submit }, recetteDe: () => 'h3-fast', broadcast: () => {}, recordWorkflow: async () => {} };
  const { queueTakes } = fileReelle(deps);
  const credit = { reservationId: 'r1', credits: 1, etat: 'reservee' };
  await expect(queueTakes({ nexoraFilm: 1, nexoraPlan: 0 }, 2, [credit, { ...credit, reservationId: 'r2' }], 'cle')).rejects.toMatchObject({ message: 'base indisponible', takeIds: [101] });
  expect(submit).toHaveBeenCalledOnce();
  expect(lignes.get(101)).toMatchObject({ nexoraCredits: credit, nexoraSoumission: 'confirmee' });
});

it('queueAfter garde la réservation si la soumission tardive devient indéterminée', async () => {
  let settings: any;
  const fail = vi.fn();
  const takes = {
    create: (row: any) => { settings = row.settings; return 101; },
    get: () => ({ settings: JSON.stringify(settings), status: 'queued' }),
    setSettings: (_id: number, s: any) => { settings = s; }, setPrompt: () => { throw new Error('base indisponible'); },
    patchSettings: (_id: number, patch: any) => { settings = { ...settings, ...patch }; }, fail,
  };
  const deps = { takes, graphFor: async () => ({ graph: {}, settings: {}, kind: 'video' }),
    eng: { moteursPour: () => [], submit: async () => 'job-accepte' }, recetteDe: () => 'h3-fast', broadcast: () => {}, recordWorkflow: async () => {} };
  const { queueAfter } = fileReelle(deps);
  const credit = { reservationId: 'r1', credits: 1, etat: 'reservee' };
  queueAfter({ nexoraFilm: 1, nexoraPlan: 0 }, 1, Promise.resolve({ takeId: 5, token: 'image' }), null,
    (body: any, still: any) => ({ ...body, startImage: still.token }), true, credit, 'cle');
  await new Promise((resolve) => setImmediate(resolve));
  expect(settings).toMatchObject({ nexoraCredits: credit, nexoraSoumission: 'indeterminee' });
  expect(fail).not.toHaveBeenCalled();
});

it('au redémarrage, ne classe pas comme orpheline une soumission indéterminée', () => {
  const texte = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  const source = ts.createSourceFile('index.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const boucle = source.statements.find((n) => ts.isForOfStatement(n) && n.expression.getText(source) === 'takes.orphans()');
  if (!boucle) throw new Error('boucle des orphelins introuvable');
  const js = ts.transpileModule(boucle.getText(source), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  const fail = vi.fn();
  const takes = { orphans: () => [
    { id: 101, settings: JSON.stringify({ nexoraSoumission: 'indeterminee' }) },
    { id: 102, settings: JSON.stringify({ nexoraSoumission: 'attente' }) },
  ], fail };
  new Function('takes', 'soumissionIndeterminee', js)(takes, soumissionIndeterminee);
  expect(fail).toHaveBeenCalledOnce();
  expect(fail).toHaveBeenCalledWith(102, expect.any(String), true);
});

it('la réconciliation ne libère pas les crédits d’une soumission indéterminée', async () => {
  const texte = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  const source = ts.createSourceFile('index.ts', texte, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const fn = source.statements.find((n) => ts.isFunctionDeclaration(n) && n.name?.text === 'solderCreditsInterne');
  if (!fn) throw new Error('réconciliation introuvable');
  const js = ts.transpileModule(fn.getText(source), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText;
  const liberer = vi.fn();
  const takes = { list: () => [{ id: 101, status: 'failed', settings: JSON.stringify({ nexoraSoumission: 'indeterminee', nexoraCredits: { reservationId: 'r1', credits: 1, etat: 'reservee' } }) }], reservationsFilmOrphelines: () => [] };
  const deps = { takes, soumissionIndeterminee, actionFacturation: () => 'liberer', facturationPour: () => ({ liberer }), accesOrganisation: () => ({}) };
  const executer = new Function(...Object.keys(deps), `${js}; return solderCreditsInterne;`)(...Object.values(deps));
  await executer();
  expect(liberer).not.toHaveBeenCalled();
});

it('refuse sur le serveur le rejeu du même plan déjà soumis', async () => {
  const lignes = new Map<number, any>();
  let prochain = 100;
  const enregistrer = (row: any) => { const id = ++prochain; lignes.set(id, { id, ...row, status: 'queued' }); return id; };
  const takes = {
    create: enregistrer,
    createProtegee: (row: any, cle: string) => {
      if ([...lignes.values()].some((t) => t.settings.nexoraClePlan === cle && t.settings.nexoraFilm !== row.settings.nexoraFilm)) throw new Error('plan déjà en cours ou indéterminé');
      return enregistrer(row);
    },
    get: (id: number) => ({ ...lignes.get(id), settings: JSON.stringify(lignes.get(id).settings) }),
    setPrompt: (id: number) => { lignes.get(id).status = 'rendering'; },
    patchSettings: (id: number, patch: any) => { Object.assign(lignes.get(id).settings, patch); }, fail: vi.fn(),
  };
  const submit = vi.fn(async () => 'job');
  const deps = { takes, resolveCast: async (body: unknown) => ({ body }), graphFor: async () => ({ graph: {}, settings: {}, kind: 'video' }),
    eng: { moteursPour: () => [], submit }, recetteDe: () => 'h3-fast', broadcast: () => {}, recordWorkflow: async () => {} };
  const { queueTakes } = fileReelle(deps);
  const credit = { reservationId: 'r1', credits: 1, etat: 'reservee' };
  await queueTakes({ nexoraFilm: 1, nexoraPlan: 0 }, 1, [credit], 'meme-plan');
  await expect(queueTakes({ nexoraFilm: 2, nexoraPlan: 0 }, 1, [credit], 'meme-plan')).rejects.toThrow('plan déjà en cours ou indéterminé');
  expect(submit).toHaveBeenCalledOnce();
});

it('ne lance pas l’image préalable si la création protégée du plan est refusée', () => {
  const premier = vi.fn(async () => ({ takeId: 3, token: 'image' }));
  const deps = { takes: { create: vi.fn(), createProtegee: () => { throw new Error('plan déjà en cours'); } } };
  const { queueAfter } = fileReelle(deps);
  expect(() => queueAfter({ nexoraFilm: 2, nexoraPlan: 0 }, 1, premier, null, (body: unknown) => body, true, undefined, 'cle')).toThrow('plan déjà en cours');
  expect(premier).not.toHaveBeenCalled();
});


it('transmet la langue du storyboard au réécrivain et conserve la réplique', async () => {
  for (const [langue, etiquette, texte] of [['fr', 'French', 'Bonjour !'], ['en', 'English', 'Hello!']] as const) {
    memoire.lignes.clear(); memoire.reecritures.length = 0;
    const queueTakes = vi.fn(async (corps, _n, credits) => {
      memoire.lignes.set(101, { id: 101, settings: JSON.stringify({ ...corps, nexoraCredits: credits[0] }) });
      return [101];
    });
    initFilms({ queueTakes, broadcast: () => {}, televerser: async () => '', llmPour: () => null });
    const sb = lireStoryboard({ langue, titre: 'Test', plans: [{ resume: 'one', description: 'A car moves', replique: texte }] }, 5);
    await tournerFilm(sb, { format: '16:9', son: true, intention: 'test', moteur: 'h3-fast' }, null);
    expect(memoire.reecritures[0].dialogues).toEqual([{ texte, langue: etiquette }]);
    expect(JSON.parse(memoire.lignes.get(1).settings).storyboard.langue).toBe(langue);
  }
});
