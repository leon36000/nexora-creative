#!/usr/bin/env bash
# Livraison par étapes : aucune opération ne supprime de données ni ne pilote un moteur GPU.
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETAPE="${1:-}"
if [ "$#" -gt 0 ]; then shift; fi
case "$ETAPE" in
  transporter)
    exec "$ICI/transporter-release.sh" "$@" ;;
  archive|construire)
    exec env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
      python3 -B "$ICI/preparer_release.py" "$ETAPE" "$@" ;;
  plan|activer|retour)
    exec env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/nonexistent PYTHONDONTWRITEBYTECODE=1 \
      python3 -B "$ICI/livrer_release.py" "$ETAPE" "$@" ;;
  *)
    printf '%s\n' 'Étapes : transporter DEPOT SHA_GIT DOSSIER_LOCAL_NEUF IDENTIFIANT | archive DEPOT SHA_GIT ARCHIVE | construire ARCHIVE SHA256 DOSSIER_NEUF | plan RELEASE CIBLE MANIFESTE | activer RELEASE CIBLE DATA BACKUP MANIFESTE | retour CIBLE DATA BACKUP' >&2
    printf '%s\n' 'Construire la release sur la VM cible, examiner le manifeste et les états avant toute activation ; activer requiert les droits systemd.' >&2
    exit 2 ;;
esac
