#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { baseUrl, login, resolveToken, TOKEN_FILE } from "./auth.js";
import { registerSecret, render, scrub, scrubText } from "./guard.js";
import { GitspaceError, type GitProvider } from "./provider.js";
import { createGitlabProvider } from "./providers/gitlab.js";
import { createForgejoProvider } from "./providers/forgejo.js";
import { TOOLS, fullShape, runTool } from "./tools.js";

function makeProvider(): { p: GitProvider; source: string } {
  const { token, source } = resolveToken();
  registerSecret(token);
  const kind = (process.env.GITSPACE_PROVIDER || "gitlab").toLowerCase();
  return { p: kind === "forgejo" ? createForgejoProvider(baseUrl(), token) : createGitlabProvider(baseUrl(), token), source };
}

async function main() {
  const cmd = process.argv[2] || "serve";
  if (cmd === "login") return login();
  if (cmd === "doctor") {
    const { p, source } = makeProvider();
    const w: any = await p.whoami({});
    console.log(JSON.stringify({ provider: p.name, url: baseUrl(), source_du_jeton: source, utilisateur: w.user?.username, admin: w.user?.is_admin, portee: w.token?.scopes ?? w.token, outils: TOOLS.length, fichier_jeton: TOKEN_FILE }, null, 1));
    return;
  }
  if (cmd !== "serve") throw new Error(`Commande inconnue « ${cmd} » : serve (défaut), login, doctor.`);

  let cached: GitProvider | null = null;
  const provider = () => (cached ??= makeProvider().p);
  const server = new McpServer({ name: "gitspace", version: "0.1.0" }, { instructions: "Pilote le GitLab privé Nexora (aujourd'hui) puis Gitspace/Forgejo avec les mêmes outils. Projets en « groupe/projet ». Les actions destructives exigent confirm: true ; dry_run: true montre l'effet sans rien changer. Aucun secret n'est jamais renvoyé." });
  for (const t of TOOLS) {
    server.registerTool(t.name, { description: t.description, inputSchema: fullShape(t), annotations: { readOnlyHint: t.kind === "read", destructiveHint: t.kind === "destructive", idempotentHint: t.kind === "read" } }, async (args: any) => {
      try {
        const out = await runTool(provider(), t, args);
        return { content: [{ type: "text" as const, text: render(scrub(out, t.name === "file_read" ? ["content"] : [])) }] };
      } catch (e: any) {
        const msg = e instanceof GitspaceError ? e.message : `Erreur inattendue : ${e?.message || e}`;
        return { isError: true, content: [{ type: "text" as const, text: scrubText(msg) }] };
      }
    });
  }
  await server.connect(new StdioServerTransport());
  process.stderr.write(`[gitspace] prêt : ${TOOLS.length} outils, ${baseUrl()}\n`);
}

main().catch((e) => { console.error(scrubText(String(e?.message || e))); process.exit(1); });
