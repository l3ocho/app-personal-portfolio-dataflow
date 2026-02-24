{{
  config(
    tags=['football']
  )
}}

with target_leagues as (
  -- Define the 7 in-scope leagues (define once, use everywhere)
  select * from (values ('GB1'), ('ES1'), ('L1'), ('IT1'), ('FR1'), ('BRA1'), ('MLS1')) as t(league_id)
),

in_scope_clubs as (
  -- Get distinct club IDs that appear in any of the 7 target leagues
  select distinct
    cs.club_id
  from {{ ref('stg_football__fact_club_season') }} cs
  inner join target_leagues tl on cs.league_id = tl.league_id
),

all_club_seasons as (
  -- Get all club-season combinations for IN-SCOPE clubs only
  -- (these are clubs that have appeared in one of the 7 leagues at any point)
  select
    isc.club_id,
    cs.season
  from in_scope_clubs isc
  -- Cross join with all seasons in the data to build all possible club-season combos
  cross join (
    select distinct season from {{ ref('stg_football__fact_player_market_value') }}
  ) cs
),

known_club_leagues as (
  -- Get all known club→league mappings from fact_club_season for IN-SCOPE clubs
  select
    cs.club_id,
    cs.season,
    cs.league_id
  from {{ ref('stg_football__fact_club_season') }} cs
  inner join in_scope_clubs isc on cs.club_id = isc.club_id
  where cs.league_id is not null
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

league_forward_filled_with_backward as (
  -- Carry backward if still NULL: max(league_id) ignores NULLs across all seasons
  select
    club_id,
    season,
    coalesce(
      league_id,
      max(league_id) over (partition by club_id)
    ) as league_id
  from league_forward_filled
),

any_known_league as (
  -- Last-resort fallback: clubs whose ONLY known seasons predate all market value
  -- seasons (e.g. known in 1999-2000, market values start 2003+) will have no
  -- non-null rows in the forward/backward fill window. Pick their most recent
  -- known league directly from the source data.
  select distinct on (club_id)
    club_id,
    league_id
  from known_club_leagues
  where league_id is not null
  order by club_id, season desc
)

select
  f.club_id,
  f.season,
  coalesce(f.league_id, akl.league_id) as league_id
from league_forward_filled_with_backward f
left join any_known_league akl on f.club_id = akl.club_id
