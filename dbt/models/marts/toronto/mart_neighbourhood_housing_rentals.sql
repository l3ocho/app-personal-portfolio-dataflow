-- Mart: Neighbourhood Housing Rentals (neighbourhood grain)
-- Dashboard Tab: Housing
-- Grain: One row per neighbourhood per bedroom_type per year
--
-- Disaggregates CMHC zone-level rental data to individual neighbourhoods
-- using area-weighted crosswalk (stg_cmhc__zone_crosswalk).

with crosswalk as (
    select * from {{ ref('stg_cmhc__zone_crosswalk') }}
),

rentals as (
    select * from {{ ref('int_rentals__annual') }}
),

neighbourhoods as (
    select
        neighbourhood_id,
        neighbourhood_name,
        geometry
    from {{ ref('stg_toronto__neighbourhoods') }}
),

-- Allocate zone-level rental metrics to neighbourhoods via area weights
-- Grain: one row per (neighbourhood_id, bedroom_type, year)
allocated as (
    select
        c.neighbourhood_id,
        r.year,
        r.bedroom_type,

        -- Weighted average rent
        sum(r.avg_rent * c.area_weight) / nullif(sum(c.area_weight), 0)           as avg_rent,

        -- Weighted vacancy rate
        sum(r.vacancy_rate * c.area_weight) / nullif(sum(c.area_weight), 0)        as vacancy_rate,

        -- Weighted turnover rate
        sum(r.turnover_rate * c.area_weight) / nullif(sum(c.area_weight), 0)       as turnover_rate,

        -- Weighted YoY rent change
        sum(r.year_over_year_rent_change * c.area_weight)
            / nullif(sum(c.area_weight), 0)                                         as year_over_year_rent_change,

        -- Proportional rental universe (sum of weighted estimates)
        sum(r.rental_universe * c.area_weight)                                     as rental_universe_estimate

    from crosswalk c
    inner join rentals r on c.cmhc_zone_code = r.zone_code
    group by c.neighbourhood_id, r.year, r.bedroom_type
),

-- Add year-over-year rent change at neighbourhood+bedroom_type level
with_yoy as (
    select
        a.*,
        lag(a.avg_rent, 1) over (
            partition by a.neighbourhood_id, a.bedroom_type
            order by a.year
        ) as prev_year_avg_rent
    from allocated a
),

final as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,

        w.year,
        w.bedroom_type,

        -- Rental metrics (area-weighted from CMHC zones)
        round(w.avg_rent::numeric, 2)                   as avg_rent,
        round(w.vacancy_rate::numeric, 4)               as vacancy_rate,
        round(w.turnover_rate::numeric, 4)              as turnover_rate,
        round(w.rental_universe_estimate::numeric, 0)   as rental_universe_estimate,
        round(w.year_over_year_rent_change::numeric, 4) as year_over_year_rent_change,

        -- Neighbourhood-level YoY rent change (computed from allocated rent)
        case
            when w.prev_year_avg_rent > 0
            then round(
                (w.avg_rent - w.prev_year_avg_rent) / w.prev_year_avg_rent * 100,
                2
            )
            else null
        end as rent_yoy_change_pct

    from with_yoy w
    inner join neighbourhoods n on w.neighbourhood_id = n.neighbourhood_id
)

select * from final
