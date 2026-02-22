{{
  config(
    tags=['football', 'dimension']
  )
}}

select
  league_id,
  league_name,
  country,
  season_start_year,
  current_timestamp() as dbt_created_at
from {{ source('raw_football', 'dim_league') }}
where league_id is not null
