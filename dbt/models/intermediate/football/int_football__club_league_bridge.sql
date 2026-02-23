{{
  config(
    tags=['football']
  )
}}

with all_club_seasons as (
  -- Get all club-season combinations from squad values (clubs with market data)
  select
    club_id,
    season
  from {{ ref('int_football__squad_values') }}
  group by club_id, season
),

known_club_leagues as (
  -- Get all known club→league mappings from fact_club_season
  select
    club_id,
    season,
    league_id
  from {{ ref('stg_football__fact_club_season') }}
  where league_id is not null
),

club_seasons_with_league as (
  -- Start with all club-seasons and try direct join first
  select
    acs.club_id,
    acs.season,
    kcl.league_id
  from all_club_seasons acs
  left join known_club_leagues kcl
    on acs.club_id = kcl.club_id
    and acs.season = kcl.season
),

league_forward_filled as (
  -- Carry forward the most recent known league (previous seasons)
  select
    club_id,
    season,
    coalesce(
      league_id,
      max(league_id) over (partition by club_id order by season rows between unbounded preceding and 1 preceding)
    ) as league_id
  from club_seasons_with_league
),

league_resolved as (
  -- Carry backward if still NULL (fill from future seasons)
  select
    club_id,
    season,
    coalesce(
      league_id,
      first_value(league_id) over (partition by club_id order by season desc rows between unbounded preceding and unbounded following)
    ) as league_id
  from league_forward_filled
)

select
  club_id,
  season,
  league_id
from league_resolved
