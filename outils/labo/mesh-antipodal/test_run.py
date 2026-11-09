import hashlib,json,struct,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import run as bench

class ContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
  self.positions=self.p/'positions';self.faces=self.p/'faces';self.glb=self.p/'model.glb';self.meta=self.p/'source.json';self.points=self.p/'points.json';self.ref=self.p/'ref.glb'
  self.positions.write_bytes(struct.pack('<9d',0,0,0,1,0,0,0,1,0));self.faces.write_bytes(struct.pack('<3I',0,1,2));self.glb.write_bytes(b'model');self.ref.write_bytes(b'reference')
  self.m={'vertices':3,'triangles':1,'positions_sha256':bench.sha(self.positions),'faces_sha256':bench.sha(self.faces),'source_sha256':bench.sha(self.glb)};self.meta.write_text(json.dumps(self.m))
  self.q={'reference_glb_sha256':bench.sha(self.ref),'points':[{'id':'p0','point':[0,0,1]}]};self.points.write_text(json.dumps(self.q))
 def validate(self):return bench.validate_inputs(self.positions,self.faces,self.glb,self.meta,self.points,self.ref)
 def test_valid_hashes_and_points(self):
  checks,q,b=self.validate();self.assertEqual((checks['vertices'],checks['triangles'],len(b)),(3,1,24));self.assertEqual(q['points'][0]['id'],'p0')
 def test_tampered_source_and_bad_counts(self):
  self.m['positions_sha256']='0'*64;self.meta.write_text(json.dumps(self.m))
  with self.assertRaisesRegex(ValueError,'metadata mismatch'):self.validate()
  self.m['positions_sha256']=bench.sha(self.positions);self.m['vertices']=True;self.meta.write_text(json.dumps(self.m))
  with self.assertRaisesRegex(ValueError,'metadata mismatch'):self.validate()
 def test_rejects_oversized_faces_before_hash(self):
  with self.faces.open('wb') as f:f.truncate((bench.MAX_FACES+1)*12)
  with patch.object(bench,'sha',side_effect=AssertionError('must not hash')):
   with self.assertRaisesRegex(ValueError,'mesh size outside bounds'):self.validate()
 def test_bad_points_and_reference(self):
  for value in ([{'id':'p','point':[0,0,float('nan')]}],[{'id':'p','point':[0,True,1]}],[{'id':'p','point':[0,1,2]}]*2,[]):
   self.q['points']=value;self.points.write_text(json.dumps(self.q))
   with self.assertRaises(ValueError):self.validate()
  self.q={'reference_glb_sha256':'0'*64,'points':[{'id':'p','point':[0,1,2]}]};self.points.write_text(json.dumps(self.q))
  with self.assertRaisesRegex(ValueError,'reference GLB'):self.validate()
 def test_invalid_or_oversized_json_and_excess_points(self):
  self.meta.write_text('{not json')
  with self.assertRaises(json.JSONDecodeError):self.validate()
  self.meta.write_text(json.dumps(self.m));self.points.write_text(' '*1048577)
  with self.assertRaisesRegex(ValueError,'JSON input too large'):self.validate()
  self.q['points']=[{'id':f'p{i}','point':[0,0,1]} for i in range(bench.MAX_POINTS+1)];self.points.write_text(json.dumps(self.q))
  with self.assertRaisesRegex(ValueError,'point count'):self.validate()
 def test_compile_failure_keeps_failure_without_success_receipt(self):
  args=SimpleNamespace(upstream=self.p,positions=self.positions,faces=self.faces,glb=self.glb,source_json=self.meta,points=self.points,reference_glb=self.ref,out=self.p/'output')
  with patch.object(bench,'verify_upstream'),patch.object(bench.shutil,'which',return_value='/usr/bin/c++'),patch.object(bench,'command',side_effect=[{'argv':['c++','--version']},RuntimeError('synthetic compile failure')]):
   with self.assertRaisesRegex(RuntimeError,'compile failure'):bench.run(args)
  self.assertIn('synthetic compile failure',(args.out/'failure.txt').read_text());self.assertFalse((args.out/'receipt.json').exists());self.assertEqual(bench.sha(self.glb),self.m['source_sha256'])
 def test_existing_output_refused_before_execution(self):
  out=self.p/'out';out.mkdir();args=SimpleNamespace(upstream=self.p,positions=self.positions,faces=self.faces,glb=self.glb,source_json=self.meta,points=self.points,reference_glb=self.ref,out=out)
  with patch.object(bench,'verify_upstream'),patch.object(bench.shutil,'which',return_value='/usr/bin/c++'),patch.object(bench,'command') as cmd:
   with self.assertRaisesRegex(ValueError,'already exists'):bench.run(args)
   cmd.assert_not_called()
 def test_pin_refuses_wrong_revision_and_dirty_headers(self):
  upstream=self.p/'upstream';(upstream/'src/antipodal').mkdir(parents=True);(upstream/'src/antipodal/gwn_mesh.hh').write_text('fixture')
  for revision,changes in [('0'*40,''),(bench.REVISION,' M src/antipodal/gwn_mesh.hh')]:
   with patch.object(bench.subprocess,'run',side_effect=[SimpleNamespace(stdout=revision),SimpleNamespace(stdout=changes)]):
    with self.assertRaisesRegex(ValueError,'revision mismatch'):bench.verify_upstream(upstream)
  with patch.object(bench.subprocess,'run',side_effect=[SimpleNamespace(stdout=bench.REVISION),SimpleNamespace(stdout='')]):bench.verify_upstream(upstream)
 def test_command_preserves_success_and_failure_logs(self):
  ok=bench.command([sys.executable,'-c','print("ok")'],self.p,'ok')
  self.assertEqual((self.p/'ok.stdout').read_text(),'ok\n');self.assertEqual(ok['stdout_sha256'],bench.sha(self.p/'ok.stdout'))
  with self.assertRaisesRegex(RuntimeError,'failed with exit 7'):bench.command([sys.executable,'-c','import sys;sys.exit(7)'],self.p,'bad')
  self.assertTrue((self.p/'bad.stderr').exists())
 def test_command_timeout_is_reported(self):
  with patch.object(bench.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',bench.TIMEOUT)):
   with self.assertRaisesRegex(RuntimeError,'timed out'):bench.command(['fixture'],self.p,'timeout')
  self.assertIn('600 seconds',(self.p/'timeout.stderr').read_text())
 def test_invalid_output_rows_rejected(self):
  for text in ['point=1 direct=0 near_surface_faces=0 antipodal=0 abs_delta=0 near_edge_hits=0 antipodal=0 abs_delta=0 near_edge_hits=0','point=0 direct=0 near_surface_faces=0 antipodal=0 abs_delta=0 near_edge_hits=0']:
   with self.assertRaisesRegex(ValueError,'malformed'):bench.parse_measurements(text,['p'])
 def test_parse_marks_surface_edge_and_nonfinite(self):
  rows=bench.parse_measurements('point=0 direct=nan near_surface_faces=1 antipodal=nan abs_delta=nan near_edge_hits=2 antipodal=0 abs_delta=nan near_edge_hits=0\n',['p'])
  self.assertTrue(rows[0]['ambiguity_detected']);self.assertIsNone(rows[0]['direct_winding']);self.assertIsNone(rows[0]['directions'][0]['winding'])
  with self.assertRaisesRegex(ValueError,'number'):bench.parse_measurements('', ['p'])
 def test_parse_keeps_both_directions_and_delta(self):
  rows=bench.parse_measurements('point=0 direct=0.5 near_surface_faces=0 antipodal=0.5 abs_delta=0 near_edge_hits=0 antipodal=0.6 abs_delta=0.1 near_edge_hits=1\n',['p'])
  self.assertEqual(len(rows[0]['directions']),2);self.assertTrue(rows[0]['ambiguity_detected']);self.assertEqual(rows[0]['directions'][1]['absolute_difference'],0.1);self.assertAlmostEqual(rows[0]['directional_difference'],0.1)
if __name__=='__main__':unittest.main()
