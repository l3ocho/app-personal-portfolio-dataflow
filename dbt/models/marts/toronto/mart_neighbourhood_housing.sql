-- Mart: Neighbourhood Housing Analysis
-- Dashboard Tab: Housing
-- Grain: One row per neighbourhood per rental year
--
-- Surfaces all housing metrics from int_neighbourhood__housing, including
-- profile pivots for dwelling type, bedroom counts, and construction period.

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

        -- Shelter costs (census-based)
        avg_shelter_cost_owner,
        avg_shelter_cost_renter,
        pct_shelter_cost_30pct,
        pct_suitable_housing,

        -- Dwelling stock
        total_private_dwellings,
        occupied_private_dwellings,
        avg_household_size,

        -- Housing quality
        pct_dwellings_in_need_of_repair,
        pct_unaffordable_housing,
        pct_overcrowded_housing,

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

        -- Dwelling type pivots (counts)
        dwelling_single_detached,
        dwelling_semi_detached,
        dwelling_row_house,
        dwelling_duplex,
        dwelling_apt_low_rise,
        dwelling_apt_high_rise,
        dwelling_other_single_attached,
        dwelling_movable,

        -- Derived: dwelling mix percentages
        round(
            (coalesce(dwelling_duplex, 0) + coalesce(dwelling_apt_low_rise, 0) + coalesce(dwelling_apt_high_rise, 0))::numeric
            / nullif(total_private_dwellings, 0) * 100,
            2
        ) as dwelling_apartment_pct,

        round(
            (coalesce(dwelling_single_detached, 0) + coalesce(dwelling_semi_detached, 0) + coalesce(dwelling_row_house, 0))::numeric
            / nullif(total_private_dwellings, 0) * 100,
            2
        ) as dwelling_ground_oriented_pct,

        -- Bedroom pivots (counts)
        bedrooms_none,
        bedrooms_1,
        bedrooms_2,
        bedrooms_3,
        bedrooms_4_plus,

        -- Construction period pivots (counts)
        construction_pre_1960,
        construction_1961_1980,
        construction_1981_1990,
        construction_1991_2000,
        construction_2001_2005,
        construction_2006_2010,
        construction_2011_2015,
        construction_2016_2021,

        -- Derived: share of post-2000 construction
        round(
            (
                coalesce(construction_2001_2005, 0) + coalesce(construction_2006_2010, 0)
                + coalesce(construction_2011_2015, 0) + coalesce(construction_2016_2021, 0)
            )::numeric
            / nullif(
                coalesce(construction_pre_1960, 0) + coalesce(construction_1961_1980, 0)
                + coalesce(construction_1981_1990, 0) + coalesce(construction_1991_2000, 0)
                + coalesce(construction_2001_2005, 0) + coalesce(construction_2006_2010, 0)
                + coalesce(construction_2011_2015, 0) + coalesce(construction_2016_2021, 0),
                0
            ) * 100,
            2
        ) as construction_post_2000_pct,

        -- Composite: weighted average shelter cost (owner/renter split)
        case
            when (pct_owner_occupied + pct_renter_occupied) > 0
            then round(
                (
                    coalesce(avg_shelter_cost_owner, 0) * coalesce(pct_owner_occupied, 0)
                    + coalesce(avg_shelter_cost_renter, 0) * coalesce(pct_renter_occupied, 0)
                ) / nullif(pct_owner_occupied + pct_renter_occupied, 0),
                0
            )
            else null
        end as avg_shelter_cost,

        -- Composite: affordability pressure score (0-100)
        -- High shelter_unaffordable pct + high renter pct + low vacancy → higher score
        round(
            least(100, greatest(0,
                coalesce(pct_shelter_cost_30pct, 0) * 0.5
                + coalesce(pct_renter_occupied, 0) * 0.3
                + greatest(0, 10 - coalesce(vacancy_rate * 100, 10)) * 2
            )),
            1
        ) as affordability_pressure_score

    from with_yoy
)

select * from final
