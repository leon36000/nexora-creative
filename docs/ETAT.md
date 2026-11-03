# Nexora Creative — où nous en sommes (mis à jour le 03/11/2026)

Document pour le fondateur : ce qui est fait, ce qui est prouvé, ce qui ne l'est pas. Détail jour par jour : `docs/JOURNAL.md`. Mesures : `recherche/08-mesures-gb10.md`.

## En une phrase

**Nexora Creative tourne dans le navigateur sur le DGX Spark (pc6)** : une phrase en français devient une vidéo avec son (MiniMax H3), ou un **film de plusieurs plans** écrit et tourné par l'AI Director, retouchable plan par plan, remontable sans nouveau rendu et exportable pour Premiere ou DaVinci. Il est prêt à être branché au portail Nexora ; **le site, lui, n'a pas encore les routes nécessaires** (contrat écrit dans `docs/INTEGRATION-NEXORA.md`).

## Mise à jour du 03/11 : l'agent à trois paliers, facturé au jeton

Branche `feat/agent-3-niveaux` (recherche/19). Éco (DeepSeek V4.1 Flash, DeepInfra), Équilibré (Muse Spark 1.3) et Expert (Gemini 4 Argon **Flex**, 1 $ / 5 $ par M) pour le tournage, le montage et le Producteur ; en ligne sur la VM 202.

| Brique | État | Preuve |
|---|---|---|
| **Mesure et facturation de chaque jeton** (grand livre, devis, réservation, règlement, libération, plafond dur ; prix = coût × 1,10 × 1,4025) | **fait, testé** | 19 tests ; ligne « jetons, crédits » dans le Producteur ; **rien débité en réel** (VM sans portail de crédits) |
| **Palier par rôle et par projet** (Éco / Équilibré / Expert), escalade automatique | **fait** | un vrai tour du Producteur par palier sur la VM (0,0006 / 0,0006 / 0,010 USD) |
| **Harnais compact** (liste en secondes compilée par le code, validateur parlant, réparations du code, mémoire k = 1 enseignée par Claude et par les paliers chers) | **fait** | Éco : 0 plan valide sans harnais → **0,92** avec (0,0007 $ le film) |
| **Campagne** 3 paliers × 8 briefs × mémoire × 3 tours (≈ 1,3 USD) | **faite** | Éco 0,63 / Équilibré 0,90 / Expert 0,94 (tous essais) ; la mémoire apporte +0,35 à Éco |
| **9 films rendus** (Réception, Surveillance, OPSYS-AI × 3 paliers) | **faits** | `~/nexora-creative-data/promo/montage/Test-agents-*` ; plans de la bibliothèque, aucune génération |

Limites : notes du code seulement (pas de juge visuel), bibliothèque de plaques petite, Éco dépend du harnais. Défauts : tournage et montage en Éco avec escalade, Producteur en Expert.

## Mise à jour du 02/11 (nuit) : vague 2 (Producteur, montage, personnages @, prises, projet long)

Branche `feat/vague2` (recherche/12, 13, 14). Détail : `docs/JOURNAL.md`. Captures : `marketing/creative/captures-v3/v2-*.jpg`.

| Brique | État | Preuve |
|---|---|---|
| Défauts du Producteur (Markdown brut, devis sans chiffre, juge grisé) | **fait** | v2-01 ; `qwen/qwen3.8-27b` par défaut pour le rôle `juge` |
| **Monter** dans le Producteur (aperçu, mesures, Améliorer) | **fait** | film réel 354 : 8 plans, −13,2 LUFS, score 0,95 ; v2-02, v2-03 |
| **Personnages @** (fiche Qwen-Image, Ref2VA) | **fait** | film réel de 2 plans, même visage et même tenue ; v2-04, v2-05, v2-07 |
| **Brouillons, prises, compteur de projet** | **fait** | brouillon 28,7 s contre 129 s la finale ; v2-06 |
| **Montre-moi** (image de départ ou de composition) | **fait (images seulement)** | deux brouillons réels ; pas de vidéo → vidéo |
| **Projet long** (scénario → plans, bible, estimation, lots, Mode Studio) | **squelette réel** | test d'échelle 1 080 plans ; réel : 4 plans, 2 tournés ; v2-08 |

