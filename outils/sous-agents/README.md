# Sous-agents bon marché pour Claude Code

Objectif : l'ingénieur en chef (Claude Code) délègue du travail routinier ou massif à des modèles non-Anthropic très peu chers, pour économiser l'abonnement Claude. Chaque sous-agent est une vraie session `claude -p` (lecture, édition, écriture, recherche, Bash) dont les appels passent par une passerelle LiteLLM locale qui les traduit vers DeepInfra ou OpenRouter.

## Les trois modèles

| Alias | Modèle | Fournisseur | Prix liste (par M de jetons, entrée / sortie) | Usage |
|---|---|---|---|---|
| `eco-deepseek` (`deepseek`) | `deepseek-ai/DeepSeek-V4.1-Flash-1017` | DeepInfra | 0,20 $ / 0,60 $ | modifications en masse, tests, corrections simples |
| `eco-muse` (`muse`) | `meta/muse-spark-1.3-contributor` | OpenRouter | 0,10 $ / 0,20 $ | le moins cher : lots de dizaines, résumés, lectures, tâches courtes |
| `eco-gemini` (`gemini`) | `google/gemini-4-argon` | OpenRouter | 2 $ / 10 $ (la version `:batch` à moitié prix n'est pas interactive, non utilisée) | le plus fort : tâches difficiles, revues |

Les prix sont ceux relevés le 03/11/2026 (API publique de DeepInfra et d'OpenRouter) et inscrits dans `litellm/config.yaml`. Le coût journalisé compte les jetons en cache au plein tarif : c'est une estimation haute.

## Démarrer, arrêter

Rien à démarrer à la main : `sous-agent.sh` et `lot.sh` lancent la passerelle si elle est arrêtée. Pour la piloter :

```
outils/sous-agents/gateway.sh start|stop|restart|status|logs
```

La passerelle est un conteneur `nexora-sa-litellm` (image LiteLLM v1.106.2 épinglée par digest, sans base de données, lecture seule, sans capacités) qui écoute sur `127.0.0.1:4410` seulement. Elle est indépendante de la LiteLLM de production (port 4400) et n'en touche ni la configuration ni les clés.

Secrets, jamais dans le dépôt :
- les clés des fournisseurs sont lues dans `/home/pc6/Desktop/Deepinfra.env` (lignes `Deepinfra: …` et `Openrouter: …`, variable `SA_KEYFILE` pour changer) et passées au conteneur par variables d'environnement ;
- la clé maître de la passerelle est générée au premier lancement dans `~/.config/nexora-sous-agents/master.key` (mode 0600) ; pour la renouveler : supprimer le fichier, puis `gateway.sh restart`.

## Lancer un sous-agent

```
outils/sous-agents/sous-agent.sh [-w] <deepseek|muse|gemini> <fichier-prompt> <dossier-de-travail> [max-tours=30] [budget-usd=0.50]
```

Sans `-w`, la commande rend la main aussitôt (arrière-plan, fichier `pid`) et affiche le dossier de résultat ; avec `-w` elle attend. Le dossier de résultat (`~/.local/share/nexora-sous-agents/runs/<id>/`, ou `$SA_OUT`) contient `result.json`, `transcript.jsonl` (flux complet), `summary.txt` (une ligne : statut, tours, coût, jetons, durée), `stderr.log`, `pid` et `done` quand c'est fini.

Exemple d'une ligne de résumé : `OK:success eco-muse … tours=7 cout=$0.00111 jetons=21653in/2920out/6req duree=28s`.

Variables : `SA_TIMEOUT` (secondes, défaut 900), `SA_EXTRA_RO` (dossiers supplémentaires montés en lecture seule), `SA_PORT`.

## En lancer cinquante

```
outils/sous-agents/lot.sh <deepseek|muse|gemini> <dossier-de-prompts> <dossier-des-workdirs> [parallélisme=8]
```

Un fichier `NOM.txt` du dossier de prompts travaille dans `<workdirs>/NOM/` (un dépôt ou une copie par tâche : deux agents ne doivent jamais écrire dans le même dossier). Le parallélisme est la limite globale de concurrence ; `LOT_BUDGET` (défaut 5 $) est le plafond global, `LOT_RUN_BUDGET` (défaut 0,30 $) le plafond par agent, `LOT_TURNS` (défaut 30) le nombre de tours. Les agents lancés après le plafond global sont sautés (`SKIP:plafond_global`). Le résultat est un `index.tsv` d'une ligne par agent. Mesuré : 24 agents `muse` en parallèle (12 à la fois) en 33 s pour 0,012 $ au total.

## Suivre la dépense

```
outils/sous-agents/cout.sh [--since AAAA-MM-JJ] [--run <préfixe>]
```

Somme par modèle depuis le journal `~/.local/share/nexora-sous-agents/usage.jsonl`, écrit par la passerelle (horodatage, identifiant d'exécution, alias, jetons, coût, durée ; jamais les prompts ni les réponses). Le coût affiché par Claude Code lui-même (`total_cost_usd`) est faux pour ces modèles : seul le journal de la passerelle fait foi.

## Sécurité par défaut

- Chaque agent tourne dans un bac à sable `bwrap` : système en lecture seule, `HOME` vide (ni `~/.ssh`, ni clés, ni autres dépôts), écriture seulement dans le dossier de travail, aucun réseau (un pont unix n'atteint que la passerelle locale). Vérifié : lecture de `~/.ssh` et des clés, écriture hors dossier et accès Internet échouent.
- Outils limités à Read, Edit, Write, Glob, Grep et Bash ; WebFetch, WebSearch, sous-agents et, par règle de refus, `git push`, `ssh`, `scp`, `sudo`, `curl`, `wget` sont interdits. Aucun accès à GitLab, Proxmox, aux VM, aux machines du fondateur ni à d'autres dépôts.
- Plafonds par exécution : tours (`--max-turns`), durée (`SA_TIMEOUT`) et dépense (un garde-fou lit le journal toutes les 4 s et tue l'agent ; une seule réponse très longue peut dépasser le plafond de quelques millièmes de dollar). Plafond global de la passerelle : 20 $ par 30 jours.
- `--bare` : aucun hook, plugin, mémoire ni `CLAUDE.md` du dépôt n'est chargé. Tout le contexte utile doit être dans le prompt.
- Le dossier de travail doit être une copie ou un dépôt jetable dont on relit ensuite le `git diff`.

## Limites

- Pas d'outils web, pas de MCP, pas de fonctions propres à Anthropic (skills, sous-agents imbriqués, mode ultra, etc.).
- Les modèles ne sont pas Claude : qualité inégale, parfois des erreurs sûres d'elles. Le résultat d'un sous-agent bon marché n'est jamais utilisé sans vérification (tests, relecture du diff par l'ingénieur en chef).
- Le garde-fou de dépense compte ce que la passerelle a journalisé ; les requêtes en cours au moment de l'arrêt peuvent ne pas l'être.

## Guide d'aiguillage

| Tâche | Modèle |
|---|---|
| Modifications répétitives sur beaucoup de fichiers, renommages, migrations mécaniques | `muse` en lot, ou `deepseek` si le code est dense |
| Écrire ou compléter des tests, corriger un test qui échoue | `deepseek` |
| Résumer ou cartographier un module, un dossier, des journaux | `muse` |
| Recherche dans le code (sans web), inventaires, extraction de données | `muse` |
| Revue de code, bogue subtil, conception, tâche en plusieurs étapes dépendantes | `gemini` |
| Recherche qui exige le web | aucun : le faire soi-même |

Règle : on commence par le moins cher (`muse`), on monte à `deepseek` puis `gemini` si le test ou la relecture échoue. Toute production d'un sous-agent est vérifiée par des tests exécutés par l'ingénieur en chef, ou relue, avant d'être reprise.

## Comment l'ingénieur en chef s'en sert

1. Préparer un dossier de travail jetable (copie ou `git worktree`) et un fichier prompt autonome : objectif, fichiers, commande de test, critère de réussite.
2. Lancer `sous-agent.sh` (ou `lot.sh`) en arrière-plan avec Bash `run_in_background`, puis lire `summary.txt` / `index.tsv`.
3. Vérifier : relancer soi-même les tests et lire `git diff` ; ne rien fusionner sans cela.
4. `cout.sh` en fin de session pour rendre compte de la dépense.

## Essai de capacité (03/11/2026)

`tests/capacite.sh` fabrique et lance 3 tâches par modèle, puis `tests/verifie.sh` les juge par des tests indépendants de l'agent : T1 renommage de fonction sur 5 fichiers et correction de tests (Python), T2 ajout d'une fonctionnalité avec tests dans un projet TypeScript, T3 lecture d'un module et résumé exact plus correction d'un bogue.

| Modèle | Réussite | Coût moyen par tâche | Durée moyenne | Tours par tâche |
|---|---|---|---|---|
| `deepseek` | 3/3 | 0,007 $ | 46 s | 11, 6, 8 |
| `muse` | 3/3 | 0,002 $ | 37 s | 16, 9, 7 |
| `gemini` | 3/3 | 0,048 $ | 52 s | 6, 15, 8 |

Ces tâches étaient faciles : elles ne départagent pas vraiment les modèles, et 3 tâches par modèle ne donnent pas un taux de réussite fiable. Aucune requête n'a échoué sur plus de 190 appels (appels d'outils parallèles, blocs de réflexion, flux continu : traduits correctement par LiteLLM). Écarts à surveiller : `muse` et `gemini` émettent des blocs de réflexion (sans conséquence constatée) ; `gemini` coûte environ 7 fois `deepseek` et 28 fois `muse` par tâche pour un résultat identique sur ces essais.
