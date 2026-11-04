# Feuille de route maître — Nexora Creative (3 novembre 2026)

Réponse à la question du fondateur : « as-tu creusé chaque variable pour en faire l'outil le plus efficace et le plus puissant du marché, tout en restant simple, avec un Mode Studio simple et très contrôlable ? ». **Réponse honnête : pas encore.** Ce document est l'audit complet, le plan unique et l'ordre de travail. Backlog : 57 issues GitLab `root/nexora-creative` #1 à #57 (clé `Bnn` = issue `#nn`), suivi dans **#58**. Source du backlog : `docs/backlog/feuille-de-route-maitre.json` (recréé par `scripts/creer-backlog-gitlab.mjs`, idempotent).

Légende des preuves : [CODE] lu dans le code, [TEST] test vert, [MESURÉ] mesure réelle, [ESTIMÉ] jugement non mesuré. Les notes des concurrents sont [ESTIMÉ] à partir de `recherche/07`, `12`, `16`, `17` (pages officielles lues le 02/11) et de la connaissance générale des produits ; aucune n'a été refaite aujourd'hui.

## 1. Audit

### 1.1 Notes (0 à 5) : nous aujourd'hui contre les leaders

Hf Higgsfield · Rw Runway · Kr Krea · CC CapCut · Pr Premiere/DaVinci · De Descript · Ca Canva · Me Meshy. « – » : hors du champ du produit.

| # | Variable | **Nous** | Hf | Rw | Kr | CC | Pr | De | Ca | Me |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Temps au premier résultat | **3** | 4 | 4 | 5 | 4 | 1 | 3 | 5 | 4 |
| 2 | Défauts et préréglages | **3** | 5 | 3 | 4 | 5 | 2 | 3 | 5 | 3 |
| 3 | Profondeur de contrôle (divulgation progressive) | **3** | 2 | 4 | 3 | 3 | 5 | 3 | 2 | 3 |
| 4 | Timeline : vitesse d'édition, raccourcis | **3** | 0 | 2 | 1 | 4 | 5 | 3 | 2 | – |
| 5 | Clic droit contextuel / bulle d'effet IA | **3** | 0 | 1 | 1 | 2 | 2 | 2 | 2 | – |
| 6 | Couches d'ajustement, images clés | **4** | 0 | 1 | 0 | 3 | 5 | 1 | 1 | – |
| 7 | Proxys, performance | **2** | – | 3 | – | 4 | 5 | 3 | 3 | – |
| 8 | Modèle d'annulation | **4** | 1 | 2 | 2 | 4 | 5 | 4 | 4 | 2 |
| 9 | Sauvegarde auto, versions | **2** | 3 | 4 | 3 | 4 | 4 | 4 | 5 | 3 |
| 10 | Collaboration, commentaires | **0** | 2 | 3 | 2 | 3 | 4 | 4 | 5 | 1 |
| 11 | IA partout (assistant, auto-montage) | **3** | 3 | 4 | 3 | 4 | 3 | 4 | 3 | 2 |
| 12 | Sous-titres automatiques | **3** | 2 | 3 | 1 | 5 | 4 | 5 | 3 | – |
| 13 | Voix off, doublage, lip-sync | **1** | 5 | 4 | 3 | 4 | 2 | 5 | 3 | – |
| 14 | Musique | **4** | 3 | 2 | 2 | 4 | 1 | 2 | 3 | – |
| 15 | Bruitage, design sonore, mixage | **2** | 3 | 3 | 2 | 4 | 4 | 3 | 2 | – |
| 16 | Agrandissement, restauration | **1** | 4 | 4 | 5 | 3 | 4 | 2 | 2 | – |
| 17 | Recadrage auto, B-roll | **1** | 3 | 3 | 3 | 5 | 3 | 4 | 4 | – |
| 18 | Édition de vidéo existante (v2v) | **0** | 4 | 5 | 4 | 3 | 3 | 2 | 1 | – |
| 19 | Contrôle qualité (juge, prises, cohérence) | **4** | 3 | 2 | 2 | 1 | 0 | 1 | 1 | 2 |
| 20 | Transparence des coûts (devis, jetons, crédits) | **4** | 2 | 3 | 3 | 2 | 5 | 3 | 3 | 3 |
| 21 | Vitesse (file, brouillons, ordonnancement GPU) | **2** | 4 | 4 | 5 | 4 | – | 3 | 4 | 4 |
| 22 | Fiabilité (reprise, idempotence) | **3** | 3 | 4 | 4 | 4 | 4 | 4 | 5 | 4 |
| 23 | Actifs : bibliothèque, kit de marque, projets | **1** | 3 | 3 | 3 | 3 | 4 | 3 | 5 | 2 |
| 24 | Sorties : formats, réseaux, lots, A/B | **3** | 3 | 3 | 3 | 4 | 5 | 4 | 5 | 4 |
| 25 | Mode Marketing et impression | **1** | 1 | 0 | 2 | 2 | 0 | 0 | 5 | 0 |
| 26 | 3D (Relief) | **3** | 1 | 1 | 2 | 0 | 2 | 0 | 1 | 5 |
| 27 | Long format (scénario → montage) | **2** | 2 | 2 | 1 | 1 | 5 | 3 | 0 | – |
| 28 | Accessibilité | **1** | 2 | 3 | 2 | 3 | 4 | 3 | 4 | 2 |
| 29 | Mobile | **2** | 4 | 3 | 3 | 5 | 1 | 2 | 5 | 2 |
| 30 | i18n fr-CA / en-CA | **3** | 2 | 3 | 2 | 5 | 5 | 3 | 5 | 3 |
| 31 | Onboarding | **2** | 4 | 4 | 4 | 4 | 2 | 4 | 5 | 4 |
| 32 | Observabilité, QA (e2e, dorés, bancs) | **3** | – | – | – | – | – | – | – | – |
| 33 | Sécurité, confidentialité | **4** | 3 | 4 | 3 | 2 | 4 | 3 | 4 | 3 |
| 34 | API, MCP, skills pour agents | **2** | 4 | 5 | 4 | 1 | 3 | 2 | 3 | 4 |
| 35 | Déploiement, exploitation Proxmox | **2** | – | – | – | – | – | – | – | – |

