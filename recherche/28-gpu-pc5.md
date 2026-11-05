# Les deux GPU de pc5 (VM 204) : ce qu'elles peuvent porter pour Creative

Mesures du 04/11/2026 sur la VM 204 `nexora-gpu` (RTX 2080 SUPER et RTX 2070 SUPER, Turing sm_75, gpu-unlock actif, pilote 595.91.07, 4 vCPU, 7,7 Go de RAM, disque 58 Go à 95 %). Tous les essais ont tourné dans des processus à moi (unité systemd transitoire `essai-detourage-20261104b`, ports 8291 et boucle locale, dossier `/srv/nexora-gpu/essais-20261104/`), sans redémarrer ni ComfyUI (8188, 8189) ni le service audio (8190), plafonnés en mémoire par cgroup (`MemoryMax`) pour qu'un dépassement ne tue que mon processus (c'est arrivé une fois, la production n'a pas bougé). Scripts et résultats bruts : `recherche/28-annexes/`. Documentation de la VM : `docs/gpu-pc5.md`.

**État du rapport** : partiel et assumé. L'ordre de la consigne (détourage rapide, transcription, NVENC, puis le reste) a été suivi ; l'économie d'abonnement a fait renoncer aux bancs d'agrandissement, d'interpolation, de tri des prises et de voix. Chaque verdict dit s'il est **mesuré**, **estimé** ou **non vérifié**.

## 0. Ce qu'il faut retenir

| # | Tâche | Verdict | Chiffre clé |
|---|---|---|---|
| 1 | **Transcription du Mode Studio** | **OUI, à brancher en premier** | faster-whisper large-v3-turbo fp16 sur la 2070 SUPER : **40 à 46 fois le temps réel**, 0 % d'erreur de mots sur la parole synthétique de 35 s à 9 min ; le CPU actuel (medium int8, 4 vCPU) fait **1,2 à 2,7 fois** et perd des phrases sur une parole répétée (27 % d'erreur) |
| 2 | **Détourage rapide** (SAM 3.1 + ViTMatte base) | **OUI** sur la 2070 SUPER | **0,91 s par image** (5080 en pod : 0,54 ; GB10 : 0,67 ; V100 : 0,84), VRAM 2,1 à 2,8 Go ; clic 0,38 s, mot 0,6 s. Libère la 5080 pour le mode pro. Limite : RAM de la VM (3,9 Go de pic sur 7,7) et disque |
| 3 | **Export NVENC** (H.264/HEVC) | **OUI** pour les livraisons et aperçus | **2,9 s pour 77,5 s de vidéo 1344×768** (27 fois le temps réel) contre 27,4 s en x264 medium sur pc6 (déjà chargé à 18 de charge) : 9,5 fois plus vite ; qualité : HEVC NVENC ≈ x264 medium à débit égal, H.264 NVENC demande ≈ 16 % de débit en plus |
| 4 | Parakeet v3 (transcription) | **OUI en repli CPU, NON sur GPU ici** | sur les 4 vCPU : **17 fois le temps réel** (7 à 14 fois plus vite que medium CPU), 2 à 3 % d'erreur ; la voie GPU (ONNX Runtime) exige CUDA 13 (≥ 1 Go de bibliothèques, pas de place) |
| 5 | Usage combiné des deux cartes (LLM réparti, MultiGPU) | **NON utile** | pas de P2P, carte 0 en PCIe x4 : 2,3 Go/s entre les deux cartes ; 16 Go ne portent pas ce que les 8 Go ne portent pas, et un LLM local de 14 à 24 Md reste très en dessous de Gemini Flex / DeepSeek |
| 6 | Deux files indépendantes en parallèle | **OUI, sans gêne** | détourage sur la carte 1 + 70 TFLOPS soutenus sur la carte 0 : détourage +3 à +4 % de temps ; mais **la RAM (7,7 Go) et le disque (2,7 Go) sont les vrais goulots** |
| 7 | Agrandissement, interpolation, débruitage, tri des prises, voix | **non mesuré** | candidats et verdicts d'après sources : §7 |

