# 15 — Littérature : génération, cohérence et long métrage (2 novembre 2026)

Demande du fondateur : que Creative et Mode Studio sachent tout faire, **jusqu'au long métrage**. Ce rapport est la moitié
« génération, cohérence, long format » de la revue ; l'autre moitié (montage, publicité, agents, évaluation des
publicités, mixage) est dans un fichier séparé. Il **prolonge** `07-litterature-scientifique.md` (axes 1 à 9, ~100 articles
déjà classés), `09-llm-au-maximum.md` (rôles du LLM) et `10-qualite-h3.md` (banc H3) sans les répéter : tout article déjà
traité en 07 n'est cité ici que pour renvoyer.

## 0. Méthode, conventions, limites

- **Sources** : recherche plein texte et métadonnées arXiv (outils de recherche d'articles), 11 requêtes (plusieurs formulations par thème) sur les 12 thèmes de
  la demande, filtrées sur juin 2025 à octobre 2026 ; lecture ciblée de passages de méthode/résultats ; API Hugging Face
  Papers (dépôt GitHub) et API GitHub (licence SPDX du **code**) ; lecture des modules `app/server/nexora/` (`film.ts`,
  `filmMoteur.ts`, `juge.ts`, `controle.ts`) et des en-têtes de `app/server/graphs/` (`h3.ts`, `cast.ts`, `seam.ts`,
  `stills.ts`, `stage.ts`, `reshoot.ts`, `music3.ts`).
- **Étiquettes** : **[LU]** = j'ai lu des passages de méthode et/ou de résultats du corps de l'article (pas seulement le
  résumé) ; **[RÉSUMÉ]** = résumé seul, donc aucune affirmation au-delà du résumé. **[MON AVIS]** = recommandation de ma part.
  **[ESTIMÉ]** = calcul de ma part, non mesuré. Les chiffres sont ceux des auteurs, sur leurs bancs, jamais reproduits ici.
- **Licence** = licence du **dépôt de code** (SPDX GitHub). `None` = aucun fichier LICENSE, donc **aucun droit de
  réutilisation** (règle posée en 07). `NOASSERTION` = licence maison à relire. « aucun dépôt » = rien trouvé via
  Hugging Face Papers. Les licences des **poids** n'ont été relues pour aucun article. Tout dérivé de H3 reste sous licence H3.
- **Limite structurante** : H3 est un modèle dont on ne réentraîne rien (07, règle « on consomme des poids publiés »).
  Les méthodes qui exigent un réglage fin (LoRA mémoire, attention inter-plans, correcteur de dérive) **ne s'appliquent pas
  à H3** ; elles servent de preuve de principe. Ce qui s'applique est **la couche d'orchestration autour du modèle** :
  banques d'entités, images clés, plan structuré, juges, boucles de reprise, audio. C'est précisément là que la littérature
  d'octobre 2025 à octobre 2026 est la plus utile et la plus directement transposable.
- **Pas relu** : licences de poids ; reproductions indépendantes (aucune) ; les articles d'octobre 2026 ont quelques jours à
  quelques semaines. Aucune mesure sur notre matériel.
- **Non redit** (déjà en 07) : HoloCine, CausalCine, CineWeaver, CineMem, LongLive(-RAG), Ring Forcing, FramePack, SkyReels,
  ViMax, MovieAgent, FilmAgent, AniMaker, StoryEngine, DramaAgent, CineEvolve (07 §7.6), VBench(-2.0), VideoScore2,
  Artifact-Bench, VideoArgus, JudgeFit, IsoVRBench, PhyProbe, AVBench/VA-Judger/AVC-Reward, Stand-In, Lynx, MAGREF, Phantom,
  Identity-GRPO, Vera, Uni3C, ReCamMaster, Foley-Omni, MMAudio, LatentSync, InfiniteTalk, FlashVSR(+), RIFE, SeedVR2, tout
  l'axe 1 (distillation, caches, quantification, VAE).

## 1. Ce que Nexora a déjà, pour situer les gains

| Brique | Fichier | Ce qu'elle fait aujourd'hui |
|---|---|---|
| Plan de film | `nexora/film.ts` | storyboard LLM : titre, **bible** (style, ≤ 8 personnages, ≤ 8 lieux, texte seul), ≤ 12 plans de 5 ou 10 s, caméra en texte, drapeau `suite` (le plan part de la dernière image du précédent), réplique FR |
| Tournage | `nexora/filmMoteur.ts` | chaque plan = une prise ; bible **répétée dans le prompt** de chaque plan ; réécriture H3 validée ; 2 candidats ; assemblage ffmpeg ; état dans la prise « film » (reprise après redémarrage) |
| Juge | `nexora/juge.ts` + `controle.ts` | contrôle déterministe d'abord (noir, figé, muet), puis juge VLM A/B sur une planche de 3 images, repli sur la première prise valide |
| Moteurs H3 | `graphs/h3.ts` | FL2VA (texte, 1re/dernière image), Ref2VA (références image/vidéo/son), recettes `h3-fast` (FastH3 V2, 8 étapes) et `h3-max` |
| Images clés / références | `graphs/stills.ts`, `graphs/cast.ts` | Qwen-Image et FLUX.2 (multi-références), feuille de références, Ingredients LTX-2.5 |
| Raccord / reprise | `graphs/seam.ts`, `reshoot.ts`, `stage.ts` | pont première/dernière image, re-cadrage MoGe + CrossView, plan d'argile → rendu |
| Musique | `graphs/music3.ts` | MiniMax Music 3 ; le minutage n'est pas suivi à la seconde (10-qualite-h3 §Musique) |

Écarts que la littérature vient chiffrer : (1) la mémoire de continuité est **textuelle** (bible répétée) et non visuelle ;
(2) le juge compare deux prises d'**un même plan** mais ne juge pas la **cohérence entre plans** ; (3) un film est plafonné à
12 plans ; (4) la caméra est une chaîne libre ; (5) aucune voix constante d'un plan à l'autre n'est garantie ; (6) la
musique est choisie, pas alignée.

## 2. Six constats qui comptent (résumé)

1. **Les orchestrations « images clés + mémoire d'entités + modèle image→vidéo gelé » battent les modèles multi-plans
   entraînés** sur les bancs de cohérence inter-plans, sans réentraînement : EntityMem, VideoMemory, CineCrew, StoryMem.
   C'est la voie que H3 permet. [LU]
2. **Les métriques d'embedding mentent sur l'identité** : sur EntityBench deux méthodes ont la même similarité DINOv2
   de visage (0,883 contre 0,875) alors qu'un juge LLM par paires reconnaît le bon personnage dans 71 % des paires pour l'une
   et 0 % pour l'autre. Le juge d'identité doit être une **comparaison par paires avec porte de fidélité**. [LU]
3. **La qualité d'image ne prédit pas la cohérence** : un modèle gagne toutes les dimensions VBench mais a le pire score
   d'identité LLM (0,09). Et MSVBench trouve que les agents « tout-en-un » (MovieAgent, MM-StoryAgent) sont derniers en
   préférence humaine, très loin des modèles à images de référence : l'agent doit **piloter** un bon moteur, pas le remplacer. [LU]
4. **La caméra se planifie et se mesure, elle ne se « décrit » pas** : les VLM confondent translation et rotation, gauche et
   droite, zoom optique et travelling ; un vocabulaire de 17 mouvements atomiques existe. Le LLM planifie en vocabulaire
   contraint, un contrôle **géométrique** (pas un VLM) vérifie. [LU]
5. **La dérive en prolongation est largement déterministe** (≈ 95 % systématique d'après Clean Forcing) et les remèdes qui
   fonctionnent partent d'**ancres** (images clés densifiées de façon hiérarchique) plutôt que d'un déroulé gauche-droite.
   Chez nous : ancrer chaque plan sur l'image canonique, ne pas chaîner indéfiniment de dernière image en dernière image. [LU/RÉSUMÉ]
6. **Un long métrage est un problème d'orchestration et d'état durable, pas de longueur de clip** : le plus gros banc
   publié compte 140 épisodes, 2 491 plans, jusqu'à 50 plans et 13 personnages récurrents avec des écarts de réapparition
   de 48 plans ; la cohérence **décroît avec la distance de réapparition** pour les méthodes sans mémoire par entité. [LU]

## 3. Axe A — Planification « film » et orchestration

### A1. CineCrew / FilmDSL — langage de film entre le scénario et le moteur [LU]
- *Better Call CineCrew: Consistent Ultra-Long Narrative-to-Film Generation* — Chen, Dong, …, Gan (UMass, MIT) — 07/09/2026 — arXiv 2609.07720.
- **Contribution** : couche d'orchestration multi-agents autour d'un **JSON unique « FilmDSL »** (en-tête `meta`, `assets`,
  `memory`, liste `clips`). Chaque plan a **trois couches** : *action narrative* (action, émotion, dialogue), *mise en scène*
  (`shot_type`, `camera_move`, cadrage, lumière, `character_refs`, `set_ref`, `required_props`/`forbidden_props`,
  `continuity_link` vers l'état du plan précédent), *spécification de rendu* (prompt d'image clé, prompt vidéo, négatif,
  durée, graine). Rôles : Showrunner, ArtDepartment (fiches personnages/décors), StoryEditor, ActingCoach (bloc de jeu par
  battement : objectif, arc émotionnel, déplacements, micro-actions), Cinematographer, TechnicalDirector, ProductionOperator,
  VODirector (voix off), **DailiesReviewer** (rushes), PostSupervisor (assemblage, sous-titres, foley, mixage).
  Boucle par plan : **image clé d'abord**, puis vidéo ; en cas de défaut le reviewer **édite les champs du DSL** (accessoires,
  lien de continuité, prompt) et non le prompt à l'aveugle, avec nombre de reprises borné R. Opérateur de continuité
  « dernière image → première image » utilisé **seulement quand deux clips forment une prise continue**. Un « Production
  Rulebook » (règles a priori anti-hallucination/anti-apparition + état d'exécution : images clés acceptées, accessoires et
  disposition verrouillés, étiquettes d'échec) sert de mémoire partagée.
- **Évaluation** : CineCrewEval = 6 scores cinéma (VLM : placement caméra, lisibilité du battement, jeu, look, cohérence
  narrative, physique), 4 scores de cohérence (identité, permanence des accessoires, continuité de disposition, passage
  d'action) + 7 scores VBench. Chiffres de résultats non lus.
- **Correspondance** : `film.ts` (`PlanFilm`, `Storyboard`) + `filmMoteur.ts` (boucle) + `juge.ts` (rushes). Notre bible texte
  devient la section `assets`/`memory` ; `suite` devient `continuity_link` typé.
- **Code/licence** : aucun dépôt (page projet seulement). **Maturité** : article, TV-style segments. **Effort** : M (schéma
  Zod + deux prompts). **Impact** : fort.

### A2. VideoMemory — banque dynamique d'entités avec états [LU]
- *VideoMemory: Toward Consistent Video Generation via Memory Integration* — 2601.03655 (janvier 2026).
- **Contribution** : trois banques (personnages, accessoires, décors) ; une entrée = (identifiant, **vecteur d'attributs
  textuel** = âge, coiffure, tenue, état, époque, **image de référence**). Un agent mémoire : extrait les entités du plan,
  **retrouve** l'entrée sémantiquement compatible (comparaison par LLM, pas par chaîne), sinon **génère une nouvelle image
  de référence en lui donnant les anciennes** (ex. « Anna à 60 ans » après « Anna à 20 ans ») : l'évolution est contrôlée,
  l'identité conservée. Image clé du plan composée avec les références, puis I2V (Wan 2.2 14B). Règles du prompt vidéo :
  ≤ 500 caractères, **action seulement**, pas de style ni de caméra, ne rien ajouter aux références.
- **Résultat [LU]** (cas à 8 plans, ablation de la banque) : personnage 0,51 → 0,65, accessoire 0,43 → 0,50, **décor
  0,28 → 0,72**. Étude utilisateur (5 personnes) : jusqu'à 95,8 % de préférence. Banc de 54 cas.
- **Correspondance** : remplace « bible répétée dans le prompt » ; le moteur Ref2VA de H3 reçoit les références ; `stills.ts`
  (FLUX.2 multi-références) génère les nouvelles entrées. **Code** : aucun dépôt. **Effort** : M. **Impact** : fort.
- **Réserve** : banc de 54 cas, 5 évaluateurs, métriques maison.

### A3. EntityBench / EntityMem — le banc et la méthode « références pré-générées » [LU]
- *EntityBench: Towards Entity-Consistent Long-Range Multi-Shot Video Generation* — 2605.15199 (mai 2026).
- **Banc** : 140 épisodes tirés de médias narratifs, 2 491 plans, jusqu'à 50 plans, 13 personnages, 8 lieux, 22 objets
  récurrents, écarts de réapparition jusqu'à 48 plans ; **calendrier d'entités par plan** ; 51 métriques en trois piliers
  (qualité intra-plan, respect du prompt, cohérence inter-plans) ; **porte de fidélité** (seuil 0,50) : la cohérence n'est
  comptée que sur les plans où l'entité est **correctement** rendue ; détection par GroundingDINO (seuils 0,25/0,20) + CLIP ;
  juge multimodal pour l'identité par paires ancre-contre-plan.
- **EntityMem** (sans entraînement) : *avant toute vidéo*, des agents génèrent les références de **toutes** les entités : un
  agent de classification décide lesquelles ont besoin d'une référence ; portrait de chaque personnage **sur fond
  chroma-key, segmenté, étiqueté de son nom en bas de l'image** (aide le modèle à lier nom et visage quand plusieurs
  personnages sont présents) ; lieux = **panorama recadré en trois variantes gauche/centre/droite** pour composer l'image clé
  selon l'angle de caméra ; agent de vérification qui retente avec un autre fond si la segmentation échoue ; agent de
  disposition qui place les portraits normalisés en hauteur ; description textuelle de chaque entité réinjectée au prompt.
  **La dernière image du plan précédent sert d'entrée de première image mais est exclue de la banque** pour ne pas écraser
  les références soignées. Argument des auteurs : extraire les références de sorties déjà générées **fait entrer les
  défauts des premiers plans dans le pool et les compose**.
- **Résultats [LU]** : personnage présent dans **96,7 %** des plans prévus contre 84,9 % pour StoryMem ; fidélité du
  personnage d = +1,71 ; **mais** les objets sont plus mal rendus (d = −0,33, « effet autocollant » du détourage) ;
  similarité DINOv2 de visage 0,883 vs 0,875 alors que l'identité par juge LLM est de 71,4 % vs 0 % ; le modèle qui gagne
  VBench a l'identité LLM la plus basse (0,09). Juge : Gemini 2.5 Pro.
- **Correspondance** : feuille de références de `cast.ts`, `stills.ts` ; le portrait étiqueté + panorama trois angles sont
  directement des entrées Ref2VA / images clés. **Code** : EntityBench (Catherine-R-He), **None**, 13 étoiles.
  **Effort** : S à M. **Impact** : fort (c'est la recette la plus précise de la revue).

### A4. FilmWorld — l'état du monde évolue avec l'intrigue [RÉSUMÉ]
- *FilmWorld: Agentic Novel-to-Film Generation through Dynamic Cinematic World Modeling* — 2607.19038 (juillet 2026).
- Résumé seul : construction (entités avec **état** et ancrage visuel) puis évolution (propagation d'état d'un plan au
  suivant, **vérification en boucle fermée de l'état**), planification de plans pilotée par l'état ; banc FilmEval, 15
  romans, 9 métriques objectives. Utile pour le **long métrage** : le modèle de données doit porter l'état (blessure, objet
  déplacé, heure) et pas seulement l'apparence. Aucun dépôt. **Effort** : M. À rapprocher de DramaAgent/StoryEngine (07).

### A5. CANVAS, SSRS, STAGE, DrawVideo — variantes utiles [RÉSUMÉ]
- **CANVAS** (2604.13452) : agents de storyboard qui planifient la **continuité** : ancres d'arrière-plan persistantes, scènes
  « par lieu » pour des transitions douces ; résumé : continuité du fond +21,6 %, personnage +9,6 %, accessoires +7,6 %.
  Idée à garder : planifier **par lieu**, pas plan par plan.
- **SSRS / MSAV-Script-100K** (2610.15512) : représentation de script « avec état et relations » séparant identités
  persistantes (visage **et voix**) et états propres au plan, avec **liaison source-son** et suite d'événements
  audio-visuels qui traverse les coupes. Utile pour structurer le champ `son` du plan (qui produit quel son).
- **STAGE** (2512.12372) : prédire un **storyboard en paires image de début / image de fin par plan** (« STEP2 »), plus un
  « paquet mémoire multi-plans ». Correspond exactement à notre FL2VA (1re/dernière image).
- **DrawVideo** (2605.23508) : plan = croquis noir et blanc + prompt d'apparence + prompt de mouvement ; image clé alignée à
  la structure, puis images clés dérivées d'actions ordonnées, puis clips entre images adjacentes. Piste pour Mode Studio
  (storyboard dessiné par l'utilisateur).
- **Code** : aucun dépôt relevé pour ces quatre. **Effort** : S à M, par idée.

## 4. Axe B — Mémoire et cohérence multi-plans

### B1. StoryMem — mémoire d'images clés dans un modèle gelé + LoRA [LU]
- *StoryMem: Multi-shot Long Video Storytelling with Memory* — Zhang et al. — 2512.19539 (décembre 2025).
- **Contribution** : génération plan par plan, chaque plan conditionné sur une **banque d'images clés** des plans passés,
  injectées par concaténation latente avec un décalage négatif de RoPE (S = 55), LoRA de rang 128 (~0,7 B paramètres actifs)
  sur Wan 2.2 I2V-A14B, entraînée sur 400 K clips de 5 s appariés à 1 à 5 clips apparentés.
- **Choix de la mémoire [LU]** : première image fixée, puis une image est ajoutée quand sa similarité CLIP avec la dernière
  image clé passe **sous un seuil dynamique** (départ 0,9) ; **filtre esthétique HPSv3** (seuil 3,0) pour écarter les images
  floues des plans à fort mouvement ; mémoire hybride **« puits » (premières images fixes = ancres longues) + fenêtre
  glissante** (récentes) ; le même moteur gère I2V (plans enchaînés) et R2V (références comme mémoire initiale).
- **Résultats [LU]** : cohérence inter-plans +28,7 % contre le modèle de base et +9,4 % contre HoloCine (ViCLIP) ; banc
  ST-Bench = 30 scripts de 8 à 12 plans. Les auteurs notent que la mémoire **réduit un peu** le suivi du prompt par plan.
- **Correspondance** : non transposable tel quel à H3 (LoRA). **Transposable** : la **règle de sélection des images clés**
  (CLIP distinct + filtre esthétique) pour choisir, parmi les plans déjà rendus, quelles images deviennent des références
  Ref2VA d'un plan ultérieur ; et la structure « puits + fenêtre » pour limiter le nombre de références.
- **Code/licence** : Kevin-thu/StoryMem, **NOASSERTION**, 777 étoiles, actif (juillet 2026). **Effort** : S (sélection).

### B2. Modèles multi-plans entraînés — à surveiller, pas à intégrer [RÉSUMÉ]
- **OneStory** (2512.07802) : « plan suivant » autorégressif sur I2V pré-entraîné, **sélection de trames pertinentes** + conditionneur adaptatif ; 60 K plans.
- **FilmWeaver** (2512.11274) : double cache (mémoire de plan = images clés des plans passés ; mémoire temporelle = historique du plan courant), interaction multi-tours ; extension et injection multi-concepts.
- **MovieGrid** (2609.06373) : post-entraînement qui range les segments d'une longue vidéo **sur une grille spatiale** ; 6,05 fois plus de plans à budget de jetons égal sur 1 616 images ; cohérence intra-plan 0,9131 vs 0,8086 pour HoloCine, inter-plans 0,5914 vs 0,5384 pour StoryMem (chiffres du résumé). Dépôt : **None**.
- **UnityShots** (2606.21661, base LTX-2.3) : **deux emplacements fixes de mémoire** (long terme = premier plan, court terme = queue du précédent), mis à jour à chaque coupe par une porte qui fusionne la probabilité visuelle de coupe et le suiveur de temps ; **un jeton de locuteur de référence injecté à chaque plan pour conserver le timbre** ; type de coupe appris en bouton de réglage de la force de transition. Dépôt : **None**.
- **JoyAI-Echo-1.5** (2608.23383) : mémoire inter-plans composable + indices de locuteur dérivés de l'audio filtré de la parole ; générateur causal peu d'étapes. Dépôt : NOASSERTION, 2 065 étoiles.
- **SubjectAnchor** (2609.34502, Wan 2.2 I2V) : mémoire **par sujet** (trace chaque sujet jusqu'à ses apparitions passées).
- **[MON AVIS] — SURVEILLER.** Aucun n'est un moteur que nous exécutons ; tous confirment la même architecture (mémoire
  de **trames clés** par plan/sujet, fixe + glissante). Si un de ces modèles sort avec poids sous licence acceptable, il
  entre au registre de capacités comme moteur « scène multi-plans » (07 §2.7 réserve la place).

### B3. Prolongation et dérive : ce qui s'applique à un moteur non autorégressif [LU/RÉSUMÉ]
- **Clean Forcing** [LU] (2610.25634, Seoul National U., Northeastern, NVIDIA, 19/10/2026) : la dérive d'un modèle
  autorégressif est ≈ 95 % **systématique** (même écart de vitesse quel que soit le bruit) donc apprenable ; correcteur LoRA
  de 5,9 M de paramètres sur base gelée, **sans vidéo réelle**, fusionné sans coût d'inférence ; sur 50 s, Δ-dérive +11,3 → +1,65
  (−0,16 avec 40 clips réels). Rang 16 dans le squelette bat le plein rang (283 M) et le réseau latéral. Pas de dépôt.
  **Pour nous** : ne s'applique pas à H3 (non autorégressif) ; confirme que **le défaut de dérive est mesurable** (écart de
  saturation / MUSIQ entre le début et la fin) et donc contrôlable par code.
- **Deep Forcing** [RÉSUMÉ] (2512.05081, KAIST) : sans entraînement, « Deep Sink » (la moitié de la fenêtre en jetons
  persistants, phase RoPE réalignée) + compression participative du cache KV ; extrapolation ×12 (5 s → 60 s+). **Apache-2.0**, 154 étoiles.
- **FlowLong** (2605.20910), **FLEX** (2602.14027), **FreqForcing** (2607.27110), **FreeSpec** (2605.06509),
  « Towards Error-Free Long Video Generation » (2606.22370) : correctifs d'inférence ou d'entraînement pour l'extension
  autorégressive/par fenêtres glissantes [RÉSUMÉ]. **Aucun ne cible un modèle fermé comme H3.**
- **Anchored Tree Sampling (ATS)** [RÉSUMÉ] (2605.20476) : remplace le déroulé gauche-droite par une **imputation
  éparse → dense bornée par des ancres**, organisée en arbre ; « transforme une dérive qui croît avec l'horizon en dérive bornée
  entre ancres » ; chemin critique K étapes → L+1 ; démontre ≥ 40 min sur LTX-2.3 (vidéo vers vidéo, caméra statique).
  **Pour nous : c'est le schéma « images clés d'abord, FL2VA entre deux ancres »**, qui est déjà notre moteur.
- **[MON AVIS] — ADOPTER l'idée, pas le code** : pour tout plan prolongé (`suite`), ancrer sur l'image canonique du
  personnage/lieu au lieu de chaîner indéfiniment de dernière image en dernière image ; ajouter à `controle.ts` une mesure de
  dérive (saturation, netteté, similarité DINO début/fin).

### B4. Cohérence de monde et de lieu (3D) [RÉSUMÉ] — SURVEILLER
- OctWorld (2609.03919, mémoire octree TSDF, Microsoft), I3DM (2603.23413), Honeycomb (2609.37690, mémoire à taille
  constante), 3DScenePrompt (2510.14945), Mirage (2606.09828), Closing the Loop (2607.21848, retour au même lieu sans
  entraînement), WorldWeave (2609.34221), Momentum (2610.23423).
- Tous visent le **monde explorable à caméra libre** (RealEstate10K, WorldScore, conduite). **Pas de gain direct pour un
  film découpé en plans.** Le substitut pragmatique et déjà validé pour le film est celui d'EntityMem : un **panorama du lieu
  recadré en trois angles** + description textuelle, plus, si un même lieu revient plus tard, la réutilisation de la même
  référence. À reconsidérer seulement si Mode Studio vise le « plan-séquence qui traverse un décor ».

## 5. Axe C — Identité et références (compléments à 07 axe 3)

- **KeyID** [RÉSUMÉ] (2608.16154, ACM MM 2026 IPVG Grand Challenge, 2e place piste « actions séquentielles ») : sans
  entraînement, **découple** la dynamique de l'identité : (1) vidéo-brouillon alignée sur plusieurs références mais
  « agnostique de l'identité », (2) **correction d'identité sur images clés éparses**, puis interpolation du mouvement. Dépôt
  : **None** (1 étoile). **Mapping** : c'est un second remède quand le juge d'identité (voir §9, T2) rejette une prise : au
  lieu de régénérer toute la prise, **retoucher l'image clé** (Qwen-Image-Edit / FLUX.2) puis relancer FL2VA.
- **Direct, parallèle ou séquentiel ?** [RÉSUMÉ] (2608.22819, ACM) : étude sans entraînement de trois façons de faire une
  I2V multi-sujets ; le séquentiel (fond d'abord, sujets ajoutés ensuite) garde le contexte de scène mais est sensible à
  l'**ordre** des sujets et propage les erreurs. Utile pour décider quand séparer une scène à deux personnages.
- **Identity as Presence** [RÉSUMÉ] (2603.17889) et **Omni-Customizer** [RÉSUMÉ] (2605.17488) : personnalisation **apparence
  + voix** conjointe sur modèles audio-vidéo, liaison identité visuelle / timbre par sujet, lutte contre la « fuite de
  parole ». Même constat qu'UnityShots : la **voix est une identité à ancrer** comme le visage.
- **ID-Crafter** [RÉSUMÉ] (2511.00511) et **DIAL** [RÉSUMÉ] (2609.11507) : multi-sujets par attention hiérarchique + RL ; DIAL
  exploite des cartes d'attention internes pour régler la force de fidélité à l'inférence. Réentraînement exigé : surveiller.
- **Gloria** [RÉSUMÉ] (2603.29931) : un personnage représenté par un **petit ensemble d'images-ancres** (« anchor frames »),
  plus de 10 minutes de vidéo cohérente ; mêmes principes que A2/B1. Pas de dépôt relevé.
- **[MON AVIS]** : le point commun de toute la littérature identité 2026 est « quelques bonnes images-ancres, variées
  (vues), choisies avec un filtre de qualité » ; notre `cast.ts` (feuille de références) est dans la bonne direction.

## 6. Axe D — Caméra et grammaire cinématographique

### D1. Vocabulaire et mesure [LU]
- **ACaM — Natural Language Camera Movement Understanding** (2607.03043, juillet 2026) [LU] : taxonomie en 17 classes
  atomiques : translation (dolly in/out, truck gauche/droite, boom haut/bas), rotation (pan gauche/droite, tilt haut/bas,
  roll horaire/anti), changement de focale (zoom in/out), statique, mouvements centrés sur l'objet (tracking, arc/orbite).
  Cinq modes d'échec des VLM : insensibilité aux petits changements, confusion mouvement physique/rotation, erreurs de sens,
  confusion **zoom optique / dolly**, confusion mouvement d'objet / mouvement de caméra. Qwen3-VL 4B/8B affiné : +10 % sur
  vidéos réelles et +11 % sur synthétiques contre Gemini 3.1 Pro, mais **écart persistant avec l'humain**. Jeu d'entraînement
  de 24 321 vidéos, test de 2 602 ; code/licence non relevés.
- **ShotBench / ShotVL** (2506.21356, juin 2025) [LU] : 3,5 K questions d'experts sur 200+ films, **huit dimensions**
  (taille de plan, cadrage, angle de caméra, focale, type d'éclairage, condition d'éclairage, composition, mouvement) ; le
  meilleur modèle (GPT-4o) reste < 60 % ; ShotQA (~70 K) + ShotVL = Qwen2.5-VL-3B affiné SFT + GRPO, +19,0 % sur toutes les
  dimensions. Dépôt Vchitect/ShotBench : **None**.
- **Autres [RÉSUMÉ]** : CinematicVQA (2609.28813, raisonnement sur la fonction narrative du cadrage ; le raisonnement pas à
  pas **dégrade** la plupart des modèles) ; SLU-Suite (2603.18448, 490 K questions, 33 tâches) ; CineCap (2606.24636,
  légendage cinématographique à récompenses RL, dépôt public) ; RefineShot (2510.02423, correction des biais de ShotBench) ;
  Geometry-Guided Camera Motion (2603.13119, extrait des **indices géométriques de modèles 3D** et les injecte dans le
  prompt du VLM sans entraînement).
- **Mapping** : (a) le champ `camera` de `PlanFilm` (texte libre) devient une **énumération** (17 mouvements × taille de
  plan × angle) que le LLM compile ensuite dans le dialecte H3 ; (b) le contrôle de **conformité de caméra** doit être
  géométrique : flux optique / homographie par code, ou MoGe déjà présent (`reshoot.ts`), **pas** le juge VLM (ACaM +
  ShotBench le déconseillent) ; (c) ShotVL/ACaM-VLM, une fois licence éclaircie, peuvent **légender nos prises** pour la
  bibliothèque (recherche « plan large en travelling arrière »).

### D2. Planifier puis contrôler [LU partiel]
- **ShotVerse** (2603.11421, SIGGRAPH Asia 2026) [LU : résumé, mise en œuvre, baselines] : « Plan-then-Control ». Un
  **Planner** (Qwen3-VL-2B + décodeur, LoRA r = 32, trajectoires tokenisées) transforme un prompt hiérarchique (global +
  par plan) en **trajectoires de caméra explicites dans un repère global commun à tous les plans** ; un **Controller**
  (HoloCine + adaptateur de caméra, LoRA r = 128, entraîné sur 96 GPU H20) les rend. Compare à Sora 2, Veo 3, Kling 3.0,
  Seedance 2.0 avec les mêmes prompts hiérarchiques ; évaluation par VLM (Gemini 3 Pro) + humains. Dépôt : **None**.
  **Pour nous** : le **Controller n'est pas transposable à H3** ; **l'idée de Planner l'est** : un LLM qui sort un
  mouvement structuré et **cohérent d'un plan à l'autre** (le repère global évite que deux plans du même lieu se
  contredisent), compilé en texte H3.
- **CT-1** [RÉSUMÉ] (2604.09201) : modèle Vision-Language-Camera estimant des trajectoires ; +25,7 % de précision de contrôle.
  **PartiCam** [RÉSUMÉ] (2609.39504) : guidage par récompense en filtre particulaire, **sans entraînement**, indépendant du
  modèle — candidat de spike sur H3 (07 §4.6 demandait déjà une méthode sans entraînement). **Rays as Pixels** (2604.09429),
  **CameraNoise** (2605.30774), **TriMotion** (2606.20774, caméra par texte/pose/vidéo dans un espace commun),
  **Track2View** (2606.15534) : contrôle appris, réentraînement exigé.

## 7. Axe E — Prompts : réécriture et boucles de rétroaction

### E1. RAPO++ [LU]
- *RAPO++: Cross-Stage Prompt Optimization for T2V via Data Alignment and Test-Time Scaling* — 2510.20206 (octobre 2025).
- **Idée** : trois étages. (1) Enrichir le prompt avec des modificateurs **récupérés** dans un graphe de relations bâti sur le
  corpus d'entraînement du modèle (2,1 M de phrases), puis le **réécrire pour qu'il ressemble à la distribution
  d'entraînement** (longueur, structure). (2) **SSPO** : boucle à plusieurs rondes ; vidéo → retour d'un VLM (LLaVA-OneVision)
  + ensemble de vérificateurs (fidélité spatiale, cohérence temporelle, alignement), flux optique pour la physique ; la
  rétroaction va dans une mémoire et un LLM (Qwen2.5-7B) réécrit ; classement moyen pour choisir. (3) Affiner le réécrivain
  (LoRA Llama 3.1) sur les paires (brut → optimisé) collectées en (2).
- **Chiffres [LU]** : VBench 82,65 % (LaVie), 80,75 % (Latte) ; testé sur LaVie, Latte, HunyuanVideo, CogVideoX, Wan2.1,
  cinq bancs. Coût d'affinage : un seul A100, ~5 h par itération. Dépôt Vchitect/RAPO : **None**.
- **Pour nous** : H3 a déjà un **guide d'écriture officiel** et un réécrivain validé (`reecritureH3.ts`) ; l'étage 1 est
  couvert par construction. Le gain à prendre est l'étage 2 **au niveau du plan** : relancer l'écriture avec un retour
  typé du juge (« la personne tourne le dos », « l'accessoire n'apparaît pas ») plutôt que de changer la graine. Étage 3 : nos
  journaux (prompt, défaut, correction, résultat) forment gratuitement le jeu de réglage d'un futur petit réécrivain.

### E2. Autres [RÉSUMÉ]
- **TIDE** (2610.15098) : distille la recherche coûteuse en un **module de règles réutilisable** (« Skill ») qui produit prompt
  positif **et négatif** en **un seul appel LLM**, appris sur 100 prompts en 14 h ; transfert à des modèles inconnus.
  Dépôt : introuvable (404). **Très proche de notre mécanisme `competences.ts`** : confirme la voie.
- **ProactGen** (2610.22608) : un VLM appris à **poser les bonnes questions à l'utilisateur à partir d'un brouillon généré
  en peu d'étapes** (le brouillon n'a pas besoin d'être de qualité finale) ; meilleur alignement au prix de 29 % du temps de
  quatre rondes de réécriture. **Pour nous** : le brouillon 8 étapes FastH3 + la question du Producteur (« tu veux plutôt
  ceci ou cela ? » avec deux vignettes).
- **Beyond Trial-and-Error** (2608.12290) : boucle LLM de prompts avec requêtes **Davidson Scene Graph** (adhérence) +
  « Common Mistake Questions » (artefacts), puis **optimisation bayésienne de la graine et du CFG** ; préférence humaine
  jusqu'à 69 %. **Pour nous** : H3 tourne à CFG 1, donc seule la graine est un levier ; la liste de questions « fautes
  courantes » alimente `controle.ts`/juge.
- **PhyPrompt** (2603.03505) : réécriture RL pour la physique, +11 pt de sens commun physique sur VideoPhy2 avec un 7B ;
  **SCMAPR** (2604.05489, dépôt None) : routage par taxonomie de scénarios complexes + vérification sémantique ;
  3R (2603.01509). Moins pertinents (modèles anciens, bancs courts).

## 8. Axe F — Évaluation et récompense (compléments à 07 axe 8)

- **MSVBench** [LU] (2602.23969, février 2026) : banc de génération multi-plans à **scripts hiérarchiques et images de
  référence**, évaluation hybride **LMM + modèles experts**, 20 méthodes ; corrélation de Spearman avec l'humain **94,4 %**
  (VBench 58,5 ; EvalCrafter 26,3 ; ViStoryBench 83,6). Constats : les références image sont une **épée à double tranchant**
  (Wan2.2-I2V cohérence proche des modèles commerciaux, mais physique plus faible que le T2V : 3,44 vs 3,86) ; les modèles
  actuels sont des « interpolateurs visuels » plutôt que des modèles du monde ; un petit Qwen3-VL-4B affiné sur les **traces de raisonnement** de
  l'évaluation rattrape Gemini 2.5 Flash. Les agents tout-en-un classent derniers en préférence humaine (MovieAgent 1,36 /
  5 ; modèles commerciaux ~4). Dépôt : aucun.
- **EntityBench** [LU] : voir A3 (porte de fidélité, juge par paires, accord/désaccord DINO-LLM).
- **PersonaShot** [RÉSUMÉ] (2608.16717) : continuité **centrée personnage** entre plans — états physiques (blessure,
  tenue), dynamique affective, grammaire cinématographique ; 16 métriques, évaluateurs légers distillés d'un enseignant
  multimodal alignés sur des experts ; constat : écart net entre qualité perceptive et continuité narrative, avec des
  « remises à zéro d'état physique » à chaque coupe. Pertinent pour le long métrage (continuité d'état).
- **LoCoT2V-Bench** [RÉSUMÉ] (2510.26412) : 17 modèles de longue vidéo ; forts en qualité perceptive et fond, faibles en
  alignement fin au texte et en cohérence de personnage.
- **Modèles de récompense** [RÉSUMÉ] : **SoliReward** (2512.22170 ; annotations binaires par vidéo + appariement inter-prompts
  contre le bruit de l'annotation par paires et le piratage de récompense ; dépôt **None**), **REACT** (2601.04033 ;
  récompense **au niveau de l'image** pour les **distorsions structurelles** avec attribution, SFT + GRPO), **GT-SVJ**
  (2602.05202 ; un modèle de génération vidéo reconverti en juge à énergie, 30 K annotations suffisent), **Diffusion-DRF**
  (2601.04153 ; VLM figé comme critique avec questions décomposées). **[MON AVIS]** : REACT est la seule voie documentée
  vers ce qu'Artifact-Bench (07 §8.3) dit manquer aux VLM — repérer des artefacts structurels ; à surveiller dès qu'un
  poids est publié. Ces modèles servent à **réentraîner** ; pour nous seul leur rôle de juge compte.

## 9. Axe G — Audio : musique, doublage, voix, bande-son

### G1. Vidéo → musique, minutage [LU]
- **V2M-Zero** [LU] (2603.11042, mars 2026) : musique **alignée dans le temps sans aucune paire vidéo-musique**. Pour une
  séquence de caractéristiques (MusicFM pour la musique à l'entraînement, DINOv2 pour la vidéo à l'inférence), la
  « **courbe d'événements** » = 1 − similarité cosinus entre vecteurs consécutifs, **standardisée** (moyenne 0, écart-type 1),
  rééchantillonnée à la longueur du latent, lissée (fenêtre de Hann) ; ajoutée comme canal au latent d'un modèle de flux
  rectifié pré-entraîné de texte→musique ; **à l'inférence, la courbe de la vidéo remplace celle de la musique**. Le texte
  garde le contrôle du genre et de l'énergie. Corrélation courbes réelles ≈ 0,6 contre ≈ 0,2 avec décalage aléatoire.
  Fine-tuning de 192 à 768 heures-GPU. Résultats : +21 à 52 % de synchronisation temporelle, +28 % d'alignement sur les
  temps de danse. Dépôt non relevé.
- **Pour nous** : MiniMax Music 3 ne suit pas le minutage (10-qualite-h3). **Sans réentraîner**, la courbe d'événements sert
  de **critère de sélection et de calage** : calculer la courbe vidéo (DINOv2 ou simple différence de trames) et la courbe de
  chaque musique candidate (analyse d'énergie déjà dans `analyser_musique.py`), prendre le candidat qui **maximise la
  corrélation** après décalage/recoupe, caler les coupes sur les temps forts. Effort S ; ne touche pas le montage détaillé
  (autre fichier).
- **VeM** [RÉSUMÉ] (2511.09585) : musique par diffusion latente avec **aligneur de transitions-temps**
  (changements de scène ↔ battements) ; jeu de données **issu de publicités e-commerce** (contrainte de synchro plus
  stricte) ; nouvelles métriques de rythme. **Diff-V2M** [RÉSUMÉ] (2511.09090, dépôt None) : la **fonction de détection
  d'attaques basse résolution** est la meilleure représentation du rythme parmi mel-spectrogramme, tempogramme et ODF.
  **VIBE** (2608.30125, récompenses sur contraintes vérifiables : tempo, tonalité). **Video-Robin** (2604.17656).
  **MVAA** (2506.18881, l'inverse : recaler la **vidéo** sur la musique par images clés sur les battements + inpainting ;
  relève du montage, 4090 en 10 min de réglage).

### G2. Doublage, voix, locuteur [LU/RÉSUMÉ]
- **JUST-DUB-IT** [LU] (2601.22143, janvier 2026) : doublage vidéo → vidéo avec un **modèle audio-vidéo de fondation +
  LoRA légère** : le modèle produit audio traduit **et mouvement de visage synchronisé**. Données auto-générées : vidéos où
  un locuteur **change de langue dans un même plan**, puis inpainting du visage et de l'audio de chaque moitié. Constats
  utiles : **compromis identité/prononciation** (sans contexte, la voix dérive ; avec le seul audio source, « fuite de
  prosodie » : le texte cible prend le rythme de la langue source) ; **masque fin conscient du latent** (le champ réceptif du
  VAE laisse fuiter la trajectoire des lèvres originales dans les jetons voisins) ; augmentation phonétique des lèvres.
  Dépôt justdubit/just-dub-it, **NOASSERTION**, 263 étoiles. Base non nommée dans les passages lus.
- **X-Dubbing** [RÉSUMÉ] (2610.32042) et **PS-TTS** [RÉSUMÉ] (2604.09111) : le **texte traduit est reparaphrasé pour tenir la
  durée de l'original (isochronie)** avant la synthèse ; PS-TTS ajoute la **synchronisation phonétique** (voyelles
  proches) et mesure aussi le français. **InstructDubber** [RÉSUMÉ] (2512.17154) : un LLM multimodal dicte débit et émotion.
  **CoSyncDiT** (2604.12292), **DiFlowDubber** (2603.14267), **VSpeechLM** (2511.22229) : TTS conditionné par vidéo (modèles appris).
- **Pour nous** : H3 produit la voix **avec** l'image ; « doubler » un film en anglais = **re-tourner le plan** avec la
  réplique traduite et paraphrasée pour la même durée, mêmes images clés, même graine si possible. La littérature
  d'isochronie dit comment écrire cette réplique (durée, nombre de syllabes, voyelles ouvertes aux moments de bouche ouverte).
- **Voix constante** : UnityShots (jeton de locuteur de référence à chaque plan), JoyAI-Echo (indices de locuteur dérivés de
  l'audio filtré), Omni-Customizer / Identity as Presence (timbre lié à l'identité) : **un échantillon sonore de référence
  par personnage, injecté à chaque plan**. H3 Ref2VA accepte des **sons de référence** (10-qualite-h3) : hypothèse à tester.

### G3. Bande-son complète [RÉSUMÉ]
- **BackgroundMellow** (2607.11364) : architecture maître-spécialistes qui décompose un récit en couches audio, avec **module
  prédisant début, durée et niveau relatif** de chaque couche ; **ControlFoley** (2604.15086, Apache-2.0, 158 étoiles :
  foley contrôlé par texte, vidéo **et audio de référence**) ; **OmniSonic** (2604.04348, sons à l'écran, hors-champ et
  parole) ; **Step-by-Step V2A** (2506.20995, couches de sons ajoutées une à une avec un guidage négatif pour ne pas
  répéter). Foley-Omni est en 07 §6.6. **[MON AVIS]** : l'idée à retenir est le **plan sonore en couches** (ambiance,
  effets, musique, voix) décrit dans le plan, comme `overall_soundscape` / `non_diegetic_music` de H3 le font déjà côté
  prompt.

## 10. Ce que la littérature ne donne pas (et ce que ça implique)

- **Pas de preuve à l'échelle d'un long métrage** : le plus grand banc a 50 plans par épisode ; Soap2Soap (2605.17423) parle
  de « centaines de plans » pour des épisodes entiers mais en vidéo vers vidéo ; CineDance-1M (2606.09639) décrit des vidéos de
  92,8 s en moyenne et 24,2 plans [RÉSUMÉ]. **Un film de 90 min reste hors de toute preuve publiée.**
- **Ordre de grandeur de coût** [ESTIMÉ] : à ~5 s par plan, 90 min ≈ 1 080 plans ; au temps moteur mesuré en 10-qualite-h3
  (≈ 290 à 350 s par plan 5,17 s, 1 candidat), cela donne environ 90 heures de GPU par jeu complet, ×2 avec deux candidats,
  réparties sur deux ou trois GPU. Ce n'est donc pas impossible, mais cela impose : état durable et reprise (déjà dans
  `filmMoteur.ts`), parallélisme par scène, **images clés vérifiées avant** de dépenser un plan vidéo, brouillons 8 étapes
  d'abord, devis au crédit avant lancement.
- **Plafond actuel** : `MAX_PLANS = 12`. Passer au film long suppose un niveau **scène** entre film et plan
  (film → actes → séquences → scènes → plans), avec une banque d'entités **par film** et un décor/lieu par scène (CANVAS).
- **Licences** : les meilleures recettes d'orchestration (CineCrew, VideoMemory, FilmWorld) n'ont **pas de code publié** : on
  s'inspire du papier, on n'a rien à copier, donc rien à relire côté licence ; les dépôts existants sont `None` ou
  `NOASSERTION` à l'exception de Deep Forcing et ControlFoley (Apache-2.0).

## 11. Les 12 techniques à implémenter d'abord (classées)

Critères : gain attendu sur le film (cohérence, taux de prises acceptées, coût GPU) × faisabilité **sans réentraîner H3** ×
proximité du code existant × risque de licence. Tout est **[MON AVIS]** sauf les chiffres cités.

| # | Technique | Source | Où | Effort |
|---|---|---|---|---|
| 1 | Banque d'entités pré-générée avec états | EntityMem [LU], VideoMemory [LU], CineCrew [LU] | `film.ts`, `cast.ts`, `stills.ts` | M |
| 2 | Juge d'identité en paires + porte de fidélité + banc de continuité | EntityBench [LU], MSVBench [LU] | `juge.ts`, `controle.ts`, tests | M |
| 3 | Images clés d'abord, paires début/fin, ancres vérifiées avant la vidéo | STAGE, ATS, KeyID, CineCrew | `filmMoteur.ts`, `stills.ts`, `h3.ts` FL2VA | M |
| 4 | Plan « FilmDSL » à trois couches, coupe ≠ continuation | CineCrew [LU], SSRS | `film.ts` | S–M |
| 5 | Rushes typés et réparation ciblée, bornée | CineCrew [LU], CANVAS, FilmWorld | `juge.ts`, `filmMoteur.ts` | M |
| 6 | Banque de voix : un son de référence par personnage | UnityShots, JoyAI-Echo, Omni-Customizer | `h3.ts` Ref2VA, `film.ts` | S–M |
| 7 | Garde de dérive et ancrage sur l'image canonique | Clean Forcing [LU], ATS, Deep Forcing | `controle.ts`, `filmMoteur.ts` | S |
| 8 | Rétroaction typée du juge vers la réécriture + brouillon interactif | RAPO++ [LU], TIDE, ProactGen | `reecritureH3.ts`, `competences.ts` | S–M |
| 9 | Sélection des images-références parmi les plans rendus (CLIP + esthétique, puits + fenêtre) | StoryMem [LU] | `filmMoteur.ts` | S |
| 10 | Caméra : énumération 17 mouvements × taille × angle, contrôle géométrique | ACaM [LU], ShotBench [LU], ShotVerse [LU] | `film.ts`, `controle.ts` | M |
| 11 | Calage de la musique par courbes d'événements | V2M-Zero [LU], VeM, Diff-V2M | `musique.ts`, `analyser_musique.py` | S |
| 12 | Doublage par ré-écriture isochrone et re-tournage du plan | X-Dubbing, PS-TTS, JUST-DUB-IT [LU] | `film.ts` (réplique), `h3.ts` | M |

### T1. Banque d'entités pré-générée avec états
**Croquis.** Nouvelle structure `EntiteBanque {id, type: personnage|accessoire|lieu, etats: [{attributs, image, valide}]}`
stockée dans la prise « film ». À la planification (`film.ts`), le LLM sort aussi un **calendrier d'entités par plan**
(quelles entités paraissent dans quel plan, dans quel état). Avant toute vidéo : (a) pour chaque personnage, portrait
**sur fond uni, détouré, nom écrit en bas** via `stills.ts` (FLUX.2, multi-références) ; (b) pour chaque lieu, panorama
recadré en gauche/centre/droite ; (c) un agent « vérification » (VLM) contrôle chaque image et retente avec un autre fond ;
(d) en cas de changement d'état prévu (âge, tenue, blessure) : **nouvelle entrée générée avec les anciennes images en
entrée** (VideoMemory). Au tournage, le plan reçoit en Ref2VA les portraits des personnages prévus + l'angle de lieu
choisi, et le prompt n'a plus qu'à citer le **nom** (la description complète vit dans la banque).
**Prompt de vérification** : « Cette image montre-t-elle une seule personne, visage net, fond uni, nom lisible, conforme à
{description} ? Réponds en JSON {ok, defauts[]}. »
**À mesurer** : présence du personnage prévu par plan (cible : dépasser les 84,9 % de la mémoire par plans passés, viser les
96,7 % publiés) ; identité LLM entre plans éloignés ; objets (le détourage donne un « effet autocollant » sur les
objets : tester séparément). Coût : nombre d'images supplémentaires par film. Risque : un défaut de la banque se propage à
tout le film, d'où la vérification **et** une validation humaine rapide dans l'interface (3 vignettes à approuver).

### T2. Juge d'identité en paires + porte de fidélité + banc de continuité
**Croquis.** Deux étages dans `juge.ts` : (1) **porte de fidélité** : l'entité prévue est-elle présente et correctement
rendue dans ce plan ? (détection par GroundingDINO ou par question VLM sur une planche ; seuil à calibrer) ; (2)
**comparaison par paires** : image ancre (portrait de la banque) contre un recadrage du personnage dans le plan, question
« Est-ce la même personne ? » avec consigne de citer visage, coiffure, tenue. DINO/ArcFace restent en couche 2 pour
l'alerte bon marché, **jamais seuls**. Le résultat alimente un score de film (par distance de réapparition). **Banc
maison** « EntityBench-lite » : 10 scripts de 8 à 20 plans avec calendrier d'entités, exécutables en brouillon 8 étapes,
rejoués à chaque changement de recette (c'est ce qui manque pour savoir si T1, T3, T5 servent).
**À mesurer** : accord du juge avec 50 paires étiquetées à la main (aussi bien « même » que « pas la même »), taux de faux
rejets ; décroissance de la cohérence en fonction de l'écart de réapparition, avant/après T1.

### T3. Images clés d'abord, paires début/fin, ancres vérifiées
**Croquis.** Pour chaque plan : `cle_debut` (et `cle_fin` si le mouvement est grand), composées avec les références de T1 ;
**contrôle sur l'image** (présence, identité, cadrage conforme à l'énumération caméra, accessoires requis/interdits) pour
un coût d'image ; **seulement ensuite** FL2VA (1re/dernière image) en brouillon 8 étapes, puis rendu `h3-max` pour les plans
retenus. Retouche locale de l'image clé (édition d'image, par ex. Qwen-Image-Edit si disponible, ou FLUX.2 avec références) quand le défaut est d'identité, au lieu de régénérer la vidéo
(KeyID). Les plans d'un même lieu peuvent être générés **en lot** dans un même contexte (idée « batch keyframe » de
Soap2Soap, grille d'images clés générées ensemble) pour stabiliser l'éclairage.
**À mesurer** : prises vidéo régénérées par plan accepté (avant/après), coût GPU par plan accepté, temps jusqu'à la
première validation par l'utilisateur. Risque : H3 FL2VA et l'image de fin forcée peuvent raidir le mouvement : mesurer sur
10 plans d'action.

