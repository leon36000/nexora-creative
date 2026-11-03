// Couche d'outils : indépendante du fournisseur (n'appelle que l'interface GitProvider).
import { z } from "zod";
import { GitspaceError, type GitProvider, type ProviderMethod } from "./provider.js";

const project = z.string().describe("Projet : chemin « groupe/projet » (ex. root/nexora-web) ou identifiant numérique");
const pg = { page: z.number().int().min(1).optional().describe("Page (défaut 1)"), per_page: z.number().int().min(1).max(100).optional().describe("Résultats par page (défaut 20, max 100)") };
const iid = z.number().int().describe("Numéro de la MR/issue dans le projet (le « !12 » ou « #12 »)");
const level = z.enum(["no_one", "developers", "maintainers", "admins"]);

export type ToolDef = {
  name: string; description: string; shape: z.ZodRawShape; method: ProviderMethod;
  kind: "read" | "write" | "destructive";
  /** décrit la cible pour dry_run / confirmation */
  preview?: (p: GitProvider, a: any) => Promise<unknown>;
  map?: (a: any) => any;
};

const R = "read" as const, W = "write" as const, D = "destructive" as const;
const fileAction = z.object({
  action: z.enum(["create", "update", "upsert", "delete", "move"]).describe("upsert = crée ou met à jour selon l'existence (le plus simple)"),
  path: z.string().describe("Chemin du fichier dans le dépôt (nouveau chemin pour move)"),
  content: z.string().optional().describe("Contenu texte (omis pour delete et move simple)"),
  encoding: z.enum(["text", "base64"]).optional().describe("base64 pour un fichier binaire"),
  previous_path: z.string().optional().describe("Ancien chemin (move uniquement)"),
  executable: z.boolean().optional().describe("Bit exécutable"),
});

