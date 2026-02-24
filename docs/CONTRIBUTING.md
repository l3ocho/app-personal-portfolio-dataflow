# Contributor Guide

This is a data engineering pipeline — no frontend code. Contributing means adding data sources, building parsers and loaders, extending dbt models, or adding new analytical domains.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Adding a New Data Source (within existing domain)](#adding-a-new-data-source)
3. [Adding a New dbt Model](#adding-a-new-dbt-model)
4. [Adding a New Domain](#adding-a-new-domain)
5. [Branch Workflow](#branch-workflow)
6. [Code Standards](#code-standards)
7. [Before You Commit](#before-you-commit)

---

## Development Setup

### Prerequisites

- Python 3.11+ (via pyenv recommended)
- Docker and Docker Compose

### Initial Setup

```bash
git clone https://gitea.hotserv.cloud/personal-projects/personal-portfolio-dataflow.git
cd personal-portfolio-dataflow

make setup        # Creates .venv, installs deps, copies .env.example
make docker-up    # Start PostgreSQL + PostGIS
make db-init      # Initialize schema + extensions
make load-toronto # Load Toronto data
make dbt-run      # Run dbt transformations
make dbt-test     # Validate output
```

### Useful Commands

```bash
make test        # Run pytest
make lint        # Run ruff linter
make format      # Auto-format with ruff
make typecheck   # Run mypy (strict)
make ci          # Full check: lint + typecheck + test
make dbt-run     # Run all dbt models
make dbt-test    # Run all dbt tests
make pgweb-up    # Browse database at http://localhost:8081
```

---

## Adding a New Data Source

To add a new data source within an existing domain (e.g., adding a new Toronto API):

### Step 1: Write the Parser

Create a new file in `dataflow/<domain>/parsers/`:

```python
# dataflow/toronto/parsers/new_source.py
"""Parser for <source name>."""

from ..schemas.new_schema import NewRecord


def fetch_new_data(url: str) -> list[NewRecord]:
    """Fetch and validate data from <source>.

    Returns list of validated Pydantic records.
    """
    # ... fetch + validate
    return [NewRecord(**row) for row in raw_data]
```

**Conventions:**
- Return Pydantic models, not raw dicts
- Normalize Unicode before string comparisons (see `_normalize_key()` in `parsers/toronto_open_data.py` for Stats Canada XLSX)
- Parser functions are pure — no DB calls
- Export new parsers from the domain's `parsers/__init__.py`

### Step 2: Define the Pydantic Schema

Create or extend a schema in `dataflow/<domain>/schemas/`:

```python
# dataflow/toronto/schemas/new_schema.py
"""Pydantic validation models for <source>."""

from pydantic import BaseModel, field_validator


class NewRecord(BaseModel):
    neighbourhood_id: int
    year: int
    value: float | None = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 2000:
            raise ValueError(f"Year {v} out of range")
        return v
```

### Step 3: Define the SQLAlchemy Model

Add a table to `dataflow/<domain>/models/`:

```python
# dataflow/toronto/models/facts.py (or a new file)
from sqlalchemy import Index, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from .dimensions import RAW_TORONTO_SCHEMA


class FactNewData(Base):
    __tablename__ = "fact_new_data"
    __table_args__ = (
        UniqueConstraint("neighbourhood_id", "year", name="uq_fact_new_data_key"),
        Index("ix_fact_new_data_nbhd_year", "neighbourhood_id", "year"),
        {"schema": RAW_TORONTO_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neighbourhood_id: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
```

### Step 4: Write the Loader

Create a loader in `dataflow/<domain>/loaders/`:

```python
# dataflow/toronto/loaders/new_loader.py
"""Loader for <source> data."""

from ..models.facts import FactNewData
from ..schemas.new_schema import NewRecord
from .base import get_session, upsert_by_key


def load_new_data(records: list[NewRecord]) -> int:
    """Upsert new data records into raw_toronto.fact_new_data.

    Returns number of rows affected.
    """
    rows = [
        {
            "neighbourhood_id": r.neighbourhood_id,
            "year": r.year,
            "value": r.value,
        }
        for r in records
    ]
    with get_session() as session:
        return upsert_by_key(session, FactNewData, rows, key_cols=["neighbourhood_id", "year"])
```

### Step 5: Wire into the ETL Script

Add the new step to `scripts/data/load_<domain>_data.py`:

```python
# In DataPipeline.run() or equivalent
def _load_new_data(self) -> None:
    logger.info("Loading new data...")
    records = fetch_new_data(NEW_DATA_URL)
    count = load_new_data(records)
    logger.info(f"Loaded {count} new_data rows")
```

### Step 6: Update the Schema Documentation

Add the new table to `docs/DATABASE_SCHEMA.md` under the appropriate raw schema section.

---

## Adding a New dbt Model

Always run `dbt parse` first to validate the existing project before adding models.

### Staging Model

For 1:1 source cleaning only — no business logic in staging:

```sql
-- dbt/models/staging/toronto/stg_toronto__new_data.sql
with source as (
    select * from {{ source('raw_toronto', 'fact_new_data') }}
),

renamed as (
    select
        neighbourhood_id,
        year,
        value::numeric(10, 2)  as value,
    from source
)

select * from renamed
```

Register the source in `dbt/models/staging/_sources.yml`:

```yaml
- name: raw_toronto
  tables:
    - name: fact_new_data
      description: "New data from <source>"
```

Add column documentation in `dbt/models/staging/toronto/_staging.yml`.

### Intermediate Model

For business logic, joins, aggregations:

```sql
-- dbt/models/intermediate/toronto/int_neighbourhood__new_analysis.sql
with foundation as (
    select * from {{ ref('int_neighbourhood__foundation') }}
),

new_data as (
    select * from {{ ref('stg_toronto__new_data') }}
),

joined as (
    select
        f.neighbourhood_id,
        f.year,
        n.value,
        -- business logic here
    from foundation f
    left join new_data n
        on f.neighbourhood_id = n.neighbourhood_id
        and f.year = n.year
)

select * from joined
```

**Rules:**
- Downstream intermediate models should reference `int_neighbourhood__foundation`, not individual staging models
- `int_neighbourhood__demographics` is soft-deprecated — do not add new references to it

### Mart Model

Marts are the read-only contract with the webapp. Column names and types are **locked once deployed to production**.

```sql
-- dbt/models/marts/toronto/mart_neighbourhood_new.sql
{{
    config(
        materialized='table',
        indexes=[{'columns': ['neighbourhood_id', 'year'], 'unique': True}]
    )
}}

with analysis as (
    select * from {{ ref('int_neighbourhood__new_analysis') }}
),

with_geometry as (
    select
        a.*,
        n.geometry,
        n.name as neighbourhood_name
    from analysis a
    left join {{ ref('stg_toronto__neighbourhoods') }} n
        on a.neighbourhood_id = n.neighbourhood_id
)

select * from with_geometry
```

Add documentation in `dbt/models/marts/_marts.yml`. Update `docs/DATABASE_SCHEMA.md`.

**Impact analysis before any mart change:**

```bash
# Check what depends on the model you're changing
cd dbt && dbt run --profiles-dir . --select +mart_neighbourhood_new+

# Check if mart columns are consumed by webapp
grep -r "mart_neighbourhood_new" /path/to/personal-portfolio/
```

---

## Adding a New Domain

A domain is a complete ETL stack for a new data subject area (e.g., `energy`, `real_estate`).

### Structure to Create

```
dataflow/<domain>/
├── __init__.py
├── parsers/
│   ├── __init__.py
│   └── <source>.py
├── schemas/
│   ├── __init__.py
│   └── <entity>.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── dimensions.py
│   └── facts.py
└── loaders/
    ├── __init__.py
    ├── base.py           # Can re-use from toronto
    └── loaders.py

dbt/models/
├── staging/<domain>/
│   ├── _sources.yml
│   └── stg_<domain>__*.sql
├── intermediate/<domain>/
│   ├── _intermediate.yml
│   └── int_<domain>__*.sql
└── marts/<domain>/
    ├── _marts.yml
    └── mart_<domain>_*.sql

scripts/data/
└── load_<domain>_data.py

# Register raw schema in scripts/db/init_schema.py
```

### Naming Conventions

| Layer | Pattern | Example |
|-------|---------|---------|
| Raw schema | `raw_<domain>` | `raw_energy` |
| Staging schema | `stg_<domain>` | `stg_energy` |
| Intermediate schema | `int_<domain>` | `int_energy` |
| Mart schema | `mart_<domain>` | `mart_energy` |
| Raw tables | `dim_*`, `fact_*`, `bridge_*` | `fact_energy_prices` |
| Staging models | `stg_<domain>__<entity>` | `stg_energy__prices` |
| Intermediate models | `int_<domain>__<transform>` | `int_energy__annual_summary` |
| Mart tables | `mart_<domain>_<subject>` | `mart_energy_market_overview` |

### Register Raw Schema

Add the new schema to `scripts/db/init_schema.py`:

```python
SCHEMAS_TO_CREATE = [
    "raw_toronto",
    "raw_football",
    "raw_energy",  # new
]
```

---

## Branch Workflow

```
main (production)
  ↑
staging (pre-production)
  ↑
development (integration)
  ↑
feature/<sprint>-<description> (your work)
```

```bash
# Start from development
git checkout development && git pull origin development

# Create feature branch (use gitflow plugin)
# /gitflow branch-start

# Work, then commit with conventional commits
# /gitflow commit

# Push and open PR to development
git push -u origin feature/<sprint>-<description>
```

**Rules:**
- Never commit directly to `main`, `staging`, or `development`
- Feature branches are temporary — delete after merge
- Use `/gitflow commit` for auto-generated conventional commit messages

---

## Code Standards

### Type Hints

Python 3.10+ syntax only:

```python
def load_records(records: list[NewRecord], dry_run: bool = False) -> int:
    ...

def parse_value(raw: str | None) -> float | None:
    ...
```

### Import Style

| Context | Style | Example |
|---------|-------|---------|
| Same directory | Single dot | `from .neighbourhood import NeighbourhoodRecord` |
| Sibling directory | Double dot | `from ..schemas.neighbourhood import CensusRecord` |
| External packages | Absolute | `import pandas as pd` |

### SQLAlchemy 2.0

Use 2.0-style mapped columns only:

```python
# Correct (2.0 style)
class MyModel(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

# Incorrect (legacy 1.x style)
# id = Column(Integer, primary_key=True)
```

### Pydantic 2.0

Use 2.0 validators only:

```python
# Correct (2.0 style)
@field_validator("year")
@classmethod
def validate_year(cls, v: int) -> int:
    ...

# Incorrect (legacy 1.x style)
# @validator("year")
# def validate_year(cls, v):
```

### Error Handling

Use custom exceptions from `dataflow/errors/exceptions.py`:

```python
from dataflow.errors.exceptions import ParseError, LoadError

def fetch_data(url: str) -> list[dict]:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ParseError(f"Failed to fetch {url}: {e}") from e
```

---

## Before You Commit

```bash
# 1. Run quality checks
make ci  # lint + typecheck + test

# 2. Validate dbt project syntax (always before dbt changes)
cd dbt && dbt parse --profiles-dir .

# 3. Run affected dbt models
make dbt-run

# 4. Run dbt tests
make dbt-test

# 5. Commit with conventional commit message
# /gitflow commit
```

**dbt mandatory rules:**
- Always `dbt parse` before `dbt run` — catches model errors early
- Never rename mart columns without coordinating with the webapp repo
- Run `dbt test` after any model change
- Check downstream impact: `dbt run --select +<changed_model>+`

---

## Questions?

- See `CLAUDE.md` for AI assistant context, code conventions, and mandatory behavior rules
- See `docs/PROJECT_REFERENCE.md` for architecture decisions and domain details
- See `docs/DATABASE_SCHEMA.md` for schema reference
