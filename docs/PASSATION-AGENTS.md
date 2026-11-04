# Nexora : passation complète pour un autre agent (revue du 04/11/2026)

**Version maître : Bureau de pc6. Revue exhaustive ajoutée en section 15.** Elle corrige les instantanés historiques des sections précédentes et donne les preuves disque, les demandes datées et les vraies lacunes. L’ensemble des annexes REVUE-*.md est sur le Bureau et dans `docs/passation/` du worktree `NexoraCreative-doc-passation`.

**Frontière de cette revue :** aucun secret ouvert, service modifié ou redémarré, fichier supprimé, rendu lancé. Le réseau SSH et le proxy Git sont bloqués dans le bac à sable ; les services distants et les limites de puissance n’ont donc pas été revalidés. Le dernier 502 GitLab est historique, pas une mesure actuelle. Pas de push tenté. Les références `gitlab/*` citées sont locales et potentiellement anciennes.

**Horaires :** dates du corpus en UTC ; Montréal = UTC−5 au 04/11. La source s’arrête à 11:13Z / 06:13 Montréal après intégration de l’addendum. Les anciennes mentions « après-midi » ou « 11 h » ne sont pas des heures locales fiables.

Tu reprends un projet en cours. Lis ce fichier en entier, puis la mémoire (`/home/pc6/.claude/projects/-home-pc6-Desktop-Nexora-Creative/memory/MEMORY.md` et ses fichiers), puis `docs/ETAT.md` et la fin de `docs/JOURNAL.md` du dépôt Creative. Le détail brut de la session précédente : `/home/pc6/.claude/projects/-home-pc6-Desktop-Nexora-Creative/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d.jsonl` (énorme : utiliser Python ligne par ligne et JSON ; pour la reprise courante, commencer par le catalogue et le registre datés dans les annexes).

