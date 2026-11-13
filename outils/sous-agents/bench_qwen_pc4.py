#!/usr/bin/env python3
"""Banc d'essai Qwen pc4 : validation OpenAI, fenêtre utile et simultanéité (stdlib only)."""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

DEFAULT_BASE_URL = "http://192.168.1.161:8080/v1"
MAX_BODY = 8 * 1024 * 1024
HTTP_TIMEOUT = 300.0


# ---------------------------------------------------------------- HTTP
def normalize_base_url(raw: str) -> str:
    value = (raw or DEFAULT_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("URL invalide")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("URL ne doit contenir ni secret ni requête")
    path = parsed.path.rstrip("/")
    if not path.endswith("/v1"):
        path = (path + "/v1") if path else "/v1"
    netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
    return urllib.parse.urlunsplit((parsed.scheme, netloc, path, "", ""))


def root_from_base(base: str) -> str:
    return base[:-3] if base.endswith("/v1") else base


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _headers(token: str | None, accept: str = "application/json") -> dict[str, str]:
    headers = {"Accept": accept, "User-Agent": "bench-qwen-pc4/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def http_get_json(url: str, token: str | None, timeout: float = 15.0) -> tuple[int | None, Any, str]:
    req = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with _opener().open(req, timeout=timeout) as resp:
            status = resp.status
            body = resp.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        return exc.code, None, f"http_{exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return None, None, str(getattr(exc, "reason", exc))[:200]
    if len(body) > MAX_BODY:
        return status, None, "reponse_trop_volumineuse"
    try:
        return status, json.loads(body.decode("utf-8")), ""
    except (UnicodeDecodeError, json.JSONDecodeError):
        return status, None, "json_invalide"


class StreamResult(dict):
    pass


def post_chat(base: str, token: str | None, payload: dict[str, Any], timeout: float = HTTP_TIMEOUT) -> dict[str, Any]:
    """POST /chat/completions (stream=false). Retourne latences, usage, contenu."""
    url = f"{base}/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    headers = _headers(token)
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t0 = time.perf_counter()
    try:
        with _opener().open(req, timeout=timeout) as resp:
            body = resp.read(MAX_BODY + 1)
        total_ms = (time.perf_counter() - t0) * 1000.0
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http_{exc.code}", "total_ms": (time.perf_counter() - t0) * 1000.0}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"ok": False, "error": str(getattr(exc, "reason", exc))[:200], "total_ms": (time.perf_counter() - t0) * 1000.0}
    if len(body) > MAX_BODY:
        return {"ok": False, "error": "reponse_trop_volumineuse", "total_ms": total_ms}
    try:
        doc = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "error": "json_invalide", "total_ms": total_ms}
    choice = (doc.get("choices") or [{}])[0] if isinstance(doc, dict) else {}
    message = choice.get("message") or {}
    usage = doc.get("usage") or {}
    completion_tokens = usage.get("completion_tokens")
    tok_s = None
    if isinstance(completion_tokens, int) and completion_tokens > 0 and total_ms > 0:
        tok_s = round(completion_tokens / (total_ms / 1000.0), 2)
    return {
        "ok": True,
        "total_ms": round(total_ms, 1),
        "usage": usage,
        "model": doc.get("model"),
        "content": message.get("content") or "",
        "tool_calls": message.get("tool_calls") or [],
        "finish_reason": choice.get("finish_reason"),
        "tok_per_s": tok_s,
    }


def post_chat_stream(base: str, token: str | None, payload: dict[str, Any], timeout: float = HTTP_TIMEOUT) -> dict[str, Any]:
    """POST stream=true ; mesure ttft (1er contenu), durée stream, chunks SSE."""
    url = f"{base}/chat/completions"
    body_payload = dict(payload, stream=True)
    data = json.dumps(body_payload).encode("utf-8")
    headers = _headers(token, accept="text/event-stream")
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    t0 = time.perf_counter()
    ttft_ms: float | None = None
    chunks = 0
    parts: list[str] = []
    usage: dict[str, Any] = {}
    tool_calls: list[Any] = []
    finish_reason = None
    first_byte_ms: float | None = None
    try:
        with _opener().open(req, timeout=timeout) as resp:
            for raw_line in resp:
                if first_byte_ms is None:
                    first_byte_ms = (time.perf_counter() - t0) * 1000.0
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                payload_line = line[5:].strip()
                if payload_line == "[DONE]":
                    break
                try:
                    event = json.loads(payload_line)
                except json.JSONDecodeError:
                    continue
                chunks += 1
                if isinstance(event.get("usage"), dict):
                    usage = event["usage"]
                choices = event.get("choices") or []
                if not choices:
                    continue
                ch = choices[0]
                if ch.get("finish_reason"):
                    finish_reason = ch["finish_reason"]
                delta = ch.get("delta") or {}
                piece = delta.get("content")
                rpiece = delta.get("reasoning_content")
                if (piece or rpiece or delta.get("tool_calls")) and ttft_ms is None:
                    ttft_ms = (time.perf_counter() - t0) * 1000.0
                if piece:
                    parts.append(piece)
                if delta.get("tool_calls"):
                    tool_calls.extend(delta["tool_calls"])
        end_ms = (time.perf_counter() - t0) * 1000.0
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http_{exc.code}", "total_ms": round((time.perf_counter() - t0) * 1000.0, 1)}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"ok": False, "error": str(getattr(exc, "reason", exc))[:200], "total_ms": round((time.perf_counter() - t0) * 1000.0, 1)}

    text = "".join(parts)
    completion_tokens = usage.get("completion_tokens")
    stream_tok_s = None
    if isinstance(completion_tokens, int) and completion_tokens > 0 and ttft_ms is not None:
        gen_ms = end_ms - ttft_ms
        if gen_ms > 0:
            stream_tok_s = round(completion_tokens / (gen_ms / 1000.0), 2)
    return {
        "ok": True,
        "ttft_ms": round(ttft_ms, 1) if ttft_ms is not None else None,
        "first_byte_ms": round(first_byte_ms, 1) if first_byte_ms is not None else None,
        "total_ms": round(end_ms, 1),
        "chunks": chunks,
        "content": text,
        "usage": usage,
        "tool_calls": tool_calls,
        "finish_reason": finish_reason,
        "stream_tok_per_s": stream_tok_s,
    }


# ---------------------------------------------------------------- 1. validation
def validate_openai(base: str, token: str | None) -> dict[str, Any]:
    root = root_from_base(base)
    out: dict[str, Any] = {"base_url": base}

    h_status, h_doc, h_err = http_get_json(f"{root}/health", token)
    out["health"] = {"status": h_status, "body": h_doc if h_doc is not None else None, "error": h_err or None}

    m_status, m_doc, m_err = http_get_json(f"{base}/models", token)
    models: list[str] = []
    if isinstance(m_doc, dict) and isinstance(m_doc.get("data"), list):
        models = [str(it.get("id")) for it in m_doc["data"] if isinstance(it, dict) and it.get("id")]
    model_id = models[0] if models else None
    out["models"] = {"status": m_status, "models": models, "error": m_err or None, "model_id": model_id}

    p_status, p_doc, p_err = http_get_json(f"{root}/props", token)
    max_context = None
    total_slots = None
    if isinstance(p_doc, dict):
        dgs = p_doc.get("default_generation_settings") or {}
        max_context = dgs.get("n_ctx") or dgs.get("n_ctx_per_seq") or p_doc.get("n_ctx")
        total_slots = p_doc.get("total_slots") or p_doc.get("n_slots")
    out["props"] = {"status": p_status, "error": p_err or None,
                    "max_context": max_context, "total_slots": total_slots}
    out["max_context"] = max_context

    s_status, s_doc, s_err = http_get_json(f"{root}/slots", token)
    if s_status == 200 and isinstance(s_doc, list):
        running = sum(1 for s in s_doc if isinstance(s, dict) and s.get("is_processing"))
        out["slots"] = {"status": s_status, "count": len(s_doc), "processing": running}
        if total_slots is None:
            total_slots = len(s_doc)
    else:
        out["slots"] = {"status": s_status, "error": s_err or "indisponible"}
    out["total_slots"] = total_slots

    prompt = "Explique en une phrase courte ce qu'est un serveur d'inférence LLM."
    if not model_id:
        out["chat"] = {"ok": False, "error": "model_id_indisponible"}
        out["chat_stream"] = {"ok": False, "error": "model_id_indisponible"}
        out["tools"] = {"ok": False, "error": "model_id_indisponible"}
        out["ok"] = False
        return out

    chat_payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 384, "temperature": 0, "stream": False}
    chat = post_chat(base, token, chat_payload)
    out["chat"] = chat

    stream_payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 384, "temperature": 0, "stream": True,
                      "stream_options": {"include_usage": True}}
    out["chat_stream"] = post_chat_stream(base, token, stream_payload)

    out["tools"] = validate_tools(base, token, model_id)
    out["ok"] = all(
        out[k].get("ok") for k in ("chat", "chat_stream", "tools")
    ) and model_id is not None
    return out


TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_build_status",
            "description": "Retourne l'état du build CI pour une branche Git.",
            "parameters": {
                "type": "object",
                "properties": {"branch": {"type": "string", "description": "Nom de branche"}},
                "required": ["branch"],
            },
        },
    }
]


def _parse_json_args(raw: str) -> tuple[bool, Any]:
    try:
        return True, json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return False, None


def validate_tools(base: str, token: str | None, model_id: str) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "Tu es un assistant. Utilise les outils disponibles quand c'est pertinent."},
        {"role": "user", "content": "Quel est l'état du build sur la branche feature/login ? Appelle l'outil."},
    ]
    r1 = post_chat(base, token, {"model": model_id, "messages": messages, "tools": TOOLS_SPEC,
                                 "tool_choice": "auto", "max_tokens": 512, "temperature": 0})
    res: dict[str, Any] = {"ok": False, "turn1_ok": r1.get("ok", False), "turn1": r1}
    if not r1.get("ok"):
        res["error"] = r1.get("error", "tour1_echec")
        return res
    calls = r1.get("tool_calls") or []
    if not calls:
        res["error"] = "aucun_tool_call"
        return res
    call = calls[0]
    fn = call.get("function") or {}
    name = fn.get("name")
    valid_json, args = _parse_json_args(fn.get("arguments") or "")
    res["tool_call"] = {"id": call.get("id"), "name": name, "arguments_raw": fn.get("arguments"),
                        "arguments": args, "arguments_json_valid": valid_json,
                        "name_ok": name == "get_build_status",
                        "branch_ok": isinstance(args, dict) and isinstance(args.get("branch"), str) and bool(args["branch"])}
    if not (valid_json and res["tool_call"]["name_ok"] and res["tool_call"]["branch_ok"]):
        res["error"] = "tool_call_invalide"
        return res

    branch = args["branch"]
    tool_result = json.dumps({"branch": branch, "status": "success", "tests": "142/142", "duration_s": 73})
    messages2 = messages + [
        {"role": "assistant", "content": r1.get("content") or None, "tool_calls": calls},
        {"role": "tool", "tool_call_id": call.get("id"), "content": tool_result},
    ]
    r2 = post_chat(base, token, {"model": model_id, "messages": messages2, "tools": TOOLS_SPEC,
                                 "max_tokens": 512, "temperature": 0})
    res["turn2"] = r2
    if not r2.get("ok"):
        res["error"] = r2.get("error", "tour2_echec")
        return res
    text = (r2.get("content") or "").lower()
    coherent = bool(text) and not r2.get("tool_calls") and (
        branch.lower() in text or "succ" in text or "ok" in text or "142" in text or "pass" in text
    )
    res["turn2_content_coherent"] = coherent
    res["ok"] = coherent
    if not coherent:
        res["error"] = "reponse_finale_incoherente"
    return res


