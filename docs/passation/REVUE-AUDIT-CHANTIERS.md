# Audit local des chantiers — 04/11/2026

Lecture seule : aucun service modifié, aucun rendu lancé, aucun secret lu. Les états distants sont des preuves historiques des documents ; cette session ne vérifie pas la production par SSH (sockets interdites par le bac à sable). Les empreintes ci-dessous viennent de `git -C <worktree> log`; « connu remote » signifie référencé dans les refs locales, sans fetch actuel.

## 1. Film Creative V7 : production loin d'être finie

- Worktree `/home/pc6/Desktop/NexoraCreative-film-v6`, branche `feat/film-v6-creative`, HEAD `4e9aeeb` (04/11 04:52:29 −05:00). `git log HEAD --not --remotes` vide : ses commits ne sont pas à déclarer « non poussés ». Le seul non suivi est `.codex-agent/` (métadonnées de sessions, ne pas committer aveuglément).
- Lire `marketing/creative/video-v7/HANDOFF.md`, `BRIEF-V7.md`, `chaine/README.md` et `recherche/26-recette-live-action.md`. Attention : HANDOFF dit que les processus tournent seuls, ce qui est antérieur à la panne ; cela ne prouve aucune activité actuelle.
- Dossiers créatifs présents dans le dépôt : Opus (20 plans), Gemini (24), Muse (12). DeepSeek est absent de `video-v7/equipes/deepseek/dossier.json`, mais son `DOSSIER.md` et `dossier.json` existent dans `/home/pc6/nexora-creative-data/promo/v7-creative/ecriture/deepseek/equipes/deepseek/` : importer et valider le matériel déjà écrit avant de le régénérer.
- Données persistantes : `~/nexora-creative-data/promo/v7-creative/` et `/media/pc6/Storage/Nexora/rendus/creative-v7/` (chemins utilisés par les états de jobs). Opus/Gemini/Muse n'ont que des images clés, avec états JSON/JSONL, prises et jugements. Aucun MP4 de plans ou montage d'équipe observé. Les seuls six MP4 V7 sont les six clips du banc `recette/`.
- Banc recette présent : 6 images et 6 MP4, correspondants aux six cas de `recherche/26`. Résultats historiques : images 2,9 → 7,0 ; vidéo 3,6 → 6,5 ; 5/6 duels gagnés dans les deux ordres, échec espace (vaisseaux deviennent cuirassés/maquettes). Ce n'est pas une note humaine finale de 8/10.
- Banc voix présent : 60 MP3 dans `voix-banc/`, index et palette dans le dépôt. HANDOFF propose Puck/Fenrir et Voxtral voix 3146 selon juge machine ; choix du fondateur non acquis.
- Suite : relire les signatures/états des images existantes, récupérer DeepSeek, vérifier les files GPU avant reprise ; produire plans et musique, brouillon, juge audio-vidéo et planches, une révision par équipe, finals 16:9/9:16, copies téléphone ≤28 Mo, archivage sur pc1 et bilan. Ne pas réutiliser des rushes d'une équipe pour les autres.

## 2. Film ultime OPSYS-AI : des brouillons existent, aucune finale attestée

