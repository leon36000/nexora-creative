#!/usr/bin/env bash
# Fake gateway: records the call, never contacts or restarts a service.
set -eu
printf '%s\n' "${1:-missing}" >> "${FAKE_GATEWAY_LOG:?}"
exit "${FAKE_GATEWAY_RC:-0}"