export const TOOLS: ToolDef[] = [
  { name: "whoami", description: "Qui suis-je sur le serveur Git : utilisateur, droits, portée et expiration du jeton (jamais le jeton). À appeler en premier pour diagnostiquer un problème d'accès.", shape: {}, method: "whoami", kind: R },

  // Projets et groupes
  { name: "group_list", description: "Liste/recherche les groupes (namespaces) visibles.", shape: { search: z.string().optional(), ...pg }, method: "groupList", kind: R },
  { name: "group_create", description: "Crée un groupe (ou sous-groupe avec parent_id).", shape: { name: z.string(), path: z.string().optional(), parent_id: z.number().optional(), visibility: z.enum(["private", "internal", "public"]).optional(), description: z.string().optional() }, method: "groupCreate", kind: W },
  {
    name: "project_create",
    description: "Crée un projet prêt à l'emploi : privé par défaut, branche par défaut « main », README, branche par défaut protégée (push Maintainer, pas de force-push), et optionnellement AGENTS.md / .gitlab-ci.yml / .gitignore Nexora et une branche de travail.",
    shape: {
      name: z.string().describe("Nom lisible du projet"), path: z.string().optional().describe("Slug d'URL (défaut : dérivé du nom)"),
      namespace: z.string().optional().describe("Groupe ou utilisateur propriétaire, chemin complet (ex. nexora, root). Défaut : l'utilisateur du jeton"),
      description: z.string().optional(), visibility: z.enum(["private", "internal", "public"]).optional().describe("Défaut private"),
      default_branch: z.string().optional().describe("Défaut main"), readme: z.boolean().optional().describe("Initialiser avec un README (défaut true)"),
      topics: z.array(z.string()).optional(), work_branch: z.string().optional().describe("Crée aussi cette branche de travail (ex. developpement)"),
      protect_main: z.boolean().optional().describe("Protéger la branche par défaut (défaut true)"),
      scaffold: z.object({ agents_md: z.boolean().optional(), ci: z.boolean().optional(), gitignore: z.boolean().optional() }).optional().describe("Fichiers de départ Nexora"),
    },
    method: "projectCreate", kind: W,
  },
  { name: "project_list", description: "Liste/recherche les projets (par défaut ceux dont je suis membre, triés par activité récente). Avec group, liste les projets d'un groupe.", shape: { search: z.string().optional(), group: z.string().optional(), owned: z.boolean().optional(), membership: z.boolean().optional(), archived: z.boolean().optional(), order_by: z.enum(["last_activity_at", "name", "created_at"]).optional(), ...pg }, method: "projectList", kind: R },
  { name: "project_get", description: "Détails d'un projet : branche par défaut, visibilité, taille, URL de clone (sans identifiants).", shape: { project }, method: "projectGet", kind: R },
  { name: "project_update", description: "Modifie un projet (description, visibilité, branche par défaut, nom, topics) ou l'archive/désarchive (archived).", shape: { project, name: z.string().optional(), description: z.string().optional(), visibility: z.enum(["private", "internal", "public"]).optional(), default_branch: z.string().optional(), topics: z.array(z.string()).optional(), archived: z.boolean().optional() }, method: "projectUpdate", kind: W },
  {
    name: "project_delete", description: "SUPPRIME un projet. Exige confirm: true ET expected_path égal au chemin exact du projet. Utilise dry_run: true pour voir ce qui serait supprimé. permanent: true force la suppression définitive.",
    shape: { project, expected_path: z.string().describe("Chemin complet du projet à supprimer, pour éviter une erreur de cible"), permanent: z.boolean().optional() },
    method: "projectDelete", kind: D, preview: (p, a) => p.projectGet({ project: a.project }),
  },
  { name: "project_export", description: "Export complet du projet (dépôt, issues, MR...) : action start puis status. Sert à la migration vers Gitspace.", shape: { project, action: z.enum(["start", "status"]) }, method: "projectExport", kind: W },

  // Branches
  { name: "branch_list", description: "Liste les branches (protégée, par défaut, tête).", shape: { project, search: z.string().optional(), ...pg }, method: "branchList", kind: R },
  { name: "branch_create", description: "Crée une branche à partir de from (défaut : branche par défaut).", shape: { project, branch: z.string(), from: z.string().optional().describe("Branche, tag ou SHA de départ") }, method: "branchCreate", kind: W },
  { name: "branch_delete", description: "Supprime une branche (impossible sur une branche protégée : la déprotéger d'abord). Exige confirm: true.", shape: { project, branch: z.string() }, method: "branchDelete", kind: D, preview: (p, a) => p.branchList({ project: a.project, search: a.branch }) },
  { name: "branch_protect", description: "Protège une branche (remplace la protection existante). push/merge : no_one, developers, maintainers, admins. Force-push refusé par défaut.", shape: { project, branch: z.string(), push: level.optional().describe("Défaut maintainers"), merge: level.optional().describe("Défaut maintainers"), allow_force_push: z.boolean().optional() }, method: "branchProtect", kind: W },
  { name: "branch_unprotect", description: "Retire la protection d'une branche. Exige confirm: true.", shape: { project, branch: z.string() }, method: "branchUnprotect", kind: D },
  { name: "protected_list", description: "Liste les branches protégées et leurs règles.", shape: { project, ...pg }, method: "protectedList", kind: R },

  // Dépôt
  { name: "file_read", description: "Lit un fichier texte d'un dépôt à une référence (branche, tag, SHA). Renvoie aussi last_commit_id.", shape: { project, path: z.string(), ref: z.string().optional() }, method: "fileRead", kind: R },
  { name: "tree_list", description: "Liste les fichiers/dossiers d'un chemin (recursive: true pour tout l'arbre).", shape: { project, path: z.string().optional(), ref: z.string().optional(), recursive: z.boolean().optional(), ...pg }, method: "treeList", kind: R },
  { name: "diff", description: "Compare deux références (branches, tags, SHA) : commits et diffs par fichier. stat_only: true pour la seule liste des fichiers.", shape: { project, from: z.string(), to: z.string(), straight: z.boolean().optional(), stat_only: z.boolean().optional(), max_diff_chars: z.number().optional() }, method: "compare", kind: R },
  { name: "blame", description: "Qui a écrit quoi : plages de lignes, commit, auteur, date.", shape: { project, path: z.string(), ref: z.string().optional() }, method: "blame", kind: R },
  { name: "commit_list", description: "Historique des commits (filtres : branche, chemin, dates).", shape: { project, ref: z.string().optional(), path: z.string().optional(), since: z.string().optional(), until: z.string().optional(), ...pg }, method: "commitList", kind: R },
  { name: "commit_get", description: "Un commit (message, stats). diff: true pour les modifications.", shape: { project, sha: z.string(), diff: z.boolean().optional() }, method: "commitGet", kind: R },
  {
    name: "commit_files",
    description: "UN commit de plusieurs fichiers (créer, modifier, supprimer, déplacer) sur une branche, sans clone local. Crée la branche si elle n'existe pas (depuis start_branch ou la branche par défaut). expected_head protège contre un écrasement concurrent. Refuse tout contenu qui ressemble à un secret.",
    shape: { project, branch: z.string(), message: z.string().describe("Message de commit (en français)"), actions: z.array(fileAction).min(1), start_branch: z.string().optional(), expected_head: z.string().optional().describe("SHA attendu de la tête de la branche ; refus si elle a avancé"), author_name: z.string().optional(), author_email: z.string().optional() },
    method: "commitFiles", kind: W,
  },
  { name: "search_code", description: "Cherche du texte dans le code d'un projet (ou de tous les projets si project est omis).", shape: { project: project.optional(), query: z.string(), ref: z.string().optional(), ...pg }, method: "searchCode", kind: R },

  // Merge requests
  { name: "mr_list", description: "Liste les merge requests (défaut : ouvertes).", shape: { project, state: z.enum(["opened", "closed", "merged", "all"]).optional(), source_branch: z.string().optional(), target_branch: z.string().optional(), author: z.string().optional(), search: z.string().optional(), ...pg }, method: "mrList", kind: R },
  { name: "mr_get", description: "Détail d'une MR : état de fusion expliqué (detailed_merge_status), pipeline de tête, SHA. with_files: true pour la liste des fichiers.", shape: { project, iid, with_files: z.boolean().optional() }, method: "mrGet", kind: R },
  { name: "mr_create", description: "Ouvre une merge request (cible : branche par défaut). draft: true pour un brouillon.", shape: { project, source_branch: z.string(), target_branch: z.string().optional(), title: z.string(), description: z.string().optional(), draft: z.boolean().optional(), remove_source_branch: z.boolean().optional(), squash: z.boolean().optional(), labels: z.array(z.string()).optional() }, method: "mrCreate", kind: W },
  { name: "mr_update", description: "Modifie une MR (titre, description, cible, labels, brouillon) ou la ferme/rouvre (state_event: close | reopen).", shape: { project, iid, title: z.string().optional(), description: z.string().optional(), target_branch: z.string().optional(), labels: z.array(z.string()).optional(), draft: z.boolean().optional(), state_event: z.enum(["close", "reopen"]).optional(), squash: z.boolean().optional(), remove_source_branch: z.boolean().optional() }, method: "mrUpdate", kind: W },
  {
    name: "mr_merge",
    description: "Fusionne une MR en sécurité : vérifie qu'elle est ouverte et fusionnable (erreur expliquée sinon), fusionne en imposant le SHA relu (refus si la branche source a bougé). wait_pipeline: true attend la fin du pipeline (timeout_s, défaut 300). when_pipeline_succeeds: true délègue à GitLab.",
    shape: { project, iid, sha: z.string().optional().describe("SHA de tête attendu (défaut : celui relu à l'instant)"), wait_pipeline: z.boolean().optional(), timeout_s: z.number().optional(), when_pipeline_succeeds: z.boolean().optional(), squash: z.boolean().optional(), squash_commit_message: z.string().optional(), merge_commit_message: z.string().optional(), remove_source_branch: z.boolean().optional() },
    method: "mrMerge", kind: W,
  },

  // Commentaires
  { name: "note_add", description: "Ajoute un commentaire sur une MR (kind: mr), une issue (kind: issue) ou un commit (kind: commit, ref = SHA).", shape: { project, kind: z.enum(["mr", "issue", "commit"]).optional(), ref: z.union([z.number(), z.string()]).describe("Numéro de MR/issue, ou SHA du commit"), body: z.string() }, method: "noteAdd", kind: W },
  { name: "discussion_list", description: "Fils de discussion d'une MR ou issue, avec leur état résolu et la position dans le code. only_unresolved: true pour ce qui bloque.", shape: { project, kind: z.enum(["mr", "issue"]).optional(), iid, only_unresolved: z.boolean().optional(), ...pg }, method: "discussionList", kind: R },
  { name: "discussion_resolve", description: "Résout (ou rouvre avec resolved: false) un fil de discussion d'une MR, avec une réponse optionnelle.", shape: { project, iid, discussion_id: z.string(), resolved: z.boolean().optional(), reply: z.string().optional() }, method: "discussionResolve", kind: W },

  // Issues
  { name: "issue_list", description: "Liste les issues d'un projet (ou d'un groupe avec group).", shape: { project: project.optional(), group: z.string().optional(), state: z.enum(["opened", "closed", "all"]).optional(), labels: z.array(z.string()).optional(), search: z.string().optional(), assignee: z.string().optional(), ...pg }, method: "issueList", kind: R },
  { name: "issue_get", description: "Une issue avec sa description.", shape: { project, iid }, method: "issueGet", kind: R },
  { name: "issue_create", description: "Crée une issue.", shape: { project, title: z.string(), description: z.string().optional(), labels: z.array(z.string()).optional(), confidential: z.boolean().optional() }, method: "issueCreate", kind: W },
  { name: "issue_update", description: "Modifie/ferme/rouvre une issue (state_event: close | reopen).", shape: { project, iid, title: z.string().optional(), description: z.string().optional(), state_event: z.enum(["close", "reopen"]).optional(), labels: z.array(z.string()).optional(), add_labels: z.array(z.string()).optional(), remove_labels: z.array(z.string()).optional(), confidential: z.boolean().optional() }, method: "issueUpdate", kind: W },

  // CI
  { name: "pipeline_list", description: "Pipelines récents (filtres : branche, statut).", shape: { project, ref: z.string().optional(), status: z.string().optional(), sha: z.string().optional(), ...pg }, method: "pipelineList", kind: R },
  { name: "pipeline_get", description: "Un pipeline avec ses jobs (nom, étape, statut).", shape: { project, id: z.number(), include_jobs: z.boolean().optional() }, method: "pipelineGet", kind: R },
  { name: "pipeline_run", description: "Lance un pipeline sur une branche (défaut : branche par défaut) avec des variables optionnelles.", shape: { project, ref: z.string().optional(), variables: z.record(z.string(), z.string()).optional() }, method: "pipelineRun", kind: W },
  { name: "pipeline_action", description: "Relance (retry) ou annule (cancel) un pipeline.", shape: { project, id: z.number(), action: z.enum(["retry", "cancel"]) }, method: "pipelineAction", kind: W },
  { name: "job_list", description: "Jobs d'un pipeline (pipeline_id) ou du projet.", shape: { project, pipeline_id: z.number().optional(), scope: z.string().optional().describe("failed, success, running..."), ...pg }, method: "jobList", kind: R },
  { name: "job_log", description: "Fin du journal d'un job (tail_lines, défaut 200). Les secrets sont masqués.", shape: { project, job_id: z.number(), tail_lines: z.number().optional() }, method: "jobLog", kind: R },

  // Tags et releases
  { name: "tag_list", description: "Liste les tags.", shape: { project, search: z.string().optional(), ...pg }, method: "tagList", kind: R },
  { name: "tag_create", description: "Crée un tag sur ref (défaut : branche par défaut).", shape: { project, tag: z.string(), ref: z.string().optional(), message: z.string().optional() }, method: "tagCreate", kind: W },
  { name: "tag_delete", description: "Supprime un tag. Exige confirm: true.", shape: { project, tag: z.string() }, method: "tagDelete", kind: D },
  { name: "release_list", description: "Liste les releases.", shape: { project, ...pg }, method: "releaseList", kind: R },
  { name: "release_create", description: "Publie une release sur un tag existant (ou crée le tag depuis ref).", shape: { project, tag: z.string(), name: z.string().optional(), description: z.string().optional(), ref: z.string().optional() }, method: "releaseCreate", kind: W },

  // Droits
  { name: "member_list", description: "Membres d'un projet (ou d'un groupe avec group) et leur rôle.", shape: { project: project.optional(), group: z.string().optional(), ...pg }, method: "memberList", kind: R },
  { name: "member_set", description: "Ajoute ou change le rôle d'un utilisateur sur un projet/groupe : guest, reporter, developer, maintainer, owner.", shape: { project: project.optional(), group: z.string().optional(), user: z.string().describe("Nom d'utilisateur GitLab"), access: z.enum(["guest", "reporter", "developer", "maintainer", "owner"]), expires_at: z.string().optional().describe("AAAA-MM-JJ") }, method: "memberSet", kind: W },
  { name: "member_remove", description: "Retire un membre. Exige confirm: true.", shape: { project: project.optional(), group: z.string().optional(), user: z.string() }, method: "memberRemove", kind: D },

  // Secrets CI, webhooks, miroirs
  { name: "ci_var_list", description: "Variables CI : NOMS et réglages seulement, jamais les valeurs.", shape: { project, ...pg }, method: "ciVarList", kind: R },
  { name: "ci_var_set", description: "Crée/remplace une variable CI. La valeur est en écriture seule (protégée et masquée par défaut) et n'est jamais relue ni renvoyée.", shape: { project, key: z.string(), value: z.string(), protected: z.boolean().optional(), masked: z.boolean().optional(), environment_scope: z.string().optional(), variable_type: z.enum(["env_var", "file"]).optional() }, method: "ciVarSet", kind: W },
  { name: "ci_var_delete", description: "Supprime une variable CI. Exige confirm: true.", shape: { project, key: z.string(), environment_scope: z.string().optional() }, method: "ciVarDelete", kind: D },
  { name: "webhook_list", description: "Webhooks du projet (URL sans identifiants, événements).", shape: { project, ...pg }, method: "webhookList", kind: R },
  { name: "webhook_create", description: "Crée un webhook. events parmi push, merge_requests, issues, pipeline, tag_push, note, job. secret_token en écriture seule.", shape: { project, url: z.string(), events: z.array(z.enum(["push", "merge_requests", "issues", "pipeline", "tag_push", "note", "job"])).optional(), secret_token: z.string().optional(), enable_ssl_verification: z.boolean().optional() }, method: "webhookCreate", kind: W },
  { name: "webhook_delete", description: "Supprime un webhook. Exige confirm: true.", shape: { project, hook_id: z.number() }, method: "webhookDelete", kind: D },
  { name: "mirror_list", description: "Miroirs de dépôt sortants (push) du projet, avec leur dernier statut. Sert à répliquer vers Gitspace.", shape: { project, ...pg }, method: "mirrorList", kind: R },
  { name: "mirror_set", description: "Ajoute un miroir sortant (push) vers une autre forge. L'URL peut contenir les identifiants : ils sont masqués ensuite.", shape: { project, url: z.string(), enabled: z.boolean().optional(), only_protected_branches: z.boolean().optional(), keep_divergent_refs: z.boolean().optional() }, method: "mirrorSet", kind: W },
  { name: "mirror_delete", description: "Supprime un miroir. Exige confirm: true.", shape: { project, mirror_id: z.number() }, method: "mirrorDelete", kind: D },
];

