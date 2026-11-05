"""Journal JSONL des appels (comptes de jetons, coût, durée) — jamais les prompts ni les réponses."""
import json, os, time
from litellm.integrations.custom_logger import CustomLogger

LOG = os.environ.get("SA_LOG", "/app/state/usage.jsonl")


def _hdr(kwargs, name):
    md = (kwargs.get("litellm_params") or {}).get("metadata") or {}
    h = md.get("headers") or {}
    return h.get(name) or h.get(name.title())


def _write(rec):
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


class SaLogger(CustomLogger):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        # L'effort de raisonnement et le point de terminaison sont fixés par config.yaml (extra_body) : on retire ceux que
        # le client (claude) ajoute, sinon OpenRouter reçoit deux valeurs contradictoires (reasoning_effort et reasoning.effort).
        if isinstance(data, dict) and str(data.get("model", "")).startswith("eco-"):
            for k in ("reasoning_effort", "reasoning", "thinking", "output_config"):
                data.pop(k, None)
        return data

    def _rec(self, kwargs, resp, start, end, ok):
        usage = {}
        try:
            u = getattr(resp, "usage", None) or (resp.get("usage") if isinstance(resp, dict) else None)
            if u is not None:
                g = (lambda k: getattr(u, k, None) if not isinstance(u, dict) else u.get(k))
                usage = {
                    "in": g("prompt_tokens") or g("input_tokens") or 0,
                    "out": g("completion_tokens") or g("output_tokens") or 0,
                }
        except Exception:
            pass
        return {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "run": _hdr(kwargs, "x-sa-run"),
            "alias": ((kwargs.get("litellm_params") or {}).get("metadata") or {}).get("model_group") or kwargs.get("model"),
            "ok": ok,
            "in": usage.get("in", 0),
            "out": usage.get("out", 0),
            "cost": kwargs.get("response_cost") or 0,
            "sec": round((end - start).total_seconds(), 2),
        }

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        _write(self._rec(kwargs, response_obj, start_time, end_time, True))

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        r = self._rec(kwargs, None, start_time, end_time, False)
        r["err"] = str(kwargs.get("exception"))[:160]
        _write(r)


proxy_handler_instance = SaLogger()
