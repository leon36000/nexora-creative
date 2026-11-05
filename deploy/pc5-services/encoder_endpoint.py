"""Encodage NVENC borné, sans modèle ni chemin/filtre fourni par le client.

Le corps multipart est consommé en flux après authentification ; fichiers privés
seekables pour MP4 non fragmenté, sortie MP4 validée avant de commencer la réponse.
Un seul travail (upload compris) par processus ; déployer avec UN worker uvicorn.
"""
import asyncio
import fcntl
import hmac
import json
import math
import os
import shutil
import stat
import sys
import tempfile
import threading
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from python_multipart.multipart import MultipartParser, parse_options_header

FICHIER_JETON = os.environ.get('NEXORA_ENCODER_JETON_FICHIER',
                             os.environ.get('NEXORA_TRANSCRIRE_JETON_FICHIER', '/srv/nexora-gpu/transcrire.token'))
RACINE = os.environ.get('NEXORA_ENCODER_TRAVAUX', '/srv/nexora-gpu/encodages')
FFMPEG = os.environ.get('NEXORA_ENCODER_FFMPEG', 'ffmpeg')
FFPROBE = os.environ.get('NEXORA_ENCODER_FFPROBE', 'ffprobe')
GPU = os.environ.get('NEXORA_ENCODER_GPU', '0')  # index visible ; service audio a CUDA_VISIBLE_DEVICES=1
H264_VALIDE = os.environ.get('NEXORA_ENCODER_H264_VALIDE') == '1'
HEVC_VALIDE = os.environ.get('NEXORA_ENCODER_HEVC_VALIDE') == '1'
TAILLE_MAX = 512 * 2**20
# Limite logique des essais, pas quota de blocs du système de fichiers.
PLAFOND_ESSAIS = os.environ.get('NEXORA_ENCODER_PLAFOND_ESSAIS', str(20 * 2**30))
DUREE_MAX_S = 600
DELAI_S = 180
VERROU = threading.BoundedSemaphore(1)


def taille_essais(racine):
    """Compte prudemment tous les fichiers, sans suivre les liens ni ignorer une erreur."""
    total = 0
    a_visiter = [racine]
    while a_visiter:
        with os.scandir(a_visiter.pop()) as entries:
            for entry in entries:
                st = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(st.st_mode):
                    a_visiter.append(entry.path)
                elif stat.S_ISREG(st.st_mode):
                    total += st.st_size
                else:
                    raise OSError('type de fichier non pris en charge')
    return total


def admettre_essai():
    """Sérialise les admissions des instances coopérantes jusqu'à la fin du travail."""
    Path(RACINE).mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(Path(RACINE)/'.encoder.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise HTTPException(429, 'stockage occupe / storage busy')
        try:
            plafond = int(PLAFOND_ESSAIS)
        except (ValueError, TypeError):
            raise HTTPException(503, 'plafond invalide / invalid storage limit')
        reserve = 2 * TAILLE_MAX
        if plafond < reserve or taille_essais(RACINE) + reserve > plafond:
            raise HTTPException(507, 'plafond des essais atteint / trial storage limit reached')
        if shutil.disk_usage(RACINE).free < reserve + 256*2**20:
            raise HTTPException(507, 'espace insuffisant / insufficient disk space')
        return fd
    except BaseException:
        os.close(fd)
        raise


def verifier_jeton(authorization):
    try:
        attendu = Path(FICHIER_JETON).read_text(encoding='utf-8').strip()
    except OSError:
        attendu = ''
    if not attendu:
        raise HTTPException(503, 'encodage non configure / encoding not configured')
    recu = authorization[7:] if authorization and authorization.startswith('Bearer ') else ''
    if not hmac.compare_digest(recu.encode(), attendu.encode()):
        raise HTTPException(401, 'jeton invalide / invalid token')


async def programme(args, *, sortie=False, limite_fichier=None, verrou_fd=None):
    """Pas de shell ; annulation et délai ne tuent que notre propre enfant."""
    if limite_fichier is not None:
        # La limite est installée avant exec : -fs de ffmpeg seul peut dépasser sa cible.
        args = [sys.executable, '-c', 'import os,resource,sys; n=int(sys.argv[1]); resource.setrlimit(resource.RLIMIT_FSIZE,(n,n)); os.execvp(sys.argv[2],sys.argv[2:])', str(limite_fichier), *args]
    p = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE if sortie else asyncio.subprocess.DEVNULL,
                                             stderr=asyncio.subprocess.DEVNULL, pass_fds=(verrou_fd,) if verrou_fd is not None else ())
    try:
        async with asyncio.timeout(DELAI_S):
            if sortie:
                # ffprobe ne produit que les champs demandés, 17 flux max inspectés.
                data = await p.stdout.read(65537)
                if len(data) > 65536:
                    raise HTTPException(422, 'metadonnees excessives / excessive metadata')
            else:
                data = b''
            if await p.wait() != 0:
                raise HTTPException(422, 'media illisible ou encodeur indisponible / invalid media or encoder unavailable')
            return data
    finally:
        if p.returncode is None:
            p.kill()
            await p.wait()


