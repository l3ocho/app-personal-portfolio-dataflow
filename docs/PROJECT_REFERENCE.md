# Project Reference

**Repository**: `personal-projects/app-personal-portfolio-dataflow`
**Gitea**: `gitea.hotserv.cloud`
**Owner**: Leo Miranda
**Status**: Sprint 14 complete — Toronto Restructure Phases 1–3 merged to `development`
**Last Updated**: February 2026

---

## Overview

This is a **data-only ETL/ELT pipeline**. No frontend code lives here. The pipeline ingests raw data from external APIs and files, validates with Pydantic, persists to PostgreSQL/PostGIS, and transforms via 43 dbt models into analytics-ready mart tables. The webapp (`personal-portfolio`) consumes the marts read-only.

**Scope boundary:**
- **This repo**: raw data → database → dbt marts
- **Webapp repo**: mart queries → Dash visualizations → user interface

---

## Sprint History

| Sprint | Phase | Completed | Deliverables |
|--------|-------|-----------|--------------|
| Sprint 1–6 | Foundation | Jan 2026 | Repo setup, Docker, PostgreSQL + PostGIS, initial data model |
| Sprint 7–9 | Dashboard (legacy) | Jan 2026 | Combined repo era — frontend + data co-located |
| Sprint 10 | Dataflow Separation | Feb 2026 | Removed ~7,000 lines of frontend code; data-only pipeline established; renamed `portfolio_app` → `dataflow` |
| Sprint 12 | Toronto Phase 1: Raw Layer | Feb 11, 2026 | `fact_census_extended`, 22 profile categories, label fixes, constraint fixes |
| Sprint 13 | Toronto Phase 2: dbt Layer | Feb 18, 2026 | `int_neighbourhood__foundation`, `stg_toronto__census_extended`, denominator bug fix |
| Sprint 14 | Toronto Phase 3: Mart Layer | Feb 23, 2026 | 3 new marts, 2 expanded marts, 50+ new columns; football pipeline integrated |

---

## Active Domains

### Toronto Neighbourhood Analysis
**Status**: Production — primary domain

| Layer | Tables | Description |
|-------|--------|-------------|
| `raw_toronto` | 11 tables | Dimensions, facts, bridge table |
| `stg_toronto` | 8 models | 1:1 source cleaning |
| `int_toronto` | 11 models | Business logic, profile pivots, extended census joins |
| `mart_toronto` | 9 tables | Analytics-ready output |

**Data sources**: City of Toronto Open Data, Toronto Police API, CMHC Rental Survey, Statistics Canada XLSX
**Coverage**: 158 neighbourhoods, 2016 + 2021 census years

### Football Analytics
**Status**: Production — secondary domain (integrated Sprint 14)

| Layer | Tables | Description |
|-------|--------|-------------|
| `raw_football` | 8 tables | Dimensions, facts, bridge table |
| `stg_football` | 8 models | 1:1 source cleaning |
| `int_football` | 4 models | Business logic, club-league bridge, financials |
| `mart_football` | 3 tables | Analytics-ready output |

**Data sources**: Transfermarkt (Salimt API), MLSPA, Deloitte Money League
**Scope**: 7 leagues — Premier League (GB1), La Liga (ES1), Bundesliga (L1), Serie A (IT1), Ligue 1 (FR1), Brasileirao (BRA1), MLS (MLS1)

---

## Architecture

### Directory Structure

