# Nexora Creative — Architecture cible (conditionnelle)

Date : 30 octobre 2026. Statut : **proposition conditionnelle**, prête à passer en lots de développement une fois les 4 conditions du §9 levées.
Détails et preuves : `recherche/01` à `recherche/05` (3 100 lignes). Ce document en est la synthèse et la décision.

## 0. Ce qui est établi, et à quel niveau de preuve

| Niveau | Contenu |
|---|---|
| **Vérifié par moi** | Texte intégral de la licence MiniMax H3 (fichier `LICENSE` sur Hugging Face, lu en entier) ; existence des poids FastH3 (nombreux dépôts à jour au 29 oct.) ; état de Nexora (brief existant, grand livre, file PostgreSQL, Privacy Router, catalogue DeepInfra sans modèle de génération) ; matériel de cette machine (DGX Spark GB10, 121 Go, 166 Go libres). |
| **Rapporté par 5 sous-agents, lecture de code et de docs, non recontrôlé par moi** | Licences des autres projets, comparaisons de studios et de moteurs, chiffres de performance, sécurité de ComfyUI. Chaque rapport étiquette [DOC] / [CODE] / [MESURÉ publié] / [ESTIMÉ]. |
| **Testé / exécuté** | **Rien.** Aucun code n'a été installé ni lancé, aucun poids téléchargé, aucun prototype construit. Les chiffres de vitesse sont des mesures de tiers non reproduites. |

Limite de la collecte : les crédits Exa et Firecrawl se sont épuisés en cours de route ; plusieurs pages ont été lues via des résumés. À recontrôler à la source avant tout engagement financier.

## 1. Décision sur la base logicielle

> **Révision du 30/10/2026 (soir), après les URL fournies par le fondateur** (`recherche/06`) : la décision est désormais **fork d'OpenField (MIT) comme base, enrichie de composants d'autres projets**, sur le même modèle que WorkStudio (fork de Sim). L'analyse ci-dessous, faite sans OpenField, reste valable pour les autres candidats ; elle concluait à l'approche (b) faute de base solide. OpenField change la donne parce qu'il est en TypeScript/React 19 comme Nexora, tourne dans le navigateur et compile déjà les graphes ComfyUI côté serveur. Il faut tout de même lui ajouter le multi-client (qu'aucun candidat n'a) et remplacer LTX-2.5, dont la licence interdit les produits concurrents de Lightricks.
>
> | Rôle | Projet | Licence | Ce qu'on prend |
> |---|---|---|---|
> | **Base forkée** | OpenField | MIT | Interface navigateur, catalogue d'applications, constructeurs de graphes (dont H3), Director, Scene, Cast, Stage, MCP, HDR, mesures de vitesse |
> | Montage | FreeCut (fork) + Mediabunny | MIT / MPL-2.0 | Timeline multipiste, rendu serveur |
> | Règles de cinéma | Director's Console, Comfield | MIT | Vocabulaire caméra/objectif/lumière, 27 mouvements |
> | Modèle de données | BeatDesign | Apache-2.0 | Idées de schéma, réécrites en PostgreSQL |
> | Idées seulement | AI Movie Studio 2 | **AGPL-3.0** | Règle des 180°, Long Take, import Fountain/FDX, export XML (réécrits en salle blanche) |
> | Nexora (existant) | Portail, grand livre, Privacy Router, file PostgreSQL | — | Comptes, crédits, confidentialité, tâches |
>
> Intégration : comme WorkStudio, Nexora Creative est une application web à part entière, ouverte depuis le panneau « Mes outils » par connexion unique, qui appelle les services Nexora (crédits, espace, confidentialité). Le fork garde `UPSTREAM.md`, `THIRD_PARTY_NOTICES.md` et des scripts de contrôle de licence et de marque.

Trois approches comparées avant la révision (détail : `recherche/01`, `recherche/02`).

