# Palette commune de voix (manche 1 du 03/11 et manche 2 du 04/11, mêmes répliques pour tous)

Manche 2 (consigne du fondateur du 04/11) : Mistral Voxtral TTS 3 et 2603 (voix préréglées françaises : OpenRouter refuse le clonage
pour ces modèles), MiniMax Speech 2.8 HD, MAI-Voice-2.1 (voix canadiennes-françaises fr-CA Sylvie, Antoine, Thierry, Jean) et Fish S2.1 Pro
(clonage). Aucune ne dépasse les meilleures de la manche 1 à l'oreille de machine ; les voix fr-CA de MAI sont québécoises mais plates.
Attention : les deux manches ont été jugées à quelques heures d'écart ; l'écart de 1 point entre manches n'est pas significatif.

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
| `fish21-jeannemance` | femme | Fish S2.1 Pro | 7.0 | 6.0 | 6.5 | 7.0 | 6.5 | 0.0 | 22.3 | 3.24 | Fish S2.1 Pro, clonage de jeannemance |
| `qwen3tts-jeannemance` | femme | Qwen3-TTS 1.7B, local GB10 | 7.0 | 5.5 | 6.0 | 7.0 | 6.5 | 0.0 | 23.1 | 3.29 | Jeanne Mance, voix québécoise, « charmante, claire et jeune » |
| `eleven-adamqc` | homme | ElevenLabs v4 | 6.5 | 5.8 | 6.0 | 6.8 | 6.3 | 0.028 | 18.9 | 5.41 | Adam, voix québécoise d'âge moyen, « chaleureuse et amicale » |
| `fish21-frederic` | homme | Fish S2.1 Pro | 6.5 | 6.0 | 5.5 | 7.0 | 6.0 | 0.0 | 17.7 | 4.26 | Fish S2.1 Pro, clonage de frederic |
| `drama3-marieline` | femme | Fish Audio Drama 3 | 7.0 | 4.5 | 5.0 | 8.0 | 6.0 | 0.074 | 20.8 | 4.63 | Marie Line, voix québécoise d'âge moyen, « énergique et claire » |
| `drama3-thomas` | homme | Fish Audio Drama 3 | 2.8 | 7.5 | 6.8 | 8.8 | 4.2 | 0.0 | 17.8 | 5.5 | Thomas, jeune voix « claire, chaleureuse, professionnelle » (accent peu québécois à l'oreille de machine) |
| `qwen3tts-frederic` | homme | Qwen3-TTS 1.7B, local GB10 | 6.0 | 6.0 | 5.0 | 7.0 | 6.0 | 0.0 | 16.3 | 5.49 | Frédéric, voix québécoise d'âge moyen, « professionnelle et assurée » (bibliothèque ElevenLabs) |
| `eleven-thomas` | homme | ElevenLabs v4 | 4.2 | 6.2 | 6.2 | 8.2 | 4.7 | 0.022 | 18.1 | 4.32 | Thomas, jeune voix « claire, chaleureuse, professionnelle » (accent peu québécois à l'oreille de machine) |
| `mai21-fr-ca-jean` | homme | MAI-Voice-2.1 | 6.5 | 4.8 | 4.8 | 7.0 | 5.5 | 0.042 | 12.2 | 5.15 | MAI-Voice-2.1 (Microsoft), voix fr-CA-JeanNeural — canadienne-française |
| `drama3-amelie` | femme | Fish Audio Drama 3 | 4.5 | 7.5 | 3.0 | 8.0 | 5.0 | 0.0 | 16.4 | 4.55 | Amélie, voix québécoise, « jeune, assurée, amicale » |
| `fish21-amelie` | femme | Fish S2.1 Pro | 4.5 | 5.5 | 6.0 | 6.5 | 5.5 | 0.043 | 17.4 | 3.89 | Fish S2.1 Pro, clonage de amelie |
| `fish21-marieline` | femme | Fish S2.1 Pro | 4.5 | 5.0 | 6.0 | 7.0 | 5.5 | 0.0 | 20.5 | 3.54 | Fish S2.1 Pro, clonage de marieline |
| `mai21-fr-ca-sylvie` | femme | MAI-Voice-2.1 | 6.0 | 4.0 | 4.8 | 7.0 | 5.8 | 0.0 | 19.8 | 2.83 | MAI-Voice-2.1 (Microsoft), voix fr-CA-SylvieNeural — canadienne-française |
| `mai21-fr-ca-antoine` | homme | MAI-Voice-2.1 | 6.0 | 4.5 | 4.5 | 7.0 | 5.0 | 0.0 | 12.8 | 5.81 | MAI-Voice-2.1 (Microsoft), voix fr-CA-AntoineNeural — canadienne-française |
| `voxtral2603-fr_marie_happy` | femme | Mistral Voxtral 2603 | 2.0 | 5.5 | 6.0 | 7.0 | 6.0 | 0.0 | 21.9 | 2.4 | Mistral Voxtral Mini TTS (2603), voix préréglée |
| `mai21-fr-ca-thierry` | homme | MAI-Voice-2.1 | 6.0 | 4.0 | 4.0 | 7.0 | 5.0 | 0.0 | 12.7 | 6.08 | MAI-Voice-2.1 (Microsoft), voix fr-CA-ThierryNeural — canadienne-française |
| `voxtral3-v592` | femme | Mistral Voxtral 3 | 3.0 | 5.0 | 6.0 | 7.0 | 5.0 | 0.0 | 25.7 | 2.81 | Mistral Voxtral TTS 3, voix préréglée française |
| `minimax28-french_femaleanchor` | femme | MiniMax Speech 2.8 HD | 3.0 | 4.5 | 5.5 | 7.0 | 5.5 | 0.0 | 22.9 | 2.37 | MiniMax Speech 2.8 HD, voix French_FemaleAnchor |
| `voxtral3-v3137` | femme | Mistral Voxtral 3 | 3.0 | 5.0 | 6.0 | 7.0 | 4.5 | 0.0 | 25.6 | 2.82 | Mistral Voxtral TTS 3, voix préréglée française |
| `voxtral3-v589` | femme | Mistral Voxtral 3 | 2.5 | 4.5 | 6.0 | 7.0 | 5.0 | 0.0 | 27.3 | 2.4 | Mistral Voxtral TTS 3, voix préréglée française |
| `minimax28-french_malenarrator` | homme | MiniMax Speech 2.8 HD | 2.5 | 5.0 | 6.0 | 7.0 | 4.0 | 0.0 | 14.3 | 4.26 | MiniMax Speech 2.8 HD, voix French_MaleNarrator |
| `mai21-fr-fr-denise` | femme | MAI-Voice-2.1 | 3.0 | 4.5 | 5.0 | 7.0 | 4.0 | 0.0 | 21.9 | 2.0 | MAI-Voice-2.1 (Microsoft), voix fr-FR-DeniseNeural |
| `voxtral3-v3141` | femme | Mistral Voxtral 3 | 3.0 | 4.5 | 5.5 | 5.5 | 4.0 | 0.0 | 26.8 | 1.81 | Mistral Voxtral TTS 3, voix préréglée française |

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
- `fish21-amelie` : Bonne énergie et diction claire, mais l'accent est français standard plutôt que québécois et il y a une erreur d'accord à la lecture. / Bonne intonation générale avec une touche québécoise crédible, mais des erreurs de liaison et de grammaire nuisent au professionnalisme attendu pour ce rôle.
- `fish21-frederic` : L'accent québécois est reconnaissable avec un bon dynamisme, mais le timbre présente des artefacts métalliques qui trahissent une voix synthétique. / L'accent québécois est bien présent et le texte est respecté, bien que la livraison manque légèrement de punch publicitaire.
- `fish21-jeannemance` : Bonne prestation avec un accent québécois crédible et une diction claire pour le rôle. / L'accent québécois est crédible et la diction est claire, bien que le ton reste légèrement synthétique et manque un peu de dynamisme.
- `fish21-marieline` : Bonne diction générale et accent crédible, bien que le ton manque un peu de dynamisme. / L'articulation est nette et le ton professionnel convient au rôle, mais l'accent sonne beaucoup trop français standard pour une diffusion télévisée québécoise.
- `mai21-fr-ca-antoine` : L'articulation est claire mais le ton synthétique et le manque de dynamisme limitent l'impact publicitaire. / L'articulation est très claire avec un accent québécois standard, mais le ton demeure trop synthétique et manque d'énergie pour une publicité télévisée.
- `mai21-fr-ca-jean` : L'accent et l'articulation sont adéquats, mais l'intonation reste légèrement synthétique et manque d'énergie publicitaire. / L'accent et l'articulation sont justes, mais l'intonation manque de naturel et de dynamisme pour une publicité télévisée.
- `mai21-fr-ca-sylvie` : L'articulation est claire et l'accent est adéquat, mais l'intonation demeure trop lisse et robotique pour une publicité télévisée. / L'accent québécois est présent et la diction est claire, mais l'intonation demeure monotone et synthétique.
- `mai21-fr-ca-thierry` : Intonation trop synthétique et manque de dynamisme pour une publicité. / L'accent canadien est perceptible mais la livraison manque de dynamisme et trahit une origine synthétique.
- `mai21-fr-fr-denise` : L'articulation est nette, mais l'accent français standard et le ton légèrement synthétique ne conviennent pas au marché québécois. / Voix synthétique à l'accent français standard, trop lisse et inadaptée au marché québécois.
- `minimax28-french_femaleanchor` : Bonne diction professionnelle, mais l'accent de France ne convient pas au marché québécois. / L'accent est clairement européen et le ton manque de dynamisme pour une publicité québécoise, bien que la diction soit claire.
- `minimax28-french_malenarrator` : Bonne diction mais l'accent français standard ne convient pas au marché québécois. / L'accent est clairement européen et non québécois, avec un ton trop neutre pour le marché local.
- `qwen3tts-frederic` : Prise claire avec un bon rythme, mais le timbre trahit une voix de synthèse et l'accent manque un peu de naturel. / L'accent et l'énergie sont acceptables, mais la prosodie trahit légèrement la synthèse vocale.
- `qwen3tts-jeannemance` : Bonne diction québécoise et ton professionnel, mais l'intonation reste légèrement mécanique. / L'accent québécois et la clarté sont bons, mais le ton reste un peu lisse et synthétique.
- `voxtral2603-fr_marie_happy` : La voix est claire et dynamique, mais l'accent français de France est inadapté au marché québécois et la fin est tronquée. / L'accent français de France et la livraison trop lisse ne conviennent pas pour une publicité québécoise.
- `voxtral3-v3137` : L'interprétation est claire et professionnelle mais l'accent est purement européen et non québécois. / Bonne diction et ton professionnel, mais l'accent européen ne convient pas pour une publicité québécoise.
- `voxtral3-v3141` : La voix présente un accent français standard inadapté au marché québécois et l'enregistrement est tronqué avant la fin de la phrase. / Bonne clarté et ton professionnel, mais l'accent européen ne convient pas pour le marché québécois.
- `voxtral3-v589` : L'interprétation convient à un rôle d'adjointe, mais l'accent est clairement européen et manque de dynamisme pour une publicité québécoise. / Bonne clarté et débit fluide, mais l'accent européen ne convient pas pour une publicité québécoise.
- `voxtral3-v592` : Bonne diction mais l'accent est clairement français de France et la phrase est tronquée à la fin. / L'interprétation est claire et naturelle, mais l'accent européen ne convient pas du tout à une publicité québécoise.

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
