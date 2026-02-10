-- Intermediate: Combined census demographics by neighbourhood
-- Joins neighbourhoods with census data for demographic analysis
-- Grain: One row per neighbourhood per census year

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

census as (
    select * from {{ ref('stg_toronto__census') }}
),

demographics as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,
        n.land_area_sqkm,

        -- Use census_year from census data, or fall back to dim_neighbourhood's year
        coalesce(c.census_year, n.census_year, 2021) as census_year,
        c.population,
        coalesce(
            c.population_density,
            case
                when n.land_area_sqkm > 0
                then round(c.population / n.land_area_sqkm, 2)
                else null
            end
        ) as population_density,
        c.median_household_income,
        c.average_household_income,
        c.median_age,
        c.unemployment_rate,
        c.pct_bachelors_or_higher as education_bachelors_pct,
        c.average_dwelling_value,

        -- Tenure mix
        c.pct_owner_occupied,
        c.pct_renter_occupied,

        -- Income quintile (city-wide comparison; NULL when no census data)
        case
            when c.median_household_income is not null
            then ntile(5) over (
                partition by c.census_year,
                    (case when c.median_household_income is not null then 1 else 0 end)
                order by c.median_household_income
            )
            else null
        end as income_quintile

    from neighbourhoods n
    left join census c on n.neighbourhood_id = c.neighbourhood_id
)

select * from demographics
