# CLAUDE.md

> See `~/.claude/CLAUDE.md` for global behavior rules that apply to this and all projects.

---

## Project Overview

**Repository**: personal-portfolio-dataflow
**Purpose**: Data engineering pipeline (ETL/ELT) for analytics projects
**Scope**: Data acquisition → Database persistence (NO FRONTEND)

This is a **data-only** repository. All visualization and frontend code lives in the separate `personal-portfolio` webapp repository.

---

## Project Status

**Last Completed Sprint**: 10 (Dataflow Separation & Production Deployment)
**Current State**: Production-ready data pipeline
**Branch**: `development` (feature branches merge here)

---

## Quick Reference

### Run Commands

```bash
# Setup & Database
make setup          # Install deps, create .env, init pre-commit
make docker-up      # Start PostgreSQL + PostGIS (auto-detects x86/ARM)
make docker-down    # Stop containers
make db-init        # Initialize database schema
make db-reset       # Drop and recreate database (DESTRUCTIVE)

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

# Run `make help` for full target list
```

### Git Workflow

**Base Branch**: `development` (feature branches merge here)
**Protected Branches**: `main`, `staging`, `development`
**Repository**: `personal-projects/app-personal-portfolio-dataflow` @ `gitea.hotserv.cloud`

Branch naming, commit conventions, workflow steps, and release procedures are documented in `/git-flow` plugin. Use `/gitflow branch-start` for branch creation and `/gitflow commit` for conventional commits.

---

## Code Conventions

### Import Style

| Context | Style | Example |
|---------|-------|---------|
| Same directory | Single dot | `from .neighbourhood import NeighbourhoodRecord` |
| Sibling directory | Double dot | `from ..schemas.neighbourhood import CensusRecord` |
| External packages | Absolute | `import pandas as pd` |

### Module Responsibilities

| Directory | Purpose |
|-----------|---------|
| `schemas/` | Pydantic models for data validation |
| `models/` | SQLAlchemy ORM for database persistence |
| `parsers/` | API/CSV extraction for raw data ingestion |
| `loaders/` | Database operations for data loading |
| `errors/` | Custom exception classes (see `errors/exceptions.py`) |

### Code Standards

- Python 3.10+ type hints: `list[str]`, `dict[str, int] | None`
- Single responsibility functions with verb naming
- Early returns over deep nesting
- Google-style docstrings only for non-obvious behavior

---

## Application Structure

**Entry Point**: ETL scripts in `scripts/data/`

| Directory | Purpose |
|-----------|---------|
| `dataflow/` | Core data pipeline code |
| `dataflow/toronto/` | Toronto data logic (parsers, loaders, schemas, models) |
| `scripts/db/` | Database initialization |
| `scripts/data/` | ETL scripts |
| `dbt/` | dbt project (transformations) |
| `data/` | Raw data files |
| `docs/` | Documentation |

**Key Operations:**
- `scripts/data/load_toronto_data.py` - Load Toronto data from APIs
- `scripts/db/init_schema.py` - Initialize database schemas
- `dbt/models/` - Data transformations

### Multi-Domain Architecture

