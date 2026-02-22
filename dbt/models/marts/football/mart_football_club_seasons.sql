{{
  config(
    tags=['football', 'mart', 'fact']
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
  points
from {{ ref('stg_football__fact_club_season') }}
