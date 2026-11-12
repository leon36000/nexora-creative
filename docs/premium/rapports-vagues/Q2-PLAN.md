# Q2 — Plan d'exécution : Ferme de sous-agents Qwen3.8 Flash Next à coût nul

- **Date** : 2026-11-12
- **Orchestrateur** : Q2 (`feat/ferme-qwen`)
- **Worktree** : `/home/pc6/Desktop/NexoraCreative-ferme-qwen`
- **Passerelle d'essaims** : active sur `http://127.0.0.1:4410` (compteur initial du jour relevé avant exécution : `120 req`, `$0.96166`)
- **Quotas visés** : `>= 60` appels de sous-agents sur la session Q2 (`>= 180 req` au compteur du jour en fin de mission), `>= 70 %` du volume d'analyse, de code, de tests et de brouillons délégué aux essaims `muse`, `deepseek` et `carbon` (`terra` non utilisé sauf blocage critique).

---

## 1. Constats initiaux (lecture préliminaire)

1. **Serveur d'inférence sur `pc4` (`192.168.1.161`)** :
   - Pod Kubernetes `qwen38-strata` en `hostNetwork` exposant `http://192.168.1.161:8080` (`/opt/strata/app/serve/server.py --engine strata`) devant le moteur natif `/opt/strata/custom/strata` (`127.0.0.1:18181`).
   - Modèle chargé : `swift-1.5-qwen3.8-flash-next-abliterated-iq3_s` (`n_ctx = 262144`, quantification `IQ3_S` + spéculation MTP `--spec 4`, KV `int8`, matériel AMD multi-GPU sur `pc4`).
   - Authentification : en-tête `Authorization: Bearer <clé>` (`api_key: true` sur `/health`), clé stockée hors dépôt.
   - Particularité critique déjà visible dans `/home/pc6/nexora-recherche/bench/qwen-flash-next/` : Strata ne maintient efficacement le cache de préfixe KV que lorsqu'une session n'est pas entrelacée avec d'autres flux concurrents, d'où la nécessité impérative d'un garde-fou local de concurrence et de continuité vers `pc4`.

2. **Architecture actuelle de `outils/sous-agents/`** :
   - Chaque sous-agent `claude -p` passe par un pont Unix local (`sa_proxy.py` lancé par `proxy_launcher.py`) vers LiteLLM (`litellm/config.yaml` + `litellm/sa_callbacks.py`).
   - Point critique identifié dans `sa_proxy.py` + `cost_snapshot.py` : tout appel journalisé avec `cost: null` bloque l'appel suivant en `503 coût précédent inconnu`. Pour `eco-qwen`, `sa_callbacks.py` et `config.yaml` doivent garantir un coût numérique exact `0.0` sur chaque réponse valide.
   - Ne jamais redémarrer le conteneur partagé `nexora-sa-litellm` (`127.0.0.1:4410`) utilisé simultanément par les autres orchestrateurs : nos tests d'intégration LiteLLM + `eco-qwen` tourneront sur une instance dédiée éphémère (`SA_PORT=4412`, `SA_CONTAINER_NAME=nexora-sa-litellm-q2`) arrêtée proprement après essai.

---

## 2. Découpage en 5 étapes et vagues d'essaims

