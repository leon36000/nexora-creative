# Ressources Nexora : conventions, registre d'allocation, plan HDD

Mis à jour le 03/11/2026 (VM 204 `nexora-gpu` et les deux GPU, §8). Règle du fondateur : ne jamais allouer plus que le besoin réel ; tout est classé, étiqueté, propre ; aucun fichier épars ; chaque Mo a une affectation. pc5 (Proxmox `pve`) est le vrai serveur Nexora : tout ce qui est Nexora y vit, sauf les modèles (pc1, pc6), les GPU et le poste de développement. Le code est sur GitLab (pc4). Tests et expériences se font sur pc1 et pc6 et sont supprimés à la fin.

Qui vit où : `docs/ENVIRONNEMENTS.md`. Journal des suppressions : `docs/JOURNAL.md` (entrée « ménage d'infrastructure : conventions »). Inventaire automatique : `ressources/inventaire.sh` (lecture seule).

## 1. Conventions

**Noms.** Volumes logiques et dossiers dédiés : `nexora-<produit>-<usage>` (ex. `nexora-creative-archives`). Produits : `site`, `creative`, `workstudio`, `code`, `rag`. Les noms hérités (`nexora-archives`, `backups`) restent jusqu'à la prochaine recréation, sans renommage à chaud.
**VM Proxmox.** Nom `nexora-<produit>` ; étiquettes `nexora;<env>;<produit>` (env : `prod`, `test`, `gabarit`) ; description obligatoire : propriétaire, usage, date de création, sauvegarde, date de revue, renvoi vers ce document. Une VM sans étiquette ou sans description est signalée par l'inventaire. Les VM qui ne sont pas à Nexora n'ont pas l'étiquette `nexora`.
**Fichiers.** `<produit>-<sujet>-<AAAAMMJJ>[-vN].<ext>` en minuscules sans espace ; un finals porte `final`, un brouillon `brouillon`.
**pc6, `~/nexora-creative-data/{models,engine,work,outputs,archive}`.** Catégories cibles ; les dossiers actuels y sont rattachés par le README racine (`~/nexora-creative-data/README.md`) et un README par dossier (but, propriétaire, rétention, statut). Les dossiers en écriture par un agent (`promo/v6`, `rendus`, `output`) ne sont pas déplacés tant que le travail est en cours.
**pc5, archives.** `/mnt/nexora-archives/<produit>/<année>-<mois>/…` avec manifeste à la racine. Disposition héritée (`pc1/`, `pc6/`, classée par machine d'origine) à convertir quand l'agent film OPSYS-AI aura fini ; toute nouvelle archive suit la convention.

**Rétention.**
| Nature | Règle |
|---|---|
| Expérience, essai, banc, clone d'étude | supprimé à la fin de l'essai, 14 jours maximum |
| Brouillon de rendu | supprimé tout de suite |
| Final (film, image publiée) | copie sur pc5 (archives), vérifiée, puis suppression de la copie de travail |
| Cache régénérable (uv, pip, npm, bun) | purgé au-delà de 200 Mo |
| Volume Docker anonyme sans conteneur | supprimé après 24 h |
| Sauvegarde vzdump | `keep-last=1` jusqu'à l'arrivée du HDD |
| Modèles | permanents sur pc1 et pc6 |

## 2. Registre d'allocation (état au 02/11/2026)

### pc5 (Proxmox, hôte 62 Go de RAM, 24 threads)
| Élément | Propriétaire / usage | Alloué (virtuel) | Occupé réel | Rétention | Statut |
|---|---|---|---|---|---|
| VM 201 `nexora-pile` | site, Directus, LiteLLM… | 220 Go, 20 Go RAM, 6 vCPU | 43 Go, 3,7 Go RAM (+13 Go cache) | permanent | prod, étiqueté |
| VM 202 `nexora-creative` | application Creative | 120 Go, 12 Go RAM, 8 vCPU | 6,5 Go, 0,8 Go RAM | permanent | prod, étiqueté |
| VM 203 `nexora-workstudio` | WorkStudio | 150 Go, 20 Go RAM, 8 vCPU | 23 Go, 3,6 Go RAM | permanent | prod, étiqueté |
| VM 9000 `tpl-ubuntu-2404` | gabarit de création de VM | 3,5 Go | 1,8 Go | permanent | étiqueté |
| VM 9100 `opsys-test-claude` | pas à Nexora (OPSYS-AI, essais) | 40 Go, 5 Go RAM, 4 vCPU | 4 Go | « à supprimer après usage » | à décider par le fondateur |
| LV `ssd-1tb/nexora-archives` | archives pc1/pc6 | **40 Go** (était 250) | 21,6 Go | permanent | ext4, `/mnt/nexora-archives` |
| LV `pve/backups` | vzdump (NVMe) | **80 Go** (était 200) | 29 Go | 1 point de restauration | provisoire jusqu'au HDD |
| LV `pve/data` (pool fin local-lvm) | réserve du NVMe, ne contient que `backups` | 346 Go | 33 Go | n/a | à restituer avec le HDD |
| LV `pve/root`, `pve/swap` | hôte | 96 Go, 8 Go | 4,2 Go | n/a | trop grand (voir §5) |
| Pool `ssd-1tb` | disques des VM, archives | 913 Go | 120 Go (12,6 %) | n/a | sain |
| Stockage `local` | ISO | 98 Go | 4,4 Go | n/a | ISO inutile supprimée |

### pc6 (GB10)
| Élément | Propriétaire | Taille | Rétention | Statut |
|---|---|---|---|---|
| `~/nexora-creative-data/models` | Nexora | 28 Go | permanente | garder |
| `…/engine` | Nexora | 13 Go | permanente | garder |
| `…/models/diffusion_models/trellis_2_int8_convrot.safetensors` (5,25 Go), `…/models/vae/trellis_2_{shape,texture}_vae_bf16.safetensors` (1,10 + 0,95 Go), `…/engine/ComfyUI/models/clip_vision/dino_v3_vit_l.safetensors` (1,21 Go), `…/models/background_removal/birefnet.safetensors` (0,44 Go) | Nexora Creative (mode 3D, TRELLIS.2) | 8,95 Go au total | permanente | lot A1 du 03/11/2026 (autorisé par le fondateur), variante int8 retenue au lieu du bf16 (10,34 Go, non téléchargé) ; dépôts Comfy-Org/TRELLIS.2 et Comfy-Org/BiRefNet (MIT ; DINOv3 sous licence Meta, copie Comfy-Org sans accès restreint) ; reste ≥ 21 Go libres sur `/` |
| `…/promo`, `rendus`, `output` | Nexora / agent OPSYS-AI | 2,2 Go, 0,4 Go, 0,4 Go | finals vers pc5 | agent en cours : ne pas toucher |
| `…/site-medias*` | Nexora site | 1,2 Go | jusqu'à publication | à archiver |
| `…/app-data, input, apercus, logs, producteur-dev, cache-analyse` | Nexora Creative | 0,2 Go | 14 jours | README posé |
| Docker `nexorasite-*` (6 conteneurs, 2 volumes 0,3 Go) | Nexora, pile de développement | ~0,5 Go | développement | à étudier (§6) |
| Docker `jeuxvideoca`, `infratechca`, `futureia`, `opsys-pg-test-*`, divers | autres projets du fondateur | voir inventaire | hors Nexora | non touché sauf volumes orphelins |
| Docker images locales `pc5-rag*` | RAG | ~8 Go | à confirmer | emplacement à confirmer |
| `~/.cache/pc5-mass-ingestion` | RAG (modèle) | 5,4 Go | à confirmer | non touché |
| `~/Desktop/NexoraCode` | Nexora Code | 3,9 Go | permanent | branche `feat/rebrand` non poussée |
| `~/Desktop/NexoraSite`, `-vert`, `-vps` | Nexora site | 1,2 à 1,3 Go chacun | copies de travail | à vérifier (§6) |

### pc1
| Élément | Taille | Rétention | Statut |
|---|---|---|---|
| `NexoraStudioWork/minimax-h3/models` | 66 Go | permanente | garder |
| `…/venv`, `ComfyUI`, `pythons`, `hf-home` | 6,9 Go | permanente | garder (ComfyUI 18388 actif) |
| `…/output`, `input` | 1,3 Go, 0,35 Go | finals vers pc5 | à archiver, rien de plus de 14 jours |
| `…/reprise-revues-20261030` | 125 Mo | fin de revue | à supprimer sur ordre |
| `~/.cache/tracker3` (index GNOME) | 9,5 Go | n/a | pas à Nexora : proposé au fondateur |
| `/tmp/nvidia-r595-*` | ~2 Go | n/a | pas à Nexora : proposé au fondateur |
| RTX 5090 : plafond 475 W + ventilateur 100 % permanent (`nexora-gpu-5090.service` + minuterie `-watch.timer`, script `/usr/local/sbin/nexora-gpu-5090.sh`, réglage `/etc/default/nexora-gpu-5090`) | n/a | permanente | Nexora, créé le 03/11/2026, ordre du fondateur : préserver la carte plutôt que les ventilateurs ; sources et retour arrière dans `deploy/pc1-gpu-5090/` ; mesures dans ce tableau |

### pc1, RTX 5090 : plafond de puissance (mesures du 03/11/2026)
Banc : multiplications bf16 8192×8192 (GPU saturé, pire cas), 60 s par palier après 10 s de chauffe, ventilateur en automatique, ComfyUI 18388 au repos (file vide). Aucun job H3 réel chronométré : la carte était occupée par les modèles du film (30 Go de VRAM), le banc ne fait que le calcul brut.
| Plafond | Débit (TFLOPS) | Perte | Puissance | Horloge SM | Température |
|---|---|---|---|---|---|
| 600 W | 228,8 | 0 % | 600 W | 2736 MHz | 51 °C (max 55) |
| 525 W | 213,9 | -6,5 % | 525 W | 2552 MHz | 57 °C (max 59) |
| **475 W (appliqué)** | 197,5 | -13,7 % | 475 W | 2355 MHz | 58,5 °C (max 59) |
| 450 W | 188,5 | -17,6 % | 450 W | 2248 MHz | 58 °C (max 59) |
| 400 W | 170,7 | -25,4 % | 400 W | 2033 MHz | 57 °C (max 57) |
| 475 W, ventilateur 100 % | 199,7 | -12,7 % | 475 W | 2377 MHz | **48 °C** (max 48) |
Lecture : 475 W économise 125 W (21 %) pour 13,7 % de calcul brut perdu (pire cas : un vrai job H3 passe aussi du temps hors des multiplications, la perte réelle est plus faible, non mesurée). Le rendement par watt monte de 0,38 à 0,42 TFLOPS/W. Le ventilateur à 100 % retire 10 °C en charge (en automatique il plafonnait à 30-37 %). Pour 525 W (-6,5 %) : mettre `POWER_LIMIT_W=525` dans `/etc/default/nexora-gpu-5090` puis `sudo systemctl restart nexora-gpu-5090.service`. Retour complet : `sudo systemctl disable --now nexora-gpu-5090-watch.timer nexora-gpu-5090.service` (remet le ventilateur en automatique et 600 W).

## 3. Sauvegardes : NVMe réduit, bascule vers le HDD

Décision du fondateur : aucune sauvegarde sur NVMe ; un HDD de 10 à 20 To va être installé. En attendant, la tâche `nexora-nightly` (03:30, VM 201, 202, 203, zstd, snapshot) est gardée avec **`keep-last=1`** sur `backup-nvme0` : un point de restauration récent par VM (29 Go au total). Le volume `pve/backups` a été ramené de 200 à 80 Go (pic de 58 Go pendant une sauvegarde, avant l'élagage).

Commandes à exécuter à l'arrivée du HDD (remplacer `/dev/sdX`, à vérifier avec `lsblk` ; tout est sur pc5 en root) :
```
parted -s /dev/sdX mklabel gpt mkpart nexora-hdd ext4 0% 100%
mkfs.ext4 -L nexora-hdd /dev/sdX1
mkdir -p /mnt/nexora-hdd && echo "UUID=$(blkid -s UUID -o value /dev/sdX1) /mnt/nexora-hdd ext4 defaults,nofail 0 2" >> /etc/fstab
mount /mnt/nexora-hdd && mkdir -p /mnt/nexora-hdd/vzdump /mnt/nexora-hdd/archives
pvesm add dir backup-hdd --path /mnt/nexora-hdd/vzdump --content backup --is_mountpoint /mnt/nexora-hdd --prune-backups keep-daily=7,keep-weekly=4,keep-monthly=3
pvesh set /cluster/backup/nexora-nightly --storage backup-hdd
vzdump 201 202 203 --storage backup-hdd --mode snapshot --compress zstd     # première sauvegarde manuelle, à vérifier
# après vérification d'un point de restauration complet sur le HDD :
pvesm remove backup-nvme0 && umount /mnt/nexora-backups
sed -i '\#/mnt/nexora-backups#d' /etc/fstab && lvremove -y pve/backups
# archives (froides) vers le HDD : rsync -aHAX --checksum /mnt/nexora-archives/ /mnt/nexora-hdd/archives/ , comparer, puis
umount /mnt/nexora-archives && sed -i '\#nexora-archives#d' /etc/fstab && lvremove -y ssd-1tb/nexora-archives
```
L'espace du NVMe `pve` (346 Go du pool `data`) est alors libre pour la prochaine VM.

## 4. Audit de l'allocation des VM et proposition de dimensionnement

Constat : les VM engagent 57 Go de RAM sur 62 Go d'hôte (l'hôte n'a plus que 7 Go libres, 12 Go avec le cache) alors que les invités utilisent 0,8 à 3,7 Go ; la charge CPU moyenne est quasi nulle (0,0 à 0,13) ; 26 vCPU alloués pour 24 threads. Le ballooning est désactivé (`balloon: 0`) et rien n'est à chaud. Les disques sont fins : un disque trop grand ne coûte rien tant qu'il n'est pas écrit, mais il fausse le plafond. **Proposition, non appliquée aux VM 201 à 203** (exige un redémarrage de chaque VM) :

| VM | RAM actuelle → proposée | vCPU | Ballon (minimum) | Disque |
|---|---|---|---|---|
| 201 `nexora-pile` | 20 Go → 10 Go | 6 → 4 | 4 Go | 220 Go : laisser (fin, 43 Go) ; élaguer le cache de construction Docker (5,1 Go dont 1,75 réclamable) et 7,4 Go d'images réclamables, sur ordre |
| 202 `nexora-creative` | 12 Go → 4 Go | 8 → 4 | 2 Go | 120 Go : laisser (6,5 Go) |
| 203 `nexora-workstudio` | 20 Go → 8 Go | 8 → 4 | 4 Go | 150 Go : laisser (23 Go) |
| Total | 52 Go → 22 Go (−30 Go) | 22 → 12 | | |

Mise en œuvre à une fenêtre calme : `qm set <id> --memory <Mo> --balloon <Mo min> --cores <n> --hotplug disk,network,usb,memory,cpu --numa 1` puis `qm reboot <id>` (une VM à la fois, sauvegarde fraîche avant, contrôle des conteneurs Compose après). VM 9100 : 5 Go de RAM et 4 vCPU non à Nexora, à supprimer par le fondateur (`qm stop 9100; qm destroy 9100 --purge`, comme dit dans sa description).
Hôte : `pve/root` 96 Go pour 4,2 Go utilisés et `pve/swap` 8 Go : trop grands mais non réductibles à chaud (ext4 sur le système) ; à rendre quand le HDD arrivera, en même temps que la suppression de `pve/backups`.

## 5. Résumé de l'inventaire (`ressources/inventaire.sh`, 02/11/2026 22:10)

- pc5 : 5 VM, 3 VM Nexora étiquetées et décrites ; [!] VM 9100 sans étiquette (pas à Nexora). 3 sauvegardes vzdump (une par VM, 29 Go). Aucun volume logique orphelin. Archives 21,6 Go sur 40 Go.
- pc6 : disque à 95 % (46 Go libres, 9 Go au départ). Aucun volume Docker orphelin, aucune image Docker sans nom. [!] 4 conteneurs arrêtés (`agent-forge-forgejo-*`, `pc6-openclaw-proof-*`, `opsys-pg-m4-m5-*`) à confirmer. [!] caches de plus de 200 Mo restants : huggingface 1,8 Go (modèles, gardé), ms-playwright 2,1 Go (tests, gardé), `pc5-mass-ingestion` 5,4 Go (RAG, emplacement à confirmer). Rien de plus de 2 jours dans `/tmp` hors sessions d'agents.
- pc1 : disque `NexoraStudioWork` 76 %, `models` 66 Go, aucun fichier de sortie de plus de 14 jours, ComfyUI 18388 en écoute (18288 ne l'était pas à ce moment) ; [!] `~/.cache/tracker3` 9,5 Go (pas à Nexora).

## 6. Ce qui est Nexora et vit hors de pc5 : proposition et ordre

1. **RAG (pc5-rag)** : seules les images `localhost/pc5-rag*` (~8 Go) et le modèle `~/.cache/pc5-mass-ingestion` (5,4 Go) sont sur pc6 ; emplacement réel inconnu. Décision : le fondateur confirme où est le RAG ; ensuite le déplacer en VM sur pc5 (étiquette `nexora;prod;rag`).
2. **`~/Desktop/NexoraCode/src` (3,9 Go)** : la branche `feat/rebrand` n'est pas poussée (dépôt local « shallow »). D'abord pousser (deepen ou nouveau remote), puis ne garder que le code sur GitLab et supprimer la copie ; l'archive `.git` est déjà sur pc5.
3. **Pile de développement `nexorasite-*`** (Docker de pc6, ~0,5 Go de volumes) : à reprendre en VM de test sur pc5 (clone du gabarit 9000, étiquette `nexora;test;site`) quand le travail sur le site se fait à distance ; la production est déjà sur la VM 201.
4. **Copies de travail du site** `NexoraSite`, `-vert`, `-vps` (3,7 Go) : vérifier que les branches sont sur GitLab et que les arbres sont propres, puis supprimer (même méthode que `NexoraSite-demo` et `-domaine`).
5. **Données non-modèles** : `site-medias*` (1,2 Go) et `promo` (finals) vers les archives de pc5 une fois la publication faite ; `minimax-h3/output` et `input` de pc1 (1,6 Go) idem.
6. Les deux GPU et les modèles restent sur pc1 et pc6 (hors Proxmox par nature).
Ordre : 2 (risque de perte), 1 (inconnu), 4, 5, 3.

## 7. Reste à faire / décision du fondateur
- Installer le HDD puis dérouler §3.
- VM 9100 : supprimer ou confirmer.
- Appliquer ou non le dimensionnement du §4 (redémarrage de chaque VM).
- Confirmer le RAG (§6.1) et les 4 conteneurs arrêtés de pc6.

## 8. Les deux GPU de pc5 et la VM 204 `nexora-gpu` (03/11/2026)

| Ressource | Affectation | Détails |
|---|---|---|
| VM 204 `nexora-gpu` | moteur GPU LAN | 4 vCPU, **8 Go fixes** (ballon coupé : le passthrough épingle la RAM), disque 60 Go fin `ssd-1tb` (≈ 40 Go utilisés : modèles 8,4 Go, deux venv), swap 8 Go interne, `onboot`, étiquettes `nexora;gpu;prod`, **hors vzdump** (tout se régénère ; modèles : sources sur la GB10) ; 192.168.1.124 |
| RTX 2080 SUPER (hôte 06:00.0-.3, lien x4) | travailleur ComfyUI 0, port 8188 | `vfio-pci` sur l'hôte, pilote `nvidia` 595 dans la VM ; 243 W max mesurés, 35 W au repos |
| RTX 2070 SUPER (hôte 01:00.0-.3, lien x16) | travailleur ComfyUI 1, port 8189, et services audio/texte, port 8190 | 212 W max mesurés, 14 W au repos |
| Ports LAN | 8188, 8189, 8190 | pare-feu Proxmox : seulement 192.168.1.0/24 (+ SSH) ; jamais exposés ailleurs |
| Hôte `pve` | `intel_iommu=on iommu=pt`, `vfio*`, `nouveau`/`nvidia` en liste noire | copies d'origine : `/root/backup-gpu-pc5/` (retour arrière : `docs/gpu-pc5.md`) |
| Mémoire hôte | engagée : 22 Go → **30 Go** sur 62 Go | une seule VM nouvelle, 8 Go non ballonnables |

Rétention : sorties ComfyUI dans `/srv/nexora-gpu/output/gpu{0,1}` à purger à la main (rien n'est sauvegardé) ; modèles non dupliqués inutilement (le lot A1 de 8,9 Go est copié une fois, seuls les 5 fichiers nécessaires). VM 9100 non touchée par ce travail, mais **arrêtée par le redémarrage de l'hôte** (pas de `onboot`) : à relancer ou supprimer par le fondateur.
