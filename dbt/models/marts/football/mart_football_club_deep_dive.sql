{{
  config(
    tags=['football', 'mart']
  )
}}

with club_base as (
  -- Get club base data with squad values (using bridge for resolved leagues)
  select
    sv.club_id,
    sv.club_name,
    clb.league_id,
    sv.season,
    sv.total_squad_value_eur,
    sv.avg_player_value_eur,
    sv.max_player_value_eur,
    lag(sv.total_squad_value_eur) over (partition by sv.club_id order by sv.season) as prev_year_squad_value
  from {{ ref('int_football__squad_values') }} sv
  left join {{ ref('int_football__club_league_bridge') }} clb
    on sv.club_id = clb.club_id
    and sv.season = clb.season
),

with_yoy_change as (
  select
    club_id,
    club_name,
    league_id,
    season,
    total_squad_value_eur,
    avg_player_value_eur,
    max_player_value_eur,
    prev_year_squad_value,
    case when prev_year_squad_value > 0
         then ((total_squad_value_eur - prev_year_squad_value) / prev_year_squad_value) * 100
         else null
    end as yoy_value_change_pct
  from club_base
),

transfer_data as (
  -- Get transfer flows per club-season
  select
    club_id,
    season,
    net_transfer_spend_eur,
    transfers_in_count,
    transfers_out_count
  from {{ ref('int_football__transfer_flows') }}
),

top_players as (
  -- Get top player by market value per club-season
  select
    club_id,
    season,
    dp.player_name as top_player_name,
    value_eur as top_player_value_eur,
    row_number() over (partition by club_id, season order by value_eur desc) as player_rank
  from {{ ref('stg_football__fact_player_market_value') }} pmv
  left join {{ ref('stg_football__dim_player') }} dp on pmv.player_id = dp.player_id
  where pmv.club_id is not null
),

top_players_deduped as (
  select
    club_id,
    season,
    top_player_name,
    top_player_value_eur
  from top_players
  where player_rank = 1
)

select
  wyc.club_id,
  wyc.club_name,
  wyc.league_id,
  wyc.season,
  wyc.total_squad_value_eur as squad_value_eur,
  wyc.yoy_value_change_pct,
  coalesce(td.net_transfer_spend_eur, 0) as net_transfer_spend_eur,
  coalesce(td.transfers_in_count, 0) as transfers_in_count,
  coalesce(td.transfers_out_count, 0) as transfers_out_count,
  wyc.avg_player_value_eur,
  tp.top_player_name,
  tp.top_player_value_eur
from with_yoy_change wyc
left join transfer_data td
  on wyc.club_id = td.club_id
  and wyc.season = td.season
left join top_players_deduped tp
  on wyc.club_id = tp.club_id
  and wyc.season = tp.season
