# Inventaire compact des VMs Nexora — PC5

Relevé du 13 novembre 2026 (heure de Montréal). Périmètre : VMs Nexora actives; aucune commande de configuration ou d’état détaillé sur la VM GitLab 206. Les tailles de disques Proxmox sont des capacités allouées; l’usage provient de `df` dans l’invité lorsque le QEMU Guest Agent répond.

| ID | Rôle | Allocation Proxmox | Usage disque racine mesuré | RAM invitée disponible au relevé |
|---:|---|---|---|---|
| 201 | Site / pile | 4 vCPU, 10 Gio, disque 220 Go | 50/213 Go (24 %) | 7,1 Gio disponibles |
| 202 | Creative | 4 vCPU, 4 Gio, disque 120 Go | 13/116 Go (11 %) | 2,9 Gio disponibles |
| 203 | WorkStudio | 4 vCPU, 8 Gio, disque 150 Go | 23/145 Go (16 %) | 4,9 Gio disponibles |
| 204 | GPU, ComfyUI, services de modèles | 4 vCPU, 8 Gio, disque système 72 Go + disque Sync 20 Gio + disque candidats 16 Gio | `/`: 65/69 Gio (94 %); Sync: 16/20 Gio (78 %; 4,5 Gio libres); candidats: 15/16 Gio (91 %) | 5,8 Gio disponibles; 3,4 Gio de swap occupés |
| 205 | Infrastructure | 4 vCPU, 8 Gio, disque 450 Go | Non vérifiable : QEMU Guest Agent inactif et la vérification SSH stricte a refusé une clé d’hôte différente. Aucune clé locale n’a été remplacée. | PVE rapporte environ 1,6 Gio résidents sur 8 Gio; métrique invitée non vérifiée |
| 207 | Runner CI isolé | 4 vCPU, 8 Gio, disque 80,5 Go | 3,7/77 Go (5 %) | 7,0 Gio disponibles au relevé |

## Cloisonnement et services partagés

- Les six VMs actives sont séparées par rôle et portent des étiquettes Nexora. Aucun conteneur LXC n’est présent.
- ComfyUI est installé une seule fois : les deux workers actifs (8188 et 8189) ont le même répertoire `/srv/nexora-gpu/ComfyUI`. Aucun worker n’a été redémarré.
- Les minuteries `fstrim.timer` sont actives dans les VMs 201, 202, 203, 204 et 207; aucun trim manuel ni effacement de fichiers n’a été lancé. État non vérifié dans la VM 205.
- Le QEMU Guest Agent répond sur 201, 202, 203 et 207. Il est inactif dans la VM 204 et ne répond pas dans la VM 205.

## Ressources Proxmox

- Hôte : 62 Gio de RAM; environ 17 Gio disponibles et 2,6 Gio de swap utilisés au relevé.
- `ssd-1tb` : 92,35 % utilisés, environ 69,8 Gio disponibles au relevé du 13/11/2026 22:24 (Montréal). Le volume candidats invité est à 15/16 Gio (91 %, 1,6 Gio libres).
- `local-lvm` : 88,19 % utilisés, environ 42,5 Gio disponibles au même relevé; aucun volume Nexora ajouté par cette intervention.
- `backup-nvme0` : 61,36 % utilisés, environ 53 Gio disponibles.

## CPU — mesure PVE sur les 7 derniers jours

Rapport CPU PVE, fenêtre de 7 jours, moyenne / maximum : VM 201 3,7 % / 38,5 %; VM 202 1,6 % / 32,2 %; VM 203 3,0 % / 18,5 %; VM 204 0,8 % / 43,4 %; VM 205 0,3 % / 3,9 %; VM 207 7,3 % / 64,1 %. Ces ratios seuls ne fixent pas le nombre minimal de vCPU par service. Aucune allocation CPU/RAM n’a été modifiée; réduire les cœurs actifs exige une fenêtre de redémarrage. Le worker ComfyUI partagé n’a pas été interrompu.

Les mesures sont des instantanés et ne remplacent pas la surveillance en charge. Le catalogue des poids est dans `MODELES-LOCAL-PC5.md`.

## Mise à jour live — 13 novembre 2026, 22:24 (Montréal)

