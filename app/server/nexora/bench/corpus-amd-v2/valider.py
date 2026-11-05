#!/usr/bin/env python3
"""Validateur autonome d'un corpus de briefs vidéo.

Bibliothèque standard uniquement. Aucun chemin absolu, aucun réseau.
Le schéma et les contraintes sont définis dans les constantes ci-dessous.

Usage :
    python3 valider.py corpus.json

API :
    validate(document, min_briefs=50) -> liste d'erreurs (vide si valide)

Les messages d'erreur n'exposent jamais le contenu des briefs (seulement
des chemins/index et des valeurs énumérées/métadonnées).
"""
import argparse
import json
import re
import sys

# --- Schéma du corpus proposé -------------------------------------------
SPLITS = ("construction", "validation", "test")
FAMILIES = (
    "publicité produit",
    "UGC",
    "marque",
    "fiction/dialogue",
    "documentaire/interview",
    "démonstration technique",
)
FORMATS = ("16:9", "9:16")
DURATIONS = (15, 30, 60)
LANGUAGES = ("fr", "en")
STATUS = "En préparation"
VOICE_APPROVAL = "pending_founder"
MEMORY_PROMOTION = "none"
ROOT_STATUS = "proposition non approuvée, en préparation"
OPTIONAL_STRING_FIELDS = {"compliance_note", "function_status_note", "intent", "intent_5s_en", "intention", "intention_5s", "notes", "notes_en", "on_screen_text_en", "pending", "product_notes", "real_world_direction_en", "unproven_features_note", "unproven_functions", "unsupported_functions"}
OPTIONAL_LIST_FIELDS = {"capabilities", "dialogues", "unproven_features"}
OPTIONAL_MAP_FIELDS = {"function_claims", "on_screen_function_note"}
MIN_CRITERIA = 2
BRIEF_ID_PREFIX = "AMD2-"

BRIEF_FIELDS = (
    "id", "campaign_id", "split", "theme", "family", "format", "duration_s",
    "language", "asset_ids", "description_en", "hook_5s", "dialogue",
    "on_screen_text", "real_world_direction", "observation_criteria",
    "status", "voice_approval", "memory_promotion",
)
ROOT_FIELDS = ("statut", "briefs")


def is_int(v):
    """Entier strict : bool n'est PAS un entier."""
    return isinstance(v, int) and not isinstance(v, bool)


def is_nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def is_valid_brief_id(v):
    return isinstance(v, str) and re.fullmatch(r"AMD2-[0-9]{3}", v) is not None


def _err(errors, path, code):
    errors.append(f"{path}: {code}")


def _check_enum(errors, path, value, allowed, code):
    if not isinstance(value, str) or value not in allowed:
        _err(errors, path, code)


def _validate_brief(brief, index, errors):
    base = f"briefs[{index}]"
    if not isinstance(brief, dict):
        _err(errors, base, "not_object")
        return None

    unknown = sorted(set(brief) - set(BRIEF_FIELDS) - OPTIONAL_STRING_FIELDS - OPTIONAL_LIST_FIELDS - OPTIONAL_MAP_FIELDS)
    for key in unknown:
        _err(errors, base, f"unknown_field:{key}")
    missing = [f for f in BRIEF_FIELDS if f not in brief]
    for key in missing:
        _err(errors, f"{base}.{key}", "missing")

    bid = brief.get("id")
    if "id" in brief and not is_valid_brief_id(bid):
        _err(errors, f"{base}.id", "invalid_brief_id")

    if "campaign_id" in brief and (not is_nonempty_str(brief["campaign_id"]) or brief["campaign_id"] != brief["campaign_id"].strip()):
        _err(errors, f"{base}.campaign_id", "expected_canonical_string")
    if "split" in brief:
        _check_enum(errors, f"{base}.split", brief["split"], SPLITS, "invalid_split")
    if "theme" in brief and not is_nonempty_str(brief["theme"]):
        _err(errors, f"{base}.theme", "expected_nonempty_string")
    if "family" in brief:
        _check_enum(errors, f"{base}.family", brief["family"], FAMILIES, "invalid_family")
    if "format" in brief:
        _check_enum(errors, f"{base}.format", brief["format"], FORMATS, "invalid_format")

    if "duration_s" in brief:
        d = brief["duration_s"]
        if not is_int(d) or d not in DURATIONS:
            _err(errors, f"{base}.duration_s", "invalid_duration_s")

    if "language" in brief:
        _check_enum(errors, f"{base}.language", brief["language"], LANGUAGES, "invalid_language")

    if "asset_ids" in brief:
        aids = brief["asset_ids"]
        if not isinstance(aids, list) or not aids:
            _err(errors, f"{base}.asset_ids", "expected_nonempty_array")
        else:
            for j, a in enumerate(aids):
                if not is_nonempty_str(a) or a != a.strip():
                    _err(errors, f"{base}.asset_ids[{j}]", "expected_canonical_string")

    for field in ("description_en", "hook_5s", "dialogue", "on_screen_text",
                  "real_world_direction"):
        if field in brief and not is_nonempty_str(brief[field]):
            _err(errors, f"{base}.{field}", "expected_nonempty_string")

    if "observation_criteria" in brief:
        crit = brief["observation_criteria"]
        if not isinstance(crit, list):
            _err(errors, f"{base}.observation_criteria", "expected_array")
        elif len(crit) < MIN_CRITERIA:
            _err(errors, f"{base}.observation_criteria", "too_few_criteria")
        else:
            for j, c in enumerate(crit):
                if not is_nonempty_str(c):
                    _err(errors, f"{base}.observation_criteria[{j}]",
                         "expected_nonempty_string")

    for field in OPTIONAL_STRING_FIELDS:
        if field in brief and not is_nonempty_str(brief[field]):
            _err(errors, f"{base}.{field}", "expected_nonempty_string")
    for field in OPTIONAL_LIST_FIELDS:
        if field in brief and (not isinstance(brief[field], list) or not brief[field]
                               or any(not is_nonempty_str(x) for x in brief[field])):
            _err(errors, f"{base}.{field}", "expected_nonempty_string_array")
    for field in OPTIONAL_MAP_FIELDS:
        if field in brief and (not isinstance(brief[field], dict) or not brief[field]
                               or any(not is_nonempty_str(k) or not is_nonempty_str(v)
                                      for k, v in brief[field].items())):
            _err(errors, f"{base}.{field}", "expected_nonempty_string_map")

    if "status" in brief and brief["status"] != STATUS:
        _err(errors, f"{base}.status", "invalid_status")
    if "voice_approval" in brief and brief["voice_approval"] != VOICE_APPROVAL:
        _err(errors, f"{base}.voice_approval", "invalid_voice_approval")
    if "memory_promotion" in brief and brief["memory_promotion"] != MEMORY_PROMOTION:
        _err(errors, f"{base}.memory_promotion", "invalid_memory_promotion")
    return brief


