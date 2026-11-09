#!/usr/bin/env python3
"""Describe raw and exact-weld edge incidences without modifying a mesh."""
from __future__ import annotations
import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from itertools import combinations
import numpy as np


def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def check_file(path: Path) -> None:
    path=Path(path)
    for item in reversed([path,*path.parents]):
        mode=item.lstat().st_mode
        if stat.S_ISLNK(mode): raise ValueError(f'symlink refused: {item}')
    if not path.is_file(): raise ValueError(f'regular file required: {path}')


DEFAULT_MAX_FACES = 500_000
HARD_MAX_FACES = 2_000_000


def _valid_sha(value) -> bool:
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def _load_source_meta(meta_path) -> dict:
    check_file(meta_path)
    try:
        meta=json.loads(Path(meta_path).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'invalid source metadata: {exc}') from exc
    if not isinstance(meta,dict): raise ValueError('source metadata must be a JSON object')
    return meta

def _check_meta_hashes(meta: dict) -> None:
    for key in ('source_sha256','positions_sha256','faces_sha256'):
        if not _valid_sha(meta.get(key)): raise ValueError(f'invalid metadata {key}')

def _check_meta_counts(meta: dict) -> None:
    if type(meta.get('vertices')) is not int or meta['vertices']<=0 or type(meta.get('triangles')) is not int or meta['triangles']<=0: raise ValueError('invalid metadata counts')

def _check_meta_arrays(meta: dict, positions_path, faces_path) -> None:
    if positions_path.stat().st_size!=meta['vertices']*24 or faces_path.stat().st_size!=meta['triangles']*12: raise ValueError('metadata counts or byte sizes mismatch')
    if sha256(positions_path)!=meta['positions_sha256'] or sha256(faces_path)!=meta['faces_sha256']: raise ValueError('array hash mismatch')

def _check_meta_source(meta: dict, source_glb) -> None:
    if source_glb is not None and sha256(source_glb)!=meta['source_sha256']: raise ValueError('source GLB hash mismatch')

def _check_meta_uv(meta: dict, uv_path) -> None:
    if uv_path is None: return
    if uv_path.stat().st_size!=meta['vertices']*8: raise ValueError('UV0 byte size mismatch')
    value=meta.get('uv0_sha256')
    if not _valid_sha(value) or sha256(uv_path)!=value: raise ValueError('UV0 hash missing or mismatch')

def verify_provenance(meta_path, positions_path, faces_path, uv_path=None, source_glb=None):
    meta=_load_source_meta(meta_path)
    _check_meta_hashes(meta)
    _check_meta_counts(meta)
    _check_meta_arrays(meta, positions_path, faces_path)
    _check_meta_source(meta, source_glb)
    _check_meta_uv(meta, uv_path)
    return meta


def _permutation_parity(tri: tuple[int,int,int]) -> int:
    inv=sum(1 for i in range(3) for j in range(i+1,3) if tri[i]>tri[j])
    return -1 if inv%2 else 1


def _face_components(face_indices):
    count=int(face_indices.max())+1 if face_indices.size else 0
    parent=list(range(count))
    def find(value):
        value=int(value)
        while parent[value]!=value:
            parent[value]=parent[parent[value]]
            value=parent[value]
        return value
    for tri in face_indices:
        find0,find1,find2=(find(x) for x in tri)
        parent[find0]=find1
        parent[find1]=find2
    roots=[find(tri[0]) for tri in face_indices]
    root_map={root:index for index,root in enumerate(sorted(set(roots)))}
    return [root_map[root] for root in roots]


def _check_vertices(vertices) -> None:
    if vertices.ndim!=2 or vertices.shape[1]!=3 or len(vertices)<3 or not np.isfinite(vertices).all():
        raise ValueError('positions must be finite Nx3 float values')

