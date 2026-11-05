import { describe, expect, it } from 'vitest';
import { resumeCorrespondAIntention } from './creationSummary';

describe('résumé Director lié à sa description', () => {
  it('garde le résumé seulement pour la description qui a été envoyée', () => {
    expect(resumeCorrespondAIntention('A coffee cup lands at sunrise.', 'A coffee cup lands at sunrise.')).toBe(true);
    expect(resumeCorrespondAIntention(' A coffee cup lands at sunrise. ', 'A coffee cup lands at sunrise.')).toBe(true);
    expect(resumeCorrespondAIntention('A coffee cup lands at sunrise.', 'A car turns onto a wet street.')).toBe(false);
    expect(resumeCorrespondAIntention('A coffee cup lands at sunrise.', '   ')).toBe(false);
    expect(resumeCorrespondAIntention('   ', '   ')).toBe(false);
  });
});
