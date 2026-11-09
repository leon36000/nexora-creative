#!/usr/bin/env python3
"""Area-weighted, bidirectional Monte Carlo distances between triangle surfaces.

The module keeps sampling/statistics independent of MeshLib so the protocol can
be tested with synthetic projectors. The CLI backend uses MeshLib for nearest
point-on-triangle projection.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


DEFAULT_MAX_FACES = 500_000
HARD_MAX_FACES = 2_000_000
DEFAULT_SAMPLES = 20_000
MAX_SAMPLES = 100_000
DEFAULT_SEED = 20261109

LABEL_A_REFERENCE = "A/reference"
LABEL_B_CANDIDATE = "B/candidate"


@dataclass(frozen=True)
class MeshArrays:
    vertices: np.ndarray
    faces: np.ndarray


@dataclass(frozen=True)
class PreparedMesh:
    vertices: np.ndarray  # float64 values exactly representable by the MeshLib float32 backend
    faces: np.ndarray
    area_weights: np.ndarray
    total_area_normalized: float
    input_vertex_count: int
    input_face_count: int
    excluded_zero_area_faces: int
    max_float32_rounding_error: float


@dataclass(frozen=True)
class PreparedPair:
    a: PreparedMesh
    b: PreparedMesh
    reference_diagonal: float
    reference_bbox_min: tuple[float, float, float]
    reference_bbox_max: tuple[float, float, float]
    combined_bbox_diagonal: float


def validate_arrays(vertices: np.ndarray, faces: np.ndarray, label: str) -> MeshArrays:
    vertices = np.asarray(vertices, dtype=np.float64)
    faces = np.asarray(faces)
    if vertices.ndim != 2 or vertices.shape[1] != 3 or len(vertices) < 3:
        raise ValueError(f"{label}: expected positions shaped (N, 3), N >= 3")
    if not np.isfinite(vertices).all():
        raise ValueError(f"{label}: positions contain NaN or infinity")
    if faces.ndim != 2 or faces.shape[1] != 3 or len(faces) == 0:
        raise ValueError(f"{label}: expected non-empty triangle indices shaped (M, 3)")
    if not np.issubdtype(faces.dtype, np.integer):
        raise ValueError(f"{label}: triangle indices must be integers")
    if faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError(f"{label}: triangle index is outside the position array")
    return MeshArrays(vertices, faces.astype(np.int64, copy=False))


def _twice_areas(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    tri = vertices[faces]
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    if not np.isfinite(e1).all() or not np.isfinite(e2).all():
        raise ValueError("coordinate subtraction overflowed float64")
    scale = np.maximum(np.max(np.abs(e1), axis=1), np.max(np.abs(e2), axis=1))
    out = np.zeros(len(faces), dtype=np.float64)
    nonzero = scale > 0
    if np.any(nonzero):
        cross = np.cross(e1[nonzero] / scale[nonzero, None], e2[nonzero] / scale[nonzero, None])
        # Only positivity is needed here; the scale-squared factor can overflow
        # for large world coordinates and does not affect the degeneracy test.
        out[nonzero] = np.linalg.norm(cross, axis=1)
    return out


def _bbox_diagonal(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    low = np.min(vertices, axis=0)
    high = np.max(vertices, axis=0)
    span = high - low
    if not np.isfinite(span).all():
        raise ValueError("bounding-box span overflowed float64")
    diagonal = math.hypot(float(span[0]), float(span[1]), float(span[2]))
    if not math.isfinite(diagonal) or diagonal <= 0:
        raise ValueError("reference bounding-box diagonal must be finite and positive")
    return low, high, diagonal


def _prepare_mesh(arrays: MeshArrays, center: np.ndarray, diagonal: float, label: str) -> PreparedMesh:
    raw_area_signal = _twice_areas(arrays.vertices, arrays.faces)
    valid = raw_area_signal > 0
    valid_faces = arrays.faces[valid]
    if not len(valid_faces):
        raise ValueError(f"{label}: no non-zero-area triangles")

    used, inverse = np.unique(valid_faces.reshape(-1), return_inverse=True)
    normalized64 = (arrays.vertices[used] - center) / diagonal
    if not np.isfinite(normalized64).all():
        raise ValueError(f"{label}: normalization produced non-finite coordinates")
    normalized32 = normalized64.astype(np.float32)
    if not np.isfinite(normalized32).all():
        raise ValueError(f"{label}: normalized coordinates exceed MeshLib float32 range")
    vertices = normalized32.astype(np.float64)
    faces = inverse.reshape(-1, 3).astype(np.int32, copy=False)
    backend_area = _twice_areas(vertices, faces)
    if np.any(backend_area <= 0):
        raise ValueError(f"{label}: float32 conversion collapsed a non-zero-area triangle")
    areas = _triangle_areas(vertices, faces)
    if np.any(areas <= 0):
        raise ValueError(f"{label}: non-zero-area triangle underflowed during area weighting")
    total_area = float(np.sum(areas, dtype=np.float64))
    if not math.isfinite(total_area) or total_area <= 0:
        raise ValueError(f"{label}: normalized surface area is invalid")
    rounding = np.abs(normalized64 - vertices)
    max_rounding_error = float(np.max(np.linalg.norm(rounding, axis=1)))
    if not math.isfinite(max_rounding_error):
        raise ValueError(f"{label}: float32 rounding error is non-finite")
    return PreparedMesh(
        vertices=vertices,
        faces=faces,
        area_weights=areas,
        total_area_normalized=total_area,
        input_vertex_count=len(arrays.vertices),
        input_face_count=len(arrays.faces),
        excluded_zero_area_faces=int((~valid).sum()),
        max_float32_rounding_error=max_rounding_error,
    )


def prepare_pair(vertices_a: np.ndarray, faces_a: np.ndarray,
                 vertices_b: np.ndarray, faces_b: np.ndarray) -> PreparedPair:
    a = validate_arrays(vertices_a, faces_a, LABEL_A_REFERENCE)
    b = validate_arrays(vertices_b, faces_b, LABEL_B_CANDIDATE)
    a_area_signal = _twice_areas(a.vertices, a.faces)
    a_valid = a.faces[a_area_signal > 0]
    b_area_signal = _twice_areas(b.vertices, b.faces)
    b_valid = b.faces[b_area_signal > 0]
    if not len(a_valid):
        raise ValueError(f"{LABEL_A_REFERENCE}: no non-zero-area triangles")
    if not len(b_valid):
        raise ValueError(f"{LABEL_B_CANDIDATE}: no non-zero-area triangles")
    a_used = np.unique(a_valid)
    b_used = np.unique(b_valid)
    ref_low, ref_high, ref_diagonal = _bbox_diagonal(a.vertices[a_used])
    ref_center = ref_low + (ref_high - ref_low) * 0.5
    combined = np.concatenate((a.vertices[a_used], b.vertices[b_used]), axis=0)
    _, _, combined_diagonal = _bbox_diagonal(combined)
    prepared_a = _prepare_mesh(a, ref_center, ref_diagonal, LABEL_A_REFERENCE)
    prepared_b = _prepare_mesh(b, ref_center, ref_diagonal, LABEL_B_CANDIDATE)
    return PreparedPair(
        a=prepared_a,
        b=prepared_b,
        reference_diagonal=ref_diagonal,
        reference_bbox_min=tuple(float(x) for x in ref_low),
        reference_bbox_max=tuple(float(x) for x in ref_high),
        combined_bbox_diagonal=combined_diagonal,
    )


def sample_surface(mesh: PreparedMesh, count: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(count, int) or count < 1 or count > MAX_SAMPLES:
        raise ValueError(f"sample count must be between 1 and {MAX_SAMPLES}")
    probabilities = mesh.area_weights / mesh.total_area_normalized
    chosen = rng.choice(len(mesh.faces), size=count, replace=True, p=probabilities)
    uv = rng.random((count, 2))
    root = np.sqrt(uv[:, 0])
    barycentric = np.column_stack((1.0 - root, root * (1.0 - uv[:, 1]), root * uv[:, 1]))
    tri = mesh.vertices[mesh.faces[chosen]]
    points = np.einsum("ni,nij->nj", barycentric, tri)
    return points, chosen


def _triangle_areas(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Return actual half-cross-product magnitudes in the current coordinates."""
    tri = vertices[faces]
    e1 = tri[:, 1] - tri[:, 0]
    e2 = tri[:, 2] - tri[:, 0]
    if not np.isfinite(e1).all() or not np.isfinite(e2).all():
        raise ValueError("coordinate subtraction overflowed float64")
    scale = np.maximum(np.max(np.abs(e1), axis=1), np.max(np.abs(e2), axis=1))
    areas = np.zeros(len(faces), dtype=np.float64)
    nonzero = scale > 0
    if np.any(nonzero):
        cross = np.cross(e1[nonzero] / scale[nonzero, None], e2[nonzero] / scale[nonzero, None])
        areas[nonzero] = np.linalg.norm(cross, axis=1) * scale[nonzero] * scale[nonzero] * 0.5
    if not np.isfinite(areas).all():
        raise ValueError("normalized triangle area overflowed float64")
    return areas


