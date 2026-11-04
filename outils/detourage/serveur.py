"""
Serveur de détourage vidéo de Nexora Creative (HTTP, stdlib + torch). Un processus par machine GPU ; le serveur de
Creative le pilote comme un moteur : il envoie la source, lance, interroge la progression, annule, récupère les fichiers.

  GET    /sante                              modèles chargés, mémoire GPU, travaux en cours
  POST   /segmenter                          aperçu interactif d'une image : {image_b64, points:[[x,y,l]], boite?} (x, y en 0..1)
  PUT    /travaux/<id>/fichiers/<nom>        dépose un fichier (source, fond)
  POST   /travaux/<id>/lancer                {params} ; reprend ce qui est déjà fait dans le dossier
  GET    /travaux/<id>                       état, progression, mesures
  POST   /travaux/<id>/annuler
  GET    /travaux/<id>/sorties/<chemin>      télécharge (Range géré)
  DELETE /travaux/<id>                       supprime tout le dossier (nettoyage)

Variables : NEXORA_DETOURAGE_DOSSIER (travaux), NEXORA_DETOURAGE_POIDS, NEXORA_DETOURAGE_PORT, FFMPEG_BIN,
NEXORA_DETOURAGE_HOTE (une ou plusieurs adresses d'écoute séparées par des virgules ; 127.0.0.1 par défaut),
NEXORA_DETOURAGE_JETON_FICHIER (fichier du jeton partagé, mode 600 ; exigé dès qu'une adresse n'est pas locale),
NEXORA_DETOURAGE_AUTORISES (adresses ou réseaux clients autorisés, ex. « 192.168.1.122 » ; exigé de même),
NEXORA_DETOURAGE_SOCKET (prise Unix d'administration locale, mode 600 : contrôles et bancs sur la machine même ; la
liste d'adresses ne s'y applique pas, le jeton si).

Protection : chaque requête doit venir d'une adresse autorisée (sinon 403) et porter « Authorization: Bearer <jeton> »
(sinon 401), comparé en temps constant. Le jeton n'est jamais journalisé ni renvoyé.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn, UnixStreamServer
from urllib.parse import unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser('~/nexora-creative-data/models/detourage/pylibs')) if os.path.isdir(os.path.expanduser('~/nexora-creative-data/models/detourage/pylibs')) else None

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from acces import Acces  # noqa: E402
from modeles import Modeles  # noqa: E402
from traitement import Tache, regler, sonder  # noqa: E402

DOSSIER = os.environ.get('NEXORA_DETOURAGE_DOSSIER') or os.path.expanduser('~/nexora-creative-data/work/detourage')
HOTES = [h.strip() for h in (os.environ.get('NEXORA_DETOURAGE_HOTE') or '127.0.0.1').split(',') if h.strip()]
acces = Acces.depuis_env(HOTES)  # refuse de démarrer si l'écoute réseau n'est pas protégée
ID = re.compile(r'^[a-zA-Z0-9_-]{6,64}$')
NOM = re.compile(r'^[a-zA-Z0-9._-]{1,80}$')
os.makedirs(DOSSIER, exist_ok=True)

modeles = Modeles()
file_gpu = threading.Semaphore(1)  # un travail à la fois sur ce GPU ; les suivants attendent
travaux: dict[str, dict] = {}  # id -> {'annule': Event, 'fil': Thread}


def chemin(id_: str, *sous: str) -> str:
    return os.path.join(DOSSIER, id_, *sous)


def lire_etat(id_: str) -> dict | None:
    try:
        return json.load(open(chemin(id_, 'etat.json')))
    except (OSError, ValueError):
        return None


def lancer_travail(id_: str, params: dict):
    ev = threading.Event()

    def corps():
        with file_gpu:
            if ev.is_set():
                json.dump({'etat': 'annule', 'etape': 'attente', 'progression': 0, 'message': 'annulé'}, open(chemin(id_, 'etat.json'), 'w'))
                return
            Tache(chemin(id_), modeles, params, ev.is_set).executer()

    json.dump({'etat': 'en_attente', 'etape': 'attente', 'progression': 0, 'message': 'en file'}, open(chemin(id_, 'etat.json'), 'w'))
    th = threading.Thread(target=corps, daemon=True, name=f'detourage-{id_}')
    travaux[id_] = {'annule': ev, 'fil': th}
    th.start()


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server_version = 'nexora-detourage/1'

    def address_string(self):
        return 'unix' if self._unix() else self.client_address[0]

    def _unix(self) -> bool:
        return isinstance(self.server, ServeurUnix)

    def log_message(self, fmt, *a):  # journal sobre, jamais de contenu
        sys.stderr.write('[detourage] %s\n' % (fmt % a))

    def _json(self, code: int, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _corps(self) -> bytes:
        n = int(self.headers.get('Content-Length') or 0)
        return self.rfile.read(n) if n else b''

    def _route(self):
        return [unquote(x) for x in urlparse(self.path).path.strip('/').split('/') if x]

    def _refuse(self) -> bool:
        """Adresse puis jeton, avant toute lecture du corps ; la connexion est fermée en cas de refus."""
        if self._unix():  # accès réservé au propriétaire du fichier de la prise : seul le jeton est vérifié
            code = 0 if acces.jeton_valide(self.headers.get('Authorization')) else 401
        else:
            code = acces.verifier(self.client_address[0], self.headers.get('Authorization'))
        if not code:
            return False
        self.close_connection = True
        b = json.dumps({'erreur': 'adresse non autorisée' if code == 403 else 'jeton manquant ou invalide'}, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Connection', 'close')
        if code == 401:
            self.send_header('WWW-Authenticate', 'Bearer')
        self.end_headers()
        self.wfile.write(b)
        return True

    def do_GET(self):
        if self._refuse():
            return
        r = self._route()
        if r == ['sante']:
            return self._json(200, {'ok': True, 'modeles': modeles.etat(), 'travaux_en_cours': [k for k, v in travaux.items() if v['fil'].is_alive()],
                                    'version': 1})
        if len(r) == 2 and r[0] == 'travaux' and ID.match(r[1]):
            e = lire_etat(r[1])
            return self._json(200, e) if e else self._json(404, {'erreur': 'travail inconnu'})
        if len(r) >= 4 and r[0] == 'travaux' and r[2] == 'sorties' and ID.match(r[1]):
            rel = os.path.normpath('/'.join(r[3:]))
            base = os.path.realpath(chemin(r[1], 'sorties'))
            m = re.match(r'^(alpha|rgba16|exr|alpha_exr)\.zip$', rel)
            if m and os.path.isdir(os.path.join(base, m.group(1))) and not os.path.exists(os.path.join(base, rel)):
                import zipfile  # séquence d'images -> archive sans recompression (PNG et EXR sont déjà compressés)
                with zipfile.ZipFile(os.path.join(base, rel) + '.part', 'w', zipfile.ZIP_STORED) as z:
                    for nom in sorted(os.listdir(os.path.join(base, m.group(1)))):
                        z.write(os.path.join(base, m.group(1), nom), nom)
                os.replace(os.path.join(base, rel) + '.part', os.path.join(base, rel))
            f = os.path.realpath(os.path.join(base, rel))
            if not f.startswith(base + os.sep) or not os.path.isfile(f):
                return self._json(404, {'erreur': 'fichier inconnu'})
            return self._envoyer(f)
        self._json(404, {'erreur': 'route inconnue'})

    def _envoyer(self, f: str):
        taille = os.path.getsize(f)
        debut, fin, code = 0, taille - 1, 200
        m = re.match(r'bytes=(\d*)-(\d*)', self.headers.get('Range') or '')
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                debut = int(m.group(1))
                fin = int(m.group(2)) if m.group(2) else taille - 1
            else:
                debut = max(0, taille - int(m.group(2)))
            fin = min(fin, taille - 1)
            code = 206
        ext = os.path.splitext(f)[1].lower()
        typ = {'.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime', '.png': 'image/png', '.exr': 'image/x-exr',
               '.json': 'application/json', '.jpg': 'image/jpeg'}.get(ext, 'application/octet-stream')
        self.send_response(code)
        self.send_header('Content-Type', typ)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(fin - debut + 1))
        if code == 206:
            self.send_header('Content-Range', f'bytes {debut}-{fin}/{taille}')
        self.end_headers()
        with open(f, 'rb') as fh:
            fh.seek(debut)
            restant = fin - debut + 1
            while restant > 0:
                b = fh.read(min(1 << 20, restant))
                if not b:
                    break
                self.wfile.write(b)
                restant -= len(b)

    def do_PUT(self):
        if self._refuse():
            return
        r = self._route()
        if len(r) == 4 and r[0] == 'travaux' and r[2] == 'fichiers' and ID.match(r[1]) and NOM.match(r[3]):
            os.makedirs(chemin(r[1]), exist_ok=True)
            n, restant = int(self.headers.get('Content-Length') or 0), 0
            cible = chemin(r[1], r[3])
            with open(cible + '.part', 'wb') as fh:
                restant = n
                while restant > 0:
                    b = self.rfile.read(min(1 << 20, restant))
                    if not b:
                        break
                    fh.write(b)
                    restant -= len(b)
            if restant:
                os.remove(cible + '.part')
                return self._json(400, {'erreur': 'envoi interrompu'})
            os.replace(cible + '.part', cible)
            info = None
            if r[3] == 'source.mp4':
                try:
                    info = sonder(cible)
                except Exception as e:  # noqa: BLE001 - un fichier illisible est refusé tout de suite
                    os.remove(cible)
                    return self._json(400, {'erreur': f'vidéo illisible : {e}'})
            return self._json(200, {'ok': True, 'octets': n, 'info': info})
        self._json(404, {'erreur': 'route inconnue'})

    def do_POST(self):
        if self._refuse():
            return
        r = self._route()
        try:
            corps = json.loads(self._corps() or b'{}')
        except ValueError:
            return self._json(400, {'erreur': 'JSON invalide'})
        if r == ['segmenter']:
            try:
                im = cv2.imdecode(np.frombuffer(base64.b64decode(corps['image_b64']), np.uint8), cv2.IMREAD_COLOR)
                if im is None:
                    raise ValueError('image illisible')
                rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
                g = {'points': corps.get('points') or [], 'boite': corps.get('boite')}
                if not g['points'] and not g['boite']:
                    raise ValueError('au moins un clic ou une boîte')
                t = time.time()  # pas de file : l'aperçu d'une image s'intercale avec un travail en cours
                proba, score = modeles.masque_image(rgb, g, corps.get('sam') or 'large')
                ok, png = cv2.imencode('.png', np.rint(proba.astype(np.float32) * 255).astype(np.uint8))
                return self._json(200, {'masque_b64': base64.b64encode(png.tobytes()).decode(), 'score': round(score, 2),
                                        'aire': round(float((proba > 0.5).mean()), 4), 'secondes': round(time.time() - t, 2),
                                        'largeur': rgb.shape[1], 'hauteur': rgb.shape[0]})
            except (KeyError, ValueError) as e:
                return self._json(400, {'erreur': str(e)})
        if len(r) == 3 and r[0] == 'travaux' and ID.match(r[1]):
            id_ = r[1]
            if r[2] == 'lancer':
                if id_ in travaux and travaux[id_]['fil'].is_alive():
                    return self._json(409, {'erreur': 'déjà en cours'})
                if not os.path.exists(chemin(id_, regler(corps.get('params')).get('source', 'source.mp4'))):
                    return self._json(400, {'erreur': 'source absente : dépose-la d’abord'})
                lancer_travail(id_, corps.get('params') or {})
                return self._json(202, {'ok': True})
            if r[2] == 'annuler':
                t = travaux.get(id_)
                if t:
                    t['annule'].set()
                return self._json(200, {'ok': True})
        self._json(404, {'erreur': 'route inconnue'})

    def do_DELETE(self):
        if self._refuse():
            return
        r = self._route()
        if len(r) == 2 and r[0] == 'travaux' and ID.match(r[1]):
            t = travaux.get(r[1])
            if t and t['fil'].is_alive():
                t['annule'].set()
                t['fil'].join(timeout=30)
            travaux.pop(r[1], None)
            shutil.rmtree(chemin(r[1]), ignore_errors=True)
            return self._json(200, {'ok': True})
        self._json(404, {'erreur': 'route inconnue'})


class ServeurUnix(ThreadingMixIn, UnixStreamServer):
    daemon_threads = True

    def get_request(self):
        r, _ = super().get_request()
        return r, ('unix', 0)


def serveur_unix(chemin_prise: str) -> ServeurUnix:
    if os.path.exists(chemin_prise):
        os.remove(chemin_prise)
    ancien = os.umask(0o177)  # la prise naît en mode 600
    try:
        return ServeurUnix(chemin_prise, H)
    finally:
        os.umask(ancien)


def main():
    port = int(os.environ.get('NEXORA_DETOURAGE_PORT') or 8231)
    # au redémarrage, un travail resté « en_cours » n'a plus de processus : on le marque pour qu'il soit relancé (reprise)
    for d in os.listdir(DOSSIER):
        e = lire_etat(d)
        if e and e.get('etat') in ('en_cours', 'en_attente'):
            e.update(etat='interrompu', message='serveur redémarré : relance pour reprendre')
            json.dump(e, open(chemin(d, 'etat.json'), 'w'))
    serveurs = [ThreadingHTTPServer((h, port), H) for h in HOTES]
    prise = (os.environ.get('NEXORA_DETOURAGE_SOCKET') or '').strip()
    if prise:
        serveurs.append(serveur_unix(prise))
    print(f'[detourage] écoute {",".join(HOTES)} port {port}{" + prise unix" if prise else ""}, dossier {DOSSIER}, {acces.resume()}, {modeles.etat()}', flush=True)
    for s in serveurs[1:]:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    serveurs[0].serve_forever()


if __name__ == '__main__':
    main()
