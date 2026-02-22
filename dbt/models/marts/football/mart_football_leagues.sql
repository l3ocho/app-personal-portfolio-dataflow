{{
  config(
    tags=['football', 'mart', 'dimension']
  )
}}

select
  league_id,
  league_name,
  country,
  season_start_year
from {{ ref('stg_football__dim_league') }}
