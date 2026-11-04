# Palette commune de voix (banc du 03/11/2026, une seule ronde, mêmes répliques pour tous)

Chaque équipe choisit par rôle une **voix de la palette** (colonne `id`), écrit le texte, la direction de jeu et la vitesse.
Notes sur 10 de l'**oreille de machine** (Gemini 4 Argon, audio, deux passes, sévère : 8 = diffusable à la télé au Québec) ;
ce n'est pas une écoute humaine. EMR = erreur de mots Whisper ; c/s = caractères par seconde (débit) ; relief = écart-type de
la hauteur en demi-tons (une voix « smooth » a peu de relief).

| id | genre | moteur | accent QC | énergie | naturel | clarté | rôle | EMR | c/s | relief | voix |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `eleven-jeannemance` | femme | ElevenLabs v4 | 9.0 | 7.2 | 8.2 | 9.0 | 8.2 | 0.056 | 21.5 | 3.65 | Jeanne Mance, voix québécoise, « charmante, claire et jeune » |
| `drama3-frederic` | homme | Fish Audio Drama 3 | 9.0 | 7.0 | 8.0 | 9.0 | 8.0 | 0.0 | 16.5 | 5.65 | Frédéric, voix québécoise d'âge moyen, « professionnelle et assurée » (bibliothèque ElevenLabs) |
| `drama3-adamqc` | homme | Fish Audio Drama 3 | 8.2 | 7.2 | 7.5 | 8.8 | 7.8 | 0.042 | 19.5 | 5.18 | Adam, voix québécoise d'âge moyen, « chaleureuse et amicale » |
| `eleven-frederic` | homme | ElevenLabs v4 | 8.3 | 6.0 | 7.7 | 8.3 | 7.7 | 0.042 | 18.7 | 4.74 | Frédéric, voix québécoise d'âge moyen, « professionnelle et assurée » (bibliothèque ElevenLabs) |
| `eleven-marieline` | femme | ElevenLabs v4 | 8.0 | 5.5 | 7.5 | 9.0 | 7.5 | 0.074 | 22.3 | 4.36 | Marie Line, voix québécoise d'âge moyen, « énergique et claire » |
| `eleven-amelie` | femme | ElevenLabs v4 | 8.5 | 5.5 | 6.8 | 8.5 | 7.0 | 0.058 | 21.1 | 3.54 | Amélie, voix québécoise, « jeune, assurée, amicale » |
| `drama3-jeannemance` | femme | Fish Audio Drama 3 | 6.7 | 6.7 | 6.5 | 8.7 | 6.3 | 0.039 | 19.1 | 3.99 | Jeanne Mance, voix québécoise, « charmante, claire et jeune » |
| `eleven-alexandre` | homme | ElevenLabs v4 | 4.5 | 7.0 | 7.5 | 8.5 | 7.0 | 0.0 | 15.2 | 5.4 | Alexandre Boutin, voix des films V5 (jugée « beaucoup trop smooth » par le fondateur) |
| `qwen3tts-jeannemance` | femme | Qwen3-TTS 1.7B, local GB10 | 7.0 | 5.5 | 6.0 | 7.0 | 6.5 | 0.0 | 23.1 | 3.29 | Jeanne Mance, voix québécoise, « charmante, claire et jeune » |
| `eleven-adamqc` | homme | ElevenLabs v4 | 6.5 | 5.8 | 6.0 | 6.8 | 6.3 | 0.028 | 18.9 | 5.41 | Adam, voix québécoise d'âge moyen, « chaleureuse et amicale » |
| `drama3-marieline` | femme | Fish Audio Drama 3 | 7.0 | 4.5 | 5.0 | 8.0 | 6.0 | 0.074 | 20.8 | 4.63 | Marie Line, voix québécoise d'âge moyen, « énergique et claire » |
| `drama3-thomas` | homme | Fish Audio Drama 3 | 2.8 | 7.5 | 6.8 | 8.8 | 4.2 | 0.0 | 17.8 | 5.5 | Thomas, jeune voix « claire, chaleureuse, professionnelle » (accent peu québécois à l'oreille de machine) |
| `qwen3tts-frederic` | homme | Qwen3-TTS 1.7B, local GB10 | 6.0 | 6.0 | 5.0 | 7.0 | 6.0 | 0.0 | 16.3 | 5.49 | Frédéric, voix québécoise d'âge moyen, « professionnelle et assurée » (bibliothèque ElevenLabs) |
| `eleven-thomas` | homme | ElevenLabs v4 | 4.2 | 6.2 | 6.2 | 8.2 | 4.7 | 0.022 | 18.1 | 4.32 | Thomas, jeune voix « claire, chaleureuse, professionnelle » (accent peu québécois à l'oreille de machine) |
| `drama3-amelie` | femme | Fish Audio Drama 3 | 4.5 | 7.5 | 3.0 | 8.0 | 5.0 | 0.0 | 16.4 | 4.55 | Amélie, voix québécoise, « jeune, assurée, amicale » |

## Avis de l'oreille de machine (extraits)

- `drama3-adamqc` : Bonne dynamique générale et un accent globalement convaincant, mais le 'pis' lu comme 'puis' et une légère rigidité trahissent la synthèse vocale. / Bonne prise naturelle et efficace avec un accent québécois crédible qui correspond très bien au rôle d'administrateur.
- `drama3-amelie` : L'énergie est là, mais le timbre synthétique et la faute de prononciation sur 'ratios' rendent la prise inutilisable en l'état. / Malgré un bon niveau d'énergie, l'accent est purement hexagonal et la prosodie sonne résolument synthétique, ce qui rend la prise inutilisable pour une publicité québécoise.
- `drama3-frederic` : Très bonne prise avec un accent québécois authentique et une diction claire, même si l'intention pourrait être encore un peu plus percutante pour un ton dramatique. / Bonne prestation avec un accent québécois naturel et une articulation claire, bien que la liaison sur « se met-t-au » fasse un peu trop soutenue.
- `drama3-jeannemance` : Très bonne prise avec un accent québécois naturel (l'affrication sur Thibault est juste) et une élision naturelle sur 'demandé', tout à fait crédible et diffusable pour le rôle d'adjointe. / Excellente prise, l'accent québécois est très naturel avec une bonne affrication et le ton professionnel correspond parfaitement au rôle d'adjointe.
- `drama3-marieline` : L'accent québécois est présent (notamment sur « Thibault »), mais l'intonation reste trop lisse, mécanique et manque d'incarnation pour une diffusion télévisée convaincante. / L'accent québécois est présent (notamment sur « Thibault »), mais l'intonation reste trop robotique et manque de vie pour une publicité télévisée.
- `drama3-thomas` : Bonne énergie publicitaire et voix claire, mais l'accent français de France est totalement inadapté pour une diffusion ciblant le marché télévisuel québécois. / Bonne énergie et clarté, mais l'accent est clairement français de France, ce qui est inutilisable pour le marché québécois.
- `eleven-adamqc` : Bonne diction et accent adéquat, mais l'intonation reste légèrement synthétique et manque de punch publicitaire. / Bonne diction et accent adéquat, bien que l'énergie reste modérée pour une publicité.
- `eleven-alexandre` : Une bonne livraison dynamique au standard radio-canadien, mais la liaison sur « se met au » sonne trop littéraire et française pour la télé d'ici. / Bonne énergie de narration publicitaire, mais l'accent sonne beaucoup trop français de France pour le marché québécois et il y a une faute de liaison grammaticale sur « met au ».
- `eleven-amelie` : L'accent québécois est authentique et le ton professionnel correspond bien au rôle d'adjointe, mais la livraison gagnerait à être un peu plus dynamique pour la télévision. / L'accent québécois est très convaincant avec de bonnes élisions naturelles, mais la livraison manque un peu de dynamisme pour une publicité télévisée.
- `eleven-frederic` : Bonne prestation avec un accent québécois authentique et une diction claire, tout à fait diffusable pour une publicité. / Très bonne prise avec un accent québécois authentique et une diction claire, tout à fait diffusable bien qu'un peu plus de punch aurait servi la finale.
- `eleven-jeannemance` : Très bonne prise, l'accent québécois est authentique et le ton professionnel correspond parfaitement au rôle d'adjointe. / Excellente prise très naturelle avec un bel accent québécois authentique, idéale pour le rôle d'adjointe et prête pour la diffusion.
- `eleven-marieline` : Bonne diction, mais le ton est un peu trop lisse et manque de naturel spontané pour une publicité québécoise. / L'accent québécois est authentique et le ton professionnel convient bien au rôle d'adjointe, bien que la livraison soit un peu lisse façon SVI plutôt que dynamique pour la télévision.
- `eleven-thomas` : Bonne dynamique, mais l'accent manque d'authenticité québécoise et l'intonation paraît légèrement synthétique. / La livraison est claire mais l'accent européen et la liaison forcée ne conviennent pas au marché québécois.
- `qwen3tts-frederic` : Prise claire avec un bon rythme, mais le timbre trahit une voix de synthèse et l'accent manque un peu de naturel. / L'accent et l'énergie sont acceptables, mais la prosodie trahit légèrement la synthèse vocale.
- `qwen3tts-jeannemance` : Bonne diction québécoise et ton professionnel, mais l'intonation reste légèrement mécanique. / L'accent québécois et la clarté sont bons, mais le ton reste un peu lisse et synthétique.

## Ce qu'il faut savoir

- **Voix native de H3** (essai : l'adjointe dit sa réplique dans le plan, sans voix ancrée) : accent québécois 8,5/10 à l'oreille, mais
  **erreur de lecture** (« 16 h » dit « 6 h ») et naturel 6,5 : non fiable pour un texte exact. La chaîne ancre donc toujours une prise
  de la palette dans les plans parlants (lèvres synchronisées sur cette voix).
- Drama 3 garde l'accent de la voix clonée quand la référence est très québécoise (Frédéric, Jeanne Mance), le perd parfois (Thomas, Amélie).
  Il accepte une consigne de jeu en langage naturel (`direction`) et `vitesse` (1,0 à 1,3 sans erreur de mots mesurée). Il tourne aussi en
  local (GB10 FP8, RTF 0,83 ; 5090 int4, RTF 0,12, mais la 5090 est prise par H3).
- ElevenLabs v4 : balises de jeu entre crochets dans `direction` (« [energetic, punchy] »), vitesse non garantie (réglée au montage).
- Qwen3-TTS : local, licence permissive, pas de consigne de jeu (le jeu vient de la référence clonée).
- Échantillons (fichiers .wav) : `~/nexora-creative-data/work/opsys-ultime/casting/voix/` sur pc6 ; copie sur pc1.
