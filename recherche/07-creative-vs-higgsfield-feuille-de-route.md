# 07 — Nexora Creative face à Higgsfield et aux leaders : écart, composants ouverts, feuille de route (2 novembre 2026)

Demande du fondateur : atteindre **au moins le niveau de Higgsfield en mode simple** et **le niveau d'un studio professionnel en mode pro**, avec une facilité extrême (l'IA fait le gros du travail). Contraintes : vidéo = MiniMax H3 uniquement ; image, audio, voix, upscale, lip-sync : les meilleurs modèles ouverts exécutables sur le GB10 (128 Go unifiés, aarch64) ou la RTX 5090 (32 Go).

Numérotation : les n° 06 et 07 existaient déjà (`06-openfield-et-aimoviestudio2.md`, `07-litterature-scientifique.md`) ; les noms de fichier sont distincts. Le rapport frère est `06-skills-claude-code-creation.md`.

## 0. Résumé

1. **Le moteur n'est plus le différenciateur.** MiniMax H3 est maintenant proposé par Pika (« H3 Flex », 29/10/2026), Luma, Krea, Leonardo et Higgsfield [OFFICIEL, pages de modèles]. Atteindre la parité de rendu est faisable ; **l'écart avec Higgsfield est dans l'orchestration et l'ergonomie** (personnages persistants, agent, apps, publicité, presets visuels), pas dans la qualité d'image.
2. **Nexora Creative a déjà ce que Higgsfield n'a pas** : un vrai montage multipiste (FreeCut) avec assistant, exports ProRes et FCP7 XML, un Director qui écrit et tourne un film, la modification d'un plan sans tout refaire, des moteurs hébergés chez nous (confidentialité), une licence H3 documentée. Higgsfield n'a pas d'éditeur intégré (revues tierces) et passe par des plugins Adobe.
3. **Mais dix fonctions du code sont inertes** : Mirror, Reshoot, Effects, Extend, Transitions, Speak, Add sound, Stage, HDR, Swap, Cast vidéo et le mode « Dream » reposent sur LTX-2.x, **bloqué par `app/server/nexora/licences.ts`** (échec fermé). Dans l'interface elles sont encore listées. Remettre ces fonctions en service sur H3 est le chemin le plus court vers la parité (items R3a, R3b, R6).
4. **Manques structurants** : personnages cohérents d'une vidéo à l'autre (le bundle H3 Ref2VA est dans `models.ts` mais non branché), agent conversationnel à outils, juge visuel, studio de publicité, voix, canvas nodal, API publique.
5. **23 items de feuille de route** (§8), chacun avec le composant ouvert à réutiliser, sa licence, sa maturité et le fichier où l'accrocher. Les cinq plus rentables : **R6 personnages persistants, R9 agent Producteur, R8 juge visuel + 2 candidats, R10 studio de publicité, R1 « image d'abord » avec brouillon**.

## 1. Méthode et niveau de preuve