**Écart restant avec Higgsfield** : voix et lip-sync sur audio fourni, édition d'une vidéo existante (échange, restyle, transfert de mouvement : H3 ne le fait pas), identité tenue sur un plan « suite » (I2VA) et sur FastH3 (pas de références), brouillon identique à la finale (la graine et le prompt sont repris, le modèle et la résolution changent : le résultat n'est pas le même plan), pas de communauté ni d'API publique.

## Mise à jour du 02/11 (soir) : harnais de montage pour LLM bon marché (tranche 1)

Branche `feat/harness-montage` (recherche/13 et 14). Un modèle bon marché (`z-ai/glm-5.3`) peut piloter le montage grâce à un contrat typé, des outils gratuits et une mémoire à la AMD. Détail : `docs/JOURNAL.md`, `recherche/14` §12.

| Brique | État | Preuve |
|---|---|---|
| **EditPlan v1** (Zod + validateur : images entières, pas de coupe dans un mot, fondus audio 30 ms, ducking, transitions, vitesse, zoom, texte, plans à tourner) | **fait** | `server/nexora/montage/editplan.ts`, 7 tests de validateur |
| **`montage_auto`** (base déterministe et repli) | **fait** | valide sur 12 briefs, durée ±5 %, aucun doublon, coupes sur les temps forts ; déterministe |
| **`analyze_media`** (ffmpeg scdet, silencedetect, ebur128 + énergie/temps forts en TS, cache) | **fait** | tempo 120,2 BPM retrouvé sur une piste de 120 BPM ; vrai fichier analysé en test |
| **Métriques en code, `critique`, `revise`** | **fait** | rythme vs énergie, coupes sur temps forts, doublons, texte, audio, crédits ; juge visuel optionnel (30 %) |
| **Mémoire AMD** (4 recettes, 4 exemplaires réels, indices de fonction, k = 1) | **fait** | exemplaires tirés du film V3 et de la pub surveillance (listes réelles) ; le 4e (explicatif) est écrit à la main |
| **Rendu ffmpeg d'un EditPlan** | **fait** | xfade, rampes, zoom, libass, musique, voix, ducking, loudnorm ; film de 15 s rendu par MCP, −14,5 LUFS |
| **Outils du Producteur** (`analyze_media`, `plan_edit`, `critique`, `revise`) | **fait côté serveur** | 2 tours au plus, plan invalide jamais gardé, score qui ne baisse pas, repli sur `montage_auto`, plafond de crédits ; **pas d'interface** : aucun bouton de rendu dans l'UI |
| **MCP** (`montage_*`, 7 outils) | **fait** | `npm run mcp:smoke:montage` (analyse → auto → mesure → rustine → rendu → relecture) |
| **Banc** (12 briefs, 3 bras, IC par brief) | **fait** | `npm run bench:montage` ; 1,6 USD dépensés au total |

**Ce que le banc dit (honnêtement)** : sur les métriques en code, `montage_auto` fait 0,937 ; GLM tel quel 0,884 (42 % de plans invalides remplacés par le code) ; GLM + exemplaire + validateur + 1 critique 0,876. La mémoire fait passer la validité de 58 % à 92 % mais **ne bat pas le code seul** et coûte ≈ ×6 par essai. Ces métriques sont des proxys proches de ce que le code optimise ; aucun juge visuel ni œil humain n'a encore tranché.
**Pas fait** : bouton de montage dans l'interface et route de rendu HTTP, juge visuel sur planche contact dans le banc, `mix_audio` en deux passes (crête −0,9 dB mesurée), son propre des plans vidéo, mots horodatés (Whisper) dans l'inventaire, recettes `grade`/`reframe`, distillation par Claude des briefs d'apprentissage, règles apprises (ACE). **VM 202 non redéployée** (voir le journal).

## Mise à jour du 02/11 : Producteur IA, juge visuel, Prolonger et Raccord, mode simple refait

Branche `feat/producteur` (feuille de route `recherche/07` : R9, R8, R3a, R2 en partie). Détail et mesures : `docs/JOURNAL.md`.

