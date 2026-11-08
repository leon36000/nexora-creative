"""Real short CPU capsules; GPU queries are simulated, never executed."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import capsule
import capsule_sync
import gpu_guard
import supervision_capsule as supervision

class ShortCapsules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Path(tempfile.mkdtemp(prefix='paint-supervision-',dir=os.environ.get('SYNC_TEST_ROOT')))
        if not Path('/usr/bin/bwrap').is_file():raise unittest.SkipTest('bubblewrap absent')
        check=subprocess.run(['/usr/bin/bwrap','--unshare-pid','--ro-bind','/','/','--proc','/proc','--clearenv','--','/usr/bin/true'],env={},capture_output=True,timeout=5)
        if check.returncode:raise unittest.SkipTest('bubblewrap PID namespaces unavailable')

    def execute(self,name,delay,control=None,foreign=None):
        runtime=self.base/(name+'-runtime');runtime.mkdir(mode=0o700)
        run=self.base/(name+'-run');run.mkdir(mode=0o700)
        script=runtime/'probe.py';script.write_text('import subprocess,sys,time\nsubprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"])\ntime.sleep('+repr(delay)+')\n');script.chmod(0o600)
        lock=self.base/(name+'.lock');lock.touch(mode=0o600)
        fd=gpu_guard.open_lock(lock,capsule_sync);read_fd,write_fd=os.pipe()
        argv=capsule_sync.construire(runtime,run,Path(sys.executable),script,[],Path('/usr/bin/true'),'GPU-00000000-0000-0000-0000-000000000000',fd,write_fd)
        class FastSupervision:
            _namespace=staticmethod(supervision._namespace)
            identite=staticmethod(supervision.identite)
            _meme=staticmethod(supervision._meme)
            @staticmethod
            def superviser(argv,run,fd,r,w,_delai,controle):return supervision.superviser(argv,run,fd,r,w,1.5,controle)
        events=[]
        try:
            with patch.object(capsule,'pids',return_value=set() if foreign is None else {foreign.pid}):
                try:result=capsule.supervise_and_check(argv,run,fd,read_fd,write_fd,control,FastSupervision,lambda event,**x:events.append((event,x)))
                except RuntimeError:result=None
            other=os.open(lock,os.O_RDWR)
            try:
                with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:os.close(other)
        finally:os.close(fd)
        return result,events

    def test_real_child_exits_and_namespace_is_empty(self):
        result,events=self.execute('normal',.3)
        self.assertEqual(result['statut'],'succès');self.assertTrue(result['arret_confirmé'])
        self.assertEqual(events[-1][1]['status'],'verifie')

    def test_timeout_stops_only_capsule(self):
        result,events=self.execute('timeout',60)
        self.assertIsNone(result);self.assertEqual(events[0][1]['phase'],'delai_depasse')
        self.assertEqual(events[-1][1]['status'],'verifie')

    def test_probe_error_stops_capsule(self):
        def broken(_identity,_pids):raise OSError('synthetic GPU query failure')
        result,events=self.execute('probe-error',60,control=broken)
        self.assertIsNone(result);self.assertEqual(events[0][1]['phase'],'erreur_supervision')
        self.assertEqual(events[-1][1]['status'],'verifie')

    def test_foreign_pid_is_not_killed_and_release_is_not_verified(self):
        foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
        try:
            result,events=self.execute('foreign',.3,foreign=foreign)
            self.assertIsNone(result);self.assertIsNone(foreign.poll())
            self.assertEqual(events[-1][1]['status'],'non_verifie')
            self.assertEqual(events[-1][1]['foreign_pids'],[foreign.pid])
        finally:foreign.terminate();foreign.wait(timeout=2)

if __name__=='__main__':unittest.main()
