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

final as (
    select
        c.neighbourhood_id,
        c.population,
        c.year,

        -- Total crime
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
        end as safety_tier

    from crime c
    left join city_avg ca on c.year = ca.year
)

select * from final
