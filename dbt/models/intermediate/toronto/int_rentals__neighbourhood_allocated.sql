-- Intermediate: CMHC rentals allocated to neighbourhoods via area weights
-- Disaggregates zone-level rental data to neighbourhood level
-- Grain: One row per neighbourhood per year

with crosswalk as (
    select * from {{ ref('stg_cmhc__zone_crosswalk') }}
),

rentals as (
    select * from {{ ref('int_rentals__annual') }}
),

neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

-- Allocate rental metrics to neighbourhoods using area weights
allocated as (
    select
        c.neighbourhood_id,
        r.year,
        r.bedroom_type,

        -- Weighted average rent (using area weight)
        sum(r.avg_rent * c.area_weight) as weighted_avg_rent,
        sum(r.median_rent * c.area_weight) as weighted_median_rent,
        sum(c.area_weight) as total_weight,

        -- Weighted vacancy rate
        sum(r.vacancy_rate * c.area_weight) / nullif(sum(c.area_weight), 0) as vacancy_rate,

        -- Weighted rental universe
        sum(r.rental_universe * c.area_weight) as rental_units_estimate

    from crosswalk c
    inner join rentals r on c.cmhc_zone_code = r.zone_code
    group by c.neighbourhood_id, r.year, r.bedroom_type
),

-- Pivot to get 2-bedroom as primary metric
pivoted as (
    select
        neighbourhood_id,
        year,
        max(case when bedroom_type = '2bed' then weighted_avg_rent / nullif(total_weight, 0) end) as avg_rent_2bed,
        max(case when bedroom_type = '1bed' then weighted_avg_rent / nullif(total_weight, 0) end) as avg_rent_1bed,
        max(case when bedroom_type = 'bachelor' then weighted_avg_rent / nullif(total_weight, 0) end) as avg_rent_bachelor,
        max(case when bedroom_type = '3bed' then weighted_avg_rent / nullif(total_weight, 0) end) as avg_rent_3bed,
        avg(vacancy_rate) as vacancy_rate,
        sum(rental_units_estimate) as total_rental_units
    from allocated
    group by neighbourhood_id, year
),

final as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,

        p.year,
        round(p.avg_rent_bachelor::numeric, 2) as avg_rent_bachelor,
        round(p.avg_rent_1bed::numeric, 2) as avg_rent_1bed,
        round(p.avg_rent_2bed::numeric, 2) as avg_rent_2bed,
        round(p.avg_rent_3bed::numeric, 2) as avg_rent_3bed,
        round(p.vacancy_rate::numeric, 2) as vacancy_rate,
        round(p.total_rental_units::numeric, 0) as total_rental_units

    from neighbourhoods n
    inner join pivoted p on n.neighbourhood_id = p.neighbourhood_id
)

select * from final
