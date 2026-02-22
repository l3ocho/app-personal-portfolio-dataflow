{{
  config(
    tags=['football', 'fact']
  )
}}

select
  id,
  player_id,
  club_id,
  value_eur,
  market_value_date,
  season,
  current_timestamp() as dbt_created_at
from {{ source('raw_football', 'fact_player_market_value') }}
where player_id is not null
  and market_value_date is not null
