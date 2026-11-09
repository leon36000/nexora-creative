import hashlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import capsule

class CapsuleTests(unittest.TestCase):
    def test_run_names(self):
        self.assertEqual(capsule.safe_name('paint-03'),'paint-03')
        for name in ('','../escape','A','a/b','x'*49):
            with self.subTest(name=name),self.assertRaises(ValueError):capsule.safe_name(name)
    def test_dry_run_does_not_touch_gpu_or_create_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);code=base/'code';root=base/'root';code.mkdir();root.mkdir()
            blender=base/'blender';blender.write_bytes(b'blender');blender.chmod(0o755)
            lock=base/'lock';lock.write_text('')
            manifest={'blender_sha256':hashlib.sha256(b'blender').hexdigest(),'runtime_versions':{'torch':'test'}}
            (code/'input-manifest.json').write_text(json.dumps(manifest))
            argv=['capsule','--root',str(root),'--lock',str(lock),'--blender',str(blender),'--run-id','test','--dry-run']
            with patch.object(capsule,'CODE',code),patch.object(capsule,'verify',return_value={'verified':True,'files':[{}]}),patch.object(capsule,'smi') as gpu,patch.object(capsule.subprocess,'run',return_value=SimpleNamespace(stdout='{"torch":"test"}')),patch.object(sys,'argv',argv):
                capsule.main();gpu.assert_not_called()
            self.assertFalse((root/'capsules').exists())
    def test_error_before_popen_is_bounded_and_not_verified(self):
        events=[]
        fake=SimpleNamespace(superviser=lambda *args: (_ for _ in ()).throw(OSError('before Popen')))
        with patch.object(capsule,'pids',return_value=set()):
            start=time.monotonic()
            with self.assertRaises(OSError):
                capsule.supervise_and_check([],Path('/unused'),3,4,5,None,fake,lambda e,**x:events.append((e,x)))
        self.assertLess(time.monotonic()-start,1)
        self.assertEqual(events[0][1]['status'],'non_verifie')

if __name__=='__main__':unittest.main()
