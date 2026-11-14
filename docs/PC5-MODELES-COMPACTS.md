# Modèles compacts Nexora — PC5 / VM 204

État revérifié le 14 novembre 2026, 06:07 UTC. La cible durable est la VM GPU 204 sur PC5.

## Règle permanente du fondateur

Tous les poids compacts qui peuvent être utilisés individuellement par l’une des deux cartes GPU PC5 doivent être stockés dans cette VM, même si l’ensemble dépasse la VRAM disponible. Les services chargent seulement le modèle demandé au moment du travail; une seule carte est réservée par essai. Éviter les poids en double ailleurs. Un fichier présent ne signifie pas que Creative l’intègre ou que ses performances sont vérifiées. Garder les modèles trop grands sur leurs moteurs dédiés ou le cloud selon le choix du fondateur.

L’objectif actif de centralisation PC5 contient déjà cette règle. Cette page est le repère durable pour les prochaines sessions.

## Contenu vérifié

- models/nexora-local-small/INVENTAIRE.csv : 142 fichiers, tous présents.
- models/nexora-candidates/INVENTAIRE-CANDIDATS.csv : 73 entrées / 15 108 667 783 octets, toutes présentes; les candidats couvrent speech, vision et restauration vidéo.
- MuseTalk 1.5 : 18 fichiers / 5 970 975 309 octets sous /srv/nexora-gpu/models/nexora-sync/MuseTalk.
- LatentSync 1.5 : 15 fichiers officiels Hugging Face à la révision 32a20d29aead0498e3e885e90dbbe8027da1b61b, plus les 3 fichiers du VAE stabilityai/sd-vae-ft-mse à la révision 31f26fdeee1355a5c34592e401dd41e45d25a493. Total vérifié : 18 fichiers / 10 156 719 188 octets; manifeste nexora-sync/LatentSync-1.5/INVENTAIRE-MODELES.csv. Aucun fichier absent, aucune taille erronée et aucun .part.
- faster-whisper large-v3-turbo : déjà présent dans le cache HF central de la VM; model.bin 1 617 884 929 octets et SHA-256 officiel e76620f83d5f5b69efd3d87e3dc180c1bd21df9fbebacfd4335e5e1efcc018da. Aucun doublon téléchargé.
- Les poids de services locaux (BGE-M3, Kokoro, Chatterbox, HTDemucs, BiRefNet, SAM 3.1, ViTMatte, Mesh/TRELLIS, etc.) étaient déjà présents selon le catalogue /srv/nexora-gpu/MODELES-LOCAL-PC5.md.

## Ressources et limites

Le volume Sync dédié de VM204 (/dev/sdb, monté sur /srv/nexora-gpu/models/nexora-sync) a été étendu de 8 à 20 Gio, puis ext4 a grandi en ligne. Après le transfert : 16 Gio utilisés, 4,5 Gio libres (78 %). Le disque candidats reste 16 Gio (15 Gio utilisés, 1,6 Gio libres); la racine reste 69 Gio (65 Gio utilisés, 4,6 Gio libres). Le pool ssd-1tb de PC5 est à 93,54 %, avec 61 828 662 KiB disponibles au relevé.

Les files ComfyUI 8188/8189 répondaient 200 avec 0 en cours et 0 en attente; les GPU affichaient 0 % d’utilisation et 312/224 Mio résidents. Aucun ComfyUI n’a été redémarré et aucune inférence n’a été lancée.

## État d’intégration

LatentSync 1.5 est préparé sur disque seulement. Le runtime n’est pas installé, Creative ne l’appelle pas encore et aucune qualité/durée n’a été mesurée. Le dépôt officiel annonce 8 Gio minimum; les deux cartes PC5 en ont 8 Gio chacune, donc tester sur une seule carte réservée avant de le déclarer utilisable. LatentSync 1.6 (18 Gio minimum), MiniMax H3 et les gros modèles vidéo demeurent sur leurs moteurs dédiés ou le cloud.

RIFE 4.7 est aussi présent dans les candidats, mais le nœud RIFE VFI manque aux deux workers ComfyUI; le poids reste non intégrable jusqu’à une maintenance Comfy planifiée.

### Vérification des sources PC1 et PC3 — 14 novembre 2026

- Confirmation du fondateur : tous les petits modèles qui fonctionnent individuellement sur un GPU PC5 restent stockés dans VM204, même si leur total dépasse la VRAM. Chaque carte a 8 Gio, non combinés automatiquement; charger le modèle requis à la demande et réserver une carte par essai.
- Les manifestes vérifiés couvrent 142 fichiers local-small, 73 candidats, 18 MuseTalk et 18 LatentSync 1.5 + VAE. Les dossiers PC5 ont été revus; aucune famille compacte admissible manquante n’a été identifiée.
- Inventaire en lecture seule du dossier MiniMax H3 de PC1 : poids H3 de 22,89 et 13,61 Go, encodeur Qwen3-VL 32B de 15,69 Go. MiniMax Music 3 comprend un DiT de 2,50 Go, mais son encodeur int8 fait 9,20 Go et les nœuds nécessaires manquent; le DiT seul n’est pas fonctionnel. Aucun de ces composants n’a été copié.
- SAM 3.1 et ViTMatte small/base connus sur PC3 sont déjà dans VM204. L’accès PC3 par le NAT documenté a refusé la connexion; VM205 demeure à vérifier sans contourner son empreinte SSH. PC6 n’a pas été consulté. Aucun modèle n’a été chargé, copié ou supprimé pendant ce relevé. Les copies BGE-M3/Whisper Medium restent jusqu’à migration vérifiée.
- GPU VM204 au contrôle : RTX 2080 SUPER 312 Mio, RTX 2070 SUPER 224 Mio, 0 % chacune; aucun service redémarré.

