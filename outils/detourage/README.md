# Détourage vidéo de Nexora Creative : serveur GPU (pc3)

Serveur qui détoure une vidéo : sélection du sujet au clic, à la boîte ou par un mot, suivi image par image, bords affinés par ViTMatte, stabilisation par flux optique, sorties alpha PNG 16 bits, RGBA, EXR, ProRes 4444, WebM alpha, matte et composite. Il tourne en production sur la RTX 5080 de pc3, dans un pod k3s ; le serveur de Creative (`app/server/nexora/detourage/`) le pilote comme un moteur et la page `/detourage` l'utilise. Recherche, licences et mesures : `recherche/22-detourage-video-pro.md`.

État au 04/11/2026 : palier **rapide** en production (SAM 3.1 + ViTMatte, pod `detourage`) ; palier **pro** installé et essayé (ComfyUI + LTX-2.5 22B + IC-LoRA Alpha-Gen, pod `comfyui-pro` à 0 : meilleur que le rapide sur le verre seulement) ; V100 validée techniquement, pas en production.

## Fichiers

| Fichier | Rôle |
|---|---|
| `noyau.py` | mathématique pure : segments, rampes de raccord, trimap, fusion, avant-plan, flux, stabilisation |
| `ecriture.py` | écrivains PNG 16 bits et EXR demi-flottant ZIP, relecture de contrôle |
| `modeles.py` | modèles du palier rapide : SAM 3.1 (par `sam31.py`) et ViTMatte (transformers), aperçu d'une image, suivi d'un segment |
| `sam31.py` | SAM 3.1 : clic, boîte, mot, suivi avant et arrière, par le code SAM 3 de ComfyUI utilisé comme bibliothèque (aucun second serveur) |
| `acces.py` | contrôle d'accès : liste d'adresses, jeton partagé en temps constant, refus de démarrer en écoute réseau sans les deux |
| `traitement.py` | chaîne reprenable (clés de contenu), occlusions, coupures de plan, sorties, contrôle |
| `serveur.py` | HTTP : `/sante`, `/segmenter`, `/texte`, `/travaux/<id>/…` ; prise Unix d'administration locale |
| `verifier.py` | relecture indépendante (OpenEXR, OpenCV, ffprobe) et mesure des raccords |
| `planche.py` | planche de contrôle : source, matte, composite, zoom ×4 sur le bord |
| `banc.py` | banc des cinq clips de mesure (mêmes clics que la GB10), mesures du serveur et VRAM vue par `nvidia-smi` |
| `modeles_manifeste.py` | manifeste des poids : `decrire`, `verifier` (sha256), `telecharger` |
| `verite/` | vérité terrain : scènes Blender (`scene_blender.py`), composition sur un vrai fond (`composer.py`), notes SAD, MSE, Grad, dtSSD (`noter.py`), banc (`banc_verite.py`) |
| `pro/` | palier pro : image ComfyUI + ComfyUI-LTXVideo, graphes API, `modeles-pro.json`, `telecharger_pro.py`, `executer_pro.py` |
| `Dockerfile` | image du serveur : torch (index CUDA choisi), ComfyUI épinglé comme bibliothèque, ffmpeg |
| `requirements.txt` | versions épinglées hors torch et torchvision |
| `tests/` | 27 tests (`python -I -c "import sys,unittest;sys.path[:0]=['.','<pylibs>'];unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('tests'))"` depuis ce dossier) |

## Installation en pod (production, `deploy/k8s/detourage/`)

Prérequis : pc3 nœud agent k3s (contrôle sur pc1), opérateur GPU NVIDIA, `kubectl` sur le poste de travail, alias SSH de pc3 (défaut `pc3-agent`, variable `PC3`). Rien n'est installé sur l'hôte : ni démon Docker, ni root.

