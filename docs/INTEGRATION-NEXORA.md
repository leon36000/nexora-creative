# Intégration de Nexora Creative au portail Nexora AI

Même patron que Nexora WorkStudio (`NexoraSite/docs/workstudio-integre.md`) : **une seule instance Nexora Creative, multi-organisations**, ouverte depuis le panneau « Mes outils » par **connexion unique**. Le site est le fournisseur d'identité OpenID Connect ; il remet à Nexora Creative, pour chaque utilisateur, la clé de passerelle `/v1` de **son** organisation (le LLM consomme ses crédits) et une API de crédits pour les rendus GPU.

État au 30/10/2026 : **côté Nexora Creative, écrit et testé avec un site simulé ; côté site, à construire** (le dépôt `nexora-web` n'est pas modifié par ce chantier). Ce document est le contrat que le site doit honorer.

```
Navigateur ──► Creative /auth/connexion ──(1)──► Site /api/auth/oauth2/authorize  (PKCE S256, portées openid profile email creative:model)
Navigateur ◄── Creative /auth/retour?code=…  ◄──(2)── code à usage unique
Creative ──(3)──► Site /api/auth/oauth2/token        (code + verifier + secret du client)
Creative ──(4)──► Site /api/auth/oauth2/userinfo     → sub, name, email, organization_id
Creative ──(5)──► Site /api/oauth/creative-access    Bearer <jeton> → { url, model, key, territory }
Creative ──(6)──► Site /api/creative/credits/*       (réserver, valider, libérer) avec la clé de l'organisation
```

## 1. Ce que le site doit ajouter (copie du patron WorkStudio)

| Élément | Détail |
|---|---|
| Client OIDC « Nexora Creative » | `CREATIVE_OIDC_CLIENT_ID`, `CREATIVE_OIDC_CLIENT_SECRET`, `CREATIVE_PUBLIC_URL` (retour exact `${CREATIVE_PUBLIC_URL}/auth/retour`). Première partie, consentement sauté, PKCE obligatoire, jetons de 10 minutes. |
| Portée `creative:model` | Ouvre la route d'accès ci-dessous. |
| `GET /api/oauth/creative-access` | Comme `workstudio-access` (`ensureModelAccess` de l'organisation) + **`territory`** : code pays ISO 3166-1 alpha-2 de l'organisation (adresse de facturation), ou `null` s'il est inconnu. Nexora Creative ferme MiniMax H3 quand il est `null` (licence H3, territoires exclus). Mêmes erreurs : 401, 403 `credits_required`, 429, 503. |
| `POST /api/creative/credits/reserve` | Corps `{ idempotencyKey, credits, label }`, en-tête `Authorization: Bearer <clé nxk_ de l'organisation>`. Réserve au grand livre (`reserve` de `packages/db/src/ledger.ts`, produit `creative`). Réponses : `200 { reservationId, credits }`, `402 insufficient_quota` (même message que la passerelle). Idempotent par `idempotencyKey`. |
| `POST /api/creative/credits/settle` | `{ reservationId, credits }` : débit réel (≤ réservé), le reste est libéré (`settleReservation`). Apparaît dans l'Activité du client (« Nexora Creative · rendu vidéo »). |
| `POST /api/creative/credits/release` | `{ reservationId }` : échec ou annulation, rien n'est débité (`releaseReservation`). |
| Espace disque | `recordStorageUsage(orgId, "creative", delta)` : appelé par les mêmes routes `credits/*` avec un champ `storageDeltaBytes` facultatif, ou par une route `POST /api/creative/storage` (à trancher par le site). |
| Panneau | Interrupteur `NEXORA_PRODUCT_CREATIVE` (patron de `NEXORA_PRODUCT_CODE`), état « Disponible » seulement quand l'instance répond et que le fondateur l'allume. |

## 2. Ce que Nexora Creative fait (code de ce dépôt)

- **Session** : après le retour OIDC, un témoin de session signé (HMAC) porte l'utilisateur et l'organisation ; la clé de passerelle reste côté serveur, jamais dans le navigateur.
- **Compte par requête** : `server/nexora/compte.ts` pose `{ organisationId, utilisateurId, territoire }` pour toute la requête ; licences, crédits et données le lisent.
- **Données isolées** : chaque prise, projet et personnage porte l'organisation ; une organisation ne voit, ne lit, ne télécharge ni ne supprime jamais ce qui ne lui appartient pas (test d'isolation).
- **LLM** : appelé avec la clé `/v1` de l'organisation (crédits débités par la passerelle, Privacy Router appliqué).
- **Rendu GPU** : devis en crédits avant tournage (`server/nexora/credits.ts`), réservation avant l'envoi au moteur, validation au prorata du temps GPU réel à la fin, libération en cas d'échec ou d'annulation.
- **Mode poste local** (développement, démonstration) : sans `NEXORA_OIDC_*`, un seul compte local (`NEXORA_TERRITOIRE`), aucun débit.

## 3. Prix (à valider par le fondateur, rien n'est publié)

1 crédit = 1 ¢ CA. Proposition de départ, calibrée sur les mesures du GB10 (`recherche/08`) et à réviser avec les mesures sur RTX 5090 : le prix suit le **profil et la durée**, pas la machine (le temps de chargement des modèles est à la charge de Nexora). Les montants exacts vivent dans la configuration, jamais en dur dans l'interface.
