# Films V5 : manifeste des livrables (03/11/2026)

Les livraisons précédentes ne sont pas modifiées.

## pc1 · `/home/pc1/Bureau/Nexora-Livrables/`
- `films-v5/` : `V5-<creative|opsys|workstudio>-<16x9|9x16>-fr-master.mp4` (x264 CRF 15, AAC 320 k) et les versions web
  `V5-…-fr.mp4` (H.264 deux passes, ≤ 25 Mo, AAC 192 k).
- `infographies/v5/` : `infographie-<film>-1080x1350.png` et `-1080x1080.png`.
- `rapports/v5/` : `RAPPORT.md`, `MANIFESTE.md`, `audio-choix.json` ; par film : `SCENARIO.md`, `film.json`,
  `revue-<format>.json` (rythme, temps d'écran du produit, loudness, poids), `planche-<film>-<format>.jpg` (une image par seconde).
- `audio/v5/<film>/` : `audio/` (stems voix, musique, bruitages ; `mix.wav` ; `audio.json`), `voix/<moteur>/` (une phrase par
  fichier : ElevenLabs v4 Alexandre retenu ; essais ElevenLabs v3 et Drama 3 clone conservés), `musique/` (deux propositions
  Lyria 3 Pro et leur grille mesurée).

## pc1 · `/run/media/pc1/Infrastructure/NexoraStudioWork/films-v3/<film>/`
Travail complet : captures réelles (Creative : flux CDP de 1 032 images, PNG 3840×2160, film produit `/api/media/63`),
plaques H3 (16:9 et 9:16, journal `plaques/plaques.json`, rejets conservés), rendus image et masters.

## pc6 · `~/nexora-creative-data/promo/montage/`
`V5-creative-16x9-fr.mp4`, `V5-creative-9x16-fr.mp4`, `V5-opsys-16x9-fr.mp4`, `V5-opsys-9x16-fr.mp4`,
`V5-workstudio-16x9-fr.mp4`, `V5-workstudio-9x16-fr.mp4` (versions web à envoyer).

## Provenance et vérité
- Creative : session réelle du Producteur sur la VM 202 (03/11, palier Expert, 2 prises par plan, juge, montage, bande
  originale), film réellement produit ; imprimés de `marketing/nexora/imprimes/final/` (« conçus avec nos outils »).
- WorkStudio : captures réelles de l'exécution du 02/11 (VM 203) ; lumière du flux, rond d'appui et envoi dessinés et étiquetés.
- OPSYS-AI : « Vision · en développement » à l'écran ; Console réelle (données fictives) ; tableau M1–M10 dessiné d'après
  `films/opsys/FAITS.md` (actions marquées RÉEL) ; plaques « marteau », « soir », « matin » reprises d'opsys-opus (v2) en 16:9.
- Plaques : MiniMax H3 sur la RTX 5090 de pc1 (h3-max 10Eros-Max pour les héros, h3-fast sinon ; Qwen-Image 2.1 pour les
  images clés tant que la GB10 était libre). Licence MiniMax H3 Community à relire avant diffusion commerciale (fondateur).
- Voix : ElevenLabs v4 « Alexandre » via OpenRouter. Musique : Lyria 3 Pro via OpenRouter (provisoire).
