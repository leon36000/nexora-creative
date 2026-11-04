import { describe, expect, it } from 'vitest';
import { prolongerRedirect } from './prolongerRedirect';

describe('redirection de /extend vers Prolonger', () => {
  it('conserve take pour prolonger un plan', () => {
    expect(prolongerRedirect(new URLSearchParams('take=42'))).toBe('/prolonger?take=42');
  });

  it('remplace transition par raccord et conserve take', () => {
    expect(prolongerRedirect(new URLSearchParams('mode=transition&take=42'))).toBe('/prolonger?mode=raccord&take=42');
  });

  it('ne crée pas de take quand il manque', () => {
    expect(prolongerRedirect(new URLSearchParams())).toBe('/prolonger');
    expect(prolongerRedirect(new URLSearchParams('mode=transition'))).toBe('/prolonger?mode=raccord');
  });

  it('ne transmet pas d’autres paramètres', () => {
    expect(prolongerRedirect(new URLSearchParams('take=42&quality=high'))).toBe('/prolonger?take=42');
  });
});
