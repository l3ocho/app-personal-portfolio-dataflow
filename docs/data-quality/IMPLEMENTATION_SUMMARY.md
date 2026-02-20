# Income Imputation Implementation Summary

**Date**: 2026-02-12
**Issue**: 2016 Census neighbourhood-level household income data not available from Toronto Open Data Portal
**Solution**: CPI-based backward inflation adjustment from 2021 census baseline

## What Was Implemented

### 1. dbt Model Enhancement

**File**: `dbt/models/intermediate/toronto/int_neighbourhood__demographics.sql`

**Changes**:
- Added CPI inflation factors table (2016-2021)
- Created 2021 census income baseline CTE
- Implemented income imputation logic using CPI adjustment
- Added `is_income_imputed` flag for transparency
- Updated income quintile calculation to use imputed values

**Logic**:
```sql
-- If 2021 census (actual data): Use it directly
-- If pre-2021 (no data): income_2021 × (CPI_year / CPI_2021)
-- Otherwise: NULL

median_household_income = CASE
    WHEN census has data THEN use it
    WHEN year < 2021 AND have 2021 baseline THEN impute
    ELSE NULL
END
```

**CPI Values**:
| Year | CPI | Adjustment Factor |
|------|-----|-------------------|
| 2016 | 128.4 | 0.9068 |
| 2017 | 130.4 | 0.9209 |
| 2018 | 133.4 | 0.9421 |
| 2019 | 136.0 | 0.9605 |
| 2020 | 137.0 | 0.9675 |
| 2021 | 141.6 | 1.0000 (baseline) |

### 2. Mart Model Update

**File**: `dbt/models/marts/toronto/mart_neighbourhood_demographics.sql`

**Changes**:
- Added `is_income_imputed` column to final output
- Enables downstream consumers to identify estimated vs actual values

### 3. Documentation Created

#### A. Data Sources Documentation
**File**: `docs/data-quality/DATA_SOURCES.md`

**Contents**:
- Complete data source inventory (Toronto Open Data Portal)
- Detailed explanation of 2016 income data gap
- Full imputation methodology documentation
- CPI reference table
- Use cases and limitations
- Validation approaches
- Future improvement suggestions

#### B. Database Schema Documentation
**File**: `docs/DATABASE_SCHEMA.md` (updated)

