# Portfolio Dataflow

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-1.9-FF694B?logo=dbt&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![PostGIS](https://img.shields.io/badge/PostGIS-3.4-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-2.0-E92063?logo=pydantic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)

> **Production-grade ELT pipeline for the [leodata.science](https://leodata.science) analytics portfolio.**
> Two domains. Six sources. 45 dbt models. One clean data contract.

Raw data in. Analytics-ready mart tables out. No frontend code here.

---

## 📋 Overview

This repository is the **data backbone** of the leodata.science portfolio. It implements a full ELT pipeline across two analytical domains:

| Step | Technology | What Happens |
|------|-----------|--------------|
| **Extract** | Python + httpx | Public APIs, open datasets, PDF reports, Wikipedia scrapes |
| **Load** | SQLAlchemy 2.0 + Pydantic 2.0 | Validated records persisted to PostgreSQL/PostGIS |
| **Transform** | dbt 1.9 | Raw → staging → intermediate → analytical marts |

The mart tables are the **stable, read-only contract** consumed by the [portfolio webapp](https://gitea.hotserv.cloud/personal-projects/personal-portfolio).

---

## 🚀 Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd app-personal-portfolio-dataflow
make setup          # Creates .venv, installs deps, initialises pre-commit

# 2. Start the database
make docker-up      # PostgreSQL 16 + PostGIS 3.4

# 3. Initialise schema and load data
make db-init        # Create all schemas and tables
make load-data      # Run Toronto + Football ETL pipelines

# 4. Run dbt transformations
make dbt-run        # staging → intermediate → marts
make dbt-test       # Run all 126 dbt tests
```

> **ARM64:** This project targets Raspberry Pi 4 (arm64). Uses `imresamu/postgis:16-3.4` for ARM64 compatibility.

---

## 🏗️ Project Structure

```
app-personal-portfolio-dataflow/
├── dataflow/                   # Core pipeline package
│   ├── toronto/                # Toronto domain (parsers, loaders, schemas, models)
│   └── football/               # Football domain (parsers, loaders, schemas, models)
├── dbt/                        # dbt project: portfolio
│   └── models/
│       ├── shared/             # Cross-domain dimensions
│       ├── staging/            # 1:1 source cleaning — views
│       │   ├── toronto/        # 9 staging models
│       │   └── football/       # 8 staging models
│       ├── intermediate/       # Business logic & joins — views
│       │   ├── toronto/        # 11 intermediate models
│       │   └── football/       # 4 intermediate models
│       └── marts/              # Analytics-ready tables — materialized
│           ├── toronto/        # 9 mart tables  ← webapp reads here
│           └── football/       # 3 mart tables  ← webapp reads here
├── scripts/
│   ├── db/                     # Schema initialisation (init_schema.py)
│   └── data/                   # ETL orchestrators (load_toronto_data.py, load_football_data.py)
├── data/raw/                   # Static files (CMHC Excel, GeoJSON, football CSV submodules)
├── tests/                      # pytest test suite
├── docs/
│   ├── toronto/README.md       # Toronto domain deep dive
│   ├── football/README.md      # Football domain deep dive
│   ├── deployment/             # VPS deployment runbooks (untouched)
│   └── runbooks/               # Operational runbooks
├── CONTRIBUTING.md
├── CHANGELOG.md
└── Makefile
```

---

## 📦 Data Domains

| Domain | Description | Sources | Raw Tables | dbt Models | Marts |
|--------|-------------|:-------:|:----------:|:----------:|:-----:|
| 🏙️ [**Toronto**](docs/toronto/README.md) | Neighbourhood-level urban analytics — housing, demographics, safety, amenities | 4 | 10 | 21 | 9 |
| ⚽ [**Football**](docs/football/README.md) | Global club financials & market values across 7 top leagues | 3 | 9 | 15 | 3 |

---

## 🗄️ Database Schemas

| Schema | Layer | Managed By | Purpose |
|--------|-------|:----------:|---------|
| `raw_toronto` | Raw | SQLAlchemy | Toronto ingestion — direct from APIs and files |
| `raw_football` | Raw | SQLAlchemy | Football ingestion — Transfermarkt, MLSPA, Deloitte |
| `stg_toronto` | Staging | dbt (views) | 1:1 cleaned + typed Toronto source data |
| `stg_football` | Staging | dbt (views) | 1:1 cleaned + typed football source data |
| `int_toronto` | Intermediate | dbt (views) | Toronto business logic, joins, aggregations |
| `int_football` | Intermediate | dbt (views) | Football squad values, transfer flows, financials |
| `mart_toronto` | **Mart** ✅ | dbt (tables) | Final Toronto analytics — webapp reads here |
| `mart_football` | **Mart** ✅ | dbt (tables) | Final football analytics — webapp reads here |
| `public` | Shared | dbt (views) | Cross-domain time dimension |

> **Contract:** The webapp reads only from `mart_toronto.*` and `mart_football.*`. Column renames or drops are breaking changes — coordinate with the webapp repo before shipping.

---

## ⏰ ETL Schedule

Runs as **cron-based jobs** on the VPS. No persistent service process.

| Job | Frequency | Make Target |
|-----|-----------|-------------|
| Toronto full refresh | Weekly (Sun 02:00) | `make load-toronto && make dbt-run` |
| Football full refresh | Weekly (Sun 03:00) | `make load-football && make dbt-run` |
| Full pipeline + tests | Monthly | `make refresh` |

---

## ⚙️ Make Targets

<details>
<summary>Expand full target list</summary>

| Target | Description |
|--------|-------------|
| `make setup` | Create `.venv`, install deps, init pre-commit |
| `make docker-up` | Start PostgreSQL 16 + PostGIS 3.4 |
| `make docker-down` | Stop containers |
| `make local-dev` | Docker + db-init + pgweb (full dev stack) |
| `make db-init` | Initialise all schemas and tables |
| `make db-reset` | ⚠️ Drop and recreate database (destructive) |
| `make load-toronto` | Run Toronto ETL pipeline (includes dbt) |
| `make load-football` | Run Football ETL pipeline (includes dbt) |
| `make load-data` | Run both ETL pipelines |
| `make refresh` | Full pipeline: load-data + dbt-test |
| `make dbt-run` | Execute all dbt models |
| `make dbt-test` | Run all dbt tests |
| `make dbt-docs` | Generate + serve dbt documentation |
| `make test` | Run pytest |
| `make test-cov` | Run pytest with coverage |
| `make lint` | Run ruff linter |
| `make format` | Run ruff formatter |
| `make typecheck` | Run mypy (strict) |
| `make ci` | Full CI: lint + typecheck + test |
| `make pgweb-up` | Start pgweb DB browser (dev only) |

</details>

---

## 🗺️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  SOURCES                                                            │
│                                                                     │
│  Toronto: City of Toronto API · Toronto Police API · CMHC · Stats  │
│  Football: Transfermarkt (Salimt) · MLSPA · Deloitte Money League  │
└─────────────────────────────┬──────────────────────────────────────┘
                              │  Python ETL (parsers → Pydantic → loaders)
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 + PostGIS 3.4                                        │
│                                                                     │
│  raw_toronto (10 tables): dim_neighbourhood · fact_census           │
│                           fact_census_extended · fact_crime          │
│                           fact_amenities · fact_rentals              │
│                           fact_neighbourhood_profile · …             │
│                                                                     │
│  raw_football (9 tables): dim_league · dim_club · dim_player        │
│                           fact_club_season · fact_player_market_value│
│                           fact_transfer · fact_mls_salary · …        │
└─────────────────────────────┬──────────────────────────────────────┘
                              │  dbt: portfolio project
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  TRANSFORMATION (45 dbt models)                                     │
│                                                                     │
│  staging/*    → 1:1 cleaning, typing, renaming (views)             │
│  intermediate/* → business logic, joins, aggregations (views)      │
│  marts/*      → analytics-ready tables (materialized)              │
└─────────────────────────────┬──────────────────────────────────────┘
                              │  Read-only contract
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  app-personal-portfolio (webapp)                                     │
│  Queries mart_toronto.* and mart_football.* — never writes          │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Links

| Resource | |
|----------|-|
| 🏙️ Toronto domain docs | [docs/toronto/README.md](docs/toronto/README.md) |
| ⚽ Football domain docs | [docs/football/README.md](docs/football/README.md) |
| 🚀 VPS deployment | [docs/deployment/vps-deployment.md](docs/deployment/vps-deployment.md) |
| 🐘 Shared PostgreSQL | [docs/deployment/shared-postgres.md](docs/deployment/shared-postgres.md) |
| 🛠️ Adding a domain | [docs/runbooks/adding-domain.md](docs/runbooks/adding-domain.md) |
| 📝 Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 📜 Changelog | [CHANGELOG.md](CHANGELOG.md) |
| 🌐 Live portfolio | [leodata.science](https://leodata.science) |

---

*v0.5.0 · Data pipeline only — no frontend · Updated February 2026*
