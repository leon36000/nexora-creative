"""
Écriture et relecture vérifiée des fichiers du détourage : PNG 16 bits (gris ou RGBA) et OpenEXR (demi-flottant, ZIP).
Écrivains maison, sans dépendance au-delà de numpy et zlib ; la relecture indépendante (OpenEXR, OpenCV, ffmpeg) se fait
dans les tests et dans le contrôle de fin de tâche. Ce qui est écrit est déclaré dans le fichier lui-même
(attribut EXR `nexora/alpha` : « premultiplied » ou « straight »).
"""
from __future__ import annotations

import struct
import zlib

import numpy as np

# ---------------------------------------------------------------- PNG 16 bits


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)


def ecrire_png16(chemin: str, img: np.ndarray, niveau: int = 4) -> None:
    """Écrit `img` (uint16 H×W gris, ou H×W×4 RGBA non prémultiplié) en PNG 16 bits. Filtre « Up » vectorisé."""
    if img.dtype != np.uint16:
        raise ValueError('uint16 attendu')
    if img.ndim == 2:
        h, w = img.shape
        canaux, ctype = 1, 0
    elif img.ndim == 3 and img.shape[2] == 4:
        h, w, _ = img.shape
        canaux, ctype = 4, 6
    else:
        raise ValueError('forme non prise en charge (H×W ou H×W×4)')
    brut = img.reshape(h, w * canaux).astype('>u2').view(np.uint8).reshape(h, w * canaux * 2)
    haut = np.vstack([np.zeros((1, brut.shape[1]), np.uint8), brut[:-1]])
    filtre = ((brut.astype(np.int16) - haut.astype(np.int16)) & 0xFF).astype(np.uint8)
    lignes = np.concatenate([np.full((h, 1), 2, np.uint8), filtre], axis=1)  # type de filtre 2 = Up
    ihdr = struct.pack('>IIBBBBB', w, h, 16, ctype, 0, 0, 0)
    with open(chemin, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr) + _chunk(b'IDAT', zlib.compress(lignes.tobytes(), niveau))
                + _chunk(b'IEND', b''))


def entete_png(chemin: str) -> dict:
    """Lit seulement l'en-tête PNG : largeur, hauteur, profondeur de bits, type de couleur (0 gris, 6 RGBA)."""
    with open(chemin, 'rb') as f:
        d = f.read(33)
    if d[:8] != b'\x89PNG\r\n\x1a\n' or d[12:16] != b'IHDR':
        raise ValueError('PNG invalide')
    w, h, bits, ctype = struct.unpack('>IIBB', d[16:26])
    return {'largeur': w, 'hauteur': h, 'bits': bits, 'type_couleur': ctype}


def alpha_vers_u16(a: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(a * 65535.0), 0, 65535).astype(np.uint16)


def rgba_vers_u16(rgb01: np.ndarray, a01: np.ndarray) -> np.ndarray:
    return np.concatenate([np.clip(np.rint(rgb01 * 65535.0), 0, 65535).astype(np.uint16), alpha_vers_u16(a01)[..., None]], axis=2)


# ---------------------------------------------------------------- OpenEXR

_MAGIE = b'\x76\x2f\x31\x01'
_COMPRESSION_ZIP16 = 3


def _attr(nom: str, type_: str, valeur: bytes) -> bytes:
    return nom.encode() + b'\0' + type_.encode() + b'\0' + struct.pack('<i', len(valeur)) + valeur


