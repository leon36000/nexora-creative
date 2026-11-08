"""Path refusals: stdlib only, no Comfy import and no GPU."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'create_private_overlay.py'

class OverlayPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'comfy' / 'comfy_extras' / 'nodes_mesh_postprocess.py'
        self.source.parent.mkdir(parents=True)
        self.source.write_text('dummy')

    def tearDown(self):
        self.tmp.cleanup()

    def check_rejected(self, path, message):
        result = subprocess.run([sys.executable, str(SCRIPT), '--source', str(self.source), '--output', str(path)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(message, result.stderr)
        self.assertEqual(self.source.read_text(), 'dummy')

    def test_rejects_comfy_tree(self):
        self.check_rejected(self.source.parent / 'overlay.py', 'dossier Comfy')

    def test_rejects_git_tree(self):
        repo = self.root / 'repo'
        repo.mkdir()
        (repo / '.git').mkdir()
        (repo / '.git' / 'HEAD').write_text('ref: refs/heads/main')
        self.check_rejected(repo / 'new' / 'overlay.py', 'dépôt Git')

    def test_rejects_broken_final_symlink(self):
        link = self.root / 'broken.py'
        link.symlink_to(self.root / 'nonexistent.py')
        self.check_rejected(link, 'Lien symbolique')
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.root / 'nonexistent.py').exists())

    def test_rejects_symlink_parent(self):
        actual = self.root / 'actual'
        actual.mkdir()
        link = self.root / 'linked'
        link.symlink_to(actual, target_is_directory=True)
        self.check_rejected(link / 'overlay.py', 'Lien symbolique')
        self.assertFalse((actual / 'overlay.py').exists())

    def test_rejects_existing_file(self):
        output = self.root / 'existing.py'
        output.write_text('preserve')
        self.check_rejected(output, 'sortie existe déjà')
        self.assertEqual(output.read_text(), 'preserve')

if __name__ == '__main__':
    unittest.main()
