# Nexora Creative — où nous en sommes (mis à jour le 03/11/2026)

Document pour le fondateur : ce qui est fait, ce qui est prouvé, ce qui ne l'est pas. Détail jour par jour : `docs/JOURNAL.md`. Mesures : `recherche/08-mesures-gb10.md`.

## En une phrase

**Nexora Creative tourne dans le navigateur sur le DGX Spark (pc6)** : une phrase en français devient une vidéo avec son (MiniMax H3), ou un **film de plusieurs plans** écrit et tourné par l'AI Director, retouchable plan par plan, remontable sans nouveau rendu et exportable pour Premiere ou DaVinci. Il est prêt à être branché au portail Nexora ; **le site, lui, n'a pas encore les routes nécessaires** (contrat écrit dans `docs/INTEGRATION-NEXORA.md`).

## Mise à jour du 03/11 (nuit) : vague 2, le mode Marketing (kit de marque, imprimés en PDF fond perdu)

Page **Marketing** dans l'application (`/marketing`) : on saisit sa marque une fois (nom, logo SVG/PNG avec contrôles, couleurs avec contraste AA, polices libres, ton, coordonnées), puis **une phrase → 3 propositions → on choisit → on retouche → PDF imprimeur / PDF fond perdu / PNG / SVG**. Le kit est aussi donné au Producteur (ton, couleurs, polices, coordonnées) pour que vidéos et textes restent dans la marque.