### T4. Plan FilmDSL à trois couches
**Croquis.** Faire évoluer `PlanFilm` : `action` {quoi, émotion, dialogue}, `mise_en_scene` {taille, angle, mouvement
(énumération T10), lumière, entites[], lieu_ref, accessoires_requis[], accessoires_interdits[], `lien`:
'coupe'|'continuation'|'raccord_geste'}, `rendu` {prompt_cle, prompt_video, negatif, duree, graine}. Le LLM remplit les
deux premières couches ; **le code compile la troisième** (réécrivain H3 validé, guide officiel). Opérateur de dernière
image seulement si `lien = continuation` (CineCrew), et dans ce cas la dernière image est **exclue de la banque de
références** (EntityMem). Niveau supérieur : `scene` entre film et plan, avec un lieu par scène, pour lever le plafond de
12 plans.
**À mesurer** : taux de plans dont la compilation passe les validateurs H3 du premier coup ; nombre de plans par film
atteint sans dégradation.

### T5. Rushes typés et réparation ciblée, bornée
**Croquis.** Le juge rend, en plus du verdict A/B, un `rapport {defauts: [{type, plan, preuve}]}` avec types fermés :
`derive_identite`, `accessoire_apparu|disparu|teleporte`, `image_cle_non_respectee`, `instabilite_temporelle`,
`camera_non_conforme`, `texte_parasite`, `son_incoherent`. Chaque type a **une** action de réparation et un plafond :
identité → retouche d'image clé (T3) ; accessoire → mise à jour du champ `accessoires_*` + prompt ; instabilité → autre
graine puis durée plus courte ; caméra → simplifier le mouvement. Journal d'exécution dans le « Rulebook » du film ; plafond
de R reprises par plan, puis **sortie propre** (« je garde la meilleure prise et je te le signale »). Garde existante :
le contrôle déterministe passe toujours avant ; un juge en panne ne bloque jamais le film.
**À mesurer** : taux de réparation réussie par type ; nombre moyen de reprises ; crédits dépensés en reprises ; taux de
fausses alarmes (le VLM voit mal les artefacts : Artifact-Bench en 07 → réserver le juge aux types sémantiques).

