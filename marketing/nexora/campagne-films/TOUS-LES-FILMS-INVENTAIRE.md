> Copie texte du manifeste de `pc1:~/Bureau/Nexora-Livrables/TOUS-LES-FILMS/` (les vidéos elles-mêmes ne sont pas dans git). Le fichier CSV détaillé (sha256, emplacements) est sur pc1.

# TOUS LES FILMS Nexora : manifeste (03/11/2026)

Dossier : `/home/pc1/Bureau/Nexora-Livrables/TOUS-LES-FILMS/` sur pc1. **1389 vidéos uniques, 22.7 Go** (dédoublonnées par sha256 sur 5 machines : pc6, pc5 + archive, pc1, VM201, VM202), plus 96 fichiers tiers listés mais non copiés. Toutes les sommes sha256 ont été recalculées sur pc1 après copie : 0 écart.

Règles : copie seule (rien déplacé ni supprimé à la source). Les fichiers déjà présents sur pc1 dans le même disque (Codex OPSYS-AI du fondateur, livrables) sont des **liens physiques** (même données, nom en plus, 0 octet de plus) ; si un jour le dossier Codex est supprimé, la copie ici survit. Noms de fichiers conservés ; variantes 9:16, 1:1, fr/en conservées.

Colonnes de notes : « fondateur » = note donnée par le fondateur ; « agent » = auto-évaluation de l’agent ; vide = pas de note connue. « rôle » : master = rendu final haute qualité, web = ré-encodage léger, rush = plan/élément de travail, travail = itération intermédiaire.

## Arborescence

| Dossier | Vidéos uniques | Taille |
|---|---:|---:|
| `01-campagne-marque/boucles-ambiance/` | 10 | 168.4 Mo |
| `01-campagne-marque/finals/` | 25 | 1.65 Go |
| `01-campagne-marque/partage-web/` | 15 | 46.5 Mo |
| `01-campagne-marque/rushes-campagne/` | 141 | 194.8 Mo |
| `01-campagne-marque/stings/` | 18 | 75.8 Mo |
| `01-campagne-marque/teasers-produits/` | 48 | 715.4 Mo |
| `02-creative-promos/V1-bande-annonce/` | 2 | 53.9 Mo |
| `02-creative-promos/V2-bande-annonce-flotte-sabres/` | 3 | 36.4 Mo |
| `02-creative-promos/V3-bataille-spatiale/` | 30 | 150.0 Mo |
| `02-creative-promos/V4-une-phrase-un-film/` | 47 | 693.7 Mo |
| `02-creative-promos/apercus-app/` | 4 | 30.6 Mo |
| `02-creative-promos/rushes-V1-V2/` | 44 | 143.6 Mo |
| `03-heros-site/` | 17 | 271.8 Mo |
| `04-workstudio/` | 24 | 287.8 Mo |
| `05-surveillance/` | 65 | 801.0 Mo |
| `06-modeles-api/` | 24 | 313.4 Mo |
| `07-opsys-ai/codex-fondateur/` | 493 | 14.13 Go |
| `07-opsys-ai/nexora/` | 51 | 667.7 Mo |
| `08-tests-agents/Test-agents-9-premiers/` | 9 | 95.3 Mo |
| `08-tests-agents/Test2-12-films/` | 12 | 901.9 Mo |
| `08-tests-agents/Test2-plaques/` | 186 | 605.0 Mo |
| `08-tests-agents/divers/` | 1 | 0.0 Mo |
| `10-autres/` | 110 | 615.6 Mo |
| `11-publie-sur-le-site/` | 10 | 83.7 Mo |

`09-films-v5/` : réservé aux films V5 (agent en cours). Les fichiers de l’agent restent dans `films-v3/` et `Nexora-Livrables/films-v5/` de pc1 ; voir `09-films-v5/LISEZ-MOI.txt`.

`11-publie-sur-le-site/` : ce que le site sert ou a servi (volume Directus de la VM201 : toutes les versions téléversées, nommées date_heure UTC + nom, et dossier `medias-web`). Dossier ajouté au plan prévu.

## Inventaire détaillé

Les plans de travail (rushes) sont résumés par dossier ; le détail fichier par fichier de TOUT est dans `INVENTAIRE.csv`.


