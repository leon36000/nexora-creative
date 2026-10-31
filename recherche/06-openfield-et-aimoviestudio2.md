# 06 — OpenField et AI Movie Studio 2 (complément du 30/10/2026)

URL fournies par le fondateur. Le rapport 01 ne les avait pas identifiés : erreur corrigée ici. Les deux dépôts ont été clonés en lecture seule ; aucun code n'a été exécuté, aucune dépendance installée. Étiquettes : [CODE] lu dans le dépôt, [DOC] README/notices.

## OpenField — https://github.com/wexloops/openfield

| Point | Constat |
|---|---|
| Licence | **MIT** (David Wexler / Strangeloop Studios) [CODE `LICENSE`, `package.json`] |
| Âge, activité | 5 commits (historique écrasé), premier le 27/10/2026, dernier le 29/10/2026 ; un seul auteur [CODE `git log`]. Projet du concours Comfy « Open Source Higgsfield » [DOC] |
| Taille, pile | ≈ 23 300 lignes TypeScript. Navigateur : Vite + **React 19** + three.js. Serveur : **Fastify 5**, `@comfyorg/sdk` (Comfy API v2), `better-sqlite3`, Zod 4, MCP SDK [CODE `package.json`] |
| Architecture | Navigateur → serveur OpenField → comfy-api-proxy → ComfyUI. **Chaque application est un constructeur de graphe TypeScript** (`server/graphs/*.ts`, 17 fichiers) qui produit un graphe ComfyUI au format API ; l'utilisateur ne touche jamais ComfyUI [CODE `server/engine.ts`, README] |
| Fonctions | Vidéo (28 préréglages de mouvement, première/dernière image), Image, Boucle, Objet 3D, Son ; **Director** (genre, caméra, cadrage, lumière, pellicule, étalonnage, époque) ; **Scene** (un LLM découpe une scène en 2 à 6 plans, rendus et montés) ; **Stage** (mise en place 3D dans le navigateur → plan) ; **Cast** (personnage/objet/lieu en `@mention`) ; Mirror (transfert de mouvement depuis le téléphone), Reshoot, Effects, Edit, Relight, Upscale, Extend, Transitions, HDR (EXR ACEScg, HLG) ; MCP à 31 outils ; chaque prise s'ouvre comme son graphe exact [DOC README, CODE `src/catalog.ts`, `mcp/server.ts`] |
| H3 | Constructeur `server/graphs/h3.ts` : i2v, première+dernière image, références ; LoRA turbo lightx2v ; **mesures notées par l'auteur sur RTX 5090** (déchargement mémoire, le turbo ne paie pas aux petites tailles) ; H3 désactivé par défaut et marqué géo-restreint [CODE] |
| Données | SQLite local : `takes`, `projects`, `cast`, `take_workflows`, `speed` (secondes par étape mesurées), `preambles` [CODE `server/jobs.ts`] |
| Multi-utilisateur | **Aucun** : « Keep it on loopback: the server has no authentication » ; seul le mode « judge » ajoute un mot de passe, un plafond et des limites [DOC, CODE `server/judge.ts`] |
| Tests | Pas de suite de tests unitaires ; `typecheck`, `test:judge`, `mcp:check` (parité), `doctor` [CODE `package.json`] |
| Dépendances de modèles | Moteur vidéo par défaut **LTX-2.5** et ses IC-LoRA (Stage, Mirror, Effects, HDR, Cast vidéo) ; images Qwen-Image (Apache-2.0) ; FLUX.2 dev et 4x-UltraSharp **non commerciaux** (optionnels) [DOC `THIRD_PARTY_NOTICES.md`] |
| Nœuds GPL | ComfyUI, VideoHelperSuite, KJNodes (GPL-3.0) tournent dans le processus ComfyUI séparé, appelé par API [DOC notices] |

### Blocage LTX-2.5 (vérifié par moi dans `LICENSE-2_x` de Lightricks)
- §2.1 : licence payante obligatoire pour toute entité à partir de 10 M$ de revenus annuels.
- Annexe A, point 20 : interdit d'utiliser LTX-2.x ou ses dérivés dans un produit, service ou application qui **concurrence directement** les produits commerciaux de Lightricks ou vise à les remplacer, sans licence commerciale séparée. Lightricks vend LTX Studio, un studio vidéo IA : **Nexora Creative tombe très probablement sous cette clause.**
- Annexe A, point 18 : usage commercial interdit pour entraîner ou améliorer un autre modèle.

Conséquence : dans un fork Nexora, tous les graphes LTX doivent être **remplacés** (H3 pour les comptes du territoire, Wan 2.2 / Kandinsky / Cosmos3 sinon) ou couverts par une licence Lightricks écrite. Les fonctions qui reposent sur des IC-LoRA LTX (Stage, Mirror, Effects, HDR, Cast vidéo) perdent leur moteur et sont à rebâtir sur des équivalents (Wan VACE / Animate, etc.) ou à mettre de côté.

### Verdict
**Meilleure base trouvée** pour Nexora Creative, à forker comme Sim l'a été pour WorkStudio :
- même famille technique que Nexora (TypeScript, React 19, Zod, Node), interface qui tourne déjà dans le navigateur ;
- son patron « constructeur de graphe côté serveur » est exactement le compilateur de recettes demandé par la sécurité (ComfyUI jamais exposé) ;
- il apporte déjà Director, Scene, Cast, Stage, MCP, HDR, mesures de vitesse par étape, et un graphe H3 éprouvé.

À ajouter ou remplacer : comptes et organisations (connexion unique Nexora), PostgreSQL multi-organisation au lieu de SQLite, stockage objet au lieu du disque local, file Nexora et agents GPU au lieu d'un ComfyUI local unique, crédits, Privacy Router, registre de capacités, moteurs non-LTX. Risques : projet de 3 jours, un seul auteur, pas de tests ; on forke une fois, on en devient mainteneur, et on ajoute nos propres tests.

## AI Movie Studio 2 — https://github.com/Heroesjouney/AIMovieStudiov2

| Point | Constat |
|---|---|
| Licence | **AGPL-3.0** [CODE `LICENSE`] |
| Activité | 65 commits, auteur principal à 61, dernier le 15/09/2026 [CODE `git log`] |
| Pile | Next.js 14 + React 18 + react-three-fiber + Zustand ; FastAPI (Python) ; pilotes ComfyUI, Fal, Replicate, Fish Speech ; ≈ 39 600 lignes [CODE] |
| Fonctions | Coffre de projets/scènes/plans, **storyboard 3D** (caméra, cône de champ, alerte de la règle des 180°), continuité par références, **Long Take** (enchaînement première/dernière image + couture ffmpeg), import de scénarios Fountain / Final Draft, export XML vers Premiere/DaVinci, prévisualisation caméra 3D avec images clés, pilotes interchangeables [DOC] |
| Multi-utilisateur | Aucun ; fichiers JSON et réglages locaux, clés d'API cloud saisies dans l'interface [CODE `routes_settings.py`] |

### Verdict
**Source d'idées seulement, pas de code.** L'AGPL-3.0 oblige à publier les sources de toute version modifiée offerte par le réseau : incompatible avec un service Nexora fermé, et impossible à mélanger au fork MIT sans faire basculer l'ensemble. Idées à réécrire en salle blanche : alerte de la règle des 180°, Long Take, import Fountain/FDX, export XML de montage, prévisualisation caméra par images clés.
