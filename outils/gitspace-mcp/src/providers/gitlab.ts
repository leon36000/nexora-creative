// Adaptateur GitLab REST API v4 (GitLab auto-hébergé Nexora, PC4).
import { GitspaceError, type GitProvider } from "../provider.js";
import { RateLimiter, registerSecret } from "../guard.js";
import { AGENTS_MD, CI_SKELETON, GITIGNORE, renderTemplate } from "../templates.js";

type Q = Record<string, string | number | boolean | undefined | null>;
const LEVEL: Record<string, number> = { no_one: 0, guest: 10, reporter: 20, developer: 30, developers: 30, maintainer: 40, maintainers: 40, owner: 50, admins: 60 };
const pick = (o: any, keys: string[]) => Object.fromEntries(keys.filter((k) => o && o[k] !== undefined).map((k) => [k, o[k]]));
const enc = (s: string | number) => encodeURIComponent(String(s));
const stripUserinfo = (u: string) => String(u || "").replace(/(\/\/)[^/@]*@/, "$1");
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function createGitlabProvider(baseUrl: string, token: string): GitProvider {
  registerSecret(token);
  const limiter = new RateLimiter();
  const api = `${baseUrl}/api/v4`;

  async function req(method: string, path: string, o: { query?: Q; body?: any; text?: boolean; okStatuses?: number[] } = {}): Promise<{ data: any; headers: Headers; status: number }> {
    const url = new URL(api + path);
    for (const [k, v] of Object.entries(o.query || {})) if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    for (let attempt = 0; ; attempt++) {
      await limiter.take();
      let res: Response;
      try {
        res = await fetch(url, {
          method, signal: AbortSignal.timeout(60000),
          headers: { "PRIVATE-TOKEN": token, ...(o.body !== undefined ? { "Content-Type": "application/json" } : {}) },
          body: o.body !== undefined ? JSON.stringify(o.body) : undefined,
        });
      } catch (e: any) {
        throw new GitspaceError(`GitLab injoignable (${e?.message || e})`, 0, `vérifie Tailscale et ${baseUrl}`);
      }
      process.stderr.write(`[gitspace] ${method} ${path} -> ${res.status}\n`);
      if (res.status === 429 && attempt < 3) { await sleep(Math.min(30, Number(res.headers.get("retry-after") || 2)) * 1000); continue; }
      if (res.status >= 500 && attempt < 2 && method === "GET") { await sleep(1500); continue; }
      const raw = await res.text();
      if (res.ok || o.okStatuses?.includes(res.status)) {
        let data: any = raw;
        if (!o.text) { try { data = raw ? JSON.parse(raw) : null; } catch { data = raw; } }
        return { data, headers: res.headers, status: res.status };
      }
      let msg = raw.slice(0, 400);
      try { const j = JSON.parse(raw); msg = typeof j.message === "string" ? j.message : JSON.stringify(j.message ?? j.error ?? j); } catch { /* texte brut */ }
      const hints: Record<number, string> = {
        400: "paramètre invalide : relis le message ci-dessus",
        401: "jeton refusé ou expiré : le fondateur doit relancer « gitspace-mcp login »",
        403: "droits insuffisants pour cette action avec ce jeton (portée « api » et rôle Maintainer/Owner requis)",
        404: "introuvable (ou invisible pour ce jeton) : vérifie le chemin « groupe/projet », la branche ou l'identifiant",
        405: "action impossible dans l'état actuel (MR non fusionnable, branche protégée...)",
        406: "la branche source a changé ou n'est pas fusionnable : relis la MR (mr_get) puis réessaie",
        409: "conflit : l'objet existe déjà ou a été modifié entre-temps",
        422: "refusé par GitLab : valeur invalide ou règle de protection",
      };
      throw new GitspaceError(`GitLab ${method} ${path} a répondu ${res.status} : ${msg}`, res.status, hints[res.status]);
    }
  }
  const get = (p: string, query?: Q) => req("GET", p, { query }).then((r) => r.data);
  const page = async (p: string, a: any, extra: Q = {}, shape?: (x: any) => any) => {
    const per_page = Math.min(Number(a.per_page || 20), 100);
    const r = await req("GET", p, { query: { page: a.page || 1, per_page, ...extra } });
    const items = Array.isArray(r.data) ? r.data.map(shape || ((x: any) => x)) : r.data;
    return { items, page: Number(a.page || 1), next_page: r.headers.get("x-next-page") ? Number(r.headers.get("x-next-page")) : null };
  };
  const P = (a: any) => { if (!a.project) throw new GitspaceError("Argument « project » manquant", 400, "donne « groupe/projet » (ex. root/nexora-web) ou l'identifiant numérique"); return `/projects/${enc(a.project)}`; };
  const G = (a: any) => `/groups/${enc(a.group)}`;
  const ownerPath = (a: any) => (a.group && !a.project ? G(a) : P(a));

  const projShape = (x: any) => pick(x, ["id", "path_with_namespace", "description", "visibility", "default_branch", "archived", "empty_repo", "last_activity_at", "web_url", "http_url_to_repo", "topics", "statistics", "marked_for_deletion_on"]);
  const mrShape = (x: any) => pick(x, ["iid", "title", "state", "draft", "source_branch", "target_branch", "author", "sha", "merge_status", "detailed_merge_status", "has_conflicts", "web_url", "created_at", "updated_at", "merged_at", "labels", "squash", "head_pipeline", "description"]);
  const slim = (x: any) => (x && x.author ? { ...x, author: x.author.username } : x);
  const issueShape = (x: any) => slim(pick(x, ["iid", "title", "state", "labels", "author", "assignees", "web_url", "created_at", "updated_at", "description", "confidential"]));
  const pipeShape = (x: any) => pick(x, ["id", "status", "ref", "sha", "source", "web_url", "created_at", "updated_at", "duration", "detailed_status"]);
  const jobShape = (x: any) => pick(x, ["id", "name", "stage", "status", "allow_failure", "duration", "web_url", "failure_reason"]);

  async function defaultBranch(a: any): Promise<string> { return (await get(P(a))).default_branch || "main"; }
  async function branchHead(a: any, branch: string): Promise<string | null> {
    const r = await req("GET", `${P(a)}/repository/branches/${enc(branch)}`, { okStatuses: [404] });
    return r.status === 404 ? null : r.data.commit.id;
  }
  async function userId(username: string): Promise<number> {
    const u = await get("/users", { username: username.replace(/^@/, "") });
    if (!u?.length) throw new GitspaceError(`Utilisateur « ${username} » introuvable`, 404, "utilise le nom d'utilisateur GitLab exact (sans @)");
    return u[0].id;
  }
  const looksSecret = (s: string) => /glpat-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|https?:\/\/[^\s/:@]+:[^\s/@]{4,}@/.test(s);

  const self: GitProvider = {
    name: "gitlab",

    async whoami() {
      const u = await get("/user");
      const t = await req("GET", "/personal_access_tokens/self", { okStatuses: [401, 403, 404] });
      return { url: baseUrl, provider: "gitlab", user: pick(u, ["id", "username", "name", "state", "is_admin", "can_create_project", "can_create_group"]), token: t.status === 200 ? pick(t.data, ["name", "scopes", "expires_at"]) : "indisponible" };
    },

    groupList: (a) => page("/groups", a, { search: a.search }, (g) => pick(g, ["id", "full_path", "name", "visibility", "description", "web_url"])),
    async groupCreate(a) {
      const g = await req("POST", "/groups", { body: { name: a.name, path: a.path || a.name, parent_id: a.parent_id, visibility: a.visibility || "private", description: a.description } });
      return pick(g.data, ["id", "full_path", "web_url", "visibility"]);
    },

    async projectCreate(a) {
      const applied: string[] = [];
      let namespace_id: number | undefined;
      const wanted = a.namespace || process.env.GITSPACE_DEFAULT_NAMESPACE;
      if (wanted) {
        const ns = await get("/namespaces", { search: String(wanted).split("/").pop() });
        const hit = (ns || []).find((n: any) => n.full_path === wanted);
        if (!hit) throw new GitspaceError(`Namespace « ${wanted} » introuvable`, 404, "liste les groupes avec group_list ; le namespace est le chemin complet (ex. nexora ou root)");
        namespace_id = hit.id;
      }
      const default_branch = a.default_branch || "main";
      const created = (await req("POST", "/projects", { body: { name: a.name, path: a.path || undefined, namespace_id, description: a.description || "", visibility: a.visibility || "private", initialize_with_readme: a.readme !== false, default_branch, topics: a.topics } })).data;
      const ref = { project: created.id };
      applied.push(`projet créé : ${created.path_with_namespace}`);
      // Un administrateur qui n'est pas membre ne peut pas fusionner : on s'ajoute Maintainer si besoin.
      const me = await get("/user");
      const mem = await req("GET", `/projects/${created.id}/members/all/${me.id}`, { okStatuses: [404] });
      if (mem.status === 404) { await req("POST", `/projects/${created.id}/members`, { body: { user_id: me.id, access_level: 40 } }); applied.push(`${me.username} ajouté Maintainer (nécessaire pour fusionner)`); }
      const files: any[] = [];
      const ctx = { nom: a.name, description: a.description || "", groupe: created.namespace?.full_path || "", projet: created.path_with_namespace };
      const sc = a.scaffold || {};
      if (sc.agents_md) files.push({ action: "upsert", path: "AGENTS.md", content: renderTemplate(AGENTS_MD, ctx) });
      if (sc.ci) files.push({ action: "upsert", path: ".gitlab-ci.yml", content: CI_SKELETON });
      if (sc.gitignore) files.push({ action: "upsert", path: ".gitignore", content: GITIGNORE });
      // GitLab protège la branche par défaut sans push possible : on fixe d'abord la règle voulue (push Maintainer).
      await self.branchProtect({ ...ref, branch: default_branch, push: "maintainers", merge: "developers" });
      if (files.length) {
        await self.commitFiles({ ...ref, branch: default_branch, message: "Initialise le projet : AGENTS.md, CI et .gitignore [skip ci]", actions: files });
        applied.push(`fichiers : ${files.map((f) => f.path).join(", ")}`);
      }
      if (a.work_branch) { await self.branchCreate({ ...ref, branch: a.work_branch, from: default_branch }); applied.push(`branche de travail : ${a.work_branch}`); }
      if (a.protect_main !== false) applied.push(`${default_branch} protégée (push Maintainer, merge Developer, pas de force-push)`);
      else { await self.branchUnprotect({ ...ref, branch: default_branch }); applied.push(`${default_branch} laissée non protégée`); }
      return { ...projShape(created), applied, clone: created.http_url_to_repo };
    },
    projectList: (a) => a.group
      ? page(`${G(a)}/projects`, a, { search: a.search, include_subgroups: true, archived: a.archived }, projShape)
      : page("/projects", a, { search: a.search, membership: a.membership ?? false, owned: a.owned, archived: a.archived ?? false, order_by: a.order_by || "last_activity_at", simple: false }, projShape),
    async projectGet(a) { return projShape(await get(P(a), { statistics: true })); },
    async projectUpdate(a) {
      const body = pick(a, ["name", "description", "visibility", "default_branch", "topics"]);
      let out: any = null;
      if (Object.keys(body).length) out = (await req("PUT", P(a), { body })).data;
      if (a.archived === true) out = (await req("POST", `${P(a)}/archive`)).data;
      if (a.archived === false) out = (await req("POST", `${P(a)}/unarchive`)).data;
      if (!out) throw new GitspaceError("Rien à modifier", 400, "passe au moins un champ : description, visibility, default_branch, name, topics, archived");
      return projShape(out);
    },
    async projectDelete(a) {
      const p = await get(P(a));
      const id = p.id;
      if (!a.permanent) {
        await req("DELETE", `/projects/${id}`);
        return { deleted: p.path_with_namespace, permanent: false, note: "GitLab peut garder le projet en attente de suppression selon sa configuration ; ajoute permanent: true pour la suppression définitive" };
      }
      if (!p.marked_for_deletion_on && !p.marked_for_deletion_at) await req("DELETE", `/projects/${id}`);
      const after = await get(`/projects/${id}`, undefined).catch(() => null);
      if (after) await req("DELETE", `/projects/${id}`, { query: { permanently_remove: true, full_path: after.path_with_namespace } });
      return { deleted: p.path_with_namespace, permanent: true };
    },
    async projectExport(a) {
      if (a.action === "start") { await req("POST", `${P(a)}/export`); return { started: true, next: "appelle project_export avec action: status" }; }
      return pick(await get(`${P(a)}/export`), ["export_status", "_links", "created_at"]);
    },

    branchList: (a) => page(`${P(a)}/repository/branches`, a, { search: a.search }, (b) => ({ name: b.name, protected: b.protected, default: b.default, merged: b.merged, head: b.commit?.id, title: b.commit?.title, date: b.commit?.committed_date })),
    async branchCreate(a) {
      const ref = a.from || (await defaultBranch(a));
      const b = (await req("POST", `${P(a)}/repository/branches`, { query: { branch: a.branch, ref } })).data;
      return { branch: b.name, from: ref, head: b.commit?.id };
    },
    async branchDelete(a) { await req("DELETE", `${P(a)}/repository/branches/${enc(a.branch)}`); return { deleted: a.branch }; },
    async branchProtect(a) {
      const push = LEVEL[a.push || "maintainers"], merge = LEVEL[a.merge || "maintainers"], force = !!a.allow_force_push;
      const ex = await req("GET", `${P(a)}/protected_branches/${enc(a.branch)}`, { okStatuses: [404] });
      const r = ex.status === 404
        ? (await req("POST", `${P(a)}/protected_branches`, { body: { name: a.branch, push_access_level: push, merge_access_level: merge, allow_force_push: force } })).data
        : (await req("PATCH", `${P(a)}/protected_branches/${enc(a.branch)}`, { body: {
            allow_force_push: force,
            allowed_to_push: [...(ex.data.push_access_levels || []).map((l: any) => ({ id: l.id, _destroy: true })), { access_level: push }],
            allowed_to_merge: [...(ex.data.merge_access_levels || []).map((l: any) => ({ id: l.id, _destroy: true })), { access_level: merge }],
          } })).data;
      return { branch: r.name, push: a.push || "maintainers", merge: a.merge || "maintainers", allow_force_push: !!r.allow_force_push };
    },
    async branchUnprotect(a) { await req("DELETE", `${P(a)}/protected_branches/${enc(a.branch)}`); return { unprotected: a.branch }; },
    protectedList: (a) => page(`${P(a)}/protected_branches`, a, {}, (b) => ({ name: b.name, allow_force_push: b.allow_force_push, push: b.push_access_levels?.map((l: any) => l.access_level_description), merge: b.merge_access_levels?.map((l: any) => l.access_level_description) })),

    async fileRead(a) {
      const ref = a.ref || (await defaultBranch(a));
      const f = await get(`${P(a)}/repository/files/${enc(a.path)}`, { ref });
      const buf = Buffer.from(f.content, "base64");
      const binary = buf.includes(0);
      return { path: f.file_path, ref, size: f.size, blob_id: f.blob_id, last_commit_id: f.last_commit_id, ...(binary ? { binary: true, note: "fichier binaire, contenu non affiché" } : { content: buf.toString("utf8") }) };
    },
    treeList: (a) => defaultBranch(a).then((db) => page(`${P(a)}/repository/tree`, a, { path: a.path, ref: a.ref || db, recursive: a.recursive }, (t) => ({ path: t.path, type: t.type }))),
    async compare(a) {
      const c = await get(`${P(a)}/repository/compare`, { from: a.from, to: a.to, straight: a.straight });
      const max = a.max_diff_chars || 4000;
      return {
        commits: (c.commits || []).map((x: any) => ({ id: x.short_id, title: x.title, author: x.author_name })),
        files: (c.diffs || []).map((d: any) => ({ path: d.new_path, old_path: d.renamed_file ? d.old_path : undefined, new: d.new_file, deleted: d.deleted_file, ...(a.stat_only ? {} : { diff: String(d.diff).length > max ? String(d.diff).slice(0, max) + "\n… [diff tronqué]" : d.diff }) })),
        compare_timeout: c.compare_timeout,
      };
    },
    async blame(a) {
      const ref = a.ref || (await defaultBranch(a));
      const rows = await get(`${P(a)}/repository/files/${enc(a.path)}/blame`, { ref });
      let line = 1;
      return (rows as any[]).map((r) => { const n = r.lines.length; const out = { lines: `${line}-${line + n - 1}`, commit: r.commit.id.slice(0, 8), author: r.commit.author_name, date: r.commit.committed_date?.slice(0, 10), title: r.commit.title }; line += n; return out; });
    },
    commitList: (a) => page(`${P(a)}/repository/commits`, a, { ref_name: a.ref, path: a.path, since: a.since, until: a.until }, (c) => ({ id: c.short_id, title: c.title, author: c.author_name, date: c.committed_date })),
    async commitGet(a) {
      const c = await get(`${P(a)}/repository/commits/${enc(a.sha)}`, { stats: true });
      const out: any = pick(c, ["id", "title", "message", "author_name", "committed_date", "stats", "parent_ids", "web_url"]);
      if (a.diff) out.files = (await get(`${P(a)}/repository/commits/${enc(a.sha)}/diff`)).map((d: any) => ({ path: d.new_path, diff: String(d.diff).slice(0, 4000) }));
      return out;
    },
    async commitFiles(a) {
      if (!Array.isArray(a.actions) || !a.actions.length) throw new GitspaceError("Aucune action de fichier", 400, "actions: [{action:'create'|'update'|'upsert'|'delete'|'move', path, content?, previous_path?}]");
      const branch = a.branch;
      const head = await branchHead(a, branch);
      if (a.expected_head && head && head !== a.expected_head) throw new GitspaceError(`La branche ${branch} a avancé (${head.slice(0, 8)} ≠ ${String(a.expected_head).slice(0, 8)})`, 409, "relis la branche (branch_list), intègre les changements puis recommence avec le nouvel expected_head");
      const start_branch = head ? undefined : a.start_branch || (await defaultBranch(a).catch(() => undefined));
      const actions: any[] = [];
      for (const f of a.actions) {
        if (!f.path || f.path.startsWith("/") || f.path.split("/").includes("..")) throw new GitspaceError(`Chemin invalide « ${f.path} »`, 400, "chemin relatif à la racine du dépôt, sans « .. »");
        let action = f.action;
        if (action === "upsert") {
          const ex = await req("HEAD", `${P(a)}/repository/files/${enc(f.path)}`, { query: { ref: head ? branch : start_branch || branch }, okStatuses: [404], text: true });
          action = ex.status === 404 ? "create" : "update";
        }
        if (!["create", "update", "delete", "move"].includes(action)) throw new GitspaceError(`Action « ${f.action} » inconnue`, 400, "create, update, upsert, delete ou move");
        if (action === "move" && !f.previous_path) throw new GitspaceError("move exige previous_path", 400, "previous_path = ancien chemin, path = nouveau");
        const base64 = f.encoding === "base64";
        if (typeof f.content === "string" && !base64 && looksSecret(f.content)) throw new GitspaceError(`Le contenu de ${f.path} ressemble à un secret (jeton, clé privée, URL avec mot de passe)`, 400, "les secrets ne vont jamais dans un dépôt : retire-le et passe par ci_var_set ou le fichier d'environnement local");
        actions.push({ action, file_path: f.path, previous_path: f.previous_path, content: f.content, encoding: base64 ? "base64" : undefined, execute_filemode: f.executable });
      }
      const c = (await req("POST", `${P(a)}/repository/commits`, { body: { branch, start_branch, commit_message: a.message, actions, author_name: a.author_name, author_email: a.author_email } })).data;
      return { commit: c.id, short_id: c.short_id, branch, created_branch: !head, files: actions.map((x) => `${x.action} ${x.file_path}`), stats: c.stats, web_url: c.web_url };
    },
    async searchCode(a) {
      const path = a.project ? `${P(a)}/search` : "/search";
      return page(path, a, { scope: "blobs", search: a.query, ref: a.ref }, (r) => ({ project: r.project_id, path: r.path, ref: r.ref, line: r.startline, snippet: String(r.data).slice(0, 600) }));
    },

    mrList: (a) => page(`${P(a)}/merge_requests`, a, { state: a.state || "opened", source_branch: a.source_branch, target_branch: a.target_branch, search: a.search, author_username: a.author }, (m) => slim(mrShape({ ...m, description: undefined }))),
    async mrGet(a) {
      const m = await get(`${P(a)}/merge_requests/${a.iid}`, { include_diverged_commits_count: true });
      const out: any = slim(mrShape(m));
      if (m.head_pipeline) out.head_pipeline = pick(m.head_pipeline, ["id", "status", "web_url"]);
      if (a.with_files) out.files = (await get(`${P(a)}/merge_requests/${a.iid}/diffs`, { per_page: 100 })).map((d: any) => d.new_path);
      return out;
    },
    async mrCreate(a) {
      const target = a.target_branch || (await defaultBranch(a));
      const title = a.draft && !/^draft:/i.test(a.title) ? `Draft: ${a.title}` : a.title;
      const m = (await req("POST", `${P(a)}/merge_requests`, { body: { source_branch: a.source_branch, target_branch: target, title, description: a.description, remove_source_branch: a.remove_source_branch, squash: a.squash, labels: a.labels?.join(",") } })).data;
      return slim(mrShape(m));
    },
    async mrUpdate(a) {
      const body: any = pick(a, ["title", "description", "target_branch", "state_event", "squash", "remove_source_branch"]);
      if (a.labels) body.labels = a.labels.join(",");
      if (a.draft === true && body.title && !/^draft:/i.test(body.title)) body.title = `Draft: ${body.title}`;
      if (a.draft === false && !body.title) body.title = String((await get(`${P(a)}/merge_requests/${a.iid}`)).title).replace(/^(draft:|\[draft\]|\(draft\))\s*/i, "");
      return slim(mrShape((await req("PUT", `${P(a)}/merge_requests/${a.iid}`, { body })).data));
    },
    async mrMerge(a) {
      const base = `${P(a)}/merge_requests/${a.iid}`;
      let m = await get(base);
      if (m.state !== "opened") throw new GitspaceError(`La MR !${a.iid} est « ${m.state} »`, 405, m.state === "merged" ? "déjà fusionnée : rien à faire" : "rouvre-la avec mr_update state_event: reopen");
      if (a.wait_pipeline) {
        const deadline = Date.now() + Math.min(Number(a.timeout_s || 300), 900) * 1000;
        for (;;) {
          m = await get(base);
          const st = m.head_pipeline?.status;
          if (!st || st === "success" || st === "skipped") break;
          if (["failed", "canceled"].includes(st)) throw new GitspaceError(`Le pipeline ${m.head_pipeline.id} est ${st}`, 405, `lis les jobs avec job_list (pipeline_id ${m.head_pipeline.id}) puis job_log`);
          if (Date.now() > deadline) throw new GitspaceError(`Pipeline toujours « ${st} » après ${a.timeout_s || 300} s`, 408, "réessaie avec un timeout_s plus long, ou when_pipeline_succeeds: true");
          await sleep(5000);
        }
      }
      for (let i = 0; i < 6 && ["checking", "unchecked", "preparing"].includes(m.detailed_merge_status); i++) { await sleep(2500); m = await get(base); }
      const bad: Record<string, string> = {
        not_approved: "approbation requise", discussions_not_resolved: "résous les discussions (discussion_resolve)", draft_status: "la MR est en brouillon : mr_update draft: false",
        conflict: "conflits : rebase/merge la branche cible dans la source", need_rebase: "rebase requis", ci_must_pass: "le pipeline doit réussir", blocked_status: "bloquée par une autre MR",
        not_open: "la MR n'est pas ouverte", external_status_checks: "contrôles externes en attente",
      };
      if (bad[m.detailed_merge_status] && !(a.when_pipeline_succeeds && m.detailed_merge_status === "ci_must_pass")) throw new GitspaceError(`MR !${a.iid} non fusionnable : ${m.detailed_merge_status}`, 405, bad[m.detailed_merge_status]);
      const sha = a.sha || m.sha;
      let r: any;
      try {
      r = (await req("PUT", `${base}/merge`, { body: { sha, squash: a.squash, squash_commit_message: a.squash_commit_message, merge_commit_message: a.merge_commit_message, should_remove_source_branch: a.remove_source_branch, auto_merge: a.when_pipeline_succeeds || undefined, merge_when_pipeline_succeeds: a.when_pipeline_succeeds || undefined } })).data;
      } catch (e: any) {
        if (e instanceof GitspaceError && (e.status === 405 || e.status === 406 || e.status === 409)) {
          const now = await get(base).catch(() => null);
          throw new GitspaceError(`${e.message} [état MR : ${now?.detailed_merge_status}, pipeline : ${now?.head_pipeline?.status ?? "aucun"}, sha MR ${String(now?.sha).slice(0, 8)}]`, e.status, e.hint);
        }
        throw e;
      }
      return { iid: r.iid, state: r.state, merged_sha: r.merge_commit_sha || r.squash_commit_sha, merge_checked_sha: sha, web_url: r.web_url };
    },

    async noteAdd(a) {
      const kind = a.kind || "mr";
      if (kind === "commit") return pick((await req("POST", `${P(a)}/repository/commits/${enc(a.ref)}/comments`, { body: { note: a.body } })).data, ["note", "author"]);
      const seg = kind === "issue" ? "issues" : "merge_requests";
      return pick((await req("POST", `${P(a)}/${seg}/${a.ref}/notes`, { body: { body: a.body } })).data, ["id", "created_at"]);
    },
    async discussionList(a) {
      const seg = a.kind === "issue" ? "issues" : "merge_requests";
      const r = await page(`${P(a)}/${seg}/${a.iid}/discussions`, a, {}, (d) => ({ id: d.id, resolved: d.notes?.[0]?.resolved ?? null, notes: d.notes.filter((n: any) => !n.system).map((n: any) => ({ id: n.id, author: n.author?.username, body: n.body, at: n.created_at?.slice(0, 16), position: n.position ? `${n.position.new_path}:${n.position.new_line}` : undefined })) }));
      if (a.only_unresolved) r.items = r.items.filter((d: any) => d.resolved === false);
      r.items = r.items.filter((d: any) => d.notes.length);
      return r;
    },
    async discussionResolve(a) {
      if (a.reply) await req("POST", `${P(a)}/merge_requests/${a.iid}/discussions/${a.discussion_id}/notes`, { body: { body: a.reply } });
      const d = (await req("PUT", `${P(a)}/merge_requests/${a.iid}/discussions/${a.discussion_id}`, { body: { resolved: a.resolved !== false } })).data;
      return { id: d.id, resolved: d.notes?.[0]?.resolved };
    },

    issueList: (a) => page(`${ownerPath(a)}/issues`, a, { state: a.state || "opened", labels: a.labels?.join(","), search: a.search, assignee_username: a.assignee }, (i) => issueShape({ ...i, description: undefined })),
    async issueGet(a) { return issueShape(await get(`${P(a)}/issues/${a.iid}`)); },
    async issueCreate(a) { return issueShape((await req("POST", `${P(a)}/issues`, { body: { title: a.title, description: a.description, labels: a.labels?.join(","), confidential: a.confidential } })).data); },
    async issueUpdate(a) {
      const body: any = pick(a, ["title", "description", "state_event", "confidential"]);
      if (a.labels) body.labels = a.labels.join(",");
      if (a.add_labels) body.add_labels = a.add_labels.join(",");
      if (a.remove_labels) body.remove_labels = a.remove_labels.join(",");
      return issueShape((await req("PUT", `${P(a)}/issues/${a.iid}`, { body })).data);
    },

    pipelineList: (a) => page(`${P(a)}/pipelines`, a, { ref: a.ref, status: a.status, sha: a.sha }, pipeShape),
    async pipelineGet(a) {
      const p = pipeShape(await get(`${P(a)}/pipelines/${a.id}`)) as any;
      if (a.include_jobs !== false) p.jobs = (await get(`${P(a)}/pipelines/${a.id}/jobs`, { per_page: 100 })).map(jobShape);
      return p;
    },
    async pipelineRun(a) {
      const variables = Object.entries(a.variables || {}).map(([key, value]) => ({ key, value: String(value) }));
      return pipeShape((await req("POST", `${P(a)}/pipeline`, { body: { ref: a.ref || (await defaultBranch(a)), variables } })).data);
    },
    async pipelineAction(a) { return pipeShape((await req("POST", `${P(a)}/pipelines/${a.id}/${a.action}`)).data); },
    jobList: (a) => a.pipeline_id ? page(`${P(a)}/pipelines/${a.pipeline_id}/jobs`, a, { "scope[]": a.scope }, jobShape) : page(`${P(a)}/jobs`, a, { "scope[]": a.scope }, jobShape),
    async jobLog(a) {
      const t: string = (await req("GET", `${P(a)}/jobs/${a.job_id}/trace`, { text: true })).data;
      const clean = t.replace(/\x1b\[[0-9;]*[A-Za-z]/g, "").replace(/\r/g, "");
      const lines = clean.split("\n");
      const n = Math.min(Number(a.tail_lines || 200), 2000);
      return { total_lines: lines.length, shown: Math.min(n, lines.length), log: lines.slice(-n).join("\n") };
    },

    tagList: (a) => page(`${P(a)}/repository/tags`, a, { search: a.search }, (t) => ({ name: t.name, message: t.message, target: t.target?.slice(0, 8), date: t.commit?.committed_date })),
    async tagCreate(a) { const t = (await req("POST", `${P(a)}/repository/tags`, { body: { tag_name: a.tag, ref: a.ref || (await defaultBranch(a)), message: a.message } })).data; return { tag: t.name, target: t.target?.slice(0, 8) }; },
    async tagDelete(a) { await req("DELETE", `${P(a)}/repository/tags/${enc(a.tag)}`); return { deleted: a.tag }; },
    releaseList: (a) => page(`${P(a)}/releases`, a, {}, (r) => ({ tag: r.tag_name, name: r.name, released_at: r.released_at, description: String(r.description || "").slice(0, 300) })),
    async releaseCreate(a) { const r = (await req("POST", `${P(a)}/releases`, { body: { tag_name: a.tag, name: a.name || a.tag, description: a.description, ref: a.ref } })).data; return { tag: r.tag_name, name: r.name }; },

    memberList: (a) => page(`${ownerPath(a)}/members/all`, a, {}, (m) => ({ username: m.username, name: m.name, access: m.access_level, state: m.state, expires_at: m.expires_at })),
    async memberSet(a) {
      const level = LEVEL[a.access];
      if (!level) throw new GitspaceError(`Rôle « ${a.access} » inconnu`, 400, "guest, reporter, developer, maintainer ou owner");
      const user_id = await userId(a.user);
      const base = `${ownerPath(a)}/members`;
      const body = { user_id, access_level: level, expires_at: a.expires_at };
      const ex = await req("POST", base, { body, okStatuses: [409] });
      const r = ex.status === 409 ? await req("PUT", `${base}/${user_id}`, { body: { access_level: level, expires_at: a.expires_at } }) : ex;
      return { user: a.user, access: a.access, updated: ex.status === 409 };
    },
    async memberRemove(a) { const id = await userId(a.user); await req("DELETE", `${ownerPath(a)}/members/${id}`); return { removed: a.user }; },

    async ciVarList(a) { return page(`${P(a)}/variables`, a, {}, (v) => pick(v, ["key", "environment_scope", "protected", "masked", "variable_type"])); },
    async ciVarSet(a) {
      const body = { key: a.key, value: a.value, protected: a.protected ?? true, masked: a.masked ?? true, environment_scope: a.environment_scope || "*", variable_type: a.variable_type || "env_var" };
      const r = await req("PUT", `${P(a)}/variables/${enc(a.key)}`, { body, okStatuses: [404], query: { "filter[environment_scope]": body.environment_scope } });
      if (r.status === 404) await req("POST", `${P(a)}/variables`, { body });
      return { key: a.key, stored: true, protected: body.protected, masked: body.masked, note: "la valeur est en écriture seule : elle ne peut plus être relue" };
    },
    async ciVarDelete(a) { await req("DELETE", `${P(a)}/variables/${enc(a.key)}`, { query: { "filter[environment_scope]": a.environment_scope } }); return { deleted: a.key }; },

    webhookList: (a) => page(`${P(a)}/hooks`, a, {}, (h) => ({ id: h.id, url: stripUserinfo(h.url), push: h.push_events, merge_requests: h.merge_requests_events, issues: h.issues_events, pipeline: h.pipeline_events, tags: h.tag_push_events, notes: h.note_events, ssl_verify: h.enable_ssl_verification })),
    async webhookCreate(a) {
      const ev = new Set<string>(a.events || ["push"]);
      const body = { url: a.url, token: a.secret_token, enable_ssl_verification: a.enable_ssl_verification ?? true, push_events: ev.has("push"), merge_requests_events: ev.has("merge_requests"), issues_events: ev.has("issues"), pipeline_events: ev.has("pipeline"), tag_push_events: ev.has("tag_push"), note_events: ev.has("note"), job_events: ev.has("job") };
      const h = (await req("POST", `${P(a)}/hooks`, { body })).data;
      return { id: h.id, url: stripUserinfo(h.url), events: [...ev] };
    },
    async webhookDelete(a) { await req("DELETE", `${P(a)}/hooks/${a.hook_id}`); return { deleted: a.hook_id }; },

    mirrorList: (a) => page(`${P(a)}/remote_mirrors`, a, {}, (m) => ({ id: m.id, url: stripUserinfo(m.url), enabled: m.enabled, only_protected_branches: m.only_protected_branches, last_update_status: m.update_status, last_update_at: m.last_update_at, last_error: m.last_error })),
    async mirrorSet(a) {
      const m = (await req("POST", `${P(a)}/remote_mirrors`, { body: { url: a.url, enabled: a.enabled ?? true, only_protected_branches: a.only_protected_branches ?? false, keep_divergent_refs: a.keep_divergent_refs ?? true } })).data;
      return { id: m.id, url: stripUserinfo(m.url), enabled: m.enabled, note: "l'URL peut contenir des identifiants : ils sont masqués dans toutes les réponses" };
    },
    async mirrorDelete(a) { await req("DELETE", `${P(a)}/remote_mirrors/${a.mirror_id}`); return { deleted: a.mirror_id }; },
  };
  return self;
}
