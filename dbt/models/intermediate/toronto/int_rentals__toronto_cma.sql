-- Intermediate: Toronto CMA rental metrics by year
-- Aggregates rental data to city-wide averages by year
-- Source: StatCan CMHC data at CMA level
-- Grain: One row per year

with rentals as (
    select * from {{ ref('stg_cmhc__rentals') }}
),

-- Pivot bedroom types to columns
yearly_rentals as (
    select
        year,
        max(case when bedroom_type = 'bachelor' then avg_rent end) as avg_rent_bachelor,
        max(case when bedroom_type = '1bed' then avg_rent end) as avg_rent_1bed,
        max(case when bedroom_type = '2bed' then avg_rent end) as avg_rent_2bed,
        max(case when bedroom_type = '3bed' then avg_rent end) as avg_rent_3bed,
        -- Use 2-bedroom as standard reference
        max(case when bedroom_type = '2bed' then avg_rent end) as avg_rent_standard,
        max(vacancy_rate) as vacancy_rate
    from rentals
    group by year
)

select * from yearly_rentals
