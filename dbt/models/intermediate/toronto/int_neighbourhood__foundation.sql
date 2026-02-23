-- Intermediate: Neighbourhood foundation — scalar demographics + extended indicators
-- Grain: One row per neighbourhood per census year
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
-- All extended columns are nullable (Statistics Canada suppression).

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

        -- Tenure mix
        c.pct_owner_occupied,
        c.pct_renter_occupied,

        -- Income quintile (city-wide comparison; NULL when no census data)
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
        end as income_quintile,

        -- === Extended scalars from census_extended (all nullable) ===
        -- Population
        ce.pop_0_to_14,
        ce.pop_15_to_24,
        ce.pop_25_to_64,
        ce.pop_65_plus,

        -- Households
        ce.total_private_dwellings,
        ce.occupied_private_dwellings,
        ce.avg_household_size,
        ce.avg_household_income_after_tax,

        -- Housing tenure and costs
        ce.pct_suitable_housing,
        ce.avg_shelter_cost_owner,
        ce.avg_shelter_cost_renter,
        ce.pct_shelter_cost_30pct,

        -- Education
        ce.pct_no_certificate,
        ce.pct_high_school,
        ce.pct_college,
        ce.pct_university,
        ce.pct_postsecondary,

        -- Labour force
        ce.participation_rate,
        ce.employment_rate,
        ce.pct_employed_full_time,

        -- Income (extended)
        ce.median_after_tax_income,
        ce.median_employment_income,
        ce.lico_at_rate,
        ce.market_basket_measure_rate,

        -- Diversity / immigration
        ce.pct_immigrants,
        ce.pct_recent_immigrants,
        ce.pct_visible_minority,
        ce.pct_indigenous,

        -- Language
        ce.pct_english_only,
        ce.pct_french_only,
        ce.pct_neither_official_lang,
        ce.pct_bilingual,

        -- Mobility / migration
        ce.pct_non_movers,
        ce.pct_movers_within_city,
        ce.pct_movers_from_other_city,

        -- Commuting / transport
        ce.pct_car_commuters,
        ce.pct_transit_commuters,
        ce.pct_active_commuters,
        ce.pct_work_from_home,
        ce.median_commute_minutes,

        -- Additional indicators
        ce.pct_lone_parent_families,
        ce.avg_number_of_children,
        ce.pct_dwellings_in_need_of_repair,
        ce.pct_unaffordable_housing,
        ce.pct_overcrowded_housing,
        ce.pct_management_occupation,
        ce.pct_business_finance_admin,
        ce.pct_service_sector,
        ce.pct_trades_transport

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
    left join census_2021_baseline c2021 on n.neighbourhood_id = c2021.neighbourhood_id
    left join cpi_factors cpi on coalesce(c.census_year, n.census_year, 2021) = cpi.year
    left join census_extended ce
        on n.neighbourhood_id = ce.neighbourhood_id
        and coalesce(c.census_year, n.census_year, 2021) = ce.census_year
)

select * from foundation