# ---------------------------------------------------------------- 2. fenêtre utile
FILLER_SENTENCE = (
    "Le rapport interne numéro {i} décrit les procédures logistiques de l'entrepôt, "
    "les horaires de livraison et les contrôles qualité associés. "
)


def build_canary_prompt(target_tokens: int, nonce: str = "PC4") -> dict[str, Any]:
    canary_start = f"CANARY-DEBUT-{nonce}-7Q9X"
    canary_end = f"CANARY-FIN-{nonce}-3M4Z"
    # ~4 caractères/token en français ; on vise target_tokens - marge.
    budget_chars = max(0, (target_tokens - 300)) * 4
    lines: list[str] = []
    size = 0
    i = 0
    while size < budget_chars:
        s = FILLER_SENTENCE.format(i=i)
        lines.append(s)
        size += len(s)
        i += 1
    body = "".join(lines)
    half = len(body) // 2
    prompt = (
        f"{canary_start}\n"
        f"{body[:half]}\n"
        f"{body[half:]}\n"
        f"{canary_end}\n"
        f"Réponds uniquement avec la valeur exacte du jeton de départ et du jeton de fin, "
        f"séparés par une virgule, sans aucun autre texte."
    )
    return {"prompt": prompt, "canary_start": canary_start, "canary_end": canary_end,
            "approx_chars": len(prompt)}


def check_canary(text: str, canary_start: str, canary_end: str) -> bool:
    return canary_start in (text or "") and canary_end in (text or "")


