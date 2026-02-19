-- Mart: Neighbourhood Demographics Analysis
-- Dashboard Tab: Demographics
-- Grain: One row per neighbourhood per census year

with demographics as (
    select * from {{ ref('int_neighbourhood__demographics') }}
),

-- City-wide averages for comparison
city_avg as (
    select
        census_year,
        avg(median_household_income) as city_avg_income,
        avg(median_age) as city_avg_age,
        avg(unemployment_rate) as city_avg_unemployment,
        avg(education_bachelors_pct) as city_avg_education,
        avg(population_density) as city_avg_density
    from demographics
    group by census_year
),

-- Profile summary: extract key indicators from community profile data
profile_summary as (
    select
        neighbourhood_id,
        census_year,
        -- pct_immigrant: from immigration_status category
        max(case when category = 'immigration_status' and subcategory = 'immigrants'
            then pct_of_neighbourhood end) as pct_immigrant,
        -- pct_visible_minority: from visible_minority category
        max(case when category = 'visible_minority'
                  and subcategory = 'total visible minority population'
            then pct_of_neighbourhood end) as pct_visible_minority,
        -- pct_neither_official_lang: from official_language category
        max(case when category = 'official_language'
                  and subcategory = 'neither english nor french'
            then pct_of_neighbourhood end) as pct_neither_official_lang,
        -- diversity_index: Shannon entropy from visible_minority
        max(case when category = 'visible_minority'
            then diversity_index end) as diversity_index
    from {{ ref('int_toronto__neighbourhood_profile') }}
    group by neighbourhood_id, census_year
),

final as (
    select
        d.neighbourhood_id,
        d.neighbourhood_name,
        d.geometry,
        d.census_year as year,

        -- Population
        d.population,
        d.land_area_sqkm,
        d.population_density,

        -- Income
        d.median_household_income,
        d.average_household_income,
        d.income_quintile,
        d.is_imputed,  -- Flag for CPI-adjusted estimated values (income, education, dwelling - 2016-2020)

        -- Income index (100 = city average)
        case
            when ca.city_avg_income > 0
            then round(d.median_household_income / ca.city_avg_income * 100, 1)
            else null
        end as income_index,

        -- Demographics
        d.median_age,
        d.unemployment_rate,
        d.education_bachelors_pct,

        -- Age index (100 = city average)
        case
            when ca.city_avg_age > 0
            then round(d.median_age / ca.city_avg_age * 100, 1)
            else null
        end as age_index,

        -- Housing tenure
        d.pct_owner_occupied,
        d.pct_renter_occupied,
        d.average_dwelling_value,

        -- Diversity index (using tenure mix as proxy - higher rental = more diverse typically)
        round(
            1 - (
                power(d.pct_owner_occupied / 100, 2) +
                power(d.pct_renter_occupied / 100, 2)
            ),
            3
        ) * 100 as tenure_diversity_index,

        -- City comparisons
        round(ca.city_avg_income::numeric, 2) as city_avg_income,
        round(ca.city_avg_age::numeric, 1) as city_avg_age,
        round(ca.city_avg_unemployment::numeric, 2) as city_avg_unemployment,

        -- Community profile summary (from neighbourhood profile data)
        round(ps.pct_immigrant::numeric, 2) as pct_immigrant,
        round(ps.pct_visible_minority::numeric, 2) as pct_visible_minority,
        round(ps.pct_neither_official_lang::numeric, 2) as pct_neither_official_lang,
        round(ps.diversity_index::numeric, 4) as diversity_index

    from demographics d
    left join city_avg ca on d.census_year = ca.census_year
    left join profile_summary ps on d.neighbourhood_id = ps.neighbourhood_id
        and d.census_year = ps.census_year
)

select * from final
