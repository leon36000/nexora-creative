#!/usr/bin/env python3
"""CPU-only private overlay proof: raw glTF normal map + TEXCOORD_1 -> baked GLB."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path.cwd()
INPUT = ROOT / "inputs"
RESULTS = ROOT / "results"
REPORTS = ROOT / "reports"
SOURCE_GLB = INPUT / "source-normalmap-uv1-w-plus-minus.glb"
TARGET_GLB = RESULTS / "target-rebaked-atlas.glb"
BAKED_PNG = RESULTS / "baked-normal-atlas.png"
REPORT = REPORTS / "normalmap-rebake-proof.json"
RESOLUTION = 128
NORMAL_SCALE = 0.35
EXPECTED_RAW_PNG_SHA256 = "ec0bbbd8f9ab4d95dd289a7332f4e8d15ae5d0a98e21c8218461299bd8b34243"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def align4(data: bytes) -> bytes:
    return data + b"\0" * ((-len(data)) % 4)


def make_source_fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if SOURCE_GLB.exists() or TARGET_GLB.exists() or BAKED_PNG.exists() or REPORT.exists():
        raise RuntimeError("Outputs already exist; preserve them and run a new attempts/vN folder")
    INPUT.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    # Two disconnected curved triangles. Each corner is unique; smooth source N/T vary by vertex,
    # while glTF TANGENT.w is constant within each face and opposite between faces.
    xy = np.array([
        [-1.2, 0.0], [-0.2, 0.0], [-1.2, 1.0],
        [ 0.2, 0.0], [ 1.2, 0.0], [ 0.2, 1.0],
    ], dtype=np.float64)
    x, y = xy[:, 0], xy[:, 1]
    z = 0.14 * x * x + 0.18 * y * y + 0.15 * x * y
    dz_dx = 0.28 * x + 0.15 * y
    dz_dy = 0.36 * y + 0.15 * x
    positions = np.column_stack((x, y, z)).astype("<f4")
    normals = np.column_stack((-dz_dx, -dz_dy, np.ones_like(x)))
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    normals = normals.astype("<f4")
    # TEXCOORD_0 is the rebake target atlas (lower half); TEXCOORD_1 is the source map
    # coordinate (upper half), with the second triangle mirrored in V. U increases with x.
    atlas_uv = np.array([
        [0.10, 0.55], [0.40, 0.55], [0.10, 0.85],
        [0.60, 0.55], [0.90, 0.55], [0.60, 0.85],
    ], dtype="<f4")
    source_uv = np.array([
        [0.10, 0.10], [0.40, 0.10], [0.10, 0.40],
        [0.60, 0.40], [0.90, 0.40], [0.60, 0.10],
    ], dtype="<f4")
    source_t = np.column_stack((np.ones(6), np.zeros(6), dz_dx)).astype(np.float64)
    source_t -= normals.astype(np.float64) * np.sum(normals.astype(np.float64) * source_t, axis=1, keepdims=True)
    source_t /= np.linalg.norm(source_t, axis=1, keepdims=True)
    source_w = np.array([1.0, 1.0, 1.0, -1.0, -1.0, -1.0], dtype=np.float64)
    source_tangents = np.column_stack((source_t, source_w)).astype("<f4")
    indices = np.arange(6, dtype="<u2")

    # Deliberately asymmetric raw RGB normal data; no sRGB transfer is applied.
    yy, xx = np.mgrid[0:32, 0:32]
    rgb = np.stack((
        92 + 3 * xx + 1 * yy,
        70 + 1 * xx + 4 * yy,
        224 + (xx // 4) - (yy // 8),
    ), axis=-1).clip(0, 255).astype(np.uint8)
    png_path = INPUT / "source-normal-raw-rgb.png"
    Image.fromarray(rgb, "RGB").save(png_path, format="PNG", optimize=False)
    if sha(png_path) != EXPECTED_RAW_PNG_SHA256:
        raise AssertionError(f"fixture PNG SHA changed: {sha(png_path)}")

    chunks: list[bytes] = []
    views: list[dict] = []

    def add_view(data: bytes, target: int | None = None) -> int:
        offset = sum(map(len, chunks))
        chunks.append(align4(data))
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        views.append(view)
        return len(views) - 1

    p_view = add_view(positions.tobytes(), 34962)
    n_view = add_view(normals.tobytes(), 34962)
    t_view = add_view(source_tangents.tobytes(), 34962)
    uv0_view = add_view(atlas_uv.tobytes(), 34962)
    uv1_view = add_view(source_uv.tobytes(), 34962)
    i_view = add_view(indices.tobytes(), 34963)
    png_bytes = png_path.read_bytes()
    image_view = add_view(png_bytes)
    blob = b"".join(chunks)
    accessors = [
        {"bufferView": p_view, "componentType": 5126, "count": 6, "type": "VEC3",
         "min": positions.min(0).astype(float).tolist(), "max": positions.max(0).astype(float).tolist()},
        {"bufferView": n_view, "componentType": 5126, "count": 6, "type": "VEC3"},
        {"bufferView": t_view, "componentType": 5126, "count": 6, "type": "VEC4"},
        {"bufferView": uv0_view, "componentType": 5126, "count": 6, "type": "VEC2"},
        {"bufferView": uv1_view, "componentType": 5126, "count": 6, "type": "VEC2"},
        {"bufferView": i_view, "componentType": 5123, "count": 6, "type": "SCALAR",
         "min": [0], "max": [5]},
    ]
    gltf = {
        "asset": {"version": "2.0", "generator": "Nexora Mesh private normal-map rebake fixture"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "TANGENT": 2,
                          "TEXCOORD_0": 3, "TEXCOORD_1": 4},
            "indices": 5, "material": 0, "mode": 4,
        }]}],
        "materials": [{
            "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                                     "metallicFactor": 0.0, "roughnessFactor": 1.0},
            "normalTexture": {"index": 0, "texCoord": 1, "scale": NORMAL_SCALE},
        }],
        "samplers": [{"magFilter": 9729, "minFilter": 9729,
                       "wrapS": 33071, "wrapT": 33071}],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": image_view, "mimeType": "image/png"}],
        "buffers": [{"byteLength": len(blob)}], "bufferViews": views, "accessors": accessors,
    }
    jraw = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    j = jraw + b" " * ((-len(jraw)) % 4)
    b = align4(blob)
    total = 12 + 8 + len(j) + 8 + len(b)
    glb = (struct.pack("<4sII", b"glTF", 2, total)
           + struct.pack("<I4s", len(j), b"JSON") + j
           + struct.pack("<I4s", len(b), b"BIN\0") + b)
    SOURCE_GLB.write_bytes(glb)
    if sha(SOURCE_GLB) != "44f8945a73194eae5520cd5cc8d5a0e40c420455340d70d9c0210194ff309d93":
        raise AssertionError("varying-frame fixture GLB SHA changed")
    return positions.astype(np.float32), normals.astype(np.float32), source_tangents.astype(np.float32), atlas_uv.astype(np.float32), source_uv.astype(np.float32)


positions_expected, normals_expected, tangents_expected, atlas_uv_expected, source_uv_expected = make_source_fixture()

# Import only after the explicit CPU flag is visible to Comfy's device selector.
sys.argv = [sys.argv[0], "--cpu"]
import comfy.options
comfy.options.args_parsing = True
from comfy_api.latest import Types
from comfy_extras.mesh3d.fileio import gltf_read
from comfy_extras.nodes_mesh_io import _merge_primitives
from comfy_extras.nodes_mesh_postprocess import (
    ApplyTextureToMesh, BakeNormalMapFromMesh, _rasterize_uv_barycentric,
    _vertex_tangents_for_item,
)
from comfy_extras.nodes_save_3d import mesh_item_to_glb_bytes
import comfy.model_management
comfy.model_management.get_torch_device = lambda: torch.device("cpu")


warnings: list[dict] = []


def warn(key, message):
    warnings.append({"key": key, "message": message})


source_gltf, source_buffers, source_primitives = gltf_read.load_gltf(SOURCE_GLB.read_bytes(), None, warn)
if len(source_primitives) != 1:
    raise AssertionError(f"expected 1 GLB primitive, got {len(source_primitives)}")
source_primitive = source_gltf["meshes"][0]["primitives"][0]
source_uv_raw, source_uv_normalized = gltf_read.read_accessor(
    source_gltf, source_buffers, source_primitive["attributes"]["TEXCOORD_1"]
)
source_uv_parsed = gltf_read.to_float(source_uv_raw, source_uv_normalized)
merged = _merge_primitives(source_primitives)
material = gltf_read.extract_material(source_gltf, source_buffers, None, 0, warn)
raw_normal_map = material["normal_map"]
source_scale = float(material["material"]["normal_scale"])
source_image = np.asarray(Image.open(INPUT / "source-normal-raw-rgb.png").convert("RGB"), dtype=np.float32) / 255.0
if not np.array_equal(raw_normal_map, source_image):
    raise AssertionError("gltf_read normal map decode changed raw RGB PNG values")
roundtrip_metrics = {}
for key, expected in (("vertices", positions_expected), ("normals", normals_expected),
                      ("tangents", tangents_expected), ("uvs", atlas_uv_expected)):
    actual = merged[key]
    if key in ("vertices", "uvs"):
        if not np.array_equal(actual, expected):
            raise AssertionError(f"GLTF parser changed {key} (strict byte-value comparison)")
        roundtrip_metrics[key] = {"strict_equal": True}
    else:
        ncomp = 3
        expected_xyz = expected[:, :ncomp].astype(np.float64)
        actual_xyz = actual[:, :ncomp].astype(np.float64)
        expected_len = np.linalg.norm(expected_xyz, axis=1)
        actual_len = np.linalg.norm(actual_xyz, axis=1)
        expected_dir = expected_xyz / np.maximum(expected_len[:, None], 1e-12)
        actual_dir = actual_xyz / np.maximum(actual_len[:, None], 1e-12)
        angle_deg = np.degrees(np.arccos(np.clip(np.sum(expected_dir * actual_dir, axis=1), -1.0, 1.0)))
        length_delta = np.abs(expected_len - actual_len)
        roundtrip_metrics[key] = {
            "max_direction_delta_degrees": float(angle_deg.max()),
            "max_length_delta": float(length_delta.max()),
            "parser_normalizes_attributes": True,
            "tolerance": {"direction_degrees": 0.02, "length": 1e-5},
        }
        if float(angle_deg.max()) > 0.02 or float(length_delta.max()) > 1e-5:
            raise AssertionError(f"GLTF parser materially changed {key}: {roundtrip_metrics[key]}")
        if key == "tangents" and not np.array_equal(actual[:, 3], expected[:, 3]):
            raise AssertionError("GLTF parser changed TANGENT.w (strict exact comparison)")
if not np.array_equal(source_uv_parsed, source_uv_expected):
    raise AssertionError("direct TEXCOORD_1 accessor read changed UV values")
faces = merged["faces"].astype(np.int64)
if faces.tolist() != [[0, 1, 2], [3, 4, 5]]:
    raise AssertionError(f"unexpected source faces: {faces.tolist()}")
if source_scale != NORMAL_SCALE:
    raise AssertionError(f"normalTexture.scale changed: {source_scale}")
if not np.allclose(merged["tangents"][faces, 3], np.array([[1, 1, 1], [-1, -1, -1]]), atol=1e-6):
    raise AssertionError("source w must remain constant +1/-1 per face")
if np.max(np.linalg.norm(normals_expected[0] - normals_expected[1:], axis=1)) < 0.03:
    raise AssertionError("fixture normals did not vary enough")
if np.max(np.linalg.norm(tangents_expected[0, :3] - tangents_expected[1:, :3], axis=1)) < 0.02:
    raise AssertionError("fixture tangents did not vary enough")

v = torch.from_numpy(np.ascontiguousarray(merged["vertices"])).float()
f = torch.from_numpy(np.ascontiguousarray(faces)).long()
n = torch.from_numpy(np.ascontiguousarray(merged["normals"])).float()
uv0 = torch.from_numpy(np.ascontiguousarray(merged["uvs"])).float()
source_t = torch.from_numpy(np.ascontiguousarray(merged["tangents"])).float()
target_n, target_t = _vertex_tangents_for_item(v, f, uv0, n, torch.device("cpu"))
low_mesh = Types.MESH(
    vertices=v.unsqueeze(0), faces=f.unsqueeze(0), uvs=uv0.unsqueeze(0),
    normals=target_n.unsqueeze(0), tangents=target_t.unsqueeze(0),
    material={"normal_scale": 1.0},
)
high_mesh = Types.MESH(
    vertices=v.unsqueeze(0), faces=f.unsqueeze(0), uvs=uv0.unsqueeze(0),
    normals=n.unsqueeze(0), tangents=source_t.unsqueeze(0),
)
source_uv_tensor = torch.from_numpy(np.ascontiguousarray(source_uv_parsed)).float().unsqueeze(0)
bake_out = BakeNormalMapFromMesh.execute(
    low_mesh, high_mesh, RESOLUTION, cage_distance=0.05, ignore_backfaces=True,
    source_uvs=source_uv_tensor, source_normal_map=raw_normal_map,
    source_normal_scale=source_scale,
)
baked = bake_out.result[0]
if tuple(baked.shape) != (1, RESOLUTION, RESOLUTION, 3):
    raise AssertionError(f"unexpected baked output shape {tuple(baked.shape)}")
Image.fromarray(np.clip(np.rint(baked[0].numpy() * 255), 0, 255).astype(np.uint8), "RGB").save(BAKED_PNG)

apply_out = ApplyTextureToMesh.execute(
    low_mesh, base_color=torch.ones((1, 4, 4, 3), dtype=torch.float32), normal_map=baked,
)
target_mesh = apply_out.result[0]
target_bytes = mesh_item_to_glb_bytes(target_mesh, 0, metadata={"purpose": "private CPU normal-map rebake proof"})
if target_bytes is None:
    raise AssertionError("target GLB serialization returned None")
TARGET_GLB.write_bytes(target_bytes)

# Re-read the actual serialized source and target. Compare interior texels under two explicit frame
# interpolation hypotheses: the overlay's re-orthogonalized interpolated N/T, and a shader-like
# frame that interpolates per-vertex bitangents before normalization.
target_gltf, target_buffers, target_primitives = gltf_read.load_gltf(TARGET_GLB.read_bytes(), None, warn)
target_material = gltf_read.extract_material(target_gltf, target_buffers, None, 0, warn)
target_raw_map = target_material["normal_map"]
target_primitive = target_gltf["meshes"][0]["primitives"][0]
target_merged = _merge_primitives(target_primitives)
target_texcoord_set = target_gltf["materials"][0]["normalTexture"].get("texCoord", 0)
target_scale = float(target_material["material"].get("normal_scale", 1.0))
if target_texcoord_set != 0 or abs(target_scale - 1.0) > 1e-8:
    raise AssertionError(f"target must use atlas UV0 and baked scale 1, got uv{target_texcoord_set}/scale {target_scale}")
if target_merged["tangents"] is None:
    raise AssertionError("target GLB lost its target TANGENT attribute")
if not np.array_equal(target_merged["vertices"], merged["vertices"]):
    raise AssertionError("target serialization changed geometry")
if not np.array_equal(target_merged["faces"], merged["faces"]):
    raise AssertionError("target serialization changed faces")


def sample_linear_clamp(img: np.ndarray, uv: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    x = uv[:, 0] * w - 0.5
    y = uv[:, 1] * h - 0.5
    x0f, y0f = np.floor(x), np.floor(y)
    tx, ty = (x - x0f)[:, None], (y - y0f)[:, None]
    x0 = np.clip(x0f.astype(np.int64), 0, w - 1); x1 = np.clip(x0f.astype(np.int64) + 1, 0, w - 1)
    y0 = np.clip(y0f.astype(np.int64), 0, h - 1); y1 = np.clip(y0f.astype(np.int64) + 1, 0, h - 1)
    a = img[y0, x0] * (1 - tx) + img[y0, x1] * tx
    b = img[y1, x0] * (1 - tx) + img[y1, x1] * tx
    return a * (1 - ty) + b * ty


face_idx_t, bary_t, mask_t = _rasterize_uv_barycentric(faces, atlas_uv_expected, RESOLUTION)
face_idx = face_idx_t.cpu().numpy()
bary = bary_t.cpu().numpy()
mask = mask_t.cpu().numpy()
atlas_y, atlas_x = np.mgrid[0:RESOLUTION, 0:RESOLUTION]
atlas_centers = np.stack(((atlas_x + 0.5) / RESOLUTION, (atlas_y + 0.5) / RESOLUTION), axis=-1)
source_attrs = source_gltf["meshes"][0]["primitives"][0]["attributes"]
source_normals = gltf_read.to_float(*gltf_read.read_accessor(source_gltf, source_buffers, source_attrs["NORMAL"]))
source_tangents_read = gltf_read.to_float(*gltf_read.read_accessor(source_gltf, source_buffers, source_attrs["TANGENT"]))
target_normals_read = gltf_read.to_float(*gltf_read.read_accessor(target_gltf, target_buffers, target_primitive["attributes"]["NORMAL"]))
target_tangents_read = gltf_read.to_float(*gltf_read.read_accessor(target_gltf, target_buffers, target_primitive["attributes"]["TANGENT"]))

metrics = []
def unit_rows(v):
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)


def summarize_angles(angles):
    return {"mean": float(angles.mean()), "median": float(np.median(angles)),
            "p95": float(np.percentile(angles, 95)), "max": float(angles.max())}


for face in range(2):
    roi = mask & (face_idx == face) & (bary.min(axis=-1) >= 0.15)
    ys, xs = np.where(roi)
    if len(xs) < 100:
        raise AssertionError(f"too few interior pixels for face {face}: {len(xs)}")
    b = bary[ys, xs]
    tri = faces[face]
    uv_source_hit = np.einsum("ni,ij->nj", b, source_uv_parsed[tri])
    source_rgb = sample_linear_clamp(raw_normal_map, uv_source_hit)
    source_ts = source_rgb[:, :3] * 2.0 - 1.0
    source_ts[:, :2] *= source_scale
    source_ts /= np.maximum(np.linalg.norm(source_ts, axis=1, keepdims=True), 1e-12)
    src_n_tri = source_normals[tri].astype(np.float64)
    src_t_tri = source_tangents_read[tri, :3].astype(np.float64)
    src_w_tri = source_tangents_read[tri, 3].astype(np.float64)
    sw = float(src_w_tri[0])
    if not np.allclose(src_w_tri, sw, atol=1e-6):
        raise AssertionError(f"source TANGENT.w changes inside face {face}")
    src_n_overlay = unit_rows(np.einsum("ni,ij->nj", b, src_n_tri))
    src_t_overlay = np.einsum("ni,ij->nj", b, src_t_tri)
    src_t_overlay = unit_rows(src_t_overlay - src_n_overlay * np.sum(src_n_overlay * src_t_overlay, axis=1, keepdims=True))
    src_b_overlay = sw * np.cross(src_n_overlay, src_t_overlay)
    source_world_overlay = unit_rows(
        source_ts[:, 0:1] * src_t_overlay + source_ts[:, 1:2] * src_b_overlay + source_ts[:, 2:3] * src_n_overlay
    )
    src_b_vertices = src_w_tri[:, None] * np.cross(src_n_tri, src_t_tri)
    src_n_three = unit_rows(np.einsum("ni,ij->nj", b, src_n_tri))
    src_t_three = unit_rows(np.einsum("ni,ij->nj", b, src_t_tri))
    src_b_three = unit_rows(np.einsum("ni,ij->nj", b, src_b_vertices))
    source_world_three = unit_rows(
        source_ts[:, 0:1] * src_t_three + source_ts[:, 1:2] * src_b_three + source_ts[:, 2:3] * src_n_three
    )

    target_uv_hit = atlas_centers[ys, xs]
    target_rgb = sample_linear_clamp(target_raw_map, target_uv_hit)
    target_ts = target_rgb[:, :3] * 2.0 - 1.0
    target_ts[:, :2] *= target_scale
    target_ts /= np.maximum(np.linalg.norm(target_ts, axis=1, keepdims=True), 1e-12)
    tgt_n_tri = target_normals_read[tri].astype(np.float64)
    tgt_t_tri = target_tangents_read[tri, :3].astype(np.float64)
    tgt_w_tri = target_tangents_read[tri, 3].astype(np.float64)
    tw = float(tgt_w_tri[0])
    if not np.allclose(tgt_w_tri, tw, atol=1e-6):
        raise AssertionError(f"target TANGENT.w changes inside face {face}")
    tgt_n_overlay = unit_rows(np.einsum("ni,ij->nj", b, tgt_n_tri))
    tgt_t_overlay = np.einsum("ni,ij->nj", b, tgt_t_tri)
    tgt_t_overlay = unit_rows(tgt_t_overlay - tgt_n_overlay * np.sum(tgt_n_overlay * tgt_t_overlay, axis=1, keepdims=True))
    tgt_b_overlay = tw * np.cross(tgt_n_overlay, tgt_t_overlay)
    target_world_overlay = unit_rows(
        target_ts[:, 0:1] * tgt_t_overlay + target_ts[:, 1:2] * tgt_b_overlay + target_ts[:, 2:3] * tgt_n_overlay
    )
    tgt_b_vertices = tgt_w_tri[:, None] * np.cross(tgt_n_tri, tgt_t_tri)
    tgt_n_three = unit_rows(np.einsum("ni,ij->nj", b, tgt_n_tri))
    tgt_t_three = unit_rows(np.einsum("ni,ij->nj", b, tgt_t_tri))
    tgt_b_three = unit_rows(np.einsum("ni,ij->nj", b, tgt_b_vertices))
    target_world_three = unit_rows(
        target_ts[:, 0:1] * tgt_t_three + target_ts[:, 1:2] * tgt_b_three + target_ts[:, 2:3] * tgt_n_three
    )
    angles_overlay = np.degrees(np.arccos(np.clip(np.sum(source_world_overlay * target_world_overlay, axis=1), -1.0, 1.0)))
    angles_three_model = np.degrees(np.arccos(np.clip(np.sum(source_world_three * target_world_three, axis=1), -1.0, 1.0)))
    # Fixture-specific bound includes PNG quantization; neither hypothesis is a general guarantee.
    for label, values in (("overlay", angles_overlay), ("vertex-B", angles_three_model)):
        if not np.isfinite(values).all() or float(values.max()) > 1.5:
            raise AssertionError(f"face {face}: {label} error exceeds 1.5° or is non-finite")
    src_n_angles = np.degrees(np.arccos(np.clip(src_n_tri @ src_n_tri.T, -1.0, 1.0)))
    src_t_angles = np.degrees(np.arccos(np.clip(src_t_tri @ src_t_tri.T, -1.0, 1.0)))
    metrics.append({
        "face": face,
        "source_tangent_w": sw,
        "target_tangent_w": tw,
        "interior_pixels": int(len(xs)),
        "source_vertex_normal_pairwise_span_degrees": float(src_n_angles.max()),
        "source_vertex_tangent_pairwise_span_degrees": float(src_t_angles.max()),
        "source_uv1_bounds": [source_uv_parsed[tri].min(0).tolist(), source_uv_parsed[tri].max(0).tolist()],
        "target_uv0_bounds": [atlas_uv_expected[tri].min(0).tolist(), atlas_uv_expected[tri].max(0).tolist()],
        "world_normal_angle_error_degrees_overlay_interpolated_NT": summarize_angles(angles_overlay),
        "world_normal_angle_error_degrees_vertex_B_interpolation_hypothesis": summarize_angles(angles_three_model),
    })

report = {
    "runtime": {"python": sys.version.split()[0], "torch": str(torch.__version__), "device": "CPU",
                "network": "bwrap --unshare-net", "comfy_operator": "private overlay only"},
    "source": {"path": str(SOURCE_GLB.relative_to(ROOT)), "sha256": sha(SOURCE_GLB),
               "image_path": str((INPUT / "source-normal-raw-rgb.png").relative_to(ROOT)),
               "image_sha256": sha(INPUT / "source-normal-raw-rgb.png"), "normal_scale": source_scale,
               "normal_texcoord": 1, "sampler": {"magFilter": "LINEAR", "minFilter": "LINEAR",
                                                 "wrapS": "CLAMP_TO_EDGE", "wrapT": "CLAMP_TO_EDGE"}},
    "target": {"path": str(TARGET_GLB.relative_to(ROOT)), "sha256": sha(TARGET_GLB),
               "baked_png_path": str(BAKED_PNG.relative_to(ROOT)), "baked_png_sha256": sha(BAKED_PNG),
               "normal_texcoord": target_texcoord_set, "normal_scale": target_scale,
               "vertices": int(target_merged["vertices"].shape[0]), "triangles": int(target_merged["faces"].shape[0])},
    "fixture": {"vertices": 6, "triangles": 2, "corner_duplicated": True,
                "source_tangent_w_per_triangle": [1.0, -1.0], "target_tangent_w_per_triangle": [
                    float(target_tangents_read[0, 3]), float(target_tangents_read[3, 3])],
                "curved_geometry": True, "normals_vary_per_vertex": True, "tangent_xyz_varies_per_vertex": True,
                "texcoord_0_atlas_and_texcoord_1_source_are_distinct": True,
                "all_uvs_in_unit_square": True, "real_source_png_normal_map": True,
                "normal_map_rgb_is_sampled_raw_linear_values_without_srgb_transfer": True,
                "normal_map_uses_asymmetric_xy_variation": True,
                "remesh_decimate_weld_unwrap": False},
    "source_attribute_roundtrip": roundtrip_metrics,
    "operator": {"path": "BakeNormalMapFromMesh.execute on copied overlay, then ApplyTextureToMesh.execute on copied overlay",
                 "source_tangent_preserved_as_input": True,
                 "source_normal_map_sampled_at_barycentric_hit_uv1": True,
                 "source_frame": "overlay: interpolate N/T at high hit, orthonormalize T against N, then B=w*cross(N,T)",
                 "normal_scale_applied_to_decoded_XY_before_normalization": True,
                 "target_frame": "per-texel from target mesh TANGENT at atlas UV0",
                 "expected_parser_warning": warnings},
    "measurements": metrics,
    "limits": [
        "Synthetic curved two-triangle fixture; N/T vary by vertex but w remains constant per triangle. Mixed w within a triangle is excluded because it violates the glTF tangent frame constraint.",
        "All UVs are inside [0,1], sampler is LINEAR + CLAMP_TO_EDGE; repeat, UVs outside the unit square, UDIM, and KHR_texture_transform are not tested.",
        "The alternative per-vertex-B metric is a shader-like hypothesis, not a substitute for the Three.js/SwiftShader reader comparison; inspect the exact measured reader output before interpreting it.",
        "Geometry, UV0, UV1, indices, and TANGENT.w are checked exactly; NORMAL/TANGENT.xyz are reported separately because the reader normalizes them (maximum permitted delta 0.02 degrees and length 1e-5).",
        "No production Comfy source was modified; no shared ComfyUI service was started or contacted; no Apple/Quick Look conclusion is made.",
    ],
}
REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"stage": "complete", "source_glb": str(SOURCE_GLB), "source_sha256": sha(SOURCE_GLB),
                  "target_glb": str(TARGET_GLB), "target_sha256": sha(TARGET_GLB),
                  "report": str(REPORT), "report_sha256": sha(REPORT), "measurements": metrics}, ensure_ascii=False))