def run_context_window(base: str, token: str | None, model_id: str, sizes: list[int]) -> list[dict[str, Any]]:
    results = []
    for size in sizes:
        p = build_canary_prompt(size)
        payload = {"model": model_id, "messages": [{"role": "user", "content": p["prompt"]}],
                   "max_tokens": 384, "temperature": 0, "stream": True,
                   "chat_template_kwargs": {"enable_thinking": False},
                   "stream_options": {"include_usage": True}}
        r = post_chat_stream(base, token, payload)
        usage = r.get("usage") or {}
        entry = {
            "target_tokens": size,
            "ok": r.get("ok", False),
            "error": r.get("error"),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "ttft_ms": r.get("ttft_ms"),
            "total_ms": r.get("total_ms"),
            "canary_ok": check_canary(r.get("content", ""), p["canary_start"], p["canary_end"]) if r.get("ok") else False,
            "response": (r.get("content") or "")[:300],
        }
        results.append(entry)
    return results


# ---------------------------------------------------------------- 3. charge
def one_request(base: str, token: str | None, model_id: str, idx: int, max_tokens: int = 96) -> dict[str, Any]:
    prompt = (
        f"Requête {idx} : liste exactement trois avantages concrets de la rotation des clés API, "
        f"une ligne par avantage, en moins de 40 mots au total."
    )
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens, "temperature": 0, "stream": True,
               "chat_template_kwargs": {"enable_thinking": False},
               "stream_options": {"include_usage": True}}
    r = post_chat_stream(base, token, payload)
    usage = r.get("usage") or {}
    return {
        "idx": idx,
        "ok": r.get("ok", False),
        "error": r.get("error"),
        "ttft_ms": r.get("ttft_ms"),
        "total_ms": r.get("total_ms"),
        "completion_tokens": usage.get("completion_tokens"),
        "content_len": len(r.get("content") or ""),
    }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def run_concurrency(base: str, token: str | None, model_id: str, conc: int) -> dict[str, Any]:
    barrier = threading.Barrier(conc)

    def worker(idx: int) -> dict[str, Any]:
        barrier.wait()
        return one_request(base, token, model_id, idx)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=conc) as pool:
        futures = [pool.submit(worker, i) for i in range(conc)]
        rows = [f.result() for f in futures]
    wall_ms = (time.perf_counter() - t0) * 1000.0

    ok_rows = [r for r in rows if r["ok"]]
    totals = [r["total_ms"] for r in ok_rows if r.get("total_ms") is not None]
    ttfts = [r["ttft_ms"] for r in ok_rows if r.get("ttft_ms") is not None]
    tokens = sum(r.get("completion_tokens") or 0 for r in ok_rows)
    return {
        "concurrency": conc,
        "requests": conc,
        "errors": len(rows) - len(ok_rows),
        "error_rate": round((len(rows) - len(ok_rows)) / len(rows), 3) if rows else None,
        "p50_ms": round(percentile(totals, 50), 1) if totals else None,
        "max_ms": round(max(totals), 1) if totals else None,
        "min_ttft_ms": round(min(ttfts), 1) if ttfts else None,
        "max_ttft_ms": round(max(ttfts), 1) if ttfts else None,
        "agg_tok_per_s": round(tokens / (wall_ms / 1000.0), 2) if wall_ms > 0 else None,
        "completion_tokens": tokens,
        "wall_ms": round(wall_ms, 1),
        "rows": rows,
    }


def run_load(base: str, token: str | None, model_id: str, concurrencies: list[int]) -> list[dict[str, Any]]:
    results = []
    baseline = None
    for c in concurrencies:
        r = run_concurrency(base, token, model_id, c)
        if c == 1:
            baseline = r["p50_ms"]
        if baseline and r["p50_ms"]:
            r["degradation_factor_vs_c1"] = round(r["p50_ms"] / baseline, 2)
        else:
            r["degradation_factor_vs_c1"] = 1.0 if c == 1 and r["p50_ms"] else None
        results.append(r)
    return results


# ---------------------------------------------------------------- rapport
def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "oui" if v else "non"
    return str(v)


