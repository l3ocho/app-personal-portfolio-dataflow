-- Intermediate: Neighbourhood foundation — scalar demographics + extended indicators
-- Grain: One row per neighbourhood per census year (316 rows: 158 × 2 census years)
-- Supersedes: int_neighbourhood__demographics (kept for backward compat, Sprint 13)
--
-- DATA QUALITY NOTE: Income Imputation for 2016-2020
-- ====================================================
-- 2016 census data from Toronto Open Data Portal lacks neighbourhood-level household income.
-- Only 2021 census contains median_household_income and average_household_income at neighbourhood grain.
--
-- Imputation Method:
-- - For years 2016-2020, we apply backward inflation adjustment from 2021 census values
-- - Uses Statistics Canada Consumer Price Index (CPI) All-Items for Toronto
-- - Formula: income_year = income_2021 × (CPI_year / CPI_2021)
--
-- CPI Reference Values:
-- - 2016: 128.4    - 2019: 136.0
-- - 2017: 130.4    - 2020: 137.0
-- - 2018: 133.4    - 2021: 141.6 (baseline)
--
-- Important: These are ESTIMATES, not observed census values.
-- The 'is_imputed' flag marks imputed values for transparency.
--
-- Extended Scalars: ~55 pre-computed indicators from fact_census_extended (Path B).
-- Age brackets (pop_0_to_14/15_24/25_64/65_plus) are not in the 2016 source XLSX.
-- For 2016 rows, they are estimated by scaling the 2021 counts by the 2016/2021
-- population ratio. The is_imputed flag covers these estimates.
-- Remaining extended columns are 2021-only and NULL for 2016 rows.
--
-- 2016 Coverage: 26 of the 34 new neighbourhood IDs (141-174) have no 2016
-- census data. Their 2016 rows are synthesized using 2021 values as baseline
-- (population, rates carried forward; income/education/dwelling CPI-imputed).
-- These rows are flagged: is_split_estimated = TRUE, is_imputed = TRUE.
-- NOTE: 8 new IDs (142, 146, 147, 149, 155, 156, 158, 172) already have real
-- 2016 census data and flow through the foundation CTE naturally.

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
),

census_extended as (
    select * from {{ ref('stg_toronto__census_extended') }}
),

-- CPI inflation factors (relative to 2021 baseline)
cpi_factors as (
    select 2016 as year, 128.4 / 141.6 as adjustment_factor union all
    select 2017, 130.4 / 141.6 union all
    select 2018, 133.4 / 141.6 union all
    select 2019, 136.0 / 141.6 union all
    select 2020, 137.0 / 141.6 union all
    select 2021, 1.0  -- No adjustment for 2021 (actual census data)
),

-- Get 2021 census baseline for imputation (income, education, dwelling value)
census_2021_baseline as (
    select
        neighbourhood_id,
        median_household_income as median_income_2021,
        average_household_income as average_income_2021,
        pct_bachelors_or_higher as education_2021,
        average_dwelling_value as dwelling_value_2021
    from census
    where census_year = 2021
),

-- Synthetic 2016 rows for new neighbourhood IDs (141-174) that lack real 2016 data.
-- The 2016 census used updated boundary IDs but only populated 8 of the 34 new
-- neighbourhoods (142, 146, 147, 149, 155, 156, 158, 172). The remaining 26 are
-- synthesised here using 2021 values as baseline: population and rates carried
-- forward unchanged; income/education/dwelling will be CPI-imputed downstream.
-- is_split_estimated = TRUE flags all synthetic rows.
distributed_2016 as (
    select
        c_2021.neighbourhood_id,
        2016                                                            as census_year,
        c_2021.population,
        c_2021.population_density,
        c_2021.median_age,
        c_2021.unemployment_rate,
        c_2021.pct_owner_occupied,
        c_2021.pct_renter_occupied
    from census c_2021
    where c_2021.census_year = 2021
      and c_2021.neighbourhood_id between 141 and 174
      and not exists (
          select 1 from census c_2016
          where c_2016.neighbourhood_id = c_2021.neighbourhood_id
            and c_2016.census_year = 2016
      )
),

