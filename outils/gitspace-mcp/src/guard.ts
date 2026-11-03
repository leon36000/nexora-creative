// Garde-fous : rate limiting, masquage des secrets, tronquage des sorties.
export class RateLimiter {
  private tokens: number;
  private last = Date.now();
  constructor(private ratePerSec = Number(process.env.GITSPACE_RATE || 8), private burst = Number(process.env.GITSPACE_BURST || 16)) {
    this.tokens = burst;
  }
  async take(): Promise<void> {
    for (;;) {
      const now = Date.now();
      this.tokens = Math.min(this.burst, this.tokens + ((now - this.last) / 1000) * this.ratePerSec);
      this.last = now;
      if (this.tokens >= 1) { this.tokens -= 1; return; }
      await new Promise((r) => setTimeout(r, Math.ceil(((1 - this.tokens) / this.ratePerSec) * 1000)));
    }
  }
}

const SECRET_KEYS = /^(token|private_token|value|secret|secret_token|password|authorization|runners_token|import_url|ssh_private_key|access_token|refresh_token)$/i;
const SECRET_PATTERNS: RegExp[] = [
  /glpat-[A-Za-z0-9_-]{10,}/g, /gl[a-z]{2,4}-[A-Za-z0-9_-]{20,}/g, /ghp_[A-Za-z0-9]{20,}/g, /sk-[A-Za-z0-9_-]{20,}/g,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
  /(https?:\/\/)[^\s/:@]+:[^\s/@]+@/g,
];
let knownSecrets: string[] = [];
export function registerSecret(s: string) { if (s && s.length > 6) knownSecrets.push(s); }

export function scrubText(t: string): string {
  for (const s of knownSecrets) t = t.split(s).join("[SECRET]");
  for (const p of SECRET_PATTERNS) t = t.replace(p, (m, g1) => (g1 ? `${g1}[SECRET]@` : "[SECRET]"));
  return t;
}

/** Retire récursivement les champs sensibles (valeurs de variables CI, jetons, import_url...). */
export function scrub(v: any, keepKeys: string[] = []): any {
  if (Array.isArray(v)) return v.map((x) => scrub(x, keepKeys));
  if (v && typeof v === "object") {
    const o: any = {};
    for (const [k, val] of Object.entries(v)) {
      if (SECRET_KEYS.test(k) && !keepKeys.includes(k)) { if (val != null && val !== "") o[k] = "[MASQUÉ]"; continue; }
      o[k] = scrub(val, keepKeys);
    }
    return o;
  }
  return typeof v === "string" ? scrubText(v) : v;
}

export const MAX_OUT = Number(process.env.GITSPACE_MAX_OUTPUT || 60000);
export function render(v: unknown): string {
  const s = typeof v === "string" ? v : JSON.stringify(v, null, 1);
  return s.length > MAX_OUT ? s.slice(0, MAX_OUT) + `\n… [tronqué : ${s.length - MAX_OUT} caractères en plus ; affine avec per_page, path ou tail_lines]` : s;
}
