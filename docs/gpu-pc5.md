# Les deux GPU de pc5 (VM 204 `nexora-gpu`)

Mis en place le 03/11/2026. Ordre du fondateur : les deux cartes entières, le minimum de ressources pour le reste. Registre d'allocation : `docs/RESSOURCES.md` §8.

## Ce qui tourne

| Élément | Valeur |
|---|---|
| Matériel (hôte `pve`) | RTX 2080 SUPER (06:00.x, lien PCIe **x4**, 8 Go) et RTX 2070 SUPER (01:00.x, x16, 8 Go) ; Turing sm_75 : fp16 et int8 oui, **bf16 et fp8 non** (bf16 n'est qu'émulé) |
| VM | 204 `nexora-gpu`, q35 + OVMF, 4 vCPU `host`, 8 Go fixes (ballon coupé), disque 72 Go fin sur `ssd-1tb` (état live du 13/11; 60 Go à la création), swap 8 Go dans la VM, `onboot`, étiquettes `nexora;gpu;prod`, **hors du job vzdump** (modèles et sorties se régénèrent) |
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

## gpu-unlock : profils et méthode (04/11/2026) : ACTIF sur les deux cartes

**Résultat : le correctif Turing de l'amont (PR #294 : branche `fix/turing-loader-halt` + « two-write chain », 3 fichiers `falcon.c`, `recipes.c`, `unlock_610.c`) débloque les deux cartes du premier coup, à chaud, sans option noyau.** Le « profil » TU104 n'est pas à écrire : la table du module connaît déjà `10de:1e84` (2070 SUPER) et `10de:1e81` (2080 SUPER), famille TU102/TU104/TU106. Ce que le tronc (`7eb51bc`) ne savait pas faire, c'est la **séquence** Turing (le booter signé libère le mutex ACR 3 par deux écritures au lieu des six de GA102, puis FLR sauté). Le travail du 4070 Laptop du fondateur (Ada, `AD106` déjà dans la table, `gpu_unlock.targets=all`) est de la même nature : installer l'amont ; les sessions Codex retrouvées (`~/.codex/sessions/2026/10/28` et `/29`) ne contiennent que la lecture du README, aucun profil maison. Ce qu'il fallait trouver était la PR #294, validée par 7 testeurs (TU102/104/106, 2060 à 2080 Ti, +52 à +69 %).

