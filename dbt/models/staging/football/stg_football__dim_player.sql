select
  player_id,
  player_name,
  date_of_birth,
  nationality,
  height_cm,
  position,
  preferred_foot
from {{ source('raw_football', 'dim_player') }}
where player_id is not null
