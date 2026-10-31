# 11 — Modèle d'image le plus puissant en poids ouverts, et musique MiniMax (31/10/2026)

Question du fondateur : une option de musique avec MiniMax Music ; apporte-t-elle un gain **substantiel** de rendu
sonore avec H3 ; et quel est le modèle d'image le plus puissant en poids ouverts.

## 1. Musique et son : ce que fait chaque modèle

| | MiniMax H3 (audio natif) | MiniMax Music 3 |
|---|---|---|
| Rôle | bruitages, ambiances, voix **synchronisés à l'image** ; musique « non diégétique » possible mais décrite en une ligne | **composition** : chansons ou musiques jusqu'à 5 min, structure (intro, montée, drop, climax, outro), tempo, instruments, voix chantées |
| Contrôle | champs `overall_soundscape` et `non_diegetic_music` du prompt | description structurée en 3 parties + paroles avec balises de section |
| Synchronisation à l'image | oui (c'est sa force) | non : la musique est calée **après coup**, au montage |
| Licence | H3 Community (territoires exclus) | Music3 Community : **aucun territoire exclu**, « MiniMax-Music3 » affiché dans l'interface, 20 M$ de revenus |

**Gain réel, mesuré ici [MESURÉ] :** 60 s de musique de bande-annonce en **27 s** sur la RTX 5090 ; sur 7 candidats, un a
suivi presque exactement la structure demandée (120 BPM mesuré à 122, silence puis impact final à 54,2 s, +33 dB). Les
autres ont suivi le style mais pas le minutage à la seconde. Donc : **oui, substantiel pour la musique** (structure,
puissance, cohérence sur la durée d'un film), **non pour les bruitages et les voix**, qui restent ceux de H3
(synchronisés, mais non remplaçables par un modèle de musique). Le montage final garde les deux : bruitages H3 à −8 dB
sous la musique, mixage à −14 LUFS. Un A/B auditif reste à faire par le fondateur sur la bande-annonce.

Intégré : bouton « Composer la musique du film » dans le panneau des plans ; bouton « Ajouter une musique » sur chaque
clip de l'accueil ; le LLM écrit la description depuis le storyboard (repli sûr sans LLM).

## 2. Image : classement des modèles à poids ouverts (arène, 30-31/10/2026)

Source : Arena (text-to-image) et Artificial Analysis T2I v2.1, lus le 31/10 [LU]. Les scores d'arène et d'AA ne sont
pas comparables entre eux.

| Modèle | Score | Taille | Licence | Utilisable dans Nexora (SaaS commercial) |
|---|---|---|---|---|
| Qwen-Image-2.1 | arène 1225 (préliminaire) | 7B | **Qwen Research License : non commercial** | non, sauf licence commerciale d'Alibaba |
| Ideogram 4.0 | arène 1200 | 9,3B (FP8 9,3 Go, NVFP4 5,5 Go) | poids non commerciaux ; **licence commerciale payante** (dès 300 $/mois pour 10 000 images/mois) | seulement en payant ; meilleur pour texte et mise en page |
| FLUX 3 Image Klein | AA 1043 (1er des poids ouverts chez AA) | 5,6B | FLUX Kommunity : limite de revenus (5 M$) et exclut l'usage en contact direct avec les utilisateurs finaux | risque élevé |
| Cosmos3-Super-Text2Image | arène 1151 (1164 avec « agentic ») | **64B, BF16 seulement (≈ 130 Go)** | OpenMDW-1.1 (commercial permis) | permis, mais ≈ 6× plus lourd que Qwen pour ≈ +26 points |
| HunyuanImage 3.0 | arène 1151 | grand | Tencent : exclut UE, R.-U., Corée | non pour ces clients |
| FLUX.2 [dev] | arène 1145 | — | non commercial | non |
| **Qwen-Image-2512** | **arène 1125** | 20B (FP8 20,4 Go ; NVFP4 19,8 Go) | **Apache-2.0** | **oui** |
| HiDream-O1-Image | arène 1115 | 8B | MIT | oui |
| Z-Image-Turbo | arène 1082 | 6B | Apache-2.0 | oui (très rapide : 7 s sur GB10 en 1024², mesure tierce) |

**Réponse :** le plus puissant *en absolu* est Qwen-Image-2.1, mais sa licence de recherche l'exclut d'un produit payant.
Le plus puissant *utilisable sans payer de licence image* est **Qwen-Image-2512 (Apache-2.0)**. Choix fait : le studio
pointe désormais dessus (au lieu de la version d'août 2025), avec Qwen-Image-Edit pour les retouches. Deux montées en
gamme possibles, chacune demandant un accord du fondateur : (a) licence commerciale Ideogram 4 pour la typographie et
les mises en page (affiches, titres), (b) licence commerciale Alibaba pour Qwen-Image-2.1.

## 3. À quoi sert l'image dans un studio vidéo

H3 démarre mieux d'une **image de départ** : plan clé du storyboard fixé (visage, costume, décor) puis animé en I2V,
au lieu de laisser H3 inventer chaque plan (c'est le principe de Higgsfield et de l'AI Director). Le studio a déjà
« Partir de ma photo » ; il manque l'étape « l'IA dessine d'abord le plan clé, tu valides, puis H3 l'anime »
(non construite). Poids Qwen-Image-2512 non téléchargés : 20,4 Go + 9,4 Go + 0,3 Go, à installer sur pc1 (350 Go libres).