- **Lu par moi** : `docs/ETAT.md`, `ARCHITECTURE-NEXORA-CREATIVE.md`, rapports `recherche/06`, `08`, `09`, `11`, et dans `app/` : `server/nexora/llm.ts`, `reecritureH3.ts`, `film.ts`, `studio.ts`, `licences.ts`, `registre.ts`, `server/models.ts`, `server/cast.ts`, `server/loras.ts`, `src/catalog.ts`, `mcp/server.ts`. **Rien n'a été exécuté** ; l'état « marche / bloqué » vient de la lecture du code et des documents du dépôt.
- **Concurrents** : un agent de recherche a lu les pages officielles (changelog Higgsfield de 220 000 caractères, pages de prix, centre d'aide, changelogs Runway, Krea, Adobe, ElevenLabs, etc.) ; un second a couvert les autres studios. Étiquettes : [OFFICIEL daté] / [TIERS daté] / [NON VÉRIFIÉ]. Ils ont travaillé avec des outils qui **résument** les pages : montants et dates sont des lectures de résumés. Les revues tierces citées pour Higgsfield contiennent des liens d'affiliation et ne sont pas des tests d'usage.
- **Projets ouverts** : environ 45 dépôts clonés en lecture seule (métadonnées Git relevées par clone sans blob), jamais exécutés ; GitLab (6 requêtes) et Codeberg (3) sondés : rien d'exploitable (§7). Les étoiles de 2026 sont souvent gonflées ; le jugement repose sur l'historique et le contenu.
- **Modèles ouverts** : cartes Hugging Face, dépôts, changelog ComfyUI (docs.comfy.org, v0.43.1 du 28/10/2026), classements Artificial Analysis non datés, forum NVIDIA pour les mesures GB10. **Aucune mesure n'est de nous.**
- **Licences** : relevées telles qu'écrites (SPDX ou texte), sans analyse. Quelques clauses évidentes (non commercial, territoire, plafond de revenus) sont signalées parce qu'elles décident de l'usage du modèle ; l'analyse reste au fondateur.

## 2. Où en est Nexora Creative (lu dans le code)

**Fonctionne** (selon `docs/ETAT.md` et le code) :

| Domaine | Ce qui existe |
|---|---|
| Vidéo | H3 (FastH3 V2 NVFP4 « rapide », H3 « cinéma »), texte, image, première+dernière image, 5/8/10 s avec son, jusqu'à 1344×768 ; deux GPU (RTX 5090 pour H3, GB10 pour Qwen et Music3) |
| Réalisation | AI Director : idée → storyboard modifiable (bible de continuité) → tournage → assemblage ; plans enchaînés depuis la dernière image ; « Refaire ce plan » ; remontage sans nouveau rendu ; contrôle qualité automatique ; reprise après panne |
| LLM (rôles) | réécriture des prompts H3 avec validateur déterministe, « Booster ma phrase », « Inspire-moi », publication par réseau, modération, description musicale, assistant de montage |
| Image | Qwen-Image-2.1 (repli 2512) ; Edit (masque), Angle, Couverture (9 plans), Push in, Next beat, Relight, Expand sur Qwen-Image-Edit 2509 ; Cast (images fixes) ; Remove background (SAM 3) ; Upscale (Real-ESRGAN, SeedVR2) ; Objet 3D (Trellis 2) |
| Son | MiniMax-Music3 (musique de film et de clip), mixage −14 LUFS |
| Montage | Mode Studio : FreeCut multipiste, assistant (silences, sous-titres au mot par faster-whisper, montage au rythme), exports ProRes 422 HQ et séquence FCP7 XML |
| Plateforme | multi-organisation, connexion unique OIDC, devis et crédits (côté Creative), UI mobile, serveur MCP (31 outils, stdio) |
| Vitrine | 27 presets de caméra/VFX/ambiance (+ « Libre »), en texte, axes Director (genre, caméra, objectif, cadrage, lumière, pellicule, look, étalonnage, époque 1960–2020, rampes de vitesse) |

**Bloqué par licence (LTX-2.x), listé mais inutilisable** : Mirror (transfert de mouvement), Reshoot, Effects, Extend, Transitions, Speak (avatar parlant), Add sound, Stage (3D), HDR, Swap, Cast vidéo (feuille d'ingrédients), Dream (upscale). Source : `licences.ts`, table `REGLES`.

**Absent** : personnages persistants en vidéo, lip-sync sur audio externe, voix (TTS, clonage, doublage), agent à outils, canvas nodal, applications partageables, studio de publicité, kit de marque, juge visuel, entraînement de LoRA, API publique, fil communautaire, interpolation de cadence, upscaler latent H3.

**Pas encore prouvé** (ETAT.md) : écoute humaine, « l'IA dessine le plan clé avant H3 », crédits côté site (routes à construire), H3 sur le GB10 (disque).

## 3. Les leaders, fin 2026

### 3.1 Higgsfield (higgsfield.ai) — lu le 2 novembre 2026 [OFFICIEL daté sauf mention]

**Cinéma et caméra**
- **Cinema Studio 4.0** : clips de 30 s multi-plans, jusqu'à 50 références, audio natif (voix, bruitages, musique en une passe). Communiqué payant du 28/10/2026 ; le changelog le date d'août (dates incohérentes entre sources).
- **Réalisation** : corps de caméra (numérique, caméscope DV, 35 mm, 8 mm), optiques de la nette à l'anamorphique vintage, 7 genres, décennies 1960–2020, tempo, plus de 50 presets de couleur, éclairage, mouvements POV/bras robot/hélicoptère, « Emotion Wheel » pour le jeu des personnages, extension avant/arrière, Edit Video ciblé.
- **65 presets de caméra** sur la page officielle `camera-controls` (360 Orbit, Bullet Time, Crane Up/Down, Crash Zoom, Dolly Zoom, Dutch Angle, FPV Drone, Snorricam, Robo Arm, Through Object, Whip Pan, Hyperlapse…), chacun avec un bouton « Generate » ; les sources tierces annoncent « 70+ » et le blog « 20+ pour WAN » (contradiction).
- Coût affiché avant la génération (70 crédits pour 10 s en 720p avec audio ; 480 crédits pour 30 s en 1080p) ; échecs techniques remboursés ; filtre sur visages réels et propriété intellectuelle.

**Personnages**
- **Soul ID** : entraînement depuis des photos (20 minimum, 80 maximum selon le centre d'aide ; d'autres pages disent 5+ ou 10–20 ; 3 à 5 minutes et 25 crédits selon un billet de blog), le personnage devient un **Element** appelé par `@` dans les générations ; non exportable.
- **Elements** (24/02/2026) : bibliothèque de personnages, lieux et accessoires `@`. Soul 2.0 (09/02), Moodboards, Soul Hex (palettes), Photodump, AI Cast (05/03), **AI Influencer** (02/10, constructeur par commandes).

**Parole et audio**
- **Lipsync Studio** : Higgsfield Speak 2.0 (~14 crédits pour 5 s en 720p), Kling Speak/Lipsync, Wan 2.5 Speak, Infinite Talk, Sync Lipsync 3 (4K 30 i/s), Veo 3 avec audio. Audio refondu le 10/08 : texte-vers-parole, changement de voix, **traduction avec lip-sync en 18 langues** ; Eleven v4 (28/09), Seed Audio 1.0 (parole, son et musique en une passe).
- Limite relevée par un comparatif tiers : dents floues sur certains avatars ; HeyGen jugé plus précis, Higgsfield plus cinématique.

**Édition, VFX, finition**
- Modèles image : Nano Banana Pro/2/2.1, GPT Image 2/2.5, Seedream 5.0, FLUX 3 Image et FLUX.2, Flux Kontext, Ideogram 4.5, Recraft V4, Reve, Soul Inpaint. **Popcorn** (storyboard : prompt + références, plusieurs cadres cohérents, 1,5 crédit par image). **Layers** (11/08) : image plate découpée en éléments éditables.
- **Genjutsu** (01/09) : transfert de mouvement, échange d'objet ou de personnage dans une vidéo existante, 30+ presets, jusqu'à 1080p ; Lite (19/10), Restyle (30/09, 20+ styles). Face Swap et Character Swap (~2 crédits). Relight et Color Palette autonomes (20/08). **Reframe** (30/05) : change le ratio en régénérant le fond. **Upscale** : ByteDance Upscale 2K/4K avec interpolation jusqu'à 60 i/s ; FLUX 3 Video Upscaler (mis à jour le 15/10). Viral Presets (15/05) et Effects 2.0 (10/09). 3D Jutsu (04/09).
- **Aucun éditeur de montage intégré** (revue tierce) : plugins Premiere Pro, After Effects, Photoshop, DaVinci Resolve, Figma, Blender, ChatGPT.

**Publicité**
- **Marketing Studio** (06/04/2026) : modèle + photo produit, lien produit, prompt ou Ad Reference ; UGC, Motion, TikTok ; avatar réutilisable ; 15 s par génération. **Ads Studio** (30/09) : lien de site → jusqu'à 20 pubs statiques par produit. **Ad Multiplier** (06/10) : recrée une pub avec vos produits, acteurs, lieux et teste accroches et appels à l'action.

**Canvas, Apps, agent**
- **Canvas** (30/04/2026) : tableau infini en nœuds, collaboration temps réel, modèles enregistrables. **Supercomputer** (13/05) : agent qui planifie, choisit les modèles et livre ; connecteurs Slack/Drive/Notion/réseaux ; mémoire ; case « Ask before generating ». **Apps** (07/07) : applications web génératives construites depuis un prompt, hébergées sur un sous-domaine Higgsfield, remixables ; l'utilisateur final paie avec ses crédits. **MCP** (28/04) et **CLI** (04/05) pour Claude, Cursor, Codex ; API pay-per-generation (15/09).

**Modèles tiers (30+)** : Seedance 2.0/2.5, Kling 2.1 à 4.0, Veo 3/3.1, Wan 2.2–3.0, MiniMax Hailuo et **H3**, Grok Imagine, etc. ; moteurs maison DoP Lite/Standard/Turbo. Sora 2 absent de la grille du 02/11 (un tiers affirme son arrêt, [NON VÉRIFIÉ]).

**Tarifs** (page de prix du 02/11/2026) : Starter 19 $ (270 crédits), Plus 59 $ (47 $ en annuel, 1 200 crédits), Ultra 129 $ (99 $, 3 000+), Team dès 65 $ par siège. Coûts : Nano Banana Pro 2 crédits ; Kling 3.0 ~7 crédits pour 5 s en 720p ; Seedance 2.0 ~22 crédits en 720p. « Illimité » restreint à quelques modèles sur 7 jours, **inopérant sur MCP, CLI, Canvas et Supercomputer**.

**Points faibles** : Trustpilot 4,0/5 sur 5 257 avis (19 % à une étoile ; plaintes sur la consommation de crédits, résultats à côté du prompt, remboursement refusé hors 7 jours, résiliation difficile) [TIERS, 02/11] ; dépendance aux modèles tiers (« possède-t-il sa technologie ? ») [TIERS, 22/10] ; qualité variable de la voix off et du rythme UGC [OFFICIEL] ; conditions d'entraînement sur les contenus à lire avant d'y charger du matériel client [TIERS].

### 3.2 Les recettes de l'extrême facilité (déduites des pages officielles)

1. **Un seul envoi, plusieurs résultats** (Genjutsu, Viral Presets : « choisir un preset, envoyer, obtenir »).
2. **Presets visuels cliquables** (65 caméras avec bouton, 30+ Genjutsu, 50+ couleurs, 20+ styles).
3. **Image d'abord, vidéo ensuite** (Marketing Studio, Popcorn, Start & End Frame).
4. **Cohérence par `@`** (Elements, Soul ID, AI Influencer par commandes plutôt que par prompt).
5. **Prix avant le clic**, confirmation avant dépense, **remboursement automatique des échecs techniques**.
6. **Du lien au résultat** (lien produit → pub ; site → 20 pubs).
7. **Agent en langage naturel** (Supercomputer, Auto Mode, Apps en une phrase, MCP/CLI).
8. **Brouillons bon marché** (Seedance Draft 480p, Kling Turbo, Genjutsu Lite).
9. **Hub multi-modèles** : un abonnement, des fenêtres d'illimité pour tester sans compter.
10. **Preuve sociale intégrée** (fil Community avec prompts visibles et remixables, défis hebdomadaires, Academy).
11. **L'outil vient à l'utilisateur** (plugins Adobe, ChatGPT, Claude, Figma, Blender).

### 3.3 Les autres leaders [OFFICIEL ou TIERS daté, voir les sources en fin de rapport]

| Produit | Fonctions qui font la différence | Dernière grosse mise à jour | Prix d'entrée |
|---|---|---|---|
| **Runway** | Aleph 2.0 + Edit Studio (une modification de cadre se propage au clip) ; Agent 2.0 (25/06) qui construit des Workflows ; Workflows en nœuds publiables en Apps (App Studio 26/10) ; Act-Two (capture de jeu) ; Characters (avatars temps réel) ; ProRes 4444 et PNG, HDR, Enhance Frame Rate 4K ; plugins Adobe (08/09) et Resolve (23/09) ; MCP ; Brand Kits ; Runway Ads (27/10) | 27/10/2026 | Free : 125 crédits ; Standard 15 $ (625 crédits) |
| **Kling** | Kling 4.0 : 3 à 30 s, jusqu'à 10 images clés, 15 références combinées (images, vidéos, sujets, voix), audio stéréo et lip-sync en 10 langues ; Motion Control ; Omni (références, Start & End) ; Avatar 2.0 ; Image 3.0 4K avec séries cohérentes ; espace Canvas [prix et spécifications 4.0 : TIERS] | 4.0 : 28/09–15/10/2026 | 66 crédits par jour (gratuit) ; Standard ~10 $ [TIERS] |
| **Luma** | Ray3.2 (contrôle image par image) ; Modify Video V2 (20 s, 1080p, images clés + personnage de référence) ; jusqu'à 16 images clés ; HDR 16 bits, EXR ; Agents (Skills, Scenes, Layers, Pages) ; Variants (redimensionner et traduire des pubs) ; Mini-Apps ; héberge Seedance, **H3**, Kling 4.0, Veo 3.1 | Mini-Apps 27/10/2026 | Plus 30 $ (10 000 crédits) |
| **Pika** | Video Studio multi-plans jusqu'à 30 s ; Product Ad, Swap Anything, Motion Transfer, Character Studio, Soundtrack ; MCP et plugin ChatGPT ; **H3 Flex** : MiniMax H3 post-entraîné, jusqu'à 12 références, 5 pistes audio, sortie 4K, poids ouverts (annonce de la société) | H3 Flex 29/10/2026 | Starter 10 $ (900 crédits) |
| **Krea** | Krea 3 (édition d'image : 6 références, 24 zones par requête, ~8 s en 2K) ; Krea Agent (planifie, pilote Photoshop et Blender) ; Nodes → Apps ; Krea 2 (poids ouverts Raw/Turbo, entraînement de LoRA ouvert à tous depuis le 01/06) ; Realtime ; Enhancer (Topaz Starlight) ; Audio avec clonage de voix ; vidéo agrégée dont **H3** | 31/10/2026 | 100 unités par jour (gratuit) ; Basic 9 $ |
| **Magnific** (ex-Freepik) | Spaces (canvas à ports typés) → **Flows** (un process publié en « app » : champs d'entrée + bouton, exécutable par MCP/API/webhook) ; Magnific One (Draft : 8 ou 16 directions pour le prix d'une image ; Brand Kit depuis un site, un PDF ou 50 images) ; **Move** (28/10) : motion design conversationnel écrit en HTML avec **HyperFrames**, export 4K jusqu'à 180 s, recomposition 9:16/1:1/4:5 | 28/10/2026 | Premium ~20 $ [TIERS] |
| **CapCut / Dreamina** | Seedance 2.5 (30 s, 50 références, édition ciblée par timestamp) ; Seedream 5.0 Pro (annotation par flèche/cercle, séparation en calques) ; **EditPilot** (montage par instruction : « 12 minutes → 90 secondes ») ; pilote agentique annoncé | 27/10/2026 | Pro 33,99 CAD |
| **Adobe Firefly** | **Firefly Graph** (canvas nodal, 250+ nœuds, partage en « capsule » exécutable sans connaître le graphe) ; Boards ; AI Assistant ; éditeur vidéo à timeline dans le navigateur ; Custom Models ; modèles partenaires (Veo 3.1, Runway, Luma, Kling 4.0 Omni, Seedance, FLUX.2, GPT Image, Topaz, ElevenLabs) | 23/10/2026 (modèles) | Standard 9,99 $ |
| **Flora** | Canvas nodal + agent FAUNA (choisit les modèles, écrit les prompts, organise le canvas, non décompté) ; Actions (21+ outils d'édition appelables) ; App Mode d'équipe | 06/05/2026 | gratuit ; Starter 18 $ par siège |
| **Figma Weave** (ex-Weavy) | nœuds/workflows pro, intégration Figma, outils publiables sur la Community | 17/04/2026 | Starter 24 $ |
| **ComfyUI** | **App Mode** (un graphe reçoit une interface d'entrées/sorties), Comfy Cloud (RTX 6000 Pro 96 Go, 900+ modèles, Comfy Agent), ComfyHub | docs.comfy.org 28/10/2026 | Standard 20 $ |
| Autres | **ElevenLabs** (Eleven v4 90+ langues, Studio, Video-to-Music, doublage) ; **HeyGen** (traduction 175+ langues avec lip-sync, Avatar V) ; **Hedra** (Character-3, API, MCP) ; **Descript / Opus / Submagic** (montage par texte, clips, silences, reframe avec suivi, sous-titres animés) ; **Topaz** (Astra, Starlight) | — | — |

### 3.4 Les dix fonctions qu'un studio sérieux a fin 2026 (consensus des deux enquêtes)

1. Plusieurs modèles dans un abonnement, **avec coût affiché avant la génération**. 2. **Audio natif synchronisé**. 3. **Personnages et références persistants** (`@`, Elements, Characters). 4. **Clips longs multi-plans** avec images clés. 5. **Édition d'une vidéo existante** (échange, restyle, transfert de mouvement). 6. **Contrôle de caméra**. 7. **Parole, lip-sync, traduction**. 8. **Agent + MCP/CLI/plugins**. 9. **Fabrique de publicités et d'apps réutilisables**. 10. **Finition pro et brouillons** (4K, interpolation, HDR, ProRes, aperçus 480p). Onzième point transversal : **canvas nodal partagé**, publiable en application.

Paradigme dominant : **un même artefact, deux vues** (Magnific Spaces → Flows ; Krea Nodes → Apps ; ComfyUI graphe → App Mode ; Firefly Graph → capsule ; Runway Workflows → Apps). Le pro construit le graphe ; le débutant ne voit que les champs et le bouton. C'est le modèle à copier pour « simple contre pro ».

## 4. Tableau comparatif : fonction → Higgsfield / leaders / Nexora Creative aujourd'hui

Légende de la dernière colonne : **OK** fonctionne ; **PARTIEL** ; **BLOQUÉ** (code présent, licence LTX bloquée) ; **ABSENT**.

| Fonction | Higgsfield | Autres leaders | Nexora Creative aujourd'hui |
|---|---|---|---|
| Texte → vidéo avec son | Cinema Studio 4.0 : 30 s multi-plans, 50 réf., son natif | Kling 4.0 (3–30 s), Seedance 2.5, Veo 3.1, Pika H3 Flex | **OK** : H3 seul, 5/8/10 s, son natif ; film multi-plans par le Director |
| Image → vidéo, première/dernière image | Start & End Frame | Luma 16 images clés, Kling 10 | **OK** (FL2VA, I2VA) |
| Presets de caméra | 65 avec vignettes et bouton | Runway, Luma Ray3.2, Kling Motion Control | **PARTIEL** : 27 presets en texte, sans vignettes rendues ; axes Director (objectif, pellicule, époque) au niveau du rig Cinema Studio |
| Personnages cohérents en vidéo | Soul ID (20–80 photos), Elements `@`, AI Influencer | Kling 15 réf., Krea Elements, Runway Characters, OpenArt, Firefly Custom Models, Krea 2 LoRA | **PARTIEL** : Cast `@` en images fixes (Qwen-Edit) ; vidéo **BLOQUÉ** (LTX) ; H3 Ref2VA installé, non branché ; pas de LoRA |
| Avatars parlants, lip-sync | Speak 2.0, Lipsync Studio (7 modèles) | Hedra Character-3, HeyGen Avatar V, Kling Avatar, Runway Act-Two | **BLOQUÉ** (Speak). Dialogues dans le prompt H3 (`<d>…</d>`) possibles ; pas de synchronisation sur un audio fourni |
| Voix : TTS, clonage, changement, traduction | audio refondu (18 langues avec lip-sync), Eleven v4 | ElevenLabs, HeyGen 175 langues, Firefly | **ABSENT** (transcription faster-whisper seulement) |
| Musique | Seed Audio | ElevenLabs Music v2.5, Hedra, Krea Audio | **OK** : Music3, mixage −14 LUFS |
| Upscale et finition | FLUX 3 Video Upscaler, upscale 4K + 60 i/s, Reframe | Topaz, Magnific, Runway (Enhance Frame Rate, ProRes, HDR), Luma (HDR, EXR) | **PARTIEL** : Real-ESRGAN, SeedVR2 ; ni interpolation, ni upscaler latent H3 ; Dream/HDR **BLOQUÉ** ; export ProRes 422 HQ **OK** |
| Édition d'image par phrase | Nano Banana Pro, Flux Kontext, Soul Inpaint, Layers | Krea 3 (6 réf., 24 zones), Firefly, Seedream (annotation) | **OK** : Edit + masque, Angle, Couverture, Relight, Expand (Qwen-Edit **2509**) ; ni annotation ni calques |
| Édition vidéo, transfert de mouvement, échange | Genjutsu (30+ presets), Character Swap | Runway Aleph 2.0, Luma Modify V2, Kling Omni, Pika Swap | **BLOQUÉ** (Mirror, Swap, Reshoot, Restyle : `models.ts` ligne 533 exige `ltx25`, `mirror`) |
| Effets en un clic | Viral Presets, Effects 2.0 | Pikaffects | **BLOQUÉ** (Effects) ; presets « VFX » en texte seulement |
| Prolonger / transitionner | Extend avant/arrière | Runway, Luma | **BLOQUÉ** ; enchaînement depuis la dernière image **OK** dans le Director |
| Storyboard / planche | Popcorn | Firefly Boards, moodboards Krea | **OK** : storyboard modifiable ; Couverture 9 plans ; Next beat |
| Montage multipiste | aucun (plugins Adobe) | Firefly (navigateur), CapCut, Descript | **OK, au-dessus de Higgsfield** : FreeCut + assistant + exports ProRes/XML |
| Auto-montage, sous-titres, silences | Shorts Studio, Content Factory | Opus, Submagic, CapCut EditPilot | **OK** (silences, sous-titres au mot, rythme) ; pas de reframing ni de coupe de moments forts |
| Agent à outils | Supercomputer | Krea Agent, FAUNA, Runway Agent 2.0, Luma Agents, Firefly Assistant | **PARTIEL** : rôles LLM + assistant de montage à commandes bornées ; pas de boucle d'outils |
| Canvas nodal | Canvas | Runway Workflows, Magnific Spaces, Krea Nodes, Flora, Firefly Graph, Weave | **ABSENT** (chaque prise s'ouvre comme son graphe, en lecture) |
| Applications partageables | Apps (remixables) | Magnific Flows, Krea Apps, Comfy App Mode, Luma Mini-Apps | **ABSENT** (8 recettes statiques) |
| Publicité depuis un produit | Marketing Studio, Ads Studio, Ad Multiplier | Runway Ads, Luma Variants, Pika Product Ad | **ABSENT** en produit (notre campagne a pourtant été faite avec nos outils : `marketing/nexora/outils/`) |
| Kit de marque | avatar de marque | Magnific One Brand Kit, Firefly Brand Intelligence | **ABSENT** |
| Juge de qualité | échecs remboursés | — | **PARTIEL** : contrôle déterministe (noir, figé, silence, durée) ; juge IA absent |
| Brouillons rapides | Seedance Draft 480p, Genjutsu Lite | Luma Draft, Magnific Draft (8–16 directions) | **PARTIEL** : « Rapide / Qualité max » ; pas d'étape image clé validée |
| Coût avant le clic | oui | Krea, Firefly | **OK** (devis temps et crédits) ; crédits côté site à construire |
| MCP, API, plugins | MCP, CLI, API, plugins Adobe/Figma/Blender | Runway, Krea, Magnific, Hedra | **PARTIEL** : MCP local (stdio), pas d'API publique |
| Communauté, remix | Community, concours, Academy | — | **ABSENT** |
| 3D, mise en place | 3D Jutsu | Runway Game Worlds | **PARTIEL** : Objet 3D **OK** ; Stage **BLOQUÉ** |
| Confidentialité, hébergement maîtrisé | — | Krea Enterprise (zéro conservation), ViewComfy | **OK, avantage** : moteurs chez nous, Privacy Router, multi-organisation |
| Mobile | app | CapCut | **OK** (interface à 375 px) |

Les neuf fonctions où Nexora est déjà au niveau ou au-dessus (texte → vidéo avec son, image → vidéo, storyboard, montage, auto-montage de base, devis, confidentialité, musique, édition d'image) représentent le socle ; les neuf lignes « BLOQUÉ ou ABSENT » à fort impact sont : personnages persistants, lip-sync/voix, édition de vidéo existante, effets/extensions, agent, canvas/apps, publicité, juge, API.

## 5. Mode simple et mode pro : ce que l'on construit

**Mode simple (niveau Higgsfield)** : traduction des onze mécanismes du §3.2.

| Mécanisme Higgsfield | Équivalent Nexora | Item |
|---|---|---|
| Un envoi, plusieurs résultats | une phrase → 4 images clés → choix → vidéo (3 variantes d'un même plan) | R1 |
| Presets visuels cliquables | 60+ presets avec vignettes **rendues par H3** | R2 |
| Image d'abord | « l'IA dessine le plan clé, tu valides, H3 l'anime » (déjà conçu, non construit) | R1 |
| Cohérence par `@` | Cast v2 : feuille de personnage + H3 Ref2VA ; LoRA en option | R6, R7 |
| Prix avant le clic, remboursement des échecs | déjà là ; ajouter remboursement automatique sur échec du contrôle qualité | existant |
| Du lien au résultat | produit/URL/photo → pub | R10 |
| Agent | « Producteur » : chat → plan → devis → exécution | R9 |
| Brouillons | H3 turbo 4 étapes en 768p (bundle `h3-turbo` déjà dans `models.ts`) | R1 |
| Hub multi-modèles | **non applicable** (H3 seul) : à remplacer par la valeur de l'orchestration (personnages, juge, publicité) | — |
| Preuve sociale | fil d'organisation avec recette visible et « recréer » | R21 |
| L'outil vient à l'utilisateur | MCP/API distants, plugins (exports Premiere/Resolve existent) | R20 |

**Mode pro (niveau studio)** : ce qui le définit et où nous en sommes.

| Exigence pro | État |
|---|---|
| Voir et régler chaque étape (prompt compilé, graphe exact, graine, moteur) | **OK** (chaque prise s'ouvre comme son graphe) ; manque l'édition du graphe |
| Canvas nodal publiable en application (le pro construit, le débutant utilise) | **ABSENT** : R15, R16 |
| Montage multipiste avec effets et titres | **OK** (FreeCut) ; titres animés propres : R12 |
| Livraison : ProRes, séquence FCP7 XML, HDR/EXR, étalonnage | ProRes et XML **OK** ; HDR/EXR **BLOQUÉ** (LTX) ; étalonnage d'époque **OK** |
| Cohérence contrôlée (références, LoRA, bible) | partielle : R6, R7 |
| Reprise ciblée d'un plan, versions | « Refaire ce plan » **OK** ; reprise partielle : R17 |
| Automatisation (API, MCP, scripts) | MCP local ; R20 |
| Collaboration, revue, rôles | multi-organisation **OK** ; commentaires et revue : hors liste |

## 6. Moteurs ouverts recommandés pour GB10 et RTX 5090

Règle : vidéo = H3. Ci-dessous, **tout le reste**. Colonnes : choix principal / repli (licence telle qu'écrite) ; ComfyUI = version minimale annoncée par le changelog ; observations aarch64. Aucune mesure n'est de nous ; les chiffres cités viennent du forum NVIDIA (septembre 2026) ou des cartes de modèles.

| Catégorie | Principal | Repli | Remarques |
|---|---|---|---|
| Image (génération) | **Qwen-Image-2.1** (actuel ; ~7 B ; licence « Qwen Research License » d'après le texte de LICENSE sur Hugging Face, usage commercial par accord séparé ; ComfyUI ≥ 0.37) | **Qwen-Image-2512** (Apache-2.0) ; **FLUX.3 Klein** (FLUX Kommunity v1.0, sorties commerciales sous 5 M$ de revenus annualisés ; ComfyUI ≥ 0.41) ; **Ming-Image-0.1-Design** (MIT, typographie ; ComfyUI ≥ 0.38) ; Z-Image, MOSS-Image (Apache-2.0) | GB10 : Qwen-Image-2.1 en 54 s à 1024² en 40 étapes, 31,6 Go de pic (forum NVIDIA, 30/09/2026, torch 2.13 cu130 aarch64) ; **bug de raccord rose** si le VAE tiling est actif (désactiver ou tuiles 1024/stride 768). Ideogram 4, Fibo 2.0 : poids non commerciaux. |
| Édition d'image | **Qwen-Image-Edit-2511** (Apache-2.0 ; relight dans la base ; ComfyUI ≥ 0.5) + LoRA multi-angles `fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA` (Apache-2.0) | FireRed-Image-Edit-1.1, JoyAI-Image-Edit-Plus (Apache-2.0) ; l'édition native de Qwen-Image-2.1 (jusqu'à 10 références) | Nous utilisons encore **2509** : mise à niveau simple (`server/models.ts`, bundle `edit`). Avec références : 1 réf. ~62 s, 3 réf. 184 s, 10 réf. 598 s sur GB10 (dérive visible). |
| Upscale image et vidéo | **SeedVR2** (Apache-2.0 ; natif ComfyUI ≥ 0.28 ; déjà dans le fork) + **upscaler latent H3 ×2** (`LBH-123-AI/Minimax_h3_latent_Upscaler`, étiquette Apache-2.0 sur HF, 467 « likes ») | **FlashVSR v1.1** / FlashVSR+ (Apache-2.0 ; 116 s sur 5090 pour 768p → 2K, 26,8 Gio, défauts d'alias sur travellings, mesure Sogni) ; Real-ESRGAN (BSD-3, figé depuis avril 2024) | SeedVR2 « conservateur » ; sur 5090 ~312 s pour 10 s en 1080p (docs ComfyUI). L'upscaler latent H3 exige les latents, pas un MP4 fini (stable sous mouvement de caméra, ~474 s, 20 Go). SUPIR, PiD, CodeFormer : non commerciaux. |
| Interpolation | **RIFE** (MIT) ; natif ComfyUI ≥ 0.20 | FILM (Apache-2.0) ; GIMM-VFI (plus lent, meilleur sur mouvements rapides) | — |
| Détourage / segmentation | **BiRefNet** (MIT ; natif ≥ 0.21) | **SAM 3.1** (licence « SAM License », gated ; natif ≥ 0.20.1) — déjà dans le fork (`sam3`, `cutout`) ; MatAnyone2 (NTU S-Lab) à relire | RMBG-2.0 : CC BY-NC. |
| Lip-sync (post-traitement d'un plan H3) | **LatentSync 1.6** (code Apache-2.0 d'après le README, poids HF étiquetés openrail++ : contradiction à clarifier ; visage 512, 18 Go de VRAM) | **MuseTalk 1.5** (MIT, code et poids ; 256×256, détails perdus, tremblements) ; InfiniteTalk v2v (Apache-2.0, base Wan 14B : lourd) | Aucun commit de LatentSync depuis 2025-06-20. Dépendances (decord, mediapipe, OpenMMLab) : peu de wheels aarch64 [à confirmer]. Prévoir un passage SeedVR2 ensuite. **Les générateurs d'avatars (InfiniteTalk image+audio, OmniAvatar, StableAvatar, LongCat-Avatar…) sont un second moteur vidéo : hors périmètre, non proposés.** |
| TTS, clonage (FR) | **Qwen3-TTS** 0.6B/1.7B-Base (Apache-2.0 ; 10 langues dont FR ; clone en 3 s ; janv. 2026 ; dépôt à 2 contributeurs) | **Chatterbox Multilingual** (MIT, filigrane PerTh, accent hérité du clip de référence) ; **Ming-3.0-tts** (MIT) | Aucun modèle n'annonce l'accent **québécois** ; un fine-tune F5-TTS existe (CC-BY-NC). Pistes : clip de référence québécois propre, ou affinage de Qwen3-TTS-Base sur un corpus dont nous avons les droits. À écouter : aucun comparatif indépendant en français. Fish Speech, Higgs TTS 3, Voxtral-TTS, F5-TTS : licences non commerciales ou de services. |
| STT, diarisation | **faster-whisper** (MIT, déjà utilisé) ; **Parakeet-tdt-0.6b-v3** (CC-BY-4.0, 25 langues dont FR) | whisperX (BSD-2, alignement au mot) ; Qwen3-ASR (Apache-2.0) ; VibeVoice-ASR (MIT, diarisation, 60 min) ; pyannote community-1 (CC-BY-4.0, gated) | — |
| SFX, foley | H3 produit déjà son synchronisé | **ThinkSound** (Apache-2.0, prototype) ; Stable Audio 3 (licence communautaire Stability + composants Gemma ; natif ≥ 0.22) | MMAudio (CC-BY-NC), HunyuanVideo-Foley (Tencent : hors UE/UK/Corée du Sud), ControlFoley (CC-BY-NC) : non retenus. |
| Musique de repli, stems | Music3 (retenu) | **ACE-Step 1.5** (MIT, 14 k étoiles, 101 contributeurs ; `requirements.txt` cible Linux aarch64 CUDA 13 ; natif ≥ 0.12) ; stems : **demucs** (fork `adefossez`, MIT, actif) | YuE2 : CC-BY-NC. BS-RoFormer : licence à relire par checkpoint. |
| Entraînement de LoRA | **ostris/ai-toolkit** (MIT) : Qwen-Image 2512/2.1/Edit, MiniMax-H3 (T2V, I2V, FL2VA, Ref2VA), « fonctionne aussi sur ARM64 Linux, y compris DGX Spark » (README) | **musubi-tuner** (kohya, Apache-2.0 déclarée au README, pas de LICENSE racine ; doc `minimax_h3.md` : modèle élagué ~21 Go en INT8, adapté aux 32 Go de la 5090) | **Risque GB10** : un fil NVIDIA (février 2026) décrit un QLoRA à ~0,01 it/s avec soupçon de blocage de noyau sm_121, non résolu à l'époque. 5090 : ~2 h pour 2 000 étapes sur un LoRA Qwen-Image (billet tiers de septembre 2025). Entraîner sur le checkpoint base, pas le distillé. |
| Juge visuel / audio | **Qwen3.8-27B** (Apache-2.0, image et vidéo, **sans audio**, ~56 Go BF16, FP8 disponible) | **Nemotron-3-Nano-Omni-30B-A3B** (NVIDIA Open Model Agreement ; vidéo + audio ; **anglais seulement** ; guide vLLM 0.20 pour DGX Spark ; ~21 Go en NVFP4) ; Qwen3-Omni-30B-A3B (Apache-2.0 ; parole FR ; 79–145 Go en BF16 selon la durée : à quantifier) ; Gemma-4-12B (Apache-2.0, léger) | Le rôle `juge` existe dans `llm.ts` (réservé). Pour l'identité : DINO/SFace ; **les poids InsightFace sont non commerciaux** (README), SFace (Apache-2.0) et AuraFace (Apache-2.0) à valider sur nos portraits. |
| Embeddings (recherche de médias) | **Qwen3-VL-Embedding-2B/8B** (Apache-2.0, jan. 2026) | SigLIP2 so400m (Apache-2.0) | — |

**À tester d'abord sur le GB10 (aarch64, sm_121)**, dans cet ordre : (1) socle ComfyUI ≥ 0.43 avec PyTorch 2.14 cu130 (le playbook NVIDIA DGX Spark pinne encore la v0.33.2, périmé) ; (2) Qwen-Image-2.1 et Edit-2511 en bf16 puis NVFP4 W4A4 à la volée (éviter la voie `modelopt_fp4`, boguée sur sm_121a) ; (3) SeedVR2 et FlashVSR (Triton, sageattn, flash-attn sur aarch64 : inconnu) ; (4) ai-toolkit sur 100 étapes pour détecter le blocage sm_121, puis comparaison avec la 5090 ; (5) LatentSync/MuseTalk (roues aarch64) ; (6) Parakeet/NeMo et Qwen3-TTS (onnxruntime, filigrane) ; (7) vLLM 0.20 avec Nemotron Omni ou Qwen3.8 FP8 ; (8) ACE-Step 1.5 et Stable Audio 3.

## 7. Projets ouverts à forker ou assembler (GitHub, GitLab, Codeberg)

**Sondage GitLab et Codeberg** (règle « open source d'abord ») : six requêtes GitLab et trois Codeberg (canvas, éditeur vidéo, ComfyUI, lip-sync, storyboard). Rien d'exploitable : `gitlab.com/afsh4ck/openedit` (3 étoiles, non lu), `gitlab.com/pixaroma/comfyui-pixaroma` (nœuds ComfyUI, 33 étoiles), `codeberg.org/Gourieff/comfyui-reactor-node` (échange de visage, non retenu).

**Verdict d'ensemble : aucun équivalent ouvert sérieux de Weavy, Flora ou Freepik Spaces n'existe.** Seuls des prototypes d'un à quatre contributeurs sont apparus en 2026. Pour le canvas, on **assemble** (xyflow) au-dessus de ce que le fork a déjà ; on ne forke pas.

| Composant | URL | Licence | Maturité | Verdict |
|---|---|---|---|---|
| xyflow (React Flow) | github.com/xyflow/xyflow | MIT | production (39 k étoiles, 175 contributeurs, dernier commit 2026-10-29) | assembler : bibliothèque de graphe du canvas |
| ostris/ai-toolkit | github.com/ostris/ai-toolkit | MIT | production (13 k étoiles, 35 contributeurs, 731 commits en 12 mois, 2026-10-31) | assembler tel quel (entraînement LoRA H3 et Qwen) |
| kohya-ss/musubi-tuner | github.com/kohya-ss/musubi-tuner | Apache-2.0 (déclarée au README) | utilisable (2,1 k, 45 contributeurs, 2026-09-27) | assembler : entraîneur de secours (5090) |
| modelscope/DiffSynth-Studio | github.com/modelscope/DiffSynth-Studio | Apache-2.0 | production (13 k, 84 contributeurs, 2026-10-30) | assembler : exemples H3 (Retake, LoRA d'identité, ControlNet) |
| tritant/ComfyUI_MiniMax_H3_Extender | github.com/tritant/ComfyUI_MiniMax_H3_Extender | Apache-2.0 | utilisable (363 étoiles, 5 contributeurs, 242 commits, 2026-10-27 ; l'auteur annonce une « final feature release ») | **recettes de graphe à porter** (clips chaînés avec contexte de mouvement, Ref2VA, audio de référence, raffinement latent), pas comme dépendance |
| LBH-123-AI/Minimax_h3_latent_Upscaler | huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler | Apache-2.0 (étiquette HF) | utilisable (313 k téléchargements ; pas de dépôt GitHub trouvé) | assembler en priorité (upscaler latent ×2) |
| OpenImagingLab/FlashVSR | github.com/OpenImagingLab/FlashVSR | Apache-2.0 | utilisable (2 k, 2026-10-16) | assembler : upscale vidéo « rapide » |
| ByteDance-Seed/SeedVR + numz/ComfyUI-SeedVR2_VideoUpscaler | github.com/numz/ComfyUI-SeedVR2_VideoUpscaler | Apache-2.0 | utilisable (3 k) | déjà dans le fork (`graphs/upscale.ts`) |
| SYSTRAN/faster-whisper ; m-bain/whisperX | github.com/SYSTRAN/faster-whisper ; github.com/m-bain/whisperX | MIT ; BSD-2 | production (26 k ; 25 k, 126 contributeurs) | assembler (faster-whisper déjà là ; whisperX pour l'alignement au mot) |
| Breakthrough/PySceneDetect ; snakers4/silero-vad ; CPJKU/beat_this | github.com/Breakthrough/PySceneDetect ; …/snakers4/silero-vad ; …/CPJKU/beat_this | BSD-3 ; MIT ; MIT (poids MIT, certains fichiers d'entraînement sous CC limitées) | production ; production ; utilisable | assembler (plans, parole, temps forts) |
| WyattBlue/auto-editor | github.com/WyattBlue/auto-editor | Unlicense | production (5,7 k, Nim, CLI) | idées + formats d'export (FCP7/FCP11, Kdenlive, MLT, OTIO, Shotcut) à comparer avec `projetExport.ts` |
| QwenLM/Qwen3-TTS ; resemble-ai/chatterbox | github.com/QwenLM/Qwen3-TTS ; github.com/resemble-ai/chatterbox | Apache-2.0 ; MIT | utilisable (14 k, jeune ; 27 k) | assembler (voix FR ; repli) |
| bytedance/LatentSync ; TMElyralab/MuseTalk | github.com/bytedance/LatentSync ; github.com/TMElyralab/MuseTalk | Apache-2.0 (code) ; MIT | utilisable mais figés (2025-06 ; 2025-09) | assembler après banc d'essai GB10 |
| ace-step/ACE-Step-1.5 | github.com/ace-step/ACE-Step-1.5 | MIT | utilisable (14 k, 101 contributeurs, 2026-08-29) | assembler : musique de repli ouverte |
| adefossez/demucs | github.com/adefossez/demucs | MIT | production (3,5 k, actif ; le dépôt Meta est figé depuis 2023) | assembler (stems) |
| timgit/pg-boss | github.com/timgit/pg-boss | MIT | production (4,1 k, 112 contributeurs) | assembler le jour où la file passe de SQLite à PostgreSQL |
| raph651/open-source-canvas | github.com/raph651/open-source-canvas | MIT | prototype (113 étoiles, 14 commits) | idées : références `@Avatar`, historique de rendus, connexions typées |
| BeatAPI/BeatDesign | github.com/BeatAPI/BeatDesign | Apache-2.0 | utilisable (310 étoiles) | idées de modèle de données (déjà au rapport 01) |
| NickPittas/DirectorsConsole ; Comfield ; lightbrushproject/opensauce | github.com/NickPittas/DirectorsConsole ; … | MIT | utilisable ; ? ; prototype | données de presets de caméra à réutiliser |
| walterlow/freecut ; mediabunny | github.com/walterlow/freecut ; github.com/Vanilagy/mediabunny | MIT ; MPL-2.0 | utilisable (2,3 k, 98 % d'un auteur) ; production (7,4 k) | **déjà retenus** (`mode-studio/`) |
| Augani/openreel-video | github.com/Augani/openreel-video | MIT | utilisable (5,5 k, 478 fichiers de tests) | plan B de l'éditeur ; paquets `agent` et `creation-agent` à lire |

**Rejetés (raison)** — copyleft fort ou « idées seulement » : AGPL-3.0 : nodetool, bananaflow, Video2X, Upscayl, SimpleTuner, OneTrainer, OpenMontage, worker-comfyui (passé en AGPL) ; GPL-3.0 : diffusion-pipe, chaiNNer, pyvideotrans, seed-vc, APISR, comfy-deploy, Inline-Studio, les packs H3 longue durée (Infinity, Long-Video, Guide). Licence incompatible avec un service ou clé de production : tldraw, Remotion, OpenVideo (react-video-editor), Twick, Fish Speech (licence du 13/10/2026 : services hébergés exclus), F5-TTS (poids CC-BY-NC), MMAudio, AudioLDM2, CodeFormer, Upscale-A-Video (S-Lab), Sonic (CC BY-NC-SA), Waifu2x-Extension-GUI (personnel seulement). Sans licence détectée : STAR, VEnhancer, MovieAgent, Wav2Lip, flowboard, Tr1dae/ComfyUI-MiniMaxH3_LatentUpscaler, clones « infinite-canvas ». Dépendance à un service : open-edit (connexion VEED), franklin-canvas (x402), flowboard (Veo). Figés : ClipsAI, editly, omniclip, SadTalker, video-retalking, InstantID, IP-Adapter, OpenVoice, Diffusion Studio core. Autre moteur vidéo (contraire à « H3 seul ») : InfiniteTalk/MultiTalk, LongCat-Avatar, StableAvatar, MagiHuman, VideoX-Fun, LTX-Video-Trainer. Étoiles jugées gonflées : OpenMontage (75 k), VoxCPM (41 k), MoneyPrinterTurbo (137 k), VibeVoice (55 k), OpenCut (97 k), Open-Generative-AI (32 k) ; OpenShorts et ClippyMe dépendent d'`ultralytics` (AGPL d'après leur README) : idées seulement.

**Nouveautés depuis les rapports du 30/10** (déjà tranchés : FreeCut, Mediabunny, OpenCut, Remotion, Twick, Director's Console, ViMax, BeatDesign) : l'écosystème d'entraînement et d'outils H3 est apparu (LoRA H3 dans ai-toolkit, musubi-tuner, DiffSynth-Studio ; upscaler latent H3 ; nœuds de vidéo longue) ; Fish Speech a changé de licence (13/10) ; worker-comfyui est passé en AGPL.

## 8. Feuille de route priorisée (23 items)

Échelle. **Impact** 1–5 (effet sur la parité simple ou le niveau pro). **Effort** : S ≤ 3 jours, M 1–2 semaines, L 3–6 semaines, XL > 6 semaines (une personne ; estimations à valider, aucune mesurée). Les chemins sont relatifs à `app/` sauf mention. « Preuve » = ce qui doit être démontré dans le navigateur ou par mesure avant de cocher.

| # | Item | Imp. | Eff. | Composant à réutiliser (URL, licence, maturité) | Où l'accrocher dans le code | Preuve de fin |
|---|---|---|---|---|---|---|
| **R1** | **Image d'abord + brouillon** : la phrase donne 4 images clés (Qwen), l'utilisateur en choisit une, H3 l'anime ; brouillon en 768p avec les LoRA turbo 4 étapes avant le rendu final | 5 | S–M | rien de nouveau : Qwen-Image-2.1/2512 + H3 I2VA/FL2VA et bundle `h3-turbo` déjà dans `models.ts` | `server/nexora/creer.ts`, `reecritureImage.ts`, `film.ts` (planifier → images clés → valider → H3), `src/pages/Creer.tsx` | parcours complet ; coût brouillon vs final affiché ; temps mesurés |
| **R2** | **Presets de caméra à vignettes (60+)** rendues par H3 ; vocabulaire H3 | 4 | S | NickPittas/DirectorsConsole (MIT, 364 ★, 3 contributeurs, utilisable) ; Comfield (MIT) ; lightbrushproject/opensauce (MIT, prototype : 7 presets JSON, écrits pour LTX, à réécrire) | `src/catalog.ts` (`PRESETS`), `public/presets/<id>.mp4` (l'emplacement est déjà prévu dans le code), `Home.tsx`, `Video.tsx` | chaque preset a une vignette vidéo et son effet vérifié à l'œil |
| **R3a** | **Remettre Extend / Transitions / Suite** sur H3 (première+dernière image, chaînage de clips avec contexte de mouvement) | 4 | M | recettes de tritant/ComfyUI_MiniMax_H3_Extender (Apache-2.0, 363 ★, 242 commits) ; DiffSynth-Studio (Apache-2.0) | `server/graphs/h3.ts` (nouveaux constructeurs) à la place de `graphs/ltxtools.ts` (`buildExtendGraph`, `buildTransitionGraph`) ; `src/pages/Extend.tsx` ; `licences.ts` (nouvel ensemble permis au lieu de `ltx-tools`) | prolongement d'un plan de 5 s, transition entre deux plans, mesure de la couture (`seam.ts` existe) |
| **R3b** | **Speak v2 / lip-sync** : (i) H3 I2VA avec dialogues `<d>` dans le prompt (déjà possible) ; (ii) audio fourni → synchronisation des lèvres en post-traitement | 4 | M | bytedance/LatentSync (code Apache-2.0, 6,2 k ★, dernier commit 2025-06, 18 Go) ; TMElyralab/MuseTalk (MIT, 6,9 k ★, 2025-09) | nouveau `server/graphs/lipsync.ts` ; `server/index.ts` (bloc `b.kind === 'speak'`, ligne ~722) ; `src/pages/Speak.tsx` ; `registre.ts` | plan parlant avec voix du TTS (R13) ou fichier audio ; test sur GB10 d'abord (roues aarch64) |
| **R4** | **Édition d'image niveau Krea 3** : Qwen-Image-Edit-2511 + LoRA angles/relight, multi-références, annotation (flèche, cercle, zone) | 4 | S–M | Qwen-Image-Edit-2511 (Apache-2.0) ; `fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA` (Apache-2.0) ; FireRed-Image-Edit-1.1, JoyAI-Image-Edit-Plus (Apache-2.0) en A/B | `server/models.ts` (bundle `edit` : 2509 → 2511), `server/graphs/edit.ts`, `src/pages/Edit.tsx` (le masque existe déjà) | A/B sur nos visages de personnage ; temps par image mesuré sur GB10 |
| **R5** | **Master 4K / 60 i/s** : upscaler latent H3 ×2 + FlashVSR en mode rapide + interpolation RIFE | 4 | S–M | LBH-123-AI/Minimax_h3_latent_Upscaler (HF, Apache-2.0 étiqueté) ; OpenImagingLab/FlashVSR (Apache-2.0, 2 k ★) ; hzwer/Practical-RIFE (MIT) | `server/graphs/upscale.ts` (le mode « dream » LTX est remplacé), `server/models.ts` (`dir: 'latent_upscale_models'`), `src/pages/Upscale.tsx` | un plan H3 de 5 s livré en 2K/4K sans scintillement ; temps et mémoire notés |
| **R6** | **Personnages persistants (notre « Soul ID »)** v1 : feuille de personnage (Qwen-Edit-2511) + **H3 Ref2VA** + `@mentions` | 5 | M | ComfyUI natif H3 Ref2VA (bundle `h3-refs` déjà décrit dans `models.ts`) ; DiffSynth-Studio (exemple de LoRA d'identité H3, Apache-2.0) | `server/cast.ts` (le mode « feuille » LTX Ingredients devient « ref2va »), `server/graphs/h3.ts`, `src/castSheet.ts`, `src/pages/Cast.tsx`, `licences.ts` (`cast` : bloqué → permis après remplacement) | même personnage reconnu sur 3 plans de 3 scènes (similarité de visage mesurée contre les références) |
| **R7** | **LoRA de personnage, de style, de marque** en un clic | 4 | L | ostris/ai-toolkit (MIT, 13 k ★, supporte H3 et Qwen-Image, README ARM64/DGX Spark) ; repli kohya-ss/musubi-tuner (Apache-2.0) | nouveau `server/trainer.ts` branché sur la file de `server/jobs.ts` ; `server/loras.ts` (lecture des LoRA produits) ; `models.ts` ; UI dans Cast | LoRA de 15 images entraîné et appliqué ; durée mesurée sur 5090 et GB10 (cf. risque sm_121) |
| **R8** | **Juge visuel + 2 candidats + diagnostic et correction automatique** (budget de reprises annoncé) | 5 | M–L | Qwen3.8-27B (Apache-2.0) ou Nemotron-3-Nano-Omni (vidéo + audio, anglais) ou Qwen3-Omni (Apache-2.0, parole FR) ; identité : SFace/AuraFace | nouveau `server/nexora/juge.ts` (le rôle `juge` est déjà réservé dans `llm.ts`), `controle.ts` (contrôle qualité), `filmMoteur.ts` ; grille JSON du rapport 09 | sur un jeu de 40 intentions : le juge choisit comme un humain ≥ X % du temps (X à fixer avec le fondateur) ; coût GPU du double rendu mesuré |
| **R9** | **Agent « Producteur »** (équivalent de Supercomputer) : chat → plan → devis → exécution avec outils, mémoire de projet, « demander avant de générer » | 5 | L | `@modelcontextprotocol/sdk` (déjà dans le fork) ; idées OpenMontage (AGPL : lecture seule) ; skills du rapport 06 §6 | `server/nexora/llm.ts` (ajouter `tools` à `completer`), nouveau `server/nexora/agent.ts` (boucle bornée), outils = corps de `mcp/bodies.ts` filtrés par `licences.ts`, UI dans `src/studio/` | « fais-moi une pub de 30 s pour X » mène à un film assemblé après un seul devis validé |
| **R10** | **Studio de publicité** : produit/URL/photo → pub (image produit composée, plans H3, musique Music3, titres en code), variantes d'accroche | 5 | L | HyperFrames (Apache-2.0) pour les graphiques ; moteur de montage maison à porter : `marketing/nexora/outils/film.py` (fondus à l'image près, étalonnage, grain, mixage −14 LUFS) | nouveau `server/nexora/pub.ts`, `film.ts`, `src/studio/` | 3 variantes de format (16:9, 9:16, 1:1) d'une même pub à partir d'une photo de produit |
| **R11** | **Kit de marque** (logo, couleurs, polices, voix, interdits) appliqué à chaque rendu ; texte et logo toujours posés en code | 4 | M | skills `logo-design`, `color-expert` (rapport 06) pour construire le kit ; aucun composant à intégrer | paramètres d'organisation (`server/nexora/compte.ts`), `Creer.tsx`, `filmMoteur.ts` | un rendu d'organisation porte son logo et ses couleurs sans texte généré |
| **R12** | **Titres, sous-titres animés, lower thirds, cartons** rendus par HyperFrames | 4 | M | heygen-com/hyperframes (Apache-2.0, ~77 k ★, 143 auteurs, 2026-11-02) ; Magnific Move est bâti dessus | `mode-studio/src/features/nexora/` + `server/nexora/studio.ts` (nouvelle action `titres`), worker de rendu sur la VM Creative (Chromium + ffmpeg ; Playwright est déjà installé dans l'image du worker) | un titre animé et des sous-titres de style posés dans le Mode Studio, rendu identique deux fois |
| **R13** | **Voix** : TTS français, clonage avec consentement documenté, doublage traduit (STT → LLM → TTS → lip-sync) | 4 | L | QwenLM/Qwen3-TTS (Apache-2.0) ; resemble-ai/chatterbox (MIT) ; Parakeet (CC-BY-4.0) / whisperX (BSD-2) ; LatentSync (R3b) | nouveau `server/nexora/voix.ts` + `voix.py` (patron de `transcrire.py`) ; `registre.ts` (`famille: z.literal('video')` à ouvrir à `audio`) ; `src/pages/Speak.tsx` | extrait de 20 s doublé de FR en EN avec lèvres synchronisées ; écoute humaine du français (et du québécois) |
| **R14** | **Auto-montage « shorts »** : moments forts, silences (Silero), sous-titres au mot (whisperX), détection de plans, temps forts (beat_this), recadrage vertical | 4 | M | snakers4/silero-vad (MIT) ; m-bain/whisperX (BSD-2) ; Breakthrough/PySceneDetect (BSD-3) ; CPJKU/beat_this (MIT) ; **pas** OpenShorts (dépend d'`ultralytics`, AGPL) | `mode-studio/src/features/nexora/`, `server/nexora/studio.ts`, `server/whisper.ts` | une vidéo de 10 min devient 3 clips verticaux sous-titrés, sans intervention |
| **R15** | **Canvas nodal** (mode pro) : nœuds Texte, Image, Vidéo, Édition, Upscale, Musique ; compilé vers les graphes du serveur | 4 | XL | xyflow (MIT, 39 k ★) ; idées de raph651/open-source-canvas (MIT, prototype) et BeatDesign (Apache-2.0) | nouveau `src/pages/Canvas.tsx` ; `server/nexora/registre.ts` (nœuds typés) ; `server/engine.ts` | un graphe de 6 nœuds s'exécute et se rejoue ; chaque nœud affiche son coût |
| **R16** | **Applications partagées** (« Flows ») : un canvas ou une recette publiée avec champs d'entrée et un bouton, partagée dans l'organisation | 4 | M–L | aucun ; réutiliser `take_workflows` (`server/jobs.ts`) et `RECIPES` (`src/catalog.ts`) | `src/pages/` (page « Applications »), `server/nexora/` (publication d'une recette), `Home.tsx` | une recette publiée est relancée par un collègue avec ses propres entrées |
| **R17** | **Retake** : régénérer une partie d'un plan (de 2 s à 4 s) sans refaire le reste | 3 | L (R&D) | scripts `Retake` et `Fun-Controlnet-Union` de DiffSynth-Studio (`examples/minimax_h3/`, Apache-2.0) | `server/graphs/h3.ts`, bouton « Refaire ce plan » du panneau des plans (`src/FilmPlans.tsx`) | segment remplacé sans saut visible (mesure de couture) |
| **R18** | **Stage v2** : mise en place 3D → image clé (rendu raster) → H3 première image | 3 | M | three.js (déjà dans le fork) ; idées dennisonbertram/emulsion (MIT, jeune) | `server/stage.ts`, `server/stageRaster.ts`, `src/pages/Stage.tsx`, `licences.ts` | un plan 3D bloqué devient un plan H3 fidèle au cadrage |
| **R19** | **Son** : loudnorm en deux passes, ducking, séparation de pistes, SFX pour plans muets ; musique de repli ouverte | 3 | S–M | ffmpeg (déjà) ; adefossez/demucs (MIT) ; ThinkSound (Apache-2.0, prototype) ; Stable Audio 3 (licence communautaire Stability) ; ACE-Step 1.5 (MIT) | `server/nexora/film.ts` (lignes 187–188 : `loudnorm` en une passe aujourd'hui), `musique.ts` | niveau final à −14,0 LUFS mesuré ; pic ≤ −1 dBTP |
| **R20** | **API publique et MCP distant** avec clés et crédits (Higgsfield, Krea, Magnific, Hedra, Runway le font) | 4 | M | `@modelcontextprotocol/sdk` (transport HTTP streamable) | `mcp/server.ts` (stdio aujourd'hui), `server/nexora/auth.ts`, `credits.ts` ; retirer les outils bloqués | un Claude Code distant génère une vidéo et le crédit est débité |
| **R21** | **Bibliothèque intelligente et remix** : recherche par description, étiquettes automatiques, « recréer avec cette recette », fil de l'organisation | 3 | M | Qwen3-VL-Embedding-2B (Apache-2.0) ; SigLIP2 en repli | `server/jobs.ts` (prises), `Home.tsx`, `recipeUrl` de `catalog.ts` | rechercher « plan de nuit sous la pluie » retrouve les bonnes prises |
| **R22** | **Pack de skills Claude Code « nexora-creative »** (piloter le studio par MCP, règles de marque, prompts H3) | 3 | S | `anthropic-skills:skill-creator` ; voir `06-skills-claude-code-creation.md` §5 | dépôt (dossier `skills/`), `mcp/server.ts` | un agent externe réalise une vidéo par MCP sans appeler d'outil bloqué |
| **R23** | **Reframe et variantes de format** (9:16, 1:1, 16:9, 4:5) : régénération du fond (Expand existe en image) et recomposition des titres par HyperFrames | 3 | M | HyperFrames (Apache-2.0) ; Qwen-Edit Expand (déjà) | `server/nexora/film.ts`, `src/pages/Edit.tsx` (Expand), `mode-studio` | un film 16:9 devient un 9:16 sans recadrage aveugle |

### 8.1 Ordre proposé (par vagues)

| Vague | Items | Pourquoi dans cet ordre |
|---|---|---|
| **0 — cette semaine** (effort S, valeur immédiate) | R2, R19 (passage loudnorm en deux passes), R22, début de R1 | gains visibles sans risque ; R2 débloque une vitrine crédible |
| **1 — parité du mode simple** (≈ 6 semaines) | R1, R3a, R3b, R4, R5, R6, R8, R11, R12 | rebâtit les fonctions inertes sur H3, ajoute la cohérence de personnage et le juge qui font la différence de qualité perçue |
| **2 — intelligence et valeur commerciale** | R9, R10, R7, R13, R14, R20 | l'agent et la publicité ont besoin de R6, R8, R11, R12 ; la voix demande les bancs d'écoute |
| **3 — mode pro et écosystème** | R15, R16, R17, R18, R21, R23 | le canvas n'a de sens qu'une fois les briques (R1 à R14) stables et typées dans le registre |

**Prérequis hors liste** (déjà prévus par `ARCHITECTURE-NEXORA-CREATIVE.md` et `docs/ETAT.md`) : routes de crédits et de stockage côté site, file de jobs PostgreSQL (pg-boss quand SQLite ne suffira plus), H3 installé aussi sur le GB10 (disque), RTX 5080. Sans les crédits côté site, R20 et R10 ne sont pas facturables.

**Indicateurs de réussite proposés** : temps entre la phrase et la première vidéo ; taux de plans acceptés sans « Refaire » ; similarité de visage d'un personnage sur 3 plans ; durée et coût GPU par minute de film fini ; part des rendus passés par le juge qui sont retenus par l'utilisateur.

## 9. Points de décision pour le fondateur (sans analyse juridique)

1. **Lip-sync et avatars** : LatentSync et MuseTalk retouchent un plan H3 existant (compatibles avec « H3 seul »). Les générateurs d'avatar (InfiniteTalk image+audio, OmniAvatar, LongCat-Avatar…) sont un second moteur vidéo : **non proposés** tant que la règle H3-seul tient.
2. **Image** : Qwen-Image-2.1 est en production (décision du 01/11) ; ses alternatives sous Apache (2512, Edit-2511) restent prêtes en repli. Aucune analyse ici.
3. **Clonage de voix** : exiger le consentement documenté de la personne, comme pour les références de visage (le registre Cast prévoit déjà ce principe).
4. **Positionnement par le prix** : repères publics au 02/11 — Higgsfield Plus 59 $ (1 200 crédits), Runway Standard 15 $ (625 crédits), Pika Starter 10 $ (900 crédits), Krea Basic 9 $, Magnific Premium ~20 $. Notre grille (0,5 crédit/s de GPU) reste une proposition non validée.
5. **Ce qui rend Nexora différent** : puisque les leaders offrent aussi H3, parier sur la cohérence (R6, R7), le juge (R8), le montage pro, la confidentialité hébergée au Canada et la publicité clé en main (R10).

## 10. Ce que je n'ai pas pu vérifier

- **Rien n'a été exécuté** : ni le code de Nexora (l'état « marche/bloqué » est déduit de la lecture et de `docs/ETAT.md`), ni aucun modèle ou projet ouvert. Aucune preuve de fonctionnement sur GB10 (aarch64, sm_121) ou RTX 5090 ; seules des mentions documentaires (ai-toolkit pour ARM64/DGX Spark, ACE-Step pour aarch64 CUDA 13).
- **Higgsfield** : dates incohérentes dans son changelog (Cinema Studio 4.0 : 11 août, 12 août, communiqué du 28 octobre ; Seedance 2.5 : 3 ou 7 août ; Soul 2.0 : 9 ou 19 février) ; nombre de photos de Soul ID contradictoire (5+, 10–20, 20–80) ; le coût de 25 crédits du Soul ID vient d'un billet de blog relayé ; Popcorn, Upscale, Relight, Speak 2.0 : pas de page produit officielle lue ; « Recast » : aucune entrée sous ce nom (équivalents : Character Swap, Face Swap, Genjutsu) ; l'arrêt de Sora est affirmé par un seul comparatif tiers.
- **Kling** : site rendu en JavaScript, accueil seul lu ; prix et spécifications 4.0 viennent de tiers (CometAPI et autres), pas de notes de version officielles. **Pika 2.5** : pas de date officielle. **Luma** : article Ray3.2 en 404 ; aucune annonce « Boards » autonome trouvée. **Runway** : Gen-4.5 successeur, GWM Worlds 2 et prix Team via sources secondaires.
- **Pages inaccessibles** (403 ou anti-bot) : tarifs Leonardo, accueil et tarifs Magnific, Adobe « What's new ». **Aucun test d'usage** : aucun compte créé, rien acheté.
- **Modèles** : vitesses sur RTX 5090 (aucune mesure datée pour Qwen-Image-2.1, FLUX.3 Klein, Fibo, MOSS ni pour les modèles audio) ; classements Artificial Analysis sans date visible ; qualité du **français** (et du québécois) de tous les TTS non testée ; licences non lues : SAM 3 (texte), MatAnyone2, Krea 2, DeepFilterNet, ClearerVoice, checkpoints BS-RoFormer ; Real-ESRGAN, CCSR, DiT4SR, STAR, GIMM-VFI, OmniGen2, Step1X-Edit, BAGEL non examinés ; le PR ComfyUI du chargement natif de l'upscaler H3 (17412, 2026-10-28) n'est attesté que par une source secondaire alors que notre moteur est en 0.43.x.
- **Projets ouverts** : étoiles en valeurs arrondies (shields.io) et souvent suspectes ; contributeurs comptés par noms d'auteur Git ; licences des poids annexes (LatentSync OpenRAIL++, InsightFace, pyannote, séparateurs de stems) non lues ; dépôts GitHub de LBH-123 (upscaler H3) introuvable ; TwitCanva, ComfyTV, Comfield, Rosesfield, Director's Console repris des rapports 01 et 05 sans relecture.
- **Injection** : la page « llm-info » de Luma contient des consignes de nommage adressées aux assistants IA ; les enquêteurs les ont ignorées et n'en ont repris que les faits de produit. Une réponse d'outil de recherche contenait aussi des « conseils d'agent » (crédits faibles, lien de facturation) ; ignorés. Aucun dépôt cloné ne contenait d'instruction adressée à un agent.

## Sources principales

- Higgsfield : higgsfield.ai/creator-hub/changelog ; higgsfield.ai/pricing ; higgsfield.ai/camera-controls ; centre d'aide (Soul ID, Marketing Studio, Apps) ; communiqué Cinema Studio 4.0 (Yahoo Finance) ; Trustpilot.
- Runway : runway.com/changelog, runway.com/pricing, docs.dev.runwayml.com/api-details/api_changelog. Luma : lumalabs.ai/news, lumalabs.ai/pricing. Pika : pika.art, pika.art/pricing. Kling : kling.ai ; cometapi.com/kling-4-0-explaineds-guide.
- Krea : krea.ai/release-notes. Adobe : helpx.adobe.com/creative-cloud/apps/generative-ai/non-adobe-models-in-adobe-products.html. Magnific : magnific.com (blog Move, Flows, One). ComfyUI : docs.comfy.org/changelog.
- Modèles : Artificial Analysis (text-to-image, édition) ; cartes Hugging Face citées ; forum NVIDIA (Qwen-Image-2.1 sur DGX Spark, fil 384774 ; FLUX.2 NVFP4, fil 376106) ; blog Sogni (upscale H3).
- Dépôts : voir les URL du §7 ; clones de travail sous le dossier temporaire de session (non conservés).
