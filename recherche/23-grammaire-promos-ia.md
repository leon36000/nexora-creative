# 23 — La grammaire des promos IA spectaculaires (v1.1, 03/11/2026)

**Pour qui** : les agents qui tournent en ce moment les films promotionnels de Creative et d'OPSYS-AI. **À lire d'abord** : §1 (les 16 règles), §5 (film « capacités infinies »), §6 (film d'entreprise OPSYS-AI), §7 (contrôle avant livraison). Le reste justifie.

**En une phrase** : les promos qui marchent en 2026 ne racontent pas l'outil, elles **le font jouer** : un plan fort avant 1 s, un plan toutes les 1 à 2,5 s, une musique à groove (110 à 135 BPM) qui s'arrête net avant chaque révélation, des personnages qui parlent ou crient dans l'image au lieu d'un narrateur doux, et une preuve visible (avant/après, ingrédients à l'écran) pour chaque capacité.

## 0. Méthode, corpus, limites

- **Corpus v1.1 : 102 vidéos analysées une à une, 101 exploitables** : lot 1 = les 2 courts demandés par le fondateur + 69 promos officielles ou démos de Higgsfield, OpenArt, Kling, Runway, Luma, Pika, MiniMax/Hailuo, Google Flow/Veo/Gemini Omni, OpenAI Sora, Seedance/Dreamina, LTX, Krea, Freepik/Magnific, Leonardo, Hedra, Vidu, Moonvalley, Meshy, Tripo, Autodesk Flow Studio ; lot 2 = 31 vidéos : 12 démos virales d'effets et faux films IA (dont 3 vidéos d'ErikDoesVFX à 1,4 à 8,8 M de vues, duels au sabre, dragon, transformation de super-héroïne), 9 films d'entreprise (ouvertures de keynote NVIDIA GTC 2024, GTC 2026, GTC Berlin 2026, CES 2026 ; Salesforce Agentforce ; LG U+ Enterprise ; deux films OpenAI) et 10 promos de plus (Runway, Luma, LTX, Seedance, OpenArt, Tripo, Higgsfield). 4 vidéos n'ont pas pu être téléchargées (privées ou 403). Listes avec liens, dates de mise en ligne et vues : annexes A et B.
- **Chaîne** : yt-dlp en ≤ 480p ; les vidéos de plus de 150 s sont coupées à 150 s (on analyse l'ouverture) ; mesures **par le code** (ffmpeg : coupes de plan par détection de scène au seuil 0,15 avec fusion des détections à moins de 0,3 s, durée, sonie intégrée EBU R128 et plage de sonie) ; analyse de **la vidéo entière avec son** par Gemini 4 Argon (OpenRouter, effort moyen ; effort élevé pour les deux courts du fondateur) sur une grille fixe (accroche 0-2 s, structure, escalade, capacités et preuves, textes à l'écran, voix, musique, design sonore, caméra, fin, faiblesses, règles). Deux planches d'images ont été regardées par moi pour contrôler Gemini sur les courts du fondateur : les descriptions concordent (jungle, timeline After Effects, « OMNI REFERENCE », vignettes Start/Middle/End).
- **Fiabilité** : durée, nombre de coupes, secondes par plan et LUFS sont **mesurés** ; tempo (BPM), énergie (1-10) et la note « spectaculaire » sont des **estimations de Gemini** (la note est généreuse : médiane 8/10 ; elle sert à classer, pas à juger). Le compteur de coupes rate une partie des transitions animées (motion design) : Gemini donne sa propre estimation à côté (annexe A, colonne Plans).
- **Droits** : toutes les vidéos ont été supprimées après analyse ; ne restent que les notes (JSON hors dépôt, dans le scratchpad de la session). Coût d'analyse des deux lots : ≈ 4,9 USD (OpenRouter, journalisé par appel).

## 1. Les 16 règles (applicables tout de suite)

| # | Règle | Seuil mesurable | Preuve dans le corpus |
|---|---|---|---|
| R1 | **Le plan le plus fort d'abord**, avant 1 s. Jamais de logo seul, jamais de carton noir en ouverture (sauf marque déjà célèbre : OpenAI peut ouvrir sur « Introducing Sora 2 », pas nous). | premier plan « wow » ≤ 1,0 s ; logo ≤ 0,8 s s'il est là | Luma Ray3.14 (zoom dans une nébuleuse, titre à 0,8 s), Kling 4.0 (sabreur face à un masque géant, flash manga à 0,8 s), Runway Gen-4.5 I2V (gros plan visage puis dézoom : elle chevauche une pieuvre géante à 1,5 s) |
| R2 | **Accroche = contraste** : échelle (gros plan → plan immense), absurde (mouche mafieuse, ours serveur), ou danger. Le son frappe dans la même image. | impact sonore (sub, coup, cri) sur la première image utile | 9Pbg (plongée à travers la canopée + grondement de cascade), Seedance 4K (TV cathodique → mouche en costume), Hailuo 02 (couteaux + cri vocal de la chanson) |
| R3 | **Un plan toutes les 1 à 2,5 s** dans les montages de démonstration ; **plans longs seulement comme preuve** (plan-séquence de 30 s, long take). | médiane 2,0 s/plan pour les vidéos notées ≥ 8 ; 2,8 s pour les ≤ 6 | Gemini Omni 1,02 s/plan (26 M de vues), Kling Creator Highlights 0,84 s, Butterfly Beyond Code 0,69 s ; contre-exemples assumés : Seedance « ON CUE » (long take de cirque, 6,9 s/plan) |
| R4 | **Escalade en 3 marches d'échelle** : personnel → lieu → monde (ou objet → foule → planète). Chaque marche ajoute un danger ou un effet. | 3 paliers d'intensité visibles ; le dernier tiers est le plus fort | 9Pbg (falaise → jaguar → pont qui cède → flèche → rocher), Pikapocalypse, Hell Grind |
| R5 | **Rendre chaque capacité évidente sans explication** : avant/après en écran partagé, ingrédients affichés **pendant** le résultat, prompt tapé à l'écran puis effet immédiat, interface en gros plan. | chaque capacité nommée a ≥ 1 preuve visuelle de ce type | Kling (5 ingrédients « OMNI REFERENCE » sous la scène générée ; 3 vignettes Start/Middle/End qui s'allument quand l'action les atteint), Higgsfield VFX (vidéo réelle en incrustation), Runway Aleph (« Remove all of the people and cars » tapé sur Times Square) |
| R6 | **Couper la musique pour prouver le son natif** : 0,5 à 1,5 s de silence musical sur une action (sabre, explosion, plongeon) laisse entendre le son généré. | ≥ 1 trou musical par film, sur un bruit diégétique | Kling 4.0 (silences à 15,5 s et 29 s), Pikapocalypse (retours au silence glacial) |
| R7 | **Pas de narrateur doux.** Dans le corpus, la voix vient surtout **des personnages dans l'image** (25 vidéos sur 70), de **personne** (18 : texte + musique + échantillons vocaux) ou d'un présentateur (12) ; un narrateur seul n'apparaît que 10 fois, et il est alors soit grave « bande-annonce », soit sincère et lent pour un film d'émotion, jamais « publicité lisse ». | voix off ≤ 25 % de la durée ; ≥ 2 répliques diégétiques ou cris | Meet Kling 4.0 (« You call the shots » dit face caméra), MiniMax H3 (« They ask me what I see. I said everything. » + cri au mégaphone), Kling The Beat (dispute filtrée au téléphone) |
| R8 | **Musique à groove, pas de nappe** : batterie dès les 2 premières secondes ou un drop avant 10 s ; tempo 110 à 135 BPM ; genres gagnants : big beat, hip-hop, funk, rock garage, jazz de batterie, drum & bass, orchestral hybride avec percussions. | BPM 110-135 (médiane du corpus 116, des meilleures 118) ; drop ≤ 10 s ; énergie ≥ 8/10 | 9Pbg (drum & bass 172 BPM), Wan 3.0 Prime (surf-rock 160), Kling Dynamic Motions (big beat 135), MiniMax « Edit the world » (percussions + « Hey! ») |
| R9 | **Échantillons vocaux dans la musique** (« Hey! », « Make it move », « Wake up ») : ils donnent l'énergie d'une voix sans le lissé d'un narrateur. | 2 à 4 interjections calées sur les temps | MiniMax « More than video » (« Make it move… Change the view »), Kling 4.0 (« Wake up »), Leonardo (« Yo, let's go! ») |
| R10 | **Coupe sur le temps, révélation sur le silence** : les coupes tombent sur les temps forts ; 0,3 à 1 s de silence total juste avant le titre ou la capacité phare, puis impact. | ≥ 80 % des coupes à ±2 images d'un temps ; 1 silence avant la révélation | Ray3 Modify (s'interrompt sur les cartons), Sora 2 « Sound on », LTX-2 (silence suspendu au clic sur l'interface, drop à 9 s) |
| R11 | **Textes courts, gros, une couleur d'accent** : 1 à 4 mots par carton, police géométrique grasse, une couleur fluo de marque, animation d'échelle ou de glissement rapide ; le texte se pose **sur** l'image, rarement sur un fond vide. | ≤ 4 mots par carton ; ≤ 1,5 s par carton ; 1 couleur d'accent | Kling 4.0 (« KLING IS BACK », « 30 SEC DURATION », rose sur blanc), Flow 2026 (« Every story »), Meet Kling (« KLING » puis « 4.0 » en vert fluo) |
| R12 | **Montrer le nombre** : compteurs, décomptes, barre de lecture qui défile (« 10 / 20 / 30 », « 00:30 »), grilles de dizaines de vignettes = l'infini rendu visible. | 1 moment « mur de résultats » (≥ 12 vignettes) | Flow 2026 (des centaines de vignettes qui convergent), Kling (timecode jusqu'à 00:29), Runway Ads (mosaïque) |
| R13 | **Boucle problème → phrase → résultat toutes les 10 à 15 s** quand on montre un outil (pas seulement de belles images). | ≥ 3 boucles complètes en 60 s | 9Pbg (danger dans la jungle → commande vocale → After Effects se remplit), Pikapocalypse (brosse à dents vivante → intrus → bombe → météorite, l'appli transforme chaque menace) |
| R14 | **Humour ou émotion, jamais neutre** : un gag, un personnage absurde, ou un vrai moment humain. Les démos « neutres » sont les moins bien notées. | 1 gag ou 1 moment d'émotion identifiable | Pika (bain zen + grondement), Freepik « Magnific One » (fillette en salopette), Luma « The Hug » (émotion pure, 65 BPM : l'exception qui confirme la règle) |
| R15 | **Fin courte et sèche** : coupe nette sur le pic, carton logo + appel de 1,5 à 3,5 s ; mieux : **une scène bonus** (gag, fausse fin, nouveau brief) après le carton. | carton ≤ 3,5 s ; pas de fondu long | Kling (carton de 2 s), Runway (1,7 s), 9Pbg (nouveau brief → sables mouvants), Pikaswaps et Sora 2 (scène après le carton) |
| R16 | **Format natif par écran** : jamais un 16:9 posé au milieu d'un 9:16 sur fond flou (Gemini le relève comme faiblesse sur les deux courts du fondateur : textes illisibles au téléphone). | 9:16 tourné ou recadré par plan, textes dans la zone sûre | 9Pbg et 5fuQ (défaut relevé par l'analyse) |