## 1. Le fondateur et les règles
- Francophone (Québec), écrit vite, souvent depuis son téléphone (Remote Control). Il nomme l'agent principal **chef de projet** : il décide, ne dérange pas, vise le niveau « triple A mondial ». Réponses en français, courtes, honnêtes, sans jargon.
- **Qualité : il exige 8/10 minimum.** Les auto-notes des agents sont trop généreuses de 1,5 à 3 points (V6 : j'avais mis 7, il a mis 5,7). Il regarde lui-même les vidéos.
- Économie de l'abonnement Claude (95 %, puis 99 % au dernier échange du 04/11 ; Codex reprend) : déléguer au maximum aux sous-agents (section 3), Claude seulement pour planifier et contrôler.
- **Interdits permanents :** ne jamais afficher/committer une clé ou un jeton (Deepinfra.env, hf-token.txt, creative.env, /srv/nexora/secrets*) ; ne jamais `pkill -f` ni tuer un processus qui n'est pas le tien ; ne jamais taper un mot de passe (sudo ou autre) à sa place : donner la commande qu'il colle lui-même ; ne pas supprimer définitivement de données (donner la commande) ; rien acheter, aucune licence/CGU acceptée, aucun compte créé ; ne pas s'étendre sur le juridique (il le gère) ; pas de connexion à Tailscale ni à des consoles de comptes à sa place ; ne pas toucher aux projets des autres (VM 9100, AgentOS, InfraTech, JeuxVideo.ca, FutureIA, Codex Forgejo, Gitspace).
- Ressources minimales : « jamais plus que le nécessaire », tout étiqueté, fichiers temporaires supprimés, pas de copies de secours inutiles.
- **Toutes les vidéos ET infographies produites sont gardées depuis le début**, essais et rejets compris (jamais supprimés), sur pc1 : `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/` + ligne dans `INVENTAIRE.csv`.
- **Tout est poussé sur GitLab au fur et à mesure** (MR vers `developpement`, pipeline vert dont gitleaks, trailer Codex de cette reprise : `Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>` (trailer Claude dans les anciens commits)). Worktrees hors du dossier principal. MCP `gitlab-nexora` (mr_create, mr_merge wait_pipeline).
- Le produit doit marcher en **français et en anglais** (vision internationale ensuite).
- Pas de nom/logo d'entreprise codé en dur : il va changer (un seul endroit).

## 2. Les projets
- **Nexora AI** : entreprise. Site public (Next.js 16 + Bun + Directus 12.5.1 + LiteLLM + Postgres), dépôt `root/nexora-web` (local `/home/pc6/Desktop/NexoraSite`), VM 201 de pc5. Thème KTM orange (#FF6600) blanc/charbon. Gitspace caché/oublié. Les 6 pages légales ne doivent jamais être publiées. Produit payant : les **VPS** sur pc5 (le reste = jetons/stockage).
- **Nexora Creative** : studio IA (image, vidéo, musique, voix, Relief 3D, détourage, Mode Studio type Premiere simplifié, Marketing). Dépôt `root/nexora-creative`, local `/home/pc6/Desktop/Nexora Creative`, branche d'intégration `developpement`. VM 202 de pc5 (https://pc5-proxmox.tail0c55ff.ts.net:9443). Déploiement : `deploy/proxmox/mettre-a-jour-creative.sh` depuis un worktree de `gitlab/developpement`.
- **WorkStudio** (agents/flux, VM 203), **OPSYS-AI** (IA qui remplace les départements d'une entreprise ; le tableau de bord n'est PAS fini : ne jamais le montrer ; VM 9100 = pas à nous).
- **3D de Creative (notre « Meshy »)** : **Nexora Mesh**, nom adopté par le fondateur le 04/11 (U107). « Relief » reste le nom de l’ancien code ; renommage `b636db9` sur `feat/nexora-mesh-nom`, pas fusionné dans la dernière référence locale d’intégration. Interface dédiée, page et films marketing, plugin : encore à finaliser. Hunyuan3D-2.1 et autres modèles déjà partiellement mesurés ; recherche persistante hors Git, rapport29 final absent (section15). Les restrictions/licences des recherches sont des données historiques, prises en charge par le fondateur.
- **Plateforme/infra** : dépôt `root/nexora-plateforme` (conteneurs, k3s, magasin de modèles, procédure de formatage).

## 3. Modèles et délégation (économie)
- Sous-agents : `outils/sous-agents/` (passerelle LiteLLM locale 127.0.0.1:4410, `sous-agent.sh`, `lot.sh`, `cout.sh`). Alias : `deepseek` (DeepSeek V4.1 Flash 1017, effort max), `muse` (Muse Spark 1.3 Contributor, effort max), `gemini` (Gemini 4 Argon **Flex seulement**, effort moyen), `gemini-eleve` (idem, élevé). Bac à sable sans réseau.
- Codex (abonnement ChatGPT du fondateur) : `outils/codex/codex-agent.sh <sol|astra|terra> <high|xhigh|max> <prompt> <dossier>` ; binaire `/usr/lib/chatgpt/resources/codex` ; `codex --search exec ...` pour la recherche web ; modèles gpt-6.1-sol, gpt-6-astra. Le MCP GitLab de Codex peut redemander une authentification (le fondateur doit la refaire).
- Consigne de modèles Claude : Opus 5.5 élevé pour vidéo/montage, Sonnet 5.5 élevé pour le reste, Haiku permis pour le mécanique.
- Clés : `/home/pc6/Desktop/Deepinfra.env` (lignes « Nom: valeur », ne jamais afficher). Jeton Hugging Face : `/home/pc6/Desktop/hf-token.txt` (lecture seule, compte leon3600 ; recommander la rotation, il s'est affiché une fois dans le chat).

## 4. Machines et accès (alias SSH dans ~/.ssh/config)
| Machine | Accès | Rôle |
|---|---|---|
| pc6 (ici) | local | GB10 DGX Spark ARM64 128 Go ; ComfyUI 127.0.0.1:37188 (Qwen-Image 2.1, TRELLIS.2 Relief, Music3) ; passerelle sous-agents ; disque système plein (99 %) ; **disque externe 1 To `/media/pc6/Storage` (dossier `Nexora/` : rendus, travail, caches, modeles)** |
| pc1 | `ssh pc1` | RTX 5090 bridée 475 W (ventilos 100 %) ; ComfyUI MiniMax-H3 :18388, tunnel local 127.0.0.1:37288 (`tunnel-pc1.sh`) ; livrables vidéo ; disque racine 96 % (travailler sur `/run/media/pc1/Infrastructure/NexoraStudioWork`) ; héberge aussi le contrôle k3s AgentOS (abandonné) |
| pc3 | `ssh pc3-agent` (clé `/home/pc6/Desktop/pc3-agent-ssh-key.txt`) | RTX 5080 16 Go : pod k3s `detourage` (SAM 3.1 + ViTMatte, namespace `nexora`, port 8231 sur 192.168.1.126 réservé à la VM 202) + mode pro LTX-2.5 ; nœud k3s d'AgentOS à ne pas toucher ; VM qemu de la V100 |
| pc3 V100 | `ssh pc3-v100-vm` (clé `pc3-v100-vm-ssh-key.txt`) | Tesla V100 16 Go (Volta sm_70 : pas de bf16/FP8 ; torch 2.14.1 cu126 mesuré, cu128/cu130 incompatibles dans les essais consignés) ; réseau NAT : Creative ne la joint pas sans `hostfwd` qemu |
| pc4 | `ssh pc4` (utilisateur `pc4`, clé `~/.ssh/id_ed25519_pc4_claude`) | **GitLab self-managed** (https://pc4.tail0c55ff.ts.net) ; GPU AMD : R9700 32 Go (ROCm natif dans `~/nexora-pc4`, Wan 2.2 installé et mesuré historiquement ; intégration Creative non prouvée), RX 9070 XT 16 Go, « MI50 » = Radeon Pro VII 16 Go gfx906 (PyTorch ROCm y échoue ; llama.cpp Vulkan) ; **sudo sans mot de passe installé par le fondateur selon les confirmations U104/U106 ; état actuel non revalidé** |
| pc5 | `ssh pc5-proxmox` | Proxmox VE 9.2 (seul PC qui garde Proxmox) : VM 201 site, 202 Creative (192.168.1.122, `ssh nexora-creative`), 203 WorkStudio, 204 GPU (192.168.1.124, `ssh nexora-gpu` : 2080 SUPER :8188, 2070 SUPER :8189, service audio :8190, gpu-unlock actif), 205 `nexora-infra` (registre, magasin de modèles, dimensionnement et copie des archives hors VM à revoir avec le HDD ; ne pas recréer pendant cette revue) ; 9100 pas à nous ; Tailscale serve de l'hôte |
- Sudo : le fondateur a déposé ses accès sur le Bureau de pc6 (ne les lis pas, ne les utilise pas) ; sudo NOPASSWD pc3/pc4 a été confirmé par le fondateur ; ne pas le lui faire réinstaller sans contrôler la situation (section 8).
- Le fondateur va installer Proxmox sur presque tous les PC (sauf pc5 déjà fait) : tout doit être en conteneurs/pods avec Dockerfile + manifestes dans GitLab + images archivées + magasin de modèles (poids hors des images, manifeste source/révision/sha256).

## 5. Dernier état documenté de Creative avant la revue (production non revalidée ici)
- **En production :** MiniMax-H3 (h3-fast nvfp4, h3-max 10Eros×Singularity int8) sur la 5090 ; Qwen-Image 2.1, TRELLIS.2, Music3, RealESRGAN sur le GB10 ; aperçus 3D (`objet-apercu`, `objet-multivue`) sur les deux cartes Turing de pc5 ; **réalisateur** (`app/server/nexora/realisateur.ts`, MR !23) : réécrit les demandes à l'arrache (Argon Flex), panneau « Ce que l'IA a compris » ; agent 3 niveaux + facturation (calcul implémenté = coût × 1,10 × 1,4025 × 100 crédits ; débit client réel et jetons Studio encore non prouvés/partiels, tarif non ratifié par le fondateur) ; Mode Studio ; Marketing ; détourage `/detourage` (SAM 3.1 + ViTMatte base, trimap 5 %, sélection par mot en anglais : à traduire automatiquement pour le français ; SAM 2.1 déclaré supprimé après SAM 3.1 fonctionnel ; inventaire distant non revalidé).
- **Config prod** : `/etc/nexora/creative.env` sur la VM 202 (`NEXORA_MOTEURS_GPU`, `NEXORA_DETOURAGE_URL` = pc3:8231, jeton).
- **Non branché / en test :** Pika H3 Flex et deuxième H3 GB10 : rapports annoncés dans le scratchpad perdu, résultats non retrouvés dans les chemins persistants inspectés. Wan 2.2 : installé et mesuré sur R9700 (T2V chaud266s, pic25,3Go ; Fun-Control266s/17,7Go), raccordement Creative non démontré. LTX 2.5 pro : mesuré sur5080, non raccordé ; verrou actuel `licences.ts` à distinguer d’un refus du fondateur (U068/U093/U095). **Transcription Studio GPU déjà livrée historiquement** : MR !33 / !35, `/transcrire` VM204:8190, Whisper large-v3-turbo, repli CPU ; essai visuel interface et disponibilité après panne non validés.
- **Qualité vidéo :** H3 était présenté comme le meilleur modèle ouvert (3e de l’arène) dans une recherche antérieure ; classement non revérifié, ne pas le reprendre comme vérité actuelle. Le client a jugé V4 « Une phrase. Un film. » (goutte d'or, en ligne sur le site) 6,5/10, V5 pire, **V6 5,7/10** : défauts = plans « jeu vidéo » au lieu de prises de vues réelles, voix « cheap » (voix native H3) ou « trop smooth » (ElevenLabs Alexandre), musique plate qui ne colle pas aux images. Il veut du spectaculaire (dragons, explosions, batailles spatiales, duels de lames d'énergie) en rendu photoréaliste, une musique écrite pour le montage (temps forts, dynamique, motif), choix du style laissé à nous.

## 6. Chantiers à reprendre (anciens agents interrompus ; état disque détaillé en section15)
1. **Film Creative V7** : 4 films à produire intégralement depuis le début par 4 équipes (DeepSeek, Muse, Argon Flex élevé, Opus), live action, voix Mistral Voxtral (`mistralai/voxtral-mini-tts-3-0`, `-2603`) contre MiniMax Speech 2.8, MAI-Voice-2.1, Fish S2.1, musique par sections ; worktree `/home/pc6/Desktop/NexoraCreative-film-v6`, branche `feat/film-v6-creative`, `marketing/creative/video-v6/` ; recette live action → `recherche/26-recette-live-action.md`.
2. **Film OPSYS-AI ultime ×4** : brief `marketing/nexora/campagne-films/opsys-ultime/BRIEF.md`, worktree `NexoraCreative-opsys-ultime`, branche `feat/opsys-ultime`, comparaison `COMPARAISON.md`. Scènes voulues : soumission par photo → signal satellite/5G/poteaux → serveur (entreprise virtuelle) → retour au représentant ; M. Morin ; adjointe (« rendez-vous avec M. Thibault à 14 h ») ; avatar comptable (+7 % de productivité) ; cédule 3 semaines ; pointage puis chèque de paye ; pas de tableau de bord ; musique entraînante.
3. **Infra pods/formatage** : `root/nexora-plateforme` (MR !1 ouverte, `docs/ARCHITECTURE.md`, `docs/FORMATAGE.md`) ; **détourage déjà en pod de production sur pc3 selon les preuves historiques ; migration complète des autres services non terminée** ; sauvegarde complète de GitLab (pc4) **non faite** (sudo requis).
4. **GPU de pc5** : mesurer ce que portent les 2 cartes 8 Go (détourage rapide, NVENC, Parakeet, Cosmos Reason2, transcription, voix, LLM réparti sur les deux) ; rapport `recherche/28-gpu-pc5.md` présent et fusionné selon la référence locale ; 69bbd96, f91a5dd. Transcription déjà raccordée, NVENC applicatif encore chantier non commité.
5. **Relief** : état de l'art + banc contre les meilleurs modèles 3D, spec plugin MCP, 10 cas d'usage → rapport29 final et spécifications `docs/backlog/relief.md` / `nexora-mesh-interface.md` **absents** ; recherches et bancs substantiels conservés hors Git dans `/media/pc6/Storage/Nexora/travail/relief-29/` (section15).
6. **Anciens bancs Codex H3/Pika GB10** : `h3-gb10/RAPPORT-H3-GB10.md` et `pika-gb10/RAPPORT-PIKA-GB10.md` étaient dans le scratchpad `/tmp` perdu. Non retrouvés dans données persistantes inspectées ; ne pas attendre un agent encore vivant, récupérer preuves et reconstruire rapports si nécessaire. Aucun gain H3/Pika établi par cette revue.
- Recherche déjà fusionnée : `recherche/23-grammaire-promos-ia.md` (102 promos analysées), `24-etat-de-lart-creative-2026-11.md`, `25-realisateur-et-vfx-blender.md`, `27-nvidia-pour-creative.md` (top 5 qualité : RTX Video SR, Cosmos Transfer 2.5, DiffusionRenderer/Harmonizer, Magpie+LipSync, Cosmos Reason2 ; top 3 vitesse : Sol-H3, NVENC+séparation des tâches, ModelOpt), backlog `docs/backlog/creative-triple-a.md` (TA1 à TA25 : mesurer Pika, refaire les promos selon la grammaire, facturation, 20 recettes, voix, interface triple A, compilateur de prompts, lipsync MuseTalk/LatentSync, MCP distant + API publique...).

## 7. Vision à moyen terme (décisions du fondateur)
- Chaque fonction de Creative (Relief, vidéo, musique, voix, détourage, lipsync...) sera aussi un **plugin Codex et Claude** via un MCP public + API (crédits). Architecture décidée : un seul dépôt produit (`nexora-creative`) avec des **modules indépendants** (README, tests, contrat E/S, conteneur, fiche MCP) + **miroirs GitLab en lecture seule par technologie** quand elle est prête + dépôt `nexora-plugins` pour les enveloppes.
- Plus tard : Relief a sa page dédiée et ses vidéos marketing ; films pour Creative, WorkStudio, Nexora, OPSYS et **15 vidéos sociales faites avec Muse** (15 angles avaient été rédigés).
- Prix : recherche/24 propose brouillon0,02CAD/s, finale0,10CAD/s, Studio gratuit et forfait29CAD/mois ; **propositions non ratifiées**, pas une décision commerciale ni la preuve d’un débit client réel.

## 8. Actions du fondateur et faux blocages à retirer
- **Déjà déclarées faites U104/U106 (04/11 09:14Z et09:18Z)** : commandes terminal pc3/pc4, sudo sans mot de passe, volume pc3 agrandi à466Go, suppression snapshot `avant-gpu-unlock-pr294` et test OrcaSAQ2 selon la suite du journal. Ne pas redemander ces manipulations ni recopier les anciennes commandes de suppression comme tâches actuelles ; vérifier d’abord quand le réseau le permet.
- **Commande regroupée depuis pc6, fichier présent et relu** : `bash ~/Desktop/nexora-actions-pc6.sh`. Le fondateur la lance lui-même si ces actions restent nécessaires : OAuth GitLab, puis limites CPU pc1/pc6 avec sudo. Cette revue ne l’a pas exécutée ; aucune confirmation d’exécution après le dernier message n’a été retrouvée. La variante pc1 y garde `GPU_SKIP=1` ; ne pas écraser sa5090 déjà à475W.
- **Réellement à suivre** : OAuth `GitLab-PC4` et visibilité complète des projets ; vérification limites CPU pc1/pc6 et carteAMD 330 W ; installation HDD10–20To, nom/domaine final, vrai SMTP, clé Stripe test et prix VPS/IPv4 publique ; rotation des clés exposées et jetonHF. Les ouvertures commerciales ne sont pas autorisées par la simple existence d’un prototype.
- **À requalifier, pas des approbations générales à redemander** : V100 réseau QEMU, retrait éventuel Chatterbox/Kokoro et environnements de tests, VM205, verrou logiciel LTX pro, vérification visuelle détourage/transcription. Le nom Mesh et les conditionsSAM 3.1 sont déjà réglés. La VM9100 et les autres projets ne doivent pas être modifiés dans ce mandat.

## 8b. Compléments historiques du 04/11 (horodatages originaux en UTC)
- **Nom du 3D de Creative : Nexora Mesh** (choisi par le fondateur). Espace de travail dédié dans Creative (type Meshy) + fonction dans Creative ; Hunyuan3D-2.1 à comparer ; recherche arXiv + GitHub/GitLab ; spec `docs/backlog/nexora-mesh-interface.md` et rapport `recherche/29` encore absents ; études/bancs persistants à synthétiser, aucun agent ancien présumé actif.
- **Documents Codex dans le dépôt** : `AGENTS.md`, `docs/PASSATION-AGENTS.md` (copie de ce fichier, à resynchroniser), `docs/PROCESSUS-TECHNOLOGIE.md` (processus standard pour toute technologie : recherche, concurrents, banc local, meilleure chaîne, module + fiche MCP, interface dédiée, marketing, miroir GitLab).
- **Dépôts** : décision = un dépôt produit (`nexora-creative`) à modules indépendants + miroirs GitLab en lecture seule par technologie + `nexora-plugins` (plugins Codex/Claude via MCP public).
- **Transcription GPU en production** (MR !33, !35) : Studio → `/transcrire` de la VM 204 (jeton dans `/srv/nexora-gpu/transcrire.token` et `creative.env`), repli CPU ; 26× le temps réel contre 1-3× ; autres points du service audio sans jeton (LAN) ; à tester dans l'interface.
- **Détourage** : en production sur pc3 (pod k3s, SAM 3.1) ; mode rapide aussi mesuré sur la 2070 SUPER de pc5 (0,91 s/image) mais la VM 204 manque de RAM (12 Go requis) et de disque.
- **Sous-agents** : passerelle corrigée (MR !31, conflit d'effort) ; les 4 alias passent. Codex en travaux : `NexoraCreative-live-director` (recette live action dans le réalisateur) et `NexoraCreative-sortie-video` (cartographie des encodages + NVENC sur pc5, `recherche/30-sortie-video.md`) ; leurs changements sont **non commités** sur disque, aucun commit inédit ; réviser/tests/commit avant push/MR (état exact section15).
- **Accès** : sudo sans mot de passe installé par le fondateur sur pc4 et pc3 ; disque de pc3 agrandi (466 Go) ; instantané `avant-gpu-unlock-pr294` supprimé ; OrcaSAQ2 supprimé.
- **Problème ouvert : Codex n'a pas accès complet à GitLab pc4.** `codex mcp list` : `GitLab-PC4` = « Not logged in » (OAuth du compte du fondateur expiré ; le fondateur doit refaire `codex mcp login GitLab-PC4` dans un terminal de pc6 et valider dans le navigateur). Le MCP `gitlab-nexora` utilise l'utilisateur de service `agent-nexora-workstudio-web` (admin, mais ne liste que certains projets : root/nexora-web, nexora-code-agent, nexora-workstudio, nexora-plateforme, nexora/nexora-code, etc.). Les projets personnels du fondateur (VoltaFabric, Gitspace/Forgejo, etc.) n'y apparaissent pas : accès à restaurer par OAuth ou par jeton d'accès personnel.

## 9. Pièges connus
- `/tmp` et les worktrees temporaires disparaissent aux pannes de courant (il y en a eu une). Tunnel pc1 : `tunnel-pc1.sh` ; ComfyUI pc1 : commande dans `~/Bureau/...` / mémoire `proxmox-nexora-infra`.
- ComfyUI de pc1 et du GB10 sont **partagés** par tous les films : jamais plus de 2 à 6 travaux d'avance, jamais de redémarrage.
- Tailscale sur pc6 est en mode utilisateur : tester les adresses ts.net depuis pc5 (`ssh pc5-proxmox curl ...`).
- Le pool SSD de pc5 (913 Go, 44 %) est sur-alloué en provisionnement léger (1000 Go de disques) : surveiller.
- Les agents délégués inventent parfois des références : vérifier chaque lien/arXiv/dépôt.

- **Film V7 de Creative** (04/11, 04 h 30, agent Opus du film Creative) : passation dans `/home/pc6/Desktop/NexoraCreative-film-v6/marketing/creative/video-v7/HANDOFF.md` (branche `feat/film-v6-creative`, MR !26) ; productions opus/gemini/muse en cours sur la file GPU, DeepSeek en écriture directe sur DeepInfra.

## 10. Comment on fait les choses (méthode du chef de projet : à reproduire)
- **Rôles.** Le chef de projet (Claude) décide, délègue et contrôle ; il ne bricole pas lui-même ce qu'un sous-agent peut faire. Équipes : Opus pour vidéo/montage/contrôle qualité de Creative, Sonnet pour le reste, sous-agents `deepseek`/`muse`/`gemini`/`gemini-eleve` pour le volume, Codex (gpt-6.1-sol, gpt-6-astra) pour des tâches d'ingénierie entières et la recherche web (`codex --search exec`). Tout le mécanique et les rendus passent par eux ; le chef de projet lit des résumés, des mesures et des planches.
- **Brief d'un agent** (toujours la même forme) : but et citations du fondateur ; ce qui existe déjà (fichiers à lire) ; machines et accès utiles ; mission numérotée avec critères de réussite ; règles non négociables ; compte rendu final court (chemins, mesures, coût, ce qui n'est pas vérifié).
- **Cycle de travail :** worktree hors du dossier principal (`/home/pc6/Desktop/NexoraCreative-<sujet>`), branche `feat/…`/`recherche/…`/`docs/…`, petits commits (trailer `Co-Authored-By`), push, MR via `gitlab-nexora` (`mr_create` puis `mr_merge` avec `wait_pipeline` : gitleaks inclus), déploiement, vérification réelle, ligne dans `docs/JOURNAL.md`. Dès qu'une MR est fusionnée : `git fetch gitlab && git merge --ff-only gitlab/developpement` dans le dossier principal et supprimer le worktree.
- **Qualité et évaluation :** jamais de note sans preuve ; planches d'images ; juges à l'aveugle présentés dans les DEUX ordres (Gemini Argon Flex élevé, GPT-6.1 Sol) ; les auto-notes des agents sont retirées de 1,5 à 3 points ; le fondateur tranche en regardant. Films comparés par équipes équitables (même brief, même budget, même chaîne, une ronde de révision chacune, version écrite à l'aveugle).
- **Recherche pour toute technologie :** voir `docs/PROCESSUS-TECHNOLOGIE.md` (littérature, libre, concurrents, banc local, meilleure chaîne, module + fiche MCP, interface, marketing, miroir GitLab). Vérifier chaque lien et chaque dépôt cités par un modèle délégué.
- **Économie :** déléguer, mesurer le coût (`outils/sous-agents/cout.sh`), ne pas relire inutilement, un seul job à la fois dans les files GPU partagées.
- **Déploiement de Creative :** depuis un worktree temporaire de `gitlab/developpement`, `deploy/proxmox/mettre-a-jour-creative.sh` (node_modules de mode-studio liés par symlink) ; VM 202 (`ssh nexora-creative`, sudo sans mot de passe), config `/etc/nexora/creative.env` (sauvegarder avant toute modification, ne jamais afficher). Vérifier : `curl http://192.168.1.122:3162/`, puis un parcours réel côté serveur.
- **Films :** chaînes dans `marketing/creative/video-v7/chaine/v7.py` (37 tests), `marketing/nexora/campagne-films/opsys-ultime/chaine/`, `usine/monter.py`. Images clés Qwen-Image (GB10), plans H3 (5090 : file partagée, 6 rendus d'avance au plus par film), voix (casting dans `voix-banc/`), musique par sections calée sur les temps forts, juge « réel contre synthèse », juge audio-vidéo sur le film mixé, copies téléphone < 28 Mo (H.264 ≈ 3,8 Mb/s, ffmpeg dans `/home/pc6/nexora-creative-data/engine/ffmpeg/`), archivage sur pc1.

## 11. Noms des technologies de Nexora Creative (attribués le 04/11 par le chef de projet sous la délégation de nommage ; seul Mesh est ratifié explicitement ; « Nexora » est le préfixe de l'entreprise, remplaçable partout en un seul endroit)
| Technologie | Nom | Rôle |
|---|---|---|
| 3D (notre « Meshy ») | **Nexora Mesh** (choisi par le fondateur) | texte/image vers 3D, textures, retopologie, rig, exports ; espace de travail dédié |
| Détourage vidéo | **Nexora Matte** | SAM 3.1 + ViTMatte, alpha pro, exports ProRes 4444/EXR/WebM |
| LLM qui réécrit les demandes | **Nexora Director** | réalisateur : prompts de tournage réel, FR/EN |
| Agent de production et de montage | **Nexora Producer** | agent à 3 niveaux, Producteur, « Producteur de nuit » |
| Montage (Mode Studio) | **Nexora Studio** | montage simple, très contrôlable, bulle d'effets au clic droit |
| Synchronisation labiale et avatars parlants | **Nexora Sync** | MuseTalk → LatentSync ; avatars d'OPSYS |
| Voix | **Nexora Voice** | narration, dialogues, clonage, FR/EN |
| Musique et son | **Nexora Score** | musique par sections calée sur le montage, effets sonores |
| Effets spéciaux | **Nexora FX** | couches RGBA, rééclairage, trajectoires, socle Wan 2.2 |
| Finition et export | **Nexora Finish** | agrandissement, interpolation, encodage NVENC |
| Tri des prises | **Nexora Critic** | juges réel/synthèse et audio-vidéo, Cosmos Reason |
| Transcription et sous-titres | **Nexora Scribe** | Whisper large-v3-turbo sur GPU de pc5, mot à mot |
| Mode marketing | **Nexora Campaign** | cartes, dépliants, logos, publicités |
| MCP public et API, plugins Codex/Claude | **Nexora Connect** | une fonction = un outil ; crédits facturés |
| Plateforme (conteneurs, k3s, modèles) | **Nexora Platform** | dépôt `nexora-plateforme` |
Marques non vérifiées (le fondateur gère le juridique). Les noms vivent dans un seul fichier de constantes (`app/src/produit3d.ts` pour Mesh ; créer un `produits.ts` commun pour les autres) pour pouvoir les changer.

## 12. Dernier état rapporté le 04/11 vers 10:39–10:53 UTC (05:39–05:53 Montréal), après disjonction — non revalidé
- **Limites de puissance déclarées posées dans la session précédente, pas mesurées ici** (service `nexora-limite-puissance` qui se réapplique à chaque démarrage ; script `/usr/local/sbin/nexora-limite-puissance.sh`, source dans le scratchpad `puissance/`, à copier dans le dépôt `deploy/puissance/`) : GPU à 80 % (pc3 5080 288 W, V100 240 W, pc4 R9700 240 W, une autre carte AMD 152 W, pc5 2080 SUPER 200 W et 2070 SUPER 172 W ; 5090 de pc1 déjà 475 W sur 600), CPU à 87 % (pc3, pc4, pc5). **Restent à faire par le fondateur (mot de passe sudo) : le CPU de pc1 et de pc6** (fichiers déjà déposés dans `/tmp` de pc1 et de pc6, commandes dans le chat). Une carte AMD de pc4 (330 W) était « occupée » : réessayer. L’ancien retour arrière désactivait le service puis redémarrait ; **ne pas l’exécuter durant cette revue**. CPU87% = plafond de fréquence/performance, pas13% de watts garanti.
- **Relancé à la main :** ComfyUI du GB10 (`engine/superviser-comfyui.sh`), tunnel pc1 (`engine/tunnel-pc1.sh`), ComfyUI de pc1 (commande : `cd $B/ComfyUI && HF_HOME=$B/hf-home TRITON_CACHE_DIR=$B/triton-cache XDG_CACHE_HOME=$B/xdg-cache TMPDIR=$B/tmp setsid nohup $B/venv/bin/python main.py --base-directory $B --listen 127.0.0.1 --port 18388 --disable-auto-launch` avec `B=/run/media/pc1/Infrastructure/NexoraStudioWork/minimax-h3`), passerelle des sous-agents (`outils/sous-agents/gateway.sh start`). VM de pc5 : toutes démarrées ; site et Creative répondent.
- **GitLab de pc4 : 502 dans le dernier diagnostic historique après redémarrage.** Le contrôle actuel ne l’atteint pas (proxy1055 indisponible), donc son état actuel est inconnu. Il tourne dans le Kubernetes de pc4 (namespace `gitlab` ; `sudo k3s kubectl get pods -A`) ; pods webservice/sidekiq en `Unknown`, `garage-0` (stockage) en `Error` ; patienter puis diagnostiquer. Sauvegarde complète de GitLab non faite (sudo maintenant disponible sur pc4).
- **Arrêtés par la panne (à relancer) :** productions des films OPSYS ×4 et V7 ×4 (chaînes reprennent où elles s'arrêtent : voir leurs `HANDOFF.md`), agents infra et Nexora Mesh, deux travaux Codex : `NexoraCreative-live-director` (recette live action dans `realisateur.ts`) et `NexoraCreative-sortie-video` (cartographie des encodages + NVENC) ; leurs prompts sont dans `docs/passation/` ; Director/Finish ont des modifications non commitées, pas des commits inédits.
- **Déployé et fusionné aujourd'hui :** transcription GPU de pc5 (MR !33/!35), détourage pod sur pc3 (MR !29), passerelle sous-agents (MR !28/!31), rapports27 et28 ; rapport26 présent sur la branche film, pas dans la dernière intégration locale ; rapport29 final absent, documents Codex (MR !34).
- **État Git corrigé** : `docs/passation-maj` a le commit local a854130 absent des refs distantes, puis le commit de cette revue à créer. Director/Finish ont des diffs non commités. V7 `4e9aeeb`, OPSYS `d728c65`, gpu-pc5 `69bbd96`, STT `fccce68`, Mesh `b636db9` et Plateforme `7a69f57` sont déjà connus par des refs distantes locales ; cela ne prouve ni fusion ni état actuel du serveur. Principal Creative en retard de6 commits, Site de7. Détails et fichiers à préserver : section15 et REVUE-ETAT-DISQUE.md.

## 13. Pour Codex : tu reprends à la place de Claude (abonnement à 99 %)
L’ordre détaillé actualisé est en section15 : vérifier réseau/services/limites/files en lecture seule ; préserver les diffs et résultats persistants ; restaurer l’accès GitLab complet avec action du fondateur uniquement si requise ; pousser la documentation quand possible ; reprendre films et intégrations depuis leurs preuves réelles ; sauvegarde intégrale/restauration avant formatage. Aucune relance générale automatique à partir d’un ancien HANDOFF.

Parle au fondateur court, honnête, en français, en disant ce qui n’est pas vérifié et en lui donnant seulement les commandes qu’il doit coller lui-même. Mets à jour le maître du Bureau et sa copie `docs/PASSATION-AGENTS.md` à chaque étape. Prompt prêt : `/home/pc6/Desktop/PROMPT-POUR-CODEX.md`.

## 14. Dernières précisions (04/11, abonnement Claude à 99 %)
- **Branche locale non poussée : `docs/passation-maj`** (worktree `/home/pc6/Desktop/NexoraCreative-doc-passation`, commit a854130 : cette passation, `docs/passation/` avec les prompts des travaux A et B, `deploy/puissance/`). À pousser et fusionner dès que GitLab (pc4) répond de nouveau (il renvoyait 502 après la panne ; un surveillant en arrière-plan attendait son retour).
- Les annexes sont aussi sur le Bureau : `/home/pc6/Desktop/NEXORA-PASSATION-ANNEXES/` (prompts A et B, script et service de limite de puissance).
- Le contenu du scratchpad de Claude (`/tmp/claude-1000/...`) a été effacé par la panne : ne compte pas dessus.


## 15. Revue exhaustive des dernières 36 h

### Périmètre, preuves et lecture

Revue du 04/11/2026, source jusqu’à 11:13Z/06:13 Montréal. Pour ne pas manquer le point de départ demandé (02/11 vers midi), la couverture dépasse volontairement 36 h et conserve aussi toutes les consignes anciennes encore actives. **101 messages réels uniques, dont 77 dans cette période ; 13 résumés analysés, 12 mémoires lues**. Notifications, résultats d’outils et doublons écartés. Une ligne corrompue L16978 et les 14 images sans texte sont signalées, sans inventer leur contenu.

Cette section et ses annexes priment sur les anciens états. `Uxxx` = message du fondateur, timestamp et ligne exacts dans **REVUE-CATALOGUE-FONDATEUR.md** ; `Sxxx` = résumé indexé dans **REVUE-SOURCES.md**. Les catégories (a) à (h) suivent ci-dessous, numérotées et datées. Les détails physiques et tout le backlog sont conservés dans les annexes ; aucune dépendance à `/tmp`.

Annexes durables : `/home/pc6/Desktop/NEXORA-PASSATION-ANNEXES/REVUE-*.md`, copies identiques dans `docs/passation/` de la branche `docs/passation-maj` :

- **REVUE-CATALOGUE-FONDATEUR.md** : chaque message réel, mots originaux, dates UTC/Montréal et ligne source ; trace des exclusions.
- **REVUE-EXTRACTION-FONDATEUR.md** : registre intégral a–h reproduit ci-dessous, avec preuves corrigées après audit.
- **REVUE-ETAT-DISQUE.md** : 18 worktrees, logs, non publiés selon refs locales, fichiers modifiés, contrôles réseau/services bloqués.
- **REVUE-AUDIT-CHANTIERS.md** : fichiers exacts films/Mesh/Director/Finish/Plateforme, sorties présentes et lacunes.
- **REVUE-AUDIT-DOCUMENTAIRE.md** : divergences ETAT/JOURNAL, VPS/Site/WorkStudio, 57 issues, critères de fini et ordre TA.
- **REVUE-SOURCES.md** : méthode, six noyaux de résumé/13 entrées, corpus, limites de preuve.
- **REVUE-RAPPORT.md** : résultat court, statut du commit/push et incertitudes restantes.

### Écarts qui changent immédiatement la reprise

| Chantier | État exact constaté et travail à reprendre |
|---|---|
| GitLab/Codex | Dernier 502 historique ; aujourd’hui le proxy 127.0.0.1:1055 est injoignable depuis le bac à sable, SSH interdit, navigateur indisponible. Pas de push, pas de preuve d’une panne GitLab actuelle. OAuth et visibilité complète VoltaFabric/NexoraCode/Gitspace/etc. restent à prouver. |
| Dépôts principaux | Creative 7139043, 6 commits derrière ref locale da27fa4 ; Site 1b8c93a, 7 derrière 56cb4c4. Ne pas réintroduire vert, Gitspace public ou transcription CPU en lisant seulement ces anciens HEAD. |
| Director | `NexoraCreative-live-director`, HEAD da27fa4 : 14 fichiers suivis modifiés + `liveAction.ts`/`bench/liveAction.ts` non suivis. Aucun commit inédit. Préserver/revoir/tests/banc de 12 briefs FR/EN, puis commit et MR ; annexe A. |
| Finish | `NexoraCreative-sortie-video`, HEAD da27fa4 : diff `filmMoteur.ts`/`service.py`, nouveaux clients/endpoint/tests/bancs ; `30-cartographie.tmp.md` présent, rapport final 30 absent. Export principal Studio = navigateur ; NVENC serveur ne déporte pas tout l’export. Annexe B. Les deux chantiers touchent `filmMoteur.ts`. |
| V7 | `NexoraCreative-film-v6` HEAD 4e9aeeb connu par refs locales. Aucun film d’équipe MP4 trouvé, seulement 6 clips du banc recette ; 60 MP3 de voix. Dossiers Opus 20 / Gemini 24 / Muse 12 plans ; **DeepSeek déjà écrit** dans `~/nexora-creative-data/promo/v7-creative/ecriture/deepseek/equipes/deepseek/`, à importer. |
| OPSYS ultime | HEAD d728c65 connu par ref locale, MR !27 historique brouillon. Rushes Opus 32 / Gemini 20 / Muse 23 / DeepSeek 25 ; brouillons long/court de 3 équipes, pas de final ni FINI ni COMPARAISON final ; DeepSeek : montage vide. Révisions existantes à reprendre, pas réécrire tout. |
| Mesh | Nom réglé, b636db9 sur wt-nom, non fusionné. Rapport 29 et spec d’interface absents ; **études nombreuses déjà faites hors Git**, sous `/media/pc6/Storage/Nexora/travail/relief-29/` : codex-a/b/ui/lit, journaux hy/pc4, runs/GLB. 20 Step1X, 3 Pixal BF16 + 4 anciens INT8, 7 TRELLIS GB10, 4 Hunyuan forme ; Paint vide. Synthétiser/vérifier, éviter de recommencer les études. |
| Wan/AMD/Plateforme | Wan 2.2 **installé et mesuré** R9700 ; intégration Creative non prouvée. Plateforme HEAD 7a69f57 : Dockerfiles / manifests / images / registre VM205 / code archivé existent ; GPU conteneurs / plan de contrôle k3s et migration complète non prouvés. Détourage déjà en pod de production. 13,14 Go de sauvegardes de code locales et ~69,9 Go de copie de poids ne remplacent pas un backup GitLab complet / une restauration. Archives OCI hors VM205 encore à faire. |
| SAM/STT/V100 | SAM 3.1 en pod pc3 et STT GPU VM204 historiquement déployés ; vérification UI / production après panne absente. V100 = torch cu126, pas cu128, réseau QEMU sans accès VM202 direct. |
| Puissance | Demande GPU −20 % sauf pc1 déjà à 475 W, CPU −10/15 %. Le script pose GPU à 80 % du plafond / CPU à 87 % de fréquence ; économies de watts CPU non mesurées. CPU pc1/pc6 et AMD 330 W restent à vérifier. Script `nexora-actions-pc6.sh` présent, aucune preuve de son exécution après le dernier échange. |
| Disques | `df -h` actuel : racine pc6 à 99 % / 16 G disponibles ; USB Storage à 26 % / 646 G disponibles. Dernière mesure historique du disque Infrastructure de pc1 : 1,8 T au total / 251 G libres, système : 33 G libres, 97 % ; pas remesuré ici. HDD pc5 attendu. |
| NexoraCode/autres | Chemin historique `~/Desktop/NexoraCode/src` absent. 10 commits historiques non poussés / refus `shallow update not allowed`, archive .git annoncée sur pc5 : **risque à récupérer**, pas une branche locale constatée. WorkStudio / GitLab autres projets = accès à vérifier, pas d’autorisation de modifier leur code. |

Les mesures issues des recherches sont datées/historiques ; fichiers présents ne signifient ni service vivant ni qualité acceptée. **La preuve fraîche de cette revue est le disque/Git local et les échecs d’accès du processus d’audit.**


## (a) Consignes permanentes et règles

1. **31/10 00:40:11Z, U001** — Philosophie « Tout le potentiel de l'IA à la portée de tous » : outil débutant, extrêmement puissant ; interface centrée sur l'intention ; mode expert ; un seul logiciel cohérent, pas une pile d'interfaces.
2. **31/10 00:40:11Z, U001** — Réutiliser une base mature, adapter les meilleurs composants, connecter des moteurs par interfaces stables ; développer seulement les manques et la différenciation. Comparer fork BeatDesign, studio plus mature, interface Nexora intégrant des SDK; pouvoir contredire les candidats initiaux.
3. **31/10 01:36:57Z, U002** — Règle pour **chaque projet logiciel Nexora** : sonder GitHub et GitLab ; fork/assemblage/base enrichie pour gagner maturité, productivité et puissance. OpenField et AIMovieStudiov2 ont bien des dépôts, fournis par le fondateur.
4. **31/10 00:40 et 02:12Z, U001/U003** — Recherche profonde : code, architecture, API, dépendances, tests, limites, performances, documentations, industrie et littérature arXiv ; ne pas s'arrêter aux README. Télécharger et tester ce qui est nécessaire dans le périmètre autorisé.
5. **31/10 00:40:11Z, U001** — Inspecter les acquis avant de recréer ; phases recherche, choix argumenté, prototype isolé, vérification ; distinguer documenté/code inspecté/tests exécutés/résultats réels. « Ne déclare aucune intégration terminée sans preuve ».
6. **31/10 02:12:26Z, U003 ; 02/11 05:08:30Z U031 ; 01/11 14:14:02Z U018 ; 04/11 07:37:58Z U089** — Chef de projet autonome : décider, prendre des initiatives, terminer, ne pas déranger ni redemander ce qui est déjà approuvé. U089 rappelle que cette infrastructure de test doit être formatée et que le temps est précieux : éviter les détours et confirmations inutiles. Continuer jusqu'à satisfaction ; la passation ne transforme pas cette autonomie en autorisation de modifier la production pendant la revue actuelle.
7. **31/10 00:40:11Z, U001/U002** — Studio accessible dans le navigateur, application de l'environnement utilisateur Nexora AI; compte unique, stockage/projets cloud, portefeuille de crédits, API/Privacy Router et jobs GPU mutualisés ; isolation multiclient dès le départ ; ComfyUI/nœuds jamais exposés directement aux clients.
8. **31/10, S001/S003 (période compactée)** — Exploiter au maximum un LLM cloud dans l'outil ; « l'important est l'outil »; intégrer toute amélioration pertinente du LLM, pas seulement un téléchargement de modèles.
9. **01/11 10:18:46Z, U016** — Ne pas consacrer les échanges au juridique : le fondateur et un avocat s'en occupent ; Qwen Image 2.1 doit être exploitable ; rester dans le mandat. La mission détourage U068 répète néanmoins aucune dépense ni acceptation de nouvelles obligations sans autorisation.
10. **01/11 14:14:02Z, U018; 02/11 U031/U032; 04/11 U069/U108** — Exigence « triple A », premium, spectaculaire, interface et ergonomie ; ne jamais déclarer une parité Higgsfield/OpenArt ou le « meilleur du marché » sur la seule confiance des agents. Étudier toutes les avenues utiles et chaque détail marketing/graphisme/moteur/code/contenu/parcours client.
11. **02/11 05:42:29Z, U032** — Satisfaction minimale **8/10**, viser 9–9,5 si possible. OPSYS-AI : **9/10 minimum** (U045). Les critiques et scores du fondateur priment sur les auto-notes.
12. **02/11 U032/U035/U039; 04/11 U069/U077/U103/U105/U108/U112** — Économiser très fortement l'abonnement Claude ; Opus 5.5 élevé pour films/montage/Creative quand nécessaire ; Sonnet 5.5 élevé pour le reste, Haiku autorisé sur mécanique. Déléguer aux autres modèles, chef de projet responsable du contrôle qualité ; quota à 95 %, puis 99 %, reprise Codex indispensable.
13. **03/11 05:01:30Z U054; 05:13:48Z U055; 04/11 U077/U105** — Trois modèles économiques disponibles pour les tâches, dizaines de DeepSeek/Muse autorisées : **DeepSeek V4.1 Flash 1017 via DeepInfra**, effort max ; **Muse Spark 1.3 Contributor via OpenRouter**, max ; **Gemini 4 Argon Flex seulement via OpenRouter**, moyen/élevé selon besoin. Ne pas remplacer Flex par une offre plus chère.
14. **03/11 U054/U058/U059; 04/11 U069/U074** — Comparaisons équitables : un même concept/brief, chaque modèle produit **entièrement** son film, y compris ses générations. Ne pas réutiliser les mêmes rushes et appeler cela plusieurs réalisations. Ajouter un quatrième film Opus ; confronter les évaluations agents et fondateur.
15. **03/11 05:01:30Z, U054; S012** — Tokens de l'agent produit facturés au client ; qualité maintenue tout en recherchant le modèle économique et la marge ; le harnais doit être spécialisé pour le montage et aider les agents à réussir cette tâche.
16. **03/11 03:00:46Z U047; 05:01:30Z U054; 04/11 U096** — Ressources et partitions : **jamais plus que le nécessaire**, minimum réel ; consolider plusieurs services si pertinent ; chaque Mo attribué, classé et étiqueté méticuleusement ; pas de fichiers éparpillés ni sauvegardes inutiles. Nettoyer les expériences terminées en respectant la conservation des créations et les interdits de suppression applicables.
17. **03/11 02:31:44Z U046; 03:00:46Z U047; 04/11 U095** — pc5 Proxmox = vrai serveur des applications Nexora ; code source sur GitLab pc4 et déploiements sur pc5; essais pc1/pc6, poids GPU sur les machines adaptées. Ne pas laisser les applications de production sur pc6 par facilité.
18. **03/11 03:00:46Z, U047** — Pas de sauvegardes sur les NVMe de pc5 à terme : HDD 10–20 To prévu ; allocations économes, plan de migration des sauvegardes à préserver.
19. **03/11 10:49:13Z U059; 23:36:37Z U064; 04/11 U110** — **Tout conserver depuis le début : chaque vidéo ET chaque infographie**, y compris essais/rejets/anciennes versions ; bureau de pc1, disque externe de pc1 si besoin ; pas seulement les derniers films. Registre et lacunes historiques à tracer.
20. **02/11 05:08:30Z U031** — Nom/domaine définitifs encore changeables : paramétrer logo/nom pour rebrand complet, conserver vidéos/infographies indépendantes de ces éléments. Réutiliser un seul endroit pour le changement.
21. **04/11 09:08:35Z, U102** — Produit international, commencer **français et anglais**; ne pas concevoir uniquement pour le français.
22. **04/11 U076/U095/U107** — Pour toute technologie : recherche scientifique et libre, composants réutilisés, tests locaux, intégration simple et puissante, environnement reproductible et transportable ; même méthode que Mesh pour toutes les technologies.
23. **04/11 U103/U107/U109/U112/U114** — Maintenir la passation continuellement, tout dire sur Nexora et les autres travaux, passé/présent/futur, méthode et accès ; relire 24–36 h ; préparer un prompt Codex collable et toutes commandes depuis pc6.
24. **S001/S008/S010/S012, consignes de sécurité rapportées** — Aucun secret dans dépôt/journal/réponse ; pas de `pkill -f`/`killall` par motif, seulement processus propres identifiés ; pas de connexion/acceptation de compte ou Tailscale à la place du fondateur ; pas d'achat, pas de mot de passe tapé pour lui. Ces règles sont reprises explicitement dans AGENTS.md ; la revue actuelle interdit même de lire les secrets.

25. **04/11 10:56:47Z et 10:58:48Z, U115/U116** — Confirme que la reprise visée est **Codex Desktop**, puis demande de vérifier concrètement que la passation et les outils sont prêts avant la bascule. L’existence de deux fichiers n’est pas une preuve de préparation complète.
26. **04/11 11:01:05Z et 11:03:23Z, U117/U118** — Confier à **Muse Spark 1.3 Contributor max** la vérification/réparation de Codex ; vouloir Codex « parfaitement fonctionnel avant que Codex commence ». Vérifier les recommandations du délégué : elles peuvent contenir des erreurs de catalogue et ne donnent pas le droit de changer les protections du fondateur.
27. **04/11 11:06:21Z, 11:09:29Z, 11:10:34Z, U119/U120/U121** — Piste de crédits **API Claude/Anthropic**, question de clé dans le courriel et inquiétude sur les 200 $ ; puis « **Ok oublions cela** ». Ne pas récupérer de clé, ouvrir le courriel ou configurer cette facturation ; piste mise de côté. Conserver l’exigence d’économie, sans inventer de tarif Sonnet.
28. **04/11 11:13:01Z, U122** — Décision finale : « **confie tout le travaille a codex** », nouvelle conversation imminente, mettre toute la reprise à jour. La passation et le transfert sont la priorité ; ne pas attendre une disponibilité Claude retrouvée.

## (b) Demandes terminées au niveau précisément prouvé

**Contrôle disque/Git effectué durant cette revue.** Fichiers et commits présents, mesures historiques conservées ; aucune production distante revalidée. Une réalisation technique partielle ne vaut ni acceptation esthétique ni livraison de toute l’ambition.

1. **31/10–01/11, U001/U008/U016** — Base OpenField et Mode Studio réellement codés : commits présents `0331521` (interface/pool GPU), `73e0ca8` (Qwen exploitable sans démo), `0f08293` (FreeCut/assistant/montage). Dépôt `Nexora Creative/app/` et `mode-studio/`. Pas de preuve du studio mondial achevé.
2. **01/11, U016/U017/U028** — Déploiement pc5 documenté et scripts présents : Creative `68f7aa3`, `deploy/proxmox/`, Site `docs/deploiement-proxmox-pile.md`, WorkStudio `docs/deploiement-proxmox-workstudio.md`. VM201 / VM202 / VM203 décrites ; disponibilité actuelle inconnue.
3. **01/11, U018/U028** — Campagne et coordonnées de gabarits présentes : `07cee14`, `8f68bdc`, `marketing/nexora/`. Nom/domaine/téléphone et validation des créations restent ouverts ; les fichiers ne constituent pas une campagne prête à publier.
4. **02–03/11, U031/U037/U041/U047/U054** — Refonte site/films réels et orange KTM : référence locale `gitlab/main` 56cb4c4 ; orange `7764d2c`, `d8f40ea`, reliquats `df79081`, `56cb4c4` ; Gitspace caché `c8e1c3a`. V4 et galerie documentés `a1aaede`/`7ccfbdb`, `0a93a72`/`fa65542`. Acceptation provisoire du site U054, pas d’autorisation de nouvelle refonte.
5. **03/11, U047/U054** — VPS pilote sur le vrai Proxmox : `82aef4d`, fusion `1b8c93a`, preuve présente `NexoraSite/docs/preuves/s6/e2e-vps-pc5.md`. Trois clients tests : checkout Stripe simulé→webhook→clone→SSH, stop/start/reboot, impayé/suspension/résiliation/rétention/disque supprimé et réconciliation sans orphelin. Paiement réel, IP publique et vente non prouvés ; prix de développement.
6. **03/11, U054/U059** — Harnais/mémoire : `a75a512`, `bed29ff`, `b148fe0`, `recherche/19` et `20` ; essais par palier et gain syntaxique consignés. Pas de preuve d’une qualité finale ≥8/10 ni d’un débit client réel.
7. **03/11, U054** — Bulle effet v0 et Marketing v1 : `ba5b2fc`, `c221d67`, fusion Marketing `1829bb7` ; 26 recettes / 19 tests et un appel LLM réel pour la bulle ; Marketing 7 formats / 9 gabarits, 26 tests, PDF avec fonds perdus. Facturation Studio, banc de 30 phrases, parité WebGPU/export, PDF/X certifié et fonctions restantes non terminés.
8. **03/11, U057/U059/U062** — TRELLIS.2 / 3D initiale et Blender : `a8e8c78`, `42c0190`, `d59938f`, recherche 21/25, code des exports/juges. Produit Mesh complet et textures/rig de tous modèles non livrés.
9. **03/11, U059/U064/U066** — Scripts pc5 gpu-unlock et 5090 présents : `deploy/pc5-gpu-unlock/`, `deploy/pc1-gpu-5090/`, recherche 28. Mesures historiques Turing 45→71 et 38→59 TFLOPS ; TRELLIS int8 inchangé. 5090 déclarée à 475 W / ventilateurs à 100 %, non remesurée.
10. **03/11, U059/U064** — Inventaire films présent, commit `dfe0dd3`, `marketing/nexora/campagne-films/TOUS-LES-FILMS-INVENTAIRE.md` : 1389 fichiers uniques / 22,7 Go retrouvés selon inventaire historique. V1/V2 anciens manquent, pas « tout récupéré ». Copies pc1 et nouveaux films/infographies non recomptés ici.
11. **03–04/11, U060/U061/U065/U074** — Bancs voix/musique présents : `f6d01cf`, `69d8701`, `marketing/nexora/campagne-films/comparatif-v2/rapports/VOIX-MUSIQUE.md` et `VOIX-MUSIQUE-MANCHE-2.md` ; Drama3 local et débit 1,30 mesurés historiquement, V7 : 60 MP3 présents. Aucune voix finale acceptée ; Mistral demandé, essais retrouvés.
12. **04/11, U068/U081/U083/U084/U085** — Détourage SAM 3.1 en pod pc3 selon journal et sources `deploy/k8s/detourage/` et `outils/detourage/README.md`, merge `3af5acb`, MR !29 puis documentation !32. LTX pro mesuré, V100 cu126 mesurée à 188,7 s / 224 images. Conditions SAM 3.1 acceptées U081. Cheveux/transparences/longs clips et parcours visuel complet non revalidés.
13. **04/11, U087/U095/U098** — Recherche NVIDIA 27 présente, fusion `75dc8c2` ; rapport pc5 `69bbd96`, fusion `f91a5dd`. Livrables de recherche achevés, implémentations proposées encore backlog (ne pas présenter un top 5 comme outils tous intégrés).
14. **04/11, U101/U102** — Transcription GPU  : code intégré : MR !33 / !35, commits `11bd236`, `fccce68`, `6758f04`, `55b0603`, `da27fa4`. `/transcrire` VM204:8190, Whisper large-v3-turbo fp16, jeton requis, WAV 150 Mo / 1 h, repli CPU ; mesures : 70 s→2,65 s GPU contre 29,4 s CPU, 221/222 mots et 149 s→3,9 s. Essai UI et disponibilité après panne inconnus.
15. **04/11, U093/U095** — Wan 2.2 R9700 installé et mesuré dans `NexoraPlateforme/docs/MESURES-PC4.md` et planches `docs/mesures/wan22-*` : T2V 266 s à chaud / 25,3 Go, FunControl 266 s / 17,7 Go. Plateforme HEAD `7a69f57`, fichiers Docker/Kustomize, registre VM205 et sauvegardes de code documentés. Migration complète, essai GPU des images et sauvegarde GitLab intégrale non terminés.
16. **04/11, U104/U106** — Commandes terminal déclarées faites par fondateur : dernières notes attestent sudo pc3/pc4, partition 466 Go, retrait snapshot / OrcaSAQ2. Preuve de déclaration utilisateur et journal ; pas de mesure distante fraîche, ne pas lui refaire faire ces suppressions.
17. **04/11, U107/U112** — Nom Mesh ratifié, code `b636db9` présent sur `feat/nexora-mesh-nom` : constante PRODUIT_3D, `/mesh` et alias, textes/MCP/tests. Pas fusionné dans da27fa4. Noms des autres technologies consignés en §11 sous délégation de nommage, sans retour explicite du fondateur ni déploiement global de constantes.

## (c) Demandes en cours : obligations précises à retrouver

1. **31/10 21:43:07Z U011 ; 02/11 U031/U032/U039/U040/U043 ; 03/11 U054/U058/U059/U062 ; 04/11 U069/U074/U075** — Page promotionnelle Creative et film épique demandés dès U011 ; refaire les films Creative jusqu'au niveau attendu, pas encore atteint. Spectaculaire mais photoréaliste live action ; rythme, flotte défendant la Terre, milliers de vaisseaux, tirs/explosions, dragons, combats/duels, effets impossibles = exemples, pas obligation de tout empiler. Meilleure référence = film à la goutte d'or visible sur le site ; U043 lui donne 6,5/10. V6 = 5,7/10 U074; versions suivantes rejetées si trop « jeu vidéo ».
2. **03/11 U054/U058/U059; 04/11 U069/U074** — Comparaison quatre équipes DeepSeek/Muse/Gemini Flex élevé/Opus : réalisations autonomes intégrales depuis zéro. Retrouver briefs, budgets, scripts, rushes, rendus et passations de chaque équipe ; plans identiques = test invalide.
3. **03/11 U060/U061/U065; 04/11 U069/U074/U075** — Voix/musique : refaire, tester d'autres voix, Mistral Voxtral privilégié pour essai francophone ; Fish Drama3 via OpenRouter vs voix H3; augmenter le débit de Drama3; ElevenLabs alors jugé meilleur mais Alexandre ensuite trop « smooth ». Qualité prioritaire, pas temps réel ; modèles locaux préférés à qualité comparable. Musique écrite pour le montage, dynamique et cohérente, style entièrement laissé au chef de projet.
4. **02/11 U043/U045; 03/11 U054/U058; 04/11 U069** — Films WorkStudio, Nexora, chaque offre et OPSYS-AI; WorkStudio ne doit pas être un tutoriel. OPSYS ne doit pas ressembler à une publicité de café : vendre concrètement le produit et faire comprendre les fonctions.
5. **04/11 U069** — OPSYS ultime : aucune capture du dashboard inachevé. Figure d'entreprise virtuelle dans un serveur ; représentant photographie revêtement → signal satellite/5G/lignes réseau → serveur/départements → soumission retournée ; Monsieur Morin ; ouvrier/chantier ; adjointe féminine professionnelle (« M. Thibault à 14 h », rendez-vous de 16 h déplacé); comptable en avatar (nouveaux ratios, productivité +7 %, profits prévus); avatar gestion donne cédule des trois semaines ; pointage puis chèque de paie. Film de 10 s ou quelques minutes selon bonne narration ; musique entraînante ; chaque équipe réalise toute sa version comme une vraie équipe marketing.
6. **03/11 U054/U059; 04/11 U069/U102/U107/U108** — Creative : poursuivre recherche scientifique et concurrence Higgsfield/OpenArt ; analyser centaines de promos ; synthèse de grammaire puis amélioration du produit. Filmcraft comme référence à dépouiller/adapter simplement ; Blender/3D pour VFX si bénéfice ; technologies manquantes à développer ; exploiter LLM au maximum, dont réécriture d'un brief « à l'arrache » en prompt détaillé.
7. **03/11 U054/U059** — AMD, mémoire du professeur, ReasoningBank et harnais spécialiste : tester réellement gain et limites, améliorer DeepSeek/Muse via professeurs Opus/Gemini/Muse ; comparaison coût/qualité, pas simple installation de mémoire.
8. **04/11 U068/U081/U083/U084/U085** — Détourage pc3 : SAM 3.1 imposé maintenant, sélectionner objet/personne/animal par clic et texte ; cheveux/fourrures/vêtements, transparence si possible ; suivi/occultations, alpha stable, fond image/vidéo, clips longs segmentés. Interface native, modes rapide/pro, job progression/annulation/reprise, aucun second éditeur ; livraison prouvée import→sélection→alpha→composition→export, plusieurs séquences et mesures réelles GPU/RAM/NVMe/temps. Pro LTX 2.5 Alpha-Gen à comparer INT8 streaming NVMe vs GGUF Q4 seulement si bénéfice, ne jamais confondre poids sur disque et mémoire totale.
9. **04/11 U071/U072/U085** — Exploiter V100 pc3, RX 9070 XT et « MI50 » pc4 utilement ; ne pas les laisser oubliées. Les poids/compatibilités/route réseau sont à mesurer, aucun modèle précis choisi par le fondateur pour ces cartes.
10. **04/11 U074/U076/U086/U087/U092/U093** — Wan 2.2 sur **R9700 pc4** : **installation et bancs déjà retrouvés** (266schaud/25,3GoT2V) ; raccordement Creative non prouvé. La demande explicite révoque le « pas Wan » de 31/10; LTX 2.5 existe déjà pc3, ne pas le choisir à la place par habitude. Question qualité la meilleure et mieux encore à étudier ; demander VRAM/prix HeyGen était une recherche, pas autorisation d'achat.
11. **04/11 U085/U086** — Bench d'un deuxième H3 sur GB10 versus **Pika H3 Flex**; le fondateur propose Pika « à la place sur pc6 », donc mesurer puis recommander, ne pas confondre intention d'installation et moteur raccordé en production.
12. **04/11 U076/U077/U095** — Mettre modèles, dépendances et environnements en conteneurs/pods reproductibles, stockables et prêts à recopier ; futur formatage de presque tout le parc, pc5 Proxmox conservé. AgentOS abandonné. Examiner si refaire rapidement ou archiver prêt à lancer ; inventaire, images, poids hors images, manifests et sauvegarde GitLab sont un travail à terminer, pas « tout en pods » déjà vrai.
13. **04/11 U087/U095/U098** — Recherche outils NVIDIA **et autres fournisseurs** : rapports27/28 présents et fusionnés selon refs locales ; concrétisation des améliorations encore partielle. Rechercher ce qui apporte un gain concret qualité/vitesse ; petits modèles utiles sur deux GPU pc5, pas seulement les grosses générations.
14. **04/11 U096/U097/U098/U099/U100/U101/U102** — Exploiter simultanément RTX 2070 SUPER et RTX 2080 SUPER pc5, minimum RAM/disque ; SAM 3.1 rapide, Whisper ou mieux en français/anglais et réellement utile ; s'il sert Creative, transcription sur GPU pc5. Ne pas attribuer la voix cheap à Whisper (STT) sans vérifier la vraie source.
15. **04/11 U102/U107** — Nexora Mesh : meilleur état de l'art, littérature/arXiv/GitHub/GitLab, comparer Hunyuan3D/TRELLIS et concurrents, cas d'usage au-delà des vidéos ; option intégrée + interface complète dédiée dans l'environnement, similaire Meshy ; page commerciale et films dédiés.
16. **03/11 U047/U049/U056/U057; 04/11 U109/U113/U114** — Débloquer **l'accès complet GitLab pc4 depuis Codex** pour VoltaFabric, Nexora Code, Gitspace/Forgejo, nv-driver-update et autres projets. Ce n'est ni développer Gitspace ni lui créer une VM. Une liste partielle du compte de service ne suffit pas. Ancienne preuve « marche » S012 contredite par le blocage signalé U109; authentification actuelle et visibilité complète à vérifier.
17. **04/11 U110/U111** — Envoyer les nouveaux films au fondateur ici/par courriel ; les archiver tous sur pc1. Mesurer espace restant du SSD **Infrastructure** pc1 avant d'y créer un dossier vidéo ; distinguer ce SSD du disque « Storage » précédemment non monté.
18. **04/11 10:34:32Z U111** — Après disjoncteur sauté : **−20 % watts de tous les GPU sauf pc1 déjà fait**, et **−10 à −15 % CPU si faisable** pour chauffe, préservation matériel et électricité. Retrouver scripts/mesures et besoin de commande fondateur ; une simple annexe préparée ne prouve pas limites appliquées/persistantes.
19. **04/11 U112/U113/U114** — Donner un nom à chaque technologie ; expliquer méthode complète à Codex ; commandes toutes exécutables **depuis pc6**, incluant accès GitLab ; passation intégrale et prompt de démarrage court.

20. **04/11 10:58–11:13Z, U116/U118/U121/U122** — Préparation de Codex et GitLab avant reprise : audit Muse rapporté, mais accès GitLab complet et retour du service encore non prouvés. L’autre session rapporte un patch de sonde PostgreSQL et une corruption Garage ; la revue ne les a pas exécutés. Détails datés en section 16 du maître. La volonté de « parfaitement fonctionnel » reste un critère, pas un résultat acquis.

## (d) Demandes jamais exécutées, oubliées ou sans preuve suffisante

1. **03/11 10:49:13Z U059** — **15 vidéos promotionnelles Muse, 15 angles différents**, après les films principaux. Les angles préparés ne sont pas les vidéos. À classer non livré tant que 15 fichiers exportés et évalués manquent.
2. **03/11 U059/U064; 04/11 U110** — Conservation de **toutes les infographies** autant que films : la passation précédente ne parle souvent que vidéos. Des vieux films supprimés sont irrécupérables si aucune autre copie n'existe ; inventaire des trous/regénération possible à conserver, pas promesse « tout est là ».
3. **04/11 U095** — Réponse claire à « as-tu mis chaque modèle et environnement dans un pod ? » : ne pas escamoter par une architecture documentaire. Inspecter les vrais runtime ; établir liste restant native.
4. **04/11 U111** — Demande de réduction de puissance GPU/CPU et mesure SSD Infrastructure, très tardive ; prouver application sur chaque machine ou lister précisément non exécuté. pc4 redémarré/GitLab indisponible ne prouve pas exécution.
5. **04/11 U112** — Noms de **toutes** les technologies : Mesh seul ne remplit pas la demande. Relever propositions actuelles, marquer proposés/choisis, ne pas annoncer des noms validés sans accord.
6. **03/11 U054; 04/11 U102/U107** — Cour(t)s/longs métrages, modules concurrents (lip-sync, avatars, motion transfer, cohérence, relight, inpainting, plugins) : un backlog ou un bouton ne suffit pas à dire réalisés. Distinguer code, moteur installé, raccordement, tests E2E et recette utilisateur.
7. **04/11 U068, S012** — Détourage pro complet : qualité cheveux/animaux/transparences, toutes catégories et clips longs, import direct dans timeline ; ne pas le qualifier terminé sur clips Big Buck Bunny ou seule preuve export. Plusieurs critères de la mission restent à retester avec SAM 3.1/pc3.
8. **03/11 U054/U058/U059; 04/11 U069/U074** — Quatre films vraiment autonomes de qualité ≥8 et OPSYS≥9 : le dossier de brief, des agents lancés ou des rushes en file ne sont pas la livraison finale.
9. **03/11 U047/U049/U056/U057; 04/11 U109** — GitLab full access toujours problème malgré annonce de succès antérieure. Tester **tous les projets** explicitement cités avec identité/permissions, sans recréer une application Gitspace.
10. **31/10 S003; 04/11 U085/U086** — H3 maintenu sur GB10 demandé puis supprimé par erreur ; demande ensuite évoluée vers Pika/bench. Documenter issue finale et résultat du bench, pas faire disparaître l'erreur ni conserver l'ancienne attente sans nuance.
11. **02/11 U031/U041** — Portail complet mettant en avant workflow et agent qui exploite le PC utilisateur : vérifier réalisation réelle, pas supposer que la refonte de l'accueil l'implémente.
12. **01/11 U018/U028; 02/11 U031** — Kit marketing et cartes : le dossier ancien ne signifie pas coordonnées finales, rebrand fait, téléphone fourni, nom domaine acheté ou imprimés 300 dpi. Toutes dépendances de finalisation restent à tracer.

## (e) Idées, ambitions et décisions de produit futures

1. **31/10 U001** — Cinema Studio (caméras, objectifs, éclairage, cadrage), T2V/I2V/V2V/audio synchronisé, motion transfer/remplacement, cohérence personnages/produits/lieux, effets un clic, productions longues multi-plans, storyboard, retouches/inpainting/relight/upscale/interpolation, bibliothèque références/LoRA/projets, exports professionnels et reprise sans perte.
2. **31/10 U001** — AI Director différenciant : idée→scénario→moteurs compatibles→références→plusieurs plans→évaluation→corrections ; reprendre une seule scène sans tout régénérer. Registre universel capacités/contraintes/formats/coûts/paramètres/droits ; ajout moteur avec minimum de changements UI; profils Rapide/Équilibré/Qualité max choisis selon tâche/matériel/coût.
3. **31/10 U001** — MiniMax majeur mais architecture non captive ; optimisation quantification/pruning/distillation/kernels/attention/cache/offload avec mesures froid/chaud/mémoire/transferts/audio/qualité/temps complet, pas présomption « plus petit = plus rapide ».
4. **01/11 U016; 02/11 U039/U043; 03/11 U054** — Mode Studio Premiere simplifié, manuel précis + automation assistée, chatbot, longs métrages et pub ; clic droit au temps 3:22→effet→bulle d'intention. Chercher skills montage/son/image de haut niveau, applicables aussi à l'agent intégré.
5. **01/11 U018; 03/11 U054** — Marketing complet : cartes d'affaires, dépliants, logos, accroche-portes, affiches/arrière-plans Facebook, objets promotionnels, campagnes numériques, vidéos ; pas seulement génération de clips.
6. **02/11 U031** — Offre réception virtuelle complète (appels entrants/sortants, courriels, SMS), surveillance vidéo temps réel/rapports/alertes email/SMS/dashboard/mobile et signalement sécurité ; infrastructure IA complète chez le client ou sur serveurs Québec. Présenter la valeur sans répéter Québec partout ; ne pas mettre caméras en tête de l'accueil (correction U047).
7. **04/11 U102/U107** — Chaque fonction indépendante de Creative (Mesh, musique, vidéo, détourage, lip-sync…) utilisable via plugins Codex/Claude et autres, MCP/API publics facturés ; modules réutilisables hors Creative. Question de dépôts individuels/tout/un double dispositif ; décision d'architecture assistant à distinguer des mots du fondateur (« Vas y » U107 peut approuver proposition précédente à contextualiser).
8. **04/11 U076/U077/U095** — Proxmox sur presque tous les PC après formatage, exception pc5 déjà en place ; unités transportables prêtes à recopier, modèles et environnements centralement archivés.
9. **04/11 U102** — Ambition internationale après fr/en ; Nexora Mesh produit recherché avec usages multiples, page et marketing même s'il demeure intégré.
10. **04/11 U111** — Baisser consommation et chaleur comme politique durable de préservation GPU/CPU, pas seulement un dépannage après panne.

## (f) Décisions/actions du fondateur encore possibles — sans faux blocages

1. **01/11 U028/U029/U030; 02/11 U031; S010** — Nom d'entreprise et domaine final ; .ai/.com/.ca, alternatives. `nexora.ai` annoncé souhaité puis trouvé indisponible dans une lecture historique ; **rien acheté prouvé**. Info@nexora.ai était une donnée de gabarit souhaitée, pas un mail opérationnel garanti. Téléphone/adresse/personne/titre restent à fournir selon livrables.
2. **03/11 U047 et S012** — Installer HDD 10–20 To pc5 et choisir disposition/sauvegardes ; Stripe test, prix VPS et IPv4 publique sont des dépendances d'ouverture, pas inférés du silence.
3. **03/11 U060/U065; 04/11 U074/U075** — Verdict humain des nouveaux films, voix et musique. Il a déjà délégué **100 % du style musical**; ne pas lui redemander de choisir un style pour avancer. Ancienne demande de garder plafond 475 W ou 400 W est surpassée pour autres machines par U111; pc1 explicitement excepté.
4. **04/11 U109/U113/U114** — Si OAuth GitLab reste expiré, fondateur exécute connexion depuis pc6 et valide navigateur ; ne pas saisir mot de passe/jeton. Après restauration, agent vérifie réellement visibilité des projets.
5. **S012; 04/11 U085/U099/U100** — Suppression environnements chatterbox/sgl-gb10, voix Kokoro/Chatterbox de VM204, réaménagement VM205 et données : si pas déjà autorisées/constatées, ne pas les marquer faits. Les demandes « supprime la » U097 doivent être rattachées à l'objet exact du tour précédent, jamais généralisées.
6. **S012** — Rotation clés exposées, éventuel montage disque Storage pc1, sort VM9100 (autre projet), LTX pro raccordé en prod si décision produit requise. « Choisir nom de Mesh », « accepter SAM3.1 », « installer sudo pc3/pc4 » et « exécuter commandes déjà faites U104/U106 » **ne sont plus des décisions ouvertes génériques**.
7. **04/11 U068** — Tout achat, nouvelle licence ou obligation contractuelle reste à son action/accord explicite ; ne pas retransformer la délégation technique en autorisation de paiement.

8. **04/11 11:10:34Z, U121** — La piste API Anthropic est mise de côté : la clé et le script de démarrage ne sont pas des actions en attente. Seule la connexion GitLab et les actions sudo encore nécessaires peuvent exiger sa participation. U122 confirme de passer le travail à Codex.

## (g) Faits d'infrastructure issus des messages — à dater et mesurer

1. **31/10 U001/U006/U008** — pc6 DGX Spark/GB10, pc1 RTX 5090 32 Go H3 déjà présent, pc3 RTX 5080 16 Go ; pc1 a des variantes H3 spécialisées. Deux H3 seulement demandés U032; Qwen2.1 et Music3 sur GB10; mémoire GB10 partagée à dimensionner. **04/11 07:07:29Z U078** : le fondateur croyait que davantage de modèles étaient sur pc6 ; clarifier l’inventaire et les emplacements réels.
2. **01/11 U016/U017/U028** — pc5 hôte Proxmox installé, accès initial 192.168.1.106:8006 et Tailscale `gx10-e526` puis `pc5-proxmox`; le vrai serveur Nexora est pc5.
3. **03/11 U047/U054/U059; S012** — pc5 deux cartes RTX 2080 SUPER et RTX 2070 SUPER, VM GPU minimale avec les deux GPU complets ; modèle exact VM204/ports et limites à relire ; VM9100 n'appartient pas au chantier.
4. **03/11 U058/U059/U064; 04/11 U071/U111** — Disques pc6/pc1 sous pression ; pc1 espace autorisé à volonté, disques externes pc1 « stockage/Storage » et SSD « Infrastructure » à distinguer ; disque externe **1 To pc6** ajouté U071.
5. **04/11 U067** — Panne d'électricité : agents/services interrompus, /tmp pouvant disparaître ; demande relance alors autorisée. **U111** : nouvelle disjonction parce que parc chargé simultanément, demande baisse puissance.
6. **04/11 U068/U070/U071/U072** — pc3 RTX 5080 16 Go, RAM 32 Go, SSD/NVMe, Comfy existant, LTX 2.5 déjà présent ; clé SSH pc3 et clé VM V100 sur bureau pc6 (ne pas ouvrir pour la revue); partition agrandissable ; OrcaSAQ2 test autorisé à supprimer.
7. **04/11 U071/U072/U085** — V100 pc3 disponible pour autre modèle ; accès VM et compatibilité à vérifier ; ne pas déduire bf16/FP8 ni accès direct depuis Creative.
8. **04/11 U076/U079/U080/U088/U090/U091/U094** — pc4 trois GPU nommés par fondateur RX 9070 XT/R9700/« MI50 »; SSH/admin via pc6, fondateur sans accès direct ; clés et sudo déposés sur bureau/courriel, sans qu'il faille les lire pour cette revue. Identité réelle « MI50 » à vérifier par inventaire matériel avant installation.
9. **04/11 U081/U082/U083/U084** — SAM 3.1 conditions déjà acceptées par fondateur, plugin HuggingFace connecté, source imposée Comfy-Org/sam3.1; token transmis en dehors de l'audit, ne pas l'afficher ni lire son fichier.
10. **04/11 U103/U112** — Limite Claude 95 % puis 99 %; sous-agents et abonnement Codex existants sont la continuité. Une session/agent « lancé » avant panne n'est pas preuve qu'il tourne encore.
11. **04/11 U109** — MCP GitLab partiel bloque depuis plusieurs jours VoltaFabric, Nexora Code, Gitspace/Forgejo et autres. État actuel doit primer sur ancien S012 « codex exec listed projects ».

12. **04/11 11:10:34–11:13:26Z, U121/U122 et rapport d’assistant L21022/L21042** — Dernier état rapporté par l’autre session : GitLab encore 502, `gitlab-postgresql-0` lent et tué par sa sonde, seuil de sonde porté de 30 à 240 ; `garage-0` en boucle avec SQLite annoncé corrompu. Volumes non vérifiés par la présente revue ; aucune réparation ou restauration à déclarer réussie. Le commit documentaire `203c633` de l’autre session est bien présent localement.

## (h) Pièges, erreurs et corrections à transmettre

1. **31/10 S003/S006** — Mauvaise lecture « connecter H3 5090 » : H3 supprimé de GB10 alors que le fondateur voulait le conserver **avec** Music3 et Qwen ; copie pc1 vérifiée historiquement, remise contrariée par espace. Demande finale évolue vers Pika, ne pas supprimer de nouveau pour résoudre une hypothèse.
2. **31/10–04/11 S003/S008/S012** — `pkill -f` a tué des shells et été réutilisé malgré interdiction. Ne jamais copier ces commandes de l'historique ; services/GPU partagés, PID exact du seul processus lancé par soi.
3. **01–04/11 S008/S012** — Plusieurs clés affichées dans sorties outils (~4 incidents rapportés); fichiers « Nom: valeur » mal expurgés. Rotation à recommander sans republier clés ; ne jamais copier sorties brutes/credentials dans passation.
4. **03/11 U048/U049/U050/U051/U052/U053/U056/U057; S012** — Contresens Gitspace : créer VM/VPS alors qu'il fallait corriger MCP GitLab. Gitspace sera pc4; suspendre son développement et le cacher du site jusqu'au produit prêt. « Gitspace » produit et MCP historiquement nommé gitspace sont deux choses ; MCP renommé `gitlab-nexora`.
5. **03/11 U058; 04/11 U074; S012** — Films plusieurs modèles visuellement identiques parce que rushes mutualisés : comparaison invalide, ne pas répéter. Vieux films OPSYS incompréhensibles, « pub de café »; WorkStudio trop tutoriel ; mieux expliquer produit et bénéfices.
6. **03/11 U060/U065; 04/11 U069/U074/U075** — Voix choisie pour vitesse au lieu de qualité (0,1/10), confusion STT/TTS et audio temps réel/rendu offline ; musique plate/non synchronisée ; Eleven Alexandre trop smooth ; simple normalisation LUFS ne remplace pas écoute réelle.
7. **03/11 U064 et S012** — Anciennes vidéos rejetées supprimées avant consigne de conservation : pertes reconnues, inventaire/régénération possibles à tracer. Ne pas dire « toutes archivées » au vu des seuls derniers films copiés.
8. **02/11 U032/U035/U037/U040; 04/11 U074** — Esthétique jeu vidéo/static/cheap, flotte pauvre et voix faibles ; auto-évaluations trop flatteuses. Donner mesures/planches, verdict fondateur ; scores 3/10, 6,5/10 puis 5,7/10 représentent des versions différentes, pas progression automatique.
9. **03/11 U047/U054/U096** — VM/disques surdimensionnés et sauvegardes NVMe contre économie ressources ; ne pas allouer « au cas où » ni supposer deux GPU utilisables comme une carte à VRAM fusionnée.
10. **04/11 U069** — Ne jamais montrer dashboard OPSYS inachevé ni inventer une fonction prête. Départements/avatars dans film représentent une vision, pas capture de produit terminé.
11. **04/11 U085/U095/U112** — Ne pas laisser copies modèles/environnements/tests inutiles ; ne pas dire « tout est en pods » quand seuls manifests/architecture existent ; conserver créations finales et besoins reproductibles.
12. **04/11 U109** — « GitLab fonctionne » après liste partielle est un faux positif : tester droits du fondateur sur projets requis ; OAuth et compte service ne sont pas interchangeables.
13. **S012** — Déploiements site désordonnés ont perdu une route Gitspace ; repartir d'une référence exacte validée et vérifier. Conflits deux agents dans un worktree ; un sujet/un worktree.
14. **S012** — Tailscale userspace pc6 peut faire échouer HTTP vers `ts.net`; tester depuis pc5 ou chemin réseau valide avant de déclarer serveur en panne. Clé hôte VM204 a changé après cloud-init/panne ; ne pas conclure attaque ni supprimer known_hosts globalement.
15. **S001/S003/S006/S008/S010/S012** — Résumés sont des instantanés, pas commandes actuelles ; certains anciens blocages (SAM gated, accès pc3, sudo, nom Mesh, transcription CPU) sont déjà dépassés. Les annonces « déployé », « lancé », « terminé », « 7,6/10 » doivent être distinguées de commit présent, endpoint répondant, résultat conservé et validation fondateur.

16. **04/11, contrôle de cette revue** — `nexora-actions-pc6.sh` utilise `set -u`, sans `set -e` ni arrêt explicite entre chaque étape. Un message « Terminé » ne prouve pas la réussite d’OAuth ou des limites de puissance. Le script n’a pas été modifié pendant cette revue.

17. **04/11 11:04–11:13Z, U118/U122 et rapport de l’autre session** — L’audit Muse de Codex s’est trompé sur des modèles/efforts ; ne pas appliquer ses propositions sans preuve locale. Ne pas changer `approval_policy` ou `sandbox_mode`. Une autre session a écrit/commité la passation pendant la revue : conserver ses ajouts, distinguer leur provenance et synchroniser les copies après réconciliation, sans écraser le travail concurrent.

## Chronologie courte et ordre de reprise proposé

- **31/10** : mission studio, base libre et recherche scientifique ; H3, Qwen, musique, réalisateur, page Creative et premières promos. Erreur suppression H3 GB10, premières contraintes secrets/processus.
- **01/11** : Mode Studio, Qwen exploitable, vrai hébergement pc5, kit marketing complet ; coordonnées provisoires et domaine non acheté.
- **02/11** : refonte accueil environnement utilisateur, photos corrigées, films trop jeu vidéo ; V4 goutte d'or atteint 6,5/10 mais texte à améliorer ; OPSYS film 9/10 demandé.
- **03/11** : ressources/VPS minimaux, GitLab Codex bloqué confondu avec Gitspace ; orange KTM; agent économique trois paliers, mémoire, 3D, deux GPU pc5; films indépendants, conservation tout et 15 futurs films Muse ; critiques sévères voix/son.
- **04/11 avant 07Z** : panne puis reprise ; mission détourage pro et pc3; grand brief Creative/OPSYS; nouvelles voix et réalisme, 5,7/10.
- **04/11 07–09Z** : SAM 3.1 imposé, Wan 2.2 pc4, Pika GB10, pods/formatage, NVIDIA/autres, utilisation pc5, transcription GPU.
- **04/11 09–10:53Z** : bilingue/plugins/Mesh, commandes sudo confirmées, passation Codex et GitLab complet, disjonction/baisse watts, tous noms technologies et prompt final.

**Aujourd'hui** : consolider preuves disque/branches/scratchpads, sauvegarder durablement ce qui existe sans production ; revalider les services et limites réelles quand un réseau autorisé est disponible ; rétablissement GitLab côté fondateur si requis ; ne pas relancer rendus avant état puissance/queues partagé ; récupérer films/rushes/rapports, vérifier quatre équipes réellement indépendantes et conservation totale ; terminer passation + prompt.

**Cette semaine** : terminer contrôles et intégration déjà codés réalisateur/sortie vidéo/Mesh/transcription/détourage ; valider perceptuellement films/voix/musique ; finaliser l’intégration Wan déjà mesuré et retrouver/reconstituer le banc Pika/H3; conteneurs/manifests/export dépendances et préparation formatage, sauvegarde GitLab et plan HDD; régler full access GitLab.

**Plus tard** : 15 films sociaux Muse après promos principales, plugins/MCP/API facturés, interfaces/marketing de chaque technologie et lip-sync/cohérence/VFX, ouverture publique après domaine/paiement/SMTP/prix, internationalisation après fr/en. Les priorités sont proposées ; ne pas convertir des dépendances hypothétiques en demandes d'approbation inutiles.

Complément de corpus : U115–U122 et leurs timestamps/lignes sont ajoutés au catalogue durable ; le relevé final source s’arrête à L21043, 04/11/2026 11:13:26.991Z. Les 114 candidats initiaux et leurs exclusions restent décrits pour traçabilité ; total final 122 candidats, 101 messages réels uniques, dont 77 depuis le 02/11 vers midi.

### Plan d’actions priorisé après cette passation

**Aujourd’hui — reprise contrôlée, sans toucher à la production pendant le diagnostic**

1. Lire le maître et les annexes, confirmer réseau GitLab/services/puissance/files en lecture seule dans un contexte autorisé ; ne pas confondre refus du bac à sable et panne distante. Vérifier sudo/OAuth déjà faits avant de demander une action au fondateur.
2. Préserver les 14 diffs Director, le code Finish et les recherches Mesh hors Git ; aucun reset / clean / suppression de worktree. Contrôler archivage pc1 et films/infographies manquants. Rechercher archive Nexora Code pc5 et backup GitLab complet avant toute opération destructrice.
3. Quand GitLab répond : actualiser les refs, vérifier projets visibles et pipeline, pousser d’abord `docs/passation-maj`, MR vers developpement ; résoudre l’écart de 6 commits documentaires. Ne pas pousser tout l’inventaire de branches aveuglément. Pas de nouvel accès/compte/jeton créé par l’agent.
4. Lire les HANDOFF des films en les traitant comme historiques, importer le travail DeepSeek V7 existant, planifier reprise à partir des états/rushes ; pas de relance massive ni des PID anciens. Finaliser Director/Finish après revue/tests adaptés, intégrer leurs conflits séparément. Cette mission de revue ne les a pas implémentés ni déployés.

**Cette semaine — qualité et fiabilité avant ouverture**

1. Achever quatre V7 et quatre OPSYS indépendants, écouter les voix FR/EN et musique sur le film mixé ; planches/mesures, une ronde équitable, verdict du fondateur ≥8 pour Creative / ≥9 pour OPSYS ; tout archiver et préparer des copies ≤28 Mo. WorkStudio/Nexora et chaque offre gardent leur demande de films propres.
2. Synthétiser la recherche 29 et l’interface Mesh depuis les travaux existants ; intégrer le renommage b636db9 sans refaire ; finir les bancs forme/texture/UX manquants. Reconstituer les rapports H3/Pika GB10 avant recommandation ; Wan déjà mesuré → étudier le raccordement et les gains VFX, pas réinstaller par oubli.
3. Vérifier les parcours SAM/STT de bout en bout, traduction FR du détourage, règles authz/quotas, facturation Studio + crédits réels (#4, #36, #54), persistance jobs/projets (#10, #31), parité aperçu/export (#8). Les paiements restent en test jusqu’à accord explicite.
4. Backup GitLab complet + restauration éprouvée, images hors VM205, inventaire des poids/source/révision/sha, plan HDD / dimensionnement minimal. Aucun formatage avant preuve de reprise. Déterminer la proposition DGXOS pc6 face à la volonté Proxmox sans inventer une décision déjà prise.

**Plus tard — ambitions à conserver**

1. Après les films principaux : **15 vidéos promotionnelles Muse, 15 angles réellement exportés**, pas seulement leur texte.
2. Plugins Claude/Codex et MCP/API publics facturés, modules réutilisables / miroirs en lecture seule, pages et films de chaque technologie ; lip-sync/avatars, continuité longue, VFX, film de 5 min puis long métrage, cours/marketing avancé ; suivre 57 issues et TA1–TA25 sans prendre les cases prévues pour des livraisons.
3. Domaine/rebrand final, SMTP, Stripe/prix VPS/IPv4 et ouverture commerciale seulement lorsque les prérequis réels sont réglés ; internationalisation après FR/EN complètement prouvés. Le style musical est déjà délégué à 100 %, le nom Mesh est déjà choisi : aucune approbation générale à redemander.

### Livrables de cette revue et statut Git

Maître du Bureau synchronisé vers `NexoraCreative-doc-passation/docs/PASSATION-AGENTS.md`, annexes durables et prompt de 51 lignes préparés. Le commit documentaire `203c633` de l’autre session est présent ; le **nouveau commit demandé n’a pas pu être créé** : `.git/worktrees/NexoraCreative-doc-passation/index.lock` est sur un système de fichiers en lecture seule dans ce bac à sable. Aucun fichier n’a été indexé par cette tentative. Depuis le terminal normal de pc6, le fondateur peut lancer `bash ~/Desktop/nexora-commiter-passation.sh` : vérification des copies, commit documentaire avec le trailer demandé, aucun push. Voir **REVUE-RAPPORT.md** ; ne pas confondre le commit antérieur de Claude et cette revue encore non commitée. **Aucun push tenté**, le contrôle Git en lecture seule échoue sur le proxy 1055 avant d’atteindre GitLab. La prochaine session relit ce statut puis agit selon la connectivité réelle.

## 16. Addendum reçu de l’autre session Claude pendant la revue (04/11, 11:13 UTC / 06:13 Montréal)

**Provenance distincte :** cet ajout et le commit `203c633` ont été produits par l’autre session, pendant la présente revue. Les interventions ci-dessous sont rapportées par elle ; notre agent d’audit ne les a pas exécutées ni vérifiées à distance. La transcription a été relue jusqu’à L21043 et les huit nouveaux messages U115–U122 sont intégrés au registre et au catalogue.

- **GitLab pc4 :** dernier rapport à 11:11Z, encore 502. Le diagnostic de cette session attribue le redémarrage en boucle de `gitlab-postgresql-0` (postgres:17.11) à un démarrage dépassant la sonde (30 essais × 10 s) ; `docker-entrypoint.sh` consommerait 100 % CPU. Elle rapporte avoir recréé le pod sur son volume puis patché `StatefulSet/gitlab-postgresql`, `startupProbe.failureThreshold` de **30 à 240** (tolérance théorique de 5 à 40 min), et recréé webservice/sidekiq. Un surveillant attendait 30 min. **Retour du service et intégrité de la base non démontrés.** Si reprise du diagnostic autorisée : processus, journaux et volume en lecture seule d’abord ; ne supprimer aucun PVC/namespace, ne pas recommencer ces opérations en boucle à partir de la note.
- **Garage :** `garage-0` en CrashLoop, SQLite annoncé corrompu (`/var/lib/garage/meta/db.sqlite`). La session dit ne pas l’avoir réparé ; sauvegarde avant toute intervention. Aucun succès de réparation ou de restauration n’est prouvé. **Sauvegarde GitLab complète et restauration d’essai restent manquantes**, même si des miroirs/bundles du code existent. Aucun formatage pc4.
- **Codex/Muse :** U117/U118 confient la vérification/réparation à Muse Spark 1.3 Contributor max. L’autre session signale des recommandations erronées sur le catalogue (modèles/effort max) et un modèle proposé inadéquat ; ne pas les appliquer aveuglément. Les modèles autorisés doivent être vérifiés dans le catalogue local de la prochaine session. **`approval_policy` et `sandbox_mode` sont les choix du fondateur : ne pas les modifier.** `gitlab-nexora` est déclaré fonctionnel dans cette autre session, mais cela ne démontre pas son exposition dans chaque session Codex ni la visibilité de tous les projets. OAuth `GitLab-PC4` reste annoncé à refaire par le fondateur.
- **Actions depuis pc6 :** `bash ~/Desktop/nexora-actions-pc6.sh` existe ; à la date de cette note, l’autre session les dit non faites (OAuth, CPU pc1/pc6). Les confirmations U104/U106 concernaient les commandes antérieures pc3/pc4, pas ce nouveau script. Vérifier les résultats étape par étape : son « Terminé » seul ne suffit pas.
- **API Anthropic :** proposition d’utiliser 200 $ et script `~/Desktop/claude-avec-cle-api.sh` rapportés. U119 demande s’il peut transmettre une clé par courriel, U120 s’inquiète du coût, puis U121 dit « **Ok oublions cela** ». Cette piste est **mise de côté**, aucune clé à récupérer/lire/créer, aucune facturation API à configurer. L’exigence d’économie reste ; les tarifs et estimations de la conversation ne sont pas des prix actuels vérifiés.
- **Décision finale U122 (11:13:01Z) :** tout confier à Codex et mettre la reprise à jour avant la nouvelle conversation. Le prompt et le rapport sont maintenant présents ; ne pas relancer la revue à partir de l’ancienne indication « s’ils sont absents ». Cette passation inclut la fin ajoutée pendant son audit.
- **Correction de portée Git :** la phrase de l’autre session « aucun travail récent sur les dépôts » est trop générale : plusieurs commits sont déjà connus des refs distantes locales. L’instantané de la revue distingue les seuls commits documentaires locaux, les diffs Director/Finish et les branches déjà référencées. `203c633` s’ajoute localement à `a854130` sur `docs/passation-maj` ; aucun fetch/push réussi ne permet de garantir le serveur actuel.

Priorité de reprise : diagnostic réseau/GitLab et sauvegarde avec preuve de restauration, accès complet Codex, synchronisation des seuls changements prêts, puis films/Mesh/Director/Finish et vérifications produit. La présente tâche reste une revue documentaire sans changement de production.

### Blocage final du commit documentaire

Le montage en lecture seule de `/home/pc6/Desktop/Nexora Creative/.git` empêche le commit de cette revue ; aucune tentative de contournement ou d’élévation. Les fichiers sont présents et synchronisés. Script prêt et vérifié syntaxiquement : `~/Desktop/nexora-commiter-passation.sh`, copie durable `docs/passation/commiter-passation.sh`. La prochaine session doit confirmer le commit avec le trailer `Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>` avant de considérer la synchronisation Git achevée. `203c633` reste le dernier commit constaté ; il ne contient pas toutes les corrections finales de cette revue.

Dernier complément consulté : L21049, autre assistant à11:17:23UTC ; notification ancienne seulement, pas de nouveau message du fondateur. Il rapporte encore502 et un surveillant en attente. Le corpus fondateur reste101messages et le résultat distant reste non vérifié par notre revue.


## 17. Reprise Codex — 04/11/2026, 06 h 26 Montréal

- Réseau SSH depuis pc6 fonctionnel vers pc1, pc3, pc4, pc5, VM202 et VM204. GitLab répond HTTP 502 au MCP `gitlab-nexora` (`GET /user`), donc identité/visibilité des projets et pipeline non vérifiables ; aucun push. OAuth `GitLab-PC4` indiqué `Unknown` par `codex mcp list`, état non prouvé.
- Lecture seule pc4 : PostgreSQL présent mais non prêt, Garage en `CrashLoopBackOff` (21 redémarrages au relevé), webservice et sidekiq en initialisation ; volumes GitLab affichés `Bound`. Aucun diagnostic d'intégrité des données par cette lecture. Aucun redémarrage ou réparation. Sauvegarde complète et restauration d'essai toujours non prouvées ; ne pas formater.
- Files ComfyUI locales 37188 et tunnel 37288 : zéro tâche active/en attente au relevé ; cela ne démontre pas les files de tous les autres moteurs. pc1 5090 : 475/600 W ; pc3 5080 : 288/360 W ; VM204 : 2080 SUPER 200/250 W et 2070 SUPER 172/215 W. pc4 : deux limites AMD lisibles 240/330 W et 152/190 W ; troisième lecture occupée. pc3 et pc5 : `intel_pstate` 87 %. pc4 : fréquence maximale 4 928 619/5 665 080 (~87 %). pc1 : fréquence maximale 5 756 452/5 756 452 (100 %), unité de limite inactive. pc6 : unité active, fréquence maximale 2 442 960/2 808 000 (~87 %) ; GPU GB10 plafond non exposé par nvidia-smi. Fréquence CPU ne mesure pas une baisse de watts.
- Disques : pc6 racine 99 % (17 Gio libres), Storage 646 Gio libres ; pc1 racine 97 % (33 Gio libres), Infrastructure 251 Gio libres ; VM204 94 % (3,7 Gio libres). Site LAN HTTP 200, WorkStudio LAN 307 ; VM202 service Creative et ses deux tunnels `active`, parcours applicatif non vérifié. pc3 interrogation k3s locale échouée (absence de contexte), état du pod non établi.
- Les diffs non commités Director et Finish sont toujours présents et intacts au contrôle `git status`. Films : HANDOFF relus comme historiques ; aucune relance ni suppression. Les archives et infographies restent à vérifier.
- `nexora-commiter-passation.sh` relu puis exécuté par Codex : commit local **80f2dde** avec trailer demandé, aucun push. La limitation `.git` en lecture seule de la revue précédente ne s'applique plus ici. Le script `nexora-actions-pc6.sh` a été relu, mais pas lancé : il combine OAuth et deux interventions système, sans arrêt sur erreur ; l'unité pc6 est déjà active et le CPU pc1 reste à vérifier/corriger par la voie appropriée après diagnostic.

### Films — 06 h 28 Montréal

Le dossier V7 DeepSeek préexistant (« La doublure » : 23 images clés, 23 plans, 3 voix, 3 musiques) a été copié depuis les données persistantes, avec `DOSSIER.md`, `dossier.json`, `fabrique.py` et `textes.json`, dans le worktree film ; les originaux sont conservés. Validation `python3 -B .../chaine/v7.py valider deepseek` : OK, deux avertissements de mentions trop longues en FR et EN. Commit local **3634d83** sur `feat/film-v6-creative` ; aucun push à cause du 502, pas de rendu ni d'acceptation humaine. La file GPU et la puissance doivent être contrôlées avant toute reprise de génération.

V100 : plafond mesuré 240/300 W et utilisation 0 %.

### Contrôles complémentaires — 06 h 31 Montréal

- Site VM201 HTTP 200, Creative VM202 port 3162 HTTP 200, WorkStudio VM203 HTTP 307 depuis pc5 ; pas de parcours connecté ni test visuel. Sur pc1, `INVENTAIRE.csv` contient 1 705 entrées hors en-tête, et 105 MP4 sous `opsys-ultime` ; couverture des infographies et vérification des sommes restent à faire. Stockage GitLab `/srv/gitlab-data` : 1,8 T disponibles affichés ; cela ne prouve pas une sauvegarde complète. PostgreSQL totalisait 5 redémarrages et Garage 22 au deuxième relevé.
- Mesh : synthèse des recherches et bancs existants, 10 cas d'usage et prochaines preuves dans `/media/pc6/Storage/Nexora/travail/relief-29/SYNTHESE-REPRISE-CODEX.md` (hors Git, aucun nouveau banc). Le renommage et rapport final restent à intégrer et vérifier.
- Director : six fichiers de tests ciblés, **80/80 passent** ; aucun changement au worktree. Toutefois la règle non commitée impose live-action à toutes les demandes, même si le client veut un style d'animation : incompatibilité potentielle avec la polyvalence du produit, à corriger avant intégration ; tests verts ne prouvent ni ce cas ni qualité visuelle. Banc 12 briefs réels non exécuté.
- Finish : 14/14 tests TypeScript ciblés passent ; test Python non exécuté car FastAPI absent des deux interpréteurs locaux essayés. Aucune mesure nouvelle NVENC, aucun service ni production modifié ; le rapport 30 reste à finir.
- pc1 : sudo non interactif indisponible ; CPU au plafond complet au contrôle. Ne pas lancer en bloc le script regroupé pendant le 502 : il retenterait aussi OAuth et pc6, et n'arrête pas ses étapes sur erreur.

### Suites du diagnostic — 06 h 32 Montréal

- VM204 : les deux ComfyUI écoutent sur l'adresse LAN, pas sur 127.0.0.1 ; services actifs, files 8188 et 8189 chacune à 0 actif/0 attente. Le service audio est actif. Le premier essai localhost refusé ne signifiait pas une panne.
- Inventaire pc1 : 1 705 entrées dont 1 553 MP4, 17 MOV, 11 WebM, 28 fichiers audio et 96 sans extension ; 101 lignes ont une raison de non-copie. Aucune extension d'image n'apparaît dans le champ de chemin de cet inventaire : archivage des infographies non établi, il faut rechercher et inventorier les images ailleurs sans les supprimer. Les entrées non copiées demandent rapprochement.
- Script ciblé pour le fondateur `/home/pc6/Desktop/nexora-cpu-pc1-codex.sh` : préparé, `bash -n` réussi, non exécuté ; il installe l'unité existante avec `GPU_SKIP=1`, demande éventuellement sudo pc1 et affiche fréquences/GPU. À confirmer par une nouvelle mesure après exécution. Il ne lance ni OAuth ni changement CPU sur pc6.

### Conservation des médias — 06 h 37 Montréal

- L'inventaire pc1 contenait cinq lignes de 16 colonnes à cause de virgules non citées dans la description. Correction ciblée : les 1 705 entrées sont conservées ; original conservé sur pc1 sous `INVENTAIRE.avant-correction-codex-20261104.csv`. Vérification du CSV après correction. Les raisons de non-copie concernent majoritairement des références et actifs tiers ; ne pas les compter automatiquement comme des créations perdues.
- Recensement ciblé des dossiers marketing Creative, OPSYS et données persistantes V7/OPSYS : 725 contenus uniques, 104 déjà présents sur pc1 et vérifiés par SHA-256. Les 621 autres sont copiés dans `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/codex-reprise-20261104-c/` : 42 MP4, 256 JPG, 274 PNG, 29 SVG et 20 PDF ; chaque copie a été vérifiée SHA-256 puis ajoutée à `INVENTAIRE.csv` avec ses sources. Inventaire final : **2 326 entrées**, 15 colonnes chacune. `MANIFESTE.json` dans l'archive et inventaires détaillés sous `/media/pc6/Storage/Nexora/travail/inventaires/`. Les sources sont conservées.
- Deux tentatives de transfert initiales ont échoué avant copie de média (erreur d'itération tar), laissant chacune un dossier contenant son seul manifeste : `codex-reprise-20261104` et `codex-reprise-20261104-b`. Ils n'ont pas été supprimés. La troisième a abouti et les 621 fichiers ont été vérifiés ; ces deux dossiers ne sont pas des archives complètes.
- Ce recensement couvre seulement les racines indiquées dans le manifeste, sans suivre les liens symboliques : il ne démontre pas que toutes les créations de toutes les machines et de toutes les époques ont été retrouvées. Poursuivre la recherche des infographies et vidéos manquantes et les inscrire.

### Finish — test Python isolé

Le test local était bloqué faute de FastAPI, mais l'environnement existant `/srv/nexora-gpu/venv-audio` de la VM204 dispose des dépendances. Les deux fichiers de test/code ont été copiés dans un dossier temporaire `nexora-encoder-test-codex.*` sur cette VM ; exécution avec environnement vide et données/jeton fictifs : **9 tests Python sur 9 passent**. Aucun service, secret réel, GPU ou configuration de production utilisé/modifié. Combiné aux **14 tests TypeScript sur 14**, cela ne démontre ni la qualité NVENC sur de vrais clips, ni un déploiement, ni la validation de l'export complet. Le dossier temporaire étiqueté reste à inventorier/nettoyer selon les règles applicables.


## 18. Décision du fondateur — 04/11/2026, reprise Codex

- **CPU pc1 : le fondateur choisit de ne pas appliquer de limite.** Cela remplace toutes les indications précédentes proposant de la lui demander ; ne pas lancer le script groupé historique `nexora-actions-pc6.sh` (qui installerait cette limite). Le script ciblé `nexora-cpu-pc1-codex.sh` a été neutralisé sans exécution et n'effectue aucune modification. Le plafond GPU 5090 mesuré à 475 W reste distinct.
- Le fondateur demande d'utiliser activement et à volonté **DeepSeek V4.1 Flash 1017**, **Muse Spark 1.3 Contributor** et **Gemini 4 Argon Flex, effort moyen à élevé** ; les deux premiers au maximum comme convenu. Il demande aussi **trois sous-agents GPT-6 Luna effort max**. Codex coordonne et vérifie leurs résultats ; aucune clé ni fichier de secret ne doit être lu ou affiché. Trois agents Luna ont été lancés sur Director, Finish et films ; leur résultat doit être contrôlé avant intégration.

### Accès aux modèles économiques

La passerelle locale répond sur son point de santé, mais `/v1/models` répond 401 sans authentification. Le lanceur `outils/sous-agents/sous-agent.sh` appelle `sa_master_key` et peut lancer `gateway.sh`, lequel lit les clés fournisseurs. Ces scripts n'ont pas été exécutés par Codex parce que le fondateur a interdit **toute lecture de secret** ; aucun appel DeepSeek/Muse/Gemini n'est encore prouvé dans cette reprise. Chercher une interface déjà authentifiée qui n'expose ni ne lit de clé dans le processus de travail ; à défaut, signaler le blocage plutôt que prétendre avoir délégué. Trois sous-agents GPT-6 Luna max sont réellement lancés.

### Conservation médias — deuxième vague

Racines supplémentaires : `Nexora Creative/marketing`, `NexoraSite/web/public`, `~/nexora-creative-data/promo` ; fichiers médias réguliers, sans suivre les liens symboliques. Sur 1 806 contenus uniques, 412 déjà archivés ont été revérifiés par SHA-256 ; **1 394 nouveaux** ont été copiés et vérifiés : 389 MP4, 9 MOV, 156 JPG, 607 PNG, 70 SVG, 163 PDF. Chaque fichier a une ligne avec sources dans `INVENTAIRE.csv` ; total vérifié **3 720 entrées**, toutes à 15 colonnes.

Pour ménager la racine pc1, cette vague est physiquement dans `/run/media/pc1/Infrastructure/NexoraStudioWork/ArchivesNexora/codex-reprise-vague2-20261104/` et accessible depuis `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/codex-reprise-vague2-20261104` par lien symbolique ; `MANIFESTE.json` et les inventaires sous `/media/pc6/Storage/Nexora/travail/inventaires/` donnent les sources et empreintes. Après copie : Infrastructure 244 Gio libres, racine pc1 33 Gio libres. Aucune source supprimée. Toute la production historique et les autres machines restent à rechercher : ne pas qualifier l'archive d'exhaustive.

### Creative et GitLab — contrôles complémentaires

- `/api/nexora/etat` sur la VM202 répond et déclare H3, Qwen-Image 2.1, Music3, un moteur de détourage configuré et le mode 3D. Cette réponse décrit la configuration détectée ; elle ne prouve pas un détourage ou une transcription de bout en bout après la panne.
- Nouvelle lecture GitLab : HTTP 502 ; PostgreSQL 7 redémarrages, non prêt, Garage 24 redémarrages, non prêt. Aucune réparation ni suppression de volume. Les copies des deux vagues de médias ont été rapprochées de leurs manifestes et de l'inventaire pc1 : 621/621 et 1 394/1 394 présentes et inscrites.

### GitLab : sonde PostgreSQL non propagée

À 06 h 45 Montréal, diagnostic en lecture seule : le StatefulSet `gitlab-postgresql` est bien configuré avec `startupProbe.failureThreshold=240`, période 10 s, génération 4 observée. **Mais le pod effectif utilise encore 30 × 10 s**, ancienne révision `gitlab-postgresql-bbc96b578`, alors que la révision désirée est `gitlab-postgresql-5cd6988b69` (stratégie RollingUpdate). Le réglage à 240 existe donc mais n'est pas appliqué au pod observé. PostgreSQL non prêt, 8 redémarrages ; événements Unhealthy/Killing ; Garage `CrashLoopBackOff`, 25 redémarrages ; GitLab encore 502. pc4 disposait d'environ 40 Gio de mémoire disponible et de swap libre à ce relevé. La cause complète, la corruption Garage et l'intégrité de la base ne sont pas établies par ces seuls éléments. Aucun pod, volume ou service modifié ; sauvegarde complète/restauration toujours manquantes.

### Tests produit ciblés

Sur le worktree Director basé sur `da27fa4`, exécution Vitest sous environnement vide des tests `auth`, `credits`, `studio` et `transcriptionGpu` : **30/30 passent** (4 fichiers). Les collaborateurs réseau et les jetons utilisés dans les tests sont fictifs ; ceci n'est ni une vérification de bout en bout dans la VM, ni une preuve de débit réel ou d'isolation complète du Studio.

### Complément de mesure AMD

Les deux limites lisibles sur pc4 sont **240/300 W par défaut** et **152/190 W par défaut**, soit 80 % chacune (le 330 W cité plus haut était le maximum autorisé de la première carte, pas son réglage d'usine par défaut). Les deux cartes lues étaient à 0 % d'activité au relevé ; une troisième carte restait occupée/illisible, plafond et activité non établis. Ne pas déduire de cette lecture que toutes les cartes AMD sont limitées.

### Banc Finish retrouvé et médias conservés

Sur VM204, `/srv/nexora-gpu/essais-sortie/` contient trois sources MKV, 12 encodages MP4 et `resultats-gpu.json`, ainsi que les scripts de banc. Les 15 vidéos (340 Mio) n'étaient pas dans l'inventaire vérifié : copie sur pc1 SSD Infrastructure, accessible par `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/codex-banc-finish-vm204-20261104/`, chacune vérifiée SHA-256 et inscrite. `INVENTAIRE.csv` contient désormais **3 735 entrées** ; sources VM204 conservées. Les mesures et leur comparabilité sont en cours de revue par l'agent Finish : aucune conclusion de qualité ni activation NVENC déduite de la présence de fichiers.

### Films et Finish : constats des agents

- OPSYS DeepSeek : sept plans du long (`p26` à `p32`) sont absents, soit environ 39,2 s ; le court manque `p26`. Le montage actuel peut remplacer un plan absent par un fond sombre sans échec explicite : ne pas interpréter un export comme film complet. Vertical : six sources dédiées absentes et repli à vérifier. Les voix et une musique référencées existent. Agent films chargé de corriger les contrôles et d'ajouter des tests sans GPU ; aucun brouillon vide lancé. Les scripts automatiques mélangent rendus, appels modèles et commit/push : ne pas les lancer aveuglément.
- Finish : 12 encodages NVENC sur trois clips retrouvés (H.264 et HEVC 10 bits, p4/p7, 12 s, 24 i/s). Les tailles et débits concordent avec le JSON mais dépassent les cibles annoncées ; SSIM comparés à la source ne prouvent pas l'équivalence face à x264. Aucun résultat de comparaison à débit égal retrouvé ; les scripts VM et les copies locales ont des empreintes différentes, sans manifeste liant le JSON aux scripts/sources. Les mesures sont donc partielles ; garder les deux codecs désactivés jusqu'au banc concluant.

### Finish : six comparaisons à débit égal, CPU isolé

Sur pc6, sources et six sorties NVENC p7 copiées depuis VM204 et contrôlées SHA-256 ; six sorties x264 medium deux passes ont été créées sur Storage, avec deux threads CPU et aucun GPU. Débits mesurés à ±0,41 % des vidéos NVENC. SSIM en yuv420p, images synchronisées par index à 24 i/s :

| Clip | H.264 NVENC / x264 | HEVC 10 bits NVENC / x264 |
|---|---:|---:|
| action | 0,992998 / 0,993582 | 0,992477 / 0,993391 |
| bureau | 0,965466 / 0,971140 | 0,965511 / 0,970249 |
| espace | 0,992070 / 0,993554 | 0,991942 / 0,993412 |

FFmpeg 7.0.2 arm64 statique ; sources 12 s, vidéo seule ; H.264 x264 deux passes sur pc6 contre résultats NVENC existants VM204 : ne pas comparer les temps comme s'il s'agissait de la même machine ni extrapoler au HDR/422/audio. Le SSIM seul ne prouve ni qualité perçue équivalente ni export complet. Sur `action-h264-p7`, le même fichier et FFmpeg donnent 0,948635 avec l'ancien alignement PTS et 0,992998 avec alignement par index : l'ancien JSON mesurait différemment. Résultats, empreintes et sorties sous `/media/pc6/Storage/Nexora/travail/finish-banc-egalite-codex-20261104/`, script dans le répertoire `work` de cette conversation. Les six nouveaux MP4 ont été archivés sur le SSD Infrastructure de pc1 et inscrits dans l'inventaire, désormais **3 741 entrées** ; sources conservées. Codecs non activés : revue visuelle et validation produit restent à faire.

### Finish : tranche locale commitée

Commit **e29ca2a** sur `feat/sortie-video-nvenc` : client/point d'encodage bornés, authentification, partage du verrou GPU avec la transcription et repli CPU ; H.264 et HEVC restent désactivés par défaut. Agent : 14 tests TS, 12 tests Python avec faux encodeurs, typecheck verts ; Codex a relancé indépendamment les 14 tests TS sur le commit (verts). Pas de déploiement ni push ; validation visuelle, temps des routes VM202 et intégration réelle encore ouverts. Dans son worktree, `docs/JOURNAL.md`, `docs/PASSATION-AGENTS.md`, `work/` et `recherche/30-annexes/recalculer_ssim.py` demeurent non commités et préservés ; leurs copies de passation sont anciennes et ne doivent pas écraser ce maître. Les trois sources et leurs quatre sorties p7/x264 respectives contiennent chacune 288 images : contrôle du banc à débit égal.

### Director : tranches locales commitées

Commits **35e680a** puis **adc14a8** sur `feat/realisateur-live-action` : recette photo conditionnelle aux promotions/produits ou aux demandes photo, respect des styles visuels explicitement demandés, modes H3 et langues pris en compte. La revue Codex a trouvé un faux positif pour « anime cette photo » ; il est corrigé par le deuxième commit. Agent : suite complète 452 tests et typecheck verts sur le premier commit ; après correction, 60 tests ciblés verts, relancés indépendamment par Codex. Worktree propre, aucun push ni déploiement. Le banc LLM des 12 briefs et les mesures de rendu ne sont pas exécutés ; la recherche 26 reste sur la branche film, absente ici. Les tests ne sont pas une preuve de qualité vidéo acceptée.

### Reprise OPSYS DeepSeek

Commit local **4b4ae82** sur `feat/opsys-ultime` : le montage refuse explicitement les plans vidéo absents au lieu de les remplacer silencieusement par de l'encre. Cinq tests ciblés passent, relancés indépendamment ; l'exception verticale `p02v → p02` est préservée, aucune correspondance `v01–v06` inventée. Le commit initial de l'agent `169d4d4` a été corrigé localement avant tout push pour inclure le trailer demandé ; `equipes/essai` non suivi reste intact.

Après contrôle des prérequis et de la file vide, un seul rendu a été lancé : OPSYS DeepSeek `p26` sur 5090, `--max-file 1`, avec environnement vide et sans appel LLM. Au relevé : 1 tâche active, aucune attente, GPU 100 %, 474,88 W pour plafond 475 W. **En cours : résultat et archivage non encore attestés**. Les autres plans restent à reprendre un par un après vérification. Aucun service redémarré.

### OPSYS DeepSeek : premier plan repris

`p26-r1.mp4` rendu en 158,8 s de moteur, sans erreur rapportée ; fichier effectivement présent, H.264 1344×768, AAC, 5,166688 s. Vidéo et planche de cinq images ont été copiées sur le SSD Infrastructure de pc1, contrôlées par SHA-256 et ajoutées à l'inventaire (**3 743 entrées**). La planche montre bien une maison et un anneau lumineux demandés ; l'image est sombre, l'évaluation du mouvement et du son reste à faire, aucune note humaine ni acceptation. Originaux conservés.

Après contrôle des références, de la voix et de la file vide, **p27** a été lancé seul (`--max-file 1`) ; il est en cours, sans résultat encore attesté. Poursuivre un plan à la fois, vérifier puis archiver chaque sortie et tout essai, sans utiliser les scripts automatiques qui poussent ou appellent des fournisseurs.

### OPSYS : contrôle du montage après p26

Validation réelle des sources du dossier DeepSeek, sans rendu : le **court** a ses plans, voix référencées et musique ; le long manque `p27–p32` pendant que `p27` tourne ; le vertical manque toujours `v01–v06`. Le garde-fou refuse bien les absents. Toutefois `monter.py` supprime actuellement le répertoire de tranches MP4 après assemblage et utilise une sortie écrasable. **Ne pas lancer le montage tant que ces comportements ne sont pas corrigés** : l'agent films prépare un correctif pour conserver les segments et éviter l'écrasement.

### OPSYS DeepSeek : p27

`p27-r1.mp4` rendu en 139,8 s de moteur, sans erreur rapportée ; fichier présent, H.264 1344×768, AAC, 5,166688 s. Vidéo et planche de cinq images archivées sur pc1 et vérifiées SHA-256 ; inventaire à **3 745 entrées**. La planche montre un homme près d'une camionnette ; voix, lèvres, mouvement et qualité finale restent à écouter et regarder. Les sources sont gardées. Après vérification de la file vide et du plafond à 475 W, `p28` a été lancé seul ; son résultat reste en attente.

### OPSYS DeepSeek : p28

`p28-r1.mp4` rendu en 162,5 s de moteur ; H.264 1344×768, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1 et vérifiées SHA-256 ; inventaire à **3 747 entrées**. La planche montre l'adjointe dans un bureau ; qualité du jeu, synchro labiale et voix non jugées sur les images fixes. p26 et p27 ont aussi été décodés entièrement sans erreur. Après file vide et plafond 475 W confirmés, `p29` a été lancé seul ; résultat en attente.

### Finish : aperçu visuel limité

Codex a comparé des recadrages 640×360 de la source et des quatre variantes p7/x264, sur une image par clip : bureau et espace à 5 s, action à 2,5 s. Pas de différence flagrante à l'échelle de l'aperçu, mais une image fixe ne démontre pas une qualité équivalente en mouvement ni un verdict humain. L'essai initial action à 5 s tombait sur une image noire et est conservé aussi. Les quatre planches PNG ont été archivées sur pc1 et vérifiées ; inventaire **3 751 entrées**. Codecs toujours désactivés en attente des autres validations.

### OPSYS DeepSeek : p29

`p29-r1.mp4` rendu en 138,3 s de moteur ; H.264 1344×768, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1 et vérifiées SHA-256 ; inventaire **3 753 entrées**. La planche montre le représentant devant une maison avec téléphone ; son et mouvement restent à juger. Après file vide et plafond 475 W confirmés, `p30` (plan plus long) a été lancé seul ; résultat en attente.

### OPSYS : conservation des tranches et brouillon court

Commit local **65acfe4** sur `feat/opsys-ultime` : conservation des tranches MP4 et du mix dans un dossier unique étiqueté ; refus d'écraser l'export existant, y compris symlink, et `ffmpeg -n`. Sept tests ciblés passent, relancés indépendamment ; `equipes/essai` non suivi préservé. Aucun push.

Après validation réelle de l'EditPlan court DeepSeek (`ok: true`, 13,5 s), présence des plans, voix et musique, et contrôle qu'aucun export du même nom n'existe, le brouillon court a été lancé en CPU (`--jobs 1`, affinité deux cœurs, priorité basse), en parallèle du seul plan GPU p30. Il est **en cours** : ne pas déclarer le film complet, ni supprimer les tranches ; à la fin, vérifier et archiver chaque MP4 ainsi que le film et leurs planches sur pc1.

### OPSYS DeepSeek : brouillon court produit

Le brouillon `~/nexora-creative-data/work/opsys-ultime/deepseek/montage/deepseek-court-brouillon.mp4` a été rendu en 50,4 s CPU après validation de l'EditPlan (13,5 s, 7 plans, aucune source manquante). `ffprobe` confirme H.264 960×540, AAC, 13,5 s ; décodage intégral sans erreur. Neuf tranches MP4, le mix WAV, l'export et une planche ont été copiés sur le SSD Infrastructure de pc1, vérifiés SHA-256 et inscrits dans l'inventaire (**3 765 entrées**), via le dossier du Bureau `codex-opsys-deepseek-court-brouillon-20261104`. Tous les originaux et tranches restent sur Storage.

Inspection de la planche uniquement : représentant/maison, signal, serveurs et carton sont présents ; plusieurs images sont sombres. Le rythme, la voix, le son, le mouvement et la qualité globale ne sont pas encore évalués. C'est un **brouillon interne**, pas une finale ni une note fondateur. `p30` du long est toujours en cours à cet instant.

### Finish : protocole consolidé

Commit local **9c223cb** sur `feat/sortie-video-nvenc` : rapport 30, JSON des six paires et protocole portable, avec empreintes, 288 images, divergence d'alignement PTS et limites de l'aperçu fixe. Contrôle indépendant : SHA du JSON commité identique à la mesure sur Storage ; syntaxe Python valide. Le script portable n'a pas été relancé et ne prouve pas, à lui seul, la reproductibilité. Codecs toujours désactivés ; aucun push ni déploiement.

### OPSYS DeepSeek : p30

`p30-r1.mp4` rendu en 400,9 s de moteur ; H.264 1344×768, AAC, 10,125 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1 et vérifiées SHA-256 ; inventaire **3 767 entrées**. La planche montre un immeuble puis un bureau ; lisibilité en mouvement, son et rendu final restent à juger. Après file vide et plafond 475 W confirmés, `p31` a été lancé seul ; résultat en attente.


## 19. GitLab revenu partiellement — 04/11/2026, 07 h 30 Montréal

- L'API répond de nouveau ; PostgreSQL, webservice et sidekiq sont prêts. Garage demeure non prêt avec 34 redémarrages au relevé. La santé complète, les objets stockés et une restauration ne sont pas prouvés. Aucune réparation de notre part.
- Identité du connecteur `gitlab-nexora` : compte de service admin `agent-nexora-workstudio-web`. En listant sans le filtre de membre, il voit notamment `root/nexora-creative`, `root/nexora-web`, `root/nexora-plateforme`, `root/nexora-workstudio`, `root/opsys-ai`, `root/voltafabric`, `root/nexora-code-agent`, `nexora/nexora-code`, `root/gitspace-forgejo` et `root/nvdriver-v100-update` (ce dernier vide). Les essais `root/gitspace` et `root/nv-driver-update` renvoient 404 : mauvais chemins ou invisibles ; les chemins précités existent. Cette visibilité n'établit pas les droits du fondateur. `GitLab-PC4` est `Not logged in` ; commande séparée donnée au fondateur pour OAuth, sans exécuter le script groupé qui appliquerait une limite CPU pc1 refusée.
- État serveur consulté : `developpement` = **a682a1d**, avec fusion Mesh nommée dans son titre ; vérifier contenu et pipeline avant déclaration de déploiement. `feat/film-v6-creative` contient déjà **3634d83**. Une autre session a poussé la branche passation jusqu'à **5141f84**, commit vide de relance CI de Claude, enfant de notre `d735d7d` ; ce commit est déjà ancêtre de notre branche locale actuelle, donc préservé sans merge ni réécriture. MR documentaire **!37** ouverte ; OPSYS **!27** brouillon. Ne pas écraser ce travail concurrent.
- Pipeline documentaire **2841 en échec** (gitleaks, semgrep, trivy `script_failure`), relance **2847 en attente** ; pas de cause affirmée sans preuve. Le connecteur montre aussi des pipelines en attente. Aucun push ou fusion supplémentaire entrepris par cette session tant que l'erreur CI/stockage n'est pas clarifiée ; ne pas conclure que le pipeline est vert. Les travaux locaux plus récents restent à synchroniser sans force une fois la situation vérifiée.

### PostgreSQL : nouvelle révision appliquée

Contrôle après le retour API : le pod PostgreSQL est maintenant prêt, utilise bien la révision désirée `gitlab-postgresql-5cd6988b69` et la sonde à **240**. L'ancien relevé à 30 concernait le pod précédent ; aucune recréation n'a été effectuée par cette session. Garage reste en échec, donc la reprise complète de GitLab et les sauvegardes ne sont pas établies.

### OPSYS DeepSeek : p31

`p31-r1.mp4` rendu en 313,1 s de moteur ; H.264 1344×768, AAC, 8,708333 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1 et vérifiées SHA-256 ; inventaire **3 769 entrées**. La planche montre une tour ; sa dernière case noire est un remplissage de la grille (4 images disponibles pour 5 cases), pas une preuve d'image noire dans le film. Son et mouvement restent à juger. Pendant le calcul, une lecture instantanée a affiché 487,83 W malgré une consigne nvidia-smi de 475 W ; aucune modification de réglage n'a été faite. Après file vide et limite configurée 475 W confirmées, `p32` a été lancé seul ; résultat en attente.

### OPSYS DeepSeek : p32 et brouillon long

`p32-r1.mp4` est présent, H.264 1344×768 et AAC, 5,166688 s ; décodage complet sans erreur. La durée de calcul et le code de sortie du processus ne sont plus disponibles : ne pas les inventer. La vidéo et sa planche sont archivées sur pc1 avec vérification SHA-256 ; inventaire à **3 771 entrées**. Son et mouvement ne sont pas évalués.

Les 32 plans du montage long DeepSeek, ses voix référencées et sa musique sont présents ; validation EditPlan `ok: true`, 140,46 s, aucune source vidéo manquante, sortie libre. Un brouillon long a été lancé en CPU, deux cœurs et un seul job ; son résultat et son archivage restent à vérifier. Tous les essais et tranches sont à conserver. Ce n’est pas une finale ni un verdict humain.

### OPSYS : contrôle des quatre dossiers

Contrôle des fichiers référencés dans les plans : DeepSeek, Gemini, Muse et Opus disposent chacun des sources vidéo, voix référencées et musique pour leurs versions longues et courtes. Pour le vertical, Gemini et Opus ont leurs sources référencées ; DeepSeek manque toujours `v01` à `v06`. Le champ `montage.vertical` de Muse est `null` et la construction de contexte lève `AttributeError` ; aucun vertical Muse utilisable n’est démontré. La présence de fichiers ne prouve ni leur qualité ni une validation des quatre films.

Contrôle GitLab renouvelé : pipeline 2847 toujours en attente ; Garage toujours non prêt, 36 redémarrages. OAuth personnel GitLab-PC4 encore déconnecté. Aucune modification de production.

### OPSYS DeepSeek : reprise verticale

Les six plans `v01` à `v06` sont bien définis dans le dossier DeepSeek en 9:16, avec références, voix éventuelles et premières images requises présentes au contrôle. Ils sont distincts des plans horizontaux. Après contrôle de file GPU vide et limite configurée 475 W (25,24 W au repos), `v01` a été lancé seul ; résultat, décodage et archive restent à vérifier. Le brouillon long CPU reste en cours.

### OPSYS DeepSeek : v01

`v01-r1.mp4` généré en 139,2 s moteur sans erreur signalée ; H.264 768×1344, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1 et SHA-256 vérifiés ; inventaire **3 773 entrées**. La planche montre un travailleur utilisant son téléphone près d’une maison ; son, mouvement et qualité finale ne sont pas jugés. Après file vide et limite 475 W confirmées, `v02` a été lancé seul.

Sur le brouillon court, une détection automatique n’a trouvé aucun passage noir continu d’au moins 0,5 s avec seuil de pixels 0,05 ; cela ne vérifie ni narration ni qualité visuelle.

### OPSYS Muse : origine du vertical absent

Diagnostic documentaire d’un sous-agent, complété par vérification du texte source : le HANDOFF rapporte une décision commune des quatre équipes de recadrer le 16:9 pour le vertical à cause de la file GPU ; le dossier Muse évoque ce recadrage si la file ne permet pas de 9:16 natif. Ce sont des indications d’équipe, **pas une décision attribuable au fondateur**. Le dossier actuel ne contient aucun montage vertical Muse défini, et les prises retrouvées sont horizontales. Le recadrage reste à concevoir et vérifier ; ne pas le déclarer livré. DeepSeek possède séparément six spécifications 9:16 propres.

### OPSYS DeepSeek : v02

`v02-r1.mp4` généré en 138,1 s moteur sans erreur signalée ; H.264 768×1344, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1, SHA-256 vérifiés ; inventaire **3 775 entrées**. La planche montre le signal montant depuis le téléphone ; son et mouvement restent à juger. Après file vide et limite 475 W confirmées, `v03` a été lancé seul.

### OPSYS DeepSeek : brouillon long produit

Le brouillon `~/nexora-creative-data/work/opsys-ultime/deepseek/montage/deepseek-long-brouillon.mp4` a été rendu en 491,6 s CPU : 32 plans, EditPlan validé sans avertissement, aucune source manquante. `ffprobe` indique H.264 960×540, AAC, 140,458333 s ; décodage intégral sans erreur. L’export, 94 tranches MP4, le mix WAV et une planche, soit 97 médias, ont été copiés sur le SSD Infrastructure de pc1, vérifiés SHA-256 et inscrits dans l’inventaire (**3 872 entrées**), dossier du Bureau `codex-opsys-deepseek-long-brouillon-20261104`. Originaux, liste des tranches et fichiers de travail préservés.

Contrôle de la planche uniquement : maisons, bureaux, signal et personnage numérique visibles ; plusieurs scènes sont sombres. La dernière case noire de la grille est un remplissage : 14 images pour 15 cases, pas une preuve de noir dans la vidéo. Ce brouillon ne valide ni mouvement, ni son, ni lisibilité, ni la note humaine ≥9/10. `v03` vertical reste en cours.

### OPSYS DeepSeek : v03 et contrôle automatique du long

`v03-r1.mp4` généré en 118,4 s moteur sans erreur signalée ; H.264 768×1344, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1, SHA-256 vérifiés ; inventaire **3 874 entrées**. La planche montre le signal longeant une route enneigée ; son et mouvement restent à juger. Après file vide et limite 475 W confirmées, `v04` a été lancé seul.

Sur le brouillon long, un contrôle automatique n’a trouvé aucun passage noir continu ≥0,5 s au seuil de pixels 0,05 ; volume moyen mesuré −15,7 dB et pic −1,5 dB. Ces mesures ne démontrent ni intelligibilité, ni mixage satisfaisant, ni qualité cinématographique.

### pc6 : espace racine critique

`df` affiche maintenant la racine à **100 %**, environ **5,1 Gio disponibles** ; deux mesures espacées sont presque stables, mais la cause de la baisse depuis le précédent relevé n’est pas établie. Inodes à 28 %. Le montage OPSYS utilise le répertoire réel sur Storage (environ 120 Mio) et les planches aussi ; aucune attribution de la baisse ne peut être faite à partir de ces chiffres. Aucune suppression ou nettoyage automatique : caches, journaux et données sont conservés. Terminer la vérification et l’archivage de v04 déjà lancé, puis suspendre les nouveaux rendus jusqu’à disposer d’une marge fiable sur la racine.

### OPSYS DeepSeek : v04, pause de génération

`v04-r1.mp4` généré en 141,0 s moteur sans erreur signalée ; H.264 768×1344, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1, SHA-256 vérifiés ; inventaire **3 876 entrées**. La planche montre un serveur puis une façade de bureaux ; son et mouvement restent à juger. Les plans verticaux `v05` et `v06` restent à générer lorsque la marge disque racine pc6 sera rétablie ; aucun autre rendu lancé.

### Consigne du fondateur : répartition du stockage

Le fondateur demande d’utiliser le SSD externe **Storage de pc6** ainsi que les espaces **Bureau et Infrastructure de pc1**. Relevé de montage : Storage pc6 `/media/pc6/Storage`, ~645 Gio libres ; Infrastructure pc1 `/run/media/pc1/Infrastructure`, ~244 Gio libres ; le dossier `/home/pc1/Bureau` est sur le système de fichiers racine de pc1, ~33 Gio libres. Les dossiers d’archives visibles au Bureau peuvent pointer par lien symbolique vers Infrastructure : ne pas confondre leur emplacement visible avec le disque physique. Privilégier Storage et Infrastructure pour les gros volumes, conserver un inventaire et vérifier les copies. Ne pas déplacer ni supprimer des données existantes sans preuve de conservation.

### Confirmation du fondateur : ambition technologique Creative

Le fondateur confirme que la reprise couvre bien Mesh, la synchronisation labiale, LTX 2.5, le détourage, Wan 2.2 sur pc4 ainsi que l’approfondissement, le peaufinage et l’optimisation de toutes les technologies de Nexora Creative mentionnées dans la passation, pour viser une technologie de pointe. Il ne limite pas le mandat aux films. Réutiliser les résultats existants, mener les recherches et essais nécessaires, comparer objectivement, intégrer et vérifier les parcours réels. Statut à ce point : synthèse Mesh hors Git réalisée ; Wan 2.2 avait des bancs historiques pc4, raccordement non prouvé ; LTX 2.5 historiquement présent pc3 ; détourage historiquement déployé pc3, parcours complet non revérifié ; comparaison lipsync et intégration restent à prouver. Ne pas confondre mandat général, proposition technique et fonctionnalité livrée.

### Nexora Sync : rapport persistant retrouvé

Le rapport `pc1:/run/media/pc1/Infrastructure/NexoraStudioWork/lipsync/RAPPORT-LIPSYNC.md` et ses entrées/sorties existent. Il rapporte des mesures CPU SyncNet sur H3 natif ancré : LSE-C 5,83 et 5,06, LSE-D 8,48 et 9,15 pour deux personnages distincts. Les témoins de voix remplacée ont été mesurés sur d’autres personnages et dialogues ; ils ne démontrent pas une comparaison équitable de modèles. MuseTalk 1.5 et LatentSync 1.6 sont préparés, mais **aucun redoublage GPU comparatif n’a été réalisé** lors de cette veille ; ne pas inventer vitesse, VRAM ou gagnant. Les deux environnements déclarent sm_120 ; l’inférence complète 5090 reste à vérifier. À reprendre avec les mêmes clips et voix, en protégeant la file partagée, dès que la marge disque est sûre.

### Quatre équipes OPSYS : copie sur le disque Bureau de pc1

Dix brouillons et essais existants ont été copiés depuis Storage sur le disque contenant le Bureau de pc1 : longs et courts des quatre équipes, ainsi que deux essais musicaux Opus. Dossier physique `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/codex-opsys-quatre-equipes-brouillons-bureau-20261104/`, 202 Mio, confirmé sur `/dev/nvme2n1p2` et non lien symbolique ; chaque fichier vérifié SHA-256, inventaire global **3 886 entrées**. Les originaux et autres archives sont conservés.

État confirmé par relevé documentaire d’un sous-agent : Gemini/Muse/Opus ont leurs brouillons long et court 16:9 ; aucun export vertical retrouvé dans les trois dossiers de montage consultés. Les dossiers Gemini et Opus définissent des montages verticaux à partir de sources résolubles, dont des replis de recadrage explicitement codés pour Opus ; Muse ne définit pas encore le sien. Présence des fichiers et propositions d’équipe ne constituent ni validation qualité ni décision du fondateur.

### pc6 : diagnostic de l’occupation, sans nettoyage

Relevé de métadonnées d’un sous-agent : caches locaux environ 25 Gio, dont uv 7,1, Hugging Face 6,5 et ingestion pc5 5,4 ; journaux système environ 4 Gio et cache APT environ 1,1 Gio. Plusieurs gros fichiers de caches ont des dates du 3 novembre : ils expliquent une partie de l’occupation, **pas nécessairement la baisse observée pendant cette reprise**. La cause de cette baisse n’est pas démontrée. Aucun contenu de secret lu, aucune suppression, migration ou modification de production. Rechercher une libération de marge sûre et vérifiée sans retirer les médias ni perturber les services.

### Détourage et LTX 2.5 : preuves historiques précisées

Le journal Creative rapporte un banc pc3 du rapide SAM 3.1 + ViTMatte : 224 images en 120 s (0,54 s/image) en pod, sur clips définis ; il ne prouve pas le parcours utilisateur complet après la panne. LTX 2.5 Alpha-Gen a été préparé et essayé sur RTX 5080 pc3 : 25 images en 18–20 s après chargement, 97 images en 88,3 s, VRAM 15,3–16,1 Gio et RAM système pic 29,2 Gio sur 30. Sur scènes synthétiques guidées, meilleur résultat rapporté pour le verre mais moins bon pour fourrure/fumée que le rapide. Ces mesures historiques ne suffisent ni à valider des vrais plans ni à déclarer le mode pro raccordé à Creative. Le pod pro était à zéro réplica dans le document ; état courant et intégration restent à vérifier en lecture seule.

## 20. Objectif actif et R&D triple A — 04/11/2026

Le fondateur active explicitement l’objectif de reprise intégrale Nexora et demande une R&D profonde de niveau triple A pour Creative et toutes les technologies : rechercher littérature scientifique, arXiv, dépôts GitHub/GitLab et autres sources primaires ; réutiliser et combiner des projets open source mûrs, puis les améliorer et vérifier sans négliger les détails utiles. Qualité, simplicité, FR/EN, preuves de bout en bout et critères de films restent inchangés.

Le fondateur demande d’utiliser librement DeepSeek V4.1 Flash 1017 max et Muse Spark 1.3 Contributor max, Gemini 4 Argon Flex effort moyen à élevé selon la tâche, et trois sous-agents GPT-6 Luna max. Après la question explicite sur la passerelle, son « OK » autorise sa lecture technique de la clé de passerelle en interne, **sans affichage ni exposition** ; cela ne permet pas de lire ou afficher les autres clés, fichiers .env réels, mots de passe ou courriels. Les appels réellement réalisés doivent être prouvés, sans déclarer une délégation supposée. Les décisions du fondateur restent distinctes des recommandations d’agents.

### Première utilisation de la passerelle autorisée

Lecture interne de la seule clé de passerelle, sans affichage ni argument contenant sa valeur : le catalogue authentifié déclare `eco-deepseek`, `eco-muse`, `eco-gemini` et `eco-gemini-eleve`. Trois requêtes de réflexion ont été lancées via la passerelle déjà active, sans lecture de clé fournisseur : `eco-gemini-eleve` a renvoyé une réponse textuelle sauvegardée sur Storage, possiblement tronquée (limite de 2 200 jetons atteinte) ; ses suggestions sont à vérifier. Sa proposition de stopper les processus workers ou vider des caches est **rejetée pour les GPU partagés** : aucune intervention sur un processus tiers ou service de production. `eco-deepseek` et `eco-muse` ont répondu sans texte avec cette limite ; nouveaux essais à plafond de sortie plus large en cours, sans prétendre à une réponse.

### pc6 : espace libéré sur demande du fondateur

Le fondateur demande de libérer pc6 en déplaçant sur Storage ce qui ne sert pas. L’ancien environnement expérimental `work/voix2-modeles/sgl-gb10` (9,3 Gio) et son `uv-cache` (~9,9 Gio) ont été copiés sur `/media/pc6/Storage/Nexora/travail/relocalisation-pc6-20261104/`, avec conservation de leurs chemins par liens symboliques. Aucun fichier `.env` réel ou clé privée identifié dans ces deux arbres ; aucun contenu de secret lu. Aucune utilisation ouverte détectée avant bascule. Deux vérifications rsync par checksum avant/après bascule ont donné zéro différence ; Python 3.12.3 et Torch 2.14.1 importent depuis l’ancien chemin. Les copies temporaires sur racine ont été retirées seulement après ces vérifications, comme nécessaire au déplacement.

Le premier transfert seul n’avait presque rien libéré, car des données étaient encore liées au cache. Après déplacement du cache, l’espace disponible est passé de 5 431 083 008 à 16 015 564 800 octets, soit **environ 9,86 Gio récupérés** ; racine à 99 %, ~15 Gio libres, Storage ~626 Gio libres. Garder cette marge sous surveillance et les originaux des médias intacts.

### pc6 : montages promotionnels déplacés et archives vérifiées

Le dossier historique `~/nexora-creative-data/promo/montage` (~3,4 Gio) ne présentait aucun fichier ouvert ni modification récente à notre relevé. Ses 128 médias ont **128 empreintes distinctes et 128 copies pc1 effectivement relues et vérifiées SHA-256**. Dossier complet copié sur Storage dans `relocalisation-pc6-20261104/montage`, comparé deux fois par checksum sans différence, puis chemin initial préservé par lien symbolique ; ancienne copie racine retirée après contrôle et sans toucher aux archives pc1.

Après les deux déplacements, racine pc6 **98 %**, 19 592 982 528 octets disponibles (~18,2 Gio), soit environ **13,2 Gio libérés** depuis 5 431 083 008 octets ; Storage ~623 Gio libres. Tous les médias, essais et chemins sont conservés. Ne pas considérer cette marge comme infinie ; vérifier avant les opérations volumineuses.

### Délégation effective et reprise du vertical OPSYS

Les trois profils de passerelle ont maintenant fourni des réponses textuelles : `eco-muse` (2343 jetons de sortie) et `eco-deepseek` (7364 ; deux essais antérieurs sans texte car plafond atteint) proposent des grilles de contrôle ; `eco-gemini-eleve` a fourni la réponse partielle déjà signalée. Les trois sont sous `Storage/Nexora/travail/rnd-codex-20261104/modeles/` et ne constituent ni preuves empiriques ni décisions fondateur. Les seuils proposés par Muse ne sont pas adoptés automatiquement. Les agents Luna mènent en parallèle trois recherches sourcées sur Mesh, Sync et détourage/Wan.

Après récupération d’environ 13,2 Gio sur pc6, et après contrôle d’une file GPU vide et du plafond 475 W configuré, le plan OPSYS DeepSeek `v05` a été lancé seul. Au contrôle précédant le lancement, la 5090 avait seulement 1 784 Mio libres malgré 0 % d’activité ; les modèles déjà chargés restent intacts et aucun processus tiers n’a été touché. Le résultat et son archive restent à vérifier.

### Premiers dossiers R&D sourcés — résultats non confondus avec des livraisons

Quatre notes de recherche existent hors Git dans `/media/pc6/Storage/Nexora/travail/rnd-codex-20261104/` : `mesh.md`, `sync.md`, `detourage-video.md` (trois agents Luna) et `montage-evaluation.md` (Codex). Elles comparent les preuves locales aux sources primaires et proposent des expériences vérifiables. Contrôles indépendants des références : PVSync arXiv 2610.09223, SUPRA-Tex 2610.22352, MatAnyone 2 2512.11782 et FilmBench 2607.24241 existent ; les performances publiées par les auteurs ne sont pas des résultats Nexora.

Pistes : comparer Sync sur les mêmes clips FR-CA/EN-CA avec jugement humain ; rapprocher des modèles Mesh par entrées et sorties réellement comparables ; tester les mattes sur vrais plans ainsi que la stabilité ; étudier l’échange EditPlan/OpenTimelineIO et une évaluation cinématographique sans prétendre à un adaptateur livré. Le projet PVSync illustre les limites d’un score de synchronisation seul ; son code et ses données sont annoncés ultérieurement dans l’article, donc non exécutés ici. Aucune recommandation d’agent ne devient décision du fondateur.

### OPSYS DeepSeek : v05

`v05-r1.mp4` généré en 118,1 s moteur sans erreur signalée ; H.264 768×1344, AAC, 5,166688 s, décodage intégral sans erreur. Vidéo et planche archivées sur pc1, empreintes SHA-256 vérifiées ; inventaire **3 888 entrées**. La planche montre une façade de bureaux ; son et mouvement restent à juger. Après file GPU vide et limite 475 W confirmées, `v06` a été lancé seul ; résultat et archive restent à vérifier. La racine pc6 affiche ~17 Gio libres au nouveau relevé, moins que les ~19 Gio affichés juste après les déplacements : surveiller, cause de la baisse non établie.

### Détourage : disponibilité exacte, correctif local

Défaut reproduit par test : si un moteur pro est déclaré, `/capacites` annonçait `disponible: true` alors que le lancement pro refusait toujours, et les erreurs attribuaient sans preuve l’indisponibilité aux poids. Correctif sur worktree séparé Storage, branche `fix/detourage-disponibilite-codex`, commit local **5d27dc6** : capacité pro déclarée indisponible, création pro refusée avant dépôt et message honnête ; palier rapide inchangé. Les quatre fichiers de base comparés à GitLab `developpement` avaient les mêmes identifiants de contenu au relevé, mais le worktree part d’une référence d’intégration locale antérieure : à réconcilier avec la branche distante avant MR. Test de régression vu échouer avant correctif ; **23 tests ciblés** et `npm run typecheck` passent après. Aucun push, pipeline, déploiement ou test utilisateur réel ; GitLab reste en erreur partielle.

### OPSYS DeepSeek : v06 et vertical en montage

`v06-r1.mp4` généré en 129,4 s moteur sans erreur signalée ; H.264 768×1344, AAC, 5,166688 s, décodage complet sans erreur. Vidéo et planche archivées sur pc1, SHA-256 vérifiés ; inventaire **3 890 entrées**. Les six plans verticaux sont présents. EditPlan vertical validé, 14,5 s, six plans, aucune source ou voix manquante, musique présente et sortie libre ; brouillon CPU sur deux cœurs lancé, résultat et archive en attente. Le film final et son verdict humain restent à faire.

### OPSYS DeepSeek : brouillon vertical produit

Le brouillon `~/nexora-creative-data/work/opsys-ultime/deepseek/montage/deepseek-vertical-brouillon.mp4` a été rendu en 52,7 s CPU : six plans, EditPlan validé, aucune source manquante. `ffprobe` indique H.264 540×960, AAC, 14,5 s ; décodage intégral sans erreur. Export, dix tranches MP4, mix WAV et planche : 13 médias copiés sur pc1, vérifiés SHA-256, inventaire **3 903 entrées**. Les originaux sont conservés.

La planche montre le travailleur, le signal, le serveur et le retour à la maison ; une image est très sombre. La dernière case noire est un remplissage de grille, pas une preuve de noir dans la vidéo. Son, mouvement, lisibilité mobile et verdict humain ≥9/10 restent à examiner ; ce n’est pas une finale.

### Mesh : contrôle structurel complémentaire

Un analyseur Python standard a vérifié entêtes GLB 2, longueurs de blocs, JSON et indices d’accesseurs pour **34 fichiers** existants : 20 Step1X AMD, 3 Pixal AMD BF16, 7 TRELLIS GB10 et 4 Hunyuan forme, tous analysables selon ce contrôle limité. Textures déclarées : respectivement **0/20, 3/3, 7/7 et 0/4** ; aucune image externe déclarée dans ce lot. Résultats détaillés `Storage/Nexora/travail/rnd-codex-20261104/mesh-inventaire-structure-glb-20261104.json`. Pas de rendu, de contrôle de topologie complet ni de classement qualité ; jeux et matériels diffèrent.

### R&D voix, films et sauvegarde ; cohérence des montages

Trois nouvelles notes d’agents Luna sur Storage : `voix-doublage.md` (mesures locales, sources et protocole d’écoute FR-CA/EN-CA, sans validation d’accent), `films-qualite.md` (mesures, sources et protocole de visionnement humain) et `fiabilite-backup.md` (sauvegarde GitLab et restauration isolée à préparer). Le coordinateur y a ajouté la copie Git de 278 fichiers/13,14 Go relevée dans les annexes : elle reste insuffisante pour une restauration GitLab complète. Garage était toujours `CrashLoopBackOff`, 44 redémarrages au dernier relevé ; pipeline 2847 en attente.

Comparaison indépendante du plan actuel à `ffprobe` : Gemini long 112,000 s contre 105,583 s rendu ; Muse long 90,458 s contre 109,708 s ; Muse court 14,500 s contre 14,000 s. Des révisions différentes peuvent expliquer les écarts : la provenance exacte reste à établir avant tout remplacement ou verdict. DeepSeek long, court et vertical correspondent chacun à leur durée prévue ; Opus long/court aussi. Aucune note créative attribuée.

Une revue de code supplémentaire par DeepSeek n’a pas abouti (délai réseau dépassé) ; une réponse DeepSeek antérieure a bien été reçue. Un essai de sous-agent Muse avec outils isolés est en cours, en passant par un relais privé qui garde la clé de passerelle hors du sous-agent ; résultat non encore établi.

### OPSYS : indice de provenance des montages existants

Lecture ciblée des champs non secrets du journal persistant de montage : le long Gemini a été enregistré à **20 plans / 105,58 s**, le long Muse à **20 plans / 109,71 s**, durées concordant aux fichiers à l’arrondi ; les plans actuels en comptent **24 et 19**. Le court Muse est inscrit à **6 plans / 14,0 s**, contre **6 plans / 14,5 s** dans le plan actuel. Ceci appuie un changement de plan ou de version de calcul depuis l’export, sans identifier la révision exacte : aucun hash historique n’est attesté par ces champs. Tous les brouillons restent préservés ; ne pas les écraser ni juger la fidélité au plan actuel comme une erreur certaine.

### Agent Muse outillé isolé : essai incomplet

Un lanceur dérivé de celui du dépôt a été essayé avec un relais Unix privé : seule la passerelle/relais lit la clé autorisée en mémoire ; l’agent ne reçoit qu’une valeur factice et travaille dans un dossier isolé sur Storage, sans réseau direct ni accès au domicile. La passerelle existante n’a pas été redémarrée et aucune clé fournisseur n’a été lue. Muse a effectué 3 requêtes et utilisé ses outils Bash/Read, mais l’exécution a atteint son délai de 240 s (`FAIL:timeout`, coût journalisé 0,00170 $) sans produire la revue demandée. Ne pas prétendre que la revue est terminée. Le dossier d’exécution est conservé pour diagnostic ; les réponses textuelles précédentes de Muse restent distinctes de cet essai outillé.

### Détourage réel : configuration et disponibilité incohérentes

Contrôle GET en lecture seule depuis pc5 vers Creative VM202 : `/api/nexora/etat` indique `detourage: true`, mais `/api/nexora/detourage/capacites` répond HTTP 200 avec `rapide.disponible: false`, aucun moteur rapide déclaré et pro indisponible. Depuis VM202, le serveur historique pc3 `192.168.1.126:8231/sante` répond **401 sans jeton** : réseau/service HTTP joignables, santé authentifiée et rendu réel non prouvés. Aucun secret ou configuration réelle consulté.

Les sources déployées `index.ts`, `engine.ts` et la route de détourage d’origine correspondent par hash aux sources consultées. Le premier état vérifie simplement la présence d’une URL ; la route rapide exige en plus une recette `detourage-rapide` ou `*`. Les deux réponses indiquent donc qu’une URL de détourage est déclarée mais qu’aucun moteur actuellement listé ne satisfait ce filtre de recette. Identifier prudemment le bon raccordement et vérifier authentification/santé avant toute correction ; aucune modification de production.

La relecture indépendante du commit `5d27dc6` a aussi trouvé qu’un ancien travail rattaché à un moteur uniquement pro pouvait contourner le refus via `lancer` ou `reprendre` en demandant rapide. Régression reproduite : 502 au lieu de 503 avec moteur fictif non joignable. Correctif local supplémentaire en cours de vérification, qui contrôle la capacité rapide du moteur lié au travail sans bloquer un moteur déclarant à la fois rapide et pro ; aucun déploiement.

### Détourage : anciens travaux protégés

Deux commits locaux complémentaires à `5d27dc6` : **826b604** contrôle que le moteur enregistré sur un ancien travail accepte bien le rapide avant lancement ou reprise ; un moteur déclaré rapide et pro reste accepté pour le rapide. **575e5cd** refuse aussi une reprise dont les paramètres historiques déclarent explicitement `palier: pro`, même sur moteur mixte. Les deux cas ont été reproduits en échec avant correction ; **24 tests ciblés** et `npm run typecheck` passent après. Les très anciens registres ne stockant pas le palier ne permettent pas de distinguer avec certitude un ancien pro d’un rapide sur un moteur mixte ; aucun lancement pro historique par la route bloquée n’a été démontré. Aucun push, pipeline ni déploiement.

### Détourage : promesse visuelle corrigée localement

Le relevé indépendant a retrouvé une phrase d’interface promettant « sans scintillement », alors que les mesures historiques montrent une réduction et non l’absence d’artefacts. Commit local **c3dbee0** sur le worktree de détourage : formulation factuelle « avec stabilisation des contours ». Correction de texte vérifiée par `git diff --check`, pas de test d’interface ni de déploiement. L’interface de détourage reste majoritairement française : la couverture FR/EN demeure un chantier distinct, non livrée.

### Détourage réel : recettes actuellement annoncées

GET en lecture seule `/api/nexora/moteurs-gpu` depuis pc5 : les quatre moteurs Creative déclarent des recettes d’image, musique, 3D ou H3, mais **aucun ne déclare `detourage-rapide` ni `*`**. Combiné au code déployé vérifié par hash et aux deux réponses d’état, cela explique le refus de sélection du moteur rapide malgré une URL de détourage déclarée. Le moteur SAM pc3 répond HTTP 401 sans jeton depuis VM202 : réseau présent, authentification et traitement réels non testés. Aucune configuration réelle, valeur de secret ou mot de passe n’a été lu ; aucun service modifié ou redémarré. Étudier une correction vérifiée sur branche ou de configuration après le diagnostic, sans supposer que l’URL suffit à prouver le bon modèle.

### Détourage : état général aligné localement

Commit local **74959b0** sur le même worktree : le booléen `detourage` de `/api/nexora/etat` utilise désormais le même sélecteur de recette rapide que `/capacites` au lieu de signaler toute URL comme disponible. Ceci décrit une **configuration sélectionnable**, pas une vérification de santé : `/capacites` reste nécessaire pour cette dernière. Le test couvre une URL déclarée avec recette sans détourage ; **24 tests ciblés** et typecheck passent. Cette correction ne raccorde pas le moteur manquant. Le `index.ts` distant a un identifiant de contenu différent de notre base locale ; réconciliation attentive indispensable avant MR. Aucun push ni production modifiée.

### Agent DeepSeek outillé isolé : premier essai incomplet

Le même relais privé a permis une exécution DeepSeek outillée : six requêtes, six appels Bash, puis limite de tours atteinte (`FAIL:error_max_turns`, 0,00472 $ journalisé), sans fichier de revue final. Traces et éventuels essais synthétiques conservés ; ne pas déclarer la revue achevée. Un second essai borné est lancé avec consigne de conclure plus directement ; pas de clé réelle visible dans l’agent et aucun accès aux autres projets.

### OPSYS : empreintes de provenance testées sur un vrai montage

Sur `feat/opsys-ultime`, commits locaux **7585b81** et **9f8f13f** : les futurs montages enregistrent SHA-256 du plan, de son annexe, des sources vidéo/voix/musique résolues et de l’export ; les sources manquantes sont indiquées et une modification constatée après rendu empêche l’attestation. Les workers reçoivent le même instantané de plan et de sources. La couverture est **partielle** : polices, logo/marque, code, dépendances, environnement et modification transitoire suivie de restauration restent hors attestation. Les 14 tests ciblés ont été relancés indépendamment avec succès.

Essai réel sur copie distincte du vertical DeepSeek : 14,5 s, six plans, rendu CPU 52,6 s, H.264 540×960/AAC, décodage complet sans erreur. Plan, annexe, sept sources et empreinte export ont été vérifiés indépendamment ; une entrée de journal correspondante. Export, dix tranches, mix et planche archivés sur pc1 et SHA vérifiés, inventaire **3 916 entrées** ; détails de provenance copiés et vérifiés sur Storage et pc1. C’est un essai technique préservé, pas un nouveau verdict humain ni une preuve de couverture complète. Aucun push ni pipeline.

### Revue Mesh par sous-agent DeepSeek outillé

Second essai isolé DeepSeek : **OK**, six requêtes, sept tours, 76 s, coût journalisé 0,00518 $ ; revue `Storage/Nexora/travail/rnd-codex-20261104/agents/deepseek-revue-glb/revue.md`. La clé réelle est restée dans le relais, pas dans le sous-agent. Il signale les limites du compteur GLB : modes strips/fans non comptés, nombre d’indices non multiple de trois tronqué, textures déclarées sans preuve de validité. Vérification indépendante du lot : **34 primitives mode 4, aucun compte non multiple de trois, aucune URI data à casse atypique** ; les mesures déclarées de ce lot restent valables dans les limites déjà indiquées. Aucun classement qualitatif.

### Viewer : actions audio non fonctionnelles masquées localement

Un audit a confirmé que `Speak` sur une image et `Add sound` sur une vidéo dirigeaient toutes deux vers `/speak`, redirigé vers un autre outil en perdant l’élément choisi. Sur le worktree distinct `Storage/Nexora/travail/fix-viewer-speak-codex-20261104`, branche `fix/viewer-speak-button-codex`, commits locaux **bef6071** et **6359dbc** : ces deux actions trompeuses sont masquées ; le code dormant est conservé. Transpilation et vérification TypeScript complète passent ; pas de test navigateur, push ou déploiement. Le Viewer distant diffère globalement de la base locale bien que les lignes concernées aient été retrouvées identiques : réconciliation avant MR.

Autre défaut relevé : la redirection de `Extend`/transition perd l’identifiant du clip ; correctif local séparé en cours. D’autres actions renvoient à `/apps` et demandent un examen avant de les qualifier.

### Sous-agent Muse outillé : seconde tentative terminée

Une seconde tâche isolée Muse a produit `agents/muse-controle-detourage/controle.md` sur Storage : cinq propositions de vérification, 5 requêtes, 6 tours, 45 s, 0,00124 $ journalisé ; aucune clé réelle accessible à l’agent. Relecture du coordinateur : priorité pratique au raccordement rapide avant le pro non intégré ; contrôle des recettes au runtime plutôt que dans le seul dépôt ; ne pas promettre une absence absolue de scintillement. Ces corrections sont ajoutées à la note ; aucun test GPU n’a été effectué par cet agent.

### Gemini Flex élevé : revue outillée de la provenance

Après les tâches outillées DeepSeek et Muse, un agent `gemini-eleve` est lancé dans le même dispositif isolé, pour relire une copie du montage et ses empreintes de provenance. Dossier et traces sur Storage ; clé de passerelle conservée uniquement dans le relais, pas dans l’agent ; aucune clé fournisseur lue. Résultat en attente, à vérifier indépendamment.

### OPSYS : concordance avec les premiers dossiers Git

Un agent Luna a comparé les dossiers Git, calcul relancé indépendamment : pour Gemini long, `9303394` contient **20 plans / 105,583 s**, contre **24 / 112 s** à `d728c65` ; pour Muse long, `9303394` contient **20 / 109,708 s**, contre **19 / 90,458 s** à `2b3e075` ; le court Muse est **6 / 14 s** puis **6 / 14,5 s**. Les premiers chiffres correspondent aux anciennes entrées de montage et aux fichiers. C’est une forte concordance avec les dossiers initiaux parmi les versions examinées, pas une preuve cryptographique de la révision exacte : aucun hash historique du plan n’a été trouvé. Pas de rendu ni remplacement.

### Gemini Flex élevé outillé : revue de provenance

La revue isolée `agents/gemini-revue-provenance/revue.md` sur Storage est terminée : 6 requêtes, 6 tours, 92 s, 0,05258 $ journalisé. La clé réelle est restée dans le relais. Gemini signale notamment qu’une source vidéo absente de `plan.sources` pourrait échapper au garde-fou et être rendue en encre, et qu’un rapport de validation `ok:false` semble ne pas arrêter le montage. Ces points sont soumis à reproduction et correction par un agent Luna ; aucune proposition n’est automatiquement acceptée. La suggestion de supprimer ou remplacer un export échoué ne doit pas contrevenir à la conservation de tous les essais ni à la protection contre l’écrasement.

### Viewer : clip conservé lors de la redirection Prolonger

Commit local **0200277** dans le worktree Viewer : les liens `/extend` conservent `take` en allant vers `/prolonger`, y compris `mode=transition` traduit en `mode=raccord`; sans identifiant les destinations restent celles d’origine. Quatre tests ciblés et le typecheck complet ont été relancés indépendamment avec succès. Pas de test navigateur ni déploiement ; réconcilier la branche avec le `developpement` serveur plus récent avant MR.

### Mesh : premier essai réel de décimation CPU

Sur la chaise Pixal BF16 déjà produite, avec `decimerGlb` du code Creative local et cible 50 000 triangles : **149 898 → 49 996 triangles**, **8 177 296 → 4 940 320 octets**, fonction 0,31 s sur deux cœurs pour cet essai (hors lecture initiale/analyses). Les cartes de couleur et métal/rugosité détectées ont des SHA-256 identiques. Le contrôle topologique local rapporte arêtes ouvertes 549 → 539, arêtes non-variété 96 → 111, 11 composantes et zéro triangle dégénéré avant/après ; aucun des deux n’est étanche selon ce contrôle. Original préservé ; GLB et deux mesures copiés sur pc1, SHA vérifiés, inventaire **3 919 entrées**.

Un objet, aucun rendu ou verdict visuel : résultat prometteur pour la taille, mais l’augmentation des arêtes non-variété interdit de conclure à une amélioration générale ou d’activer ce réglage automatiquement. Mesures et limites sur Storage `rnd-codex-20261104/mesh-essai-decimation/` et note `mesh.md`.

### OPSYS : garde-fous après revue Gemini

Commit local **71499dd** : un plan vidéo sans source résolue et une voix sans identifiant valide sont refusés ; un rapport du validateur explicitement `ok:false` arrête le rendu ; les nouveaux journaux indiquent le mode brouillon et la résolution. Les quatre lacunes ont été reproduites avant correction ; **18 tests ciblés** relancés indépendamment passent. Limites : si le validateur est absent et retourne `None`, la validation n’est pas démontrée ; les exports échoués restent conservés sans faux succès ; ABA reste explicitement hors attestation.

Un nouvel essai CPU étiqueté du vertical DeepSeek tourne avec un nom différent pour vérifier ces derniers changements sur un vrai montage ; résultat et archivage en attente. Tous les essais précédents sont conservés.

### Détourage : contrôle de santé explicite

Un test réseau local simulé a montré que `/capacites` annonçait le rapide disponible même si `/sante` répondait HTTP 200 avec `{}` ou `ok:false`. Le serveur de détourage documenté renvoie `ok:true` en santé. Commit local **2ba45b0** : disponibilité vraie seulement avec `ok:true`, tandis qu’un moteur déclaré mais refusant ou renvoyant une réponse incomplète reste identifié comme indisponible. Régression observée avant correction ; **25 tests ciblés** et typecheck passent. Cela ne remplace pas un vrai parcours connecté, ne rajoute pas la recette manquante et n’est pas déployé.

### OPSYS : garde-fous vérifiés sur un vrai montage

Après `71499dd`, nouvel essai distinct du vertical DeepSeek : 14,5 s, six plans, validation `ok:true`, 52,3 s CPU ; décodage intégral sans erreur. Le journal indique correctement `brouillon:true`, 540×960, empreintes et couverture partielle ; SHA de l’export vérifié indépendamment. Film, dix tranches, mix et planche copiés sur pc1 et SHA vérifiés ; détails de provenance aussi copiés, inventaire **3 932 entrées**. Cet essai a la même empreinte export que l’essai précédent, sans conclure à un déterminisme général. Aucun verdict humain attribué.

### Mesh : collision d’arêtes corrigée localement

La clé numérique historique `a × 2^32 + b` pouvait confondre des arêtes distinctes au-delà d’environ **2,1 millions de sommets soudés**, ce qui peut fausser les arêtes ouvertes/non-variété, l’étanchéité et le volume. Collision reproduite et confirmée par un agent indépendant ; elle ne touche pas la chaise Pixal à 94 612 sommets. Commit local **bfafe59** sur `fix/mesh-aretes-codex` : clé exacte calculée selon le nombre de sommets, repli BigInt au-delà du seuil sûr. Test initial en échec puis **12 tests** et typecheck réussis ; revue mathématique indépendante et comparaison sur la chaise réelle : mêmes métriques, trois temps comparables, sans preuve de gain de vitesse. La branche et les fichiers distants diffèrent globalement : réconcilier avant MR ; aucun push/déploiement.

Autres limites identifiées, non corrigées : fusion des positions arrondies à 1e-5, volume signé ambigu pour plusieurs coquilles, instancing GLB et exports multi-matériaux non pleinement pris en compte. Leur portée et leurs cas d’utilisation demandent des tests spécifiques ; ne pas généraliser l’essai Pixal à tous les modèles.

### Reprise Codex — Viewer et volume Mesh, 4 novembre 2026

- Viewer : commit local `368ae95` dans `fix/viewer-speak-button-codex` : masquage de cinq actions Restyle, Add effect et Stage dont les routes redirigent vers Apps et perdent la prise. Les pages et fonctions restent présentes. Typecheck et contrôle du diff réussis; pas de test navigateur ni déploiement. Les extraits retirés correspondent à GitLab, mais le ref local est en retard : réconciliation indispensable avant MR. Les autres actions n’ont pas été auditées exhaustivement.
- Mesh : reproduction en mémoire de deux tétraèdres fermés séparés : orientations identiques, volume 1/3; seconde orientation inversée, volume 0 malgré deux composantes étanches. Une cavité orientée inversement demande au contraire une soustraction : sommer les volumes absolus serait incorrect. Correctif prudent en cours, aucun résultat de volume matériel à promettre avant validation.
- Stockage vérifié : racine pc6 16 Gio libres (99 %), Storage 623 Gio libres. Les déplacements déjà documentés ont préservé les chemins et les fichiers; aucune nouvelle suppression.

### Reprise Codex — validation des films, 4 novembre 2026

- Commit local `94da540` sur `feat/opsys-ultime` : export final refusé si le validateur est indisponible; brouillon possible avec `validation:null`; rapports mal formés ou `ok:false` refusés. 21 tests ciblés repassés indépendamment. Le vrai validateur a accepté DeepSeek vertical (14,5 s) et Muse long (90,458 s, deux avertissements); il refuse Gemini long : `c23` demande à `p19` les images 36–132 alors que la source déclare 124 images. Diagnostic de la source et des autres versions en cours; aucun montage relancé ni plan modifié. Revue indépendante du contrat en cours.
- Bilan espace : l'inventaire a identifié de volumineux travaux OPSYS et des qualifications dont l'usage et les dépendances restent à établir; conservés en place.

### Reprise Codex — volume Mesh ambigu, 4 novembre 2026

- Commit local `25b2824`, branche `fix/mesh-aretes-codex` : pour plusieurs composantes fermées, volume `null` et avertissement au lieu d'un chiffre pouvant être faux; le cas simple reste inchangé. 13 tests ciblés repassés indépendamment, typecheck réussi par l'agent; pas de déploiement. Distinguer les solides séparés des cavités demandera une classification géométrique. L'étanchéité actuelle ne démontre ni orientation cohérente ni absence d'auto-intersections; vérification complémentaire en cours. Réconciliation avec GitLab nécessaire avant MR.

### Reprise Codex — contrôles indépendants, 4 novembre 2026

- Montage `94da540` : revue indépendante du contrat TypeScript et du pont Python sans incompatibilité réelle trouvée; les 21 tests ciblés ont été relancés. Une réponse fabriquée `ok:true` de durée 0 ou supérieure à 180 s passerait le garde Python, mais le validateur officiel ne produit pas ces cas réussis.
- Mesh : un tétraèdre fermé translaté, avec une face inversée, reste déclaré étanche alors que son volume calculé peut valoir 5/6 ou 13/6 au lieu de 1/6. Garde supplémentaire en cours, sans prétendre détecter les auto-intersections.
- GitLab pc4, lecture seule : pod `garage-0` non prêt, `CrashLoopBackOff`, 59 redémarrages observés. Pas de diagnostic de perte de données, pas de redémarrage ni de push.

### Reprise Codex — orientation Mesh et plan Gemini, 4 novembre 2026

- Commit local `a35a2d7` : détection d'orientation incohérente par arête, volume `null` et avertissement; l'étanchéité reste un constat topologique. Les 14 tests ciblés ont été repassés indépendamment; typecheck réussi par l'agent. Cela ne détecte pas les auto-intersections; une formulation UI plus prudente est en cours. Revue indépendante et réconciliation GitLab nécessaires.
- Films : le fichier retenu Gemini p19 contient effectivement 124 images à 24 i/s. Son plan c23 demande 96 images depuis l'image 36, jusqu'à la borne exclusive 132 : dépassement de 8 images confirmé. Les 11 plans existants des quatre équipes ont été vérifiés avec le vrai validateur; seul Gemini long échoue. Les options préservent l'ancien plan et les exports; aucune modification encore faite.

### Reprise Codex — plan Gemini corrigé et affichage Mesh, 4 novembre 2026

- Films : commit local `9e90859` : Gemini long `c23.entree_f` 36→28, sans changement de durée ni vitesse. Les 11 EditPlans présents passent désormais le vrai validateur; Muse vertical est absent, Muse long et court gardent respectivement 2 et 12 avertissements. Seule la durée média réelle de Gemini p19 a été vérifiée contre le fichier; ailleurs, le validateur utilise les durées déclarées. Ancien EditPlan Gemini long conservé sous Storage `Nexora/travail/films-reprise-codex/archives/gemini-long/gemini-long-before-c23-entry-fix-20261104T144226662401Z.json`, SHA-256 `7206988f86bd560a0a179674be6cb4bc2944bdebcfec11e66e952f67fc860dc3`, revérifié. 21 tests ciblés réussis. Aucune vidéo ou export antérieur modifié; nouvelle amorce à juger humainement, aucun rendu lancé.
- Mesh : commit local `4ba718b` : l’interface indique « Arêtes fermées » sans promettre l'aptitude à imprimer. Revue indépendante : avertissements affichés, aucun consommateur numérique de `volume` trouvé; typecheck réussi. Ces contrôles ne détectent pas les auto-intersections. Pas de push ni déploiement; réconciliation GitLab requise.

### Reprise Codex — mesure du garde Mesh, 4 novembre 2026

- Sur la chaise Pixal de 149 898 triangles, trois analyses CPU à deux cœurs après ajout du contrôle d'orientation ont pris 0,222 / 0,192 / 0,154 s; 549 arêtes ouvertes, 96 non-variété et 11 composantes, identiques aux contrôles précédents. Comparaison indicative sur un seul objet, sans preuve de performance générale. Résultat conservé dans `Nexora/travail/rnd-codex-20261104/mesh-essai-decimation/controle-orientation-a35a2d7.json` sur Storage.
- Le reste de l'environnement Ming de voix comprend des fichiers à plusieurs liens physiques, et un nom potentiellement sensible détecté dans son environnement; il n'a pas été déplacé ni lu. Aucun gain d'espace n'est présumé.

### Reprise Codex — contrôle visuel Gemini p19, 4 novembre 2026

- Une planche CPU des images 24, 28, 32, 36 et 123 de la source Gemini p19 a été créée sur Storage `Nexora/travail/films-reprise-codex/controle-gemini-c23-20261104/`. Elle montre une structure futuriste aux premières images et un bureau avec serveur à la 123e; les images intermédiaires et l'intention narrative restent à vérifier. Aucune conclusion de qualité ni note humaine. Planche archivée physiquement sur Infrastructure pc1, copie vérifiée par SHA-256, inventaire pc1 porté à 3933 entrées. Première tentative de commande sans chemin absolu FFmpeg : binaire introuvable, aucun fichier produit; seconde réussie.

### Reprise Codex — revues Mesh et intention Gemini, 4 novembre 2026

- Gemini p19 : le dossier de l'équipe décrit explicitement le passage continu de la Citadelle vers le bureau; les deux extrémités de la planche correspondent donc à l'intention écrite. Les images fixes ne prouvent pas la fluidité ni la qualité du montage; jugement humain requis.
- Revue indépendante Mesh `4ba718b` : incidents à une, deux et trois faces contrôlés, tétraèdre à positions négatives vérifié, 14 tests réussis; aucune régression constatée. Limites : la cohérence d'orientation n'exclut ni auto-intersection ni recouvrement; le soudage arrondi peut fusionner des sommets proches. Les clés ont été testées jusqu’à 2^32, mais l'analyseur utilise aussi un `Int32Array` : son fonctionnement n'est pas démontré à partir de 2^31 sommets. Aucun push ni déploiement.

### Reprise Codex — état réel Director/Finish et vertical Muse, 4 novembre 2026

- Les worktrees originaux sont `NexoraCreative-live-director` (`feat/realisateur-live-action`, `adc14a8`, code propre) et `NexoraCreative-sortie-video` (`feat/sortie-video-nvenc`, `9c223cb`). Les anciens changements de code non commités de la passation sont maintenant dans les commits locaux documentés. Finish conserve des modifications non commitées de `docs/JOURNAL.md` et `docs/PASSATION-AGENTS.md`, ainsi que `recherche/30-annexes/recalculer_ssim.py` et `work/` non suivis : intégralement préservés. État GitLab distant et intégration non démontrés par le ref local.
- Vertical Muse OPSYS : `montage.vertical` absent dans les deux révisions historiques examinées. Le court courant emploie six rushes propres Muse p01,p02,p04,p05,p07,p16; sélection actuelle p04/p05 r2 et p07 r1. Les reprises r2 p07/p13/p14 prévues ne sont pas présentes. Les 23 rushes examinés sont horizontaux; la passation prévoit le recadrage 9:16. Une proposition de Muse et une planche de cadrage archivée sont en préparation; aucun vertical rendu ni qualité attribuée.

### Reprise Codex — proposition Muse et limites lipsync, 4 novembre 2026

- Muse Spark 1.3 Contributor, via passerelle protégée isolée, a rédigé `Nexora/travail/rnd-codex-20261104/agents/muse-vertical-opsys/proposition-vertical.md` sur Storage : proposition 9:16 de 14,5 s avec les six rushes de son court. Exécution réussie, 5 requêtes et 0,00767 $ relevés. Le modèle n'a pas visionné les rushes : cadrages et recommandations sont hypothétiques, non des décisions du fondateur; aucune vidéo produite ni dossier produit modifié. Une planche réelle est en cours de préparation et d'archivage.
- Synchronisation labiale : les rapports persistants pc1 indiquent quatre essais LatentSync/MuseTalk `not_run_no_gpu_window` et aucun processus d'inférence GPU correspondant. Une évaluation CPU SyncNet existe sur deux clips H3 et deux témoins TTS; ce n'est pas une comparaison d'efficacité des modèles de retouche. Revue détaillée en cours.

### Reprise Codex — échéance lipsync et cadrage Muse, 4 novembre 2026

- Veille lèvres pc1 : `gpu_guard.py` cherche l'échéance à la racine et seulement au démarrage; le fichier existant se trouve sous `logs/`. Pour l'essai documenté, sa valeur correspondait cependant au même plafond de 3 h : le défaut ne démontre pas un surcoût substantiel. Risque confirmé pour une échéance différente ou ajoutée après démarrage. Une adaptation et des tests isolés sont proposés; aucun GPU ni fichier pc1 modifié.
- Planche Muse du court produite sur Storage (source unique par plan, image médiane, crop central 9:16) : à l'image p07-r1, un grand texte généré déformé apparaît dans une salle, ce qui ne correspond pas à la soumission décrite dans la proposition textuelle; visage p01 partiellement coupé. La planche n'établit pas le contenu du mouvement entier. Recherche de prises Muse alternatives en lecture seule et archivage pc1 de la planche en cours; aucun jugement humain ni vidéo nouvelle.

### Reprise Codex — archive planche Muse, 4 novembre 2026

- La planche comparative Muse est conservée sous Storage `Nexora/travail/films-reprise-codex/muse-court-vertical-comparison-20261104T212005732041Z/` et copiée sur le disque Infrastructure de pc1 sous `NexoraStudioWork/ArchivesNexora/codex-opsys-muse-court-vertical-comparison-20261104T212005732041Z/`. SHA-256 `392accf6ea804e261c2b0943d62da363bd65bf0ce8496128a0f96ca00d8c70ae` revérifié à distance; inventaire pc1 vérifié, 3934 entrées. Les autres aperçus de recherche ont été décodés en mémoire, sans fichiers images supplémentaires. Une seule image médiane par plan ne juge pas l'animation entière.

### Reprise Codex — candidat veille GPU, 4 novembre 2026

- Copie et correctif candidats sous Storage `Nexora/travail/rnd-codex-20261104/sync-gpu-guard-isolated/`; original pc1 inchangé, SHA-256 `829b5820262288feae8d2fb2baf39418ca9d855338a21c9b433fa44e3146a449`. Six tests CPU repassés indépendamment pour l'échéance; aucun accès GPU ou service.
- Revue bloquante : le candidat conservait l'appel original `POST /free` à ComfyUI, susceptible de décharger des modèles partagés. Il ne doit pas être exécuté ni intégré ainsi durant le diagnostic; suppression de cet effet en cours et test demandé. Une file vide ne constitue pas une réservation exclusive. L'échéance historique déjà expirée bloquerait toute future exécution jusqu'à sa mise à jour explicite.
