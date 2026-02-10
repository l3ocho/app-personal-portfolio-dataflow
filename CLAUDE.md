# CLAUDE.md

## ⛔ MANDATORY BEHAVIOR RULES - READ FIRST

**These rules are NON-NEGOTIABLE. Violating them wastes the user's time and money.**

### 1. WHEN USER ASKS YOU TO CHECK SOMETHING - CHECK EVERYTHING
- Search ALL locations, not just where you think it is
- Check cache directories: `~/.claude/plugins/cache/`
- Check installed: `~/.claude/plugins/marketplaces/`
- Check source directories
- **NEVER say "no" or "that's not the issue" without exhaustive verification**

### 2. WHEN USER SAYS SOMETHING IS WRONG - BELIEVE THEM
- The user knows their system better than you
- Investigate thoroughly before disagreeing
- **Your confidence is often wrong. User's instincts are often right.**

### 3. NEVER SAY "DONE" WITHOUT VERIFICATION
- Run the actual command/script to verify
- Show the output to the user
- **"Done" means VERIFIED WORKING, not "I made changes"**

### 4. SHOW EXACTLY WHAT USER ASKS FOR
- If user asks for messages, show the MESSAGES
- If user asks for code, show the CODE
- **Do not interpret or summarize unless asked**

**FAILURE TO FOLLOW THESE RULES = WASTED USER TIME = UNACCEPTABLE**

---



## Mandatory Behavior Rules

**These rules are NON-NEGOTIABLE. Violating them wastes the user's time and money.**

1. **CHECK EVERYTHING** - Search ALL locations before saying "no" (cache, installed, source directories)
2. **BELIEVE THE USER** - Investigate thoroughly before disagreeing; user instincts are often right
3. **VERIFY BEFORE "DONE"** - Run commands, show output; "done" means verified working
4. **SHOW EXACTLY WHAT'S ASKED** - Do not interpret or summarize unless requested

---

Working context for Claude Code on the Analytics Portfolio project.

---

## Project Status

**Last Completed Sprint**: 9 (Neighbourhood Dashboard Transition)
**Current State**: Ready for deployment sprint or new features
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

# Application
make run            # Start Dash dev server

# Testing & Quality
make test           # Run pytest
make lint           # Run ruff linter
make format         # Run ruff formatter
make typecheck      # Run mypy type checker
make ci             # Run all checks (lint, typecheck, test)

# dbt
make dbt-run        # Run dbt models
make dbt-test       # Run dbt tests
make dbt-docs       # Generate and serve dbt documentation

# Run `make help` for full target list
```

### Branch Workflow

1. Create feature branch FROM `development`: `git checkout -b feature/{sprint}-{description}`
2. Work and commit on feature branch
3. Merge INTO `development` when complete
4. `development` -> `staging` -> `main` for releases

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
| `services/` | Query functions for dbt mart queries |
| `figures/` | Chart factories for Plotly figure generation |
| `errors/` | Custom exception classes (see `errors/exceptions.py`) |

### Code Standards

- Python 3.10+ type hints: `list[str]`, `dict[str, int] | None`
- Single responsibility functions with verb naming
- Early returns over deep nesting
- Google-style docstrings only for non-obvious behavior

---

## Application Structure

**Entry Point:** `portfolio_app/app.py` (Dash app factory with Pages routing)

| Directory | Purpose |
|-----------|---------|
| `pages/` | Dash Pages (file-based routing) |
| `pages/toronto/` | Toronto Dashboard (`tabs/` for layouts, `callbacks/` for interactions) |
| `components/` | Shared UI components |
| `figures/toronto/` | Toronto chart factories |
| `toronto/` | Toronto data logic (parsers, loaders, schemas, models) |

**Key URLs:** `/` (home), `/toronto` (dashboard), `/blog` (listing), `/blog/{slug}` (articles), `/health` (status)

### Multi-Dashboard Architecture

- **figures/**: Domain-namespaced (`figures/toronto/`, future: `figures/football/`)
- **dbt models**: Domain subdirectories (`staging/toronto/`, `marts/toronto/`)
- **Database schemas**: Domain-specific raw data (`raw_toronto`, future: `raw_football`)

---

## Tech Stack (Locked)

| Layer | Technology | Version |
|-------|------------|---------|
| Database | PostgreSQL + PostGIS | 16.x |
| Validation | Pydantic | >=2.0 |
| ORM | SQLAlchemy | >=2.0 (2.0-style API only) |
| Transformation | dbt-postgres | >=1.7 |
| Visualization | Dash + Plotly + dash-mantine-components | >=2.14 |
| Geospatial | GeoPandas + Shapely | >=0.14 |
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

---

## Environment Variables

Required in `.env`:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio
POSTGRES_USER=portfolio
POSTGRES_PASSWORD=<secure>
POSTGRES_DB=portfolio
DASH_DEBUG=true
SECRET_KEY=<random>
LOG_LEVEL=INFO
```

