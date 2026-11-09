#!/bin/sh
# Tous les fichiers de mesure et les journaux restent sous V7_CI_ROOT.
set -u
status=0
python3 -m coverage run --parallel-mode --branch marketing/creative/video-v7/chaine/ci_tests.py > "$V7_CI_ROOT/tests.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch recherche/30-annexes/finish-banc/verifier_paquet.py > "$V7_CI_ROOT/finish-verification-couverture.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s marketing/creative/video-v7/chaine/tests -p test_finish_ci.py -v > "$V7_CI_ROOT/finish-tests.log" 2>&1 || status=1
PYTHONPATH=marketing/creative/video-v7/chaine python3 -m coverage run --parallel-mode --branch -m unittest discover -s marketing/creative/video-v7/chaine/tests -p test_assemblage_portable.py -v > "$V7_CI_ROOT/assemblage-tests.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s marketing/creative/video-v7/chaine/tests -p test_politique_voix_film.py -v > "$V7_CI_ROOT/politique-voix-tests.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s outils/detourage/tests -p test_comparateur_alpha.py -v > "$V7_CI_ROOT/matte-tests.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s app/server/nexora/bench/production-evidence-v2 -p test_importer.py -v > "$V7_CI_ROOT/production-evidence-v2-tests.log" 2>&1 || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s app/server/nexora/bench/corpus-amd-v2 -p 'test_*.py' -v > "$V7_CI_ROOT/amd2-tests.log" 2>&1 || status=1
# Les tests SyncRnd exigent une racine R&D distincte du dépôt.
sync_rnd_tmp="$(mktemp -d /tmp/nexora-sync-rnd.XXXXXX)" || exit 1
TMPDIR="$sync_rnd_tmp" python3 -m coverage run --parallel-mode --branch -m unittest discover -s app/server/nexora/bench/sync-rnd -p 'test_*.py' -v > "$V7_CI_ROOT/sync-rnd-tests.log" 2>&1 || status=1
sync_rnd_restes="$(mktemp -d "$V7_CI_ROOT/sync-rnd-restes.XXXXXX")" || exit 1
cp -a "$sync_rnd_tmp"/. "$sync_rnd_restes"/ || status=1
python3 -m coverage run --parallel-mode --branch -m unittest discover -s marketing/nexora/campagne-films/opsys-ultime/chaine/tests -p 'test_*.py' -v > "$V7_CI_ROOT/opsys-tests.log" 2>&1 || status=1
cat "$V7_CI_ROOT/tests.log" "$V7_CI_ROOT/finish-verification-couverture.log" "$V7_CI_ROOT/finish-tests.log" "$V7_CI_ROOT/assemblage-tests.log" "$V7_CI_ROOT/politique-voix-tests.log" "$V7_CI_ROOT/matte-tests.log" "$V7_CI_ROOT/production-evidence-v2-tests.log" "$V7_CI_ROOT/opsys-tests.log" "$V7_CI_ROOT/amd2-tests.log" "$V7_CI_ROOT/sync-rnd-tests.log"
python3 - "$V7_CI_ROOT/opsys-tests.log" <<'PY' || status=1
import re, sys
from pathlib import Path
match = re.search(r'^Ran (\d+) tests? in ', Path(sys.argv[1]).read_text(), re.M)
if not match or int(match.group(1)) < 20:
    raise SystemExit('Au moins 20 tests OPSYS sont attendus')
PY
python3 -m coverage run --parallel-mode --branch -m unittest discover -s deploy/proxmox -p 'test_*release.py' -v > "$V7_CI_ROOT/release-tests.log" 2>&1 || status=1
cat "$V7_CI_ROOT/release-tests.log"
python3 -m coverage combine --keep > "$V7_CI_ROOT/coverage-combine.log" 2>&1 || status=1
python3 -m coverage xml -o "$V7_CI_ROOT/coverage.xml" > "$V7_CI_ROOT/coverage-xml.log" 2>&1 || status=1
cat "$V7_CI_ROOT/coverage-combine.log" "$V7_CI_ROOT/coverage-xml.log"
if ! python3 - "$V7_CI_ROOT/coverage.xml" <<'PY'
import ast
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

names = {'ci_tests.py', 'banc_finish.py', 'profondeur_10bits.py', 'execution_bornee.py', 'verifier_paquet.py', 'assemblage_portable.py', 'comparateur_alpha.py', 'importer.py', 'sync_rnd.py'}
expected_importer = (Path.cwd() / 'app/server/nexora/bench/production-evidence-v2/importer.py').resolve()
expected_opsys = (Path.cwd() / 'marketing/nexora/campagne-films/opsys-ultime/chaine/monter.py').resolve()
sources = [Path(item.text) for item in ET.parse(sys.argv[1]).findall('./sources/source') if item.text]
found, covered, total = set(), 0, 0
opsys_classes = []
for item in ET.parse(sys.argv[1]).iter('class'):
    filename = item.get('filename', '')
    path = Path(filename)
    candidates = [path.resolve()] if path.is_absolute() else [(source / path).resolve() for source in sources]
    if expected_opsys in candidates:
        if {candidate for candidate in candidates if candidate.is_file()} != {expected_opsys}:
            raise ValueError('Chemin de couverture OPSYS ambigu')
        opsys_classes.append(item)
    name = filename.rsplit('/', 1)[-1]
    if name not in names:
        continue
    if name in found:
        raise ValueError('Fichier de couverture ambigu : ' + name)
    if name == 'importer.py':
        if candidates.count(expected_importer) != 1:
            raise ValueError('Le XML doit relier importer.py à app/server/nexora/bench/production-evidence-v2/importer.py')
    found.add(name)
    file_covered, file_total = 0, 0
    for line in item.iter('line'):
        if line.get('branch') == 'true':
            fraction = line.get('condition-coverage').split('(')[-1].rstrip(')').split('/')
            file_covered += int(fraction[0]); file_total += int(fraction[1])
    covered += file_covered; total += file_total
    if name in {'assemblage_portable.py', 'comparateur_alpha.py', 'importer.py', 'sync_rnd.py'}:
        if not file_total or file_covered / file_total < .85:
            raise ValueError(f'Couverture des branches insuffisante : {name}')
        print(f'Branches {name} : {file_covered}/{file_total} = {file_covered/file_total:.1%}')
if found != names or not total:
    raise ValueError('Fichiers ou branches de couverture manquants')
if len(opsys_classes) != 1:
    raise ValueError('Couverture OPSYS monter.py manquante ou ambiguë')
opsys_lines = {int(line.get('number')): int(line.get('hits')) for line in opsys_classes[0].iter('line')}
fonctions = {'mesurer_typo_cadre', 'poser_typo', 'verifier_typo_cadre'}
nodes = {n.name: n for n in ast.parse(expected_opsys.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in fonctions}
def corps_execute(node):
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    return bool(body) and any(opsys_lines.get(n, 0) > 0 for n in range(body[0].lineno, node.end_lineno + 1))
if set(nodes) != fonctions or any(not corps_execute(node) for node in nodes.values()):
    raise ValueError('Couverture OPSYS des fonctions typographiques manquante')
print('Couverture OPSYS : vrai chemin et trois fonctions exécutées')
print(f'Branches du code nouveau : {covered}/{total} = {covered/total:.1%}')
if covered / total < .85:
    raise SystemExit('Couverture de branches inférieure à 85 %')
PY
then status=1; fi
exit "$status"
