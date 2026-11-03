// Test réel de bout en bout via le protocole MCP (stdio). Crée puis SUPPRIME un projet jetable.
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const NS = process.env.SMOKE_NAMESPACE || "root";
const PROJECT = `${NS}/zz-test-gitspace-mcp`;
const t = new StdioClientTransport({ command: "node", args: ["dist/index.js"], env: { ...process.env }, stderr: "ignore" });
const c = new Client({ name: "smoke", version: "0" });
await c.connect(t);
const tools = (await c.listTools()).tools;
console.log("outils exposés :", tools.length);
let ok = 0, ko = 0;
async function call(name, args, expectError = false) {
  const r = await c.callTool({ name, arguments: args });
  const text = r.content?.[0]?.text ?? "";
  const pass = expectError ? !!r.isError : !r.isError;
  console.log(pass ? "OK " : "KO ", name, expectError ? "(erreur attendue)" : "", pass ? "" : text.slice(0, 300));
  pass ? ok++ : ko++;
  try { return JSON.parse(text); } catch { return text; }
}
try {
  await call("whoami", {});
  const l = await call("project_list", { per_page: 3 });
  console.log("  projets listés :", l.items?.length);
  await c.callTool({ name: "project_delete", arguments: { project: PROJECT, expected_path: PROJECT, confirm: true, permanent: true } }); // nettoyage d'un éventuel reste
  const created = await call("project_create", { name: "zz-test-gitspace-mcp", namespace: NS, description: "Projet jetable de test de gitspace-mcp", work_branch: "developpement", scaffold: { agents_md: true, ci: true, gitignore: true } });
  console.log("  créé :", created.path_with_namespace, created.applied);
  await call("branch_create", { project: PROJECT, branch: "feat/test", from: "main" });
  const cm = await call("commit_files", { project: PROJECT, branch: "feat/test", message: "Ajoute, modifie et déplace des fichiers de test", actions: [
    { action: "upsert", path: "docs/a.md", content: "# A\n" }, { action: "upsert", path: "src/b.txt", content: "b\n" },
    { action: "upsert", path: "README.md", content: "# zz-test\nmodifié par le test\n" }] });
  await call("commit_files", { project: PROJECT, branch: "feat/test", message: "Déplace et supprime", actions: [{ action: "move", previous_path: "src/b.txt", path: "src/c.txt" }, { action: "delete", path: "docs/a.md" }] });
  await call("commit_files", { project: PROJECT, branch: "feat/test", message: "secret", actions: [{ action: "upsert", path: "x.txt", content: "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----" }] }, true);
  await call("file_read", { project: PROJECT, path: "src/c.txt", ref: "feat/test" });
  await call("tree_list", { project: PROJECT, ref: "feat/test", recursive: true });
  await call("diff", { project: PROJECT, from: "main", to: "feat/test", stat_only: true });
  await call("blame", { project: PROJECT, path: "README.md", ref: "feat/test" });
  const mr = await call("mr_create", { project: PROJECT, source_branch: "feat/test", title: "Test : fichiers", description: "MR de test", remove_source_branch: false });
  await call("note_add", { project: PROJECT, kind: "mr", ref: mr.iid, body: "Commentaire de test" });
  await call("discussion_list", { project: PROJECT, iid: mr.iid });
  await call("mr_get", { project: PROJECT, iid: mr.iid });
  await call("mr_merge", { project: PROJECT, iid: mr.iid, wait_pipeline: false });
  await call("branch_protect", { project: PROJECT, branch: "developpement", push: "no_one", merge: "maintainers" });
  await call("protected_list", { project: PROJECT });
  await call("ci_var_set", { project: PROJECT, key: "ZZ_TEST", value: "valeur-secrete-de-test" });
  const vars = await call("ci_var_list", { project: PROJECT });
  if (JSON.stringify(vars).includes("valeur-secrete")) { console.log("KO  la valeur d'une variable CI a fuité"); ko++; }
  await call("ci_var_delete", { project: PROJECT, key: "ZZ_TEST" }, true);          // refusé sans confirm
  await call("ci_var_delete", { project: PROJECT, key: "ZZ_TEST", confirm: true });
  await call("tag_create", { project: PROJECT, tag: "v0.0.1", message: "test" });
  await call("branch_delete", { project: PROJECT, branch: "feat/test", dry_run: true });
  await call("branch_delete", { project: PROJECT, branch: "feat/test" }, true);        // refusé sans confirm
  await call("branch_delete", { project: PROJECT, branch: "feat/test", confirm: true });
  await call("pipeline_list", { project: PROJECT });
  await call("search_code", { project: PROJECT, query: "modifié" });
  await call("member_list", { project: PROJECT });
  await call("project_delete", { project: PROJECT, expected_path: "root/autre-chose", confirm: true }, true);
} finally {
  await call("project_delete", { project: PROJECT, expected_path: PROJECT, confirm: true, permanent: true });
  await c.close();
  console.log(`\nRésultat : ${ok} OK, ${ko} KO`);
  process.exit(ko ? 1 : 0);
}
