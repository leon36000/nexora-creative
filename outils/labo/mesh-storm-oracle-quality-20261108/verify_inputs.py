#!/usr/bin/env python3
"""Verify locked assets and a separate empty Storage run without following symlinks."""
from __future__ import annotations
import argparse, hashlib, json, os, stat, sys
from pathlib import Path

STORAGE_ROOT = Path(os.environ.get('MESH_ORACLE_STORAGE_ROOT', '/media/pc6/Storage/Nexora/travail'))

def symlink_component(path: Path) -> Path | None:
    """Return the first symlink in the lexical absolute path, if any."""
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(mode):
            return current
    return None

def _git_marker(marker: Path) -> bool:
    try:
        mode = marker.lstat().st_mode
    except FileNotFoundError:
        return False
    if stat.S_ISDIR(mode):
        head = marker / 'HEAD'
        return head.is_file() and not head.is_symlink()
    if stat.S_ISREG(mode):
        try:
            first = marker.read_text(encoding='utf-8', errors='replace').splitlines()[0].strip()
        except (OSError, IndexError):
            return False
        if not first.lower().startswith('gitdir:'):
            return False
        target = Path(first.split(':', 1)[1].strip())
        if not target.is_absolute():
            target = marker.parent / target
        if symlink_component(target):
            return False
        head = target / 'HEAD'
        return head.is_file() and not head.is_symlink()
    return False

def git_root_ancestor(path: Path) -> Path | None:
    p = Path(os.path.abspath(path))
    if p.exists() and p.is_file():
        p = p.parent
    for ancestor in (p, *p.parents):
        if _git_marker(ancestor / '.git'):
            return ancestor
    return None

def validate_layout(assets_root: Path, run_dir: Path, code_dir: Path, storage_root: Path = STORAGE_ROOT) -> tuple[Path, Path]:
    assets_root = Path(assets_root)
    run_dir = Path(run_dir)
    code_dir = Path(code_dir)
    storage_root = Path(storage_root)
    for label, path in [('asset root', assets_root), ('run dir', run_dir), ('storage root', storage_root)]:
        if not path.is_absolute():
            raise ValueError(f'{label} must be absolute: {path}')
        link = symlink_component(path)
        if link:
            raise ValueError(f'{label} has symlink component: {link}')
    if not storage_root.is_dir():
        raise ValueError(f'Storage root is absent: {storage_root}')
    if not assets_root.is_dir():
        raise ValueError(f'asset root is absent or not a directory: {assets_root}')
    if not run_dir.is_dir():
        raise ValueError(f'run dir must already exist as an empty directory: {run_dir}')
    if any(run_dir.iterdir()):
        raise ValueError(f'run dir must be empty: {run_dir}')
    assets = assets_root.resolve(strict=True)
    run = run_dir.resolve(strict=True)
    code = code_dir.resolve(strict=True)
    storage = storage_root.resolve(strict=True)
    if storage not in run.parents:
        raise ValueError(f'run dir must be under {storage}: {run}')
    if git_root_ancestor(run):
        raise ValueError(f'run dir is inside a Git worktree/repository: {git_root_ancestor(run)}')
    if any(part.lower() == 'comfyui' for part in run.parts):
        raise ValueError(f'run dir cannot be under ComfyUI: {run}')
    if run == assets or run in assets.parents or assets in run.parents:
        raise ValueError(f'assets and run must be separate paths: assets={assets} run={run}')
    if run == code or run in code.parents or code in run.parents:
        raise ValueError(f'code and run must be separate paths: code={code} run={run}')
    return assets, run

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def verify_entry(item: dict, path: Path) -> str:
    link = symlink_component(path)
    if link:
        raise ValueError(f"lien symbolique dans l’entrée {item['role']}: {link}")
    if not path.is_file():
        raise ValueError(f"entrée requise introuvable: {item['role']} -> {path}")
    size, sha = path.stat().st_size, digest(path)
    if size != item['bytes'] or sha != item['sha256']:
        raise ValueError(f"taille/SHA différents pour {item['role']}: {path}; bytes={size}; sha256={sha}")
    return sha

