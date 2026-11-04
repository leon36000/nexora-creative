"""Tests du noyau et des écrivains. Lancer : python -m unittest discover -s outils/detourage/tests (voir README)."""
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import ecriture as E  # noqa: E402
import noyau as N  # noqa: E402

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None
try:
    import OpenEXR
except Exception:  # pragma: no cover
    OpenEXR = None


class Segments(unittest.TestCase):
    def test_une_seule_fenetre(self):
        self.assertEqual(N.plan_segments(50, 96, 12), [{'debut': 0, 'fin': 50}])

    def test_recouvrement_et_couverture(self):
        segs = N.plan_segments(300, 96, 12)
        self.assertEqual(segs[0]['debut'], 0)
        self.assertEqual(segs[-1]['fin'], 300)
        for a, b in zip(segs, segs[1:]):
            self.assertEqual(a['fin'] - b['debut'], 12)

    def test_dernier_segment_trop_court_fusionne(self):
        segs = N.plan_segments(100, 96, 12)  # un 2e segment de 16 images ne ferait que recouvrir
        self.assertTrue(all((s['fin'] - s['debut']) > 12 for s in segs))
        self.assertEqual(segs[-1]['fin'], 100)

    def test_poids_somment_a_un_dans_les_recouvrements(self):
        segs = N.plan_segments(300, 96, 12)
        for f in range(300):
            total = sum(N.poids_segment(f, i, segs, 12) for i in range(len(segs)))
            self.assertAlmostEqual(total, 1.0, places=6, msg=f'image {f}')

    def test_vecteur_commun_avec_le_serveur(self):
        segs = N.plan_segments(200, 100, 8)
        self.assertEqual(segs, [{'debut': 0, 'fin': 100}, {'debut': 92, 'fin': 192}, {'debut': 184, 'fin': 200}])
        self.assertEqual([round(N.poids_segment(f, 1, segs, 8), 4) for f in (92, 93, 96, 99, 100)],
                         [0.1111, 0.2222, 0.5556, 0.8889, 1.0])

    def test_coupure_interdit_le_recouvrement(self):
        segs = N.plan_segments(10, 4, 1)  # contrôle : sans coupure ça recouvre
        self.assertTrue(any(a['fin'] > b['debut'] for a, b in zip(segs, segs[1:])))
        pl = N.plan_plans(60, [25], 20, 4)
        self.assertEqual({s['plan'] for s in pl}, {0, 1})
        for a, b in zip(pl, pl[1:]):
            if a['plan'] != b['plan']:
                self.assertEqual(a['fin'], b['debut'])  # aucun recouvrement à travers la coupure
                self.assertEqual(b['debut'], 25)
        for f in range(60):
            self.assertAlmostEqual(sum(N.poids_segment(f, i, pl, 4) for i in range(len(pl))), 1.0, places=6)

    def test_raccord_fond_constant(self):
        segs = N.plan_segments(40, 20, 6)
        parts = [(s['debut'], np.full((s['fin'] - s['debut'], 4, 4), 0.7, np.float32)) for s in segs]
        out = N.raccorder(parts, segs, 40, 6)
        self.assertTrue(np.allclose(out, 0.7, atol=1e-6))

    def test_raccord_lisse_un_saut(self):
        segs = N.plan_segments(30, 20, 10)  # recouvrement 10 : A=0..19, B=10..29
        a = np.zeros((20, 2, 2), np.float32)
        b = np.ones((20, 2, 2), np.float32)
        out = N.raccorder([(0, a), (10, b)], segs, 30, 10)
        col = out[:, 0, 0]
        self.assertEqual(col[5], 0.0)
        self.assertEqual(col[25], 1.0)
        self.assertTrue(np.all(np.diff(col[9:21]) >= -1e-6))  # monotone dans le recouvrement


