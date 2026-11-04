> Annexe du rapport `recherche/24-etat-de-lart-creative-2026-11.md`. Rapport délégué (GPT-6.1 Sol, effort très élevé, Codex avec recherche web, 03/11/2026), conservé tel quel. Contrôle par Claude Opus 5.5 : 79/79 titres arXiv identiques à arxiv.org, 83/85 dépôts GitHub existants (SongBloom 404, une URL mal extraite), quatre affirmations recoupées à la main (voir §12 du rapport 24). Les chiffres non recoupés restent ceux des sources citées.

# Vidéo locale et VFX ouverts pour Nexora Creative

**État vérifié le 3 novembre 2026 — 40 pistes : 15 familles de générateurs, 25 pistes VFX.** H3 est la référence déjà exploitée, hors numérotation. Classement par utilité pour le studio, dans chaque partie. Recherche et lecture seulement : aucune installation, aucun téléchargement de poids, aucun test GPU. Les cinq notes demandées ont été consultées en lecture seule ; elles n'ont pas été modifiées. Aucune analyse juridique.

## Décision principale

**Je ne trouve pas de remplacement local dont la supériorité générale sur MiniMax H3 soit démontrée.** L'investissement utile est de compléter H3 par des moteurs de contrôle et de retouche, capables d'intervenir sur un plan existant. Générer une bataille spectaculaire et conserver exactement le décor, les trajectoires et les personnages sont des problèmes différents.