- **dataflow/**: Domain-namespaced (`dataflow/toronto/`, future: `dataflow/football/`)
- **dbt models**: Domain subdirectories (`staging/toronto/`, `marts/toronto/`)
- **Database schemas**: Domain-specific raw data (`raw_toronto`, future: `raw_football`)

---

## Tech Stack (Locked)

| Layer | Technology | Version |
|-------|------------|---------|
| Database | PostgreSQL + PostGIS | 16.x / 3.4 |
| Validation | Pydantic | >=2.0 |
| ORM | SQLAlchemy | >=2.0 (2.0-style API only) |
| Transformation | dbt-postgres | >=1.7 |
| Data Processing | Pandas, GeoPandas, Shapely | Latest |
| Python | 3.11+ | Via pyenv |

**Notes**: SQLAlchemy 2.0 + Pydantic 2.0 only. Docker Compose V2 format (no `version` field).

---

## Data Model Overview

### Database Schemas

| Schema | Purpose |
|--------|---------|
| `public` | Shared dimensions (dim_time) |
| `raw_toronto` | Toronto-specific raw/dimension tables |
| `stg_toronto` | Toronto dbt staging views |
| `int_toronto` | Toronto dbt intermediate views |
| `mart_toronto` | Toronto dbt mart tables |

### dbt Project: `portfolio`

| Layer | Naming | Purpose |
|-------|--------|---------|
| Shared | `stg_dimensions__*` | Cross-domain dimensions |
| Staging | `stg_{source}__{entity}` | 1:1 source, cleaned, typed |
| Intermediate | `int_{domain}__{transform}` | Business logic |
| Marts | `mart_{domain}` | Final analytical tables |

---

## Deferred Features

**Stop and flag if a task requires these**:

| Feature | Reason |
|---------|--------|
| Historical boundary reconciliation (140->158) | 2021+ data only for V1 |
| ML prediction models | Energy project scope (future phase) |
| Frontend visualizations | Moved to separate webapp repository |
| Policy event annotation (dim_policy_event) | Table exists but requires manual data curation (future phase) |
| dbt source freshness checks | Requires migration to add updated_at timestamp columns to raw tables |

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

**Removed** (frontend-only):
- `DASH_DEBUG` - Not applicable
- `SECRET_KEY` - Not applicable

---

## Reference Documents

| Document | Location | Use When |
|----------|----------|----------|
| Deployment runbook | `docs/deployment/vps-deployment.md` | Deploying to VPS |
| Shared postgres | `docs/deployment/shared-postgres.md` | Multi-database postgres setup |
| Database schema | `docs/DATABASE_SCHEMA.md` | Schema reference |
| Lessons learned | `docs/project-lessons-learned/INDEX.md` | Past issues and solutions |

---

## Plugin Reference

### Sprint Management: projman

**CRITICAL: Always use projman for sprint and task management.**

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `/projman:sprint-plan` | New sprint/feature | Architecture analysis + Gitea issue creation |
| `/projman:sprint-start` | Begin implementation | Load lessons learned, start execution |
| `/projman:sprint-status` | Check progress | Review blockers and completion |
| `/projman:sprint-close` | Sprint completion | Capture lessons learned |

**Default workflow**: `/projman:sprint-plan` before code -> create issues -> `/projman:sprint-start` -> track via Gitea -> `/projman:sprint-close`

**Gitea**: `personal-projects/personal-portfolio-dataflow` at `gitea.hotserv.cloud`

### Data Platform: data-platform

Use for dbt, PostgreSQL, and PostGIS operations.

| Skill | Purpose |
|-------|---------|
| `/data-platform:data-review` | Audit data integrity, schema validity, dbt compliance |
| `/data-platform:data-gate` | CI/CD data quality gate (pass/fail) |

**When to use:** Schema changes, dbt model development, data loading, before merging data PRs.

**MCP tools available:** `pg_connect`, `pg_query`, `pg_tables`, `pg_columns`, `pg_schemas`, `st_*` (PostGIS), `dbt_*` operations.

### Code Quality: code-sentinel

Use for security scanning and refactoring analysis.

| Skill | Purpose |
|-------|---------|
| `/code-sentinel:security-scan` | Full security audit of codebase |
| `/code-sentinel:refactor` | Apply refactoring patterns |
| `/code-sentinel:refactor-dry` | Preview refactoring without applying |

**When to use:** Before major releases, after adding auth/data handling code, periodic audits.

### Documentation: doc-guardian

Use for documentation drift detection and synchronization.

| Skill | Purpose |
|-------|---------|
| `/doc-guardian:doc-audit` | Scan project for documentation drift |
| `/doc-guardian:doc-sync` | Synchronize pending documentation updates |

**When to use:** After significant code changes, before releases.

### Pull Requests: pr-review

Use for comprehensive PR review with multiple analysis perspectives.

| Skill | Purpose |
|-------|---------|
| `/pr-review:initial-setup` | Configure PR review for project |
| Triggered automatically | Security, performance, maintainability, test analysis |

**When to use:** Before merging significant PRs to `development` or `main`.

### Requirement Clarification: clarity-assist

Use when requirements are ambiguous or need decomposition.

**When to use:** Unclear specifications, complex feature requests, conflicting requirements.

### Git Workflow: git-flow

Use for standardized git operations.

| Skill | Purpose |
|-------|---------|
| `/git-flow:commit` | Auto-generated conventional commit |
| `/git-flow:branch-start` | Create feature/fix/chore branch |
| `/git-flow:git-status` | Comprehensive status with recommendations |

**When to use:** Complex merge scenarios, branch management, standardized commits.

### Deployment: ops-deploy-pipeline

Use for deployment configuration generation and validation.

| Skill | Purpose |
|-------|---------|
| `/ops-deploy-pipeline:deploy-generate` | Generate docker-compose.yml, Caddyfile, systemd units |
| `/ops-deploy-pipeline:deploy-validate` | Validate deployment configs for correctness and security |
| `/ops-deploy-pipeline:deploy-check` | Pre-deployment health check |
| `/ops-deploy-pipeline:deploy-rollback` | Generate rollback plan |

**When to use:** Preparing VPS deployments, validating configs, planning rollbacks for cron jobs.

### Release Management: ops-release-manager

Use for version management and release automation.

| Skill | Purpose |
|-------|---------|
| `/ops-release-manager:release-prepare` | Bump versions, update changelog, create release branch |
| `/ops-release-manager:release-validate` | Pre-release verification (version consistency, dependencies) |
| `/ops-release-manager:release-tag` | Create annotated git tag with release notes |
| `/ops-release-manager:release-status` | Show current version and release readiness |

**When to use:** Preparing releases, version bumping, changelog updates.

---

## Deployment

### Production Deployment

This repository deploys to VPS as **cron-based ETL jobs** (not a containerized service).

**Architecture:**
```
VPS: /opt/apps/
├── docker-compose.yml          # PostgreSQL (shared with Gitea, CloudBeaver)
├── gitea/
├── cloudbeaver/
└── portfolio-dataflow/         # This application (venv + cron)
    ├── .venv/
    ├── dataflow/
    ├── dbt/
    └── scripts/
```

**Deployment Steps:**
1. Clone to `/opt/apps/portfolio-dataflow`
2. Create Python venv and install dependencies
3. Configure `.env` with shared postgres connection
4. Initialize database and load data
5. Schedule cron jobs for automated ETL

**See**: `docs/deployment/vps-deployment.md` for complete guide

### Shared PostgreSQL

VPS uses a single PostgreSQL container with multiple databases:
- `gitea` - Gitea database
- `portfolio` - Portfolio dataflow database

**See**: `docs/deployment/shared-postgres.md` for multi-database setup

---

## Webapp Integration

The frontend webapp (`personal-portfolio`) consumes data from this pipeline:

**Interface Contract:**
- Dataflow produces: `mart_toronto.*` tables
- Webapp consumes: Read-only queries to mart tables
- Connection: Same postgres instance, different database client

**Responsibilities:**
- **Dataflow** (this repo): Maintain stable mart schemas, document column contracts, version changes
- **Webapp**: Read-only access, never write to database

---

*Last Updated: February 2026 (Sprint 10)*
