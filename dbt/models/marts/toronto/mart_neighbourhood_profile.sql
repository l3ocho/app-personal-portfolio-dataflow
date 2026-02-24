-- Mart: Neighbourhood community profile analytical table
-- Grain: One row per (neighbourhood_id, census_year, category, subcategory, level)
-- Final consumption table for dashboard with all computed metrics

with profile as (
    select * from {{ ref('int_toronto__neighbourhood_profile') }}
),

final as (
    select
        p.neighbourhood_id,
        p.census_year,
        p.category,
        p.subcategory,
        p.count,
        p.pct_of_neighbourhood,
        p.city_total,
        p.pct_of_city,
        p.rank_in_neighbourhood,
        p.level,
        p.indent_level,
        p.category_total,
        case when p.indent_level > 0 then true else false end as is_subtotal,
        p.diversity_index
    from profile p
)

select * from final
