import { existsSync, lstatSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, isAbsolute, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const codeRoot = dirname(fileURLToPath(import.meta.url));
function requiredPath(name) {
  const value = process.env[name];
  if (!value || !isAbsolute(value)) throw new Error(`Required absolute path env ${name} is missing.`);
  return resolve(value);
}
function firstSymlink(value) {
  const path = resolve(value);
  let current = sep;
  for (const part of path.split(sep).filter(Boolean)) {
    current = current === sep ? `${current}${part}` : `${current}${sep}${part}`;
    try { if (lstatSync(current).isSymbolicLink()) return current; }
    catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  }
  return null;
}
function isGitMarker(marker) {
  try {
    const st = lstatSync(marker);
    if (st.isDirectory()) return existsSync(resolve(marker, 'HEAD'));
    if (!st.isFile()) return false;
    const line = readFileSync(marker, 'utf8').split(/\r?\n/, 1)[0].trim();
    if (!line.toLowerCase().startsWith('gitdir:')) return false;
    const raw = line.slice(line.indexOf(':') + 1).trim();
    const target = isAbsolute(raw) ? resolve(raw) : resolve(dirname(marker), raw);
    if (firstSymlink(target)) return false;
    return existsSync(resolve(target, 'HEAD'));
  } catch (error) { if (error.code === 'ENOENT') return false; throw error; }
}
function gitRootAncestor(value) {
  let current = resolve(value);
  try { if (lstatSync(current).isFile()) current = dirname(current); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  while (true) {
    if (isGitMarker(resolve(current, '.git'))) return current;
    const parent = resolve(current, '..');
    if (parent === current) return null;
    current = parent;
  }
}
export const assetRoot = requiredPath('MESH_ORACLE_ASSET_ROOT');
export const runRoot = requiredPath('MESH_ORACLE_RUN_DIR');
const storage = process.env.MESH_ORACLE_STORAGE_ROOT || '/media/pc6/Storage/Nexora/travail';
if (!runRoot.startsWith(storage + sep)) throw new Error(`Run output must be under ${storage}: ${runRoot}`);
for (const [label, path] of [['asset root', assetRoot], ['run root', runRoot]]) {
  const link = firstSymlink(path);
  if (link) throw new Error(`${label} has symlink path component: ${link}`);
}
if (gitRootAncestor(runRoot)) throw new Error(`Run output cannot be inside a Git worktree/repository: ${gitRootAncestor(runRoot)}`);
if (runRoot.split(sep).some((part) => part.toLowerCase() === 'comfyui')) throw new Error(`Run output cannot be in ComfyUI: ${runRoot}`);
if (runRoot === codeRoot || runRoot.startsWith(codeRoot + sep) || codeRoot.startsWith(runRoot + sep)) throw new Error('Run output and source-code package must remain separate.');
if (runRoot === assetRoot || runRoot.startsWith(assetRoot + sep) || assetRoot.startsWith(runRoot + sep)) throw new Error('Run output and input assets must remain separate.');
if (!existsSync(assetRoot) || !lstatSync(assetRoot).isDirectory()) throw new Error(`Asset root missing: ${assetRoot}`);
if (!existsSync(runRoot) || !lstatSync(runRoot).isDirectory()) throw new Error(`Run directory must exist; verify it is empty before generation: ${runRoot}`);
const packageJson = process.env.MESH_NODE_PACKAGE_JSON;
if (!packageJson || !isAbsolute(packageJson) || !existsSync(packageJson)) throw new Error('Set MESH_NODE_PACKAGE_JSON to the existing dependency package.json; no installation is performed.');
export const nodeRequire = createRequire(resolve(packageJson));
