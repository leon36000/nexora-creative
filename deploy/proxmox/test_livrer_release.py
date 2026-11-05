import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
SPEC = importlib.util.spec_from_file_location('livrer_release', Path(__file__).with_name('livrer_release.py'))
L = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(L)
import transaction_release as T


class Livraison(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cible, self.data, self.backup = (self.root / p for p in ('cible', 'data', 'backup'))
        self.release = self.cible / 'releases/candidate'
        for root in (self.release, self.cible):
            (root / 'app/server').mkdir(parents=True)
            (root / 'app/node_modules').mkdir()
        self.data.mkdir()
        (self.release / 'BUILD_OK').write_text('a' * 64 + '\n')
        (self.release / 'app/server/code.ts').write_text('nouveau')
        (self.cible / 'app/server/code.ts').write_text('ancien')
        (self.release / 'app/node_modules/code.js').write_text('nouvelles dépendances')
        (self.cible / 'app/node_modules/code.js').write_text('anciennes dépendances')
        (self.release / 'DEPENDANCES_SHA256').write_text(T.empreinte_dependances(self.release / 'app/node_modules') + '\n')
        (self.cible / 'app/inconnu').write_text('conserver')
        with sqlite3.connect(self.data / 'openfield.db') as db:
            db.execute('CREATE TABLE takes(status TEXT, settings TEXT)')
            db.execute('CREATE TABLE projets_longs(data TEXT)')
        self.actions = T.planifier(self.release, self.cible, ['app/server/code.ts'])
        self.dependances = T.planifier_dependances(self.release, self.cible)
        self.appels = []

    def activer(self, sante):
        L.activer(self.release, self.cible, self.data, self.backup, self.actions, self.dependances,
                  stopper=lambda: self.appels.append('stop'), demarrer=lambda: self.appels.append('start'),
                  verifier=lambda: sante, identite=lambda _data: None)

    def test_succes_maintenance_unique_et_fichiers_inconnus_conserves(self):
        self.activer(True)
        self.assertEqual(self.appels, ['stop', 'start'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'nouveau')
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'nouvelles dépendances')
        self.assertEqual((self.cible / 'app/inconnu').read_text(), 'conserver')
        self.assertTrue((self.backup / 'openfield-avant.db').is_file())
        self.assertEqual((self.backup / 'openfield-avant.sha256').read_text().strip(), T.digest(self.backup / 'openfield-avant.db'))

    def test_plan_est_lisible_et_ne_modifie_pas_la_cible(self):
        (self.release / 'SOURCE_FILES.json').write_text(json.dumps(['app/server/code.ts']))
        (self.release / 'SOURCE_HASHES.json').write_text(json.dumps({'app/server/code.ts': T.digest(self.release / 'app/server/code.ts')}))
        (self.release / 'FICHIERS_SHA256.json').write_text(json.dumps({'app/server/code.ts': T.digest(self.release / 'app/server/code.ts')}))
        plan = self.root / 'plan.json'
        L.planifier(self.release, self.cible, plan)
        objet = json.loads(plan.read_text())
        self.assertEqual(objet['actions'], self.actions)
        self.assertEqual(objet['dependances'], self.dependances)
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')
        self.assertFalse(self.backup.exists())
        (self.release / 'app/server/code.ts').write_text('source modifiée')
        (self.root / 'refuse').mkdir()
        with self.assertRaisesRegex(ValueError, 'fichiers modifiés'):
            L.planifier(self.release, self.cible, self.root / 'refuse/plan.json')

    def test_sante_echouee_restaure_code_et_dependances(self):
        with self.assertRaisesRegex(ValueError, 'santé'):
            self.activer(False)
        self.assertEqual(self.appels, ['stop', 'start', 'stop', 'start'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'anciennes dépendances')
        self.assertEqual((self.cible / 'app/inconnu').read_text(), 'conserver')

    def test_travail_actif_empeche_maintenance(self):
        with sqlite3.connect(self.data / 'openfield.db') as db:
            db.execute('INSERT INTO takes VALUES (?,?)', ('rendering', '{}'))
        with self.assertRaisesRegex(ValueError, 'travaux actifs'):
            self.activer(True)
        self.assertEqual(self.appels, [])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')

    def test_build_non_valide_n_arrete_pas_le_service(self):
        (self.release / 'BUILD_OK').unlink()  # fixture temporaire
        with self.assertRaisesRegex(ValueError, 'build non vérifié'):
            self.activer(True)
        self.assertEqual(self.appels, [])
        self.assertFalse(self.backup.exists())

    def test_nouveau_travail_entre_prevol_et_arret_bloque_avant_copie(self):
        def stop_et_nouveau_travail():
            self.appels.append('stop')
            with sqlite3.connect(self.data / 'openfield.db') as db:
                db.execute('INSERT INTO takes VALUES (?,?)', ('rendering', '{}'))
        with self.assertRaisesRegex(ValueError, 'travaux actifs'):
            L.activer(self.release, self.cible, self.data, self.backup, self.actions, self.dependances,
                      stopper=stop_et_nouveau_travail, demarrer=lambda: self.appels.append('start'),
                      verifier=lambda: True, identite=lambda _data: None)
        self.assertEqual(self.appels, ['stop', 'start'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')

    def test_conflit_refuse_rollback_et_ne_redemarre_pas(self):
        def ecriture_tierce(*_args):
            (self.cible / 'app/server/code.ts').write_text('tiers')
            raise OSError('fixture')
        with patch.object(T, 'appliquer', side_effect=ecriture_tierce):
            with self.assertRaisesRegex(ValueError, 'conflit'):
                self.activer(True)
        self.assertEqual(self.appels, ['stop'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'tiers')
        self.assertEqual((self.backup / 'avant/app/server/code.ts').read_text(), 'ancien')
        self.assertEqual((self.release / 'app/server/code.ts').read_text(), 'nouveau')

    def test_sante_attend_le_demarrage(self):
        reponse = io.BytesIO(b'{"rapide":{"disponible":true}}')
        with patch.object(L.urllib.request, 'urlopen', side_effect=[OSError('démarrage'), OSError('démarrage'), reponse]), patch.object(L.time, 'sleep'):
            self.assertTrue(L.sante())

    def test_base_ouverte_par_le_cgroup(self):
        cgroup, proc = self.root / 'cgroup', self.root / 'proc'
        (cgroup / 'system.slice/nexora.service').mkdir(parents=True)
        (cgroup / 'system.slice/nexora.service/cgroup.procs').write_text('42\n')
        (proc / '42/fd').mkdir(parents=True)
        (proc / '42/fd/3').symlink_to(self.data / 'openfield.db')
        L.base_ouverte(self.data, '/system.slice/nexora.service', cgroup, proc)
        with self.assertRaisesRegex(ValueError, 'groupe'):
            L.base_ouverte(self.data, '/../autre', cgroup, proc)
        (proc / '42/fd/3').unlink()  # lien factice du test
        with self.assertRaisesRegex(ValueError, 'non confirmée'):
            L.base_ouverte(self.data, '/system.slice/nexora.service', cgroup, proc)

    def test_commande_systemd_ne_vise_que_creative(self):
        with patch.object(L.subprocess, 'run') as run:
            L.service('stop')
        self.assertEqual(run.call_args.args[0], ['systemctl', 'stop', 'nexora-creative'])
        with patch.object(L.subprocess, 'check_output', return_value='/system.slice/nexora.service\n'), patch.object(L, 'base_ouverte') as base:
            L.verifier_base_active(self.data)
        base.assert_called_once_with(self.data, '/system.slice/nexora.service')

    def test_cli_verifie_le_manifeste_avant_activation(self):
        (self.release / 'SOURCE_FILES.json').write_text(json.dumps(['app/server/code.ts']))
        (self.release / 'SOURCE_HASHES.json').write_text(json.dumps({'app/server/code.ts': T.digest(self.release / 'app/server/code.ts')}))
        (self.release / 'FICHIERS_SHA256.json').write_text(json.dumps({'app/server/code.ts': T.digest(self.release / 'app/server/code.ts')}))
        plan = self.root / 'plan.json'
        L.main(['plan', str(self.release), str(self.cible), str(plan)])
        args = ['activer', str(self.release), str(self.cible), str(self.data), str(self.backup), str(plan)]
        with patch.object(L, 'activer') as activer:
            L.main(args)
        activer.assert_called_once()
        objet = json.loads(plan.read_text())
        objet['actions'][0]['chemin'] = 'app/server/autre.ts'
        plan.write_text(json.dumps(objet))
        with patch.object(L, 'activer') as activer, self.assertRaisesRegex(ValueError, 'liste de fichiers'):
            L.main(args)
        activer.assert_not_called()
        with self.assertRaises(SystemExit):
            L.main(['inconnu'])

    def test_retour_explicite_restaure_les_versions(self):
        self.activer(True)
        L.retour(self.cible, self.data, self.backup, stopper=lambda: self.appels.append('stop'),
                 demarrer=lambda: self.appels.append('start'), identite=lambda _data: None, verifier=lambda: True, en_marche=lambda: True)
        self.assertEqual(self.appels, ['stop', 'start', 'stop', 'start'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'anciennes dépendances')
        self.assertEqual((self.release / 'app/server/code.ts').read_text(), 'nouveau')

    def test_retour_divergent_refuse_avant_arret(self):
        self.activer(True)
        (self.cible / 'app/server/code.ts').write_text('tiers')
        with self.assertRaisesRegex(ValueError, 'conflit'):
            L.retour(self.cible, self.data, self.backup, stopper=lambda: self.appels.append('stop'),
                     demarrer=lambda: self.appels.append('start'), identite=lambda _data: None, en_marche=lambda: True)
        self.assertEqual(self.appels, ['stop', 'start'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'tiers')

    def test_retour_signale_service_indisponible(self):
        self.activer(True)
        with self.assertRaisesRegex(ValueError, 'indisponible après retour'):
            L.retour(self.cible, self.data, self.backup, stopper=lambda: self.appels.append('stop'),
                     demarrer=lambda: self.appels.append('start'), identite=lambda _data: None, verifier=lambda: False, en_marche=lambda: True)
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')

    def test_retour_si_service_deja_arrete_utilise_identite_sauvee(self):
        self.activer(True)
        L.retour(self.cible, self.data, self.backup, stopper=lambda: self.appels.append('stop'),
                 demarrer=lambda: self.appels.append('start'), identite=lambda _data: self.fail('FD service arrêté'),
                 verifier=lambda: True, en_marche=lambda: False)
        self.assertEqual(self.appels, ['stop', 'start', 'start'])
        self.assertEqual((self.cible / 'app/server/code.ts').read_text(), 'ancien')


if __name__ == '__main__':
    unittest.main()
