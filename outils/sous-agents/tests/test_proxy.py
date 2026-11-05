import http.client
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location('sa_proxy', Path(__file__).resolve().parents[1] / 'sa_proxy.py')
proxy = importlib.util.module_from_spec(spec); spec.loader.exec_module(proxy)
FAKE_KEY = 'FAKE_GATEWAY_KEY_937214'

class Upstream(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_args): pass
    def do_POST(self):
        payload = self.rfile.read(int(self.headers['Content-Length']))
        if not getattr(self.server, 'no_log', False):
            with self.server.ledger.open('a') as f:
                f.write(json.dumps({'run':self.headers.get('x-sa-run'),'cost':0.001})+'\n')
        self.server.received.append({'path': self.path, 'key': self.headers.get('x-api-key'),
                                     'auth': self.headers.get('Authorization'), 'run': self.headers.get('x-sa-run'),
                                     'proxy_auth': self.headers.get('Proxy-Authorization'), 'rewrite': self.headers.get('X-Original-URL'),
                                     'payload': json.loads(payload)})
        self.send_response(self.server.status)
        self.send_header('Content-Type', 'text/event-stream')
        if self.server.content_length is not None: self.send_header('Content-Length', str(self.server.content_length))
        if self.server.encoding: self.send_header('Content-Encoding', self.server.encoding)
        self.send_header('Connection', 'close'); self.end_headers()
        for index, chunk in enumerate(self.server.chunks):
            self.wfile.write(chunk); self.wfile.flush()
            if index == 0 and self.server.pause_after_first: time.sleep(self.server.pause_after_first)
        self.close_connection = True