- Worktree `/home/pc6/Desktop/NexoraCreative-opsys-ultime`, branche `feat/opsys-ultime`, HEAD `d728c65` (04/11 05:00:03 −05:00), égal à la ref locale `gitlab/feat/opsys-ultime`. MR !27 annoncée brouillon ; état actuel non relu. `equipes/essai` non suivi : ne pas l'intégrer sans examen.
- Lire `marketing/nexora/campagne-films/opsys-ultime/{BRIEF,HANDOFF}.md`, les quatre dossiers/révisions, `chaine/` et `marque-opsys.json` (nom/logo centralisés). Les indications de processus/PID du HANDOFF sont historiques, pas une preuve après redémarrage.
- Rushes observés dans `~/nexora-creative-data/work/opsys-ultime/<équipe>/plans/` : Opus 32 MP4 ; Gemini 20 ; Muse 23 (inclut reprises) ; DeepSeek 25. Les dossiers révisés Opus et DeepSeek contiennent chacun 38 entrées de plans : compter les seuls fichiers ne suffit pas à dire production achevée. Aucun marqueur `FINI` d'équipe observé.
- `/media/pc6/Storage/Nexora/rendus/opsys-ultime/` contient 9 MP4 : Opus long/court brouillons + essais musique c1/c2 ; Gemini long/court brouillons ; Muse long/court brouillons ; un essai de chaîne. DeepSeek/montage vide. Aucun final long/court/vertical et aucun `COMPARAISON.md` final observé dans les emplacements audités.
- Revues `REVUE.md` présentes pour les quatre équipes ; `choix.json` présent pour Opus/Muse/Gemini. Les voix/musiques et fichiers d'état persistent.
- HANDOFF historique à 04:50 : 99 vidéos archivées pc1 ; cette session n'a pas accès au disque distant pour recompter. Critère final : vérifier `INVENTAIRE.csv`, archiver aussi les nouvelles reprises et infographies.
- Lipsync : HANDOFF désigne installation persistante pc1 `NexoraStudioWork/lipsync/`, mais rapport Codex était dans scratch `/tmp` disparu. Localement, deux clips `tests/lipsync/` existent ; ce ne sont pas les preuves d'un comparatif LatentSync/MuseTalk terminé. Rechercher les fichiers persistants pc1 avant de refaire.
- Suite : reprendre étape par étape en conservant les brouillons/rushes ; terminer les reprises, choisir musique jugée sur film mixé, exporter long/court/vertical et téléphone, archiver, générer/revoir comparaison puis MR. Ne pas lancer en masse les scripts « automatiques » avant contrôle de leurs préconditions et des files partagées.

## 3. Director et Finish : code NON COMMITÉ, pas « commits non poussés »

- `/home/pc6/Desktop/NexoraCreative-live-director`, branche `feat/realisateur-live-action`, HEAD `da27fa4`. Aucun commit inédit dans `HEAD --not --remotes`. 14 fichiers suivis modifiés (331 ajouts/84 retraits au relevé), dont `graphs/h3.ts`, `index.ts`, `creer.ts`, `filmMoteur.ts`, `personnages.ts`, `promptH3.ts`, `realisateur.ts`, `reecritureH3.ts` et tests ; nouveaux `app/server/nexora/liveAction.ts` et `bench/liveAction.ts`. Préserver le diff, lire annexe A, vérifier/tests/banc avant commit/MR. Aucun déploiement de ce chantier prouvé.
- `/home/pc6/Desktop/NexoraCreative-sortie-video`, branche `feat/sortie-video-nvenc`, HEAD `da27fa4`. Modifications suivies `filmMoteur.ts`, `deploy/pc5-services/service.py` ; nouveaux `encodageGpu.ts`, test, `encoder_endpoint.py`, `test_encoder.py`, scripts `recherche/30-annexes/` et `recherche/30-cartographie.tmp.md`. Aucun commit de chantier, aucun rapport final `30-sortie-video.md` constaté.
- Cartographie 30 existante établit : export principal Mode Studio dans navigateur/Mediabunny/WebCodecs, pas CPU VM202 ; NVENC `/encoder` ne déporte pas automatiquement effets/compositing/OPFS. ProRes côté navigateur mappé AVC, pas encodeur ProRes client ; export ProRes serveur reste CPU ; « agrandir à l'export » ne lance pas Real-ESRGAN. Temps par route VM202 encore marqués non mesurés. Ce document doit être finalisé et testé, pas présenté comme déploiement NVENC achevé.

## 4. Mesh : recherches substantielles hors Git, rapport final manquant

- Recherche `/media/pc6/Storage/Nexora/travail/relief-29/wt`, branche `recherche/relief-29`, HEAD `f9de0e3`, propre, sans nouveau commit. Rapport final `recherche/29-relief-etat-de-lart.md`, backlog `relief.md` et `nexora-mesh-interface.md` absents des worktrees inspectés.
- Renommage `/media/pc6/Storage/Nexora/travail/relief-29/wt-nom`, branche `feat/nexora-mesh-nom`, HEAD `b636db9`, arbre propre, commit connu dans refs remotes locales. Ce commit ajoute `PRODUIT_3D`, route `/mesh`, préserve `/relief` et `/object`, met à jour textes/MCP/compétence Producteur/tests. Il n'est pas fusionné dans la ref locale `gitlab/developpement` ; déploiement non établi. Le nom est choisi ; ce n'est pas une décision encore ouverte.
- Sources persistantes de recherche à intégrer, sous `/media/pc6/Storage/Nexora/travail/relief-29/` :
  - `codex-a/resultat.md` : marché/produits hébergés, ~82 ko ;
  - `codex-b/resultat.md` : modèles ouverts et chaîne de post-traitement, ~94 ko ;
  - `codex-ui/resultat.md` : étude UX de dix produits, ~74 ko ;
  - `codex-lit/resultat.md` : 68 entrées principales, 15 étages, ~64 ko ;
  - `sa-carte/carte.md`, `sa-chaine/chaine.md`, prompts et résultats délégués ;
  - `codex-hy/JOURNAL.md`, `codex-pc4/JOURNAL-banc-pc4.md`, `runs/`, `glb/`, images fixes, manifestes de SHA.
