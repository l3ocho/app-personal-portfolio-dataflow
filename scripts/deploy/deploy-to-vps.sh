#!/bin/bash
set -e

# ==============================================================================
# Portfolio Dataflow - VPS Deployment Script
# ==============================================================================
# This script deploys portfolio-dataflow to your VPS with shared PostgreSQL
# ==============================================================================

echo "======================================================================"
echo "🚀 Portfolio Dataflow VPS Deployment"
echo "======================================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPS_HOST="lmiranda@hotserv.tailc9b278.ts.net"
POSTGRES_CONTAINER="hotserv_postgres"
POSTGRES_USER="postgres"
DB_NAME="portfolio"
APPS_DIR="\$HOME/apps"  # Deploy to user's home directory
DEPLOY_PATH="$APPS_DIR/personal-portfolio-dataflow"
GIT_REPO="ssh://git@hotserv.tailc9b278.ts.net:2222/personal-projects/app-personal-portfolio-dataflow.git"

# Require POSTGRES_PASSWORD to be set in the environment — never hardcode secrets
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo -e "${RED}ERROR: POSTGRES_PASSWORD environment variable is not set.${NC}"
    echo "Export it before running this script:"
    echo "  export POSTGRES_PASSWORD='your_secure_password'"
    exit 1
fi
GIT_BRANCH="${1:-development}"  # Default to development branch, can override with argument

# ==============================================================================
# Step 1: Verify PostGIS Installation
# ==============================================================================
echo -e "${BLUE}Step 1: Verifying PostGIS installation...${NC}"
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -c 'SELECT version();' && docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -c 'SELECT PostGIS_version();' 2>/dev/null || echo 'PostGIS not yet enabled (this is OK)'"
echo -e "${GREEN}✓ PostgreSQL verified${NC}"
echo ""

# ==============================================================================
# Step 2: Create Portfolio Database
# ==============================================================================
echo -e "${BLUE}Step 2: Creating portfolio database and enabling PostGIS...${NC}"

# First, create the database if it doesn't exist
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -tc \"SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'\" | grep -q 1 || docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -c 'CREATE DATABASE $DB_NAME'"

# Then, enable extensions and create schemas
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'CREATE EXTENSION IF NOT EXISTS postgis;'"
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'CREATE EXTENSION IF NOT EXISTS postgis_topology;'"

# Create schemas
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'CREATE SCHEMA IF NOT EXISTS raw_toronto;'"
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'CREATE SCHEMA IF NOT EXISTS stg_toronto;'"
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'CREATE SCHEMA IF NOT EXISTS int_toronto;'"
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'CREATE SCHEMA IF NOT EXISTS mart_toronto;'"

# Verify PostGIS is enabled
ssh $VPS_HOST "docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'SELECT PostGIS_version();'"

echo -e "${GREEN}✓ Database '$DB_NAME' created with PostGIS${NC}"
echo ""

# ==============================================================================
# Step 3: Clone Repository
# ==============================================================================
echo -e "${BLUE}Step 3: Cloning repository to VPS...${NC}"
ssh $VPS_HOST "
    # Create apps directory if it doesn't exist
    mkdir -p $APPS_DIR

    if [ -d '$DEPLOY_PATH/.git' ]; then
        echo 'Repository already exists, pulling latest changes from $GIT_BRANCH...'
        cd $DEPLOY_PATH && git fetch origin && git reset --hard origin/$GIT_BRANCH
    else
        echo 'Cloning repository (branch: $GIT_BRANCH)...'
        # Remove directory if it exists but is not a git repo
        rm -rf $DEPLOY_PATH
        cd $APPS_DIR && git clone -b $GIT_BRANCH $GIT_REPO personal-portfolio-dataflow
    fi
"
echo -e "${GREEN}✓ Repository ready at $DEPLOY_PATH${NC}"
echo ""

# ==============================================================================
# Step 4: Create Python Virtual Environment
# ==============================================================================
echo -e "${BLUE}Step 4: Setting up Python virtual environment...${NC}"
ssh $VPS_HOST "
    cd $DEPLOY_PATH
    if [ ! -d '.venv' ]; then
        echo 'Creating virtual environment...'
        python3 -m venv .venv
    fi
    echo 'Installing dependencies...'
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -e '.[dev,dbt]'
"
echo -e "${GREEN}✓ Virtual environment ready${NC}"
echo ""

# ==============================================================================
# Step 5: Configure Environment
# ==============================================================================
echo -e "${BLUE}Step 5: Creating .env configuration...${NC}"
ssh $VPS_HOST "cat > $DEPLOY_PATH/.env <<'EOF'
# Database Configuration - Shared PostgreSQL
# Use localhost since we're running on VPS host, not inside Docker
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$DB_NAME
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_DB=$DB_NAME

