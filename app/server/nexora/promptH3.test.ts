import { describe, expect, it } from 'vitest';
import { instructionH3, validerPromptH3 } from './promptH3.js';

const corps = `integrated_multimodal_description: [Shot 1] Live-action, cinematic, a wide shot frames a red car on a coastal road. The camera performs an arc shot at slow speed around the car. [Shot 2] At 00:03.500, the camera cuts to a close-up of the headlight as the woman (S1) says: <d>[French] On y va.</d>

overall_soundscape: Waves crash on the rocks while the wind blows.

non_diegetic_music: N/A`;

describe('validateur de prompt H3 (guide officiel MiniMax)', () => {
  it('accepte un prompt T2VA conforme', () => {
    expect(validerPromptH3(corps, { mode: 't2va', dureeS: 5.17, dialogues: ['On y va.'] })).toEqual([]);
  });

  it('exige les trois champs, dans l’ordre', () => {
    const erreurs = validerPromptH3(corps.replace(/\n\noverall_soundscape:[^\n]*/, ''), { mode: 't2va', dureeS: 5.17 });
    expect(erreurs.join(' ')).toMatch(/overall_soundscape/);
    const inverse = `overall_soundscape: x\n\nintegrated_multimodal_description: [Shot 1] a\n\nnon_diegetic_music: N/A`;
    expect(validerPromptH3(inverse, { mode: 't2va', dureeS: 5 }).join(' ')).toMatch(/ordre/);
  });

  it('refuse un horodatage sur le premier plan et des horodatages non croissants ou hors durée', () => {
    expect(validerPromptH3(corps.replace('[Shot 1]', '[Shot 1] At 00:00.000,'), { mode: 't2va', dureeS: 5.17 }).join(' ')).toMatch(/Shot 1/);
    const hors = corps.replace('At 00:03.500', 'At 00:06.000');
    expect(validerPromptH3(hors, { mode: 't2va', dureeS: 5.17 }).join(' ')).toMatch(/durée/);
    const trois = corps.replace('non_diegetic', '').replace(
      '<d>[French] On y va.</d>',
      '<d>[French] On y va.</d> [Shot 3] At 00:02.000, the shot cuts to the sea.',
    );
    expect(validerPromptH3(`${trois}\n\nnon_diegetic_music: N/A`, { mode: 't2va', dureeS: 5.17 }).join(' ')).toMatch(/croissant/);
  });

  it('refuse des numéros de plans non consécutifs', () => {
    expect(validerPromptH3(corps.replace('[Shot 2]', '[Shot 3]'), { mode: 't2va', dureeS: 5.17 }).join(' ')).toMatch(/consécutif/);
  });

  it('exige les répliques de l’utilisateur mot pour mot dans <d>', () => {
    const e = validerPromptH3(corps.replace('On y va.', 'Allons-y.'), { mode: 't2va', dureeS: 5.17, dialogues: ['On y va.'] });
    expect(e.join(' ')).toMatch(/On y va\./);
  });

  it('exige la ligne d’instruction exacte en I2VA et FL2VA', () => {
    const i2va = `${instructionH3({ mode: 'i2va', dureeS: 5.17, dernierPlan: 2 })}\n\n${corps}`;
    expect(validerPromptH3(i2va, { mode: 'i2va', dureeS: 5.17 })).toEqual([]);
    expect(validerPromptH3(corps, { mode: 'i2va', dureeS: 5.17 }).join(' ')).toMatch(/instruction/);
    const fl = instructionH3({ mode: 'fl2va', dureeS: 5.17, dernierPlan: 2 });
    expect(fl).toBe(
      'How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 2) aligns with the 5.17-second mark of the target video.',
    );
    expect(validerPromptH3(`${fl}\n\n${corps}`, { mode: 'fl2va', dureeS: 5.17 })).toEqual([]);
  });

  it('refuse un champ inventé hors du guide (ex. on_screen_text)', () => {
    const avec = corps.replace('non_diegetic_music: N/A', 'on_screen_text: At 00:04.200, golden text.\n\nnon_diegetic_music: N/A');
    expect(validerPromptH3(avec, { mode: 't2va', dureeS: 5.17 }).join(' ')).toMatch(/on_screen_text/);
  });
});
