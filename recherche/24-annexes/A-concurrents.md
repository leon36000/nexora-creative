> Annexe du rapport `recherche/24-etat-de-lart-creative-2026-11.md`. Rapport délégué (GPT-6.1 Sol, effort élevé, Codex avec recherche web, 03/11/2026), conservé tel quel. Contrôle par Claude Opus 5.5 : 79/79 titres arXiv identiques à arxiv.org, 83/85 dépôts GitHub existants (SongBloom 404, une URL mal extraite), quatre affirmations recoupées à la main (voir §12 du rapport 24). Les chiffres non recoupés restent ceux des sources citées.

# Concurrents de Nexora Creative — état au 3 novembre 2026

Rapport produit pour un studio vidéo, image et 3D francophone au Québec. **Consultations effectuées le 3 novembre 2026.** Les dates de lancement sont distinguées des dates de consultation. Les prix sont en dollars américains, hors taxes, sauf devise expressément indiquée.

## Périmètre et méthode

Les trois sections demandées ont été lues en premier, en lecture seule : `07-creative-vs-higgsfield-feuille-de-route.md` §3, `12-higgsfield-videos-analyse.md` §3 et `FEUILLE-DE-ROUTE-MAITRE.md` §1. Elles servent à éviter une nouvelle feuille de route et à identifier les affirmations à recontrôler ; elles ne servent pas de preuves sur les concurrents.

Ce rapport repose sur les pages officielles effectivement ouvertes : tarifs, documentation, changelogs et annonces des éditeurs. Les extraits des moteurs de recherche ont servi à découvrir les pages ; **un extrait plus riche que la page ouverte n'a pas été utilisé pour combler ses lacunes**. Un catalogue commercial ne prouve pas à lui seul que chaque modèle peut encore être exécuté. Aucun abonnement, compte payant ou rendu n'a été acheté ou testé.

Les notes de bas de page donnent l'URL exacte ouverte et la date de consultation pour les chiffres et les fonctions. **« Non vérifié » signifie que les pages accessibles ne permettent pas de conclure**, pas que la fonction est absente. Les observations d'ergonomie sont des déductions des parcours documentés, pas des résultats d'un test utilisateur. Une promesse de fidélité ou de qualité reste une affirmation de l'éditeur.

### Comment lire les coûts

- Référence : modèle phare identifié dans chaque fiche, génération sans vidéo d'entrée, une seule sortie, audio lorsqu'il fait partie du modèle. Cible : 1080p ; une autre résolution est indiquée explicitement lorsque c'est le seul palier chiffrable ou le palier pertinent du modèle.
- Abonnement : `crédits par génération ÷ secondes × (prix du plan ÷ crédits inclus)`. C'est une **allocation théorique du forfait**, en consommant tous les crédits sur ce seul usage. Ce n'est pas un prix marginal à l'achat de secondes. Crédits inutilisés, échecs créatifs, images préparatoires, voix séparées et montage augmentent le coût réel.
- API : les crédits API ne sont jamais assimilés aux crédits de l'application. Quand l'API facture directement en dollars, on conserve son unité réelle ; on ne crée pas de faux crédits.
- Base principale : facturation mensuelle récurrente. L'annuel est un engagement distinct, précisé lorsqu'il est disponible. Une promotion est identifiée ; une hypothèse ne devient pas un tarif vérifié.
- Un brouillon 720p ne remplace pas un prix 1080p introuvable. Les exemples de brouillon sont exclus du classement principal. Une animation 3D ou une seconde de mocap ne devient pas une seconde de génération vidéo.

## Les vingt fiches

### 1. Higgsfield

**Modèles et date.** **DoP**, présenté comme modèle image→vidéo propriétaire, apparaît sous « Higgsfield Standard » ; sa version numérotée et sa date de lancement restent **non vérifiées**. Son guide est daté du **2 août 2026**, ce qui ne prouve pas une date de sortie. **Cinema Studio 4.0 utilise Seedance 2.5**, selon l’aide officielle : c’est un espace de réalisation. Le changelog date Cinema 4.0 du **12 août 2026**, le catalogue API du **18 septembre 2026** ; ces dates couvrent des périmètres différents. Autres tiers listés : Seedance 2.0, Kling 4.0/3.0, MiniMax H3, Wan 3.0, LTX 2.5 et Grok Imagine.[^HF8][^HF9][^HF1][^HF4][^HF5]

**Fonctions.** Presets visuels de caméra ; Elements et personnages réutilisables ; séquences multi-plans ; Genjutsu pour motion transfer, remplacement et restyle. Intone ajoute les personnages parlants avec voix persistante ; TTS, changement de voix et traduction avec lip-sync sont documentés. Supercomputer, Canvas, MCP et plugin ChatGPT élargissent le parcours. 3D et assemblage automatique existent dans certaines expériences ; une timeline multipiste générale reste **non vérifiée**.[^HF1][^HF6][^HF7]

**Ergonomie.** Vignettes de mouvements, références appelées par `@`, paramètres laissables sur Auto. Lourdeur déduite : profusion d'espaces et de moteurs ; paramètres de réalisation nombreux ; facturation application/API à distinguer.[^HF2][^HF6]

**Prix.** Le billet officiel du 24 octobre donne Starter **15 $/200 crédits**, Plus **49 $/1 000**, Ultra **129 $/3 000** ; Team **79 $/siège/1 000** et Scale **215 $/siège/2 500**. La page de vente ouverte ne restitue aucun tarif : **confirmation du tarif actuel au paiement non vérifiée**. Ne pas reconduire les 19 $/270 crédits du rapport antérieur comme un fait confirmé.[^HF3][^HF0]

**Calcul application, indicatif documenté** : Plus est le premier plan du billet ouvrant tous les modèles. Cinema 4.0, 10 s, 1080p avec audio : `160 ÷ 10 × (49 ÷ 1 000) = 0,784 $/s` ; maintien de cette offre au 3 novembre **non vérifié**.[^HF2][^HF3]

**API, meilleure résolution documentée 720p** : facturation aux jetons vidéo. Pour 5 s, 1280×720, 24 i/s, sans vidéo d'entrée : `ceil(5 × 1280 × 720 × 24 ÷ 1024) = 108 000 jetons` ; `108 000 ÷ 5 × (0,0214 $ ÷ 1 000) = 0,46224 $/s`. Hypothèse : format 16:9 exact. La page arrondit à **0,4623 $/s** ; l'API 1080p n'est pas documentée pour ce produit.[^HF4]

### 2. OpenArt

**Modèles et date.** Modèle vidéo fondation maison : **non vérifié**. SwitchX appartient à **Beeble**, même s'il est intégré à OpenArt VFX. Agrégation documentée : Seedance 2.5/2.0, Kling, Wan, LTX, PixVerse, Gemini Omni et autres. Seedance 2.5 est traité dans un guide OpenArt du **21 septembre 2026** ; cela ne constitue pas sa date de lancement chez ByteDance.[^OA1][^OA3][^OA4]

**Fonctions.** Director organise films, publicités et clips musicaux ; Character Builder pour les références persistantes ; Motion Control ; VFX avec masque, arrière-plan et relight ; Worlds pour des environnements 3D navigables ; MCP/CLI dans Claude et ChatGPT. Audio, voix et musique sont intégrés aux parcours Director. Doublage spécialisé, timeline multipiste, API REST publique autonome et collaboration simultanée : **non vérifiés**.[^OA1][^OA3][^OA4][^OA5][^OA6]

**Ergonomie.** Entrée par résultat attendu — film, UGC, publicité produit — et bibliothèque de personnages ; VFX avec comparaison source/résultat. Lourdeur déduite : choisir le moteur et préparer ses références ; le montage automatique ne prouve pas un contrôle éditorial fin.[^OA3][^OA4]

**Prix.** Tarifs mensuels de référence affichés : Starter **14 $/4 000 crédits**, Plus **34 $/12 000**, Pro **56 $/24 000**, Wonder **240 $/106 000** ; équivalents annuels affichés **13/27/44/175 $ par mois**. Le texte extrait juxtapose les deux modes : le total annuel au paiement n'a pas été contrôlé. Supplément Plus : **15 $/5 000 crédits**.[^OA2]

**Coût phare Seedance 2.5 en 1080p : non vérifié**, application et API. Le coût en crédits pour cette configuration n'est pas exposé dans la page tarifaire ouverte. Formule prête : `(C1080 ÷ durée) × (14 ÷ 4 000)` si Starter permet exactement cette configuration. Le nombre approximatif de « vidéos par mois » n'indique ni le modèle ni la résolution : il ne permet pas de calculer un prix fiable.[^OA2][^OA3]

### 3. Kling — Kuaishou

**Modèles et date.** **Kling 4.0**, disponible depuis le **15 octobre 2026**, avec variante Flash ; la page produit décrit 3–30 s, jusqu'à 15 références combinées et 10 images clés. L'annonce 4K/HDR reste mêlée à la mention « coming soon » : disponibilité effective de ces sorties **non vérifiée**. Agrégation de modèles vidéo tiers : **non vérifiée**.[^KL1][^KL2]

**Fonctions.** Mouvements caméra, sujets/voix de référence, multi-plans, édition ciblée et recréation d'une vidéo existante ; Avatar et Lip Sync figurent dans le produit. Agent, chat et Canvas : **non vérifiés**. API officielle existante ; son barème complet n'est pas lisible dans l'ouverture. TTS autonome, doublage, musique autonome, 3D exportable, montage multipiste et collaboration : **non vérifiés**.[^KL2][^KL4][^KL5]

**Ergonomie.** Un même parcours texte/image/références ; images clés placées sur une chronologie. Lourdeur déduite : limites croisées des médias et différences entre modèles, résolutions et services.[^KL2]