### 01-campagne-marque

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `01-campagne-marque/boucles-ambiance/ambiance-atelier-16x9-12s-symbole.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/ambiance-atelier-16x9-12s-symbole.mp4` | 6.1 Mo | 12.0 s | 1920x1080 | 2026-11-01 10:53 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/ambiance-atelier-16x9-12s.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/ambiance-atelier-16x9-12s.mp4` | 15.8 Mo | 12.0 s | 1920x1080 | 2026-11-01 10:51 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/ambiance-fleuve-16x9-12s-symbole.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/ambiance-fleuve-16x9-12s-symbole.mp4` | 10.3 Mo | 12.0 s | 1920x1080 | 2026-11-01 10:49 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/ambiance-fleuve-16x9-12s.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/ambiance-fleuve-16x9-12s.mp4` | 17.6 Mo | 12.0 s | 1920x1080 | 2026-11-01 10:47 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/ambiance-ville-16x9-12s-symbole.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/ambiance-ville-16x9-12s-symbole.mp4` | 7.5 Mo | 12.0 s | 1920x1080 | 2026-11-01 10:46 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/ambiance-ville-16x9-12s.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/ambiance-ville-16x9-12s.mp4` | 16.7 Mo | 12.0 s | 1920x1080 | 2026-11-01 10:46 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/boucle-aurore-16x9-20s-symbole.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/boucle-aurore-16x9-20s-symbole.mp4` | 15.0 Mo | 20.0 s | 1920x1080 | 2026-11-01 10:44 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/boucle-aurore-16x9-20s.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/boucle-aurore-16x9-20s.mp4` | 30.5 Mo | 20.0 s | 1920x1080 | 2026-11-01 10:40 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/boucle-aurore-9x16-20s-symbole.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/boucle-aurore-9x16-20s-symbole.mp4` | 17.1 Mo | 20.0 s | 1080x1920 | 2026-11-01 10:45 | Boucle d’ambiance | master |  |
| `01-campagne-marque/boucles-ambiance/boucle-aurore-9x16-20s.mp4` | `pc6:NC/marketing/nexora/video/teasers/boucles/final/boucle-aurore-9x16-20s.mp4` | 31.7 Mo | 20.0 s | 1080x1920 | 2026-11-01 10:45 | Boucle d’ambiance | master |  |
| `01-campagne-marque/finals/film-marque/film-marque-16x9-en.mp4` | `pc6:NC/marketing/nexora/video/final/film-marque-16x9-en.mp4` | 161.1 Mo | 1:00.0 | 1920x1080 | 2026-11-01 10:30 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/film-marque/film-marque-16x9-fr.mp4` | `pc6:NC/marketing/nexora/video/final/film-marque-16x9-fr.mp4` | 161.2 Mo | 1:00.0 | 1920x1080 | 2026-11-01 10:23 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/film-marque/film-marque-1x1-en.mp4` | `pc6:NC/marketing/nexora/video/final/film-marque-1x1-en.mp4` | 91.0 Mo | 1:00.0 | 1080x1080 | 2026-11-01 10:35 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/film-marque/film-marque-1x1-fr.mp4` | `pc6:NC/marketing/nexora/video/final/film-marque-1x1-fr.mp4` | 91.1 Mo | 1:00.0 | 1080x1080 | 2026-11-01 10:26 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/film-marque/film-marque-9x16-en.mp4` | `pc6:NC/marketing/nexora/video/final/film-marque-9x16-en.mp4` | 162.7 Mo | 1:00.0 | 1080x1920 | 2026-11-01 10:34 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/film-marque/film-marque-9x16-fr.mp4` | `pc6:NC/marketing/nexora/video/final/film-marque-9x16-fr.mp4` | 162.6 Mo | 1:00.0 | 1080x1920 | 2026-11-01 10:25 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-15s/spot-15s-16x9-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-15s-16x9-en.mp4` | 30.8 Mo | 15.0 s | 1920x1080 | 2026-11-01 10:53 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-15s/spot-15s-16x9-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-15s-16x9-fr.mp4` | 30.8 Mo | 15.0 s | 1920x1080 | 2026-11-01 10:49 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-15s/spot-15s-1x1-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-15s-1x1-en.mp4` | 18.1 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:54 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-15s/spot-15s-1x1-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-15s-1x1-fr.mp4` | 18.1 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:52 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-15s/spot-15s-9x16-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-15s-9x16-en.mp4` | 30.3 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:53 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-15s/spot-15s-9x16-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-15s-9x16-fr.mp4` | 30.3 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:51 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-16x9-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-16x9-en.mp4` | 82.6 Mo | 30.0 s | 1920x1080 | 2026-11-01 10:45 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-16x9-fr-apercu.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-16x9-fr-apercu.mp4` | 2.4 Mo | 30.0 s | 960x540 | 2026-11-01 10:18 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-16x9-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-16x9-fr.mp4` | 82.5 Mo | 30.0 s | 1920x1080 | 2026-11-01 10:38 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-1x1-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-1x1-en.mp4` | 47.7 Mo | 30.0 s | 1080x1080 | 2026-11-01 10:48 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-1x1-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-1x1-fr.mp4` | 47.8 Mo | 30.0 s | 1080x1080 | 2026-11-01 10:43 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-9x16-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-9x16-en.mp4` | 84.5 Mo | 30.0 s | 1080x1920 | 2026-11-01 10:46 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-30s/spot-30s-9x16-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-30s-9x16-fr.mp4` | 84.5 Mo | 30.0 s | 1080x1920 | 2026-11-01 10:41 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-6s/spot-6s-16x9-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-6s-16x9-en.mp4` | 43.4 Mo | 6.0 s | 1920x1080 | 2026-11-01 10:55 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-6s/spot-6s-16x9-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-6s-16x9-fr.mp4` | 43.4 Mo | 6.0 s | 1920x1080 | 2026-11-01 10:54 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-6s/spot-6s-1x1-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-6s-1x1-en.mp4` | 24.9 Mo | 6.0 s | 1080x1080 | 2026-11-01 10:56 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-6s/spot-6s-1x1-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-6s-1x1-fr.mp4` | 24.9 Mo | 6.0 s | 1080x1080 | 2026-11-01 10:55 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-6s/spot-6s-9x16-en.mp4` | `pc6:NC/marketing/nexora/video/final/spot-6s-9x16-en.mp4` | 46.5 Mo | 6.0 s | 1080x1920 | 2026-11-01 10:56 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/finals/spot-6s/spot-6s-9x16-fr.mp4` | `pc6:NC/marketing/nexora/video/final/spot-6s-9x16-fr.mp4` | 46.5 Mo | 6.0 s | 1080x1920 | 2026-11-01 10:55 | Film de campagne finalisé ; campagne de lancement 01/11 | master |  |
| `01-campagne-marque/partage-web/film-marque-16x9-en.mp4` | `pc6:NC/marketing/nexora/partage/video/film-marque-16x9-en.mp4` | 11.3 Mo | 1:00.0 | 1280x720 | 2026-11-01 11:01 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/film-marque-16x9-fr.mp4` | `pc6:NC/marketing/nexora/partage/video/film-marque-16x9-fr.mp4` | 11.3 Mo | 1:00.0 | 1280x720 | 2026-11-01 11:01 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/film-marque-9x16-fr.mp4` | `pc6:NC/marketing/nexora/partage/video/film-marque-9x16-fr.mp4` | 11.2 Mo | 1:00.0 | 720x1280 | 2026-11-01 11:01 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/spot-15s-9x16-fr.mp4` | `pc6:NC/marketing/nexora/partage/video/spot-15s-9x16-fr.mp4` | 1.1 Mo | 15.0 s | 720x1280 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/spot-30s-16x9-fr.mp4` | `pc6:NC/marketing/nexora/partage/video/spot-30s-16x9-fr.mp4` | 5.6 Mo | 30.0 s | 1280x720 | 2026-11-01 11:01 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/spot-6s-1x1-fr.mp4` | `pc6:NC/marketing/nexora/partage/video/spot-6s-1x1-fr.mp4` | 0.3 Mo | 6.0 s | 720x720 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/sting-nexora-16x9.mp4` | `pc6:NC/marketing/nexora/partage/video/sting-nexora-16x9.mp4` | 0.2 Mo | 4.6 s | 1280x720 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-bot-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-bot-fr-9x16.mp4` | 0.5 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-code-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-code-fr-9x16.mp4` | 0.8 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-creative-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-creative-fr-9x16.mp4` | 0.8 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-privacy-router-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-privacy-router-fr-9x16.mp4` | 0.7 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-rag-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-rag-fr-9x16.mp4` | 0.7 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-vps-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-vps-fr-9x16.mp4` | 0.7 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-webpilot-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-webpilot-fr-9x16.mp4` | 0.7 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/partage-web/teaser-workstudio-fr-9x16.mp4` | `pc6:NC/marketing/nexora/partage/video/teaser-workstudio-fr-9x16.mp4` | 0.7 Mo | 15.0 s | 540x960 | 2026-11-01 11:00 | Copie web légère (galerie privée de partage) | web |  |
| `01-campagne-marque/stings/barre-inferieure-16x9-en-CA-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/barre-inferieure-16x9-en-CA-alpha.mov` | 10.3 Mo | 5.0 s | 1920x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/barre-inferieure-16x9-fr-CA-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/barre-inferieure-16x9-fr-CA-alpha.mov` | 9.9 Mo | 5.0 s | 1920x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/barre-inferieure-1x1-en-CA-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/barre-inferieure-1x1-en-CA-alpha.mov` | 8.6 Mo | 5.0 s | 1080x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/barre-inferieure-1x1-fr-CA-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/barre-inferieure-1x1-fr-CA-alpha.mov` | 8.3 Mo | 5.0 s | 1080x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/barre-inferieure-9x16-en-CA-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/barre-inferieure-9x16-en-CA-alpha.mov` | 10.8 Mo | 5.0 s | 1080x1920 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/barre-inferieure-9x16-fr-CA-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/barre-inferieure-9x16-fr-CA-alpha.mov` | 10.4 Mo | 5.0 s | 1080x1920 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/sting-nexora-16x9-en-CA.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/sting-nexora-16x9-en-CA.mp4` | 0.6 Mo | 4.6 s | 1920x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/sting-nexora-16x9-fr-CA.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/sting-nexora-16x9-fr-CA.mp4` | 0.6 Mo | 4.6 s | 1920x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/sting-nexora-1x1-en-CA.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/sting-nexora-1x1-en-CA.mp4` | 0.5 Mo | 4.6 s | 1080x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/sting-nexora-1x1-fr-CA.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/sting-nexora-1x1-fr-CA.mp4` | 0.5 Mo | 4.6 s | 1080x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/sting-nexora-9x16-en-CA.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/sting-nexora-9x16-en-CA.mp4` | 0.6 Mo | 4.6 s | 1080x1920 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/sting-nexora-9x16-fr-CA.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/sting-nexora-9x16-fr-CA.mp4` | 0.6 Mo | 4.6 s | 1080x1920 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/transition-1s-16x9-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/transition-1s-16x9-alpha.mov` | 5.2 Mo | 1.0 s | 1920x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/transition-1s-16x9.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/transition-1s-16x9.mp4` | 0.2 Mo | 1.0 s | 1920x1080 | 2026-11-01 09:44 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/transition-1s-1x1-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/transition-1s-1x1-alpha.mov` | 3.0 Mo | 1.0 s | 1080x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/transition-1s-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/transition-1s-1x1.mp4` | 0.2 Mo | 1.0 s | 1080x1080 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/transition-1s-9x16-alpha.mov` | `pc6:NC/marketing/nexora/video/teasers/stings/final/transition-1s-9x16-alpha.mov` | 5.3 Mo | 1.0 s | 1080x1920 | 2026-11-01 09:43 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/stings/transition-1s-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/stings/final/transition-1s-9x16.mp4` | 0.2 Mo | 1.0 s | 1080x1920 | 2026-11-01 09:44 | Sting sonore et visuel (alpha) | master |  |
| `01-campagne-marque/teasers-produits/bot/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/bot/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/bot/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/bot/sources/carte-en.mp4`<br>+2 | 0.8 Mo | 5.5 s | 1080x1920 | 2026-11-01 10:31 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/bot/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/bot/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/bot/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/bot/sources/carte-fr.mp4`<br>+2 | 0.8 Mo | 5.5 s | 1080x1920 | 2026-11-01 10:27 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/bot/teaser-bot-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/bot/final/teaser-bot-en-CA-1x1.mp4` | 20.1 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:53 | Teaser de 15 s bot | master |  |
| `01-campagne-marque/teasers-produits/bot/teaser-bot-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/bot/final/teaser-bot-en-CA-9x16.mp4` | 32.1 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:51 | Teaser de 15 s bot | master |  |
| `01-campagne-marque/teasers-produits/bot/teaser-bot-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/bot/final/teaser-bot-fr-CA-1x1.mp4` | 20.0 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s bot | master |  |
| `01-campagne-marque/teasers-produits/bot/teaser-bot-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/bot/final/teaser-bot-fr-CA-9x16.mp4` | 32.3 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s bot | master |  |
| `01-campagne-marque/teasers-produits/code/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/code/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/code/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/code/sources/carte-en.mp4`<br>+2 | 0.8 Mo | 5.6 s | 1080x1920 | 2026-11-01 10:31 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/code/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/code/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/code/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/code/sources/carte-fr.mp4`<br>+2 | 0.9 Mo | 5.6 s | 1080x1920 | 2026-11-01 10:27 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/code/teaser-code-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/code/final/teaser-code-en-CA-1x1.mp4` | 10.9 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:53 | Teaser de 15 s code | master |  |
| `01-campagne-marque/teasers-produits/code/teaser-code-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/code/final/teaser-code-en-CA-9x16.mp4` | 19.2 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:51 | Teaser de 15 s code | master |  |
| `01-campagne-marque/teasers-produits/code/teaser-code-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/code/final/teaser-code-fr-CA-1x1.mp4` | 10.9 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s code | master |  |
| `01-campagne-marque/teasers-produits/code/teaser-code-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/code/final/teaser-code-fr-CA-9x16.mp4` | 19.2 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s code | master |  |
| `01-campagne-marque/teasers-produits/creative/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/creative/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/creative/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/creative/sources/carte-en.mp4`<br>+2 | 0.9 Mo | 5.7 s | 1080x1920 | 2026-11-01 10:31 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/creative/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/creative/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/creative/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/creative/sources/carte-fr.mp4`<br>+2 | 0.9 Mo | 5.7 s | 1080x1920 | 2026-11-01 10:27 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/creative/teaser-creative-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/creative/final/teaser-creative-en-CA-1x1.mp4` | 17.0 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:52 | Teaser de 15 s creative | master |  |
| `01-campagne-marque/teasers-produits/creative/teaser-creative-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/creative/final/teaser-creative-en-CA-9x16.mp4` | 30.2 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:51 | Teaser de 15 s creative | master |  |
| `01-campagne-marque/teasers-produits/creative/teaser-creative-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/creative/final/teaser-creative-fr-CA-1x1.mp4` | 17.0 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s creative | master |  |
| `01-campagne-marque/teasers-produits/creative/teaser-creative-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/creative/final/teaser-creative-fr-CA-9x16.mp4` | 30.1 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s creative | master |  |
| `01-campagne-marque/teasers-produits/privacy-router/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/privacy-router/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/privacy-router/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/privacy-router/sources/carte-en.mp4`<br>+2 | 0.9 Mo | 5.8 s | 1080x1920 | 2026-11-01 09:52 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/privacy-router/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/privacy-router/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/privacy-router/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/privacy-router/sources/carte-fr.mp4`<br>+2 | 0.9 Mo | 5.6 s | 1080x1920 | 2026-11-01 10:27 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/privacy-router/teaser-privacy-router-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/privacy-router/final/teaser-privacy-router-en-CA-1x1.mp4` | 18.1 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:53 | Teaser de 15 s privacy-router | master |  |
| `01-campagne-marque/teasers-produits/privacy-router/teaser-privacy-router-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/privacy-router/final/teaser-privacy-router-en-CA-9x16.mp4` | 31.6 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:52 | Teaser de 15 s privacy-router | master |  |
| `01-campagne-marque/teasers-produits/privacy-router/teaser-privacy-router-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/privacy-router/final/teaser-privacy-router-fr-CA-1x1.mp4` | 18.1 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s privacy-router | master |  |
| `01-campagne-marque/teasers-produits/privacy-router/teaser-privacy-router-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/privacy-router/final/teaser-privacy-router-fr-CA-9x16.mp4` | 31.6 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s privacy-router | master |  |
| `01-campagne-marque/teasers-produits/rag/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/rag/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/rag/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/rag/sources/carte-en.mp4`<br>+2 | 0.8 Mo | 5.2 s | 1080x1920 | 2026-11-01 10:31 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/rag/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/rag/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/rag/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/rag/sources/carte-fr.mp4`<br>+2 | 0.8 Mo | 5.2 s | 1080x1920 | 2026-11-01 10:27 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/rag/teaser-rag-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/rag/final/teaser-rag-en-CA-1x1.mp4` | 11.5 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:52 | Teaser de 15 s rag | master |  |
| `01-campagne-marque/teasers-produits/rag/teaser-rag-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/rag/final/teaser-rag-en-CA-9x16.mp4` | 19.0 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:51 | Teaser de 15 s rag | master |  |
| `01-campagne-marque/teasers-produits/rag/teaser-rag-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/rag/final/teaser-rag-fr-CA-1x1.mp4` | 11.4 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s rag | master |  |
| `01-campagne-marque/teasers-produits/rag/teaser-rag-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/rag/final/teaser-rag-fr-CA-9x16.mp4` | 18.9 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s rag | master |  |
| `01-campagne-marque/teasers-produits/vps/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/vps/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/vps/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/vps/sources/carte-en.mp4`<br>+2 | 0.8 Mo | 5.2 s | 1080x1920 | 2026-11-01 10:42 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/vps/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/vps/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/vps/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/vps/sources/carte-fr.mp4`<br>+2 | 0.8 Mo | 5.2 s | 1080x1920 | 2026-11-01 10:37 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/vps/teaser-vps-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/vps/final/teaser-vps-en-CA-1x1.mp4` | 14.7 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:53 | Teaser de 15 s vps | master |  |
| `01-campagne-marque/teasers-produits/vps/teaser-vps-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/vps/final/teaser-vps-en-CA-9x16.mp4` | 27.8 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:52 | Teaser de 15 s vps | master |  |
| `01-campagne-marque/teasers-produits/vps/teaser-vps-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/vps/final/teaser-vps-fr-CA-1x1.mp4` | 14.6 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s vps | master |  |
| `01-campagne-marque/teasers-produits/vps/teaser-vps-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/vps/final/teaser-vps-fr-CA-9x16.mp4` | 27.8 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s vps | master |  |
| `01-campagne-marque/teasers-produits/webpilot/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/webpilot/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/webpilot/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/webpilot/sources/carte-en.mp4`<br>+2 | 0.9 Mo | 5.8 s | 1080x1920 | 2026-11-01 10:31 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/webpilot/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/webpilot/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/webpilot/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/webpilot/sources/carte-fr.mp4`<br>+2 | 0.9 Mo | 5.8 s | 1080x1920 | 2026-11-01 10:27 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/webpilot/teaser-webpilot-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/webpilot/final/teaser-webpilot-en-CA-1x1.mp4` | 20.4 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:52 | Teaser de 15 s webpilot | master |  |
| `01-campagne-marque/teasers-produits/webpilot/teaser-webpilot-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/webpilot/final/teaser-webpilot-en-CA-9x16.mp4` | 37.3 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:51 | Teaser de 15 s webpilot | master |  |
| `01-campagne-marque/teasers-produits/webpilot/teaser-webpilot-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/webpilot/final/teaser-webpilot-fr-CA-1x1.mp4` | 20.3 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s webpilot | master |  |
| `01-campagne-marque/teasers-produits/webpilot/teaser-webpilot-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/webpilot/final/teaser-webpilot-fr-CA-9x16.mp4` | 37.0 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:48 | Teaser de 15 s webpilot | master |  |
| `01-campagne-marque/teasers-produits/workstudio/cartons/carte-en.mp4` | `pc6:NC/marketing/nexora/video/teasers/workstudio/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/workstudio/sources/carte-en.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/workstudio/sources/carte-en.mp4`<br>+2 | 0.9 Mo | 5.8 s | 1080x1920 | 2026-11-01 10:30 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/workstudio/cartons/carte-fr.mp4` | `pc6:NC/marketing/nexora/video/teasers/workstudio/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-memoire/marketing/nexora/video/teasers/workstudio/sources/carte-fr.mp4`<br>`pc6:/home/pc6/Desktop/NexoraCreative-montage/marketing/nexora/video/teasers/workstudio/sources/carte-fr.mp4`<br>+2 | 0.9 Mo | 5.8 s | 1080x1920 | 2026-11-01 09:39 | Carton de teaser |  |  |
| `01-campagne-marque/teasers-produits/workstudio/teaser-workstudio-en-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/workstudio/final/teaser-workstudio-en-CA-1x1.mp4` | 16.6 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:53 | Teaser de 15 s workstudio | master |  |
| `01-campagne-marque/teasers-produits/workstudio/teaser-workstudio-en-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/workstudio/final/teaser-workstudio-en-CA-9x16.mp4` | 24.6 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:52 | Teaser de 15 s workstudio | master |  |
| `01-campagne-marque/teasers-produits/workstudio/teaser-workstudio-fr-CA-1x1.mp4` | `pc6:NC/marketing/nexora/video/teasers/workstudio/final/teaser-workstudio-fr-CA-1x1.mp4` | 16.6 Mo | 15.0 s | 1080x1080 | 2026-11-01 10:50 | Teaser de 15 s workstudio | master |  |
| `01-campagne-marque/teasers-produits/workstudio/teaser-workstudio-fr-CA-9x16.mp4` | `pc6:NC/marketing/nexora/video/teasers/workstudio/final/teaser-workstudio-fr-CA-9x16.mp4` | 24.6 Mo | 15.0 s | 1080x1920 | 2026-11-01 10:49 | Teaser de 15 s workstudio | master |  |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `01-campagne-marque/rushes-campagne/cartons/` | 19 | 11.6 Mo | 2:31.9 | Rush / plan source de la campagne (H3 rapide) |
| `01-campagne-marque/rushes-campagne/essais/` | 2 | 1.7 Mo | 16.9 s | Essai de carton (code) |
| `01-campagne-marque/rushes-campagne/plans/` | 1 | 1.7 Mo | 5.2 s | Rush / plan source de la campagne (H3 rapide) |
| `01-campagne-marque/rushes-campagne/plans-rapide/` | 32 | 52.5 Mo | 2:45.4 | Rush / plan source de la campagne (H3 rapide) |
| `01-campagne-marque/rushes-campagne/plans-vertical/` | 24 | 38.4 Mo | 2:04.1 | Rush / plan source de la campagne (H3 rapide) |
| `01-campagne-marque/rushes-campagne/teasers/` | 63 | 88.9 Mo | 6:35.0 | Rush / plan source de la campagne (H3 rapide) |

