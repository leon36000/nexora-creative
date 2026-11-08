#!/usr/bin/env python3
"""Rejeu borné d'un essai Paint ; aucune activation produit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import gpu_guard
from verify_manifest import verify

CODE = Path(__file__).resolve().parent
PYTHON_EXECUTABLE = 'venv/bin/python'
MINIMAL_PATH = '/usr/bin:/bin'


def safe_name(value):
    if not value or len(value) > 48 or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in value):
        raise ValueError('run id must contain lowercase letters, digits or hyphens')
    return value


def smi(query):
    result = subprocess.run(['nvidia-smi', query, '--format=csv,noheader,nounits'],
                            capture_output=True, text=True, check=True, timeout=5)
    return result.stdout.strip()


def pids():
    return gpu_guard.parse_pids(smi('--query-compute-apps=pid'))


def ram_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    raise RuntimeError('MemAvailable unavailable')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def supervise_and_check(cmd, run, fd, read_fd, write_fd, controle, supervision, record):
    try:
        result = supervision.superviser(cmd, run, fd, read_fd, write_fd, 900, controle)
    except Exception as exc:
        record('release_check', **gpu_guard.check_release(lambda: False, pids))
        record('supervision_error', error=type(exc).__name__)
        raise
    record('supervision_finished', status=result['statut'], phase=result['phase'])
    state = gpu_guard.check_release(lambda: gpu_guard.namespace_stopped(result, supervision), pids)
    record('release_check', **state)
    if state['status'] != 'verifie':
        raise RuntimeError('GPU or capsule release not verified')
    if result['statut'] != 'succès' or not result['arret_confirmé']:
        raise RuntimeError('paint failed or stop not confirmed')
    return result


def verify_configuration(args):
    root = args.root.resolve(strict=True)
    blender = args.blender.resolve(strict=True)
    if not root.is_dir() or not args.lock.is_file() or not blender.is_file() or not os.access(blender, os.X_OK):
        raise ValueError('invalid root, lock or Blender')
    if root == CODE or CODE in root.parents:
        raise ValueError('experiment root must be outside code')
    manifest = json.loads((CODE / 'input-manifest.json').read_text())
    if sha256(blender) != manifest['blender_sha256']:
        raise RuntimeError('Blender SHA mismatch')
    checked = verify(root, manifest)
    if not checked['verified']:
        failures = [item for item in checked['files'] if item['status'] != 'ok']
        raise RuntimeError('input verification failed: ' + json.dumps(failures))
    check = 'import importlib.metadata as m,json,sys; print(json.dumps({n:m.version(n) for n in json.loads(sys.argv[1])}))'
    command = [str(root / PYTHON_EXECUTABLE), '-c', check, json.dumps(list(manifest['runtime_versions']))]
    runtime = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30,
                             env={'PATH': MINIMAL_PATH, 'PYTHONDONTWRITEBYTECODE': '1'})
    if json.loads(runtime.stdout) != manifest['runtime_versions']:
        raise RuntimeError('runtime versions mismatch')
    return root, blender, len(checked['files'])


def make_run(root, name):
    capsules = root / 'capsules'
    if capsules.is_symlink():
        raise ValueError('capsules directory cannot be symlink')
    capsules.mkdir(exist_ok=True)
    run = capsules / name
    run.mkdir(mode=0o700, exist_ok=False)
    for directory in ('home', 'tmp', 'hf', 'xdg', 'torch', 'mpl', 'output'):
        (run / directory).mkdir()
    return run


def base_command(root, run):
    return ['bwrap', '--unshare-net', '--unshare-pid', '--die-with-parent', '--new-session',
            '--ro-bind', '/', '/', '--dev-bind', '/dev', '/dev', '--proc', '/proc',
            '--bind', str(run), str(run), '--chdir', str(root / 'source')]


def environment(root, run, gpu):
    return {'PATH': MINIMAL_PATH, 'HOME': str(run / 'home'), 'TMPDIR': str(run / 'tmp'),
            'HF_HOME': str(run / 'hf'), 'TORCH_HOME': str(run / 'torch'),
            'XDG_CACHE_HOME': str(run / 'xdg'), 'MPLCONFIGDIR': str(run / 'mpl'),
            'MESH_PAINT_ROOT': str(root), 'MESH_PAINT_RUN_ROOT': str(run / 'output'),
            'PYTHONDONTWRITEBYTECODE': '1', 'CUDA_VISIBLE_DEVICES': gpu,
            'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'HF_HUB_DISABLE_IMPLICIT_TOKEN': '1',
            'TORCH_FORCE_WEIGHTS_ONLY_LOAD': '1', 'USE_TF': '0'}


def add_environment(command, values):
    command.append('--clearenv')
    for key, value in values.items():
        command.extend(['--setenv', key, value])
    command.append('--')


def cpu_preflight(root, run):
    if ram_available() < 24 * 1024**3:
        raise RuntimeError('insufficient RAM for CPU preflight')
    command = base_command(root, run)
    add_environment(command, environment(root, run, ''))
    command += [str(root / PYTHON_EXECUTABLE), str(CODE / 'preflight_cpu.py')]
    with (run / 'cpu-preflight.log').open('x') as output:
        subprocess.run(command, stdout=output, stderr=subprocess.STDOUT,
                       env={'PATH': MINIMAL_PATH}, check=True, timeout=180)


def gpu_preflight(run, record):
    rows = smi('--query-gpu=uuid,memory.free').splitlines()
    if len(rows) != 1:
        raise RuntimeError('expected one GPU')
    uuid, free = (part.strip() for part in rows[0].split(','))
    ram, disk, busy = ram_available(), shutil.disk_usage(run).free, sorted(pids())
    record('preflight', gpu_uuid=uuid, gpu_free_mb=int(free), ram_available=ram,
           disk_free=disk, pids=busy, comfy_queue='unknown', timeout_seconds=900)
    if busy or int(free) < 24576 or ram < 24 * 1024**3 or disk < 10 * 1024**3:
        raise RuntimeError('resource preflight failed')
    return uuid


def execute(root, lock_path, blender, run):
    sync_dir = CODE.parents[1] / 'sync/labo'
    if sync_dir.is_dir():
        sys.path.insert(0, str(sync_dir))
    import capsule_sync
    import supervision_capsule
    fd = gpu_guard.open_lock(lock_path, capsule_sync)
    try:
        with (run / 'monitor.jsonl').open('x') as log:
            def record(event, **fields):
                log.write(json.dumps({'event': event, 'time': time.time(), **fields}) + '\n')
                log.flush()
            uuid = gpu_preflight(run, record)
            read_fd, write_fd = os.pipe()
            command = base_command(root, run)
            command += ['--sync-fd', str(fd), '--json-status-fd', str(write_fd)]
            values = environment(root, run, uuid)
            values['MESH_PAINT_BLENDER'] = str(blender)
            add_environment(command, values)
            command += [str(root / PYTHON_EXECUTABLE), str(CODE / 'run_paint.py'), '--run-id', 'paint']
            last = [0.0]
            def controle(_identity, namespace_pids):
                if time.monotonic() - last[0] < 1:
                    return
                last[0] = time.monotonic()
                if pids() - set(namespace_pids):
                    raise RuntimeError('foreign GPU PID detected')
            supervise_and_check(command, run, fd, read_fd, write_fd, controle, supervision_capsule, record)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True, help='private provisioned experiment root')
    parser.add_argument('--lock', type=Path, required=True, help='existing shared GPU lock')
    parser.add_argument('--blender', type=Path, required=True, help='Blender 5.2.3 executable')
    parser.add_argument('--run-id', required=True, type=safe_name)
    parser.add_argument('--dry-run', action='store_true', help='verify files only; do not create output or use GPU')
    args = parser.parse_args()
    root, blender, count = verify_configuration(args)
    print(json.dumps({'inputs_verified': count, 'dry_run': args.dry_run}), flush=True)
    if args.dry_run:
        return
    run = make_run(root, args.run_id)
    cpu_preflight(root, run)
    execute(root, args.lock, blender, run)


if __name__ == '__main__':
    main()