**Prix.** Le guide officiel de juillet indique Standard **660 crédits**, Pro **3 000**, Premier **8 000**, Ultra **26 000**, avec plusieurs prix promotionnels et de renouvellement. Exemple Standard : **6,99 $** initialement, **8,80 $** au renouvellement, **10 $** également affiché. **Offre récurrente actuelle non vérifiée** : ne pas choisir arbitrairement un montant. **Prix/s Kling 4.0 application et API : non vérifié** ; les crédits par seconde et le prix de l'unité API ne sont pas lisibles ensemble dans les pages ouvertes. Le tarif Kling 3.0 ne doit pas être attribué à 4.0.[^KL3][^KL5]

### 4. Runway

**Modèles et date.** **Gen-4.5**, génération, annoncé le **1er décembre 2025** ; le changelog marque sa disponibilité le **11 décembre 2025**. **Aleph 2.0**, édition, est annoncé le **21 mai 2026**. Les dates du catalogue développeur correspondent à l’arrivée dans l’API et diffèrent. Act-Two et Characters complètent le catalogue maison. **GWM Worlds 2**, aperçu de recherche annoncé le **3 septembre 2026**, génère des mondes interactifs continus en **720p à 24 i/s**, avec audio **48 kHz** ; disponibilité commerciale et prix non vérifiés. Tiers : Kling 4.0, Seedance 2.5, MiniMax H3, Wan, Veo et Gemini Omni notamment.[^RW7][^RW1][^RW2][^RW5][^RW9]

**Fonctions.** Références, direction caméra, capture de performance, avatars interactifs, voix/TTS/doublage et génération musicale ; Aleph propage la modification d'une image à la vidéo, retire des objets et restyle. Agent, Workflows, Apps, MCP/API, projets partagés et commentaires sont documentés. Multi-plans : modèles et recettes ; véritable édition 3D exportable : **non vérifiée**. Montage : outils et assemblage, à distinguer d'un NLE complet.[^RW1][^RW2][^RW3][^RW5][^RW6]

**Ergonomie.** Prévisualiser l'édition sur une image avant le rendu vidéo ; agent et routage des modèles ; applications réutilisables. Lourdeur déduite : formats professionnels, modèles et suppléments multiplient les choix.[^RW2][^RW5]

**Prix.** Free **125 crédits uniques** ; Standard **15 $/625 crédits par mois**, Pro **35 $/2 250**, Max **95 $/9 500** ; annuel **12/28/76 $ par mois**. Gen-4.5 consomme **60 crédits/5 s** : `60 ÷ 5 × (15 ÷ 625) = 0,288 $/s` en génération de base ; annuel `= 0,2304 $/s`. La documentation Gen-4.5 donne **720p natif**, pour **2 à 10 s**, à **12 crédits/s**. Ces coûts correspondent donc au maximum natif documenté ; coût total d’une livraison agrandie en 1080p **non vérifié**.[^RW3][^RW8]

**API Gen-4.5** : `60 ÷ 5 × 0,01 = 0,12 $/s`, sortie native 720p, hors agrandissement et formats additionnels.[^RW8] Pour une comparaison 1080p explicitement documentée, **Aleph 2.0 édite** jusqu'à 30 s en 1080p : `140 ÷ 5 × (15 ÷ 625) = 0,672 $/s` sur Standard ; API `28 × 0,01 = 0,28 $/s`. C'est de l'édition d'une vidéo fournie, pas le même travail qu'une génération Gen-4.5.[^RW2][^RW3][^RW4]

### 5. Luma — Dream Machine / Luma Agents

**Modèles et date.** **Ray 3.2** est la version vidéo maison vérifiée dans la documentation Agents ; date précise du lancement **non vérifiée**, la page d'annonce n'étant pas ouvrable par l'outil. Uni-1/Uni-1-max sont des modèles image. Catalogue tiers de l'application et correspondance actuelle avec Dream Machine : **non vérifiés** ; les pages commerciales retournent un format non pris en charge.[^LU1]

**Fonctions.** L'API documente texte/image→vidéo, première/dernière image, multi-images clés, boucle, extension, édition de vidéo, reframe, réglages par signal, HDR et EXR. La documentation actuelle indique **jusqu'à 64 ancrages**, sans que cela prouve un storyboard de 64 plans. Agent/chat dans l'application, presets, avatars, voix, musique, 3D, timeline et collaboration : **non vérifiés dans les pages effectivement lisibles**.[^LU1]

**Ergonomie.** Contrôle visuel par images clés et modification d'une vidéo existante. Lourdeur déduite : types de requête et restrictions HDR/durée différents ; le prix ne progresse pas toujours linéairement avec la durée.[^LU1][^LU2]

**Prix application.** Plans, crédits et coût/s : **non vérifiés** ; les montants de l'ancien rapport ne sont pas repris.

**API Ray 3.2, 1080p SDR** : **400 crédits/5 s**, **1 200/10 s**. Taux catalogue par défaut **0,003 $/crédit** : `400 ÷ 5 × 0,003 = 0,24 $/s` ; pour 10 s, `1 200 ÷ 10 × 0,003 = 0,36 $/s`. Hypothèse explicite : compte au taux catalogue, sans tarif contractuel. HDR 1080p sur 5 s : `800 ÷ 5 × 0,003 = 0,48 $/s`, hors option EXR supplémentaire.[^LU2][^LU3]

### 6. Pika

**Modèles et date.** **Pika H3 Flex**, annoncé le **29 octobre 2026**, est un post-entraînement de MiniMax H3 par Pika ; Pika 2.5 reste listé. L'annonce prévoit Flex dans le produit de création le **2 novembre** ; la grille tarifaire le liste effectivement. Tiers : Seedance 2.5, MiniMax H3, Wan 3.0, Gemini Omni, Kling, modèles image et audio.[^PI1][^PI2]

**Fonctions.** Presets, caméra par instruction, références multimodales et personnages, parole synchronisée ; swap/retrait/restyle et motion transfer ; Video Studio et timeline dans ChatGPT ; studios voix/musique/bruitages, MCP/API. Flex propose une finition jusqu'en 4K et des pistes audio séparées. 3D exportable, doublage dédié et collaboration entre plusieurs humains : **non vérifiés**.[^PI1][^PI3][^PI4]

**Ergonomie.** Applications par tâche, comparaison/retouche dans le chat, brouillon conservé puis finition. Lourdeur déduite : distinguer Flex, les modèles tiers, les applications et la facturation API.[^PI3][^PI4]

**Prix application.** Starter **10 $/900 crédits**, Creator **35 $/3 150**, Fancy dès **95 $/8 550** mensuels ; annuel **8/28/76 $**. Flex 768p, 5 s : `10 ÷ 5 × (10 ÷ 900) = 0,02222 $/s`. **Application 1080p/4K : coût non vérifié** ; aucun nombre de crédits de finition ne permet de prolonger ce calcul.[^PI2]

**API Flex, sans référence vidéo** : 1080p **0,035 $/s** au prix de lancement, **0,07 $/s** régulier ; exemple `0,175 $ ÷ 5 = 0,035 $/s`. 4K **0,08 $/s** lancement, **0,16 $/s** régulier. L'offre gratuite du Club est annoncée jusqu'au **5 novembre** ; la page ne donne pas clairement la même échéance au prix de lancement : ne pas les confondre. Audio stems facultatifs : **0,001 $/s** en supplément.[^PI3]

### 7. Hailuo / MiniMax — MiniMax Design

**Modèles et date.** **MiniMax H3**, lancé le **31 juillet 2026**, poids publiés le **3 août** ; variantes tarifées H3, Highspeed, Lite et Max, dates individuelles **non vérifiées**. Hailuo 2.3 demeure dans les modèles historiques de l'API. Modèles tiers agrégés par Design : **non vérifiés** ; la sélection automatique de modèles ne prouve pas leur identité.[^MM1][^MM2][^MM3]

**Fonctions.** H3 : audio stéréo, références image/vidéo/audio, personnages, premier/dernier cadre, caméra par référence et v2v. Design ajoute agent, skills, presets de workflows, scénario/storyboard, musique/voix et traitement sur timeline. API, outils MCP de l'écosystème. Avatar et lip-sync : **partiels**, via génération guidée par audio ; service de doublage, 3D exportable et collaboration simultanée : **non vérifiés**.[^MM1][^MM2][^MM3][^MM4]

**Ergonomie.** Brief→exécution par l'agent ; nœuds reliés automatiquement ; actifs sauvegardés localement. Lourdeur déduite : application de bureau, configuration des médias et distinction entre exécution locale et services hébergés. « Local » ne prouve pas que tous les rendus sont exécutés sur l'ordinateur.[^MM4]

**Prix application.** Design et Hailuo : plans, crédits et coût/s **non vérifiés**, écrans de souscription sans contenu exploitable.[^MM5]

**API phare H3, 2K** : **0,13 $/seconde de sortie**. Exemple `0,65 $ ÷ 5 = 0,13 $/s`, sans vidéo d'entrée, au plus cinq images et sans Context-IR facturé en plus. Vidéo d'entrée : **0,13 $/s supplémentaire** ; images au-delà du quota : **0,04 $ chacune**. Le 768p coûte **0,08 $/s**. Ne pas prendre le prix Lite 480p pour le prix du H3 phare 2K.[^MM3]

### 8. Google — Veo / Flow / Gemini Omni

**Modèles et date.** **Flow reste le produit** : Gemini Omni ne le remplace pas, il est l'un de ses moteurs. Veo 3.1 Lite/Fast/Quality coexistent avec **Gemini Omni Flash 1.1**, annoncé le **27 août 2026**. Modèles vidéo tiers dans Flow : **non vérifiés**.[^GO1][^GO2]

**Fonctions.** Texte, cadres et ingrédients ; références cohérentes, voix personnalisées, génération audio ; Omni édite des vidéos importées et générées. Flow Agent planifie, choisit le modèle, produit et organise les actifs. Construction de scènes et coupe de clips ; API Gemini. Musique via Flow Music, service lié mais crédits séparés. Presets d'effets comparables au catalogue Higgsfield, doublage dédié, 3D exportable, MCP officiel Flow et collaboration simultanée : **non vérifiés**.[^GO2][^GO4][^GO5][^GO7]

