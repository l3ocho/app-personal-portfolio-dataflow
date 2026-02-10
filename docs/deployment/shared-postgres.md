# Shared PostgreSQL Architecture

This document describes how to run multiple applications using a single PostgreSQL instance on your VPS.

## Overview

Instead of running separate PostgreSQL containers for each application, we use a single PostgreSQL container with **multiple databases**.

## Architecture

```
VPS Server
├── PostgreSQL Container (postgis/postgis:16-3.4)
│   ├── Database: gitea (for Gitea)
│   ├── Database: cloudbeaver (if needed)
│   └── Database: portfolio (for portfolio-dataflow)
│
├── Gitea (connects to postgres:5432/gitea)
├── CloudBeaver (connects to postgres:5432)
└── Portfolio Dataflow (connects to postgres:5432/portfolio)
```

## Setup Instructions

### Step 1: Upgrade Existing Postgres to PostGIS

If you're already running `postgres:16`, upgrade to `postgis/postgis:16-3.4` to support geospatial data:

**Update your main docker-compose.yml:**

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4  # Changed from postgres:16
    container_name: postgres
    networks:
      - app_network
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d/
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### Step 2: Create Database Initialization Script

Create `init-scripts/create-multiple-databases.sh`:

```bash
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create databases
    CREATE DATABASE gitea;
    CREATE DATABASE portfolio;

    -- Enable PostGIS for portfolio database
    \c portfolio
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;

    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS public;
    CREATE SCHEMA IF NOT EXISTS raw_toronto;
    CREATE SCHEMA IF NOT EXISTS stg_toronto;
    CREATE SCHEMA IF NOT EXISTS int_toronto;
    CREATE SCHEMA IF NOT EXISTS mart_toronto;
EOSQL
```

Make it executable:

```bash
chmod +x init-scripts/create-multiple-databases.sh
```

### Step 3: Restart PostgreSQL

**IMPORTANT**: If databases already exist, the init script won't run. To apply:

**Option A: Preserve existing data (recommended)**

```bash
# Connect to postgres and manually create databases
docker exec -it postgres psql -U postgres

CREATE DATABASE portfolio;
\c portfolio
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

**Option B: Fresh start (destroys all data)**

```bash
docker compose down -v  # WARNING: Deletes all data!
docker compose up -d
```

### Step 4: Update Connection Strings

**Gitea** (no changes needed if already using postgres):
```
DB_TYPE=postgres
DB_HOST=postgres:5432
DB_NAME=gitea
DB_USER=postgres
DB_PASSWD=${POSTGRES_PASSWORD}
```

**Portfolio Dataflow** `.env`:
```bash
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/portfolio
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=portfolio
```

**CloudBeaver**:
- Connect to: `postgres:5432`
- Use existing postgres credentials

## Network Configuration

All applications must be on the same Docker network to access postgres by hostname:

```yaml
networks:
  app_network:
    driver: bridge

services:
  postgres:
    networks:
      - app_network

  gitea:
    networks:
      - app_network

  cloudbeaver:
    networks:
      - app_network
```

## Database Management

### Connect to a specific database:

```bash
# From host
docker exec -it postgres psql -U postgres -d portfolio

# From inside container
docker exec -it postgres bash
psql -U postgres -d portfolio
```

### List all databases:

```bash
docker exec -it postgres psql -U postgres -c "\l"
```

### Check database sizes:

```bash
docker exec -it postgres psql -U postgres -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size FROM pg_database;"
```

## Security Considerations

### Option 1: Single User (Simple)

Use the `postgres` superuser for all applications. Simpler but less secure.

### Option 2: Separate Users (Recommended for Production)

Create separate database users with limited permissions:

```sql
-- Create user for portfolio dataflow
CREATE USER portfolio_etl WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE portfolio TO portfolio_etl;

-- Create read-only user for webapp
CREATE USER portfolio_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE portfolio TO portfolio_readonly;
GRANT USAGE ON SCHEMA public, raw_toronto, stg_toronto, int_toronto, mart_toronto TO portfolio_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public, raw_toronto, stg_toronto, int_toronto, mart_toronto TO portfolio_readonly;
```

## Backup Strategy

Back up individual databases:

```bash
# Backup portfolio database
docker exec postgres pg_dump -U postgres portfolio > portfolio_backup.sql

# Backup gitea database
docker exec postgres pg_dump -U postgres gitea > gitea_backup.sql

# Backup all databases
docker exec postgres pg_dumpall -U postgres > full_backup.sql
```

Restore:

```bash
docker exec -i postgres psql -U postgres portfolio < portfolio_backup.sql
```

## Troubleshooting

### PostGIS extension not available

```sql
-- Check available extensions
SELECT * FROM pg_available_extensions WHERE name LIKE 'postgis%';

-- If missing, you're not using the PostGIS image
-- Upgrade to postgis/postgis:16-3.4
```

### Connection refused from portfolio-dataflow

Check network:

```bash
# Verify both containers are on same network
docker network inspect app_network

# Test connectivity
docker exec portfolio-dataflow-container ping postgres
```

### Database doesn't exist

```bash
# List databases
docker exec postgres psql -U postgres -c "\l"

# Create if missing
docker exec postgres psql -U postgres -c "CREATE DATABASE portfolio;"
```

## Migration Checklist

When migrating from separate postgres containers to shared:

- [ ] Backup all existing databases
- [ ] Update postgres image to PostGIS
- [ ] Create init script for multiple databases
- [ ] Update all application connection strings
- [ ] Verify network configuration
- [ ] Test connections from each application
- [ ] Run portfolio-dataflow initialization
- [ ] Verify dbt models run successfully
- [ ] Update backup scripts for multiple databases
