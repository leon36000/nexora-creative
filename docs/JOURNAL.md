# Journal — Nexora Creative

Une entrée par itération : date, lot, ce qui a été fait, preuves, échecs, prochaine action.

## 30/10/2026 — démarrage de la boucle autonome
- Conception et recherche (01 à 06) poussées sur `root/nexora-creative` (commit 0dad3d8).
- État machine : 145 Go libres sur `/` (en baisse : autres sessions), GB10, 121 Go de mémoire unifiée, Docker + NVIDIA Container Toolkit 1.20.1, aucun jeton Hugging Face local (les dépôts FastVideo et Wan visés ne sont pas « gated »).
- Tailles relevées sur Hugging Face : FastH3 V2 NVFP4 Comfy = DiT 13,6 Go + encodeur Qwen3-VL NVFP4 15,7 Go + VAE 5,2 Go (≈ 35 Go sélectifs) ; FastH3 Omni NVFP4 13,8 Go ; Wan 2.2 TI2V-5B ≈ 34 Go en dépôt officiel.
- Prochaine action : lot R (littérature) en parallèle du lot 0b (fork OpenField).

## 30/10/2026 — itération 1 (lot 0b)
- Import brut d'OpenField 96cf7c1 dans `app/` (commit c355ce9), `UPSTREAM.md`. `npm install` + `npm run typecheck` verts [TEST].
- Politique de licences en échec fermé (`app/server/nexora/licences.ts`) : LTX-2.x et tous ses dérivés, FLUX.2 dev, 4x-UltraSharp bloqués ; H3 permis seulement si le territoire du compte n'est pas US/UE/R.-U./Corée ; ensemble inconnu bloqué. Branchée sur `blockingReason`, `effectBlockingReason` et les rendus en moteur distant. Contexte de compte par requête (`compte.ts`, AsyncLocalStorage). 8 tests vitest verts [TEST].
- Téléchargement FastH3 V2 NVFP4 (≈ 35 Go) lancé en arrière-plan dans `~/nexora-creative-data/models`.
- Prochaine action : lot 1 (ComfyUI sur GB10).

## 30/10/2026 — itération 1, suite (lots R, 1, 2 ; priorité du fondateur : « l'important est l'outil »)
- Lot R fait : `recherche/07-litterature-scientifique.md` (≈ 95 articles, 9 axes, top 10 classé) par un sous-agent ; chiffres des auteurs, non reproduits.
- Lot 1 fait : ComfyUI v0.43.2 + PyTorch 2.14.1 cu130 sur GB10, écoute 127.0.0.1:37188 [TEST]. Piège `Python.h` contourné sans droits (voir rapport 08).
- Lot 2 fait : **premier rendu H3 réel** — 832×480, 5,17 s, son stéréo, **92,1 s à froid, 82,1 s à chaud** [MESURÉ]. Vidéo envoyée au fondateur. Graphe : prise en charge des points de contrôle FastH3 distillés (4 tests).
- Demande du fondateur : exploiter un LLM cloud au maximum → conception `recherche/09-llm-au-maximum.md` (12 rôles) ; réécrivain H3 (rôle 4) codé : validateur déterministe du guide officiel MiniMax + réparation + repli (10 tests). Client LLM compatible OpenAI, modèle par rôle. Essai réel en cours avec `dev/cloud-glm-5-3` via le LiteLLM de développement de NexoraSite (petite dépense cloud, pratique établie de Nexora pour vérifier avec de vrais modèles).
- Note : `main` est protégée sur GitLab ; le travail est poussé sur la branche `developpement`.

