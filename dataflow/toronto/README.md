# Toronto Dataflow Module

This module contains the data acquisition, validation, and loading logic for Toronto neighbourhood analytics.

## Module Structure

```
dataflow/toronto/
├── __init__.py
├── demo_data.py          # Demo data generators
├── loaders/              # Database loading operations
│   ├── amenity.py        # Load amenity counts
│   ├── census.py         # Load census profiles
│   ├── crime.py          # Load crime statistics
│   └── neighbourhood.py  # Load neighbourhood boundaries
├── models/               # SQLAlchemy ORM models
│   ├── amenity.py
│   ├── census.py
│   ├── crime.py
│   └── neighbourhood.py
├── parsers/              # API data extraction
│   └── toronto_open_data.py  # Toronto Open Data Portal API client
└── schemas/              # Pydantic validation schemas
    ├── amenity.py
    ├── census.py
    ├── crime.py
    └── neighbourhood.py
```

## Data Flow

```
Toronto Open Data Portal API
          ↓
    parsers/ (extract & validate with Pydantic)
          ↓
    loaders/ (insert/upsert with SQLAlchemy)
          ↓
    PostgreSQL raw_toronto schema
          ↓
    dbt transformations (staging → intermediate → marts)
          ↓
    Analytical tables (consumed by webapp)
```

## Key Components

### Parsers (`parsers/toronto_open_data.py`)

**Purpose**: Fetch data from Toronto Open Data CKAN API and convert to Pydantic models

**Key Methods**:
- `get_neighbourhoods()` → List[NeighbourhoodRecord]
- `get_census_profiles(year)` → List[CensusRecord]
- `get_crime_data()` → List[CrimeRecord]
- `get_transit_stops()` → List[AmenityRecord]
- `get_parks()` → List[AmenityRecord]
- `get_libraries()` → List[AmenityRecord]
- `get_community_centres()` → List[AmenityRecord]

**Features**:
- Retry logic with exponential backoff
- Response validation with Pydantic
- Error logging
- Spatial matching for amenities (PostGIS ST_Contains)

### Schemas (`schemas/`)

**Purpose**: Pydantic models for data validation and type safety

**Key Schemas**:
- `NeighbourhoodRecord`: Neighbourhood boundaries and metadata
- `CensusRecord`: Census profile indicators
- `CrimeRecord`: Crime incidents
- `AmenityRecord`: Points of interest (transit, parks, libraries, community centres)

**Validation Rules**:
- Required fields enforcement
- Type coercion (str → int, str → float)
- Range validation (e.g., latitude/longitude bounds)
- Custom validators for spatial coordinates

### Loaders (`loaders/`)

**Purpose**: Insert or update records in PostgreSQL using SQLAlchemy ORM

**Pattern**: Upsert (insert or update on conflict)

**Key Functions**:
- `load_neighbourhoods(records, session)` → int (count inserted/updated)
- `load_census_data(records, session)` → int
- `load_crime_data(records, session)` → int
- `load_amenities(records, year, session)` → int

**Features**:
- Natural key-based upsert (prevents duplicates)
- Transaction management
- Bulk operations for performance
- Error logging

### Models (`models/`)

**Purpose**: SQLAlchemy ORM definitions for database tables

**Schema**: `raw_toronto`

**Tables**:
- `dim_neighbourhood`: 158 neighbourhood boundaries (SRID 4326)
- `fact_census`: Census profiles by neighbourhood × year
- `fact_crime`: Crime statistics by neighbourhood × year × type
- `fact_amenities`: Amenity counts by neighbourhood × type × year

## Data Sources

### Toronto Open Data Portal

**Base URL**: `https://ckan0.cf.opendata.inter.prod-toronto.ca`

**Datasets Used**:

| Dataset | Resource ID | Update Frequency | Coverage |
|---------|-------------|------------------|----------|
| Neighbourhoods | `neighbourhoods-planning-areas-wgs84` | As needed | 158 neighbourhoods (2021+) |
| Census 2021 | `neighbourhood-profiles` | Census years | 158 neighbourhoods |
| Census 2016 | `neighbourhood-profiles` | Census years | 140 neighbourhoods ⚠️ |
| Crime Data | `neighbourhood-crime-rates` | Annual | 2014-present |
| TTC Stops | `ttc-routes-and-schedules` | Monthly | Current stops |
| Parks | `parks-and-recreation-facilities` | Quarterly | Current facilities |
| Libraries | `library-branch-general-information` | Quarterly | TPL branches |

