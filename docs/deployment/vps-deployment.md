# VPS Deployment Guide

Complete guide for deploying portfolio-dataflow to a VPS with shared PostgreSQL infrastructure.

## Prerequisites

- VPS with Docker + Docker Compose V2
- Existing PostgreSQL container (see `shared-postgres.md` for multi-database setup)
- Python 3.11+ with venv support
- Git access to repository
- Database named `portfolio` in PostgreSQL
- `make` installed (verify with `make --version`; install with `sudo apt install make -y`)

## Architecture Overview

```
VPS: ~/apps/
├── docker-compose.yml          # Main orchestrator (postgres, gitea, cloudbeaver)
├── gitea/
├── cloudbeaver/
└── personal-portfolio-dataflow/  # This application
    ├── .venv/                    # Python virtual environment
    ├── dataflow/                 # Data pipeline code
    ├── dbt/                      # dbt models
    ├── scripts/                  # ETL scripts
    ├── data/                     # Raw data files
    └── .env                      # Environment configuration
```

**Deployment Model**: Not a containerized service, runs via **cron jobs** for scheduled ETL.

---

## Deployment Steps

### Step 1: Clone Repository

```bash
# Navigate to apps directory
cd /opt/apps  # or ~/apps depending on your setup

# Clone repository
git clone https://gitea.hotserv.cloud/personal-projects/app-personal-portfolio-dataflow.git personal-portfolio-dataflow
cd personal-portfolio-dataflow

# Checkout desired branch
git checkout main  # or staging for staging environment
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Verify Python version (should be 3.11+)
python --version
```

### Step 3: Install Dependencies

```bash
# Install in editable mode with all extras
pip install -e ".[dev,dbt]"

# Verify installation
pip list | grep portfolio-dataflow
```

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**

```bash
# Database Connection
DATABASE_URL=postgresql://postgres:PASSWORD@postgres:5432/portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=portfolio

# Logging
LOG_LEVEL=INFO
```

**Notes:**
- Use `postgres` as hostname (Docker network name)
- Use same credentials as main postgres container
- If using read-only user for webapp, create separate `portfolio_etl` user here

### Step 5: Verify Database Connection

```bash
# Test connection
docker exec -it postgres psql -U postgres -d portfolio -c "SELECT version();"

# Or use psql from host (if installed)
psql $DATABASE_URL -c "SELECT version();"
```

### Step 6: Initialize Database Schema

```bash
# Run schema initialization
make db-init

# Verify tables created
docker exec -it postgres psql -U postgres -d portfolio -c "\dt raw_toronto.*"
```

Expected output:
```
Schema       | Name                  | Type  | Owner
-------------+-----------------------+-------+--------
raw_toronto  | dim_neighbourhood     | table | postgres
raw_toronto  | dim_time              | table | postgres
raw_toronto  | fact_census           | table | postgres
...
```

### Step 7: Load Initial Data

```bash
# Load Toronto data (will take several minutes)
make load-toronto

# Check data loaded
docker exec -it postgres psql -U postgres -d portfolio -c "SELECT COUNT(*) FROM raw_toronto.dim_neighbourhood;"
```

Expected: 158 neighbourhoods

### Step 8: Run dbt Models

```bash
# Run all dbt models
make dbt-run

# Run dbt tests
make dbt-test

# Verify mart tables created
docker exec -it postgres psql -U postgres -d portfolio -c "\dt mart_toronto.*"
```

### Step 9: Verify Installation

```bash
# Run test suite
make test

# Run linter
make lint

# Run type checker
make typecheck

# All checks
make ci
```

---

## Scheduled ETL with Cron

Set up cron jobs for automated data refreshes.

### Create Log Directory

```bash
sudo mkdir -p /var/log/portfolio-dataflow
sudo chown $USER:$USER /var/log/portfolio-dataflow
```

### Configure Cron Jobs

```bash
# Edit crontab
crontab -e
```

**Recommended Schedule:**

```bash
# Portfolio Dataflow - Toronto Data ETL
# Run every day at 2 AM (data refresh)
0 2 * * * cd ~/apps/personal-portfolio-dataflow && ~/apps/personal-portfolio-dataflow/.venv/bin/python scripts/data/load_toronto_data.py >> /var/log/portfolio-dataflow/etl.log 2>&1

# Run dbt models every day at 3 AM (after data loads)
0 3 * * * cd ~/apps/personal-portfolio-dataflow && ~/apps/personal-portfolio-dataflow/.venv/bin/make dbt-run >> /var/log/portfolio-dataflow/dbt.log 2>&1

# Run dbt tests every day at 4 AM (after models run)
0 4 * * * cd ~/apps/personal-portfolio-dataflow && ~/apps/personal-portfolio-dataflow/.venv/bin/make dbt-test >> /var/log/portfolio-dataflow/dbt-test.log 2>&1

# Weekly full refresh (Sundays at 1 AM)
0 1 * * 0 cd ~/apps/personal-portfolio-dataflow && ~/apps/personal-portfolio-dataflow/.venv/bin/make db-reset && ~/apps/personal-portfolio-dataflow/.venv/bin/make load-toronto >> /var/log/portfolio-dataflow/weekly-refresh.log 2>&1
```

**Notes:**
- Use absolute paths to venv executables
- Redirect output to log files
- Stagger job times to avoid conflicts

### Verify Cron Jobs

```bash
# List configured cron jobs
crontab -l

# Monitor cron execution
sudo tail -f /var/log/syslog | grep CRON

# Check ETL logs
tail -f /var/log/portfolio-dataflow/etl.log
```

---

## Monitoring & Maintenance