### T6. Banque de voix
**Croquis.** À la première réplique d'un personnage, garder l'extrait audio retenu (le premier plan parlé sert de source) comme `voix_ref` du personnage ; l'injecter en **son de référence** à chaque plan suivant du
personnage via Ref2VA ; compléter par la direction de voix dans le prompt. Vérifier la voix par **similarité d'embeddings
de locuteur** entre plans (ECAPA ou équivalent).
**À mesurer** : similarité de locuteur inter-plans avec/sans référence ; intelligibilité (transcription Whisper déjà
présente dans `whisper.ts`) ; effet de la référence sonore sur le visage (fuite de parole, Omni-Customizer). **Hypothèse non
vérifiée** : que Ref2VA tienne vraiment le timbre ; premier test à faire sur 3 personnages × 6 plans.

### T7. Garde de dérive et ancrage
**Croquis.** `controle.ts` ajoute une **mesure de dérive** par prise (saturation moyenne, netteté, similarité DINO de la
première et de la dernière cinquième partie ; seuils calibrés sur nos prises) et, pour un plan `continuation`, **interdit de
chaîner plus de N plans** sans repasser par l'image canonique (ancrage). Les plans enchaînés reçoivent comme première image
la dernière image du précédent **et** les références canoniques en Ref2VA.
**À mesurer** : valeur de la dérive sur chaînes de 3, 5, 8 plans avec/sans ancrage ; seuils.

