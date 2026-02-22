{{
  config(
    tags=['football', 'mart', 'fact']
  )
}}

select
  id,
  club_id,
  club_name,
  season,
  revenue_eur,
  operating_profit_eur
from {{ ref('stg_football__fact_club_finance') }}