def ecrire_exr(chemin: str, rgba: np.ndarray | None = None, alpha: np.ndarray | None = None, premultiplie: bool = True,
               commentaire: str = '') -> None:
    """Écrit un EXR demi-flottant compressé ZIP (16 lignes par bloc).

    - `rgba` : float H×W×4. Si `premultiplie` vaut True, les canaux couleur DOIVENT déjà être multipliés par l'alpha
      (convention EXR) ; l'écrivain ne multiplie rien, il le déclare dans l'attribut `nexora/alpha`.
    - ou `alpha` seul : float H×W, écrit en un canal `A`.
    """
    if (rgba is None) == (alpha is None):
        raise ValueError('rgba ou alpha, pas les deux')
    if rgba is not None:
        h, w, _ = rgba.shape
        canaux = {'A': rgba[..., 3], 'B': rgba[..., 2], 'G': rgba[..., 1], 'R': rgba[..., 0]}
    else:
        h, w = alpha.shape
        canaux = {'A': alpha}
    noms = sorted(canaux)  # EXR : canaux triés par nom
    chlist = b''.join(n.encode() + b'\0' + struct.pack('<iBxxxii', 1, 0, 1, 1) for n in noms) + b'\0'  # 1 = HALF
    fenetre = struct.pack('<iiii', 0, 0, w - 1, h - 1)
    entete = (_attr('channels', 'chlist', chlist) + _attr('compression', 'compression', bytes([_COMPRESSION_ZIP16]))
              + _attr('dataWindow', 'box2i', fenetre) + _attr('displayWindow', 'box2i', fenetre)
              + _attr('lineOrder', 'lineOrder', b'\0') + _attr('pixelAspectRatio', 'float', struct.pack('<f', 1.0))
              + _attr('screenWindowCenter', 'v2f', struct.pack('<ff', 0, 0)) + _attr('screenWindowWidth', 'float', struct.pack('<f', 1.0))
              + _attr('nexora/alpha', 'string', (b'premultiplied' if premultiplie and rgba is not None else b'straight'))
              + (_attr('comments', 'string', commentaire.encode()) if commentaire else b'') + b'\0')
    demi = {n: np.ascontiguousarray(canaux[n].astype('<f2')) for n in noms}
    blocs = []
    for y0 in range(0, h, 16):
        y1 = min(h, y0 + 16)
        # une ligne = tous les canaux (dans l'ordre) l'un derrière l'autre
        brut = np.concatenate([demi[n][y].view(np.uint8) for y in range(y0, y1) for n in noms]).tobytes()
        arr = np.frombuffer(brut, np.uint8)
        t = np.concatenate([arr[0::2], arr[1::2]])  # réordonne : octets pairs puis impairs
        p = t.copy()
        p[1:] = ((t[1:].astype(np.int16) - t[:-1].astype(np.int16) + 128) & 0xFF).astype(np.uint8)  # prédicteur
        comp = zlib.compress(p.tobytes(), 4)
        if len(comp) >= len(brut):
            comp = brut  # non compressible : stocké tel quel (le décodeur compare les tailles)
        blocs.append(struct.pack('<ii', y0, len(comp)) + comp)
    debut = len(_MAGIE) + 4 + len(entete) + 8 * len(blocs)
    table, pos = b'', debut
    for b in blocs:
        table += struct.pack('<Q', pos)
        pos += len(b)
    with open(chemin, 'wb') as f:
        f.write(_MAGIE + struct.pack('<I', 2) + entete + table + b''.join(blocs))


def lire_exr(chemin: str) -> dict:
    """Relit un EXR écrit par `ecrire_exr` : retourne {'canaux': {nom: float32 H×W}, 'bits': {nom: 16|32}, 'alpha': str}.

    Décodeur volontairement limité (ZIP16 ou non compressé, scanlines) : il sert à vérifier nos fichiers ;
    les tests recoupent avec la bibliothèque OpenEXR officielle quand elle est installée.
    """
    d = open(chemin, 'rb').read()
    if d[:4] != _MAGIE:
        raise ValueError('EXR invalide')
    i, attrs = 8, {}
    while d[i] != 0:
        j = d.index(b'\0', i)
        nom = d[i:j].decode()
        k = d.index(b'\0', j + 1)
        typ = d[j + 1:k].decode()
        n = struct.unpack('<i', d[k + 1:k + 5])[0]
        attrs[nom] = (typ, d[k + 5:k + 5 + n])
        i = k + 5 + n
    i += 1
    x0, y0, x1, y1 = struct.unpack('<iiii', attrs['dataWindow'][1])
    w, h = x1 - x0 + 1, y1 - y0 + 1
    ch, c = [], attrs['channels'][1]
    while c[0] != 0:
        j = c.index(b'\0')
        nom = c[:j].decode()
        typ = struct.unpack('<i', c[j + 1:j + 5])[0]
        ch.append((nom, typ))
        c = c[j + 1 + 16:]
    comp = attrs['compression'][1][0]
    lignes = 16 if comp == _COMPRESSION_ZIP16 else 1
    nb = (h + lignes - 1) // lignes
    offsets = struct.unpack('<%dQ' % nb, d[i:i + 8 * nb])
    taille_px = {0: 4, 1: 2, 2: 4}
    sortie = {n: np.zeros((h, w), np.float32) for n, _ in ch}
    for b, off in enumerate(offsets):
        y, taille = struct.unpack('<ii', d[off:off + 8])
        data = d[off + 8:off + 8 + taille]
        nl = min(lignes, h - y)
        attendu = nl * w * sum(taille_px[t] for _, t in ch)
        if comp == _COMPRESSION_ZIP16 and taille != attendu:
            p = np.frombuffer(zlib.decompress(data), np.uint8).astype(np.int64)
            out = np.empty_like(p)  # inverse du prédicteur : somme cumulée modulo 256
            out[0] = p[0]
            out[1:] = (p[0] + np.cumsum(p[1:] - 128)) & 0xFF
            raw = np.empty(len(out), np.uint8)
            moitie = (len(out) + 1) // 2
            raw[0::2] = out[:moitie]
            raw[1::2] = out[moitie:]
            data = raw.tobytes()
        pos = 0
        for yy in range(nl):
            for nom, typ in ch:
                taille_l = w * taille_px[typ]
                dt = '<f2' if typ == 1 else '<f4'
                sortie[nom][y + yy] = np.frombuffer(data[pos:pos + taille_l], dt)
                pos += taille_l
    return {'canaux': sortie, 'bits': {n: (16 if t == 1 else 32) for n, t in ch},
            'alpha': attrs.get('nexora/alpha', ('', b''))[1].decode(), 'taille': (w, h)}
