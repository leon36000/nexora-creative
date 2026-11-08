# Reprojection expérimentale vers le repère Storm

`reprojectNormal` convertit **un échantillon** de normale glTF dans le repère dérivé de `P` et `st=(u,1-v)` utilisé par OpenUSD Storm 26.03. Il reproduit le chemin Three.js r186 à tangentes explicites : normales, tangentes et bitangentes par sommet sont normalisées et interpolées séparément, sans orthogonalisation après interpolation. La fonction résout la matrice cible plutôt que de supposer que le repère source interpolé est orthogonal.

La fonction reçoit trois coins dans le même espace objet, UV de la carte normale, coordonnées barycentriques et un texel RGB brut déjà échantillonné, ainsi que `normalScale`. Elle renvoie la normale cible en espace tangent et les vecteurs de contrôle; elle n’écrit pas de fichier. Elle refuse notamment les signes `w` mixtes, valeurs non finies, UV/géométrie dégénérés et orientations instables. La garde d’orthogonalité concerne seulement les paires N/T **aux sommets** (tolérance restrictive 1e-4); elle n’exige pas l’orthogonalité des vecteurs interpolés. Ces refus sont propres à cette expérience et ne constituent pas une classification générale de validité glTF.

```sh
node --test outils/labo/mesh-storm-frame/reproject.test.mjs
```

Les tests couvrent UV miroir, tangentes tournées, normales variables, repère interpolé non orthogonal, facteur nul et refus. Un oracle numérique indépendant vérifie les valeurs sur deux repères fixes. La fixture synthétique à quatre faces a aussi été vérifiée analytiquement aux centroïdes contre les formules GLSL Storm; cela ne remplace pas un rendu du rebake. Cette fonction ne gère ni lecture de texture, filtres, nœuds transformés, animation, atlas, recouvrements UV, ni toute une scène. Elle suppose une face avant; les faces arrière `doubleSided` ne sont pas couvertes. Elle n’est reliée ni au produit ni à l’export USDZ; les cartes normales et AO continuent d’être refusées par ce dernier.

Un atlas expérimental utilisant cette fonction sur une fixture à quatre faces (UV direct/miroir, normales variables et tangentes alignées ou tournées) a été comparé à un témoin géométrique dans Storm/llvmpipe. Dans la vue testée, l’écart maximal est de 1 niveau RGB 8 bits sur l’intérieur érodé; le maximum global atteint 28 niveaux dans la bande de bord, dont la cause exacte reste à établir. Cette mesure ne valide ni les autres lecteurs, ni le champ complet d’un modèle quality.
