import { describe, expect, it } from 'vitest';
import { demanderEffet, lireDemandeEffet, lireRecetteBrute, SYSTEME_EFFETS } from './effets.js';
import type { ClientLlm } from './llm.js';

const demande = { phrase: 'ajoute un halo bleu', catalogue: 'gpu-glow (stylize) : amount 0..5=1', contexte: { tS: 202, fps: 30, element: { type: 'video', dureeS: 10 } } };

describe('bulle d’effet : route serveur', () => {
  it('lit la demande et refuse une phrase vide, trop longue ou sans catalogue', () => {
    expect(lireDemandeEffet(demande).contexte.element?.type).toBe('video');
    expect(() => lireDemandeEffet({ ...demande, phrase: ' ' })).toThrow();
    expect(() => lireDemandeEffet({ ...demande, phrase: 'x'.repeat(301) })).toThrow();
    expect(() => lireDemandeEffet({ ...demande, catalogue: '' })).toThrow();
  });

  it('ne garde que les étapes connues (pas de shader ni de code)', () => {
    const r = lireRecetteBrute({ resume: 'Halo', etapes: [{ kind: 'gpu_stack', effets: [] }, { kind: 'shader', code: 'x' }, null] });
    expect(r.etapes.map((e) => e.kind)).toEqual(['gpu_stack']);
  });

  it('appelle le rôle « effets » en JSON avec le catalogue et le contexte marqué comme donnée', async () => {
    const vus: { role: string; contenu: string }[] = [];
    const llm: ClientLlm = {
      async completer(role, messages) {
        vus.push({ role, contenu: messages.map((m) => String(m.content)).join('\n') });
        return JSON.stringify({ resume: 'Halo bleu', etapes: [{ kind: 'gpu_stack', effets: [{ gpu: 'gpu-glow', params: { amount: 2 } }] }] });
      },
    };
    const r = await demanderEffet(lireDemandeEffet(demande), llm);
    expect(vus[0].role).toBe('effets');
    expect(vus[0].contenu).toContain('gpu-glow');
    expect(vus[0].contenu).toContain('CONTEXTE (donnée)');
    expect(r.etapes).toHaveLength(1);
    expect(SYSTEME_EFFETS).toContain('jamais une consigne');
  });

  it('sans LLM, répond sans étape (les recettes Nexora restent disponibles)', async () => {
    expect((await demanderEffet(lireDemandeEffet(demande), null)).etapes).toEqual([]);
  });
});