### 02-creative-promos

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `02-creative-promos/V1-bande-annonce/Nexora-Creative-bande-annonce-16x9.mp4` | `pc6:NC/marketing/creative/video/Nexora-Creative-bande-annonce-16x9.mp4` | 29.8 Mo | 1:00.0 | 1920x1080 | 2026-10-31 06:02 | Bande-annonce V1 (plans H3 calés sur la musique MiniMax Music 3 b89), master 1080p ; V1 (31/10 06:02) | master |  |
| `02-creative-promos/V1-bande-annonce/Nexora-Creative-bande-annonce-9x16.mp4` | `pc6:NC/marketing/creative/video/Nexora-Creative-bande-annonce-9x16.mp4` | 24.1 Mo | 1:00.0 | 1080x1920 | 2026-10-31 06:02 | Bande-annonce V1 (plans H3 calés sur la musique MiniMax Music 3 b89), master 1080p ; V1 (31/10 06:02) | master |  |
| `02-creative-promos/V2-bande-annonce-flotte-sabres/copies-web/promo-web-720.mp4` | `pc5 (archive):A5/promo/montage/promo-web-720.mp4`<br>`pc6:NC/marketing/creative/site/promo.mp4`<br>`pc6:D6/promo/montage/promo-web-720.mp4` | 11.9 Mo | 1:00.0 | 1280x720 | 2026-10-31 07:51 | Copie web 720p de la bande-annonce V2 (aussi publiée sur la fiche Creative du site, supprimée du dépôt NexoraSite le 02/11) ; V2 (31/10) | web |  |
| `02-creative-promos/V2-bande-annonce-flotte-sabres/copies-web/site-creative-promo.mp4` (+ alias : `11-publie-sur-le-site/medias-web/site-creative-promo.mp4`, `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0603_site-creative-promo.mp4`) | `VM201:/srv/nexora/medias/web/site-creative-promo.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/2b828d5e-8253-4122-8ab6-89b3788fb1e4.mp4`<br>`pc6:D6/site-medias-web/site-creative-promo.mp4` | 13.4 Mo | 1:00.0 | 1280x720 | 2026-11-02 00:47 | Bande-annonce V2 re-encodée 720p, publiée sur le site (volume Directus 02/11) ; V2 | web | publié sur le site |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-16x9-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-16x9-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-16x9-en-15.mp4` | 19.1 Mo | 15.6 s | 1920x1080 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-16x9-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-16x9-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-16x9-en-30.mp4` | 36.1 Mo | 28.2 s | 1920x1080 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-16x9-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-16x9-en.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-16x9-en.mp4` | 76.9 Mo | 59.5 s | 1920x1080 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-16x9-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-16x9-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-16x9-fr-15.mp4` | 19.1 Mo | 15.6 s | 1920x1080 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-16x9-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-16x9-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-16x9-fr-30.mp4` | 36.2 Mo | 28.2 s | 1920x1080 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-16x9-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-16x9-fr.mp4` | 77.0 Mo | 59.5 s | 1920x1080 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-9x16-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-9x16-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-9x16-en-15.mp4` | 19.7 Mo | 15.6 s | 1080x1920 | 2026-11-02 05:46 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-9x16-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-9x16-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-9x16-en-30.mp4` | 36.0 Mo | 28.2 s | 1080x1920 | 2026-11-02 05:46 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-9x16-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-9x16-en.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-9x16-en.mp4` | 77.8 Mo | 59.5 s | 1080x1920 | 2026-11-02 05:46 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-9x16-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-9x16-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-9x16-fr-15.mp4` | 19.6 Mo | 15.6 s | 1080x1920 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-9x16-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-9x16-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-9x16-fr-30.mp4` | 36.0 Mo | 28.2 s | 1080x1920 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/Nexora-Creative-promo-V4-9x16-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Creative-promo-V4-9x16-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-Creative-promo-V4-9x16-fr.mp4` | 77.5 Mo | 59.5 s | 1080x1920 | 2026-11-02 05:45 | Promo V4 « Une phrase. Un film. » ; V4 (02/11) | master | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/copies-web-site/film-creative-16x9-en.mp4` | `pc6:D6/site-medias/film-creative-16x9-en.mp4` | 15.2 Mo | 59.5 s | 1920x1080 | 2026-11-02 05:45 | Film Creative publié sur le site (copie web) ; V4 | web | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/copies-web-site/film-creative-16x9-fr.mp4` | `pc6:D6/site-medias/film-creative-16x9-fr.mp4` | 15.1 Mo | 59.5 s | 1920x1080 | 2026-11-02 05:45 | Film Creative publié sur le site (copie web) ; V4 | web | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/copies-web-site/film-creative-9x16-en.mp4` | `pc6:D6/site-medias/film-creative-9x16-en.mp4` | 14.7 Mo | 59.5 s | 1080x1920 | 2026-11-02 05:46 | Film Creative publié sur le site (copie web) ; V4 | web | 6,5/10 (fondateur) |
| `02-creative-promos/V4-une-phrase-un-film/copies-web-site/film-creative-9x16-fr.mp4` | `pc6:D6/site-medias/film-creative-9x16-fr.mp4` | 14.6 Mo | 59.5 s | 1080x1920 | 2026-11-02 05:46 | Film Creative publié sur le site (copie web) ; V4 | web | 6,5/10 (fondateur) |
| `02-creative-promos/apercus-app/cafe-vertical.mp4` | `VM202:/srv/creative/data/rendus/OpenField/Publicit_pour_un_caf_glac_gouttes_au_ralenti_lumire_d_230008202.mp4`<br>`pc5 (archive):A5/output/video/OpenField_00001_.mp4`<br>`pc5 (archive):A5/rendus/OpenField/Publicit_pour_un_caf_glac_gouttes_au_ralenti_lumire_d_230008202.mp4`<br>+1 | 1.2 Mo | 5.2 s | 480x832 | 2026-10-30 22:33 | Aperçu produit de l’app Nexora Creative ; apercu | master |  |
| `02-creative-promos/apercus-app/film-crimson-rising.mp4` | `VM202:/srv/creative/data/rendus/films/film_2_1793415078920.mp4`<br>`pc5 (archive):A5/rendus/films/film_2_1793415078920.mp4`<br>`pc6:D6/apercus/film-crimson-rising.mp4` | 13.7 Mo | 41.0 s | 832x480 | 2026-10-30 22:51 | Aperçu produit de l’app Nexora Creative ; apercu | master |  |
| `02-creative-promos/apercus-app/film-metamorphose-pluie.mp4` | `VM202:/srv/creative/data/rendus/films/film_14_1793415988322.mp4`<br>`pc5 (archive):A5/rendus/films/film_14_1793415988322.mp4`<br>`pc6:D6/apercus/film-metamorphose-pluie.mp4` | 11.5 Mo | 20.5 s | 832x480 | 2026-10-30 23:06 | Aperçu produit de l’app Nexora Creative ; apercu | master |  |
| `02-creative-promos/apercus-app/robot-qualite-max.mp4` | `VM202:/srv/creative/data/rendus/OpenField/Ma_voiture_rouge_se_transforme_en_robot_gant_pendant_que_la_486010313.mp4`<br>`pc5 (archive):A5/output/video/OpenField_00016_.mp4`<br>`pc5 (archive):A5/rendus/OpenField/Ma_voiture_rouge_se_transforme_en_robot_gant_pendant_que_la_486010313.mp4`<br>+1 | 4.2 Mo | 5.2 s | 1344x768 | 2026-10-30 23:23 | Aperçu produit de l’app Nexora Creative ; apercu | master |  |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `02-creative-promos/V2-bande-annonce-flotte-sabres/essais/` | 1 | 11.1 Mo | 6.0 s | Essai de sound design (sfx synthétisés) |
| `02-creative-promos/V3-bataille-spatiale/comparaison-variantes-H3/` | 3 | 16.4 Mo | 15.5 s | Ronde de comparaison H3 (même prompt, graine 7777) (H3 officiel / FastH3 / PRISM) |
| `02-creative-promos/V3-bataille-spatiale/rushes-plans-H3/` | 27 | 133.6 Mo | 2:19.6 | Rush H3 de la promo V3 bataille spatiale (plan p01-orbite-nuit-v) (H3 officiel ref2va / FastH3 / 10Eros-Max × Singularity) |
| `02-creative-promos/V4-une-phrase-un-film/rushes-hero/` | 12 | 23.6 Mo | 1:22.1 | Rush de la V4 (H3 (FastH3 / PRISM)) |
| `02-creative-promos/V4-une-phrase-un-film/rushes-plans/` | 19 | 79.5 Mo | 1:38.2 | Rush H3 de la V4 (genre ville) (H3 (FastH3 / PRISM)) |
| `02-creative-promos/rushes-V1-V2/banc-moteurs/` | 1 | 4.6 Mo | 5.2 s | Banc comparatif de moteurs H3 (dragon/karaté) (H3 officiel / Singularity / FastH3) |
| `02-creative-promos/rushes-V1-V2/cartons/` | 13 | 1.5 Mo | 48.7 s | Carton de texte posé en code (code (libass)) |
| `02-creative-promos/rushes-V1-V2/plans-H3/` | 11 | 71.3 Mo | 56.9 s | Rush H3 de la bande-annonce (plan p01) (H3 (GB10 FastH3 ou 5090)) |
| `02-creative-promos/rushes-V1-V2/sorties-pc1-et-pc5/` | 19 | 66.3 Mo | 1:38.1 | Premiers essais H3 (banc, intention) (H3) |

### 03-heros-site

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `03-heros-site/autres-site-medias/site-film-marque-en.mp4` (+ alias : `11-publie-sur-le-site/medias-web/site-film-marque-en.mp4`, `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0603_site-film-marque-en.mp4`) | `VM201:/srv/nexora/medias/web/site-film-marque-en.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/ef4cf967-89ca-43c6-b177-2c3660be8172.mp4`<br>`pc6:D6/site-medias-web/site-film-marque-en.mp4` | 15.2 Mo | 1:00.0 | 1920x1080 | 2026-11-02 00:47 | Média du site | web | publié sur le site |
| `03-heros-site/autres-site-medias/site-film-marque-fr.mp4` (+ alias : `11-publie-sur-le-site/medias-web/site-film-marque-fr.mp4`, `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0603_site-film-marque-fr.mp4`) | `VM201:/srv/nexora/medias/web/site-film-marque-fr.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/2eb0012a-4fb6-48bd-a52c-6263fed5caca.mp4`<br>`pc6:D6/site-medias-web/site-film-marque-fr.mp4` | 15.4 Mo | 1:00.0 | 1920x1080 | 2026-11-02 00:47 | Média du site | web | publié sur le site |
| `03-heros-site/boucles-hero/masters/hero-boucle-16x9-master.mp4` | `pc6:D6/site-medias/masters/hero-boucle-16x9-master.mp4` | 88.8 Mo | 12.0 s | 1920x1080 | 2026-11-02 00:38 | Boucle hero du site ; hero v2/v3 (02/11) | master |  |
| `03-heros-site/boucles-hero/masters/hero-boucle-9x16-master.mp4` | `pc6:D6/site-medias/masters/hero-boucle-9x16-master.mp4` | 91.6 Mo | 12.0 s | 1080x1920 | 2026-11-02 01:52 | Boucle hero du site ; hero v2/v3 (02/11) | master |  |
| `03-heros-site/boucles-hero/web/hero-boucle-16x9.mp4` (+ alias : `11-publie-sur-le-site/medias-web/site-hero-boucle.mp4`, `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0853_site-hero-boucle.mp4`) | `VM201:/srv/nexora/medias/web/site-hero-boucle.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/43c2f566-3998-4ab9-a0ef-6f1c6f9d161a.mp4`<br>`pc6:D6/site-medias-web/site-hero-boucle.mp4`<br>+1 | 5.3 Mo | 18.2 s | 1920x1080 | 2026-11-02 03:49 | Boucle hero du site ; hero v2/v3 (02/11) | web | publié sur le site |
| `03-heros-site/boucles-hero/web/hero-boucle-16x9.webm` | `pc6:D6/site-medias/hero-boucle-16x9.webm` | 6.9 Mo |  |  | 2026-11-02 03:50 | Boucle hero du site ; hero v2/v3 (02/11) | web |  |
| `03-heros-site/boucles-hero/web/hero-boucle-9x16.mp4` | `pc6:D6/site-medias/hero-boucle-9x16.mp4` | 5.1 Mo | 18.2 s | 1080x1920 | 2026-11-02 03:50 | Boucle hero du site ; hero v2/v3 (02/11) | web |  |
| `03-heros-site/boucles-hero/web/hero-boucle-9x16.webm` | `pc6:D6/site-medias/hero-boucle-9x16.webm` | 6.6 Mo |  |  | 2026-11-02 03:52 | Boucle hero du site ; hero v2/v3 (02/11) | web |  |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `03-heros-site/rushes-plans/hero/` | 4 | 25.5 Mo | 29.2 s | Plan H3 du hero (allée d’entrepôt) (H3) |
| `03-heros-site/rushes-plans/reception/` | 5 | 11.3 Mo | 25.9 s | Plan H3 « réception » (H3) |

### 04-workstudio

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `04-workstudio/copies-web-site/film-workstudio-16x9-en-15.mp4` | `pc6:D6/site-medias/film-workstudio-16x9-en-15.mp4` | 2.0 Mo | 15.5 s | 1920x1080 | 2026-11-02 16:48 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-16x9-en-30.mp4` | `pc6:D6/site-medias/film-workstudio-16x9-en-30.mp4` | 4.4 Mo | 29.9 s | 1920x1080 | 2026-11-02 16:48 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-16x9-en.mp4` | `pc6:D6/site-medias/film-workstudio-16x9-en.mp4` | 6.5 Mo | 46.7 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-16x9-fr-15.mp4` | `pc6:D6/site-medias/film-workstudio-16x9-fr-15.mp4` | 2.0 Mo | 15.5 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-16x9-fr-30.mp4` | `pc6:D6/site-medias/film-workstudio-16x9-fr-30.mp4` | 4.6 Mo | 29.9 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-16x9-fr.mp4` | `pc6:D6/site-medias/film-workstudio-16x9-fr.mp4` | 6.8 Mo | 46.7 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-9x16-en-15.mp4` | `pc6:D6/site-medias/film-workstudio-9x16-en-15.mp4` | 1.6 Mo | 15.5 s | 1080x1920 | 2026-11-02 16:49 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-9x16-en-30.mp4` | `pc6:D6/site-medias/film-workstudio-9x16-en-30.mp4` | 3.6 Mo | 29.9 s | 1080x1920 | 2026-11-02 16:49 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-9x16-en.mp4` | `pc6:D6/site-medias/film-workstudio-9x16-en.mp4` | 5.4 Mo | 46.7 s | 1080x1920 | 2026-11-02 16:49 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-9x16-fr-15.mp4` | `pc6:D6/site-medias/film-workstudio-9x16-fr-15.mp4` | 1.6 Mo | 15.5 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-9x16-fr-30.mp4` | `pc6:D6/site-medias/film-workstudio-9x16-fr-30.mp4` | 3.7 Mo | 29.9 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/copies-web-site/film-workstudio-9x16-fr.mp4` | `pc6:D6/site-medias/film-workstudio-9x16-fr.mp4` | 5.5 Mo | 46.7 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio (copie web / formats courts) ; v2 | web |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-16x9-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-16x9-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-16x9-en-15.mp4` | 9.6 Mo | 15.5 s | 1920x1080 | 2026-11-02 16:48 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-16x9-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-16x9-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-16x9-en-30.mp4` | 21.7 Mo | 29.9 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-16x9-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-16x9-en.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-16x9-en.mp4` | 31.3 Mo | 46.7 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-16x9-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-16x9-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-16x9-fr-15.mp4` | 9.9 Mo | 15.5 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-16x9-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-16x9-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-16x9-fr-30.mp4` | 22.3 Mo | 29.9 s | 1920x1080 | 2026-11-02 16:47 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-16x9-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-16x9-fr.mp4` | 32.8 Mo | 46.7 s | 1920x1080 | 2026-11-02 16:46 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-9x16-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-9x16-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-9x16-en-15.mp4` | 8.4 Mo | 15.5 s | 1080x1920 | 2026-11-02 16:49 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-9x16-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-9x16-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-9x16-en-30.mp4` | 18.9 Mo | 29.9 s | 1080x1920 | 2026-11-02 16:49 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-9x16-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-9x16-en.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-9x16-en.mp4` | 28.1 Mo | 46.7 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-9x16-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-9x16-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-9x16-fr-15.mp4` | 8.7 Mo | 15.5 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-9x16-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-9x16-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-9x16-fr-30.mp4` | 19.4 Mo | 29.9 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |
| `04-workstudio/v2/Nexora-WorkStudio-film-9x16-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-WorkStudio-film-9x16-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-WorkStudio-film-9x16-fr.mp4` | 28.9 Mo | 46.7 s | 1080x1920 | 2026-11-02 16:48 | Film WorkStudio v2 (cycle réel complet) ; v2 | master |  |

### 05-surveillance

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `05-surveillance/v1/copies-web-site/film-surveillance-en-16x9.mp4` | `pc6:D6/site-medias/film-surveillance-en-16x9.mp4` | 22.5 Mo | 40.5 s | 1920x1080 | 2026-11-02 03:06 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-en-16x9.webm` | `pc6:D6/site-medias/film-surveillance-en-16x9.webm` | 8.5 Mo |  |  | 2026-11-02 03:09 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-en-9x16.mp4` | `pc6:D6/site-medias/film-surveillance-en-9x16.mp4` | 15.0 Mo | 40.5 s | 1080x1920 | 2026-11-02 03:16 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-en-9x16.webm` | `pc6:D6/site-medias/film-surveillance-en-9x16.webm` | 9.4 Mo |  |  | 2026-11-02 03:22 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-fr-16x9.mp4` | `pc6:D6/site-medias/charge/film-surveillance-fr-16x9.mp4`<br>`pc6:D6/site-medias/film-surveillance-fr-16x9.mp4` | 22.4 Mo | 40.5 s | 1920x1080 | 2026-11-02 03:01 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-fr-16x9.webm` | `pc6:D6/site-medias/film-surveillance-fr-16x9.webm` | 8.5 Mo |  |  | 2026-11-02 03:05 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-fr-9x16.mp4` | `pc6:D6/site-medias/film-surveillance-fr-9x16.mp4` | 15.0 Mo | 40.5 s | 1080x1920 | 2026-11-02 03:11 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/film-surveillance-fr-9x16.webm` | `pc6:D6/site-medias/film-surveillance-fr-9x16.webm` | 9.5 Mo |  |  | 2026-11-02 03:14 | Film Surveillance IA v1 ; v1 | web |  |
| `05-surveillance/v1/copies-web-site/site-film-surveillance-fr.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0842_site-film-surveillance-fr.mp4`) | `VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/1e4787e7-e887-4386-8702-e3783c15f534.mp4`<br>`pc6:D6/site-medias-web/site-film-surveillance-fr.mp4` | 10.4 Mo | 40.5 s | 1920x1080 | 2026-11-02 03:42 | Film Surveillance IA v1 ; v1 | web | publié sur le site |
| `05-surveillance/v1/copies-web-site/site-film-surveillance.mp4` (+ alias : `11-publie-sur-le-site/medias-web/site-film-surveillance.mp4`, `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0842_site-film-surveillance-en.mp4`) | `VM201:/srv/nexora/medias/web/site-film-surveillance.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/04333770-3a02-4fa9-a363-276e99c95758.mp4`<br>`pc6:D6/site-medias-web/site-film-surveillance-en.mp4`<br>+1 | 10.3 Mo | 40.5 s | 1920x1080 | 2026-11-02 03:40 | Film Surveillance IA v1 ; v1 | web | publié sur le site |
| `05-surveillance/v1/masters/film-surveillance-en-16x9-master.mp4` | `pc6:D6/site-medias/masters/film-surveillance-en-16x9-master.mp4` | 46.9 Mo | 40.5 s | 1920x1080 | 2026-11-02 03:06 | Film Surveillance IA v1 ; v1 | master |  |
| `05-surveillance/v1/masters/film-surveillance-en-9x16-master.mp4` | `pc6:D6/site-medias/masters/film-surveillance-en-9x16-master.mp4` | 47.0 Mo | 40.5 s | 1080x1920 | 2026-11-02 03:15 | Film Surveillance IA v1 ; v1 | master |  |
| `05-surveillance/v1/masters/film-surveillance-fr-16x9-master.mp4` | `pc6:D6/site-medias/masters/film-surveillance-fr-16x9-master.mp4` | 46.8 Mo | 40.5 s | 1920x1080 | 2026-11-02 02:59 | Film Surveillance IA v1 ; v1 | master |  |
| `05-surveillance/v1/masters/film-surveillance-fr-9x16-master.mp4` | `pc6:D6/site-medias/masters/film-surveillance-fr-9x16-master.mp4` | 46.8 Mo | 40.5 s | 1080x1920 | 2026-11-02 03:10 | Film Surveillance IA v1 ; v1 | master |  |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-16x9-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-16x9-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-16x9-en-15.mp4` | 13.1 Mo | 14.9 s | 1920x1080 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-16x9-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-16x9-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-16x9-en-30.mp4` | 31.9 Mo | 29.1 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-16x9-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-16x9-en.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-16x9-en.mp4` | 37.6 Mo | 33.3 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-16x9-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-16x9-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-16x9-fr-15.mp4` | 13.0 Mo | 14.9 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-16x9-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-16x9-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-16x9-fr-30.mp4` | 32.0 Mo | 29.1 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-16x9-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-16x9-fr.mp4` | 37.7 Mo | 33.3 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-9x16-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-9x16-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-9x16-en-15.mp4` | 14.2 Mo | 14.9 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-9x16-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-9x16-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-9x16-en-30.mp4` | 35.3 Mo | 29.1 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-9x16-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-9x16-en.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-9x16-en.mp4` | 41.1 Mo | 33.3 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-9x16-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-9x16-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-9x16-fr-15.mp4` | 14.3 Mo | 14.9 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-9x16-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-9x16-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-9x16-fr-30.mp4` | 35.4 Mo | 29.1 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/Nexora-Surveillance-IA-v2-9x16-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Surveillance-IA-v2-9x16-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-Surveillance-IA-v2-9x16-fr.mp4` | 41.2 Mo | 33.3 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 ; v2 | master | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-16x9-en-15.mp4` | `pc6:D6/site-medias/film-surveillance-v2-16x9-en-15.mp4` | 3.3 Mo | 14.9 s | 1920x1080 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-16x9-en-30.mp4` | `pc6:D6/site-medias/film-surveillance-v2-16x9-en-30.mp4` | 7.2 Mo | 29.1 s | 1920x1080 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-16x9-en.mp4` | `pc6:D6/site-medias/film-surveillance-v2-16x9-en.mp4` | 8.7 Mo | 33.3 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-16x9-fr-15.mp4` | `pc6:D6/site-medias/film-surveillance-v2-16x9-fr-15.mp4` | 3.3 Mo | 14.9 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-16x9-fr-30.mp4` | `pc6:D6/site-medias/film-surveillance-v2-16x9-fr-30.mp4` | 7.3 Mo | 29.1 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-16x9-fr.mp4` | `pc6:D6/site-medias/film-surveillance-v2-16x9-fr.mp4` | 8.7 Mo | 33.3 s | 1920x1080 | 2026-11-02 16:05 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-9x16-en-15.mp4` | `pc6:D6/site-medias/film-surveillance-v2-9x16-en-15.mp4` | 3.6 Mo | 14.9 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-9x16-en-30.mp4` | `pc6:D6/site-medias/film-surveillance-v2-9x16-en-30.mp4` | 7.5 Mo | 29.1 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-9x16-en.mp4` | `pc6:D6/site-medias/film-surveillance-v2-9x16-en.mp4` | 8.9 Mo | 33.3 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-9x16-fr-15.mp4` | `pc6:D6/site-medias/film-surveillance-v2-9x16-fr-15.mp4` | 3.5 Mo | 14.9 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-9x16-fr-30.mp4` | `pc6:D6/site-medias/film-surveillance-v2-9x16-fr-30.mp4` | 7.4 Mo | 29.1 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |
| `05-surveillance/v2/copies-web-site/film-surveillance-v2-9x16-fr.mp4` | `pc6:D6/site-medias/film-surveillance-v2-9x16-fr.mp4` | 8.7 Mo | 33.3 s | 1080x1920 | 2026-11-02 16:06 | Film Surveillance IA v2 (copie web / formats courts) ; v2 | web | 7,6 (agent) |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `05-surveillance/cartons/` | 5 | 4.1 Mo | 1:02.5 | Carton du film Surveillance (code) |
| `05-surveillance/rushes-plans-v1/` | 22 | 53.0 Mo | 1:53.7 | Plan H3 du film Surveillance (v1) (H3) |

### 06-modeles-api

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `06-modeles-api/Nexora-Modeles-et-API-film-16x9-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-16x9-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-16x9-en-15.mp4` | 12.6 Mo | 15.0 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-16x9-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-16x9-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-16x9-en-30.mp4` | 24.5 Mo | 29.5 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-16x9-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-16x9-en.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-16x9-en.mp4` | 30.6 Mo | 35.6 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-16x9-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-16x9-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-16x9-fr-15.mp4` | 12.2 Mo | 15.0 s | 1920x1080 | 2026-11-02 20:30 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-16x9-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-16x9-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-16x9-fr-30.mp4` | 23.8 Mo | 29.5 s | 1920x1080 | 2026-11-02 20:30 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-16x9-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-16x9-fr.mp4` | 27.9 Mo | 35.6 s | 1920x1080 | 2026-11-02 20:30 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-9x16-en-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-9x16-en-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-9x16-en-15.mp4` | 11.3 Mo | 15.0 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-9x16-en-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-9x16-en-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-9x16-en-30.mp4` | 23.8 Mo | 29.5 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-9x16-en.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-9x16-en.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-9x16-en.mp4` | 28.7 Mo | 35.6 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-9x16-fr-15.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-9x16-fr-15.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-9x16-fr-15.mp4` | 10.9 Mo | 15.0 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-9x16-fr-30.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-9x16-fr-30.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-9x16-fr-30.mp4` | 22.6 Mo | 29.5 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/Nexora-Modeles-et-API-film-9x16-fr.mp4` | `pc5 (archive):A5/promo/montage/Nexora-Modeles-et-API-film-9x16-fr.mp4`<br>`pc6:D6/promo/montage/Nexora-Modeles-et-API-film-9x16-fr.mp4` | 26.9 Mo | 35.6 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API ; v1 | master | 7,1 (agent) |
| `06-modeles-api/copies-web-site/film-modeles-16x9-en-15.mp4` | `pc6:D6/site-medias/film-modeles-16x9-en-15.mp4` | 2.8 Mo | 15.0 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-16x9-en-30.mp4` | `pc6:D6/site-medias/film-modeles-16x9-en-30.mp4` | 5.6 Mo | 29.5 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-16x9-en.mp4` | `pc6:D6/site-medias/film-modeles-16x9-en.mp4` | 6.8 Mo | 35.6 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-16x9-fr-15.mp4` | `pc6:D6/site-medias/film-modeles-16x9-fr-15.mp4` | 2.8 Mo | 15.0 s | 1920x1080 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-16x9-fr-30.mp4` | `pc6:D6/site-medias/film-modeles-16x9-fr-30.mp4` | 5.5 Mo | 29.5 s | 1920x1080 | 2026-11-02 20:30 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-16x9-fr.mp4` | `pc6:D6/site-medias/film-modeles-16x9-fr.mp4` | 6.5 Mo | 35.6 s | 1920x1080 | 2026-11-02 20:30 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-9x16-en-15.mp4` | `pc6:D6/site-medias/film-modeles-9x16-en-15.mp4` | 2.5 Mo | 15.0 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-9x16-en-30.mp4` | `pc6:D6/site-medias/film-modeles-9x16-en-30.mp4` | 5.3 Mo | 29.5 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-9x16-en.mp4` | `pc6:D6/site-medias/film-modeles-9x16-en.mp4` | 6.2 Mo | 35.6 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-9x16-fr-15.mp4` | `pc6:D6/site-medias/film-modeles-9x16-fr-15.mp4` | 2.4 Mo | 15.0 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-9x16-fr-30.mp4` | `pc6:D6/site-medias/film-modeles-9x16-fr-30.mp4` | 5.0 Mo | 29.5 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |
| `06-modeles-api/copies-web-site/film-modeles-9x16-fr.mp4` | `pc6:D6/site-medias/film-modeles-9x16-fr.mp4` | 6.0 Mo | 35.6 s | 1080x1920 | 2026-11-02 20:31 | Film Modèles et API (copie web / formats courts) ; v1 | web | 7,1 (agent), non publié à l’origine |

