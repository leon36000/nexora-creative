# Imprimés Nexora AI (famille « imprimés »)

Cartes d'affaires, papeterie, affiches, dépliants et fiches, supports de salon, présentation PowerPoint. Aperçu de tout : `apercu.png`. Tout part du moteur partagé `../identite/sources/moteur.mjs` (charte, polices locales, logos officiels, mosaïque générée en code).

## Régénérer
```
./regenerer-tout.sh                    # tout, depuis ../coordonnees.json (voir plus bas pour 1 à N personnes)
./generer-cartes [--coordonnees f.json] [--sortie dossier] [--seulement slug]   # cartes seulement
bun sources/papeterie.mjs [--coordonnees f.json] [--url-images https://…/images]
bun sources/affiches.mjs [heros famille quebec typo creative code workstudio]
bun sources/depliants.mjs [trois-volets a5 fiches]
bun sources/salon.mjs
cd sources/presentation && bun actifs.mjs && bun deck.mjs && ./rendre-controle.sh
```
Prérequis : `bun`, Chromium de Playwright (importé depuis le dépôt du site), `pdftoppm`/`pdftocairo` (poppler), `soffice` (contrôle des .pptx seulement), `pptxgenjs` (`cd sources/presentation && bun install`).

### Quand `coordonnees.json` sera rempli
Remplir `../coordonnees.json` (ajouter une entrée par personne dans `personnes`), puis `./regenerer-tout.sh` (ou `NEXORA_COORDONNEES=f.json ./regenerer-tout.sh`). Une carte (4 variantes, 2 PDF chacune, PNG) et une signature courriel (fr, en, `.txt`) sont produites **par personne**, dans `final/cartes/<slug>/` (slug = nom sans accents, ou `personne-N` tant que le nom est un marqueur). Tant qu'une valeur est un marqueur `«à compléter…»`, elle s'affiche telle quelle (version d'essai, aucun défaut caché).

## Ce qui est livré (`final/`)
| Pièce | Fichiers |
|---|---|
| **Cartes d'affaires** 3,5 × 2 po (88,9 × 50,8 mm), fond perdu 3 mm | `cartes/<slug>/carte-<slug>-<fr|en|braise-fr|braise-en>-impression.pdf` (recto, verso, **calque de vernis** en page 3 ; traits de coupe), `…-sans-traits.pdf` (mêmes pages, fond perdu, sans traits), `carte-<slug>-recto.png` et `…-verso-<variante>.png` (300 dpi, taille finale). `cartes/vernis/carte-vernis.svg` (calques `fond-perdu` et `vernis`) et `.pdf`. |
| **Papeterie** (`papeterie/`) | Papier à en-tête Lettre et A4 (fr, en) ; enveloppes DL (110 × 220 mm) et n° 10 (4,125 × 9,5 po), face + dos (rabat), fond perdu et traits ; carte de remerciement 5 × 7 po (fr, en) ; facture / soumission Lettre et A4 (fr, en, champs vides) ; étiquette d'expédition 4 × 6 po (bilingue) ; `signature-courriel/` (HTML fr/en à tables et styles en ligne, version `.txt`, images à héberger dans `images/`, aperçus PNG). |
| **Affiches** (`affiches/<id>/`) | 7 compositions × fr/en × 18 × 24 po, 24 × 36 po, A2 : `affiche-<id>-<lang>-<format>-fond-perdu.pdf` (fond perdu 0,125 po ; 3 mm pour l'A2 ; sans traits) et `.png` (format fini, 100 dpi, pour l'écran). `heros` (« Rêvez grand. Gardez le contrôle. »), `famille` (huit outils en grille de filets), `quebec` (« IA souveraine au Québec »), `typo` (le symbole géant dans la matière), série `creative`, `code`, `workstudio` (« un outil, une image »). |
| **Dépliants** (`depliants/`) | `depliant-3-volets-lettre-<fr|en>-<impression|ecran>.pdf` (11 × 8,5 po, extérieur + intérieur ; `impression` = fond perdu + traits) ; `depliant-a5-plie-…` (A4 paysage plié en A5) ; `fiches/fiche-<outil>-<fr|en>.pdf` (Lettre, une page ; `-impression.pdf` avec fond perdu) et `.png` : 8 outils × 2 langues. |
| **Salon** (`salon/`) | Bannière rétractable 850 × 2000 mm (fr, en ; PDF fond perdu 5 mm + PNG + PNG avec zones de sécurité) ; fond de stand 3 × 2,4 m **à l'échelle 1:10** (PDF vectoriel 300 × 240 mm, à agrandir à 1000 %) + PNG ; badge 4 × 3 po (équipe, visiteur) ; tour de cou 20 × 900 mm ; signalisation de porte Lettre (« Bienvenue / Welcome », « Séance en cours / Session in progress ») ; accroche-porte 3,5 × 8,5 po (fr, en, avec gabarit de découpe en page 3). |
| **Présentation** (`presentation/`) | `presentation-nexora-ai-fr.pptx` et `-en.pptx` (16:9) : 7 dispositions maîtres (Titre, Section, Contenu, Citation, Grille des outils, Image, Fin) + 12 diapositives d'exemple, notes d'orateur. `polices-a-installer/` : Geist Medium, Inter, JetBrains Mono Medium en TTF statiques (licences OFL). |

## Notes de fabrication
**Cartes d'affaires.** Recto : noir profond `#0A0A0E` plein bord, symbole officiel (25 mm) et mosaïque braise qui se dissout vers la gauche (graine fixe, vectorielle). Verso : papier `#FBFBF8`, bande braise de quatre barres au bord droit (déborde dans le fond perdu) ; variantes fr, en, et « braise » (orange `#FF5A1F`, texte et logo noirs, version fr et en). PDF d'impression et sans traits des cartes : **texte converti en contours** (Ghostscript, aucune police à fournir). Autres PDF : polices intégrées en Type 3 (glyphes vectoriels exportés par Chromium pour les polices variables) ; si l'imprimeur l'exige, les faire convertir en contours.
- **Finition : vernis sélectif sur le symbole du recto.** Fournir `cartes/vernis/carte-vernis.pdf` (ou le calque `vernis` du `.svg`, ou la page 3 de chaque PDF d'impression) comme **couleur d'accompagnement nommée « VERNIS »**, 100 % noir, à la position exacte du symbole (25 × 25 mm, à 9 mm du bord gauche, centré en hauteur). Vernis UV sélectif brillant sur un recto noir mat ou *soft-touch* ; le symbole doit recevoir le vernis *par-dessus* l'encre (le crème et l'orange restent visibles, le noir autour reste mat). Un PDF Chromium ne porte pas de calques optionnels (OCG) : le calque est donc fourni en **fichier et page séparés**, c'est la façon standard de remettre un masque de vernis. Prévoir avec l'imprimeur une légère surcote du masque (repérage) et une épreuve.
- Couleur : les PDF sont en **RVB**. Ne pas convertir naïvement en CMJN : demander à l'imprimeur un noir riche pour les aplats et pour le texte (équivalent de `#0A0A0E`, pas un noir 100 % ni un gris) et une épreuve de l'orange `#FF5A1F` (hors gamme CMJN, il ternit). Papier, grammage et prix : à fixer avec l'imprimeur (non spécifiés ici).
- Traits de coupe : repères à 3,5 mm du fond perdu, filet de 0,18 mm ; la ligne de légende en bas porte le nom du fichier.
- Si les noms sont plus longs que le gabarit (nom sur 2 lignes), relire le verso : le bloc nom + titre a 14 mm de haut.

**Papeterie.** Papier à en-tête sans fond perdu (impression de bureau). Enveloppes : le dos (rabat) est pleine page noire avec mosaïque (impression commerciale, fond perdu 3 mm, traits). La facture / soumission ne contient **aucun montant, taux ni numéro** : `TPS`, `TVQ`, `N° TPS`, `N° TVQ` sont des champs vides à compléter. Signature courriel : tables et styles en ligne (Arial/Helvetica de repli : les clients courriel ne chargent pas Geist) ; le symbole (PNG 2×) et le logo sont dans `signature-courriel/images/` : **les héberger** (HTTPS public) puis régénérer avec `--url-images https://…/images` (sinon le chemin est relatif `images/`, valable seulement pour l'aperçu local).

**Affiches.** Texte et logo posés en code (vectoriels) ; images générées avec `outils/generer.py` (Qwen-Image-2.1, 9:16, 1024 × 1792) puis agrandies ×4 (Real-ESRGAN, `sources/agrandir-lot.sh`, 4096 × 7168). **Résolution réelle de l'image** (l'outil ne dépasse pas ×4) : 18 × 24 po ≈ 224 dpi, A2 ≈ 244 dpi, 24 × 36 po ≈ 169 dpi ; bien pour une affiche regardée à distance, mais pas les 300 dpi demandés. Pour 300 dpi réels sur 24 × 36 po il faudrait une image de 7200 × 10800 px (deuxième passe d'agrandissement ou génération plus grande). Le texte, le logo, la mosaïque et la bande braise sont vectoriels (nets à toute taille). Images sources : `sources/generees/` (brutes `.png`, agrandies `-x4.jpg`). Rejetée : `generees/rejetees/salle-calcul-16x9.png` (trop sombre, inutilisable). `aurore-hero-9x16.png` vient de l'essai `essais/aurore.png`, réagrandie à 4096 px.
- Le symbole de l'affiche `typo` est le **symbole officiel inchangé**, à 48 % de la largeur, sur fond noir uni : la matière (mosaïque) le contourne en gardant sa zone de protection (la charte interdit le logo en couleur sur la mosaïque). C'est notre lecture de « le N pixel géant en matière ».
- Les affiches indiquent l'état honnête de l'outil (« État : Plus tard » pour Nexora Creative, « Bientôt » pour Code, « Disponible » pour WorkStudio), lu dans `web/src/i18n/apps.ts` et `product-family.tsx` au 01/11/2026. Si un état change, modifier `OUTILS` dans `moteur.mjs`.

**Dépliants et fiches.** Panneaux à tiers égaux (3,667 po) ; en production le rabat intérieur est souvent un peu plus étroit (à confirmer avec l'imprimeur). Les fiches reprennent le texte du site : phrase d'accroche, trois points, état (« Disponible / Bientôt / Plus tard ») et la note « Aucune date n'est annoncée » du site. Aucun chiffre, prix ni date.

**Salon.** « 33 × 80 po » est réalisé à **850 × 2000 mm** (taille courante, 33,46 × 78,74 po ; la bannière à 33 × 80 po exacts mesure 838 × 2032 mm : si le fabricant l'exige, changer `w`/`h` dans `salon.mjs`). Zones de sécurité : bas masqué par le boîtier (≈ 200 mm) et haut (≈ 60 mm) — `…-zones-de-securite.png`. Le fond de stand est à 1:10 : l'image (7168 × 4096 px agrandie) donne ≈ 61 dpi sur 3 m, adapté à une vue de loin. Badge : champs « Nom / Organisation » à remplir (aucun nom d'événement inventé). Accroche-porte : trou de 1,5 po de diamètre et fente tracés (page 3 = découpe, couleur d'accompagnement).

**Présentation.** Texte natif (modifiable), mosaïques en PNG transparents, polices Geist Medium / Inter / JetBrains Mono Medium **non intégrées** au .pptx (pptxgenjs ne peut pas les embarquer) : installer `polices-a-installer/` ; sans elles PowerPoint substitue (Calibri/Arial) et les mises en page restent lisibles. Contrôle visuel fait avec LibreOffice (polices chargées sans installation système) : `sources/html/deck-controle/`.

## Ce qui dépend d'une information manquante
1. **`coordonnees.json`** : domaine, courriel, téléphone, adresse, et nom, titre, courriel, téléphone de chaque personne (tout est `«à compléter…»`).
2. **URL d'hébergement des images de la signature courriel** (`--url-images`).
3. **Numéros TPS / TVQ et conditions** de la facture : champs vides.
4. **Événement de salon** (nom, dates) : non inventé, rien sur les badges ni les supports.
5. **Taille exacte de fabrication** des supports (rétractable, fond de stand, rabat du dépliant), **papier, grammage, finitions et conversion CMJN** : à fixer avec l'imprimeur / le fabricant.
6. **Résolution 300 dpi** des grandes affiches : voir « Affiches » (nécessite des images sources plus grandes).
7. **Pastille « Disponible / Bientôt »** : à relire quand un outil change d'état.
