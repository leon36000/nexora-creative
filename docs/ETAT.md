# Nexora Creative — où nous en sommes (31/10/2026)

Document pour le fondateur : ce qui est fait, ce qui est prouvé, ce qui ne l'est pas. Détail jour par jour : `docs/JOURNAL.md`. Mesures : `recherche/08-mesures-gb10.md`.

## En une phrase

**Nexora Creative tourne dans le navigateur sur le DGX Spark (pc6)** : une phrase en français devient une vidéo avec son (MiniMax H3), ou un **film de plusieurs plans** écrit et tourné par l'AI Director, retouchable plan par plan, remontable sans nouveau rendu et exportable pour Premiere ou DaVinci. Il est prêt à être branché au portail Nexora ; **le site, lui, n'a pas encore les routes nécessaires** (contrat écrit dans `docs/INTEGRATION-NEXORA.md`).

## La base

Fork d'**OpenField** (MIT), comme WorkStudio est un fork de Sim : interface React 19 dans le navigateur, serveur Fastify qui compile lui-même les graphes ComfyUI (ComfyUI n'est jamais exposé). Rebaptisé Nexora Creative, en français. Provenance : `app/UPSTREAM.md`.

## Ce qui est fait et prouvé

| Fonction | Preuve |
|---|---|
| Moteur **MiniMax H3** (FastH3 V2 NVFP4) sur GB10 | rendus réels : 5 s en 82 à 92 s, 10 s en 230 s, son stéréo vérifié [MESURÉ] |
| Moteur **Wan 2.2** (Apache-2.0), repli sans dépendre de H3 | rendu réel 5 s en 118,6 s [MESURÉ] |
| **Réécrivain LLM** des prompts H3 (guide officiel MiniMax + validateur déterministe) | votre exemple voiture → robot réussi du premier coup en 3,4 s ; défaut « champ inventé » trouvé et corrigé [TEST réel] |
| Accueil **Créer** : phrase → vidéo, formats, durées, son, Rapide / Qualité max, **partir de sa photo** | parcours complet dans le navigateur (pub café verticale) ; photo → vidéo réel (93 s) [TEST navigateur] |
| **AI Director** : idée → storyboard modifiable (plans, caméra, bible de continuité) → tournage → assemblage | film réel « Crimson Rising », 6 plans, 41 s, assemblé en 3,1 s, repris après plusieurs redémarrages du serveur [TEST réel] |
| **Plans enchaînés** depuis la dernière image du plan précédent | film « Métamorphose sous la pluie » : le plan 2 part de l'image extraite du plan 1, prompt I2VA [TEST réel] |
| **Refaire un seul plan** | version du film avec 1 plan retourné (94 s), 5 réutilisés, réassemblée en 2,8 s, nouvelle description visible [TEST navigateur] |
| **Montage sans rendu** (ordre, retrait, coupe ou fondu) et **exports pros** | version en fondus de 33,84 s en 2,4 s ; ProRes 422 HQ 10 bits en 2,4 s ; ZIP projet avec séquence FCP7 XML valide [TEST réel] |
| **Contrôle qualité** automatique (noir, figé, silence, durée) + reprise d'un plan raté | 4 tests ; tous les plans réels l'ont passé (la reprise n'a donc jamais eu à servir en réel) |
| **Licences** en échec fermé (LTX, FLUX.2 dev, UltraSharp bloqués ; H3 selon le territoire) et **registre de capacités** | 8 + 7 tests ; le moteur est choisi par le code, jamais par le LLM |
| **Multi-organisation** (prises, personnages, projets, direct isolés) | 3 tests d'isolation |
| **Connexion unique** au portail (OIDC + PKCE, patron WorkStudio) | test de bout en bout avec un faux site Nexora (3 tests) |
| **Crédits** des rendus (devis, réservation, validation ou libération) et **espace disque** par organisation | 4 + 2 tests contre une API de site simulée |

**79 tests automatisés verts**, contrôle de types vert, code sur GitLab (`root/nexora-creative`, branche `developpement`, demande de fusion !1).

## Ce qui n'est pas fait ou pas prouvé

- **Côté site Nexora (nexora-web)** : client OIDC « Nexora Creative », portée `creative:model`, routes `/api/oauth/creative-access`, `/api/creative/credits/*`, `/api/creative/storage`, carte du panneau. Rien n'est construit : je n'ai pas touché au dépôt du site.
- **Prix** : les crédits par seconde de GPU sont une proposition (0,5 crédit/s, soit ≈ 43 crédits pour 5 s rapides) ; à valider.
- **Juge visuel par IA** : conçu (rapport 09), pas construit faute d'un modèle vision appelable sur la passerelle de développement.
- **Production** : une seule instance (SQLite en WAL) et un seul moteur ComfyUI ; pas encore d'agent GPU séparé pour la RTX 5090 et la 5080, ni de stockage objet, ni de tests de panne provoquée.
- **FreeCut** (montage avancé multipiste) : écarté pour l'instant après inspection, car il exige Chrome ou Edge et garde les projets sur le disque de l'utilisateur. Le montage cloud de Nexora (plans) et l'export Premiere/DaVinci couvrent le besoin de départ.
- **Import du ZIP dans Premiere ou Resolve** : non essayé (logiciels absents de la machine).
- Juridique : la stratégie de territoire H3 et les obligations de sa licence restent à valider par un juriste (architecture §7).

## Pour l'essayer

Sur pc6 : `~/nexora-creative-data/engine/lancer-comfyui.sh` (moteur), puis `app/scripts/dev-nexora.sh` (studio), puis ouvrir <http://localhost:37160>. Poids et rendus : `~/nexora-creative-data/` (≈ 55 Go, hors dépôt).
