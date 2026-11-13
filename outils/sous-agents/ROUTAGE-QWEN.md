# Routage `qwen` / `eco-qwen` — pc4 local (coût $0.00000)

> Brouillon opérationnel. Cible : `outils/sous-agents/`.
> Modèle : Qwen3.8-Flash-Next sur pc4 (RTX 3090, `SA_QWEN_URL=http://192.168.1.161:8080/v1`).
> Alias `qwen` = `eco-qwen` (cf. `sa_alias()` dans `lib.sh`). Coût compté à `$0.00000` (`FREE_ALIASES` dans `cout.py`).
> Disponibilité vérifiée par sonde locale (`qwen_ctl.py probe` → `/health` + `/v1/models`) ; repli automatique sinon.

Règle d'or : **`eco-qwen` par défaut pour le mécanique factuel et borné ; tout le reste → `eco-deepseek` / `eco-muse` / modèles forts.**

Seuils : prompt **≤ 12k jetons et ≤ 15 tours** → candidat `eco-qwen`. Entre 12k et 16k → arbitrage prudent. **> 16k jetons → jamais `eco-qwen`.**

## 1. Quand utiliser `qwen` / `eco-qwen`

Utiliser pour tâches **fermées, vérifiables, à contexte borné** :

- **Extraction structurée** : JSON / TSV / front-matter depuis logs, rapports, transcripts.
- **Résumés factuels** : `summary.txt`, journaux, `rapport.json` → 10 lignes, sans avis.
- **Tests unitaires simples** : ajouter/étendre un test évident, lancer `pytest`/`npm test`, rapporter.
- **Traductions FR/EN i18n** : chaînes UI, docs, sans ton créatif.
- **Recherche de références** : lister fichiers/symboles (`Grep`/`Glob`), pas d'arbitrage.
- **Formatage / typage mécanique** : `prettier`, types évidents, renommage local, imports.

Conditions obligatoires :

- Prompt court, consignes explicites, critère de fini vérifiable par commande.
- Dossier de travail isolé (worktree git pour orchestrateur, workdir dédié sinon).
- Vérification imposée dans le prompt (« exécute les tests, cite fichiers + commandes »).

## 2. Quand NE JAMAIS utiliser `eco-qwen`

Interdit, même si pc4 répond sain :

- **Sécurité / secrets / sandbox** : clés, `master.key`, `strata.key`, `~/.ssh`, `~/.aws`, contournement `bwrap`/proxy, `git push`/`ssh`/`curl`.
- **Décisions d'architecture / ADR** : choix de modèle, schéma, protocole, arbitrage multi-critères.
- **Concurrence complexe** : `lot.sh` à fort parallélisme, sémaphores imbriqués, conditions de course.
- **Code critique prod / ledger** : `usage.jsonl`, `cost_snapshot.py`, `lot.py`, `proxy`/`gateway`, comptabilité des coûts.
- **Tâches ambiguës** : brief flou,plausible, critères de fini non testables.
- **Très gros contexte** : **> 16k jetons**, repo entier à comprendre, historique long.

→ Dans ces cas : `eco-deepseek` (mécanique payant), `eco-muse` (bon marché fort), `eco-gemini-eleve`/`eco-terra` (difficile), jamais `SA_QWEN_FALLBACK=0` pour forcer.

## 3. Comment router (commandes)

Prérequis : passerelle démarrée (`activer.sh [--local]` affiche la ligne `Ferme Qwen pc4 …` via `qwen_ctl.py status-line`, informative, non bloquante).

### 3.1 `router.sh` — aiguillage rapide

```bash
# Une tâche : route vers eco-qwen si mécanique + bornée, sinon repli conseillé
outils/sous-agents/router.sh --file prompts/tache-01.txt

# Lot de prompts : une décision par fichier
outils/sous-agents/router.sh --batch prompts/lot-a/

# Sortie machine pour scripts / lot.sh
outils/sous-agents/router.sh --batch prompts/lot-a/ --json
```

- `--file <prompt>` : analyse un prompt, affiche `eco-qwen` ou le modèle conseillé + motif.
- `--batch <dossier-prompts>` : idem pour chaque `.txt`/`.md` du dossier.
- `--json` : même résultat en JSON (`{tache, modele, motif}`) ; à combiner avec `--file`/`--batch`.
- Le routeur ne lance rien : il applique §1/§2 + seuils 12k/16k jetons.

### 3.2 `sous-agent.sh qwen` — une tâche

```bash
outils/sous-agents/sous-agent.sh -w qwen prompts/tache-01.txt work/tache-01 15 0.30
```

