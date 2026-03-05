#!/bin/bash
set -euo pipefail

cd ~/apps/personal-portfolio-dataflow

echo "Pulling latest changes..."
git fetch origin main
git reset --hard origin/main

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -e ".[dev,dbt]" --quiet

echo "Loading environment variables..."
set -a && source .env && set +a

echo "Applying schema migrations..."
python scripts/db/init_schema.py

echo "Cleaning up renamed mart tables..."
python scripts/db/migrations/drop_renamed_marts.py

echo "Running dbt models..."
cd dbt && dbt run --profiles-dir . && cd ..

echo "Running dbt tests..."
cd dbt && dbt test --profiles-dir . && cd ..

echo "Loading Toronto data and cleaning deprecated tables..."
python scripts/data/load_toronto_data.py

echo "Production deployment complete!"
