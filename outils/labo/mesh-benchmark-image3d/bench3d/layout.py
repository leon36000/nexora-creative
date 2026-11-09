"""Deterministic planning: public bench plan + blind review plan + local key.

Two kinds of artefacts are produced, deliberately separated:

* Blind artefacts (safe to hand to a human or an external judge):
  - blind_plan.json  : per review unit (subject x arm), a random opaque label
                       (A, B, C, ...) with the arm name REMOVED.
  - layout.csv       : flat review sheet, same anonymised labels.
* Local artefacts (must stay private, never shipped with outputs under review):
  - mapping_key.json : random label -> arm id/label, plus seed + layout digest.

No quality score is produced: ordering inside a unit is the seeded shuffle,
not a ranking. This tool does not compare model quality.
"""
from __future__ import annotations

import hashlib
import json
import random
import string
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .manifest import Manifest

PLAN_VERSION = 1


class LayoutError(ValueError):
    pass


def _digest(manifest: Manifest) -> str:
    """Fingerprint of manifest-relevant content (order-insensitive on lists)."""
    payload = {
        "arms": sorted([a.id, a.label, a.kind or ""] for a in manifest.arms),
        "subjects": sorted([s.id, s.image_rel, s.sha256, s.category or ""]
                           for s in manifest.subjects),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _labels_for(n_arms: int) -> List[str]:
    """Opaque labels: A..Z then AA, AB... Bounded to avoid ambiguity."""
    letters = string.ascii_uppercase
    labels: List[str] = []
    if n_arms <= 26:
        return list(letters[:n_arms])
    overflow = n_arms - 26
    labels = list(letters)
    for i in range(overflow):
        labels.append(letters[i // 26] + letters[i % 26])
    return labels


@dataclass
class Layout:
    seed: int
    plan: Dict[str, Any]
    blind_plan: Dict[str, Any]
    mapping_key: Dict[str, Any]
    layout_csv: str


def build_layout(manifest: Manifest, seed: Optional[int] = None) -> Layout:
    """Build the plan/mapping. Deterministic for a given (manifest, seed)."""
    if seed is None:
        seed = manifest.seed
    if seed is None:
        raise LayoutError("no seed: pass --seed or set 'seed' in the manifest")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise LayoutError("seed must be an integer")
    if not manifest.arms or not manifest.subjects:
        raise LayoutError("manifest has no arms or no subjects")

    # Sort for order-independence, then shuffle with a seed derived from
    # (seed, arm id) so each subject gets its own reproducible permutation.
    # Using per-subject RNG keyed by subject id keeps layout stable when a
    # subject is added/removed elsewhere.
    arm_ids = sorted(a.id for a in manifest.arms)
    op = _labels_for(len(arm_ids))

    units: List[Dict[str, Any]] = []
    blind_units: List[Dict[str, Any]] = []
    key_entries: List[Dict[str, Any]] = []
    csv_rows = ["subject_id,blind_label,review_order,image_file"]

    for subj in sorted(manifest.subjects, key=lambda s: s.id):
        # filename prefix is a short hash of the subject id (deterministic,
        # does not leak arm names).
        subject_token = hashlib.sha256(
            ("%s|%s" % (seed, subj.id)).encode("utf-8")
        ).hexdigest()[:10]
        rng = random.Random("bench3d|%d|%s" % (seed, subj.id))
        shuffled = arm_ids[:]
        rng.shuffle(shuffled)
        for position, arm_id in enumerate(shuffled, start=1):
            unit_id = "u-%s-%02d" % (subject_token, position)
            label = op[position - 1]
            units.append({
                "unit_id": unit_id,
                "subject_id": subj.id,
                "arm_id": arm_id,              # public plan (local use)
                "review_order": position,
                "blind_label": label,
            })
            # blind row: NO arm name, NO score, opaque label
            blind_file = "%s/%s.png" % (unit_id, label)
            blind_units.append({
                "unit_id": unit_id,
                "subject_id": subj.id,
                "blind_label": label,
                "expected_output": blind_file,
            })
            key_entries.append({
                "unit_id": unit_id,
                "subject_id": subj.id,
                "blind_label": label,
                "arm_id": arm_id,
            })
            csv_rows.append(",".join([
                _csv(subj.id), _csv(label),
                str(position), _csv(blind_file),
            ]))

    layout_digest = _digest(manifest)
    common = {
        "plan_version": PLAN_VERSION,
        "seed": seed,
        "n_subjects": len(manifest.subjects),
        "n_arms": len(manifest.arms),
        "n_units": len(units),
        "manifest_digest": layout_digest,
        "manifest_file_sha256": manifest.source_sha256,
    }
    plan = dict(common, kind="public_plan",
                arms=[{"id": a.id, "label": a.label, "kind": a.kind} for a in manifest.arms],
                subjects=[{"id": s.id, "image": s.image_rel, "sha256": s.sha256,
                           "bytes": s.size, "category": s.category} for s in manifest.subjects],
                units=units)
    blind_common = {k: v for k, v in common.items() if k not in ("seed", "manifest_digest", "manifest_file_sha256")}
    blind_plan = dict(blind_common, kind="blind_review_plan",
                      instructions="Blind review only. Labels are anonymous. "
                                   "No quality score is generated; any ordering "
                                   "is random, not a ranking.",
                      units=blind_units)
    mapping_key = dict(common, kind="local_answer_key",
                       warning="PRIVATE: do NOT ship with the blind outputs.",
                       mapping=key_entries)
    return Layout(seed=seed, plan=plan, blind_plan=blind_plan,
                  mapping_key=mapping_key, layout_csv="\n".join(csv_rows) + "\n")


def _csv(value: str) -> str:
    if any(c in value for c in ',"\n\r'):
        return '"' + value.replace('"', '""') + '"'
    return value


def mapping_from_key(key: Dict[str, Any]) -> Dict[str, str]:
    """Invert the local key into {'unit_id': arm_id} for scoring later."""
    return {entry["unit_id"]: entry["arm_id"] for entry in key["mapping"]}
