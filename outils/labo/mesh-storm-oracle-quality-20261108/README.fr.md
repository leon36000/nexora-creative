# Oracle Storm de normales — sources minimales de revue

Cette copie de code est séparée des assets et du dossier de sortie. Elle ne contient pas de GLB, PNG, rendu, cache, `node_modules` ni dépendance. Les chemins d’assets sont contrôlés par `inputs.json` (rôles, tailles, SHA-256); les appels exigent un dossier d’assets et un dossier de run vide, distincts et explicites. Aucun script n’écrit à côté de ses sources.

## Entrées

`inputs.json` : GLB quality amont (chemin absolu + SHA), extrait de 21 faces et GLB atlas (chemins relatifs à `MESH_ORACLE_ASSET_ROOT` + SHA), recalcul indépendant Terra (chemin relatif + SHA). Le GLB source quality 45 974 088 octets et le patch extrait 28 616 148 octets restent hors de ce paquet et hors Git. La vérification refuse les chemins manquants, liens symboliques, tailles/SHA inattendus et run absent, non vide, lié, dans un dépôt Git/worktree réel ou sous ComfyUI.

## Génération

Depuis cette copie de sources, définir trois variables :

```sh
export MESH_ORACLE_ASSET_ROOT=/media/pc6/Storage/Nexora/travail/mesh-quality-normal-patch-extract-20261108T-luna01
export MESH_ORACLE_RUN_DIR=/media/pc6/Storage/Nexora/travail/mesh-quality-normal-storm-repro-run-review-20261108T-luna02
mkdir -- "$MESH_ORACLE_RUN_DIR"
export MESH_NODE_PACKAGE_JSON=/media/pc6/Storage/Nexora/travail/wt-mesh-aretes-reconcilie-codex-20261104/app/package.json
./generate.sh
```

Créer d’abord le dossier de run vide sous `/media/pc6/Storage/Nexora/travail`; le script accepte uniquement un dossier vide réel, distinct du code et des assets. Il crée ensuite `payload-03` par création exclusive. Aucun package n’est installé. Environnement relevé : Node v24.22.0, Python 3.12.3, `@gltf-transform/core` 4.5.1, `sharp` 0.35.5, Blender 5.2.3/OpenUSD 26.03.

Les stages sont écrits uniquement dans `$MESH_ORACLE_RUN_DIR/payload-03/`. `compare_generated.py` compare les SHA de 14 stages USD aux références en `reference-stages-sha256.json`; il écrit un reçu uniquement à l’emplacement explicite si celui-ci n’existe pas.

## Rendu et analyse

Le rendu exige aussi `MESH_ORACLE_STAGE_DIR`, `MESH_ORACLE_OUTPUT_DIR` et `MESH_ORACLE_RUN_DIR` absolus et séparés; `MESH_ORACLE_STORAGE_ROOT` peut pointer vers une racine de banc temporaire (ex. `/tmp` sur PC3), avec les mêmes contrôles de symlink et de vrais dépôts Git; le script refuse une sortie dans/sous le dossier du code, garde un processus Blender/Hydra neuf par stage, et exige llvmpipe. Il écrit des readbacks dans le run, jamais à côté des sources. Après les readbacks, l’analyseur crée `storm-analysis-final` par mkdir exclusif et écrit les images/rapports en mode `x`; il refuse toute relance qui remplacerait ces sorties. Les résultats de référence sont conservés dans le dossier de preuve original. Validation GPU-free : 19 tests stdlib couvrent chemins, SHA et noms de stage. Le rendu n4 du renderer empaqueté a aussi été repris sur PC3 sous bwrap réseau isolé; son RGBA (1 228 800 octets) a le même SHA que le readback initial (`85b1432fddcc4202f06029c81f8d883eef62605704690cc21c8a9b8ed1f20873`). Reçu et sortie rapatriés sous `mesh-quality-normal-storm-pc3-n4-20261108T-luna01/` dans Storage.

## Limites mesurées

L’oracle tessellé n64 (86 016 triangles) n’a pas satisfait le critère préannoncé MAE ≤0,25 niveau RGB 8 bits et maximum ≤2 : n32↔n64 MAE 0,03095, maximum 12. Sur l’intersection de masque érodée de 2 px (12 496 pixels), MAE 0,03065 et maximum 1, mais cela ne transforme pas l’échec global en convergence. Y inversé vs n64 disponible : MAE 0,14875/max 12 sur masque union >3; intérieur érodé 12 494 px, MAE 0,15031/max 2. Portée limitée à l’extrait 21 faces, w constant, UV0 in-range, LINEAR/CLAMP et Hydra Storm/llvmpipe. Pas de conclusion Apple/Quick Look ou généralisée.
