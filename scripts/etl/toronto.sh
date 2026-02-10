#!/usr/bin/env bash
# scripts/etl/toronto.sh - Run Toronto data pipeline
#
# Usage:
#   ./scripts/etl/toronto.sh --full        # Complete reload of all data
#   ./scripts/etl/toronto.sh --incremental # Only new data since last run
#   ./scripts/etl/toronto.sh               # Default: incremental
#
# Logs are written to .dev/logs/etl/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.dev/logs/etl"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/toronto_${TIMESTAMP}.log"

MODE="${1:---incremental}"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting Toronto ETL pipeline (mode: $MODE)"
log "Log file: $LOG_FILE"

cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    log "Activated virtual environment"
fi

case "$MODE" in
    --full)
        log "Running FULL data reload..."

        log "Step 1/4: Parsing neighbourhood/geographic data..."
        python -m portfolio_app.toronto.parsers.geo 2>&1 | tee -a "$LOG_FILE"

        log "Step 2/4: Parsing Toronto Open Data (census, amenities)..."
        python -m portfolio_app.toronto.parsers.toronto_open_data 2>&1 | tee -a "$LOG_FILE"

        log "Step 3/4: Parsing crime data..."
        python -m portfolio_app.toronto.parsers.toronto_police 2>&1 | tee -a "$LOG_FILE"

        log "Step 4/4: Running dbt transformations..."
        cd dbt && dbt run --full-refresh --profiles-dir . 2>&1 | tee -a "$LOG_FILE" && cd ..
        ;;

    --incremental)
        log "Running INCREMENTAL update..."

        log "Step 1/2: Checking for new data..."
        # Add incremental logic here when implemented

        log "Step 2/2: Running dbt transformations..."
        cd dbt && dbt run --profiles-dir . 2>&1 | tee -a "$LOG_FILE" && cd ..
        ;;

    *)
        log "ERROR: Unknown mode '$MODE'. Use --full or --incremental"
        exit 1
        ;;
esac

log "Toronto ETL pipeline completed successfully"
log "Full log available at: $LOG_FILE"
