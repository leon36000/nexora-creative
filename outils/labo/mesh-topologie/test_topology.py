import json
import struct
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io
import numpy as np
from topology import analyze, load_arrays, main as topology_main
from repair import read_stl, main as repair_main


class TopologyTest(unittest.TestCase):
    def setUp(self):
        self.v = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]], dtype=float)
        self.f = np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]], dtype=np.int32)

    def test_closed_tetrahedron(self):
        result = analyze(self.v, self.f)
        for mode in ('exact', 'quantized'):
            self.assertEqual((result[mode]['open_edges'],result[mode]['nonmanifold_edges'],result[mode]['components']),(0,0,1))

    def test_open_triangle(self):
        self.assertEqual(analyze(self.v, self.f[:1])['exact']['open_edges'], 3)

    def test_three_faces_sharing_edge(self):
        v = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[0,-1,0]])
        f = np.array([[0,1,2],[1,0,3],[0,1,4]])
        self.assertEqual(analyze(v,f)['exact']['nonmanifold_edges'], 1)

    def test_exact_uv_seam_duplicates_are_welded(self):
        v = np.concatenate([self.v,self.v])
        f = self.f.copy();f[1] += len(self.v)
        self.assertEqual(analyze(v,f)['exact']['open_edges'], 0)

    def test_near_vertices_quantization_changes_partition(self):
        v = np.vstack([self.v, self.v[0] + [1e-6,0,0]])
        self.assertFalse(analyze(v,self.f)['partitions_identical'])

    def test_degenerate_face_and_invalid_inputs(self):
        self.assertEqual(analyze(self.v,np.array([[0,0,1]]))['exact']['degenerate'],1)
        with self.assertRaises(ValueError): analyze(np.array([[float('nan'),0,0]]),np.empty((0,3),dtype=int))
        with self.assertRaises(ValueError): analyze(self.v,np.array([[0,1,8]]))

    def test_truncated_raw_arrays_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = Path(d) / 'p', Path(d) / 'f'
            p.write_bytes(bytes(24) + b'x'); f.write_bytes(bytes(12))
            with self.assertRaises(ValueError): load_arrays(p, f)
            p.write_bytes(bytes(24)); f.write_bytes(bytes(12) + b'x')
            with self.assertRaises(ValueError): load_arrays(p, f)

    def test_binary_stl_and_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'test.stl'
            p.write_bytes(bytes(80) + struct.pack('<I', 1) + struct.pack('<12fH', 0,0,1, 0,0,0, 1,0,0, 0,1,0, 0))
            v, f = read_stl(p)
            self.assertEqual(analyze(v, f)['exact']['open_edges'], 3)
            p.write_bytes(p.read_bytes()[:-1])
            with self.assertRaises(ValueError): read_stl(p)

    def test_cli_is_exclusive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); self.v.astype('<f8').tofile(p/'p');self.f.astype('<u4').tofile(p/'f')
            command=['topology.py','--positions',str(p/'p'),'--faces',str(p/'f'),'--out',str(p/'report.json')]
            with patch.object(sys, 'argv', command): topology_main()
            report=json.loads((p/'report.json').read_text());self.assertEqual(report['exact']['open_edges'],0)
            with patch.object(sys, 'argv', command), self.assertRaises(FileExistsError): topology_main()

    def test_repair_rejects_invalid_divisor_without_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            command=['repair.py','--positions',str(p/'missing-p'),'--faces',str(p/'missing-f'),'--out',str(p/'out'),'--voxel-divisor','0']
            with patch.object(sys, 'argv', command), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): repair_main()
            self.assertFalse((p/'out').exists())

if __name__ == '__main__': unittest.main()
