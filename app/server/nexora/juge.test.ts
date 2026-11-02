import { describe, expect, it } from 'vitest';
import { argsPlanche, choisirCandidat, jugeDisponible, jugerCandidats, lireVerdict } from './juge.js';
import type { ClientLlm } from './llm.js';

describe('juge visuel : lecture de la réponse', () => {
  it('lit le gagnant, la raison et les notes', () => {
    expect(lireVerdict('```json\n{"gagnant":"b","raison":"Mains intactes, mouvement fluide.","notes":{"A":4,"B":8}}\n```')).toEqual({ gagnant: 'B', raison: 'Mains intactes, mouvement fluide.', notes: { A: 4, B: 8 } });
  });
  it('refuse une réponse sans gagnant valable', () => {
    expect(lireVerdict('{"gagnant":"C","raison":"x"}')).toBeNull();
    expect(lireVerdict('je préfère le premier')).toBeNull();
  });
  it('coupe une raison trop longue et borne les notes', () => {
    const v = lireVerdict(JSON.stringify({ gagnant: 'A', raison: 'x'.repeat(400), notes: { A: 42, B: -3 } }))!;
    expect(v.raison.length).toBeLessThanOrEqual(200);
    expect(v.notes).toEqual({ A: 10, B: 0 });
  });
});

describe('juge visuel : choix', () => {
  it('le contrôle qualité passe avant le juge', () => {
    expect(choisirCandidat([{ take: 1, controleOk: false }, { take: 2, controleOk: true }], { gagnant: 'A', raison: 'r', notes: { A: 9, B: 1 } })).toEqual({ take: 2, source: 'controle', raison: 'Seule la prise 2 passe le contrôle qualité.' });
  });
  it('deux prises valides : le verdict du juge', () => {
    expect(choisirCandidat([{ take: 1, controleOk: true }, { take: 2, controleOk: true }], { gagnant: 'B', raison: 'Plus fidèle.', notes: { A: 5, B: 8 } })).toEqual({ take: 2, source: 'juge', raison: 'Plus fidèle.' });
  });
  it('sans verdict : la première prise valide', () => {
    expect(choisirCandidat([{ take: 1, controleOk: true }, { take: 2, controleOk: true }], null)).toMatchObject({ take: 1, source: 'repli' });
    expect(choisirCandidat([{ take: 1, controleOk: false }, { take: 2, controleOk: false }], null)).toMatchObject({ take: 1, source: 'repli' });
  });
});

describe('juge visuel : appel au modèle', () => {
  it('envoie les deux planches en images et la grille versionnée', async () => {
    let vus: any[] = [];
    const llm: ClientLlm = { completer: async (_r, m) => { vus = m; return '{"gagnant":"A","raison":"Visage net.","notes":{"A":8,"B":6}}'; } };
    const v = await jugerCandidats(llm, 'A baker smiles', ['data:image/jpeg;base64,AAA', 'data:image/jpeg;base64,BBB']);
    expect(v?.gagnant).toBe('A');
    expect(String(vus[0].content)).toContain('[compétence juge v1]');
    const parts = vus[1].content as any[];
    expect(parts.filter((p) => p.type === 'image_url').map((p) => p.image_url.url)).toEqual(['data:image/jpeg;base64,AAA', 'data:image/jpeg;base64,BBB']);
  });
  it('une panne du modèle donne null (le code choisit alors seul)', async () => {
    const llm: ClientLlm = { completer: async () => { throw new Error('HTTP 500'); } };
    expect(await jugerCandidats(llm, 'x', ['a', 'b'])).toBeNull();
    expect(await jugerCandidats(null, 'x', ['a', 'b'])).toBeNull();
  });
  it('n’est disponible que si un modèle vision est réglé pour le rôle « juge »', () => {
    expect(jugeDisponible({} as NodeJS.ProcessEnv)).toBe(false);
    expect(jugeDisponible({ NEXORA_LLM_MODELE_JUGE: 'qwen/qwen3.8-27b' } as NodeJS.ProcessEnv)).toBe(true);
  });
  it('la planche prend trois images réparties sur la durée', () => {
    const a = argsPlanche('/r/a.mp4', '/r/a.jpg', 5.17).join(' ');
    expect(a).toContain('tile=3x1');
    expect(a).toContain('fps=3/5.17');
  });
});
