# Portfolio Data Pipeline

[![CI](https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/actions/workflows/ci.yml/badge.svg)](https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![dbt 1.9+](https://img.shields.io/badge/dbt-1.9+-orange.svg)](https://www.getdbt.com/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![PostGIS 3.4](https://img.shields.io/badge/PostGIS-3.4-4DB33D.svg)](https://postgis.net/)

> Production-grade ETL/ELT pipeline. Two domains, six sources, 43 dbt models, one clean data contract.

This is the **data-only** backend for the [personal-portfolio](https://gitea.hotserv.cloud/personal-projects/personal-portfolio) analytics platform. It ingests raw data from external APIs and files, validates with Pydantic, persists to PostgreSQL/PostGIS, and transforms through a full dbt model layer into analytics-ready mart tables consumed by the webapp.

**No frontend code lives here.** Raw data in. Clean marts out.

---

## Domains

| Domain | Status | Raw Tables | dbt Models | Notes |
|--------|--------|:----------:|:----------:|-------|
| **Toronto Neighbourhood Analysis** | ✅ Production | 11 | 25 | 158 neighbourhoods, 2016 + 2021 census |
| **Football Analytics** | ✅ Production | 8 | 18 | 7 leagues, transfers, market values, financials |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  SOURCES                                                                      │
│                                                                               │
│  Toronto: City of Toronto API · Toronto Police API · CMHC · Statistics Canada │
│  Football: Transfermarkt (Salimt) · MLSPA · Deloitte Money League             │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │  Python ETL (parsers → loaders)
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  PostgreSQL + PostGIS                                                         │
│                                                                               │
│  raw_toronto: dim_neighbourhood · dim_cmhc_zone · fact_census                │
│               fact_census_extended · fact_crime · fact_amenities              │
│               fact_rentals · fact_neighbourhood_profile                       │
│                                                                               │
│  raw_football: dim_league · dim_club · dim_player                             │
│                fact_player_market_value · fact_transfer · fact_club_season    │
│                fact_mls_salary · fact_club_finance                            │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │  dbt: portfolio project
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  TRANSFORMATION                                                               │
│                                                                               │
│  stg_*   →  1:1 source cleaning, typed, ready for logic                      │
│  int_*   →  business logic, joins, aggregations, profile pivots              │
│  mart_*  →  analytics-ready tables (read-only contract with webapp)          │
└──────────────────────────┬───────────────────────────────────────────────────┘
                           │  PostgreSQL (shared instance)
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  CONSUMER: personal-portfolio webapp                                          │
│  Read-only queries to mart_toronto.* and mart_football.*                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Toronto Neighbourhood Analysis

The primary domain. Comprehensive socioeconomic, housing, safety, amenity, and demographic intelligence across Toronto's 158 official neighbourhoods.

**Sources:**
- **City of Toronto Open Data Portal** — neighbourhood boundaries, census profiles, amenity counts
- **Toronto Police Service API** — crime statistics by neighbourhood
- **CMHC Rental Market Survey** — rental market data (annual, zone grain)
- **Statistics Canada XLSX** — 55+ extended scalar census indicators per neighbourhood

**Data Volume:**
- 158 neighbourhoods with PostGIS boundaries (SRID 4326)
- 2021 census data; 2016 census with CPI-imputed income values
- 22 community profile categories (immigration, languages, ethnic origin, housing type, commute, and more)
- 108,000+ community profile rows
- 4,424 neighbourhood-grain rental rows (area-weighted disaggregation from CMHC zones)

### Toronto Mart Tables

| Mart | Grain | Columns | Purpose |
|------|-------|:-------:|---------|
| `mart_neighbourhood_overview` | neighbourhood | ~20 | Composite livability scores |
| `mart_neighbourhood_foundation` | neighbourhood × year | 65+ | Cross-domain scalar base (demographics, income, housing costs, labour, education) |
| `mart_neighbourhood_housing` | neighbourhood × year | 75+ | Housing metrics, dwelling/bedroom/construction pivots, shelter costs, fit scores |
| `mart_neighbourhood_housing_rentals` | neighbourhood × bedroom × year | ~10 | CMHC rentals disaggregated to neighbourhood grain |
| `mart_neighbourhood_demographics` | neighbourhood × year | 45+ | Income, age, population, diversity indices, profile summary |
| `mart_neighbourhood_safety` | neighbourhood × year | ~15 | Crime rate calculations by type |
| `mart_neighbourhood_amenities` | neighbourhood | 35+ | Amenity scores, commute pivots, car dependency index |
| `mart_neighbourhood_profile` | neighbourhood × category × subcategory | 13 | Community profile breakdown with geometry |

---

## Football Analytics

Football market intelligence across 7 major European leagues. Player market values, transfer history, club season performance, MLS salaries, and Deloitte revenue data.

**Sources:**
- **Transfermarkt** (via Salimt API) — clubs, players, transfers, market value snapshots
- **MLSPA** — MLS player salary data
- **Deloitte Money League** (Wikipedia) — club annual revenue

**Scope:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Eredivisie, MLS

### Football Mart Tables

| Mart | Purpose |
|------|---------|
| `mart_football_club_rankings` | Club rankings, squad values, season performance, financials |
| `mart_football_club_deep_dive` | Deep-dive per-club player and transfer analysis |
| `mart_football_league_comparison` | Cross-league comparison (7 in-scope leagues) |

---

## Quick Start

### Local Development

```bash
# Clone and install
git clone https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow.git
cd personal-portfolio-dataflow
make setup

# Start PostgreSQL + PostGIS
make docker-up

# Initialize schema and load data
make db-init
make load-toronto
make load-football  # optional

# Run dbt transformations
make dbt-run
make dbt-test
```

### One-Command Dev Environment

```bash
make local-dev  # Docker + db-init + pgweb
```

Then load data: `make load-toronto && make dbt-run`

---

## Project Structure

```
.
├── dataflow/                       # Core ETL package
│   ├── config.py                   # Database connection
│   ├── errors/                     # Custom exceptions
│   ├── toronto/                    # Toronto domain
│   │   ├── parsers/                # API + XLSX extraction
│   │   │   ├── toronto_open_data.py
│   │   │   ├── toronto_police.py
│   │   │   ├── cmhc.py, cmhc_excel.py, statcan_cmhc.py
│   │   │   └── geo.py
│   │   ├── loaders/                # Database persistence
│   │   │   ├── dimensions.py, census.py, census_extended_loader.py
│   │   │   ├── profile_loader.py, crime.py, amenities.py
│   │   │   └── cmhc.py, cmhc_crosswalk.py, base.py
│   │   ├── schemas/                # Pydantic validation models
│   │   │   ├── neighbourhood.py, dimensions.py, census_extended.py
│   │   │   ├── profile.py, amenities.py, cmhc.py
│   │   └── models/                 # SQLAlchemy ORM (raw_toronto schema)
│   │       ├── dimensions.py, facts.py
│   │       ├── census_extended.py, profile.py
│   └── football/                   # Football domain
│       ├── parsers/                # Transfermarkt, MLSPA, Deloitte parsers
│       ├── loaders/                # Football data loaders
│       ├── schemas/                # Pydantic models (salimt, mlspa, deloitte)
│       └── models/                 # SQLAlchemy ORM (raw_football schema)
│
├── dbt/                            # dbt project: portfolio
│   └── models/
│       ├── shared/                 # Cross-domain: stg_dimensions__time
│       ├── staging/
│       │   ├── toronto/            # 8 staging models
│       │   └── football/           # 8 staging models
│       ├── intermediate/
│       │   ├── toronto/            # 11 intermediate models
│       │   └── football/           # 4 intermediate models
│       └── marts/
│           ├── toronto/            # 8 mart tables
│           └── football/           # 3 mart tables
│
├── scripts/
│   ├── db/                         # Schema initialization
│   └── data/                       # ETL orchestration scripts
│       ├── load_toronto_data.py
│       ├── load_football_data.py
│       └── xlsx_diagnostic.py
│
├── data/                           # Raw data files (CMHC Excel, GeoJSON, etc.)
├── docs/                           # Documentation
├── notebooks/                      # Exploratory Jupyter notebooks
└── tests/                          # pytest test suite
```

---

## dbt Model Catalog

43 models across 3 layers and 2 domains.

### Staging Layer — 1:1 source cleaning, typed

**Toronto (stg_toronto schema):**

| Model | Source |
|-------|--------|
| `stg_toronto__neighbourhoods` | `raw_toronto.dim_neighbourhood` |
| `stg_toronto__census` | `raw_toronto.fact_census` |
| `stg_toronto__census_extended` | `raw_toronto.fact_census_extended` |
| `stg_toronto__profiles` | `raw_toronto.fact_neighbourhood_profile` |
| `stg_toronto__crime` | `raw_toronto.fact_crime` |
| `stg_toronto__amenities` | `raw_toronto.fact_amenities` |
| `stg_cmhc__rentals` | `raw_toronto.fact_rentals` |
| `stg_cmhc__zone_crosswalk` | `raw_toronto.bridge_cmhc_neighbourhood` |

**Football (stg_football schema):**

| Model | Source |
|-------|--------|
| `stg_football__dim_league` | `raw_football.dim_league` |
| `stg_football__dim_club` | `raw_football.dim_club` |
| `stg_football__dim_player` | `raw_football.dim_player` |
| `stg_football__fact_player_market_value` | `raw_football.fact_player_market_value` |
| `stg_football__fact_transfer` | `raw_football.fact_transfer` |
| `stg_football__fact_club_season` | `raw_football.fact_club_season` |
| `stg_football__fact_mls_salary` | `raw_football.fact_mls_salary` |
| `stg_football__fact_club_finance` | `raw_football.fact_club_finance` |

**Shared:**

| Model | Purpose |
|-------|---------|
| `stg_dimensions__time` | Monthly time dimension (cross-domain) |

### Intermediate Layer — business logic, joins, aggregations

**Toronto (int_toronto schema):**

| Model | Purpose |
|-------|---------|
| `int_neighbourhood__foundation` | Cross-domain foundation with 50+ extended census scalars; central hub for downstream marts |
| `int_neighbourhood__housing` | Housing metrics with dwelling/bedroom/construction profile pivot CTEs |
| `int_neighbourhood__amenity_scores` | Amenity accessibility scores with commute pivot CTEs and car dependency index |
| `int_neighbourhood__crime_summary` | Crime rate calculations |
| `int_neighbourhood__demographics` | ⚠️ Soft-deprecated; reads from foundation; kept for backward compat |
| `int_rentals__annual` | Annual CMHC rental aggregations |
| `int_rentals__neighbourhood_allocated` | Zone rentals disaggregated to neighbourhood grain (area-weighted) |
| `int_rentals__toronto_cma` | Toronto CMA rental aggregates |
| `int_toronto__neighbourhood_profile` | Profile aggregations with MAX(category_total) denominator |
| `int_census__toronto_cma` | CMA-level census aggregates |
| `int_year_spine` | Year dimension helper |

**Football (int_football schema):**

| Model | Purpose |
|-------|---------|
| `int_football__club_league_bridge` | Club-league associations (resolves NULL league_id gaps) |
| `int_football__league_financials` | League-level financial aggregations |
| `int_football__squad_values` | Squad market value calculations |
| `int_football__transfer_flows` | Transfer network flows between clubs |

### Mart Layer — analytics-ready tables (read-only contract with webapp)

See **Toronto Mart Tables** and **Football Mart Tables** above.

---

## Tech Stack

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| Database | PostgreSQL | 16.x | `imresamu/postgis:16-3.4` for ARM64 |
| Geospatial | PostGIS | 3.4 | All geometries SRID 4326 |
| Validation | Pydantic | 2.x | 2.0 API only |
| ORM | SQLAlchemy | 2.x | 2.0-style API only |
| Transformation | dbt-postgres | 1.9+ | Project: `portfolio` |
| Data Processing | Pandas, GeoPandas, Shapely | Latest | Spatial operations |
| Testing | pytest | Latest | `tests/` directory |
| Linting | ruff | 0.8+ | Replaces flake8 + black + isort |
| Type Checking | mypy | 1.14+ | Strict mode |
| Python | 3.11+ | Via pyenv | `.python-version = 3.11` |

---

## Development

### Makefile Reference

```bash
# Setup & Database
make setup          # Install deps, create .env, init pre-commit
make docker-up      # Start PostgreSQL + PostGIS
make docker-down    # Stop containers
make db-init        # Initialize database schema
make db-reset       # Drop and recreate database (DESTRUCTIVE)

# Data Loading
make load-data      # Load all domains
make load-toronto   # Load Toronto data from APIs
make load-football  # Load football data

# dbt
make dbt-run        # Run all dbt models
make dbt-test       # Run dbt tests
make dbt-docs       # Generate and serve dbt docs (http://localhost:8080)

# Quality Checks
make test           # Run pytest
make lint           # Run ruff linter
make format         # Run ruff formatter
make typecheck      # Run mypy
make ci             # Run all checks (lint + typecheck + test)

# Development Tools
make pgweb-up       # Start pgweb database browser (dev only)
make pgweb-down     # Stop pgweb
make local-dev      # Start Docker + db-init + pgweb
```

### Database Browser (pgweb)

A lightweight read-only web UI for exploring the database during development.

```bash
make pgweb-up
```

- **Localhost**: http://localhost:8081
- **LAN**: `http://<hostname>.local:8081`

Runs as `portfolio_reader` (SELECT-only on `mart_*` tables). Never runs in production.

### dbt Commands

```bash
# Run specific model
cd dbt && dbt run --profiles-dir . --select mart_neighbourhood_foundation

# Run domain-specific models
cd dbt && dbt run --profiles-dir . --select staging.toronto+
cd dbt && dbt run --profiles-dir . --select marts.football+

# Full refresh (rebuilds all tables)
cd dbt && dbt run --profiles-dir . --full-refresh

# Impact analysis before changes
cd dbt && dbt run --profiles-dir . --select +int_neighbourhood__foundation+

# Tests
make dbt-test
```

**Always `dbt parse` before `dbt run`** to catch syntax errors early:

```bash
cd dbt && dbt parse --profiles-dir .
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio
POSTGRES_USER=portfolio
POSTGRES_PASSWORD=<secure>
POSTGRES_DB=portfolio

# Logging
LOG_LEVEL=INFO
```

---

## Deployment

### VPS Deployment (Cron-Based ETL)

This pipeline deploys as **scheduled ETL jobs**, not a containerized service.

```
/opt/apps/portfolio-dataflow/
├── .venv/              # Python virtual environment
├── dataflow/           # ETL source code
├── dbt/                # dbt transformation project
├── scripts/            # ETL orchestration scripts
└── .env                # Environment configuration
```

**Recommended cron schedule:**

```bash
0 2 * * *   make load-toronto   # Daily data refresh at 2 AM
0 3 * * *   make dbt-run        # Transform after load at 3 AM
0 4 * * *   make dbt-test       # Validate transformations at 4 AM
0 1 * * 0   make db-reset       # Weekly full refresh Sunday 1 AM
```

Full guide: [docs/deployment/vps-deployment.md](docs/deployment/vps-deployment.md)

### CI/CD

Gitea Actions:
- **ci.yml** — Lint and test on push to `development`, `staging`, `main`
- **deploy-staging.yml** — Deploy on push to `staging`
- **deploy-production.yml** — Deploy on push to `main`

---

## Documentation

| Document | Purpose |
|----------|---------|
| [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | Complete schema reference (raw + mart tables) |
| [vps-deployment.md](docs/deployment/vps-deployment.md) | Production deployment runbook |
| [shared-postgres.md](docs/deployment/shared-postgres.md) | Multi-database PostgreSQL setup |
| [deployment-checklist.md](docs/deployment/deployment-checklist.md) | Pre-deploy checklist |
| [PROJECT_REFERENCE.md](docs/PROJECT_REFERENCE.md) | Architecture reference and sprint history |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Contributor guide (adding domains, models, parsers) |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CLAUDE.md](CLAUDE.md) | AI assistant context and code conventions |

---

## Related Repositories

- **Webapp**: [personal-portfolio](https://gitea.hotserv.cloud/personal-projects/personal-portfolio) — Dash visualization app consuming mart tables
- **Live**: [leodata.science](https://leodata.science)

---

## License

MIT — Leo Miranda
