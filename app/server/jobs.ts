/**
 * Job history — SQLite, one row per take. Settings persist as JSON so any
 * take can be refired verbatim or with a nudged seed/prompt.
 */
import Database from 'better-sqlite3';
import { mkdirSync } from 'fs';
import { join } from 'path';
import { config } from './config.js';
import { compteCourant } from './nexora/compte.js';
import { selectionnerFilmsAvecReservationsEnAttente } from './nexora/filmReservations.js';

mkdirSync(config.dataDir, { recursive: true });
const db = new Database(join(config.dataDir, 'openfield.db'));
// Nexora : lectures concurrentes pendant les écritures (direct, réconciliation, requêtes) et attente courte sur verrou.
db.pragma('journal_mode = WAL');
db.pragma('busy_timeout = 5000');

db.exec(`
CREATE TABLE IF NOT EXISTS takes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  project_id INTEGER,
  kind TEXT NOT NULL,               -- 'video' | 'still' | 'upres'
  shot_name TEXT NOT NULL,
  prompt_id TEXT,                   -- ComfyUI prompt id
  status TEXT NOT NULL DEFAULT 'queued',  -- queued|rendering|done|failed|stopped
  settings TEXT NOT NULL,           -- JSON of all params
  output_path TEXT,
  render_seconds REAL,
  transcript TEXT,
  starred INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  parent_take_id INTEGER            -- upres links back to its source take
);
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  folder TEXT NOT NULL,
  last_used TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS speed (
  key TEXT PRIMARY KEY,             -- model|WxH|frames bucket
  seconds_per_step REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS preambles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  text TEXT NOT NULL,
  sort INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cast (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE COLLATE NOCASE,   -- what @mentions match
  kind TEXT NOT NULL DEFAULT 'character',     -- character | prop | place
  refs TEXT NOT NULL DEFAULT '[]',            -- JSON CastRef[], 1 to 6
  notes TEXT NOT NULL DEFAULT '',             -- the words a mention puts in the prompt
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS take_workflows (
  take_id INTEGER PRIMARY KEY,      -- one API-format graph per take
  graph TEXT NOT NULL,              -- JSON, loadable as-is in ComfyUI
  source TEXT NOT NULL              -- 'engine' (what ran) | 'submitted' (our copy)
);
`);

/**
 * Nexora : chaque prise, personnage et projet appartient à une organisation. Les lectures faites pendant une requête
 * ne voient que l'organisation du compte (server/nexora/compte.ts) ; le moteur, hors requête, voit tout pour terminer
 * les rendus. Migration idempotente : colonne `organisation_id` ('local' pour l'existant) et unicité des noms de
 * personnages et de projets par organisation au lieu de globale.
 */
function colonnes(table: string): string[] {
  return (db.prepare(`PRAGMA table_info(${table})`).all() as { name: string }[]).map((c) => c.name);
}
if (!colonnes('takes').includes('organisation_id')) {
  db.exec("ALTER TABLE takes ADD COLUMN organisation_id TEXT NOT NULL DEFAULT 'local'");
}
if (!colonnes('cast').includes('organisation_id')) {
  db.exec(`
    BEGIN;
    CREATE TABLE cast_org (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      organisation_id TEXT NOT NULL DEFAULT 'local',
      name TEXT NOT NULL COLLATE NOCASE,
      kind TEXT NOT NULL DEFAULT 'character',
      refs TEXT NOT NULL DEFAULT '[]',
      notes TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (organisation_id, name)
    );
    INSERT INTO cast_org (id, name, kind, refs, notes, created_at) SELECT id, name, kind, refs, notes, created_at FROM cast;
    DROP TABLE cast;
    ALTER TABLE cast_org RENAME TO cast;
    COMMIT;`);
}
if (!colonnes('projects').includes('organisation_id')) {
  db.exec(`
    BEGIN;
    CREATE TABLE projects_org (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      organisation_id TEXT NOT NULL DEFAULT 'local',
      name TEXT NOT NULL,
      folder TEXT NOT NULL,
      last_used TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE (organisation_id, name)
    );
    INSERT INTO projects_org (id, name, folder, last_used) SELECT id, name, folder, last_used FROM projects;
    DROP TABLE projects;
    ALTER TABLE projects_org RENAME TO projects;
    COMMIT;`);
}

