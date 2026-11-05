"""Tests CPU du comparateur ; toutes les images sont synthétiques."""
import hashlib
import json
import os
import sys
import struct
import subprocess
import time
import zlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import comparateur_alpha as C
import ecriture as E

FFMPEG = Path(os.environ.get('MATTE_TEST_FFMPEG', '/usr/bin/ffmpeg'))


class ComparateurTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'ref').mkdir()
        (self.root / 'cand').mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def frame(self, role, index, values, rgba=False):
        pixels = np.array(values, dtype=np.uint16)
        if rgba:
            rgba_pixels = np.zeros((*pixels.shape, 4), dtype=np.uint16)
            rgba_pixels[:, :, 3] = pixels
            pixels = rgba_pixels
        path = self.root / role / f'{index}.png'
        E.ecrire_png16(str(path), pixels)
        return path

    def manifest(self, role, indices, fps='24/1'):
        path = self.root / role / 'sequence.json'
        path.write_text(json.dumps({'fps': fps, 'frames': [{'index': i, 'fichier': f'{i}.png'} for i in indices]}))
        return path

    def pairs(self, candidate_delta=0):
        for i in range(3):
            self.frame('ref', i, [[1000, 2000]])
            self.frame('cand', i, [[1000 + (candidate_delta if i == 1 else 0), 2000 + (candidate_delta if i == 1 else 0)]])
        return self.manifest('ref', range(3)), self.manifest('cand', range(3))

    def test_identique_et_provenance(self):
        ref, cand = self.pairs()
        result = C.comparer(ref, cand, FFMPEG)
        self.assertEqual(result['mae_alpha'], 0)
        self.assertEqual([x['variation_temporelle_residu'] for x in result['transitions']], [0, 0])
        self.assertEqual(result['sources']['reference']['manifest_sha256'], hashlib.sha256(ref.read_bytes()).hexdigest())
        entry = result['sources']['reference']['images'][0]
        self.assertEqual(entry['sha256'], hashlib.sha256((self.root / 'ref/0.png').read_bytes()).hexdigest())
        self.assertEqual((result['largeur'], result['hauteur'], result['fps']), (2, 1, '24/1'))

    def test_impulsion_provoque_deux_transitions(self):
        ref, cand = self.pairs(candidate_delta=6554)
        result = C.comparer(ref, cand, FFMPEG)
        values = [x['variation_temporelle_residu'] for x in result['transitions']]
        self.assertEqual([x['index'] for x in result['transitions']], [1, 2])
        for value in values:
            self.assertAlmostEqual(value, 6554 / 65535, places=12)
            self.assertLess(abs(value - .1), 1 / 65535)
        self.assertAlmostEqual(result['mae_alpha'], 6554 / 65535 / 3, places=12)

    def test_rgba16_preserve_un_seul_niveau(self):
        ref = self.frame('ref', 0, [[0, 1, 257, 32769, 65535]], rgba=True)
        cand = self.frame('cand', 0, [[0, 2, 257, 32769, 65535]], rgba=True)
        result = C.comparer(ref, cand, FFMPEG)
        self.assertAlmostEqual(result['mae_alpha'], 1 / 65535 / 5, places=13)
        self.assertIsNone(result['fps'])
        self.assertIsNone(result['variation_temporelle_moyenne'])
        self.assertEqual(result['sources']['reference']['images'][0]['profondeur_bits'], 16)

    def test_gris_et_rgba_8_bits(self):
        grey = self.root / 'ref/grey.png'
        rgba = self.root / 'cand/rgba.png'
        Image.new('L', (1, 1), 26).save(grey)
        Image.new('RGBA', (1, 1), (0, 0, 0, 26)).save(rgba)
        self.assertEqual(C.comparer(grey, rgba, FFMPEG)['mae_alpha'], 0)

    def test_profondeurs_differentes_sans_perte(self):
        gray8 = self.root / 'ref/gray8.png'
        Image.new('L', (1, 1), 26).save(gray8)
        gray16 = self.frame('cand', 0, [[26 * 257]])
        self.assertEqual(C.comparer(gray8, gray16, FFMPEG)['mae_alpha'], 0)

    def test_gris_alpha_huit_et_seize_bits(self):
        gray = self.frame('ref', 0, [[1, 32769, 65535]])
        path = self.root / 'cand/la16.png'
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        pixels = b''.join(struct.pack('>HH', 1234, alpha) for alpha in (1, 32769, 65535))
        header = struct.pack('>IIBBBBB', 3, 1, 16, 4, 0, 0, 0)
        path.write_bytes(C.SIGNATURE + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(b'\x00' + pixels)) + chunk(b'IEND', b''))
        self.assertEqual(C.comparer(gray, path, FFMPEG)['mae_alpha'], 0)
        gray8 = self.root / 'ref/gray8.png'; la8 = self.root / 'cand/la8.png'
        Image.new('L', (1, 1), 51).save(gray8)
        Image.new('LA', (1, 1), (20, 51)).save(la8)
        self.assertEqual(C.comparer(gray8, la8, FFMPEG)['mae_alpha'], 0)

    def test_gris_alpha16_un_niveau_independant_de_la_luminance(self):
        def la16(path, luminance, alpha):
            def chunk(tag, data):
                return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
            header = struct.pack('>IIBBBBB', 1, 1, 16, 4, 0, 0, 0)
            data = b'\x00' + struct.pack('>HH', luminance, alpha)
            path.write_bytes(C.SIGNATURE + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b''))
        ref, cand = self.root / 'ref/la.png', self.root / 'cand/la.png'
        la16(ref, 65535, 1); la16(cand, 0, 2)
        self.assertAlmostEqual(C.comparer(ref, cand, FFMPEG)['mae_alpha'], 1 / 65535, places=13)

    def test_png_invalide_anime_et_crc_refuses(self):
        valid = self.frame('ref', 0, [[1000]]).read_bytes()
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        animated = valid[:33] + chunk(b'acTL', struct.pack('>II', 2, 0)) + valid[33:]
        color_key = valid[:33] + chunk(b'tRNS', b'\x00\x00') + valid[33:]
        significant = valid[:33] + chunk(b'sBIT', b'\x08') + valid[33:]
        corrupt = bytearray(valid); corrupt[29] ^= 1
        for bad in (valid + b'extra', valid[:-2], animated, color_key, significant, bytes(corrupt), b'bad'):
            with self.subTest(size=len(bad)), self.assertRaises(ValueError):
                C._png_info(bad)

    def test_erreurs_manifestes_et_modes_mixtes(self):
        ref, cand = self.pairs()
        image = self.root / 'ref/0.png'
        for a, b in ((ref, image), (image, cand)):
            with self.assertRaisesRegex(ValueError, 'image fixe'):
                C.comparer(a, b, FFMPEG)
        for content in ('[1]', '{', '{"fps":"24/1","frames":[]}',
                        '{"fps":"24/1","frames":[{"index":true,"fichier":"0.png"}]}'):
            cand.write_text(content)
            with self.subTest(content=content), self.assertRaises(ValueError):
                C.comparer(ref, cand, FFMPEG)

    def test_decoder_timeout_et_sortie_tronquee(self):
        path = self.frame('ref', 0, [[1000]])
        process = MagicMock()
        process.communicate.side_effect = subprocess.TimeoutExpired('ffmpeg', 30)
        with patch.object(C.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'arrêt confirmé'):
                C._alpha(path, FFMPEG)
        process.kill.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)
        process = MagicMock(returncode=0)
        process.communicate.return_value = (b'', b'')
        with patch.object(C.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'incomplet'):
                C._alpha(path, FFMPEG)

    def test_delai_borne_si_arret_refuse(self):
        path = self.frame('ref', 0, [[1000]])
        process = MagicMock()
        def expiration(**_kwargs):
            time.sleep(0.05)
            raise subprocess.TimeoutExpired('ffmpeg', 30)
        process.communicate.side_effect = expiration
        process.kill.side_effect = PermissionError('signal refusé')
        start = time.monotonic()
        with patch.object(C.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'arrêt non confirmé.*PermissionError'):
                C._alpha(path, FFMPEG)
        self.assertLess(time.monotonic() - start, 1)
        process.wait.assert_not_called()
        process.kill.side_effect = None
        process.wait.side_effect = subprocess.TimeoutExpired('ffmpeg', 5)
        with patch.object(C.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'arrêt non confirmé.*TimeoutExpired'):
                C._alpha(path, FFMPEG)

    def test_lectures_bornees(self):
        path = self.root / 'trop-grand.bin'
        path.write_bytes(b'12345')
        with self.assertRaisesRegex(ValueError, 'volumineux'):
            C._read_bounded(path, 4)
        fifo = self.root / 'pipe'
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, 'ordinaire'):
            C._read_bounded(fifo, 4)

    def test_cadence_dimensions_nombre_et_indices_refuses(self):
        ref, cand = self.pairs()
        data = json.loads(cand.read_text())
        for change in ('fps', 'nombre', 'indices', 'dimension', 'absente'):
            mutated = json.loads(json.dumps(data))
            if change == 'fps': mutated['fps'] = '25/1'
            if change == 'nombre': mutated['frames'].pop()
            if change == 'indices': mutated['frames'][1]['index'] = 4
            if change == 'dimension': self.frame('cand', 2, [[1], [2]])
            if change == 'absente': mutated['frames'][2]['fichier'] = 'absente.png'
            cand.write_text(json.dumps(mutated))
            with self.subTest(change=change), self.assertRaises((ValueError, OSError)):
                C.comparer(ref, cand, FFMPEG)
            if change == 'dimension': self.frame('cand', 2, [[1000, 2000]])

    def test_indices_non_nuls_sont_explicites_et_identiques(self):
        ref, cand = self.pairs()
        for path in (ref, cand):
            data = json.loads(path.read_text())
            for entry in data['frames']:
                entry['index'] += 5
            path.write_text(json.dumps(data))
        result = C.comparer(ref, cand, FFMPEG)
        self.assertEqual([item['index'] for item in result['frames']], [5, 6, 7])
        self.assertEqual([item['index'] for item in result['transitions']], [6, 7])

    def test_cadence_equivalente_et_saisie_stricte(self):
        ref, cand = self.pairs()
        data = json.loads(cand.read_text())
        data['fps'] = '48/2'
        cand.write_text(json.dumps(data))
        self.assertEqual(C.comparer(ref, cand, FFMPEG)['fps'], '24/1')
        for bad in ('0/1', '1/0', '24', 24, 'nan'):
            data['fps'] = bad
            cand.write_text(json.dumps(data))
            with self.subTest(fps=bad), self.assertRaises(ValueError):
                C.comparer(ref, cand, FFMPEG)
        cand.write_text('{"fps":"24/1","fps":"25/1","frames":[]}')
        with self.assertRaisesRegex(ValueError, 'dupliquée'):
            C.comparer(ref, cand, FFMPEG)

    def test_rgb_et_decodeur_absent_sont_refuses(self):
        ref, cand = self.pairs()
        Image.new('RGB', (2, 1), (1, 2, 3)).save(self.root / 'cand/0.png')
        with self.assertRaisesRegex(ValueError, 'gris'):
            C.comparer(ref, cand, FFMPEG)
        with self.assertRaisesRegex(ValueError, 'FFmpeg'):
            C.comparer(ref, ref, self.root / 'absent')

    def test_cli_reelle_et_code_erreur(self):
        ref, cand = self.pairs(candidate_delta=6554)
        output = self.root / 'cli.json'
        command = [sys.executable, '-B', str(Path(C.__file__)), '--reference', str(ref),
                   '--candidat', str(cand), '--sortie', str(output), '--ffmpeg', str(FFMPEG)]
        env = {'PATH': '/usr/bin:/bin', 'HOME': os.environ.get('HOME', '/tmp'), 'PYTHONDONTWRITEBYTECODE': '1'}
        if 'PYTHONPATH' in os.environ:
            env['PYTHONPATH'] = os.environ['PYTHONPATH']
        result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(json.loads(output.read_text())['mae_alpha'], 6554 / 65535 / 3, places=12)
        failed = subprocess.run(command, capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(failed.returncode, 1)
        self.assertIn('Erreur', failed.stderr)

    def test_sortie_exclusive_et_echec_sans_sortie(self):
        ref, cand = self.pairs()
        output = self.root / 'rapport.json'
        argv = ['comparateur_alpha', '--reference', str(ref), '--candidat', str(cand), '--sortie', str(output), '--ffmpeg', str(FFMPEG)]
        with patch.object(sys, 'argv', argv):
            C.main()
        before = output.read_bytes()
        with patch.object(sys, 'argv', argv), self.assertRaises(FileExistsError):
            C.main()
        self.assertEqual(output.read_bytes(), before)
        output2 = self.root / 'echec.json'
        data = json.loads(cand.read_text()); data['fps'] = '30/1'; cand.write_text(json.dumps(data))
        argv[argv.index(str(output))] = str(output2)
        with patch.object(sys, 'argv', argv), self.assertRaises(ValueError):
            C.main()
        self.assertFalse(output2.exists())


if __name__ == '__main__':
    unittest.main()
