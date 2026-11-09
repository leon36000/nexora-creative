"""Contrats hors ligne : les notes et empreintes sont des fixtures synthétiques."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import apparier

ROOT = Path(__file__).parent
CORPUS = ROOT / 'corpus.json'


class ComparaisonTest(unittest.TestCase):
    def setUp(self):
        self.corpus, self.sha = apparier._charger(CORPUS)
        self.ids = sorted(b['id'] for b in self.corpus['briefs'] if b['split'] == 'test')
        self.protocole = {'corpus_sha256': self.sha, 'split_attendu': {'construction': 30, 'validation': 10, 'test': 10}, 'eleve': 'fixture-eleve', 'memoires': {'reference': 'c' * 64, 'candidate': 'd' * 64}, 'repetitions_attendues': [1, 2]}
        self.data = {'protocole_sha256': 'e' * 64, 'observations': [
            {'brief_id': bid, 'condition': condition, 'repetition': rep, 'seed': rep + 100, 'score': score, 'evidence_sha256': 'a' * 64}
            for bid in self.ids for rep in (1, 2) for condition, score in [('reference', .4), ('candidate', .6)]]}

    def preparation(self):
        return apparier.preparer(self.corpus, self.sha, self.protocole, 'e' * 64, self.data, 'b' * 64)

    def test_reel_corpus_et_paires_synthetiques(self):
        resultat = self.preparation()
        self.assertEqual(len(self.corpus['briefs']), 50)
        self.assertEqual(len(resultat['reference']), 10)
        self.assertEqual(resultat['nombre_campagnes_test'], 2)
        self.assertEqual(resultat['repetitions'], [1, 2])
        self.assertEqual(resultat['reference'][self.ids[0]], [.4, .4])
        self.assertEqual(resultat['candidate'][self.ids[0]], [.6, .6])
        self.assertEqual(resultat['preuves'], 'empreintes_declarees_non_verifiees')
        self.assertEqual(resultat['statut'], 'paires_pretes_sans_promotion')

    def test_aucun_brief_ou_repetition_manquant(self):
        self.data['observations'].pop()
        with self.assertRaisesRegex(ValueError, 'incomplètes'):
            self.preparation()

    def test_seed_non_appariee_refusee(self):
        self.data['observations'][1]['seed'] = 999
        with self.assertRaisesRegex(ValueError, 'Seeds'):
            self.preparation()

    def test_repetition_entiere_absente_refusee(self):
        self.data['observations'] = [o for o in self.data['observations'] if o['repetition'] == 1]
        with self.assertRaisesRegex(ValueError, 'incomplètes'):
            self.preparation()

    def test_split_declared_modifie_refuse(self):
        self.protocole['split_attendu'] = {'construction': 29, 'validation': 10, 'test': 11}
        with self.assertRaisesRegex(ValueError, 'Effectifs'):
            self.preparation()

    def test_protocole_et_observations_mal_formes_refuses(self):
        data = self.data
        for invalid in (None, {}, {'protocole_sha256': 'f' * 64, 'observations': []}, {'protocole_sha256': 'e' * 64, 'observations': []}):
            self.data = invalid
            with self.subTest(data=invalid), self.assertRaises(ValueError):
                self.preparation()
        self.data = data
        for champ, invalid in [('eleve', ''), ('memoires', {}), ('repetitions_attendues', []), ('repetitions_attendues', [1, 1])]:
            initial = self.protocole[champ]; self.protocole[champ] = invalid
            with self.subTest(champ=champ, invalid=invalid), self.assertRaises(ValueError):
                self.preparation()
            self.protocole[champ] = initial
        self.protocole = {}
        with self.assertRaisesRegex(ValueError, 'Protocole invalide'):
            self.preparation()

    def test_doublon_ou_brief_construction_refuses(self):
        self.data['observations'].append(copy.deepcopy(self.data['observations'][0]))
        with self.assertRaisesRegex(ValueError, 'dupliquée'):
            self.preparation()
        self.data['observations'].pop()
        self.data['observations'][0]['brief_id'] = next(b['id'] for b in self.corpus['briefs'] if b['split'] == 'construction')
        with self.assertRaisesRegex(ValueError, 'hors test'):
            self.preparation()

    def test_corpus_insuffisant_fuite_ou_emp_reinte_modifiee(self):
        original = copy.deepcopy(self.corpus)
        self.corpus['briefs'].pop()
        with self.assertRaisesRegex(ValueError, 'too_few_briefs'):
            self.preparation()
        self.corpus = copy.deepcopy(original)
        a = self.corpus['briefs'][0]; b = next(b for b in self.corpus['briefs'] if b['split'] != a['split'])
        b['campaign_id'] = a['campaign_id']
        with self.assertRaisesRegex(ValueError, 'split_leak'):
            self.preparation()
        self.corpus = original
        self.protocole['corpus_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Empreinte'):
            self.preparation()

    def test_valeurs_et_schema_invalides(self):
        o = self.data['observations'][0]
        for field, invalid in [('score', float('nan')), ('score', float('inf')), ('score', True), ('score', 2), ('repetition', True), ('seed', True), ('brief_id', []), ('condition', []), ('evidence_sha256', 'abc')]:
            old = o[field]; o[field] = invalid
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                self.preparation()
            o[field] = old
        o['extra'] = 1
        with self.assertRaisesRegex(ValueError, 'Observation invalide'):
            self.preparation()

    def test_cli_reelle_et_cles_dupliquees(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as d:
            path = Path(d) / 'observations.json'
            protocole = Path(d) / 'protocole.json'
            protocole.write_text(json.dumps(self.protocole))
            protocole_sha = hashlib.sha256(protocole.read_bytes()).hexdigest()
            self.data['protocole_sha256'] = protocole_sha
            path.write_text(json.dumps(self.data))
            commande = [sys.executable, str(ROOT / 'apparier.py'), str(CORPUS), str(protocole), str(path), '--sha-protocole', protocole_sha]
            run = subprocess.run(commande, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['statut'], 'paires_pretes_sans_promotion')
            path.write_text('{"corpus_sha256":"a","corpus_sha256":"b","observations":[]}')
            run = subprocess.run(commande, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(run.stdout, '')
            self.assertIn('dupliquée', run.stderr)
            protocole.write_text(json.dumps({**self.protocole, 'repetitions_attendues': [1]}))
            run = subprocess.run(commande, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 1)
            self.assertIn('protocole gelé', run.stderr)

    def test_main_valide_et_refus_protocoles_reels(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as d:
            dossier = Path(d)
            protocole = dossier / 'protocole.json'
            observations = dossier / 'observations.json'
            protocole.write_text(json.dumps(self.protocole))
            empreinte = hashlib.sha256(protocole.read_bytes()).hexdigest()
            self.data['protocole_sha256'] = empreinte
            observations.write_text(json.dumps(self.data))
            args = [str(CORPUS), str(protocole), str(observations), '--sha-protocole', empreinte]
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(apparier.main(args), 0)
            self.assertEqual(json.loads(out.getvalue())['nombre_briefs_test'], 10)
            self.assertEqual(err.getvalue(), '')
            protocole.write_text(json.dumps({**self.protocole, 'repetitions_attendues': [1]}))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                self.assertEqual(apparier.main(args), 1)
            self.assertIn('protocole gelé', err.getvalue())
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                self.assertEqual(apparier.main([str(CORPUS), str(dossier / 'absent'), str(observations), '--sha-protocole', empreinte]), 1)
            self.assertIn('refusées', err.getvalue())


if __name__ == '__main__':
    unittest.main()
