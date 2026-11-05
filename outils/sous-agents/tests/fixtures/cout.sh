#!/usr/bin/env bash
# Fake cost report for offline tests.
set -eu
printf 'rapport de coûts fictif\n'
exit "${FAKE_COUT_RC:-0}"
