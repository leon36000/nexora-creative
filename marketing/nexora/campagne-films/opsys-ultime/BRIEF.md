# Film ultime OPSYS-AI : brief commun des quatre équipes (03/11/2026)

Ce dossier est **le seul brief**. Les quatre équipes le reçoivent tel quel, au mot près : DeepSeek V4.1 Flash 1017 (effort
max), Muse Spark 1.3 Contributor (effort max), Gemini 4 Argon (effort élevé) et Opus 5.5 (effort très élevé). Chaque équipe
joue une agence complète (direction de création, rédaction, réalisation, distribution, direction musicale, montage,
production) et rend un dossier créatif. Les quatre films sont ensuite tournés et montés **par la même chaîne**, avec le même
budget. Le fondateur choisit.

Producteur exécutif : Opus 5.5 (il écrit aussi l'une des quatre versions, à l'aveugle, avant de lire les autres). Le
producteur ne réécrit pas la création des autres : il corrige seulement le technique (format, prompt refusé par un moteur,
durée hors grille) et consigne chaque correction dans `equipes/<equipe>/CORRECTIONS.md`.

---------------------------------------------------------------------------------------------------------------------------

## 1. Le brief du fondateur (presque mot pour mot)

> « Tu ne peux pas montrer le dashboard d'OPSYS alors qu'il n'est pas terminé, mais tu dois montrer une IA qui travaille pour
> nous ; un OPSYS-AI qui peut remplacer des organes complets d'une entreprise. Une figure d'une grosse entreprise qui travaille
> pour représenter OPSYS-AI, comme si chaque département était un département d'une grande entreprise, car c'est ça OPSYS-AI. »

Ses exemples de scènes (ce sont des exemples : on peut en ajouter, en retirer, les réordonner) :
1. **La soumission par photo.** Un représentant prend une photo d'un revêtement ; le signal voyage dans le ciel jusqu'à un
   satellite ou une tour 5G, longe les lignes réseau des poteaux électriques jusqu'à un serveur ; à l'intérieur du serveur, la
   grande entreprise virtuelle travaille, fait la soumission et la renvoie au représentant. En 10 secondes, ou dans un film de
   quelques minutes.
2. **Monsieur Morin.** Cette même soumission, adressée à « Monsieur Morin », traverse encore un signal jusqu'à un employé
   devant une shop de travail qui rassemble les informations sur son chantier.
3. **La comptabilité qui parle.** Un administrateur d'entreprise parle à l'avatar virtuel de sa comptabilité.
4. **Le pointage et la paye.** Un employé pointe l'heure d'arrivée, puis on enchaîne sur la remise d'un chèque de paye.
5. **L'adjointe.** Une adjointe administrative (voix féminine de qualité) appelle un représentant : « Vous avez un rendez-vous
   avec monsieur Thibault à 14 h, et j'ai déplacé votre rendez-vous de 16 h comme vous me l'avez demandé. »
6. **La projection.** Une projection comptable avec un pourcentage de rentabilité ; l'avatar comptable dit : « Voici les
   profits anticipés, mis à jour avec les nouveaux ratios de productivité des employés : leur productivité a augmenté de 7 %. »
7. **La cédule.** L'avatar de gestion qui s'occupe des cédules dit à un administrateur : « Voici la cédule des trois
   prochaines semaines. »

> « Nous devons montrer les capacités et les fonctionnalités d'OPSYS-AI. N'hésite pas à mettre du spectaculaire et des effets
> spéciaux, ça doit être impressionnant, nous devons sentir la puissance technologique d'OPSYS-AI. La musique doit être
> entraînante et non déprimante. »

Ce qu'il a rejeté (à ne pas refaire) : les derniers films, jugés « pires » ; la voix ElevenLabs « Alexandre », **« beaucoup trop
smooth »** (il veut une voix énergique, avec du caractère) ; la bataille spatiale à 3/10 l'était par son exécution « cheap,
jeu vidéo, statique, sans rythme », pas par l'ambition. Son meilleur souvenir : « le premier vidéo avec la goutte d'or ». Sa
porte : **8/10 minimum** ; il vise 9. Il sait que nos auto-notes ont été trop généreuses de 1 à 3 points.

