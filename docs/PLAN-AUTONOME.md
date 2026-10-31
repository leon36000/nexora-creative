# Plan de travail autonome — Nexora Creative

Mandat du fondateur (30/10/2026, soir) : carte blanche. Recherche approfondie (y compris arXiv), téléchargements et tests autorisés, faire l'outil le plus puissant et le plus simple possible, travailler en autonomie dans une boucle. Ce fichier est relu au début de **chaque** itération ; `docs/JOURNAL.md` dit où on en est.

## Règles permanentes (ne jamais déroger)

1. **Machine partagée (pc6 = DGX Spark GB10).** D'autres sessions, la démo publique du site et des projets d'autres entreprises tournent ici. Ne jamais arrêter un processus par motif (`pkill -f`, `killall`) : noter le PID de ce que je lance et n'arrêter que lui. Ne pas toucher aux conteneurs `nexorasite-*`, `infratechca-*`, `jeuxvideoca-*`, ni au dossier `~/Desktop/NexoraSite` (lecture seule).
2. **Disque.** Vérifier `df -h /` avant tout téléchargement. Garder **au moins 50 Go libres** ; budget total de poids pour Nexora Creative ≈ 80 Go dans `~/nexora-creative-data/` (hors dépôt). Télécharger fichier par fichier, jamais un dépôt HF entier. Nettoyer ses propres images Docker et caches de build.
3. **Aucune dépense, aucun compte créé**, aucun secret dans le dépôt ni dans un journal. Rien vers GitHub ; GitLab pc4 seulement (`git push gitlab`).
4. **Licences.** Rien de non commercial, AGPL ou de clause « produit concurrent » dans le produit (LTX-2.x, FLUX.2 dev, 4x-UltraSharp, MusicGen exclus). H3 : territoire par compte, « MiniMax H3 » affiché dans l'interface. Provenance gardée (`UPSTREAM.md`, `THIRD_PARTY_NOTICES.md`).
5. **Code tiers.** Dépôts clonés dans le scratchpad ou `vendor/` ; ComfyUI et moteurs dans des conteneurs ou des environnements virtuels dédiés, écoute sur 127.0.0.1 seulement, ports de la plage 37xxx.
6. **Vérité.** Distinguer [DOC] / [CODE] / [TEST] / [MESURÉ par nous]. Ne jamais déclarer une fonction faite sans preuve (test vert, mesure, capture). Les échecs sont écrits au journal tels quels.
7. **Méthode.** Test qui échoue avant le code pour toute logique. Commits en français terminés par `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. `main` est protégée sur GitLab : on pousse sur `developpement` (demande de fusion ouverte vers `main`, fusionnée par le fondateur).
8. **Simplicité pour l'utilisateur.** Mode simple d'abord (une intention en français → résultat), mode expert ensuite. fr-CA d'abord.

## Lots (cocher au fur et à mesure, avec la preuve)

- [x] **R. Littérature scientifique** — fait (`recherche/07`). : `recherche/07-litterature-scientifique.md` (arXiv : génération vidéo, distillation/accélération, cohérence de personnages, vidéos longues, contrôle caméra, agents réalisateurs, évaluation automatique, édition vidéo). Chaque article : idée, résultat publié, ce qu'on en fait dans Nexora Creative.
- [x] **0b. Fork OpenField** — fait le 30/10 : import brut c355ce9, politique de licences `app/server/nexora/licences.ts` branchée sur le preflight (8 tests verts, typecheck vert) [TEST]. dans `app/` : `UPSTREAM.md` (commit d'origine), notices, retrait des modèles non commerciaux, graphes LTX isolés et désactivés, `npm install` + `typecheck` verts, contrôle de licences (`scripts/check-licenses.*`).
- [x] **1. Moteur local sur GB10** — fait (`recherche/08`). : environnement PyTorch pour sm_121 (vérifier `torch.cuda.get_arch_list()`), ComfyUI figé (version notée), nœuds minimaux. Rapport `recherche/08-mesures-gb10.md`.
- [x] **2. Premier rendu H3 réel** — fait : 92,1 s à froid, 82,1 s à chaud (`recherche/08`). (FastH3 quantifié) via le serveur OpenField forké ou via l'API ComfyUI : vidéo de 5 s, temps froid et chaud, pic mémoire, avec et sans audio. Vidéo gardée hors dépôt, empreinte et réglages au journal.
- [x] **3. Second moteur à licence propre** — Wan 2.2 TI2V-5B : rendu réel 5 s en 118,6 s à froid (`recherche/08`), choix automatique par licence et territoire. (Wan 2.2 TI2V-5B, Apache-2.0) : même mesure. Preuve « jamais exclusif ».
- [ ] **4. Registre de capacités** (`CapabilityManifest` Zod, rapport 05 §5) + planificateur (filtres durs puis score) + tests ; branché sur le catalogue d'applications.
- [~] **5. Multi-client** — isolation par organisation (SQLite, tests), SSO OIDC (test de bout en bout avec faux site) ; reste : PostgreSQL et stockage objet pour la production. : PostgreSQL d'essai (conteneur dédié, port 37432), organisations/utilisateurs, projets/plans/prises, connexion par jeton signé (contrat compatible avec la connexion unique Nexora), stockage objet (SeaweedFS ou Garage) avec quota.
- [~] **6. File et agent GPU** — crédits réserver/valider/libérer (tests) ; reprise après redémarrage prouvée en réel ; reste : agent GPU séparé, bail/fencing, tests de panne. : bail, heartbeat, jeton de fencing, idempotence, annulation ; crédits réserver/valider/libérer via une interface compatible avec le grand livre Nexora ; tests de panne (SIGKILL moteur, SIGKILL agent, coupure base).
- [x] **7. Interface simple** — Créer (clip et film), storyboard modifiable, plans d'un film, « MiniMax H3 » affiché ; testée dans le navigateur. : « Décris ta scène » → plan proposé (plans, caméra, durée, coût) → génération → résultat ; préréglages de cinéma ; affichage « MiniMax H3 » ; territoire du compte.
- [x] **8. AI Director v1** — film réel de 6 plans prouvé ; contrôle qualité + reprise, plans enchaînés, refaire un plan (tests). Juge VLM : en attente d'un modèle vision sur la passerelle. : découpage en plans, 2 candidats par plan, contrôles déterministes puis juge, reprise d'un seul plan sans tout régénérer ; démontré sur l'exemple « voiture qui se transforme en robot géant, caméra en orbite ».
- [ ] **9. Montage** : timeline (FreeCut ou équivalent MIT), plans → prises, export MP4 et ProRes (FFmpeg LGPL), reprise du projet sans perte.
- [ ] **10. Vérification de bout en bout** dans le navigateur (parcours débutant complet), rapport final `docs/ETAT.md` (fait / testé / mesuré / pas fait).

## Condition d'arrêt de la boucle

Tous les lots cochés avec leurs preuves, `docs/ETAT.md` écrit et poussé sur GitLab. Un lot impossible (matériel, licence) est marqué « bloqué » avec la raison et un contournement ; il ne bloque pas les suivants.
