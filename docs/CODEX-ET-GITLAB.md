# Codex et GitLab Nexora

Mis à jour le 02/11/2026. Ce document sert à deux choses : (1) dire où en est chaque agent Codex et lui donner le message exact pour continuer sur GitLab, puis sur Gitspace (Forgejo) ; (2) donner au fondateur le rituel pour créer un nouveau projet.

## 1. Comment Codex utilise GitLab maintenant

| Voie | État | Ce qu'il faut |
|---|---|---|
| Serveur MCP **`gitspace`** (le nôtre, `outils/gitspace-mcp`, 58 outils) | **Fonctionne dans Codex** : essai réel avec `codex exec` (outils `whoami` et `project_list` exécutés). Déclaré dans `~/.codex/config.toml` | Rien d'obligatoire. Recommandé : le fondateur crée son jeton d'accès personnel (portée `api`) et lance `node outils/gitspace-mcp/dist/index.js login` (voir `outils/gitspace-mcp/README.md`), pour ne plus dépendre du jeton partagé de l'agent `agent-nexora-workstudio-web` (compte administrateur) |
| Serveur MCP intégré `GitLab-PC4` (`/api/v4/mcp`) | **Non connecté dans Codex** (`codex mcp list` : *Not logged in*). Outils limités, ni création de projet ni protection de branche | Optionnel : `codex mcp login GitLab-PC4` dans un terminal (OAuth dans le navigateur). Inutile si `gitspace` suffit |
| `git` en ligne de commande | Fonctionne (push HTTPS, jeton fourni par l'assistant d'identifiants du dépôt) | Dépôt cloné avec un remote `gitlab` ou `origin` vers `https://pc4.tail0c55ff.ts.net/...` |

Règle commune : jamais de force-push, jamais de jeton dans un message, un fichier ou un commit.

## 2. Carte des chantiers Codex

Relevé fait en lisant les sessions Codex (`~/.codex/sessions`, `automations`), l'état Git local et l'API GitLab. Les trois chantiers demandés d'abord, puis les autres. Les dates sont celles de la dernière activité observée.

### 2.1 Gitspace (Forgejo) — « forge conçue pour les agents IA »

- **But** : une forge pour agents IA où Gitspace reste l'autorité sur missions, budgets, preuves et décisions de fusion, avec un Forgejo derrière. Le crate Rust s'appelle `agent-forge-core`.
- **Où** : dossier local `/home/pc6/Documents/Codex/2026-10-21-mission-construire-une-forge-con-ue` (37 Go, presque tout dans `target/`), worktree d'intégration `.runtime/webhook-005-workspace`. Forgejo local v17.0.0 sur `127.0.0.1:3130` (dépôt `forge-admin/agent-forge-core`). Remote `pc4-gitlab` vers **`root/gitspace-forgejo`** sur GitLab : branche par défaut protégée `codex/pc6-transfer-2026-10-28`, plus `codex/pc6-transfer-work-2026-10-28` et `security/gitleaks-triage-2026-11-02`. Le projet GitLab `root/agent-forge-core` est vide. Travaux plus anciens : `/home/pc6/NAOS/60_travaux/GitSpace_Hermes_20261011`.
- **État** : 426 tests Rust passés, 0 échec (au 24/10), parcours REQ-001, LIC-001, WEBHOOK-001/002 fusionnés dans le Forgejo local, récepteur de webhook signé et idempotent, réconciliation. Veille GitHub/arXiv du 01-02/11 (looper, Harbor, LiteLLM, SWE-ReX...) déposée dans le projet. Le projet est déclaré incomplet : aucun parcours LLM/AgentOS démontré, licence du produit non choisie (métadonnées Cargo sans licence).
- **Derniers blocages** : (1) le transfert vers GitLab PC4 est volontairement bloqué tant que rotation/révocation des secrets, assainissement, scan complet et pipeline de sécurité ne sont pas vérifiés (la branche `security/gitleaks-triage-2026-11-02` en est le début) ; (2) Forgejo n'a pas de précondition atomique « la base n'a pas bougé » à la fusion (course constatée dans les tests) ; (3) le test Go du lot CAS/LFS n'a pas pu tourner : pas de toolchain Go.
- **Non poussé** : modifications locales non commitées (`Cargo.toml`, `README.md`, `docs/*`, `evidence/`, `tests/`, `.superpowers/`). Les automatisations « continuer-la-forge-locale » et « poursuivre-la-forge-agentique » sont en pause.