def validate_stage_name(name: str, stage_dir: Path) -> Path:
    import re
    if not isinstance(name, str) or not name or '\x00' in name or '/' in name or '\\' in name:
        raise ValueError('stage name must be a plain basename without separators')
    if Path(name).is_absolute() or Path(name).name != name or name in ('.', '..'):
        raise ValueError('absolute or traversal stage name refused')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.(?:usda|usdz)', name):
        raise ValueError('stage must have a unique basename ending in .usda or .usdz')
    root = Path(stage_dir)
    link = symlink_component(root)
    if link:
        raise ValueError(f'stage directory has symlink component: {link}')
    if not root.is_dir():
        raise ValueError(f'stage directory absent: {root}')
    path = root / name
    link = symlink_component(path)
    if link:
        raise ValueError(f'stage file has symlink component: {link}')
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        raise ValueError(f'stage file absent: {path}')
    if not stat.S_ISREG(mode):
        raise ValueError(f'stage file must be a regular non-symlink file: {path}')
    return path.resolve(strict=True)

def validate_renderer_paths(run_dir: Path, stage_dir: Path, output_dir: Path, code_dir: Path, storage_root: Path) -> tuple[Path, Path, Path, Path]:
    run_dir, stage_dir, output_dir, code_dir, storage_root = map(Path, (run_dir, stage_dir, output_dir, code_dir, storage_root))
    for label, path in [('run', run_dir), ('stage', stage_dir), ('output', output_dir), ('storage root', storage_root)]:
        if not path.is_absolute():
            raise ValueError(f'{label} must be absolute: {path}')
        link = symlink_component(path)
        if link:
            raise ValueError(f'{label} has symlink component: {link}')
    if not storage_root.is_dir() or not run_dir.is_dir() or not stage_dir.is_dir():
        raise ValueError('storage root, run and stage must already be directories')
    run = run_dir.resolve(strict=True)
    stage = stage_dir.resolve(strict=True)
    output = output_dir.resolve(strict=False)
    code = code_dir.resolve(strict=True)
    storage = storage_root.resolve(strict=True)
    if storage not in run.parents or git_root_ancestor(run):
        raise ValueError('run must be under the selected storage root and outside a real Git repository/worktree')
    if any(part.lower() == 'comfyui' for part in run.parts):
        raise ValueError('run cannot be under ComfyUI')
    if code == run or code in run.parents or run in code.parents:
        raise ValueError('source code and run must be separate')
    if run not in stage.parents or run not in output.parents or stage == output or stage in output.parents or output in stage.parents:
        raise ValueError('stage and output must be separate children of the run')
    if output.exists() and not output.is_dir():
        raise ValueError('output path exists as a non-directory')
    return run, stage, output, storage

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--assets-root', required=True)
    ap.add_argument('--run-dir', required=True)
    ap.add_argument('--manifest', default=str(Path(__file__).with_name('inputs.json')))
    ap.add_argument('--input', action='append', default=[], metavar='ROLE=PATH')
    ns = ap.parse_args()
    try:
        root, run = validate_layout(Path(ns.assets_root), Path(ns.run_dir), Path(__file__).resolve().parent)
    except ValueError as e:
        print(f'REFUS: {e}', file=sys.stderr)
        return 2
    overrides = {}
    for pair in ns.input:
        if '=' not in pair:
            print(f'REFUS: override invalide: {pair}', file=sys.stderr)
            return 2
        key, value = pair.split('=', 1)
        path = Path(value)
        if not path.is_absolute():
            print(f'REFUS: chemin d’override non absolu: {value}', file=sys.stderr)
            return 2
        overrides[key] = path
    try:
        manifest = json.loads(Path(ns.manifest).read_text(encoding='utf-8'))
    except Exception as e:
        print(f'REFUS: manifeste absent/illisible: {ns.manifest}: {e}', file=sys.stderr)
        return 2
    bad = False
    for item in manifest.get('inputs', []):
        if not item.get('required', True):
            continue
        path = overrides.get(item['role'])
        if path is None:
            path = Path(item['path']) if item.get('path') else root / item['relative_path']
        try:
            sha = verify_entry(item, path)
            size = path.stat().st_size
        except ValueError as e:
            print(f'REFUS: {e}', file=sys.stderr)
            bad = True
            continue
        print(f"OK: {item['role']} bytes={size} sha256={sha} path={path}")
    if bad:
        return 3
    print(f'OK: {len(manifest.get("inputs", []))} entrées vérifiées; run vide validé: {run}; aucun asset copié.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