### Vérification physique des manifestes et services — 14 novembre 2026

Comparaison live des chemins CSV avec le système de fichiers : local-small 142/142 présents, candidats 71/71, MuseTalk 18/18, LatentSync 1.5 + VAE 18/18; zéro fichier listé manquant. À cet instant, Comfy 8188/8189 et nexora-services 8190 répondent 200; files 0/0; Ollama /api/ps est vide; les RTX 2080 SUPER et 2070 SUPER affichent 312/224 Mio et 0 %. Les services écoutent sur l’adresse LAN.

### Modèles voix compacts centralisés — 14 novembre 2026

Inspection ciblée de la cache voix active de PC1 : les sept paquets suivants ont été copiés dans VM204, en conservant les sources PC1 intactes : Qwen3-TTS 1.7B Base, Qwen3-TTS 1.7B VoiceDesign, XTTS-v2, F5-TTS Québec + Vocos, Chatterbox Multilingual V2, Chatterbox Multilingual V3 et Chatterbox English. L’inventaire `docs/PC5-VOIX-COMPACTES.tsv` liste 64 chemins (21 101 440 506 octets logiques); le manifeste PC1 et les fichiers VM204 concordent par SHA-256.

Le volume voix de 16 Gio est monté sur `/srv/nexora-gpu/models/nexora-voice-models` (1 102 569 472 octets disponibles au contrôle). XTTS-v2 et le poids T3 propre à V3 résident sur la racine de VM204 puis sont liés depuis leurs chemins de modèles; les deux modèles Qwen 1.7B partagent le tokenizer déjà centralisé du 0.6B. Tous les modèles restent inactifs, prêts à être sélectionnés un à la fois. Aucun test GPU n’a validé la VRAM, la vitesse ou la qualité; V3 et English ne sont pas encore intégrés au moteur Creative.

État live après copie : les services GPU répondent, les files Comfy sont vides et les deux GPU sont au repos. L’espace libre est de 5 231 235 072 octets sur `/`, 4 794 101 760 sur Sync, 1 604 071 424 sur candidats et 1 102 569 472 sur voix. Les paquets ont été sélectionnés pour une tentative individuelle sur une carte de 8 Gio; cela ne vaut pas preuve d’exécution GPU.


### Transfert des dépendances compactes de Sync — 14 novembre 2026, 06:07 UTC

### Centralisation PC1 → VM204 — 14 novembre 2026, 06:07 UTC

- Le fondateur confirme la règle permanente : stocker dans VM204 tous les petits modèles utilisables individuellement par un GPU PC5, même si la somme dépasse la VRAM; charger uniquement ceux requis et réserver une carte par essai.
- Copie depuis l’arbre actif PC1 `NexoraStudioWork`, sans supprimer ni modifier la source, vers `/srv/nexora-gpu/models/nexora-candidates/vision/insightface/buffalo_l/` : `2d106det.onnx` (5 030 888 octets, SHA-256 `f001b856447c413801ef5c42091ed0cd516fcd21f2d6b79635b1e733a7109dbf`) et `det_10g.onnx` (16 923 827 octets, SHA-256 `5838f7fe053675b1c7a08b633df49e7af5495cee0493c7dcf6697200b85b5b91`). Hashes source/destination identiques; une ligne par fichier dans le manifeste.
- Le manifeste candidats compte 73 poids / 15 108 667 783 octets; les 73/73 chemins et tailles concordent. `sfd_face.pth`, `whisper/tiny.pt` et les auxiliaires `s3fd` de MuseTalk étaient déjà présents. Aucun autre modèle compact complet manquant n’a été repéré dans les dossiers actifs PC1 examinés; archives/sauvegardes PC1 non couvertes.
- Hunyuan Paint reste exclu en pièces détachées : son pipeline demande au moins 21 Gio de VRAM; LatentSync 1.6 demande 18 Gio minimum. Les lots incomplets ne constituent pas un modèle utilisable sur une carte PC5 de 8 Gio.
- Après copie : services actifs; endpoints LAN 8188/8189/8190/11434 HTTP 200; files Comfy 0/0; Ollama sans modèle chargé; GPU à 0 %, 312/224 Mio. Aucun redémarrage ni essai d’inférence. Le volume candidats utilise 15 109 046 272 octets et en garde 1 604 071 424 libres (91 %); Sync garde 4 794 101 760 octets libres; la racine 9 461 444 608.
- PC3 et VM205 demeurent non vérifiés sans validation indépendante de leurs clés SSH; PC6/VM206 hors périmètre.