### T8. Rétroaction typée juge → réécriture + brouillon interactif
**Croquis.** Dans `reecritureH3.ts`, un paramètre `retours: Defaut[]` (issus de T5) qui amène le LLM à réécrire **la
phrase concernée**, pas le prompt entier ; consignes négatives issues de la liste de « fautes courantes » ; flux « brouillon
8 étapes d'abord » : l'utilisateur voit deux brouillons, un seul clic « garder / change X » (ProactGen), et seulement alors
on lance `h3-max`. Les paires (brut → corrigé → verdict) sont archivées pour affiner plus tard un petit réécrivain (RAPO++
étage 3).
**À mesurer** : nombre de rondes avant acceptation ; part des brouillons acceptés tels quels ; coût LLM par plan.

### T9. Sélection des références parmi les plans rendus
**Croquis.** Après chaque plan accepté, extraire des images candidates, retenir celles qui diffèrent assez (CLIP < seuil
dynamique), filtrer par score esthétique, et proposer à la banque de l'entité (T1) une **vue supplémentaire** (pas un
remplacement : les références pré-générées restent prioritaires, EntityMem). Politique « puits + fenêtre » : les 2-3
premières références restent, les suivantes tournent.
**À mesurer** : A/B « références pré-générées seules » contre « + vues extraites » sur le banc de T2.

