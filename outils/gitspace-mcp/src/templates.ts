// Modèles injectés par project_create (scaffold) et repris dans docs/CODEX-ET-GITLAB.md.
export function renderTemplate(t: string, ctx: Record<string, string>): string {
  return t.replace(/\{\{(\w+)\}\}/g, (_, k) => ctx[k] ?? "");
}

export const AGENTS_MD = `# AGENTS.md — {{nom}}

{{description}}

Dépôt : \`{{projet}}\` sur le GitLab privé Nexora (https://pc4.tail0c55ff.ts.net, réseau Tailscale).

## Où vit le travail
- Le développement se passe sur GitLab, dans ce dépôt. Une branche par tâche, une merge request par livraison.
- Tests et expériences sur pc1 ou pc6 : dossier jetable, supprimé dès l'expérience terminée (le résultat utile est commité, pas le dossier).
- Tout ce qui est Nexora vit sur pc5. Rien de durable ne reste sur pc1/pc6.

## Discipline de ressources
- Pas d'allocation démesurée (RAM, VRAM, disque, processus) : dimensionner d'abord, mesurer, puis monter.
- Chaque fichier créé a un propriétaire (qui l'a produit et pourquoi) et une durée de conservation. Sans les deux : ne pas le créer.
- Nettoyer après chaque expérience : processus arrêtés, caches, venv, modèles, archives temporaires. Ne jamais \`pkill -f\` (cibler un PID).
- Un volume de données ou un modèle ne va jamais dans Git.

## Sécurité
- Aucun secret dans le dépôt (jeton, mot de passe, clé, \`.env\`). Les secrets passent par les variables CI (\`ci_var_set\`) ou un fichier local hors Git.
- Ne jamais afficher ni copier un jeton dans un journal, un message de commit ou une réponse.
- Pas de force-push. Pas de suppression de branche protégée. Les actions destructives demandent \`confirm: true\`.

## Façon de travailler
- Commits en français, à l'impératif ou au passé simple et clair, avec le trailer de co-auteur de l'agent.
- Avant de reprendre : \`git fetch\`, lire l'état distant, intégrer sans écraser.
- Après chaque tranche utile : commit, push de la branche, MR vers la branche par défaut. Ne déclarer « synchronisé » qu'après vérification du SHA distant.
- Outils : le serveur MCP \`gitspace\` (project_create, commit_files, mr_create, mr_merge...) plutôt que des scripts ad hoc.

## Reprise
Lire d'abord README.md, puis docs/ (état, décisions, blocages). Consigner chaque blocage dans docs/ avec la prochaine action.
`;

export const CI_SKELETON = `# Squelette CI Nexora — à adapter au projet. Aucun déploiement implicite.
stages: [controle]

controle-hygiene:
  stage: controle
  script:
    - echo "Contrôle d'hygiène du dépôt"
    - test -z "$(git ls-files | grep -E '(^|/)\\.env(\\.|$)|\\.pem$|id_rsa' || true)" || { echo "Fichier sensible versionné"; exit 1; }
    - test -z "$(git ls-files -z | xargs -0 -r du -k 2>/dev/null | awk '$1 > 5120' | head -1)" || { echo "Fichier de plus de 5 Mo versionné"; exit 1; }
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
`;

export const GITIGNORE = `.env
.env.*
*.pem
*.key
node_modules/
target/
dist/
__pycache__/
.venv/
*.log
*.gguf
*.safetensors
`;
