-- Mart: Neighbourhood community profile analytical table
-- Grain: One row per (neighbourhood_id, census_year, category, subcategory, level)
-- Final consumption table for dashboard with all computed metrics

with profile as (
    select * from {{ ref('int_toronto__neighbourhood_profile') }}
),

neighbourhoods as (
    select
        neighbourhood_id,
        neighbourhood_name
    from {{ ref('stg_toronto__neighbourhoods') }}
),

final as (
    select
        p.neighbourhood_id,
        n.neighbourhood_name,
        p.census_year,
        p.category,
        p.subcategory,
        p.count,
        p.pct_of_neighbourhood,
        p.city_total,
        p.pct_of_city,
        p.rank_in_neighbourhood,
        p.level,
        p.diversity_index
    from profile p
    left join neighbourhoods n using (neighbourhood_id)
)

select * from final
