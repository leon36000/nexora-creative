#!/usr/bin/env python3
"""Contrôle de durée audiovisuelle CPU ; ne juge pas la synchronisation labiale."""
import argparse
import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import time
from fractions import Fraction


class ValidationErreur(Exception):
    pass


def fichier(valeur):
    try:
        p = Path(valeur).resolve(strict=True)
        if not p.is_file():
            raise ValueError()
        return p
    except (OSError, ValueError) as exc:
        raise ValidationErreur('Fichier local absent ou invalide') from exc


def executer(args, limite_s, conserver, limite_contenu=65536):
    """Lit les octets sans stocker le PCM ; n'attend jamais indéfiniment l'enfant."""
    try:
        p = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise ValidationErreur('Exécutable indisponible') from exc
    selection = selectors.DefaultSelector()
    selection.register(p.stdout, selectors.EVENT_READ)
    fin = time.monotonic() + limite_s
    contenu, taille = bytearray(), 0
    try:
        while True:
            reste = fin - time.monotonic()
            if reste <= 0:
                raise ValidationErreur('Délai de décodage dépassé')
            if not selection.select(reste):
                raise ValidationErreur('Délai de décodage dépassé')
            bloc = os.read(p.stdout.fileno(), 65536)
            if not bloc:
                break
            taille += len(bloc)
            if conserver:
                if taille > limite_contenu:
                    raise ValidationErreur('Métadonnées excessives')
                contenu.extend(bloc)
        try:
            code = p.wait(timeout=max(0.001, fin - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise ValidationErreur('Délai de décodage dépassé') from exc
        if code:
            raise ValidationErreur('Média illisible ou décodage échoué')
        return bytes(contenu) if conserver else taille
    finally:
        selection.close()
        if p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    p.kill()
                    p.wait(timeout=1)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise ValidationErreur('Arrêt du décodeur non confirmé') from exc
        if p.stdout:
            p.stdout.close()


def informations(ffprobe, chemin, delai):
    data = executer([str(ffprobe), '-v', 'error', '-protocol_whitelist', 'file,pipe', '-count_frames',
                     '-show_entries', 'stream=codec_type,sample_rate,nb_read_frames,avg_frame_rate,duration',
                     '-of', 'json', str(chemin)], delai, True)
    try:
        flux = json.loads(data)['streams']
        if not isinstance(flux, list):
            raise ValueError()
        return flux
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationErreur('Métadonnées de flux invalides') from exc


def mesure_audio(ffmpeg, chemin, flux, delai):
    try:
        audio = next(x for x in flux if x.get('codec_type') == 'audio')
        taux = int(audio['sample_rate'])
        if not 8000 <= taux <= 192000:
            raise ValueError()
    except (StopIteration, KeyError, TypeError, ValueError) as exc:
        raise ValidationErreur('Flux audio absent ou fréquence invalide') from exc
    octets = executer([str(ffmpeg), '-v', 'error', '-xerror', '-nostdin', '-protocol_whitelist', 'file,pipe',
                       '-i', str(chemin), '-map', '0:a:0', '-vn', '-ac', '1', '-ar', str(taux),
                       '-c:a', 'pcm_s16le', '-f', 's16le', 'pipe:1'], delai, False)
    if not octets or octets % 2:
        raise ValidationErreur('Audio décodé vide ou incomplet')
    return {'echantillons': octets // 2, 'frequence_hz': taux, 'duree_secondes': octets / 2 / taux}


def mesure_video(ffprobe, chemin, flux, delai):
    try:
        video = next(x for x in flux if x.get('codec_type') == 'video')
        images = int(video['nb_read_frames'])
        cadence = Fraction(video['avg_frame_rate'])
        if images <= 0 or cadence <= 0 or cadence > 240:
            raise ValueError()
        donnees = executer([str(ffprobe), '-v', 'error', '-protocol_whitelist', 'file,pipe',
                             '-select_streams', 'v:0', '-show_frames',
                             '-show_entries', 'frame=best_effort_timestamp_time,duration_time,pkt_duration_time',
                             '-of', 'json', str(chemin)], delai, True, 16 * 1024 * 1024)
        frames = json.loads(donnees)['frames']
        if len(frames) != images:
            raise ValueError()
        pts = [float(x['best_effort_timestamp_time']) for x in frames]
        if any(not math.isfinite(t) for t in pts) or any(b <= a for a, b in zip(pts, pts[1:])):
            raise ValueError()
        duree_fin, provenance = None, None
        for champ in ('duration_time', 'pkt_duration_time'):
            try:
                candidate = float(frames[-1][champ])
                if math.isfinite(candidate) and candidate > 0:
                    duree_fin, provenance = candidate, champ
                    break
            except (KeyError, TypeError, ValueError):
                pass
        if duree_fin is None:
            duree_fin, provenance = 1 / float(cadence), 'estimation_cadence_moyenne'
        duree = pts[-1] - pts[0] + duree_fin
        return {'images_decodees': images, 'cadence_moyenne': str(cadence), 'duree_secondes': duree,
                'intervalles_images_secondes': [b - a for a, b in zip(pts, pts[1:])],
                'methode_duree': ('ecart_pts_images_plus_estimation_derniere_image' if provenance == 'estimation_cadence_moyenne'
                                   else 'ecart_pts_images_plus_duree_derniere_image'),
                'pts_premiere_image_secondes': pts[0], 'pts_derniere_image_secondes': pts[-1],
                'duree_derniere_image_secondes': duree_fin, 'provenance_duree_derniere_image': provenance}
    except (StopIteration, KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ValidationErreur('Flux vidéo absent ou horodatages invalides') from exc


def debut_audio(ffprobe, chemin, delai):
    donnees = executer([str(ffprobe), '-v', 'error', '-protocol_whitelist', 'file,pipe',
                         '-select_streams', 'a:0', '-show_frames',
                         '-show_entries', 'frame=best_effort_timestamp_time',
                         '-of', 'json', str(chemin)], delai, True, 16 * 1024 * 1024)
    try:
        frames = json.loads(donnees)['frames']
        debut = float(frames[0]['best_effort_timestamp_time'])
        if not math.isfinite(debut):
            raise ValueError()
        return debut
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValidationErreur('Départ audio du rendu absent ou invalide') from exc


def valider(reference, rendu, ffmpeg, ffprobe, padding_codec, delai=120, cadence_cible=None):
    if not math.isfinite(padding_codec) or not 0 <= padding_codec <= 1:
        raise ValidationErreur('Padding codec hors limites [0, 1] seconde')
    reference, rendu, ffmpeg, ffprobe = map(fichier, (reference, rendu, ffmpeg, ffprobe))
    ref = mesure_audio(ffmpeg, reference, informations(ffprobe, reference, delai), delai)
    flux = informations(ffprobe, rendu, delai)
    audio = mesure_audio(ffmpeg, rendu, flux, delai)
    video = mesure_video(ffprobe, rendu, flux, delai)
    image = video['duree_derniere_image_secondes']
    intervalles = video.pop('intervalles_images_secondes')
    ecart_video = video['duree_secondes'] - ref['duree_secondes']
    ecart_audio = audio['duree_secondes'] - ref['duree_secondes']
    audio['pts_premier_echantillon_secondes'] = debut_audio(ffprobe, rendu, delai)
    decalage = audio['pts_premier_echantillon_secondes'] - video['pts_premiere_image_secondes']
    cadence_valide = None
    if cadence_cible is not None:
        try:
            cible = Fraction(cadence_cible)
            if cible <= 0 or cible > 240:
                raise ValueError()
        except (ValueError, TypeError, ZeroDivisionError) as exc:
            raise ValidationErreur('Cadence cible invalide') from exc
        periode = 1 / float(cible)
        cadence_valide = (bool(intervalles) and abs(image - periode) <= .001
                           and all(abs(x - periode) <= .001 for x in intervalles))
    valide = (abs(ecart_video) <= image + 1e-6 and abs(ecart_audio) <= padding_codec + 1e-6
              and abs(decalage) <= image + padding_codec + 1e-6 and cadence_valide is not False)
    return {'valide': valide, 'audio_reference': ref, 'audio_rendu': audio, 'video': video,
            'tolerance': {'video_secondes': image, 'audio_secondes': padding_codec,
                          'decalage_debut_secondes': image + padding_codec,
                          'une_image_secondes': image, 'padding_codec_secondes': padding_codec,
                          'total_secondes': image + padding_codec},
            'cadence_cible': cadence_cible, 'cadence_cible_valide': cadence_valide,
            'ecarts_secondes': {'video_moins_reference': ecart_video, 'audio_moins_reference': ecart_audio,
                                'debut_audio_moins_video': decalage},
            'portee': 'durées et départs des flux uniquement ; aucune évaluation de synchronisation labiale'}



def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-audio', required=True)
    p.add_argument('--rendu', required=True)
    p.add_argument('--ffmpeg', required=True)
    p.add_argument('--ffprobe', required=True)
    p.add_argument('--padding-codec-secondes', type=float, required=True)
    p.add_argument('--cadence-cible', help='CFR requis ; périodes des images à 1 ms près, par exemple 24 ou 24000/1001')
    args = p.parse_args()
    try:
        resultat = valider(args.reference_audio, args.rendu, args.ffmpeg, args.ffprobe, args.padding_codec_secondes, cadence_cible=args.cadence_cible)
        print(json.dumps(resultat, ensure_ascii=False, allow_nan=False))
        return 0 if resultat['valide'] else 1
    except ValidationErreur as exc:
        print(json.dumps({'valide': False, 'erreur': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
