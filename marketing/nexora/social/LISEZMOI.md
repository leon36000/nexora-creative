# Nexora AI : lancement, famille SOCIAL

Réseaux sociaux, arrière-plans et calendrier éditorial du lancement. Ligne de campagne : « Rêvez grand. Gardez le contrôle. » (EN : « Dream big. Stay in control. »). Tout ce qui porte du texte existe en fr-CA (suffixe `.fr`) et en en-CA (`.en`). Les images générées par IA ne contiennent aucun texte ni logo : le texte, les logos officiels (fichiers SVG copiés tels quels), la mosaïque, la grille, la règle et la bande braise sont posés en code.

`apercu.png` : planche-contact de toutes les pièces. `calendrier-lancement.md` (et `.csv`) : le calendrier de 30 jours.

## Où est quoi (`final/`)

| Dossier | Contenu |
|---|---|
| `facebook/` | `profil.png` (1080), `couverture-{aurore,nuit,mosaique}.{fr,en}.png` (1640 × 624, zone sûre mobile : les 1000 px du centre), `evenement` (1920 × 1005), `partage-lien` (1200 × 630), `couverture-groupe` (1640 × 856), `publications/` (8 publications 1080 × 1350, une par outil, en damier photo / code), `stories/` (5 × 1080 × 1920, zones de sécurité 250 px en haut et 340 px en bas), `arrieres-plans/` (4 fonds sans texte pour fonds de story, de texte ou de page) |
| `instagram/` | `profil.png`, `publications/` (6 × 1080 × 1350), `carrousel/` (7 images « un compte, tous vos outils » : accroche, quatre doubles d’outils, le compte, l’appel à l’action), `a-la-une/` (8 couvertures 1080 × 1920, un glyphe par outil dans un cadre de filets, dans le disque de découpe), `reels/` (`reels-cadre` PNG transparent à superposer à la vidéo, `reels-guides` avec les zones masquées par l’interface) |
| `linkedin/` | `banniere-page`, `banniere-personnelle` (1584 × 396, rien dans le tiers gauche : photo de profil), `publications/` (6 × 1200 × 627), `image-partage`, `carrousel-nexora-ai.{fr,en}.pdf` (PDF vectoriel, 8 pages 1080 × 1350) et les huit pages en PNG |
| `x/` | `entete` (1500 × 500, bas gauche libre pour la photo de profil), 4 images 1600 × 900 |
| `youtube/` | `banniere` (2560 × 1440, texte dans la zone sûre 1546 × 423), `vignettes/` (8 × 1280 × 720, une par outil), `carte-de-fin` (1920 × 1080, emplacements pour deux vidéos et l’abonnement) |
| `tiktok/` | `profil.png`, 3 couvertures 1080 × 1920 |
| `discord-slack/` | bannière 960 × 540, icônes 512 (Discord et Slack), 8 émojis 128 × 128 sur fond transparent (un glyphe par outil) |
| `fonds/` | `visioconference/` (1920 × 1080 : aurore, atelier chaud, ville au crépuscule, mosaïque minimale ; chaque ambiance sans logo et avec un petit symbole discret), `ordinateur/` (6 × 3840 × 2160), `telephone/` (6 × 1290 × 2796) |

Les huit outils (noms exacts) : Nexora WorkStudio, Nexora Code, Nexora RAG, Nexora Bot, Nexora Creative, Nexora WebPilot, Nexora Privacy Router, VPS au Québec. L’état affiché vient de `web/src/i18n/apps.ts` : Code, RAG, Bot, WebPilot et Privacy Router « Bientôt » ; Creative « Plus tard » ; WorkStudio « Démonstration sur demande » ; VPS « En préparation ». Aucun outil n’est présenté comme disponible en libre-service.

## Régénérer

```bash
cd social/sources
bun construire.mjs                 # tout (≈ 1 min) ; ou : bun construire.mjs fb ig li x yt tt chat fonds
bun construire.mjs fb --filtre publication      # une famille de pièces
python3 calendrier.py              # calendrier-lancement.md et .csv
python3 apercu_familles.py social  # apercu.png
python3 generer_bibliotheque.py    # plans manquants de la bibliothèque (Qwen-Image-2.1, GPU partagé : 3 à 5 min par plan)
```