class UnixHTTP(http.client.HTTPConnection):
    def __init__(self, path): super().__init__('localhost', timeout=5); self.path = str(path)
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout); self.sock.connect(self.path)

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        self.upstream.received = []; self.upstream.status = 200; self.upstream.encoding = None
        self.upstream.ledger = Path(self.tmp.name) / 'usage.jsonl'; self.upstream.ledger.write_text('')
        self.upstream.chunks = [b'data: ok\n\n']; self.upstream.pause_after_first = 0; self.upstream.content_length = None
        self.up_thread = threading.Thread(target=self.upstream.serve_forever, daemon=True); self.up_thread.start()
        self.addCleanup(self.stop_upstream)
        self.sockpath = Path(self.tmp.name) / 'proxy.sock'
        old = os.umask(0o077)
        try:
            self.server = proxy.Server(str(self.sockpath), proxy.Handler, key=FAKE_KEY, run='lot-test-run',
                                       model='eco-deepseek', port=self.upstream.server_port, timeout=3,
                                       audit_path=str(Path(self.tmp.name) / 'audit.jsonl'), ledger_path=str(self.upstream.ledger),
                                       budget=Decimal('0.10'), ledger_wait=0.3)
        finally:
            os.umask(old)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.stop_proxy)

    def stop_proxy(self): self.server.shutdown(); self.server.server_close(); self.thread.join()
    def stop_upstream(self): self.upstream.shutdown(); self.upstream.server_close(); self.up_thread.join()

    def send(self, method='POST', path='/v1/messages', body=None, headers=None):
        c = UnixHTTP(self.sockpath)
        body = json.dumps({'model': 'eco-deepseek', 'max_tokens': 100, 'messages': []}) if body is None else body
        c.request(method, path, body=body, headers=headers or {'Content-Type': 'application/json'})
        r = c.getresponse(); result = (r.status, r.read()); c.close(); return result

    def test_only_allowed_route_model_and_forced_headers(self):
        code, _ = self.send(headers={'Content-Type': 'application/json', 'x-api-key': 'fake',
                                      'Authorization': 'Bearer fake', 'x-sa-run': 'forged',
                                      'Proxy-Authorization': 'fake', 'X-Original-URL': '/key/generate'})
        self.assertEqual(code, 200)
        got = self.upstream.received[0]
        self.assertEqual((got['key'], got['auth']), (FAKE_KEY, None))
        self.assertRegex(got['run'], r'^lot-test-run--p[0-9a-f]{16}--c1$')
        self.assertIsNone(got['proxy_auth']); self.assertIsNone(got['rewrite'])
        self.assertEqual(got['payload']['model'], 'eco-deepseek')

    def test_admin_and_wrong_model_are_never_forwarded(self):
        self.assertEqual(self.send('GET', '/key/info')[0], 403)
        self.assertEqual(self.send('POST', '/key/generate')[0], 403)
        self.assertEqual(self.send(body=json.dumps({'model': 'eco-muse'}))[0], 403)
        self.assertEqual(self.upstream.received, [])

    def test_count_tokens_is_explicitly_disabled_before_audit_or_upstream(self):
        c = UnixHTTP(self.sockpath)
        try:
            c.putrequest('POST', '/v1/messages/count_tokens?beta=true')
            c.putheader('Content-Type', 'application/json')
            c.putheader('Content-Length', '8')
            c.endheaders()
            response = c.getresponse()
            self.assertEqual(response.status, 501)
            self.assertIn('suivi de coût fiable', json.loads(response.read())['error'])
        finally:
            c.close()
        audit = Path(self.tmp.name) / 'audit.jsonl'
        self.assertEqual(audit.read_text(), '')
        self.assertEqual(self.server._sequence, 0)
        self.assertEqual(self.upstream.received, [])

    def test_ambiguous_headers_and_queries_are_refused(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.settimeout(3); s.connect(str(self.sockpath))
        body = json.dumps({'model':'eco-deepseek','max_tokens':10,'messages':[]}).encode()
        s.sendall(b'POST /v1/messages HTTP/1.1\r\nHost: localhost\r\nx-sa-run: one\r\nX-SA-RUN: two\r\nContent-Length: '
                  + str(len(body)).encode() + b'\r\n\r\n' + body)
        self.assertIn(b'400', s.recv(256)); s.close()
        self.assertEqual(self.send(path='/v1/messages?model=eco-muse')[0], 403)
        self.assertEqual(self.upstream.received, [])

    def test_duplicate_json_keys_cannot_bypass_model_filter(self):
        body = '{"model":"eco-muse","model":"eco-deepseek","messages":[]}'
        self.assertEqual(self.send(body=body)[0], 400)
        nested = '{"model":"eco-deepseek","messages":[{"role":"user","role":"assistant"}]}'
        self.assertEqual(self.send(body=nested)[0], 400)
        self.assertEqual(self.upstream.received, [])

    def test_output_token_limit_is_checked_before_upstream(self):
        for value in (None, 0, -1, 16001, True, '100'):
            body = json.dumps({'model': 'eco-deepseek', 'max_tokens': value, 'messages': []})
            self.assertEqual(self.send(body=body)[0], 400)
        self.assertEqual(self.upstream.received, [])
        body = json.dumps({'model': 'eco-deepseek', 'max_tokens': 16000, 'messages': []})
        self.assertEqual(self.send(body=body)[0], 200)

    def test_split_secret_is_not_returned(self):
        self.upstream.chunks = [b'data: ' + FAKE_KEY[:6].encode(), FAKE_KEY[6:14].encode(), FAKE_KEY[14:].encode() + b'\n\n']
        code, body = self.send()
        self.assertEqual(code, 200); self.assertNotIn(FAKE_KEY.encode(), body); self.assertIn(b'[redacted]', body)

    def test_incomplete_client_does_not_block_valid_request(self):
        self.server.client_timeout = 0.8
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.settimeout(2); c.connect(str(self.sockpath))
        try:
            c.sendall(b'POST /v1/messages HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1000000\r\n\r\n{')
            time.sleep(0.05)
            self.assertEqual(self.send()[0], 200)
            self.assertEqual(len(self.upstream.received), 1)
        finally:
            c.close()

    def test_slow_clients_cannot_create_unbounded_workers(self):
        self.server.client_timeout = 0.3
        clients = []
        try:
            for _ in range(12):
                c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.settimeout(1)
                try: c.connect(str(self.sockpath))
                except OSError: c.close(); continue
                try: c.sendall(b'POST /v1/messages HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1000000\r\n\r\n{')
                except OSError: pass
                clients.append(c)
            time.sleep(0.15)
            active = [t for t in threading.enumerate() if getattr(getattr(t, '_target', None), '__self__', None) is self.server and getattr(getattr(t, '_target', None), '__name__', '') == 'process_request_thread']
            self.assertLessEqual(len(active), 4)
            time.sleep(0.4)
            self.assertEqual(self.upstream.received, [])
        finally:
            for c in clients: c.close()

    def test_incomplete_upstream_is_detected_by_client(self):
        self.upstream.chunks = [b'data: partial\n\n']
        self.upstream.content_length = 100
        c = UnixHTTP(self.sockpath)
        c.request('POST', '/v1/messages', body=json.dumps({'model':'eco-deepseek','max_tokens':10,'messages':[]}))
        r = c.getresponse()
        self.assertEqual(r.status, 200)
        with self.assertRaises(http.client.IncompleteRead): r.read()
        c.close()

    def test_audit_contains_only_forwarding_attempts_and_no_sensitive_content(self):
        self.assertEqual(self.send('POST', '/key/generate')[0], 403)
        self.assertEqual(self.send()[0], 200)
        log = (Path(self.tmp.name)/'audit.jsonl').read_text()
        records = [json.loads(line) for line in log.splitlines()]
        self.assertEqual(len(records), 1); self.assertEqual(records[0]['sequence'], 1)
        self.assertRegex(records[0]['call'], r'^lot-test-run--p[0-9a-f]{16}--c1$')
        self.assertNotIn(FAKE_KEY, log)

    def test_budget_reached_or_unknown_blocks_before_upstream(self):
        self.upstream.ledger.write_text(json.dumps({'run':'lot-test-run','cost':0.10})+'\n')
        self.assertEqual(self.send()[0], 429)
        self.upstream.ledger.write_text(json.dumps({'run':'lot-test-run','cost':None})+'\n')
        self.assertEqual(self.send()[0], 503)
        self.assertEqual(self.upstream.received, [])

    def test_budget_comparison_uses_exact_decimal_without_rounding(self):
        self.upstream.ledger.write_text('{"run":"lot-test-run","cost":0.0999999999999999999999999999}\n')
        self.assertEqual(self.server.budget_status(), 'ok')
        self.upstream.ledger.write_text('{"run":"lot-test-run","cost":0.1000000000000000000000000001}\n')
        self.assertEqual(self.server.budget_status(), 'limite')

    def test_historical_tag_is_counted_but_does_not_confirm_current_attempt(self):
        self.upstream.ledger.write_text(
            '{"run":"lot-test-run--p0123456789abcdef--c7","cost":0.10}\n')
        self.assertEqual(self.send()[0], 429)
        self.assertEqual(self.upstream.received, [])

    def test_ledger_duplicate_cost_cannot_hide_spend(self):
        self.upstream.ledger.write_text('{"run":"lot-test-run","cost":1.0,"cost":0.0}\n')
        self.assertEqual(self.send()[0], 503)
        self.assertEqual(self.upstream.received, [])

    def test_duplicate_ledger_rows_cannot_confirm_a_different_attempt(self):
        self.assertEqual(self.send()[0], 200)
        row = self.upstream.ledger.read_text()
        self.upstream.ledger.write_text(row + row)
        self.upstream.no_log = True
        self.assertEqual(self.send()[0], 200)
        self.assertEqual(self.send()[0], 503)
        self.assertEqual(len(self.upstream.received), 2)

    def test_unlogged_previous_request_blocks_next(self):
        self.assertEqual(self.send()[0], 200)
        self.upstream.ledger.write_text('')
        started = time.monotonic()
        self.assertEqual(self.send()[0], 503)
        elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 0.25)
        self.assertLess(elapsed, 1.5)
        self.assertEqual(len(self.upstream.received), 1)

    def test_failed_connection_is_recorded_as_attempt_not_confirmed_delivery(self):
        # An unused local port refuses connections; this does not prove upstream receipt.
        sock = socket.socket(); sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]; sock.close()
        self.server.port = port
        self.assertEqual(self.send()[0], 502)
        log = (Path(self.tmp.name)/'audit.jsonl').read_text()
        records = [json.loads(line) for line in log.splitlines()]
        self.assertEqual(len(records), 1); self.assertEqual(records[0]['sequence'], 1)
        self.assertRegex(records[0]['call'], r'^lot-test-run--p[0-9a-f]{16}--c1$')
        self.assertEqual(self.upstream.received, [])

    def test_second_concurrent_request_is_not_forwarded(self):
        self.upstream.chunks = [b'data:a\n\n', b'data:b\n\n']; self.upstream.pause_after_first = 0.8
        c = UnixHTTP(self.sockpath)
        c.request('POST', '/v1/messages', body=json.dumps({'model':'eco-deepseek','max_tokens':10,'messages':[]}))
        response = c.getresponse()
        self.assertEqual(response.read1(8), b'data:a\n\n')
        self.assertEqual(self.send()[0], 429)
        self.assertEqual(response.read(), b'data:b\n\n'); c.close()
        self.assertEqual(len(self.upstream.received), 1)

    def test_short_sse_event_arrives_before_next_event(self):
        self.upstream.chunks = [b'data:a\n\n', b'data:b\n\n']
        self.upstream.pause_after_first = 0.8
        c = UnixHTTP(self.sockpath)
        c.request('POST', '/v1/messages', body=json.dumps({'model':'eco-deepseek','max_tokens':10,'messages':[]}))
        c.sock.settimeout(0.4); r = c.getresponse()
        self.assertEqual(r.read1(8), b'data:a\n\n')
        r.fp.raw._sock.settimeout(3); self.assertEqual(r.read(), b'data:b\n\n'); c.close()

    def test_encoded_response_is_refused(self):
        self.upstream.encoding = 'gzip'; self.upstream.chunks = [b'opaque']
        self.assertEqual(self.send()[0], 502)

    def test_status_and_stream_body_preserved(self):
        self.upstream.status = 429; self.upstream.chunks = [b'data: x\n\n', b'data: y\n\n']
        self.assertEqual(self.send(), (429, b'data: x\n\ndata: y\n\n'))

    def test_zero_length_upstream_is_not_rejected(self):
        self.upstream.chunks = []
        self.upstream.content_length = 0
        self.assertEqual(self.send(), (200, b''))

    def test_socket_is_private(self):
        self.assertEqual(self.sockpath.stat().st_mode & 0o777, 0o700 - 0o100)