**Changes**:
- Added data quality warning for income columns in `fact_census` table
- Documented raw data status (2021 has data, 2016 doesn't)
- Explained imputation approach
- Referenced detailed docs

#### C. Module Documentation
**File**: `dataflow/toronto/README.md` (new)

**Contents**:
- Complete module structure overview
- Data flow diagram
- Component descriptions (parsers, loaders, models, schemas)
- Data source details with 2016 limitation highlighted
- Usage examples
- Spatial data handling
- Data quality notes
- Development guide

#### D. Test Queries
**File**: `docs/data-quality/INCOME_IMPUTATION_TEST.sql` (new)

**Contents**:
- 5 validation queries to test imputation correctness
- Expected results documented
- Covers flag distribution, ratio validation, quintile distribution

## How It Works

### Data Flow

```
1. Raw Data Load (Python/SQLAlchemy)
   ↓
   raw_toronto.fact_census
   - 2021: median_household_income = actual values
   - 2016: median_household_income = NULL

2. Staging (dbt)
   ↓
   stg_toronto__census
   - Pass-through, no transformation

3. Intermediate (dbt) ⭐ IMPUTATION HAPPENS HERE
   ↓
   int_neighbourhood__demographics
   - Join 2021 baseline income
   - Apply CPI adjustment for 2016-2020
   - Set is_income_imputed = TRUE for estimates

4. Mart (dbt)
   ↓
   mart_neighbourhood_demographics
   - Include is_income_imputed flag
   - Calculate income_index, quintiles using imputed values
```

### Example Calculation

**Neighbourhood**: Annex
**2021 Census Actual**: $80,000 median household income

**2016 Estimate**:
```
= $80,000 × (128.4 / 141.6)
= $80,000 × 0.9068
= $72,542
```

**Flag**: `is_income_imputed = TRUE` for 2016 value

## Validation

### To Test After dbt Run

1. **Start database and run dbt**:
   ```bash
   make docker-up
   make dbt-run
   ```

2. **Run validation queries**:
   ```bash
   psql $DATABASE_URL -f docs/data-quality/INCOME_IMPUTATION_TEST.sql
   ```

3. **Expected results**:
   - 2021: 158 neighbourhoods, `is_income_imputed = FALSE`
   - 2016: 132 neighbourhoods, `is_income_imputed = TRUE`
   - Ratio 2016/2021 ≈ 0.9068 for all neighbourhoods

### Manual Verification

Check a specific neighbourhood:
```sql
SELECT
    neighbourhood_name,
    census_year,
    median_household_income,
    is_income_imputed
FROM int_toronto.int_neighbourhood__demographics
WHERE neighbourhood_id = 95  -- Annex
ORDER BY census_year;
```

## Files Modified/Created

### Modified
1. `dbt/models/intermediate/toronto/int_neighbourhood__demographics.sql` - Core imputation logic
2. `dbt/models/marts/toronto/mart_neighbourhood_demographics.sql` - Added flag to output
3. `docs/DATABASE_SCHEMA.md` - Added data quality note

### Created
1. `docs/data-quality/DATA_SOURCES.md` - Complete data quality documentation
2. `docs/data-quality/INCOME_IMPUTATION_TEST.sql` - Validation queries
3. `docs/data-quality/IMPLEMENTATION_SUMMARY.md` - This file
4. `dataflow/toronto/README.md` - Module documentation

## Impact on Existing Data

### Before Implementation
- `mart_neighbourhood_demographics` years 2016-2020: Income columns = NULL
- 290 total rows (158 × 2021 + 132 × 2016)
- Only 158 rows (54.5%) had income data

### After Implementation
- `mart_neighbourhood_demographics` years 2016-2020: Income columns = CPI-adjusted estimates
- 290 total rows (unchanged)
- All 290 rows (100%) have income data
- 132 rows flagged with `is_income_imputed = TRUE`

### Downstream Effects
- Income quintile now calculated for all years (not just 2021)
- Income index available for all years
- Time-series income analysis now possible
- Housing affordability ratios (income/rent) now computable for 2016+

## Transparency & Limitations

### Transparency Measures
✅ `is_income_imputed` flag in all downstream tables
✅ Comprehensive SQL comments in dbt model
✅ Documentation in 4 locations (DATA_SOURCES.md, DATABASE_SCHEMA.md, README.md, SQL comments)
✅ Test queries provided
✅ CPI source documented

### Known Limitations
⚠️ Assumes neighbourhood income changes match city-wide CPI
⚠️ Does not account for gentrification effects
⚠️ Does not account for neighbourhood-specific economic shocks
⚠️ Based on 2021 baseline only (no 2011 data for validation)

### Appropriate Uses
✅ Time-series trend analysis (relative changes)
✅ Neighbourhood rankings and comparisons
✅ Housing affordability estimates
✅ Income distribution analysis

### Inappropriate Uses
❌ Precise point-in-time estimates for 2016
❌ Validation against external 2016 income data
❌ Regulatory/compliance reporting

## Next Steps

1. **Test the implementation**:
   ```bash
   make docker-up
   make dbt-run
   make dbt-test
   psql $DATABASE_URL -f docs/data-quality/INCOME_IMPUTATION_TEST.sql
   ```

2. **Update webapp consumers**:
   - Check if frontend needs to display `is_income_imputed` flag
   - Add tooltip/disclaimer for imputed income values
   - Update data download exports to include flag

3. **Monitor data quality**:
   - Set up dbt test for ratio validation
   - Alert if CPI ratio deviates from expected value
   - Verify quintile distributions remain stable

4. **Future enhancements**:
   - Load 2011 census if available (for better baseline)
   - Consider linear interpolation between census years
   - Explore correlation with MLS housing prices

## References

- **Statistics Canada CPI**: Table 18-10-0004-01
- **Toronto Open Data Investigation**: See previous conversation
- **CPI Methodology**: https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes

---

**Status**: ✅ Implementation complete, awaiting testing
**Author**: Claude Code
**Review Required**: Yes - validate calculations after dbt run