def _check_faces(faces, vertices) -> None:
    if faces.ndim!=2 or faces.shape[1]!=3 or len(faces)==0 or not np.issubdtype(faces.dtype,np.integer):
        raise ValueError('faces must be non-empty Mx3 integer indices')
    if int(faces.min())<0 or int(faces.max())>=len(vertices): raise ValueError('face index out of range')

def _load_uv0(uv0, vertex_count):
    if uv0 is None: return None
    uv0=np.asarray(uv0,dtype=np.float64)
    if uv0.shape!=(vertex_count,2) or not np.isfinite(uv0).all(): raise ValueError('UV0 must be finite Nx2')
    return uv0

@dataclass(frozen=True)
class GeometryContext:
    vertices: np.ndarray
    exact_xyz: np.ndarray
    exact_ids: np.ndarray
    uv0: np.ndarray | None
    raw_by_exact: list[list[int]]
    raw_component_ids: list[int]
    exact_component_ids: list[int]

@dataclass(frozen=True)
class EdgeFrame:
    axis: np.ndarray
    basis_u: np.ndarray
    basis_v: np.ndarray
    midpoint: np.ndarray


def _face_edge_data(face_id, raw, exact, geometry: GeometryContext, normals):
    vertices=geometry.vertices; exact_ids=geometry.exact_ids; uv0=geometry.uv0
    raw_component_ids=geometry.raw_component_ids; exact_component_ids=geometry.exact_component_ids
    duplicate={'face':face_id,'raw_vertices':[int(x) for x in raw],'exact_vertices':list(exact),'winding_parity':_permutation_parity(exact)}
    tri=vertices[raw]
    e1=tri[1]-tri[0]; e2=tri[2]-tri[0]
    if not np.isfinite(e1).all() or not np.isfinite(e2).all(): raise ValueError('triangle coordinate subtraction overflow')
    scale=float(max(np.max(np.abs(e1)),np.max(np.abs(e2))))
    cross=np.cross(e1/scale,e2/scale) if scale else np.zeros(3)
    norm=math.hypot(*(float(x) for x in cross))
    degenerate=norm==0 or len(set(exact))<3
    normal=None if degenerate else (cross/norm).tolist()
    normals.append(normal)
    raw_incidents=[]; exact_incidents=[]
    for ia,ib,ic in ((0,1,2),(1,2,0),(2,0,1)):
        ra,rb,ro=int(raw[ia]),int(raw[ib]),int(raw[ic])
        ea,eb=int(exact_ids[ra]),int(exact_ids[rb])
        raw_incidents.append((tuple(sorted((ra,rb))),{'face':face_id,'from_raw':ra,'to_raw':rb,'opposite_raw':ro,'orientation':1 if ra<rb else -1}))
        record={'face':face_id,'from_raw':ra,'to_raw':rb,'opposite_raw':ro,'from_exact':ea,'to_exact':eb,'opposite_exact':int(exact_ids[ro]),'orientation':1 if ea<eb else -1,'face_unit_normal':normal,'raw_component':raw_component_ids[face_id],'exact_component':exact_component_ids[face_id],'face_vertices_raw':[int(x) for x in raw],'face_vertices_xyz':tri.tolist()}
        if uv0 is not None:
            record['uv_from']=[float(x) for x in uv0[ra]]
            record['uv_to']=[float(x) for x in uv0[rb]]
            record['uv_opposite']=[float(x) for x in uv0[ro]]
            record['face_uv0']=[[float(x) for x in uv0[int(vertex)]] for vertex in raw]
        exact_incidents.append((tuple(sorted((ea,eb))),record))
    return duplicate, degenerate, raw_incidents, exact_incidents