## 2. OPSYS-AI : les faits (source : `films/opsys/FAITS.md`, à lire en entier)

**Ce que c'est.** Un système d'entreprise IA pour PME, installé chez le client (VPS, poste ou serveur) : **dix départements
virtuels** (M1 à M10) pilotés par des agents, une console web et une application mobile à quatre profils (admin, vendeur,
employé, client). Contexte de départ réel : PME de rénovation extérieure au Québec (gouttières, revêtement, soffite-fascia).
Règle d'or écrite dans le produit : **« le code calcule (prix, soldes, scores, cédules), le LLM orchestre et rédige. Aucune
donnée inventée. »** Les actions financières, fiscales, légales et sensibles exigent une **approbation humaine** (niveaux
N0 à N5). Ampleur mesurée par les auteurs : ≈ 105 000 lignes de code dans les départements, 188 000 lignes de tests, 710 outils
exposés aux agents. État : **produit en consolidation, aucun déploiement de production complet.**

Ambition écrite du fondateur : « Donner à une PME les ressources d'une grande entreprise : dix départements complets,
plusieurs agents spécialisés, une vérité partagée, des opérations interconnectées et une autonomie gouvernée. » Il veut aussi
« pouvoir communiquer avec les départements par avatar 3D audiovisuel ».

| M | Département | RÉEL aujourd'hui (code + tests) | EN PRÉPARATION | VISION |
|---|---|---|---|---|
| M1 | Réception | qualification des demandes, transferts, plaintes, appels manqués, résumé | messagerie vocale transcrite, SMS, envoi réel | réceptionniste vocale en direct |
| M2 | CRM | ingestion des leads, prochaine action, prêt pour l'estimation | client 360, relances | — |
| M3 | Estimation | estimation déterministe qui refuse de chiffrer sans information, Monte Carlo, **soumission PDF brouillon** filtrée des coûts internes, revue en 11 critères + approbation avant envoi | calibration estimé/réel | **mesure à partir de photos**, géospatial |
| M4 | Terrain | intervention née du devis accepté, fin de chantier | **cédule par tournées, pointage**, preuves photo, météo | GPS en direct, répartition |
| M5 | Finance | **facture brouillon** après travaux, comptes à recevoir et à payer, calculs exacts | **prévision 26 semaines**, cash libre, TPS/TVQ, dossier CFO | comptabilité complète, **paie**, banques |
| M6 | Matériel | besoins depuis le devis, réservations, écarts de quantités | bons de commande (approbation), réceptions | catalogue, API fournisseurs |
| M7 | Marketing | chantier terminé → contenus proposés, consentement vérifié | demande d'avis, attribution | publication sur réseaux |
| M8 | Analytique | collecte, vue exécutive | « non calculable » si donnée manquante, alertes | — |
| M9 | Stratégie | **briefing du matin**, lecture stratégique | suivi des décisions | conseil d'agents, scénarios |
| M10 | Mémoire | registres chaînés, contexte, recherche d'affaire | mémoire hybride | rappel sémantique |

Chaîne réelle la plus forte : devis accepté (M3) → intervention (M4) → besoins matériel (M6) → fin de chantier → facture
brouillon (M5) → contenus proposés (M7) → vue exécutive (M8) → briefing du matin (M9) → mémoire (M10). Tout en brouillons,
avec validation humaine ; l'envoi réel au client n'existe pas encore.