## 30/10/2026 — itération 1, suite (lot 7 en partie : l'outil dans le navigateur)
- Réécrivain réel avec le LLM cloud `dev/cloud-glm-5-3` : exemple du fondateur (voiture → robot géant, caméra en orbite) → prompt H3 conforme du 1er coup en 3,4 s → rendu H3 84,1 s [MESURÉ]. Vidéo envoyée au fondateur.
- Application dans le navigateur (http://localhost:37160, pc6) : marque Nexora Creative, accueil **Créer** en français (intention, format, durée, son, idées, scénario visible, « MiniMax H3 » affiché), route `/api/nexora/creer`. **Test de bout en bout dans le navigateur** : idée « publicité café glacé », format vertical → vidéo 480×832 5,17 s avec son en 84,2 s ; texte « Le froid qui réveille. » correct à l'image [TEST navigateur + ffprobe]. Vidéo envoyée au fondateur.
- Défaut trouvé pendant ce test : le LLM a inventé un champ `on_screen_text` ; le validateur le refuse désormais (test ajouté, 26 verts).
- Pas encore fait dans le lot 7 : devis en crédits avant tournage, territoire du compte dans l'interface, plan proposé avant tournage.
- Prochaine action : AI Director multi-plans (vidéos plus longues, découpage, 2 candidats, juge), profil Qualité 1344×768.

## 30/10/2026 — itération 1, suite (Director, Wan, multi-organisation, SSO, crédits, contrôle qualité)
- **AI Director v1** : idée → storyboard LLM (plans, caméra, bible de continuité) modifiable dans l'interface → tournage H3 → contrôle qualité de chaque plan → assemblage. **Premier film réel « Crimson Rising » : 6 plans, 41,0 s, tous contrôlés OK, assemblé en 3,1 s** [TEST navigateur + ffprobe], malgré plusieurs redémarrages du serveur pendant le tournage (reprise prouvée). Film envoyé au fondateur.
- Mesure : un plan H3 de 10 s coûte 230 s contre 85 s pour 5 s sur le GB10 [MESURÉ] (rapport 08).
- **Wan 2.2 TI2V-5B** (Apache-2.0) téléchargé (18 Go) et branché ; choix du moteur par le code selon licence et territoire ; premier rendu Wan en file.
- **Multi-organisation** (isolation prouvée par 3 tests), **connexion unique OIDC + PKCE** (prouvée de bout en bout avec un faux site Nexora, 3 tests), **crédits GPU** (devis, réservation, validation/libération ; 4 tests), contrat du site dans `docs/INTEGRATION-NEXORA.md`. Côté site : **rien n'est construit** (dépôt nexora-web non modifié).
- **Contrôle qualité déterministe** (noir, figé, silencieux, durée ; 4 tests) + reprise automatique d'un plan raté. **Plans enchaînés** depuis la dernière image du précédent (I2VA). **Refaire un seul plan** d'un film (nouvelle version, autres plans gardés ; 3 tests).
- Non testé en réel : la reprise automatique d'un plan raté (aucun plan n'a échoué au contrôle), les plans enchaînés (le film testé a été planifié avant cette fonction), la facturation contre un vrai site.
- 59 tests verts, typecheck vert.

