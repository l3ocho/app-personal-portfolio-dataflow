{{
  config(
    tags=['football']
  )
}}

with club_finances as (
  -- Aggregate club-level finance data to league-season level
  select
    fcs.league_id,
    fcs.season,
    sum(cf.revenue_eur) as total_revenue_eur,
    avg(cf.revenue_eur) as avg_revenue_eur,
    max(cf.revenue_eur) as max_revenue_eur,
    count(distinct cf.club_id) as club_count_with_revenue
  from {{ ref('stg_football__fact_club_finance') }} cf
  left join {{ ref('stg_football__fact_club_season') }} fcs
    on cf.club_id = fcs.club_id and cf.season = fcs.season
  where cf.revenue_eur > 0
  group by fcs.league_id, fcs.season
),

league_dimensions as (
  -- Get league metadata
  select
    league_id,
    league_name,
    country
  from {{ ref('stg_football__dim_league') }}
)

select
  ld.league_id,
  ld.league_name,
  ld.country,
  cf.season,
  cf.total_revenue_eur,
  cf.avg_revenue_eur,
  cf.max_revenue_eur,
  cf.club_count_with_revenue
from league_dimensions ld
left join club_finances cf on ld.league_id = cf.league_id
