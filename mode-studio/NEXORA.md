# Mode Studio : provenance et modifications Nexora

**Base** : FreeCut, https://github.com/walterlow/freecut, licence MIT (fichier `LICENSE`, conservé), commit
`5ceeeb388eef5423640b7db157706274bf1b8165` (29/10/2026). Choisi après recherche le 01/11/2026 (même pile que l'app
Creative : React 19, Vite, Zod 4, Zustand ; timeline multipiste, outils ripple/lame, moniteur, propriétés, vumètres,
export WebCodecs, transcription et sous-titres locaux, couche d'opérations d'édition validées). Écartés : Remotion et
react-video-editor (licences payantes au-delà de 3 salariés), OpenChatCut (AGPL + Remotion), Etro/Kdenlive/Shotcut (GPL),
OpenCut (en réécriture complète), omniclip (trop léger). Algorithmes d'édition par agent inspirés de FableCut (MIT).

## Modifications Nexora (à reporter en cas de reprise de l'amont)

| Fichier | Changement |
|---|---|
| `vite.config.ts` | `base: '/mode-studio/'`, relais `/api` vers le serveur Creative en développement, pas de source maps |
| `src/app.tsx` | `basepath: '/mode-studio'` du routeur |
| `src/main.tsx` | service worker désactivé |
| `src/routes/index.tsx` | l'accueil marketing redirige vers `/projects` |
| `src/features/workspace-gate/workspace-gate.tsx` | espace de travail dans le stockage privé du navigateur (OPFS), sans choix de dossier ; chemins protégés lus sans le préfixe `/mode-studio` |
| `src/components/brand/freecut-logo.tsx`, `index.html`, locales `fr`/`en` | marque « Mode Studio · Nexora Creative » |
| `src/config/community.ts` + barre d'outils et pages projets | liens Docs/Discord/GitHub de FreeCut masqués (`AFFICHER_LIENS_FREECUT`) |
| `src/config/editor-workspaces.ts` | onglets `assistant` et `creations`, assistant ouvert par défaut |
| `src/features/editor/components/media-sidebar.tsx` | onglets Assistant et Créations Nexora en tête |
| `src/features/nexora/` (nouveau) | assistant de montage, créations Nexora, actions d'IA, traduction des commandes vers les opérations FreeCut |

## Ce que fait la couche Nexora

- **Créations** : les rendus de l'organisation (vidéos MiniMax H3, images Qwen-Image, musiques MiniMax-Music3) posés d'un
  clic (à la suite sur la piste vidéo principale, ou sur une piste audio libre) ; génération directe d'un nouveau média.
- **Assistant** : demande en français → le LLM renvoie des commandes en secondes (texte, déplacer, couper, raccourcir,
  volume, transition, ajouter un clip, modifier) et des actions d'IA ; une demande = un seul pas d'annulation.
- **Actions d'IA** : couper les silences (ffmpeg silencedetect, suppression avec raccord), sous-titres (faster-whisper au
  mot, piste « Sous-titres », lignes de 42 caractères), montage au rythme (temps de la musique, coupes recalées, son lié
  synchronisé), génération d'un plan, d'une image ou d'une musique posée à la tête de lecture.
- Les analyses ne portent que sur les médias venus des créations Nexora (le serveur a leur fichier).