@unittest.skipIf(cv2 is None, 'OpenCV absent')
class Masques(unittest.TestCase):
    def setUp(self):
        self.m = np.zeros((200, 200), np.float32)
        self.m[50:150, 60:140] = 1.0

    def test_trimap_trois_niveaux(self):
        t = N.trimap(self.m, 8, 8)
        self.assertEqual(set(np.unique(t)), {0, 128, 255})
        self.assertEqual(t[100, 100], 255)
        self.assertEqual(t[10, 10], 0)
        self.assertEqual(t[50, 100], 128)  # exactement sur le bord : zone inconnue

    def test_fusion_garde_les_zones_sures(self):
        t = N.trimap(self.m, 8, 8)
        mat = np.full(self.m.shape, 0.5, np.float32)
        a = N.fusionner(self.m, mat, t)
        self.assertEqual(a[100, 100], 1.0)
        self.assertEqual(a[10, 10], 0.0)
        self.assertEqual(a[50, 100], 0.5)

    def test_boite(self):
        self.assertEqual(N.boite(self.m), (60, 50, 140, 150))
        self.assertIsNone(N.boite(np.zeros((8, 8), np.float32)))

    def test_avant_plan_retire_le_fond_du_bord(self):
        # un sujet rouge sur fond vert, bord à 50 % : l'avant-plan estimé doit être plus rouge que le pixel mélangé
        h = w = 64
        alpha = np.zeros((h, w), np.float32)
        alpha[:, 32:] = 1.0
        alpha[:, 31] = 0.5
        fg = np.zeros((h, w, 3), np.float32); fg[..., 0] = 1.0
        bg = np.zeros((h, w, 3), np.float32); bg[..., 1] = 1.0
        img = fg * alpha[..., None] + bg * (1 - alpha[..., None])
        f = N.avant_plan(img, alpha, 15, 3)
        self.assertGreater(f[10, 31, 0], img[10, 31, 0] + 0.2)
        self.assertLess(f[10, 31, 1], img[10, 31, 1])

    def test_composer_over(self):
        fg = np.ones((2, 2, 3), np.float32)
        fond = np.zeros((2, 2, 3), np.float32)
        a = np.array([[0.0, 0.25], [0.5, 1.0]], np.float32)
        out = N.composer(fg, a, fond)
        self.assertTrue(np.allclose(out[..., 0], a))


@unittest.skipIf(cv2 is None, 'OpenCV absent')
class Temps(unittest.TestCase):
    def _sequence(self, n=8, bruit=0.0, seed=1):
        rng = np.random.default_rng(seed)
        rgbs, alphas = [], []
        base = (rng.random((96, 96, 3)) * 255).astype(np.uint8)
        for t in range(n):
            im = np.roll(base, 2 * t, axis=1)  # texture qui défile de 2 px par image
            a = np.zeros((96, 96), np.float32)
            a[20:76, 20 + 2 * t:70 + 2 * t] = 1.0
            a = cv2.GaussianBlur(a, (0, 0), 1.5)
            a = np.clip(a + rng.normal(0, bruit, a.shape).astype(np.float32), 0, 1)
            rgbs.append(im)
            alphas.append(a)
        return alphas, rgbs

    def test_le_lissage_reduit_le_scintillement(self):
        alphas, rgbs = self._sequence(bruit=0.08)
        avant = N.scintillement(alphas, rgbs)
        apres = N.scintillement(N.lisser_temporel(alphas, rgbs), rgbs)
        self.assertLess(apres, avant * 0.9)

    def test_coeur_et_fond_ne_bougent_pas(self):
        alphas, rgbs = self._sequence(bruit=0.0)
        out = N.lisser_temporel(alphas, rgbs)
        self.assertTrue(np.allclose(out[3][40:60, 40:70], 1.0))
        self.assertTrue(np.allclose(out[3][:5, :5], 0.0))

    def test_sans_voisines_rien_ne_change(self):
        alphas, rgbs = self._sequence(n=2)
        out = N.lisser_temporel(alphas, rgbs)
        self.assertTrue(all(np.array_equal(a, b) for a, b in zip(alphas, out)))


