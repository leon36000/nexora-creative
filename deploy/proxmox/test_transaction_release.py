import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('transaction_release', Path(__file__).with_name('transaction_release.py'))
T = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(T)


class Transaction(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cible, self.backup = self.root / 'cible', self.root / 'backup'
        self.release = self.cible / 'releases/candidate'
        for root in (self.release, self.cible):
            (root / 'app/server').mkdir(parents=True)
        (self.release / 'BUILD_OK').write_text('a' * 64 + '\n')
        (self.cible / 'app/server/a.ts').write_text('ancien')
        (self.cible / 'app/inconnu').write_text('conserver')
        (self.cible / 'app/data').mkdir()
        (self.cible / 'app/data/utilisateur').write_text('données')
        (self.release / 'app/server/a.ts').write_text('nouveau')
        (self.release / 'app/server/b.ts').write_text('créé')
        self.liste = ['app/server/a.ts', 'app/server/b.ts']

    def test_deploiement_et_retour_preservent_fichiers_hors_liste(self):
        actions = T.preparer(self.release, self.cible, self.backup, T.planifier(self.release, self.cible, self.liste))
        T.appliquer(self.release, self.cible, actions)
        self.assertEqual((self.cible / self.liste[0]).read_text(), 'nouveau')
        T.rollback(self.cible, self.backup)
        self.assertEqual((self.cible / self.liste[0]).read_text(), 'ancien')
        self.assertFalse((self.cible / self.liste[1]).exists())
        self.assertEqual((self.backup / 'nouveaux' / self.liste[1]).read_text(), 'créé')
        self.assertEqual((self.cible / 'app/inconnu').read_text(), 'conserver')
        self.assertEqual((self.cible / 'app/data/utilisateur').read_text(), 'données')
        T.rollback(self.cible, self.backup)  # une reprise ne modifie rien

    def test_rollback_refuse_conflit_sans_ecraser_les_versions(self):
        actions = T.preparer(self.release, self.cible, self.backup, T.planifier(self.release, self.cible, self.liste))
        T.appliquer(self.release, self.cible, actions)
        (self.cible / self.liste[0]).write_text('modification tierce')
        with self.assertRaisesRegex(ValueError, 'conflit'):
            T.rollback(self.cible, self.backup)
        self.assertEqual((self.cible / self.liste[0]).read_text(), 'modification tierce')
        self.assertEqual((self.cible / self.liste[1]).read_text(), 'créé')
        self.assertEqual((self.backup / 'avant' / self.liste[0]).read_text(), 'ancien')
        self.assertEqual((self.release / self.liste[0]).read_text(), 'nouveau')

    def test_refuse_preimage_modifiee_apres_revue(self):
        actions = T.planifier(self.release, self.cible, self.liste)
        (self.cible / self.liste[0]).write_text('modification tierce')
        with self.assertRaisesRegex(ValueError, 'manifeste revu'):
            T.preparer(self.release, self.cible, self.backup, actions)
        self.assertFalse(self.backup.exists())
        self.assertEqual((self.cible / self.liste[0]).read_text(), 'modification tierce')

    def test_refuse_sauvegarde_dans_application_active(self):
        actions = T.planifier(self.release, self.cible, self.liste)
        with self.assertRaisesRegex(ValueError, 'arbre actif'):
            T.preparer(self.release, self.cible, self.cible / 'app/backup', actions)
        self.assertFalse((self.cible / 'app/backup').exists())

    def test_interruption_partielle_reparable(self):
        actions = T.preparer(self.release, self.cible, self.backup, T.planifier(self.release, self.cible, self.liste))
        original = T.copier
        def erreur_sur_second(src, dst, *a):
            if dst.name == 'b.ts':
                raise OSError('fixture')
            return original(src, dst, *a)
        with patch.object(T, 'copier', side_effect=erreur_sur_second):
            with self.assertRaises(OSError):
                T.appliquer(self.release, self.cible, actions)
        T.rollback(self.cible, self.backup)
        self.assertEqual((self.cible / self.liste[0]).read_text(), 'ancien')
        self.assertFalse((self.cible / self.liste[1]).exists())

    def test_refuse_traversal_donnees_et_liens(self):
        for path in ('../hors', 'app/data/utilisateur', 'app/.env', 'app/server/.npmrc'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                T.planifier(self.release, self.cible, [path])
        (self.release / 'app/server/lien').symlink_to('/tmp')
        with self.assertRaises(ValueError):
            T.planifier(self.release, self.cible, ['app/server/lien'])
        self.assertFalse(self.backup.exists())

    def test_refuse_release_sans_build_et_ancetre_symbolique(self):
        (self.release / 'BUILD_OK').unlink()  # fixture créée par ce test
        with self.assertRaisesRegex(ValueError, 'build non vérifié'):
            T.planifier(self.release, self.cible, self.liste)
        (self.release / 'BUILD_OK').write_text('a' * 64 + '\n')
        lien = self.root / 'alias'
        lien.symlink_to(self.cible)
        with self.assertRaisesRegex(ValueError, 'symbolique'):
            T.planifier(self.release, lien, self.liste)

    def test_dependances_preconstruites_et_rollback(self):
        for root, contenu in ((self.release, 'nouveau'), (self.cible, 'ancien')):
            (root / 'app/node_modules').mkdir()
            (root / 'app/node_modules/code.js').write_text(contenu)
        (self.release / 'DEPENDANCES_SHA256').write_text(T.empreinte_dependances(self.release / 'app/node_modules') + '\n')
        actions = T.preparer(self.release, self.cible, self.backup, T.planifier(self.release, self.cible, self.liste))
        state = T.preparer_dependances(self.release, self.cible, self.backup, T.planifier_dependances(self.release, self.cible))
        T.rollback_dependances(self.cible, self.backup)  # aucune mutation avant application
        T.appliquer(self.release, self.cible, actions)
        T.appliquer_dependances(self.cible, self.backup, state)
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'nouveau')
        T.rollback_dependances(self.cible, self.backup)
        T.rollback_dependances(self.cible, self.backup)  # reprise idempotente
        T.rollback(self.cible, self.backup)
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'ancien')
        self.assertEqual((self.release / 'app/node_modules/code.js').read_text(), 'nouveau')

    def test_dependances_modifiees_bloquent_rollback(self):
        for root in (self.release, self.cible):
            (root / 'app/node_modules').mkdir()
            (root / 'app/node_modules/code.js').write_text('initial')
        (self.release / 'DEPENDANCES_SHA256').write_text(T.empreinte_dependances(self.release / 'app/node_modules') + '\n')
        T.preparer(self.release, self.cible, self.backup, T.planifier(self.release, self.cible, self.liste))
        state = T.preparer_dependances(self.release, self.cible, self.backup, T.planifier_dependances(self.release, self.cible))
        T.appliquer_dependances(self.cible, self.backup, state)
        (self.release / 'app/node_modules/code.js').write_text('modification tierce')
        with self.assertRaisesRegex(ValueError, 'conflit'):
            T.rollback_dependances(self.cible, self.backup)
        self.assertTrue((self.cible / 'app/node_modules').is_symlink())
        self.assertEqual((self.backup / 'node_modules-avant/code.js').read_text(), 'initial')

    def test_deux_livraisons_successives_puis_retour(self):
        releases = self.cible / 'releases'
        premiere, seconde = releases / 'une', releases / 'deux'
        for root, valeur in ((premiere, 'version 1'), (seconde, 'version 2')):
            (root / 'app/node_modules').mkdir(parents=True)
            (root / 'app/node_modules/code.js').write_text(valeur)
            (root / 'BUILD_OK').write_text('a' * 64 + '\n')
            (root / 'DEPENDANCES_SHA256').write_text(T.empreinte_dependances(root / 'app/node_modules') + '\n')
        (self.cible / 'app/node_modules').symlink_to(premiere / 'app/node_modules')
        actions = T.planifier(self.release, self.cible, self.liste)
        T.preparer(self.release, self.cible, self.backup, actions)
        state = T.preparer_dependances(seconde, self.cible, self.backup, T.planifier_dependances(seconde, self.cible))
        T.appliquer_dependances(self.cible, self.backup, state)
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'version 2')
        T.rollback_dependances(self.cible, self.backup)
        T.rollback_dependances(self.cible, self.backup)
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'version 1')

    def test_lien_dependances_echoue_restauration_possible(self):
        for root in (self.release, self.cible):
            (root / 'app/node_modules').mkdir()
            (root / 'app/node_modules/code.js').write_text('initial')
        (self.release / 'DEPENDANCES_SHA256').write_text(T.empreinte_dependances(self.release / 'app/node_modules') + '\n')
        T.preparer(self.release, self.cible, self.backup, T.planifier(self.release, self.cible, self.liste))
        state = T.preparer_dependances(self.release, self.cible, self.backup, T.planifier_dependances(self.release, self.cible))
        with patch.object(T.os, 'symlink', side_effect=OSError('fixture')):
            with self.assertRaises(OSError):
                T.appliquer_dependances(self.cible, self.backup, state)
        self.assertFalse((self.cible / 'app/node_modules').exists())
        T.rollback_dependances(self.cible, self.backup)
        self.assertEqual((self.cible / 'app/node_modules/code.js').read_text(), 'initial')

    def test_verrou_exclusif_et_lien_refuse(self):
        path = self.root / 'livraison.lock'
        with T.verrou(path):
            with self.assertRaises(BlockingIOError):
                with T.verrou(path):
                    self.fail('deuxième verrou acquis')
        lien = self.root / 'lien.lock'
        lien.symlink_to(path)
        with self.assertRaises(OSError):
            with T.verrou(lien):
                self.fail('lien accepté')

    def test_prevol_rejette_travail_actif_et_soumission_ambigue(self):
        data = self.root / 'data'
        data.mkdir()
        db = data / 'openfield.db'
        with sqlite3.connect(db) as conn:
            conn.execute('CREATE TABLE takes (status TEXT, settings TEXT)')
            conn.execute('CREATE TABLE projets_longs (data TEXT)')
            conn.execute('INSERT INTO takes VALUES (?,?)', ('done', '{}'))
        T.verifier_travaux(data)
        with sqlite3.connect(db) as conn:
            conn.execute('INSERT INTO takes VALUES (?,?)', ('failed', '{"nexoraSoumission":"indeterminee"}'))
        with self.assertRaisesRegex(ValueError, 'indéterminé'):
            T.verifier_travaux(data)
        with sqlite3.connect(db) as conn:
            conn.execute('DELETE FROM takes WHERE status=?', ('failed',))
        (data / 'detourage').mkdir()
        (data / 'detourage/registre.json').write_text(json.dumps([{'etat': 'en_cours'}]))
        with self.assertRaisesRegex(ValueError, 'détourage actifs'):
            T.verifier_travaux(data)

    def test_sauvegarde_sqlite_wal_inclut_transactions_validees(self):
        data = self.root / 'data-wal'
        data.mkdir()
        db = sqlite3.connect(data / 'openfield.db')
        self.addCleanup(db.close)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE fixture (nombre INTEGER)')
        db.execute('INSERT INTO fixture VALUES (42)')
        db.commit()
        self.backup.mkdir()
        T.sauvegarder_base(data, self.backup)
        with sqlite3.connect(self.backup / 'openfield-avant.db') as copie:
            self.assertEqual(copie.execute('SELECT nombre FROM fixture').fetchone()[0], 42)
