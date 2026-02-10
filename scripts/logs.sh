#!/usr/bin/env bash
# scripts/logs.sh - Follow docker compose logs
#
# Usage:
#   ./scripts/logs.sh           # All services
#   ./scripts/logs.sh postgres  # Specific service
#   ./scripts/logs.sh -n 100    # Last 100 lines

set -euo pipefail

SERVICE="${1:-}"
EXTRA_ARGS="${@:2}"

if [[ -n "$SERVICE" && "$SERVICE" != -* ]]; then
    echo "Following logs for service: $SERVICE"
    docker compose logs -f "$SERVICE" $EXTRA_ARGS
else
    echo "Following logs for all services"
    docker compose logs -f $@
fi
