#!/usr/bin/env bash
# Passerelle LiteLLM légère des sous-agents. Usage : gateway.sh start|stop|status|restart|logs
set -u
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"
case "${1:-status}" in
  start)
    if sa_up; then echo "déjà démarrée sur $SA_URL"; exit 0; fi
    docker rm -f "$SA_CONTAINER" >/dev/null 2>&1
    DK="$(sa_extract Deepinfra)"; OK="$(sa_extract Openrouter)"
    [ -n "$DK" ] && [ -n "$OK" ] || { echo "clés introuvables dans $SA_KEYFILE (formats « Deepinfra: … » et « Openrouter: … »)" >&2; exit 1; }
    MK="$(sa_master_key)"
    DEEPINFRA_API_KEY="$DK" OPENROUTER_API_KEY="$OK" LITELLM_MASTER_KEY="$MK" SA_LOG=/app/state/usage.jsonl \
    docker run -d --name "$SA_CONTAINER" --restart no --user "$(id -u):$(id -g)" \
      -p "127.0.0.1:${SA_PORT}:4000" \
      -e DEEPINFRA_API_KEY -e OPENROUTER_API_KEY -e LITELLM_MASTER_KEY -e SA_LOG \
      -e LITELLM_LOG=ERROR -e LITELLM_TELEMETRY=False -e DISABLE_ADMIN_UI=True -e HOME=/tmp \
      -v "$SA_DIR/litellm:/app/cfg:ro" -v "$SA_STATE:/app/state" \
      --read-only --tmpfs /tmp:rw,size=256m --cap-drop ALL --security-opt no-new-privileges:true \
      --memory 2g --pids-limit 512 \
      "$SA_IMAGE" --config /app/cfg/config.yaml --port 4000 >/dev/null || exit 1
    unset DK OK MK
    for i in $(seq 1 60); do sa_up && { echo "passerelle prête sur $SA_URL"; exit 0; }; sleep 2; done
    echo "la passerelle n'a pas démarré ; voir : $0 logs" >&2; exit 1 ;;
  stop) docker rm -f "$SA_CONTAINER" >/dev/null 2>&1 && echo arrêtée || echo "pas de conteneur" ;;
  restart) "$0" stop; "$0" start ;;
  status) if sa_up; then echo "en marche sur $SA_URL"; else echo "arrêtée"; exit 1; fi ;;
  logs) docker logs --tail 80 "$SA_CONTAINER" 2>&1 | sed -E 's/(sk-[A-Za-z0-9_-]{6})[A-Za-z0-9_-]+/\1…/g' ;;
  *) echo "usage: $0 start|stop|restart|status|logs" >&2; exit 2 ;;
esac
