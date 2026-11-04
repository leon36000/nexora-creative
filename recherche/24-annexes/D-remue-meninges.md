# 24-D — Remue-méninges brut (03/11/2026)

Même consigne pour les deux modèles (dossier de départ résumé dans le §10 du rapport 24). Réponses non filtrées : ce qui a été retenu et écarté est dans `../24-etat-de-lart-creative-2026-11.md` §10.

## Gemini 4 Argon (OpenRouter, effort élevé, 0,083 USD)

Voici ma contribution au remue-méninges produit. Pas de langue de bois : à 2,4/5 à l’audit interne et avec seulement quatre GPU locaux, nous mourrons si nous jouons au supermarché de modèles contre Higgsfield. Notre arme absolue, c’est le **couplage entre un coût marginal ridicule (0,005 $/s), le Producteur à devis déterministe et une vraie sortie post-production (ProRes 4444 / XML / PDF fond perdu)**.

---

### 1. Positionnement et les 3 preuves en moins de 3 minutes

**La phrase de positionnement :**
> **« Décrivez votre idée, validez le devis en centimes et obtenez un film monté en 60 secondes — ou ouvrez le capot multipiste ProRes que les studios facturent 10 000 $. »**

**Les 3 preuves produit (< 180 secondes pour un débutant) :**
1. **0:00 à 1:15 — Le choc du Producteur à devis franc :** L’utilisateur tape *« Pub nerveuse de 15 s pour ma brûlerie de café à Montréal avec @Julie »* et glisse un égoportrait. Le code affiche un devis ferme : **0,09 $ CAD**. Un clic : scénario, 6 plans synchronisés à 125 BPM (avec arrêt net de la musique avant le plan final), même visage sur chaque plan, juge visuel qui élimine les mains tordues.
2. **1:15 à 2:10 — La retouche chirurgicale sans graphe :** Dans la timeline, un détail cloche. Clic droit sur le plan 3 → bulle *« Effet IA ici : détoure Julie et mets un mur de briques flou derrière »*. SAM 2.1 + ViTMatte crée la couche alpha 16 bits en 8 secondes, annulable par un simple `Ctrl+Z`.
3. **2:10 à 2:55 — Le livrable d’agence omnicanal :** En un seul clic d’export, l’utilisateur télécharge la vidéo 16:9, sa déclinaison 9:16 ET le dépliant PDF vectoriel avec fond perdu prêt pour l’imprimeur (mode Marketing) reprenant la même direction artistique. Aucun concurrent ne relie vidéo IA et imprimé pro.

---

### 2. Le Top 10 pour dépasser Higgsfield et OpenArt (Impact ÷ Effort)

*Règle : assemblage de briques à poids ouverts uniquement, zéro entraînement lourd.*

