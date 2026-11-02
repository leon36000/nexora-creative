# 14 — Harnais Nexora Creative : distillation de mémoire (AMD), éval et auto-optimisation (02/11/2026)

Demande du fondateur : un modèle moins cher doit *in fine* monter les films ; Nexora Creative doit donc lui donner des capacités de montage hors du commun. Pistes citées : « AMD (agent memory distillation) » avec Claude Code, puis un harnais propre à Nexora Creative ; aucune piste à négliger.
Statut : **conception** [PROPOSÉ]. Niveaux de certitude : [CONFIRMÉ] lu à la source aujourd'hui, [CONNU] connaissance générale non revérifiée aujourd'hui, [HYPOTHÈSE], [ESTIMÉ]. La note 13 (API de montage, autre agent) n'existait pas sur `gitlab/developpement` à l'écriture : les outils du §3 sont donc des outils typés *supposés*, à aligner sur elle.

## 1. Ce qu'est « AMD »

**[CONFIRMÉ] Agent Memory Distillation (AMD)** existe sous ce nom exact : article *« Agent Memory Distillation: Empowering Small LLM Agents with Hierarchical Teacher Memory »*, Taeil Kim, Kangsan Kim, Sung Ju Hwang, 7 août 2026.
- arXiv : https://arxiv.org/abs/2608.07169 (HTML : https://arxiv.org/html/2608.07169v1) ; page HF : https://huggingface.co/papers/2608.07169
- Code de recherche : https://github.com/taeilkim2465/agentic_memory_distillation (9 étoiles, dernière mise à jour 10/08/2026, **licence non indiquée** sur la page).
- Ce n'est **pas un logiciel installable** : c'est une technique + un dépôt de reproduction qui se superpose aux dépôts de trois bancs (AppWorld/ace-appworld, BFCL V3/gorilla, ToolSandbox) ; dossiers `memp/`, `rb/`, `sasm/` = comparaisons. Il ne se « met pas sur » Nexora Creative ni sur Claude Code : on en reprend **la méthode**, avec Claude dans le rôle du *professeur*.

