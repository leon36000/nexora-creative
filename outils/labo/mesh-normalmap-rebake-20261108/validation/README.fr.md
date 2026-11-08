# Reçu lecteur Three.js / SwiftShader

Les fichiers racine proviennent du run principal `/media/pc6/Storage/Nexora/travail/mesh-normal-rebake-reader-20261108/`; le sous-dossier `control/` provient du run témoin `/media/pc6/Storage/Nexora/travail/mesh-normal-rebake-reader-control-20261108/`. Les originaux Storage restent intacts. Les dossiers `tmp/` et `cache/` ne sont pas copiés.

Three.js r186 a chargé la source et le GLB rebaké avec ANGLE/SwiftShader, mêmes caméra et éclairage. Dans ces rapports, `fixture` désigne le GLB source et `fixture_mikk` le GLB rebaké. Ils ne signifient pas que les tangentes de la cible sont calculées par MikkTSpace.

- Paire source/rebake : SHA source `1d805fe01a756def94de42e89ae797f6b87b0cc342d5a43d2be7904651aeae9b`; SHA rebaké `21c561cdd9e3f8ead326650ace459102af54a19eb03c1b580bce94c5cac2ac18`.
- Mesure image entière : `5917/307200` pixels différents, canal maximal `1/255`, MAE RGB encodée `0.0192610677/255`.
- Sensibilité : dans le run `control/`, régler le normalScale source à zéro change `15791/307200` pixels, canal maximal `13/255`, MAE RGB encodée `0.2712109375/255`.

Les PNG sont les sorties conservées telles quelles, y compris `difference-x8.png`; les rapports JSON et le script `run.cjs` sont les originaux copiés avec leurs octets. Ce résultat qualifie uniquement la fixture et ce lecteur précis.
