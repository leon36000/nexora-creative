import json
import os
import shlex
import sys
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'sous-agent.sh'

class TestRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.work = root / 'work \"fictif\"'; self.work.mkdir()
        self.prompt = root / 'prompt.txt'; self.prompt.write_text('donnée fictive')
        self.state = root / ('s' * 90); self.state.mkdir()
        (self.state / 'usage.jsonl').write_text(''); (self.state / 'usage.jsonl').chmod(0o600)
        self.home = root / 'config'; self.home.mkdir()
        (self.home / 'master.key').write_text('FAKE_TEST_KEY'); (self.home / 'master.key').chmod(0o600)
        self.bin = root / 'bin'; self.bin.mkdir()
        self.stub('curl', '#!/bin/sh\n[ "${1:-}" = "--noproxy" ] && [ "${2:-}" = "*" ] || exit 9\nprintf 200\n')
        self.stub('claude', '#!/bin/sh\nexit 0\n')
        self.stub('python3', '''#!/bin/sh
case "$*" in *'os.kill(p,0)'*)
 if [ "${FAKE_DENY_PROBE:-0}" = 1 ]; then
  for f in "$SA_STATE"/runs/*/pid; do
   [ -f "$f" ] || continue
   for arg in "$@"; do [ "$arg" = "$(cat "$f")" ] && exit 2; done
  done
 fi
 if [ "${FAKE_DENY_SUPERVISOR:-0}" = 1 ]; then
  for f in "$SA_STATE"/runs/*/superviseur.pid; do
   [ -f "$f" ] || continue
   for arg in "$@"; do [ "$arg" = "$(cat "$f")" ] && exit 2; done
  done
 fi;; esac
case "$*" in *pidfd_send_signal*) if [ "${FAKE_DENY_PIDFD:-0}" = 1 ]; then echo refused >> "$FAKE_SIGNAL_LOG"; exit 2; fi;; esac
exec /usr/bin/python3 "$@"
''')
        self.stub('docker', '''#!/bin/sh
if [ "${FAKE_DOCKER_MISMATCH:-0}" = 1 ]; then echo invalid; else printf 'true|%s|127.0.0.1:%s,\\n' "$FAKE_IMAGE" "${SA_PORT:-4410}"; fi
''')
        self.stub('socat', '''#!/usr/bin/python3
import os, socket, sys, time
if os.environ.get('FAKE_BAD_SOCKET') == '1': sys.exit(1)
path = sys.argv[1].split(':', 1)[1].split(',', 1)[0]
s = socket.socket(socket.AF_UNIX); s.bind(path); s.listen()
time.sleep(30)
''')
        self.stub('bwrap', '''#!/usr/bin/python3
import json, os, sys, time
from pathlib import Path
from decimal import Decimal
Path(os.environ['FAKE_WORK']).joinpath('bwrap-called').write_text('yes')
key = 'FAKE_TEST_KEY'
if key in sys.argv or os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('SA_PROXY_KEY'):
    sys.exit(19)
if '--clearenv' not in sys.argv or 'nexora-sandbox' not in sys.argv:
    sys.exit(21)
if 'donnée fictive' in sys.argv or sys.stdin.read() != 'donnée fictive':
    sys.exit(20)
header = sys.argv[sys.argv.index('ANTHROPIC_CUSTOM_HEADERS') + 1]
run = header.split(': ', 1)[1]
audit = Path(os.environ['SA_STATE']) / 'runs' / run / 'proxy-audit.jsonl'
nonce = '0123456789abcdef'
tags = [f'{run}--p{nonce}--c1']
if os.environ.get('FAKE_MISSING_LEDGER_ENTRY') == '1': tags.append(f'{run}--p{nonce}--c2')
if os.environ.get('FAKE_NO_AUDIT') != '1':
    with audit.open('a') as f:
        for sequence, tag in enumerate(tags, 1):
            f.write(json.dumps({'sequence':sequence, 'call':tag}) + '\\n')
if os.environ.get('FAKE_NO_LOG') != '1':
    cost = 'null' if os.environ.get('FAKE_UNKNOWN_COST') == '1' else format(Decimal(os.environ.get('FAKE_COST', '0.001')), 'f')
    with (Path(os.environ['SA_STATE']) / 'usage.jsonl').open('a') as f:
        f.write(json.dumps({'run': tags[0], 'in': 1, 'out': 1})[:-1] + ',"cost":' + cost + '}\\n')
if os.environ.get('FAKE_BARRIER'):
    marker = Path(os.environ['FAKE_BARRIER'])
    marker.with_suffix('.pid').write_text(str(os.getpid()))
    while not marker.exists(): time.sleep(0.05)
elif os.environ.get('FAKE_STALL') == '1': time.sleep(12)
if os.environ.get('FAKE_EXIT_125') == '1': sys.exit(125)
if os.environ.get('FAKE_BAD_RESULT') == '1':
    print(json.dumps({'type':'result','subtype':'test'}))
else:
    print(json.dumps({'type':'result','is_error':os.environ.get('FAKE_RESULT_FAIL') == '1','subtype':'test','num_turns':int(os.environ.get('FAKE_NUM_TURNS','1'))}))
''')
        self.env = dict(os.environ, SA_HOME=str(self.home), SA_STATE=str(self.state),
                        PATH=str(self.bin) + os.pathsep + os.environ['PATH'], SA_TIMEOUT='15', FAKE_WORK=str(self.work),
                        SA_LEDGER_WAIT='0.3',
                        FAKE_IMAGE='ghcr.io/berriai/litellm@sha256:7294b90f868c5c38c99b83021c7ba46f9b439e95f8e32964c925c7d2563a03f7')

    def stub(self, name, source):
        p = self.bin / name; p.write_text(source.replace("/usr/bin/python3", shlex.quote(sys.executable))); p.chmod(0o755)

    def call(self, *flags, env=None, timeout=15):
        return subprocess.run([str(SCRIPT), *flags, 'deepseek', str(self.prompt), str(self.work), '2', '0.1'],
                              env=env or self.env, text=True, capture_output=True, timeout=timeout)

    def test_wait_mode_short_socket_and_key_not_in_arguments(self):
        r = self.call('-w')
        self.assertEqual(r.returncode, 0, r.stderr)
        out = Path(r.stdout.splitlines()[0])
        self.assertTrue((out / 'done').exists())
        self.assertTrue((out / 'summary.txt').read_text().startswith('OK:'))
        self.assertNotIn('FAKE_TEST_KEY', r.stdout + r.stderr)
        self.assertGreater(len(str(self.state)), 100)

    def test_refused_signal_stops_proxy_cooperatively(self):
        bash_env = self.tmp_path() / 'deny-signals.sh'
        signal_log = self.tmp_path() / 'signals.log'
        bash_env.write_text('kill() { if [ "${1:-}" = "-0" ]; then builtin kill "$@"; else echo refused >> "$FAKE_SIGNAL_LOG"; return 1; fi; }\n')
        r = self.call('-w', env=dict(self.env, BASH_ENV=str(bash_env), FAKE_SIGNAL_LOG=str(signal_log)))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = Path(r.stdout.splitlines()[0])
        self.assertTrue((out / 'proxy-stop').exists())
        self.assertFalse(signal_log.exists())
        self.assertFalse((out / 'proxy-stop-error').exists())

    def tmp_path(self):
        return Path(self.tmp.name)

    def release_barrier(self, marker):
        marker.touch()
        pidfile = marker.with_suffix('.pid')
        pidfiles = list(self.state.glob('runs/*/pid'))
        if pidfile.exists(): pidfiles.append(pidfile)
        for path in pidfiles:
            pid = int(path.read_text())
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
                except FileNotFoundError:
                    break
                if state == 'Z': break
                time.sleep(0.05)
            else:
                self.fail('le faux client ne confirme pas sa sortie après libération')

    def test_refused_client_stop_is_bounded_and_reported(self):
        signal_log = self.tmp_path() / 'signals.log'
        marker = self.tmp_path() / 'release-client'
        debut = time.monotonic()
        try:
            r = self.call('-w', env=dict(self.env, FAKE_SIGNAL_LOG=str(signal_log), FAKE_DENY_PIDFD='1',
                                         FAKE_BARRIER=str(marker), FAKE_COST='0.2'), timeout=30)
            self.assertLess(time.monotonic() - debut, 25)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('FAIL:plafond_budget', r.stdout)
            self.assertIn('arret_client=non_confirme', r.stdout)
            self.assertTrue(signal_log.exists())
        finally:
            self.release_barrier(marker)

    def test_timeout_with_refused_signal_returns_without_claiming_exit(self):
        self.stub('timeout', '#!/bin/sh\nshift 2\nexec "$@"\n')
        marker = self.tmp_path() / 'release-client'
        signal_log = self.tmp_path() / 'signals.log'
        debut = time.monotonic()
        try:
            r = self.call('-w', env=dict(self.env, FAKE_SIGNAL_LOG=str(signal_log), FAKE_DENY_PIDFD='1',
                                         FAKE_BARRIER=str(marker), SA_TIMEOUT='2'), timeout=30)
            self.assertLess(time.monotonic() - debut, 25)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('FAIL:timeout', r.stdout)
            self.assertIn('arret_client=non_confirme', r.stdout)
            self.assertTrue(signal_log.exists())
        finally:
            self.release_barrier(marker)

    def test_inconclusive_signal_zero_keeps_monitoring_until_deadline(self):
        self.stub('timeout', '#!/bin/sh\nshift 2\nexec "$@"\n')
        marker = self.tmp_path() / 'release-client'
        signal_log = self.tmp_path() / 'signals.log'
        debut = time.monotonic()
        try:
            r = self.call('-w', env=dict(self.env, FAKE_DENY_PROBE='1', FAKE_DENY_PIDFD='1',
                                         FAKE_SIGNAL_LOG=str(signal_log), FAKE_BARRIER=str(marker),
                                         SA_TIMEOUT='2'), timeout=30)
            self.assertGreaterEqual(time.monotonic() - debut, 1.5)
            self.assertLess(time.monotonic() - debut, 25)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('FAIL:timeout', r.stdout)
            self.assertIn('arret_client=non_confirme', r.stdout)
            self.assertTrue(signal_log.exists())
        finally:
            self.release_barrier(marker)

    def test_unresponsive_proxy_is_reported_without_unbounded_wait(self):
        runtime = self.tmp_path() / 'runtime'
        runtime.mkdir()
        for name in ('sous-agent.sh', 'lib.sh', 'proxy_launcher.py', 'cost_snapshot.py'):
            shutil.copy2(ROOT / name, runtime / name)
        (runtime / 'sa_proxy.py').write_text(
            "import socket,sys,time\n"
            "s=socket.socket(socket.AF_UNIX); s.bind(sys.argv[1]); s.listen(); time.sleep(8)\n"
        )
        bash_env = self.tmp_path() / 'deny-signals.sh'
        signal_log = self.tmp_path() / 'signals.log'
        bash_env.write_text('kill() { if [ "${1:-}" = "-0" ]; then builtin kill "$@"; else echo refused >> "$FAKE_SIGNAL_LOG"; return 1; fi; }\n')
        debut = time.monotonic()
        env = dict(self.env, BASH_ENV=str(bash_env), FAKE_SIGNAL_LOG=str(signal_log))
        r = subprocess.run([str(runtime / 'sous-agent.sh'), '-w', 'deepseek', str(self.prompt), str(self.work), '2', '0.1'],
                           env=env, text=True, capture_output=True, timeout=15)
        self.assertLess(time.monotonic() - debut, 15)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('arret_relais=non_confirme', r.stdout)
        self.assertFalse(signal_log.exists())

    def test_exit_125_is_distinct_from_unconfirmed_stop(self):
        r = self.call('-w', env=dict(self.env, FAKE_EXIT_125='1'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('arret_client=confirme', r.stdout)
        self.assertNotIn('arret_client=non_confirme', r.stdout)

    def test_summary_identifies_client_counter_and_gateway_cost(self):
        r = self.call('-w', env=dict(self.env, FAKE_NUM_TURNS='18'))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('num_turns_client=18', r.stdout)
        self.assertIn('source_cout=estimation_passerelle', r.stdout)
        self.assertIn('1req', r.stdout)
        self.assertNotIn(' tours=', r.stdout)

    def test_failure_result_returns_nonzero(self):
        r = self.call('-w', env=dict(self.env, FAKE_RESULT_FAIL='1'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:', r.stdout)

    def test_background_survives_caller_and_finishes(self):
        r = self.call()
        self.assertEqual(r.returncode, 0, r.stderr)
        out = Path(r.stdout.splitlines()[0])
        end = time.monotonic() + 12
        while not (out / 'done').exists() and time.monotonic() < end:
            time.sleep(0.1)
        self.assertTrue((out / 'done').exists(), (out / 'lancement.log').read_text())
        self.assertTrue((out / 'summary.txt').read_text().startswith('OK:'))
        meta = json.loads((out / 'meta.json').read_text())
        self.assertEqual(meta['run'], out.name)

    def test_missing_or_unknown_ledger_cost_fails_without_fake_zero(self):
        for variable in ('FAKE_NO_LOG', 'FAKE_UNKNOWN_COST'):
            with self.subTest(variable=variable):
                r = self.call('-w', env=dict(self.env, **{variable: '1'}))
                self.assertNotEqual(r.returncode, 0)
                self.assertIn('FAIL:cout_inconnu', r.stdout)
                self.assertIn('cout=inconnu', r.stdout)

    def test_missing_error_flag_is_not_success(self):
        r = self.call('-w', env=dict(self.env, FAKE_BAD_RESULT='1'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:', r.stdout)

    def test_small_nonzero_cost_is_not_displayed_as_zero(self):
        r = self.call('-w', env=dict(self.env, FAKE_COST='0.0000001'))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('cout=<$0.00001', r.stdout)

    def test_fewer_cost_entries_than_forwarded_calls_is_unknown(self):
        r = self.call('-w', env=dict(self.env, FAKE_MISSING_LEDGER_ENTRY='1'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:cout_inconnu', r.stdout)

    def test_final_cost_at_or_above_budget_is_not_reported_successful(self):
        r = self.call('-w', env=dict(self.env, FAKE_COST='0.11'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:plafond_budget', r.stdout)

    def test_final_cost_just_over_budget_is_not_rounded_below_limit(self):
        r = self.call('-w', env=dict(self.env, FAKE_COST='0.1000000000000000000000000001'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:plafond_budget', r.stdout)
        self.assertIn('cout_exact=0.1000000000000000000000000001', r.stdout)

    def test_success_result_without_any_audited_attempt_is_unknown(self):
        r = self.call('-w', env=dict(self.env, FAKE_NO_AUDIT='1'))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:cout_inconnu', r.stdout)

    def test_unreconciled_call_wait_is_bounded(self):
        started = time.monotonic()
        r = self.call('-w', env=dict(self.env, FAKE_NO_LOG='1'))
        elapsed = time.monotonic() - started
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:cout_inconnu', r.stdout)
        self.assertGreaterEqual(elapsed, 0.25)
        self.assertLess(elapsed, 3)

    def test_missing_socket_fails_before_model_launch(self):
        self.stub('python3', '#!/bin/sh\ncase "$*" in *sa_proxy.py*) exit 1;; *) exec /usr/bin/python3 "$@";; esac\n')
        r = self.call('-w')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:pont_indisponible', r.stdout)
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_run_id_longer_than_snapshot_limit_is_rejected_early(self):
        r = subprocess.run(
            [str(SCRIPT), '--runner-internal-run-id', 'r' * 129, '-w', 'deepseek', str(self.prompt), str(self.work), '2', '0.1'],
            env=self.env, text=True, capture_output=True, timeout=15,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('identifiant de run invalide', r.stderr)
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_background_completed_failure_returns_nonzero(self):
        key = self.home / 'master.key'; key.unlink()
        target = self.home.parent / 'target'; target.write_text('')
        key.symlink_to(target)
        r = self.call()
        self.assertNotEqual(r.returncode, 0)
        out = Path(r.stdout.splitlines()[0])
        self.assertTrue((out / 'done').exists())
        self.assertTrue((out / 'summary.txt').read_text().startswith('FAIL:cle_indisponible'))

    def test_background_unconfirmed_start_says_not_to_relaunch_and_finishes(self):
        self.stub('curl', '#!/bin/sh\nsleep 3\nprintf 200\n')
        r = self.call()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('démarrage non confirmé', r.stderr)
        self.assertIn('ne pas relancer', r.stderr)
        out = Path(r.stdout.splitlines()[0])
        end = time.monotonic() + 12
        while not (out / 'done').exists() and time.monotonic() < end:
            time.sleep(0.1)
        self.assertTrue((out / 'done').exists())
        self.assertTrue((out / 'summary.txt').read_text().startswith('OK:'))

    def test_background_inconclusive_signal_zero_warns_against_retry(self):
        self.stub('curl', '#!/bin/sh\nsleep 3\nprintf 200\n')
        r = self.call(env=dict(self.env, FAKE_DENY_SUPERVISOR='1'))
        self.assertEqual(r.returncode, 2)
        self.assertIn('démarrage non confirmé', r.stderr)
        self.assertIn('ne pas relancer', r.stderr)
        out = Path(r.stdout.splitlines()[0])
        end = time.monotonic() + 12
        while not (out / 'done').exists() and time.monotonic() < end: time.sleep(0.1)
        self.assertTrue((out / 'done').exists())

    def test_secret_mount_or_ancestor_is_refused_without_launch(self):
        for mount in (self.home, self.home.parent):
            with self.subTest(mount=mount):
                r = self.call('-w', env=dict(self.env, SA_EXTRA_RO=str(mount)))
                self.assertNotEqual(r.returncode, 0)
                self.assertFalse((self.work / 'bwrap-called').exists())
        link = self.work.parent / 'secret-link'; link.symlink_to(self.home, target_is_directory=True)
        r = self.call('-w', env=dict(self.env, SA_EXTRA_RO=str(link)))
        self.assertNotEqual(r.returncode, 0)

    def test_untrusted_gateway_is_refused_before_launch(self):
        r = self.call('-w', env=dict(self.env, FAKE_DOCKER_MISMATCH='1'))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_symlinked_master_key_is_refused_without_modifying_target(self):
        key = self.home / 'master.key'; key.unlink()
        target = self.home.parent / 'target'; target.write_text('')
        key.symlink_to(target)
        r = self.call('-w')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:cle_indisponible', r.stdout)
        self.assertEqual(target.read_text(), '')
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_missing_master_key_is_refused_without_recreation(self):
        key = self.home / 'master.key'; key.unlink()
        r = self.call('-w')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:cle_indisponible', r.stdout)
        self.assertFalse(key.exists())
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_fifo_master_key_is_refused_without_blocking_or_model_launch(self):
        key = self.home / 'master.key'; key.unlink(); os.mkfifo(key)
        started = time.monotonic()
        r = self.call('-w')
        elapsed = time.monotonic() - started
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:cle_indisponible', r.stdout)
        self.assertLess(elapsed, 3)
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_result_directory_cannot_be_mounted_into_agent_workspace(self):
        out = self.work / 'results'
        r = self.call('-w', env=dict(self.env, SA_OUT=str(out)))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(out.exists())
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_broad_temp_directory_cannot_be_mounted(self):
        r = self.call('-w', env=dict(self.env, SA_EXTRA_RO='/tmp'))
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.work / 'bwrap-called').exists())

    def test_existing_result_is_not_overwritten(self):
        existing = self.state / 'existing'; existing.mkdir()
        (existing / 'summary.txt').write_text('préservé')
        r = self.call('-w', env=dict(self.env, SA_OUT=str(existing)))
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((existing / 'summary.txt').read_text(), 'préservé')

    def test_sa_internal_run_id_environment_cannot_bypass_existing_output_guard(self):
        runs = self.state / 'runs'; runs.mkdir(exist_ok=True)
        existing = runs / 'existing-run'; existing.mkdir(); existing.chmod(0o700)
        summary = existing / 'summary.txt'; summary.write_text('PRESERVE-ME')
        mode_before = existing.stat().st_mode & 0o777
        r = self.call('-w', env=dict(self.env, SA_INTERNAL_RUN_ID='existing-run', SA_OUT=str(existing)))
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(summary.read_text(), 'PRESERVE-ME')
        self.assertEqual(existing.stat().st_mode & 0o777, mode_before)

    def test_forged_internal_argument_cannot_reuse_existing_output(self):
        runs = self.state / 'runs'; runs.mkdir(exist_ok=True)
        existing = runs / 'existing-run'; existing.mkdir()
        summary = existing / 'summary.txt'; summary.write_text('PRESERVE-ME')
        r = subprocess.run(
            [str(SCRIPT), '--runner-internal-run-id', 'existing-run', '-w', 'deepseek', str(self.prompt), str(self.work), '2', '0.1'],
            env=dict(self.env, SA_OUT=str(existing)), text=True, capture_output=True, timeout=15,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('reprise interne invalide', r.stderr)
        self.assertEqual(summary.read_text(), 'PRESERVE-ME')

    def test_internal_argument_cannot_overwrite_even_with_forged_handoff(self):
        runs = self.state / 'runs'; runs.mkdir(exist_ok=True)
        existing = runs / 'existing-run'; existing.mkdir(); existing.chmod(0o700)
        meta = {'run': 'existing-run', 'alias': 'eco-deepseek', 'workdir': str(self.work.resolve()),
                'max_turns': 2, 'budget_usd': 0.1}
        (existing / 'meta.json').write_text(json.dumps(meta)); (existing / 'meta.json').chmod(0o600)
        (existing / '.runner-handoff').write_text('existing-run\n'); (existing / '.runner-handoff').chmod(0o600)
        summary = existing / 'summary.txt'; summary.write_text('PRESERVE-ME')
        r = subprocess.run(
            [str(SCRIPT), '--runner-internal-run-id', 'existing-run', '-w', 'deepseek', str(self.prompt), str(self.work), '2', '0.1'],
            env=dict(self.env, SA_OUT=str(existing)), text=True, capture_output=True, timeout=15,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('résultat interne déjà présent', r.stderr)
        self.assertEqual(summary.read_text(), 'PRESERVE-ME')
        self.assertTrue((existing / 'meta.json').exists())

    def test_sa_out_under_ssh_is_rejected_before_writes_or_chmod(self):
        ssh = self.home / '.ssh'; ssh.mkdir(); (ssh / 'keep').write_text('PRESERVE-ME'); ssh.chmod(0o700)
        mode_before = ssh.stat().st_mode & 0o777
        out = ssh / 'new-run'
        r = self.call('-w', env=dict(self.env, SA_OUT=str(out)))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('dossier de résultats protégé', r.stderr)
        self.assertFalse(out.exists())
        self.assertEqual((ssh / 'keep').read_text(), 'PRESERVE-ME')
        self.assertEqual(ssh.stat().st_mode & 0o777, mode_before)

    def test_only_child_paths_under_state_runs_or_lots_are_allowed(self):
        (self.state / 'runs').mkdir(parents=True, exist_ok=True)
        cases = (self.state, self.state / 'runs', self.state / 'lots', self.state / 'usage.jsonl')
        for out in cases:
            with self.subTest(out=out):
                before_exists = out.exists()
                r = self.call('-w', env=dict(self.env, SA_OUT=str(out)))
                self.assertNotEqual(r.returncode, 0)
                self.assertIn('dossier de résultats protégé', r.stderr)
                self.assertFalse((self.work / 'bwrap-called').exists())
                if not before_exists:
                    self.assertFalse(out.exists())

    def test_missing_usage_ledger_is_created_safely_on_first_run(self):
        ledger = self.state / 'usage.jsonl'; ledger.unlink()
        r = self.call('-w')
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue(ledger.is_file())
        self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
        self.assertTrue((self.work / 'bwrap-called').exists())

    def test_insecure_usage_ledger_is_rejected_before_agent_launch(self):
        ledger = self.state / 'usage.jsonl'; ledger.chmod(0o666)
        before = ledger.read_text()
        r = self.call('-w')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('FAIL:journal_indisponible', r.stdout)
        self.assertEqual(ledger.read_text(), before)
        self.assertEqual(ledger.stat().st_mode & 0o777, 0o666)
        self.assertFalse((self.work / 'bwrap-called').exists())

if __name__ == '__main__':
    unittest.main()