/** Organisation de la requête en cours, ou null hors requête (moteur, reprise, scripts) : alors pas de filtre. */
function org(): string | null {
  return compteCourant()?.organisationId ?? null;
}
/** Organisation à écrire sur une nouvelle ligne. */
const orgEcrite = () => org() ?? 'local';
/** Fragment SQL et paramètres qui limitent une requête à l'organisation en cours. */
function portee(prefixe = 'AND'): [string, unknown[]] {
  const o = org();
  return o === null ? ['', []] : [` ${prefixe} organisation_id=?`, [o]];
}

export interface Take {
  id: number;
  created_at: string;
  project_id: number | null;
  kind: string;
  shot_name: string;
  prompt_id: string | null;
  status: string;
  settings: string;
  output_path: string | null;
  render_seconds: number | null;
  transcript: string | null;
  starred: number;
  error: string | null;
  parent_take_id: number | null;
  organisation_id: string;
}

export const takes = {
  create(row: { project_id: number | null; kind: string; shot_name: string; settings: unknown; parent_take_id?: number }): number {
    const r = db
      .prepare('INSERT INTO takes (project_id, kind, shot_name, settings, parent_take_id, organisation_id) VALUES (?,?,?,?,?,?)')
      .run(row.project_id, row.kind, row.shot_name, JSON.stringify(row.settings), row.parent_take_id ?? null, orgEcrite());
    return Number(r.lastInsertRowid);
  },
  /*
   * 'stopped' (cancelled, cleared, removed) is terminal: the engine often
   * reports the dead job later (as canceled, expired or even succeeded), and
   * that late result must not relabel the take or bring it back to the Library.
   */
  setPrompt(id: number, promptId: string) {
    db.prepare("UPDATE takes SET prompt_id=?, status=CASE WHEN status='stopped' THEN status ELSE 'rendering' END WHERE id=?").run(promptId, id);
  },
  finish(id: number, outputPath: string, renderSeconds?: number) {
    db.prepare("UPDATE takes SET status='done', output_path=?, render_seconds=? WHERE id=? AND status<>'stopped'").run(outputPath, renderSeconds ?? null, id);
  },
  fail(id: number, error: string, stopped = false) {
    db.prepare("UPDATE takes SET status=?, error=? WHERE id=? AND status<>'stopped'").run(stopped ? 'stopped' : 'failed', error.slice(0, 500), id);
  },
  /** Replace a take's settings (a chained take learns its start frame late; the Director's scene cut keeps its shot list here). */
  setSettings(id: number, settings: unknown) {
    db.prepare('UPDATE takes SET settings=? WHERE id=?').run(JSON.stringify(settings), id);
  },
  /** Queued takes that never reached the engine: a chain a restart cut short. */
  orphans(): Take[] {
    return db.prepare("SELECT * FROM takes WHERE status='queued' AND prompt_id IS NULL").all() as Take[];
  },
  /** Merge fields into a take's settings JSON (measurements and outputs added after the render). */
  patchSettings(id: number, patch: Record<string, unknown>) {
    const row = db.prepare('SELECT settings FROM takes WHERE id=?').get(id) as { settings: string } | undefined;
    if (!row) return;
    db.prepare('UPDATE takes SET settings=? WHERE id=?').run(JSON.stringify({ ...JSON.parse(row.settings), ...patch }), id);
  },
  setTranscript(id: number, t: string) {
    db.prepare('UPDATE takes SET transcript=? WHERE id=?').run(t, id);
  },
  star(id: number, on: boolean) {
    const [w, a] = portee();
    db.prepare(`UPDATE takes SET starred=? WHERE id=?${w}`).run(on ? 1 : 0, id, ...a);
  },
  delete(id: number) {
    const [w, a] = portee();
    if (db.prepare(`DELETE FROM takes WHERE id=?${w}`).run(id, ...a).changes) {
      db.prepare('DELETE FROM take_workflows WHERE take_id=?').run(id);
    }
  },
  get(id: number): Take | undefined {
    const [w, a] = portee();
    return db.prepare(`SELECT * FROM takes WHERE id=?${w}`).get(id, ...a) as Take | undefined;
  },
  byPrompt(promptId: string): Take | undefined {
    const [w, a] = portee();
    return db.prepare(`SELECT * FROM takes WHERE prompt_id=?${w}`).get(promptId, ...a) as Take | undefined;
  },
  list(projectId: number | null, limit = 100): Take[] {
    const [w, a] = portee();
    return projectId === null
      ? (db.prepare(`SELECT * FROM takes WHERE 1=1${w} ORDER BY id DESC LIMIT ?`).all(...a, limit) as Take[])
      : (db.prepare(`SELECT * FROM takes WHERE project_id=?${w} ORDER BY id DESC LIMIT ?`).all(projectId, ...a, limit) as Take[]);
  },
  /** Failed films can retain reservations for suite plans that never became individual takes. */
  filmsAvecReservationsEnAttente(): Take[] {
    return selectionnerFilmsAvecReservationsEnAttente((sql) => db.prepare(sql).all() as Take[]);
  },
  /** Organisation propriétaire d'une prise, sans filtre (diffusion en direct, facturation). */
  organisationDe(id: number): string | undefined {
    return (db.prepare('SELECT organisation_id FROM takes WHERE id=?').get(id) as { organisation_id: string } | undefined)?.organisation_id;
  },
  active(): Take[] {
    return db.prepare("SELECT * FROM takes WHERE status IN ('queued','rendering') ORDER BY id").all() as Take[];
  },
};

