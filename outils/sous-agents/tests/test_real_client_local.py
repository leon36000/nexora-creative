"""Essai local : vrai client d'agent, fausse passerelle locale, aucun fournisseur."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAKE_KEY = 'FAKE_LOCAL_GATEWAY_KEY_81253'
PROMPT = 'Réponds avec la réponse fictive de test.'
FAKE_IMAGE = 'ghcr.io/berriai/litellm@sha256:7294b90f868c5c38c99b83021c7ba46f9b439e95f8e32964c925c7d2563a03f7'

def fake_docker(root):
    bin_dir = root / 'bin'; bin_dir.mkdir()
    stub = bin_dir / 'docker'
    stub.write_text("#!/bin/sh\n" + "printf 'true|%s|127.0.0.1:%s,\\n' \"$FAKE_IMAGE\" \"$SA_PORT\"\n")
    stub.chmod(0o755)
    return str(bin_dir) + os.pathsep + os.environ['PATH']

def install_racing_cat(root, key_path):
    stub = root / 'bin' / 'cat'
    stub.write_text('''#!/bin/sh
for path in "$@"; do
  if [ "$path" = "$FAKE_MASTER_PATH" ]; then
    /bin/cat "$path"
    printf FAKE_REPLACEMENT_GATEWAY_KEY > "$path.replacement"
    chmod 600 "$path.replacement"
    mv "$path.replacement" "$path"
    exit 0
  fi
done
exec /bin/cat "$@"
''')
    stub.chmod(0o755)

class FakeGateway(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *_args): pass
    def do_GET(self):
        if self.path != '/health/liveliness':
            self.send_response(404); self.send_header('Content-Length', '0'); self.end_headers(); return
        self.send_response(200); self.send_header('Content-Length', '0'); self.end_headers()
    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        try: data = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            self.send_response(400); self.send_header('Content-Length', '0'); self.end_headers(); return
        run = self.headers.get('x-sa-run')
        self.server.records.append({'path': self.path, 'correct_key': self.headers.get('x-api-key') == FAKE_KEY,
                                    'run': run, 'model': data.get('model'),
                                    'prompt_present': PROMPT in json.dumps(data, ensure_ascii=False),
                                    'tool_result_safe': 'nexora-sandbox|absent' in json.dumps(data, ensure_ascii=False),
                                    'parent_secret_seen': 'FAKE_PARENT_SENTINEL_4721' in json.dumps(data, ensure_ascii=False),
                                    'gateway_key_seen': FAKE_KEY in json.dumps(data, ensure_ascii=False)})
        if run:
            with (self.server.state / 'usage.jsonl').open('a') as f:
                f.write(json.dumps({'run':run, 'cost':getattr(self.server, 'cost', 0.001), 'in':12, 'out':3})+'\n')
        message = {'id':'msg_fake_123','type':'message','role':'assistant','model':'eco-deepseek',
                   'content':[],'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':12,'output_tokens':0}}
        events = [
            ('message_start', {'type':'message_start','message':message}),
            ('content_block_start', {'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}}),
            ('content_block_delta', {'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':'Réponse fictive'}}),
            ('content_block_stop', {'type':'content_block_stop','index':0}),
            ('message_delta', {'type':'message_delta','delta':{'stop_reason':'end_turn','stop_sequence':None},'usage':{'output_tokens':3}}),
            ('message_stop', {'type':'message_stop'}),
        ]
        if getattr(self.server, 'inspect_tool', False) and len(self.server.records) == 1:
            command = 'printf "%s|%s" "$ANTHROPIC_API_KEY" "${FAKE_PARENT_SECRET:-absent}"'
            events = [
                ('message_start', {'type':'message_start','message':message}),
                ('content_block_start', {'type':'content_block_start','index':0,'content_block':{'type':'tool_use','id':'toolu_fake_123','name':'Bash','input':{}}}),
                ('content_block_delta', {'type':'content_block_delta','index':0,'delta':{'type':'input_json_delta','partial_json':json.dumps({'command':command})}}),
                ('content_block_stop', {'type':'content_block_stop','index':0}),
                ('message_delta', {'type':'message_delta','delta':{'stop_reason':'tool_use','stop_sequence':None},'usage':{'output_tokens':3}}),
                ('message_stop', {'type':'message_stop'}),
            ]
        self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.send_header('Connection','close'); self.end_headers()
        for event, data in events:
            self.wfile.write(('event: '+event+'\ndata: '+json.dumps(data,ensure_ascii=False)+'\n\n').encode()); self.wfile.flush()
        self.close_connection = True

class TestRealClient(unittest.TestCase):
    def prepare_candidate_lot_runtime(self, root):
        runtime = root / 'sous-agents'; runtime.mkdir()
        candidate = ROOT
        for name in ('lot.sh', 'lot.py'):
            shutil.copy2(candidate / name, runtime / name)
        for name in ('lib.sh', 'sous-agent.sh', 'sa_proxy.py', 'proxy_launcher.py', 'cost_snapshot.py'):
            shutil.copy2(ROOT / name, runtime / name)
        gateway_log = root / 'fake-gateway-start.log'
        gateway = runtime / 'gateway.sh'
        gateway.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_GATEWAY_START_LOG"\nexit 0\n')
        gateway.chmod(0o755)
        cost = runtime / 'cout.sh'; cost.write_text('#!/bin/sh\nexit 0\n'); cost.chmod(0o755)
        return runtime, gateway_log

    def test_real_client_uses_stdin_and_local_fake_gateway(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'work'; work.mkdir(); state = root / 'state'; state.mkdir()
            (state/'usage.jsonl').write_text(''); (state/'usage.jsonl').chmod(0o600); cfg = root/'config'; cfg.mkdir(); (cfg/'master.key').write_text(FAKE_KEY); (cfg/'master.key').chmod(0o600)
            prompt = root/'prompt.txt'; prompt.write_text(PROMPT)
            site_dir = root/'site'; site_dir.mkdir()
            site_sentinel = root/'sitecustomize-read-fd3'
            (site_dir/'sitecustomize.py').write_text(
                "import os\nfrom pathlib import Path\n"
                "try: data=os.read(3,4097)\nexcept OSError: data=b''\n"
                "Path(" + repr(str(site_sentinel)) + ").write_bytes(data)\n"
            )
            gateway = ThreadingHTTPServer(('127.0.0.1',0), FakeGateway)
            gateway.records = []; gateway.state = state
            thread = threading.Thread(target=gateway.serve_forever,daemon=True); thread.start()
            try:
                path = fake_docker(root)
                install_racing_cat(root, cfg/'master.key')
                env = dict(os.environ, SA_HOME=str(cfg), SA_STATE=str(state), SA_PORT=str(gateway.server_port),
                           SA_TIMEOUT='45', NO_PROXY='127.0.0.1,localhost', PATH=path,
                           FAKE_MASTER_PATH=str(cfg/'master.key'), FAKE_IMAGE=FAKE_IMAGE,
                           PYTHONPATH=str(site_dir), FAKE_HOST_SENTINEL='should-not-reach-relay')
                r = subprocess.run([str(ROOT/'sous-agent.sh'),'-w','deepseek',str(prompt),str(work),'2','0.10'],
                                   env=env, text=True,capture_output=True,timeout=65)
                out = Path(r.stdout.splitlines()[0])
                state = out.parent.parent
                details = (f"résumé={((out/'summary.txt').read_text() if (out/'summary.txt').exists() else 'absent')} "
                           f"audit={((out/'proxy-audit.jsonl').read_text() if (out/'proxy-audit.jsonl').exists() else 'absent')} "
                           f"ledger={(state/'usage.jsonl').read_text() if (state/'usage.jsonl').exists() else 'absent'} "
                           f"proxy={(out/'proxy.log').read_text() if (out/'proxy.log').exists() else 'absent'}")
                self.assertEqual(r.returncode,0, f"lancement local échoué; {details}")
                result = json.loads((out/'result.json').read_text())
                self.assertFalse(result['is_error'])
                self.assertEqual(result.get('result'), 'Réponse fictive')
                self.assertTrue(gateway.records)
                first = gateway.records[0]
                self.assertTrue(first['correct_key']); self.assertTrue(first['prompt_present'])
                self.assertEqual(first['model'],'eco-deepseek')
                self.assertEqual((cfg/'master.key').read_text(), FAKE_KEY)
                self.assertFalse(site_sentinel.exists())
                self.assertNotIn(FAKE_KEY, r.stdout+r.stderr)
            finally:
                gateway.shutdown(); gateway.server_close(); thread.join()

    def test_model_tool_sees_dummy_key_not_host_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root/'work'; work.mkdir(); state = root/'state'; state.mkdir()
            (state/'usage.jsonl').write_text(''); (state/'usage.jsonl').chmod(0o600); cfg = root/'config'; cfg.mkdir(); (cfg/'master.key').write_text(FAKE_KEY); (cfg/'master.key').chmod(0o600)
            prompt = root/'prompt.txt'; prompt.write_text(PROMPT)
            gateway = ThreadingHTTPServer(('127.0.0.1',0), FakeGateway)
            gateway.records = []; gateway.state = state; gateway.inspect_tool = True
            thread = threading.Thread(target=gateway.serve_forever, daemon=True); thread.start()
            try:
                env = dict(os.environ, SA_HOME=str(cfg), SA_STATE=str(state), SA_PORT=str(gateway.server_port),
                           SA_TIMEOUT='45', NO_PROXY='127.0.0.1,localhost', FAKE_PARENT_SECRET='FAKE_PARENT_SENTINEL_4721',
                           PATH=fake_docker(root), FAKE_IMAGE=FAKE_IMAGE)
                r = subprocess.run([str(ROOT/'sous-agent.sh'),'-w','deepseek',str(prompt),str(work),'4','0.10'],
                                   env=env, text=True,capture_output=True,timeout=65)
                out = Path(r.stdout.splitlines()[0])
                self.assertEqual(r.returncode,0, f"agent local fictif échoué; résumé={((out/'summary.txt').read_text() if (out/'summary.txt').exists() else 'absent')}")
                self.assertGreaterEqual(len(gateway.records), 2)
                self.assertTrue(any(record['tool_result_safe'] for record in gateway.records[1:]))
                self.assertFalse(any(record['parent_secret_seen'] or record['gateway_key_seen'] for record in gateway.records))
                for name in ('transcript.jsonl','result.json','stderr.log','proxy.log'):
                    text = (out/name).read_text()
                    self.assertNotIn(FAKE_KEY, text); self.assertNotIn('FAKE_PARENT_SENTINEL_4721', text)
            finally:
                gateway.shutdown(); gateway.server_close(); thread.join()

    def test_hardened_lot_candidate_runs_current_runner_and_attributes_tagged_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / 'workdirs'; work_root.mkdir()
            work = work_root / 'task-a'; work.mkdir()
            prompts = root / 'prompts'; prompts.mkdir()
            prompt = prompts / 'task-a.txt'; prompt.write_text(PROMPT)
            state = root / 'state'; state.mkdir()
            cfg = root / 'config'; cfg.mkdir()
            (cfg / 'master.key').write_text(FAKE_KEY); (cfg / 'master.key').chmod(0o600)
            runtime, gateway_start_log = self.prepare_candidate_lot_runtime(root)

            gateway = ThreadingHTTPServer(('127.0.0.1', 0), FakeGateway)
            gateway.records = []; gateway.state = state
            thread = threading.Thread(target=gateway.serve_forever, daemon=True); thread.start()
            try:
                env = dict(os.environ, SA_HOME=str(cfg), SA_STATE=str(state), SA_PORT=str(gateway.server_port),
                           SA_TIMEOUT='45', PATH=fake_docker(root), FAKE_IMAGE=FAKE_IMAGE,
                           FAKE_GATEWAY_START_LOG=str(gateway_start_log), LOT_BUDGET='1',
                           LOT_RUN_BUDGET='0.10', LOT_TURNS='2')
                result = subprocess.run([str(runtime / 'lot.sh'), 'deepseek', str(prompts), str(work_root), '1'],
                                        env=env, text=True, capture_output=True, timeout=65)
                lot_roots = list((state / 'lots').glob('*')) if (state / 'lots').exists() else []
                self.assertEqual(len(lot_roots), 1, result.stderr + result.stdout)
                lot = lot_roots[0]
                index = lot / 'index.tsv'
                self.assertTrue(index.is_file(), result.stderr + result.stdout)
                rows = index.read_text().splitlines()
                self.assertEqual(rows[0], 'statut\ttache\tcode_retour\tdetail')
                self.assertEqual(rows[1], 'OK\ttask-a\t0\ttermine')
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                out = lot / 'task-a'
                self.assertTrue((out / 'done').exists())
                run_id = json.loads((out / 'meta.json').read_text())['run']
                self.assertTrue(run_id.startswith(lot.name + '-'))
                self.assertTrue(gateway.records)
                self.assertTrue(all(record['correct_key'] for record in gateway.records))
                ledger_rows = [json.loads(line) for line in (state / 'usage.jsonl').read_text().splitlines()]
                self.assertTrue(ledger_rows)
                self.assertTrue(all(re.fullmatch(re.escape(run_id) + r'--p[0-9a-f]{16}--c[1-9][0-9]*', row['run'])
                                    for row in ledger_rows))
                self.assertTrue(gateway_start_log.is_file())
                self.assertTrue((state / 'usage.jsonl').is_file())
            finally:
                gateway.shutdown(); gateway.server_close(); thread.join()

    def test_hardened_lot_index_marks_run_budget_overage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work_root = root / 'workdirs'; work_root.mkdir()
            work = work_root / 'task-a'; work.mkdir()
            prompts = root / 'prompts'; prompts.mkdir()
            prompt = prompts / 'task-a.txt'; prompt.write_text(PROMPT)
            state = root / 'state'; state.mkdir()
            cfg = root / 'config'; cfg.mkdir()
            (cfg / 'master.key').write_text(FAKE_KEY); (cfg / 'master.key').chmod(0o600)
            runtime, gateway_start_log = self.prepare_candidate_lot_runtime(root)

            gateway = ThreadingHTTPServer(('127.0.0.1', 0), FakeGateway)
            gateway.records = []; gateway.state = state; gateway.cost = 0.15
            thread = threading.Thread(target=gateway.serve_forever, daemon=True); thread.start()
            try:
                env = dict(os.environ, SA_HOME=str(cfg), SA_STATE=str(state), SA_PORT=str(gateway.server_port),
                           SA_TIMEOUT='45', PATH=fake_docker(root), FAKE_IMAGE=FAKE_IMAGE,
                           FAKE_GATEWAY_START_LOG=str(gateway_start_log), LOT_BUDGET='0.20',
                           LOT_RUN_BUDGET='0.10', LOT_TURNS='2')
                result = subprocess.run([str(runtime / 'lot.sh'), 'deepseek', str(prompts), str(work_root), '1'],
                                        env=env, text=True, capture_output=True, timeout=65)
                lot_roots = list((state / 'lots').glob('*')) if (state / 'lots').exists() else []
                self.assertEqual(len(lot_roots), 1, result.stderr + result.stdout)
                lot = lot_roots[0]
                self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
                self.assertEqual((lot / 'lot_status.txt').read_text().strip(), 'FAIL')
                self.assertEqual((lot / 'index.tsv').read_text().splitlines()[1],
                                 'FAIL\ttask-a\t1\tbudget_run_depasse')
                self.assertTrue(gateway.records)
            finally:
                gateway.shutdown(); gateway.server_close(); thread.join()

if __name__ == '__main__': unittest.main()
