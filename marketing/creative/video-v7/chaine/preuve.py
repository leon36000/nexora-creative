#!/usr/bin/env python3
"""Preuve CPU hors ligne des onze commandes ; aucun appel GPU/API/SSH."""
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.dont_write_bytecode = True
from commun import ICI, ecrire_json
from production import binaire, sonder, image_juge
from v7 import main


def preuve():
    debut = time.monotonic()
    root = ICI / '.a-blanc'
    with patch('urllib.request.urlopen', side_effect=AssertionError('Réseau interdit pendant la preuve')):
        for cmd in ('valider', 'cles', 'plans', 'voix', 'musique', 'monter', 'juger-musique', 'planche', 'telephone', 'archiver', 'bilan'):
            args = [cmd, 'essai', '--a-blanc', '--donnees', str(root)]
            if cmd == 'monter':
                args.append('--brouillon')
            print('\n$ python3 chaine/v7.py '+' '.join(args), flush=True)
            if main(args):
                raise RuntimeError(f'Preuve échouée : {cmd}')
    films = []
    for f in sorted((root/'essai/films').glob('*.mp4')):
        j = sonder(f)
        video = next(s for s in j['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in j['streams'] if s['codec_type'] == 'audio')
        assert abs(float(j['format']['duration'])-10) < .1
        assert video['codec_name'] == 'h264' and video['r_frame_rate'] == '24/1'
        assert audio['codec_name'] == 'aac'
        films.append({'fichier': str(f), 'duree': j['format']['duration'], 'resolution': [video['width'], video['height']],
                      'video': video['codec_name'], 'audio': audio['codec_name']})
        # Vérification réelle du triptyque, sans appeler le juge distant.
        assert image_juge(f).startswith('data:image/jpeg;base64,')
    assert len(films) == 2
    copies = []
    for f in sorted((root/'essai/telephone').glob('*.mp4')):
        assert f.stat().st_size <= 28_000_000
        raw = f.read_bytes()
        assert raw.find(b'moov') < raw.find(b'mdat')
        copies.append({'fichier': str(f), 'octets': f.stat().st_size})
    assert len(copies) == 2
    report = {'reseau': False, 'gpu': False, 'commandes': 11, 'films': films, 'telephone': copies,
              'secondes': round(time.monotonic()-debut, 2), 'ffmpeg': binaire('ffmpeg')}
    ecrire_json(root/'essai/preuve.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    preuve()
