#!/usr/bin/env python3
"""Compare deux PNG alpha ou deux séquences explicites, sans inférence ni score perceptuel.

Manifeste : {"fps":"24/1", "frames":[{"index":0,"fichier":"alpha0000.png"}, ...]}.
Indices consécutifs, premier index libre mais identique des deux côtés. Les fichiers sont
relatifs au manifeste ou absolus. Le gris est un masque ; pour RGBA/LA,
seul le canal alpha est comparé. PNG 8 ou 16 bits ; RGB et palettes sont refusés.
"""
import argparse
import hashlib
import json
import math
import os
import re
import stat
import struct
import subprocess
import sys
import zlib
from fractions import Fraction
from pathlib import Path

import numpy as np

VERSION = '1.0'
MAX_PIXELS = 33_177_600  # 8K UHD ; limite le tampon de décodage CPU.
MAX_PNG_BYTES = 256 * 1024 * 1024
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
SIGNATURE = b'\x89PNG\r\n\x1a\n'


def _json_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'clé JSON dupliquée : {key}')
        result[key] = value
    return result


def _json_no_constant(value):
    raise ValueError(f'constante invalide : {value}')


def _fps(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+/[0-9]+', value):
        raise ValueError('cadence attendue sous forme de fraction positive, ex. 24/1')
    try:
        rate = Fraction(value)
    except ZeroDivisionError:
        raise ValueError('dénominateur de cadence nul') from None
    if rate <= 0:
        raise ValueError('cadence strictement positive requise')
    return rate


def _read_bounded(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError(f'fichier ordinaire requis : {path}')
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f'fichier trop volumineux : {path}')
    return data


def _file_sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _sequence(path):
    path = Path(path).resolve(strict=True)
    if path.suffix.lower() == '.png':
        return {'source': str(path), 'manifest_sha256': None, 'fps': None,
                'frames': [(0, path)]}
    raw = _read_bounded(path, MAX_MANIFEST_BYTES)
    try:
        manifest = json.loads(raw, object_pairs_hook=_json_unique,
                              parse_constant=_json_no_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f'manifeste invalide : {path}') from error
    if not isinstance(manifest, dict) or set(manifest) != {'fps', 'frames'}:
        raise ValueError('manifeste : champs fps et frames requis')
    rate = _fps(manifest['fps'])
    entries = manifest['frames']
    if not isinstance(entries, list) or not entries:
        raise ValueError('manifestes : liste frames non vide requise')
    frames = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {'index', 'fichier'}:
            raise ValueError('frame : index et fichier requis')
        index, name = entry['index'], entry['fichier']
        if type(index) is not int or index < 0 or not isinstance(name, str) or not name.strip():
            raise ValueError('frame : index entier positif ou nul et fichier requis')
        if frames and index != frames[-1][0] + 1:
            raise ValueError('indices de frames non consécutifs ou désordonnés')
        image = Path(name)
        if image.suffix.lower() != '.png':
            raise ValueError('chaque frame doit être un fichier PNG')
        frames.append((index, (path.parent / image).resolve(strict=True)))
    return {'source': str(path), 'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'fps': rate, 'frames': frames}


def _check_chunk(tag, size, offset, end, total, seen_idat):
    if tag in (b'acTL', b'fcTL', b'fdAT'):
        raise ValueError('PNG animé non pris en charge')
    if tag == b'IHDR' and offset != 8:
        raise ValueError('PNG : IHDR dupliqué')
    if tag in (b'tRNS', b'sBIT'):
        raise ValueError('PNG avec tRNS ou sBIT ambigu non pris en charge')
    if tag == b'IEND':
        if size or end != total or not seen_idat:
            raise ValueError('PNG : IEND invalide ou données excédentaires')
        return True
    return False


def _check_chunks(data):
    offset, seen_idat = 8, False
    while offset + 12 <= len(data):
        size = int.from_bytes(data[offset:offset+4], 'big')
        end = offset + 12 + size
        if end > len(data):
            raise ValueError('PNG tronqué')
        tag = data[offset+4:offset+8]
        expected_crc = int.from_bytes(data[end-4:end], 'big')
        if zlib.crc32(data[offset+4:end-4]) & 0xffffffff != expected_crc:
            raise ValueError('PNG : CRC invalide')
        seen_idat = seen_idat or tag == b'IDAT'
        if _check_chunk(tag, size, offset, end, len(data), seen_idat):
            return
        offset = end
    raise ValueError('PNG incomplet : IEND absent')


def _png_info(data):
    if len(data) < 33 or data[:8] != SIGNATURE or data[8:16] != b'\x00\x00\x00\rIHDR':
        raise ValueError('PNG invalide : en-tête absent')
    width, height, depth, color, compression, filt, interlace = struct.unpack('>IIBBBBB', data[16:29])
    if not (0 < width * height <= MAX_PIXELS) or width == 0 or height == 0:
        raise ValueError('PNG : dimensions invalides ou trop grandes')
    if (color, depth) not in {(0, 8), (0, 16), (4, 8), (4, 16), (6, 8), (6, 16)}:
        raise ValueError('PNG : gris, gris-alpha ou RGBA 8/16 bits requis')
    if compression or filt or interlace not in (0, 1):
        raise ValueError('PNG : en-tête non pris en charge')
    _check_chunks(data)
    return width, height, depth, color


def _alpha(path, ffmpeg):
    data = _read_bounded(path, MAX_PNG_BYTES)
    width, height, depth, color = _png_info(data)
    formats = {0: ('gray', 'gray16le'), 4: ('ya8', 'ya16le'), 6: ('rgba', 'rgba64le')}
    fmt = formats[color][depth == 16]
    command = [str(ffmpeg), '-nostdin', '-v', 'error', '-xerror', '-protocol_whitelist', 'pipe',
               '-f', 'image2pipe', '-c:v', 'png', '-i', 'pipe:0', '-frames:v', '1',
               '-pix_fmt', fmt, '-f', 'rawvideo', 'pipe:1']
    try:
        result = subprocess.run(command, input=data, capture_output=True, check=True, timeout=30,
                                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(f'décodage PNG impossible avec FFmpeg : {path} ({type(error).__name__})') from error
    channels = {0: 1, 4: 2, 6: 4}[color]
    if len(result.stdout) != width * height * channels * (depth // 8):
        raise ValueError(f'décodage PNG incomplet : {path}')
    values = np.frombuffer(result.stdout, dtype='u1' if depth == 8 else '<u2').reshape(height, width, channels)
    alpha = values[:, :, channels - 1].astype(np.float64) / ((1 << depth) - 1)
    return alpha, {'fichier': str(path), 'sha256': hashlib.sha256(data).hexdigest(),
                   'largeur': width, 'hauteur': height, 'profondeur_bits': depth}


def comparer(reference, candidat, ffmpeg):
    if (Path(reference).suffix.lower() == '.png') != (Path(candidat).suffix.lower() == '.png'):
        raise ValueError('image fixe et séquence ne peuvent pas être comparées')
    try:
        ffmpeg = Path(ffmpeg).resolve(strict=True)
    except OSError as error:
        raise ValueError('FFmpeg introuvable') from error
    if not ffmpeg.is_file() or not os.access(ffmpeg, os.X_OK):
        raise ValueError('FFmpeg doit être un exécutable local')
    decoder_sha = _file_sha256(ffmpeg)
    ref, cand = _sequence(reference), _sequence(candidat)
    if ref['fps'] != cand['fps']:
        raise ValueError('cadences incompatibles ou image fixe comparée à une séquence')
    if [i for i, _ in ref['frames']] != [i for i, _ in cand['frames']]:
        raise ValueError('nombre ou indices de frames différents')
    frames, transitions, provenance = [], [], {'reference': [], 'candidat': []}
    previous, shape = None, None
    for (index, rp), (_, cp) in zip(ref['frames'], cand['frames']):
        expected, rmeta = _alpha(rp, ffmpeg)
        actual, cmeta = _alpha(cp, ffmpeg)
        if expected.shape != actual.shape or (shape is not None and expected.shape != shape):
            raise ValueError(f'dimensions incompatibles à la frame {index}')
        shape = expected.shape
        residual = actual - expected
        frames.append({'index': index, 'mae_alpha': float(np.mean(np.abs(residual)))})
        if previous is not None:
            transitions.append({'index': index, 'variation_temporelle_residu': float(np.mean(np.abs(residual - previous)))})
        previous = residual
        provenance['reference'].append({'index': index, **rmeta})
        provenance['candidat'].append({'index': index, **cmeta})
    if _file_sha256(ffmpeg) != decoder_sha:
        raise ValueError('FFmpeg a changé pendant la comparaison')
    values = [x['variation_temporelle_residu'] for x in transitions]
    return {'version': VERSION, 'decodeur': {'outil': 'ffmpeg', 'chemin': str(ffmpeg), 'sha256': decoder_sha}, 'fps': f"{ref['fps'].numerator}/{ref['fps'].denominator}" if ref['fps'] is not None else None,
            'largeur': shape[1], 'hauteur': shape[0], 'nombre_frames': len(frames),
            'mae_alpha': math.fsum(x['mae_alpha'] for x in frames) / len(frames),
            'frames': frames, 'transitions': transitions,
            'variation_temporelle_moyenne': math.fsum(values) / len(values) if values else None,
            'variation_temporelle_max': max(values) if values else None,
            'sources': {role: {'source': seq['source'], 'manifest_sha256': seq['manifest_sha256'],
                               'images': provenance[role]} for role, seq in [('reference', ref), ('candidat', cand)]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True, type=Path)
    parser.add_argument('--candidat', required=True, type=Path)
    parser.add_argument('--sortie', required=True, type=Path)
    parser.add_argument('--ffmpeg', type=Path, default=Path('/usr/bin/ffmpeg'), help='exécutable FFmpeg local')
    args = parser.parse_args()
    report = comparer(args.reference, args.candidat, args.ffmpeg)
    payload = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    fd = os.open(args.sortie, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print(f'Erreur : {error}', file=sys.stderr)
        raise SystemExit(1)
