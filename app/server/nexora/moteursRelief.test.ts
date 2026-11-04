import { afterEach, describe, expect, it } from 'vitest';
import { appliquerMoteurs, lireSecondes, moteurs, moteursPour, retablirMoteursEnv } from '../engine.js';

const GB10_SECONDES = { 'objet-apercu': 38, 'objet-qualite': 162 };
function parc() {
  moteurs[0].recettes = ['qwen21', 'objet-apercu', 'objet-qualite'];
  moteurs[0].secondes = GB10_SECONDES;
  appliquerMoteurs([
    { id: 'turing-2080s', nom: '2080S', comfyUrl: 'http://x:8188', baseUrl: 'http://127.0.0.1:37388', recettes: ['objet-apercu'], secondes: { 'objet-apercu': 126 } },
    { id: 'turing-2070s', nom: '2070S', comfyUrl: 'http://x:8189', baseUrl: 'http://127.0.0.1:37389', recettes: ['objet-apercu'], secondes: { 'objet-apercu': 150 } },
  ]);
}
afterEach(() => retablirMoteursEnv());

describe('Relief : routage des brouillons 3D', () => {
  it('lireSecondes ignore le bruit', () => {
    expect(lireSecondes('{"a":38,"b":"x","c":-1}')).toEqual({ a: 38 });
    expect(lireSecondes('pas du json')).toBeUndefined();
    expect(lireSecondes('')).toBeUndefined();
  });
  it('file vide : le brouillon reste sur la GB10', () => {
    parc();
    expect(moteursPour('objet-apercu', () => 0)[0].id).toBe('principal');
  });
  it('file chargée (3 tâches sur la GB10) : le brouillon déborde sur la 2080 SUPER, puis la 2070 SUPER', () => {
    parc();
    const charge = (n: Record<string, number>) => (id: string) => n[id] ?? 0;
    expect(moteursPour('objet-apercu', charge({ principal: 2 }))[0].id).toBe('principal'); // 3 × 38 = 114 < 126
    expect(moteursPour('objet-apercu', charge({ principal: 3 }))[0].id).toBe('turing-2080s'); // 4 × 38 = 152 > 126
    expect(moteursPour('objet-apercu', charge({ principal: 3, 'turing-2080s': 1 }))[0].id).toBe('turing-2070s'); // 252 > 150
  });
  it('la qualité ne part jamais sur les Turing', () => {
    parc();
    expect(moteursPour('objet-qualite', () => 9).map((m) => m.id)).toEqual(['principal']);
  });
  it('un moteur hors ligne est écarté tant qu’un autre capable répond', () => {
    parc();
    const hors = new Set(['principal', 'turing-2080s']);
    expect(moteursPour('objet-apercu', () => 0, (id) => !hors.has(id)).map((m) => m.id)).toEqual(['turing-2070s']);
    // tout hors ligne : on garde la liste (le travail attendra le retour d'un moteur plutôt que de ne rien faire)
    expect(moteursPour('objet-apercu', () => 0, () => false)).toHaveLength(3);
  });
  it('sans secondes déclarées, l’ancien comportement : le moins chargé', () => {
    appliquerMoteurs([{ id: 'b', nom: 'b', comfyUrl: 'http://x:1', baseUrl: 'http://127.0.0.1:1', recettes: ['*'] }]);
    expect(moteursPour('h3-fast', (id) => (id === 'principal' ? 1 : 0))[0].id).toBe('b');
  });
});
