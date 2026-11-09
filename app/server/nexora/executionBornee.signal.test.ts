import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ spawn: vi.fn() }));
vi.mock('node:child_process', () => ({ spawn: mocks.spawn }));

import { executerBorne } from './executionBornee.js';

type Mode = 'error-event' | 'throw' | 'false';

function fauxEnfant(mode: Mode) {
  const enfant = new EventEmitter() as EventEmitter & {
    stdout: PassThrough;
    kill: ReturnType<typeof vi.fn>;
    unref: ReturnType<typeof vi.fn>;
  };
  enfant.stdout = new PassThrough();
  enfant.kill = vi.fn(() => {
    if (mode === 'error-event') {
      const err = Object.assign(new Error('kill EACCES'), { code: 'EACCES' });
      enfant.emit('error', err);
      return false;
    }
    if (mode === 'throw') throw Object.assign(new Error('kill EACCES'), { code: 'EACCES' });
    return false;
  });
  enfant.unref = vi.fn();
  return enfant;
}

it.each<Mode>(['error-event', 'throw', 'false'])('garde la raison du délai si kill retourne %s', async (mode) => {
  vi.useFakeTimers();
  try {
    const enfant = fauxEnfant(mode);
    mocks.spawn.mockReturnValue(enfant);
    const promesse = executerBorne('/ignored', [], 10);
    const attenteErreur = expect(promesse).rejects.toThrow('Délai dépassé ; arrêt de l’enfant non confirmé.');
    await vi.advanceTimersByTimeAsync(10);
    await attenteErreur;
    expect(enfant.kill).toHaveBeenCalledWith('SIGKILL');
    expect(enfant.stdout.destroyed).toBe(true);
    expect(enfant.unref).toHaveBeenCalledOnce();
  } finally {
    vi.useRealTimers();
  }
});

it.each<Mode>(['error-event', 'throw', 'false'])('garde la raison du consommateur si kill retourne %s', async (mode) => {
  const enfant = fauxEnfant(mode);
  mocks.spawn.mockReturnValue(enfant);
  const promesse = executerBorne('/ignored', [], 5000, () => { throw new Error('erreur consommateur'); });
  enfant.stdout.emit('data', Buffer.from('x'));
  await expect(promesse).rejects.toThrow('Flux de sortie invalide ; arrêt de l’enfant non confirmé.');
  expect(enfant.kill).toHaveBeenCalledWith('SIGKILL');
  expect(enfant.stdout.destroyed).toBe(true);
  expect(enfant.unref).toHaveBeenCalledOnce();
});
