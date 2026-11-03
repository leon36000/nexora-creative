# 20. Mémoire AMD, ReasoningBank et harnais des paliers bon marché : comparaison, audit, essais (03/11/2026)

Commande du fondateur : rendre **Éco** (DeepSeek V4.1 Flash 1017) et **Équilibré** (Muse Spark 1.3 Contributor) meilleurs pour Nexora Creative avec AMD
(agent memory distillation), **vérifier si ReasoningBank (Google) peut aider**, répondre à « as-tu créé un harnais propre à Creative ? », et **tester** :
l'agent le plus économique pour le client, la plus grande marge pour nous, la qualité à la barre. Analyse et professeur : Claude Opus 5.5 (effort élevé).
Code : `app/server/nexora/montage/{memoires,film}.ts`, `memoire/professeur/`, `memoire/fonctions/{liste_montage,tournage}.json`, `bench/memoires.ts` ;
données : `app/server/nexora/bench/resultats/memoire-amd-rb/` (registre, réponses du juge, banques de stratégies, rapport).

## 1. ReasoningBank et ses voisins, lus à la source, pour notre cas

| Méthode (source) | Ce qui est stocké | Signal (succès / échecs) | Qui juge | Récupération, injection | Coût | Élève faible vs fort |
|---|---|---|---|---|---|---|
| **AMD** (arXiv 2608.07169, page du projet) | trajectoires **du professeur** → workflow (prose), sous-tâches (description + code), fonction (exemple d'appel) | réussites du professeur **seulement** | le banc (vérité terrain) | top-1 workflow au début, top-1 par sous-tâche, fonction **sur erreur** | hors ligne, une fois | gros gain sur petits élèves (Qwen3-4B : AppWorld 14,9 → 49,4), décroît avec la taille ; mémoire de l'élève seul : presque rien ; un professeur « accessible » vaut mieux qu'un plus fort |
| **ReasoningBank** (arXiv 2509.25140, ICLR 2026) | items {titre, description, contenu} (≤ 3 par trajectoire) : stratégies et pièges | **réussites ET échecs** (contre-exemples) | **LLM juge, même modèle, sans vérité terrain** (72,7 % d'accord avec la vérité sur Shopping ; un juge à 70-90 % fait presque aussi bien) | plongement cosinus sur la requête, **k = 1** (k = 1 : 49,7 ; k = 4 : 44,4), dans le message système ; consolidation = simple ajout | +4 % de jetons par tâche, −1,4 pas | WebArena : Gemini 2.5 Flash 40,5 → 48,8, Pro 46,7 → 53,9, Claude 3.7 41,7 → 46,3 ; Gemma-3-12B 17,1 → 24,1. Échecs utiles : 46,5 (succès seuls) → 49,7. MaTTS (k = 5) : 55,1 en parallèle |
| **ACE** (arXiv 2510.04618) | *playbook* de puces à identifiant + compteurs utile/nuisible | succès et erreurs ; marche sans vérité terrain avec un retour d'exécution (AppWorld 59,4 avec, 57,2 sans) | réflecteur LLM | tout le playbook dans le contexte, mises à jour **par delta** (fusion en code, jamais de réécriture : une réécriture complète a fait tomber le contexte de 18 282 à 122 jetons) | −86,9 % de latence d'adaptation | un réflecteur faible injecte du bruit qui **nuit** (FiNER 70,7 → 66,7) |
| **AWM** (arXiv 2409.07429) | workflows abstraits (variables `{nom}`) | réussites seulement (jugées par AutoEval en ligne) | LLM évaluateur | injectés dans le contexte | — | GPT-4 : WebArena 35,5 contre 23,5 |
| Reflexion (2303.11366) | réflexions verbales épisodiques | retour scalaire ou textuel | environnement ou soi | mémoire de l'épisode, réessai | un réessai par échec | — |
| Voyager (2305.16291) | bibliothèque de compétences **en code exécutable** | retour d'exécution + auto-vérification | soi | par description | — | — |
| A-MEM (2502.12110), Mem0 (2504.19413) | notes / faits de conversation liés | aucun signal de réussite | — | — | Mem0 : −90 % de jetons vs contexte complet | mémoire personnelle, pas de savoir-faire : **hors sujet pour le montage**, utile plus tard pour la mémoire de style par client |

**Ce qui transfère au montage et à l'écriture de films.** Nos tâches ont ce que le web n'a pas : un **validateur déterministe** et une **note en code**
gratuits. Le signal de réussite n'a donc pas besoin d'un juge LLM (c'est le point faible de ReasoningBank et d'ACE : bruit du juge) ; le goût, lui, n'est vu
que par un juge (texte en ordre inversé ici, visuel quand il y a des images). AMD transfère tel quel (la liste de montage *est* du code court : « prose pour les plans,
code pour l'exécution ») ; ReasoningBank transfère en principe (stratégies de l'élève, y compris ses pièges), MaTTS est notre meilleur-de-n.
**Risques** : pollution de la mémoire (stratégies fausses ou trop spécifiques : une banque de l'élève a produit « tourner des plans de 6 à 8 s », impossible
chez nous), biais du juge (un juge sévère étiquette « échec » une réussite réparée), sur-apprentissage du banc (8 briefs de test, 4 d'apprentissage : tout
est petit), monoculture d'un seul professeur.

## 2. Audit honnête : « as-tu créé un harnais propre à Creative ? »

Oui, depuis le 02/11 (notes 14 et 19), et il est réellement spécialisé : **liste de montage en secondes** compilée par le code (images, aimantation sur les
temps forts, audio, durée exacte), **validateur parlant** (valeur attendue + réparation), 2 réparations, **réparations mécaniques du code**, repli
déterministe `montageAuto`, deux rôles courts (`tournage`, `montage`), adaptateurs par modèle (effort de raisonnement, point de terminaison Flex),
mémoire k = 1, escalade Éco → Équilibré → Expert sous plafond, facturation au jeton. **Ce qui manquait pour les paliers bon marché** (constaté avant ce travail) :
mémoire de fonction **réactive** pour la liste de montage (elle n'existait que pour l'ancien EditPlan), mémoire du professeur bâtie sur une partition
**d'apprentissage séparée** (les graines venaient des films mêmes du banc), mémoire de **sous-tâche** (on injectait un plan entier), décomposition
**plan puis remplissage**, meilleur-de-n dans la route, sortie contrainte par grammaire / schéma JSON (non fait : mode JSON seulement), auto-cohérence,
dialectes de prompt par modèle (mêmes prompts pour les trois), juge (texte ou visuel) dans la boucle.

## 3. Essais

**Protocole.** Partition **scellée** : *apprentissage* = 4 briefs neufs (Traduction en direct, Comptabilité IA, Usine connectée, Recherche documentaire ;
2 pubs, 2 bandes-annonces), seuls à recevoir les trajectoires du professeur (Opus 5.5 a écrit à la main tournage + liste de chaque film, validés, note en code
0,90-0,93 : `memoire/professeur/*.json`) et seuls joués par l'élève pour bâtir sa banque ReasoningBank ; *test* = les 8 briefs de la campagne (note 19),
joués 3 fois par condition, rien n'en est appris. Pas de partition de validation : aucun réglage n'a été choisi sur le test (conditions et n = 4 fixés avant).
Note = composite en code (0 si repli) ; IC95 bootstrap sur les briefs ; Δ apparié par brief contre B (le défaut en production avant ce travail).
**Juge** : Gemini 4 Argon Flex, en **ordre inversé** (X contre B, puis B contre X, même brief, même répétition, répétitions 1-2) sur le texte du film
(plans, temps, textes) : 1 point si les deux ordres préfèrent X, 0 s'ils préfèrent B, 0,5 sinon (n = 16 paires par cellule ; juge visuel impossible :
aucune image sans GPU). Coût en crédits = USD × 1,10 × 1,4025 × 100 (exact, avant l'arrondi au crédit supérieur). Dépense totale : **2,09 USD** (plafond 6), 2 173 appels.
Conditions : **A** sans mémoire · **B** mémoire existante · **C** AMD professeur (workflow top-1 + une sous-tâche top-1 par phase, sources anonymisées
`<SRC_A>` et durées annotées + mémoire de fonction réactive) · **D** ReasoningBank (l'élève se juge, tire ≤ 3 stratégies de ses réussites et de ses échecs,
top-1 dans le message système) · **E** C + D · **F** meilleur-de-4 sur B (juge = note en code, gratuit) · **G** décomposé sur B (structure, puis textes avec le
budget de caractères calculé par le code ; le code choisit les points d'entrée et pose le carton) · **H** C + G.

| Palier | Cond. | note [IC95] | Δ vs B [IC95] | liste valide 1er coup | repli | USD / film | crédits / film | juge vs B (V-D-É) |
|---|---|---|---|---|---|---|---|---|
| Éco | A | 0,677 [0,450 ; 0,838] | −0,155 [−0,271 ; −0,039] | 33 % | 25 % | 0,00079 | 0,122 | 0,56 (5-3-8) |
| Éco | B | 0,832 [0,682 ; 0,914] | — | 29 % | 8 % | 0,00092 | 0,142 | — |
| Éco | C | 0,902 [0,893 ; 0,910] | +0,070 [−0,013 ; 0,222] | 71 % | 0 % | 0,00056 | 0,087 | 0,69 (9-3-4) |
| Éco | D | 0,680 [0,496 ; 0,833] | −0,152 [−0,377 ; 0,039] | 29 % | 25 % | 0,00085 | 0,131 | 0,41 (3-6-7) |
| Éco | E | 0,910 [0,902 ; 0,918] | +0,078 [−0,009 ; 0,232] | 67 % | 0 % | 0,00066 | 0,101 | 0,81 (11-1-4) |
| Éco | F | 0,932 [0,918 ; 0,946] | +0,100 [0,013 ; 0,256] | 46 % | 0 % | 0,00168 | 0,259 | 0,63 (8-4-4) |
| Éco | G | 0,863 [0,787 ; 0,908] | +0,031 [−0,112 ; 0,217] | 50 % | 4 % | 0,00067 | 0,103 | 0,75 (9-1-6) |
| **Éco** | **H** | **0,914 [0,906 ; 0,923]** | +0,082 [−0,007 ; 0,239] | **96 %** | **0 %** | **0,00061** | **0,095** | **0,84 (11-0-5)** |
| Équilibré | A | 0,916 [0,907 ; 0,924] | +0,007 [−0,003 ; 0,016] | 42 % | 0 % | 0,00094 | 0,146 | 0,50 (5-5-6) |
| Équilibré | B | 0,909 [0,901 ; 0,919] | — | 29 % | 0 % | 0,00113 | 0,174 | — |
| Équilibré | C | 0,890 [0,872 ; 0,906] | −0,020 [−0,035 ; −0,002] | 88 % | 0 % | 0,00087 | 0,134 | 0,63 (5-1-10) |
| Équilibré | D | 0,875 [0,802 ; 0,915] | −0,034 [−0,106 ; 0,007] | 42 % | 4 % | 0,00108 | 0,166 | 0,53 (6-5-5) |
| Équilibré | E | 0,892 [0,872 ; 0,912] | −0,018 [−0,038 ; 0,004] | 92 % | 0 % | 0,00096 | 0,149 | 0,56 (4-2-10) |
| Équilibré | F | 0,929 [0,912 ; 0,948] | +0,020 [0,010 ; 0,031] | 46 % | 0 % | 0,00367 | 0,567 | 0,41 (3-6-7) |
| Équilibré | G | 0,921 [0,904 ; 0,940] | +0,012 [0,001 ; 0,025] | 63 % | 0 % | 0,00117 | 0,180 | 0,56 (6-4-6) |
| **Équilibré** | **H** | **0,912 [0,902 ; 0,921]** | +0,003 [−0,009 ; 0,015] | **100 %** | 0 % | **0,00105** | **0,162** | **0,72 (9-2-5)** |
| Expert | A | 0,930 [0,913 ; 0,943] | −0,008 [−0,022 ; 0,006] | 88 % | 0 % | 0,01109 | 1,711 | non jugé |
| **Expert** | **B** | **0,938 [0,920 ; 0,958]** | — | 63 % | 0 % | 0,01204 | 1,858 | — |
| Expert | C | 0,913 [0,903 ; 0,922] | −0,025 [−0,043 ; −0,005] | 96 % | 0 % | 0,01059 | 1,634 | non jugé |

Latences médianes : Éco H 26 s (B 30 s), Équilibré H 28 s (B 36 s), Expert B 26 s. Données : `bench/resultats/memoire-amd-rb/{registre,juge,apprentissage}.jsonl`, `rapport.md`.

**Lecture.**
1. **AMD (C) est le levier pour Éco** : la variance s'effondre (IC de largeur 0,02 au lieu de 0,23), plus aucun repli, 71 % de listes justes du premier coup
   au lieu de 29 %, et −39 % de coût (moins de réparations). La mémoire du professeur **bâtie sur d'autres briefs** fait mieux que l'ancienne, tirée des films mêmes du banc.
2. **Le harnais décomposé (G) se cumule à AMD (H)** : 96-100 % de listes valides du premier coup sur les deux paliers bon marché, la meilleure préférence du
   juge (Éco 11 victoires, 0 défaite ; Équilibré 9-2). Seul, G aide peu Éco (il reste dépendant de la mémoire existante).
3. **Pour les modèles forts, imiter le professeur coûte un peu de note en code** (Équilibré C −0,020, Expert C −0,025, significatifs) : mes trajectoires
   suivent mal la courbe d'énergie que mesure le code (rythme 0,67-0,77, Spearman ≈ 0). Le juge, lui, ne les trouve pas moins bonnes (Équilibré C : 5-1-10).
   Résultat conforme à AMD : le gain culmine chez l'élève faible et disparaît chez le fort.
4. **ReasoningBank (D) n'aide pas, ni Éco ni Équilibré** : note ≈ A, juge 0,41 et 0,53. Causes visibles : juge de l'élève mal étalonné (accord avec le code
   6/8 pour Éco, **1/8** pour Équilibré, qui déclare « échec » toute liste réparée), stratégies génériques ou fausses pour notre outil (« tourner des plans
   de 6 à 8 s », nos prises font 5 ou 10 s), 8 trajectoires seulement. E (C + D) ≈ C sur la note ; le gain de juge d'Éco E (0,81 contre 0,69) n'est pas significatif.
   C'est exactement la mise en garde d'AMD : « la mémoire collectée par l'élève seul aide à peine ».
5. **Meilleur-de-4 (F)** donne la meilleure note en code (Éco 0,932, Équilibré 0,929) mais coûte **×2,8 à ×3,2** et le juge ne le préfère pas pour Équilibré (0,41) :
   il optimise la métrique, pas le film. À garder pour les rendus payants à fort enjeu, pas par défaut.
6. Marge : au prix de liste ×1,10, Éco H coûte 0,095 crédit exact par film ; facturé au crédit entier (1 crédit, 0,01 $ CA), la marge brute réelle d'un film
   Éco est ≈ 91 % ; c'est le palier le plus rentable à qualité égale à celle d'Équilibré (0,914 contre 0,912).

## 4. Décision

| Rôle / palier | Défaut (code : `optionsPalier`, route `POST /api/nexora/agent/film`) | Pourquoi |
|---|---|---|
| `tournage` + `montage`, départ | **Éco, H** (mémoire du professeur + harnais décomposé), escalade Éco → Équilibré → Expert si score < 0,85 | 0,914 pour 0,0006 $ (0,095 crédit), 0 % de repli, juge 11-0 contre l'ancien défaut ; l'escalade ne sert presque plus |
| Équilibré (escalade, ou choix du client) | **H** | même note qu'avant, 100 % valide du premier coup, −7 % de coût, −8 s |
| Expert | **B** (inchangé) | la mémoire du professeur y baisse la note en code ; déjà au plafond |
| ReasoningBank | **éteint** (module `BanqueStrategies` livré et testé, réutilisable) | aucun gain mesuré ; à rejouer seulement avec un juge étalonné (note en code) et ≥ 50 trajectoires |
| Meilleur-de-n | éteint par défaut (`candidats` dans `OptionsRun`) | ×3 de coût pour +0,02 de note en code, pas préféré par le juge |
| `producteur` | inchangé (Expert) | non mesuré ici |
`NEXORA_HARNAIS_FILM=v3` rétablit l'ancien comportement. Modules exposés pour l'écriture de films : `ModuleMemoire`, `composer`, `MemoireProfesseur`,
`BanqueStrategies`, `jugerTrace`, `extraireStrategies` (`montage/memoires.ts`) ; options `module`, `decompose`, `candidats` de `runFilm` / `monterListe`.

## 5. Limites, et ce qu'il faut rejouer quand la mémoire grossit

- **Petits échantillons** : 8 briefs de test (tous 16:9, pub ou bande-annonce, français), 4 d'apprentissage, 3 répétitions ; les IC des Δ d'Éco contre B
  croisent 0 malgré des moyennes très différentes, parce que B a deux briefs catastrophiques (replis). Les résultats ne valent pas pour 9:16, l'explicatif ni la voix off.
- **Métrique circulaire** : la note en code mesure ce que le code impose (grille, doublons, lisibilité) ; le juge texte est un seul modèle (Gemini), sans image,
  et une paire gagne d'office quand B est tombé en repli (Éco B : 2 replis sur 16 paires jugées). L'œil du fondateur reste le vrai juge.
- **Un seul professeur** (moi), 4 films écrits à la main : risque de monoculture de style (mêmes tournures « Vous parlez. », « Eux, si. »), et mes listes suivent
  mal la courbe d'énergie (corriger le professeur : plans plus courts quand l'énergie monte en fin de pub).
- ReasoningBank testé dans sa variante **hors ligne** (banque figée après l'apprentissage), pas en flux sur le test ; plongements remplacés par un recouvrement de mots.
- Aucune sortie contrainte par grammaire / schéma JSON (non testée), ni dialectes de prompt par modèle.
- Un test préexistant échoue sur `developpement` (`reglagesSite.test.ts`, moteur principal), sans lien avec ce travail.
**À rejouer quand la mémoire grossit** : (1) chaque nouvelle trajectoire du professeur (≥ 0,90 en code ET préférée par le juge) sur un brief neuf → rejouer
Éco H/B sur le test, garder si Δ ≥ 0 ; (2) à 12 trajectoires, revoir k (un workflow par genre et format) et ajouter 9:16 et explicatif au test ; (3) ReasoningBank
avec le juge remplacé par la note en code + validateur (signal fiable gratuit) et ≥ 50 trajectoires d'élève, plus la variante en flux ; (4) films acceptés par
des clients (avec consentement) comme trajectoires de professeur ; (5) juge visuel en ordre inversé dès que des plaques rendues existent.
