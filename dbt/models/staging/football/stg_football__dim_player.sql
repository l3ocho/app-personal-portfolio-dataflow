{{
  config(
    tags=['football', 'dimension']
  )
}}

select
  player_id,
  player_name,
  date_of_birth,
  nationality,
  height_cm,
  position,
  preferred_foot,
  current_timestamp() as dbt_created_at
from {{ source('raw_football', 'dim_player') }}
where player_id is not null