/**
 * The ComfyUI graph behind each take, kept in its own table so the take list
 * stays small. Input files are named the way ComfyUI knows them, so the JSON
 * opens in ComfyUI without OpenField in the loop.
 */
export const takeWorkflows = {
  set(takeId: number, graph: Record<string, unknown>, source: 'engine' | 'submitted') {
    db.prepare(
      'INSERT INTO take_workflows (take_id, graph, source) VALUES (?,?,?) ON CONFLICT(take_id) DO UPDATE SET graph=excluded.graph, source=excluded.source'
    ).run(takeId, JSON.stringify(graph), source);
  },
  get(takeId: number): { graph: Record<string, unknown>; source: string } | undefined {
    const r = db.prepare('SELECT graph, source FROM take_workflows WHERE take_id=?').get(takeId) as any;
    return r ? { graph: JSON.parse(r.graph), source: r.source } : undefined;
  },
};

export type CastKind = 'character' | 'prop' | 'place';
/** One reference picture: the engine's input token plus our own copy on disk. */
export interface CastRef { token: string; file: string; w: number; h: number }
export interface CastMember { id: number; name: string; kind: CastKind; refs: CastRef[]; notes: string; created_at: string }

const castRow = (r: any): CastMember => ({ ...r, refs: JSON.parse(r.refs || '[]') });

/** Cast: characters, props and places, saved once and @mentioned in any prompt. */
export const cast = {
  list(): CastMember[] {
    const [w, a] = portee('WHERE');
    return (db.prepare(`SELECT * FROM cast${w} ORDER BY id`).all(...a) as any[]).map(castRow);
  },
  get(id: number): CastMember | undefined {
    const [w, a] = portee();
    const r = db.prepare(`SELECT * FROM cast WHERE id=?${w}`).get(id, ...a);
    return r ? castRow(r) : undefined;
  },
  byName(name: string): CastMember | undefined {
    const [w, a] = portee();
    const r = db.prepare(`SELECT * FROM cast WHERE name=?${w}`).get(name, ...a);
    return r ? castRow(r) : undefined;
  },
  create(row: { name: string; kind: CastKind; refs: CastRef[]; notes: string }): number {
    const r = db.prepare('INSERT INTO cast (name, kind, refs, notes, organisation_id) VALUES (?,?,?,?,?)')
      .run(row.name, row.kind, JSON.stringify(row.refs), row.notes, orgEcrite());
    return Number(r.lastInsertRowid);
  },
  update(id: number, patch: Partial<{ name: string; kind: CastKind; refs: CastRef[]; notes: string }>) {
    const cur = cast.get(id);
    if (!cur) return;
    // cast.get a déjà vérifié l'organisation.
    db.prepare('UPDATE cast SET name=?, kind=?, refs=?, notes=? WHERE id=?').run(
      patch.name ?? cur.name, patch.kind ?? cur.kind, JSON.stringify(patch.refs ?? cur.refs), patch.notes ?? cur.notes, id,
    );
  },
  delete(id: number) {
    const [w, a] = portee();
    db.prepare(`DELETE FROM cast WHERE id=?${w}`).run(id, ...a);
  },
};

