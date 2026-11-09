#!/usr/bin/env python3
"""Offline bounded Antipodal CPU experiment; never alters the input mesh."""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, resource, shutil, struct, subprocess, time
from pathlib import Path

REVISION='127f18de2ed133c0f2d8577e5717182d48ed06ce'
MAX_FACES=500_000
MAX_VERTICES=1_500_000
MAX_POINTS=32
MAX_BYTES=2*1024**3
TIMEOUT=600
HERE=Path(__file__).resolve().parent

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def regular(path):
    if path.is_symlink() or not path.is_file():raise ValueError(f'regular file required: {path}')
    return path

def read_json(path):
    regular(path)
    if path.stat().st_size>1024*1024:raise ValueError('JSON input too large')
    return json.loads(path.read_text(encoding='utf-8'))

def validate_inputs(positions, faces, glb, source_json, points, reference_glb):
    for p in (positions,faces,glb,source_json,points,reference_glb):regular(p)
    nv,rv=divmod(positions.stat().st_size,24);nf,rf=divmod(faces.stat().st_size,12)
    if rv or rf or not 3<=nv<=MAX_VERTICES or not 1<=nf<=MAX_FACES:raise ValueError('mesh size outside bounds')
    meta=read_json(source_json); checks={'vertices':nv,'triangles':nf,'positions_sha256':sha(positions),'faces_sha256':sha(faces),'source_sha256':sha(glb)}
    if not isinstance(meta,dict) or any(meta.get(k)!=v or (k in ('vertices','triangles') and type(meta.get(k)) is not int) for k,v in checks.items()):raise ValueError('source metadata mismatch')
    queries=read_json(points)
    if not isinstance(queries,dict) or queries.get('reference_glb_sha256')!=sha(reference_glb):raise ValueError('point reference GLB mismatch')
    rows=queries.get('points');
    if not isinstance(rows,list) or not 1<=len(rows)<=MAX_POINTS:raise ValueError('point count outside bounds')
    seen=set(); values=[]
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id'] or len(row['id'])>80 or row['id'] in seen:raise ValueError('invalid or duplicate point id')
        seen.add(row['id']);point=row.get('point')
        if not isinstance(point,list) or len(point)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in point):raise ValueError('invalid point coordinates')
        values.extend(point)
    return checks,queries,struct.pack('<'+'d'*len(values),*values)

def verify_upstream(path):
    head=subprocess.run(['git','-C',str(path),'rev-parse','HEAD'],check=True,text=True,capture_output=True,timeout=10).stdout.strip()
    changes=subprocess.run(['git','-C',str(path),'status','--porcelain','--untracked-files=all','--','src/antipodal'],check=True,text=True,capture_output=True,timeout=10).stdout
    if head!=REVISION or changes:raise ValueError('Antipodal revision mismatch or modified headers')
    if not (path/'src/antipodal/gwn_mesh.hh').is_file():raise ValueError('Antipodal headers missing')

def limits():
    resource.setrlimit(resource.RLIMIT_AS,(MAX_BYTES,MAX_BYTES))

def command(argv,out,stem):
    start=time.monotonic()
    try:
        result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=TIMEOUT,preexec_fn=limits)
    except subprocess.TimeoutExpired as exc:
        (out/(stem+'.stderr')).write_text('timeout after 600 seconds\n',encoding='utf-8');raise RuntimeError('command timed out') from exc
    (out/(stem+'.stdout')).write_text(result.stdout,encoding='utf-8');(out/(stem+'.stderr')).write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(f'{stem} failed with exit {result.returncode}')
    return {'argv':list(map(str,argv)),'elapsed_wall_seconds':time.monotonic()-start,'stdout_sha256':sha(out/(stem+'.stdout')),'stderr_sha256':sha(out/(stem+'.stderr'))}

def parse_measurements(text, point_ids):
    rows=[line for line in text.splitlines() if line.startswith('point=')]
    if len(rows)!=len(point_ids):raise ValueError('unexpected number of query results')
    result=[]
    for i,line in enumerate(rows):
        first=re.match(r'point=(\d+) direct=([^ ]+) near_surface_faces=(\d+)',line)
        directions=re.findall(r'antipodal=([^ ]+) abs_delta=([^ ]+) near_edge_hits=(\d+)',line)
        if not first or int(first.group(1))!=i or len(directions)!=2:raise ValueError('malformed query result')
        def finite(value):
            number=float(value);return number if math.isfinite(number) else None
        direct=finite(first.group(2)); near=int(first.group(3)); parsed=[]
        for value,delta,hits in directions:
            parsed.append({'winding':finite(value),'absolute_difference':finite(delta),'near_edge_hits':int(hits)})
        ambiguous=near>0 or direct is None or any(d['near_edge_hits']>0 or d['winding'] is None or d['absolute_difference'] is None for d in parsed)
        directional_difference=abs(parsed[0]['winding']-parsed[1]['winding']) if all(d['winding'] is not None for d in parsed) else None
        result.append({'id':point_ids[i],'direct_winding':direct,'near_surface_faces':near,'directions':parsed,'directional_difference':directional_difference,'ambiguity_detected':ambiguous})
    return result


