from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("proxy_launcher", ROOT / "proxy_launcher.py")
launcher = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(launcher)


class ProxyLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = self.root / "master.key"
        self.key.write_bytes(b"FAKE_INITIAL_GATEWAY_KEY")
        self.key.chmod(0o600)

    def test_open_descriptor_survives_path_replacement(self) -> None:
        fd = launcher.open_master_key(str(self.key))
        try:
            moved = self.root / "opened-original"
            os.replace(self.key, moved)
            self.key.write_bytes(b"FAKE_REPLACEMENT_KEY")
            self.key.chmod(0o600)
            self.assertEqual(os.read(fd, 4097), b"FAKE_INITIAL_GATEWAY_KEY")
        finally:
            os.close(fd)

    def test_symlink_and_fifo_are_rejected_without_read_or_block(self) -> None:
        target = self.root / "target"
        target.write_bytes(b"FAKE_TARGET_KEY")
        target.chmod(0o600)
        self.key.unlink()
        self.key.symlink_to(target)
        with self.assertRaises(launcher.KeyUnavailable):
            launcher.open_master_key(str(self.key))
        self.assertEqual(target.read_bytes(), b"FAKE_TARGET_KEY")

        self.key.unlink()
        os.mkfifo(self.key)
        started = time.monotonic()
        with self.assertRaises(launcher.KeyUnavailable):
            launcher.open_master_key(str(self.key))
        self.assertLess(time.monotonic() - started, 1)

    def test_missing_key_is_refused_and_not_created(self) -> None:
        self.key.unlink()
        with self.assertRaises(launcher.KeyUnavailable):
            launcher.open_master_key(str(self.key))
        self.assertFalse(self.key.exists())

    def test_missing_ledger_is_created_atomically_and_existing_data_is_preserved(self) -> None:
        ledger = self.root / "usage.jsonl"
        launcher.ensure_ledger(str(ledger))
        self.assertEqual(ledger.read_bytes(), b"")
        self.assertEqual(ledger.stat().st_mode & 0o777, 0o600)
        ledger.write_text('{"run":"fictive","cost":0}\n')
        before = ledger.read_bytes()
        launcher.ensure_ledger(str(ledger))
        self.assertEqual(ledger.read_bytes(), before)

    def test_unsafe_ledger_types_and_permissions_are_rejected_without_modification(self) -> None:
        ledger = self.root / "usage.jsonl"
        ledger.write_text("keep\n")
        ledger.chmod(0o666)
        before = ledger.read_bytes()
        with self.assertRaises(launcher.LedgerUnavailable):
            launcher.ensure_ledger(str(ledger))
        self.assertEqual(ledger.read_bytes(), before)

        ledger.unlink()
        target = self.root / "target-ledger"
        target.write_text("keep\n")
        target.chmod(0o600)
        ledger.symlink_to(target)
        with self.assertRaises(launcher.LedgerUnavailable):
            launcher.ensure_ledger(str(ledger))
        self.assertEqual(target.read_text(), "keep\n")

        ledger.unlink()
        os.mkfifo(ledger)
        started = time.monotonic()
        with self.assertRaises(launcher.LedgerUnavailable):
            launcher.ensure_ledger(str(ledger))
        self.assertLess(time.monotonic() - started, 1)

    def test_pythonpath_sitecustomize_and_host_environment_do_not_reach_relay(self) -> None:
        site_dir = self.root / "site"
        site_dir.mkdir()
        sentinel = self.root / "sitecustomize-ran"
        (site_dir / "sitecustomize.py").write_text(
            "from pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('ran')\n"
        )
        fake_relay = self.root / "fake_relay.py"
        key_capture = self.root / "captured-key"
        env_capture = self.root / "captured-env.json"
        fake_relay.write_text(
            "import json, os, sys\n"
            "open(sys.argv[1], 'wb').write(os.read(3, 4097))\n"
            "open(" + repr(str(env_capture)) + ", 'w').write(json.dumps({'pythonpath':'PYTHONPATH' in os.environ,"
            "'sentinel':'FAKE_HOST_SENTINEL' in os.environ}))\n"
        )
        proxy_env = {name: f"test-{name.lower()}" for name in launcher.PROXY_ENV}
        proxy_env.update({
            "SA_PROXY_PORT": "12345",
            "SA_PROXY_TIMEOUT": "5",
            "SA_PROXY_BUDGET": "1.0",
            "SA_PROXY_LEDGER_WAIT": "0",
            "SA_PROXY_AUDIT": str(self.root / "audit.jsonl"),
            "SA_PROXY_LEDGER": str(self.root / "usage.jsonl"),
        })
        env = dict(os.environ, **proxy_env, PYTHONPATH=str(site_dir), FAKE_HOST_SENTINEL="must-not-reach")
        proc = subprocess.run(
            [sys.executable, "-E", "-s", "-S", str(ROOT / "proxy_launcher.py"), str(self.key),
             str(fake_relay), str(key_capture)],
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(sentinel.exists())
        self.assertEqual(key_capture.read_bytes(), b"FAKE_INITIAL_GATEWAY_KEY")
        self.assertEqual(json.loads(env_capture.read_text()), {"pythonpath": False, "sentinel": False})


if __name__ == "__main__":
    unittest.main()
