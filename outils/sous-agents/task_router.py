#!/usr/bin/env python3
"""Routeur de tâches pour les sous-agents eco-* (stdlib uniquement).

Classe une demande en texte libre et décide si elle peut être confiée au petit
modèle local eco-qwen (mécanique, vérifiable, courte) ou s'il faut un modèle
plus capable (eco-deepseek, eco-muse, eco-gemini-eleve).

CLI :
    python3 task_router.py [--json] [--file PATH | --batch DIR | TEXT]

Sortie (dict) : alias, eligible_qwen, category, confidence, reasons,
blockers, estimated_tokens.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ALIASES = ("eco-qwen", "eco-deepseek", "eco-muse", "eco-gemini-eleve")
DEFAULT_MAX_QWEN_BYTES = 49152  # ~12k jetons
MAX_INPUT_BYTES = 8 * 1024 * 1024

# ---------------------------------------------------------------------------
# Signaux mécaniques (tâches vérifiables)
# ---------------------------------------------------------------------------
# (catégorie, motif). Les regex sont appliquées sur un texte normalisé
# (minuscules, sans accents, espaces compactés).
MECHANICAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (cat, re.compile(pat))
    for cat, pat in (
        ("extraction", r"\b(extrai[ts]?|extract|extraire|parse[rz]?|analyser|converti[ts]?|convert|transforme[rz]?|convertir)\b.{0,60}\b(json|jsonl|csv|tsv|yaml|xml|table|tableau|colonnes?|champs?|regex|regexp|motifs?|pattern)\b|\b(json|jsonl|csv|tsv|xml|yaml)\b.{0,40}\b(en|vers|to|->|=>)\b.{0,30}\b(json|jsonl|csv|tsv|xml|yaml|markdown|md)\b"),
        ("extraction", r"\b(regex|regexp|expression reguliere|regular expression)\b"),
        ("tests", r"\b(tests? unitaires?|unit tests?|fixtures?|cas de test|test cases?|asserts?)\b"),
        ("tests", r"\bajoute[rz]?\s+(un|des|le|les)?\s*tests?\b|\bwrite[s]?\s+(a|the)?\s*tests?\b"),
        ("resume", r"\b(resume[rz]?|resumer|summar\w+|synthese factuelle|condense[rz]?|condensee?|factual summary|tl;?dr|en\s+\d+\s+lignes?)\b"),
        ("traduction", r"\b(tradui[ts]\w*|traduc\w*|translat\w+|traduire|i18n|l10n|locali[sz]\w*|localiser|version anglaise|version francaise|in english|en anglais|en francais)\b"),
        ("inventaire", r"\b(inventaire|inventory|liste[rz]?|list\b|recense[rz]?|enumere[rz]?|enumerate|localise[rz]?|trouve[rz]?|find\b|grep|references?|symboles?|symbols?|usages?|call ?sites?|occurrences?)\b"),
        ("formatage", r"\b(format(e|er|ez|age)?|formatting|indent\w*|reindent\w*|lint\w*|black|ruff|prettier|eslint|type ?hints?|typage|type annotation\w*|annotations? de type|typer?|type\b.{0,20}\b(annotations?|hints?))\b"),
        ("docstrings", r"\b(docstrings?|doc ?comments?|comments? de documentation|pydoc\w*)\b"),
        ("renommage", r"\b(renomme[rz]?|rename\w*|remplace[rz]?\s+(toutes?\s+les?\s+)?occurrences?|renommage)\b"),
    )
)

# ---------------------------------------------------------------------------
# Signaux d'exclusion (catégorie, poids, alias cible, motif)
# ---------------------------------------------------------------------------
EXCLUSION_RULES: tuple[tuple[str, int, str, re.Pattern[str]], ...] = tuple(
    (cat, weight, alias, re.compile(pat))
    for cat, weight, alias, pat in (
        # ---- sécurité / secrets : jugement -> gemini-eleve ; correctif -> deepseek
        ("securite", 50, "eco-gemini-eleve", r"\b(securi\w+|security|audit\w* de securite|security audit|threat model\w*|modele de menace|vulnerabil\w+|vulnerabilit\w+|failles?|exploit\w*|pentest\w*|fuzzing|durcissement|hardening)\b"),
        ("securite", 50, "eco-gemini-eleve", r"\b(jwt|oauth\w*|saml|sso|csrf|xss|ssrf|xxe|rac[e]? ?condition|privilege escalation|escalade de privileges?)\b"),
        ("secrets", 40, "eco-gemini-eleve", r"\b(secrets?|api[ _-]?keys?|cles? api|mot de passe|passwords?|passwd|credentials?|identifiants?|tokens? d.acces|access tokens?|cercles? de cles|keyring)\b"),
        ("auth", 40, "eco-gemini-eleve", r"\b(auth\w*|authentification|authentication|autorisation|authorization|rbac|abac|permissions?|acls?|privileges?|sessions?(?:\s+(?:cookie|fixation))?|login|connexion utilisateur)\b"),
        ("crypto", 40, "eco-gemini-eleve", r"\b(crypt\w+|chiffr\w+|encrypt\w*|decrypt\w*|dechiffr\w*|aes|rsa|ecdsa|ed25519|sha-?\d+|tls|ssl|hmac|signatures? numeriques?|nonce|iv\b)\b"),
        ("sandbox", 35, "eco-gemini-eleve", r"\b(sandbox\w*|bac a sable|seccomp|namespace[s]? linux|chroot|cgroup[s]?|isolation|container escape|echappement de conteneur)\b"),
        ("injection", 45, "eco-gemini-eleve", r"\b(injections? (sql|nosql|de commande|shell|ldap|xpath|prompt)|sql injection|prompt injection|rce|remote code execution|execution de code a distance|\bexec\(|\beval\(|pickle\.loads)\b"),
        ("cve", 45, "eco-gemini-eleve", r"\b(cve-?\d{4}-\d+|cvss|zero[- ]?day|0day|patch de securite|security patch|kritische?\b|advisory|advisories)\b"),
        ("privileges", 35, "eco-gemini-eleve", r"\b(sudo|su -|setuid|root\b|admin rights|droits? (?:root|admin)|chmod\s+[0-7]*7|umask)\b"),
        ("reseau-securise", 35, "eco-gemini-eleve", r"\b(ssh|sshd|authorized_keys|private keys?|cles? privees?|known_hosts|firewall|pare-feu|iptables|nftables|vpn|wireguard)\b"),
        # ---- architecture / décision -> gemini-eleve
        ("architecture", 40, "eco-gemini-eleve", r"\b(architectur\w+|architecture|conception (?:systeme|globale|logicielle)|design system\w*|system design|micro-?services?\b.{0,40}\b(design|choix|architecture)|refonte globale|scalabilit\w+|scale\w* horizontally)\b"),
        ("architecture", 35, "eco-gemini-eleve", r"\b(adr|architecture decision record|decision (?:produit|technique|d.architecture)|trade-?offs?|compromis (?:techniques?|architecturaux?)|choix de (?:stack|technologie|framework))\b"),
        ("migration", 35, "eco-gemini-eleve", r"\b(migration (?:critique|de donnees|de base|vers|majeure)|migrer?\s+(?:la\s+)?(?:base|bdd|db|database)|zero[- ]downtime)\b"),
        ("schema-bdd", 35, "eco-gemini-eleve", r"\b(schema (?:de )?(?:bdd|base|db|database|sql)|data model\w*|modele de donnees|normalisation|3nf|bcnf|ddl|alter table|partitionn\w+ (?:de table|de base))\b"),
        ("schema-bdd", 20, "eco-gemini-eleve", r"\b(prod|production)\b.{0,30}\b(schema|migration|base|bdd|database|db)\b|\b(schema|migration|base|bdd|database|db)\b.{0,30}\b(prod|production)\b"),
        # ---- concurrence / paiement / bugs multi-services -> deepseek
        ("concurrence", 40, "eco-deepseek", r"\b(deadlock\w*|interblocage\w*|race condition\w*|course critique|data race|concurrence (?:complexe|avancee)|thread[- ]?safety|lock-?free|wait-?free|atomicite|semaphore\w*|mutex|condition variable)\b"),
        ("paiement", 40, "eco-deepseek", r"\b(paiements? (?:critique|recurrent)|ledger|grand livre|stripe|facturation (?:critique|complexe)|billing\w*|transaction\w* financier\w*|idempotence des? paiements?|webhooks? (?:stripe|paiement))\b"),
        ("multi-services", 35, "eco-deepseek", r"\b(bug (?:multi[- ]?services?|distribue|subtile?|intermittent|aleatoire)|course entre services|propagation de (?:l.erreur|panne)|consistance (?:eventuelle|distribuee)|eventual consistency|trace distribuee|panne en cascade)\b"),
        ("diagnostic", 25, "eco-deepseek", r"\b(pourquoi\b.{0,60}\b(?:echoue|plante|casse|crash|bug|regression|ralentit)|root cause\w*|cause racine|post-?mortem|diagnostic\w* (?:de bug|complexe))\b"),
        # ---- créatif -> muse
        ("creation", 35, "eco-muse", r"\b(brainstorm\w*|brainstorming|ideation|idees? (?:creative|originale|neuve)|nom (?:de marque|du produit)|naming|tagline|slogan|copywriting|copy ?write\w*|storytelling|pitch (?:deck|produit)|campagne (?:marketing|de communication))\b"),
        ("creation", 30, "eco-muse", r"\b(redige[rz]? (?:un|une) (?:article|post|newsletter|blog|thread|tweet)|ecri[sz]? (?:un|une) (?:article|post|newsletter|blog|conte|histoire|nouvelle|poeme)|creative writing|fiction|landing page copy)\b"),
        # ---- ambigu -> deepseek
        ("ambigu", 30, "eco-deepseek", r"\b(?:ameliore|ameliorer|optimise[rz]?|refactor\w*|nett?oie[rz]?|modernise[rz]?|revois|review)\b.{0,30}\b(?:le )?(?:code|projet|repo|tout|ca)\b"),
    )
)

CVE_PATTERN = re.compile(r"\bcve-\d{4}-\d+\b")
NUMBERED_STEPS = re.compile(r"(?m)^\s*(?:\d+[.)]|[-*])\s+\S")
CODE_FENCE = re.compile(r"```")
QUESTION_MARKERS = re.compile(r"\b(?:que faire|comment (?:choisir|decider|aborder)|quel(?:le)? strateg\w+|recommand\w+|conseil\w*|avis|recommendation\w*)\b")


def normalize(text: str) -> str:
    """Minuscules, sans diacritiques, espaces compactés."""
    lowered = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(ch for ch in lowered if not unicodedata.combining(ch))
    return " ".join(stripped.split())


def estimate_tokens(text: str) -> int:
    """Estimation prudente (~2.5 octets/jeton pour du FR/EN mixte + code)."""
    return (len(text.encode("utf-8")) + 2) // 3


@dataclass
class RouteResult:
    alias: str
    eligible_qwen: bool
    category: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    estimated_tokens: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "eligible_qwen": self.eligible_qwen,
            "category": self.category,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "blockers": self.blockers,
            "estimated_tokens": self.estimated_tokens,
        }


def route_task(text: str, *, max_qwen_bytes: int = DEFAULT_MAX_QWEN_BYTES) -> dict[str, Any]:
    """Route ``text`` vers un alias eco-* et explique la décision."""
    if not isinstance(text, str):
        raise TypeError("text doit être une str")
    if not isinstance(max_qwen_bytes, int) or max_qwen_bytes <= 0:
        raise ValueError("max_qwen_bytes doit être un entier positif")

    norm = normalize(text)
    nbytes = len(text.encode("utf-8"))
    tokens = estimate_tokens(text)
    reasons: list[str] = []
    blockers: list[str] = []

    # 1) Signaux mécaniques
    mech: list[tuple[int, str, str]] = []  # (position, catégorie, extrait)
    for cat, pat in MECHANICAL_PATTERNS:
        for m in pat.finditer(norm):
            mech.append((m.start(), cat, m.group(0)))
            break  # un extrait par catégorie
    mech_categories = sorted({cat for _, cat, _ in mech})

    # 2) Signaux d'exclusion
    excl: list[tuple[str, int, str, str]] = []  # (catégorie, poids, alias, extrait)
    for cat, weight, alias, pat in EXCLUSION_RULES:
        m = pat.search(norm)
        if m:
            excl.append((cat, weight, alias, m.group(0)))

    # Signal critique : présence d'au moins un marqueur dur
    hard = {"securite", "secrets", "auth", "crypto", "sandbox", "injection", "cve",
            "privileges", "reseau-securise", "concurrence", "paiement", "multi-services",
            "architecture", "migration", "schema-bdd"}
    hard_excl = [e for e in excl if e[0] in hard]
    soft_excl = [e for e in excl if e[0] not in hard]

    for cat, weight, alias, snippet in excl:
        blockers.append(f"{cat}: {snippet[:60]}")

    # 3) Taille du prompt
    too_long = nbytes > max_qwen_bytes
    if too_long:
        blockers.append(f"taille: {nbytes} octets > {max_qwen_bytes} (limite eco-qwen)")
    elif nbytes > max_qwen_bytes * 0.75:
        reasons.append(f"taille proche de la limite: {nbytes}/{max_qwen_bytes} octets")

    # 4) Décision
    alias: str
    category: str
    confidence: float
    eligible = False

    if hard_excl:
        # alias cible = celui du signal le plus lourd ; tie-break ordre des règles
        hard_sorted = sorted(enumerate(hard_excl), key=lambda p: (-p[1][1], p[0]))
        alias = hard_sorted[0][1][2]
        cats = {e[0] for e in hard_excl}
        category = hard_sorted[0][1][0] if len(cats) == 1 else "exclusion"
        reasons.append("signal critique: " + ", ".join(sorted(cats)))
        confidence = min(0.99, 0.7 + 0.03 * max(e[1] for e in hard_excl))
    elif soft_excl and not mech:
        # créatif ou ambigu sans tâche mécanique
        soft_sorted = sorted(enumerate(soft_excl), key=lambda p: (-p[1][1], p[0]))
        alias = soft_sorted[0][1][2]
        cats = sorted({e[0] for e in soft_excl})
        category = "creation" if "creation" in cats else "ambigu"
        reasons.append("aucune tâche mécanique; signal: " + ", ".join(cats))
        confidence = 0.72
    elif mech:
        alias = "eco-qwen" if not too_long else "eco-deepseek"
        category = mech_categories[0] if len(mech_categories) == 1 else "mecanique-mixte"
        reasons.append("tâche mécanique: " + ", ".join(mech_categories))
        if soft_excl:
            reasons.append("signaux mineurs ignorés: " + ", ".join(sorted({e[0] for e in soft_excl})))
        if too_long:
            reasons.append("trop long pour eco-qwen -> eco-deepseek")
            confidence = 0.75
        else:
            eligible = True
            confidence = min(0.98, 0.7 + 0.06 * len(mech_categories) - 0.05 * len(soft_excl))
    else:
        # rien de mécanique, rien d'identifié : flou
        if too_long:
            alias = "eco-deepseek"
            category = "flou-long"
            blockers.append("taille: prompt long sans tâche mécanique")
            confidence = 0.7
        else:
            alias = "eco-deepseek"
            category = "flou"
            confidence = 0.6
        reasons.append("aucun signal mécanique ni exclusion claire; repli prudent")

    # Taille : un prompt trop long n'est jamais éligible eco-qwen,
    # sauf signal critique déjà prioritaire.
    if too_long and alias == "eco-qwen":
        alias, eligible = "eco-deepseek", False
    if alias != "eco-qwen":
        eligible = False

    confidence = max(0.0, min(1.0, confidence))
    return RouteResult(
        alias=alias,
        eligible_qwen=eligible,
        category=category,
        confidence=confidence,
        reasons=reasons,
        blockers=blockers,
        estimated_tokens=tokens,
    ).as_dict()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _read_text_file(path: Path) -> str:
    data = path.read_bytes()[:MAX_INPUT_BYTES]
    return data.decode("utf-8", errors="replace")


def _format_human(res: dict[str, Any]) -> str:
    lines = [
        f"alias        : {res['alias']}",
        f"eligible_qwen: {'oui' if res['eligible_qwen'] else 'non'}",
        f"category     : {res['category']}",
        f"confidence   : {res['confidence']:.3f}",
        f"tokens(est.) : {res['estimated_tokens']}",
    ]
    if res["reasons"]:
        lines.append("reasons      : " + " | ".join(res["reasons"]))
    if res["blockers"]:
        lines.append("blockers     : " + " | ".join(res["blockers"]))
    return "\n".join(lines)


def _load_batch(directory: Path) -> list[tuple[str, str]]:
    """Charge (nom, texte). Accepte .txt individuels ou un fichier tasks.tsv/.json."""
    items: list[tuple[str, str]] = []
    seen_files: set[Path] = set()

    tsv = directory / "tasks.tsv"
    if tsv.is_file():
        seen_files.add(tsv)
        for lineno, line in enumerate(tsv.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                items.append((parts[0].strip() or f"ligne{lineno}", "\t".join(parts[1:]).strip()))
            else:
                items.append((f"ligne{lineno}", parts[0].strip()))

    js = directory / "tasks.json"
    if js.is_file():
        seen_files.add(js)
        raw = json.loads(js.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = [{"name": k, "text": v} for k, v in raw.items()]
        if not isinstance(raw, list):
            raise ValueError("tasks.json doit contenir une liste ou un objet")
        for idx, entry in enumerate(raw, 1):
            if isinstance(entry, str):
                items.append((f"item{idx}", entry))
            elif isinstance(entry, dict):
                body = entry.get("text") or entry.get("task") or entry.get("prompt") or ""
                name = str(entry.get("name") or entry.get("id") or f"item{idx}")
                items.append((name, str(body)))
            else:
                raise ValueError(f"tasks.json: entrée {idx} invalide")

    for path in sorted(directory.glob("*.txt")):
        if path.name in {"tasks.txt"}:
            continue
        items.append((path.stem, _read_text_file(path)))

    if not items:
        raise ValueError(f"aucune tâche trouvée dans {directory} (tasks.tsv, tasks.json ou *.txt)")
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route une tâche vers un alias eco-*.")
    parser.add_argument("--json", action="store_true", help="sortie JSON")
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--file", type=Path, help="lire la tâche depuis un fichier")
    src.add_argument("--batch", type=Path, help="dossier de tâches (tasks.tsv/.json/*.txt)")
    parser.add_argument("--max-qwen-bytes", type=int, default=DEFAULT_MAX_QWEN_BYTES,
                        help=f"limite eco-qwen en octets (défaut {DEFAULT_MAX_QWEN_BYTES})")
    parser.add_argument("text", nargs="*", help="texte de la tâche")
    args = parser.parse_args(argv)

    try:
        if args.batch is not None:
            if not args.batch.is_dir():
                print(f"erreur: {args.batch} n'est pas un dossier", file=sys.stderr)
                return 2
            rows = _load_batch(args.batch)
            results = [(name, route_task(body, max_qwen_bytes=args.max_qwen_bytes)) for name, body in rows]
            if args.json:
                payload = {
                    "total": len(results),
                    "eligible_qwen": sum(1 for _, r in results if r["eligible_qwen"]),
                    "tasks": [{"name": n, **r} for n, r in results],
                }
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print("nom\talias\teligible_qwen\tcategory\tconfidence\ttokens")
                for name, r in results:
                    print(f"{name}\t{r['alias']}\t{'oui' if r['eligible_qwen'] else 'non'}"
                          f"\t{r['category']}\t{r['confidence']:.2f}\t{r['estimated_tokens']}")
                n = len(results)
                q = sum(1 for _, r in results if r["eligible_qwen"])
                print(f"\n% eco-qwen : {100.0 * q / n:.1f}% ({q}/{n})")
            return 0

        if args.file is not None:
            if not args.file.is_file():
                print(f"erreur: fichier introuvable: {args.file}", file=sys.stderr)
                return 2
            text = _read_text_file(args.file)
        else:
            text = " ".join(args.text)
            if not text.strip() and not sys.stdin.isatty():
                text = sys.stdin.read()
        if not text.strip():
            print("erreur: texte vide (fournir TEXT, --file ou stdin)", file=sys.stderr)
            return 2
        res = route_task(text, max_qwen_bytes=args.max_qwen_bytes)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print(_format_human(res))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"erreur: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
