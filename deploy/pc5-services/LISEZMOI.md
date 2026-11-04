# Transcription GPU du Mode Studio (VM 204)
Ces fichiers n’ont PAS été appliqués en production.
`service.py` est une référence minimale ; conserver le service existant de la VM 204.
Copier `transcrire_endpoint.py` à côté du `service.py` existant (FastAPI, python-multipart, NumPy, faster-whisper et ffmpeg requis).
Ajouter `from transcrire_endpoint import installer` aux imports de ce service.
Après la création de CACHE, LOCK, LAST et la définition de charge, ajouter `installer(app, charge, LOCK, LAST)`.
Le contrat de référence utilise `LAST["stt"]` pour l’horodatage de dernière utilisation, sous LOCK.
Activer ensuite avec `sudo systemctl restart nexora-services` sur la VM 204.
Côté Creative, définir `NEXORA_TRANSCRIPTION_URL=http://192.168.1.124:8190` pour essayer le GPU avec repli CPU.
