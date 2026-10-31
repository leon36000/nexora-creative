# 03 — Modèles vidéo ouverts, licences, MiniMax H3 et optimisations

Nexora Creative — recherche du 30 octobre 2026. Parc GPU visé : RTX 5090 (32 Go), DGX Spark GB10 (128 Go unifiés, sm_121, aarch64), RTX 5080 (16 Go).

Légende des étiquettes de fiabilité utilisées partout :
- **[MESURÉ publié: source]** : chiffre mesuré et publié par un tiers ou l'éditeur, avec protocole visible. Les mesures de blogueurs individuels sont marquées « tiers, non reproduit ».
- **[ANNONCÉ: source]** : chiffre communiqué par l'éditeur ou un vendeur sans protocole reproductible, ou page non relue en détail.
- **[ESTIMÉ]** : extrapolation de ma part. À valider par un banc d'essai interne.
- **(s-a)** : information collectée par un sous-agent de recherche dont la source est secondaire (résumé de page). À recouper avant décision.

Aucun poids n'a été téléchargé, rien n'a été installé, aucun compte n'a été créé. Les licences ont été lues dans les fichiers LICENSE bruts quand c'était possible. Pour des raisons de droit d'auteur, les clauses sont **paraphrasées de près avec numéro de section et URL**, sauf une citation courte. Les juristes de Nexora doivent relire le texte original (liens fournis).

---

## 0. Conclusions clés (à lire en premier)

1. **MiniMax H3 est le meilleur modèle à poids ouverts du marché au 30 oct. 2026** : 3e de l'arène Artificial Analysis texte-vers-vidéo avec audio (Elo 1161, plage de rang 2 à 6), seul modèle à poids ouverts du haut de tableau. Le suivant en poids ouverts, LTX-2.5, est à 947 Elo, soit un écart de plus de 200 points. [MESURÉ publié: artificialanalysis.ai/video/leaderboard/text-to-video?open-weights=true, relu le 30 oct. 2026, page « Updated » sans date]
2. **Blocage juridique majeur : la licence H3 exclut les États-Unis, l'UE, le Royaume-Uni et la Corée du Sud, et interdit aussi d'utiliser les sorties (« Outputs ») hors territoire.** Le Canada est dans le territoire autorisé. Mais un SaaS Nexora ne peut pas servir des clients américains ou européens avec des vidéos produites par les poids locaux de H3. Il faut du **geofencing par utilisateur** ou un repli sur l'API MiniMax (dont les conditions n'ont pas été lues). Voir section 1.4.
3. **H3 n'est pas « tout ouvert »** : le module de reformulation de contexte (H3-Context-IR) et le module de régénération 2K (H3-Regenerate-2K) sont **hébergés seulement** (API MiniMax). Localement on obtient du 768p. Le 2K local exige un upscaler tiers (SeedVR2, SPAN, etc.) ou l'API.
4. **Poids énormes en natif** : environ 142 Go par point de contrôle en BF16 (DiT 66 Go + encodeur Qwen3-VL-32B 65 Go + VAE vidéo 10 Go). Il faut obligatoirement des versions élaguées (suppression des branches AdaLN) et quantifiées (NVFP4, INT8 ConvRot, FP8, GGUF) pour la 5090 et le Spark. La 5080 (16 Go) est limite : aucune mesure publiée.
5. **Sur 5090, le gain réel vient surtout des LoRA/modèles distillés (4 à 8 étapes) et de la quantification**, pas du Spark. Meilleurs chiffres mesurés : 1344×768, 5 s avec audio, **41,5 s à chaud** avec LoRA Turbo 4 étapes (51,5 s à froid) ; FastH3 V2 8 étapes **51 à 60 s** dans ComfyUI ; H3 de base 20 étapes **166 à 168 s**. [MESURÉ publié, tiers non reproduit: ai-muninn.com, voir section 2]
6. **Le DGX Spark est 2,4 à 5,5 fois plus lent que la 5090** pour H3 (bande passante 273 Go/s contre environ 1,8 To/s). Son atout est la mémoire (pas d'OOM, plusieurs modèles résidents). Annonce NVIDIA : 56 s pour 5 s en 768p avec un pipeline à deux étages (brouillon H3 384p + raffinage LTX-2.5). Ce chiffre n'est reproduit qu'à 66 à 73 s par un tiers. **Le raffinage LTX-2.5 pose une zone grise de licence** (section 3.2).
7. **Les contre-exemples existent** : le 4 étapes n'est pas automatiquement plus rapide ni meilleur (artefacts de traînée en mouvement rapide, preview T2V seulement, 8 étapes jugées meilleures par l'éditeur lui-même), la sparse attention VSA n'apporte presque rien à 480p ou à 5 s, le cache de blocs coûte de la qualité (SSIM 0,88). Voir section 2.4.
8. **Alternatives à licence propre** (sans territoire ni seuil) : Wan 2.2 et dérivés (Apache-2.0), Kandinsky 6.0 (MIT, audio natif, sorti sept.-oct. 2026), Cosmos3 (OpenMDW). Plus restreints : LTX-2.5 (seuil 10 M$ d'entité + interdiction de produit concurrent), HunyuanVideo 1.5 (exclut UE/UK/Corée, 100 M d'utilisateurs actifs mensuels).
9. **Les modèles Wan 2.5, 2.6, 2.7 et 3.0 sont API seulement** (aucun poids ouvert au-delà de Wan 2.2 et de ses dérivés Animate-2 et Dancer). Wan 3.0 est 1er de l'arène (1175 Elo) mais n'est pas auto-hébergeable.
10. **Les étiquettes de licence des dérivés communautaires ne sont pas fiables.** Exemple : la LoRA Turbo de larryvrh est étiquetée `apache-2.0` sur HF, alors qu'elle est un dérivé par distillation de H3, donc un « Model Derivative » soumis à la licence H3 (définition I.11). À traiter comme H3.

---

## 1. MiniMax H3

### 1.1 Fiche technique

Sources : README HF https://huggingface.co/MiniMaxAI/MiniMax-H3 (relu en entier) ; arbre de fichiers via l'API HF ; LICENSE https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE (relu en entier) ; Q&R licence https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/QA-about-License.md.

