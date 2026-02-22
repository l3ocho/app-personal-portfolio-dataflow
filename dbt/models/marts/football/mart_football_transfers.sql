{{
  config(
    tags=['football', 'mart', 'fact']
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
  season
from {{ ref('stg_football__fact_transfer') }}
