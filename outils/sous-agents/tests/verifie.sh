#!/usr/bin/env bash
# Vérifie les 3 tâches fabriquées par fabrique.py. Usage : verifie.sh <racine>  ->  affiche T1/T2/T3 PASS|FAIL (indépendamment de l'agent)
R="$(readlink -f "$1")"; cd "$R" || exit 2
# T1 : tests verts + plus aucun ancien nom
( cd work/t1 && python3 -m unittest discover -s tests -t . >/dev/null 2>&1 && ! grep -rq calcul_prix_ttc . && python3 -c "import boutique.prix as p;assert p.prix_ttc(100)==114.98" ) && echo "T1 PASS" || echo "T1 FAIL"
# T2 : tests de l'agent verts + tests cachés
( cd work/t2 && node --test >/dev/null 2>&1 ) && ( node --test verif/t2.test.ts 2>&1 | grep -q "^ℹ fail 0" ) && echo "T2 PASS" || echo "T2 FAIL"
# T3 : bogue corrigé (tests cachés + test fourni) + résumé : au moins 6 faits sur 8
OK3=0; ( cd work/t3 && python3 -m unittest >/dev/null 2>&1 && python3 "$R/verif/t3_hidden.py" . >/dev/null 2>&1 ) && OK3=1
F=0; S="$(tr 'A-Z' 'a-z' < work/t3/RESUME.md 2>/dev/null)"
for k in "lru|moins récemment" "ttl" "seconde" "horloge|clock" "verrou|lock|thread" "purge" "get_or_set" "stats|hit"; do echo "$S" | grep -Eq "$k" && F=$((F+1)); done
{ [ $OK3 = 1 ] && [ $F -ge 6 ] && echo "T3 PASS (faits résumé $F/8)"; } || echo "T3 FAIL (bogue corrigé=$OK3, faits résumé $F/8)"