export const projects = {
  list() {
    const [w, a] = portee('WHERE');
    return db.prepare(`SELECT * FROM projects${w} ORDER BY last_used DESC`).all(...a);
  },
  create(name: string, folder: string): number {
    const r = db.prepare('INSERT INTO projects (name, folder, organisation_id) VALUES (?,?,?)').run(name, folder, orgEcrite());
    return Number(r.lastInsertRowid);
  },
  touch(id: number) {
    db.prepare("UPDATE projects SET last_used=datetime('now') WHERE id=?").run(id);
  },
  get(id: number): { id: number; name: string; folder: string } | undefined {
    const [w, a] = portee();
    return db.prepare(`SELECT * FROM projects WHERE id=?${w}`).get(id, ...a) as any;
  },
};

export const speed = {
  get(key: string): number | undefined {
    const r = db.prepare('SELECT seconds_per_step FROM speed WHERE key=?').get(key) as any;
    return r?.seconds_per_step;
  },
  set(key: string, secondsPerStep: number) {
    db.prepare(
      'INSERT INTO speed (key, seconds_per_step) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET seconds_per_step=excluded.seconds_per_step'
    ).run(key, secondsPerStep);
  },
};

/**
 * Style preambles — text prepended to every prompt, so a house look does not
 * have to be retyped per shot.
 *
 * These ship as starting points, not as law: they are ordinary rows, editable
 * and deletable in the UI. The seed runs once and records that it ran, so a
 * preamble you delete stays deleted instead of reappearing on next boot.
 */
const SEED_PREAMBLES: { name: string; text: string }[] = [
  {
    name: 'Cel anime',
    text:
      '1990s hand-drawn cel anime, imperfect paint edges, 16mm film grain, graphite underdrawing visible, ' +
      'limited palette, no modern anime gloss, no speed lines. Held stillness with precise small motion.',
  },
  {
    name: 'Cinematic dark',
    text:
      'Cinematic, high contrast, deep blacks and negative space, luminous highlights in a dark environment, ' +
      'volumetric light, dense evolving texture, a witnessed camera that holds and breathes.',
  },
];

export interface Preamble {
  id: number;
  name: string;
  text: string;
  sort: number;
}

export const preambles = {
  list(): Preamble[] {
    return db.prepare('SELECT * FROM preambles ORDER BY sort, id').all() as Preamble[];
  },
  get(id: number): Preamble | undefined {
    return db.prepare('SELECT * FROM preambles WHERE id=?').get(id) as Preamble | undefined;
  },
  create(name: string, text: string): number {
    const sort = (db.prepare('SELECT COALESCE(MAX(sort),0)+1 AS n FROM preambles').get() as any).n;
    const r = db.prepare('INSERT INTO preambles (name, text, sort) VALUES (?,?,?)').run(name, text, sort);
    return Number(r.lastInsertRowid);
  },
  update(id: number, patch: { name?: string; text?: string }) {
    const cur = preambles.get(id);
    if (!cur) return;
    db.prepare('UPDATE preambles SET name=?, text=? WHERE id=?')
      .run(patch.name ?? cur.name, patch.text ?? cur.text, id);
  },
  delete(id: number) {
    db.prepare('DELETE FROM preambles WHERE id=?').run(id);
  },
  /** Insert the starters exactly once in the lifetime of a database. */
  seedOnce() {
    const done = db.prepare("SELECT value FROM meta WHERE key='preambles_seeded'").get() as any;
    if (done) return;
    const insert = db.prepare('INSERT OR IGNORE INTO preambles (name, text, sort) VALUES (?,?,?)');
    SEED_PREAMBLES.forEach((p, i) => insert.run(p.name, p.text, i));
    db.prepare("INSERT INTO meta (key, value) VALUES ('preambles_seeded','1')").run();
  },
};

preambles.seedOnce();

/** Small machine-wide settings (the render size, ...), shared by every browser and the MCP server. */
export const meta = {
  get(key: string): string | undefined {
    return (db.prepare('SELECT value FROM meta WHERE key=?').get(key) as { value: string } | undefined)?.value;
  },
  set(key: string, value: string) {
    db.prepare('INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value').run(key, value);
  },
  delete(key: string) {
    db.prepare('DELETE FROM meta WHERE key=?').run(key);
  },
};

