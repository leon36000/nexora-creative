# Nexora : passation complète pour un autre agent (écrit le 04/11/2026)

Tu reprends un projet en cours. Lis ce fichier en entier, puis la mémoire (`/home/pc6/.claude/projects/-home-pc6-Desktop-Nexora-Creative/memory/MEMORY.md` et ses fichiers), puis `docs/ETAT.md` et la fin de `docs/JOURNAL.md` du dépôt Creative. Le détail brut de la session précédente : `/home/pc6/.claude/projects/-home-pc6-Desktop-Nexora-Creative/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d.jsonl` (énorme : cherche avec grep/python, ne le lis pas en entier).

## 1. Le fondateur et les règles
- Francophone (Québec), écrit vite, souvent depuis son téléphone (Remote Control). Il nomme l'agent principal **chef de projet** : il décide, ne dérange pas, vise le niveau « triple A mondial ». Réponses en français, courtes, honnêtes, sans jargon.
- **Qualité : il exige 8/10 minimum.** Les auto-notes des agents sont trop généreuses de 1,5 à 3 points (V6 : j'avais mis 7, il a mis 5,7). Il regarde lui-même les vidéos.
- Économie de l'abonnement Claude (il est à 95 % de la limite le 04/11) : déléguer au maximum aux sous-agents (section 3), Claude seulement pour planifier et contrôler.
- **Interdits permanents :** ne jamais afficher/committer une clé ou un jeton (Deepinfra.env, hf-token.txt, creative.env, /srv/nexora/secrets*) ; ne jamais `pkill -f` ni tuer un processus qui n'est pas le tien ; ne jamais taper un mot de passe (sudo ou autre) à sa place : donner la commande qu'il colle lui-même ; ne pas supprimer définitivement de données (donner la commande) ; rien acheter, aucune licence/CGU acceptée, aucun compte créé ; ne pas s'étendre sur le juridique (il le gère) ; pas de connexion à Tailscale ni à des consoles de comptes à sa place ; ne pas toucher aux projets des autres (VM 9100, AgentOS, InfraTech, JeuxVideo.ca, FutureIA, Codex Forgejo, Gitspace).
- Ressources minimales : « jamais plus que le nécessaire », tout étiqueté, fichiers temporaires supprimés, pas de copies de secours inutiles.
- **Toutes les vidéos produites sont gardées** (jamais supprimées), sur pc1 : `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/` + ligne dans `INVENTAIRE.csv`.
- **Tout est poussé sur GitLab au fur et à mesure** (MR vers `developpement`, pipeline vert dont gitleaks, trailer de commit `Co-Authored-By: Claude <modèle> <noreply@anthropic.com>`). Worktrees hors du dossier principal. MCP `gitlab-nexora` (mr_create, mr_merge wait_pipeline).
- Le produit doit marcher en **français et en anglais** (vision internationale ensuite).
- Pas de nom/logo d'entreprise codé en dur : il va changer (un seul endroit).

## 2. Les projets
- **Nexora AI** : entreprise. Site public (Next.js 16 + Bun + Directus 12.5.1 + LiteLLM + Postgres), dépôt `root/nexora-web` (local `/home/pc6/Desktop/NexoraSite`), VM 201 de pc5. Thème KTM orange (#FF6600) blanc/charbon. Gitspace caché/oublié. Les 6 pages légales ne doivent jamais être publiées. Produit payant : les **VPS** sur pc5 (le reste = jetons/stockage).
- **Nexora Creative** : studio IA (image, vidéo, musique, voix, Relief 3D, détourage, Mode Studio type Premiere simplifié, Marketing). Dépôt `root/nexora-creative`, local `/home/pc6/Desktop/Nexora Creative`, branche d'intégration `developpement`. VM 202 de pc5 (https://pc5-proxmox.tail0c55ff.ts.net:9443). Déploiement : `deploy/proxmox/mettre-a-jour-creative.sh` depuis un worktree de `gitlab/developpement`.
- **WorkStudio** (agents/flux, VM 203), **OPSYS-AI** (IA qui remplace les départements d'une entreprise ; le tableau de bord n'est PAS fini : ne jamais le montrer ; VM 9100 = pas à nous).
- **3D de Creative (notre « Meshy »)** : le fondateur n'aime PAS le nom « Relief » (04/11) ; nom à choisir (pistes : Maquette, Sculpt, Kiln, Anvil ; Forma est pris par Autodesk) ; Hunyuan3D-2.1 à comparer (licence : exclut UE, Royaume-Uni, Corée du Sud). Ancien nom « Relief » : **nom actuel du code** (`app/src/produit3d.ts`, modifiable) : aura sa page et ses vidéos, et sera un plugin.
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
| pc3 | `ssh pc3-agent` (clé `/home/pc6/Desktop/pc3-agent-ssh-key.txt`) | RTX 5080 16 Go : pod k3s `detourage` (SAM 3.1 + ViTMatte, namespace `nexora`, port 8231 réservé à la VM 202) + mode pro LTX-2.5 ; nœud k3s d'AgentOS à ne pas toucher ; VM qemu de la V100 |
| pc3 V100 | `ssh pc3-v100-vm` (clé `pc3-v100-vm-ssh-key.txt`) | Tesla V100 16 Go (Volta : pas de bf16/FP8, cu128) ; réseau NAT : Creative ne la joint pas sans `hostfwd` qemu |
| pc4 | `ssh pc4` (utilisateur `pc4`, clé `~/.ssh/id_ed25519_pc4_claude`) | **GitLab self-managed** (https://pc4.tail0c55ff.ts.net) ; GPU AMD : R9700 32 Go (ROCm natif dans `~/nexora-pc4`, Wan 2.2 prévu), RX 9070 XT 16 Go, « MI50 » = Radeon Pro VII 16 Go gfx906 (PyTorch ROCm y échoue ; llama.cpp Vulkan) ; **pas de sudo pour l'agent** |
| pc5 | `ssh pc5-proxmox` | Proxmox VE 9.2 (seul PC qui garde Proxmox) : VM 201 site, 202 Creative (192.168.1.122, `ssh nexora-creative`), 203 WorkStudio, 204 GPU (192.168.1.124, `ssh nexora-gpu` : 2080 SUPER :8188, 2070 SUPER :8189, service audio :8190, gpu-unlock actif), 205 `nexora-infra` (registre, magasin de modèles, trop grosse, à recréer à 120 Go avec le HDD) ; 9100 pas à nous ; Tailscale serve de l'hôte |
- Sudo : le fondateur a déposé ses accès sur le Bureau de pc6 (ne les lis pas, ne les utilise pas) ; la voie propre est un sudoers NOPASSWD qu'il installe lui-même (commandes en section 8).
- Le fondateur va installer Proxmox sur presque tous les PC (sauf pc5 déjà fait) : tout doit être en conteneurs/pods avec Dockerfile + manifestes dans GitLab + images archivées + magasin de modèles (poids hors des images, manifeste source/révision/sha256).

## 5. État de Creative (04/11)
- **En production :** MiniMax-H3 (h3-fast nvfp4, h3-max 10Eros×Singularity int8) sur la 5090 ; Qwen-Image 2.1, TRELLIS.2, Music3, RealESRGAN sur le GB10 ; aperçus 3D (`objet-apercu`, `objet-multivue`) sur les deux cartes Turing de pc5 ; **réalisateur** (`app/server/nexora/realisateur.ts`, MR !23) : réécrit les demandes à l'arrache (Argon Flex), panneau « Ce que l'IA a compris » ; agent 3 niveaux + facturation (prix client = coût × 1,10 × 1,4025 × 100 crédits) ; Mode Studio ; Marketing ; détourage `/detourage` (SAM 3.1 + ViTMatte base, trimap 5 %, sélection par mot en anglais : à traduire automatiquement pour le français ; SAM 2.1 supprimé).
- **Config prod** : `/etc/nexora/creative.env` sur la VM 202 (`NEXORA_MOTEURS_GPU`, `NEXORA_DETOURAGE_URL` = pc3:8231, jeton).
- **Non branché / en test :** Pika H3 Flex (installé sur le GB10, rendus de mesure en cours par Codex), Wan 2.2 (prévu R9700), LTX-2.5 pro (tourne sur la 5080, pas branché : `licences.ts` le bloque, décision du fondateur), transcription Studio (aujourd'hui faster-whisper medium sur le CPU de la VM 202 ; à basculer sur pc5 GPU).
- **Qualité vidéo :** H3 est le meilleur modèle ouvert (3e de l'arène). Le client a jugé V4 « Une phrase. Un film. » (goutte d'or, en ligne sur le site) 6,5/10, V5 pire, **V6 5,7/10** : défauts = plans « jeu vidéo » au lieu de prises de vues réelles, voix « cheap » (voix native H3) ou « trop smooth » (ElevenLabs Alexandre), musique plate qui ne colle pas aux images. Il veut du spectaculaire (dragons, explosions, batailles spatiales, duels de lames d'énergie) en rendu photoréaliste, une musique écrite pour le montage (temps forts, dynamique, motif), choix du style laissé à nous.

## 6. Chantiers en cours (agents lancés ; résultats attendus)
1. **Film Creative V7** : 4 films faits depuis le début par 4 équipes (DeepSeek, Muse, Argon Flex élevé, Opus), live action, voix Mistral Voxtral (`mistralai/voxtral-mini-tts-3-0`, `-2603`) contre MiniMax Speech 2.8, MAI-Voice-2.1, Fish S2.1, musique par sections ; worktree `/home/pc6/Desktop/NexoraCreative-film-v6`, branche `feat/film-v6-creative`, `marketing/creative/video-v6/` ; recette live action → `recherche/26-recette-live-action.md`.
2. **Film OPSYS-AI ultime ×4** : brief `marketing/nexora/campagne-films/opsys-ultime/BRIEF.md`, worktree `NexoraCreative-opsys-ultime`, branche `feat/opsys-ultime`, comparaison `COMPARAISON.md`. Scènes voulues : soumission par photo → signal satellite/5G/poteaux → serveur (entreprise virtuelle) → retour au représentant ; M. Morin ; adjointe (« rendez-vous avec M. Thibault à 14 h ») ; avatar comptable (+7 % de productivité) ; cédule 3 semaines ; pointage puis chèque de paye ; pas de tableau de bord ; musique entraînante.
3. **Infra pods/formatage** : `root/nexora-plateforme` (MR !1 ouverte, `docs/ARCHITECTURE.md`, `docs/FORMATAGE.md`) ; rien n'est encore en pod en production ; sauvegarde complète de GitLab (pc4) **non faite** (sudo requis).
4. **GPU de pc5** : mesurer ce que portent les 2 cartes 8 Go (détourage rapide, NVENC, Parakeet, Cosmos Reason2, transcription, voix, LLM réparti sur les deux) ; rapport `recherche/28-gpu-pc5.md`.
5. **Relief** : état de l'art + banc contre les meilleurs modèles 3D, spec plugin MCP, 10 cas d'usage → `recherche/29-relief-etat-de-lart.md`, `docs/backlog/relief.md`.
6. **Codex (scratchpad de la session, `/tmp/claude-1000/-home-pc6-Desktop-Nexora-Creative/4a161a25-a3c4-4a78-94f6-c7dc7ebef37d/scratchpad/` ; peut disparaître au redémarrage)** : `h3-gb10/RAPPORT-H3-GB10.md` (un 2e H3 sur le GB10 vaut-il la peine ?), `pika-gb10/RAPPORT-PIKA-GB10.md` (Pika H3 Flex, graphes dans `graphes/`).
- Recherche déjà fusionnée : `recherche/23-grammaire-promos-ia.md` (102 promos analysées), `24-etat-de-lart-creative-2026-11.md`, `25-realisateur-et-vfx-blender.md`, `27-nvidia-pour-creative.md` (top 5 qualité : RTX Video SR, Cosmos Transfer 2.5, DiffusionRenderer/Harmonizer, Magpie+LipSync, Cosmos Reason2 ; top 3 vitesse : Sol-H3, NVENC+séparation des tâches, ModelOpt), backlog `docs/backlog/creative-triple-a.md` (TA1 à TA25 : mesurer Pika, refaire les promos selon la grammaire, facturation, 20 recettes, voix, interface triple A, compilateur de prompts, lipsync MuseTalk/LatentSync, MCP distant + API publique...).

## 7. Vision à moyen terme (décisions du fondateur)
- Chaque fonction de Creative (Relief, vidéo, musique, voix, détourage, lipsync...) sera aussi un **plugin Codex et Claude** via un MCP public + API (crédits). Architecture décidée : un seul dépôt produit (`nexora-creative`) avec des **modules indépendants** (README, tests, contrat E/S, conteneur, fiche MCP) + **miroirs GitLab en lecture seule par technologie** quand elle est prête + dépôt `nexora-plugins` pour les enveloppes.
- Plus tard : Relief a sa page dédiée et ses vidéos marketing ; films pour Creative, WorkStudio, Nexora, OPSYS et **15 vidéos sociales faites avec Muse** (15 angles avaient été rédigés).
- Prix : brouillon 0,02 $, finale 0,10 $, Studio gratuit, forfait 29 $ (proposition recherche/24).

## 8. À faire par le fondateur (donner les commandes, il les colle)
- Terminal pc6 (onglet « Accès sudo pc4 et pc3 » ouvert dans l'app) :
  - `ssh -t pc4 'echo "pc4 ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/90-nexora-agent >/dev/null && sudo chmod 440 /etc/sudoers.d/90-nexora-agent && echo PC4-OK'`
  - `ssh -t pc3-agent 'echo "pc3 ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/90-nexora-agent >/dev/null && sudo chmod 440 /etc/sudoers.d/90-nexora-agent && echo PC3-OK'`
  - Supprimer l'instantané : `ssh pc5-proxmox 'qm delsnapshot 204 avant-gpu-unlock-pr294'`
  - pc3 : agrandir le volume `sudo lvextend -r -l +100%FREE /dev/ubuntu-vg/ubuntu-lv` et supprimer `~/models/OrcaSAQ-2-27B-Uncensored` et `~/models/OrcaSAQ2-DFlash2-CPU`.
- Décisions en attente : accord pour brancher LTX-2.5 pro dans Creative ; retirer Chatterbox/Kokoro de la VM 204 ; supprimer des environnements de test de pc6 (`chatterbox` 5,7 Go, `sgl-gb10` 9,3 Go) ; V100 en production (réglage `hostfwd` qemu sur pc3) ; vérification visuelle de `/detourage` dans le navigateur ; refaire l'authentification MCP GitLab de Codex ; faire tourner (rotation) les clés DeepInfra/OpenRouter et le jeton HF ; installer le disque dur 10-20 To sur pc5 (docs/RESSOURCES.md §3) ; nom de domaine (nexora.ai pris, rien acheté) ; clé Stripe de test, prix VPS, bloc IPv4 public ; sort de la VM 9100.

## 9. Pièges connus
- `/tmp` et les worktrees temporaires disparaissent aux pannes de courant (il y en a eu une). Tunnel pc1 : `tunnel-pc1.sh` ; ComfyUI pc1 : commande dans `~/Bureau/...` / mémoire `proxmox-nexora-infra`.
- ComfyUI de pc1 et du GB10 sont **partagés** par tous les films : jamais plus de 2 à 6 travaux d'avance, jamais de redémarrage.
- Tailscale sur pc6 est en mode utilisateur : tester les adresses ts.net depuis pc5 (`ssh pc5-proxmox curl ...`).
- Le pool SSD de pc5 (913 Go, 44 %) est sur-alloué en provisionnement léger (1000 Go de disques) : surveiller.
- Les agents délégués inventent parfois des références : vérifier chaque lien/arXiv/dépôt.

- **Film V7 de Creative** (04/11, 04 h 30, agent Opus du film Creative) : passation dans `/home/pc6/Desktop/NexoraCreative-film-v6/marketing/creative/video-v7/HANDOFF.md` (branche `feat/film-v6-creative`, MR !26) ; productions opus/gemini/muse en cours sur la file GPU, DeepSeek en écriture directe sur DeepInfra.
