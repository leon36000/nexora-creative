#!/usr/bin/env python3
"""Pont Unix limité aux messages : la clé de la passerelle reste côté hôte."""
from __future__ import annotations

import http.client
import json
import os
import secrets
import socketserver
import stat
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler
from decimal import Decimal, DecimalException
from urllib.parse import urlsplit

from cost_snapshot import snapshot_wait as cost_snapshot_wait

def trace_erreur(phase, erreur=None):
    """Ne conserve que la phase et un errno numérique, sans message ni données HTTP."""
    numero = getattr(erreur, 'errno', None)
    if type(numero) is not int or not 0 <= numero <= 4095:
        numero = None
    try:
        print(json.dumps({'evenement': 'proxy_erreur', 'phase': phase, 'errno': numero}), file=sys.stderr, flush=True)
    except OSError:
        pass


MAX_BODY = 16 * 1024 * 1024
MAX_OUTPUT_TOKENS = 16000
ALLOWED_PATHS = frozenset(('/v1/messages',))
UNTRACKED_COUNT_PATH = '/v1/messages/count_tokens'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def __init__(self, path, handler, *, key, run, model, port, timeout, audit_path, ledger_path, budget,
                 client_timeout=30, max_workers=4, ledger_wait=3):
        self.key, self.run, self.model, self.port, self.upstream_timeout = key, run, model, port, timeout
        self.client_timeout, self.audit_path, self.ledger_path = client_timeout, audit_path, ledger_path
        self.budget, self.ledger_wait = budget, ledger_wait
        self._slots = threading.BoundedSemaphore(max_workers)
        self._forward_lock = threading.Lock()
        self._audit_fd = os.open(audit_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
        self._sequence = 0
        self._nonce = secrets.token_hex(8)
        ouvert = False
        try:
            super().__init__(path, handler)
            ouvert = True
            os.chmod(path, 0o600)
        except BaseException:
            if ouvert:
                self.server_close()
            else:
                self._close_audit()
            raise

    def budget_status(self):
        # Every prior forwarding attempt must have an exact ledger match before another starts.
        while True:
            try:
                result = cost_snapshot_wait(self.ledger_path, self.audit_path, self.run, self.ledger_wait)
                spent = Decimal(result['spent'])
                return 'limite' if spent >= self.budget else 'ok'
            except Exception:
                return 'inconnu'

    def record_attempt(self):
        sequence = self._sequence + 1
        tag = f'{self.run}--p{self._nonce}--c{sequence}'
        data = (json.dumps({'sequence': sequence, 'call': tag}) + '\n').encode()
        if os.write(self._audit_fd, data) != len(data):
            raise OSError('journal incomplet')
        self._sequence = sequence
        return tag

    def _close_audit(self):
        fd, self._audit_fd = self._audit_fd, None
        if fd is not None:
            os.close(fd)

    def server_close(self):
        try:
            super().server_close()
        finally:
            self._close_audit()

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(self.client_timeout)
        return connection, address

    def process_request(self, request, address):
        if not self._slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self._slots.release()

    def handle_error(self, _request, _client_address):
        pass  # Never print attacker-controlled headers, payloads, or secrets.


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_args):
        pass  # Never log a prompt, key, URL, header, or upstream error body.

    def reject(self, status, message):
        body = json.dumps({'error': message}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def do_GET(self):
        self.reject(403, 'route interdite')

    def do_POST(self):
        try:
            path = urlsplit(self.path)
        except ValueError:
            self.reject(400, 'route invalide')
            return
        if ((path.path not in ALLOWED_PATHS and path.path != UNTRACKED_COUNT_PATH)
                or path.scheme or path.netloc or path.fragment or path.query not in ('', 'beta=true')):
            self.reject(403, 'route interdite')
            return
        if path.path == UNTRACKED_COUNT_PATH:
            self.reject(501, 'comptage de jetons indisponible sans suivi de coût fiable')
            return
        names = [name.lower() for name, _value in self.headers.raw_items()]
        lengths = self.headers.get_all('Content-Length') or []
        if (len(names) != len(set(names)) or len(lengths) != 1 or len(lengths[0]) > 9
                or not lengths[0].isdigit() or self.headers.get('Transfer-Encoding')):
            self.reject(400, 'longueur invalide')
            return
        length = int(lengths[0])
        if length > MAX_BODY:
            self.reject(413, 'requête trop volumineuse')
            return
        deadline = time.monotonic() + self.server.client_timeout
        parts = []
        remaining = length
        try:
            while remaining:
                seconds = deadline - time.monotonic()
                if seconds <= 0:
                    raise TimeoutError
                self.connection.settimeout(seconds)
                chunk = self.rfile.read1(min(65536, remaining))
                if not chunk:
                    raise EOFError
                parts.append(chunk)
                remaining -= len(chunk)
            self.connection.settimeout(self.server.client_timeout)
        except (OSError, EOFError):
            self.close_connection = True
            return
        body = b''.join(parts)
        try:
            request = json.loads(body, object_pairs_hook=unique_object)
        except (UnicodeError, ValueError, RecursionError):
            self.reject(400, 'requête invalide')
            return
        if len(body) != length or not isinstance(request, dict) or request.get('model') != self.server.model:
            self.reject(403, 'modèle non autorisé')
            return
        tokens = request.get('max_tokens')
        if type(tokens) is not int or not 1 <= tokens <= MAX_OUTPUT_TOKENS:
            self.reject(400, 'limite de jetons invalide')
            return
        allowed = {'content-type', 'accept', 'anthropic-version', 'anthropic-beta', 'user-agent', 'x-app'}
        headers = {key: value for key, value in self.headers.items()
                   if key.lower() in allowed or key.lower().startswith('x-stainless-')}
        headers.update({'Host': f'127.0.0.1:{self.server.port}', 'Content-Length': str(length),
                        'Accept-Encoding': 'identity', 'x-api-key': self.server.key,
                        'x-sa-run': self.server.run})
        # Do not let an incomplete client body lock out valid requests.
        if not self.server._forward_lock.acquire(blocking=False):
            self.reject(429, 'un seul appel à la fois')
            return
        try:
            self.dispatch(body, headers)
        finally:
            self.server._forward_lock.release()

    def dispatch(self, body, headers):
        budget = self.server.budget_status()
        if budget != 'ok':
            self.reject(429 if budget == 'limite' else 503,
                        'budget atteint' if budget == 'limite' else 'coût précédent inconnu')
            return
        connection = http.client.HTTPConnection('127.0.0.1', self.server.port, timeout=self.server.upstream_timeout)
        try:
            # Une connexion refusée avant tout envoi HTTP ne peut pas avoir atteint le fournisseur.
            connection.connect()
        except (OSError, http.client.HTTPException, ValueError) as exc:
            trace_erreur('connexion', exc)
            connection.close()
            self.reject(502, 'passerelle indisponible')
            return
        try:
            # Dès que l'envoi est possible, conserver toute issue ambiguë dans l'audit.
            headers['x-sa-run'] = self.server.record_attempt()
        except OSError:
            connection.close()
            self.reject(503, 'journal indisponible')
            return
        try:
            connection.request('POST', self.path, body=body, headers=headers)
            response = connection.getresponse()
        except (OSError, http.client.HTTPException, ValueError) as exc:
            trace_erreur('envoi_ou_reponse', exc)
            connection.close()
            self.reject(502, 'passerelle indisponible')
            return
        try:
            encoding = response.getheader('Content-Encoding', 'identity').lower()
            if encoding not in ('', 'identity'):
                trace_erreur('reponse_invalide')
                self.reject(502, 'réponse encodée non vérifiable')
                return
            lengths = response.headers.get_all('Content-Length') or []
            if len(lengths) > 1 or (lengths and not lengths[0].isdigit()):
                trace_erreur('reponse_invalide')
                self.reject(502, 'longueur amont invalide')
                return
            expected = int(lengths[0]) if lengths else None
            if response.status == 502:
                trace_erreur('reponse_amont_502')
            self.send_response(response.status)
            for key, value in response.getheaders():
                lower = key.lower()
                if lower in {'content-type', 'retry-after', 'request-id'} or lower.startswith(('x-ratelimit-', 'anthropic-ratelimit-')):
                    self.send_header(key, value.replace(self.server.key, '[redacted]'))
            # Only send the terminating chunk after a complete upstream response.
            self.send_header('Transfer-Encoding', 'chunked')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True

            def emit(data):
                if data:
                    self.wfile.write(f'{len(data):x}\r\n'.encode() + data + b'\r\n')
                    self.wfile.flush()

            secret = self.server.key.encode()
            pending = b''
            received = 0
            while True:
                chunk = response.read1(8192)
                if not chunk:
                    break
                received += len(chunk)
                pending = (pending + chunk).replace(secret, b'[redacted]')
                hold = min(len(secret) - 1, len(pending))
                while hold and not pending.endswith(secret[:hold]):
                    hold -= 1
                ready = pending[:-hold] if hold else pending
                pending = pending[-hold:] if hold else b''
                emit(ready)
            if expected is not None and received != expected:
                return  # Missing terminal chunk makes upstream truncation observable.
            emit(pending)
            self.wfile.write(b'0\r\n\r\n')
            self.wfile.flush()
        except (OSError, http.client.HTTPException):
            pass  # Close without a terminal chunk if streaming fails.
        finally:
            connection.close()

    def do_PUT(self):
        self.reject(403, 'route interdite')

    def do_DELETE(self):
        self.reject(403, 'route interdite')


def main():
    if len(sys.argv) != 2:
        return 2
    try:
        info = os.fstat(3)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            return 2
        raw = os.read(3, 4097)
        os.close(3)
        if len(raw) > 4096:
            return 2
        key = raw.decode('utf-8').strip()
    except (OSError, UnicodeError):
        return 2
    run = os.environ.pop('SA_PROXY_RUN', '')
    model = os.environ.pop('SA_PROXY_MODEL', '')
    audit = os.environ.pop('SA_PROXY_AUDIT', '')
    ledger = os.environ.pop('SA_PROXY_LEDGER', '')
    try:
        port = int(os.environ.pop('SA_PROXY_PORT', ''))
        timeout = int(os.environ.pop('SA_PROXY_TIMEOUT', '900'))
        budget = Decimal(os.environ.pop('SA_PROXY_BUDGET', ''))
        ledger_wait = Decimal(os.environ.pop('SA_PROXY_LEDGER_WAIT', '3'))
    except (ValueError, DecimalException):
        return 2
    if (not key or not run or not model or not audit or not os.path.isabs(audit)
            or not ledger or not os.path.isabs(ledger) or not budget.is_finite() or budget <= 0
            or not ledger_wait.is_finite() or not 0 <= ledger_wait <= 60
            or not 1 <= port <= 65535 or timeout <= 0):
        return 2
    os.umask(0o077)
    try:
        with Server(sys.argv[1], Handler, key=key, run=run, model=model, port=port, timeout=timeout,
                    audit_path=audit, ledger_path=ledger, budget=budget, ledger_wait=float(ledger_wait)) as server:
            os.chmod(sys.argv[1], 0o600)
            # Le propriétaire du run peut demander l'arrêt sans envoyer de signal.
            # Le dossier d'audit n'est pas exposé à la sandbox du client.
            stop = os.path.join(os.path.dirname(audit), 'proxy-stop')
            server.timeout = 0.2
            while not os.path.exists(stop):
                server.handle_request()
    except OSError:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