class Ecriture(unittest.TestCase):
    def test_png16_gris_relu_par_opencv_et_entete(self):
        a = np.linspace(0, 1, 64 * 48, dtype=np.float32).reshape(48, 64)
        u = E.alpha_vers_u16(a)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'a.png')
            E.ecrire_png16(p, u)
            h = E.entete_png(p)
            self.assertEqual((h['bits'], h['type_couleur'], h['largeur'], h['hauteur']), (16, 0, 64, 48))
            if cv2 is not None:
                r = cv2.imread(p, cv2.IMREAD_UNCHANGED)
                self.assertEqual(r.dtype, np.uint16)
                self.assertTrue(np.array_equal(r, u))  # sans perte, valeurs 16 bits exactes (pas 8 bits promus)

    def test_png16_rgba(self):
        rgb = np.random.default_rng(0).random((20, 30, 3)).astype(np.float32)
        a = np.random.default_rng(1).random((20, 30)).astype(np.float32)
        u = E.rgba_vers_u16(rgb, a)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'c.png')
            E.ecrire_png16(p, u)
            self.assertEqual(E.entete_png(p)['type_couleur'], 6)
            if cv2 is not None:
                r = cv2.imread(p, cv2.IMREAD_UNCHANGED)  # OpenCV relit en BGRA
                self.assertTrue(np.array_equal(r[..., 2], u[..., 0]))
                self.assertTrue(np.array_equal(r[..., 3], u[..., 3]))

    def test_valeurs_16_bits_distinctes_de_8_bits(self):
        u = E.alpha_vers_u16(np.array([[0.0, 1 / 65535, 0.5, 1.0]], np.float32))
        self.assertEqual(list(u[0]), [0, 1, 32768, 65535])

    def test_exr_rgba_aller_retour_et_premultiplication(self):
        rng = np.random.default_rng(3)
        rgb = rng.random((37, 50, 3)).astype(np.float32)  # hauteur non multiple de 16 : dernier bloc partiel
        a = rng.random((37, 50)).astype(np.float32)
        rgba = np.concatenate([rgb * a[..., None], a[..., None]], axis=2)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.exr')
            E.ecrire_exr(p, rgba=rgba, premultiplie=True)
            r = E.lire_exr(p)
            self.assertEqual(r['alpha'], 'premultiplied')
            self.assertEqual(set(r['bits'].values()), {16})
            self.assertEqual(set(r['canaux']), {'R', 'G', 'B', 'A'})
            for i, n in enumerate('RGBA'):
                self.assertTrue(np.allclose(r['canaux'][n], rgba[..., i], atol=2e-3), n)
            # la couleur est bien déjà multipliée par l'alpha : R ≤ A partout
            self.assertTrue(np.all(r['canaux']['R'] <= r['canaux']['A'] + 2e-3))
            if OpenEXR is not None:  # relecture indépendante par la bibliothèque officielle
                f = OpenEXR.File(p)
                px = f.channels()['RGBA'].pixels
                self.assertEqual(px.shape, (37, 50, 4))
                self.assertEqual(px.dtype, np.float16)
                self.assertTrue(np.allclose(px[..., 3], rgba[..., 3], atol=2e-3))

    def test_exr_alpha_seul(self):
        a = np.random.default_rng(5).random((20, 33)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'a.exr')
            E.ecrire_exr(p, alpha=a)
            r = E.lire_exr(p)
            self.assertEqual(list(r['canaux']), ['A'])
            self.assertTrue(np.allclose(r['canaux']['A'], a, atol=2e-3))
            self.assertEqual(r['alpha'], 'straight')

    def test_exr_incompressible_stocke_tel_quel(self):
        rng = np.random.default_rng(9)
        a = rng.random((16, 16)).astype(np.float32)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'a.exr')
            E.ecrire_exr(p, alpha=a)
            self.assertTrue(np.allclose(E.lire_exr(p)['canaux']['A'], a, atol=2e-3))


if __name__ == '__main__':
    unittest.main()