**En tête** : nous **2,4/5** de moyenne (35 lignes) ; Higgsfield ≈ 2,7 ; CapCut ≈ 3,3 (le plus complet en montage simple) ; le meilleur du marché ligne par ligne fait ≈ 4,8. **Nous menons** sur le contrôle qualité (juge visuel, 2 prises, contrôle automatique, personnages `@`), la transparence des coûts (devis par le code avant toute dépense, jetons facturés) et la combinaison unique génération + montage multipiste + 3D + impression sur des moteurs hébergés chez nous. **Nous sommes derniers** sur la collaboration, la v2v, la voix, l'agrandissement, le recadrage, les actifs et le Marketing dans l'interface.

### 1.2 Détail : état, écart, meilleur motif, plus petite tranche

| # | État aujourd'hui (preuve) | Écart | Meilleur motif du marché | Plus petite tranche → issue |
|---|---|---|---|---|
| 1 | Phrase → H3 en 82-92 s [MESURÉ] ; brouillon 28,7 s [MESURÉ] ; Producteur propose en ≈ 6 s | pas de parcours guidé, brouillon ≠ finale | Krea/Canva : résultat visible en < 10 s, raffiné ensuite | onboarding #53 ; brouillon fidèle #32 |
| 2 | 8 modèles prêts (Explorer), 16 caméras, 26 recettes de bulle [CODE] | pas de galerie de gabarits ni de styles de marque | Higgsfield : centaines de presets illustrés | gabarits Marketing #15 ; Flows #49 |
| 3 | Simple, Producteur, Studio séparés [CODE] | passer du simple au Studio perd le contexte | Premiere : propriétés à un clic ; Runway : Act/Edit sur la même vue | « Ouvrir dans le Studio » avec le projet (dans #10) ; Agent unifié #57 |
| 4 | FreeCut : ripple, lame, raccourcis, multipiste [CODE] | non mesuré sur gros projets | DaVinci : clavier complet, découpe en direct | e2e #9 ; banc perf #11 |
| 5 | **Bulle « Effet IA ici… » v0 livrée** [TEST, capture] | recette non persistée, LLM non mesuré, pas de raccourci | aucun concurrent n'a d'effet par phrase au point du clic : notre avance si on la finit | #1, #2, #3 |
| 6 | 52 effets WebGPU, couches d'ajustement, images clés, Lottie, RIFE [CODE] | pas de rampe de vitesse, pas de particules | Premiere : Lumetri + time remapping | #6, #7, #5 |
| 7 | aucun proxy automatique, aucune mesure | risque de lenteur 4K | DaVinci : proxys optimisés transparents | #11 |
| 8 | une demande = un pas d'annulation (`enUnePas`) [TEST] | – | Premiere : historique nommé | (fait) |
| 9 | projets Studio dans l'OPFS du navigateur [CODE] | perte au changement de poste, aucune version | Canva/Descript : sauvegarde continue, versions | #10 |
| 10 | rien | aucune revue client | Frame.io / Canva : commentaires horodatés, lien de revue | #12 |
| 11 | assistant Studio, Producteur, montage auto, silences, rythme [TEST] | non facturé au jeton côté Studio | Descript Underlord : agent sur tout le projet | #4, #57 |
| 12 | Whisper au mot, lignes de 42 car. [TEST] | aucun style animé | CapCut : 50 styles karaoké | #29 |
| 13 | « Faire parler » par dialogue H3 [CODE] ; Kokoro/Chatterbox sur pc5 hors UI | pas de TTS, doublage, lip-sync | Higgsfield Speak, Descript Overdub | #24, #25, #26 |
| 14 | MiniMax-Music3, mixage −14 LUFS [MESURÉ] | – | – | (fait) |
| 15 | son natif H3, ducking dans le rendu EditPlan | crête −0,9 dB, pas de bruitages | CapCut : bibliothèque SFX | #27, #28 |
| 16 | Anime4K navigateur seulement | pas d'agrandissement vidéo serveur | Krea/Topaz : ×2-×4 en un clic | #33 |
| 17 | rien | pas de 16:9 → 9:16 intelligent | CapCut/Opus Clip : recadrage suivi | #42, #21 |
| 18 | H3 ne fait pas de v2v ; LTX retiré (licence) | pas d'édition de vidéo existante | Runway Aleph, Krea Edit | #37 → #38, #39, #40, #41 |
| 19 | juge `qwen/qwen3.8-27b`, 2 prises, contrôle noir/figé/silence, personnages `@` sur 2 plans [MESURÉ] | continuité non prouvée sur 20+ plans | aucun concurrent ne juge chaque plan | #44, #34 |
| 20 | devis par le code, grand livre des jetons (prix = coût × 1,10 × 1,4025) [TEST] | Studio non facturé ; devis dispersés | Premiere : prix fixe lisible | #4, #36 |
| 21 | parc GB10 + 5090 routé par recette ; Turing pc5 non branché | pas de planificateur global ni d'attente estimée | Krea : temps réel ; Runway : file visible | #30 |
| 22 | reprise de film après `kill -9` [MESURÉ] | pas uniforme (3D, musique, Marketing), pas d'idempotence générale | – | #31 |
| 23 | liste de créations ; personnages `@` | pas de bibliothèque ni de kit de marque | Canva Brand Kit | #13, #48 |
| 24 | MP4, ProRes 422 HQ, ZIP FCP7 XML, publication par réseau [TEST] | pas de lots, variantes, A/B | Canva : redimensionner tout ; Higgsfield : variantes | #21, #22 |
| 25 | pipeline `marketing/nexora/imprimes/` (PDF fond perdu, traits, vernis) en ligne de commande [CODE] | rien dans l'interface | Canva Print | #13, #15, #16, #17, #18, #19, #20 |
| 26 | Image→3D et Texte→3D TRELLIS.2, GLB [MESURÉ] | pas d'usage hors du mode 3D | Meshy : retexture, rig, formats | #56 (après l'agent Relief) |
| 27 | squelette projet long (4 plans réels) | pas de Fountain, d'états, de lots | DaVinci : timelines longues ; Hf : pas de long | #43 |
| 28 | non audité | inconnu | Canva : AA, clavier | #52 |
| 29 | accueil 375 px sans débordement [TEST 31/10] | Producteur, Marketing, Studio non testés | CapCut mobile complet | #50 |
| 30 | fr-CA d'abord ; locales FreeCut sans accents | en-CA partielle | CapCut, Canva | #51 |
| 31 | aucun parcours | – | Canva : tâches guidées | #53 |
| 32 | ≈ 200 tests unitaires, bancs montage/agent/3D [TEST] | pas d'e2e Studio, pas de banc nocturne | – | #9, #34, #35 |
| 33 | auto-hébergé, licences en échec fermé, isolation par organisation [TEST] | routes Studio à auditer, CSP | – | #54 |
| 34 | MCP stdio (22 outils) | pas d'API publique ni de MCP distant | Runway/Krea API | #46, #47 |
| 35 | déploiement manuel, VM 202 de 4 Go | pas de CI de déploiement, pas de retour arrière | – | #55 |