**Ce que ça veut dire pour les scènes du fondateur** (statut honnête de chacune) :
| Scène | Statut |
|---|---|
| Soumission chiffrée et revue (M3) | RÉEL (brouillon + approbation) |
| Soumission **à partir d'une photo**, en 10 s | VISION (la mesure par photo n'existe pas) |
| Le signal (satellite, 5G, poteaux, serveur) | métaphore visuelle (OPSYS tourne sur un serveur du client : vrai) |
| Le dossier de chantier envoyé à l'employé (M4) | RÉEL côté serveur (intervention née du devis) ; l'envoi au mobile est EN PRÉPARATION |
| Avatar parlant (comptable, gestion) | VISION (aucun code d'avatar) |
| Adjointe qui appelle et déplace un rendez-vous | VISION (réceptionniste vocale) ; la gestion d'agenda n'est pas documentée |
| Projection de profits | EN PRÉPARATION (prévision 26 semaines) ; **le « 7 % » est une donnée de scène, fictive** |
| Cédule des 3 semaines | EN PRÉPARATION (cédule par tournées) |
| Pointage | EN PRÉPARATION ; **paye : VISION** |
| Approbation humaine avant tout envoi | RÉEL (mécanisme N0–N5) : c'est un atout à montrer |

Règles d'honnêteté (légères, sans juridique) : le film est un **film de vision** ; il le dit **une fois** à la fin (carton
de mentions, par ex. « Film de vision. Certaines fonctions sont en préparation. Données fictives. ») et marque d'une petite
étiquette « VISION » ou « EN PRÉPARATION » (style `prepa` de la chaîne) les plans qui montrent une fonction non livrée **quand
le plan la présente comme un fait** (une étiquette discrète par scène suffit, pas sur chaque plan). Aucun chiffre de temps
gagné, aucune statistique de performance d'OPSYS, aucun client réel. Les chiffres **dans** une scène (le 7 %, une soumission de
18 940 $, 14 h, 16 h) sont des données fictives de l'histoire : permis. Interdit à l'écran : le tableau de bord ou la console
d'OPSYS, toute marque tierce (« nvidia », logos de téléphones, d'opérateurs, de fabricants), « avatar NVIDIA ACE ».

## 3. Grammaire des promos de référence (à lire avant d'écrire)

Le fondateur a cité deux courts. Notes du producteur (visionnés en basse définition, fichiers supprimés) :
- **« Higgsfield x Claude Opus 5.5 for Motion Design » (73 s, 9:16)** : une histoire avec **un seul héros** (un randonneur en
  manteau bleu dans une jungle), tournée comme un vrai film ; pendant qu'il avance, **les sorties de l'IA se matérialisent dans
  le monde réel** (une mascotte animée apparaît près de lui, une flamme, du code d'expression flotte dans l'air), entrecoupées de
  **messages d'état très courts** de l'IA (« Promo brief received. Starting with the reserve logo. », « Creating photos, pins,
  and badges… », « Mapped. Five stops. One route. »). La démonstration avance par étapes lisibles ; le résultat final (une carte,
  une affiche) arrive en apothéose. Coupes ≈ toutes les 1,5 à 4 s ; la caméra bouge toujours.
- **« Kling 4.0 makes AI video look like a real film shoot » (36 s, 9:16)** : bande-annonce typographique frénétique : un
  crochet visuel à la première seconde (masque, logo qui glitche), **un mot géant par fonction** (« OMNI REFERENCE », « 30 SEC
  DURATION », « START · MIDDLE · END », « 4K »), chaque fonction **prouvée par un plan encadré** dans une mise en page graphique
  (chevrons, cadres, couleurs vives), coupes sous la seconde, transitions glitch, fin « Now live on… ».