---

## Reference Documents

| Document | Location | Use When |
|----------|----------|----------|
| Project reference | `docs/PROJECT_REFERENCE.md` | Architecture decisions |
| Developer guide | `docs/CONTRIBUTING.md` | How to add pages, tabs |
| Lessons learned | `docs/project-lessons-learned/INDEX.md` | Past issues and solutions |
| Deployment runbook | `docs/runbooks/deployment.md` | Deploying to environments |
| Plugin workflow prompts | `docs/plugin-prompts/` | Interactive UI adjustment sessions |

### Plugin Workflow Prompts

The `docs/plugin-prompts/` directory contains specialized workflow prompts for activating leo-code-marketplace plugins in interactive UI refinement sessions:

| Prompt | Purpose | Plugins Used |
|--------|---------|--------------|
| `ui-dash-adjust.md` | Dashboard page adjustments (data-driven pages with dbt, Plotly, callbacks) | viz-platform, data-platform, git-flow |
| `ui-layout-adjust.md` | Non-dashboard page adjustments (home, about, contact, projects, resume, blog) | viz-platform, git-flow |

**When to use:**
- Start live Dash debug sessions with iterative UI changes
- Auto-reload on save workflow
- Includes quality gates and git-flow integration for branch management

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

**Gitea**: `personal-projects/personal-portfolio` at `gitea.hotserv.cloud`

### Data Platform: data-platform

Use for dbt, PostgreSQL, and PostGIS operations.

| Skill | Purpose |
|-------|---------|
| `/data-platform:data-review` | Audit data integrity, schema validity, dbt compliance |
| `/data-platform:data-gate` | CI/CD data quality gate (pass/fail) |

**When to use:** Schema changes, dbt model development, data loading, before merging data PRs.

**MCP tools available:** `pg_connect`, `pg_query`, `pg_tables`, `pg_columns`, `pg_schemas`, `st_*` (PostGIS), `dbt_*` operations.

### Visualization: viz-platform

Use for Dash/Mantine component validation and chart creation.

| Skill | Purpose |
|-------|---------|
| `/viz-platform:component` | Inspect DMC component props and validation |
| `/viz-platform:chart` | Create themed Plotly charts |
| `/viz-platform:theme` | Apply/validate themes |
| `/viz-platform:dashboard` | Create dashboard layouts |

**When to use:** Dashboard development, new visualizations, component prop lookup.

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

### Contract Validation: contract-validator

Use for plugin interface validation.

| Skill | Purpose |
|-------|---------|
| `/contract-validator:agent-check` | Quick agent definition validation |
| `/contract-validator:full-validation` | Full plugin contract validation |

**When to use:** When modifying plugin integrations or agent definitions.

### Git Workflow: git-flow

Use for standardized git operations.

| Skill | Purpose |
|-------|---------|
| `/git-flow:commit` | Auto-generated conventional commit |
| `/git-flow:branch-start` | Create feature/fix/chore branch |
| `/git-flow:git-status` | Comprehensive status with recommendations |

**When to use:** Complex merge scenarios, branch management, standardized commits.

---

*Last Updated: February 2026*