### T10. Caméra énumérée et mesurée
**Croquis.** `camera` devient {mouvement ∈ 17 classes, taille, angle, focale}. Interface : liste visuelle (vignette
animée). Compilation en dialecte H3 par le réécrivain. Contrôle `controle.ts` : mouvement estimé par **flux optique /
homographie** (et MoGe en option) comparé à l'intention ; tolérance par classe ; jamais le juge VLM pour ce point.
Planificateur multi-plans à la ShotVerse : le LLM garde un **repère de scène** (où est la caméra par rapport au décor) pour
que deux plans du même lieu soient cohérents.
**À mesurer** : taux de conformité par classe de mouvement sur H3 (les classes mal suivies ressortiront, il faudra les
retirer de l'interface ou les compenser en prompt) ; spike PartiCam à envisager si la conformité est faible.

### T11. Calage de la musique
**Croquis.** `musique.ts` : calculer la courbe d'événements du montage assemblé ; générer N=3 à 4 musiques (≈ 27 s de calcul
pour 60 s de musique sur la 5090, mesuré en 10-qualite-h3) ; calculer leur courbe ; choisir la meilleure corrélation après le meilleur décalage ; proposer
aux monteurs de caler les coupes sur les temps forts (voir le fichier jumeau pour le montage).
**À mesurer** : corrélation des courbes avant/après sélection ; préférence interne en test à l'aveugle (10 extraits).

