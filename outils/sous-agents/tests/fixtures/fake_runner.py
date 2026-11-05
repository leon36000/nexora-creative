#!/usr/bin/env python3
"""Offline launcher simulator. Prompts contain only test directives."""
import fcntl
import json
import os
import re
import sys
import time
from pathlib import Path


def locked_update(path: Path, update):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        current = json.loads(stream.read() or "{}")
        value = update(current)
        stream.seek(0)
        stream.truncate()
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
        fcntl.flock(stream, fcntl.LOCK_UN)


def write_journal(journal, mode, run_id, cost, alias):
    if mode == "CORRUPT":
        with journal.open("a", encoding="utf-8") as stream:
            stream.write('{"cost":\n')
    elif mode in {"TAGGED_COST", "OVER_BOUNDARY_TAGGED"}:
        parts = (("0.004", "0.006") if mode == "TAGGED_COST" else
                 ("0.1", "0.20000000000000000000000000000000000000000000000001"))
        for sequence, part in enumerate(parts, start=1):
            tagged_run = f"{run_id}--p0123456789abcdef--c{sequence}"
            if mode == "OVER_BOUNDARY_TAGGED":
                record = (f'{{"run":{json.dumps(tagged_run)},"cost":{part},'
                          f'"alias":{json.dumps(alias)},"ok":true}}')
            else:
                row = {"run": tagged_run, "cost": float(part), "alias": alias, "ok": True}
                record = json.dumps(row)
            with journal.open("a", encoding="utf-8") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX)
                stream.write(record + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                fcntl.flock(stream, fcntl.LOCK_UN)
    elif mode == "UNATTRIBUTED":
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"cost": 0.01}) + "\n")
    elif mode == "NO_FINAL_LF":
        row = {"run": run_id, "cost": float(cost), "alias": alias, "ok": True}
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row))
    elif mode != "NO_COST":
        recorded_cost = None if mode == "UNKNOWN_COST" else float(cost)
        row = {"run": run_id, "cost": recorded_cost, "alias": alias, "ok": True}
        with journal.open("a", encoding="utf-8") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            fcntl.flock(stream, fcntl.LOCK_UN)


def main():
    args = sys.argv[1:]
    if len(args) != 6 or args[0] != "-w":
        return 2
    _, alias, prompt_arg, _, _, _ = args
    prompt = Path(prompt_arg)
    name = prompt.name.rsplit(".", 1)[0]
    directives = prompt.read_text(encoding="utf-8")

    def match(pattern, default):
        found = re.search(pattern, directives)
        return found.group(1) if found else default

    delay = float(match(r"DELAY=([0-9.]+)", "0.08"))
    cost = match(r"COST=([0-9.]+)", "0.01")
    mode = match(r"MODE=([A-Z_]+)", "OK")
    rc = int(match(r"RC=(-?[0-9]+)", "0"))
    counter = Path(os.environ["FAKE_COUNTER"])

    def increment(obj):
        obj["active"] = int(obj.get("active", 0)) + 1
        obj["max_active"] = max(int(obj.get("max_active", 0)), obj["active"])
        obj.setdefault("started", []).append(name)
        return obj

    locked_update(counter, increment)
    out = Path(os.environ["SA_OUT"])
    out.mkdir(parents=True, mode=0o700)
    run_id = (f"{os.environ['SA_TAG']}-shared-fake" if mode == "DUPLICATE_RUN_ID"
              else f"{os.environ['SA_TAG']}-{name}-fake")
    (out / "meta.json").write_text(json.dumps({"run": run_id}), encoding="utf-8")
    print(str(out), flush=True)
    time.sleep(delay)

    journal = Path(os.environ["SA_STATE"]) / "usage.jsonl"
    write_journal(journal, mode, run_id, cost, alias)

    summary = "FAIL:fake" if mode == "FAIL_SUMMARY" else "OK:fake"
    print(f"{summary} {alias} {run_id} tours=1 cout=${cost} jetons=1in/1out/1req duree=0s dossier={out}", flush=True)

    def decrement(obj):
        obj["active"] = max(0, int(obj.get("active", 1)) - 1)
        return obj

    locked_update(counter, decrement)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