def _edge_geometry(key, exact_xyz):
    a,b=key
    edge_start=exact_xyz[a]; edge_end=exact_xyz[b]
    edge_vector=edge_end-edge_start; edge_length=math.hypot(*(float(x) for x in edge_vector))
    if not math.isfinite(edge_length): raise ValueError('edge length overflow')
    axis=edge_vector/edge_length if edge_length>0 else np.array([1.0,0.0,0.0])
    helper=np.eye(3)[int(np.argmin(np.abs(axis)))]
    basis_u=np.cross(axis,helper); basis_u=basis_u/np.linalg.norm(basis_u)
    basis_v=np.cross(axis,basis_u)
    midpoint=edge_start*0.5+edge_end*0.5
    return a,b,axis,basis_u,basis_v,edge_length,midpoint

def _edge_incident_detail(rec, geometry: GeometryContext, frame: EdgeFrame, raw_variants, uv_at):
    vertices=geometry.vertices; uv0=geometry.uv0
    axis=frame.axis; basis_u=frame.basis_u; basis_v=frame.basis_v; midpoint=frame.midpoint
    item=dict(rec)
    raw_variants[tuple(sorted((rec['from_raw'],rec['to_raw'])))].append(rec['face'])
    opposite=vertices[rec['opposite_raw']]
    delta=opposite-midpoint
    radial=delta-axis*float(np.dot(delta,axis))
    item['opposite_xyz']=[float(x) for x in opposite]
    item['opposite_radial_distance']=math.hypot(*(float(x) for x in radial))
    item['opposite_radial_angle_degrees']=float(np.degrees(np.arctan2(np.dot(radial,basis_v),np.dot(radial,basis_u))))
    if uv0 is not None:
        uv_at[rec['from_exact']].append(rec['uv_from'])
        uv_at[rec['to_exact']].append(rec['uv_to'])
    return item

def _raw_variant_rows(raw_variants, raw_component_ids):
    rows=[]
    for raw_key,face_ids in sorted(raw_variants.items()):
        rows.append({'raw_indices':list(raw_key),'incident_faces':face_ids,'incidence_count':len(face_ids),'raw_components':sorted({raw_component_ids[x] for x in face_ids})})
    return rows

def _add_uv0_summary(out, uv_at) -> None:
    out['uv0_at_endpoint_variants']={str(k):sorted({tuple(v) for v in vals}) for k,vals in uv_at.items()}
    out['uv0_endpoint_variant_counts']={str(k):len({tuple(v) for v in vals}) for k,vals in uv_at.items()}

def _add_normal_dots(out, records) -> None:
    norms=[np.asarray(r['face_unit_normal'],dtype=np.float64) for r in records if r['face_unit_normal'] is not None]
    if len(norms)>1:
        out['face_normal_pairwise_dots']=[float(np.dot(norms[i],norms[j])) for i,j in combinations(range(len(norms)),2)]

def _edge_summary(key,records,geometry: GeometryContext):
    exact_xyz=geometry.exact_xyz; uv0=geometry.uv0
    raw_by_exact=geometry.raw_by_exact; raw_component_ids=geometry.raw_component_ids
    a,b,axis,basis_u,basis_v,edge_length,midpoint=_edge_geometry(key,exact_xyz)
    frame=EdgeFrame(axis,basis_u,basis_v,midpoint)
    raw_variants=defaultdict(list); uv_at={a:[],b:[]}; detailed=[]
    for rec in records:
        detailed.append(_edge_incident_detail(rec,geometry,frame,raw_variants,uv_at))
    out={'exact_vertex_ids':[a,b],'coordinates':[exact_xyz[a].tolist(),exact_xyz[b].tolist()],
         'edge_length':edge_length,
         'incident_face_count':len(records),'orientation_signs':{'+':sum(r['orientation']>0 for r in records),'-':sum(r['orientation']<0 for r in records)},
         'raw_endpoint_indices':{str(a):raw_by_exact[a],str(b):raw_by_exact[b]},
         'raw_edge_variants':_raw_variant_rows(raw_variants,raw_component_ids),
         'connected_components':{'raw_index_ids':sorted({raw_component_ids[r['face']] for r in records}),'exact_weld_ids':sorted({r['exact_component'] for r in records})},
         'radial_angle_basis':{'axis_from_exact_endpoint_a_to_b':[float(x) for x in axis],'basis_u':[float(x) for x in basis_u],'basis_v':[float(x) for x in basis_v],'angle_note':'deterministic orthonormal basis; angles describe opposite-vertex positions around this edge, not a manifold criterion'},
         'incidents':detailed}
    if uv0 is not None: _add_uv0_summary(out,uv_at)
    _add_normal_dots(out,records)
    return out