### 07-opsys-ai

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `07-opsys-ai/codex-fondateur/bureau-versions/video-opsys-a-revoir.mp4` | `pc1:/home/pc1/Bureau/video-opsys-a-revoir.mp4`<br>`pc1:OPS/exports/brochure20261027/OPSYS-AI-film-revision-r3.mp4` | 38.2 Mo | 1:15.0 | 1920x1080 | 2026-10-27 23:34 | Version de la vidéo OPSYS-AI du fondateur (projet Codex) | master |  |
| `07-opsys-ai/codex-fondateur/bureau-versions/video-opsys-avant-grok45-94c0f7538ab9.mp4` | `pc1:/home/pc1/Bureau/OPSYS-AI-versions/video-opsys-avant-grok45-94c0f7538ab9.mp4`<br>`pc1:OPS/exports/grok20261028/OPSYS-AI-Grok-45s-r1.mp4` | 85.8 Mo | 45.0 s | 1920x1080 | 2026-10-28 21:52 | Version de la vidéo OPSYS-AI du fondateur (projet Codex) | master |  |
| `07-opsys-ai/codex-fondateur/bureau-versions/video-opsys-avant-grok45-e7917f8bed90.mp4` | `pc1:/home/pc1/Bureau/OPSYS-AI-versions/video-opsys-avant-grok45-e7917f8bed90.mp4`<br>`pc1:OPS/exports/vfx20261028/OPSYS-AI-film-VFX-r3.mp4` | 64.9 Mo | 1:15.0 | 1920x1080 | 2026-10-28 02:36 | Version de la vidéo OPSYS-AI du fondateur (projet Codex) | master |  |
| `07-opsys-ai/codex-fondateur/bureau-versions/video-opsys-avant-vfx.mp4` (+ alias : `11-publie-sur-le-site/medias-web/video-opsys.mp4`, `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0603_video-opsys.mp4`) | `VM201:/srv/nexora/medias/web/video-opsys.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/bfeb4ff4-f5b7-4196-999e-b6621b2548ea.mp4`<br>`pc1:/home/pc1/Bureau/OPSYS-AI-versions-precedentes/video-opsys-avant-vfx.mp4`<br>+2 | 26.1 Mo | 1:15.0 | 1920x1080 | 2026-10-25 23:57 | Version de la vidéo OPSYS-AI du fondateur (projet Codex) | master | publié sur le site |
| `07-opsys-ai/codex-fondateur/bureau-versions/video-opsys.mp4` | `pc1:/home/pc1/Bureau/video-opsys.mp4`<br>`pc1:OPS/exports/grok20261028/OPSYS-AI-Grok-45s-r2.mp4`<br>`pc6:D6/work/opsys-pc1/films/OPSYS-AI-Grok-45s-master.mp4` | 84.6 Mo | 45.0 s | 1920x1080 | 2026-10-28 22:04 | Version de la vidéo OPSYS-AI du fondateur (projet Codex) | master |  |
| `07-opsys-ai/codex-fondateur/exports-brand75/OPSYS-AI-marque-75s-master-r1-supersede.mov` | `pc1:OPS/exports/brand75/OPSYS-AI-marque-75s-master-r1-supersede.mov` | 1.55 Go | 1:15.0 | 1920x1080 | 2026-10-25 21:57 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-brand75/OPSYS-AI-marque-75s-master-r2-supersede.mov` | `pc1:OPS/exports/brand75/OPSYS-AI-marque-75s-master-r2-supersede.mov` | 1.55 Go | 1:15.0 | 1920x1080 | 2026-10-25 22:05 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-brand75/OPSYS-AI-marque-75s-master-r4-avant-mention.mov` | `pc1:OPS/exports/brand75/OPSYS-AI-marque-75s-master-r4-avant-mention.mov` | 1.55 Go | 1:15.0 | 1920x1080 | 2026-10-25 23:54 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-brand75/OPSYS-AI-marque-75s-master.mov` | `pc1:OPS/exports/brand75/OPSYS-AI-marque-75s-master.mov` | 1.56 Go | 1:15.0 | 1920x1080 | 2026-10-25 23:57 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-brochure20261027/OPSYS-AI-revue-gmail-1080p.mp4` | `pc1:OPS/exports/brochure20261027/OPSYS-AI-revue-gmail-1080p.mp4` | 15.7 Mo | 1:15.0 | 1920x1080 | 2026-10-28 01:10 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM01-REVUE-r15-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM01-REVUE-r15-1080p.mp4` | 54.4 Mo | 1:15.0 | 1920x1080 | 2026-10-30 23:03 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM02-REVUE-r2-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM02-REVUE-r2-1080p.mp4` | 49.7 Mo | 1:15.0 | 1920x1080 | 2026-10-30 23:13 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM03-REVUE-r3-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM03-REVUE-r3-1080p.mp4` | 52.5 Mo | 1:15.0 | 1920x1080 | 2026-10-30 23:18 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM03-SYNC-r1-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM03-SYNC-r1-1080p.mp4` | 53.0 Mo | 1:15.0 | 1920x1080 | 2026-10-31 01:15 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM04-RAPPEL-r1-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM04-RAPPEL-r1-1080p.mp4` | 72.5 Mo | 1:15.0 | 1920x1080 | 2026-10-31 01:23 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM04-REVUE-r12-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM04-REVUE-r12-1080p.mp4` | 71.1 Mo | 1:15.0 | 1920x1080 | 2026-10-30 23:23 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM05-REVUE-1080p-r18.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM05-REVUE-1080p-r18.mp4` | 46.9 Mo | 1:15.0 | 1920x1080 | 2026-10-30 17:01 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM06-DISTINCT-r1-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM06-DISTINCT-r1-1080p.mp4` | 52.4 Mo | 1:15.0 | 1920x1080 | 2026-10-31 00:49 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM06-REVUE-1080p-r10.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM06-REVUE-1080p-r10.mp4` | 61.7 Mo | 1:15.0 | 1920x1080 | 2026-10-30 18:38 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM06-REVUE-1080p-r13.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM06-REVUE-1080p-r13.mp4`<br>`pc6:D6/work/opsys-pc1/films/FILM06-REVUE-1080p-r13.mp4` | 65.3 Mo | 1:15.0 | 1920x1080 | 2026-10-30 18:46 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM07-RAPPEL-r1-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM07-RAPPEL-r1-1080p.mp4` | 51.9 Mo | 1:15.0 | 1920x1080 | 2026-10-31 00:42 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM07-REVUE-r12-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM07-REVUE-r12-1080p.mp4` | 55.8 Mo | 1:15.0 | 1920x1080 | 2026-10-30 22:49 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM08-DISTINCT-r1-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM08-DISTINCT-r1-1080p.mp4` | 53.6 Mo | 1:15.0 | 1920x1080 | 2026-10-31 00:47 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/FILM08-REVUE-r6-1080p.mp4` | `pc1:OPS/exports/minimax-h3-20261029/FILM08-REVUE-r6-1080p.mp4`<br>`pc6:D6/work/opsys-pc1/films/FILM08-REVUE-r6-1080p.mp4` | 57.2 Mo | 1:15.0 | 1920x1080 | 2026-10-30 23:07 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-racine/OPSYS-AI-master-animatique-72s.mov` | `pc1:OPS/exports/OPSYS-AI-master-animatique-72s.mov` | 532.8 Mo | 1:12.0 | 1920x1080 | 2026-10-24 21:15 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-racine/OPSYS-AI-revue-master-72s.mov` | `pc1:OPS/exports/OPSYS-AI-revue-master-72s.mov` | 1.00 Go | 1:12.0 | 1920x1080 | 2026-10-25 04:20 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/codex-fondateur/exports-vfx20261028/OPSYS-AI-VFX-gmail-r3-1080p.mp4` | `pc1:OPS/exports/vfx20261028/OPSYS-AI-VFX-gmail-r3-1080p.mp4`<br>`pc6:D6/work/opsys-pc1/films/OPSYS-AI-VFX-r3-1080p.mp4` | 15.8 Mo | 1:15.0 | 1920x1080 | 2026-10-28 15:48 | Film / rush OPSYS-AI du projet Codex du fondateur | master |  |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-16x9-en-15.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-16x9-en-15.mp4` | 14.4 Mo | 14.9 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-16x9-en-30.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-16x9-en-30.mp4` | 21.5 Mo | 27.1 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-16x9-en.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-16x9-en.mp4` | 72.4 Mo | 1:14.0 | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-16x9-fr-15.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-16x9-fr-15.mp4` | 14.4 Mo | 14.9 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-16x9-fr-30.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-16x9-fr-30.mp4` | 21.7 Mo | 27.1 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-16x9-fr.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-16x9-fr.mp4` | 72.0 Mo | 1:13.8 | 1920x1080 | 2026-11-02 21:57 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-9x16-en-15.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-9x16-en-15.mp4` | 16.7 Mo | 14.9 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-9x16-en-30.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-9x16-en-30.mp4` | 24.3 Mo | 27.1 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-9x16-en.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-9x16-en.mp4` | 82.1 Mo | 1:14.0 | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-9x16-fr-15.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-9x16-fr-15.mp4` | 17.0 Mo | 14.9 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-9x16-fr-30.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-9x16-fr-30.mp4` | 24.9 Mo | 27.1 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/Nexora-OPSYS-AI-9x16-fr.mp4` | `pc6:D6/promo/montage/Nexora-OPSYS-AI-9x16-fr.mp4` | 82.1 Mo | 1:14.0 | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI « Ils travaillent. Vous vivez. » ; v1 | master | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-16x9-en-15.mp4` | `pc6:D6/site-medias/film-opsys-16x9-en-15.mp4` | 3.4 Mo | 14.9 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-16x9-en-30.mp4` | `pc6:D6/site-medias/film-opsys-16x9-en-30.mp4` | 5.5 Mo | 27.1 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-16x9-en.mp4` | `pc6:D6/site-medias/film-opsys-16x9-en.mp4` | 17.0 Mo | 1:14.0 | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-16x9-fr-15.mp4` | `pc6:D6/site-medias/film-opsys-16x9-fr-15.mp4` | 3.4 Mo | 14.9 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-16x9-fr-30.mp4` | `pc6:D6/site-medias/film-opsys-16x9-fr-30.mp4` | 5.7 Mo | 27.1 s | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-16x9-fr.mp4` | `pc6:D6/site-medias/film-opsys-16x9-fr.mp4` | 17.0 Mo | 1:13.8 | 1920x1080 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-9x16-en-15.mp4` | `pc6:D6/site-medias/film-opsys-9x16-en-15.mp4` | 3.2 Mo | 14.9 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-9x16-en-30.mp4` | `pc6:D6/site-medias/film-opsys-9x16-en-30.mp4` | 5.5 Mo | 27.1 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-9x16-en.mp4` | `pc6:D6/site-medias/film-opsys-9x16-en.mp4` | 17.1 Mo | 1:14.0 | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-9x16-fr-15.mp4` | `pc6:D6/site-medias/film-opsys-9x16-fr-15.mp4` | 3.3 Mo | 14.9 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-9x16-fr-30.mp4` | `pc6:D6/site-medias/film-opsys-9x16-fr-30.mp4` | 5.5 Mo | 27.1 s | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |
| `07-opsys-ai/nexora/copies-web-site/film-opsys-9x16-fr.mp4` | `pc6:D6/site-medias/film-opsys-9x16-fr.mp4` | 17.1 Mo | 1:14.0 | 1080x1920 | 2026-11-02 21:58 | Film OPSYS-AI (copie web / formats courts) ; v1 | web | 7,1/10 |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `07-opsys-ai/codex-fondateur/exports-brand75/` | 7 | 159.7 Mo | 8:45.1 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/exports-brochure20261027/` | 3 | 47.1 Mo | 3:45.0 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/exports-grok20261028/` | 2 | 28.8 Mo | 1:30.0 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/exports-minimax-h3-itérations/` | 202 | 3.54 Go | 159:25.0 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/exports-racine/` | 7 | 78.3 Mo | 5:20.1 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/exports-vfx20261028/` | 2 | 127.4 Mo | 2:30.0 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/reprise-revues-20261030/` | 6 | 130.5 Mo | 7:30.1 | Revue de reprise des films OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-evidence-brand75/` | 1 | 2.0 Mo | 6.0 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-film01/` | 13 | 31.3 Mo | 1:07.2 | Rush H3 du projet OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-film02/` | 6 | 12.5 Mo | 31.0 s | Rush H3 du projet OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-film03/` | 8 | 18.9 Mo | 41.4 s | Rush H3 du projet OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-film04/` | 1 | 3.7 Mo | 5.2 s | Rush H3 du projet OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-film05/` | 1 | 3.7 Mo | 5.2 s | Rush H3 du projet OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-film07/` | 2 | 6.4 Mo | 8.9 s | Rush H3 du projet OPSYS-AI (H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film02/` | 18 | 38.5 Mo | 1:33.1 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film03/` | 16 | 49.0 Mo | 1:22.7 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film04/` | 20 | 82.4 Mo | 1:43.2 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film05/` | 22 | 63.1 Mo | 1:53.7 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film06/` | 17 | 63.5 Mo | 1:27.9 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film07/` | 13 | 54.5 Mo | 1:01.9 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/film08/` | 9 | 27.7 Mo | 46.5 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-h3-work/racine/` | 36 | 106.1 Mo | 3:06.1 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-media-brand75/` | 8 | 36.1 Mo | 52.1 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-media-brochure20261027/` | 1 | 15.4 Mo | 6.0 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-media-capture-source/` | 4 | 3.9 Mo |  | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-media-grok20261028/` | 11 | 171.7 Mo | 1:21.4 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-media-minimax-h3-20261029/` | 1 | 2.9 Mo | 5.2 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-public-brand75/` | 6 | 45.0 Mo | 36.0 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-public-brochure20261027/` | 1 | 8.7 Mo | 3.0 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-public-generated/` | 3 | 26.6 Mo | 24.0 s | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-public-grok20261028/` | 11 | 202.3 Mo | 1:21.4 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/codex-fondateur/rushes-public-vfx20261028/` | 8 | 62.4 Mo | 1:01.0 | Film / rush OPSYS-AI du projet Codex du fondateur (Codex : Grok / Veo / MiniMax H3) |
| `07-opsys-ai/nexora/v6-travail/avatar/` | 12 | 67.1 Mo | 1:15.3 | Travail du film OPSYS-AI (plaques H3 / avatar) (H3, Audio2Face-3D) |
| `07-opsys-ai/nexora/v6-travail/plaques/` | 15 | 33.5 Mo | 1:17.5 | Travail du film OPSYS-AI (plaques H3 / avatar) (H3, Audio2Face-3D) |

### 08-tests-agents

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `08-tests-agents/Test-agents-9-premiers/Test-agents-eco-opsys-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-eco-opsys-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-eco-opsys-16x9-fr.mp4` | 11.7 Mo | 40.0 s | 1280x720 | 2026-11-03 01:12 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-eco-reception-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-eco-reception-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-eco-reception-16x9-fr.mp4` | 10.3 Mo | 36.0 s | 1280x720 | 2026-11-03 01:08 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-eco-surveillance-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-eco-surveillance-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-eco-surveillance-16x9-fr.mp4` | 10.4 Mo | 36.0 s | 1280x720 | 2026-11-03 01:10 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-equilibre-opsys-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-equilibre-opsys-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-equilibre-opsys-16x9-fr.mp4` | 10.1 Mo | 40.0 s | 1280x720 | 2026-11-03 01:13 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-equilibre-reception-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-equilibre-reception-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-equilibre-reception-16x9-fr.mp4` | 9.5 Mo | 36.0 s | 1280x720 | 2026-11-03 01:09 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-equilibre-surveillance-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-equilibre-surveillance-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-equilibre-surveillance-16x9-fr.mp4` | 11.2 Mo | 36.0 s | 1280x720 | 2026-11-03 01:11 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-expert-opsys-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-expert-opsys-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-expert-opsys-16x9-fr.mp4` | 11.1 Mo | 40.0 s | 1280x720 | 2026-11-03 01:12 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-expert-reception-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-expert-reception-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-expert-reception-16x9-fr.mp4` | 10.0 Mo | 36.0 s | 1280x720 | 2026-11-03 01:08 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test-agents-9-premiers/Test-agents-expert-surveillance-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/premier-test-rejete/Test-agents-expert-surveillance-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test-agents-expert-surveillance-16x9-fr.mp4` | 11.0 Mo | 36.0 s | 1280x720 | 2026-11-03 01:10 | Test-agents (9 films, 3 niveaux × 3 sujets) ; test 1 | master | 3/10, rejeté; rejeté |
| `08-tests-agents/Test2-12-films/Test2-creative-eco-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-creative-eco-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-creative-eco-16x9-fr.mp4` | 63.2 Mo | 39.8 s | 1920x1080 | 2026-11-03 12:22 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-creative-equilibre-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-creative-equilibre-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-creative-equilibre-16x9-fr.mp4` | 83.0 Mo | 46.0 s | 1920x1080 | 2026-11-03 12:26 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-creative-expert-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-creative-expert-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-creative-expert-16x9-fr.mp4` | 87.0 Mo | 46.7 s | 1920x1080 | 2026-11-03 12:30 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-creative-opus-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-creative-opus-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-creative-opus-16x9-fr.mp4` | 82.7 Mo | 44.7 s | 1920x1080 | 2026-11-03 12:31 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-opsys-eco-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-opsys-eco-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-opsys-eco-16x9-fr.mp4` | 75.3 Mo | 45.3 s | 1920x1080 | 2026-11-03 12:24 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-opsys-equilibre-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-opsys-equilibre-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-opsys-equilibre-16x9-fr.mp4` | 84.3 Mo | 45.5 s | 1920x1080 | 2026-11-03 12:28 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-opsys-expert-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-opsys-expert-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-opsys-expert-16x9-fr.mp4` | 74.2 Mo | 46.1 s | 1920x1080 | 2026-11-03 12:30 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-opsys-opus-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-opsys-opus-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-opsys-opus-16x9-fr.mp4` | 76.2 Mo | 49.1 s | 1920x1080 | 2026-11-03 12:32 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-workstudio-eco-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-workstudio-eco-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-workstudio-eco-16x9-fr.mp4` | 65.5 Mo | 43.5 s | 1920x1080 | 2026-11-03 12:25 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-workstudio-equilibre-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-workstudio-equilibre-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-workstudio-equilibre-16x9-fr.mp4` | 72.5 Mo | 44.1 s | 1920x1080 | 2026-11-03 12:29 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-workstudio-expert-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-workstudio-expert-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-workstudio-expert-16x9-fr.mp4` | 71.0 Mo | 45.1 s | 1920x1080 | 2026-11-03 12:31 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |
| `08-tests-agents/Test2-12-films/Test2-workstudio-opus-16x9-fr.mp4` | `pc1:/home/pc1/Bureau/Nexora-Livrables/2026-11-03/films/Test2-workstudio-opus-16x9-fr.mp4`<br>`pc6:D6/promo/montage/Test2-workstudio-opus-16x9-fr.mp4` | 67.0 Mo | 46.1 s | 1920x1080 | 2026-11-03 12:33 | Comparatif v2 : film écrit entièrement par le modèle ; test 2 | master | 4,2 à 5,4 (agent) ; narration 0,1/10 (fondateur) |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `08-tests-agents/Test2-plaques/creative-eco/` | 15 | 44.4 Mo | 1:17.5 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/creative-equilibre/` | 16 | 55.8 Mo | 1:22.7 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/creative-expert/` | 16 | 56.0 Mo | 1:22.7 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/creative-opus/` | 16 | 66.7 Mo | 1:22.7 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-eco/` | 10 | 45.4 Mo | 51.7 s | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-eco/tableaux/` | 6 | 3.7 Mo | 15.8 s | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-equilibre/` | 13 | 56.7 Mo | 1:07.2 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-equilibre/tableaux/` | 3 | 2.3 Mo | 9.8 s | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-expert/` | 13 | 49.8 Mo | 1:07.2 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-expert/tableaux/` | 4 | 3.1 Mo | 10.7 s | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-opus/` | 12 | 50.9 Mo | 1:02.0 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/opsys-opus/tableaux/` | 5 | 3.8 Mo | 15.5 s | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/workstudio-eco/` | 12 | 34.2 Mo | 1:02.0 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/workstudio-equilibre/` | 14 | 47.2 Mo | 1:12.4 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/workstudio-expert/` | 15 | 46.8 Mo | 1:17.5 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/Test2-plaques/workstudio-opus/` | 16 | 38.2 Mo | 1:22.7 | Plaque H3 / tableau du comparatif Test2 (H3 + usine) |
| `08-tests-agents/divers/` | 1 | 0.0 Mo | 8.0 s | Carton neutre de test (code) |

