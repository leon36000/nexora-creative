import hashlib
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
import numpy as np
import bench_inpaint as bench

class InputTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        self.texture=self.base/'texture.npy';self.mask=self.base/'mask.npy'
        self.t=np.array([[[0.0,0.5,1.0],[0.25,0.75,0.0]]],dtype=np.float32)
        self.m=np.array([[0,255]],dtype=np.uint8)
        self.write(self.t,self.m)
    def tearDown(self):self.tmp.cleanup()
    def write(self,texture,mask):
        np.save(self.texture,texture);np.save(self.mask,mask)
    def test_valid_roundtrip(self):
        t,m=bench.load_inputs(self.texture,self.mask)
        np.testing.assert_array_equal(t,self.t);np.testing.assert_array_equal(m,self.m)
    def test_wrong_shapes_and_dtypes_rejected(self):
        cases=[(self.t.astype(np.float64),self.m),(self.t[:,:,0],self.m),(self.t,self.m.astype(np.int32)),(self.t,self.m[:,:1]),(np.empty((0,2,3),np.float32),np.empty((0,2),np.uint8))]
        for t,m in cases:
            with self.subTest(shape=t.shape,dtype=t.dtype,mask=m.shape):
                self.write(t,m)
                with self.assertRaises(ValueError):bench.load_inputs(self.texture,self.mask)
    def test_fortran_order_rejected_before_output(self):
        texture=np.asfortranarray(np.zeros((3,4,3),np.float32))
        mask=np.asfortranarray(np.full((3,4),255,np.uint8))
        for t,m in ((texture,np.full((3,4),255,np.uint8)),(np.zeros((3,4,3),np.float32),mask)):
            self.write(t,m)
            with self.assertRaisesRegex(ValueError,'C-contiguous'):bench.load_inputs(self.texture,self.mask)
            self.assertFalse((self.base/'result').exists())
    def test_nonfinite_and_out_of_range_rejected(self):
        for value in (np.nan,np.inf,-0.1,1.1):
            t=self.t.copy();t[0,0,0]=value;self.write(t,self.m)
            with self.subTest(value=value),self.assertRaises(ValueError):bench.load_inputs(self.texture,self.mask)
    def test_nonbinary_mask_rejected(self):
        self.write(self.t,np.array([[0,1]],np.uint8))
        with self.assertRaises(ValueError):bench.load_inputs(self.texture,self.mask)
    def test_npz_archive_rejected(self):
        archive=self.base/'texture.npz';np.savez(archive,texture=self.t)
        with self.assertRaises(ValueError):bench.load_inputs(archive,self.mask)
    def test_pickle_refused(self):
        np.save(self.texture,np.array([{'x':1}],dtype=object))
        with self.assertRaises(ValueError):bench.load_inputs(self.texture,self.mask)
    def test_array_hash_matches_actual_bytes_and_noncontiguous_rejected(self):
        self.assertEqual(bench.sha_array(self.m),hashlib.sha256(self.m.tobytes()).hexdigest())
        with self.assertRaises(ValueError):bench.sha_array(self.t[:,:,0])
    def test_output_directory_is_exclusive(self):
        path=self.base/'result';self.assertEqual(bench.create_output(path),path)
        with self.assertRaises(FileExistsError):bench.create_output(path)
    def test_opencv_attestation_checks_version_and_directory(self):
        module=self.base/'cv2.py';module.write_text('fixture',encoding='utf-8')
        metadata=SimpleNamespace(__file__=str(module),__version__='4.11.0',getBuildInformation=lambda:'fixture build')
        actual=bench.attest_opencv(metadata,'4.11.0',self.base)
        self.assertEqual(actual['module_sha256'],hashlib.sha256(b'fixture').hexdigest())
        with self.assertRaises(ValueError):bench.attest_opencv(metadata,'4.9.0',self.base)
        other=self.base/'other';other.mkdir()
        with self.assertRaises(ValueError):bench.attest_opencv(metadata,'4.11.0',other)
    def test_file_hash(self):
        self.assertEqual(bench.sha_file(self.mask),hashlib.sha256(self.mask.read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
