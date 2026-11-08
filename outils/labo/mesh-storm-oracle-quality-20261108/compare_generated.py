#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
NAMES=['oracle-n4.usda','oracle-n8.usda','oracle-n16.usda','oracle-n16-flat.usda','oracle-n32-v2.usda','oracle-n64.usda','source-direct-normal.usda','source-flat-material.usda','target-flat-material.usda','target-flat-normal.usda','target-normal.usda','target-normal-yflip.usda','target-normal-vsame.usda','target-normal-yflip-vsame.usda']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
p=argparse.ArgumentParser();p.add_argument('--generated-dir',required=True);p.add_argument('--reference-dir',required=True);p.add_argument('--output',required=True);a=p.parse_args()
g=Path(a.generated_dir);r=Path(a.reference_dir);o=Path(a.output)
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_inputs import git_root_ancestor, symlink_component
if not g.is_dir() or not r.is_dir():raise SystemExit('REFUS: dossier généré ou référence absent')
for label,path in [('generated',g),('reference',r),('receipt',o)]:
 link=symlink_component(path)
 if link:raise SystemExit(f'REFUS: composante liée ({label}): {link}')
if o.exists():raise SystemExit(f'REFUS: reçu existe déjà: {o}')
storage=Path(os.environ.get('MESH_ORACLE_STORAGE_ROOT','/media/pc6/Storage/Nexora/travail')).resolve(); code=Path(__file__).resolve().parent; out_resolved=o.resolve(strict=False); run=g.resolve().parent
if storage not in run.parents or git_root_ancestor(run) or code in out_resolved.parents or run != out_resolved.parent:raise SystemExit(f'REFUS: reçu doit être neuf à la racine du run Storage non-Git: {out_resolved}')
rows=[];fail=False
for name in NAMES:
 x=g/name;y=r/name
 if not x.is_file() or x.is_symlink() or not y.is_file() or y.is_symlink():
  print(f'REFUS: stage absent: generated={x} reference={y}',file=sys.stderr);fail=True;continue
 hx,hy=sha(x),sha(y);rows.append({'stage':name,'generated_sha256':hx,'reference_sha256':hy,'match':hx==hy})
 if hx!=hy:fail=True
report={'source_code_dir':str(Path(__file__).resolve().parent),'generated_dir':str(g.resolve()),'reference_dir':str(r.resolve()),'exact_sha_match':not fail,'stages':rows}
if fail:report['status']='mismatch_or_missing'
else:report['status']='all_stage_sha256_match'
with o.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'receipt':str(o),'stages':len(rows)}))
raise SystemExit(0 if not fail else 3)
