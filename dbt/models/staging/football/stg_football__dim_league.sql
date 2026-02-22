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
from {{ source('raw_football', 'dim_league') }}
where league_id is not null
