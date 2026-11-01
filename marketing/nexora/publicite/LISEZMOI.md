# Nexora AI : lancement, famille PUBLICITÉ

Annonces Facebook et Instagram, bannières Web (IAB), courriel, page d’atterrissage et images Open Graph. Même moteur et mêmes composants que `social/` (`social/sources/moteur/`), mêmes jetons de marque. `apercu.png` : planche-contact de toutes les pièces.

## Où est quoi (`final/`)

| Dossier | Contenu |
|---|---|
| `facebook-instagram/accroches/<reve|outils|quebec>/` | 3 accroches × 4 formats (`1x1` 1080², `4x5` 1080 × 1350, `paysage` 1200 × 628, `9x16` 1080 × 1920) × fr et en = 24 images. Le format 9 : 16 respecte les zones de sécurité (250 px en haut, 340 px en bas). |
| `facebook-instagram/carrousels/<outils|quebec>/` | 2 carrousels de 5 cartes 1080² × fr et en |
| `facebook-instagram/video-6s/` et `video-15s/` (`9x16`, `1x1`) | plans fixes numérotés prêts pour l’animation : 6 s = 3 plans, 15 s = 6 plans. `storyboard-6s.md`, `storyboard-15s.md` (temps, texte, mouvement) et `sequence-*.json` (chemins, débuts, fins, fondu) |
| `facebook-instagram/textes-annonces.md` et `.csv` | titres, textes principaux, descriptions, bouton Meta, appel à l’action ; **limites vérifiées** à chaque génération (titre 40, texte principal 125, description 30) |
| `display/png/` et `display/html5/` | 9 formats IAB (300 × 250, 336 × 280, 728 × 90, 970 × 250, 160 × 600, 300 × 600, 320 × 50, 320 × 100, 468 × 60) × 2 concepts (`reve` : photo d’aurore ; `outil` : WorkStudio, mosaïque) × fr et en = 36 PNG statiques et 36 bannières HTML5 (dossier avec `index.html` autonome et `.zip` prêt à téléverser ; 60 Ko au plus chacune, limite 150 Ko) |
| `courriel/images/` | en-tête 600 × 200 et 1200 × 400 (à afficher à 600 px de large), bouton « Planifier un diagnostic » en image, pied 1200 × 200 |
| `courriel/modeles/` | `modele-{lancement,infolettre,invitation}.{fr,en}.html` : tableaux, styles en ligne, polices système de repli, bouton robuste (VML pour Outlook), texte de pré-en-tête, champs `{{...}}` à remplacer, pied légal |
| `atterrissage/` | `index.fr.html`, `index.en.html` (une page autonome de ≈ 280 Ko : polices, images et mosaïque intégrées, aucune requête externe) ; aperçus rendus `apercu-1440.*.png` et `apercu-390.*.png` |
| `og/` | `og-{accueil,solutions,apps,creative,vps,modeles,tarifs,contact}.{fr,en}.png` (1200 × 630) |

## Appels à l’action et état réel des outils

Lu dans `web/src/i18n/apps.ts` et `cms/content/claims.json` : aucun outil n’est vendu en libre-service (CL-12), les outils de Nexora Apps sont « Bientôt » et Nexora Creative « Plus tard ». On écrit donc **« Planifier un diagnostic »** (l’accompagnement sur mesure existe), **« Voir les solutions »** et **« Rejoindre la liste d’attente »**. **« Essayer Nexora Creative » n’est pas utilisé** : ce serait faux tant que l’outil n’est pas livré. Aucun chiffre, prix, date, client, certification, ni « meilleur » ; jamais « conforme à la Loi 25 ».

## Bannières HTML5

Chaque `index.html` : police Geist intégrée (29 Ko, polices système de repli), logo officiel intégré en data-URI, `<meta name="ad.size">`, variable `clickTag` (Google Ads), bordure de 1 px, animation CSS finie (≈ 5 s, une seule lecture, pulsation du bouton deux fois), `prefers-reduced-motion` respecté. Le PNG statique est l’image de fin de l’animation. Logo complet à 110 px de large ou plus, sinon symbole seul ; texte à 11 px au minimum.

## Page d’atterrissage

Héros sombre avec mosaïque braise et aurore, signature, huit outils (état écrit en toutes lettres), section « le contrôle » (sur place / hébergé au Québec / jamais pour entraîner un modèle, avec la réserve du registre : un serveur au Québec n’écarte pas à lui seul les lois qui s’appliquent), méthode en cinq temps, appel à l’action final et coordonnées. 390 à 1440 px sans débordement horizontal (vérifié), lien d’évitement, focus visible, texte alternatif, contrastes de la charte, mouvement sous `prefers-reduced-motion: no-preference`. Les aperçus sont rendus avec le mouvement réduit pour que les apparitions au défilement soient visibles.

## Régénérer

```bash
cd publicite/sources
bun construire.mjs                 # annonces, bannières, courriel (images et modèles), Open Graph (≈ 30 s)
bun construire.mjs annonces        # ou : banniere | courriel | og      (--filtre texte pour une seule pièce)
python3 images_bannieres.py        # recadre les plans pour les bannières (avant `construire.mjs banniere`)
bun atterrissage.mjs               # page d'atterrissage + aperçus
bun documents.mjs                  # textes d'annonces, storyboards, .zip des bannières
python3 ../../social/sources/apercu_familles.py publicite
```

## Ce qui dépend d’une information manquante

- **Domaine, courriel, téléphone, adresse** (`coordonnees.json`, marqueurs `«à compléter…»`) : affichés tels quels dans la page d’atterrissage, le pied des courriels et les modèles ; le bouton principal de la page pointe sur son ancre `#contact` tant que le domaine manque (puis sur `<domaine>/contact`).
- **Liens des courriels** : `{{lien_principal}}`, `{{lien_solutions}}`, `{{lien_desabonnement}}`, `{{lien_navigateur}}` ; adresse postale et mécanisme de désabonnement exigés par la loi anti-pourriel : à fournir.
- **Lien des bannières** : `clickTag` fourni par la plateforme publicitaire.
- **Vidéos** : on livre les plans fixes, les storyboards et les durées ; l’animation et la musique restent à produire (Nexora Creative : MiniMax H3 et MiniMax-Music3, sur le GPU de pc6, ou montage).
- **Bibliothèque de plans** : 11 plans sur 26 prévus, plans de repli pour les autres (voir `social/LISEZMOI.md`) ; `bash ../social/sources/construire-tout.sh` reconstruit tout.