### 1.3 Les dix plus gros écarts (impact × distance)

1. **Édition de vidéo existante** (v2v : retirer, remplacer, restyler) : 0/5 — #37, #38, #40.
2. **Voix, doublage, lip-sync** : 1/5 — #24, #25, #26.
3. **Mode Marketing absent de l'interface** alors que le moteur d'impression existe : 1/5 — #13, #15, #16.
4. **Actifs et kit de marque** : 1/5 — #13, #48.
5. **Collaboration et projets Studio persistés côté serveur** : 0-2/5 — #10, #12.
6. **Recadrage 9:16 et B-roll automatiques** : 1/5 — #42.
7. **Agrandissement / Master** : 1/5 — #33.
8. **Vitesse perçue** (planificateur GPU, brouillon fidèle, attente affichée) : 2/5 — #30, #32.
9. **API publique et MCP distant** : 2/5 — #46.
10. **Onboarding, mobile, accessibilité** : 1-2/5 — #53, #50, #52.

## 2. Vision et principes

**« Simple en surface, contrôle total dessous. »** Une phrase suffit pour un résultat ; chaque résultat s'ouvre à un clic dans un outil expert qui garde l'intention (la phrase, la recette, le devis) au lieu de la perdre.

Trois modes d'interaction, un seul projet :