def render_markdown(report: dict[str, Any]) -> str:
    v = report.get("validation") or {}
    lines = ["# Banc Qwen pc4", "", f"- Base URL : `{report.get('base_url')}`", ""]
    lines.append("## 1. Validation OpenAI")
    lines.append("")
    health = v.get("health") or {}
    err = v.get("models", {}).get("error") or health.get("error")
    lines.append(f"- Health : {_fmt(health.get('status'))}" + (f" (erreur : {err})" if err and err not in ("json_invalide",) else ""))
    lines.append(f"- model_id : `{_fmt(v.get('models', {}).get('model_id'))}`")
    lines.append(f"- max_context : {_fmt(v.get('max_context'))}")
    lines.append(f"- total_slots : {_fmt(v.get('total_slots'))}")
    chat = v.get("chat") or {}
    lines.append(f"- chat (stream=false) : ok={_fmt(chat.get('ok'))} latence={_fmt(chat.get('total_ms'))} ms, "
                 f"tok/s={_fmt(chat.get('tok_per_s'))}, usage={_fmt(chat.get('usage'))}")
    st = v.get("chat_stream") or {}
    lines.append(f"- chat (stream=true) : ok={_fmt(st.get('ok'))} ttft={_fmt(st.get('ttft_ms'))} ms, "
                 f"chunks={_fmt(st.get('chunks'))}, stream_tok/s={_fmt(st.get('stream_tok_per_s'))}")
    tl = v.get("tools") or {}
    tc = tl.get("tool_call") or {}
    lines.append(f"- tools : ok={_fmt(tl.get('ok'))} name_ok={_fmt(tc.get('name_ok'))} "
                 f"json_valide={_fmt(tc.get('arguments_json_valid'))} branch={_fmt((tc.get('arguments') or {}).get('branch'))} "
                 f"final_coherent={_fmt(tl.get('turn2_content_coherent'))}")
    lines.append("")

    cw = report.get("context_window") or []
    if cw:
        lines.append("## 2. Fenêtre utile")
        lines.append("")
        lines.append("| cible | prompt_tokens | ttft_ms | total_ms | canary_ok |")
        lines.append("|---|---|---|---|---|")
        for r in cw:
            lines.append(f"| {r['target_tokens']} | {_fmt(r['prompt_tokens'])} | {_fmt(r['ttft_ms'])} | "
                         f"{_fmt(r['total_ms'])} | {_fmt(r['canary_ok'])} |")
        lines.append("")

    load = report.get("load") or []
    if load:
        lines.append("## 3. Simultanéité et charge")
        lines.append("")
        lines.append("| c | p50_ms | max_ms | min_ttft | max_ttft | agg_tok/s | err_rate | dégrad. vs c1 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in load:
            lines.append(f"| {r['concurrency']} | {_fmt(r['p50_ms'])} | {_fmt(r['max_ms'])} | {_fmt(r['min_ttft_ms'])} | "
                         f"{_fmt(r['max_ttft_ms'])} | {_fmt(r['agg_tok_per_s'])} | {_fmt(r['error_rate'])} | "
                         f"{_fmt(r['degradation_factor_vs_c1'])} |")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- clé
def load_token() -> str | None:
    try:
        mod_path = Path(__file__).resolve().parent
        if str(mod_path) not in sys.path:
            sys.path.insert(0, str(mod_path))
        import qwen_ctl  # type: ignore
        return qwen_ctl.load_strata_key()
    except Exception:  # noqa: BLE001
        pass
    val = os.environ.get("STRATA_API_KEY", "").strip()
    if val and val not in ("sk-strata-unconfigured", "sk-strata-local"):
        return val
    return None


def parse_int_list(raw: str) -> list[int]:
    return [int(x) for x in raw.split(",") if x.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("SA_QWEN_URL", DEFAULT_BASE_URL))
    parser.add_argument("--context-sizes", default="1024,4096,12288,24576")
    parser.add_argument("--concurrencies", default="1,2,3,4")
    parser.add_argument("--out", default=None, help="chemin du JSON de résultats")
    parser.add_argument("--timeout", type=float, default=300.0, help="timeout HTTP par requête (s)")
    parser.add_argument("--skip", default="", help="étapes à ignorer : validation,context,load")
    args = parser.parse_args(argv)

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    try:
        base = normalize_base_url(args.base_url)
    except ValueError as exc:
        print(f"erreur: {exc}", file=sys.stderr)
        return 2
    global HTTP_TIMEOUT
    token = load_token()

    report: dict[str, Any] = {"base_url": base, "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    model_id = None
    if "validation" not in skip:
        v = validate_openai(base, token)
        report["validation"] = v
        model_id = v.get("models", {}).get("model_id")
    else:
        _, m_doc, _ = http_get_json(f"{base}/models", token)
        if isinstance(m_doc, dict) and m_doc.get("data"):
            model_id = m_doc["data"][0].get("id")
        report["validation"] = {"models": {"model_id": model_id}, "ok": None}

    exit_ok = model_id is not None
    if model_id:
        if "context" not in skip:
            report["context_window"] = run_context_window(base, token, model_id, parse_int_list(args.context_sizes))
        if "load" not in skip:
            report["load"] = run_load(base, token, model_id, parse_int_list(args.concurrencies))
    report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if report.get("validation", {}).get("ok") is False:
        exit_ok = False

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Résultats JSON : {out_path}", file=sys.stderr)

    print(render_markdown(report))
    return 0 if exit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
