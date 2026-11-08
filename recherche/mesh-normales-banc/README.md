# Banc Blender des normales OBJ

Ce script est la copie exacte du renderer du banc de la chaise Nexora ; il est spécifique aux trois actifs identifiés dans `manifest.json`. Les actifs, images, fichiers Blender et résultats sont conservés hors Git. Ce banc mesure une comparaison géométrique et des rendus neutres ; il ne valide pas une importation GLB native, un matériau PBR complet ou une appréciation humaine.

Avec Blender 5.2.3 et Cycles CPU disponibles, créer un répertoire de travail neuf sur Storage contenant `inputs/` et `renders/`. Placer dans `inputs/` les trois fichiers portant exactement les noms et empreintes du manifeste. Depuis la racine du dépôt, lancer successivement :

```sh
blender --background --python recherche/mesh-normales-banc/rendu_blender.py -- --stage prepare --run-root "$RUN_ROOT"
blender --background --python recherche/mesh-normales-banc/rendu_blender.py -- --stage import-check-v5 --run-root "$RUN_ROOT"
blender --background --python recherche/mesh-normales-banc/rendu_blender.py -- --stage render --run-root "$RUN_ROOT"
```

`RUN_ROOT` désigne ce répertoire de travail préalablement créé. Les étapes écrivent leurs rapports sans écrasement ; `render` exige le rapport `import-check-v5` et des géométries compatibles. Le GLB est reconstruit depuis ses tableaux, avec deux normales de coin calculées depuis les faces ; les OBJ sont importés avec `validate_meshes=False`. Les rendus utilisent un matériau neutre, 768 × 768, 16 échantillons et deux threads CPU. Les limites et réglages précis figurent dans le script.