async def sonder(path):
    try:
        data = await programme([FFPROBE, '-v', 'error', '-protocol_whitelist', 'file,pipe',
                                '-format_whitelist', 'mov,matroska,webm,avi',
                                '-show_entries', 'format=duration,format_name:stream=codec_name,codec_type,width,height,pix_fmt,avg_frame_rate,duration,color_transfer,color_primaries,color_space,channels',
                                '-of', 'json', str(path)], sortie=True)
        obj = json.loads(data)
        streams = obj['streams']
        if len(streams) > 16:
            raise ValueError()
        v = next(s for s in streams if s['codec_type'] == 'video')
        a = next((s for s in streams if s['codec_type'] == 'audio'), None)
        duration = max(float(obj['format']['duration']), float(v.get('duration', 0)))
        num, den = v['avg_frame_rate'].split('/')
        fps = float(num) / float(den)
        if not math.isfinite(duration) or duration <= 0 or duration > DUREE_MAX_S + .05:
            raise HTTPException(413, 'video trop longue / video too long')
        if not 0 < fps <= 60 or not 0 < v['width'] <= 3840 or not 0 < v['height'] <= 3840 or v['width'] * v['height'] > 3840 * 2160:
            raise HTTPException(413, 'dimensions ou cadence excessives / excessive dimensions or frame rate')
        # Ces recettes sont SDR 4:2:0 uniquement ; ne jamais dégrader un maître HDR/alpha/422.
        if v.get('pix_fmt') not in ('yuv420p', 'yuvj420p', 'yuv420p10le', 'nv12', 'p010le') or v.get('color_transfer') in ('smpte2084', 'arib-std-b67'):
            raise HTTPException(422, 'SDR 4:2:0 seulement / SDR 4:2:0 only')
        if a and a.get('channels', 0) > 2:
            raise HTTPException(422, 'audio stereo maximum / stereo audio maximum')
        return {'duree': duration, 'video': v, 'audio': a}
    except (ValueError, KeyError, StopIteration, TypeError, ZeroDivisionError):
        raise HTTPException(422, 'video invalide / invalid video')