def _quantiles(distances: np.ndarray, diagonal: float) -> dict:
    if distances.ndim != 1 or not len(distances):
        raise ValueError("projector must return a non-empty vector of distances")
    if not np.isfinite(distances).all() or np.any(distances < 0):
        raise ValueError("projector returned a negative or non-finite distance")
    qs = np.quantile(distances, [0.5, 0.95, 0.99, 1.0], method="linear")
    names = ("median", "p95", "p99", "max_sampled")
    return {
        "sample_count": int(len(distances)),
        "normalized_by_reference_bbox_diagonal": {name: float(value) for name, value in zip(names, qs)},
        "distance_in_input_units": {name: float(value * diagonal) for name, value in zip(names, qs)},
    }


Projector = Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]


def compare_prepared(pair: PreparedPair, sample_count: int, seed: int, projector: Projector) -> dict:
    if not isinstance(seed, int) or seed < 0 or seed > (2**64 - 1):
        raise ValueError("seed must be an unsigned 64-bit integer")
    if not isinstance(sample_count, int) or sample_count < 1 or sample_count > MAX_SAMPLES:
        raise ValueError(f"sample count must be between 1 and {MAX_SAMPLES}")
    child_a, child_b = np.random.SeedSequence(seed).spawn(2)
    points_a, selected_a = sample_surface(pair.a, sample_count, np.random.Generator(np.random.PCG64(child_a)))
    points_b, selected_b = sample_surface(pair.b, sample_count, np.random.Generator(np.random.PCG64(child_b)))
    d_ab = np.asarray(projector(points_a, pair.b.vertices, pair.b.faces), dtype=np.float64)
    d_ba = np.asarray(projector(points_b, pair.a.vertices, pair.a.faces), dtype=np.float64)
    result = {
        "protocol": {
            "name": "area-weighted bidirectional Monte Carlo nearest-surface distance",
            "reference": "A",
            "sampling": "triangles chosen with probability proportional to normalized area; points uniform within each triangle via square-root barycentric sampling",
            "seed": seed,
            "bit_generator": "NumPy PCG64; independent SeedSequence child streams for A-to-B and B-to-A",
            "samples_per_direction": sample_count,
            "hard_max_samples_per_direction": MAX_SAMPLES,
            "quantiles": "NumPy linear quantile interpolation over the sampled distances",
            "normalization": "shared reference A surface bounding-box diagonal; B does not affect normalization",
            "hausdorff": False,
            "limitation": "finite deterministic Monte Carlo sample; not a Hausdorff distance and may miss small features or rare extrema",
        },
        "scale": {
            "reference_bbox_min_input_units": list(pair.reference_bbox_min),
            "reference_bbox_max_input_units": list(pair.reference_bbox_max),
            "reference_bbox_diagonal_input_units": pair.reference_diagonal,
            "combined_a_b_bbox_diagonal_input_units_diagnostic_only": pair.combined_bbox_diagonal,
        },
        "surfaces": {
            "A_reference": _mesh_summary(pair.a, int(len(selected_a))),
            "B_candidate": _mesh_summary(pair.b, int(len(selected_b))),
        },
        "directions": {
            "A_to_B": {**_quantiles(d_ab, pair.reference_diagonal), "max_sample_point_float32_rounding_error_in_reference_diagonal_units": _max_float32_error(points_a)},
            "B_to_A": {**_quantiles(d_ba, pair.reference_diagonal), "max_sample_point_float32_rounding_error_in_reference_diagonal_units": _max_float32_error(points_b)},
        },
    }
    return result


