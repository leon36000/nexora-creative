# Audit documentaire local — Nexora, 04/11/2026

Périmètre : lecture seule, aucun secret ouvert, aucun réseau, aucun test/rendu/déploiement lancé. Fichiers consultés : `AGENTS.md` des deux dépôts ; Creative `docs/{PASSATION-AGENTS,ETAT,JOURNAL,PLAN-AUTONOME,PROCESSUS-TECHNOLOGIE,FEUILLE-DE-ROUTE-MAITRE,RESSOURCES}.md`, `docs/backlog/*` ; Site `docs/{ETAT-DES-LIEUX,direction-du-site,refonte-signal,deploiement-proxmox-pile,deploiement-proxmox-workstudio,proxmox-mise-en-service,infra}.md`, conception du 26/10, ledger, `docs/vps/*`, preuve VPS. Les mesures ci-dessous sont des **preuves historiques consignées**, pas une mesure de production effectuée aujourd'hui.

## 1. Corrections indispensables à la passation

1. **Ne pas prendre les introductions d'ETAT pour l'état actuel.** Creative ETAT intro dit encore pc6, portail absent ; ses entrées anciennes disent SAM 2.1, pc3 inaccessible et gpu-unlock impossible. JOURNAL ligne 321-333 supersède : pod SAM 3.1 sur pc3, palier pro mesuré, V100 testée. Site ETAT-DES-LIEUX est du 30/10 (Creative non construit, pas Proxmox, pas Dockerfile) : totalement historique.
2. **V100 : CUDA cu126, pas cu128.** JOURNAL ligne 330 : torch 2.14.1 cu126, sm_70 ; roues cu128 et cu130 sans sm_70. FP16, pas BF16/FP8. 188,7 s/224 images, 0,84 s/image, réseau QEMU user sans accès VM202, venv 7,1 Go, poids WebDAV montés depuis pc3.
3. **Nom 3D décidé : Nexora Mesh.** L'ancienne phrase « Relief, nom à choisir » est révoquée par U107. Le code local principal reste plus ancien, branche `feat/nexora-mesh-nom` b636db9 porte `/mesh`, alias `/relief`/`/object`. Référence locale `gitlab/feat/nexora-mesh-nom` existe : ne pas dire catégoriquement « jamais poussé ».
4. **Une partie de la production est déjà en pod.** JOURNAL ligne 322 : `detourage` namespace nexora, hostPort 8231 sur 192.168.1.126, kaniko, registre provisoire, NetworkPolicy, liste d'IP 192.168.1.122. Phrase « rien en pod en production » fausse. Reste de la conteneurisation non démontré.
5. **Studio transcription GPU livrée historiquement** (MR !33 / !35, commits 11bd236, fccce68, 6758f04, 55b0603, da27fa4). Lire `git show gitlab/developpement:docs/JOURNAL.md` : `/transcrire` :8190 VM204, Whisper large-v3-turbo fp16, WAV, 150 Mo/1 h, jeton exigé/503 sans fichier, client repli CPU. 70 s audio → 2,65 s GPU vs 29,4 s CPU, 221/222 mots, clip149s→3,9s. Essai visuel UI encore attendu ; autres points STT/TTS/Demucs/embed sans jeton LAN historiquement.
6. **Références de branche ≠ production actuelle.** Principal Creative 7139043 est en retard de 6 commits sur référence locale `gitlab/developpement` da27fa4 ; Site main1b8c93a est en retard de 7 commits sur référence locale `gitlab/main`56cb4c4. Ces refs sont des instantanés locaux ; le réseau est bloqué dans cette revue.
7. **Site orange et Gitspace caché sont dans gitlab/main** : 7764d2c/3b95ebe/d8f40ea (orange), c8e1c3a (`GITSPACE_VISIBLE=false`), df79081/56cb4c4 (reliquats verts, MR web !24). Le `main` local visible en bleu/vert ne représente pas ce dernier code connu.
8. **LTX : verrou réel, question du fondateur distincte.** `app/server/nexora/licences.ts` L49-60 bloque les ensembles LTX. JOURNAL ligne 331 dit « décision du fondateur », mais ne pas inventer une demande de refus : U068 demande intégration si droits/résultats permettent, U069 rappelle ne pas perdre de temps juridique, U093 décide Wan sur pc4. Identifier précisément ce verrou et les limites de ressources ; ne pas l'effacer pendant cette revue.
9. **Puissance CPU : 87% de fréquence/performance**, pas 13% de watts garantis. Le script annexé écrit intel_pstate max_perf_pct ou scaling_max_freq. La demande utilisateur était réduction GPU20%, CPU10-15% ; la réduction électrique CPU n'est pas mesurée.
10. **Rétention docs obsolète** : RESSOURCES §1 dit supprimer brouillons/rendus ; U059/U064/U110 exigent garder absolument tous les films et infographies depuis le début. Cette consigne récente prime : jamais supprimer les vidéos sous prétexte de nettoyage.
11. **Rapports absents ≠ travaux faits.** Principal : recherche/26 absent (présent branche film), recherche/29 et docs/backlog/{relief,nexora-mesh-interface}.md absents. Reconstituer la recherche29 et les spécifications au lieu de les annoncer fusionnées. Les rapports H3/Pika du scratchpad restent perdus tant qu'aucune copie durable n'est trouvée ; ne pas publier un gain Pika non mesuré.

