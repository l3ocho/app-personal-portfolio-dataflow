{{
  config(
    tags=['football']
  )
}}

with latest_market_values as (
  -- Get the most recent market value for each player per season
  select
    player_id,
    club_id,
    season,
    value_eur,
    row_number() over (partition by player_id, season order by market_value_date desc) as value_rank
  from {{ ref('stg_football__fact_player_market_value') }}
  where club_id is not null and value_eur > 0
),

player_values_deduped as (
  -- Keep only the latest market value per player per season
  select
    player_id,
    club_id,
    season,
    value_eur
  from latest_market_values
  where value_rank = 1
),

club_season_values as (
  -- Aggregate to club-season level: sum of player values
  select
    pv.club_id,
    c.club_name,
    pv.season,
    sum(pv.value_eur) as total_squad_value_eur,
    avg(pv.value_eur) as avg_player_value_eur,
    count(distinct pv.player_id) as squad_size,
    max(pv.value_eur) as max_player_value_eur
  from player_values_deduped pv
  left join {{ ref('stg_football__dim_club') }} c on pv.club_id = c.club_id
  group by pv.club_id, c.club_name, pv.season
),

filtered_to_in_scope_clubs as (
  -- INNER JOIN with bridge to only include clubs in the 7 target leagues
  select
    csv.club_id,
    csv.club_name,
    csv.season,
    csv.total_squad_value_eur,
    csv.avg_player_value_eur,
    csv.max_player_value_eur,
    csv.squad_size
  from club_season_values csv
  inner join {{ ref('int_football__club_league_bridge') }} clb
    on csv.club_id = clb.club_id
    and csv.season = clb.season
)

select
  club_id,
  club_name,
  season,
  total_squad_value_eur,
  avg_player_value_eur,
  max_player_value_eur,
  squad_size
from filtered_to_in_scope_clubs