def _max_float32_error(points: np.ndarray) -> float:
    rounded = np.asarray(points, dtype=np.float32)
    if not np.isfinite(rounded).all():
        raise ValueError("sample points exceed MeshLib float32 range")
    error = np.linalg.norm(np.asarray(points, dtype=np.float64) - rounded.astype(np.float64), axis=1)
    return float(np.max(error))


def _mesh_summary(mesh: PreparedMesh, samples: int) -> dict:
    return {
        "input_vertices": mesh.input_vertex_count,
        "input_triangles": mesh.input_face_count,
        "sampled_surface_triangles": int(len(mesh.faces)),
        "excluded_zero_area_triangles": mesh.excluded_zero_area_faces,
        "surface_area_in_reference_diagonal_squared": mesh.total_area_normalized,
        "sample_count": samples,
        "backend_coordinate_type": "float32 (MeshLib); distances are reported in normalized units and rescaled by A's input-space diagonal",
        "maximum_vertex_rounding_error_in_reference_diagonal_units": mesh.max_float32_rounding_error,
    }


def meshlib_projector():
    try:
        from meshlib import mrmeshpy as mm, mrmeshnumpy as mn
    except ImportError as exc:
        raise RuntimeError("MeshLib is required for CLI projection; activate the existing private MeshLib venv") from exc

    def project(points: np.ndarray, vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
        mesh = mn.meshFromFacesVerts(
            np.asarray(faces, dtype=np.int32),
            np.asarray(vertices, dtype=np.float32),
            duplicateNonManifoldVertices=True,
        )
        part = mm.MeshPart(mesh)
        result = np.empty(len(points), dtype=np.float64)
        for index, point in enumerate(points):
            projection = mm.findProjection(mm.Vector3f(float(point[0]), float(point[1]), float(point[2])), part)
            if not projection.valid():
                raise RuntimeError(f"MeshLib returned no valid surface projection at sample {index}")
            dist_sq = float(projection.distSq)
            if not math.isfinite(dist_sq) or dist_sq < 0:
                raise RuntimeError(f"MeshLib returned invalid squared distance at sample {index}")
            result[index] = math.sqrt(dist_sq)
        return result
    return project


def check_binary_pair(positions_path: Path, faces_path: Path, label: str, max_faces: int = DEFAULT_MAX_FACES) -> None:
    if type(max_faces) is not int or not 1 <= max_faces <= HARD_MAX_FACES:
        raise ValueError(f"{label}: max faces must be between 1 and {HARD_MAX_FACES}")
    if positions_path.is_symlink() or faces_path.is_symlink():
        raise ValueError(f"{label}: symlink inputs are refused")
    if not positions_path.is_file() or not faces_path.is_file():
        raise ValueError(f"{label}: regular position and face files are required")
    if positions_path.stat().st_size == 0 or positions_path.stat().st_size % 24:
        raise ValueError(f"{label}: positions file size must be a non-zero multiple of 24 bytes")
    if faces_path.stat().st_size == 0 or faces_path.stat().st_size % 12:
        raise ValueError(f"{label}: faces file size must be a non-zero multiple of 12 bytes")
    if faces_path.stat().st_size // 12 > max_faces:
        raise ValueError(f"{label}: face count exceeds max-faces before allocation")
    if positions_path.stat().st_size // 24 > 3 * max_faces:
        raise ValueError(f"{label}: vertex count exceeds 3 * max-faces before allocation")


def load_binary_pair(positions_path: Path, faces_path: Path, label: str, max_faces: int = DEFAULT_MAX_FACES) -> MeshArrays:
    check_binary_pair(positions_path, faces_path, label, max_faces)
    vertices = np.fromfile(positions_path, dtype="<f8").reshape(-1, 3)
    faces = np.fromfile(faces_path, dtype="<u4").reshape(-1, 3)
    return validate_arrays(vertices, faces, label)


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_metadata_hash(metadata: dict, expected: dict, key: str) -> None:
    value = metadata.get(key)
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"extractor metadata has invalid {key}")
    if value != expected[key]:
        raise ValueError(f"extractor metadata {key} does not match its source file")


