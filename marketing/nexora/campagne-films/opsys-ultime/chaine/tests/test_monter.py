"""Contrôles sans rendu des gardes et correspondances de montage."""
import sys
import tempfile
import unittest
from pathlib import Path
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

    def test_construire_stops_before_editplan_validation_or_rendering(self):
        ctx = type("Context", (), {"vid": {"p26": None}})()
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


if __name__ == "__main__":
    unittest.main()
