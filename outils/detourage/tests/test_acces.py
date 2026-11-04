"""Contrôle d'accès du serveur de détourage : jeton (fichier 600), liste d'adresses, refus de démarrer sans protection."""
import os
import tempfile
import unittest

from acces import Acces, ConfigAcces, lire_jeton, lire_reseaux

JETON = 'a' * 40


class TestAcces(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.f = os.path.join(self.d, 'jeton')
        with open(self.f, 'w') as fh:
            fh.write(JETON + '\n')
        os.chmod(self.f, 0o600)

    def tearDown(self):
        os.remove(self.f)
        os.rmdir(self.d)

    def env(self, **kw):
        return {'NEXORA_DETOURAGE_JETON_FICHIER': self.f, 'NEXORA_DETOURAGE_AUTORISES': '192.168.1.122,127.0.0.1', **kw}

    def test_jeton_mode_600_exige(self):
        for mode in (0o644, 0o604, 0o660, 0o666):
            os.chmod(self.f, mode)
            with self.assertRaises(ConfigAcces, msg=oct(mode)):
                lire_jeton(self.f)
        os.chmod(self.f, 0o640)  # groupe du processus (Secret monté avec fsGroup) : admis
        self.assertEqual(lire_jeton(self.f), JETON)
        os.chmod(self.f, 0o600)
        self.assertEqual(lire_jeton(self.f), JETON)

    def test_jeton_trop_court(self):
        with open(self.f, 'w') as fh:
            fh.write('court')
        with self.assertRaises(ConfigAcces):
            lire_jeton(self.f)

    def test_ecoute_reseau_sans_protection_refusee(self):
        with self.assertRaises(ConfigAcces):
            Acces.depuis_env(['192.168.1.126'], {})
        with self.assertRaises(ConfigAcces):
            Acces.depuis_env(['192.168.1.126'], {'NEXORA_DETOURAGE_JETON_FICHIER': self.f})
        with self.assertRaises(ConfigAcces):
            Acces.depuis_env(['0.0.0.0'], {'NEXORA_DETOURAGE_AUTORISES': '192.168.1.122'})
        # boucle locale seule : permis sans jeton (poste de développement)
        self.assertEqual(Acces.depuis_env(['127.0.0.1'], {}).verifier('127.0.0.1', None), 0)

    def test_verification(self):
        a = Acces.depuis_env(['127.0.0.1', '192.168.1.126'], self.env())
        ok = 'Bearer ' + JETON
        self.assertEqual(a.verifier('192.168.1.122', ok), 0)
        self.assertEqual(a.verifier('::ffff:192.168.1.122', ok), 0)
        self.assertEqual(a.verifier('127.0.0.1', ok), 0)
        self.assertEqual(a.verifier('192.168.1.50', ok), 403)  # bonne clé, mauvaise machine
        self.assertEqual(a.verifier('100.90.188.1', ok), 403)
        self.assertEqual(a.verifier('192.168.1.122', None), 401)
        self.assertEqual(a.verifier('192.168.1.122', 'Bearer ' + 'b' * 40), 401)
        self.assertEqual(a.verifier('192.168.1.122', JETON), 401)  # sans « Bearer »
        self.assertEqual(a.verifier('192.168.1.122', 'Bearer ' + JETON[:-1]), 401)
        self.assertNotIn(JETON, a.resume())

    def test_reseaux(self):
        r = lire_reseaux(' 192.168.1.0/24 , 100.64.0.0/10,')
        self.assertEqual(len(r), 2)
        a = Acces(JETON, r)
        self.assertTrue(a.adresse_autorisee('100.90.188.53'))
        self.assertFalse(a.adresse_autorisee('pas-une-ip'))


if __name__ == '__main__':
    unittest.main()