Dépendances : `bun`, Playwright (celui de `NexoraSite/web/node_modules`), PIL. Polices Geist, Inter et JetBrains Mono copiées dans `sources/polices/` (licences libres, voir `NexoraSite/web/src/fonts/LICENSE-*.txt`) ; logos officiels copiés dans `sources/logos/` (jamais modifiés).

- `sources/moteur/marque.mjs` : jetons de marque, mosaïque (port exact de `web/src/components/brand/mosaic.tsx`, graine fixe), grille de mesure, règle graduée, bande braise, cadre de filets, glyphes de 7 × 7 carrés (un par outil), pastille d’outil, logos, mise en page « affiche », rendu Playwright et PDF. **Réutilisé par `publicite/`.**
- `sources/moteur/compo.mjs`, `modeles.mjs` : fonds, voiles, grille des huit outils, publications, stories.
- `sources/{fb,ig,li,x,yt,tt,chat,fonds}.mjs` : une famille par fichier ; `sources/html/` : le HTML de chaque pièce (ouvrable dans un navigateur) ; `sources/generees/` : plans bruts générés par IA ; `sources/generer_bibliotheque.py` : les prompts.
- Un contrôle automatique (`data-fit`) réduit le corps d’un titre qui déborderait et signale tout débordement restant.

## Règles de lisibilité appliquées

Sur les formats de 1080 px de large, aucun texte sous 26 px (≈ 9 px à 360 px de large), le texte courant à 36 à 40 px et les titres à 100 px ou plus ; sur les paysages (1200 et 1600 px), étiquettes à 24 px et plus, texte courant à 30 px (LinkedIn) et 42 px (X), titres à 66 px et plus ; 4 à 7 mots par titre; le texte est tenu à l’écart de la mosaïque (repoussée vers un bord ou une bande) ; le logo en couleur ne se pose que sur fond noir uni, la version blanche sur photo ; orange de texte `#FF7A45` sur noir (7,6:1), texte clair `#F5F4EF` (17,9:1).

## Ce qui dépend d’une information manquante

- **Domaine, courriel, téléphone, adresse** : `coordonnees.json` contient encore des marqueurs `«à compléter…»`. Le domaine s’affiche tel quel sur la carte de fin YouTube ; aucune autre image sociale ne porte d’adresse (les appels à l’action sont des phrases). Remplir le fichier puis relancer `bun construire.mjs`.
- **Date du lancement, noms de comptes (@)** : non fournis ; le calendrier compte en « J1 à J30 ».
- **Bibliothèque de plans générés : 11 sur 26 prévus.** Le GPU est partagé (3 à 5 min par plan, au lieu de 50 s) : ont été générés et gardés, après examen un par un (aucun texte, visage ni artefact) : `aurore-foret`, `aurore-lac`, `fleuve-aube`, `ville-crepuscule`, `atelier`, `phare`, `cabane-neige`, `salle-calcul`, `carres-flottants`, `aurore-vertical`, `ville-vertical`. L’aurore de `cabane-neige` était vert-de-gris, hors palette : elle a été ramenée au bleu nuit par un traitement de canal (original conservé : `cabane-neige-original.png`). Les 15 autres plans de `generer_bibliotheque.py` (`bureau-nuit`, `montagne-aube`, `phare-vertical`, `fleuve-vertical`, `foret-vertical`, `braises-montantes`, mosaïques, pont de lumière…) ne sont pas générés : `REPLI` dans `marque.mjs` les remplace par le plan le plus proche, recadré (le résultat reste net, vérifié sur les stories et les fonds d’écran). Pour compléter : `python3 sources/generer_bibliotheque.py` puis `bun sources/construire.mjs`, ou `sources/construire-tout.sh`.
- **Fonds d’écran 3840 × 2160** : les plans générés font 1792 × 1024 ; sans la version ×4 (`outils/agrandir.py`, nom du plan suivi de `-4k.png`), l’image est agrandie par le navigateur et le grain masque la perte de netteté.
- **Musique et vidéo** : hors de cette famille (voir `publicite/` pour les plans d’animation).
