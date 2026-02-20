-- Test Query: Validate Income Imputation Implementation
--
-- Run this query after `dbt run` to verify the income imputation logic is working correctly
--
-- Expected Results:
-- - 2021: is_income_imputed = FALSE (actual census data)
-- - 2016-2020: is_income_imputed = TRUE (CPI-adjusted estimates)
-- - Income values for 2016 should be ~9% lower than 2021 (CPI adjustment)

-- Test 1: Check imputation flag distribution
SELECT
    census_year,
    is_income_imputed,
    COUNT(*) as neighbourhood_count,
    COUNT(median_household_income) as with_income_data,
    ROUND(AVG(median_household_income), 2) as avg_median_income
FROM int_toronto.int_neighbourhood__demographics
GROUP BY census_year, is_income_imputed
ORDER BY census_year DESC, is_income_imputed;

-- Expected output:
-- census_year | is_income_imputed | neighbourhood_count | with_income_data | avg_median_income
-- 2021        | FALSE            | 158                 | 158              | ~$XX,XXX (actual)
-- 2016        | TRUE             | 132                 | 132              | ~90.68% of 2021

-- Test 2: Compare 2016 vs 2021 for same neighbourhoods
WITH income_comparison AS (
    SELECT
        neighbourhood_id,
        neighbourhood_name,
        census_year,
        median_household_income,
        is_income_imputed
    FROM int_toronto.int_neighbourhood__demographics
    WHERE census_year IN (2016, 2021)
        AND median_household_income IS NOT NULL
)
SELECT
    i2021.neighbourhood_id,
    i2021.neighbourhood_name,
    i2016.median_household_income as income_2016_imputed,
    i2021.median_household_income as income_2021_actual,
    i2016.is_income_imputed as is_2016_imputed,
    i2021.is_income_imputed as is_2021_imputed,
    ROUND(i2016.median_household_income / i2021.median_household_income, 4) as ratio_2016_to_2021,
    ROUND(128.4 / 141.6, 4) as expected_cpi_ratio
FROM income_comparison i2021
LEFT JOIN income_comparison i2016
    ON i2021.neighbourhood_id = i2016.neighbourhood_id
    AND i2016.census_year = 2016
WHERE i2021.census_year = 2021
LIMIT 10;

-- Expected: ratio_2016_to_2021 should equal expected_cpi_ratio (0.9068)

-- Test 3: Check mart table has the flag
SELECT
    year,
    is_income_imputed,
    COUNT(*) as count,
    COUNT(median_household_income) as with_income,
    ROUND(AVG(median_household_income), 2) as avg_income
FROM mart_toronto.mart_neighbourhood_demographics
GROUP BY year, is_income_imputed
ORDER BY year DESC, is_income_imputed;

-- Test 4: Verify income quintiles are calculated correctly
SELECT
    census_year,
    income_quintile,
    COUNT(*) as neighbourhood_count,
    ROUND(MIN(median_household_income), 2) as min_income,
    ROUND(MAX(median_household_income), 2) as max_income,
    ROUND(AVG(median_household_income), 2) as avg_income
FROM int_toronto.int_neighbourhood__demographics
WHERE median_household_income IS NOT NULL
GROUP BY census_year, income_quintile
ORDER BY census_year DESC, income_quintile;

-- Expected: Each quintile should have roughly equal counts (~31-32 neighbourhoods for 2021, ~26-27 for 2016)

-- Test 5: Check for NULL income values (should only be pre-2016 or neighbourhoods without 2021 baseline)
SELECT
    census_year,
    COUNT(*) as total_neighbourhoods,
    COUNT(median_household_income) as with_income,
    COUNT(*) - COUNT(median_household_income) as nulls
FROM int_toronto.int_neighbourhood__demographics
GROUP BY census_year
ORDER BY census_year DESC;

-- Expected:
-- 2021: 158 total, 158 with income, 0 nulls
-- 2016: 132 total, 132 with income, 0 nulls (if 2021 baseline exists for all)
