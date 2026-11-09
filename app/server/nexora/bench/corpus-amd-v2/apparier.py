#!/usr/bin/env python3
"""Prépare des paires AMD v2 complètes pour le calcul statistique existant.

Aucune promotion, décision humaine ou validité des scores n'est déduite des entrées.
Les empreintes d'observation sont déclaratives ; les fichiers associés ne sont pas lus.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

from valider import validate

SHA = re.compile(r'[0-9a-f]{64}', re.ASCII)
FIELDS = {'brief_id', 'condition', 'repetition', 'seed', 'score', 'evidence_sha256'}


def preparer(corpus, corpus_sha, protocole, protocole_sha, donnees, donnees_sha):
    """Refuse les pertes de paires et rend les deux bras pour compareApparie."""
    erreurs = validate(corpus)  # inclut 50 briefs et étanchéité campagnes/assets
    if erreurs:
        raise ValueError('Corpus invalide : ' + '; '.join(erreurs))
    if not isinstance(donnees, dict) or set(donnees) != {'protocole_sha256', 'observations'}:
        raise ValueError('Enveloppe d’observations invalide')
    if donnees['protocole_sha256'] != protocole_sha:
        raise ValueError('Empreinte du protocole différente')
    if not isinstance(protocole, dict) or set(protocole) != {'corpus_sha256', 'split_attendu', 'eleve', 'memoires', 'repetitions_attendues'}:
        raise ValueError('Protocole invalide')
    if protocole['corpus_sha256'] != corpus_sha:
        raise ValueError('Empreinte du corpus différente')
    attendu_split = protocole['split_attendu']
    effectif = {split: sum(b['split'] == split for b in corpus['briefs']) for split in ('construction', 'validation', 'test')}
    if (not isinstance(attendu_split, dict) or set(attendu_split) != set(effectif)
            or any(type(v) is not int or v < 1 for v in attendu_split.values()) or attendu_split != effectif):
        raise ValueError('Effectifs des partitions différents du protocole déclaré')
    memoires = protocole['memoires']
    if (not isinstance(protocole['eleve'], str) or not protocole['eleve'].strip() or not isinstance(memoires, dict)
            or set(memoires) != {'reference', 'candidate'}
            or any(not isinstance(v, str) or not SHA.fullmatch(v) for v in memoires.values())):
        raise ValueError('Élève ou empreintes des mémoires invalides')
    ids = {b['id'] for b in corpus['briefs'] if b['split'] == 'test'}
    if not ids:
        raise ValueError('Partition test vide')
    observations = donnees['observations']
    if not isinstance(observations, list) or not observations:
        raise ValueError('Observations absentes')
    cases = {}
    for o in observations:
        if not isinstance(o, dict) or set(o) != FIELDS:
            raise ValueError('Observation invalide')
        bid, condition, rep, seed, score, preuve = (o[k] for k in ('brief_id', 'condition', 'repetition', 'seed', 'score', 'evidence_sha256'))
        if not isinstance(bid, str) or bid not in ids or not isinstance(condition, str) or condition not in ('reference', 'candidate'):
            raise ValueError('Brief hors test ou condition inconnue')
        if type(rep) is not int or rep < 1 or type(seed) is not int or seed < 0 or isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1 or not math.isfinite(score):
            raise ValueError('Répétition, seed ou score invalide')
        if not isinstance(preuve, str) or not SHA.fullmatch(preuve):
            raise ValueError('Empreinte de preuve invalide')
        key = (bid, rep, condition)
        if key in cases:
            raise ValueError('Observation dupliquée')
        cases[key] = (score, seed, preuve)
    reps_declares = protocole['repetitions_attendues']
    if (not isinstance(reps_declares, list) or not reps_declares
            or any(type(rep) is not int or rep < 1 for rep in reps_declares)
            or len(reps_declares) != len(set(reps_declares))):
        raise ValueError('Répétitions attendues invalides')
    repetitions = set(reps_declares)
    expected = {(bid, rep, condition) for bid in ids for rep in repetitions for condition in ('reference', 'candidate')}
    if set(cases) != expected:
        raise ValueError('Paires ou répétitions incomplètes')
    if any(cases[bid, rep, 'reference'][1] != cases[bid, rep, 'candidate'][1] for bid in ids for rep in repetitions):
        raise ValueError('Seeds appariées différentes')
    reps = sorted(repetitions)
    return {'statut': 'paires_pretes_sans_promotion', 'split': 'test', 'corpus_sha256': corpus_sha,
            'protocole_sha256': protocole_sha, 'observations_sha256': donnees_sha, 'preuves': 'empreintes_declarees_non_verifiees',
            'limites': ['independance_semantique_et_chronologique_non_demontree',
                        'juge_et_scores_non_calibres_par_cette_garde', 'bootstrap_par_brief_pas_par_campagne',
                        'identites_et_execution_du_protocole_non_attestees'],
            'eleve': protocole['eleve'], 'memoires': memoires, 'split_attendu': attendu_split, 'repetitions': reps,
            'nombre_briefs_test': len(ids),
            'nombre_campagnes_test': len({b['campaign_id'] for b in corpus['briefs'] if b['split'] == 'test'}),
            'seeds': {bid: [cases[bid, rep, 'reference'][1] for rep in reps] for bid in sorted(ids)},
            'preuves_declarees': {condition: {bid: [cases[bid, rep, condition][2] for rep in reps] for bid in sorted(ids)}
                                  for condition in ('reference', 'candidate')},
            'reference': {bid: [cases[bid, rep, 'reference'][0] for rep in reps] for bid in sorted(ids)},
            'candidate': {bid: [cases[bid, rep, 'candidate'][0] for rep in reps] for bid in sorted(ids)}}


def _charger(path):
    data = Path(path).read_bytes()
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Clé JSON dupliquée')
            result[k] = v
        return result
    return json.loads(data, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Constante JSON invalide'))), hashlib.sha256(data).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('corpus'); parser.add_argument('protocole'); parser.add_argument('observations')
    parser.add_argument('--sha-protocole', required=True, help='SHA-256 attendu du protocole gelé')
    args = parser.parse_args(argv)
    try:
        corpus, sha = _charger(args.corpus)
        protocole, protocole_sha = _charger(args.protocole)
        if not SHA.fullmatch(args.sha_protocole) or protocole_sha != args.sha_protocole:
            raise ValueError('SHA du protocole gelé différent')
        donnees, donnees_sha = _charger(args.observations)
        print(json.dumps(preparer(corpus, sha, protocole, protocole_sha, donnees, donnees_sha), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f'Paires refusées : {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
