# Nexora AI : famille OBJETS PROMOTIONNELS

Vingt-quatre objets (21 demandés + 3 idées originales), chacun avec un **fichier de fabrication** vectoriel à l'échelle réelle et une **maquette** de 2400 px. Tout est reproductible en code.

## Où trouver quoi

| Chemin | Contenu |
|---|---|
| `apercu.png` | planche-contact de toutes les maquettes |
| `final/catalogue.pdf`, `final/catalogue-en.pdf` | catalogue de présentation fr-CA / en-CA (une page par objet : maquette, description, matériau, impression, quantité minimale indicative, **sans prix**) |
| `final/NN-slug/NN-slug-fabrication.svg` | gabarit **1:1 en millimètres**, calques nommés : `ART` (couleurs de marque), `GAUFRAGE-SEC` et `FEUILLE-ORANGE` (matrice de la frappe signature), `ZONE-IMPRESSION` (cyan), `SECURITE` (vert), `COUPE` (magenta, ligne « CutContour » / emporte-pièce), `SILHOUETTE` (schéma de référence, non imprimé), `REPERES`, `NOTES` (cotes) |
| `final/NN-slug/NN-slug-fabrication.pdf` | page 1 : le même gabarit en PDF vectoriel à l'échelle 1:1 ; page 2 : fiche de spécifications bilingue (technique, matériau, zones, couleurs avec **Pantone approchés + RVB + CMJN indicatifs**, notes de fabrication, quantité minimale indicative) |
| `final/NN-slug/NN-slug-fabrication-en.*` | variante en-CA des objets qui portent du texte (autocollants, sac de papier, ruban, kiosque) |
| `final/NN-slug/NN-slug-maquette*.jpg` | maquette 2400 × 2400 |
| `sources/code/` | `nx.py` (couleurs, logos officiels lus sans modification, mosaïque, texte en contours Geist 500, rendu Chromium), `mock.py` (perspective, cylindre, lumière, broderie, feuille à chaud, gravure, gaufrage), `fab.py` (gabarit et fiche), `o_*.py` (un fichier par groupe d'objets : données + gabarit + maquette), `build.py`, `catalogue.py` |
| `sources/prompts_photos.py`, `sources/generees/` | prompts et photos de produits **vierges** générées avec Qwen-Image-2.1 (`*_x.png` = agrandies ×4 Real-ESRGAN puis ramenées à 2400 px, voir `agrandir_lot.py`) |

Numéros : 01 t-shirt · 02 chandail à capuchon · 03 casquette · 04 tuque · 05 tasse · 06 gourde en acier · 07 sac fourre-tout · 08 carnet · 09 stylo · 10 clé USB et étui · 11 porte-badge et cordon · 12 planche d'autocollants · 13 épinglettes · 14 tapis de bureau · 15 pochette portable · 16 trousse de bienvenue · 17 sac de papier · 18 ruban adhésif · 19 coffret « édition lancement » · 20 bouteille isotherme · 21 jeu de cartes Pixel · 22 puzzle N en braise · 23 lampe veilleuse carrée · 24 fond de kiosque et comptoir.

## Régénérer

```bash
cd objets/sources/code
# environnement : python 3.12 + numpy, Pillow, opencv-python-headless, fonttools, brotli, uharfbuzz, pypdf ; bun + Playwright (site Nexora)
python build.py                      # tout (gabarits + maquettes)
python build.py tasse tshirt         # certains objets
python build.py tasse --sans-maquette   # seulement les fichiers de fabrication
python catalogue.py                  # catalogue.pdf, catalogue-en.pdf, apercu.png
python ../prompts_photos.py nom ...  # (re)génère des photos vierges (2 rendus en parallèle au plus)
```
Les mosaïques et le « N en braise » sont déterministes (graine fixe, port exact de `web/src/components/brand/mosaic.tsx`). Les logos sont lus dans `NexoraSite/docs/marque/logos/` et jamais modifiés.

## Méthode des maquettes
Aucun logo ni texte n'est dessiné par une IA : les photos de produits sont vierges (prompts « no text, no logo ») ; l'œuvre (SVG en mm) est rastérisée par Chromium puis **posée en code** (homographie ou projection sur cylindre), éclairée par la carte de luminance de la photo, avec la technique propre à l'objet : encre (sérigraphie/UV), broderie (fils, encoches d'aiguille, relief, ombre), feuille à chaud, gravure laser, gaufrage à sec, émail dur (rendu intégral en code). Les objets plats (autocollants, cartes, puzzle, épinglettes) sont rendus entièrement en code.