**Ergonomie.** Chat au sein du projet, glisser les actifs comme références, tester en 360p avant d'agrandir. Lourdeur déduite : différences de fonctions Veo/Omni, crédits par sortie plutôt que par requête et conditions régionales.[^GO1][^GO2][^GO3]

**Prix application.** Plus **200 crédits/mois**, Pro **1 000**, Ultra **10 000 ou 25 000** suivant l'offre ; allocation quotidienne distincte **50 crédits**. Prix de vente Plus/Pro local actuel : **non vérifié** dans la page commerciale ouverte. Le billet de janvier donne Plus US **7,99 $/mois**, à traiter comme prix publié au lancement, pas comme vérification du paiement québécois.[^GO3][^GO6][^GO8]

**Calcul sous hypothèse publiée** : si Plus reste à 7,99 $ pour 200 crédits, Omni 720p 10 s coûte 15 crédits et l'upscale 1080p est inclus : `15 ÷ 10 × (7,99 ÷ 200) = 0,059925 $/s livré en 1080p agrandi`. Exclut les crédits quotidiens. **Tarif récurrent actuel non vérifié**.[^GO3][^GO8]

**API Omni 1.1** : taux vidéo **17,50 $/million de jetons**, **5 792 jetons/s à 720p** : `5 792 × 17,50 ÷ 1 000 000 = 0,10136 $/s`, plus entrées et sorties texte/raisonnement. Coût 1080p/4K dans cette grille native : **non vérifié** ; aucune extrapolation quadratique n'est appliquée. Prix API Veo 3.1 actuel dans les sources Google ouvertes : **non vérifié**.[^GO9]

### 9. OpenAI Sora

**État.** **Produit arrêté le 26 avril 2026** ; Videos API et Sora 2/Sora 2 Pro retirés le **24 septembre 2026**. Dernières références historiques de la famille : Sora 2 et Sora 2 Pro ; pas de nouvelle version disponible vérifiée au 3 novembre. Aucun agrégateur tiers n'est assimilé à une offre OpenAI active.[^SO1][^SO2]

**Fonctions et ergonomie actuelles.** Toutes les capacités de production Sora sont **indisponibles dans l'offre retirée**. Les anciennes interfaces ou fiches de modèles encore en ligne ne sont pas une preuve d'accès. Ergonomie actuelle à évaluer : sans objet ; travail résiduel = récupération éventuelle d'archives, pas création.[^SO1][^SO2]

**Prix.** Aucun plan ou prix/s de production actuel. **Sans objet**, application et API ; les anciennes grilles ne doivent pas entrer dans un classement d'achat de novembre. Le maintien d'un lien Sora dans OpenArt ou Krea est un écart de documentation, pas la preuve de sa remise en service.[^SO2][^OA1][^KR4]

### 10. Seedance / Dreamina — ByteDance, BytePlus, CapCut

**Modèles et date.** **Seedance 2.5**, annoncé le **31 juillet 2026** ; 30 s, jusqu'à 30 images + 10 vidéos + 10 audios, édition par timestamp. Seedance 2.0/Fast/Mini restent proposés. Dreamina agrège aussi des modèles image et Veo ; le lien Sora est traité comme historique/non vérifié. Ne pas confondre le moteur Seedance, l'interface Dreamina, l'API BytePlus et l'éditeur CapCut.[^SD1][^SD2][^SD3]

**Fonctions.** Références cohérentes, caméra, audio, multi-plans, extension, v2v et édition ciblée. Dreamina présente Cinema/Trends/Marketing Studio et avatars. CapCut est la composante montage de l'écosystème ; partage exact des projets, abonnements et fonctions avec Dreamina **non vérifié**. TTS autonome, doublage, musique autonome, 3D exportable, MCP, agent de montage et collaboration dans Dreamina : **non vérifiés**.[^SD1][^SD3]

**Ergonomie.** Studio par usage et référence multimodale ; modification d'un moment précis. Lourdeur déduite : régions, promotions, produits et portefeuilles de crédits distincts.[^SD1][^SD3][^SD4]

**Prix application.** La page Dreamina décrit Basic US **1 575 crédits**, **0,29 $** le premier mois éligible, puis **15 $/mois** ; Seedance 2.5 **37 crédits/s en 720p**. Promotion US, pas prix Québec. Exemple récurrent à ce palier : `185 ÷ 5 × (15 ÷ 1 575) = 0,35238 $/s` ; premier mois `= 0,006813 $/s`. **Coût application 1080p et offre québécoise : non vérifiés** ; exemples 720p exclus du classement principal.[^SD3]

**API BytePlus, 1080p sans vidéo d'entrée** : l'exemple officiel 5 s vaut **2,843 $**, soit `2,843 ÷ 5 = 0,5686 $/s` estimé. Facturation aux jetons : `jetons ÷ durée × prix du jeton`, estimation officielle `(durée entrée + durée sortie) × largeur × hauteur × i/s ÷ 1024`. La grille sans vidéo donne **11,70 $** pour le palier 1080p dans la tarification aux jetons ; l'exemple monétaire est privilégié car l'unité de cette colonne est peu explicite dans l'extraction. Avec vidéo, minima et secondes d'entrée modifient le coût : ne pas appliquer 0,5686 $/s sans changement.[^SD4]

### 11. LTX Studio — Lightricks

**Modèles et date.** **LTX-2.5 Fast/Pro**, introduits dans l'API le **11 août 2026** ; extension des sorties Pro à 4K le **2 septembre**. LTX-2.3 subsiste. Tiers dans Studio : Kling, Seedance, Veo et modèles image de partenaires.[^LX1][^LX2][^LX3]

**Fonctions.** Caméra, Elements cohérents, storyboards et pitch decks ; génération audio→vidéo, son synchronisé, v2v et outils d'édition ; Flows en nœuds, API et collaborateurs selon le plan. La fonction retake/extend existe dans l'écosystème mais **n'est pas prise en charge par LTX-2.5 dans la matrice actuelle**. TTS autonome, doublage, musique autonome, vrai asset 3D, agent/chat et MCP Studio : **non vérifiés**.[^LX1][^LX3][^LX4]

**Ergonomie.** Scénario/storyboard comme point d'entrée, personnages sauvegardés, paramètres caméra. Lourdeur déduite : fonctionnalités et moteurs dépendent du plan ; storyboard, nœuds et montage demandent des arbitrages différents.[^LX3]

**Prix application.** Lite **15 $/8 000 crédits**, Standard **35 $/28 000**, Pro **125 $/110 000** ; annuel **12/28/100 $ par mois**. **Coût/s LTX-2.5 1080p dans Studio : non vérifié**, consommation par génération non publiée dans la page ouverte. Formule Lite : `(C1080 ÷ durée) × (15 ÷ 8 000)` ; ne pas supposer que crédits Studio et dollars API sont interchangeables.[^LX3]

**API Pro 1080p** : tarif direct **0,17 $/s** ; pour une durée acceptée de 6 s : `1,02 $ ÷ 6 = 0,17 $/s`. Fast 1080p : **0,13 $/s** ; Pro 4K : **0,39 $/s**. Ces tarifs concernent la génération vidéo ; le modèle tarifé directement ne nécessite pas de conversion de crédits.[^LX4][^LX5]

### 12. Krea

**Modèles et date.** Pas de modèle vidéo fondation maison identifié : **non vérifié**. **Krea 3 est un modèle image**, sorti de bêta le **20 octobre 2026**, pas une nouvelle version vidéo. Catalogue vidéo : Seedance 2.5, Kling 4.0, MiniMax H3/Max, Wan 3, FLUX 3 Video/Max, Runway et Veo.[^KR1][^KR2][^KR3]

**Fonctions.** Agent qui planifie et pilote des outils ; Nodes→Apps ; références, entraînement de styles/personnages ; Realtime image ; vidéo restyle, motion transfer, lipsync ; voix/clonage ; génération d'objets 3D ; MCP/API/plugins et partage de projets Nodes. Timeline multipiste, doublage et musique autonome : **non vérifiés**. Le temps réel d'image n'est pas une preuve de vidéo interactive temps réel.[^KR1][^KR2][^KR3]

**Ergonomie.** Agent à partir d'un brief ; apps cachant les nœuds ; devis MCP avant exécution. Lourdeur déduite : choix des modèles, graphes complexes et solde API séparé des unités de l'application.[^KR2][^KR4]

**Prix application.** Basic **9 $/5 000 unités**, Pro **35 $/20 000**, Max **105 $/60 000** ; Business **200 $/80 000**, niveaux configurables. Basic ne donne accès qu'à une sélection vidéo, Pro à tous. **Seedance 2.5 1080p : coût/s et plan minimal exact non vérifiés** ; les comptes approximatifs de vidéos du comparateur ne sont pas convertis en crédits par rendu.[^KR1]

**API.** Solde USD séparé. Seedance 2.5 existe en 1080p, mais son prix pour cette configuration est **non vérifié** dans la grille accessible. Gen-4.5 est affiché **0,12 $/s**, exemple de moteur tiers de repli, sans résolution explicite : exclu du classement 1080p du modèle phare. Ne pas appliquer le prix « from » de Seedance 2.0 à Seedance 2.5.[^KR4][^KR5][^KR6]

### 13. Freepik, désormais Magnific

**Identité et modèles.** Renommage officiel **le 28 avril 2026** : même compte, plan et crédits, domaine magnific.com. **Magnific One est un modèle image** ; modèle vidéo maison **non vérifié**. Le studio agrège notamment Seedance, Kling, Veo, Runway, Wan et LTX ; la disponibilité varie suivant l'outil.[^MA1][^MA2][^MA3]

