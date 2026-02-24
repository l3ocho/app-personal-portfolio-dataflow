{{
  config(
    tags=['football', 'mart']
  )
}}

with club_with_league as (
  -- Enrich squad values with league information (using bridge for resolved leagues)
  select
    sv.club_id,
    sv.club_name,
    sv.season,
    sv.total_squad_value_eur,
    clb.league_id,
    ld.league_name
  from {{ ref('int_football__squad_values') }} sv
  left join {{ ref('int_football__club_league_bridge') }} clb
    on sv.club_id = clb.club_id
    and sv.season = clb.season
  left join {{ ref('stg_football__dim_league') }} ld on clb.league_id = ld.league_id
),

ranked_clubs as (
  -- Rank clubs globally and mark top 3
  select
    club_id,
    club_name,
    season,
    total_squad_value_eur,
    league_id,
    league_name,
    row_number() over (partition by season order by total_squad_value_eur desc) as global_rank,
    row_number() over (partition by season order by total_squad_value_eur desc) <= 3 as is_top_3
  from club_with_league
),

league_aggregates as (
  -- Aggregate to league-season level
  select
    league_id,
    league_name,
    season,
    sum(total_squad_value_eur) as total_squad_value_eur,
    avg(total_squad_value_eur) as avg_squad_value_eur,
    count(distinct club_id) as club_count,
    sum(case when is_top_3 then total_squad_value_eur else 0 end) as top3_total_value
  from ranked_clubs
  group by league_id, league_name, season
),

with_concentration as (
  select
    league_id,
    league_name,
    season,
    total_squad_value_eur,
    avg_squad_value_eur,
    club_count,
    case when total_squad_value_eur > 0
         then (top3_total_value / total_squad_value_eur) * 100
         else 0
    end as top3_concentration_pct
  from league_aggregates
),

league_financials as (
  select distinct
    league_id,
    season,
    total_revenue_eur
  from {{ ref('int_football__league_financials') }}
)

select
  wc.league_id,
  wc.league_name,
  wc.season,
  wc.total_squad_value_eur,
  wc.avg_squad_value_eur,
  wc.top3_concentration_pct,
  wc.club_count,
  lf.total_revenue_eur
from with_concentration wc
left join league_financials lf
  on wc.league_id = lf.league_id
  and wc.season = lf.season
