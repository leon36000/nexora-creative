# Film V7 de Creative : passation (04/11/2026, 04 h 30) — arrêt demandé (économie de l'abonnement Claude)

## Fait
- Recette live action : `recette/` (prompts `recette_live.py`, juge `juge_reel.py` en Flex, mesures images clés
  `mesures-cles.json` : 5/6 duels gagnés, réalisme 2,9 → 7,0) ; note `recherche/26-recette-live-action.md`.
- Banc des voix francophones : `voix/banc_voix_v7.py`, résultats `voix/INDEX-banc.md`, palette `voix/PALETTE.md` ; échantillons :
  `~/nexora-creative-data/promo/v7-creative/voix-banc/` (`<moteur>-<voix>-<narration|cri>.mp3`). Tête du banc (oreille de
  machine) : Gemini 3.8 TTS Puck, Fenrir, Voxtral 3 voix 3146 (meilleur accent québécois). Voxtral local : poids CC BY-NC, exclu.
- Brief commun `BRIEF-V7.md`, prompt d'équipe `prompt-equipe.md`, chaîne `chaine/v7.py` (Codex, 37 tests ; README).
- Dossiers : `equipes/opus/` (« Chez toi. », écrit à l'aveugle, commit 3d30eee), `equipes/gemini/` (« LA FIN DU JEU. », Argon Flex
  élevé), `equipes/muse/` (« Tape petit. Vois grand. », écriture directe : la passerelle refusait Muse derrière Claude Code,
  conflit « reasoning_effort »). Corrections techniques : `equipes/<e>/CORRECTIONS.md`.

## En cours (processus lancés, à laisser tourner)
- Production `cles → plans → (voix) → musique` pour opus, gemini, muse (journaux `~/nexora-creative-data/promo/v7-creative/prod-<e>.log`,
  sorties `~/nexora-creative-data/promo/v7-creative/<e>/`). Lent : la GB10 est occupée par un banc H3 d'un autre agent et la 5090
  par les quatre films OPSYS ; reprise possible (la chaîne ne refait pas ce qui existe).
- DeepSeek : deux sessions d'agent coupées à 45 min (trop lent en effort max) ; écriture directe sur DeepInfra en cours
  (`ecriture_directe.py`, journal `…/ecriture/deepseek/ecriture.log`). Une fois `…/ecriture/deepseek/equipes/deepseek/dossier.json`
  écrit : le copier dans `equipes/deepseek/`, `python3 -B chaine/v7.py valider deepseek`, corriger le technique, lancer sa production.
- Banc vidéo de la recette (6 plans h3-max, `recette/specs-recette.json`) : 3 sur 6 rendus au moment de l'arrêt.

## Reste
1. Quand les plans d'une équipe sont faits : `monter <e> --brouillon`, `juger-musique <e>`, `planche <e>` ; ronde de révision
   (prompt de révision à écrire sur le modèle de `../../nexora/campagne-films/opsys-ultime/chaine/prompt-revision.md`, ≤ 6 unités).
2. Finals : `monter <e>` (16:9 + 9:16, fr), `telephone <e>` (≤ 28 Mo), `archiver <e>` (pc1 `TOUS-LES-FILMS/creative-v7/<e>/`), `bilan <e>`.
3. Compléter `recherche/26` (plans vidéo du banc, section son mesurée) ; notes sévères des quatre films (retirer ≥ 1,5 point).
Studio de la branche : `../video-v6/lancer-studio.sh` (ports 37170/37171), utilisé pour les captures et Music3.
