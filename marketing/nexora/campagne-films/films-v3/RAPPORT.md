# Films V5 : rapport (03/11/2026)

Trois films refaits de zéro dans la grammaire d'une publicité Apple : une idée par film, un moment humain, puis le produit réel
grand à l'écran avant 7 s, peu de mots, une seule ligne à retenir et un carton (marque dans `marque.json`).
Durées : Creative 56,3 s ; WorkStudio 46,5 s ; OPSYS-AI 54,6 s. Chaque film existe en 16:9 et en 9:16 natif (cadrages
verticaux propres, plaques H3 tournées en 9:16), en fr-CA. Une infographie par film en 1080×1350 et en 1080×1080.

## Audio
- Narration : **ElevenLabs v4 « Alexandre »** (choix du fondateur à l'écoute), une phrase par fichier, contrôle Whisper (EMR 0
  sauf homophones « Ça part » / « sa part » et « Opsis AI »). Débit mesuré 2,1 à 2,3 mots/s.
- Musique : **Lyria 3 Pro, provisoire** (pas encore de verdict), deux propositions par film, choix par la courbe d'énergie du
  scénario ; tempo mesuré et coupes aimantées sur la grille (écart moyen 0,10 à 0,13 s).
- Stems séparés (`audio/{voix,musique,sfx}-stem.wav`, `audio.json`). Changer de voix (par exemple Drama 3 au second tour)
  revient à lancer `outils/refaire_audio.sh <film> <moteur>` : les plaques et l'image ne sont pas refaites.
- Mixage : musique −10 dB sous la voix (écart mesuré voix/musique 10,6 à 14 dB), −14,1 à −14,6 LUFS, crête vraie −1,5 dBTP.

## Notes sévères (regard d'étranger, /10 ; le son n'a pas été écouté par un humain)
| Film | concept | produit | accroche | spectacle | texte/voix | rythme | son | finition | **total** |
|---|---|---|---|---|---|---|---|---|---|
| Creative « Une phrase » | 8 | 9 | 7 | 7,5 | 8 | 7,5 | 6,5 | 7,5 | **7,6** |
| WorkStudio « Rien ne part sans vous » | 8 | 6 | 7 | 6 | 8 | 6,5 | 6,5 | 7 | **6,9** |
| OPSYS-AI « Votre entreprise, au complet » | 7,5 | 6 | 7,5 | 7 | 7,5 | 7 | 6,5 | 7 | **7,0** |

## Temps d'écran du produit (16:9)
| Film | 1re apparition | captures réelles et sortie réelle | dessins du code | imprimés réels |
|---|---|---|---|---|
| Creative | 5,9 s | 34,0 s (session réelle du Producteur + le film qu'elle a tourné) | 0 | 4,5 s |
| WorkStudio | 6,7 s | 19,4 s (deux captures réelles de l'exécution du 02/11) | 4,7 s (recomposition de l'envoi, étiquetée) | 0 |
| OPSYS-AI | 6,2 s | 8,7 s (Console réelle, données fictives) | 20,0 s (tableau M1–M10) | 0 |

## Pourquoi pas 8 partout (à dire franchement)
- **Creative (7,6)** : interface sombre sur fond sombre (lisible, mais peu de contraste à petite taille) ; le film produit est en
  832×480 (qualité « rapide ») : agrandi en carte, il reste doux ; les imprimés sont ceux de Nexora, pas ceux de l'atelier ;
  musique non validée à l'oreille. Pour passer 8 : refaire la session en « Qualité cinéma » et demander la « Version verticale »
  au Producteur (vrai 9:16), et faire valider la musique.
- **WorkStudio (6,9)** : aucune nouvelle session (pas de connexion par mot de passe par l'agent) ; deux captures fixes de
  1186×906, la lumière du flux et l'envoi sont dessinés (dit à l'écran). Pour passer 8 : une vraie capture en mouvement
  (commande ci-dessous) et l'arrivée réelle du courriel dans Mailpit.
- **OPSYS-AI (7,0)** : film de vision ; la Console réelle est une page d'administration brute ; le tableau est un dessin.
  Pour passer 8 : une vraie vue de la console (ou l'application mobile) avec un style produit, et un plan d'avatar si le
  fondateur le veut.

## Option prête : capture réelle WorkStudio par le fondateur
Les scripts `films/workstudio/{connexion,capturer}.mjs` doivent être lancés depuis l'arbre principal (ils importent
`mode-studio/node_modules`, absent d'un arbre de travail temporaire), avec le relais TLS local **sur 127.0.0.1:8443** (la règle
d'hôte de Chromium vise 127.0.0.1:8443 ; un relais sur 127.0.0.2 ne sert à rien) vers 192.168.1.123:80, et le tunnel Mailpit
`ssh -N -L 18025:127.0.0.1:8025 nexora-workstudio` :
```
cd "/home/pc6/Desktop/Nexora Creative" && git fetch gitlab && git checkout gitlab/developpement -- marketing/nexora/campagne-films/films/workstudio
cd marketing/nexora/campagne-films/films/workstudio
node connexion.mjs ~/.nexora-temoins-ws.json          # le fondateur, lui-même (mot de passe du compte de test lu sur la VM)
node capturer.mjs ~/nexora-creative-data/work/films-v3/workstudio/cap-live ~/.nexora-temoins-ws.json <id-workflow-fr>
```
Puis remplacer `ui/ws-*.jpg` par les captures et relancer `composer.py workstudio 16x9|9x16` et `finir.py`.

## Chaîne (sources, sans binaire)
`films-v3/outils/` : `capturer-creative.mjs` (session réelle du Producteur, flux CDP), `plaques.py` (Qwen + H3, ou H3
texte→vidéo quand la GB10 est occupée), `voix.py`, `musique.py`, `mixer.py`, `composer.py` (cartes d'interface, tableau,
recomposition, typographie, carton, 9:16 natif), `finir.py` (master, web ≤ 25 Mo, planche, revue chiffrée), `infographie.py`,
`livrer.py`, `refaire_audio.sh`. Scénarios et découpages : `<film>/SCENARIO.md`, `<film>/film.json`.
