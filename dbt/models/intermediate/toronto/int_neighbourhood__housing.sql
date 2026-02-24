-- Intermediate: Housing indicators by neighbourhood
-- Combines foundation (with CPI imputation) with allocated CMHC rental data
--   and profile pivots for dwelling type, bedrooms, and construction period.
-- Grain: One row per neighbourhood per rental year
--
-- Note: Uses int_neighbourhood__foundation which has CPI-based imputation
-- for income and dwelling values for years 2016-2020 (100% data coverage)

with neighbourhoods as (
    select * from {{ ref('stg_toronto__neighbourhoods') }}
),

foundation as (
    select * from {{ ref('int_neighbourhood__foundation') }}
),

allocated_rentals as (
    select * from {{ ref('int_rentals__neighbourhood_allocated') }}
),

-- Profile pivots: dwelling type, bedrooms, construction period
-- Grain: one row per (neighbourhood_id, census_year)
profile_housing as (
    select
        neighbourhood_id,
        census_year,

        -- Dwelling type
        max(case when category = 'dwelling_type' and subcategory = 'single-detached house'                                    then count end) as dwelling_single_detached,
        max(case when category = 'dwelling_type' and subcategory = 'semi-detached house'                                      then count end) as dwelling_semi_detached,
        max(case when category = 'dwelling_type' and subcategory = 'row house'                                                then count end) as dwelling_row_house,
        max(case when category = 'dwelling_type' and subcategory = 'apartment or flat in a duplex'                            then count end) as dwelling_duplex,
        max(case when category = 'dwelling_type' and subcategory = 'apartment in a building that has fewer than five storeys' then count end) as dwelling_apt_low_rise,
        max(case when category = 'dwelling_type' and subcategory = 'apartment in a building that has five or more storeys'    then count end) as dwelling_apt_high_rise,
        max(case when category = 'dwelling_type' and subcategory = 'other single-attached house'                              then count end) as dwelling_other_single_attached,
        max(case when category = 'dwelling_type' and subcategory = 'movable dwelling'                                         then count end) as dwelling_movable,

        -- Bedrooms
        max(case when category = 'bedrooms' and subcategory = 'no bedrooms'       then count end) as bedrooms_none,
        max(case when category = 'bedrooms' and subcategory = '1 bedroom'         then count end) as bedrooms_1,
        max(case when category = 'bedrooms' and subcategory = '2 bedrooms'        then count end) as bedrooms_2,
        max(case when category = 'bedrooms' and subcategory = '3 bedrooms'        then count end) as bedrooms_3,
        max(case when category = 'bedrooms' and subcategory = '4 or more bedrooms' then count end) as bedrooms_4_plus,

        -- Construction period
        max(case when category = 'construction_period' and subcategory = '1960 or before'  then count end) as construction_pre_1960,
        max(case when category = 'construction_period' and subcategory = '1961 to 1980'    then count end) as construction_1961_1980,
        max(case when category = 'construction_period' and subcategory = '1981 to 1990'    then count end) as construction_1981_1990,
        max(case when category = 'construction_period' and subcategory = '1991 to 2000'    then count end) as construction_1991_2000,
        max(case when category = 'construction_period' and subcategory = '2001 to 2005'    then count end) as construction_2001_2005,
        max(case when category = 'construction_period' and subcategory = '2006 to 2010'    then count end) as construction_2006_2010,
        max(case when category = 'construction_period' and subcategory = '2011 to 2015'    then count end) as construction_2011_2015,
        max(case when category = 'construction_period' and subcategory = '2016 to 2021'    then count end) as construction_2016_2021

    from {{ ref('stg_toronto__profiles') }}
    where category in ('dwelling_type', 'bedrooms', 'construction_period')
    group by neighbourhood_id, census_year
),

housing as (
    select
        n.neighbourhood_id,
        n.neighbourhood_name,
        n.geometry,

        r.year,
        f.census_year,

        -- Foundation metrics (CPI-imputed for 2016-2020, actual for 2021)
        f.income_quintile,
        f.pct_owner_occupied,
        f.pct_renter_occupied,
        f.average_dwelling_value,
        f.median_household_income,

        -- Extended: shelter costs and housing quality
        f.avg_shelter_cost_owner,
        f.avg_shelter_cost_renter,
        f.pct_shelter_cost_30pct,
        f.pct_suitable_housing,
        f.total_private_dwellings,
        f.occupied_private_dwellings,
        f.avg_household_size,
        f.pct_dwellings_in_need_of_repair,
        f.pct_unaffordable_housing,
        f.pct_overcrowded_housing,

        -- Allocated rental metrics (weighted average from CMHC zones)
        r.avg_rent_2bed,
        r.vacancy_rate,

        -- Affordability calculations
        case
            when f.median_household_income > 0 and r.avg_rent_2bed > 0
            then round((r.avg_rent_2bed * 12 / f.median_household_income) * 100, 2)
            else null
        end as rent_to_income_pct,

        -- Affordability threshold (30% of income)
        case
            when f.median_household_income > 0 and r.avg_rent_2bed > 0
            then r.avg_rent_2bed * 12 <= f.median_household_income * 0.30
            else null
        end as is_affordable,

        -- Dwelling type pivots
        ph.dwelling_single_detached,
        ph.dwelling_semi_detached,
        ph.dwelling_row_house,
        ph.dwelling_duplex,
        ph.dwelling_apt_low_rise,
        ph.dwelling_apt_high_rise,
        ph.dwelling_other_single_attached,
        ph.dwelling_movable,

        -- Bedroom pivots
        ph.bedrooms_none,
        ph.bedrooms_1,
        ph.bedrooms_2,
        ph.bedrooms_3,
        ph.bedrooms_4_plus,

        -- Construction period pivots
        ph.construction_pre_1960,
        ph.construction_1961_1980,
        ph.construction_1981_1990,
        ph.construction_1991_2000,
        ph.construction_2001_2005,
        ph.construction_2006_2010,
        ph.construction_2011_2015,
        ph.construction_2016_2021

    from neighbourhoods n
    left join allocated_rentals r
        on n.neighbourhood_id = r.neighbourhood_id
    -- Join to most recent census data available for each rental year
    -- Foundation has imputed data for 2016-2020, actual data for 2021
    left join foundation f
        on n.neighbourhood_id = f.neighbourhood_id
        and f.census_year = (
            select max(f2.census_year)
            from {{ ref('int_neighbourhood__foundation') }} f2
            where f2.neighbourhood_id = n.neighbourhood_id
                and f2.census_year <= r.year
        )
    -- Join profile pivots at the resolved census year
    left join profile_housing ph
        on n.neighbourhood_id = ph.neighbourhood_id
        and ph.census_year = f.census_year
)

select * from housing
