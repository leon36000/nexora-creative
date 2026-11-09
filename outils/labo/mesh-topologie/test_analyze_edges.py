import unittest
from unittest.mock import patch
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
import analyze_edges as ae
from analyze_edges import analyze_arrays, verify_provenance

class IncidenceTests(unittest.TestCase):
    def test_two_tetrahedra_share_welded_edge_but_not_raw_indices(self):
        a=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],dtype=float)
        b=np.array([[0,0,0],[1,0,0],[0,-1,0],[0,0,-1]],dtype=float)
        v=np.vstack([a,b])
        f=np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3],[4,6,5],[4,5,7],[4,7,6],[5,6,7]],dtype=np.uint32)
        uv=np.arange(len(v)*2,dtype=np.float32).reshape(-1,2)
        r=analyze_arrays(v,f,uv)
        self.assertEqual(r['raw_edges']['nonmanifold_edge_classes'],0)
        self.assertEqual(r['exact_weld_edges']['nonmanifold_edge_classes'],1)
        edge=r['exact_weld_edges']['nonmanifold_edges'][0]
        self.assertEqual(edge['incident_face_count'],4)
        self.assertEqual(len(edge['raw_edge_variants']),2)
        self.assertEqual(sorted(x['incidence_count'] for x in edge['raw_edge_variants']),[2,2])
        self.assertEqual(len(edge['connected_components']['raw_index_ids']),2)
        self.assertEqual(len(edge['connected_components']['exact_weld_ids']),1)
        self.assertTrue(all(np.isfinite(x['opposite_radial_angle_degrees']) for x in edge['incidents']))

    def test_three_faces_on_same_raw_edge_report_orientation_and_incidents(self):
        v=np.array([[0,0,0],[1,0,0],[0,1,0],[0,-1,0],[0,0,1]],dtype=float)
        f=np.array([[0,1,2],[1,0,3],[0,1,4]],dtype=np.uint32)
        r=analyze_arrays(v,f)
        self.assertEqual(r['raw_edges']['nonmanifold_edge_classes'],1)
        self.assertEqual(r['exact_weld_edges']['nonmanifold_edge_classes'],1)
        self.assertEqual(r['raw_edges']['nonmanifold_edges'][0]['incident_face_count'],3)
        self.assertEqual(r['exact_weld_edges']['nonmanifold_edges'][0]['orientation_signs'],{'+':2,'-':1})

    def test_face_duplicate_after_exact_weld_is_not_silently_discarded(self):
        v=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,0],[1,0,0],[0,1,0]],dtype=float)
        f=np.array([[0,1,2],[3,4,5]],dtype=np.uint32)
        r=analyze_arrays(v,f)
        self.assertEqual(len(r['duplicate_geometric_faces_after_exact_weld']),1)
        self.assertEqual(len(r['duplicate_geometric_faces_after_exact_weld'][0]),2)

    def test_uv_variants_are_reported_at_welded_endpoint(self):
        v=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,0],[0,-1,0]],dtype=float)
        f=np.array([[0,1,2],[1,3,4]],dtype=np.uint32)
        uv=np.array([[0,0],[1,0],[0,1],[0.2,0.3],[0,1]],dtype=np.float32)
        r=analyze_arrays(v,f,uv)
        edge=next(e for e in r['exact_weld_edges']['nonmanifold_edges'] if e['incident_face_count']>2) if r['exact_weld_edges']['nonmanifold_edges'] else None
        # The seam is not nonmanifold; endpoint variants appear only in a diagnostic output edge.
        self.assertIsNone(edge)
        # Re-run with an added third triangle across the same welded edge to expose its endpoint UV variants.
        v=np.vstack([v,[[0,0,-1]]]); uv=np.vstack([uv,[[1,1]]]); f=np.vstack([f,[[3,1,5]]]).astype(np.uint32)
        r=analyze_arrays(v,f,uv)
        item=next(e for e in r['exact_weld_edges']['nonmanifold_edges'] if e['incident_face_count']==3)
        self.assertGreater(max(item['uv0_endpoint_variant_counts'].values()),1)

    def test_invalid_uv_and_indices_rejected(self):
        v=np.array([[0,0,0],[1,0,0],[0,1,0]],dtype=float); f=np.array([[0,1,3]],dtype=np.uint32)
        with self.assertRaises(ValueError): analyze_arrays(v,f)
        with self.assertRaises(ValueError): analyze_arrays(v,np.array([[0,1,2]],dtype=np.uint32),np.array([[0,0],[float('nan'),0],[0,1]]))

