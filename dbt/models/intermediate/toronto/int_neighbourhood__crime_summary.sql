-- Intermediate: Aggregated crime by neighbourhood with YoY change
-- Pivots crime types and calculates year-over-year trends
-- Grain: One row per neighbourhood per year

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
),

crime as (
    select * from {{ ref('stg_toronto__crime') }}
),

-- Aggregate crime types
crime_by_year as (
    select
        neighbourhood_id,
        crime_year as year,
        sum(incident_count) as total_incidents,
        sum(case when crime_type = 'assault' then incident_count else 0 end) as assault_count,
        sum(case when crime_type = 'auto_theft' then incident_count else 0 end) as auto_theft_count,
        sum(case when crime_type = 'break_and_enter' then incident_count else 0 end) as break_enter_count,
        sum(case when crime_type = 'robbery' then incident_count else 0 end) as robbery_count,
        sum(case when crime_type = 'theft_over' then incident_count else 0 end) as theft_over_count,
        sum(case when crime_type = 'homicide' then incident_count else 0 end) as homicide_count,
        avg(rate_per_100k) as avg_rate_per_100k
    from crime
    group by neighbourhood_id, crime_year
),

-- Add year-over-year changes
with_yoy as (
    select
        c.*,
        lag(c.total_incidents, 1) over (
            partition by c.neighbourhood_id
            order by c.year
        ) as prev_year_incidents,
        round(
            (c.total_incidents - lag(c.total_incidents, 1) over (
                partition by c.neighbourhood_id
                order by c.year
            ))::numeric /
            nullif(lag(c.total_incidents, 1) over (
                partition by c.neighbourhood_id
                order by c.year
            ), 0) * 100,
            2
        ) as yoy_change_pct
    from crime_by_year c
),

crime_summary as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        c.population,

        w.year,
        w.total_incidents,
        w.assault_count,
        w.auto_theft_count,
        w.break_enter_count,
        w.robbery_count,
        w.theft_over_count,
        w.homicide_count,
        w.yoy_change_pct,

        -- Crime rate per 100K population (use source data avg, or calculate if population available)
        coalesce(
            w.avg_rate_per_100k,
            case
                when c.population > 0
                then round(w.total_incidents::numeric / c.population * 100000, 2)
                else null
            end
        ) as crime_rate_per_100k

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
    inner join with_yoy w on n.neighbourhood_id = w.neighbourhood_id
)

select * from crime_summary
