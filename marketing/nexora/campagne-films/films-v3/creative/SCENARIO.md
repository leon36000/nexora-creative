# Nexora Creative · « Une phrase » (V5, 56 s, 16:9 et 9:16, fr-CA)

**Idée unique** : vous écrivez une phrase ; le studio en fait un vrai film. Tout ce qu'on voit du produit est une vraie
session du Producteur, enregistrée le 03/11 sur la VM 202 (« Une pub de 15 secondes pour mon atelier de vélos à Québec… »),
et le film montré au milieu est celui que cette session a réellement tourné (« L'Aube à Vélo — Québec », 3 plans H3, 20 s).

**Structure de révélation** : moment humain (une mécanicienne, son atelier, une idée) → question implicite (« pas d'équipe de
tournage ») → à 6 s, la vraie interface, grande, où la phrase se tape → le plan, le prix d'abord, les deux prises jugées →
**héros à 26 s : son film, plein cadre en carte, sur la levée musicale** → contrôle du montage → l'étendue (imprimés réels) →
retour humain (elle le montre à un client) → une seule ligne : « Écrivez-le. On le filme. » → carton.

## Découpage seconde par seconde (temps auteur ; les coupes sont aimantées sur la grille mesurée de la musique)

| t (s) | Plan | Image | Son |
|---|---|---|---|
| 0,0–3,4 | p01 | Plaque héros h3-max : atelier de briques à l'aube, elle s'arrête, regarde la rue ; poussée lente ; ouverture au noir | air, roue qui tourne · **n1** |
| 3,4–6,0 | p02 | Ses mains sur le portable (écran caché) | frappe douce · **n2** |
| 6,0–12,4 | p03 | **Produit à l'écran** : flux réel de la frappe dans le Producteur, carte arrondie, poussée vers la zone de saisie ; surtitre « Captures réelles du studio » | **n3** puis silence de frappe, clic à « Envoyer » |
| 12,4–18,0 | p04 | Le plan proposé (« L'Aube à Vélo — Québec », 3 plans, cartons, musique), poussée | **n4** |
| 18,0–21,2 | p05 | Gros plan devis : « ≈ 90 crédits », « 2 prises par plan », « Valider et lancer » | clic |
| 21,2–26,2 | p06 | Suite de captures du suivi : en file → au tournage → tourné, « ✦ Juge : B montre mieux la main… », « Prêt » | **n5** |
| 26,2–36,4 | p07 | **Héros** : le film réellement produit (atelier, cycliste, sourire), carte large ; surtitre « Le film qu'il a tourné » | coup sourd, levée musicale |
| 36,4–40,0 | p08 | Fenêtre « Plans et montage » réelle (ordre des plans, coupe franche / fondu, bande originale, export) | musique |
| 40,0–44,6 | p09–p11 | Imprimés conçus avec nos outils, sur table claire : carte, affiche « Peignez avec la lumière », accroche-porte | **n6** sur les temps |
| 44,6–48,6 | p12 | Plaque : elle tourne l'écran vers un client, sourires | musique seule |
| 48,6–52,2 | p13 | Ligne : « Écrivez-le. *On le filme.* » (révélation mot à mot, accent orange) | coup sourd doux |
| 52,2–56,4 | p14 | Carton : N E X O R A / Creative / « Une phrase suffit. » | accord tenu, fin |

## Narration (fr-CA, calme, intime ; 6 phrases, 41 mots, ≈ 2,2–2,5 mots/s, pauses réelles)
1. « Vous avez une idée. »
2. « Pas d'équipe de tournage. »
3. « Écrivez-la. »
4. « Le studio fait le plan… et vous montre le prix d'abord. »
5. « Il tourne deux prises, garde la meilleure, et monte sur la musique. »
6. « Le film. L'affiche. La carte. »

## À l'écran
- La ligne à retenir : **« Écrivez-le. On le filme. »** (écho du titre de l'application : « Écris-le. Nexora le filme. »).
- Trois surtitres d'honnêteté seulement : « Captures réelles du studio », « Le film qu'il a tourné », « Imprimés conçus avec nos outils ».

## Matière
- Captures (Playwright 1920×1080 à 2×, `outils/capturer-creative.mjs`) : flux CDP de la frappe (1 032 images), plan proposé,
  devis, 9 captures du suivi, « Prêt », fenêtre de montage, Mode Studio (non retenu : projet vide, rien à montrer).
- Sortie réelle : `/api/media/63`, 832×480, 20 s (plans retenus 3,4–6,0 / 7,0–11,6 / 13,8–16,9).
- Imprimés : `marketing/nexora/imprimes/final/` (carte recto, affiche Creative 18×24, accroche-porte recto) ; la carte verso
  (adresse et domaine) est écartée.
- Plaques : `atelier` (h3-max), `mains`, `client` (h3-fast, première image Qwen exacte), en 16:9 et en 9:16 natif.
- Écarté : le mode 3D « Relief » (aucun objet 3D sur la VM 202 ; ne rien montrer qui n'a pas été produit).

## Musique et bruitages
Lyria 3 Pro, piste séparée : presque silence 0–6 s, pulsation douce, **levée à 26 s** (révélation du film), allègement, accord
final. Tempo mesuré, coupes aimantées sur les temps. Bruitages rares : souffle d'ouverture, deux clics d'interface, deux coups sourds.
Voix sous laquelle la musique baisse de 10 dB ; −14 LUFS, crête vraie ≤ −1,5 dBTP.

## Auto-contrôle sévère (avant tournage)
- Clair en 5 s ? Presque : une femme, un atelier, « Vous avez une idée. Pas d'équipe de tournage. » ; le produit arrive à 6 s.
- Produit à l'écran avant 10 s ? Oui (6,0 s), grand, réel.
- Une seule idée ? Oui : une phrase devient un film. Les imprimés élargissent sans changer d'idée (4,6 s seulement).
- Ligne retenue ? « Écrivez-le. On le filme. »
- Risques : le film produit est en 832×480 (montré en carte, pas plein écran) ; interface sombre sur fond sombre (liseré + ombre).
