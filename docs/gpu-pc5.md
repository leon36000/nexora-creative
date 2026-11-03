# Les deux GPU de pc5 (VM 204 `nexora-gpu`)

Mis en place le 03/11/2026. Ordre du fondateur : les deux cartes entières, le minimum de ressources pour le reste. Registre d'allocation : `docs/RESSOURCES.md` §8.

## Ce qui tourne

| Élément | Valeur |
|---|---|
| Matériel (hôte `pve`) | RTX 2080 SUPER (06:00.x, lien PCIe **x4**, 8 Go) et RTX 2070 SUPER (01:00.x, x16, 8 Go) ; Turing sm_75 : fp16 et int8 oui, **bf16 et fp8 non** (bf16 n'est qu'émulé) |
| VM | 204 `nexora-gpu`, q35 + OVMF, 4 vCPU `host`, 8 Go fixes (ballon coupé), disque 60 Go fin sur `ssd-1tb`, swap 8 Go dans la VM, `onboot`, étiquettes `nexora;gpu;prod`, **hors du job vzdump** (modèles et sorties se régénèrent) |
| Accès | `ssh nexora-gpu` (192.168.1.124, utilisateur `nexora`, clé `~/.ssh/id_ed25519_nexora_vm`). Pare-feu Proxmox `/etc/pve/firewall/204.fw` : entrée coupée sauf SSH, 8188-8190 et ping depuis 192.168.1.0/24 |
| Pilote | `nvidia-driver-595-server-open` (595.91.07, DKMS), `nvidia-persistenced` actif |
| Python | `/srv/nexora-gpu/venv` (torch 2.11.0+cu128, ComfyUI) et `/srv/nexora-gpu/venv-audio` (services) |
| ComfyUI | **v0.43.2 figé** (comme la GB10 : nœuds TRELLIS natifs), `/srv/nexora-gpu/ComfyUI`, unité `nexora-comfy@N` : N=0 → GPU 0 (2080 SUPER) port **8188**, N=1 → GPU 1 (2070 SUPER) port **8189** (`--reserve-vram 2.5` pour laisser de la place aux services). Écoute sur 192.168.1.124 seulement. Modèles : `/srv/nexora-gpu/models` (8,4 Go : TRELLIS.2 int8, deux VAE, DINOv3, BiRefNet, copiés depuis la GB10) |
| Services | `nexora-services` (FastAPI, port **8190**, GPU 1) : `/stt` (faster-whisper large-v3-turbo fp16), `/tts` (Kokoro ou Chatterbox multilingue, `engine=kokoro\|chatterbox`, `lang=fr`, `reference=` pour cloner une voix), `/demucs` (htdemucs, zip de 4 pistes), `/embed` (BAAI/bge-m3), `/health`. Un seul modèle en VRAM à la fois, libéré après 120 s d'inactivité |