def options_valides(raw, count):
    try:
        o = json.loads(raw)
        if not isinstance(o, dict) or set(o) - {'codec', 'profil', 'taille', 'assemblage'}:
            raise ValueError()
        if o.get('codec', 'h264') not in ('h264', 'hevc') or o.get('profil', 'livraison') not in ('livraison', 'apercu'):
            raise ValueError()
        if 'taille' in o:
            w, h = o['taille']
            if type(w) is not int or type(h) is not int or min(w, h) < 64 or max(w, h) > 3840 or w*h > 3840*2160 or w % 2 or h % 2:
                raise ValueError()
        if 'assemblage' in o:
            a = o['assemblage']
            if not isinstance(a, dict) or set(a) != {'transition', 'durees', 'fondu', 'son'}:
                raise ValueError()
            if a['transition'] not in ('coupe', 'fondu') or type(a['son']) is not bool or len(a['durees']) != count:
                raise ValueError()
            ds = a['durees']
            if any(type(d) not in (float, int) or not math.isfinite(d) or d <= 0 or d > DUREE_MAX_S for d in ds):
                raise ValueError()
            f = a['fondu']
            if type(f) not in (int, float) or not math.isfinite(f) or not 0 <= f <= 2:
                raise ValueError()
            if a['transition'] == 'fondu' and (f <= 0 or min(ds) <= 2*f):
                raise ValueError()
            if sum(ds) > DUREE_MAX_S:
                raise HTTPException(413, 'assemblage trop long / assembly too long')
        elif count != 1:
            raise ValueError()
        return o
    except (ValueError, TypeError, KeyError, OverflowError):
        raise HTTPException(422, 'options invalides / invalid options')


class Reception:
    """Parse multipart sans spooling implicite de Starlette, noms ignorés."""
    def __init__(self, boundary, dossier):
        self.dossier, self.files, self.options = dossier, [], b'{}'
        self.total = 0
        self.fini = False
        self.parser = MultipartParser(boundary, {
            'on_part_begin': self.debut, 'on_header_field': self.entete_nom,
            'on_header_value': self.entete_valeur, 'on_header_end': self.entete_fin,
            'on_headers_finished': self.entetes_fin, 'on_part_data': self.donnees,
            'on_part_end': self.fin, 'on_end': self.termine,
        })
        self.fd = None
        self.options_vues = False

    def debut(self):
        self.headers, self.hnom, self.hval, self.part = {}, b'', b'', b''
        self.entete_octets = 0

    def entete_nom(self, d, s, e):
        self.entete_octets += e-s
        if self.entete_octets > 8192:
            raise HTTPException(413, 'entetes excessives / excessive headers')
        self.hnom += d[s:e]

    def entete_valeur(self, d, s, e):
        self.entete_octets += e-s
        if self.entete_octets > 8192:
            raise HTTPException(413, 'entetes excessives / excessive headers')
        self.hval += d[s:e]

    def entete_fin(self):
        self.headers[self.hnom.lower()] = self.hval
        self.hnom, self.hval = b'', b''

    def entetes_fin(self):
        _, params = parse_options_header(self.headers.get(b'content-disposition', b''))
        self.nom = params.get(b'name')
        if self.nom == b'files' and len(self.files) < 16:
            path = self.dossier / f'entree-{len(self.files)}'
            self.files.append(path)
            self.fd = path.open('xb')
        elif self.nom == b'options' and not self.options_vues:
            self.options_vues = True
        else:
            raise HTTPException(422, 'partie inattendue / unexpected part')

    def donnees(self, d, s, e):
        self.total += e-s
        if self.total > TAILLE_MAX:
            raise HTTPException(413, 'fichiers trop volumineux / files too large')
        if self.nom == b'files':
            self.fd.write(d[s:e])
        else:
            if len(self.part) + e-s > 16384:
                raise HTTPException(413, 'options excessives / excessive options')
            self.part += d[s:e]

    def fin(self):
        if self.fd:
            self.fd.close()
            self.fd = None
        else:
            self.options = self.part

    def termine(self):
        self.fini = True

    def fermer(self):
        if self.fd:
            self.fd.close()
            self.fd = None


