-- Mart: Neighbourhood Housing Analysis
-- Dashboard Tab: Housing
-- Grain: One row per neighbourhood per rental year
--
-- Surfaces actual housing metrics from int_neighbourhood__housing and rental data.
-- Removed 34 NULL-only columns (dwelling type/bedroom/construction pivots, shelter costs)
-- that were never populated from the source.

with housing as (
    select * from {{ ref('int_neighbourhood__housing') }}
),

rentals as (
    select * from {{ ref('int_rentals__neighbourhood_allocated') }}
),

-- Add year-over-year rent changes and additional rental unit breakdown
with_yoy as (
    select
        h.*,
        r.avg_rent_bachelor,
        r.avg_rent_1bed,
        r.avg_rent_3bed,
        r.total_rental_units,

        -- Previous year rent for YoY calculation
        lag(h.avg_rent_2bed, 1) over (
            partition by h.neighbourhood_id
            order by h.year
        ) as prev_year_rent_2bed

    from housing h
    left join rentals r
        on h.neighbourhood_id = r.neighbourhood_id
        and h.year = r.year
),

final as (
    select
        neighbourhood_id,
        year,
        census_year,

        -- Tenure mix
        pct_owner_occupied,
        pct_renter_occupied,

        -- Housing values and income
        average_dwelling_value,
        median_household_income,
        income_quintile,

        -- Rental metrics
        avg_rent_bachelor,
        avg_rent_1bed,
        avg_rent_2bed,
        avg_rent_3bed,
        vacancy_rate,
        total_rental_units,

        -- Affordability
        rent_to_income_pct,
        is_affordable,

        -- Affordability index (100 = city average for the year)
        round(
            rent_to_income_pct / nullif(
                avg(rent_to_income_pct) over (partition by year),
                0
            ) * 100,
            1
        ) as affordability_index,

        -- Year-over-year rent change
        case
            when prev_year_rent_2bed > 0
            then round(
                (avg_rent_2bed - prev_year_rent_2bed) / prev_year_rent_2bed * 100,
                2
            )
            else null
        end as rent_yoy_change_pct,

        -- Composite: affordability pressure score (0-100)
        -- High rent-to-income pct + high renter pct + low vacancy → higher score
        round(
            least(100, greatest(0,
                coalesce(rent_to_income_pct, 0) * 0.5
                + coalesce(pct_renter_occupied, 0) * 0.3
                + greatest(0, 10 - coalesce(vacancy_rate * 100, 10)) * 2
            )),
            1
        ) as affordability_pressure_score

    from with_yoy
)

select * from final
