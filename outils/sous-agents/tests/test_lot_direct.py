"""Exécute le coordinateur source directement avec les mêmes fixtures sans réseau."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lot
import test_lot


class LotDirectTests(unittest.TestCase):
    def test_completed_tasks_are_all_reaped_from_snapshot(self):
        process = SimpleNamespace(returncode=0, poll=lambda: 0)
        first = lot.Task('first', Path('/fictif/first.txt'), Path('/fictif/first'), process=process, run_id='lot-first')
        second = lot.Task('second', Path('/fictif/second.txt'), Path('/fictif/second'), process=process, run_id='lot-second')
        state = lot.SupervisorState(tasks=[first, second], pending=[], active=[first, second],
                                    run_owners={}, duplicate_run_ids=set())
        journal = lot.Ledger(True, 0, {'lot-first': 0, 'lot-second': 0})
        baseline = lot.LedgerBaseline(raw=b'', unattributed_rows=0)
        with patch.object(lot, 'register_run_id', return_value=''), patch.object(lot, 'read_ledger', return_value=journal), patch.object(lot, 'finish_task') as finish:
            changed = lot.reap_finished(state, 'lot', Path('/fictif/journal'), baseline, 1, state.tasks)
        self.assertTrue(changed)
        self.assertEqual(state.active, [])
        self.assertEqual(finish.call_count, 2)

    def test_cost_report_write_error_is_classified_as_127(self):
        config = SimpleNamespace(sa_dir=Path('/fictif'))
        report = SimpleNamespace(stdout='donnée fictive', returncode=0)
        with patch.object(lot.subprocess, 'run', return_value=report), patch('builtins.print', side_effect=OSError('fictif')):
            result = lot.report_costs(config, 'lot-fictif', {})
        self.assertEqual(result, 127)

    def test_workdir_creation_error_blocks_other_tasks(self):
        root = Path('/fictif')
        failed = lot.Task('bad', root / 'bad.txt', root / 'bad', detail='a_creer')
        other = lot.Task('ready', root / 'ready.txt', root / 'ready')
        with patch.object(Path, 'mkdir', side_effect=PermissionError('fictif')):
            result = lot.create_workdirs([failed, other], root)
        self.assertEqual((result[0].status, result[0].detail), ('FAIL', 'creation_workdir_echec'))
        self.assertEqual((result[1].status, result[1].detail), ('SKIP', 'creation_lot_incomplete'))

    def test_run_suffix_digits_remain_ascii_only(self):
        tag = 'lot-fake--p0123456789abcdef--c1٢'
        self.assertEqual(lot.base_run_id(tag), tag)
        self.assertEqual(lot.base_run_id('lot-fake--p0123456789abcdef--c12'), 'lot-fake')

    def setUp(self):
        self.fixture = test_lot.LotTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.run_lot = self.run_lot

    def run_lot(self, *extra, timeout=10):
        del timeout
        f = self.fixture
        env = dict(f.env, SA_DIR=str(f.tool))
        out, err = io.StringIO(), io.StringIO()
        args = ['muse', str(f.prompts), str(f.workdirs), *map(str, extra)]
        with patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = lot.main(args)
        return subprocess.CompletedProcess(args, code, out.getvalue(), err.getvalue())

    def test_budget_concurrent_et_reservation(self):
        self.fixture.test_global_budget_reservations_bound_parallel_starts_then_reuse_after_completion()

    def test_budget_reste_insuffisant(self):
        self.fixture.test_budget_too_small_for_two_reservations_waits_and_reuses_remainder()

    def test_tags_attribues(self):
        self.fixture.test_proxy_per_call_run_tags_aggregate_back_to_parent_run()

    def test_journal_corrompu(self):
        self.fixture.test_corrupt_cost_journal_stops_new_starts()

    def test_cout_inconnu(self):
        self.fixture.test_unknown_cost_stops_new_starts()

    def test_cout_non_attribue(self):
        self.fixture.test_new_unattributed_cost_row_after_snapshot_stops_pending_agents()

    def test_collision_identifiants(self):
        self.fixture.test_duplicate_run_ids_fail_attribution_for_every_affected_task()

    def test_creation_explicite(self):
        self.fixture.test_explicit_creation_adds_only_missing_workdir_and_preserves_existing_contents()

    def test_dossiers_identiques(self):
        self.fixture.test_distinct_names_that_resolve_through_symlinks_to_one_workdir_abort()

    def test_noms_de_sortie_reserves(self):
        self.fixture.test_internal_artifact_names_are_reserved_before_any_start()

# Exercices supplémentaires du coordinateur original : validations, échecs et coût exact.
def _cas_direct(nom):
    def executer(self):
        getattr(self.fixture, nom)()
    return executer

for _nom in (
    'test_populated_workdirs_are_preserved_and_success_needs_summary_and_exit_zero',
    'test_txt_md_name_collision_aborts_before_gateway_or_launcher',
    'test_task_log_name_cannot_overlap_another_task_output_directory',
    'test_prompt_symlink_resolving_outside_prompt_root_aborts_before_start',
    'test_workdir_symlink_resolving_outside_work_root_aborts_before_start',
    'test_workdir_symlink_staying_inside_root_remains_supported',
    'test_nested_symlink_workdirs_abort_before_either_agent_starts',
    'test_missing_workdir_is_skip_without_implicit_creation',
    'test_small_decimal_budget_uses_runner_accepted_plain_notation',
    'test_small_decimal_budget_passes_real_runner_validation_without_docker',
    'test_other_lot_cost_rows_are_not_shared_reservations_and_warning_is_visible',
    'test_exact_cost_sum_detects_over_budget_below_decimal_context_precision',
    'test_fail_summary_with_zero_process_code_is_not_reported_as_success',
    'test_nonzero_launcher_code_is_failure_even_with_ok_summary',
    'test_unattributed_historical_prefix_is_ignored_but_reported',
    'test_unterminated_historical_snapshot_blocks_before_gateway',
    'test_non_regular_cost_journal_is_rejected_without_blocking',
    'test_symlink_cost_journal_is_rejected_before_gateway',
    'test_unterminated_new_append_is_rejected',
    'test_corrupt_initial_journal_blocks_gateway_and_all_launches',
):
    setattr(LotDirectTests, 'test_direct_' + _nom[5:], _cas_direct(_nom))
