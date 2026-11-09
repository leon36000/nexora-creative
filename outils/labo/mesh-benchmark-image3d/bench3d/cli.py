"""Command-line entry point: prepare (validate + plan) and verify-key."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .layout import LayoutError, build_layout
from .manifest import ManifestError, load_manifest, _refuse_sensitive_path
from .outputs import dumps, prepare_outdir, relative_portable, write_exclusive

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_MANIFEST = 2
EXIT_USAGE = 64
EXIT_EXISTS = 65


def _write_stdout(text: str) -> None:
    sys.stdout.write(text)


def _write_stderr(text: str) -> None:
    sys.stderr.write(text)


def cmd_prepare(args: argparse.Namespace) -> int:
    try:
        manifest = load_manifest(Path(args.manifest))
    except ManifestError as exc:
        _write_stderr("manifest error:\n")
        for p in exc.problems:
            _write_stderr("  - %s\n" % p)
        return EXIT_MANIFEST
    try:
        layout = build_layout(manifest, args.seed)
    except LayoutError as exc:
        _write_stderr("planning error: %s\n" % exc)
        return EXIT_USAGE

    payloads = {
        "plan.json": dumps(layout.plan),
        "blind_plan.json": dumps(layout.blind_plan),
        "mapping_key.json": dumps(layout.mapping_key),
        "layout.csv": layout.layout_csv,
    }

    if args.stdout:
        # Print the blind submission + info to stdout, key to stderr? No:
        # key must never be mixed with the blind stream. Print only blind plan.
        _write_stdout(dumps(layout.blind_plan))
        _write_stderr("note: mapping key NOT printed to stdout on purpose; "
                      "use a directory output to obtain it.\n")
        return EXIT_OK

    if not args.out:
        _write_stderr("error: --out DIR is required (or use --stdout for a preview)\n")
        return EXIT_USAGE
    try:
        out_dir = prepare_outdir(Path(args.out), inputs=[manifest.path])
    except OSError as exc:
        _write_stderr("error: %s\n" % exc)
        return EXIT_EXISTS

    created = []
    try:
        for name, text in payloads.items():
            target = out_dir / name
            write_exclusive(target, text)
            created.append(target)
    except OSError as exc:
        _write_stderr("error: %s\n(partial outputs kept for inspection)\n" % exc)
        return EXIT_EXISTS

    for t in created:
        _write_stdout("%s\n" % relative_portable(t, out_dir))
    _write_stderr(
        "ok: %d units, %d subjects x %d arms; seed=%d\n"
        "IMPORTANT: keep mapping_key.json private; blind_plan.json is the "
        "submission. No model was run; no quality was compared.\n"
        % (layout.plan["n_units"], layout.plan["n_subjects"], layout.plan["n_arms"],
           layout.seed)
    )
    return EXIT_OK


def cmd_verify_key(args: argparse.Namespace) -> int:
    try:
        key_path = Path(args.key)
        _refuse_sensitive_path(key_path)
        _refuse_sensitive_path(key_path.resolve())
        key = json.loads(key_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _write_stderr("error: cannot read key: %s\n" % exc)
        return EXIT_ERROR
    if not isinstance(key, dict) or key.get("kind") != "local_answer_key":
        _write_stderr("error: not a mapping key file\n")
        return EXIT_ERROR
    units = key.get("mapping")
    if not isinstance(units, list) or not units or any(
        not isinstance(u, dict) or any(not isinstance(u.get(k), str) or not u[k] for k in ("unit_id", "subject_id", "blind_label", "arm_id"))
        for u in units
    ):
        _write_stderr("error: invalid mapping key structure\n")
        return EXIT_ERROR
    units_ids = [u["unit_id"] for u in units]
    labels = {}
    problems = []
    for u in units:
        s = u["subject_id"]
        if u["blind_label"] in labels.get(s, set()):
            problems.append("duplicate label %s for subject %s" % (u["blind_label"], s))
        labels.setdefault(s, set()).add(u["blind_label"])
    if len(set(units_ids)) != len(units_ids):
        problems.append("duplicate unit ids")
    if problems:
        for p in problems:
            _write_stderr("  - %s\n" % p)
        return EXIT_ERROR
    _write_stdout(dumps({"ok": True, "n_units": len(units),
                         "n_subjects": len(labels),
                         "seed": key.get("seed"),
                         "manifest_digest": key.get("manifest_digest")}))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m bench3d",
        description="Prepare an image->3D blind review bench. Does NOT run models "
                    "and does NOT compare quality.",
    )
    p.add_argument("--version", action="version", version="bench3d " + __version__)
    sub = p.add_subparsers(dest="command", required=True)

    pp = sub.add_parser("prepare", help="validate manifest and write plan/key")
    pp.add_argument("manifest", help="path to manifest JSON")
    pp.add_argument("--out", help="existing or new output directory (exclusive files)")
    pp.add_argument("--seed", type=int, help="override seed (must be explicit for a fresh run)")
    pp.add_argument("--stdout", action="store_true",
                    help="print the blind plan only to stdout (no files, no key)")
    pp.set_defaults(func=cmd_prepare)

    pk = sub.add_parser("verify-key", help="sanity-check a mapping key file")
    pk.add_argument("key")
    pk.set_defaults(func=cmd_verify_key)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