class ProvenanceAndBoundsTests(unittest.TestCase):
    def fixture(self, root):
        positions=root/'positions'; faces=root/'faces'; uv=root/'uv'; glb=root/'model.glb'; meta=root/'source.json'
        np.array([[0,0,0],[1,0,0],[0,1,0]],dtype='<f8').tofile(positions)
        np.array([[0,1,2]],dtype='<u4').tofile(faces)
        np.array([[0,0],[1,0],[0,1]],dtype='<f4').tofile(uv); glb.write_bytes(b'synthetic')
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        m={'vertices':3,'triangles':1,'positions_sha256':digest(positions),'faces_sha256':digest(faces),'uv0_sha256':digest(uv),'source_sha256':digest(glb)}
        meta.write_text(json.dumps(m)); return positions,faces,uv,glb,meta,m

    def test_metadata_hashes_and_uv_are_required_and_verified(self):
        with tempfile.TemporaryDirectory() as d:
            p,f,u,g,m,data=self.fixture(Path(d))
            self.assertEqual(verify_provenance(m,p,f,u,g)['vertices'],3)
            data['uv0_sha256']='0'*64; m.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'UV0 hash'): verify_provenance(m,p,f,u,g)
            data.pop('uv0_sha256'); m.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'UV0 hash'): verify_provenance(m,p,f,u,g)

    def test_wrong_glb_and_wrong_array_and_count_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p,f,u,g,m,data=self.fixture(Path(d)); g.write_bytes(b'other')
            with self.assertRaisesRegex(ValueError,'GLB hash'): verify_provenance(m,p,f,None,g)
            f.write_bytes(bytes(12))
            with self.assertRaisesRegex(ValueError,'array hash'): verify_provenance(m,p,f)
            data['vertices']=4; m.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'byte sizes'): verify_provenance(m,p,f)

    def test_cli_rejects_dense_before_array_load(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p,f,u,g,m,_=self.fixture(root)
            with f.open('wb') as stream: stream.truncate(500001*12)
            cli=Path(__file__).with_name('analyze_edges.py')
            r=subprocess.run([sys.executable,str(cli),'--positions',str(p),'--faces',str(f),'--source-json',str(m),'--out',str(root/'out')],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('before allocation',r.stderr);self.assertFalse((root/'out').exists())

    def test_nondegenerate_at_small_and_large_scales(self):
        for scale in (1e-100,1.,1e100):
            v=np.array([[0,0,0],[scale,0,0],[0,scale,0]])
            r=analyze_arrays(v,np.array([[0,1,2]]))
            self.assertEqual(r['input_counts']['degenerate_triangles_by_exact_weld'],0)

class VertexBoundsCliTests(unittest.TestCase):
    def test_rejects_oversized_vertices_before_fromfile(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);pos=root/'positions';faces=root/'faces';meta=root/'source.json'
            with pos.open('wb') as f: f.truncate(1500001*24)
            with faces.open('wb') as f: f.truncate(12)
            meta.write_text('{}')
            argv=['analyze_edges.py','--positions',str(pos),'--faces',str(faces),'--source-json',str(meta),'--out',str(root/'out')]
            with patch('sys.argv',argv),patch.object(ae.np,'fromfile') as fromfile:
                with self.assertRaisesRegex(SystemExit,'vertex count'): ae.main()
                fromfile.assert_not_called()
            self.assertFalse((root/'out').exists())

if __name__=='__main__': unittest.main(verbosity=2)
