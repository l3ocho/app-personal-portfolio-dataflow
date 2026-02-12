-- Intermediate: Housing indicators by neighbourhood
-- Combines demographics (with CPI imputation) with allocated CMHC rental data
-- Grain: One row per neighbourhood per year
--
-- Note: Uses int_neighbourhood__demographics which has CPI-based imputation
-- for income and dwelling values for years 2016-2020 (100% data coverage)

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

-- Use demographics table which has CPI-based imputation for all years (2016-2020)
demographics as (
    select * from {{ ref('int_neighbourhood__demographics') }}
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

        -- Demographics metrics (now with imputation for all years 2016-2025)
        d.pct_owner_occupied,
        d.pct_renter_occupied,
        d.average_dwelling_value,
        d.median_household_income,

        -- Allocated rental metrics (weighted average from CMHC zones)
        r.avg_rent_2bed,
        r.vacancy_rate,

        -- Affordability calculations
        case
            when d.median_household_income > 0 and r.avg_rent_2bed > 0
            then round((r.avg_rent_2bed * 12 / d.median_household_income) * 100, 2)
            else null
        end as rent_to_income_pct,

        -- Affordability threshold (30% of income)
        case
            when d.median_household_income > 0 and r.avg_rent_2bed > 0
            then r.avg_rent_2bed * 12 <= d.median_household_income * 0.30
            else null
        end as is_affordable

    from neighbourhoods n
    left join allocated_rentals r
        on n.neighbourhood_id = r.neighbourhood_id
    -- Join to most recent census data available for each rental year
    -- Demographics has imputed data for 2016-2020, actual data for 2021
    left join demographics d
        on n.neighbourhood_id = d.neighbourhood_id
        and d.census_year = (
            select max(d2.census_year)
            from {{ ref('int_neighbourhood__demographics') }} d2
            where d2.neighbourhood_id = n.neighbourhood_id
                and d2.census_year <= r.year
        )
)

select * from housing
