"""Adaptateur voix OPSYS Eleven v4 ; sorties/reçus exclusifs, sans connexion à l'import."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request

MODELE = 'elevenlabs/eleven-v4'
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')


def _identifiant(value, nom):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f'{nom} invalide')
    return value


def contrat(equipe, lid, moteur, texte, direction, vitesse, prise, langue):
    _identifiant(equipe, 'Équipe'); _identifiant(lid, 'Réplique')
    if not isinstance(moteur, str) or not moteur.startswith('eleven:'):
        raise ValueError('Un identifiant eleven:<voix> explicite est requis.')
    voix = _identifiant(moteur.removeprefix('eleven:'), 'Voix')
    if langue not in ('fr', 'en'):
        raise ValueError('Langue explicite requise : fr ou en.')
    if not isinstance(texte, str) or not texte.strip() or not isinstance(direction, str):
        raise ValueError('Texte et direction invalides.')
    if isinstance(vitesse, bool) or not isinstance(vitesse, (int, float)) or not math.isfinite(vitesse) or vitesse != 1:
        raise ValueError('Eleven v4 : vitesse numérique non neutre non prise en charge.')
    if type(prise) is not int or prise < 1:
        raise ValueError('Prise invalide.')
    direction = direction.strip().replace('[', '').replace(']', '')
    entree = f'[{direction}] {texte}' if direction else texte
    return {'equipe': equipe, 'id': lid, 'prise': prise, 'moteur': moteur, 'modele_demande': MODELE,
            'voix': voix, 'langue': langue, 'input': entree, 'vitesse': 1, 'response_format': 'mp3'}


def demander(corps):
    """Réutilise la résolution explicite du client V7 ; aucun fichier de clé n'est lu."""
    chemin = Path(__file__).resolve().parents[5] / 'marketing/creative/video-v7/chaine/commun.py'
    spec = importlib.util.spec_from_file_location('opsys_client_v7_commun', chemin)
    if spec is None or spec.loader is None:
        raise RuntimeError('Client V7 indisponible.')
    commun = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(commun)
    url, cle = commun.api_configuration('audio/speech', MODELE)
    requete = urllib.request.Request(url, data=json.dumps(corps).encode(),
                                     headers={'Authorization': 'Bearer ' + cle, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(requete, timeout=300) as reponse:
            return reponse.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'HTTP {exc.code}') from None


def _sha(fichier):
    h = hashlib.sha256()
    with fichier.open('rb') as audio:
        for bloc in iter(lambda: audio.read(1024 * 1024), b''):
            h.update(bloc)
    return h.hexdigest()


def _creer(fichier, data):
    with fichier.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def signature(spec, factice):
    return hashlib.sha256(json.dumps({'contrat': spec, 'factice': factice}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ligne(equipe, lid, moteur, texte, direction, vitesse, prise, *, langue, racine, ffmpeg, transport=None, factice=False):
    if (transport is None) == factice:
        raise ValueError('Transport injecté et origine factice doivent être déclarés ensemble.')
    spec = contrat(equipe, lid, moteur, texte, direction, vitesse, prise, langue)
    empreinte = signature(spec, factice)
    root = Path(racine).absolute()
    dossier = root / equipe / 'voix' / 'eleven4' / spec['voix'] / empreinte
    if any(p.is_symlink() for p in (root, root / equipe, root / equipe / 'voix', root / equipe / 'voix' / 'eleven4', dossier.parent, dossier)):
        raise ValueError('Lien symbolique interdit dans le cache de voix.')
    dossier.mkdir(parents=True, exist_ok=True)
    source = dossier / f'{lid}-p{prise}.mp3'
    cible = dossier / f'{lid}-p{prise}.wav'
    recu = dossier / f'{lid}-p{prise}.json'
    intention = dossier / 'intention.json'
    # Une intention existante sans reçu indique un résultat incertain : aucun nouvel appel.
    if recu.exists() and not recu.is_symlink():
        data = json.loads(recu.read_text())
        if data.get('contrat') == spec and verifier_recu(data, recu, factice):
            return data
        raise ValueError('Reçu de voix existant incompatible ; fichiers conservés.')
    if any(p.exists() or p.is_symlink() for p in (intention, source, cible, recu)):
        raise FileExistsError('Prise partielle ou existante ; aucun nouvel envoi.')
    _creer(intention, json.dumps({'signature': empreinte, 'statut': 'intention_avant_envoi'}).encode())
    corps = {k: spec[k] for k in ('modele_demande', 'input', 'response_format')}
    corps['model'] = corps.pop('modele_demande'); corps['voice'] = spec['voix']
    octets = (transport or demander)(corps)
    if not isinstance(octets, bytes) or not octets:
        raise ValueError('Réponse audio vide ou invalide.')
    _creer(source, octets)
    subprocess.run([str(ffmpeg), '-nostdin', '-n', '-v', 'error', '-i', str(source), '-ar', '48000', '-ac', '2', str(cible)],
                   check=True, capture_output=True, timeout=120)
    data = {'equipe': equipe, 'id': lid, 'prise': prise, 'moteur': moteur, 'langue': langue,
            'modele_demande': MODELE, 'origine': 'factice' if factice else 'modele_demande_non_atteste',
            'signature': empreinte, 'contrat': spec, 'direction_demandee': spec['input'] != texte, 'vitesse': vitesse,
            'fichier': str(cible), 'sha256': _sha(cible), 'source_sha256': _sha(source),
            'duree_s': None, 'utile_s': None, 'emr': None, 'oreille': None, 'statut_humain': 'non_juge'}
    _creer(recu, (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode())
    return data


def verifier_recu(recu, chemin_recu, autoriser_factice=False):
    chemin_recu = Path(chemin_recu)
    attendu = chemin_recu.with_suffix('.wav')
    source = chemin_recu.with_suffix('.mp3')
    origine = recu.get('origine')
    if origine != 'modele_demande_non_atteste' and not (autoriser_factice and origine == 'factice'):
        return False
    if (chemin_recu.is_symlink() or recu.get('signature') != chemin_recu.parent.name
            or recu.get('modele_demande') != MODELE or recu.get('langue') not in ('fr', 'en')
            or not isinstance(recu.get('moteur'), str) or not recu['moteur'].startswith('eleven:')
            or not isinstance(recu.get('fichier'), str) or attendu.is_symlink() or not attendu.is_file()
            or source.is_symlink() or not source.is_file()):
        return False
    return (Path(recu['fichier']).resolve() == attendu.resolve() and recu.get('sha256') == _sha(attendu)
            and recu.get('source_sha256') == _sha(source))
