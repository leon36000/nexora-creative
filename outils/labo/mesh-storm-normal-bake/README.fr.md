# Conversion expérimentale de carte normale vers Storm

`bakeStormNormalMap` est une brique CPU en mémoire, non branchée au produit. Elle prend une liste bornée de triangles dont les positions/normales/tangentes glTF correspondent aux mêmes trois coins, un jeu `sourceUv` pour échantillonner la carte normale RGB(A) brute et un jeu `targetUv` pour rasteriser et déterminer le repère Storm. La correspondance entre les deux UV passe par les coordonnées barycentriques; une rotation du chart cible est testée. L’image source doit déjà être décodée en octets raw avec origine glTF en haut à gauche.

Le prototype accepte uniquement le filtrage LINEAR et CLAMP_TO_EDGE explicites, des UV dans `[0,1]`, des faces avant en espace objet et au plus 512 triangles. Pour limiter les risques de sous-flux numériques, les coordonnées UV non nulles inférieures à `2^-400` sont refusées. Il refuse plus de 16 777 216 positions candidates dans les rectangles englobants des triangles, avant d’allouer l’atlas ; ce compteur ne mesure pas le coût des calculs de reprojection. Il refuse notamment les signes `w` mixtes et les UV dégénérés. Il cherche les recouvrements d’intérieurs de triangles cibles, même sous-pixel, au moyen de `orient2d` adaptatif de `robust-predicates` 3.0.2 (Unlicense, dépendance de développement verrouillée dans `app/package-lock.json`) ; il refuse aussi les collisions de centres de texels sur une frontière commune. Ce banc n’est pas une validation de toutes les géométries possibles.

Le retour contient un nouveau tableau RGB8, un masque de couverture et un tableau d’ownership (identifiant par triangle, zéro hors couverture); il n’écrit aucun fichier. Les texels non couverts sont neutres. **Il ne produit pas de marge, mipmap ou atlas prêt à être affiché**, ne gère pas texture transform, wrap répété, morphing, skinning, transformations de scène ou faces arrière. Il ne reprojette pas les autres cartes et n’est pas relié à USDZ. Le refus actuel des cartes normales/AO et le repli GLB restent inchangés.

```sh
npm ci --prefix app --ignore-scripts
node --test outils/labo/mesh-storm-normal-bake/bake.test.mjs
```

Les tests synthétiques couvrent l’orientation cible à 90°, la séparation sampling/source et repère/cible, une texture raw variable et les refus. Ils ne prouvent pas une conversion sûre des modèles quality.

Un banc séparé à quatre triangles utilise une carte source variable, UV1, une rotation cible de 90°, des UV miroirs, des signes `w` constants par face et `normalScale=0,7`. Dans Storm CPU, l’atlas et un oracle géométrique n64 calculé séparément depuis la texture et la frame source diffèrent d’au plus un niveau RGB 8 bits à l’intérieur du masque érodé de deux pixels; l’écart maximal global est de 28 niveaux sur le bord. Le masque est déduit de la couleur du fond, pas d’un alpha de référence. Les témoins UV incorrects, signe `w` inversé et normale neutralisée produisent des différences visibles. Ce résultat ne valide ni les bords ni les six modèles quality, et ne démontre pas la compatibilité Apple.

`padNormalCharts` est un post-traitement séparé : il étend par copies successives des valeurs RGB appartenant à des chartes identifiées dans un tableau `Uint16Array` fourni par l’appelant. L’ownership émis par le bake peut lui être transmis directement, mais attribue un identifiant distinct à chaque triangle, même quand plusieurs triangles appartiennent à une seule charte. Le padding peut donc refuser des triangles voisins d’une même charte. Il renvoie de nouveaux tableaux et refuse tout contact entre identifiants distincts, avant et pendant l’extension (rayon 1 à 8, un million de pixels au maximum). L’appelant doit fournir une attribution exacte; ce module ne la déduit pas et ne résout pas les collisions.

Le bake accepte des images de sortie jusqu’à 2 048 × 2 048, mais le padding refuse plus de 1 048 576 pixels. Lors de chaque extension à huit voisins, la première valeur admissible est copiée : elle n’est pas nécessairement la plus proche en distance euclidienne. Un échantillon ou un repère dégénéré peut également être détecté en cours de rasterisation, après allocation; aucun résultat partiel n’est retourné.

Sur la fixture tournante à quatre faces, l’essai Storm a utilisé une attribution vérifiée et huit pixels de marge. La différence maximale globale avec le témoin géométrique est passée de 32 à 28 niveaux RGB 8 bits dans une vue; le maximum intérieur érodé reste de 2 niveaux. Cette amélioration locale ne démontre pas la cause des écarts de bord ni la fidélité sur les modèles quality.

```sh
node --test outils/labo/mesh-storm-normal-bake/*.test.mjs
```
