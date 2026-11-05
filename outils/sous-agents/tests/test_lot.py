import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]


class LotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.prompts = self.root / "prompts"
        self.workdirs = self.root / "workdirs"
        self.state = self.root / "state"
        self.tool = self.root / "tool"
        self.prompts.mkdir()
        self.workdirs.mkdir()
        self.tool.mkdir()
        for source in (HERE / "lot.sh", HERE / "lot.py"):
            shutil.copy2(source, self.tool / source.name)
        for source in (HERE / "tests" / "fixtures").iterdir():
            if not source.is_file():
                continue
            target = self.tool / source.name
            shutil.copy2(source, target)
            if source.name.endswith(".sh"):
                target.chmod(0o755)
        self.gateway_log = self.root / "gateway.log"
        self.counter = self.root / "counter.json"
        self.counter.write_text(json.dumps({"active": 0, "max_active": 0, "started": []}))
        self.env = dict(os.environ)
        self.env.update({
            "SA_STATE": str(self.state),
            "FAKE_GATEWAY_LOG": str(self.gateway_log),
            "FAKE_COUNTER": str(self.counter),
            "LOT_BUDGET": "5",
            "LOT_RUN_BUDGET": "0.30",
            "LOT_TURNS": "5",
        })

    def add_task(self, name, body=""):
        (self.prompts / f"{name}.txt").write_text(body or "MODE=OK\n", encoding="utf-8")
        (self.workdirs / name).mkdir()

    def run_lot(self, *extra, timeout=10):
        return subprocess.run(
            ["bash", str(self.tool / "lot.sh"), "muse", str(self.prompts), str(self.workdirs), *map(str, extra)],
            env=self.env, text=True, capture_output=True, timeout=timeout,
        )

    def index(self):
        files = list((self.state / "lots").glob("*/index.tsv"))
        self.assertTrue(files)
        return files[-1], files[-1].read_text(encoding="utf-8")

    def started(self):
        return json.loads(self.counter.read_text(encoding="utf-8"))["started"]

    def test_populated_workdirs_are_preserved_and_success_needs_summary_and_exit_zero(self):
        self.add_task("alpha", "DELAY=0.03\n")
        self.add_task("beta", "DELAY=0.03\n")
        (self.workdirs / "alpha" / "KEEP").write_text("alpha sentinel")
        (self.workdirs / "beta" / "KEEP").write_text("beta sentinel")
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        _, index = self.index()
        self.assertIn("OK\talpha\t0\ttermine", index)
        self.assertIn("OK\tbeta\t0\ttermine", index)
        self.assertEqual((self.workdirs / "alpha" / "KEEP").read_text(), "alpha sentinel")
        self.assertEqual((self.workdirs / "beta" / "KEEP").read_text(), "beta sentinel")
        self.assertEqual(len(self.started()), 2)

    def test_txt_md_name_collision_aborts_before_gateway_or_launcher(self):
        (self.prompts / "same.txt").write_text("MODE=OK\n")
        (self.prompts / "same.md").write_text("MODE=OK\n")
        (self.workdirs / "same").mkdir()
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("collision .txt/.md", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        self.assertFalse((self.state / "lots").exists())

    def test_internal_artifact_names_are_reserved_before_any_start(self):
        for name in ("index.tsv", "index.tsv.tmp", "lot_status.txt"):
            (self.prompts / f"{name}.txt").write_text("MODE=OK\n")
            (self.workdirs / name).mkdir()
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("nom de tâche réservé", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        self.assertFalse((self.state / "lots").exists())

    def test_task_log_name_cannot_overlap_another_task_output_directory(self):
        (self.prompts / "first.txt").write_text("MODE=OK\n")
        (self.prompts / "first.launcher.log.md").write_text("MODE=OK\n")
        (self.workdirs / "first").mkdir()
        (self.workdirs / "first.launcher.log").mkdir()
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("collision de sorties", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        self.assertFalse((self.state / "lots").exists())

    def test_distinct_names_that_resolve_through_symlinks_to_one_workdir_abort(self):
        (self.prompts / "one.txt").write_text("MODE=OK\n")
        (self.prompts / "two.md").write_text("MODE=OK\n")
        (self.workdirs / "one").mkdir()
        (self.workdirs / "two").symlink_to("one", target_is_directory=True)
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("identiques ou liés par symlink", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])

    def test_prompt_symlink_resolving_outside_prompt_root_aborts_before_start(self):
        outside = self.root / "outside-prompt.txt"
        outside.write_text("MODE=OK\n", encoding="utf-8")
        (self.prompts / "secret.txt").symlink_to(outside)
        (self.workdirs / "secret").mkdir()
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("prompt résolu hors du dossier déclaré", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        self.assertFalse((self.state / "lots").exists())

    def test_workdir_symlink_resolving_outside_work_root_aborts_before_start(self):
        outside = self.root / "outside-workdir"
        outside.mkdir()
        (self.prompts / "escape.txt").write_text("MODE=OK\n", encoding="utf-8")
        (self.workdirs / "escape").symlink_to(outside, target_is_directory=True)
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("workdir résolu hors du dossier déclaré", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        self.assertFalse((self.state / "lots").exists())

    def test_workdir_symlink_staying_inside_root_remains_supported(self):
        (self.prompts / "alias.txt").write_text("MODE=OK\n", encoding="utf-8")
        (self.workdirs / "real").mkdir()
        (self.workdirs / "alias").symlink_to("real", target_is_directory=True)
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.started(), ["alias"])
        _, index = self.index()
        self.assertIn("OK\talias\t0\ttermine", index)

    def test_nested_symlink_workdirs_abort_before_either_agent_starts(self):
        (self.prompts / "parent.txt").write_text("MODE=OK\n")
        (self.prompts / "nested.md").write_text("MODE=OK\n")
        (self.workdirs / "parent" / "child").mkdir(parents=True)
        (self.workdirs / "nested").symlink_to(self.workdirs / "parent" / "child", target_is_directory=True)
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("workdirs se recouvrent", result.stderr)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        self.assertFalse((self.state / "lots").exists())

    def test_duplicate_run_ids_fail_attribution_for_every_affected_task(self):
        self.add_task("first", "MODE=DUPLICATE_RUN_ID\nDELAY=0.04\n")
        self.add_task("second", "MODE=DUPLICATE_RUN_ID\nDELAY=0.04\n")
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(set(self.started()), {"first", "second"})
        _, index = self.index()
        self.assertIn("FAIL\tfirst\t0\trun_id_duplique", index)
        self.assertIn("FAIL\tsecond\t0\trun_id_duplique", index)

    def test_missing_workdir_is_skip_without_implicit_creation(self):
        (self.prompts / "missing.txt").write_text("MODE=OK\n")
        result = self.run_lot("2")
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.workdirs / "missing").exists())
        self.assertFalse(self.gateway_log.exists())
        index_path, index = self.index()
        self.assertIn("SKIP\tmissing\t-\tpas_de_workdir", index)
        self.assertEqual((index_path.parent / "lot_status.txt").read_text().strip(), "FAIL")

    def test_explicit_creation_adds_only_missing_workdir_and_preserves_existing_contents(self):
        (self.prompts / "kept.txt").write_text("MODE=OK\n")
        (self.prompts / "new.md").write_text("MODE=OK\n")
        (self.workdirs / "kept").mkdir()
        (self.workdirs / "kept" / "sentinel").write_text("do not alter")
        result = self.run_lot("2", "--create-workdirs")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue((self.workdirs / "new").is_dir())
        self.assertEqual((self.workdirs / "kept" / "sentinel").read_text(), "do not alter")
        _, index = self.index()
        self.assertIn("OK\tnew\t0\ttermine", index)

    def test_global_budget_reservations_bound_parallel_starts_then_reuse_after_completion(self):
        for name in ("a", "b", "c"):
            self.add_task(name, "DELAY=0.16\nCOST=0.01\n")
        self.env["LOT_BUDGET"] = "0.60"
        self.env["LOT_RUN_BUDGET"] = "0.30"
        result = self.run_lot("3", timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        counts = json.loads(self.counter.read_text())
        self.assertEqual(set(counts["started"]), {"a", "b", "c"})
        self.assertEqual(counts["max_active"], 2)

    def test_budget_too_small_for_two_reservations_waits_and_reuses_remainder(self):
        for name in ("a", "b", "c"):
            self.add_task(name, "DELAY=0.08\nCOST=0.01\n")
        self.env["LOT_BUDGET"] = "0.35"
        self.env["LOT_RUN_BUDGET"] = "0.30"
        result = self.run_lot("3", timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        counts = json.loads(self.counter.read_text())
        self.assertEqual(set(counts["started"]), {"a", "b", "c"})
        self.assertEqual(counts["max_active"], 1)

    def test_small_decimal_budget_uses_runner_accepted_plain_notation(self):
        self.add_task("small", "COST=0.000000001\n")
        self.env["LOT_BUDGET"] = "0.30"
        self.env["LOT_RUN_BUDGET"] = "0.00000001"
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        _, index = self.index()
        self.assertIn("OK\tsmall\t0\ttermine", index)
        self.assertNotIn("budget invalide", result.stdout + result.stderr)

    def test_small_decimal_budget_passes_real_runner_validation_without_docker(self):
        runner = Path(os.environ.get("SA_TEST_RUNNER", str(HERE / "sous-agent.sh")))
        if not runner.is_file():
            self.skipTest("runner réel absent de cette copie de fichiers")
        shutil.copy2(runner, self.tool / "sous-agent.sh")
        (self.tool / "sous-agent.sh").chmod(0o755)
        (self.tool / "lib.sh").write_text(
            'SA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
            'SA_STATE="${SA_STATE:?}"; SA_HOME="$SA_STATE/home"; SA_PORT=4410\n'
            'SA_URL=http://127.0.0.1:4410; SA_KEYFILE="$SA_STATE/keys"; SA_IMAGE=fake; SA_CONTAINER=fake\n'
            'sa_alias(){ case "$1" in muse|eco-muse) echo eco-muse;; *) return 1;; esac; }\n',
            encoding="utf-8",
        )
        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        docker_log = self.root / "docker.log"
        docker = fake_bin / "docker"
        docker.write_text(
            '#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$FAKE_DOCKER_LOG"\nexit 1\n',
            encoding="utf-8",
        )
        docker.chmod(0o755)
        self.env.update({
            "LOT_BUDGET": "0.30",
            "LOT_RUN_BUDGET": "0.00000001",
            "FAKE_DOCKER_LOG": str(docker_log),
            "PATH": f"{fake_bin}:{Path(sys.executable).parent}:/usr/bin:/bin",
        })
        self.add_task("small", "MODE=OK\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)  # fake Docker deliberately blocks before service access
        self.assertTrue(docker_log.exists())
        launcher_logs = list((self.state / "lots").glob("*/*.launcher.log"))
        self.assertEqual(len(launcher_logs), 1)
        text = launcher_logs[0].read_text(encoding="utf-8")
        self.assertIn("passerelle non identifiée", text)
        self.assertNotIn("budget invalide", text)

    def test_proxy_per_call_run_tags_aggregate_back_to_parent_run(self):
        self.add_task("tagged", "MODE=TAGGED_COST\nCOST=0.01\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        _, index = self.index()
        self.assertIn("OK\ttagged\t0\ttermine", index)

    def test_other_lot_cost_rows_are_not_shared_reservations_and_warning_is_visible(self):
        self.add_task("local", "COST=0.01\n")
        self.state.mkdir()
        (self.state / "usage.jsonl").write_text(
            json.dumps({"run": "other-lot-20261105", "cost": 1000, "alias": "eco-muse"}) + "\n",
            encoding="utf-8",
        )
        self.env["LOT_BUDGET"] = "0.30"
        self.env["LOT_RUN_BUDGET"] = "0.30"
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("aucun partage entre lots simultanés", result.stdout)

    def test_exact_cost_sum_detects_over_budget_below_decimal_context_precision(self):
        self.add_task("boundary", "MODE=OVER_BOUNDARY_TAGGED\n")
        self.env["LOT_BUDGET"] = "0.3"
        self.env["LOT_RUN_BUDGET"] = "0.3"
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        _, index = self.index()
        self.assertIn("FAIL\tboundary\t0\tbudget_run_depasse", index)

    def test_fail_summary_with_zero_process_code_is_not_reported_as_success(self):
        self.add_task("bad", "MODE=FAIL_SUMMARY\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)
        _, index = self.index()
        self.assertIn("FAIL\tbad\t0\tresume_agent_echec", index)
        self.assertIn("statut du lot : FAIL (cout_attribue)", result.stdout)
        self.assertIn("aucun partage entre lots simultanés ni plafond dur", result.stdout)

    def test_nonzero_launcher_code_is_failure_even_with_ok_summary(self):
        self.add_task("bad", "RC=7\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)
        _, index = self.index()
        self.assertIn("FAIL\tbad\t7\tprocessus_en_echec", index)

    def assert_cost_failure_stops(self, mode):
        self.add_task("first", f"MODE={mode}\nDELAY=0.02\n")
        self.add_task("second", "MODE=OK\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(self.started(), ["first"])
        _, index = self.index()
        self.assertIn("FAIL\tfirst", index)
        self.assertIn("SKIP\tsecond", index)

    def test_corrupt_cost_journal_stops_new_starts(self):
        self.assert_cost_failure_stops("CORRUPT")

    def test_unknown_cost_stops_new_starts(self):
        self.assert_cost_failure_stops("UNKNOWN_COST")

    def test_unattributed_historical_prefix_is_ignored_but_reported(self):
        self.add_task("current", "COST=0.01\n")
        self.state.mkdir()
        rows = [{"cost": None, "alias": "eco-muse"} for _ in range(34)]
        (self.state / "usage.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8",
        )
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("34 ligne(s) sans run existaient avant ce lot", result.stdout)

    def test_new_unattributed_cost_row_after_snapshot_stops_pending_agents(self):
        self.add_task("first", "MODE=UNATTRIBUTED\nDELAY=0.02\n")
        self.add_task("second", "MODE=OK\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertEqual(self.started(), ["first"])
        _, index = self.index()
        self.assertIn("FAIL\tfirst\t0\tcout_nouveau_non_attribuable", index)
        self.assertIn("SKIP\tsecond\t-\tcout_nouveau_non_attribuable", index)

    def test_unterminated_historical_snapshot_blocks_before_gateway(self):
        self.add_task("current", "MODE=OK\n")
        self.state.mkdir()
        (self.state / "usage.jsonl").write_text(
            json.dumps({"run": "old-run", "cost": 0.01}), encoding="utf-8",
        )
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        _, index = self.index()
        self.assertIn("SKIP\tcurrent\t-\tjournal_illisible", index)

    def test_non_regular_cost_journal_is_rejected_without_blocking(self):
        self.add_task("current", "MODE=OK\n")
        self.state.mkdir()
        os.mkfifo(self.state / "usage.jsonl")
        result = self.run_lot("1", timeout=3)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        _, index = self.index()
        self.assertIn("SKIP\tcurrent\t-\tjournal_illisible", index)

    def test_symlink_cost_journal_is_rejected_before_gateway(self):
        self.add_task("current", "MODE=OK\n")
        self.state.mkdir()
        real_log = self.state / "real-usage.jsonl"
        real_log.write_text(json.dumps({"run": "old-run", "cost": 0.01}) + "\n", encoding="utf-8")
        (self.state / "usage.jsonl").symlink_to(real_log)
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        _, index = self.index()
        self.assertIn("SKIP\tcurrent\t-\tjournal_illisible", index)

    def test_unterminated_new_append_is_rejected(self):
        self.add_task("first", "MODE=NO_FINAL_LF\n")
        self.add_task("second", "MODE=OK\n")
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.started(), ["first"])
        _, index = self.index()
        self.assertIn("FAIL\tfirst\t0\tjournal_illisible", index)
        self.assertIn("SKIP\tsecond\t-\tjournal_illisible", index)

    def test_corrupt_initial_journal_blocks_gateway_and_all_launches(self):
        self.add_task("first", "MODE=OK\n")
        self.state.mkdir()
        (self.state / "usage.jsonl").write_text('{"cost":\n')
        result = self.run_lot("1")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.gateway_log.exists())
        self.assertEqual(self.started(), [])
        _, index = self.index()
        self.assertIn("SKIP\tfirst\t-\tjournal_illisible", index)


if __name__ == "__main__":
    unittest.main()