## Écarts et précisions (état final)
- **Clé USB et étui (10)** : la maquette montre la clé (gravure laser claire sur aluminium anodisé anthracite) ; l'étui existe dans le gabarit (frappe signature) mais n'est pas rendu en maquette, la photo d'étui générée n'étant pas exploitable (`generees/usb.png`, non utilisée).
- **Tapis de bureau (14)** : livré en sous-main 640 × 580 mm (la photo vierge est un sous-main carré) ; la variante « long tapis de souris » 900 × 400 mm est décrite dans les notes (même art étiré).
- **Fond de kiosque (24)** : mur 3 000 × 3 000 mm et face de comptoir 1 800 × 950 mm, calés sur les proportions de la photo ; texte et logo placés au-dessus de la zone cachée par le comptoir.
- **Porte-badge (11)** : le cordon reste noir uni (retenue) ; la marque est sur l'insert (logo complet + bande braise). Bande braise sur cordon = option à valider.
- **T-shirt (01)** : deux vues, dos (mosaïque N en braise) et face (symbole de 40 mm au cœur) : `01-tshirt-maquette.jpg` et `-face.jpg`. **Carnet (08)** : couverture et pages à grille de points (`-pages.jpg`). **Autocollants (12)** : maquette de la planche fr-CA ; gabarit fr et en.
- Rendus à faire valider visuellement par le fondateur avant commande : les orientations et tailles de marque sont réalistes mais les proportions du vêtement dépendent du fabricant.
- Les maquettes d'épinglettes, d'autocollants, de cartes et de puzzle sont rendues entièrement en code (pas de photo) ; leur réalisme (émail, vinyle) est approché.

## Décisions de direction artistique à connaître
- **Frappe signature** (carnet, étui USB, coffret) : le symbole garde la géométrie officielle ; les **montants sont gaufrés à sec** (relief ton sur ton) et la **diagonale en feuille orange**. C'est la façon de livrer « symbole en gaufrage/dorure orange » sans publier un symbole monochrome orange, qui n'existe pas dans la charte (monochromes : noir et blanc). Variante à valider avec le fondateur : montants aussi en feuille (os nacré).
- **Symbole en couleur sur fond clair** (tuque sur patch écru, sac en toile, bouteille isotherme) : version « claire » officielle (`#121218` + `#F04A10`). Sur la mosaïque ou à côté d'elle : version blanche uniquement (tapis).
- **« Le N en braise »** (dos du t-shirt, autocollant B, puzzle) est un dérivé graphique de la mosaïque (carrés qui se rassemblent en N, motif approuvé au §3 de la direction artistique), **pas une modification du logo** : le logo officiel apparaît séparément, intact, sur la même pièce ou le même ensemble.
- Le symbole n'est jamais utilisé comme motif répété : le cordon porte la bande braise (quatre barres) et un seul symbole ; le ruban répète le **logo complet**, pas le symbole.
- Mots sur les objets : uniquement la signature, « Rêvez grand. Gardez le contrôle. », « Sous votre contrôle », « IA souveraine au Québec » et le nom Nexora AI (versions en-CA : « Under your control », « Dream big. Stay in control. », « Sovereign AI, made in Québec »). Aucun chiffre, date, URL ni prix.

## Ce qui dépend d'une information manquante
- **Coordonnées** (`../coordonnees.json` : site, courriel, téléphone, adresse, nom/titre des personnes) : valeurs encore à compléter, donc **aucun objet n'en porte** (le carnet n'a pas de page de garde imprimée, le porte-badge n'a ni nom ni URL, la carte de bienvenue n'a pas de message ni de coordonnées). Quand le fichier sera rempli : ajouter l'URL au verso de la carte et du sac, un champ au porte-badge, puis `python build.py trousse-bienvenue sac-papier porte-badge`.
- **Carte de remerciement** : le mot « Merci » n'est pas dans la liste des mots autorisés sur les objets ; le recto/verso porte donc la ligne de campagne (fr / en). À valider avec le fondateur.
- **Fournisseurs** : Pantone, CMJN, quantités minimales et techniques sont **approchés ou indicatifs** (à valider sur nuancier, échantillon et devis). Aucun prix n'est donné.
- **Clé USB** : capacité et contenu préchargé à décider. **Lampe** : aucune performance annoncée avant mesure ; la teinte allumée de l'orange est à valider sur prototype.
- **« Édition lancement »** n'est imprimé nulle part (aucune date, numéro ni quantité prouvable).
- Les maquettes sont des **simulations** : l'aspect final (relief de broderie, brillance de feuille, teinte des encres) dépend du fournisseur.
