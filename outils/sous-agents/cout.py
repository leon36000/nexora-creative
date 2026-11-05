#!/usr/bin/env python3
"""Sommes déclarées par la passerelle, sans lire ni imprimer de prompts ou clés."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal, DecimalException, InvalidOperation, ROUND_HALF_UP, getcontext
from pathlib import Path

# Enough precision for bounded input values and realistic journal sizes.
getcontext().prec = 128


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def number(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if (result.is_finite() and result >= 0 and len(result.as_tuple().digits) <= 64
                      and (result.is_zero() or -30 <= result.adjusted() <= 30)) else None


def aggregate(rows: list[dict]) -> dict:
    costs = [number(row.get('cost')) for row in rows]
    def tokens(value):
        n = number(value)
        return n if n is not None and n == n.to_integral_value() else None
    ins = [tokens(row.get('in')) for row in rows]
    outs = [tokens(row.get('out')) for row in rows]
    missing = sum(x is None for x in costs)
    return {
        'requetes': len(rows),
        'echecs': sum(row.get('ok') is False for row in rows),
        'statuts_inconnus': sum(not isinstance(row.get('ok'), bool) for row in rows),
        'in': str(sum(ins, Decimal(0))) if rows and all(x is not None for x in ins) else None,
        'out': str(sum(outs, Decimal(0))) if rows and all(x is not None for x in outs) else None,
        'cout_connu': str(sum((x for x in costs if x is not None), Decimal(0))),
        'couts_inconnus': missing,
        'cout_total': None if missing or not rows else str(sum(costs, Decimal(0))),
    }


def money(amount: str) -> str:
    try:
        return str(Decimal(amount).quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP))
    except InvalidOperation:
        # A very large recorded number stays visible rather than being silently replaced with zero.
        return amount


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--since', default='')
    parser.add_argument('--run', default='', help='identifiant exact ou identifiant de lot suivi de ses runs')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.since:
        try:
            parsed = date.fromisoformat(args.since)
            if parsed.isoformat() != args.since:
                raise ValueError
        except ValueError:
            parser.error('--since doit être une date AAAA-MM-JJ valide')
    try:
        state = os.environ.get('SA_STATE')
        path = (Path(state) if state else Path.home() / '.local/share/nexora-sous-agents') / 'usage.jsonl'
        rows = []
        with path.open(encoding='utf-8') as stream:
            for index, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line, parse_float=Decimal, parse_constant=lambda _x: None, object_pairs_hook=unique_object)
                except (json.JSONDecodeError, ValueError, DecimalException, RecursionError):
                    print(f'journal illisible à la ligne {index} ; coût inconnu', file=sys.stderr)
                    return 1
                if not isinstance(row, dict):
                    print(f'journal invalide à la ligne {index} ; coût inconnu', file=sys.stderr)
                    return 1
                rows.append(row)
    except (OSError, UnicodeError, RuntimeError):
        print('journal indisponible ; coût inconnu', file=sys.stderr)
        return 1
    def day(row: dict) -> date | None:
        stamp = row.get('ts')
        if not isinstance(stamp, str):
            return None
        try:
            return datetime.fromisoformat(stamp).date()
        except ValueError:
            return None

    if args.run:
        # Entries without a run cannot be assigned to the requested run.
        unattributed = sum(
            (not isinstance(row.get('run'), str) or not row.get('run'))
            and (not args.since or day(row) is None or day(row) >= parsed)
            for row in rows
        )
        rows = [row for row in rows if isinstance(row.get('run'), str) and (row['run'] == args.run
                or row['run'].startswith(args.run if args.run.endswith('-') else args.run + '-'))]
    else:
        unattributed = 0
    if args.since:
        undated = sum(day(row) is None for row in rows)
        rows = [row for row in rows if day(row) is not None and day(row) >= parsed]
    else:
        undated = 0
    groups: dict[str, list[dict]] = {}
    for row in rows:
        alias = row.get('alias')
        # Ne jamais recopier de texte arbitraire ni de données du journal dans la sortie.
        if alias not in ('eco-deepseek', 'eco-muse', 'eco-gemini', 'eco-gemini-eleve', 'gemini'):
            alias = 'autre'
        groups.setdefault(alias, []).append(row)
    report = {'groupes': {key: aggregate(val) for key, val in sorted(groups.items())},
              'total': aggregate(rows), 'sans_date': undated, 'sans_identifiant': unattributed}
    if undated or unattributed:
        # A row excluded for missing attribution may belong to the requested selection.
        report['total']['cout_total'] = None
        report['total']['in'] = report['total']['out'] = None
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
        return 0
    for alias, group in [*report['groupes'].items(), ('TOTAL', report['total'])]:
        known = money(group['cout_connu'])
        amount = Decimal(group['cout_connu'])
        shown = '<$0.00001' if Decimal(0) < amount < Decimal('0.00001') else f'≈${known}'
        if not group['requetes']:
            cost = 'aucune donnée de coût'
        elif group['cout_total'] is None:
            cost = f'coût déclaré {shown} + {group["couts_inconnus"]} coût(s) inconnu(s)'
            if alias == 'TOTAL' and (undated or unattributed):
                cost += f' + {undated + unattributed} entrée(s) non attribuable(s)'
        else:
            cost = shown
        unknown = f' (+{group["statuts_inconnus"]} statut(s) inconnu(s))' if group['statuts_inconnus'] else ''
        print(f'{alias}\t{group["requetes"]} req\t{group["echecs"]} echecs{unknown}\t{group["in"] or "?"} in\t{group["out"] or "?"} out\t{cost}')
    if undated or unattributed:
        print(f'Non attribuables au filtre : {undated} sans date, {unattributed} sans identifiant.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
