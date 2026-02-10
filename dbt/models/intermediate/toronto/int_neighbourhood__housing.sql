-- Intermediate: Housing indicators by neighbourhood
-- Combines census housing data with allocated CMHC rental data
-- Grain: One row per neighbourhood per year

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
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

        -- Census housing metrics (forward-filled from 2021)
        c.pct_owner_occupied,
        c.pct_renter_occupied,
        c.average_dwelling_value,
        c.median_household_income,

        -- Allocated rental metrics (weighted average from CMHC zones)
        r.avg_rent_2bed,
        r.vacancy_rate,

        -- Affordability calculations
        case
            when c.median_household_income > 0 and r.avg_rent_2bed > 0
            then round((r.avg_rent_2bed * 12 / c.median_household_income) * 100, 2)
            else null
        end as rent_to_income_pct,

        -- Affordability threshold (30% of income)
        case
            when c.median_household_income > 0 and r.avg_rent_2bed > 0
            then r.avg_rent_2bed * 12 <= c.median_household_income * 0.30
            else null
        end as is_affordable

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
    left join allocated_rentals r
        on n.neighbourhood_id = r.neighbourhood_id
)

select * from housing
