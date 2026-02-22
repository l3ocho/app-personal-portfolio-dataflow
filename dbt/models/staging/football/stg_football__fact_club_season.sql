{{
  config(
    tags=['football', 'fact']
  )
}}

select
  id,
  club_id,
  league_id,
  season,
  position,
  matches_played,
  wins,
  draws,
  losses,
  goals_for,
  goals_against,
  points,
from {{ source('raw_football', 'fact_club_season') }}
where club_id is not null
  and league_id is not null
  and season is not null
