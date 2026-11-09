"""Diagnostic CPU : bords et composantes avant toute réparation."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def _validate(vertices, faces):
    vertices = np.asarray(vertices, dtype=np.float64)
    faces = np.asarray(faces)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all():
        raise ValueError('positions invalides ou non finies')
    if faces.ndim != 2 or faces.shape[1] != 3 or not np.issubdtype(faces.dtype, np.integer):
        raise ValueError('indices invalides')
    if faces.size and (faces.min() < 0 or faces.max() >= len(vertices)):
        raise ValueError('indice hors plage')
    return vertices, faces.astype(np.int64, copy=False)


def _components(tris, count):
    parent = np.arange(count, dtype=np.int64)
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b, c in tris:
        parent[root(a)] = root(b)
        parent[root(b)] = root(c)
    roots = np.array([root(x) for x in tris[:, 0]], dtype=np.int64)
    if not len(roots):
        return []
    _, counts = np.unique(roots, return_counts=True)
    return sorted((int(x) for x in counts), reverse=True)


def _stats(vertices, faces, ids, count):
    tri = ids[faces]
    a, b, c = (vertices[faces[:, i]] for i in range(3))
    cross = np.cross(b - a, c - a)
    area2 = np.einsum('ij,ij->i', cross, cross)
    valid = ((tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) &
             (tri[:, 0] != tri[:, 2]) & (area2 >= 1e-18))
    good = tri[valid]
    edges = np.concatenate((good[:, [0, 1]], good[:, [1, 2]], good[:, [2, 0]]))
    edges.sort(axis=1)
    _, occurrences = np.unique(edges, axis=0, return_counts=True)
    components = _components(good, count)
    return {'vertices': count, 'triangles': len(faces), 'degenerate': int((~valid).sum()),
            'open_edges': int((occurrences == 1).sum()),
            'nonmanifold_edges': int((occurrences > 2).sum()),
            'components': len(components), 'component_triangle_counts': components,
            'minimum_cross_squared': float(area2.min()) if len(area2) else None}


def analyze(vertices, faces):
    vertices, faces = _validate(vertices, faces)
    if vertices.size and np.max(np.abs(vertices)) >= 9e13:
        raise ValueError('positions hors plage de quantification')
    exact, exact_ids = np.unique(vertices, axis=0, return_inverse=True)
    quant, quant_ids = np.unique(np.floor(vertices * 1e5 + .5).astype(np.int64), axis=0, return_inverse=True)
    pairs = np.unique(np.column_stack((exact_ids, quant_ids)), axis=0)
    return {'scope': 'diagnostic géométrique; pas de contrôle auto-intersection ni impression',
            'exact': _stats(vertices, faces, exact_ids, len(exact)),
            'quantized': _stats(vertices, faces, quant_ids, len(quant)),
            'partitions_identical': len(pairs) == len(exact) == len(quant),
            'quantization': 1e5, 'cross_squared_threshold': 1e-18}


def load_arrays(positions, faces):
    if Path(positions).stat().st_size % 24 or Path(faces).stat().st_size % 12:
        raise ValueError('taille de fichier non multiple de triplet')
    p = np.fromfile(positions, dtype='<f8')
    f = np.fromfile(faces, dtype='<u4')
    if len(p) % 3 or len(f) % 3:
        raise ValueError('longueur de fichier non multiple de trois')
    return _validate(p.reshape(-1, 3), f.reshape(-1, 3))


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positions', type=Path, required=True, help='triplets float64 little-endian')
    parser.add_argument('--faces', type=Path, required=True, help='triplets uint32 little-endian')
    parser.add_argument('--out', type=Path, required=True, help='nouveau rapport JSON')
    args = parser.parse_args()
    vertices, faces = load_arrays(args.positions, args.faces)
    report = analyze(vertices, faces)
    report['inputs'] = {'positions_sha256': file_sha(args.positions), 'faces_sha256': file_sha(args.faces)}
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
