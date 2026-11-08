import hashlib
import tempfile
import unittest
from pathlib import Path
from verify_manifest import verify

class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); (self.root/'input.bin').write_bytes(b'abc')
        self.entry={'path':'input.bin','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}
        self.manifest={'schema':'nexora-mesh-paint-inputs-v1','files':[self.entry]}
    def test_matching(self):self.assertTrue(verify(self.root,self.manifest)['verified'])
    def test_missing(self):
        self.entry['path']='missing';self.assertEqual(verify(self.root,self.manifest)['files'][0]['status'],'missing')
    def test_mismatch(self):
        self.entry['bytes']=4;self.assertEqual(verify(self.root,self.manifest)['files'][0]['status'],'mismatch')
    def test_symlink_refused(self):
        (self.root/'link').symlink_to(self.root/'input.bin');self.entry['path']='link'
        with self.assertRaises(ValueError):verify(self.root,self.manifest)
    def test_traversal_refused(self):
        self.entry['path']='../input.bin'
        with self.assertRaises(ValueError):verify(self.root,self.manifest)
    def test_noncanonical_refused(self):
        self.entry['path']='./input.bin'
        with self.assertRaises(ValueError):verify(self.root,self.manifest)
    def test_duplicate_refused(self):
        self.manifest['files'].append(dict(self.entry))
        with self.assertRaises(ValueError):verify(self.root,self.manifest)
    def test_empty_refused(self):
        self.manifest['files']=[]
        with self.assertRaises(ValueError):verify(self.root,self.manifest)

if __name__=='__main__':unittest.main()
