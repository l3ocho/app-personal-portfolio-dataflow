{{
  config(
    tags=['football']
  )
}}

with outgoing_transfers as (
  -- Calculate outgoing transfer fees per club-season
  select
    from_club_id as club_id,
    season,
    sum(fee_eur) as fees_out,
    count(*) as transfers_out_count
  from {{ ref('stg_football__fact_transfer') }}
  where from_club_id is not null and season is not null
  group by from_club_id, season
),

incoming_transfers as (
  -- Calculate incoming transfer fees per club-season
  select
    to_club_id as club_id,
    season,
    sum(fee_eur) as fees_in,
    count(*) as transfers_in_count
  from {{ ref('stg_football__fact_transfer') }}
  where to_club_id is not null and season is not null
  group by to_club_id, season
),

combined_flows as (
  -- Combine incoming and outgoing transfers
  select
    coalesce(outgoing.club_id, incoming.club_id) as club_id,
    coalesce(outgoing.season, incoming.season) as season,
    coalesce(fees_in, 0) as fees_in,
    coalesce(fees_out, 0) as fees_out,
    coalesce(fees_in, 0) - coalesce(fees_out, 0) as net_transfer_spend_eur,
    coalesce(transfers_in_count, 0) as transfers_in_count,
    coalesce(transfers_out_count, 0) as transfers_out_count
  from outgoing_transfers outgoing
  full outer join incoming_transfers incoming
    on outgoing.club_id = incoming.club_id
    and outgoing.season = incoming.season
)

select
  club_id,
  season,
  fees_in,
  fees_out,
  net_transfer_spend_eur,
  transfers_in_count,
  transfers_out_count
from combined_flows