**Ce qu'il y a de plus rentable à brancher en premier** : la transcription (gain 15 à 35 fois, zéro VRAM supplémentaire notable, intégration de 1 fichier côté Creative, MR prête), puis le détourage rapide sur la 2070 SUPER, puis NVENC pour les exports.

**Deux blocages à lever par le fondateur avant tout déploiement durable** : mémoire de la VM 204 (7,7 Go ; ComfyUI ×2 + audio en consomment déjà 4,5 : le détourage a été tué à 3 Go de plafond et n'a réussi qu'à 3,8 Go) et disque (voir §6, 6 Go récupérables sans rien casser).

## 1. Matériel et réseau interne de la VM

| | RTX 2080 SUPER (GPU 0) | RTX 2070 SUPER (GPU 1) |
|---|---|---|
| Lien PCIe en charge | **Gen3 x4** | Gen3 x16 |
| Hôte → carte (mesuré, 512 Mo épinglés) | **3,1 Go/s** | **11,8 Go/s** |
| Carte → hôte | 3,1 Go/s | 12,3 Go/s |
| Carte 0 ↔ carte 1 | 2,3 / 2,4 Go/s (`nvidia-smi topo -m` : PHB, via le pont hôte ; `can_device_access_peer` = faux) | |
| matmul fp16 soutenu (déblocage actif) | 69,8 TFLOPS | 59,2 (banc du 04/11) |

Conséquence : tout ce qui doit entrer ou sortir beaucoup de données par la carte 0 est quatre fois plus lent. Une image 1344×768 fp16 pèse 6 Mo, donc les images ne sont pas un problème ; charger 6 Go de poids prend 2 s sur la carte 0, 0,5 s sur la carte 1. Les services audio sont déjà sur la carte 1 (`CUDA_VISIBLE_DEVICES=1`).

## 2. Détourage rapide sur la 2070 SUPER (priorité 1)

