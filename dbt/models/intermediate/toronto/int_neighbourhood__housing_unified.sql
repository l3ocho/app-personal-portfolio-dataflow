-- Intermediate: Unified housing profile per neighbourhood per year
-- Grain: one row per neighbourhood per rental year
-- Sources: int_neighbourhood__housing (census tenure + income for affordability)
--          int_rentals__annual (CMHC long format, per bedroom_type per zone)
--          stg_cmhc__zone_crosswalk (zone → neighbourhood area-weighted allocation)
--
-- NOTE: Does NOT reference any mart. Built directly from intermediates.
-- NOTE: int_rentals__neighbourhood_allocated is already wide-pivoted (no bedroom_type
--       column). This intermediate re-allocates from int_rentals__annual to get true
--       per-bedroom breakdowns for vacancy, turnover, yoy, and rental universe.
-- NOTE: median_household_income is used here for affordability calculations only.
--       It is NOT surfaced in the final SELECT (lives in mart_neighbourhood_people).
-- NOTE: Columns duplicated in mart_neighbourhood_people (dwelling value, income,
--       shelter costs, dwelling/bedroom/construction pivots, fit scores) are excluded.

with housing as (
    select * from {{ ref('int_neighbourhood__housing') }}
),

crosswalk as (
    select * from {{ ref('stg_cmhc__zone_crosswalk') }}
),

rentals_annual as (
    select * from {{ ref('int_rentals__annual') }}
),

-- Allocate zone-level rental metrics to neighbourhoods via area weights
-- Grain: one row per (neighbourhood_id, bedroom_type, year)
rentals_allocated as (
    select
        c.neighbourhood_id,
        r.year,
        r.bedroom_type,

        -- Weighted average rent
        sum(r.avg_rent * c.area_weight) / nullif(sum(c.area_weight), 0)                as avg_rent,

        -- Weighted vacancy rate
        sum(r.vacancy_rate * c.area_weight) / nullif(sum(c.area_weight), 0)             as vacancy_rate,

        -- Weighted turnover rate
        sum(r.turnover_rate * c.area_weight) / nullif(sum(c.area_weight), 0)            as turnover_rate,

        -- Weighted year-over-year rent change
        sum(r.year_over_year_rent_change * c.area_weight)
            / nullif(sum(c.area_weight), 0)                                             as year_over_year_rent_change,

        -- Proportional rental universe (sum of weighted estimates)
        sum(r.rental_universe * c.area_weight)                                          as rental_universe_estimate

    from crosswalk c
    inner join rentals_annual r on c.cmhc_zone_code = r.zone_code
    group by c.neighbourhood_id, r.year, r.bedroom_type
),

-- Add year-over-year rent change pct per neighbourhood × bedroom_type
rentals_with_yoy as (
    select
        ra.*,
        lag(ra.avg_rent, 1) over (
            partition by ra.neighbourhood_id, ra.bedroom_type
            order by ra.year
        ) as prev_year_avg_rent
    from rentals_allocated ra
),

-- Pivot from long (bedroom_type) to wide (4 columns per metric)
rentals_pivot as (
    select
        neighbourhood_id,
        year,

        -- Average rent by bedroom type
        max(case when bedroom_type = 'bachelor' then round(avg_rent::numeric, 2)                    end) as housing_rent_bachelor_avg,
        max(case when bedroom_type = '1bed'     then round(avg_rent::numeric, 2)                    end) as housing_rent_1bed_avg,
        max(case when bedroom_type = '2bed'     then round(avg_rent::numeric, 2)                    end) as housing_rent_2bed_avg,
        max(case when bedroom_type = '3bed'     then round(avg_rent::numeric, 2)                    end) as housing_rent_3bed_avg,

        -- Vacancy rate by bedroom type
        max(case when bedroom_type = 'bachelor' then round(vacancy_rate::numeric, 4)                end) as housing_vacancy_rate_bachelor,
        max(case when bedroom_type = '1bed'     then round(vacancy_rate::numeric, 4)                end) as housing_vacancy_rate_1bed,
        max(case when bedroom_type = '2bed'     then round(vacancy_rate::numeric, 4)                end) as housing_vacancy_rate_2bed,
        max(case when bedroom_type = '3bed'     then round(vacancy_rate::numeric, 4)                end) as housing_vacancy_rate_3bed,

        -- Turnover rate by bedroom type
        max(case when bedroom_type = 'bachelor' then round(turnover_rate::numeric, 4)               end) as housing_turnover_rate_bachelor,
        max(case when bedroom_type = '1bed'     then round(turnover_rate::numeric, 4)               end) as housing_turnover_rate_1bed,
        max(case when bedroom_type = '2bed'     then round(turnover_rate::numeric, 4)               end) as housing_turnover_rate_2bed,
        max(case when bedroom_type = '3bed'     then round(turnover_rate::numeric, 4)               end) as housing_turnover_rate_3bed,

        -- YoY rent change (absolute, from CMHC source) by bedroom type
        max(case when bedroom_type = 'bachelor' then round(year_over_year_rent_change::numeric, 4)  end) as housing_rent_yoy_bachelor,
        max(case when bedroom_type = '1bed'     then round(year_over_year_rent_change::numeric, 4)  end) as housing_rent_yoy_1bed,
        max(case when bedroom_type = '2bed'     then round(year_over_year_rent_change::numeric, 4)  end) as housing_rent_yoy_2bed,
        max(case when bedroom_type = '3bed'     then round(year_over_year_rent_change::numeric, 4)  end) as housing_rent_yoy_3bed,

        -- YoY rent change pct (computed from allocated neighbourhood rents) by bedroom type
        max(case when bedroom_type = 'bachelor' and prev_year_avg_rent > 0
                 then round((avg_rent - prev_year_avg_rent) / prev_year_avg_rent * 100, 2) end)     as housing_rent_yoy_pct_bachelor,
        max(case when bedroom_type = '1bed'     and prev_year_avg_rent > 0
                 then round((avg_rent - prev_year_avg_rent) / prev_year_avg_rent * 100, 2) end)     as housing_rent_yoy_pct_1bed,
        max(case when bedroom_type = '2bed'     and prev_year_avg_rent > 0
                 then round((avg_rent - prev_year_avg_rent) / prev_year_avg_rent * 100, 2) end)     as housing_rent_yoy_pct_2bed,
        max(case when bedroom_type = '3bed'     and prev_year_avg_rent > 0
                 then round((avg_rent - prev_year_avg_rent) / prev_year_avg_rent * 100, 2) end)     as housing_rent_yoy_pct_3bed,

        -- Rental universe estimate by bedroom type
        max(case when bedroom_type = 'bachelor' then round(rental_universe_estimate::numeric, 0)    end) as housing_rental_universe_est_bachelor,
        max(case when bedroom_type = '1bed'     then round(rental_universe_estimate::numeric, 0)    end) as housing_rental_universe_est_1bed,
        max(case when bedroom_type = '2bed'     then round(rental_universe_estimate::numeric, 0)    end) as housing_rental_universe_est_2bed,
        max(case when bedroom_type = '3bed'     then round(rental_universe_estimate::numeric, 0)    end) as housing_rental_universe_est_3bed,

        -- Total rental units (sum across all bedroom types)
        round(sum(rental_universe_estimate)::numeric, 0)                                             as housing_rental_units

    from rentals_with_yoy
    group by neighbourhood_id, year
),

