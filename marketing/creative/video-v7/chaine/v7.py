#!/usr/bin/env python3
"""Chaîne commune V7 : python3 chaine/v7.py <commande> <équipe> [options]."""
import sys
sys.dont_write_bytecode = True
import argparse
import json
from pathlib import Path

from commun import DATA, ICI, V7, IDENTIFIANT, lire_json, valider
from production import Atelier, verrou

COMMANDES = ('valider', 'cles', 'plans', 'voix', 'musique', 'monter', 'juger-musique', 'planche', 'telephone', 'archiver', 'bilan')


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('commande', choices=COMMANDES)
    p.add_argument('equipe', help='nom dans video-v7/equipes/, ou chemin du dossier.json')
    p.add_argument('--a-blanc', action='store_true', help='aucun réseau ; médias doublés, montage CPU réel')
    p.add_argument('--donnees', type=Path, help='racine de données (défaut disque externe ; à blanc : chaine/.a-blanc)')
    p.add_argument('--musique', help='identifiant mX pour une variante')
    p.add_argument('--langue', choices=('fr', 'en'), action='append', help='répétable ; défaut fr')
    p.add_argument('--anglais', action='store_true', help='ajouter en au français')
    p.add_argument('--format', choices=('16x9', '9x16'), action='append', help='répétable ; défaut les deux')
    p.add_argument('--brouillon', action='store_true')
    p.add_argument('--jobs', type=int, default=1, help='processus CPU pour monter_v6')
    return p


def dossier(valeur):
    p = Path(valeur).expanduser()
    if p.is_file():
        return p.resolve()
    if p.is_dir() and (p / 'dossier.json').exists():
        return (p / 'dossier.json').resolve()
    if not IDENTIFIANT.fullmatch(valeur):
        raise ValueError(f'Équipe ou chemin introuvable : {valeur}')
    candidats = [V7 / 'equipes' / valeur / 'dossier.json', ICI / 'equipes' / valeur / 'dossier.json']
    return next((f for f in candidats if f.exists()), candidats[0])


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        path = dossier(args.equipe)
        d = lire_json(path)
        if d is None:
            raise ValueError(f'Dossier absent : {path}')
        erreurs, warnings = valider(d, path.parent)
        for w in warnings:
            print('AVERTISSEMENT : '+w)
        if erreurs:
            for e in erreurs:
                print('ERREUR : '+e)
            return 1
        if args.commande == 'valider':
            print('OK')
            return 0
        if args.jobs < 1:
            raise ValueError('--jobs doit être positif')
        root = (args.donnees or (ICI / '.a-blanc' if args.a_blanc else DATA)).expanduser().resolve()
        if args.a_blanc and root == DATA.resolve():
            raise ValueError('--a-blanc : choisir une racine distincte des données de production')
        travail = root / d['equipe']
        # Un seul écrivain par équipe, quatre équipes indépendantes autorisées.
        with verrou(travail / '.chaine.lock'):
            atelier = Atelier(d, path.parent, travail, args.a_blanc)
            if args.commande == 'monter':
                langues = args.langue or ['fr']
                if args.anglais and 'en' not in langues:
                    langues.append('en')
                result = atelier.monter(args.musique, langues, args.format or ['16x9', '9x16'], args.brouillon, args.jobs)
            else:
                method = {'juger-musique': 'juger_musique'}.get(args.commande, args.commande)
                result = getattr(atelier, method)()
        if result is not None:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        print('OK')
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as e:
        print(f'ERREUR : {e}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Interrompu ; état conservé pour la reprise.', file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
