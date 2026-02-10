# Portfolio Dataflow - VPS Deployment Checklist

## ✅ Pre-Deployment Verification

- [x] **PostGIS enabled** in VPS PostgreSQL (custom image: `hotserv/postgres:pg15-postgis`)
- [ ] **SSH access** to VPS: `ssh lmiranda@hotserv.tailc9b278.ts.net`
- [ ] **Git access** to Gitea: `ssh://git@hotserv.tailc9b278.ts.net:2222`

---

## 🚀 Automated Deployment (Recommended)

Run this from your local machine (hotport):

```bash
cd ~/repositories/personal/app-personal-portfolio-dataflow
./deploy-to-vps.sh
```

The script will automatically:
1. ✅ Verify PostGIS installation
2. ✅ Create `portfolio` database with PostGIS extensions
3. ✅ Clone repository to `$HOME/apps/personal-portfolio-dataflow`
4. ✅ Create Python venv and install dependencies
5. ✅ Configure `.env` with shared PostgreSQL credentials
6. ✅ Initialize database schema
7. ✅ Load Toronto data from APIs
8. ✅ Run dbt models and tests
9. ✅ Verify installation
10. ✅ Set up cron jobs for automated ETL

---

## 📋 Manual Deployment (Alternative)

If you prefer to run steps manually:

### 1. Verify PostGIS

```bash
ssh lmiranda@hotserv.tailc9b278.ts.net
docker exec hotserv_postgres psql -U postgres -c "SELECT PostGIS_version();"
```

### 2. Create Portfolio Database

```bash
docker exec hotserv_postgres psql -U postgres <<EOF
CREATE DATABASE portfolio;
\c portfolio
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS raw_toronto;
CREATE SCHEMA IF NOT EXISTS stg_toronto;
CREATE SCHEMA IF NOT EXISTS int_toronto;
CREATE SCHEMA IF NOT EXISTS mart_toronto;
EOF
```

### 3. Clone Repository

```bash
cd $HOME/apps
git clone ssh://git@hotserv.tailc9b278.ts.net:2222/personal-projects/personal-portfolio-dataflow.git
cd personal-portfolio-dataflow
```

### 4. Setup Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,dbt]"
```

### 5. Configure Environment

```bash
cat > .env <<'EOF'
# Use localhost since running on VPS host, not inside Docker container
DATABASE_URL=postgresql://postgres:h0ts3rv_db_secure_2024@localhost:5432/portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=h0ts3rv_db_secure_2024
POSTGRES_DB=portfolio
LOG_LEVEL=INFO
EOF
```

### 6. Initialize and Load Data

```bash
source .venv/bin/activate

# Initialize database schema
python scripts/db/init_schema.py

# Load Toronto data
python scripts/data/load_toronto_data.py
python scripts/data/seed_amenity_data.py

# Run dbt models
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .
```

### 7. Setup Cron Jobs

```bash
sudo mkdir -p /var/log/portfolio-dataflow
sudo chown $USER:$USER /var/log/portfolio-dataflow

crontab -e
```

Add these lines:

```cron
# Portfolio Dataflow - Toronto Data ETL
0 2 * * * cd $HOME/apps/personal-portfolio-dataflow && $HOME/apps/personal-portfolio-dataflow/.venv/bin/python scripts/data/load_toronto_data.py >> /var/log/portfolio-dataflow/etl.log 2>&1
0 3 * * * cd $HOME/apps/personal-portfolio-dataflow/dbt && $HOME/apps/personal-portfolio-dataflow/.venv/bin/dbt run --profiles-dir . >> /var/log/portfolio-dataflow/dbt.log 2>&1
0 4 * * * cd $HOME/apps/personal-portfolio-dataflow/dbt && $HOME/apps/personal-portfolio-dataflow/.venv/bin/dbt test --profiles-dir . >> /var/log/portfolio-dataflow/dbt-test.log 2>&1
```

---

## 🔍 Post-Deployment Verification

### Check Database

```bash
docker exec hotserv_postgres psql -U postgres -d portfolio -c "\dt raw_toronto.*"
docker exec hotserv_postgres psql -U postgres -d portfolio -c "\dt mart_toronto.*"
docker exec hotserv_postgres psql -U postgres -d portfolio -c "SELECT COUNT(*) FROM raw_toronto.dim_neighbourhood;"
```

Expected: 158 neighbourhoods

### Check Logs

```bash
tail -f /var/log/portfolio-dataflow/etl.log
tail -f /var/log/portfolio-dataflow/dbt.log
```

### Check Cron Jobs

```bash
crontab -l | grep portfolio
```

---

## 📊 Architecture Overview

```
VPS: $HOME/apps/
├── personal-portfolio-dataflow/    # This application (Python venv + cron)
│   ├── .venv/                      # Python virtual environment
│   ├── dataflow/                   # Data pipeline code
│   ├── dbt/                        # dbt transformations
│   ├── scripts/                    # ETL scripts
│   └── .env                        # Environment config
│
└── (from serv-hotserv-apps repo)
    └── PostgreSQL Container
        └── Database: portfolio     # Shared with other services
            ├── Schema: raw_toronto
            ├── Schema: stg_toronto
            ├── Schema: int_toronto
            └── Schema: mart_toronto
```

**Key Points:**
- ✅ Uses existing `hotserv_postgres` container (no new containers)
- ✅ Creates new `portfolio` database alongside `gitea_db`, `wikijs_db`, etc.
- ✅ Runs as Python venv with cron-based ETL jobs
- ✅ Completely isolated from other VPS services

---

## 🔧 Useful Commands

### Database Access

```bash
# Connect to portfolio database
docker exec -it hotserv_postgres psql -U postgres -d portfolio

# List all databases
docker exec hotserv_postgres psql -U postgres -c "\l"

# Check database size
docker exec hotserv_postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('portfolio'));"
```

### Application Management

```bash
# Manual data refresh
cd $HOME/apps/personal-portfolio-dataflow
source .venv/bin/activate
python scripts/data/load_toronto_data.py
python scripts/data/seed_amenity_data.py

# Run dbt models
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .

# Run tests
pytest

# Update deployment
git pull origin main
pip install -e ".[dev,dbt]"
python scripts/db/init_schema.py  # Apply any schema changes
```

### Monitoring

```bash
# Watch ETL logs live
tail -f /var/log/portfolio-dataflow/etl.log

# Check cron execution
sudo tail -f /var/log/syslog | grep CRON

# Check recent errors
grep -i error /var/log/portfolio-dataflow/*.log
```

---

## 🚨 Troubleshooting

### Can't connect to database

**Check PostgreSQL is running:**
```bash
docker ps | grep hotserv_postgres
```

**Test connection:**
```bash
docker exec hotserv_postgres psql -U postgres -d portfolio -c "SELECT 1;"
```

### PostGIS not found

**Enable PostGIS extension:**
```bash
docker exec hotserv_postgres psql -U postgres -d portfolio -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Cron jobs not running

**Check cron service:**
```bash
sudo systemctl status cron
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog | tail -20
```

**Test manually:**
```bash
cd $HOME/apps/personal-portfolio-dataflow
source .venv/bin/activate
python scripts/data/load_toronto_data.py
```

---

## 📚 Related Documentation

- **VPS Apps Repository**: `ssh://git@hotserv.tailc9b278.ts.net:2222/bandit-den/serv-hotserv-apps.git`
- **Deployment Guide**: `docs/deployment/vps-deployment.md`
- **Shared PostgreSQL**: `docs/deployment/shared-postgres.md`
- **Database Schema**: `docs/DATABASE_SCHEMA.md`

---

**Last Updated**: 2026-02-10
