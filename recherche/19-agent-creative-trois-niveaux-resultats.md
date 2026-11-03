# 19. L'agent de Creative en trois niveaux : harnais, facturation au jeton, campagne de tests (03/11/2026)

Commande du fondateur : faire de l'agent intégré un **monteur spécialiste et économique**, sur trois paliers (**Éco**
DeepSeek V4.1 Flash 1017 chez DeepInfra, **Équilibré** Muse Spark 1.3 Contributor et **Expert** Gemini 4 Argon Flex chez
OpenRouter), **facturer chaque jeton** au client, et **prouver par des essais** où les modèles font les vidéos eux-mêmes
(le chef de projet écrit les briefs). Les trois modèles sont puissants : les paliers servent au coût et à l'escalade.
Code : `app/server/nexora/{niveaux,usage,paliers}.ts`, `montage/{liste,film}.ts`, `bench/{campagne,films,rapport}.ts` ;
données : `app/server/nexora/bench/resultats/trois-paliers/`. Dépense totale de la campagne : **≈ 1,3 USD** (plafond 10).

## 1. Modèles, prix, manies (vérifiés le 03/11/2026)

| Palier | Modèle (fournisseur) | Prix de liste (USD / M jetons, entrée / sortie) | Manies gérées par l'adaptateur |
|---|---|---|---|
| Éco | `deepseek-ai/DeepSeek-V4.1-Flash-1017` (DeepInfra) | 0,20 / 0,60 (API `models/list` : 2e-5 et 6e-5 ¢ par jeton) | raisonne par défaut : `reasoning_effort: "none"` ; coût rapporté : `usage.estimated_cost` |
| Équilibré | `meta/muse-spark-1.3-contributor` (OpenRouter) | 0,10 / 0,20 | **raisonnement obligatoire** (`enabled:false` et `none` refusés en 400) : `reasoning.effort: "minimal"` (≈ 2 000 jetons de raisonnement par film, latence 42 s) |
| Expert | `google/gemini-4-argon` (OpenRouter) | **Flex : 1 / 5** (point de terminaison `google-ai-studio/flex`) ; standard 2 / 10 ; `:batch` 1 / 5 non interactif | `provider: {order:["google-ai-studio/flex"], allow_fallbacks:false}`, `reasoning.effort: "low"` (0 jeton de raisonnement) ; repli explicite sur `google-vertex/global` au double du prix, **désactivé par défaut**, étiqueté dans la mesure |

Les trois acceptent le mode JSON et l'appel de fonctions (vérifié : l'outil `etat_studio` du Producteur est appelé par les trois).
Reprises : 429, 408 et 5xx avec attente exponentielle (1,5 s, 3 s, 6 s…), trois tentatives ; aucune erreur de capacité Flex n'est
remontée pendant la campagne.

## 2. Facturation de chaque jeton

- **Mesure** : chaque appel renvoie jetons lus, écrits, de raisonnement et, quand le fournisseur le donne, son coût réel (OpenRouter
  `usage.cost`, DeepInfra `estimated_cost`) ; sinon coût au prix de liste. Une ligne du grand livre (`usage-llm.jsonl`) par appel : horodatage,
  utilisateur, organisation, projet, run, tâche, rôle, palier, modèle, point de terminaison, repli, jetons, USD, crédits, latence.
- **Prix client** = coût fournisseur × **1,10** (marge) × **1,4025** (USD→CAD) × 100 crédits (1 crédit = 1 ¢ CA), constantes de la passerelle du site
  (`NexoraSite/docs/catalogue-deepinfra.md`), configurables (`NEXORA_LLM_MARGE`, `NEXORA_USD_CAD`). 1 USD = 154,275 crédits.