| Mode | Pour qui | Surface | Dessous |
|---|---|---|---|
| **Simple** | tout le monde | Explorer, Créer, une phrase | Producteur et registre de capacités |
| **Studio** | monteurs | timeline FreeCut, bulle d'effet au clic droit, propriétés | opérations validées, recettes typées |
| **Agent** | ceux qui délèguent | le Producteur en conversation | outils typés, devis, juge ; ne dépense jamais sans validation |

Modes d'usage = **configurations** du même projet (`Mode` de `recherche/17` §B0 : schéma de brief, gabarits, outils permis, compétences, recettes, sorties, règle de devis) : **Marketing** (imprimés et identité), **Courts / Cours**, **Long métrage**, **Relief 3D**.

Principes (non négociables) :
1. **Le modèle propose, le code dispose** : toute sortie de LLM est une structure typée validée contre un catalogue fermé (EditPlan, EffectRecipe, SpecConception). Aucun code arbitraire.
2. **Devis par le code avant toute dépense**, réservé au grand livre, libéré en cas d'échec ; jetons facturés partout.
3. **Gratuit et instantané d'abord** : P0 navigateur → P1 serveur court → P2 GPU sur devis. Les recettes reconnues par le code ne coûtent aucun jeton.
4. **Non destructif** : effets sur couches d'ajustement ou pistes supérieures ; un résultat génératif est un nouveau média posé au-dessus ; une demande = un Ctrl+Z.
5. **Preuve avant affirmation** : test, mesure ou capture pour chaque fonction ; banc doré qui bloque les régressions.
6. **Licences en échec fermé** (aucun poids NC, AGPL, ni clause concurrente).
7. **fr-CA d'abord, en-CA complet.**