def _check_partition_leaks(briefs, errors):
    """Campagne (et asset) ne peut appartenir qu'à une seule partition."""
    campaign_splits = {}
    asset_splits = {}
    for index, brief in enumerate(briefs):
        if not isinstance(brief, dict):
            continue
        split = brief.get("split")
        if not isinstance(split, str):
            continue
        cid = brief.get("campaign_id")
        if is_nonempty_str(cid):
            campaign_splits.setdefault(cid, set()).add(split)
        aids = brief.get("asset_ids")
        if isinstance(aids, list):
            for a in aids:
                if is_nonempty_str(a):
                    asset_splits.setdefault(a, set()).add(split)
    for cid, splits in campaign_splits.items():
        if len(splits) > 1:
            _err(errors, "campaign_id", f"split_leak:{cid}")
    for aid, splits in asset_splits.items():
        if len(splits) > 1:
            _err(errors, "asset_ids", f"split_leak:{aid}")


def validate(document, min_briefs=50):
    """Valide un document corpus. Retourne la liste des erreurs (vide = valide).

    messages d'erreur n'incluent jamais le contenu textuel des briefs.
    """
    errors = []
    if not isinstance(document, dict):
        _err(errors, "$", "expected_object")
        return errors

    for key in sorted(set(document) - set(ROOT_FIELDS)):
        _err(errors, "$", f"unknown_field:{key}")
    for key in ROOT_FIELDS:
        if key not in document:
            _err(errors, key, "missing")

    if "statut" in document and document["statut"] != ROOT_STATUS:
        _err(errors, "statut", "invalid_root_status")

    briefs = document.get("briefs")
    if "briefs" not in document:
        return errors
    if not isinstance(briefs, list):
        _err(errors, "briefs", "expected_array")
        return errors
    if min_briefs is not None and len(briefs) < min_briefs:
        _err(errors, "briefs", f"too_few_briefs:min={min_briefs}")

    seen_ids = set()
    for index, brief in enumerate(briefs):
        _validate_brief(brief, index, errors)
        if isinstance(brief, dict):
            bid = brief.get("id")
            if isinstance(bid, str):
                if bid in seen_ids:
                    _err(errors, f"briefs[{index}].id", "duplicate_id")
                else:
                    seen_ids.add(bid)
    _check_partition_leaks(briefs, errors)
    return errors


def load_document(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Valide un corpus JSON de briefs (corpus.json).")
    parser.add_argument("corpus", help="chemin du fichier JSON à valider")
    parser.add_argument("--min-briefs", type=int, default=50,
                        help="nombre minimal de briefs (défaut : 50)")
    args = parser.parse_args(argv)

    try:
        document = load_document(args.corpus)
    except FileNotFoundError:
        print(f"ERREUR: fichier introuvable: {args.corpus}", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERREUR: lecture impossible ({type(exc).__name__})", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERREUR: JSON invalide (ligne {exc.lineno}, colonne {exc.colno})",
              file=sys.stderr)
        return 2

    errors = validate(document, min_briefs=args.min_briefs)
    if errors:
        for e in errors:
            print(f"ERREUR: {e}", file=sys.stderr)
        print(f"INVALIDE: {len(errors)} erreur(s)", file=sys.stderr)
        return 1
    print("VALIDE: corpus conforme")
    return 0


if __name__ == "__main__":
    sys.exit(main())
