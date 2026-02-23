select
  id,
  player_id,
  value_eur,
  market_value_date,
  season
from {{ source('raw_football', 'fact_player_market_value') }}
where player_id is not null and market_value_date is not null