## 2. Oublis importants à réintégrer au suivi

- **Nexora Code : risque de code perdu** : JOURNAL ligne 217, RESSOURCES §6.2 : `/home/pc6/Desktop/NexoraCode/src`, branche feat/rebrand, 10 commits non poussés, push refusé « shallow update not allowed », archive `.git` copiée sur pc5 `pc6/depots-non-pousses/`. **Contrôle local de cette revue : `/home/pc6/Desktop/NexoraCode/src` et son parent NexoraCode sont absents. Aucun worktree WorkStudio trouvé sous Desktop ni `/media/pc6/Storage/Nexora/travail` (profondeur 4, hors dépendances).** Impossible donc de vérifier ces 10 commits ou la copie pc5 depuis cette session ; retrouver l’archive avant de conclure à une perte ou à une publication réussie. Site : image code-workspace, binaire, wildcard DNS/TLS et proxy terminal restent non prouvés.
- **RAG** : images pc5-rag ~8 Go et cache modèle ~5,4 Go sur pc6 ; emplacement/service réel inconnu, à clarifier avant migration. Ne pas confondre nom pc5-rag avec preuve d'hébergement pc5.
- **Facturation réelle** : agent3paliers a mesure/grand livre/réservation, mais ETAT dit rien débité en réel sur VM sans portail. Routes site observées : seulement `/api/creative/config`, `/api/admin/creative/...` ; pas de routes creative credits/storage sous `web/src/app/api/creative/`. #4 (Studio assistant/bulle) non facturé. Audit authz Studio #54 requis avant ouverture/API.
- **Bulle effet** : v0 livrée MR !12 (26 recettes, 19 tests), un appel LLM réel démontré ; banc de 30 phrases et parité aperçu/export #8 encore ouverts. WebGPU absent navigateur intégré : effets appliqués mais invisibles, ne pas conclure au rendu correct à partir de l'état des calques.
- **Persistance projets Studio côté serveur, collaboration/revue**, verrou concurrent et invalidation ciblée : encore backlog (#10,#12,TA6,TA24).
- **Marketing v1 partiel** : kit, 7 formats/9 gabarits, 3 propositions, PDF TrimBox/BleedBox, PNG≈300dpi, SVG, CMJN conditionnel Ghostscript ; 26 tests, 285-390ms/gabarit, page mobile sans débordement. Restent : fond Qwen depuis la page, vectorisation logos, PDF/X certifié+ICC, n-up, Fabric glisser-déposer, réseaux 1:1/4:5/9:16, affiche et DL propres, présentation/PPTX, campagne globale agent unifié.
- **Voix et musique** : aucun modèle n'a acquis le statut « accepté fondateur » par un score automatique ; voix native H3 cheap, Eleven Alexandre trop smooth, Drama3 débit lent, Mistral demandé. Écoute humaine FR/EN indispensable ; une note d'analyse audio n'est pas une validation esthétique.
- **Mode long métrage** : squelette1 080 plans estimés<500ms ; seulement4 plans / 20 s dont2 tournés, pas un long métrage démontré. Continuité @ prouvée2plans seulement ; pas50. Film de 5 min, Fountain, tableaux et lots nocturnes restent backlog.
- **GPU pc5** : utiliser deux GPU ne double pas automatiquement la VRAM d'une tâche ; routage parallèle et répartition de petites tâches d'abord. gpu-unlock PR294 : 2080 45→71TFLOPS et2070 38→59, mais TRELLISint8 inchangé. VM2048GoRAM/60Godisque, ~4Golibres historiquement, quatrevues Pixal font tuer ComfyUI ; SAM3.1pc5 nécessite12GoRAM selon recherche28. Ne pas relancer/modifier production pendant revue.
- **VM205/registre/magasin modèles** : conteneurs reproductibles et sauvegarde GitLab complète avant formatage sont essentiels, pas livrés simplement parce que Dockerfiles existent. Ne jamais formater pc4 avant sauvegarde vérifiée/restauration.
- **Sauvegardes** : fondateur interdit sauvegardesNVMe et attend HDD10-20To ; implémentation provisoire conserve keep-last=1 et volume de 80 Go (pas « aucune sauvegarde »). Archives40 Go / 21,6 Go historiques. Les propositions dimensionnement201/202/203 de RESSOURCES §4 sont dites « non appliquées » dans cette version : ne pas les présenter faites sans vérification.

## 3. VPS : preuve existante bien plus précise que « système prêt »

Commit82aef4d, fusion1b8c93a ; `NexoraSite/docs/preuves/s6/e2e-vps-pc5.md` (02/11), `docs/vps/{EXPLOITATION-PC5,capacite-et-isolation-pc5}.md` : 3 clients tests, checkout → stripe-mock → webhook signé → tâche → clone cloudinit → SSH, stop/start/reboot, impayé/grâce/suspension et résiliation/rétention/suppression des disques réels. Nettoyage3 VPS et comptes fini, journaux comptables/orgs restent. Pas de facturation horaire ; pas de vraie clé Stripe de test ; pas accès Internet entrant ; réinstallation et reprise suspendue après invoice.paid non prouvées. Mode pilote NAT10.77.0.0/24 via vmbr1, gabarit9001 dans pool clients-vps, SSH seul, pas d'IP publique par client. Capacité vendable historique8vCPU/4096Mo/60Go, plansnano/mini/standard prixdéveloppement. Toute vente publique attend prix, paiement réel autorisé, adresses publiques/infrastructure réseau.

Bogues corrigés dans vrai Proxmox : nextid400si9000pris ; 403horspool=introuvable ; skiplockréservéroot ; booléens1/0dansquery ; CTzone1nécessaireNATavecparefeu ; pontdansinterfacesprincipal ; SSHworkerabsent/variablesnontransmises. Réconciliation `deploy/vps/reconcilier.sh` est lecture seule et détecte zombies/orphelins/plafonds/pool80%.

## 4. Site, WorkStudio : ancien et actuel à distinguer

- Site `docs/refonte-signal.md` §5 : VM201, `SITE_URL=https://pc5-proxmox.tail0c55ff.ts.net`, tailscale hôte→nginx192.168.1.121:80,73pages publiées via version/approbation/promote. Fermé/noindex ;6pageslégales à garder horspublication. Rebrand `brand.ts`, nom/domaine nonchoisi. Produit«votreordinateur» enpréparation ; ne paspromettre une capacité livrée.
- Creative V4«Unephrase.Unfilm.» suraccueil+fiche, `media_lang` FR/EN, ancien filmspatialretiré ; commits a1aaede/7ccfbdb,0a93a72/fa65542. Films WorkStudio,Surveillancev2,Modèles/API surpages :764e54d/1e765b7,slugEN06bf143/d9e1f02.
- WorkStudio VM203, correctionproxy502en-têtes5834566/e448ce3 ; reprise workflow réellement prouvée Mailpit, fully_resumed/completed et1courriel cc6348d/fd5dd62. Démo«Triducourrierentrant», pas de vraie livraisoncourriels tant queSMTPprovisoire.
- Restent : domaine/DNS/TLS, SMTP/SPF-DKIM-DMARC et vraies adresses, Stripe, prix / change / offres, licenceDirectusOIG, comptepropriétaire/2FA, copie hors VM des secrets parfondateur, sauvegarde du produit WorkStudio chiffrée planifiée et restauration jamais éprouvée, modèle de production approuvé. Ne pas redemander une autorisation générale déjà donnée ; demander uniquement décision concrète réellement manquante.

## 5. Définition de fini à conserver (FEUILLE-DE-ROUTE-MAITRE §5)

Première vidéo<3min5personnes/5sans aide ; carteimprimable<2min ; audit≥4,2/5aucuneligne<3 ; devis±10% ; intention gardée etCtrl+Z ; juge≥0,9bancdoré + visage≥0,7sur20plans +fondateur≥8/10 ;0tâcheperdue/100pannes et0doubledébit ;0axegrave,FR/ENcomplets ;API/MCP/skillsutilisésréellementparClaudeetCodex. Ce sont des critères futurs, **pas des mesures acquises**.

Ordre TA : A=TA1,TA25,TA20,TA9,TA24 ; B=TA2,TA4,TA3,TA19 ; C=TA5,TA6,TA8,TA7,TA17 ; D=TA11,TA12,TA13,TA14,TA18,TA10 ; E=TA15,TA23,TA21,TA22,TA16. Les tarifs0,02/0,10CAD/s et29CAD/mois sont propositions, non décision commerciale du fondateur.

## 6. Liste des 57 issues prévues (pas une attestation qu'elles sont ouvertes/fermées aujourd'hui)

Source autoritative locale : `docs/backlog/feuille-de-route-maitre.json`, correspondance `numeros-gitlab.json`, suivi#58. Les titres listent le périmètre à ne pas perdre ; voir critères et dépendances dans JSON.

| Issue | Vague | Priorité | Chantier |
|---|---|---|---|
| #1 | 1 | P1 | Bulle d'effet v1 : banc LLM de 30 phrases hors recettes maison |
| #2 | 1 | P1 | Bulle d'effet : recette gardée sur l'élément, « Modifier l'effet », préréglage perso |
| #3 | 1 | P2 | Bulle d'effet : découvrabilité (raccourci, règle, assistant, clic extérieur) |
| #4 | 1 | P1 | Facturer les jetons des appels du Mode Studio (assistant, bulle) |
| #5 | 1 | P2 | Importer gl-transitions (WGSL) dans le registre de transitions |
| #6 | 1 | P1 | Rampe de vitesse (famille `temps` de la bulle) |
| #7 | 1 | P2 | Calques procéduraux : pluie, neige, étincelles, confettis (P0) |
| #8 | 1 | P1 | Parité aperçu/export et repli sans WebGPU |
| #9 | 1 | P1 | Tests e2e Playwright du Mode Studio en CI GitLab |
| #10 | 1 | P1 | Projets Studio sauvegardés côté serveur, versions et reprise |
| #11 | 4 | P2 | Proxys et performance de la timeline |
| #12 | 7 | P2 | Commentaires horodatés et lien de revue en lecture seule |
| #13 | 2 | P1 | Kit de marque partagé par tous les modes |
| #14 | 2 | P3 | Extraction automatique du kit depuis un site ou un logo |
| #15 | 2 | P1 | SpecConception JSON et gabarits paramétrés sur le moteur des imprimés |
| #16 | 2 | P1 | Mode Marketing dans l'interface (brief → 3 propositions → retouche → PDF) |
| #17 | 2 | P2 | Contrôle préliminaire imprimeur et CMJN/PDF-X |
| #18 | 2 | P3 | Imposition n-up (planches de cartes, accroche-portes) |
| #19 | 2 | P1 | Compétence « accroches » (AIDA / PAS) et juge |
| #20 | 2 | P2 | Module Logo (Qwen → vtracer → nettoyage SVG) |
| #21 | 2 | P2 | Déclinaisons de format automatiques (1:1, 4:5, 9:16, 16:9) |
| #22 | 2 | P2 | Variantes en lot et A/B |
| #23 | 2 | P3 | Présentation (deck) à partir du kit de marque |
| #24 | 3 | P1 | Voix off TTS fr-CA / en-CA avec mots horodatés |
| #25 | 3 | P2 | Doublage traduit (STT → LLM → TTS → calage) |
| #26 | 3 | P2 | Lip-sync sur audio fourni (avec consentement) |
| #27 | 3 | P2 | Bruitages : bibliothèque CC0 indexée par texte (famille `audio` de la bulle) |
| #28 | 3 | P1 | Mixage final : loudnorm deux passes, crête −1 dBTP, ducking auto |
| #29 | 3 | P1 | Sous-titres animés stylés (mot à mot) aux couleurs du kit |
| #30 | 4 | P1 | Planificateur GPU unique (GB10, RTX 5090, Turing pc5) |
| #31 | 4 | P1 | File de jobs persistante : bail, heartbeat, idempotence, reprise |
| #32 | 4 | P2 | Brouillon fidèle à la finale |
| #33 | 4 | P2 | Mode « Master » : agrandissement, restauration, 60 i/s |
| #34 | 4 | P1 | Banc doré nocturne (régression de qualité bloquante) |
| #35 | 4 | P2 | Observabilité produit et tableau de bord admin |
| #36 | 4 | P1 | Devis unifié, crédits et marge |
| #37 | 5 | P1 | Masques par texte (SAM 3) sur une plage |
| #38 | 5 | P1 | Retrait d'objet (SAM 3 + DiffuEraser / VACE) |
| #39 | 5 | P2 | Remplacement de ciel et relight |
| #40 | 5 | P2 | Restyle vidéo-à-vidéo d'une plage (VACE) |
| #41 | 5 | P2 | Plaques générées sur noir (éclats, fumée, flammes) + mélange écran |
| #42 | 5 | P1 | Recadrage auto 9:16 avec suivi du sujet et B-roll automatique |
| #43 | 6 | P1 | Mode Long métrage : modèle Film, Fountain, tableau d'états, lots nocturnes |
| #44 | 6 | P1 | Cohérence long format : bible et juge de continuité |
| #45 | 6 | P2 | Mode Cours v1 (leçon → narration horodatée → scènes → chapitres) |
| #46 | 7 | P1 | API publique et MCP distant avec clés et crédits |
| #47 | 7 | P2 | Pack de skills « nexora-creative » pour agents externes |
| #48 | 7 | P1 | Bibliothèque d'actifs intelligente, projets et versions communs aux modes |
| #49 | 7 | P3 | Gabarits partagés dans l'organisation (« Flows ») |
| #50 | 7 | P2 | Mobile : mode simple complet à 375 px, Studio en revue |
| #51 | 7 | P2 | i18n : en-CA complet et correction des locales fr de FreeCut |
| #52 | 7 | P2 | Accessibilité (clavier, ARIA, contrastes AA, axe en CI) |
| #53 | 7 | P1 | Onboarding : première vidéo en moins de 3 minutes |
| #54 | 1 | P1 | Sécurité : authz par organisation des routes Studio, limites, CSP |
| #55 | 1 | P2 | Déploiement continu VM 202 et retour arrière en une commande |
| #56 | 6 | P3 | Relief 3D dans le Studio et le Marketing |
| #57 | 6 | P1 | Mode Agent unifié : le Producteur pilote Studio et Marketing |

## 7. Contrôle de dépôts transversaux (lecture seule)

Le 04/11, `/home/pc6/Desktop/NexoraCode/src` et `/home/pc6/Desktop/NexoraCode` sont absents. Aucun dossier WorkStudio n’a été trouvé sous Desktop ni `/media/pc6/Storage/Nexora/travail` (profondeur quatre, hors dépendances). Les mentions de dix commits `feat/rebrand`, du refus shallow et de l’archive `.git` sur pc5 sont des traces historiques des 02–03/11, pas un état local confirmé. Ne pas les supprimer du suivi : retrouver la copie ou prouver leur publication sur GitLab.
