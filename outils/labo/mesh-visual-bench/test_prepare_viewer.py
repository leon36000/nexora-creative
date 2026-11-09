import hashlib,json,struct,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
import prepare_viewer as pv

class PrepareTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.run=self.root/'run';self.run.mkdir();self.three=self.root/'three';self.three.mkdir();(self.three/'package.json').write_text('{"version":"0.186.1"}')
  for name in pv.ASSETS:
   f=self.three/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('synthetic')
  self.case='s01';self.prompt='c4fd99ed-e74b-467a-baee-27b185adb7cb';self.graph={'node':{'class_type':'test'}};self.dump(self.run/'graph.json',self.graph)
  img=b'\x89PNG\r\n\x1a\nsynthetic';(self.run/'input.png').write_bytes(img);self.meta={'prompt_id':self.prompt,'graph_sha256':pv.sha(self.run/'graph.json'),'input_sha256':hashlib.sha256(img).hexdigest(),'outputs':[x+'_save' if x!='dense' else 'dense_save' for x in pv.LABELS]};self.dump(self.run/'preparation.json',self.meta)
  self.corpus=self.root/'corpus.json';self.dump(self.corpus,{'subjects':[{'id':self.case,'sha256':self.meta['input_sha256'],'category':'synthetic'}]})
  self.art=[];self.outputs={}
  for label,node in zip(pv.LABELS,self.meta['outputs']):
   j=b'{\"asset\":{\"version\":\"2.0\"}}';j+=b' '*((-len(j))%4);data=struct.pack('<4sIII4s',b'glTF',2,20+len(j),len(j),b'JSON')+j;(self.run/(label+'.glb')).write_bytes(data)
   ref={'filename':'mesh_pair_'+self.prompt.replace('-','')+'_'+label+'_00001_.glb','subfolder':'ESSAI','type':'output'}
   self.art.append({'node':node,'filename':label+'.glb','reference':ref,'output_bytes':len(data),'output_sha256':hashlib.sha256(data).hexdigest()});self.outputs[node]={'3d':[ref]}
  self.events=[{'event':'prepared','prompt_id':self.prompt,'graph_sha256':self.meta['graph_sha256']},{'event':'prompt_accepted','prompt_id':self.prompt},{'event':'completed','prompt_id':self.prompt,'artifacts':self.art}];self.writeevents()
  self.history={'status':{'status_str':'success','completed':True},'prompt':[0,self.prompt,self.graph],'outputs':self.outputs};self.dump(self.run/'history-final.json',self.history)
 def dump(self,path,value):path.write_text(json.dumps(value))
 def writeevents(self): (self.run/'events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in self.events))
 def prepare(self):return pv.prepare(self.run,self.corpus,self.case,self.root/'out',self.three)
 def test_prepares_verified_static_viewer_without_dense_copy(self):
  result=self.prepare();out=self.root/'out';side=json.loads((out/'provenance.json').read_text());self.assertEqual(result['sidecar_sha256'],pv.sha(out/'provenance.json'));self.assertEqual(side['case_id'],'s01');self.assertEqual(side['preparer_sha256'],pv.sha(Path(pv.__file__)));self.assertEqual(side['models']['dense']['sha256'],self.art[4]['output_sha256']);self.assertFalse((out/'dense.glb').exists());self.assertFalse((out/'provenance.json').name in side['viewer_files'])
  with self.assertRaisesRegex(ValueError,'already exists'):self.prepare()
 def test_output_inside_run_refused(self):
  with self.assertRaisesRegex(ValueError,'inside source run'):pv.prepare(self.run,self.corpus,self.case,self.run/'viewer',self.three)
 def test_detects_corruption_during_copy(self):
  import shutil
  original=shutil.copyfile
  def copy_and_corrupt(src,dst):
   value=original(src,dst)
   if Path(dst).name=='A.glb':Path(dst).write_bytes(b'corrupted')
   return value
  with patch.object(pv.shutil,'copyfile',side_effect=copy_and_corrupt):
   with self.assertRaisesRegex(ValueError,'copied GLB mismatch'):self.prepare()
  self.assertTrue((self.root/'out').is_dir())
 def test_rejects_missing_or_tampered_dense_before_output(self):
  (self.run/'dense.glb').write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'digest or size'):self.prepare()
  self.assertFalse((self.root/'out').exists())
 def test_rejects_conflicting_terminal_event(self):
  self.events.append({'event':'stopped_or_uncertain','prompt_id':self.prompt});self.writeevents()
  with self.assertRaisesRegex(ValueError,'uncertain'):self.prepare()
 def test_rejects_uuid_variant(self):
  self.meta['prompt_id']=self.prompt.upper();self.dump(self.run/'preparation.json',self.meta)
  with self.assertRaisesRegex(ValueError,'case or prompt'):self.prepare()
 def test_rejects_duplicate_completion(self):
  self.events.append(self.events[-1]);self.writeevents()
  with self.assertRaisesRegex(ValueError,'ambiguous'):self.prepare()
 def test_rejects_wrong_graph_and_history(self):
  self.dump(self.run/'graph.json',{'changed':True})
  with self.assertRaisesRegex(ValueError,'graph hash'):self.prepare()
 def test_rejects_different_history_prompt(self):
  self.history['prompt'][1]='00000000-0000-4000-8000-000000000000';self.dump(self.run/'history-final.json',self.history)
  with self.assertRaisesRegex(ValueError,'history prompt'):self.prepare()
 def test_rejects_foreign_output(self):
  self.art[0]['reference']['subfolder']='other';self.writeevents();self.dump(self.run/'history-final.json',self.history)
  with self.assertRaisesRegex(ValueError,'output reference'):self.prepare()
 def test_rejects_case_and_input_mismatch(self):
  (self.run/'input.png').write_bytes(b'not the input')
  with self.assertRaisesRegex(ValueError,'PNG mismatch'):self.prepare()
 def test_rejects_duplicate_subject(self):
  self.dump(self.corpus,{'subjects':[{'id':'s01'},{'id':'s01'}]})
  with self.assertRaisesRegex(ValueError,'duplicated'):self.prepare()
 def test_rejects_external_uri_before_copy(self):
  path=self.run/'A.glb';doc=json.dumps({'asset':{'version':'2.0'},'images':[{'uri':'https://example.invalid/a.png'}]},separators=(',',':')).encode();doc+=b' '*((-len(doc))%4);data=struct.pack('<4sIII4s',b'glTF',2,20+len(doc),len(doc),b'JSON')+doc;path.write_bytes(data);self.art[0]['output_bytes']=len(data);self.art[0]['output_sha256']=hashlib.sha256(data).hexdigest();self.writeevents()
  with self.assertRaisesRegex(ValueError,'URI refused'):self.prepare()
  self.assertFalse((self.root/'out').exists())
 def test_rejects_wrong_three_version(self):
  (self.three/'package.json').write_text('{"version":"0.0.0"}')
  with self.assertRaisesRegex(ValueError,'Three version'):self.prepare()
if __name__=='__main__':unittest.main()
