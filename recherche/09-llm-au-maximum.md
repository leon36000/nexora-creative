# 09 — Exploiter un LLM cloud au maximum dans Nexora Creative

Demande du fondateur (30/10/2026) : « réfléchis en profondeur comment exploiter un LLM au max, nous allons en utiliser un cloud ».
Statut : **conception** [PROPOSÉ], appuyée sur les guides d'écriture de MiniMax (`vendor/minimax-h3-guides/`, lus en entier), le catalogue de modèles Nexora (`NexoraSite/web/src/server/gateway/catalog-deepinfra/selection.json`) et les rapports 05 et 07. Les choix de modèles par rôle sont à confirmer par le banc d'évaluation du §6.

## 1. Le principe

Le modèle vidéo sait **rendre** ; il ne sait ni comprendre une intention vague, ni découper une histoire, ni juger son propre résultat. Un débutant écrit « ma voiture se transforme en robot géant pendant qu'une caméra tourne autour » ; H3 attend un prompt structuré de plusieurs centaines à plusieurs milliers de mots, avec des plans numérotés et horodatés, un vocabulaire de caméra précis, des locuteurs `(S1)`, des dialogues balisés `<d>[Langue] …</d>`, une ambiance sonore et une musique décrites à part. MiniMax garde son propre réécrivain (H3-Context-IR) pour son API et le dit « fortement recommandé ». **Le LLM cloud est notre Context-IR, et plus encore** : c'est le cerveau du studio, le modèle vidéo en est la caméra.

Règle d'architecture : **le LLM propose, le code dispose.** Tout ce qui touche à la licence, à la confidentialité, aux crédits et au matériel est décidé par du code déterministe (registre de capacités, politique de licences, grand livre) ; le LLM ne peut jamais choisir un moteur interdit ni dépenser sans devis.

## 2. Les douze rôles du LLM

| # | Rôle | Entrée → sortie | Gain pour l'utilisateur |
|---|---|---|---|
| 1 | **Compréhension d'intention** | texte libre (fr) + images/vidéos jointes → `Brief` typé (sujet, style, durée, format, plateforme, ton, personnages, lieux, voix, langue des dialogues, contraintes) | écrire comme on parle ; au plus **une** question de clarification, avec des choix |
| 2 | **Bible de continuité** | `Brief` → fiches personnages/produits/lieux (apparence, vêtements, palette, matières), règles de style | la même voiture, le même héros d'un plan à l'autre |
| 3 | **Réalisation (Director)** | `Brief` + bible → storyboard : scènes → plans (durée sur la grille 124 + 17n, cadrage, mouvement de caméra en vocabulaire H3, lumière, action, son, dialogues, transitions) | un film découpé comme par un réalisateur |
| 4 | **Compilation de prompt par moteur** | plan → prompt dans le « dialecte » du moteur : H3 T2VA / I2VA / FL2VA / Ref2VA selon le guide officiel, Wan, images clés Qwen-Image | qualité maximale de chaque moteur sans rien savoir des moteurs |
| 5 | **Images clés** | plan → prompt d'image de départ (et d'arrivée) → I2VA / FL2VA | cohérence et contrôle du cadrage avant de payer la vidéo |
| 6 | **Juge visuel et sonore** | prise (vidéo + audio) + fiche du plan → grille JSON : fidélité au plan, identité, artefacts, mouvement de caméra, synchronisation audio, texte à l'écran ; **comparaison par paires** des 2 candidats | l'utilisateur ne voit que les bonnes prises |
| 7 | **Diagnostic et correction** | défauts relevés → action ciblée : autre graine, réécriture d'une partie du prompt, plan raccourci, caméra simplifiée, image clé, autre moteur, retouche locale ; budget de reprises | « ça corrige tout seul », dans un budget annoncé |
| 8 | **Édition conversationnelle** | « rends le ciel plus orageux au plan 3 » → **opérations de patch** sur le JSON du projet ; le code invalide les prises dépendantes et fait un devis | modifier sans tout régénérer |
| 9 | **Montage assisté** | prises retenues → ordre, rythme, transitions, sous-titres (depuis les dialogues), titres, variantes 9:16 / 1:1 / 16:9 | une vidéo prête à publier |
| 10 | **Audio** | dialogues, direction de voix, description de musique et d'ambiance (champs H3 `overall_soundscape`, `non_diegetic_music`) | son natif cohérent avec l'image |
| 11 | **Garde-fous** | prompt et références → contrôle de l'AUP H3 (usurpation d'identité, mineurs, élections, faux avis) **en plus** de règles déterministes ; contrôle a posteriori des prises | conformité exigée par la licence H3 (V.5) |
| 12 | **Assistant d'interface** | état du projet → prochaines étapes suggérées, explications, noms et étiquettes des médias, recherche dans la bibliothèque | un studio qui guide un débutant |

## 3. Le parcours débutant, de bout en bout

