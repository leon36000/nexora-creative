"""Fixtures PNG synthétiques ; aucun rendu ni modèle."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import types
import unittest
import zlib
from contextlib import redirect_stdout
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'noter.py'
spec = importlib.util.spec_from_file_location('noter_matte_test', SOURCE)
noter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(noter)


def png(width, height, depth, color, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    header = struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, 0)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
    fmt = 'B' if depth == 8 else '>H'
    stride = width * channels
    scan = b''.join(b'\0' + b''.join(struct.pack(fmt, v) for v in pixels[y*stride:(y+1)*stride]) for y in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(scan)) + chunk(b'IEND', b'')


class TestNoter(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='matte-noter-fixture-', dir=os.environ['TMPDIR']))
        self.gt = self.root / 'gt'; self.pred = self.root / 'pred'; self.gt.mkdir(); self.pred.mkdir()

    def ecrire(self, directory, name, data):
        (directory / name).write_bytes(data)

    def gris(self, width=2, height=2, value=128):
        return png(width, height, 8, 0, [value] * width * height)

    def test_indices_normalises_et_sha_octets(self):
        data = self.gris()
        for i in range(2):
            self.ecrire(self.gt, f'alpha_{i:04}.png', data); self.ecrire(self.pred, f'{i:06}.png', data)
        r = noter.noter(str(self.gt), str(self.pred), 0)
        self.assertEqual(r['images'], 2); self.assertEqual(r['image']['sad'], 0)
        self.assertEqual(r['schema'], 'nexora-matte-noter-v2')
        self.assertEqual(r['provenance']['verite'][0]['sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(r['provenance']['verite'][0]['index'], 0)

    def test_sequence_tronquee_et_dimensions_differentes_refusees(self):
        self.ecrire(self.gt, 'alpha_0000.png', self.gris()); self.ecrire(self.gt, 'alpha_0001.png', self.gris())
        self.ecrire(self.pred, '000000.png', self.gris())
        with self.assertRaisesRegex(ValueError, 'indices|séquence'):
            noter.noter(str(self.gt), str(self.pred))
        self.ecrire(self.pred, '000001.png', self.gris(1, 1))
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            noter.noter(str(self.gt), str(self.pred))

    def test_gaps_doublons_et_indices_differents_refuses(self):
        self.ecrire(self.gt, 'alpha_0000.png', self.gris()); self.ecrire(self.gt, 'alpha_0002.png', self.gris())
        self.ecrire(self.pred, '000000.png', self.gris()); self.ecrire(self.pred, '000002.png', self.gris())
        with self.assertRaisesRegex(ValueError, 'consécutif'):
            noter.noter(str(self.gt), str(self.pred))
        self.ecrire(self.gt, '0.png', self.gris())
        with self.assertRaisesRegex(ValueError, 'doublon'):
            noter.noter(str(self.gt), str(self.pred))

    def test_indices_egaux_en_nombre_mais_non_apparies_refuses(self):
        self.ecrire(self.gt, 'alpha_0001.png', self.gris()); self.ecrire(self.gt, 'alpha_0002.png', self.gris())
        self.ecrire(self.pred, '000000.png', self.gris()); self.ecrire(self.pred, '000001.png', self.gris())
        with self.assertRaisesRegex(ValueError, 'indices'):
            noter.noter(str(self.gt), str(self.pred))

    def test_image_indexee_non_png_refusee_metadonnees_ignorees(self):
        for dossier in (self.gt, self.pred):
            self.ecrire(dossier, '000000.png', self.gris())
            self.ecrire(dossier, 'metadata.json', b'{}')
        self.assertEqual(noter.noter(str(self.gt), str(self.pred), 0)['images'], 1)
        for dossier in (self.gt, self.pred):
            self.ecrire(dossier, '000001.jpg', b'image fictive')
        with self.assertRaisesRegex(ValueError, 'non PNG'):
            noter.noter(str(self.gt), str(self.pred), 0)

    def test_dimensions_inconstantes_memes_des_deux_cotes_refusees(self):
        for d, noms in ((self.gt, ('alpha_0000.png', 'alpha_0001.png')), (self.pred, ('000000.png', '000001.png'))):
            self.ecrire(d, noms[0], self.gris()); self.ecrire(d, noms[1], self.gris(3, 3))
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            noter.noter(str(self.gt), str(self.pred))

    def test_sequence_vide_nom_non_reconnu_et_png_tronque_refuses(self):
        with self.assertRaisesRegex(ValueError, 'séquence vide'):
            noter.noter(str(self.gt), str(self.pred))
        self.ecrire(self.gt, 'image.png', self.gris())
        with self.assertRaisesRegex(ValueError, 'nom PNG'):
            noter.noter(str(self.gt), str(self.pred))
        (self.gt / 'image.png').rename(self.gt / '0.png')
        self.ecrire(self.pred, '0.png', self.gris()[:-4])
        with self.assertRaisesRegex(ValueError, 'PNG'):
            noter.noter(str(self.gt), str(self.pred))

    def test_rgb_palette_et_px_invalides_refuses(self):
        self.ecrire(self.gt, '0.png', self.gris()); self.ecrire(self.pred, '0.png', png(2, 2, 8, 2, [128]*12))
        with self.assertRaises(ValueError): noter.noter(str(self.gt), str(self.pred))
        for px in (-1, True, 1.5):
            with self.subTest(px=px), self.assertRaises(ValueError): noter.noter(str(self.gt), str(self.pred), px)
        (self.pred / '0.png').write_bytes(png(2, 2, 8, 3, [0]*4))
        with self.assertRaises(ValueError): noter.noter(str(self.gt), str(self.pred))

    def test_alpha_la_rgba_8_16(self):
        for depth in (8, 16):
            maximum = (1 << depth) - 1
            for color, pixel in ((0, [maximum // 2]), (4, [maximum, maximum // 2]), (6, [maximum, 0, maximum, maximum // 2])):
                with self.subTest(depth=depth, color=color):
                    sample = png(2, 2, depth, color, pixel * 4)
                    self.ecrire(self.gt, '0.png', sample); self.ecrire(self.pred, '0.png', sample)
                    r = noter.noter(str(self.gt), str(self.pred), 0)
                    self.assertEqual(r['image']['mse'], 0)
                    self.assertEqual(r['provenance']['verite'][0]['profondeur'], depth)
                    self.assertEqual(r['provenance']['verite'][0]['type_png'], color)

    def test_alpha_la_16_valeurs_discriminantes(self):
        self.ecrire(self.gt, '0.png', png(2, 2, 16, 0, [32768]*4))
        self.ecrire(self.pred, '0.png', png(2, 2, 16, 4, [65535, 32768]*4))
        self.assertEqual(noter.noter(str(self.gt), str(self.pred), 0)['image']['mse'], 0)
        self.ecrire(self.pred, '0.png', png(2, 2, 16, 4, [32768, 16384]*4))
        self.assertGreater(noter.noter(str(self.gt), str(self.pred), 0)['image']['mse'], 60)

    def test_bande_vide_et_support_partiel_ne_sont_pas_des_notes_parfaites(self):
        for i, value in enumerate((0, 128, 0)):
            self.ecrire(self.gt, f'alpha_{i:04}.png', self.gris(value=value))
            self.ecrire(self.pred, f'{i:06}.png', self.gris(value=255))
        r = noter.noter(str(self.gt), str(self.pred), 0)
        self.assertEqual(r['pixels_bande'], [0, 4, 0])
        self.assertEqual(r['frames_bande_evaluees'], 1)
        self.assertEqual(r['transitions_bande_evaluees'], 1)
        self.assertEqual(r['bande'], {'sad': None, 'mse': None, 'grad': None, 'dtssd': None})
        self.assertGreater(r['image']['sad'], 0)

    def test_bande_entierement_vide_est_non_mesurable(self):
        self.ecrire(self.gt, 'alpha_0000.png', self.gris(value=0))
        self.ecrire(self.pred, '000000.png', self.gris(value=255))
        r = noter.noter(str(self.gt), str(self.pred), 0)
        self.assertEqual(r['frames_bande_evaluees'], 0)
        self.assertEqual(r['transitions_bande_evaluees'], 0)
        self.assertTrue(all(x is None for x in r['bande'].values()))
        self.assertGreater(r['image']['sad'], 0)

    def test_biais_constant_temporel_zero_mais_erreur_image_presente(self):
        for i in range(2):
            self.ecrire(self.gt, f'alpha_{i:04}.png', self.gris(value=128))
            self.ecrire(self.pred, f'{i:06}.png', self.gris(value=230))
        r = noter.noter(str(self.gt), str(self.pred), 0)
        self.assertEqual(r['image']['dtssd'], 0)
        self.assertEqual(r['image']['mse'], 160)
        self.assertEqual(r['transitions_bande_evaluees'], 1)

    def test_cli_reelle_option_bande_et_echec_clair(self):
        self.ecrire(self.gt, '0.png', self.gris()); self.ecrire(self.pred, '0.png', self.gris())
        cmd = [sys.executable, '-s', str(SOURCE), '--bande', '0', str(self.gt), str(self.pred)]
        run = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['bande_px'], 0)
        run = subprocess.run([sys.executable, '-s', str(SOURCE), str(self.gt), str(self.pred), '--bande', '-1'], capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertIn('entier positif', run.stderr)

    def test_banc_affiche_na_pour_bande_vide_sans_appel_service_reel(self):
        clips = self.root / 'clips'; clip = clips / 'clip-essai'; gt = clip / 'verite'
        alpha = self.root / 'travaux/verite-essai/sorties/alpha'
        gt.mkdir(parents=True); alpha.mkdir(parents=True)
        self.ecrire(gt, 'alpha_0000.png', self.gris(value=0))
        self.ecrire(alpha, '000000.png', self.gris(value=255))
        (clip / 'invites.json').write_text('{}')
        (self.root / 'travaux/verite-essai/source.mp4').write_bytes(b'fixture')
        faux_banc = types.ModuleType('banc'); faux_banc.appel = lambda *args, **kwargs: {'etat': 'termine', 'mesures': {}}
        spec_banc = importlib.util.spec_from_file_location('banc_verite_fixture', SOURCE.parent / 'banc_verite.py')
        module_banc = importlib.util.module_from_spec(spec_banc)
        with patch.dict(sys.modules, {'banc': faux_banc, 'noter': noter}):
            spec_banc.loader.exec_module(module_banc)
        sortie = self.root / 'resultats.json'; flux = io.StringIO()
        with patch.object(sys, 'argv', ['banc_verite.py', 'factice', str(self.root / 'travaux'), str(clips), str(sortie), 'fixture={}']), \
             patch.object(module_banc.time, 'sleep'), redirect_stdout(flux):
            module_banc.main()
        self.assertIn('bande: SAD N/A  MSE N/A  Grad N/A  dtSSD N/A', flux.getvalue())
        self.assertIsNone(json.loads(sortie.read_text())['essai']['fixture']['bande']['sad'])


if __name__ == '__main__': unittest.main()
