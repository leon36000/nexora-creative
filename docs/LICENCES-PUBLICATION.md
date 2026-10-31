# Licences : ce qu'il faut régler avant de publier la vidéo et d'ouvrir le produit (31/10/2026)

Dossier préparé pour le fondateur et son juriste. **Rien n'a été envoyé à MiniMax ni à Alibaba** : les messages ci-dessous sont des brouillons. Ce n'est pas un avis juridique ; les citations viennent des textes de licence lus dans `recherche/03-modeles-video-licences-h3.md` et `recherche/11-image-et-musique.md`.

## 1. Publier la bande-annonce sur les réseaux sociaux (MiniMax H3)

| Point | Ce que dit la licence | Conséquence |
|---|---|---|
| Territoire (I.3, I.5, V.4) | Monde entier **sauf** États-Unis, Union européenne, Royaume-Uni, Corée du Sud. Interdit d'utiliser, reproduire, distribuer **ou afficher** les sorties hors du territoire | Une publication sur un réseau public est visible aux États-Unis et en Europe : zone de risque directe |
| Demande de licence pour les territoires exclus (II) | Formulaire public : https://platform.minimax.io/h3-license | Seule voie propre pour publier partout |
| Affichage (IV.2) | « MiniMax H3 » en évidence dans l'interface du produit | Fait dans Nexora Creative (étiquette sur les fonctions H3) |
| Garde-fous (V.5) | Modération, signalement, suspension des récidivistes | Modération en place ; **mécanisme de signalement et suspension à construire** côté site |
| Droit applicable (IX) | Hong Kong | À faire relire par un avocat québécois |

**Ce qui est sans risque de licence dans la bande-annonce publique** : la musique (MiniMax-Music3, communautaire, aucun territoire exclu, mention « MiniMax-Music3 » à afficher), les sons synthétisés par nous, les cartons et le logo. **Seuls les plans vidéo H3 posent la question du territoire.**

Options, de la plus sûre à la plus risquée :
1. Obtenir la licence MiniMax pour les territoires exclus (brouillon ci-dessous), puis publier partout.
2. Publier seulement sur des comptes et des audiences au Canada / hors territoires exclus (difficile à garantir sur un réseau public ; à faire valider par le juriste).
3. Refaire la vidéo publique avec un modèle sans restriction de territoire (Wan 2.2 Apache-2.0, Kandinsky 6.0 MIT) : écarté pour l'instant sur ordre du fondateur (H3 seul).

### Brouillon de demande à MiniMax (à envoyer par le fondateur, pas par moi)

> Objet : Demande de licence MiniMax H3 pour les territoires exclus (Nexora Creative)
>
> Bonjour, Nexora est une entreprise québécoise qui exploite Nexora Creative, un studio de création vidéo et image hébergé (SaaS) qui utilise MiniMax H3 et MiniMax-Music3 avec l'affichage « MiniMax H3 » et « MiniMax-Music3 » dans l'interface, une modération avant rendu et un mécanisme de signalement. Nous demandons une licence couvrant la diffusion de contenus générés avec H3 aux États-Unis, dans l'Union européenne, au Royaume-Uni et en Corée du Sud, d'abord pour la promotion de notre produit sur les réseaux sociaux, puis pour les utilisateurs finaux de notre service. Pouvez-vous aussi confirmer par écrit : (1) la définition du revenu pour le seuil de 20 M$ ; (2) le cas d'un client situé dans le territoire autorisé qui publie ensuite dans un territoire exclu ; (3) l'usage de l'API hébergée pour les utilisateurs situés dans un territoire exclu. Merci.

## 2. Qwen-Image-2.1 (Alibaba)

- Licence : **Qwen Research License**, « non commercial » = recherche ou évaluation. La démonstration privée à des investisseurs est de l'évaluation ; tout produit payant ou toute publication marketing ne l'est pas.
- Dans le code : `licences.ts` règle « demo », actif seulement avec `NEXORA_MODE_DEMO=1`. La bande-annonce publique n'en contient aucun plan.
- Pour un usage commercial : écrire à Alibaba (model-business@notice.qwencloud.com). Brouillon :

> Subject: Commercial license request for Qwen-Image-2.1 (Nexora Creative)
>
> Hello, we operate Nexora Creative, a hosted AI creative studio (Quebec, Canada). We would like a commercial license for Qwen-Image-2.1 weights for use inside our hosted service, including generated outputs delivered to end users. Please send us your commercial terms and pricing, and confirm whether outputs may be used in our marketing.

- Défaut propre : **Qwen-Image-2512 (Apache-2.0)**, non installé (≈ 30 Go) ; il faut de la place disque (voir §4).

## 3. Autres points déjà identifiés

- Ressemblance avec des franchises : H3 reproduit parfois des designs connus sans qu'on les nomme (robots, cockpit de saut en hyperespace). Revue humaine des plans avant toute publication ; un contrôle automatique de ressemblance reste à construire.
- Aucun A/B sonore par un humain n'a été fait : écouter les trois versions avant publication.
- Registre d'affirmations du site (`cms/content/claims.json`) : à renseigner pour chaque chiffre de la page marketing avant son intégration.

## 4. Espace disque de pc6

Le disque unique de pc6 est à 93 % (66 Go libres). Remettre H3 sur le GB10 demande 35 Go (poids FastH3 13,6 + encodeur texte 15,7 + VAE 5,8) et ramènerait la réserve à 31 Go, sous la règle des 50 Go. Qwen-Image-2512 demanderait ≈ 30 Go de plus. Ce qui est récupérable, **hors de mon périmètre** (à autoriser explicitement) : cache de build Docker (15,6 Go dont 5,5 Go récupérables), volumes Docker non utilisés (13 Go récupérables), images non utilisées (6,3 Go), caches `~/.cache/uv` (6,7 Go) et `pip` (2 Go).
