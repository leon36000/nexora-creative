import unittest
from unittest.mock import patch
import hashlib
import json
import tempfile
from pathlib import Path

import numpy as np

import surface_distance as sd


class SurfaceDistanceTests(unittest.TestCase):
    def setUp(self):
        self.square = np.array(
            [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float64
        )
        self.square_faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)

    def test_uniform_parallel_surfaces_have_expected_bidirectional_distance(self):
        b = self.square.copy()
        b[:, 2] = 0.25
        pair = sd.prepare_pair(self.square, self.square_faces, b, self.square_faces)

        def plane_project(points, target_vertices, target_faces):
            del target_faces
            target_z = float(target_vertices[:, 2].mean())
            return np.abs(points[:, 2] - target_z)

        result = sd.compare_prepared(pair, 128, 21, plane_project)
        expected = 0.25 / np.sqrt(2.0)
        for direction in ("A_to_B", "B_to_A"):
            normalized = result["directions"][direction]["normalized_by_reference_bbox_diagonal"]
            self.assertTrue(np.allclose(list(normalized.values()), expected, rtol=0, atol=2e-8))
            absolute = result["directions"][direction]["distance_in_input_units"]
            self.assertTrue(np.allclose(list(absolute.values()), 0.25, rtol=0, atol=2e-8))
        self.assertFalse(result["protocol"]["hausdorff"])

    def test_far_b_piece_does_not_change_reference_a_normalizer(self):
        near_b = self.square.copy()
        near_b[:, 2] = 0.25
        far_vertices = np.vstack((near_b, [[100, 0, 0], [101, 0, 0], [100, 1, 0]]))
        far_faces = np.vstack((self.square_faces, [[4, 5, 6]]))
        pair_near = sd.prepare_pair(self.square, self.square_faces, near_b, self.square_faces)
        pair_far = sd.prepare_pair(self.square, self.square_faces, far_vertices, far_faces)
        self.assertAlmostEqual(pair_near.reference_diagonal, np.sqrt(2.0))
        self.assertAlmostEqual(pair_far.reference_diagonal, pair_near.reference_diagonal)
        self.assertGreater(pair_far.combined_bbox_diagonal, 100)
        fixed_distance = 0.125
        project = lambda points, target_vertices, target_faces: np.full(len(points), fixed_distance)
        near_result = sd.compare_prepared(pair_near, 32, 7, project)
        far_result = sd.compare_prepared(pair_far, 32, 7, project)
        self.assertAlmostEqual(near_result["directions"]["A_to_B"]["normalized_by_reference_bbox_diagonal"]["median"], fixed_distance)
        self.assertAlmostEqual(far_result["directions"]["A_to_B"]["normalized_by_reference_bbox_diagonal"]["median"], fixed_distance)

    def test_area_weighted_triangle_selection_is_deterministic(self):
        vertices = np.array(
            [
                [0, 0, 0], [1, 0, 0], [0, 1, 0],  # area 0.5
                [10, 0, 0], [13, 0, 0], [10, 3, 0],  # area 4.5
            ], dtype=np.float64
        )
        faces = np.array([[0, 1, 2], [3, 4, 5]], dtype=np.int64)
        pair = sd.prepare_pair(vertices, faces, vertices, faces)
        rng1 = np.random.Generator(np.random.PCG64(13579))
        rng2 = np.random.Generator(np.random.PCG64(13579))
        pts1, tri1 = sd.sample_surface(pair.a, 10_000, rng1)
        pts2, tri2 = sd.sample_surface(pair.a, 10_000, rng2)
        self.assertTrue(np.array_equal(tri1, tri2))
        self.assertTrue(np.array_equal(pts1, pts2))
        large_fraction = float(np.mean(tri1 == 1))
        self.assertAlmostEqual(large_fraction, 0.9, delta=0.015)
        self.assertTrue(np.isfinite(pts1).all())

    def test_uniform_barycentric_points_stay_inside_triangle(self):
        right_triangle = self.square[[0, 1, 3]]
        pair = sd.prepare_pair(right_triangle, np.array([[0, 1, 2]]), right_triangle, np.array([[0, 1, 2]]))
        points, _ = sd.sample_surface(pair.a, 10_000, np.random.default_rng(4))
        vertices = pair.a.vertices[pair.a.faces[0]]
        edges = (vertices[1:] - vertices[0]).T
        coefficients = np.linalg.lstsq(edges, (points - vertices[0]).T, rcond=None)[0].T
        barycentric = np.column_stack((1 - coefficients.sum(axis=1), coefficients))
        self.assertTrue(np.all(barycentric >= -1e-12))
        self.assertTrue(np.all(barycentric <= 1 + 1e-12))
        self.assertTrue(np.allclose(barycentric.sum(axis=1), 1, atol=1e-12))
        self.assertTrue(np.allclose(barycentric.mean(axis=0), 1 / 3, atol=0.015))

    def test_zero_area_faces_are_excluded_and_counted(self):
        vertices = np.vstack((self.square[:3], [2, 0, 0]))
        faces = np.array([[0, 1, 2], [0, 1, 3]], dtype=np.int64)
        pair = sd.prepare_pair(vertices, faces, vertices, faces)
        self.assertEqual(pair.a.excluded_zero_area_faces, 1)
        self.assertEqual(len(pair.a.faces), 1)

    def test_rejects_invalid_indices_and_all_degenerate_surfaces(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            sd.validate_arrays(self.square, np.array([[0, 1, 8]]), "A")
        degenerate = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=np.float64)
        with self.assertRaisesRegex(ValueError, "no non-zero-area"):
            sd.prepare_pair(degenerate, np.array([[0, 1, 2]]), self.square[:3], self.square_faces[:1])

    def test_rejects_float32_collapsed_triangles(self):
        # The A bbox has unit scale, while B has distinct float64 coordinates
        # too close to survive the float32 MeshLib backend.
        tiny = np.array([[0, 0, 0], [1e-30, 0, 0], [0, 1e-30, 0]], dtype=np.float64)
        with self.assertRaisesRegex(ValueError, "float32 conversion collapsed"):
            sd.prepare_pair(self.square[:3], self.square_faces[:1], tiny, np.array([[0, 1, 2]]))

    def test_rejects_unbounded_sample_counts_and_bad_projector_values(self):
        pair = sd.prepare_pair(self.square[:3], self.square_faces[:1], self.square[:3], self.square_faces[:1])
        with self.assertRaisesRegex(ValueError, "sample count"):
            sd.sample_surface(pair.a, sd.MAX_SAMPLES + 1, np.random.default_rng(0))
        with self.assertRaisesRegex(ValueError, "non-finite"):
            sd._quantiles(np.array([0.0, np.nan]), pair.reference_diagonal)

    def test_extractor_metadata_must_match_binary_arrays(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pos = root / "positions.f64le"
            idx = root / "faces.u32le"
            meta = root / "source.json"
            glb = root / "source.glb"
            glb.write_bytes(b"synthetic GLB payload")
            self.square.astype("<f8").tofile(pos)
            self.square_faces.astype("<u4").tofile(idx)
            metadata = {
                "scope": "fixture",
                "source_sha256": hashlib.sha256(glb.read_bytes()).hexdigest(),
                "positions_sha256": hashlib.sha256(pos.read_bytes()).hexdigest(),
                "faces_sha256": hashlib.sha256(idx.read_bytes()).hexdigest(),
                "vertices": 4,
                "triangles": 2,
            }
            meta.write_text(json.dumps(metadata), encoding="utf-8")
            arrays = sd.load_binary_pair(pos, idx, "A")
            accepted = sd.load_extraction_metadata(meta, glb, pos, idx, arrays)
            self.assertEqual(accepted["source_glb_sha256"], metadata["source_sha256"])
            metadata["faces_sha256"] = "b" * 64
            meta.write_text(json.dumps(metadata), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                sd.load_extraction_metadata(meta, glb, pos, idx, arrays)


class InputBoundsCliTests(unittest.TestCase):
    def test_rejects_oversized_faces_and_vertices_before_fromfile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); pos = root / 'positions'; faces = root / 'faces'; glb = root / 'source.glb'; meta = root / 'source.json'
            glb.write_bytes(b'x'); meta.write_text('{}')
            for position_bytes, face_bytes, expected in ((3*24, 500001*12, 'face count'), ((1500001)*24, 12, 'vertex count')):
                with pos.open('wb') as f: f.truncate(position_bytes)
                with faces.open('wb') as f: f.truncate(face_bytes)
                args = ['surface_distance.py','--a-positions',str(pos),'--a-faces',str(faces),'--a-glb',str(glb),'--a-source-json',str(meta),'--b-positions',str(pos),'--b-faces',str(faces),'--b-glb',str(glb),'--b-source-json',str(meta),'--out',str(root/'result')]
                with patch('sys.argv',args), patch.object(sd.np,'fromfile') as fromfile:
                    with self.assertRaisesRegex(ValueError, expected): sd.main()
                    fromfile.assert_not_called()
                self.assertFalse((root/'result').exists())

    def test_rejects_oversized_second_mesh_before_loading_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); pos=root/'positions'; ok=root/'ok'; large=root/'large'; glb=root/'source.glb'; meta=root/'source.json'
            pos.write_bytes(bytes(72)); ok.write_bytes(bytes(12)); glb.write_bytes(b'x'); meta.write_text('{}')
            with large.open('wb') as f: f.truncate(500001*12)
            argv=['surface_distance.py','--a-positions',str(pos),'--a-faces',str(ok),'--a-glb',str(glb),'--a-source-json',str(meta),'--b-positions',str(pos),'--b-faces',str(large),'--b-glb',str(glb),'--b-source-json',str(meta),'--out',str(root/'result')]
            with patch('sys.argv',argv), patch.object(sd.np,'fromfile') as fromfile:
                with self.assertRaisesRegex(ValueError,'B/candidate: face count'): sd.main()
                fromfile.assert_not_called()

    def test_rejects_unbounded_override_before_fromfile(self):
        with patch.object(sd.np,'fromfile') as fromfile:
            with self.assertRaisesRegex(ValueError,'max faces'): sd.load_binary_pair(Path('a'),Path('b'),'A',2_000_001)
            fromfile.assert_not_called()

if __name__ == "__main__":
    unittest.main()
