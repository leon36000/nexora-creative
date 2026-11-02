# 12 — Les quatre vidéos Higgsfield d'octobre 2026 : ce qu'elles montrent, ce qui nous manque, 12 ajouts classés (2 novembre 2026)

Extension de `07-creative-vs-higgsfield-feuille-de-route.md` (ses numéros R1 à R23 sont repris, pas refaits). Le fondateur veut atteindre le niveau de Higgsfield ou le dépasser.

## 0. Méthode et limites (à lire d'abord)

- **Vues** : titre, chaîne, date, description, chapitres et **transcription automatique anglaise** des quatre vidéos (yt-dlp). Pour `ktGkJfxNN9M` (28 min), j'ai lu la transcription entière en recherche par mots-clés (crédits, Claude, skill, élément, brouillon, budget), pas ligne à ligne. Les trois autres ont été lues en entier.
- **Images** : copie 360p de chaque vidéo, une planche de 16 images uniformément espacées par vidéo (pas de détection de changement de scène), regardées une à une. À 360p et avec 16 images pour 11 à 28 minutes, **les écrans d'interface ne sont lisibles qu'en gros** (boutons, grilles de prises, volet de commentaires) ; aucun texte de prompt ne l'est. Les liens « tous les prompts et assets » (`higgsfield.ai/s/…`) n'ont **pas** été ouverts. Copies supprimées après usage (23 Mo de texte restent hors dépôt).
- **Sources produit** : changelog officiel `higgsfield.ai/creator-hub/changelog` (lu par extraction), billet Katana officiel, dépôts de skills tiers (étiquetés TIERS). Étiquettes : [VIDÉO] ce qui est dit ou montré par l'auteur, [OFFICIEL] page Higgsfield, [TIERS].
- **Côté Nexora** : lecture de `docs/ETAT.md`, de `recherche/07`, de `app/src/pages/`, de `app/server/nexora/` et de deux captures de `captures-v3/` ; **rien n'a été exécuté**. Les efforts (S ≤ 3 j, M 1–2 sem., L 3–6 sem.) sont des estimations non mesurées.
- Ce sont des **vidéos promotionnelles de la marque** (même présentateur, Adil, sur les quatre) : les affirmations de gain de temps et d'argent sont celles de Higgsfield.

## 1. Constat d'ensemble : le produit est devenu « Claude + Higgsfield »

Les quatre vidéos datent de octobre 2026 et ne montrent presque plus l'interface Higgsfield seule. Le schéma commun : **un chat Claude (Opus 5.5) connecté par MCP à Higgsfield, chargé de « skills » (fichiers de savoir-faire)**, qui écrit les prompts, branche les références par leur nom, lance les rendus et monte. Higgsfield devient un moteur de génération dans la conversation de l'utilisateur. Les skills cités : *directing workflow*, *acting*, *fighting*, *dance direction*, *anamorphic lens*, *clipping*, *motion system*, *generation* ; produits maison côté Claude : **Katana** (montages), **Ad Multiplier**, **Supercomputer** (analyse de vidéo de référence) [OFFICIEL : changelog, 27/05 et 06–08/10/2026].

Conséquence pour nous : notre « Producteur IA » (02/11) est l'équivalent de ce chat, mais **enfermé dans notre interface** et avec **cinq** compétences seulement (`app/server/nexora/competences/*.md`). Higgsfield gagne la préférence par trois leviers que nos rapports précédents sous-pesaient : les compétences de métier, les références multimodales de correction, l'acquisition par le chat de l'utilisateur.

## 2. Notes par vidéo

### 2.1 `ktGkJfxNN9M` — « I Spent 72 Hours Making This AI Commercial With Seedance 2.5 » (Higgsfield AI, 30/10/2026, 27 min 55 s, 93 k vues)

