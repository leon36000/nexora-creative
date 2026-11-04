# 25 — Le réalisateur (« le LLM qui booste le tout ») et les effets en images de synthèse (Relief + Blender), 04/11/2026

Branche `feat/llm-booste`. Code : `app/server/nexora/realisateur.ts`, `reecritureH3.ts`, `bench/` (banc, juges, planches), `vfx/scene_blender.py`. Données brutes : `app/server/nexora/bench/resultats/reecriture-2026-11-04/`.

## 1. Ce qui existait

- `/api/nexora/creer` → `reecrireH3` : le LLM du poste (en production `z-ai/glm-5.3` par OpenRouter, raisonnement obligatoire) reçoit **le guide officiel H3 entier** (≈ 3 700 jetons) et rend un prompt ; un validateur vérifie la forme, deux réparations, puis un repli. Même chemin pour les plans des films (`filmMoteur.ts`), le projet long et les références.
- « Booster ma phrase » : réécriture française de l'idée (rôle `boost`), sans lien avec le prompt H3.
- Les paliers Éco / Équilibré / Expert (`niveaux.ts`) ne servaient pas à la rédaction ; ses jetons n'étaient ni mesurés ni facturés.

## 2. Ce qui est construit

**Le réalisateur** (`realisateur.ts`), un appel, deux réparations au plus :

