{{
  config(
    tags=['football', 'mart', 'dimension']
  )
}}

select
  player_id,
  player_name,
  date_of_birth,
  nationality,
  height_cm,
  position,
  preferred_foot
from {{ ref('stg_football__dim_player') }}
