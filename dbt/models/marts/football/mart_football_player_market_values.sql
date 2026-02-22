{{
  config(
    tags=['football', 'mart', 'fact']
  )
}}

select
  id,
  player_id,
  club_id,
  value_eur,
  market_value_date,
  season
from {{ ref('stg_football__fact_player_market_value') }}
