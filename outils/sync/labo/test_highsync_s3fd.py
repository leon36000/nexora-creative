"""Contrat des boîtes du détecteur expérimental, sans modèle chargé."""
import unittest

from outils.sync.labo.highsync_s3fd import choisir


class ChoixS3FDTest(unittest.TestCase):
    def test_choix_plus_grande_face_confiance_et_bornage(self):
        detections = [(4, 4, 14, 14, .99), (-4, 5, 40, 60, .7), (0, 0, 99, 99, .5)]
        self.assertEqual(choisir(detections, 30, 50), (0, 5, 30, 50, .7))

    def test_aucune_detection_ne_fabrique_une_boite(self):
        self.assertIsNone(choisir([(0, 0, 10, 10, .5)], 30, 50))
        self.assertIsNone(choisir([], 30, 50))

    def test_donnee_invalide_refusee(self):
        with self.assertRaises(ValueError):
            choisir([(0, 0, float('nan'), 10, .8)], 30, 50)
        with self.assertRaises(ValueError):
            choisir([(0, 0, 10)], 30, 50)


if __name__ == '__main__':
    unittest.main()
