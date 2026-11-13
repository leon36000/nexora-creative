#!/usr/bin/env python3
"""Suite de tests hors-ligne pour la ferme locale Qwen (eco-qwen / pc4)."""
from __future__ import annotations

import asyncio
import datetime as dt
import http.server
import importlib.util
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SA_DIR = TESTS_DIR.parent
sys.path.insert(0, str(SA_DIR))

import lot  # noqa: E402
import qwen_ctl  # noqa: E402
import task_router  # noqa: E402


def _load_sa_callbacks():
    import types

    litellm_mod = types.ModuleType("litellm")
    integ_mod = types.ModuleType("litellm.integrations")
    cl_mod = types.ModuleType("litellm.integrations.custom_logger")

    class CustomLogger:
        pass

    cl_mod.CustomLogger = CustomLogger
    saved = {k: sys.modules.get(k) for k in ("litellm", "litellm.integrations", "litellm.integrations.custom_logger")}
    sys.modules["litellm"] = litellm_mod
    sys.modules["litellm.integrations"] = integ_mod
    sys.modules["litellm.integrations.custom_logger"] = cl_mod
    try:
        spec = importlib.util.spec_from_file_location("sa_callbacks_qwen_test", SA_DIR / "litellm" / "sa_callbacks.py")
        mod = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