| Fonction | État | Preuve |
|---|---|---|
| **Producteur IA** (onglet par défaut de Créer) : un objectif → plan (plans, réplique, musique, cartons de texte) → devis calculé par le code → validation d'un clic → tournage par les routes ordinaires → suivi plan par plan → variantes en un clic | **fait** | film réel « Chez Mado » (pub verticale, 2 plans × 2 prises, musique, 2 cartons) lancé depuis le navigateur ; plan proposé en ≈ 6 s par `z-ai/glm-5.3` ; ≈ 7 000 jetons par message [TEST navigateur + réel] |
| Garde-fous de l'agent | **fait** | le LLM n'a aucun outil qui dépense ; plafond par production ; 6 étapes au plus par message ; budget de jetons ; validation exécutée une seule fois (15 tests) |
| **Juge visuel** (option « 2 prises par plan », rôle LLM `juge`, `qwen/qwen3.8-27b`) | **fait** | plan 2 du film réel : prise B gardée, « évite le texte orange indésirable sur la vitrine » (le texte parasite de la prise A est visible) ; contrôle qualité d'abord, repli sans juge (10 tests) |
| **Cartons de texte posés en code** (titre, appel à l'action) | **fait** | début et fin du film réel, libass (le `drawtext` manque au ffmpeg du poste) |
| **Musique composée pendant le tournage** | **fait** | Music3 sur le GB10 en 35,5 s, mixée à l'assemblage |
| **Prolonger** (I2VA depuis la dernière image) et **Raccord** (FL2VA entre deux clips), sur MiniMax H3 | **fait** | remplacent Extend et Transitions (LTX) ; voir le journal pour les rendus réels |
| **Compétences versionnées** des rôles LLM (`server/nexora/competences/*.md`) | **fait** | producteur, réalisation, montage, publication, juge ; injectées dans les consignes existantes (4 tests) |
| **Mode simple** : Explorer = 8 modèles prêts à produire (un clic → plan et devis), 16 mouvements de caméra à vignettes dans Vidéo, « Faire parler » (photo + réplique) | **fait** | captures `marketing/creative/captures-v3/` |
| Apps qui reposaient sur LTX (Mirror, Reshoot, Effects, Stage, HDR, Swap/Restyle, Speak, Add sound, Dream, Director LTX, Vidéo LTX) | **retirées de l'interface** | leurs adresses mènent à l'outil qui les remplace ; 15 outils MCP correspondants ne sont plus exposés |
| MCP : outils `nexora_*` (état, Producteur, valider, créer, prolonger, raccorder) | **fait** | 22 outils listés par un client MCP réel, `nexora_etat` appelé |
| **Personnages persistants (R6, Ref2VA)** | **pas fait** | les points de contrôle `minimax_h3_ref2va_*` sont présents sur la RTX 5090 ; câblage à faire (voir journal) |
| **Brouillon rapide H3 (R1)** | **pas fait** | « image d'abord » existe (plan clé Qwen → Animer) ; pas de brouillon 768p turbo |

**Écart restant avec Higgsfield** : personnages `@` en vidéo (Soul ID), lip-sync sur un audio fourni et voix (TTS, doublage), édition d'une vidéo existante (échange, restyle, transfert de mouvement), un seul moteur vidéo, presets de caméra illustrés par des clips d'OpenField et non par des rendus H3, pas d'API publique ni de communauté. **Avance** : agent qui chiffre avant de dépenser et contrôle chaque plan, juge visuel, montage multipiste, moteurs hébergés.

## La base

Fork d'**OpenField** (MIT), comme WorkStudio est un fork de Sim : interface React 19 dans le navigateur, serveur Fastify qui compile lui-même les graphes ComfyUI (ComfyUI n'est jamais exposé). Rebaptisé Nexora Creative, en français. Provenance : `app/UPSTREAM.md`.

## Mise à jour du 31/10 (demande du fondateur : H3 seul, deux GPU, qualité maximale, vidéo promo, page marketing)