- **Cycle** : devis (jetons typiques de la tâche, ou moyenne de l'historique du palier à partir de 3 runs) → **réservation** du plafond dur (devis × 2) →
  appels mesurés, le suivant est refusé au-delà du plafond → **règlement** du réel (arrondi au crédit supérieur, minimum 1 crédit dès qu'un jeton est consommé) →
  **libération** du reste. Un échec en cours de route règle quand même les jetons consommés. Sans crédits (poste local, développement) : rien n'est débité,
  tout est enregistré. 19 tests (`usage.test.ts`).
- **Interface** : sélecteur Éco / Équilibré / Expert dans le Producteur (par projet) et ligne « jetons lus, écrits, crédits » sous la carte du devis.
- **Prix d'un film en crédits d'IA** (plan de tournage + montage, moyenne a3) : Éco 0,11 ; Équilibré 0,17 ; Expert 1,93. Avec l'arrondi au crédit, chaque run est facturé au moins 1 crédit.

## 3. Le harnais fait pour ces agents (et rien d'autre)

1. **Format compact** : le modèle écrit une *liste de montage* en secondes (une ligne par plan : source, départ, durée, transition, texte) au lieu d'un EditPlan en images ;
   le code compile (images entières, durée totale exacte, coupes aimantées sur les temps forts, textes calés sur le temps de lecture, audio −8 dB / −14 LUFS, fondu final).
   Deux fois moins de jetons, et l'arithmétique d'images, point faible des petits modèles, disparaît.
2. **Validateur parlant** : chaque violation donne la valeur attendue et la réparation (« le plan lit de 4,2 à 7,2 s, la source dure 5,1 s : in ≤ 2,1 »), 2 réparations, puis des
   **réparations mécaniques par le code** (bornes de lecture, texte qui ne tient pas, même source de suite), puis le repli `montageAuto`.
3. **Deux appels, deux rôles** : `tournage` (8 à 12 plans, prompts anglais sans texte ni marque ni franchise, validés) puis `montage`. Compétences `tournage-film` et `montage-film`
   (règles de métier écrites avec mes mots : accroche avant 3 s, apogée entre 12 et 15 s, respiration avant l'apogée, texte ≤ 6 mots et 15 caractères par seconde, sources variées, carton neutre portant la marque).
4. **Mémoire à la AMD, k = 1** : une recette par genre, un exemplaire de montage et un exemplaire de tournage. **Professeur = Claude** : 4 films de la campagne (V4/V5 : Surveillance,
   WorkStudio, OPSYS-AI, Modèles et API) convertis en segments EditPlan typés (`bench/graines.ts`) + 2 exemplaires de tournage écrits à la main. Anti-fuite : jamais la graine du film dont le brief est tiré.
   La mémoire **apprend** entre les tours : les plans valides à ≥ 0,85 de tous les paliers deviennent des exemplaires (le palier cher enseigne au palier économique).
5. **Escalade** : Éco → Équilibré → Expert si le plan n'est pas du modèle, si le tournage est invalide ou si le score est sous 0,85, dans le plafond de dépense (route `POST /api/nexora/agent/film`).

## 4. Campagne A (sans GPU) : 3 paliers × 8 briefs × mémoire éteinte / allumée × 3 tours

Briefs du chef de projet (WorkStudio, Nexora, Creative, Réception virtuelle, Surveillance IA, Infrastructure IA, Modèles et API, OPSYS-AI ; 30 à 45 s, 16:9, français du Québec ; marque lue dans `marque.json`).
Note = composite en code (rythme, coupes sur la grille, doublons, texte, audio ; 0 si le modèle n'a pas livré de plan valide). IC95 par bootstrap sur les briefs (n = 8). Détail : `rapport-a2.md`.
J'ai fait 3 tours au lieu de 2 pour la courbe d'évolution ; le juge visuel n'a pas servi (aucune vignette sans GPU) : les notes sont celles du code.

### Par palier (harnais v2, 48 essais par palier, tous tours)

| Palier | note [IC95] | tournage valide 1er coup | montage valide 1er coup | repli | USD / film | crédits / film | latence médiane |
|---|---|---|---|---|---|---|---|
| Éco | 0,627 [0,522 ; 0,747] | 71 % | 17 % | 31 % | 0,0008 | 0,12 | 28 s |
| Équilibré | 0,896 [0,854 ; 0,923] | 73 % | 44 % | 2 % | 0,0011 | 0,16 | 42 s |
| Expert | **0,936** [0,921 ; 0,952] | 85 % | 67 % | 0 % | 0,0120 | 1,86 | 29 s |

### Ce que la mémoire apporte (allumée − éteinte, apparié par brief)

| Palier | éteinte | allumée | Δ [IC95] |
|---|---|---|---|
| Éco | 0,453 | 0,801 | **+0,348** [0,230 ; 0,472] |
| Équilibré | 0,874 | 0,918 | +0,045 [0,004 ; 0,116] |
| Expert | 0,931 | 0,941 | +0,009 [−0,004 ; 0,024] |

### Évolution, tour par tour (la mémoire grossit : 8 graines → 30 segments après le tour 1, 32 après le tour 2)

| Palier / mémoire | tour 1 | tour 2 | tour 3 |
|---|---|---|---|
| Éco, éteinte | 0,338 | 0,450 | 0,571 |
| Éco, allumée | 0,689 | **0,913** | 0,802 |
| Équilibré, éteinte | 0,913 | 0,909 | 0,799 |
| Équilibré, allumée | 0,914 | 0,927 | 0,915 |
| Expert, éteinte | 0,925 | 0,935 | 0,934 |
| Expert, allumée | 0,942 | 0,938 | 0,942 |

Lecture : Expert est déjà au plafond (rien à apprendre) ; la mémoire fait presque tout pour Éco : tour 1 avec les seules graines du professeur 0,69, tour 2 avec les plans appris 0,91
(la baisse du tour 3, 0,80, est de la variance de Flash sur quelques briefs, pas une dérive prouvée). Éco éteinte progresse aussi sans mémoire (0,34 → 0,57), ce qui montre le bruit d'échantillonnage : à lire avec les IC.

### Évolution du harnais (tour 1, même matière, mêmes briefs)

| Harnais | Éco éteinte | Éco allumée | Éco repli | Équilibré (éteinte / allumée) | Expert (éteinte / allumée) |
|---|---|---|---|---|---|
| v0 : EditPlan brut, un appel, sans mémoire (a1 : 88 % de replis ; a2 : 100 %) | **0,092** (a1) / **0,000** (a2) | | 88 à 100 % | | |
| v1 : liste compacte + validateur + 2 réparations | 0,222 | 0,567 | 56 % | 0,917 / 0,791 | 0,922 / 0,938 |
| v2 : tolérance ±25 % sur la durée, lisibilité à 16,5 caractères/s | 0,338 | 0,689 | 43 % | 0,913 / 0,914 | 0,925 / 0,942 |
| v3 : réparations mécaniques du code avant le repli | **0,674** | **0,920** | **12 %** | 0,927 / 0,919 | 0,937 / 0,942 |

Éco sans harnais ne produit aucun plan valide (v0 : 0/8) ; avec le harnais v3 et la mémoire, il atteint 0,92 pour 0,0007 USD, à 0,02 de l'Expert (qui coûte 18 fois plus).
Causes des replis d'Éco (v2) : texte trop long pour le temps disponible (9), lecture au-delà de la source (6), même source de suite (1), plans de tournage non distincts (1) : ce sont les deux premières que v3 répare en code.
Coût par film **valide** : Éco 0,0008 USD, Équilibré 0,0011, Expert 0,0125.

### Par brief (note moyenne, v2)

| Brief | Éco | Équilibré | Expert |
|---|---|---|---|
| WorkStudio | 0,77 | 0,93 | 0,96 |
| Nexora | 0,93 | 0,93 | 0,97 |
| Creative | 0,75 | 0,89 | 0,91 |
| Réception virtuelle | 0,44 | 0,76 | 0,92 |
| Surveillance IA | 0,46 | 0,91 | 0,92 |
| Infrastructure IA | 0,46 | 0,91 | 0,94 |
| Modèles et API | 0,59 | 0,90 | 0,92 |
| OPSYS-AI | 0,62 | 0,93 | 0,96 |

## 5. Campagne B : trois films par palier, rendus pour de vrai

Réception virtuelle, Surveillance IA et OPSYS-AI, 36 à 40 s, 16:9, français, 1280×720, rendu ffmpeg du produit (`rendreEditPlan`) : textes en code (ASS), carton neutre sombre portant `NEXORA`
(marque.json), musique des films de la campagne (recep-v1, surv-v2, opsys-musique-71), −14 LUFS. Pour chaque palier : **3 candidats, le meilleur score en code gagne** (mémoire = graines + plans appris en A).
Les plans viennent de la **bibliothèque** de plaques H3 déjà tournées (9 à 12 plaques par film) : aucune génération GPU. Fichiers : `~/nexora-creative-data/promo/montage/Test-agents-<palier>-<brief>-16x9-fr.mp4`.

| Brief | Éco | Équilibré | Expert |
|---|---|---|---|
| Réception virtuelle | 0,917 (0,0005 $) | 0,910 (0,0008 $) | 0,921 (0,0086 $) |
| Surveillance IA | 0,924 (0,0004 $) | 0,920 (0,0014 $) | 0,946 (0,0084 $) |
| OPSYS-AI | 0,862 (0,0005 $) | 0,952 (0,0009 $) | 0,954 (0,0117 $) |

Constat visuel (planches de contrôle) : les trois paliers livrent un film cohérent, sans coupe ni texte cassé. Tous emploient toutes les plaques de la bibliothèque (9 à 12), mais pas au même rythme : en OPSYS-AI Éco monte 38 plans (≈ 1 s chacun, beaucoup de reprises de plaques, doublons 0,63),
Équilibré 24 et Expert 32 ; en Réception et Surveillance les trois font 13 à 17 plans. La bibliothèque est petite : les mêmes images reviennent dans tous les films.

## 6. Recommandation de défaut par rôle

| Rôle | Palier de départ | Pourquoi |
|---|---|---|
| `tournage`, `montage`, `monteur` | **Éco, mémoire allumée, escalade automatique** (Équilibré puis Expert) | 0,92 pour 0,0007 $ le film ; l'escalade ne se déclenche que sur échec (12 % des films) |
| `producteur` (conversation, outils) | **Expert** (Argon Flex) | ≈ 0,01 $ le tour (1,5 crédit), le tour reste le moment où la qualité se voit ; Équilibré est un bon repli à 0,0006 $ mais raisonne toujours (≈ 2 000 jetons, 40 s) |
| `juge`, `moderation`, `redaction` | inchangés (non mesurés ici) | |

Le palier se change par projet (sélecteur), par rôle (réglage du site `palier:eco`, ou `NEXORA_PALIER_<ROLE>`) ou globalement (`NEXORA_PALIER`).

## 7. Ce qui a échoué, limites honnêtes

- Le harnais v1 laissait Éco échouer 56 % du temps ; trois itérations ont été nécessaires (v1 → v3), les deux premières décidées **pendant** la campagne (les lignes de chaque version sont conservées : `essais-a1/a2/a3.json`). v3 n'a été mesuré qu'au tour 1 (a3), pas sur trois tours.
- Éco **n'écrit pas lui-même un plan valide** du premier coup (17 % en moyenne) : il dépend des réparations, de la mémoire et du code. Sans eux : zéro.
- La note est celle du **code** (rythme, grille, doublons, texte, audio) : les coupes sur la grille valent toujours 1,00 (c'est le code qui aimante), donc elle ne voit ni la qualité des textes, ni la tenue de l'histoire, ni le goût. Ni juge visuel, ni juge LLM en ordre inversé sur ces films ; je n'ai regardé que des planches. Le fondateur est le vrai juge des 9 films.
- Stade B : les plans viennent d'une **bibliothèque** (pas des prompts de tournage du palier) ; la comparaison porte sur le choix, l'ordre, le rythme et le texte, pas sur la génération d'images. Aucune plaque nouvelle n'a été tournée.
- Les graines du professeur viennent de 4 des 8 films (écartées pour leur propre brief) ; les briefs Surveillance, WorkStudio, OPSYS-AI et Modèles ont donc un voisin thématique plus faible que s'ils étaient inédits, les 4 autres n'en ont pas du tout : la mémoire fait ses preuves sur les uns et les autres, mais l'échantillon est petit (n = 8 briefs).
- Typographie du rendu ffmpeg : DejaVu Sans en ASS (lisible, neutre, mais pas la typographie cinétique de l'usine Python des films de campagne).
- Les IC sont larges (8 briefs) ; les différences Équilibré/Expert hors OPSYS-AI et Réception ne sont pas significatives.
- Facturation : tout est mesuré et testé, mais **rien n'a été débité** en conditions réelles (la VM tourne sans portail de crédits : `facture: 0`). Le règlement contre l'API de crédits du site est couvert par des tests avec un faux grand livre.
