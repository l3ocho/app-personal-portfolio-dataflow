{{
  config(
    tags=['football', 'mart', 'dimension']
  )
}}

select
  club_id,
  club_name,
  country,
  club_slug,
  logo_url,
  source_url
from {{ ref('stg_football__dim_club') }}
