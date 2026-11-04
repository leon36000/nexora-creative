"""Tests hors ligne : contrats réels du montage, moteurs et API doublés."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ICI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ICI))
import commun as C
import production as P
import v7

ESSAI = ICI / 'equipes/essai/dossier.json'


def essai():
    return json.loads(ESSAI.read_text())


class BaseHorsLigne(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ICI, prefix='test-')
        self.root = Path(self.tmp.name)
        self.net = patch('urllib.request.urlopen', side_effect=AssertionError('Réseau interdit dans les tests'))
        self.net.start()
        self.d = essai()

    def tearDown(self):
        self.net.stop()
        self.tmp.cleanup()

    def valider(self, d=None):
        return C.valider(d or self.d, ESSAI.parent)


class ValidationTests(BaseHorsLigne):
    def test_essai_et_vrai_validateur(self):
        with patch.object(C.montage_module(), 'charger', wraps=C.montage_module().charger) as f:
            errors, warnings = self.valider()
        self.assertFalse(errors, errors)
        self.assertEqual(f.call_count, 2)  # français et anglais
        self.assertTrue(any('10 s' in w for w in warnings))

    def test_schema_et_doublons(self):
        for value in (None, [], {}, {'equipe': '../x'}, {'plans': 'x'}):
            self.assertTrue(C.valider(value, ESSAI.parent)[0])
        self.d['cles'][1]['id'] = 'k01'
        self.assertTrue(any('doublon' in e for e in self.valider()[0]))

    def test_types_finis(self):
        for group, key, val in [('plans', 'images', True), ('cles', 'graine', '42'), ('temps_forts', 't', float('nan'))]:
            d = essai()
            d[group][0][key] = val
            self.assertTrue(self.valider(d)[0])

    def test_avertissement_texte_carton_long(self):
        marque = C.lire_json(C.V7/'marque-v7.json')
        marque['textes']['fr']['slogan'] = 'Un slogan de plus de quatre mots'
        path = self.root/'marque.json'
        C.ecrire_json(path, marque)
        self.d['montage']['marque'] = str(path)
        self.d['montage']['segments'][1]['duree'] = 3
        self.d['montage']['segments'].append({'type': 'carton', 'debut': 8, 'duree': 2})
        erreurs, warnings = self.valider()
        self.assertFalse(erreurs, erreurs)
        self.assertTrue(any('carton' in x and 'slogan' in x for x in warnings))

    def test_grille_et_unites(self):
        for n in (124, 141, 158, 175, 192, 209, 226, 243):
            self.assertEqual(C.unites(n), 1 if n == 124 else 2)
        for n in (0, 123, 125, 140, 244, 260, 124., True, None):
            with self.assertRaises(ValueError):
                C.unites(n)

    def test_budgets_cles_voix_musiques(self):
        for group, count in [('cles', 25), ('voix', 9), ('musiques', 4)]:
            d = essai()
            d[group] = [{**d[group][0], 'id': f'x{i}'} for i in range(count)]
            self.assertTrue(any(f'Budget {group}' in e for e in self.valider(d)[0]))
        d = essai()
        d['revision'] = True
        d['musiques'] = [{**d['musiques'][0], 'id': f'm{i}'} for i in range(4)]
        d['montage']['musique']['fichier'] = 'musique:m1'
        self.assertFalse(self.valider(d)[0])

    def test_budget_formats(self):
        for fmt, count in [('16:9', 11), ('9:16', 3)]:
            d = essai()
            d['cles'][0]['format'] = fmt
            d['plans'] = [{**d['plans'][0], 'id': f'p{i}', 'format': fmt, 'images': 141} for i in range(count)]
            self.assertTrue(any(f'Budget H3 {fmt}' in e for e in self.valider(d)[0]))

    def test_mots_interdits_positifs(self):
        for mot in C.INTERDITS:
            for group in ('cles', 'plans'):
                d = essai()
                d[group][0]['prompt'] += ' '+mot.upper()
                self.assertTrue(any('mot interdit' in e for e in self.valider(d)[0]), (mot, group))
        d = essai()
        d['cles'][0]['prompt'] += ' teal-and-orange'
        self.assertTrue(self.valider(d)[0])
        # Un sous-mot ne doit pas déclencher « epic ».
        self.d['cles'][0]['prompt'] += ' depiction'
        self.assertFalse(self.valider()[0])

    def test_no_text(self):
        self.d['plans'][0]['prompt'] = 'Live-action footage on 35mm film.'
        self.assertTrue(any('No text' in e for e in self.valider()[0]))

    def test_references(self):
        for edit, attendu in [
            (lambda d: d['plans'][0].update(cle='inconnue'), 'clé inconnue'),
            (lambda d: d['montage']['segments'][0].update(fichier='plan:inconnu'), 'Référence inconnue'),
            (lambda d: d['montage']['segments'][0].update(fichier_vertical='plan_v:p01'), 'Référence inconnue'),
            (lambda d: d['montage']['musique'].update(fichier='musique:inconnue'), 'Référence inconnue'),
            (lambda d: d['montage']['voix'][0].update(id='inconnue'), 'Voix inconnue')]:
            d = essai()
            edit(d)
            self.assertTrue(any(attendu in e for e in self.valider(d)[0]))

    def test_captures_reelles_absentes(self):
        self.d['montage']['segments'][0] = {'type': 'saisie', 'debut': 0, 'duree': 5,
                                           'dossier': str(self.root/'captures-absentes'), 'zone': [0, 0, 100, 100]}
        self.assertTrue(any('Source absente' in e for e in self.valider()[0]))

    def test_validation_montage_recouvrements_et_limites(self):
        for edit in [lambda d: d['montage']['segments'][1].update(debut=4),
                     lambda d: d['montage']['segments'][0].update(entree=3),
                     lambda d: d['montage']['segments'][0].update(vitesse=-1),
                     lambda d: d['montage']['musique'].update(trous=[[4, 3]])]:
            d = essai()
            edit(d)
            self.assertTrue(any('monter_v6.charger' in e for e in self.valider(d)[0]))

    def test_substitution_recursive_native_et_voix(self):
        self.d['cles'].append({**self.d['cles'][0], 'id': 'kv', 'format': '9:16'})
        self.d['plans'].append({**self.d['plans'][0], 'id': 'pv', 'cle': 'kv', 'format': '9:16'})
        self.d['montage']['segments'][0]['fichier_vertical'] = 'plan_v:pv'
        self.d['montage']['segments'][1]['sur_video'] = {'fichier': 'plan:p01'}
        self.d['montage']['musique'].pop('calage')
        avant = copy.deepcopy(self.d)
        m = C.substituer(self.d, ESSAI.parent, self.root)
        self.assertEqual(m['segments'][0]['fichier_vertical'], str(self.root/'plans/pv.mp4'))
        self.assertEqual(m['segments'][1]['sur_video']['fichier'], str(self.root/'plans/p01.mp4'))
        self.assertEqual(m['voix'][0]['fichier'], str(self.root/'voix/v01.wav'))
        self.assertEqual(avant, self.d)
        self.d['voix'][0]['moteur'] = 'h3-natif'
        self.assertFalse(C.substituer(self.d, ESSAI.parent, self.root)['voix'])

    def test_calage_auto(self):
        g = {'energie_db_05s': [-40]*10+[-5]*20, 'duree_s': 30, 'bpm': 120, 'phase_s': .1, 'temps_s': .5}
        self.assertEqual(C.calage_auto(g, 2, 10), 3)
        self.assertEqual(C.calage_auto(g, 6, 10), 0)
        self.assertEqual(C.calage_auto(g, 2, 29), 0)
        C.ecrire_json(self.root/'musique/m1.grille.json', g)
        m = C.substituer(self.d, ESSAI.parent, self.root)
        self.assertEqual(m['musique']['entree'], 4)
        self.assertAlmostEqual(m['phase'], .1)
        self.assertNotIn('calage', m['musique'])
        with self.assertRaisesRegex(ValueError, 'Grille absente'):
            C.substituer(self.d, ESSAI.parent, self.root/'absent')

    def test_mesures_synchro_coupes_et_trous(self):
        m = {'segments': [{'debut': x} for x in (0, 1, 1.5, 2.1)],
             'musique': {'entree': 2, 'trous': [[1.4, 1.6]], 'coupes': [[2, 4]]}}
        g = {'phase_s': 0, 'temps_s': .5, 'bpm': 120}
        r = P.mesures_synchro(m, g, [3, 3.5, 4.1], 3)
        self.assertEqual(r['coupes_audibles'], 2)
        self.assertEqual(r['part_coupes_a_2_images_temps'], .5)
        self.assertAlmostEqual(r['ecart_moyen_impacts_coupes_s'], 0)

    def test_verrou_deux_processus_meme_equipe(self):
        with P.verrou(self.root/'lock'):
            with self.assertRaises(RuntimeError):
                with P.verrou(self.root/'lock'):
                    pass
        with P.verrou(self.root/'lock'):
            pass

    def test_wer(self):
        self.assertEqual(P.wer('On y va !', 'on y va'), 0)
        self.assertAlmostEqual(P.wer('On y va', 'On va'), 1/3)

    def test_import_musique_sans_collision_commun(self):
        legacy = C.musique_legacy()
        self.assertIsNot(legacy.C, C)
        self.assertTrue(callable(legacy.C.lire))
        self.assertIs(sys.modules['commun'], C)

    def test_music3_graphe(self):
        g = P.graphe_music3({'prompt': 'test', 'graine': 101}, 65, 'v7-essai/musique/m1')
        self.assertEqual(g['enc']['inputs']['max_duration'], 65)
        self.assertEqual(g['ks']['inputs']['steps'], 30)
        self.assertTrue(g['save']['inputs']['filename_prefix'].startswith('v7-essai/'))

    def test_secrets_et_cout(self):
        atelier = P.Atelier(self.d, ESSAI.parent, self.root, blanc=True)
        with self.assertRaisesRegex(RuntimeError, 'interdit'):
            atelier.post('https://exemple', {})
        atelier.cout({'id': 'gen-1', 'usage': {'cost': .02}}, 'modele', 'test')
        atelier.cout({'id': 'gen-1', 'usage': {'cost': .02}}, 'modele', 'test')
        self.assertEqual(atelier.bilan()['cout_openrouter_usd_connu'], .02)


    def test_argon_flex_force_et_secret_hors_journal(self):
        atelier = P.Atelier(self.d, ESSAI.parent, self.root)
        atelier._key = 'secret-test-ne-pas-journaliser'
        class Response:
            headers = {}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self):
                return json.dumps({'id': 'gen-2', 'usage': {'cost': .05}, 'choices': []}).encode()
        with patch('urllib.request.urlopen', return_value=Response()) as call:
            atelier.post('https://openrouter.ai/api/v1/chat/completions', {'model': 'google/gemini-4-argon'})
        corps = json.loads(call.call_args.args[0].data)
        self.assertEqual(corps['provider'], {'order': ['google-ai-studio/flex'], 'allow_fallbacks': False})
        self.assertNotIn(atelier._key, atelier.couts.read_text())
        self.assertEqual(C.lignes(atelier.couts)[0]['cost'], .05)

    def test_juge_triptyque_trois_images_et_api_note(self):
        from PIL import Image
        import base64, io
        with patch.object(P, 'sonder', return_value={'format': {'duration': '8'}}), \
             patch.object(P, 'image_frame', side_effect=lambda *a: Image.new('RGB', (320, 180))) as f:
            b64 = P.image_juge(self.root/'p01.mp4')
        self.assertEqual([round(c.args[1], 2) for c in f.call_args_list], [1.2, 4., 6.8])
        im = Image.open(io.BytesIO(base64.b64decode(b64.split(',')[1])))
        self.assertEqual(im.width, 1023)
        atelier = P.Atelier(self.d, ESSAI.parent, self.root)
        with patch.object(P, 'image_juge', return_value=b64), \
             patch.object(atelier, 'demander', return_value={'reel': 7, 'defauts': []}) as ask:
            self.assertEqual(atelier.noter(self.root/'p01.mp4')['reel'], 7)
        self.assertEqual(ask.call_args.args[0][0]['type'], 'image_url')

    def test_voix_deux_prises_choix_et_reprise(self):
        atelier = P.Atelier(self.d, ESSAI.parent, self.root, blanc=True)
        def fake_media(f, **kw):
            Path(f).write_bytes(b'audio')
        def fake_ff(*args):
            Path(args[-1]).write_bytes(b'audio')
        with patch.object(atelier, 'factice', side_effect=fake_media), patch.object(P, 'ff', side_effect=fake_ff):
            atelier.voix()
            atelier.voix()
        rows = C.lignes(self.root/'voix/journal.jsonl')
        self.assertEqual(len(rows), 2)
        self.assertEqual({r['prise'] for r in rows}, {1, 2})
        self.assertTrue((self.root/'voix/v01.wav').exists())
        self.assertEqual(C.lire_json(self.root/'voix/v01.json')['choix']['wer'], 0)

    def test_h3_natif_aucun_speech(self):
        self.d['voix'][0]['moteur'] = 'h3-natif'
        atelier = P.Atelier(self.d, ESSAI.parent, self.root)
        with patch.object(C.banc(), 'generer', side_effect=AssertionError('aucun speech')):
            atelier.voix()
        self.assertFalse((self.root/'voix/v01.wav').exists())

    def test_musique_reutilise_grille_et_pas_de_double_generation(self):
        atelier = P.Atelier(self.d, ESSAI.parent, self.root)
        legacy = C.musique_legacy()
        def fake_ff(*args):
            Path(args[-1]).write_bytes(b'audio wav')
        g = {'bpm': 123, 'phase_s': .12, 'temps_s': 60/123, 'duree_s': 60, 'energie_db_05s': [-20]*120}
        with patch.object(legacy, 'lyria', return_value=(b'audio mp3', .04)) as composer, \
             patch.object(legacy, 'grille', return_value=g) as mesurer, patch.object(P, 'ff', side_effect=fake_ff):
            atelier.musique()
            atelier.musique()
        self.assertEqual(composer.call_count, 1)
        self.assertEqual(mesurer.call_count, 1)
        self.assertEqual(C.lire_json(self.root/'musique/m1.grille.json')['bpm'], 123)
        self.assertEqual(atelier.bilan()['cout_openrouter_usd_connu'], .04)

    def test_musique_mesure_interrompue_reutilise_audio_recu(self):
        atelier = P.Atelier(self.d, ESSAI.parent, self.root)
        legacy = C.musique_legacy()
        def fake_ff(*args):
            Path(args[-1]).write_bytes(b'audio wav')
        with patch.object(legacy, 'lyria', return_value=(b'audio mp3', .04)) as composer, \
             patch.object(legacy, 'grille', side_effect=[RuntimeError('mesure interrompue'), {'bpm': 120}]), \
             patch.object(P, 'ff', side_effect=fake_ff):
            with self.assertRaisesRegex(RuntimeError, 'interrompue'):
                atelier.musique()
            atelier.musique()
        self.assertEqual(composer.call_count, 1)

    def test_archivage_a_blanc_pas_de_ssh(self):
        f = self.root/'films/a.mp4'
        f.parent.mkdir()
        f.write_bytes(b'video')
        atelier = P.Atelier(self.d, ESSAI.parent, self.root, blanc=True)
        with patch.object(P, 'commande', side_effect=AssertionError('aucun SSH')):
            plan = atelier.archiver()
        self.assertEqual(plan[0]['destination'], 'creative-v7/essai/films/a.mp4')
        self.assertEqual(len(plan[0]['sha256']), 64)


class FauxComfy:
    def __init__(self, root, equipe='essai'):
        self.root, self.equipe = root, equipe
        self.url = 'http://doublure.invalid'
        self.en_cours = {}
        self.historique = {}
        self.graphes = []
        self.maximum = 0
        self.au_premier_resultat = None
        self.coupure = False
        self.couper_une_fois = False
        self.etrangers = [[0, 'etranger', {'save': {'inputs': {'filename_prefix': 'v7-autre/plans/p01'}}}]]*30

    def queue(self):
        return self.etrangers+[[0, pid, g] for pid, g in self.en_cours.items()]

    def compte(self, prefix):
        return sum(P.Comfy.appartient(q, prefix) for q in self.queue())

    def soumettre(self, graph):
        pid = str(len(self.graphes))
        self.graphes.append(graph)
        self.en_cours[pid] = graph
        self.maximum = max(self.maximum, self.compte('v7-'+self.equipe+'/'))
        if self.couper_une_fois and not self.coupure:
            self.coupure = True
            raise RuntimeError('coupure après POST')
        return pid

    def retrouver(self, prefix):
        for pid, g in {**self.historique, **self.en_cours}.items():
            if g['save']['inputs']['filename_prefix'] == prefix:
                return pid
        return None

    def resultat(self, pid, destination):
        if self.au_premier_resultat is None:
            self.au_premier_resultat = len(self.graphes)
        self.historique[pid] = self.en_cours.pop(pid, self.historique.get(pid))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b'doublure video')
        return {'fichier': str(destination), 'secondesMoteur': 2.5}


class FileTests(BaseHorsLigne):
    def setup_plans(self, n):
        key = self.root/'cles/k01.png'
        key.parent.mkdir()
        key.write_bytes(b'doublure image')
        self.d['plans'] = [{**self.d['plans'][0], 'id': f'p{i:02}'} for i in range(n)]
        self.atelier = P.Atelier(self.d, ESSAI.parent, self.root, poll=0)
        self.fake = FauxComfy(self.root)

    def lancer(self, noter=lambda f: {'reel': 8, 'defauts': []}):
        with patch.object(C.moteur(), 'envoyer_image', return_value='reference.png'), \
             patch.object(self.atelier, 'noter', side_effect=noter):
            return self.atelier._rendus('plans', self.d['plans'], self.fake)

    def test_file_six_et_asynchrone(self):
        self.setup_plans(9)
        choix = self.lancer()
        self.assertEqual(len(choix), 9)
        self.assertEqual(self.fake.maximum, 6)
        self.assertEqual(self.fake.au_premier_resultat, 6)
        self.assertEqual(len(self.fake.etrangers), 30)
        for g in self.fake.graphes:
            self.assertEqual(g['gen']['class_type'], 'MiniMaxH3ReferenceToVideo')
            self.assertEqual(g['sched']['inputs']['steps'], 8)
            self.assertEqual(g['shift']['inputs']['shift_video'], 12)
            self.assertEqual(g['shift']['inputs']['shift_audio'], 3)
            self.assertEqual(g['sampler']['inputs']['sampler_name'], 'euler')
            self.assertEqual(g['u']['inputs']['unet_name'], C.recette().PRISM)
            self.assertIn('<Picture 1>', g['gen']['inputs']['prompt'])
        self.lancer()
        self.assertEqual(len(self.fake.graphes), 9)  # reprise : aucun nouveau rendu
        bilan = self.atelier.bilan()
        self.assertEqual(bilan['unites_h3']['16:9'], 9)
        self.assertEqual(bilan['secondes_gpu_connues'], 22.5)

    def test_coupure_reponse_post_et_reprise(self):
        self.setup_plans(2)
        self.fake.couper_une_fois = True
        with self.assertRaisesRegex(RuntimeError, 'coupure'):
            self.lancer()
        state = C.lire_json(self.root/'plans/etat.json')
        self.assertEqual(next(iter(state['jobs'].values()))['etat'], 'intention')
        self.lancer()
        self.assertEqual(len(self.fake.graphes), 2)

    def test_intention_introuvable_ne_resoumet_pas(self):
        self.setup_plans(1)
        self.fake.couper_une_fois = True
        with self.assertRaises(RuntimeError):
            self.lancer()
        self.fake.en_cours.clear()
        with self.assertRaisesRegex(RuntimeError, 'ambiguë'):
            self.lancer()
        self.assertEqual(len(self.fake.graphes), 1)

    def test_relance_unique_plus_1000_meilleure(self):
        self.setup_plans(2)
        def note(f):
            return {'reel': 7 if '-g1201' in str(f) else 5, 'defauts': ['test']}
        choix = self.lancer(note)
        self.assertEqual(len(self.fake.graphes), 4)
        self.assertEqual(choix['p00']['graine'], 1201)
        self.assertEqual(choix['p00']['note'], 7)
        self.assertEqual(len(C.lignes(self.root/'plans/journal.jsonl')), 4)
        # Pas de troisième prise même si la deuxième reste sous le seuil.
        self.assertEqual(choix['p01']['note'], 7)

    def test_relance_budget_reserve_aux_plans_initiaux(self):
        self.setup_plans(20)
        choix = self.lancer(lambda f: {'reel': 5, 'defauts': []})
        self.assertEqual(len(self.fake.graphes), 20)
        self.assertTrue(all(x['relance_refusee_budget'] for x in choix.values()))

    def test_une_unite_libre_une_seule_relance(self):
        self.setup_plans(19)
        choix = self.lancer(lambda f: {'reel': 5, 'defauts': []})
        self.assertEqual(len(self.fake.graphes), 20)
        self.assertEqual(sum(not x['relance_refusee_budget'] for x in choix.values()), 1)

    def test_relance_verticale_limite_quatre(self):
        self.setup_plans(4)
        for p in self.d['plans']:
            p['format'] = '9:16'
        self.lancer(lambda f: {'reel': 2, 'defauts': []})
        self.assertEqual(len(self.fake.graphes), 4)
        self.assertEqual(self.fake.graphes[0]['gen']['inputs']['width'], 768)

    def test_revision_enveloppe_six_et_plans_inchanges(self):
        self.setup_plans(7)
        self.lancer()
        self.d['revision'] = True
        for p in self.d['plans'][:6]:
            p['graine'] += 10
        self.lancer()
        self.assertEqual(len(self.fake.graphes), 13)
        self.assertEqual(self.atelier.bilan()['unites_revision'], 6)
        self.d['plans'][6]['graine'] += 10
        with self.assertRaisesRegex(ValueError, 'Budget'):
            self.lancer()
        self.assertEqual(len(self.fake.graphes), 13)

    def test_deux_unites_long_plan_vertical_relance(self):
        self.setup_plans(1)
        self.d['plans'][0].update(format='9:16', images=141)
        self.lancer(lambda f: {'reel': 5, 'defauts': []})
        self.assertEqual(len(self.fake.graphes), 2)
        self.assertEqual(self.atelier.bilan()['unites_h3']['9:16'], 4)

    def test_images_negatif_relance_et_reprise(self):
        fake = FauxComfy(self.root)
        specs = [self.d['cles'][0]]
        atelier = P.Atelier(self.d, ESSAI.parent, self.root, poll=0)
        with patch.object(atelier, 'noter', return_value={'reel': 5, 'defauts': ['test']}):
            atelier._rendus('cles', specs, fake)
            atelier._rendus('cles', specs, fake)
        self.assertEqual(len(fake.graphes), 2)
        self.assertEqual(fake.graphes[0]['enc']['inputs']['negative_prompt'], C.recette().NEG)
        self.assertEqual(fake.graphes[1]['k']['inputs']['seed'], 1101)


if __name__ == '__main__':
    unittest.main(verbosity=2)