**Fonctions.** Presets/visual prompts, Custom Characters, multi-plans, Speak, voix/clonage et musique ; Clip Editor/Video Project Editor ; vidéo relight et agrandissement ; objets/scènes 3D ; Spaces collaboratifs ; Flows exécutables en interface simple, MCP et API. Doublage avec traduction/lipsync dédié : **non vérifié** dans les documents ouverts.[^MA2][^MA3][^MA4][^MA5][^MA6]

**Ergonomie.** Un Flow devient quelques champs et un bouton ; modèles et actifs dans le même espace ; annotations visuelles. Lourdeur déduite : construction du graphe en amont et somme des coûts de chaque nœud ; règles d'illimité dépendantes des modèles.[^MA3][^MA4]

**Prix.** Premium affiche **20 $/mois** ou **14,50 $/mois annuel**, avec **20 000 crédits/mois** ou **240 000/an**. Premium+ **45 $** ou **33,75 $ annuel**, **45 000/mois** ou **600 000/an** ; Pro Starter **110 $** ou **82,50 $ annuel**, **1,5 million/an** affiché. Les allocations annuelles ne sont pas toujours douze fois les allocations mensuelles.[^MA2][^MA7]

**Prix/s Seedance 2.5 1080p : non vérifié**, application comme API : coût du rendu en crédits absent des pages lisibles. Formule Premium mensuel : `(C1080 ÷ durée) × (20 ÷ 20 000)`. Flows API/MCP utilisent le même solde selon leur documentation ; cela ne permet pas de déduire le barème d'un modèle manquant ni celui d'un autre produit API.[^MA4][^MA7]

### 14. Leonardo.Ai

**Modèles et date.** Famille vidéo de marque **Motion 2.0 / Motion 2.0 Fast** ; date de lancement et architecture fondation maison **non vérifiées**. Le guide vidéo, mis à jour le **10 août 2026**, met surtout en avant Seedance 2.5, FLUX 3 Video, MiniMax H3, Veo 3.1, Kling et Wan. Il signale explicitement le retrait de Sora chez Leonardo.[^LE1]

**Fonctions.** Blueprints prédéfinis ; commandes caméra Motion ; références et modèles personnalisés ; édition/restyle de vidéo ; scènes multi-plans via les moteurs compatibles ; équipes et API. Parole/son : partiels via modèles tiers audio-vidéo. Avatar/lipsync autonome, TTS/doublage, musique autonome, 3D exportable, timeline multipiste, agent et MCP : **non vérifiés**.[^LE1][^LE2][^LE3][^LE4]

**Ergonomie.** Blueprints combinant réglages et modèles ; réutilisation des images pour tester plusieurs moteurs ; bibliothèque privée. Lourdeur déduite : coûts variant selon modèle/références, file ralentie après épuisement des tokens sur les offres compatibles.[^LE2][^LE4][^LE5]

**Prix.** Essential **12 $/8 500 tokens mensuels**, Premium **30 $/25 000**, Ultimate **60 $/60 000** ; API au paiement à l'usage séparé. **Prix/s phare Seedance 2.5 1080p : non vérifié** dans l'application et l'API. Formule Essential : `(T1080 ÷ durée) × (12 ÷ 8 500)` si cette configuration y est ouverte. L'aide confirme que le prix est affiché avant génération, mais ne fournit pas ici sa valeur.[^LE4][^LE5]

### 15. Hedra

**Modèles et date.** **Character 3**, modèle audio→avatar, sorti en **mars 2025** selon sa fiche ; **Omnia**, modèle de recherche, mentionné en **février 2026**, sans preuve dans les pages lues d'un remplacement commercial de Character 3. Agrégation : Seedance 2.5, MiniMax H3, Kling, Veo, Wan, modèles image et ElevenLabs.[^HE1][^HE2]

**Fonctions.** Avatars parlants/chantants, lip-sync à partir d'audio ; Elements persistants ; agent, skills, canvas partagé, API et MCP. TTS, changement/clonage de voix, musique et bruitages dans l'API ; édition/motion transfer/restyle/retrait proposés selon le moteur. **Musique dans Studio annoncée « coming soon »**, donc ne pas la confondre avec l'API disponible. Caméra : via modèles tiers. 3D exportable et timeline générale : **non vérifiées**.[^HE1][^HE2][^HE3][^HE4][^HE5]

**Ergonomie.** Portrait + audio pour Character ; brief→agent ; éléments et skills partagés. Lourdeur déduite : Studio et API ont des soldes séparés ; préparer un audio propre ; large catalogue à paramètres différents.[^HE1][^HE3][^HE5]

**Prix application.** Plans et crédits Studio : **non vérifiés** ; la page ouverte expose surtout le paiement API. **API Character 3 en 1080p : 6,25 cents/s**, donc pour 10 s `0,625 $ ÷ 10 = 0,0625 $/s`. Audio fourni, TTS éventuel en supplément. Les tarifs 540p **0,025 $/s** et 720p **0,05 $/s** ne sont pas le prix 1080p. Prix/s Studio : **non vérifié**.[^HE1][^HE4]

### 16. Vidu — ShengShu

**Modèles et date.** **Vidu Q4 Preview**, au changelog du **7 octobre 2026** ; Q3 et S2 complètent l'offre. La page grand public dit Q4, tandis que l'API maintient Preview : conserver cette distinction. Tiers vidéo agrégés : **non vérifiés**.[^VI1][^VI2]

**Fonctions.** Q4 : jusqu'à 15 images et 3 références de voix, multi-plans, lip-sync et sorties jusqu'à 4K ; templates d'effets, motion sync, remplacement et extension dans l'écosystème. S2 Avatar et S2 Editing : interaction/édition de flux en temps réel, annoncées le **15 septembre**. TTS, clonage, audio, agent marketing avec storyboard, API et MCP. 3D exportable, timeline multipiste et collaboration simultanée : **non vérifiées**.[^VI1][^VI2][^VI3][^VI4]

**Ergonomie.** Templates et génération depuis références ; agent préconfiguré ; voix attachées aux personnages. Lourdeur déduite : familles Q/S et variantes, Preview, grilles régionales et modalités temps réel différentes.[^VI1][^VI2][^VI4]

**Prix application.** Plans et montants **non vérifiés**, la page reste sur « Loading pricing plans ». **API vérifiée dans la grille RMB accessible** : Q4 Preview 4K **78 crédits/s**, **0,03125 RMB/crédit** ; exemple `390 ÷ 5 × 0,03125 = 2,4375 RMB/s`. Cette grille mentionne un rechargement **500 RMB/16 000 crédits**. **Prix mondial USD et prix 1080p Q4 : non vérifiés** ; aucune conversion de devise ni fusion de crédits régionaux n'est faite.[^VI5][^VI3]

### 17. Moonvalley — Marey

**Modèles et date.** Dernière version numérotée trouvée sur le site : **Marey v1.5**, présentée le **8 juillet 2025**. Nouvelle version 2026 : **non vérifiée**. Pas d'agrégation vidéo tierce vérifiée.[^MV1]

**Fonctions.** Caméra pilotée depuis une scène reconstruite, références séparées personnages/objets, transfert de pose et de mouvement, trajectoires dessinées, images clés sur une chronologie et extension. Cette chronologie guide la génération : elle ne prouve pas un montage multipiste. Scène 3D interne : partiel ; export d'assets 3D, avatars/lipsync, voix/doublage, musique, agent/MCP, API directe ouverte et collaboration : **non vérifiés**. Le site indique une liste d'attente API et des partenaires d'inférence.[^MV2][^MV3]

**Ergonomie.** Dessiner une trajectoire et poser des images clés rendent la direction concrète. Lourdeur documentée : accès commercial centré sur les partenariats ; la plateforme n'est plus à traiter comme un abonnement libre-service ordinaire.[^MV2][^MV3]

**Prix.** Moonvalley annonce l'arrêt des renouvellements Standard/Plus/Pro le **23 mars 2026**, avec fin d'accès à l'échéance du cycle. Offre entreprises/studios sur contact. **Prix/s actuel application et API : non vérifié** ; aucun ancien forfait n'est recyclé comme tarif actif.[^MV3]

### 18. Meshy

**Modèles et date.** Produit **3D**, pas modèle vidéo généraliste. L'aide identifie **Meshy 7.1** ; date exacte de cette sous-version **non vérifiée** (Meshy 7 : août 2026). **N1**, texturage natif 3D, annoncé le **3 novembre 2026**, ne doit pas être appelé nouveau générateur vidéo ou nouveau modèle de géométrie. Tiers vidéo : sans objet.[^ME1][^ME2]

**Fonctions.** Texte/image→3D, textures, rigging, animations préréglées, agent 3D, MCP/CLI/API et plugins DCC ; partage d'actifs, annotations et crédits d'équipe selon plan. Cohérence = réutiliser le même mesh. Caméra cinématique vidéo, lipsync/TTS/doublage, musique, v2v, storyboard et timeline de montage : **hors cœur de produit / non vérifiés**, pas des fonctions vidéo à lui attribuer à partir de ses animations 3D.[^ME3][^ME4]

**Ergonomie.** Photo ou croquis en entrée, auto-rig, envoi vers Blender/Unity. Lourdeur déduite : topologie, textures et format d'export restent des décisions de production 3D.[^ME3]

**Prix.** Page rendue en **GBP** : Pro **16 £/1 000 crédits mensuels** (premier mois 8 £), Premium **32 £/3 000**, Ultra **80 £/8 000**, Studio **56 £/5 500 crédits partagés**, sièges affichés à **8 £/mois**. Prix USD **non vérifié**. **Prix par seconde de vidéo : sans objet**, application et API. Un temps de calcul de mesh n'est pas une durée de vidéo livrée.[^ME4]

### 19. Tripo

**Modèles et date.** Produit **3D**. Géométrie **H3.1**, snapshot `v3.1-20260211` ; **P2**, snapshot `P2-20260801` pour la topologie de production ; texturage `v3.5-20260815`. Ces dates sont celles des identifiants, pas une preuve d'un même jour de lancement Studio. Aucun modèle vidéo généraliste maison vérifié.[^TR1][^TR2]

