#!/usr/bin/env python3
"""Prepare an offline paired-run viewer; this command never submits jobs."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import struct
import uuid
from pathlib import Path

LABELS = ('A', 'B', 'C', 'D', 'dense')
CASE_NAMES = {'s01': {'fr': 'chaise', 'en': 'chair'}, 's04': {'fr': 'vase', 'en': 'vase'}}
ASSETS = {
    'build/three.module.js': 'assets/three.module.js',
    'build/three.core.js': 'assets/three.core.js',
    'examples/jsm/loaders/GLTFLoader.js': 'assets/loaders/GLTFLoader.js',
    'examples/jsm/utils/BufferGeometryUtils.js': 'assets/utils/BufferGeometryUtils.js',
    'examples/jsm/utils/SkeletonUtils.js': 'assets/utils/SkeletonUtils.js',
}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def regular(path):
    if path.is_symlink() or not path.is_file(): raise ValueError(f'regular file required: {path}')
    return path

def json_file(path):
    with regular(path).open(encoding='utf-8') as f: return json.load(f)

def glb_header(path):
    with regular(path).open('rb') as f:
        header=f.read(20)
        if len(header)!=20: raise ValueError('truncated GLB header')
        magic,version,size,json_size,chunk=struct.unpack('<4sIII4s',header)
        if magic!=b'glTF' or version!=2 or size!=path.stat().st_size or chunk!=b'JSON' or json_size%4 or json_size>16*1024*1024 or 20+json_size>size: raise ValueError('invalid GLB header or size')
        doc=json.loads(f.read(json_size))
    def has_uri(value):
        if isinstance(value,dict): return 'uri' in value or any(has_uri(x) for x in value.values())
        if isinstance(value,list): return any(has_uri(x) for x in value)
        return False
    if has_uri(doc): raise ValueError('GLB external or embedded URI refused')


def validated_run(run, corpus, case_id):
    if len(case_id)!=3 or case_id[0]!='s' or not case_id[1:].isdigit(): raise ValueError('invalid case ID')
    meta=json_file(run/'preparation.json'); events=[json.loads(line) for line in regular(run/'events.jsonl').read_text(encoding='utf-8').splitlines()]; history=json_file(run/'history-final.json'); graph=json_file(run/'graph.json'); book=json_file(corpus)
    try: prompt=str(uuid.UUID(meta['prompt_id'],version=4))
    except (KeyError,ValueError,TypeError,AttributeError) as exc: raise ValueError('invalid prompt UUID') from exc
    if prompt!=meta['prompt_id'] or meta.get('case_id',case_id)!=case_id: raise ValueError('case or prompt mismatch')
    subjects=[x for x in book.get('subjects',[]) if x.get('id')==case_id]
    if len(subjects)!=1: raise ValueError('case missing or duplicated in corpus')
    subject=subjects[0]
    if not isinstance(subject.get('category'),str) or len(subject['category'])>100: raise ValueError('invalid case category')
    original=meta.get('original_sha256',meta.get('input_sha256'))
    if original!=subject.get('sha256'): raise ValueError('case source hash mismatch')
    if 'input_manifest_sha256' in meta:
        input_manifest=run/'input-manifest.json'; manifest=json_file(input_manifest)
        if sha(input_manifest)!=meta['input_manifest_sha256'] or manifest.get('cases',{}).get(case_id,{}).get('png_sha256')!=meta.get('input_sha256') or manifest['cases'][case_id].get('original_sha256')!=original: raise ValueError('input conversion provenance mismatch')
    image=regular(run/'input.png')
    with image.open('rb') as f: png_signature=f.read(8)
    if image.stat().st_size>64*1024*1024 or sha(image)!=meta.get('input_sha256') or png_signature!=b'\x89PNG\r\n\x1a\n': raise ValueError('input PNG mismatch')
    if sha(run/'graph.json')!=meta.get('graph_sha256'): raise ValueError('graph hash mismatch')
    verify_history_and_events(meta, prompt, graph, events, history)
    models = verify_outputs(run, meta, prompt, events, history)
    return {'case_id':case_id,'case_names':CASE_NAMES.get(case_id, {'fr': subject['category'], 'en': subject['category']}),'category':subject.get('category',''),'prompt_id':prompt,'graph_sha256':meta['graph_sha256'],'input_original_sha256':original,'input_sha256':meta['input_sha256'],'preparation_sha256':sha(run/'preparation.json'),'events_sha256':sha(run/'events.jsonl'),'history_sha256':sha(run/'history-final.json'),'corpus_manifest_sha256':sha(corpus),'models':models}

def verify_history_and_events(meta, prompt, graph, events, history):
    prepared=[e for e in events if e.get('event')=='prepared']; accepted=[e for e in events if e.get('event')=='prompt_accepted']; complete=[e for e in events if e.get('event')=='completed']
    if any(e.get('event')=='stopped_or_uncertain' for e in events): raise ValueError('stopped or uncertain execution cannot be used as completed run')
    if len(prepared)!=1 or len(accepted)!=1 or len(complete)!=1 or any(e.get('prompt_id')!=prompt for e in (prepared[0],accepted[0],complete[0])): raise ValueError('ambiguous or mismatched events')
    if prepared[0].get('graph_sha256')!=meta['graph_sha256'] or not (events.index(prepared[0])<events.index(accepted[0])<events.index(complete[0])): raise ValueError('event order or graph mismatch')
    if history.get('status',{}).get('status_str')!='success' or history['status'].get('completed') is not True or not isinstance(history.get('prompt'),list) or len(history['prompt'])<3 or history['prompt'][1]!=prompt or history['prompt'][2]!=graph: raise ValueError('history prompt or status mismatch')

def verify_outputs(run, meta, prompt, events, history):
    complete=[e for e in events if e.get('event')=='completed']
    outputs=history.get('outputs',{}); expected_nodes=[x+'_save' if x!='dense' else 'dense_save' for x in LABELS]
    if set(outputs)!=set(expected_nodes) or meta.get('outputs')!=expected_nodes: raise ValueError('unexpected output nodes')
    artifacts=complete[0].get('artifacts')
    if not isinstance(artifacts,list) or len(artifacts)!=5 or {a.get('node') for a in artifacts}!=set(expected_nodes): raise ValueError('unexpected completed artifacts')
    by_node={a['node']:a for a in artifacts}; models={}
    for label,node in zip(LABELS,expected_nodes):
        art=by_node[node]; filename=label+'.glb'; path=regular(run/filename); max_bytes=(512 if label=='dense' else 256)*1024*1024
        refs=outputs[node].get('3d')
        if not isinstance(refs,list) or len(refs)!=1 or refs[0]!=art.get('reference') or art.get('filename')!=filename or refs[0].get('subfolder')!='ESSAI' or refs[0].get('type')!='output': raise ValueError('output reference mismatch')
        expected_prefix='mesh_pair_'+prompt.replace('-','')+'_'+label+'_'
        ref_name=refs[0].get('filename','')
        if not isinstance(ref_name,str) or not ref_name.startswith(expected_prefix) or len(ref_name)!=len(expected_prefix)+10 or not ref_name[len(expected_prefix):len(expected_prefix)+5].isascii() or not ref_name[len(expected_prefix):len(expected_prefix)+5].isdigit() or not ref_name.endswith('_.glb'): raise ValueError('output reference filename mismatch')
        if path.stat().st_size>max_bytes or path.stat().st_size!=art.get('output_bytes') or sha(path)!=art.get('output_sha256'): raise ValueError('output digest or size mismatch')
        glb_header(path);models[label]={'filename':filename,'bytes':path.stat().st_size,'sha256':art['output_sha256']}
    return models

def prepare(run, corpus, case_id, output, three_dir):
    run=Path(run).resolve();corpus=Path(corpus);output=Path(output);three_dir=Path(three_dir)
    if output.exists() or output.is_symlink(): raise ValueError('output already exists')
    if output.resolve().is_relative_to(run): raise ValueError('output cannot be inside source run')
    provenance=validated_run(run,corpus,case_id)
    package=json_file(three_dir/'package.json')
    if package.get('version')!='0.186.1': raise ValueError('Three version must be 0.186.1')
    for source in ASSETS: regular(three_dir/source)
    # Exclusive directory: errors leave the partial evidence visible rather than overwrite.
    output.mkdir(mode=0o700)
    source_root=Path(__file__).resolve().parent
    for name in ('index.html','metrics.mjs','views.mjs'): shutil.copyfile(source_root/name,output/name)
    shutil.copyfile(run/'input.png',output/'input.png')
    for label in LABELS[:4]: shutil.copyfile(run/(label+'.glb'),output/(label+'.glb'))
    for source,dest in ASSETS.items():
        target=output/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(three_dir/source,target)
    for label in LABELS[:4]:
        copied=output/(label+'.glb')
        if copied.stat().st_size!=provenance['models'][label]['bytes'] or sha(copied)!=provenance['models'][label]['sha256']: raise ValueError('copied GLB mismatch')
    if sha(output/'input.png')!=provenance['input_sha256']: raise ValueError('copied input mismatch')
    for source,dest in ASSETS.items():
        if sha(three_dir/source)!=sha(output/dest): raise ValueError('copied asset mismatch')
    model_manifest={'scope':'GLB appariés, empreintes vérifiées sur le run','models':{k:provenance['models'][k] for k in LABELS[:4]}}
    (output/'model-manifest.json').write_text(json.dumps(model_manifest,indent=2)+'\n')
    viewer_files=['index.html','metrics.mjs','views.mjs','model-manifest.json','input.png',*ASSETS.values()]
    provenance.update({'version':1,'preparer_sha256':sha(Path(__file__)),'scope':'provenance préparée, aucune mesure réalisée','viewer_files':{name:{'sha256':sha(output/name),'bytes':(output/name).stat().st_size} for name in viewer_files}})
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    all_files=[*(x+'.glb' for x in LABELS[:4]),*viewer_files,'provenance.json']
    (output/'MANIFEST.sha256').write_text(''.join(f'{sha(output/name)}  {name}\n' for name in all_files))
    return {'output':str(output),'sidecar_sha256':sha(output/'provenance.json'),'manifest_sha256':sha(output/'MANIFEST.sha256')}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--corpus-manifest',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--three-dir',type=Path,default=Path(__file__).resolve().parents[3]/'app/node_modules/three');a=p.parse_args()
    print(json.dumps(prepare(a.run,a.corpus_manifest,a.case,a.out,a.three_dir),ensure_ascii=False))
if __name__=='__main__': main()