### Étape 1 — Vague 1 d'essaims (`muse` + `deepseek`) : exploitation complète des journaux existants
- Dépouiller `/home/pc6/nexora-recherche/bench/qwen-flash-next/` (`requetes.jsonl`, `bilan-pilote.jsonl`, `bilan-smoke.jsonl`, `sondes/`, logs d'essais `origin` et `pisol`) : TTFB, débit tok/s, impact du cache KV, ratio `reasoning_chars / content_chars`, taux d'appels d'outils mal formés ou boucles.
- Dépouiller `~/.local/share/nexora-sous-agents/usage.jsonl` et `runs/*/summary.txt` : profil réel des essaims Nexora (volume de jetons par modèle, distribution du nombre de tours, coût unitaire, potentiel d'économie mensuelle).
- Auditer les contraintes exactes de la suite `outils/sous-agents/tests/ci_hors_ligne.sh` (couverture et contrats existants).

### Étape 2 — Inspection non intrusive de `pc4` et protocole d'appels d'outils
- Vérifier l'absence de requêtes actives sur `pc4` avant toute sonde directe.
- Mesurer proprement et brièvement :
  - Latence au premier jeton (TTFB) et débit (tok/s) à **1 / 2 / 4 / 8 flux parallèles** sur requêtes courtes bornées.
  - Fenêtre de contexte réelle et comportement du cache de préfixe KV (`cached_tokens`).
  - Protocole `tool_calls` (format OpenAI et traduction Anthropic `/v1/messages` via LiteLLM) : JSON strict, schémas d'outils complets vs réduits (`Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`), sensibilité à `temperature` / `top_p` / longueur du prompt système, modes de défaillance et contournements.

### Étape 3 — Vague 2 d'essaims (`deepseek` + `carbon`) : intégration de `eco-qwen` dans `outils/sous-agents/`
- **`litellm/config.yaml` & `litellm/sa_callbacks.py`** : alias `eco-qwen` (`0 $/jeton`, paramètres d'échantillonnage stabilisés pour les outils, coût `0.0` garanti dans `usage.jsonl`, retrait des champs de raisonnement contradictoires).
- **`qwen_ctl.py`** : utilitaire Python standard (sans dépendance externe) assurant :
  1. la sonde rapide de disponibilité/latence de `pc4` (`SA_QWEN_PROBE_TIMEOUT`, défaut `3s`) ;
  2. le garde-fou de concurrence inter-processus (`flock` à slots bornés `SA_QWEN_MAX_CONCURRENCY`, défaut `1`, délai d'attente `SA_QWEN_QUEUE_TIMEOUT`) pour ne jamais noyer `pc4` ni casser son cache KV ;
  3. la politique de repli propre (`SA_QWEN_FALLBACK=1`, cible `SA_QWEN_FALLBACK_MODEL` par défaut `eco-muse`, ou `eco-deepseek`) avant lancement et en cas d'échec de connexion/délai amont.
- **`lib.sh`, `sous-agent.sh`, `lot.sh`, `lot.py`, `gateway.sh`, `activation_check.py`, `orchestrateur.sh`** :
  - Support de `qwen` / `eco-qwen` partout, chargement optionnel de `STRATA_API_KEY` / `STRATA_API_BASE` sans jamais exposer de secret, compatibilité avec `carbon`/`argon`/`kimi`, budget par défaut adapté au gratuit, traçabilité du repli dans `summary.txt`.
- **`cout.py`** : `eco-qwen` à `0.00000 $`, jetons et requêtes gratuits comptés à part du total payant pour ne pas fausser les moyennes ni les totaux de facturation.
- **Tests hors-ligne** : `tests/test_qwen.py` + passage intégral de `tests/ci_hors_ligne.sh` avec couverture maintenue.

### Étape 4 — Vague 3 : essai réel de bout en bout (3 tâches × 3 modèles : `qwen` vs `muse` vs `deepseek`)
- Démarrer une passerelle LiteLLM de test isolée (`127.0.0.1:4412`) pointant vers `pc4` (avec arrêt garanti en `trap` final).
- Exécuter 3 tâches représentatives vérifiées par scripts automatiques indépendants :
  1. **T1 — Extraction structurée** : extraire l'inventaire JSON exact des routes/erreurs/constantes d'un module Python dense ;
  2. **T2 — Test unitaire** : écrire une suite `unittest` couvrant les cas limites d'un module métier Python et détectant/documentant son comportement ;
  3. **T3 — Petite retouche TypeScript** : implémenter une évolution ciblée et ses tests `node --test`.
- Comparer objectivement réussite, durée murale, nombre de tours, jetons consommés et coût réel entre `qwen` (`0 $`), `muse` et `deepseek`.
- Tester également en réel le repli `SA_QWEN_FALLBACK=1` (cible simulée injoignable → bascule propre sur `muse`).

### Étape 5 — Vague 4 d'essaims (`muse` + `carbon`) : matrice de routage et rapport final
- Rédiger `docs/premium/ferme-qwen.md` : matrice de routage honnête par famille de tâches (`qwen` vs `muse` vs `deepseek` vs `carbon` vs `terra`), règles de concurrence/contexte sur `pc4`, chiffrage d'économie mensuelle fondé sur les vrais chiffres de `~/.local/share/nexora-sous-agents/usage.jsonl`.
- Rédiger `docs/premium/rapports-vagues/Q2-RAPPORT.md` : synthèse factuelle, mesures vérifiées, fichiers livrés, preuves de tests, compteurs début/fin de `cout.sh`.
- Commits propres par sous-tâche sur `feat/ferme-qwen` (aucun `git push`, aucune fusion dans `par/integ`, aucun secret).
