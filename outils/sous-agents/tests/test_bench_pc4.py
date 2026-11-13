"""Tests bench_qwen_pc4 avec un faux serveur HTTP OpenAI-compatible local."""
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import bench_qwen_pc4 as bench

SECRET = "sk-SECRET-do-not-leak-42"


class FakeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    log_message = lambda *a, **k: None  # noqa: E731

    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"status": "ok"})
        elif self.path == "/v1/models":
            self._send_json({"object": "list", "data": [{"id": "qwen-test", "object": "model"}]})
        elif self.path == "/props":
            self._send_json({"default_generation_settings": {"n_ctx": 4096}, "total_slots": 4})
        elif self.path == "/slots":
            self._send_json([{"id": 0, "is_processing": False}, {"id": 1, "is_processing": False}])
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        user = payload["messages"][-1]
        tool_turn = any(m.get("role") == "tool" for m in payload["messages"])
        has_tool_result_msg = tool_turn

        if payload.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Connection", "close")
            self.end_headers()

            def send(obj):
                self.wfile.write(f"data: {json.dumps(obj)}\n\n".encode())
                self.wfile.flush()

            canary = ""
            text = user.get("content") or ""
            for word in text.split():
                if word.startswith("CANARY-"):
                    canary += word.rstrip(",") + ","
            if canary:
                pieces = [canary]
            else:
                pieces = ["Bonjour", " monde", " stream"]
            for p in pieces:
                send({"choices": [{"delta": {"content": p}, "index": 0}]})
            send({"choices": [{"delta": {}, "finish_reason": "stop", "index": 0}],
                  "usage": {"prompt_tokens": 12 + len(text) // 8, "completion_tokens": len(pieces)}})
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return

        if payload.get("tools") and has_tool_result_msg:
            msg = {"role": "assistant", "content": "Le build sur feature/login a réussi (142/142 tests)."}
            usage = {"prompt_tokens": 80, "completion_tokens": 14}
            finish = "stop"
        elif payload.get("tools"):
            msg = {"role": "assistant", "content": None,
                   "tool_calls": [{"id": "call_1", "type": "function",
                                   "function": {"name": "get_build_status",
                                                "arguments": json.dumps({"branch": "feature/login"})}}]}
            usage = {"prompt_tokens": 60, "completion_tokens": 18}
            finish = "tool_calls"
        else:
            msg = {"role": "assistant", "content": "Un serveur d'inférence exécute des modèles LLM."}
            usage = {"prompt_tokens": 20, "completion_tokens": 10}
            finish = "stop"
        self._send_json({"id": "x", "model": payload.get("model"), "choices": [{"message": msg, "finish_reason": finish}],
                         "usage": usage})


class BenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_normalize(self):
        self.assertEqual(bench.normalize_base_url("http://h:1"), "http://h:1/v1")
        self.assertEqual(bench.normalize_base_url("http://h:1/v1/"), "http://h:1/v1")
        with self.assertRaises(ValueError):
            bench.normalize_base_url("http://u:p@h:1/v1")
        with self.assertRaises(ValueError):
            bench.normalize_base_url("ftp://h/v1")

    def test_validate(self):
        v = bench.validate_openai(self.base, SECRET)
        self.assertEqual(v["models"]["model_id"], "qwen-test")
        self.assertEqual(v["max_context"], 4096)
        self.assertEqual(v["total_slots"], 4)
        self.assertTrue(v["chat"]["ok"])
        self.assertEqual(v["chat"]["usage"]["completion_tokens"], 10)
        self.assertIsNotNone(v["chat"]["tok_per_s"])
        st = v["chat_stream"]
        self.assertTrue(st["ok"])
        self.assertIsNotNone(st["ttft_ms"])
        self.assertEqual(st["chunks"], 4)  # 3 contenu + 1 finish/usage
        self.assertIsNotNone(st["stream_tok_per_s"])
        self.assertTrue(v["tools"]["ok"])
        self.assertTrue(v["tools"]["tool_call"]["arguments_json_valid"])
        self.assertEqual(v["tools"]["tool_call"]["arguments"]["branch"], "feature/login")
        self.assertTrue(v["tools"]["turn2_content_coherent"])
        self.assertNotIn(SECRET, json.dumps(v))

    def test_canary(self):
        p = bench.build_canary_prompt(1024)
        self.assertIn(p["canary_start"], p["prompt"])
        self.assertIn(p["canary_end"], p["prompt"])
        self.assertGreater(len(p["prompt"]), 1000)
        self.assertTrue(bench.check_canary(f"{p['canary_start']},{p['canary_end']}",
                                           p["canary_start"], p["canary_end"]))
        self.assertFalse(bench.check_canary("rien", p["canary_start"], p["canary_end"]))

    def test_context_window(self):
        res = bench.run_context_window(self.base, None, "qwen-test", [1024, 4096])
        self.assertEqual(len(res), 2)
        for r in res:
            self.assertTrue(r["ok"], r)
            self.assertTrue(r["canary_ok"], r)
            self.assertIsNotNone(r["prompt_tokens"])
            self.assertIsNotNone(r["ttft_ms"])

    def test_load(self):
        res = bench.run_load(self.base, None, "qwen-test", [1, 2, 4])
        self.assertEqual([r["concurrency"] for r in res], [1, 2, 4])
        for r in res:
            self.assertEqual(r["errors"], 0)
            self.assertEqual(r["error_rate"], 0)
            self.assertIsNotNone(r["p50_ms"])
            self.assertIsNotNone(r["min_ttft_ms"])
            self.assertIsNotNone(r["max_ttft_ms"])
            self.assertIsNotNone(r["agg_tok_per_s"])
        self.assertEqual(res[0]["degradation_factor_vs_c1"], 1.0)
        self.assertIsNotNone(res[1]["degradation_factor_vs_c1"])

    def test_percentile(self):
        self.assertEqual(bench.percentile([], 50), None)
        self.assertEqual(bench.percentile([5], 50), 5)
        self.assertAlmostEqual(bench.percentile([1, 2, 3, 4], 50), 2.5)

    def test_main_end_to_end(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "r.json")
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = bench.main(["--base-url", self.base, "--context-sizes", "1024",
                                 "--concurrencies", "1,2", "--out", out])
            self.assertEqual(rc, 0)
            md = buf.getvalue()
            self.assertIn("# Banc Qwen pc4", md)
            self.assertIn("qwen-test", md)
            self.assertIn("| 1024 |", md)
            self.assertIn("canary_ok", md)
            from pathlib import Path
            text_json = Path(out).read_text(encoding="utf-8")
            data = json.loads(text_json)
            self.assertIn("validation", data)
            self.assertIn("context_window", data)
            self.assertIn("load", data)
            self.assertNotIn(SECRET, text_json)


if __name__ == "__main__":
    unittest.main()
