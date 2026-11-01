# Identité Nexora AI (famille « identité »)

Exports des logos officiels, photos de profil, verrouillages de produit, icônes et guide « Kit de marque Nexora AI » (fr-CA et en-CA). Aperçu de tout : `apercu.png`.

## Ce qui est livré (`final/`)

| Dossier | Contenu |
|---|---|
| `final/logos/svg/` | Copie **inchangée** des SVG officiels du dépôt du site (`docs/marque/logos/`) : logo complet clair, sombre, noir, blanc ; symbole seul (4 variantes) ; tuiles d'application. |
| `final/logos/png/` | PNG transparents : logo complet et symbole, 4 variantes (`clair`, `sombre`, `noir`, `blanc`), largeurs 256, 512, 1024, 2048 et 4096 px. Aussi `…-sur-sombre`, `…-sur-clair`, `…-sur-creme` (1024 et 2048 px) : le logo posé sur son fond avec la zone de protection de 10,4 unités. |
| `final/logos/pdf/` | PDF vectoriels de chaque variante (logo : 100 mm de large ; symbole : 40 mm) et versions sur fond. |
| `final/profils/` | Photos de profil carrées 1080 px (+ SVG) : noir profond, orange avec symbole noir, orange avec symbole blanc, crème, papier. Symbole à 44 % de la largeur : le symbole **et** sa zone de protection tiennent dans le cercle d'un recadrage rond (contrôlé : `sources/html/_cercle-*.png`). |
| `final/verrouillages/` | Verrouillages de produit horizontaux (symbole officiel + nom en Geist 500) pour les 8 outils, sur sombre et sur clair : `svg/` (texte converti en contours, sans police), `svg-texte-editable/` (texte + Geist intégré en base64), `png/` (2048 px, transparents). Variante `-en` pour « VPS in Quebec ». |
| `final/icones/` | `icone-application-1024.png` (tuile officielle), `icone-tuile-arrondie-1024.png`, `icone-maskable-1024.png`, `banniere-icone-1024.png` (tuile + matière). |
| `final/guide/` | `kit-de-marque-nexora-ai-fr-CA.pdf` et `nexora-ai-brand-kit-en-CA.pdf` : 21 pages 16:9 (1920 × 1080 px), polices intégrées. |

**Favicons et icônes déjà dans le dépôt du site (à ne pas refaire)** : `web/src/app/icon.svg` (favicon SVG clair/sombre), `web/src/app/favicon.ico` (16, 32, 48 px), `web/src/app/apple-icon.png` (180 px), `web/public/icon-192.png`, `icon-512.png`, `icon-maskable-512.png`, gabarit Open Graph `/og/*`. Tuiles sources : `docs/marque/logos/app/`.

## Décisions de marque appliquées
- Les logos ne sont jamais modifiés : seule la racine `<svg>` (classe, taille) est touchée à l'inclusion ; les chemins sont ceux du dépôt.
- **Version horizontale seulement** : la charte (§2) ne définit pas de version empilée ; on n'en invente pas.
- Verrouillage de produit : le symbole garde sa taille de logo, le nom est du texte (Geist 500, −0,03 em, capitales de 36 unités centrées sur le symbole, même espacement que le logotype).
- Nom anglais de l'outil VPS : « VPS in Quebec » (graphie du site, `home.family.items.vps`).

## Régénérer
```
./regenerer-identite.sh            # tout : logos, profils, verrouillages, icônes, guide fr + en, apercu.png
bun sources/construire-identite.mjs logos profils verrouillages icones   # une partie
bun sources/guide.mjs              # les deux guides
```
Prérequis : `bun`, Chromium de Playwright (importé depuis `/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test`), `gs` (Ghostscript) et `pdftocairo` (poppler) pour les SVG de verrouillage en contours.

## Sources (`sources/`)
- `moteur.mjs` : **moteur de gabarits partagé** (charte en variables, `@font-face` Geist/Inter/JetBrains Mono depuis `polices/`, logos officiels, mosaïque générée en code — port fidèle de `mosaic.tsx`, graine fixe —, règle, grille, bande braise, feuille d'impression avec fond perdu et traits de coupe, rendu PNG/PDF, planche-contact, lecture de `coordonnees.json`, textes et état des 8 outils). Les imprimés (`../imprimes/sources/*.mjs`) le réutilisent.
- `polices/` : Geist, Inter, JetBrains Mono (woff2, licences OFL jointes). `logos/` : copie des SVG officiels.
- `construire-identite.mjs`, `guide.mjs`, `apercu.mjs`, `planche.mjs`.

## Ce qui dépend d'une information manquante
- Le guide cite les coordonnées de `coordonnees.json` à la dernière page : tant qu'elles sont des marqueurs `«à compléter…»`, elles s'affichent telles quelles. Remplir le fichier puis relancer `bun sources/guide.mjs`.
- Les affirmations du guide viennent de la charte du 27/10/2026 (contrastes, tailles minimales) ; rien n'est ajouté. Les exemples « Non » du ton de voix sont des contre-exemples de rédaction, pas des citations.
- Date du guide : « Version 1 · Novembre 2026 » (mois du lancement, brief du 01/11/2026).
