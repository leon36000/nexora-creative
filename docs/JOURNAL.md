# Journal — Nexora Creative

Une entrée par itération : date, lot, ce qui a été fait, preuves, échecs, prochaine action.

## 30/10/2026 — démarrage de la boucle autonome
- Conception et recherche (01 à 06) poussées sur `root/nexora-creative` (commit 0dad3d8).
- État machine : 145 Go libres sur `/` (en baisse : autres sessions), GB10, 121 Go de mémoire unifiée, Docker + NVIDIA Container Toolkit 1.20.1, aucun jeton Hugging Face local (les dépôts FastVideo et Wan visés ne sont pas « gated »).
- Tailles relevées sur Hugging Face : FastH3 V2 NVFP4 Comfy = DiT 13,6 Go + encodeur Qwen3-VL NVFP4 15,7 Go + VAE 5,2 Go (≈ 35 Go sélectifs) ; FastH3 Omni NVFP4 13,8 Go ; Wan 2.2 TI2V-5B ≈ 34 Go en dépôt officiel.
- Prochaine action : lot R (littérature) en parallèle du lot 0b (fork OpenField).

## 30/10/2026 — itération 1 (lot 0b)
- Import brut d'OpenField 96cf7c1 dans `app/` (commit c355ce9), `UPSTREAM.md`. `npm install` + `npm run typecheck` verts [TEST].
- Politique de licences en échec fermé (`app/server/nexora/licences.ts`) : LTX-2.x et tous ses dérivés, FLUX.2 dev, 4x-UltraSharp bloqués ; H3 permis seulement si le territoire du compte n'est pas US/UE/R.-U./Corée ; ensemble inconnu bloqué. Branchée sur `blockingReason`, `effectBlockingReason` et les rendus en moteur distant. Contexte de compte par requête (`compte.ts`, AsyncLocalStorage). 8 tests vitest verts [TEST].
- Téléchargement FastH3 V2 NVFP4 (≈ 35 Go) lancé en arrière-plan dans `~/nexora-creative-data/models`.
- Prochaine action : lot 1 (ComfyUI sur GB10).
