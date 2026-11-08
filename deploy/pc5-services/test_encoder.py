"""Sans GPU : python test_encoder.py (FastAPI/httpx/python-multipart requis)."""
import asyncio
import errno
import fcntl
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
import encoder_endpoint as ep


def peut_signaler_son_enfant():
    """Teste uniquement SIGKILL sur un enfant court, avec attente bornée s'il sort naturellement."""
    enfant = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(.25)'],
                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, env={})
    try:
        enfant.kill()
    except (PermissionError, ProcessLookupError):
        enfant.wait(timeout=1)
        return False
    try:
        enfant.wait(timeout=1)
    except subprocess.TimeoutExpired:
        # Le processus a son propre délai court; on le réapprend sans nouvelle tentative de signal.
        enfant.wait(timeout=1)
        return False
    return enfant.returncode == -signal.SIGKILL


class Encoder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='test-encoder-')
        self.root = Path(self.tmp.name)
        self.old = {k: getattr(ep, k) for k in ('FICHIER_JETON', 'RACINE', 'FFMPEG', 'FFPROBE', 'TAILLE_MAX', 'PLAFOND_ESSAIS', 'DELAI_S', 'H264_VALIDE', 'HEVC_VALIDE')}
        ep.H264_VALIDE = ep.HEVC_VALIDE = True
        token = self.root/'jeton'
        token.write_text('jeton-test-encoder\n')
        ep.FICHIER_JETON, ep.RACINE = str(token), str(self.root/'jobs')
        # De vrais processus enfants, aucune simulation du cycle FastAPI/subprocess.
        ep.FFMPEG = str(self.script('ffmpeg', '''
import pathlib,sys,time
args=sys.argv[1:]
root=pathlib.Path(__file__).parent
with (root/'commandes.jsonl').open('a') as f: f.write(__import__('json').dumps(args)+'\\n')
if '-f' in args and args[-1]=='-': sys.exit(0)
src=pathlib.Path(args[args.index('-i')+1]).read_bytes()
if b'ECHEC' in src: sys.exit(1)
if b'DELAI' in src: time.sleep(2)
codec='HEVC' if 'hevc_nvenc' in args else 'H264'
pathlib.Path(args[-1]).write_bytes(b'ENCODE-'+codec.encode()+src)
'''))
        ep.FFPROBE = str(self.script('ffprobe', '''
import json,pathlib,sys
src=pathlib.Path(sys.argv[-1]).read_bytes()
if b'INVALIDE' in src: sys.exit(1)
out=b'ENCODE' in src
hevc=b'ENCODE-HEVC' in src
v={'codec_type':'video','codec_name':'hevc' if hevc else 'h264','width':1344,'height':768,'avg_frame_rate':'24/1','pix_fmt':'yuv420p10le' if hevc else 'yuv420p'}
if b'ENCODE-HEVC8BIT' in src: v['pix_fmt']='yuv420p'
if b'HDR' in src: v['color_transfer']='smpte2084'
if b'422' in src: v['pix_fmt']='yuv422p'
if b'8K' in src: v['width']=7680
if b'FPS' in src: v['avg_frame_rate']='120/1'
duration=601 if b'LONG' in src else (1 if out and b'TRONQUE' in src else 12)
print(json.dumps({'format':{'duration':str(duration)},'streams':[v]}))
'''))
        self.app = FastAPI()
        self.gpu_lock = threading.Lock()
        ep.installer(self.app, self.gpu_lock)
        self.c = TestClient(self.app)
        self.auth = {'Authorization': 'Bearer jeton-test-encoder'}

    def script(self, name, src):
        p = self.root/name
        p.write_text('#!'+sys.executable+'\n'+src)
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
        return p

    def tearDown(self):
        self.c.close()
        for k, v in self.old.items(): setattr(ep, k, v)
        self.tmp.cleanup()

    def post(self, media=b'VIDEO', options=None, auth=True, files=None):
        return self.c.post('/encoder', files=files or [('files', ('../../un-chemin.mp4', media, 'video/mp4'))],
                           data={'options': json.dumps(options or {})}, headers=self.auth if auth else {})

    def propre(self):
        self.assertTrue(ep.VERROU.acquire(blocking=False))
        ep.VERROU.release()

    def test_auth_avant_corps(self):
        self.assertEqual(self.post(auth=False).status_code, 401)
        self.assertEqual(self.c.post('/encoder', content=b'invalide', headers={'Authorization':'Bearer faux'}).status_code,401)
        ep.FICHIER_JETON = str(self.root/'absent')
        self.assertEqual(self.post().status_code,503)
        self.assertFalse(Path(ep.RACINE).exists())

    def test_flux_h264_hevc(self):
        for codec in ('h264','hevc'):
            r = self.post(options={'codec':codec})
            self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(r.content,b'ENCODE-'+codec.upper().encode()+b'VIDEO')
            self.assertEqual(int(r.headers['content-length']),len(r.content))
            self.assertEqual(r.headers['x-nexora-encodeur'],codec+'_nvenc')
            cmds=[json.loads(s) for s in (self.root/'commandes.jsonl').read_text().splitlines()]
            cmd=cmds[-2]
            self.assertIn('p7',cmd); self.assertIn('fullres',cmd)
            self.assertIn('p010le' if codec=='hevc' else 'yuv420p',cmd)
            self.assertNotIn('../../un-chemin.mp4',cmd)
            self.propre()

    def test_rejet_medias(self):
        for data,code in ((b'INVALIDE',422),(b'LONG',413),(b'8K',413),(b'FPS',413),(b'HDR',422),(b'422',422),(b'ECHEC',422),(b'TRONQUE',422)):
            r=self.post(data); self.assertEqual(r.status_code,code,(data,r.text)); self.propre()

    def test_options_fermees(self):
        for o in ({'codec':'av1'},{'chemin':'/etc/passwd'},{'filtre':'movie=/etc/passwd'},
                  {'taille':[1921,1080]},{'taille':[True,720]},
                  {'assemblage':{'transition':'fondu','durees':[12],'fondu':float('nan'),'son':False}}):
            self.assertEqual(self.post(options=o).status_code,422); self.propre()

    def test_codec_ferme_sans_banc_qualite(self):
        ep.H264_VALIDE = ep.HEVC_VALIDE = False
        for codec in ('h264', 'hevc'):
            self.assertEqual(self.post(options={'codec':codec}).status_code,503)
            self.propre()

    def test_rejette_sortie_hevc_8bits(self):
        ep.FFMPEG = str(self.script('ffmpeg-hevc-8bits', '''
import pathlib,sys
args=sys.argv[1:]
if '-f' in args and args[-1]=='-': sys.exit(0)
pathlib.Path(args[-1]).write_bytes(b'ENCODE-HEVC8BIT')
'''))
        self.assertEqual(self.post(options={'codec':'hevc'}).status_code,422)
        self.propre()

    def test_assemblage_graphe_fixe(self):
        files=[('files',('a.mp4',b'VIDEO')),('files',('b.mp4',b'VIDEO'))]
        for transition in ('coupe','fondu'):
            o={'assemblage':{'transition':transition,'durees':[12,12],'fondu':.35,'son':False},'taille':[1280,720]}
            # Faux ffprobe rend 12s : rejet final attendu car l'assemblage devrait faire ~24s.
            self.assertEqual(self.post(options=o,files=files).status_code,422)
            cmds=[json.loads(s) for s in (self.root/'commandes.jsonl').read_text().splitlines()]
            filtre=cmds[-1][cmds[-1].index('-filter_complex')+1]
            self.assertIn('xfade=' if transition=='fondu' else 'concat=',filtre)
            self.propre()
        self.assertEqual(self.post(files=files).status_code,422)

    def test_taille_bornee_et_multipart_tronque(self):
        ep.TAILLE_MAX=100
        self.assertEqual(self.post(b'x'*101).status_code,413)
        self.propre()
        self.assertEqual(self.c.post('/encoder',content=b'--x\r\n',headers={**self.auth,'Content-Type':'multipart/form-data; boundary=x'}).status_code,422)
        self.propre()
        self.assertEqual(self.c.post('/encoder',content=b'{}',headers={**self.auth,'Content-Type':'application/json'}).status_code,415)

    def test_occupe_sans_file(self):
        ep.VERROU.acquire()
        try: self.assertEqual(self.post().status_code,429)
        finally: ep.VERROU.release()

    def test_gpu_partage_avec_le_service_audio(self):
        self.gpu_lock.acquire()
        try:
            self.assertEqual(self.post().status_code,429)
            self.assertFalse((self.root/'commandes.jsonl').exists())
            self.propre()
        finally: self.gpu_lock.release()

    def test_delai_nettoie_enfant(self):
        if not peut_signaler_son_enfant():
            self.skipTest('runner ne permet pas de confirmer SIGKILL sur notre enfant; refus couvert par mocks')
        ep.DELAI_S=.2
        self.assertEqual(self.post(b'DELAI').status_code,504)
        self.propre()

    def test_echec_preserve_entree_et_sortie_partielle_sans_jeton(self):
        ep.FFMPEG = str(self.script('ffmpeg-partiel', """
import pathlib,sys
pathlib.Path(sys.argv[-1]).write_bytes(b'VIDEO-PARTIELLE')
sys.exit(1)
"""))
        self.assertEqual(self.post(b'VIDEO-SOURCE').status_code,422)
        dossiers = list(Path(ep.RACINE).glob('enc-*'))
        self.assertEqual(len(dossiers), 1)
        self.assertEqual((dossiers[0]/'entree-0').read_bytes(), b'VIDEO-SOURCE')
        self.assertEqual((dossiers[0]/'sortie.mp4').read_bytes(), b'VIDEO-PARTIELLE')
        self.assertEqual({p.name for p in dossiers[0].iterdir()}, {'entree-0', 'sortie.mp4'})
        self.assertNotIn(b'jeton-test-encoder', b''.join(p.read_bytes() for p in dossiers[0].iterdir()))
        self.propre()

    def test_quota_refuse_avant_reception_et_preserve_essais(self):
        ep.TAILLE_MAX = 100
        ep.PLAFOND_ESSAIS = '205'
        root = Path(ep.RACINE)
        root.mkdir()
        ancien = root/'essai-existant.mp4'
        ancien.write_bytes(b'123456')
        self.assertEqual(self.post(b'nouveau').status_code, 507)
        self.assertEqual(ancien.read_bytes(), b'123456')
        self.assertEqual(list(root.glob('enc-*')), [])
        self.propre()

    def test_plafond_invalide_et_lien_refusent_admission(self):
        root = Path(ep.RACINE)
        root.mkdir()
        ep.PLAFOND_ESSAIS = 'invalide'
        self.assertEqual(self.post().status_code, 503)
        ep.PLAFOND_ESSAIS = str(20 * 2**30)
        (root/'lien').symlink_to(self.root/'absent')
        self.assertEqual(self.post().status_code, 503)
        self.assertEqual(list(root.glob('enc-*')), [])
        self.propre()

    def test_verrou_entre_processus_refuse_sans_nouvel_essai(self):
        root = Path(ep.RACINE)
        root.mkdir()
        script = "import fcntl,os,sys; f=os.open(sys.argv[1],os.O_RDWR|os.O_CREAT,0o600); fcntl.flock(f,fcntl.LOCK_EX); print('ok',flush=True); sys.stdin.read(1)"
        p = subprocess.Popen([sys.executable, '-c', script, str(root/'.encoder.lock')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            self.assertEqual(p.stdout.readline(), b'ok\n')
            self.assertEqual(self.post().status_code, 429)
            self.assertEqual(list(root.glob('enc-*')), [])
        finally:
            p.stdin.close()
            p.wait(timeout=5)
            p.stdout.close()
        self.propre()

    def test_limite_exacte_est_admise(self):
        ep.TAILLE_MAX = 100
        ep.PLAFOND_ESSAIS = '206'
        root = Path(ep.RACINE)
        root.mkdir()
        (root/'ancien').write_bytes(b'123456')
        fd = ep.admettre_essai()
        os.close(fd)
        self.assertEqual((root/'ancien').read_bytes(), b'123456')

    def test_enfant_encodeur_herite_du_verrou(self):
        marqueur = self.root/'demarre'
        script = self.script('attente', "import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_text('ok'); time.sleep(.3)")
        async def verifier():
            fd = ep.admettre_essai()
            travail = asyncio.create_task(ep.programme([script, str(marqueur)], limite_fichier=100, verrou_fd=fd))
            try:
                for _ in range(100):
                    if marqueur.exists():
                        break
                    await asyncio.sleep(.01)
                self.assertTrue(marqueur.exists())
                os.close(fd)
                fd = None
                with self.assertRaises(ep.HTTPException) as erreur:
                    ep.admettre_essai()
                self.assertEqual(erreur.exception.status_code, 429)
                await travail
                fd2 = ep.admettre_essai()
                os.close(fd2)
            finally:
                if fd is not None:
                    os.close(fd)
                await travail
        asyncio.run(verifier())

    def test_limite_systeme_preserve_sortie_partielle(self):
        fichier = self.root/'fragment.mp4'
        ecrivain = self.script('ecrivain', "import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(b'x'*100)")
        with self.assertRaises(ep.HTTPException):
            asyncio.run(ep.programme([ecrivain, str(fichier)], limite_fichier=32))
        self.assertEqual(fichier.stat().st_size, 32)
        self.assertEqual(fichier.read_bytes(), b'x'*32)

    def test_sortie_trop_grosse(self):
        ep.TAILLE_MAX=25  # options 2 + input24 <=26 : réduit après réception dans le faux ffmpeg via sortie ?
        # La limite compte les options et les fichiers ; entrée23+{}2=25, sortie29 >25.
        self.assertEqual(self.post(b'V'*23).status_code,422)
        self.propre()


class ProgrammeArretTests(unittest.IsolatedAsyncioTestCase):
    def test_probe_refus_attend_lenfant_naturellement(self):
        with patch.object(subprocess.Popen, 'kill', side_effect=PermissionError(errno.EACCES, 'permission denied')):
            debut = time.monotonic()
            self.assertFalse(peut_signaler_son_enfant())
            self.assertLess(time.monotonic() - debut, 1)

    async def test_permission_denied_is_explicit_bounded_and_passes_lock_fd(self):
        class FauxProcessus:
            returncode = None
            stdout = None
            def __init__(self): self.kill_calls = 0; self.wait_calls = 0
            def kill(self):
                self.kill_calls += 1
                raise PermissionError(errno.EACCES, 'permission denied')
            async def wait(self):
                self.wait_calls += 1
                await asyncio.Future()

        proc = FauxProcessus()
        spawn = AsyncMock(return_value=proc)
        fd_r, fd_w = os.pipe()
        try:
            with patch.object(ep.asyncio, 'create_subprocess_exec', new=spawn), \
                    patch.object(ep, 'DELAI_S', .01), patch.object(ep, 'DELAI_ARRET_S', .02):
                with self.assertRaises(ep.HTTPException) as erreur:
                    await asyncio.wait_for(ep.programme(['/fake/ffmpeg'], verrou_fd=fd_w), timeout=.5)
            self.assertEqual(erreur.exception.status_code, 503)
            self.assertIn('arrêt non confirmé', erreur.exception.detail)
            self.assertEqual(proc.kill_calls, 1)
            self.assertEqual(proc.wait_calls, 1, 'ne pas attendre un enfant qu’on ne peut pas arrêter')
            self.assertEqual(spawn.await_args.kwargs['pass_fds'], (fd_w,))
        finally:
            os.close(fd_r); os.close(fd_w)

    async def test_permission_denied_closes_only_stdout_pipe_parent(self):
        class FauxPipe:
            def __init__(self): self.closed = False
            def close(self): self.closed = True

        class FauxTransport:
            def __init__(self): self.pipe = FauxPipe(); self.requested = []
            def get_pipe_transport(self, fd):
                self.requested.append(fd)
                return self.pipe

        class FauxStdout:
            async def read(self, _limit): await asyncio.Future()

        class FauxProcessus:
            returncode = None
            stdout = FauxStdout()
            def __init__(self): self.kill_calls = 0; self.wait_calls = 0; self._transport = FauxTransport()
            def kill(self):
                self.kill_calls += 1
                raise PermissionError(errno.EACCES, 'permission denied')
            async def wait(self):
                self.wait_calls += 1
                await asyncio.Future()

        proc = FauxProcessus()
        spawn = AsyncMock(return_value=proc)
        with patch.object(ep.asyncio, 'create_subprocess_exec', new=spawn), \
                patch.object(ep, 'DELAI_S', .01), patch.object(ep, 'DELAI_ARRET_S', .02):
            with self.assertRaises(ep.HTTPException) as erreur:
                await asyncio.wait_for(ep.programme(['/fake/ffprobe'], sortie=True), timeout=.5)
        self.assertEqual(erreur.exception.status_code, 503)
        self.assertEqual(proc._transport.requested, [1])
        self.assertTrue(proc._transport.pipe.closed)
        self.assertEqual(proc.kill_calls, 1)
        self.assertEqual(proc.wait_calls, 0)

    async def test_permission_denied_closes_real_stdout_pipe_and_reaps_child(self):
        created = {}
        real_create = asyncio.create_subprocess_exec

        async def capture_child(*args, **kwargs):
            child = await real_create(*args, **kwargs)
            created['child'] = child
            return child

        def deny_kill(_child):
            raise PermissionError(errno.EACCES, 'permission denied')

        try:
            with patch.object(ep.asyncio, 'create_subprocess_exec', new=capture_child), \
                    patch.object(asyncio.subprocess.Process, 'kill', new=deny_kill), \
                    patch.object(ep, 'DELAI_S', .02), patch.object(ep, 'DELAI_ARRET_S', .02):
                with self.assertRaises(ep.HTTPException) as erreur:
                    await asyncio.wait_for(ep.programme(
                        [sys.executable, '-c', 'import time; time.sleep(.4)'], sortie=True), timeout=.8)
            self.assertEqual(erreur.exception.status_code, 503)
            child = created['child']
            pipe = child._transport.get_pipe_transport(1)
            self.assertTrue(pipe.is_closing())
            self.assertIsNone(child.returncode)
            await asyncio.wait_for(child.wait(), timeout=1)
            self.assertEqual(child.returncode, 0)
        finally:
            child = created.get('child')
            if child is not None and child.returncode is None:
                await asyncio.wait_for(child.wait(), timeout=1)

    async def test_process_lookup_error_reconcile_wait_is_bounded_and_timeout_remains(self):
        class FauxProcessus:
            returncode = None
            stdout = None
            def __init__(self): self.kill_calls = 0; self.wait_calls = 0
            def kill(self):
                self.kill_calls += 1
                raise ProcessLookupError(errno.ESRCH, 'already exited')
            async def wait(self):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    await asyncio.Future()
                self.returncode = -signal.SIGKILL
                return self.returncode

        proc = FauxProcessus()
        spawn = AsyncMock(return_value=proc)
        with patch.object(ep.asyncio, 'create_subprocess_exec', new=spawn), \
                patch.object(ep, 'DELAI_S', .01), patch.object(ep, 'DELAI_ARRET_S', .02):
            with self.assertRaises(TimeoutError):
                await asyncio.wait_for(ep.programme(['/fake/ffmpeg']), timeout=.5)
        self.assertEqual(proc.kill_calls, 1)
        self.assertEqual(proc.wait_calls, 2)

    async def test_wait_after_successful_kill_is_bounded(self):
        class FauxProcessus:
            returncode = None
            stdout = None
            def __init__(self): self.kill_calls = 0; self.wait_calls = 0
            def kill(self): self.kill_calls += 1
            async def wait(self):
                self.wait_calls += 1
                await asyncio.Future()

        proc = FauxProcessus()
        spawn = AsyncMock(return_value=proc)
        with patch.object(ep.asyncio, 'create_subprocess_exec', new=spawn), \
                patch.object(ep, 'DELAI_S', .01), patch.object(ep, 'DELAI_ARRET_S', .02):
            with self.assertRaises(ep.HTTPException) as erreur:
                await asyncio.wait_for(ep.programme(['/fake/ffmpeg']), timeout=.5)
        self.assertEqual(erreur.exception.status_code, 503)
        self.assertIn('arrêt non confirmé', erreur.exception.detail)
        self.assertEqual(proc.wait_calls, 2)

    async def test_permission_denied_child_keeps_lock_until_natural_exit(self):
        with tempfile.TemporaryDirectory(prefix='programme-lock-') as tmp:
            lock_path = Path(tmp)/'.encoder.lock'
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            created = {}
            real_create = asyncio.create_subprocess_exec

            async def capture_child(*args, **kwargs):
                child = await real_create(*args, **kwargs)
                created.update(child=child, pass_fds=kwargs.get('pass_fds'))
                return child

            def deny_kill(_child):
                raise PermissionError(errno.EACCES, 'permission denied')

            probe_fd = None
            try:
                with patch.object(ep.asyncio, 'create_subprocess_exec', new=capture_child), \
                        patch.object(asyncio.subprocess.Process, 'kill', new=deny_kill), \
                        patch.object(ep, 'DELAI_S', .02), patch.object(ep, 'DELAI_ARRET_S', .02):
                    with self.assertRaises(ep.HTTPException) as erreur:
                        await asyncio.wait_for(ep.programme([sys.executable, '-c', 'import time; time.sleep(.8)'], limite_fichier=1024, verrou_fd=fd), timeout=.5)
                self.assertEqual(erreur.exception.status_code, 503)
                self.assertEqual(created['pass_fds'], (fd,))
                self.assertIsNone(created['child'].returncode)
                os.close(fd); fd = None
                probe_fd = os.open(lock_path, os.O_RDWR)
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(probe_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                await asyncio.wait_for(created['child'].wait(), timeout=1.2)
                fcntl.flock(probe_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                if created.get('child') is not None and created['child'].returncode is None:
                    await asyncio.wait_for(created['child'].wait(), timeout=1.2)
                if fd is not None: os.close(fd)
                if probe_fd is not None: os.close(probe_fd)


if __name__=='__main__': unittest.main()
