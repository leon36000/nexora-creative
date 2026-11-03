// Interface commune. La couche d'outils (tools.ts) n'appelle QUE ces méthodes :
// passer de GitLab à Gitspace (Forgejo) = écrire un autre adaptateur, les outils restent identiques.
export const PROVIDER_METHODS = [
  "whoami",
  "groupList", "groupCreate",
  "projectCreate", "projectList", "projectGet", "projectUpdate", "projectDelete", "projectExport",
  "branchList", "branchCreate", "branchDelete", "branchProtect", "branchUnprotect", "protectedList",
  "fileRead", "treeList", "compare", "blame", "commitList", "commitGet", "commitFiles", "searchCode",
  "mrList", "mrGet", "mrCreate", "mrUpdate", "mrMerge",
  "noteAdd", "discussionList", "discussionResolve",
  "issueList", "issueGet", "issueCreate", "issueUpdate",
  "pipelineList", "pipelineGet", "pipelineRun", "pipelineAction", "jobList", "jobLog",
  "tagList", "tagCreate", "tagDelete", "releaseList", "releaseCreate",
  "memberList", "memberSet", "memberRemove",
  "ciVarList", "ciVarSet", "ciVarDelete",
  "webhookList", "webhookCreate", "webhookDelete",
  "mirrorList", "mirrorSet", "mirrorDelete",
] as const;

export type ProviderMethod = (typeof PROVIDER_METHODS)[number];
export type GitProvider = { readonly name: string } & { [K in ProviderMethod]: (args: any) => Promise<any> };

export class GitspaceError extends Error {
  constructor(message: string, public status?: number, public hint?: string) {
    super(hint ? `${message} — ${hint}` : message);
  }
}
