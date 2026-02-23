-- Intermediate: Neighbourhood community profile with computed metrics
-- Grain: One row per (neighbourhood_id, census_year, category, subcategory, level)
-- Adds:
--   - Percentage within neighbourhood's category total
--   - Percentage of city total
--   - Rank within neighbourhood and category
--   - City-wide sum for comparison
--   - Shannon diversity index (visible_minority only)

with profiles as (
    select * from {{ ref('stg_toronto__profiles') }}
),

-- Compute category-level totals per neighbourhood (for pct_of_neighbourhood)
-- Uses category_total from section header rows (indent_level=0) as the true denominator.
-- Previous implementation used SUM(count) which inflated totals 1.5-2x by including subtotals.
neighbourhood_category_totals as (
    select
        neighbourhood_id,
        census_year,
        category,
        max(category_total) as neighbourhood_category_total
    from profiles
    where category_total is not null
    group by neighbourhood_id, census_year, category
),

-- Compute city-wide totals per subcategory (for pct_of_city and city_total)
city_subcategory_totals as (
    select
        census_year,
        category,
        subcategory,
        level,
        sum(count) as city_total
    from profiles
    where count is not null
    group by census_year, category, subcategory, level
),

-- Compute Shannon entropy for visible_minority per neighbourhood
-- H = -SUM( (count/total) * ln(count/total) ) where count > 0
-- Returns NULL if all values are suppressed or total is zero
visible_minority_entropy as (
    select
        p.neighbourhood_id,
        p.census_year,
        -1.0 * sum(
            case
                when p.count > 0 and nct.neighbourhood_category_total > 0
                then (p.count::numeric / nct.neighbourhood_category_total)
                     * ln(p.count::numeric / nct.neighbourhood_category_total)
                else 0
            end
        ) as diversity_index
    from profiles p
    join neighbourhood_category_totals nct
        on p.neighbourhood_id = nct.neighbourhood_id
        and p.census_year = nct.census_year
        and p.category = nct.category
    where p.category = 'visible_minority'
      and p.count is not null
    group by p.neighbourhood_id, p.census_year
),

-- Final: join all metrics together
enriched as (
    select
        p.neighbourhood_id,
        p.census_year,
        p.category,
        p.subcategory,
        p.level,
        p.indent_level,
        p.count,

        -- Percentage within this neighbourhood + category
        case
            when nct.neighbourhood_category_total > 0 and p.count is not null
            then round(
                (p.count::numeric / nct.neighbourhood_category_total) * 100,
                2
            )
            else null
        end as pct_of_neighbourhood,

        -- City-wide total for this subcategory
        cst.city_total,

        -- Percentage of city total
        case
            when cst.city_total > 0 and p.count is not null
            then round(
                (p.count::numeric / cst.city_total) * 100,
                2
            )
            else null
        end as pct_of_city,

        -- Rank within neighbourhood + category (1 = most prevalent)
        rank() over (
            partition by p.neighbourhood_id, p.census_year, p.category
            order by p.count desc nulls last
        ) as rank_in_neighbourhood,

        -- Shannon diversity index (only populated for visible_minority rows)
        case
            when p.category = 'visible_minority'
            then vme.diversity_index
            else null
        end as diversity_index

    from profiles p
    left join neighbourhood_category_totals nct
        on p.neighbourhood_id = nct.neighbourhood_id
        and p.census_year = nct.census_year
        and p.category = nct.category
    left join city_subcategory_totals cst
        on p.census_year = cst.census_year
        and p.category = cst.category
        and p.subcategory = cst.subcategory
        and coalesce(p.level, '') = coalesce(cst.level, '')
    left join visible_minority_entropy vme
        on p.neighbourhood_id = vme.neighbourhood_id
        and p.census_year = vme.census_year
        and p.category = 'visible_minority'
)

select * from enriched