**Ce qui est montré** : une publicité de sport de 2 min (trois héros : gardien de but blessé, danseuse, élève « nerd » ; script en quatre temps *setup, problème, choix, résolution*), fabriquée en trois étapes : **assets, scènes, montage**.
**Fonctions et flux** :
1. Histoire réduite à une **liste de personnages, tenues et lieux**, un dossier par héros dans un projet Cinema Studio.
2. **Fiche de personnage standard** (fond gris, vues du corps sans la tête, gros plan du visage) générée en 4 options avec Soul Cinema (« peau réelle »), enregistrée comme **élément nommé** ; **la même image et le même nom sont donnés à Claude**, donc le prompt collé en retour rattache l'élément tout seul.
3. **Tenue** : Claude écrit le prompt d'édition, Seedream (« C Dream ») change l'habit en gardant le visage ; variante « avec attelle ».
4. **Compétence « directing workflow »** (téléversée une fois dans Claude : Personnaliser → Skills) : transforme une scène en plan de tournage, **un bloc = un prompt = plusieurs scènes**, décide mouvement de caméra, état émotionnel, **jeu du visage beat par beat**.
5. **Presets de couleur par code hex** choisis avant génération (essai « Twilight Fable » : trop violet, abandonné).
6. **Brouillons 480p** (26 s, 9 plans) pour juger mouvement et cadre ; **seules les prises retenues sont refaites en 1080p** ; les scènes finales viennent de **plusieurs prises** (sprint et chute d'une prise, demi-tour d'une autre, coach d'une troisième).
7. **Corriger par la référence, pas par les mots** : le présentateur **se filme lui-même** (genou haut une foulée sur deux) et joint le clip comme référence de mouvement ; pour le tunnel, il **dessine un croquis** (bleu = gardien, jaune = coach) qui donne les positions ; pour le dîner, scènes demandées ensemble à Claude puis recadrées ; une feuille de quatre coéquipiers évite les figurants aléatoires.
8. Compétence « danse » fabriquée en donnant à Claude des vidéos d'amis qui dansent ; comparaison côte à côte avec et sans la compétence.
9. Montage dans un éditeur à timeline (capture : pistes vidéo en vert, aperçu au centre).
**Chiffre** : **« environ 8 500 crédits en comptant les prises non retenues »**, 72 h de travail, contre « des centaines de milliers de dollars et des mois » pour un tournage réel [VIDÉO].
**Ce qui fait « premium »** : film complet montré **d'abord** (2 min), puis la fabrication ; barre de progression à quatre cases (Setup / Problème / Choix / Résolution) qui se remplit pendant l'explication ; chaque plan est nommé selon son rôle narratif ; prises comparées côte à côte, échecs montrés, **coût total annoncé**. Fin sur une surimpression de commentaires de spectateurs (preuve sociale).

### 2.2 `wFbgrPmVXb0` — « How I Make Realistic AI Short Films Using Seedance 2.5 » (24/10/2026, 21 min 26 s, 214 k vues)

**Ce qui est montré** : court métrage d'action noir (vampire contre mafia), « fait en deux jours ». Mêmes outils : Cinema Studio, Seedance 2.5, Claude + compétences.
**Fonctions et flux** :
1. **Réalisme avant tout** : GPT Image 2.5 donne une peau « plastique » qui bouge mal en vidéo ; remède : Seedream avec **références de texture** (peau, cheveux, tissu, fond), « comme texturer un personnage 3D » ; comparaison côte à côte.
2. **AI Cast** : choix par budget, époque, archétype → lot de visages → choix ; les rôles secondaires sont générés avec Soul Cinema.
3. **Élément vidéo = visage + voix** : « un élément image donne l'apparence, **un élément vidéo donne aussi les mouvements du visage et la voix** » ; l'auteur enregistre sa propre voix et celle d'amis ; plus de prises gâchées sur des visages qui bougent mal.
4. **Lieux et objectifs** : cabine téléphonique en 24 mm bords doux et bokeh ovale, bureau en anamorphique 35 mm ; **compétence « anamorphique »** pour répéter les détails d'optique.
5. **Boucle de scène** : Claude reçoit le fichier du personnage et son nom, une **compétence de conflit** (« qui veut quoi ») construit la scène, puis Claude écrit le prompt avec second par second, caméra, jeu ; 2 à 4 prises par lot.
6. **Brouillons 480p** pour voir les prises et qui se tient où, puis 1080p des prises gardées.
7. **Foule** : « chaque figurant a un rôle » ; **compétence de combat** (la même scène sans elle est « raide ») : la chorégraphie est écrite en liste (où va le pied, comment le coup touche, comment le garde tombe).
8. **Cacher les coupes** : coupe sur un mouvement (whip pan), prises de lots différents combinées ; **relight** d'une prise « trop froide et bleue » au lieu de refaire ; **second côté de la pièce** générée pour champ/contrechamp.
9. **Acting skill** : prompts « autour de ce que chaque personnage veut de l'autre » ; trois corrections données à Claude (réplique raccourcie, pas de verre, place pour des pauses) ; la balle qui change d'une prise à l'autre est fixée par **deux références (balle, blessure)** et cachée derrière le dos d'Adam.
10. **Blocage** : un **tour de la pièce en vidéo** sert de référence de géométrie ; une seule vidéo donne **de nouveaux angles** ; **Extend** dans Cinema Studio pour finir un geste ; prolongation vers l'avant.
**Wow** : prise 4 sélectionnée dans une **grille « Take 01 à 04 »** avec chronologie des prises choisies ; plans de combat en corridor ; dialogue à pistolet dans le bureau.
**Ce qui fait « premium »** : bande-annonce en ouverture (« cold open ») avec un faux conflit comique entre le héros du film et le présentateur ; chaque étape est suivie d'un **extrait « Watch »** du résultat ; tous les prompts livrés par lien.

### 2.3 `rZvF_EWZoHw` — « Claude Opus 5.5 Made Clipping The Easiest Side Hustle of 2026 » (11/10/2026, 13 min 25 s, 167 k vues)

**Ce qui est montré** : le **clipping** (montages « aura » et teasers à partir de films et de podcasts) fabriqué par **Katana** dans Claude, sans logiciel de montage.
**Fonctions et flux** :
1. Ouvrir Claude, choisir Opus 5.5, **connecter Katana par MCP**, ajouter la compétence « clipping ». Entrées : **film, podcast ou simple lien**, une **vidéo de référence** (« une mauvaise référence donne un mauvais résultat » : choisir par vues, mentions et commentaires), la **musique**. Consignes : durée, vertical, accroche forte, rythme de la référence, **coupes calées sur la musique**, **rapport après chaque étape**.
2. Sortie : Katana analyse le film, **repère les moments forts**, choisit l'accroche, monte autour de la référence et de la musique ; « chaque coupe tombe sur le temps fort » ; le style de la référence est reproduit « presque un pour un ».
3. **Podcast** : l'agent trouve une phrase qui se tient seule, ajoute **sous-titres et graphiques** et **génère des visuels** autour de la parole ; tout dans un seul chat (« sinon : générer, garder le style, animer, importer, monter »).
4. **Lot** : « dix montages à partir du même film, moments et accroches différents » en environ une heure d'IA et 20 min de relecture ; **plusieurs teasers** d'un même film avec des angles différents ; teaser de 30 s à partir d'un **film de 2 h** (l'IA choisit ce qu'on révèle et où on laisse en suspens).
5. **Traduction** de l'édition en d'autres langues (« versions coréennes »).
**Claims** : 0,50 $ les 1 000 vues éligibles ; forfait de 500 $ pour 10 clips par mois avec bonus de performance de 50 $ par clip à 100 000 vues ; « 3 milliards de dollars » d'économie du clipping en 2026 ; un streamer aurait dépensé 1,4 M$ en 5 semaines [VIDÉO, non vérifié par moi]. La vidéo vend un **revenu** (démarcher studios, streamers, podcasteurs), pas un outil.
**Interface** : capture d'une **galerie de presets Katana** (vignettes verticales) dans la conversation ; les étapes de l'agent défilent (« inspecter la section à plus haute résolution », « cartographier coupes et transitions »).

### 2.4 `5HYYXYYCrL4` — « Claude Opus 5.5 + Higgsfield Make Insane Motion Graphics! (Claude Motion) » (13/10/2026, 10 min 46 s, 344 k vues — la plus vue)

**Ce qui est montré** : **Claude Motion** (artefact « Motion » de Claude : motion design **écrit en code**, rendu en vidéo) + Higgsfield pour les plans générés ; trois défis.
**Fonctions et flux** :
1. **Défi 1 : refaire une vidéo de lancement virale** (référence téléversée : « rebâtis le mouvement en code, génère les plans avec Higgsfield, garde tout éditable ») ; première version : mouvement bon, plans à retravailler ; **deuxième message** : « garde le mouvement, améliore les lieux et les actions, nettoie le logo et l'audio » ; **export vers After Effects avec calques éditables**.
2. **À partir de trois liens Instagram seulement** : film original de 20 s ; **édition en direct** : changer le texte (la mise en page se recalcule), masquer ou déplacer un calque, **changer palette, police, vitesse**, allonger une séquence : « les scènes liées suivent et la musique reste synchronisée » ; six scènes (sphère de particules, grille de points, ventilateur 3D) codées en 3 h contre « environ une semaine » pour un motion designer [VIDÉO].
3. **Défi 2 : pub 3D de produit** à partir d'une référence ; « remplace le camion par ce vélo » (échange de produit en une phrase) ; **export Blender** (plans, timing, caméras).
4. **Vidéo SaaS** : compétence « motion system » qui apprend la charte.
5. **Défi 3 : court métrage 2D** (chat qui voyage avec un passeport) : voix générées via HeyGen, cartes et pages animées en code, **plans générés remplacés un par un** (« je régénère seulement les plans à corriger, cela économise des crédits »).
6. **Corrections par commentaires épinglés** sur la lecture vidéo : on clique sur un instant, on écrit « @Claude remplace l'entrée flottante par un pas posé… » avec une case **« Envoyer à Claude »** ; version corrigée en retour. Une version courte de 90 s devient **10 minutes** « en HTML ».
**Ce qui fait « premium »** : la vidéo a de 1,6 à 3,7 fois plus de vues que les trois autres : la promesse « **je garde la main sur le résultat** » (calques, palette, texte, export vers les outils pro) pèse plus que la génération ; la page de titre présente trois défis comme un jeu à niveaux.

## 3. Ce que Higgsfield a de plus, hors des quatre vidéos (mise à jour du 02/11, en complément de `07` §3.1)

| Élément | Contenu | Source |
|---|---|---|
| **Katana** (08/10) | skill Claude : une vidéo de référence ou un preset de la bibliothèque (styles Aura farming, Motion, Clipping) + **jusqu'à cinq photos** (personnages, produits, vêtements) → montage refait avec vos éléments ; **durée, ratio et cadence repris de la référence** ; sortie dans le chat et dans Assets ; même abonnement, **pas de supplément pour le MCP** ; formulaire sur le site à trois champs (vidéo, personnages, consignes facultatives) | OFFICIEL (billet + changelog) |
| **Ad Multiplier** (06/10) | skill Claude : une pub devient **plusieurs variantes** (mêmes vidéo, montage, rythme ; autres personnages, vêtements, lieux, objets) | OFFICIEL |
| **Analyse et recréation de vidéo dans Claude** | le skill Supercomputer découpe structure, plans et rythme d'une vidéo déposée et génère les éléments | OFFICIEL (changelog) |
| **MCP** (avril–mai 2026) | cinq outils exposés ; `claude mcp add higgsfield https://mcp.higgsfield.ai/mcp` ; **CLI** `higgsfield generate create <modèle> …` | OFFICIEL + TIERS |
| **Cinema Studio 4.0** | 30 s par génération, **50 références**, 30+ mouvements de caméra, 4 types de caméra, 5 optiques, **50+ palettes**, **Emotion Wheel** (8+ émotions), sélecteur d'**époque**, **tempo** (vitesse des coupes), **Extend** avant et arrière | OFFICIEL (changelog) |
| **Seedance 2.5 via Higgsfield** | quatre modes (`t2v`, `omni_reference`, `video_edit`, `video_extension`), 4–30 s, jusqu'à 1080p, références jusqu'à 30 images / 10 vidéos / 10 audios | TIERS (bibliothèque de skills, 819 étoiles) + CLI |
| **Content Factory** (22/10) | un sujet « et si… » → script, personnages, scènes avec voix off, montage ; 15 s à 5 min, 1 à 4 épisodes par lancement, **50+ formats** ou vos formats appris par liens ; chaque réplique de voix refaisable seule | OFFICIEL |
| **Playable** (26/10) | description ou vidéo de gameplay → jeu mobile jouable dans le navigateur ; publicités jouables (Enterprise, export HTML ≤ 5 Mo) | OFFICIEL |
| **Community** (15/10), **Grants**, **Weekly Challenge** (21/10) | fil public (Projets, Plans, Créateurs, Concours, Originaux) ; subvention jusqu'à 200 000 crédits pour un projet ouvert d'au moins 1 min ; défi hebdomadaire de 120 s, 30 000 / 20 000 / 10 000 crédits | OFFICIEL |
| **3D Angles** (19/10) | plugin ChatGPT : photo ou texte → scène 3D reprenable sous d'autres angles, 24–300 mm, f/1,4–f/16, jusqu'à 30 s, brouillons | OFFICIEL |
| **Autres** | Genjutsu Lite (19/10), mise à jour FLUX 3 Video Upscaler (15/10), support du chinois (20/10), Kling 4.0 (21/10), modèles de langage (GPT-6.1, Kimi K3.1) dans le chat | OFFICIEL |

Le reste (Soul ID, Elements, tarifs, Popcorn, Canvas, Apps, Speak) est dans `07` §3.1.

## 4. Les huit recettes que les vidéos enseignent (au-delà des 11 de `07` §3.2)

1. **Les compétences de métier sont le produit** : combat, jeu d'acteur (« ce que chacun veut de l'autre »), danse (pas nommés), optique anamorphique, scène (but / obstacle / retournement). L'auteur les fabrique en donnant des vidéos d'exemple à Claude.
2. **Fiche d'abord, scène ensuite** : fond gris, corps sans tête, gros plan ; tenue par édition ; nom identique chez l'IA et dans l'outil.
3. **Brouillons 480p, prises multiples, finale seulement des prises gardées**, puis **mélange de prises de lots différents** dans le montage ; coût total affiché, **prises ratées comprises**.
4. **Corriger avec un média, pas avec des mots** : clip filmé au téléphone (mouvement), croquis (positions), tour de pièce en vidéo (géométrie), deux images (accessoire exact).
5. **Relight et nouveaux angles au lieu de relancer** ; coupes cachées par un mouvement.
6. **Le projet reste éditable** : calques, palette, police, durée ; export vers After Effects et Blender ; **régénération d'un seul plan** ; commentaires épinglés sur la timeline.
7. **Référence → recréation** : on dépose un montage qu'on aime, on fournit ses photos, l'agent refait ; pas de réglage de durée, ratio, cadence.
8. **« Tous les prompts et les assets » en lien** sous chaque vidéo : chaque démo est un **pack de recette** copiable.

