"""Régressions ciblées : les sorties existantes et les essais restent intacts."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h3  # noqa: E402
import monter  # noqa: E402
import tourner  # noqa: E402


class MixerPreservationTests(unittest.TestCase):
    def contexte_sans_pistes(self):
        return SimpleNamespace(
            plan={"audio": {}, "video": []}, total=24, annexe={"sfx": []},
            voix={}, musique=None, vid={}, debuts=[],
        )

    def test_existing_mix_is_refused_before_audio_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            mix = Path(tmp) / "mix.wav"
            mix.write_bytes(b"existing mix")
            with (
                patch.object(monter.sfx_v3, "ecrire") as ecrire,
                patch.object(monter.subprocess, "run") as run,
            ):
                with self.assertRaises(FileExistsError):
                    monter.mixer(self.contexte_sans_pistes(), mix)

            ecrire.assert_not_called()
            run.assert_not_called()
            self.assertEqual(b"existing mix", mix.read_bytes())

    def test_mix_keeps_raw_audio_and_uses_unique_names_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mix = root / "mix.wav"
            brut = root / "mix.brut.wav"
            brut.write_bytes(b"previous raw mix")
            commandes = []

            def ecrire(_piste, chemin):
                Path(chemin).write_bytes(b"new raw mix")

            def run(commande, **kwargs):
                commandes.append((commande, kwargs))
                if "null" in commande:
                    mesure = {"input_i": -20, "input_tp": -1, "input_lra": 1,
                              "input_thresh": -30, "target_offset": 0}
                    return SimpleNamespace(stderr=("loudnorm\n" + json.dumps(mesure)).encode())
                self.assertIn("-n", commande)
                cible = Path(commande[-1])
                self.assertFalse(cible.exists())
                cible.write_bytes(b"new final mix")
                return SimpleNamespace(returncode=0)

            with (
                patch.object(monter.sfx_v3, "ecrire", side_effect=ecrire),
                patch.object(monter.subprocess, "run", side_effect=run),
            ):
                monter.mixer(self.contexte_sans_pistes(), mix)

            self.assertEqual(b"previous raw mix", brut.read_bytes())
            self.assertEqual(b"new raw mix", (root / "mix.brut-2.wav").read_bytes())
            self.assertEqual(b"new final mix", mix.read_bytes())
            self.assertEqual(2, len(commandes))
            self.assertIn("-n", commandes[1][0])
            self.assertNotIn("-y", commandes[1][0])


class TranchePreservationTests(unittest.TestCase):
    def test_render_refuses_existing_slice_and_uses_no_overwrite(self):
        class FakeEncoder:
            def __init__(self):
                self.stdin = SimpleNamespace(close=lambda: None)

            def wait(self):
                return 0

        ctx = SimpleNamespace(
            W=4, H=4, plan={"video": [], "textes": []}, annexe={},
            vert=False, debuts=[], vid={},
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            part = root / "existing-t000000.mp4"
            new_part = root / "t000000.mp4"
            with (
                patch.object(monter, "contexte", return_value=ctx),
                patch.object(monter.subprocess, "Popen") as popen,
            ):
                part.write_bytes(b"previous slice")
                with self.assertRaises(FileExistsError):
                    monter.rendre_tranche(("equipe", "long", True, 0, 0, part))
                popen.assert_not_called()
                self.assertEqual(b"previous slice", part.read_bytes())

                popen.return_value = FakeEncoder()
                self.assertEqual(str(new_part), monter.rendre_tranche(("equipe", "long", True, 0, 0, new_part)))

            commande = popen.call_args.args[0]
            self.assertIn("-n", commande)
            self.assertNotIn("-y", commande)


class H3PublicationPreservationTests(unittest.TestCase):
    def test_completed_render_is_published_under_a_free_name(self):
        pid = "prompt-1"
        historique = {
            "status": {"status_str": "success", "completed": True, "messages": []},
            "outputs": {"node": {"video": [{"filename": "render.mp4"}]}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "take-r1.mp4"
            output.write_bytes(b"previous render")
            with (
                patch.object(h3.time, "sleep"),
                patch.object(h3, "http", side_effect=[json.dumps({pid: historique}).encode(), b"new render"]),
            ):
                result = h3.attendre(
                    {"nom": "take-r1", "sortie": tmp}, "http://comfy.invalid", pid, 0,
                )

            new_output = Path(result["fichier"])
            self.assertEqual("take-r1-2.mp4", new_output.name)
            self.assertEqual(b"previous render", output.read_bytes())
            self.assertEqual(b"new render", new_output.read_bytes())


class DerniereImagePreservationTests(unittest.TestCase):
    def test_existing_keyframe_is_preserved_and_ffmpeg_uses_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.mp4"
            sortie = Path(tmp) / "fin-p01.png"
            source.write_bytes(b"source")
            sortie.write_bytes(b"previous keyframe")
            commandes = []

            def ffmpeg(commande, check):
                commandes.append((commande, check))
                Path(commande[-1]).write_bytes(b"new keyframe")
                return SimpleNamespace(returncode=0)

            with patch.object(tourner.subprocess, "run", side_effect=ffmpeg):
                result = tourner.derniere_image(source, sortie)

            self.assertEqual("fin-p01-2.png", Path(result).name)
            self.assertEqual(b"previous keyframe", sortie.read_bytes())
            self.assertEqual(b"new keyframe", Path(result).read_bytes())
            self.assertIn("-n", commandes[0][0])
            self.assertNotIn("-y", commandes[0][0])
            self.assertTrue(commandes[0][1])


if __name__ == "__main__":
    unittest.main()