# Logging
LOG_LEVEL=INFO

# Note: DASH_DEBUG and SECRET_KEY removed (frontend-only)
EOF
"
echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# ==============================================================================
# Step 6: Initialize Database Schema
# ==============================================================================
echo -e "${BLUE}Step 6: Initializing database schema...${NC}"
ssh $VPS_HOST "
    cd $DEPLOY_PATH
    source .venv/bin/activate
    python scripts/db/init_schema.py
"
echo -e "${GREEN}✓ Database schema initialized${NC}"
echo ""

# ==============================================================================
# Step 7: Load Toronto Data
# ==============================================================================
echo -e "${BLUE}Step 7: Loading Toronto data (this may take several minutes)...${NC}"
ssh $VPS_HOST "
    cd $DEPLOY_PATH
    source .venv/bin/activate
    python scripts/data/load_toronto_data.py
    python scripts/data/seed_amenity_data.py
"
echo -e "${GREEN}✓ Toronto data loaded${NC}"
echo ""

# ==============================================================================
# Step 8: Run dbt Models
# ==============================================================================
echo -e "${BLUE}Step 8: Running dbt models and tests...${NC}"
ssh $VPS_HOST "
    cd $DEPLOY_PATH
    source .venv/bin/activate
    # Load environment variables
    set -a && source .env && set +a
    # Run dbt
    cd dbt && dbt deps --profiles-dir . && dbt run --profiles-dir . && dbt test --profiles-dir .
"
echo -e "${GREEN}✓ dbt models executed${NC}"
echo ""

# ==============================================================================
# Step 9: Verify Installation
# ==============================================================================
echo -e "${BLUE}Step 9: Verifying installation...${NC}"
ssh $VPS_HOST "
    # Check neighbourhood count
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c 'SELECT COUNT(*) as neighbourhood_count FROM raw_toronto.dim_neighbourhood;'

    # Check mart tables exist
    docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME -c '\dt mart_toronto.*'
"
echo -e "${GREEN}✓ Installation verified${NC}"
echo ""

# ==============================================================================
# Step 10: Setup Cron Jobs
# ==============================================================================
echo -e "${BLUE}Step 10: Setting up cron jobs...${NC}"
ssh $VPS_HOST "
    # Create log directory
    sudo mkdir -p /var/log/portfolio-dataflow
    sudo chown \$USER:\$USER /var/log/portfolio-dataflow

    # Backup existing crontab
    crontab -l > /tmp/crontab.backup 2>/dev/null || true

    # Add cron jobs (if not already present)
    (crontab -l 2>/dev/null | grep -v 'portfolio-dataflow'; cat <<CRONEOF
# Portfolio Dataflow - Toronto Data ETL
# Daily data refresh at 2 AM
0 2 * * * cd $APPS_DIR/personal-portfolio-dataflow && set -a && source .env && set +a && $APPS_DIR/personal-portfolio-dataflow/.venv/bin/python scripts/data/load_toronto_data.py >> /var/log/portfolio-dataflow/etl.log 2>&1

# Run dbt models at 3 AM (after data loads)
0 3 * * * cd $APPS_DIR/personal-portfolio-dataflow && set -a && source .env && set +a && cd dbt && $APPS_DIR/personal-portfolio-dataflow/.venv/bin/dbt run --profiles-dir . >> /var/log/portfolio-dataflow/dbt.log 2>&1

# Run dbt tests at 4 AM
0 4 * * * cd $APPS_DIR/personal-portfolio-dataflow && set -a && source .env && set +a && cd dbt && $APPS_DIR/personal-portfolio-dataflow/.venv/bin/dbt test --profiles-dir . >> /var/log/portfolio-dataflow/dbt-test.log 2>&1
CRONEOF
    ) | crontab -
"
echo -e "${GREEN}✓ Cron jobs configured${NC}"
echo ""

# ==============================================================================
# Deployment Complete
# ==============================================================================
echo "======================================================================"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "======================================================================"
echo ""
echo "📊 Portfolio Dataflow Status:"
echo "  • Database: $DB_NAME"
echo "  • Location: $DEPLOY_PATH"
echo "  • Logs: /var/log/portfolio-dataflow/"
echo ""
echo "🔧 Next Steps:"
echo "  1. Monitor ETL logs: ssh $VPS_HOST 'tail -f /var/log/portfolio-dataflow/etl.log'"
echo "  2. Check database: ssh $VPS_HOST 'docker exec $POSTGRES_CONTAINER psql -U $POSTGRES_USER -d $DB_NAME'"
echo "  3. View cron jobs: ssh $VPS_HOST 'crontab -l'"
echo ""
echo "📚 Documentation: docs/deployment/vps-deployment.md"
echo "======================================================================"
