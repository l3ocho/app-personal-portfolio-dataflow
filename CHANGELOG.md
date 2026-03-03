# 📜 Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) | Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

> **Sprint narratives** are captured in the [Gitea Wiki](https://gitea.hotserv.cloud/personal-projects/app-personal-portfolio-dataflow/wiki) with full lessons learned.

---

## [Unreleased]

### Removed
- `mart_neighbourhood_foundation` — deleted as redundant; every column it contained is also present in `mart_neighbourhood_demographics`, which additionally provides age band population columns, index columns, and city-wide comparisons. Use `mart_neighbourhood_demographics` instead.

---

## [0.5.0] — 2026-02-24

### Sprint 15 — Geometry Mart Extraction

#### Added
- `mart_neighbourhood_geometry` — New dedicated geometry lookup mart (158 rows, canonical SSoT for neighbourhood boundaries and names)
- `prompt-reference.md` in webapp repo — AI context file for cross-repo coordination

#### Changed
- Removed `neighbourhood_name` and `geometry` columns from 8 analytical mart SQL files — geometry is now accessed exclusively via JOIN to `mart_neighbourhood_geometry`
- Updated `_marts.yml` — FK relationship tests now reference `mart_neighbourhood_geometry` instead of staging refs
- `geometry_service.py` (webapp) — queries `mart_neighbourhood_geometry` instead of `mart_neighbourhood_overview` / `raw_toronto.dim_neighbourhood`
- `neighbourhood_service.py` (webapp) — added JOIN to `mart_neighbourhood_geometry` across all 8 service functions
- `docs/DATABASE_SCHEMA.md` — updated in both repos
- `docs/PROJECT_REFERENCE.md` — corrected league scope (Brasileirão, not Eredivisie), updated mart count to 9

#### Architectural Decision
> Geometry is never embedded in analytical marts. All spatial lookups go through `mart_neighbourhood_geometry` via `neighbourhood_id`. This prevents geometry bloat in wide tables and maintains a single source of truth.

---

## [0.4.0] — 2026-02-23

### Sprints 12–14 — Toronto Restructure + Football Pipeline

#### Added (Sprint 14 — Mart Layer)
- `mart_neighbourhood_foundation` — New cross-domain mart (65+ cols, grain: neighbourhood × year) built from `int_neighbourhood__foundation`
- `mart_neighbourhood_housing_rentals` — Neighbourhood-grain rental mart (grain: neighbourhood × bedroom_type × year, 4,424 rows); replaces zone-grain `mart_toronto_rentals`
- `mart_neighbourhood_housing` — Expanded +27 columns: dwelling type pivots (7 types), bedroom pivots (5 sizes), construction period pivots (8 buckets), shelter cost scalars, composite fit scores
- `mart_neighbourhood_amenities` — Expanded +20 columns: commute mode pivots (6 modes), commute duration pivots (5 buckets), commute destination pivots (4 destinations), `car_dependency_index`
- `mart_neighbourhood_profile` — Exposes `indent_level`, `category_total`, `is_subtotal`

#### Added (Football Pipeline)
- `raw_football` schema with 9 tables: `dim_league`, `dim_club`, `dim_player`, `fact_player_market_value`, `fact_transfer`, `fact_club_season`, `fact_mls_salary`, `fact_club_finance`, `bridge_player_competition`
- 8 football staging models, 4 intermediate models, 3 mart tables
- `DeloitteParser` — Wikipedia revenue scraper for Deloitte Money League data
- `int_football__club_league_bridge` — Resolves NULL `league_id` gaps from Transfermarkt data
- Football scope: Premier League (GB1), La Liga (ES1), Bundesliga (L1), Serie A (IT1), Ligue 1 (FR1), Brasileirão (BRA1), MLS (MLS1)
- `scripts/data/load_football_data.py` — Football ETL orchestration

#### Added (Sprint 13 — dbt Layer)
- `stg_toronto__census_extended` — 1:1 staging model for `fact_census_extended` (~55 scalar columns)
- `int_neighbourhood__foundation` — New intermediate superseding `int_neighbourhood__demographics`; CPI imputation + LEFT JOIN to `stg_toronto__census_extended` for 50+ extended scalar columns
- 50+ extended census scalar columns surfaced in `mart_neighbourhood_demographics`

#### Added (Sprint 12 — Raw Layer)
- `fact_census_extended` in `raw_toronto` schema — ~55 scalar indicators per neighbourhood per census year
- `category_total` and `indent_level` columns on `fact_neighbourhood_profile`
- `CensusExtendedRecord` Pydantic schema + `FactCensusExtended` SQLAlchemy model
- `census_extended_loader.py` — upsert loader for census extended data
- 12 new profile categories (total: 22 categories, up from 10): `religion`, `education_level`, `field_of_study`, `commute_mode`, `commute_duration`, `commute_destination`, `housing_suitability`, `dwelling_type`, `bedrooms`, `construction_period`, `mother_tongue`, `indigenous_identity`
- `_normalize_key()` — Unicode apostrophe normalization (U+2019 → ASCII) for Statistics Canada XLSX parsing

#### Changed (Sprint 14)
- `int_neighbourhood__housing` refactored — switched from deprecated `int_neighbourhood__demographics` to `int_neighbourhood__foundation`
- `int_neighbourhood__amenity_scores` refactored — switched from `stg_toronto__census` to `int_neighbourhood__foundation`

#### Changed (Sprint 13)
- `mart_neighbourhood_demographics` now reads from `int_neighbourhood__foundation`
- `int_neighbourhood__demographics` soft-deprecated (`meta: deprecated: true`); kept for backward compatibility

#### Fixed (Sprint 13)
- Profile denominator bug — `neighbourhood_category_totals` now uses `MAX(category_total)` from section header rows instead of `SUM(count)`, eliminating 1.5–2x inflation from subtotal contamination

#### Fixed (Sprint 12)
- Profile `UniqueConstraint` extended to include `indent_level` (fixes hierarchical subcategory collisions)
- 21 `CENSUS_EXTENDED_MAPPING` label corrections (wrong label text, missing phrases, wrong suffixes)
- `field_of_study` XLSX anchor scoped to 15+ population section (prevents duplicate rows)

#### Removed (Sprint 14)
- `mart_toronto_rentals` (deprecated zone-grain rental mart) — replaced by `mart_neighbourhood_housing_rentals`

---

## [0.1.0] — 2026-02-10

### Sprint 10 — Repository Separation + Production Deployment

#### Added
- Initial data pipeline for Toronto neighbourhood analysis
- PostgreSQL 16 + PostGIS 3.4 schema (`raw_toronto`, `mart_toronto`)
- dbt models for data transformation (staging → intermediate → marts)
- ETL scripts for Toronto Open Data, Toronto Police API, CMHC data
- Parsers, loaders, Pydantic schemas, and SQLAlchemy models for Toronto domain
- VPS deployment documentation (`docs/deployment/vps-deployment.md`)
- Shared PostgreSQL setup guide (`docs/deployment/shared-postgres.md`)
- Cron-based ETL deployment strategy

#### Changed
- Repository scope reduced to data-only pipeline — removed ~7,000 lines of frontend Dash code
- Package renamed `portfolio_app` → `dataflow`
- CI/CD workflows updated for data-only deployment

#### Removed
- All frontend code: Dash app, pages, figures, components, callbacks
- Frontend dependencies: `dash`, `plotly`, `dash-mantine-components`
- Blog content system and Markdown utilities

---

*Changelog · app-personal-portfolio-dataflow · [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format*
