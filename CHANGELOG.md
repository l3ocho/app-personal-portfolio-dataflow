# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.4.0] - 2026-02-23

Toronto Restructure Phases 1–3 (Sprints 12–14) + Football Pipeline Integration.

### Added (Sprint 14 — Toronto Restructure Phase 3: Mart Layer)
- `mart_neighbourhood_foundation` — NEW cross-domain mart (65 cols, grain: neighbourhood × year) from `int_neighbourhood__foundation`
- `mart_neighbourhood_housing_rentals` — NEW neighbourhood-grain rentals mart (grain: neighbourhood × bedroom_type × year, 4,424 rows); replaces `mart_toronto_rentals` (zone grain, removed)
- `mart_neighbourhood_housing` expanded +27 columns: dwelling type pivots (7 types), bedroom pivots (5 sizes), construction period pivots (8 buckets), shelter cost scalars, composite scores (`family_housing_fit`, `couple_housing_fit`, `singles_housing_fit`)
- `mart_neighbourhood_amenities` expanded +20 columns: commute mode pivots (6 modes), commute duration pivots (5 buckets), commute destination pivots (4 destinations), `car_dependency_index` composite
- `mart_neighbourhood_profile` exposes 3 new columns: `indent_level`, `category_total`, `is_subtotal`

### Changed (Sprint 14)
- `int_neighbourhood__housing` refactored: switched from deprecated `int_neighbourhood__demographics` ref to `int_neighbourhood__foundation`; added dwelling/bedroom/construction profile pivot CTEs
- `int_neighbourhood__amenity_scores` refactored: switched from deprecated `stg_toronto__census` ref to `int_neighbourhood__foundation`; added commute pivot CTEs and `car_dependency_index`

### Removed (Sprint 14)
- `mart_toronto_rentals` (deprecated zone-grain rental mart) — replaced by `mart_neighbourhood_housing_rentals`

### Added (Football Pipeline Integration)
- `raw_football` schema: `dim_league`, `dim_club`, `dim_player`, `fact_player_market_value`, `fact_transfer`, `fact_club_season`, `fact_mls_salary`, `fact_club_finance`, `bridge_player_competition`
- 8 football staging models, 4 intermediate models, 3 mart tables
- `DeloitteParser` — Wikipedia revenue scraper for Deloitte Money League data
- `int_football__club_league_bridge` — resolves NULL `league_id` gaps from Transfermarkt data
- Football scope filtered to 7 in-scope leagues only (Premier League, La Liga, Bundesliga, Serie A, Ligue 1, Eredivisie, MLS)
- `scripts/data/load_football_data.py` — football ETL orchestration

### Added (Sprint 13 — Toronto Restructure Phase 2: dbt Layer)
- `stg_toronto__census_extended` — 1:1 staging model for `fact_census_extended` (~55 scalar columns)
- `int_neighbourhood__foundation` — new intermediate superseding `int_neighbourhood__demographics`; CPI imputation + LEFT JOIN to `stg_toronto__census_extended` for 50+ extended scalar columns
- 50+ extended census scalar columns surfaced in `mart_neighbourhood_demographics`: population age groups, household metrics, housing costs, education breakdowns, labour force, extended income, immigration/diversity, language, mobility, commuting, family/housing quality, occupations

### Fixed (Sprint 13)
- `int_toronto__neighbourhood_profile` denominator bug: `neighbourhood_category_totals` now uses `MAX(category_total)` from section header rows instead of `SUM(count)` — eliminates 1.5–2x inflation from subtotal contamination; `pct_of_neighbourhood` now correctly sums to ~100% per category
- `stg_toronto__profiles` now exposes `category_total` and `indent_level` columns (were silently stripped from explicit column list)

### Changed (Sprint 13)
- `mart_neighbourhood_demographics` now reads from `int_neighbourhood__foundation` instead of `int_neighbourhood__demographics`
- `int_neighbourhood__demographics` soft-deprecated (`meta: deprecated: true`); kept for backward compatibility until webapp switchover

### Added (Sprint 12 — Toronto Restructure Phase 1: Raw Layer)
- `fact_census_extended` table in `raw_toronto` schema with ~55 scalar indicators per neighbourhood per census year
- `category_total` and `indent_level` columns to `fact_neighbourhood_profile` (denominator bug fix foundation)
- `CensusExtendedRecord` Pydantic schema and `FactCensusExtended` SQLAlchemy model
- `census_extended_loader.py` — upsert loader for census extended data
- `get_census_extended()` parser with exact label matching and smart quote normalization for Statistics Canada XLSX
- `_normalize_key()` helper for Unicode apostrophe normalization (U+2019 → ASCII)
- 12 new profile categories: `religion`, `education_level`, `field_of_study`, `commute_mode`, `commute_duration`, `commute_destination`, `housing_suitability`, `dwelling_type`, `bedrooms`, `construction_period`, `mother_tongue`, `indigenous_identity` (total: 22 categories, up from 10)
- DB migration: `ix_fact_profile_indent` composite index on `(neighbourhood_id, category, indent_level)`
- ETL step `_load_census_extended()` in `load_toronto_data.py`
- dbt `accepted_values` expanded to 22 profile categories in `_staging.yml` and `_marts.yml`
- `scripts/data/xlsx_diagnostic.py` — XLSX label validation utility

### Fixed (Sprint 12)
- Profile `UniqueConstraint` extended to include `indent_level` as 6th discriminator (fixes hierarchical subcategory collisions)
- 21 `CENSUS_EXTENDED_MAPPING` label corrections (wrong label text, missing "in private households" phrase, wrong sample type suffix, comma differences)
- `field_of_study` section anchor scoped to 15+ population section (prevents duplicate rows from XLSX 25–64 population section)

---

## [0.1.0] - 2026-02-10

### Added
- Initial data pipeline for Toronto neighbourhood analysis
- PostgreSQL + PostGIS database schema (`raw_toronto`, `mart_toronto`)
- dbt models for data transformation (staging → intermediate → marts)
- ETL scripts for Toronto Open Data, Toronto Police API, CMHC data
- Parsers, loaders, schemas, and SQLAlchemy models for Toronto data domain
- VPS deployment documentation (`docs/deployment/vps-deployment.md`)
- Shared PostgreSQL setup guide (`docs/deployment/shared-postgres.md`)
- Cron-based ETL deployment strategy

### Changed
- Repository scope reduced to data-only pipeline (removed ~7,000 lines of frontend Dash code)
- Package renamed `portfolio_app` → `dataflow`
- CI/CD workflows updated for data-only deployment

### Removed
- All frontend code: Dash app, pages, figures, components, callbacks
- Frontend dependencies: dash, plotly, dash-mantine-components
- Blog content system and Markdown utilities

### Fixed
- Enum linting warnings (upgraded to `StrEnum`)
