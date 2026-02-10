#!/usr/bin/env bash
# scripts/run-detached.sh - Start containers and wait for health
#
# Usage:
#   ./scripts/run-detached.sh

set -euo pipefail

TIMEOUT=60
INTERVAL=5

echo "Starting containers in detached mode..."
docker compose up -d

echo "Waiting for services to become healthy..."
elapsed=0

while [ $elapsed -lt $TIMEOUT ]; do
    # Check if postgres is ready
    if docker compose exec -T postgres pg_isready -U portfolio > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"

        # Check if app health endpoint responds (if running)
        if curl -sf http://localhost:8050/health > /dev/null 2>&1; then
            echo "Application health check passed!"
            echo "All services are healthy."
            exit 0
        fi
    fi

    echo "Waiting... ($elapsed/$TIMEOUT seconds)"
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
done

echo "ERROR: Health check timed out after $TIMEOUT seconds"
docker compose ps
exit 1
