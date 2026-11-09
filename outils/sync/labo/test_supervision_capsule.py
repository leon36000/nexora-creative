"""Vraies capsules CPU ; tous les témoins sont conservés dans SYNC_TEST_ROOT."""
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

from outils.sync.labo import capsule_sync, supervision_capsule as s


class CapsulesReelles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp(prefix='sync-supervision-',
            dir=os.getenv('SYNC_TEST_ROOT')))
        if not Path('/usr/bin/bwrap').is_file():
            raise unittest.SkipTest('bubblewrap absent ; aucune simulation présentée comme preuve réelle')
        r = subprocess.run(['/usr/bin/bwrap','--unshare-pid','--ro-bind','/','/',
            '--proc','/proc','--clearenv','--','/usr/bin/true'], env={},
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
        if r.returncode:
            (cls.base/'bwrap-indisponible.log').write_bytes(r.stderr)
            raise unittest.SkipTest('namespaces bubblewrap indisponibles sur cet hôte')

    def lancer(self, nom, attente, delai, controle=None):
        runtime = self.base/(nom+'-runtime')
        runtime.mkdir(mode=0o700)
        run = self.base/(nom+'-run')
        run.mkdir(mode=0o700)
        script = runtime/'probe.py'
        script.write_text('''import json,os,subprocess,sys,socket,time
from pathlib import Path
run=Path(sys.argv[1])
try:
    Path(__file__).with_name('interdit.txt').write_text('interdit')
    ro=False
except OSError as e:
    ro=e.errno==30
subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
(run/'preuve.json').write_text(json.dumps({'ro':ro,'interfaces':[n for _,n in socket.if_nameindex()], 'pid':os.getpid()}))
time.sleep(float(sys.argv[2]))
''')
        script.chmod(0o600)
        lock_path = self.base/(nom+'.lock')
        fd = os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        r,w = os.pipe()
        argv = capsule_sync.construire(runtime,run,Path(sys.executable),script,
            [str(run),str(attente)],Path('/usr/bin/true'),
            'GPU-00000000-0000-0000-0000-000000000000',fd,w)
        anciens = {sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
        try:
            bilan = s.superviser(argv,run,fd,r,w,delai,controle)
            self.assertEqual(anciens,{sig:signal.getsignal(sig) for sig in anciens})
            autre = os.open(lock_path,os.O_RDWR)
            try:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(autre,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:
                os.close(autre)
        finally:
            os.close(fd)
        self.assertTrue(bilan['arret_confirmé'],bilan)
        self.assertNotEqual(bilan['identite_namespace']['ns'],os.readlink('/proc/self/ns/pid'))
        self.assertNotEqual(bilan['identite_namespace']['pid'],bilan['wrapper_pid'])
        self.assertGreaterEqual(len(bilan['processus_observés']),3)
        for avant in bilan['processus_observés']:
            try:
                apres = s.identite(avant['pid'])
            except FileNotFoundError:
                continue
            self.assertFalse(s._meme(avant,apres) and apres['etat'] not in ('Z','X'))
        self.assertEqual(0o600,(run/'execution.log').stat().st_mode&0o777)
        self.assertEqual(0o600,(run/'resultat-execution.json').stat().st_mode&0o777)
        preuve = json.loads((run/'preuve.json').read_text())
        self.assertTrue(preuve['ro'])
        self.assertEqual(preuve['interfaces'],['lo'])
        self.assertEqual(preuve['pid'],2)
        self.assertFalse((runtime/'interdit.txt').exists())
        return bilan

    def test_sortie_normale_emporte_enfant_restant(self):
        self.assertEqual(self.lancer('normal',1,10)['statut'],'succès')

    def test_delai_arrete_nos_processus_et_conserve_les_traces(self):
        b = self.lancer('timeout',60,1.5)
        self.assertEqual(b['statut'],'echec')
        self.assertEqual(b['phase'],'delai_depasse')

    def test_refus_controle_arrete_notre_capsule(self):
        def refuser(idn,pids):
            if len(pids)>=3:
                raise RuntimeError('témoin synthétique de refus')
        b = self.lancer('controle',60,10,refuser)
        self.assertEqual(b['statut'],'echec')
        self.assertEqual(b['phase'],'erreur_supervision')
        self.assertIn('témoin synthétique',b['erreur'])


if __name__ == '__main__':
    unittest.main()
