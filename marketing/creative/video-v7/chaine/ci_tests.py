#!/usr/bin/env python3
"""Tests CPU hors ligne de la chaîne V7 et du monteur, avec fixtures synthétiques."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import unittest
from unittest.mock import patch

POLICE_DEJAVU_SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
IMAGE_BOOST = '0032-boost.jpg'

V7 = Path(__file__).resolve().parent.parent
V6 = V7.parent / 'video-v6'
# Validation AVANT toute création : jamais de fallback vers le HOME utilisateur.
base = Path(os.path.abspath(os.environ['V7_CI_ROOT']))
chemins = [Path(os.path.abspath(os.environ[name])) for name in ('HOME', 'V7_TEST_TMPDIR', 'V6_CACHE', 'TMPDIR')]
if any(path == base or base not in path.parents for path in chemins):
    raise ValueError('HOME, tests, cache et temporaire doivent être sous V7_CI_ROOT')
base = base.resolve()
chemins = [path.resolve() for path in chemins]
if any(path == base or base not in path.parents for path in chemins):
    raise ValueError('Chemin résolu hors de V7_CI_ROOT')
if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(chemins) for b in chemins[i+1:]):
    raise ValueError('HOME, tests, cache et temporaire doivent être distincts')
_, ROOT, CACHE, _ = chemins

from PIL import Image, ImageDraw, ImageFont
FIXTURE = ROOT / 'fixture-v6'
FIXTURE.mkdir(parents=True, exist_ok=False)
CAPTURES = FIXTURE / 's01'
CAPTURES.mkdir()
CACHE.mkdir(parents=True, exist_ok=True)
fonts = Path.home() / 'Desktop/NexoraSite/web/src/fonts'
fonts.mkdir(parents=True, exist_ok=True)
(fonts / 'geist-latin-wght-normal.woff2').symlink_to(POLICE_DEJAVU_SANS)
(fonts / 'jetbrains-mono-latin-wght-normal.woff2').symlink_to('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')

# Copie du contrat historique ; les chemins personnels sont remplacés par
# de petits médias factices. Rien n'est lu dans le HOME du développeur.
for nom in ('monter_v6.py', 'effets_v6.py', 'sfx_v6.py'):
    shutil.copyfile(V7 / nom, FIXTURE / nom)
marque = json.loads((V6 / 'marque-v6.json').read_text())
marque['polices']['titre'] = POLICE_DEJAVU_SANS
marque['polices']['mono'] = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
(FIXTURE / 'marque-v6.json').write_text(json.dumps(marque, ensure_ascii=False))

journal = []
for i in range(17):
    image = Image.new('RGB', (1600, 900), (24 + i * 7, 48, 92))
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 296, 532, 765), fill=(32, 36, 48), outline='white', width=4)
    font = ImageFont.truetype(POLICE_DEJAVU_SANS, 12)
    draw.text((105, 307), 'DRAGON ATTAQUE CHATEAU EN FLAMMES', fill=(100, 100, 100), font=font)
    draw.rectangle((110, 310, 220, 316), fill='white')
    draw.line((110, 326, 510, 326), fill=(255, 40, 20), width=5)
    name = f'{i:04d}-saisie.png'
    image.save(CAPTURES / name)
    journal.append({'t': i, 'etiquette': 'saisie', 'image': name})
Image.new('RGB', (1600, 900), (80, 160, 220)).save(CAPTURES / IMAGE_BOOST)
journal.append({'t': 18, 'etiquette': 'boost', 'image': IMAGE_BOOST})
(CAPTURES / 'journal.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in journal))
for folder, key in zip(('s01', 's02', 's03', 's04', 's08', 's10'), ('dragon', 'bataille spatiale', 'orage', 'monstre marin', 'petit chat', 'silence')):
    dest = FIXTURE / folder
    dest.mkdir(exist_ok=True)
    text = ('paysages et mouvement sans dialogue dans le décor. ' * 12) + key
    (dest / 'boost.json').write_text(json.dumps({'boost': text, 'mots': 'dragon château flammes'}))

ffmpeg = os.environ['V6_FFMPEG']
rush = FIXTURE / 'rush.mp4'
music = FIXTURE / 'musique.wav'
subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
                '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24:duration=12',
                '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=12',
                '-c:v', 'libx264', '-threads', '2', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-shortest', str(rush)], check=True)
subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-n',
                '-f', 'lavfi', '-i', 'sine=frequency=220:sample_rate=48000:duration=40',
                '-ac', '2', '-c:a', 'pcm_s16le', str(music)], check=True)

montage = json.loads((V6 / 'montage-essai.json').read_text())
def remplace(obj):
    if isinstance(obj, dict):
        return {key: remplace(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [remplace(value) for value in obj]
    if isinstance(obj, str):
        prefix = '~/nexora-creative-data/promo/v6-creative/'
        if obj == prefix + 'musique/lyria-3.wav': return str(music)
        if obj == prefix + 'rushes/765.mp4': return str(rush)
        if obj == prefix + 'captures/boost/s01': return str(CAPTURES)
        if obj == prefix + 'captures/boost/s01/0032-boost.jpg': return str(CAPTURES / IMAGE_BOOST)
    return obj
(FIXTURE / 'montage-essai.json').write_text(json.dumps(remplace(montage), ensure_ascii=False))

# Interdit les connexions réseau depuis les suites Python, même si un test régresse.
blocage_reseau = patch.object(socket.socket, "connect", side_effect=AssertionError("Réseau interdit pendant les tests"))
blocage_reseau.start()
# Les 48 tests utilisent le contrat V7 et les doublures réseau existantes.
chaine = unittest.TestLoader().discover(str(V7 / 'chaine/tests'), pattern='test_chaine.py')
resultat_chaine = unittest.TextTestRunner(verbosity=2).run(chaine)
# Les 26 tests réels du moteur V7 attendent le contrat historique V6 via ICI.
sys.path.insert(0, str(V7))
import monter_v6
monter_v6.ICI = FIXTURE
moteur = unittest.TestLoader().discover(str(V7), pattern='test_monter_v6.py')
resultat_moteur = unittest.TextTestRunner(verbosity=2).run(moteur)
blocage_reseau.stop()
print(f'Tests exécutés : chaîne {resultat_chaine.testsRun}/48, moteur {resultat_moteur.testsRun}/26 ; erreurs/échecs : {len(resultat_chaine.errors)+len(resultat_chaine.failures)+len(resultat_moteur.errors)+len(resultat_moteur.failures)}', flush=True)
if not (resultat_chaine.wasSuccessful() and resultat_moteur.wasSuccessful()
        and resultat_chaine.testsRun >= 48 and resultat_moteur.testsRun >= 26):
    raise SystemExit(1)