| Fichier | Contenu |
|---|---|
| `00-namespace.yaml` | namespace `nexora` |
| `10-registre-provisoire.yaml` | registre d'images provisoire, `127.0.0.1:5000` sur pc3, htpasswd, stockage `~/nexora-detourage/k8s/registre` |
| `20-construction-kaniko.yaml` | Job de construction d'image (kaniko), sans démon ni root |
| `30-detourage.yaml` | serveur de détourage : 1 GPU, hostPort 8231 sur 192.168.1.126, Service ClusterIP, NetworkPolicy |
| `40-comfyui-pro.yaml` | ComfyUI du palier pro, `replicas: 0` par défaut (la 5080 est attribuée en entier : rapide et pro ne tournent pas ensemble) |
| `50-poids-webdav.yaml` | poids servis en lecture seule à la VM V100 (`rclone serve webdav`, `127.0.0.1:8095`) |
| `construire.sh` | construit et pousse l'image : `construire.sh <cu130\|cu126> [tag] [contexte] [image]` |
| `modeles.json` | manifeste des poids du palier rapide (ViTMatte : révisions, tailles, sha256) |

Ordre d'installation :

1. **Secrets, hors git, jamais de valeur en argument** (coller la valeur sur l'entrée standard ; `--from-file=clé=/dev/stdin` évite l'historique du shell et la ligne de commande) :
```
kubectl -n nexora create secret generic detourage-jeton    --from-file=jeton=/dev/stdin
kubectl -n nexora create secret generic registre-htpasswd  --from-file=htpasswd=/dev/stdin
kubectl -n nexora create secret generic registre-tirage    --type=kubernetes.io/dockerconfigjson --from-file=.dockerconfigjson=/dev/stdin
kubectl -n nexora create secret generic poids-webdav       --from-file=mdp=/dev/stdin
```
   Le jeton du serveur fait au moins 32 caractères ; le mot de passe WebDAV est collé sans saut de ligne final ; le fichier htpasswd est produit localement (`htpasswd -B`) puis passé sur l'entrée standard. Le jeton Hugging Face du palier pro n'est pas un Secret k8s : il reste un fichier mode 600 sur pc3 (`~/nexora-detourage/secrets/hf-token`), lu par `HF_TOKEN_PATH`, jamais affiché.
2. `kubectl apply -f deploy/k8s/detourage/00-namespace.yaml -f deploy/k8s/detourage/10-registre-provisoire.yaml`.
3. Poids du palier rapide, hors image : `python -I modeles_manifeste.py telecharger ~/nexora-detourage/modeles deploy/k8s/detourage/modeles.json`, puis `verifier`. SAM 3.1 et les poids pro : `python -I pro/telecharger_pro.py pro/modeles-pro.json ~/nexora-detourage/modeles rtx5080 sam3.1` avec `HF_TOKEN_PATH` (fichier mode 600).
4. Image : `deploy/k8s/detourage/construire.sh cu130 <tag>` (ou `cu126` pour la V100), puis remplacer `__TAG__` dans `30-detourage.yaml` et appliquer. Le premier chargement des modèles en pod passe par le disque local.
5. `kubectl apply -f deploy/k8s/detourage/30-detourage.yaml` ; vérifier `/sante` avec le jeton.
6. Facultatif : `50-poids-webdav.yaml` (VM V100), `40-comfyui-pro.yaml` (palier pro, `replicas: 0`).

Le registre est **provisoire** : il sera retiré quand les images partiront au registre commun (`kubectl -n nexora delete -f deploy/k8s/detourage/10-registre-provisoire.yaml`).

## Installation native de secours (`deploy/pc3/`)

C'est l'installation de départ (venv uv Python 3.12), arrêtée après validation du pod ; les scripts restent pour un dépannage sans k3s.

| Fichier | Rôle |
|---|---|
| `demarrer.sh` | lance `superviser.sh` détaché de la session SSH (idempotent) |
| `superviser.sh` | relance `serveur.py` 5 s après un arrêt anormal ; ne tue que son enfant |
| `arreter.sh` | arrêt par fichier PID, aucun `pkill` |
| `detourage.env` | port 8231, écoute 192.168.1.126, client autorisé 192.168.1.122, aucun secret (le jeton est dans `secrets/jeton`, mode 600) |
| `nexora-detourage.service` | unité systemd utilisateur ; utile seulement avec `loginctl enable-linger pc3` (à faire par le fondateur) |

Le code est copié dans `~/nexora-detourage/code/detourage`, les poids dans `~/nexora-detourage/modeles`, les travaux dans `~/nexora-detourage/travaux`, ffmpeg dans `~/nexora-detourage/ffmpeg`.

## Brancher Creative