def ambiguity_fixture(executable,out):
    # Point on a face and on a shared edge must remain visible and flagged.
    vertices=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(0.,0.,1.)]
    faces=[(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
    points=[(.2,.2,0.),(.5,0.,0.),(.1,.1,.1)]
    for name,data,fmt in [('fixture-vertices',vertices,'<3d'),('fixture-faces',faces,'<3I'),('fixture-points',points,'<3d')]:
        (out/name).write_bytes(b''.join(struct.pack(fmt,*row) for row in data))
    record=command([str(executable),str(out/'fixture-vertices'),str(out/'fixture-faces'),str(out/'fixture-points')],out,'ambiguity-fixture')
    rows=parse_measurements((out/'ambiguity-fixture.stdout').read_text(),['face','edge','interior'])
    if not rows[0]['ambiguity_detected'] or not rows[1]['ambiguity_detected'] or rows[2]['ambiguity_detected'] or abs(rows[2]['direct_winding']-1)>1e-9:raise ValueError('ambiguity fixture failed')
    return record,rows


def run(args):
    upstream=args.upstream.resolve();verify_upstream(upstream)
    inputs,queries,packed=validate_inputs(args.positions,args.faces,args.glb,args.source_json,args.points,args.reference_glb)
    compiler=shutil.which('c++')
    if not compiler:raise ValueError('C++ compiler unavailable')
    if args.out.exists() or args.out.is_symlink():raise ValueError('output already exists')
    args.out.mkdir(mode=0o700)
    (args.out/'points.f64le').write_bytes(packed)
    flags=[compiler,'-std=c++20','-O2','-Wall','-Wextra','-pedantic','-I',str(upstream/'src')]
    records={}
    try:
        records['compiler_version']=command([compiler,'--version'],args.out,'compiler-version')
        records['compile_cube']=command([*flags,str(HERE/'cubes.cpp'),'-o',str(args.out/'cubes')],args.out,'compile-cube')
        records['cube_fixtures']=command([str(args.out/'cubes')],args.out,'cube-fixtures')
        records['compile_real']=command([*flags,str(HERE/'real_mesh.cpp'),'-o',str(args.out/'real_mesh')],args.out,'compile-real')
        records['ambiguity_fixture'],fixture_rows=ambiguity_fixture(args.out/'real_mesh',args.out)
        records['real_mesh']=command([str(args.out/'real_mesh'),str(args.positions),str(args.faces),str(args.out/'points.f64le')],args.out,'real-mesh')
        measurements=parse_measurements((args.out/'real-mesh.stdout').read_text(),[r['id'] for r in queries['points']])
        report={'status':'complete','scope':'numerical experiment only; not a repair, watertightness or inside classification','antipodal_revision':REVISION,'upstream_headers_sha256':{n:sha(upstream/'src/antipodal'/n) for n in ('gwn_mesh.hh','dispatcher/dispatcher.hh','intersector/intersector.hh','math/common.hh')},'input':inputs,'reference_glb_sha256':sha(args.reference_glb),'points_sha256':sha(args.points),'point_ids':[r['id'] for r in queries['points']],'source_files':{n:sha(HERE/n) for n in ('run.py','cubes.cpp','real_mesh.cpp')},'memory_limit_bytes':MAX_BYTES,'timeout_seconds_per_command':TIMEOUT,'ambiguity_note':'Detected near-surface or near-edge hits and non-finite values are flagged; absence of flags is not a robustness proof.', 'ambiguity_fixture':fixture_rows,'measurements':measurements,'records':records}
        (args.out/'receipt.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        return report
    except Exception as exc:
        (args.out/'failure.txt').write_text(f'{type(exc).__name__}: {exc}\n',encoding='utf-8');raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('upstream','positions','faces','glb','source-json','points','reference-glb','out'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();report=run(args);print(json.dumps({'status':report['status'],'receipt':str(args.out/'receipt.json')}))
if __name__=='__main__':main()
