"""Cycle de réponse ASGI de l'encodeur, uniquement médias et processus factices."""
import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request
import test_encoder
import encoder_endpoint as ep


def requete(media=b'VIDEO'):
    corps = (b'--fixture\r\nContent-Disposition: form-data; name="files"; filename="a.mp4"\r\nContent-Type: video/mp4\r\n\r\n' + media + b'\r\n--fixture--\r\n')
    scope = {'type': 'http', 'asgi': {'spec_version': '2.4'}, 'method': 'POST', 'path': '/encoder', 'headers': [
        (b'authorization', b'Bearer jeton-test-encoder'),
        (b'content-type', b'multipart/form-data; boundary=fixture'),
        (b'content-length', str(len(corps)).encode())]}
    async def recevoir():
        return {'type': 'http.request', 'body': corps, 'more_body': False}
    return Request(scope, recevoir), scope


class FluxASGI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.banc = test_encoder.Encoder()
        self.banc.setUp()
        self.endpoint = next(r.endpoint for r in self.banc.app.routes if getattr(r, 'path', None) == '/encoder')

    def tearDown(self):
        self.banc.tearDown()

    def verifier_verrous(self):
        self.assertTrue(ep.VERROU.acquire(blocking=False))
        ep.VERROU.release()
        fd = ep.admettre_essai()
        ep.os.close(fd)

    async def verifier_envoi(self, mode):
        req, scope = requete()
        admission, fermer = ep.admettre_essai, ep.os.close
        fds, fermetures = [], []
        def admettre():
            fd = admission(); fds.append(fd); return fd
        def fermer_fd(fd):
            if fds and fd == fds[0]: fermetures.append(fd)
            return fermer(fd)
        with patch.object(ep, 'admettre_essai', admettre), patch.object(ep.os, 'close', fermer_fd):
            response = await self.endpoint(req)
            self.assertEqual(fermetures, [fds[0]])
        self.verifier_verrous()
        travaux = [p for p in ep.Path(ep.RACINE).iterdir() if p.is_dir()]
        self.assertEqual((travaux[0] / 'entree-0').read_bytes(), b'VIDEO')
        self.assertEqual((travaux[0] / 'sortie.mp4').read_bytes(), b'ENCODE-H264VIDEO')
        self.assertGreaterEqual(ep.taille_essais(ep.RACINE), len(b'VIDEO') + len(b'ENCODE-H264VIDEO'))
        self.assertEqual(self.banc.post(media=b'VIDEO2').status_code, 200)
        if mode:
            async def recevoir(): return {'type': 'http.disconnect'}
            async def envoyer(message):
                if message['type'] == mode: raise OSError('erreur ASGI factice')
            with self.assertRaises(Exception):
                await response(scope, recevoir, envoyer)
        self.verifier_verrous()

    async def test_reponse_jamais_appelee(self):
        await self.verifier_envoi(None)

    async def test_erreur_envoi_entete(self):
        await self.verifier_envoi('http.response.start')

    async def test_erreur_envoi_corps(self):
        await self.verifier_envoi('http.response.body')

    async def test_encodage_serialise(self):
        demarre, continuer = asyncio.Event(), asyncio.Event()
        programme = ep.programme
        async def suspendre(args, **kwargs):
            if args[0] == ep.FFMPEG and args[-1] != '-':
                demarre.set(); await continuer.wait()
            return await programme(args, **kwargs)
        with patch.object(ep, 'programme', suspendre):
            task = asyncio.create_task(self.endpoint(requete()[0]))
            await asyncio.wait_for(demarre.wait(), 5)
            try:
                with self.assertRaises(HTTPException) as err: await self.endpoint(requete()[0])
                self.assertEqual(err.exception.status_code, 429)
            finally:
                continuer.set()
                await task
        self.verifier_verrous()

    async def test_echec_encodage(self):
        self.assertEqual(self.banc.post(media=b'ECHEC').status_code, 422)
        self.verifier_verrous()
        self.assertEqual(self.banc.post(media=b'VIDEO2').status_code, 200)

    async def test_erreur_close(self):
        admission, fermer = ep.admettre_essai, ep.os.close
        fds, fermetures = [], []
        def admettre():
            fd = admission(); fds.append(fd); return fd
        def fermer_fd(fd):
            if fds and fd == fds[0]:
                fermetures.append(fd); fermer(fd); raise OSError('fixture close')
            return fermer(fd)
        with patch.object(ep, 'admettre_essai', admettre), patch.object(ep.os, 'close', fermer_fd):
            with self.assertRaises(HTTPException) as err: await self.endpoint(requete()[0])
            self.assertEqual(err.exception.status_code, 503)
        self.assertEqual(fermetures, [fds[0]])
        self.verifier_verrous()

    async def test_quota_et_erreur_fermeture_reception(self):
        await self.endpoint(requete()[0])
        taille, plafond = ep.taille_essais(ep.RACINE), ep.PLAFOND_ESSAIS
        try:
            ep.PLAFOND_ESSAIS = str(2 * ep.TAILLE_MAX + taille - 1)
            self.assertEqual(self.banc.post(media=b'VIDEO2').status_code, 507)
        finally:
            ep.PLAFOND_ESSAIS = plafond
        with patch.object(ep.Reception, 'fermer', side_effect=OSError('fixture réception')):
            with self.assertRaises(OSError): await self.endpoint(requete(b'ECHEC')[0])
        self.verifier_verrous()
        self.assertEqual(self.banc.post(media=b'VIDEO3').status_code, 200)


if __name__ == '__main__':
    unittest.main()