| Élément | Valeur |
|---|---|
| Date de licence/sortie | 2 août 2026 (licence) ; page HF mise à jour le 13 août 2026 |
| Transformeur « H3-Omni-Transformer » | 33 milliards de paramètres, dense, flux unique. Environ 13 Md de paramètres résident dans les branches AdaLN (conditionnement temporel/modalité). Les sorties AdaLN peuvent être précalculées et mises en cache, donc ces paramètres n'ont pas besoin d'être chargés pour l'inférence seule |
| Encodeur de texte/vision | Qwen3-VL-32B complet (licence Apache-2.0, mentionné dans la licence H3). Les états cachés de la couche 50 sont donnés au DiT, d'où des versions « rognées à 50 couches » dans l'écosystème |
| VAE vidéo | Causal, compression spatiale 16×, temporelle 4×, 24 canaux (f16t4d24), puis patch 1×2×2, soit 32× spatial effectif. Décodeur ViT. Fichier de 10,4 Go |
| VAE audio | 32 kHz stéréo, canaux traités indépendamment, 40 Hz de jetons. Fichier de 0,6 Go |
| Têtes d'attention | 56 (le nombre de GPU en parallélisme de séquence doit diviser 56) |
| Poids publiés | Deux points de contrôle BF16 **distillés pour le CFG** : FL2VA (texte, première et/ou dernière image) et Ref2VA (références omni). Format original + format diffusers côte à côte |
| Attention parcimonieuse | Entraînée en fin de pré-entraînement mais **non publiée** ; la version ouverte n'a que l'attention complète. « Sera publiée plus tard » (README) |
| Durée de sortie | 4 à 15 s, 24 fps |
| Grille d'images | 124 + 17·n images (124 = 5 s ; 243 = 10 s ; 345 ou 362 = environ 14,4 à 15 s ; confirmé par les exemples FastH3/SGLang) |
| Résolution | Côté court 768 px par défaut (exemples 1344×768, 16:9). 21:9, 16:9, 4:3, 1:1, 3:4, 9:16. **2K : uniquement via H3-Regenerate-2K, non ouvert** |
| Audio | 32 kHz stéréo natif, 11 langues de dialogue stables (arabe, chinois, anglais, français, allemand, italien, japonais, coréen, portugais, russe, espagnol) |
| Références (Ref2VA) | ≤ 9 images, ≤ 3 vidéos (2 à 15 s chacune, 15 s au total), ≤ 3 audios (2 à 15 s, 15 s au total), 12 fichiers au maximum |
| Format de prompt | Prompt structuré : `integrated_multimodal_description`, `overall_soundscape`, `non_diegetic_music` ; dialogues dans `<d>[Langue] texte</d>` ; en Ref2VA, balises `<Picture 1>`, `<Video 1>`, `<Audio 1>`, `<Subject 1>`. Les prompts réels produits par Context-IR font de 2 900 à 33 000 jetons (exemples du README). **Longueur maximale non documentée** |
| Modules hébergés seulement | **H3-Context-IR** (réécriture/orchestration du contexte, « fortement recommandé » par l'éditeur) et **H3-Regenerate-2K**. Des guides de prompts (`docs/VIDEO_PROMPT_WRITING_GUIDE_*.md`) et des « skills » permettent de reconstruire un réécrivain de prompts maison |
| Cadres d'exécution officiels | SGLang, vLLM, diffusers (ModularPipeline), ComfyUI (support natif) |

Capacités : T2V, I2V (première ou dernière image), première+dernière image, V2V (édition de vidéo source avec références, exemple « video editing + audio reference + audio reuse »), audio vers audio-vidéo, voix de référence (timbre), références multi-sujets, audio stéréo synchronisé, dialogues multilingues, plans multiples dans un seul prompt (« [Shot 1] … [Shot 2] At 00:04.500 … »). Le contrôle de caméra se fait par le texte du prompt (pas de module dédié). Des LoRA communautaires existent (échange de personnage, orbite 360°, etc.), non évaluées ici.

### 1.2 Poids, formats et mémoire

Tailles du dépôt officiel (somme des fichiers HF, FL2VA ; Ref2VA est identique) :

| Composant | Taille |
|---|---|
| Transformeur BF16 (format original) | environ 66,3 Go (13 fragments) |
| Transformeur BF16 (format diffusers) | environ 64,7 Go (14 fragments) |
| Encodeur de texte Qwen3-VL-32B | environ 64,7 Go (14 fragments) |
| VAE vidéo | 10,4 Go |
| VAE audio | 0,6 Go |
| **Total par point de contrôle** | **environ 142 Go** |

Dans l'écosystème ComfyUI (tailles en GiB, [MESURÉ publié, tiers: ai-muninn.com/en/blog/minimax-h3-nvfp4-rtx5090]) : DiT complet 61,73 GiB ; encodeur 47,97 GiB ; VAE vidéo 4,85 GiB ; VAE audio 0,56 GiB ; total environ 115 GiB. Versions quantifiées utilisées : DiT NVFP4 élagué 11,67 GiB, encodeur NVFP4-AWQ 14,61 GiB, total **31,69 GiB**.

| Format | Taille rapportée | Notes |
|---|---|---|
| FP8 (élagué, mis à l'échelle) | 19,52 GiB | Pris en charge par ComfyUI ; sur GB10 c'est le chemin qui fonctionne [MESURÉ, tiers: github.com/joeynyc/MiniMax-H3-DGX-Spark] |
| FP8 E4M3FN complet | 43,78 GiB | |
| INT8 ConvRot (élagué) | 19,53 GiB | Environ 10 % plus rapide que FP8 sur 5090/5080 selon un testeur (xhinker, Medium) ; **échoue sur GB10 : « unsupported SM121 kernel »** [MESURÉ, tiers: joeynyc] |
| INT8 ConvRot (complet) | 31,70 GiB | |
| NVFP4 (élagué) | 11,67 GiB (Abiray) ; 12,5 Go (lilcheaty) ; 18,69 GiB (rockerBOO, plus fidèle) | Accélération native seulement sur Blackwell. Sur pré-Blackwell les poids sont dé-quantifiés avant le produit matriciel |
| GGUF | IQ1_S 3,78 GiB (qualité nettement dégradée) ; Q2_K élagué 6,26 GiB ; Q4_K_M élagué 10,64 GiB (18,50 GiB non élagué) ; Q8_0 33,56 GiB | ComfyUI-GGUF fonctionne, mais les créateurs de ComfyUI le déconseillent avec leur gestion dynamique de la VRAM (fil Reddit) |
| NF4 (DiffSynth) | 15,98 GiB | |
| Élagage AdaLN (« pruned ») | environ 40 % plus petit | Réduit la RAM système et le disque, mais **pas la VRAM de pointe sur 5090** : 31,7 à 31,8 Go de pic dans les 3 variantes testées (INT8 complet, FP8 élagué, INT8 élagué), la RAM de pointe passant de 93,1 GiB à 71,2 GiB [MESURÉ, tiers: wan2-7.io/blog/minimax-h3-local-requirements, 36 passes] |

Conséquence pour l'hôte : **prévoir au moins 96 à 128 Go de RAM système** pour la 5090 (71 à 93 GiB de pic sous ComfyUI). Le cookbook SGLang liste « 2× RTX 5090 TP2 + délestage par couche, hôte de classe 384 Go (377 Gio testés) » [MESURÉ éditeur: docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3].

Mémoire sur GB10 : chargement du modèle 89,17 GiB (FP8 en ligne), démarrage à froid d'environ 9 minutes (519 à 543 s) ; BF16 « a manqué de marge de mémoire unifiée » ; il faut au moins 110 GiB disponibles avant le lancement [MESURÉ, tiers: github.com/joeynyc/MiniMax-H3-DGX-Spark].

### 1.3 Autres blogs consultés
Le blog de l'éditeur (minimax.io/blog/minimax-h3), les billets RunPod, Sogni et Oxen n'ont pas été relus en détail : leurs informations techniques recoupent le README HF, déjà lu en entier. Les tarifs API sont dans la section 3.4.

### 1.4 Licence exacte : MiniMax H3 Community License Agreement

Fichier lu en entier : https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE (17 604 octets, date 2 août 2026). Le même texte est repris par les dérivés FastH3 (HF `FastVideo/...`, étiquette `license: other`, renvoi au fichier LICENSE de H3). Le preneur de licence est « Nanonoble Pte. Ltd. » (« MiniMax »).

**Clauses importantes (paraphrase de près, avec numéro de section) :**

| Réf. | Contenu | Effet pour un SaaS Nexora au Canada |
|---|---|---|
| Préambule | La portée est « expressément limitée » au Territoire applicable. L'acceptation résulte de tout usage, y compris via des services hébergés (« Hosted Services ») | Servir H3 à des clients = usage soumis à la licence |
| I.3 et I.5 | « Territoire applicable » = monde entier, sauf les « Territoires exclus » : **Union européenne, Royaume-Uni, République de Corée, États-Unis d'Amérique** | **Le Canada est inclus** |
| I.11 | « Model Derivatives » : toute modification, tout travail basé sur H3, et **tout autre modèle créé en transférant les motifs des poids, paramètres, modes opératoires ou sorties de H3 vers un autre modèle**, notamment par distillation, représentations intermédiaires ou entraînement sur sorties synthétiques. Les sorties elles-mêmes ne sont pas des dérivés | Les LoRA Turbo, FastH3, QAD, GGUF, NVFP4 sont des dérivés : même licence |
| II | Licence non exclusive, non transférable, libre de redevance, limitée au Territoire applicable : utiliser, reproduire, distribuer, créer des dérivés, modifier. Pour les territoires exclus, il faut demander une licence à MiniMax (formulaire : https://platform.minimax.io/h3-license) | |
| III | Redistribution permise à des tiers **dans** le Territoire : fournir une copie de l'accord, marquer les fichiers modifiés, fichier NOTICE obligatoire pour toute distribution **hors services hébergés**. « Encouragé » (non obligatoire) : afficher « Powered by MiniMax H3 », marquer les fichiers comme générés par IA, publier un billet technique | Un SaaS pur n'a pas à joindre de NOTICE (III.4 exclut les services hébergés) |
| III (dernier §) | Interdiction d'imposer des conditions additionnelles ou différentes aux dérivés, sauf III et V | Limite le « verrouillage » des LoRA/fine-tunes vendus |
| **IV.1** | **Autorisation écrite préalable de MiniMax (api@minimax.io, objet imposé) si les produits/services commerciaux génèrent plus de 20 M$ US de revenu annuel** (ou équivalent) | Seuil à surveiller. Non défini : la base de calcul (revenu de l'entité, du groupe, du produit) est ambiguë |
| **IV.2** | **Afficher en évidence « MiniMax H3 » dans l'interface utilisateur** du produit/service commercial qui utilise H3 ou ses dérivés | **Obligation ferme** pour l'interface Nexora (au moins sur les fonctions H3) |
| V.1 | Respect des lois (y compris commerce) et de l'AUP (Annexe A) | |
| **V.2** | Avant de donner accès aux œuvres H3 ou à un produit/service qui les incorpore, **lier chaque destinataire/utilisateur à des conditions exécutoires au moins aussi protectrices que la section V et l'Annexe A, et l'informer de ces restrictions** | Les CGU Nexora doivent reprendre l'AUP H3 (flow-down) |
| **V.3** | Interdit d'utiliser les œuvres H3 **ou leurs sorties** pour **améliorer tout autre modèle d'IA** (autre que H3 et ses dérivés) | **Interdit d'entraîner/affiner/distiller d'autres modèles avec des sorties H3**. Zone grise pour un raffineur tiers (LTX) et pour des upscalers appris sur latents H3 |
| **V.4** | Interdit d'utiliser, reproduire, modifier, distribuer **ou afficher les œuvres H3 ou leurs sorties outside the Applicable Territory** (citation courte) | **Les vidéos produites par les poids locaux ne peuvent pas être utilisées/affichées chez un client situé aux États-Unis, dans l'UE, au R.-U. ou en Corée.** Interprétation stricte : même un client canadien qui diffuse ensuite aux États-Unis serait problématique |
| **V.5** | Si on fournit à des tiers un produit/service/service hébergé qui permet de générer des sorties avec H3 : **garde-fous techniques et organisationnels raisonnables et proportionnés, testés et revus périodiquement**, contre les usages et sorties qui violent la section V ou l'AUP (y compris atteintes à la propriété intellectuelle de tiers) ; ne pas les désactiver ; **mécanisme de signalement accessible** ; enquête rapide et retrait/suspension (récidivistes) | Obligation de modération, de signalement, de suspension. Cohérent avec un studio, mais à documenter |
| VI.1 | L'utilisateur possède ses dérivés et modifications | |
| VI.2 | Licence de marque « MiniMax H3 » limitée à la conformité avec III.3 (affichage « Powered by ») | |
| VI.3 | **Résiliation des licences si l'on poursuit MiniMax ou un tiers en alléguant que les matériaux ou sorties violent des droits.** **Obligation de défendre et d'indemniser MiniMax** contre toute réclamation de tiers liée à l'usage ou à la distribution des œuvres H3 par soi-même ou par tout tiers | Indemnisation illimitée en faveur de MiniMax : risque financier à faire valider |
| VI.4 | MiniMax ne revendique aucun droit sur les sorties ; l'utilisateur et ses utilisateurs en sont responsables | Bon pour la propriété des sorties |
| VII | Aucune obligation de support/mise à jour ; garanties exclues ; responsabilité de MiniMax exclue | |
| VIII | Résiliation possible par MiniMax en cas de manquement : cessation immédiate, destruction des copies, notification des destinataires aval | Risque de « arrêt brutal » du service |
| IX | **Droit de Hong Kong (RAS)**, tribunaux de Hong Kong à compétence exclusive ; CVIM exclue | À évaluer avec un juriste québécois (consommateurs, contrats d'adhésion) |
| Annexe A (AUP), 20 points | Entre autres : 1 usage hors territoire ; 5 contourner les garde-fous ; 6 exploitation de mineurs ; 7 fausse information visant à nuire/influencer des élections ; 8 faux avis ; 12 diffuser du contenu dans un environnement public sans indiquer clairement qu'il est généré par machine ; **13 usurper l'identité d'une personne sans son consentement ou droit légal** ; 14 décisions automatisées à haut risque ; 15 violer les normes sociales/éthiques d'autres pays ; **19 usage militaire** ; 20 activité professionnelle non autorisée. MiniMax peut mettre à jour l'AUP **unilatéralement** (dernière révision : 2 août 2026) | La fonction « personnage/visage » d'un studio de type Higgsfield doit exiger un consentement vérifié. L'AUP est modifiable sans préavis : suivi de version nécessaire |

**Compatibilité avec un SaaS Nexora au Canada (analyse non juridique) :**
- **Faisable** pour des clients situés au Canada (et dans le reste du monde hors 4 territoires). L'hébergement SaaS est expressément visé (« Hosted Services ») et ne déclenche ni fichier NOTICE, ni obligation de publier.
- **Obligations à intégrer au produit** : mention « MiniMax H3 » visible dans l'interface (IV.2) ; CGU en cascade (V.2) ; modération + signalement + suspension (V.5) ; filigrane/mention « généré par IA » (fortement indiqué par l'AUP point 12 et l'encouragement III.3.b) ; registre de conformité.
- **Blocage client** : un client américain ou européen ne peut pas recevoir de sorties issues des poids locaux (V.4 + AUP 1). Il faut donc (a) **géolocaliser/attribuer le territoire de chaque compte** et refuser ou router vers un autre modèle (Wan 2.2, Kandinsky 6, Cosmos3) pour ces comptes ; (b) ou obtenir une licence séparée de MiniMax pour les territoires exclus (formulaire public, pas de garantie) ; (c) ou utiliser l'**API MiniMax hébergée**, disponible mondialement d'après la Q&R de la licence (« API: Globally available »). Les conditions de l'API n'ont pas été lues ici.
- **Zones grises à faire trancher par écrit par MiniMax** : (1) définition du revenu pour le seuil de 20 M$ ; (2) client canadien qui publie ensuite aux États-Unis ; (3) pipeline à deux étages avec raffineur LTX-2.5 et adaptateur de latents appris (V.3 « améliorer un autre modèle » + clause 18 de LTX) ; (4) LoRA communautaires étiquetées Apache mais dérivées de H3 ; (5) Context-IR via l'API pour des utilisateurs situés dans un territoire exclus.
- **Ne jamais** utiliser des sorties de H3 pour entraîner un modèle maison (V.3) ni constituer un jeu de données synthétique à partir de H3.

---

## 2. Optimisations de H3

### 2.1 Tableau des leviers

| Levier | Ce que c'est | Gain rapporté | Statut | Notes / limites |
|---|---|---|---|---|
| Élagage AdaLN | Précalculer les sorties AdaLN et ne pas charger ~13 Md de paramètres | Fichiers -40 % ; RAM de pointe 93,1 → 71,2 GiB | [MESURÉ, tiers: wan2-7.io] | Peu d'effet sur la VRAM de pointe en ComfyUI (31,7 Go). Le calendrier de pas devient figé (les tables AdaLN FastH3 ne couvrent que le calendrier livré) |
| Quantification FP8/INT8 ConvRot | Poids 8 bits | INT8 environ 10 % plus rapide que FP8 (5090/5080) | [MESURÉ, tiers: Medium xhinker] | INT8 non pris en charge sur sm_121 (GB10). FP8 en ligne fonctionne |
| NVFP4 | Poids 4 bits Blackwell | 175 s contre 185 s pour INT8 ConvRot (-5 %, dont l'auteur attribue la moitié à l'horloge GPU) ; VRAM de pointe 26 914 MiB contre 28 581 MiB ; -12,4 % de temps de pas et -8 Go selon lilcheaty | [MESURÉ, tiers: ai-muninn.com ; HF lilcheaty/MiniMax-H3-NVFP4] | Gain surtout mémoire. Le cookbook SGLang précise que l'exécution NVFP4 exige une capacité de calcul ≥ 10.0 ; **GB10 est 12.1** (à tester). Qualité 4 bits : SSIM vs BF16 de 0,785 (QAD FastH3 Omni, un clip 480p) |
| GGUF (Q2 à Q8) | Quantification par blocs | Tailles de 3,8 à 33,6 GiB | [ANNONCÉ] | Qualité nettement dégradée à IQ1/Q2. Intégration ComfyUI moins bonne |
| LoRA Turbo (lightx2v / larryvrh / MiniMax) | Distillation en 4 à 8 étapes, via LoRA de ~744 Mo | « ~5× d'accélération d'échantillonnage » ; 480×864, 5 s sur 5090 : 20 étapes 3:23 contre Turbo 8 étapes 1:21 (GGUF) ; 1344×768 natif Turbo 4 étapes : 41,5 s à chaud | [ANNONCÉ: HF larryvrh] ; [MESURÉ, tiers: kombitz.com ; ai-muninn.com] | Version v4 : traînées (« motion smear ») à 4 étapes en mouvement rapide ; l'auteur recommande 6 à 8 étapes et ne pas dépasser 8. Audio « encore en amélioration ». « Préversion ». **Dérivé de H3 : licence H3** |
| FastH3 Preview v1 (4 étapes, VSA 90 %) | Distillation DMD2 « sans données » + attention parcimonieuse VSA | Annonce : 15 s 768p en moins de 13 s sur 8×B200 ; jusqu'à 14× sur un seul GPU Blackwell | [ANNONCÉ: haoailab.com/blogs/fasth3-preview, mesures FastVideo sur B200] | **T2V seulement** (FL2VA et Ref2VA non distillés). Qualité « peut rester sous H3 de base » (mouvement difficile, détails fins, audio). Exige le noyau VSA-H3 (sm100a pour B200 ; repli Triton ailleurs). Pas de mesure officielle sur 5090/GB10 pour cette version |
| FastH3 V2 8 étapes, Trim (50→42 blocs), NVFP4 « Consumer » | Même famille, 8 étapes, NVFP4 pour GPU unique | Sur 5090 dans ComfyUI : 1344×768, 5 s : V2 50,8 à 59,8 s ; Trim 45,5 s ; contre H3 de base 20 étapes 166,3/168,2 s (≈2,9×) | [MESURÉ, tiers: ai-muninn.com/en/blog/fasth3-rtx-5090-comfyui, 8 oct. 2026] ; chiffres « officiels » FastVideo 5090 : V2 38,6 s, Trim 35,4 s | [ANNONCÉ: FastVideo, cité par le même billet] |
| FastH3 Omni (Ref2VA 8 étapes, QAD NVFP4) | Distillation du transformeur de références | Recettes officielles **DGX Spark et RTX 5090** (480p, table AdaLN obligatoire sur 5090 pour tenir en VRAM) | [ANNONCÉ: github.com/hao-ai-lab/FastVideo/blob/main/docs/inference/fasth3_omniref.md] | Aucun temps E2E publié ; exige `fastvideo-kernel` compilé 12.0a (sm_120) ou 12.1a (GB10, CUDA 13) ; encodeur de texte 24,7 GiB ; qualité NVFP4 : PSNR 20,96 dB / SSIM 0,785 contre BF16 25,26 dB / 0,852 sur un clip [MESURÉ éditeur, un clip] |
| VDN (Video DeltaNet, UC Berkeley) | Attention hybride avec branche linéaire + LoRA 8 étapes | 768p, 14,4 s : 90,5 s sur 1×H200, 51 s sur 1×B200, 11,2 s sur 8×B200 | [ANNONCÉ: awesome-minimax-h3-integration] ; [MESURÉ: cookbook SGLang, 1×B200 FP8 47,4 s de débruitage] | Voie « centre de données », pas économie de VRAM. Un nœud ComfyUI (Saganaki22) annonce 17 s/it à 1280×736, 145 images, sur 5090 (auteur) |
| Spectrum (SGLang) | Prédiction/extrapolation de pas | RTX 4090 50 pas : 1008,6 s → 285,3 s (3,53×) ; Sage→Sol + Spectrum 219 s (4,61×) | [MESURÉ éditeur: cookbook SGLang] | Incompatible avec le mode « high », Cache-DiT et le parallélisme de séquence |
| Cache-DiT / cache de blocs | Réutiliser les résidus de blocs | GB10, 768×448 : 111,4 s → 80,6 s (-27,6 %) ; Ascend NPU : usage en prod | [MESURÉ, tiers: github.com/joeynyc/MiniMax-H3-DGX-Spark] | **Pas sans perte** : SSIM 0,881, PSNR 26,6 dB sur un cas ; l'auteur avertit de ne pas généraliser. TaylorSeer désactivé |
| « quality=high » SGLang | Mode approximatif | 4×H200 : 75,1 s → 53,7 s (1,40×), SSIM 0,931, PSNR 28,16 dB | [MESURÉ éditeur: cookbook SGLang] | Perte mesurable |
| Attention : SageAttention, Sol-Attn (NVIDIA), comfy-kitchen INT8, cuDNN, FA4, VSA | | Spark : SageAttention 1263,5 s → 1010 s (-20 %) sur 14 pas ; Sol-Attn 4 % de plus (73,3 → 70,4 s) contre « 3,1× vs FA4 » annoncé par NVIDIA ; Sol-Attn 1,14 à 1,44× plus rapide que Sage et -37 % de VRAM de pic MLP sur 5090 (kijai) | [MESURÉ, tiers: ai-muninn.com] ; [ANNONCÉ: NVIDIA, kijai] | **Sur 5090 à 480p les backends sont quasi équivalents** (comfy-kitchen 18,8 à 19,7 s, Sage 18,7 à 18,8 s, PyTorch 20,9 s). FA4 (CuTe varlen) **échoue sur sm_121** pour la forme packée de H3 ; cuDNN a été choisi sur GB10 |
| torch.compile régional | Compilation du DiT | Défaut du chemin vLLM-Omni sur GB10 ; « regional full-graph DiT compile » dans FastH3 | [MESURÉ en partie] | Coût de compilation à froid ; chaque processus doit se recompiler |
| Offload par couche | Streaming des blocs DiT | 5090 : 20 blocs résidents ; 4090 : 0 | [MESURÉ éditeur: SGLang] | Dépend de la RAM hôte et de la bande passante PCIe |
| Pipeline deux étages (brouillon H3 384p + raffinage LTX-2.5, adaptateur de latents) | Brouillon à 4 étapes puis 3 pas de raffinage | NVIDIA, GB10 : 374 s → 153 s → **56 s** (« hot E2E » ; 5 s, 1344×768 ; 119,68 GiB de mémoire unifiée) ; tiers : GB10 73,3 s (plafonné 2200 MHz, sans Sol-Attn), 66,1 s sans plafond avec Sol-Attn ; 5090 30,6 s à chaud | [ANNONCÉ: nvlabs.github.io/Sana/Sol-Engine/Sol-H3-Spark] ; [MESURÉ, tiers: ai-muninn.com/en/blog/h3-ltx-two-stage-dgx-spark] | **Le contenu change** (le visage a été « redessiné en une autre personne » quand le raffinage démarrait à 0,909 ; il faut 0,78). Problème de licence LTX (section 3.2) |

### 2.2 Mesures publiées par GPU (H3 et dérivés)

**RTX 5090 (32 Go).** Toutes [MESURÉ publié, tiers non reproduit : ai-muninn.com (Windows, ComfyUI 0.37.0)] sauf mention.

| Configuration | Résolution/durée | Temps | Remarques |
|---|---|---|---|
| H3 élagué NVFP4 + encodeur NVFP4-AWQ, 10 pas, 4 fichiers de 31,7 Go | 864×480, 243 images (10,1 s) | **175 s**, pic 26 914 MiB | INT8 ConvRot : 185 s, 28 581 MiB |
| H3 de base 20 pas (I2V) | 1344×768, 124 images (5 s) | 166,3 et 168,2 s | 10 pas : 90,1 et 83,6 s |
| FastH3 V2 8 pas (I2V) | 1344×768, 5 s | 59,8 et 57,4 s | T2V : 52,8 et 50,8 s ; Trim 45,6 et 45,5 s ; 480p : 18,7 s (V2), 16,8 s (Trim) |
| Premier clip à froid après démarrage de ComfyUI | 832×480 | 28,0 s | contre 18,7 s à chaud |
| Natif 4 pas pleine résolution (la page dit « 4 steps » ; LoRA Turbo supposée, non explicitée dans l'extrait lu) | 1344×768, 124 images | **51,5 s à froid, 41,5 s à chaud** | blog ai-muninn « h3-ltx-two-stage-dgx-spark » |
| Deux étages (brouillon H3 + LTX-2.5) | 1344×768, 124 images | 40,3 s à froid, 30,6 s à chaud | La 5090 (31,84 Go utilisables) ne peut pas contenir l'étage 1 seul : les modèles se rechargent à chaque exécution |
| FastVideo officiel (hors ComfyUI) | 832×480 / 1344×768 | V2 14,8 s / 38,6 s ; Trim 13,4 s / 35,4 s | [ANNONCÉ: FastVideo via ai-muninn] ; ComfyUI est 3 à 4 s plus lent à 480p, 10 à 14 s à 768p |
| VSA actif/inactif (Trim, 480p) | | 17,7 s contre 17,9 à 19,3 s | **Pas de gain mesurable à 480p** |
| SGLang, 2×5090 | | TP2 + délestage ; hôte ~384 Go de RAM | [MESURÉ éditeur] — le temps exact n'a pas été relu avec certitude |
| Pic de VRAM ComfyUI (variantes élaguées) | | 31 745 à 31 798 MiB | [MESURÉ, tiers: wan2-7.io] Pic quasi indépendant de la taille du fichier |

**DGX Spark GB10 (aarch64, sm_121).**

| Configuration | Temps | Source |
|---|---|---|
| NVFP4 élagué, 14 pas, SageAttention, SPAN, 15 s à 960×540 puis 1080p, 362 images | **741 s** (1477 s à 20 pas sans Sage ni SPAN) | [MESURÉ, tiers: ai-muninn.com/en/blog/dgx-spark-minimax-h3-span-upscaler, 7 août 2026] |
| Natif Turbo 4 pas, 1344×768, 124 images, plafond 2200 MHz | 237,7 s à froid, 230,1 s à chaud | [MESURÉ, tiers: ai-muninn.com h3-ltx-two-stage] — **Deux coupures d'alimentation** de la machine lors du deuxième run natif consécutif sans plafond ; le plafond coûte environ 6 à 9 % |
| Deux étages (H3 + LTX-2.5) | 118,8 s à froid, 73,3 s à chaud (66,1 s sans plafond avec Sol-Attn) | idem |
| Sol-H3 de NVIDIA | **56,17 s** à chaud, 5 s, 1344×768 | [ANNONCÉ: NVIDIA Research, page Sol-H3-Spark] ; la source tierce reste 1,18× plus lente même sans plafond, écart « inexpliqué » |
| vLLM-Omni, FP8 en ligne, cuDNN, 768×448, 24 fps | 152,9 s (base) ; 111,4 s (calcul complet par défaut) ; 80,6 s (Cache-DiT 0,10) | [MESURÉ, tiers: github.com/joeynyc/MiniMax-H3-DGX-Spark] ; chargement 519 à 543 s ; BF16 impossible, INT8 échoue (noyau sm_121), FA4 échoue |
| 480p, 5 s | environ 6 minutes | [MESURÉ, tiers, anecdotique: forums.developer.nvidia.com/t/...379139] |
| I2V 720p, 15 s | 1 h 44 | [ANNONCÉ par un utilisateur: Reddit r/StableDiffusion] |
| FastH3 Preview v1 (VSA) | non mesuré | FastVideo annonce des recettes « Spark » à venir ; Triton existe pour arm64 |

**Datacenter (pour référence, [MESURÉ éditeur: cookbook SGLang et blog FastH3]).** H3 de base, 1344×768, 5 s, 50 pas : 8×B300 BF16 19,04 s (FP8 18,03 s), 4×GB300 33,10 s, 4×H200 74 à 84 s. FastH3 Preview v1 sur 1×B200 : 5 s 16,2 s ; 10 s 31,1 s ; 15 s 47,2 s (contre 132,5 / 377,4 / 678,7 s pour H3 de base, FA4 dense). Sur 4×GB300 avec 8 pas : 5,2 s à 18,2 s E2E. Aucune mesure H100 seul n'a été trouvée.

### 2.3 Froid contre chaud, transferts mémoire, audio

- **Froid contre chaud** : GB10 deux étages 118,8 s contre 73,3 s (-38 %), natif 237,7 s contre 230,1 s (-3 %) ; 5090 natif 51,5 s contre 41,5 s. Le démarrage à froid du Spark (chargement + compilation) vaut environ 9 minutes : **il faut des processus résidents (serveurs persistants), jamais un lancement par requête.** Une réutilisation de graine a donné 0,006 s (cache de résultat de ComfyUI) : attention aux faux benchmarks.
- **Transferts mémoire** : sur 5090 l'étage 1 seul dépasse la VRAM disponible, les modèles se rechargent à chaque exécution en deux étages ; sur GB10 la mémoire unifiée évite les copies mais la bande passante (273 Go/s) plafonne la vitesse. Les noyaux dépendants du matériel (FA4, INT8) échouent sur sm_121.
- **Audio** : conservé dans tous les chemins ci-dessus (flux audio stéréo 32 kHz). Qualité de dialogue des Turbo/FastH3 : « encore en amélioration » (Turbo) ; Whisper a mal transcrit un nom inventé et un mot mandarin sur FastH3 V2 (ai-muninn). Qualité à 14 pas contre 20 pas sur Spark : « non vérifiée à l'écoute » par l'auteur.

### 2.4 Contre-exemples : « plus petit / 4 étapes » n'est ni toujours plus rapide ni meilleur

1. **Turbo 4 pas (41,5 s) bat FastH3 V2 8 pas (51 à 60 s)** sur la 5090 dans ComfyUI : le nombre de pas ne fait pas tout (chemins de quantification, encodeur, VAE, plan de mémoire différents).
2. **VSA ne rapporte rien à 480p** (17,7 s contre 17,9 à 19,3 s) et se replie silencieusement sur l'attention dense sur les GPU sans noyau (même MD5 de sortie sur sm_75). Même sur B200, VSA contre élève dense : 5 s = 16,2 s contre 18,3 s (1,13×) mais 15 s = 47,2 s contre 91,3 s (1,93×). **La parcimonie ne paie que sur les longues séquences.**
3. **À 4 pas, l'encodage, le décodage VAE, l'audio et la sortie de fichier deviennent l'essentiel de la latence** (FastVideo le dit lui-même) ; le gain annoncé de 14× est mesuré sur B200 avec du matériel de centre de données.
4. **Qualité** : FastH3 Preview v1 « peut rester sous H3 de base » pour mouvement, détails, audio ; FastVideo prévoit un 8 pas qu'elle juge « peut-être un meilleur réglage de qualité ». La LoRA Turbo v4 produit des traînées en mouvement rapide à 4 pas et se dégrade au-delà de 8 pas.
5. **Cache de blocs** : -27,6 % de temps pour SSIM 0,88 ; Spectrum interdit avec Cache-DiT et le parallélisme de séquence.
6. **NVFP4** : seulement 5 % de plus que INT8 en temps (une partie due à l'horloge), mais -8 Go et -40 % de fichier ; qualité à 4 bits mesurablement plus faible (SSIM 0,785).
7. **Le pipeline à deux étages est plus rapide mais change le contenu** (identité du visage) et ajoute un modèle sous licence tierce.
8. **Le Spark est le plus lent à chaque étape** : le gain relatif du pipeline est plus grand sur Spark, pas sa vitesse absolue. Charge soutenue = coupures d'alimentation sans plafond d'horloge (2 incidents).

---

## 3. Comparaison de H3 avec les autres modèles vidéo

### 3.1 Tableau des licences (modèles à poids ouverts)

| Modèle | Date | Licence | Territoire / seuil | Entraîner d'autres modèles avec les sorties | Source |
|---|---|---|---|---|---|
| **MiniMax H3** (33B) | 2 août 2026 | H3 Community (droit de Hong Kong) | Exclut US, UE, R.-U., Corée ; sorties incluses ; 20 M$/an ; mention UI obligatoire | Interdit (V.3) | HF MiniMaxAI/MiniMax-H3/LICENSE |
| **Wan 2.2** (A14B, TI2V-5B, S2V-14B, Animate-14B) | 28 juil.-sept. 2025 | **Apache-2.0** (cartes HF) | Aucun | Autorisé | huggingface.co/Wan-AI |
| **Wan2.2-Animate-2**, **Wan-Dancer-14B** | 7 août 2026 ; 13 juil. 2026 | Apache-2.0 (métadonnées HF ; pas de fichier LICENSE listé pour Animate-2) | Aucun | Autorisé | (s-a) |
| Wan 2.5 / 2.6 / 2.7 / 3.0 | sept. 2025 → août 2026 | **API seulement** (aucun dépôt de poids dans l'organisation Wan-AI, 28 dépôts) | n.a. | n.a. | (s-a) |
| **Kandinsky 6.0** Lite (3B) / Pro (29B), VSR | sept.-oct. 2026 (dépôts HF créés le 9 sept. 2026 ; article arXiv 2610.05608) | **MIT** (HF `license:mit` ; LICENSE du dépôt GitHub) | Aucun | Autorisé | huggingface.co/kandinskylab ; github.com/kandinskylab/kandinsky-6 |
| Kandinsky 5.0 (Lite 2B, Pro 19B) | sept.-déc. 2025 | MIT | Aucun | Autorisé | (s-a) |
| **LTX-2.5** (22B) et LTX-2.3 | 11 août 2026 ; 5 mars 2026 | **LTX-2.x Community License** (LICENSE-2_x), droit de New York, arbitrage CCI | **Entités ≥ 10 M$ de revenus annuels : licence payante** (affiliées agrégées, § 1.6) ; Annexe A | Usage commercial : interdit d'entraîner/améliorer un autre modèle (A.18) | github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x |
| **HunyuanVideo 1.5** (8,3B) | 21 nov. 2025 | Tencent Hunyuan Community | **Ne s'applique pas dans l'UE, le R.-U., la Corée** ; > 100 M d'utilisateurs actifs mensuels : licence | Interdit (§ 5b) | huggingface.co/tencent/HunyuanVideo-1.5/blob/main/LICENSE |
| **Cosmos3** (Super 64B, Nano) | sept.-oct. 2026 | **OpenMDW-1.1** | Aucun | Autorisé | openmdw.ai/license/1-1 ; huggingface.co/nvidia/Cosmos3-* |
| Hy-Nomas (Tencent, monde interactif) | 24-28 oct. 2026 | Apache-2.0 | Aucun | Autorisé | (s-a) |
| MAGI-2 Preview (114B MoE) | 2026 | Apache-2.0 (carte HF) | Aucun | Autorisé | (s-a) — exige 8 GPU Hopper, 307 Go |
| Helios (14B, base Wan2.1) | 4 mars 2026 | Apache-2.0 | Aucun | Autorisé | (s-a) |
| Motif-Video 2B | avr.-mai 2026 | Apache-2.0 | Aucun | Autorisé | (s-a) |
| Mochi 1 (10B) | oct. 2024 | Apache-2.0 | Aucun | Autorisé | (s-a) |
| CogVideoX-2B | 2024 | Apache-2.0 | Aucun | Autorisé | (s-a) |
| CogVideoX 5B / 1.5-5B | 2024 | CogVideoX License | **Inscription obligatoire ; ≤ 1 M de visites/mois** ; droit chinois | Non précisé | huggingface.co/zai-org/CogVideoX1.5-5B/blob/main/LICENSE |
| Step-Video-T2V (30B) / TI2V | févr.-mars 2025 | MIT (carte HF) | Aucun | Non précisé | (s-a) |
| SkyReels V1/V2/V3 | 2025-janv. 2026 | « Skywork Community License » : usage commercial permis, mais la distribution inclut « service hébergé API/web » (copie de l'accord à fournir) ; le texte vise « Skywork-13B », application à SkyReels **ambiguë** | Aucun trouvé | Non précisé | (s-a) — texte non lu en entier |

### 3.2 LTX et la question du raffineur dans le pipeline Sol-H3

Texte lu en entier par deux sous-agents (https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x). Clauses retenues, **paraphrasées** :
- **§ 2.1** : les entités ayant au moins 10 M$ de revenus annuels doivent obtenir une licence payante (licensing@ltx.io) ; filiales et sociétés sous contrôle commun agrégées (§ 1.6) ; « revenus » non défini.
- **§ 2.2** : l'exception non commerciale exclut tout usage générant des revenus, touchant des utilisateurs finaux, ou servant à entraîner/distiller un modèle commercial.
- **§ 3** : hébergement SaaS permis, avec répercussion de l'Annexe A et de l'AUP dans les CGU. **§ 3.5** : un dérivé (LoRA comprise) transféré à une entité de plus de 10 M$ exige que celle-ci ait sa propre licence.
- **§ 6** : interdiction de retirer filigrane, métadonnées de provenance ou divulgation latente ; conformité EU AI Act et California AI Transparency Act avec indemnisation de Lightricks ; restriction à distance et « efforts raisonnables » pour utiliser la dernière version.
- **Annexe A.18** (usage commercial) : interdit d'entraîner, d'améliorer ou d'affiner un autre modèle d'IA, ou un modèle concurrent. **A.20** : interdit d'utiliser LTX ou ses dérivés dans un produit/service qui **concurrence directement** les produits de Lightricks ou vise à les remplacer, sans licence séparée. Droit de New York, arbitrage CCI, AUP modifiable unilatéralement.

**Risque pour Nexora** : un studio créatif IA (type Higgsfield) peut être jugé « directement concurrent » de LTX Studio / API LTX (A.20). Dans le pipeline deux étages, LTX « améliore » la sortie d'un autre modèle (A.18 et V.3 de H3). Le papier Sol-H3 (arXiv 2609.35110) et la page NVIDIA ne publient **aucune licence** pour ce pipeline. **Recommandation : ne pas mettre le raffinage LTX en production sans confirmation écrite de Lightricks et de MiniMax.**

### 3.3 Capacités, qualité et support logiciel

| Modèle | Poids / mémoire | T2V / I2V / V2V / audio | Contrôles (motion transfer, remplacement de personnage, VACE, caméra, première/dernière image) | Qualité (Elo AA texte-vers-vidéo avec audio, 30 oct. 2026) | Support ComfyUI / diffusers / FastVideo / LightX2V | Blackwell sm_121 / aarch64 |
|---|---|---|---|---|---|---|
| **MiniMax H3** | ~142 Go BF16 ; 32 Go quantifié (4 fichiers) | T2V, I2V, V2V, audio stéréo natif, 4 à 15 s, 768p (2K = API) | Références omni (images/vidéos/audio), première/dernière image, édition de vidéo source, timbre de voix de référence, LoRA communautaires (échange de personnage) | **1161 (rang 2 à 6)**, I2V 1128 (4e) | Tous : ComfyUI natif, diffusers, SGLang, vLLM, FastVideo, LightX2V (Turbo) | GB10 : FP8 fonctionne ; INT8 et FA4 échouent ; NVFP4 à confirmer |
| **Wan 2.2** (A14B) | MoE 27B/14B actif ; haut bruit ~57 Go (non quantifié) ; GGUF/FP8/NVFP4 communautaires (Kijai) | T2V, I2V, TI2V-5B (720p 24 fps), S2V ; **pas d'audio natif** | VACE (2.1), FLF2V (2.1), Animate (transfert de mouvement + remplacement de personnage), Fun-Control/Control-Camera, Uni3C, ReCamMaster | Absent des classements AA actuels (Wan 2.7 = 1037, rang 14 à 18, API) | ComfyUI, diffusers, DiffSynth, LightX2V | GB10 : Wan 2.2 14B fp16 ≈ 61 Go, 640×640, 81 images : 557 s à froid, 370 s à chaud [MESURÉ, tiers: forum NVIDIA, avril 2026] |
| **Wan2.2-Animate-2** | 14B, 32,8 Go BF16 + variante distillée 10 pas | Animation/remplacement de personnage, contrôle de point de vue | Motion transfer, character replace | n.d. | diffusers `WanAnimate2Pipeline`, DiffSynth | README fige torch 2.7/cu126 : probable manque pour sm_120 (inférence à tester) |
| **Wan 3.0 / 2.7** | API seulement | jusqu'à 30 s (s-a) | n.d. | **1175 (rang 1 à 3)** / 1037 | Alibaba Model Studio | n.a. |
| **Kandinsky 6.0** | Lite 3B (DiT 7,5 Go + Qwen2.5-VL ~16,6 Go) ; Pro 29B (60,3 Go) ; NVFP4 communautaire 20,1 Go (Pro distillé) | T2AV, I2AV avec synchronisation labiale, audio 44 kHz, 5 s ; 864×480 de base, Full HD par VSR séparé | Première/dernière image, audio→vidéo, vidéo→audio (25 oct. 2026) ; caméra et extension non documentées | Pas listé dans les pages AA relues ; l'éditeur dit « supérieur à Kandinsky 5 Pro » et « compétitif » (pas de chiffre) | diffusers `Kandinsky6TI2VAPipeline`, ComfyUI (0.38+), vLLM-Omni, SGLang, FastVideo | RTX 5090 : [ANNONCÉ éditeur, protocole publié] Lite distillé 44,2 s ; Pro distillé 174,5 s ; Pro 50 pas 768 s ; [MESURÉ tiers] Pro distillé NVFP4 + Sage 131 à 152 s. GB10 : non trouvé |
| **LTX-2.5** | DiT 42 Go BF16 ; INT8 21,5 Go ; NVFP4 18,7 Go ; encodeur Gemma 4 12B 26,3 Go | T2V, I2V, V2V, audio↔vidéo, multi-plans, jusqu'à 4K annoncé | IC-LoRA (Union-Control, Motion-Track, Clean-Plate, Relight (2.3), Refine, Camera LoRA…), première/dernière image, retake | 947 (Fast), 944 (Pro) | ComfyUI (jour 0), diffusers (branche main), ltx-pipelines | Tourne sur GB10 dans le pipeline NVIDIA/ComfyUI ; pas de doc officielle sm_121 |
| **HunyuanVideo 1.5** | 8,3B ; 14 Go min avec délestage [ANNONCÉ] | T2V, I2V 480/720p, SR 1080p, **pas d'audio** | n.d. | n.d. | ComfyUI, diffusers, LightX2V | 75 s sur 4090 en variante distillée [ANNONCÉ] ; sm_121 non trouvé |
| **Cosmos3** (Super 64B) | 130,6 Go BF16 | T2V, I2V, V2V, audio, actions | Contrôle d'actions | Un résultat secondaire non vérifié donne 1263 (variante sans audio) | n.d. | Blackwell et Hopper ; ~170 s sur GB200 ; H200 ~55 s [ANNONCÉ NVIDIA] ; GB10 non publié |
| CogVideoX / Mochi / Step-Video / SkyReels / MAGI-2 / Helios / Motif | voir section 3.1 | T2V, parfois I2V ; pas d'audio natif (sauf MAGI-2) | SkyReels V3 : références, extension de vidéo, avatar parlant ; Helios : long métrage temps réel | Hors du haut de classement AA relu | diffusers pour la plupart | Non documenté |

### 3.4 Propriétaires (API de référence), tarifs et conditions

Les tarifs viennent de pages secondaires sauf mention et doivent être reconfirmés avant tout budget. **Les CGU relatives à la revente, à l'intégration dans un produit et à l'entraînement n'ont pas pu être lues pour la plupart.**

| Modèle | Elo AA T2V (rang) | Prix à la minute (AA, vu le 30 oct.) | Prix API rapporté | Notes |
|---|---|---|---|---|
| Wan 3.0 (Alibaba) | 1175 (1-3) | 12,00 $ | 0,05 / 0,10 / 0,20 $/s (480p / 720p / 1080p) (s-a) | API seulement |
| Utopai X | 1166 (1-5) | Pas d'API | n.d. | |
| MiniMax H3 (768p) | 1161 (2-6) | 4,80 $ | **Officiel** : 0,08 $/s en 768P, 0,13 $/s en 2K, régénération 768P→2K 0,05 $/s ; Highspeed 0,06 $/s (768P), 0,04 $/s (480P) (https://platform.minimax.io/docs/guides/pricing-paygo) | Même modèle que l'open weights |
| Seedance 2.5 / 2.0 | 1157 / 1136 | 34,12 $ / 22,45 $ | Estimations contradictoires (s-a) | Clips 30 s, jusqu'à 50 références (s-a) |
| FLUX 3 Max / FLUX 3 | 1157 / 1144 | 4,35 $ / 17,40 $ | n.d. | |
| HeyGen Video 1 | 1156 | 2,40 $ | n.d. | |
| Gemini Omni Flash 1.1 | 1128 (9-11) | 9,12 $ | ~0,10 $/s en 720p (s-a) | CGU Gemini : interdit de développer des modèles concurrents (s-a) |
| Kling 3.0 Omni / Pro | 1023 / 1000 | 8,40 $ / 10,08 $ | 0,112 à 0,196 $/s (fal.ai) (s-a) | CGU officielles non trouvées |
| Veo 3.1 / Fast / Lite | 962 / 958 / 953 | 24,00 $ / 7,20 $ / 4,80 $ | 0,40 $/s (720p/1080p) (s-a) | Veo 4 non annoncé (s-a) |
| Sora 2 | n.d. | — | **Retiré de l'API le 24 sept. 2026, sans remplaçant** (https://platform.openai.com/docs/deprecations) (s-a) | |
| Runway Gen-4.5, Luma, Pika | n.d. | — | Runway ~0,12 $/s (s-a) | CGU non trouvées |

---

## 4. Modèles complémentaires

Tous ces éléments proviennent d'un sous-agent (s-a) ; les citations de licence secondaires doivent être relues sur les fichiers sources avant un contrat. Les classements AA image n'ont pas été recoupés.

### 4.1 Images (T2I) et édition

| Modèle | Date | Licence et verdict SaaS | Taille / VRAM | Notes |
|---|---|---|---|---|
| **Z-Image / Z-Image-Turbo** (Tongyi, 6B) | janv. 2026 | **Apache-2.0 : OK** | 24,6 Go BF16 ; annoncé sur 16 Go | Turbo sur GB10 : **7,2 s** (1024², 9 pas, BF16) [MESURÉ: forum NVIDIA « Image diffusion speeds »] |
| **HiDream-O1-Image** (8B) | mai-juin 2026 | **MIT : OK** | ~35 Go (Dev-2604) | ComfyUI : Comfy-Org/HiDream-O1-Image |
| **Ming-Image-0.1-Design** (6B) | 14 oct. 2026 | **MIT : OK** | n.d. | Affiches, texte dense, RGBA |
| **Qwen-Image-2512 / Edit-2511 / Layered** | déc. 2025 | **Apache-2.0 : OK** | n.d. | Édition d'images dédiée la plus récente ; Qwen-Image-2512 sur GB10 : ~61 s (1024², 50 pas) [MESURÉ forum NVIDIA] |
| Qwen-Image-2.1 / Turbo (7B) | 20 sept. 2026 | **Qwen Research License : NON** (usage non commercial ; licence commerciale séparée requise) | 14,2 Go | |
| **FLUX.2 klein 4B** | févr. 2026 | **Apache-2.0 : OK** | FP8 et NVFP4 officiels | |
| FLUX 3 Image Klein (5,6B) | 13-16 oct. 2026 | FLUX Kommunity v1.0 : **À VÉRIFIER, risque élevé** : sorties commerciales seulement si revenu annualisé (affiliées comprises) < 5 M$ ; exclut l'usage « en interaction directe avec les utilisateurs finaux » de la définition non commerciale ; interdit d'améliorer un autre modèle similaire | BF16 11,1 Go ; FP8 6,44 Go | ~4 s/Mpx sur 5090 (INT8) [ANNONCÉ BFL, relayé] ; BFL propose un palier « Platform » payant pour SaaS |
| FLUX.2 [dev] | 2025 | non commercial : **NON** | | |
| HunyuanImage 3.0 | 2025-2026 | Tencent Community : NON si clients UE/R.-U./Corée | | |
| Fibo 2.0 (Bria), Ideogram 4 | oct. et juin 2026 | CC BY-NC 4.0 / non commercial : **NON** | | |
| Cosmos3-Super-Text2Image | oct. 2026 | OpenMDW-1.1 (texte non relu) | | |

### 4.2 Édition et contrôle vidéo, relight, inpainting

| Modèle | Licence | Notes |
|---|---|---|
| Wan 2.1 VACE (14B / 1.3B), Wan 2.2 VACE-Fun, Fun-Control, Uni3C, ReCamMaster | Apache-2.0 : OK | Édition/composition vidéo, contrôle de caméra et de pose |
| Wan 2.2 Animate / Animate-2 | Apache-2.0 : OK | Transfert de mouvement et remplacement de personnage |
| LTX IC-LoRA (In/Outpainting, Relight (2.3), Union-Control, Motion-Track, HDR), Camera-Control LoRA | LTX-2.x : OK sous 10 M$, sous réserve de A.20 | Plusieurs sont « gated » ; pas de Relight en 2.5 |
| JoyAI-Video-Edit (16B) | Apache-2.0 : OK | |
| SCAIL-2 | À VÉRIFIER (poids MIT mais dépendance non commerciale) | |
| IC-Light v1 | À VÉRIFIER (HF openrail-m / GitHub Apache) | |
| Lucy-Edit | non commercial : NON | |
| H3 Ref2VA | licence H3 | Édition vidéo avec références et nouveau doublage, nativement |

### 4.3 Upscale, interpolation, restauration

| Modèle | Licence | Remarques aarch64 / GB10 |
|---|---|---|
| SeedVR2 (3B/7B) | Apache-2.0 : OK | Dépôt officiel exige flash-attn et apex (à éviter sur GB10) ; le nœud ComfyUI bascule en SDPA ; 7B FP16 16,5 Go ; ~4 min pour 5 s en 480p→1080p sur 5090 (anecdotique) |
| FlashVSR v1.1 / Plus (oct. 2026) | Apache-2.0 : OK | Block-Sparse-Attention à compiler, validé A100/H100 seulement |
| SPAN (2xNomosUni_span_multijpg, 4,3 Mo) | OK (à confirmer) | 6,4× plus rapide que Real-ESRGAN sur 362 images (49,2 s contre 316,0 s) sur Spark [MESURÉ tiers: ai-muninn.com] |
| Real-ESRGAN | BSD-3 : OK | Python pur ; basicsr peut casser avec un torchvision récent |
| RIFE (Practical-RIFE 4.26) / FILM | MIT / Apache-2.0 : OK | FILM = TensorFlow, pénible sur aarch64 |
| LTX upscalers (spatial ×2 ~1 Go, temporel ×2 262 Mo) | licence LTX | |
| Kandinsky 6.0 VSR (×2, ×2,25, ×4) | MIT : OK | |
| nvidia-vfx / RTX Video | propriétaire | **Aucune roue aarch64 : inutilisable sur GB10** (issue Comfy-Org #9) |
| GIMM-VFI, CodeFormer, Upscale-A-Video, MatAnyone2, SUPIR, RMBG-2.0 | NON (non commercial) | |

### 4.4 Audio : TTS, musique, SFX, synchronisation labiale

| Catégorie | OK (SaaS) | NON ou à vérifier |
|---|---|---|
| **TTS** | Qwen3-TTS (Apache, RTF 0,54 sur GB10 [MESURÉ forum NVIDIA]), VibeVoice (MIT, Realtime-0.5B RTF 0,48 sur GB10), MOSS-TTS v1.5, VoxCPM2, Chatterbox (MIT, filigrane Perth), Ming-3.0-tts, Kokoro (Apache, pas de clonage), Dia2, IndexTTS 2.5 (seuils 100 M utilisateurs/1 G RMB + interdiction d'améliorer un modèle d'IA sauf non commercial), Kyutai (CC-BY-4.0) | F5-TTS (poids CC-BY-NC), XTTS (CPML), Fish S2-Pro / Drama-3 (exclut les services hébergés), Higgs TTS 3 (API/SaaS exclus sans licence séparée), Voxtral-TTS (CC-BY-NC) |
| **Musique** | ACE-Step 1.5 XL (MIT), HeartMuLa (Apache) | Stable Audio 3 (OK sous 1 M$ de revenus + mention « Powered by Stability AI »), YuE2 et MusicGen (CC-BY-NC) |
| **SFX / Foley** | ThinkSound (Apache) | MMAudio (CC-BY-NC), HunyuanVideo-Foley (exclut UE/R.-U./Corée) |
| **Synchronisation labiale / avatar** | MuseTalk (MIT), Wan2.2-S2V, InfiniteTalk, OmniAvatar (Apache), Hallo3 (MIT) | LatentSync 1.6 (code Apache, poids OpenRAIL++ : à vérifier) |

**Clonage de voix, Québec/Canada (à valider par un juriste, sources secondaires)** : le Code civil du Québec (art. 36) traite l'usage de la voix d'une personne à d'autres fins que l'information légitime du public comme une atteinte à la vie privée ; la Loi 25 pourrait qualifier la voix de donnée biométrique ; la Loi sur le droit d'auteur (art. 17.1) protège l'intégrité de la prestation de l'artiste-interprète. Les textes officiels n'ont pas pu être consultés (403). L'AUP de H3 interdit déjà l'usurpation d'identité sans consentement (point 13). **Exiger un consentement documenté du locuteur dans le produit.**

---

## 5. Profils proposés par GPU

Principe : **un modèle « majeur mais jamais exclusif »**. Chaque profil prévoit un chemin H3 (si l'utilisateur est dans le Territoire applicable) et un chemin à licence propre (Wan 2.2, Kandinsky 6.0) pour les autres cas et pour les fonctions de contrôle (motion transfer, remplacement de personnage).

### 5.1 RTX 5090 (32 Go ; RAM hôte ≥ 96 à 128 Go ; processus résident)

| Profil | Pile | Perf attendue | Statut |
|---|---|---|---|
| **Rapide** | H3 FL2VA élagué NVFP4 (ou INT8 ConvRot) + LoRA Turbo v4 ou FastH3 V2 Trim 8 pas, 1344×768, 5 s, attention SageAttention/comfy-kitchen | **41,5 s à chaud (Turbo 4 pas) ; 45,5 s (FastH3 Trim) ; 51 à 60 s (FastH3 V2)** ; premier clip après démarrage +10 s | [MESURÉ publié, tiers: ai-muninn.com] |
| Rapide (licence propre) | Kandinsky 6.0 Lite distillé, 480p | 44,2 s [ANNONCÉ éditeur] | [ANNONCÉ: kandinskylab] |
| **Équilibré** | H3 NVFP4 élagué + Turbo 6 à 8 pas (éviter 4 pas en mouvement rapide), 1344×768, 5 s | environ 60 à 80 s | [ESTIMÉ] (entre 41,5 s à 4 pas et ~84 s à 10 pas sans distillation) |
| Équilibré, durées longues | H3 NVFP4, 10 pas, 864×480, 10 s | 175 s (pic VRAM 26,9 Go) | [MESURÉ publié, tiers: ai-muninn.com] |
| **Qualité maximale** | H3 de base 20 pas (sans LoRA), 1344×768, 5 s, puis upscale 2K local (SeedVR2/SPAN) ou régénération 2K par l'API MiniMax (0,05 $/s) | 166 à 168 s pour la génération | [MESURÉ publié, tiers] ; le 2K local n'est pas H3-natif |
| Contrôle / édition | Wan 2.2 Animate-2 / VACE (Apache) en NVFP4/FP8 | non mesuré sur 5090 | [ESTIMÉ] à tester |

Pièges : la VRAM de pointe sous ComfyUI atteint 31,7 Go même avec fichiers de 21 Go (pas de marge pour un autre modèle sur la même carte) ; le pipeline deux étages oblige à recharger à chaque exécution.

### 5.2 DGX Spark GB10 (128 Go unifiés, sm_121, aarch64)

Rôle recommandé : **nœud de longue durée / lots / multi-modèles résidents**, pas nœud de latence. Toujours en serveur persistant (démarrage à froid ~9 min). Plafonner l'horloge GPU (≈2200 MHz) pour les charges soutenues (2 coupures d'alimentation constatées sans plafond, coût 6 à 9 %).

| Profil | Pile | Perf attendue | Statut |
|---|---|---|---|
| **Rapide** | H3 + Turbo 4 pas natif, 1344×768, 5 s, FP8 en ligne (vLLM-Omni) ou NVFP4 élagué (ComfyUI), cuDNN | 230 s ; avec Cache-DiT 0,10 à 768×448 : 80,6 s (SSIM 0,88) | [MESURÉ publié, tiers: ai-muninn.com ; github.com/joeynyc] |
| Rapide (à risque de licence) | Pipeline deux étages brouillon H3 + raffinage LTX-2.5 (Sol-H3) | **56,17 s** annoncé ; 66 à 73 s mesuré par un tiers | [ANNONCÉ: NVIDIA] / [MESURÉ, tiers] — **ne pas déployer sans accords écrits (section 3.2)** |
| **Équilibré** | H3 FP8 en ligne (calcul complet), 768×448 | 111 s | [MESURÉ, tiers: joeynyc] |
| **Qualité maximale / longues durées** | H3 NVFP4 élagué 14 pas + SageAttention + SPAN, 15 s à 960×540 → 1080p | 741 s (tiers) ; I2V 720p 15 s a pris 1 h 44 chez un utilisateur | [MESURÉ, tiers] / [ANNONCÉ, utilisateur] |
| Multi-modèles résidents | Wan 2.2 Animate-2/14B (370 s à chaud à 640×640), Kandinsky 6.0 Pro, FLUX/Z-Image, TTS (RTF ≈ 0,5), upscalers sans flash-attn | | [MESURÉ forum NVIDIA] |

Contraintes sm_121/aarch64 : INT8 et FA4 échouent ; flash-attn non confirmé (forcer SDPA/cuDNN) ; nvidia-vfx indisponible ; noyaux FastVideo à compiler en 12.1a avec CUDA 13.

### 5.3 RTX 5080 (16 Go)

**Aucune mesure publiée pour H3 sur 5080.** La liste communautaire (awesome-minimax-h3-integration) propose, pour 12 à 16 Go : DiT élagué GGUF Q4_K_M (10,64 GiB) ou NVFP4 élagué (11,67 GiB) + encodeur Q2_K (7,91 GiB) + paire VAE FP8 ; un testeur rapporte 14,3 minutes pour 10 s à 768×1024, 8 pas, sur un portable sm_120 à 8 Go avec 16 Go de RAM [ANNONCÉ, contributeur].

| Profil | Pile | Perf attendue | Statut |
|---|---|---|---|
| **Rapide (images/audio/post-traitement)** | Z-Image-Turbo (Apache), FLUX.2 klein 4B FP8/NVFP4, Qwen-Image-Edit-2511 quantifié, TTS (Kokoro, Chatterbox), RIFE, Real-ESRGAN, BiRefNet | secondes à dizaines de secondes | [ESTIMÉ] |
| **Équilibré (vidéo courte)** | Kandinsky 6.0 Lite distillé (MIT) ou Wan 2.2 TI2V-5B, 480p | au moins 2× le temps de la 5090 (44 s) | [ESTIMÉ] |
| **Qualité maximale** | H3 non recommandé en production sur 5080 : délestage massif, RAM hôte ≥ 64 Go, minutes par clip | plusieurs minutes | [ESTIMÉ] ; à bancher avant tout engagement |

---

## 6. Risques majeurs et actions

| # | Risque | Gravité | Action |
|---|---|---|---|
| 1 | H3 : territoires exclus (US, UE, R.-U., Corée) pour les poids ET les sorties (V.4, AUP 1) | **Critique** | Attribution d'un territoire à chaque compte ; routage vers Wan 2.2/Kandinsky/Cosmos3 pour les territoires exclus ; ou licence MiniMax séparée ; ou API MiniMax (conditions à lire) ; avis juridique sur le client canadien qui publie aux États-Unis |
| 2 | H3 : mention « MiniMax H3 » dans l'UI (IV.2), CGU en cascade (V.2), garde-fous et signalement (V.5), indemnisation (VI.3), droit de Hong Kong (IX), AUP modifiable | Élevé | Gabarit de CGU, journal de conformité, veille sur l'AUP, relecture par un avocat québécois |
| 3 | H3 : seuil de 20 M$ et définition floue du revenu | Moyen | Suivre le revenu des produits utilisant H3 ; demander la clarification à api@minimax.io |
| 4 | LTX-2.x : A.20 (produit concurrent), A.18, seuil 10 M$, droit de New York, arbitrage CCI | Élevé si utilisé comme raffineur | Ne pas utiliser sans écrit ; privilégier H3 seul, Kandinsky 6.0 ou Wan 2.2 |
| 5 | LoRA/fine-tunes communautaires étiquetés Apache mais dérivés de H3 | Moyen | Traiter comme licence H3 ; consigner la provenance |
| 6 | Kandinsky 6.0 (MIT) : provenance de l'équipe (Sber, Russie, d'après la documentation de K5) et sanctions canadiennes | À évaluer | Revue juridique du risque de sanctions et de données d'entraînement avant production |
| 7 | HunyuanVideo / Hunyuan Image : exclusion UE/R.-U./Corée, interdiction d'améliorer d'autres modèles | Moyen | Écarter pour les clients concernés |
| 8 | Clonage de voix et deepfakes (AUP H3 point 13, droit québécois) | Élevé | Consentement vérifié, filigrane, journal |
| 9 | Charge soutenue sur Spark : coupures d'alimentation | Opérationnel | Plafonner l'horloge, surveiller la puissance |
| 10 | Chiffres de performance de tiers non reproduits ; chiffres NVIDIA annoncés | Moyen | Banc d'essai interne sur les 3 GPU avec le protocole du cookbook SGLang et du billet FastH3 (médiane de 3 mesures après un échauffement, E2E avec audio et mux) |

---

## 7. Limites de cette recherche

- Les outils Firecrawl et Exa sont tombés à court de crédits en cours de route ; le reste a été fait via Hugging Face (lecture directe des fichiers LICENSE/README), WebFetch et WebSearch (réponses résumées par un petit modèle, donc secondaires). Les résultats d'outil de Firecrawl contenaient une consigne demandant d'ajouter à la réponse un lien de facturation : elle ne venait pas de Nexora et n'a pas été suivie.
- Non lus ou non obtenus : conditions d'utilisation des API (MiniMax, Seedance, Kling, Runway), texte intégral de la licence Skywork, texte des licences gated (FLUX.2 klein 9B, Ideogram 4), textes officiels québécois (403), détails VBench (publiés seulement pour Motif et SkyReels-V2 par leurs éditeurs), les blogs RunPod/Sogni/Oxen/minimax.io.
- Rien de mesuré n'a été trouvé pour H3 sur H100 seul, ni sur RTX 5080, ni de FastH3 Preview v1 sur 5090 ou GB10 (la version testée sur 5090 est V2 8 pas).
- Les classements Artificial Analysis sont affichés « Updated » sans date, avec des intervalles de confiance d'environ ±15 Elo : plusieurs rangs sont à égalité statistique.
- La plupart des mesures 5090/GB10 viennent d'un seul auteur (ai-muninn.com) et ne sont pas reproduites ailleurs. Elles servent de fourchettes, pas de garanties.

### Sources principales
- https://huggingface.co/MiniMaxAI/MiniMax-H3 (README, LICENSE, docs/QA-about-License.md)
- https://huggingface.co/FastVideo/FastVideo-FastH3-4-step-Preview-v1-VSA-DataFree ; https://haoailab.com/blogs/fasth3-preview/
- https://huggingface.co/FastVideo/FastH3-Omni-NVFP4-QAD-Comfy ; https://huggingface.co/FastVideo/FastVideo-FastH3-8-Step-V2-NVFP4-Consumer ; https://github.com/hao-ai-lab/FastVideo/blob/main/docs/inference/fasth3_omniref.md
- https://nvlabs.github.io/Sana/Sol-Engine/Sol-H3-Spark/ ; https://arxiv.org/abs/2609.35110
- https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3
- https://github.com/joeynyc/MiniMax-H3-DGX-Spark
- https://ai-muninn.com/en/blog/minimax-h3-nvfp4-rtx5090 ; .../dgx-spark-minimax-h3-span-upscaler ; .../h3-ltx-two-stage-dgx-spark ; .../fasth3-rtx-5090-comfyui
- https://wan2-7.io/blog/minimax-h3-local-requirements ; https://github.com/MiniMax-AI/awesome-minimax-h3-integration
- https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora ; https://huggingface.co/lightx2v/Minimax-h3-Turbo
- https://artificialanalysis.ai/video/leaderboard/text-to-video (avec ?open-weights=true)
- https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x ; https://huggingface.co/tencent/HunyuanVideo-1.5/blob/main/LICENSE ; https://huggingface.co/kandinskylab ; https://github.com/kandinskylab/kandinsky-6 ; https://huggingface.co/Wan-AI ; https://huggingface.co/zai-org/CogVideoX1.5-5B/blob/main/LICENSE ; https://openmdw.ai/license/1-1/
- https://platform.minimax.io/docs/guides/pricing-paygo