- `qm list` filtré aux VM 201–205, 207 et aux VM de restauration 297–301 : 201–205 et 207 sont en marche; 297–301 sont arrêtées. VM206 exclue du relevé détaillé. Les allocations des VM 201–205 restent 4 vCPU chacune; RAM maximale 10/4/8/8/8 Gio. Aucun changement d’allocation. Mémoire Proxmox utilisée à l’instantané : 201 6,77/10 Gio; 202 3,65/4; 203 6,78/8; 204 7,97/8; 205 1,63/8. La pression CPU instantanée ne permet pas de choisir des cœurs minimaux; aucune réduction ni arrêt n’est engagé.
- `pvesm status` : `ssd-1tb` 92,35 % (69,8 Gio libres), `local-lvm` 88,19 % (42,5 Gio libres), `backup-nvme0` 61,36 % (53,2 Gio libres).
- VM204 : racine `/` 65/69 Gio (94 %, 4,6 Gio libres), modèles sur FS racine 23 Gio; venv 8,2 Gio, venv-audio 2,2 Gio, venv-banc 458 Mio (`du -x`). Disques montés séparément : candidats 15/16 Gio (91 %, 1,6 Gio libres), Sync 5,6/7,8 Gio (73 %, 2,2 Gio libres). Pas de suppression ni déplacement.
- WorkStudio VM203 : le conteneur Ollama local contient BGE-M3 mais n’a aucun modèle chargé; l’application utilise encore le nom d’hôte local `ollama`. Le YAML Compose pointe vers PC5/204, mais `.env` est absent; aucun secret lu, aucun conteneur redéployé ou arrêté. L’API Ollama de PC5/204 possède aussi BGE-M3, non chargé.
- ComfyUI reste une installation unique sur VM204. Le checkpoint RIFE 4.7 a été ajouté au manifeste candidats avec digest GitHub vérifié, mais `RIFE VFI` est absent de `/object_info`; son intégration attend une maintenance planifiée.


## État des modèles PC5 — 13 novembre 2026, 22:52 (Montréal)

Le volume Sync /srv/nexora-gpu/models/nexora-sync est maintenant de 20 Gio après extension en ligne du disque de VM204 et agrandissement ext4. Relevé après transfert : 16 Gio utilisés, 4,5 Gio libres (78 %). Le cache des modèles compacts est centralisé dans VM204 et chargé à la demande; le détail est dans docs/PC5-MODELES-COMPACTS.md.

### Relevé live PC5 — 14 novembre 2026

Lecture seule; VM206 exclue.

| VM | Rôle | CPU / RAM Proxmox | Disque invité observé |
|---:|---|---|---|
| 201 | Pile/site | 4 vCPU; max 10 Gio, ballon min 4 | 50/213 Gio (24 %); 4,1 Gio disponibles |
| 202 | Creative | 4 vCPU; max 4 Gio, ballon min 2 | 13/116 Gio (11 %); 3,0 Gio disponibles |
| 203 | WorkStudio | 4 vCPU; max 8 Gio, ballon min 4 | 23/145 Gio (16 %); 4,0 Gio disponibles |
| 204 | GPU | 4 vCPU; 8 Gio fixes | racine 60/69 Gio (88 %); Sync 16/20 Gio (78 %); candidats 15/16 Gio (91 %); 5,0 Gio disponibles et 3,1 Gio de swap occupés |
| 205 | Infrastructure | 4 vCPU; max 8 Gio, ballon min 3 | invité non vérifié : empreinte SSH changée |
| 207 | Runner isolé | 4 vCPU; 8 Gio fixes | 9,5/77 Gio (13 %); 5,0 Gio disponibles |

Pools Proxmox : ssd-1tb 91,64 % (≈76 Gio libres), local-lvm 88,19 %, backup-nvme0 61,36 %. Aucun réglage CPU/RAM/disque modifié. Les relevés ne prouvent pas qu’une réduction serait sûre; VM204 a du swap occupé et VM205 n’a pas de mesure invitée fiable.

VM204 : services GPU et agent invité actifs; santé 8188/8189/8190 = HTTP 200; files Comfy 0/0; Ollama /api/ps vide; GPU 0 %, 312/224 Mio. Aucun service/conteneur Comfy détecté sur VM201, 202, 203 et 207; VM205 non vérifiée. Services Comfy liés à l’adresse LAN, pas à localhost.

Vérification des chemins du manifeste VM204 : local-small 142/142 présents; candidats 71/71; MuseTalk 18/18; LatentSync 1.5 + VAE 18/18; zéro chemin manquant. Les fichiers bruts incluent aussi index et README.

PC3 reste injoignable par le NAT SSH documenté. Le .env sécurisé WorkStudio est absent; sa copie BGE locale reste intacte jusqu’à migration vérifiée. PC6 et VM206 non consultés ni modifiés.