## 5. Nexora Creative face à cela

Ce que nous avons déjà (preuves dans `docs/ETAT.md` du 02/11, captures `marketing/creative/captures-v3/`) : le Producteur IA avec plan, devis calculé par le code et validation d'un clic (capture 01) ; le juge visuel et les « 2 prises par plan » ; Prolonger et Raccord sur H3 ; cartons en code ; musique Music3 ; Explorer à 8 modèles prêts à produire (capture 06) ; 16 mouvements de caméra à vignettes ; Cast `@` en images fixes (`app/src/mentions.ts`, `server/cast.ts`) ; Couverture 9 plans, Angle, Relight, Expand sur Qwen-Image-Edit ; montage FreeCut avec exports ProRes et XML ; MCP à 22 outils (stdio) ; interface mobile.
Ce que nous n'avons pas : personnages persistants en **vidéo** (Ref2VA présent, non branché), brouillons 480p et grille de prises, références vidéo/croquis, lip-sync et voix, API distante.

### 5.1 Tableau : fonction Higgsfield → nous aujourd'hui → écart → plan avec nos seuls moteurs → effort / impact

H3 n'a pas de mode « modifier une vidéo existante » ni de transfert de mouvement : tout ce qui y ressemble passe par **image clé (Qwen-Edit) puis H3 I2VA/FL2VA/Ref2VA**, ou par DiffSynth (Retake, ControlNet), jamais mesuré chez nous. Je l'écris pour chaque ligne concernée.

