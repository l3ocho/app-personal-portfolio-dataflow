-- Intermediate: Toronto CMA census statistics by year
-- Provides city-wide averages for metrics not available at neighbourhood level
-- Used when neighbourhood-level data is unavailable (e.g., median household income)
-- Grain: One row per year

with years as (
    select * from {{ ref('int_year_spine') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
),

-- Census data is only available for 2016 and 2021
-- Map each analysis year to the appropriate census year
year_to_census as (
    select
        y.year,
        case
            when y.year <= 2018 then 2016
            else 2021
        end as census_year
    from years y
),

-- Toronto CMA median household income from Statistics Canada
-- Source: Census Profile Table 98-316-X2021001
-- 2016: $65,829 (from Census Profile)
-- 2021: $84,000 (from Census Profile)
cma_income as (
    select 2016 as census_year, 65829 as median_household_income union all
    select 2021 as census_year, 84000 as median_household_income
),

-- City-wide aggregates from loaded neighbourhood data
city_aggregates as (
    select
        census_year,
        sum(population) as total_population,
        avg(population_density) as avg_population_density,
        avg(unemployment_rate) as avg_unemployment_rate
    from census
    where population is not null
    group by census_year
),

final as (
    select
        y.year,
        y.census_year,
        ci.median_household_income,
        ca.total_population,
        ca.avg_population_density,
        ca.avg_unemployment_rate
    from year_to_census y
    left join cma_income ci on y.census_year = ci.census_year
    left join city_aggregates ca on y.census_year = ca.census_year
)

select * from final
