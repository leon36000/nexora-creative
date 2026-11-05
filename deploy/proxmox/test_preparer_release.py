import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('preparer_release', Path(__file__).with_name('preparer_release.py'))
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


class Preparation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def archive(self, extra=()):
        path = self.root / 'release.tar'
        with tarfile.open(path, 'w') as tar:
            for name in ('app/package.json', 'mode-studio/package.json', *extra):
                raw = b'{}'
                info = tarfile.TarInfo(name)
                info.size = len(raw)
                tar.addfile(info, io.BytesIO(raw))
        with path.open('rb') as f:
            sha = hashlib.file_digest(f, 'sha256').hexdigest()
        return path, sha

    def test_build_reussi_avec_environnement_explicite(self):
        path, sha = self.archive()
        appels = []
        def fake(cmd, **opts):
            appels.append((cmd, opts))
            if cmd[1] == 'ci':
                (opts['cwd'] / 'node_modules').mkdir()
            else:
                (opts['cwd'] / 'dist').mkdir()
                (opts['cwd'] / 'dist/index.html').write_text('fixture')
        release = self.root / 'release'
        P.construire(path, sha, release, fake)
        self.assertEqual(len(appels), 4)
        self.assertEqual((release / 'BUILD_OK').read_text().strip(), sha)
        self.assertEqual(json.loads((release / 'SOURCE_FILES.json').read_text()),
                         ['app/dist/index.html', 'app/package.json', 'mode-studio/dist/index.html'])
        for _, opts in appels:
            self.assertEqual(opts['env']['NPM_CONFIG_USERCONFIG'], '/dev/null')
            self.assertEqual(opts['env']['NPM_CONFIG_GLOBALCONFIG'], '/dev/null')
            self.assertNotIn('NODE_OPTIONS', opts['env'])

    def test_echec_build_ne_cree_pas_marqueur_ni_ne_touche_application(self):
        path, sha = self.archive()
        cible = self.root / 'application-active'
        cible.mkdir()
        (cible / 'inconnu').write_text('conservé')
        def fake(cmd, **opts):
            raise subprocess.CalledProcessError(1, cmd)
        with self.assertRaises(subprocess.CalledProcessError):
            P.construire(path, sha, self.root / 'release', fake)
        self.assertFalse((self.root / 'release/BUILD_OK').exists())
        self.assertEqual((cible / 'inconnu').read_text(), 'conservé')

    def test_archive_secrete_ou_modifiee_refusee(self):
        path, sha = self.archive(('app/.env',))
        with self.assertRaises(ValueError):
            P.construire(path, sha, self.root / 'release', lambda *a, **k: None)
        self.assertFalse((self.root / 'release/BUILD_OK').exists())
        with self.assertRaisesRegex(ValueError, 'altérée'):
            P.construire(path, '0' * 64, self.root / 'autre', lambda *a, **k: None)
        self.assertFalse((self.root / 'autre').exists())

    def test_build_reel_hors_chroot_refuse_avant_creation(self):
        source, sha = self.archive()
        with self.assertRaisesRegex(ValueError, 'chroot CI isolé'):
            P.construire(source, sha, self.root / 'interdit')
        self.assertFalse((self.root / 'interdit').exists())

    def test_archive_git_exclut_env_et_npmrc_sans_les_lire(self):
        repo = self.root / 'repo'
        repo.mkdir()
        env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.root), 'GIT_CONFIG_NOSYSTEM': '1',
               'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
               'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
        def git(*args):
            return subprocess.check_output(['git', '-C', str(repo), *args], env=env, stderr=subprocess.DEVNULL)
        git('init', '-q')
        (repo / 'app').mkdir()
        (repo / 'mode-studio').mkdir()
        (repo / 'app/package.json').write_text('{}')
        (repo / 'app/.env.example').write_text('fixture')
        (repo / 'app/.npmrc').write_text('fixture')
        (repo / 'mode-studio/package.json').write_text('{}')
        git('add', '-f', 'app', 'mode-studio')
        git('commit', '-qm', 'fixture')
        sha = git('rev-parse', 'HEAD').decode().strip()
        out = self.root / 'source.tar'
        digest = P.archive(repo, sha, out)
        with tarfile.open(out) as tar:
            noms = tar.getnames()
        self.assertIn('app/package.json', noms)
        self.assertNotIn('app/.env.example', noms)
        self.assertNotIn('app/.npmrc', noms)
        self.assertEqual(len(digest), 64)
        with self.assertRaises(ValueError):
            P.archive(repo, 'main', self.root / 'invalide.tar')

    def test_import_artefact_ci_et_sha_git(self):
        source, sha = self.archive()
        release = self.root / 'release'
        def fake(cmd, **opts):
            if cmd[1] == 'ci':
                (opts['cwd'] / 'node_modules').mkdir()
            else:
                (opts['cwd'] / 'dist').mkdir()
                (opts['cwd'] / 'dist/index.html').write_text('fixture')
        P.construire(source, sha, release, fake)
        (release / 'CI_COMMIT_SHA').write_text('a' * 40 + '\n')
        artefact = self.root / 'artefact.tar'
        with tarfile.open(artefact, 'w') as tar:
            for item in ('app', 'mode-studio/dist', 'BUILD_OK', 'SOURCE_FILES.json', 'SOURCE_HASHES.json', 'DEPENDANCES_SHA256', 'CI_COMMIT_SHA'):
                tar.add(release / item, arcname='release/' + item)
        with artefact.open('rb') as f:
            empreinte = hashlib.file_digest(f, 'sha256').hexdigest()
        P.importer(artefact, empreinte, 'a' * 40, self.root / 'importe')
        self.assertEqual((self.root / 'importe/BUILD_OK').read_text().strip(), sha)
        with self.assertRaisesRegex(ValueError, 'SHA Git'):
            P.importer(artefact, empreinte, 'b' * 40, self.root / 'refuse')
        self.assertFalse((self.root / 'refuse/BUILD_OK').exists())


if __name__ == '__main__':
    unittest.main()
