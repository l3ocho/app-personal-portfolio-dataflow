-- Intermediate: Housing indicators by neighbourhood
-- Combines foundation (with CPI imputation) with allocated CMHC rental data
--   and profile pivots for dwelling type, bedrooms, and construction period.
-- Grain: One row per neighbourhood per rental year
--
-- Note: Uses int_neighbourhood__foundation which has CPI-based imputation
-- for income and dwelling values for years 2016-2020 (100% data coverage)

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

foundation as (
    select * from {{ ref('int_neighbourhood__foundation') }}
),

allocated_rentals as (
    select * from {{ ref('int_rentals__neighbourhood_allocated') }}
),

housing as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,

        r.year,
        f.census_year,

        -- Foundation metrics (CPI-imputed for 2016-2020, actual for 2021)
        f.income_quintile,
        f.pct_owner_occupied,
        f.pct_renter_occupied,
        f.average_dwelling_value,
        f.median_household_income,

        -- Allocated rental metrics (weighted average from CMHC zones)
        r.avg_rent_2bed,
        r.vacancy_rate,

        -- Affordability calculations
        case
            when f.median_household_income > 0 and r.avg_rent_2bed > 0
            then round((r.avg_rent_2bed * 12 / f.median_household_income) * 100, 2)
            else null
        end as rent_to_income_pct,

        -- Affordability threshold (30% of income)
        case
            when f.median_household_income > 0 and r.avg_rent_2bed > 0
            then r.avg_rent_2bed * 12 <= f.median_household_income * 0.30
            else null
        end as is_affordable

    from neighbourhoods n
    left join allocated_rentals r
        on n.neighbourhood_id = r.neighbourhood_id
    -- Join to most recent census data available for each rental year
    -- Foundation has imputed data for 2016-2020, actual data for 2021
    left join foundation f
        on n.neighbourhood_id = f.neighbourhood_id
        and f.census_year = (
            select max(f2.census_year)
            from {{ ref('int_neighbourhood__foundation') }} f2
            where f2.neighbourhood_id = n.neighbourhood_id
                and f2.census_year <= r.year
        )
)

select * from housing
