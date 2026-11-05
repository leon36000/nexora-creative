#!/usr/bin/env python3
"""Tests offline du démarrage et de l’activation (Docker et HTTP simulés)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
SCRIPTS = BASE / "outils" / "sous-agents"
IMAGE = re.search(r'^SA_IMAGE="([^"]+)"', (SCRIPTS / "lib.sh").read_text(), re.M).group(1)
ALIASES = re.findall(r"^\s*-\s*model_name:\s*([A-Za-z0-9._-]+)",
                     (SCRIPTS / "litellm" / "config.yaml").read_text(), re.M)
FAKE_MASTER = "test-master-secret-only"
FAKE_DEEPINFRA = "test-deepinfra-secret-only"
FAKE_OPENROUTER = "test-openrouter-secret-only"


class FakeHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send_json(self, status, document):
        body = json.dumps(document).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.server.records.append(("GET", self.path, self.headers.get("Authorization"), None))
        if self.path == "/health/liveliness":
            self.send_json(self.server.health_status, {"status": "ok"})
        elif self.path == "/v1/models":
            if self.headers.get("Authorization") != f"Bearer {FAKE_MASTER}":
                self.send_json(401, {"error": "unauthorized"})
            else:
                self.send_json(200, {"data": [{"id": alias} for alias in ALIASES]})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.server.records.append(("POST", self.path, self.headers.get("Authorization"), body))
        if (self.path == "/v1/chat/completions"
                and self.headers.get("Authorization") == f"Bearer {FAKE_MASTER}"):
            self.send_json(200, {"choices": [{"message": {"content": "OK"}}]})
        else:
            self.send_json(404, {"error": "not found"})


def serve(health_status=200):
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
    server.health_status = health_status
    server.records = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="harness-test-", dir=BASE)
        self.root = Path(self.tmp.name)
        self.state = self.root / "docker-state"
        self.state.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.docker_log = self.root / "docker.log"
        self.fake_docker = self.bin / "docker"
        self.fake_docker.write_text(
            """#!/bin/sh
printf '%s\\n' "$*" >> "$MOCK_DOCKER_LOG"
cmd=${1:-}
case "$cmd" in
  inspect)
    if [ ! -f "$MOCK_DOCKER_STATE/exists" ]; then exit 1; fi
    if [ "${2:-}" != "--format" ]; then exit 0; fi
    fmt=${3:-}
    case "$fmt" in
      '{{.Config.Image}}') printf '%s' "$MOCK_IMAGE" ;;
      *HostPort*) printf '%s' "$MOCK_PORT" ;;
      '{{.State.Status}}') cat "$MOCK_DOCKER_STATE/status" ;;
      *) exit 2 ;;
    esac ;;
  info) exit 0 ;;
  run)
    expected=$(cat "$MOCK_MASTER_KEY_FILE")
    if [ "${LITELLM_MASTER_KEY:-}" != "$expected" ]; then echo "master key mismatch" >&2; exit 3; fi
    touch "$MOCK_DOCKER_STATE/master-key-validated" "$MOCK_DOCKER_STATE/exists"
    printf 'running\\n' > "$MOCK_DOCKER_STATE/status" ;;
  start) printf 'running\\n' > "$MOCK_DOCKER_STATE/status" ;;
  stop) printf 'exited\\n' > "$MOCK_DOCKER_STATE/status" ;;
  restart) printf 'running\\n' > "$MOCK_DOCKER_STATE/status" ;;
  logs) printf 'fake logs\\n' ;;
  rm) rm -f "$MOCK_DOCKER_STATE/exists" "$MOCK_DOCKER_STATE/status" ;;
  *) echo "unexpected docker command" >&2; exit 2 ;;
