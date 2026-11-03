// Squelette de l'adaptateur Gitspace (Forgejo). À remplir le jour de la bascule :
// API Forgejo = /api/v1 (compatible Gitea). Table de correspondance dans README.md.
import { GitspaceError, PROVIDER_METHODS, type GitProvider } from "../provider.js";

export function createForgejoProvider(_baseUrl: string, _token: string): GitProvider {
  const p: any = { name: "forgejo" };
  for (const m of PROVIDER_METHODS) {
    p[m] = async () => {
      throw new GitspaceError(
        `L'adaptateur Forgejo n'implémente pas encore « ${m} ».`, 501,
        "Implémente cette méthode dans src/providers/forgejo.ts (voir la table de correspondance du README) ou utilise GITSPACE_PROVIDER=gitlab.",
      );
    };
  }
  return p as GitProvider;
}
