# Creative « triple A » : backlog priorisé et plan d'intégration (03/11/2026)

Sources : `recherche/23-grammaire-promos-ia.md` (101 promos analysées), `recherche/24-etat-de-lart-creative-2026-11.md` et ses annexes (concurrents, libre, littérature, remue-méninges), `docs/FEUILLE-DE-ROUTE-MAITRE.md` (audit 35 variables, issues #1 à #57). Ce document **ne remplace pas** la feuille de route maître : il ajoute ce que la recherche du 03/11 a trouvé, le classe, et renvoie aux issues existantes quand elles couvrent déjà le sujet. Personne n'écrit de code à partir d'ici sans la mesure d'acceptation de la ligne.

## 0. Les réponses demandées, en clair

| Question | Réponse |
|---|---|
| **Blender piloté par l'agent est-il indispensable au triple A ?** | **Non.** Les bancs 2025-2026 (BlenderGym, 3DHarnessBench, BlenderWorld) montrent que les agents ratent encore des opérations simples ; Gemini 4 Argon et GPT-6.1 Sol arrivent à la même conclusion. Le triple A vient de la fiabilité du parcours, des recettes et de l'édition vidéo. Blender devient utile **plus tard**, en **travailleur à gabarits** (5 opérations bornées : poser un objet, une caméra, une lumière studio, une trajectoire, rendre des passes) pour les packshots exacts et pour guider la vidéo (TA16). Avant cela, une **scène 3D légère dans le navigateur** (la visionneuse de Relief existe) suffit pour poser objet et caméra (TA15). |
| **Que prendre de FilmCraft ?** | Des **contrats**, aucun code (Rust, 440 k lignes) : validation indexée des opérations groupées, aperçu en lecture seule sérialisé, rapport d'export qui dit ce qui est perdu, fermeture des dépendances d'une sélection exportée, unités séparées (fréquence audio ≠ cadence vidéo), verrou d'écriture par projet (TA24). **Correction** : son `command_batch` n'est pas atomique ; notre `enUnePas` garde sa propre atomicité. Et l'idée d'ensemble : un **registre de commandes auto-descriptif** partagé entre l'interface et l'agent (recherche/13 §2). |
| **Quelles technologies développer nous-mêmes en assemblant du libre ?** | (1) **Recettes et grammaire de promo** codées dans l'`EditPlan` (notre savoir, personne ne le vend) ; (2) **compilateur de prompts par mode H3** + règles distillées (TIDE) jugées sur le rendu ; (3) **couches d'effets VFX** : SAM 2.1/ViTMatte (fait) + Wan2.2-Fun-Control/VACE-Fun + éléments RGBA Wan-Alpha + lumière LiveLight/Relit-LiVE + sabres procéduraux ; (4) **chaîne voix** : TTS local à émotion (Qwen3-TTS, CosyVoice 3, Chatterbox réglé) + lip-sync MuseTalk/LatentSync ; (5) **recadrage suivi** sur SAM 2.1 ; (6) **ordonnanceur de prises** (budget adaptatif, ancre d'abord, juge) ; (7) **MCP distant** sur nos 22 outils. Tout sous licence permissive vérifiée ligne par ligne (annexes 24). |
| **Quel coût par seconde sur nos GPU, quelle stratégie de prix ?** | Coût complet estimé **0,002 à 0,008 CAD par seconde produite**, **0,006 à 0,025 CAD par seconde finie** prises ratées comprises (recherche/24 §2.4). Prix proposé : **brouillon 2 crédits/s (0,02 $), finale 10 crédits/s retenue (0,10 $) avec deux prises et le juge inclus**, Studio gratuit, LLM au jeton, forfait 29 $/mois avec 150 s finales (§4). Marge brute 75 à 95 % ; contrainte réelle = **capacité GPU**, pas le coût. |
| **Qu'est-ce qu'une interface visuellement et ergonomiquement triple A ?** | Huit règles mesurables au §5 : deux vitesses, pas de champ vide (vignettes animées), rideau avant/après universel, attente lisible avec coût verrouillé, 60 i/s sacrés, une seule grammaire d'actions, système visuel strict, accessibilité et mobile. |

## 1. Le backlog classé (impact × effort)

Impact 1-5 (effet sur « simple et extrêmement puissant » et sur l'écart avec Higgsfield/OpenArt). Effort : S ≤ 1 semaine-agent, M 2-3, L 4-6. Score = impact ÷ (S = 1, M = 2, L = 4). Issue : numéro GitLab existant quand il couvre le sujet (sinon « nouvelle »).

| Rang | Id | Chantier | Imp. | Eff. | Score | Issue |
|---|---|---|---|---|---|---|
| 1 | **TA1** | Pika H3 Flex sur nos bases H3 (mesure, puis recettes `h3-flex` et brouillon fidèle) | 5 | S | 5,0 | nouvelle (+ #32) |
| 2 | **TA25** | Films promo refaits selon recherche/23 (contrôles automatiques) | 5 | S | 5,0 | nouvelle |
| 3 | **TA2** | Gabarit « Promo qui claque » + 20 recettes complètes illustrées | 5 | M | 2,5 | #49, #15 |
| 4 | **TA4** | Voix expressive locale + audio fourni + voix off phrase par phrase | 5 | M | 2,5 | #24, #25 |
| 5 | **TA19** | Interface triple A (8 règles du §5) | 5 | M | 2,5 | #53, #50, #52 |
| 6 | **TA20** | Prix à la seconde retenue, affichage en dollars, devis unifié | 4 | S | 4,0 | #36 |
| 7 | **TA3** | Compilateur de prompts par mode H3 + banc 24 briefs + règles TIDE | 4 | M | 2,0 | nouvelle |
| 8 | **TA5** | Un projet, trois formats (recadrage suivi + régénération verticale) | 4 | M | 2,0 | #42, #21 |
| 9 | **TA6** | « Change seulement le plan 2 » : invalidation minimale | 4 | M | 2,0 | #10 |
| 10 | **TA8** | Lip-sync : MuseTalk en aperçu, LatentSync en finale | 4 | M | 2,0 | #26 |
| 11 | **TA7** | MCP distant + API publique (idempotence, plafond, devis) | 4 | M | 2,0 | #46, #47 |
| 12 | **TA9** | Agrandissement à l'export (FlashVSR+, SeedVR2 témoin) | 3 | S | 3,0 | #33 |
| 13 | **TA17** | ACE-Step 1.5 en complément de Music3 (structure imposée, réparation) | 3 | S | 3,0 | nouvelle |
| 14 | **TA24** | Contrats repris de FilmCraft | 2 | S | 2,0 | nouvelle |
| 15 | **TA11** | Socle VFX : Wan2.2-Fun-5B-Control → VACE-Fun (retrait, fond, profondeur) | 5 | L | 1,25 | #37, #38, #39, #40 |
| 16 | **TA12** | Couches d'effets : éléments RGBA (Wan-Alpha v2), sabres procéduraux, bibliothèque d'explosions | 4 | M | 2,0 | #7, #41 |
| 17 | **TA18** | Ordonnanceur de prises : budget adaptatif, ancre d'abord, références complémentaires | 3 | M | 1,5 | #44, #30 |
| 18 | **TA10** | Lien de revue client horodaté | 3 | M | 1,5 | #12 |
| 19 | **TA13** | Relight vidéo (LiveLight contre Relit-LiVE) | 3 | M | 1,5 | nouvelle |
| 20 | **TA14** | Trajectoires dessinées (Wan-Move) | 3 | M | 1,5 | nouvelle |
| 21 | **TA15** | Prévisualisation 3D dans le navigateur → première/dernière image et profondeur | 3 | M | 1,5 | nouvelle |
| 22 | **TA23** | « Refaire comme ça » : montage d'après une vidéo de référence (façon Katana) | 4 | L | 1,0 | nouvelle |
| 23 | **TA21** | Expérience « Producteur de nuit » | 3 | M | 1,5 | nouvelle |
| 24 | **TA22** | Expérience « film document vivant » | 3 | L | 0,75 | nouvelle |
| 25 | **TA16** | Travailleur Blender à gabarits | 2 | M | 1,0 | nouvelle |

Ordre d'exécution (dépendances comprises) : **vague A** TA1, TA25, TA20, TA9, TA24 ; **vague B** TA2, TA4, TA3, TA19 (en continu) ; **vague C** TA5, TA6, TA8, TA7, TA17 ; **vague D** TA11, TA12, TA13, TA14, TA18, TA10 ; **vague E** TA15, TA23, TA21, TA22, TA16.

## 2. Plan d'intégration par élément

Chaque fiche : ce que voit l'utilisateur ; ce qu'on assemble ; où ça se branche ; mesure d'acceptation ; machine.

### TA1 — Pika H3 Flex sur nos bases H3
- **Utilisateur** : la qualité cinéma arrive en un peu plus d'une minute au lieu de cinq ; les plans peuvent durer 15 s ; le brouillon devient **le même modèle** que la finale (fin de « brouillon ≠ finale », #32).
- **Assemblage** : adaptateurs ComfyUI `comfy/loras/pika_h3_flex_fl2va_comfy_bf16.safetensors` et `..._ref2va_...` de [Pika-Labs/Pika-H3-Flex](https://huggingface.co/Pika-Labs/Pika-H3-Flex) (non protégés, licence H3 Community, la même que nos poids actuels) posés sur `minimax_h3_fl2va_pruned_int8_convrot` et `minimax_h3_ref2va_*` déjà sur pc1 ; workflows Comfy-Org `video_pika_h3_flex_{t2v,fl2va,ref2va}.json` ; contrat d'échantillonnage du README : **6 évaluations, nœuds 1000/750/500/250/100/40/0, décalage vidéo 12, audio 3, bruit intermédiaire frais** (un « 6 étapes » générique ne le reproduit pas).
- **Branchement** : nouvelles recettes `h3-flex` et `h3-flex-ref` dans `app/server/engine.ts` / compilateur de graphes (LoraLoader + sigmas personnalisés), secondes mesurées dans `NEXORA_MOTEUR_SECONDES`, devis dans `credits.ts`. Fichiers sur `/run/media/pc1/Infrastructure/NexoraStudioWork` (disque racine de pc1 à 96 %), lien dans `models/loras/`. Coordonner avec l'agent qui entretient le ComfyUI de pc1 (il n'est pas à nous) et passer par la file GPU séquentielle.
- **Acceptation** : banc des prompts de recherche/10 (dragon, karaté, humains) + 8 prompts de promo de recherche/23 §5 ; temps de bout en bout ≤ 40 % de `h3-max` ; juge visuel et fondateur à l'aveugle : Flex ≥ `h3-max` sur ≥ 50 % des paires ; son présent et synchronisé ; Ref2VA garde le visage `@` sur 2 plans. Si échec : garder `h3-max`, rien ne change.
- **Machine** : 5090 d'abord (bases présentes) ; GB10 ensuite (FastH3 NVFP4 est une autre base : l'adaptateur ne s'y applique pas tel quel, vérifier).

### TA25 — Films promotionnels refaits selon la grammaire
- **Utilisateur (le public)** : un film « capacités infinies » (dragon, explosion, bataille spatiale, duel au sabre) et un film OPSYS-AI qui claquent.
- **Assemblage** : recettes A et B de recherche/23 §5-§6 ; plans H3 (puis Flex si TA1 passe) ; Music3 avec la consigne de §4.7 ; voix diégétiques H3 + échantillons vocaux ; contrôles du §7 ajoutés à `marketing/nexora/refonte-medias/revue.py` (premier plan ≤ 1 s, médiane 1,5-2,5 s par plan, drop ≤ 10 s, trous musicaux, narration ≤ 25 %, carton ≤ 3,5 s, 9:16 natif).
- **Acceptation** : tous les contrôles verts **et** ≥ 8/10 au regard du fondateur (sa règle). **Machine** : file GPU existante. **Agents** : ceux qui tournent les films aujourd'hui.

### TA2 — Gabarit « Promo qui claque » + 20 recettes complètes
- **Utilisateur** : dans Explorer, 20 cartes (pub restaurant, produit, événement, témoignage, bande-annonce, « capacités infinies », immobilier, recrutement…) avec un **exemple rendu chez nous** qui s'anime au survol et trois champs ; résultat reproductible avec ses propres ingrédients.
- **Assemblage** : compétence `app/server/nexora/competences/promo-spectaculaire.md` (les 16 règles) ; contraintes typées dans l'`EditPlan` (`intent.energy_curve`, rythme cible, trous musicaux, révélation à 70-85 %) vérifiées par `critique` ; recettes en données (`recettes/*.json` : plans types, durée, tempo, cartons, voix, musique) ; les 8 « modèles prêts » actuels deviennent 20.
- **Acceptation** : 20 recettes × 3 essais par un débutant avec ses propres médias ; ≥ 80 % jugés « publiables » par le juge et le fondateur ; aucune recette ne sort sans son exemple rendu. Remplace l'idée de « centaines de presets » (refusée, recherche/24 §10).

### TA4 — Voix expressive
- **Utilisateur** : choisir une voix (bibliothèque ou la sienne avec consentement), une énergie (« bande-annonce », « urgent », « sourire », « intime »), ou déposer son propre audio ; voix off posée phrase par phrase sur les coupes.
- **Assemblage** : réglages Chatterbox « dramatique » (`exaggeration` ≈ 0,7, `cfg_weight` ≈ 0,3) **tout de suite** sur pc5 ; casting à l'aveugle Qwen3-TTS 1.7B (Apache-2.0), CosyVoice 3 (Apache-2.0), Drama 3 local (déjà mesuré), référence ElevenLabs v4 ; textes et références enregistrées **dans le style visé** (annexe C §5) ; une phrase par fichier, pauses de 0,15-0,25 s au montage, ducking 4 à 6 dB (pas 10), Whisper pour l'erreur de mots.
- **Branchement** : service TTS de pc5 (port 8190) ; rôle « voix » du Producteur ; piste voix de l'`EditPlan` ; issue #24/#25.
- **Acceptation** : le fondateur choisit à l'aveugle une voix locale ≥ ElevenLabs sur « énergie » pour 4 textes sur 6 ; EMR ≤ 0,03 ; aucune voix off au-delà de 25 % de la durée d'une promo.

### TA19 — Interface triple A : voir §5.

### TA20 — Prix et devis : voir §4. Branchement : `credits.ts` (tarif par recette et par seconde retenue), `usage.ts` (inchangé), affichage « ≈ 0,60 $ » à côté des crédits, devis unifié #36.

### TA3 — Compilateur de prompts par mode H3
- **Utilisateur** : il écrit trois lignes à l'arrache ; il voit « ce que le réalisateur a compris » (sujet, action, caméra, lumière, son) en cinq puces modifiables.
- **Assemblage** : le LLM produit une **intention typée** (sujet, action observable, état initial/final, caméra, lumière, son, contraintes immuables, références) ; le code la compile dans le dialecte du mode (guides officiels `base-en.txt`, `ref-en.txt` : Ref2VA a ses champs `subject_definitions`, `summary`, `retention_analysis`, `detailed_description` ; FL2VA veut un plan continu cohérent avec les deux images) ; une bibliothèque versionnée de **règles gagnantes** distillées hors ligne (méthode TIDE, arXiv 2610.15098) ; double évaluation à la VPO (fidélité au brief, qualité de la vidéo).
- **Branchement** : `app/server/nexora/promptH3.ts`, `reecritureH3.ts`, banc `app/server/nexora/bench/`.
- **Acceptation** : banc de 24 briefs, même budget de prises : préférence du compilateur ≥ 60 % contre le réécrivain actuel **sans** baisse du mouvement (piège mesuré par Prompt-A-Video).

### TA5 — Un projet, trois formats
- **Utilisateur** : case « décliner en 9:16, 1:1, 16:9 » à l'export ; sujet toujours cadré, textes dans la zone sûre ; réglage manuel possible.
- **Assemblage** : pour les plans générés, **régénération verticale native** (déjà prouvée en V3) proposée sur devis ; pour les médias importés, suivi du sujet par SAM 2.1 (déjà sur la GB10, `outils/detourage/`) → trajectoire lissée (filtre de Kalman ou zone morte de `reframe.js`, FableCut MIT) ; pas de YOLO (AGPL).
- **Acceptation** : 3 films × 3 formats, aucun visage coupé, aucun texte hors zone sûre, caméra virtuelle sans à-coups (accélération bornée). Issues #42, #21.

### TA6 — « Change seulement le plan 2 »
- **Utilisateur** : il clique un plan ou un instant, écrit « plus chaud, plus court » ; seul ce plan est refait, le reste reste identique, le supplément est annoncé.
- **Assemblage** : graphe de dépendances des ressources de l'`EditPlan` (plan → prises → rendu → exports) ; différence d'`EditPlan` ; invalidation des seuls aperçus/exports touchés (idée WeVisCut et FilmCraft) ; persistance serveur des projets (#10).
- **Acceptation** : sur un film de 8 plans, une correction locale ne relance qu'un rendu, le personnage `@` est conservé, le reste est bit à bit identique.

### TA8 — Lip-sync
- MuseTalk 1.5 (MIT) en aperçu sur Turing ou 5090 ; LatentSync 1.6 (Apache-2.0 code, OpenRAIL++ poids, 18 Go) en finale sur la 5090 ; visages de face d'abord. Branchement : nouvelle recette `levres-apercu` / `levres-finale`, déclenchée quand une piste voix externe est posée sur un plan avec visage. Acceptation : banc annexe C §4 (10-20 s, français et québécois, trois cadrages, mains près du visage) ; synchro, identité, dents, contours jugés sur la vidéo entière. Issue #26.

### TA7 — MCP distant et API publique
- Exposer les 22 outils `nexora_*` en MCP HTTP (authentification par la connexion unique existante, OIDC + PKCE) ; tâches asynchrones, clés d'idempotence, **le devis et la validation restent dans Nexora** (le LLM n'a aucun outil qui dépense) ; plafond de dépense par session ; page « Brancher à Claude ». Acceptation : Claude Code et Codex produisent un film de 20 s de bout en bout sans double débit après coupure provoquée. Issues #46, #47.

### TA9 — Agrandissement à l'export
- FlashVSR+ (0,5 à 0,98 image/s publiés sur 4090 : outil d'export, pas d'aperçu) dans la file d'export, SeedVR2 en témoin ; option « Master 1080p / 4K » au devis ; grain léger pour éviter la peau plastique. Acceptation : comparaison à 100 % sur 5 plans, aucun détail inventé sur un produit ou un texte. Issue #33.

### TA17 — ACE-Step 1.5 en complément de Music3
- Seulement quand la structure doit être exacte (drop à 8 s, arrêt sec à 17 s) ou pour **réparer un passage** ; Music3 reste le défaut (meilleur PER publié). Acceptation : trois briefs 15/30/60 s : corrections de montage comptées ; ACE-Step adopté seulement s'il en demande moins. Machine : 5090 (XL ≥ 20 Go recommandé) ou Turing (2B).

### TA24 — Contrats repris de FilmCraft
- `studioTools` (registre de commandes avec état d'activation partagé UI/agent), validation indexée des modifications groupées, `previewQueue` en lecture seule, `exportReport` (pertes des formats d'échange), `collectSelectionDependencies()`, verrou d'écriture et révision attendue par projet. Branchement : `mode-studio/src/features/nexora/` et `app/server/nexora/montage/`. Acceptation : tests unitaires, aucune perte lors de deux tâches concurrentes sur un même projet.

### TA11 — Socle VFX : Wan2.2-Fun-Control puis VACE-Fun
- **Utilisateur** : « enlève le lampadaire », « remplace le ciel par un ciel d'orage », « garde l'acteur, change le décor » ; masque par un clic (SAM 2.1 déjà livré), devis, rendu.
- **Assemblage** : Wan2.2-Fun-5B-Control (Apache-2.0) sur la 5090, VACE-Fun-A14B sur la GB10 ; masque + zone autorisée pour ombres et reflets ; recomposition dans la couche (jamais toute l'image). DiffuEraser seulement après vérification de sa dépendance ProPainter. H3 ne fait pas de v2v : ce socle ne le remplace pas, il le complète.
- **Acceptation** (feuille de route vague 5) : « enlève le lampadaire » sur un plan réel noté ≥ 7/10 ; zéro changement hors masque élargi. Issues #37 à #40.

### TA12 — Couches d'effets
- Bibliothèque d'éléments RGBA (Wan-Alpha v2 ; « Effect RGBA » d'Alpha++ quand les poids sortent) : fumée, étincelles, débris, flammes, créatures ; posés en calque dans le Mode Studio avec la bulle « Effet IA ici… » ; **sabres de lumière procéduraux** (suivi de la lame + segment lumineux WebGPU, lumière projetée générative en TA13). Acceptation : chaque élément testé sur noir, blanc, damier et caméra mobile ; un duel au sabre de 10 s monté avec lames droites et passages derrière le corps corrects. Issues #7, #41.

### TA18 — Ordonnanceur de prises
- Plus de prises pour les plans difficiles (budget adaptatif borné, idée AniMaker) ; tourner d'abord les plans « ancres » des entités (GroundShot) ; choisir 2 à 4 références **complémentaires** (lieu + personnage + accessoire) plutôt que quatre portraits. Branchement : `prises.ts`, `personnagesCast.ts`, projet long. Acceptation : film de 6-12 plans, moins d'incohérences à budget égal ; visage ≥ 0,7 sur 20 plans (#44).

### TA10 — Lien de revue client
- Lien privé, commentaire cliqué à un instant, versions immuables comparables, validation ; pas de co-montage simultané. Dépend de #10. Issue #12.

### TA13 — Relight vidéo
- Comparer LiveLight et Relit-LiVE (≥ 24 Go, 5090) sur explosion et sabre ; garder un seul chemin. Acceptation : visage stable, lumière hors masque contrôlée.

### TA14 — Trajectoires dessinées
- L'utilisateur trace la courbe du dragon ou du vaisseau sur l'image ; Wan-Move (≥ 40 Go publiés, GB10). Acceptation : erreur de trajectoire mesurée sur 3 scènes, silhouettes et nombre d'objets préservés.

### TA15 — Prévisualisation 3D dans le navigateur
- Poser un objet Relief (GLB) et une caméra dans la visionneuse existante, tirer la première et la dernière image (FL2VA de H3) ou une carte de profondeur (Wan-Fun). Coût GPU serveur nul. Acceptation : packshot produit de 5 s dont la trajectoire suit la prévisualisation.

### TA23 — « Refaire comme ça »
- Dépôt d'une vidéo de référence + jusqu'à 5 photos + une musique ; découpe (scdet, battues, mots), plan de montage, plans H3 manquants sous devis, titres HyperFrames. Reprend recherche/12 §6.5 ; dépend de TA2, TA3, TA6. Acceptation : 3 références, durée, ratio et cadence repris ; rapport après chaque étape.

### TA21 — Expérience « Producteur de nuit »
- Pour un abonné qui l'active explicitement, avec un plafond : entre 1 h et 6 h, sur GPU libres, le studio prépare une pub de 15 s depuis son catalogue ou ses nouveautés, livrée au réveil pour validation (rien n'est publié sans lui). Lisse la charge des GPU. Mesure : taux d'adoption et de publication sur 10 comptes pilotes.

### TA22 — Expérience « film document vivant »
- Prix, horaires, stock reliés au catalogue : une promotion change le carton, une rupture retire le produit ; rendu incrémental, nouvelle version soumise à validation. Dépend de TA6. Mesure : une pub approuvée maintenue un mois sans nouveau tournage.

### TA16 — Travailleur Blender à gabarits
- `mcp-for-blender` (MIT) dans un processus isolé, **cinq opérations typées seulement** (objet, caméra, lumière studio, trajectoire, passes), sortie `.blend` + proxy + passes + manifeste vérifié (durée, caméra active, cadrage) ; dix tâches internes inspirées de BlenderWorld. Après TA15, seulement si un client a besoin de packshots exacts.

## 3. Ce qu'on refuse (et pourquoi)

- **Agréger des API payantes** (Seedance, Kling, Luma) : marge détruite, devis faux, cohérence perdue entre plans ; H3 est 3e mondial et ouvert.
- **Centaines de presets** : vingt recettes fiables et illustrées valent plus (TA2).
- **Communauté, concours, réseau social** maintenant ; **mondes jouables** ; **entraînement de LoRA par les clients** sur nos GPU ; **« illimité »** GPU ; **plans longs comme objectif** en soi.
- **Blender conversationnel libre** (surface de panne) ; **réécriture de FilmCraft** ; **YOLO** (AGPL) ; **poids non commerciaux** (F5-TTS, ProPainter, YuE2, Higgs TTS 3, HoloCine) dans un parcours vendu.

## 4. Coût par seconde et stratégie de prix

### 4.1 Coût (recherche/24 §2.4 ; hypothèses d'amortissement à remplacer par les vraies valeurs)
Seconde de GPU : ≈ 0,000136 CAD (5090), ≈ 0,000124 CAD (GB10). Seconde de vidéo produite : 0,0008 CAD (brouillon), 0,002 (rapide GB10), 0,0035 (Ref2VA cinéma), 0,0076 (FL2VA cinéma 5090), ≈ 0,002-0,003 attendu avec Flex (à mesurer). Seconde **finie** (×3 pour brouillons, deuxième prise, ratés) : **0,006 à 0,025 CAD**. Musique et LLM : négligeables (moins de 0,001 CAD par film).

### 4.2 Capacité (la vraie limite)
À pleine qualité sur la 5090 : 56 s de GPU par seconde de vidéo, soit ≈ **64 s de vidéo par heure** ; GB10 en rapide ≈ 225 s par heure à 832×480. Avec Flex (si TA1 passe) : ≈ 180-240 s par heure sur la 5090 [ESTIMÉ]. En ordre de grandeur, **quelques milliers de secondes finies par jour** pour tout le parc. Le prix doit donc **protéger la file** (priorité aux forfaits, brouillons sur la GB10 et les Turing), pas seulement couvrir le coût.

### 4.3 Prix proposé (à valider par le fondateur ; 1 crédit = 1 ¢ CA, `usage.ts`)
| Élément | Prix | Comparaison |
|---|---|---|
| Studio, montage, 52 effets navigateur, bulle « recette maison » | **gratuit** (calcul dans le navigateur) | — |
| Écriture du film par le Producteur (palier Éco) | au jeton, ≈ 0,1 crédit | — |
| Brouillon | **2 crédits/s** (0,02 $) | Flow : 360p gratuit ou quasi ; Pika : brouillon puis finition payée |
| Finale qualité cinéma, **par seconde retenue**, 2 prises + juge inclus | **10 crédits/s** (0,10 $) | Pika H3 Flex API 0,07 USD ≈ 0,098 CAD régulier ; MiniMax H3 API 0,13 USD ; Higgsfield app ≈ 0,78 USD |
| Master 1080p/4K (agrandissement) | + 3 crédits/s | LTX 4K 0,39 USD/s |
| Voix, lip-sync, retrait d'objet, relight | devis par tâche (secondes GPU mesurées × 0,5 crédit) | — |
| Forfait Créateur | **29 $/mois**, 150 s finales incluses, file prioritaire, exports pros | Higgsfield Plus 49 USD/1 000 crédits |

Marge brute sur la finale : 75 à 95 % avant hébergement, paiement, soutien et sous-utilisation (ce n'est pas une marge nette). Avant publication : mesurer 100 commandes réelles, reprises comprises, et le coût par seconde **retenue**. Le devis actuel à 0,5 crédit par seconde GPU (`credits.ts`) donne ≈ 28 crédits/s en `h3-max` : trop cher face à Pika, et il facture nos ratés au client ; TA20 le remplace.

## 5. Interface triple A : huit règles mesurables

1. **Deux vitesses, un projet** : le mode simple (Producteur, Explorer) ne montre ni piste, ni image clé, ni jargon ; « Ouvrir dans le Studio » garde l'intention, la recette et le devis (#3 de l'audit). Mesure : 8 débutants sur 10 obtiennent un brouillon utilisable sans aide en 3 minutes.
2. **Pas de champ vide** : chaque réglage (caméra, lumière, style, rythme, énergie de voix) est une **vignette vidéo rendue par H3 chez nous** qui s'anime au survol ; un texte libre reste possible. Mesure : 100 % des options de l'Explorer et du panneau de plan ont leur vignette.
3. **Rideau avant/après universel** sur toute action IA (effet, détourage, retrait, relight, agrandissement, choix du juge), au même instant et même cadrage, son synchronisé.
4. **Attente lisible** : état réel, fourchette de délai, coût **verrouillé**, aperçu qui se précise, annulation et reprise après fermeture ; jamais de sablier muet. Mesure : chaque tâche GPU expose étape, délai estimé et coût réservé.
5. **60 i/s sacrés** : proxys WebCodecs générés en tâche de fond dès qu'un plan arrive ; la tête de lecture ne saccade jamais (banc perf #11).
6. **Une seule grammaire d'actions** : sélection, clic droit, raccourcis, Ctrl+Z, glisser-déposer identiques partout ; une action IA = un pas d'annulation nommé.
7. **Système visuel strict** : grille de 8 px, trois niveaux typographiques (Geist), une couleur d'accent (orange Nexora), contraste AA, aucun panneau qui saute au chargement (squelettes), résultat ≈ 60 % de l'écran ; mêmes règles que la grammaire des promos (R11) pour que le produit ressemble à ses films.
8. **Partout** : fr-CA et en-CA complets, clavier, lecteur d'écran sur les parcours principaux, revue et validation au téléphone (#50, #51, #52).

## 6. Mesures à lancer en premier (rapides, tranchent des questions)

1. **TA1** : Pika H3 Flex contre `h3-max` sur la 5090, 12 prompts, temps de bout en bout et préférence à l'aveugle (≈ 2 h de GPU, adaptateurs de quelques Go sur NexoraStudioWork).
2. **TA4** : réglage « dramatique » de Chatterbox sur pc5 et casting à l'aveugle de 6 textes (≈ 1 h).
3. **TA3** : banc de 24 briefs réécrivain actuel contre compilateur par mode (≈ 1 USD de LLM, 48 brouillons).
4. **TA20** : relever le coût réel par seconde retenue sur les 9 derniers films (journal GPU) pour remplacer les hypothèses du §4.1.
5. **TA25** : passer les films en cours au contrôle du §7 de recherche/23 avant de les montrer au fondateur.
