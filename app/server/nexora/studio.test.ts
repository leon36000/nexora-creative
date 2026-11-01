import { describe, expect, it } from 'vitest';
import {
  creationsPourStudio, decouperSousTitres, demanderAssistant, detecterTemps, lireDemandeAssistant, lireReponseAssistant,
  lireSilences, lireTranscription, MAX_COMMANDES, silencesAvecMarge, TAUX_RYTHME,
} from './studio.js';
import type { ClientLlm } from './llm.js';

const prise = (o: Partial<{ id: number; kind: string; status: string; shot_name: string; output_path: string | null; settings: string }>) => ({
  id: 1, kind: 'video', status: 'done', shot_name: 'plan', output_path: '/x/plan.mp4', settings: '{}', created_at: '2026-11-01', ...o,
});

describe('créations du Mode Studio', () => {
  it('garde les prises terminées et devine leur genre', () => {
    const c = creationsPourStudio([
      prise({ id: 1, settings: JSON.stringify({ intention: 'Un dragon', lengthFrames: 121 }) }),
      prise({ id: 2, kind: 'still', output_path: '/x/a.png' }),
      prise({ id: 3, kind: 'musique', output_path: '/x/m.mp3', settings: JSON.stringify({ dureeS: 60 }) }),
      prise({ id: 4, status: 'failed' }),
      prise({ id: 5, output_path: null }),
    ]);
    expect(c.map((x) => [x.id, x.genre])).toEqual([[1, 'video'], [2, 'image'], [3, 'musique']]);
    expect(c[0]).toMatchObject({ nom: 'Un dragon', url: '/api/studio/media/1', dureeS: 5 });
    expect(c[2].dureeS).toBe(60);
  });
});

describe('assistant du Mode Studio', () => {
  it('ne garde que les commandes et actions connues, aux temps finis', () => {
    const r = lireReponseAssistant({
      reponse: 'Je coupe.',
      commandes: [
        { commande: 'couper', id: 'a', aS: 2.5 },
        { commande: 'rm -rf', id: 'a' },
        { commande: 'deplacer', id: 'a', debutS: 'demain' },
        { commande: 'texte', texte: 'Titre', debutS: 0, dureeS: 3 },
      ],
      actions: [{ type: 'silences' }, { type: 'pirater' }],
    });
    expect(r.commandes.map((c) => c.commande)).toEqual(['couper', 'texte']);
    expect(r.actions.map((a) => a.type)).toEqual(['silences']);
  });

  it('borne le nombre de commandes et donne une réponse par défaut', () => {
    const r = lireReponseAssistant({ commandes: Array.from({ length: 500 }, () => ({ commande: 'supprimer', ids: ['a'] })) });
    expect(r.commandes).toHaveLength(MAX_COMMANDES);
    expect(r.reponse).toBeTruthy();
  });

  it('refuse une demande vide et garde les huit derniers échanges', () => {
    expect(() => lireDemandeAssistant({ demande: '  ' })).toThrow();
    const d = lireDemandeAssistant({ demande: 'coupe', historique: Array.from({ length: 12 }, (_, i) => ({ role: i % 2 ? 'assistant' : 'user', content: `m${i}` })) });
    expect(d.historique).toHaveLength(8);
    expect(d.historique[7].content).toBe('m11');
  });

  it('envoie l’état et la demande au rôle « assistant » et lit le JSON rendu', async () => {
    const vus: unknown[] = [];
    const llm: ClientLlm = {
      async completer(role, messages, options) {
        vus.push({ role, json: options?.json, dernier: messages[messages.length - 1].content });
        return '```json\n{"reponse":"Titre ajouté.","commandes":[{"commande":"texte","texte":"Bonjour","debutS":0,"dureeS":2}]}\n```';
      },
    };
    const r = await demanderAssistant(lireDemandeAssistant({ demande: 'ajoute un titre', etat: { fps: 30 } }), llm);
    expect(r.commandes).toHaveLength(1);
    expect(vus[0]).toMatchObject({ role: 'assistant', json: true });
    expect(String((vus[0] as any).dernier)).toContain('"fps":30');
  });

  it('dit clairement quand aucun modèle n’est configuré', async () => {
    const r = await demanderAssistant(lireDemandeAssistant({ demande: 'coupe' }), null);
    expect(r.commandes).toEqual([]);
    expect(r.reponse).toMatch(/pas disponible/);
  });
});