| Fonction Higgsfield | Nous aujourd'hui | Écart | Plan (H3, Qwen-Image, Music3, ouvert) | Eff. / Imp. |
|---|---|---|---|---|
| Éléments `@` (personnage, lieu, accessoire) en vidéo, dossier par héros, rattachement par le nom | Cast `@` en **images fixes** ; vidéo bloquée (LTX) | personnage non constant d'un plan à l'autre | Fiche standard Qwen-Edit (fond gris, corps sans tête, gros plan) + **H3 Ref2VA** ; nom du fichier = nom de la mention ; dossier de projet « Distribution » (R6) | M / 5 |
| Tenues et variantes d'un personnage | Qwen-Edit sur image | pas de « garde-robe » liée au personnage | Fiche de tenue par édition (visage verrouillé par recadrage), rangée sous l'élément | S / 3 |
| Lieux en cinq vues + second côté de la pièce | Couverture 9 plans, Angle | pas de fiche de lieu réutilisable | Fiche de lieu Qwen-Edit (5 vues, plan de situation) attachée à Ref2VA | S–M / 4 |
| Brouillon 480p puis finale des prises gardées | « Rapide / Qualité max » ; juge à 2 prises | pas de brouillon, pas de grille de prises, pas de compteur incluant les rejets | Brouillon 768p turbo (R1), grille « Prise 1–4 », refaire en cinéma seulement les choisies, compteur de projet | M / 5 |
| Mélange de prises de lots différents | Montage sans rendu (ordre, coupe, fondu) | pas de « choix de prise par plage » | Dans le panneau des plans : choisir, par plan, une prise ou un extrait de prise (début/fin) ; coupe sur mouvement proposée par le code | S–M / 4 |
| Compétences de métier (combat, acting, danse, anamorphique) | 5 compétences invisibles | peu nombreuses, non choisies, non partageables | Bibliothèque de 20+ fichiers `competences/*.md` versionnés, **cases dans l'interface**, injectés dans le Producteur (R22) | S–M / 5 |
| Presets : couleur hex, 65 caméras, époque, tempo, Emotion Wheel | 27 presets en texte, 16 caméras à vignettes, axes époque/pellicule/étalonnage | pas d'émotions pilotées, pas de palettes en vignettes | Presets rendus par H3 (R2), palettes hex en puces, roue d'émotions = champ « jeu » du prompt écrit par la compétence acting | S / 3 |
| Référence de mouvement filmée au téléphone | rien | pas de « montre-moi » | **Qwen3-Omni/VL décrit le clip seconde par seconde** → prompt chronométré ; **pas de transfert de mouvement réel** (limite H3) ; repli : image clé tirée du clip | M / 4 |
| Croquis de blocage (positions) | rien | pas de dessin | Croquis → Qwen-Edit rend l'image clé avec les positions → H3 I2VA | S–M / 4 |
| Tour de pièce en vidéo, nouveaux angles depuis une prise | Couverture / Angle sur image | pas depuis une prise vidéo | Extraire des images de la prise → Qwen Angle/Couverture → I2VA/Ref2VA avec les mêmes éléments | M / 4 |
| Relight d'une prise sans refaire | Relight en image | pas sur vidéo | Relight de l'image clé + nouvelle prise I2VA ; **pas de relight vidéo** direct | M / 3 |
| Extend avant/arrière | Prolonger (vers l'avant), Raccord | pas vers l'arrière | Arrière : générer le plan précédent avec **dernière image = première image de la prise** (FL2VA) | S / 3 |
| Fiche de combat / foule / jeu d'acteur | rien | qualité d'action | Compétences écrites ; juge visuel vérifiant « corps déformé, main en trop » (R8, existant) | S / 4 |
| **Katana** : montage refait d'après une référence + 5 photos | assistant de montage (silences, sous-titres, rythme) | pas d'analyse de référence, pas de recréation | Détection de plans, temps forts (beat_this), parole (whisperX), analyse Qwen-Omni ; **recomposition avec nos médias, titres HyperFrames, plans H3 manquants** (R14+R12) | L / 5 |
| Clipping : moments forts, shorts, teasers, lots de 10, traduction | sous-titres au mot, silences | pas de sélection de moments ni de lot | Sélection par LLM sur transcription + scènes ; lot de N montages ; sous-titres traduits (R14) | M / 4 |
| **Ad Multiplier** | Producteur : variantes d'une pub | pas d'échange de produit, d'acteur ou de lieu | Même plan de montage, images clés refaites par Qwen-Edit avec les nouveaux éléments, Ref2VA ; accroches multiples par le LLM (R10) | M–L / 4 |
| **Claude Motion** : projet éditable, calques, palette, export After Effects/Blender | cartons en code (libass) ; FreeCut | pas de projet à calques ; pas de commentaires épinglés | HyperFrames (HTML → vidéo, Apache-2.0) comme moteur de graphiques ; paramètres exposés (texte, palette, police, durée) ; **commentaire épinglé → Producteur** ; export ProRes/XML déjà là (R12) ; **pas d'export After Effects/Blender** prévu | L / 5 |
| Régénérer seulement les plans à corriger | « Refaire ce plan » | OK sur la vidéo ; pas sur les calques | Garder, un projet = liste de plans + calques ; régénération ciblée | S / 3 |
| MCP et skills dans Claude | MCP stdio (22 outils) | non distant, sans compte, sans skill publié | MCP HTTP avec clés et crédits ; pack de skills `nexora-creative` (R20, R22) | M / 4 |
| Voix : élément vidéo avec voix, doublage, lip-sync | dialogue `<d>` dans H3 ; Speak retiré | pas d'audio fourni, pas de voix choisie | TTS + clonage avec consentement, LatentSync (R3b, R13) ; la voix de H3 reste imprévisible | L / 4 |
| Content Factory (sujet → épisodes, 50 formats) | Explorer (8 modèles), Producteur | catalogue étroit | 50 formats = 50 « recettes » du Producteur (fichier + vignette) ; lots d'épisodes | S–M / 3 |
| Community, Grants, défi hebdomadaire | rien | pas d'effet de réseau | Fil d'organisation + pages publiques de « recettes » (R21) ; défi mensuel plus tard | M / 3 |
| Playable, 3D Angles | Objet 3D ; Stage retiré | hors cœur | **Ne pas suivre** pour l'instant | — |
| Elements/Characters, upscale, voix, tarifs, canvas, apps | voir `07` §4 | voir `07` | voir R5, R7, R15, R16 | — |

## 6. Les 12 ajouts les plus rentables, classés

Classement : valeur pour atteindre « le niveau de Higgsfield en mode simple », avec ce que les vidéos font voir. Chaque entrée dit **ce que voit et clique l'utilisateur** et **ce que fait l'IA**. Les numéros R renvoient à `07` §8.

**1. Éléments `@` persistants en vidéo : « ma distribution » (R6 enrichi)** — Eff. M, Imp. 5. Dans Créer, une colonne « Distribution » (personnages, lieux, accessoires) avec un bouton « Ajouter ». L'utilisateur dépose une photo ou écrit un mot ; l'IA génère **la fiche standard** (fond gris, corps sans tête, gros plan) en quatre options, il en clique une, tape un nom. En écrivant `@Mado` dans une phrase ou dans le Producteur, l'élément s'attache seul (H3 Ref2VA). Une ligne « Tenues » permet d'ajouter des habits (« avec un tablier rouge ») ; la fiche de lieu donne cinq vues. L'IA verrouille le visage par recadrage, écrit la description invariante de la bible de continuité et la répète telle quelle dans chaque plan. Preuve visée : même visage sur deux plans de deux prises, jugé par le juge visuel puis par un humain.

**2. Prises : brouillon, grille, finale (R1 + R8 étendus)** — M / 5. À côté de « Valider et lancer », une case « Brouillon d'abord » : le Producteur rend 2 à 4 **prises en 768p turbo** par plan et affiche une **grille « Prise 1 à 4 »** (comme dans la vidéo wFbg). L'utilisateur clique la meilleure ou laisse le juge choisir ; seules les prises retenues sont refaites en qualité cinéma. Un **compteur de projet** (« 8 prises, dont 5 non gardées : 612 crédits ») est toujours visible, avec le coût prévu avant chaque lancement. L'IA explique en une ligne pourquoi elle recommande une prise (« visage stable, mouvement net »).

**3. Bibliothèque de compétences visibles et 50 formats** — S–M / 5. Un onglet « Savoir-faire » : des cartes « Combat », « Jeu d'acteur », « Danse », « Anamorphique », « Dialogue », « Pub locale », « Teaser »… avec une case à cocher et un exemple avant/après (rendu H3). Le Producteur les active selon la demande, l'utilisateur peut les forcer. Chaque carte est un fichier `competences/*.md` versionné, avec la méthode des vidéos (liste d'actions, intentions par beat, géométrie de la scène). Explorer passe de 8 à 50 « formats » (vignette + objectif prérempli). L'IA écrit alors des prompts chronométrés (« 0–2 s … ») que le validateur H3 vérifie.

**4. « Montre-moi » : corriger avec un média** — M / 4. Sous un plan raté, un bouton « Corriger avec… » propose quatre choix : **un clip filmé au téléphone** (le mouvement), **un croquis** (qui se tient où, dessiné avec deux couleurs), **un plan de pièce**, **une image d'objet**. L'IA analyse le média (Qwen-Omni pour le clip, Qwen-Edit pour le croquis, qui devient l'image clé), écrit le prompt corrigé, **propose le devis** et relance. Dit clairement : pour le clip, nous **décrivons** le mouvement, nous ne le copions pas (limite H3).

**5. Refaire un montage d'après une référence (équivalent de Katana)** — L / 5. Un bouton « Refaire comme ça » : l'utilisateur dépose une vidéo (ou un lien), jusqu'à cinq photos (ses personnages, son produit) et une musique. L'IA découpe la référence (plans, rythme, temps forts), choisit les plans à générer en H3 avec les éléments de l'utilisateur, pose titres et sous-titres (HyperFrames) et cale les coupes sur la musique. Durée, format et cadence viennent de la référence, sans réglage. Elle montre un **rapport après chaque étape** (« 12 plans repérés, accroche au plan 3 »), valide au devis, puis rend.

**6. Connecteur Claude (MCP distant) et pack de skills** — M / 4 (R20 + R22). Une page « Brancher à Claude » avec une adresse MCP et une commande à copier ; l'utilisateur connecte son compte Nexora (connexion unique existante), ajoute le skill `nexora-creative` et écrit dans son chat « fais-moi une pub de 20 s ». Les outils existants (Producteur, valider, prolonger, raccorder) sont exposés ; **le devis et la validation restent dans Nexora** (le LLM n'a aucun outil qui dépense). Sans lien avec l'interface, c'est la porte d'acquisition qui fait 344 000 vues chez Higgsfield.

**7. Projet éditable avec commentaires épinglés** — L / 5 (R12). Le film devient un projet à **calques** : plans, titres, sous-titres, musique. L'utilisateur change le texte, la palette, la police ou la durée d'un titre, et la mise en page se recalcule ; il **clique un instant de la lecture et écrit** « raccourcis ce plan, plus chaud » ; l'IA ne régénère que le plan touché et le remet en place. Export : ProRes et XML (existants) ; **pas d'export After Effects ou Blender** (non prévu).

**8. Shorts et teasers par lots, avec traduction** — M / 4 (R14 + R13). L'utilisateur dépose un film, un podcast ou un lien : l'IA propose **10 clips** (moments forts, accroche, sous-titres au mot), un teaser de 30 s avec trois angles possibles, au format vertical ; il coche, ajuste, lance. Option « versions en d'autres langues » (sous-titres traduits d'abord, doublage plus tard). Coût du lot affiché à l'avance.

**9. Studio de publicité et multiplicateur de variantes** — M–L / 4 (R10). Une photo de produit ou un lien : l'IA compose l'image produit, écrit 3 accroches, tourne la pub (plans H3, musique Music3, cartons en code). Ensuite « **Multiplier** » : même montage et rythme avec un autre produit, un autre acteur (`@`), un autre lieu ; l'IA refait les images clés (Qwen-Edit) et relance seulement les plans changés.

**10. Outils de couverture sur un plan existant** — M / 4. Sur n'importe quelle prise terminée : « Autre angle » (image extraite → Angle/Couverture → nouvelle prise avec les mêmes éléments), « Changer l'éclairage » (relight de l'image clé → nouvelle prise), « Prolonger vers l'arrière » (plan précédent construit pour finir sur la première image). L'utilisateur choisit l'angle sur une grille de vignettes ; l'IA garde les éléments `@` et affiche le devis.

**11. Voix et synchronisation labiale (R3b + R13)** — L / 4. Pour un plan avec parole : choisir une voix (bibliothèque ou **voix de l'utilisateur, avec consentement signé dans l'interface**), écrire ou déposer la réplique ; l'IA fabrique l'audio, tourne le plan en H3 avec la réplique, puis synchronise les lèvres si l'audio est externe. Les voix de H3 restent imprévisibles, donc l'option est proposée à côté, pas imposée.

**12. Recettes partageables et défi mensuel (R21)** — M / 3. Chaque film réussi porte un bouton « Partager la recette » : une page (privée par défaut) avec la vidéo, les prompts, les éléments, le plan et le coût, et un bouton **« Refaire avec mes éléments »** (remix). Plus tard : fil d'organisation, puis défi mensuel. L'IA anonymise les noms et retire les éléments personnels avant publication.

## 7. Ordre de réalisation proposé et avertissements

- **Vague 1 (≈ 3–4 semaines)** : n° 1 (Ref2VA, bloqué aujourd'hui seulement par le câblage), n° 2, n° 3 ; elles se renforcent entre elles (compétences + éléments + prises).
- **Vague 2** : n° 4, n° 6, n° 10 ; **vague 3** : n° 5, n° 7, n° 8, n° 9 ; **vague 4** : n° 11, n° 12.
- **À ne pas promettre** : transfert de mouvement réel, relight vidéo, édition d'une vidéo existante (limites de H3, DiffSynth non mesuré), export After Effects ou Blender, voix constante de H3.
- **Mesures à faire avant d'afficher quoi que ce soit** : nombre maximal de références de Ref2VA sur H3 (Pika annonce 12 pour « H3 Flex », non vérifié chez nous), temps d'un brouillon 768p turbo sur la RTX 5090, tenue du visage entre deux prises, qualité de la description de mouvement par Qwen-Omni.
- **Point de prudence produit** : Higgsfield montre que la **conversation** (Claude) devient l'interface ; notre Producteur doit rester utilisable **sans** chat (boutons et cartes) pour le mode simple, avec le chat en option.
