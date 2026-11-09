/**
 * Matte — registre corrompu : régression fail-closed (locale, sans réseau).
 *
 * Fichier indépendant de gestion.test.ts : cas synthétiques non secrets.
 * Exige, en mode indisponible : constructeur sans throw, lister/creer/possede
 * refusés en 503 avec un message générique (ni contenu du fichier ni chemin),
 * nettoyer résolu à [] sans rejet, octets source intacts après TOUTES les
 * opérations, et 0 appel moteur/client/facturation (aucune écriture avant garde).
 * Un registre absent (ENOENT) reste un nouveau registre valide.
 */
import { mkdtempSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { Detourage, ErreurDetourage, type OptionsDetourage } from './gestion.js';

type Compteurs = { moteur: number; clientDe: number; client: number; facturation: number };

/** Dossiers temporaires dans TMPDIR, conservés tels quels (pas de suppression). */
function dossier(): string {
  return mkdtempSync(join(tmpdir(), 'matte-registre-'));
}

function compteurs(): Compteurs {
  return { moteur: 0, clientDe: 0, client: 0, facturation: 0 };
}

function optionsPour(registre: string, c: Compteurs): OptionsDetourage {
  const touche = () => { c.client++; };
  const client = {
    async sante() { touche(); return { ok: true }; },
    async segmenter() { touche(); throw new Error('non utilisé'); },
    async texte() { touche(); throw new Error('non utilisé'); },
    async deposer() { touche(); throw new Error('non utilisé'); },
    async lancer() { touche(); },
    async etat() { touche(); return null; },
    async annuler() { touche(); },
    async supprimer() { touche(); },
    async sortie() { touche(); throw new Error('non utilisé'); },
  };
  return {
    registre,
    moteur: () => { c.moteur++; return { id: 'm1', client }; },
    clientDe: (id: string) => { c.clientDe++; return id === 'm1' ? client : null; },
    facturation: () => { c.facturation++; return null; },
    maintenant: () => 1_000_000,
    ttl: { termineMs: 1000, deposeMs: 5000 },
  };
}

function entree(id: string, org = 'org-a'): Record<string, unknown> {
  return {
    id, organisation: org, utilisateur: 'u', nom: 'travail', moteurId: 'm1',
    creeLe: 1, majLe: 2, etat: 'termine', etape: 'fin', progression: 1,
    message: 'ok', fichiers: {},
  };
}

function construit(registre: string, c: Compteurs): Detourage {
  let d!: Detourage;
  expect(() => { d = new Detourage(optionsPour(registre, c)); }).not.toThrow();
  return d;
}

function attrape(fn: () => unknown): unknown {
  try { fn(); } catch (e) { return e; }
  throw new Error('aurait dû refuser en 503');
}

function attendRefusGenerique(e: unknown, registre: string, marqueur: string): void {
  expect(e).toBeInstanceOf(ErreurDetourage);
  expect((e as ErreurDetourage).code).toBe(503);
  const message = (e as ErreurDetourage).message;
  expect(typeof message).toBe('string');
  expect(message.length).toBeGreaterThan(0);
  expect(message).not.toContain(registre);
  expect(message).not.toContain(marqueur);
}

/** Toutes les opérations refusées ou neutres, octets intacts, 0 appel externe. */
async function refuseTout(registre: string, d: Detourage, c: Compteurs, avantHex: string, marqueur: string): Promise<void> {
  attendRefusGenerique(attrape(() => d.lister('org-a')), registre, marqueur);
  attendRefusGenerique(attrape(() => d.creer('org-a', 'u', 'nouveau')), registre, marqueur);
  attendRefusGenerique(attrape(() => d.obtenir('org-a', 'a'.repeat(24))), registre, marqueur);
  for (const operation of [
    () => d.deposer('org-a', 'a1', 'source.mp4', Buffer.from('x'), 1),
    () => d.lancer('org-a', 'a1', {}, { secondes: 1, credits: 1 }),
    () => d.actualiser('org-a', 'a1'), () => d.annuler('org-a', 'a1'),
    () => d.reprendre('org-a', 'a1'), () => d.supprimer('org-a', 'a1'),
  ]) {
    const erreur = await operation().then(() => { throw new Error('aurait dû refuser'); }, (e: unknown) => e);
    attendRefusGenerique(erreur, registre, marqueur);
  }
  await expect(d.nettoyer()).resolves.toEqual([]);
  expect(c).toEqual({ moteur: 0, clientDe: 0, client: 0, facturation: 0 });
  expect(readFileSync(registre).toString('hex')).toBe(avantHex);
}

describe('registre Matte fail-closed', () => {
  it('absent (ENOENT) : nouveau registre valide', () => {
    const registre = join(dossier(), 'registre.json');
    const d = construit(registre, compteurs());
    expect(d.lister('org-a')).toEqual([]);
    const t = d.creer('org-a', 'u', 'premier');
    expect(t.organisation).toBe('org-a');
    const relu = JSON.parse(readFileSync(registre, 'utf8')) as unknown[];
    expect(Array.isArray(relu)).toBe(true);
    expect(relu).toHaveLength(1);
    expect(construit(registre, compteurs()).obtenir('org-a', t.id).nom).toBe('premier');
  });

  it('une création sur JSON tronqué conserve les octets au lieu de remplacer le registre', () => {
    const registre = join(dossier(), 'registre.json');
    const original = '[{"id":"travail-ancien-incomplet"';
    writeFileSync(registre, original);
    const c = compteurs();
    const d = construit(registre, c);
    let erreur: unknown;
    try { d.creer('org-a', 'u', 'nouveau'); } catch (e) { erreur = e; }
    expect(readFileSync(registre, 'utf8')).toBe(original);
    attendRefusGenerique(erreur, registre, 'travail-ancien-incomplet');
    expect(c).toEqual({ moteur: 0, clientDe: 0, client: 0, facturation: 0 });
  });

  it('un tableau vide reste un registre valide', () => {
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, '[]');
    const d = construit(registre, compteurs());
    expect(d.lister('org-a')).toEqual([]);
    expect(d.creer('org-a', 'u', 'premier').etat).toBe('depose');
  });

  it('vide : bloqué, octets intacts', async () => {
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, '');
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    await refuseTout(registre, construit(registre, c), c, avant, 'vide-marqueur-ne-doit-pas-fuir');
  });

  it('tronqué : bloqué, octets intacts', async () => {
    const marqueur = 'tronque-marqueur-9f3k';
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, `[{"id": "a1", "organisation": "org-a", "${marqueur}": true`);
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    await refuseTout(registre, construit(registre, c), c, avant, marqueur);
  });

  it('objet JSON (non-tableau) : bloqué, octets intacts', async () => {
    const marqueur = 'objet-marqueur-7q2x';
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, JSON.stringify({ id: 'a1', organisation: 'org-a', [marqueur]: 'contenu-fichier' }));
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    await refuseTout(registre, construit(registre, c), c, avant, marqueur);
  });

  it('tableau partiellement invalide : aucun chargement partiel', async () => {
    const marqueur = 'partiel-marqueur-4m8p';
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, JSON.stringify([{ ...entree('a1'), [marqueur]: 'contenu-fichier' }, 42]));
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    const d = construit(registre, c);
    await refuseTout(registre, d, c, avant, marqueur);
    attendRefusGenerique(attrape(() => d.obtenir('org-a', 'a1')), registre, marqueur);
  });

  it('doublons d’ID : bloqué, octets intacts', async () => {
    const marqueur = 'doublon-marqueur-2h6n';
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, JSON.stringify([{ ...entree('a1'), [marqueur]: 1 }, entree('a1', 'org-b')]));
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    await refuseTout(registre, construit(registre, c), c, avant, marqueur);
  });

  it('erreur lecture (EISDIR) : bloqué, dossier intact', async () => {
    const registre = dossier(); // un dossier, pas un fichier : readFileSync lève EISDIR
    const marqueur = 'eisdir-marqueur-5t1v';
    writeFileSync(join(registre, `sentinelle-${marqueur}.txt`), 'sentinelle');
    const avant = readdirSync(registre).sort();
    const c = compteurs();
    const d = construit(registre, c);
    attendRefusGenerique(attrape(() => d.lister('org-a')), registre, marqueur);
    attendRefusGenerique(attrape(() => d.creer('org-a', 'u', 'nouveau')), registre, marqueur);
    attendRefusGenerique(attrape(() => d.obtenir('org-a', 'a1')), registre, marqueur);
    await expect(d.nettoyer()).resolves.toEqual([]);
    expect(c).toEqual({ moteur: 0, clientDe: 0, client: 0, facturation: 0 });
    expect(readdirSync(registre).sort()).toEqual(avant);
  });

  it('valide ancien : entrées historiques compatibles', () => {
    const registre = join(dossier(), 'registre.json');
    const ancien = { ...entree('a1'), reliquat1970: { champ: 'historique-conservé' } };
    writeFileSync(registre, JSON.stringify([ancien, entree('b2')]));
    const d = construit(registre, compteurs());
    expect(d.lister('org-a').map((t) => t.id).sort()).toEqual(['a1', 'b2']);
    expect(d.obtenir('org-a', 'a1').nom).toBe('travail');
  });

  it.each([
    null, [], 42, { ...entree('a1'), id: '' }, { ...entree('a1'), organisation: '' },
    { ...entree('a1'), moteurId: '' }, { ...entree('a1'), nom: null },
    { ...entree('a1'), creeLe: null }, { ...entree('a1'), majLe: '2' },
    { ...entree('a1'), progression: null }, { ...entree('a1'), etat: 'inconnu' },
    { ...entree('a1'), fichiers: null }, { ...entree('a1'), fichiers: { 'source.mp4': '1' } },
    { ...entree('a1'), credits: null }, { ...entree('a1'), credits: { reservationId: '', credits: 1, etat: 'reservee' } },
    { ...entree('a1'), credits: { reservationId: 'r1', credits: '1', etat: 'reservee' } },
    { ...entree('a1'), credits: { reservationId: 'r1', credits: 1, etat: 'inconnu' } },
    { ...entree('a1'), credits: { reservationId: 'r1', credits: 1, etat: 'reservee', reglement: 'inconnu' } },
  ])('refuse une entrée mal typée sans perdre la précédente : %j', async (invalide) => {
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, JSON.stringify([entree('valide'), invalide]));
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    await refuseTout(registre, construit(registre, c), c, avant, 'marqueur-absent');
  });

  it.each(['reservee', 'validee', 'liberee'] as const)('conserve les crédits %s et les champs historiques inconnus', (etat) => {
    const registre = join(dossier(), 'registre.json');
    const ancien = { ...entree('a1'), extensionFuture: { x: true }, params: { ancienneOption: 'oui' },
      credits: { reservationId: 'r1', credits: 1, etat, reglement: 'valider' } };
    writeFileSync(registre, JSON.stringify([ancien]));
    const d = construit(registre, compteurs());
    d.creer('org-a', 'u', 'second');
    expect((JSON.parse(readFileSync(registre, 'utf8')) as unknown[])).toContainEqual(ancien);
  });

  it('réparation humaine : reste bloqué jusqu’à une nouvelle instance', async () => {
    const marqueur = 'reparation-marqueur-8w3z';
    const registre = join(dossier(), 'registre.json');
    writeFileSync(registre, `[{"id": "${marqueur}"`);
    const avant = readFileSync(registre).toString('hex');
    const c = compteurs();
    const d = construit(registre, c);
    await refuseTout(registre, d, c, avant, marqueur);
    writeFileSync(registre, JSON.stringify([entree('a1')])); // réparation humaine externe
    await refuseTout(registre, d, c, readFileSync(registre).toString('hex'), marqueur);
    expect(construit(registre, compteurs()).lister('org-a').map((t) => t.id)).toEqual(['a1']);
  });
});