final as (
    select
        h.neighbourhood_id,
        h.year,
        h.census_year,

        -- ── Tenure ────────────────────────────────────────────────────────
        h.pct_owner_occupied                                as housing_occupied_owner_pct,
        h.pct_renter_occupied                               as housing_occupied_renter_pct,

        -- ── Rent by bedroom type ──────────────────────────────────────────
        r.housing_rent_bachelor_avg,
        r.housing_rent_1bed_avg,
        r.housing_rent_2bed_avg,
        r.housing_rent_3bed_avg,

        -- ── YoY rent change (absolute) by bedroom type ────────────────────
        r.housing_rent_yoy_bachelor,
        r.housing_rent_yoy_1bed,
        r.housing_rent_yoy_2bed,
        r.housing_rent_yoy_3bed,

        -- ── YoY rent change pct by bedroom type ───────────────────────────
        r.housing_rent_yoy_pct_bachelor,
        r.housing_rent_yoy_pct_1bed,
        r.housing_rent_yoy_pct_2bed,
        r.housing_rent_yoy_pct_3bed,

        -- ── Vacancy rate by bedroom type ──────────────────────────────────
        r.housing_vacancy_rate_bachelor,
        r.housing_vacancy_rate_1bed,
        r.housing_vacancy_rate_2bed,
        r.housing_vacancy_rate_3bed,

        -- ── Turnover rate by bedroom type ─────────────────────────────────
        r.housing_turnover_rate_bachelor,
        r.housing_turnover_rate_1bed,
        r.housing_turnover_rate_2bed,
        r.housing_turnover_rate_3bed,

        -- ── Rental universe by bedroom type ───────────────────────────────
        r.housing_rental_universe_est_bachelor,
        r.housing_rental_universe_est_1bed,
        r.housing_rental_universe_est_2bed,
        r.housing_rental_universe_est_3bed,
        r.housing_rental_units,

        -- ── Affordability (computed from income — income NOT surfaced) ─────
        -- 2-bed used as standard reference unit for affordability
        case
            when h.median_household_income > 0 and r.housing_rent_2bed_avg > 0
            then round((r.housing_rent_2bed_avg * 12 / h.median_household_income) * 100, 2)
            else null
        end                                                 as housing_rent2income_pct,

        case
            when h.median_household_income > 0 and r.housing_rent_2bed_avg > 0
            then r.housing_rent_2bed_avg * 12 <= h.median_household_income * 0.30
            else null
        end                                                 as housing_affordable,

        -- Affordability index (100 = city average for the year)
        round(
            case
                when h.median_household_income > 0 and r.housing_rent_2bed_avg > 0
                then (r.housing_rent_2bed_avg * 12 / h.median_household_income) * 100
                else null
            end
            / nullif(
                avg(
                    case
                        when h.median_household_income > 0 and r.housing_rent_2bed_avg > 0
                        then (r.housing_rent_2bed_avg * 12 / h.median_household_income) * 100
                        else null
                    end
                ) over (partition by h.year),
                0
            ) * 100,
            1
        )                                                   as housing_affordability_index,

        -- Affordability pressure score (0-100)
        -- 2-bed rent-to-income burden (50%) + renter share (30%) + low vacancy penalty (20%)
        round(
            least(100, greatest(0,
                coalesce(
                    case
                        when h.median_household_income > 0 and r.housing_rent_2bed_avg > 0
                        then (r.housing_rent_2bed_avg * 12 / h.median_household_income) * 100
                        else null
                    end,
                0) * 0.5
                + coalesce(h.pct_renter_occupied, 0) * 0.3
                + greatest(0,
                    10 - coalesce(r.housing_vacancy_rate_2bed * 100, 10)
                  ) * 2
            )),
            1
        )                                                   as housing_affordability_pressure_score,

        -- Turnover rate reference (2-bed as primary scalar proxy, for callers
        -- that expect a single turnover_rate value)
        r.housing_turnover_rate_2bed                        as housing_turnover_rate

    from housing h
    left join rentals_pivot r
        on h.neighbourhood_id = r.neighbourhood_id
        and h.year = r.year
)

select * from final
