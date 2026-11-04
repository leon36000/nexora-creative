# AGENTS.md : consignes pour tout agent (Codex, Claude Code ou autre) sur Nexora Creative

Lis d'abord `docs/PASSATION-AGENTS.md` (état complet, machines, accès, chantiers, décisions en attente, instantané du 04/11/2026), puis `docs/ETAT.md` et la fin de `docs/JOURNAL.md`. Le dépôt GitLab est `root/nexora-creative` (https://pc4.tail0c55ff.ts.net, remote `gitlab`), branche d'intégration `developpement`. Réponds en français.

## Règles non négociables
- **Aucun secret** dans le dépôt, les journaux ou les réponses : clés (`/home/pc6/Desktop/Deepinfra.env`), jeton Hugging Face (`/home/pc6/Desktop/hf-token.txt`), `/etc/nexora/creative.env`, `/srv/nexora/secrets*`, fichiers de mots de passe du Bureau. Lis-les par script, sans les afficher.
- Ne tape jamais un mot de passe à la place du fondateur : donne-lui la commande à coller. Ne supprime pas de données définitivement sans qu'il le fasse (donne la commande).
- Jamais `pkill -f` ni tuer un processus qui n'est pas le tien. Les ComfyUI (pc1, GB10, VM 204) sont **partagés** : ne les redémarre pas, pas plus de 2 à 6 travaux à toi dans leur file.
- Rien acheter, aucune licence ou condition acceptée, aucun compte créé, pas de juridique.
- Ressources minimales, tout étiqueté, fichiers temporaires supprimés. Le disque système de pc6 est plein : travaille sur `/media/pc6/Storage/Nexora/` ou sur pc1/pc4/pc5.
- **Toutes les vidéos produites sont gardées** (pc1 : `~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/` + `INVENTAIRE.csv`).
- Qualité : 8/10 minimum exigé. Les auto-notes sont trop généreuses de 1,5 à 3 points : retire-les, et montre des planches d'images ou des mesures.
- Produit bilingue **français et anglais**. Nom et logo de l'entreprise : un seul endroit à changer.

## Façon de travailler
- Un worktree hors du dossier principal, une branche par sujet, **commit et push à chaque étape**, MR vers `developpement` (`gitlab-nexora` : `mr_create`, puis `mr_merge` avec `wait_pipeline`, gitleaks compris). Trailer de commit : `Co-Authored-By: <ton modèle> <noreply@anthropic.com>`.
- **Économie de l'abonnement** : délègue le mécanique à `outils/sous-agents/` (`deepseek`, `muse` effort max ; `gemini` Argon Flex seulement, effort moyen ; `gemini-eleve` Flex élevé) et à Codex (`outils/codex/codex-agent.sh sol|astra high|xhigh <prompt> <dossier>`). Toi, tu décides et tu contrôles. Les modèles délégués inventent parfois des références : vérifie les liens, articles et dépôts.
- **Processus pour toute nouvelle technologie** : `docs/PROCESSUS-TECHNOLOGIE.md`.
- Mets à jour `docs/JOURNAL.md` et `docs/PASSATION-AGENTS.md` quand l'état change.

## Si tu reprends à la place de Claude (abonnement arrivé à échéance)
Tout ce qu'il faut est dans le dépôt et `docs/PASSATION-AGENTS.md`. Outils déjà configurés pour Codex : serveur MCP `gitlab-nexora` (58 outils GitLab) et `GitLab-PC4` dans `~/.codex/config.toml` (l'authentification de GitLab-PC4 peut être à refaire par le fondateur). Accès SSH par alias (`pc1`, `pc3-agent`, `pc3-v100-vm`, `pc4`, `pc5-proxmox`, `nexora-creative`, `nexora-gpu`) dans `~/.ssh/config`. Modèles Codex : `gpt-6.1-sol`, `gpt-6-astra`. La mémoire de Claude est dans `/home/pc6/.claude/projects/-home-pc6-Desktop-Nexora-Creative/memory/`.