def commande(files, infos, sortie, o):
    args = [FFMPEG, '-hide_banner', '-v', 'error', '-nostdin', '-y', '-xerror', '-filter_complex_threads', '2']
    for f in files:
        args += ['-threads', '2', '-protocol_whitelist', 'file,pipe', '-format_whitelist', 'mov,matroska,webm,avi', '-i', str(f)]
    size = o.get('taille')
    mise = (f'scale={size[0]}:{size[1]}:force_original_aspect_ratio=increase,crop={size[0]}:{size[1]},' if size else '')
    a = o.get('assemblage')
    if a:
        son = a['son']
        if son and any(not i['audio'] for i in infos):
            raise HTTPException(422, 'piste audio manquante / missing audio stream')
        # Même graphe fixe que film.ts ; aucune expression, URL ou chemin fourni par le client.
        filtres = [f'[{k}:v:0]{mise}setsar=1,fps=24,settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[n{k}]' for k in range(len(files))]
        if son:
            filtres += [f'[{k}:a:0]aresample=48000,asetpts=PTS-STARTPTS[au{k}]' for k in range(len(files))]
        if a['transition'] == 'fondu' and len(files) > 1:
            pv, pa, cumul = 'n0', 'au0', 0
            for k in range(1, len(files)):
                cumul += a['durees'][k-1]
                offset = round(cumul-k*a['fondu'], 3)
                filtres.append(f'[{pv}][n{k}]xfade=transition=fade:duration={a["fondu"]}:offset={offset}[v{k}]')
                pv = f'v{k}'
                if son:
                    filtres.append(f'[{pa}][au{k}]acrossfade=d={a["fondu"]}[a{k}]')
                    pa = f'a{k}'
            video, audio = f'[{pv}]', f'[{pa}]'
        else:
            flux = ''.join(f'[n{k}]'+(f'[au{k}]' if son else '') for k in range(len(files)))
            filtres.append(f'{flux}concat=n={len(files)}:v=1:a={int(son)}[v]'+('[a]' if son else ''))
            video, audio = '[v]', '[a]'
        args += ['-filter_complex', ';'.join(filtres), '-map', video]
        if son:
            args += ['-map', audio]
    else:
        son = bool(infos[0]['audio'])
        args += ['-map', '0:v:0']
        if son:
            args += ['-map', '0:a:0']
        if size:
            args += ['-vf', mise.rstrip(',')+',setsar=1']
    if son:
        args += ['-c:a', 'aac', '-b:a', '128k' if o.get('profil') == 'apercu' else '192k', '-ar', '48000']
    else:
        args += ['-an']
    hevc, preview = o.get('codec') == 'hevc', o.get('profil') == 'apercu'
    codec = 'hevc_nvenc' if hevc else 'h264_nvenc'
    args += ['-c:v', codec, '-gpu', GPU, '-preset', 'p4' if preview else 'p7', '-tune', 'hq',
             '-rc', 'vbr', '-cq', '23' if preview else ('21' if hevc else '19'), '-b:v', '0',
             '-multipass', 'fullres', '-spatial-aq', '1', '-temporal-aq', '1', '-rc-lookahead', '32', '-bf', '3',
             '-pix_fmt', 'p010le' if hevc else 'yuv420p']
    if hevc:
        args += ['-profile:v', 'main10', '-tag:v', 'hvc1']
    args += ['-map_metadata', '-1', '-t', str(DUREE_MAX_S+1), '-fs', str(TAILLE_MAX+1), '-movflags', '+faststart', '-f', 'mp4', str(sortie)]
    return args, codec