L'arène publique **AA-Video-T2V v2.1, avec audio**, consultée le **2026-11-03**, donne H3 768p **3e, 1160 ± 14 Elo**, MAGI-2 Preview **15e, 1041 ± 13**, LTX-2.5 Fast **25e, 944 ± 15**, LTX-2.5 Pro **26e, 940 ± 16**. Wan 3.0 est premier à 1172, mais aucun artefact officiel permettant son exécution locale n'a été identifié. Les intervalles sont à 95 %. **Le score du service H3 n'est pas celui de FastH3 V2 NVFP4**, et « MiniMax H3 Max » chez fal n'est pas une mesure de votre recette locale `h3-max`. [Classement Artificial Analysis](https://artificialanalysis.ai/video/leaderboard/text-to-video).

Ces chiffres actualisent la note 03 : ses 1161/947 Elo étaient un autre instantané. Ils ne prouvent pas une régression des modèles. Les services évalués peuvent employer des réécritures, des résolutions et des raffinages différents de ceux des poids publiés.

## Ce que ce rapport ajoute aux notes existantes

| Déjà documenté ou construit | Complément apporté ici |
|---|---|
| H3/FastH3, Qwen-Image/Edit, Music3, TRELLIS.2/Pixal3D | Conservés comme socle ; pas de nouvelle intégration proposée pour les mêmes fonctions. |
| VACE 2.1, contrôles Wan, Uni3C | Priorité à **Wan2.2-Fun-5B-Control / VACE-Fun-A14B**, et à **Wan-Move** pour les trajectoires de régions. |
| Wan-Animate-2 et LiveLight seulement repérés | Dépôts et publications de poids retrouvés ; disponibilité distincte de la qualification sur nos GPU. |
| Wan-Alpha / Alpha++ évoqués en A2 | Distinction vérifiée entre **RGBA normal publié** et **poids Effect RGBA encore annoncés** ; licence du dépôt ++ non vérifiée. |
| DiffuEraser marqué Apache | Dépendance explicite à **ProPainter**, avec sa propre licence, et tableau L20 retrouvés. |
| FlashVSR+ annoncé « 4K sur 4090 » | Débit réel publié : **0,50 image/s Base, 0,98 Turbo** ; outil d'export, pas d'aperçu temps réel. |
| Effets de référence seulement en veille | VFXMaster a maintenant un chemin d'inférence ; **EffectMaker reste un dépôt presque vide**, IC-Effect ne publie pas encore les Effect-LoRA. |
| Catalogue vidéo 03 | Ajout substantiel de **SANA-Video 2.0** et vérification des limites de Helios/Motif ; correction de la date Cosmos3 vers mai 2026. |
| Pas de SoL-Refiner repéré dans les cinq notes | **Raffinement une étape publié**, versions LTX-2.3 et extension H3/LTX-2.5 distinctes ; gain 27× démontré sur deux GB200, pas sur notre parc. |
| SAM 2.1 + ViTMatte déjà construits ; Alpha-Gen pro déjà étudié | Ne pas reconstruire le détourage ni répéter le chantier LTX Alpha-Gen. Les nouveaux actifs RGBA sont un autre besoin. |

Références internes lues : `03-modeles-video-licences-h3.md`, `07-litterature-scientifique.md`, `15-litterature-generation-coherence-long-metrage.md`, partie A2 de `17-modes-creative-et-mode-studio-effets.md`, `22-detourage-video-pro.md`, sous `/home/pc6/Desktop/NexoraCreative-recherche/recherche/`.

## Comment lire les preuves et les machines

- **P** : mesure ou exigence publiée dans une source primaire, non reproduite ici. **A** : annonce sans protocole suffisant. **E** : mon estimation de capacité, jamais une mesure de fonctionnement. **NV / non vérifié** : information non confirmée, y compris une absence de résultat accessible.
- Les paramètres désignent le générateur, sauf précision. Un modèle 14B demande environ **28 Go de poids BF16 seuls [E]** ; il faut ajouter encodeurs, VAE, activations et contrôles. La taille du téléchargement n'est pas le pic de mémoire.
- **« Tient GB10 [E] » signifie capacité mémoire plausible pour des clips courts**, avec compilation ARM64/sm_121 encore non vérifiée. Ce n'est ni une preuve de compatibilité des noyaux ni une promesse de vitesse. La bande passante du Spark interdit de déduire sa vitesse de ses 128 Go.
- **5090** : toute admission par quantification/offload est conditionnelle au chemin indiqué. Aucune mesure publiée relevée n'est qualifiée à votre plafond **475 W** ; ne pas lui attribuer les temps d'une carte sans plafond connu.
- **Turing** signifie **une carte 8 Go**, pas 16 Go disponibles en commun. Répartir deux tâches indépendantes sur les deux cartes est réaliste ; additionner leur VRAM pour un pipeline sans support explicite ne l'est pas. BF16/FP8/NVFP4 et FlashAttention récents ne deviennent pas compatibles parce que les poids sont petits.
- Pour une **durée maximale**, je distingue plafond documenté, exemple et continuation. « Prolongation possible » n'est pas une garantie de cohérence pendant plusieurs minutes.
- Les numéros de version de VBench ne sont pas interchangeables. Son interface publique et ses fichiers de classement n'ont pas livré de tableau exploitable dans cette session. Les scores d'articles ci-dessous restent **des résultats sur un banc public, rapportés par les auteurs** : leur **rang mondial actuel est non vérifié**. [VBench officiel](https://vchitect.github.io/VBench-project/), [arène HF](https://huggingface.co/spaces/Vchitect/VBench_Leaderboard).
- Les licences sont des **étiquettes factuelles à un terme** : `Apache-2.0`, `MIT`, `Community`, `Skywork`, `OpenMDW-1.1`, etc. Code et poids sont séparés quand nécessaire. Les dates de commit sont celles du **committer du dernier commit de la branche par défaut**, relevées via l'API GitHub, pas `updated_at` ni `pushed_at`. Les liens de preuve sont en annexe.

## Partie 1 — Générateurs à poids ouverts : les 15 familles utiles à comparer

### Catalogue, capacités et qualité

**Tous les rangs AA dans ce tableau sont l'instantané du 2026-11-03, avec audio.** Une absence de cette catégorie ne classe pas un générateur muet dernier.

| # | Famille ; date vérifiée | Paramètres ; licence | Audio natif | Résolution et durée locales documentées | Classement public daté et lecture pour Nexora |
|---|---|---|---|---|---|
| **1** | **Wan 2.1 / 2.2** ; 2.1 publié **2025-02-25**, 2.2 **2025-07-28** | 2.1 : 1,3B/14B ; 2.2 : 5B ou A14B à deux experts ; **Apache-2.0** | **Non**. S2V consomme une parole externe. | 480/720p ; TI2V-5B 1280×704 à 24 i/s ; configurations courtes autour de 5 s. Maximum universel : **non vérifié**. | 2.2 : VBench **84,23** avec optimisation de prompt, tableau Motif d'avril-mai 2026 ; rang actuel **non vérifié**. Intérêt : écosystème VFX, pas remplacement de H3. [2.1](https://github.com/Wan-Video/Wan2.1), [2.2](https://github.com/Wan-Video/Wan2.2), [licence](https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt), [5B](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B). |
| **2** | **LTX-2 / 2.3 / 2.5** ; article 2 : **2026-01-06** ; dépôt HF 2.3 créé **2026-03-04**, sortie couramment datée du 5 ; 2.5 : **2026-08-11** | **19B / 22B / 22B** ; **Community** | **Oui** | 2.5 : exemples 1536×1024 et DFR jusqu'à **3840×2176**, avec étapes de détail/agrandissement ; 24 i/s, agrandissement temporel optionnel. Pas de plafond de durée local confirmé ; `8n+1` images n'en définit pas un. | AA : Fast **25e/944**, Pro **26e/940** ; 2.3 Pro **29e/884**. Spécialiste de guides/LoRA et du rendu multi-étages ; égalité avec H3 non démontrée. [2](https://huggingface.co/Lightricks/LTX-2), [2.3](https://huggingface.co/Lightricks/LTX-2.3), [2.5](https://huggingface.co/Lightricks/LTX-2.5), [licence 2.x](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x). |
| **3** | **Kandinsky 5 / 6** ; K5 Lite **2025-09-29**, Pro **2025-11-20** ; K6 code/poids **2026-10-06** | K5 **2B/19B** ; K6 **3B/29B** ; **MIT** | K5 **non** ; K6 **oui**, 44 kHz | K6 : **5 s, 480×864**, 1080p par SR externe au générateur ; première/dernière image et entrées audio/vidéo ajoutées **2026-10-25**. | K6 : rang AA/VBench **non vérifié**. K5 Pro annoncé premier ouvert sur LMArena **2025-12-12**, affirmation du dépôt, pas classement actuel vérifié. Repli AV à tester, pas concurrent prouvé de H3. [K5](https://github.com/kandinskylab/kandinsky-5), [K6 et mesures](https://github.com/kandinskylab/kandinsky-6), [licence](https://github.com/kandinskylab/kandinsky-6/blob/main/LICENSE). |
| **4** | **SANA-Video 2.0 / 4-Step Preview** ; article **2026-07-23** ; poids 50 pas **août**, 4 pas **septembre 2026** d'après les annonces du dépôt ; jours exacts **non vérifiés** | Échelles annoncées **5B/14B** ; checkpoint public « 5B » = **4 466 980 960** paramètres ; **Apache-2.0** pour le générateur | **Non** | 50 pas T2V/TI2V : **1280×736, 193 images, 24 i/s, 8,04 s**. Preview 4 pas **T2V seul**, 81 images/16 i/s (~5 s) ou 193/24 (~8 s). **14B non livré** selon le README ; plafond supérieur non vérifié. VAE LTX-2.3 séparé. | VBench **84,30**, **5B/40 pas/480p**, auteurs, juillet 2026 ; rang public actuel et score du 4-Step **non vérifiés**. [50 pas](https://huggingface.co/Efficient-Large-Model/SANA-Video_2.0_5B_720p), [4 pas](https://huggingface.co/Efficient-Large-Model/SANA-Video_2.0_5B_720p_4step), [projet](https://nvlabs.github.io/Sana/Video2/), [code/licence](https://github.com/NVlabs/Sana). |
| **5** | **HunyuanVideo 1.5** ; code/poids **2025-11-20**, licence datée du **21** | **8,3B** ; **Community** | **Non** ; Foley est un autre modèle | 480p/720p ; SR jusqu'à **1080p** ; article traite notamment 10 s. Maximum local officiellement garanti : **non vérifié**. | Rang AA/VBench actuel **non vérifié** ; ne pas lui attribuer le 83,24 de HunyuanVideo 13B. Alternative compacte, moins utile que les contrôles Wan pour nos VFX. [Dépôt](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5), [fiche](https://huggingface.co/tencent/HunyuanVideo-1.5), [licence](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE). |
| **6** | **Helios** ; code/poids/article **2026-03-04** | **14B**, Base/Mid/Distilled ; **Apache-2.0** | **Non** | Génération par blocs de **33 images** ; séquences de l'ordre de la minute démontrées ; plafond et résolution maximale **non vérifiés**. Ne pas assimiler un tutoriel 4K au modèle natif. | Rang AA/VBench actuel **non vérifié**. Atout : continuation et aperçu ; pas preuve de qualité premium H3. [Code](https://github.com/PKU-YuanGroup/Helios), [licence](https://github.com/PKU-YuanGroup/Helios/blob/main/LICENSE.txt). |
| **7** | **Cosmos 3** ; fiches officielles : **2026-05-31** | Nano **16B**, Super **64B**, Edge annoncé **4B** ; **OpenMDW-1.1** | Nano/Super **oui**, ambiance ; Edge **non** dans la matrice | Nano : jusqu'à **720p**, **5–400 images**, 189 par défaut ; durée dépend de la cadence demandée. Pas une promesse de dialogue H3. | Rang AA/VBench actuel **non vérifié**. Modèle physique/action/raisonnement, intéressant pour contrôle et simulation visuelle. Génération Edge téléchargeable : **non vérifiée**. [Nano](https://huggingface.co/nvidia/Cosmos3-Nano), [Super](https://huggingface.co/nvidia/Cosmos3-Super), [matrice](https://docs.nvidia.com/cosmos/latest/cosmos3/model_matrix.html), [code/licence](https://github.com/NVIDIA/cosmos-framework). |
| **8** | **LongCat-Video**, puis Avatar 1.5 ; **2025-10-25**, **2026-05-21** | Base **13,6B** ; **MIT** | Base **non** ; Avatar **audio fourni**, pas synthèse native du son | Base **720p/30 i/s**, continuation sur plusieurs minutes ; plafond garanti **non vérifié**. Avatar 1.5 distillé à 8 étapes. | Rang public actuel **non vérifié** ; les MOS internes du dépôt ne sont pas une arène indépendante. Complément long format déjà couvert conceptuellement en 15. [Dépôt](https://github.com/meituan-longcat/LongCat-Video), [licence](https://github.com/meituan-longcat/LongCat-Video/blob/main/LICENSE). |
| **9** | **Ovi / Ovi 1.1** ; article **2025-09-30**, 1.1 **2025-11-10** | Checkpoint **11B** ; branche audio annoncée 5B ; **Apache-2.0** pour le code | **Oui** | 1.1 : **960×960**, **10 s**, 24 i/s ; autres ratios et modèles 5 s. Pas de plafond supérieur confirmé. | Rang AA/VBench actuel **non vérifié**. Le README annonce 24 Go en FP8/offload, mais ne démontre pas une qualité égale à H3. [Dépôt](https://github.com/character-ai/Ovi), [licence code](https://github.com/character-ai/Ovi/blob/main/LICENSE). Licence de chaque composant audio téléchargé : **non vérifiée**. |
| **10** | **SkyReels V2 / V3 / V4** ; V2 **2025-04-21**, V3 **2026-01-29**, article V4 **2026-02-25** | V2 1,3B/14B ; V3 R2V/V2V **14B**, avatar **19B** ; **Skywork** ; V4 paramètres/licence **non vérifiés** | V2/V3 **non** en génération audio ; avatar guidé par son. V4 **oui**, dans l'article | V3 : recommandé **720p, 5 s/24 i/s** et extension ; plafond non vérifié. V4 annonce **1080p/32 i/s/15 s**, **poids locaux non vérifiés**. | Rang actuel **non vérifié**. Ne pas présenter V4 comme alternative locale installable. [V3](https://github.com/SkyworkAI/SkyReels-V3), [licence publiée](https://github.com/SkyworkAI/SkyReels-V3/blob/main/LICENSE.txt), [organisation de poids](https://huggingface.co/Skywork). |
| **11** | **MAGI-1 / 1.1 / MAGI-2 Preview** ; **2025-04-21**, **2026-06-17**, publication Preview en **août 2026** | 1 : **4,5B/24B** ; 2 : **114B stockés / 6B actifs par jeton** ; **Apache-2.0** | 1 **non** ; 2 **oui** | 1 : blocs de 24 images, exemple 720×720 pour 4,5B, continuation ; max non vérifié. 2 : **10 s uniquement**, **1080p par raffineur**. | 2 : AA **15e, 1041** ; 1 : rang actuel non vérifié. Le faible nombre de paramètres actifs de MAGI-2 ne réduit pas les poids à charger à 6B. [1](https://github.com/SandAI-org/MAGI-1), [2](https://huggingface.co/sand-ai/MAGI-2-preview), [code 2](https://github.com/SandAI-org/MAGI-2-preview). |
| **12** | **Motif-Video 2B** ; **2026-04-14** | **2B** ; poids **Apache-2.0** ; licence du nœud ComfyUI **non vérifiée** | **Non** | Configuration recommandée **1280×736, 121 images, 24 i/s**, soit ~5 s ; maximum non vérifié. | VBench **83,76**, article avril/révision mai 2026 ; rang actuel non vérifié. Les auteurs signalent eux-mêmes un écart perceptuel en faveur de Wan 14B. [Fiche](https://huggingface.co/Motif-Technologies/Motif-Video-2B), [nœud](https://github.com/MotifTechnologies/ComfyUI-MotifVideo2B). |
| **13** | **Step-Video-T2V / Turbo / TI2V** ; code/poids **2025-02-17**, TI2V **2025-03-17** | **30B** ; **MIT** | **Non** | Jusqu'à **204 images** ; profils **768×768** ou **992×544** ; durée en secondes dépend de l'export. Maximum temporel vérifié : 204 images. | VBench **81,83** dans le tableau Motif avril-mai 2026 ; rang mondial actuel non vérifié. Pas de gain établi pour notre studio. [Dépôt](https://github.com/stepfun-ai/Step-Video-T2V), [licence](https://github.com/stepfun-ai/Step-Video-T2V/blob/main/LICENSE). |
| **14** | **Mochi 1 Preview** ; **2024-10-22**, témoin ancien demandé | **10B** ; **Apache-2.0** | **Non** | **480p** ; exemple officiel 84 images à 30 i/s, soit 2,8 s. Durée maximale : **non vérifiée**. | Rang actuel **non vérifié**. Aucun nouveau Mochi 2025–2026 vérifié ; un commit récent ne constitue pas une nouvelle génération de poids. [Fiche](https://huggingface.co/genmo/mochi-1-preview), [dépôt](https://github.com/genmoai/mochi), [annonce datée](https://www.genmo.ai/blog). |
| **15** | **Waver 1.0** ; article **2025-08-21** | **12B** ; licence et poids **non vérifiés** ; dépôt = README + actifs de démonstration | **Non** dans les capacités publiées | Article : **720p natif, 5–10 s**, puis 1080p par SR. Ce n'est pas une capacité locale disponible vérifiée. | **Top 3 T2V/I2V revendiqué par les auteurs au 2025-07-30** ; README cite aussi le 5 août. Rang actuel non vérifié ; ne pas extrapoler ce résultat historique à H3. [Dépôt ouvert](https://github.com/FoundationVision/Waver). |

**Wan 2.5/2.6/2.7/3.x :** pas de poids officiels identifiés au-delà des familles 2.2 et de leurs dérivés dans les sources consultées. Ce sont des entrées de service, pas une mise à niveau locale établie. Pour Wan 3.0, nombre de paramètres, mémoire locale, licence de poids et vitesse locale : **non vérifiés**. [Organisation officielle Wan-AI](https://huggingface.co/Wan-AI).

**Vérification de périmètre FLUX 3 :** les poids publics [FLUX 3 Action 7B](https://huggingface.co/black-forest-labs/flux-3-action-base) servent à la prédiction d'actions et d'images futures pour robotique/jeux ; leur existence ne publie pas le générateur vidéo **FLUX 3 Max** évalué dans l'arène. Cette politique d'action est exclue du catalogue des générateurs de studio. [Présentation primaire](https://bfl.ai/models/flux-3-action).

### Mémoire et vitesse : ce qu'on peut effectivement promettre

Dans la colonne matériel, **G = GB10**, **R = RTX 5090**, **T = une Turing 8 Go**. `Oui [E]` reste une estimation de capacité ; `NV` n'est pas un échec mesuré. Les exigences sans temps publié ne sont pas transformées en benchmark.

| # | Mémoire et chemin d'exécution | Vitesse publiée sur machine proche ; sinon limite de preuve | Verdict G / R / T et choix |
|---|---|---|---|
| **1 Wan** | **P** : 5B 720p sur **24 Go** avec T5 CPU/offload ; A14B commande officielle à **≥80 Go**. Ancien 2.1-1,3B : **8,19 Go** publiés. Quantification/offload requis pour A14B sur 32 Go. | [README officiel 2.1](https://github.com/Wan-Video/Wan2.1) : **~4 min pour 5 s/480p sur 4090**, sans quantification, avec offload/T5 CPU. Mesure proche 2.2 : **non vérifiée ici**. Les temps TurboDiffusion de 07 ne se transfèrent pas aux contrôleurs VFX. | **G oui [E]**, clips courts ; **R oui 5B [P→E], A14B conditionnel** ; **T pas de configuration qualifiée**, 2.1-1,3B réduit à tester seulement, 8,19 Go dépassant déjà les 8 Go. **Adopter le socle spécialisé.** |
| **2 LTX** | 2.5 : DiT BF16 ≈44 Go de poids seuls [E], encodeur Gemma4-12B séparé ; NVFP4/INT8 et offload sur 32 Go. Les activations DFR augmentent la mémoire. | Mesure E2E complète 2.5 sur nos classes de GPU : **non vérifiée** dans les sources primaires retenues. Ne pas recycler les temps de LTX-Video 2B ou d'un raffineur H3+LTX. | **G oui [E]** avec marge à contrôler ; **R conditionnel [E]** ; **T non qualifié**. **Tester comme spécialiste** ; accès HF 2.5 protégé, déjà relevé en 22. |
| **3 Kandinsky** | **P** : K6 Lite résident sur **5090 32 Go** ; Pro en **block offload** sur 5090/4090 ; profils aussi publiés sur 5060 Ti 16 Go. | **5090**, 480×864/5 s/audio, 10 étapes : **Lite 44,2 s ; Pro 174,5 s** ; avec SR Full HD **140,3 / 269,5 s**. **Exclut chargement et encodage MP4**, un échantillon après chauffe. [Table primaire](https://github.com/kandinskylab/kandinsky-6#performance). | **G oui mémoire [E], noyaux NV** ; **R oui [P]** ; **T aucune preuve à 8 Go**. **Tester K6 Lite Distill comme repli AV** ; K5 moins prioritaire. |
| **4 SANA** | **E** : 4,47B BF16 ≈8,94 Go de DiT seuls, puis Gemma2-2B, VAE et activations. Pic public complet sur 32 Go : **non vérifié**. Le 4-Step garde les mêmes poids de grande taille. | **Pas de mesure proche vérifiée.** Référence distincte **H100** : 5B+Sol-Engine **13,06 s pour 720p/5 s**, protocole distinct des sorties HF 50 pas et 4-Step. Ne pas lui attribuer automatiquement ce débit. | **G oui [E]** ; **R probable avec gestion mémoire [E]** ; **T non établi**. **Tester 4-Step pour le brouillon T2V** ; choisir le 50 pas si une image initiale est nécessaire. |
| **5 Hunyuan 1.5** | **P** : minimum annoncé **14 Go avec offload** ; BF16 par défaut, encodeurs séparés. | **RTX 4090** : annonce officielle **≤75 s** en **480p I2V distillé 8/12 pas** (2025-12-05), sans protocole E2E détaillé. Ce n'est pas 720p/1080p à ce temps. | **G oui [E]** ; **R oui par capacité [E]** ; **T non au plancher publié**. **Surveiller**, pas d'avantage VFX décisif établi. |
| **6 Helios** | **P/A** : recette group-offload annoncée à **~6 Go VRAM**. Les poids 14B et la RAM hôte demeurent nécessaires. | **Sur GPU proche : non vérifié**. **H100 : 19,5 i/s**, à ne pas transférer au Spark ni au mode 6 Go. | **G oui [E]** ; **R oui avec offload [E]** ; **T capacité 6 Go plausible, compatibilité/FP16/vitesse NV**. **Tester seulement pour aperçu/continuation**. |
| **7 Cosmos3** | Nano16B : **~32 Go de poids BF16 seuls [E]** ; Super64B : **~128 Go de poids seuls [E]**, donc aucune marge dans un Spark 128 Go. La FAQ du framework affiche encore 8B/32B, en conflit avec fiches et matrice actuelles : ne pas utiliser ce raccourci. | Mesure vidéo comparable sur 5090/GB10 : **non vérifiée**. La fiche ne qualifie officiellement que BF16 ; documentation d'installation **aarch64** et GPU Ampere ou plus récent. [Quickstart](https://nvidia.github.io/cosmos-framework/get_started/quickstart/). | Nano : **G plausible [E]**, **R pas résident en BF16**, quantification/offload NV ; **T hors support annoncé**. Super : **non résident** sur nos machines en BF16. **Surveiller Nano**, pas moteur principal. |
| **8 LongCat** | Base13,6B ≈27,2 Go de poids seuls [E], donc offload/quantification pour marge sur 5090. Avatar officiel souvent multi-GPU. | Base : **non vérifié** sur machine proche. PR communautaire **non fusionnée #115**, Avatar1.5/4090 : ~2 min pour un segment 3,7 s, ~70 min pour 12 s ; réglages différents, pas débit constant. [PR et protocole](https://github.com/meituan-longcat/LongCat-Video/pull/115). | **G plausible [E]** ; **R conditionnel [E]** ; **T non qualifié**. **Surveiller** ; ne pas entreprendre une troisième pile de film long maintenant. |
| **9 Ovi** | **P** : ~80 Go sans optimisation ; **32 Go offload**, **24 Go FP8/offload** selon README. FP8 stocké mais calcul BF16 dans ce chemin. | Tableau **83–118 s**, 121 images/720×720/50 pas, mais **GPU non identifié** dans le tableau : mesure proche **non vérifiée**. | **G oui mémoire [E]**, **R conditionnel 24 Go [P→E]**, **T non** au plancher documenté. **Surveiller**, derrière K6 Lite pour un repli AV. |
| **10 SkyReels** | V2 **P** : 540p 1,3B ~14,7 Go, 14B ~51,2 Go ; ce ne sont pas des mesures V3. V3 offload disponible, pic **non vérifié**. | V3/V4 sur GB10/5090 : **non vérifié**. | V3 **G plausible [E]**, **R conditionnel [E]**, **T non qualifié** ; V4 **NV partout sans poids**. **Surveiller**. |
| **11 MAGI** | **P** : 1-4,5B recommandé **24 Go**, variante quantifiée/window=1 **12 Go** ; 24B recommandé multi-GPU. MAGI-2 exige **8 Hopper**, dépôt de poids ~307 Go. | 1/2 sur machine proche avec protocole : **non vérifié**. Les 6B actifs de 2 ne justifient aucun chiffre de vitesse sur 5090. | MAGI1-4,5B : **G/R oui par capacité [E]**, **T sous le plancher publié** ; MAGI2 : **non sur G/R/T dans le chemin publié**. **Écarter de la priorité locale**. |
| **12 Motif** | **P** : 4090 720p/121 images, Q4_K_M **12,16 Go alloués**, ~16 Go réservés avec Sage ; BF16 **14,73 Go alloués** dans ce protocole. | **4090 : 1502 s E2E**, Q4_K_M+Sage, **50 pas**, 1280×736/121 images ; BF16+Sage 1492 s. Le 14,59 s/it souvent cité vient du **H200**, pas de la 4090. [Mesure primaire](https://huggingface.co/Motif-Technologies/Motif-Video-2B/blob/main/docs/gguf-sageattention.md). | **G/R oui par capacité [E]**, **T non au profil mesuré**. **Écarter comme accélérateur de H3**. Petit nombre de paramètres ≠ aperçu rapide. |
| **13 Step** | **P** : **72,48–78,55 Go**, profils 136/204 images ; services encodeur/VAE séparés. Attention encodeur ne liste que sm_80/86/90. | Tableau 50 pas : **743 s** en 992×544×204, **860 s** en 768²×204 ; contexte **4 GPU** et carte non précisée. Ce n'est pas une mesure monocarte proche des nôtres. | **G capacité possible mais stack sm_121 NV** ; **R non dans le profil publié** ; **T non**. **Écarter**. |
| **14 Mochi** | **P** : ~60 Go chemin original ; exemple Diffusers BF16/offload/tiling **22 Go**, autre chemin 42 Go. | Vitesse sur machine proche : **non vérifiée**. | **G/R oui par capacité sur chemin 22 Go [E]**, **T non qualifié**. **Écarter** comme nouveau moteur 2026. |
| **15 Waver** | Exigence mémoire locale **non vérifiée**, poids non identifiés ; pas de calcul de VRAM présenté comme capacité installable. | **Non vérifié**. | **G/R/T non vérifiés** faute d'artefact. **Écarter du catalogue local disponible**, surveiller une vraie publication. |

**Précision Kandinsky6 :** les fiches des [poids Lite Distill](https://huggingface.co/kandinskylab/Kandinsky-6.0-Lite-distill-5s-Diffusers) et [Pro Distill](https://huggingface.co/kandinskylab/Kandinsky-6.0-Pro-distill-5s-Diffusers) affichent **MIT**. Le [quickstart natif](https://github.com/kandinskylab/kandinsky-6/blob/main/docs/quickstart/quick_start.md) liste explicitement les capacités **12.0/12.1**, PyTorch CUDA13 et SageAttention2.2 ; cela ne constitue pas un test ARM64 sur notre Spark.

### Articles de la partie 1 effectivement ouverts

Les titres ci-dessous sont recopiés des pages arXiv, et les dates sont celles de première soumission, distinctes des sorties de poids.

| Famille | Identifiant, titre exact et date |
|---|---|
| LTX | [2601.03233 — LTX-2: Efficient Joint Audio-Visual Foundation Model](https://arxiv.org/abs/2601.03233), **2026-01-06**. |
| Hunyuan | [2511.18870 — HunyuanVideo 1.5 Technical Report](https://arxiv.org/abs/2511.18870), **2025-11-24**. |
| Kandinsky6 | [2610.05608 — Kandinsky 6.0 Video: Foundation Models for Synchronized Video and Audio Generation](https://arxiv.org/abs/2610.05608), **2026-10-04**. |
| SANA2 | [2607.21553 — SANA-Video 2.0: Hybrid Linear Attention with Attention Residuals for Efficient Video Generation](https://arxiv.org/abs/2607.21553), **2026-07-23**. |
| Helios | [2603.04379 — Helios: Real Real-Time Long Video Generation Model](https://arxiv.org/abs/2603.04379), **2026-03-04**. |
| Motif | [2604.16503 — Motif-Video 2B: Technical Report](https://arxiv.org/abs/2604.16503), **2026-04-14**, révision **2026-05-19**. |
| LongCat | [2510.22200 — LongCat-Video Technical Report](https://arxiv.org/abs/2510.22200), **2025-10-25**. |
| Ovi | [2510.01284 — Ovi: Twin Backbone Cross-Modal Fusion for Audio-Video Generation](https://arxiv.org/abs/2510.01284), **2025-09-30**. |
| MAGI1 | [2505.13211 — MAGI-1: Autoregressive Video Generation at Scale](https://arxiv.org/abs/2505.13211), **2025-05-19**. |
| Step | [2502.10248 — Step-Video-T2V Technical Report: The Practice, Challenges, and Future of Video Foundation Model](https://arxiv.org/abs/2502.10248), **2025-02-14**. |
| Waver | [2508.15761 — Waver: Wave Your Way to Lifelike Video Generation](https://arxiv.org/abs/2508.15761), **2025-08-21**. |
| SkyReels4 | [2602.21818 — SkyReels-V4: Multi-modal Video-Audio Generation, Inpainting and Editing model](https://arxiv.org/abs/2602.21818), **2026-02-25**, révision **2026-03-18**. |

## Partie 2 — Les 25 pistes VFX, classées par utilité pour le studio

**Maturité** : `recherche` = résultat expérimental ou chaîne incomplète ; `démo` = inférence et actifs utilisables publiés, sans qualification Nexora ; `prod` = chaîne déjà qualifiée dans le studio. Aucun nouveau modèle ci-dessous n'a été testé par nous : aucun n'est étiqueté prod. **Adopter** signifie retenir la brique dans la feuille de route, avec qualification avant activation publique ; **tester** signifie banc borné ; **surveiller** signifie qu'il manque un artefact ou une preuve décisive ; **écarter** signifie ne pas retenir cette piste pour le produit standard actuel.

### 16 — Wan-Move : dessiner où passe le dragon, le vaisseau ou le projectile

**Article ouvert :** [2512.08765 — Wan-Move: Motion-controllable Video Generation via Latent Trajectory Guidance](https://arxiv.org/abs/2512.08765), **2025-12-09**.

**Dépôt :** [ali-vilab/Wan-Move](https://github.com/ali-vilab/Wan-Move). **Licence code : Apache-2.0**, [texte lu](https://github.com/ali-vilab/Wan-Move/blob/main/LICENSE.txt) ; [poids officiels](https://huggingface.co/Ruihang/Wan-Move-14B-480P) étiquetés Apache-2.0. **Dernier commit : 2026-01-05**.

**Apport :** trajectoires denses de points, propagées dans les conditions latentes de la première image ; contrôle régional plus précis qu'un prompt. Poids publiés le 10 décembre 2025, **5 s/480p**, interface de contrôle et intégration ComfyUI référencée. Nouveauté utile absente des cinq notes : contrôler le trajet d'un objet plutôt que demander simplement « vole à gauche ».

**Matériel :** exigence publiée **40 Go** en BF16 avec T5 CPU/offload. **GB10 : tient en mémoire [E], ARM/sm_121 NV** ; **5090 : seulement avec quantification/offload supplémentaire [E], pas dans le profil 40 Go publié** ; **Turing : écarter ce profil**. Temps sur nos classes de GPU : **non vérifié**.

**Maturité : démo. Verdict : tester**, prioritaire pour les scènes d'action. La trajectoire n'assure pas à elle seule les collisions, les ombres ou la conservation de l'identité.

### 17 — Wan2.2-Fun-Control / VACE-Fun : la passerelle 3D, profondeur, pose et fond

**Article de fondation ouvert :** [2503.07598 — VACE: All-in-One Video Creation and Editing](https://arxiv.org/abs/2503.07598), **2025-03-10**. Article spécifique de chaque poids Fun 2.2 : **non vérifié** ; ne pas présenter ce papier comme leur rapport technique.

**Dépôt :** [aigc-apps/VideoX-Fun](https://github.com/aigc-apps/VideoX-Fun). **Licence code : Apache-2.0**, [texte lu](https://github.com/aigc-apps/VideoX-Fun/blob/main/LICENSE). **Dernier commit : 2026-10-28**. Poids [5B-Control](https://huggingface.co/alibaba-pai/Wan2.2-Fun-5B-Control) et [VACE-Fun-A14B](https://huggingface.co/alibaba-pai/Wan2.2-VACE-Fun-A14B) : **Apache-2.0** sur les fiches ouvertes.

**Apport :** Canny, profondeur, pose, MLSD et trajectoires ; variantes caméra ; VACE-Fun ajoute références de sujet et édition guidée. Le gain sur les anciennes notes est **le choix de poids 2.2 précis**, dont un 5B, plutôt que refaire la présentation de VACE 2.1. Entrée naturelle : prévisualisation 3D de TRELLIS/Pixal3D ou animation simplifiée, puis rendu contrôlé. Pour le fond, réutiliser le masque SAM existant.

**Matériel :** 5B : **GB10/5090 plausibles [E]**, avec offload selon longueur ; A14B : **GB10 plausible [E], 5090 quantifiée/offload [E]**. Le « 64,0 GB » de la fiche est une taille d'artefacts, **pas un pic mesuré**. **Turing : uniquement variante 1,3B/FP16 fortement réduite à qualifier**, aucune preuve pour le profil 2.2-HD. Vitesse proche : **non vérifiée**.

**Maturité : démo. Verdict : adopter** comme première famille de contrôle et comme candidat principal à qualifier pour inpainting/remplacement de fond.

### 18 — Wan-Alpha v2 / Wan-Alpha++ : vrais actifs RGBA

**Articles ouverts :** [2509.24979 — Video Generation with Stable Transparency via Shiftable RGB-A Distribution Learner](https://arxiv.org/abs/2509.24979), **2025-09-29**, révision **2025-12-16** ; [2610.26189 — Wan-Alpha++: Animating a Single RGBA Asset into Controllable Transparent Video Effects](https://arxiv.org/abs/2610.26189), **2026-10-19**.

**Dépôts :** [Wan-Alpha](https://github.com/WeChatCV/Wan-Alpha), **MIT**, [licence lue](https://github.com/WeChatCV/Wan-Alpha/blob/main/LICENSE), dernier commit **2026-10-20** ; [Wan-Alpha_PlusPlus](https://github.com/WeChatCV/Wan-Alpha_PlusPlus), **licence propre non vérifiée**, aucun LICENSE à la racine consultée, dernier commit **2026-10-25**. Poids [v2](https://huggingface.co/htdong/Wan-Alpha-v2.0) et [I2V ++](https://huggingface.co/htdong/Wan-Alpha-I2V) : **Apache-2.0** affiché.

**Apport :** v2 génère RGB+alpha, y compris transparence fine ; ++ conditionne sur un actif RGBA et étudie son apparition/disparition. **Publication partielle : poids RGBA normaux disponibles ; “Effect RGBA” encore non cochés.** Une image de dragon animée avec alpha et une explosion apparaissant puis disparaissant ne sont donc pas deux fonctions également livrées.

**Matériel :** v2 base Wan14B ; ++ base Wan2.2-A14B, exemple **832×480×49** lancé sur 8 GPU. **GB10 plausible [E]**, exécution monocarte à qualifier ; **5090 quantifiée/offload [E]**, compatibilité des LoRA à vérifier ; **Turing non qualifiée**. Pic et vitesse GB10/5090 : **non vérifiés**.

**Maturité : démo partielle. Verdict : tester v2 pour une bibliothèque d'actifs ; surveiller ++ pour les effets transitoires.** Complète le détourage de 22, sans le remplacer.

### 19 — Wan-Animate-2 : transférer un geste ou un duel

**Article ouvert :** [2608.06009 — Wan-Animate-2: Pushing the Application Boundaries of Character Animation](https://arxiv.org/abs/2608.06009), **2026-08-06**, révision **2026-08-08**.

**Dépôt :** [Wan-Video/Wan-Animate-2](https://github.com/Wan-Video/Wan-Animate-2). **Apache-2.0**, [licence lue](https://github.com/Wan-Video/Wan-Animate-2/blob/main/LICENSE). **Dernier commit : 2026-08-08**. [Poids Base/Distillation](https://huggingface.co/Wan-AI/Wan2.2-Animate-2-14B) publiés **2026-08-07**, licence affichée **Apache-2.0**.

**Apport :** utilise directement la vidéo motrice, supprime les extracteurs de pose intermédiaires, ajoute un point de vue piloté par texte. Adapté aux gestes d'un acteur transformé en personnage fantastique. **Correction de 07 : des scripts et poids existent.** La variante Lite temps réel est décrite dans l'article ; sa publication autonome et son débit local restent **non vérifiés**.

**Matériel :** réglages officiels **8×A800 à 720p**, essais **2×A800 à 480p**. **GB10 mémoire plausible [E] mais chemin monocarte NV** ; **5090 non vérifié**, quantification/offload à établir ; **Turing non qualifiée**. Ne pas promettre les deux combattants et leurs contacts avec une seule animation humaine.

**Maturité : démo. Verdict : tester**, en gardant Wan-Animate actuel comme témoin, sans réinstaller les deux piles en parallèle avant comparaison.

### 20 — LiveLight : lumière mobile d'explosion ou de sabre

**Article ouvert :** [2608.01771 — LiveLight: Real-time Streaming Video Relighting with Interactive Control](https://arxiv.org/abs/2608.01771), **2026-08-03**.

**Dépôt :** [mayuelala/LiveLight](https://github.com/mayuelala/LiveLight). **MIT**, [licence lue](https://github.com/mayuelala/LiveLight/blob/main/LICENSE). **Dernier commit : 2026-08-04**. README : code et poids ModelScope annoncés publiés **2026-07-27** ; accès effectif et licence séparée des poids **non vérifiés** dans cette session.

**Apport :** déplacer une lumière ponctuelle 3D, régler couleur et intensité, avec cohérence temporelle et traitement en flux. C'est un bon candidat pour faire réagir un visage ou une armure à une lumière rouge/bleue. **15,78 i/s, latence 0,253 s, 4 étapes** publiés ; GPU correspondant et pic mémoire **non vérifiés**, donc aucune promesse de temps réel sur notre parc.

**Matériel :** base SD Image Variations, deux UNet et module temporel ; **GB10/5090 plausibles [E]**, portage de dépendances nécessaire ; **Turing 8 Go non vérifiée**, fenêtre courte/FP16 à examiner. Les anciens environnements PyTorch ne sont pas un profil Blackwell/ARM prêt à l'emploi.

**Maturité : démo. Verdict : tester**, premier choix de banc pour une lumière interactive. Ne garantit ni matériau exact ni conservation parfaite de tous les pixels.

### 21 — Relit-LiVE : accorder l'éclairage d'un plan composite

**Article ouvert :** [2605.06658 — Relit-LiVE: Relight Video by Jointly Learning Environment Video](https://arxiv.org/abs/2605.06658), **2026-05-07**.

**Dépôt :** [zhuxing0/Relit-LiVE](https://github.com/zhuxing0/Relit-LiVE). **Apache-2.0**, [licence lue](https://github.com/zhuxing0/Relit-LiVE/blob/main/LICENSE). **Dernier commit : 2026-06-07**.

**Apport :** génère ensemble vidéo rééclairée et cartes d'environnement par image ; réintroduit le RGB de référence pour réduire les pertes de décomposition. Intérêt : mieux intégrer un objet dans une scène avec caméra mobile, ombres et reflets plausibles. Poids/inférence publiés ; formats vidéo **832×480, 25 ou 57 images**. Le modèle **1472×1024 est une variante image à une trame**, pas une preuve de vidéo HD.

**Matériel :** README recommande **≥24 Go**, base Wan1,3B. **5090 tient par capacité [E]**, **GB10 tient mémoire [E], ARM NV**, **Turing sous la recommandation**. La chaîne complète inverse→rendu dépend aussi de DiffusionRenderer/Cosmos7B ; le minimum 24 Go ne qualifie pas automatiquement tous ces étages. Temps proche : **non vérifié**.

**Maturité : démo. Verdict : tester**, comparaison hors ligne avec LiveLight ; plus directement documenté en mémoire, moins interactif.

### 22 — FlashVSR+ : exporter les effets en 1080p/4K

**Article ouvert :** [2610.17552 — FlashVSR+: Efficient Video Super-Resolution via Hybrid Attention and Reward-Yield Distribution Matching](https://arxiv.org/abs/2610.17552), **2026-10-13**.

**Dépôt :** [OpenImagingLab/FlashVSR_Plus](https://github.com/OpenImagingLab/FlashVSR_Plus). **Apache-2.0**, [licence lue](https://github.com/OpenImagingLab/FlashVSR_Plus/blob/main/LICENSE) ; [poids](https://huggingface.co/ruchangyao/FlashVSR_plus) **Apache-2.0**. **Dernier commit : 2026-10-16**.

**Apport :** étudiant **1,3B**, restauration une étape ; réduit l'attention sans perdre tout le contexte global. Complément à H3 768p et aux contrôleurs 480p. **Nouveau par rapport à 07 : lecture des chiffres et du chemin grand public**, pas seulement de l'annonce 4K.

**Matériel/mesures :** [projet officiel](https://www.flashvsr.tech/) : **RTX4090 24 Go, 4K sans tuilage spatial**, **0,50 i/s Base / 0,98 Turbo**, E2E sur vidéos de 89 images. Les **26,33 Go de pic** du tableau H200 Turbo sont un autre chemin d'exécution. **5090 tient par capacité [E]**, **GB10 plausible [E], Triton/sm_121 NV**, **Turing pas de profil 4K qualifié**. Temps 5090 à 475 W : **non vérifié**.

**Maturité : démo. Verdict : adopter pour la file d'export**, après banc qualité contre SeedVR2 déjà envisagé. L'upscale peut inventer des détails : vérifier visages, armes fines, inscriptions et grain.

### 23 — SoL-Refiner : raffiner les sorties H3/LTX en une seule étape

**Article ouvert :** [2609.37969 — SoL-Refiner: Speed-of-Light One-Step Refinement for High-Resolution Video](https://arxiv.org/abs/2609.37969), **2026-09-29**.

**Dépôt :** [NVlabs/Sana, branche sol-engine, models/sol-refiner](https://github.com/NVlabs/Sana/tree/sol-engine/models/sol-refiner). **Licence propre de cette branche : non vérifiée** : aucun LICENSE trouvé à sa racine ; ne pas transférer automatiquement l'Apache-2.0 lu sur la branche principale. **Dernier commit de sol-engine : 2026-10-30**, [781e834](https://github.com/NVlabs/Sana/commit/781e8341fb3b29d3aea5d50265772e9619340b66). Poids [LTX-2.3 One-Step](https://huggingface.co/Efficient-Large-Model/SoL-Refiner-LTX-2.3-One-Step) et [extension H3/LTX-2.5](https://huggingface.co/Efficient-Large-Model/SoL-Refiner-LTX-2.5-for-MiniMax-H3) publiés ; **licence spécifique non vérifiée**, fiches sans model card.

**Apport :** produire un brouillon moins coûteux puis restaurer la résolution en un passage du raffineur. **L'article étudie LTX-2.3 ; la version H3/LTX-2.5 est une extension ultérieure.** Le code H3 ouvert sort **1920×1080**, depuis un canevas interne 1088 recadré, garde `8k+1` images et **ne conserve pas l'audio** : remux nécessaire. Le 4K du papier ne qualifie pas ce chemin H3 par défaut.

**Matériel/mesures :** [projet primaire](https://nvlabs.github.io/Sana/Sol-Refiner/) : **5,64 s** pour 5 s/1344×768, **un GB200 par étage**, contre 152,3 s H3 pleine résolution sur un GPU ; ce **27,03× ne mesure pas FastH3 V2 sur Spark**. README H3 testé **H100 80 Go**, CPU-offload et VAE tuilé. Poids HF ~19B : **GB10 plausible [E]**, **5090 offload nécessaire [E], pic/temps non vérifiés**, **Turing non qualifiée**. NATTEN/sm_121/ARM64 à vérifier.

**Maturité : démo. Verdict : tester en second pour le raffinement H3**, après documentation de la licence spécifique ; comparer au rendu H3 actuel et à FlashVSR+, sans additionner leurs gains annoncés.

### 24 — DiffuEraser : retirer un objet, avec une dépendance à traiter

**Article ouvert :** [2501.10018 — DiffuEraser: A Diffusion Model for Video Inpainting](https://arxiv.org/abs/2501.10018), **2025-01-17**.

**Dépôt :** [lixiaowen-xw/DiffuEraser](https://github.com/lixiaowen-xw/DiffuEraser). **Apache-2.0**, [licence lue](https://github.com/lixiaowen-xw/DiffuEraser/blob/main/LICENSE). **Dernier commit : 2025-04-17**. **Le README exige aussi ProPainter comme modèle préalable**, remplaçable selon ses auteurs ; [licence de cette dépendance lue : S-Lab](https://github.com/sczhou/ProPainter/blob/main/LICENSE), non commerciale.

**Apport :** retirer perche, câble ou passant et compléter un fond masqué. Le modèle génère plus que la simple propagation de pixels ; il peut aussi halluciner le fond caché. Ne pas le réintroduire comme « tout Apache » sur la seule base de la note 17.

**Matériel :** tableau du README, qualifié d'estimation par les auteurs, **L20**, **250 images/~10 s** : **360p 12 Go/92 s ; 540p 20 Go/175 s ; 720p 33 Go/314 s**. **GB10 plausible [E]**, **5090 540p plausible [E], 720p dépasse 32 Go annoncé** ; **Turing sous le minimum publié**. Vitesse sur nos cartes **non vérifiée**.

**Maturité : démo. Verdict : tester**, avec inventaire des dépendances et comparaison à VACE-Fun ; aucune adoption directe du pipeline complet n'est recommandée ici.

### 25 — Qwen-Video-Edit : une retouche par instruction qui réutilise notre famille image

**Article ouvert :** [2608.14790 — Instruction-Based Video Editing by Repurposing an Image Editing Model](https://arxiv.org/abs/2608.14790), **2026-08-14**, révision **2026-08-21**. Le titre arXiv ne commence pas par « Qwen-Video-Edit ».

**Dépôt :** [yunpeng1998/Qwen-Video-Edit](https://github.com/yunpeng1998/Qwen-Video-Edit). **Licence propre du code : non vérifiée** ; README renvoie aux licences amont dans `licenses/`, aucun LICENSE général à la racine. [Poids](https://huggingface.co/yunpeng1998/Qwen-Video-Edit) affichés **MIT**. **Dernier commit : 2026-09-01**.

**Apport :** planches de latents vidéo Wan traitées par Qwen-Image-Edit, avec projections apprises ; retouche locale/globale et variante sim2real. **Poids publiés**, contrairement à l'incertitude de 07. Configurations : 360p/45 images ; 480p/81 images ; 720p/45 images. Ce n'est pas une fonction obtenue gratuitement en lançant notre Qwen-Image-Edit actuel sur chaque image.

**Matériel :** README **~55 Go de pile édition**, puis expert Wan **~28 Go** en séquence ; mode de parking par défaut demande **~100 Go de RAM hôte**. **GB10 candidat prioritaire [E]**, en évitant les duplications CPU/GPU en mémoire unifiée ; **5090 non vérifiée dans le chemin stock**, quantification nécessaire ; **Turing écarter**. Vitesse proche : **non vérifiée**.

**Maturité : démo. Verdict : tester sur GB10**, seulement après clarification factuelle de la licence du code propre et du budget mémoire ; potentiel fort pour « change ce décor/costume ».

### 26 — UniVideo : édition et références dans une même interface

**Article ouvert :** [2510.08377 — UniVideo: Unified Understanding, Generation, and Editing for Videos](https://arxiv.org/abs/2510.08377), **2025-10-09**, révision **2026-07-03**.

**Dépôt :** [KlingAIResearch/UniVideo](https://github.com/KlingAIResearch/UniVideo), anciennement KlingTeam. **Licence code : MIT**, [texte lu](https://github.com/KlingAIResearch/UniVideo/blob/main/LICENSE.txt). **Dernier commit : 2026-07-03**. Code et [poids UniVideo](https://huggingface.co/KlingTeam/UniVideo) annoncés publiés **2026-01-07** ; licence complète de la pile de poids, dont la base HunyuanVideo : **non vérifiée**.
La fiche des poids propres affiche **Apache-2.0** ; cette étiquette ne documente pas à elle seule toutes les dépendances.

**Apport :** combiner instruction, références visuelles et vidéo pour ajouter, supprimer ou transformer du contenu ; compréhension Qwen2.5-VL et générateur HunyuanVideo. C'est un candidat à l'interface « modifie cet élément » plus général que les LoRA par effet. **Nouveau par rapport à 07 : il existe un chemin d'inférence**, pas seulement un article et des vidéos.

**Matériel :** minimum VRAM et temps sur machine proche **non vérifiés**. **GB10 plausible [E]**, sous réserve du chargement séquentiel ; **5090 offload/quantification non vérifiés** ; **Turing non qualifiée**. Les scripts multi-GPU du README lancent aussi plusieurs tâches indépendantes : ce n'est pas une preuve qu'une tâche se répartit sur nos deux cartes 8 Go.

**Maturité : démo. Verdict : tester en second**, après Qwen-Video-Edit, qui réutilise davantage notre famille image. Ne pas ajouter deux éditeurs lourds avant de mesurer leur différence sur les mêmes plans.

### 27 — Light-A-Video : autre voie de rééclairage sans entraînement spécifique

**Article ouvert :** [2502.08590 — Light-A-Video: Training-free Video Relighting via Progressive Light Fusion](https://arxiv.org/abs/2502.08590), **2025-02-12**, révision **2025-03-12**.

**Dépôt :** [bcmi/Light-A-Video](https://github.com/bcmi/Light-A-Video). **Apache-2.0**, [licence lue](https://github.com/bcmi/Light-A-Video/blob/main/LICENSE). **Dernier commit : 2026-10-25**. Licence de tous les poids associés, notamment IC-Light et les différentes bases : **non vérifiée**.

**Apport :** attention de lumière cohérente et fusion progressive pour transférer à la vidéo les capacités d'un modèle de rééclairage image. Le dépôt a ajouté **Wan2.1 le 2025-03-11** et **CogVideoX le 2025-03-14**. Il faut choisir un chemin précis ; le qualificatif « sans entraînement » ne signifie pas sans modèle ni sans coût de diffusion.

**Matériel :** pas de couple mémoire/temps proche exploitable vérifié. **GB10/5090 plausibles [E]**, selon la base AnimateDiff, CogVideoX ou Wan choisie ; **Turing non vérifiée**, éventuellement seulement une petite base FP16. Aucun port H3 n'est établi.

**Maturité : démo. Verdict : tester comme solution de repli**, derrière LiveLight pour l'interaction et Relit-LiVE pour la chaîne documentée en mémoire.

### 28 — Cosmos-Transfer2.5 : transformer une prévisualisation 3D en rendu

**Article ouvert :** [2511.00062 — World Simulation with Video Foundation Models for Physical AI](https://arxiv.org/abs/2511.00062), première soumission **2025-10-28**, révision **2026-02-24**. La date initiale est bien en octobre malgré le préfixe numérique `2511`.

**Dépôt :** [nvidia-cosmos/cosmos-transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5). **Code : Apache-2.0**, [licence lue](https://github.com/nvidia-cosmos/cosmos-transfer2.5/blob/main/LICENSE). **Poids 2B : NVIDIA-Open**, étiquette abrégée de la [licence affichée sur la fiche](https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B), distincte de celle du code. **Dernier commit : 2026-06-07**. Sortie initiale **2025-10-06** ; ARM/Blackwell ajoutés **2025-11-25**, modèle Edge distillé **2026-02-23**.

**Apport :** contrôles profondeur, segmentation, contours, flou et RGB pour passer d'un rendu 3D/simulé à une vidéo réaliste. Bon outil de contrôle géométrique ; les exemples de robotique ne prouvent pas encore sa qualité pour dragons ou batailles spatiales.

**Matériel/mesures :** [documentation primaire](https://github.com/nvidia-cosmos/cosmos-transfer2.5/blob/main/docs/inference.md) : **65,4 Go**, 93 images ; H100 PCIe **264,13 s de génération / 533,58 s E2E**. Modèle Edge sur **RTX PRO 6000 Blackwell SE** : **78,5 s de diffusion**, contre 605,7 s pour la base. Ce GPU 96 Go n'est pas une 5090. **GB10 : mémoire plausible [E], ARM explicitement pris en charge mais exécution NV** ; **5090 : ne tient pas dans le profil stock**, offload supplémentaire NV ; **Turing : non**.

**Maturité : démo. Verdict : tester**, après Wan-Fun, pour les cas où conserver la géométrie de la prévisualisation est plus important que varier librement le plan.

### 29 — VFX Creator : des LoRA d'effets, avec contrôle publié incomplet

**Article ouvert :** [2502.05979 — VFX Creator: Animated Visual Effect Generation with Controllable Diffusion Transformer](https://arxiv.org/abs/2502.05979), **2025-02-09**, révision **2025-04-01**.

**Dépôt :** [vfx-creator0/VFXCreator](https://github.com/vfx-creator0/VFXCreator). **Licence propre : non vérifiée**, aucun LICENSE à la racine consultée. **Dernier commit : 2025-03-24**. [Poids sophiaa/VFXCreator](https://huggingface.co/sophiaa/VFXCreator) : licence **non vérifiée** sur la fiche ouverte.

**Apport :** base CogVideoX-5B-I2V, LoRA par catégorie d'effet, commandes spatiales par masque et temporelles par début/fin. OpenVFX couvre **15 catégories** ; cela donne un petit vocabulaire extensible, pas une infinité d'effets apprise. **LoRA généraux publiés ; poids du contrôle spatial/temporel encore non publiés dans la liste du dépôt.**

**Matériel :** **GB10 plausible [E]** ; **5090 potentielle avec gestion mémoire [E]**, minimum exact et vitesse proche **non vérifiés** ; **Turing 8 Go non qualifiée**. Le coût d'entraînement d'un nouvel effet doit être compté séparément du coût d'inférence.

**Maturité : démo partielle. Verdict : surveiller**, avec priorité à la publication du contrôle et d'une licence explicite. Utile comme référence pour une bibliothèque d'effets ; pas un module produit prêt à brancher.

### 30 — VFXMaster : transférer l'effet d'une vidéo de référence

**Article ouvert :** [2510.25772 — VFXMaster: Unlocking Dynamic Visual Effect Generation via In-Context Learning](https://arxiv.org/abs/2510.25772), **2025-10-29**.

**Dépôt :** [libaolu312/VFXMaster](https://github.com/libaolu312/VFXMaster). **Licence propre : non vérifiée**, aucun LICENSE à la racine consultée. **Dernier commit : 2026-04-07**. Le README donne les commandes de téléchargement `8ruceLi/VFXMaster` ; licence de ces poids **non vérifiée**. Base **CogVideoX-Fun-V1.1-5b-InP**.

**Apport :** une vidéo sert d'exemple d'effet et une image de cible ; apprentissage en contexte pour dissocier apparence de la cible et dynamique de l'effet. **Correction de la note 17 : poids et inférence sont maintenant cochés et des commandes existent.** Ce progrès ne démontre pas la conservation exacte d'un plan source complet ni les interactions physiques.

**Matériel :** exigence README **≥34 Go**, testé sur **A800-SXM4-80 Go**. **GB10 : capacité plausible [E], ARM NV** ; **5090 : sous le minimum publié**, offload supplémentaire NV ; **Turing : non**. Qwen2.5-VL-72B intervient dans les outils de préparation : ne pas le compter comme une obligation simultanée d'inférence sans examiner le chemin choisi. Temps proche **non vérifié**.

**Maturité : démo. Verdict : surveiller**, éventuellement banc GB10 après publication d'une licence claire. Plus prometteur pour « imiter cet effet » que pour « conserver toute ma vidéo et ajouter cet objet ».

### 31 — IC-Effect : ne pas confondre l'éditeur livré avec les Effect-LoRA annoncés

**Article ouvert :** [2512.15635 — IC-Effect: Precise and Efficient Video Effects Editing via In-Context Learning](https://arxiv.org/abs/2512.15635), **2025-12-17**.

**Dépôt :** [CUC-MIPG/IC-Effect](https://github.com/CUC-MIPG/IC-Effect). **Licence propre : non vérifiée**, aucun LICENSE à la racine consultée. **Dernier commit : 2026-01-29**. Code d'inférence, benchmark et **VideoEditor** annoncés publiés ce jour ; **Effect-LoRA, code d'entraînement et données VFX encore non cochés**. Licence des poids spécifiques **non vérifiée**.

**Apport :** édition en contexte sur Wan2.2-A14B, avec objectif de préserver le sujet tout en ajoutant un effet ; catalogue expérimental de 15 styles. Le point décisif est l'état des livraisons : télécharger le VideoEditor général ne donne pas automatiquement les LoRA qui reproduisent les effets de l'article.

**Matériel :** **GB10 plausible [E]** pour l'éditeur court ; **5090 quantification/offload non vérifiés** ; **Turing non qualifiée**. Pic, temps et profil monocarte de la branche effets **non vérifiés**.

**Maturité : démo partielle. Verdict : surveiller**, sans présenter les effets de démonstration comme un catalogue exploitable aujourd'hui.

### 32 — EasyVFX : adaptation d'un effet en une centaine d'étapes

**Article ouvert :** [2605.22051 — EasyVFX: Frequency-Driven Decoupling for Resource-Efficient VFX Generation](https://arxiv.org/abs/2605.22051), **2026-05-21**.

**Dépôt :** [mayuelala/EasyVFX](https://github.com/mayuelala/EasyVFX). **MIT**, [licence lue](https://github.com/mayuelala/EasyVFX/blob/main/LICENSE). **Dernier commit : 2026-05-24**. Des scripts et modèles sont présents ; publication d'un checkpoint EasyVFX complet distinct de la base **CogVideoX-5B-I2V : non vérifiée**.

**Apport :** séparation fréquentielle de l'apparence et du mouvement, mélange d'experts, puis adaptation à un effet inédit par **environ 100 étapes d'entraînement au moment du test sur un GPU**. Ce chiffre ne désigne ni le nombre d'étapes d'inférence vidéo ni une garantie de fonctionnement dans 32 Go. Intéressant pour produire en amont des variantes de bibliothèque, moins pour entraîner un effet à chaque clic utilisateur.

**Matériel :** **GB10 plausible en mémoire [E]** ; **5090 inférence potentielle [E], adaptation 100 étapes non vérifiée** ; **Turing non qualifiée**. Pic et temps sur machine proche **non vérifiés**. Le README contient encore une commande de clonage d'un autre projet : packaging à examiner avant tout essai.

**Maturité : recherche/démo. Verdict : surveiller**, en attendant un checkpoint et une recette d'adaptation réellement mesurée sur une carte de 24–32 Go.

### 33 — EffectMaker : catalogue très large, implémentation encore absente

**Article ouvert :** [2603.06014 — EffectMaker: Unifying Reasoning and Generation for Customized Visual Effect Creation](https://arxiv.org/abs/2603.06014), **2026-03-06**.

**Dépôt :** [ysy31415/EffectMaker](https://github.com/ysy31415/EffectMaker). **MIT**, [licence lue](https://github.com/ysy31415/EffectMaker/blob/main/LICENSE). **Dernier commit : 2026-03-06**. Racine consultée : README très court et licence ; **pas de chaîne d'inférence ni de poids vérifiés**. La [page de projet](https://effectmaker.github.io/) annonce encore le code à venir.

**Apport :** raisonnement multimodal pour comprendre un effet de référence puis guider sa génération. La taille annoncée d'EffectData, environ **120–130 k vidéos et plus de 3 000 effets** selon les sections des sources, est celle d'un corpus, **pas celle d'un menu de fonctions livrées**. Ne pas convertir les démonstrations de désintégration/transformation en promesse produit.

**Matériel : GB10/5090/Turing non vérifiés**, faute d'artefacts et de profil d'inférence ; vitesse proche **non vérifiée**.

**Maturité : recherche. Verdict : surveiller**. Une licence MIT sur un dépôt presque vide ne suffit pas à rendre le système exécutable.

### 34 — InsertAnywhere : insertion avec géométrie, occultations et lumière

**Article ouvert :** [2512.17504 — InsertAnywhere: Geometrically Grounded and Optics-Aware Video Object Insertion](https://arxiv.org/abs/2512.17504), **2025-12-19**, révision **2026-06-29**. Le titre reproduit est celui de la version courante ouverte ; la version initiale portait un autre titre.

**Dépôt :** [myyzzzoooo/InsertAnywhere](https://github.com/myyzzzoooo/InsertAnywhere). **Licence : non vérifiée**, aucun LICENSE à la racine consultée. **Dernier commit : 2026-07-28**. README et [projet](https://myyzzzoooo.github.io/InsertAnywhere/) : code à venir, poids **non vérifiés**.

**Apport :** ancrer un objet avec une pose 3D, propager son placement dans le temps et traiter les interactions optiques. Le masque d'édition doit englober ombres et reflets, pas seulement la silhouette de l'objet. C'est exactement le manque entre un calque détouré et une insertion crédible dans une prise de vue réelle. ROSE++ sert à l'apprentissage de ces interactions.

**Matériel : GB10/5090/Turing non vérifiés** ; aucun pic ni temps proche exploitable. Un budget 128 Go ne permet pas de conclure sans implémentation publiée.

**Maturité : recherche. Verdict : surveiller**, haute valeur scientifique mais faible disponibilité immédiate. Réutiliser dès maintenant le principe de masque élargi dans notre propre compositeur.

### 35 — OmniInsert : insertion par références sans masque manuel

**Article ouvert :** [2509.17627 — OmniInsert: Mask-Free Video Insertion of Any Reference via Diffusion Transformer Models](https://arxiv.org/abs/2509.17627), **2025-09-22**.

**Dépôt :** [Phantom-video/OmniInsert](https://github.com/Phantom-video/OmniInsert). **Apache-2.0**, [licence lue](https://github.com/Phantom-video/OmniInsert/blob/main/LICENSE). **Dernier commit : 2026-03-04**. La liste de tâches du README ne coche toujours pas la publication de l'inférence et d'InsertBench ; poids exécutables **non vérifiés**.

**Apport :** insertion guidée par plusieurs images de référence et par instruction, sans dessiner le masque de destination ; harmonisation contextuelle. Pertinent pour « place ce vaisseau dans ce ciel ». Les comparaisons qualitatives de l'article n'établissent ni la publication du modèle ni un meilleur classement de génération générale que H3.

**Matériel : GB10/5090/Turing non vérifiés**, sans chemin livré à qualifier ; vitesse proche **non vérifiée**. Ne pas appliquer automatiquement les profils matériels du modèle Phantom apparenté.

**Maturité : recherche. Verdict : surveiller**, en gardant un contrôle de placement explicite dans l'interface studio : le mode sans masque n'est pas toujours le plus précis.

### 36 — PhysChoreo : chorégraphier une action avec une simulation intermédiaire

**Article ouvert :** [2511.20562 — PhysChoreo: Physics-Controllable Video Generation with Part-Aware Semantic Grounding](https://arxiv.org/abs/2511.20562), **2025-11-25**, révision **2026-06-26**.

**Dépôt :** [KAKAKA0521/physchoreo](https://github.com/KAKAKA0521/physchoreo). **Licence propre : non vérifiée**, aucun LICENSE à la racine consultée. **Dernier commit : 2026-03-16**. Scripts de perception, simulation et rendu présents ; licences de l'ensemble des composants **non vérifiées**.

**Apport :** identifier parties et propriétés des objets, reconstruire une scène, appliquer une simulation MPM, puis conditionner le rendu Wan2.2. Permet d'exprimer une force ou un comportement matériel au lieu d'espérer que le prompt produise une collision plausible. La qualité dépend de la reconstruction initiale et de l'estimation des matériaux ; ce n'est pas une preuve de destruction ou de combustion physiquement exacte.

**Matériel : GB10 plausible [E]** en séparant perception, simulation et rendu ; **5090 chaîne par étapes possible [E], profil complet non vérifié** ; **Turing chaîne complète non qualifiée**. Temps et pic proche **non vérifiés**, les coûts de simulation varient avec la scène.

**Maturité : recherche. Verdict : surveiller**, avec intérêt pour un futur mode expert « force/impact ». Trop de sous-systèmes à qualifier pour devenir le premier moteur d'effets grand public.

### 37 — RealWonder : action physique interactive, avec une licence explicitement NC

**Article ouvert :** [2603.05449 — RealWonder: Real-Time Physical Action-Conditioned Video Generation](https://arxiv.org/abs/2603.05449), **2026-03-05**.

**Dépôt :** [liuwei283/RealWonder](https://github.com/liuwei283/RealWonder). **CC-BY-NC-SA-4.0**, [licence lue](https://github.com/liuwei283/RealWonder/blob/main/LICENSE.md). **Dernier commit : 2026-03-06**. Le README fournit les téléchargements de checkpoints, dont `ziyc/realwonder`, et les dépendances de reconstruction SAM-3D-Objects.

**Apport :** reconstruction depuis une image, simulation de forces/actions, puis conversion du flux optique et du RGB simulés en vidéo ; générateur Wan1,3B distillé en quatre étapes. Rigidité, déformation, fluides et granulaires sont démontrés. [Projet](https://liuwei283.github.io/RealWonder/) : **13,2 i/s, 480×832 sur H200**, démonstrations affichées accélérées ×2 ; aucun transfert de cette mesure vers une 5090 n'est justifié.

**Matériel : GB10/5090 plausibles [E] pour le générateur**, mais chaîne complète, mémoire et temps proches **non vérifiés** ; **Turing non qualifiée**. Le petit générateur n'englobe pas à lui seul la reconstruction et la simulation.

**Maturité : recherche/démo. Verdict : écarter du produit standard actuel**, conserver comme référence scientifique ; l'étiquette de licence NC est explicite, sans analyse juridique ici.

### 38 — FluidGen : fumée, feu et explosions guidés par un mouvement physique

**Article ouvert :** [2610.25660 — FluidGen: Physics-Aware Fluid Video Generation via Motion-Guided Post-Training](https://arxiv.org/abs/2610.25660), **2026-10-19**.

**Dépôt : non publié** dans les sources primaires consultées. La [page de projet](https://y-zheng18.github.io/FluidGen/) affiche **Code (soon)** et **Data (soon)**, sans dépôt exécutable. **Licence : non vérifiée ; dernier commit : sans objet.** Ne pas fabriquer une URL GitHub à partir du nom de l'article.

**Apport :** base Wan2.1-I2V-14B, prédiction conjointe de RGB et de vitesses 3D par pixel ; post-entraînement guidé par simulations Houdini et vidéos réelles. Démonstrations de fumée, feu, explosions et débris, y compris formes contrôlées. Le champ de vitesse peut aussi guider une simulation Houdini. **La génération vidéo n'est pas elle-même un solveur garantissant la conservation physique.**

**Matériel : GB10/5090/Turing non vérifiés** faute de poids ; capacité GB10 plausible seulement comme hypothèse pour une base 14B, pas comme verdict de fonctionnement de FluidGen. Temps proche **non vérifié**.

**Maturité : recherche. Verdict : surveiller en priorité pour la physique des effets**, sans en faire une dépendance de livraison. C'est l'une des nouveautés les plus pertinentes d'octobre 2026 pour notre thème.

### 39 — SPEED : interpolation générative, à comparer au RIFE déjà intégré

**Article ouvert :** [2607.15585 — SPEED: One-Step Pixel Diffusion for High-quality Video Frame Interpolation](https://arxiv.org/abs/2607.15585), **2026-07-17**.

**Dépôt :** [bbldCVer/SPEED](https://github.com/bbldCVer/SPEED). **Licence propre du code : non vérifiée**, aucun LICENSE à la racine consultée. **Dernier commit : 2026-07-20**. [Poids SPEED](https://huggingface.co/bbldCVer-hf/SPEED), destination actuelle de l'ancien lien `zhZ524/SPEED` : **Apache-2.0** affiché.

**Apport :** diffusion pixel une étape, génération multi-échelle 64→32→16 pour reconstruire les images intermédiaires sans passage VAE. À examiner pour occultations et mouvements rapides où RIFE se trompe. L'accélération **63,3 %** de l'article est relative à ses comparateurs ; elle ne prouve pas un gain équivalent sur notre RIFE ONNX. Les baisses de LPIPS ne sont pas des gains de fidélité mesurés sur nos duels.

**Matériel :** xformers, CuPy et noyau CUDA de corrélation ; **GB10/5090 plausibles en capacité [E], compilation NV**, **Turing 8 Go non vérifiée**, taille d'image déterminante. Le script de benchmark existe mais aucune mesure proche chiffrée n'a été vérifiée ; ce script n'a pas été exécuté ici.

**Maturité : démo. Verdict : surveiller**, puis petit comparatif seulement si la licence du code est documentée. **Conserver RIFE** pour la production déjà construite ; interpoler n'améliore ni la trajectoire physique ni la netteté d'une image source ratée.

### 40 — VideoPainter : très bon sujet d'inpainting, profil académique explicite

**Article ouvert :** [2503.05639 — VideoPainter: Any-length Video Inpainting and Editing with Plug-and-Play Context Control](https://arxiv.org/abs/2503.05639), **2025-03-07**, révision **2025-04-09**.

**Dépôt :** [TencentARC/VideoPainter](https://github.com/TencentARC/VideoPainter). **Academic**, étiquette abrégée du [texte lu](https://github.com/TencentARC/VideoPainter/blob/main/LICENSE), qui décrit l'usage académique/recherche/éducation et exclut l'usage commercial. **Dernier commit : 2025-04-08**. Code d'inférence et poids publiés ; la licence du système n'est pas rendue Apache par sa base CogVideoX.

**Apport :** encodeur de contexte léger, contrôle par masque et rééchantillonnage préservant l'identité pour inpainting et édition de longues vidéos. « Any-length » signifie traitement organisé sur des fenêtres, pas mémoire constante gratuite ni cohérence indéfinie. Intérêt méthodologique pour retirer un objet sans reconstruire tout le plan.

**Matériel : GB10 plausible [E]**, **5090 possible avec offload [E]**, **Turing 8 Go non qualifiée** ; pic et vitesse sur machine proche **non vérifiés**. Les faibles paramètres du seul adaptateur n'incluent pas les poids de la base.

**Maturité : démo. Verdict : écarter du produit standard actuel**, garder comme point de comparaison scientifique. Pour le chantier immédiat, préférer qualifier VACE-Fun.

## Ce que « effets spéciaux infinis » peut devenir dans le studio

Les chaînes suivantes sont **des propositions d'architecture**, pas des fonctions déjà implémentées ni des mesures. La nouveauté utile est d'assembler les briques avec les outils déjà construits. Un effet doit pouvoir être prévisualisé, déplacé, masqué, chronométré et corrigé sans régénérer arbitrairement toute la prise.

| Scène grand public | Chaîne proposée avec les pistes retenues | Point de contrôle décisif |
|---|---|---|
| **Dragon dans une prise réelle** | Référence Qwen-Image ; actif RGBA Wan-Alpha v2 ; trajectoire Wan-Move ou prévisualisation 3D→Wan-Fun ; masques SAM/ViTMatte existants ; ombre et harmonisation locale ; Relit-LiVE à comparer. | Le dragon passe derrière les personnes/arbres, conserve sa taille et ne glisse pas sur le sol. La génération de l'actif et le contrôle de trajectoire sont deux chemins à composer ; leur compatibilité directe n'est pas établie. |
| **Explosion avec fumée et débris** | H3 pour un plan entièrement généré ; pour une prise existante, élément d'effet séparé, masque temporel et composite ; lumière d'impact LiveLight ; FlashVSR+ en fin de chaîne. | Déclenchement à l'image voulue, ombre et lumière sur le décor, fumée semi-transparente. Les poids « Effect RGBA » de Wan-Alpha++ ne sont pas encore une dépendance disponible vérifiée. FluidGen reste une veille. |
| **Bataille spatiale** | TRELLIS/Pixal3D pour les actifs existants ; animation simple et passes profondeur/contours/segmentation→Wan-Fun ; trajectoires Wan-Move pour un élément isolé ; H3 pour les plans d'ensemble et le son. | Séparer les trajectoires, préserver les silhouettes et le nombre de vaisseaux. Un contrôle monocible ne résout pas automatiquement la chorégraphie de dix objets ni leurs occultations mutuelles. |
| **Duel au sabre lumineux** | Conserver la prise des acteurs ; suivre les lames et ancrer des segments lumineux procéduraux ; réutiliser les masques existants pour occultations ; LiveLight/Relit-LiVE pour une passe lumineuse ; Wan-Animate-2 seulement pour transformer le personnage. | Rectitude des lames, mains, contacts et passage devant/derrière le corps. Une retouche générative de toute l'image risque de changer les gestes ; l'effet de lame gagne à rester déterministe. |

**Séparation des passes :** conserver la vidéo source hors du masque d'intervention ; autoriser une zone supplémentaire pour ombres, reflets et illumination, explicitement contrôlée. Un masque strict limité à l'objet empêche les interactions lumineuses crédibles ; une régénération globale empêche de garantir la conservation du plan. Le choix de cette zone doit être éditable.

**Fond et retrait :** le détourage est déjà un acquis de 22. Le travail manquant est la reconstruction du fond derrière le sujet et son accord temporel : commencer par VACE-Fun, comparer DiffuEraser seulement avec ses dépendances identifiées. Une vidéo sur fond noir additionnée au plan peut servir pour un éclair ou des étincelles ; **ce n'est pas un alpha correct pour une fumée sombre ou semi-transparente**.

**Son :** les contrôleurs Wan et la plupart des éditeurs ci-dessus sont muets. Préserver les dialogues et ambiances sources, puis synchroniser bruitages, impacts et musique dans la chaîne audio existante. MiniMax-Music3 est un moteur musical, pas une preuve de synthèse universelle de bruitages synchronisés. Aucun module sonore supplémentaire non étudié n'est proposé dans ce rapport.

**Physique :** pour une collision, une trajectoire garantit surtout un déplacement ; pour une fumée, une vidéo plausible ne garantit pas un champ de vitesse conservatif. Réserver le mot « simulation » aux étapes effectivement simulées. PhysChoreo/RealWonder/FluidGen montrent des voies intéressantes, mais aucune chaîne ouverte vérifiée ici ne livre sur notre parc une destruction générale contrôlable, physiquement fiable et prête pour le produit.

## Les huit recommandations, dans l'ordre de travail

| Priorité | Recommandation | Machine et résultat attendu avant activation |
|---|---|---|
| **1** | **Conserver H3 comme moteur principal** et les outils image, son, 3D, détourage et interpolation déjà construits. | GB10 FastH3 / 5090 h3-fast et h3-max actuels. Aucun remplacement général démontré ; comparer les spécialistes sur la fonction qui manque. |
| **2** | **Adopter Wan2.2-Fun-5B-Control comme premier chantier de contrôle**, puis VACE-Fun-A14B pour les retouches plus difficiles. | 5090 d'abord pour le 5B ; GB10 pour le grand modèle. Un même petit rendu 3D doit piloter profondeur, pose, occultations et remplacement de fond. |
| **3** | **Tester Wan-Move pour les trajectoires** de dragon, vaisseau et projectile. | GB10 d'abord, exigence publiée 40 Go. Vérifier le chemin monocarte et la précision de trajectoire avant d'entreprendre la quantification 5090. |
| **4** | **Tester Wan-Alpha v2 pour une bibliothèque RGBA**, et maintenir ++ en veille jusqu'aux poids d'effets transitoires. | GB10, puis 5090 si une recette quantifiée est qualifiée. Tester chaque actif sur fond noir, blanc et damier avec caméra mobile. |
| **5** | **Comparer LiveLight et Relit-LiVE** sur lumière d'explosion et sabres ; garder un seul chemin par usage. | 5090 pour Relit-LiVE au plancher publié ≥24 Go ; LiveLight à qualifier. Mesurer stabilité du visage et lumière hors masque, pas seulement le débit. |
| **6** | **Adopter FlashVSR+ dans la file d'export**, avec SeedVR2 comme témoin déjà envisagé. | 5090, puis GB10 si les noyaux fonctionnent. Ne pas annoncer 4K temps réel : référence 4090 Turbo ~0,98 i/s, avant validation locale. |
| **7** | **Tester Wan-Animate-2 sur un seul personnage**, contre Wan-Animate existant. | GB10 seulement si une recette monocarte tient. Arrêter ce banc si le chemin reste dépendant du multi-A800 ; ne pas transformer l'essai en chantier de distribution. |
| **8** | **Qualifier SANA-Video 2.0 4-Step pour les brouillons T2V muets et Kandinsky6 Lite Distill comme repli AV**. | 5090 d'abord. SANA n'a pas de mesure proche vérifiée ; sa preview 4 pas ne gère pas l'image initiale. K6 dispose d'un protocole 5090 à 44,2 s/5 s SD audio, hors chargement/MP4, sans plafond 475 W connu. |

**Répartition pratique :** pc1 pour les essais à base 5B/3B et les exports ; pc6 pour les poids 14B, la retouche lourde et les prototypes dont la mémoire dépasse 32 Go. pc5 reste utile aux tâches indépendantes déjà compatibles FP16/FP32, au prétraitement et à la préparation des médias ; aucune nouvelle génération vidéo premium 8 Go n'est qualifiée par ce dossier. Faire fonctionner deux petites tâches en parallèle peut être utile ; répartir un gros générateur sur les deux Turing reste un projet distinct.

### Banc de décision proposé — à réaliser, pas exécuté ici

Limiter le premier banc aux **quatre scènes du tableau**, à trois variantes par méthode et à des clips de **5 s en 480p**, puis 720p si la méthode passe. Garder un témoin H3 et, pour chaque spécialité, l'outil déjà présent. Les variantes servent à mesurer le taux d'échec ; ne publier que le meilleur exemple masquerait le coût réel.

Relever séparément **chargement/compilation à froid, latence à chaud, encodage, audio, transferts CPU/GPU, pic VRAM alloué/réservé, RAM hôte et mémoire unifiée totale**. Sur 5090, consigner le plafond **475 W** et les réglages exacts ; sur GB10, éviter de compter deux fois les poids en copies CPU et GPU. Un temps par étape ne remplace pas le temps entre clic et fichier exploitable.

Noter ensuite : préservation du sujet hors masque, cohérence de l'identité, erreur de trajectoire, occultations, conservation des contacts, scintillement des ombres, fuite de couleur dans l'alpha, et perte de détail après upscale/interpolation. Le critère studio est **le temps machine par clip accepté**, avec taux de réussite, pas le meilleur débit isolé. Ce banc spécialisé peut justifier un outil meilleur que H3 pour une tâche, même si son générateur est moins bien classé en T2V général.

## Annexe de provenance — dépôts et derniers commits

Les tableaux suivants servent à retrouver les sources des **40 pistes**, pas à ajouter d'autres pistes au catalogue. Les dépôts regroupés dans une famille restent séparés pour la traçabilité. Date UTC du dernier commit de la branche par défaut, relevé par lecture de l'API GitHub avec une borne au **2026-11-03T23:59:59Z** ; le lien SHA pointe le commit exact. **Exception explicite : SoL-Refiner suit la branche sol-engine**, avec son propre relevé. Une date de commit récente ne démontre ni de nouveaux poids ni la qualité du système.


| Dépôt ouvert | Licence propre lue, ou absence signalée | Dernier commit UTC ; preuve |
|---|---|---|
| [Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1) | [Apache-2.0](https://github.com/Wan-Video/Wan2.1/blob/main/LICENSE.txt) | 2026-03-05 · [9737cba](https://github.com/Wan-Video/Wan2.1/commit/9737cba9c1c3c4d04b33fcad41c111989865d315) |
| [Wan-Video/Wan2.2](https://github.com/Wan-Video/Wan2.2) | [Apache-2.0](https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt) | 2026-09-21 · [1ea34ff](https://github.com/Wan-Video/Wan2.2/commit/1ea34ff48f87168174e12956e200b1d908b1c5ff) |
| [Lightricks/LTX-2](https://github.com/Lightricks/LTX-2) | [Community](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x) | 2026-10-18 · [e98f6d9](https://github.com/Lightricks/LTX-2/commit/e98f6d927d83c92ef2be6aec76c8440b19306e39) |
| [Tencent-Hunyuan/HunyuanVideo-1.5](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) | [Community](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/LICENSE) | 2026-04-10 · [60783e7](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/commit/60783e704160023913bee78f0b47036d393d4dfa) |
| [kandinskylab/kandinsky-5](https://github.com/kandinskylab/kandinsky-5) | [MIT](https://github.com/kandinskylab/kandinsky-5/blob/main/LICENSE) | 2026-01-19 · [3a74261](https://github.com/kandinskylab/kandinsky-5/commit/3a74261b957df0446c1969c5cedf8bbb07969ac2) |
| [kandinskylab/kandinsky-6](https://github.com/kandinskylab/kandinsky-6) | [MIT](https://github.com/kandinskylab/kandinsky-6/blob/main/LICENSE) | 2026-10-25 · [7ceeefa](https://github.com/kandinskylab/kandinsky-6/commit/7ceeefad7fb625011f7db602c43893a989f19c15) |
| [SkyworkAI/SkyReels-V3](https://github.com/SkyworkAI/SkyReels-V3) | [Skywork](https://github.com/SkyworkAI/SkyReels-V3/blob/main/LICENSE.txt) | 2026-01-30 · [28c771e](https://github.com/SkyworkAI/SkyReels-V3/commit/28c771e8456341be6a213e3d1133ed1fd19bf75d) |
| [genmoai/mochi](https://github.com/genmoai/mochi) | [Apache-2.0](https://github.com/genmoai/mochi/blob/main/LICENSE) | 2026-10-22 · [15c9bad](https://github.com/genmoai/mochi/commit/15c9bad662df1fa3e7b53136423695b286484c08) |
| [stepfun-ai/Step-Video-T2V](https://github.com/stepfun-ai/Step-Video-T2V) | [MIT](https://github.com/stepfun-ai/Step-Video-T2V/blob/main/LICENSE) | 2025-03-17 · [675e08c](https://github.com/stepfun-ai/Step-Video-T2V/commit/675e08c0dd08aaf60b4da1a2ce57e9bd0d8af31c) |
| [SandAI-org/MAGI-1](https://github.com/SandAI-org/MAGI-1) | [Apache-2.0](https://github.com/SandAI-org/MAGI-1/blob/main/LICENSE) | 2026-06-17 · [0fcefde](https://github.com/SandAI-org/MAGI-1/commit/0fcefdef8ce2df37a3b8890979433c06eb003328) |
| [SandAI-org/MAGI-2-preview](https://github.com/SandAI-org/MAGI-2-preview) | [Apache-2.0](https://github.com/SandAI-org/MAGI-2-preview/blob/main/LICENSE) | 2026-08-06 · [f68a0f9](https://github.com/SandAI-org/MAGI-2-preview/commit/f68a0f9bbccbea56e0177a9bd912abc3b18ffe61) |
| [FoundationVision/Waver](https://github.com/FoundationVision/Waver) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2025-08-27 · [fddc88f](https://github.com/FoundationVision/Waver/commit/fddc88f80866263b23a2a27e1a8bcccff22771df) |
| [meituan-longcat/LongCat-Video](https://github.com/meituan-longcat/LongCat-Video) | [MIT](https://github.com/meituan-longcat/LongCat-Video/blob/main/LICENSE) | 2026-05-27 · [6b3f4b8](https://github.com/meituan-longcat/LongCat-Video/commit/6b3f4b8582a8bc3f20f795735f5383716c4ba794) |
| [NVIDIA/cosmos-framework](https://github.com/NVIDIA/cosmos-framework) | [OpenMDW-1.1](https://github.com/NVIDIA/cosmos-framework/blob/main/LICENSE) | 2026-11-03 · [d04e506](https://github.com/NVIDIA/cosmos-framework/commit/d04e5067dd2f353fa8fab65fd99fcd86819e537d) |
| [character-ai/Ovi](https://github.com/character-ai/Ovi) | [Apache-2.0](https://github.com/character-ai/Ovi/blob/main/LICENSE) | 2025-11-15 · [5b69b25](https://github.com/character-ai/Ovi/commit/5b69b25a4b3115216e9ea53a37a04410be6ad39a) |
| [PKU-YuanGroup/Helios](https://github.com/PKU-YuanGroup/Helios) | [Apache-2.0](https://github.com/PKU-YuanGroup/Helios/blob/main/LICENSE.txt) | 2026-11-01 · [f1a8aad](https://github.com/PKU-YuanGroup/Helios/commit/f1a8aadd7c42df29968b9ed73b5c3bc6ae2980c4) |
| [NVlabs/Sana](https://github.com/NVlabs/Sana) | [Apache-2.0](https://github.com/NVlabs/Sana/blob/main/LICENSE) | 2026-10-29 · [890e500](https://github.com/NVlabs/Sana/commit/890e5000edb08ffbdaab3e5b0d6fbe25a8b2b3b7) |
| [NVlabs/Sana, sol-engine](https://github.com/NVlabs/Sana/tree/sol-engine) | **non vérifiée** : pas de LICENSE trouvé à la racine de cette branche | 2026-10-30 · [781e834](https://github.com/NVlabs/Sana/commit/781e8341fb3b29d3aea5d50265772e9619340b66) |
| [MotifTechnologies/ComfyUI-MotifVideo2B](https://github.com/MotifTechnologies/ComfyUI-MotifVideo2B) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-04-26 · [f563299](https://github.com/MotifTechnologies/ComfyUI-MotifVideo2B/commit/f563299313da6eec906bb72e552239331b9d5261) |
| [WeChatCV/Wan-Alpha](https://github.com/WeChatCV/Wan-Alpha) | [MIT](https://github.com/WeChatCV/Wan-Alpha/blob/main/LICENSE) | 2026-10-20 · [9e5d053](https://github.com/WeChatCV/Wan-Alpha/commit/9e5d0533da2dea390bbb0e50c59adfebe5613323) |
| [WeChatCV/Wan-Alpha_PlusPlus](https://github.com/WeChatCV/Wan-Alpha_PlusPlus) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-10-25 · [9c655d0](https://github.com/WeChatCV/Wan-Alpha_PlusPlus/commit/9c655d0614741e7a197a4fbca76e39bda5b787da) |
| [ali-vilab/Wan-Move](https://github.com/ali-vilab/Wan-Move) | [Apache-2.0](https://github.com/ali-vilab/Wan-Move/blob/main/LICENSE.txt) | 2026-01-05 · [80c58a7](https://github.com/ali-vilab/Wan-Move/commit/80c58a7d2ad175fa82a4d57f79f2a1415317dcfa) |
| [lixiaowen-xw/DiffuEraser](https://github.com/lixiaowen-xw/DiffuEraser) | [Apache-2.0](https://github.com/lixiaowen-xw/DiffuEraser/blob/main/LICENSE) | 2025-04-17 · [8e6f279](https://github.com/lixiaowen-xw/DiffuEraser/commit/8e6f279ac7531e27ad1849c6f8dab5372a8597e7) |
| [zhuxing0/Relit-LiVE](https://github.com/zhuxing0/Relit-LiVE) | [Apache-2.0](https://github.com/zhuxing0/Relit-LiVE/blob/main/LICENSE) | 2026-06-07 · [49ba180](https://github.com/zhuxing0/Relit-LiVE/commit/49ba18075b6d21d41d2016b5ca220287d5094a8e) |
| [bcmi/Light-A-Video](https://github.com/bcmi/Light-A-Video) | [Apache-2.0](https://github.com/bcmi/Light-A-Video/blob/main/LICENSE) | 2026-10-25 · [13c0eef](https://github.com/bcmi/Light-A-Video/commit/13c0eefd105135178c24c801bdbc093d688eac69) |
| [myyzzzoooo/InsertAnywhere](https://github.com/myyzzzoooo/InsertAnywhere) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-07-28 · [3b8856d](https://github.com/myyzzzoooo/InsertAnywhere/commit/3b8856dac7aa9dfc4f73083d862edaf78ccf0a45) |
| [Phantom-video/OmniInsert](https://github.com/Phantom-video/OmniInsert) | [Apache-2.0](https://github.com/Phantom-video/OmniInsert/blob/main/LICENSE) | 2026-03-04 · [af23a19](https://github.com/Phantom-video/OmniInsert/commit/af23a19f4d23c86bede91fe7c2aa2098f6236b5a) |
| [Wan-Video/Wan-Animate-2](https://github.com/Wan-Video/Wan-Animate-2) | [Apache-2.0](https://github.com/Wan-Video/Wan-Animate-2/blob/main/LICENSE) | 2026-08-08 · [3ad2fef](https://github.com/Wan-Video/Wan-Animate-2/commit/3ad2fef7d61d6200c9c653e0fe47be7616b323f3) |
| [TencentARC/VideoPainter](https://github.com/TencentARC/VideoPainter) | [Academic](https://github.com/TencentARC/VideoPainter/blob/main/LICENSE) | 2025-04-08 · [bbab6cd](https://github.com/TencentARC/VideoPainter/commit/bbab6cd5cd5cb89f0e2444305c32fd74a010ae0a) |
| [KlingAIResearch/UniVideo](https://github.com/KlingAIResearch/UniVideo) | [MIT](https://github.com/KlingAIResearch/UniVideo/blob/main/LICENSE.txt) | 2026-07-03 · [893c9da](https://github.com/KlingAIResearch/UniVideo/commit/893c9da04b87fdf5099e8e0e9ef164bca6753327) |
| [yunpeng1998/Qwen-Video-Edit](https://github.com/yunpeng1998/Qwen-Video-Edit) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-09-01 · [4e44e49](https://github.com/yunpeng1998/Qwen-Video-Edit/commit/4e44e4992793379752387724666d24873ed9b8b2) |
| [OpenImagingLab/FlashVSR_Plus](https://github.com/OpenImagingLab/FlashVSR_Plus) | [Apache-2.0](https://github.com/OpenImagingLab/FlashVSR_Plus/blob/main/LICENSE) | 2026-10-16 · [b548a2c](https://github.com/OpenImagingLab/FlashVSR_Plus/commit/b548a2cc2c929d3d4676f2973abe27876ec4dee7) |
| [bbldCVer/SPEED](https://github.com/bbldCVer/SPEED) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-07-20 · [40fadbe](https://github.com/bbldCVer/SPEED/commit/40fadbe85c88cc6e4015062389da464fd7e85ab9) |
| [vfx-creator0/VFXCreator](https://github.com/vfx-creator0/VFXCreator) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2025-03-24 · [df6ca7c](https://github.com/vfx-creator0/VFXCreator/commit/df6ca7c05458c6f170b2d55545cc5b9be50ba500) |
| [CUC-MIPG/IC-Effect](https://github.com/CUC-MIPG/IC-Effect) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-01-29 · [fbc27d3](https://github.com/CUC-MIPG/IC-Effect/commit/fbc27d38d0e20b915e145d4c16cc9ec6ab40b8a3) |
| [ysy31415/EffectMaker](https://github.com/ysy31415/EffectMaker) | [MIT](https://github.com/ysy31415/EffectMaker/blob/main/LICENSE) | 2026-03-06 · [1266b85](https://github.com/ysy31415/EffectMaker/commit/1266b85e32d77534e5a52a30cd7ffe7dad05f454) |
| [mayuelala/EasyVFX](https://github.com/mayuelala/EasyVFX) | [MIT](https://github.com/mayuelala/EasyVFX/blob/main/LICENSE) | 2026-05-24 · [cf3da03](https://github.com/mayuelala/EasyVFX/commit/cf3da03ce58d8810237ca113c102bcac8a17e7c6) |
| [libaolu312/VFXMaster](https://github.com/libaolu312/VFXMaster) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-04-07 · [0632c5a](https://github.com/libaolu312/VFXMaster/commit/0632c5a9979586adc1d4f96632e5b808ee11712f) |
| [mayuelala/LiveLight](https://github.com/mayuelala/LiveLight) | [MIT](https://github.com/mayuelala/LiveLight/blob/main/LICENSE) | 2026-08-04 · [f17e981](https://github.com/mayuelala/LiveLight/commit/f17e981f3f7afe2de70345a9547fd6534ff64ef8) |
| [liuwei283/RealWonder](https://github.com/liuwei283/RealWonder) | [CC-BY-NC-SA-4.0](https://github.com/liuwei283/RealWonder/blob/main/LICENSE.md) | 2026-03-06 · [51f5f80](https://github.com/liuwei283/RealWonder/commit/51f5f800b87a51d2e23ac0403251e02bf3f1d29d) |
| [KAKAKA0521/physchoreo](https://github.com/KAKAKA0521/physchoreo) | **non vérifiée** : pas de LICENSE général trouvé à la racine | 2026-03-16 · [b2d4f8a](https://github.com/KAKAKA0521/physchoreo/commit/b2d4f8a4289cc54f9b803b6903c0f4f0c1278b83) |
| [aigc-apps/VideoX-Fun](https://github.com/aigc-apps/VideoX-Fun) | [Apache-2.0](https://github.com/aigc-apps/VideoX-Fun/blob/main/LICENSE) | 2026-10-28 · [e8c314f](https://github.com/aigc-apps/VideoX-Fun/commit/e8c314fbfa494d0429bbef605c9f6112b79a7ead) |
| [nvidia-cosmos/cosmos-transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5) | [Apache-2.0](https://github.com/nvidia-cosmos/cosmos-transfer2.5/blob/main/LICENSE) | 2026-06-07 · [2ff49d0](https://github.com/nvidia-cosmos/cosmos-transfer2.5/commit/2ff49d0717af02057ae79bc75c00fbff9da1b4e7) |

**Exceptions de provenance :** FluidGen ne publie pas encore de dépôt à consulter ; son commit n'est donc pas inventé. Pour les dépôts sans LICENSE général trouvé, l'absence à la racine n'est pas une analyse de tous les fichiers : la licence applicable reste **non vérifiée**. Les licences de poids et de dépendances sont indiquées séparément dans les fiches ; une licence de code dans cette annexe ne les remplace pas.

**Périmètre de la conclusion :** titres et métadonnées arXiv vérifiés par ouverture des pages d'articles ; dépôts, fichiers de licence et commits lus dans les sources primaires. Les pages inaccessibles ou champs non documentés restent signalés. Les estimations GB10/5090/Turing ne sont pas des benchmarks. Aucun résultat local n'a été mesuré, et aucune pile n'a été installée pour ce rapport.



