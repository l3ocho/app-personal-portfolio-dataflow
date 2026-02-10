-- Mart: Neighbourhood Housing Analysis
-- Dashboard Tab: Housing
-- Grain: One row per neighbourhood per year

with housing as (
    select * from {{ ref('int_neighbourhood__housing') }}
),

rentals as (
    select * from {{ ref('int_rentals__neighbourhood_allocated') }}
),

demographics as (
    select * from {{ ref('int_neighbourhood__demographics') }}
),

-- Add year-over-year rent changes
with_yoy as (
    select
        h.*,
        r.avg_rent_bachelor,
        r.avg_rent_1bed,
        r.avg_rent_3bed,
        r.total_rental_units,
        d.income_quintile,

        -- Previous year rent for YoY calculation
        lag(h.avg_rent_2bed, 1) over (
            partition by h.neighbourhood_id
            order by h.year
        ) as prev_year_rent_2bed

    from housing h
    left join rentals r
        on h.neighbourhood_id = r.neighbourhood_id
        and h.year = r.year
    left join (
        select *
        from demographics
        where census_year = (select max(census_year) from demographics)
    ) d
        on h.neighbourhood_id = d.neighbourhood_id
),

final as (
    select
        neighbourhood_id,
        neighbourhood_name,
        geometry,
        year,

        -- Tenure mix
        pct_owner_occupied,
        pct_renter_occupied,

        -- Housing values
        average_dwelling_value,
        median_household_income,

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

        -- Affordability index (100 = city average)
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

        income_quintile

    from with_yoy
)

select * from final