def _collect_incidences(faces,geometry: GeometryContext):
    exact_ids=geometry.exact_ids
    raw_edges=defaultdict(list); exact_edges=defaultdict(list); duplicate_faces=defaultdict(list)
    degenerate_faces=[]; unit_normals=[]
    for face_id,raw in enumerate(faces):
        exact=tuple(int(exact_ids[int(i)]) for i in raw)
        duplicate,degenerate,raw_incidents,exact_incidents=_face_edge_data(face_id,raw,exact,geometry,unit_normals)
        duplicate_faces[tuple(sorted(exact))].append(duplicate)
        if degenerate: degenerate_faces.append(face_id)
        for raw_key,raw_record in raw_incidents: raw_edges[raw_key].append(raw_record)
        for key,record in exact_incidents: exact_edges[key].append(record)
    return raw_edges,exact_edges,duplicate_faces,degenerate_faces

def analyze_arrays(vertices, faces, uv0=None):
    vertices=np.asarray(vertices,dtype=np.float64)
    faces=np.asarray(faces)
    _check_vertices(vertices)
    _check_faces(faces,vertices)
    faces=faces.astype(np.int64,copy=False)
    uv0=_load_uv0(uv0,len(vertices))
    exact_xyz,exact_ids=np.unique(vertices,axis=0,return_inverse=True)
    exact_faces=np.asarray(exact_ids[faces],dtype=np.int64)
    raw_component_ids=_face_components(faces)
    exact_component_ids=_face_components(exact_faces)
    raw_by_exact=[[] for _ in range(len(exact_xyz))]
    for raw_id,exact_id in enumerate(exact_ids): raw_by_exact[int(exact_id)].append(raw_id)
    geometry=GeometryContext(vertices,exact_xyz,exact_ids,uv0,raw_by_exact,raw_component_ids,exact_component_ids)
    raw_edges,exact_edges,duplicate_faces,degenerate_faces=_collect_incidences(faces,geometry)
    raw_nm=[(key,records) for key,records in raw_edges.items() if len(records)>2]
    exact_nm=[(key,records) for key,records in exact_edges.items() if len(records)>2]
    duplicate_groups=[rec for rec in duplicate_faces.values() if len(rec)>1]
    raw_records=[]
    for key,records in sorted(raw_nm):
        raw_records.append({'raw_vertex_ids':list(key),'coordinates':vertices[list(key)].tolist(),'incident_face_count':len(records),'incidents':records})
    exact_records=[_edge_summary(key,records,geometry) for key,records in sorted(exact_nm)]
    return {'scope':'read-only incidence description; exact coordinate welding only; not a repair or watertightness certification',
            'input_counts':{'vertices_raw':int(len(vertices)),'triangles':int(len(faces)),'vertices_exact_weld':int(len(exact_xyz)),'raw_index_face_components':len(set(raw_component_ids)),'exact_weld_face_components':len(set(exact_component_ids)),'degenerate_triangles_by_exact_weld':len(degenerate_faces)},
            'raw_edges':{'edge_occurrence_classes':len(raw_edges),'nonmanifold_edge_classes':len(raw_records),'nonmanifold_edges':raw_records},
            'exact_weld_edges':{'edge_occurrence_classes':len(exact_edges),'nonmanifold_edge_classes':len(exact_records),'nonmanifold_edges':exact_records},
            'duplicate_geometric_faces_after_exact_weld':duplicate_groups}