## 3. Vagues (1 à 2 semaines chacune)

Agents : **Opus** pour l'architecture et ce qui engage la qualité ou l'argent ; **Sonnet** pour l'implémentation ; **sous-agents** (`outils/sous-agents/`, modèles bon marché via la passerelle) pour les corvées (locales, imposition, skills, migration de libellés). Chaque vague finit par une MR fusionnée dans `developpement`, un déploiement VM 202 et une ligne dans `docs/ETAT.md`.

| Vague | Durée | Contenu (issues) | Test d'acceptation mesurable | Agents |
|---|---|---|---|---|
| **1 — Studio complet** | 2 sem. | v0 bulle (**livrée**), #1, #2, #3, #4, #5, #6, #7, #8, #9, #10, #54, #55 | « look film des années 80 » au clic droit → couche de 4 effets, Ctrl+Z la retire ; 30 phrases LLM ≥ 90 % valides ; projet repris sur un autre navigateur ; e2e vert en CI | Opus #10 #54 ; Sonnet le reste |
| **2 — Marketing et marque** | 2 sem. | #13 → #15 → #16, #17, #18, #19, #20, #21, #22, #14, #23 | kit saisi une fois → carte, flyer, accroche-porte, affiche en PDF fond perdu conformes au contrôle préliminaire en < 60 s ; les 4 formats sociaux en un clic | Opus #13 #15 ; Sonnet ; sous-agent #18 |
| **3 — Voix et son** | 1-2 sem. | #24, #28, #29, #27, #25, #26 | voix off fr-CA posée et sous-titrée au mot ; −14 LUFS ±0,5 et crête ≤ −1 dBTP sur 10 films ; un doublage en-CA ±5 % de durée par phrase | Sonnet ; Opus #26 |
| **4 — Vitesse, fiabilité, coût** | 2 sem. | #30, #31, #36, #32, #33, #34, #35, #11 | SIGKILL pendant 3 tâches → toutes reprises sans double débit ; devis = débit ±10 % ; attente estimée affichée ; banc doré nocturne en place | Opus #30 #31 #32 #36 |
| **5 — Édition de vidéo existante** | 2 sem. | #37 → #38, #39, #40, #41, #42 | « enlève le lampadaire » sur un plan réel noté ≥ 7/10 ; 16:9 → 9:16 suivi sur 3 films | Opus #38 #40 ; Sonnet |
| **6 — Long métrage, Cours, Agent** | 2 sem. | #43, #44, #45, #57, #56 | film de 5 min de bout en bout ; visage ≥ 0,7 sur 20 plans ; « campagne complète » en un devis ; leçon avec PresentQuiz ≥ 80 % | Opus #43 #44 #57 ; Sonnet #45 #56 |
| **7 — Écosystème et accès** | 2 sem. | #46, #47, #48, #49, #12, #50, #51, #52, #53 | API + MCP distant utilisés par Claude Code ; première vidéo < 3 min sur 5 personnes ; 0 violation axe sérieuse ; Studio en revue au téléphone | Opus #46 ; Sonnet ; sous-agents #47 #51 |

**Dépendances clés** : kit de marque #13 avant tout Marketing, sous-titres stylés et Agent unifié ; facturation Studio #4 avant le devis unifié #36, lui-même avant toute P2 (v2v, plaques, API) ; planificateur #30 et file #31 avant SAM 3 et le long métrage ; persistance serveur #10 avant commentaires #12 et bibliothèque #48.

