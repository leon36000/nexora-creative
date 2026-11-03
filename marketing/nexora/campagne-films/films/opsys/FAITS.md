# OPSYS-AI : fiche des faits pour le film (02/11/2026)

Sources lues (rien n'est inventé ; chaque ligne porte un statut) :
- dépôt `leon36000/OPSYS-AI`, copie locale `~/Documents/Codex/2026-10-05/github-plugin-github-openai-curated-remote-4/work/OPSYS-AI-major-audit-ci-20261020-r2813`
  (`README.md`, `00-DIGEST.md`, `docs/produit/PERIMETRE-MODULES.md`, `CAHIER-AMBITIONS-TRANSMISSION-2026-10-05.md`,
  `INSTRUCTION-NATHAN-2026-10-02.md`, `VISION-ENTREPRISE-APPRENANTE.md`, `departments/*/department.yaml`) ;
- sessions Claude Code Desktop « Tu prends la responsabilité complète de la coordin… » (31/10 → 02/11, coordination en cours,
  boucle Ralph) et « Tu reprends le chantier OPSYS-AI après une passation de Codex » ;
- site : `NexoraSite/docs/recherche/07-opsys-ai-couverture.md` (audit du 26/10, classes de preuve A à E), `cms/content/claims.json`
  (CL-O01 à CL-O10, CL-D01 à CL-D10), `cms/content/pages/opsys-ai.fr-CA.md`.

Statuts : **RÉEL** = code présent, chemin réel et test non trivial (classe A de l'audit du site, « disponible » ou « qualifié
localement ») ; **EN PRÉPARATION** = pilote, partiel, simulé ou sans connecteur réel ; **VISION** = cible écrite par le fondateur,
sans code.

## 1. Ce qu'est OPSYS-AI
- Système d'entreprise IA pour PME, installé sur le VPS du client (ou poste/serveur) : **dix départements virtuels** pilotés par
  des agents, une console web et une application mobile à quatre profils (admin, vendeur, employé, client). RÉEL (dépôt).
- Le « M » : chaque département est un module **M1 à M10** (`departments/m01-…` à `m10-…`). RÉEL.
- Cœur : fork modifié d'OpenClaw (MIT) ; départements en Python, outils déterministes exposés en MCP ; approbations humaines
  N0–N5 ; registres chaînés par hachage ; bus d'événements ; SQLite par défaut, PostgreSQL en option. RÉEL.
- Règle d'or écrite : « le code calcule (prix, soldes, scores, cédules), le LLM orchestre et rédige. Aucune donnée inventée. »
  Les actions financières, fiscales, légales et sensibles exigent une approbation humaine. RÉEL (règle et mécanisme d'approbation).
- Ampleur : environ 105 000 lignes de code dans les départements et 188 000 lignes de tests (audit du site, 26/10) ; le registre
  MCP expose **710 outils** dont 254 ouverts aux appareils (révision 28, session de coordination, 02/11). Mesures d'auteurs,
  pas des preuves de production.
- Contexte de départ : PME de rénovation extérieure au Québec (gouttières, revêtement, soffite-fascia). RÉEL (CL-O10).
- État global déclaré : **produit en consolidation**, aucun déploiement de production complet (CL-O01). À afficher dans le film.

## 2. Les dix départements (nom du dépôt, ce que l'agent fait, statut)
| M | Département | Réel aujourd'hui | En préparation | Vision |
|---|---|---|---|---|
| M1 | Réception (Front Office) | qualification de demandes, transferts, plaintes, appels manqués saisis, résumé de réception (console) | messagerie vocale transcrite, envoi réel au client, SMS | réceptionniste vocale omnicanale en direct |
| M2 | CRM (Revenue CRM) | ingestion de leads, prochaine action suggérée, readiness pour l'estimation | client 360, relances | — |
| M3 | Estimation | estimation déterministe qui refuse de chiffrer sans information, Monte Carlo, **soumission PDF brouillon** filtrée des coûts internes, revue en 11 critères + approbation avant envoi | calibration estimé/réel | mesure à partir de photos, géospatial |
| M4 | Terrain (Field Ops) | intervention née du devis accepté, fin de chantier côté serveur | cédule par tournées, pointage, preuves photo, météo | GPS en direct, dispatch |
| M5 | Finance (FinanceCore) | **facture brouillon après travaux terminés**, comptes à recevoir et à payer, calculs en Decimal | cash libre, prévision 26 semaines, calendrier TPS/TVQ, dossier CFO et décision de capital (fixtures « camion 95 000 $ ») | comptabilité complète, paie, connecteurs bancaires |
| M6 | Matériel | besoins depuis le devis accepté, réservations, variance en quantités | bons de commande (approbation N3), réceptions | catalogue, API fournisseurs |
| M7 | Marketing | chantier terminé → propositions de contenus, consentement vérifié, export manuel ; inbox d'avis | demande d'avis, attribution lead → marge | publication sur réseaux, OAuth |
| M8 | Analytique | collecte par le bus, vue exécutive | mesures « non calculable » si donnée manquante, alertes | — |
| M9 | Stratégie | **briefing du matin**, lecture stratégique | suivi de décisions, état consolidé | conseil d'agents, scénarios |
| M10 | Mémoire | registres chaînés, paquet de contexte, recherche d'affaire | mémoire hybride (PostgreSQL), consolidation | rappel sémantique et graphe |

Chaîne réelle la plus forte (à raconter) : **devis accepté (M3) → intervention (M4) → besoins matériel (M6) → fin de chantier →
facture brouillon (M5) → contenus proposés (M7) → vue exécutive (M8) → briefing du matin (M9) → mémoire (M10)**, tout côté
serveur, en brouillons, avec validation humaine. Les envois réels au client n'existent pas encore.

## 3. L'ambition du fondateur (citée des documents, sans chiffre inventé)
- « Donner à une PME les ressources d'une grande entreprise : dix départements complets, plusieurs agents spécialisés, une vérité
  partagée, des opérations interconnectées et une autonomie gouvernée » (cahier d'ambition du 05/10).
- Le fondateur (02/10) veut « pouvoir communiquer avec les départements aussi par avatar 3D audio visuel style NVIDIA ACE ».
- Aucun chiffre de temps gagné n'est documenté : le film ne montre **aucun nombre d'heures économisées** ; le temps rendu se
  montre par l'heure de la journée et par la vie de la personne.

## 4. NVIDIA ACE dans OPSYS-AI
- Dans le dépôt : VISION. « ACE/Audio2Face/LiveKit/Pipecat/WebGL sont candidates » ; « Aucune dépendance NVIDIA, clé NGC ou
  licence de modèle n'est installée par cette décision » (`VISION-ENTREPRISE-APPRENANTE.md`). La console liste « Avatar 3D /
  Audio2Face : à qualifier par adaptateur » (`console/connecteurs_ui.py`). Aucun code d'avatar.
- Dans le film (fait ici, réel) : le visage de l'avatar est animé par **NVIDIA Audio2Face-3D v2.3.1 (identité « Claire »)**,
  modèle ouvert publié par NVIDIA sur Hugging Face (licence NVIDIA Open Model License), exécuté en ONNX (onnxruntime, processeur
  du GB10) à partir de la voix : 140 coefficients de peau + yeux par image, géométrie de 61 520 sommets. Rendu « Signal » écrit
  pour le film (`avatar_a2f.py`). Composants ACE **non** utilisés : Riva (voix et reconnaissance), NIM, Audio2Emotion, le SDK
  TensorRT, Animation Graph, Omniverse. La voix est synthétique (Kokoro-82M, Apache-2.0 ; voix française « siwis », accent de
  France, pas québécois) ; les réponses de l'avatar sont écrites pour le film, pas produites en direct par un agent OPSYS.
- Formulation exacte permise : « Visage animé par Audio2Face-3D, un modèle ouvert de NVIDIA ». À ne pas écrire : « avatar NVIDIA
  ACE », « propulsé par NVIDIA ACE », ni « l'avatar d'OPSYS-AI est disponible ». Le mot « nvidia » est interdit à l'écran par
  l'usine (marques tierces) : la mention reste dans le manifeste et le rapport ; au fondateur de trancher pour l'écran.

## 5. Voix, personnalité
- Ton des SOUL des départements : précis, sourcé, refuse d'inventer, demande la validation. L'avatar du film parle court, donne
  le fait, propose l'action et **demande l'accord** (fidèle aux approbations N4/N5).

## 6. Incohérences relevées entre le site et le dépôt (à corriger par le responsable du site)
1. Le site (CL-O03, page) promet des « spécialistes IA configurables » mais ne mentionne pas l'avatar 3D, alors que c'est une
   demande expresse du fondateur : si le film est publié, ajouter une affirmation « Avatar vocal 3D : vision, non livré ».
2. L'audit du site date du commit `54d89d3` (21/10) ; la ligne de développement a beaucoup bougé depuis (710 outils MCP,
   producteurs M1/M4/M7 pour M9, coût certifié). Les statuts M4/M5/M9 de la page sont à revalider (plusieurs « pilote » sont
   peut-être devenus « qualifié localement »), sans rien promouvoir sans preuve.
3. Licence contradictoire dans le dépôt (`LICENSE` Apache-2.0 contre ADR-0003 propriétaire) : à trancher avant tout discours
   « open source » sur la page.
4. « Mode souverain » : absent du code (audit du site) ; ne pas l'afficher.