### T12. Doublage isochrone par re-tournage
**Croquis.** Pour une version EN/ES : le LLM **paraphrase la traduction** pour tenir la durée de chaque réplique
(consigne : même durée en secondes, mêmes pauses, voyelles ouvertes sur les mots longs si possible) ; re-tournage du plan à
partir de la **même image clé** et avec la voix de référence (T6). Pas de TTS superposé : le visage et la voix sont générés
ensemble par H3.
**À mesurer** : écart de durée de la réplique rendue vs cible ; synchronisation labiale (SyncNet, 07 §8.7) ; taux de
re-tournages nécessaires.

## 12. Ce que je recommande de ne pas faire maintenant

- Entraîner ou affiner quoi que ce soit : StoryMem, FilmWeaver, OneStory, MovieGrid, ShotVerse (Controller), Clean Forcing
  demandent des LoRA ou des dizaines de GPU-jours sur des bases Wan/LTX/HoloCine, pas H3.
- Intégrer du code `None` (EntityBench, ShotBench, ShotVerse, MovieGrid, UnityShots, RAPO, SoliReward, Diff-V2M, KeyID,
  SCMAPR) : on lit, on réimplémente l'idée, on ne copie pas.
- Utiliser un juge VLM pour la caméra, pour les artefacts fins, ou DINO/CLIP seul pour l'identité.
- Chercher la mémoire 3D de monde (OctWorld et suivants) : cible différente (caméra libre).
- Remplacer le Producteur par un agent « tout-en-un » : MSVBench le classe en bas de tableau.