**Risques** : licences des poids (lip-sync, v2v, SAM) → lecture avant intégration, colonne licence par brique ; GPU partagés avec les films → banc nocturne hors heures, priorités du planificateur ; WebGPU absent sur certains postes (constaté dans le navigateur intégré : effets appliqués mais invisibles) → #8 ; dérive de périmètre → une tranche par mode sur les mêmes briques ; aarch64 (GB10) pour SAM 3 et VACE → fiche de mesure avant promesse ; aperçu ≠ export → test de parité #8 ; coût LLM de la bulle → recettes maison d'abord, rôle `effets` en palier Éco.

## 4. Modèle de coût et de marge

| Ressource | Mesure | Prix client | Où |
|---|---|---|---|
| Jetons LLM | jetons d'entrée/sortie/raisonnement × prix fournisseur | coût × 1,10 × 1,4025 (marge + change + crédits), arrondi au crédit supérieur | `server/nexora/usage.ts` |
| GPU | secondes mesurées par recette et par moteur (GB10, 5090, Turing) | proposition 0,5 crédit/s, à valider ; coefficient par moteur (Turing ×0,3 du prix GB10 car plus lent) | `credits.ts`, devis unifié #36 |
| P0 navigateur | – | 0 | bulle, montage |
| P1 serveur court (CPU, Whisper, Demucs) | secondes CPU | forfait 1 crédit | #36 |

