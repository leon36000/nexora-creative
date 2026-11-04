import { describe, expect, it } from 'vitest';
import type { ClientLlm } from './llm.js';
import { moderer, modererParRegles } from './moderation.js';

const llm = (r: string | Error): ClientLlm & { appels: number } => {
  const o = { appels: 0, async completer() { o.appels++; if (r instanceof Error) throw r; return r; } };
  return o;
};

describe('modération avant rendu', () => {
  it('laisse passer la fiction et l’action stylisée (dragons, combats, batailles spatiales)', () => {
    for (const t of ['Un dragon crache du feu sur une forteresse', 'Combat de karaté sous la pluie', 'Duel d’épées d’énergie dans un volcan', 'Une flotte surgit de l’hyperespace']) {
      expect(modererParRegles(t).ok, t).toBe(true);
    }
  });

  it('refuse par règles, sans appeler le LLM, le contenu sexuel impliquant des mineurs (FR et EN)', async () => {
    const l = llm('{"verdict":"ok"}');
    for (const t of ['une adolescente nue', 'naked child on a beach', 'un enfant dans une scène sexuelle']) {
      const v = await moderer(t, l);
      expect(v, t).toMatchObject({ ok: false, categorie: 'mineurs', source: 'regles' });
    }
    expect(l.appels).toBe(0);
  });

  it('suit le verdict du LLM : refus avec raison en français, ou accord', async () => {
    expect(await moderer('x', llm('{"verdict":"refuse","categorie":"personne_reelle","raison":"Imitation d’une personne réelle."}'))).toMatchObject({ ok: false, source: 'llm', categorie: 'personne_reelle' });
    expect(await moderer('x', llm('```json\n{"verdict":"ok"}\n```'))).toMatchObject({ ok: true, source: 'llm' });
  });

  it('retourne un refus et demande le motif en anglais lorsque la langue est explicitement choisie', async () => {
    expect(modererParRegles('fake video of a named person', 'en').raison).toBe('Deceptive impersonations of real people are not allowed.');
    let systeme = '';
    const anglais: ClientLlm = { async completer(_role, messages) {
      const contenu = messages[0].content;
      systeme = typeof contenu === 'string' ? contenu : contenu.map((partie) => partie.type === 'text' ? partie.text : '').join('');
      return '{"verdict":"refuse","categorie":"personne_reelle","raison":"Deceptive impersonation is not allowed."}';
    } };
    expect(await moderer('x', anglais, () => {}, 'en')).toMatchObject({ ok: false, raison: 'Deceptive impersonation is not allowed.' });
    expect(systeme).toContain('one short sentence in English for the user');
    expect(modererParRegles('fake video of a named person').raison).toBe('Les imitations trompeuses de personnes réelles sont interdites.');
  });

  it('en cas de panne ou de réponse illisible du LLM, applique les règles seules et le journalise', async () => {
    const msgs: string[] = [];
    expect(await moderer('un renard', llm(new Error('HTTP 503')), (m) => msgs.push(m))).toMatchObject({ ok: true, source: 'regles_seules' });
    expect(await moderer('un renard', llm('pas du json'), (m) => msgs.push(m))).toMatchObject({ ok: true, source: 'regles_seules' });
    expect(await moderer('un renard', null)).toMatchObject({ ok: true, source: 'regles_seules' });
    expect(msgs).toHaveLength(2);
  });
});