**⚠️ Important - 2016 Census Limitation**:

The 2016 census dataset from Toronto Open Data **does not include neighbourhood-level household income data**. Only city-wide aggregates are available.

**Impact**:
- `median_household_income` and `average_household_income` are NULL for 2016 census in raw data
- Income values for 2016-2020 are **imputed** in dbt transformations using backward inflation adjustment

**Solution**:
We use 2021 census income as baseline and apply Statistics Canada CPI backwards:
```
income_2016 = income_2021 × (CPI_2016 / CPI_2021)
```

**See**: `docs/data-quality/DATA_SOURCES.md` for complete imputation methodology.

## Usage

### Loading All Toronto Data

```bash
# Run the ETL script
python scripts/data/load_toronto_data.py
```

**This will**:
1. Fetch neighbourhoods from API
2. Load 2016 + 2021 census profiles
3. Load crime statistics
4. Load amenities (transit, parks, libraries, community centres)

### Loading Specific Datasets

```python
from dataflow.toronto.parsers.toronto_open_data import TorontoOpenDataParser
from dataflow.toronto.loaders.census import load_census_data
from dataflow.database import get_session

# Initialize parser
parser = TorontoOpenDataParser()

# Fetch 2021 census
census_records = parser.get_census_profiles(year=2021)

# Load to database
with get_session() as session:
    count = load_census_data(census_records, session)
    print(f"Loaded {count} census records")
```

## Spatial Data Handling

### Coordinate System

**SRID**: 4326 (WGS84)
- Longitude: -180 to 180
- Latitude: -90 to 90
- Toronto bounds: Lon ~-79.6 to -79.1, Lat ~43.6 to 43.9

### Spatial Operations

**Neighbourhood Matching**:

Amenities (libraries, parks, transit stops) are matched to neighbourhoods using PostGIS:

```sql
SELECT neighbourhood_id
FROM raw_toronto.dim_neighbourhood
WHERE ST_Contains(
    geometry,
    ST_SetSRID(ST_Point(longitude, latitude), 4326)
)
```

**Performed in**: `parsers/toronto_open_data.py._assign_neighbourhood_id()`

## Data Quality

### Natural Keys

All loaders use natural keys to prevent duplicates:

- **Neighbourhoods**: `neighbourhood_id`
- **Census**: `(neighbourhood_id, census_year)`
- **Crime**: `(neighbourhood_id, year, crime_type)`
- **Amenities**: `(neighbourhood_id, amenity_type, amenity_name, year)`

### Validation

**Schema-level** (Pydantic):
- Type validation
- Required fields
- Range checks

**Database-level** (PostgreSQL):
- NOT NULL constraints
- Foreign key constraints
- Unique constraints
- PostGIS geometry validation

### Error Handling

**Parser errors**:
- HTTP errors: Logged as warnings, returns empty list
- Validation errors: Skips invalid records, logs error

**Loader errors**:
- Integrity violations: Raises exception (fails fast)
- Duplicate keys: Performs upsert (updates existing)

## Transformation Pipeline (dbt)

After raw data loading, dbt performs transformations:

```
raw_toronto.fact_census
    ↓
stg_toronto__census (staging: 1:1 with source, typed)
    ↓
int_neighbourhood__demographics (intermediate: income imputation applied here)
    ↓
mart_neighbourhood_demographics (mart: final analytical table)
```

**Income Imputation** happens in `int_neighbourhood__demographics`:
- 2021 census: Use actual values
- 2016 census: Apply CPI-based backward adjustment from 2021
- Flag imputed values with `is_income_imputed = true`

## Development

### Adding a New Data Source

1. **Add parser method** in `parsers/toronto_open_data.py`
2. **Create Pydantic schema** in `schemas/`
3. **Create SQLAlchemy model** in `models/`
4. **Create loader function** in `loaders/`
5. **Update ETL script** `scripts/data/load_toronto_data.py`
6. **Add dbt staging model** `dbt/models/staging/toronto/stg_toronto__{entity}.sql`

### Testing

```bash
# Run data loading tests
pytest tests/dataflow/toronto/

# Run dbt tests
make dbt-test
```

## References

- **API Documentation**: https://open.toronto.ca/
- **Database Schema**: `/docs/DATABASE_SCHEMA.md`
- **Data Quality Notes**: `/docs/data-quality/DATA_SOURCES.md`
- **dbt Models**: `/dbt/models/`

---

*Last Updated: 2026-02-12*