1. **« Décris ta vidéo »** (une zone de texte, des pièces jointes facultatives). Rôle 1 produit le `Brief` en 2 à 5 s, en flux continu à l'écran.
2. **Une seule question si nécessaire** (« Format pour TikTok ou YouTube ? » avec deux boutons). Sinon, on avance avec des valeurs par défaut et on le dit.
3. **Proposition** : storyboard en vignettes texte (rôle 3), durée totale, **coût en crédits** et temps estimé (calculés par le code depuis le registre, pas par le LLM). Boutons : « Lancer », « Modifier », « Plus court », « Plus spectaculaire ».
4. **Génération** : par plan, image clé (rôle 5) puis vidéo ; 2 candidats ; juge (rôle 6) ; correction automatique dans le budget (rôle 7). Progression visible, aperçus latents.
5. **Résultat** : montage assemblé (rôle 9), lecteur, « Refaire ce plan », « Changer la musique », chat d'édition (rôle 8).
6. **Mode expert** : chaque étape s'ouvre (prompt compilé, réglages, moteur, graines, graphe exact).

## 4. Contrats techniques

- **Sorties structurées partout** : chaque rôle a un schéma Zod ; appel en *JSON schema / tool calling* ; validation ; en cas d'échec, une réparation avec le message d'erreur du validateur ; puis repli déterministe. Jamais de texte libre interprété par le code.
- **Validateurs déterministes du prompt H3** (issus du guide) : les trois champs présents et dans l'ordre ; `[Shot 1]` sans horodatage ; horodatages `At MM:SS.mmm` strictement croissants et dans la durée ; ligne d'instruction exacte en I2VA / FL2VA / L2VA (durée à deux décimales) ; dialogues fournis par l'utilisateur recopiés **mot pour mot** dans `<d>[Langue] …</d>` ; identifiants `(S1)` stables ; texte à l'écran entre guillemets ; `non_diegetic_music: N/A` si aucune musique. Un prompt qui échoue est réparé avant tout appel GPU, donc sans dépense vidéo.
- **Tout passe par la passerelle Nexora `/v1`** : clé de l'organisation, crédits débités, Privacy Router appliqué, collecte amont refusée. Le LLM n'est jamais appelé directement chez un fournisseur.
- **Rôle → modèle en configuration**, pas en dur ; chaque appel journalise le rôle, le modèle, les jetons et la décision prise (sans contenu, comme le journal du Privacy Router).
- **Cache de prompt** : les consignes système (guides H3 de 15 à 23 Ko, bible du projet) sont stables et placées en tête ; le catalogue Nexora porte un tarif de lecture en cache (`cacheReadRate`).
- **Flux continu** (SSE) pour le brief et le storyboard : l'utilisateur voit le plan s'écrire.
- **Confidentialité** : le juge envoie la vidéo générée au modèle cloud. C'est un média de l'organisation : réglage « Évaluation automatique par IA » lié au niveau de confidentialité (désactivée par défaut en « Souverain strict », remplacée par les contrôles déterministes seuls).

## 5. Quels modèles pour quels rôles (catalogue Nexora, à confirmer par banc)

Modèles présents dans le catalogue au 30/10/2026 (tous « en aperçu », pas encore appelables par l'API publique) :

| Rôle | Candidats | Pourquoi |
|---|---|---|
| Intention, réalisation, édition (1, 2, 3, 8) | Kimi-K3, GLM-5.3, DeepSeek-V4.1-Flash, Qwen3.5-397B-A17B | raisonnement et suivi de consignes longues ; sorties structurées |
| Compilation de prompt (4, 5, 10) | même famille ou version Flash | appels fréquents ; consignes longues mises en cache |
| Juge vidéo **et audio** (6, 7, 11b) | **MiMo-V2.6-Pro** (entrée vidéo + audio), MiniMax-M3 (vidéo), Qwen3.5-397B (vidéo), Gemma-4-31B (vidéo + audio) | H3 produit du son : un juge qui entend est nécessaire pour la synchronisation et les dialogues |
| Rapide et bon marché (12, étiquettes) | MiMo-V2.6-Flash, GLM-5.3-Flash, Gemma-4-26B | latence et coût |
| Recherche dans la bibliothèque | Qwen3-Embedding-8B, embeddinggemma-2 (multimodal) | médias retrouvés par description |

[ESTIMÉ] Ordre de grandeur : quelques dizaines de milliers de jetons par vidéo de 30 s (brief, storyboard, 6 prompts compilés, 12 jugements). C'est faible devant le coût GPU d'une vidéo, donc **il est rentable de dépenser du LLM pour éviter une génération ratée.**

## 6. Mesurer plutôt que croire

- **Jeu d'or** de 40 intentions en français (publicité produit, effet spectaculaire, dialogue, clip musical, transformation, sport, animation) avec ce qu'un humain attend.
- Pour chaque rôle et chaque modèle candidat : taux de JSON valide du premier coup, taux de prompts H3 valides, latence, coût en jetons, et **qualité vidéo à l'arrivée** par comparaison par paires (juge humain sur un échantillon, juge VLM sur le reste).
- Le rapport 05 rappelle que les juges VLM généralistes sont peu fiables sur les artefacts : contrôles déterministes d'abord (durée, résolution, images noires ou figées, piste audio présente, niveau sonore), puis identité (DINO/ArcFace), puis VLM, puis humain.

## 7. Ordre de construction

1. **Réécrivain H3** (rôle 4) + validateurs déterministes + tests : c'est le gain de qualité immédiat sur chaque rendu. *En cours.*
2. Brief (rôle 1) + storyboard (rôle 3) + devis : le parcours « Décris ta vidéo ».
3. Juge par paires (rôle 6) + correction (rôle 7) avec budget.
4. Édition conversationnelle par patch (rôle 8), montage assisté (rôle 9).
5. Garde-fous (rôle 11), assistant (rôle 12), mémoire de style par organisation.
