# Brief Codex : moteur de montage du film V6 de Nexora Creative (`monter_v6.py`)

Tu travailles dans le dépôt `/home/pc6/Desktop/NexoraCreative-film-v6` (branche `feat/film-v6-creative`). Écris uniquement dans
`marketing/creative/video-v6/` (code) et dans le cache donné par la variable `V6_CACHE` (défaut :
`marketing/creative/video-v6/.cache/`, à ignorer par git via un `.gitignore` local). Ne lance aucun rendu GPU, ne touche à aucun
service, aucun autre dossier, aucun fichier de clé. **Le disque de pc6 n'a que ~9 Go libres** : rends les segments en flux
(PIL → tube ffmpeg, comme `video-v4/monter_v4.py`), jamais en séquences PNG sur disque ; nettoie ton cache de test à la fin.
Aucun commit (je relis et je committe). Réponds en français dans ton dernier message.

## But
Un film publicitaire de 55 à 65 s, rythmé comme les promos « Kling 4.0 » de Higgsfield : coupes sur le temps (124,8 BPM),
typographie cinétique énorme, captures réelles de l'application zoomées, plans d'effets spéciaux générés (MiniMax H3, rushes
1344×768 ou 768×1344 à 24 i/s, avec leur son natif). Quatre sorties : 16:9 1920×1080 et 9:16 1080×1920, français et anglais.
Le moteur lit une **liste de montage JSON** (`montage-v6.json`, que j'écris) et un fichier de marque (`marque-v6.json`, seul
endroit des textes, couleurs, polices, logo, carton de fin ; le nom de l'entreprise va changer).

## Ce qui existe déjà et que tu dois réutiliser (lis-les d'abord)
- `marketing/creative/video-v4/monter_v4.py` : architecture à reprendre (segments rendus en parallèle dans un cache, PIL → ffmpeg,
  `police()`, `ease()`, `interp()`, `recadrer()`, `poser_textes()`, mixage numpy, loudnorm). Copie ce qui sert, n'importe pas V4.
- `marketing/creative/video-v3/couches.py` : étalonnage, grain, vignette, flou, `FFMPEG`/`FFPROBE` (binaire statique arm64).
- `marketing/creative/video-v3/sfx_v3.py` : bruitages synthétisés (impacts, souffles, risers) ; réutilise-les et ajoute un clic de
  clavier mécanique synthétisé et un « whoosh » court.
- Polices : `~/Desktop/NexoraSite/web/src/fonts/geist-latin-wght-normal.woff2` (variable, utiliser la graisse 800-900 pour les titres)
  et `jetbrains-mono-latin-wght-normal.woff2` (mono). Couleurs de la marque Signal : encre (8,8,10), os (246,244,238),
  brume (160,160,172), signal (255,90,31).
- Exemple de capture réelle (Playwright, 3200×1800 JPEG, viewport CSS 1600×900 ×2) : `~/nexora-creative-data/promo/v6-creative/captures/boost/s01/`
  (`NNNN-<etape>.jpg` : `vide`, `saisie` une image par touche, `saisie-fin`, `survol`, `reflexion`, `boost`, `utiliser-survol`,
  `utilisee` ; `journal.jsonl` horodate chaque image ; `boost.json` contient les mots tapés et la version boostée réelle). Le champ
  de saisie est vers (124,370)-(660,592) en pixels CSS ; le bloc « Version boostée » vers (124,612)-(660,956).
- Exemple de rush : `~/nexora-creative-data/promo/v6-creative/rushes/765.mp4` (1344×768, 24 i/s, 5,2 s, son natif).
- Musique d'essai : `~/nexora-creative-data/promo/v6-creative/musique/lyria-3.wav` (124,81 BPM, phase 0,317 s, voir `musique.json`).

## Types de segments à implémenter (chacun : `type`, `debut` dans le film en s, `duree`, plus ses champs)
1. `plan` : un rush (`fichier`, `fichier_vertical` optionnel pour le 9:16), `entree` (s dans le rush), `vitesse` (nombre, ou rampe
   `[[t_rel, vitesse], …]` intégrée correctement, pour un ralenti sur l'impact), `cadrage` images-clés `[[t_rel, cx, cy, zoom]]`
   (centre normalisé, zoom ≥ 1) séparées pour 16:9 et 9:16 (`cadrage_v`), remise à l'échelle lanczos + accentuation légère,
   `secousses` `[[t_rel, amplitude_px, duree]]` (tremblement amorti, flou de bougé directionnel), `flash` `[[t_rel, couleur, duree]]`,
   `etalonnage` (préréglage nommé : `nuit_feu`, `espace`, `orage`, `aube`, `neutre`), `inverse` (lecture à l'envers, optionnel).
   En 9:16 sans `fichier_vertical`, recadrer selon `cadrage_v`.
2. `saisie` : séquence de captures (`dossier`, `etapes` à inclure, par ex. `["vide","saisie","saisie-fin","survol"]`), retimée
   pour tenir dans `duree` ; caméra virtuelle qui part du plein écran et pousse vers la zone `zone` (pixels CSS) avec un léger flou
   de profondeur hors zone ; en 9:16, cadrer la zone en pleine largeur. Bruit de clavier à chaque nouvelle image `saisie`.
3. `boost` : **l'effet signature**. Départ : capture `boost` (zone « Version boostée »). En `duree` (≈ 1 s) : les mots du
   texte réel (`boost.json`, ou `texte` fourni) jaillissent du bloc et remplissent l'écran en vagues (décalage d'une image par mot,
   mono, tailles variées, profondeur et flou de mouvement), les `termes_cles` listés sont en couleur signal et plus gros ;
   puis tout est aspiré vers la caméra (zoom ×3 + flou radial + flash) et on coupe sur le plan suivant. Souffle + riser synchronisés.
4. `titre` : typographie cinétique plein écran, 1 à 4 mots (`texte_id` de la marque), styles `claque` (échelle 1,35→1 en 4 images,
   flou de mouvement, secousse, sous un impact sonore), `balayage` (masque latéral), `empile` (un mot par temps, pour
   « IMAGE · VIDÉO · MUSIQUE… »). Fond : noir, ou par-dessus la vidéo du segment précédent/suivant (`sur_video`).
   9:16 : retour à la ligne automatique, marges de sécurité 12 % haut et 20 % bas.
5. `chapitre` (grammaire Kling) : panneau à chevrons `»` `«` animés, étiquette courte (`texte_id`), un média dedans (capture JPEG,
   séquence de captures ou mp4) avec poussée lente, fond = version floue et sombre du média ; badge optionnel `EN PRÉPARATION`
   (texte de la marque) quand la fonction n'est pas livrée.
6. `avant_apres` : deux ou trois sources synchronisées (`couches` : brut, masque/damier, composite), une ligne de balayage animée
   qui révèle la couche suivante, petites étiquettes (`BRUT`, `MASQUE`, `FINAL` depuis la marque).
7. `mosaique` : 3 à 9 rushes qui apparaissent un par temps en grille (16:9) ou en pile (9:16).
8. `noir` : noir (avec ou sans texte) pour un souffle.
9. `carton` : le carton de fin **unique et remplaçable** : logo PNG si `marque.logo` n'est pas nul, sinon nom typographié
   (`marque.nom` + `marque.produit`), slogan de la langue, `url` si non vide, mentions en petit.
Chaque segment peut porter `textes` : surimpressions `{t, duree, texte_id, style, position}`.

## Audio
- Musique : `musique.fichier`, `musique.entree` (s dans le morceau au début du film), coupes de morceau optionnelles
  `musique.coupes` `[[t_film, t_morceau]]` (saut aligné sur une mesure, fondu de 30 ms), gain.
- Voix : pour chaque langue, un dossier de fichiers `<id>.wav` (une phrase par fichier) placés par `voix: [{id, t}]` ; la musique
  baisse de 7 dB sous la voix (attaque 60 ms, relâche 250 ms).
- Son natif des rushes : `son_db` par segment `plan` (le grondement du dragon, les explosions), coupé net à la coupe avec fondu de 10 ms.
- Bruitages : liste `sfx: [{t, type, db}]` (types de sfx_v3 + `clavier`, `whoosh`, `impact`, `riser`, `sub`).
- Mastering : deux sorties possibles, `web` (−14 LUFS, crête vraie −1,5 dBTP) et `reseaux` (−10 LUFS, −1 dBTP).

## Ligne de commande et sorties
`python3 monter_v6.py montage-v6.json --format 16x9|9x16 --langue fr|en --sortie <mp4> [--master web|reseaux] [--de s --a s] [--jobs N] [--brouillon]`
(`--brouillon` = demi-résolution, pour les essais ; `--de/--a` = n'en rendre qu'une plage). H.264 High, CRF 16, yuv420p, 24 i/s,
AAC 320 k, `+faststart`. Plus `planche_v6.py <mp4> <jpg>` : une image par seconde avec le temps, en grille.

## Preuve demandée
Écris `montage-essai.json` (≈ 12 s, en n'utilisant que le matériel listé ci-dessus : saisie s01 → boost s01 → titre claque → plan
765 avec ralenti et secousse → chapitre avec une capture → avant_apres avec 765 et une version désaturée de 765 → carton), rends-le
en 16:9 et 9:16 (`--brouillon` accepté pour le 9:16), fais la planche, mesure la loudness. Mets les MP4 d'essai dans
`marketing/creative/video-v6/.cache/essais/` (ne les supprime pas : je les archive ; ton bac à sable n'écrit que dans le dépôt). Dans ton dernier message : ce qui marche, ce qui
reste approximatif, temps de rendu par seconde de film, et la commande exacte.
