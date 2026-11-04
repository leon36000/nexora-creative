# Qui vit où (état du 03/11/2026)

Règles du fondateur : tout ce qui est lourd et n'est pas un modèle ni un moteur GPU vit sur pc5 (Proxmox) ; tout le code est sur GitLab pc4 ; seuls les modèles restent sur pc1 et pc6.

## Produits

| Produit | S'exécute sur | Données | Source de vérité (GitLab pc4) | Déploiement / mise à jour | Sauvegarde |
|---|---|---|---|---|---|
| Site Nexora (front, site, worker) | VM 201 `nexora-pile`, Compose projet `nexorasite` | Postgres de la pile, `/srv/nexora` sur la VM | `root/nexora-web`, branche `main` | Compose sur la VM ; domaine par `deploy/domaine.sh` (non exécuté) | vzdump 03:30 de la VM 201 |
| Directus (CMS) | VM 201 | base Postgres de la pile | `root/nexora-web` | idem | vzdump VM 201 |
| LiteLLM (passerelle modèles) | VM 201 ; relais LAN `nexora-litellm-lan` pour la VM 203 | config et secrets `/srv/nexora/secrets` (0400) | `root/nexora-web` | idem | vzdump VM 201 |
| SearXNG, WebPilot (navigateur), Mailpit | VM 201 | éphémère / Postgres | `root/nexora-web` | idem | vzdump VM 201 |
| Nexora Creative (application) + Mode Studio | VM 202 `nexora-creative`, systemd `nexora-creative` | `/srv/creative/data` (dont `rendus`), config `/etc/nexora/creative.env` | `root/nexora-creative`, branche `developpement` (`main` protégée) | `deploy/proxmox/mettre-a-jour-creative.sh` | vzdump VM 202 |
| Moteur Creative : tunnels vers les GPU | VM 202, services `nexora-tunnel-gb10` et `nexora-tunnel-rtx5090` | aucune | `root/nexora-creative` (`deploy/proxmox`) | idem | sans objet |
| Moteur Creative : ComfyUI GB10 (Qwen-Image, MiniMax Music 3) | pc6, port 37188, `~/nexora-creative-data/engine/superviser-comfyui.sh` | modèles `~/nexora-creative-data/models` (28 Go) | scripts dans `root/nexora-creative` | à la main sur pc6 | modèles : à retélécharger |
| Moteur Creative : ComfyUI RTX 5090 (MiniMax H3) | pc1, port 18388 | modèles `minimax-h3/models` (66 Go) | scripts dans `root/nexora-creative` | à la main sur pc1 | modèles : à retélécharger |
| Moteur Creative : GPU Turing de pc5 (TRELLIS.2 int8, Whisper, TTS Kokoro et Chatterbox, Demucs, embeddings) | VM 204 `nexora-gpu` (192.168.1.124) : `nexora-comfy@0` 8188, `nexora-comfy@1` 8189, `nexora-services` 8190, LAN seulement | modèles `/srv/nexora-gpu/models` (8,4 Go, copiés de la GB10) | `docs/gpu-pc5.md` et `deploy/proxmox/creative.env.example` (`root/nexora-creative`) | à la main dans la VM (`ssh nexora-gpu`) ; **transcription du Mode Studio branchée depuis le 04/11** (`/transcrire`, jeton, repli CPU ; `NEXORA_TRANSCRIPTION_URL` et `NEXORA_TRANSCRIPTION_TOKEN` dans `creative.env`), le reste non branché | aucune (régénérable) |
| Protection RTX 5090 (plafond 475 W, ventilateur 100 %) | pc1, `nexora-gpu-5090.service` + `nexora-gpu-5090-watch.timer` (systemd), `/usr/local/sbin/nexora-gpu-5090.sh`, `/etc/default/nexora-gpu-5090` | aucune | `deploy/pc1-gpu-5090` (dépôt `root/nexora-creative`) | `systemctl restart nexora-gpu-5090.service` | sans objet |
| WorkStudio | VM 203 `nexora-workstudio`, Compose projet `nexora`, `/srv/nexora/workstudio/ws.sh` | `/srv/nexora/secrets-workstudio` | `root/nexora-workstudio` | `ws.sh` ; domaine via `NEXORA_DOMAINE` | vzdump VM 203 |
| Nexora Code (agent, fork d'opencode) | poste de travail (pc6, `~/Desktop/NexoraCode/src`) | sans objet | `root/nexora-code-agent` (`main` à jour ; **branche `feat/rebrand` non poussée**, dépôt local tronqué) ; `root/nexora-code`, `root/nexora-corpus` | à définir | `.git` copié sur pc5 (archives) |
| RAG (pc5-rag) | à confirmer : seules des images `localhost/pc5-rag*` sont sur le Docker de pc6 | à confirmer | à confirmer | à confirmer | à confirmer |
| VPS / OPSYS-AI | à confirmer ; la VM 9100 `opsys-test-claude` n'est pas à Nexora ; films OPSYS-AI en cours de fabrication sur pc6 (`promo/v6`) | films : pc6 puis archives pc5 | `root/nexora-creative` (`marketing/nexora/campagne-films`, non suivi pour l'instant) | sans objet | à faire après la fin du film |

## Stockage

| Lieu | Contenu | Sauvegarde |
|---|---|---|
| pc5 `ssd-1tb` (volume fin) : VM 201, 202, 203 (sauvegardées) et 204 `nexora-gpu` (non sauvegardée) | disques des VM | vzdump vers `backup-nvme0` chaque nuit à 03:30 (7 jours, 4 semaines) |
| pc5 `/mnt/nexora-archives` (LV fin `ssd-1tb/nexora-archives`, 250 Go, ext4) | archives pc6 et pc1 : films rendus, rushes, plaques, rendus de l'application, caches d'évaluation ; manifeste `MANIFESTE.md` | pas dans vzdump (volontairement) ; pas de copie secondaire |
| pc6 `~/nexora-creative-data` | modèles (28 Go), moteur ComfyUI (13 Go), `promo` (finals V4 et films, `v6` en cours), `site-medias` (copie de travail du site), `app-data` | archives sur pc5 pour le reste |
| pc1 `/run/media/pc1/Infrastructure/NexoraStudioWork/minimax-h3` | `models` (66 Go), ComfyUI, venv, hf-home | aucune (modèles) |

## Pas encore sur Proxmox

- La pile de développement `nexorasite-*` sur le Docker de pc6 (db, directus, litellm, searxng, mailpit, stripe-mock) : sert au développement ; la production est sur la VM 201.
- Les deux GPU (GB10 de pc6 et RTX 5090 de pc1) : par nature hors Proxmox, joints par tunnel depuis la VM 202.
- Docker de pc6 : 21,9 Go d'images et 14,9 Go de volumes, dont 13,3 Go de volumes anonymes (263) ; aussi les projets jeuxvideo.ca, infratech.ca et futureia, qui ne sont pas à Nexora (aucun nettoyage fait, décision du fondateur).
- RAG pc5-rag : emplacement à confirmer (voir tableau).
- `~/Desktop/NexoraCode/src` : branche `feat/rebrand` non poussée sur GitLab.
- `~/Desktop/Nexora` : dossier vide.