Un job par GPU : deux travailleurs ComfyUI indépendants. Il n'y a pas de découpage d'un modèle sur les deux cartes (PCIe x4 d'un côté, aucun NVLink : le gain serait négatif) ; TRELLIS.2 int8 tient en entier dans 8 Go.

## Mesures (03/11/2026, GPU nus, aucune surcote)

| | RTX 2080 SUPER | RTX 2070 SUPER |
|---|---|---|
| matmul fp16 (8192², cuBLAS) | 45,6 TFLOPS à 243 W, 49 °C, 1918 MHz | 38,1 TFLOPS à 212 W, 62 °C, 1909 MHz |
| matmul fp32 | 10,2 | 8,8 |
| bande passante mémoire | 425 Go/s | 385 Go/s |
| repos (pilote chargé) | 35 W, 36 °C | 14 W, 50 °C |
| TRELLIS.2 int8 « aperçu » (150 k faces) | 126 s à froid, 136 s autre graine ; pic VRAM **7,2 Go** | |
| TRELLIS.2 int8 « qualité » (400 k faces, texture 4096) | | **531 s**, pic VRAM **7,8 Go** sur 8,2 (passe, de justesse) |
| Référence GB10 | aperçu 38 s, qualité 162 s : les cartes Turing sont ~3,3 fois plus lentes | |

Services (GPU 1, phrase de 7 s) : Kokoro 0,12 s à chaud (8 s à froid) ; Chatterbox multilingue fr 2,1 s à chaud (36 s à froid) ; Whisper turbo 0,47 s à chaud (voix reconnue sans faute) ; Demucs 2,1 s ; embeddings bge-m3 17 s à froid. **Non mesurés** : RIFE, agrandisseurs, modèles d'image (à tester à la demande).

## gpu-unlock : verdict

`Zagitta/gpu-unlock` est un **module noyau Linux** (pas de VBIOS, pas de pilote modifié) qui, au démarrage et avant `nvidia`, lève le plafond de débit des cœurs tensoriels des GeForce (fp16/bf16/tf32 à accumulation fp32), puis fait un FLR. Il ne touche ni aux fréquences ni aux limites de puissance. **Turing y est « expérimental »**. Testé dans la VM (DKMS + micrologiciel extrait du pilote 610.43.03, `gpu_unlock.targets=all`) : **échec sur les deux cartes** (`unlock_transaction_fwsec error=-19`, puis `-16` au retour) ; le module garde alors les régions mémoire des cartes et **empêche `nvidia` de s'initialiser**. Les tickets amont #242 et #287 décrivent la même carte (2070 SUPER, 10de:1e84) sans solution ; le correctif PR #294 (« Turing, two-write chain ») est ouvert. Gain : **aucun** ; risque : GPU indisponible jusqu'à retrait de l'option. Désactivé (option retirée du noyau) : paquets `gpu-unlock-dkms` et `gpu-unlock-firmware` laissés installés mais inertes (rien ne se passe sans `gpu_unlock.targets=`). À retenter si #294 est fusionné (le plafond fp32-accum de Turing est probablement ce qui limite les 45 TFLOPS mesurés, mais à 243 W la carte est de toute façon au plafond de puissance).

**Annuler** : `sudo rm /etc/default/grub.d/99-gpu-unlock.cfg && sudo update-grub && sudo sync`, puis redémarrer (un `qm stop` brutal avant le `sync` perd la modification : c'est arrivé).

## Hôte : passthrough et retour arrière

Fichiers sur `pve` (copie d'origine dans `/root/backup-gpu-pc5/`) :
- `/etc/default/grub` : `GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt video=efifb:off video=vesafb:off"` puis `update-grub` (l'hôte démarre sur GRUB, `proxmox-boot-tool` n'est pas initialisé) ;
- `/etc/modprobe.d/vfio.conf` (ids `10de:1e84,1e81,10f8,1ad8,1ad9` + `softdep`), `/etc/modprobe.d/blacklist-gpu-host.conf` (`nouveau`, `nvidia`, `nvidiafb`, `nvidia_drm`, `i2c_nvidia_gpu`) ;
- `/etc/modules` et `/etc/initramfs-tools/modules` : `vfio vfio_iommu_type1 vfio_pci` ; `update-initramfs -u -k all`.

Groupes IOMMU propres : chaque carte (4 fonctions) est seule dans son groupe (15 et 20). L'hôte garde le GPU intégré Intel pour une console. Les fonctions USB et UCSI sont rendues à vfio-pci par Proxmox au démarrage de la VM.

**Revenir à l'état d'avant** : `qm stop 204` ; restaurer `/root/backup-gpu-pc5/grub` vers `/etc/default/grub`, supprimer `vfio.conf` et `blacklist-gpu-host.conf` de `/etc/modprobe.d`, restaurer `modules` et `initramfs-modules`, `update-grub`, `update-initramfs -u -k all`, redémarrer. L'hôte retrouve `nouveau` sur les cartes.

## Exploitation

- Voir : `ssh nexora-gpu 'nvidia-smi; systemctl status nexora-comfy@0 nexora-comfy@1 nexora-services'` ; santé des services : `curl http://192.168.1.124:8190/health`.
- Redémarrer un travailleur : `sudo systemctl restart nexora-comfy@1`.
- Mettre le pilote à jour : `apt install nvidia-driver-<branche>-server-open` (branche qui accepte Turing), redémarrer la VM ; vérifier `nvidia-smi` et relancer le banc `/srv/nexora-gpu/bench_gpu.py`.
- Mettre ComfyUI à jour : seulement avec le banc `scripts/bench-3d.ts` (les noms de nœuds TRELLIS changent d'une version à l'autre) ; rester sur 0.43.2 tant que Creative l'exige.
- Banc de ce document : `/srv/nexora-gpu/bench_gpu.py`, `run_prompt.py` (envoie un graphe et mesure le temps et le pic VRAM), `trellis_draft.json`.

## Brancher Creative (VM 202)

Le serveur lance lui-même un `comfy-api-proxy` par moteur dont `baseUrl` est local, vers le `comfyUrl` donné : pas de tunnel pour ce moteur. Dans `/etc/nexora/creative.env` de la VM 202, ajouter au JSON de `NEXORA_MOTEURS_GPU` (exemple dans `deploy/proxmox/creative.env.example`) :

```
{"id":"turing-2080s","nom":"RTX 2080 SUPER (pc5)","comfyUrl":"http://192.168.1.124:8188","baseUrl":"http://127.0.0.1:37388","recettes":["objet-apercu"]},
{"id":"turing-2070s","nom":"RTX 2070 SUPER (pc5)","comfyUrl":"http://192.168.1.124:8189","baseUrl":"http://127.0.0.1:37389","recettes":["objet-apercu","objet-qualite"]}
```

puis `sudo systemctl restart nexora-creative`. **Pas activé sur la VM 202** (aucun redéploiement) : le routage envoie la recette au moteur le moins chargé parmi ceux qui la déclarent, donc une fois activé, un job « qualité » peut partir sur la 2070 SUPER (531 s au lieu de 162 s) alors que la GB10 est libre. À décider par le fondateur ; pour laisser la GB10 seule sur « qualité », ne déclarer que `objet-apercu`. Les services STT/TTS/Demucs (port 8190) ne sont pas dans le parc ComfyUI : Creative (ou un autre agent) les appelle en HTTP sur `http://192.168.1.124:8190` ; le code de Creative n'a pas encore de client pour eux.

## Chaleur, bruit, consommation

Sous charge maximale les deux cartes tirent ensemble ~455 W (GPU seuls) ; au repos ~50 W. Le serveur est une machine d'atelier : les ventilateurs montent à fond sous TRELLIS ou matmul continu (non mesuré en décibels). La 2070 SUPER est plus chaude (62 °C contre 49 °C). Aucune surcote ni limite de puissance modifiée.