class _MockStrataHandler(http.server.BaseHTTPRequestHandler):
    mode = "ok"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.mode == "down":
            self.send_response(503)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if self.path == "/health":
            body = json.dumps(
                {
                    "status": "ok",
                    "model": "swift-1.5-qwen3.8-flash-next-abliterated-iq3_s",
                    "max_context": 262144,
                    "loaded": True,
                    "api_key": False,
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/v1/models":
            body = json.dumps(
                {"data": [{"id": "swift-1.5-qwen3.8-flash-next-abliterated-iq3_s", "object": "model"}]}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()


class TestQwenIntegration(unittest.TestCase):
    def test_lib_sh_sa_alias_qwen(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            cmd = (
                f". '{SA_DIR / 'lib.sh'}' && "
                "for a in qwen eco-qwen; do sa_alias \"$a\"; done"
            )
            res = subprocess.run(["bash", "-c", cmd], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(res.stdout.strip().splitlines(), ["eco-qwen", "eco-qwen"])

    def test_sa_callbacks_zero_cost_and_billing_pin(self):
        cb = _load_sa_callbacks()
        logger = cb.SaLogger()
        t0 = dt.datetime(2026, 11, 12, 12, 0, 0)
        t1 = dt.datetime(2026, 11, 12, 12, 0, 1)
        rec = logger._rec(
            {"model": "eco-qwen", "response_cost": None, "litellm_params": {"metadata": {"headers": {"x-sa-run": "r1"}}}},
            {"usage": {"prompt_tokens": 120, "completion_tokens": 30}},
            t0,
            t1,
            True,
        )
        self.assertEqual(rec["alias"], "eco-qwen")
        self.assertEqual(rec["cost"], 0.0)
        self.assertEqual(rec["in"], 120)
        self.assertEqual(rec["out"], 30)

        rec_other = logger._rec(
            {"model": "eco-deepseek", "response_cost": None, "litellm_params": {}},
            {"usage": {"prompt_tokens": 10, "completion_tokens": 5}},
            t0,
            t1,
            True,
        )
        self.assertIsNone(rec_other["cost"])

        data = {
            "model": "eco-qwen",
            "reasoning_effort": "high",
            "thinking": {"type": "enabled"},
            "messages": [
                {"role": "system", "content": "x-anthropic-billing-header: cc_version=2.1; cch=a9f3e;\nTu es utile."},
                {"role": "system", "content": [{"type": "text", "text": "x-anthropic-billing-header: cch=12bc9;"}]},
                {"role": "user", "content": "cch=99999 ne doit pas bouger hors system"},
            ],
        }
        out = asyncio.run(logger.async_pre_call_hook(None, None, data, "completion"))
        self.assertNotIn("reasoning_effort", out)
        self.assertNotIn("thinking", out)
        self.assertIn("cch=00000", out["messages"][0]["content"])
        self.assertIn("cch=00000", out["messages"][1]["content"][0]["text"])
        self.assertIn("cch=99999", out["messages"][2]["content"])

    def test_config_yaml_and_clean_patch_apply_on_base_and_dirty_main(self):
        cfg_text = (SA_DIR / "litellm" / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("model_name: eco-qwen", cfg_text)
        self.assertIn("max_parallel_requests: 2", cfg_text)
        self.assertIn("rpm: 24", cfg_text)
        self.assertIn('reasoning_effort: "medium"', cfg_text)
        self.assertIn("reasoning_budget_tokens: 4096", cfg_text)
        self.assertIn('- {"eco-qwen": ["eco-deepseek"]}', cfg_text)

        patch_path = SA_DIR / "litellm" / "eco-qwen.patch"
        self.assertTrue(patch_path.is_file(), "eco-qwen.patch doit être présent")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            target = tmp_p / "outils" / "sous-agents" / "litellm" / "config.yaml"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SA_DIR / "litellm" / "config.yaml", target)
            subprocess.run(["git", "-C", tmp, "init", "-q"], check=True)
            subprocess.run(["git", "-C", tmp, "apply", "-R", str(patch_path)], check=True)
            base_text = target.read_text(encoding="utf-8")
            self.assertNotIn("eco-qwen", base_text)

            subprocess.run(["git", "-C", tmp, "apply", "--check", str(patch_path)], check=True)

            dirty_text = base_text.replace(
                "general_settings:",
                "  - model_name: eco-carbon\n    litellm_params:\n      model: openrouter/test\n      timeout: 900\ngeneral_settings:",
            ).replace("max_budget: 20", "max_budget: 90")
            target.write_text(dirty_text, encoding="utf-8")
            subprocess.run(["git", "-C", tmp, "apply", "--check", str(patch_path)], check=True)
            subprocess.run(["git", "-C", tmp, "apply", str(patch_path)], check=True)
            merged = target.read_text(encoding="utf-8")
            self.assertIn("model_name: eco-qwen", merged)
            self.assertIn("model_name: eco-carbon", merged)
            self.assertIn("max_budget: 90", merged)

    def test_qwen_ctl_with_mock_server_fallback_and_slots(self):
        class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True

        _MockStrataHandler.mode = "ok"
        srv = ThreadedHTTPServer(("127.0.0.1", 0), _MockStrataHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            url = f"http://127.0.0.1:{port}/v1"
            p = qwen_ctl.probe_pc4(url=url, timeout=2.0)
            self.assertTrue(p["ok"])
            line = qwen_ctl.format_status_line(p, "eco-deepseek")
            self.assertIn("disponible", line)

            dec_ok = qwen_ctl.resolve_model("qwen", url=url, timeout=2.0, fallback_enabled=True)
            self.assertTrue(dec_ok["ok"])
            self.assertEqual(dec_ok["model"], "eco-qwen")
            self.assertFalse(dec_ok["fallback_used"])

            _MockStrataHandler.mode = "down"
            dec_fb = qwen_ctl.resolve_model("qwen", url=url, timeout=1.0, fallback_enabled=True, fallback_model="deepseek")
            self.assertTrue(dec_fb["ok"])
            self.assertEqual(dec_fb["model"], "eco-deepseek")
            self.assertTrue(dec_fb["fallback_used"])

            dec_strict = qwen_ctl.resolve_model("qwen", url=url, timeout=1.0, fallback_enabled=False)
            self.assertFalse(dec_strict["ok"])

            with tempfile.TemporaryDirectory() as lock_tmp:
                rc = qwen_ctl.run_with_slot(Path(lock_tmp), 2, 2.0, [sys.executable, "-c", "raise SystemExit(0)"])
                self.assertEqual(rc, 0)
        finally:
            srv.server_close()

    def test_lot_py_accepts_qwen_alias(self):
        self.assertEqual(lot.ALIASES.get("qwen"), "eco-qwen")
        self.assertEqual(lot.ALIASES.get("eco-qwen"), "eco-qwen")
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "prompts"
            wdir = Path(tmp) / "work"
            pdir.mkdir()
            wdir.mkdir()
            alias, _, _, par, _ = lot.parse_args(["qwen", str(pdir), str(wdir), "8"])
            self.assertEqual(alias, "eco-qwen")
            self.assertEqual(par, 8)

    def test_cout_py_counts_eco_qwen_zero_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "usage.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "ts": "2026-11-12T17:00:00+00:00",
                        "run": "20261112-qwen--abcd",
                        "alias": "eco-qwen",
                        "ok": True,
                        "in": 1500,
                        "out": 300,
                        "cost": 0.0,
                        "sec": 2.4,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["SA_STATE"] = tmp
            res = subprocess.run(
                [sys.executable, str(SA_DIR / "cout.py"), "--json"],
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(res.stdout)
            self.assertIn("eco-qwen", data["groupes"])
            self.assertEqual(float(data["gratuit"]["cout_total"]), 0.0)
            self.assertEqual(float(data["groupes"]["eco-qwen"]["cout_total"]), 0.0)

    def test_orchestrateur_sh_usage_lists_qwen(self):
        res = subprocess.run([str(SA_DIR / "orchestrateur.sh")], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.assertIn("qwen", res.stderr)

    def test_task_router_and_cli(self):
        r_ok = task_router.route_task("Extrais tous les champs JSON de config.yaml et vérifie la syntaxe.")
        self.assertEqual(r_ok["alias"], "eco-qwen")
        self.assertTrue(r_ok["eligible_qwen"])

        r_sec = task_router.route_task("Fais un audit de sécurité complet de l'authentification JWT et des secrets.")
        self.assertNotEqual(r_sec["alias"], "eco-qwen")
        self.assertFalse(r_sec["eligible_qwen"])

        r_arch = task_router.route_task("Conçois l'architecture distribuée et arbitre le choix de base de données.")
        self.assertNotEqual(r_arch["alias"], "eco-qwen")
        self.assertFalse(r_arch["eligible_qwen"])

        with tempfile.TemporaryDirectory() as tmp:
            pf = Path(tmp) / "prompt.txt"
            pf.write_text("Traduis ce fichier README.md du français vers l'anglais fidèlement.", encoding="utf-8")
            cli = subprocess.run(
                [str(SA_DIR / "router.sh"), "--file", str(pf), "--json"],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(cli.stdout)
            self.assertEqual(payload["alias"], "eco-qwen")


if __name__ == "__main__":
    unittest.main()
