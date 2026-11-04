# NVIDIA pour Nexora Creative — recherche technique et recommandations

**État vérifié le 4 novembre 2026. Rapport en français.** Périmètre : amélioration des vidéos MiniMax-H3 dans ComfyUI sur RTX 5090 32 Go à 475 W, Pika H3 Flex sur DGX Spark/GB10 128 Go, et délestage sur RTX 5080, V100 et RTX 20 SUPER.

## Lecture rapide

Les investissements les plus utiles sont une **finition vidéo correctement intégrée**, un **moteur H3 optimisé pour vos machines**, et un **tri automatique des prises**. Changer entièrement de générateur n’est pas la première action recommandée.

- **À adopter tout de suite :** encodage NVENC adapté à la carte ; chaîne de finition RTX Video sur une machine compatible ; transcription Parakeet v3 et vérification du texte parlé ; séparation des files génération, finition et audio.
- **À tester en priorité :** Sol-H3/Sol Engine sur 5090 et Spark ; SoL-Refiner pour vos sorties H3 ; Harmonizer et Cosmos-Transfer1-DiffusionRenderer pour certains plans ; Cosmos Transfer 2.5 pour la transformation contrôlée ; Cosmos Reason2 pour le tri des prises ; Magpie pour le français ; LipSync pour les avatars vidéo.
- **À écarter du service payant dans leur distribution actuelle :** PiD, DiffusionRenderer académique, UniRelight, Difix3D+ et Lyra 2.0, pour des restrictions de recherche/non-commerciales. Leur code visible ne suffit pas à autoriser les poids ou l’ensemble du pipeline.
- **À surveiller :** HorizonRelight et TRON. Les pages officielles consultées annoncent encore le code à venir.

**Découverte particulièrement adaptée à Creative :** NVlabs publie désormais des entrées **Sol-H3-RTX5090**, **Sol-H3-Spark** et **Sol-H3-ComfyUI**. Il existe donc une piste NVIDIA spécifique à votre générateur, et pas seulement des promesses générales TensorRT. Les chiffres et leurs limites figurent plus bas.

### Méthode, dates et niveau de preuve

Les liens de ce rapport ont été ouverts pendant la recherche ; les sources retenues sont NVIDIA, ses dépôts officiels, les dépôts des auteurs, ou les fiches de poids liées depuis ces sources. Une page accessible ne démontre pas qu’un téléchargement restreint est accessible à votre compte. Aucun téléchargement de poids ni benchmark n’a été effectué sur vos machines.

**Contrôle final : 132 URL distinctes citées, toutes ouvertes avec succès pendant cette recherche**, dont une nouvelle passe sur les 130 liens principaux ; les deux liens de version ajoutés ensuite ont également été ouverts. Les pages mobiles restent susceptibles de changer après le 4 novembre 2026.

Les dates indiquées désignent la publication, la mise à jour annoncée ou le tag observé. **« Instantané 04-11-2026 »** signifie que la source n’affiche pas de version/date de publication suffisamment nette. Les mentions **confirmé**, **plausible/à porter**, **non validé** et **hors budget mémoire** sont délibérément distinctes. Les recommandations et estimations de gain sont mon analyse, pas des mesures de Nexora.

Les documentations `latest` et branches `main` sont mobiles. Pour reproduire un essai, enregistrer le commit, la révision des poids, le digest du conteneur, CUDA/PyTorch, les paramètres et la limite de puissance. Certaines pages officielles se contredisent : les désaccords utiles sont conservés explicitement.

### Comment lire « licence en un mot »

| Mot utilisé | Signification | Service Creative payant |
|---|---|---|
| **Apache-2.0**, **MIT**, **BSD** | Licence permissive du composant identifié | Oui, avec ses notices ; les poids et dépendances peuvent avoir d’autres termes |
| **CC-BY-4.0** | Attribution requise | Oui, avec attribution appropriée |
| **NOML** | NVIDIA Open Model License | Oui selon ses conditions, pour les poids concernés |
| **OpenMDW-1.1** | Licence affichée par Cosmos 3 | Oui ; conserver les obligations du texte distribué |
| **NSCL**, **Noncommerciale**, **Recherche** | Restrictions de recherche/évaluation ou d’usage interne scientifique | Non pour la production du service dans ces conditions |
| **Propriétaire** | SDK, runtime, application ou conteneur sous EULA NVIDIA | Possible selon le produit et l’offre ; ne pas confondre modèle autorisé, API d’essai et droit d’exploiter le runtime |
| **Indéterminée** | Aucun texte suffisamment clair identifié pour l’artefact exact | Autorisation commerciale non établie |

La [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) autorise l’exploitation commerciale des modèles concernés. La [FAQ de licences NVIDIA](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-licensing-overview-and-faq/) distingue logiciels libres, produits communautaires utilisables en production et offres Enterprise payantes. **Tous les NIM ne sont donc pas automatiquement payants, ni automatiquement libres d’exploitation.** Ce rapport précise le cas quand la source le permet ; il ne transforme pas une licence de poids en licence du conteneur.

## 1. Votre parc : ce qui change réellement les choix

| Machine | Architecture et mémoire | Rôle conseillé | Limites à retenir |
|---|---|---|---|
| RTX 5090 | Blackwell **sm_120**, 32 Go dédiés | H3 principal, prototypes de finition et de conversion | 32 Go imposent souvent quantification et offload. Un kernel « Blackwell B200 » n’est pas nécessairement compilé pour sm_120 |
| RTX 5080 | Blackwell **sm_120**, 16 Go | Finition RTX Video, AV1, petits modèles audio/vision | Trop petite pour reprendre sans adaptation un pipeline vidéo prévu pour 32–80 Go |
| DGX Spark / GB10 | Blackwell **sm_121**, CPU **ARM64**, 128 Go unifiés | H3/Flex, modèles plus volumineux, services audio ou juge en créneaux réservés | RAM partagée avec OS/CPU ; capacité mémoire et débit ne sont pas ceux d’un GPU datacenter. Le paquet doit aussi être ARM64 |
| Tesla V100 | Volta **sm_70**, 16 Go | Tâches FP16 compatibles avec une ancienne pile, encodage HEVC/H.264 | Pas de chemin natif BF16/FP8/NVFP4 ; exclue des TensorRT actuels et de nombreux kernels modernes. Aucun cœur RT/OFA |
| RTX 2080 SUPER / 2070 SUPER | Turing **sm_75**, généralement 8 Go | Encodage HEVC, Optical Flow, certains effets et petits traitements | FP16/INT8 ; pas de NVFP4 natif ni d’encodage AV1. Compatibilité par effet, pas par simple présence de Tensor Cores |
| AMD | Modèles non précisés | CPU/logiciels génériques, certains backends ouverts | Pas de TensorRT, NVENC ou Maxine NVIDIA natifs. NeMo-Speech.cpp mérite une vérification de backend séparée |

