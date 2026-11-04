# Film V6 de Creative « Trois mots. » : concept, découpage, sources (03-04/11/2026)

## Ce qu'on retient de l'historique
- **V4 (goutte d'or, 6,5/10, le meilleur)** : une image de luxe photoréaliste (goutte d'or dans l'eau noire, flacon), une histoire
  produit lisible (phrase → plan → film), un seul registre maîtrisé. Elle a plu parce qu'elle montrait **un vrai résultat beau** et
  **le vrai parcours**. Ses défauts : 24 s d'interface avant le premier « wow », textes timides, aucun spectacle.
- **V3 (bataille spatiale, 3/10)** : 60 s d'un seul genre, caméra lente, vaisseaux « jouets », particules de compositing « jeu vidéo ».
- **V5 (atelier de vélos)** : banal, lent, beaucoup d'interface, voix « trop smooth » (direction « calme, intime, lent »).
- **Recherche 23** (102 promos) : plan fort avant 1 s, plans de 2 s en moyenne, musique d'énergie 8/10 qui s'arrête avant la
  révélation, voix des personnages plutôt qu'un narrateur lisse, une preuve visible par capacité, mur de résultats, fin courte + bonus.
- Les deux courts cités par le fondateur : Kling 4.0 (typographie cinétique énorme, un chapitre = une capacité + sa preuve) et
  Higgsfield × Opus 5.5 (un personnage tape des ordres très courts, l'outil fabrique, humour, boucle danger → phrase → résultat).

## L'idée
On tape **trois mots à l'arrache** (fautes comprises), on clique « Booster ma phrase », le texte réécrit par le LLM de Creative
**explose à l'écran**, et le plan qui en sort est un plan de blockbuster. Le motif revient quatre fois et **escalade** :
dragon → bataille spatiale (« PLUS GROS. ») → duel aux lames d'énergie (« PLUS FOU. ») → explosion au ralenti (« PLUS GRAND. »),
puis la palette en chapitres Kling (détourage avant/après, Relief fil de fer → argile → texturé, voix native, Mode Studio, Marketing,
mur des prises), un silence, on tape **« tout »**, et toutes les réécritures du film explosent ensemble avant la reprise finale
(dragon contre croiseur, flotte de dragons à l'aube). Carton remplaçable, puis **scène bonus** : la vraie faute de frappe
« dragn chato feu » que le LLM a lue « chat » : un petit chat crache du feu.

**Ce qui est réel** : chaque phrase est tapée dans le vrai Creative (serveur de la branche, LLM de production z-ai/glm-5.3 via
OpenRouter) ; la version boostée affichée est celle du LLM ; elle sert telle quelle d'intention au mode Image (image clé
Qwen-Image-2.1, réécrivain d'image du studio) puis à « Créer » en Qualité cinéma (réécrivain H3 du studio, h3-max sur la 5090),
avec un mouvement de caméra choisi dans les préréglages du studio. Le détourage, Relief, le Mode Studio, Marketing et la
bibliothèque sont des captures Playwright de l'application réelle. Les deux plans à réplique (pilote, duelliste) sont des prompts
H3 écrits à la main (le studio ne gère la réplique qu'en français) : c'est le même moteur, mais pas le parcours client.
Le kit de marque Marketing « Studio Braise » est fictif (poste de développement).

## Délégation des concepts (même brief)
- **Muse** (« Tape n'importe quoi ») : bon squelette, motif à 4 s max, budget d'interface de 7 s. Gardé : le plafond d'interface.
- **Gemini 4 Argon** (« Tapé à l'arrache. Filmé en IMAX ») : le plus riche (10 plans, chapitres outils) mais surchargé (73 mots,
  trop de fonctions). Gardé : HUD à chevrons, décomposition détourage, « 3D Relief » fil de fer → texturé.
- **DeepSeek** (« Quatre mots », incomplet : limite de tours) : escalade « plus gros / encore / tout », chaîne finale de raccords.
  Gardé : le mot final « tout ».
- Mon choix : le squelette « trois mots → boost → plan » qui escalade, la grammaire de la recherche 23, la scène bonus du chat.

## Découpage (temps de 0,4807 s à 124,81 BPM, drop du morceau à 2,40 s) : voir `montage_v6.py`
| temps film | bloc | contenu |
|---|---|---|
| 0–0,7 | accroche | le dragon crache sur la tour (son natif + sub) |
| 0,7–2,4 | motif 1 | « dragn chateau feu » tapé, boost qui explose (« Trois mots. » « L'IA écrit le reste. ») |
| 2,4–6,3 | dragon | 3 plans sur le drop, « PLUS GROS. » |
| 6,3–12,5 | espace | saisie + boost, plongée drone entre les croiseurs, la pilote crie « Bouclier ! Maintenant ! » |
| 12,5–18,5 | duel | saisie + boost, duel, réplique « C'est tout ?! », **trou musical** sur le choc des lames, « PLUS GRAND. » |
| 18,5–22,1 | explosion | saisie + boost, voiture qui explose en temps figé |
| 22,1–29,8 | palette | DÉTOURAGE (brut → masque → final), 3D RELIEF, VOIX, MODE STUDIO, MARKETING, mur des prises |
| 29,8–36,5 | silence | on tape « tout », toutes les réécritures explosent, « TOUT. » |
| 36,5–48 | climax | rafale de 1 à 3 temps puis la flotte de dragons à l'aube (« T'écris trois mots. On fait le film. ») |
| ~48–51 | carton | unique, remplaçable (`marque-v6.json`) |
| ~51–55 | bonus | « dragn chato feu » → le chat qui crache du feu |

## Fichiers
`capturer_boost.mjs` (saisie + boost réels), `capturer_relief.mjs`, `capturer_detourage.mjs`, `capturer_pages.mjs`,
`capturer_studio.mjs`, `tourner.py` (images clés et plans par l'API du studio, file limitée à 6 de mes travaux), `prises.py`
(rushes), `coupes.py`, `planche_rush.sh`, `voix_casting.py` / `voix_mesure.py` / `voix_qwen_pc1.py` / `voix_h3.py` /
`voix_narration.py` (distribution et narration), `musique_v6.py` (Lyria 3 Pro), `montage_v6.py` → `montage-v6.json`,
`monter_v6.py` + `effets_v6.py` + `sfx_v6.py` (moteur de montage écrit par Codex, relu), `archiver.py` (copie sur pc1 et
INVENTAIRE.csv), `lancer-studio.sh` (studio de la branche avec le LLM de production, clé jamais affichée).
Données : `~/nexora-creative-data/promo/v6-creative/` (captures, rushes, voix, musique, montage, journaux, tournage.jsonl).