## 2. Ce que disent les chiffres (lots 1 et 2, n = 101 analyses exploitables)

| Mesure | Médiane du corpus | Médiane des notes ≥ 8 (n = 81) | Médiane des notes ≤ 6 (n = 9) | Source |
|---|---|---|---|---|
| Durée analysée | 70 s | 70 s | 86 s | code |
| Secondes par plan | 2,34 s | **2,09 s** | 2,94 s | code |
| Tempo | 118 BPM | 121 BPM | 115 BPM | Gemini |
| Énergie musicale | 8/10 | 8/10 | **5/10** | Gemini |
| Sonie intégrée | −15,1 LUFS (de −24,8 à −4,7) ; plage de sonie médiane 4,9 LU | — | — | code |

Lecture : la différence entre une promo « qui claque » et une démo plate tient d'abord à **l'énergie de la musique** (8 contre 5) et au **rythme des plans** (2 s contre 2,8 s), pas à la durée. La sonie n'est **pas** un levier : les promos vont de −24 à −5 LUFS, et les plateformes normalisent à la lecture. Garder −14 LUFS et une crête vraie à −1 dBTP, mais **compresser la musique** pour la densité (voir §4.7).

Voix (présence principale, n = 101) : personnages 33, aucune 25, voix off seule 21, présentateur 16, mélanges 6. **Mais les films d'entreprise font exception** : 6 des 9 reposent sur une voix off (NVIDIA, Salesforce, LG), toujours posée et grave, **sur un montage frénétique** : le contraste voix lente / image rapide est leur signature (§6).

## 3. Les deux courts demandés par le fondateur

### 3.1 [9Pbg-_ptBcE](https://youtube.com/shorts/9Pbg-_ptBcE) — « Higgsfield x Claude Opus 5.5 for Motion Design » (Higgsfield, 26/09/2026, 73 s, 190 k vues au 03/11)