Méthode : serveur du dépôt (`outils/detourage/serveur.py`, tel quel, aucune modification) lancé par `deploy/pc5-gpu/lancer-detourage-essai.sh` sur la carte 1, venv d'essai qui réutilise en lecture le torch 2.11.0+cu128 de la VM, ComfyUI épinglé `2c75dc1` (v0.44.0) comme bibliothèque, poids officiels `Comfy-Org/sam3.1` (révision 7bb8374, 1,75 Go, fp16) et `hustvl/vitmatte-base-composition-1k`, téléchargés sans jeton et **supprimés après l'essai**. Les clips sont les cinq clips Big Buck Bunny de pc3 (mêmes clics), banc `banc.py` du dépôt, 1280 px, bande 5 %, fp16 (dtype choisi par le code : Turing n'a pas de bf16).

| Séquence | Images | Total | s/image | Suivi SAM | Matting | Stabilisation + sorties | Encodage | VRAM pic (torch / smi) |
|---|---|---|---|---|---|---|---|---|
| Lapin en prairie (1er passage, modèles froids) | 22 | 19,9 s | 0,90 | 6,9 | 3,0 | 6,3 | 3,1 | 2,12 Go / 2,59 |
| Lapin en prairie (chaud) | 22 | 17,8 s | 0,81 | 6,3 | 2,3 | 6,2 | 2,3 | 2,32 / 2,78 |
| Gros plan flou | 25 | 15,7 s | 0,63 | 4,5 | 2,3 | 5,9 | 2,7 | 2,32 / 2,74 |
| Trio | 23 | 10,8 s | 0,47 | 2,2 | 0,7 | 4,0 | 3,5 | 2,32 / 2,80 |
| Raccords 12/4 | 32 | 27,7 s | 0,87 | 11,1 | 3,1 | 8,8 | 3,9 | 2,32 / 2,83 |
| **Long continu (105 images sur 224, segments 64/12)** | 105 | **94,5 à 96,3 s** | **0,90 à 0,92** | 41,5 à 41,9 | 11,5 à 13,7 | 30,3 | 8,7 | 2,1 à 2,3 / 2,6 à 2,9 |

Le scintillement après stabilisation est identique à celui des autres machines (0,0035 sur le long clip, gain 32 %). Aperçu interactif : **clic 0,38 s** (5080 : 0,11 à 0,16), **mot** « rabbit » 0,6 s (score 0,987), premier mot 2,3 s à froid. Les 105 images remplacent les 224 de la référence parce que le disque de la VM ne laissait pas la place (voir plus bas) ; le temps par image est le chiffre comparable.

| Machine (mêmes clips, long continu) | s/image | Total |
|---|---|---|
| RTX 5080 en pod (pc3) | 0,54 | 120 s |
| GB10 (bf16, SAM 2.1) | 0,67 | 151 s |
| V100 en VM | 0,84 | 188,7 s |
| **RTX 2070 SUPER en VM (cette mesure)** | **0,91** | ≈ 204 s extrapolés |

Lecture : la 2070 SUPER est 1,7 fois plus lente que la 5080 mais le travail qui coûte 0,54 s par image à la 5080 n'est que de la file d'attente de plus pour les films ; sur 105 images, **les étapes GPU (suivi + matting) font 0,52 s par image, les étapes CPU (stabilisation par flux optique, écriture PNG/EXR, encodage) 0,38 s par image** et plafonnent à 4 vCPU. Le réseau n'est pas un obstacle (VM 202 en 192.168.1.122, VM 204 en .124, même LAN, contrairement à la V100).

**Verdict : OUI.** Assez rapide pour libérer la 5080 pour le palier pro (LTX-2.5). Les trois conditions sont : (1) **RAM** : le serveur monte à 3,85 Go ; avec ComfyUI ×2 et le service audio résidents, il faut passer la VM de 8 à 12 Go (décision du fondateur) ; (2) **disque** : le garde-fou du serveur exige 3 Go libres + 0,08 Go par seconde de vidéo à 720p ; avec 2,7 Go libres il a refusé de travailler sur le disque (message `espace disque insuffisant`) et mes essais ont dû mettre les travaux en `tmpfs` (/dev/shm, qui consomme la RAM) ; après le plan §6 la place existe ; (3) **pare-feu Proxmox** : ouvrir un port (par ex. 8231) vers 192.168.1.122 seulement dans `/etc/pve/firewall/204.fw` (aujourd'hui seuls 8188-8190 sont ouverts).

Branchement Creative (**non fait**, la production n'a pas changé) : le champ `detourageUrl` d'une entrée de `NEXORA_MOTEURS_GPU` déclare le serveur par moteur (voir `outils/detourage/README.md`). Exemple pour la 2070 SUPER, à ajouter à l'entrée existante `turing-2070s` :

```
{"id":"turing-2070s",…,"recettes":["objet-apercu","objet-multivue","detourage-rapide"],"detourageUrl":"http://192.168.1.124:8231","secondes":{"objet-apercu":220,"objet-multivue":220,"detourage-rapide":0.9}}
```

plus, côté VM 204, `NEXORA_DETOURAGE_HOTE=192.168.1.124`, `NEXORA_DETOURAGE_AUTORISES=192.168.1.122`, `NEXORA_DETOURAGE_JETON_FICHIER=/etc/nexora/detourage-jeton` (mode 600, valeur créée par le fondateur, jamais dans git) ; le serveur refuse de démarrer sans l'un ou l'autre. Les `secondes` de routage sont par image et à valider avec l'équipe Creative selon la façon dont `moteursPour` interprète les recettes de détourage.

## 3. Transcription (priorité 2)

Banc `recherche/28-annexes/asr.py` + `score.py` (taux d'erreur de mots avec `jiwer`, normalisation : minuscules, ponctuation retirée). Carte 1. **Limites assumées** : pas de parole humaine de référence (aucun enregistrement sous licence avec transcription n'est dans le dépôt) ; la parole longue est du **Kokoro `ff_siwis`** lu sur un texte connu (34,5 s, répété 3 puis 15 fois : 103 s et 8,6 min) ; la parole « québécoise » est celle des voix `vox3-voice*` du banc de voix V7 (texte connu : « Trois mots et tout explose »), jamais d'un locuteur réel ; le bruit est du bruit rose ajouté. **Les chiffres disent donc que les modèles lisent une parole propre et courte sans faute, pas qu'ils tiennent une prise réelle bruitée.**

| Modèle / machine | VRAM pic | Vitesse (fois le temps réel) | WER parole 35 s | WER 103 s | WER 8,6 min | WER 11 clips courts (Québec, bruit) | Mots sur silence, musique synthétique, ambiance de rushes H3 |
|---|---|---|---|---|---|---|---|
| **faster-whisper large-v3-turbo fp16, GPU 2070 SUPER** | 2,5 Go | **40 à 46** (clips de 3 s : 15 à 21) | 0,0 % | 3,8 % | 0,0 % | propres 0 %, bruitées 8 % | 0 / 0 / 0 |
| faster-whisper medium int8, **4 vCPU** (équivalent du chemin actuel de Creative) | – | **1,2 à 2,8** | 0,0 % | **27,0 %** (phrases sautées) | non fini | propres 0 % | 0 / 0 |
| **Parakeet-TDT-0.6B-v3 int8 (onnx-asr), 4 vCPU** | 0 (CPU) | **16 à 18** | 1,9 % | 3,1 % | 2,4 % | propres 0 %, bruitées 12 % | 0 / 0 / 0 |

Notes : (1) `large-v3` complet, Voxtral, Canary et WhisperX **n'ont pas été mesurés** (poids de 3 à 9 Go pour 2,7 Go de disque) ; Voxtral en 8 Go demanderait de la quantification et n'a pas de mots horodatés. (2) Les trois modèles ne produisent **aucun mot sur le silence, le ton pur et l'ambiance des rushes** grâce au VAD (Whisper) ; je n'ai pas testé la musique avec chant ni les rushes parlés. (3) **Horodatage des mots** : disponible pour les deux (Whisper par attention croisée, Parakeet par jeton). Sur la première phrase, Whisper donne « Bienvenue 0,02 s, chez 0,80, Nexora 0,96, Creative 1,34 », Parakeet « 0,16 / 0,64 / 0,88 / 1,60 » : **écarts de 0,1 à 0,3 s entre les deux** ; faute de vérité terrain (les durées de Kokoro auraient pu en servir), la justesse absolue pour couper au montage **n'est pas établie** ; à calibrer sur de vrais plans avant de couper sur le mot. (4) Parakeet GPU : ONNX Runtime 1.31 exige CUDA 13 (`libcublasLt.so.13` absent) : non faisable ici sans installer plus d'un Go. NeMo-Speech.cpp (archives CUDA x86 sm_75+) reste la voie GPU à essayer.

**Le service `/stt` actuel (:8190) ne renvoie pas les mots** : il appelle `m.transcribe(..., vad_filter=True)` sans `word_timestamps=True` et ne garde que `{start, end, text}` par segment (vérifié dans `service.py`). Il faut donc un point `/transcrire`. Il est prêt dans la MR `feat/transcription-gpu-pc5` (non fusionnée) : `deploy/pc5-services/transcrire_endpoint.py` (même format que `transcrire.py` : langue, phrases, mots avec `debutS`/`finS`), client `app/server/nexora/transcriptionGpu.ts` (délai, jamais d'exception), et dans `index.ts` repli automatique sur le CPU quand `NEXORA_TRANSCRIPTION_URL` n'est pas défini ou que le service ne répond pas. **Non appliqué en production** : activer le point sur la VM 204 demande de redémarrer `nexora-services`, décision du fondateur.

**Y a-t-il mieux que Whisper ?** Pour le français, sur ces mesures : non pour la précision (Whisper turbo ≥ Parakeet), **oui pour la vitesse CPU** (Parakeet, 17× contre 1,2 à 2,7× sur les mêmes 4 vCPU), ce qui en fait le meilleur repli si le GPU est indisponible. Résultat à confirmer sur une vraie prise avec bruit et sur un locuteur québécois réel.

## 4. NVENC (priorité 3)

NVENC fonctionne dans la VM en passthrough (FFmpeg 6.1.1, `h264_nvenc` et `hevc_nvenc` ; `av1_nvenc` est listé mais Turing n'a pas d'AV1). Source : 15 rushes H3 de 1344×768 à 24 i/s mis bout à bout (1 860 images, 77,5 s, 7,0 Mb/s). Mesures sans audio, SSIM contre la source, un seul encodage de la source déjà compressée (cas d'un export de montage).

| Encodeur | Réglage | Débit (kb/s) | SSIM | Temps | Vitesse |
|---|---|---|---|---|---|
| x264, VM 4 vCPU | medium CRF 18 | 6 330 | 0,9928 | 27,8 s | 2,8× |
| x264, **pc6** (20 cœurs ARM, charge 18 à 30) | medium CRF 18 | 6 342 | 0,9929 | 27,4 s | 2,8× |
| x264, pc6 | fast CRF 18 | 6 533 | 0,9928 | 19,2 s | 4× |
| x264, pc6 | veryfast CRF 21 | 4 083 | 0,9874 | 12,0 s | 6,5× |
| x264, VM | medium CRF 21 / 24 | 4 412 / 2 936 | 0,9892 / 0,9848 | – | – |
| **h264_nvenc** p4 hq | CQ 19 / 23 / 26 | 8 068 / 5 100 / 3 573 | 0,9924 / 0,9890 / 0,9855 | 4,3 / **2,9** / 2,9 s | **27×** |
| h264_nvenc p7 | CQ 23 | 5 068 | 0,9893 | 7,9 s | 9,8× |
| **hevc_nvenc** p4 | CQ 23 / 27 | 4 302 / 2 611 | 0,9883 / 0,9838 | 3,3 / 3,4 s | 23× |
| hevc_nvenc p7 | CQ 25 | 3 358 | 0,9864 | 6,3 s | 12× |

À débit égal : **HEVC NVENC (0,9883 à 4,3 Mb/s) ≈ x264 medium (0,9892 à 4,4 Mb/s)**, H.264 NVENC demande ≈ 16 % de débit en plus (5,1 Mb/s pour 0,9890). Les cartes 0 et 1 donnent des fichiers **octet pour octet identiques** (même taille et mêmes mesures). Deux encodages simultanés (une par carte) : 5,0 et 5,1 s chacun (le décodage H.264 de la source sur les 4 vCPU devient le goulot). Le décodage matériel (`-hwaccel cuda`) ne gagne rien ici (3,7 contre 2,9 s). Un encodage NVENC pendant qu'un matmul fp16 occupe la même carte : **9,8 s** au lieu de 2,9 s (mon générateur de charge occupe aussi un cœur ; la part GPU et la part CPU n'ont pas été séparées), et le matmul perd 4 % (67,2 contre 69,8 TFLOPS).

**Verdict : OUI** pour les aperçus (veryfast CRF 28 aujourd'hui dans `montage/rendu.ts`) et les livraisons HEVC/H.264 8 bits. **NON** pour ce qui doit rester sur CPU : ProRes (`film.ts`, `hdr.ts`), toute sortie 4:2:2 ou 4:4:4, l'AV1 (absent sur Turing), et l'export « archive » en x264 CRF 12 (`stage.ts`) si la fidélité maximale prime. Les films dont l'export est le dernier goulot de pc6 gagnent un facteur ≈ 10 sur cette étape ; il faut compter le transfert du montage vers pc5 et le retour (≈ 70 Mo pour 77 s, LAN : négligeable). La recette est à écrire côté Creative : un moteur « export » qui appelle un petit serveur FFmpeg sur pc5 (non écrit). Paramètres qui ont servi : `-c:v hevc_nvenc -preset p4 -tune hq -rc vbr -cq 25 -b:v 0 -spatial-aq 1 -temporal-aq 1 -rc-lookahead 20 -bf 3` (les anciens noms de préréglage disparaissent avec le pilote 590+).

## 5. Usage combiné des deux cartes (demande du fondateur)

| Idée | Verdict | Pourquoi (mesuré ou déduit) |
|---|---|---|
| Un LLM de 14 à 24 Md en Q4/Q5 réparti sur 16 Go (llama.cpp `--tensor-split`) | **NON utile ; non mesuré** | Aucun modèle de plusieurs Go n'a pu être téléchargé (2,7 Go libres). Débit borné par la mémoire : au mieux ≈ 416 Go/s ÷ 8,5 Go ≈ 49 jetons/s pour un 14 Md Q4, ≈ 25 pour un 24 Md, **estimations non mesurées**. Le découpage par couches ne transfère que des activations (peu de données) et le lien de 2,3 Go/s suffirait, mais cette solution mobilise les **deux** cartes et bloque tout le reste (Relief, détourage, transcription). Qualité : un 14 à 24 Md local n'égale ni Gemini 4 Argon ni DeepSeek V4.1 pour le réalisateur ; le coût de ces API (0,10 à 1 $ par million de jetons) est négligeable devant l'occupation de deux GPU. |
| ComfyUI MultiGPU (encodeur de texte sur une carte, diffusion sur l'autre) | **NON utile** | Le gain n'existe que si la somme dépasse 8 Go sans qu'un composant seul le dépasse. Qwen-Image 2.1 (20 Md), H3 et TRELLIS.2 fp16 restent hors de portée d'un composant de 8 Go ; sans FP8 ni bf16 les poids int8 sont déjà ce qui tient. Le transfert de plongements est négligeable, mais le chargement de poids sur la carte 0 (3,1 Go/s) coûte. À reconsidérer seulement pour un cas précis (ex. encodeur T5 de 5 Go + petit DiT de 5 Go). |
| Deux files de travaux indépendantes (une par carte) | **OUI, déjà bon, mesuré** | Détourage (carte 1) pendant un matmul fp16 soutenu sur la carte 0 : 70 TFLOPS (la référence), détourage 98,5 s contre 94,5 à 96,3 s seul (+3 à +4 %). Carte 0 : 235 W et 58 °C, 1 591 MHz en moyenne ; carte 1 : 72 W en moyenne, 67 °C au pic. Pas de limite d'alimentation constatée. Non mesuré : les deux cartes à pleine charge et le détourage en même temps (≈ 455 W annoncés, doc `gpu-pc5.md`). Le CPU (4 vCPU) est la ressource qui se partage : 0,38 s par image du détourage et le décodage des exports sont CPU. |

## 6. Plan d'économie de disque (rien appliqué)

État mesuré : `venv` 8,2 Go et `venv-audio` 8,2 Go contiennent **le même torch 2.11.0+cu128** ; `diff -rq` sur `nvidia/` (4,2 Go), `torch/` (1,6 Go) et `triton/` (0,64 Go) : **0 différence**, soit **6,4 Go dupliqués**. Cache HF 7,8 Go : bge-m3 2,9 Go et chatterbox 3,0 Go (**aucun code de Creative ne les appelle**), Whisper turbo 1,6 Go, Kokoro 0,3 Go, HTDemucs 0,08 Go. `venv-banc` 566 Mo (banc, sans service). `/var/cache/apt` 677 Mo, `/home/nexora/.cache` 354 Mo.

| Étape | Gain | Risque |
|---|---|---|
| 1. Dédoublonner par liens physiques les trois dossiers identiques (`jdupes -L -r venv/.../site-packages/{nvidia,torch,triton} venv-audio/.../{nvidia,torch,triton}` ou `cp -al`), même système de fichiers | **≈ 6,4 Go** | nul pour les processus en cours (l'inode reste ouvert) ; à faire avec une copie de sécurité de la liste des fichiers ; ne modifie ni versions ni chemins ; un `pip install` qui réécrirait un fichier le délierait (sans casser l'autre venv) |
| 2. Déplacer bge-m3 et chatterbox sur `/media/pc6/Storage/Nexora/modeles/pc5-cache-hf/` et les recharger à la demande (ou les retélécharger depuis Hugging Face) | ≈ 5,9 Go | casse `/embed` et `/tts?engine=chatterbox` tant qu'ils sont absents ; aujourd'hui sans appelant dans Creative |
| 3. `apt-get clean` | ≈ 0,7 Go | nul |
| 4. Supprimer `venv-banc` s'il est abandonné (à confirmer avec celui qui l'a créé) | 0,57 Go | nul si inutilisé |
| 5. À moyen terme : un seul venv commun pour ComfyUI et les services (`.pth` vers le même `site-packages`, deux jeux de paquets en plus) | encore ≈ 2 à 3 Go de paquets propres | demande de retester ComfyUI et le service audio ; garder les liens physiques tant que ce n'est pas fait |

L'étape 1 seule porte les 2,7 Go libres à ≈ 9 Go, suffisant pour le détourage (poids 2,2 Go, 3 Go de marge) et un cache de modèles de tri des prises.

## 7. Inventaire sans mesure (sources, pas de banc)

Synthèse fidèle au rapport de recherche Codex du 04/11 (`recherche/28-annexes/candidats-synthese.md`), tailles « estimées » = non vérifiées. Constats de la VM : le dossier `models/upscale_models` est **vide** (Real-ESRGAN n'est pas installé malgré la consigne) ; ComfyUI y est en 0.43.2.

| Tâche | Candidat réaliste en 8 Go | Licence des poids | Verdict (non mesuré) |
|---|---|---|---|
| Agrandissement image/vidéo | Real-ESRGAN x2/x4 ou RealPLKSR/SPAN (≈ 30 à 70 Mo), tuilé | BSD / MIT / Apache | oui, simple, sans cohérence temporelle garantie ; SeedVR2-3B Q4 (2 Go) : « non vérifié », expérimental |
| Interpolation | Practical-RIFE 4.25/4.26 (≈ 23 Mo) ; FILM (Apache) en second | MIT / Apache | oui sur la 2080 SUPER ; les nœuds RTX Video Frame Generation exigent RTX 40+, **non** sur Turing |
| Débruitage | `hqdn3d`/`atadenoise` ffmpeg (CPU), FastDVDnet, NAFNet-32 | MIT | oui ; à comparer à l'existant |
| Tri des prises | Qwen3-VL-2B Q8 ou 4B Q4 (vidéo native), SmolVLM2-2.2B, SigLIP 2 base (score par image) | Apache-2.0 | oui probable, **non mesuré** ; Cosmos-Reason2 : accès protégé à accepter, **non contourné** ; MiniCPM-V 4.5 : non, trop gros |
| Voix | Kokoro (mesuré : 0,12 s la phrase), Chatterbox multilingue (2,1 s), Demucs (2,1 s) déjà en place ; Qwen3-TTS-0.6B à tester | Apache / MIT | oui pour l'existant ; Voxtral TTS : poids non ouverts dans le rapport ; Magpie : accès restreint, non contourné |
| NVIDIA RTX Video Super Resolution / Video Effects SDK | – | propriétaire | non vérifié pour Turing sous Linux (documenté Windows RTX20+) ; pas de nœud ComfyUI testé |
| Relief (aperçu, multivue) | déjà en place | – | débit réel **non mesuré** ici ; voir `docs/gpu-pc5.md` (126 s aperçu sur 2080 SUPER, 531 s qualité sur 2070 SUPER) |

## 8. Répartition proposée des rôles et des files

| Carte | Rôle | Files | VRAM résidente |
|---|---|---|---|
| **RTX 2070 SUPER** (x16, 12 Go/s) — « atelier de finition » | Détourage rapide ; transcription (service audio existant + `/transcrire`) ; voix Kokoro/Demucs ; exports NVENC | (a) **interactive** : clic/mot de détourage, transcription (< 5 s), un seul travail à la fois ; (b) **lot** : détourage d'une vidéo, export NVENC, avec priorité inférieure ; l'export est préemptable (arrêt du processus FFmpeg) | 2,8 (détourage) + 2,5 (Whisper) ≈ 5,3 Go sur 8,2 |
| **RTX 2080 SUPER** (x4, 3 Go/s) — « Relief et lots lourds » | Relief 3D (aperçu, multivue, qualité), puis juge de prises (VLM 2 à 4 Md) quand elle est libre | file ComfyUI 8188 inchangée ; le tri des prises passe après | TRELLIS.2 aperçu 7,2 Go : la carte est pleine pendant un job |

Pourquoi : la 2070 SUPER a le meilleur lien PCIe et porte déjà les services audio ; la 2080 SUPER, limitée à x4, ne convient qu'à des travaux longs dont les poids restent résidents. Le Relief « qualité » reste sur la GB10 (531 s sur 2070 contre 162 s).

## 9. Ce qu'il faut changer dans Creative pour l'utiliser

1. **Transcription** : MR `feat/transcription-gpu-pc5` ; variable `NEXORA_TRANSCRIPTION_URL=http://192.168.1.124:8190` sur la VM 202 ; côté VM 204, installer `transcrire_endpoint.py` dans `service.py` puis redémarrer `nexora-services` (fenêtre sans Relief ni audio en cours).
2. **Détourage** : variables §2 et entrée `NEXORA_MOTEURS_GPU` ; `secondes` de la recette `detourage-rapide` ; ouvrir le port au pare-feu de la VM 204 ; image : le `Dockerfile` existant avec `TORCH_INDEX=cu128 TORCH_VERSION=2.11.0 TORCHVISION_VERSION=0.26.0`, manifeste prêt dans `deploy/pc5-gpu/detourage-2070s.yaml`.
3. **Exports** : un serveur FFmpeg NVENC (non écrit) et une recette « export » dans `NEXORA_MOTEURS_GPU` ; passer `montage/rendu.ts` et `film.ts` (livraison) sur HEVC/H.264 NVENC quand le moteur est disponible, x264 en repli.
4. **Registre de ressources** : ajouter la carte 1 à `docs/RESSOURCES.md` §8 comme « atelier de finition » après décision.

## 10. Ce que je n'ai pas pu vérifier

- Qualité sur **vraie parole**, bruitée, spontanée, québécoise ; justesse absolue des horodatages de mots ; hallucinations sur musique avec chant.
- `large-v3`, Voxtral, Canary, WhisperX, NeMo-Speech.cpp (GPU) : faute de disque et d'économie.
- Agrandissement, interpolation, débruitage, tri des prises par VLM, Qwen3-TTS, RTX Video SDK : seulement le rapport de recherche.
- LLM réparti sur deux cartes : débit et qualité non mesurés (estimations flagrantes).
- Durée du détourage sur les 224 images complètes (disque) ; coût mémoire exact avec ComfyUI ×2 sous charge (la RAM de la VM était libre pendant les essais).
- L'effet de gpu-unlock modèle par modèle : il n'est pas possible de le désactiver sans redémarrer la VM et les services ; seules les mesures matmul avant/après du 04/11 (45 → 70 TFLOPS en fp16 accumulé en fp32) valent.
- Le comportement de NVENC avec le pilote 590+ pour d'anciens préréglages, et les limites de sessions (non lues).

## 11. Nettoyage

Dossier d'essai `/srv/nexora-gpu/essais-20261104/` supprimé en fin de travail (uniquement ce qui m'appartient) ; unités `essai-detourage-20261104*` arrêtées ; poids téléchargés effacés ; copies temporaires côté pc6 sous `/media/pc6/Storage/Nexora/travail/gpu-pc5-essais/` effacées. L'état de la VM après nettoyage est donné dans le compte rendu.
