{{
  config(
    tags=['football', 'fact']
  )
}}

select
  id,
  club_id,
  club_name,
  season,
  revenue_eur,
  operating_profit_eur,
from {{ source('raw_football', 'fact_club_finance') }}
where club_id is not null and season is not null