```
dataflow/                       # Core ETL package
├── config.py                   # Database connection (PostgreSQL URL)
├── errors/exceptions.py        # Custom exception classes
├── toronto/                    # Toronto domain
│   ├── parsers/                # API + XLSX data extraction
│   ├── loaders/                # PostgreSQL persistence
│   ├── schemas/                # Pydantic validation models
│   └── models/                 # SQLAlchemy ORM (raw_toronto schema)
└── football/                   # Football domain
    ├── parsers/                # Transfermarkt, MLSPA, Deloitte parsers
    ├── loaders/                # Football data loaders
    ├── schemas/                # Pydantic validation models
    └── models/                 # SQLAlchemy ORM (raw_football schema)

dbt/                            # dbt project: portfolio
└── models/
    ├── shared/                 # stg_dimensions__time (cross-domain)
    ├── staging/toronto/        # 8 staging models
    ├── staging/football/       # 8 staging models
    ├── intermediate/toronto/   # 11 intermediate models
    ├── intermediate/football/  # 4 intermediate models
    ├── marts/toronto/          # 9 mart tables
    └── marts/football/         # 3 mart tables

scripts/
├── db/init_schema.py           # Schema + extension initialization
└── data/
    ├── load_toronto_data.py    # Toronto ETL (DataPipeline class)
    ├── load_football_data.py   # Football ETL
    └── xlsx_diagnostic.py      # XLSX label validation utility
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `parsers/` | Extract raw data from APIs and files. Returns validated Pydantic objects. |
| `schemas/` | Pydantic models for input validation. Defines the shape of inbound data. |
| `models/` | SQLAlchemy 2.0 ORM models. Defines raw table schemas in PostgreSQL. |
| `loaders/` | Persist validated data to PostgreSQL. Uses upsert or delete-then-insert patterns. |
| `dbt/staging/` | 1:1 source cleaning, type casting, column renaming. No business logic. |
| `dbt/intermediate/` | Business logic: joins, aggregations, pivots, CPI adjustments, composite scores. |
| `dbt/marts/` | Final analytical tables. Denormalized, documented, read-only contract with webapp. |

### Loading Patterns

| Pattern | Used For | Rationale |
|---------|----------|-----------|
| DELETE-then-INSERT | `fact_neighbourhood_profile` | Profile data is replaced wholesale per census year |
| UPSERT-by-key | `fact_census`, `fact_census_extended`, `fact_rentals` | Idempotent re-runs without duplicates |
| Bulk INSERT (no conflict) | Initial dimension loads | Fast first-time population |

---

## Key Architectural Decisions

### `int_neighbourhood__foundation` — Central Hub
The `int_neighbourhood__foundation` intermediate model is the canonical source for downstream Toronto marts. It joins `fact_census`, `fact_census_extended`, and CPI imputation in one place. All marts that need neighbourhood-level scalar indicators should reference foundation, not individual staging models.

`int_neighbourhood__demographics` is soft-deprecated; it reads from foundation and is kept only for backward compatibility until the webapp fully migrates.

### CPI Income Imputation
2016 census from Toronto Open Data does not include neighbourhood-level income. dbt imputes 2016 income by backward-adjusting 2021 census values using Statistics Canada CPI ratios:
- `income_2016 = income_2021 × (128.4 / 141.6)`
- All imputed values are flagged `is_imputed = TRUE`

### Profile Denominator Fix (Sprint 13)
`int_toronto__neighbourhood_profile` previously calculated percentages using `SUM(count)` as the denominator, which included subtotals and caused 1.5–2× inflation. Fixed by using `MAX(category_total)` from the XLSX section header rows. `indent_level` distinguishes subcategory hierarchy.

### CMHC Rental Disaggregation
CMHC publishes rental data at the zone grain (~36 zones). `int_rentals__neighbourhood_allocated` uses the `bridge_cmhc_neighbourhood` area-weighted crosswalk to disaggregate zone values to 158 neighbourhoods. `mart_neighbourhood_housing_rentals` is the output.

### Football Club-League Bridge
Transfermarkt club season data often has NULL `league_id`. `int_football__club_league_bridge` resolves these gaps by inferring league associations from transfer and market value data.

---

## Data Quality Notes

### Known Issues

| Issue | Status | Location |
|-------|--------|----------|
| 2016 income NULL at neighbourhood level | Mitigated via CPI imputation | `int_neighbourhood__foundation` |
| StatCan cell suppression (NULL counts) | Expected behavior — flag in analytics | `fact_neighbourhood_profile` |
| 6 deferred profile categories (occupation, industry, income bracket, income source, household type, family type) | Wrong XLSX anchors — future sprint | `fact_neighbourhood_profile` |
| Historical boundary reconciliation (140→158 neighbourhoods) | Deferred — 2021+ data only | All toronto models |
| Gitea `create_issue_dependency` API returns 404 | Dependencies documented in issue bodies instead | CI/tooling |

### XLSX Label Matching
Statistics Canada XLSX files use Unicode smart quotes (U+2019 `'` → ASCII `'`). The `_normalize_key()` helper in parsers handles normalization before label comparison. Always run `scripts/data/xlsx_diagnostic.py` before writing a new XLSX field mapping.

---

## Tech Stack

| Layer | Technology | Version | Constraint |
|-------|------------|---------|------------|
| Database | PostgreSQL | 16.x | — |
| Geospatial | PostGIS | 3.4 | `imresamu/postgis:16-3.4` for ARM64 |
| Validation | Pydantic | 2.x | 2.0 API only — no 1.x patterns |
| ORM | SQLAlchemy | 2.x | 2.0-style API only — no legacy `Session.query()` |
| Transformation | dbt-postgres | 1.9+ | Project: `portfolio` |
| Data Processing | Pandas, GeoPandas, Shapely | Latest | Required for spatial join in crosswalk builder |
| Testing | pytest | Latest | `tests/` directory |
| Linting | ruff | 0.8+ | Replaces flake8 + black + isort |
| Type Checking | mypy | 1.14+ | Strict mode |
| Python | 3.11+ | Via pyenv | `.python-version = 3.11` |

---

## Branching Strategy

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `main` | Production releases | VPS (production) |
| `staging` | Pre-production testing | VPS (staging) |
| `development` | Active development integration | Local |

**Rules:**
- Feature branches from `development`: `feature/{sprint}-{description}`
- Merge into `development` when complete
- `development` → `staging` → `main` for releases
- Never delete `development`
- Use `/gitflow branch-start` and `/gitflow commit` for standardized workflow

---

## Environment Variables

Required in `.env`:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio
POSTGRES_USER=portfolio
POSTGRES_PASSWORD=<secure>
POSTGRES_DB=portfolio
LOG_LEVEL=INFO
```

---

## Deferred Features

Stop and flag if a task requires these:

| Feature | Reason |
|---------|--------|
| Historical boundary reconciliation (140→158 neighbourhoods) | 2021+ data only for V1 |
| 6 deferred profile categories (occupation, industry, income, household, family) | Wrong XLSX anchors — needs investigation |
| ML prediction models | Future phase |
| Policy event annotation (`dim_policy_event`) | Table exists; requires manual data curation |
| dbt source freshness checks | Awaits `updated_at` timestamp migration on raw tables |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `README.md` | Quick start and overview |
| `CLAUDE.md` | AI assistant context and mandatory behavior rules |
| `docs/DATABASE_SCHEMA.md` | Full schema reference |
| `docs/CONTRIBUTING.md` | Contributor guide |
| `docs/deployment/vps-deployment.md` | Production deployment runbook |
| `docs/deployment/shared-postgres.md` | Multi-database PostgreSQL setup |
| `docs/project-lessons-learned/INDEX.md` | Sprint lessons learned |

---

*Reference Version: 4.0*
*Updated: February 2026 — Sprint 14 complete*
