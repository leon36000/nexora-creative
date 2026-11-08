"""Exerce le vrai superviseur et son contrôle AV, avec enfant simulé CPU."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from unittest import mock

from outils.sync.labo import highsync_execution as e

ROOT = Path(os.environ.get('SYNC_TEST_ROOT') or os.environ['TMPDIR'])
FFMPEG = Path(os.environ.get('SYNC_TEST_FFMPEG') or os.environ.get('SYNC_FFMPEG') or shutil.which('ffmpeg'))
FFPROBE = Path(os.environ.get('SYNC_TEST_FFPROBE') or os.environ.get('SYNC_FFPROBE') or shutil.which('ffprobe'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class ParcoursHighSyncTest(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / ('highsync-parcours-' + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.run = self.root/'essai'; self.run.mkdir()
        self.runtime = self.run/'runtime'; self.runtime.mkdir()
        (self.runtime/'inference_adaptee.py').write_text('# simulé')
        self.audio = self.run/'audio-entree.wav'
        self.video = self.run/'video-entree.mp4'
        self.reference = self.root/'sortie-modele-synthetique.mp4'
        def ff(*args):
            subprocess.run([str(FFMPEG), '-v','error','-nostdin','-n',*args], check=True, timeout=30)
        ff('-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=1',str(self.audio))
        ff('-f','lavfi','-i','color=black:s=32x32:r=25:d=1.2','-c:v','libx264','-pix_fmt','yuv420p',str(self.video))
        ff('-f','lavfi','-i','color=black:s=32x32:r=25:d=1','-i',str(self.audio),'-map','0:v','-map','1:a','-c:v','libx264','-c:a','aac',str(self.reference))
        self.orig = self.root/'audio-original.mp3'; self.orig.write_bytes(b'source synthetique')
        provenance = self.root/'provenance-audio.json'
        provenance.write_text(json.dumps({'audio_original_sha256':sha(self.orig)}))
        self.evidence = self.root/'evidence.json'; self.evidence.write_text('{}')
        prep = self.run/'manifest.json'
        prep.write_text(json.dumps({'entrees':{'video_sha256':sha(self.video),'audio_sha256':sha(self.audio)}}))
        cfg = self.run/'runtime-config.json'; cfg.write_text('{}')
        self.weights = self.root/'fake-s3fd'; self.weights.write_bytes(b'poids factices')
        self.lock = self.root/'active-gpu.lock'; self.lock.touch(mode=0o600)
        opts = {'python':'/usr/bin/true', 'ffmpeg':str(FFMPEG), 'ffprobe':str(FFPROBE), 'nvidia_smi':'/usr/bin/true',
                'deps':str(self.root), 'gpu_uuid':'GPU-factice', 'cuda_fraction':.6, 'min_vram_mib':12288,
                'min_ram_mib':12288,'processus_autorises':{},'s3fd_utils_root':str(self.root), 's3fd_poids':str(self.weights),
                'gpu_lock':str(self.lock),'delai_secondes':1, 'audio_provenance_path':str(self.evidence),
                'audio_provenance_sha256':sha(self.evidence)}
        commande = [opts['python'], str(self.runtime/'inference_adaptee.py'), '--config',str(cfg),
                    '--source_video',str(self.video),'--driving_audio',str(self.audio),'--output',str(self.run/'sortie.mp4'),
                    '--ffmpeg',opts['ffmpeg'],'--cuda-fraction','0.6','--s3fd-utils-root',opts['s3fd_utils_root'],
                    '--s3fd-poids',opts['s3fd_poids']]
        self.plan = {'statut':'planifie_sans_inference','options':opts,'poids':{},'commande':commande,
                     'preparation_sha256':sha(prep),'provenance_sha256':sha(provenance),'configuration_sha256':sha(cfg),
                     'source':str(self.root),'source_manifest':str(self.evidence),
                     'executables_sha256':{k:sha(Path(opts[k]).resolve()) for k in ('python','ffmpeg','ffprobe','nvidia_smi')},
                     'runtime_sha256':{'inference_adaptee.py':sha(self.runtime/'inference_adaptee.py')}}
        (self.run/'plan-execution.json').write_text(json.dumps(self.plan))
        self.plan_sha = sha(self.run/'plan-execution.json')

    def lancer(self, mode, verrouille=False):
        real_popen = subprocess.Popen
        def popen(cmd, *args, **kwargs):
            if cmd == self.plan['commande']:
                self.assertEqual(len(kwargs.get('pass_fds', ())), 1)
                os.fstat(kwargs['pass_fds'][0])
                if mode == 'ok':
                    shutil.copyfile(self.reference, self.run/'sortie.mp4')
                    cmd = ['/usr/bin/true']
                elif mode == 'error':
                    cmd = ['/usr/bin/false']
                else:
                    cmd = ['/usr/bin/sleep','10']
            return real_popen(cmd, *args, **kwargs)
        lock = self.lock.open('r+')
        if verrouille:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            with mock.patch.object(e, 'GPU_LOCK_PC3', self.lock), mock.patch.object(e, 'POIDS', {}), \
                 mock.patch.object(e.highsync_s3fd, 'WEIGHT_SHA', sha(self.weights)), \
                 mock.patch.object(e.highsync_s3fd, 'SOURCE_SHA', {}), \
                 mock.patch.object(e, 'verifier_sources'), \
                 mock.patch.object(e, 'snapshot_gpu', return_value=({'free_mib':15573,'utilisation':0},[])), \
                 mock.patch.object(e, '_memoire_disponible_mib', return_value=20000), \
                 mock.patch.object(e.subprocess, 'Popen', side_effect=popen), \
                 mock.patch.object(e, '_vram_enfant', return_value=None), \
                 mock.patch.object(e.time, 'sleep', return_value=None):
                return e.executer(self.run,self.plan_sha)
        finally:
            lock.close()

    def test_succes_enfant_puis_validation_av_reelle(self):
        result = self.lancer('ok')
        self.assertEqual(result['statut'],'av_valide_non_jugé')
        self.assertTrue(result['validation_av']['valide'])
        self.assertEqual(result['sortie_sha256'],sha(self.reference))
        self.assertNotIn('vram_max_observe_mib',result)

    def test_echec_enfant_n_annonce_pas_av_valide(self):
        result = self.lancer('error')
        self.assertEqual(result['phase'],'inference_echouee')
        self.assertEqual(result['statut'],'echec')
        self.assertNotIn('validation_av',result)

    def test_timeout_arrete_uniquement_enfant(self):
        result = self.lancer('timeout')
        self.assertEqual(result['phase'],'delai_depasse')
        self.assertTrue(result['arret_confirme'])
        self.assertTrue(result['descendants_non_verifies'])

    def test_flock_persiste_dans_enfant_apres_sortie_parent(self):
        programme = """import fcntl,os,subprocess,sys
f=os.open(sys.argv[1],os.O_RDWR)
fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
p=subprocess.Popen(['/usr/bin/sleep','1'],pass_fds=(f,),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(p.pid,flush=True)
"""
        parent = subprocess.run([sys.executable, '-c', programme, str(self.lock)],
                                capture_output=True, text=True, check=True, timeout=5)
        self.assertTrue(parent.stdout.strip().isdigit())
        with self.lock.open('r+') as fichier:
            with self.assertRaises(BlockingIOError):
                fcntl.flock(fichier, fcntl.LOCK_EX | fcntl.LOCK_NB)
            deadline = time.monotonic() + 4
            while True:
                try:
                    fcntl.flock(fichier, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.05)

    def test_verrou_deja_tenu_refuse_avant_enfant(self):
        with self.assertRaises(BlockingIOError):
            self.lancer('ok',verrouille=True)
        self.assertFalse((self.run/'execution-pid.json').exists())
        self.assertFalse((self.run/'sortie.mp4').exists())


if __name__ == '__main__':
    unittest.main()
