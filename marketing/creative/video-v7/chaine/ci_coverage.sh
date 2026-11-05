#!/bin/sh
# Tous les fichiers de mesure et les journaux restent sous V7_CI_ROOT.
set -u
status=0
python3 -m coverage run --parallel-mode --branch marketing/creative/video-v7/chaine/ci_tests.py > "$V7_CI_ROOT/tests.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch recherche/30-annexes/finish-banc/verifier_paquet.py > "$V7_CI_ROOT/finish-verification-couverture.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s marketing/creative/video-v7/chaine/tests -p test_finish_ci.py -v > "$V7_CI_ROOT/finish-tests.log" 2>&1 || status=1
cat "$V7_CI_ROOT/tests.log" "$V7_CI_ROOT/finish-verification-couverture.log" "$V7_CI_ROOT/finish-tests.log"
python3 -m coverage combine --keep > "$V7_CI_ROOT/coverage-combine.log" 2>&1 || status=1
python3 -m coverage xml -o "$V7_CI_ROOT/coverage.xml" > "$V7_CI_ROOT/coverage-xml.log" 2>&1 || status=1
cat "$V7_CI_ROOT/coverage-combine.log" "$V7_CI_ROOT/coverage-xml.log"
if ! python3 - "$V7_CI_ROOT/coverage.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET

names = {'ci_tests.py', 'banc_finish.py', 'profondeur_10bits.py', 'execution_bornee.py', 'verifier_paquet.py'}
found, covered, total = set(), 0, 0
for item in ET.parse(sys.argv[1]).iter('class'):
    name = item.get('filename', '').rsplit('/', 1)[-1]
    if name not in names:
        continue
    if name in found:
        raise ValueError('Fichier de couverture ambigu : ' + name)
    found.add(name)
    for line in item.iter('line'):
        if line.get('branch') == 'true':
            fraction = line.get('condition-coverage').split('(')[-1].rstrip(')').split('/')
            covered += int(fraction[0]); total += int(fraction[1])
if found != names or not total:
    raise ValueError('Fichiers ou branches de couverture manquants')
print(f'Branches du code nouveau : {covered}/{total} = {covered/total:.1%}')
if covered / total < .85:
    raise SystemExit('Couverture de branches inférieure à 85 %')
PY
then status=1; fi
exit "$status"
