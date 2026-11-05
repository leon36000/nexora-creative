"""Sans GPU : python test_encoder.py (FastAPI/httpx/python-multipart requis)."""
import asyncio
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
import encoder_endpoint as ep


class Encoder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='test-encoder-')
        self.root = Path(self.tmp.name)
        self.old = {k: getattr(ep, k) for k in ('FICHIER_JETON', 'RACINE', 'FFMPEG', 'FFPROBE', 'TAILLE_MAX', 'DELAI_S', 'H264_VALIDE', 'HEVC_VALIDE')}
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
        dossiers = list(Path(ep.RACINE).iterdir())
        self.assertEqual(len(dossiers), 1)
        self.assertEqual((dossiers[0]/'entree-0').read_bytes(), b'VIDEO-SOURCE')
        self.assertEqual((dossiers[0]/'sortie.mp4').read_bytes(), b'VIDEO-PARTIELLE')
        self.assertEqual({p.name for p in dossiers[0].iterdir()}, {'entree-0', 'sortie.mp4'})
        self.assertNotIn(b'jeton-test-encoder', b''.join(p.read_bytes() for p in dossiers[0].iterdir()))
        self.propre()

    def test_sortie_trop_grosse(self):
        ep.TAILLE_MAX=25  # options 2 + input24 <=26 : réduit après réception dans le faux ffmpeg via sortie ?
        # La limite compte les options et les fichiers ; entrée23+{}2=25, sortie29 >25.
        self.assertEqual(self.post(b'V'*23).status_code,413)
        self.propre()


if __name__=='__main__': unittest.main()
