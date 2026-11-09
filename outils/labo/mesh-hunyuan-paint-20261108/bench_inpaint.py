#!/usr/bin/env python3
"""Rejoue une étape OpenCV NS sur deux NPY, sans modifier l'environnement."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np


def sha_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def sha_array(array):
    if not array.flags.c_contiguous:
        raise ValueError('array must be C-contiguous')
    return hashlib.sha256(memoryview(array).cast('B')).hexdigest()


def load_inputs(texture_path, mask_path):
    texture = np.load(texture_path, allow_pickle=False)
    mask = np.load(mask_path, allow_pickle=False)
    if not isinstance(texture, np.ndarray) or not isinstance(mask, np.ndarray):
        for value in (texture, mask):
            if hasattr(value, 'close'):
                value.close()
        raise ValueError('inputs must be NPY arrays')
    if texture.dtype != np.float32 or texture.ndim != 3 or texture.shape[2] != 3:
        raise ValueError('texture must be HxWx3 float32')
    if mask.dtype != np.uint8 or mask.ndim != 2 or mask.shape != texture.shape[:2] or not mask.size:
        raise ValueError('mask must be nonempty HxW uint8 matching texture')
    if not texture.flags.c_contiguous or not mask.flags.c_contiguous:
        raise ValueError('inputs must be C-contiguous')
    if not np.isfinite(texture).all() or np.any(texture < 0) or np.any(texture > 1):
        raise ValueError('texture must be finite and in [0,1]')
    if not np.all((mask == 0) | (mask == 255)):
        raise ValueError('mask values must be 0 or 255')
    return texture, mask


def attest_opencv(cv2, version, root):
    module = Path(cv2.__file__).resolve(strict=True)
    allowed = Path(root).resolve(strict=True)
    if cv2.__version__ != version:
        raise ValueError('unexpected OpenCV version')
    if not allowed.is_dir() or allowed not in module.parents:
        raise ValueError('OpenCV module is outside the expected directory')
    return {'version': cv2.__version__, 'module_path': str(module),
            'module_sha256': sha_file(module), 'note': 'module path/hash; loaded native libraries not individually attested',
            'build_info_sha256': hashlib.sha256(cv2.getBuildInformation().encode('utf-8')).hexdigest()}


def create_output(path):
    output = Path(path)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    return output


def run(texture_path, mask_path, output_dir, expected_version, expected_root):
    import cv2
    opencv = attest_opencv(cv2, expected_version, expected_root)
    texture_hash, mask_hash = sha_file(texture_path), sha_file(mask_path)
    texture, mask = load_inputs(texture_path, mask_path)
    if sha_file(texture_path) != texture_hash or sha_file(mask_path) != mask_hash:
        raise RuntimeError('input changed while loading')
    inputs = {'texture_npy_sha256': texture_hash, 'mask_npy_sha256': mask_hash,
              'shape': list(texture.shape), 'texture_dtype': str(texture.dtype), 'mask_dtype': str(mask.dtype)}
    output = create_output(output_dir)
    convert_start = time.monotonic()
    source = (texture * 255).astype(np.uint8)
    inpaint_mask = 255 - mask
    conversion_seconds = time.monotonic() - convert_start
    args = {'source_uint8_raw_sha256': sha_array(source), 'inpaint_mask_raw_sha256': sha_array(inpaint_mask)}
    start = time.monotonic()
    result = cv2.inpaint(source, inpaint_mask, 3, cv2.INPAINT_NS)
    inpaint_seconds = time.monotonic() - start
    if sha_array(source) != args['source_uint8_raw_sha256'] or sha_array(inpaint_mask) != args['inpaint_mask_raw_sha256']:
        raise RuntimeError('OpenCV mutated input arguments')
    if result.dtype != np.uint8 or result.shape != source.shape:
        raise RuntimeError('unexpected OpenCV output')
    result_path = output / 'output.npy'
    with result_path.open('xb') as stream:
        np.save(stream, result, allow_pickle=False)
    receipt = {'opencv': opencv, 'numpy_version': np.__version__, 'numpy_path': str(Path(np.__file__).resolve()),
               'python_version': sys.version, 'inputs': inputs, 'arguments': args,
               'method': 'INPAINT_NS', 'radius': 3,
               'conversion_seconds': conversion_seconds, 'inpaint_seconds': inpaint_seconds,
               'conversion_plus_inpaint_seconds': conversion_seconds + inpaint_seconds,
               'timing_note': 'sum of conversion and call; argument hashing is excluded',
               'output_npy_sha256': sha_file(result_path)}
    with (output / 'receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--texture', required=True, type=Path)
    parser.add_argument('--mask', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--opencv-version', required=True)
    parser.add_argument('--opencv-root', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.texture, args.mask, args.output_dir, args.opencv_version, args.opencv_root), ensure_ascii=False))


if __name__ == '__main__':
    main()
