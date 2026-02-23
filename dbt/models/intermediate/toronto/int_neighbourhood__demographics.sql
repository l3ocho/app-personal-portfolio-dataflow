-- DEPRECATED (Sprint 13) — Use int_neighbourhood__foundation instead.
-- This model is kept for backward compatibility until webapp confirms switchover.
-- Do NOT add new columns here. Do NOT reference from new models.
--
-- Intermediate: Combined census demographics by neighbourhood
-- Joins neighbourhoods with census data for demographic analysis
-- Grain: One row per neighbourhood per census year
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
-- The 'is_income_imputed' flag marks imputed values for transparency.

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
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

demographics as (
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
        -- TRUE if any of: income, education, or dwelling value is imputed
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

        -- Tenure mix
        c.pct_owner_occupied,
        c.pct_renter_occupied,

        -- Income quintile (city-wide comparison; NULL when no census data)
        -- Note: Quintiles are calculated AFTER imputation, using adjusted values
        case
            when c.median_household_income is not null
                or (c.census_year < 2021 and c2021.median_income_2021 is not null)
            then ntile(5) over (
                partition by coalesce(c.census_year, n.census_year, 2021)
                order by
                    case
                        when c.median_household_income is not null then c.median_household_income
                        when c.census_year < 2021 and c2021.median_income_2021 is not null
                            then c2021.median_income_2021 * cpi.adjustment_factor
                        else null
                    end
            )
            else null
        end as income_quintile

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
    left join census_2021_baseline c2021 on n.neighbourhood_id = c2021.neighbourhood_id
    left join cpi_factors cpi on coalesce(c.census_year, n.census_year, 2021) = cpi.year
)

select * from demographics
