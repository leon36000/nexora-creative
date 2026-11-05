#!/usr/bin/env bash
# Passerelle LiteLLM légère. Les actions start/stop ne suppriment jamais de conteneur.
set -u
set +x
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

# La vérification porte toujours sur la boucle locale, jamais sur un proxy hérité.
sa_up() { curl --noproxy '*' -s -m 3 -o /dev/null -w '%{http_code}' "$SA_URL/health/liveliness" 2>/dev/null | grep -q '^200$'; }

container_exists() {
  docker inspect "$SA_CONTAINER" >/dev/null 2>&1 && return 0
  # Ne pas confondre un conteneur absent avec un daemon Docker inaccessible.
  if ! docker info >/dev/null 2>&1; then
    echo "Docker est indisponible; état du conteneur inconnu" >&2
    return 2
  fi
  return 1
}

validate_container() {
  local image port
  image="$(docker inspect --format '{{.Config.Image}}' "$SA_CONTAINER" 2>/dev/null)" || {
    echo "impossible d’inspecter le conteneur existant; aucune action effectuée" >&2
    return 1
  }
  port="$(docker inspect --format '{{with index .HostConfig.PortBindings "4000/tcp"}}{{range .}}{{.HostIp}}:{{.HostPort}}{{end}}{{end}}' "$SA_CONTAINER" 2>/dev/null)" || {
    echo "impossible d’inspecter le port du conteneur existant; aucune action effectuée" >&2
    return 1
  }
  if [ "$image" != "$SA_IMAGE" ]; then
    echo "image du conteneur inattendue. Aucune action effectuée." >&2
    return 1
  fi
  if [ "$port" != "127.0.0.1:$SA_PORT" ]; then
    echo "port du conteneur inattendu. Aucune action effectuée." >&2
    return 1
  fi
  return 0
}

wait_healthy() {
  local attempts="${SA_HEALTH_CHECKS:-60}" delay="${SA_HEALTH_DELAY:-2}" i
  case "$attempts" in ''|*[!0-9]*|0) echo "nombre de vérifications santé invalide" >&2; return 2;; esac
  case "$delay" in ''|*[!0-9]*) echo "délai de vérification santé invalide" >&2; return 2;; esac
  for ((i=1; i<=attempts; i++)); do
    if sa_up; then return 0; fi
    if [ "$i" -lt "$attempts" ]; then sleep "$delay"; fi
  done
  return 1
}

start_existing() {
  local status
  validate_container || return 1
  status="$(docker inspect --format '{{.State.Status}}' "$SA_CONTAINER" 2>/dev/null)" || {
    echo "impossible de lire l’état du conteneur; aucune action effectuée" >&2
    return 1
  }
  case "$status" in
    running)
      if sa_up; then echo "passerelle déjà saine sur $SA_URL"; return 0; fi
      echo "conteneur en marche mais passerelle non saine; conteneur conservé. Voir: $0 logs" >&2
      return 1 ;;
    exited|created)
      docker start "$SA_CONTAINER" >/dev/null || { echo "échec du démarrage du conteneur existant; il est conservé" >&2; return 1; } ;;
    *)
      echo "état du conteneur non démarrable ($status); aucune action effectuée" >&2
      return 1 ;;
  esac
  if wait_healthy; then echo "passerelle prête sur $SA_URL"; return 0; fi
  echo "la passerelle existante n’est pas saine; conteneur conservé. Voir: $0 logs" >&2
  return 1
}

start_new() {
  local dk ok mk run_status
  dk="$(sa_extract Deepinfra)"; ok="$(sa_extract Openrouter)"
  [ -n "$dk" ] && [ -n "$ok" ] || { echo "clés introuvables dans $SA_KEYFILE (formats « Deepinfra: … » et « Openrouter: … »)" >&2; return 1; }
  mk="$(sa_master_key)" || { unset dk ok mk; echo "clé maître indisponible" >&2; return 1; }
  DEEPINFRA_API_KEY="$dk" OPENROUTER_API_KEY="$ok" LITELLM_MASTER_KEY="$mk" SA_LOG=/app/state/usage.jsonl \
  docker run -d --name "$SA_CONTAINER" --restart no --user "$(id -u):$(id -g)" \
    -p "127.0.0.1:${SA_PORT}:4000" \
    -e DEEPINFRA_API_KEY -e OPENROUTER_API_KEY -e LITELLM_MASTER_KEY -e SA_LOG \
    -e LITELLM_LOG=ERROR -e LITELLM_TELEMETRY=False -e DISABLE_ADMIN_UI=True -e HOME=/tmp \
    -v "$SA_DIR/litellm:/app/cfg:ro" -v "$SA_STATE:/app/state" \
    --read-only --tmpfs /tmp:rw,size=256m --cap-drop ALL --security-opt no-new-privileges:true \
    --memory 2g --pids-limit 512 \
    "$SA_IMAGE" --config /app/cfg/config.yaml --port 4000 >/dev/null
  run_status=$?
  unset dk ok mk
  [ "$run_status" -eq 0 ] || { echo "échec de création de la passerelle; aucun conteneur n’a été supprimé" >&2; return 1; }
  if wait_healthy; then echo "passerelle prête sur $SA_URL"; return 0; fi
  echo "la passerelle n’a pas démarré; conteneur conservé pour diagnostic. Voir: $0 logs" >&2
  return 1
}

case "${1:-status}" in
  start)
    container_exists; result=$?
    case "$result" in
      0) start_existing; exit $? ;;
      1) start_new; exit $? ;;
      *) exit 1 ;;
    esac ;;
  stop)
    container_exists; result=$?
    case "$result" in
      1) echo "pas de conteneur"; exit 0 ;;
      0) validate_container || exit 1 ;;
      *) exit 1 ;;
    esac
    status="$(docker inspect --format '{{.State.Status}}' "$SA_CONTAINER" 2>/dev/null)" || exit 1
    if [ "$status" = running ]; then
      docker stop "$SA_CONTAINER" >/dev/null && echo "conteneur arrêté et conservé" || { echo "échec de l’arrêt; conteneur conservé" >&2; exit 1; }
    else
      echo "conteneur déjà arrêté et conservé"
    fi ;;
  restart)
    container_exists; result=$?
    case "$result" in
      1) start_new; exit $? ;;
      0) validate_container || exit 1 ;;
      *) exit 1 ;;
    esac
    docker restart "$SA_CONTAINER" >/dev/null || { echo "échec du redémarrage; conteneur conservé" >&2; exit 1; }
    if wait_healthy; then echo "passerelle redémarrée sur $SA_URL"; else echo "passerelle non saine après redémarrage; conteneur conservé" >&2; exit 1; fi ;;
  status)
    container_exists || { result=$?; [ "$result" -eq 1 ] && { echo "arrêtée"; exit 1; }; exit 1; }
    validate_container || exit 1
    if sa_up; then echo "en marche sur $SA_URL"; else echo "conteneur présent mais passerelle non saine"; exit 1; fi ;;
  logs)
    docker logs --tail 80 "$SA_CONTAINER" 2>&1 | sed -E 's/(sk-[A-Za-z0-9_-]{6})[A-Za-z0-9_-]+/\1…/g' ;;
  *) echo "usage: $0 start|stop|status|restart|logs" >&2; exit 2 ;;
esac
