"""Contrôles sans rendu des gardes et correspondances de montage."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import monter  # noqa: E402


class PlansVideoManquantsTests(unittest.TestCase):
    def test_present_sources_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            present = Path(tmp) / "p01-r1.mp4"
            present.write_bytes(b"video")

            self.assertEqual([], monter.verifier_sources_video("deepseek", "long", {"p01": present}))

    def test_missing_sources_are_named_and_intentional_ink_sources_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            present = Path(tmp) / "p01-r1.mp4"
            present.write_bytes(b"video")
            missing = Path(tmp) / "p27-r1.mp4"
            sources = {
                "p01": present,
                "p26": None,
                "p27": missing,
                "noir": None,
                "carton": None,
            }

            with self.assertRaises(monter.PlansVideoManquants) as err:
                monter.verifier_sources_video("deepseek", "long", sources)

        self.assertIn("deepseek/long", str(err.exception))
        self.assertIn("p26, p27", str(err.exception))

    def test_video_reference_missing_from_plan_sources_is_refused(self):
        with self.assertRaisesRegex(monter.PlansVideoManquants, "p99"):
            monter.verifier_sources_video("gemini", "long", {}, video=[{"src": "p99"}])

    def test_construire_rejects_video_reference_missing_from_source_map(self):
        ctx = SimpleNamespace(
            vid={}, voix={}, musique=None,
            plan={"video": [{"src": "p99"}], "audio": {}}, annexe={}, total=24,
            W=960, H=540,
        )
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.object(monter, "Contexte", return_value=ctx),
                patch.object(monter, "valider_ts") as valider,
                patch.object(monter, "ProcessPoolExecutor") as pool,
            ):
                with self.assertRaisesRegex(monter.PlansVideoManquants, "p99"):
                    monter.construire("gemini", "long", sortie=Path(tmp) / "draft.mp4", jobs=1)

        valider.assert_not_called()
        pool.assert_not_called()

    def test_construire_stops_before_editplan_validation_or_rendering(self):
        ctx = type("Context", (), {"vid": {"p26": None}, "plan": {"video": [{"src": "p26"}]}})()
        with tempfile.TemporaryDirectory() as tmp:
            montage = Path(tmp) / "montage"
            sortie = montage / "draft.mp4"
            with (
                patch.object(monter, "Contexte", return_value=ctx),
                patch.object(monter, "valider_ts") as valider,
                patch.object(monter, "rendre_tranche") as rendre,
                patch.object(monter, "ProcessPoolExecutor") as pool,
                patch.object(monter.T, "dossier_travail", return_value=montage) as dossier_travail,
            ):
                with self.assertRaisesRegex(monter.PlansVideoManquants, "p26"):
                    monter.construire("deepseek", "long", brouillon=True, sortie=sortie, jobs=1)

            valider.assert_not_called()
            rendre.assert_not_called()
            pool.assert_not_called()
            dossier_travail.assert_not_called()
            self.assertFalse(sortie.exists())

    def test_explicit_ts_validation_failure_stops_before_allocating_or_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "p01.mp4"
            source.write_bytes(b"video")
            output = root / "custom-name.mp4"
            ctx = SimpleNamespace(
                vid={"p01": source}, voix={}, musique=None,
                plan={"video": [{"src": "p01"}], "audio": {}}, annexe={}, total=24,
                W=960, H=540,
            )
            with (
                patch.object(monter, "Contexte", return_value=ctx),
                patch.object(monter, "valider_ts", return_value={"ok": False, "erreurs": [{"regle": "test", "message": "invalid"}]}),
                patch.object(monter, "ProcessPoolExecutor") as pool,
                patch.object(monter.T, "dossier_travail") as dossier_travail,
            ):
                with self.assertRaises(monter.EditPlanInvalide):
                    monter.construire("gemini", "long", sortie=output, jobs=1)

            pool.assert_not_called()
            dossier_travail.assert_not_called()
            self.assertFalse(output.exists())



class RepliVerticalTests(unittest.TestCase):
    def resoudre(self, source_id, choices):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        music = root / "deepseek" / "musique" / "lyria-1.wav"
        music.parent.mkdir(parents=True)
        music.write_bytes(b"audio")
        plan = {
            "format": "9:16",
            "sources": {source_id: {"kind": "video"}},
            "audio": {},
        }

        def selected(_equipe, pid, fmt="16:9"):
            return choices.get(pid)

        patcher = patch.multiple(
            monter.T,
            TRAVAIL=root,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.enterContext(patch.object(monter.T, "plan_retenu", side_effect=selected))
        self.enterContext(patch.object(monter.T, "choix", return_value={"plans": {}, "voix": {}, "musique": None}))
        self.enterContext(patch.object(monter.T, "dossier", return_value={"musique": {"prompts": []}}))
        return monter.resoudre("deepseek", plan, "vertical")

    def test_known_suffix_pair_falls_back_to_horizontal_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            horizontal = Path(tmp) / "p02-r1.mp4"
            horizontal.write_bytes(b"video")
            vid, _voix, _musique = self.resoudre("p02v", {"p02": horizontal})

        self.assertEqual(vid["p02v"], str(horizontal))

    def test_unmapped_vertical_id_is_left_missing_instead_of_guessed(self):
        vid, _voix, _musique = self.resoudre("v01", {})

        self.assertIsNone(vid["v01"])
        with self.assertRaisesRegex(monter.PlansVideoManquants, "v01"):
            monter.verifier_sources_video("deepseek", "vertical", vid)


class ExportPreservationTests(unittest.TestCase):
    def test_existing_export_is_refused_before_validation_or_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "p01-r1.mp4"
            source.write_bytes(b"source")
            output = root / "film.mp4"
            output.write_bytes(b"existing export")
            ctx = SimpleNamespace(vid={"p01": source}, plan={"video": [{"src": "p01"}]})

            with (
                patch.object(monter, "Contexte", return_value=ctx),
                patch.object(monter, "valider_ts") as valider,
                patch.object(monter, "ProcessPoolExecutor") as pool,
                patch.object(monter.T, "dossier_travail") as dossier_travail,
            ):
                with self.assertRaisesRegex(FileExistsError, "export existant"):
                    monter.construire("deepseek", "long", sortie=output, jobs=1)

            valider.assert_not_called()
            pool.assert_not_called()
            dossier_travail.assert_not_called()
            self.assertEqual(b"existing export", output.read_bytes())

    def test_render_keeps_labeled_tranches_and_disables_ffmpeg_overwrite(self):
        pools = []

        class FakePool:
            def __init__(self, _jobs, initializer=None, initargs=()):
                self.initializer = initializer
                self.initargs = initargs
                pools.append(self)

            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                return False

            def map(self, _func, tasks):
                tasks = list(tasks)
                for task in tasks:
                    Path(task[-1]).write_bytes(b"tranche")
                return [None] * len(tasks)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            out_dir = root / "montage"
            out_dir.mkdir()
            source = root / "p01-r1.mp4"
            source.write_bytes(b"source")
            output = out_dir / "custom-output.mp4"
            ctx = SimpleNamespace(vid={"p01": source}, voix={}, musique=None,
                                  plan={"video": [{"src": "p01"}], "audio": {}},
                                  annexe={"etalonnage": {"contraste": 1.03}, "incrustations": [{"type": "titre", "texte": "DÉMO"}]},
                                  total=36, W=960, H=540)
            commandes = []

            def mixer_factice(_ctx, fichier):
                Path(fichier).write_bytes(b"mix")

            def ffmpeg_factice(commande, check):
                commandes.append((commande, check))
                Path(commande[-1]).write_bytes(b"export")
                return SimpleNamespace(returncode=0)

            with (
                patch.object(monter, "Contexte", return_value=ctx),
                patch.object(monter, "valider_ts", return_value=None),
                patch.object(monter, "ProcessPoolExecutor", FakePool),
                patch.object(monter, "mixer", side_effect=mixer_factice),
                patch.object(monter.subprocess, "run", side_effect=ffmpeg_factice),
                patch.object(monter.T, "TRAVAIL", work),
                patch.object(monter.T, "dossier_travail", return_value=out_dir),
            ):
                result = monter.construire("deepseek", "long", brouillon=True, sortie=output, jobs=1)

            tranches = Path(result["tranches"])
            self.assertRegex(tranches.name, r"^tranches-deepseek-long-brouillon-\d{8}-\d{6}-\d+$")
            self.assertTrue((tranches / "t000000.mp4").is_file())
            self.assertTrue((tranches / "mix.wav").is_file())
            self.assertTrue(output.is_file())
            self.assertEqual(1, len(commandes))
            self.assertIn("-n", commandes[0][0])
            self.assertNotIn("-y", commandes[0][0])
            self.assertTrue(commandes[0][1])
            self.assertIs(result["brouillon"], True)
            self.assertEqual({"largeur": 960, "hauteur": 540}, result["resolution"])

            provenance = result["provenance"]
            self.assertEqual(monter.empreinte_editplan(ctx.plan), provenance["editplan_sha256"])
            self.assertEqual(monter.empreinte_annexe(ctx.annexe), provenance["annexe_sha256"])
            self.assertEqual(hashlib.sha256(b"source").hexdigest(), provenance["sources_sha256"]["video"]["p01"])
            self.assertEqual(hashlib.sha256(b"export").hexdigest(), provenance["export_sha256"])
            self.assertEqual("partielle", provenance["couverture"])
            for limite in ("polices", "logo", "code de montage", "configurations"):
                self.assertTrue(any(limite in item for item in provenance["non_couverts"]))
            self.assertIn("ne certifie pas l'exhaustivité", provenance["note_sources_absentes"])
            journal = json.loads((work / "journal-montage.jsonl").read_text().splitlines()[-1])
            self.assertEqual(provenance, journal["provenance"])
            self.assertIs(pools[0].initializer, monter.initialiser_contexte_rendu)
            self.assertEqual(monter.empreinte_editplan(ctx.plan), monter.empreinte_editplan(pools[0].initargs[-1]["plan"]))
            self.assertEqual({"p01": source}, pools[0].initargs[-1]["vid"])
            self.assertTrue(result["film"].endswith("custom-output.mp4"))
            self.assertTrue(result["brouillon"])
            self.assertEqual({"largeur": 960, "hauteur": 540}, result["resolution"])
            self.assertTrue(journal["brouillon"])
            self.assertEqual({"largeur": 960, "hauteur": 540}, journal["resolution"])

    def test_source_change_during_render_blocks_success_record_and_keeps_export(self):
        class FakePool:
            def __init__(self, _jobs, initializer=None, initargs=()):
                self.initializer = initializer
                self.initargs = initargs

            def __enter__(self):
                return self

            def __exit__(self, *_exc):
                return False

            def map(self, _func, tasks):
                tasks = list(tasks)
                for task in tasks:
                    Path(task[-1]).write_bytes(b"tranche")
                return [None] * len(tasks)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "work"
            work.mkdir()
            out_dir = root / "montage"
            out_dir.mkdir()
            source = root / "p01-r1.mp4"
            source.write_bytes(b"source")
            output = out_dir / "film.mp4"
            ctx = SimpleNamespace(vid={"p01": source}, voix={}, musique=None,
                                  plan={"video": [{"src": "p01"}], "audio": {}}, annexe={}, total=36)

            def mixer_factice(_ctx, fichier):
                Path(fichier).write_bytes(b"mix")
                source.write_bytes(b"changed during render")

            def ffmpeg_factice(commande, check):
                Path(commande[-1]).write_bytes(b"export")
                return SimpleNamespace(returncode=0)

            with (
                patch.object(monter, "Contexte", return_value=ctx),
                patch.object(monter, "valider_ts", return_value=None),
                patch.object(monter, "ProcessPoolExecutor", FakePool),
                patch.object(monter, "mixer", side_effect=mixer_factice),
                patch.object(monter.subprocess, "run", side_effect=ffmpeg_factice),
                patch.object(monter.T, "TRAVAIL", work),
                patch.object(monter.T, "dossier_travail", return_value=out_dir),
            ):
                with self.assertRaisesRegex(monter.ErreurProvenance, "a changé pendant le rendu"):
                    monter.construire("deepseek", "long", brouillon=True, sortie=output, jobs=1)

            self.assertTrue(output.is_file())
            self.assertFalse((work / "journal-montage.jsonl").exists())

    def test_worker_initializer_uses_the_frozen_context_snapshot(self):
        snapshot = {"plan": {"version": 1}, "annexe": {}, "vid": {}, "voix": {}, "musique": None}
        with patch.object(monter, "contexte") as build_context:
            monter.initialiser_contexte_rendu("gemini", "long", True, snapshot)

        build_context.assert_called_once_with(("gemini", "long", True), instantane=snapshot)


class ProvenanceTests(unittest.TestCase):
    def test_editplan_hash_is_stable_and_changes_with_plan_content(self):
        first = {"version": 1, "fps": 24, "video": [{"src": "p01", "duree_f": 24}]}
        reordered = {"video": [{"duree_f": 24, "src": "p01"}], "fps": 24, "version": 1}
        changed = {"version": 1, "fps": 24, "video": [{"src": "p01", "duree_f": 25}]}

        digest = monter.empreinte_editplan(first)
        self.assertEqual(digest, monter.empreinte_editplan(reordered))
        self.assertNotEqual(digest, monter.empreinte_editplan(changed))

    def test_annexe_hash_is_stable_and_sensitive_to_render_settings(self):
        first = {"etalonnage": {"contraste": 1.03}, "recadrage_v": {"p01": 0.4}}
        reordered = {"recadrage_v": {"p01": 0.4}, "etalonnage": {"contraste": 1.03}}
        changed = {"etalonnage": {"contraste": 1.04}, "recadrage_v": {"p01": 0.4}}

        digest = monter.empreinte_annexe(first)
        self.assertEqual(digest, monter.empreinte_annexe(reordered))
        self.assertNotEqual(digest, monter.empreinte_annexe(changed))

    def test_sources_hash_only_references_used_and_deduplicates_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "shared.mp4"
            voice = root / "voice.wav"
            music = root / "music.wav"
            unused = root / "unused.mp4"
            for path, data in ((video, b"video"), (voice, b"voice"), (music, b"music"), (unused, b"unused")):
                path.write_bytes(data)
            ctx = SimpleNamespace(
                plan={
                    "video": [{"src": "p01"}, {"src": "p02"}, {"src": "p01"}],
                    "audio": {"voix": [{"src": "v01"}, {"src": "v01"}], "musique": {"src": "m01"}},
                },
                vid={"p01": video, "p02": video, "inutilise": unused},
                voix={"v01": voice},
                musique=music,
            )
            original = monter.empreinte_fichier
            with patch.object(monter, "empreinte_fichier", wraps=original) as empreinte:
                resultat = monter.empreintes_sources_utilisees(ctx)

            self.assertEqual(3, empreinte.call_count)
            self.assertEqual({"p01", "p02"}, set(resultat["sources_sha256"]["video"]))
            self.assertEqual(resultat["sources_sha256"]["video"]["p01"], resultat["sources_sha256"]["video"]["p02"])
            self.assertEqual(hashlib.sha256(b"voice").hexdigest(), resultat["sources_sha256"]["voix"]["v01"])
            self.assertEqual(hashlib.sha256(b"music").hexdigest(), resultat["sources_sha256"]["musique"]["m01"])
            self.assertEqual([], resultat["sources_absentes"]["voix"])

    def test_source_hash_changes_with_file_contents_and_read_failure_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.wav"
            source.write_bytes(b"first")
            first = monter.empreinte_fichier(source)
            source.write_bytes(b"second")
            self.assertNotEqual(first, monter.empreinte_fichier(source))

            ctx = SimpleNamespace(
                plan={"video": [], "audio": {"voix": [{"src": "v01"}]}},
                vid={}, voix={"v01": source / "missing.wav"}, musique=None,
            )
            with self.assertRaises(monter.ErreurProvenance):
                monter.empreintes_sources_utilisees(ctx)

    def test_missing_voice_and_music_are_reported_as_scoped_absences(self):
        ctx = SimpleNamespace(
            plan={"video": [], "audio": {"voix": [{"src": "v01"}], "musique": {"src": "m01"}}},
            vid={}, voix={}, musique=None,
        )

        resultat = monter.empreintes_sources_utilisees(ctx)

        self.assertEqual({"video": [], "voix": ["v01"], "musique": ["m01"]}, resultat["sources_absentes"])
        self.assertEqual({"video": {}, "voix": {}, "musique": {}}, resultat["sources_sha256"])

    def test_empty_voice_source_id_is_not_silently_omitted(self):
        ctx = SimpleNamespace(
            plan={"video": [], "audio": {"voix": [{"src": ""}]}},
            vid={}, voix={"": None}, musique=None,
        )

        with self.assertRaisesRegex(monter.ErreurProvenance, "identifiant.*voix"):
            monter.empreintes_sources_utilisees(ctx)


if __name__ == "__main__":
    unittest.main()
