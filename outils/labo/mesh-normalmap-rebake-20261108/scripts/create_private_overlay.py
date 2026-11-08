#!/usr/bin/env python3
"""Create a private Comfy operator overlay; never writes to the shared Comfy tree."""
from pathlib import Path
import argparse
import hashlib

EXPECTED_SOURCE_SHA256 = '3b7083984c974d9bc5d14e026a37d0eee0a4063b61a7df20ae15bdd68015a141'
parser = argparse.ArgumentParser(description='Créer une copie privée instrumentée du nœud Comfy Mesh.')
parser.add_argument('--source', type=Path, required=True, help='nodes_mesh_postprocess.py source, épinglé par SHA-256')
parser.add_argument('--output', type=Path, required=True, help='chemin de sortie hors du dépôt, absent au départ')
args = parser.parse_args()
source = args.source.resolve()
overlay = args.output.resolve()
if not source.is_file():
    raise SystemExit(f'Source introuvable: {source}')
source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
if source_sha256 != EXPECTED_SOURCE_SHA256:
    raise SystemExit(f'SHA source inattendu: {source_sha256}; attendu {EXPECTED_SOURCE_SHA256}')
if overlay.exists():
    raise SystemExit('La sortie existe déjà; la préserver et choisir un nouveau dossier de run')
s=source.read_text()
old_sig='''def _bake_normal_map(high_v, high_f, high_n, low_v_np, low_f_np, low_uv_np, low_n, tangents,
                     resolution, cage_distance=0.05, ignore_backfaces=True):'''
new_sig='''def _bake_normal_map(high_v, high_f, high_n, low_v_np, low_f_np, low_uv_np, low_n, tangents,
                     resolution, cage_distance=0.05, ignore_backfaces=True,
                     source_uvs_np=None, source_tangents=None, source_normal_map=None,
                     source_normal_scale=1.0):'''
