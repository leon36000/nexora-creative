import { expect, it } from 'vitest';
import { mkdtempSync, readdirSync, readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { creerExportProres } from './exportProres.js';

function base() {
  const root = mkdtempSync(join(tmpdir(), 'export-prores-test-'));
  const source = join(root, 'source.mp4'); writeFileSync(source, 'source synthetique');
  return { root, source, exports: join(root, 'exports') };
}

it('dedoublonne deux demandes et publie atomiquement apres validation', async () => {
  const b = base(); let encoder = 0; let relacher!: () => void; let chemin = '';
  const attente = new Promise<void>((r) => { relacher = r; });
  const exporteur = creerExportProres(async (_source, provisoire) => {
    encoder++; chemin = provisoire; writeFileSync(provisoire, 'partiel'); await attente;
    writeFileSync(provisoire, 'complet');
  }, async (p) => { expect(readFileSync(p, 'utf8')).toBe('complet'); });
  const a = exporteur(4, b.source, b.exports), c = exporteur(4, b.source, b.exports);
  expect(encoder).toBe(1); expect(existsSync(chemin.replace('provisoire', 'complet'))).toBe(false);
  relacher(); const [x, y] = await Promise.all([a, c]);
  expect(x).toBe(y); expect(readFileSync(x, 'utf8')).toBe('complet');
  expect(statSync(x).ino).toBe(statSync(chemin).ino);
  expect(await exporteur(4, b.source, b.exports)).toBe(x); expect(encoder).toBe(1);
});

it('conserve le partiel après échec et retente sur un nouveau chemin', async () => {
  const b = base(); const chemins: string[] = [];
  const exporteur = creerExportProres(async (_source, p) => {
    chemins.push(p); writeFileSync(p, chemins.length === 1 ? 'partiel' : 'complet');
    if (chemins.length === 1) throw new Error('encodeur en echec');
  }, async () => {});
  await expect(exporteur(8, b.source, b.exports)).rejects.toThrow('encodeur en echec');
  expect(readFileSync(chemins[0], 'utf8')).toBe('partiel');
  expect(JSON.parse(readFileSync(join(chemins[0], '..', 'ECHEC.json'), 'utf8')).phase).toBe('encodage');
  const sortie = await exporteur(8, b.source, b.exports);
  expect(chemins[1]).not.toBe(chemins[0]); expect(readFileSync(sortie, 'utf8')).toBe('complet');
  expect(readdirSync(b.exports)).toHaveLength(2);
});

it('ignore le cache historique et refuse de publier si validation échoue', async () => {
  const b = base(); const { mkdirSync } = await import('node:fs'); mkdirSync(b.exports);
  const historique = join(b.exports, 'film_9_prores.mov'); writeFileSync(historique, 'ancien partiel'); let chemin = '';
  const exporteur = creerExportProres(async (_s, p) => { chemin=p; writeFileSync(p, 'faux'); }, async () => { throw new Error('validation'); });
  await expect(exporteur(9, b.source, b.exports)).rejects.toThrow('validation');
  expect(readFileSync(historique, 'utf8')).toBe('ancien partiel');
  expect(readFileSync(chemin, 'utf8')).toBe('faux');
  expect(existsSync(chemin.replace('provisoire','complet'))).toBe(false);
  expect(JSON.parse(readFileSync(join(chemin, '..', 'ECHEC.json'), 'utf8')).phase).toBe('validation');
});

it('refuse la publication si la source change pendant l’encodage', async () => {
  const b = base(); let provisoire = '';
  const exporteur = creerExportProres(async (_s, p) => { provisoire=p; writeFileSync(p, 'partiel'); writeFileSync(b.source, 'source changee'); }, async () => {});
  await expect(exporteur(4, b.source, b.exports)).rejects.toThrow('source a changé');
  expect(existsSync(provisoire)).toBe(true); expect(existsSync(provisoire.replace('provisoire','complet'))).toBe(false);
});


it('ne réutilise pas une sortie modifiée après publication', async () => {
  const b = base(); let appels = 0;
  const exporteur = creerExportProres(async (_s, p) => { appels++; writeFileSync(p, 'complet'); }, async () => {});
  const ancien = await exporteur(10, b.source, b.exports);
  writeFileSync(ancien, 'modifie');
  const nouveau = await exporteur(10, b.source, b.exports);
  expect(nouveau).not.toBe(ancien); expect(appels).toBe(2);
  expect(readFileSync(ancien, 'utf8')).toBe('modifie');
});

it('une interruption simulée conserve le fichier et ne publie pas', async () => {
  const b = base(); let chemin = '';
  const exporteur = creerExportProres(async (_s, p) => { chemin = p; writeFileSync(p, 'partiel'); throw Object.assign(new Error('interruption'), { signal: 'SIGTERM' }); }, async () => {});
  await expect(exporteur(11, b.source, b.exports)).rejects.toThrow('interruption');
  expect(readFileSync(chemin, 'utf8')).toBe('partiel');
  expect(existsSync(chemin.replace('provisoire','complet'))).toBe(false);
  expect(JSON.parse(readFileSync(join(chemin, '..', 'ECHEC.json'), 'utf8')).phase).toBe('encodage');
});

it('refuse durée tronquée, mauvais profil et audio non PCM', async () => {
  const { verifierRapports } = await import('./exportProres.js');
  const source = {format:{duration:'10'}, streams:[{codec_type:'audio'}]};
  const bon = {format:{duration:'10'}, streams:[{codec_type:'video',codec_name:'prores',profile:'HQ',pix_fmt:'yuv422p10le',width:160,height:90},{codec_type:'audio',codec_name:'pcm_s16le'}]};
  expect(() => verifierRapports(source,bon)).not.toThrow();
  expect(() => verifierRapports(source,{...bon,format:{duration:'1'}})).toThrow();
  expect(() => verifierRapports(source,{...bon,streams:[{...bon.streams[0],profile:'LT'},bon.streams[1]]})).toThrow();
  expect(() => verifierRapports(source,{...bon,streams:[bon.streams[0],{codec_type:'audio',codec_name:'aac'}]})).toThrow();
});

it('contrôle la durée des flux vidéo sans imposer le nombre de frames VFR', async () => {
  const { verifierChronologies } = await import('./exportProres.js');
  const source = { images: 48, debut: 0, fin: 2, derniereDuree: 1 / 24 };
  expect(() => verifierChronologies(source, { images: 12, debut: 0, fin: 0.5, derniereDuree: 1 / 24 })).toThrow();
  expect(() => verifierChronologies(source, { images: 47, debut: 0, fin: 2, derniereDuree: 1 / 24 })).not.toThrow();
  expect(() => verifierChronologies(source, { images: 0, debut: 0, fin: 2, derniereDuree: 1 / 24 })).toThrow();
  expect(() => verifierChronologies({ images: 4, debut: 0, fin: 2, derniereDuree: 1.6 }, { images: 3, debut: 0, fin: 1.3, derniereDuree: 0.1 })).toThrow();
  for (const invalid of [ { ...source, derniereDuree: NaN }, { ...source, images: -1 }, { ...source, images: NaN }, { ...source, debut: Infinity }, { ...source, derniereDuree: 0 } ]) {
    expect(() => verifierChronologies(source, invalid)).toThrow();
    expect(() => verifierChronologies(invalid, source)).toThrow();
  }
  expect(() => verifierChronologies({ ...source, debut: -2, fin: 0 }, source)).not.toThrow();
});

it('lit les horodatages par clé et refuse une durée finale absente', async () => {
  const { verifierProres } = await import('./exportProres.js');
  const b = base(); const sonde = join(b.root, 'fausse-sonde');
  const entete = JSON.stringify({format:{duration:'2'},streams:[{codec_type:'video',codec_name:'prores',profile:'HQ',pix_fmt:'yuv422p10le',width:160,height:90}]});
  const script = (fin: string) => `#!/usr/bin/env node\nif (process.argv.includes('json')) console.log(${JSON.stringify(entete)}); else { console.log('duration_time=1|best_effort_timestamp_time=0|'); console.log('pkt_duration_time=${fin}|best_effort_timestamp_time=1|'); }\n`;
  writeFileSync(sonde, script('1'), {mode:0o755});
  await expect(verifierProres('sortie', 'source', sonde)).resolves.toBeUndefined();
  writeFileSync(sonde, script('N/A'));
  await expect(verifierProres('sortie', 'source', sonde)).rejects.toThrow('dernière image non vérifiable');
});
