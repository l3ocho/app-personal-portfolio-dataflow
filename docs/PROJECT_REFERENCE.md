# Portfolio Project Reference

**Project**: Analytics Portfolio
**Owner**: Leo Miranda
**Status**: Sprint 9 Complete (Dashboard Implementation Done)
**Last Updated**: January 2026

---

## Project Overview

Personal portfolio website with an interactive Toronto Neighbourhood Dashboard demonstrating data engineering, visualization, and analytics capabilities.

| Component | Description | Status |
|-----------|-------------|--------|
| Portfolio Website | Bio, About, Projects, Resume, Contact, Blog | Complete |
| Toronto Dashboard | 5-tab neighbourhood analysis | Complete |
| Data Pipeline | dbt models, figure factories | Complete |
| Deployment | Production deployment | Pending |

---

## Completed Work

### Sprint 1-6: Foundation
- Repository setup, Docker, PostgreSQL + PostGIS
- Bio landing page implementation
- Initial data model design

### Sprint 7: Navigation & Theme
- Sidebar navigation
- Dark/light theme toggle
- dash-mantine-components integration

### Sprint 8: Portfolio Website
- About, Contact, Projects, Resume pages
- Blog system with Markdown/frontmatter
- Health endpoint

### Sprint 9: Neighbourhood Dashboard Transition
- Phase 1: Deleted legacy TRREB code
- Phase 2: Documentation cleanup
- Phase 3: New neighbourhood-centric data model
- Phase 4: dbt model restructuring
- Phase 5: 5-tab dashboard implementation
- Phase 6: 15 documentation notebooks
- Phase 7: Final documentation review

---

## Application Architecture

### URL Routes

| URL | Page | File |
|-----|------|------|
| `/` | Home | `pages/home.py` |
| `/about` | About | `pages/about.py` |
| `/contact` | Contact | `pages/contact.py` |
| `/projects` | Projects | `pages/projects.py` |
| `/resume` | Resume | `pages/resume.py` |
| `/blog` | Blog listing | `pages/blog/index.py` |
| `/blog/{slug}` | Article | `pages/blog/article.py` |
| `/toronto` | Dashboard | `pages/toronto/dashboard.py` |
| `/toronto/methodology` | Methodology | `pages/toronto/methodology.py` |
| `/health` | Health check | `pages/health.py` |

### Directory Structure

```
portfolio_app/
├── app.py                    # Dash app factory
├── config.py                 # Pydantic BaseSettings
├── assets/                   # CSS, images
├── callbacks/                # Global callbacks (sidebar, theme)
├── components/               # Shared UI components
├── content/blog/             # Markdown blog articles
├── errors/                   # Exception handling
├── figures/
│   └── toronto/              # Toronto figure factories
├── pages/
│   ├── home.py
│   ├── about.py
│   ├── contact.py
│   ├── projects.py
│   ├── resume.py
│   ├── health.py
│   ├── blog/
│   │   ├── index.py
│   │   └── article.py
│   └── toronto/
│       ├── dashboard.py
│       ├── methodology.py
│       ├── tabs/             # 5 tab layouts
│       └── callbacks/        # Dashboard interactions (map_callbacks, chart_callbacks, selection_callbacks)
├── toronto/                  # Data logic
│   ├── parsers/              # API extraction (geo, toronto_open_data, toronto_police, cmhc)
│   ├── loaders/              # Database operations (base, cmhc, cmhc_crosswalk)
│   ├── schemas/              # Pydantic models
│   ├── models/               # SQLAlchemy ORM (raw_toronto schema)
│   ├── services/             # Query functions (neighbourhood_service, geometry_service)
│   └── demo_data.py          # Sample data
└── utils/
    └── markdown_loader.py    # Blog article loading

dbt/                          # dbt project: portfolio
├── models/
│   ├── shared/               # Cross-domain dimensions
│   ├── staging/toronto/      # Toronto staging models
│   ├── intermediate/toronto/ # Toronto intermediate models
│   └── marts/toronto/        # Toronto mart tables

notebooks/
└── toronto/                  # Toronto documentation notebooks
```

---

## Toronto Dashboard

### Data Sources

| Source | Data | Format |
|--------|------|--------|
| City of Toronto Open Data | Neighbourhoods (158), Census profiles, Parks, Schools, Childcare, TTC | GeoJSON, CSV, API |
| Toronto Police Service | Crime rates, MCI, Shootings | CSV, API |
| CMHC | Rental Market Survey | CSV |

### Geographic Model

```
City of Toronto Neighbourhoods (158) ← Primary analysis unit
CMHC Zones (~20) ← Rental data (Census Tract aligned)
```

### Dashboard Tabs

