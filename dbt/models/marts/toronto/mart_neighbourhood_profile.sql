-- Mart: Neighbourhood community profile analytical table
-- Grain: One row per (neighbourhood_id, census_year, category, subcategory, level)
-- Final consumption table for dashboard with populated metrics only (removed 3 NULL-only columns)

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
        p.city_total,
        p.pct_of_city,
        p.rank_in_neighbourhood,
        p.level,
        p.indent_level,
        case when p.indent_level > 0 then true else false end as is_subtotal
    from profile p
)

select * from final