### Check ETL Status

```bash
# View recent ETL logs
tail -50 /var/log/portfolio-dataflow/etl.log

# Check for errors
grep -i error /var/log/portfolio-dataflow/*.log
```

### Check dbt Status

```bash
# View dbt run logs
tail -50 /var/log/portfolio-dataflow/dbt.log

# Check dbt test failures
grep -i fail /var/log/portfolio-dataflow/dbt-test.log
```

### Database Health

```bash
# Check database size
docker exec postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('portfolio'));"

# Check table sizes
docker exec postgres psql -U postgres -d portfolio -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname IN ('raw_toronto', 'mart_toronto')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Check row counts
docker exec postgres psql -U postgres -d portfolio -c "
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname IN ('raw_toronto', 'mart_toronto')
ORDER BY n_live_tup DESC;
"
```

### Update Deployment

```bash
# Navigate to directory
cd ~/apps/personal-portfolio-dataflow

# Pull latest changes
git fetch origin
git checkout main  # or staging
git pull origin main

# Activate venv
source .venv/bin/activate

# Update dependencies
pip install -e ".[dev,dbt]"

# Run migrations (if any)
make db-init

# Run dbt models
make dbt-run

# Verify
make test
```

---

## Troubleshooting

### ETL Job Not Running

**Check cron is active:**
```bash
sudo systemctl status cron
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog | tail -20
```

**Run manually to test:**
```bash
cd ~/apps/personal-portfolio-dataflow
source .venv/bin/activate
python scripts/data/load_toronto_data.py
```

### Database Connection Errors

**Verify postgres is running:**
```bash
docker compose ps postgres
```

**Test connection:**
```bash
docker exec -it postgres psql -U postgres -d portfolio
```

**Check DATABASE_URL:**
```bash
cd ~/apps/personal-portfolio-dataflow
cat .env | grep DATABASE_URL
```

**Common issues:**
- Wrong password in `.env`
- Database name doesn't exist
- Container not on same network

### dbt Errors

**Check dbt profile:**
```bash
cd ~/apps/personal-portfolio-dataflow/dbt
cat profiles.yml
```

**Run with debug:**
```bash
cd dbt
dbt run --profiles-dir . --debug
```

**Check dbt target directory:**
```bash
ls -la dbt/target/
cat dbt/target/run_results.json
```

### Disk Space Issues

**Check available space:**
```bash
df -h
```

**Clean old logs:**
```bash
# Archive old logs
cd /var/log/portfolio-dataflow
gzip *.log.1 *.log.2 *.log.3

# Keep only last 7 days
find /var/log/portfolio-dataflow -name "*.log" -mtime +7 -delete
```

**Clean Docker:**
```bash
docker system prune -af
```

### Python Dependency Issues

**Recreate virtual environment:**
```bash
cd ~/apps/personal-portfolio-dataflow
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,dbt]"
```

---

## Rollback Procedure

If deployment fails:

```bash
# Navigate to directory
cd ~/apps/personal-portfolio-dataflow

# Revert to previous commit
git log --oneline -5  # Find previous commit hash
git reset --hard <previous-commit-hash>

# Reinstall dependencies
source .venv/bin/activate
pip install -e ".[dev,dbt]"

# Verify
make test
```

---

## Security Checklist

- [ ] `.env` file has secure passwords
- [ ] `.env` file is not committed to git (in `.gitignore`)
- [ ] PostgreSQL not exposed to public internet
- [ ] Only necessary ports open on VPS firewall
- [ ] Cron job logs don't contain sensitive data
- [ ] Database backups scheduled and tested
- [ ] Separate read-only user for webapp (optional but recommended)

---

## Performance Optimization

### Database Indexes

Key indexes are created by `db-init`. Verify:

```sql
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname IN ('raw_toronto', 'mart_toronto')
ORDER BY schemaname, tablename;
```

### dbt Incremental Models

For large datasets, use incremental models:

```yaml
# dbt/models/marts/toronto/mart_example.sql
{{ config(materialized='incremental', unique_key='id') }}
```

### Parallel dbt Runs

Run models in parallel:

```bash
dbt run --profiles-dir . --threads 4
```

---

## Backup Strategy

### Automated Database Backups

Add to crontab:

```bash
# Daily backup at midnight
0 0 * * * docker exec postgres pg_dump -U postgres portfolio | gzip > /opt/backups/portfolio-$(date +\%Y\%m\%d).sql.gz

# Weekly full backup (Sundays at midnight)
0 0 * * 0 docker exec postgres pg_dumpall -U postgres | gzip > /opt/backups/full-backup-$(date +\%Y\%m\%d).sql.gz

# Delete backups older than 30 days
0 1 * * * find /opt/backups -name "portfolio-*.sql.gz" -mtime +30 -delete
```

### Restore from Backup

```bash
# Restore specific database
gunzip -c /opt/backups/portfolio-20260210.sql.gz | docker exec -i postgres psql -U postgres portfolio

# Restore full backup
gunzip -c /opt/backups/full-backup-20260210.sql.gz | docker exec -i postgres psql -U postgres
```

---

## CI/CD Integration

The repository includes Gitea Actions workflows for automated deployment:

- **`ci.yml`**: Runs on push to development/staging/main
- **`deploy-staging.yml`**: Deploys to staging on push to staging branch
- **`deploy-production.yml`**: Deploys to production on push to main branch

Configure Gitea secrets:
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
- `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`

---

## Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## Support

For issues or questions:
- Check logs: `/var/log/portfolio-dataflow/`
- Review Gitea issues: https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/issues
- Check CLAUDE.md in repository root for project-specific guidance
