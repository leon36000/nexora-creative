# Film ultime OPSYS-AI : passation (04/11/2026, mise à jour 04 h 50)

Arrêt anticipé demandé (abonnement Claude du fondateur à 95 %). La production continue **seule** : des scripts en arrière-plan
tournent, révisent, mettent en musique et montent les quatre films. Ce document dit où en est chaque chose et comment reprendre.

## Où sont les choses
- Dépôt : branche `feat/opsys-ultime` (worktree `/home/pc6/Desktop/NexoraCreative-opsys-ultime`), MR !27 (brouillon) vers `developpement`.
- Création et chaîne : `marketing/nexora/campagne-films/opsys-ultime/` — `BRIEF.md` (brief commun), `equipes/<e>/` (DOSSIER.md,
  dossier.json, CORRECTIONS.md, REVISION.json), `casting/` (PALETTE.md, palette.json, MOTEURS.md), `chaine/` (tous les outils, voir l'en-tête
  de chaque script), `marque-opsys.json` (seul endroit du nom et du logo : le carton se refait en relançant `monter.py`).
- Travail (pc6) : `~/nexora-creative-data/work/opsys-ultime/<e>/` (fiches, cles, voix, musique, plans = rushes H3, revue, choix.json) ;
  les montages sont sur le disque externe `/media/pc6/Storage/Nexora/rendus/opsys-ultime/<e>/montage/` (lien symbolique `montage`).
- Vidéos gardées (pc1) : `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/opsys-ultime/<e>/{plans,montage,voix,musique,…}` + `INVENTAIRE.csv`
  (`chaine/archiver.py <e>`, relancé à la fin de chaque film).
- État en une commande : `~/nexora-creative-data/work/opsys-ultime/etat.sh`.

## Ce qui est fait
- Brief, chaîne (tournage H3 avec références et voix ancrées, palette de voix en deux manches, musique conformée au montage, juges de
  machine, rendu EditPlan + incrustations), quatre dossiers créatifs (Opus écrit à l'aveugle et commité à 23 h 05 le 03/11 ; DeepSeek,
  Muse, Gemini par `outils/sous-agents`). Coûts d'écriture : DeepSeek 0,76 $, Muse 0,025 $, Gemini 1,30 $ (avant Flex).
- Tournage 16:9 : ≈ 80 plans sur ≈ 110 à 04 h 15 (file de la 5090 partagée, ≈ 18 plans par heure).
- Décisions communes aux quatre équipes : 9:16 natif annulé (file GPU) → vertical recadré depuis le 16:9 ; nouvelles consignes du fondateur
  (musique écrite pour le montage, voix manche 2, rendu « prise de vues réelle ») données à la révision.

## Ce qui tourne tout seul (processus en arrière-plan, journaux dans `~/nexora-creative-data/work/opsys-ultime/`)
1. `file.py plans` par équipe (`file-<e>-169.log`) : fin du tournage 16:9.
2. `chaine/vers_revision.sh <e>` (`vers-revision-<e>.log`) : dès que les plans d'une équipe sont tournés → premier montage (brouillon),
   juge « réel contre synthèse », juge audio-vidéo, `revue/REVUE.md` et planches, puis **session de révision** du sous-agent
   (DeepSeek et Muse en effort max, Gemini en `gemini-eleve` Flex). Pour `opus`, il s'arrête au matériel de révision.
3. `chaine/apres_revision.sh <e>` (`apres-revision-<e>.log`), déclenché quand la révision est terminée : import et contrôle du dossier
   révisé, voix, reprises (≤ 8 unités), 3 à 4 musiques candidates (Lyria 3 Pro, MiniMax-Music3, ACE-Step 1.5), conformation, juge,
   choix, montages finaux long / court / vertical, juge final, archivage pc1, `comparer.py` (→ `comparaison.json`).
4. Codex : évaluation de LatentSync 1.6 / MuseTalk 1.5 contre la parole native de H3 (dossier
   `/tmp/claude-1000/…/scratchpad/codex-lipsync/`, installation sur pc1 `NexoraStudioWork/lipsync/`), en attente d'une fenêtre GPU.

## État à 04 h 50
- Plans 16:9 : opus 28/32, deepseek 18/32, muse 20/20 (fini), gemini 18/20. Muse est en session de révision depuis 04 h 31.
- Révision Opus écrite et commitée (REVISION.json : 8 unités de reprises en prise de vues réelle ; voix n01, n07, m01 refaites) ; son
  `apres_revision.sh` part tout seul dès que ses plans sont tournés.
- Chaîne musique testée de bout en bout sur Opus (évaluation de 2 candidates sur le film mixé) : Lyria c1 note du juge 7,5/10 (accord 7,
  dynamique 8, motif 7), ACE-Step c2 6,9 ; Music3 c3 à régénérer (le GB10 est chargé par d'autres bancs).
- 99 vidéos déjà archivées sur pc1 et inventoriées (rushes, essais de synchronisation labiale, voix natives H3, essai de chaîne).
- `chaine/finir.sh` attend les quatre « FINI » puis écrit `COMPARAISON.md` (rapporteur gemini-eleve), commite et pousse.

## Ce qui reste
- Surveiller les journaux `apres-revision-<e>.log` (le premier passage réel de cette chaîne sera Muse) et `finir.log` ; en cas d'échec
  d'une étape, la relancer seule (chaque script est idempotent : ce qui existe est sauté).
- Relire `COMPARAISON.md` (écrit par un sous-agent à partir des seules données) et y ajouter, si possible, une note humaine sévère.
- Fusion de la MR !27 après relecture ; nettoyage : `equipes/essai/` (essai de chaîne, non commité), fichiers temporaires du scratchpad,
  courts YouTube déjà supprimés.

## Pièges connus
- `pkill -f` / `pgrep -f` avec un motif présent dans sa propre ligne de commande tue son propre shell : tuer par PID seulement.
- ElevenLabs lit à voix haute toute consigne en prose : seules les balises entre crochets lui sont transmises (corrigé dans `voix.py`).
- Répliques très courtes (1 à 2 mots) : Drama 3 et ElevenLabs les ratent souvent ; préférer une phrase de 4 mots ou plus.
- H3 : texte et logos spontanés, ouverture parasite de 0,5 à 1 s sur certains plans (entrer à 1 s), figurants non demandés.
- Gemini 4 Argon : toujours par Flex (`provider.order = ["google-ai-studio/flex"]`, fait dans `voix.post`).
