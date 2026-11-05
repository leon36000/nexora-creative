import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'cout.py'

class TestCout(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.log = self.state / 'usage.jsonl'
        self.env = dict(os.environ, SA_STATE=str(self.state))

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=self.env, text=True, capture_output=True)

    def write_rows(self, *rows):
        self.log.write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def row(self, alias='eco-muse', cost=0.1, **kwargs):
        return {'ts': '2026-11-05T01:00:00-0500', 'run': 'lot-a-1', 'alias': alias, 'ok': True,
                'in': 100, 'out': 10, 'cost': cost, **kwargs}

    def test_mixed_models_sum_all_tokens_and_costs(self):
        self.write_rows(self.row(), self.row(alias='eco-deepseek', cost=0.2, **{'in': 20, 'out': 5}))
        r = self.run_cli('--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        t = json.loads(r.stdout)['total']
        self.assertEqual((t['requetes'], t['in'], t['out'], t['cout_total']), (2, '120', '15', '0.3'))

    def test_missing_cost_is_not_zero_and_known_subtotal_remains_visible(self):
        self.write_rows(self.row(cost=None), self.row(cost=0.2))
        r = self.run_cli('--json')
        t = json.loads(r.stdout)['total']
        self.assertIsNone(t['cout_total'])
        self.assertEqual((t['couts_inconnus'], t['cout_connu']), (1, '0.2'))
        self.assertIn('inconnu', self.run_cli().stdout)

    def test_zero_cost_is_distinct_from_unknown(self):
        self.write_rows(self.row(cost=0))
        t = json.loads(self.run_cli('--json').stdout)['total']
        self.assertEqual((t['cout_total'], t['couts_inconnus']), ('0', 0))

    def test_missing_tokens_and_status_reported_unknown(self):
        row = self.row(); row.update({'in': None, 'ok': None})
        self.write_rows(row)
        t = json.loads(self.run_cli('--json').stdout)['total']
        self.assertIsNone(t['in']); self.assertEqual(t['statuts_inconnus'], 1)

    def test_filters_and_unattributed_records(self):
        self.write_rows(self.row(run=None), self.row(run='lot-a-2'), self.row(run='lot-b-2', cost=0.4))
        r = self.run_cli('--since', '2026-11-05', '--run', 'lot-a', '--json')
        d = json.loads(r.stdout)
        self.assertEqual((d['total']['requetes'], d['sans_identifiant']), (1, 1))
        self.assertIsNone(d['total']['cout_total']); self.assertIsNone(d['total']['in'])

    def test_corruption_or_missing_journal_is_not_reported_as_zero(self):
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.log.write_text('{"cost":')
        r = self.run_cli()
        self.assertNotEqual(r.returncode, 0); self.assertIn('inconnu', r.stderr)
        self.assertNotIn('{"cost":', r.stderr)

    def test_invalid_date_and_unknown_alias_do_not_echo_payload(self):
        self.write_rows(self.row(alias='SECRET_DO_NOT_PRINT'))
        self.assertNotEqual(self.run_cli('--since', '2026-99-99').returncode, 0)
        r = self.run_cli()
        self.assertNotIn('SECRET_DO_NOT_PRINT', r.stdout)
        self.assertIn('autre', r.stdout)

    def test_noninteger_tokens_are_not_presented_as_a_count(self):
        self.write_rows(self.row(**{'in': 1.5}))
        t = json.loads(self.run_cli('--json').stdout)['total']
        self.assertIsNone(t['in'])

    def test_undated_record_makes_filtered_total_unknown(self):
        self.write_rows(self.row(ts=None), self.row())
        t = json.loads(self.run_cli('--since', '2026-11-05', '--json').stdout)
        self.assertEqual(t['sans_date'], 1)
        self.assertIsNone(t['total']['cout_total'])
        self.assertIsNone(t['total']['in'])

    def test_run_prefix_does_not_include_similar_identifier(self):
        self.write_rows(self.row(run='abc-1', cost=0.1), self.row(run='abcd-1', cost=0.2))
        t = json.loads(self.run_cli('--run', 'abc', '--json').stdout)['total']
        self.assertEqual((t['requetes'], t['cout_total']), (1, '0.1'))

    def test_duplicate_json_keys_are_not_accepted_as_a_cost(self):
        self.log.write_text('{"cost":1.0,"cost":0.0}\n')
        r = self.run_cli('--json')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('inconnu', r.stderr)

    def test_no_matching_rows_is_not_a_free_request(self):
        self.write_rows(self.row())
        r = self.run_cli('--run', 'absent')
        self.assertIn('aucune donnée de coût', r.stdout)
        total = json.loads(self.run_cli('--run', 'absent', '--json').stdout)['total']
        self.assertIsNone(total['cout_total'])
        self.assertIsNone(total['in']); self.assertIsNone(total['out'])

    def test_tiny_nonzero_cost_is_not_displayed_as_zero(self):
        self.write_rows(self.row(cost=0.00000001))
        self.assertIn('<$0.00001', self.run_cli().stdout)

    def test_extreme_cost_or_exponent_does_not_crash_or_report_zero(self):
        self.log.write_text('{"alias":"eco-muse","cost":1e999999999}\n')
        r = self.run_cli('--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIsNone(json.loads(r.stdout)['total']['cout_total'])
        self.log.write_text('{"cost":1e99999999999999999999}\n')
        r = self.run_cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn('Traceback', r.stderr)

    def test_undated_rows_are_scoped_to_selected_run(self):
        self.write_rows(self.row(run='a-1', ts=None), self.row(run='b-1'))
        d = json.loads(self.run_cli('--run', 'b', '--since', '2026-11-05', '--json').stdout)
        self.assertEqual((d['sans_date'], d['total']['requetes']), (0, 1))

    def test_deep_json_and_missing_home_fail_without_traceback(self):
        self.log.write_text('[' * 20000)
        r = self.run_cli()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn('Traceback', r.stderr)
        env = dict(self.env); env.pop('HOME', None)
        self.write_rows(self.row())
        r = subprocess.run([sys.executable, str(SCRIPT)], env=env, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_decimal_sum_keeps_small_cost_next_to_large_value(self):
        self.log.write_text('{"cost":9999999999999999999999999.12345}\n{"cost":0.00001}\n')
        d = json.loads(self.run_cli('--json').stdout)
        self.assertEqual(d['total']['cout_total'], '9999999999999999999999999.12346')

if __name__ == '__main__':
    unittest.main()
