"""Contrats de prévol et refus du superviseur, sans GPU ni réseau."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from outils.sync.labo import highsync_execution as e


class PrevolHighSyncTest(unittest.TestCase):
    def setUp(self):
        self.gpu = {'free_mib': 15573, 'utilisation': 0}
        self.process = {'pid': 6266, 'uid': 1000, 'start': 6144, 'exe': '/usr/local/bin/python3.12', 'vram_mib': 260}
        self.allow = {'6266': {'uid': 1000, 'start': 6144, 'exe': '/usr/local/bin/python3.12', 'max_mib': 512}}

    def test_prevol_valide_et_refus_utilisation(self):
        e.verifier_gpu(self.gpu, [self.process], self.allow, 12288)
        with self.assertRaises(ValueError):
            e.verifier_gpu(dict(self.gpu, utilisation=1), [self.process], self.allow, 12288)
        with self.assertRaises(ValueError):
            e.verifier_gpu(dict(self.gpu, free_mib=12287), [self.process], self.allow, 12288)

    def test_refus_pid_absent_modifie_et_vram_gonflee(self):
        for processus in ([], [dict(self.process, start=1)], [dict(self.process, vram_mib=513)]):
            with self.subTest(processus=processus), self.assertRaises(ValueError):
                e.verifier_gpu(self.gpu, processus, self.allow, 12288)
        with self.assertRaises(ValueError):
            e.verifier_gpu(self.gpu, [self.process], {'6266': dict(self.allow['6266'], max_mib=9999)}, 12288)

    def test_choix_gpu_unique_et_identite(self):
        rep = mock.Mock()
        rep.stdout = 'GPU-A, 16303, 15573, 0\nGPU-B, 16303, 16000, 0\n'
        with mock.patch.object(e.subprocess, 'run', return_value=rep):
            with self.assertRaisesRegex(ValueError, 'ambigu'):
                e.snapshot_gpu(Path('/fake/nvidia-smi'), 'GPU-A')

    def test_plan_altere_refuse_avant_processus(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            fichier = run/'plan-execution.json'
            fichier.write_text(json.dumps({'statut':'planifie_sans_inference'}))
            with mock.patch.object(e.subprocess, 'Popen') as popen:
                with self.assertRaises(ValueError):
                    e.executer(run, '0'*64)
                popen.assert_not_called()

    def test_arret_echec_et_timeout_limites_a_lenfant(self):
        enfant = mock.Mock()
        enfant.poll.return_value = None
        enfant.wait.side_effect = [subprocess.TimeoutExpired('enfant',2), subprocess.TimeoutExpired('enfant',2)]
        self.assertFalse(e._arreter_enfant(enfant))
        enfant.terminate.assert_called_once_with()
        enfant.kill.assert_called_once_with()
        self.assertEqual(enfant.wait.call_count, 2)

    def test_json_duplique_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'config.json'
            path.write_text('{"a":1,"a":2}')
            with self.assertRaisesRegex(ValueError, 'dupliquée'):
                e.lire_json(path)


if __name__ == '__main__':
    unittest.main()
