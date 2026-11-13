#!/usr/bin/env python3
"""score_20.py — vérificateur déterministe, apparié et objectif pour tasks_20.json.

Stdlib uniquement, sans réseau. Note chaque tâche sur 10 points.

Usage:
  python3 score_20.py --validate [--tasks tasks_20.json]
  python3 score_20.py --self-test [--tasks tasks_20.json]
  python3 score_20.py --workdir <dir> [--tasks tasks_20.json] [--task T01] [--json]
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TIMEOUT = 25

def get_path(obj, dotted):
    """Accède à obj via chemin pointé. Indices numériques pour listes. '[0]' supporté."""
    if dotted in (None, "", "."):
        return obj
    cur = obj
    for part in str(dotted).split("."):
        p = part.strip()
        if p.startswith("[") and p.endswith("]"):
            p = p[1:-1]
        if isinstance(cur, list):
            if not re.fullmatch(r"-?\d+", p):
                raise KeyError(f"index non numérique '{p}' sur liste")
            cur = cur[int(p)]
        elif isinstance(cur, dict):
            if p not in cur:
                raise KeyError(f"clé '{p}' absente")
            cur = cur[p]
        else:
            raise KeyError(f"chemin '{dotted}' bloqué sur scalaire")
    return cur

def _rp(workdir, path):
    p = os.path.join(workdir, path)
    if os.path.abspath(p) != p:
        pass
    # garde-fou: rester dans le workdir
    base = os.path.abspath(workdir)
    tgt = os.path.abspath(p)
    if tgt != base and not tgt.startswith(base + os.sep):
        raise ValueError(f"chemin hors workdir: {path}")
    return tgt

def ev_file_exists(check, workdir, task):
    rp = _rp(workdir, check["path"])
    ok = os.path.isfile(rp)
    return ok, ("présent" if ok else f"absent: {check['path']}")

def ev_json_valid(check, workdir, task):
    rp = _rp(workdir, check["path"])
    if not os.path.isfile(rp):
        return False, "fichier absent"
    try:
        with open(rp, encoding="utf-8") as f:
            json.load(f)
        return True, "JSON valide"
    except Exception as e:
        return False, f"JSON invalide: {e}"

def ev_json_equals(check, workdir, task):
    rp = _rp(workdir, check["path"])
    try:
        with open(rp, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        return False, f"lecture JSON impossible: {e}"
    try:
        val = get_path(doc, check.get("key")) if check.get("key") not in (None, "") else doc
    except KeyError as e:
        return False, f"clé introuvable: {e}"
    if val == check["expected"]:
        return True, "égal"
    return False, f"attendu {json.dumps(check['expected'], ensure_ascii=False)[:300]}, obtenu {json.dumps(val, ensure_ascii=False)[:300]}"

def ev_json_keys(check, workdir, task):
    rp = _rp(workdir, check["path"])
    try:
        with open(rp, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        return False, f"lecture JSON impossible: {e}"
    try:
        sub = get_path(doc, check.get("key")) if check.get("key") not in (None, "") else doc
    except KeyError as e:
        return False, f"clé introuvable: {e}"
    if isinstance(sub, dict):
        got = sorted(sub.keys())
    elif isinstance(sub, list):
        got = sub
        if check.get("ordered", False):
            pass
        else:
            try:
                got = sorted(got)
            except TypeError:
                got = list(got)
    else:
        return False, "cible ni objet ni liste"
    exp = sorted(check["expected"]) if not check.get("ordered", False) and isinstance(sub, list) else check["expected"]
    if isinstance(sub, dict):
        exp_cmp = sorted(check["expected"])
    else:
        exp_cmp = exp
        if not check.get("ordered", False):
            try:
                exp_cmp = sorted(check["expected"])
            except TypeError:
                pass
    if got == exp_cmp:
        return True, "clés/valeurs exactes"
    return False, f"attendu {exp_cmp}, obtenu {got}"

def ev_csv_headers(check, workdir, task):
    rp = _rp(workdir, check["path"])
    try:
        with open(rp, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except Exception as e:
        return False, f"lecture CSV impossible: {e}"
    if not rows:
        return False, "CSV vide"
    if rows[0] == check["expected"]:
        return True, "en-têtes exactes"
    return False, f"en-têtes attendues {check['expected']}, obtenues {rows[0]}"

def ev_csv_equals(check, workdir, task):
    rp = _rp(workdir, check["path"])
    try:
        with open(rp, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except Exception as e:
        return False, f"lecture CSV impossible: {e}"
    exp = [list(map(str, r)) for r in check["expected"]]
    if rows == exp:
        return True, "CSV exact"
    return False, f"attendu {exp[:10]}, obtenu {rows[:10]}"

def _read_text(workdir, path):
    rp = _rp(workdir, path)
    with open(rp, encoding="utf-8") as f:
        return f.read()

def ev_text_contains(check, workdir, task):
    try:
        t = _read_text(workdir, check["path"])
    except FileNotFoundError:
        return False, "fichier absent"
    subs = check["substrings"] if "substrings" in check else [check["substring"]]
    if check.get("case_insensitive"):
        t2 = t.lower()
        missing = [s for s in subs if s.lower() not in t2]
    else:
        missing = [s for s in subs if s not in t]
    if not missing:
        return True, "extraits présents"
    return False, f"manquants: {missing[:5]}"

def ev_text_not_contains(check, workdir, task):
    try:
        t = _read_text(workdir, check["path"])
    except FileNotFoundError:
        return False, "fichier absent"
    subs = check["substrings"] if "substrings" in check else [check["substring"]]
    found = [s for s in subs if s in t]
    if not found:
        return True, "aucun interdit"
    return False, f"interdits trouvés: {found[:5]}"

def ev_regex_match(check, workdir, task):
    try:
        t = _read_text(workdir, check["path"])
    except FileNotFoundError:
        return False, "fichier absent"
    flags = re.MULTILINE | re.DOTALL if check.get("dotall", True) else 0
    if re.search(check["pattern"], t, flags):
        return True, "motif trouvé"
    return False, f"motif absent: {check['pattern'][:120]}"

def ev_py_assert(check, workdir, task):
    code = check["code"]
    timeout = int(check.get("timeout", TIMEOUT))
    try:
        r = subprocess.run([sys.executable, "-c", code], cwd=workdir,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timeout {timeout}s (blocage/deadlock ?)"
    if r.returncode == 0:
        return True, "assertion OK"
    err = (r.stderr.strip() or r.stdout.strip())[-600:]
    return False, f"exit {r.returncode}: {err}"

def ev_unittest_pass(check, workdir, task):
    test_file = check["test_file"]
    min_tests = int(check.get("min_tests", 1))
    timeout = int(check.get("timeout", TIMEOUT))
    src = os.path.join(os.path.abspath(workdir), test_file)
    if not os.path.isfile(src):
        return False, f"fichier test absent: {test_file}"
    tmp = tempfile.mkdtemp(prefix="score20_")
    try:
        for name, content in (task.get("files") or {}).items():
            dest = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(dest) or tmp, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
        shutil.copy(src, os.path.join(tmp, os.path.basename(test_file)))
        mod = os.path.basename(test_file)
        if mod.endswith(".py"):
            mod = mod[:-3]
        r = subprocess.run([sys.executable, "-m", "unittest", mod, "-v"],
                           cwd=tmp, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        m = re.search(r"Ran (\d+) tests?", out)
        n = int(m.group(1)) if m else 0
        ok = r.returncode == 0 and "OK" in out and n >= min_tests
        if ok:
            return True, f"unittest OK ({n} tests)"
        return False, f"unittest échec (exit {r.returncode}, {n} tests, min {min_tests}): {out.strip()[-600:]}"
    except subprocess.TimeoutExpired:
        return False, f"timeout {timeout}s"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

EVALUATORS = {
    "file_exists": ev_file_exists,
    "json_valid": ev_json_valid,
    "json_equals": ev_json_equals,
    "json_keys": ev_json_keys,
    "csv_headers": ev_csv_headers,
    "csv_equals": ev_csv_equals,
    "text_contains": ev_text_contains,
    "text_not_contains": ev_text_not_contains,
    "regex_match": ev_regex_match,
    "py_assert": ev_py_assert,
    "unittest_pass": ev_unittest_pass,
}

def score_check(check, workdir, task):
    ctype = check.get("type")
    pts = int(check.get("points", 0))
    fn = EVALUATORS.get(ctype)
    if fn is None:
        return False, 0, f"type inconnu: {ctype}"
    try:
        ok, msg = fn(check, workdir, task)
    except Exception as e:
        ok, msg = False, f"erreur évaluateur: {e}"
    return ok, (pts if ok else 0), msg

def score_task(task, workdir):
    details = []
    total = 0
    for c in task.get("checks", []):
        ok, pts, msg = score_check(c, workdir, task)
        total += pts
        details.append({"type": c.get("type"), "points": c.get("points"),
                        "awarded": pts, "pass": ok, "message": msg,
                        "label": c.get("label", "")})
    total = max(0, min(10, total))
    return {"id": task["id"], "score": total, "max": 10, "route": task.get("expected_route"),
            "category": task.get("category"), "details": details}

def load_tasks(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        return data["tasks"]
    if isinstance(data, list):
        return data
    raise ValueError("format tasks invalide: liste ou {'tasks': [...]} attendu")

def validate_tasks(tasks):
    errors = []
    if not isinstance(tasks, list):
        return ["les tâches doivent former une liste"]
    if len(tasks) != 20:
        errors.append(f"20 tâches requises, trouvé {len(tasks)}")
    ids = [t.get("id") for t in tasks]
    if ids != [f"T{i:02d}" for i in range(1, 21)]:
        errors.append(f"ids attendus T01..T20 dans l'ordre, obtenus {ids}")
    eco = sum(1 for t in tasks if t.get("expected_route") == "eco-qwen")
    hors = sum(1 for t in tasks if t.get("expected_route") == "hors-qwen")
    if eco != 14 or hors != 6:
        errors.append(f"répartition attendue 14 eco-qwen / 6 hors-qwen, obtenue {eco}/{hors}")
    hors_ids = [t.get("id") for t in tasks if t.get("expected_route") == "hors-qwen"]
    if hors_ids != [f"T{i:02d}" for i in range(15, 21)]:
        errors.append(f"hors-qwen attendus T15..T20, obtenus {hors_ids}")
    for t in tasks:
        tid = t.get("id", "?")
        for k in ("id", "category", "expected_route", "files", "prompt", "checks"):
            if k not in t:
                errors.append(f"{tid}: champ manquant '{k}'")
        if not isinstance(t.get("files"), dict) or not t["files"]:
            errors.append(f"{tid}: 'files' doit être un dict non vide")
        if not isinstance(t.get("prompt"), str) or len(t["prompt"]) < 50:
            errors.append(f"{tid}: 'prompt' trop court ou absent")
        if t.get("expected_route") not in ("eco-qwen", "hors-qwen"):
            errors.append(f"{tid}: expected_route invalide")
        checks = t.get("checks", [])
        if not isinstance(checks, list) or not checks:
            errors.append(f"{tid}: 'checks' doit être une liste non vide")
            continue
        s = sum(int(c.get("points", 0)) for c in checks)
        if s != 10:
            errors.append(f"{tid}: somme des points = {s}, attendu 10")
        for c in checks:
            if c.get("type") not in EVALUATORS:
                errors.append(f"{tid}: type de check inconnu '{c.get('type')}'")
            if int(c.get("points", -1)) < 0:
                errors.append(f"{tid}: points négatifs")
    return errors

def self_test(tasks_path):
    results = []
    def ok(name, cond, info=""):
        results.append((name, bool(cond), info))
    # 1. get_path
    try:
        ok("get_path dict/liste", get_path({"a": [{"b": 1}]}, "a.0.b") == 1)
        ok("get_path [i]", get_path({"a": [10, 20]}, "a.[1]") == 20)
        try:
            get_path({"a": 1}, "a.zzz"); ok("get_path manque", False)
        except KeyError:
            ok("get_path manque", True)
    except Exception as e:
        ok("get_path", False, str(e))
    # 2. évaluateurs statiques sur tmp
    tmp = tempfile.mkdtemp(prefix="selftest20_")
    try:
        with open(os.path.join(tmp, "d.json"), "w", encoding="utf-8") as f:
            json.dump({"x": 1, "lst": [{"ip": "a"}]}, f)
        with open(os.path.join(tmp, "t.csv"), "w", newline="", encoding="utf-8") as f:
            f.write("a,b\n1,2\n")
        with open(os.path.join(tmp, "t.txt"), "w", encoding="utf-8") as f:
            f.write("hello workspace {count} %s")
        dummy = {"files": {}}
        ok("file_exists OK", ev_file_exists({"path": "d.json"}, tmp, dummy)[0])
        ok("file_exists KO", not ev_file_exists({"path": "nope"}, tmp, dummy)[0])
        ok("json_valid OK", ev_json_valid({"path": "d.json"}, tmp, dummy)[0])
        ok("json_equals OK", ev_json_equals({"path": "d.json", "key": "x", "expected": 1}, tmp, dummy)[0])
        ok("json_equals KO borne", not ev_json_equals({"path": "d.json", "key": "x", "expected": 2}, tmp, dummy)[0])
        ok("json vide borne inf/sup",
           ev_json_equals({"path": "d.json", "key": "lst.0.ip", "expected": "a"}, tmp, dummy)[0])
        ok("json_keys OK", ev_json_keys({"path": "d.json", "expected": ["lst", "x"]}, tmp, dummy)[0])
        ok("json_keys KO", not ev_json_keys({"path": "d.json", "expected": ["x"]}, tmp, dummy)[0])
        ok("csv_headers OK", ev_csv_headers({"path": "t.csv", "expected": ["a", "b"]}, tmp, dummy)[0])
        ok("csv_equals OK", ev_csv_equals({"path": "t.csv", "expected": [["a", "b"], ["1", "2"]]}, tmp, dummy)[0])
        ok("csv_equals KO", not ev_csv_equals({"path": "t.csv", "expected": [["a", "b"], ["9", "9"]]}, tmp, dummy)[0])
        ok("text_contains OK", ev_text_contains({"path": "t.txt", "substring": "workspace"}, tmp, dummy)[0])
        ok("text_not_contains OK", ev_text_not_contains({"path": "t.txt", "substring": "zzz"}, tmp, dummy)[0])
        ok("text_not_contains KO", not ev_text_not_contains({"path": "t.txt", "substring": "hello"}, tmp, dummy)[0])
        ok("regex OK", ev_regex_match({"path": "t.txt", "pattern": r"\{count\}"}, tmp, dummy)[0])
        ok("py_assert OK", ev_py_assert({"code": "assert 1+1==2"}, tmp, dummy)[0])
        ok("py_assert KO", not ev_py_assert({"code": "assert 1==2"}, tmp, dummy)[0])
        ok("py_assert borne 0..10", True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # 3. unittest_pass (positif + négatif), sans réseau
    tmp2 = tempfile.mkdtemp(prefix="selftest20u_")
    try:
        task_u = {"files": {"mod_u.py": "def f(x):\n    return x*2\n"}}
        with open(os.path.join(tmp2, "test_u.py"), "w", encoding="utf-8") as f:
            f.write("import unittest\nimport mod_u\nclass T(unittest.TestCase):\n"
                    "    def test_a(self):\n        self.assertEqual(mod_u.f(2),4)\n"
                    "    def test_b(self):\n        self.assertEqual(mod_u.f(0),0)\n")
        ok("unittest_pass OK", ev_unittest_pass({"test_file": "test_u.py", "min_tests": 2}, tmp2, task_u)[0])
        with open(os.path.join(tmp2, "test_bad.py"), "w", encoding="utf-8") as f:
            f.write("import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertEqual(1,2)\n")
        ok("unittest_pass KO détecté", not ev_unittest_pass({"test_file": "test_bad.py", "min_tests": 1}, tmp2, {"files": {}})[0])
        ok("unittest_pass min_tests", not ev_unittest_pass({"test_file": "test_u.py", "min_tests": 99}, tmp2, task_u)[0])
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)
    # 4. plafonnement 0..10 et bornes
    t = {"id": "TX", "expected_route": "eco-qwen", "category": "x", "files": {},
         "checks": [{"type": "py_assert", "code": "assert True", "points": 7},
                    {"type": "py_assert", "code": "assert True", "points": 7}]}
    r = score_task(t, tempfile.gettempdir())
    ok("plafond 10", r["score"] == 10, str(r["score"]))
    t2 = {"id": "TX", "expected_route": "eco-qwen", "category": "x", "files": {},
          "checks": [{"type": "py_assert", "code": "assert False", "points": 10}]}
    ok("plancher 0", score_task(t2, tempfile.gettempdir())["score"] == 0)
    # 5. tasks_20.json réel
    try:
        tasks = load_tasks(tasks_path)
        errs = validate_tasks(tasks)
        ok("tasks_20.json 20 tâches valides", not errs, "; ".join(errs)[:800])
        # vérifie distribution + somme points déjà dans validate; re-vérifie bornes
        per = []
        for task in tasks:
            s = sum(int(c.get("points", 0)) for c in task["checks"])
            per.append(s == 10)
        ok("chaque tâche totalise 10", all(per))
        # aucun appel réseau dans ce vérificateur
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "score_20.py"), encoding="utf-8") as f:
            src = f.read()
        ok("sans réseau", not re.search(r"\b(socket|requests|urllib\.request|http\.client)\b", src))
    except Exception as e:
        ok("tasks_20.json chargeable", False, str(e))
    n_ok = sum(1 for _, c, _ in results if c)
    print(f"SELF-TEST: {n_ok}/{len(results)} assertions OK (sans réseau, déterministe)")
    for name, c, info in results:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}" + (f" — {info}" if info and not c else ""))
    return 0 if n_ok == len(results) else 1

def main():
    ap = argparse.ArgumentParser(description="Vérificateur déterministe tasks_20 (stdlib, sans réseau).")
    ap.add_argument("--tasks", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks_20.json"))
    ap.add_argument("--workdir", default=".")
    ap.add_argument("--task", default=None, help="ex: T01")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test(a.tasks))
    tasks = load_tasks(a.tasks)
    if a.validate:
        errs = validate_tasks(tasks)
        if errs:
            print(f"TASKS INVALIDES ({len(errs)} erreurs):")
            for e in errs:
                print(f"  - {e}")
            sys.exit(1)
        print("TASKS VALIDES: 20 tâches T01..T20, 14 eco-qwen (T01..T14) + 6 hors-qwen (T15..T20), 10 pts/tâche.")
        sys.exit(0)
    if a.task:
        tasks = [t for t in tasks if t["id"] == a.task]
        if not tasks:
            print(f"tâche inconnue: {a.task}", file=sys.stderr)
            sys.exit(2)
    out = [score_task(t, a.workdir) for t in tasks]
    tot = sum(r["score"] for r in out)
    eco = sum(r["score"] for r in out if r["route"] == "eco-qwen")
    hors = sum(r["score"] for r in out if r["route"] == "hors-qwen")
    if a.json:
        print(json.dumps({"results": out, "total": tot, "max": 10 * len(out),
                          "eco_qwen": eco, "eco_qwen_max": 14 * 10,
                          "hors_qwen": hors, "hors_qwen_max": 6 * 10}, ensure_ascii=False, indent=2))
    else:
        for r in out:
            print(f"{r['id']} [{r['route']}] {r['score']}/10 ({r['category']})")
            for d in r["details"]:
                mark = "ok" if d["pass"] else "KO"
                print(f"    [{mark}] +{d['awarded']}/{d['points']} {d['type']}: {d['message'][:160]}")
        print(f"TOTAL {tot}/{10*len(out)} | eco-qwen {eco}/140 | hors-qwen {hors}/60")

if __name__ == "__main__":
    main()