class ProcessTests(unittest.TestCase):
    def test_status_is_sent_before_upstream_headers_are_read(self):
        events = []
        handler = object.__new__(proxy.Handler)
        handler.send_response = lambda status: events.append(('statut', status))
        class FakeResponse:
            status = 200
            def getheaders(self):
                events.append(('en-têtes', None))
                raise http.client.HTTPException('fictif')
        response = FakeResponse()
        with self.assertRaises(http.client.HTTPException):
            handler._send_stream_headers(response)
        self.assertEqual(events, [('statut', 200), ('en-têtes', None)])

    def test_socket_path_too_long_preserves_original_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit, ledger = root / 'audit', root / 'ledger'
            ledger.write_text('')
            path = str(root / ('x' * 150))
            kwargs = dict(key=FAKE_KEY, run='test-run', model='eco-deepseek', port=1, timeout=1,
                          audit_path=str(audit), ledger_path=str(ledger), budget=Decimal('1'))
            with self.assertRaises(OSError) as erreur:
                proxy.Server(path, proxy.Handler, **kwargs)
            self.assertIn('path too long', str(erreur.exception).lower())

    def test_chmod_failure_closes_listener_and_preserves_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit, ledger, sockpath = root / 'audit', root / 'ledger', root / 'socket'
            ledger.write_text('')
            path = str(sockpath)
            kwargs = dict(key=FAKE_KEY, run='test-run', model='eco-deepseek', port=1, timeout=1,
                          audit_path=str(audit), ledger_path=str(ledger), budget=Decimal('1'))
            with patch.object(proxy.os, 'chmod', side_effect=PermissionError('chmod factice')):
                with self.assertRaisesRegex(PermissionError, 'chmod factice'):
                    proxy.Server(path, proxy.Handler, **kwargs)
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                with self.assertRaises(ConnectionRefusedError):
                    client.connect(str(sockpath))
            finally:
                client.close()

    def test_key_passes_via_fd_not_argv_or_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); key = root/'key'; key.write_text(FAKE_KEY); key.chmod(0o600)
            ledger = root/'ledger'; ledger.write_text(''); sock = root/'socket'; audit = root/'audit'
            env = dict(os.environ, SA_PROXY_RUN='test-run', SA_PROXY_MODEL='eco-deepseek',
                       SA_PROXY_PORT='12345', SA_PROXY_TIMEOUT='5', SA_PROXY_AUDIT=str(audit),
                       SA_PROXY_LEDGER=str(ledger), SA_PROXY_BUDGET='0.10')
            observation = root/'observation.json'
            bootstrap = root/'bootstrap.py'
            bootstrap.write_text(
                "import json, os, runpy, sys\n"
                f"expected = {FAKE_KEY!r}\n"
                "report = {\n"
                " 'argv_propre': all(expected not in a for a in sys.argv),\n"
                " 'environnement_propre': all(expected not in v for v in os.environ.values()),\n"
                " 'fd_contient_cle_factice': os.pread(3, 4096, 0).decode() == expected,\n"
                "}\n"
                "with open(sys.argv[3], 'w') as output: json.dump(report, output)\n"
                "sys.path.insert(0, os.path.dirname(sys.argv[1]))\n"
                "sys.argv = [sys.argv[1], sys.argv[2]]\n"
                "runpy.run_path(sys.argv[0], run_name='__main__')\n"
            )
            process = subprocess.Popen(['bash', '-c', 'exec 3<"$1"; exec "$2" "$3" "$4" "$5" "$6"',
                                        '_', str(key), sys.executable, str(bootstrap), str(Path(proxy.__file__)),
                                        str(sock), str(observation)],
                                       env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                end = time.monotonic()+5
                while not sock.exists() and process.poll() is None and time.monotonic()<end: time.sleep(0.05)
                self.assertTrue(sock.exists())
                self.assertEqual(json.loads(observation.read_text()), {
                    'argv_propre': True, 'environnement_propre': True, 'fd_contient_cle_factice': True,
                })
            finally:
                (root / 'proxy-stop').write_text('arrêt fictif')
                process.wait(timeout=5)

    def test_world_readable_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); key=root/'key'; key.write_text(FAKE_KEY); key.chmod(0o644)
            ledger=root/'ledger'; ledger.write_text(''); sock=root/'socket'; audit=root/'audit'
            env=dict(os.environ, SA_PROXY_RUN='test-run', SA_PROXY_MODEL='eco-deepseek', SA_PROXY_PORT='12345',
                     SA_PROXY_TIMEOUT='5', SA_PROXY_AUDIT=str(audit), SA_PROXY_LEDGER=str(ledger), SA_PROXY_BUDGET='0.10')
            process=subprocess.run(['bash','-c','exec 3<"$1"; exec "$2" "$3" "$4"',
                                    '_',str(key),sys.executable,str(Path(proxy.__file__)),str(sock)],
                                   env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
            self.assertNotEqual(process.returncode,0); self.assertFalse(sock.exists())
            self.assertNotIn(FAKE_KEY.encode(), process.stdout+process.stderr)

if __name__ == '__main__': unittest.main()
