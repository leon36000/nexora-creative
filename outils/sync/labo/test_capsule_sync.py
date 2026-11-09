"""Tests purs de capsule_sync ; aucun subprocess, aucun GPU, aucun réseau."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

from outils.sync.labo import capsule_sync
from outils.sync.labo.capsule_sync import ErreurCapsule, construire

GPU = 'GPU-0b1f2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d'


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix='capsule-test-')
        self.addCleanup(self._tmp.cleanup)
        self.racine = Path(self._tmp.name)
        self.runtime = self.racine / 'essai' / 'runtime'
        self.run = self.racine / 'essai-runs' / 'run01'
        self.bin = self.racine / 'bin'
        for d in (self.runtime, self.run, self.bin):
            d.mkdir(parents=True)
        os.chmod(self.runtime, 0o755)
        os.chmod(self.run, 0o700)
        self.script = self.runtime / 'inference.py'
        self.script.write_text('pass\n')
        self.python = self._executable('python3')
        self.ffmpeg = self._executable('ffmpeg')
        self.bwrap = self._executable('bwrap')

    def _executable(self, nom: str) -> Path:
        p = self.bin / nom
        p.write_text('#!/bin/sh\n')
        os.chmod(p, 0o755)
        return p

    def _construire(self, **kw):
        params = dict(runtime=self.runtime, run=self.run, python=self.python,
                      script=self.script, arguments=[], ffmpeg=self.ffmpeg,
                      gpu_uuid=GPU, lock_fd=7, bwrap=self.bwrap)
        params.update(kw)
        return construire(**params)

    @staticmethod
    def _apres(argv, option):
        i = argv.index(option)
        return argv[i + 1]

    @staticmethod
    def _valeur_env(argv, nom):
        for i, x in enumerate(argv):
            if x == '--setenv' and argv[i + 1] == nom:
                self_i = argv
                return self_i[i + 2]
        raise AssertionError(f'variable absente : {nom}')

    def _refus(self, **kw):
        with self.assertRaises(ErreurCapsule):
            self._construire(**kw)


class TestStructure(Base):
    def test_retour_liste_de_str_et_aucun_effet(self):
        argv = self._construire()
        self.assertIsInstance(argv, list)
        self.assertTrue(all(isinstance(x, str) for x in argv))
        self.assertEqual(sorted(p.name for p in self.run.iterdir()), [])
        self.assertEqual(argv[0], str(self.bwrap))

    def test_noms_despace_et_fins_de_phase_presentes(self):
        argv = self._construire()
        for opt in ('--unshare-net', '--unshare-pid', '--die-with-parent',
                    '--new-session', '--clearenv'):
            self.assertIn(opt, argv)
        self.assertEqual(self._apres(argv, '--ro-bind'), '/')
        self.assertEqual(self._apres(argv, '--chdir'), str(self.runtime))
        self.assertEqual(self._apres(argv, '--bind'), str(self.run))

    def test_clearenv_avant_tout_setenv(self):
        argv = self._construire(status_fd=9)
        self.assertEqual(argv.count('--clearenv'), 1)
        self.assertLess(argv.index('--clearenv'),
                        min(i for i, x in enumerate(argv) if x == '--setenv'))

    def test_sync_et_status_fd(self):
        argv = self._construire(lock_fd=3, status_fd=11)
        self.assertEqual(self._apres(argv, '--sync-fd'), '3')
        self.assertEqual(self._apres(argv, '--json-status-fd'), '11')
        self.assertNotIn('--json-status-fd', self._construire())

    def test_seul_separateur_est_exactement_avant_python(self):
        argv = self._construire(status_fd=4)
        self.assertEqual(argv[argv.index('--') + 1:argv.index('--') + 3],
                         [str(self.python), str(self.script)])
        self.assertFalse(any(x == '--' for x in argv[argv.index('--') + 1:]))

    def test_environnement_explicite(self):
        argv = self._construire()
        run = str(self.run)
        self.assertEqual(self._valeur_env(argv, 'PYTHONPATH'), str(self.runtime))
        self.assertEqual(self._valeur_env(argv, 'CUDA_VISIBLE_DEVICES'), GPU)
        self.assertEqual(self._valeur_env(argv, 'PATH'),
                         str(self.bin) + ':/usr/bin:/bin')
        for nom in ('HF_HOME', 'TORCH_HOME', 'XDG_CACHE_HOME', 'MPLCONFIGDIR', 'TMPDIR'):
            self.assertTrue(self._valeur_env(argv, nom).startswith(run + '/'), nom)
        for nom, val in (('HF_HUB_OFFLINE', '1'), ('TRANSFORMERS_OFFLINE', '1'),
                         ('PYTHONDONTWRITEBYTECODE', '1'),
                         ('NO_ALBUMENTATIONS_UPDATE', '1'),
                         ('TOKENIZERS_PARALLELISM', 'false')):
            self.assertEqual(self._valeur_env(argv, nom), val)
        noms = {argv[i + 1] for i, x in enumerate(argv) if x == '--setenv'}
        self.assertNotIn('HOME', noms)
        self.assertEqual(len(noms), len([x for x in argv if x == '--setenv']))

    def test_frontiere_protege_les_arguments_dash(self):
        argv = self._construire(arguments=['--config', 'x', '--dev-bind', 'a b'])
        self.assertEqual(argv[argv.index('--') + 1:],
                         [str(self.python), str(self.script),
                          '--config', 'x', '--dev-bind', 'a b'])
        self.assertEqual(argv[-2:], ['--dev-bind', 'a b'])
        # Un seul séparateur, exactement avant le python.
        self.assertEqual(argv.count('--'), 1)  # seul le séparateur entre options et commande

    def test_separateur_dans_arguments_reste_un_argument_python(self):
        argv = self._construire(arguments=['--', '--x'])
        self.assertEqual(argv[argv.index('--') + 1:],
                         [str(self.python), str(self.script), '--', '--x'])

    def test_valeur_argument_vide_reste_litterale(self):
        argv = self._construire(arguments=['--texte', ''])
        self.assertEqual(argv[argv.index('--') + 1:],
                         [str(self.python), str(self.script), '--texte', ''])


class TestChemins(Base):
    def test_runtime_relatif_refuse(self):
        self._refus(runtime=Path('runtime'))

    def test_racine_seule_refusee(self):
        self._refus(run=Path('/'))

    def test_chemin_avec_parent_refuse(self):
        # Path conserve les remontées « .. », contrairement aux « . » et « // ».
        self._refus(runtime=self.runtime / '..' / 'runtime')
        self._refus(script=self.runtime / '..' / 'runtime' / 'inference.py')
        self._refus(run=self.run / '..' / 'run01')

    def test_run_lien_refuse(self):
        lien = self.racine / 'lien-run'
        lien.symlink_to(self.run, target_is_directory=True)
        self._refus(run=lien)

    def test_cache_lie_hors_essai_refuse(self):
        cache_externe = self.racine / 'cache-externe'
        cache_externe.mkdir()
        (self.run / 'cache').symlink_to(cache_externe, target_is_directory=True)
        self._refus()

    def test_sous_cache_lie_hors_essai_refuse(self):
        (self.run / 'cache').mkdir()
        cache_externe = self.racine / 'cache-externe'
        cache_externe.mkdir()
        (self.run / 'cache' / 'hf').symlink_to(cache_externe, target_is_directory=True)
        self._refus()

    def test_cache_fichier_refuse(self):
        (self.run / 'cache').write_text('fixture sans donnée utilisateur')
        self._refus()

    def test_runtime_parent_lien_refuse(self):
        parent = self.racine / 'essai'
        lien = self.racine / 'essai-lien'
        lien.symlink_to(parent, target_is_directory=True)
        self._refus(runtime=lien / 'runtime')

    def test_run_egale_ou_imbrique_runtime_refuse(self):
        self._refus(run=self.runtime)
        self._refus(run=self.runtime / 'run')
        self._refus(run=self.racine)

    def test_run_permissions_trop_larges(self):
        os.chmod(self.run, 0o750)
        self._refus()

    def test_run_pas_un_dossier(self):
        self._refus(run=self.script)

    def test_script_hors_runtime_refuse(self):
        autre = self.racine / 'autre.py'
        autre.write_text('pass\n')
        self._refus(script=autre)

    def test_script_lien_refuse(self):
        lien = self.runtime / 'lien.py'
        lien.symlink_to(self.script)
        self._refus(script=lien)

    def test_script_non_py_ou_dossier_refuse(self):
        autre = self.runtime / 'script.txt'
        autre.write_text('pass\n')
        self._refus(script=autre)
        self._refus(script=self.runtime)

    def test_script_parent_lien_refuse(self):
        sous = self.runtime / 'pkg'
        sous.mkdir()
        (sous / 'main.py').write_text('pass\n')
        raccourci = self.runtime / 'raccourci'
        raccourci.symlink_to(sous, target_is_directory=True)
        self._refus(script=raccourci / 'main.py')

    def test_executable_relatif_absent_ou_sans_x_refuse(self):
        self._refus(ffmpeg=Path('ffmpeg'))
        self._refus(ffmpeg=self.bin / 'absent')
        os.chmod(self.ffmpeg, 0o644)
        self._refus(ffmpeg=self.ffmpeg)
        os.chmod(self.ffmpeg, 0o775)  # writable par groupe
        self._refus(ffmpeg=self.ffmpeg)

    def test_arguments_type_et_nul(self):
        self._refus(arguments='--a b')
        self._refus(arguments=('a',))
        self._refus(arguments=['a\x00b'])
        self._refus(arguments=[Path('/x')])
        self._refus(arguments=[1])

    def test_gpu_uuid(self):
        for mauvais in (None, 'GPU-0B1F2C3D', 'GPU-0b1f2c3d4e5f6a7b8c9d0e1f2a3b4c5d',
                        '0b1f2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d', GPU + ' ',
                        'GPU-0b1f2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d\n', GPU + 'x'):
            self._refus(gpu_uuid=mauvais)

    def test_fd_invalides(self):
        for mauvais in (True, False, '7', 7.0, 2, 0, -5, None):
            self._refus(lock_fd=mauvais)
        self._refus(status_fd=True)
        self._refus(status_fd=7)  # même valeur que lock_fd

    def test_python_et_bwrap_non_path(self):
        self._refus(python=str(self.python))
        self._refus(bwrap='bwrap')


class TestVenvPreserve(Base):
    def test_metadonnees_executable_systeme_acceptees(self):
        # Aucun lancement : un binaire système appartient généralement à root,
        # ce qui doit être accepté depuis un utilisateur normal.
        exe = Path(sys.executable).absolute()
        argv = self._construire(python=exe, ffmpeg=exe, bwrap=exe)
        self.assertEqual(argv[0], str(exe))
        self.assertEqual(argv[argv.index('--') + 1], str(exe))

    def test_python_venv_lien_non_resolu(self):
        venv = self.racine / 'venv' / 'bin'
        venv.mkdir(parents=True)
        lien = venv / 'python'
        lien.symlink_to(self.python)
        argv = self._construire(python=lien)
        self.assertEqual(argv[-2], str(lien))
        self.assertNotEqual(argv[-2], str(self.python))
        self.assertNotEqual(argv[-2], str(lien.resolve()))

    def test_lien_casse_refuse(self):
        lien = self.bin / 'python-lien'
        lien.symlink_to(self.bin / 'nexiste-pas')
        self._refus(python=lien)

    def test_executable_pas_appartenant_a_uid_refuse_unite_seulement(self):
        # Contrôle supplémentaire d’un propriétaire tiers, sans requérir root en CI.
        if os.getuid() != 0:
            self.skipTest('UID non-root : test réservé à root')
        f = self.bin / 'autre'
        f.write_text('x')
        os.chmod(f, 0o755)
        os.chown(f, 1, 1)
        self._refus(ffmpeg=f)


if __name__ == '__main__':
    unittest.main()
