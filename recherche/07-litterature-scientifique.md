# 07 — Revue de littérature scientifique pour Nexora Creative

Date : 30 octobre 2026. Auteur : agent de recherche (revue automatisée). Statut : **lecture, aucun test** ; rien installé, aucun poids téléchargé.

## 0. Méthode, conventions et limites

- **Sources interrogées** : alphaXiv (`discover_papers` sur les 9 axes, triés par récence ; lecture de pages PDF ciblées pour HoloCine, ViMax, VBench-2.0), API publique Hugging Face Papers (`/api/papers/{id}` : résumé, dépôt GitHub) avec repli sur l'API arXiv, texte HTML arXiv (recherche de tableaux de résultats pour ~15 articles), API GitHub (licence SPDX du **code**, nombre d'étoiles, dernière activité, relevés le 30/10/2026).
- **Étiquettes** : **[PUBLIÉ]** = chiffre tiré de l'article (résumé ou tableau), jamais reproduit par nous. **[MON AVIS]** = recommandation ou interprétation de ma part. **[À VÉRIFIER]** = information que je n'ai pas pu confirmer dans une source primaire lue ici (souvent une licence de **poids**).
- **Licence** : la licence indiquée est celle du **dépôt de code** (SPDX GitHub). La licence des **poids** peut différer ; elle n'a été relue pour aucun article de ce rapport. `NOASSERTION` = GitHub ne reconnaît pas la licence (souvent une licence maison) ; `None` = pas de fichier LICENSE, donc **aucun droit de réutilisation du code**.
- **Règle H3 rappelée** (rapport 03, §7 de l'architecture) : tout dérivé de MiniMax H3 (LoRA, version distillée, quantifiée, élaguée) suit la licence H3, y compris ses restrictions de territoire, quelle que soit l'étiquette du dépôt.
- **Limites** : pour une partie des articles je n'ai lu que le résumé et un extrait de tableau ; les chiffres sont ceux des auteurs, sur leurs propres bancs d'essai, souvent sur Wan 2.1/2.2 et sur H100/A100, rarement sur RTX 5090 et presque jamais sur GB10. Les articles d'octobre 2026 ont quelques jours d'existence et aucune reproduction indépendante.
- **Lots** : numérotation de `ARCHITECTURE-NEXORA-CREATIVE.md` §11 (0 spikes, 1 registre, 2 base/file, 3 agent GPU + FastVideo, 4 UI simple, 5 ComfyUI + Wan 2.2, 6 montage FreeCut, 7 AI Director v1, 8 bibliothèque de références, 9 mode expert/vidéos longues).

Légende des décisions : **ADOPTER MAINTENANT** (dans un lot 0-5), **PLUS TARD** (lot 6-9 ou après), **SURVEILLER** (pas de décision avant reproduction), **IGNORER**.

---

## Axe 1 — Accélération de la diffusion vidéo

### 1.1 Sol-H3 (NVIDIA) — accélération dédiée à MiniMax H3
- **Titre** : *Sol-H3: Recursive Self-Improvement for MiniMax-H3 Inference Acceleration on Sol-Engine across Cloud and Edge* — Yitong Li, …, Song Han, Enze Xie (NVIDIA) — 28/09/2026 — https://arxiv.org/abs/2609.35110
- **Idée** : ordonnanceur deux étages inter-résolutions (premières étapes en basse résolution, dernières en haute) relié par un module latent→latent appris qui évite le cycle décodage/réencodage VAE ; noyaux fusionnés trouvés par une boucle de recherche automatique.
- **[PUBLIÉ]** jusqu'à **30×** de bout en bout et **−20 %** de mémoire ; 5 s, 1344×768 avec audio : **3,5× plus rapide que le temps réel sur 8×GB200**, et **moins d'une minute en mémoire résidente sur un seul DGX Spark**.
- **Code/licence** : aucune licence publiée pour le pipeline (déjà relevé au rapport 03 §3.2, où le raffineur est LTX).
- **[MON AVIS] — SURVEILLER, puis ADOPTER l'idée au lot 3 sur GB10.** C'est le seul travail qui vise exactement notre matériel GB10 avec H3. Le schéma « basse résolution puis haute résolution sans repasser par le VAE » est réutilisable pour le profil **Qualité** sur GB10. Ne pas déployer le raffineur LTX (licence, rapport 03). Emplacement : recette moteur H3 dans l'`EngineAdapter` FastVideo, profil `qualité-gb10` du `CapabilityManifest`.

### 1.2 PDMD — distillation stabilisée, testée sur H3
- **Titre** : *PDMD: Projected Distribution Matching Distillation for Video Diffusion Models* — Zimo Wang, Junkun Yuan, … (UC San Diego, ByteDance) — 28/09/2026 — https://arxiv.org/abs/2609.35768
- **Idée** : projeter hors de la mise à jour DMD la composante due à l'erreur du critique ; « une ligne de code » qui supprime la sur-saturation et les textures artificielles de DMD.
- **[PUBLIÉ]** Wan 2.1, 4 NFE : VBench total **83,73** (+1,03 vs DMD). **MiniMax-H3 vidéo+audio, 4 NFE** : VideoGen-Eval visuel **83,17** (+0,41 vs meilleur distillé), meilleur sur les **6 métriques audio** parmi les modèles 4 NFE.
- **Code/licence** : page pdmd2026.github.io, « code et modèles disponibles » ; licence non relevée [À VÉRIFIER]. Un modèle H3 distillé PDMD serait un dérivé H3.
- **[MON AVIS] — PLUS TARD (candidat de profil Rapide H3).** Le chiffre H3 est le plus pertinent de toute la revue pour le profil Rapide. Nous ne distillons pas nous-mêmes ; on l'intègre si les auteurs publient des poids H3 4 étapes. À comparer en spike contre FastH3 V2 et la LoRA Turbo (rapport 03), sur le même jeu de prompts.

### 1.3 rCM — distillation par cohérence en temps continu (NVIDIA)
- **Titre** : *Large Scale Diffusion Distillation via Score-Regularized Continuous-Time Consistency* — Kaiwen Zheng et al. (Tsinghua, NVIDIA) — 09/10/2025 — https://arxiv.org/abs/2510.08431
- **Idée** : sCM (cohérence continue) + distillation de score comme régulariseur « mode-seeking » ; noyau JVP FlashAttention-2 pour passer à 14B.
- **[PUBLIÉ]** Wan 2.1 et Cosmos-Predict2 jusqu'à 14B : égale ou dépasse DMD2 en qualité, meilleure diversité, **1 à 4 étapes**, accélération **15× à 50×**.
- **Code/licence** : NVlabs/rcm, **Apache-2.0** (code).
- **[MON AVIS] — ADOPTER INDIRECTEMENT (lot 5)** via TurboDiffusion (1.4), qui l'utilise pour Wan. La meilleure diversité compte pour l'AI Director : deux candidats par plan n'ont d'intérêt que s'ils diffèrent.

### 1.4 TurboDiffusion — pile complète pour Wan sur RTX 5090
- **Titre** : *TurboDiffusion: Accelerating Video Diffusion Models by 100-200 Times* — Jintao Zhang, Kaiwen Zheng, … (Tsinghua/thu-ml, UC Berkeley) — 18/12/2025 — https://arxiv.org/abs/2512.16093
- **Idée** : SageAttention basse précision + attention creuse-linéaire entraînable (SLA) + distillation rCM + quantification **W8A8** + optimisations d'ingénierie.
- **[PUBLIÉ]** **100× à 200×** de bout en bout « même sur une seule RTX 5090 », qualité « comparable », sur Wan2.2-I2V-14B-720P et Wan2.1-T2V (1,3B et 14B).
- **Code/licence** : thu-ml/TurboDiffusion, **Apache-2.0** (code), points de contrôle inclus ; 3 857 étoiles ; actif (août 2026). Licence des poids distillés Wan [À VÉRIFIER], a priori héritée d'Apache-2.0 de Wan.
- **[MON AVIS] — ADOPTER MAINTENANT (lot 5, spike au lot 0).** C'est la voie la plus courte pour un **profil Rapide Wan 2.2** propre juridiquement, donc pour les comptes hors territoire H3. Spike : mesurer sur 5090 contre la référence 40 pas, et vérifier les noyaux sur GB10 (sm_121).

### 1.5 Self Forcing — combler l'écart entraînement/inférence en autorégressif
- **Titre** : *Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion* — Xun Huang, Zhengqi Li, Guande He, Mingyuan Zhou, et al. — 09/06/2025 — https://arxiv.org/abs/2506.08009
- **Idée** : pendant l'entraînement, chaque image est conditionnée sur les images **générées** (déroulé avec cache KV), avec une perte au niveau vidéo ; cache KV glissant à l'inférence.
- **[PUBLIÉ]** génération en flux **temps réel avec latence inférieure à la seconde sur un GPU**, qualité égale ou supérieure à des modèles non causaux plus lents.
- **Code/licence** : guandeh17/Self-Forcing, **Apache-2.0**.
- **[MON AVIS] — PLUS TARD (lot 9).** Fondation de toute la famille autorégressive (axe 2). Utile pour un futur mode « aperçu en direct » ; pas pour le produit débutant initial, où l'on génère des plans de 5-10 s.

### 1.6 VSA — attention creuse entraînable (FastVideo)
- **Titre** : *VSA: Faster Video Diffusion with Trainable Sparse Attention* — Peiyuan Zhang, Haofeng Huang, Yongqi Chen, Will Lin, et al. (UC San Diego, MBZUAI, Berkeley) — 19/05/2025 — https://arxiv.org/abs/2505.13389
- **Idée** : étape grossière (tuiles regroupées, sélection des tuiles critiques) + étape fine dans ces tuiles, un seul noyau différentiable.
- **[PUBLIÉ]** 85 % du MFU de FlashAttention3 ; −2,53× FLOPS d'entraînement sans perte ; sur Wan-2.1 : attention **6×** plus rapide, bout en bout **31 s → 18 s**.
- **Code/licence** : hao-ai-lab/FastVideo, **Apache-2.0**.
- **[MON AVIS] — ADOPTER MAINTENANT (lot 3), sans configuration de notre part.** Déjà embarqué dans FastH3 Preview (VSA 90 %, rapport 03). Rappel du rapport 04 : VSA n'aide pas à 480p/5 s ; le manifeste doit l'activer seulement au-delà d'un seuil de jetons (720p ou >5 s).

### 1.7 Sliding Tile Attention (STA) et Radial Attention — attention creuse sans réentraînement
- **STA** : *Fast Video Generation with Sliding Tile Attention* — Peiyuan Zhang et al. (UC San Diego) — 06/02/2025 — https://arxiv.org/abs/2502.04507. **[PUBLIÉ]** HunyuanVideo 720p 5 s : l'attention prend **800 s sur 945 s** ; STA ramène la latence à **685 s sans entraînement**, **268 s** avec ajustement (−0,09 % VBench). Code dans FastVideo (Apache-2.0).
- **Radial Attention** : *Radial Attention: O(n log n) Sparse Attention with Energy Decay for Long Video Generation* — Xingyang Li, Muyang Li, …, Song Han (MIT, NVIDIA) — 24/06/2025 — https://arxiv.org/abs/2506.19852. **[PUBLIÉ]** jusqu'à **1,9×** sur Wan2.1-14B/HunyuanVideo/Mochi ; avec LoRA, vidéos **4× plus longues**, entraînement **4,4×** moins cher, inférence **3,7×** plus rapide que l'attention dense. mit-han-lab/radial-attention, **Apache-2.0**.
- **[MON AVIS] — PLUS TARD (lot 9, vidéos longues).** Radial est la piste la plus intéressante pour **allonger** un plan Wan (10-20 s) sans changer de modèle. STA est surtout utile pour les modèles non distillés (profil Qualité).

### 1.8 SageAttention2 / SageAttention3 — attention 4 bits et FP4 Blackwell
- **SageAttention2** — Jintao Zhang et al. (Tsinghua) — 17/11/2024 — https://arxiv.org/abs/2411.10958. **[PUBLIÉ]** INT4 (Q,K) + FP8 (P,V), ~**3×** FlashAttention2 sur RTX 4090, perte de métriques « négligeable ».
- **SageAttention3** — Jintao Zhang et al. — 16/05/2025 — https://arxiv.org/abs/2505.11594. **[PUBLIÉ]** attention FP4 (microscaling) : **1 038 TOPS sur RTX 5090, 5×** le FlashAttention le plus rapide sur cette carte ; prête à l'emploi pour l'inférence.
- **Code/licence** : thu-ml/SageAttention, **Apache-2.0** ; dernière activité janvier 2026.
- **[MON AVIS] — ADOPTER MAINTENANT sur 5090 (lot 3), à valider sur GB10.** Gain gratuit (aucun réentraînement), cumulable avec la distillation. Risque déjà noté au rapport 04 : noyaux FP4 compilés pour sm_120 ; GB10 est sm_121. Le manifeste doit porter un champ `kernels.requires_sm` et le test de santé doit vérifier le noyau avant d'annoncer le profil.

### 1.9 Caches entre étapes : TeaCache, MagCache, TaylorSeer, DisCa
- **TeaCache** — Feng Liu et al. — 28/11/2024 — https://arxiv.org/abs/2411.19108 — **[PUBLIÉ]** jusqu'à **4,41×** sur Open-Sora-Plan, −0,07 % VBench. **Apache-2.0**.
- **MagCache** — Zehong Ma et al. — 10/06/2025 — https://arxiv.org/abs/2506.09045 — **[PUBLIÉ]** **2,68×** sur Wan 2.1, calibration sur **un seul** échantillon. **Apache-2.0**.
- **TaylorSeer** — Jiacheng Liu et al. — 10/03/2025 — https://arxiv.org/abs/2503.06923 — **[PUBLIÉ]** **5,00×** « presque sans perte » sur HunyuanVideo. **GPL-3.0** (copyleft).
- **DisCa** — Chang Zou et al. (SJTU, Tencent Hunyuan) — 05/02/2026 — https://arxiv.org/abs/2602.05449 — **[PUBLIÉ]** le cache sans entraînement **dégrade davantage** un modèle déjà distillé (étapes plus espacées) ; leur prédicteur appris + « Restricted MeanFlow » atteint **11,8×**. Code « bientôt ».
- **[MON AVIS] — ADOPTER MagCache pour le seul profil Qualité (lot 5, via ComfyUI/LightX2V) ; IGNORER les caches sur les profils distillés.** DisCa confirme ce que le rapport 04 avait relevé : cache + 4 étapes = perte de qualité. TaylorSeer : GPL-3.0, acceptable côté serveur mais à isoler ; inutile si MagCache suffit.

### 1.10 Quantification de DiT vidéo : SVDQuant/Nunchaku, FPSAttention, W4A4 Wan2.2, SparkDiffusion
- **SVDQuant** — Muyang Li et al. (MIT) — 07/11/2024 — https://arxiv.org/abs/2411.05007 — **[PUBLIÉ]** W4A4 avec branche basse-rang absorbant les valeurs aberrantes ; FLUX.1 12B : mémoire **÷3,5**, **3,0×** plus rapide que le 4 bits poids seuls sur 4090 portable ; LoRA sans requantification. mit-han-lab/nunchaku, **Apache-2.0**.
- **W4A4 Wan2.2-I2V (SVDQuant-GPTQ par pas de temps)** — Junhao Wu, Dezhong Yao, Hai Jin — 26/05/2026 — https://arxiv.org/abs/2605.27003 — **[PUBLIÉ]** mémoire de pointe **−59,3 %**, VBench moyen **−0,9 %**, qualité d'image −2,3 % ; calibration séparée par expert (haut/bas bruit) et par tranche de pas de temps. Code non relevé.
- **Distillation + basse précision Wan2.2 A14B** — Jinyang Du et al. (Beihang, SenseTime) — 30/05/2026 — https://arxiv.org/abs/2606.00658 — **[PUBLIÉ]** calibrer la quantification **sur l'élève distillé** plutôt que sur le maître ; dépasse le BF16 d'origine à 8 et 20 étapes ; 20 étapes = meilleur compromis testé.
- **FPSAttention** — Akide Liu et al. (Monash, Alibaba DAMO) — 05/06/2025 — https://arxiv.org/abs/2506.04648 — **[PUBLIÉ]** FP8 + parcimonie co-entraînés : noyau **7,09×**, bout en bout **4,96×** à 720p sur Wan2.1, sans perte VBench. Noyau Hopper (pas Blackwell grand public).
- **SparkDiffusion** — Yuxi Liu et al. (Peking U., Tsinghua, Alibaba) — 19/09/2026 — https://arxiv.org/abs/2609.23153 — **[PUBLIÉ]** 97 % de parcimonie d'attention + distillation 3 étapes sans CFG + FP8 : **265×** sur Wan2.1-T2V-14B-720P **sur une RTX 5090** (220× sur H100) ; 1,3B 480p débruité en **1,3 s**. Code non relevé.
- **LongLive-2.0** (NVIDIA) — 18/05/2026 — https://arxiv.org/abs/2605.18739 — **[PUBLIÉ]** inférence **W4A4 NVFP4** sur Blackwell, cache KV en NVFP4, décodage VAE asynchrone : **1,84×** à l'inférence ; 5B à **45,7 images/s**.
- **[MON AVIS] — ADOPTER les formats déjà packagés (lot 3) ; SURVEILLER SparkDiffusion.** Leçons utilisables tout de suite dans le registre : (a) pour Wan 2.2, la quantification doit être **calibrée par expert** et **sur la version distillée** ; (b) NVFP4 W4A4 ne concerne que Blackwell (5090, GB10 à vérifier), FP8 reste le repli universel ; (c) un manifeste = un couple (précision, nombre d'étapes) testé, jamais une combinaison libre. SparkDiffusion revendique un chiffre RTX 5090 spectaculaire mais sans code relevé : spike seulement si les poids sortent.

### 1.11 Élagage et VAE rapides : PARE, LightVAE, FlashDecoder
- **PARE** — Yutong Wang et al. (U. Sydney, Shanghai AI Lab, CUHK) — 26/05/2026 — https://arxiv.org/abs/2605.27336 — **[PUBLIÉ]** élagage largeur (têtes spatiales vs temporelles) + routeur de blocs par pas de temps sur Wan2.1-14B ; réduit le calcul par pas « en préservant la qualité VBench », cumulable avec la distillation (pas de chiffre global dans le résumé). Rappel rapport 03 : FastH3 « Trim » passe déjà de 50 à 42 blocs.
- **LightVAE** — Shiqiao Gu, …, Ruihao Gong (SenseTime/ModelTC, Beihang, NTU) — 10/10/2026 — https://arxiv.org/abs/2610.14726 — **[PUBLIÉ]** reparamétrage exact des Conv3D causales + compression basse-rang temporelle + élagage de blocs. Famille Wan VAE : **2,24×** (H100) et **1,11×** (RTX 5090) le débit des meilleurs décodeurs rapides existants ; **MiniMax-H3 : 2,97× le débit de décodage d'origine en gardant 99,51 % du score VBench-2.0**. Code ModelTC/LightVAE : **pas de licence** (36 étoiles).
- **FlashDecoder** — Minguk Kang, Suha Kwak (Pika Labs, POSTECH) — 16/07/2026 — https://arxiv.org/abs/2607.14898 — **[PUBLIÉ]** décodeur Transformer image par image avec cache KV glissant, espaces latents Wan2.1/2.2 : PSNR 1080p **41,55 vs 41,49 dB**, **3,6× à 4,7×** plus rapide, jusqu'à **11× moins de mémoire** (H100), jusqu'à 12× avec optimisations. Code non relevé.
- **[MON AVIS] — LightVAE : SURVEILLER (licence absente), forte priorité.** Le décodage VAE est un goulot réel (SeedVR2 mesure >95 % du temps dans le VAE à 720p, axe 9) et LightVAE est **le seul résultat publié sur le VAE de H3**. Sans licence, on ne peut ni copier ni déployer le code : demander une licence à ModelTC (qui publie LightX2V en Apache-2.0). FlashDecoder : PLUS TARD si poids publiés (intéressant pour le décodage de vidéos longues, lot 9). Élagage AdaLN/blocs : IGNORER en interne, on consomme les versions élaguées publiées (FastH3 Trim).

---

## Axe 2 — Vidéos longues et cohérentes

### 2.1 CausVid — de bidirectionnel lent à causal rapide
- *From Slow Bidirectional to Fast Causal Video Generators* — Tianwei Yin, Qiang Zhang, Richard Zhang, William T. Freeman, et al. — 10/12/2024 — https://arxiv.org/abs/2412.07772
- **Idée** : transformer un DiT bidirectionnel en générateur causal (KV cache) distillé par DMD en 4 étapes, initialisation par trajectoires ODE, maître bidirectionnel / élève causal.
- **[PUBLIÉ]** **9,4 images/s** en flux sur un GPU ; vidéo longue malgré un entraînement sur clips courts ; v2v en flux et changement de prompt à la volée sans entraînement.
- **Code** : non lié dans la fiche HF [À VÉRIFIER].
- **[MON AVIS] — IGNORER directement** ; base conceptuelle remplacée par Self Forcing / LongLive.

### 2.2 LongLive (NVIDIA) — long, interactif, temps réel
- *LongLive: Real-time Interactive Long Video Generation* — Shuai Yang, Wei Huang, …, Song Han (NVIDIA, MIT, HKU, Tsinghua) — 26/09/2025 — https://arxiv.org/abs/2509.22622
- **Idée** : AR image par image, **KV-recache** au changement de prompt, entraînement long (« train-long-test-long »), fenêtre courte + « frame sink ».
- **[PUBLIÉ]** 1,3B → génération d'une minute en **32 jours-GPU** de réglage ; **20,7 images/s sur un H100** ; jusqu'à **240 s** sur un H100 ; INT8 avec perte marginale.
- **Code/licence** : NVlabs/LongLive, **Apache-2.0**, très actif (29/10/2026). Base Wan 1,3B.
- **[MON AVIS] — PLUS TARD (lot 9).** Bon candidat pour un mode « plan long continu » (travelling, plan-séquence) sur Wan, pas pour la qualité premium.

### 2.3 LongLive-RAG et Ring Forcing — mémoire longue par récupération
- **LongLive-RAG** — Qixin Hu, Shuai Yang, Wei Huang, Song Han (NVIDIA, USC, MIT) — 01/06/2026 — https://arxiv.org/abs/2606.02553 — **[PUBLIÉ]** l'historique généré devient une mémoire adressable par contenu ; meilleur rang moyen VBench-Long sur plusieurs bases AR. **Apache-2.0**.
- **Ring Forcing** — Bowen Xue, …, (Stanford, MIT, Peking U., Berkeley, ByteDance) — 27/08/2026 — https://arxiv.org/abs/2608.26794 — **[PUBLIÉ]** entraînement en anneau qui force la récupération d'un historique lointain ; « permanence des objets » sur plusieurs minutes ; pas de chiffre dans le résumé. Code non relevé.
- **[MON AVIS] — SURVEILLER.** Le principe « mémoire récupérable » est le même que celui que nous mettons dans l'AI Director (références canoniques par entité). Pour l'instant, la mémoire inter-plans de Nexora reste **explicite** (images de référence par personnage/lieu), pas implicite dans le KV d'un modèle.

### 2.4 Causal-rCM — recette ouverte de distillation causale (NVIDIA), appliquée à Cosmos 3
- *Causal-rCM: A Unified Teacher-Forcing and Self-Forcing Open Recipe…* — Kaiwen Zheng, Guande He, …, Jintao Zhang (Tsinghua, UT Austin, NVIDIA) — 24/06/2026 — https://arxiv.org/abs/2606.25473
- **[PUBLIÉ]** CM en teacher-forcing = meilleure initialisation avant Self-Forcing DMD ; convergence **10×** plus rapide que les CM discrets ; Wan2.1-1.3B causal 2 étapes : **VBench-T2V 84,63** en 1 ou 2 étapes ; appliqué à **Cosmos 3** (génération conditionnée par action).
- **[MON AVIS] — SURVEILLER (pour le repli Cosmos3).** Si NVIDIA publie un Cosmos 3 distillé causal sous OpenMDW, il devient un candidat « aperçu rapide » propre juridiquement.

### 2.5 FramePack — contexte de taille fixe
- *Packing Input Frame Context in Next-Frame Prediction Models for Video Generation* — Lvmin Zhang, Maneesh Agrawala (Stanford) — 17/04/2025 — https://arxiv.org/abs/2504.12626
- **Idée** : compression des images passées pour un contexte constant ; échantillonnage anti-dérive en ordre temporel inversé avec extrémités établies d'abord.
- **[PUBLIÉ]** coût comparable à de la diffusion d'image, grands lots d'entraînement ; pas de chiffre de qualité dans le résumé.
- **Code/licence** : lllyasviel/FramePack, **Apache-2.0**, 17 334 étoiles. Base HunyuanVideo (licence Tencent, territoires exclus [À VÉRIFIER]).
- **[MON AVIS] — IGNORER pour le produit** (base HunyuanVideo, licence à territoires) ; retenir l'idée « fixer la dernière image d'abord » pour nos plans I2V première+dernière image.

### 2.6 SkyReels-V2 — Diffusion Forcing pour longueur infinie
- *SkyReels-V2: Infinite-length Film Generative Model* — Guibin Chen et al. (Skywork AI) — 17/04/2025 — https://arxiv.org/abs/2504.13074
- **Idée** : captioneur de langage cinématographique (SkyCaptioner-V1), RL sur le mouvement, Diffusion Forcing à bruit non décroissant pour l'extension.
- **[PUBLIÉ]** pas de chiffre retenu dans le résumé (résultats VBench dans le corps, non relus).
- **Code/licence** : SkyworkAI/SkyReels-V2, `NOASSERTION` (licence maison Skywork [À VÉRIFIER]).
- **[MON AVIS] — IGNORER** tant que la licence n'est pas relue ; l'idée du captioneur « langage de plan » est réutilisable pour l'étiquetage de nos prises (métadonnées de recherche dans la bibliothèque).

### 2.7 HoloCine — génération multi-plans holistique
- *HoloCine: Holistic Generation of Cinematic Multi-Shot Long Video Narratives* — Yihao Meng, Hao Ouyang, … (HKUST, Ant Group, ZJU, CUHK, NTU) — 23/10/2025 — https://arxiv.org/abs/2510.20822
- **Idée** : toute la scène est générée d'un bloc ; **Window Cross-Attention** (chaque plan ne lit que son prompt + le prompt global) ; **Sparse Inter-Shot Self-Attention** (dense dans un plan, résumé = jetons de la première image entre plans). Base **Wan2.2 14B**, 480×832, jusqu'à 13 plans, 5/15/60 s.
- **[PUBLIÉ]** (Tab. 1, 100 prompts maison) : contrôle des transitions (SCA) **0,9837** vs 0,4843 pour Wan2.2 seul ; cohérence inter-plans **0,7509** vs 0,7364 (StoryDiffusion+Wan2.2) ; sans les jetons de résumé inter-plans, l'identité s'effondre. Limite déclarée : raisonnement causal (verre resté vide après qu'on l'a rempli).
- **Code/licence** : yihao-meng/HoloCine, `NOASSERTION` [À VÉRIFIER] ; poids dérivés de Wan2.2 (Apache-2.0).
- **[MON AVIS] — PLUS TARD (lot 9), comme moteur « scène multi-plans » dans le registre.** Incompatible avec notre « reprise d'un seul plan » : une scène holistique se régénère en entier. À n'utiliser que pour un mode « scène courte d'un bloc » (≤ 15 s) avec devis séparé. Le **format de prompt hiérarchique** (global + par plan + balise `[shot cut]`) doit en revanche être adopté **dès le lot 7** dans le plan de plans de l'AI Director : il est compatible avec H3, Wan et les futurs modèles multi-plans.

### 2.8 CausalCine — multi-plans autorégressif en temps réel (même équipe)
- *CausalCine: Real-Time Autoregressive Generation for Multi-Shot Video Narratives* — Yihao Meng et al. (HKUST, Ant Group, SJTU) — 12/05/2026 — https://arxiv.org/abs/2605.12496
- **Idée** : modèle causal entraîné sur des séquences multi-plans natives ; **Content-Aware Memory Routing** (récupère les entrées KV par pertinence d'attention, pas par proximité) ; **réutilise le contexte sans régénérer les plans précédents** ; distillé en peu d'étapes.
- **[PUBLIÉ]** « dépasse nettement les AR de référence et approche les modèles bidirectionnels » (pas de chiffre dans le résumé).
- **[MON AVIS] — SURVEILLER, forte pertinence.** C'est l'architecture la plus alignée avec notre modèle « plans → prises » : chaque nouveau plan conditionné sur les précédents **sans** les régénérer. Si poids et licence ouverts paraissent, candidat lot 9.

### 2.9 Autres travaux octobre 2026 (dérive, mémoire, multi-plans sans entraînement)
- **In-Distribution Forcing** (Seoul National U., 02/10/2026, https://arxiv.org/abs/2610.03120) : correctif **au moment de l'inférence** contre la dérive des couleurs/textures au-delà de l'horizon d'entraînement (« self-caching ») ; code GitHub (8 étoiles).
- **CineWeaver** (SJTU, China Telecom, 29/07/2026, https://arxiv.org/abs/2607.26529) : multi-plans + références par plan **sans réentraînement**, en manipulant encodage positionnel et motifs d'attention d'un modèle pré-entraîné.
- **CineMem** (Shanghai AI Lab, Fudan, 13/10/2026, https://arxiv.org/abs/2610.17926) : cache KV regroupé en ligne, récupération par requête, cas de « retour dans un lieu déjà vu ».
- **[MON AVIS] — SURVEILLER CineWeaver** : « sans entraînement » sur un modèle pré-entraîné signifie potentiellement applicable à Wan 2.2 (et peut-être H3) via une recette ComfyUI ; à reproduire avant toute promesse.

---

## Axe 3 — Cohérence de sujets, personnages et produits

### 3.1 VACE — tout-en-un création/édition (Alibaba)
- *VACE: All-in-One Video Creation and Editing* — Zeyinzi Jiang, Zhen Han, Chaojie Mao, … (Alibaba Tongyi) — 10/03/2025 — https://arxiv.org/abs/2503.07598
- **Idée** : une interface unique (Video Condition Unit) pour référence→vidéo, v2v, v2v masqué ; « Context Adapter » qui injecte les tâches.
- **[PUBLIÉ]** « à égalité avec les modèles spécialisés » par tâche (résumé) ; sur le banc multi-sujets de MAGREF, VACE obtient ID-Sim **0,345** (vs 0,595 MAGREF).
- **Code/licence** : ali-vilab/VACE, **Apache-2.0** ; intégré à l'écosystème Wan.
- **[MON AVIS] — ADOPTER MAINTENANT (lot 5) comme recette Wan polyvalente** (références, inpainting, extension) dans ComfyUI. Moins bon que les spécialistes sur l'identité visage : ne pas l'utiliser seul pour les personnages humains.

### 3.2 Phantom et OmniInsert (ByteDance) — sujet → vidéo, insertion sans masque
- **Phantom** — Lijie Liu, Tianxiang Ma, Bingchuan Li, … (ByteDance) — 16/02/2025 — https://arxiv.org/abs/2502.11079 — alignement texte-image-vidéo sur triplets, mono et multi-sujets. **[PUBLIÉ par tiers]** sur le banc MAGREF multi-sujets : ID-Sim **0,481** ; sur le banc Stand-In : similarité visage **0,519** (14B). **Apache-2.0**.
- **OmniInsert** — Jinshu Chen et al. (ByteDance) — 22/09/2025 — https://arxiv.org/abs/2509.17627 — insertion d'un sujet de référence dans une vidéo existante **sans masque** ; « dépasse les solutions commerciales » sur leur InsertBench. **Apache-2.0** (code ; « sera publié » dans le résumé).
- **[MON AVIS] — Phantom : ADOPTER (lot 5) pour produits/objets multi-références sur Wan ; OmniInsert : PLUS TARD (lot 9)** pour le placement de produit dans une vidéo client (fonction très « Higgsfield »).

### 3.3 MAGREF — n'importe quelle référence, guidage masqué
- *MAGREF: Masked Guidance for Any-Reference Video Generation* — Yufan Deng, Xun Guo, … (ByteDance) — 29/05/2025 — https://arxiv.org/abs/2505.23742
- **[PUBLIÉ]** (banc multi-sujets des auteurs) : ID-Sim **0,595**, score total **0,694** vs Phantom 0,575, VACE 0,590, SkyReels-A2 0,527, Kling 1.6 0,598, Vidu 2.0 0,603.
- **Code/licence** : MAGREF-Video/MAGREF, **Apache-2.0** ; base Wan.
- **[MON AVIS] — ADOPTER (lot 5)** comme recette « plusieurs personnages + décor » pour Wan. Chiffres sur le banc des auteurs : à confirmer sur notre jeu de scénarios au lot 7.

### 3.4 Stand-In — identité légère (≈1 % de paramètres)
- *Stand-In: A Lightweight and Plug-and-Play Identity Control for Video Generation* — Bowen Xue, Qixin Yan, … (WeChat Vision, Tencent) — 11/08/2025 — https://arxiv.org/abs/2508.07901
- **Idée** : branche image conditionnelle + auto-attention restreinte ; LoRA rang 128 sur QKV des jetons image ; appris avec **2 000 paires**.
- **[PUBLIÉ]** similarité visage **0,724** vs Phantom-14B 0,519 et 1,3B 0,440 (banc des auteurs, Wan2.1-14B) ; compatible avec sujet, pose, stylisation, échange de visage.
- **Code/licence** : WeChatCV/Stand-In, **Apache-2.0**, actif (août 2026).
- **[MON AVIS] — ADOPTER MAINTENANT (lot 5) comme module identité par défaut pour Wan**, combinable avec VACE/pose. Au lot 8, chaque personnage de la bibliothèque (avec consentement vérifié, AUP 13) porte une image d'identité utilisable par Stand-In.

### 3.5 Lynx — identité haute fidélité (ByteDance)
- *Lynx: Towards High-Fidelity Personalized Video Generation* — Shen Sang et al. (ByteDance) — 19/09/2025 — https://arxiv.org/abs/2509.15496
- **Idée** : ID-adapter (ArcFace → Perceiver Resampler → jetons) + Ref-adapter (traits VAE denses injectés par attention croisée).
- **[PUBLIÉ]** 40 sujets × 20 prompts = 800 cas ; jugé par Gemini-2.5-Pro : suivi du prompt **0,779** vs Phantom 0,664, Stand-In 0,611, MAGREF 0,575.
- **Code/licence** : bytedance/lynx, **Apache-2.0**.
- **[MON AVIS] — ADOPTER en second candidat identité (lot 5)** : Stand-In et Lynx deviennent les deux candidats de l'AI Director pour un plan « visage », le juge identité (ArcFace) tranche. Note : le banc Lynx est noté par un VLM, voir axe 8 sur la fiabilité de ce type de juge.

### 3.6 SkyReels-A2 — éléments → vidéo
- *SkyReels-A2: Compose Anything in Video Diffusion Transformers* — Zhengcong Fei et al. (Skywork AI) — 03/04/2025 — https://arxiv.org/abs/2504.02436
- **[PUBLIÉ par tiers]** score total **0,527** sur le banc MAGREF (dernier des modèles ouverts comparés).
- **Code/licence** : `NOASSERTION` [À VÉRIFIER].
- **[MON AVIS] — IGNORER** (licence floue, dépassé par MAGREF/Phantom).

### 3.7 Identity-GRPO — RL pour l'identité multi-personnes
- *Identity-GRPO: Optimizing Multi-Human Identity-preserving Video Generation via Reinforcement Learning* — Xiangyu Meng et al. (Alibaba, Fudan) — 16/10/2025 — https://arxiv.org/abs/2510.14256
- **[PUBLIÉ]** jusqu'à **+18,9 %** sur les métriques de cohérence humaine pour VACE et Phantom.
- **[MON AVIS] — IGNORER pour l'entraînement** (pas notre métier) ; à **ADOPTER si des poids post-entraînés sont publiés**, en remplacement direct dans la même recette.

### 3.8 Travaux 2026 : Vera (S2V humain), MSR, OmniShowcase, AdSpark
- **Vera S2V** (22/07/2026, https://arxiv.org/abs/2607.20247) : million de paires identité-alignées, supervision masquée sur l'identité, liaison rôle↔identité multi-personnes ; pas de chiffre dans le résumé ; code non relevé.
- **MSR** (Licon Studio, 16/09/2026, https://arxiv.org/abs/2609.18393) : références multiples par « emplacements » numérotés, **LoRA sur LTX** ; les auteurs notent eux-mêmes la confusion sur vêtements similaires et changements de point de vue. **IGNORER** (base LTX, interdite chez nous, rapport 03).
- **OmniShowcase** (KAIST, 26/10/2026, https://arxiv.org/abs/2610.35684) : produit vu sous **360°** à partir de plusieurs vues, conditionné par une platine de cartes de normales reconstruites ; code GitHub (licence non relevée). **SURVEILLER** : exactement le cas « produit qui tourne » des publicités e-commerce.
- **AdSpark** (Peking U., JD, 07/10/2026, https://arxiv.org/abs/2610.10047) : 300 K triplets publicitaires et banc à 6 dimensions dont **fidélité produit** et **efficacité publicitaire** ; « publié après acceptation ». **PLUS TARD (lot 7)** : la grille AdSpark-Bench est un bon modèle de rubrique pour le juge d'un plan « produit ».

---

## Axe 4 — Contrôle caméra et cinéma

### 4.1 CameraCtrl / CameraCtrl II
- **CameraCtrl** — Hao He, Yinghao Xu, Yuwei Guo, Gordon Wetzstein, … (CUHK, Stanford) — 02/04/2024 — https://arxiv.org/abs/2404.02101 — module caméra prêt à brancher (rayons de Plücker) entraîné sur un T2V gelé. **[PUBLIÉ]** pas de chiffre retenu (résumé qualitatif). **Apache-2.0** ; dépôt inactif depuis 2024.
- **CameraCtrl II** — Hao He et al. (CUHK, Stanford, ByteDance) — 13/03/2025 — https://arxiv.org/abs/2503.10592 — préserve la dynamique sous grands mouvements de caméra, exploration par trajectoires successives. Pas de code relevé.
- **[MON AVIS] — IGNORER le code** (ancien, pas sur nos modèles) ; retenir la **paramétrisation Plücker**, devenue standard, comme format interne des trajectoires dans le manifeste.

### 4.2 MotionCtrl — caméra et objets séparés
- *MotionCtrl: A Unified and Flexible Motion Controller for Video Generation* — Zhouxia Wang et al. (Tencent ARC) — 06/12/2023 — https://arxiv.org/abs/2312.03641 — **[PUBLIÉ]** qualitatif dans le résumé. **Apache-2.0**.
- **[MON AVIS] — IGNORER** (2023, bases anciennes) ; l'idée « caméra et trajectoire d'objet sont deux contrôles distincts » doit se retrouver dans l'UI expert (lot 9).

### 4.3 Uni3C — caméra + mouvement humain par nuage de points (Alibaba DAMO)
- *Uni3C: Unifying Precisely 3D-Enhanced Camera and Human Motion Controls for Video Generation* — Chenjie Cao, Jingkai Zhou, … (Alibaba DAMO, Fudan) — 21/04/2025 — https://arxiv.org/abs/2504.14899
- **Idée** : PCDController (nuage de points issu de la profondeur monoculaire) sur un modèle gelé ; guidage 3D conjoint (scène + SMPL-X).
- **[PUBLIÉ]** surcoût d'inférence **+23 %** (480p : 62,3 s vs 50,5 s) et **+17 %** (720p : 213,4 s vs 182,7 s) par rapport à RealisDance-DiT ; « dépasse nettement » les concurrents en contrôle caméra.
- **Code/licence** : ewrfcas/Uni3C, **Apache-2.0** ; base Wan.
- **[MON AVIS] — ADOPTER (lot 5, recette Wan « caméra précise »).** Les presets caméra du lot 4 (travelling, orbite, dolly) se compilent en trajectoires ; Uni3C est l'exécutant précis côté Wan. Coût +17-23 % à intégrer dans la formule de prix du manifeste.

### 4.4 ReCamMaster — re-filmer une vidéo existante (Kuaishou)
- *ReCamMaster: Camera-Controlled Generative Rendering from A Single Video* — Jianhong Bai, Menghan Xia, … (ZJU, Kuaishou, CUHK) — 14/03/2025 — https://arxiv.org/abs/2503.11647
- **Idée** : conditionner un T2V pré-entraîné par la vidéo source ; jeu de données multi-caméras synchronisées rendu sous Unreal Engine 5.
- **[PUBLIÉ]** (Tab. 2) FID **57,10**, FVD **122,74**, erreur de rotation **1,22**, de translation **4,85**, FVD-V **90,38** — meilleur que DaS (FVD 159,60), Trajectory-Attention (276,06), GCD (367,32). Applications annoncées : stabilisation, super-résolution, outpainting.
- **Code/licence** : KwaiVGI/ReCamMaster, **MIT** ; base Wan.
- **[MON AVIS] — PLUS TARD (lot 9) comme capacité `v2v.recamera`.** Licence MIT propre, base Wan : la fonction « re-filmer ma vidéo sous un autre angle » est un argument produit fort ; elle est plus lourde (v2v complet) et ne doit pas entrer dans le parcours débutant initial.

### 4.5 TrajectoryCrafter, SpaceTimePilot, CameraAnything, FlashRender — re-filmage 2025-2026
- **TrajectoryCrafter** (Tencent, CUHK, 07/03/2025, https://arxiv.org/abs/2503.05638) : rendu de nuage de points + vidéo source en double flux. Code `NOASSERTION`.
- **SpaceTimePilot** (Cambridge, Adobe, 31/12/2025, https://arxiv.org/abs/2512.25075) : change **à la fois** le point de vue et le temps (ralenti, inversion, gel) d'une vidéo monoculaire. Code GitHub (licence non relevée).
- **CameraAnything** (CUHK, Ant, Tsinghua, ZJU, HKUST, 27/07/2026, https://arxiv.org/abs/2607.24591) : contrôle **intrinsèque + extrinsèque** (focale, résolution native, position) et transitions multi-plans en une génération ; code non relevé.
- **FlashRender** (EverEx, Yonsei, Korea U., 03/09/2026, https://arxiv.org/abs/2609.03563) : re-filmage en peu d'étapes (MeanFlow + distillation de carte de flot) ; **[PUBLIÉ]** qualité et cohérence géométrique des modèles multi-étapes **à 25× moins de calcul d'échantillonnage**. Code GitHub (13 étoiles, licence non relevée).
- **[MON AVIS] — SURVEILLER FlashRender et CameraAnything.** FlashRender rend le re-filmage compatible avec un coût « débutant » ; CameraAnything couvre « recadrer en 9:16 sans rogner » (adaptation multi-plateforme), cas fréquent chez nos utilisateurs.

### 4.6 Caméra sans entraînement : « Probing into Camera Control », WorldForge V2
- **Probing into Camera Control of Video Models** (Oxford, 14/05/2026, https://arxiv.org/abs/2605.14815) : la caméra comme **champ de déplacements** appliqué par rééchantillonnage différentiable des latents pendant le débruitage ; **sans entraînement**, « dégradation minimale » vs bases fine-tunées ; sert de sonde des biais des modèles.
- **WorldForge V2** (Westlake U., 22/10/2026, https://arxiv.org/abs/2610.31640) : guidage sans entraînement par références déformées + « Trajectory LoRA » sur les blocs les plus sensibles.
- **[MON AVIS] — SURVEILLER, potentiel élevé pour H3.** Une méthode sans entraînement est la seule voie réaliste pour donner un contrôle caméra précis à **H3** (pour lequel aucun module caméra ouvert n'existe à ma connaissance). Spike candidat après le lot 5 : appliquer la méthode Oxford à H3 sur 3 presets (pan, dolly, orbite) et mesurer l'erreur de pose.

---

## Axe 5 — Édition et transformation vidéo

### 5.1 Wan-Animate et Wan-Animate-2 — animation et remplacement de personnage
- **Wan-Animate** — Gang Cheng, Xin Gao, Li Hu, … (Alibaba Tongyi / HumanAIGC) — 17/09/2025 — https://arxiv.org/abs/2509.14055 — squelette spatialement aligné + traits faciaux implicites ; mode **remplacement** avec **LoRA de relighting** pour accorder lumière et colorimétrie. **[PUBLIÉ]** (Tab. 1, banc maison) meilleures valeurs des trois métriques rapportées : **0,834 / 0,205 / 94,65** (vraisemblablement SSIM↑ / LPIPS↓ / FVD↓, en-têtes non relus) vs X-portrait2 0,825 / 0,212 / 98,03 ; préféré en évaluation humaine à Runway Act-Two et DreamActor-M1. Poids intégrés au dépôt Wan2.2 (**Apache-2.0** pour le code ; poids [À VÉRIFIER], a priori Apache-2.0).
- **Wan-Animate-2** — Guangyuan Wang, Li Hu, … (Alibaba) — 06/08/2026 — https://arxiv.org/abs/2608.06009 — consomme directement la vidéo motrice (plus d'extracteur de pose) ; **contrôle du point de vue par texte** ; variante **Lite temps réel** par Self-Forcing. Code/poids non relevés.
- **[MON AVIS] — ADOPTER Wan-Animate MAINTENANT (lot 5) comme capacités `motion-transfer` et `replace`** (déjà prévues dans le manifeste). Garde-fou AUP 13/L4 : remplacement de personne réelle seulement avec consentement vérifié. Wan-Animate-2 : PLUS TARD, si poids ouverts.

### 5.2 PAI-Actor et PAI-Studio (Utopai) — remplacement multi-personnages, fond cinématographique
- **PAI-Actor** (05/09/2026, https://arxiv.org/abs/2609.05918) : remplacement de **plusieurs** personnages dans une scène réelle, 1080p bidirectionnel puis distillé en v2v autorégressif.
- **PAI-Studio** (31/05/2026, https://arxiv.org/abs/2606.01399) : remplacement de **fond** aligné sur le mouvement de caméra avec ré-éclairage du premier plan ; 30 K exemples issus de films.
- **[PUBLIÉ]** « surpasse les solutions ouvertes et API » (pas de chiffre dans les résumés). Code non relevé.
- **[MON AVIS] — SURVEILLER** (pas de code ; même équipe, sortie probable de poids à suivre).

### 5.3 Vera (Netflix) — édition en calques avec matte alpha
- *Vera: A Layered Diffusion Model for Content-Preserving Video Editing* — Hongkai Zheng, …, Yisong Yue (Netflix) — 22/06/2026 — https://arxiv.org/abs/2606.23610
- **Idée** : générer **un calque d'édition + un alpha** à composer sur la source, au lieu de régénérer tous les pixels ; MoT avec un DiT par calque.
- **[PUBLIÉ]** meilleure préservation du contenu que les éditeurs ouverts, qualité d'édition compétitive (benchmark et étude humaine ; 486 K images d'entraînement).
- **[MON AVIS] — SURVEILLER, idée à ADOPTER dans le format de projet (lot 6).** Un calque + alpha s'intègre naturellement dans FreeCut (composition non destructive) et respecte la règle « retake sans casser le montage ». Si un modèle ouvert équivalent sort, la capacité `edit.layer` doit produire un calque, pas une vidéo aplatie.

### 5.4 Qwen-Video-Edit, OmniXRef — édition par instruction
- **Qwen-Video-Edit** (UT Austin, Reve, 14/08/2026, https://arxiv.org/abs/2608.14790) : réutilise **Qwen-Image-Edit** sur les latents VAE de Wan 2.1 disposés en planche-contact ; affinage sur Ditto-1M ; quelques pas Wan 2.2 en option pour la cohérence temporelle.
- **OmniXRef** (Brown, Adobe, 15/10/2026, https://arxiv.org/abs/2610.22744) : édition à références multiples texte+image+**vidéo** (transférer la caméra, le mouvement, le style ou un effet VFX d'une vidéo de référence) ; « dépasse les spécialistes et les modèles commerciaux » sur OmniXRef-Bench.
- **[MON AVIS] — Qwen-Video-Edit : SURVEILLER** (si poids Apache-2.0 publiés, éditeur par instruction peu coûteux) ; **OmniXRef : SURVEILLER** (Adobe, publication de poids incertaine) — son interface « banque de références » est un bon modèle pour l'UI expert.

### 5.5 Relighting vidéo : RelightVid, LiveLight
- **RelightVid** (Shanghai AI Lab, Fudan, SJTU, ZJU, Stanford, CUHK, 27/01/2025, https://arxiv.org/abs/2501.16330) : ré-éclairage par vidéo de fond, texte ou carte d'environnement, sans décomposition intrinsèque. Code GitHub (licence non relevée), base image IC-Light.
- **LiveLight** (HKUST et al., 03/08/2026, https://arxiv.org/abs/2608.01771) : ré-éclairage **temps réel en flux** avec lumières 3D interactives (cartes d'irradiance multi-plans).
- **[MON AVIS] — PLUS TARD (lot 9).** Pour le lot 5, le seul relighting utile est la **LoRA de relighting de Wan-Animate** (remplacement). Licence IC-Light à vérifier avant RelightVid.

### 5.6 SkyReels-V4 — modèle unifié vidéo+audio+inpainting
- *SkyReels-V4: Multi-modal Video-Audio Generation, Inpainting and Editing model* — Guibin Chen et al. (Skywork) — 25/02/2026 — https://arxiv.org/abs/2602.21818 — **[PUBLIÉ]** jusqu'à **1080p, 32 images/s, 15 s**, multi-plans, audio synchronisé ; génération basse résolution complète + images clés haute résolution, puis SR et interpolation dédiées.
- **[MON AVIS] — SURVEILLER** (concurrent de H3 en « omni » ; licence et poids non vérifiés). Son schéma « basse résolution complète + images clés HD + SR » rejoint celui de Sol-H3 (1.1) : c'est la tendance pour atteindre 1080p à coût raisonnable.

---

## Axe 6 — Audio-vidéo joint, foley, lip-sync

### 6.1 Ovi (Character.AI) — deux tours jumelles audio/vidéo
- *Ovi: Twin Backbone Cross-Modal Fusion for Audio-Video Generation* — Chetwin Low, Weimin Wang, Calder Katyal (Character.AI, Yale) — 30/09/2025 — https://arxiv.org/abs/2510.01284
- **Idée** : tour audio de même architecture que la tour vidéo (Wan2.2 5B), échanges bloc par bloc de timing (RoPE mis à l'échelle) et de sémantique (attention croisée bidirectionnelle).
- **[PUBLIÉ]** évaluation par **taux de victoire par paires, étude en aveugle de 50 participants** ; audio évalué selon le protocole MMAudio (FD, IS, CLAP). Chiffres de victoire non relevés ici.
- **Code/licence** : character-ai/Ovi, **Apache-2.0**, poids publiés.
- **[MON AVIS] — ADOPTER (lot 5) comme repli audio-vidéo natif hors territoire H3**, à mettre en concurrence avec Kandinsky 6 (6.4). Base Wan 5B : qualité visuelle inférieure à H3 ; adapté aux plans dialogués courts.

### 6.2 UniVerse-1 (StepFun) — « couture d'experts »
- *UniVerse-1: Unified Audio-Video Generation via Stitching of Experts* — Duomin Wang et al. (StepFun, HKUST) — 07/09/2025 — https://arxiv.org/abs/2509.06155 — fusion des blocs d'un modèle vidéo et d'un modèle musique pré-entraînés ; ~**7 600 h** d'affinage audio-vidéo ; banc Verse-Bench. **Apache-2.0**.
- **[MON AVIS] — IGNORER pour la production** (dépassé par Ovi/Kandinsky 6/H3) ; **Verse-Bench** reste utile comme jeu de prompts audio-vidéo pour nos tests de non-régression.

### 6.3 JavisDiT / JavisDiT++
- **JavisDiT** — Kai Liu et al. (ZJU, NUS, …) — 30/03/2025 — https://arxiv.org/abs/2503.23377 ; **JavisDiT++** — 22/02/2026 — https://arxiv.org/abs/2602.19163 — MoE spécifique à la modalité, **TA-RoPE** (synchronisation image par image entre jetons audio et vidéo), **AV-DPO** ; base Wan2.1-1.3B, ~1 M d'entrées publiques. **[PUBLIÉ]** « état de l'art » ouvert (pas de chiffre dans le résumé). **Apache-2.0**.
- **[MON AVIS] — IGNORER** comme moteur (petit modèle) ; TA-RoPE explique pourquoi la synchro labiale dépend de l'alignement temporel des positions, utile pour diagnostiquer H3.

### 6.4 Kandinsky 6.0 Video — notre repli audio natif (MIT)
- *Kandinsky 6.0 Video: Foundation Models for Synchronized Video and Audio Generation* — Team Kandinsky (Kandinsky Lab) — 04/10/2026 — https://arxiv.org/abs/2610.05608
- **Idée** : Lite **3B** et Pro **29B** ; CrossDiT double flux ; audio **44 kHz** synchronisé **avec lip-sync** ; T2AV et I2AV ; super-résolution intégrée jusqu'à **1920×1080** ; SFT + RL + distillation.
- **[PUBLIÉ]** en évaluation humaine côte à côte, Pro « dépasse nettement » Kandinsky 5.0 Pro et reste « compétitif avec les meilleurs modèles audio-vidéo, surtout en qualité de parole ».
- **Code/licence** : kandinskylab/kandinsky-6, **MIT** (code, points de contrôle et intégration diffusers annoncés sous MIT).
- **[MON AVIS] — ADOPTER (lot 5) comme premier repli audio-vidéo**, sous réserve de la revue de provenance L5. Lite 3B est le seul modèle audio-vidéo natif qui a des chances de tenir sur la **RTX 5080 16 Go**.

### 6.5 DreamX-Creator (Alibaba AMAP) et NAVA (Baidu)
- **DreamX-Creator 1.0** (31/08/2026, https://arxiv.org/abs/2608.31106) : générateur **7B** audio-vidéo natif, attention croisée à portes ; raffinement **2K autorégressif en 1 étape** par bloc temporel. **Apache-2.0** (code).
- **NAVA** (Baidu, 28/05/2026, https://arxiv.org/abs/2605.30073) : MMDiT « Align-then-Fuse », **timbre de voix de référence** par plage de parole ; 6,3B. Dépôt **sans licence**.
- **[MON AVIS] — DreamX-Creator : SURVEILLER (candidat repli 7B Apache, à évaluer face à Ovi). NAVA : IGNORER** (pas de licence) ; noter que le **clonage de timbre** est une capacité à garde-fou AUP 13 (consentement vocal).

### 6.6 Foley (vidéo → audio) : MMAudio, HunyuanVideo-Foley, Kling-Foley, Foley-Omni
- **MMAudio** — Ho Kei Cheng et al. (UIUC, Sony AI) — 19/12/2024 — https://arxiv.org/abs/2412.15322 — **[PUBLIÉ]** **157 M** de paramètres, **1,23 s pour un clip de 8 s**, état de l'art ouvert en qualité, sémantique et synchronisation. **MIT**.
- **HunyuanVideo-Foley** (Tencent, 23/08/2025, https://arxiv.org/abs/2508.16930) : 100 K heures, alignement de représentation ; état de l'art annoncé. Licence `NOASSERTION` (licence communautaire Tencent, exclusions de territoires probables [À VÉRIFIER]).
- **Kling-Foley** (Kuaishou, 24/06/2025, https://arxiv.org/abs/2506.19774) : MMDiT + codec audio universel + rendu stéréo ; banc Kling-Audio-Eval ouvert ; poids non relevés.
- **Foley-Omni** (Nanjing U. et al., 02/06/2026, https://arxiv.org/abs/2606.03672) : bande-son **complète** (parole + effets + musique) conjointe ; banc V2ST-Bench.
- **[MON AVIS] — ADOPTER MMAudio MAINTENANT (lot 5)** comme capacité `v2a.foley` : minuscule, rapide, MIT, applicable à toute vidéo muette (Wan, Cosmos3, prises importées). HunyuanVideo-Foley : IGNORER tant que la licence territoriale n'est pas relue.

### 6.7 Lip-sync et doublage : LatentSync, InfiniteTalk
- **LatentSync** (ByteDance, 12/12/2024, https://arxiv.org/abs/2412.09262) : lip-sync par diffusion latente conditionnée par l'audio, TREPA pour la cohérence temporelle ; **[PUBLIÉ]** SyncNet porté de **91 % à 94 %** de précision sur HDTF. **Apache-2.0**.
- **InfiniteTalk** (MeiGen-AI, 19/08/2025, https://arxiv.org/abs/2508.14033) : **doublage à images clés éparses** — garde des images de référence (identité, gestes, caméra) et régénère tout le corps en synchronie avec l'audio, en flux pour des durées illimitées ; état de l'art annoncé sur HDTF, CelebV-HQ, EMTD. **Apache-2.0**, 8 212 étoiles.
- **[MON AVIS] — ADOPTER InfiniteTalk (lot 5) comme capacité `dub` / « faire parler » sur Wan, LatentSync comme correcteur léger de bouche (lot 6, post-production).** Garde-fous : consentement voix + visage, marquage « généré par IA ».

### 6.8 Soundwich — stems audio séparés
- *Soundwich: Video Generation with Layered and Controllable Audio* — Zhuo Ning, …, Daniel Cohen-Or (SFU, Tel Aviv U., …) — 30/09/2026 — https://arxiv.org/abs/2610.00691 — **sans entraînement** : un modèle audio-vidéo figé produit des **pistes séparées** (parole, musique, effets, ambiance) synchronisées, que l'on peut décaler, couper, remplacer. Code GitHub (licence non relevée).
- **[MON AVIS] — SURVEILLER, très aligné avec le montage (lot 6).** L'audio natif de H3 arrive en **une piste mixée** : impossible de baisser la musique sous un dialogue dans FreeCut. Si Soundwich s'applique à H3 (« modèle flow-matching audio-vidéo figé »), c'est un gain d'ergonomie majeur. En attendant : séparation de sources classique en post-production (outil à choisir au rapport 02).

### 6.9 Évaluation de H3 lui-même
- *Can MiniMax-H3 Reason About the Physical World? An Evaluation of Omni-Modal Generative Model* — Haoyu Zhao, …, Shuicheng Yan (NUS, Fudan, Tencent) — 16/09/2026 — https://arxiv.org/abs/2609.18323
- **[PUBLIÉ]** 517 cas multimodaux : réussite globale **41,97 %** ; raisonnement de décision à partir d'une vidéo **56,00 %** ; désambiguïsation par l'audio **27,40 %**. Jeu de données publié (HF `gulucaptain/MiniMax-H3-Reason`).
- **[MON AVIS] — À intégrer au lot 7.** H3 exploite mal une **entrée audio** pour comprendre la scène : l'AI Director ne doit pas compter sur « une référence audio » pour piloter le contenu visuel ; préférer texte + images de référence. Le jeu de données sert de test de non-régression lors des mises à jour de H3.

---

## Axe 7 — Agents réalisateurs, storyboard, script-to-video

### 7.1 ViMax (HKU) — référence la plus proche de notre AI Director
- *ViMax: Agentic Video Generation* — Lingxuan Huang, Sizhe He, Hengji Zhou, Liqiang Nie, Lianghao Xia, Chao Huang (HKU, SCUT, HIT Shenzhen) — 02/06/2026 (v2 21/07/2026) — https://arxiv.org/abs/2606.07649
- **Idée** : moteur narratif hiérarchique avec RAG, **graphe de dépendances visuelles** entre plans (portrait de personnage + « ancre » caméra parent-enfant), **vidéos de transition** entre positions de caméra pour en extraire des vues cohérentes, contrôle qualité par VLM sur les **images clés**.
- **[PUBLIÉ]** (ViMax-Bench, 35 histoires, 8-16 plans) : cohérence globale **0,5571** vs HoloCine 0,5272, AniMaker 0,5167, MovieAgent 0,4716. Ordonnancement : parallèle **310 s / GC 0,5085**, sériel **835 s / 0,5511**, graphe **405 s / 0,5571**. Sans sélection VLM : GC **−3,8 %** ; sans dépendances : **−8,7 %**. Best-of-k sur images clés : **k=2 → 0,5571 pour 17,50 $ et 405 s** ; k=3 → 0,5041 ; k=4 → 0,5194. Version Wan2.2 : GC 0,5320. Humains : victoire **60,5 %** vs HoloCine, **74,8 %** vs Veo 3.1 seul (35 histoires, 15 évaluateurs). Planification de roman : GPT-5.4 meilleur, Claude Sonnet 4.6 meilleur en qualité narrative locale mais plus faible en cohérence visuelle.
- **Code/licence** : HKUDS/ViMax, **MIT**, 12 805 étoiles, actif.
- **[MON AVIS] — ADOPTER les principes au lot 7 (déjà partiellement retenus).** (1) Deux candidats par plan, **au niveau image clé** (moins cher qu'en vidéo) ; (2) le plan de plans est un **graphe**, pas une liste : les plans indépendants se génèrent en parallèle sur 5090 + GB10, les dépendants attendent leur parent — ça colle à notre invalidation « périmé » des dépendants ; (3) « vidéo de transition » pour obtenir le contrechamp cohérent d'une même pièce. Attention : métrique ViCLIP maison, 35 histoires, aucune mesure d'identité visage.

### 7.2 MovieAgent (NUS Show Lab)
- *Automated Movie Generation via Multi-Agent CoT Planning* — Weijia Wu, Zeyu Zhu, Mike Zheng Shou (NUS) — 10/03/2025 — https://arxiv.org/abs/2503.07314 — rôles réalisateur, scénariste, storyboardiste, repéreur ; script + banque de personnages → film multi-scènes avec sous-titres. **[PUBLIÉ par tiers]** dernier des agents sur ViMax-Bench (GC 0,4716). Dépôt **sans licence**.
- **[MON AVIS] — IGNORER le code** (pas de licence) ; garder la **banque de personnages** comme entrée de premier rang (déjà dans notre lot 8).

### 7.3 FilmAgent (HIT Shenzhen, Tsinghua)
- *FilmAgent: A Multi-Agent Framework for End-to-End Film Automation in Virtual 3D Spaces* — Zhenran Xu, Longyue Wang, … — 22/01/2025 — https://arxiv.org/abs/2501.12909 — **[PUBLIÉ]** 15 idées, note humaine moyenne **3,98/5** ; un système multi-agents sous GPT-4o dépasse o1 seul. **MIT**.
- **[MON AVIS] — IGNORER comme système** (espaces 3D Unity, pas de génération vidéo) ; retenir le résultat « boucle de critique entre rôles > un seul gros modèle » pour justifier un rôle critique séparé au lot 7.

### 7.4 AniMaker — MCTS sur les clips + évaluateur dédié
- *AniMaker: Automated Multi-Agent Animated Storytelling with MCTS-Driven Clip Generation* — Haoyuan Shi, Yunxin Li, … (HIT, Alibaba) — 12/06/2025 — https://arxiv.org/abs/2506.10540 — agents Réalisateur / Photographie / Critique / Post-production ; **MCTS-Gen** explore l'espace des candidats ; **AniEval** évalue le multi-plans. **[PUBLIÉ par tiers]** GC 0,5167 sur ViMax-Bench. Code HITsz-TMG/Anim-Director (licence non relevée).
- **[MON AVIS] — PLUS TARD (lot 7+).** Le MCTS coûte cher en GPU ; ViMax montre que k=2 suffit. À garder pour un mode « Qualité maximale » facturé.

### 7.5 StoryAgent et Mora — précurseurs
- **StoryAgent** (MBZUAI, 07/11/2024, https://arxiv.org/abs/2411.04925) : histoire personnalisée, LoRA-BE pour la cohérence intra-plan.
- **Mora** (Zhengqing Yuan et al., 20/03/2024, https://arxiv.org/abs/2403.13248) : multi-agents « à la Sora », écart reconnu avec Sora. Code `lichao-sun/mora`.
- **[MON AVIS] — IGNORER** (historique).

### 7.6 Agents 2026 : StoryEngine, DramaAgent, CineForge, VideoGen-Agent, CineEvolve
- **StoryEngine** (Tencent, NUS, 27/09/2026, https://arxiv.org/abs/2609.33627) : sépare **plans sémantiques faisant autorité** et **observations visuelles non fiables** ; état d'entités explicite, état de début/fin de chaque plan, **boucle de réparation bornée**. Code GitHub (19 étoiles).
- **DramaAgent** (Peking U. et al., 08/09/2026, https://arxiv.org/abs/2610.00097) : couche de contrôle **indépendante du modèle** : planification, conditionnement persistant des personnages, synthèse par scène, **réparation ciblée** guidée par diagnostic (dérive d'identité, sémantique manquante, discontinuité, décalage audio-vidéo).
- **CineForge** (Tongji, Kuaishou, Fudan, 30/08/2026, https://arxiv.org/abs/2608.29621) : l'agent apprend de ses échecs **d'une histoire à l'autre** (correctifs locaux validés par rejeu) ; **[PUBLIÉ]** CineScope-Metric **4,024 → 4,380**.
- **VideoGen-Agent** (Princeton, Stanford, 21/09/2026, https://arxiv.org/abs/2609.24997) : agent entraîné par RL à utiliser des outils (augmentation, génération, vérification) ; **[PUBLIÉ]** VABench **56,5 → 75,6** (+19,1) au-dessus du générateur de base ; **86,1** en changeant d'outils sans réentraîner ; préféré dans **84,3 %** des comparaisons humaines.
- **CineEvolve** (BUPT, Peking U., Tencent, 21/10/2026, https://arxiv.org/abs/2610.29590) : Réalisateur et Critique dans une même politique VLM co-entraînée par RL ; jeu CineTraj 40 K.
- **Revue « Agentic Visual Generation »** (Fudan, Tongyi Wan, 06/09/2026, https://arxiv.org/abs/2609.06758) : échelle **L0 → L4** (L1 préparer l'entrée ; L2 choisir l'opération ; L3 changer d'opération après observation ; L4 apprendre des tâches passées).
- **[MON AVIS] — ADOPTER au lot 7 trois idées :** (a) **StoryEngine** : l'état du monde (qui porte quoi, où est l'objet) est la vérité, la vidéo n'est qu'une observation ; c'est ce qui permet de reprendre un seul plan sans réécrire l'histoire ; (b) **DramaAgent** : la réparation est **typée** (identité → regénérer avec référence renforcée ; décalage audio → reprendre l'audio seul), avec un **budget de réparations borné** inclus dans le devis ; (c) **VideoGen-Agent** : le gain vient surtout des **outils** (+9,5 points en changeant d'outils), donc investir dans le registre de capacités plutôt que dans un LLM planificateur entraîné. Selon l'échelle de la revue Fudan, notre Director v1 vise **L3** ; L4 (CineForge) plus tard, avec journal des échecs par recette.

---

## Axe 8 — Évaluation automatique et fiabilité mesurée

### 8.1 VBench et VBench-2.0
- **VBench** — Ziqi Huang et al. (NTU S-Lab, Shanghai AI Lab) — 29/11/2023 — https://arxiv.org/abs/2311.17982 — 16 dimensions « superficielles » (cohérence du sujet, fluidité, scintillement…). **Apache-2.0**.
- **VBench-2.0** — Dian Zheng, Ziqi Huang, … Ziwei Liu — 27/03/2025 — https://arxiv.org/abs/2503.21755 — 18 dimensions « intrinsèques » (fidélité humaine, contrôle, créativité, physique, sens commun), juges VLM/LLM + détecteur d'anomalies (Qwen2.5-VL-3B affiné). **[PUBLIÉ]** corrélation de Spearman avec les humains **0,817 à 0,995** selon la dimension — mais calculée sur les taux de victoire **au niveau modèle, avec 4 modèles** ; « intrigue complexe » ≤ **11,2 %** pour tous ; échec ~**80 %** sur changements simples d'attributs/positions.
- **[MON AVIS] — ADOPTER au lot 7 certaines dimensions VBench (1.0) comme contrôles déterministes** (cohérence du sujet DINO, du fond CLIP, scintillement, fluidité du mouvement), car elles sont calculables et stables. **Ne pas utiliser VBench-2.0 pour noter une prise individuelle** : une corrélation sur 4 points (modèles) ne dit rien de la fiabilité vidéo par vidéo.

### 8.2 VideoScore / VideoScore2 (TIGER-Lab)
- **VideoScore** (21/06/2024, https://arxiv.org/abs/2406.15252) ; **VideoScore2** (26/09/2025, https://arxiv.org/abs/2509.22799) — évaluateur multidimensionnel (qualité visuelle, alignement texte, cohérence physique) avec raisonnement ; 27 168 vidéos annotées ; SFT + GRPO. **[PUBLIÉ]** précision **44,35 %** (+5,94) sur VideoScore-Bench-v2, **50,37 %** de moyenne sur 4 bancs hors domaine. **MIT**.
- **[MON AVIS] — ADOPTER comme signal secondaire (lot 7)**, jamais comme décision : 44-50 % de précision signifie que l'outil se trompe environ une fois sur deux sur la note exacte. Utilisable pour **départager deux candidats** (classement relatif), pas pour rejeter une prise.

### 8.3 Artifact-Bench — les VLM voient mal les artefacts
- *Artifact-Bench: Evaluating MLLMs on Detecting and Assessing the Artifacts of AI-Generated Videos* — Yuqi Tang et al. (HKUST-GZ, Peking U., Kling, …) — 18/05/2026 — https://arxiv.org/abs/2605.18984
- **[PUBLIÉ]** 19 MLLM ; meilleur = **Gemini 3.1 Pro, score total 47,5** ; réel vs généré **74,0 %** ; comparaison de réalisme par paires **48,6 %** (tâche binaire, hasard ≈ 50 %) ; **identification fine des artefacts 9,8 %**. Désalignement notable avec les préférences humaines. Code : dépôt FrankYang-17/Artifact-Bench (licence non relevée).
- **[MON AVIS] — Confirme la règle de l'architecture §5.3.** Le juge VLM **ne doit pas** servir à détecter mains déformées, fusions d'objets ou scintillements : utiliser des détecteurs spécialisés et des contrôles déterministes ; réserver le VLM à « le plan montre-t-il ce que demande le prompt ? ».

### 8.4 VideoArgus et JudgeFit — rendre le juge VLM plus fiable
- **VideoArgus** (U. Rochester, 06/08/2026, https://arxiv.org/abs/2608.05485) : pour chaque entrée, une **rubrique spécifique** est générée une fois (sans voir les sorties), puis réutilisée pour noter tous les candidats via questions VLM + outils visuels. **[PUBLIÉ]** sur 1 260 vidéos, corrélations Spearman/Kendall **intra-entrée** avec les humains supérieures aux évaluateurs spécialisés, sur les 5 tâches ; classements stables entre VLM. Code et données publiés.
- **JudgeFit** (QMUL, Huawei, Imperial, 22/06/2026, https://arxiv.org/abs/2606.22918) : taxonomie d'erreurs **propre à chaque VLM**, calibrée sur des notes humaines ; **[PUBLIÉ]** **+32 %** d'amélioration relative moyenne sur 16 VLM.
- **[MON AVIS] — ADOPTER VideoArgus au lot 7, c'est la bonne forme pour notre juge.** Le plan de plans contient déjà la spécification du plan : en dériver **une rubrique par plan** (personnage X présent, action Y, cadrage Z) au moment de la planification, avant génération ; la même rubrique note les 2 candidats. La corrélation **intra-entrée** est exactement la mesure pertinente pour choisir entre deux prises. JudgeFit : calibrer notre VLM juge sur un petit jeu annoté par nous (lot 7, preuve de fin).

### 8.5 IsoVRBench — où les modèles de récompense échouent
- *IsoVRBench: Video Reward Modeling Without Human Feedback* — Shuyue Stella Li et al. (U. Washington, Meta) — 12/10/2026 — https://arxiv.org/abs/2610.17234
- **[PUBLIÉ]** 8 000 paires par intervention contrôlée (une seule propriété modifiée) : le meilleur modèle de récompense n'atteint que **60,8 %** sur des **images réordonnées** contre **100 %** pour les humains ; les classements sur les bancs existants ne prédisent pas cet échec.
- **[MON AVIS] — ADOPTER la méthode pour nos tests du juge (lot 7).** Générer nos propres paires « une seule chose cassée » (images inversées, visage remplacé, plan coupé trop tôt) et mesurer chaque juge dessus avant de lui confier une décision. Contrôle déterministe à ajouter : **ordre temporel** (flux optique cohérent), puisque les juges appris le ratent.

### 8.6 PhyProbe (NVIDIA) — score de physique calibré
- *PhyProbe: Rethinking Physical Consistency Evaluation in Generated Videos* — Max Ku et al. (NVIDIA, Waterloo, Vector) — 29/09/2026 — https://arxiv.org/abs/2609.38377 — encodeur spatio-temporel gelé + petite tête de score ; score de violation **[0,1] calibré** ; meilleur dans les cas « généré vs généré » où les évaluateurs affinés s'effondrent. Code GitHub (licence non relevée).
- **[MON AVIS] — SURVEILLER (lot 7+)** : un score calibré sur [0,1] permet un seuil de rejet automatique, ce que les VLM ne donnent pas.

### 8.7 Évaluation audio-vidéo : AVBench, VA-Judger, AVC-Reward
- **AVBench** (Tsinghua, CUHK, 23/05/2026, https://arxiv.org/abs/2605.24652) : 10 dimensions centrées humain (lip-sync, cohérence multi-niveaux), évaluateurs entraînés sur perturbations contrôlées, score continu dérivé de la confiance.
- **VA-Judger** (Shanghai Innovation Institute, 19/08/2026, https://arxiv.org/abs/2608.18607) : VAPref-10K (10,3 K comparaisons humaines) ; montre que combiner des métriques séparées (qualité audio + vidéo + synchro) encourage le **piratage de récompense**.
- **AVC-Reward** (ZJU, 15/10/2026, https://arxiv.org/abs/2610.22321) : cohérence audio-vidéo **par événement** (harmonie globale, synchro par événement, attributs).
- **[MON AVIS] — PLUS TARD (lot 7+)** : pour H3 (audio natif), le juge doit inclure au moins un contrôle de synchro (SyncNet sur les plans parlés, déterministe) ; AVC-Reward/AVBench seulement après évaluation de leurs licences.

### 8.8 Métriques d'identité
- Aucun article de 2025-2026 lu ici ne remplace les mesures classiques : similarité **ArcFace** (visage) et **DINO/CLIP** (sujet, produit), utilisées par HoloCine (DINO, CLIP, ViCLIP), Stand-In (similarité visage), MAGREF (ID-Sim, Subj-Sim, Bg-Sim). [MON AVIS] Les garder comme couche 2 de notre cascade ; un plan « produit » doit en plus être comparé à **plusieurs vues** de référence (OmniShowcase, 3.8) pour ne pas pénaliser un angle non montré.

---

## Axe 9 — Upscale et interpolation

### 9.1 SeedVR2 (ByteDance Seed) — restauration en une étape
- *SeedVR2: One-Step Video Restoration via Diffusion Adversarial Post-Training* — Jianyi Wang, Shanchuan Lin, … (ByteDance Seed) — 05/06/2025 — https://arxiv.org/abs/2506.05301
- **[PUBLIÉ]** une seule étape, qualité égale ou supérieure aux méthodes multi-étapes ; **limite déclarée** : le VAE causal prend **plus de 4×** le temps des VAE usuels et **plus de 95 % du temps total** pour une vidéo 720p de 100 images.
- **Code/licence** : ByteDance-Seed/SeedVR, **Apache-2.0** (poids [À VÉRIFIER]).
- **[MON AVIS] — PLUS TARD, profil « export Qualité » (lot 9)** ; trop lent pour l'aperçu.

### 9.2 FlashVSR et FlashVSR+ — super-résolution en flux
- **FlashVSR** — Junhao Zhuang et al. (Tsinghua, Shanghai AI Lab, CUHK, SJTU) — 14/10/2025 — https://arxiv.org/abs/2510.12747 — **[PUBLIÉ]** ~**17 images/s** en 768×1408 sur un A100, jusqu'à **12×** plus rapide que les VSR diffusion une étape antérieurs ; jeu VSR-120K. **Apache-2.0**.
- **FlashVSR+** — Ruchang Yao et al. (MMLab-CUHK) — 13/10/2026 — https://arxiv.org/abs/2610.17552 — **[PUBLIÉ]** attention hybride : DiT jusqu'à **2× plus rapide**, **−45 %** de mémoire de pointe, **4K sans tuilage sur une RTX 4090 24 Go** ; distillation alignée sur les préférences (Ry-DMD). **Apache-2.0**, code, modèles et données publiés.
- **[MON AVIS] — ADOPTER FlashVSR+ MAINTENANT (lot 6, post-production) comme capacité `upscale` par défaut.** Apache-2.0, tient sur 24 Go donc sur 5090 (32 Go) ; 4K sans tuilage évite les coutures. Permet aussi de générer en 720p et d'exporter en 1080p/4K, ce qui réduit le coût GPU des profils Rapide/Équilibré.

### 9.3 Autres VSR 2026 utiles
- **High-Throughput Generative VSR on a Single Consumer GPU** (Cyprus U. of Technology, 09/10/2026, https://arxiv.org/abs/2610.13179) : SR une étape sur **images clés** + **interpolateur à flot** entre elles ; **[PUBLIÉ]** jusqu'à ~**32 images/s en 720p sur RTX 4090** ; +44 % de vitesse en 4K par substitution d'attention ; échange explicite de fidélité contre vitesse.
- **[MON AVIS] — l'idée « SR des images clés + interpolation » est à retenir pour l'aperçu rapide** (lot 6) ; pas pour l'export final.

### 9.4 Interpolation : RIFE, LDF-VFI, SPEED
- **RIFE** — Zhewei Huang et al. (Megvii, Peking U.) — 12/11/2020 — https://arxiv.org/abs/2011.06294 — **[PUBLIÉ]** **4 à 27×** plus rapide que SuperSlomo/DAIN, meilleure qualité. **MIT**.
- **LDF-VFI** (SJTU, Fudan, 21/01/2026, https://arxiv.org/abs/2601.14959) : interpolation par DiT autorégressif sur toute la séquence, généralise jusqu'au **4K** ; code publié.
- **SPEED** (Fudan, Bilibili, 17/07/2026, https://arxiv.org/abs/2607.15585) : diffusion **pixel** en une étape ; **[PUBLIÉ]** SNU-FILM : LPIPS **−8,8 %**, **63,3 %** plus rapide, −10,6 % mémoire ; en 4K jusqu'à **−51,5 %** LPIPS vs méthodes antérieures.
- **[MON AVIS] — ADOPTER RIFE MAINTENANT (lot 6)** : 16→24/30 i/s et ralentis, MIT, quasi gratuit en calcul. SPEED/LDF-VFI : SURVEILLER pour les grands mouvements où RIFE produit des fantômes.

---

## 10. Synthèse — les 10 techniques à plus fort impact pour Nexora Creative

Classement par impact sur le produit (vitesse perçue × qualité × coût GPU × risque juridique faible). Tout est **[MON AVIS]**, fondé sur les chiffres **[PUBLIÉ]** ci-dessus, non reproduits.

| Rang | Technique | Pourquoi | Preuve publiée la plus forte | Lot |
|---|---|---|---|---|
| 1 | **Distillation peu d'étapes packagée** (FastH3 / PDMD pour H3 ; TurboDiffusion = rCM + SLA + W8A8 pour Wan 2.2) | Premier levier de coût et de temps d'attente ; rend le parcours débutant viable | rCM 15-50× en 1-4 étapes ; TurboDiffusion 100-200× sur RTX 5090 ; PDMD meilleur 4 NFE sur H3 (visuel 83,17, 6/6 audio) | **3** (H3), **5** (Wan) ; spike S3 au **0** |
| 2 | **Basse précision par matériel** (NVFP4/FP8 + SageAttention2/3), déclarée dans le manifeste avec `requires_sm` | Mémoire (H3 BF16 ≈ 142 Go) et vitesse ; doit être sûr sur GB10 sm_121 | SageAttention3 5× sur 5090 ; W4A4 Wan2.2 −59 % mémoire pour −0,9 % VBench ; calibrer sur l'élève distillé | **1** (champ manifeste), **3** (5090/GB10) |
| 3 | **Juge à rubrique par plan** (VideoArgus) dans la cascade déterministe → identité → VLM, **testé par paires « une seule chose cassée »** (IsoVRBench) | Décide quelle prise montrer ; un juge non fiable coûte des régénérations et de la confiance | VLM : 9,8 % en identification d'artefacts (Artifact-Bench) ; RM 60,8 % vs humains 100 % sur ordre temporel ; VideoArgus meilleure corrélation intra-entrée | **7** |
| 4 | **Plan de plans en graphe + 2 candidats en image clé + état du monde explicite** (ViMax + StoryEngine + réparation typée bornée de DramaAgent) | Cohérence multi-plans et reprise d'un seul plan sans tout refaire ; parallélisme sur nos 3 GPU | ViMax : k=2 optimal (0,5571 vs 0,5041 à k=3), dépendances −8,7 % si retirées, 405 s vs 835 s en sériel | **7** |
| 5 | **Identité légère + multi-références sur Wan** (Stand-In par défaut, Lynx en 2e candidat, MAGREF/Phantom pour produits et groupes) | Cœur de l'offre type Higgsfield (personnages, produits) hors territoire H3 | Stand-In 0,724 vs Phantom 0,519 en similarité visage, 1 % de paramètres ; MAGREF ID-Sim 0,595 vs VACE 0,345 | **5** (recettes), **8** (bibliothèque) |
| 6 | **Post-production générative légère** : FlashVSR+ (upscale 4K), RIFE (fréquence d'images), MMAudio (foley pour les moteurs muets) | Générer petit et exporter grand ; donner du son à Wan/Cosmos ; tout est Apache/MIT | FlashVSR+ 4K non tuilé sur 24 Go, 2× DiT ; RIFE 4-27× ; MMAudio 1,23 s pour 8 s, 157 M | **6** (MMAudio dès le **5**) |
| 7 | **Format de prompt hiérarchique multi-plans** (global + par plan + `[shot cut]`, HoloCine) dans le plan de plans | Gratuit, compatible avec tous les moteurs, prépare l'arrivée des modèles multi-plans | HoloCine SCA 0,98 vs 0,48 pour Wan2.2 seul | **7** (format), **9** (moteur multi-plans) |
| 8 | **Contrôle caméra par preset compilé en trajectoire Plücker** : Uni3C sur Wan ; méthode sans entraînement (Oxford « Probing », WorldForge V2) à tester sur H3 ; ReCamMaster pour re-filmer | Le langage caméra est un argument central des studios type Higgsfield ; H3 n'a pas de module caméra ouvert | ReCamMaster FVD 122,7 vs 159,6 (DaS) ; Uni3C coût +17-23 % | **4** (presets UI), **5** (Uni3C), spike H3 après **5**, **9** (re-filmage) |
| 9 | **Remplacement/transfert de mouvement et doublage** : Wan-Animate (avec LoRA relighting), InfiniteTalk, LatentSync | Fonctions « effets » à forte valeur perçue, licences Apache, base Wan | Wan-Animate meilleur sur ses 3 métriques et préféré à Act-Two ; LatentSync SyncNet 91→94 % | **5** (capacités `replace`, `motion-transfer`, `dub`), garde-fous **8** |
| 10 | **Accélération du VAE et génération deux résolutions** (LightVAE sur H3, schéma Sol-H3 latent→latent, FlashDecoder) | Le décodage devient le goulot une fois le débruitage distillé ; clé pour GB10 | LightVAE ×2,97 décodage H3 à 99,51 % VBench-2.0 ; Sol-H3 < 1 min sur un DGX Spark ; SeedVR2 : VAE >95 % du temps | **3/9** — bloqué par licences (LightVAE sans licence, Sol-H3 sans licence) : demande de licence au lot **0** |

### Ce que je recommande de ne PAS faire maintenant
- Entraîner ou distiller nous-mêmes (rCM, DMD, Self-Forcing, Identity-GRPO) : on consomme des poids publiés.
- Brancher un cache (TeaCache/MagCache/TaylorSeer) sur un modèle 4-8 étapes : DisCa et le rapport 04 montrent la perte de qualité ; cache seulement sur le profil Qualité multi-étapes.
- Utiliser un juge VLM seul pour rejeter une prise, ou VBench-2.0 pour noter une prise individuelle.
- Intégrer du code sans licence (LightVAE, MovieAgent, NAVA) ou à licence maison non relue (HoloCine, SkyReels-V2/A2, HunyuanVideo-Foley, TrajectoryCrafter, DMD2) ; ni rien sur base LTX (MSR, raffineur Sol-H3).
- Mettre la génération holistique de scène (HoloCine) dans le parcours débutant : elle casse la reprise d'un seul plan.

### Spikes proposés (à ajouter à la liste S1-S10 du rapport 04, sans rien lancer sans accord)
1. TurboDiffusion Wan2.2-I2V sur 5090 et GB10 : temps froid/chaud, pic mémoire, qualité vs référence 40 pas.
2. SageAttention3 FP4 et noyaux NVFP4 sur GB10 (sm_121) : fonctionne / repli FP8.
3. Juge : 50 paires « une seule chose cassée » (IsoVRBench) × {VLM généraliste, VideoScore2, ArcFace/DINO, contrôles déterministes} → taux de détection par juge.
4. Caméra sans entraînement (méthode « Probing ») sur H3, 3 presets : erreur de pose et dégradation de qualité.
5. Stand-In vs Lynx sur 10 identités consenties : similarité ArcFace et préférence humaine interne.

## 11. Ce qui n'est pas fait
- Aucune reproduction, aucune mesure ; les chiffres sont ceux des auteurs, sur leurs bancs.
- Licences des **poids** non relues pour aucun article ; licences de code relevées par l'API GitHub uniquement.
- Plusieurs articles d'octobre 2026 lus au niveau du résumé seulement (CineMem, Mise-en-Video, Triage, AB-Attention, RECAP, REEL, Attn-Forcing, Memory Forcing, etc. repérés mais non retenus faute de code ou de chiffres).
- Les chiffres Ovi (taux de victoire) et UniVerse-1 n'ont pas été relevés dans le corps de l'article.
