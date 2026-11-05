#!/usr/bin/env python3
"""Tests unittest du validateur. Fixtures 100 % fictives, en mémoire."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

import valider

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "valider.py")


def make_brief(n, split="construction", campaign=None, assets=None, **over):
    brief = {
        "id": "AMD2-%03d" % n,
        "campaign_id": campaign if campaign is not None else "campagne-fixture-%03d" % n,
        "split": split,
        "theme": "thème fictif numéro %d" % n,
        "family": "UGC",
        "format": "9:16",
        "duration_s": 30,
        "language": "fr",
        "asset_ids": assets if assets is not None else ["asset-fixture-%05d" % n],
        "description_en": "A fictional description for testing only.",
        "hook_5s": "Fictional hook.",
        "dialogue": "Fictional dialogue line.",
        "on_screen_text": "FICTIONAL TEXT",
        "real_world_direction": "Fictional direction.",
        "observation_criteria": ["critère fictif un", "critère fictif deux"],
        "status": "En préparation",
        "voice_approval": "pending_founder",
        "memory_promotion": "none",
    }
    brief.update(over)
    return brief


def make_corpus(count=3, start=1):
    splits = ("construction", "validation", "test")
    briefs = [make_brief(start + i, split=splits[i % 3]) for i in range(count)]
    return {"statut": valider.ROOT_STATUS, "briefs": briefs}


class BaseCase(unittest.TestCase):
    def assertInvalid(self, doc, code_fragment=None, min_briefs=3):
        errors = valider.validate(doc, min_briefs=min_briefs)
        self.assertTrue(errors, "document aurait dû être invalide")
        if code_fragment is not None:
            joined = "\n".join(errors)
            self.assertIn(code_fragment, joined, joined)
        return errors

    def assertValid(self, doc, min_briefs=3):
        errors = valider.validate(doc, min_briefs=min_briefs)
        self.assertEqual(errors, [], "\n".join(errors))


class TestCorpusValide(BaseCase):
    def test_corpus_fictif_valide(self):
        self.assertValid(make_corpus())

    def test_min_briefs_par_defaut_50(self):
        self.assertTrue(valider.validate(make_corpus(3)))
        doc = make_corpus(50)
        self.assertEqual(valider.validate(doc), [])

    def test_min_briefs_assoupli(self):
        doc = make_corpus(1)
        self.assertEqual(valider.validate(doc, min_briefs=1), [])


class TestTypesStricts(BaseCase):
    def test_duree_bool_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["duration_s"] = True
        self.assertInvalid(doc, "duration_s")

    def test_duree_faux_bool_invalide(self):
        doc = make_corpus()
        doc["briefs"][1]["duration_s"] = False
        self.assertInvalid(doc, "duration_s")

    def test_duree_flottant_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["duration_s"] = 30.0
        self.assertInvalid(doc, "duration_s")

    def test_duree_hors_enumeration(self):
        doc = make_corpus()
        doc["briefs"][0]["duration_s"] = 45
        self.assertInvalid(doc, "invalid_duration_s")

    def test_duree_chaine_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["duration_s"] = "30"
        self.assertInvalid(doc, "duration_s")

    def test_liste_au_lieu_objet_invalide(self):
        doc = make_corpus()
        doc["briefs"][0] = [1, 2, 3]
        self.assertInvalid(doc, "not_object")

    def test_asset_ids_texte_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["asset_ids"] = "asset-fixture-00001"
        self.assertInvalid(doc, "expected_nonempty_array")

    def test_critere_non_chaine_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["observation_criteria"] = ["ok", 42]
        self.assertInvalid(doc, "observation_criteria[1]")

    def test_objet_au_lieu_liste_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["observation_criteria"] = {"a": "b"}
        self.assertInvalid(doc, "expected_array")


class TestValeursObligatoires(BaseCase):
    def test_champ_manquant(self):
        for field in valider.BRIEF_FIELDS:
            with self.subTest(field=field):
                doc = make_corpus()
                del doc["briefs"][0][field]
                self.assertInvalid(doc, "missing")

    def test_racine_statut_manquant(self):
        doc = make_corpus()
        del doc["statut"]
        self.assertInvalid(doc, "statut")

    def test_racine_briefs_manquant(self):
        doc = make_corpus()
        del doc["briefs"]
        self.assertInvalid(doc, "briefs")

    def test_document_non_objet(self):
        self.assertInvalid([], "expected_object")


class TestChaineBlanche(BaseCase):
    def test_champs_texte_blancs(self):
        fields = ("campaign_id", "theme", "description_en", "hook_5s",
                  "dialogue", "on_screen_text", "real_world_direction")
        for field in fields:
            for blank in ("", "   ", "\t\n"):
                with self.subTest(field=field, value=repr(blank)):
                    doc = make_corpus()
                    doc["briefs"][0][field] = blank
                    self.assertInvalid(doc, field)

    def test_id_blanc(self):
        doc = make_corpus()
        doc["briefs"][0]["id"] = "   "
        self.assertInvalid(doc, "invalid_brief_id")

    def test_statut_racine_blanc(self):
        doc = make_corpus()
        doc["statut"] = "  "
        self.assertInvalid(doc, "statut")

    def test_asset_id_blanc(self):
        doc = make_corpus()
        doc["briefs"][0]["asset_ids"] = ["ok-asset", " "]
        self.assertInvalid(doc, "asset_ids[1]")

    def test_identifiants_espaces_refuses(self):
        doc = make_corpus()
        doc["briefs"][0]["campaign_id"] = " campagne-fictive "
        doc["briefs"][1]["asset_ids"] = [" asset-fictif "]
        self.assertInvalid(doc, "expected_canonical_string")

    def test_critere_blanc(self):
        doc = make_corpus()
        doc["briefs"][0]["observation_criteria"] = ["ok", ""]
        self.assertInvalid(doc, "observation_criteria[1]")


class TestListeCriteres(BaseCase):
    def test_un_seul_critere(self):
        doc = make_corpus()
        doc["briefs"][0]["observation_criteria"] = ["unique"]
        self.assertInvalid(doc, "too_few_criteria")

    def test_liste_vide(self):
        doc = make_corpus()
        doc["briefs"][0]["observation_criteria"] = []
        self.assertInvalid(doc, "too_few_criteria")

    def test_deux_criteres_ok(self):
        doc = make_corpus()
        doc["briefs"][0]["observation_criteria"] = ["a", "b", "c"]
        self.assertValid(doc)


class TestListesAssetsNonVides(BaseCase):
    def test_asset_ids_vide(self):
        doc = make_corpus()
        doc["briefs"][0]["asset_ids"] = []
        self.assertInvalid(doc, "expected_nonempty_array")


class TestIdentifiantsDupliques(BaseCase):
    def test_id_duplique(self):
        doc = make_corpus()
        doc["briefs"][1]["id"] = doc["briefs"][0]["id"]
        self.assertInvalid(doc, "duplicate_id")

    def test_id_format_invalide(self):
        for bad in ("AMD2-12", "XXX-00001", "AMD2-0000A", "AMD2-0000", "AMD2-１２３", 123):
            with self.subTest(bad=bad):
                doc = make_corpus()
                doc["briefs"][0]["id"] = bad
                self.assertInvalid(doc, "invalid_brief_id")

    def test_id_format_valide(self):
        doc = make_corpus()
        doc["briefs"][0]["id"] = "AMD2-000"
        self.assertValid(doc)


class TestFuitesPartitions(BaseCase):
    def test_campagne_construction_validation(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="construction", campaign="camp-partagee"),
                make_brief(2, split="validation", campaign="camp-partagee"),
                make_brief(3, split="test"),
            ],
        }
        self.assertInvalid(doc, "split_leak:camp-partagee")

    def test_campagne_validation_test(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="validation", campaign="camp-x"),
                make_brief(2, split="test", campaign="camp-x"),
                make_brief(3, split="construction"),
            ],
        }
        self.assertInvalid(doc, "split_leak:camp-x")

    def test_campagne_construction_test(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="construction", campaign="camp-y"),
                make_brief(2, split="test", campaign="camp-y"),
                make_brief(3, split="validation"),
            ],
        }
        self.assertInvalid(doc, "split_leak:camp-y")

    def test_asset_construction_validation(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="construction", assets=["a-partage"]),
                make_brief(2, split="validation", assets=["b-propre", "a-partage"]),
                make_brief(3, split="test"),
            ],
        }
        self.assertInvalid(doc, "split_leak:a-partage")

    def test_asset_test_construction(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="construction", assets=["a-partage"]),
                make_brief(2, split="test", assets=["a-partage"]),
                make_brief(3, split="validation"),
            ],
        }
        self.assertInvalid(doc, "split_leak:a-partage")

    def test_asset_validation_test(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="validation", assets=["a-partage"]),
                make_brief(2, split="test", assets=["a-partage"]),
                make_brief(3, split="construction"),
            ],
        }
        self.assertInvalid(doc, "split_leak:a-partage")

    def test_meme_partition_ok(self):
        doc = {
            "statut": valider.ROOT_STATUS,
            "briefs": [
                make_brief(1, split="test", campaign="camp-z", assets=["asset-z"]),
                make_brief(2, split="test", campaign="camp-z", assets=["asset-z"]),
                make_brief(3, split="construction"),
            ],
        }
        self.assertValid(doc)


class TestStatusMemoryVoice(BaseCase):
    def test_status_strict(self):
        for bad in ("En préparation ", "en préparation", "Prêt", "", None, 1):
            with self.subTest(bad=bad):
                doc = make_corpus()
                doc["briefs"][0]["status"] = bad
                self.assertInvalid(doc, "invalid_status")

    def test_memory_promotion_stricte(self):
        for bad in ("allowed", "", "None", True, None):
            with self.subTest(bad=bad):
                doc = make_corpus()
                doc["briefs"][0]["memory_promotion"] = bad
                self.assertInvalid(doc, "invalid_memory_promotion")

    def test_voice_approval_stricte(self):
        for bad in ("approved", "", "Pending_founder", True, None):
            with self.subTest(bad=bad):
                doc = make_corpus()
                doc["briefs"][0]["voice_approval"] = bad
                self.assertInvalid(doc, "invalid_voice_approval")


class TestChampsInconnus(BaseCase):
    def test_champ_brief_inconnu(self):
        doc = make_corpus()
        doc["briefs"][0]["champ_supplementaire"] = "x"
        self.assertInvalid(doc, "unknown_field:champ_supplementaire")

    def test_champ_racine_inconnu(self):
        doc = make_corpus()
        doc["extra"] = 1
        self.assertInvalid(doc, "unknown_field:extra")


class TestChampsOptionnelsEtRacine(BaseCase):
    def test_options_du_schema_acceptees(self):
        doc = make_corpus()
        doc["briefs"][0].update({"product_notes": "note fictive", "dialogues": ["texte fictif"],
                                 "function_claims": {"point": "fiction"}})
        self.assertValid(doc)

    def test_option_type_invalide(self):
        doc = make_corpus()
        doc["briefs"][0]["dialogues"] = "pas une liste"
        self.assertInvalid(doc, "expected_nonempty_string_array")

    def test_statut_racine_publie_refuse(self):
        doc = make_corpus()
        doc["statut"] = "publié"
        self.assertInvalid(doc, "invalid_root_status")


class TestPartitionsEnum(BaseCase):
    def test_split_inconnu(self):
        doc = make_corpus()
        doc["briefs"][0]["split"] = "production"
        self.assertInvalid(doc, "invalid_split")


class TestPasDeFuiteDeContenu(BaseCase):
    def test_erreurs_sans_contenu(self):
        doc = make_corpus()
        doc["briefs"][0]["description_en"] = "SECRET-MARKER-DESCRIPTION"
        doc["briefs"][0]["status"] = "SECRET-MARKER-STATUS"
        errors = valider.validate(doc, min_briefs=3)
        joined = "\n".join(errors)
        self.assertNotIn("SECRET-MARKER-DESCRIPTION", joined)
        self.assertNotIn("SECRET-MARKER-STATUS", joined)


class TestCLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args],
                              capture_output=True, text=True)

    def write_tmp(self, content):
        fd, path = tempfile.mkstemp(suffix=".json")
        self.addCleanup(os.remove, path)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            if isinstance(content, str):
                fh.write(content)
            else:
                json.dump(content, fh, ensure_ascii=False)
        return path

    def test_cli_valide(self):
        path = self.write_tmp(make_corpus(3))
        r = self.run_cli(path, "--min-briefs", "3")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_cli_cinquante_fictifs_par_defaut(self):
        path = self.write_tmp(make_corpus(50))
        r = self.run_cli(path)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_cli_invalide(self):
        doc = make_corpus(3)
        doc["briefs"][0]["status"] = "Publié"
        path = self.write_tmp(doc)
        r = self.run_cli(path, "--min-briefs", "3")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid_status", r.stderr)

    def test_cli_defaut_50(self):
        path = self.write_tmp(make_corpus(3))
        r = self.run_cli(path)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("too_few_briefs", r.stderr)

    def test_cli_json_invalide(self):
        path = self.write_tmp("{ceci n'est pas du json")
        r = self.run_cli(path)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("JSON invalide", r.stderr)

    def test_cli_fichier_absent(self):
        r = self.run_cli("fichier-qui-nexiste-pas-fixture.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("introuvable", r.stderr)

    def test_cli_n_affiche_pas_le_contenu(self):
        doc = make_corpus(3)
        doc["briefs"][0]["hook_5s"] = "SECRET-MARKER-HOOK"
        doc["briefs"][1]["voice_approval"] = "SECRET-MARKER-VOICE"
        path = self.write_tmp(doc)
        r = self.run_cli(path, "--min-briefs", "3")
        self.assertNotEqual(r.returncode, 0)
        out = r.stdout + r.stderr
        self.assertNotIn("SECRET-MARKER-HOOK", out)
        self.assertNotIn("SECRET-MARKER-VOICE", out)


if __name__ == "__main__":
    unittest.main()
