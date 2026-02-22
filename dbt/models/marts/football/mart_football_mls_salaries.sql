{{
  config(
    tags=['football', 'mart', 'fact']
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
  guaranteed_compensation_usd
from {{ ref('stg_football__fact_mls_salary') }}