- Ces études sont documentaires : « [LU] » signifie source textuelle ouverte, pas interface manipulée ni modèle essayé. Les assertions de moteurs/classes mondiales/prix doivent rester attribuées et datées ; aucune raison de les recommencer parce que le rapport 29 final manque.
- Banc constaté localement : 20 GLB Step1X3D R9700 (géométrie seule), 3 GLB Pixal3D BF16, 4 anciens GLB Pixal3D INT8 dans `codex-pc4/logs-pc4/pixal-int8-glb/`, 7 GLB Relief/TRELLIS GB10, 4 GLB Hunyuan2.1 forme. Répertoire `glb/hunyuan21-paint/` vide : Paint n'est pas fini. Les fichiers peuvent évoluer après le relevé : relire compteurs et états avant reprise.
- `runs/synthese-pc4.json` + `step1x3d-r9700.jsonl` attestent 20/20 sorties, médiane 28,986 s, pic alloué 8 838,37 Mo ; variante géométrie avec remplacement original du décodeur volume, pas pipeline officiel texture complet. `relief-trellis2-r9700.jsonl` : 0 succès, 3 tentatives sur première image puis 19 non tentées (NaN/Inf au remesh). `triposg-r9700.jsonl` : 20 entrées de non-exécution pour blocage droits identifié par l'agent, pas 20 essais GPU ratés.
- Pixal : échec UV FP64 sur GPU, repli CPU natif puis 4 exports INT8, échec NaN figurine ; troisième configuration BF16 avec options conservatrices réussit au moins 3 exports locaux. Aucun bilan final BF16 dans `runs/` au relevé. Ne pas confondre anciennes sorties INT8 et jeu canonique BF16.
- Hunyuan : `runs/hunyuan21-forme.jsonl` contient 4 mesures réussies (4 GLB). Chaise 227,4129 s, pic torch 7 837,96 Mio ; chargement 194,3008 s. Les deltas RAM système sont contaminés par autres jobs ComfyUI ; ils ne mesurent pas la seule RAM Hunyuan. Garde mémoire corrigé de `free` vers `MemAvailable` (12 Gio requis, arrêt préventif14 Gio), poids assignés par mmap/meta. Paint préparé mais pas prouvé exécuté ; remesh CPU de vérification à40k faces n'est pas un rendu Paint.

## 5. Plateforme et Wan : davantage fait que le maître ne le dit

