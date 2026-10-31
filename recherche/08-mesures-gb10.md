# 08 — Mesures réelles sur le DGX Spark GB10 (pc6)

Toutes les lignes de ce fichier sont **[MESURÉ par nous]** sauf mention contraire. Machine partagée avec d'autres sessions : les temps peuvent varier selon la charge.

## Environnement (30/10/2026)

| Élément | Valeur |
|---|---|
| GPU | NVIDIA GB10 (DGX Spark), pilote 580.178.04, CUDA 13.0, 121 Go de mémoire unifiée (≈ 105 Go libres au démarrage) |
| PyTorch | 2.14.1+cu130 ; `get_arch_list()` = sm_80, sm_90, sm_100, sm_110, sm_120 (le GB10 sm_121 tourne sur les binaires sm_120) |
| ComfyUI | v0.43.2 (frontend 1.57.4), nœuds natifs MiniMax H3, `comfy_kitchen` (backends eager et cuda actifs, NVFP4 `scaled_mm_nvfp4` disponible ; triton désactivé) |
| Piège rencontré | Triton compile un module C au premier encodage de texte et exige `Python.h` ; sans droits administrateur, en-têtes extraits du paquet `libpython3.12-dev` (`apt-get download` + `dpkg -x`) et passés par `CPATH` (`~/nexora-creative-data/engine/lancer-comfyui.sh`). |
| Poids | FastH3 V2 8 étapes élagué NVFP4 (13,6 Go), encodeur Qwen3-VL-32B NVFP4-AWQ (15,7 Go), VAE vidéo fp16 (5,2 Go), VAE audio fp32 (0,6 Go) — 35,1 Go au total |

## Rendus H3 (FastH3 V2 NVFP4, 8 étapes, res_multistep, décalage sigma 10/3, sans VSA)

| # | Résolution | Images (durée) | Audio | État | Temps total | Détail |
|---|---|---|---|---|---|---|
| 1 | 832×480 | 124 (5,17 s) | stéréo 32 kHz | **à froid** | **92,1 s** | échantillonnage 61 s (7,65 s/étape) ; le reste = chargement + encodage du texte + décodage VAE |
| 2 | 832×480 | 124 (5,17 s) | stéréo 32 kHz | **à chaud** | **82,1 s** | graine différente |
| 3 | 832×480 | 124 (5,17 s) | stéréo | à chaud, dans un film | 82,9 à 86,3 s | 4 plans de 5 s du film « Crimson Rising » |
| 4 | 832×480 | **243 (10,1 s)** | stéréo | à chaud, dans un film | **230,2 et 230,9 s** | ≈ 24 s par étape : **2,7 fois le temps d'un plan de 5 s pour 2 fois la durée** (l'attention croît plus vite que la longueur) |
| 5 | assemblage ffmpeg | 6 plans → 41,0 s | AAC | — | **3,1 s** | concaténation ré-encodée H.264 CRF 18 + AAC |

Conséquence pour le Director : préférer des plans de 5 s (meilleur rapport temps/durée), réserver 10 s aux actions continues.

Vérification du fichier n° 1 (ffprobe) : H.264 High 832×480 24 i/s + AAC stéréo 32 kHz, 5,17 s ; volume moyen −18,9 dB, crête −3,9 dB (le son est bien présent). Contrôle visuel : le mouvement de caméra en orbite demandé est respecté, la voiture garde son identité sur tout le plan.

Comparaison avec les chiffres publiés (rapports 03 et 04) : un tiers annonçait 141,4 s sur Spark pour FastH3 V2 NVFP4 en 480p 5 s ; nous mesurons 82 à 92 s avec ComfyUI 0.43.2, donc mieux que ce chiffre publié. Non comparable directement : version du moteur, réglages et résolution exacte diffèrent.

## À mesurer ensuite
- 1344×768 (résolution native de H3), 10 s et 15 s, avec et sans VSA (`BlockSparseAttention`).
- Encodeur de texte INT8 contre NVFP4 (qualité de compréhension du prompt).
- Mémoire de pointe (le GB10 n'expose pas la mémoire GPU à `nvidia-smi` ; lire `torch.cuda.max_memory_allocated` dans le moteur).
- Wan 2.2 TI2V-5B (licence Apache-2.0) sur la même scène.
