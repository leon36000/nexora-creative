from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cost_snapshot


RUN = "offline-test"
TAG1 = RUN + "--p0123456789abcdef--c1"
TAG2 = RUN + "--p0123456789abcdef--c2"


def jsonl(*records: str) -> bytes:
    return ("\n".join(records) + ("\n" if records else "")).encode("utf-8")


def obj(**fields: object) -> str:
    return json.dumps(fields, separators=(",", ":"))


class SnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / "ledger.jsonl"
        self.audit = self.root / "audit.jsonl"

    def write(self, ledger: bytes, audit: bytes) -> None:
        self.ledger.write_bytes(ledger)
        self.audit.write_bytes(audit)

    def audit_rows(self, *tags: str) -> bytes:
        return jsonl(*(obj(sequence=i, call=tag) for i, tag in enumerate(tags, 1)))

    def assert_generic_failure(self) -> None:
        with self.assertRaises(cost_snapshot.SnapshotError) as caught:
            cost_snapshot.snapshot(self.ledger, self.audit, RUN)
        self.assertEqual(str(caught.exception), "snapshot failed")

    def test_sums_base_run_and_exact_tags_and_deduplicates_attempts(self) -> None:
        self.write(
            jsonl(
                '{"run":"offline-test","cost":0.10}',
                '{"run":"offline-test--p0123456789abcdef--c1","cost":0.20}',
                '{"run":"offline-test--p0123456789abcdef--c1","cost":0.30}',
                obj(run="old-run", cost=99),
                obj(run=RUN + "--pffffffffffffffff--c1", cost=88),
            ),
            self.audit_rows(TAG1, TAG2),
        )
        self.assertEqual(
            cost_snapshot.snapshot(self.ledger, self.audit, RUN),
            {"spent": "88.60", "attempts": 2, "pending": 1, "records": 4},
        )

    def test_zero_is_present_and_keeps_declared_scale(self) -> None:
        self.write(jsonl('{"run":"offline-test","cost":0.00}'), b"")
        self.assertEqual(
            cost_snapshot.snapshot(self.ledger, self.audit, RUN),
            {"spent": "0.00", "attempts": 0, "pending": 0, "records": 1},
        )

    def test_empty_audit_and_ledger_are_zero_and_run_cost_is_optional(self) -> None:
        self.write(b"", b"")
        self.assertEqual(
            cost_snapshot.snapshot(self.ledger, self.audit, RUN),
            {"spent": "0", "attempts": 0, "pending": 0, "records": 0},
        )

        self.write(b"", self.audit_rows(TAG1))
        self.assertEqual(
            cost_snapshot.snapshot(self.ledger, self.audit, RUN),
            {"spent": "0", "attempts": 1, "pending": 1, "records": 0},
        )

        self.write(jsonl(obj(run=TAG1, cost=0.4)), self.audit_rows(TAG1))
        self.assertEqual(
            cost_snapshot.snapshot(self.ledger, self.audit, RUN),
            {"spent": "0.4", "attempts": 1, "pending": 0, "records": 1},
        )

    def test_exact_sum_does_not_round(self) -> None:
        self.write(
            jsonl(
                '{"run":"offline-test","cost":0.123456789012345678901234567890}',
                '{"run":"offline-test","cost":0.000000000000000000000000000001}',
            ),
            b"",
        )
        self.assertEqual(
            cost_snapshot.snapshot(self.ledger, self.audit, RUN)["spent"],
            "0.123456789012345678901234567891",
        )

    def test_repeated_nonce_is_allowed_when_counter_is_distinct(self) -> None:
        self.write(jsonl(obj(run=RUN, cost=0)), self.audit_rows(TAG1, TAG2))
        self.assertEqual(cost_snapshot.snapshot(self.ledger, self.audit, RUN)["attempts"], 2)

    def test_old_run_and_nonce_do_not_confirm_current_attempt(self) -> None:
        current = RUN + "--p0123456789abcdef--c1"
        self.write(
            jsonl(
                obj(run=RUN, cost=0),
                obj(run="older-run--p0123456789abcdef--c1", cost=20),
                obj(run=RUN + "--p1111111111111111--c1", cost=30),
            ),
            self.audit_rows(current),
        )
        result = cost_snapshot.snapshot(self.ledger, self.audit, RUN)
        self.assertEqual(result, {"spent": "30", "attempts": 1, "pending": 1, "records": 2})

    def test_malformed_ledger_tag_claims_fail_closed(self) -> None:
        self.audit.write_bytes(b"")
        for tag in (
            RUN + "--p123--c1",
            RUN + "--p0123456789ABCDEF--c1",
            RUN + "--p0123456789abcdef--c0",
            RUN + "--p0123456789abcdef--c01",
        ):
            with self.subTest(tag=tag):
                self.ledger.write_bytes(jsonl(obj(run=RUN, cost=0), obj(run=tag, cost=1)))
                self.assert_generic_failure()

    def test_audit_requires_consecutive_sequence_and_matching_call_counter(self) -> None:
        bad_audits = [
            jsonl(obj(sequence=2, call=TAG1)),
            jsonl(obj(sequence=1, call=TAG2)),
            jsonl(obj(sequence=1, call=RUN + "--p0123456789abcdeZ--c1")),
            jsonl(obj(sequence=1, call=RUN + "--p0123456789abcdef--c01")),
            jsonl(obj(sequence=True, call=TAG1)),
        ]
        self.ledger.write_bytes(jsonl(obj(run=RUN, cost=0)))
        for bad in bad_audits:
            with self.subTest(audit=bad):
                self.audit.write_bytes(bad)
                self.assert_generic_failure()

    def test_duplicate_keys_are_rejected_in_every_line(self) -> None:
        self.write(jsonl('{"run":"offline-test","cost":1,"cost":0}'), b"")
        self.assert_generic_failure()
        self.write(jsonl(obj(run=RUN, cost=0)), b'{"sequence":1,"call":"' + TAG1.encode() + b'","call":"' + TAG1.encode() + b'"}\n')
        self.assert_generic_failure()
        # Even an otherwise unrelated ledger row is parsed strictly.
        self.write(jsonl(obj(run=RUN, cost=0), '{"run":"other","x":1,"x":2}'), b"")
        self.assert_generic_failure()
        # The duplicate-key hook applies recursively too.
        self.write(jsonl('{"run":"offline-test","cost":0,"nested":{"a":1,"a":2}}'), b"")
        self.assert_generic_failure()

    def test_bad_relevant_costs_are_rejected(self) -> None:
        for cost in ("null", '"1"', "true", "NaN", "Infinity", "-0.01", "1e1001"):
            with self.subTest(cost=cost):
                self.write(jsonl('{"run":"offline-test","cost":' + cost + "}"), b"")
                self.assert_generic_failure()
        self.write(b'{"run":"offline-test"}\n', b"")
        self.assert_generic_failure()

    def test_malformed_lines_and_missing_files_are_generic(self) -> None:
        self.write(b'{broken\n', b"")
        self.assert_generic_failure()
        self.write(jsonl(obj(run=RUN, cost=0)), b"not-json\n")
        self.assert_generic_failure()
        self.write(jsonl(obj(run=RUN, cost=0)), b"")
        self.audit.unlink()
        self.assert_generic_failure()

    def test_unreadable_and_non_regular_files_are_generic(self) -> None:
        self.write(jsonl(obj(run=RUN, cost=0)), b"")
        with patch.object(cost_snapshot.os, "open", side_effect=PermissionError("sensitive path")):
            self.assert_generic_failure()
        self.ledger.unlink()
        self.ledger.mkdir()
        self.assert_generic_failure()

    def test_limits_fail_closed(self) -> None:
        self.write(jsonl(obj(run=RUN, cost=0)), b"")
        with patch.object(cost_snapshot, "MAX_FILE_BYTES", 5):
            self.assert_generic_failure()
        self.write(jsonl(obj(run=RUN, cost=0)), b"")
        with patch.object(cost_snapshot, "MAX_LINE_BYTES", 5):
            self.assert_generic_failure()
        self.write(jsonl(obj(run=RUN, cost=0), obj(run="irrelevant", cost=0)), b"")
        with patch.object(cost_snapshot, "MAX_RECORDS", 1):
            self.assert_generic_failure()
        self.write(b'{"run":"offline-test","cost":123}\n', b"")
        with patch.object(cost_snapshot, "MAX_DECIMAL_DIGITS", 2):
            self.assert_generic_failure()

    def test_cli_success_is_json_and_failure_does_not_echo_payload_or_arguments(self) -> None:
        self.write(jsonl(obj(run=RUN, cost=0)), b"")
        script = Path(cost_snapshot.__file__)
        good = subprocess.run(
            [sys.executable, str(script), "--ledger", str(self.ledger), "--audit", str(self.audit), "--run", RUN],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(good.returncode, 0)
        self.assertEqual(json.loads(good.stdout), {"spent": "0", "attempts": 0, "pending": 0, "records": 1})
        self.assertEqual(good.stderr, "")

        marker = "PROMPT_OR_KEY_DO_NOT_ECHO"
        self.write(jsonl('{"run":"offline-test","cost":"' + marker + '"}'), b"")
        bad_input = subprocess.run(
            [sys.executable, str(script), "--ledger", str(self.ledger), "--audit", str(self.audit), "--run", RUN],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(bad_input.returncode, 0)
        self.assertEqual(bad_input.stdout, "")
        self.assertEqual(bad_input.stderr.strip(), "snapshot failed")
        self.assertNotIn(marker, bad_input.stderr + bad_input.stdout)

        bad_args = subprocess.run(
            [sys.executable, str(script), "--run", RUN, "--credential", marker],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(bad_args.returncode, 0)
        self.assertEqual(bad_args.stderr.strip(), "snapshot failed")
        self.assertNotIn(marker, bad_args.stderr + bad_args.stdout)


if __name__ == "__main__":
    unittest.main()
