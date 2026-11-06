"""Incrustations lisibles et bornées, sans rendu distant."""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import monter


class TypoMobileTests(unittest.TestCase):
    def setUp(self):
        police = Path(os.environ.get('OPSYS_TEST_MONO_FONT', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
        self.assertTrue(police.is_file(), f'Police de test absente : {police}')
        marque = {**monter.MARQUE, 'polices': {**monter.MARQUE['polices'], 'dossier': str(police.parent), 'mono': police.name}}
        self.typo = monter.Typo(marque)

    def test_long_text_stays_inside_safe_area_without_cutting_words(self):
        texte = 'EN PRÉPARATION · DONNÉES FICTIVES'
        ctx = SimpleNamespace(typo=self.typo)
        for size in ((480, 270), (270, 480)):
            for position, type_ in (('haut-gauche', 'surtitre'), ('bas-droite', 'etiquette')):
                with self.subTest(size=size, position=position, type=type_):
                    bg = Image.new('RGB', size, (0, 0, 0))
                    spec = {'type': type_, 'texte': texte, 'position': position, 'duree_f': 72, 'echelle': 4}
                    with patch.object(ctx.typo, 'tracer', wraps=ctx.typo.tracer) as tracer:
                        result = monter.poser_typo(ctx, bg, spec, 1.0)
                    self.assertEqual(tracer.call_args.args[2], texte)
                    bounds = ImageChops.difference(result, bg).getbbox()
                    self.assertIsNotNone(bounds)
                    marge = (0.08 if size[1] > size[0] else 0.06) * size[0]
                    self.assertGreaterEqual(bounds[0], int(marge) - 1)
                    self.assertLessEqual(bounds[2], size[0] - int(marge) + 1)

    def test_impossible_text_is_explicitly_refused(self):
        ctx = SimpleNamespace(typo=self.typo)
        spec = {'type': 'etiquette', 'texte': 'W' * 500, 'position': 'haut-gauche', 'duree_f': 72, 'echelle': 4}
        with self.assertRaisesRegex(ValueError, 'trop long'):
            monter.poser_typo(ctx, Image.new('RGB', (480, 270)), spec, 1.0)

    def test_giant_scale_keeps_short_label_inside_vertical_safe_area(self):
        ctx = SimpleNamespace(typo=self.typo)
        for size in ((480, 270), (270, 480)):
            for pos in ('haut-gauche', 'bas-droite'):
                with self.subTest(size=size, pos=pos):
                    bg = Image.new('RGB', size)
                    spec = {'type': 'etiquette', 'texte': 'VISION', 'position': pos, 'duree_f': 72, 'echelle': 100}
                    bounds = ImageChops.difference(monter.poser_typo(ctx, bg, spec, 1.0), bg).getbbox()
                    self.assertGreaterEqual(bounds[1], int(size[1] * 0.04) - 1)
                    self.assertLessEqual(bounds[3], int(size[1] * 0.96) + 1)

    def test_impossible_text_refused_before_ffmpeg_starts(self):
        spec = {'type': 'etiquette', 'texte': 'W' * 500, 'position': 'haut-gauche', 'debut_f': 0, 'duree_f': 72}
        ctx = SimpleNamespace(W=480, H=270, plan={'video': [], 'textes': []}, annexe={'incrustations': [spec]}, typo=self.typo)
        with patch.object(monter, 'contexte', return_value=ctx), patch.object(monter.subprocess, 'Popen') as encoder:
            with self.assertRaisesRegex(ValueError, 'trop long'):
                monter.rendre_tranche(('opus', 'long', True, 0, 1, '/tmp/never-created.mp4'))
        encoder.assert_not_called()


if __name__ == '__main__':
    unittest.main()
