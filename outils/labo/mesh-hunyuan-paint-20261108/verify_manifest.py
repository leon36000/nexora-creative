#!/usr/bin/env python3
"""Verify a locally provisioned Paint experiment; never downloads or runs it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

def verify(root, manifest):
    root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('root is not a directory')
    if manifest.get('schema') != 'nexora-mesh-paint-inputs-v1':raise ValueError('unexpected manifest schema')
    entries=manifest.get('files')
    if not isinstance(entries,list) or not entries:raise ValueError('empty file list')
    results=[]; seen=set()
    for entry in entries:
        name=entry['path']; rel=PurePosixPath(name)
        if not name or rel.is_absolute() or rel.as_posix()!=name or any(x in ('','.', '..') for x in rel.parts) or '\\' in name or name in seen:
            raise ValueError('invalid or duplicate relative path')
        seen.add(name); expected=entry['sha256']
        if len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):raise ValueError('invalid SHA-256')
        target=root
        try:
            for part in rel.parts:
                target=target/part
                if target.is_symlink():raise ValueError('symlink not accepted: '+name)
            if not target.is_file():
                results.append({'path':name,'status':'missing'});continue
            h=hashlib.sha256()
            with target.open('rb') as f:
                for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
            size=target.stat().st_size
            results.append({'path':name,'status':'ok' if h.hexdigest()==expected and size==entry['bytes'] else 'mismatch','bytes':size,'sha256':h.hexdigest()})
        except FileNotFoundError:
            results.append({'path':name,'status':'missing'})
    return {'verified':all(x['status']=='ok' for x in results),'files':results}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('root');parser.add_argument('manifest')
    args=parser.parse_args()
    with open(args.manifest,encoding='utf-8') as f:manifest=json.load(f)
    result=verify(args.root,manifest);print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['verified'] else 1

if __name__=='__main__':raise SystemExit(main())