Ordres de grandeur mesurés : un film Éco écrit par l'agent 0,0006 $ (0,095 crédit) ; 5 s H3 rapide ≈ 43 crédits à 0,5 crédit/s ; bulle P0 = 0 ; une phrase de bulle au LLM ≈ 3 000 jetons d'entrée (catalogue compact) ≈ 0,0003 $ en Éco [ESTIMÉ, à mesurer #1]. Règle : marge brute ≥ 60 % par tâche GPU, ≥ 40 % sur les jetons, vérifiée par le tableau #35.

## 5. Définition de fini : « le meilleur outil du marché tout en restant simple »

Fini quand **toutes** ces mesures sont vraies en même temps, sur la VM de production, prouvées par le banc doré et un test utilisateur :
1. Première vidéo regardable en **< 3 min** (brouillon) pour 5 personnes sur 5 sans aide ; première carte d'affaires imprimable en **< 2 min**.
2. Note moyenne de l'audit **≥ 4,2/5**, aucune ligne sous 3, et **≥ 4 sur les lignes 5, 13, 18, 23, 25** (nos dix écarts).
3. Toute action génératrice affiche un devis exact (±10 %) avant dépense ; marge vérifiée.
4. Toute fonction du mode simple s'ouvre dans le Studio avec son intention conservée ; toute action IA s'annule d'un Ctrl+Z.
5. Qualité : juge ≥ 0,9 sur le banc doré, visage ≥ 0,7 sur 20 plans, ≥ 8/10 au regard du fondateur sur les films de démonstration.
6. Fiabilité : 0 tâche perdue sur 100 pannes provoquées ; 0 double débit.
7. Accès : 0 violation axe sérieuse, fr-CA et en-CA complets, revue au téléphone.
8. Ouvert aux agents : API + MCP distant + skills, utilisés par Claude Code et Codex.

## 6. Spécification : bulle d'effet au clic droit

Fondée sur `recherche/17` §A1 et §E. **v0 livrée** dans `mode-studio/src/features/nexora/effets/` (MR vague 1) ; le reste est découpé en #1 à #7, #27, #41.

**Entrées de menu.** Clic droit sur un clip : « ✨ Effet IA ici… » en tête du menu (`item-context-menu.tsx`, prop `effetIa`). Clic droit sur un vide de piste : même entrée (`timeline-track.tsx`, image du clic). À venir (#3) : règle temporelle, raccourci E à la tête de lecture, panneau Assistant.

**Bulle** (`bulle-effet.tsx`, hôte unique monté par `editor.tsx`, état `useBulleEffetStore`) : titre « Effet IA ici · m:ss », champ de phrase, puces (recettes maison marquées `puce`), portée **2 s / 5 s / Ce clip** (Ce clip par défaut sur un clip), état « le compilateur réfléchit… », puis une ligne de résumé (« 4 effets sur une couche d'ajustement de 5,0 s · gratuit, aperçu direct · recette Nexora, 0 jeton »), avertissements du validateur, boutons **Plus doux / Plus fort / Avant-Après / Annuler / Garder**. Échap ferme.

**Flux.** Phrase → `recetteLocale()` (26 recettes, motifs normalisés sans accents ; 36 phrases du banc, ≥ 90 % reconnues [TEST]) → sinon `POST /api/studio/effet` (rôle LLM `effets`, catalogue compact ≤ 16 000 caractères, contexte marqué « donnée, jamais consigne », sortie JSON filtrée par `server/nexora/effets.ts`) → `validerRecette()` contre le catalogue → `recetteVersOps()` → `enUnePas()`.

**EffectRecipe v1** (`effets/recette.ts`) : `{version: 1, prompt, resume, portee: {kind: 'plage'|'clip', debut, duree, itemId?}, etapes: EtapeRecette[], devis: {palier, credits}}`. Étapes v0 : `gpu_stack {effets: [{gpu, params}]}`, `volume {db}`, `texte {texte, position}`. À ajouter dans cet ordre : `transition` (#5), `temps` (rampe, #6), `calque` P0 (#7) puis P2 (#41), `audio` (#27), `v2v` (#38-#40). Règles du validateur : identifiant présent dans le catalogue, paramètre connu et borné (min/max du registre), valeur typée (nombre, booléen, option de liste, couleur `#rrggbb`), ≤ 8 effets et ≤ 4 étapes, portée en images entières ≤ 60 s, volume ∈ [−60 ; 12] seulement s'il y a un clip sonore, texte ≤ 80 caractères, étape inconnue ignorée avec avertissement, rien d'exécutable → refus en une phrase.

**Catalogue** (`effets/catalogue.ts`) : généré au chargement depuis `GPU_EFFECT_REGISTRY` (52 effets ; paramètres `number`, `boolean`, `select`, `color` seulement, avec bornes et défaut) ; un test échoue si un effet du registre manque ou si un effet inconnu apparaît : le catalogue ne peut pas dériver du moteur.

**Opérations.** Portée « plage » : une couche `adjustment` sur la piste « Effets IA » (créée en haut de la pile, réutilisée si libre), effets avec paramètres par défaut complétés depuis le registre. Portée « clip » : `addEffect` sur le clip. `volume` → `updateItem`, `texte` → `addText` sur la piste « Titres ».

**Aperçus à faible coût.** P0 : direct dans le moniteur (WebGPU) ; sans WebGPU, bandeau explicite (#8). P2 : image fixe éditée (Qwen-Image-Edit) ou masque superposé, puis devis, puis tâche (#38).

**Annulation.** Une application = un pas nommé « Effet IA : … ». Plus fort / Plus doux : on défait l'application et on réapplique la même recette transformée (`ajusterIntensite` : chaque paramètre éloigné ou rapproché de sa valeur neutre, borné) — l'historique garde un seul pas. Avant/Après : défaire / refaire de l'historique. Une nouvelle phrase remplace l'effet de la même bulle.

**Facturation.** P0 = 0 crédit ; recette maison = 0 jeton ; recette LLM : jetons au grand livre (#4, aujourd'hui **non facturés**, comme l'assistant) ; P1 forfait ; P2 devis réservé (#36).

**Persistance et préréglages** (#2) : `nexoraEffet` sur l'élément, « Modifier l'effet », « Enregistrer comme préréglage » ; recettes réussies versées à la mémoire AMD (`recherche/14`).

## 7. Spécification : mode Marketing (« Imprimés et identité »)

Fondée sur `recherche/17` §B1 et sur `marketing/nexora/imprimes/` (moteur HTML → Playwright → PDF fond perdu, traits de coupe, texte en contours par Ghostscript, calque de vernis, PNG).

1. **Kit de marque** (#13) : `KitMarque {couleurs: [{hex, cmjn?, nom}], polices: [OFL], logos: [{svg, fond: clair|sombre, zoneProtection}], ton: {adjectifs[3], interdits[]}, personnes: [{nom, titre, tel, courriel}], qr: {url, format}, style: {references[], prefixePrompt}}` par organisation ; extraction d'un site ou d'un logo en proposition (#14).
2. **Brief** : formulaire court (pièce, quantité, message, public) + phrase libre → compétence « accroches » (#19 : 5 variantes × 3 angles, mots comptés par le code).
3. **SpecConception** (#15) : JSON de calques (texte : contenu, police, taille, position, couleur, contour, alignement, interlignage ; actif : position, recadrage, rotation, masque ; forme ; z-order ; zones de sécurité ; invite de fond séparée). Le LLM choisit un gabarit et des valeurs ; le code garantit marges, zone de sécurité, contraste AA, débord.
4. **Gabarits v1** : carte d'affaires 3,5 × 2 po (recto/verso, vernis), dépliant lettre, accroche-porte 3,5 × 8,5 po (découpe de poignée en calque `decoupe`), affiche 18 × 24 po, posts 1:1 / 4:5 / 9:16, bannière ; logo (#20) et présentation (#23) ensuite.
5. **Fond** : Qwen-Image conditionné sur le rendu des calques de premier plan ; agrandissement pour l'affiche (≈ 224 dpi constatés sur 18 × 24 po → avertissement).
6. **Interface** (#16) : onglet Marketing → 3 propositions en < 60 s → éditeur léger Fabric.js sur la même spec → rendu de référence serveur → téléchargements.
7. **Sorties imprimeur** (#17, #18) : PDF fond perdu 0,125 po + traits, PDF/X par Ghostscript avec mention « épreuve conseillée » (orange #FF5A1F hors gamme CMJN, jamais de promesse de fidélité), contrôle préliminaire (dpi effectif, polices intégrées, noir riche, débord, QR décodé à la taille finale par zxing-js), imposition n-up, PNG pour le web.
8. **Vidéo de la campagne** : la même spec alimente les cartons du Producteur et les déclinaisons sociales (#21) ; l'Agent unifié (#57) produit « la campagne complète » sous un seul devis.

## 8. Ce que la vague 1 a livré (03/11)

Bulle « Effet IA ici… » v0 : clic droit clip et vide de piste, 26 recettes maison instantanées (0 jeton), rôle LLM `effets` et route `POST /api/studio/effet`, validateur et catalogue généré du registre, Plus fort / Plus doux, Avant/Après, un seul Ctrl+Z. Preuves : 15 tests Studio + 4 tests serveur verts, typecheck Studio vert ; vérifié dans le navigateur intégré (couche de 4 effets « Look film années 80 » créée sur la piste « Effets IA », retirée d'un Ctrl+Z ; « Glitch » posé sur le clip, visible dans le panneau Effets) — captures `marketing/creative/captures-v3/vague1-*.jpg`. **Limite constatée** : le navigateur intégré n'a pas d'adaptateur WebGPU, donc le rendu visuel des effets n'a pas été vu (#8) ; la voie LLM n'est testée qu'avec un faux modèle (#1).

## 9. Ce que la vague 2 a livré (03/11 nuit, tranche v1)

Kit de marque (#13), `SpecConception` v1 et 9 gabarits (#15), page Marketing (#16), contrôle préliminaire de base (#17, sans PDF/X), accroches filtrées (#19), pistes de logo en SVG (#20 sans vtracer). Restent : #14 (extraction depuis un site), #18 imposition, #21 déclinaisons sociales, #22 lots et A/B, #23 présentation. Voir `docs/ETAT.md`.

