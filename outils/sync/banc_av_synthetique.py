#!/usr/bin/env python3
"""Banc synthétique AV : offset = temps impulsion audio - temps marqueur vidéo."""
import argparse
import hashlib
import json
import os
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import struct
import subprocess
from pathlib import Path

FPS, RATE, WIDTH, FRAMES = 25, 48000, 32, 50

def run(args):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30).stdout

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def create(folder, name, delta, ffmpeg, ffprobe):
    video = folder / (name + '.gray')
    audio = folder / (name + '.pcm')
    media = folder / (name + '.mkv')
    with video.open('xb') as f:
        for i in range(FRAMES):
            f.write(bytes([255 if i == 20 else 0]) * WIDTH * WIDTH)
    with audio.open('xb') as f:
        pulse = int((0.8 + delta) * RATE)
        for i in range(2 * RATE):
            f.write(struct.pack('<h', 24000 if pulse <= i < pulse + 48 else 0))
    run([str(ffmpeg), '-v','error','-nostdin','-n', '-f','rawvideo','-pixel_format','gray','-video_size',f'{WIDTH}x{WIDTH}','-framerate',str(FPS),'-i',str(video),'-f','s16le','-ar',str(RATE),'-ac','1','-i',str(audio),'-c:v','ffv1','-c:a','pcm_s16le',str(media)])
    info = json.loads(run([str(ffprobe),'-v','error','-show_entries','format=duration,start_time:stream=codec_type,codec_name,r_frame_rate,sample_rate,start_time,time_base','-of','json',str(media)]))
    streams = info.get('streams', [])
    if len(streams) != 2 or {s.get('codec_type') for s in streams} != {'video', 'audio'}:
        raise ValueError('Flux audio/vidéo attendus absents')
    try:
        if Decimal(info['format']['start_time']) != 0:
            raise ValueError('Départ du conteneur non nul')
        for stream in streams:
            if Decimal(stream['start_time']) != 0 or Fraction(stream['time_base']) <= 0:
                raise ValueError('Départ commun nul ou base de temps valide absent')
    except (KeyError, InvalidOperation, ZeroDivisionError) as exc:
        raise ValueError('Horodatage absent ou invalide') from exc
    frames = run([str(ffmpeg),'-v','error','-nostdin','-i',str(media),'-map','0:v:0','-f','rawvideo','-pix_fmt','gray','pipe:1'])
    samples = run([str(ffmpeg),'-v','error','-nostdin','-i',str(media),'-map','0:a:0','-f','s16le','-acodec','pcm_s16le','-ac','1','-ar',str(RATE),'pipe:1'])
    if len(frames) != FRAMES * WIDTH * WIDTH or len(samples) != 2 * RATE * 2:
        raise ValueError('Durée décodée inattendue')
    marked = [i for i in range(FRAMES) if max(frames[i*WIDTH*WIDTH:(i+1)*WIDTH*WIDTH]) > 200]
    hits = [i for i,(value,) in enumerate(struct.iter_unpack('<h',samples)) if value > 20000]
    if marked != [20] or len(hits) != 48 or hits != list(range(hits[0], hits[0]+48)):
        raise ValueError('Marqueur ou impulsion invalide')
    measured = hits[0] / RATE - marked[0] / FPS
    if abs(measured - delta) > 1 / RATE:
        raise ValueError('Décalage mesuré incorrect')
    return {'media':media.name,'sha256':sha(media),'video_frame':marked[0],'audio_sample':hits[0],'offset_secondes':round(measured,6),'attendu_secondes':delta,'ffprobe':info}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path,help='répertoire neuf, créé sans écrasement')
    p.add_argument('--ffmpeg', type=Path, required=True)
    p.add_argument('--ffprobe', type=Path, required=True)
    args=p.parse_args()
    for binary in (args.ffmpeg, args.ffprobe):
        if not binary.is_absolute() or not binary.is_file() or not os.access(binary, os.X_OK):
            p.error(f'Exécutable absolu invalide : {binary}')
    versions = {name: run([str(binary), '-version']).decode('utf-8', 'replace').splitlines()[0]
                for name, binary in [('ffmpeg', args.ffmpeg), ('ffprobe', args.ffprobe)]}
    args.destination.mkdir(mode=0o700)
    results=[create(args.destination,n,d,args.ffmpeg,args.ffprobe) for n,d in [('zero',0.0),('retard_audio',0.2),('avance_audio',-0.2)]]
    report={'nature':'marqueur synthétique ; aucune mesure de lèvres ou de visèmes','fps':FPS,'audio_hz':RATE,'versions':versions,'resultats':results}
    with (args.destination/'resultats.json').open('x') as f:
        json.dump(report,f,indent=2,ensure_ascii=False)
        f.write('\n')
    print(json.dumps({'resultats':[{k:r[k] for k in ('media','sha256','video_frame','audio_sample','offset_secondes','attendu_secondes')} for r in results]},ensure_ascii=False))

if __name__ == '__main__':
    main()
