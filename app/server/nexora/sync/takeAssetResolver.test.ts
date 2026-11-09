import { lstatSync, mkdirSync, mkdtempSync, symlinkSync, writeFileSync } from 'node:fs';
import { isAbsolute, join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { createHash } from 'node:crypto';
import {
  creerResolveurSyncTake,
  SYNC_WORKER_MAX_DURATION_SECONDS,
  SYNC_WORKER_MAX_INPUT_BYTES,
  type SyncTakeProbe,
  type TakeForSync,
} from './takeAssetResolver.js';

const racineTest = process.env.SYNC_TEST_ROOT || process.env.TMPDIR;
if (!racineTest || !isAbsolute(racineTest)) throw new Error('SYNC_TEST_ROOT ou TMPDIR absolu requis.');
try {
  const racineStat = lstatSync(racineTest);
  if (racineStat.isSymbolicLink() || !racineStat.isDirectory()) throw new Error();
} catch {
  throw new Error('La racine de test explicite doit être un dossier réel existant.');
}

function fixture(bytes = Buffer.from('fixture-media')) {
  const dossier = mkdtempSync(join(racineTest!, 'take-resolver-'));
  const fichier = join(dossier, 'source.bin');
  writeFileSync(fichier, bytes, { flag: 'wx' });
  const take: TakeForSync = { id: 41, organisation_id: 'org-a', kind: 'video', status: 'done', output_path: fichier };
  const info: SyncTakeProbe = {
    format: { duration: '9.04' },
    streams: [{ codec_type: 'video', avg_frame_rate: '25/1', r_frame_rate: '25/1' }],
  };
  return { dossier, fichier, take, info };
}

function resolver(take: TakeForSync | undefined, info: unknown, opts: {
  probe?: (bin: string, path: string, timeout: number) => Promise<unknown>;
  limits?: { maxInputBytes?: number; maxDurationSeconds?: number; probeTimeoutMs?: number };
  lookup?: (id: number) => TakeForSync | undefined;
} = {}) {
  return creerResolveurSyncTake({
    getTake: opts.lookup ?? ((id) => take?.id === id ? take : undefined),
    ffprobeBin: '/usr/bin/ffprobe',
    limits: opts.limits,
    probe: opts.probe ?? (async () => info),
  });
}

describe('résolution DB → SyncTakeAsset', () => {
  it('refuse avant toute lecture une prise d’une autre organisation', async () => {
    const f = fixture();
    let sondes = 0;
    const r = resolver(f.take, f.info, { probe: async () => { sondes++; return f.info; } });
    await expect(r('org-b', f.take.id)).resolves.toBeUndefined();
    expect(sondes).toBe(0);
  });

  it.each(['queued', 'rendering', 'failed', 'stopped'] as const)('n’accepte que status=done (%s refusé)', async (status) => {
    const f = fixture(); f.take.status = status;
    await expect(resolver(f.take, f.info)('org-a', f.take.id)).resolves.toBeUndefined();
  });

  it('refuse une kind inconnue et une sortie absente', async () => {
    const f = fixture();
    f.take.kind = 'still';
    await expect(resolver(f.take, f.info)('org-a', f.take.id)).resolves.toBeUndefined();
    f.take.kind = 'video'; f.take.output_path = null;
    await expect(resolver(f.take, f.info)('org-a', f.take.id)).resolves.toBeUndefined();
  });

  it('retourne l’empreinte SHA-256 du flux lu et les mesures vidéo bornées', async () => {
    const data = Buffer.from('video fixture: bytes stay bounded');
    const f = fixture(data);
    let fdPath = '';
    let timeout = 0;
    const r = resolver(f.take, f.info, {
      limits: { maxInputBytes: 256, maxDurationSeconds: 10, probeTimeoutMs: 2200 },
      probe: async (_bin, path, ms) => { fdPath = path; timeout = ms; return f.info; },
    });
    const asset = await r('org-a', f.take.id);
    expect(asset).toMatchObject({
      id: f.take.id, organisationId: 'org-a', status: 'done', kind: 'video',
      outputPath: f.fichier, bytes: data.length, sha256: createHash('sha256').update(data).digest('hex'),
      durationSeconds: 9.04, fps: 25,
    });
    expect(fdPath).toMatch(new RegExp(`^/proc/${process.pid}/fd/\\d+$`));
    expect(timeout).toBe(2200);
  });

  it('résout une prise audio et son sample rate depuis ffprobe', async () => {
    const f = fixture(Buffer.from('wav fixture'));
    f.take.kind = 'audio';
    const audio = { format: { duration: '8.5' }, streams: [{ codec_type: 'audio', sample_rate: '16000' }] };
    await expect(resolver(f.take, audio)('org-a', f.take.id)).resolves.toMatchObject({ kind: 'audio', sampleRate: 16000, durationSeconds: 8.5 });
  });

  it('refuse un lien symbolique final et un chemin dont un parent est un lien', async () => {
    const f = fixture();
    const finalLink = join(f.dossier, 'source-link.bin'); symlinkSync(f.fichier, finalLink);
    f.take.output_path = finalLink;
    await expect(resolver(f.take, f.info)('org-a', f.take.id)).resolves.toBeUndefined();

    const parentLink = join(f.dossier, 'alias'); symlinkSync(f.dossier, parentLink);
    f.take.output_path = join(parentLink, 'source.bin');
    await expect(resolver(f.take, f.info)('org-a', f.take.id)).resolves.toBeUndefined();

    const directory = join(f.dossier, 'directory'); mkdirSync(directory);
    f.take.output_path = directory;
    await expect(resolver(f.take, f.info)('org-a', f.take.id)).resolves.toBeUndefined();
  });

  it('refuse les fichiers vides ou au-dessus de la limite avant la sonde', async () => {
    const f = fixture(Buffer.alloc(9));
    let sondes = 0;
    const r = resolver(f.take, f.info, { limits: { maxInputBytes: 8 }, probe: async () => { sondes++; return f.info; } });
    await expect(r('org-a', f.take.id)).resolves.toBeUndefined();
    expect(sondes).toBe(0);

    const empty = fixture(Buffer.alloc(0));
    await expect(resolver(empty.take, empty.info)('org-a', empty.take.id)).resolves.toBeUndefined();
  });

  it('refuse une mutation du contenu avant la fin de la sonde', async () => {
    const f = fixture();
    const r = resolver(f.take, f.info, {
      probe: async () => { writeFileSync(f.fichier, 'replacement bytes'); return f.info; },
    });
    await expect(r('org-a', f.take.id)).resolves.toBeUndefined();
  });

  it.each(['organisation_id', 'status', 'output_path'] as const)('revalide la ligne DB si le champ %s change pendant le probe', async (field) => {
    const f = fixture();
    const r = resolver(f.take, f.info, {
      probe: async () => {
        if (field === 'organisation_id') f.take.organisation_id = 'org-b';
        if (field === 'status') f.take.status = 'failed';
        if (field === 'output_path') f.take.output_path = join(f.dossier, 'replacement.bin');
        return f.info;
      },
    });
    await expect(r('org-a', f.take.id)).resolves.toBeUndefined();
  });

  it('refuse des mesures manquantes, invalides ou au-delà des caps worker', async () => {
    const f = fixture();
    await expect(resolver(f.take, { streams: [{ codec_type: 'video', avg_frame_rate: '0/0' }], format: { duration: '9' } })('org-a', f.take.id)).resolves.toBeUndefined();
    await expect(resolver(f.take, { streams: [{ codec_type: 'video', avg_frame_rate: '25/1' }], format: { duration: '31' } })('org-a', f.take.id)).resolves.toBeUndefined();
    await expect(resolver(f.take, { streams: [{ codec_type: 'video', avg_frame_rate: '25/1' }], format: { duration: '0' } })('org-a', f.take.id)).resolves.toBeUndefined();
    expect(() => creerResolveurSyncTake({ getTake: () => undefined, ffprobeBin: '/usr/bin/ffprobe', limits: { maxInputBytes: SYNC_WORKER_MAX_INPUT_BYTES + 1 } })).toThrow();
    expect(() => creerResolveurSyncTake({ getTake: () => undefined, ffprobeBin: '/usr/bin/ffprobe', limits: { maxDurationSeconds: SYNC_WORKER_MAX_DURATION_SECONDS + 1 } })).toThrow();
  });

  it('borne l’id DB avant toute consultation', async () => {
    const f = fixture(); let lookups = 0;
    const r = resolver(f.take, f.info, { lookup: () => { lookups++; return f.take; } });
    await expect(r('org-a', 0)).resolves.toBeUndefined();
    await expect(r('org-a', Number.MAX_SAFE_INTEGER + 1)).resolves.toBeUndefined();
    expect(lookups).toBe(0);
  });
});
