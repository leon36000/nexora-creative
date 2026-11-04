#!/usr/bin/env bash
# Construit et pousse l'image du détourage sur pc3 (Job kaniko), depuis les fichiers suivis par git d'outils/detourage.
#   deploy/k8s/detourage/construire.sh <cu130|cu126> [tag] [contexte=outils/detourage] [image=detourage]
#   ex. palier pro : construire.sh cu130 '' outils/detourage/pro detourage-pro
# KUBECTL : commande kubectl du groupe k3s (défaut : kubectl). PC3 : alias SSH de pc3 (défaut : pc3-agent).
set -euo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; RACINE="$(cd "$ICI/../../.." && pwd)"
VARIANTE=${1:?cu130 ou cu126}; KUBECTL=${KUBECTL:-kubectl}; PC3=${PC3:-pc3-agent}
TAG=${2:-$(git -C "$RACINE" rev-parse --short HEAD)-$VARIANTE}
SOURCE=${3:-outils/detourage}; IMAGE=${4:-detourage}
PROF=$(echo "$SOURCE" | tr -cd / | wc -c); PROF=$((PROF + 1))
CONTEXTE=/home/pc3/nexora-detourage/k8s/construction/$IMAGE-$TAG
echo "== contexte $TAG"
ssh "$PC3" "rm -rf $CONTEXTE && mkdir -p $CONTEXTE"
git -C "$RACINE" archive HEAD "$SOURCE" | ssh "$PC3" "tar -x -C $CONTEXTE --strip-components=$PROF"
echo "== Job kaniko"
sed -e "s|__TAG__|$TAG|g" -e "s|__IMAGE__|$IMAGE|g" -e "s|__TORCH_INDEX__|https://download.pytorch.org/whl/$VARIANTE|g" -e "s|__CONTEXTE__|$CONTEXTE|g" \
  "$ICI/20-construction-kaniko.yaml" | $KUBECTL apply -f -
$KUBECTL -n nexora wait --for=condition=complete --timeout=3600s "job/construction-$IMAGE-$TAG"
echo "== poussée : 127.0.0.1:5000/nexora/$IMAGE:$TAG"
ssh "$PC3" "rm -rf $CONTEXTE"