def _build_parser():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positions',type=Path,required=True,help='Nx3 float64 little-endian')
    parser.add_argument('--faces',type=Path,required=True,help='Mx3 uint32 little-endian')
    parser.add_argument('--uv0',type=Path,help='Nx2 float32 little-endian, optional')
    parser.add_argument('--source-json',type=Path,required=True,help='extractor metadata; UV requires uv0_sha256')
    parser.add_argument('--source-glb',type=Path,help='optional source GLB checked against metadata')
    parser.add_argument('--max-faces',type=int,default=DEFAULT_MAX_FACES,help='limit before allocation; maximum 2000000')
    parser.add_argument('--out',type=Path,required=True,help='new JSON path; existing output refused')
    return parser

def _check_input_sizes(args) -> None:
    for p in (args.positions,args.faces,args.uv0,args.source_glb,args.source_json):
        if p is not None: check_file(p)
    if args.positions.stat().st_size==0 or args.positions.stat().st_size%24: raise SystemExit('positions size must be a nonzero multiple of 24')
    if args.faces.stat().st_size==0 or args.faces.stat().st_size%12: raise SystemExit('faces size must be a nonzero multiple of 12')
    if args.faces.stat().st_size//12 > args.max_faces: raise SystemExit('face count exceeds max-faces before allocation')
    if args.positions.stat().st_size//24 > 3*args.max_faces: raise SystemExit('vertex count exceeds 3 * max-faces before allocation')

def _load_uv_file(args, uv0_path):
    if uv0_path is None: return None
    if uv0_path.stat().st_size%8: raise SystemExit('UV0 size must be a multiple of 8')
    return np.fromfile(uv0_path,dtype='<f4').reshape(-1,2)

def _input_info(path) -> dict:
    return {'path':str(path),'sha256':sha256(path),'bytes':path.stat().st_size}

def _attach_report_metadata(report, args, meta) -> None:
    report['provenance']={'source_metadata_sha256':sha256(args.source_json),'declared_source_sha256':meta['source_sha256'],'source_glb_verified':args.source_glb is not None,'max_faces':args.max_faces}
    report['inputs']={'positions':_input_info(args.positions),'faces':_input_info(args.faces)}
    if args.uv0 is not None: report['inputs']['uv0']=_input_info(args.uv0)
    if args.source_glb is not None: report['inputs']['source_glb']=_input_info(args.source_glb)

def _write_report(out_path, report) -> None:
    fd=os.open(out_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as stream: json.dump(report,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')

def _print_summary(out_path, report) -> None:
    print(json.dumps({'out':str(out_path),'sha256':sha256(out_path),'exact_nonmanifold_edges':report['exact_weld_edges']['nonmanifold_edge_classes'],'raw_nonmanifold_edges':report['raw_edges']['nonmanifold_edge_classes'],'duplicate_geometric_face_groups':len(report['duplicate_geometric_faces_after_exact_weld'])},indent=2))

def main():
    args=_build_parser().parse_args()
    if not 1 <= args.max_faces <= HARD_MAX_FACES: raise SystemExit('max-faces must be between 1 and 2000000')
    _check_input_sizes(args)
    meta=verify_provenance(args.source_json,args.positions,args.faces,args.uv0,args.source_glb)
    vertices=np.fromfile(args.positions,dtype='<f8').reshape(-1,3)
    faces=np.fromfile(args.faces,dtype='<u4').reshape(-1,3)
    uv=_load_uv_file(args,args.uv0)
    report=analyze_arrays(vertices,faces,uv)
    _attach_report_metadata(report,args,meta)
    if args.out.exists() or args.out.is_symlink(): raise SystemExit('output exists or is a symlink')
    _write_report(args.out,report)
    _print_summary(args.out,report)

if __name__=='__main__': main()
