{{
  config(
    tags=['football', 'fact']
  )
}}

select
  id,
  player_id,
  from_club_id,
  to_club_id,
  transfer_date,
  fee_eur,
  is_loan,
  season,
from {{ source('raw_football', 'fact_transfer') }}
where player_id is not null
  and to_club_id is not null
  and transfer_date is not null
