"""Reconstruction volumique expérimentale vers un nouveau STL, sans UV."""
import argparse
import importlib.metadata
import json
import time
from pathlib import Path

import numpy as np
from topology import analyze, file_sha, load_arrays


def read_stl(path):
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError('STL tronqué')
    n = int.from_bytes(data[80:84], 'little')
    if len(data) != 84 + n * 50:
        raise ValueError('taille STL invalide')
    dtype = np.dtype([('normal', '<f4', 3), ('vertices', '<f4', (3, 3)), ('attr', '<u2')])
    vertices = np.frombuffer(data, dtype=dtype, offset=84, count=n)['vertices'].reshape(-1, 3).astype(np.float64)
    return vertices, np.arange(len(vertices), dtype=np.uint32).reshape(-1, 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positions', type=Path, required=True)
    parser.add_argument('--faces', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='nouveau dossier exclusif')
    parser.add_argument('--voxel-divisor', type=int, required=True)
    parser.add_argument('--fix-degeneracies', action='store_true', help='appliquer le remesh local après reconstruction')
    args = parser.parse_args()
    if not 20 <= args.voxel_divisor <= 1000:
        parser.error('voxel-divisor doit être entre 20 et 1000')
    vertices, faces = load_arrays(args.positions, args.faces)
    if not len(vertices) or not len(faces):
        parser.error('géométrie vide')
    diagonal = float(np.linalg.norm(np.ptp(vertices, axis=0)))
    if not np.isfinite(diagonal) or diagonal <= 0:
        parser.error('boîte englobante invalide')
    from meshlib import mrmeshpy as mm, mrmeshnumpy as mn
    unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
    mesh = mn.meshFromFacesVerts(np.asarray(inverse[faces], dtype=np.int32), np.asarray(unique, dtype=np.float32))
    params = mm.GeneralOffsetParameters()
    params.voxelSize = diagonal / args.voxel_divisor
    params.signDetectionMode = mm.SignDetectionMode.HoleWindingRule
    params.closeHolesInHoleWindingNumber = True
    args.out.mkdir(mode=0o700)
    start = time.monotonic()
    result = mm.generalOffsetMesh(mm.MeshPart(mesh), 0.0, params)
    elapsed = time.monotonic() - start
    before = args.out / 'avant-correction.stl'
    mm.saveMesh(result, before)
    fix_settings = None
    if args.fix_degeneracies:
        fix = mm.FixMeshDegeneraciesParams()
        fix.mode = mm.FixMeshDegeneraciesParams.Mode.Remesh
        fix.maxDeviation = params.voxelSize * .1
        fix.tinyEdgeLength = params.voxelSize * .01
        fix.criticalTriAspectRatio = 1000
        mm.fixMeshDegeneracies(result, fix)
        fix_settings = {'mode': 'Remesh', 'max_deviation': float(fix.maxDeviation),
                        'tiny_edge_length': float(fix.tinyEdgeLength), 'critical_aspect_ratio': 1000}
    out = args.out / 'derive.stl'
    mm.saveMesh(result, out)
    stl_vertices, stl_faces = read_stl(out)
    before_vertices, before_faces = read_stl(before)
    receipt = {'status': 'ESSAI géométrique; STL sans UV ni texture; non qualifié impression',
               'meshlib_core': importlib.metadata.version('meshlib-core'),
               'input_positions_sha256': file_sha(args.positions), 'input_faces_sha256': file_sha(args.faces),
               'before_sha256': file_sha(before), 'output_sha256': file_sha(out), 'fix': fix_settings, 'voxel_size': float(params.voxelSize),
               'bbox_diagonal': diagonal, 'voxel_divisor': args.voxel_divisor,
               'sign_detection': 'HoleWindingRule', 'close_holes': True, 'offset': 0,
               'offset_seconds': elapsed, 'before_diagnostic': analyze(before_vertices, before_faces),
               'output_diagnostic': analyze(stl_vertices, stl_faces)}
    with (args.out / 'receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
