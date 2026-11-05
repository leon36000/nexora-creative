"""Tests locaux du journal de passerelle, sans LiteLLM ni réseau."""
import asyncio
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

CALLBACK = Path(__file__).resolve().parents[1] / 'litellm' / 'sa_callbacks.py'

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / 'usage.jsonl'
        fake = types.ModuleType('litellm.integrations.custom_logger')
        fake.CustomLogger = type('CustomLogger', (), {})
        modules = {'litellm': types.ModuleType('litellm'), 'litellm.integrations': types.ModuleType('litellm.integrations'),
                   'litellm.integrations.custom_logger': fake}
        self.mod_patch = patch.dict(sys.modules, modules); self.mod_patch.start(); self.addCleanup(self.mod_patch.stop)
        self.env_patch = patch.dict(os.environ, {'SA_LOG': str(self.log)}); self.env_patch.start(); self.addCleanup(self.env_patch.stop)
        spec = importlib.util.spec_from_file_location('local_sa_callback', CALLBACK)
        self.mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
        self.handler = self.mod.proxy_handler_instance
        self.t0 = datetime(2026, 1, 1, 12, 0, 0); self.t1 = self.t0 + timedelta(seconds=2)

    def record(self, cost_marker, error=None):
        kwargs = {'model':'eco-muse', 'litellm_params':{'metadata':{'model_group':'eco-muse','headers':{'x-sa-run':'test-run'}}}}
        if cost_marker != 'absent': kwargs['response_cost'] = cost_marker
        if error is not None: kwargs['exception'] = error
        if error is None:
            asyncio.run(self.handler.async_log_success_event(kwargs, {'usage':{'prompt_tokens':3,'completion_tokens':5}}, self.t0, self.t1))
        else:
            asyncio.run(self.handler.async_log_failure_event(kwargs, None, self.t0, self.t1))
        return json.loads(self.log.read_text().splitlines()[-1])

    def test_absent_none_invalid_and_negative_cost_are_unknown(self):
        for value in ('absent', None, -1, True, '1.0', float('nan'), float('inf')):
            with self.subTest(value=value): self.assertIsNone(self.record(value)['cost'])

    def test_decimal_underflow_or_precision_loss_is_unknown(self):
        for value in (Decimal('1e-1000'), Decimal('1e-324'), Decimal('0.123456789012345678901')):
            self.assertIsNone(self.mod._cost({'response_cost': value}))
        self.assertEqual(self.mod._cost({'response_cost': Decimal('0.1')}), 0.1)

    def test_zero_and_positive_cost_are_preserved(self):
        self.assertEqual(self.record(0)['cost'], 0)
        result = self.record(0.0023)
        self.assertEqual(result['cost'], 0.0023); self.assertEqual((result['in'], result['out']), (3, 5))
        self.assertEqual((result['run'], result['alias'], result['ok']), ('test-run', 'eco-muse', True))

    def test_exception_message_and_dynamic_type_name_are_not_logged(self):
        secret = 'FAKE_SECRET_4821'
        result = self.record(None, RuntimeError(secret))
        self.assertEqual(result['err'], 'RuntimeError')
        dynamic = type(secret, (Exception,), {})
        result = self.record(None, dynamic(secret))
        self.assertEqual(result['err'], 'AutreErreur')
        self.assertNotIn(secret, self.log.read_text())

    def test_only_expected_fields_and_no_prompt_or_response_are_logged(self):
        secret = 'FAKE_PRIVATE_PROMPT_7392'
        kwargs = {'model':'eco-muse', 'messages':[{'content':secret}],
                  'litellm_params':{'metadata':{'model_group':'eco-muse','headers':{'x-sa-run':'test-run'}}},
                  'response_cost':0.001}
        response = {'usage':{'prompt_tokens':1,'completion_tokens':1}, 'content':secret}
        asyncio.run(self.handler.async_log_success_event(kwargs, response, self.t0, self.t1))
        raw = self.log.read_text(); result = json.loads(raw.splitlines()[-1])
        self.assertEqual(set(result), {'ts','run','alias','ok','in','out','cost','sec'})
        self.assertEqual(result['sec'], 2.0)
        datetime.strptime(result['ts'][:19], '%Y-%m-%dT%H:%M:%S')
        self.assertNotIn(secret, raw)

    def test_pre_call_hook_keeps_its_existing_behavior(self):
        data = {'model':'eco-muse','reasoning_effort':'high','reasoning':{},'thinking':{},'output_config':{},'messages':[]}
        result = asyncio.run(self.handler.async_pre_call_hook({}, None, data, 'completion'))
        self.assertEqual(result, {'model':'eco-muse','messages':[]})

if __name__ == '__main__': unittest.main()
