-- Mart: Neighbourhood Overview with Composite Livability Score
-- Dashboard Tab: Overview
-- Grain: One row per neighbourhood per year
-- Time spine: Years 2014-2025 (driven by crime/rental data availability)

with years as (
    select * from {{ ref('int_year_spine') }}
),

neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

-- Create base: all neighbourhoods × all years
neighbourhood_years as (
    select
        n.neighbourhood_id,
        y.year
    from neighbourhoods n
    cross join years y
),

-- Census data (available for 2016, 2021)
-- For each year, use the most recent census data available
census as (
    select * from {{ ref('stg_toronto__census') }}
),

census_mapped as (
    select
        ny.neighbourhood_id,
        ny.year,
        c.population,
        c.unemployment_rate,
        c.pct_bachelors_or_higher as education_bachelors_pct
    from neighbourhood_years ny
    left join census c on ny.neighbourhood_id = c.neighbourhood_id
        -- Use census year <= analysis year, prefer most recent
        and c.census_year = (
            select max(c2.census_year)
            from {{ ref('stg_toronto__census') }} c2
            where c2.neighbourhood_id = ny.neighbourhood_id
            and c2.census_year <= ny.year
        )
),

-- CMA-level census data (for income - not available at neighbourhood level)
cma_census as (
    select * from {{ ref('int_census__toronto_cma') }}
),

-- Crime data (2014-2024)
crime as (
    select * from {{ ref('int_neighbourhood__crime_summary') }}
),

-- Rentals (2019-2025) - CMA level applied to all neighbourhoods
rentals as (
    select * from {{ ref('int_rentals__toronto_cma') }}
),

-- Housing affordability (neighbourhood-level)
housing as (
    select
        neighbourhood_id,
        year,
        affordability_index
    from {{ ref('mart_neighbourhood_housing') }}
),

-- Amenities (use latest year since infrastructure changes slowly)
amenities as (
    select
        neighbourhood_id,
        amenity_index as amenity_score,
        total_amenities_per_1000
    from {{ ref('mart_neighbourhood_amenities') }}
    where year = (select max(year) from {{ ref('mart_neighbourhood_amenities') }})
),

-- Compute scores
scored as (
    select
        ny.neighbourhood_id,
        ny.year,
        cm.population,
        -- Use neighbourhood-level income where available, CMA-level as fallback
        coalesce(c.median_household_income, cma.median_household_income) as median_household_income,

        -- Safety score: inverse of crime rate (higher = safer)
        case
            when cr.crime_rate_per_100k is not null
            then 100 - percent_rank() over (
                partition by ny.year
                order by cr.crime_rate_per_100k
            ) * 100
            else null
        end as safety_score,

        -- Affordability score: use neighbourhood-level affordability_index from housing mart
        h.affordability_index as affordability_score,

        -- Amenity score: use neighbourhood-level amenity_score from amenities mart
        a.amenity_score,

        -- Raw metrics
        cr.crime_rate_per_100k,
        case
            when cma.median_household_income > 0 and r.avg_rent_standard > 0
            then round((r.avg_rent_standard * 12 / cma.median_household_income) * 100, 2)
            else null
        end as rent_to_income_pct,
        r.avg_rent_standard as avg_rent_2bed,
        r.vacancy_rate,
        a.total_amenities_per_1000

    from neighbourhood_years ny
    left join census_mapped cm
        on ny.neighbourhood_id = cm.neighbourhood_id
        and ny.year = cm.year
    left join census c
        on ny.neighbourhood_id = c.neighbourhood_id
        and c.census_year = (
            select max(c2.census_year)
            from {{ ref('stg_toronto__census') }} c2
            where c2.neighbourhood_id = ny.neighbourhood_id
            and c2.census_year <= ny.year
        )
    left join cma_census cma
        on ny.year = cma.year
    left join crime cr
        on ny.neighbourhood_id = cr.neighbourhood_id
        and ny.year = cr.year
    left join rentals r
        on ny.year = r.year
    left join housing h
        on ny.neighbourhood_id = h.neighbourhood_id
        and ny.year = h.year
    left join amenities a
        on ny.neighbourhood_id = a.neighbourhood_id
),

final as (
    select
        neighbourhood_id,
        year,
        population,
        median_household_income,

        -- Component scores (0-100 scale, except amenity_score which is per-1000 basis)
        round(safety_score::numeric, 1) as safety_score,
        round(affordability_score::numeric, 1) as affordability_score,
        round(amenity_score::numeric, 1) as amenity_score,

        -- Composite livability score: safety (30%), affordability (40%), amenities (30%)
        -- Note: Amenity score is normalized to 0-100 scale for weighting
        round(
            (coalesce(safety_score, 50) * 0.30 +
             coalesce(affordability_score, 50) * 0.40 +
             coalesce(amenity_score / 2.5, 50) * 0.30)::numeric,
            1
        ) as livability_score,

        -- Raw metrics
        crime_rate_per_100k,
        rent_to_income_pct,
        avg_rent_2bed,
        vacancy_rate,
        total_amenities_per_1000

    from scored
)

select * from final
