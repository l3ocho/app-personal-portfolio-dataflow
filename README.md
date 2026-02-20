# Portfolio Data Pipeline

[![CI](https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/actions/workflows/ci.yml/badge.svg)](https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/actions)

**Data engineering pipeline for analytics projects.** This repository contains the ETL/ELT infrastructure that powers the portfolio analytics platform.

## Purpose

This is a **data-only** repository focused on:
- Data acquisition from external sources (APIs, files)
- Data validation and transformation
- Database persistence and schema management
- Analytics-ready data preparation via dbt

**Frontend/Visualization**: See [personal-portfolio](https://gitea.hotserv.cloud/personal-projects/personal-portfolio) (separate repository)

## Architecture

```mermaid
flowchart LR
    subgraph Sources
        A1[City of Toronto API]
        A2[Toronto Police API]
        A3[CMHC Data]
    end

    subgraph ETL["ETL Pipeline (This Repo)"]
        B1[Parsers]
        B2[Loaders]
    end

    subgraph Database
        C1[(PostgreSQL/PostGIS)]
        C2[dbt Models]
    end

    subgraph Consumer["Portfolio Webapp"]
        D1[Query Services]
        D2[Visualizations]
    end

    A1 & A2 & A3 --> B1 --> B2 --> C1 --> C2 --> D1 --> D2
```

**Pipeline Stages:**
1. **Sources**: External APIs and data files
2. **ETL**: Python parsers extract and validate data; loaders persist to PostgreSQL
3. **Transformation**: dbt models transform raw → staging → intermediate → marts
4. **Consumer**: Webapp reads from mart tables (read-only access)

## Current Projects

### Toronto Neighbourhood Analysis

Comprehensive data pipeline for Toronto's 158 official neighbourhoods:

**Data Sources**:
- City of Toronto Open Data Portal (neighbourhoods, census, amenities)
- Toronto Police Service (crime statistics)
- CMHC Rental Market Survey (rental market data)

**Output Schemas**:
- `raw_toronto.*` - Raw fact and dimension tables
- `stg_toronto.*` - dbt staging views (cleaned, typed)
- `int_toronto.*` - dbt intermediate models (business logic)
- `mart_toronto.*` - Analytics-ready tables for consumption

**dbt Lineage**:
```
raw_toronto.dim_neighbourhood
  └─> stg_toronto__dim_neighbourhood
      └─> int_toronto__neighbourhood_metrics
          └─> mart_toronto.dim_neighbourhood
```

## Quick Start

### Local Development

**Quick Setup (recommended):**
```bash
# Clone repository
git clone https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow.git
cd personal-portfolio-dataflow

# Install dependencies
make setup

# Start everything at once (Docker, database, pgweb)
make local-dev
```

**Step-by-step (if you prefer):**
```bash
make docker-up      # Start PostgreSQL
make db-init        # Initialize database schema
make pgweb-up       # Start pgweb database browser (optional)
make load-toronto   # Load Toronto data
make dbt-run        # Run dbt models
```

**View logs:**
```bash
make docker-logs    # Database logs
make pgweb-logs     # pgweb logs (dev only)
```

### Production Deployment

See [docs/deployment/vps-deployment.md](docs/deployment/vps-deployment.md) for complete VPS deployment guide.

**Summary:**
1. Clone to VPS: `/opt/apps/portfolio-dataflow`
2. Create Python venv and install dependencies
3. Configure `.env` with database connection
4. Initialize database and load data
5. Schedule cron jobs for automated ETL

## Project Structure

```
dataflow/
├── config.py              # Database configuration
├── errors/                # Exception classes
└── toronto/               # Toronto data pipeline
    ├── parsers/           # API data extraction
    ├── loaders/           # Database persistence
    ├── schemas/           # Pydantic validation models
    └── models/            # SQLAlchemy ORM (raw_toronto schema)

dbt/                       # dbt project: portfolio
├── models/
│   ├── shared/            # Cross-domain dimensions (dim_time)
│   ├── staging/toronto/   # Toronto staging models
│   ├── intermediate/toronto/ # Toronto business logic
│   └── marts/toronto/     # Toronto analytical tables

scripts/
├── db/                    # Database initialization
└── data/                  # ETL scripts
    ├── load_toronto_data.py
    └── seed_amenity_data.py

data/                      # Raw data files (CSV, Excel)
docs/
├── deployment/            # Deployment guides
│   ├── vps-deployment.md
│   └── shared-postgres.md
└── project-lessons-learned/
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Validation | Pydantic 2.x |
| ORM | SQLAlchemy 2.x |
| Transformation | dbt-postgres 1.9+ |
| Data Processing | Pandas, GeoPandas, Shapely |
| PDF Parsing | pdfplumber, tabula-py |
| Testing | pytest |
| Python | 3.11+ |

## Development

### Database Browser (pgweb)

pgweb is available for browsing the database during development. It provides a lightweight web interface with read-only access.

**Start pgweb:**
```bash
make pgweb-up
```

**Access pgweb:**
- **From localhost**: http://localhost:8081
- **From LAN** (other devices on your network):
  - mDNS: `http://<hostname>.local:8081` (e.g., `http://raspberrypi.local:8081`)
  - Direct IP: `http://<pi-ip>:8081` (e.g., `http://192.168.1.184:8081`)

**Stop pgweb:**
```bash
make pgweb-down
```

**View logs:**
```bash
make pgweb-logs
```

**Security Notes:**
- pgweb runs with the `portfolio_reader` user (read-only, `SELECT` on `mart_*` tables only)
- pgweb is configured with `--readonly` flag for additional safety
- pgweb is bound to `0.0.0.0` (all network interfaces) for LAN access
- **Only use on trusted home networks** — stop the container on shared/public networks
- pgweb only starts with the `dev` profile and never runs in production

### Makefile Targets

```bash
# Setup & Database
make setup          # Install deps, create .env, init pre-commit
make docker-up      # Start PostgreSQL + PostGIS
make docker-down    # Stop containers
make db-init        # Initialize database schema
make db-reset       # Drop and recreate database (DESTRUCTIVE)

# Development Tools
make pgweb-up       # Start pgweb database browser (dev only)
make pgweb-down     # Stop pgweb
make pgweb-logs     # View pgweb logs

# Data Loading
make load-data      # Load all project data (currently: Toronto)
make load-toronto   # Load Toronto data from APIs

# dbt
make dbt-run        # Run dbt models
make dbt-test       # Run dbt tests
make dbt-docs       # Generate and serve dbt documentation

# Testing & Quality
make test           # Run pytest
make lint           # Run ruff linter
make format         # Run ruff formatter
make typecheck      # Run mypy type checker
make ci             # Run all checks (lint, typecheck, test)
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database Connection
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio
POSTGRES_USER=portfolio
POSTGRES_PASSWORD=<secure>
POSTGRES_DB=portfolio

# Logging
LOG_LEVEL=INFO
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_loaders.py -v
```

## dbt Models

### Model Layers

| Layer | Naming | Purpose |
|-------|--------|---------|
| Staging | `stg_{domain}__{entity}` | 1:1 source mapping, cleaned |
| Intermediate | `int_{domain}__{transform}` | Business logic, joins |
| Marts | `mart_{domain}` | Analytics-ready tables |

### Run Models

```bash
# Run all models
make dbt-run

# Run specific model
cd dbt && dbt run --profiles-dir . --select stg_toronto__dim_neighbourhood

# Run with full refresh
cd dbt && dbt run --profiles-dir . --full-refresh

# Run tests
make dbt-test
```

### Generate Documentation

```bash
make dbt-docs
# Opens browser to http://localhost:8080
```

## Deployment

### VPS Deployment

Complete guide: [docs/deployment/vps-deployment.md](docs/deployment/vps-deployment.md)

**Prerequisites:**
- VPS with Docker + Docker Compose
- PostgreSQL container (see [shared-postgres.md](docs/deployment/shared-postgres.md))
- Python 3.11+

**Deployment model**: Cron-based ETL jobs (not a containerized service)

**Recommended schedule:**
- Daily data refresh: 2 AM
- dbt models: 3 AM (after data load)
- dbt tests: 4 AM
- Weekly full refresh: Sunday 1 AM

### CI/CD

Gitea Actions workflows:
- **ci.yml**: Lint and test on push to development/staging/main
- **deploy-staging.yml**: Deploy to staging on push to staging branch
- **deploy-production.yml**: Deploy to production on push to main branch

## Database Schema

### Toronto Raw Schema

**Dimensions:**
- `raw_toronto.dim_neighbourhood` - 158 neighbourhoods with geometries
- `raw_toronto.dim_time` - Date dimension
- `raw_toronto.dim_cmhc_zone` - CMHC zones (36 zones)

**Facts:**
- `raw_toronto.fact_census` - Census metrics by neighbourhood
- `raw_toronto.fact_crime` - Crime incidents by neighbourhood and date
- `raw_toronto.fact_rentals` - Rental data by CMHC zone and date
- `raw_toronto.fact_amenities` - Points of interest by neighbourhood

### Toronto Mart Schema

- `mart_toronto.dim_neighbourhood` - Enriched neighbourhood dimension
- `mart_toronto.fact_neighbourhood_metrics` - Pre-aggregated metrics
- `mart_toronto.fact_crime_summary` - Crime statistics
- `mart_toronto.fact_housing_metrics` - Housing affordability metrics

See [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) for complete schema documentation.

## Adding New Data Domains

To add a new data domain (e.g., `football`):

1. **Create domain directory**: `dataflow/football/`
2. **Implement parsers**: Extract data from sources
3. **Create schemas**: Pydantic models for validation
4. **Define models**: SQLAlchemy ORM for `raw_football` schema
5. **Build loaders**: Persist data to database
6. **Write dbt models**: `staging/football/`, `marts/football/`
7. **Create load script**: `scripts/data/load_football_data.py`
8. **Add Makefile target**: `make load-football`

## Documentation

- **Deployment**: [docs/deployment/vps-deployment.md](docs/deployment/vps-deployment.md)
- **Deployment Checklist**: [docs/deployment/deployment-checklist.md](docs/deployment/deployment-checklist.md)
- **Shared PostgreSQL**: [docs/deployment/shared-postgres.md](docs/deployment/shared-postgres.md)
- **For Claude Code**: [CLAUDE.md](CLAUDE.md) (AI assistant context)
- **Database Schema**: [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **Lessons Learned**: [docs/project-lessons-learned/INDEX.md](docs/project-lessons-learned/INDEX.md)

## Related Repositories

- **Frontend/Webapp**: [personal-portfolio](https://gitea.hotserv.cloud/personal-projects/personal-portfolio) - Dash app with visualizations
- **Live Site**: [leodata.science](https://leodata.science) (when deployed)

## License

MIT

## Author

Leo Miranda
- GitHub: [leonardomiranda](https://github.com/leonardomiranda)
- Email: contact@leodata.science
