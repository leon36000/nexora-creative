#!/usr/bin/env python3
"""Build or validate a single-team montage from portable, hash-pinned assets."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

TEAM_RE = {'muse', 'opus', 'gemini', 'deepseek'}
TEAM_STATUS = 'incomplete-review-draft'
STATUS_FILE = 'status.json'
LANGUAGES = ('fr', 'en')
FORMATS = ('16x9', '9x16')
HEX64_RE = re.compile(r'^[0-9a-fA-F]{64}$')


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def require_number(value, label, *, minimum=None, positive=False):
    if not _is_number(value):
        raise ValueError(f'{label}: nombre attendu (booléens refusés), reçu {type(value).__name__}')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{label}: valeur non finie (NaN/Inf) refusée')
    if positive and value <= 0:
        raise ValueError(f'{label}: valeur strictement positive attendue, reçu {value}')
    if minimum is not None and value < minimum:
        raise ValueError(f'{label}: valeur >= {minimum} attendue, reçu {value}')
    return value


def require_sha256(value, label):
    if not isinstance(value, str) or not HEX64_RE.match(value):
        raise ValueError(f'{label}: SHA256 hex de 64 caractères attendu')
    return value.lower()


def require_relative_path(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label}: chemin relatif non vide attendu')
    rel = Path(value)
    if '\\' in value or rel.is_absolute() or not rel.parts or any(p in ('..', '.', '') for p in value.split('/')):
        raise ValueError(f'{label}: chemin relatif sans traversal attendu: {value!r}')
    return value


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def portable_asset(root, relative, expected_sha):
    rel = Path(require_relative_path(relative, 'asset path'))
    if rel.is_absolute() or not rel.parts or '..' in rel.parts:
        raise ValueError(f'asset path must be relative and traversal-free: {relative}')
    root = Path(root).resolve(strict=True)
    candidate = root / rel
    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f'symlink asset refused: {relative}')
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f'asset escaped its root: {relative}') from exc
    if not resolved.is_file() or sha_file(resolved) != require_sha256(expected_sha, 'asset sha256'):
        raise ValueError(f'missing asset or SHA mismatch: {relative}')
    return resolved


def _validate_crop(crop, where):
    if not isinstance(crop, list) or not crop:
        raise ValueError(f'{where}.crop_9x16: liste de clés attendue')
    previous = -1.0
    for key in crop:
        if not isinstance(key, list) or len(key) != 4:
            raise ValueError(f'{where}.crop_9x16: clés [t, x, y, zoom] attendues')
        t, x, y, zoom = [require_number(v, f'{where}.crop_9x16') for v in key]
        if t < 0 or t <= previous or not (0 <= x <= 1 and 0 <= y <= 1) or zoom <= 0:
            raise ValueError(f'{where}.crop_9x16: clés invalides')
        previous = t


def _validate_segment(segment, index, team):
    where = f'segments[{index}]'
    if not isinstance(segment, dict):
        raise ValueError(f'{where}: objet JSON attendu')
    require_relative_path(segment.get('source'), f'{where}.source')
    require_sha256(segment.get('sha256'), f'{where}.sha256')
    root = segment.get('source_root')
    if root not in ('ui', 'h3'):
        raise ValueError(f"{where}.source_root: 'ui' ou 'h3' attendu, reçu {root!r}")
    require_number(segment.get('start_s'), f'{where}.start_s', minimum=0)
    require_number(segment.get('duration_s'), f'{where}.duration_s', positive=True)
    if 'entry_s' in segment:
        require_number(segment['entry_s'], f'{where}.entry_s', minimum=0)
    if 'sound_db' in segment:
        require_number(segment['sound_db'], f'{where}.sound_db')
    if 'grade' in segment and not isinstance(segment['grade'], str):
        raise ValueError(f'{where}.grade: chaîne attendue')
    if 'crop_9x16' in segment:
        _validate_crop(segment['crop_9x16'], where)
    if root == 'h3' and team not in Path(segment['source']).name:
        raise ValueError(f'{where}.source: le clip H3 doit nommer l\'équipe {team}')


def _load_manifest_doc(manifest_path):
    raw = Path(manifest_path).read_bytes()
    try:
        doc = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'invalid JSON manifest: {exc}') from exc
    if not isinstance(doc, dict):
        raise ValueError('manifest: top-level object expected')
    schema = doc.get('schema')
    if not _is_number(schema) or schema != 1:
        raise ValueError('manifest: schema must be the number 1')
    return raw, doc


def _select_team_doc(doc, team):
    teams = doc.get('teams', {})
    if not isinstance(teams, dict):
        raise ValueError('manifest: teams must be an object')
    selected = teams.get(team)
    if not isinstance(selected, dict):
        raise ValueError(f'manifest: team {team!r} absent or not an object')
    if selected.get('status') != TEAM_STATUS:
        raise ValueError(f'{team}: status must be {TEAM_STATUS!r}, got {selected.get("status")!r}')
    return selected


def _check_team_optional_fields(selected, team):
    if 'language' in selected and selected['language'] not in LANGUAGES:
        raise ValueError(f'{team}.language: one of {LANGUAGES} expected, got {selected["language"]!r}')
    if 'format' in selected and selected['format'] not in FORMATS:
        raise ValueError(f'{team}.format: one of {FORMATS} expected, got {selected["format"]!r}')
    if 'notes' in selected and not (isinstance(selected['notes'], list)
                                    and all(isinstance(n, str) for n in selected['notes'])):
        raise ValueError(f'{team}.notes: list of strings expected')
    if 'overlays' in selected and not isinstance(selected['overlays'], list):
        raise ValueError(f'{team}.overlays: list expected')


def _contiguity_cursor(selected, team):
    segments = selected.get('segments')
    if not isinstance(segments, list) or not segments:
        raise ValueError(f'{team}: segment list must be a non-empty list')
    for index, segment in enumerate(segments):
        _validate_segment(segment, index, team)
    ordered = sorted(segments, key=lambda s: float(s['start_s']))
    cursor = 0.0
    for segment in ordered:
        start = float(segment['start_s'])
        seg_duration = float(segment['duration_s'])
        if not math.isclose(start, cursor, abs_tol=1e-9):
            raise ValueError(f'segments must be contiguous: expected start {cursor}, got {start}')
        if not math.isclose(seg_duration * 24, round(seg_duration * 24), abs_tol=1e-7):
            raise ValueError('segment duration is not on the 24 fps frame grid')
        cursor = start + seg_duration
    return ordered, cursor


def load_team(manifest_path, team):
    if team not in TEAM_RE:
        raise ValueError(f'unknown team {team!r}; expected one of {sorted(TEAM_RE)}')
    raw, doc = _load_manifest_doc(manifest_path)
    selected = _select_team_doc(doc, team)
    duration = require_number(selected.get('duration_s'), f'{team}.duration_s', positive=True)
    _check_team_optional_fields(selected, team)
    ordered, cursor = _contiguity_cursor(selected, team)
    if not math.isclose(cursor, duration, abs_tol=1e-9):
        raise ValueError(f'segment total {cursor} differs from declared duration {duration}')
    return raw, doc, selected, ordered


def compile_montage(team_doc, team, args, ui_root, h3_root, brand_file):
    segments = []
    resolved_sources = []
    for source in sorted(team_doc['segments'], key=lambda item: item['start_s']):
        if source['source_root'] == 'ui':
            root = ui_root
        elif source['source_root'] == 'h3':
            root = h3_root
        else:
            raise ValueError(f"unknown source root: {source['source_root']}")
        path = portable_asset(root, source['source'], source['sha256'])
        if source['source_root'] == 'h3' and team not in path.name:
            raise ValueError(f'H3 source does not identify team {team}: {path.name}')
        item = {
            'type': 'plan', 'debut': float(source['start_s']), 'duree': float(source['duration_s']),
            'fichier': str(path), 'entree': float(source.get('entry_s', 0)),
            'etalonnage': source.get('grade', 'neutre'), 'son_db': float(source.get('sound_db', 0)),
        }
        if args.format == '9x16' and 'crop_9x16' in source:
            item['cadrage_v'] = source['crop_9x16']
        segments.append(item)
        resolved_sources.append({'path': str(path), 'sha256': require_sha256(source['sha256'], 'asset sha256'),
                                 'bytes': path.stat().st_size, 'kind': source['source_root']})
    montage = {
        'marque': str(brand_file), 'bpm': 120, 'phase': 0,
        'duree': float(team_doc['duration_s']), 'voix': [], 'musique': None, 'sfx': [],
        'textes': team_doc.get('overlays', []), 'segments': segments,
    }
    return montage, resolved_sources


def validate_with_engine(repo_root, montage_path, cache_dir, language, home):
    engine = Path(repo_root) / 'marketing/creative/video-v7/monter_v6.py'
    if not engine.is_file():
        raise ValueError(f'monter_v6.py not found under supplied repo root: {engine}')
    engine_dir = str(engine.parent)
    old_path = list(sys.path)
    old_bytecode = sys.dont_write_bytecode
    old_home, old_cache = os.environ.get('HOME'), os.environ.get('V6_CACHE')
    try:
        if engine_dir not in sys.path:
            sys.path.insert(0, engine_dir)
        os.environ['V6_CACHE'] = str(cache_dir)
        os.environ['HOME'] = str(home)
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('v7_portable_monter_v6', engine)
        if spec is None or spec.loader is None:
            raise ValueError('could not load the supplied montage engine')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.charger(montage_path, language, tolerant=False)
    finally:
        sys.path[:] = old_path
        sys.dont_write_bytecode = old_bytecode
        for key, previous in (('HOME', old_home), ('V6_CACHE', old_cache)):
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
    return engine


def _render(args, run_id, cache_dir, run_dir, repo_root, engine, montage_path):
    output = cache_dir / f'{args.team}-{run_id}.mp4'
    if output.exists():
        raise FileExistsError(f'refusing to overwrite {output}')
    env = {'HOME': str(args.home.resolve()), 'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'V6_CACHE': str(cache_dir)}
    if args.ffmpeg:
        env['V6_FFMPEG'] = str(args.ffmpeg.resolve(strict=True))
    if args.ffprobe:
        env['V6_FFPROBE'] = str(args.ffprobe.resolve(strict=True))
    command = [sys.executable, '-B', str(engine), str(montage_path), '--format', args.format,
               '--langue', args.language, '--sortie', str(output), '--master', 'web', '--jobs', str(args.jobs), '--brouillon']
    result = subprocess.run(command, cwd=repo_root, env=env, capture_output=True, text=True)
    write_new(run_dir / 'render.stdout.txt', result.stdout.encode())
    write_new(run_dir / 'render.stderr.txt', result.stderr.encode())
    if result.returncode != 0 or not output.is_file():
        status = {'status': 'render-failed-preserved', 'return_code': result.returncode,
                  'output_path': str(output), 'run_dir': str(run_dir)}
    else:
        status = {'status': 'draft-rendered-preserved', 'return_code': 0,
                  'output_path': str(output), 'output_bytes': output.stat().st_size,
                  'output_sha256': sha_file(output), 'run_dir': str(run_dir)}
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path, help='portable JSON manifest')
    parser.add_argument('--team', required=True, choices=sorted(TEAM_RE))
    parser.add_argument('--repo-root', required=True, type=Path, help='checkout root containing video-v7/monter_v6.py')
    parser.add_argument('--ui-root', required=True, type=Path, help='root for relative UI capture clips')
    parser.add_argument('--h3-root', required=True, type=Path, help='root for relative H3 video clips')
    parser.add_argument('--brand-file', required=True, type=Path, help='runtime brand JSON; not embedded in the portable manifest')
    parser.add_argument('--output-root', required=True, type=Path, help='new run directories are created here')
    parser.add_argument('--language', choices=('fr', 'en'), default=None)
    parser.add_argument('--format', choices=('16x9', '9x16'), default=None)
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--render', action='store_true', help='render a CPU draft after validation; default is validation only')
    parser.add_argument('--ffmpeg', type=Path, help='optional explicit ffmpeg executable')
    parser.add_argument('--ffprobe', type=Path, help='optional explicit ffprobe executable')
    parser.add_argument('--home', type=Path, required=True, help='explicit runtime home used for brand font expansion')
    args = parser.parse_args()
    if args.jobs < 1:
        raise ValueError('--jobs must be positive')

    raw, _, team_doc, _ = load_team(args.manifest, args.team)
    language = args.language or team_doc.get('language', 'fr')
    format_name = args.format or team_doc.get('format', '16x9')
    if language not in LANGUAGES or format_name not in FORMATS:
        raise ValueError(f'language ({language!r}) or format ({format_name!r}) not supported')
    args.format = format_name
    args.language = language
    repo_root = args.repo_root.resolve(strict=True)
    ui_root = args.ui_root.resolve(strict=True)
    h3_root = args.h3_root.resolve(strict=True)
    if args.brand_file.is_symlink():
        raise ValueError('brand file must not be a symlink')
    brand_file = args.brand_file.resolve(strict=True)
    if not brand_file.is_file():
        raise ValueError('brand file must be a regular file')

    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_id = uuid.uuid4().hex
    run_dir = output_root / f'{args.team}-{stamp}-{run_id}'
    run_dir.mkdir(exist_ok=False)
    phase = 'preparation'
    try:
        cache_dir = run_dir / 'cache'
        cache_dir.mkdir(exist_ok=False)

        montage, sources = compile_montage(team_doc, args.team, args, ui_root, h3_root, brand_file)
        montage_bytes = (json.dumps(montage, ensure_ascii=False, indent=2) + '\n').encode()
        montage_path = run_dir / 'montage.json'
        write_new(montage_path, montage_bytes)
        provenance = {
            'created_utc': datetime.now(timezone.utc).isoformat(), 'team': args.team,
            'status': team_doc['status'], 'language': language, 'format': format_name,
            'fps': 24, 'duration_s': team_doc['duration_s'],
            'manifest_sha256': sha_bytes(raw), 'montage_sha256': sha_bytes(montage_bytes),
            'brand_sha256': sha_file(brand_file),
            'engine_sha256': sha_file(repo_root / 'marketing/creative/video-v7/monter_v6.py'), 'sources': sources,
            'notes': team_doc.get('notes', []), 'voice': 'none', 'music': 'none',
            'human_judgment': 'not performed', 'causal_link_ui_to_h3': 'unverified',
            'render_requested': bool(args.render), 'run_id': run_id,
        }
        write_new(run_dir / 'provenance.json', json.dumps(provenance, ensure_ascii=False, indent=2).encode())
        phase = 'validation'
        try:
            engine = validate_with_engine(repo_root, montage_path, cache_dir, language, args.home.resolve())
        except Exception as error:
            failure = {'status': 'validation-failed-preserved', 'error_type': type(error).__name__,
                       'error': str(error), 'run_dir': str(run_dir)}
            encoded_failure = json.dumps(failure, ensure_ascii=False, indent=2).encode()
            write_new(run_dir / 'validation-error.json', encoded_failure)
            write_new(run_dir / STATUS_FILE, encoded_failure)
            raise

        status = {'status': 'validated-not-rendered', 'engine': str(engine), 'run_dir': str(run_dir)}
        if args.render:
            phase = 'render'
            status = _render(args, run_id, cache_dir, run_dir, repo_root, engine, montage_path)
        write_new(run_dir / STATUS_FILE, json.dumps(status, ensure_ascii=False, indent=2).encode())
        print(json.dumps(status, ensure_ascii=False, indent=2))
        if status['status'] == 'render-failed-preserved':
            raise RuntimeError('render failed; details preserved in status.json')
    except Exception as error:
        # Le disque peut lui-même être inaccessible ; ne jamais écraser un statut déjà écrit.
        if not (run_dir / STATUS_FILE).exists():
            failure = {'status': 'failed-preserved', 'phase': phase,
                       'error_type': type(error).__name__, 'error': str(error), 'run_dir': str(run_dir)}
            write_new(run_dir / STATUS_FILE, json.dumps(failure, ensure_ascii=False, indent=2).encode())
        raise


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'ERREUR: {error}', file=sys.stderr)
        raise SystemExit(1)