1. **Comprendre** : orthographe, québécois (char, pis, tuque, tire…), famille de la demande (pub, produit, film, vfx, cours, social, clip), tout ce que le client a nommé est gardé ; marques et personnages protégés remplacés par un équivalent générique (sabre laser → lame d'énergie ; « comme Starbucks » → café haut de gamme). **Aucune question** : les choix faits par défaut sont listés (`hypotheses`).
2. **Réaliser** : chaque plan est **un paragraphe de prose de réalisateur** (cadrage et objectif, action découpée dans le temps, un mouvement de caméra du vocabulaire H3, lumière motivée, matières, sons synchronisés), découpage multi-plans réglé par la durée (5 s : 1 plan ; 10 s : 2-3 ; 15 s : 3-4 ; ≥ 2,5 s par plan), règles propres à chaque famille (à la TIDE / SCMAPR : routage puis règles du scénario), moteur visé (FastH3 832×480 : compositions lisibles ; cinéma : détail).
3. **Compiler (le code, pas le LLM)** : dialecte H3 T2VA / I2VA (ligne d'instruction, champs, horodatages), personnages `[P1]` décrits **une seule fois en entier** puis toujours par le même groupe nominal (cohérence), répliques `[R1]` posées **mot pour mot** avec l'identifiant de locuteur du guide, dialecte image (plan clé Qwen) depuis la même fiche. Vérifications : durées, marques, texte à l'écran non demandé, français resté dans les champs, longueur.
4. **Montrer** : `compris` (ce que l'IA a compris, en français), `hypotheses`, `variantes` (trois autres directions), storyboard (cadrage et début de chaque plan) ; affichés dans Créer (panneau « Ce que l'IA a compris », variantes en un clic, prompt H3 visible sur demande, crédits de l'écriture).

**Facturation** : rôle `redaction` au palier **Expert** par défaut (`paliers.ts`), secours Équilibré ; dans `/creer` l'écriture passe par `executerSousReservation` (devis `realisation`, réservation, règlement, grand livre) ; ailleurs (films, projet long, références) chaque jeton va au grand livre. `NEXORA_REALISATEUR=off` rétablit l'ancien réécrivain, qui reste aussi le repli automatique.

## 3. Banc texte : 32 demandes à l'arrache, deux juges à l'aveugle

Demandes : `bench/demandesReecriture.ts` (6 pubs, 5 films, 10 effets spéciaux dont dragons, explosions, bataille spatiale, duels de sabres d'énergie, 4 produits, 3 cours, 3 réseaux sociaux, 1 clip ; fautes et québécois ; 3 répliques à dire mot pour mot ; une demande de texte à l'écran). Chaque demande garde une liste de ce qu'elle exige (jamais montrée aux LLM).

### 3.1 Coût, fiabilité, délai (moyennes par demande)

| Système | Valide au 1er coup | Jetons entrée / sortie | USD | Crédits exacts | Délai médian |
|---|---|---|---|---|---|
| Actuel, GLM-5.3 (production) | 30/32 | 4 336 / 2 583 | 0,01033 | 1,59 | 17,5 s |
| Actuel, Éco (DeepSeek V4.1 Flash) | 32/32 | 3 926 / 386 | 0,00016 | 0,02 | 7,3 s |
| Réalisateur v1 (champs), Éco | 23/32 | 2 733 / 1 027 | 0,00033 | 0,05 | 25,3 s |
| Réalisateur v1, Équilibré (Muse Spark 1.3) | 32/32 | 1 880 / 825 | 0,00029 | 0,05 | 10,5 s |
| Réalisateur v1, Expert (Gemini 4 Argon Flex) | 32/32 | 1 993 / 740 | 0,00569 | 0,88 | 15,0 s |
| **Réalisateur v2 (prose), Expert** | **32/32** | **2 140 / 672** | **0,00550** | **0,85** | **14,3 s** |
| Réalisateur v2, Équilibré | 32/32 | 2 026 / 885 | 0,00032 | 0,05 | 10,8 s |
| Réalisateur v2, Éco | 13/32 | 3 755 / 1 111 | 0,00036 | 0,06 | 16,7 s |

Aucun repli sur 256 réécritures. Le crédit facturé est arrondi au supérieur avec un minimum de 1 : **Éco, Équilibré et Expert coûtent tous 1 crédit au client** ; l'ancien chemin GLM en coûtait 2. Le réalisateur Expert est donc **moins cher que la production actuelle** (−47 % en dollars) et plus rapide.

### 3.2 Juge 1 : Gemini 4 Argon, raisonnement élevé, liste de 5 prompts mélangés, deux ordres

Échelle sévère (« les évaluations passées étaient de 1 à 3 points trop généreuses »). Note globale moyenne (IC 95 % par rééchantillonnage des demandes) :

| Ronde | Actuel GLM | Réal. v1 Expert | Réal. v2 Expert | v2 Équilibré | v2 Éco |
|---|---|---|---|---|---|
| ronde 1 (v1) | 6,11 [5,67 ; 6,58] | 7,34 [6,91 ; 7,73] | — | (v1 : 5,67) | (v1 : 5,47) |
| ronde 2 (v2) | 5,36 [5,00 ; 5,75] | 6,66 [6,33 ; 7,00] | **8,03 [7,72 ; 8,31]** | 5,67 | 5,84 |

Écart apparié v2 Expert − actuel : **+2,67 [+2,14 ; +3,19]**, 28 demandes gagnées, 2 perdues. Les modèles bon marché ne battent pas significativement l'actuel (+0,3 et +0,5, IC qui touchent 0).

La ronde 1 a servi de diagnostic : le juge reprochait au v1 un **style télégraphique** (listes de mots-clés recollées), des contradictions (« static shot » qui bouge, macro qui cadre deux personnes), des plans de 3 s surchargés, un accent québécois ajouté sans demande (mon propre exemple dans les consignes), le look anamorphique en 9:16, l'absence de musique dans une pub, des incohérences de saison (lucioles dans la neige) ou d'ordre (le cuisinier mange avant de servir), « canister » pour canette. Le v2 corrige chacun de ces points (prose, vérification silencieuse des contradictions, règles de durée, musique, traduction exacte).

### 3.3 Juge 2 : GPT-6.1 Sol (Codex, effort élevé), par paires, ordre tiré au hasard

Pour écarter la **préférence de Gemini pour un texte écrit par Gemini** : réalisateur v2 Expert contre l'actuel, 32 paires.

**Réalisateur 23 victoires, actuel 9** ; notes moyennes **7,09 contre 5,88 (+1,2)**. C'est l'écart que je retiens : celui d'Argon (+2,7) est probablement gonflé par l'auto-préférence. Défauts que Sol trouve encore au réalisateur : quelques plans trop chargés (cockpit, chat en skate), une découverte physiquement maladroite (film noir), un ajout de destruction non demandé (robot), une explication biologique moins juste (cellule).

## 4. Banc vidéo : le meilleur prompt donne-t-il la meilleure vidéo ?

(voir §4 rempli après les rendus)

## 5. Effets en images de synthèse : Relief + Blender

(voir §5 rempli après les rendus)
