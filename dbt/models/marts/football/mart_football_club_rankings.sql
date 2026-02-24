{{
  config(
    tags=['football', 'mart']
  )
}}

with club_season_data as (
  -- Join squad values with league and finance data (using bridge for resolved leagues)
  select
    sv.club_id,
    sv.club_name,
    clb.league_id,
    ld.league_name,
    sv.season,
    sv.total_squad_value_eur,
    case when lf.total_revenue_eur is not null then 1 else 0 end as has_revenue_data,
    lf.total_revenue_eur
  from {{ ref('int_football__squad_values') }} sv
  left join {{ ref('int_football__club_league_bridge') }} clb
    on sv.club_id = clb.club_id
    and sv.season = clb.season
  left join {{ ref('stg_football__dim_league') }} ld on clb.league_id = ld.league_id
  left join {{ ref('int_football__league_financials') }} lf
    on clb.league_id = lf.league_id
    and sv.season = lf.season
),

with_rankings as (
  select
    club_id,
    club_name,
    league_id,
    league_name,
    season,
    total_squad_value_eur,
    has_revenue_data,
    total_revenue_eur,
    rank() over (partition by season order by total_squad_value_eur desc) as global_rank,
    rank() over (partition by league_id, season order by total_squad_value_eur desc) as league_rank
  from club_season_data
)

select
  club_id,
  club_name,
  league_id,
  league_name,
  season,
  total_squad_value_eur as squad_value_eur,
  global_rank,
  league_rank,
  total_revenue_eur as revenue_eur,
  has_revenue_data
from with_rankings