## 13. Spikes proposés (aucun lancé)

1. **Banque d'entités** : 3 scripts × 12 plans en brouillon 8 étapes, avec/sans T1 ; mesurer présence et identité LLM par paires.
2. **Ref2VA son de référence** : un personnage, 6 plans, avec/sans extrait de référence ; similarité de locuteur.
3. **Conformité de caméra de H3** : 17 mouvements × 3 graines ; mesure géométrique ; carte des classes fiables.
4. **Dérive en chaîne** : 3/5/8 plans enchaînés avec et sans ancrage ; mesure de T7.
5. **Calage musique** : 10 montages × 4 musiques ; corrélation et test à l'aveugle.

## 14. Index des articles (ajoutés par ce rapport)

Lus [LU] : 2609.07720 CineCrew · 2601.03655 VideoMemory · 2605.15199 EntityBench · 2512.19539 StoryMem · 2603.11421 ShotVerse ·
2607.03043 ACaM · 2506.21356 ShotBench · 2603.11042 V2M-Zero · 2510.20206 RAPO++ · 2601.22143 JUST-DUB-IT · 2602.23969 MSVBench ·
2610.25634 Clean Forcing.

Résumé seul [RÉSUMÉ] : 2607.19038 FilmWorld · 2604.13452 CANVAS · 2610.15512 SSRS · 2512.12372 STAGE · 2605.23508 DrawVideo ·
2605.17423 Soap2Soap · 2606.09639 CineDance · 2512.07802 OneStory · 2512.11274 FilmWeaver · 2609.06373 MovieGrid ·
2606.21661 UnityShots · 2608.23383 JoyAI-Echo-1.5 · 2609.34502 SubjectAnchor · 2512.05081 Deep Forcing · 2605.20476 ATS ·
2605.20910 FlowLong · 2602.14027 FLEX · 2607.27110 FreqForcing · 2605.06509 FreeSpec · 2606.22370 · 2608.16154 KeyID ·
2608.22819 · 2603.17889 · 2605.17488 · 2511.00511 · 2609.11507 · 2603.29931 Gloria · 2609.28813 CinematicVQA · 2603.18448 SLU-Suite ·
2606.24636 CineCap · 2510.02423 RefineShot · 2603.13119 · 2604.09201 CT-1 · 2609.39504 PartiCam · 2604.09429 · 2605.30774 ·
2606.20774 · 2606.15534 · 2610.15098 TIDE · 2610.22608 ProactGen · 2608.12290 · 2603.03505 PhyPrompt · 2604.05489 SCMAPR ·
2603.01509 · 2608.16717 PersonaShot · 2510.26412 LoCoT2V-Bench · 2512.22170 SoliReward · 2601.04033 REACT · 2602.05202 GT-SVJ ·
2601.04153 Diffusion-DRF · 2511.09585 VeM · 2511.09090 Diff-V2M · 2608.30125 VIBE · 2604.17656 Video-Robin · 2506.18881 MVAA ·
2610.32042 X-Dubbing · 2604.09111 PS-TTS · 2512.17154 InstructDubber · 2604.12292 · 2603.14267 · 2511.22229 · 2607.11364
BackgroundMellow · 2604.15086 ControlFoley · 2604.04348 OmniSonic · 2506.20995 · 3D : 2609.03919 · 2603.23413 · 2609.37690 ·
2510.14945 · 2606.09828 · 2607.21848 · 2609.34221 · 2610.23423.

## 15. Ce qui n'est pas fait

- Aucune reproduction, aucune mesure sur GB10 ou 5090 ; les gains attendus sont ceux des auteurs, sur d'autres modèles.
- 12 articles lus en passages ; les autres au niveau du résumé (marqués). Aucun article lu en entier. Les tableaux de résultats
  de CineCrew et de ShotVerse n'ont pas été lus.
- Licences des poids non relues ; licence de code obtenue via l'API GitHub non authentifiée seulement.
- Accélération/distillation de vidéo (demandée dans le thème) : **aucun nouvel article ajouté**, 07 axe 1 couvre le sujet
  (Sol-H3, PDMD, rCM, TurboDiffusion, caches, quantification) et je n'ai pas trouvé mieux à y ajouter dans le temps imparti.
- Montage, publicité, mixage final : fichier jumeau.