| Tab | Choropleth Metric | Supporting Charts |
|-----|-------------------|-------------------|
| Overview | Livability score | Top/Bottom 10 bar, Income vs Safety scatter |
| Housing | Affordability index | Rent trend line, Tenure breakdown bar |
| Safety | Crime rate per 100K | Crime breakdown bar, Crime trend line |
| Demographics | Median income | Age distribution, Population density bar |
| Amenities | Amenity index | Amenity radar, Transit accessibility bar |

### Star Schema

| Table | Type | Description |
|-------|------|-------------|
| `dim_neighbourhood` | Dimension | 158 neighbourhoods with geometry |
| `dim_time` | Dimension | Date dimension |
| `dim_cmhc_zone` | Dimension | ~20 CMHC zones with geometry |
| `fact_census` | Fact | Census indicators by neighbourhood |
| `fact_crime` | Fact | Crime stats by neighbourhood |
| `fact_rentals` | Fact | Rental data by CMHC zone |
| `fact_amenities` | Fact | Amenity counts by neighbourhood |

### dbt Project: `portfolio`

**Model Structure:**
```
dbt/models/
├── shared/                 # Cross-domain dimensions (stg_dimensions__time)
├── staging/toronto/        # Toronto staging models
├── intermediate/toronto/   # Toronto intermediate models
└── marts/toronto/          # Toronto mart tables
```

| Layer | Naming | Example |
|-------|--------|---------|
| Shared | `stg_dimensions__*` | `stg_dimensions__time` |
| Staging | `stg_{source}__{entity}` | `stg_toronto__neighbourhoods` |
| Intermediate | `int_{domain}__{transform}` | `int_neighbourhood__demographics` |
| Marts | `mart_{domain}` | `mart_neighbourhood_overview` |

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Database | PostgreSQL + PostGIS | 16.x |
| Validation | Pydantic | 2.x |
| ORM | SQLAlchemy | 2.x |
| Transformation | dbt-postgres | 1.7+ |
| Data Processing | Pandas, GeoPandas | Latest |
| Visualization | Dash + Plotly | 2.14+ |
| UI Components | dash-mantine-components | Latest |
| Testing | pytest | 7.0+ |
| Python | 3.11+ | Via pyenv |

---

## Branching Strategy

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `main` | Production releases | VPS (production) |
| `staging` | Pre-production testing | VPS (staging) |
| `development` | Active development | Local only |

**Rules:**
- Feature branches from `development`: `feature/{sprint}-{description}`
- Merge into `development` when complete
- `development` → `staging` → `main` for releases
- Never delete `development`

---

## Code Standards

### Type Hints (Python 3.10+)

```python
def process(items: list[str], config: dict[str, int] | None = None) -> bool:
    ...
```

### Imports

| Context | Style |
|---------|-------|
| Same directory | `from .module import X` |
| Sibling directory | `from ..schemas.model import Y` |
| External | `import pandas as pd` |

### Error Handling

```python
class PortfolioError(Exception):
    """Base exception."""

class ParseError(PortfolioError):
    """Data parsing failed."""

class ValidationError(PortfolioError):
    """Validation failed."""

class LoadError(PortfolioError):
    """Database load failed."""
```

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

## Makefile Targets

| Target | Purpose |
|--------|---------|
| `setup` | Install deps, create .env, init pre-commit |
| `docker-up` | Start PostgreSQL + PostGIS (auto-detects x86/ARM) |
| `docker-down` | Stop containers |
| `docker-logs` | View container logs |
| `db-init` | Initialize database schema |
| `db-reset` | Drop and recreate database (DESTRUCTIVE) |
| `load-data` | Load Toronto data from APIs, seed dev data |
| `load-toronto-only` | Load Toronto data without dbt or seeding |
| `seed-data` | Seed sample development data |
| `run` | Start Dash dev server |
| `test` | Run pytest |
| `test-cov` | Run pytest with coverage |
| `lint` | Run ruff linter |
| `format` | Run ruff formatter |
| `typecheck` | Run mypy type checker |
| `ci` | Run all checks (lint, typecheck, test) |
| `dbt-run` | Run dbt models |
| `dbt-test` | Run dbt tests |
| `dbt-docs` | Generate and serve dbt documentation |
| `clean` | Remove build artifacts and caches |

---

## Next Steps

### Deployment (Sprint 10+)
- [ ] Production Docker configuration
- [ ] CI/CD pipeline
- [ ] HTTPS/SSL setup
- [ ] Domain configuration

### Data Enhancement
- [ ] Connect to live APIs (currently using demo data)
- [ ] Data refresh automation
- [ ] Historical data loading

### Future Projects
- Energy Pricing Analysis dashboard (planned)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `README.md` | Quick start guide |
| `CLAUDE.md` | AI assistant context |
| `docs/CONTRIBUTING.md` | Developer guide |
| `notebooks/README.md` | Notebook documentation |

---

*Reference Version: 3.0*
*Updated: January 2026*