**Fonctions.** Texte/image/multivues→mesh, PBR, segmentation, retopologie, rigging/retargeting, export DCC ; API, CLI et plugin Codex. Modèles image tiers listés : Seedream, Nano Banana, ChatGPT Image. Espace d'actifs partagé dans Team. Presets d'animation : partiel. Voix, lipsync, musique, v2v, montage, storyboard et agent vidéo : **non vérifiés / hors périmètre 3D**.[^TR1][^TR2][^TR3][^TR4]

**Ergonomie.** Déposer une image, choisir géométrie détaillée ou adaptée au jeu, export par lots. Lourdeur déduite : polygones, UV, textures et options de topologie ; plusieurs suppléments peuvent s'additionner.[^TR2][^TR3]

**Prix.** Pro **20 $/3 000 crédits mensuels**, Max **90 $/25 000** affichés ; les blocs mensuel/annuel se contredisent sur certains totaux, donc échéancier annuel exact **non vérifié**. Team : tarifs et total ambigus, **non vérifiés**. API H3.1 texte→3D : **10 crédits/0,10 $** sans texture, **20/0,20 $** avec texture standard ; image→3D : **20/0,20 $**, **30/0,30 $** respectivement. **Prix/s vidéo : sans objet** ; les secondes de génération affichées sont des latences.[^TR2][^TR3]

### 20. Autodesk Flow Studio — ex-Wonder Studio

**Modèles et date.** Pas de modèle fondation vidéo maison nommé et versionné vérifié. Wonder 3D, Neural Layer et outils de capture constituent le socle ; le produit agrège désormais des modèles partenaires : Seedance 2.5, Wan 3.0, Veo, Kling, modèles image, voix Gemini et Trellis 2.0. Dates de lancement individuelles de ces intégrations : **non vérifiées**.[^AU1][^AU2][^AU3]

**Fonctions.** 3D Editor + Canvas ; caméra contrôlable ; personnages persistants et LoRA Neural Layer ; génération/rigging 3D, capture faciale/corps/mains, remplacement de comédiens, clean plates, masques et scènes Maya/Blender/Unreal/USD. Parole et audio : via partenaires ; véritable service de doublage, musique autonome, MCP/API publique, agent/chat et collaboration simultanée : **non vérifiés**. Timeline d'animation : partielle par rapport au montage multipiste.[^AU1][^AU2][^AU3]

**Ergonomie.** Vidéo réelle→personnage CG sans marqueurs ; exports de scène conservant les éléments éditables ; parcours Canvas puis scène 3D. Lourdeur déduite : préparation des personnages et finition DCC. Le site précise que le mobile n'est pas encore optimisé.[^AU2][^AU3]

**Prix.** Free **300 crédits/mois** ; Lite **10 $/2 100**, Standard **45 $/6 000**, Pro **95 $/12 000** ; annuel respectivement **7/30/64 $ par mois** ; Enterprise sur devis.[^AU3]

**Coût de traitement comparable mais distinct** : Live Action/Animation **20 crédits/s**, Lite livré jusqu'à 1080p : `100 ÷ 5 × (10 ÷ 2 100) = 0,095238 $/s de vidéo traitée` ; annuel `= 0,066667 $/s`. **Ce n'est pas le coût du modèle phare texte→vidéo agrégé** : ce dernier, ainsi que son éventuel tarif API, reste **non vérifié**. Mocap seul et clean plate ont d'autres barèmes.[^AU3][^AU4]


## Tableau comparatif unique des fonctions

**Légende :** ✔ = capacité explicitement documentée dans l'offre concernée ; **partiel** = périmètre limité, moteur partenaire, assemblage automatique ou fonction voisine ; ✘ = offre retirée ou fonction hors du type de produit ; **non vérifié** = preuve insuffisante. Le tableau décrit la disponibilité annoncée, pas la qualité observée. Un ✔ n'indique pas que le plan d'entrée inclut la fonction.

Colonnes : **Hf** Higgsfield ; **OA** OpenArt ; **Kl** Kling ; **Rw** Runway ; **Lu** Luma ; **Pi** Pika ; **MM** MiniMax ; **Go** Google ; **So** Sora ; **SD** Seedance/Dreamina ; **LX** LTX Studio ; **Kr** Krea ; **Ma** Magnific ; **Le** Leonardo ; **He** Hedra ; **Vi** Vidu ; **MV** Moonvalley ; **Me** Meshy ; **Tr** Tripo ; **Au** Autodesk Flow Studio.

Sources : celles de chaque fiche, en particulier les documentations des fonctions ; les cellules « non vérifié » ne sont pas remplacées par des croix. 3D : « partiel » peut désigner une scène interne sans export établi. Collaboration : partage d'actifs suffit ici, le co-montage simultané n'est pas sous-entendu. Montage : une suite de plans, une chronologie d'images clés et un éditeur multipiste restent distincts.

| Fonction | Hf | OA | Kl | Rw | Lu | Pi | MM | Go | So | SD | LX | Kr | Ma | Le | He | Vi | MV | Me | Tr | Au |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Modèle vidéo maison actif | ✔ | non vérifié | ✔ | ✔ | ✔ | partiel | ✔ | ✔ | ✘ | ✔ | ✔ | non vérifié | non vérifié | non vérifié | ✔ | ✔ | ✔ | ✘ | ✘ | non vérifié |
| Modèles vidéo tiers agrégés | ✔ | ✔ | non vérifié | ✔ | non vérifié | ✔ | non vérifié | non vérifié | ✘ | partiel | ✔ | ✔ | ✔ | ✔ | ✔ | non vérifié | non vérifié | ✘ | ✘ | ✔ |
| Effets / recettes à presets | ✔ | ✔ | non vérifié | ✔ | non vérifié | ✔ | ✔ | non vérifié | ✘ | ✔ | partiel | partiel | partiel | ✔ | partiel | ✔ | non vérifié | partiel | partiel | non vérifié |
| Direction / contrôle caméra | ✔ | partiel | ✔ | partiel | ✔ | ✔ | partiel | partiel | ✘ | ✔ | ✔ | ✔ | partiel | ✔ | partiel | ✔ | ✔ | partiel | partiel | ✔ |
| Personnages / éléments cohérents | ✔ | ✔ | ✔ | ✔ | partiel | ✔ | ✔ | ✔ | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Avatar parlant / lip-sync | ✔ | partiel | ✔ | ✔ | non vérifié | ✔ | partiel | partiel | ✘ | ✔ | partiel | ✔ | ✔ | partiel | ✔ | ✔ | non vérifié | ✘ | ✘ | partiel |
| Voix / TTS / clonage autonome | ✔ | partiel | non vérifié | ✔ | non vérifié | ✔ | ✔ | partiel | ✘ | non vérifié | non vérifié | ✔ | ✔ | non vérifié | ✔ | ✔ | non vérifié | ✘ | ✘ | partiel |
| Doublage / traduction dédiée | ✔ | non vérifié | non vérifié | ✔ | non vérifié | non vérifié | non vérifié | non vérifié | ✘ | non vérifié | non vérifié | non vérifié | non vérifié | non vérifié | non vérifié | non vérifié | non vérifié | ✘ | ✘ | non vérifié |
| Musique générée | ✔ | partiel | non vérifié | ✔ | non vérifié | ✔ | ✔ | partiel | ✘ | partiel | partiel | non vérifié | ✔ | partiel | partiel | partiel | non vérifié | ✘ | ✘ | non vérifié |
| Édition vidéo existante / restyle | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ | ✔ | ✔ | partiel | ✔ | ✔ | ✔ | ✔ | ✘ | ✘ | ✔ |
| Retrait / modification locale vidéo | ✔ | ✔ | ✔ | ✔ | partiel | ✔ | ✔ | ✔ | ✘ | ✔ | partiel | non vérifié | partiel | partiel | ✔ | ✔ | partiel | ✘ | ✘ | ✔ |
| 3D éditable / exportable | partiel | partiel | non vérifié | non vérifié | non vérifié | non vérifié | non vérifié | non vérifié | ✘ | non vérifié | non vérifié | ✔ | ✔ | non vérifié | non vérifié | non vérifié | partiel | ✔ | ✔ | ✔ |
| Montage / timeline | partiel | partiel | partiel | partiel | non vérifié | ✔ | ✔ | partiel | ✘ | partiel | partiel | non vérifié | ✔ | non vérifié | non vérifié | partiel | partiel | ✘ | ✘ | partiel |
| Agent / chat de création intégré | ✔ | ✔ | non vérifié | ✔ | non vérifié | partiel | ✔ | ✔ | ✘ | non vérifié | non vérifié | ✔ | partiel | non vérifié | ✔ | ✔ | non vérifié | ✔ | non vérifié | non vérifié |
| MCP officiel vérifié | ✔ | ✔ | non vérifié | ✔ | non vérifié | ✔ | partiel | non vérifié | ✘ | non vérifié | non vérifié | ✔ | ✔ | non vérifié | ✔ | ✔ | non vérifié | ✔ | non vérifié | non vérifié |
| API officielle vérifiée | ✔ | non vérifié | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | partiel | ✔ | ✔ | non vérifié |
| Storyboard / réalisation multi-plans | ✔ | ✔ | ✔ | ✔ | partiel | ✔ | ✔ | ✔ | ✘ | ✔ | ✔ | partiel | ✔ | partiel | partiel | ✔ | partiel | ✘ | ✘ | partiel |
| Collaboration / actifs partagés | ✔ | non vérifié | non vérifié | ✔ | non vérifié | non vérifié | non vérifié | non vérifié | ✘ | non vérifié | ✔ | ✔ | ✔ | ✔ | ✔ | non vérifié | non vérifié | ✔ | ✔ | non vérifié |

