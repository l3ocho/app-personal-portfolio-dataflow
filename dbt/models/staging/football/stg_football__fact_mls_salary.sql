{{
  config(
    tags=['football', 'fact']
  )
}}

select
  id,
  player_id,
  player_name,
  club_id,
  club_name,
  season,
  salary_usd,
  guaranteed_compensation_usd,
from {{ source('raw_football', 'fact_mls_salary') }}
where player_id is not null
  and club_id is not null
  and season is not null