- Ce qu'on en retient pour OPSYS : (1) un crochet en moins de 2 s ; (2) un héros humain qu'on suit, et l'IA qui agit **autour de
  lui** (hologrammes, documents qui s'assemblent, voix) ; (3) chaque fonction = un nom court + une preuve visuelle de 2 à 4 s ;
  (4) des messages d'état de l'IA comme fil narratif (« Photo reçue. Mesures en cours… ») ; (5) la musique pilote les coupes ;
  (6) une apothéose, puis le carton.
- La note de recherche `recherche/23-grammaire-promos-ia.md` (autre agent) sera ajoutée ici dès sa parution ; à défaut, ces
  notes font foi.

## 4. Les outils, et leurs limites MESURÉES

Toutes les équipes ont exactement les mêmes. Mesures du 02 au 03/11/2026 sur nos machines.

### 4.1 Vidéo : MiniMax H3 (RTX 5090 de pc1), deux recettes
| | `h3-max` (plans héros) | `h3-fast` (volume) |
|---|---|---|
| Point de contrôle | 10Eros-Max × Singularity V2, ref2va, 8 étapes | FastH3 nvfp4, fl2va, 8 étapes |
| Entrées | texte + **jusqu'à 9 images de référence** (fiches de personnages, lieux, objets) + **ancrages** : image exacte à un indice d'image (première image, ou dernière image d'un plan précédent pour enchaîner) et **piste audio ancrée** (voix choisie → lèvres synchronisées) | texte + **première image exacte** (image clé) ; pas de références |
| Temps moteur | 112 s pour 5,2 s en 1344×768 ; 120 à 129 s avec références ou audio ancré | 104 s |
| Forces | mouvement, échelle, fumée, débris, lumière ; même visage d'un plan à l'autre avec la fiche | fidélité à l'image de départ |
| Faiblesses | met spontanément du **texte et des logos** (un logo rouge est apparu sur une veste au test) : toujours écrire « plain clothing with no logo, no text, no letters anywhere » ; imite des franchises connues sans qu'on les nomme ; mains et visages lointains fragiles ; plus de 2 personnages qui parlent = risqué | aspect « jeu vidéo » sur les vaisseaux et la foule ; moins de mouvement |

Durées possibles (24 i/s, grille 17k + 5) : 124 images = 5,2 s ; 141 = 5,9 s ; 158 = 6,6 s ; 175 = 7,3 s ; 192 = 8,0 s ;
209 = 8,7 s ; 226 = 9,4 s ; 243 = 10,1 s. Au-delà : non testé. Résolution : 1344×768 (16:9) ou 768×1344 (9:16 natif) ;
remise à l'échelle en 1920×1080 au montage (Lanczos + accentuation légère ; aucun super-résolveur ne tourne aujourd'hui).
Le son natif de H3 (ambiance, bruitages) sort avec chaque plan et peut être gardé sous la musique.

**Parole synchronisée (mesurée)** : on ancre la prise de voix choisie (piste audio) dans le plan ; H3 génère le visage qui la
dit. Test du 03/11 (patron de PME en gros plan, avatar holographique) : la piste ressort mot pour mot (Whisper), lèvres et
mâchoire bougent avec les syllabes, avance de la bouche de 1 à 2 images sur le son (naturel) ; 120 à 124 s pour 5,2 s. Une
réplique ≤ 10 s par plan. Une seule personne qui parle par plan. La voix est choisie AVANT le tournage (section 4.3) : un plan
parlant se tourne sur une prise de voix figée.

**Références dans un prompt** : nommez chaque référence de `refs` par **`@id`** (« @etienne raises his phone towards @maison ») ;
la chaîne remplace `@id` par les balises `<Picture n>` dans l'ordre et écrit elle-même les lignes `subject_definitions` (une fiche
de personnage = 2 images : corps entier et visage). Un plan `parole` reçoit automatiquement `<Audio 1>` (la prise de voix retenue)
et sa durée est allongée sur la grille si la réplique l'exige.

**Grammaire de prompt H3** (respecter les sections, en anglais ; `subject_definitions` est écrit par la chaîne) :
```
summary:
A single continuous cinematic shot ... (une phrase)

detailed_description:
Cinematic frame from a 2026 feature film, shot on a large-format digital cinema camera ... (style, lumière, décor, sujets)
[Shot 1] Ce qui se passe, l'action, le mouvement de caméra. No text, no logos.

dialogue:                                                              (plan parlant seulement)
@etienne speaks in Québécois French, matching <Audio 1> word for word.

overall_soundscape:
Ambiance et bruitages voulus (H3 les génère).

non_diegetic_music:
N/A
```

### 4.2 Images : Qwen-Image-2.1 (GB10 de pc6)
≈ 50 s par image en 1664×928 (16:9) ou 928×1664 (9:16). Sert à deux choses : (a) **fiches de personnages et de lieux**
(fond gris uni, corps entier à gauche, gros plan du visage à droite, 1792×1024 ; découpées en deux références) qui donnent le
même visage, la même tenue d'un plan à l'autre ; (b) **images clés** (première image exacte d'un plan `h3-fast`, ou ancrage
d'un plan `h3-max`). Faiblesses : texte illisible ou inventé (n'en jamais demander), images souvent trop sombres.