**La méthode** (chiffres tirés de l'extraction de la page arXiv, non recoupés avec le PDF) : sans entraînement (*training-free*), un agent « professeur » fort produit des trajectoires réussies, distillées **hors ligne** en trois niveaux de mémoire que l'élève lit **figée** :
1. **Mémoire de workflow** : par tâche réussie, une consigne verbalisée (outils, préconditions, règles de décision, indices de validation, échecs courants), valeurs concrètes remplacées par des jetons typés (`<ID>`, `<FILE_PATH>`). Récupérée par similarité cosinus sur l'énoncé de la tâche, **injectée au début** (top-1). Format texte = meilleur (49,4 % contre 44,1 % en code).
2. **Mémoire de sous-tâche** : la trajectoire découpée en segments sémantiques (étiquette, description, exemples d'exécution) ; l'élève décompose sa tâche (≤ 6 sous-tâches), un segment top-1 par sous-tâche. Format « description + blocs de code » : 49,4 % contre 23,2 % en langage seul. C'est le niveau qui apporte le plus.
3. **Mémoire de fonction** : par outil, un appel exemple réel + schéma ; injectée **réactivement**, seulement quand l'appel d'outil échoue (indice ajouté au message d'erreur).

Résultats rapportés (corrigés le 02/11 d'après la page du projet https://agent-memory-distillation.github.io/ ; l'extraction arXiv de la première version de cette note donnait des moyennes inférieures, +27,2 / +11,2 / +3,4, non retenues) : professeur GPT-5-mini ; élève Qwen3-4B : **AppWorld 14,88 → 49,40 (+34,5 points ; le professeur seul fait 50,0), BFCL V3 +23,0, ToolSandbox +3,9**. Autres élèves : Qwen3-8B, Gemma4-E4B, Llama3.1-8B. La mémoire de sous-tâche est celle qui compte le plus ; prose pour les plans, code pour l'exécution ; **k = 1** ; la mémoire collectée par l'élève seul n'aide presque pas ; un professeur *plus accessible* vaut mieux qu'un professeur plus fort. Enseignements transposables : **k = 1 est optimal** (k plus grand dégrade, sous-tâche 49,4 → 33,3) ; la mémoire fabriquée par l'élève lui-même est nettement moins bonne que celle du professeur ; un professeur plus fort n'est pas toujours meilleur (GPT-5-mini > DeepSeek V4 Pro pour l'élève 4B) ; le gain culmine pour les petits élèves (4B) et diminue avec la taille.
**Limites déclarées** : mémoire figée (aucune adaptation en cours d'usage) ; validé seulement sur de l'appel d'outils texte (API Python/fonctions) ; **non vérifié en multimodal ni en génération ouverte** : le montage vidéo en est un cas hors du domaine validé [HYPOTHÈSE de transfert].

**Pistes voisines**
- [CONFIRMÉ] **ACE — Agentic Context Engineering** (Zhang et al., Stanford/SambaNova) https://arxiv.org/abs/2510.04618 : le contexte est un *playbook* évolutif (générateur → réflecteur → curateur, mises à jour **incrémentales par delta**, jamais de réécriture complète), +10,6 % sur agents, utilisable hors ligne (prompt système) et en ligne (mémoire). Implémentation d'échafaudage : https://github.com/mgechev/ACE-open (Python). C'est la brique « règles apprises des échecs ».
- [CONFIRMÉ comme lignes de base du dépôt AMD] Memp (mémoire procédurale) et ReasoningBank (`rb/`) ; [CONNU, non revérifié] Reflexion, Voyager (bibliothèque de compétences), Mem0, Letta/MemGPT, A-MEM (mémoire conversationnelle ou personnelle, moins adaptée au savoir-faire de montage).
- **Si le fondateur pensait à autre chose** (le sigle AMD désigne aussi le fabricant de puces) : aucune autre technique « AMD » n'a été trouvée ; l'article ci-dessus est de loin le candidat le plus plausible, daté d'il y a trois mois, et colle exactement à « un modèle bon marché hérite de l'expérience d'un fort ».

**Décision « open source d'abord »** : ne pas forker le dépôt AMD (surcouche à trois bancs, licence absente, pas de sens hors AppWorld). Reprendre le *schéma* à trois niveaux (§4) ; pour l'optimiseur, utiliser **DSPy/GEPA** (déjà éprouvés par le fondateur) en Python hors ligne.

## 2. Ce que le travail antérieur du fondateur apporte (lu : 3 PDF du 30/09 et 03/10)

Protocole GEPA/DSPy/Meta-Harness autour de DeepSeek Harness/Cordis, modèle GLM 5.3 Flash, plafond 20 USD.
**Réutilisable tel quel**
- **Séparation stricte apprentissage / validation / test scellé**, identifiants et empreintes SHA-256 préenregistrés, test fermé aux optimiseurs.
- **Registre** (SQLite + JSONL : candidats, parents, versions, métriques, coût, jetons, latence, erreurs ; secrets jamais dans les traces destinées aux optimiseurs).
- **Boucle bornée** : observer les échecs → hypothèse → candidat → test → comparer → promouvoir ou rejeter ; arrêt après plafond, 3 fenêtres sans promotion ou contrat obligatoire en échec.
- **Règle de promotion** : borne inférieure de l'IC à 95 % du gain de qualité > 0, **ou** coût par tâche −10 % avec non-infériorité qualité (2 points) ; latence p95 ≤ +10 % ; front de Pareto qualité/coût ; bootstrap **groupé par tâche**, comparaisons appariées, intervalles simultanés ; une validation réutilisée ne devient pas une preuve de généralisation.
- **Contrats obligatoires avant toute évaluation coûteuse** (isolation, JSON valide, budget) ; ablations brique seule / combinaison / retrait.
**Leçons négatives à intégrer** (rapport du 03/10) : référence 75,0 % [53 ; 93] ; DSPy −1,0, MIPROv2 +5,2 [−10,4 ; +22,9], GEPA 0,0 : **tous indéterminés**, car 32 tâches × 3 essais ne détectent que des effets ≥ ~15-20 points ; Meta-Harness et le bras combiné sans artefact car **sorties tronquées à 4 096 jetons** (réponses brutes non conservées : cause non prouvable) ; 14,17 USD dépensés sur 20 pour aucune promotion. D'où quatre règles pour Nexora : (a) **conserver toute réponse brute** et fixer `max_tokens` généreux ; (b) **métrique continue** (score composite 0-1) plutôt que réussite binaire, pour gagner de la puissance ; (c) **commencer par les leviers à gros effet** (outils déterministes, validateurs, mémoire du professeur à la AMD, repli code) et ne lancer l'évolution de prompts qu'après une analyse de puissance ; (d) un plafond en dollars par campagne, vérifié dans le registre.
**Notes du dépôt** : `09-llm-au-maximum.md` (règle « le LLM propose, le code dispose », 12 rôles, schémas Zod + réparation + repli, jeu d'or de 40 intentions, métriques de contrôle d'abord déterministes) et `10-qualite-h3.md` (leçons mesurées sur H3 : « cinematic CG » pousse vers le rendu 3D, notes parasites du réécrivain : ce sont de futures **règles apprises**). Déjà en place dans le code : `competences.ts` + `competences/*.md` (procédures versionnées par rôle, dont `montage.md` et `juge.md`), `juge.ts`, `controle.ts`, `agent.ts` (Producteur : outils Zod, devis, plafonds), `llm.ts` (rôle → modèle).

## 3. Le harnais : principes et surface d'outils

**Principe directeur : le modèle bon marché ne fait que le delta au-dessus d'une base de code.**
1. **Base déterministe** `montage_auto` (code pur) : coupes sur la grille de temps forts, durées de plan dans la bande du genre, `loudnorm`, sous-titres posés, carton final. Toute sortie du LLM est un *patch* appliqué à cette base ; si tout échoue, la base part telle quelle. Le plancher de qualité ne dépend jamais du modèle.
2. **Macro-outils plutôt que primitives** : un petit modèle réussit mieux 6 appels de haut niveau que 40 appels fins. Les recettes distillées deviennent des outils (`monter_pub`, `monter_bande_annonce`, `boucle_parfaite`).
3. **Édition = liste de décisions typée (EDL JSON)**, jamais de texte libre ni de commande shell ; état unique versionné ; annuler/rejouer.
4. **Boucle bornée** : analyser → planifier → construire → mesurer (métriques gratuites) → au plus 2 révisions guidées par les métriques et le juge.
5. **Meilleur-de-n par métriques** : n = 2-3 candidats, choisis par métriques déterministes (gratuites) avant tout appel au juge VLM payant.
6. **Cascade** : modèle bon marché d'abord ; escalade vers un modèle intermédiaire seulement si la porte de qualité échoue deux fois.

**Outils typés** (à aligner sur la note 13) : `analyze_media` (durée, plans, silences, parole/transcription, énergie par fenêtre de 0,5 s, tempo + temps forts, luminance, visages) ; `plan_edit` (brief → EDL squelette) ; `build_timeline` (applique des opérations de patch à l'EDL) ; `cut_on_beat` (aimante une coupe sur le temps fort à ±60 ms) ; `mix_audio` (ducking, cibles LUFS, fondus 30 ms) ; `place_text` (sous-titres, cartons, zone de sécurité) ; `render_preview` (basse résolution) ; `critique` (métriques + juge, renvoie une liste d'écarts typés) ; `revise` (opérations ciblées sur l'EDL). Chaque outil : schéma Zod d'entrée et de sortie, erreurs typées avec champ `indice` (nourrit la mémoire de fonction), coût en crédits déclaré, idempotent.
**EDL minimale** :
```jsonc
{ "version": 1, "format": "16:9", "fps": 30, "duree_cible_s": 30, "genre": "pub",
  "pistes": { "video": [{"id":"v1","clip":"<CLIP_ID>","entree":0.0,"sortie":2.4,"debut":0.0,"transition":"coupe"}],
              "musique": [{"piste":"<MUSIQUE_ID>","debut":0,"gain_db":-8}],
              "texte": [{"texte":"…","debut":24.0,"fin":29.0,"style":"carton"}] },
  "metadonnees": { "modele":"z-ai/glm-5.3", "savoir": ["montage@3","pub-recette@2"] } }
```
**Passerelle MCP** : exposer les mêmes outils en serveur MCP. Claude Code (le professeur) les pilote alors en session et enregistre ses trajectoires **dans le format exact** que lira l'élève : zéro conversion entre l'enseignement et l'usage.

## 4. Mémoire et distillation du savoir-faire de montage

**Correspondance AMD → montage**
| Niveau AMD | Équivalent Nexora | Récupération | Format |
|---|---|---|---|
| Workflow | **Recette de genre** (pub, bande-annonce, explicatif, réseaux 9:16, clip/boucle) : structure (accroche / montée / résolution / appel à l'action), bandes de durée de plan, rythme vs énergie, règles audio | genre + format + durée + énergie du brief, **top-1** | texte court (≤ 600 mots) |
| Sous-tâche | **Segment de montage** : « ouverture accrocheuse », « coupe sur le drop », « enchaîner deux plans d'action », « carton final lisible », « raccord de boucle » ; chaque segment = description + extrait d'EDL réel | une requête par segment du plan du modèle, **top-1 chacun** | description + bloc JSON (le code l'emporte) |
| Fonction | **Appel exemple valide par outil** + piège connu | **réactive** : seulement sur erreur de validation de l'outil | indice joint au message d'erreur |
Jetons typés pour les valeurs concrètes (`<CLIP_ID>`, `<BPM>`, `<DUREE_S>`). **Un seul exemplaire par niveau et par appel** (résultat AMD sur k).

**Qui distille ?** Claude (le professeur) hors ligne : (1) il monte, en session via le MCP, les briefs d'**apprentissage** (jamais ceux de validation/test) ; (2) un tri automatique garde les trajectoires qui passent la porte de qualité et le juge (D+) ; (3) Claude les découpe en segments, anonymise les valeurs, rédige la recette ; (4) un humain relit au premier lot, ensuite les entrées entrent par revue de diff. Un professeur plus faible peut suffire (résultat AMD) : prévoir une distillation par lot API avec un modèle intermédiaire pour les volumes, Claude réservé aux recettes de référence [HYPOTHÈSE].

**Les cinq artefacts** (tout versionné, tout fichier ou ligne SQLite, jamais exécuté)
```
app/server/nexora/harnais/
  savoir/
    recettes/<genre>.md        # frontmatter: name, version, roles, genres, formats ; texte ≤ 600 mots
    segments/<id>.json         # Segment (ci-dessous)
    fonctions/<outil>.json     # appel exemple valide + pièges
    regles/<role>.json         # règles apprises (ci-dessous)
    styles/                    # par utilisateur : en base, pas en dépôt
  savoir.ts                    # charge, valide (Zod), récupère top-1, assemble le message système (cachable)
  distiller/ (hors ligne)      # tri D+, découpe, anonymisation, écriture en revue
```
```jsonc
// Segment (sous-tâche) — retrouvable par étiquette+description, injecté en code
{ "id":"seg-pub-accroche-03","version":2,"genre":["pub","reseaux"],"etiquette":"ouverture_accrocheuse",
  "description":"Premier plan < 1,2 s, mouvement vers la caméra, texte ≤ 4 mots, coupe sur le 1er temps fort",
  "extrait_edl":{"video":[{"clip":"<CLIP_ID>","entree":0,"sortie":1.1}]},
  "preuve":{"brief":"train-007","score":0.86,"juge":8,"modele_professeur":"claude"}, "statut":"actif" }
// Règle apprise d'un échec du juge/des métriques (style ACE : delta, jamais réécriture)
{ "id":"r-0042","role":"montage","texte":"Ne jamais poser un texte blanc sur un plan de luminance > 0,7 sans fond.",
  "source":{"brief":"train-011","metrique":"lisibilite","valeur":2.9},"aides":4,"nuisances":0,"statut":"actif" }
```
Chaque entrée porte compteurs `aides/nuisances` mis à jour par l'éval : une règle qui nuit est désactivée automatiquement. Plafond ~8 000 jetons de savoir par rôle (déjà vérifié par test dans `competences.test.ts`).
**Stockage** : fichiers + SQLite `better-sqlite3` (déjà la pile de l'application) suffisent largement jusqu'à quelques milliers d'entrées ; similarité par vecteurs en mémoire (embedding via la passerelle, ex. Qwen3-Embedding) ou, **pour la tranche 1, simple filtre structuré** (genre, format, durée, énergie) sans vecteurs. **pgvector** seulement si le service hébergé multi-locataire passe sur PostgreSQL et dépasse ~10 000 entrées.
**Mémoire de style par utilisateur** (donnée, pas instruction) : préférences observées (rythme, typographie, palette, musique, durée), alimentée par les acceptations/refus ; plafonnée à ~300 jetons, isolée par organisation, effaçable, jamais mêlée au savoir global ; avec consentement seulement, ses montages acceptés peuvent proposer de nouveaux exemplaires.
**Deuxième voie à terme** : quand ≥ 500 trajectoires validées existent, distillation de poids (SFT/LoRA d'un petit modèle ouvert) comparée à la mémoire sur le même banc ; hors tranche 1.

## 5. Banc d'évaluation (le même pour tous les modèles)

**Jeu de 30 briefs** en `harnais/eval/briefs/*.json` : 6 genres × 5 (pub produit, bande-annonce, explicatif, réseaux 9:16, clip musical/boucle, présentation de services), formats 16:9 / 9:16 / 1:1, durées 10-60 s. Un brief = énoncé en français, inventaire de médias **pré-analysés** (aucun GPU : clips tirés de `~/nexora-creative-data/rendus` et `marketing/nexora/refonte-medias`, métadonnées d'analyse figées), musique avec grille de temps forts et courbe d'énergie, contraintes (durée, texte imposé, marque). **Partition** : 12 apprentissage (source des exemplaires), 6 validation (choix des candidats), 12 test **scellé** (publié seulement aux jalons). Un exemplaire ne sert jamais son propre brief (retrait à l'exécution).
**Métriques automatiques** (toutes en code, gratuites ; sur l'EDL pour la tranche 1, sur le rendu ensuite) :
| Critère | Contrôle |
|---|---|
| **porte** : validité | schéma Zod, références de médias existantes, pas de chevauchement, durée ± 5 % de la cible |
| rythme | corrélation de Spearman entre densité de coupes (fenêtres de 2 s) et courbe d'énergie ; part de coupes à ±60 ms d'un temps fort ; durée moyenne de plan dans la bande du genre ; aucune coupe < 0,5 s |
| son | LUFS intégré dans la cible ± 1 (−14 réseaux) ; crête ≤ −1 dBTP ; ducking : musique ≥ 8 dB sous la voix ; fondus aux raccords (`ebur128`/`loudnorm`) |
| luminance | pas d'image noire ni figée (`controle.ts`) ; saut de luminance moyen aux coupes sous seuil |
| texte | contraste ≥ 4,5:1 sur la zone ; hauteur ≥ 4 % de l'image ; zone de sécurité ; ≤ 17 caractères/s ; ≥ 1 s à l'écran ; ≤ 2 lignes × 42 car. |
| boucle/raccord | pour les boucles : distance d'histogramme et SSIM dernière/première image, fondu audio au raccord (`seam.ts` existe) |
| coût | jetons entrée/sortie × tarif, nombre d'appels d'outil, erreurs d'outil, révisions, crédits |
| juge VLM | `qwen/qwen3.8-27b` sur planche de 4-6 images + rubrique (accroche, cohérence, lisibilité, finition) → 0-10 ; comparaison par paires contre la sortie de la base `montage_auto` ; **ne pèse que 30 %** du score et ne casse jamais une porte (juges généralistes peu fiables, note 05) |
**Score composite** = porte × (0,7 × moyenne pondérée des métriques + 0,3 × juge/10). **« Bon résultat »** = porte franchie, composite ≥ 0,70, juge ≥ 7. **Indicateur central : coût (USD) par bon résultat** et taux de bons résultats du premier coup.
**Exécution façon CI** : `npm run eval:harnais -- --modele z-ai/glm-5.3 --bras memoire --reps 3 --partition validation` ; chaque tentative écrit une ligne au registre JSONL (brief, bras, modèle, version du savoir, jetons, coût, score par métrique, réponse brute, durée) ; rapport Markdown + tableau de Pareto ; plafond en dollars par campagne ; job nocturne sur la partition validation à chaque changement de savoir/prompt/modèle ; test scellé manuel.
**Bras** : `A_code` (base seule, sans LLM) · `A0` (modèle + `montage.md` actuel) · `A1` (+ recette et segment top-1 + validateur/réparation + indice de fonction) · `A2` (+ règles apprises) · `A3` (+ meilleur-de-3 par métriques). **Modèles** : GLM-5.3 (référence du jour), Qwen3.5/3.8, MiniMax-M3, DeepSeek-V4.1-Flash, Kimi-K3, MiMo-V2.6-Flash (liste du catalogue de la note 09, tous à confirmer disponibles), plus un modèle intermédiaire de repli. Comparaison **appariée par brief**, IC à 95 % par bootstrap groupé par brief, sur coût par bon résultat.
**Puissance** [ESTIMÉ] : avec métrique continue et appariement, 12 briefs × 3 répétitions détectent grossièrement des gains composites ≥ 0,08-0,10 ; le rapport du 03/10 montre qu'avec une métrique binaire et 32 tâches on ne voit rien sous ~15 points. Mesurer d'abord la variance entre répétitions et le MDE réel (étape 0), et n'engager l'optimiseur qu'en fonction.

## 6. Boucle d'auto-optimisation (après le banc, pas avant)

Python hors ligne (DSPy ≥ 3.4, GEPA, et l'infrastructure de registre/campagne du fondateur) ; l'exécution en production ne lit que des artefacts gelés (Markdown/JSON). Trois boucles :
1. **Réflexion sur échec (Reflexion/ACE)** : pour chaque tentative sous la porte ou sous 0,5, un réflecteur (modèle intermédiaire) lit EDL + métriques + texte du juge → cause racine → **règle candidate** ; un curateur la fusionne par *delta* (ajout / correction / retrait), jamais par réécriture ; la règle entre `statut: essai` et passe `actif` seulement si son effet apparié sur la validation est ≥ 0 (compteurs aides/nuisances).
2. **Évolution de compétences (GEPA-like)** : les fichiers `recettes/*.md` et `montage.md` sont des candidats mutables, mutation = diff borné (≤ 15 % du texte) proposé à partir des traces d'échec ; sélection sur le front de Pareto (score, coût), promotion par la règle du fondateur (§2) ; tous les candidats gardent leurs parents.
3. **Enrichissement continu des exemplaires** : montage accepté par un utilisateur (avec consentement) ou d'un score élevé → candidat exemplaire → revue → banque.
**Plafonds** : dollars par campagne (ex. 5 USD, vérifié dans le registre avant chaque lot), ≤ 3 fenêtres sans promotion, ≤ 20 candidats par campagne, le test scellé jamais lu par l'optimiseur, retour automatique à la version précédente si une régression du banc de surveillance dépasse 2 points.

## 7. Garde-fous

Le LLM propose, le code dispose (note 09). Arguments d'outils validés par Zod, une réparation avec le message du validateur + indice de fonction, puis repli ; **au plus 25 pas, 60 000 jetons et un devis de crédits** par montage, décidés par le code (le modèle ne peut ni dépenser ni choisir un moteur interdit) ; rendu final toujours précédé d'`analyze`/`critique` gratuits ; `montage_auto` en repli déterministe à toute exception, plafond atteint ou JSON invalide ; interrupteur par rôle et par version de savoir ; le savoir est du texte et des JSON, jamais du code exécuté ; écriture de savoir uniquement par distillation relue (anti-empoisonnement et anti-dérive) ; mémoire de style isolée par organisation ; aucun média utilisateur envoyé au professeur sans consentement ; journal sans contenu (comme le Privacy Router).

## 8. Ordre de construction (efforts [ESTIMÉS], une personne)

| # | Étape | Effort |
|---|---|---|
| 0 | **Tranche 1** (§9) : banc minimal sur EDL + bras A_code/A0/A1 | **1 jour** |
| 1 | Alignement sur la note 13 : EDL canonique, outils typés, `montage_auto`, passerelle MCP | 3 j |
| 2 | Banc complet : 30 briefs et fixtures, métriques son/luminance/texte/boucle depuis le rendu, juge VLM, registre, rapport, CI nocturne | 4 j |
| 3 | Distillation : sessions du professeur sur 12 briefs d'apprentissage, tri D+, recettes (6 genres), ~60 segments, fonctions par outil, revue | 4 j |
| 4 | Règles apprises (réflecteur + curateur, compteurs aides/nuisances) | 2 j |
| 5 | Matrice de modèles + courbe coût par bon résultat ; choix du modèle par rôle | 2 j (+ coût API) |
| 6 | Boucle GEPA-like sur recettes, après analyse de puissance | 3 j |
| 7 | Mémoire de style par utilisateur + enrichissement par acceptations | 3 j |
| 8 | Éventuelle distillation de poids (≥ 500 trajectoires) | à décider |
Total ≈ 3-4 semaines pour 1-7 ; l'étape 0 donne un premier chiffre dès demain.

## 9. Tranche 1 : réalisable en un jour, gain mesurable

**Objectif** : prouver, sur *un* rôle et sans rendu, que « base de code + mémoire AMD à 3 niveaux + validateur » élève GLM-5.3 d'un montant mesurable. **Tâche** : brief + inventaire de clips + grille de temps forts + courbe d'énergie → EDL JSON valide. Pas de GPU, pas de rendu ; coût API de l'ordre de quelques dollars [ESTIMÉ, à mesurer].
1. **Matin (3 h)** : schéma Zod de l'EDL (`harnais/edl.ts`) ; 12 briefs synthétiques (4 genres × 3) avec inventaire de 8-15 clips et grille/énergie générées ; `harnais/eval/metriques.ts` (validité, coupes sur temps forts, corrélation rythme/énergie, bande de durée de plan, lisibilité du texte par cadence, durée) ; `montage_auto` en code (bras de référence).
2. **Midi (1,5 h)** : lanceur `eval/lanceur.ts` (modèle × bras × briefs × 3 reps, registre JSONL, plafond en dollars, réponses brutes conservées) ; bras `A0` = rôle assistant actuel + `montage.md`.
3. **Après-midi (2,5 h)** : bras `A1` : `savoir.ts` (récupération top-1 par filtre structuré) ; **6 exemplaires du professeur** (Claude), tirés de briefs d'**apprentissage** seulement : 4 recettes de genre + 6 segments + 3 appels de fonction exemples (les montages JSON déjà écrits dans `marketing/nexora/refonte-medias/montages/` fournissent la forme réelle) ; boucle de réparation sur erreur de validation avec indice de fonction.
4. **Soir (1 h)** : exécuter A_code / A0 / A1 sur les 6 briefs de validation × 3 reps ; rapport apparié avec IC.
**Critères préenregistrés** : A1 − A0 sur le score composite, borne basse de l'IC à 95 % > 0 ; taux d'EDL valide du premier coup ≥ 90 % (contre la valeur de A0) ; jetons par EDL valide non supérieurs de plus de 25 % (la mémoire coûte ~2-3 k jetons, cachables) ; A1 ≥ A_code sur le composite (sinon le LLM n'apporte rien au-dessus du code). Si A1 ne bat pas A0, on le publie tel quel et on regarde pourquoi avant d'étendre.
**Hypothèse à confirmer, pas un résultat** : l'essentiel du gain attendu vient des validateurs, de la base de code et de l'exemplaire de recette ; l'article AMD rapporte de gros gains sur des élèves de 4-8 G de paramètres, GLM-5.3 étant plus grand, le gain pourrait être plus faible.

## 10. Risques

- **Transfert d'AMD non prouvé** : domaine texte/outils validé seulement ; le montage est évalué ici par des proxys (rythme, loudness, lisibilité) qui ne valent pas le goût humain. Parade : jugement humain sur un échantillon à chaque jalon, ne jamais optimiser sur le juge seul.
- **Sur-apprentissage de 30 briefs** et fuite : partition scellée, retrait de l'exemplaire du brief courant, nouveaux briefs ajoutés chaque mois.
- **Juge VLM peu fiable** (note 05) : poids limité (30 %), jamais bloquant, vérifié par paires.
- **Mémoire figée qui vieillit** (moteur, dialecte H3, tendances) : versions du savoir liées à la version des moteurs ; rejeu nocturne ; règle qui nuit désactivée seule.
- **Gonflement du contexte** : k = 1, ≤ 8 000 jetons de savoir par rôle, cache de prompt de la passerelle.
- **Monoculture de style** d'un seul professeur : plusieurs recettes par genre, mémoire de style par utilisateur pour décaler.
- **Dépense** de l'optimiseur (leçon du 03/10 : 14 USD pour rien de promouvable) : plafonds durs, puissance mesurée avant d'optimiser.
- **Dépendance à la note 13** : si les outils changent, l'EDL est le seul contrat stable ; le banc teste l'EDL, pas les outils.

## 11. Sources

AMD : https://arxiv.org/abs/2608.07169 · https://huggingface.co/papers/2608.07169 · https://github.com/taeilkim2465/agentic_memory_distillation. ACE : https://arxiv.org/abs/2510.04618 · https://github.com/mgechev/ACE-open. Travaux du fondateur : `Mission_GEPA_DSPy_MetaHarness_Protocole_2026-09-30.pdf`, `Mission_Harness_AutoEvolution_2026-09-30.pdf`, `Mission_Harness_AutoEvolution_intermediaire_2026-10-03.pdf` (Bureau). GEPA https://arxiv.org/abs/2507.19457 · Meta-Harness https://arxiv.org/abs/2603.28052 (références citées par ces PDF). Internes : `recherche/05`, `09`, `10`, `app/server/nexora/{competences,juge,agent,llm}.ts`.