Sources : [capacités CUDA actuelles](https://developer.nvidia.com/cuda/gpus) et [anciennes générations](https://developer.nvidia.com/cuda/gpus/legacy), instantané 04-11-2026. Les rôles sont des recommandations d’organisation.

**Trois précautions concrètes :**

1. **sm_120 ≠ sm_100 ≠ sm_121.** Une recette B200/GB200 ne garantit ni les instructions, ni les wheels, ni la mémoire sur 5090 ou GB10.
2. **« RTX Spark » Windows N1X ≠ « DGX Spark » Linux GB10.** Une annonce Windows ARM64 n’établit pas la disponibilité du même SDK pour Linux ARM64.
3. **Ne pas fusionner vos VRAM sur le papier.** Une 5090 et une 5080 ne forment pas spontanément un GPU de 48 Go. Pour ce parc hétérogène, plusieurs workers indépendants sont généralement une meilleure première étape qu’un modèle réparti sur toutes les cartes.

Aucun benchmark cité ci-dessous n’établit les performances à **475 W**. Mesurer temps complet, énergie par prise acceptée et débit sous file réelle ; ne pas appliquer une règle proportionnelle entre watts et secondes.

## 2. Sol Engine et Sol-H3 : première piste pour réduire la file

### 2.1 Sol Engine / Sol-Attn, sans changer les poids H3

**Apport :** accélérer votre moteur existant grâce aux kernels fusionnés, à la compilation, au décodage VAE et, selon le profil, à l’attention parcimonieuse et au cache entre étapes.

Le billet officiel [H3 sur DGX Spark et RTX 5090](https://nvlabs.github.io/Sana/Sol-Engine/H3-OnDevice/) publié dans la série d’annonces d’août 2026 mesure :

| Expérience publiée | Référence | Pile complète | Point essentiel |
|---|---:|---:|---|
| Spark, 832×480, 124 images, 50 étapes | 710,6 s | 181,3 s, soit 3,92× | Job en 480p |
| 5090, 1344×768, 124 images, 50 étapes | 1 045,4 s | 231,2 s, soit 4,52× | Job en 768p ; comparaison interne à cette carte |

Les kernels seuls représentent une optimisation sans approximation algorithmique ; l’attention parcimonieuse et le cache introduisent des approximations. **« Pas de distillation » ne signifie pas résultat mathématiquement identique.** Le plus gros gain de cette expérience vient du cache. Ces résultats ne mesurent pas Pika H3 Flex à six étapes.

**Local :** preuves explicites 5090 et GB10 ; 5080 non validée par ces mesures ; V100/Turing à écarter pour ce chemin moderne. **Intégration :** branche `sol-engine` de Sana, runtime Python ; chemins ComfyUI ci-dessous. **Licence : Apache-2.0** pour le code, **commercial : oui** pour ce code ; H3 et les composants gardent leurs licences. **Verdict : tester en priorité.**

### 2.2 Sol-H3 dans ComfyUI : version locale publiée en octobre 2026

Le [README officiel Sol-H3-ComfyUI](https://raw.githubusercontent.com/NVlabs/Sana/sol-engine/models/minimax_h3/Sol-H3-ComfyUI/README.md) décrit un worker séparé, une interface Studio et des workflows. Il exige **Linux, 5090 32 Go, au moins 90 Go de RAM hôte**, ComfyUI ≥ 0.30, Python 3.12, PyTorch 2.12/CUDA 13, Triton 3.7 et des extensions construites pour SM120.

| Profil du README | Temps publié pour environ 5 s, avec audio | Ce qui change |
|---|---:|---|
| H3 BF16, 50 étapes | 989,0 s | Référence publiée |
| HyperFlow 8 étapes, BF16 | 193,6 s | Adaptateur de distillation tiers |
| Une étape de pipeline : H3 FP8 + LoRA 8 étapes + fast VAE | 67,2 s | « One stage » désigne une seule phase de pipeline, pas un seul pas de débruitage |
| Deux phases, RTX 5090 | 35,5 s | Brouillon H3 puis raffinement LTX |
| Deux phases, DGX Spark | 64,3 s | Entrée Spark dédiée |

**Licence : Apache-2.0** pour le nœud ; **commercial : conditionnel pour le pipeline complet**, qui inclut H3, LoRA et LTX. **Verdict : tester**, puis adopter le profil gagnant sur vos prises. Ne pas remplacer silencieusement Flex par un adaptateur FastH3 ou HyperFlow.

### 2.3 Les chiffres locaux ne décrivent pas tous le même protocole

Les [notes de validation ComfyUI du 13 octobre 2026](https://raw.githubusercontent.com/NVlabs/Sana/sol-engine/models/minimax_h3/Sol-H3-ComfyUI/docs/validation.md) distinguent mesures uniques, warmup, encodeur Qwen quantifié et différents adaptateurs. Le [paquet RTX5090](https://raw.githubusercontent.com/NVlabs/Sana/sol-engine/models/minimax_h3/Sol-H3-RTX5090/README.md) rapporte aussi **39,80 s** pour une requête formelle avec chargement Qwen par requête. Ce chiffre n’est pas interchangeable avec les 35,5 s du Studio.

Le [paquet Spark](https://raw.githubusercontent.com/NVlabs/Sana/sol-engine/models/minimax_h3/Sol-H3-Spark/README.md) décrit quatre mises à jour H3 à 672×384, un transfert latent et **trois mises à jour LTX-2.5**, avec l’audio H3 conservé. Il précise que ce chemin **n’utilise pas un raffineur à un pas**. Ses tests incluent aussi certains cas première/dernière image et références, mais pas toutes les combinaisons.

À l’autre extrême, le [Sol-H3 B300](https://nvlabs.github.io/Sana/Sol-Engine/Sol-H3/) annonce 1,653 s sur **huit B300** pour un clip de cinq secondes. Comparaison à un H3 à 50 étapes, adaptateur à quatre passes, modèle chaud, chargement/compilation/MP4 exclus : ce n’est pas une promesse de temps réel sur votre parc. Le [README de ce chemin](https://github.com/NVlabs/Sana/tree/sol-engine/models/minimax_h3/Sol-H3) marque certains backends SM120 non validés ; utiliser les entrées locales dédiées, pas le profil B300 par défaut.

### 2.4 SoL-Refiner et Open-H3-Regenerate-2K

**Apport :** générer un brouillon moins cher puis reconstruire des textures et détails à plus haute résolution ; directement pertinent pour votre 1344×768 agrandi.

La [page SoL-Refiner](https://nvlabs.github.io/Sana/Sol-Refiner/), annoncée en septembre 2026, étudie une étape de débruitage à la résolution cible, jusqu’à 4K. Le [code publié](https://raw.githubusercontent.com/NVlabs/Sana/sol-engine/models/sol-refiner/README.md) sépare la version du papier **LTX-2.3** et l’extension ultérieure **LTX-2.5 pour H3**. Cette dernière accepte une vidéo H3 et un prompt via [une entrée Diffusers dédiée](https://raw.githubusercontent.com/NVlabs/Sana/sol-engine/models/sol-refiner/MiniMax-H3/README.md).

**Disponibilité et droits :** les [poids de l’extension H3](https://huggingface.co/Efficient-Large-Model/SoL-Refiner-LTX-2.5-for-MiniMax-H3) existent, mais la page consultée affiche **« No model card »** sans licence explicite. Les [poids LTX-2.3 une étape](https://huggingface.co/Efficient-Large-Model/SoL-Refiner-LTX-2.3-One-Step) existent aussi. Ne pas déduire leurs droits de la licence Apache du dépôt Sana.

**Local :** 5090/Spark plausibles avec offload et recette appropriée ; la mémoire maximale du raffinement 4K de cette entrée n’est pas établie par les benchmarks locaux Sol-H3 en 768p. 5080 non garantie ; V100/Turing hors cible. **Licence : Indéterminée** pour l’autorisation complète des poids exacts ; **commercial : non établi**. **Verdict : tester en R&D, pas encore adopter pour les livraisons payantes sur cette seule preuve.**

Le gain **27,03×** affiché sur la page concerne un protocole H3 en deux phases sur **GB200**, pas un upscale 4K en 1,56 s sur 5090. [Open-H3-Regenerate-2K](https://nvlabs.github.io/Sana/Open-H3-Regenerate-2K/) constitue une autre piste publiée de raffinement H3 ; ne pas l’assimiler au paquet ComfyUI ni à la preuve d’un pipeline commercial prêt sur 32 Go. **Licence et mémoire locales exactes : non confirmées ; verdict : tester seulement après identification des artefacts.**

## 3. Cosmos : versions actuelles, conversion photoréaliste et juge vidéo

### 3.1 La famille actuelle est Cosmos 3

Le [dépôt NVIDIA Cosmos](https://github.com/NVIDIA/cosmos) et les [notes de sortie](https://github.com/NVIDIA/Cosmos/releases) établissent **Cosmos 3**, annoncé le **31 mai 2026**, publié dans GitHub le **1er juin**. La gamme comprend **Edge 4B**, **Nano 16B**, **Super 64B**, avec surfaces de raisonnement et de génération. Edge apparaît dans les annonces de juillet ; sa [fiche officielle](https://huggingface.co/nvidia/Cosmos3-Edge) signale une mise à jour du générateur le **25 août 2026**. Les variantes de simulation d’octobre visent surtout conduite et robotique.

Les lignes séparées **Predict 2.5**, **Transfer 2.5** et **Reason2** restent disponibles, mais leurs dépôts annoncent une maintenance limitée et renvoient à Cosmos 3. Il serait donc incorrect de présenter Predict 2.5 comme la dernière génération de toute la plateforme.

| Élément / version vérifiée | Apport concret pour Creative | Local sur votre parc | Intégration ; licence ; service payant | Verdict |
|---|---|---|---|---|
| **Cosmos 3 Edge, 4B**, juillet/août 2026 | Petit juge visuel ou moteur de prévisualisation à comparer | 5090 : candidat ; 5080 : à dimensionner. **Générateur mesuré sur DGX Spark** dans la fiche officielle, PyTorch et vLLM-Omni ; ne pas assimiler cela à un budget VRAM universel du Reasoner. V100/Turing : pas de chemin de référence recommandé | Transformers/Diffusers/vLLM selon tâche ; nœud ComfyUI officiel spécifique non confirmé. **OpenMDW-1.1**, oui | **Tester** surtout le raisonnement ; ne pas attendre d’un petit modèle un remplacement supérieur à H3 |
| **Cosmos 3 Nano, 16B** | Génération, audio et compréhension de scènes ; autre moteur pour certains plans physiques | Fiche de déploiement : **60 Go minimum** pour le modèle complet ; 5090/5080 hors configuration standard. Spark : capacité plausible, installation ARM64 à établir pour le backend choisi. V100/Turing : écarter | Python, Diffusers, vLLM-Omni, NIM. **OpenMDW-1.1**, oui pour les poids | **Tester sur Spark en créneau dédié**, sans pénaliser Flex |
| **Cosmos 3 Super, 64B**, dont Image2Video | Référence de qualité ou enseignant ; intérêt potentiel pour plans difficiles | **145 Go minimum** annoncé pour le modèle complet : hors de vos machines individuellement, Spark 128 Go compris | API ou GPU externe approprié ; mêmes réserves NIM. **OpenMDW-1.1**, oui | **Écarter du déploiement local actuel** |

Sources matérielles : [matrice Cosmos 3, mise à jour 30-10-2026](https://docs.nvidia.com/cosmos/latest/cosmos3/model_matrix.html), [fiche Nano](https://huggingface.co/nvidia/Cosmos3-Nano), [fiche de déploiement Nano/Super](https://build.nvidia.com/nvidia/cosmos3-nano/modelcard). Les tailles **16B/64B totales ne sont pas les tailles des seules tours Reasoner** ; les exigences du modèle complet ne constituent pas celles d’un juge qui ne charge que sa partie raisonnement.

### 3.2 Predict, Transfer et Reason : dernières lignes spécialisées attestées

| Élément | Version et date attestées | Usage Creative | Matériel / local | Intégration, licence, commercial | Verdict |
|---|---|---|---|---|---|
| **Cosmos Predict 2.5** | 2B et 14B ; 14B ajouté le **05-12-2025**, 2B distillé Text2World le **19-12-2025** | Générer/prolonger des plans, contrôler leur état initial ; comparer la plausibilité des mouvements | Ampere+ ; Blackwell et ARM ajoutés le 25-11-2025. La recette standard n’est pas une preuve de tenue en 32 Go ; partir d’un 2B avec offload. Spark candidat. V100/Turing hors cible | Code Python, Diffusers pour le 2B, conteneurs. **NOML** poids / Apache-2.0 code ; oui | **Tester ponctuellement** ; gain contre H3 non établi |
| **Cosmos Transfer 2.5, 2B** | Checkpoints contrôles mis à jour le **12-12-2025** ; **Distilled Edge 23-02-2026** | Transformer un rendu ou un plan en conservant profondeur, contours, segmentation ou structure floutée ; candidat pour atténuer l’aspect jeu vidéo | Guide officiel : **65,4 Go** pour l’inférence standard. 5090/5080 : pas dans ce budget ; offload/quantification à démontrer. Spark : candidat documenté CUDA 13/ARM, avec marge OS. V100/Turing exclus | Python, entrées JSON, Docker ; intégration ComfyUI par wrapper/service à qualifier. **NOML** / Apache-2.0 ; oui | **Tester sur Spark**, surtout plans présélectionnés ; éviter une seconde diffusion sur chaque prise |
| **Cosmos Reason2** | **2B/8B : 19-12-2025 ; 32B : 29-04-2026** | Examiner une vidéo et signaler défauts de mouvement, disparition d’objets, non-respect du brief | Minimums documentés **24 Go pour 2B, 32 Go pour 8B** ; 5090 possible en exclusivité ; 5080 sous ces minimums ; **Spark testé officiellement**. Minimum 32B non confirmé. V100/Turing non validés | Transformers ≥ 4.57, vLLM, exemples Docker ; service appelé par ComfyUI ou ordonnanceur. **NOML** poids / Apache-2.0 code ; oui | **Tester en priorité le 2B**, puis 8B si le gain de jugement justifie le coût |

Sources : [Predict 2.5 et historique](https://raw.githubusercontent.com/nvidia-cosmos/cosmos-predict2.5/main/README.md), [guide Predict](https://raw.githubusercontent.com/nvidia-cosmos/cosmos-predict2.5/main/docs/inference.md), [Transfer 2.5 et historique](https://raw.githubusercontent.com/nvidia-cosmos/cosmos-transfer2.5/main/README.md), [mémoire et contrôles Transfer](https://raw.githubusercontent.com/nvidia-cosmos/cosmos-transfer2.5/main/docs/inference.md), [installation ARM/Spark Transfer](https://raw.githubusercontent.com/nvidia-cosmos/cosmos-transfer2.5/main/docs/setup.md), [Reason2, versions et plateformes](https://raw.githubusercontent.com/nvidia-cosmos/cosmos-reason2/main/README.md), [licence des poids Transfer](https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B).

**Le mot « Edge » est ambigu :** le contrôle **Edge** de Transfer signifie **contours** ; ce n’est pas la même chose que le petit modèle **Cosmos 3 Edge** pour appareils périphériques.

### 3.3 Ce que Transfer et Reason ne résolvent pas automatiquement

Transfer peut réinventer les textures et l’éclairage au prix d’une dérive de visage, costume, bouche ou détails narratifs. Pour vos personnages récurrents, mesurer l’identité sur toute la séquence, et non seulement sur une belle image. Conserver des références approuvées et limiter la transformation aux plans qui en bénéficient.

Reason est un modèle de compréhension, **pas une métrique objective validée de « qualité cinéma »**. Il peut manquer des défauts entre images échantillonnées, juger à tort un effet fantastique comme une erreur physique, ou préférer une image lisse. Utiliser une grille explicite et des exemples de référence Creative. Une explosion ou un sabre autorisé par le brief ne doit pas être automatiquement rejeté comme « impossible ».

## 4. Rééclairage, rendu et apparence photoréaliste

### 4.1 Les outils réellement disponibles

| Élément et version/date | Ce qu’il apporte | Matériel et faisabilité locale | Intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|---|
| **DiffusionRenderer académique / SVD**, CVPR 2025, code **11-06-2025** | Estime géométrie/matériaux et rééclaire une vidéo ; expérimentation d’insertion d’objets | > **22 Go** avec options mémoire pour 512²/24 images ; 4090 24 Go testée. 5090 : adaptation de la vieille pile ; 5080 insuffisante dans ce réglage. Spark ARM non validé ; V100/Turing non recommandés | Scripts PyTorch ; pas de nœud officiel ComfyUI confirmé | **NSCL** ; **non**. Le fichier de licence limite à recherche/évaluation ; base SVD avec ses propres termes | **Écarter de la production payante** |
| **Cosmos-Transfer1-DiffusionRenderer**, code et poids **12-06-2025**, modèle 7B | Variante améliorée pour retirer puis reconstruire l’éclairage et modifier les matériaux | Dépôt : **16 Go minimum**, **48 Go ou plus recommandés** ; testé A100 80 Go et A6000 48 Go. 5090 possible avec économies mémoire, pas preuve de confort ; 5080 à la limite théorique. Spark à porter ; V100/Turing hors cible | Python, Dockerfile, deux passes et signaux intermédiaires ; intégration service/nœud à développer | **NOML** poids, Apache-2.0 code ; **oui** | **Tester** pour effets et harmonisation sur plans importants |
| **UniRelight**, NeurIPS 2025 ; poids/code indiqués **06-04-2026** | Décomposition et rééclairage conjoints ; ombres, réflexions et transparence | Cosmos 7B, référence A100/Linux, sortie annoncée 848×480. Pic mémoire fiable non publié dans la fiche ; pas de garantie 5090/5080 ou ARM. V100/Turing à écarter | Scripts PyTorch, HDRI, compilation de dépendances ; nœud officiel non confirmé | **Noncommerciale**, NVIDIA OneWay / NSCL ; **non** | **Écarter du service payant** |
| **HorizonRelight**, ECCV 2026, page NVIDIA datée **14-08-2026** | Maintient le rééclairage entre fenêtres d’une longue vidéo ; réduit les ruptures temporelles | **Non établi** : pas de paquet publié sur la page consultée ; aucune exigence locale vérifiable pour vos cartes | Page/papier et démos ; **Code Coming soon** | **Indéterminée** ; commercial non établi | **Écarter de l’intégration immédiate**, surveiller |
| **TRON**, prépublication **juin 2026** | Reconstruction gaussienne avec matériaux/lumières explicites et rendu neuronal en une étape | Démonstration interactive, mais exigences du futur paquet non confirmées ; aucune validation sm_120/ARM/Volta établie | **Code Coming Soon** sur page officielle | **Indéterminée** ; commercial non établi | **Surveiller**, pas un SDK installable démontré |

Sources ouvertes : [DiffusionRenderer, code et mémoire](https://github.com/nv-tlabs/diffusion-renderer), [sa licence effective](https://raw.githubusercontent.com/nv-tlabs/diffusion-renderer/main/LICENSE.txt), [variante Cosmos et minimums](https://raw.githubusercontent.com/nv-tlabs/cosmos-transfer1-diffusion-renderer/main/README.md), [fiche UniRelight](https://huggingface.co/nvidia/UniRelight), [licence UniRelight](https://github.com/nv-tlabs/UniRelight/blob/main/LICENSE), [HorizonRelight, disponibilité](https://research.nvidia.com/labs/sil/projects/horizonrelight/), [date NVIDIA HorizonRelight](https://research.nvidia.com/publication/2026-08_horizonrelight-relighting-long-horizon-videos-consistently-diffusion), [TRON](https://research.nvidia.com/labs/sil/projects/tron/).

Il n’est pas établi qu’un produit public nommé **« DiffusionRenderer 2 »** existe. Les travaux ci-dessus sont des évolutions ou des approches voisines ; ils ne constituent pas une gamme de versions interchangeable.

### 4.2 Harmonizer : le complément 2026 à considérer

**Harmonizer-cosmos-0.6B**, version V1 de **juin 2026**, est un raffineur de rendus de reconstruction neuronale : raccord de couleur et d’éclairage, ombres d’objets insérés, correction d’artefacts NeRF/3DGS. Deux poids : temporel et non temporel. **Apport Creative :** améliorer un compositing ou un décor 3D avant passage dans H3 ; tester également sur des images générées, en reconnaissant le décalage avec ses données de conduite/simulation.

**Local :** fiche compatible Ampere/Hopper/Blackwell, Linux ; pas de preuve dédiée 5090/GB10 dans cette fiche. Le **NIM 1.0.0** valide notamment une 4090 24 Go avec un profil mémoire réduit ; la 5090 32 Go est une candidate pour le code Python, pas une configuration NIM explicitement attestée par cette liste. 5080 16 Go non garantie ; ARM64 non confirmé ; V100/Turing hors cible.

**Intégration :** [code et Dockerfile officiels](https://github.com/NVIDIA/harmonizer), PyTorch ; [poids NVIDIA](https://huggingface.co/nvidia/Harmonizer) ; [matrice NIM](https://docs.nvidia.com/nim/harmonizer/support-matrix). **Licence : NOML** poids, Apache-2.0 code ; **commercial : oui** sur cette voie, termes du NIM séparés. **Verdict : tester en priorité pour les plans avec insertions.** Ce modèle ne fournit pas un contrôle arbitraire de chaque source lumineuse.

### 4.3 Pour les explosions et sabres de lumière

Le problème est l’**interaction lumineuse** : un sabre doit éclairer le visage proche et une explosion doit produire un rebond et une variation d’exposition cohérents. Ajouter un halo ou convertir en HDR ne crée pas ces interactions.

Procédure recommandée, à tester sur un plan court : conserver le plan de base ; extraire masques et indices de profondeur/normales ; produire une contribution lumineuse animée ; rééclairer/harmoniser les zones touchées ; recomposer l’effet et vérifier visage, ombres, clignotement et texture de peau. Cosmos DiffusionRenderer est une piste pour l’étape lourde, Harmonizer pour certains raccords. Leur réinterprétation peut altérer les détails : comparer aussi à un compositing classique limité aux zones éclairées.

Le **Video Relighting de Maxine** traite surtout une personne sous une **HDRI 360°×180°** ; c’est intéressant pour un avatar dans un décor, moins directement pour une explosion localisée au milieu d’un environnement. Ce produit est détaillé avec les autres effets vidéo ci-dessous.

## 5. SANA, édition, personnages et scènes 3D/4D

### 5.1 La famille SANA : plusieurs usages, plusieurs générations

| Élément et état daté | Apport Creative | Local : 5090 / 5080 / Spark / anciennes cartes | Intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|---|
| **SANA image**, 0,6B/1,6B ; **SANA-1.5**, 1,6B/4,8B ; **SANA-Sprint**, instantané 04-11-2026 | Images de référence, décors, concepts et premières images à faible coût ; Sprint réduit les étapes | Les petits profils sont adaptés aux RTX grand public. Les options 4K et quantifiées ont des budgets différents ; encodeur, VAE et offload comptent aussi. Spark : port ARM à contrôler par recette ; V100/Turing : pas les kernels FP4/FP8 modernes | Docs ComfyUI renvoyant vers **ComfyUI_ExtraModels**, intégration communautaire ; scripts officiels | **Apache-2.0** pour SANA ; **oui**, vérifier aussi encodeur et modèle exact | **Tester** pour préparer les prises, pas pour réparer directement une vidéo |
| **SANA-Video 2B**, 480p/720p, ICLR 2026 | Générateur vidéo léger, utile pour brouillons et variantes rapides | Démonstration **5090 NVFP4** publiée ; le billet mesure 71 → 29 s pour 5 s en 720p. Pas une mesure de Video 2.0. 5080 : mémoire à tester ; Spark : dépendances ARM à vérifier ; anciennes cartes : pas cette accélération NVFP4 | Scripts Sana ; aucun nœud officiel couvrant toutes ces variantes confirmé | **Apache-2.0** ; **oui** pour les artefacts ainsi licenciés | **Tester** comme moteur de prévisualisation |
| **SANA-Video 2.0 5B**, 720p/193 images/8 s ; poids disponibles au 04-11-2026 | Nouvelle génération de vidéo, candidat alternatif à H3 sur certains styles | Référence 50 étapes ; pic VRAM exact pour vos machines non établi. Distillation **DMD 4 étapes** publiée en aperçu, **texte-vers-vidéo seulement** ; ne pas extrapoler aux références personnages | Scripts et poids officiels ; pas de preuve de nœud ComfyUI complet pour cette version | **Apache-2.0** sur la fiche 5B ; **oui** | **Tester** ; conserver H3 comme référence qualité |
| **SANA-Video 2.0 14B** | Variante plus lourde annoncée | Documentation : **Coming soon** ; poids/configuration non disponibles dans le catalogue consulté | Aucun paquet exploitable confirmé | **Indéterminée** pour les futurs poids | **Écarter de l’intégration immédiate** |
| **LongSANA**, 2B, instantané 04-11-2026 | Vidéos longues avec attention bornée ; scènes d’ambiance | Annonce de débit dans son protocole, pas preuve de débit sur votre parc. Pic mémoire local et ARM non établis | Scripts de la famille Sana | **Apache-2.0** pour le code ; vérifier poids/base exacts avant service | **Tester** seulement si les plans longs deviennent prioritaires |
| **SANA-Streaming**, article **28-05-2026**, 2B | Édition vidéo-vers-vidéo en flux ; piste directe pour modifier l’apparence sans régénérer tout le mouvement | Article : **1280×704, 24 i/s de bout en bout sur une 5090**, cœur DiT 58 i/s. Ce résultat n’établit ni fidélité de visage, ni débit à 475 W, ni support GB10. 5080 non attestée ; V100/Turing hors recette quantifiée | Code/docs dans Sana et poids publiés ; pas de nœud ComfyUI officiel vérifié. La fiche de poids seule est peu documentée | **Apache-2.0** sur les poids ; **oui**, dépendances à contrôler | **Tester en priorité R&D** pour retouches et variantes |
| **SANA-WM**, **2,6B**, versions bidirectionnelle et streaming, 2026 | Vidéo longue avec **trajectoire caméra 6-DoF** ; préparer des mouvements reproductibles | Pipeline avec raffineur LTX ; génération minute/720p annoncée sur un GPU, sans garantie 5090 dans ce chiffre. Recette FP4 cible sm_100/sm_120 ; **sm_121/ARM non démontré par cette mention**. Mémoire totale à mesurer ; V100/Turing hors recette | Scripts image + prompt + trajectoire, pas contrôle direct ajouté à H3 | **Apache-2.0** sur les poids WM consultés ; **oui**, termes des composants LTX/Gemma séparés | **Tester** pour caméra/prévisualisation, pas pour garantir l’identité |

Sources : [catalogue officiel et variantes disponibles](https://nvlabs.github.io/Sana/docs/model_zoo/), [intégration ComfyUI documentée](https://nvlabs.github.io/Sana/docs/ComfyUI/comfyui/), [SANA-Video et benchmark 5090](https://nvlabs.github.io/Sana/Video/), [documentation Video 2.0 et limites du 14B](https://nvlabs.github.io/Sana/docs/sana_video2/), [licence des poids Video 2.0 5B](https://huggingface.co/Efficient-Large-Model/SANA-Video_2.0_5B_720p), [article SANA-Streaming](https://arxiv.org/abs/2605.30409), [poids Streaming](https://huggingface.co/Efficient-Large-Model/SANA-Streaming), [fonctionnement et quantification WM](https://nvlabs.github.io/Sana/docs/sana_wm/), [poids WM bidirectionnels](https://huggingface.co/Efficient-Large-Model/SANA-WM_bidirectional).

**Pour l’aspect « jeu vidéo » :** SANA-Streaming et Transfer sont des candidats à une conversion d’apparence. Ils peuvent aussi modifier visage, bijoux ou textures ; sélectionner d’abord quelques plans où la géométrie est bonne et le matériau trop synthétique. Ni leur nom ni une démo ne prouvent une conversion photoréaliste stable de tous les plans H3.

### 5.2 ChronoEdit, GEN3C, Lyra et les modèles voisins

| Élément / version datée | Apport Creative | Faisabilité locale | Intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|---|
| **ChronoEdit-14B**, publié **29-10-2025**, distillation 8 étapes ; upscaler LoRA **10-11-2025**, PaintBrush **16-11-2025** | Éditer une image avec raisonnement temporel ; préparer costume, pose et références. Le nom ne signifie pas montage temporel arbitraire d’une vidéo entière | **34 Go** avec offload, **38 Go** avec raisonnement temporel selon README : dépasse la 5090 32 Go dans le profil publié ; 5080 non. Spark a la capacité mais ARM/extensions non validés. Prompt enhancer optionnel jusqu’à ~60 Go ; V100/Turing hors configuration | Diffusers, scripts et LoRA ; nœud officiel non confirmé. 2B et distillation 4 étapes restent annoncés, pas de distribution officielle confirmée | **NOML** pour les poids ; **oui**. Fiche : métadonnée Apache et corps NOML contradictoires ; retenir le texte applicable aux poids, code Apache | **Tester sur Spark après port**, priorité moyenne |
| **GEN3C**, CVPR 2025 ; code **06-06-2025** | Vidéo contrôlée par caméra et cache 3D ; réutiliser une géométrie plutôt que réinventer le décor à chaque vue | **43 Go de pic même avec offload** ; A100/H100 testés. 5090/5080 hors profil ; Spark capacité plausible, ARM à porter ; V100/Turing hors cible | Scripts, profondeur/caméra et environnement ViPE ; pas de nœud officiel confirmé | **NOML** poids, Apache code ; **oui** | **Tester en R&D**, coût d’intégration élevé |
| **Lyra 1**, **23-09-2025** | Reconstruction/génération de mondes 3D/4D, décodage en Gaussian Splatting ; décor réutilisable entre plans | Pipeline SDG/GEN3C avec référence ~43 Go offload ; pas confort 5090. Spark à porter ; V100/Turing hors profil | Scripts reconstruction, génération et rendu | **NOML** poids, Apache code ; **oui** | **Tester** si Creative développe des décors persistants |
| **Lyra 2**, **15-04-2026**, entraînement/GUI ajoutés **20-07-2026** | Mondes persistants explorables avec mémoire longue | Pile validée H100/Ubuntu/CUDA 12.8 ; dépendances x86 et attention à adapter pour sm_120/ARM. Pas de minimum local fiable établi ; 16 Go non crédible sans nouvelle recette | Dépôt officiel, GUI, outils de reconstruction et entraînement | **Recherche** : poids sous **NVIDIA Internal Scientific Research and Development Model License** ; **non** pour le service payant | **Écarter de la production** |
| **PiD / PiD 1.5**, code **25-05-2026**, mise à jour **09-07-2026** | Décodage de latents d’image en pixels, détails en peu d’étapes ; intéressant pour références haute résolution | Exemple officiel 512²→2048², 4 étapes, **<1 s / ~13 Go sur 5090**. Pas de preuve de compatibilité directe avec les latents H3 ni de cohérence vidéo. Spark non validé ; anciennes cartes non ciblées | Intégration ComfyUI annoncée **27-05-2026** ; types de latents pris en charge définis par modèle | **NSCL** poids ; **non**. Code Apache ne libère pas les poids | **Écarter du service commercial** |
| **Difix3D+**, CVPR 2025, code **11-06-2025** | Retire des artefacts de vues issues de NeRF/3DGS en une étape ; utile avant un plan sur décor reconstruit | Dépend de la reconstruction et du pipeline ; mémoire minimale pour vos machines non établie. Pas une super-résolution générale garantie sur MP4 H3 | Diffusers/scripts, pas de nœud officiel vérifié | **Noncommerciale** dans la licence du dépôt ; **non** | **Écarter de la production payante** ; préférer étudier Harmonizer |
| **ViPE 1.2.0**, **juin 2026**, traitement long ajouté **septembre 2026** | Estime poses caméra, profondeur et intrinsics d’une vidéo ; fournit des contrôles pour VFX et reconstruction | CUDA/extensions ; compiler pour sm_120 si nécessaire, ARM non confirmé. Budget dépend de la résolution/fenêtre ; ancienne pile sur Volta non attestée | `nvidia-vipe`, Python, sorties géométriques exploitables par un worker | **Apache-2.0**, **oui pour ce code**, mais dépendance optionnelle **UniK3D BY-NC-SA** à exclure d’un pipeline commercial | **Tester** pour vos plans VFX |
| **3DGRUT 2.0.0**, **juin 2026** | 3DGUT/3DGRT : reconstruction et rendu de splats ; textures harmoniques neuronales dans v2. Décor stable et caméra reproductible | RTX 5090/5080 et Turing candidates, mémoire selon scène ; **3DGRT nécessite RT**, pas 3DGUT de la même façon. V100 sans RT : pas ce chemin GRT. ARM Spark non validé | Code CUDA/Python, conversion de scènes ; pas de nœud vidéo H3 direct | **Apache-2.0** ; **oui**, contenus et autres composants séparés | **Tester** si besoin réel de décors 3D |
| **ByG / Bootstrap Your Generator**, ICML **2026** | Méthode d’édition sans paires, dont démos stylisé→photo ; piste pertinente pour l’aspect synthétique | Aucun paquet de poids/code exploitable confirmé sur la page officielle ; mémoire et support matériel inconnus | Papier/démos ; pas un SDK installable démontré | **Indéterminée** ; commercial non établi | **Surveiller** |
| **Video Storyboarding / Identity–Motion Trade-offs**, travaux 2024–2025 | Injection de caractéristiques entre plans ; étudie explicitement le compromis identité/mouvement | Expériences VideoCrafter2/T2V-Turbo/Wan, pas de port H3 validé trouvé. Aucun budget sm_120/ARM établi pour un paquet prêt à l’emploi | Articles et démos ; aucune intégration H3 confirmée | **Indéterminée** pour un outil distribuable complet | **Surveiller**, ne pas promettre une solution d’identité installable |

Sources datées et licences : [ChronoEdit, disponibilité et mémoire](https://github.com/nv-tlabs/ChronoEdit), [fiche ChronoEdit](https://huggingface.co/nvidia/ChronoEdit-14B-Diffusers), [GEN3C](https://github.com/nv-tlabs/GEN3C), [historique Lyra](https://github.com/nv-tlabs/lyra), [Lyra 1](https://raw.githubusercontent.com/nv-tlabs/lyra/main/Lyra-1/README.md), [Lyra 2 et licence des poids](https://raw.githubusercontent.com/nv-tlabs/lyra/main/Lyra-2/README.md), [installation Lyra 2](https://raw.githubusercontent.com/nv-tlabs/lyra/main/Lyra-2/INSTALL.md), [PiD, résultats matériels](https://research.nvidia.com/labs/sil/projects/pid/index.html), [versions PiD](https://raw.githubusercontent.com/nv-tlabs/PiD/main/README.md), [licence des poids PiD](https://huggingface.co/nvidia/PiD), [Difix3D+](https://github.com/nv-tlabs/Difix3D), [licence Difix](https://raw.githubusercontent.com/nv-tlabs/Difix3D/main/LICENSE.txt), [ViPE et dépendances](https://raw.githubusercontent.com/nv-tlabs/vipe/main/README.md), [3DGRUT](https://raw.githubusercontent.com/nv-tlabs/3dgrut/main/README.md), [licence 3DGRUT](https://raw.githubusercontent.com/nv-tlabs/3dgrut/main/LICENSE), [ByG](https://research.nvidia.com/labs/par/projects/byg/), [Video Storyboarding](https://research.nvidia.com/labs/par/projects/video_storyboarding/), [publication NVIDIA sur identité/mouvement, 25-07-2025](https://research.nvidia.com/publication/2025-07_identity-motion-trade-offs-text-video-generation).

### 5.3 La cohérence des personnages demande une chaîne de contrôle

Aucun des outils vérifiés ci-dessus n’est une garantie universelle de même personnage sur des séquences H3 indépendantes. GEN3C et Lyra ciblent surtout la cohérence de scène/espace ; une reconstruction 3D d’un décor ne garantit pas un visage récurrent animé.

Pour Creative : établir une fiche visuelle approuvée du personnage ; réutiliser les fonctions de références et première/dernière image déjà disponibles dans votre moteur ; choisir des plans courts et raccordables ; comparer visages, coiffure, vêtements et accessoires au début, au milieu et à la fin. Une passe Transfer ou de raffinement doit passer cette même vérification. Des corrections locales sur quelques images de référence sont généralement moins risquées qu’une conversion agressive de tout le plan.

## 6. Accélération : où TensorRT aide réellement

### 6.1 Versions et usages vérifiés

| Outil / version observée au 04-11-2026 | Apport concret | Compatibilité locale | Intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|---|
| **TensorRT 11.4.1** | Compile/optimise un graphe pris en charge, fusionne opérations et exploite les précisions disponibles ; intéressant pour réseaux fixes répétés | Matrice actuelle : **SM ≥7.5**, x86-64 et Linux SBSA ARM64 ; sm_120/sm_121 couverts par les plateformes appropriées. **V100 sm_70 exclue**. Mémoire dépend du modèle et du workspace | ONNX/API/Python/C++, conteneurs ; export et validation nécessaires | **Propriétaire** pour distribution/runtime NVIDIA ; **oui selon EULA**, composants open source séparés | **Tester ciblé**, pas conversion globale automatique de H3 |
| **TensorRT-RTX 1.7**, notes **15-10-2026** | Runtime orienté RTX, compilation JIT et moteurs plus portables ; utile pour application locale et petits sous-réseaux | Turing et plus selon matrice ; sm_120 et sm_121. Linux ARM64/DGX Spark annoncé depuis 1.6 ; V100 exclue. Le moteur JIT et le cache ont leur propre coût initial | SDK C++/Python ; moteur/runtime spécifiques, pas remplacement binaire de TensorRT classique | **Propriétaire** ; **oui selon EULA** | **Tester** pour intégrations dédiées |
| **ComfyUI_TensorRT**, branche master au 04-11-2026 | Accélération de modèles explicitement gérés : SD, SDXL, SVD/SVD-XT, Flux, etc. | Exemples : SVD ~16 Go, SVD-XT ~24 Go, Flux >24 Go. 5090 nécessite versions compatibles ; ARM non garanti par le README ; Volta hors TensorRT actuel | Nœuds **existants**, export puis moteur statique/dynamique. **H3 et Pika ne figurent pas dans sa liste** ; LoRA/ControlNet non compatibles dans le README consulté | **MIT** pour les nœuds ; **oui**, poids et runtime séparés | **Écarter comme accélérateur H3 prêt à l’emploi** ; tester pour pipelines secondaires compatibles |
| **NVIDIA Model Optimizer / ModelOpt 0.48.0**, **02-11-2026** | Quantification FP8/NVFP4, calibration, distillation/pruning selon modèle ; baisse de mémoire pouvant éviter un offload coûteux | NVFP4 natif sur Blackwell ; FP8 sur GPU et kernels appropriés. 5090/5080 et GB10 candidats, mais recette ARM et architecture du modèle à valider. V100 et RTX20 : aucun gain natif NVFP4/FP8 à attendre | Python, exemples Diffusers/ONNX/TensorRT ; pas un bouton générique dans ComfyUI | **Apache-2.0** ; **oui** pour le code | **Tester en priorité sur le goulot identifié** |
| **TensorRT-LLM 1.4.0rc2**, **28-10-2026** ; roue **1.4.0rc2.post1** | LLM/VLM et désormais **VisualGen** pour images/vidéo. Potentiel pour encodeur de prompt, juge, et modèles vidéo pris en charge | Dépend du modèle/backend, pas une garantie 5090/Spark. Le chemin H3 comporte une restriction d’attention détaillée ci-dessous. Volta hors pile actuelle ; RTX20 non cible des recettes modernes | Python, `trtllm-serve`, NGC ; **préversion**, pas une version finale 1.4.0 | **Apache-2.0** pour le cœur, sous-répertoires et poids avec licences propres ; **oui sous ces conditions** | **Tester sélectivement** ; Sol-H3 local est plus directement documenté pour vous |

Sources : [notes TensorRT](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/release-notes.html), [matrice TensorRT](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/support-matrix.html), [TensorRT-RTX 1.7](https://docs.nvidia.com/deeplearning/tensorrt-rtx/latest/getting-started/release-notes-1/1.7.html), [matrice RTX](https://docs.nvidia.com/deeplearning/tensorrt-rtx/latest/getting-started/support-matrix.html), [page de téléchargement RTX](https://developer.nvidia.com/tensorrt-rtx), [nœuds ComfyUI TensorRT et limites](https://raw.githubusercontent.com/comfyanonymous/ComfyUI_TensorRT/master/README.md), [dépôt et licence des nœuds](https://github.com/comfyanonymous/ComfyUI_TensorRT), [versions ModelOpt](https://github.com/NVIDIA/Model-Optimizer/releases), [exemples ModelOpt](https://raw.githubusercontent.com/NVIDIA/Model-Optimizer/main/README.md), [quantification diffusion et configurations 5090 validées](https://github.com/NVIDIA/Model-Optimizer/blob/main/examples/windows/torch_onnx/diffusers/README.md), [versions TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/releases), [licences TensorRT-LLM et composants](https://raw.githubusercontent.com/NVIDIA/TensorRT-LLM/main/LICENSE).

**Écart documentaire à conserver :** les notes TensorRT-RTX décrivent **1.7**, tandis que la page développeur de téléchargement ouverte affiche encore **1.6**. La publication des notes ne prouve pas que le même paquet 1.7 est téléchargeable pour toutes les plateformes.

### 6.2 TensorRT-LLM n’est plus limité aux LLM, mais H3 reste particulier

La [documentation VisualGen actuelle](https://github.com/NVIDIA/TensorRT-LLM/blob/main/docs/source/models/visual-generation.md) inclut MiniMax-H3, Cosmos 3 et d’autres générateurs. Pour H3, elle décrit texte-vers-vidéo/audio, première/dernière image et références, mais restreint actuellement **TRTLLM attention à SM100/SM103**. Cela ne démontre donc pas ce backend d’attention sur **SM120/SM121**. D’autres backends et ports doivent être vérifiés séparément ; la présence de H3 dans le tableau de modèles ne constitue pas une validation locale.

Le mécanisme expérimental sleep/wake H3 conserve un backing en RAM hôte ; il peut éviter des rechargements, mais reste interne, monogpu et non exposé par l’API publique VisualGen/HTTP. Sa couverture complète publiée concerne FP8 texte-vers-vidéo/audio, pas toutes les variantes de références. Ce n’est pas encore une fonction de planification prête à brancher dans votre ComfyUI.

### 6.3 FP4/FP8 : mesurer l’image, pas seulement la mémoire

Un fichier de poids en quatre bits ne garantit pas des multiplications quatre bits rapides. Le gain dépend des couches converties, des kernels, des conversions, du déchargement CPU et de la taille des matrices. Ne pas extrapoler une recette Flux ou B200 à H3 sur 5090.

Conserver une référence BF16/FP16 ; calibrer sur peau, cheveux, mouvements rapides, fumée et lumières saturées ; comparer les mêmes seeds, références et durées. Vérifier aussi l’audio et la synchronisation. Une réduction mémoire permettant de garder tout le modèle résident peut être plus utile qu’un gain de calcul isolé.

Isoler les environnements : TensorRT 11 ne conserve pas toutes les anciennes API ; Audio2Face-3D SDK documente encore TensorRT **<11**. Mettre à jour tous les workers vers « le dernier TensorRT » casserait potentiellement des intégrations.

## 7. Finition : super-résolution, débruitage, HDR et interpolation

### 7.1 La voie la plus pratique : les nœuds RTX Video officiels

Le dépôt **Comfy-Org/ComfyUI_Nvidia_VFX_Nodes**, anciennement `Nvidia_RTX_Nodes_ComfyUI`, fournit réellement **RTX Video Super Resolution**, **RTX Video HDR** et **RTX Video Frame Generation**. Ce sont des traitements de vos images/vidéos dans ComfyUI ; il ne faut pas les confondre avec l’amélioration d’une vidéo seulement pendant sa lecture dans un navigateur.

**État au 04-11-2026 :** le README demande PyTorch **cu130 ou supérieur** et un GPU RTX ; le fichier de dépendances indique **`nvidia-vfx>=0.2`**, ce qui est un minimum et non le numéro de la dernière roue. La publication **AI for Media R22 du 11-09-2026** annonce une roue Python **2.0.0**. Code des nœuds **Apache-2.0**, **commercial : oui pour ce code** ; bibliothèques/modèles NVIDIA sous leurs termes propres. **Verdict : adopter la voie d’intégration**, après comparaison du traitement et vérification du paquet réellement installé.

Sources : [dépôt officiel, fonctionnalités et exigences](https://github.com/Comfy-Org/ComfyUI_Nvidia_VFX_Nodes), [dépendances minimales](https://raw.githubusercontent.com/Comfy-Org/ComfyUI_Nvidia_VFX_Nodes/main/requirements.txt), [annonce datée R22 et roue 2.0.0](https://forums.developer.nvidia.com/t/ai-for-media-latest-release/382943).

| Fonction / version pertinente | Apport Creative | Matériel local | Intégration et licence ; commercial | Verdict |
|---|---|---|---|---|
| **RTX Video Super Resolution**, SDK RTX Video **1.1** et distribution VFX **R22** | Agrandit, réduit bruit et certains défauts de compression ; gain immédiat sur la sortie 1344×768. Les modes débruitage/défloutage à taille identique peuvent éviter un surtraitement | 5090 et 5080 adaptées ; SDK 1.1 documente RTX20+ sous Windows. Nœuds : RTX et pile CUDA requise. V100 non. DGX Spark Linux ARM : ne pas déduire le support de la seule mention RTX Spark | Nœuds officiels, SDK, Python wheel, NIM ; **Propriétaire**, commercial possible selon EULA/runtime. Code des nœuds Apache | **Adopter**, réglage conservateur et comparaison à un agrandissement classique |
| **RTX Video HDR / TrueHDR**, SDK 1.1 / R22 | Crée une interprétation HDR à partir du SDR ; améliore parfois l’impact lumineux sur un écran HDR | RTX compatible selon distribution ; 5090/5080 candidates, V100 non. ARM Linux non confirmé | Nœud, SDK ; **Propriétaire**, commercial selon termes | **Tester uniquement pour une vraie livraison HDR** ; aucun bénéfice garanti en SDR |
| **Video Effects SDK / Maxine, désormais AI for Media**, **R22**, docs **22-09-2026** | Ensemble VSR, débruitage, fond, rééclairage de personne et VFG ; pipeline avec initialisation partagée | Windows : cartes RTX selon effet, Blackwell sm_120 et Windows ARM sm_121 référencés. Linux : matrice surtout datacenter/x86 ; ne pas considérer tous les binaires Windows transposables. 5090 prouvée par les tables de performance de plusieurs effets ; 5080 à profiler ; Volta hors cible | SDK C/C++, SDKs modulaires NGC, Python/NIM selon fonction ; **Propriétaire**, commercial sous termes du paquet | **Adopter VSR**, **tester les autres effets séparément** |
| **Artifact Reduction** du VFX historique | Réduit blocs, ringing et bruit de compression, surtout **H.264** ; utile sur des sources déjà abîmées | Dépend de l’ancien SDK/effet, pas de promesse sur chaque carte moderne/ARM. Débruitage moderne à privilégier si pipeline neuf | Ancienne API VFX ; **Propriétaire**, commercial selon EULA | **Tester seulement si de vrais artefacts de codec sont présents** ; ne corrige pas anatomie ou incohérence de génération |
| **RTX Video Frame Generation**, R22 | Ajoute des images intermédiaires ; conversion de cadence, ralenti à partir de mouvement exploitable | Nœuds : **RTX40 ou plus**, donc 5090/5080 oui ; RTX20 et V100 non. SDK : Ada/Blackwell, Hopper Linux x86 selon filtre ; Windows ARM RTX Spark ne valide pas DGX Spark Linux | Nœud officiel ou VFX ; **Propriétaire**, code des nœuds Apache ; commercial selon runtime. R22 annonce 2×/4×, 6×/8× en aperçu | **Tester**, pas en finition systématique de toutes les prises |
| **Optical Flow SDK 5.0**, **février 2023**, dernière version publique trouvée | Vecteurs de mouvement matériels ; **NvFRUC** produit des images intermédiaires. Utiles aussi comme signal de contrôle de mouvements/défauts | OFA **Turing et plus** : vos RTX20 peuvent servir ici. V100 sans OFA. Sur Blackwell, interroger les capacités réelles avec l’API ; paquet ARM GB10 non confirmé | SDK C/C++, CUDA/DirectX selon plateforme ; pas de nœud officiel H3 confirmé. **Propriétaire**, SDK annoncé utilisable commercialement | **Tester** pour délestage Turing ou outil spécialisé ; choisir d’abord le nœud VFG sur 5080 si disponible |

Sources : [RTX Video SDK](https://developer.nvidia.com/rtx-video-sdk), [version 1.1 et plateformes](https://developer.nvidia.com/rtx-video-sdk/getting-started), [documentation VFX actuelle](https://docs.nvidia.com/maxine/vfx/latest/index.html), [installation Windows et architectures](https://docs.nvidia.com/maxine/vfx/latest/WindowsVFXSDK/InstalltheVFXSDK.html), [installation Linux](https://docs.nvidia.com/maxine/vfx/latest/LinuxVFXSDK/InstalltheVFXSDK.html), [tables de performance par effet et GPU](https://docs.nvidia.com/maxine/vfx/latest/WindowsVFXSDK/PerformanceReference.html), [VFG et plateformes](https://docs.nvidia.com/maxine/vfx/latest/Filters/VideoFrameGeneration.html), [rééclairage VFX](https://docs.nvidia.com/maxine/vfx/latest/Filters/VideoRelighting.html), [guide historique Artifact Reduction](https://docs.nvidia.com/deeplearning/maxine/vfx-sdk-programming-guide/index.html), [Optical Flow, téléchargement/version/licence](https://developer.nvidia.com/opticalflow/download), [documentation Optical Flow et NvFRUC](https://docs.nvidia.com/video-technologies/optical-flow-sdk/index.html).

### 7.2 Ce que l’upscale doit préserver

**1344×768 = 1,75 ; 1920×1080 = 1,777…** Un redimensionnement direct vers 1080p ou 4K 16:9 déforme légèrement le plan. Définir un recadrage, un padding ou une taille intermédiaire respectant l’aspect. Les nœuds imposent aussi des multiples de taille ; conserver une politique explicite, identique pour tous les plans.

Pour une source synthétique propre, commencer par un mode prévu pour source de bonne qualité ; réserver le débruitage fort aux défauts visibles. Inspecter pores, cheveux, yeux, inscriptions, fumée et flammes en lecture : une image fixe plus nette peut scintiller davantage en mouvement. Un upscale ne reconstruit pas la vérité perdue et n’enlève pas automatiquement le rendu « jeu vidéo ».

Le chemin **10 bits RGB10A2 n’est pas une conversion HDR**. Un nœud HDR doit être suivi d’une gestion cohérente de primaires, transfert PQ/HLG, profondeur et métadonnées jusqu’au fichier. Vérifier que le nœud d’enregistrement ne ramène pas silencieusement le résultat à huit bits.

L’interpolation peut produire des doubles contours sur sabres, dents, fumée et occultations. Elle augmente le nombre d’images, sans accélérer la synthèse des images originales. Pour un rendu cinéma à 24 i/s, l’appliquer seulement à une conversion ou un ralenti motivé ; vérifier les coupes et conserver la durée audio.

## 8. Voix, transcription, avatars et synchronisation labiale

### 8.1 Avatars 3D et reprise d’une vidéo existante : deux chaînes distinctes

| Élément / version datée | Apport Creative | Matériel et local | Intégration | Licence ; service payant | Verdict |
|---|---|---|---|---|---|
| **Audio2Face-3D SDK**, ouvert **24-09-2025** ; modèle diffusion **v3.0** ; Samples **v2.0, 11-03-2026** | Audio→animation faciale/expressions sur un personnage **riggé** ; avatars contrôlables et reproductibles | SDK : **4 Go VRAM**, 8 Go RAM recommandés ; Windows/Linux x86. CUDA ≥12.8 et **<13**, TensorRT ≥10.13 et **<11** documentés. 5090 possible avec pile correspondante ; Turing à valider ; V100 hors TensorRT moderne. GB10 ARM non établi et pile CUDA à réconcilier | SDK C++/CUDA/TensorRT, ONNX, samples et connecteurs DCC/Unreal selon produit ; pas un nœud réparant la bouche d’un MP4 | **MIT** SDK ; **NOML** modèle v3.0 ; **oui** sur cette voie, runtime NIM séparé | **Adopter si avatars 3D**, **tester** le rig et les expressions |
| **ACE**, famille de services, état 04-11-2026 | Orchestre voix, compréhension, animation et rendu pour un avatar interactif ; composants réutilisables pour production | Aucun budget GPU unique : dépend du cumul ASR/LLM/TTS/A2F/rendu ; réserver mémoire et workers. ARM et Volta doivent être vérifiés composant par composant | SDKs/services NIM, APIs, Unreal/Omniverse selon composant ; pas une application unique ni un modèle unique | **Propriétaire** pour produits/services, composants ouverts distincts ; **commercial conditionnel à l’offre** | **Tester les composants utiles**, écarter une grosse orchestration pour du rendu batch simple |
| **Audio2Face-2D NIM 1.0**, artefact **25-02-2025** | Portrait + audio→visage parlant, basé SpeechLivePortrait | Conteneur **non multi-architecture**, ARM non. La taille compressée de 22,79 Go n’est pas une exigence VRAM. Minimum local fiable non établi dans la page examinée | NGC/NIM ; page marquée **End of Support** | **Propriétaire**, EULA AI Enterprise et licence communautaire des poids indiquées ; **commercial à établir pour cette distribution** | **Écarter pour un nouveau déploiement** |
| **LipSync**, modèle initial **17-10-2025**, amélioré **R22 septembre 2026**, 613M paramètres | **Vidéo déjà existante + audio cible→bouche resynchronisée** ; outil directement pertinent pour vos avatars générés | Fiche : Turing/Ampere/Ada/Hopper/Blackwell, Windows/Linux x86. 5090/5080 candidates ; RTX20 selon mémoire/paquet ; V100 et Linux ARM GB10 non établis. Minimum VRAM non publié dans la fiche consultée ; une face, vidéo jusqu’à 4K | SDK AR / NIM, collection NGC **accès privé/restreint** ; pas de nœud ComfyUI officiel confirmé | **NOML** poids ; **oui** pour les poids, accès et termes logiciels du produit à obtenir | **Tester en priorité après obtention d’accès** ; ne pas présenter comme téléchargement public libre |

Sources : [SDK Audio2Face-3D et exigences](https://github.com/NVIDIA/Audio2Face-3D-SDK), [annonce d’ouverture et versions initiales](https://developer.nvidia.com/blog/nvidia-open-sources-audio2face-animation-model/), [poids Audio2Face v3.0](https://huggingface.co/nvidia/Audio2Face-3D-v3.0), [versions Samples](https://github.com/NVIDIA/Audio2Face-3D-Samples/releases), [Audio2Face-2D, version et fin de support](https://catalog.ngc.nvidia.com/orgs/nim/nvidia/containers/maxine-audio2face-2d/1.0), [LipSync, modèle, matériel et restrictions](https://build.nvidia.com/nvidia/lipsync/modelcard), [collection LipSync et conditions d’accès](https://catalog.ngc.nvidia.com/orgs/nvidia/maxine/collections/nvarlipsync/-?_lr=1).

Une voix française n’implique pas automatiquement une qualité française égale pour les lèvres. Pour LipSync, tester les labiales **p/b/m**, les fricatives **f/v**, les voyelles arrondies, les accents québécois et les têtes de profil. Les améliorations R22 sur occultations et dents sont utiles mais ne prouvent pas la réussite sur vos personnages.

### 8.2 TTS, nettoyage et transcription

| Élément / version datée | Apport Creative et français | Matériel local | Intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|---|
| **Riva / Speech NIM 26.10.0**, **07-10-2026** ; **Magpie TTS Multilingual 357M v2607**, **21-07-2026** ; catalogue API **v4.0** | **Français fr-FR disponible**, parmi 12 langues ; voix synthétiques et production batch. Le français canadien n’est pas un profil garanti. Le nom 357M et les 364M annoncés dans le corps de fiche ne sont pas deux modèles différents à inventer | NIM TTS actuel : **CC≥8**, **16 Go minimum**, RTX50 et **DGX Spark explicitement pris en charge**. 5090 oui ; 5080 à réserver au service, marge mémoire à vérifier ; V100 et RTX20 exclus de ce NIM | NIM local HTTP/gRPC/WebSocket ; NeMo pour les poids ; voie C++ plus légère ci-dessous. Zero-shot multilingue existe aussi mais accès restreint | **NOML** poids ; **oui**. Runtime/NGC sous termes séparés | **Tester puis adopter si le français satisfait vos voix de marque** |
| **Studio Voice v0.5.1**, **16-03-2026**, 183M ; **Audio Effects SDK 3.0.0**, docs **22-09-2026** | Nettoyage de voix : bruit, réverbération et qualité micro. Français à auditionner : entraînement surtout anglais. Ne compose pas musique, bruitages ou ambiance | Fiche valide notamment RTX5080/5090 ; Turing et plus selon modèle. GB10 Linux ARM non confirmé par Windows ARM/N1X. Volta hors cible. Modes haute qualité avec chunks de **6 s** et latence correspondante | AFX SDK, batch/NIM selon distribution, Broadcast pour essais ; pas de nœud officiel ComfyUI vérifié | **NOML** poids ; **oui** ; SDK **Propriétaire** avec ses conditions | **Tester** sur voix enregistrées ; éviter un traitement fort sur une TTS déjà propre |
| **Canary-1B-v2**, **14-08-2025**, ~978M | ASR **25 langues dont français**, traduction anglais↔autres langues ; contrôle des paroles et sous-titres | Référence NVIDIA A100/H100 ; pas de minimum universel dans la fiche. Petits extraits sur 8–16 Go sont une cible d’essai, pas un minimum certifié. FP16/FP32 pour V100/Turing avec backend compatible ; ARM dépend du runtime | NeMo/Transformers selon implémentation, service maison ; pas de nœud officiel ComfyUI confirmé | **CC-BY-4.0** ; **oui**, attribution | **Tester** pour ASR/traduction, surtout si Parakeet ne suffit pas |
| **Parakeet-TDT-0.6B-v3**, **14-08-2025** | ASR **25 langues dont français**, détection de langue et timestamps ; contrôler texte, sous-titrage et mots manquants. **v2 était anglais seulement** | Modèle compact mais mémoire dépend de durée/backend. 5080 appropriée ; RTX20 ou CPU via runtime léger à essayer. V100 : environnement FP16 compatible ; Spark via voie C++ documentée | NeMo et **NeMo-Speech.cpp** ; scripts/CLI/API hors ComfyUI | **CC-BY-4.0** ; **oui**, attribution | **Adopter pour la transcription française**, après validation de votre accent/vocabulaire |
| **NeMo-Speech.cpp 0.3.0**, fichier VERSION lu le **04-11-2026** | Runtime NVIDIA léger pour **Parakeet v3 et Magpie**, entre autres ; économise la file principale et l’empilement Python | CPU, CUDA et Vulkan. Archives Linux CUDA x86 **sm_75+** ; **Linux ARM64 CUDA13 pour DGX Spark explicitement documenté**. V100 : CPU/Vulkan ou compilation avec pile adaptée, pas l’archive CUDA moderne. AMD : piste Vulkan, à tester selon votre carte | C++/GGML, CLI et APIs ; GGUF/quantification selon modèle ; pas besoin de déployer tous les NIM | **Apache-2.0** runtime ; **oui**, licences des poids conservées | **Tester en priorité**, puis adopter pour délester ASR/TTS |
| **NVIDIA Broadcast 2.3.0**, annoncé **11-09-2026** | Essai rapide de Studio Voice et traitements de fichiers, VSR/VFG ; interface utile pour comparer avant d’écrire un worker | Application Windows, RTX ; exigences spécifiques par effet, VFG RTX40+. Pas application native Linux ARM DGX Spark ; V100 non | Application avec traitement offline et MCP annoncés ; automatisation de service plutôt via SDK | **Propriétaire** ; usage logiciel selon EULA, **ne pas déduire un droit de redistribution/hébergement de l’application** | **Tester pour évaluation**, SDK préféré pour le service |

Sources : [versions Speech NIM](https://docs.nvidia.com/nim/speech/26.10.0/about/release-notes.html), [Magpie, langues et versions des poids](https://huggingface.co/nvidia/magpie_tts_multilingual_357m), [Magpie du catalogue API](https://build.nvidia.com/nvidia/magpie-tts-multilingual/modelcard), [matrice TTS incluant Spark et RTX50](https://docs.nvidia.com/nim/speech/26.10.0/reference/support-matrix/tts.html), [déploiement et modèles TTS](https://docs.nvidia.com/nim/speech/26.10.0/tts/deploy-tts-model.html), [Studio Voice, poids et tests GPU](https://build.nvidia.com/nvidia/studiovoice/modelcard), [AFX 3.0.0](https://docs.nvidia.com/maxine/afx/3.0.0/index.html), [Studio Voice, fonctionnement batch](https://docs.nvidia.com/maxine/afx/3.0.0/AboutTheEffects/AboutStudioVoiceEffect.html), [Canary v2](https://huggingface.co/nvidia/canary-1b-v2), [Parakeet v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3), [runtime NeMo-Speech.cpp](https://raw.githubusercontent.com/NVIDIA/NeMo-Speech.cpp/main/README.md), [installation et plateformes C++](https://raw.githubusercontent.com/NVIDIA/NeMo-Speech.cpp/main/docs/install.md), [fonctionnement de Broadcast](https://www.nvidia.com/en-us/geforce/broadcasting/broadcast-app/faq/). Version Broadcast : annonce R22 citée en §7.1.

**Précision sur Riva :** les documentations historiques Riva, les versions de conteneurs Speech NIM et les versions de poids Magpie ne partagent pas nécessairement le même numéro. Ne pas déployer un ancien exemple anglophone puis conclure que Magpie ne parle pas français. Le modèle et le profil exacts de 26.10 doivent être enregistrés.

Version du runtime C++ : [fichier VERSION officiel, 0.3.0](https://raw.githubusercontent.com/NVIDIA/NeMo-Speech.cpp/main/VERSION). Le numéro de branche ne garantit pas la même disponibilité des binaires pour chaque plateforme.

**Pour une voix française stable :** choisir d’abord voix, débit, prononciation des noms et rendu émotionnel ; figer l’audio accepté ; seulement ensuite calculer les lèvres. Transcrire le résultat et comparer au script avant de mobiliser un générateur vidéo lourd. Garder séparées voix, musique et effets ; Studio Voice sur une piste mixée peut endommager les éléments que vous voulez conserver.

### 8.3 Audio génératif et autres pistes : limites réelles

| Élément | Apport et disponibilité | Local / intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|
| **PersonaPlex-7B-v1**, **15-01-2026** | Dialogue vocal full-duplex contrôlable ; **anglais seulement** dans la fiche, pas solution TTS française attestée | Référence Linux A100/H100 ; 5090 candidate avec mémoire à mesurer, 5080 serrée sans recette ; Spark ARM et V100 non validés. Code Python/poids, pas nœud officiel confirmé | **NOML** poids, MIT code ; **oui** | **Écarter du pipeline français courant**, tester pour avatars interactifs anglais |
| **Fugatto 1**, travail 2024 / ICLR **2025** | Démos de génération/transformation de sons, musique et voix | Le catalogue officiel audio consulté pointe article et démos ; **aucun paquet de poids/code exploitable ou service public confirmé**. Matériel local non établi | **Indéterminée** pour un outil distribuable | **Écarter de la planification de production** ; ne pas inventer une API Fugatto |
| **Audio Flamingo 3**, modèle HF 7B, 2025 | Compréhension audio : événements, parole, musique ; candidat théorique au contrôle des bruitages | Transformers, fenêtres audio ; 5090 plausible mais budget variable, ARM/Volta non validés ; nœud officiel non confirmé | **Noncommerciale**, recherche seulement sur la fiche des poids ; **non** | **Écarter du service payant** |

Sources : [PersonaPlex, code](https://github.com/NVIDIA/personaplex), [PersonaPlex, poids/langue/licence](https://huggingface.co/nvidia/personaplex-7b-v1), [catalogue officiel Audio Intelligence et Fugatto](https://raw.githubusercontent.com/NVIDIA/audio-intelligence/main/README.md), [Audio Flamingo 3, fiche effective](https://huggingface.co/nvidia/audio-flamingo-3-hf).

**Bruitages et musique :** je n’ai pas trouvé dans les distributions NVIDIA vérifiées une solution locale, commercialement claire et immédiatement déployable qui remplace votre moteur généraliste de bande-son. Magpie traite la parole ; Studio Voice améliore une voix ; Fugatto ne doit pas être présenté comme un produit téléchargeable démontré.

## 9. Encodage : NVENC, AV1 et HEVC 10 bits

**Video Codec SDK 13.1** est la version affichée au téléchargement au 04-11-2026. Il expose NVENC/NVDEC ; la page présente aussi **PyNvVideoCodec 2.0**, voie Python pour décodage/encodage et échanges avec les traitements GPU. **Licence : Propriétaire** pour le SDK ; **commercial : oui selon les conditions du SDK**, avec les licences du logiciel d’intégration et des codecs à examiner séparément. **Verdict : adopter NVENC**, pas nécessairement écrire une intégration SDK si FFmpeg satisfait déjà votre besoin.

| Carte | NVENC selon matrice officielle | AV1 encodage | HEVC 10 bits | Rôle Creative recommandé |
|---|---:|---|---|---|
| **RTX 5090** | **3**, génération 9 | Oui | Oui | Export rapide quand disponible ; privilégier le maintien de H3 en mémoire |
| **RTX 5080** | **2**, génération 9 | Oui | Oui | Worker finition + encodage AV1/HEVC ; premier choix de délestage |
| **DGX Spark** | **1**, génération 9 | Oui | Oui | Export local ARM via intégration compatible ; ne pas transférer inutilement un gros master |
| **RTX 2080 SUPER / 2070 SUPER** | **1**, génération 7 | Non | Oui | Exports HEVC/H.264, prévisualisations ; utile pour libérer les cartes Blackwell |
| **Tesla V100** | **3**, génération 6 | Non | Oui | Encodage HEVC/H.264 sur pile compatible ; **pas de B-frames HEVC** selon matrice |

**Oui, la V100 possède NVENC dans la matrice NVIDIA.** Ne pas lui appliquer la situation de l’A100. Ce tableau décrit les blocs matériels ; vérifier ensuite pilote, build FFmpeg et API réellement utilisables sur votre machine. Il ne certifie pas que la dernière pile CUDA/Python destinée à Blackwell fonctionne sur Volta.

Sources : [Video Codec SDK 13.1 et PyNvVideoCodec](https://developer.nvidia.com/video-codec-sdk), [matrice matérielle NVENC/NVDEC](https://developer.nvidia.com/video-encode-decode-support-matrix), [dépréciations SDK 13.1](https://docs.nvidia.com/video-technologies/video-codec-sdk/13.1/deprecation-notices/index.html). Dans 13.1, les anciens presets et modes de contrôle de débit sont notamment retirés à partir du pilote 590 : une vieille commande d’encodage doit être migrée, pas recopiée aveuglément.

Pour Creative, préparer deux profils vérifiés : **AV1 10 bits pour diffusion quand accepté** et **HEVC 10 bits pour compatibilité de livraison/montage**. Choisir débit ou qualité constante après inspection des gradients, cheveux, fumées et effets lumineux. Le nombre de moteurs ne signifie pas un facteur de débit identique dans tous les encodeurs : split-frame, résolution, preset et concurrence changent le résultat.

NVENC est un bloc dédié, mais les copies mémoire, le décodage, le redimensionnement CUDA et les buffers partagent des ressources avec H3. Mesurer l’impact sous charge. Éviter de recompresser le plan à chaque étape : conserver un intermédiaire de qualité suffisante, faire les effets et l’upscale, puis un seul export de livraison. Le 10 bits réduit certains défauts de quantification ; il ne récupère pas les dégradés perdus dans une source huit bits déjà écrêtée.

## 10. Omniverse, RTX Remix, DLSS et outils de développement

| Outil / état vérifié | Utilité réelle pour Creative | Local et intégration | Licence ; commercial | Verdict |
|---|---|---|---|---|
| **Omniverse / Kit 110.1.4**, documentation mise à jour **03-09-2026** | Prévisualisation, scènes USD, matériaux/lumières/caméras répétables ; générer contrôles profondeur/normales/segmentation pour Transfer ; décors pour avatars | RTX 5090/5080 adaptées au rendu RTX, mémoire selon scène ; RTX20 plus limitée. V100 sans RT : pas le renderer RTX. Support Kit Linux ARM GB10 exact non confirmé ; installer un paquet x86 sur ARM ne suffit pas. SDK/extensions, pas filtre MP4 | **Propriétaire** ; accord **mai 2026** autorisant développement, production et redistribution sous conditions ; support Enterprise distinct | **Tester** si vous voulez des décors et éclairages contrôlés |
| **RTX Remix 1.6.1**, **23-10-2026** | Capture/remaster de jeux compatibles, remplacement d’assets ; intégration ComfyUI 2.0 d’assets et DLSS 5 NR dans cette version | Outils/runtime orientés Windows et jeux ; chemin Windows ARM N1X annoncé, pas validation Linux ARM GB10. RTX50 préférable pour nouveautés, V100 hors cible ; VRAM selon scène | **MIT** pour les composants ouverts identifiés par le dépôt ; runtimes et contenus ont leurs termes propres ; **oui conditionnel au composant et aux droits des contenus** | **Écarter pour améliorer directement vos MP4 H3** ; tester si Creative travaille sur décors/jeux |
| **DLSS 5 Neural Rendering**, disponibilité 2026 ; modèle amélioré annoncé **13-10-2026**, diffusé **16-10-2026** | Rendu neuronal qui peut transformer apparence/matériaux dans des intégrations de rendu ; pertinent pour comprendre la recherche vers le photoréalisme | RTX50 et produits RTX Spark Windows selon intégration. **Pas de chemin officiel ComfyUI H3/offline généraliste confirmé** ; pas démontré DGX Spark Linux, V100 ou RTX20 pour ce NR | **Propriétaire** pour produit/runtime ; commercial via intégration et conditions NVIDIA, pas licence d’un modèle vidéo libre | **Écarter du pipeline H3 immédiat**, surveiller SDK/intégrations officielles |
| **OptiX 9.1.0 et AI Denoiser**, **décembre 2025**, version proposée au téléchargement | Réduit le bruit de rendu Monte-Carlo ; utile si vous fabriquez une vraie couche 3D, pas pour restaurer la physique d’une vidéo H3 | **Turing et plus**, pilote **R590+**, SDK Windows/Linux **x86 et ARM** ; 5090/5080 candidates, vérifier que l’application embarque aussi cette version/architecture. V100 exclue de cette version actuelle ; mémoire selon scène | **Propriétaire**, **commercial gratuit annoncé** pour le SDK | **Tester seulement pour rendu 3D**, pas priorité vidéo générative |
| **Nsight Systems 2026.5.1**, page actuelle au **04-11-2026** | Montre chargement, offload CPU, temps GPU et périodes inutilisées ; permet de cibler ce qui ralentit réellement votre file | CLI/GUI et traces ; 5090/GB10 via plateforme compatible, fonctionnalités de profilage selon GPU/pilote. Volta : ne pas supposer toutes les métriques modernes disponibles. Pas de mémoire de modèle supplémentaire imposée, overhead de profilage à mesurer | **Propriétaire**, outil de développement ; utilisation commerciale selon licence | **Adopter pour diagnostiquer**, pas comme accélération automatique |

Sources : [Kit 110.1.4, migration et date](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/110.1.4/guide/migration.html), [accord Omniverse mai 2026](https://docs.omniverse.nvidia.com/guide-kit-cae/latest/common/NVIDIA_Omniverse_License_Agreement.html), [RTX Remix, versions](https://github.com/NVIDIAGameWorks/rtx-remix/releases), [dépôt RTX Remix et composants](https://github.com/NVIDIAGameWorks/rtx-remix), [annonce DLSS 5 d’octobre](https://www.nvidia.com/en-us/geforce/news/dlss-5-faster-ai-model-hogwarts-legacy-rtx-spark-laptops/), [recherche DLSS 5](https://research.nvidia.com/labs/adlr/DLSS5/), [OptiX et débruiteur](https://developer.nvidia.com/optix), [Nsight Systems, version affichée](https://developer.nvidia.com/nsight-systems).

**Ne pas confondre les produits :** RTX Video VSR améliore des images/vidéos ; DLSS est intégré à une application de rendu et à son chemin d’exécution. Une démo spectaculaire DLSS 5 ne constitue pas la preuve d’un nœud disponible qui transforme arbitrairement vos rushes H3 en prises réelles. L’annonce d’octobre inclut aussi des disponibilités futures selon les jeux ; elles ne sont pas toutes acquises au 4 novembre.

Version et plateformes OptiX : [page de téléchargement 9.1](https://developer.nvidia.com/designworks/optix/download). Le SDK ARM existe bien ; cela ne prouve pas la disponibilité ARM de chaque moteur 3D qui utilise OptiX.

## 11. Contrôle qualité automatique : une proposition exploitable

### 11.1 Employer Cosmos comme assistant de sélection

**Choix initial : Cosmos Reason2-2B**, plutôt qu’un Cosmos 3 complet de 60 Go minimum. Tester le 8B en créneau réservé si son jugement apporte assez de précision. Le 2B est déjà annoncé à 24 Go minimum : **pas de déploiement promis sur la 5080 16 Go sans recette mémoire distincte**. Sur la 5090, ne pas le garder résident en concurrence avec H3. Le Spark peut l’exécuter en alternance avec Flex ; il ne devient pas gratuit en temps GPU parce que la RAM est grande.

Faire deux passes : un tri peu coûteux sur vignettes/échantillons, puis une inspection temporelle plus dense des candidats. L’échantillonnage à quatre images par seconde peut manquer un défaut d’une image ; associer contrôles déterministes et inspection humaine des livraisons. Pour une scène de sabre/explosion, transmettre le brief et les effets intentionnels au juge.

Grille proposée — **conception Creative à calibrer, pas score officiel NVIDIA** :

| Axe | Ce que le juge doit décrire | Contrôle complémentaire |
|---|---|---|
| Identité | Changement de visage, coiffure, costume, accessoires, avec temps précis | Comparer aux références approuvées ; revue humaine des gros plans |
| Apparence filmée | Peau cireuse, matériaux uniformes, ombres absentes, netteté artificielle | Comparaison aveugle sur écran de livraison |
| Temps et mouvement | Flicker, apparition/disparition, glissement de texture, membres incohérents | Parcourir toutes les images autour du défaut, pas seulement les vignettes |
| Lumière et VFX | Réaction de la peau et du décor au sabre/explosion, ombres et reflets | Confronter à l’emplacement et à la durée de l’effet prévus |
| Parole | Bouche mobile pendant le silence, mouvements décalés | Parakeet : texte exact, timestamps ; écoute et inspection labiale |
| Technique | Image noire, doublon/freeze, coupe inattendue, durée ou ratio erronés | Décodage complet, nombre d’images, cadence, résolution, audio, niveaux et métadonnées |

Demander un résultat structuré contenant verdict **accepter / revoir / rejeter**, défauts, horodatages et incertitude, avec citations descriptives de ce qui est visible. Ne pas interpréter une explication éloquente comme un score calibré. Commencer sur **30 à 50 prises déjà annotées par votre équipe**, mesurer faux rejets et défauts manqués, puis ajuster le seuil. Le critère utile est le **coût par prise acceptée**, incluant retouches et régénérations.

### 11.2 Autres briques AI for Media pour le contrôle

La publication R22 annonce **Active Speaker Detection** et **Synthetic Video Detector** améliorés. Le premier peut signaler quel personnage semble parler ; il ne mesure pas à lui seul la précision phonétique. Le second détecte du contenu synthétique : **vos vidéos le sont volontairement**, donc ce n’est pas une métrique de réalisme cinématographique ou de satisfaction client.

**Version : R22, septembre 2026. Intégration : SDK/NIM selon fonction. Licence : Propriétaire pour les distributions ; droits des poids et accès exacts non établis ici. Local :** la note annonce notamment RTX5090 pour le détecteur, pas un minimum VRAM ni une validation DGX Spark ARM ; V100 non confirmée. **Verdict : tester ASD si dialogues multi-personnages ; écarter Synthetic Video Detector comme juge principal de qualité.** Source : [annonce NVIDIA datée R22](https://forums.developer.nvidia.com/t/ai-for-media-latest-release/382943).

## 12. Ordre d’intégration conseillé pour Nexora

| Étape | Action concrète | Machine proposée | Critère de décision |
|---|---|---|---|
| **1 — Référence** | Archiver 30–50 prises, paramètres H3, version, temps complet, défauts et acceptation | Parc actuel | Même jeu de comparaison pour tous les essais |
| **2 — Finition** | Worker VSR conservateur + export AV1/HEVC 10 bits, sans HDR automatique | **5080** ; RTX20/V100 pour exports compatibles | Plus de prises acceptées, sans flicker ni déformation du ratio |
| **3 — Audio** | Parakeet v3 ; essai Magpie français via NeMo-Speech.cpp ; texte approuvé avant lipsync | **CPU / RTX20** ou créneau Spark, selon débit mesuré | Prononciation, accent, exactitude et stabilité de voix |
| **4 — H3 plus rapide** | Environnement Sol-H3 isolé ; comparer d’abord optimisations sans changer le nombre d’étapes, puis profils approximatifs/distillés | **5090 à 475 W**, puis **Spark** | Secondes et énergie par prise acceptée ; pas seulement étapes/s |
| **5 — Tri** | Reason2 avec grille et références ; exécuter avant upscale lourd | 5090/Spark **en alternance**, pas concurrence mémoire avec génération | Temps de revue gagné sans rejets créatifs excessifs |
| **6 — Plans difficiles** | Transfer2.5, Cosmos DiffusionRenderer, Harmonizer, puis LipSync si accès accordé | Spark pour capacité / 5090 pour profils compatibles | Gain visible sur les catégories visées, identité conservée |
| **7 — R&D** | SANA-Streaming, SANA-WM, 3DGRUT/Omniverse ; SoL-Refiner après clarification des poids | Créneaux réservés | Justifier l’intégration avant d’en faire une dépendance client |

Pour chaque essai, séparer **premier lancement** (téléchargement, compilation, warmup) et **régime chaud**, puis mesurer médiane et cas lents sur plusieurs prises. Ne pas multiplier les accélérations annoncées de Sol, quantification et TensorRT : ces méthodes se recouvrent souvent. Prévoir chargement/rechargement des modèles, copies et export dans le temps complet.

## 13. Ce qui reste non établi et ce qu’il ne faut pas annoncer

- Aucun test réel n’a été effectué ici sur votre 5090 à 475 W, vos installations ComfyUI ou votre GB10 ; le rapport vérifie **l’existence et la documentation**, pas une compatibilité obtenue en laboratoire Creative.
- « Poids ouverts » ne suffit pas pour la licence commerciale. PiD, UniRelight, Lyra 2 et DiffusionRenderer académique sont des exemples concrets où une recommandation commerciale sans lecture des poids serait trompeuse.
- **Pas de « DiffusionRenderer 2 » public confirmé**, pas de poids SANA-Video 2.0 14B confirmés, pas de paquet opérationnel HorizonRelight/TRON/ByG confirmé sur les pages consultées. Une publication datée n’est pas une disponibilité logicielle.
- Les accès NGC privés n’ont pas été exercés. LipSync est réel mais restreint ; cliquer sa fiche ne donne pas le droit ni la capacité de télécharger son runtime.
- Les bibliothèques Windows ARM pour RTX Spark/N1X ne prouvent pas un conteneur Linux ARM pour DGX Spark/GB10. Les supports Spark explicitement documentés — Sol-H3, plusieurs Cosmos, Speech NIM et NeMo-Speech.cpp — sont distingués des ports hypothétiques.
- La chaîne **Pika H3 Flex** n’a pas été auditée comme artefact de poids distinct. Les résultats H3 de NVIDIA ne prouvent pas l’accélération de votre paquet Flex, de ses adaptateurs ni de son workflow. Il faut conserver son profil réel comme référence séparée.
- Le rapport vise les outils ayant un usage identifiable pour Creative ; il ne prétend pas inventorier toutes les publications NVIDIA. Lorsqu’aucun minimum VRAM ou aucune licence exploitable n’est publié, il le dit au lieu d’inventer une valeur.

## 14. Top 5 — gain attendu sur la qualité perçue

Classement **recommandé pour votre parc et vos problèmes**, fondé sur portée, disponibilité et coût d’intégration ; ce ne sont pas cinq gains mesurés ni additifs.

| Rang | Choix | Gain attendu et réserve | Décision |
|---:|---|---|---|
| **1** | **RTX Video Super Resolution, nœuds officiels ComfyUI** | Finition plus propre sur presque chaque livraison agrandie ; faible changement de pipeline. Préserver grain/textures et contrôler le flicker. Le rendu synthétique de la source peut persister | **Adopter sur 5080**, réglage validé en A/B |
| **2** | **Cosmos Transfer2.5** | Plus fort potentiel de changement d’apparence vers un rendu filmé tout en gardant des contrôles de scène ; risque de dérive d’identité et coût important. Le profil publié dépasse 32 Go | **Tester sur Spark après validation ARM et mémoire** |
| **3** | **Cosmos-Transfer1-DiffusionRenderer**, complété selon plan par **Harmonizer** | Pour vos VFX, une lumière qui atteint visage/décor change davantage la crédibilité qu’un halo plus net. Dépend de géométrie, masques et comportement temporel | **Tester sur plans prioritaires**, comparaison au compositing classique |
| **4** | **LipSync + Magpie français** | Sur avatars parlants, voix stable, mots exacts et bouche synchronisée rendent le plan beaucoup plus convaincant. Accès LipSync restreint ; accent et phonèmes à valider | **Tester Magpie maintenant**, LipSync après accès ; A2F-3D si avatar riggé |
| **5** | **Cosmos Reason2 pour sélectionner les prises** | Améliore la qualité livrée en écartant les mauvais plans et en ciblant les retouches ; ne modifie aucun pixel et exige calibration humaine | **Tester 2B**, puis intégrer si ses erreurs sont acceptables |

**Candidat à fort potentiel, hors classement d’adoption : SoL-Refiner pour H3.** C’est une piste très directement alignée avec votre agrandissement, mais la licence des poids de l’extension H3 n’est pas explicitée dans la fiche consultée. Il ne doit pas entrer en production payante sur la seule licence Apache du code. **SANA-Streaming** mérite également un banc d’essai pour l’édition rapide, avec validation de fidélité avant toute préférence face à Transfer.

## 15. Top 3 — gain attendu sur la vitesse

| Rang | Choix | Pourquoi il passe avant les autres | Décision |
|---:|---|---|---|
| **1** | **Sol Engine / Sol-H3, recettes 5090 et Spark dédiées** | Seule piste étudiée ici publiant des mesures locales directement sur **H3 + vos architectures**. Gros gain potentiel, mais les meilleurs chiffres changent étapes, attention, quantification et parfois raffineur ; commencer par un profil conservateur | **Tester en premier**, comparaison à qualité acceptée égale et à 475 W |
| **2** | **NVENC + séparation génération / finition / audio** | Libérer 5090 et Spark des exports, de l’ASR et des traitements secondaires avec 5080, RTX20, V100 et CPU. Le gain de débit dépend de la part réellement occupée par ces tâches ; aucun facteur universel promis | **Adopter maintenant**, avec mesure de la file et des transferts |
| **3** | **ModelOpt FP8/NVFP4 ciblé, après profilage Nsight** | Réduire les coûts des composants dominants et surtout éviter l’offload si la mémoire devient suffisante. Ne pas quantifier à nouveau un profil Sol qui fait déjà la même chose ; TensorRT/VisualGen seulement quand modèle, backend et architecture sont validés | **Tester après les deux premiers**, garder la référence de qualité et le temps complet |