- `/home/pc6/Desktop/NexoraPlateforme`, branche `developpement`, HEAD `7a69f57` (04/11 04:14:17 −05:00), propre, aucun commit hors refs remotes locales. Lire `docs/{ARCHITECTURE,FORMATAGE,INVENTAIRE,VERDICT-A-OU-B,MESURES-PC4}.md` et scripts de préparation.
- Fichiers présents : Dockerfiles H3, ROCm, llama-Vulkan, Blender, modeles-init ; verrous versions ; Kustomize passerelle-SA/H3/registre-relais, overlays pc1/pc3/pc6, manifeste modèles, scripts archives/mirrors/import/export, inventaires dix machines. Cela ne signifie pas que tous les services sont migrés en pods.
- Historique `ARCHITECTURE` §8 : registre VM205 `192.168.1.125:5000` en service ; images H3/modeles-init/LiteLLM multiarch/Blender/ROCm/Vulkan construites ; passerelle testée en pod pc3 avec clés factices, essai arm64 bloqué DiskPressure ; H3 démarrage CPU testé, GPU conteneur encore à valider ; ROCm/Vulkan en conteneur non essayés. Plan de contrôle k3s neuf/gabarits/snapshots non faits. Détourage est déjà un pod de production selon docs Creative : éviter « rien en pod en production ».
- Wan2.2 est installé ET testé historiquement sur R9700 (ComfyUI0.44, torch2.13 ROCm7.1) : T2V832×480,33 images,20pas,298s froid/266s chaud,25,3Go pic ; Fun-Control266s,17,7Go. Planches présentes `docs/mesures/wan22-{t2v,funcontrol}-planche.png`. T2V acceptable, Fun-Control comporte première image corrompue et géométrie inventée ; profondeur+VACE-Fun à tester. Poids VACE-Fun et LoRA4pas présents selon doc mais essais non faits. Intégration Creative non prouvée.
- Protection RAM pc4 historique : unité utilisateur transitoire `MemoryMax=22G`, `MemoryHigh=18G`, `MemorySwapMax=0`, cache-none/pinned désactivé, pour ne pas affamer GitLab (45Go RAM totale). Ne pas relancer les bancs AMD sans tenir compte de GitLab et des plafonds de puissance.
- Radeon « MI50 » est ProVII16Go gfx906 ; PyTorch ROCm7.1 échoue, llama.cpp Vulkan fonctionne (Qwen2.5-32B partiellement offload :4,2t/s). RX9070XT matmul fonctionne ; rôle applicatif réellement branché non établi.
- Preuves locales de sauvegarde : `/media/pc6/Storage/Nexora/sauvegardes/gitlab/20261104/` existe, 13 144 847 185 octets sur278 fichiers (miroirs/bundles/manifeste, pas sauvegarde GitLab complète). `/media/pc6/Storage/Nexora/modeles/magasin-copie/` existe (~69,9Go fichiers, dont8 poids H3/Music3 et manifeste). Sommes complètes non recalculées ici (coûtI/O). Aucun `/media/pc6/Storage/Nexora/images/` local : archives OCI attestées seulement VM205, copie hors VM à faire d'après docs.
- Sauvegarde GitLab complète (base/tickets/MR/CI/secrets chart) et restauration d'essai toujours non prouvées ; copies code seules insuffisantes. HDD pc5 pas installé selon dernier document. Ne formater aucun PC pendant cette mission.
- Contradictions docs : anciennes sections disent sudo pc4 absent, snapshot gpu-unlock à garder, Blender Dockerfile non fait et détourage SAM2.1 ; remplacées par dernières confirmations fondateur/docs Creative. Proxmox pc6 : volonté fondateur quasi tout parc, mais proposition architecte garde DGXOS sur ARM64/GB10 ; ne pas la présenter comme validation explicite du fondateur.

## 6. Rapports H3/Pika GB10 perdus ou non retrouvés

`RAPPORT-H3-GB10.md` et `RAPPORT-PIKA-GB10.md` non retrouvés dans `~/nexora-creative-data` ni `/media/pc6/Storage/Nexora` en excluant environnements/poids/sources. Les chemins annoncés étaient scratch `/tmp` supprimé par panne. Ne pas déclarer ces évaluations conclues. Vérifier anciens rendus/graphes et metadata persistants des moteurs, puis reconstruire le rapport si nécessaire ; ne pas relancer de benchmark pendant cette passation.

## Reprise priorisée

1. Préserver Director/Finish non commités, intégrer recherche Mesh hors Git et données films persistantes ; éviter tout reset/clean/worktree removal.
2. Contrôler accès/services/GPU/files après panne dans un contexte réseau autorisé, sans relancer en masse ; GitLab d'abord pour sauvegarde/synchronisation.
3. Finaliser Director/Finish par revue/tests, sans confondre export navigateur et serveur ; commits/MR distincts.
4. Achever quatre OPSYS et quatre V7 depuis leurs propres rushes/états, archiver tout (vidéos et infographies), conserver copies téléphone, demander seulement choix qualitatif humain quand livrables concrets.
5. Synthétiser29 et interface Mesh à partir de travaux déjà disponibles, terminer bancs restants seulement après contrôle ressources ; renommer en intégrant b636db9 sans réécrire son travail.
6. Compléter sauvegarde intégrale GitLab/restauration et archives horsVM205 avant toute migration/formatage ; HDD, V100 cu126 compatible sm70, images voix/lipsync et tests GPU conteneur restent à traiter.
