-- Mart: Neighbourhood Safety Analysis
-- Dashboard Tab: Safety
-- Grain: One row per neighbourhood per year

with crime as (
    select * from {{ ref('int_neighbourhood__crime_summary') }}
),

-- City-wide averages for comparison
city_avg as (
    select
        year,
        avg(crime_rate_per_100k) as city_avg_crime_rate,
        avg(assault_count) as city_avg_assault,
        avg(auto_theft_count) as city_avg_auto_theft,
        avg(break_enter_count) as city_avg_break_enter
    from crime
    group by year
),

-- Housing affordability index (neighbourhood × year)
housing as (
    select
        neighbourhood_id,
        year,
        housing_affordability_index
    from {{ ref('mart_neighbourhood_housing') }}
),

-- Amenity index — latest census year used as static value (infrastructure changes slowly)
people as (
    select
        neighbourhood_id,
        amenities_index
    from {{ ref('mart_neighbourhood_people') }}
    where census_year = (select max(census_year) from {{ ref('mart_neighbourhood_people') }})
),

-- Compute safety_score in a separate CTE — window functions cannot be nested in livability_score
scored as (
    select
        c.neighbourhood_id,
        c.population,
        c.year,
        c.total_incidents,
        c.crime_rate_per_100k,
        c.yoy_change_pct as crime_yoy_change_pct,

        -- Crime breakdown
        c.assault_count,
        c.auto_theft_count,
        c.break_enter_count,
        c.robbery_count,
        c.theft_over_count,
        c.homicide_count,

        -- Per 100K rates by type
        case when c.population > 0
            then round(c.assault_count::numeric / c.population * 100000, 2)
            else null
        end as assault_rate_per_100k,

        case when c.population > 0
            then round(c.auto_theft_count::numeric / c.population * 100000, 2)
            else null
        end as auto_theft_rate_per_100k,

        case when c.population > 0
            then round(c.break_enter_count::numeric / c.population * 100000, 2)
            else null
        end as break_enter_rate_per_100k,

        -- Comparison to city average
        round(ca.city_avg_crime_rate::numeric, 2) as city_avg_crime_rate,

        -- Crime index (100 = city average)
        case
            when ca.city_avg_crime_rate > 0
            then round(c.crime_rate_per_100k / ca.city_avg_crime_rate * 100, 1)
            else null
        end as crime_index,

        -- Safety tier based on crime rate percentile (NULL when no rate data)
        case
            when c.crime_rate_per_100k is not null
            then ntile(5) over (
                partition by c.year,
                    (case when c.crime_rate_per_100k is not null then 1 else 0 end)
                order by c.crime_rate_per_100k desc
            )
            else null
        end as safety_tier,

        -- Safety score: percentile inversion (higher = safer, 0-100)
        case
            when c.crime_rate_per_100k is not null
            then round(
                ((1 - percent_rank() over (
                    partition by c.year
                    order by c.crime_rate_per_100k
                )) * 100)::numeric,
                1
            )
            else null
        end as safety_score,

        -- Livability components (carried through for composite below)
        h.housing_affordability_index,
        p.amenities_index

    from crime c
    left join city_avg ca on c.year = ca.year
    left join housing h
        on c.neighbourhood_id = h.neighbourhood_id
        and c.year = h.year
    left join people p
        on c.neighbourhood_id = p.neighbourhood_id
),

final as (
    select
        neighbourhood_id,
        population,
        year,

        -- Total crime
        total_incidents,
        crime_rate_per_100k,
        crime_yoy_change_pct,

        -- Crime breakdown
        assault_count,
        auto_theft_count,
        break_enter_count,
        robbery_count,
        theft_over_count,
        homicide_count,

        -- Per 100K rates by type
        assault_rate_per_100k,
        auto_theft_rate_per_100k,
        break_enter_rate_per_100k,

        -- Comparison to city average
        city_avg_crime_rate,

        -- Crime index (100 = city average)
        crime_index,

        -- Safety tier based on crime rate percentile (NULL when no rate data)
        safety_tier,

        -- Safety score: percentile inversion (0-100, higher = safer)
        safety_score,

        -- Livability score: composite (safety 30% + affordability 40% + amenity 30%)
        -- NULL when any component is missing — no coalesce fallback
        case
            when safety_score is not null
                and housing_affordability_index is not null
                and amenities_index is not null
            then round(
                (
                    safety_score * 0.30
                    + housing_affordability_index * 0.40
                    + (amenities_index / 2.5) * 0.30
                )::numeric,
                1
            )
            else null
        end as livability_score

    from scored
)

select * from final