- **Accroche (0-2,5 s)** : logo de la collaboration sur une jungle, puis plongée de caméra à toute vitesse à travers la canopée jusqu'à une cascade ; grondement d'eau et souffle. L'échelle du mouvement fait le travail.
- **Récit** : un motion designer suspendu au-dessus du vide reçoit un SMS « Need a motion promo video. ASAP » ; une mascotte pixel lui propose des outils compliqués (texte d'expression After Effects `time * 60 wiggle(2,10)` flottant dans le décor) ; il refuse et **dicte** à Claude. Ensuite, **double escalade parallèle** : danger physique (jaguar, pont de singe qui cède, flèche, rocher à la Indiana Jones) et complexité de ce qui se construit tout seul dans After Effects (logo, calques avec images clés, carte isométrique animée, page « THE SUN GATE »).
- **Rythme** : 23 plans mesurés (3,15 s/plan) mais perçu rapide : mouvements internes incessants, zooms dans l'interface, drum & bass à ≈ 172 BPM qui entre à 22 s, au moment où l'on passe dans l'interface.
- **Preuve** : gros plans sur la timeline After Effects (barres de calques et losanges d'images clés qui se posent en rythme) : la promesse « projet éditable » est montrée, pas dite.
- **Voix** : jeu d'acteur haletant et pressé (« Render the final and send it to the client! ») contre une mascotte pince-sans-rire ; aucun narrateur.
- **Fin** : fausse résolution, nouveau brief (« a safety video for the reserve ») puis chute dans des sables mouvants ; une ligne d'appel en petit sous la mascotte (3,5 s) et coupe au noir.
- **Faiblesses** : 16:9 dans un cadre 9:16 sur fond flou (texte d'interface illisible au téléphone) ; course du jaguar physiquement incohérente.
- **À reprendre chez nous** : la boucle *danger réel → une phrase → l'outil exécute* toutes les 10 à 15 s ; le zoom sur la preuve éditable (notre timeline Mode Studio, le devis, la grille de prises) ; la fin-gag qui relance.

### 3.2 [5fuQnUuu1BM](https://youtube.com/shorts/5fuQnUuu1BM) — « Kling 4.0 makes AI video look like a real film shoot » (Higgsfield, 29/10/2026, 36 s, 29 k vues)

- **Accroche (0-1,5 s)** : homme en costume, katana, face à un masque robotique géant ; flash rouge et trame manga à 0,8 s, « HIGGSFIELD » rose fluo ; sub industriel saturé dès la première milliseconde.
- **Structure** : promesse typographique (« KLING IS BACK », « THE DEFINING VIDEO MODEL ») → crâne robotique translucide → **trois capacités, une preuve chacune** : *Omni Reference* (décor, sabres, personnage, onde sonore, mécha posés à plat, puis la scène où tout interagit, vignettes gardées sous la vidéo), *30 SEC DURATION* (décompte géant 10 / 20 / 30, barre jaune et timecode qui défile jusqu'à 00:29 sur un plan continu), *START / MIDDLE / END* (plongeon d'un bateau parmi des poissons rouges, les 3 vignettes s'allument au moment exact) → « COMING 4K SOON » sur un visage parcouru d'une grille de points → carton de 2 s.
- **Son** : techno industrielle ≈ 115 BPM, énergie 9 ; **deux silences musicaux** (15,5 s et 29 s) pour laisser entendre les sabres, l'explosion et l'eau ; échantillon vocal « Wake up ».
- **Habillage** : fond blanc, typographie géométrique noire et rose fluo autour de vidéos sombres : identité reconnaissable en une image.
- **Faiblesses** : même cadre 16:9 dans 9:16 ; le plan de 30 s est accéléré, on ne juge pas la fluidité.
- **À reprendre chez nous** : « une capacité = un mot géant + une preuve qui garde ses ingrédients à l'écran » ; les silences pour le son natif de H3 ; un habillage clair et une couleur (notre orange #FF5A1F sur encre ou sur blanc).

## 4. Dimension par dimension

### 4.1 Accroche des deux premières secondes
Les 35 accroches notées 9 ont toutes au moins deux de ces trois ingrédients : **mouvement de caméra violent ou changement d'échelle** (plongée, crash zoom, dézoom de révélation), **sujet improbable** (créature, échelle impossible, personnage absurde), **impact sonore synchrone**. Les ouvertures lentes (citation sur fond noir chez Luma « This is Ray3 », carton « Introducing Sora 2 ») ne marchent que pour des marques qui ont déjà l'attention.
Modèles d'accroche à copier pour Creative : (a) *gros plan → dézoom* : un œil, puis le dragon dont c'est l'œil, puis la ville sous ses ailes ; (b) *prompt tapé → monde* : trois mots tapés en blanc, frappe de touche, coupe sur le plan qui en sort ; (c) *quotidien → absurde* : une cuisine banale, une phrase, la cuisine devient un pont de vaisseau.

### 4.2 Rythme
Deux régimes coexistent dans les meilleures promos : **rafales** (0,7 à 1,5 s par plan, sur 4 à 8 temps) et **respirations** (un plan de 3 à 6 s qui prouve : un long take, un avant/après). Alterner rafale – respiration – rafale. Ne jamais dépasser 6 s sans coupe hors plan-preuve. Avec H3 (plans de 5 s) : un rendu donne 2 à 3 coupes utilisables (début, pic du mouvement, fin) ; prévoir 1,5 rendu par seconde de film en rafale.

### 4.3 Escalade
Schéma dominant en quatre temps : **promesse (0-5 s) → démonstration (une capacité par bloc de 4 à 8 s) → escalade (échelle et nombre) → révélation (la capacité phare, après un silence)** → appel. L'intensité monte par l'échelle (une personne → une ville → une flotte), par le nombre (un effet → dix effets → mur de vignettes), par l'enjeu (danger). Le dernier tiers doit être le plus fort, et la révélation arrive à 70-85 % de la durée.

### 4.4 Rendre les capacités évidentes
Classement des preuves les plus fréquentes : (1) **écran partagé avant/après** (réel ↔ IA, brouillon ↔ 1080p chez Seedance Draft) ; (2) **ingrédients visibles pendant le résultat** (images de référence en vignettes sous la vidéo) ; (3) **prompt tapé à l'écran** puis effet immédiat ; (4) **interface en gros plan** (timeline, calques, boutons) avec zoom et flou de bougé ; (5) **compteur** (durée, nombre de plans, prix). Pour Creative, nos preuves uniques : **le devis chiffré avant dépense**, **la grille de prises jugées**, **le Producteur qui découpe une phrase en plans**, **la bulle « Effet IA ici… »** au clic droit. Les montrer en gros plan, 1,5 à 3 s chacune.

### 4.5 Textes à l'écran
1 à 4 mots, capitales géométriques grasses, une couleur d'accent, animation d'entrée de 4 à 8 images (échelle 120 % → 100 %, glissement, découpe par masque), sortie sur la coupe. Les noms de capacités deviennent des **titres-objets** (« OMNI REFERENCE », « 30 SEC ») placés autour de l'image, pas des sous-titres. Sous-titres de dialogue en bas, mot actif en couleur (style CapCut) seulement s'il y a de la parole.

### 4.6 Voix : remède au « beaucoup trop smooth »
Ce qui rend notre voix actuelle lisse (films V5, `campagne-films/films-v3/RAPPORT.md`) : une narration continue posée sur tout le film, débit régulier de 2,1 à 2,3 mots/s, musique baissée de 10 dB dessous, direction « Apple ». Le corpus fait l'inverse :
1. **Remplacer la narration par des répliques dans l'image** : H3 sait faire parler et crier ses personnages (balise de dialogue) ; 3 à 6 répliques de 2 à 6 mots, criées, chuchotées, ordonnées (« Bouclier ! », « Ils arrivent ! », « Feu ! »), réparties sur le film.
2. **Si narration il y a : bande-annonce, pas publicité** : timbre grave et rauque, phrases de 3 à 7 mots, **une phrase par coupe**, attaques franches, pauses de 0,15 à 0,25 s posées au montage (déjà mesuré par l'équipe voix) ; deux registres alternés (murmure → cri). Leviers concrets : ElevenLabs v4 avec stabilité basse et style haut ; Drama 3 **sans** consigne lente et `speed` 1,10 à 1,15 (rapport voix manche 2) ; Chatterbox avec `exaggeration` ≈ 0,7 et `cfg_weight` ≈ 0,3, réglage que son README conseille pour une parole « expressive ou dramatique » ([resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox), lu le 03/11/2026).
3. **Musique au même niveau que la voix sur les impacts**, ducking de 4 à 6 dB seulement (pas 10), et la musique repart pleine entre les phrases.
4. **Échantillons vocaux dans la musique** (R9) : enregistrer ou générer 4 interjections (« Hé ! », « Action ! », « Encore ! », « Plus grand ! ») et les caler sur les temps.
5. Test simple avant livraison : si l'on peut couper le son et que le film reste compréhensible **et** si l'on peut couper l'image et que le son seul donne envie de bouger, c'est gagné.

### 4.7 Musique entraînante
- **Tempo 110-135 BPM** pour une promo d'outil ; 140-175 (drum & bass, surf-rock) pour une rafale d'action courte ; < 90 seulement pour un film d'émotion.
- **Structure** : intro tendue 2 à 8 s (souvent un riff ou un beat sec, pas une nappe) → **drop avant 10 s** → groove continu avec relances toutes les 4 ou 8 mesures → **arrêt sec** (0,3 à 1 s) avant la révélation → reprise plus forte → coupe nette sur le carton.
- **Genres** qui dominent les vidéos notées 9 : big beat et hip-hop percussif, funk et nu-disco, rock garage et rock alternatif, jazz de batterie et big band, orchestral hybride avec percussions lourdes et chœur. Les nappes ambiantes et le lo-fi sont réservés aux tutoriels (notés plus bas).
- **Pour Music3 / Lyria** : demander explicitement « punchy, driving drums from bar 1, drop at 8 seconds, stop-time break before the final hit, 124 BPM » ; générer 4 candidates, mesurer la courbe d'énergie et le tempo (`marketing/creative/outils/analyser_musique.py`, `tempo.py`), garder celle dont le drop tombe avant 10 s ; poser l'image sur sa grille (coupes aimantées).
- **Mixage** : −14 LUFS intégrés, crête vraie ≤ −1 dBTP, mais musique compressée (plage de sonie basse) et **trous musicaux volontaires** (R6) plutôt qu'un fond constant.

### 4.8 Design sonore
Toutes les vidéos notées 9 ont un design sonore dense : whooshes sur chaque mouvement de texte, sub-drops sur les coupes de section, impacts sur les titres, risers de 1 à 2 s avant les drops, sons diégétiques laissés seuls dans les trous musicaux. Chez nous : H3 fournit le son diégétique ; ajouter une banque de 20 effets (whoosh, impact, riser, sub, clic d'interface, frappe de touche) posés par le montage aux coupes et aux titres.

### 4.9 Fin
Carton de 1,5 à 3,5 s, coupe sèche, une ligne d'appel (« Essayez Creative »), puis **scène bonus** de 2 à 5 s (gag, réplique d'un personnage, nouveau brief). Les fondus longs et les cartons de 6 s (MiniMax « Butterfly ») sont l'exception.

### 4.10 Effets spéciaux et action : ce qu'apprennent les démos virales (lot 2)
Les démos d'effets les plus vues (ErikDoesVFX : [Did AI Just Change Movies Forever?](https://youtu.be/BRESQ8NX-us) 8,8 M de vues, [Did AI Just Kill VFX?](https://youtu.be/eIq1uw8q3dE) 1,8 M, [Is AI The New VFX?](https://youtu.be/jfGVMfle07g) 1,4 M) et les faux films (duels au sabre, dragon en vue subjective, transformation de super-héroïne) donnent six règles propres aux VFX :
1. **Réel d'abord, effet ensuite, dans le même mouvement** : un plan-séquence réel (présentateur qui marche, travelling arrière) dans lequel les créatures se construisent en direct. Le spectateur croit l'effet parce que la caméra ne coupe pas.
2. **La transformation en un seul plan de 4 à 5 s**, déclenchée sur le drop (armure qui grimpe sur la joue et le bras d'une motarde lancée à pleine vitesse, flash synchronisé au drop à 3,4 s) : prouve « pas de triche au montage ». À l'inverse, **le combat se découpe en plans de 0,3 à 0,5 s** avec un impact sonore à chaque coupe : cela cache les limites physiques du modèle (le duel Jaina contre Desann : 296 coupes en 142 s).
3. **Lumière diégétique forte** (sabres, néons, feu, éclairs) : elle unifie des plans générés séparément et masque les écarts de rendu.
4. **Le son fait croire à l'image** : respirations, bourdonnement des lames, impacts précis ; un design sonore familier rend crédible un plan imparfait.
5. **Rupture de ton aux deux tiers** (un juron en plein vol, un gag) : c'est ce qui rend la démo partageable.
6. **Ne pas étirer une scène d'action dans un seul décor au-delà de 30 à 45 s** : changer de lieu ou d'échelle.
Pour nous : pas de franchise ni de personnage protégé (Star Wars, Toy Story) : le « et si ? » doit porter sur nos propres personnages et sur le quotidien du spectateur (sa rue, son garage, son bureau).

## 5. Recette A — « Les capacités de Creative sont infinies » (effets spéciaux, dragons, explosions, batailles spatiales, duels au sabre lumineux)

**Idée** : une seule personne ordinaire, une seule phrase à la fois, et le monde qui monte d'une marche à chaque phrase. Le fil : la phrase tapée (ou dite) dans Creative, qui devient le plan suivant. Personnage proposé : une technicienne d'atelier québécoise (jamais de célébrité ni de franchise : « sabre de lumière » générique, vaisseaux originaux, aucun logo de film).

**Format maître** : 45 s en 9:16 natif (réseaux) ; 75 s en 16:9 (site). Tempo de la piste : 124 BPM (une mesure = 1,94 s). Les temps ci-dessous sont pour 45 s.

| Temps | Mesures | Image | Texte à l'écran | Son | Preuve |
|---|---|---|---|---|---|
| 0,0-1,0 | — | Très gros plan d'un œil reptilien doré qui s'ouvre ; dézoom brutal : un dragon posé sur le toit de son atelier | — | sub + rugissement (son H3) | accroche R1-R2 |
| 1,0-2,9 | 1 | Elle, au clavier, tape « un dragon sur mon toit » ; frappe de touche sur chaque mot | la phrase en blanc, mot par mot | beat sec qui démarre | prompt → monde (R5) |
| 2,9-7,8 | 2,5 | Rafale de 4 plans (1,2 s) : le dragon décolle, survole Montréal la nuit, crache du feu sur le fleuve, frôle la caméra | « UNE PHRASE. » | **drop** à 3,9 s | escalade marche 1 |
| 7,8-9,7 | 1 | Gros plan sur Creative : le Producteur découpe la phrase en 5 plans, devis affiché « 43 crédits » | « 5 PLANS. 1 DEVIS. » | clics d'interface | preuve unique (devis) |
| 9,7-17,5 | 4 | Elle tape « plus grand » : rafale de 6 plans (1,3 s) : explosion en ralenti d'une usine, onde de choc qui soulève des voitures, débris au premier plan | « PLUS GRAND. » | relance à chaque mesure, whoosh | escalade marche 2 |
| 17,5-18,5 | ½ | **silence total**, écran partagé : sa photo de garage ↔ le même garage devenu hangar de vaisseau | — | silence puis clic | avant/après (R5, R10) |
| 18,5-26,3 | 4 | Bataille spatiale : flotte au-dessus de la Terre, saut en hyperespace, chasseurs qui passent sous la caméra ; une réplique criée dans un cockpit « Bouclier ! » | « PLUS LOIN. » | reprise plus forte, échantillon « Hé ! » | escalade marche 3 + voix diégétique (R7) |
| 26,3-34,0 | 4 | **Duel au sabre de lumière** : deux combattantes dans un temple en ruine sous l'orage ; la musique se coupe 1 s sur le choc des lames (son H3 seul) ; ralenti sur l'étincelle | « RIEN N'EST TROP. » | trou musical sur le choc (R6) | son natif |
| 34,0-37,9 | 2 | **Mur de résultats** : la grille des prises jugées (Prise 1 à 4, la gagnante entourée) puis zoom arrière sur 48 vignettes de tous les plans du film | « 48 PLANS. 1 APRÈS-MIDI. » (seulement si vrai : chiffre du journal de tournage) | riser | nombre (R12), juge |
| 37,9-38,8 | ½ | noir, silence | — | silence | révélation (R10) |
| 38,8-42,0 | 1,5 | Retour dans l'atelier : le dragon passe la tête par la porte de garage, elle lui tend un café | « NEXORA CREATIVE » + « Une phrase suffit. » | impact final, coupe nette | humour (R14) |
| 42,0-45,0 | 1,5 | Carton orange sur encre, adresse ; **scène bonus** : elle tape « une deuxième tasse » | « Essayez Creative » | dernier coup | fin R15 |

**Plans H3 à tourner** (recette `h3-max` sur la 5090 ; *Singularity* pour les créatures, vaisseaux et combats non humains, H3 officiel pour les humains, recherche/10) : ≈ 22 plans de 5 s pour 45 s, dont 8 en I2VA depuis une image clé Qwen vérifiée (dragon, hangar, temple), 2 en Ref2VA pour tenir l'héroïne (`@` personnage, fiche Qwen), 2 dialogues courts criés. Prompts : « photorealistic cinematic CG » pour dragon, flotte, explosions ; « live-action, large-format cinema camera, real actors » pour l'héroïne (recherche/10, leçon 2). Mouvements imposés : dézoom de révélation, survol rasant, travelling sous les vaisseaux, orbite lente sur le duel.
**Musique** : Music3, « driving big beat / hybrid orchestral trailer, 124 BPM, punchy drums from bar 1, drop at 4 s, stop-time break at 17 s and 38 s, choir hits, final hit and hard stop » ; 4 candidates, choix par la courbe d'énergie.
**Voix** : aucune narration ; 3 répliques H3 (« Bouclier ! », « Maintenant ! », un rire) ; 3 échantillons vocaux calés sur les temps.
**Version 75 s (16:9)** : même ossature, une marche de plus (« plus vrai » : ses propres photos animées, un personnage `@` qui garde son visage sur 3 plans, R5 avec l'écran partagé), et un bloc de 6 s sur la bulle « Effet IA ici… » du Mode Studio (clic droit, « ambiance film d'horreur », la couche s'applique).

**Règles de vérité** (non négociables, comme pour les films V5) : chaque chiffre à l'écran vient du journal réel du tournage ; chaque capture d'interface est réelle ; les plans générés sont signalés comme tels dans la mention de fin.

## 6. Recette B — film d'entreprise OPSYS-AI spectaculaire

Le concept existant (`campagne-films/films/opsys/CONCEPT.md`, « Ils travaillent. Vous vivez. ») est juste sur le fond (l'humain décide, dix départements) mais sa grammaire est celle d'une publicité calme. Les films d'ouverture de conférences et les promos d'agents du corpus suggèrent de garder l'histoire et de changer l'énergie :

1. **Accroche** : pas le noir et la question en premier : **le chaos d'abord** (téléphone qui sonne, trois messages, un camion en retard, la pluie sur un chantier : 4 plans de 0,5 s), puis **coupe au silence** et la question « Opsys, on en est où ? ».
2. **Les dix départements comme une équipe de casse** (film de braquage, « heist ») : chaque département entre sur un temps, cadré comme un personnage (surtitre « M3 · ESTIMATION » en gros, une action en 3 mots, un geste net), **rafale de 10 plans de 1 mesure** à 124-128 BPM, whoosh et impact par entrée ; split-screen 2×2 puis 3×3 à la 8e mesure pour montrer qu'ils travaillent **en même temps** (R12).
3. **Preuves réelles en gros plan** (règle de vérité de `FAITS.md`) : la soumission PDF brouillon de M3, la facture brouillon de M5, la demande d'approbation N3 sur le téléphone : 1,5 s chacune, zoom et flou de bougé, comme la timeline After Effects du 9Pbg.
4. **Moment humain** (R14) : le match de hockey du soir, la fille au déjeuner ; la musique s'adoucit seulement là (2 mesures), puis repart.
5. **La décision, sur un silence** : « Le deuxième camion, on peut ? » → l'avatar répond (réplique courte, vraie voix grave, pas lisse) → **silence d'une demi-mesure** → « Approuvé. » sur un clic et un coup de grosse caisse (R10).
6. **Fin** : carton « OPSYS-AI · Ils travaillent. Vous vivez. » de 2,5 s, puis **scène bonus** : le téléphone vibre à 6 h 12 le lendemain, « M1 : trois nouvelles demandes, déjà qualifiées », Marc se rendort en souriant.
7. **Son** : funk ou big beat à 124 BPM avec cuivres (registre « mission » de *Catch Me If You Can*, comme la promo MiniMax H3 très bien notée), échantillons « Go! » ; voix de l'avatar au même niveau que la musique sur les impacts.
8. **Durées** : 60 s (site), 30 s (chaos → 4 départements → approuvé → carton), 15 s (chaos → « Approuvé. » → carton).

**Ce que font les 9 films d'entreprise du lot 2** (NVIDIA GTC et CES, Salesforce Agentforce, LG U+, OpenAI), à appliquer à OPSYS-AI :
- **Voix posée et grave sur un montage frénétique** : Salesforce pose une voix rauque de bande-annonce (« Is AI going to replace us, or are we going to be in command of it? ») sur des coupes de moins d'une seconde (75 plans en 60 s) ; LG U+ : 34 plans en 30 s sous une voix institutionnelle grave. Pour OPSYS-AI, si narration il y a, c'est celle-là : grave, lente, peu de mots, **jamais sur un montage lent**.
- **Rendre visible le travail invisible de l'IA** par des incrustations d'interface (compteurs qui défilent, fiches qui s'ouvrent, boîtes de détection, jauges) **posées sur les plans de vie réels**, et par le raccord « simulation → réel » (NVIDIA : jumeau numérique de la gare de Marseille, puis la vraie foule). Chez nous : la carte « M3 · soumission prête » s'ouvre au-dessus du chantier filmé, puis le client signe dans le plan suivant.
- **Rafales rythmiques** de 4 à 6 plans de 0,3 s sur les temps forts au milieu d'une narration plus posée (NVIDIA GTC 2026) : idéal pour l'entrée des dix départements.
- **Raccord géométrique** (LG U+ : un cercle gardé au centre de l'écran pendant 6 à 8 plans différents) et **jeu de format** : le problème enfermé dans un cadre réduit, l'image qui s'ouvre en plein écran quand l'IA entre en scène.
- **Une question universelle comme enjeu** (Salesforce : remplacer ou commander) ; pour OPSYS-AI : « Qui garde la main ? » → « Vous. Toujours. » (cohérent avec les approbations N0-N5, réelles).
- **Ce qu'il ne faut pas copier** : les ouvertures de keynote lentes (noir, violons, particules pendant 5 à 20 s) sont faites pour une salle obscure ; Gemini les juge peu efficaces en ligne. En ligne, l'accroche reste R1.

## 7. Contrôle avant livraison (mesurable, à automatiser dans `revue.py`)

| Contrôle | Seuil | Comment le mesurer |
|---|---|---|
| Premier plan fort | ≤ 1,0 s ; aucun carton noir ou logo seul au-delà de 0,8 s | première coupe (scdet) + inspection de l'image 0,5 s |
| Rythme | médiane 1,5 à 2,5 s par plan ; aucun plan > 6 s sauf plan-preuve déclaré | `scdet` seuil 0,15, fusion à 0,3 s |
| Coupes sur la grille | ≥ 80 % à ±2 images d'un temps | grille de `tempo.py` |
| Drop | ≤ 10 s | courbe d'énergie de la musique |
| Trous musicaux | ≥ 1 trou de 0,5 à 1,5 s sur un son diégétique ; 1 silence avant la révélation | `silencedetect` sur la piste musique seule |
| Voix | narration ≤ 25 % de la durée ; ≥ 2 répliques diégétiques ; ducking 4 à 6 dB | stems voix/musique |
| Textes | ≤ 4 mots, ≤ 1,5 s par carton, zone sûre 9:16 | spec des cartons |
| Preuves | chaque capacité nommée a une preuve (avant/après, ingrédients, interface, compteur) | liste du brief |
| Format | 9:16 natif (aucun 16:9 sur fond flou) | dimensions des plaques |
| Sonie | −14 LUFS ±1, crête vraie ≤ −1 dBTP | `ebur128` |
| Fin | carton 1,5 à 3,5 s ; scène bonus recommandée | durée du dernier segment |
| Vérité | tout chiffre à l'écran a sa source dans le journal | revue manuelle |

## 8. À ne pas faire (faiblesses relevées dans le corpus)

- 16:9 dans un 9:16 sur fond flou (les deux courts du fondateur) ; textes d'interface trop petits pour un téléphone.
- Tutoriels « présentateur + musique lo-fi » : énergie 2 à 5, les moins bien notés (OpenArt VFX, Higgsfield « same face »).
- Plan de démonstration de 30 s accéléré : il ne prouve plus la fluidité.
- Ouverture philosophique lente quand la marque n'est pas connue.
- Narration continue posée sur toute la musique (notre défaut actuel).
- Physique incohérente laissée dans un plan-vedette (course du jaguar) : le juge visuel doit écarter ces prises.

## 9. Limites de cette version

- BPM, énergie et notes sont des estimations d'un modèle ; aucune écoute humaine. Le compteur de coupes sous-compte les transitions animées.
- Les vidéos longues n'ont été analysées que sur leurs 150 premières secondes.
- Le corpus est biaisé vers les chaînes officielles (promos montées par des pros) ; 12 démos virales seulement.
- Les vues ne mesurent pas la conversion ; aucune donnée de clics ni d'inscriptions.
- Prochaines étapes (v2) : passer à 200 puis 300 vidéos par lots (TikTok et Instagram n'ont pas été explorés), mesurer automatiquement la synchronisation des coupes sur les temps (onsets), et confronter les recettes A et B à un vrai montage noté par le fondateur.

## Annexe A — Corpus du lot 1 (trié par note Gemini, puis par marque)

Colonnes : durée analysée (s) ; plans mesurés (estimation Gemini entre parenthèses) ; secondes par plan mesurées ; BPM et énergie estimés ; voix principale ; sonie intégrée mesurée ; note « spectaculaire » de Gemini. Dates de mise en ligne et vues relevées par yt-dlp le 03/11/2026.

| # | Marque | Vidéo (id) | Date | Vues | Durée s | Plans | s/plan | BPM | Énergie | Voix | LUFS | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Freepik | [Magnific One: Art Direction Built Into AI Image Generation](https://youtu.be/CUJ0mgONj7Q) | 20261008 | 39775 | 58 | 28 (28) | 2.09 | 112 | 8 | personnages | -17.6 | 9 |
| 2 | Freepik | [SLICE — AI short film made with Seedance 2.5](https://youtu.be/p2WiG5H-pOg) | 20260906 | 15991 | 142 | 49 (49) | 2.89 | 115 | 6 | personnages | -22.1 | 9 |
| 3 | Google | [Introducing Flow / Google’s New AI Filmmaking Tool](https://youtu.be/A0VttaLy4sU) | 20250520 | 938243 | 105 | 28 (32) | 3.74 | 88 | 6 | voix off | -16.1 | 9 |
| 4 | Google | [Introducing the New Flow, Your AI Creative Studio](https://youtu.be/BGuxsk79sYY) | 20260225 | 136965 | 60 | 25 (25) | 2.38 | 116 | 8 | aucune | -15.0 | 9 |
| 5 | Google | [Introducing Gemini Omni: Create Anything from Anything](https://youtu.be/KUyRq7szZsM) | 20260519 | 26067966 | 54 | 53 (53) | 1.02 | 108 | 8 | aucune | -16.2 | 9 |
| 6 | Higgsfield | [Higgsfield x Claude Opus 5.5 for Motion Design / Editable Af](https://youtu.be/9Pbg-_ptBcE) | 20260926 | 190348 | 73 | 23 (25) | 3.15 | 172 | 8 | personnages | -7.1 | 9 |
| 7 | Higgsfield | [Hell Grind / Official Trailer / Higgsfield Original Series](https://youtu.be/CVzfQuC0aMU) | 20260519 | 243846 | 150 | 102 (102) | 1.47 | 115 | 9 | personnages | -11.7 | 9 |
| 8 | Higgsfield | [I Added Insane AI VFX to Real Footage in 4K(Seedance 2.0)](https://youtu.be/Yte-UGhYkPQ) | 20260629 | 425347 | 150 | 27 (27) | 5.56 | 110 | 6 | présentateur | -15.5 | 9 |
| 9 | Higgsfield | [Change Everything in Your Video / Seedance 2.5 + Genjutsu](https://youtu.be/b6wVWdnN97M) | 20261031 | 34188 | 56 | 7 (12) | 7.95 | 122 | 7 | présentateur | -14.1 | 9 |
| 10 | Kling | [Kling 4.0 Creator Highlights: Dynamic Motions](https://youtu.be/V-qElAG3kDQ) | 20261029 | 75809 | 75 | 90 (90) | 0.84 | 135 | 9 | aucune | -16.7 | 9 |
| 11 | Kling | [Meet KLING 4.0 / You Call the Shots](https://youtu.be/nlM7kL3kv_Y) | 20260928 | 159063 | 114 | 73 (73) | 1.56 | 125 | 9 | personnages | -13.4 | 9 |
| 12 | Kling | [The Beat / Made with KLING 4.0](https://youtu.be/w3397LF5MAc) | 20260928 | 163738 | 150 | 127 (127) | 1.18 | 128 | 9 | personnages | -15.3 | 9 |
| 13 | LTX | [Introducing LTX-2: 4K AI Video with Audio and Lipsync](https://youtu.be/KRJW3yXwJdY) | 20251023 | 475708 | 47 | 28 (28) | 1.68 | 130 | 8 | voix off et personnages | -11.7 | 9 |
| 14 | LTX | [Apple-Level Product Ads in 60 Seconds (AI Tutorial)](https://youtu.be/iOJcIm5bVOw) | 20250911 | 154980 | 72 | 48 (48) | 1.49 | 124 | 8 | voix off | -19.2 | 9 |
| 15 | Leonardo | [Yours To Create](https://youtu.be/-f9rxj2goYM) | 20260218 | 4164 | 70 | 40 (40) | 1.75 | 115 | 9 | personnages | -11.4 | 9 |
| 16 | Luma | [Luma AI - Introducing Ray3 Modify](https://youtu.be/4s-wRxtSKC0) | 20251218 | 39833 | 44 | 30 (30) | 1.46 | 125 | 9 | aucune | -7.9 | 9 |
| 17 | Luma | [The Hug](https://youtu.be/lVskemTwfEU) | 20260409 | 101676 | 94 | 8 (16) | 11.79 | 65 | 3 | voix off et narrateur à l'écran | -13.0 | 9 |
| 18 | Luma | [Luma AI - Introducing Ray3.14](https://youtu.be/w7ZCcWsx5bU) | 20260126 | 24233 | 26 | 16 (16) | 1.64 | 110 | 9 | aucune | -7.2 | 9 |
| 19 | Luma | [Luma AI - This is Ray3](https://youtu.be/z2UIcD2xvsA) | 20250918 | 42992 | 64 | 50 (50) | 1.28 | 115 | 9 | voix off | -7.2 | 9 |
| 20 | MiniMax | [MiniMax-H3 Is Now Publicly Available](https://youtu.be/AvjamLzt2pg) | 20260803 | 146055 | 42 | 30 (30) | 1.38 | 128 | 9 | personnages | -11.2 | 9 |
| 21 | MiniMax | [Hailuo AI /  Video 02 Model](https://youtu.be/J18idUz87LA) | 20250618 | 6163521 | 54 | 22 (22) | 2.46 | 155 | 9 | voix off | -4.7 | 9 |
| 22 | MiniMax | [🎬 Butterfly Beyond Code / Official Trailer](https://youtu.be/JmaEB1w-Bn4) | 20260702 | 22534 | 85 | 123 (123) | 0.69 | 128 | 9 | personnages | -13.8 | 9 |
| 23 | MiniMax | [More than video. Edit the world.](https://youtu.be/z8sb0ghbTDI) | 20260819 | 1120 | 60 | 63 (63) | 0.95 | 116 | 9 | aucune | -11.4 | 9 |
| 24 | OpenAI | [Sound on for Sora 2](https://youtu.be/1PaoWKvcJP0) | 20250930 | 554744 | 134 | 104 (104) | 1.29 | 120 | 8 | présentateur | -15.1 | 9 |
| 25 | OpenAI | [This is Sora 2](https://youtu.be/lEcg6AJ6DVY) | 20250930 | 849525 | 57 | 23 (13) | 2.49 | 100 | 6 | personnages | -16.0 | 9 |
| 26 | Pika | [Introducing Pika H3 Flex / Built for Professional Iteration](https://youtu.be/-R2ftjEOSX0) | 20261029 | 3380 | 63 | 25 (25) | 2.51 | 120 | 8 | personnages | -9.7 | 9 |
| 27 | Pika | [Introducing Pikaswaps!](https://youtu.be/CvSHo5lnNyY) | 20250220 | 10515 | 40 | 24 (24) | 1.65 | 120 | 9 | personnages | -9.5 | 9 |
| 28 | Pika | [Pikapocalypse](https://youtu.be/xSLyQdsBdZY) | 20250512 | 15477 | 121 | 45 (45) | 2.69 | 122 | 8 | personnages | -16.4 | 9 |
| 29 | Runway | [Introducing Gen-4.5 Image to Video / Runway](https://youtu.be/AwKSrJFvdps) | 20260121 | 590634 | 69 | 69 (69) | 1.0 | 120 | 8 | voix off | -13.1 | 9 |
| 30 | Runway | [Introducing Gen-4.5 / Runway](https://youtu.be/ei2PsDpPbB4) | 20251201 | 120242 | 88 | 74 (74) | 1.19 | 125 | 9 | voix off et personnage final | -9.9 | 9 |
| 31 | Seedance | [Seedance 2.5 4K / Built for the Big Screen](https://youtu.be/5ymQgaSP03Q) | 20261023 | 276125 | 150 | 46 (46) | 3.26 | 130 | 8 | personnages | -15.2 | 9 |
| 32 | Seedance | [Dreamina Seedance 2.5 / ON CUE: A Seamless Circus Long Take](https://youtu.be/o2Hb2fsf_as) | 20260803 | 45374 | 123 | 18 (18) | 6.85 | 135 | 9 | personnages | -14.5 | 9 |
| 33 | Tripo | [Tripo P2.0 / Shape What You Imagine](https://youtu.be/CoB_B-EVEQE) | 20261031 | 6667 | 36 | 23 (23) | 1.57 | 115 | 8 | aucune | -11.6 | 9 |
| 34 | Vidu | [Meet Vidu Q4 Preview—our next-gen flagship AI video model](https://youtu.be/jJcbxCDRRaw) | 20261007 | 120644 | 65 | 32 (32) | 2.04 | 116 | 9 | aucune | -15.2 | 9 |
| 35 | Autodesk | [Introducing Autodesk Flow Studio (formerly Wonder Studio)](https://youtu.be/nEHCBPGo-5M) | 20230310 | 177521 | 128 | 9 (26) | 14.22 | 90 | 6 | voix off | -18.6 | 8 |
| 36 | Google | [Veo 3.1 - Designed to empower creatives](https://youtu.be/I06Ef8alr2Y) | 20251015 | 117495 | 90 | 18 (26) | 5.0 | 108 | 6 | voix off et personnages | -14.6 | 8 |
| 37 | Hedra | [Introducing Hedra Studio and Character-3](https://youtu.be/Ew7V75NO858) | 20250313 | 238 | 32 | 25 (25) | 1.29 | 115 | 8 | personnages | -17.6 | 8 |
| 38 | Higgsfield | [Kling 4.0 makes AI video look like a real film shoot](https://youtu.be/5fuQnUuu1BM) | 20261029 | 29311 | 36 | 10 (10) | 3.65 | 115 | 9 | aucune | -6.8 | 8 |
| 39 | Higgsfield | [Did We Have a Choice? / An AI Commercial Made With Claude + ](https://youtu.be/8-PM8Q4Z39M) | 20261026 | 13601 | 79 | 22 (22) | 3.6 | 95 | 6 | personnages | -16.3 | 8 |
| 40 | Higgsfield | [Higgsfield x Wan 3.0 Prime / Switch Between Animation Styles](https://youtu.be/9iytKvKluso) | 20261028 | 19611 | 41 | 21 (25) | 1.96 | 160 | 9 | personnages | -13.3 | 8 |
| 41 | Higgsfield | [Turn One Idea Into a Full Explainer Reel / Higgsfield Conten](https://youtu.be/Z-UFzX4lsjA) | 20261027 | 28531 | 75 | 41 (41) | 1.84 | 122 | 8 | présentateur | -14.5 | 8 |
| 42 | Higgsfield | [Can AI Beat VFX? (feat. ⁨⁨ErikDoesVFX)](https://youtu.be/uZkGA1EuIHI) | 20261005 | 144837 | 150 | 54 (54) | 2.78 | 108 | 6 | présentateur | -21.8 | 8 |
| 43 | LTX | [Eclipse Falls / AI Trailer / LTX Studio](https://youtu.be/S-JtjLOnE0g) | 20250130 | 41586 | 40 | 29 (28) | 1.36 | 110 | 8 | voix off | -11.5 | 8 |
| 44 | LTX | [LTX-2.5: The Open World Model the World Builds On](https://youtu.be/ZDfjZae7Da0) | 20260811 | 685272 | 124 | 56 (56) | 2.21 | 124 | 8 | voix off et intervenants (interviews) | -15.1 | 8 |
| 45 | Luma | [Travel between worlds made with Luma Agents](https://youtu.be/xKYHvD7XKdU) | 20260307 | 2590403 | 60 | 15 (15) | 4.01 | 90 | 8 | voix off | -11.5 | 8 |
| 46 | Meshy | [Introducing Meshy 3D Agent: The World's First AI Agent for 3](https://youtu.be/YwnwaCpRNGE) | 20260529 | 541930 | 71 | 42 (42) | 1.7 | 155 | 8 | aucune | -21.6 | 8 |
| 47 | MiniMax | [It's coming.](https://youtu.be/tyZF0V_ajNA) | 20260730 | 106356 | 60 | 37 (37) | 1.62 | 90 | 6 | aucune | -15.3 | 8 |
| 48 | Moonvalley | [Introducing Marey – The Most Powerful AI Video Model Trained](https://youtu.be/CNt-BJ46z7o) | 20250312 | 5874 | 63 | 57 (57) | 1.11 | 128 | 8 | aucune | -14.2 | 8 |
| 49 | OpenArt | [Say it and it’s made @openart_ai](https://youtu.be/7IbuYQkfd5I) | 20261101 | 1225 | 35 | 14 (15) | 2.51 | 110 | 7 | personnages | -15.5 | 8 |
| 50 | OpenArt | [Smart Shot: Stop paying for bad takes 😜](https://youtu.be/VEp8seauQv0) | 20261001 | 6699 | 35 | 7 (15) | 5.01 | 135 | 8 | personnages | -19.3 | 8 |
| 51 | Pika | [NO. MORE. COMPLICATED. PROMPTS.](https://youtu.be/8vmWDkMH-ec) | 20251006 | 2982 | 76 | 38 (38) | 1.99 | 128 | 8 | personnages | -11.2 | 8 |
| 52 | Runway | [Edit Anything with Aleph 2.0 / Runway](https://youtu.be/ZuLdYV9AjZ4) | 20260604 | 8406 | 31 | 15 (15) | 2.08 | 85 | 4 | aucune | -15.2 | 8 |
| 53 | Runway | [Create compositing mattes in seconds with Aleph 2.0](https://youtu.be/kBgZ94KzjIc) | 20260601 | 2765 | 56 | 27 (27) | 2.08 | 115 | 7 | voix off | -15.8 | 8 |
| 54 | Runway | [Introducing Runway Ads / Runway](https://youtu.be/yeRj7xGYUoM) | 20260930 | 7551 | 114 | 2 (45) | 57.13 | 128 | 8 | personnages | -19.2 | 8 |
| 55 | Seedance | [Introducing Draft Mode for Dreamina Seedance 2.5 / Draft Fas](https://youtu.be/3Kq9RhwH708) | 20260922 | 309560 | 22 | 1 (9) | 21.56 | 0 | 7 | personnages | -21.0 | 8 |
| 56 | Seedance | [Tom Tykwer’s Volcano High / Trailer](https://youtu.be/UkhUzKW7muM) | 20261023 | 95290 | 86 | 13 (13) | 6.65 | 115 | 8 | personnages | -15.3 | 8 |
| 57 | VFX | [Can AI Video Beat a VFX Artist?](https://youtu.be/UCV692sxr_Q) | 20250320 | 3243818 | 150 | 80 (80) | 1.88 | 124 | 8 | voix off | -15.1 | 8 |
| 58 | Freepik | [Green Screen vs Final Result: VFX Magic with Seedance 2.5 on](https://youtu.be/-0nqs_hTEOg) | 20260929 | 3742 | 28 | 6 (6) | 4.7 | 0 | 2 | personnages | -19.6 | 7 |
| 59 | Higgsfield | [The easiest way to make your videos look pro](https://youtu.be/xtkm45qzJko) | 20261028 | 54400 | 40 | 3 (3) | 13.34 | 110 | 6 | présentateur | -15.7 | 7 |
| 60 | Kling | [Create Hitchcock Zoom in Seconds 🎬 #klingai #kling #hitchcoc](https://youtu.be/Snp18Q0nE2Y) | 20260817 | 25749 | 20 | 6 (5) | 3.32 | 115 | 6 | aucune | -12.8 | 7 |
| 61 | Krea | [Alter your reality with Omni Flash. Try it now on krea.ai](https://youtu.be/mX1qvn1XCP8) | 20260811 | 1757 | 17 | 3 (3) | 5.64 | 118 | 6 | aucune | -18.8 | 7 |
| 62 | Meshy | [3D to Video: A New Way to Create Your Vision in Meshy](https://youtu.be/n4sT-Rb7LjU) | 20250904 | 3319738 | 53 | 12 (12) | 4.39 | 118 | 8 | aucune | -23.6 | 7 |
| 63 | OpenArt | [Turn 1 Ad Into 100: The AI Machine You Need for Scaling](https://youtu.be/l81KWJBzAFk) | 20261020 | 924735 | 150 | 29 (29) | 5.17 | 110 | 5 | présentateur | -14.3 | 7 |
| 64 | Tripo | [3D is the language of the world. And ours. Introducing Tripo](https://youtu.be/A3fViMX2JjQ) | 20261024 | 10898 | 80 | 9 (22) | 8.89 | 118 | 6 | aucune | -15.7 | 7 |
| 65 | Higgsfield | [How I Make AI Fight Scenes Actually Hit](https://youtu.be/jofpFg6W9ow) | 20261025 | 13707 | 34 | 11 (11) | 3.07 | 95 | 5 | présentateur | -14.7 | 6 |
| 66 | Krea | [Introducing K2: Krea’s First Foundation Model](https://youtu.be/L8LUeow2x5Y) | 20260520 | 947 | 110 | 48 (48) | 2.3 | 108 | 5 | présentateur | -13.1 | 6 |
| 67 | Meshy | [Meshy + Blender: Build a 3D Miniature Town Using Only AI-Gen](https://youtu.be/GLdFo1MFnWo) | 20260602 | 11162593 | 82 | 43 (15) | 1.91 | 118 | 7 | aucune | -10.6 | 6 |
| 68 | OpenAI | [Higgsfield takes AI video from 1 minute to over 10](https://youtu.be/inrYeej3Big) | 20261026 | 61347 | 86 | 33 (33) | 2.61 | 118 | 6 | présentateur | -19.4 | 6 |
| 69 | Higgsfield | [How to get the same AI face in every shot](https://youtu.be/MsxIRbuYmyU) | 20261026 | 67138 | 34 | 8 (8) | 4.25 | 95 | 3 | présentateur | -14.2 | 5 |
| 70 | OpenArt | [AI VFX For The Beginner or Pro!](https://youtu.be/P_uaf2HI92M) | 20260917 | 223974 | 150 | 51 (51) | 2.94 | 115 | 2 | présentateur | -21.7 | 5 |

## Annexe B — Corpus du lot 2 (mêmes colonnes)

| # | Marque | Vidéo (id) | Date | Vues | Durée s | Plans | s/plan | BPM | Énergie | Voix | LUFS | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Entreprise | [Tokens, the Building Blocks of AI / Official GTC 2026 Keynot](https://youtu.be/O-_-CEeFHCM) | 20260318 | 13997 | 150 | 64 (64) | 2.34 | 112 | 8 | voix off | -22.5 | 9 |
| 2 | Entreprise | [The Rise of AI: NVIDIA Live at CES 2026 Opening Video](https://youtu.be/d24W8AqeOHM) | 20260106 | 38840 | 150 | 58 (58) | 2.59 | 124 | 9 | personnages | -17.3 | 9 |
| 3 | Higgsfield | [Claude Opus 5.5 + Higgsfield Make Insane Motion Graphics! (C](https://youtu.be/5HYYXYYCrL4) | 20261013 | 358062 | 150 | 53 (53) | 2.83 | 122 | 8 | présentateur | -15.4 | 9 |
| 4 | Higgsfield | [This AI Movie Trailer Looks Insane… / ALRIGHT (2027) — made ](https://youtu.be/kvXojaSEDM4) | 20260217 | 1219 | 61 | 51 (51) | 1.2 | 130 | 9 | personnages | -13.3 | 9 |
| 5 | Luma | [Ray3 Modify is now available. Your vision. Your performance,](https://youtu.be/BoM25iSp_V4) | 20251218 | 2753 | 44 | 16 (22) | 2.73 | 130 | 9 | aucune | -7.9 | 9 |
| 6 | Runway | [Introducing Solaris our first Interface World Model / Runway](https://youtu.be/c2yCePPnrSA) | 20260831 | 66396 | 83 | 28 (28) | 2.95 | 112 | 5 | voix off | -24.8 | 9 |
| 7 | VFX-viral | [Seedance 2.0 Created This Superhero Suit-Up in Seconds 🤯 / A](https://youtu.be/Vd1H80XqBho) | 20260226 | 1011 | 15 | 9 (9) | 1.64 | 145 | 9 | personnages | -6.9 | 9 |
| 8 | VFX-viral | [100% AI Generated Dragon POV / Seedance 2.0 Cinematic VFX Te](https://youtu.be/nE_q54w6BZw) | 20260825 | 924 | 29 | 21 (1) | 1.37 | 130 | 8 | personnages | -18.8 | 9 |
| 9 | VFX-viral | [Breakfast, Interrupted — Time Freeze VFX with Seedance 2.5](https://youtu.be/w4wqR0L7V6A) | 20260813 | 23925 | 30 | 2 (1) | 15.01 | 85 | 6 | personnages | -23.2 | 9 |
| 10 | Entreprise | [AX 기술로, 미래를 선명하게 / LG U+ Enterprise 브랜드필름 30s ver](https://youtu.be/028R5_G0qno) | 20261030 | 646045 | 30 | 34 (34) | 0.88 | 124 | 8 | voix off | -9.0 | 8 |
| 11 | Entreprise | [The Rise of the Agentic Enterprise / Salesforce Agentforce](https://youtu.be/Ad5NUrYD9yc) | 20260207 | 7539 | 60 | 75 (75) | 0.8 | 120 | 8 | voix off | -24.1 | 8 |
| 12 | Entreprise | [Official Keynote Opening Video / NVIDIA GTC Berlin 2026](https://youtu.be/VsZpy3aFLeY) | 20261021 | 25004 | 150 | 44 (46) | 3.41 | 96 | 7 | voix off | -24.3 | 8 |
| 13 | Entreprise | [I Am AI / NVIDIA GTC 2024 / Official Keynote Intro](https://youtu.be/jMW8_YVFgzY) | 20240319 | 122420 | 150 | 25 (35) | 6.0 | 110 | 7 | voix off | -20.1 | 8 |
| 14 | Entreprise | [There are many futures. Which do you want to build?](https://youtu.be/o4D1J1YWjhg) | 20261030 | 121689 | 77 | 37 (18) | 2.08 | 128 | 6 | aucune | -14.8 | 8 |
| 15 | Entreprise | [GPT-6.1 Terra is now in orbit](https://youtu.be/tTuk4pGnT0A) | 20261026 | 523804 | 31 | 4 (7) | 7.87 | 122 | 8 | aucune | -16.0 | 8 |
| 16 | LTX | [How I Made Crazy Macro Shots in Seconds!](https://youtu.be/N_jrBqhGorI) | 20250930 | 183115 | 70 | 56 (56) | 1.25 | 130 | 7 | voix off | -19.2 | 8 |
| 17 | OpenArt | [“Storm” Viral Preset Available](https://youtu.be/3eUbF8l2prg) | 20260921 | 4228 | 23 | 5 (4) | 4.61 | 115 | 8 | aucune | -19.4 | 8 |
| 18 | Tripo | [Why is my head so brittle？](https://youtu.be/DYVVOiGYeiM) | 20261028 | 574055 | 52 | 63 (62) | 0.82 | 140 | 7 | voix off | -8.0 | 8 |
| 19 | VFX-viral | [Did AI Just Change Movies Forever?](https://youtu.be/BRESQ8NX-us) | 20260807 | 8838770 | 150 | 48 (48) | 3.13 | 125 | 8 | présentateur | -13.7 | 8 |
| 20 | VFX-viral | [End of Humanity / Short AI Film](https://youtu.be/VBlxAP8hGZ8) | 20261011 | 3286231 | 150 | 44 (44) | 3.41 | 75 | 6 | aucune | -11.4 | 8 |
| 21 | VFX-viral | [FIFA World Cup 2026  / Cinematic AI Trailer / Made with Goog](https://youtu.be/Xcmge73Mkr0) | 20260703 | 7193 | 128 | 50 (50) | 2.56 | 128 | 9 | aucune | -15.3 | 8 |
| 22 | VFX-viral | [Did AI Just Kill VFX?](https://youtu.be/eIq1uw8q3dE) | 20260605 | 1846668 | 150 | 86 (86) | 1.74 | 125 | 8 | présentateur | -13.6 | 8 |
| 23 | VFX-viral | [Is AI The New VFX?](https://youtu.be/jfGVMfle07g) | 20261003 | 1382911 | 150 | 66 (65) | 2.27 | 125 | 8 | présentateur | -13.0 | 8 |
| 24 | VFX-viral | [Yoda vs Vader: The Duel That Never Was (AI Generated)](https://youtu.be/vSBmAeKZ5nw) | 20250621 | 108445 | 72 | 21 (21) | 3.45 | 130 | 9 | personnages | -18.4 | 8 |
| 25 | Runway | [Introducing Praxis-1 / Runway](https://youtu.be/sXiLq_3TaAI) | 20260930 | 12844 | 115 | 57 (57) | 2.01 | 95 | 4 | voix off | -15.9 | 7 |
| 26 | Tripo | [3D prints are too fragile!](https://youtu.be/VgHscVzMOXo) | 20261009 | 883161 | 29 | 34 (34) | 0.86 | 130 | 6 | voix off | -13.7 | 7 |
| 27 | VFX-viral | [GRANNY MOVIE Trailer (2026) Concept](https://youtu.be/LDmrS2BUBfI) | 20260630 | 4121914 | 61 | 40 (40) | 1.52 | 110 | 9 | personnages | -15.6 | 7 |
| 28 | VFX-viral | [Medusa: Cursed Beauty (2026) - Angelina Jolie, Jason Momoa /](https://youtu.be/RXYMizkPhAk) | 20260131 | 1338258 | 99 | 44 (44) | 2.25 | 90 | 8 | voix off et personnages | -9.4 | 7 |
| 29 | Runway | [Introducing Continuum: A Real-Time Video Operating System / ](https://youtu.be/K7Q7FESRHJY) | 20261001 | 109494 | 150 | 9 (9) | 16.67 | 95 | 3 | voix off | -14.1 | 6 |
| 30 | Seedance | [Dreamina Seedance 2.0: Video Editing](https://youtu.be/MgQlW5IhXjc) | 20260605 | 5179 | 46 | 5 (6) | 9.16 | 130 | 6 | aucune | -14.6 | 6 |
| 31 | VFX-viral | [STAR WARS: DARK FORCES Amazing Lightsaber Fight! Jaina Solo ](https://youtu.be/lHbSPoyeegI) | 20260827 | 84054 | 142 | 296 (296) | 0.48 | 140 | 9 | personnages | -14.3 | 6 |
