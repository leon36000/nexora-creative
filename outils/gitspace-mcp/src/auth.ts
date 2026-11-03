// Résolution du jeton, sans jamais l'écrire ni l'afficher.
// Ordre : GITSPACE_TOKEN (env) -> ~/.config/gitspace/token (0600) -> `git credential fill`.
import { execFileSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { createInterface } from "node:readline";

export const DEFAULT_URL = "https://pc4.tail0c55ff.ts.net";
export const TOKEN_FILE = join(process.env.XDG_CONFIG_HOME || join(homedir(), ".config"), "gitspace", "token");

export function baseUrl(): string {
  return (process.env.GITSPACE_URL || DEFAULT_URL).replace(/\/+$/, "");
}

export type TokenSource = "env" | "fichier" | "git-credential";

export function resolveToken(): { token: string; source: TokenSource } {
  const env = process.env.GITSPACE_TOKEN?.trim();
  if (env) return { token: env, source: "env" };
  if (existsSync(TOKEN_FILE)) {
    const mode = statSync(TOKEN_FILE).mode & 0o077;
    if (mode !== 0) throw new Error(`${TOKEN_FILE} est lisible par d'autres utilisateurs : exécute « chmod 600 ${TOKEN_FILE} ».`);
    const t = readFileSync(TOKEN_FILE, "utf8").trim();
    if (t) return { token: t, source: "fichier" };
  }
  const host = new URL(baseUrl());
  const cwds = [process.env.GITSPACE_CREDENTIAL_REPO, process.cwd(), homedir()].filter(Boolean) as string[];
  for (const cwd of cwds) {
    try {
      const out = execFileSync("git", ["credential", "fill"], {
        cwd, input: `protocol=${host.protocol.replace(":", "")}\nhost=${host.host}\n\n`,
        encoding: "utf8", timeout: 10000, env: { ...process.env, GIT_TERMINAL_PROMPT: "0" }, stdio: ["pipe", "pipe", "ignore"],
      });
      const m = /^password=(.+)$/m.exec(out);
      if (m?.[1]) return { token: m[1], source: "git-credential" };
    } catch { /* essai suivant */ }
  }
  throw new Error(
    "Aucun jeton GitLab disponible. Le fondateur doit exécuter UNE fois : « node <dossier>/dist/index.js login » " +
      "(il colle un jeton d'accès personnel de portée « api » créé dans GitLab > Préférences > Jetons d'accès).",
  );
}

/** `gitspace-mcp login` : demande le jeton sur le terminal sans écho et le range en 0600. */
export async function login(): Promise<void> {
  if (!process.stdin.isTTY) throw new Error("`login` doit être lancé dans un terminal interactif.");
  console.error(`Colle ton jeton d'accès personnel GitLab (portée « api ») pour ${baseUrl()} puis Entrée (rien ne s'affiche) :`);
  const rl = createInterface({ input: process.stdin, output: process.stderr, terminal: true });
  (rl as any)._writeToOutput = () => {};
  const token: string = await new Promise((res) => rl.question("", (a) => res(a.trim())));
  rl.close();
  if (!token) throw new Error("Jeton vide : rien n'a été enregistré.");
  const r = await fetch(`${baseUrl()}/api/v4/user`, { headers: { "PRIVATE-TOKEN": token } });
  if (!r.ok) throw new Error(`GitLab a refusé ce jeton (HTTP ${r.status}). Vérifie la portée « api » et la date d'expiration.`);
  const u: any = await r.json();
  mkdirSync(dirname(TOKEN_FILE), { recursive: true, mode: 0o700 });
  writeFileSync(TOKEN_FILE, token + "\n", { mode: 0o600 });
  chmodSync(TOKEN_FILE, 0o600);
  console.error(`OK : connecté en tant que « ${u.username} », jeton rangé dans ${TOKEN_FILE} (0600).`);
}
