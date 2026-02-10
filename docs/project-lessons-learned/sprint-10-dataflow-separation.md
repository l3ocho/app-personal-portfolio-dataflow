# Sprint 10: Dataflow Separation

**Date**: 2026-02-10
**Status**: ✅ Completed
**Milestone**: [Sprint 10](http://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/milestone/30)

## Summary

Successfully converted personal-portfolio-dataflow repository from mixed webapp/data pipeline to data-only repository. Removed all frontend code (~7,000 lines) and restructured as pure ETL/ELT pipeline.

## Objectives

- Remove all frontend code (Dash app, pages, figures, components)
- Rename `portfolio_app` → `dataflow` for clarity
- Remove frontend dependencies
- Create VPS deployment documentation
- Prepare for production deployment with shared PostgreSQL

## Results

✅ **All 9 issues completed**
- 95 files changed (1,191 insertions, 8,228 deletions)
- Net reduction: ~7,000 lines of code
- 0 linting errors, all tests passing
- Documentation updated for data-only focus

## Key Changes

### Removed
- `app.py` - Dash application
- `pages/` - All page components (11 files)
- `figures/` - Chart factories (8 files)
- `components/` - UI components (5 files)
- `callbacks/` - Dash callbacks (4 files)
- `assets/`, `content/`, `design/`, `utils/` - Frontend support
- `toronto/services/` - Query functions (moved to webapp)

### Restructured
- Renamed `portfolio_app/` → `dataflow/`
- Updated 13 Python files with new imports
- Simplified `config.py` (removed Dash-specific settings)
- Updated Makefile (removed `run` target)
- Updated CI workflows for data-only deployment

### Added
- `docs/deployment/vps-deployment.md` - Complete VPS deployment guide
- `docs/deployment/shared-postgres.md` - Multi-database PostgreSQL setup
- `CHANGELOG.md` - Project changelog

### Fixed
- 8 enum linting warnings (upgraded `(str, Enum)` → `StrEnum`)

## Technical Notes

### Package Rename Strategy
- Used `mv portfolio_app dataflow` for directory rename
- Applied `sed` bulk replacement for import statements across all Python files
- Updated `pyproject.toml` package references and isort config
- No import errors after rename

### Dependency Cleanup
**Removed:**
- dash, plotly, dash-mantine-components, dash-iconify
- python-frontmatter, markdown, pygments

**Retained:**
- PostgreSQL/PostGIS, SQLAlchemy, Pydantic
- pandas, geopandas, shapely
- dbt-postgres
- Testing tools (pytest, ruff, mypy)

### CI/CD Updates
- Modified `.gitea/workflows/ci.yml` to use `pip install -e ".[dev,dbt]"`
- Updated deploy workflows to use `portfolio-dataflow` directory path
- Removed health check endpoints (no web server)

## Deployment Model

**VPS Architecture:**
```
/opt/apps/
├── docker-compose.yml          # Shared PostgreSQL
├── portfolio-dataflow/         # This repo (cron-based ETL)
└── portfolio-webapp/           # Separate frontend repo
```

**ETL Scheduling:**
- Daily data refresh: 2 AM
- dbt models: 3 AM
- dbt tests: 4 AM
- Weekly full refresh: Sunday 1 AM

## Challenges & Solutions

None reported. Sprint executed smoothly with no major blockers.

## Metrics

- **Duration**: Single sprint session
- **Issues**: 9/9 completed
- **Code Changes**: -7,000 lines
- **Test Status**: ✅ All passing
- **Linting**: ✅ Clean

## Recommendations

1. **Deploy to VPS** following `docs/deployment/vps-deployment.md`
2. **Set up shared PostgreSQL** using `docs/deployment/shared-postgres.md`
3. **Configure cron jobs** for automated ETL
4. **Adapt webapp repository** to remove data pipeline code and keep only frontend

## Related Documentation

- [VPS Deployment Guide](../deployment/vps-deployment.md)
- [Shared PostgreSQL Setup](../deployment/shared-postgres.md)
- [README.md](../../README.md)
- [CLAUDE.md](../../CLAUDE.md)

## Git References

- **Commit**: [b2526da](http://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/commit/b2526da)
- **CHANGELOG**: [976b4f7](http://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow/commit/976b4f7)
- **Branch**: development

---

*Sprint closed: 2026-02-10*
