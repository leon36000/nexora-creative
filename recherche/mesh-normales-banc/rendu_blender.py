#!/usr/bin/env python3
"""Reproducible CPU-only Blender import/render comparison for the chair asset.

Run with Blender 5.2.3 in background mode. The script verifies immutable input
hashes, extracts only the two known three-file OBJ bundles, and writes new
reports/renders exclusively. The render stage requires matching imported
geometry bounds and triangle counts before it starts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import struct
import sys
import zipfile


EXPECTED = {
    "glb": {
        "name": "trellis2-draft-gb10-01-chaise.glb",
        "sha256": "227cb2959def0a2b72e0d7c38173fae3cacf08d01a40514b6a9d4d339ff8e509",
        "bytes": 11123980,
    },
    "old_obj_zip": {
        "name": "real-chair-export.zip",
        "sha256": "8cda64887c6385579ba85f241eae7feaab8d23acc76eadba1c4c4f22ea41cab3",
        "bytes": 14309825,
    },
    "new_obj_zip": {
        "name": "chaise-obj-normales-v3.zip",
        "sha256": "66495d710fb54fba10c0d2ee770071c7245d0e674e60ebb0ac72d8e20f82d05d",
        "bytes": 19936936,
    },
}
EXPECTED_TRIANGLES = 149942
ZIP_MEMBERS = {"chaise.obj", "chaise.mtl", "chaise.png"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with path.open("x", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())


def verify_input(path: Path, key: str) -> dict:
    expected = EXPECTED[key]
    if path.name != expected["name"]:
        raise RuntimeError(f"unexpected input name for {key}: {path.name}")
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"missing or symlink input: {path}")
    actual_size = path.stat().st_size
    actual_sha = sha256_file(path)
    if actual_size != expected["bytes"] or actual_sha != expected["sha256"]:
        raise RuntimeError(f"input identity mismatch: {key}")
    return {"path": str(path), "bytes": actual_size, "sha256": actual_sha}


def safe_extract_zip(zip_path: Path, out_dir: Path, key: str) -> dict:
    verify_input(zip_path, key)
    if out_dir.exists():
        raise RuntimeError(f"extraction destination already exists: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    extracted = []
    with zipfile.ZipFile(zip_path) as archive:
        names = [i.filename for i in archive.infolist()]
        if set(names) != ZIP_MEMBERS or len(names) != len(ZIP_MEMBERS):
            raise RuntimeError(f"unexpected ZIP members: {names}")
        for info in archive.infolist():
            rel = PurePosixPath(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if rel.is_absolute() or ".." in rel.parts or len(rel.parts) != 1 or mode == 0o120000:
                raise RuntimeError(f"unsafe ZIP member: {info.filename}")
            target = out_dir / rel.name
            with archive.open(info) as src, target.open("xb") as dst:
                while True:
                    block = src.read(1024 * 1024)
                    if not block:
                        break
                    dst.write(block)
                dst.flush()
                os.fsync(dst.fileno())
            extracted.append({"name": rel.name, "bytes": target.stat().st_size, "sha256": sha256_file(target)})
    return {"zip": str(zip_path), "extracted_dir": str(out_dir), "files": extracted}


def args_after_double_dash() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("prepare", "import-check", "import-check-v5", "diagnostic", "preserve-probe", "render"), required=True)
    parser.add_argument("--run-root", required=True, type=Path)
    return parser.parse_args(argv)


def prepare(root: Path) -> dict:
    input_dir = root / "inputs"
    extracted_dir = root / "extracted"
    inputs = {
        "glb": verify_input(input_dir / EXPECTED["glb"]["name"], "glb"),
        "old_obj_zip": verify_input(input_dir / EXPECTED["old_obj_zip"]["name"], "old_obj_zip"),
        "new_obj_zip": verify_input(input_dir / EXPECTED["new_obj_zip"]["name"], "new_obj_zip"),
    }
    extracted_dir.mkdir(parents=True, exist_ok=True)
    old = safe_extract_zip(input_dir / EXPECTED["old_obj_zip"]["name"], extracted_dir / "old_obj", "old_obj_zip")
    new = safe_extract_zip(input_dir / EXPECTED["new_obj_zip"]["name"], extracted_dir / "new_obj_v3", "new_obj_zip")
    return {"stage": "prepare", "inputs": inputs, "extractions": {"old_obj": old, "new_obj_v3": new}}


def object_meshes():
    import bpy  # pylint: disable=import-outside-toplevel

    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def read_glb_accessor(doc: dict, binary: bytes, accessor_index: int, expected_type: str | None = None) -> list:
    accessor = doc["accessors"][accessor_index]
    if "sparse" in accessor:
        raise RuntimeError("sparse glTF accessors are outside this fixed input contract")
    if accessor.get("bufferView") is None:
        raise RuntimeError("glTF accessor has no bufferView")
    view = doc["bufferViews"][accessor["bufferView"]]
    if view.get("buffer", 0) != 0:
        raise RuntimeError("glTF input references a nonzero buffer")
    fmt_by_component = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}
    n_by_type = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    component = accessor["componentType"]
    kind = accessor["type"]
    if component not in fmt_by_component or kind not in n_by_type:
        raise RuntimeError(f"unsupported glTF accessor type: {component}/{kind}")
    if expected_type is not None and kind != expected_type:
        raise RuntimeError(f"unexpected glTF accessor shape: {kind}, wanted {expected_type}")
    fmt = fmt_by_component[component]
    width = n_by_type[kind]
    element_bytes = struct.calcsize("<" + fmt) * width
    stride = view.get("byteStride", element_bytes)
    if stride < element_bytes:
        raise RuntimeError("glTF bufferView stride smaller than accessor element")
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    count = accessor["count"]
    end = start + (count - 1) * stride + element_bytes if count else start
    if start < 0 or end > len(binary) or end > view.get("byteOffset", 0) + view["byteLength"]:
        raise RuntimeError("glTF accessor range exceeds its bufferView")
    unpack = struct.Struct("<" + fmt * width).unpack_from
    result = [unpack(binary, start + i * stride) for i in range(count)]
    if component == 5126 and any(not math.isfinite(value) for row in result for value in row):
        raise RuntimeError("glTF accessor has non-finite float data")
    return result


def make_glb_mesh_exact(filepath: Path):
    """Build the known GLB primitive without Blender mesh.validate deduplication."""
    import bpy  # pylint: disable=import-outside-toplevel

    raw = filepath.read_bytes()
    if len(raw) < 20:
        raise RuntimeError("truncated GLB header")
    magic, version, declared_length = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(raw):
        raise RuntimeError("invalid GLB header/declared length")
    json_chunk = None
    binary = None
    offset = 12
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise RuntimeError("truncated GLB chunk header")
        chunk_len, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        if offset + chunk_len > len(raw):
            raise RuntimeError("GLB chunk length exceeds file")
        chunk = raw[offset : offset + chunk_len]
        offset += chunk_len
        if chunk_type == 0x4E4F534A:
            json_chunk = chunk
        elif chunk_type == 0x004E4942:
            binary = chunk
    if json_chunk is None or binary is None:
        raise RuntimeError("GLB JSON or BIN chunk missing")
    doc = json.loads(json_chunk.decode("utf-8").rstrip(" \t\r\n\0"))
    if doc.get("asset", {}).get("version") != "2.0" or len(doc.get("meshes", [])) != 1:
        raise RuntimeError("GLB outside one-mesh glTF 2.0 contract")
    nodes = doc.get("nodes", [])
    if len(nodes) != 1 or nodes[0].get("mesh") != 0:
        raise RuntimeError("GLB outside one-node/one-mesh contract")
    if any(k in nodes[0] for k in ("matrix", "translation", "rotation", "scale")):
        raise RuntimeError("GLB node transform not supported by exact-array builder")
    primitives = doc["meshes"][0].get("primitives", [])
    if len(primitives) != 1 or primitives[0].get("mode", 4) != 4:
        raise RuntimeError("GLB outside one-triangle-primitive contract")
    primitive = primitives[0]
    attrs = primitive.get("attributes", {})
    if not all(key in attrs for key in ("POSITION", "NORMAL", "TEXCOORD_0")) or "indices" not in primitive:
        raise RuntimeError("GLB lacks required indexed position/normal/UV attributes")
    positions = read_glb_accessor(doc, binary, attrs["POSITION"], "VEC3")
    normals = read_glb_accessor(doc, binary, attrs["NORMAL"], "VEC3")
    texcoords = read_glb_accessor(doc, binary, attrs["TEXCOORD_0"], "VEC2")
    indices_rows = read_glb_accessor(doc, binary, primitive["indices"], "SCALAR")
    if len(positions) != len(normals) or len(positions) != len(texcoords):
        raise RuntimeError("GLB position/normal/UV counts differ")
    indices = [row[0] for row in indices_rows]
    if len(indices) != EXPECTED_TRIANGLES * 3 or len(indices) % 3:
        raise RuntimeError("GLB index count does not match source triangle contract")
    if any(index < 0 or index >= len(positions) for index in indices):
        raise RuntimeError("GLB index out of position range")
    # The Blender glTF importer calls mesh.validate(), which removes one
    # opposite-winding duplicate from this source. Preserve the input face list
    # and convert glTF Y-up to Blender Z-up using the importer-observed mapping.
    blender_positions = [(x, -z, y) for x, y, z in positions]
    blender_normals = [(x, -z, y) for x, y, z in normals]
    faces = [tuple(indices[i : i + 3]) for i in range(0, len(indices), 3)]
    mesh = bpy.data.meshes.new("ChairGLBSourceArrays")
    mesh.from_pydata(blender_positions, [], faces)
    if len(mesh.polygons) != EXPECTED_TRIANGLES:
        raise RuntimeError(f"Blender from_pydata did not preserve GLB faces: {len(mesh.polygons)}")
    mesh.update(calc_edges=True)
    for poly in mesh.polygons:
        poly.use_smooth = True
    uv_layer = mesh.uv_layers.new(name="TEXCOORD_0")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = texcoords[vertex_index]
    # Set per-corner normals last. The source has one zero vertex normal used by
    # two opposite-winding faces; fill only those two corners with their own
    # geometric face normal, keeping every valid source normal unchanged.
    loop_normals = [None] * len(mesh.loops)
    repaired_zero_corners = []
    for poly in mesh.polygons:
        loop_ids = list(poly.loop_indices)
        if len(loop_ids) != 3:
            raise RuntimeError("GLB source unexpectedly produced a non-triangle face")
        points = [mesh.vertices[mesh.loops[li].vertex_index].co for li in loop_ids]
        face_normal = (points[1] - points[0]).cross(points[2] - points[0])
        if face_normal.length <= 1e-20:
            raise RuntimeError("GLB source has a zero-area face")
        face_normal.normalize()
        for li in loop_ids:
            vertex_index = mesh.loops[li].vertex_index
            if all(value == 0 for value in normals[vertex_index]):
                loop_normals[li] = tuple(float(x) for x in face_normal)
                repaired_zero_corners.append({"loop": li, "vertex": vertex_index, "face": poly.index, "normal": list(loop_normals[li])})
            else:
                loop_normals[li] = blender_normals[vertex_index]
    if any(value is None for value in loop_normals):
        raise RuntimeError("not all GLB corner normals were assigned")
    mesh.normals_split_custom_set(loop_normals)
    obj = bpy.data.objects.new("ChairGLBSourceArrays", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return {
        "mesh": mesh,
        "object": obj,
        "method": "direct glTF 2.0 accessor reconstruction; preserves duplicate opposite-winding face; glTF Y-up converted to Blender Z-up",
        "source_positions": len(positions),
        "source_indices": len(indices),
        "source_normals_zero_vectors": sum(1 for n in normals if all(x == 0 for x in n)),
        "source_normal_policy": "all nonzero normals transformed Y-up to Blender Z-up; two corners using the one zero vector filled with their geometric face normals",
        "repaired_zero_normal_corners": repaired_zero_corners,
    }


def import_asset(kind: str, root: Path, validate_obj: bool = True) -> dict:
    import bpy  # pylint: disable=import-outside-toplevel

    if kind == "glb":
        filepath = root / "inputs" / EXPECTED["glb"]["name"]
        return make_glb_mesh_exact(filepath)
    else:
        dir_name = "old_obj" if kind == "old_obj" else "new_obj_v3"
        filepath = root / "extracted" / dir_name / "chaise.obj"
        result = bpy.ops.wm.obj_import(
            filepath=str(filepath),
            forward_axis="NEGATIVE_Z",
            up_axis="Y",
            global_scale=1.0,
            use_split_objects=False,
            use_split_groups=False,
            validate_meshes=validate_obj,
        )
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender importer did not finish for {kind}: {result}")
    return {"method": "Blender OBJ importer with validate_meshes=" + str(validate_obj)}


def summarize_scene(kind: str, root: Path) -> dict:
    import bpy  # pylint: disable=import-outside-toplevel
    from mathutils import Vector  # pylint: disable=import-outside-toplevel

    meshes = object_meshes()
    if not meshes:
        raise RuntimeError(f"no mesh objects imported for {kind}")
    tri_count = sum(sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons) for obj in meshes)
    verts = 0
    smooth_faces = 0
    poly_count = 0
    polygon_sizes = {}
    materials = set()
    bounds_min = [math.inf, math.inf, math.inf]
    bounds_max = [-math.inf, -math.inf, -math.inf]
    for obj in meshes:
        verts += len(obj.data.vertices)
        poly_count += len(obj.data.polygons)
        smooth_faces += sum(1 for p in obj.data.polygons if p.use_smooth)
        for p in obj.data.polygons:
            polygon_sizes[len(p.vertices)] = polygon_sizes.get(len(p.vertices), 0) + 1
        materials.update(m.name if m else None for m in obj.data.materials)
        for v in obj.data.vertices:
            p = obj.matrix_world @ v.co
            for i in range(3):
                bounds_min[i] = min(bounds_min[i], float(p[i]))
                bounds_max[i] = max(bounds_max[i], float(p[i]))
    extents = [bounds_max[i] - bounds_min[i] for i in range(3)]
    for obj in meshes:
        obj.data.calc_loop_triangles()
    loop_triangle_count = sum(len(obj.data.loop_triangles) for obj in meshes)
    return {
        "kind": kind,
        "objects": len(meshes),
        "mesh_vertices_total": verts,
        "polygons_total": poly_count,
        "polygon_sizes": {str(k): v for k, v in sorted(polygon_sizes.items())},
        "triangles": tri_count,
        "blender_loop_triangles": loop_triangle_count,
        "smooth_polygons": smooth_faces,
        "materials": sorted("<null>" if x is None else x for x in materials),
        "bounds_world": {"min": bounds_min, "max": bounds_max, "extents": extents},
    }


def import_check(root: Path) -> dict:
    import bpy  # pylint: disable=import-outside-toplevel

    results = []
    for kind in ("glb", "old_obj", "new_obj_v3"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        import_info = import_asset(kind, root, validate_obj=False)
        report = summarize_scene(kind, root)
        report["import_method"] = import_info.get("method")
        for key in ("source_positions", "source_indices", "source_normals_zero_vectors", "source_normal_policy", "repaired_zero_normal_corners"):
            if key in import_info:
                report[key] = import_info[key]
        if report["triangles"] != EXPECTED_TRIANGLES:
            report["triangle_count_matches_expected"] = False
        else:
            report["triangle_count_matches_expected"] = True
        results.append(report)
    reference = results[0]["bounds_world"]
    bound_delta = []
    bounds_match = True
    for report in results[1:]:
        delta = max(
            abs(report["bounds_world"][axis][i] - reference[axis][i])
            for axis in ("min", "max")
            for i in range(3)
        )
        bound_delta.append({"kind": report["kind"], "max_abs_delta_from_glb": delta})
        if delta > 1e-4:
            bounds_match = False
    result = {
        "stage": "import-check",
        "blender_version": bpy.app.version_string,
        "background": bpy.app.background,
        "cycles_build_option": bool(bpy.app.build_options.cycles),
        "expected_triangles_each": EXPECTED_TRIANGLES,
        "assets": results,
        "bounds_comparison": bound_delta,
        "bounds_match_within_1e-4": bounds_match,
        "all_triangle_counts_match": all(x["triangle_count_matches_expected"] for x in results),
        "render_authorized_by_script": bounds_match and all(x["triangle_count_matches_expected"] for x in results),
        "limits": ["Blender structural import and CPU setup only", "no aesthetic rating", "no simplification"],
    }
    return result


def diagnostic(root: Path) -> dict:
    """Inspect all importers without authorizing a render, even on mismatches."""
    import bpy  # pylint: disable=import-outside-toplevel

    results = []
    for kind in ("glb", "old_obj", "new_obj_v3"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        import_info = import_asset(kind, root, validate_obj=True)
        report = summarize_scene(kind, root)
        report["import_method"] = import_info.get("method")
        report["triangle_count_matches_expected"] = report["triangles"] == EXPECTED_TRIANGLES
        results.append(report)
    reference = results[0]["bounds_world"]
    bound_delta = []
    for report in results[1:]:
        delta = max(abs(report["bounds_world"][axis][i] - reference[axis][i]) for axis in ("min", "max") for i in range(3))
        bound_delta.append({"kind": report["kind"], "max_abs_delta_from_glb": delta})
    return {
        "stage": "diagnostic",
        "blender_version": bpy.app.version_string,
        "assets": results,
        "bounds_comparison": bound_delta,
        "render_authorized": False,
        "purpose": "diagnostic import accounting only; no visual comparison performed",
    }


def preserve_probe(root: Path) -> dict:
    """Test Blender's documented OBJ validation switch; never authorizes render."""
    import bpy  # pylint: disable=import-outside-toplevel

    results = []
    for kind in ("glb", "old_obj", "new_obj_v3"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        import_info = import_asset(kind, root, validate_obj=False)
        report = summarize_scene(kind, root)
        report["import_method"] = import_info.get("method")
        report["triangle_count_matches_expected"] = report["triangles"] == EXPECTED_TRIANGLES
        results.append(report)
    prop = bpy.ops.wm.obj_import.get_rna_type().properties["validate_meshes"]
    return {
        "stage": "preserve-probe",
        "blender_version": bpy.app.version_string,
        "obj_validate_meshes": False,
        "obj_validate_meshes_description": prop.description,
        "assets": results,
        "render_authorized": False,
    }


def apply_neutral_material(meshes) -> None:
    import bpy  # pylint: disable=import-outside-toplevel

    mat = bpy.data.materials.new("NexoraNeutralComparison")
    mat.diffuse_color = (0.48, 0.50, 0.54, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.48, 0.50, 0.54, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.68
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(mat)


def point_camera(obj, target) -> None:
    from mathutils import Vector  # pylint: disable=import-outside-toplevel

    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene(root: Path, kind: str) -> dict:
    import bpy  # pylint: disable=import-outside-toplevel
    from mathutils import Vector  # pylint: disable=import-outside-toplevel

    bpy.ops.wm.read_factory_settings(use_empty=True)
    import_info = import_asset(kind, root, validate_obj=False)
    meshes = object_meshes()
    summary = summarize_scene(kind, root)
    summary["import_method"] = import_info.get("method")
    for key in ("source_positions", "source_indices", "source_normals_zero_vectors", "source_normal_policy", "repaired_zero_normal_corners"):
        if key in import_info:
            summary[key] = import_info[key]
    if summary["triangles"] != EXPECTED_TRIANGLES:
        raise RuntimeError(f"triangle count mismatch for render {kind}: {summary['triangles']}")
    # Reuse one camera/light rig derived from the same bounds across all formats.
    # Bounds have already been checked against the GLB by import-check.
    bounds = summary["bounds_world"]
    center = [(bounds["min"][i] + bounds["max"][i]) / 2 for i in range(3)]
    diagonal = math.sqrt(sum(x * x for x in bounds["extents"]))
    apply_neutral_material(meshes)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.seed = 0
    scene.cycles.use_animated_seed = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("NexoraNeutralComparisonWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.055, 0.055, 0.055, 1.0)
    background.inputs["Strength"].default_value = 0.8
    camera_data = bpy.data.cameras.new("ComparisonCamera")
    camera = bpy.data.objects.new("ComparisonCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = Vector((center[0] + diagonal * 1.35, center[1] - diagonal * 1.8, center[2] + diagonal * 1.05))
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(bounds["extents"]) * 1.55
    point_camera(camera, center)
    scene.camera = camera
    # Three broad area sources, positioned relative to the same asset bounds.
    light_specs = [
        ("Key", (1.5, -1.2, 2.0), 950.0, diagonal * 0.9),
        ("Fill", (-1.6, -0.4, 0.7), 520.0, diagonal * 0.8),
        ("Rim", (0.2, 1.8, 1.3), 760.0, diagonal * 0.7),
    ]
    for name, rel, power, size in light_specs:
        data = bpy.data.lights.new(name, type="AREA")
        data.energy = power
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = Vector((center[0] + rel[0] * diagonal, center[1] + rel[1] * diagonal, center[2] + rel[2] * diagonal))
        point_camera(light, center)
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.color_mode = "RGBA"
    return summary


def render(root: Path) -> dict:
    import bpy  # pylint: disable=import-outside-toplevel

    out_dir = root / "renders"
    if not out_dir.is_dir():
        raise RuntimeError(f"render output directory missing: {out_dir}")
    import_report_path = root / "import-check-v5-report.json"
    if not import_report_path.is_file():
        raise RuntimeError("render refused: successful import-check report is absent")
    with import_report_path.open("r", encoding="utf-8") as f:
        import_report = json.load(f)
    if import_report.get("stage") not in ("import-check", "import-check-v5") or len(import_report.get("assets", [])) != 3:
        raise RuntimeError("render refused: malformed import-check report")
    if any(item.get("triangles") != EXPECTED_TRIANGLES for item in import_report["assets"]):
        raise RuntimeError("render refused: import-check triangle counts do not match")
    if any(item.get("max_abs_delta_from_glb", math.inf) > 1e-4 for item in import_report.get("bounds_comparison", [])):
        raise RuntimeError("render refused: import-check bounds do not match")
    if not bpy.app.build_options.cycles:
        raise RuntimeError("Cycles CPU unavailable in this Blender build")
    outputs = []
    for kind, filename in (("glb", "chair-glb-neutral.png"), ("old_obj", "chair-old-obj-neutral.png"), ("new_obj_v3", "chair-normales-v3-neutral.png")):
        target = out_dir / filename
        if target.exists() or target.is_symlink():
            raise RuntimeError(f"refusing to overwrite render: {target}")
        summary = setup_scene(root, kind)
        scene = bpy.context.scene
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError(f"render output missing or empty: {target}")
        outputs.append({"kind": kind, "path": str(target), "bytes": target.stat().st_size, "sha256": sha256_file(target), "triangles": summary["triangles"], "resolution": [scene.render.resolution_x, scene.render.resolution_y], "samples": scene.cycles.samples, "threads": scene.render.threads})
    return {"stage": "render", "blender_version": bpy.app.version_string, "engine": "Cycles CPU", "gpu_requested": False, "outputs": outputs}


def main() -> int:
    opts = args_after_double_dash()
    root = opts.run_root.resolve(strict=True)
    if opts.stage == "prepare":
        report = prepare(root)
    elif opts.stage == "import-check":
        report = import_check(root)
    elif opts.stage == "import-check-v5":
        report = import_check(root)
        report["stage"] = "import-check-v5"
    elif opts.stage == "diagnostic":
        report = diagnostic(root)
    elif opts.stage == "preserve-probe":
        report = preserve_probe(root)
    else:
        report = render(root)
    report_path = root / f"{opts.stage}-report.json"
    write_json_exclusive(report_path, report)
    print(json.dumps({"stage": opts.stage, "report": str(report_path), "status": "complete"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