assert s.count(old_sig)==1
s=s.replace(old_sig,new_sig)
old_doc='''    ignore_backfaces skips surfaces facing away (crevices/enclosures); misses fall back to
    closest-point. Returns [H,W,3] in [0,1]."""
'''
new_doc='''    ignore_backfaces skips surfaces facing away (crevices/enclosures); misses fall back to
    closest-point. Experimental optional source_normal_map path samples raw glTF normal pixels at
    interpolated source_uvs, reconstructs source world normals from interpolated NORMAL/TANGENT
    (with per-triangle constant w), and bakes them into the target frame. Returns [H,W,3] in [0,1]."""
'''
assert s.count(old_doc)==1
s=s.replace(old_doc,new_doc)
needle='''def _bake_normal_map(high_v, high_f, high_n, low_v_np, low_f_np, low_uv_np, low_n, tangents,
'''
helper='''def _sample_gltf_normal_linear_clamp(image01, uv, device):
    """Sample raw, top-left-origin glTF normal PNG values with LINEAR/CLAMP_TO_EDGE."""
    image = torch.from_numpy(np.ascontiguousarray(image01, dtype=np.float32)).to(device)
    h, w = image.shape[:2]
    uv = uv.to(device).float()
    x = uv[:, 0] * float(w) - 0.5
    y = uv[:, 1] * float(h) - 0.5
    x0f, y0f = torch.floor(x), torch.floor(y)
    tx, ty = (x - x0f)[:, None], (y - y0f)[:, None]
    x0 = x0f.long().clamp(0, w - 1); x1 = (x0f.long() + 1).clamp(0, w - 1)
    y0 = y0f.long().clamp(0, h - 1); y1 = (y0f.long() + 1).clamp(0, h - 1)
    a = image[y0, x0] * (1.0 - tx) + image[y0, x1] * tx
    b = image[y1, x0] * (1.0 - tx) + image[y1, x1] * tx
    return a * (1.0 - ty) + b * ty


'''
assert s.count(needle)==1
s=s.replace(needle,helper+needle)
old='''    hv = high_v.to(dev).float()
    hf = high_f.to(device=dev, dtype=torch.int32)
    tri = hv[hf]
'''
new='''    hv = high_v.to(dev).float()
    hf = high_f.to(device=dev, dtype=torch.int32)
    hf_long = hf.to(torch.long)
    use_source_texture = source_normal_map is not None
    if use_source_texture:
        if source_uvs_np is None or source_tangents is None:
            raise ValueError("source normal-map bake requires source UVs and explicit source TANGENT")
        source_uvs = torch.as_tensor(np.ascontiguousarray(source_uvs_np, dtype=np.float32), device=dev)
        source_tangents_t = source_tangents.to(dev).float()
        if source_uvs.shape != (hv.shape[0], 2) or source_tangents_t.shape != (hv.shape[0], 4):
            raise ValueError("source UV/TANGENT attributes must align 1:1 with high-poly vertices")
        source_w = source_tangents_t[hf_long, 3]
        if not torch.allclose(source_w, source_w[:, :1].expand_as(source_w), atol=1e-6, rtol=0.0):
            raise ValueError("glTF source TANGENT.w must be constant at all three corners of each triangle")
        if float(source_normal_scale) < 0.0:
            raise ValueError("source normalTexture.scale must be non-negative")
        if not np.isfinite(source_normal_map).all() or source_normal_map.ndim != 3 or source_normal_map.shape[2] < 3:
            raise ValueError("source normal map must be finite raw RGB values in [0,1]")
    tri = hv[hf]
'''
start=s.index('def _bake_normal_map(')
end=s.index('\ndef _jfa_fill_gpu', start)
bake=s[start:end]
assert bake.count(old)==1
bake=bake.replace(old,new)
s=s[:start]+bake+s[end:]
old='''    htri = tri[bface]                                                  # [K,3,3]
    bary = _barycentric(hitpoint, htri)
    hn_tri = high_n.to(dev).float()[hf[bface]]                         # [K,3,3] vertex normals
    Nh = torch.nn.functional.normalize((bary[:, :, None] * hn_tri).sum(1), dim=-1, eps=1e-6)

    # Per-texel TBN (Gram-Schmidt tangent against the interpolated normal).
'''
new='''    htri = tri[bface]                                                  # [K,3,3]
    bary = _barycentric(hitpoint, htri)
    hface = hf_long[bface]
    hn_tri = high_n.to(dev).float()[hface]                             # [K,3,3] vertex normals
    Nh = torch.nn.functional.normalize((bary[:, :, None] * hn_tri).sum(1), dim=-1, eps=1e-6)
    if use_source_texture:
        # Interpolate and re-orthogonalize the source frame at the actual ray impact point.
        ht_tri = source_tangents_t[hface, :3]
        Th = (bary[:, :, None] * ht_tri).sum(1)
        Th = torch.nn.functional.normalize(Th - Nh * (Nh * Th).sum(-1, keepdim=True), dim=-1, eps=1e-6)
        wh = source_tangents_t[hface, 3][:, 0]
        hu_tri = source_uvs[hface]
        hu_hit = (bary[:, :, None] * hu_tri).sum(1)
        sampled = _sample_gltf_normal_linear_clamp(source_normal_map, hu_hit, dev)
        source_ts = sampled[:, :3] * 2.0 - 1.0
        source_ts[:, 0:2] *= float(source_normal_scale)                 # glTF scale affects X/Y before normalize
        source_ts = torch.nn.functional.normalize(source_ts, dim=-1, eps=1e-6)
        Bh = wh[:, None] * torch.cross(Nh, Th, dim=-1)
        Nh = torch.nn.functional.normalize(
            Th * source_ts[:, 0:1] + Bh * source_ts[:, 1:2] + Nh * source_ts[:, 2:3],
            dim=-1, eps=1e-6)

    # Per-texel target TBN (Gram-Schmidt tangent against the interpolated target normal).
'''
assert s.count(old)==1
s=s.replace(old,new)
old='''    def execute(cls, low_poly, high_poly, resolution, cage_distance=0.05, ignore_backfaces=True):
'''
new='''    def execute(cls, low_poly, high_poly, resolution, cage_distance=0.05, ignore_backfaces=True,
                source_uvs=None, source_normal_map=None, source_normal_scale=1.0):
'''
assert s.count(old)==1
s=s.replace(old,new)
old='''            # Tangents build the per-texel TBN; ApplyTextureToMesh recomputes the same basis on export.
            n_attr_i = low_n_attr[i, :n] if low_n_attr is not None else None
            low_n, tangents = _vertex_tangents_for_item(lv, lf, torch.from_numpy(uv_np).to(dev), n_attr_i, dev)

            hv_i, hf_i, *_ = get_mesh_batch_item(high_poly, i if h_batch > 1 else 0)
            hv = hv_i.to(dev).float()
            hf = hf_i.to(dev).long()
            high_n = (high_n_attr[i, :hv.shape[0]].to(dev).float() if high_n_attr is not None
                      else _compute_vertex_normals(hv, hf))

            img = _bake_normal_map(
                hv, hf, high_n,
                lv.detach().cpu().numpy(), lf.detach().cpu().numpy().astype(np.uint32), uv_np,
                low_n, tangents, resolution, cage_distance=float(cage_distance),
                ignore_backfaces=bool(ignore_backfaces),
            )
'''
new='''            # Preserve an explicit glTF TANGENT when present; otherwise retain the legacy fallback.
            n_attr_i = low_n_attr[i, :n] if low_n_attr is not None else None
            if low_poly.tangents is not None:
                tangent_i = low_poly.tangents[i, :n] if low_poly.tangents.ndim == 3 else low_poly.tangents[:n]
                tangents = tangent_i.to(dev).float()
                if tangents.shape != (n, 4):
                    raise ValueError("low_poly TANGENT must be aligned per vertex (N,4)")
                low_n = n_attr_i.to(dev).float() if n_attr_i is not None else _compute_vertex_normals(lv, lf)
            else:
                low_n, tangents = _vertex_tangents_for_item(lv, lf, torch.from_numpy(uv_np).to(dev), n_attr_i, dev)

            hi = i if h_batch > 1 else 0
            hv_i, hf_i, *_ = get_mesh_batch_item(high_poly, hi)
            hv = hv_i.to(dev).float()
            hf = hf_i.to(dev).long()
            high_n_i = high_n_attr[hi, :hv.shape[0]] if high_n_attr is not None and high_n_attr.ndim == 3 else high_n_attr[:hv.shape[0]] if high_n_attr is not None else None
            high_n = high_n_i.to(dev).float() if high_n_i is not None else _compute_vertex_normals(hv, hf)
            source_uv_i = source_uvs
            if source_uv_i is not None and getattr(source_uv_i, "ndim", 0) == 3:
                source_uv_i = source_uv_i[hi, :hv.shape[0]]
            high_tan_attr = high_poly.tangents
            source_tan_i = None
            if high_tan_attr is not None:
                source_tan_i = high_tan_attr[hi, :hv.shape[0]] if high_tan_attr.ndim == 3 else high_tan_attr[:hv.shape[0]]

            img = _bake_normal_map(
                hv, hf, high_n,
                lv.detach().cpu().numpy(), lf.detach().cpu().numpy().astype(np.uint32), uv_np,
                low_n, tangents, resolution, cage_distance=float(cage_distance),
                ignore_backfaces=bool(ignore_backfaces),
                source_uvs_np=(source_uv_i.detach().cpu().numpy() if isinstance(source_uv_i, torch.Tensor) else source_uv_i),
                source_tangents=source_tan_i, source_normal_map=source_normal_map,
                source_normal_scale=float(source_normal_scale),
            )
'''
assert s.count(old)==1
s=s.replace(old,new)
old='''                n_attr_i = low_n_attr[i, :n] if low_n_attr is not None else None
                low_n, tangents = _vertex_tangents_for_item(lv, lf, uv_i, n_attr_i, dev)
                tangents_padded[i, :n] = tangents.cpu()
                normals_padded[i, :n] = low_n.cpu()
'''
new='''                n_attr_i = low_n_attr[i, :n] if low_n_attr is not None else None
                if mesh.tangents is not None:
                    tangent_i = mesh.tangents[i, :n] if mesh.tangents.ndim == 3 else mesh.tangents[:n]
                    tangents = tangent_i.to(dev).float()
                    low_n = n_attr_i.to(dev).float() if n_attr_i is not None else _compute_vertex_normals(lv, lf)
                else:
                    low_n, tangents = _vertex_tangents_for_item(lv, lf, uv_i, n_attr_i, dev)
                tangents_padded[i, :n] = tangents.cpu()
                normals_padded[i, :n] = low_n.cpu()
'''
assert s.count(old)==1
s=s.replace(old,new)
overlay.parent.mkdir(parents=True, exist_ok=True)
with overlay.open('x', encoding='utf-8', newline='') as stream:
    stream.write(s)
    stream.flush()
print({'source':str(source),'source_sha256':source_sha256,'overlay':str(overlay),
       'sha256':hashlib.sha256(overlay.read_bytes()).hexdigest(),'bytes':overlay.stat().st_size})
