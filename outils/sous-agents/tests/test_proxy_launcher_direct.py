"""Teste directement les branches du lanceur, avec des descripteurs et une exécution fictifs."""
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import proxy_launcher as launcher


class LauncherDirectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {name: 'fictif' for name in launcher.PROXY_ENV}
        self.env['SA_PROXY_LEDGER'] = str(self.root / 'journal')

    def appel(self, env, fd=3, exec_failure=True):
        stderr = io.StringIO()
        with patch.object(sys, 'argv', ['launcher', 'cle-fictive', 'relais-fictif', 'socket-fictif']), \
             patch.dict(os.environ, env, clear=True), patch.object(launcher.os, 'umask'), \
             patch.object(launcher, 'open_master_key', return_value=fd), \
             patch.object(launcher, 'ensure_ledger', side_effect=launcher.LedgerUnavailable if env.get('SA_PROXY_LEDGER') == str(self.root) else None), \
             patch.object(launcher.os, 'set_inheritable'), patch.object(launcher.os, 'dup2'), \
             patch.object(launcher.os, 'close'), \
             patch.object(launcher.os, 'execve', side_effect=OSError('échec simulé') if exec_failure else None) as execute, \
             contextlib.redirect_stderr(stderr):
            resultat = launcher.main()
        return resultat, stderr.getvalue(), execute

    def test_relais_recoit_uniquement_variables_autorisees(self):
        env = dict(self.env, SECRET_FICTIF='ne-doit-pas-etre-transmis')
        resultat, message, execute = self.appel(env, fd=4)
        self.assertEqual(resultat, 2)
        self.assertIn('relay startup failed', message)
        transmis = execute.call_args.args[2]
        self.assertEqual(set(transmis), set(launcher.PROXY_ENV))
        self.assertNotIn('SECRET_FICTIF', transmis)

    def test_variable_manquante_refuse_sans_exec(self):
        env = dict(self.env)
        del env['SA_PROXY_RUN']
        resultat, _, execute = self.appel(env)
        self.assertEqual(resultat, 2)
        execute.assert_not_called()

    def test_journal_non_regulier_refuse_sans_exec(self):
        env = dict(self.env, SA_PROXY_LEDGER=str(self.root))
        resultat, message, execute = self.appel(env)
        self.assertEqual(resultat, 4)
        self.assertIn('usage ledger unavailable', message)
        execute.assert_not_called()

    def test_arguments_incomplets_refuses(self):
        with patch.object(sys, 'argv', ['launcher']):
            self.assertEqual(launcher.main(), 2)