-- 2021 baseline for age bracket carry-forward to 2016 rows.
-- Age brackets (pop_0_to_14 etc.) are not available in the 2016 XLSX source.
-- For 2016 rows, we estimate using the 2021 age distribution scaled by the 2016/2021
-- population ratio. This is the same imputation pattern used for income and education.
census_extended_2021_baseline as (
    select neighbourhood_id, population, pop_0_to_14, pop_15_to_24, pop_25_to_64, pop_65_plus
    from census_extended
    where census_year = 2021
),

-- Only 2021 extended census data is available from the source.
-- For 2016, we use core census fields only (income, age, education, housing tenure).
-- Extended fields (commuting, occupation, immigration, etc.) are only populated for 2021.
-- LEFT JOIN to census_extended: allows 2016 rows to flow through with NULL extended fields.
foundation as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        n.land_area_sqkm,

        -- Use census_year from census data, or fall back to dim_neighbourhood's year
        coalesce(c.census_year, n.census_year, 2021) as census_year,
        c.population,
        coalesce(
            c.population_density,
            case
                when n.land_area_sqkm > 0
                then round(c.population / n.land_area_sqkm, 2)
                else null
            end
        ) as population_density,

        -- Income imputation logic:
        -- - If census has income data (2021), use it directly
        -- - If no income data (2016) but we have 2021 baseline, apply CPI adjustment
        -- - Otherwise NULL
        case
            when c.median_household_income is not null then c.median_household_income
            when c.census_year < 2021 and c2021.median_income_2021 is not null
                then round(c2021.median_income_2021 * cpi.adjustment_factor, 2)
            else null
        end as median_household_income,

        case
            when c.average_household_income is not null then c.average_household_income
            when c.census_year < 2021 and c2021.average_income_2021 is not null
                then round(c2021.average_income_2021 * cpi.adjustment_factor, 2)
            else null
        end as average_household_income,

        c.median_age,
        c.unemployment_rate,

        -- Education imputation (same CPI adjustment)
        case
            when c.pct_bachelors_or_higher is not null then c.pct_bachelors_or_higher
            when c.census_year < 2021 and c2021.education_2021 is not null
                then round(c2021.education_2021 * cpi.adjustment_factor, 2)
            else null
        end as education_bachelors_pct,

        -- Dwelling value imputation (same CPI adjustment)
        case
            when c.average_dwelling_value is not null then c.average_dwelling_value
            when c.census_year < 2021 and c2021.dwelling_value_2021 is not null
                then round(c2021.dwelling_value_2021 * cpi.adjustment_factor, 0)
            else null
        end as average_dwelling_value,

        -- Flag to indicate imputed values for transparency
        case
            when c.census_year < 2021
                and (
                    (c.median_household_income is null and c2021.median_income_2021 is not null)
                    or (c.pct_bachelors_or_higher is null and c2021.education_2021 is not null)
                    or (c.average_dwelling_value is null and c2021.dwelling_value_2021 is not null)
                )
            then true
            else false
        end as is_imputed,

        -- Age distribution: 2021 actual; 2016 estimated by scaling 2021 counts by
        -- the 2016/2021 population ratio (same imputation pattern as income/education).
        coalesce(
            ce.pop_0_to_14,
            round(ce2021.pop_0_to_14 * c.population::numeric / nullif(ce2021.population, 0))::integer
        ) as pop_0_to_14,
        coalesce(
            ce.pop_15_to_24,
            round(ce2021.pop_15_to_24 * c.population::numeric / nullif(ce2021.population, 0))::integer
        ) as pop_15_to_24,
        coalesce(
            ce.pop_25_to_64,
            round(ce2021.pop_25_to_64 * c.population::numeric / nullif(ce2021.population, 0))::integer
        ) as pop_25_to_64,
        coalesce(
            ce.pop_65_plus,
            round(ce2021.pop_65_plus * c.population::numeric / nullif(ce2021.population, 0))::integer
        ) as pop_65_plus,

        -- Tenure mix
        c.pct_owner_occupied,
        c.pct_renter_occupied

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
    left join census_2021_baseline c2021 on n.neighbourhood_id = c2021.neighbourhood_id
    left join cpi_factors cpi on coalesce(c.census_year, n.census_year, 2021) = cpi.year
    -- LEFT JOIN to census_extended: 2016 rows flow through with NULL extended fields
    left join census_extended ce
        on n.neighbourhood_id = ce.neighbourhood_id
        and coalesce(c.census_year, n.census_year, 2021) = ce.census_year
    -- 2021 baseline for age bracket imputation on 2016 rows
    left join census_extended_2021_baseline ce2021 on n.neighbourhood_id = ce2021.neighbourhood_id
),

