{{
  config(
    tags=['football', 'mart', 'dimension']
  )
}}

select
  club_id,
  club_name,
  club_code,
  country,
  founded_year,
  city
from {{ ref('stg_football__dim_club') }}
