"""Export CPU distinct d'un rendu HighSync ; ne lance aucun modèle.

Le fichier canonique conserve les N premières images en H.264 lossless et
l'audio PCM intégral. Il ne modifie jamais le rendu ni le PCM sources.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import uuid
import wave

from outils.sync import valider_duree_av as av
from outils.sync.labo.highsync_preflight import _verifier_fichier


def _sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def _decoder_pcm(ffmpeg, audio):
    cmd = [str(ffmpeg), '-v','error','-xerror','-nostdin','-protocol_whitelist','file,pipe',
           '-i',str(audio),'-map','0:a:0','-vn','-ac','1','-ar','16000',
           '-c:a','pcm_s16le','-f','s16le','pipe:1']
    return hashlib.sha256(av.executer(cmd, 120, True, 32*1024*1024)).hexdigest()


def _images_md5(ffmpeg, video, nombre):
    cmd = [str(ffmpeg), '-v','error','-xerror','-nostdin','-protocol_whitelist','file,pipe',
           '-i',str(video),'-map','0:v:0','-an','-frames:v',str(nombre),'-f','framemd5','pipe:1']
    lignes = av.executer(cmd, 180, True, 16*1024*1024).decode('ascii').splitlines()
    images = [l.split(',')[-1].strip() for l in lignes if l and not l.startswith('#')]
    if len(images) != nombre or any(len(x) != 32 for x in images):
        raise ValueError('empreintes images incomplètes')
    return images


def exporter(root: Path, brut: Path, brut_sha: str, audio: Path, audio_sha: str,
             ffmpeg: Path, ffprobe: Path, telephone: bool = False) -> Path:
    if not root.is_absolute() or root.is_symlink() or not root.is_dir() or root.resolve() != root:
        raise ValueError('racine de sortie invalide')
    _verifier_fichier(brut, brut_sha)
    _verifier_fichier(audio, audio_sha)
    for binaire in (ffmpeg, ffprobe):
        if not binaire.is_absolute() or not binaire.is_file() or not os.access(binaire, os.X_OK):
            raise ValueError('binaire absolu exécutable requis')
    try:
        with wave.open(str(audio), 'rb') as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, 'NONE'):
                raise ValueError('audio WAV PCM mono 16 bits 16 kHz requis')
    except (wave.Error, EOFError) as exc:
        raise ValueError('audio WAV PCM invalide') from exc
    mesures = av.mesure_audio(ffmpeg, audio, av.informations(ffprobe, audio, 120), 120)
    if mesures['frequence_hz'] != 16000:
        raise ValueError('audio 16 kHz requis')
    cible = Fraction(mesures['echantillons'] * 25, mesures['frequence_hz'])
    if cible.denominator != 1 or cible <= 0:
        raise ValueError('durée PCM non entière en images à 25 i/s')
    nombre = int(cible)
    video = av.mesure_video(ffprobe, brut, av.informations(ffprobe, brut, 120), 120)
    if (Fraction(video['cadence_moyenne']) != 25 or
        any(abs(i - .04) > .001 for i in video['intervalles_images_secondes']) or
        video['images_decodees'] < nombre):
        raise ValueError('vidéo trop courte ou non CFR 25 i/s')
    reference_images = _images_md5(ffmpeg, brut, nombre)
    reference_pcm = _decoder_pcm(ffmpeg, audio)
    run = root/('highsync-export-'+uuid.uuid4().hex)
    run.mkdir(mode=0o700)
    canonique = run/'canonique.mkv'
    commande = [str(ffmpeg),'-v','error','-xerror','-nostdin','-n','-protocol_whitelist','file,pipe',
                '-i',str(brut),'-i',str(audio),'-map','0:v:0','-map','1:a:0',
                '-frames:v',str(nombre),'-c:v','libx264','-crf','0','-pix_fmt','yuv420p',
                '-c:a','pcm_s16le','-ar','16000',str(canonique)]
    resultat = {'statut':'echec','brut_sha256':brut_sha,'audio_sha256':audio_sha,
                'ffmpeg_sha256':_sha(ffmpeg),'ffprobe_sha256':_sha(ffprobe),
                'images_source':video['images_decodees'],'images_cibles':nombre,
                'echantillons_pcm':mesures['echantillons'],'commande_canonique':commande}
    try:
        av.executer(commande, 180, True)
        if _images_md5(ffmpeg, canonique, nombre) != reference_images:
            raise ValueError('images décodées différentes du brut')
        if _decoder_pcm(ffmpeg, canonique) != reference_pcm:
            raise ValueError('PCM exporté différent de la source')
        _verifier_fichier(brut, brut_sha)
        _verifier_fichier(audio, audio_sha)
        controle = av.valider(audio, canonique, ffmpeg, ffprobe, 0, cadence_cible='25')
        if not controle['valide'] or controle['video']['images_decodees'] != nombre:
            raise ValueError('validation audiovisuelle canonique refusée')
        resultat.update(statut='canonique_valide', validation_av=controle,
                        canonique_sha256=_sha(canonique), pcm_decode_sha256=reference_pcm,
                        images_framemd5_sha256=hashlib.sha256(('\n'.join(reference_images)+'\n').encode()).hexdigest())
        if telephone:
            mobile = run/'telephone.mp4'
            cmd = [str(ffmpeg),'-v','error','-xerror','-nostdin','-n','-protocol_whitelist','file,pipe',
                   '-i',str(canonique),'-map','0:v:0','-map','0:a:0','-c:v','libx264','-crf','18',
                   '-pix_fmt','yuv420p','-c:a','aac','-ar','44100',str(mobile)]
            resultat['commande_telephone'] = cmd
            av.executer(cmd,180,True)
            controle_mobile = av.valider(audio,mobile,ffmpeg,ffprobe,.08,cadence_cible='25')
            if not controle_mobile['valide'] or controle_mobile['video']['images_decodees'] != nombre or mobile.stat().st_size >= 28_000_000:
                raise ValueError('version téléphone invalide ou supérieure à 28 Mo')
            resultat.update(statut='canonique_et_telephone_valides',telephone_sha256=_sha(mobile),
                            telephone_octets=mobile.stat().st_size,validation_telephone=controle_mobile)
    except (OSError, ValueError, av.ValidationErreur) as exc:
        resultat.update(statut='echec',erreur=str(exc))
    with (run/'manifest.json').open('x',encoding='utf-8') as f:
        os.fchmod(f.fileno(),0o600)
        json.dump(resultat,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
    return run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root',type=Path,required=True); p.add_argument('--brut',type=Path,required=True)
    p.add_argument('--brut-sha256',required=True);p.add_argument('--audio',type=Path,required=True)
    p.add_argument('--audio-sha256',required=True);p.add_argument('--ffmpeg',type=Path,required=True)
    p.add_argument('--ffprobe',type=Path,required=True);p.add_argument('--telephone',action='store_true')
    args=p.parse_args()
    try:
        run=exporter(args.run_root,args.brut,args.brut_sha256,args.audio,args.audio_sha256,args.ffmpeg,args.ffprobe,args.telephone)
        manifest=json.loads((run/'manifest.json').read_text())
        print(json.dumps({'run':str(run),'statut':manifest['statut']},ensure_ascii=False))
        return 0 if manifest['statut']!='echec' else 1
    except (ValueError,OSError,av.ValidationErreur) as exc:
        print(json.dumps({'statut':'refuse','erreur':str(exc)},ensure_ascii=False));return 1


if __name__ == '__main__':
    raise SystemExit(main())
