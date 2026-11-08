"""Exécute le vrai bloc adapté sur des listes synthétiques ; aucun modèle."""
import ast
import contextlib
import copy
import io
from types import SimpleNamespace
import unittest
from unittest import mock

from outils.sync.labo.test_latentsync_patch import extraire, charger_fonction

PIPELINE = 'latentsync/pipelines/lipsync_pipeline.py'


def preparateur(pcm, source):
    call = extraire(PIPELINE, '__call__')
    debut = next(i for i,n in enumerate(call.body)
                 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='whisper_feature' for t in n.targets))
    fin = next(i for i,n in enumerate(call.body)
               if isinstance(n,ast.Assign) and 'self.loop_video' in ast.unparse(n.value))
    f = ast.parse('def preparer(self, audio_path, video_path, video_fps, audio_sample_rate):\n    pass').body[0]
    f.body = copy.deepcopy(call.body[debut:fin+1]) + ast.parse('return whisper_chunks, audio_samples, video_frames').body
    lecteur = mock.Mock(return_value=source)
    return charger_fonction(f,dict(read_audio=lambda _:pcm,read_video=lecteur)), lecteur


class CalagePCM(unittest.TestCase):
    def lancer(self, samples=144640, chunks_count=228, source_count=253, fps=25, rate=16000):
        pcm = SimpleNamespace(numel=lambda:samples)
        source = list(range(source_count))
        chunks = [object() for _ in range(chunks_count)]
        encoder = SimpleNamespace(audio2feat=mock.Mock(return_value=list(range(452))),
            feature2chunks=mock.Mock(return_value=chunks))
        affine = mock.Mock(return_value=('faces','boxes','matrices'))
        obj = SimpleNamespace(audio_encoder=encoder,affine_transform_video=affine)
        boucle = charger_fonction(extraire(PIPELINE,'loop_video'),{})
        obj.loop_video = lambda ch,vid:boucle(obj,ch,vid)
        preparer,lire = preparateur(pcm,source)
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log):
                value = preparer(obj,'synthetic.wav','synthetic.mp4',fps,rate)
        except ValueError:
            affine.assert_not_called()
            raise
        return value, chunks, pcm, source, affine, lire, log.getvalue()

    def test_frontieres_couvrent_tout_le_pcm_sans_chunk_ajoute(self):
        for samples,expected,available in [(1,1,2),(639,1,2),(640,1,3),(641,2,3),
            (144639,226,227),(144640,226,228),(144641,227,228),
            (144959,227,228),(144960,227,228),(144961,227,228)]:
            with self.subTest(samples=samples):
                (selected,audio,frames),original,pcm,source,affine,lire,log = self.lancer(samples,available)
                self.assertEqual(len(selected),expected)
                self.assertEqual(selected,original[:expected])
                self.assertEqual(len(original),available)  # Liste source non modifiée.
                self.assertIs(audio,pcm)
                self.assertEqual(frames,source[:expected])
                affine.assert_called_once_with(source[:expected])
                self.assertGreaterEqual(expected*16000,samples*25)
                self.assertLess((expected-1)*16000,samples*25)

    def test_source_de_226_images_suffit_malgre_228_chunks_bruts(self):
        (selected,audio,frames),*rest = self.lancer(source_count=226)
        self.assertEqual(len(selected),226)
        self.assertEqual(len(frames),226)

    def test_source_de_225_images_refusee_avant_affine(self):
        with self.assertRaisesRegex(ValueError,'Nombre d’images insuffisant'):
            self.lancer(source_count=225)

    def test_conditionnement_insuffisant_refuse_avant_video(self):
        pcm = SimpleNamespace(numel=lambda:144640)
        prepare,lire = preparateur(pcm,list(range(253)))
        obj = SimpleNamespace(audio_encoder=SimpleNamespace(
            audio2feat=lambda _:list(range(452)),feature2chunks=lambda **_:list(range(225))))
        with self.assertRaisesRegex(ValueError,'Conditionnement trop court'):
            prepare(obj,'synthetic.wav','synthetic.mp4',25,16000)
        lire.assert_not_called()

    def test_pcm_et_calendrier_invalides_refuses_avant_video(self):
        for samples,fps,rate in [(0,25,16000),(-1,25,16000),(True,25,16000),
            (640.0,25,16000),(640,24,16000),(640,True,16000),
            (640,25,16001),(640,25,True)]:
            with self.subTest(samples=samples,fps=fps,rate=rate):
                pcm = SimpleNamespace(numel=lambda:samples)
                prepare,lire = preparateur(pcm,list(range(253)))
                obj = SimpleNamespace(audio_encoder=SimpleNamespace(
                    audio2feat=lambda _:list(range(452)),feature2chunks=lambda **_:list(range(228))))
                affine = mock.Mock(return_value=('faces','boxes','matrices'))
                obj.affine_transform_video = affine
                boucle = charger_fonction(extraire(PIPELINE,'loop_video'),{})
                obj.loop_video = lambda ch,vid:boucle(obj,ch,vid)
                with self.assertRaises(ValueError):
                    prepare(obj,'synthetic.wav','synthetic.mp4',fps,rate)
                lire.assert_not_called()
                affine.assert_not_called()

    def test_journal_contient_les_dimensions_reellement_recues(self):
        *_,log = self.lancer()
        self.assertIn('NEXORA_PCM samples=144640 rate=16000 fps=25 features=452 chunks=228 frames=226',log)


if __name__=='__main__':
    unittest.main()