/** Ajoute dry_run/confirm aux outils qui modifient. */
export function fullShape(t: ToolDef): z.ZodRawShape {
  const s: any = { ...t.shape };
  if (t.kind !== "read") s.dry_run = z.boolean().optional().describe("true = ne rien faire, montrer ce qui serait fait");
  if (t.kind === "destructive") s.confirm = z.boolean().optional().describe("DOIT valoir true pour exécuter cette action destructive");
  return s;
}

export async function runTool(p: GitProvider, t: ToolDef, args: any): Promise<unknown> {
  const { dry_run, confirm, ...a } = args || {};
  if (t.kind === "destructive" && t.name === "project_delete" && a.expected_path !== undefined) {
    const proj: any = await p.projectGet({ project: a.project });
    if (proj.path_with_namespace !== a.expected_path) throw new GitspaceError(`expected_path « ${a.expected_path} » ≠ projet ciblé « ${proj.path_with_namespace} »`, 400, "corrige expected_path ou project : rien n'a été supprimé");
  }
  if (dry_run) {
    return { dry_run: true, tool: t.name, action: "aucune modification effectuée", args: a, cible: t.preview ? await t.preview(p, a).catch((e: any) => `introuvable : ${e.message}`) : undefined, pour_executer: t.kind === "destructive" ? "relance sans dry_run, avec confirm: true" : "relance sans dry_run" };
  }
  if (t.kind === "destructive" && confirm !== true) {
    throw new GitspaceError(`« ${t.name} » est destructif : confirm: true manquant`, 400, "relis la cible avec dry_run: true, puis relance avec confirm: true");
  }
  return (p as any)[t.method](t.map ? t.map(a) : a);
}
