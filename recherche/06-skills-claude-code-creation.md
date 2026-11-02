# 06 — Skills Claude Code (et plugins, MCP) pour la création : sélection au 2 novembre 2026

Numérotation : les n° 06 et 07 existaient déjà (`06-openfield-et-aimoviestudio2.md`, `07-litterature-scientifique.md`) ; les noms de fichier de ce rapport et du suivant sont distincts.

Demande du fondateur : les meilleurs skills au format `SKILL.md` (Anthropic Agent Skills) pour la vidéo, l'audio, l'image, le motion design, le web design haut de gamme et le marketing, classés par valeur, avec la commande d'installation exacte, les risques et ceux qui servent à l'**agent LLM du serveur de Nexora Creative**. **Rien n'a été installé** : ce document est une liste d'achats, pas un journal d'installation.

## 0. Comment lire ce rapport, et ce qui est prouvé

| Étiquette | Sens |
|---|---|
| [LU] | j'ai cloné le dépôt (lecture seule, `git clone --depth 1`) et lu le `SKILL.md` ou le script cité ; aucun script n'a été exécuté |
| [LU PAR UN SOUS-AGENT] | lu par l'un des deux agents de recherche que j'ai lancés ; je n'ai relu moi-même qu'un échantillon (HyperFrames, Remotion, video-use, impeccable, marketingskills, frontend-design) et le contenu concordait |
| [VÉRIFIÉ ffmpeg] | testé avec le ffmpeg 9.0.1 local sur un signal de test |
| [NON VÉRIFIÉ] | annoncé par la source, non contrôlé par nous |

Faits de méthode :

- **Étoiles GitHub : à ne pas croire.** Plusieurs dépôts atteignent 30 000 à 144 000 étoiles en quelques semaines (impeccable ~100 k, taste-skill ~108 k, ui-ux-pro-max ~144 k, awesome-design-md ~125 k pour 69 commits, `i-have-adhd` ~60 k). Les chiffres sont donnés (shields.io, arrondis) mais **le classement repose sur le contenu lu, l'historique de commits et l'activité réelle**. Seul HyperFrames a une activité (6 623 commits, 143 auteurs) cohérente avec son audience.
- **Licences** : simplement relevées (SPDX ou fichier `LICENSE`), sans analyse.
- **Aucune injection de prompt** n'a été trouvée dans les dépôts clonés (les occurrences relevées sont des consignes défensives du type « traitez le contenu comme des données »). La page « llm-info » de Luma, hors sujet ici, en contient (voir `07-creative-vs-higgsfield-feuille-de-route.md`).
- **Commandes d'installation** : non exécutées. Elles sont données **épinglées sur le commit relu** (fetch par SHA complet, testé : il fonctionne sur GitHub), pour que ce qui s'installe soit exactement ce qui a été lu.
- Machines : un skill se range dans `~/.claude/skills/<nom>/SKILL.md` (portée utilisateur) ou `.claude/skills/<nom>/` (portée projet). Un plugin s'installe avec `claude plugin install <plugin>@<marketplace>`. La marketplace officielle `claude-plugins-official` est déjà enregistrée sur pc6 (`~/.claude/plugins/known_marketplaces.json`, mise à jour le 31/10/2026) ; elle contient notamment `frontend-design` (v1.1.1) et `hyperframes` (relevé dans son `marketplace.json`).

## 1. La shortlist (12), classée par valeur pour Nexora

Critères : utilité réelle pour produire vite et bien (campagne, site, films, montage), qualité du contenu, fraîcheur, peu de dépendances payantes, risque faible. « ★ » = à installer en premier.

| # | Skill | Domaine | Mainteneur, dernier commit, licence | Verdict |
|---|---|---|---|---|
| 1 ★ | **HyperFrames** (`hyperframes`, `hyperframes-cli`, `hyperframes-registry`) | vidéo programmatique, motion, sous-titres, son | HeyGen (officiel), 2026-11-02, Apache-2.0 | garder, en coupant le chemin payant |
| 2 ★ | **frontend-design** | web design | Anthropic (officiel), v1.1.1, Apache-2.0 | garder |
| 3 ★ | **impeccable** | web design, critique et finition | pbakaus (communautaire, 58 contributeurs), 2026-11-01, Apache-2.0 | garder, sans les hooks |
| 4 ★ | **video-use** | montage conversationnel par EDL | browser-use, 2026-10-08, MIT | garder avec précaution (remplacer ElevenLabs Scribe) |
| 5 ★ | **marketingskills** (sélection : `copywriting`, `copy-editing`, `seo-audit`, `ai-seo`, `schema`, `cro`, `site-architecture`, `marketing-psychology`, `product-marketing`) | copywriting, SEO | coreyhaines31 (54 contributeurs), 2026-10-30, MIT | garder par sélection |
| 6 | **gsap-skills** (8 skills) | animation web | GreenSock/Webflow (officiel), 2026-04-21, MIT | garder |
| 7 | **emilkowalski/skills** (`emil-design-eng`, `animation-vocabulary`, `review-animations`…) | finition UI, easing, durées | emilkowalski (3 contributeurs), 2026-10-28, MIT | garder |
| 8 | **Skills Remotion** (`remotion-best-practices`, `remotion-markup`, `remotion-captions`, `remotion-render`, `remotion-create`, `remotion-studio`) | vidéo programmatique React | Remotion (officiel), 2026-10-26, pas de fichier LICENSE dans ce dépôt | garder (si Remotion est choisi comme moteur) |
| 9 | **web-quality-skills** (`accessibility`, `seo`, `core-web-vitals`) | accessibilité WCAG 2.2, performance | addyosmani (5 contributeurs), 2026-08-24, MIT | garder |
| 10 | **agentara/skills** (`video-plan`, `video-character-design`, `video-storyboard`) | agent réalisateur : plan, personnages, storyboard | agentara (4 auteurs), 2026-09-29, MIT | garder |
| 11 | **logo-design** | identité de marque, logos SVG | kaankiziltug (3 contributeurs), 2026-10-20, MIT | garder |
| 12 | **color-expert** | couleur : OKLCH, rampes, contraste APCA/WCAG | meodai, 2026-10-21, CC-BY-4.0 | garder |