- **MiniMax H3 seul** : Wan 2.2 est retiré (code, registre, poids supprimés). Hors territoire H3, refus clair, aucun repli. Wan 2.2 : plus aucune trace dans le code.
- **Deux GPU** : le serveur pilote un parc (GB10 + RTX 5090 de pc1 par tunnel SSH en boucle locale), route chaque tâche vers un moteur qui porte sa recette (depuis le 31/10 soir : H3 « rapide » et « cinéma » sur la RTX 5090, image Qwen et musique Music3 sur le GB10). Prouvé : les deux moteurs rendent des plans de la même bande-annonce ; l'application voit les deux en ligne.
- **Banc qualité** : `recherche/10-qualite-h3.md` (5090 : 5 s en 1344×768 avec son en 290 s ; GB10 : 344 s).
- **Musique MiniMax-Music3** : bande originale pour les films (panneau des plans) et les clips (bouton « Ajouter une musique »), description écrite par le LLM, mixage −14 LUFS. 60 s de musique en 27 s sur la 5090. Gain réel pour la musique ; les bruitages et voix restent ceux de H3 (`recherche/11-image-et-musique.md`).
- **Image** : Qwen-Image-2.1 installé sur le GB10 **en mode démonstration seulement** (licence de recherche) ; le défaut propre Qwen-Image-2512 (Apache-2.0) n'est **pas installé** (disque). Ideogram 4 exige une licence commerciale.
- **Vidéo promotionnelle et page marketing** : voir `marketing/creative/` et le journal du 31/10.
- **Non prouvé** : l'écoute par un humain (aucun A/B sonore fait), l'étape « l'IA dessine le plan clé avant H3 », le test réel du bouton « Ajouter une musique » dans le navigateur.

## Mise à jour du 31/10 soir et nuit (Studio, Qwen, LLM, administration du site, bande-annonce V2)

