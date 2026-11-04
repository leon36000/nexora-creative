#!/usr/bin/env bash
# Détourage rapide (SAM 3.1 + ViTMatte) sur la RTX 2070 SUPER de la VM 204, en unité systemd transitoire (essai).
# Reproduit l'essai du 04/11/2026 (recherche/28). Ne touche ni à ComfyUI (8188/8189) ni au service audio (8190).
# Usage, sur la VM 204 : lancer-detourage-essai.sh start|stop|etat
# Prérequis : <E>/ev (venv avec .pth vers /srv/nexora-gpu/venv : torch 2.11 cu128, transformers 5.22), <E>/extra (opencv-python-headless
# 5.0.0.93, openexr 3.5.3, huggingface-hub 2.4.0), <E>/comfy044 (ComfyUI 2c75dc1, sans .git), poids sous <E>/poids
# (pro/Comfy-Org/sam3.1/checkpoints/sam3.1_multiplex_fp16.safetensors, hf/hub/models--hustvl--vitmatte-base-composition-1k avec refs/main).
set -euo pipefail
E=${E:-/srv/nexora-gpu/essais-$(date +%Y%m%d)}; D=$E/detourage; U=essai-detourage
# Le disque de la VM est presque plein : le garde-fou du serveur exige 3 Go libres, les travaux vont donc en mémoire (tmpfs).
TRAVAUX=${TRAVAUX:-/dev/shm/essai-detourage}; PORT=${PORT:-8291}
case "${1:-etat}" in
  start) mkdir -p "$TRAVAUX"; sudo systemd-run --unit=$U --uid=nexora --gid=nexora -p MemoryMax=3800M -p MemorySwapMax=1G -p CPUQuota=250% \
    --working-directory="$D" --setenv=CUDA_VISIBLE_DEVICES=1 --setenv=PYTHONPATH="$E/extra" --setenv=NEXORA_DETOURAGE_POIDS="$D/poids" \
    --setenv=HF_HOME="$D/poids/hf" --setenv=HF_HUB_OFFLINE=1 --setenv=NEXORA_DETOURAGE_DOSSIER="$TRAVAUX" --setenv=NEXORA_DETOURAGE_PORT=$PORT \
    --setenv=NEXORA_DETOURAGE_SOCKET="$D/essai.sock" --setenv=NEXORA_COMFYUI="$E/comfy044" --setenv=FFMPEG_BIN=/usr/bin/ffmpeg \
    --setenv=PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True --setenv=PYTHONDONTWRITEBYTECODE=1 "$E/ev/bin/python" -I "$D/serveur.py" ;;
  stop) sudo systemctl stop $U; rm -rf "$TRAVAUX" ;;
  *) systemctl status $U --no-pager | head -8 ;;
esac
# Banc : BANC_GPU=1 $E/ev/bin/python -I $D/banc.py unix:$D/essai.sock <clips> <sortie.json> --matting vitmatte-base --params '{"bande":0.05}'
# En production : NEXORA_DETOURAGE_HOTE=192.168.1.124, NEXORA_DETOURAGE_JETON_FICHIER (mode 600) et NEXORA_DETOURAGE_AUTORISES=192.168.1.122
# sont obligatoires (le serveur refuse de démarrer sans) ; ouvrir le port dans /etc/pve/firewall/204.fw.
