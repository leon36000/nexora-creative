"""Vérifications de l'horloge commune, du mixage et des neuf compositeurs.

python3 -B marketing/creative/video-v6/test_monter_v6.py
Lit seulement les médias de l'essai ; les éventuels fichiers temporaires sont dans V6_CACHE.
"""
import json
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stderr

sys.dont_write_bytecode = True
import numpy as np
import monter_v6 as v


class MoteurTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m, cls.b, cls.n, _ = v.charger(v.ICI/"montage-essai.json", "fr")

    def setUp(self):
        self.cache_avant = set((v.CACHE/"segments").glob("*.mp4"))

    def tearDown(self):
        # Nettoyer aussi après une assertion ratée, sans retirer un cache existant.
        for f in set((v.CACHE/"segments").glob("*.mp4"))-self.cache_avant:
            f.unlink(missing_ok=True)

    @staticmethod
    def montage_temp(dossier, **champs):
        f = Path(dossier)/"montage.json"
        m = {"marque": str(v.ICI/"marque-v6.json"),
             "segments": [{"type": "noir", "debut": 0, "duree": 1}], **champs}
        f.write_text(json.dumps(m))
        return f

    def test_sources_localisees_recursives_et_repli(self):
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            base = Path(d)
            for nom in ["base.png", "en.png", "fr.png", "vertical-en.png"]:
                v.Image.new("RGB", (32, 32), "white").save(base/nom)
            (base/"captures-en").mkdir()
            (base/"captures-fr").mkdir()
            source = {"fichier": "base.png", "fichier_en": "en.png", "fichier_fr": "fr.png"}
            obj = {"segments": [dict(source, type="plan", fichier_vertical_en="vertical-en.png"),
                    {"type": "saisie", "dossier": "absent", "dossier_en": "captures-en", "dossier_fr": "captures-fr"},
                    {"type": "boost", "dossier": "absent", "dossier_en": "captures-en", "dossier_fr": "captures-fr"},
                    {"media": source, "sur_video": source, "couches": [source], "rushes": [source]}]}
            for langue in ["en", "fr"]:
                m = v.resoudre(obj, base, langue)
                self.assertEqual(m["segments"][0]["fichier"], str(base/f"{langue}.png"))
                for s in m["segments"][1:3]:
                    self.assertEqual(s["dossier"], str(base/f"captures-{langue}"))
                s = m["segments"][3]
                for child in [s["media"], s["sur_video"], *s["couches"], *s["rushes"]]:
                    self.assertEqual(child["fichier"], str(base/f"{langue}.png"))
            m = v.resoudre(obj, base, "en")
            self.assertEqual(m["segments"][0]["fichier_vertical"], str(base/"vertical-en.png"))
            for key in ["fichier", "fichier_vertical", "dossier"]:
                with self.subTest(key=key), redirect_stderr(io.StringIO()) as avertissement:
                    spec = {"fichier": "base.png", "dossier": "captures-fr", f"{key}_en": "introuvable"}
                    r = v.resoudre(spec, base, "en")
                    self.assertEqual(r[key], str(base/("captures-fr" if key == "dossier" else "base.png")))
                    self.assertIn("Avertissement", avertissement.getvalue())

    def test_sources_localisees_chargees_image_et_son_vertical(self):
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            rush = self.m["segments"][3]["fichier"]
            f = self.montage_temp(d, segments=[{"type": "plan", "debut": 0, "duree": .5,
                "fichier": "absent.mp4", "fichier_en": rush, "fichier_fr": "fr-absent.mp4",
                "fichier_vertical_en": rush, "son_db": 0}])
            m, b, n, deps = v.charger(f, "en")
            self.assertEqual(m["_medias_absents"], [])
            self.assertIn(rush, [p for p, _, _ in deps])
            # Utiliser deux chemins distincts pour vérifier le choix effectif en 9:16.
            s = m["segments"][0]
            s["fichier_vertical"] = "vertical-virtuel"
            r = v.Rendu(m, b, "9x16", "en", taille=(90, 160))
            with patch.object(r.lecteur, "image", return_value=v.Image.new("RGB", (90, 160))) as lecture:
                r.image(s, .2)
            self.assertEqual(lecture.call_args.args[0], "vertical-virtuel")
            with patch.object(v, "sonder", return_value={"streams": [{"codec_type": "audio"}]}), \
                    patch.object(v, "lire_audio", side_effect=self.audio_horloge) as lecture_audio:
                a = v.mixer(m, "en", "9x16", n)
            self.assertEqual(lecture_audio.call_args.args[0], "vertical-virtuel")
            self.assertGreater(a[int(.2*v.SR), 0], .19)
            with redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "Source absente"):
                    v.charger(f, "fr")
            f = self.montage_temp(d, segments=[{"type": "plan", "debut": 0, "duree": .5,
                "fichier": rush, "fichier_en": "en-absent.mp4", "fichier_vertical_en": "vertical-absent.mp4"}])
            with redirect_stderr(io.StringIO()) as avertissement:
                m, _, _, _ = v.charger(f, "en")
            self.assertEqual(m["segments"][0]["fichier"], rush)
            self.assertEqual(m["segments"][0]["fichier_vertical"], rush)
            self.assertEqual(m["_medias_absents"], [])
            self.assertEqual(avertissement.getvalue().count("Avertissement"), 2)

    def test_trous_musique_fondus_chevauchements_et_horloge_film(self):
        def constant(f, debut=0, duree=None):
            return np.ones((round(duree*v.SR), 2), np.float32)
        m = {"musique": {"fichier": "virtuel", "coupes": [[1, 5]],
                         "trous": [[.5, 1.25], [1, 1.5], [2.95, 4]]}, "segments": []}
        with patch.object(v, "lire_audio", constant):
            a = v.musique(m, 3*v.SR)
            extrait = v.mixer(m, "fr", "16x9", 72, de=12, fin=48)
        self.assertAlmostEqual(a[int(.48*v.SR), 0], 1)
        self.assertAlmostEqual(a[int(.4925*v.SR), 0], .5, places=5)
        self.assertEqual(float(a[int(.5*v.SR):int(1.5*v.SR)].max()), 0)
        self.assertAlmostEqual(a[int(1.5075*v.SR), 0], .5, places=5)
        self.assertAlmostEqual(a[int(1.52*v.SR), 0], 1)
        self.assertEqual(float(a[int(2.95*v.SR):].max()), 0)
        np.testing.assert_array_equal(extrait, a[v.SR//2:2*v.SR])

    def test_trou_ne_coupe_ni_voix_ni_son_natif_et_db_voix(self):
        def constant(f, debut=0, duree=None):
            return np.full((round((duree if duree is not None else 1)*v.SR), 2),
                           {"musique": 1., "voix": 2., "rush": 3.}[f], np.float32)
        m = {"musique": {"fichier": "musique", "trous": [[.2, .8]], "ducking_db": 12},
             "voix": [{"fichier": "voix", "t": 0, "db": -6}],
             "segments": [{"type": "plan", "debut": 0, "duree": 1, "fichier": "rush", "son_db": -3}]}
        with patch.object(v, "lire_audio", constant), \
                patch.object(v, "sonder", return_value={"streams": [{"codec_type": "audio"}]}):
            a = v.mixer(m, "fr", "16x9", 24)
        attendu = 2*10**(-6/20)+3*10**(-3/20)
        self.assertAlmostEqual(a[v.SR//2, 0], attendu, places=5)
        self.assertAlmostEqual(a[int(.1*v.SR), 0], attendu+10**(-12/20), places=5)
        for db in [0, 3, 12]:
            g = v.ducking(3*v.SR, [(1, 1.5), (1.4, 2)], db)
            self.assertAlmostEqual(g[int(1.6*v.SR)], 10**(-db/20), places=5)
            self.assertAlmostEqual(g[int(.97*v.SR)], 10**(-db*.5/20), places=5)

    def test_validation_trous_et_ducking(self):
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            for champs in [{"trous": [[1, 0]]}, {"trous": [[-1, 1]]}, {"trous": [[0, float("inf")]]},
                           {"trous": [[0]]}, {"trous": [["a", 1]]}, {"ducking_db": -1},
                           {"ducking_db": float("nan")}, {"ducking_db": "7"}]:
                f = self.montage_temp(d, musique=champs)
                with self.subTest(champs=champs), self.assertRaises(ValueError):
                    v.charger(f, "fr")

    def test_tolerant_noir_et_sources_imbriquees(self):
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            manquant = str(Path(d)/"rush-introuvable.mp4")
            segments = [
                {"type": "plan", "fichier": manquant, "son_db": 0},
                {"type": "saisie", "dossier": "captures-absentes"},
                {"type": "boost", "dossier": "boost-absent"},
                {"type": "titre", "texte_id": "tourne", "sur_video": {"fichier": manquant}},
                {"type": "chapitre", "texte_id": "chapitre_boost", "media": manquant},
                {"type": "avant_apres", "couches": [manquant, manquant]},
                {"type": "mosaique", "rushes": [manquant]*3}]
            for i, s in enumerate(segments):
                s.update(debut=i, duree=1, sfx_auto=False)
            f = self.montage_temp(d, segments=segments)
            with self.assertRaisesRegex(ValueError, "Source absente"):
                v.charger(f, "fr")
            with redirect_stderr(io.StringIO()):
                m, b, n, _ = v.charger(f, "fr", tolerant=True)
            self.assertEqual(len(m["_medias_absents"]), 3)
            for fmt in ["16x9", "9x16"]:
                r = v.Rendu(m, b, fmt, "fr", taille=(320, 180) if fmt == "16x9" else (180, 320))
                for s in m["segments"]:
                    im = np.asarray(r.image(s, .5))
                    self.assertGreater(im.max(), 100)
                noir = np.asarray(r.image(m["segments"][0], .5))
                self.assertTrue(np.all(noir[0] == 0))
                self.assertGreater(np.count_nonzero(noir), 30)
            np.testing.assert_array_equal(v.mixer(m, "fr", "16x9", n), 0)

    def test_tolerant_capture_journal_absente_et_json_invalide_refuse(self):
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            folder = Path(d)/"captures"
            folder.mkdir()
            journal = folder/"journal.jsonl"
            journal.write_text(json.dumps({"t": 0, "etiquette": "saisie", "image": "absente.jpg"})+"\n")
            f = self.montage_temp(d, segments=[{"type": "saisie", "dossier": "captures", "debut": 0, "duree": 1}])
            with self.assertRaisesRegex(ValueError, "absente.jpg"):
                v.charger(f, "fr")
            with redirect_stderr(io.StringIO()):
                m, b, _, _ = v.charger(f, "fr", tolerant=True)
            self.assertEqual(m["_medias_absents"], [str(folder/"absente.jpg")])
            r = v.Rendu(m, b, "16x9", "fr", taille=(320, 180))
            self.assertGreater(np.asarray(r.image(m["segments"][0], .5)).max(), 100)
            journal.write_text("{invalide}\n")
            v.sequence.cache_clear()
            with self.assertRaises(json.JSONDecodeError):
                v.charger(f, "fr", tolerant=True)

    def test_tolerant_rapport_et_audio_absent(self):
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            f = self.montage_temp(d, segments=[{"type": "plan", "fichier": "absent.mp4", "debut": 0,
                    "duree": .25, "son_db": 0}], musique={"fichier": "musique-absente.wav"},
                    voix=[{"id": "voix-absente", "t": 0}], dossiers_voix={"fr": "voix"})
            film = Path(d)/"animatique.mp4"
            args = v.parser().parse_args([str(f), "--format", "16x9", "--langue", "fr", "--sortie", str(film),
                                         "--tolerant", "--brouillon", "--jobs", "1"])
            with redirect_stderr(io.StringIO()):
                rapport = v.construire(args)
            self.assertTrue(rapport["tolerant"])
            self.assertEqual(len(rapport["medias_absents"]), 3)
            self.assertEqual(json.loads(film.with_suffix(".rendu.json").read_text())["medias_absents"], rapport["medias_absents"])
            self.assertEqual(rapport["images"], 6)

    def test_boost_long_cles_sequentielles_centrees_deux_formats(self):
        folder = Path(self.m["segments"][1]["dossier"]).parent
        texte = "\n".join(json.loads((folder/s/"boost.json").read_text())["boost"]
                          for s in ["s01", "s02", "s03", "s04", "s08", "s10"])
        self.assertGreater(len(texte), 2500)
        termes = ["dragon", "bataille spatiale", "orage", "monstre marin", "petit chat"]
        mots = v.mots_boost(texte, termes, .96)
        self.assertEqual([m for m, important in mots if important], termes)
        self.assertLessEqual(len(mots), len(termes)+12)
        s = dict(self.m["segments"][1], _texte_boost=texte, termes_cles=termes, duree=.96, debut=0)
        for fmt in ["16x9", "9x16"]:
            r = v.Rendu({"segments": [s]}, self.b, fmt, "fr", True)
            for terme, debut, fin in v.cles_boost(s):
                self.assertIn(fin-debut, [2, 3])
                im = np.asarray(r.image(s, debut/v.IPS))
                np.testing.assert_array_equal(im, np.asarray(r.image(s, debut/v.IPS)))
                ys, xs = np.where(np.all(im == r.c["signal"], axis=2))
                self.assertGreater(len(xs), 100)
                self.assertGreaterEqual(xs.min(), .04*r.W)
                self.assertLess(xs.max(), .96*r.W)
                self.assertGreater(ys.max()-ys.min(), .12*r.H)
                self.assertAlmostEqual((xs.min()+xs.max())/2/r.W, .5, delta=.06)
                self.assertAlmostEqual((ys.min()+ys.max())/2/r.H, .49, delta=.08)
            self.assertFalse(np.array_equal(np.asarray(r.image(s, .3)), np.asarray(r.image(s, .6))))
            self.assertLess(len(r.sprites), 80)  # coût borné même avec six prompts

    def test_boost_saisie_reelle_lexique_et_surcharge(self):
        self.assertEqual(v.fautes_boost("dragn chateau feu"), {"dragn", "chateau"})
        self.assertEqual(v.fautes_boost("dragon château fire"), set())
        self.assertEqual(v.fautes_boost("dragon atak croiseur spatial"), {"atak"})
        self.assertEqual(v.fautes_boost("inconnu feu", []), set())
        self.assertEqual(v.fautes_boost("dragon feu", ["feu"]), {"feu"})
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            dossier = Path(self.m["segments"][1]["dossier"])
            data = Path(d)/"boost.json"
            data.write_text(json.dumps({"mots": ["dragon", "feu"], "fautes": ["feu"], "boost": "texte réel"}))
            f = self.montage_temp(d, segments=[{"type": "boost", "debut": 0, "duree": .72,
                "dossier": str(dossier), "boost_json": str(data), "texte": "surcharge réelle"}])
            m, _, _, deps = v.charger(f, "fr")
            s = m["segments"][0]
            self.assertEqual(s["_texte_boost"], "surcharge réelle")
            self.assertEqual(s["_mots_saisis"], "dragon feu")
            self.assertEqual(s["_fautes"], ["feu"])
            self.assertIn(str(data), [dep[0] for dep in deps])
        s = dict(self.m["segments"][1], debut=1.68, duree=.72,
                 _mots_saisis="dragn chateau feu", _fautes=["dragn", "chateau"],
                 termes_cles=["dragon", "château", "feu", "flammes", "rugissant", "travelling circulaire", "nuit"])
        r = v.Rendu({"segments": [s]}, self.b, "16x9", "fr", True)
        lettres, traits = r.lettres_boost(s)
        self.assertEqual(len(lettres), len("dragnchateaufeu"))
        self.assertEqual(len(traits), 2)
        rouge = np.asarray(r.image(s, 0))
        self.assertGreater(((rouge[:,:,0] > 200) & (rouge[:,:,1] < 100)).sum(), 50)
        # La projection change la silhouette ; les éclats sortent du bloc central.
        explosion = np.asarray(r.image(s, 2/v.IPS))
        self.assertFalse(np.array_equal(rouge, explosion))
        _, n, a, b = v.horloge_boost(s, 0)
        self.assertLessEqual(len(v.cles_boost(s)), (b-a)//2)
        for i in range(n):
            t = max(0, (round(s["debut"]*v.IPS)+i)/v.IPS-s["debut"])
            blanc = np.all(np.asarray(r.image(s, t)) == 255)
            self.assertEqual(blanc, i >= n-2)
        self.assertEqual([e["type"] for e in v.evenements_auto({"segments": [s]})], ["souffle", "riser"])

    def test_saisie_ligne_large_correcteur_et_zoom(self):
        s = self.m["segments"][0]
        for fmt in ["16x9", "9x16"]:
            r = v.Rendu(self.m, self.b, fmt, "fr", True)
            im = np.asarray(r.image(s, s["duree"]*.97))
            # La zone nette se trouve au centre vertical, la typographie de l'UI
            # environnante reste hors de cette mesure.
            roi = im[round(r.H*.45):round(r.H*.56)].astype(np.int16)
            ys, xs = np.where((roi.min(2) > 140) & (roi.max(2)-roi.min(2) < 50))
            self.assertGreater(xs.max()-xs.min(), r.W*.35)
            self.assertGreater(((roi[:,:,0] > 130) & (roi[:,:,0] > roi[:,:,1]*1.8)).sum(), 20)
            src = v.capture(v.fichier_capture(s, s["duree"]*.97))
            normal = r.cadre_saisie(src, s, .1)
            zoom = r.cadre_saisie(src, dict(s, zoom_texte=1.2), .1)
            self.assertAlmostEqual(zoom[2]/normal[2], 1.2)
            cible = dict(s, zone_texte=[104, 300, 470, 345])
            self.assertEqual(r.image(cible, .5).size, (r.W, r.H))
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            for valeur in [0, -1, float("nan"), "1"]:
                f = self.montage_temp(d, segments=[dict(s, zoom_texte=valeur)])
                with self.assertRaisesRegex(ValueError, "zoom_texte"):
                    v.charger(f, "fr")

    def test_chapitre_zone_titre_panneau_entree(self):
        # Hors de la zone : magenta ; dans la zone : vert. Aucun pixel magenta
        # ne doit revenir dans le panneau, quel que soit son rapport d'aspect.
        source = v.Image.new("RGB", (160, 90), (255, 0, 255))
        v.ImageDraw.Draw(source).rectangle((20, 20, 119, 69), fill=(0, 180, 0))
        spec = {"fichier": "source.png", "zone": [20, 20, 120, 70], "viewport": [160, 90]}
        for fmt in ["16x9", "9x16"]:
            r = v.Rendu(self.m, self.b, fmt, "fr", True)
            with patch.object(r.lecteur, "image", return_value=source):
                panneau = np.asarray(r.source(spec, .3, 300, 200, decouper_zone=True))
                np.testing.assert_array_equal(panneau, np.broadcast_to([0, 180, 0], panneau.shape))
                s = {"type": "chapitre", "texte_id": "chapitre_boost", "media": spec, "debut": 0, "duree": 2}
                entree = np.asarray(r.image(s, 0))
                arrivee = np.asarray(r.image(s, 3/v.IPS))
            vert = np.all(arrivee == [0, 180, 0], axis=2)
            yy, xx = np.where(vert)
            self.assertAlmostEqual((xx.max()-xx.min()+1)/r.W, .92 if r.vertical else .86, delta=.005)
            self.assertLess(np.all(entree == [0, 180, 0], axis=2).sum(), vert.sum()*.90)
            titre = np.asarray(r.titre_chapitre("3D RELIEF"))
            for couleur in [r.c["os"], r.c["signal"]]:
                yy, xx = np.where(np.all(titre[:,:,:3] == couleur, axis=2) & (titre[:,:,3] > 0))
                self.assertGreater(yy.max()-yy.min(), r.H*.065)

    def test_integrale_exacte_et_retour_arriere(self):
        ramp = [[.25, 2.], [1.25, .5], [2., 1.5]]
        for t in [0, .1, .25, .7, 1.25, 1.9, 2., 3.1]:
            dense = np.linspace(0, t, 100001)
            valeur = np.trapezoid(np.interp(dense, *np.asarray(ramp).T), dense)
            self.assertAlmostEqual(float(v.integrale_vitesse(ramp, t)), valeur, places=8)
        seg = {"entree": 8, "inverse": True, "vitesse": ramp}
        self.assertAlmostEqual(float(v.temps_source(seg, 2)), 8-2.5, places=8)

    def test_coupes_globales_sans_derive(self):
        ranges = [(round(s["debut"]*24), round((s["debut"]+s["duree"])*24)) for s in self.m["segments"]]
        self.assertEqual(sum(b-a for a, b in ranges), 288)
        self.assertEqual([b for a, b in ranges[:-1]], [a for a, b in ranges[1:]])
        de, fin = 37, 203
        self.assertEqual(sum(max(0, min(fin, b)-max(de, a)) for a, b in ranges), fin-de)

    def test_ducking_7db_et_chevauchement(self):
        n = 3*v.SR
        gain = v.ducking(n, [(1., 1.5), (1.4, 2.)])
        self.assertAlmostEqual(gain[int(.90*v.SR)], 1)
        self.assertAlmostEqual(gain[int(.97*v.SR)], 10**(-3.5/20), places=5)
        self.assertAlmostEqual(gain[int(1.6*v.SR)], 10**(-7/20), places=5)
        self.assertAlmostEqual(gain[int(2.125*v.SR)], 10**(-3.5/20), places=5)
        self.assertAlmostEqual(gain[int(2.25*v.SR)], 1)

    def test_pose_negative_et_fin_bornee(self):
        piste = np.zeros((10, 2), np.float32)
        son = np.arange(10, dtype=np.float32)[:, None]*np.ones((1, 2))
        v.poser(piste, son, -3/v.SR)
        np.testing.assert_array_equal(piste[:7, 0], np.arange(3, 10))
        self.assertEqual(float(piste[7:].sum()), 0)

    @staticmethod
    def audio_horloge(f, debut=0, duree=None):
        t = debut+np.arange(round(duree*v.SR))/v.SR
        return np.stack([t, t], 1).astype(np.float32)

    def test_musique_fondu_centre_sans_dephasage(self):
        m = {"musique": {"fichier": "virtuel", "entree": 0, "coupes": [[1, 5]]}}
        with patch.object(v, "lire_audio", self.audio_horloge):
            a = v.musique(m, 2*v.SR)
        self.assertAlmostEqual(a[int(.5*v.SR), 0], .5, places=5)
        self.assertAlmostEqual(a[v.SR, 0], 3, places=5)
        self.assertAlmostEqual(a[int(1.02*v.SR), 0], 5.02, places=5)

    def test_son_natif_suit_integrale_image_et_inverse(self):
        for inverse in [False, True]:
            seg = {"type": "plan", "debut": 1/24, "duree": 1, "entree": 3 if inverse else .5,
                   "vitesse": [[0, 1.5], [.5, .3], [1, 1.]], "inverse": inverse, "fichier": "virtuel", "son_db": 0}
            m = {"segments": [seg]}
            with patch.object(v, "lire_audio", self.audio_horloge), patch.object(v, "sonder", return_value={"streams": [{"codec_type": "audio"}]}):
                a = v.mixer(m, "fr", "16x9", 26)
            for t in [.1, .4, .7, .9]:
                i = round((seg["debut"]+t)*v.SR)
                expected = v.temps_source(seg, i/v.SR-seg["debut"])
                self.assertAlmostEqual(a[i, 0], float(expected), places=5)
            self.assertEqual(a[2000, 0], 0)  # fondu d'entrée de 10 ms

    def test_clavier_une_fois_par_nouvelle_image(self):
        s = self.m["segments"][0]
        events = [e for e in v.evenements_auto({"segments": [s]}) if e["type"] == "clavier"]
        self.assertEqual(len(events), 17)
        self.assertEqual(len({e["t"] for e in events}), 17)

    def test_neuf_types_deux_formats_deux_langues(self):
        for fmt in ["16x9", "9x16"]:
            for langue in ["fr", "en"]:
                m, b, _, _ = v.charger(v.ICI/"montage-essai.json", langue)
                taille = (320, 180) if fmt == "16x9" else (180, 320)
                r = v.Rendu(m, b, fmt, langue, taille=taille)
                for seg in m["segments"]:
                    im = r.image(seg, seg["duree"]*.4)
                    self.assertEqual(im.size, taille)
                    self.assertEqual(im.mode, "RGB")
                    self.assertGreater(np.asarray(im).std(), 1)
                rush = m["segments"][3]["fichier"]
                extra = [
                    {"type": "noir", "texte_id": "souffle", "style": "balayage"},
                    {"type": "titre", "texte_id": "modalites", "style": "empile"},
                    {"type": "titre", "texte_id": "tourne", "style": "balayage", "sur_video": {"fichier": rush}},
                    {"type": "chapitre", "texte_id": "chapitre_boost", "media": {"dossier": m["segments"][0]["dossier"], "etapes": ["boost"], "duree": 2}, "en_preparation": True},
                    {"type": "avant_apres", "couches": [{"fichier": rush}, {"type": "damier"}, {"fichier": rush}]},
                    {"type": "mosaique", "rushes": [{"fichier": rush} for _ in range(9)]}
                ]
                for seg in extra:
                    seg.update(debut=0, duree=5)
                    seg["textes"] = [{"t": 0, "duree": 5, "texte_id": "preparation", "style": "legende", "position": "bas"}]
                    self.assertEqual(r.image(seg, 4.5).size, taille)

    def test_lecteur_inverse_et_bloc_borne(self):
        lecteur = v.Lecteur()
        f = self.m["segments"][3]["fichier"]
        a = lecteur.image(f, .5)
        for t in [1.2, 2.2, 1.5, .5]:
            lecteur.image(f, t)
            self.assertLessEqual(len(lecteur.blocs), 2)
        np.testing.assert_array_equal(np.asarray(a), np.asarray(lecteur.image(f, .5)))

    def test_titre_quatre_mots_dans_marges_meme_pendant_claque(self):
        r = v.Rendu(self.m, self.b, "9x16", "fr", True)
        for t in [0, 1/24, 2/24, 4/24, .5]:
            im = r.cinetique(r.noir(), "MAKE YOUR NEXT FILM", "claque", t, 2)
            mask = np.any(np.asarray(im) != np.array(r.c["encre"]), axis=2)
            ys = np.where(mask)[0]
            self.assertGreaterEqual(ys.min(), np.ceil(.12*r.H))
            self.assertLess(ys.max(), np.floor(.80*r.H))

    def test_validation_textes_et_superpositions(self):
        v.CACHE.mkdir(parents=True, exist_ok=True)
        for bad in ["texte", "superposition"]:
            raw = json.loads((v.ICI/"montage-essai.json").read_text())
            raw["marque"] = str(v.ICI/"marque-v6.json")
            if bad == "texte":
                raw["segments"][2]["texte_id"] = "absent"
            else:
                raw["segments"][1]["debut"] = 0
            with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
                f = Path(d)/"m.json"
                f.write_text(json.dumps(raw))
                with self.assertRaises(ValueError):
                    v.charger(f, "fr")

    def test_master_court_web_et_reseaux(self):
        # Le plafond de crête peut empêcher loudnorm d'atteindre -10 LUFS sur
        # un montage court : vérifier le WAV réellement produit après calibration.
        son = v.mixer(self.m, "fr", "16x9", self.n, fin=192)
        v.CACHE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            for master, cible, plafond in [("web", -14, -1.5), ("reseaux", -10, -1)]:
                f = Path(d)/f"{master}.wav"
                v.masteriser(son, f, master)
                mesure = v.analyser_audio(f, master)
                self.assertLess(abs(float(mesure["input_i"])-cible), .16)
                self.assertLessEqual(float(mesure["input_tp"]), plafond)

    def test_master_reseaux_preserve_lufs_apres_aac(self):
        # Cas réel qui provoquait un dépassement AAC de ~0,2 dB et une perte
        # de loudness quand on corrigeait uniquement le volume après encodage.
        mu = dict(self.m["musique"])
        mu["coupes"] = [[4, mu["entree"]+4+4*60/self.m["bpm"]]]
        seg = dict(self.m["segments"][3], debut=4.5, duree=1, entree=2.5, inverse=True,
                   vitesse=[[0, 1.], [1, .5]], son_db=-9)
        m = {"marque": str(v.ICI/"marque-v6.json"), "duree": 8.5,
             "musique": mu, "segments": [seg], "sfx": self.m["sfx"]}
        v.CACHE.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=v.CACHE) as d:
            fichier, film = Path(d)/"m.json", Path(d)/"film.mp4"
            fichier.write_text(json.dumps(m))
            avant = set((v.CACHE/"segments").glob("*.mp4"))
            args = v.parser().parse_args([str(fichier), "--format", "9x16", "--langue", "en", "--sortie", str(film),
                                         "--master", "reseaux", "--de", ".25", "--a", "8.25", "--jobs", "1", "--brouillon"])
            rapport = v.construire(args)
            j = rapport["loudness_aac"]
            self.assertLessEqual(float(j["input_tp"]), -1)
            self.assertLess(abs(float(j["input_i"])+10), .25)
            video = next(s for s in v.sonder(str(film))["streams"] if s["codec_type"] == "video")
            self.assertEqual(int(video["nb_frames"]), 192)
            self.assertEqual((video["width"], video["height"]), (540, 960))
            for f in rapport["cache_segments"]:
                if Path(f) not in avant:
                    Path(f).unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
