#!/usr/bin/env python3
"""Contrôle local des empreintes, de la syntaxe et des résultats, sans encodage."""
import ast
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
for line in (root / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ', 1)
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f'Empreinte incorrecte : {name}')
for name in ('banc_finish.py', 'profondeur_10bits.py', 'execution_bornee.py', 'verifier_paquet.py'):
    ast.parse((root / name).read_text(), filename=name)
summary = json.loads((root / 'synthese.json').read_text())
for field, filename, expected_count in (
    ('resultats_high', 'resultats-high.csv', 12),
    ('resultats_main', 'resultats-main.csv', 6),
    ('resultats_main_corrections', 'resultats-main-corrections.csv', 2),
):
    rows = summary[field]
    if len(rows) != expected_count or len({(x['clip'], x['profil_nvenc']) for x in rows}) != expected_count:
        raise ValueError(f'Cas inattendus : {field}')
    with (root / filename).open(newline='') as stream:
        csv_rows = list(csv.DictReader(stream))
    if len(csv_rows) != len(rows):
        raise ValueError(f'CSV incomplet : {filename}')
    for csv_row, row in zip(csv_rows, rows):
        if set(csv_row) != set(row) or any(csv_row[key] != str(value) for key, value in row.items()):
            raise ValueError(f'CSV différent du JSON : {filename}')
for row in summary['resultats_main_corrections']:
    if abs(row['ecart_corrige_pct']) > 0.1:
        raise ValueError('Écart de débit corrigé hors ±0,1 %')
print('Paquet vérifié : empreintes, syntaxe et 12 + 6 + 2 cas cohérents.')
