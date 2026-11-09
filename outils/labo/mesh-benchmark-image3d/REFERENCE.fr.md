# Références et limites du banc

Le parcours actuel Nexora/Object utilise `app/server/graphs/trellis.ts` (TRELLIS.2 ; le code propose aussi Pixal3D). Les candidats du protocole sont Nexora/TRELLIS.2, Pixal3D et Hunyuan3D-2.1 Shape + Paint. Les configurations réellement installées, poids, versions et prétraitements sont à établir avant tout essai ; la présence du code n'établit pas la disponibilité d'une chaîne exécutable.

Le témoin historique Hunyuan Paint sur une chaise a été mesuré avec deux versions d'OpenCV : 763,509 s et 57,172 s de temps interne, respectivement. Il s'agit de retexture d'un GLB existant, pas d'une génération complète image→3D, et d'un seul sujet. Le corpus préparatoire ne contient aucun résultat de génération nouveau.

- [Processus Nexora : deux alternatives, 20 entrées, juges et regard humain](../../../docs/PROCESSUS-TECHNOLOGIE.md).
- [TRELLIS.2, dépôt Microsoft](https://github.com/microsoft/TRELLIS.2) ; [Pixal3D, dépôt TencentARC](https://github.com/TencentARC/Pixal3D) ; [Hunyuan3D-2.1 Shape + Paint](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1).
- [Documentation image→3D de Meshy](https://docs.meshy.ai/en/api/image-to-3d) : référence documentaire de `recherche/18`, sans benchmark Nexora ni parité mesurée. Le nom « Meshify » n'identifie pas sans ambiguïté ce service.

Les images du corpus doivent être tracées au fichier et leur origine décrite. Une partie provient des dépôts de candidats et six sont les images historiques générées par Qwen ; ce jeu préparatoire n'est pas un échantillon indépendant ni représentatif. L'origine individuelle des exemples amont n'est pas établie. Les résultats, échecs, versions, temps et mémoire devront être relevés au moment d'une exécution réelle, avec deux juges et un regard humain.