## Prix par seconde, du moins cher au plus cher

**Tri numérique des configurations chiffrables**, pas classement de qualité ou de coût d'un film terminé. La nature du travail est indiquée : un avatar audio-guidé, une édition de tournage et une vidéo créée à partir d'un prompt ne sont pas des substituts parfaits. La durée est celle de la sortie. Les lignes régulières et promotionnelles Pika sont volontairement séparées. Les autres forfaits et configurations restent dans leurs fiches.

| Rang | Concurrent, route et travail | Résolution / durée du calcul | Calcul | USD/seconde | Condition / source |
|---|---|---|---|---:|---|
| 1 | Pika API — H3 Flex, génération | 1080p, exemple 5 s | 0,175 ÷ 5 | **0,03500** | Prix de lancement affiché, échéance du tarif non vérifiée[^PI3] |
| 2 | Hedra API — Character 3, avatar | 1080p, exemple 10 s | 0,625 ÷ 10 | **0,06250** | Audio fourni ; voix supplémentaire exclue[^HE1] |
| 3 | Pika API — H3 Flex, génération | 1080p, exemple 5 s | 0,35 ÷ 5 | **0,07000** | Prix régulier affiché à côté de la promotion[^PI3] |
| 4 | Runway API — Gen-4.5, génération | **720p, maximum natif documenté**, 5 s | 60 ÷ 5 × 0,01 | **0,12000** | Agrandissement exclu[^RW4][^RW8] |
| 5 | MiniMax API — H3, génération | 2K, exemple 5 s | 0,65 ÷ 5 | **0,13000** | Sans vidéo de référence ni supplément d'entrée[^MM3] |
| 6 | LTX API — 2.5 Pro, génération | 1080p, 6 s | 1,02 ÷ 6 | **0,17000** | Tarif direct de sortie[^LX4][^LX5] |
| 7 | Luma API — Ray 3.2, génération | 1080p SDR, 5 s | 400 ÷ 5 × 0,003 | **0,24000** | Taux catalogue par défaut, hors contrat[^LU2][^LU3] |
| 8 | Runway API — Aleph 2.0, **édition** | 1080p, exemple 5 s | 140 ÷ 5 × 0,01 | **0,28000** | Une vidéo source est nécessaire[^RW2][^RW4] |
| 9 | Runway Standard — Gen-4.5, génération | **720p, maximum natif documenté**, 5 s | 60 ÷ 5 × 15/625 | **0,28800** | Forfait mensuel, crédits entièrement consommés[^RW3][^RW8] |
| 10 | Luma API — Ray 3.2, génération | 1080p SDR, 10 s | 1 200 ÷ 10 × 0,003 | **0,36000** | Même modèle, durée plus chère par seconde[^LU2][^LU3] |
| 11 | LTX API — 2.5 Pro, génération | 4K, 6 s | 2,34 ÷ 6 | **0,39000** | Palier supérieur facultatif[^LX4][^LX5] |
| 12 | Higgsfield API — Cinema 4.0, génération | **720p maximum API documenté**, 5 s | 108 000 ÷ 5 × 0,0214/1 000 | **0,46224** | 16:9, 24 i/s, sans vidéo d'entrée[^HF4] |
| 13 | BytePlus API — Seedance 2.5, génération | 1080p, 5 s | 2,843 ÷ 5 | **0,56860** | Exemple officiel estimé ; sans vidéo d'entrée[^SD4] |
| 14 | Runway Standard — Aleph 2.0, **édition** | 1080p, exemple 5 s | 140 ÷ 5 × 15/625 | **0,67200** | Allocation totale du forfait mensuel à l'édition[^RW2][^RW3] |

**Autres chiffres utiles, exclus du tri ci-dessus :**

- **Higgsfield application : 0,784 $/s en 1080p**, calcul du billet officiel sous l'hypothèse Plus 49 $/1 000 crédits ; offre actuelle au paiement **non vérifiée**.[^HF2][^HF3]
- **Google application : 0,059925 $/s en 1080p agrandi**, sous l'hypothèse du prix Plus US publié en janvier ; tarif actuel et Québec **non vérifiés**. Omni API : **0,10136 $/s de sortie 720p**, plus entrées/texte ; coût 1080p **non vérifié**.[^GO3][^GO8][^GO9]
- **Runway Gen-4.5 est classé à son maximum natif documenté, 720p** ; le supplément total pour une livraison agrandie en 1080p demeure **non vérifié**.[^RW8]
- **Autodesk Lite : 0,095238 $/s traitée en 1080p**, calcul Live Action/Animation ; il ne chiffre pas Seedance ou un autre modèle génératif. Ne pas le présenter comme prix texte→vidéo.[^AU3][^AU4]
- **Vidu Q4 Preview 4K API : 2,4375 RMB/s**, grille régionale, sans conversion en USD. Prix 1080p mondial **non vérifié**.[^VI3]
- **OpenArt, Kling, Krea, Magnific, Leonardo : prix/s du phare en 1080p non vérifiés** pour les configurations demandées. Luma, MiniMax, Pika, LTX et Hedra : prix/s application en haute résolution **non vérifiés** malgré un tarif API exploitable. Voir les valeurs manquantes et formules dans chaque fiche.
- **Dreamina : 1080p application non vérifié** ; les promotions US 720p ne sont pas classées comme prix 1080p. **Moonvalley : sur contact, coût/s non vérifié. Sora : retiré. Meshy et Tripo : sans objet pour des secondes de vidéo.**[^SD3][^MV3][^SO2][^ME3][^TR1]

## Dix tendances observables à l'automne 2026

Il s'agit d'une synthèse des offres visibles au 3 novembre, pas de dix inventions toutes lancées en automne. Chaque tendance est appuyée par **deux pages officielles ouvertes**. L'ampleur de l'adoption et la qualité en production n'ont pas été mesurées.

1. **Le studio arrive dans Claude et ChatGPT.** Higgsfield expose un MCP et un plugin ChatGPT ; Pika apporte le 16 octobre des panneaux interactifs et une timeline dans ChatGPT. La proposition produit devient « poursuivre le brief dans le même contexte », avec interface visuelle dans la conversation. Sources : Higgsfield MCP et lancement Pika ChatGPT.[^HF7][^PI4]

2. **Le brouillon devient une étape commerciale explicite.** Flow permet d'explorer en 360p puis d'agrandir ; Pika Flex facture la différence pour finir une prise basse résolution. Le point différenciant est la continuité entre la prise choisie et le master, pas seulement un bouton de génération bon marché. Sources : mise à jour Flow du 27 août et page Flex.[^GO1][^PI3]

3. **Les références deviennent des entrées de direction multimodales.** Kling 4.0 combine images, vidéos, sujets et voix ; Seedance 2.5 prend de nombreux médias avec des rôles distincts. Le prompt doit expliquer quelle référence guide l'identité, le mouvement, la caméra ou le son. Sources : fonction Kling 4.0 et lancement ByteDance.[^KL2][^SD1]

4. **Les plans de 30 secondes deviennent des séquences dirigées.** Cinema 4.0 et Seedance 2.5 proposent des sorties de cette durée avec changements de plans et continuité. Cela réduit une partie de l'assemblage ; cela ne garantit pas la justesse du montage ni un film fini en une seule requête. Sources : changelog Higgsfield et lancement Seedance.[^HF1][^SD1]

5. **La 4K s'accompagne de chemins de finition différents.** Pika distingue génération basse résolution et finition hébergée ; LTX documente des paliers jusqu'à 4K pour Fast et Pro. « Sortie 4K », « natif 4K », HDR et agrandissement sont des caractéristiques à relever séparément dans un devis. Sources : lancement Flex et matrice LTX-2.5.[^PI1][^LX4]

6. **La révision d'une vidéo existante devient un produit central.** Aleph 2.0 part d'une image modifiée puis propage l'édition ; OpenArt SwitchX utilise la vidéo source pour préserver le sujet pendant les changements de décor, d'éclairage ou de zone. Cela transforme une demande de correction client en parcours dédié. Sources : annonce Runway Edit Studio et documentation SwitchX.[^RW2][^OA4]

7. **Le temps réel se spécialise en avatars et flux éditables.** Runway Characters est conçu pour les personnages interactifs ; Vidu annonce S2 Avatar et S2 Editing pour interaction et modification d'un flux. Cela diffère du temps de calcul réduit d'un clip hors ligne : le benchmark DiT de Pika ne prouve pas une conversation vidéo interactive. Sources : documentation Characters et changelog Vidu.[^RW6][^VI2]

8. **Les mondes explorables et les jeux jouables élargissent le périmètre.** Project Genie reste un prototype de mondes interactifs ; Higgsfield Playable, annoncé le 26 octobre, produit un jeu jouable à partir d'une description ou d'un gameplay. Ce sont deux mécanismes distincts : monde généré interactif et fabrication d'un jeu. Ils ne démontrent pas un export 3D ou un moteur de jeu universel. Sources : lancement Project Genie et changelog Higgsfield.[^GO10][^HF1]

9. **Le graphe professionnel devient une application simple partageable.** Les Flows Magnific cachent les nœuds derrière des entrées ; Krea documente Apps, Nodes et agent construisant des nœuds. Un spécialiste prépare le processus, l'équipe réutilise le résultat depuis un formulaire ou un agent. Sources : documentation Flows et changelog Krea du 27 octobre.[^MA4][^KR2]

10. **L'audio est co-généré, puis rendu éditable.** H3 produit vidéo et audio stéréo ensemble ; Flex ajoute la séparation des composantes sonores pour la finition. Pour le studio, cohérence audiovisuelle et possibilité de remplacer une voix, une ambiance ou une musique deviennent deux exigences complémentaires. Sources : publication ouverte H3 et lancement Flex.[^MM2][^PI1]

## Ce que cette vérification corrige dans le portrait précédent