## 30/10/2026 — itération 1, suite (Wan mesuré, refaire un plan prouvé, photo de départ, registre)
- **Wan 2.2 réel** : 5 s en 118,6 s à froid, transformation présente, sans son [MESURÉ + contrôle visuel].
- **Refaire un seul plan prouvé dans le navigateur** : description du plan 2 modifiée → nouvelle version du film (n° 10) avec 1 plan retourné (94 s) et 5 plans réutilisés, réassemblée en 2,8 s ; la nouvelle description est visible à l'image [TEST navigateur + contrôle visuel].
- **Partir de sa photo** (I2V, H3 et Wan) : 2 tests ; pas encore essayé avec une vraie photo.
- **Registre de capacités v1** (`server/nexora/registre.ts`, Zod) : manifestes H3 et Wan, planificateur à filtres durs (tâche, durée, licence/territoire, modèles installés) puis classement ; 7 tests. Le moteur de « Créer » vient du registre ; route `/api/nexora/moteurs` (raisons d'exclusion lisibles).
- 68 tests verts.

## 30/10/2026 — itération 1, suite (tests de panne réels, montage, exports, qualité)
- **Pannes provoquées** (`kill -9` du moteur ComfyUI en plein échantillonnage) :
  1. clip isolé : la prise passe en échec avec un message clair ; en mode portail ses crédits sont libérés (règle testée) ;
  2. moteur sous superviseur (`~/nexora-creative-data/engine/superviser-comfyui.sh`) : **relevé seul en 13 s**, rendu suivant réussi (95,9 s) [TEST réel] ;
  3. film de 2 plans : 1er essai, **défaut trouvé** (la relance partait pendant que le moteur était à terre et faisait échouer le film) → corrigé (le plan attend le moteur, la réconciliation le relance) ; 2e essai : **les 2 plans relancés automatiquement, film terminé et contrôlé** [TEST réel]. Les crédits d'un plan relancé suivent la nouvelle prise (« transferee »).
- **Plans enchaînés prouvés** : film « Métamorphose sous la pluie » (20,5 s), raccords sans rupture visible ; défaut d'une enseigne inventée → le réécrivain refuse désormais le texte à l'écran non demandé (2 tests).
- **Photo de départ prouvée** (93,4 s, première image = photo).
- **Montage sans rendu** (33,84 s en 2,4 s), **ProRes 422 HQ** (2,4 s), **ZIP projet Premiere/DaVinci** (FCP7 XML valide ; import non testé faute des logiciels).
- **Profil Qualité max** (1344×768) branché ; pas encore mesuré.
- Décision : FreeCut écarté comme éditeur cloud après inspection (Chromium seulement, projets sur le disque de l'utilisateur) ; montage cloud Nexora + export pro à la place.
- Décision : SQLite (WAL) pour une instance ; PostgreSQL quand il y aura plusieurs instances (le serveur d'OpenField est synchrone sur SQLite partout : bascule coûteuse sans gain aujourd'hui).
- **Bloqué, décision du fondateur requise** : moteurs sur RTX 5090 et 5080 (machine non identifiée, installation sur une autre infrastructure non autorisée par cette mission).
- 81 tests verts.

## 31/10/2026 — lot 10 (vérification finale)
- **Qualité max** mesurée : 1344×768, 5 s avec son, 340 s sur GB10 ; estimation de coût recalée sur les mesures réelles.
- Devis affiché avant création (temps ; crédits en mode portail). Parcours débutant revérifié dans le navigateur ; mobile 375 px sans défilement horizontal ; puces de durée qui ne se coupent plus.
- `docs/ETAT.md` à jour (fait / prouvé / bloqué / pas fait). 81 tests verts, typecheck vert.

## 31/10/2026 — demande du fondateur : H3 seul, deux GPU, qualité « AAA », vidéo promo et page marketing
- **pc1 inspecté** : ComfyUI 0.43.0 d'une autre session (port 18288, boucle locale) avec trois variantes de H3 (FL2VA officiel int8, Ref2VA bf16/int8, Singularity V2 int8) et des LoRA turbo Ref2V. Utilisé sans le modifier, par tunnel SSH ; seuls les poids MiniMax Music 3 y ont été ajoutés (12 Go, SSD Infrastructure).
- **Wan retiré** ; recette « cinéma » (`h3-max`) sur la 5090 ; parc de moteurs dans `server/engine.ts`.
- **Banc** (`recherche/10`) : 5090 H3 complet 290 s, Singularity 292 s, GB10 FastH3 344 s pour 5 s en 1344×768 avec son. Singularity : excellent sur le dragon, trop « 3D » sur les humains → H3 officiel par défaut.
- **Défauts du réécrivain trouvés en réel** : note parasite « (S1 is not applicable) », « airships » au lieu de vaisseaux, deux mots français dans un prompt anglais. Les deux premiers sont désormais refusés par le code (1 test).
- **MiniMax Music 3** : 60 s de musique en 27 s sur la 5090 ; le style est suivi, pas le minutage à la seconde → choix de la candidate par analyse d'énergie (`outils/analyser_musique.py`, `tempo.py`) et montage calé sur ses impacts.
- Erreur de méthode de ma part : un `pkill -f` lancé sur pc6 (n'a rien tué, motif exact sans correspondance) ; contraire à la règle « tuer seulement ses PID ». Corrigé : arrêt par PID.
- 84 tests verts.

## 31/10/2026 (suite) — redémarrage des deux machines, vidéo promo, page, musique des clips
- **pc6 et pc1 ont redémarré** pendant la session (moteurs et tunnel perdus). Relancés : moteur pc6 par son superviseur ; sur pc1, **ma propre instance** de ComfyUI (port 18388, boucle locale, journal dans `minimax-h3/logs/comfy-nexora-creative.log`) au lieu de l'instance de l'autre session ; tunnel `engine/tunnel-pc1.sh` repointé.
- **Rushes** : 14 plans utilisables (GB10 FastH3 8 étapes ≈ 340 s ; 5090 H3 complet 24 étapes ≈ 292 s), choix plan par plan à l'œil : aucun moteur n'est meilleur partout (p04 bien meilleur sur GB10, p03 et p12 sur 5090).
- **Défaut de propriété intellectuelle trouvé** : le robot de p09 (rouge et bleu, crête) imitait Optimus Prime et celui de p11 la Hulkbuster, sans que le prompt les nomme. Écartés ; re-tournés avec un design original (graphite, lignes ambre). **À retenir pour le produit** : un contrôle de ressemblance avec des franchises connues avant livraison est à construire (clause 1 de l'AUP de H3 : ne pas porter atteinte aux droits de tiers).
- **Défauts de montage trouvés par mesure** : (1) deux plans ralentis dépassaient la fin de leur rush et raccourcissaient la timeline (logo 0,6 s trop tôt) → image figée de complément ; (2) chaque segment arrondi à l'image supérieure cumulait 0,2 s de retard → coupes comptées en images ; (3) mon animation de logo était inversée (mosaïque qui se remplit) → corrigée. Résultat mesuré : flash du logo à 54,208 s, impact audio à 54,19 s ; silence forcé 52,80-54,20 s.
- **Musique** : 7 candidates MiniMax Music 3 (27 s de calcul pour 60 s) ; retenue b89 (122 BPM, silence puis impact +33 dB à 54,2 s).
- **Page marketing** assemblée et vérifiée (bureau + 375 px). Deux affirmations non prouvables retirées (« au Canada », « payé en crédits » devenu « prévu »).
- **Musique des clips** : routes `/api/nexora/clip/:id/musique` et `/avec-musique`, bouton dans « Tes vidéos » ; prouvé dans le navigateur (clip → musique composée sur la 5090 → clip « + musique », −13,2 LUFS). Défaut trouvé : musique 0,17 s plus courte que le clip → durée arrondie à la seconde supérieure.
- **Image** : studio pointé sur Qwen-Image-2512 (Apache-2.0) ; poids non téléchargés.
- 84 tests verts.
