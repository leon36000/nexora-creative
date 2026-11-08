#!/usr/bin/env python3
"""Prépare un manifeste de banc : aucune génération ni transformation de média."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys


def positif(texte):
    nombre = float(texte)
    if not math.isfinite(nombre) or nombre <= 0:
        raise argparse.ArgumentTypeError('valeur finie strictement positive attendue')
    return nombre


def non_negatif(texte):
    nombre = float(texte)
    if not math.isfinite(nombre) or nombre < 0:
        raise argparse.ArgumentTypeError('valeur finie positive ou nulle attendue')
    return nombre


def fichier(chemin):
    if '..' in Path(chemin).parts:
        raise ValueError('chemin contenant .. refusé')
    p = Path(chemin).absolute()
    if any(c.is_symlink() for c in (p, *p.parents)) or not p.is_file():
        raise ValueError(f'fichier inaccessible, non régulier ou lien symbolique : {p}')
    return p


def empreinte(p):
    h = hashlib.sha256()
    avant = p.stat()
    with p.open('rb') as entree:
        for bloc in iter(lambda: entree.read(1024 * 1024), b''):
            h.update(bloc)
    apres = p.stat()
    if (avant.st_dev, avant.st_ino, avant.st_size, avant.st_mtime_ns) != (apres.st_dev, apres.st_ino, apres.st_size, apres.st_mtime_ns):
        raise ValueError(f'entrée modifiée pendant lecture : {p}')
    return h.hexdigest()


def examiner(ffprobe, chemin, type_flux):
    p = fichier(chemin)
    avant = p.stat()
    processus = subprocess.Popen([str(ffprobe), '-v', 'error', '-protocol_whitelist', 'file,pipe',
        '-show_streams', '-show_format', '-of', 'json', str(p)], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    try:
        stdout, stderr = processus.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            processus.kill()  # uniquement le processus enfant que nous avons créé
            processus.communicate(timeout=2)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError(f'ffprobe délai dépassé ; arrêt enfant non confirmé : {exc}') from exc
        raise ValueError('ffprobe délai dépassé ; arrêt enfant confirmé') from None
    if processus.returncode:
        raise ValueError(f'ffprobe code {processus.returncode} : {stderr.decode(errors="replace")[:500]}')
    info = json.loads(stdout)
    flux = [s for s in info.get('streams', []) if s.get('codec_type') == type_flux
            and not (type_flux == 'video' and s.get('disposition', {}).get('attached_pic'))]
    if len(flux) != 1:
        raise ValueError(f'{p} : un seul flux {type_flux} attendu, trouvé {len(flux)}')
    # La durée du flux prime ; le conteneur n'est pas une preuve de durée du flux.
    try:
        duree = float(flux[0]['duration'])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f'{p} : durée du flux {type_flux} absente ou invalide') from None
    if not math.isfinite(duree) or duree <= 0:
        raise ValueError(f'{p} : durée du flux invalide')
    sha = empreinte(p)
    apres = p.stat()
    if (avant.st_dev, avant.st_ino, avant.st_size, avant.st_mtime_ns) != (apres.st_dev, apres.st_ino, apres.st_size, apres.st_mtime_ns):
        raise ValueError(f'entrée modifiée pendant son analyse : {p}')
    return {'chemin': str(p), 'sha256': sha, 'taille_octets': apres.st_size,
            'duree_flux_secondes': duree, 'ffprobe': info}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--pair', nargs=4, metavar=('LANG', 'TYPE', 'VIDEO', 'AUDIO'), action='append', required=True)
    parser.add_argument('--fps', type=positif, required=True)
    parser.add_argument('--padding-seconds', type=non_negatif, required=True)
    parser.add_argument('--ffprobe', required=True)
    args = parser.parse_args(argv)
    try:
        if '..' in Path(args.namespace).parts:
            raise ValueError('namespace contenant .. refusé')
        destination = Path(args.namespace).absolute()
        if os.path.lexists(destination):
            raise ValueError('namespace déjà existant : aucun fichier ou cache ne sera réutilisé')
        if any(p.is_symlink() for p in destination.parents) or not destination.parent.is_dir():
            raise ValueError('parent absent ou lien symbolique')
        sonde = fichier(args.ffprobe)
        couples = []
        for langue, genre, video, audio in args.pair:
            if langue not in ('fr', 'en') or genre not in ('continu', 'avatar-bouclable'):
                raise ValueError('langue ou type de plan inconnu')
            v, a = examiner(sonde, video, 'video'), examiner(sonde, audio, 'audio')
            boucle = a['duree_flux_secondes'] > v['duree_flux_secondes']
            if boucle and genre == 'continu':
                raise ValueError('plan continu plus court que son audio')
            couples.append({'expected_language': langue, 'type': genre, 'video': v, 'audio': a,
                            'boucle_necessaire_selon_durees': boucle})
        manifeste = {'statut': 'ESSAI NON APPROUVE', 'generation_effectuee': False,
            'contrat_declare': {'fps_cible': args.fps, 'padding_video_clone_secondes_par_segment': args.padding_seconds,
                'boucle_autorisee_uniquement_avatar': True, 'transformations_executees': False},
            'ffprobe': str(sonde), 'couples': couples}
        destination.mkdir(mode=0o700)  # réservation atomique ; aucun namespace existant réutilisé
        with (destination / 'manifest.json').open('x', encoding='utf-8') as sortie:
            json.dump(manifeste, sortie, ensure_ascii=False, indent=2, allow_nan=False)
            sortie.write('\n')
        print(destination / 'manifest.json')
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f'prévol refusé : {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