describe('silences', () => {
  const stderr = [
    '  Duration: 00:00:12.50, start: 0.000000, bitrate: 128 kb/s',
    '[silencedetect @ 0x1] silence_start: 1.2',
    '[silencedetect @ 0x1] silence_end: 2.4 | silence_duration: 1.2',
    '[silencedetect @ 0x1] silence_start: -0.01',
    '[silencedetect @ 0x1] silence_end: 0.3 | silence_duration: 0.31',
    '[silencedetect @ 0x1] silence_start: 11.1',
  ].join('\n');

  it('lit les plages, y compris un silence qui court jusqu’à la fin', () => {
    expect(lireSilences(stderr, 12.5)).toEqual([
      { debutS: 1.2, finS: 2.4 },
      { debutS: 0, finS: 0.3 },
      { debutS: 11.1, finS: 12.5 },
    ]);
  });

  it('garde une marge de parole et oublie les silences trop courts une fois rognés', () => {
    expect(silencesAvecMarge([{ debutS: 1.2, finS: 2.4 }, { debutS: 0, finS: 0.3 }])).toEqual([{ debutS: 1.32, finS: 2.28 }]);
  });
});

describe('temps forts d’une musique', () => {
  it('retrouve 120 BPM et la grille d’un clic métronomique', () => {
    const duree = 10;
    const pcm = new Float32Array(TAUX_RYTHME * duree);
    const periode = 0.5;
    for (let t = 0.25; t < duree; t += periode) {
      const debut = Math.round(t * TAUX_RYTHME);
      for (let i = 0; i < 400; i++) pcm[debut + i] = Math.sin(i * 0.6) * Math.exp(-i / 80);
    }
    const r = detecterTemps(pcm, TAUX_RYTHME);
    expect(Math.abs(r.bpm - 120)).toBeLessThan(3);
    expect(r.temps.length).toBeGreaterThanOrEqual(18);
    const ecarts = r.temps.map((t) => Math.abs(((t - 0.25) % periode + periode) % periode));
    expect(Math.max(...ecarts.map((e) => Math.min(e, periode - e)))).toBeLessThan(0.06);
  });

  it('ne renvoie rien pour un son trop court', () => {
    expect(detecterTemps(new Float32Array(1000))).toEqual({ bpm: 0, temps: [] });
  });
});

describe('transcription et sous-titres', () => {
  const brut = JSON.stringify({
    langue: 'fr',
    phrases: [
      { texte: 'Le froid qui réveille', debutS: 2.1, finS: 4.78, mots: [{ mot: 'Le', debutS: 2.1, finS: 2.3 }] },
      { texte: '', debutS: 5, finS: 6 },
      {
        texte: 'Une phrase beaucoup trop longue pour tenir sur une seule ligne de sous-titres.',
        debutS: 6, finS: 11,
        mots: 'Une phrase beaucoup trop longue pour tenir sur une seule ligne de sous-titres.'.split(' ').map((m, i) => ({ mot: m, debutS: 6 + i * 0.4, finS: 6.3 + i * 0.4 })),
      },
    ],
  });

  it('jette les phrases vides et lit les mots', () => {
    const t = lireTranscription(brut);
    expect(t.langue).toBe('fr');
    expect(t.phrases).toHaveLength(2);
  });

  it('découpe les phrases longues en lignes de 42 caractères au plus, aux temps des mots', () => {
    const lignes = decouperSousTitres(lireTranscription(brut));
    expect(lignes[0]).toEqual({ texte: 'Le froid qui réveille', debutS: 2.1, finS: 4.78 });
    expect(lignes.length).toBeGreaterThan(2);
    for (const l of lignes) expect(l.texte.length).toBeLessThanOrEqual(42);
    expect(lignes[1].debutS).toBe(6);
    expect(lignes.map((l) => l.texte).slice(1).join(' ')).toBe('Une phrase beaucoup trop longue pour tenir sur une seule ligne de sous-titres.');
  });
});
