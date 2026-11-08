# Banc privé de rebake des normales glTF

Ce paquet de laboratoire vérifie une hypothèse ciblée : conserver le `TANGENT` glTF explicite, lire une vraie texture de normale raw avec son jeu UV dédié, appliquer `normalTexture.scale`, puis rebaker cette normale monde dans un atlas UV0. Il ne change aucun fichier produit.

## Contenu

- `scripts/create_private_overlay.py` copie et adapte le seul module `nodes_mesh_postprocess.py` fourni à l’exécution. Le SHA source est épinglé; le module Comfy complet n’est pas inclus. Les sorties dans Comfy ou un dépôt Git, les liens symboliques et les fichiers existants sont refusés.
- `scripts/test_normalmap_rebake.py` génère la fixture GLB, appelle `BakeNormalMapFromMesh.execute` et `ApplyTextureToMesh.execute` de la copie privée, sérialise le GLB cible, puis compare numériquement les normales monde des textures source et rebakée.
- `scripts/run_cpu_isolated.sh` lance Python en CPU dans `bwrap --unshare-net`; la racine est montée en lecture seule et seul le dossier de run est inscriptible, monté à son chemin absolu sans masquer `/run`.
- `fixtures/` contient la fixture source générée (GLB de 2 060 octets et PNG raw RGB de 118 octets).
- `references/analytical-proof-v3.json` conserve le rapport analytique du run validé.
- `validation/` contient le récapitulatif indépendant Three.js/SwiftShader, ses deux contrôles, PNG et rapport complet.

## Reproduire

Utiliser le runtime Comfy privé déjà installé, sans installer ni modifier de dépendances. Exemple pour un nouveau dossier de run vide :

```bash
PACKAGE=/chemin/vers/outils/labo/mesh-normalmap-rebake-20261108
COMFY_ROOT=/home/pc6/nexora-creative-data/engine/ComfyUI
PYTHON=/home/pc6/nexora-creative-data/engine/venv/bin/python
RUN=/media/pc6/Storage/Nexora/travail/mesh-normalmap-rebake-run-20261108-unique
mkdir -p "$RUN"/{inputs,results,reports,tmp,overlay}
python3 "$PACKAGE/scripts/create_private_overlay.py" \
  --source "$COMFY_ROOT/comfy_extras/nodes_mesh_postprocess.py" \
  --output "$RUN/overlay/nodes_mesh_postprocess.py"
"$PACKAGE/scripts/run_cpu_isolated.sh" \
  "$COMFY_ROOT" "$PYTHON" "$RUN/overlay/nodes_mesh_postprocess.py" \
  "$RUN" "$PACKAGE/scripts/test_normalmap_rebake.py"
```

Choisir un nouveau dossier à chaque essai. Les scripts refusent de remplacer un overlay existant et le test refuse de réutiliser ses sorties. Le lanceur ne définit ni ne modifie `HOME`; il vide l’environnement du processus et fournit seulement les variables nécessaires au runtime isolé.

Les tests de refus, sans Comfy ni GPU, se lancent avec `python3 -B -m unittest discover -s "$PACKAGE/tests" -v`.

## Versions épinglées et preuve

- Python `3.12.3`, Torch `2.14.1+cu130` en CPU, NumPy `2.5.4`, Pillow `13.0.0`, bubblewrap `0.9.0`.
- `nodes_mesh_postprocess.py` source : SHA-256 `3b7083984c974d9bc5d14e026a37d0eee0a4063b61a7df20ae15bdd68015a141`.
- `gltf_read.py` : SHA-256 `298915d308ba14bc519cce8a9dd01bba36d414a95f61f9ba79a261ddb07bdb5b`.
- `nodes_save_3d.py` : SHA-256 `7fa90b74bc140ae811220374f34a3bda0abb9af395809850b5069163a22f8b87`.
- GLB source : SHA-256 `1d805fe01a756def94de42e89ae797f6b87b0cc342d5a43d2be7904651aeae9b`.
- GLB rebaké : SHA-256 `21c561cdd9e3f8ead326650ace459102af54a19eb03c1b580bce94c5cac2ac18`.
- Rapport analytique v3 : SHA-256 `95aa019046354387c73ff94915b6480ec429adf9b7e9987ea16f1b66fff0f56b`.

La fixture comporte deux triangles frontaux, six sommets dupliqués par coin, des tangentes explicites avec `w=+1` puis `w=-1`, et `TEXCOORD_0` d’atlas distinct de `TEXCOORD_1` source. Les UV restent dans `[0,1]`. La texture normal raw est asymétrique, échantillonnée LINEAR avec CLAMP_TO_EDGE, `normalTexture.scale=0.35`; la cible met la carte rebakée sur UV0 avec scale `1.0`.

Mesure analytique après réouverture des GLB : 210 pixels intérieurs par triangle; angle moyen source→cible `0,365°` pour le triangle source `w=+1` et `0,326°` pour `w=-1` (maxima respectifs `0,669°` et `0,574°`). Ces valeurs sont un contrôle numérique à repère tangent constant par triangle; elles ne remplacent pas le lecteur.

Contrôle indépendant Three.js `r186` avec ANGLE/SwiftShader, mêmes caméra et lumière : 5 917 pixels différents sur 307 200, différence de canal maximale `1/255`, MAE RGB encodée sur l’image entière `0,01926/255`. Le témoin source `normalScale=0` change 15 791 pixels, avec un maximum de `13/255`, ce qui confirme que la scène réagit à la carte normale. Les sorties et rapports originaux sont conservés sous `validation/`.

## Limites

La preuve couvre seulement deux triangles avec normales, tangentes et `w` constants par face. Elle n’établit pas le comportement pour `w` mixtes par triangle, normales/tangentes variables, repeat, UV hors `[0,1]`, UDIM, `KHR_texture_transform`, ni d’autres lecteurs. La source utilise `TEXCOORD_1` et la cible atlas UV0. Cette comparaison ne constitue pas une validation Apple/Quick Look ni une équivalence PBR générale.

Les échecs des runs v1 et v2 sont préservés dans le dossier Storage du banc, pas dans ce paquet : v1 utilisait la clé de primitif avant fusion; v2 s’arrêtait après export sur la même différence de clé lors du contrôle. Le run v3 complet est reproductible dans `references/`.

## Fixture à repères variables

Pour refaire le deuxième banc, employer les mêmes commandes dans un nouveau dossier vide et remplacer `test_normalmap_rebake.py` par `test_varying_frame.py`. Sur deux triangles distincts, les normales et tangentes varient par sommet; les signes restent constants par face. Les contrôles analytiques pour les deux interpolations exigent un angle maximal inférieur à 1,5° sur les pixels intérieurs. Ce seuil concerne cette fixture et ne prouve pas la fidélité générale ou le comportement des w mixtes. Le comparatif Three/SwiftShader et les artefacts sont archivés dans le lot `mesh-normalmap-varying-frame-bench-20261108T-luna01` sur Storage et pc1.
