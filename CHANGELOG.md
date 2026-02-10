# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Converted repository to data-only pipeline (Sprint 10)
- Renamed `portfolio_app` package to `dataflow`
- Simplified configuration for data pipeline focus
- Updated CI/CD workflows for data-only deployment

### Removed
- All frontend code (Dash app, pages, figures, components, callbacks)
- Frontend dependencies (dash, plotly, dash-mantine-components)
- Blog content and markdown utilities
- Removed ~7,000 lines of code

### Added
- VPS deployment documentation (`docs/deployment/vps-deployment.md`)
- Shared PostgreSQL setup guide (`docs/deployment/shared-postgres.md`)
- Cron-based ETL deployment strategy

### Fixed
- Enum linting warnings (upgraded to StrEnum)

## [0.1.0] - 2026-02-10

### Added
- Initial data pipeline for Toronto neighbourhood analysis
- PostgreSQL + PostGIS database schema
- dbt models for data transformation
- ETL scripts for Toronto Open Data, Police API, CMHC data
- Parsers, loaders, schemas, and models for Toronto data
