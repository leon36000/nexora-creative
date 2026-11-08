#!/usr/bin/env python3
"""CPU-only stdlib checks for manifest and path refusals."""
from __future__ import annotations
import hashlib, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_inputs import git_root_ancestor, symlink_component, validate_layout, validate_renderer_paths, validate_stage_name, verify_entry

class PathSafetyTests(unittest.TestCase):
    def layout(self, base: Path):
        storage=base/'Storage'/'Nexora'/'travail'; storage.mkdir(parents=True)
        assets=storage/'assets'; assets.mkdir()
        code=storage/'code'; code.mkdir()
        run=storage/'run'; run.mkdir()
        return storage,assets,code,run

    def test_empty_storage_run_allowed_with_empty_git_marker_ancestor(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); storage,assets,code,run=self.layout(base)
            # Empty .git directories are not repositories.
            (storage.parent/'.git').mkdir()
            self.assertIsNone(git_root_ancestor(run))
            self.assertEqual(validate_layout(assets,run,code,storage),(assets.resolve(),run.resolve()))

    def test_real_git_directory_with_head_refused(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); storage,assets,code,run=self.layout(base)
            marker=storage.parent/'.git'; marker.mkdir(); (marker/'HEAD').write_text('ref: refs/heads/main\n')
            with self.assertRaisesRegex(ValueError,'Git worktree/repository'):
                validate_layout(assets,run,code,storage)

    def test_gitfile_worktree_pointer_refused(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); storage,assets,code,run=self.layout(base)
            repo=base/'repo'; gitdir=repo/'.git'/'worktrees'/'w'; gitdir.mkdir(parents=True); (gitdir/'HEAD').write_text('ref: refs/heads/main\n')
            worktree=storage/'worktree'; worktree.mkdir(); (worktree/'.git').write_text('gitdir: '+str(gitdir)+'\n')
            target=worktree/'run'; target.mkdir()
            with self.assertRaisesRegex(ValueError,'Git worktree/repository'):
                validate_layout(assets,target,code,storage)

    def test_symlink_parent_refused(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); storage,assets,code,run=self.layout(base)
            real=storage/'real'; real.mkdir(); alias=storage/'alias'; alias.symlink_to(real,target_is_directory=True)
            linked=alias/'new'; linked.mkdir()
            self.assertEqual(symlink_component(linked),alias)
            with self.assertRaisesRegex(ValueError,'symlink component'):
                validate_layout(assets,linked,code,storage)

    def test_nonempty_run_refused(self):
        with tempfile.TemporaryDirectory() as td:
            storage,assets,code,run=self.layout(Path(td)); (run/'occupied').touch()
            with self.assertRaisesRegex(ValueError,'must be empty'):
                validate_layout(assets,run,code,storage)

    def test_comfyui_destination_refused(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); storage=base/'Storage'/'Nexora'/'travail'; storage.mkdir(parents=True)
            assets=storage/'assets'; assets.mkdir(); code=storage/'code'; code.mkdir()
            run=storage/'ComfyUI'/'run'; run.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'ComfyUI'):
                validate_layout(assets,run,code,storage)

    def test_assets_and_run_overlap_refused(self):
        with tempfile.TemporaryDirectory() as td:
            storage=Path(td)/'Storage'/'Nexora'/'travail'; storage.mkdir(parents=True)
            assets=storage/'assets'; assets.mkdir(); code=storage/'code'; code.mkdir()
            run=assets/'run'; run.mkdir()
            with self.assertRaisesRegex(ValueError,'separate paths'):
                validate_layout(assets,run,code,storage)

    def test_renderer_paths_accept_explicit_tmp_root(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'tmp'; run=root/'run'; stage=run/'inputs'; output=run/'outputs'; code=root/'code'
            stage.mkdir(parents=True); output.mkdir(); code.mkdir()
            self.assertEqual(validate_renderer_paths(run,stage,output,code,root),(run,stage,output,root))

    def test_renderer_paths_refuse_repo_under_override_root(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'tmp'; repo=root/'repo'; git=repo/'.git'; git.mkdir(parents=True); (git/'HEAD').write_text('ref: refs/heads/main\n')
            run=repo/'run'; stage=run/'inputs'; output=run/'outputs'; code=root/'code'
            stage.mkdir(parents=True); output.mkdir(); code.mkdir()
            with self.assertRaisesRegex(ValueError,'Git repository/worktree'):
                validate_renderer_paths(run,stage,output,code,root)

    def test_renderer_paths_refuse_symlink_stage(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'tmp'; run=root/'run'; run.mkdir(parents=True); code=root/'code'; code.mkdir()
            real=run/'real'; real.mkdir(); alias=run/'inputs'; alias.symlink_to(real,target_is_directory=True); out=run/'outputs'; out.mkdir()
            with self.assertRaisesRegex(ValueError,'symlink component'):
                validate_renderer_paths(run,alias,out,code,root)

    def test_renderer_paths_refuse_output_alias(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'tmp'; run=root/'run'; stage=run/'inputs'; stage.mkdir(parents=True); code=root/'code'; code.mkdir()
            with self.assertRaisesRegex(ValueError,'separate children'):
                validate_renderer_paths(run,stage,stage,code,root)

    def test_stage_name_accepts_regular_usda(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); stage=root/'oracle-n4.usda'; stage.write_text('usda')
            self.assertEqual(validate_stage_name('oracle-n4.usda',root),stage.resolve())

    def test_stage_name_refuses_absolute_path(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); stage=root/'oracle-n4.usda'; stage.write_text('usda')
            with self.assertRaisesRegex(ValueError,'basename|absolute'):
                validate_stage_name(str(stage),root)

    def test_stage_name_refuses_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); stage=root.parent/'outside.usda'; stage.write_text('usda')
            with self.assertRaisesRegex(ValueError,'basename|traversal'):
                validate_stage_name('../outside.usda',root)

    def test_stage_name_refuses_backslash_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'basename'):
                validate_stage_name('..\\outside.usda',Path(td))

    def test_stage_name_refuses_symlink_file(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); real=root/'real.usda'; real.write_text('usda'); (root/'alias.usda').symlink_to(real)
            with self.assertRaisesRegex(ValueError,'symlink'):
                validate_stage_name('alias.usda',root)

    def test_stage_name_refuses_wrong_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); stage=root/'oracle.usd'; stage.write_text('usd')
            with self.assertRaisesRegex(ValueError,'suffix|ending'):
                validate_stage_name('oracle.usd',root)

    def test_missing_input_fails_clearly(self):
        with tempfile.TemporaryDirectory() as td:
            missing=Path(td)/'not-there.glb'
            with self.assertRaisesRegex(ValueError,'introuvable'):
                verify_entry({'role':'fixture','bytes':1,'sha256':'0'*64},missing)

    def test_input_hash_and_size_checked(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fixture.bin'; p.write_bytes(b'fixture')
            item={'role':'fixture','bytes':7,'sha256':hashlib.sha256(b'fixture').hexdigest()}
            self.assertEqual(verify_entry(item,p),item['sha256'])
            item['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'taille/SHA différents'):
                verify_entry(item,p)

if __name__=='__main__': unittest.main(verbosity=2)