### 4.3 Voix : palette commune (`casting/PALETTE.md` et `casting/palette.json`, préparées une seule fois pour tous)
Moteurs comparés sur les mêmes répliques (ElevenLabs v4 par OpenRouter, Fish Audio Drama 3 avec direction de jeu et vitesse,
Qwen3-TTS 1.7B en local, voix native de H3), mesurés (débit, relief de la hauteur, dynamique, EMR Whisper) et passés à une
« oreille de machine » (Gemini 4 Argon, audio : accent québécois, énergie, naturel, clarté, sur 10). **Chaque équipe choisit,
par rôle, une voix de la palette**, écrit le texte et la direction de jeu (consigne en langage naturel, balises [energetic]…,
vitesse 0,8 à 1,3). Jusqu'à 3 prises par réplique. Les pauses se posent au montage (générer phrase par phrase si besoin).
Résultat du banc (détail dans PALETTE.md) : les voix les plus québécoises et les plus vivantes à l'oreille de machine sont Frédéric
(homme) et Jeanne Mance (femme), en ElevenLabs comme en Drama 3 ; Alexandre (la voix rejetée) et Thomas sont jugés peu québécois.
La voix native de H3 a un bel accent mais **déforme le texte** (« 16 h » devenu « 6 h ») : on ne s'en sert pas pour une réplique.