esac
""",
            encoding="utf-8",
        )
        self.fake_docker.chmod(0o755)
        self.home = self.root / "home"
        self.home.mkdir()
        self.sa_home = self.root / "config"
        self.sa_home.mkdir()
        (self.sa_home / "master.key").write_text(FAKE_MASTER + "\n")
        (self.sa_home / "master.key").chmod(0o600)
        self.sa_state = self.root / "usage"
        self.sa_state.mkdir()
        self.keyfile = self.root / "fake-provider-keys.env"
        self.keyfile.write_text(f"Deepinfra: {FAKE_DEEPINFRA}\nOpenrouter: {FAKE_OPENROUTER}\n")
        self.server, self.thread = serve()
        self.env = {
            **os.environ,
            "PATH": str(self.bin) + os.pathsep + os.environ.get("PATH", ""),
            "HOME": str(self.home),
            "SA_HOME": str(self.sa_home),
            "SA_STATE": str(self.sa_state),
            "SA_KEYFILE": str(self.keyfile),
            "SA_PORT": str(self.server.server_port),
            "SA_HEALTH_CHECKS": "1",
            "SA_HEALTH_DELAY": "0",
            "MOCK_DOCKER_LOG": str(self.docker_log),
            "MOCK_DOCKER_STATE": str(self.state),
            "MOCK_MASTER_KEY_FILE": str(self.sa_home / "master.key"),
            "MOCK_IMAGE": IMAGE,
            "MOCK_PORT": f"127.0.0.1:{self.server.server_port}",
        }

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def set_container(self, status="running", image=None, port=None):
        (self.state / "exists").touch()
        (self.state / "status").write_text(status)
        if image is not None:
            self.env["MOCK_IMAGE"] = image
        if port is not None:
            self.env["MOCK_PORT"] = port

    def docker_commands(self):
        return self.docker_log.read_text().splitlines() if self.docker_log.exists() else []

    def call(self, script, *args):
        return subprocess.run([str(script), *args], env=self.env, text=True,
                              capture_output=True, timeout=8)

    def test_default_activation_tests_aliases_and_local_mode_is_explicit(self):
        result = self.call(SCRIPTS / "activer.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("peut entraîner des coûts", result.stdout)
        self.assertNotIn(FAKE_MASTER, result.stdout + result.stderr)
        self.assertNotIn(FAKE_DEEPINFRA, result.stdout + result.stderr)
        self.assertNotIn(FAKE_OPENROUTER, result.stdout + result.stderr)
        posts = [r for r in self.server.records if r[0] == "POST"]
        self.assertEqual(len(posts), len(ALIASES))
        self.assertTrue(any(r[0] == "GET" and r[1] == "/v1/models" for r in self.server.records))
        self.assertIn("run", [cmd.split()[0] for cmd in self.docker_commands()])
        self.assertNotIn(FAKE_DEEPINFRA, self.docker_log.read_text())
        self.assertNotIn(FAKE_OPENROUTER, self.docker_log.read_text())
        self.assertNotIn(FAKE_MASTER, self.docker_log.read_text())
        self.assertTrue((self.state / "master-key-validated").exists())
        for _method, path, authorization, raw in posts:
            request = json.loads(raw)
            self.assertEqual(path, "/v1/chat/completions")
            self.assertEqual(authorization, f"Bearer {FAKE_MASTER}")
            self.assertEqual(request["max_tokens"], 1)
        self.server.records.clear()
        local = self.call(SCRIPTS / "activer.sh", "--local")
        self.assertEqual(local.returncode, 0, local.stderr)
        self.assertIn("Fournisseurs non testés", local.stdout)
        self.assertFalse(any(r[0] == "POST" for r in self.server.records))

    def test_start_new_rejects_unsafe_keys_before_docker_run(self):
        key = self.sa_home / "master.key"
        target = self.root / "key-target"
        target.write_text(FAKE_MASTER)
        target.chmod(0o600)

        key.chmod(0o644)
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("run", [cmd.split()[0] for cmd in self.docker_commands()])

        self.docker_log.unlink(missing_ok=True)
        key.unlink()
        key.symlink_to(target)
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("run", [cmd.split()[0] for cmd in self.docker_commands()])
        self.assertNotIn(FAKE_MASTER, result.stdout + result.stderr)

        self.docker_log.unlink(missing_ok=True)
        key.unlink()
        os.mkfifo(key, 0o600)
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("run", [cmd.split()[0] for cmd in self.docker_commands()])
        self.assertNotIn(FAKE_MASTER, result.stdout + result.stderr)

    def test_start_new_creates_private_key_atomically_and_injects_it_only_as_env(self):
        key = self.sa_home / "master.key"
        key.unlink()
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertEqual(result.returncode, 0, result.stderr)
        content = key.read_text().strip()
        self.assertRegex(content, r"^sk-sa-[0-9a-f]{48}$")
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)
        self.assertTrue((self.state / "master-key-validated").exists())
        self.assertNotIn(content, result.stdout + result.stderr)
        self.assertNotIn(content, self.docker_log.read_text())
        self.assertIn("run", [cmd.split()[0] for cmd in self.docker_commands()])

    def test_concurrent_key_creation_publishes_one_complete_private_key(self):
        key = self.sa_home / "master.key"
        key.unlink()
        self.sa_home.chmod(0o700)
        command = ["python3", str(SCRIPTS / "master_key.py"), "--path", str(key)]
        processes = [subprocess.Popen(command, env=self.env, text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for _ in range(8)]
        results = [process.communicate(timeout=5) + (process.returncode,) for process in processes]
        self.assertTrue(all(code == 0 for _out, _err, code in results), results)
        values = [out for out, _err, _code in results]
        self.assertEqual(len(set(values)), 1)
        self.assertRegex(values[0], r"^sk-sa-[0-9a-f]{48}$")
        self.assertEqual(key.read_text().strip(), values[0])
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(self.sa_home.glob(".master.key.*.tmp")), [])

    def test_local_check_ignores_proxy_environment(self):
        self.set_container('running')
        proxy, proxy_thread = serve()
        try:
            self.env.update({'HTTP_PROXY':f'http://127.0.0.1:{proxy.server_port}',
                             'http_proxy':f'http://127.0.0.1:{proxy.server_port}', 'NO_PROXY':'', 'no_proxy':''})
            result = self.call(SCRIPTS / 'activer.sh')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(proxy.records, [])
        finally:
            proxy.shutdown(); proxy.server_close(); proxy_thread.join(timeout=2)

    def test_insecure_or_symlinked_key_is_refused(self):
        self.set_container('running')
        key = self.sa_home / 'master.key'; key.chmod(0o644)
        result = self.call(SCRIPTS / 'activer.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(r[1] == '/v1/models' for r in self.server.records))
        key.unlink(); target = self.root/'fake-target'; target.write_text(FAKE_MASTER); target.chmod(0o600)
        key.symlink_to(target)
        result = self.call(SCRIPTS / 'activer.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(FAKE_MASTER, result.stdout + result.stderr)

    def test_start_keeps_healthy_container_without_restart(self):
        self.set_container("running")
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.docker_commands()
        self.assertFalse(any(cmd.startswith(x) for cmd in commands for x in ("run ", "start ", "restart ", "stop ", "rm ")))

    def test_start_starts_stopped_container_without_recreating(self):
        self.set_container("exited")
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = [cmd.split()[0] for cmd in self.docker_commands()]
        self.assertIn("start", commands)
        self.assertNotIn("run", commands)
        self.assertNotIn("rm", commands)
        self.assertEqual((self.state / "status").read_text(), "running\n")

    def test_start_refuses_unexpected_image_or_port_without_mutation(self):
        for image, port in (("unexpected-image", self.env["MOCK_PORT"]),
                            (IMAGE, "0.0.0.0:4410")):
            with self.subTest(image=image, port=port):
                self.docker_log.unlink(missing_ok=True)
                self.set_container("running", image=image, port=port)
                result = self.call(SCRIPTS / "gateway.sh", "start")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Aucune action effectuée", result.stderr)
                commands = [cmd.split()[0] for cmd in self.docker_commands()]
                self.assertFalse(any(cmd in commands for cmd in ("run", "start", "restart", "stop", "rm")))

    def test_stop_stops_but_does_not_remove(self):
        self.set_container("running")
        result = self.call(SCRIPTS / "gateway.sh", "stop")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.state / "exists").exists())
        commands = [cmd.split()[0] for cmd in self.docker_commands()]
        self.assertIn("stop", commands)
        self.assertNotIn("rm", commands)

    def test_running_unhealthy_container_is_preserved(self):
        self.server.health_status = 503
        self.set_container("running")
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.state / "exists").exists())
        commands = [cmd.split()[0] for cmd in self.docker_commands()]
        self.assertFalse(any(cmd in commands for cmd in ("run", "start", "restart", "stop", "rm")))

    def test_new_unhealthy_container_is_kept_for_diagnostics(self):
        self.server.health_status = 503
        result = self.call(SCRIPTS / "gateway.sh", "start")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.state / "exists").exists())
        commands = [cmd.split()[0] for cmd in self.docker_commands()]
        self.assertIn("run", commands)
        self.assertNotIn("rm", commands)


if __name__ == "__main__":
    unittest.main(verbosity=2)
