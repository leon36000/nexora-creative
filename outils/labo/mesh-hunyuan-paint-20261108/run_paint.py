#!/usr/bin/env python3
"""Isolated Hunyuan Paint runner; never use without resource/queue preflight."""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import types

ROOT = pathlib.Path(os.environ['MESH_PAINT_ROOT']).resolve(strict=True)
SOURCE = ROOT / 'source'
INPUTS = ROOT / 'inputs'
EXPECTED = {
    '01-chaise.glb': '227cb2959def0a2b72e0d7c38173fae3cacf08d01a40514b6a9d4d339ff8e509',
    '01-chaise.png': '52c90fd149babb471f58cce2ed9d61edf6090a912ec4ccc2d6ab388baec25be5',
}

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-imports', action='store_true')
    parser.add_argument('--run-id', help='new output directory basename')
    args = parser.parse_args()
    if os.environ.get('TORCH_FORCE_WEIGHTS_ONLY_LOAD') != '1':
        raise RuntimeError('TORCH_FORCE_WEIGHTS_ONLY_LOAD=1 is required')
    for name, expected in EXPECTED.items():
        if sha(INPUTS / name) != expected:
            raise RuntimeError('input SHA mismatch: ' + name)
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.chdir(SOURCE)
    sys.path.insert(0, str(SOURCE / 'hy3dpaint'))
    from utils.torchvision_fix import apply_fix
    apply_fix()
    import huggingface_hub
    def local_snapshot(repo_id, **kwargs):
        if repo_id != 'tencent/Hunyuan3D-2.1':
            raise RuntimeError('unexpected model repository: ' + str(repo_id))
        return str(ROOT / 'model-source')
    huggingface_hub.snapshot_download = local_snapshot
    # Upstream imports bpy solely for its optional OBJ-to-GLB step. Conversion
    # runs in the existing standalone Blender instead of inside this venv.
    sys.modules['bpy'] = types.ModuleType('bpy')
    from textureGenPipeline import Hunyuan3DPaintConfig, Hunyuan3DPaintPipeline
    if args.check_imports:
        print('IMPORTS_OK; no model created; no GPU inference')
        return
    if not args.run_id or not args.run_id.replace('-', '').isalnum():
        raise ValueError('provide a new alphanumeric --run-id')
    run_root = pathlib.Path(os.environ['MESH_PAINT_RUN_ROOT']).resolve(strict=True)
    if ROOT not in run_root.parents:
        raise ValueError('run root must be inside the private experiment')
    run = run_root / args.run_id
    run.mkdir(parents=True, exist_ok=False)
    conf = Hunyuan3DPaintConfig(max_num_view=6, resolution=512)
    conf.dino_ckpt_path = str(ROOT / 'dinov2-giant')
    conf.realesrgan_ckpt_path = str(SOURCE / 'hy3dpaint/ckpt/RealESRGAN_x4plus.pth')
    start = time.monotonic()
    pipeline = Hunyuan3DPaintPipeline(conf)
    obj = pipeline(mesh_path=str(INPUTS / '01-chaise.glb'), image_path=str(INPUTS / '01-chaise.png'), output_mesh_path=str(run / 'result.obj'), use_remesh=False, save_glb=False)
    glb = run / 'result.glb'
    blender = pathlib.Path(os.environ['MESH_PAINT_BLENDER']).resolve(strict=True)
    subprocess.run([str(blender), '--background', '--factory-startup', '--python', str(pathlib.Path(__file__).resolve().with_name('convert_obj.py')), '--', str(obj), str(glb)], check=True)
    products = {p.name: sha(p) for p in run.iterdir() if p.is_file() and not p.is_symlink()}
    receipt = {'source_revision': '82920d643c0dc2f7bfd7255f45f62d386edfe60c', 'model_revision': '0b94677654c57bb9a6b6845cd7b704ccf551d327', 'dino_revision': '611a9d42f2335e0f921f1e313ad3c1b7178d206d', 'inputs': EXPECTED, 'use_remesh': False, 'uv_unwrap': 'xatlas upstream', 'resolution': 512, 'max_num_view': 6, 'forced_weights_only': True, 'ignored_diffusers_config': ['requires_safety_checker', 'image_encoder'], 'elapsed_seconds': time.monotonic() - start, 'obj': str(obj), 'glb_sha256': sha(glb), 'products_sha256': products}
    with (run / 'receipt.json').open('x') as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt))

if __name__ == '__main__':
    main()
