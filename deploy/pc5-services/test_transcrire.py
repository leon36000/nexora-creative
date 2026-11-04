"""Essai du point /transcrire avec un faux modèle (sans GPU). Lancer : python test_transcrire.py"""
import io, os, struct, tempfile, threading, time, types, sys
sys.modules.setdefault("faster_whisper", types.SimpleNamespace(WhisperModel=object))
jeton = tempfile.NamedTemporaryFile("w", delete=False); jeton.write("secret-essai\n"); jeton.close()
os.environ["NEXORA_TRANSCRIRE_JETON_FICHIER"] = jeton.name
os.environ["NEXORA_TRANSCRIRE_TAILLE_MAX"] = "200000"
os.environ["NEXORA_TRANSCRIRE_DUREE_MAX_S"] = "5"
from fastapi import FastAPI
from fastapi.testclient import TestClient
import transcrire_endpoint as te

class Mot: word, start, end = " Bonjour. ", 0.1, 1.2
class Seg: text, start, end, words = " Bonjour. ", 0.1, 1.2, [Mot]
class Faux:
    def transcribe(self, audio, **kw):
        assert kw["word_timestamps"] and kw["language"] == "fr"
        return [Seg], types.SimpleNamespace(language="fr")
app, LAST = FastAPI(), [0]
te.installer(app, lambda cle, f: Faux(), threading.Lock(), LAST)
c = TestClient(app)

def wav(s):
    n = 16000 * s
    return b"RIFF" + struct.pack("<I", 36 + 2 * n) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, 16000, 32000, 2, 16) + b"data" + struct.pack("<I", 2 * n) + b"\0\0" * n

def post(h=None, data=None, lang="fr"):
    return c.post("/transcrire", files={"file": ("a.wav", data if data is not None else wav(1), "audio/wav")}, data={"language": lang}, headers=h or {})

ok = {"Authorization": "Bearer secret-essai"}
assert post().status_code == 401
assert post({"Authorization": "Bearer faux"}).status_code == 401
assert post({"Authorization": "secret-essai"}).status_code == 401
r = post(ok); assert r.status_code == 200, r.text
assert r.json() == {"langue": "fr", "phrases": [{"texte": "Bonjour.", "debutS": 0.1, "finS": 1.2, "mots": [{"mot": "Bonjour.", "debutS": 0.1, "finS": 1.2}]}]}, r.json()
assert post(ok, data=b"\0" * 300000).status_code == 413          # trop gros
assert post(ok, data=wav(7)[:199000]).status_code in (413, 422)  # trop long ou tronqué
assert post(ok, data=b"pas un wav").status_code == 422
assert post(ok, lang="../../etc/passwd").status_code == 422
os.environ["NEXORA_TRANSCRIRE_JETON_FICHIER"] = "/inexistant"; te.FICHIER_JETON = "/inexistant"
assert post(ok).status_code == 503                                # fermé sans jeton configuré
os.unlink(jeton.name); print("OK")