### 4.4 Musique : Lyria 3 Pro (OpenRouter)
Mesuré : une demande de 150 s a rendu **153,7 s** (128,3 BPM mesurés pour 124 demandés), avec sauts d'énergie à 15, 37,5 et
79 s ; 90 s de calcul, 0,08 USD. Lyria suit à peu près une structure écrite en secondes ; le BPM demandé n'est jamais exact :
**la chaîne mesure la grille** (tempo, phase, sauts d'énergie) et le montage s'y cale. Instrumental seulement. Alternative :
Lyria 3 Clip (30 s). MiniMax-Music3 local : plus faible (déconseillé).

### 4.5 Montage : la chaîne commune
- Contrat : **EditPlan v1** (`app/server/nexora/montage/editplan.ts`, validé par `validerEditPlan`) : durées en images
  entières à 24 i/s, plans vidéo (`src` = identifiant du plan tourné, `entree_f`, `duree_f`, `vitesse` 0,25 à 4 ou `rampe`,
  `transition_in` cut / fondu / dip / glisse, `zoom` 1 → 1,6), musique, voix (`src` = identifiant de réplique, `debut_f`),
  ducking (≥ 6 dB obligatoire sous une voix), `textes` (titre, sous-titre, carton, bas).
- **Annexe** (propre à ce film, lue par le moteur de rendu) : incrustations graphiques en code (liste en 4.6), bruitages
  synthétiques, son natif des plans, étalonnage, flashs, étiquettes VISION / EN PRÉPARATION.
- Rendu : 1920×1080 à 24 i/s (et 1080×1920), étalonnage « pellicule » et grain des promos V3/V4, typographie cinétique
  (`usine/typo.py` : Geist SemiBold, JetBrains Mono pour les surtitres, un seul mot orange par ligne avec `*mot*`), mixage
  −14 LUFS intégrés, crête vraie ≤ −1,5 dBTP.
- Charte « Signal » : encre, lumière bleu ion, **un seul** point chaud orange (#FF5A1F). Libre à chaque équipe d'en sortir si
  le film y gagne, mais le carton final reste dans la charte.

### 4.6 Incrustations disponibles (tracées en code à la résolution finale : nettes, chiffres exacts)
`titre`, `impact`, `pile`, `surtitre` (mono, capitales, puce orange), `statut` (message d'état de l'IA, mono, point qui pulse,
frappé lettre à lettre), `document` (carte holographique qui s'assemble ligne par ligne : titre, destinataire, lignes, total,
tampon « APPROUVÉ » optionnel), `compteur` (nombre qui monte, de → à, suffixe, étiquette), `courbe` (projection : courbe qui
se trace, zone remplie, valeur finale), `cedule` (grille de N semaines qui se remplit, blocs colorés étiquetés), `pointage`
(heure frappée + nom + état), `appel` (carte d'appel : nom, sous-titre, onde vocale animée par la vraie voix), `trajet`
(ligne lumineuse qui relie des points du cadre : le signal), `etiquette` (VISION / EN PRÉPARATION), `flash`, `glitch`,
`carton` (fin). Chacune a `debut_f`, `duree_f`, une position et ses champs (voir `chaine/INCRUSTATIONS.md`). Le producteur peut
ajouter un gabarit demandé par une équipe s'il sert aux quatre (il est alors offert à toutes).

### 4.7 Autres outils (offerts, à justifier)
Blender 5.2.3 (pc1 : mêmes GPU que H3, donc compté dans le budget GPU : 1 unité = 2 min de rendu) ; Relief (3D depuis une
image) ; interpolation d'images : non disponible (préférer « slow motion » dans le prompt H3) ; la vitesse et les rampes du
montage (images mélangées).

## 5. Budget identique par équipe

| Poste | Budget |
|---|---|
| Fiches de distribution (Qwen-Image) | 8 (personnages, lieux, objets) |
| Images clés (Qwen-Image) | 24 |
| Plans vidéo H3, film principal + version courte 16:9 | **40 unités** (1 unité = un rendu ≤ 124 images ≈ 5,2 s ; de 125 à 243 images = 2 unités) |
| dont plans parlants (audio ancré) | au plus 12 |
| Version courte 9:16 native (768×1344) | 6 unités, rendues seulement si la file GPU le permet pour les **quatre** équipes (sinon recadrage du 16:9) |
| Reprises après la ronde de révision | 8 unités |
| Voix | ≤ 30 répliques, ≤ 3 prises chacune, toute la palette |
| Musique | 3 générations Lyria 3 Pro (ou Clip) ; l'équipe choisit |
| Montage | 1 EditPlan long + 1 court (+ 1 vertical), une révision |
| Écriture (jetons) | une session d'écriture et une session de révision, mêmes plafonds de tours et de dépense pour les trois sous-agents ; coût réel relevé par `outils/sous-agents/cout.sh` |

File GPU : la 5090 est partagée avec un autre film ; jamais plus de 6 rendus d'avance par film. Ordre de tournage : les plans
des quatre équipes sont entrelacés pour que personne n'attende plus qu'un autre.

## 6. Ce que chaque équipe rend : `equipes/<equipe>/`

### 6.1 `DOSSIER.md` (lisible par le fondateur)
1. **Concept** : idée en une phrase, logline, pourquoi ça vend OPSYS, ton, références.
2. **Scénario et voix hors champ** : séquence par séquence, avec chaque réplique (fr-CA) et sa durée visée.
3. **Distribution et direction des voix** : chaque personnage (qui, apparence, tenue, voix de la palette, direction de jeu).
4. **Liste de plans** (tableau) : id, séquence, durée, recette (`h3-max` / `h3-fast` / incrustation seule / noir), caméra,
   effets, son, réplique ancrée, statut honnête (RÉEL / EN PRÉPARATION / VISION).
5. **Direction musicale** : genre, BPM, structure en secondes, coups à caler (quel événement sur quel coup).
6. **Plan de montage** : rythme, transitions, textes à l'écran (≤ 7 mots par titre), étiquettes, carton.
7. **Version courte** (10 à 15 s : la soumission qui voyage par signal) et, si possible, 9:16.
8. **Auto-évaluation sévère** par critère (spectacle, clarté des fonctions, voix, musique, rythme, crédibilité) et risques.

### 6.2 `dossier.json` (lu par la chaîne ; tout champ inconnu est ignoré, tout champ manquant est signalé)
Contrôle : `python3 chaine/valider.py equipes/<equipe>/dossier.json casting/palette.json` (le même pour tous ; « OK » exigé).
```json
{
  "equipe": "opus",
  "titre": "…",
  "personnages": [{"id": "rep", "nom": "Étienne", "role": "représentant", "fiche": "<prompt Qwen-Image de la fiche>", "voix": "<id palette>"}],
  "lieux": [{"id": "serveur", "fiche": "<prompt Qwen-Image>"}],
  "cles": [{"id": "k01", "prompt": "<prompt Qwen-Image de la première image>", "format": "16:9"}],
  "voix": [{"id": "l01", "role": "narrateur", "voix": "<id palette>", "texte": "…", "direction": "…", "vitesse": 1.1, "prises": 2}],
  "plans": [{
    "id": "p01", "sequence": "S1", "recette": "h3-max", "images": 124, "graine": 1001, "format": "16:9",
    "refs": ["rep", "chantier"], "premiere": null, "parole": null,
    "prompt": "<prompt H3 complet, grammaire 4.1>",
    "camera": "…", "effets": "…", "son": "…", "statut": "VISION"
  }],
  "musique": {"prompt": "<prompt Lyria complet>", "bpm_vise": 124, "duree_s": 150,
              "coups": [{"t_s": 15.0, "evenement": "le signal quitte le téléphone"}]},
  "montage": {"long": {"<EditPlan v1>": "…"}, "court": {"<EditPlan v1>": "…"}, "vertical": null},
  "annexe": {"long": {"incrustations": [], "sfx": [], "son_plans": [], "etalonnage": {}}, "court": {}}
}
```
- `refs` : identifiants de personnages, lieux ou objets (≤ 9) ; `h3-max` seulement.
- `premiere` : `null`, une image clé (`"k01"`) ou `"fin:p03"` (la dernière image du plan p03 : enchaînement continu).
- `parole` : identifiant de réplique ancrée (plan parlant, `h3-max`, ≤ 243 images, la réplique doit tenir dans le plan).
- `montage.*` : EditPlan v1 exact (fps 24, format, `sources` = un objet par plan `{"kind": "video"}`, par réplique
  `{"kind": "audio"}` et `"musique": {"kind": "audio"}`). Les durées des voix et de la musique sont estimées à l'écriture ;
  la chaîne les remplace par les durées mesurées et signale ce qui ne tient plus (l'équipe corrige à la révision).
- `annexe.*.incrustations` : `[{"type": "document", "debut_f": 240, "duree_f": 96, "position": "droite", …champs}]`.
- `annexe.*.sfx` : `[{"type": "fouet|impact|montee|inverse|chute|clic|frappe|souffle|boom|drone", "debut_f": 0, "db": -6}]`.
- `annexe.*.son_plans` : `[{"plan": "p04", "db": -10}]` (son natif H3 gardé sous la musique).

### 6.3 Livrables du film
- **Film principal** : 90 s à 3 min, 16:9 (1920×1080, 24 i/s), français québécois.
- **Version courte** : 10 à 15 s, **la soumission qui voyage par signal** (photo → ciel → serveur → retour), 16:9, et 9:16
  si le budget GPU le permet.
- **Un seul carton remplaçable** : le nom et le logo vont changer. Ils vivent dans `marque-opsys.json` (nom, logo, signature,
  mentions) ; le carton est tracé en code depuis ce fichier. La voix hors champ ne prononce le nom qu'au plus une fois, dans une
  réplique isolée (régénérée en une minute si le nom change).

## 7. La ronde de révision (une seule)

Après le tournage, chaque équipe reçoit : la **planche** de ses plans (3 images par plan, numérotées), la liste des rendus
(durée réelle, temps GPU, défauts relevés par le producteur : texte ou logo dans l'image, visage déformé, franchise imitée),
ses **voix** (transcription Whisper, durée, débit, relief, et l'avis de l'oreille de machine : on ne peut pas écouter à sa
place), la grille mesurée de ses musiques, et un **premier montage** de son EditPlan. Elle décide elle-même : quelles reprises
(≤ 8 unités, prompt modifié ou nouvelle graine), quelle prise de voix, quelle musique, et rend un EditPlan révisé.

## 8. Jugement

Le producteur note chaque film, sévèrement, sur 10, par critère : **spectacle** (effets, échelle, puissance), **clarté des
fonctions** (un étranger comprend ce qu'OPSYS fait), **voix** (naturelle, québécoise, avec caractère), **musique** (entraînante,
calée), **rythme**, **crédibilité** (honnêteté, aucun défaut d'IA visible). Il recommande ; le fondateur choisit.
