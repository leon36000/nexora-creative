#!/bin/sh
# Bounded retry for this one CI package-install step; do not use for other commands.
set -eu

attempt=1
while [ "$attempt" -le 3 ]; do
    if apk add --no-cache python3 make g++; then
        if [ "$attempt" -gt 1 ]; then
            printf 'apk add succeeded on attempt %s/3\n' "$attempt"
        fi
        exit 0
    else
        status=$?
    fi

    if [ "$attempt" -eq 3 ]; then
        printf 'apk add --no-cache python3 make g++ failed after 3 attempts (last exit %s)\n' "$status" >&2
        exit "$status"
    fi

    delay=$((attempt * 2))
    printf 'apk add failed on attempt %s/3 (exit %s); retrying in %s seconds\n' \
        "$attempt" "$status" "$delay" >&2
    if sleep "$delay"; then
        :
    else
        sleep_status=$?
        printf 'retry pause failed (exit %s); stopping\n' "$sleep_status" >&2
        exit "$sleep_status"
    fi
    attempt=$((attempt + 1))
done

# The loop exits only through apk success or an explicit non-zero error above.
printf 'internal retry loop error\n' >&2
exit 1