-- Union: rows from stg_toronto__census (132 at 2016, 158 at 2021) + 26 synthetic 2016 rows
foundation_all as (
    select
        f.neighbourhood_id,
        f.neighbourhood_name,
        f.geometry,
        f.land_area_sqkm,
        f.census_year,
        f.population,
        f.population_density,
        f.median_household_income,
        f.average_household_income,
        f.median_age,
        f.unemployment_rate,
        f.education_bachelors_pct,
        f.average_dwelling_value,
        f.is_imputed,
        f.pop_0_to_14,
        f.pop_15_to_24,
        f.pop_25_to_64,
        f.pop_65_plus,
        f.pct_owner_occupied,
        f.pct_renter_occupied,
        false                                                           as is_split_estimated
    from foundation f

    union all

    -- 26 new neighbourhood IDs missing real 2016 data: synthetic rows from 2021 baseline
    select
        d.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        n.land_area_sqkm,
        d.census_year,
        d.population,
        d.population_density,
        -- CPI-imputed income (same path as 124 original neighbourhoods for 2016)
        case
            when c2021.median_income_2021 is not null
            then round(c2021.median_income_2021 * cpi.adjustment_factor, 2)
            else null
        end                                                             as median_household_income,
        case
            when c2021.average_income_2021 is not null
            then round(c2021.average_income_2021 * cpi.adjustment_factor, 2)
            else null
        end                                                             as average_household_income,
        d.median_age,
        d.unemployment_rate,
        -- CPI-imputed education
        case
            when c2021.education_2021 is not null
            then round(c2021.education_2021 * cpi.adjustment_factor, 2)
            else null
        end                                                             as education_bachelors_pct,
        -- CPI-imputed dwelling value
        case
            when c2021.dwelling_value_2021 is not null
            then round(c2021.dwelling_value_2021 * cpi.adjustment_factor, 0)
            else null
        end                                                             as average_dwelling_value,
        true                                                            as is_imputed,
        -- Age brackets: scale 2021 counts by population ratio (same pattern as foundation CTE)
        round(ce2021.pop_0_to_14  * d.population::numeric / nullif(ce2021.population, 0))::integer as pop_0_to_14,
        round(ce2021.pop_15_to_24 * d.population::numeric / nullif(ce2021.population, 0))::integer as pop_15_to_24,
        round(ce2021.pop_25_to_64 * d.population::numeric / nullif(ce2021.population, 0))::integer as pop_25_to_64,
        round(ce2021.pop_65_plus  * d.population::numeric / nullif(ce2021.population, 0))::integer as pop_65_plus,
        d.pct_owner_occupied,
        d.pct_renter_occupied,
        true                                                            as is_split_estimated
    from distributed_2016 d
    join neighbourhoods n on n.neighbourhood_id = d.neighbourhood_id
    join census_2021_baseline c2021 on c2021.neighbourhood_id = d.neighbourhood_id
    left join census_extended_2021_baseline ce2021 on ce2021.neighbourhood_id = d.neighbourhood_id
    cross join (select adjustment_factor from cpi_factors where year = 2016) cpi
)

-- Recompute income_quintile over all 316 rows, partitioned by census_year
-- so 2016 and 2021 quintiles are each calibrated within their own year
select
    fa.*,
    case
        when fa.median_household_income is not null
        then ntile(5) over (
            partition by fa.census_year
            order by fa.median_household_income
        )
        else null
    end as income_quintile
from foundation_all fa