Lecture de la liste :

- **Audio et image** : aucun skill de premier rang n'existe (§4). Les deux domaines sont couverts par du savoir-faire que nous écrirons nous-mêmes (§5) et par des outils, pas par des skills tiers.
- Les rangs 6 et 7 sont des compléments de la fiche web design ; le rang 8 est un équivalent de HyperFrames, à ne prendre que si Remotion est le moteur choisi (voir la note de licence ci-dessous).

### 1.1 Fiches

**1. HyperFrames — https://github.com/heygen-com/hyperframes** [LU]
- Créé le 2026-03-10, dernier commit 2026-11-02, 6 623 commits, 143 auteurs, ~77 k étoiles, Apache-2.0. Présent dans la marketplace officielle (`claude-plugins-official`, SHA épinglé).
- Ce qu'il fait : l'agent écrit des fichiers **HTML + GSAP** ; le moteur « cherche » une timeline en pause image par image, donc chaque rendu est identique ; le même fichier s'édite dans un Studio d'aperçu. Le routeur `hyperframes/SKILL.md` (7 Ko) fixe un contrat de 12 règles vérifiables (`npx hyperframes check --json` donne la ligne `Fix:`), plus ~110 Ko de références : sous-titres mot à mot, motion, son (mixage, ducking, SFX liés aux actions visibles), transcription, types de films (lancement, explicatif, musique, vertical, personnage). Autres skills : `hyperframes-cli`, `hyperframes-registry`, `media-use`, `slideshow`, `figma`, `remotion-to-hyperframes`, `reverse-any-video`.
- Pourquoi il est bon : contenu dense, précis, bouclé sur une vérification mécanique, sans remplissage. Il colle à la règle de la charte Nexora (texte et logo toujours posés en code, jamais générés). Signal de marché : **Magnific Move** (28/10/2026) fait du motion design conversationnel avec HyperFrames (voir `07-creative-vs-higgsfield-feuille-de-route.md`).
- Risques : tout passe par `npx hyperframes …` (code npm téléchargé à l'exécution) ; le rendu lance Chromium ; le dépôt pèse 338 Mo (les skills seuls : 4,4 Mo). **`media-use`** oriente fortement vers les crédits HeyGen payants (ligne relue : « ne remplace pas par du moins cher… ne dis jamais les prix »). Il existe des alternatives locales gratuites dans la même famille (transcription whisper ou Parakeet, TTS Kokoro, SFX Openverse). Une partie des références suppose le chemin du plugin ; non testé en autonome.
- Installation recommandée : les trois skills sans `media-use`.
  - Plugin officiel : `claude plugin install hyperframes@claude-plugins-official`
  - Manuelle épinglée : voir le script §3 (copie de `skills/{hyperframes,hyperframes-cli,hyperframes-registry}`).

**2. frontend-design — plugin officiel Anthropic** [LU, présent en local]
- v1.1.1, Apache-2.0, aucun script. Un seul `SKILL.md` de 71 lignes : plan de design avant le code (palette de 4 à 6 hex, typographie, plan de page), **auto-revue contre le brief**, liste des tics des pages générées (crème + serif + terracotta, noir + vert acide, cartes identiques, étiquettes en capitales…), plancher de qualité (responsive, focus clavier, `prefers-reduced-motion`, contraste).
- Pourquoi : le meilleur rapport valeur/risque de la liste. Équivalent exact de la méthode « charte avant code » de `marketing/nexora/DIRECTION-ARTISTIQUE.md`.
- Installation : `claude plugin install frontend-design@claude-plugins-official` (marketplace déjà présente) ou copie du dossier depuis `anthropics/skills` (§3).

**3. impeccable — https://github.com/pbakaus/impeccable** [LU]
- Créé le 2025-11-16, v4.8.0, 2,6 k commits, 58 contributeurs, ~100 k étoiles (non crédible telle quelle), Apache-2.0, dernier commit 2026-11-01.
- Un skill (`.claude/skills/impeccable/SKILL.md`) avec 24 commandes (`critique`, `audit`, `polish`, `bolder`, `quieter`, `typeset`, `harden`, `animate`, `onboard`, `shape`…) et des références chiffrées (`craft-floor.md` : contraste 4,5:1, mesure 65 à 75 caractères, interdits : étiquettes en capitales, numérotation 01/02 sans suite réelle, dégradé sur texte).
- Risques [LU] : le skill appelle `scripts/impeccable`, un lanceur shell qui **télécharge un binaire** dans `~/.impeccable/bin/` depuis les « releases » GitHub, vérifié par sha256 contre `engine-checksums.txt` ; l'installeur (`npx impeccable install`) propose des **hooks** (SessionStart, PostToolUse, Stop) qui analysent chaque fichier UI modifié ; le mode `live` exécute un script `package.json` optionnel. **Recommandation : copier le dossier du skill sans l'installeur (donc sans hooks)** ; le binaire ne se télécharge qu'au premier appel de commande.

**4. video-use — https://github.com/browser-use/video-use** [LU]
- Créé le 2026-04-11, dernier commit 2026-10-08, 23 commits, 9 auteurs, ~30 k étoiles (élevé pour 23 commits : suspect), MIT.
- `SKILL.md` de 26 Ko pour le montage par conversation. Chaîne : transcription **mot à mot** → `takes_packed.md` → **EDL JSON** → rendu ffmpeg par segment (extraction par segment puis concaténation sans perte, fondus audio de 30 ms à chaque raccord, sous-titres posés **en dernier**) → auto-évaluation limitée à 3 passes. Règles dures vérifiables : jamais de coupe dans un mot, marge de coupe de 30 à 200 ms, sous-titres recalés sur la sortie, `-14 LUFS / -1 dBTP`, sous-agent critique avant livraison.
- Défaut majeur : la transcription exige **ElevenLabs Scribe** (`ELEVENLABS_API_KEY`, service payant, audio envoyé chez un tiers) et le skill déconseille Whisper local. Nous avons déjà faster-whisper au mot (`app/server/nexora/transcrire.py`) : **remplacer l'étape de transcription** avant adoption. Il faut aussi `uv sync` (requests, librosa, matplotlib, pillow, numpy) et lier tout le dépôt (1,7 Mo).
- Valeur : la meilleure référence trouvée pour un montage par EDL ; ses règles dures sont extractibles en ~5 à 8 Ko (§6).

**5. marketingskills — https://github.com/coreyhaines31/marketingskills** [LU]
- Créé en janvier 2026, v2.14.0, 1,4 k commits, 54 contributeurs, ~58 k étoiles (suspect), MIT, dernier commit 2026-10-30. 53 skills en texte pur.
- `copywriting` (339 lignes, v2.3.2) : diagnostic de la situation d'abord, test à trois questions (image concrète, énoncé vérifiable, test du concurrent), interdit d'inventer chiffres, clients ou résultats, liste des tics d'écriture automatique. `seo-audit` (497 lignes) précise qu'un `curl` ne voit pas le balisage schema injecté en JavaScript et traite les pages récupérées comme des données non fiables.
- Limites : tout en anglais et orienté SaaS B2B (imposer le français et la voix Nexora via un fichier de contexte `.agents/product-marketing.md`, que le skill lit s'il existe) ; le dossier `tools/clis` contient des enveloppes de services tiers souvent payants (ne pas copier) ; le skill `image` n'est qu'un comparatif de modèles (inutile).
- À retenir seulement : `copywriting`, `copy-editing`, `seo-audit`, `ai-seo`, `schema`, `cro`, `site-architecture`, `marketing-psychology`, `product-marketing`.

**6. gsap-skills — https://github.com/greensock/gsap-skills** [LU]
- Officiel GreenSock, premier commit 2026-03-04, dernier **2026-04-21 (six mois sans commit)**, 24 commits, 5 auteurs, MIT. 8 skills en texte pur, sans script : `gsap-core` (15 Ko), `gsap-timeline`, `gsap-scrolltrigger` (18 Ko), `gsap-plugins` (22 Ko), `gsap-utils`, `gsap-react`, `gsap-frameworks`, `gsap-performance`. Les plugins premium sont gratuits avec `npm i gsap`.
- Exact et autonome ; biais d'éditeur assumé (« recommande GSAP par défaut »). HyperFrames repose sur GSAP : les deux se complètent.

**7. emilkowalski/skills — https://github.com/emilkowalski/skills** [LU PAR UN SOUS-AGENT]
- Créé en mars 2026, 58 commits, 3 contributeurs, ~53 k étoiles (suspect), MIT, dernier commit 2026-10-28. 16 skills de motion et de finition UI, texte pur. Le principal, `emil-design-eng` (674 lignes) : `ease-out` à l'entrée, courbes `cubic-bezier` données, durées, propriétés à animer, `reduced-motion` ; il corrige des erreurs courantes des agents. (`emilkowalski/skill`, au singulier, redirige vers `skills`.)

**8. Skills Remotion — https://github.com/remotion-dev/skills** [LU]
- Officiel Remotion, créé le 2026-01-19, dernier commit 2026-10-26, 93 commits, 2 auteurs, ~6,1 k étoiles. 12 skills : `remotion-markup` (13 Ko + ~35 fichiers de référence : timing, transitions, sous-titres, ffmpeg, détection de silence `loudnorm` puis `silencedetect`, voix off, effets, 3D, Lottie, flou de mouvement), `remotion-captions`, `remotion-render`, `remotion-studio`, `remotion-create`, etc. Contenu précis, versionné (4.0.539), prudent (ne rend pas sans demande).
- Défauts : `remotion-best-practices` embarque des copies de tous les autres (1,8 Mo, doublon) ; `remotion-docs` interroge Algolia (clé publique) ; la voix off suppose ElevenLabs ; `whisper-webgpu` exige un GPU compatible et **ne marche pas sur Linux arm64** ; certains SFX sont lus depuis `remotion.media`.
- **Pas de fichier LICENSE dans ce dépôt de skills.** Le produit Remotion a sa propre licence (le dépôt parent est `NOASSERTION` côté GitHub) ; le rapport 02 avait déjà mis Remotion de côté **pour le produit**. Pour des films maison, HyperFrames (Apache-2.0) est le choix le plus simple ; Remotion n'est utile que si l'on veut son écosystème React.

**9. web-quality-skills — https://github.com/addyosmani/web-quality-skills** [LU PAR UN SOUS-AGENT]
- Créé en janvier 2026, 34 commits, 5 contributeurs, ~3 k étoiles, MIT, dernier commit 2026-08-24. `accessibility` (464 lignes, WCAG 2.2) est fondé sur des preuves : audit Lighthouse, arbre d'accessibilité, test clavier ; il précise qu'un score de 100 n'équivaut pas à la conformité. Texte pur. `seo`, `performance`, `core-web-vitals` en complément léger.

**10. agentara/skills (`skills/aigc/video-plan`, `video-character-design`, `video-storyboard`) — https://github.com/agentara/skills** [LU]
- Créé le 2026-05-12, dernier commit 2026-09-29, 44 commits, 4 auteurs, ~622 étoiles, MIT. ~57 Ko au total, aucun script. Flux : spécification Markdown d'abord, **planche de personnage** générée après validation, planches `storyboard/scene-XX.png` et scripts de prompt vidéo `scene-XX.md`, avec cohérence des personnages par références d'images.
- Très proche du besoin de continuité de personnages ; il appelle un outil `image_gen` du client (à remplacer). Les dossiers voisins du dépôt (poster, 3D, etc.) ne servent pas.

**11. logo-design — https://github.com/kaankiziltug/logo-design-skill** [LU PAR UN SOUS-AGENT]
- Créé en septembre 2025, 25 commits, 3 contributeurs, ~5,8 k étoiles, MIT, dernier commit 2026-10-20. `skills/logo-design/SKILL.md` (223 lignes) : brief, concepts, SVG géométrique, tests (16 px, monochrome, flou), planches de présentation, export favicon/icônes ; répond dans la langue de l'utilisateur ; impose un point d'arrêt (montrer les concepts avant le kit complet). Scripts Python sans dépendance qui appellent `rsvg-convert`, `inkscape` ou Chrome ; aucun réseau relevé. Le dépôt embarque 14 Mo dont ~1 400 logos SVG de référence (ne copier que `skills/logo-design`).
- Rappel : le logo « N » de Nexora est fixé et ne doit pas être modifié ; ce skill sert à des marques de clients ou à des sous-marques.

**12. color-expert — https://github.com/meodai/skill.color-expert** [LU PAR UN SOUS-AGENT]
- Créé en mars 2026, 117 commits, ~631 étoiles, CC-BY-4.0, dernier commit 2026-10-21. `SKILL.md` de 321 lignes + 4 Mo de références : OKLCH, rampes, tokens, contraste APCA/WCAG, impression contre écran. Texte pur. C'est de la science de la couleur pour le design, **pas de l'étalonnage photo ou vidéo**.

## 2. Pistes lues mais non retenues dans la shortlist (à garder en lecture)

| Dépôt | Pourquoi seulement en lecture |
|---|---|
| calesthio/OpenMontage (AGPL-3.0, 500 commits, 80 auteurs, ~75 k étoiles suspectes) | La meilleure matière d'« agent réalisateur » trouvée : directeurs d'étape (idée, script, scène, assets, montage, publication), `creative/video-gen-prompting.md` (16,7 Ko, squelette Sujet/Mouvement/Scène/Spatial/Caméra), `sound-design.md`, `subtitle-sync.md`, protocole de points de contrôle, portes d'approbation humaine. **AGPL : idées seulement, rien ne se copie dans nos prompts** (règle déjà posée dans `ARCHITECTURE-NEXORA-CREATIVE.md` §1 : AGPL = idées seulement). Les skills vendorés `.agents/skills/` incluent le `media-use` HeyGen. |
| kangarooking/director-skills (MIT, ~257 étoiles, 10 commits) | Méthode sérieuse (références avec rôle explicite, un seul geste dominant par plan, texte et logos en post-production, ne jamais inventer de faits, journal de génération en CSV). Mais écrite pour Seedance, README en chinois ; `miora-video-studio` (37 Ko) lié à un outil tiers. Lire pour s'inspirer. |
| digitalsamba/claude-code-video-toolkit (MIT, 389 commits, 16 auteurs) | Seul son skill `ffmpeg` (13 Ko) vaut le détour ; le reste est lié à Modal/RunPod/ElevenLabs/upload YouTube. |
| aicontentskills/ai-video-storyboard-skill (sans licence, 2 commits) | SKILL.md de 7,8 Ko utile comme squelette (cadences par plateforme, couche de cohérence visuelle) ; trop jeune et sans licence. |
| different-ai/agent-bank, `video-subtitle-cutter` (MIT) | Procédure autonome de 16 Ko (Whisper local, détection de coupes, ré-encodage obligatoire, jamais `-c copy`) ; dépôt sans rapport avec la vidéo, frontmatter orienté opencode. À récupérer comme dossier seul si besoin. |
| CloudAI-X/threejs-skills (MIT, ~3,9 k étoiles) | 12 skills de 18 à 30 Ko calés sur three.js r186 ; volumineux, à charger par sujet seulement (shaders, post-traitement). |
| diffusionstudio/lottie, `text-to-lottie` (MIT) | Skill de 10 Ko, mais sa vérification passe par le lecteur Skottie du dépôt (bun) : pas autonome. |
| JosiahSiegel/claude-plugin-marketplace, `ffmpeg-core/ffmpeg-audio-processing` (MIT, 223 SKILL.md : production en série) | Contient une recette `loudnorm` en deux passes correcte, mais aussi des erreurs vérifiées (§4). À n'utiliser que comme matière brute. |
| AgriciDaniel/claude-seo (MIT, 26 sous-skills, hook PostToolUse) | Utile pour `hreflang` FR/EN ; scripts Python et hook qui s'exécute après chaque Edit/Write ; services payants en option. Après revue seulement. |
| Leonxlnx/taste-skill, nextlevelbuilder/ui-ux-pro-max-skill, alchaincyf/huashu-design | Fonctionnent, mais : Node 22 + Chrome local, palettes « par type de produit » génériques (à rebours d'une identité distinctive), skill en chinois avec BGM de provenance non vérifiée. |
| artokun/comfyui-mcp (MIT, ~884 étoiles) — MCP, pas un skill | Voie réaliste pour piloter ComfyUI (upscale, inpainting) depuis Claude Code ; lancé par `npx -y comfyui-mcp` (code npm exécuté). Chez nous, le serveur MCP d'OpenField (`app/mcp/server.ts`, 31 outils) fait déjà ce travail et passe par les licences. |
| elevenlabs/skills (MIT, ~529 étoiles) | Bonne documentation d'API (TTS fr, SFX, musique, doublage) mais **cloud payant** (`ELEVENLABS_API_KEY`) ; sans objet pour un studio qui veut des moteurs locaux. |

## 3. Script d'installation (NON EXÉCUTÉ) — portée utilisateur `~/.claude/skills/`

À lancer par une personne, après relecture. Chaque dépôt est récupéré **au commit relu** (`git fetch --depth 1 <url> <SHA complet>`), dans un dossier temporaire, puis seuls les sous-dossiers voulus sont copiés.

```bash
set -euo pipefail
SK="$HOME/.claude/skills"; mkdir -p "$SK"; T="$(mktemp -d)"
get() { git init -q "$3" && git -C "$3" fetch -q --depth 1 "$1" "$2" && git -C "$3" checkout -q FETCH_HEAD; }

# 1. HyperFrames (sans media-use : chemin payant HeyGen). Alternative officielle : claude plugin install hyperframes@claude-plugins-official
get https://github.com/heygen-com/hyperframes b1316e61d170d29067735150ebb5ab291e0f4171 "$T/hf"
cp -r "$T"/hf/skills/{hyperframes,hyperframes-cli,hyperframes-registry} "$SK"/

# 2. frontend-design : plugin officiel (la marketplace est déjà enregistrée)
claude plugin install frontend-design@claude-plugins-official
#    (ou, sans plugin : get https://github.com/anthropics/skills ca45fc496a3436251f191354091d557da31c15b5 "$T/as" && cp -r "$T/as/skills/frontend-design" "$SK"/)

# 3. impeccable : le dossier du skill seulement (PAS d'installeur, donc PAS de hooks)
get https://github.com/pbakaus/impeccable e89e3ada3e875a89ac2c5d33d11e65ebef6fe285 "$T/imp"
cp -r "$T/imp/.claude/skills/impeccable" "$SK"/

# 4. video-use : à adapter avant usage (remplacer ElevenLabs Scribe par faster-whisper au mot)
get https://github.com/browser-use/video-use 43cfc566833548093455c9d4a46bd69913b7e552 "$T/vu"
cp -r "$T/vu" "$SK/video-use" && rm -rf "$SK/video-use/.git"
#    puis, dans $SK/video-use : uv sync   (dépendances Python : requests, librosa, matplotlib, pillow, numpy)

# 5. marketingskills : sélection
get https://github.com/coreyhaines31/marketingskills 88c79f6528a9347420e57ceb1fff9a60de651768 "$T/mk"
for s in copywriting copy-editing seo-audit ai-seo schema cro site-architecture marketing-psychology product-marketing; do cp -r "$T/mk/skills/$s" "$SK"/; done

# 6. gsap-skills
get https://github.com/greensock/gsap-skills aed9cfd3277740755f6bfc1155c7aa645403b760 "$T/gs"
cp -r "$T"/gs/skills/gsap-* "$SK"/

# 7. emilkowalski/skills : le skill principal et les trois d'animation
get https://github.com/emilkowalski/skills a81dbca07f2217b7103e510c0f13f8d5b017afc9 "$T/ek"
for s in emil-design-eng animation-vocabulary review-animations improve-animations; do cp -r "$T/ek/skills/$s" "$SK"/; done

# 8. Remotion (seulement si Remotion est retenu) : alternative officielle documentée : npx skills add remotion-dev/skills
get https://github.com/remotion-dev/skills 30d4553ecd46fbc5212fd0ff006ae43af522158b "$T/rm"
for s in remotion-markup remotion-captions remotion-render remotion-create remotion-studio; do cp -r "$T/rm/skills/$s" "$SK"/; done

# 9. web-quality-skills
get https://github.com/addyosmani/web-quality-skills afa8da942115f2961fdbfa80807ea0b232ff6c00 "$T/wq"
cp -r "$T"/wq/skills/{accessibility,seo,core-web-vitals} "$SK"/

# 10. agentara (agent réalisateur)
get https://github.com/agentara/skills 950e1bfb11e1df67b46df19804ed85ada9012c33 "$T/ag"
cp -r "$T"/ag/skills/aigc/{video-plan,video-character-design,video-storyboard} "$SK"/

# 11. logo-design
get https://github.com/kaankiziltug/logo-design-skill 734090317a2155c5bf1ae8bd4cc85c6848a0128f "$T/ld"
cp -r "$T/ld/skills/logo-design" "$SK"/

# 12. color-expert (le SKILL.md est à la racine du dépôt)
get https://github.com/meodai/skill.color-expert 5bf7c7704d56bccc6aeea38c36bcf449abe56a6c "$T/ce"
mkdir -p "$SK/color-expert" && cp -r "$T"/ce/{SKILL.md,references} "$SK/color-expert"/
```

Remarques :

- Avant d'exécuter, vérifier que l'ordre de grandeur du nombre de skills chargés reste raisonnable : chaque skill ajoute sa description (une ligne) au contexte au démarrage ; ~50 skills dont certains à description longue pèsent. Installer d'abord les cinq étoilés.
- Le chemin `npx skills add <dépôt> -g -a claude-code` (outil `vercel-labs/skills`) est documenté par Remotion et HyperFrames et installe aussi dans `~/.claude/skills/`, mais il tire la dernière version, pas la version relue ; je ne l'ai pas utilisé.

## 4. Audio, image : pas de bon skill — ce qui existe réellement

### 4.1 Audio

Constat : **aucun skill n'est « bon » de bout en bout** pour le mixage, le mastering, la voix. Le meilleur contenu est dispersé en recettes ffmpeg.

Recette de loudness [VÉRIFIÉ ffmpeg 9.0.1, résultat −14,0 LUFS pour la cible web et −23,0 LUFS pour la cible EBU, pic sous le plafond] :

```
# Passe 1 : mesure
ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11:print_format=json -f null -
# Passe 2 : application linéaire avec les valeurs mesurées
ffmpeg -i in.wav -af "loudnorm=I=-14:TP=-1:LRA=11:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…:offset=…:linear=true" out.wav
# Contrôle
ffmpeg -i out.wav -af ebur128=peak=true -f null -
```

Cibles : web −14 LUFS / −1 dBTP ; broadcast EBU R128 −23 LUFS / −1 dBTP ; ATSC A/85 −24 LKFS / −2 dBTP ; podcast −16. Limite connue : `linear=true` ne s'applique que si le contenu respecte la plage LRA, sinon ffmpeg repasse en mode dynamique.

**Constat sur notre code** : `app/server/nexora/film.ts` (lignes 187–188) applique `loudnorm=I=-14:TP=-1:LRA=11` **en une seule passe** (mode dynamique) ; une passe de mesure puis `linear=true` donnerait un niveau exact et sans pompage. Petit gain, faible effort.

Candidats audio lus :

| Candidat | Verdict | Détail |
|---|---|---|
| JosiahSiegel `ffmpeg-audio-processing` (MIT, 59 étoiles, dernier commit 2026-06-18) | matière brute | Tableau des standards correct, deux passes avec `offset` + `linear=true` correct. **Erreurs vérifiées** : `deesser=i=0.4:f=4000:w=0.5` est invalide (`f` doit valoir entre 0 et 1) ; la « peak normalization » met deux `-af` sur la même commande (le second écrase le premier) ; la ligne rapide « EBU R128 » donne `TP=-2` au lieu de −1. |
| AgriciDaniel `video-audio` (MIT, 8 commits, à l'arrêt depuis 2026-04-06) | matière brute | loudnorm deux passes correct, limiteur `alimiter=limit=0.95:level=false` valide, ducking, `silencedetect`. Appelle `scripts/preflight.sh` ; l'installeur officiel est un `curl | bash` (à éviter). |
| bitwize-music-studio `mastering-engineer` / `mix-engineer` (CC0-1.0, 11 contributeurs, 908 commits, dernier 2026-10-13) | musique seulement | Flux pour musique générée (WAV, −14 LUFS / −1 dBTP) avec serveur MCP Python local (pyloudnorm, matchering, scipy, numpy, noisereduce) ; pas de réseau relevé ; limiteur true-peak non audité. Envisageable pour les musiques Music3. |
| elevenlabs/skills | hors sujet | cloud payant. |

À défaut de skill : `slhck/ffmpeg-normalize` (outil, presets `podcast`, `music`, `streaming-video`, v1.43.0, dernier commit 2026-10-14) et `pyloudnorm` (MIT) pour l'analyse. Pour la voix, `afftdn`/`anlmdn` de ffmpeg suffisent à un premier nettoyage ; DeepFilterNet est inactif depuis 2024.

### 4.2 Image

Constat : **aucun skill de qualité** pour le compositing, la retouche, l'upscaling, le détourage ou l'étalonnage photo. Les candidats sont soit des enveloppes autour d'API cloud payantes, soit des mémos génériques. Les seuls skills solides touchent à la marque et à la couleur (rangs 11 et 12), et à `canvas-design` / `theme-factory` d'Anthropic (officiels, sans réseau ; utiles pour des affiches et des thèmes de documents, pas pour de la retouche).

Rejetés avec leur raison : `inference-sh/skills image-upscaling` (la description annonce Real-ESRGAN, Thera, FLUX et Topaz mais le corps n'en liste qu'un, Topaz ; exige le CLI `belt` avec connexion) ; `fal-ai-community/skills` (cloud fal.ai, binaire installé par `curl | bash`, le `fal-upscale` des listes n'existe plus) ; `openai/skills imagegen` (conçu pour Codex, `OPENAI_API_KEY`) ; `oaustegard/claude-skills processing-images` (mémo ImageMagick/Pillow sans upscale, détourage ni étalonnage).

Outils à défaut (hors skills) : détourage `rembg` (MIT) ou BiRefNet (MIT) ; upscale Real-ESRGAN (BSD-3, figé depuis 2024) ou SeedVR2 ; retouche/compositing ImageMagick, Pillow, libvips ; étalonnage ffmpeg (`lut3d`, `eq`, `colorbalance`). Chez nous, ces moteurs passent par ComfyUI via les graphes d'OpenField (voir `07-creative-vs-higgsfield-feuille-de-route.md`).

## 5. Skills à écrire nous-mêmes (avec `anthropic-skills:skill-creator`)

La recherche montre trois trous où Nexora a déjà la matière :

1. **`nexora-audio-mix`** : la recette loudnorm deux passes ci-dessus, le mixage « bruitages H3 à −8 dB sous la musique, −14 LUFS » de `film.ts`, les règles de fondu de 30 ms de video-use (reprises en nos mots), ducking. Source : `app/server/nexora/film.ts` et ce rapport.
2. **`nexora-h3-prompting`** : le guide officiel MiniMax (`app/server/nexora/guides/`), les validateurs de `promptH3.ts`, les défauts connus (« champ inventé », enseigne inventée, remarques entre parenthèses). Aujourd'hui injecté dans le réécrivain ; un skill le rendrait aussi utilisable depuis Claude Code.
3. **`nexora-marque`** : `marketing/nexora/DIRECTION-ARTISTIQUE.md` (logo « N » jamais modifié, orange signal, Geist/Inter/JetBrains Mono, aucun robot, aucun chiffre ni client inventé, texte et logo toujours posés en code).
4. **`nexora-creative-mcp`** : comment piloter le studio depuis Claude Code via `app/mcp/server.ts` (31 outils), avec la liste des outils **bloqués par licence** (§6.1) pour qu'un agent externe ne les appelle pas.

## 6. Pour l'agent LLM à l'intérieur de Nexora Creative

### 6.1 Comment il est construit aujourd'hui (lu dans `app/server/`)

- **Ce n'est pas un agent à boucle d'outils.** C'est une série d'**appels uniques « chat/completions » par rôle** : `ClientLlm.completer(role, messages, {json, temperature, maxTokens})` dans `app/server/nexora/llm.ts` (96 lignes). Le client parle à une API compatible OpenAI (la passerelle Nexora `/v1` en production, LiteLLM/OpenRouter en développement ; modèle par rôle : `redaction`, `realisation`, `boost`, `musique`, `moderation`, `publication`, `idees`, `juge` (réservé), `assistant`). **Il n'y a pas de paramètre `tools` / appel de fonctions** dans `completer`.
- Chaque rôle a son prompt système écrit en dur dans un fichier TypeScript : `consignesSysteme()` dans `reecritureH3.ts` (le guide officiel MiniMax lu sur disque, `guides/VIDEO_PROMPT_WRITING_GUIDE_base_en.md`), `CONSIGNES` dans `film.ts` (Director : storyboard + bible de continuité), `SYSTEME_ASSISTANT` dans `studio.ts` (Mode Studio : demande française + résumé de la timeline en JSON → commandes de montage), `moderation.ts`, `musique.ts`, `publication.ts`, `reecritureImage.ts`.
- Principe constant : **le LLM propose, le code dispose** ; sorties JSON validées (Zod / validateurs déterministes), deux réparations, puis repli minimal toujours conforme. Les commandes du Mode Studio sont bornées (`COMMANDES`, `ACTIONS`, `MAX_COMMANDES = 200`).
- À côté : un **serveur MCP** (`app/mcp/server.ts`, stdio, 31 outils : `generate_video`, `direct_scene`, `upscale`, `speak`, `edit_image`…) qui fait piloter tout le studio par un agent externe (Claude Code, Cursor). Attention : il expose aussi des outils dont la licence est **bloquée** (`mirror_motion`, `reshoot`, `apply_effect`, `extend_video`, `make_transition`, `speak`, `add_sound`, `stage_render`, `finish_hdr`, `restyle_video`, `swap_object`) : ensembles LTX refusés par `app/server/nexora/licences.ts`.

### 6.2 Trois façons de lui donner un skill ou une procédure

| Voie | Principe | Quand | Coût |
|---|---|---|---|
| A. **Injection statique par rôle** | un dossier `app/server/nexora/competences/<nom>.md` (frontmatter `name`, `description`, `roles: [...]`, `jetons: n`) lu comme `guides/` l'est aujourd'hui ; un chargeur `competencesPour(role)` les ajoute au message `system` après les consignes existantes | procédures courtes et stables (règles de montage, style de copy, storyboard) | 2 à 8 k jetons par appel ; **stable donc cachable** (le catalogue Nexora porte déjà un tarif de lecture en cache) |
| B. **Divulgation progressive** | le prompt système ne porte que l'index (nom + description, une ligne par skill) ; un code déterministe (ou un premier appel bon marché au rôle `assistant`) choisit 0 à 2 skills à charger dans l'appel principal | beaucoup de skills, gros corpus | un appel de plus, mais prompt principal court |
| C. **Boucle d'outils** (vrai agent) | ajouter `tools` à `completer`, boucle bornée (nombre de tours, devis obligatoire avant dépense), les outils = les corps de `app/mcp/bodies.ts` ; les skills arrivent par A ou B | agent « Producteur » (`07-creative-vs-higgsfield-feuille-de-route.md`, item R10) | plus de développement ; indispensable pour une vraie conversation |

Recommandation : **A tout de suite** (quelques heures, déjà dans l'esprit du code), **B** quand il y a plus de ~8 skills, **C** avec l'agent Producteur. Dans tous les cas : un skill injecté est un **texte** ; il ne peut pas appeler de scripts (le serveur n'exécute rien de ce que le LLM écrit).

Précautions propres à Nexora :

- **Licence des textes injectés** : n'y mettre que des sources MIT, Apache-2.0, CC0 ou CC-BY (avec la mention requise, à consigner dans `THIRD_PARTY_NOTICES.md` du fork) ; **OpenMontage (AGPL-3.0) et tout texte sans licence** : lecture seule, on réécrit en nos mots.
- **Pas de contenu distant** : `vercel-labs/web-design-guidelines` récupère ses règles à chaque revue sur `raw.githubusercontent.com` ; ne jamais faire cela côté serveur.
- **Taille** : mesurer avec le validateur existant (`promptH3.test.ts` montre comment) ; plafonner le total à ~8 k jetons par rôle ; le prompt actuel du réécrivain H3 est déjà de 15 à 23 Ko.

### 6.3 Ce qui est injectable, rôle par rôle

| Rôle de `llm.ts` | Skill ou procédure | Source (licence) | Nature |
|---|---|---|---|
| `realisation` (Director, `film.ts`) | règles de plan/continuité : planche de personnage avant les plans, « un seul geste dominant par plan », texte et logos jamais générés, cadence ~5 s par plan | agentara `video-plan` / `video-storyboard` (MIT) ; idées de `kangarooking/director-skills` (MIT) ; OpenMontage (AGPL : idées seulement) | condenser en ~2 k jetons, en anglais comme le prompt actuel |
| `assistant` (Mode Studio, `studio.ts`) | règles dures du montage : jamais de coupe dans un mot, marge de coupe 30–200 ms, fondus de 30 ms aux raccords, sous-titres posés en dernier, niveau −14 LUFS / −1 dBTP ; styles de sous-titres | video-use (MIT) pour les règles ; `hyperframes/references/captions.md` et `sound.md` (Apache-2.0) | extraire ~5 à 8 k caractères ; les commandes restent bornées |
| `publication` | copywriting : test à trois questions, aucun chiffre ni client inventé, tics à éviter, adaptation par réseau | marketingskills `copywriting`, `copy-editing` (MIT) | condenser à ~60 lignes ; imposer le français et la voix Nexora |
| `redaction` (H3, image) | déjà alimenté par le guide MiniMax ; ajouter les défauts constatés (`nexora-h3-prompting`) | nos propres notes | inchangé |
| `musique` | structure (intro, montée, drop, outro), tempo, instruments | notre `musique.ts` + notes de rapport 11 | inchangé |
| `moderation`, `idees`, `boost` | rien à ajouter | — | — |
| `juge` (à construire) | grille de défauts (identité, artefacts, mouvement de caméra, synchro audio, texte à l'écran) | rapport 09 §2 rôle 6 + nos défauts réels | à écrire |

Ce qui **ne s'injecte pas** : HyperFrames (le contrat suppose le CLI `npx hyperframes check/snapshot/render` ; seules ses références `captions.md`, `sound.md`, `motion.md` sont de la connaissance réutilisable), impeccable (binaire, hooks), logo-design (scripts), claude-seo (scripts et réseau), bitwize (serveur MCP Python), comfyui-mcp (ComfyUI + GPU). Ces skills servent **Claude Code** (nous, pour produire des pièces), pas l'agent du serveur.

## 7. Ce que je n'ai pas pu vérifier

- Aucun skill n'a été **installé ni essayé** ; les commandes du §3 ne sont pas exécutées. Elles reposent sur la structure des dépôts relue le 02/11/2026.
- Les scripts Python et JS des dépôts n'ont pas été audités ligne à ligne (seuls `scripts/impeccable`, les `helpers/` de video-use et `plugin-cli.mjs` de HyperFrames ont été parcourus).
- Un sous-agent a signalé un `curl … | bash` d'installation du CLI `heygen` dans `media-use` ; **je ne l'ai pas retrouvé** à ma relecture des skills de HyperFrames (ce qui ne prouve rien pour d'autres versions). Raison de plus pour ne pas installer `media-use`.
- L'authenticité des étoiles, les issues et les contributeurs réels n'ont pas été vérifiés (limite de l'API GitHub : 60 requêtes par heure, partagée).
- Non examinés : `ComposioHQ/awesome-claude-skills`, `wshobson/agents`, `alirezarezvani/claude-skills` (clonés, non analysés) ; les skills Motion.dev et Rive (aucun skill officiel trouvé ; seulement des tiers non lus).
- La licence réelle du produit Remotion (au-delà d'une certaine taille d'entreprise) n'a pas été relue ici.
- Rien sur la qualité **à l'usage** : un skill bien écrit n'est pas un skill efficace ; le seul test honnête est un essai sur un vrai travail (par exemple la prochaine pièce de campagne), ce qui reste à faire après installation des cinq premiers.
