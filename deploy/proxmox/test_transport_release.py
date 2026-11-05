import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tarfile
import unittest


class Transport(unittest.TestCase):
    def test_transport_ssh_fictif_unique_et_empreintes(self):
        with tempfile.TemporaryDirectory() as dossier:
            base = Path(dossier)
            repo, distant, binaires = (base / x for x in ('repo', 'distant', 'bin'))
            for p in (repo / 'deploy/proxmox', repo / 'app', repo / 'mode-studio', distant, binaires):
                p.mkdir(parents=True)
            origine = Path(__file__).parent
            for nom in ('preparer_release.py', 'transaction_release.py', 'livrer_release.py', 'mettre-a-jour-creative.sh'):
                shutil.copyfile(origine / nom, repo / 'deploy/proxmox' / nom)
            (repo / 'app/package.json').write_text('{}')
            (repo / 'mode-studio/package.json').write_text('{}')
            ssh = binaires / 'ssh'
            ssh.write_text('#!/usr/bin/python3\nimport os,subprocess,sys\nc=sys.argv[-1].replace("/srv/creative",os.environ["TEST_DISTANT"])\nsys.exit(subprocess.run(["/bin/bash","-c",c],stdin=sys.stdin).returncode)\n')
            ssh.chmod(0o755)
            env = {'PATH': f'{binaires}:/usr/bin:/bin', 'HOME': str(base), 'TEST_DISTANT': str(distant),
                   'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_SYSTEM': '/dev/null',
                   'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
                   'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], env=env, stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('add', '.')
            git('commit', '-qm', 'fixture')
            sha = git('rev-parse', 'HEAD').decode().strip()
            artefact = base / 'artefact.tar'
            with tarfile.open(artefact, 'w') as t:
                contenu = (sha + '\n').encode()
                entree = tarfile.TarInfo('release/CI_COMMIT_SHA')
                entree.size = len(contenu)
                t.addfile(entree, io.BytesIO(contenu))
            sha_artefact = hashlib.sha256(artefact.read_bytes()).hexdigest()
            script = origine / 'transporter-release.sh'
            local = base / 'local-neuf'
            cmd = ['bash', str(script), str(repo), sha, str(artefact), sha_artefact, str(local), 'test-12345678']
            subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL)
            recu = distant / 'livraisons/test-12345678'
            for nom in ('release.tar', 'release.sha256', 'commit.sha', 'preparer_release.py', 'transaction_release.py', 'livrer_release.py', 'mettre-a-jour-creative.sh'):
                self.assertEqual(hashlib.sha256((local / nom).read_bytes()).digest(), hashlib.sha256((recu / nom).read_bytes()).digest())
            original = (recu / 'release.tar').read_bytes()
            cmd[6] = str(base / 'local-autre')
            with self.assertRaises(subprocess.CalledProcessError):
                subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertEqual((recu / 'release.tar').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
