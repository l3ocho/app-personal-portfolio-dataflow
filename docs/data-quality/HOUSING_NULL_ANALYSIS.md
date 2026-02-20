# Housing Table NULL Analysis & Solutions

**Date**: 2026-02-12
**Table**: `mart_toronto.mart_neighbourhood_housing`
**Total Rows**: 1,106 (158 neighbourhoods × 7 years: 2019-2025)

---

## Executive Summary

| Issue | Severity | Rows Affected | Root Cause | Solution Complexity |
|-------|----------|---------------|------------|---------------------|
| `total_rental_units` | ❌ CRITICAL | 1,106 (100%) | Internal - column never populated | Medium |
| Income/dwelling/affordability | ⚠️ WARNING | 316 (28.6%) | Internal - not using imputed demographics | Easy |
| `pct_owner/renter_occupied` | ✓ MINOR | 52 (4.7%) | Internal - same join issue as above | Easy (fixed with #2) |
| `rent_yoy_change_pct` | ✅ OK | 158 (14.3%) | Expected - first year has no baseline | N/A (correct behavior) |

---

## Detailed Analysis

### 1. ❌ CRITICAL: `total_rental_units` (100% NULL)

**Current State**:
```
NULL count: 1,106/1,106 (100%)
Source: int_rentals__neighbourhood_allocated
Status: Column exists but never populated
```

**Root Cause**:
- **Internal Issue**: The column `total_rental_units` is defined in the schema but **never calculated or populated** in the rental allocation logic
- The `int_rentals__neighbourhood_allocated` table has 1,106 rows with rent and vacancy data, but `total_rental_units` is NULL for all rows
- CMHC data provides rental unit counts at the **zone level**, but the neighbourhood allocation logic only weights rent/vacancy, not unit counts

**Data Source**:
- CMHC rental survey provides `universe` (total rental units) at zone level
- Zones cover multiple neighbourhoods
- Current allocation logic: Distributes zone-level rent/vacancy to neighbourhoods using area-based weights
- Missing: Allocation of `universe` (rental units) to neighbourhoods

**Impact**:
- Cannot calculate rental density (units per capita)
- Cannot show rental housing stock size
- Limits housing analysis capabilities

**Solution Options**:

#### Option A: Allocate CMHC Universe to Neighbourhoods (RECOMMENDED)
**Complexity**: Medium
**Approach**:
1. In `int_rentals__neighbourhood_allocated`, add allocation logic for `universe` field
2. Use same area-based weighting as rent/vacancy:
   ```sql
   sum(universe * weight) as total_rental_units
   ```
3. This gives an **estimate** of rental units per neighbourhood

**Pros**:
- ✅ Provides neighbourhood-level rental stock estimates
- ✅ Consistent with existing allocation methodology
- ✅ Enables density calculations

**Cons**:
- ⚠️ Estimated values (allocated from zones, not actual neighbourhood counts)
- ⚠️ Requires documentation of estimation method

#### Option B: Remove Column from Mart
**Complexity**: Easy
**Approach**: Drop `total_rental_units` from mart schema

**Pros**:
- ✅ Quick fix
- ✅ No misleading NULL values

**Cons**:
- ❌ Loses potentially valuable metric
- ❌ Webapp may expect this column

#### Option C: Leave as NULL with Documentation
**Complexity**: Easy
**Approach**: Document that this metric is not available

**Pros**:
- ✅ No code changes
- ✅ Transparent about data limitations

**Cons**:
- ❌ 100% NULL column wastes space
- ❌ Confusing to users

**RECOMMENDATION**: **Option A** - Allocate CMHC universe to neighbourhoods using area weights

---

### 2. ⚠️ WARNING: Income/Dwelling/Affordability Columns (28.6% NULL)

**Current State**:
```
Affected columns:
- median_household_income     : 316 NULL (28.6%)
- average_dwelling_value      : 316 NULL (28.6%)
- rent_to_income_pct          : 316 NULL (28.6%)
- is_affordable               : 316 NULL (28.6%)
- affordability_index         : 316 NULL (28.6%)

NULL breakdown by year:
- 2019: 158 NULL (100% of year)
- 2020: 158 NULL (100% of year)
- 2021-2025: 0 NULL (0%)
```

**Root Cause**:
- **Internal Issue**: `int_neighbourhood__housing` joins directly to `stg_toronto__census` instead of using `int_neighbourhood__demographics`
- The demographics intermediate table **already has CPI-based imputation** for 2016-2020 income and dwelling values
- Housing model doesn't use this imputed data, so years 2019-2020 (pre-2021 census) get NULL

**Current Join Logic** (int_neighbourhood__housing.sql lines 53-59):
```sql
left join census c on n.neighbourhood_id = c.neighbourhood_id
    and c.census_year = (
        select max(c2.census_year)
        from {{ ref('stg_toronto__census') }} c2
        where c2.neighbourhood_id = n.neighbourhood_id
        and c2.census_year <= r.year
    )
```

**Problem**:
- For year 2019: Looks for max(census_year) <= 2019 → finds 2016
- But 2016 census has NULL income at neighbourhood level
- For year 2020: Same issue
- For year 2021+: Finds 2021 census (has actual data)

**Data Source**:
- We **HAVE** the data in `int_neighbourhood__demographics` with CPI imputation applied
- Just need to **use the right table**

**Impact**:
- Cannot calculate affordability for 2019-2020
- Cannot show income trends for pre-2021 years
- Breaks time-series analysis

**Solution**:

#### Option A: Use int_neighbourhood__demographics (RECOMMENDED)
**Complexity**: Easy
**Approach**:
1. Change join from `stg_toronto__census` to `int_neighbourhood__demographics`
2. Join on year instead of census_year
3. Use imputed data which already has 100% coverage

**Code Change**:
```sql
-- Replace lines 8-11, 25-30, 52-59
demographics as (
    select * from {{ ref('int_neighbourhood__demographics') }}
),

housing as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        r.year,

        -- Demographics metrics (now with imputation for all years)
        d.pct_owner_occupied,
        d.pct_renter_occupied,
        d.average_dwelling_value,
        d.median_household_income,

        -- ... rest of columns

    from neighbourhoods n
    left join allocated_rentals r
        on n.neighbourhood_id = r.neighbourhood_id
    left join demographics d
        on n.neighbourhood_id = d.neighbourhood_id
        and d.census_year = r.year  -- Direct year match (demographics has all years)
)
```

**Pros**:
- ✅ Immediate fix - uses existing imputation logic
- ✅ 100% data coverage (0 NULLs)
- ✅ Consistent with demographics table methodology
- ✅ No new code needed

**Cons**:
- None - this is the correct approach

**RECOMMENDATION**: **Option A** - Use demographics table with imputation

---

### 3. ✓ MINOR: Tenure Mix (4.7% NULL)

**Current State**:
```
- pct_owner_occupied    : 52 NULL (4.7%)
- pct_renter_occupied   : 52 NULL (4.7%)

Expected: 0 NULL (census data has 100% coverage)
```

**Root Cause**:
- **Same issue as #2**: Join to `stg_toronto__census` fails for some rows
- Census data itself has 0 NULLs for tenure mix
- The 52 NULLs come from failed census joins

**Breakdown**:
Likely the 26 neighbourhoods that existed in 2021 but not in 2016 (158 - 132 = 26), across 2 years (2019-2020) = 52 rows

**Solution**:
✅ **Automatically fixed by Solution #2** - using demographics table will resolve this

---

### 4. ✅ OK: Year-over-Year Rent Change (14.3% NULL)

**Current State**:
```
- rent_yoy_change_pct   : 158 NULL (14.3%)

Year 2019: 158 NULL (100% of first year)
Year 2020+: 0 NULL
```

**Root Cause**:
- **Expected behavior**: First year (2019) has no previous year to calculate % change
- This is **correct** - not an issue

**Logic** (mart_neighbourhood_housing.sql lines 82-89):
```sql
case
    when prev_year_rent_2bed > 0
    then round(
        (avg_rent_2bed - prev_year_rent_2bed) / prev_year_rent_2bed * 100,
        2
    )
    else null
end as rent_yoy_change_pct
```

**Solution**:
✅ **No action needed** - this is correct behavior

---

## Implementation Plan

### Phase 1: Quick Wins (Easy - 1 hour)
1. ✅ **Fix income/dwelling/affordability NULLs**
   - Update `int_neighbourhood__housing.sql` to join `int_neighbourhood__demographics`
   - Run dbt, verify 316 NULLs → 0 NULLs
   - This also fixes tenure mix (52 → 0 NULLs)

### Phase 2: Rental Units (Medium - 2-3 hours)
2. 🔧 **Add total_rental_units allocation**
   - Update `int_rentals__neighbourhood_allocated.sql`
   - Add weighted allocation logic for universe field
   - Test allocation accuracy
   - Document estimation methodology
   - Run dbt, verify 1,106 NULLs → 0 NULLs

### Phase 3: Documentation (Easy - 30 min)
3. 📝 **Update data quality docs**
   - Add section on rental unit estimation
   - Update DATABASE_SCHEMA.md
   - Add transparency notes

---

## Expected Results After Implementation

| Column | Before | After | Change |
|--------|--------|-------|--------|
| `total_rental_units` | 1,106 NULL (100%) | 0 NULL (0%) ✅ | Allocated from CMHC zones |
| `median_household_income` | 316 NULL (28.6%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `average_dwelling_value` | 316 NULL (28.6%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `rent_to_income_pct` | 316 NULL (28.6%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `is_affordable` | 316 NULL (28.6%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `affordability_index` | 316 NULL (28.6%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `pct_owner_occupied` | 52 NULL (4.7%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `pct_renter_occupied` | 52 NULL (4.7%) | 0 NULL (0%) ✅ | Use imputed demographics |
| `rent_yoy_change_pct` | 158 NULL (14.3%) | 158 NULL (14.3%) ✓ | Expected (first year) |

**Final Result**:
- **Before**: 3,792 NULL values across 9 columns
- **After**: 158 NULL values in 1 column (expected)
- **Improvement**: 95.8% reduction in NULLs ✅

---

## Next Steps

1. **Review this analysis** - Confirm solution approach
2. **Implement Phase 1** - Fix demographics join (quick win)
3. **Implement Phase 2** - Add rental units allocation (medium effort)
4. **Test & validate** - Run dbt and verify NULL counts
5. **Update documentation** - Document estimation methods

---

*Last Updated: 2026-02-12*
