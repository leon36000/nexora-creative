"""Vrai mux FFmpeg du bloc adapté ; génération et écriture imageio simulées."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
import wave

from outils.sync import valider_duree_av as av
from outils.sync.labo.test_latentsync_patch import extraire, charger_fonction


class MuxReelLatentSync(unittest.TestCase):
    def test_conserve_les_paquets_du_premier_encodage(self):
        ff = os.getenv('SYNC_FFMPEG') or shutil.which('ffmpeg')
        probe = os.getenv('SYNC_FFPROBE') or shutil.which('ffprobe')
        if not ff or not probe:
            self.skipTest('FFmpeg/FFprobe absents : aucune preuve de mux simulée')
        root = Path(tempfile.mkdtemp(prefix='latentsync-mux-',dir=os.getenv('SYNC_TEST_ROOT')))
        video, audio = root/'premier-encodage.mp4', root/'pcm-original.wav'
        def run(cmd,**kwargs):
            return subprocess.run(cmd,env={'PATH':'/usr/bin:/bin'},
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True,**kwargs)
        run([ff,'-v','error','-nostdin','-n','-f','lavfi','-i',
            'testsrc2=size=64x64:rate=25:duration=0.24',
            '-frames:v','6','-c:v','libx264','-crf','13','-pix_fmt','yuv420p',str(video)])
        run([ff,'-v','error','-nostdin','-n','-f','lavfi','-i',
            'sine=frequency=440:sample_rate=16000:duration=0.24',
            '-c:a','pcm_s16le','-ac','1',str(audio)])
        with wave.open(str(audio),'rb') as w:
            self.assertEqual(w.getnframes(),3840)
        initial = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (video,audio)}
        call = extraire('latentsync/pipelines/lipsync_pipeline.py','__call__')
        debut = next(i for i,n in enumerate(call.body)
                     if isinstance(n,ast.If) and 'synced_video_frames.shape' in ast.unparse(n.test))
        f = ast.parse('def finir(audio_samples, synced_video_frames, video_fps, audio_sample_rate, is_train, temp_dir, video_out_path, audio_path):\n    pass').body[0]
        f.body = call.body[debut:]
        commands = []
        def encodeur(cmd,**kwargs):
            commands.append(list(cmd))
            cmd = [ff,*cmd[1:]]  # Le binaire explicitement fourni par le banc.
            return subprocess.run(cmd,env={'PATH':'/usr/bin:/bin'},
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,**kwargs)
        def premier_encodage(path,frames,fps):
            self.assertEqual((frames.shape[0],fps),(6,25))
            shutil.copyfile(video,path)  # Source H264 réelle, aucune génération simulée comme réelle.
        finir = charger_fonction(f,dict(os=os,
            subprocess=SimpleNamespace(run=encodeur,DEVNULL=subprocess.DEVNULL),
            sf=SimpleNamespace(write=lambda path,*_:shutil.copyfile(audio,path)),
            write_video=premier_encodage))
        pcm = SimpleNamespace(numel=lambda:3840,cpu=lambda:SimpleNamespace(numpy=lambda:[]))
        output = root/'mux-final.mp4'
        finir(pcm,SimpleNamespace(shape=(6,)),25,16000,False,
              str(root/'intermediaires'),str(output),str(audio))
        def packets(path):
            p=run([probe,'-v','error','-select_streams','v:0','-show_packets',
                '-show_entries','packet=pts_time,duration_time,data_hash',
                '-show_data_hash','sha256','-of','json',str(path)])
            return json.loads(p.stdout)['packets']
        before,after = packets(video),packets(output)
        self.assertEqual(len(before),6)
        for packet in before+after:
            self.assertRegex(packet.get('data_hash') or '',r'^SHA256:[0-9a-f]{64}$')
        self.assertEqual(after,before)  # Paquets et calendrier, pas uniquement nombre d'images.
        self.assertEqual(initial,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (video,audio)})
        controle = av.valider(audio,output,Path(ff),Path(probe),.08,cadence_cible='25')
        self.assertTrue(controle['valide'],controle)
        self.assertEqual(controle['video']['images_decodees'],6)
        (root/'preuve.json').write_text(json.dumps({'packets_before':before,
            'packets_after':after,'validation_av':controle,'commande':commands,
            'scope':'vrai mux et premiers encodages synthétiques ; modèle non exécuté'},indent=2)+'\n')


if __name__=='__main__':
    unittest.main()