def installer(app, verrou_gpu=None):
    """`verrou_gpu` est le verrou du service audio si NVENC partage sa carte."""
    @app.post('/encoder')
    async def encoder(request: Request):
        verifier_jeton(request.headers.get('authorization'))
        if not VERROU.acquire(blocking=False):
            raise HTTPException(429, 'encodeur occupe / encoder busy')
        dossier = None
        verrou_stockage = None
        reception = None
        rendu = False
        try:
            verrou_stockage = admettre_essai()
            dossier = Path(tempfile.mkdtemp(prefix='enc-', dir=RACINE))
            typ, opts = parse_options_header(request.headers.get('content-type', ''))
            boundary = opts.get(b'boundary', b'')
            if typ != b'multipart/form-data' or not 1 <= len(boundary) <= 200:
                raise HTTPException(415, 'multipart attendu / multipart required')
            if int(request.headers.get('content-length', '0')) > TAILLE_MAX + 65536:
                raise HTTPException(413, 'requete trop volumineuse / request too large')
            reception = Reception(boundary, dossier)
            total = 0
            async with asyncio.timeout(60):
                async for chunk in request.stream():
                    total += len(chunk)
                    if total > TAILLE_MAX+65536:
                        raise HTTPException(413, 'requete trop volumineuse / request too large')
                    reception.parser.write(chunk)
            reception.parser.finalize()
            if not reception.fini or not reception.files:
                raise HTTPException(422, 'multipart incomplet / incomplete multipart')
            o = options_valides(reception.options, len(reception.files))
            if (o.get('codec', 'h264') == 'h264' and not H264_VALIDE) or (o.get('codec') == 'hevc' and not HEVC_VALIDE):
                raise HTTPException(503, 'codec en attente du banc qualité / codec awaits quality benchmark')
            infos = [await sonder(f) for f in reception.files]
            if sum(i['duree'] for i in infos) > DUREE_MAX_S+.05:
                raise HTTPException(413, 'assemblage trop long / assembly too long')
            if o.get('assemblage'):
                for d, i in zip(o['assemblage']['durees'], infos):
                    if abs(d-i['duree']) > .5:
                        raise HTTPException(422, 'duree incorrecte / incorrect duration')
            sortie = dossier/'sortie.mp4'
            args, codec = commande(reception.files, infos, sortie, o)
            if verrou_gpu is not None and not verrou_gpu.acquire(blocking=False):
                raise HTTPException(429, 'gpu occupe / GPU busy')
            try:
                await programme(args, limite_fichier=TAILLE_MAX, verrou_fd=verrou_stockage)
            finally:
                if verrou_gpu is not None:
                    verrou_gpu.release()
            if not sortie.exists() or sortie.stat().st_size > TAILLE_MAX:
                raise HTTPException(413, 'sortie trop volumineuse / output too large')
            resultat = await sonder(sortie)
            codec_attendu = 'hevc' if o.get('codec', 'h264') == 'hevc' else 'h264'
            pixel_attendu = 'yuv420p10le' if codec_attendu == 'hevc' else 'yuv420p'
            if resultat['video'].get('codec_name') != codec_attendu or resultat['video'].get('pix_fmt') != pixel_attendu:
                raise HTTPException(422, 'codec ou profondeur de sortie invalide / invalid output codec or bit depth')
            a = o.get('assemblage')
            attendu = sum(i['duree'] for i in infos)
            if a and a['transition'] == 'fondu':
                attendu -= (len(infos)-1)*a['fondu']
            if abs(resultat['duree']-attendu) > .5:
                raise HTTPException(422, 'sortie tronquee / truncated output')
            # Décodage complet : un -fs ou un flux corrompu ne doit pas livrer une vidéo tronquée.
            await programme([FFMPEG, '-v', 'error', '-xerror', '-nostdin', '-threads', '2', '-i', str(sortie), '-map', '0:v:0', '-map', '0:a?', '-f', 'null', '-'])
            async def flux():
                try:
                    with sortie.open('rb') as f:
                        while chunk := f.read(256*1024):
                            yield chunk
                finally:
                    os.close(verrou_stockage)
                    VERROU.release()
            response = StreamingResponse(flux(), media_type='video/mp4', headers={
                'Content-Length': str(sortie.stat().st_size), 'X-Nexora-Encodeur': codec,
                'Content-Disposition': 'attachment; filename="export.mp4"', 'Cache-Control': 'no-store',
            })
            rendu = True
            return response
        except TimeoutError:
            raise HTTPException(504, 'delai depasse / timeout')
        except OSError:
            raise HTTPException(503, 'encodeur indisponible / encoder unavailable')
        except ValueError:
            raise HTTPException(422, 'requete invalide / invalid request')
        finally:
            if reception:
                reception.fermer()
            if not rendu:
                if verrou_stockage is not None:
                    os.close(verrou_stockage)
                VERROU.release()
