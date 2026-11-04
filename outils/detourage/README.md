# Détourage vidéo de Nexora Creative : serveur GPU

Palier **rapide** : SAM 2.1 (clic, suivi, occlusions), ViTMatte (bords), stabilisation par flux optique, sorties alpha PNG 16 bits, EXR, ProRes 4444, WebM alpha, composite. Recherche, licences et mesures : `recherche/22-detourage-video-pro.md`. Le serveur de Creative (`app/server/nexora/detourage/`) le pilote ; l'interface est la page `/detourage`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `noyau.py` | mathématique pure : segments, rampes de raccord, trimap, fusion, avant-plan, flux, stabilisation |
| `ecriture.py` | écrivains PNG 16 bits et EXR demi-flottant ZIP, relecture de contrôle |
| `modeles.py` | SAM 2.1 et ViTMatte (transformers), aperçu d'une image, suivi d'un segment |
| `traitement.py` | chaîne reprenable (clés de contenu), occlusions, coupures de plan, sorties, contrôle |
| `serveur.py` | HTTP : `/sante`, `/segmenter`, `/travaux/<id>/…` |
| `verifier.py` | relecture indépendante (OpenEXR, OpenCV, ffprobe) et mesure des raccords |
| `planche.py` | planche de contrôle : source, matte, composite, zoom ×4 sur le bord |
| `tests/` | 22 tests (`python -I -c "import sys,unittest;sys.path[:0]=['.','<pylibs>'];unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('tests'))"` depuis ce dossier) |

## Installer sur une machine GPU (sans toucher au ComfyUI en place)

1. Un Python avec `torch >= 2.5` (CUDA), `transformers >= 5`, `numpy`, `Pillow` : sur la GB10, le `venv` de ComfyUI convient (rien n'y est installé).
2. Bibliothèques en plus, dans un dossier à part : `python -m pip install --target <poids>/pylibs opencv-python-headless OpenEXR` (OpenEXR ne sert qu'aux contrôles).
3. Poids libres, sans compte ni jeton : `HF_HOME=<poids>/hf` puis `huggingface_hub.snapshot_download` de `facebook/sam2.1-hiera-large`, `facebook/sam2.1-hiera-small`, `hustvl/vitmatte-small-composition-1k`, `hustvl/vitmatte-base-composition-1k` (1,5 Go ; le serveur travaille hors ligne : `HF_HUB_OFFLINE=1`).
4. `ffmpeg` avec `prores_ks`, `libvpx-vp9`, `libx264`, `exr` (`FFMPEG_BIN`).
5. Lancer : `NEXORA_DETOURAGE_PORT=8231 python -I outils/detourage/serveur.py` ou le service `deploy/gb10/nexora-detourage.service`.
6. Variables : `NEXORA_DETOURAGE_DOSSIER` (travaux), `NEXORA_DETOURAGE_POIDS`, `NEXORA_DETOURAGE_PORT`, `NEXORA_DETOURAGE_HOTE` (127.0.0.1 par défaut : le serveur n'a pas d'authentification, ne pas l'ouvrir au réseau).

## Brancher sur Creative

Moteur principal : `NEXORA_DETOURAGE_URL=http://127.0.0.1:8231` dans l'environnement du serveur Creative. Autre machine : champ `"detourageUrl"` d'une entrée de `NEXORA_MOTEURS_GPU` avec `"detourage-rapide"` dans ses `recettes`. Depuis la VM 202, un tunnel SSH par moteur (comme pour ComfyUI) : unité `deploy/proxmox/nexora-tunnel.service.modele`, `permitopen="127.0.0.1:8231"` dans les `authorized_keys` côté GPU.

## Pc3 (RTX 5080) : ce qu'il faut me donner

Je n'ai pas d'accès SSH à pc3 (la clé de pc6 est refusée) et je n'ai rien tenté d'autre. Il faut, au choix : (a) ajouter la clé publique de pc6 (`~/.ssh/id_ed25519.pub`) aux `authorized_keys` d'un utilisateur de pc3, ou (b) me donner un alias SSH déjà valable ; puis confirmer (1) que ComfyUI et le modèle en cours sur la 5080 peuvent être **arrêtés** (pas supprimés) le temps des essais, (2) le dossier de travail (≥ 3 Go libres pour les poids rapide, davantage pour le pro : 21,5 Go de modèle + 15,4 Go d'encodeur), (3) la version de Python et de CUDA. Les poids du palier pro ne seront téléchargés qu'après acceptation des formulaires Hugging Face par le fondateur (jeton de lecture fourni par lui).

## Disque

≈ 0,08 Go par seconde de vidéo à 720p (images, masques, sorties ; proportionnel aux pixels). Le serveur refuse un travail qui laisserait moins de 3 Go libres ; Creative limite un travail à 120 s par défaut (`NEXORA_DETOURAGE_SECONDES_MAX`). Pour des plans plus longs, installer le serveur sur une machine avec du disque (pc1, pc3).

## Limites connues

Le sujet qui ressort après une longue occlusion **au milieu d'un raccord de segments** n'est retrouvé que par un nouveau clic ; un plan sans clic donne un masque vide (signalé) ; pas de sélection par texte (SAM 3 protégé) ; flux optique et écriture des images sur CPU (0,26 s par image à 720p) ; pas de palier pro.