- `qwen` ≡ `eco-qwen`. `-w` attend la fin ; sans `-w`, arrière-plan (`summary.txt`, `done`).
- Résolution à chaque lancement (`qwen_ctl.py resolve`) : si pc4 sain → `eco-qwen` + slot local ; sinon → repli (voir §3.5) ou `FAIL:pc4_indisponible` si `SA_QWEN_FALLBACK=0`.
- File pc4 pleine (`hold-slot` TIMEOUT) → repli ou `FAIL:file_pc4_pleine`.
- Résultat : `$SA_STATE/runs/<run>/` (`summary.txt` commence par `OK:`/`FAIL:`, `repli_depuis=eco-qwen` si repli).

### 3.3 `lot.sh qwen` — lot apparié

```bash
LOT_TURNS=15 LOT_RUN_BUDGET=0.30 LOT_BUDGET=5 \
  outils/sous-agents/lot.sh qwen prompts/lot-a/ work/lot-a/ 8
```

- Parallélisme plafonné pour qwen : `min(parallélisme, SA_QWEN_LOT_PARALLEL=3)` si repli actif, sinon `min(parallélisme, SA_QWEN_MAX_CONCURRENCY)`.
- Index : `$SA_STATE/lots/<lot>/index.tsv` + `lot_status.txt`. Coût vérifié par run dans `usage.jsonl`.

### 3.4 `orchestrateur.sh qwen` — pilotage multi-tours

```bash
outils/sous-agents/orchestrateur.sh -w qwen prompts/brief.md /chemin/worktree-git 250 12
```

- Re-sonde pc4 à **chaque tour** (`OR_ROUNDS=6` par défaut) et prend un slot (`with-slot`) si `eco-qwen`.
- Le worktree doit être un worktree git ; seul dossier d'écriture. Ne pousse jamais.

### 3.5 Variables de contrôle

| Variable | Défaut (`lib.sh`) | Effet |
|---|---|---|
| `SA_QWEN_MAX_CONCURRENCY` | `2` | Slots pc4 simultanés (`with-slot` / `hold-slot`). |
| `SA_QWEN_QUEUE_TIMEOUT` | `180` | Attente max d'un slot (s) ; au-delà → repli ou `75`. |
| `SA_QWEN_FALLBACK` | `1` | `1` = repli auto si pc4 HS/lent/plein ; `0` = échec sec. |
| `SA_QWEN_FALLBACK_MODEL` | `eco-deepseek` | Cible du repli (`eco-deepseek` ou `eco-muse` uniquement). |
| `SA_QWEN_MAX_PROBE_MS` | `1500` | Latence max sonde ; au-delà → `pc4_lent_*ms` → repli. |
| `SA_QWEN_PROBE_TIMEOUT` | `3` (`1.0` pour `activer.sh`) | Timeout HTTP `/health` + `/v1/models`. |
| `SA_QWEN_URL` | `http://192.168.1.161:8080/v1` | Point pc4 (jamais de secret dans l'URL). |
| `SA_QWEN_LOT_PARALLEL` | `3` (`lot.py`) | Plafond lots qwen quand repli actif. |

Diagnostic :

```bash
python3 outils/sous-agents/qwen_ctl.py probe | jq .
python3 outils/sous-agents/qwen_ctl.py resolve eco-qwen | jq .
outils/sous-agents/cout.sh --run <run-ou-lot>   # eco-qwen → $0.00000
```

## 4. Mesures réelles — 20 tâches appariées (à remplir)

Protocole : même prompt, même workdir isolé, mêmes `LOT_TURNS`/`LOT_RUN_BUDGET`, un run par modèle (`eco-qwen` vs `eco-deepseek` vs `eco-muse`). Noter `summary.txt` (`OK:`/`FAIL:`), jetons (`usage.jsonl`), durée, coût (`cout.sh --run`).

| # | Tâche (type §1) | Prompt (jetons) / tours max | `eco-qwen` OK/FAIL · durée · in/out · coût | `eco-deepseek` OK/FAIL · durée · in/out · coût | `eco-muse` OK/FAIL · durée · in/out · coût | Verdict (qwen suffit ? repli ?) |
|---|---|---|---|---|---|---|
| 01 | _ex. extraction JSON depuis log_ | _…_ / 15 | _à mesurer_ | _à mesurer_ | _à mesurer_ | _…_ |
| 02 | | | | | | |
| 03 | | | | | | |
| 04 | | | | | | |
| 05 | | | | | | |
| 06 | | | | | | |
| 07 | | | | | | |
| 08 | | | | | | |
| 09 | | | | | | |
| 10 | | | | | | |
| 11 | | | | | | |
| 12 | | | | | | |
| 13 | | | | | | |
| 14 | | | | | | |
| 15 | | | | | | |
| 16 | | | | | | |
| 17 | | | | | | |
| 18 | | | | | | |
| 19 | | | | | | |
| 20 | | | | | | |

Synthèse (à compléter après mesures) : taux `OK:`, durée médiane, jetons médians, économies vs payants, cas de repli (`pc4_lent`, `file_pc4_pleine`, `modele_qwen_absent`).