| Critère | (a) Fork BeatDesign / studio existant | (b) **Interface Nexora (Next.js) + composants sélectionnés** | (c) Fork d'un studio plus mature |
|---|---|---|---|
| Multi-client, comptes, crédits | **Absent partout** : tous les studios de type Higgsfield sont mono-utilisateur (BeatDesign l'écrit : « no account boundary ») ; réécriture du stockage et de l'authentification | Natif : portail, grand livre, entitlements existent | Idem (a). InvokeAI (Apache-2.0) a des comptes en option mais c'est un studio d'images |
| Licence | Variable ; ComfyUI et son frontend sont GPL-3.0 (copyleft contaminant), Velorn GPL + CLA, ComfyTV ambigu, Open-Higgsfield sans fichier LICENSE | Contrôlée : MIT / Apache / MPL seulement | Dépend du candidat |
| Cohérence « un seul logiciel » | Un second serveur et une seconde interface à fusionner dans le portail | Une seule application | Idem (a) |
| Maturité des candidats | Les studios « Higgsfield open source » ont de 0 à quelques milliers d'étoiles et quelques semaines d'existence | On reprend des **idées et modules** (modèle de données BeatDesign Apache-2.0, règles de cinéma de Director's Console MIT, 27 mouvements de caméra de Comfield MIT) sans hériter de leurs dettes | — |

**Décision : approche (b).** Aucun studio n'est forké comme base. Raison décisive : la multi-location et les crédits sont notre cœur, et aucun candidat ne les fournit ; les adapter coûterait plus que de les écrire dans notre pile. BeatDesign reste une **source de modèle de données** (Apache-2.0, à réécrire en PostgreSQL avec `tenant_id`), pas une base.

**Par rapport à votre hypothèse initiale :** OpenField est retenu comme base (révision ci-dessus). BeatDesign reste une source de modèle de données ; Backlot, FreeField, Aftertake, SwarmUI et InvokeAI ne sont pas retenus comme composants du produit ; FreeCut (fork MIT) est retenu côté montage (voir §3). AI Movie Studio 2 est AGPL-3.0 : idées seulement.

## 2. Architecture cible

```
Navigateur : Nexora Creative (fork OpenField, Vite + React 19), ouvert depuis « Mes outils » par connexion unique
   │  intention → plan guidé → résultat ; mode expert
   ▼
Serveur Nexora Creative (fork du serveur Fastify d'OpenField : constructeurs de graphes = compilateur de recettes)
   ▼
Plan de contrôle Nexora (web + worker existants)
   ├─ Compte / organisation / droits ......... Nexora Portal (existant)
   ├─ Crédits : reserve → settle/release ..... grand livre (existant)
   ├─ Espace : recordStorageUsage(…,"creative") entitlements (existant)
   ├─ Confidentialité ........................ Privacy Router (existant, à étendre aux pièces jointes média)
   ├─ Registre de capacités .................. NOUVEAU (manifestes + Zod) — §4
   ├─ AI Director ............................ NOUVEAU — §5
   ├─ Projets / plans / prises ............... NOUVEAU (PostgreSQL) — §6
   └─ File de tâches GPU ..................... extension de la file PostgreSQL SKIP LOCKED (existante)
   │         bail + heartbeat + jeton de fencing + idempotence + annulation
   ▼
Agent GPU (un par machine, aucun accès entrant)
   │  réclame un job, lance un moteur isolé, téléverse les sorties avec des identifiants limités au job
   ▼
Moteurs (conteneurs durcis, sans réseau sortant, poids en lecture seule, un job par GPU)
   FastVideo (H3 / FastH3, Wan, Kandinsky) · ComfyUI interne (recettes compilées) · LightX2V / SGLang-Diffusion après spikes
   ▼
Stockage objet S3-compatible (SeaweedFS ou Garage à tester ; MinIO écarté : archivé) → URL pré-signées courtes
```

Principes non négociables (confirmés par la lecture des rapports) :
1. **ComfyUI n'est jamais exposé.** L'API publique n'accepte qu'un `recipe_id` + paramètres validés ; un compilateur de recettes signées produit le graphe ; nœuds en liste blanche, sans ComfyUI-Manager, sans réseau sortant, safetensors uniquement. Un rapport cite des nœuds personnalisés ayant compromis plus de 1 000 instances en 2026 (source secondaire, à recontrôler).
2. **La file PostgreSQL de Nexora est la source de vérité.** Aucun moteur étudié (FastVideo, LightX2V, SGLang, vLLM-Omni, ComfyUI) ne conserve ses jobs après un redémarrage.
3. **Crédits en trois temps** avec les primitives du grand livre existant : `reserve` à l'acceptation, `settleReservation` au succès, `releaseReservation` à l'échec/annulation. Coût imputé selon le profil, pas selon la machine ; les temps de chargement de modèle sont à la charge de la plateforme.
4. **Pas d'orchestrateur de plus** pour 3 machines (Temporal à reconsidérer si un job dépasse ~3 étapes durables ; Ray, Celery, BullMQ, Kubernetes écartés).
5. **Produit éteint par défaut** : interrupteur `NEXORA_PRODUCT_CREATIVE` (patron de `NEXORA_PRODUCT_CODE`) ; la fiche reste « Plus tard » tant que rien n'est livré et prouvé.

## 3. Composants : retenus, adaptés, séparés, écartés

| Fonction | Retenu | Statut | Licence | Remarque |
|---|---|---|---|---|
| Inférence H3 / FastH3 / Wan | **FastVideo** | Séparé (moteur) | Apache-2.0 (à confirmer dans le dépôt) | Seul moteur documenté pour sm_121 (GB10) |
| Graphes de workflows | **ComfyUI** | Séparé, interne, caché | GPL-3.0 | Utilisé comme programme externe via API ; **ne jamais importer son code frontend** dans le portail |
| Éditeur multipiste | **FreeCut (fork)** | Adapté, dans le portail | MIT | Un seul mainteneur ; son générateur de musique (MusicGen, CC-BY-NC) à **désactiver** ; PoC obligatoire |
| Couche média navigateur/serveur | **Mediabunny** (+ `@mediabunny/server`) | Intégré | MPL-2.0 | ProRes en export |
| Masters pro | **FFmpeg build LGPL** (worker) | Séparé | LGPL | `prores_ks`, `dnxhd` vus dans les sources ; HDR/DNxHR à construire |
| Format d'échange | **OpenTimelineIO** | Export seulement | Apache-2.0 | Ne porte aucun effet |
| Cohérence / réalisation | Idées de **ViMax**, **DramaAgent** (reprise par fichier, empreinte de requête, réparation ciblée) | À réécrire | À vérifier | Les autres « agents réalisateurs » sont des démos de recherche |
| Cinéma (caméra/objectif/lumière) | Règles Director's Console (MIT), 27 mouvements Comfield (MIT) | Porté en données | MIT | Sept dialectes de traduction par modèle (rapport 05 §11) |
| Studio d'images alternatif | InvokeAI | **À évaluer plus tard** | Apache-2.0 | Moteur image possible, pas la base |
| Multi-GPU | SwarmUI | **Non retenu** | — | Notre agent + file font ce travail avec nos crédits |

**Écartés, avec raison :**
- Remotion (payant au-delà de 3 personnes ; éditeur intégré = offre « Automators » ; FFmpeg GPL ; pas de HDR), OpenVideo (idem), Twick (SaaS interdit sans accord), Shotstack Studio SDK (clause de non-concurrence), Etro (GPL-3.0), Concat (AGPL), Rendley et Diffusion Studio Core (propriétaires/filigrane).
- Open-Higgsfield-AI / Open-Generative-AI (aucun fichier LICENSE ou couplage MuAPI avec clés en localStorage), ComfyTV (licence contradictoire MIT/GPL), Velorn (GPL + CLA), Backlot / FreeField / Comfield et similaires (jours d'existence).
- MinIO (archivé), ComfyUI-Manager, gVisor/Kata sur GPU (non documentés pour RTX 50 / GB10).
- Raffineur LTX-2.5 dans le pipeline de production (voir §7 risque L3).

## 4. Registre universel de capacités

Spécification complète et code Zod/TypeScript : `recherche/05-director-et-registre-capacites.md` §5 (**non compilé** ; doit passer `tsc --strict` et des tests écrits d'abord). Idée centrale : un **`CapabilityManifest`** par modèle ou recette décrit tâches (t2v, i2v, v2v, motion-transfer, replace…), entrées typées, contraintes (grille 124+17n images, résolutions, durées, nombre de références), paramètres simples vs experts, profils Rapide / Équilibré / Qualité, formule de prix (modèle ComfyUI `PriceBadge`), **licence et droits** (territoires, commercial, entraînement interdit, affichage obligatoire), exigences matérielles, garde-fous, test de santé.

- L'UI se génère depuis le manifeste ; ajouter un modèle = ajouter un fichier de données + une recette.
- Le planificateur applique **d'abord les filtres durs** (licence/territoire du compte, confidentialité, matériel, crédits), **puis** score qualité/coût. Licence « inconnue » = non commercial par défaut.
- Un manifeste H3 existe avec un champ `territory.excluded = [US, EU, GB, KR]` ; voir §7.

## 5. Nexora AI Director

Algorithme détaillé : rapport 05 §9. Résumé :
1. Intention → brief → plan de plans (shots) avec références (personnages, produits, lieux), caméra, effets ; l'utilisateur valide un **devis en crédits** avant génération.
2. Sélection du moteur par le planificateur (§4), 2 candidats par plan (le papier ViMax mesure 2 comme optimum ; 3-4 coûtent plus et dégradent la cohérence).
3. Évaluation dans cet ordre : contrôles déterministes → identité (ArcFace/DINO) → juge VLM → humain. Les juges VLM généralistes sont peu fiables sur les artefacts.
4. **Reprise d'un plan** : chaque plan est un emplacement dont les prises sont adressées par empreinte SHA-256 de la recette ; modifier un plan invalide seulement ses dépendants (« périmé »), avec devis avant régénération.

## 6. Modèle de projet (reprise sans perte)

Format natif JSON versionné : **projet → plans (slots) → prises (takes)**, où une prise = fichier + recette + empreinte + version du moteur. Le montage référence des plans, pas des fichiers : régénérer un plan ne casse ni effets ni keyframes (idée issue d'Aftertake/FreeCut). Persistance PostgreSQL (`tenant_id` partout, migration numérotée après la 0029) ; objets en S3 avec quota via `recordStorageUsage(orgId, "creative", delta)` **avant** écriture. OTIO en export.

## 7. Risques de licence et de maintenance

Licence H3 relue par moi en entier ; les clauses ci-dessous sont mes propres lectures du texte.

| # | Risque | Gravité | Traitement proposé |
|---|---|---|---|
| L1 | **Territoire H3** (I.5, V.4, AUP 1) : États-Unis, UE, Royaume-Uni, Corée exclus, **y compris pour utiliser ou afficher les sorties**. Le Canada est inclus. Un client américain ou européen ne peut pas recevoir de vidéos H3 locales. | **Critique** | Territoire attribué à chaque compte ; hors territoire → routage vers Wan 2.2 / Kandinsky / Cosmos3 ; ou demander à MiniMax la licence séparée prévue (II, formulaire public) ; ou API MiniMax (conditions non lues). Avis juridique sur le client canadien qui publie ensuite aux États-Unis. |
| L2 | **Obligations d'exploitation H3** : afficher « MiniMax H3 » dans l'interface (IV.2, **obligatoire**), lier chaque utilisateur à des conditions au moins aussi strictes que la section V et l'AUP (V.2), garde-fous testés et mécanisme de signalement (V.5), indemnisation de MiniMax (VI.3), droit et tribunaux de Hong Kong (IX), seuil de 20 M$ de revenus annuels (IV.1), interdiction d'utiliser les sorties pour améliorer un autre modèle (V.3). L'AUP peut changer sans préavis. | Élevée | Conditions d'utilisation de Nexora Creative, jeu de garde-fous, versionnement de l'AUP, avis juridique. |
| L3 | **Dérivés = même licence** : FastH3 et les LoRA sont des « Model Derivatives » (I.11) ; une étiquette Apache sur un dérivé communautaire ne change rien. | Élevée | Tout dérivé H3 traité comme H3. |
| L3b | **LTX-2.x** (relu par moi dans `LICENSE-2_x`) : licence payante dès 10 M$ de revenus (§2.1) et **interdiction d'usage dans un produit qui concurrence directement Lightricks** (annexe A, point 20). C'est le moteur par défaut d'OpenField. | **Critique pour le fork** | Retirer ou remplacer tous les graphes LTX du fork ; pas de LTX en production sans licence écrite de Lightricks. |
| L3c | FLUX.2 dev et 4x-UltraSharp (optionnels dans OpenField) : non commerciaux | Élevée | Retirés du fork. |
| L4 | Visage / personnage : AUP 13 (usurpation) et 12 (contenu public non signalé comme généré) | Élevée | Consentement vérifié pour les références de personnes ; marquage « généré par IA » (la licence l'encourage). |
| L5 | Kandinsky 6.0 (MIT) : revue de provenance/sanctions à faire | Moyenne | Avis juridique avant usage commercial. |
| M1 | FreeCut : un seul mainteneur (~98 % des commits) | Moyenne | Fork interne, limiter la surface adoptée, PoC. |
| M2 | Moteurs jeunes, API instables | Moyenne | Adaptateur de moteur derrière un contrat fixe. |
| M3 | Dérive du catalogue : modèles qui changent de licence | Moyenne | Manifeste versionné, licence dans la donnée, alerte à la mise à jour. |

Wan 2.2 (Apache-2.0) et Cosmos3 (OpenMDW) sont les replis les plus propres. Wan 2.5 à 3.0 sont en API seulement.

## 8. Matériel : ce que disent les chiffres publiés (aucun mesuré par nous)

- **RTX 5090** : 5 s, 1344×768, audio : ~41,5 s à chaud (LoRA 4 étapes), 51–60 s (FastH3 V2, 8 étapes), ~166 s (H3 de base, 20 étapes) — mesures de tiers non reproduites.
- **DGX Spark GB10** : environ 2,4 à 5,5 fois plus lent que la 5090 ; ~141 s contre ~15 s sur une charge FastH3 V2 NVFP4 480p dans le seul comparatif direct. Machine de **capacité** (batch, plusieurs modèles résidents), pas d'interactivité. Les noyaux NVFP4 de LightX2V ciblent sm_120a : fonctionnement sur GB10 à tester.
- **RTX 5080 16 Go** : aucune mesure H3 publiée ; limite.
- Contre-exemples à ne pas oublier : 4 étapes pas toujours plus rapide ni meilleur ; VSA n'aide pas à 480p/5 s ; le cache de blocs coûte de la qualité.
- Poids H3 BF16 ≈ 142 Go par point de contrôle ; versions élaguées/quantifiées nécessaires (FP8, NVFP4, INT8, GGUF).

Profils (à calibrer par spike, jamais en dur) : **Rapide** = FastH3 4–8 étapes quantifié ; **Équilibré** = FastH3 V2 8 étapes ; **Qualité maximale** = H3 de base, plus d'étapes, sur 5090/GB10 ; sélection automatique selon tâche, matériel disponible, coût et territoire du compte.

## 9. Conditions pour passer en développement

1. **Décision juridique sur L1/L2** (stratégie de territoire H3). Sans elle, H3 ne peut servir que des comptes canadiens/hors-quatre-territoires, ce qui est faisable mais à coder dès le lot 2.
2. **Accord pour le prototype** (téléchargement de poids et installation isolée, §10).
3. ~~Création d'un projet GitLab~~ : fait par le fondateur le 30/10/2026 (`root/nexora-creative` sur pc4).
4. **Relecture humaine** des licences des autres composants retenus (FreeCut, Mediabunny, FastVideo, Wan, Kandinsky).

## 10. Prototype isolé (non commencé)

Dans `Nexora Creative/prototype/`, sans toucher aux installations de production de Nexora. Proposition de séquence minimale :
- P1 (GB10, cette machine) : FastVideo + un FastH3 quantifié, une génération T2V courte, chronométrée froid/chaud, pic mémoire noté.
- P2 : même chose sur une recette Wan 2.2 pour prouver « jamais exclusif ».
- P3 : modification d'un plan (retake) et reprise du projet depuis son JSON, sans GPU.
- P4 : tests de panne du contrat job/agent (SIGKILL, coupure base) sur une base PostgreSQL d'essai.

Points à savoir : cette machine héberge la démo du site et d'autres sessions ; le brief Nexora existant dit « jamais de modèle local » pour le travail de la session principale. Je ne lance donc rien de GPU-lourd, ni ne télécharge de poids, sans votre accord explicite (je donnerai noms, sources et tailles exactes avant).

## 11. Ordre de développement par lots vérifiables

Chaque lot : tests écrits d'abord et vus échouer ; fusion ; résumé en 3 lignes ; produit toujours éteint.

| Lot | Contenu | Preuve de fin |
|---|---|---|
| 0 | Avis juridiques, projet GitLab, spikes S1–S10 (rapport 04 §9) | Rapport de spikes signé ; décisions L1–L5 |
| 0b | Import du fork OpenField dans `root/nexora-creative` (`UPSTREAM.md`, notices, retrait FLUX.2 dev / UltraSharp, graphes LTX isolés et désactivés), contrôle de licences | `typecheck` vert ; script de contrôle des licences |
| 1 | `CapabilityManifest` (Zod, `tsc --strict`), registre, manifestes H3 / Wan / Kandinsky, branché sur le catalogue d'applications d'OpenField | Tests de validation + de planification (filtres durs avant score) |
| 2 | Schéma PostgreSQL projets/plans/prises ; API `/api/creative/*` ; file étendue (bail, heartbeat, fencing, idempotence) ; crédits reserve/settle/release ; quota S3 | Tests de panne : zéro double facturation, zéro job perdu |
| 3 | Agent GPU + adaptateur FastVideo (H3) sur GB10 puis 5090 ; stockage objet ; URL pré-signées | Une vidéo réelle générée, mesurée, facturée et rejouable |
| 4 | Interface simple : intention → devis → génération → résultat ; presets caméra ; géorestriction H3 | Parcours de bout en bout en fr-CA, accessibilité WCAG 2.2 AA |
| 5 | Moteur ComfyUI interne + compilateur de recettes + second modèle (Wan 2.2) | Test d'évasion S10 ; bascule automatique H3 → Wan hors territoire |
| 6 | Fork FreeCut intégré ; format plans/prises ; rendu serveur | Retake d'un plan sans casser le montage |
| 7 | AI Director v1 : plan, 2 candidats, contrôles déterministes + identité + VLM, reprise partielle | Mesure de coût et de taux de réussite sur un jeu de scénarios |
| 8 | Bibliothèque de personnages/références avec consentement vérifié | Tests de garde AUP 13 |
| 9 | Mode expert, export pro (ProRes/DNxHR, HDR), vidéos longues | Export vérifié par ffprobe |

Ouverture publique : seulement après lots 0–5 prouvés, interrupteur allumé par vous, affirmations publiques dans `claims.json` en « en_revue ».

## 12. Ce qui n'est pas fait

Aucun prototype, aucun test, aucune mesure propre, aucune installation. Le code d'OpenField a été lu, pas exécuté. Les conditions de l'API MiniMax et plusieurs licences secondaires n'ont pas été lues. Aucun avis juridique n'a été obtenu.