def load_extraction_metadata(path: Path, source_glb_path: Path, positions_path: Path,
                             faces_path: Path, arrays: MeshArrays) -> dict:
    for item, label in ((path, "metadata"), (source_glb_path, "source GLB")):
        if item.is_symlink() or not item.is_file():
            raise ValueError(f"extractor {label} must be a regular, non-symlink file")
    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid extractor metadata JSON: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ValueError("extractor metadata must be a JSON object")
    expected = {
        "source_sha256": file_sha(source_glb_path),
        "positions_sha256": file_sha(positions_path),
        "faces_sha256": file_sha(faces_path),
        "vertices": len(arrays.vertices),
        "triangles": len(arrays.faces),
    }
    for key in ("source_sha256", "positions_sha256", "faces_sha256"):
        _validate_metadata_hash(metadata, expected, key)
    for key in ("vertices", "triangles"):
        if type(metadata.get(key)) is not int or metadata[key] != expected[key]:
            raise ValueError(f"extractor metadata {key} does not match the supplied array")
    return {
        "source_glb_sha256": metadata["source_sha256"],
        "positions_sha256": expected["positions_sha256"],
        "faces_sha256": expected["faces_sha256"],
        "vertices": expected["vertices"],
        "triangles": expected["triangles"],
        "extractor_metadata_sha256": file_sha(path),
        "source_glb_path": str(source_glb_path.resolve()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--a-positions", type=Path, required=True, help=f"{LABEL_A_REFERENCE} positions.f64le")
    parser.add_argument("--a-faces", type=Path, required=True, help=f"{LABEL_A_REFERENCE} faces.u32le")
    parser.add_argument("--a-glb", type=Path, required=True, help=f"original {LABEL_A_REFERENCE} GLB; hash checked against source.json")
    parser.add_argument("--a-source-json", type=Path, required=True, help="extract-glb.mts source.json for A")
    parser.add_argument("--b-positions", type=Path, required=True, help=f"{LABEL_B_CANDIDATE} positions.f64le")
    parser.add_argument("--b-faces", type=Path, required=True, help=f"{LABEL_B_CANDIDATE} faces.u32le")
    parser.add_argument("--b-glb", type=Path, required=True, help=f"original {LABEL_B_CANDIDATE} GLB; hash checked against source.json")
    parser.add_argument("--b-source-json", type=Path, required=True, help="extract-glb.mts source.json for B")
    parser.add_argument("--max-faces", type=int, default=DEFAULT_MAX_FACES, help="per-mesh allocation limit; hard maximum 2000000")
    parser.add_argument("--samples-per-direction", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, required=True, help="new JSON report; existing paths are refused")
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit("output path already exists or is a symlink")
    if not 1 <= args.samples_per_direction <= MAX_SAMPLES:
        raise SystemExit(f"samples-per-direction must be between 1 and {MAX_SAMPLES}")
    if not 1 <= args.max_faces <= HARD_MAX_FACES:
        raise SystemExit(f"max-faces must be between 1 and {HARD_MAX_FACES}")
    check_binary_pair(args.a_positions, args.a_faces, LABEL_A_REFERENCE, args.max_faces)
    check_binary_pair(args.b_positions, args.b_faces, LABEL_B_CANDIDATE, args.max_faces)
    a = load_binary_pair(args.a_positions, args.a_faces, LABEL_A_REFERENCE, args.max_faces)
    b = load_binary_pair(args.b_positions, args.b_faces, LABEL_B_CANDIDATE, args.max_faces)
    a_meta = load_extraction_metadata(args.a_source_json, args.a_glb, args.a_positions, args.a_faces, a)
    b_meta = load_extraction_metadata(args.b_source_json, args.b_glb, args.b_positions, args.b_faces, b)
    prepared = prepare_pair(a.vertices, a.faces, b.vertices, b.faces)
    report = compare_prepared(prepared, args.samples_per_direction, args.seed, meshlib_projector())
    report["inputs"] = {
        "A_reference": {"paths": {"positions": str(args.a_positions.resolve()), "faces": str(args.a_faces.resolve()), "extractor_metadata": str(args.a_source_json.resolve())}, **a_meta},
        "B_candidate": {"paths": {"positions": str(args.b_positions.resolve()), "faces": str(args.b_faces.resolve()), "extractor_metadata": str(args.b_source_json.resolve())}, **b_meta},
    }
    try:
        meshlib_version = importlib.metadata.version("meshlib-core")
    except importlib.metadata.PackageNotFoundError:
        meshlib_version = "unknown"
    report["backend"] = {
        "name": "MeshLib mrmeshpy.findProjection + mrmeshnumpy.meshFromFacesVerts",
        "meshlib_core_version": meshlib_version,
        "numpy_version": np.__version__,
        "builder_duplicate_nonmanifold_vertices": True,
        "coordinate_type": "float32",
    }
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
