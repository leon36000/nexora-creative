# Modèles compacts Nexora — PC5 / VM 204

État vérifié le 13 novembre 2026, 22:52, heure de Montréal. La cible durable est la VM GPU 204 sur PC5.

## Règle permanente du fondateur

Tous les poids compacts qui peuvent être utilisés individuellement par l’une des deux cartes GPU PC5 doivent être stockés dans cette VM, même si l’ensemble dépasse la VRAM disponible. Les services chargent seulement le modèle demandé au moment du travail; une seule carte est réservée par essai. Éviter les poids en double ailleurs. Un fichier présent ne signifie pas que Creative l’intègre ou que ses performances sont vérifiées. Garder les modèles trop grands sur leurs moteurs dédiés ou le cloud selon le choix du fondateur.

L’objectif actif de centralisation PC5 contient déjà cette règle. Cette page est le repère durable pour les prochaines sessions.

## Contenu vérifié

- models/nexora-local-small/INVENTAIRE.csv : 142 fichiers, tous présents.
- models/nexora-candidates/INVENTAIRE-CANDIDATS.csv : 71 entrées, toutes présentes; les candidats couvrent speech, vision et restauration vidéo.
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
- Les manifestes vérifiés couvrent 142 fichiers local-small, 71 candidats, 18 MuseTalk et 18 LatentSync 1.5 + VAE. Les dossiers PC5 ont été revus; aucune famille compacte admissible manquante n’a été identifiée.
- Inventaire en lecture seule du dossier MiniMax H3 de PC1 : poids H3 de 22,89 et 13,61 Go, encodeur Qwen3-VL 32B de 15,69 Go. MiniMax Music 3 comprend un DiT de 2,50 Go, mais son encodeur int8 fait 9,20 Go et les nœuds nécessaires manquent; le DiT seul n’est pas fonctionnel. Aucun de ces composants n’a été copié.
- SAM 3.1 et ViTMatte small/base connus sur PC3 sont déjà dans VM204. L’accès PC3 par le NAT documenté a refusé la connexion; VM205 demeure à vérifier sans contourner son empreinte SSH. PC6 n’a pas été consulté. Aucun modèle n’a été chargé, copié ou supprimé pendant ce relevé. Les copies BGE-M3/Whisper Medium restent jusqu’à migration vérifiée.
- GPU VM204 au contrôle : RTX 2080 SUPER 312 Mio, RTX 2070 SUPER 224 Mio, 0 % chacune; aucun service redémarré.