- **Interface Studio** refaite (état des deux GPU, modes Vidéo / Image / Film, « Booster ma phrase », publication par réseau, « Inspire-moi »).
- **LLM par rôle**, modération avant rendu (règles + LLM), réglable depuis l'administration du site : **branche `feat/creative-admin-modeles` du dépôt du site, non fusionnée, non déployée** ; la migration 0030 n'est pas appliquée à la vraie base.
- **Bande-annonce V2** (60 s : flotte au-dessus de la Terre, hyperespace, duels de sabres laser) en trois versions : publique 16:9, publique 9:16, démo investisseurs. **Non publiée** : réserve de licence H3 V.4 (voir `docs/LICENCES-PUBLICATION.md`). **Jamais écoutée par un humain** : volume, silences et synchro mesurés seulement.
- **Page marketing** complète dans `marketing/creative/` ; pas encore dans le site Nexora (registre d'affirmations à remplir).
- **H3 n'est pas sur le GB10** : malentendu de ma part (déplacé vers pc1 au lieu de dupliqué). Le retour demande 35 Go ; disque de pc6 à 93 % (66 Go libres, réserve de 50 Go) → autorisation de libérer de l'espace attendue.
- **Pas encore au niveau de Higgsfield** : manquent personnages constants d'une vidéo à l'autre (Ref2VA non branché), transfert de mouvement, avatars qui parlent, retouche locale / relight, juge visuel automatique, crédits côté site, machine RTX 5080.

## Ce qui est fait et prouvé (état du 31/10 matin)

| Fonction | Preuve |
|---|---|
| Moteur **MiniMax H3** (FastH3 V2 NVFP4) sur GB10 | rendus réels : 5 s en 82 à 92 s, 10 s en 230 s, **Qualité max 1344×768 en 340 s**, son stéréo vérifié [MESURÉ] |
| **Réécrivain LLM** des prompts H3 (guide officiel MiniMax + validateur déterministe) | votre exemple voiture → robot réussi du premier coup en 3,4 s ; défaut « champ inventé » trouvé et corrigé [TEST réel] |
| Accueil **Créer** : phrase → vidéo, formats, durées, son, Rapide / Qualité max, **partir de sa photo** | parcours complet dans le navigateur (pub café verticale) ; photo → vidéo réel (93 s) [TEST navigateur] |
| **AI Director** : idée → storyboard modifiable (plans, caméra, bible de continuité) → tournage → assemblage | film réel « Crimson Rising », 6 plans, 41 s, assemblé en 3,1 s, repris après plusieurs redémarrages du serveur [TEST réel] |
| **Plans enchaînés** depuis la dernière image du plan précédent | film « Métamorphose sous la pluie » : le plan 2 part de l'image extraite du plan 1, prompt I2VA [TEST réel] |
| **Refaire un seul plan** | version du film avec 1 plan retourné (94 s), 5 réutilisés, réassemblée en 2,8 s, nouvelle description visible [TEST navigateur] |
| **Montage sans rendu** (ordre, retrait, coupe ou fondu) et **exports pros** | version en fondus de 33,84 s en 2,4 s ; ProRes 422 HQ 10 bits en 2,4 s ; ZIP projet avec séquence FCP7 XML valide [TEST réel] |
| **Contrôle qualité** automatique (noir, figé, silence, durée) + reprise d'un plan raté | 4 tests ; tous les plans réels l'ont passé (la reprise sur défaut n'a donc jamais eu à servir en réel) |
| **Reprise après panne** du moteur | `kill -9` réels : moteur relevé seul en 13 s (superviseur) ; film terminé malgré la panne, plans relancés automatiquement [TEST réel] |
| **Devis avant création** (temps, crédits en mode portail) et **interface mobile** | affiché dans l'accueil ; page sans défilement horizontal à 375 px [TEST navigateur] |
| Texte à l'écran non demandé refusé avant rendu | défaut vu dans un film réel (enseigne inventée), corrigé (2 tests) |
| **Licences** en échec fermé (LTX, FLUX.2 dev, UltraSharp bloqués ; H3 selon le territoire) et **registre de capacités** | 8 + 7 tests ; le moteur est choisi par le code, jamais par le LLM |
| **Multi-organisation** (prises, personnages, projets, direct isolés) | 3 tests d'isolation |
| **Connexion unique** au portail (OIDC + PKCE, patron WorkStudio) | test de bout en bout avec un faux site Nexora (3 tests) |
| **Crédits** des rendus (devis, réservation, validation ou libération) et **espace disque** par organisation | 4 + 2 tests contre une API de site simulée |

**152 tests automatisés verts au 02/11** (99 au 31/10), contrôle de types vert, code sur GitLab (`root/nexora-creative`, branche `developpement`, demande de fusion !1).

## Ce qui n'est pas fait ou pas prouvé

- **Côté site Nexora (nexora-web)** : client OIDC « Nexora Creative », portée `creative:model`, routes `/api/oauth/creative-access`, `/api/creative/credits/*`, `/api/creative/storage`, carte du panneau. Rien n'est construit : je n'ai pas touché au dépôt du site.
- **Prix** : les crédits par seconde de GPU sont une proposition (0,5 crédit/s, soit ≈ 43 crédits pour 5 s rapides) ; à valider.
- **Juge visuel par IA et 2 candidats par plan** : conçus (rapports 05 et 09), **bloqués** faute d'un modèle vision appelable (les modèles vision du catalogue sont « en aperçu » tant que la clé DeepInfra n'est pas déposée). Sans juge, tourner 2 candidats doublerait le coût pour un choix au hasard. En attendant : contrôle qualité automatique, reprise, et « Refaire ce plan ».
- **Production** : une seule instance (SQLite en WAL) ; deux moteurs (GB10 + RTX 5090). **Bloqué** : moteurs sur la RTX 5090 et la 5080, il faut me dire quelles machines et m'autoriser à y installer ComfyUI. Fichiers sur le disque du serveur (pas encore de stockage objet).
- **FreeCut** (montage avancé multipiste) : écarté pour l'instant après inspection, car il exige Chrome ou Edge et garde les projets sur le disque de l'utilisateur. Le montage cloud de Nexora (plans) et l'export Premiere/DaVinci couvrent le besoin de départ.
- **Import du ZIP dans Premiere ou Resolve** : non essayé (logiciels absents de la machine).
- Juridique : la stratégie de territoire H3 et les obligations de sa licence restent à valider par un juriste (architecture §7).

## Pour l'essayer

Sur pc6 : `~/nexora-creative-data/engine/lancer-comfyui.sh` (moteur), puis `app/scripts/dev-nexora.sh` (studio), puis ouvrir <http://localhost:37160>. Poids et rendus : `~/nexora-creative-data/` (≈ 55 Go, hors dépôt).