| Rang | Fonctionnalité | Ce que voit l'utilisateur | Brique technique à assembler | Ce qui ferait échouer |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Bascule sur Pika H3 Flex (Sorti il y a 5 jours)** | Brouillon en **3,5 s** (au lieu de 28,7 s), finale en **35 s** (au lieu de 290 s), plans jusqu'à 15 s. `[Hypothèse : gain 8x linéaire avec le passage de 50 à 6 étapes]` | Chargement des adaptateurs LoRA Pika H3 Flex (FL2VA/Ref2VA) directement sur notre pipeline MiniMax H3 existant. | Dégradation de la piste audio native de H3 à 6 étapes (nécessiterait de garder Music3/Foley séparé). |
| **2** | **Gabarit « Promo Gagnante » (Ad Multiplier)** | Un bouton *« Format Pub Virale »* qui applique automatiquement les règles des 101 promos : accroche < 1 s, coupe/2 s, 120 BPM, coupure sèche avant révélation, écran scindé avant/après. | Règles codées en dur dans l'`EditPlan` typé + détection de transitoires audio (`librosa`) sur MiniMax-Music3. | Rendu trop mécanique si l'utilisateur l'utilise 10 fois de suite (prévoir 8 variantes rythmiques). |
| **3** | **Recadrage 9:16 intelligent (Auto-Reframe)** | Case à cocher *« Décliner en TikTok/Reels »* à l'export : le sujet reste toujours cadré sans couper les visages ni les sous-titres. | Suivi de centroïde via **YOLOv11 + SAM 2.1** (déjà installé) converti en courbes de Bézier X/Y dans la timeline FreeCut. | Mouvements de caméra virtuels trop brusques (il faut un filtre de Kalman pour amortir l'inertie). |
| **4** | **Clonage de montage par référence (« Katana »)** | L'utilisateur glisse une vidéo TikTok qu'il adore : Creative extrait le rythme, les angles et remplace chaque plan par les produits/personnages de l'utilisateur. | **PySceneDetect** + **Qwen2.5-VL** (analyse plan par plan sur les Turing 8 Go) → génération directe d'un `EditPlan` JSON. | Latence d'analyse si la vidéo source dépasse 60 s (bloquer à 30 s max). |
| **5** | **Agrandissement 4K + 60 ips** | Bouton *« Master 4K »* sur la timeline ou par plan (passe de 1344×768 à 3840×2160 net, sans scintillement). | **FlashVSR** ou **Real-ESRGAN + RIFE** compilés en TensorRT sur les deux RTX Turing 8 Go (décharge la 5090). | Texture « plastique » sur les peaux (injecter un grain de pellicule 35 mm WebGPU par-dessus). |
| **6** | **MCP distant (SSE) + Skills Claude/ChatGPT** | L'utilisateur pilote son studio depuis Claude Desktop ou ChatGPT : *« Fais-moi 3 variantes de pub avec le kit de marque @Nexora »*. | Encapsuler nos 22 outils MCP `stdio` derrière un serveur **FastAPI SSE + OAuth2** avec validation de devis par lien cliquable. | Saturation de nos GPU par des boucles d'agents externes (imposer un plafond de dépenses par session MCP). |
| **7** | **Voix persistante & Lip-Sync (« Intone »)** | L'acteur `@Personnage` parle en français (avec accent québécois ou international) sur un fichier audio fourni ou généré, lèvres parfaitement synchronisées. | **F5-TTS** (ou Fish-Speech 1.5) pour le clonage vocal + **LatentSync** (ou Hallo3) en post-passe sur le visage détecté. | Désynchronisation entre l'audio natif généré par H3 et la voix plaquée (muter la voix H3, garder seulement l'ambiance H3). |
| **8** | **Rééclairage 2.5D en timeline (« SwitchX »)** | Dans la bulle clic droit : *« Ajoute un néon rouge à gauche du visage »* avec une sphère lumineuse interactive dans le canevas. | **Depth-Anything-V2** + **NormalCrafter** → calcul d'éclairage PBR en temps réel dans un shader **WebGPU** + passe **IC-Light v2** au rendu. | Incohérence temporelle des normales sur les cheveux (utiliser le masque alpha 16 bits de ViTMatte pour isoler). |
| **9** | **Édition vidéo v2v (Retrait d'objet / Restyle)** | L'utilisateur peint grossièrement une voiture en arrière-plan → elle disparaît ou devient une calèche sur toute la durée du plan. | Masque **SAM 2.1** (déjà là) envoyé dans **ProPainter** (retrait pur) ou **Wan-2.1/H3 VACE Inpainting** (remplacement). | Explosion de VRAM au-delà de 80 frames en 1344×768 (découper en fenêtres glissantes sur le GB10 128 Go). |
| **10** | **Lien de révision client (Collaboration légère)** | Un bouton *« Partager au client »* génère une URL privée où le client clique sur la vidéo à 0:04s pour écrire *« Change la musique ici »*, ce qui apparaît dans la timeline. | Lecteur web léger + base SQLite/Postgres mappant les commentaires aux marqueurs temporels d'`EditPlan`. | Tenter de faire du montage simultané multi-utilisateurs façon Figma (beaucoup trop lourd, inutile). |

---

### 3. Ce qu'il faut REFUSER de faire (Pièges mortels)

1. **Devenir un agrégateur d’API payantes (Kling 4.0, Seedance 2.5, Luma) :** C'est le piège n°1. Dès qu'on revend une API à 0,57 $/s, notre marge brute s'effondre, notre système de devis à quelques centimes devient mensonger et la cohérence visuelle entre les plans d'un même film disparaît. Restons 100 % souverains sur nos GPU avec H3 + Pika H3 Flex.
2. **Construire un réseau social interne ou des concours communautaires :** À notre taille, une galerie communautaire a l'air d'un centre commercial abandonné. C'est un gouffre de modération (NSFW, droits d'auteur) qui dilue l'image d'outil professionnel.
3. **Les « Mondes 3D jouables » (façon OpenArt Worlds) :** Gadget complet pour 99 % des créateurs vidéo. Gardons TRELLIS.2 strictement pour générer des accessoires/produits 3D à intégrer dans nos vidéos ou à imprimer.
4. **L'entraînement de LoRA personnalisés par l'utilisateur :** Ne laissez jamais un client lancer un fine-tuning sur notre RTX 5090. Ça monopolise la carte pendant 40 minutes pour un seul client et génère du support client infini. Notre système `@Personnage` (Qwen → H3 Ref2VA sans entraînement) suffit largement.

---

### 4. Stratégie de prix : tuer le « crédit » opaque

Avec Pika H3 Flex (6 étapes), notre coût réel (électricité à 0,11 $ CAD/kWh + amortissement) descend à **~0,002 $ – 0,004 $ USD/s** `[Hypothèse basée sur une division par 6 du temps GPU]`. Mais attention : avec 1× 5090 et 1× GB10, notre capacité maximale est d'environ **2 500 secondes de vidéo finale par heure** `[Hypothèse]`. Si on casse les prix en API sèche contre Pika (0,035 $/s), des développeurs vont saturer nos 2 gros GPU en 10 minutes sans aucune fidélité.

**Notre modèle : Zéro « crédit » incompréhensible. Devis en vrais dollars + Abonnement logiciel.**

* **Gratuit (Produit d'appel à coût GPU nul) :**
  * Mode Studio (timeline, 52 effets WebGPU, montage manuel) **100 % gratuit et illimité** (tourne sur le GPU du navigateur client !).
  * **1,00 $ de portefeuille offert** à l'inscription (= ~25 secondes de vidéo brouillon générée par le Producteur IA, soit 2 mini-films complets pour tester les 3 preuves en 3 minutes). Export 720p avec discret filigrane.
* **Tarification à la carte (au devis validé) :**
  * **Mode Brouillon (Pika H3 Flex 6 étapes) :** **0,04 $ USD / seconde** (marge brute > 90 %). Un film de 15 s coûte **0,60 $**.
  * **Mode Master (H3 50 étapes ou Flex + Upscale 4K) :** **0,12 $ USD / seconde** (6x moins cher que Higgsfield à 0,78 $/s, marge brute ~85 %).
* **Ce qui justifie l'abonnement mensuel « Studio Pro » à 29 $ USD/mois (39 $ CAD) :**
  * Inclut **15 $ USD** de budget de production mensuel rechargeable.
  * Débloque les **livrables d'agence** : exports ProRes 4444 / EXR 16 bits, FCP7 XML, PDF fond perdu (mode Marketing), absence de filigrane, file prioritaire sur la RTX 5090 (vs GB10) et accès au MCP distant.

---

### 5. Intégration Blender pilotée par l'agent : indispensable pour le « Triple A » ?

**NON. C'est un mirage d'ingénieur.**
Faire écrire du code Python (`bpy`) à un LLM dans un Blender sans tête échoue spatialement ~40 % du temps `[Hypothèse]` (objets qui s'interpénètrent, caméras à l'envers), prend 15 secondes à rendre par essai et terrorise le commun des mortels. Quant aux vrais artistes 3D, ils ont déjà Blender ouvert sur leur propre machine et exporteront nos fichiers `.GLB/.USDZ` (TRELLIS.2) et `.EXR` (SAM 2.1).

**Ce qu'il faut faire à la place :** Intégrer une **scène 3D légère en Three.js / WebGPU directement dans le canevas de la timeline**. L'utilisateur (ou l'agent via JSON typé) pose son objet TRELLIS.2, tourne autour à la souris à 60 ips, et le navigateur extrait instantanément la carte de profondeur (Depth) et le contour pour guider H3. C'est 100 fois plus rapide, déterministe, visuel, et ça consomme 0 % de nos GPU serveurs.

---

### 6. Les 5 règles concrètes d'une interface « Triple A »

Pour passer de 2,4/5 à 4,5/5 face à CapCut (3,3) :

1. **Séparation radicale à 2 vitesses (Zéro surcharge cognitive) :** Le *Mode Producteur* ne doit contenir AUCUNE piste audio, aucun keyframe, aucun jargon : juste le scénario, les cartes de plans illustrées, le bouton de re-tirage et le devis en dollars. Un bouton **« Ouvrir dans le Studio (Avancé) »** bascule vers la timeline FreeCut sombre (`#0D0D0F`, bordures `1px solid #222`).
2. **Règle des 16 millisecondes (60 ips sacrés) :** Le curseur de lecture de la timeline ne doit jamais saccader. Dès qu'un plan H3 ou un détourage SAM 2.1 est généré, le navigateur ou une carte Turing encode un proxy WebCodecs léger en tâche de fond.
3. **Interdiction des champs texte vides (Presets vidéo au survol) :** Le commun des mortels ne sait pas écrire un prompt de caméra. Chaque paramètre (mouvement, éclairage, style, rythme) doit être une vignette vidéo qui s'anime en boucle au survol de la souris, générée une fois pour toutes sur nos serveurs.
4. **Le « Rideau Avant/Après » universel :** Chaque opération IA (bulle clic droit, détourage 16 bits, juge visuel à 2 prises, upscale 4K) doit afficher un séparateur vertical glissant en temps réel sur le lecteur vidéo pour prouver visuellement la valeur ajoutée.
5. **Télémétrie rassurante en direct :** Au lieu d'un sablier muet pendant 35 secondes, afficher le décodage latent étape par étape (les 6 étapes de Pika H3 Flex envoyées en WebSocket sous forme d'images floues qui deviennent nettes) accompagné du ticket de caisse : `RTX 5090 • Étape 4/6 • Coût verrouillé : 0,06 $`.

---

### 7. L'idée la plus audacieuse : « Le Quart de Nuit » (Agence Autonome en Heures Creuses)

Notre contrainte physique (4 GPU auto-hébergés au Québec, électricité à 0,11 $ CAD/kWh) est en réalité notre plus grand levier marketing si on l'inverse. Entre **1 h 00 et 6 h 00 du matin**, nos GPU dorment alors qu'ils sont déjà amortis.

**Le concept :** Un commutateur dans le Kit de Marque appelé **« Producteur de Nuit »**.
L'utilisateur (une PME, un créateur, un commerce en ligne) connecte son catalogue produit ou son flux RSS et fixe un plafond de **0,50 $/nuit**. Chaque nuit, pendant que les GPU sont libres, le Producteur IA regarde les tendances, génère **sans qu'on lui demande** une vidéo promo complète de 15 s (prête avec les règles des 101 promos) + le visuel imprimable assorti.

À 7 h 30 chaque matin, l'utilisateur reçoit un courriel : *« Bonjour ! Cette nuit, votre studio a tourné cette publicité pour votre nouveau produit (coût : 0,14 $). Cliquez ici pour la publier en 9:16 ou la modifier. »*
**Impact :** On transforme un outil passif (où l'utilisateur a le syndrome de la page blanche) en un employé créatif proactif qui lisse à 100 % la charge de nos serveurs sur 24 heures. Personne sur le marché ne peut copier ça avec des API tierces coûteuses.
## GPT-6.1 Sol (Codex, effort élevé, sans recherche web)

**Ma décision : viser les petites entreprises et créateurs francophones qui veulent publier régulièrement.** Dépasser Higgsfield et OpenArt sur ce travail précis est crédible. Les dépasser sur toutes leurs fonctions disperserait Creative.

Je prends votre dossier comme référence. Les efforts, prix et objectifs ci-dessous sont des **hypothèses à valider**.

**1. « Votre idée devient un film prêt à publier, et vous gardez la main sur chaque détail. »**

Trois preuves, dans un parcours débutant de moins de trois minutes :

- **0–25 s : comprendre sans apprendre.** « Une pub pour ma boulangerie, chaleureuse, avec @Julie. » Creative montre les plans proposés, les ingrédients et le prix total. Un seul bouton : « Produire ».
- **25–90 s : voir sa propre idée prendre vie.** Premier plan en brouillon, personnage reconnaissable, son audible. Montrer les références à côté du résultat. Vos 28,7 secondes rendent cette preuve plausible pour **un plan**, sans promettre tout le film.
- **90–180 s : exercer un vrai contrôle.** « Le titre plus gros, une ambiance plus chaude. » Modification visible dans Studio, comparaison, Ctrl+Z, export du brouillon.

Le master peut terminer ensuite. Ne promettez pas un film complet en trois minutes avant d’avoir mesuré ce délai chez les débutants, attente GPU comprise.

**2. Les dix ajouts, classés par impact utilisateur ÷ effort.**

Impact sur 5 ; effort en **semaines-personne**, pour une première version exploitable. Ces estimations supposent la réutilisation de votre infrastructure ; les ratios servent à décider, pas à prédire précisément.

| Rang, ratio | Ce que voit l’utilisateur | Brique technique | Ce qui ferait échouer |
|---|---|---|---|
| **1 — 5/1** | **20 recettes complètes** : annonce restaurant, produit, événement, témoignage. Exemple animé et champs simples. | EditPlan paramétré, références, musique et cartons éprouvés. | De beaux exemples impossibles à reproduire avec ses propres ingrédients. |
| **2 — 5/2** | **Un projet, trois formats** : vertical, carré, horizontal ; sous-titres bien placés. | Suivi sujet avec SAM, trajectoire de recadrage lissée, transcription et zones réservées aux textes. | Visage coupé, caméra qui tremble, texte masqué. Prévoir un ajustement manuel. |
| **3 — 4/2** | **Ma voix, mon texte, mon accent.** Audio fourni ou voix off, prononciations mémorisées. | Import audio, alignement temporel, TTS local sélectionné après écoute en français québécois. | Accent français imposé, noms locaux mal prononcés, voix différente entre plans. |
| **4 — 5/3** | **Davantage d’essais pendant la même séance.** | Évaluer H3 Flex, puis intégrer seulement les modes validés ; modèles maintenus en mémoire, cache et ordonnancement. | Transformer « 6 étapes contre 50 » en promesse de vitesse ×8. Mesurer temps total, mémoire, son et fidélité des références. |
| **5 — 4/3** | **« Change seulement le deuxième plan. »** Le reste demeure intact et le supplément est annoncé. | Comparaison d’EditPlan, dépendances entre ressources, invalidation minimale du cache. | Une correction locale régénère le film ou change le personnage. C’est plus large que votre bulle d’effets actuelle. |
| **6 — 3/3** | **Creative dans Claude, ChatGPT et les automatisations.** Même projet et même devis partout. | API publique, MCP distant, authentification, tâches asynchrones, opérations idempotentes, plafond de dépense. | Double facturation, tâches perdues, prix différent entre interfaces. Réutiliser les 22 outils. |
| **7 — 5/6** | **« Fais-lui dire cet enregistrement. »** Identité et voix persistantes. | Banc d’essai de synchronisation labiale, dont [MuseTalk](https://github.com/TMElyralab/MuseTalk), puis raccord audio et contrôle visage. | Bouche artificielle, profils inutilisables, mauvaise synchronisation. Commencer par des visages de face. |
| **8 — 3/4** | **Une finale plus propre en 1080p**, avec comparaison à 100 %. | Agrandissement temporel, traitement par tuiles et détection du scintillement. | Inventer des détails sur le produit ou présenter un agrandissement comme du 1080p natif. |
| **9 — 3/5** | **« Voici la version à approuver. »** Commentaires au bon instant, versions comparables, validation client. | Liens privés, annotations temporelles, permissions et instantanés immuables. | Le commentaire vise une version qui a changé. Reporter le montage simultané. |
| **10 — 5/10** | **Réparer une vidéo existante**, d’abord retirer un objet dans un plan court. | SAM + candidat d’édition masquée tel que [VACE](https://github.com/ali-vilab/VACE), puis recomposition. | Scintillement, ombres restantes, décor déformé. Ne pas lancer simultanément retrait, restyle et relight. |

**Ordre d’exécution : 1–4, puis 5–6.** Les autres passent par des essais techniques avant engagement produit. Une fonction libre n’est pas une intégration gratuite.

Critère de victoire proposé : **8 débutants sur 10 obtiennent un premier brouillon utilisable sans assistance en trois minutes**. Ensuite, comparer à l’aveugle les résultats des trois plateformes sur les mêmes briefs. Votre moyenne de 35 variables ne remplace pas cette épreuve.

**3. Ce qu’il faut refuser.**

- **La collection de modèles.** Ajouter un moteur seulement s’il débloque une tâche importante que H3 échoue régulièrement.
- **Des centaines de presets.** Vingt recettes fiables valent davantage qu’un catalogue intimidant.
- **Communauté, concours et réseau social maintenant.** Ils exigent animation et distribution, pas seulement du code.
- **Le montage professionnel exhaustif.** Consolider Studio et les exports ; préserver le temps consacré au Producteur.
- **L’illimité GPU.** Il vend une capacité que votre parc ne possède pas.
- **Les longs plans comme objectif autonome.** Un bon film de 30 secondes peut comporter quinze plans. La durée continue doit répondre à un besoin narratif.

**4. Prix : vendre un résultat contrôlable, avec un compteur compréhensible.**

**Proposition en CAD, hors taxes :**

- Brouillon : **0,02 $/seconde**.
- Finale : **0,10 $/seconde retenue**, avec deux prises et sélection comprises dans le devis.
- Chaque essai supplémentaire choisi par l’utilisateur : prix annoncé avant lancement.
- Exporter plusieurs formats à partir des mêmes prises : inclus lorsque cela nécessite seulement montage, recadrage et encodage.

Ainsi, **30 secondes finales coûtent 3 $**, hors brouillons et options explicitement chiffrées. Les travaux spécialisés ont leur propre devis.

Gratuit : scénarisation raisonnablement plafonnée, montage de médias importés, consultation des projets et **10 secondes de brouillon à l’inscription**, sans recharge quotidienne automatique.

**Forfait Créateur : 29 $/mois, 150 secondes finales incluses**, plusieurs kits de marque, traitements par lots et file prioritaire encadrée. Le forfait achète la récurrence et l’organisation ; le paiement ponctuel reste disponible.

Si vos coûts estimés sont bien en CAD, 0,10 $ contre 0,005–0,02 $ laisse **80–95 % avant hébergement, paiement, soutien, développement et sous-utilisation**. Ce n’est pas une marge nette.

Avant publication du tarif : mesurer 100 commandes, reprises comprises, et le coût par seconde **retenue**. Comparer les concurrents à devise, résolution, son et politique de reprises identiques. Votre sortie native 1344×768 ne se compare pas directement à leur 1080p.

**5. Blender piloté par agent : non, pas indispensable au niveau triple A.**

Il devient stratégique pour les packshots exacts, éclairages reproductibles, rotations produit et mouvements de caméra déterministes.

Commencer alors par **cinq opérations bornées**, exécutées par scripts en arrière-plan — mode prévu par [Blender](https://docs.blender.org/api/5.1/info_tips_and_tricks.html). Chaque opération produit un aperçu et un fichier récupérable.

Un agent libre de manipuler tout Blender créerait surtout une nouvelle surface de panne. La finition triple A vient d’abord de la fiabilité du parcours.

**6. Cinq règles d’interface triple A.**

1. **Le résultat domine :** aperçu occupant environ 60 % de l’espace, une action principale, paramètres avancés repliés.
2. **Chaque attente est lisible :** état réel, fourchette de délai, coût engagé, annulation et reprise après fermeture.
3. **Chaque action se comporte pareil :** sélection, raccourcis, annulation, glisser-déposer et menus cohérents partout.
4. **Chaque comparaison est honnête :** même cadrage, même instant, son synchronisé ; avant/après accessible immédiatement.
5. **La finition est systématique :** grille de 8 px, trois niveaux typographiques, contraste accessible, navigation clavier et animations discrètes. Aucun panneau ne saute pendant le chargement.

**7. Mon pari le plus audacieux : le film devient un document vivant.**

Le commerçant relie prix, horaires et disponibilité à son catalogue. Une rupture de stock retire le produit ; une promotion change le carton ; Creative recalcule uniquement les éléments concernés et soumet la nouvelle version à validation.

Techniquement : plans approuvés immuables, données structurées, règles de composition et rendu incrémental. **Hypothèse :** cela pourrait justifier davantage un abonnement que des secondes moins chères.

Le premier prototype tient dans une offre concrète : **une publicité approuvée, actualisée pendant un mois sans refaire le tournage.**