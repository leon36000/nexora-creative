#!/usr/bin/env node
// Qualification sans serveur, fichier de données, configuration ni accès réseau.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const [release, uidTexte] = process.argv.slice(2);
assert(release && /^\d+$/.test(uidTexte ?? ''), 'usage: qualifier-release.mjs RELEASE UID');
assert.equal(process.getuid(), Number(uidTexte), 'identité réelle différente du service attendu');
assert.equal(process.geteuid(), Number(uidTexte), 'identité effective différente du service attendu');
const require = createRequire(pathToFileURL(resolve(release, 'app/package.json')));
const Database = require('better-sqlite3');
const db = new Database(':memory:');
try {
  assert.equal(db.prepare('SELECT 42 AS valeur').get().valeur, 42);
} finally {
  db.close();
}
const sharp = require('sharp');
const png = await sharp({ create: { width: 2, height: 3, channels: 3, background: '#123456' } }).png().toBuffer();
const image = await sharp(png).metadata();
assert.equal(image.width, 2);
assert.equal(image.height, 3);
assert.equal(image.format, 'png');
process.stdout.write(JSON.stringify({ sqlite: 'memory_select_42_ok', sharp: 'png_2x3_roundtrip_ok', uid: process.getuid(), euid: process.geteuid(), arch: process.arch, platform: process.platform, node: process.version }) + '\n');