Les changements les plus nets sont le retrait de Sora, la fin du libre-service Moonvalley, la confirmation officielle du renommage Magnific et la distinction entre H3 et le post-entraînement Pika H3 Flex. Flow demeure un produit qui héberge Omni ; Cinema Studio 4.0 utilise Seedance 2.5, tandis que DoP est le modèle maison distinct de Higgsfield. Les grilles accessibles ne permettent pas de confirmer tous les anciens prix : **une précision arithmétique ne compense pas un tarif de départ incertain**.[^SO1][^SO2][^MV3][^MA1][^PI1][^GO2][^HF8][^HF9]

Pour Nexora, la comparaison exploitable porte surtout sur les parcours documentés : références persistantes, aperçu avant dépense, retouche locale, passage du brouillon au master, réutilisation de workflows et livraison dans les outils de travail. Ce constat n'ajoute pas une nouvelle feuille de route aux documents existants.

## Registre des sources officielles

Chaque note ci-dessous associe l'URL réellement ouverte à sa date de consultation. Une page vide ou incomplète est conservée uniquement pour expliquer un « non vérifié ». Les URL ayant échoué sans ouverture exploitable ne servent pas de preuve factuelle.

[^HF1]: [Higgsfield — changelog, notamment Cinema 4.0, audio, Intone et Playable](https://higgsfield.ai/creator-hub/changelog) — **consulté le 3 novembre 2026**.

[^HF4]: [Higgsfield API — Cinema Studio 4.0, facturation aux jetons et résolutions](https://open.higgsfield.ai/models/higgsfield/cinema-studio/4.0/playground) — **consulté le 3 novembre 2026**.

[^HF5]: [Higgsfield API — catalogue officiel](https://open.higgsfield.ai/explore) — **consulté le 3 novembre 2026**.

[^HF6]: [Higgsfield — Camera Controls, galerie de presets](https://higgsfield.ai/camera-controls) — **consulté le 3 novembre 2026**.

[^HF7]: [Higgsfield — MCP et plugin ChatGPT](https://higgsfield.ai/mcp) — **consulté le 3 novembre 2026**.

[^HF2]: [Higgsfield — guide Cinema Studio 4.0, contrôles et consommation](https://higgsfield.ai/blog/cinema-studio-4-0-complete-guide) — **consulté le 3 novembre 2026**.

[^HF3]: [Higgsfield — Pricing Explained, billet du 24 octobre 2026](https://higgsfield.ai/blog/higgsfield-pricing-explained) — **consulté le 3 novembre 2026**.

[^HF0]: [Higgsfield — page de prix, montants non restitués](https://higgsfield.ai/pricing) — **consulté le 3 novembre 2026**.

[^OA1]: [OpenArt — outils et catalogue](https://openart.ai/) — **consulté le 3 novembre 2026**.

[^OA3]: [OpenArt — usages Seedance 2.5, Director, voix et résolution](https://openart.ai/blog/seedance-2-5-use-cases/) — **consulté le 3 novembre 2026**.

[^OA4]: [OpenArt — SwitchX de Beeble, VFX et édition de vidéo](https://openart.ai/ai-model/switchx/) — **consulté le 3 novembre 2026**.

[^OA5]: [OpenArt — Worlds](https://openart.ai/features/openart-worlds/) — **consulté le 3 novembre 2026**.

[^OA6]: [OpenArt — Director, parcours court métrage](https://openart.ai/suite/director?quickStart=short-film) — **consulté le 3 novembre 2026**.

[^OA2]: [OpenArt — plans et crédits, page ouverte sans calculateur détaillé par modèle](https://openart.ai/pricing) — **consulté le 3 novembre 2026**.

[^KL1]: [Kling — bilan de déploiement 4.0, 27 octobre 2026](https://kling.ai/blog/kling4-work-creative-vision-production) — **consulté le 3 novembre 2026**.

[^KL2]: [Kling — fonctionnalités 4.0, y compris les mentions coming soon](https://kling.ai/feature/kling-4-ai-video-generation) — **consulté le 3 novembre 2026**.

[^KL4]: [Kling — abonnement, ouverture limitée à un titre](https://kling.ai/app/subscribe) — **consulté le 3 novembre 2026**.

[^KL5]: [Kling — page API/pricing, barème non restitué](https://kling.ai/dev/pricing) — **consulté le 3 novembre 2026**.

[^KL3]: [Kling — guide officiel des crédits 3.0, juillet 2026 ; pas un devis 4.0](https://kling.ai/blog/kling-video-3-0-credit-cost-guide?tab=all) — **consulté le 3 novembre 2026**.

[^RW1]: [Runway — changelog produit](https://runway.com/changelog) — **consulté le 3 novembre 2026**.

[^RW2]: [Runway — lancement Aleph 2.0 et Edit Studio](https://runway.com/news/introducing-aleph-2-and-edit-studio) — **consulté le 3 novembre 2026**.

[^RW5]: [Runway Dev — catalogue des modèles, dates propres au catalogue API](https://docs.dev.runwayml.com/guides/models/) — **consulté le 3 novembre 2026**.

[^RW3]: [Runway — abonnements, crédits et exemples de consommation](https://runway.com/pricing) — **consulté le 3 novembre 2026**.

[^RW6]: [Runway Dev — Characters](https://docs.dev.runwayml.com/characters/) — **consulté le 3 novembre 2026**.

[^RW4]: [Runway Dev — prix API et unité de crédit](https://docs.dev.runwayml.com/guides/pricing/) — **consulté le 3 novembre 2026**.

[^LU1]: [Luma Agents — modèles et capacités](https://docs.agents.lumalabs.ai/guides/model/) — **consulté le 3 novembre 2026**.

[^LU2]: [Luma Agents — crédits par génération, SDR et HDR](https://docs.agents.lumalabs.ai/guides/pricing/) — **consulté le 3 novembre 2026**.

[^LU3]: [Luma Agents — conversion crédits/dollars, taux catalogue et contrats](https://docs.agents.lumalabs.ai/guides/usage/) — **consulté le 3 novembre 2026**.

[^PI1]: [Pika — lancement H3 Flex, 29 octobre 2026](https://pika.art/blog/pika-h3-flex) — **consulté le 3 novembre 2026**.

[^PI2]: [Pika — plans, crédits et consommation par modèle](https://pika.art/pricing) — **consulté le 3 novembre 2026**.

[^PI3]: [Pika — H3 Flex, tarifs API réguliers et de lancement, finition et audio](https://pika.art/pika-h3-flex) — **consulté le 3 novembre 2026**.

[^PI4]: [Pika — lancement du plugin ChatGPT et de sa timeline, 16 octobre 2026](https://pika.art/blog/pika-chatgpt-plugin) — **consulté le 3 novembre 2026**.

[^MM1]: [MiniMax — lancement H3, 31 juillet 2026](https://www.minimax.io/blog/minimax-h3) — **consulté le 3 novembre 2026**.

[^MM2]: [MiniMax — publication des poids H3, 3 août 2026](https://www.minimax.io/news/minimax-h3-open-source) — **consulté le 3 novembre 2026**.

[^MM3]: [MiniMax API — prix actuels vidéo, variantes H3, voix et outils](https://platform.minimax.io/docs/pricing/overview?tab=api-enterprise) — **consulté le 3 novembre 2026**.

[^MM4]: [MiniMax Design — agent, canvas, actifs locaux et timeline](https://design.minimax.io/) — **consulté le 3 novembre 2026**.

[^MM5]: [Hailuo — souscription, écran Loading sans tarifs exploitables](https://hailuoai.video/subscribe) — **consulté le 3 novembre 2026**.

[^GO1]: [Google — nouveaux contrôles Flow avec Omni 1.1, 27 août 2026](https://blog.google/innovation-and-ai/models-and-research/google-labs/new-creative-controls-google-flow/) — **consulté le 3 novembre 2026**.

[^GO2]: [Google Flow Help — modèles et fonctions pris en charge](https://support.google.com/flow/answer/16352836?hl=en) — **consulté le 3 novembre 2026**.

[^GO4]: [Google Flow Help — agent, instructions et génération dans le projet](https://support.google.com/flow/answer/17093911?hl=en&ref_topic=16908930) — **consulté le 3 novembre 2026**.

[^GO5]: [Google Flow Help — édition des vidéos et construction de scènes](https://support.google.com/flow/answer/16935718?hl=en&ref_topic=16908930) — **consulté le 3 novembre 2026**.

[^GO7]: [Google One Help — avantages Plus et Flow Music, solde séparé](https://support.google.com/googleone/answer/16882689) — **consulté le 3 novembre 2026**.

[^GO3]: [Google Flow Help — allocations et coûts en crédits par génération](https://support.google.com/flow/answer/16526234?hl=en) — **consulté le 3 novembre 2026**.

[^GO6]: [Google One — plans commerciaux, montants non restitués dans la page ouverte](https://one.google.com/about/google-ai-plans/?hl=en_US) — **consulté le 3 novembre 2026**.

[^GO8]: [Google — prix US publié au lancement AI Plus, 27 janvier 2026](https://blog.google/products-and-platforms/products/google-one/google-ai-plus-availability/) — **consulté le 3 novembre 2026**.

[^GO9]: [Google AI Studio — prix Gemini API, Omni 1.1 et jetons vidéo](https://aistudio.google.com/docs/pricing) — **consulté le 3 novembre 2026**.

[^SO1]: [OpenAI — page Sora annonçant son indisponibilité depuis le 26 avril 2026](https://openai.com/index/sora/) — **consulté le 3 novembre 2026**.

[^SO2]: [OpenAI API — dépréciations et retrait Sora/Videos API au 24 septembre 2026](https://developers.openai.com/api/docs/deprecations) — **consulté le 3 novembre 2026**.

[^KR4]: [Krea — prix API en USD séparés des plans application](https://www.krea.ai/app/api/pricing) — **consulté le 3 novembre 2026**.

[^SD1]: [ByteDance Seed — lancement Seedance 2.5, 31 juillet 2026](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5) — **consulté le 3 novembre 2026**.

[^SD2]: [BytePlus — offre et accès API Seedance 2.5, prix des packs non chargés](https://ai.byteplus.com/en/product/seedance) — **consulté le 3 novembre 2026**.

[^SD3]: [Dreamina — prix Seedance, conditions US, premier mois et renouvellement](https://dreamina.capcut.com/seedance/seedance-price) — **consulté le 3 novembre 2026**.

[^SD4]: [BytePlus ModelArk — tarification vidéo, formule et exemples Seedance 2.5](https://ai.byteplus.com/ark/region:ap-southeast-1/docs/model-pricing) — **consulté le 3 novembre 2026**.

[^LX1]: [LTX — introduction API LTX-2.5 le 11 août 2026](https://docs.ltx.io/api-changelog/2026/8/11) — **consulté le 3 novembre 2026**.

[^LX2]: [LTX — changelog API et extensions de fonctions](https://docs.ltx.io/api-changelog) — **consulté le 3 novembre 2026**.

[^LX3]: [LTX Studio — plans, crédits, Elements, storyboards et collaborateurs](https://ltx.io/studio/pricing) — **consulté le 3 novembre 2026**.

[^LX4]: [LTX — matrice LTX-2.5, durées, résolutions et endpoints](https://docs.ltx.io/models/ltx-2-5/) — **consulté le 3 novembre 2026**.

[^LX5]: [LTX — tarifs API par seconde](https://docs.ltx.io/pricing) — **consulté le 3 novembre 2026**.

[^KR1]: [Krea — plans et unités ; estimations de volumes](https://www.krea.ai/pricing) — **consulté le 3 novembre 2026**.

[^KR2]: [Krea — changelog, Agent, Nodes, Krea 3 et retraits de modèles](https://www.krea.ai/docs/changelog) — **consulté le 3 novembre 2026**.

[^KR3]: [Krea — API, catalogue, outils, plugins et workflows](https://www.krea.ai/features/api) — **consulté le 3 novembre 2026**.

[^KR5]: [Krea — API Seedance, modèles, résolutions et facturation séparée](https://www.krea.ai/docs/developers/seedance) — **consulté le 3 novembre 2026**.

[^KR6]: [Krea — documentation, entrée développeurs et fonctions](https://www.krea.ai/docs) — **consulté le 3 novembre 2026**.

[^MA1]: [Magnific — Freepik is now Magnific, 28 avril 2026](https://www.magnific.com/freepik) — **consulté le 3 novembre 2026**.

[^MA2]: [Magnific — prix des plans et allocations annuelles](https://www.magnific.com/pricing) — **consulté le 3 novembre 2026**.

[^MA3]: [Magnific — génération vidéo, visual prompts, multi-shot et personnages](https://www.magnific.com/ai/docs/video-generator) — **consulté le 3 novembre 2026**.

[^MA4]: [Magnific — Flows, exécution simple, MCP/API et coût cumulé](https://www.magnific.com/ai/docs/flows) — **consulté le 3 novembre 2026**.

[^MA5]: [Magnific — collaboration et partage Spaces](https://www.magnific.com/ai/docs/collaboration-and-sharing) — **consulté le 3 novembre 2026**.

[^MA6]: [Magnific — index officiel des outils image, vidéo, audio et 3D](https://www.magnific.com/ai/docs) — **consulté le 3 novembre 2026**.

[^MA7]: [Magnific — plans, crédits mensuels/annuels et limites](https://www.magnific.com/ai/docs/plans-and-pricing) — **consulté le 3 novembre 2026**.

[^LE1]: [Leonardo — guide des modèles vidéo, mise à jour du 10 août 2026](https://leonardo.ai/news/ai-video-models) — **consulté le 3 novembre 2026**.

[^LE2]: [Leonardo — générateur vidéo et Blueprints](https://leonardo.ai/ai-video-generator) — **consulté le 3 novembre 2026**.

[^LE3]: [Leonardo — éditeur/restyle vidéo](https://leonardo.ai/ai-video-editor) — **consulté le 3 novembre 2026**.

[^LE4]: [Leonardo — plans individuels, équipes et API](https://leonardo.ai/pricing) — **consulté le 3 novembre 2026**.

[^LE5]: [Leonardo Help — tokens, devis, report et mode ralenti](https://intercom.help/leonardo-ai/en/articles/9044700-tokens-frequently-asked-questions) — **consulté le 3 novembre 2026**.

[^HE1]: [Hedra — Character 3, date historique et prix par résolution](https://www.hedra.com/models/video/hedra/character-3) — **consulté le 3 novembre 2026**.

[^HE2]: [Hedra — catalogue vidéo, image et audio](https://www.hedra.com/models) — **consulté le 3 novembre 2026**.

[^HE3]: [Hedra Studio — agent visuel, espaces partagés et Elements](https://www.hedra.com/studio) — **consulté le 3 novembre 2026**.

[^HE4]: [Hedra — tarifs API et catégories de services](https://www.hedra.com/pricing) — **consulté le 3 novembre 2026**.

[^HE5]: [Hedra — plateforme développeur et MCP, solde API distinct](https://www.hedra.com/develop) — **consulté le 3 novembre 2026**.

[^VI1]: [Vidu — page Q4, voix, références et résolutions](https://www.vidu.com/vidu-q4) — **consulté le 3 novembre 2026**.

[^VI2]: [Vidu API — changelog Q4 Preview, S2, audio et montage guidé](https://platform.vidu.com/docs/api-reference/updates) — **consulté le 3 novembre 2026**.

[^VI3]: [Vidu API — grille accessible RMB, Q4 Preview 4K et crédits](https://platform.vidu.com/docs/overview/pricing) — **consulté le 3 novembre 2026**.

[^VI4]: [Vidu — agent marketing, skills et storyboard](https://www.vidu.com/vidu-claw) — **consulté le 3 novembre 2026**.

[^VI5]: [Vidu — page de prix application, chargement des plans incomplet](https://www.vidu.com/pricing) — **consulté le 3 novembre 2026**.

[^MV1]: [Moonvalley — showcase et versions Marey](https://www.moonvalley.com/showcase) — **consulté le 3 novembre 2026**.

[^MV2]: [Moonvalley — Marey, caméra, références et images clés](https://www.moonvalley.com/marey) — **consulté le 3 novembre 2026**.

[^MV3]: [Moonvalley — fin des abonnements libre-service et partenariats](https://www.moonvalley.com/selfserve) — **consulté le 3 novembre 2026**.

[^ME1]: [Meshy Help — modèles 7.1, 7, 6 et 6 Lite](https://help.meshy.ai/en/articles/15697060-meshy-7-vs-meshy-6-vs-meshy-6-lite-which-ai-model-should-you-use) — **consulté le 3 novembre 2026**.

[^ME2]: [Meshy — lancement N1, texturage natif 3D, 3 novembre 2026](https://www.meshy.ai/blog/meshy-n1-texture) — **consulté le 3 novembre 2026**.

[^ME3]: [Meshy — outils 3D, agent, MCP et intégrations](https://www.meshy.ai/) — **consulté le 3 novembre 2026**.

[^ME4]: [Meshy — prix officiels, devise GBP restituée](https://www.meshy.ai/pricing) — **consulté le 3 novembre 2026**.

[^TR1]: [Tripo — modèles et versions, géométrie et images](https://developers.tripo3d.ai/en/docs/models-and-versions) — **consulté le 3 novembre 2026**.

[^TR2]: [Tripo — H3.1, prix API et versions de texturage](https://developers.tripo3d.ai/en/models/v3-1) — **consulté le 3 novembre 2026**.

[^TR3]: [Tripo — plans Studio et capacités](https://www.tripo3d.ai/pricing) — **consulté le 3 novembre 2026**.

[^TR4]: [Tripo — plugin Codex](https://developers.tripo3d.ai/en/docs/codex-plugin) — **consulté le 3 novembre 2026**.

[^AU1]: [Autodesk Flow Studio — présentation, modèles partenaires et scène 3D](https://www.autodesk.com/products/flow-studio/overview) — **consulté le 3 novembre 2026**.

[^AU2]: [Autodesk Flow Studio — fonctions et formats exportables](https://www.autodesk.com/products/flow-studio/product-details) — **consulté le 3 novembre 2026**.

[^AU3]: [Autodesk — guide tarifaire Flow Studio du 28 septembre 2026](https://blogs.autodesk.com/media-and-entertainment/2026/09/28/autodesk-flow-studio-pricing-and-subscription-guide/) — **consulté le 3 novembre 2026**.

[^AU4]: [Autodesk UK — barème crédits/seconde par type de traitement](https://www.autodesk.com/uk/products/flow-studio/compare) — **consulté le 3 novembre 2026**.

[^GO10]: [Google — lancement du prototype Project Genie, 29 janvier 2026](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/) — **consulté le 3 novembre 2026**.


[^HF8]: [Higgsfield — guide DoP, modèle propriétaire et presets](https://higgsfield.ai/creator-hub/help-center/ai-models/how-do-i-use-dop) — **consulté le 3 novembre 2026**.

[^HF9]: [Higgsfield — guide Cinema Studio, moteur Seedance 2.5 et collaboration](https://higgsfield.ai/creator-hub/help-center/tools/how-do-i-use-cinema-studio) — **consulté le 3 novembre 2026**.

[^RW7]: [Runway — annonce Gen-4.5, 1er décembre 2025](https://runway.com/research/introducing-runway-gen-4.5) — **consulté le 3 novembre 2026**.

[^RW8]: [Runway Help — Gen-4.5, résolution, durée et crédits](https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5) — **consulté le 3 novembre 2026**.

[^RW9]: [Runway — GWM Worlds 2, aperçu de recherche du 3 septembre 2026](https://runway.com/research/introducing-gwm-worlds-2) — **consulté le 3 novembre 2026**.