| Brique | État | Preuve |
|---|---|---|
| Kit de marque (modèle zod, API `GET/PUT /api/nexora/marque`, téléversement du logo, couleurs dominantes SVG et PNG) | **fait, testé** | `server/nexora/marketing/kit.ts`, 26 tests |
| `SpecConception` v1 (7 formats, faces, calques texte/image/forme/logo/QR, variables, champs vides qui disparaissent) | **fait, testé** | `spec.ts` ; fond perdu 0,125 po, zone de sécurité |
| Rendu : Playwright → PDF avec **traits de coupe**, TrimBox/BleedBox, polices TrueType intégrées, PNG ≈ 300 dpi, mesure réelle du texte | **fait, prouvé** | 9 gabarits rendus en **285 à 390 ms** chacun (carte, dépliant, accroche-porte) |
| Contrôle préliminaire (dpi, zone de sécurité, zone de la poignée, fond perdu, contraste AA, texte trop petit) | **fait, testé** | `controler()` ; 0 erreur sur les 9 échantillons |
| 9 gabarits (3 cartes, 3 dépliants/affiches, 3 accroche-portes), pilotés par le kit | **faits**, vus à l'écran | `marketing/creative/echantillons-vague2/` |
| Assistant (rôle `design`, Éco d'abord, escalade) : 3 propositions, filtre d'allégations, 4 pistes de logo SVG | **prouvé en réel** (DeepInfra, Éco) | propositions : 0,019 à 0,026 crédit mesuré (devis 1) ; logos : 0,057 crédit (devis 1) |
| Devis en crédits avant dépense | **fait** | le rendu est gratuit (CPU du serveur) ; seuls les appels au modèle sont facturés |
| CMJN par Ghostscript | **fait si `gs` est installé** | échantillon `cmjn/` ; pas de PDF/X certifié, profil par défaut |

**Pas fait dans cette tranche** : fond généré par Qwen-Image depuis la page (utiliser l'outil Image puis importer), vectorisation vtracer des idées de logo, PDF/X-1a certifié et profil ICC choisi par l'imprimeur, imposition n-up, éditeur Fabric.js par glisser-déposer (le panneau expert édite texte, taille, police, interligne), déclinaisons sociales 1:1 / 4:5 / 9:16 (#21), affiche et brochure DL sans gabarit propre (l'affiche réutilise les gabarits dépliant). Détail : `docs/JOURNAL.md`.

## Mise à jour du 03/11 (soir tard) : feuille de route maître et vague 1 (bulle d'effet)

Audit complet (35 variables, notes contre Higgsfield, Runway, Krea, CapCut, Premiere/DaVinci, Descript, Canva, Meshy : **nous 2,4/5**, Higgsfield ≈ 2,7, CapCut ≈ 3,3), plan en 7 vagues, spécifications de la bulle d'effet et du mode Marketing : `docs/FEUILLE-DE-ROUTE-MAITRE.md`. **57 issues** GitLab (#1 à #57) + suivi **#58**. Vague 1 commencée : **bulle « Effet IA ici… » v0** au clic droit du Mode Studio (26 recettes instantanées à 0 jeton, rôle LLM `effets`, un seul Ctrl+Z, Plus fort / Plus doux, Avant/Après) ; 19 tests verts, vérifiée dans le navigateur (`marketing/creative/captures-v3/vague1-*.jpg`). Limites : rendu visuel non vu (pas de WebGPU dans le navigateur intégré, #8), voie LLM prouvée une fois en réel sur la VM 202 (« ambiance de film d'horreur, froid et inquiétant » → 5 effets du catalogue, tous dans leurs bornes), banc de 30 phrases à faire (#1), jetons du Studio non facturés (#4).

## Mise à jour du 03/11 (nuit) : les deux GPU de pc5 au travail (VM 204 `nexora-gpu`)

Les RTX 2080 SUPER et 2070 SUPER de pc5 sont en passthrough dans une VM minimale (4 vCPU, 8 Go, 60 Go) ; ComfyUI 0.43.2 figé, un travailleur par carte (ports 8188 et 8189, LAN seulement) et des services STT/TTS/Demucs/embeddings (8190). **TRELLIS.2 int8 tourne sur Turing** : aperçu 126 s (GB10 : 38 s), qualité 531 s (GB10 : 162 s), pic VRAM 7,2 et 7,8 Go sur 8,2. Whisper, Kokoro et Chatterbox fr répondent en 0,1 à 2 s pour une phrase. `gpu-unlock` échoue sur Turing (à ne pas activer). **Brancher Creative** : ajouter les deux moteurs à `NEXORA_MOTEURS_GPU` (ligne prête dans `deploy/proxmox/creative.env.example`), puis relancer `nexora-creative` ; **non fait** sur la VM 202 (le routage enverrait aussi du « qualité » sur la 2070 SUPER, 3,3 fois plus lente que la GB10). Détail, mesures et retour arrière : `docs/gpu-pc5.md`.

## Mise à jour du 03/11 (soir) : le mode « 3D » à la façon de Meshy, première tranche

Branche `feat/mode-3d` (recherche/18). **Image → 3D** et **Texte → 3D** tournent de bout en bout sur la GB10 (TRELLIS.2, nœuds ComfyUI 0.43.2, pur PyTorch, aucun noyau à compiler).

| Brique | État | Preuve |
|---|---|---|
| Poids lot A1 en **int8** (5,25 Go au lieu de 10,34 Go ; 8,95 Go au total) | **téléchargés, fonctionnent sur sm_121** | `docs/RESSOURCES.md` ; ≥ 21 Go libres après |
| Mesure TRELLIS.2 sur GB10 (chaise en chêne, image Qwen-Image-2.1) | **faite** | aperçu **38 s** à chaud (46 s à froid), 150 000 faces, GLB 9,9 Mo ; qualité **162 s**, 400 000 faces, GLB 45 Mo ; image de référence 24 s |
| Recettes `objet-apercu` et `objet-qualite`, devis en crédits (secondes mesurées), `NEXORA_MOTEUR_RECETTES` | **faits, testés** (18 tests) | `server/nexora/objet3d.ts` ; ComfyUI **figé à 0.43.2** (les noms de nœuds du graphe `trellis.ts` sont ceux de cette version : relancer le banc `scripts/bench-3d.ts` à chaque mise à jour du moteur) |
| Page Object : visionneuse 3D, textures / argile / fil de fer, téléchargement GLB | **vérifiée** dans Chromium (WebGL logiciel) | `marketing/creative/captures-v3/3d-*.jpg` |
| **Texte → 3D** : image de référence propre, TRELLIS.2, juge sur 4 côtés, une relance au plus | **de bout en bout prouvé** (« chaise en bois clair », « robot jouet ») ; **juge non prouvé en réel** | le passerelle LLM de développement n'a aucun modèle vision : sans juge, l'objet est gardé sans note (repli prévu et testé) |

**Qualité honnête** : aperçu 7,5/10, qualité 7/10 sur la chaise (forme cohérente des quatre côtés, pieds et dossier propres ; en qualité la texture bruitée laisse des taches et des bavures sous l'assise). Planches : `marketing/creative/captures-v3/3d-planche-chaise-*.jpg` (outil `scripts/planche-3d.mjs`). Plafond connu : pas de topologie quad, pas de rigging (rapport 18).

Limites : pas de multi-images, retexture, formats autres que GLB, ni polycount réglable dans l'interface ; le juge visuel attend un modèle vision branché sur le LLM ; la VM 202 ne porte pas la GB10 : le mode ne s'y active qu'avec le moteur GB10 déclaré (voir `deploy/proxmox/creative.env.example`).

## Mise à jour du 03/11 (soir) : mémoire AMD du professeur + harnais décomposé (recherche/20)

Branche `feat/memoire-amd-reasoningbank`. Banc scellé (4 briefs d'apprentissage écrits par Opus 5.5, 8 briefs de test × 3, juge Gemini en ordre inversé, 2,09 USD).
**Éco, nouveau défaut H** (mémoire du professeur à trois niveaux + structure puis textes) : **0,914** [0,906 ; 0,923] au lieu de 0,832, 0 % de repli, 96 % de listes valides du premier coup,
0,0006 $ (0,095 crédit) le film, juge 11-0-5 contre l'ancien défaut. Équilibré H : 0,912, 100 % du premier coup. Expert inchangé. ReasoningBank (stratégies de l'élève) et
meilleur-de-4 : **sans gain** à ce coût, livrés éteints. `NEXORA_HARNAIS_FILM=v3` rétablit l'ancien comportement.

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
