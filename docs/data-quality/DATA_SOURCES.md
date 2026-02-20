# Data Sources and Quality Notes

This document describes the data sources used in the Toronto Neighbourhood Analytics project and documents known data quality issues, limitations, and imputation methods.

## Data Sources

### Toronto Open Data Portal

**Provider**: City of Toronto
**URL**: https://open.toronto.ca/

#### 1. Neighbourhood Profiles (Census)

**Dataset**: `neighbourhood-profiles`
**API**: Toronto Open Data CKAN API
**Coverage**: 2016, 2021 Census

**Available Granularity**:
- **2021 Census**: 158 neighbourhoods - ✅ Complete data including income metrics
- **2016 Census**: 140 neighbourhoods - ⚠️ Missing neighbourhood-level income data

**Key Indicators**:
- Population ✅
- Population density ✅
- Median age ✅
- Unemployment rate ✅
- Housing tenure (owner/renter %) ✅
- **Education levels (% bachelor's degree or higher)** (2021 only at neighbourhood level)
- **Average dwelling value** (2021 only at neighbourhood level)
- **Median household income** (2021 only at neighbourhood level)
- **Average household income** (2021 only at neighbourhood level)

**Known Limitations**:

##### 2016 Census Neighbourhood-Level Data Gap

**Issue**: The 2016 census dataset from Toronto Open Data Portal contains neighbourhood-level data for most indicators, but the following are only available as city-wide aggregates, not at the neighbourhood level:
- **Median household income**
- **Average household income**
- **Education (% bachelor's degree or higher)**
- **Average dwelling value**

**Investigation**:
- Confirmed via API queries (datastore search returns blank values)
- Confirmed via CSV download (`neighbourhood-profiles-2016-140-model.csv` - rows 1019-1029 blank for neighbourhoods)
- Statistics Canada published 2016 income data at city level but Toronto did not publish neighbourhood-level disaggregation

**Impact**:
- Years 2016-2020 would have NULL values for income, education, and dwelling metrics
- This affects:
  - Income-based analysis (quintile calculations, housing affordability)
  - Education attainment trends
  - Dwelling value appreciation analysis
  - Socioeconomic composite scores

**Solution**: CPI-based imputation for all four metrics (see below)

#### 2. Neighbourhood Community Profile Data (2021)

**Dataset**: `neighbourhood-profiles` (same as census, but different extraction)
**Coverage**: 2021 Census only - 158 neighbourhoods
**Data Format**: Long/narrow fact table (one row per neighbourhood × category × subcategory)

**Categories Extracted** (10 total):
- Immigration status (immigrants, non-permanent residents, etc.)
- Place of birth (by country and continent level)
- Citizenship status
- Generation status (1st, 2nd, 3rd+ generation)
- Admission category (economic, family-sponsored, refugee, etc.)
- Visible minority status (14 categories + "Not a visible minority")
- Ethnic origin (top 30 by city-wide count)
- Mother tongue (top 15 non-official languages per neighbourhood + English + French)
- Official language (English only, French only, Both, Neither)

**Key Features**:
- ✅ One row per neighbourhood-category-subcategory combination
- ✅ Includes StatCan suppression codes (NULL counts for small populations)
- ✅ Place of birth hierarchy level flagged (continent vs country)
- ✅ Mother tongue filtered to top-15 per neighbourhood (avoids 300+ language rows)
- ✅ Ethnic origin filtered to top-30 city-wide (avoids 200+ ethnicity rows)

**Quality Notes**:
- **Mother tongue**: Only top-15 non-official languages extracted per neighbourhood to avoid data explosion; always includes English and French totals
- **Ethnic origin**: Multi-response data; neighbourhood totals may exceed population (people report multiple origins)
- **Place of birth**: Available at both country and continent levels; continent totals provided for context
- **StatCan suppression**: Small population cells marked as NULL; documented in `count` column

**Data Lineage**:
```
Toronto Open Data XLSX (neighbourhood-profiles 2021)
  ↓
raw_toronto.fact_neighbourhood_profile (Python parser)
  ↓
stg_toronto__profiles (dbt staging - normalization)
  ↓
int_toronto__neighbourhood_profile (dbt intermediate - percentages + Shannon diversity)
  ↓
mart_toronto__neighbourhood_profile (dbt mart - final consumption)
```

**Downstream Use**:
- `mart_neighbourhood_demographics` enriched with profile summary columns:
  - `pct_immigrant` (from immigration_status)
  - `pct_visible_minority` (from visible_minority)
  - `pct_neither_official_lang` (from official_language)
  - `diversity_index` (Shannon entropy on visible_minority)

---

## Data Quality: Imputation Methods

### Census Data Imputation (2016-2020)

Since 2016 census data for income, education, and dwelling values is not available at neighbourhood level, we use **backward inflation adjustment** from 2021 census values to estimate 2016-2020 data.

#### Method

**Baseline**: 2021 census neighbourhood-level data (actual observed values)
- Median household income
- Average household income
- Education (% bachelor's degree or higher)
- Average dwelling value

**Adjustment**: Statistics Canada Consumer Price Index (CPI) All-Items for Toronto

**Formula**:
```
income_year = income_2021 × (CPI_year / CPI_2021)
```

#### CPI Reference Values

| Year | CPI Value | Adjustment Factor | Example: $80k income / 42% edu / $1.9M dwelling in 2021 → |
|------|-----------|-------------------|-----------------------------------------------------------|
| 2016 | 128.4 | 0.9068 | $72,544 income / 38.1% edu / $1.72M dwelling |
| 2017 | 130.4 | 0.9209 | $73,672 income / 38.7% edu / $1.75M dwelling |
| 2018 | 133.4 | 0.9421 | $75,368 income / 39.6% edu / $1.79M dwelling |
| 2019 | 136.0 | 0.9605 | $76,840 income / 40.3% edu / $1.82M dwelling |
| 2020 | 137.0 | 0.9676 | $77,408 income / 40.6% edu / $1.84M dwelling |
| 2021 | 141.6 | 1.0000 | $80,000 / 42.0% / $1.90M (baseline - actual census) |

**Source**: Statistics Canada Table 18-10-0004-01 - Consumer Price Index, monthly, not seasonally adjusted

#### Implementation

**Location**: `dbt/models/intermediate/toronto/int_neighbourhood__demographics.sql`

**Logic**:
1. Extract 2021 census baseline values for each neighbourhood:
   - `median_household_income`
   - `average_household_income`
   - `education_bachelors_pct`
   - `average_dwelling_value`
2. For years 2016-2020, multiply 2021 values by the corresponding CPI adjustment factor
3. For 2021, use actual census values (no adjustment)
4. Set `is_imputed = true` flag for all imputed values

**Transparency**:
- All imputed values are flagged with `is_imputed = true`
- SQL comments document the imputation method
- This documentation provides full methodology

#### Limitations

**Important**: These are **estimates**, not observed census values.

**Assumptions**:
- Assumes neighbourhood-level changes mirror city-wide inflation
- Does not account for:
  - **Income**: Neighbourhood-specific economic growth/decline, gentrification, local employment shocks
  - **Education**: Changes in demographic composition, university/college proximity effects
  - **Dwelling Value**: Neighbourhood-specific real estate appreciation, redevelopment, transit infrastructure impacts

**When to use**:
- ✅ Time-series trend analysis (relative changes over time)
- ✅ Comparative analysis (neighbourhood rankings, quintiles)
- ✅ Housing affordability estimates (income-to-rent ratios)
- ✅ Socioeconomic composite scores (combining income, education, dwelling value)
- ✅ Education attainment trends
- ✅ Dwelling value appreciation analysis

**When NOT to use**:
- ❌ Precise point-in-time estimates for 2016-2020
- ❌ Validating against external 2016 census data
- ❌ Regulatory/compliance reporting requiring actual census values
- ❌ Education policy analysis requiring exact attainment rates
- ❌ Real estate appraisals (dwelling values are estimates, not actual market values)

#### Validation

To verify the imputation quality, compare:
1. **2021 actual vs 2016 imputed**: Forward-adjust 2016 imputed values and compare to 2021 actual
2. **City-wide aggregate**: Sum of neighbourhood estimates should approximate city-wide CPI-adjusted value
3. **Quintile stability**: Neighbourhood income quintile rankings should be relatively stable 2016→2021

---

## Future Improvements

### Potential Alternative Data Sources

1. **Statistics Canada Census Profile Tables**: Check if neighbourhood-level 2016 income data exists in raw Census tables (DA/CT aggregation)
2. **T1 Family File**: Administrative tax data (requires Research Data Centre access)
3. **Census Tract Aggregation**: Aggregate Census Tract (CT) level income to neighbourhoods using spatial weights

### Forward-Fill Strategy

For years between censuses (2017-2020), consider:
- **Linear interpolation** between 2016 (imputed) and 2021 (actual)
- **Polynomial interpolation** if more than 2 census points available
- **Housing price index correlation**: Use MLS price changes as proxy for income changes

---

## Data Lineage

| Source | Raw Schema | Staging | Intermediate | Mart |
|--------|------------|---------|--------------|------|
| Toronto Open Data (2021) | `raw_toronto.fact_census` | `stg_toronto__census` | `int_neighbourhood__demographics` | `mart_neighbourhood_demographics` |
| Toronto Open Data (2016) | `raw_toronto.fact_census` | `stg_toronto__census` | `int_neighbourhood__demographics` (imputed) | `mart_neighbourhood_demographics` |

**Imputation Layer**: `int_neighbourhood__demographics` (dbt intermediate model)

**Consumer Tables**:
- `mart_neighbourhood_demographics`
- `mart_neighbourhood_overview` (via demographics join)
- `mart_neighbourhood_housing` (via demographics join)

---

## Contact

For questions about data quality or imputation methodology:
- Check project documentation: `/docs/`
- Review dbt model SQL: `/dbt/models/intermediate/toronto/`
- Consult CLAUDE.md project instructions

---

*Last Updated: 2026-02-19*
