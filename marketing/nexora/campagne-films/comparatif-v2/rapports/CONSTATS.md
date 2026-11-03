# Comparatif v2 : constats (03/11/2026)

**Chaîne** (une fois, pour tous) : `auteur.py` (le modèle écrit tout le film : concept, narration, plans avec SES prompts image/mouvement/son,
textes, musique, carton ; validation en code, une réparation par classe de violation, puis réparations mécaniques) → `plaques.py` (ses images
clés Qwen-Image sur la GB10, ses plans H3 sur la 5090 de pc1 : h3-max sur ses ≤ 3 plans héros, h3-fast ailleurs ; sa musique Music3 ;
contrôles noir/figé/doublon, une régénération) → `voix.py` (Chatterbox multilingue cloné sur une voix québécoise, contrôle Whisper,
3 prises max) → `monter_film.py` (tempo mesuré, coupes aimantées sur la grille réelle, typographie `usine/typo.py`, tableau M1–M10
et inserts d'interface en code, musique −11 dB sous la voix, −14 LUFS) → `rapport.py`, `infographie.py`.

**Ce qui diffère vraiment entre modèles** (les plaques ne sont plus partagées) : Éco écrit des plans corrects mais génériques et répète
(6 tableaux sur 16 plans en OPSYS-AI) ; Équilibré raisonne longtemps (≈ 15 000 à 22 000 jetons de sortie à l'effort « max ») pour une
copie sobre ; Expert fait les images les plus spectaculaires et les plus chargées en texte (14 lignes en WorkStudio) ; Opus 5.5 construit le
meilleur arc et la copie la plus québécoise et la plus vendeuse (« Rien ne part sans vous », « Tout est prêt. Rien n'est parti. »).
Aucun des douze n'atteint la porte de 8 : notes sévères 4,2 à 5,4.

**Tempo** : Music3 ne respecte pas le tempo demandé (demandé 96 à 120 BPM, mesuré 74 à 159, souvent la moitié ou le double) ;
le montage est recalé sur la grille mesurée (écart moyen des coupes 0,13 à 0,16 s).

**Voix** : voir `../voix-essais.md`. Chatterbox (MIT) intelligible (WER Whisper ≈ 0,03 à 0,12 par film) ; deux hallucinations de fin
de phrase rattrapées par la 3e prise ; l'accent québécois n'est pas vérifiable par la machine : à écouter.

**Faiblesses** : le produit n'apparaît jamais à l'écran (aucune vraie capture de Creative ni d'OPSYS-AI : le tableau M1–M10 est un
dessin du code) ; plans de nuit parfois trop noirs ; son non écouté par un humain ; Opus mesuré en jetons du sous-agent, pas en dollars.