- `NEXORA_DETOURAGE_URL=http://192.168.1.126:8231` et `NEXORA_DETOURAGE_JETON=<jeton>` dans `/etc/nexora/creative.env` de la VM 202 ; `/api/nexora/etat` répond alors `detourage: true`.
- Le serveur n'accepte que les adresses de `NEXORA_DETOURAGE_AUTORISES` (`192.168.1.122`, la VM 202) et exige `Authorization: Bearer <jeton>` à chaque requête, comparé en temps constant. Il refuse de démarrer en écoute réseau sans jeton ni liste d'adresses.
- Deux verrous réseau en plus : le hostPort n'est lié qu'à l'adresse LAN de pc3 (ni Tailscale ni boucle locale) et la NetworkPolicy n'ouvre l'entrée qu'à `192.168.1.122/32`.
- Vérification de bout en bout depuis la VM 202 : `deploy/proxmox/verifier-detourage.mts` (santé, aperçu d'un clic, dépôt, travail complet, téléchargement des sorties, nettoyage). Déploiement du code : `deploy/proxmox/mettre-a-jour-creative.sh`.
- Administration locale (bancs, contrôles) par la prise Unix : `~/nexora-detourage/secrets/detourage.sock` hors pod, `/tmp/detourage.sock` dans le pod (`kubectl exec`).

Matrice d'accès vérifiée :

| Depuis | Résultat |
|---|---|
| VM 202 avec le jeton | 200 |
| VM 202 sans jeton | 401 |
| pc6 | coupé (NetworkPolicy) |
| pc3 lui-même, VM V100 | 403 (la VM V100 sort par NAT avec l'adresse de pc3, absente de la liste) |
| Tailscale, boucle locale | rien n'écoute |

## Modèles

| Modèle | Dépôt, révision | Taille | Emplacement | Licence |
|---|---|---|---|---|
| SAM 3.1 (Object Multiplex) | Comfy-Org/sam3.1, `7bb8374…` ; `checkpoints/sam3.1_multiplex_fp16.safetensors`, sha256 vérifié | 1,75 Go | `modeles/pro/Comfy-Org/sam3.1/` | licence SAM de Meta, jointe au dépôt |
| ViTMatte base (défaut) et small | hustvl/vitmatte-*-composition-1k | 0,49 Go | `modeles/hf/` (`HF_HOME`) | Apache-2.0 |

Manifeste du palier rapide : `deploy/k8s/detourage/modeles.json` (révisions, tailles, sha256) ; palier pro : `pro/modeles-pro.json`. Outils : `modeles_manifeste.py decrire|verifier|telecharger` et `pro/telecharger_pro.py` (jeton lu par `HF_TOKEN_PATH`, jamais affiché).

SAM 3.1 est utilisé par le code SAM 3 de ComfyUI v0.44.0 appelé comme bibliothèque (`sam31.py`) : pas de serveur ComfyUI pour le rapide, un seul processus tient le GPU. Sélection au clic, à la boîte ou par un mot (en anglais), suivi avant et arrière. Les anciens noms `large` et `small` envoyés par d'anciens clients désignent désormais SAM 3.1.

### Retiré le 04/11/2026 (SAM 2.1)

- **Quoi** : SAM 2.1 hiera-large et hiera-small, code de repli compris. Consigne du fondateur.
- **Où** : poids supprimés sur pc3 (`~/nexora-detourage/modeles/hf`) et sur pc6 (`~/nexora-creative-data/models/detourage/hf`, blobs 1,08 Go et cache `xet`). `modeles.json` ne décrit plus que ViTMatte.
- **Conséquence** : le suivi du palier rapide est celui de SAM 3.1 ; les mesures de qualité à vérité terrain (recherche/22 §9) ont été faites avec SAM 2.1, sans nouveau banc comparatif (consigne du fondateur).

## V100 (Tesla 16 Go, sm_70) : état et ce qu'il manque

- Validé techniquement dans la VM qemu `pc3-v100-vm` (pilote 580.178) : torch 2.14.1 cu126 (les roues cu128 et cu130 n'ont plus sm_70), fp16, SAM 3.1 et ViTMatte tournent, chaîne complète à 0,84 s par image (188,7 s pour 224 images).
- `~/nexora-detourage-v100/` dans la VM : venv local (7,1 Go), ffmpeg, poids montés depuis pc3 par `rclone mount` (WebDAV du pod `poids-webdav`) au lieu d'être copiés.
- **Pas en production** : la VM 202 ne peut pas joindre la VM V100 (réseau qemu « user » : NAT, joignable seulement par SSH 127.0.0.1:22223 sur pc3). Il manque, au choix, un `hostfwd=tcp:192.168.1.126:8232-:8231` sur le netdev de la VM (redémarrage de la VM) ou une interface pontée sur le LAN ; avec la future plateforme (Proxmox sur pc3), une VM ou un nœud avec la V100 et sa propre adresse. Image : même `Dockerfile` avec `TORCH_INDEX=cu126`.
- Rôle visé : le rapide sur la V100, le pro sur la 5080.

## Palier pro

- Poids officiels téléchargés sur pc3 (`~/nexora-detourage/modeles/pro/`, 38,7 Go) et vérifiés contre les métadonnées LFS : LTX-2.5 22B distilled nvfp4 (18,72 Go), encodeur Gemma 4 12B int8 (15,37 Go), VAE vidéo, VAE vidéo conv, VAE audio, IC-LoRA Alpha-Gen (1,31 Go).
- ComfyUI démarre dans le pod sur la 5080 (15,8 Go de VRAM vus, DynamicVRAM, 1091 nœuds, poids visibles) ; graphe API dans `pro/executer_pro.py`, d'après le flux officiel V2V IC-LoRA Single Stage Distilled.
- Essai du 04/11 sur la 5080 (nvfp4, LoRA 1,0, 8 pas distillés, `executer_pro.py`) : fonctionne ; 25 images en 1280×736 en 18 à 20 s une fois les poids en mémoire (0,73 à 0,8 s par image ; premier passage 768×448 avec chargement : 34,4 s), 97 images en 88,3 s (0,91 s par image) ; VRAM pleine (15,3 à 16,1 Go, déchargement dynamique en RAM) ; RAM de pc3 au pic 29,2 Go sur 30 (pod 14,8 Go) : 1920×1088 ou 145 images saturerait pc3 tant que la VM V100 garde ses 14 Go. Qualité à vérité terrain (SAD de bande, 25 images, 1280 px) : le pro choisit seul l'avant-plan et prend le personnage du fond de Sintel (fourrure brute 123, ignorée) ; guidé par notre masque SAM (hors sujet remplacé par du gris), il donne **verre 19,4 contre 102,8 pour le rapide (5 fois mieux)**, mais **fourrure 22,5 contre 6,05** et **fumée 35,4 contre 6,59** (moins bien). Scènes de synthèse : le modèle est entraîné sur des prises réelles, à revérifier sur de vrais plans.
- Usage recommandé : le pro pour les sujets transparents ou réfractifs (verre, eau), toujours guidé par le masque SAM 3.1 du sujet ; le rapide pour le reste. La politique de licences de Creative bloque LTX-2.x : brancher le pro dans Creative est une décision du fondateur.
- R9700 (pc4, 32 Go, RDNA4) : à évaluer, rien n'est installé.

## Disque

≈ 0,08 Go par seconde de vidéo à 720p (images, masques, sorties ; proportionnel aux pixels). Le serveur refuse un travail qui laisserait moins de 3 Go libres ; Creative limite un travail à 120 s par défaut (`NEXORA_DETOURAGE_SECONDES_MAX`). Sur pc3 : poids 0,49 Go (rapide) + 40,4 Go (pro, dont SAM 3.1), registre provisoire 8,4 Go, travaux sous `~/nexora-detourage/k8s/travaux` et `k8s/travaux-pro`.

## Limites connues

- SAM 3.1 : le suivi part d'**un masque initial par segment** ; les autres clics du segment ne servent qu'à l'image où ils sont posés, et les masques suivis sont binaires.
- Le **verre transparent** échoue avec toutes les variantes rapides (SAD ≈ 100 : le sujet est rendu opaque) ; c'est le cas d'usage du palier pro.
- Le mot de sélection est en **anglais**.
- Le sujet qui ressort après une longue occlusion **au milieu d'un raccord** n'est retrouvé que par un nouveau clic ; un plan sans clic donne un masque vide (signalé).
- Flux optique et écriture des images sur CPU (0,26 s par image à 720p).
- Palier pro : pas encore branché dans Creative (politique de licences, décision du fondateur) ; il ne choisit pas le sujet (guidage par masque obligatoire) ; ≤ 145 images et ≤ 1920×1088 par passe ; sur pc3, il ne tourne pas en même temps que le rapide.