### 2.2 Nexora Code (client desktop natif en Rust)

- **But** : successeur de « codeCo », un client de code type Codex en Rust (moteur Codex public épinglé, mémoire/RAG locaux, mécanismes UltraCode, interface graphique).
- **Où** : GitLab **`nexora/nexora-code`** (ID 12, privé, branche `main`, dernier commit le 01/11 : admission d'activation en lecture seule). `root/nexora-code` existe aussi mais est vide : ne pas l'utiliser. Checkout canonique sur PC1 : `/home/pc1/AgentOS-Construction`. Sur cette machine : `/home/pc6/Desktop/NexoraCode` (source seule, sans `.git`) et `/home/pc6/Desktop/Claude Code/nexora-code` (non Git à l'inspection). Session Codex d'origine : « Nexora Code natif en Rust » (21-22/10).
- **État** : 970 tests Rust, 54 Python, 52 audits de traces au checkpoint du 31/10 ; prototype précompilé qui démarre hors checkout. Pas encore qualifié : installation, missions modèle générales, produit complet.
- **Règles du dépôt** (`docs/GITLAB_CONTINUITY.md`) : travail 100 % GitLab privé, synchroniser après chaque tranche (push avec `ci.skip`, jamais de force-push), ne dire « synchronisé » qu'après avoir vérifié que le SHA distant est égal au HEAD local, secrets/caches/modèles/runtimes hors Git, pas de CI ni déploiement implicite.
- **À ne pas confondre** : `root/nexora-code-agent` est le fork OpenCode (branche `feat/rebrand`), travail de Claude Code, pas de Codex.

### 2.3 Mise à jour du pilote NVIDIA (« NV driver update »)

- **But** : pilote NVIDIA « hybride » (module noyau ouvert R580 corrigé pour GV100/V100, recherche sur le HAL R595) pour faire cohabiter les V100 avec les GPU récents.
- **Où** : projet GitLab **`root/nvdriver-v100-update`**, créé le 29/09 et **toujours vide** (aucune branche). Le travail réel est local : `/home/pc6/Documents/Codex/driver-hybrid-*`, `nvidia-hybrid-fault-audit-20261021`, `pc6-r595-hal-v2-*`, `pc6-nvos56-review-v2-20261023`, `/home/pc6/claude-driver-hybrid-uvm-v5-20261023` (rapport + correctif `patched/`), `claude-driver-hybrid-waitlock-v1-20261023`, `claude-driver-hybrid-preflight-module-collision-v1`. **Je n'ai pas retrouvé le dépôt de travail principal** (les sessions Codex pertinentes sont dans l'espace `2026-10-05/github-plugin-...`, 295 Go) : le premier travail de l'agent est de le localiser et de le dire.
- **État** : revues indépendantes de correctifs UVM (R580.178.04, patch 0002) et audit du drainage des fautes non rejouables GV100 à la suspension. Verdict du 23/10 : « conditionnellement correct sur le périmètre nommé », **validation statique seulement** (`hardware_validated = false`, aucun module compilé, installé ni chargé).
- **Dernier blocage** : l'expérience de validation décisive sur matériel n'est pas faite ; tout ce qui n'est pas poussé (correctifs, tests, rapports) est local.

### 2.4 Autres chantiers repérés

| Chantier | Où | État (relevé du 02/11) |
|---|---|---|
| OPSYS-AI (CRM terrain, missions M4/M5) | GitHub `leon36000/OPSYS-AI` (PR #856), GitLab `root/opsys-ai` (branche `migration/product-r3206`), Codex `2026-10-28-voici-une-missions-pour-opsys-ai/OPSYS-AI` | M5 bloquée par la dépendance au socle ; PR #856 partielle, 17 tests de cascade/publication/lecture en échec, jonction ciblée à 56 tests verts |
| VoltaFabric (moteur d'experts sur V100) | GitLab `root/voltafabric` (branches `r114`...`r366`), `/home/pc6/NAOS/60_travaux/voltafabric-reprise-gitlab-20261030` (a un `AGENTS.md`) | Veille arXiv/GitHub quotidienne, réutilisation de composants de moteurs ; comparaisons de vitesse en attente ; automatisation en pause |
| PC5 (RAG, OpenClaw, Evolution) | `work/pc5-power-recovery-20261004/...` (dossier Codex 2026-10-18), `/home/pc6/NAOS/PC5-Chaine-Logicielle-20261012` | Automatisations en pause ; un seul coordinateur modifie la production |
| DSH / évolution sous plafond API | `/home/pc6/Documents/Codex/2026-09-28/in/work/mission-20260930` | Plafond de 20 USD presque consommé : aucun nouvel appel payant |
| rea (rétro-ingénierie) | serveur MCP local `rea` dans `~/.codex/config.toml` | Installé le 14/10 ; pas de projet GitLab dédié |
| Helix 32B | GitLab `root/helix-32b` (`main`) | Paquet de modèle poussé le 30/10 |

Je n'ai pas vérifié le détail de ces cinq lignes : à confirmer par l'agent concerné avec le message générique du paragraphe 3.1.

## 3. Messages à envoyer aux agents

### 3.1 Message générique (début de toute reprise)

```text
Tu as accès à GitLab par le serveur MCP « gitspace » (déjà configuré, aucune connexion à faire). Commence par l'outil whoami.
Le GitLab privé est https://pc4.tail0c55ff.ts.net (réseau Tailscale). Tout le développement se passe là :
un projet par chantier, une branche par tâche, une merge request par livraison. Pas de force-push, pas de secret dans un dépôt,
pas de jeton affiché ou copié nulle part. Les actions destructives demandent confirm: true (essaie d'abord dry_run: true).
Outils utiles : project_list, project_get, tree_list, file_read, branch_create, commit_files (plusieurs fichiers en un commit),
mr_create, mr_merge (wait_pipeline: true), job_log, ci_var_set. Pour un gros dépôt local, utilise git (remote https, push sans force).
Les tests et expériences sur pc1/pc6 sont supprimés une fois finis ; tout ce qui est Nexora vit sur pc5.
Avant d'agir : lis l'état distant (branch_list, commit_list), intègre sans écraser, et dis-moi ce qui n'est pas encore poussé.
```

### 3.2 Agent Gitspace (Forgejo)

```text
Reprends la mission « forge conçue pour les agents IA » (Gitspace). Utilise le serveur MCP « gitspace » pour GitLab.
Lis d'abord : docs/checkpoint.md, README.md, puis docs/CODEX-ET-GITLAB.md du dépôt nexora-creative (section 2.1).
Dépôt GitLab : root/gitspace-forgejo (branche par défaut protégée codex/pc6-transfer-2026-10-28 ; travail sur
codex/pc6-transfer-work-2026-10-28 ; branche security/gitleaks-triage-2026-11-02 à lire avant toute chose).
Règle : le transfert vers GitLab reste bloqué tant que la rotation/révocation des secrets, l'assainissement de l'historique,
le scan complet (gitleaks) et le pipeline de sécurité ne sont pas vérifiés. Ne pousse aucun contenu non assaini ; commence par
terminer et documenter ce contrôle, puis ouvre une merge request pour le reste.
Ensuite : commit des modifications locales en attente (Cargo.toml, docs, evidence, tests) en branche de travail, MR, puis
reprends les lacunes ouvertes : précondition de base à la fusion, lot CAS/LFS (installe Go si nécessaire dans un dossier jetable),
choix de licence à demander au fondateur. Prépare la future bascule : GitLab est la source de continuité, Gitspace/Forgejo la cible ;
le serveur gitspace-mcp a un adaptateur Forgejo à écrire (outils/gitspace-mcp/src/providers/forgejo.ts), ne le fais qu'après accord.
Ne lance aucun runner mutatif sur le Forgejo actif. Supprime target/ et tout dossier de test dès qu'ils ne servent plus.
```

### 3.3 Agent Nexora Code

```text
Reprends Nexora Code. Dépôt : GitLab nexora/nexora-code (branche main), checkout canonique /home/pc1/AgentOS-Construction.
Lis d'abord README.md, docs/GITLAB_CONTINUITY.md et le dernier checkpoint de verification/. Avant de coder : git fetch, compare
le SHA distant au HEAD local, intègre sans écraser. Après chaque tranche utile : commit en français, push (ci.skip, sans force),
vérifie que le SHA distant égale le HEAD local, puis seulement alors écris « synchronisé ». Secrets, caches, modèles et runtimes
restent hors Git. Utilise le serveur MCP « gitspace » pour les MR, pipelines et lectures, git pour les pushes volumineux.
N'utilise pas root/nexora-code (vide, doublon) ni root/nexora-code-agent (autre chantier : fork OpenCode).
Priorités : les 162 capacités et l'interface graphique desktop ; ne substitue pas une CLI au produit. Dis ce qui n'est pas qualifié.
```

### 3.4 Agent mise à jour du pilote NVIDIA

```text
Reprends le chantier « NV driver update » (pilote NVIDIA hybride R580, GV100/V100, recherche R595). Utilise le serveur MCP « gitspace ».
Étape 1 : retrouve le dépôt de travail principal (les dossiers connus : ~/Documents/Codex/driver-hybrid-*, nvidia-hybrid-fault-audit-20261021,
pc6-r595-hal-v2-*, ~/claude-driver-hybrid-uvm-v5-20261023 avec patched/ et REPORT.md) et dis-moi où il est.
Étape 2 : le projet GitLab root/nvdriver-v100-update est vide. Pousse-y, par branche et MR : les correctifs (patches/), les tests, les
rapports de revue et un docs/ETAT.md (verdict du 23/10 : validation statique seulement, hardware_validated = false). Aucun binaire,
archive du code source NVIDIA complet, module compilé, modèle ou secret dans Git : référence l'archive par son nom et son empreinte.
Étape 3 : définis l'expérience de validation sur matériel (drainage des fautes GV100 à la suspension) sur une machine jetable ; ne charge
aucun module sur une machine de production sans mon accord. Supprime les dossiers d'audit jetables une fois les résultats poussés.
```

### 3.5 Message pour les autres chantiers

Utiliser le message générique (3.1), en ajoutant la ligne « Dépôt GitLab : <projet> ; lis d'abord AGENTS.md ou README.md ; les automatisations en pause le restent tant que je ne les ai pas relancées ».

## 4. Créer un nouveau projet

### 4.1 Message à copier-coller dans Codex

Remplacer les trois champs entre crochets.

```text
Crée un nouveau projet sur notre GitLab avec le serveur MCP « gitspace » :
- nom : [NOM], description : [UNE PHRASE], groupe : [root ou nexora], visibilité privée ;
- appelle project_create avec namespace, readme: true, default_branch: "main", work_branch: "developpement",
  scaffold: { agents_md: true, ci: true, gitignore: true } (la branche main est protégée : push Maintainer, merge Developer, pas de force-push) ;
- complète ensuite AGENTS.md avec le but du projet et la façon de le lancer (commit_files sur la branche developpement, puis mr_create vers main) ;
- ne mets aucun secret dans le dépôt : les secrets passent par ci_var_set ou un fichier local hors Git ;
- puis rends-moi : l'adresse du projet, le chemin groupe/projet, les branches, et la première étape proposée.
Règles : le développement se passe sur GitLab ; les tests et expériences sur pc1/pc6 sont supprimés une fois terminés ;
tout ce qui est Nexora vit sur pc5 ; aucune allocation démesurée ; chaque fichier créé a un propriétaire et une durée de conservation.
```

### 4.2 Modèle `AGENTS.md`

Ce modèle est celui que `project_create` dépose quand `scaffold.agents_md` vaut `true` (source : `outils/gitspace-mcp/src/templates.ts`). Il se copie aussi à la main dans un projet existant.

```markdown
# AGENTS.md — [NOM]

[Description]

Dépôt : `[groupe/projet]` sur le GitLab privé Nexora (https://pc4.tail0c55ff.ts.net, réseau Tailscale).

## Où vit le travail
- Le développement se passe sur GitLab, dans ce dépôt. Une branche par tâche, une merge request par livraison.
- Tests et expériences sur pc1 ou pc6 : dossier jetable, supprimé dès l'expérience terminée (le résultat utile est commité, pas le dossier).
- Tout ce qui est Nexora vit sur pc5. Rien de durable ne reste sur pc1/pc6.

## Discipline de ressources
- Pas d'allocation démesurée (RAM, VRAM, disque, processus) : dimensionner d'abord, mesurer, puis monter.
- Chaque fichier créé a un propriétaire (qui l'a produit et pourquoi) et une durée de conservation. Sans les deux : ne pas le créer.
- Nettoyer après chaque expérience : processus arrêtés, caches, venv, modèles, archives temporaires. Ne jamais `pkill -f` (cibler un PID).
- Un volume de données ou un modèle ne va jamais dans Git.

## Sécurité
- Aucun secret dans le dépôt (jeton, mot de passe, clé, `.env`). Les secrets passent par les variables CI (`ci_var_set`) ou un fichier local hors Git.
- Ne jamais afficher ni copier un jeton dans un journal, un message de commit ou une réponse.
- Pas de force-push. Pas de suppression de branche protégée. Les actions destructives demandent `confirm: true`.

## Façon de travailler
- Commits en français, à l'impératif ou au passé simple et clair, avec le trailer de co-auteur de l'agent.
- Avant de reprendre : `git fetch`, lire l'état distant, intégrer sans écraser.
- Après chaque tranche utile : commit, push de la branche, MR vers la branche par défaut. Ne déclarer « synchronisé » qu'après vérification du SHA distant.
- Outils : le serveur MCP `gitspace` (project_create, commit_files, mr_create, mr_merge...) plutôt que des scripts ad hoc.

## Reprise
Lire d'abord README.md, puis docs/ (état, décisions, blocages). Consigner chaque blocage dans docs/ avec la prochaine action.
```

### 4.3 Squelette CI

Le fichier `.gitlab-ci.yml` déposé par `scaffold.ci` ne contrôle que l'hygiène du dépôt (fichiers sensibles, fichiers de plus de 5 Mo) ; aucun déploiement. À adapter au projet.

```yaml
# Squelette CI Nexora — à adapter au projet. Aucun déploiement implicite.
stages: [controle]

controle-hygiene:
  stage: controle
  script:
    - echo "Contrôle d'hygiène du dépôt"
    - test -z "$(git ls-files | grep -E '(^|/)\.env(\.|$)|\.pem$|id_rsa' || true)" || { echo "Fichier sensible versionné"; exit 1; }
    - test -z "$(git ls-files -z | xargs -0 -r du -k 2>/dev/null | awk '$1 > 5120' | head -1)" || { echo "Fichier de plus de 5 Mo versionné"; exit 1; }
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## 5. Passage à Gitspace plus tard

1. GitLab reste la source de continuité tant que Gitspace n'a pas passé son contrôle de sécurité (point 2.1).
2. L'adaptateur Forgejo de `gitspace-mcp` se branche sans changer les noms d'outils ; les agents gardent les mêmes messages.
3. Pendant la transition : `project_export` (sauvegarde) et `mirror_set` (réplication poussée GitLab vers Gitspace), puis bascule du remote des dépôts.