/**
 * Nexora : conversations de l'agent Producteur (server/nexora/agent.ts), une ligne par conversation, l'état en JSON.
 * Isolées par organisation comme les prises ; la file des rendus reste la table `takes` (l'agent n'y écrit que par les
 * routes ordinaires du studio).
 */
db.exec(`
CREATE TABLE IF NOT EXISTS producteur_sessions (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL DEFAULT 'local',
  titre TEXT NOT NULL,
  data TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS producteur_sessions_org ON producteur_sessions (organisation_id, updated_at);
`);

export const sessionsProducteur = {
  get<T>(id: string): T | undefined {
    const [w, a] = portee();
    const r = db.prepare(`SELECT data FROM producteur_sessions WHERE id=?${w}`).get(id, ...a) as { data: string } | undefined;
    return r ? (JSON.parse(r.data) as T) : undefined;
  },
  save(s: { id: string; titre: string }): void {
    const [w, a] = portee();
    const existe = db.prepare('SELECT organisation_id FROM producteur_sessions WHERE id=?').get(s.id) as { organisation_id: string } | undefined;
    if (existe) {
      db.prepare(`UPDATE producteur_sessions SET titre=?, data=?, updated_at=datetime('now') WHERE id=?${w}`).run(s.titre.slice(0, 120), JSON.stringify(s), s.id, ...a);
    } else {
      db.prepare('INSERT INTO producteur_sessions (id, organisation_id, titre, data) VALUES (?,?,?,?)').run(s.id, orgEcrite(), s.titre.slice(0, 120), JSON.stringify(s));
    }
  },
  list(limit = 30): { id: string; titre: string; updated_at: string }[] {
    const [w, a] = portee('WHERE');
    return db.prepare(`SELECT id, titre, updated_at FROM producteur_sessions${w} ORDER BY updated_at DESC LIMIT ?`).all(...a, limit) as any[];
  },
  delete(id: string): void {
    const [w, a] = portee();
    db.prepare(`DELETE FROM producteur_sessions WHERE id=?${w}`).run(id, ...a);
  },
};

/**
 * Projets longs (server/nexora/projet.ts) : scénario, bible, arbre séquences → scènes → plans et état de tournage,
 * une ligne par projet (JSON), isolée par organisation. Aucune limite de taille codée au-delà de celle de SQLite.
 */
db.exec(`
CREATE TABLE IF NOT EXISTS projets_longs (
  id TEXT PRIMARY KEY,
  organisation_id TEXT NOT NULL DEFAULT 'local',
  titre TEXT NOT NULL,
  data TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS projets_longs_org ON projets_longs (organisation_id, updated_at);
`);

export const projetsLongs = {
  get<T>(id: string): T | undefined {
    const [w, a] = portee();
    const r = db.prepare(`SELECT data FROM projets_longs WHERE id=?${w}`).get(id, ...a) as { data: string } | undefined;
    return r ? (JSON.parse(r.data) as T) : undefined;
  },
  save(s: { id: string; titre: string }): void {
    const [w, a] = portee();
    const existe = db.prepare('SELECT organisation_id FROM projets_longs WHERE id=?').get(s.id) as { organisation_id: string } | undefined;
    if (existe) db.prepare(`UPDATE projets_longs SET titre=?, data=?, updated_at=datetime('now') WHERE id=?${w}`).run(s.titre.slice(0, 120), JSON.stringify(s), s.id, ...a);
    else db.prepare('INSERT INTO projets_longs (id, organisation_id, titre, data) VALUES (?,?,?,?)').run(s.id, orgEcrite(), s.titre.slice(0, 120), JSON.stringify(s));
  },
  list<T>(limit = 100): T[] {
    const [w, a] = portee('WHERE');
    return (db.prepare(`SELECT data FROM projets_longs${w} ORDER BY updated_at DESC LIMIT ?`).all(...a, limit) as { data: string }[]).map((r) => JSON.parse(r.data) as T);
  },
  delete(id: string): void {
    const [w, a] = portee();
    db.prepare(`DELETE FROM projets_longs WHERE id=?${w}`).run(id, ...a);
  },
};
