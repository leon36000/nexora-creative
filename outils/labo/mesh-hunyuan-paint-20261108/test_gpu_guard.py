import fcntl
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
import capsule_sync
import gpu_guard

class GuardTests(unittest.TestCase):
    def test_pid_response_fails_closed(self):
        self.assertEqual(gpu_guard.parse_pids("12\n34\n"),{12,34})
        for bad in ("unknown","0","12\nerror"):
            with self.assertRaises(ValueError):gpu_guard.parse_pids(bad)
    def test_private_lock_and_competing_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"gpu.lock";path.touch(mode=0o600)
            fd=gpu_guard.open_lock(path,capsule_sync)
            try:
                contender=os.open(path,os.O_RDWR)
                try:
                    with self.assertRaises(BlockingIOError):fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)
                finally:os.close(contender)
            finally:os.close(fd)
    def test_rejects_wide_permissions_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"gpu.lock";path.touch(mode=0o600);path.chmod(0o644)
            with self.assertRaises(ValueError):gpu_guard.open_lock(path,capsule_sync)
            path.chmod(0o600);link=Path(tmp)/"link";link.symlink_to(path)
            with self.assertRaises(ValueError):gpu_guard.open_lock(link,capsule_sync)
    def test_missing_namespace_cannot_prove_release(self):
        self.assertFalse(gpu_guard.namespace_stopped({"identite_namespace":None},None))
        self.assertEqual(gpu_guard.check_release(lambda:False,lambda:set())["status"],"non_verifie")
    def test_persistent_probe_failure_is_bounded(self):
        def bad():raise OSError("synthetic failure")
        start=time.monotonic();result=gpu_guard.check_release(lambda:True,bad)
        self.assertLess(time.monotonic()-start,1);self.assertEqual(result["status"],"non_verifie")
        self.assertEqual(result["error"],"OSError")
    def test_persistent_foreign_process_is_reported_not_signalled(self):
        child=subprocess.Popen([sys.executable,"-c","import sys;sys.stdin.read()"],stdin=subprocess.PIPE)
        try:
            start=time.monotonic();result=gpu_guard.check_release(lambda:True,lambda:{child.pid})
            self.assertLess(time.monotonic()-start,1);self.assertEqual(result["status"],"non_verifie")
            self.assertEqual(result["foreign_pids"],[child.pid]);self.assertIsNone(child.poll())
        finally:child.stdin.close();child.wait(timeout=2)
    def test_clear_requires_both_proofs(self):
        self.assertEqual(gpu_guard.check_release(lambda:True,lambda:set())["status"],"verifie")

if __name__=="__main__":unittest.main()
