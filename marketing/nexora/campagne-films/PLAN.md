# Campagne de films Nexora : usine, typographie, plan (02/11/2026)

Huit films pour faire connaître ce que Nexora offre. Le premier (WorkStudio) est fait ; les sept autres sont des briefs à
remplir et à lancer avec l'usine, dans l'ordre du §4. Tout ce qui touche à la marque (nom, logo, adresse, couleurs, polices)
vit dans `marque.json` : le nom va changer, on modifie ce fichier et on relance `rendu revue livrer`.

## 1. L'usine (ce qu'un agent fait pour produire un film)

```
marketing/nexora/campagne-films/
  marque.json                 marque de toute la campagne (seul endroit)
  usine/usine.py              brief → films : valider · plaques · captures · montage · animatique · rendu · revue · livrer
  usine/monter.py             rendu (réutilise video-v4/monter_v4.py + video-v3/couches.py et sfx_v3.py)
  usine/typo.py               typographie cinétique
  films/<film>/brief.json     LE fichier à remplir (copier films/workstudio/brief.json, c'est le gabarit commenté par l'exemple)
  films/<film>/*.py|*.mjs     outils propres au film (capture Playwright, prompts de plaques, musique)
```

Marche à suivre (un film = une journée d'agent, GPU en file normale) :
1. Copier `films/workstudio/` vers `films/<film>/`, réécrire `brief.json` : concept, public, `segments` (une fois chacun),
   `versions` (ordre + surcharges `d`, `t_marque`…), `textes` fr/en, `musique`, `commandes`.
2. Musique : adapter `musique.py` (Music3, 2 graines), puis **mesurer** la piste (énergie par 0,25 s, autocorrélation : voir
   l'analyse dans l'historique du film WorkStudio) : temps, longueur des phrases, coup fort. Écrire `bpm`, `subdivision` et
   `repere_source`. Ne pas croire le BPM demandé : Music3 a rendu 83,5 BPM pour 120 demandés.
3. Images : `commandes.captures` (Playwright sur l'application réelle, une étiquette par phase : `repos`, `execution`…) et/ou
   `commandes.plaques` (images clés Qwen-Image d'abord, vérifiées une à une, puis vidéos H3 : recette `h3-max` pour les plans
   héros, `h3-fast` pour les plans de remplissage ; voir `creative/video-v4/plans_v4.py`). Regarder **chaque** plaque : H3
   imite spontanément des franchises connues, met du texte et des logos ; rejeter.
4. `python3 usine/usine.py films/<film>/brief.json valider montage animatique` : le validateur liste chaque violation avec
   l'endroit, la valeur attendue et la correction (coupe hors grille musicale → durée proposée ; temps de lecture
   0,3 s/mot + 0,5 s ; titre > 7 mots ; traduction manquante ; mot interdit ; fonction « En préparation » sans étiquette).
   L'animatique (demi-définition, 10 s de calcul) est la porte : on la regarde avant le rendu.
5. `… rendu revue` : 12 fichiers (2 formats × 2 langues × long/30/15), planches et `revue.json` (LUFS, crête vraie,
   délai de la preuve, densité de texte, plan moyen). Les mesures d'abord ; la note sévère ensuite, écrite à la main dans
   `brief.json › revue` (grille du §3). Ne jamais confier la note à un juge LLM seul (accord faible, biais d'ordre) ; si on en
   utilise un, deux passes en ordre inversé, et lui donner les chiffres audio plutôt que « écoute ».
6. Corriger seulement les postes faibles, relancer `rendu revue` (cache par segment ; changer `VERSION_RENDU` dans
   `monter.py` après une modification du code de rendu, sinon les segments en cache restent anciens).
7. `… livrer` : finaux dans `~/nexora-creative-data/promo/montage/Nexora-<nom>-<fmt>-<langue>[-30|-15].mp4`, web H.264
   ≤ 25 Mo `site-medias/film-<film>-*.mp4`, affiche, entrée `films.<film>` de `site-medias/manifest-campagne.json`.
   Purger ensuite `<travail>/rendu` (le disque de pc6 est à 99 %).

Effets déclarés : `valider`, `revue` lisent ; `montage`, `animatique`, `rendu` écrivent dans le dossier de travail (idempotent,
cache) ; `plaques` occupe le GPU ; `captures` agit sur l'application réelle ; `livrer` remplace les fichiers livrés du film.

Segments : `noir` (fond d'encre + textes), `ecran` (capture recadrée dans une carte arrondie, texte dans la marge sombre ;
`cadre`/`cadre_v` = [t, cx, cy, largeur] en fractions de la capture, un cadrage par format ; `curseur` + `clics` = curseur
dessiné aux positions réelles des clics), `plan` (plaque H3, étalonnage pellicule V3), `ab`, `chrono`, `fin` (carton).
`"base": "<id>"` fait hériter un segment d'un autre ; `"preuve": true` marque le plan qui prouve le produit (mesuré).
Musique : posée pour que `repere_source` tombe au début de `repere_segment` ; arrêt net sur `silence` ; `queue` = un passage
calme de la même piste sous le carton (son coup fort fait apparaître le nom : `t_marque`).

## 2. La typographie cinétique (`usine/typo.py`)

Geist SemiBold en affiche, interlettrage −2 %, crénage conservé ; JetBrains Mono pour les surtitres et citations. Tout est
tracé à la résolution finale à chaque image (net à toute taille, aucun agrandissement de bitmap).
- `titre` : mots révélés un à un sous un cache de ligne (montée de 0,9 ligne, 0,07 s entre les mots, 0,42 s par mot) ;
  `*mot*` = orange signal ; `|` = retour à la ligne voulu (« Il trie.|Il *rédige.* »). Le corps se réduit seul si la ligne
  déborde de sa zone.
- `impact` : phrase seule au centre, arrivée échelle 1,10 → 1 et flou 14 → 0 px en 0,35 s (sur un coup de musique).
- `pile` : lignes révélées l'une après l'autre (0,14 s). `sur` : surtitre mono en capitales +12 %, puce orange
  (« CAPTURE RÉELLE »). `prepa` : étiquette « En préparation » à contour orange, **obligatoire** sur toute fonction non livrée.
  `citation` : texte cité, frappé lettre à lettre.
- Zones et marges sûres : colonne gauche (16:9), bande haute (9:16, au-dessus de la carte), bas, centre ; 6 % des côtés en
  16:9 ; 8 % des côtés, 10,5 % en haut en 9:16. Sortie : fondu de 0,22 s.
- Écriture : ≤ 7 mots par titre, une seule idée, verbes concrets, rien qu'on ne peut prouver à l'écran ; pas de « ce n'est
  pas X, c'est Y », pas de listes « sans X, sans Y, sans Z » ; un seul mot d'accent par ligne.

## 3. Grille de revue sévère (chaque film)

Concept · preuve rapide (le produit fait quelque chose de vrai avant 12 s) · textes · rythme · son · finition · authenticité,
sur 10, moyenne = note. Porte de livraison : 8. Noter comme un étranger qui n'a jamais vu le produit.

## 4. Les films, par ordre d'impact

Estimations GPU : image clé Qwen ≈ 0,5 min ; plan H3 `h3-fast` ≈ 1,5 min, `h3-max` ≈ 3 min (5 s) ; Music3 ≈ 2,5 min par
graine ; rendu complet des 12 fichiers ≈ 5 min CPU. Ce sont des estimations, sauf Music3 (153 s mesurées) et le rendu.

### (a) WorkStudio : « Il fait le travail. Vous gardez la main. » — FAIT, v2 (46,7 / 29,8 / 15,5 s)
Concept : deux vrais courriels de clients (boulangerie fictive) font tourner le workflow réel « Tri du courrier entrant » : tri,
brouillon, pause de validation humaine, accord sur la page de reprise, envoi SMTP vers une boîte de test (Mailpit), journal
d'exécution et trace ; puis l'étendue (vue Étapes, blocs ajoutés par glisser-déposer). Quatre exécutions capturées (fr-CA et en-CA :
l'application suit l'en-tête Accept-Language, l'interface anglaise est donc réelle). Preuve à 0,4 s, clic d'accord à 9,3 s, courriel reçu
à 14,4 s. Musique : celle de la v1 (83,478 BPM mesurés, coup à 11,5 s posé sur le clic d'accord). Master : loudnorm deux passes
(étape `master`) −14 LUFS, crête ≤ −1,6 dBTP. Note sévère : **8,1** (voir `films/workstudio/brief.json › revue`, faiblesses comprises).
Refaire : `node connexion.mjs <témoins>`, `python3 workflow.py creer en` (deuxième workflow), `capturer.mjs` (4 cycles + étendue, ≈ 8 min),
`python3 construire_brief.py`, puis `usine.py brief.json valider montage rendu master revue livrer`.

### (b) Nexora, l'entreprise — 60/30/15 s · difficulté moyenne · GPU ≈ 25 min
Concept : « Un seul compte. Vos outils d'IA, au Québec. » Le panneau Nexora dans le navigateur : on passe d'un outil à
l'autre en un clic (WorkStudio, Creative, WebPilot, Assistant), chacun montré en train de faire une chose vraie, puis
l'espace infonuagique dont les agents peuvent utiliser le PC de l'utilisateur, **étiqueté « En préparation »**.
Réel aujourd'hui : WorkStudio (captures de ce film), Creative (captures V4), site et panneau (captures du site),
WebPilot si une session réelle tourne. Illustratif : agent de code, RAG, espace infonuagique (maquettes d'interface en code,
étiquette `prepa` à l'écran tout le temps). 60 s : 0–4 la question (« Combien d'outils pour une PME ? ») · 4–12 la preuve :
un clic, WorkStudio rédige · 12–40 un outil toutes les 5,75 s (une phrase de musique) · 40–50 « En préparation » · carton.
30 s : 3 outils. 15 s : 1 outil + carton. Musique : pulsation chaude, montée continue, 4 phrases.
Textes fr : « Vos outils d'IA. Un seul compte. » · « Il rédige vos réponses. » · « Il tourne vos vidéos. » · « Il cherche
pour vous. » · « Bientôt : vos agents sur votre poste. » · carton « Un compte. Tous vos outils d'IA. »
en : “Your AI tools. One account.” · “It drafts your replies.” · “It shoots your videos.” · “It searches for you.” ·
“Coming: your agents on your own PC.” · “One account. All your AI tools.”

### (c) Creative, deuxième film : « Votre pub en une phrase » — 30/15 s (60 s optionnel) · moyenne · GPU ≈ 60 min
Angle différent de la V4 (qui montrait l'étendue des genres) : un commerçant obtient une publicité de 15 s pour son commerce.
Réel : une vraie session du Producteur (capturer.mjs de la V4) sur « Une pub de 15 s pour une boulangerie de quartier :
le pain sort du four à l'aube » ; plans H3 `h3-max` du Producteur (4 plans), musique et carton du studio. Structure 30 s :
0–3 la phrase tapée · 3–6 le devis · 6–24 la pub finie, plein cadre · 24–30 « Une phrase. Votre pub. » + carton. 15 s :
phrase (2 s) → pub (10 s) → carton. Musique : celle que le Producteur a composée (c'est la preuve).
Textes fr : « Une phrase. » · « Le devis, avant le tournage. » · « Votre pub, prête à publier. » ; en : “One sentence.” ·
“The quote comes first.” · “Your ad, ready to post.” Pas de visage reconnaissable ; pas de marque sur les vitrines.

### (d) Infrastructure IA : « Vos modèles, chez vous » — 30/15 s · facile · GPU ≈ 15 min
Photos produits réelles (`~/nexora-creative-data/site-medias/photos-produits/` : la tour du fondateur et la machine compacte),
en mouvements de caméra calculés (parallaxe 2,5D, lumière qui glisse) + 2 plaques H3 de détail (ventilateur, voyants) à partir
des photos (image vers vidéo, `h3-fast`). Aucun nom de fabricant ni de puce à l'écran. Textes fr : « Un serveur d'IA dans
votre bureau. » · « Vos données restent ici. » · « Installé et suivi par Nexora. » (à confirmer par l'offre réelle avant
rendu) ; en : “An AI server in your office.” · “Your data stays here.” · “Set up and monitored by Nexora.”

### (e) Surveillance IA v2 — FAIT (33,3 / 29,1 / 14,9 s) · note sévère 7,6 · `films/surveillance/` (brief généré par `fabriquer_brief.py`)
Avec les plaques et la musique de la refonte (piste surv-v2 mesurée à 86,5 BPM) : ouverture sur la détection qui passe au rouge à 2,08 s sur le coup de musique, puis problème, détection d'entrepôt, alerte (pile : texto, courriel, tableau de bord, application), consigne, rapport. Livré : `site-medias/film-surveillance-v2-*`, masters dans `promo/montage/Nexora-Surveillance-IA-v2-*`. Faiblesses : voir `brief.json › revue`.
Plan d'origine :
Le film existant (`refonte-medias/montages/film-surveillance-*.json`) garde ses plans ; on remplace ses textes par le
système `typo.py` (titres révélés, surtitres « DÉTECTION EN DIRECT » en mono, preuve avant 5 s), on recoupe sur la grille de sa
musique et on ajoute les versions 9:16 avec bande de texte haute. Un brief qui pointe vers les plaques existantes suffit.

### (f) Réception virtuelle — 30/15 s · moyenne · GPU ≈ 30 min
Vérifier d'abord son état dans le registre des affirmations du site ; si elle n'est pas en service, étiquette `prepa` sur tout
le film. Réel possible : un appel ou un clavardage de test enregistré (son réel), sinon maquette. Concept : 23 h, un client
écrit ; la réception répond, prend le rendez-vous, et le matin le résumé attend. Textes fr : « 23 h. Un client écrit. » ·
« Elle répond. » · « Le rendez-vous est pris. » ; en : “11 p.m. A customer writes.” · “It answers.” · “The booking is made.”
Personnages : générer d'abord une banque d'entités (portraits détourés sur fond uni, nom en bas de la planche, décor en
panorama recadré en 3 angles), images clés avant toute vidéo, identité jugée par paires avec un seuil de fidélité (pas par
similarité d'empreintes), petit banc de continuité.

### (g) Modèles et API — FAIT MAIS NON PUBLIÉ (26,7 / 15,5 s) · note sévère 7,1 < 8 (porte) et < 7,5 · `films/modeles/`
Le catalogue réel du site est vide et l'API n'est pas ouverte : le film montre un terminal en code (étiqueté Aperçu) et les captures réelles de /modeles. Non livré dans site-medias ni dans le manifeste ; à refaire quand un modèle est publié (fiche, filtres, appel réels). Brouillons : `~/nexora-creative-data/promo/v5/modeles/brouillons/`. Accès au site : `socat TCP-LISTEN:18081 … EXEC:"ssh -T pc5-proxmox nc 192.168.1.121 80"` (le `ssh -L` est refusé par le nœud).
Plan d'origine :
Réel : un vrai appel `curl` à la passerelle (terminal filmé en code, clé masquée), la réponse en streaming, la fiche de
résidence des données d'un modèle sur le site. Le catalogue public est encore en brouillon : ne montrer que des modèles en
service, ou étiqueter. Textes fr : « Une clé. Plusieurs modèles. » · « Hébergés au Québec ou ailleurs : c'est écrit. » ;
en : “One key. Many models.” · “Hosted in Québec or elsewhere, and labelled.”

### (h) Code et RAG — 30/15 s · moyenne · GPU ≈ 10 min · **En préparation**
Illustratif : maquettes d'interface en code (pas de capture d'un produit non livré présentée comme réelle), étiquette `prepa`
visible tout le film. RAG : « Vos documents répondent, avec leurs sources. » ; Code : « Un agent de code, hébergé. » ;
en : “Your documents answer, with sources.” · “A hosted coding agent.”

Ordre d'exécution conseillé pour les agents suivants : (e) puis (g) (aucun GPU, rodent l'usine), (b), (c), (d), (f), (h).

## 5. Filmer WorkStudio (VM 203) : ce qu'il faut savoir

- Accès : relais TLS local `socat openssl-listen:8443,bind=127.0.0.1,fork,cert=<cert auto-signé> tcp:192.168.1.123:80` et Chromium lancé
  avec `--host-resolver-rules=MAP studio.nexora.ai:443 127.0.0.1:8443` (origine et témoins `Secure` exacts) ; Mailpit (sans port publié) par
  `ssh -f -N -L 127.0.0.1:18025:<ip du conteneur>:8025 nexora-workstudio`. La connexion est limitée (429) : une seule session
  (`connexion.mjs`, témoins dans un fichier privé hors dépôt, mot de passe lu sur la VM sans l'afficher).
- Les défauts de la v1 sont corrigés (proxy `front`, reprise après validation, sortie `mailpit` autorisée, bloc SMTP à la place du bloc API) ;
  la reprise puis l'envoi prennent environ 1,4 s après le clic.
- Workflows filmés : `films/workstudio/workflow.py` (fr et en, courriel 1 ou 2), captures : `capturer.mjs`. L'exécution réelle dure ≈ 3 s :
  le film l'étire (10 images) ; ne jamais ralentir un son ni prétendre que l'exécution est lente.

### (g) Modèles et API : « Une clé. Tous les modèles. » — FAIT (35,6 / 29,5 / 15,0 s) · note sévère 7,5 · `films/modeles/`
Parcours réel de la page `/modeles` (et `/en/modeles`) du site : `capturer.mjs` enregistre le flux d'images (CDP screencast) et le journal des gestes
(en-tête du site masqué : la marque va changer), `decouper.py` en tire des séquences à 30 images/s par segment et les temps du curseur, `fabriquer_brief.py`
écrit le brief. Accueil (réponse en continu, preuve à 0 s) → 36 modèles, pastille Code (25) → recherche, tri par prix → fiche (prix en CAD, benchmarks avec
source) → exemple d'appel étiqueté Aperçu, clic Copier → « une ligne » → carton. Piste mod-musique-72 mesurée à 127,7 BPM. L'usine mixe maintenant par
loudnorm (−14 LUFS visés, crête −3 dBTP) : le limiteur seul laissait +2 dB de crête après l'AAC. Faiblesses : voir `brief.json › revue` (capture 1×, beat « une ligne »
sans vrai changement de modèle tant que l'API n'est pas ouverte, son non écouté). Pour passer 8 : refaire la capture à 2× et filmer un appel réel dès l'ouverture de l'API.