**Ce que « débloquer » change.** NVIDIA bride sur les GeForce, par fusibles et sélecteurs de sous-système (`ss0/ss1`), le débit des cœurs tensoriels quand ils **accumulent en fp32** (entrées fp16/bf16/tf32, sortie fp32, ce que presque toute l'IA utilise) : demi-débit. Le module écrit les deux sélecteurs (`ss0=0x88888888`, `ss1=0x8`) en exploitant le booter signé SEC2 avant que `nvidia` ne prenne la carte. Ni fréquences, ni limites de puissance, ni VBIOS : l'état est **volatil** (perdu à la réinitialisation de la carte). Le fp32 des cœurs CUDA, l'int8 et la mémoire ne changent pas.

| Mesure (8192³, cuBLAS, GPU nus) | 2080 SUPER avant → après | 2070 SUPER avant → après |
|---|---|---|
| fp16, accumulation **fp32** | 45,2 → **70,6** TFLOPS (+56 %) | 38,1 → **59,2** (+55 %) |
| fp16, accumulation fp16 | 71,1 → 72,1 (inchangé) | 60,2 → 60,1 |
| int8 (`_int_mm`) | 42,8 → 43,3 | 35,9 → 36,0 |
| fp32 CUDA | 10,4 → 10,5 | 8,6 → 8,6 |
| bande passante mémoire | 426 → 416 Go/s | 378 → 383 Go/s |
| puissance, température, horloge | 245 → 244 W, 60 → 54 °C, 1804 → 1771 MHz | 214 → 213 W, 74 → 73 °C, 1805 → 1758 MHz |
| TRELLIS.2 int8 aperçu (2080 SUPER) | 126 s → 126,1 s | |
| TRELLIS.2 int8 qualité (2070 SUPER) | | 531 s → 543,8 s (bruit) |

Lecture : le gain est réel et ramène le fp32-accumulate au débit du fp16 pur (à 215-245 W les cartes sont déjà au plafond de puissance : l'horloge baisse de 2-3 %, la puissance ne bouge pas), mais **les jobs actuels n'en profitent pas** : TRELLIS.2 est quantifié en int8 et borné par la mémoire. À gagner pour tout modèle fp16 qui accumule en fp32 (Whisper fp16, diffusion fp16, Chatterbox, futurs modèles) ; pas mesuré job par job. Verdict : **gardé** (coût nul mesuré, risque faible, retour arrière en un fichier).

**Mise en œuvre (VM 204).** Pas d'option noyau (celle du premier essai empêchait `nvidia` de démarrer en cas d'échec) : l'unité `nexora-gpu-unlock.service` (sources dans `deploy/pc5-gpu-unlock/`, installée dans `/usr/local/sbin/nexora-gpu-unlock.sh` et `/etc/systemd/system/`, activée, testée au redémarrage) tourne **avant** `nvidia-persistenced`, ComfyUI et `nexora-services` : pour chaque carte, détache `nvidia` (`unbind`), charge `gpu_unlock targets=<adresse PCI>`, le retire, rattache `nvidia`. **Contrôle de santé** : si `nvidia-smi -L` ne montre pas les deux cartes, retrait du module, rattachement, en dernier recours rechargement de `nvidia` ; l'unité sort en échec sans bloquer les services. Durée : 7 s. Module : PR #294 (`9422be4`) compilé par DKMS (`gpu-unlock/2.0.0`, sources de la PR dans `/usr/src/gpu-unlock-2.0.0`, originales copiées dans `/root/gpu-unlock-2.0.0.orig` ou `/var/tmp/`). Le `gpu_unlock` de l'initramfs est l'ancienne copie, inerte (sans `targets=`). Vérifier : `journalctl -b -t nexora-gpu-unlock` et `sudo dmesg | grep 'gpu_unlock: unlocked'` ; banc : `/srv/nexora-gpu/bench2.py` (avant : `bench_avant_pr294.jsonl`, après : `bench_apres_pr294.jsonl`). Le message `poll timeout: reg=0x840100` est attendu (le SEC2 Turing se lit « arrêté » après réinitialisation). Une coupure de courant a eu lieu pendant le travail : au redémarrage le module était inerte, rien de demi-appliqué, l'unité a ensuite débloqué les cartes à froid du premier coup.

**Désactiver / revenir en arrière.** `sudo touch /etc/nexora/gpu-unlock.disabled` puis redémarrer la VM (ou `sudo systemctl disable nexora-gpu-unlock`). Total : `qm stop 204 && qm rollback 204 avant-gpu-unlock-pr294` (état d'avant toute modification, sur l'hôte `pve` ; supprimer l'instantané avec `qm delsnapshot 204 avant-gpu-unlock-pr294` quand le fondateur valide). Carte bloquée : `qm reset 204`.

**Reproduire pour une autre carte.** (1) `lspci -nn -D` : l'identifiant doit figurer dans la table du module de la branche utilisée ; (2) la séquence dépend de la **famille** (Turing : PR #294 ; Ampere : tronc ; Ada : tronc / branche `ada-beta`) et du micrologiciel extrait du pilote **610.43.03** (paquet `gpu-unlock-firmware`) ; la version du pilote `nvidia` utilisé ensuite (595.91.07 ici, 595.99 et 615.x chez les testeurs) n'a pas d'importance ; (3) arrêter les services, `unbind`, `modprobe gpu_unlock targets=<adresse>`, lire `dmesg` (`stage=handoff ret=0` puis `unlocked`), `bind`, mesurer avec `bench2.py` ; (4) un `-110` intermittent existe en amont (timing de la phase GSP ; l'attente de 10 ms du `9422be4` utilisé ici le traite) : relancer ; si `retained=1`, redémarrer la VM.

**Blackwell (RTX 5090 de pc1) et GB10 : proposition, rien n'a été touché.** Les sources publiques concordantes (fil r/LocalLLaMA du 28/10, ai.rs, TweakTown) disent qu'**aucun déblocage n'existe pour les RTX 50** : Turing, Ampere et Ada passent par un défaut du booter signé, absent de GB202 (nouveau chargeur, micrologiciel de gestion séparé, écritures de registres ignorées, modification des fusibles = carte qui ne démarre plus). Il faudrait une nouvelle faille de micrologiciel, non publique : ce n'est pas un travail de profil. Pour la 5090 (475 W, −13 % de calcul brut), le gain par déblocage est donc **indisponible aujourd'hui** ; leviers réels : 525 W (−6,5 %), vérifier les noyaux fp8/fp4 natifs, surveiller `Zagitta/gpu-unlock` (branche Blackwell éventuelle). À tester dans une fenêtre sûre seulement si une version Blackwell apparaît : instantané et retour arrière préparés, aucun essai pendant les films. GB10 (DGX Spark) : pas de plafond GeForce documenté, absent de la liste prise en charge ; rien à faire.

**Premier essai (03/11, abandonné)** : tronc `7eb51bc` par option noyau `gpu_unlock.targets=all` : `error=-19` sur les deux cartes, module retenant les cartes et bloquant `nvidia` ; remplacé par la PR #294 chargée à chaud.

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

Le serveur lance lui-même un `comfy-api-proxy` par moteur dont `baseUrl` est local, vers le `comfyUrl` donné : pas de tunnel pour ce moteur. Dans `/etc/nexora/creative.env` de la VM 202 (déployé le 04/11/2026, voir `docs/JOURNAL.md`) :

```
NEXORA_MOTEUR_SECONDES={"objet-apercu":46,"objet-qualite":189}
NEXORA_MOTEURS_GPU=[…, {"id":"turing-2080s","nom":"RTX 2080 SUPER (pc5)","comfyUrl":"http://192.168.1.124:8188","baseUrl":"http://127.0.0.1:37388","recettes":["objet-apercu","objet-multivue"],"secondes":{"objet-apercu":190,"objet-multivue":190}},
  {"id":"turing-2070s","nom":"RTX 2070 SUPER (pc5)","comfyUrl":"http://192.168.1.124:8189","baseUrl":"http://127.0.0.1:37389","recettes":["objet-apercu","objet-multivue"],"secondes":{"objet-apercu":220,"objet-multivue":220}}]
```

Règle de routage (`moteursPour`, `server/engine.ts`) : le moteur qui **finit le plus tôt** = (tâches en cours + 1) × secondes de la recette sur ce moteur. Un brouillon 3D reste sur la GB10 (46 s) tant que sa file ne dépasse pas trois tâches, puis déborde sur la 2080 SUPER (190 s) puis la 2070 SUPER ; la **qualité** (`objet-qualite`) n'est déclarée que sur la GB10 (531 s sur une 2070 SUPER contre 189 s). `objet-multivue` (Pixal3D, plusieurs vues) n'existe que sur ces deux moteurs : c'est là que vivent les poids Pixal3D. Les services STT/TTS/Demucs (port 8190) ne sont pas dans le parc ComfyUI : Creative (ou un autre agent) les appelle en HTTP sur `http://192.168.1.124:8190` ; le code de Creative n'a pas encore de client pour eux.

**Disque de la VM** : 58 Go dont ≈ 4 Go libres (04/11/2026, après purge du cache pip) ; les poids Pixal3D (5,58 Go) y remplacent un fichier de même taille. Un nouveau modèle de 6 Go demande d'agrandir le disque (`qm resize`, décision du fondateur).

## Chaleur, bruit, consommation

Sous charge maximale les deux cartes tirent ensemble ~455 W (GPU seuls) ; au repos ~50 W. Le serveur est une machine d'atelier : les ventilateurs montent à fond sous TRELLIS ou matmul continu (non mesuré en décibels). La 2070 SUPER est plus chaude (62 °C contre 49 °C). Aucune surcote ni limite de puissance modifiée.


## Modèles compacts — centralisation PC5 (13 novembre 2026)

Le fondateur demande de conserver dans la VM GPU 204 tous les poids compacts utilisables individuellement sur l’une des deux cartes 8 Gio, même si on ne les charge pas tous ensemble. Ils sont activés à la demande, une carte réservée par essai. Inventaires live : nexora-local-small (142 fichiers), nexora-candidates (71 entrées), MuseTalk (18 fichiers), LatentSync 1.5 et son VAE (18 fichiers). faster-whisper large-v3-turbo se trouve déjà dans le cache HF de la VM; son empreinte officielle a été vérifiée. Le détail complet et les limites de qualification sont dans docs/PC5-MODELES-COMPACTS.md.

LatentSync 1.5 est rangé dans /srv/nexora-gpu/models/nexora-sync/LatentSync-1.5 avec son manifeste. Aucun runtime ni branchement Creative n’a été installé et aucun rendu GPU n’a été lancé. Son minimum officiel de 8 Gio correspond à la capacité exacte de chaque carte PC5; une qualification isolée reste nécessaire. Le volume Sync est 20 Gio, 16 Gio utilisés, 4,5 Gio libres.