### 10-autres

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `10-autres/app-creative-rendus/clips-musique/clip_20_musique_1793441320169.mp4` | `VM202:/srv/creative/data/rendus/clips-musique/clip_20_musique_1793441320169.mp4`<br>`pc5 (archive):A5/rendus/clips-musique/clip_20_musique_1793441320169.mp4` | 2.5 Mo | 5.2 s | 832x480 | 2026-10-31 06:08 | Clip avec musique (app Creative) | master |  |
| `10-autres/app-creative-rendus/clips-musique/clip_32_musique_1793441356733.mp4` | `VM202:/srv/creative/data/rendus/clips-musique/clip_32_musique_1793441356733.mp4`<br>`pc5 (archive):A5/rendus/clips-musique/clip_32_musique_1793441356733.mp4` | 4.3 Mo | 5.2 s | 1344x768 | 2026-10-31 06:09 | Clip avec musique (app Creative) | master |  |
| `10-autres/app-creative-rendus/films/film_10_1793415293431.mp4` | `VM202:/srv/creative/data/rendus/films/film_10_1793415290243.mp4`<br>`VM202:/srv/creative/data/rendus/films/film_10_1793415293431.mp4`<br>`pc5 (archive):A5/rendus/films/film_10_1793415290243.mp4`<br>+1 | 14.0 Mo | 41.0 s | 832x480 | 2026-10-30 22:54 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_12_1793415400361.mp4` | `VM202:/srv/creative/data/rendus/films/film_12_1793415400361.mp4`<br>`pc5 (archive):A5/rendus/films/film_12_1793415400361.mp4` | 12.1 Mo | 33.8 s | 832x480 | 2026-10-30 22:56 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_12_prores.mov` | `VM202:/srv/creative/data/rendus/films/exports/film_12_prores.mov`<br>`pc5 (archive):A5/rendus/films/exports/film_12_prores.mov` | 237.9 Mo | 33.9 s | 832x480 | 2026-10-30 22:56 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_1_1793600512619.mp4` | `pc6:D6/producteur-dev/rendus/films/film_1_1793600512619.mp4` | 3.1 Mo | 14.9 s | 480x832 | 2026-11-02 01:21 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_1_1793600512619_musique.mp4` | `pc6:D6/producteur-dev/rendus/films/film_1_1793600512619_musique.mp4` | 3.3 Mo | 14.9 s | 480x832 | 2026-11-02 01:21 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_1_carton0.mp4` | `pc6:D6/producteur-dev/rendus/films/film_1_carton0.mp4` | 0.0 Mo | 2.0 s | 480x832 | 2026-11-02 01:21 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_1_carton1.mp4` | `pc6:D6/producteur-dev/rendus/films/film_1_carton1.mp4` | 0.0 Mo | 2.5 s | 480x832 | 2026-11-02 01:21 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_25_1793416620743.mp4` | `VM202:/srv/creative/data/rendus/films/film_25_1793416620743.mp4`<br>`pc5 (archive):A5/rendus/films/film_25_1793416620743.mp4` | 2.2 Mo | 10.4 s | 832x480 | 2026-10-30 23:17 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_354_1793611665184.mp4` | `pc5 (archive):A5/rendus/films/film_354_1793611665184.mp4`<br>`pc6:D6/rendus/films/film_354_1793611665184.mp4` | 5.3 Mo | 25.3 s | 1344x768 | 2026-11-02 04:27 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_354_carton0.mp4` | `pc5 (archive):A5/rendus/films/film_354_carton0.mp4`<br>`pc6:D6/rendus/films/film_354_carton0.mp4` | 0.0 Mo | 2.0 s | 1344x768 | 2026-11-02 04:27 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_354_carton1.mp4` | `pc5 (archive):A5/rendus/films/film_354_carton1.mp4`<br>`pc6:D6/rendus/films/film_354_carton1.mp4` | 0.0 Mo | 2.5 s | 1344x768 | 2026-11-02 04:27 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_360_1793612144436.mp4` | `pc5 (archive):A5/rendus/films/film_360_1793612144436.mp4`<br>`pc6:D6/rendus/films/film_360_1793612144436.mp4` | 5.1 Mo | 20.7 s | 1344x768 | 2026-11-02 04:35 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_362_1793612255973.mp4` | `pc5 (archive):A5/rendus/films/film_362_1793612255973.mp4`<br>`pc6:D6/rendus/films/film_362_1793612255973.mp4` | 5.3 Mo | 20.7 s | 1344x768 | 2026-11-02 04:37 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_364_1793612367340.mp4` | `pc5 (archive):A5/rendus/films/film_364_1793612367340.mp4`<br>`pc6:D6/rendus/films/film_364_1793612367340.mp4` | 5.9 Mo | 20.7 s | 1344x768 | 2026-11-02 04:39 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_366_1793612813662.mp4` | `pc5 (archive):A5/rendus/films/film_366_1793612813662.mp4`<br>`pc6:D6/rendus/films/film_366_1793612813662.mp4` | 5.9 Mo | 25.3 s | 768x1344 | 2026-11-02 04:46 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_366_1793612813662_musique.mp4` | `pc5 (archive):A5/rendus/films/film_366_1793612813662_musique.mp4`<br>`pc6:D6/rendus/films/film_366_1793612813662_musique.mp4` | 6.2 Mo | 25.2 s | 768x1344 | 2026-11-02 04:47 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_366_carton0.mp4` | `pc5 (archive):A5/rendus/films/film_366_carton0.mp4`<br>`pc6:D6/rendus/films/film_366_carton0.mp4` | 0.0 Mo | 2.0 s | 768x1344 | 2026-11-02 04:46 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_366_carton1.mp4` | `pc5 (archive):A5/rendus/films/film_366_carton1.mp4`<br>`pc6:D6/rendus/films/film_366_carton1.mp4` | 0.0 Mo | 2.5 s | 768x1344 | 2026-11-02 04:46 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_63_1793747126846.mp4` | `VM202:/srv/creative/data/rendus/films/film_63_1793747126846.mp4` | 8.4 Mo | 20.1 s | 832x480 | 2026-11-03 18:05 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_63_carton0.mp4` | `VM202:/srv/creative/data/rendus/films/film_63_carton0.mp4` | 0.0 Mo | 2.0 s | 832x480 | 2026-11-03 18:05 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_63_carton1.mp4` | `VM202:/srv/creative/data/rendus/films/film_63_carton1.mp4` | 0.0 Mo | 2.5 s | 832x480 | 2026-11-03 18:05 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_7_1793601272214.mp4` | `pc6:D6/producteur-dev/rendus/films/film_7_1793601272214.mp4` | 2.7 Mo | 10.4 s | 480x832 | 2026-11-02 01:34 | Film généré par l’app Creative (Director) | master |  |
| `10-autres/app-creative-rendus/films/film_9_1793601301922.mp4` | `pc6:D6/producteur-dev/rendus/films/film_9_1793601301922.mp4` | 5.0 Mo | 15.6 s | 480x832 | 2026-11-02 01:35 | Film généré par l’app Creative (Director) | master |  |

**Rushes et itérations de travail (résumé)**

| Dossier | Fichiers | Taille | Durée cumulée | Contenu |
|---|---:|---:|---:|---|
| `10-autres/app-creative-rendus/openfield-clips/` | 65 | 177.4 Mo | 5:36.9 | Clip OpenField (rendu de l’app Creative, essais) (H3/Wan (app Creative)) |
| `10-autres/sorties-h3-pc1/test-h3/` | 7 | 12.0 Mo | 32.6 s | Sortie H3 de pc1 (banc / essai) (H3) |
| `10-autres/sorties-h3-pc1/voixbench/` | 6 | 6.7 Mo | 39.5 s | Sortie H3 de pc1 (banc / essai) (H3) |
| `10-autres/usine-films-v3-travail/` | 7 | 90.3 Mo | 3:00.5 | Extrait / plaque de travail de l’usine à films (v3, pc6) (H3 + usine) |

### 11-publie-sur-le-site

| Chemin sous TOUS-LES-FILMS/ | Origine(s) | Taille | Durée | Rés. | Date | Quoi | Rôle | Note / site |
|---|---|---:|---:|---|---|---|---|---|
| `11-publie-sur-le-site/medias-web/site-film-creative-en.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-02_1100_site-film-creative-en.mp4`) | `VM201:/srv/nexora/medias/web/site-film-creative-en.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/36641d74-3b57-4241-bc9e-33aa846cbfc6.mp4` | 15.2 Mo | 59.5 s | 1920x1080 | 2026-11-02 05:59 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-creative-fr.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-02_1100_site-film-creative-fr.mp4`) | `VM201:/srv/nexora/medias/web/site-film-creative-fr.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/5100babd-d2ef-4a1e-af61-585ea30a163d.mp4` | 15.1 Mo | 59.5 s | 1920x1080 | 2026-11-02 05:59 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-modeles-en.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-03_0138_site-film-modeles-en.mp4`) | `VM201:/srv/nexora/medias/web/site-film-modeles-en.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/d867cbf3-2a97-4943-af12-aa3cc34f6591.mp4` | 6.8 Mo | 35.6 s | 1920x1080 | 2026-11-02 20:34 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-modeles-fr.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-03_0138_site-film-modeles-fr.mp4`) | `VM201:/srv/nexora/medias/web/site-film-modeles-fr.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/8f54f047-7266-4797-809e-251390bdb9d8.mp4` | 6.5 Mo | 35.6 s | 1920x1080 | 2026-11-02 20:34 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-surveillance-en.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-03_0138_site-film-surveillance-en.mp4`) | `VM201:/srv/nexora/medias/web/site-film-surveillance-en.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/dcf1c576-1b04-4cc3-ab3e-1887a3d6a529.mp4` | 8.7 Mo | 33.3 s | 1920x1080 | 2026-11-02 20:34 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-surveillance-fr.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-03_0138_site-film-surveillance-fr.mp4`) | `VM201:/srv/nexora/medias/web/site-film-surveillance-fr.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/e1a66eef-285e-4cbc-a4fd-3f26765fec5d.mp4` | 8.7 Mo | 33.3 s | 1920x1080 | 2026-11-02 20:34 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-workstudio-en.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-03_0138_site-film-workstudio-en.mp4`) | `VM201:/srv/nexora/medias/web/site-film-workstudio-en.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/4d288837-2e7f-4d59-ba8b-8916f62410a3.mp4` | 6.5 Mo | 46.7 s | 1920x1080 | 2026-11-02 20:34 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/medias-web/site-film-workstudio-fr.mp4` (+ alias : `11-publie-sur-le-site/volume-directus-versions/2026-11-03_0138_site-film-workstudio-fr.mp4`) | `VM201:/srv/nexora/medias/web/site-film-workstudio-fr.mp4`<br>`VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/bf95e20b-a235-4a41-b20c-30c6b4409f8f.mp4` | 6.8 Mo | 46.7 s | 1920x1080 | 2026-11-02 20:34 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0603_site-hero-boucle.mp4` | `VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/b94c538d-c275-47ca-a1ee-30a902d92f78.mp4` | 5.7 Mo | 12.0 s | 1920x1080 | 2026-11-02 01:03 | Fichier servi par le site (re-encodage web) | web | publié sur le site |
| `11-publie-sur-le-site/volume-directus-versions/2026-11-02_0832_site-hero-boucle.mp4` | `VM201:/var/lib/docker/volumes/nexorasite_uploads/_data/81324ad5-aba1-44be-bb63-1f7097e3e253.mp4` | 3.8 Mo | 12.0 s | 1920x1080 | 2026-11-02 03:32 | Fichier servi par le site (re-encodage web) | web | publié sur le site |

## Doublons identiques (même sha256)

821 vidéos existent en plusieurs exemplaires identiques, copiées une seule fois. Total d’exemplaires lus : 2763 pour 1485 vidéos distinctes. Les plus répétées :

| Fichier | Exemplaires | Où |
|---|---:|---|
| `film_12_prores.mov` | 2 | VM202, pc5 (archive) |
| `video-opsys.mp4` | 3 | pc1, pc6 |
| `Test2-creative-expert-16x9-fr.mp4` | 2 | pc1, pc6 |
| `video-opsys-avant-grok45-94c0f7538ab9.mp4` | 2 | pc1 |
| `Test2-opsys-equilibre-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-creative-equilibre-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-creative-opus-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Nexora-Creative-promo-V4-9x16-en.mp4` | 2 | pc5 (archive), pc6 |
| `Nexora-Creative-promo-V4-9x16-fr.mp4` | 2 | pc5 (archive), pc6 |
| `Nexora-Creative-promo-V4-16x9-fr.mp4` | 2 | pc5 (archive), pc6 |
| `Nexora-Creative-promo-V4-16x9-en.mp4` | 2 | pc5 (archive), pc6 |
| `Test2-opsys-opus-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-opsys-eco-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-opsys-expert-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-workstudio-equilibre-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-workstudio-expert-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-workstudio-opus-16x9-fr.mp4` | 2 | pc1, pc6 |
| `Test2-workstudio-eco-16x9-fr.mp4` | 2 | pc1, pc6 |
| `FILM06-REVUE-1080p-r13.mp4` | 2 | pc1, pc6 |
| `video-opsys-avant-vfx.mp4` | 5 | VM201, pc1, pc6 |
| `video-opsys-avant-grok45-e7917f8bed90.mp4` | 2 | pc1 |
| `Test2-creative-eco-16x9-fr.mp4` | 2 | pc1, pc6 |
| `FILM08-REVUE-r6-1080p.mp4` | 2 | pc1, pc6 |
| `8820340.mp4` | 2 | pc1 |
| `Nexora-Surveillance-IA-v2-9x16-fr.mp4` | 2 | pc5 (archive), pc6 |

## Non copiés (96 fichiers, 745 Mo)

Fichiers qui ne sont pas des films produits pour Nexora (actifs de logiciels tiers, vidéos de stock, références publicitaires de recherche, démos de clones amont) : listés avec leur emplacement dans `INVENTAIRE.csv` (colonne non_copie_raison).

- actif amont du fork WorkStudio (pas produit par Nexora) : 12
- vidéos de stock tierces (Codex OPSYS) : 17
- références publicitaires tierces, recherche seule : 20
- cache/outil tiers : 29
- démos amont du clone FableCut (tiers) : 18
## Chronologie des films (de quoi se compose chaque dossier)

| Date (heure locale) | Événement | Dossier |
|---|---|---|
| 24–31/10 | Projet Codex OPSYS-AI du fondateur (Grok, Veo, MiniMax H3) : exports, itérations, rushes | `07-opsys-ai/codex-fondateur/` |
| 30–31/10 | Premiers essais H3 (banc de moteurs, dragon, karaté), bande-annonce V1 (06:02) puis V2 « flotte au-dessus de la Terre, duels de sabres laser » (07:5x) | `02-creative-promos/V1…`, `V2…`, `rushes-V1-V2/` |
| 01/11 | Campagne de lancement : film de marque 60 s, spots 30/15/6 s, 8 teasers, stings, boucles | `01-campagne-marque/` |
| 02/11 | Hero v2/v3, Surveillance IA v1 (03:01) puis v2 (16:05, note agent 7,6), promo V3 bataille spatiale (03:17, 3/10, rejetée), promo V4 « Une phrase. Un film. » (05:47, 6,5/10), WorkStudio v1 (06:48) puis v2 (16:46), Modèles et API (20:30, 7,1), OPSYS-AI « Ils travaillent. Vous vivez. » (22:08, 7,1/10) | `03` à `07` |
| 03/11 | Test-agents (9 films, 3/10, rejetés) puis Test2/comparatif v2 (12 films, 4,2 à 5,4 par l’agent ; narration 0,1/10 selon le fondateur) | `08-tests-agents/` |
| en cours | Films V5 (agent) | `09-films-v5/` |

## Ce qui n’existe plus (vérité) et comment le refaire

Fichiers recherchés partout (pc6, archive pc5, pc1, VM201 volume Directus et docker, VM202, historique git des dépôts Creative et NexoraSite) ; commandes non lancées (aucun rendu lourd exécuté).

| Perdu | Constat | Régénérable ? |
|---|---|---|
| **Promo V3 « bataille spatiale »** : les 12 films `Nexora-Creative-promo-V3-{16x9,9x16}-{fr,en}[-30s\|-15s]` et leurs copies web `film-creative-*` (écrasées par la V4 le 02/11 à 05:45) ; données `promo/v3/` (1,9 Go : brouillons, images clés Qwen `cles/`, cache de rendu, `audio/v3-musique-31.flac`, `tout-rendre.sh`) supprimées de pc6 le 02/11 avant la consigne « tout garder » ; absentes de l’archive pc5 | Les **49 plans H3 (p01–p10, t01–t09, 16:9 et verticaux) et la ronde de comparaison survivent sur pc1** (`02-creative-promos/V3-bataille-spatiale/`). Le code et la liste de montage sont dans git (commit `0d00192`, `marketing/creative/video-v3/`). Manquent : images clés Qwen, musique `v3-musique-31.flac` (candidates 314 et 2718 écartées), cache de rendu | **Oui, en grande partie** : copier les plans dans `~/nexora-creative-data/promo/v3/plans/`, régénérer une musique MiniMax Music 3 (≈ 27 s de GPU, pas identique sans la graine d’origine), puis `cd "…/marketing/creative/video-v3" && python3 montage_v3.py > montage-v3.json && python3 monter_v3.py montage-v3.json --format 16x9 --langue fr` (répéter pour 9x16/en et `--version 30\|15` ; ≈ 25 min de CPU pour les 12). **Ne pas lancer `livrer.sh` tel quel** : il écraserait `site-medias/film-creative-*` (films V4 publiés). Le film était noté 3/10 par le fondateur. |
| **Bande-annonce V2, masters 1080p** (16:9 et 9:16) | Seules subsistent les copies web : `promo-web-720.mp4` = `promo.mp4` = l’ancien `web/public/creative-bande-annonce.mp4` du dépôt NexoraSite (commit `a30b724`, retiré le 02/11, octets identiques), et `site-creative-promo.mp4` (720p, volume Directus) | **Oui** : rushes H3 en archive pc5 (`rushes-V1-V2/plans-H3`), musique b89 et sfx sur pc6 (`promo/musique`, `promo/sfx`), cartons ; `python3 outils/liste_promo_v2.py` produit la liste, `python3 outils/monter.py liste.json` rend (≈ quelques minutes CPU). La variante « démo investisseurs » demande 2 plans issus d’images clés Qwen : à vérifier. |
| **WorkStudio v1** (commit `0a4b90b`, 06:48) | Écrasé par la v2 (mêmes noms de fichiers, 16:46) ; non retrouvé | Possible mais coûteux : checkout de `0a4b90b -- marketing/nexora/campagne-films`, relancer l’usine avec la capture réelle sur la VM 203. La v2 remplace la v1. |
| **`apercu-v1/2/3`, `nexora-creative-promo-16x9/9x16`, `Nexora-Creative-V2-*`, `nexora-creative-v2-demo/public`** | Aucun fichier de ce nom sur aucune machine ni archive ni dans l’historique git (jamais versionnés). Seuls 4 aperçus de l’app survivent (`apercus-app/`) | Non à l’identique. Les plans H3 sources de V1/V2 sont en archive ; refaire le montage comme ci-dessus. **Les poids H3 fl2va int8, ref2va bf16/int8 et Singularity ont été supprimés de pc1 le 02/11** (134 Go, journal) : un rendu H3 neuf utilise FastH3 nvfp4 ou le PRISM, donc **pas à l’identique** des plans d’origine. |

Aussi à savoir : l’historique de versions du site (3 boucles hero, 2 versions de Surveillance, etc.) est conservé dans `11-publie-sur-le-site/volume-directus-versions/`. Les cartons `carte-*.mp4` des teasers sont versionnés dans git (commits de la campagne). Le seul film autrefois commité puis retiré de git est `creative-bande-annonce.mp4` (dépôts NexoraSite et NexoraSite-deploy).

## Besoin du fondateur

- Espace : pc1 `/` à 96 % (≈ 37 Go libres après la copie). Ce dossier n’a consommé que ≈ 7,8 Go de données neuves (le reste, ≈ 14,9 Go, est en liens physiques). Si les films V5 et les prochains rendus s’empilent, le disque partitionné « Storage » (sda2, 1,8 To, non monté) serait à monter par le fondateur ; je n’y ai pas touché.
- Rien n’a été supprimé nulle part. Les doublons restent à leur emplacement d’origine.
