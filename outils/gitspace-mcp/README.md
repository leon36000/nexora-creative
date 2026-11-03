# gitspace-mcp

Serveur MCP (stdio, TypeScript) qui donne aux agents (Codex, Claude Code...) des outils **naturels** pour piloter le GitLab privé Nexora (`https://pc4.tail0c55ff.ts.net`) : créer un projet prêt à l'emploi, committer plusieurs fichiers d'un coup, ouvrir et fusionner une MR en sécurité, protéger des branches, gérer variables CI, webhooks, miroirs, membres.
Il comble les manques du serveur MCP intégré de GitLab (`/api/v4/mcp`, qui n'a ni création/suppression de projet, ni protection de branche, ni membres, ni variables CI, ni webhooks) et il **ne demande pas d'OAuth**.

Il est conçu pour la bascule vers **Gitspace (Forgejo)** : les outils ne parlent qu'à une interface (`src/provider.ts`), seul l'adaptateur change.

## Installation (une fois)

```bash
cd outils/gitspace-mcp
npm ci && npm run build        # produit dist/
node dist/index.js doctor      # vérifie l'accès : utilisateur, portée du jeton, nombre d'outils
```

Déjà déclaré sur cette machine : `~/.codex/config.toml` (`[mcp_servers.gitspace]`) et Claude Code (portée utilisateur, `claude mcp list`).

## Authentification (aucun secret dans un fichier de config ni dans Git)

Ordre de résolution du jeton :

1. variable `GITSPACE_TOKEN` (si tu en as vraiment besoin) ;
2. fichier `~/.config/gitspace/token` (mode 0600), créé par `login` ;
3. identifiants Git déjà enregistrés pour `pc4.tail0c55ff.ts.net` (`git credential fill`, lancé depuis `GITSPACE_CREDENTIAL_REPO`, par défaut le dossier courant). C'est ce qui marche aujourd'hui sans rien configurer : le jeton de l'agent `agent-nexora-workstudio-web` (portée `api`, compte administrateur).

**Recommandé (étape à faire par le fondateur, 2 minutes)** : un jeton à son nom, avec expiration, au lieu du jeton partagé de l'agent.

1. GitLab > ton avatar > *Préférences* > *Jetons d'accès* > *Ajouter un nouveau jeton*.
2. Nom `gitspace-mcp`, expiration dans 90 jours, portée **api** uniquement. Copie le jeton (il ne s'affiche qu'une fois).
3. Dans un terminal : `node outils/gitspace-mcp/dist/index.js login`, colle le jeton (rien ne s'affiche), Entrée.
   La commande teste le jeton puis l'écrit dans `~/.config/gitspace/token` (0600). Rien n'est écrit ailleurs.
4. `node outils/gitspace-mcp/dist/index.js doctor` doit indiquer `source_du_jeton: fichier`.

Révoquer : supprimer le jeton dans GitLab, puis `rm ~/.config/gitspace/token`.

## Variables d'environnement

| Variable | Rôle | Défaut |
|---|---|---|
| `GITSPACE_URL` | adresse de la forge | `https://pc4.tail0c55ff.ts.net` |
| `GITSPACE_PROVIDER` | `gitlab` ou `forgejo` | `gitlab` |
| `GITSPACE_DEFAULT_NAMESPACE` | groupe/utilisateur des nouveaux projets | utilisateur du jeton (sur cette machine : `root`) |
| `GITSPACE_CREDENTIAL_REPO` | dossier d'où lire `git credential` | dossier courant |
| `GITSPACE_RATE`, `GITSPACE_BURST` | requêtes/s et rafale | 8 et 16 |
| `GITSPACE_MAX_OUTPUT` | taille max d'une réponse | 60000 caractères |

## Les 58 outils

Lecture : `whoami`, `group_list`, `project_list`, `project_get`, `branch_list`, `protected_list`, `file_read`, `tree_list`, `diff`, `blame`, `commit_list`, `commit_get`, `search_code`, `mr_list`, `mr_get`, `discussion_list`, `issue_list`, `issue_get`, `pipeline_list`, `pipeline_get`, `job_list`, `job_log`, `tag_list`, `release_list`, `member_list`, `ci_var_list` (noms seulement), `webhook_list`, `mirror_list`.

Écriture (acceptent `dry_run: true`) : `group_create`, `project_create`, `project_update`, `project_export`, `branch_create`, `branch_protect`, `commit_files`, `mr_create`, `mr_update`, `mr_merge`, `note_add`, `discussion_resolve`, `issue_create`, `issue_update`, `pipeline_run`, `pipeline_action`, `tag_create`, `release_create`, `member_set`, `ci_var_set` (valeur en écriture seule), `webhook_create`, `mirror_set`.

Destructifs (exigent `confirm: true`, acceptent `dry_run: true`) : `project_delete` (exige aussi `expected_path`), `branch_delete`, `branch_unprotect`, `tag_delete`, `member_remove`, `ci_var_delete`, `webhook_delete`, `mirror_delete`.

Conventions : `project` = `groupe/projet` ou identifiant numérique ; listes paginées (`page`, `per_page`, réponse `{items, page, next_page}`) ; erreurs en français avec la correction à appliquer.

Points d'attention :
- `project_create` : privé, `main`, README, branche protégée (push Maintainer, merge Developer, pas de force-push), option `scaffold` (`AGENTS.md`, `.gitlab-ci.yml`, `.gitignore` Nexora) et `work_branch`. Si le compte du jeton est administrateur sans être membre du groupe cible, il s'ajoute Maintainer (sinon GitLab refuse de fusionner).
- `commit_files` : actions `create`, `update`, `upsert` (le plus simple), `delete`, `move` en un seul commit ; `expected_head` refuse l'écriture si la branche a avancé ; refuse tout contenu qui ressemble à un secret.
- `mr_merge` : impose le SHA relu, explique pourquoi une MR n'est pas fusionnable, `wait_pipeline` attend le pipeline.
- Rien de secret n'est renvoyé : champs `token`, `value`, `password`, `import_url`... masqués, motifs `glpat-`, clés privées et URL avec mot de passe remplacés par `[SECRET]` dans toutes les sorties.

## Test de bout en bout

`npm run smoke` crée `root/zz-test-gitspace-mcp`, enchaîne branche, commit multi-fichiers, MR, fusion, protection, variable CI, balise, refus sans `confirm`, puis **supprime le projet** (31 vérifications). Dernier passage : 31 OK, 0 KO.

## Basculer vers Gitspace (Forgejo)

1. Écrire `src/providers/forgejo.ts` (squelette fourni : chaque méthode renvoie « non implémenté ») : mêmes noms de méthodes que `PROVIDER_METHODS`.
2. `GITSPACE_PROVIDER=forgejo`, `GITSPACE_URL=<adresse Gitspace>`, `login` avec un jeton Forgejo. Les noms d'outils ne changent pas : les agents n'ont rien à réapprendre.
3. Migrer les dépôts : `project_export` (sauvegarde GitLab) et `mirror_set` (réplication poussée vers Gitspace) pendant la transition.

Correspondance GitLab v4 vers Forgejo `/api/v1` pour l'adaptateur :

| Méthodes | GitLab | Forgejo |
|---|---|---|
| projectCreate/List/Get/Update/Delete | `/projects` | `POST /user/repos`, `/orgs/{org}/repos`, `/repos/search`, `/repos/{o}/{r}` |
| branchCreate/List/Delete | `/repository/branches` | `/repos/{o}/{r}/branches` (`old_branch_name`) |
| branchProtect/Unprotect | `/protected_branches` | `/repos/{o}/{r}/branch_protections` |
| commitFiles | `POST /repository/commits` (actions) | `POST /repos/{o}/{r}/contents` (changement de fichiers en lot, `files[]` avec `operation`) |
| fileRead / treeList | `/repository/files`, `/tree` | `/contents/{path}`, `/git/trees/{sha}` |
| compare / commits | `/repository/compare`, `/commits` | `/compare/{base}...{head}`, `/commits` |
| mr* | `/merge_requests` | `/pulls` (`POST /pulls/{n}/merge`, `head_commit_id` = contrôle du SHA) |
| issues, notes | `/issues`, `/notes` | `/issues`, `/issues/{n}/comments` |
| pipelines, jobs | `/pipelines`, `/jobs` | `/actions/runs`, `/actions/jobs` (selon version) |
| tags, releases | `/repository/tags`, `/releases` | `/tags`, `/releases` |
| membres | `/members` | `/collaborators`, `/orgs/{org}/teams` |
| variables CI | `/variables` | `/actions/variables` et `/actions/secrets` (écriture seule) |
| webhooks | `/hooks` | `/hooks` |
| miroirs | `/remote_mirrors` | `/push_mirrors` |

Limite connue côté Forgejo, relevée par l'agent Gitspace : pas de précondition atomique « la base n'a pas bougé » sur la fusion ; le contrôle `head_commit_id` ne couvre que la tête de la PR.
